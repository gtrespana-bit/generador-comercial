"""Métricas de producto para el panel de analítica del operador.

Una sola entrada (:func:`resumen_analitica`) calcula todo lo que pinta
``/admin/analitica``: KPIs, embudo, series diarias, cohortes de retención,
uso de funciones, riesgo de churn y los eventos recientes.

Fuentes de datos deliberadamente **híbridas**:

- Tablas maestras exactas (``usuarios``, ``organizaciones``, ``licencias``,
  ``compras_plan``): el dato comercial real, el mismo que ya usa
  ``/admin``. El operador puede leerlas por RLS.
- :class:`EventoProducto` para lo que solo ocurre en la petición: uso por
  día (latidos), primer presupuesto, envíos, importaciones…

El embudo no consulta ``presupuestos`` a propósito: es una tabla de tenant
sin política de lectura para el operador, y los eventos ``presupuesto.*``
ya contienen la señal agregada necesaria (desde la implantación de la
telemetría). Las series y cohortes se agrupan en Python a partir de filas
acotadas por ventana (7/30/90 días y 6 meses): con el volumen de un SaaS
joven son cientos de filas, no hace falta SQL de ventana por dialecto
(SQLite/PostgreSQL) y el código queda verificable.
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import date, datetime, timedelta

from sqlalchemy import func

from ..models import CompraPlan, EventoProducto, Licencia, Organizacion, Usuario
from .licencias import vence_cadena
from .telemetria import ACCIONES, dias_sin_uso, etiqueta

#: Meses hacia atrás de la tabla de cohortes.
MESES_COHORTE = 6

#: Días sin latido para considerar una organización en riesgo de churn.
DIAS_RIESGO = 14


def _pct(numerador: int, denominador: int) -> float:
    """Porcentaje 0-100 con una decimal; 0 si el denominador es 0."""
    if not denominador:
        return 0.0
    return round(100.0 * numerador / denominador, 1)


def _mes_clave(momento: datetime | date) -> str:
    return momento.strftime("%Y-%m")


def _etiqueta_mes(clave: str) -> str:
    try:
        anyo, mes = int(clave[:4]), int(clave[5:7])
    except (ValueError, IndexError):
        return clave
    nombres = [
        "ene", "feb", "mar", "abr", "may", "jun",
        "jul", "ago", "sep", "oct", "nov", "dic",
    ]
    return f"{nombres[mes - 1]} {str(anyo)[2:]}"


def _mes_siguiente(clave: str) -> str:
    anyo, mes = int(clave[:4]), int(clave[5:7])
    mes += 1
    if mes > 12:
        anyo, mes = anyo + 1, 1
    return f"{anyo:04d}-{mes:02d}"


def _dias_de_serie(desde: datetime, hasta: datetime) -> list[date]:
    dias = []
    cursor = desde.date()
    fin = hasta.date()
    while cursor <= fin:
        dias.append(cursor)
        cursor += timedelta(days=1)
    return dias


# ---------------------------------------------------------------------------
# Bloques del panel
# ---------------------------------------------------------------------------


def _kpis(db, *, hoy: date, desde: datetime) -> dict:
    usuarios = db.query(func.count(Usuario.id)).scalar() or 0
    usuarios_recientes = (
        db.query(func.count(Usuario.id))
        .filter(Usuario.created_at >= desde)
        .scalar()
        or 0
    )
    organizaciones = db.query(func.count(Organizacion.id)).scalar() or 0
    org_recientes = (
        db.query(func.count(Organizacion.id))
        .filter(Organizacion.created_at >= desde)
        .scalar()
        or 0
    )
    licencias_pago = db.query(Licencia).filter(Licencia.origen == "pago").all()
    orgs_que_pagaron = {l.organizacion_id for l in licencias_pago}
    ingresos = sum(l.importe for l in licencias_pago if l.importe > 0)

    return {
        "usuarios": usuarios,
        "usuarios_recientes": usuarios_recientes,
        "organizaciones": organizaciones,
        "org_recientes": org_recientes,
        "orgs_que_pagaron": len(orgs_que_pagaron),
        "ingresos": ingresos,
        # Los activos por ventana salen de los latidos (ver _actividad).
        "registro_a_empresa": _pct(organizaciones, usuarios),
        "empresa_a_pago": _pct(len(orgs_que_pagaron), organizaciones),
    }


def _actividad(db, *, dias: int) -> dict:
    """Series diarias y activos por ventana, a partir de los latidos."""
    hasta = datetime.utcnow()
    desde = hasta - timedelta(days=dias - 1)
    desde_utc = datetime.combine(desde.date(), datetime.min.time())

    latidos = (
        db.query(EventoProducto.organizacion_id, EventoProducto.created_at)
        .filter(
            EventoProducto.accion == "actividad.diaria",
            EventoProducto.created_at >= desde_utc,
        )
        .all()
    )
    activos_por_dia: dict[date, set[int]] = defaultdict(set)
    for org_id, creado in latidos:
        if org_id and creado:
            activos_por_dia[creado.date()].add(int(org_id))

    # Presupuestos creados por día (telemetría propia).
    presupuestos = (
        db.query(EventoProducto.created_at)
        .filter(
            EventoProducto.accion == "presupuesto.creado",
            EventoProducto.created_at >= desde_utc,
        )
        .all()
    )
    presupuestos_por_dia: dict[date, int] = defaultdict(int)
    for (creado,) in presupuestos:
        if creado:
            presupuestos_por_dia[creado.date()] += 1

    # Registros por día.
    registros = (
        db.query(Usuario.created_at)
        .filter(Usuario.created_at >= desde_utc)
        .all()
    )
    registros_por_dia: dict[date, int] = defaultdict(int)
    for (creado,) in registros:
        if creado:
            registros_por_dia[creado.date()] += 1

    lista_dias = _dias_de_serie(desde, hasta)
    hoy = date.today()
    serie = [
        {
            "fecha": d,
            "etiqueta": d.strftime("%d %b"),
            "activas": len(activos_por_dia.get(d, ())),
            "presupuestos": presupuestos_por_dia.get(d, 0),
            "registros": registros_por_dia.get(d, 0),
        }
        for d in lista_dias
    ]

    activas_hoy = len(activos_por_dia.get(hoy, ()))
    ventana7 = {org for d, orgs in activos_por_dia.items() if d >= hoy - timedelta(days=6) for org in orgs}
    ventana = {org for orgs in activos_por_dia.values() for org in orgs}

    return {
        "dias": dias,
        "serie": serie,
        "activas_hoy": activas_hoy,
        "activas_7d": len(ventana7),
        "activas_ventana": len(ventana),
    }


def _embudo(db, kpis: dict, orgs_con_presupuesto: set[int], orgs_que_enviaron: set[int]) -> list[dict]:
    organizaciones = kpis["organizaciones"]
    pasos = [
        ("Cuentas registradas", kpis["usuarios"], kpis["usuarios"]),
        ("Empresas creadas", organizaciones, kpis["usuarios"]),
        ("Crearon presupuesto", len(orgs_con_presupuesto), organizaciones),
        ("Enviaron presupuesto", len(orgs_que_enviaron), organizaciones),
        ("Pagaron", kpis["orgs_que_pagaron"], organizaciones),
    ]
    return [
        {
            "etiqueta": etiqueta,
            "valor": valor,
            "pct": _pct(valor, base),
        }
        for etiqueta, valor, base in pasos
    ]


def _funciones(db, *, desde: datetime) -> list[dict]:
    filas = (
        db.query(EventoProducto.accion, func.count(EventoProducto.id))
        .filter(
            EventoProducto.created_at >= desde,
            EventoProducto.accion != "actividad.diaria",
        )
        .group_by(EventoProducto.accion)
        .order_by(func.count(EventoProducto.id).desc())
        .all()
    )
    maximo = max((total for _, total in filas), default=0)
    return [
        {
            "accion": accion,
            "etiqueta": etiqueta(accion),
            "total": total,
            "pct": _pct(total, maximo) or (4 if total else 0),
        }
        for accion, total in filas
    ]


def _cohortes(db, *, hoy: date) -> list[dict]:
    """Retención mensual por cohorte de creación (latidos por mes)."""
    # Cohortes de los últimos MESES_COHORTE meses (el actual incluido).
    clave_actual = _mes_clave(hoy)
    claves = []
    clave = clave_actual
    for _ in range(MESES_COHORTE):
        claves.append(clave)
        anyo, mes = int(clave[:4]), int(clave[5:7])
        mes -= 1
        if mes < 1:
            anyo, mes = anyo - 1, 12
        clave = f"{anyo:04d}-{mes:02d}"
    claves.reverse()

    desde_cohortes = datetime(
        int(claves[0][:4]), int(claves[0][5:7]), 1
    )
    organizaciones = (
        db.query(Organizacion.id, Organizacion.created_at)
        .filter(Organizacion.created_at >= desde_cohortes)
        .all()
    )
    orgs_por_cohorte: dict[str, list[int]] = defaultdict(list)
    for org_id, creado in organizaciones:
        if creado:
            orgs_por_cohorte[_mes_clave(creado)].append(int(org_id))

    # Meses con uso (latidos) por organización, limitando a las orgs de las
    # cohortes para no traer historia ajena a la tabla.
    ids_cohorte = {org_id for orgs in orgs_por_cohorte.values() for org_id in orgs}
    meses_con_uso: dict[int, set[str]] = defaultdict(set)
    if ids_cohorte:
        latidos = (
            db.query(EventoProducto.organizacion_id, EventoProducto.created_at)
            .filter(
                EventoProducto.accion == "actividad.diaria",
                EventoProducto.created_at >= desde_cohortes,
                EventoProducto.organizacion_id.in_(ids_cohorte),
            )
            .all()
        )
        for org_id, creado in latidos:
            if org_id and creado:
                meses_con_uso[int(org_id)].add(_mes_clave(creado))

    # Último mes evaluable: el actual. Se ancla a la lista de claves para
    # que los offsets futuros queden como None (celdas vacías).
    indice_actual = len(claves) - 1
    tabla = []
    for i, clave_cohorte in enumerate(claves):
        orgs = orgs_por_cohorte.get(clave_cohorte, [])
        fila = {
            "mes": clave_cohorte,
            "etiqueta": _etiqueta_mes(clave_cohorte),
            "organizaciones": len(orgs),
            "valores": [],
        }
        for offset in range(MESES_COHORTE):
            if i + offset > indice_actual:
                fila["valores"].append(None)  # futuro: todavía sin datos
                continue
            objetivo = clave_cohorte
            for _ in range(offset):
                objetivo = _mes_siguiente(objetivo)
            activas = sum(
                1 for org_id in orgs if objetivo in meses_con_uso.get(org_id, ())
            )
            fila["valores"].append(_pct(activas, len(orgs)) if orgs else None)
        tabla.append(fila)
    return tabla


def _riesgo(db, *, hoy: date) -> dict:
    """Organizaciones con plan activo pero sin uso reciente (churn)."""
    licencias = db.query(Licencia).order_by(Licencia.inicio, Licencia.id).all()
    vigentes: dict[int, list[Licencia]] = defaultdict(list)
    for licencia in licencias:
        if licencia.vigente(hoy):
            vigentes[licencia.organizacion_id].append(licencia)

    if not vigentes:
        return {"pagantes_en_riesgo": [], "total_vigentes": 0}

    ultima_actividad = dict(
        db.query(
            EventoProducto.organizacion_id, func.max(EventoProducto.created_at)
        )
        .filter(
            EventoProducto.organizacion_id.in_(list(vigentes)),
        )
        .group_by(EventoProducto.organizacion_id)
        .all()
    )
    organizaciones = {
        org.id: org
        for org in db.query(Organizacion)
        .filter(Organizacion.id.in_(list(vigentes)))
        .all()
    }

    en_riesgo = []
    for org_id, licencias_org in vigentes.items():
        org = organizaciones.get(org_id)
        ultima = ultima_actividad.get(org_id)
        referencia = ultima or getattr(org, "created_at", None)
        dias = dias_sin_uso(referencia)
        if dias is None or dias < DIAS_RIESGO:
            continue
        vence_total = vence_cadena(licencias_org, hoy)
        en_riesgo.append(
            {
                "organizacion": org,
                "dias_inactivo": dias,
                "ultima_actividad": ultima,
                "vence": vence_total,
                "dias_restantes": max((vence_total - hoy).days, 0) if vence_total else 0,
            }
        )
    en_riesgo.sort(key=lambda f: (-f["dias_inactivo"], f["organizacion"].nombre))
    return {
        "pagantes_en_riesgo": en_riesgo,
        "total_vigentes": len(vigentes),
    }


def _paises(db, *, desde: datetime) -> list[dict]:
    """Registros por país (detalle del evento global ``cuenta.registrada``)."""
    filas = (
        db.query(EventoProducto.detalle)
        .filter(
            EventoProducto.accion == "cuenta.registrada",
            EventoProducto.created_at >= desde,
        )
        .all()
    )
    contador: dict[str, int] = defaultdict(int)
    for (detalle,) in filas:
        try:
            datos = json.loads(detalle or "{}")
        except (TypeError, ValueError):
            datos = {}
        pais = str((datos or {}).get("pais") or "?").upper()
        contador[pais] += 1
    total = sum(contador.values())
    return [
        {"pais": pais, "total": n, "pct": _pct(n, total)}
        for pais, n in sorted(contador.items(), key=lambda kv: -kv[1])[:8]
    ]


def _eventos_recientes(db, *, limite: int = 60) -> list[dict]:
    filas = (
        db.query(EventoProducto, Organizacion.nombre)
        .outerjoin(Organizacion, Organizacion.id == EventoProducto.organizacion_id)
        .order_by(EventoProducto.created_at.desc(), EventoProducto.id.desc())
        .limit(limite)
        .all()
    )
    resultado = []
    for evento, org_nombre in filas:
        detalle = evento.detalle_dict()
        resultado.append(
            {
                "id": evento.id,
                "accion": evento.accion,
                "etiqueta": etiqueta(evento.accion),
                "organizacion": org_nombre or "—",
                "actor": evento.actor_email or "—",
                "detalle": detalle,
                "created_at": evento.created_at,
                "global": evento.organizacion_id is None,
            }
        )
    return resultado


# ---------------------------------------------------------------------------
# Geometría de las gráficas SVG (se calcula aquí, la plantilla solo pinta)
# ---------------------------------------------------------------------------

ANCHO = 720
ALTO = 150
MARGEN_INFERIOR = 18


def _geometria_barras(serie: list[dict], clave: str) -> dict:
    """Barras SVG para una serie de la actividad diaria."""
    n = max(len(serie), 1)
    paso = ANCHO / n
    ancho_barra = max(min(paso * 0.68, 26.0), 2.0)
    maximo = max([punto[clave] for punto in serie] or [0])
    escala = (ALTO - MARGEN_INFERIOR - 8) / maximo if maximo else 0
    puntos = []
    for i, punto in enumerate(serie):
        valor = punto[clave]
        alto = round(valor * escala, 1)
        puntos.append(
            {
                "x": round(i * paso + (paso - ancho_barra) / 2, 1),
                "y": round(ALTO - MARGEN_INFERIOR - alto, 1),
                "ancho": round(ancho_barra, 1),
                "alto": alto,
                "valor": valor,
                "etiqueta": punto["etiqueta"],
                "fecha": punto["fecha"],
                "activas": punto["activas"],
                "presupuestos": punto["presupuestos"],
                "registros": punto["registros"],
            }
        )
    return {
        "ancho": ANCHO,
        "alto": ALTO,
        "maximo": maximo,
        "base": ALTO - MARGEN_INFERIOR,
        "puntos": puntos,
        "hueco": round(paso, 1),
        "total": sum(punto[clave] for punto in serie),
    }


# ---------------------------------------------------------------------------
# Entrada única del panel
# ---------------------------------------------------------------------------


def resumen_analitica(db, *, hoy: date | None = None, dias: int = 30) -> dict:
    """Todo lo que pinta ``/admin/analitica``, calculado en el servidor."""
    hoy = hoy or date.today()
    if dias not in (7, 30, 90):
        dias = 30
    hasta = datetime.utcnow()
    desde = hasta - timedelta(days=dias)

    kpis = _kpis(db, hoy=hoy, desde=desde)
    actividad = _actividad(db, dias=dias)

    orgs_con_presupuesto = {
        org_id
        for (org_id,) in db.query(EventoProducto.organizacion_id)
        .filter(EventoProducto.accion == "presupuesto.creado")
        .distinct()
        .all()
        if org_id
    }
    orgs_que_enviaron = {
        org_id
        for (org_id,) in db.query(EventoProducto.organizacion_id)
        .filter(EventoProducto.accion == "presupuesto.enviado_email")
        .distinct()
        .all()
        if org_id
    }

    kpis["activas_hoy"] = actividad["activas_hoy"]
    kpis["activas_7d"] = actividad["activas_7d"]
    kpis["activas_ventana"] = actividad["activas_ventana"]
    kpis["adopcion_activa"] = _pct(actividad["activas_ventana"], kpis["organizaciones"])
    kpis["empresa_a_presupuesto"] = _pct(
        len(orgs_con_presupuesto), kpis["organizaciones"]
    )

    serie = actividad["serie"]
    return {
        "hoy": hoy,
        "dias": dias,
        "kpis": kpis,
        "embudo": _embudo(db, kpis, orgs_con_presupuesto, orgs_que_enviaron),
        "actividad": actividad,
        "chart_activas": _geometria_barras(serie, "activas"),
        "chart_presupuestos": _geometria_barras(serie, "presupuestos"),
        "chart_registros": _geometria_barras(serie, "registros"),
        "funciones": _funciones(db, desde=desde),
        "cohortes": _cohortes(db, hoy=hoy),
        "riesgo": _riesgo(db, hoy=hoy),
        "paises": _paises(db, desde=desde),
        "eventos": _eventos_recientes(db),
        "acciones_catalogo": sorted(ACCIONES),
    }
