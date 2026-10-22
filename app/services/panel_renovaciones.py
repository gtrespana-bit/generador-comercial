"""Panel de renovaciones (Fase 2, B3): qué vence este mes y qué hacer.

Reutiliza ``resumen_organizaciones`` (solo tablas del titular: organizaciones,
licencias) y añade la vista mensual por vencimiento, el importe y el estado de
aviso. Nada de esto abre datos de tenant.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

from ..models import CompraPlan, Licencia, Organizacion
from .licencias import aviso_enviado_hoy


#: Columnas ordenables de la agenda. La clave viaja en la URL y el tercer
#: elemento es la dirección con la que empieza al pulsarla por primera vez: lo
#: que vence antes interesa primero; el importe, de mayor a menor.
ORDENES_RENOVACIONES = (
    ("vence", "Vencimiento", "asc"),
    ("dias", "Días restantes", "asc"),
    ("importe", "Importe", "desc"),
    ("cliente", "Cliente", "asc"),
)


def _normalizar_importe(valor):
    try:
        return round(float(valor or 0), 2)
    except (TypeError, ValueError):
        return 0.0


def filtrar_renovaciones(filas, *, q: str = "", estado: str = ""):
    """Filas que pasan la búsqueda y el estado.

    La comparten la pantalla y el CSV: exportar «lo que estoy mirando» no puede
    devolver el mes entero. Se busca por nombre y por slug porque el operador
    unas veces teclea «Obras Norte» y otras «obras-norte».
    """
    texto = str(q or "").strip().lower()
    salida = []
    for fila in filas:
        if estado and fila["estado"] != estado:
            continue
        if texto:
            org = fila["organizacion"]
            if texto not in f"{org.nombre} {org.slug}".lower():
                continue
        salida.append(fila)
    return salida


def ordenar_renovaciones(filas, *, orden: str = "vence", direccion: str = "asc"):
    """Orden en el servidor: la misma fila se ve igual en la tabla y en el CSV."""
    clave = orden if orden in {o[0] for o in ORDENES_RENOVACIONES} else "vence"
    invertido = direccion == "desc"

    def valor(fila):
        if clave == "dias":
            return fila["dias_restantes"]
        if clave == "importe":
            return fila["importe"]
        if clave == "cliente":
            return fila["organizacion"].nombre.lower()
        return fila["vence"]

    # El nombre desempata: dos licencias que vencen el mismo día no pueden
    # cambiar de sitio entre dos páginas (eso duplicaría filas al paginar).
    return sorted(
        filas,
        key=lambda fila: (valor(fila), fila["organizacion"].nombre.lower()),
        reverse=invertido,
    )


def renovaciones_del_mes(
    db,
    *,
    mes: date | None = None,
    hoy: date | None = None,
) -> dict:
    """Renovaciones del mes pedido, más recientes por vencimiento primero."""
    hoy = hoy or date.today()
    mes = mes or hoy.replace(day=1)
    inicio = mes.replace(day=1)
    if inicio.month == 12:
        fin = inicio.replace(year=inicio.year + 1, month=1, day=1)
    else:
        fin = inicio.replace(month=inicio.month + 1, day=1)

    organizaciones = {o.id: o for o in db.query(Organizacion).all()}
    licencias = db.query(Licencia).filter(
        Licencia.estado != "cancelada"
    ).all()
    por_org: dict[int, list[Licencia]] = defaultdict(list)
    for lic in licencias:
        por_org[lic.organizacion_id].append(lic)

    filas = []
    for org_id, grupo in por_org.items():
        for lic in grupo:
            vence = lic.vence
            if not vence or not (inicio <= vence < fin):
                continue
            dias = max((vence - hoy).days, 0)
            importe = _normalizar_importe(lic.importe)
            estado = "vencida" if lic.estado == "vencida" or vence < hoy else (
                "por_renovar" if dias <= 15 else "activa"
            )
            filas.append({
                "organizacion": organizaciones.get(org_id),
                "organizacion_id": org_id,
                "licencia": lic,
                "vence": vence,
                "dias_restantes": dias,
                "importe": importe,
                "estado": estado,
                "avisado_hoy": bool(aviso_enviado_hoy(lic, hoy)),
                "origen": lic.origen or "",
            })
    filas = [f for f in filas if f["organizacion"] is not None]
    filas.sort(key=lambda f: (f["vence"], f["organizacion"].nombre))
    importe_mes = sum(f["importe"] for f in filas)
    por_renovar = sum(1 for f in filas if f["estado"] == "por_renovar")
    return {
        "mes": mes,
        "inicio": inicio,
        "fin": fin.replace(day=1) - timedelta(days=1),
        "filas": filas,
        "importe_mes": _normalizar_importe(importe_mes),
        "por_renovar": por_renovar,
        "total": len(filas),
    }


def listar_renovaciones(
    db,
    *,
    mes: date | None = None,
    hoy: date | None = None,
    q: str = "",
    estado: str = "",
    orden: str = "vence",
    direccion: str = "asc",
    pagina: int = 1,
    por_pagina: int = 25,
) -> dict:
    """Agenda del mes filtrada, ordenada y recortada a una página (Fase 1).

    Los KPI —importe en juego, por renovar, avisos— se siguen calculando sobre
    el mes completo: son la foto del negocio, no de la búsqueda. ``total``, los
    contadores de los chips y ``filas`` sí responden a lo que se está mirando.
    """
    from .panel_listas import paginar_lista

    datos = renovaciones_del_mes(db, mes=mes, hoy=hoy)
    # La búsqueda se aplica antes de contar para que los chips digan cuántas
    # quedarían con ese estado, igual que en Compras y Soporte.
    con_texto = filtrar_renovaciones(datos["filas"], q=q)
    contadores = {
        "": len(con_texto),
        "por_renovar": sum(1 for f in con_texto if f["estado"] == "por_renovar"),
        "vencida": sum(1 for f in con_texto if f["estado"] == "vencida"),
        "activa": sum(1 for f in con_texto if f["estado"] == "activa"),
    }
    visibles = ordenar_renovaciones(
        filtrar_renovaciones(con_texto, estado=estado),
        orden=orden,
        direccion=direccion,
    )
    filas, meta = paginar_lista(visibles, pagina=pagina, por_pagina=por_pagina)
    return {
        **datos,
        "filas": filas,
        "total": len(visibles),
        # El KPI de la cabecera responde al mes, no a la búsqueda: cambiar de
        # filtro no puede cambiar «cuántos accesos vencen en octubre».
        "total_mes": datos["total"],
        "meta": meta,
        "contadores": contadores,
        "avisos_hoy": sum(1 for f in datos["filas"] if f.get("avisado_hoy")),
    }


def proximas_renovaciones(db, *, hoy: date | None = None, limite: int = 20) -> list[dict]:
    """Las renovaciones más próximas (para el dashboard y notificaciones)."""
    hoy = hoy or date.today()
    organizaciones = {o.id: o for o in db.query(Organizacion).all()}
    licencias = db.query(Licencia).filter(Licencia.estado != "cancelada").all()
    filas = []
    for lic in licencias:
        if not lic.vence:
            continue
        dias = max((lic.vence - hoy).days, 0)
        if dias > 15:
            continue
        filas.append({
            "organizacion": organizaciones.get(lic.organizacion_id),
            "organizacion_id": lic.organizacion_id,
            "vence": lic.vence,
            "dias_restantes": dias,
            "importe": _normalizar_importe(lic.importe),
        })
    filas = [f for f in filas if f["organizacion"] is not None]
    filas.sort(key=lambda f: (f["vence"], f["organizacion"].nombre))
    return filas[:limite]
