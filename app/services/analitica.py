"""Métricas de producto para el panel de analítica del operador.

Una sola entrada (:func:`resumen_analitica`) calcula todo lo que pinta
``/admin/analitica``: KPIs, presencia en vivo, embudo, series diarias,
actividad por organización, cohortes de retención, uso de funciones, horas
punta, riesgo de churn y el explorador de eventos.

Fuentes de datos deliberadamente **híbridas**:

- Tablas maestras exactas (``usuarios``, ``organizaciones``, ``licencias``,
  ``compras_plan``): el dato comercial real, el mismo que ya usa
  ``/admin``. El operador puede leerlas por RLS.
- :class:`EventoProducto` para lo que solo ocurre en la petición: presencia
  (``sesion.activa``), uso por día (latidos), primer presupuesto, envíos,
  importaciones…
- ``cotizat_security.admin_resumen_organizaciones()`` en PostgreSQL para los
  agregados por empresa (miembros, presupuestos, clientes, facturas): una
  sola consulta, sin abrir el aislamiento multi-tenant. En SQLite se calcula
  con consultas directas.

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
from datetime import date, datetime, time, timedelta

from urllib.parse import urlencode

from sqlalchemy import func, or_, text

from ..models import (
    Cliente,
    CompraPlan,
    EventoProducto,
    Factura,
    Licencia,
    Membresia,
    Organizacion,
    Presupuesto,
    Usuario,
)
from .licencias import vence_cadena
from .telemetria import (
    ACCIONES,
    ACCIONES_RUIDO,
    PRESENCIA_MINUTOS,
    dias_sin_uso,
    etiqueta,
)

#: Meses hacia atrás de la tabla de cohortes.
MESES_COHORTE = 6

#: Días sin latido para considerar una organización en riesgo de churn.
DIAS_RIESGO = 14

#: Eventos por página del explorador.
EVENTOS_POR_PAGINA = 50

#: Tope de la tabla por organización (protege el panel de una base enorme).
MAXIMO_ORGANIZACIONES_TABLA = 200


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


def _inicio_dia(dia: date) -> datetime:
    return datetime.combine(dia, time.min)


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

    inicio_hoy = _inicio_dia(hoy)
    usuarios_hoy = (
        db.query(func.count(Usuario.id))
        .filter(Usuario.ultimo_acceso_at >= inicio_hoy)
        .scalar()
        or 0
    )
    usuarios_7d = (
        db.query(func.count(Usuario.id))
        .filter(Usuario.ultimo_acceso_at >= _inicio_dia(hoy - timedelta(days=6)))
        .scalar()
        or 0
    )
    return {
        "usuarios": usuarios,
        "usuarios_recientes": usuarios_recientes,
        "usuarios_hoy": usuarios_hoy,
        "usuarios_7d": usuarios_7d,
        "organizaciones": organizaciones,
        "org_recientes": org_recientes,
        "orgs_que_pagaron": len(orgs_que_pagaron),
        "ingresos": ingresos,
        # Los activos por ventana salen de los latidos (ver _actividad).
        "registro_a_empresa": _pct(organizaciones, usuarios),
        "empresa_a_pago": _pct(len(orgs_que_pagaron), organizaciones),
    }


def _presupuestos_por_ventana(db, *, hoy: date) -> dict:
    """Cuántos presupuestos se han creado: hoy, esta semana, este mes y ventana."""
    inicio_hoy = _inicio_dia(hoy)
    inicio_semana = _inicio_dia(hoy - timedelta(days=hoy.weekday()))
    inicio_mes = datetime(hoy.year, hoy.month, 1)

    def _contar(desde: datetime) -> int:
        return int(
            db.query(func.count(EventoProducto.id))
            .filter(
                EventoProducto.accion == "presupuesto.creado",
                EventoProducto.created_at >= desde,
            )
            .scalar()
            or 0
        )

    return {
        "hoy": _contar(inicio_hoy),
        "semana": _contar(inicio_semana),
        "mes": _contar(inicio_mes),
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


def _en_vivo(db, *, hoy: date | None = None) -> dict:
    """Presencia real: quién está usando el producto ahora mismo.

    ``sesion.activa`` se escribe con freno desde ``get_db``, así que una fila
    reciente significa «alguien de esta empresa estuvo trabajando hace menos de
    ``PRESENCIA_MINUTOS``». Es la única señal con granularidad suficiente para
    distinguir «en línea» de «entró esta mañana».
    """
    ahora = datetime.utcnow()
    hoy = hoy or date.today()
    corte = ahora - timedelta(minutes=PRESENCIA_MINUTOS)

    filas = (
        db.query(
            EventoProducto.organizacion_id,
            EventoProducto.actor_email,
            EventoProducto.detalle,
            EventoProducto.created_at,
        )
        .filter(
            EventoProducto.accion == "sesion.activa",
            EventoProducto.created_at >= corte,
        )
        .order_by(EventoProducto.created_at.desc())
        .all()
    )
    por_org: dict[int, dict] = {}
    for org_id, actor, detalle, creado in filas:
        if not org_id:
            continue
        org_id = int(org_id)
        anterior = por_org.get(org_id)
        if anterior is not None and anterior["visto"] >= creado:
            continue
        try:
            datos = json.loads(detalle or "{}")
        except (TypeError, ValueError):
            datos = {}
        por_org[org_id] = {
            "organizacion_id": org_id,
            "visto": creado,
            "actor": actor or "",
            "pagina": str((datos or {}).get("pagina") or ""),
        }

    nombres = {}
    if por_org:
        nombres = {
            org.id: org.nombre
            for org in db.query(Organizacion)
            .filter(Organizacion.id.in_(list(por_org)))
            .all()
        }
    en_linea = [
        {
            "organizacion_id": org_id,
            "organizacion": nombres.get(org_id, f"Empresa #{org_id}"),
            "actor": datos["actor"],
            "pagina": datos["pagina"],
            "visto": datos["visto"],
            "minutos": max(int((ahora - datos["visto"]).total_seconds() // 60), 0),
        }
        for org_id, datos in por_org.items()
    ]
    en_linea.sort(key=lambda f: f["visto"], reverse=True)

    inicio_hoy = _inicio_dia(hoy)
    logueados = (
        db.query(Usuario.id, Usuario.email, Usuario.nombre, Usuario.ultimo_acceso_at)
        .filter(Usuario.ultimo_acceso_at >= inicio_hoy)
        .order_by(Usuario.ultimo_acceso_at.desc())
        .all()
    )
    eventos_15 = int(
        db.query(func.count(EventoProducto.id))
        .filter(
            EventoProducto.created_at >= ahora - timedelta(minutes=15),
            EventoProducto.accion.notin_(tuple(ACCIONES_RUIDO)),
        )
        .scalar()
        or 0
    )

    return {
        "actualizado": ahora,
        "en_linea": en_linea,
        "en_linea_total": len(en_linea),
        "logueados": [
            {
                "id": u.id,
                "email": u.email,
                "nombre": u.nombre,
                "acceso": u.ultimo_acceso_at,
            }
            for u in logueados
        ],
        "logueados_total": len(logueados),
        "eventos_ultimos_15": eventos_15,
        "presencia_minutos": PRESENCIA_MINUTOS,
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
            EventoProducto.accion.notin_(tuple(ACCIONES_RUIDO)),
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


def _horas_punta(db, *, desde: datetime) -> dict:
    """Cuándo se trabaja: distribución por hora UTC y por día de la semana.

    Sirve para decisiones concretas (ventanas de mantenimiento, horarios de
    soporte, envíos de correo) que una lista de eventos no responde.
    """
    filas = (
        db.query(EventoProducto.created_at)
        .filter(
            EventoProducto.created_at >= desde,
            EventoProducto.accion.notin_(tuple(ACCIONES_RUIDO)),
        )
        .all()
    )
    por_hora = [0] * 24
    por_dia = [0] * 7
    for (creado,) in filas:
        if not creado:
            continue
        por_hora[creado.hour] += 1
        por_dia[creado.weekday()] += 1
    maximo_hora = max(por_hora, default=0)
    maximo_dia = max(por_dia, default=0)
    nombres_dia = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
    return {
        "horas": [
            {
                "hora": h,
                "etiqueta": f"{h:02d}",
                "total": total,
                "pct": _pct(total, maximo_hora),
            }
            for h, total in enumerate(por_hora)
        ],
        "dias": [
            {
                "dia": i,
                "etiqueta": nombre,
                "total": por_dia[i],
                "pct": _pct(por_dia[i], maximo_dia),
            }
            for i, nombre in enumerate(nombres_dia)
        ],
        "total": len(filas),
        "hora_punta": por_hora.index(maximo_hora) if maximo_hora else None,
        "chart_horas": _geometria_series(
            [
                {"etiqueta": f"{h:02d}", "total": total}
                for h, total in enumerate(por_hora)
            ]
        ),
        "chart_dias": _geometria_series(
            [
                {"etiqueta": nombre, "total": por_dia[i]}
                for i, nombre in enumerate(nombres_dia)
            ],
            alto=110,
        ),
    }


def _agregados_por_organizacion_postgres(db) -> dict[int, dict]:
    """Agregados por empresa con una sola consulta (función de la migración)."""
    filas = db.execute(
        text("SELECT * FROM cotizat_security.admin_resumen_organizaciones()")
    ).mappings().all()
    return {
        int(fila["organizacion_id"]): {
            "miembros": int(fila.get("miembros") or 0),
            "presupuestos": int(fila.get("presupuestos") or 0),
            "clientes": int(fila.get("clientes") or 0),
            "facturas": int(fila.get("facturas") or 0),
            "total_presupuestado": float(fila.get("total_presupuestado") or 0),
            "ultimo_acceso": fila.get("ultimo_acceso"),
        }
        for fila in filas
    }


def _agregados_por_organizacion_sqlite(db) -> dict[int, dict]:
    """Equivalente directo para SQLite (sin RLS)."""
    agregados: dict[int, dict] = {}

    def _fila(org_id: int) -> dict:
        return agregados.setdefault(
            org_id,
            {
                "miembros": 0,
                "presupuestos": 0,
                "clientes": 0,
                "facturas": 0,
                "total_presupuestado": 0.0,
                "ultimo_acceso": None,
            },
        )

    for org_id, total in (
        db.query(Membresia.organizacion_id, func.count(Membresia.id))
        .filter(Membresia.activa.is_(True))
        .group_by(Membresia.organizacion_id)
        .all()
    ):
        _fila(org_id)["miembros"] = int(total or 0)
    for org_id, total in (
        db.query(Presupuesto.organizacion_id, func.count(Presupuesto.id))
        .filter(Presupuesto.es_demo.is_(False))
        .group_by(Presupuesto.organizacion_id)
        .all()
    ):
        _fila(org_id)["presupuestos"] = int(total or 0)
    for org_id, total in (
        db.query(Cliente.organizacion_id, func.count(Cliente.id))
        .group_by(Cliente.organizacion_id)
        .all()
    ):
        _fila(org_id)["clientes"] = int(total or 0)
    for org_id, total in (
        db.query(Factura.organizacion_id, func.count(Factura.id))
        .group_by(Factura.organizacion_id)
        .all()
    ):
        _fila(org_id)["facturas"] = int(total or 0)
    for org_id, total in (
        db.query(Presupuesto.organizacion_id, func.sum(Presupuesto.total_calculado))
        .filter(Presupuesto.total_calculado > 0)
        .group_by(Presupuesto.organizacion_id)
        .all()
    ):
        _fila(org_id)["total_presupuestado"] = float(total or 0)
    for org_id, acceso in (
        db.query(Membresia.organizacion_id, func.max(Usuario.ultimo_acceso_at))
        .join(Usuario, Usuario.id == Membresia.usuario_id)
        .filter(Membresia.activa.is_(True))
        .group_by(Membresia.organizacion_id)
        .all()
    ):
        _fila(org_id)["ultimo_acceso"] = acceso
    return agregados


def _tabla_organizaciones(db, *, desde: datetime, en_vivo: dict) -> dict:
    """Una fila por empresa con lo que de verdad se quiere mirar.

    Mezcla el dato comercial (miembros, presupuestos, clientes, último acceso)
    con el de uso (eventos en la ventana, última actividad, presencia). Sin
    abrir contenido de presupuestos ni datos de los clientes de la empresa.
    """
    limitada = False
    try:
        if db.get_bind().dialect.name == "postgresql":
            agregados = _agregados_por_organizacion_postgres(db)
        else:
            agregados = _agregados_por_organizacion_sqlite(db)
    except Exception:
        # Migración pendiente: el panel sigue abriendo con lo que sí puede leer.
        try:
            db.rollback()
        except Exception:
            pass
        agregados = {}
        limitada = True

    organizaciones = (
        db.query(Organizacion)
        .order_by(Organizacion.created_at.desc(), Organizacion.id.desc())
        .limit(MAXIMO_ORGANIZACIONES_TABLA)
        .all()
    )

    eventos = dict(
        db.query(EventoProducto.organizacion_id, func.count(EventoProducto.id))
        .filter(
            EventoProducto.created_at >= desde,
            EventoProducto.accion.notin_(tuple(ACCIONES_RUIDO)),
        )
        .group_by(EventoProducto.organizacion_id)
        .all()
    )
    ultima_actividad = dict(
        db.query(
            EventoProducto.organizacion_id, func.max(EventoProducto.created_at)
        )
        .group_by(EventoProducto.organizacion_id)
        .all()
    )
    # Días de uso de la ventana (latidos): el DAU por empresa, que es más
    # informativo que un recuento de eventos sueltos.
    dias_por_org: dict[int, set[date]] = defaultdict(set)
    for org_id, creado in (
        db.query(EventoProducto.organizacion_id, EventoProducto.created_at)
        .filter(
            EventoProducto.accion == "actividad.diaria",
            EventoProducto.created_at >= desde,
        )
        .all()
    ):
        if org_id and creado:
            dias_por_org[int(org_id)].add(creado.date())
    licencias: dict[int, list[Licencia]] = defaultdict(list)
    for licencia in db.query(Licencia).all():
        licencias[licencia.organizacion_id].append(licencia)
    hoy = date.today()
    en_linea = {fila["organizacion_id"]: fila for fila in en_vivo["en_linea"]}

    filas = []
    for org in organizaciones:
        datos = agregados.get(org.id, {})
        vigentes = [l for l in licencias.get(org.id, []) if l.vigente(hoy)]
        vence = vence_cadena(vigentes, hoy)
        ultima = ultima_actividad.get(org.id)
        presencia = en_linea.get(org.id)
        if presencia:
            estado = "en_linea"
        elif ultima and (datetime.utcnow() - ultima).days < 1:
            estado = "hoy"
        elif ultima and (datetime.utcnow() - ultima).days <= 7:
            estado = "semana"
        elif ultima:
            estado = "inactiva"
        else:
            estado = "nunca"
        filas.append(
            {
                "id": org.id,
                "nombre": org.nombre,
                "creada": org.created_at,
                "activa": bool(org.activa),
                "miembros": int(datos.get("miembros") or 0),
                "presupuestos": int(datos.get("presupuestos") or 0),
                "clientes": int(datos.get("clientes") or 0),
                "facturas": int(datos.get("facturas") or 0),
                "total_presupuestado": float(datos.get("total_presupuestado") or 0),
                "ultimo_acceso": datos.get("ultimo_acceso"),
                "eventos": int(eventos.get(org.id) or 0),
                "dias_uso": len(dias_por_org.get(org.id, ())),
                "ultima_actividad": ultima,
                "en_linea": bool(presencia),
                "visto": presencia["visto"] if presencia else None,
                "plan_vence": vence,
                "dias_plan": max((vence - hoy).days, 0) if vence else 0,
                "pagando": bool(vigentes),
                "estado": estado,
            }
        )
    def _orden(fila: dict) -> tuple[int, float]:
        """En línea primero; después, por la última señal de vida."""
        referencia = fila["visto"] or fila["ultima_actividad"]
        marca = referencia.timestamp() if referencia else 0.0
        return (0 if fila["en_linea"] else 1, -marca)

    filas.sort(key=_orden)
    return {
        "filas": filas,
        "limitada": limitada,
        "total": len(organizaciones),
    }


# ---------------------------------------------------------------------------
# Explorador de eventos
# ---------------------------------------------------------------------------


def _enlace_explorador(filtros: dict, *, dias: int, pagina: int) -> str:
    """Query string del explorador conservando los filtros (sin `pagina`)."""
    parametros = [("dias", dias)]
    if filtros["organizacion_id"]:
        parametros.append(("organizacion_id", filtros["organizacion_id"]))
    if filtros["accion"]:
        parametros.append(("accion", filtros["accion"]))
    if filtros["actor"]:
        parametros.append(("actor", filtros["actor"]))
    if filtros["q"]:
        parametros.append(("q", filtros["q"]))
    if filtros["desde"]:
        parametros.append(("desde", filtros["desde"].isoformat()))
    if filtros["hasta"]:
        parametros.append(("hasta", filtros["hasta"].isoformat()))
    if not filtros["ocultar_ruido"]:
        parametros.append(("ruido", 1))
    if filtros["ocultar_mios"]:
        parametros.append(("sin_mios", 1))
    if pagina > 1:
        parametros.append(("pagina", pagina))
    return urlencode(parametros)


def _fecha_filtro(valor) -> date | None:
    """``YYYY-MM-DD`` (o un ``date``) a fecha, sin admitir nada más."""
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    texto = str(valor or "").strip()
    if not texto:
        return None
    try:
        return datetime.strptime(texto, "%Y-%m-%d").date()
    except ValueError:
        return None


def _filtros_eventos(filtros: dict | None) -> dict:
    """Normaliza los filtros que llegan de la URL (nunca se confía en ellos)."""
    filtros = dict(filtros or {})
    accion = str(filtros.get("accion") or "").strip()
    if accion not in ACCIONES:
        accion = ""
    try:
        organizacion_id = int(filtros.get("organizacion_id") or 0)
    except (TypeError, ValueError):
        organizacion_id = 0
    pagina = filtros.get("pagina")
    try:
        pagina = max(int(pagina or 1), 1)
    except (TypeError, ValueError):
        pagina = 1
    return {
        "accion": accion,
        "organizacion_id": organizacion_id if organizacion_id > 0 else 0,
        "actor": str(filtros.get("actor") or "").strip()[:254],
        "q": str(filtros.get("q") or "").strip()[:120],
        "desde": _fecha_filtro(filtros.get("desde")),
        "hasta": _fecha_filtro(filtros.get("hasta")),
        "pagina": pagina,
        "ocultar_ruido": bool(filtros.get("ocultar_ruido", True)),
        "ocultar_mios": bool(filtros.get("ocultar_mios", False)),
        "mi_email": str(filtros.get("mi_email") or "").strip().lower(),
    }


def _eventos(db, *, filtros: dict, dias: int = 30) -> dict:
    """Explorador de eventos: filtros por empresa, acción, actor y fecha.

    Devuelve además del listado el **total** sin paginar, que es lo que
    responde «¿cuántos eventos hay de verdad?» y lo que faltaba cuando la
    tabla solo enseñaba las 60 filas más recientes de toda la plataforma.
    """
    consulta = db.query(EventoProducto, Organizacion.nombre).outerjoin(
        Organizacion, Organizacion.id == EventoProducto.organizacion_id
    )
    if filtros["ocultar_ruido"]:
        consulta = consulta.filter(
            EventoProducto.accion.notin_(tuple(ACCIONES_RUIDO))
        )
    if filtros["accion"]:
        consulta = consulta.filter(EventoProducto.accion == filtros["accion"])
    if filtros["organizacion_id"]:
        consulta = consulta.filter(
            EventoProducto.organizacion_id == filtros["organizacion_id"]
        )
    if filtros["actor"]:
        consulta = consulta.filter(
            EventoProducto.actor_email.ilike(f"%{filtros['actor']}%")
        )
    if filtros["ocultar_mios"] and filtros["mi_email"]:
        consulta = consulta.filter(
            func.lower(EventoProducto.actor_email) != filtros["mi_email"]
        )
    if filtros["desde"]:
        consulta = consulta.filter(
            EventoProducto.created_at >= _inicio_dia(filtros["desde"])
        )
    if filtros["hasta"]:
        consulta = consulta.filter(
            EventoProducto.created_at < _inicio_dia(filtros["hasta"] + timedelta(days=1))
        )
    if filtros["q"]:
        patron = f"%{filtros['q']}%"
        consulta = consulta.filter(
            or_(
                EventoProducto.detalle.ilike(patron),
                EventoProducto.actor_email.ilike(patron),
                Organizacion.nombre.ilike(patron),
            )
        )

    total = consulta.count()
    por_pagina = EVENTOS_POR_PAGINA
    paginas = max((total + por_pagina - 1) // por_pagina, 1)
    pagina = min(filtros["pagina"], paginas)
    filas = (
        consulta.order_by(EventoProducto.created_at.desc(), EventoProducto.id.desc())
        .offset((pagina - 1) * por_pagina)
        .limit(por_pagina)
        .all()
    )

    # Enlaces ya construidos: el explorador se pagina sin perder los filtros
    # ni el orden en que llegaron (y sin concatenar cadenas en la plantilla).
    filtros["enlace_anterior"] = _enlace_explorador(filtros, dias=dias, pagina=pagina - 1) if pagina > 1 else ""
    filtros["enlace_siguiente"] = _enlace_explorador(filtros, dias=dias, pagina=pagina + 1) if pagina < paginas else ""

    eventos = []
    for evento, org_nombre in filas:
        detalle = evento.detalle_dict()
        eventos.append(
            {
                "id": evento.id,
                "accion": evento.accion,
                "etiqueta": etiqueta(evento.accion),
                "organizacion": org_nombre or "—",
                "organizacion_id": evento.organizacion_id,
                "actor": evento.actor_email or "—",
                "detalle": detalle,
                "created_at": evento.created_at,
                "global": evento.organizacion_id is None,
            }
        )

    organizaciones = [
        {"id": org.id, "nombre": org.nombre}
        for org in db.query(Organizacion).order_by(Organizacion.nombre).all()
    ]
    return {
        "eventos": eventos,
        "total": total,
        "pagina": pagina,
        "paginas": paginas,
        "por_pagina": por_pagina,
        "filtros": filtros,
        "organizaciones": organizaciones,
    }


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


def _geometria_series(filas: list[dict], *, clave: str = "total", ancho: int = 720, alto: int = 120) -> dict:
    """Barras SVG para listas simples (horas del día, días de la semana)."""
    n = max(len(filas), 1)
    paso = ancho / n
    ancho_barra = max(min(paso * 0.7, 34.0), 3.0)
    maximo = max([fila[clave] for fila in filas] or [0])
    base = alto - 12
    escala = (base - 6) / maximo if maximo else 0
    puntos = []
    for i, fila in enumerate(filas):
        valor = fila[clave]
        barra = round(valor * escala, 1)
        puntos.append(
            {
                "x": round(i * paso + (paso - ancho_barra) / 2, 1),
                "y": round(base - barra, 1),
                "ancho": round(ancho_barra, 1),
                "alto": barra,
                "valor": valor,
                "etiqueta": fila["etiqueta"],
            }
        )
    return {
        "ancho": ancho,
        "alto": alto,
        "base": base,
        "maximo": maximo,
        "puntos": puntos,
    }


# ---------------------------------------------------------------------------
# Entrada única del panel
# ---------------------------------------------------------------------------


def resumen_analitica(
    db, *, hoy: date | None = None, dias: int = 30, filtros: dict | None = None
) -> dict:
    """Todo lo que pinta ``/admin/analitica``, calculado en el servidor."""
    hoy = hoy or date.today()
    if dias not in (7, 30, 90):
        dias = 30
    hasta = datetime.utcnow()
    desde = hasta - timedelta(days=dias)

    kpis = _kpis(db, hoy=hoy, desde=desde)
    actividad = _actividad(db, dias=dias)
    en_vivo = _en_vivo(db, hoy=hoy)

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

    presupuestos_ventana = _presupuestos_por_ventana(db, hoy=hoy)
    filtros_normalizados = _filtros_eventos(filtros)
    explorador = _eventos(db, filtros=filtros_normalizados, dias=dias)
    tabla_organizaciones = _tabla_organizaciones(db, desde=desde, en_vivo=en_vivo)

    kpis["activas_hoy"] = actividad["activas_hoy"]
    kpis["activas_7d"] = actividad["activas_7d"]
    kpis["activas_ventana"] = actividad["activas_ventana"]
    kpis["adopcion_activa"] = _pct(actividad["activas_ventana"], kpis["organizaciones"])
    kpis["empresa_a_presupuesto"] = _pct(
        len(orgs_con_presupuesto), kpis["organizaciones"]
    )
    kpis["presupuestos_ventana"] = sum(
        punto["presupuestos"] for punto in actividad["serie"]
    )
    kpis["presupuestos_hoy"] = presupuestos_ventana["hoy"]
    kpis["presupuestos_semana"] = presupuestos_ventana["semana"]
    kpis["presupuestos_mes"] = presupuestos_ventana["mes"]
    kpis["orgs_sin_presupuesto"] = max(
        kpis["organizaciones"] - len(orgs_con_presupuesto), 0
    )
    # Si hay empresas pero ninguna cuenta visible, la lectura de `usuarios`
    # está bloqueada por RLS (migración pendiente). El panel lo dice en vez de
    # enseñar un «1» que parece un dato.
    kpis["usuarios_limitados"] = bool(kpis["organizaciones"] and not kpis["usuarios"])

    serie = actividad["serie"]
    return {
        "hoy": hoy,
        "dias": dias,
        "kpis": kpis,
        "en_vivo": en_vivo,
        "embudo": _embudo(db, kpis, orgs_con_presupuesto, orgs_que_enviaron),
        "actividad": actividad,
        "chart_activas": _geometria_barras(serie, "activas"),
        "chart_presupuestos": _geometria_barras(serie, "presupuestos"),
        "chart_registros": _geometria_barras(serie, "registros"),
        "funciones": _funciones(db, desde=desde),
        "cohortes": _cohortes(db, hoy=hoy),
        "riesgo": _riesgo(db, hoy=hoy),
        "paises": _paises(db, desde=desde),
        "horas": _horas_punta(db, desde=desde),
        "organizaciones": tabla_organizaciones,
        "eventos": explorador["eventos"],
        "explorador": explorador,
        "acciones_catalogo": sorted(ACCIONES),
    }
