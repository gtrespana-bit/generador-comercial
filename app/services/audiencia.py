"""Audiencia de la capa pública: visitantes y páginas vistas por día.

Mide lo que Google Analytics 4 ve por fuera (tráfico, páginas, origen) pero
con un dato propio del servidor, sin cookies y sin terceros, desligado de
cuentas. Cada visita de página deja una fila en ``visitas_pagina`` a través
de ``app.main.AudienciaMiddleware``; este servicio agrega esas filas **en SQL**
(nunca trayendo la tabla cruda a memoria, lo que disparaba el egress de la BD)
y poda automáticamente el histórico fuera de la ventana de retención.

Todas las funciones son best-effort: si la tabla aún no existe (migración
pendiente) o la lectura falla, devuelven vacíos en lugar de tirar el panel.
"""
from __future__ import annotations

import logging
import os
from datetime import date, datetime, time, timedelta

from sqlalchemy import case, func, or_

from ..models import VisitaPagina

logger = logging.getLogger("cotizat.audiencia")

#: Páginas más vistas que se enseñan en el panel.
PAGINAS_TOP = 8

#: Días de histórico crudo conservados por omisión en ``visitas_pagina``.
#: El cron diario poda todo lo anterior para acotar el tamaño en disco.
RETENCION_AUDIENCIA_DIAS = 30


def audiencia_bd_activada() -> bool:
    """Interruptor de escritura en ``visitas_pagina`` (``COTIZAT_AUDIENCIA_BD``).

    Activo por omisión. Ponerlo en ``false`` detiene las inserciones en base de
    datos al instante (p. ej. ante una oleada de scrapers) sin afectar a GA4 ni
    a Vercel Analytics.
    """
    valor = os.environ.get("COTIZAT_AUDIENCIA_BD", "true").strip().lower()
    return valor not in {"0", "false", "no", "off"}


def retencion_audiencia_dias() -> int:
    """Días que se conservan en ``visitas_pagina`` (0 desactiva la poda)."""
    crudo = os.environ.get(
        "COTIZAT_AUDIENCIA_RETENCION_DIAS", str(RETENCION_AUDIENCIA_DIAS)
    ).strip()
    try:
        valor = int(crudo)
    except (TypeError, ValueError):
        return RETENCION_AUDIENCIA_DIAS
    return max(0, min(valor, 365))


def _a_fecha(valor: date | datetime | str | None) -> date | None:
    """Normaliza ``date``, ``datetime`` o cadena ISO (``func.date`` en SQLite)."""
    if valor is None:
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    texto = str(valor).strip()
    if len(texto) >= 10:
        try:
            return date.fromisoformat(texto[:10])
        except ValueError:
            return None
    return None


def _inicio_dia(dia: date | datetime) -> datetime:
    fecha = dia.date() if isinstance(dia, datetime) else dia
    return datetime.combine(fecha, time.min)


def _dias_de_serie(desde: date | datetime, hasta: date | datetime) -> list[date]:
    """Días del rango, con los dos extremos incluidos.

    Acepta ``date`` y ``datetime``. ``resumen_audiencia`` recibe ``hoy`` como
    fecha (lo pasa el panel) y le resta ``timedelta``, así que aquí llegan
    ``date``; llamar ``.date()`` sobre una fecha fue el 500 del 06/11/2026
    (``AttributeError: 'datetime.date' object has no attribute 'date'``),
    que solo apareció cuando la audiencia empezó a tener filas.
    """
    dias = []
    cursor = desde.date() if isinstance(desde, datetime) else desde
    fin = hasta.date() if isinstance(hasta, datetime) else hasta
    while cursor <= fin:
        dias.append(cursor)
        cursor += timedelta(days=1)
    return dias


def _pagina_etiqueta(ruta) -> str:
    ruta = (ruta or "/").strip()
    return ruta if ruta else "/"


def resumen_audiencia(db, *, dias: int = 30, hoy: date | datetime | None = None) -> dict:
    """Visitantes únicos y páginas vistas por día en la ventana.

    Un visitante = un ``ip_hash`` distinto en un día. Nunca se guarda la IP,
    solo su hash. La agregación ocurre íntegra en la base de datos: devuelve
    como máximo ``dias`` filas para la serie y ``PAGINAS_TOP`` para cada lista,
    en lugar de transferir toda la tabla ``visitas_pagina`` por red.
    """
    ventana = max(int(dias or 30), 1)
    vacio = {
        "dias": ventana,
        "visitantes_hoy": 0,
        "visitantes_7d": 0,
        "visitantes_ventana": 0,
        "vistas_hoy": 0,
        "vistas_ventana": 0,
        "serie": [],
        "paginas_top": [],
        "referentes_top": [],
        "disponible": False,
    }

    hoy_fecha = _a_fecha(hoy) or date.today()
    desde = hoy_fecha - timedelta(days=ventana - 1)
    desde_utc = _inicio_dia(desde)
    hasta_utc = _inicio_dia(hoy_fecha + timedelta(days=1))
    filtros = (
        VisitaPagina.created_at.isnot(None),
        VisitaPagina.created_at >= desde_utc,
        VisitaPagina.created_at < hasta_utc,
        or_(
            VisitaPagina.ruta.is_(None),
            ~VisitaPagina.ruta.like("/idioma/%"),
        ),
        func.coalesce(VisitaPagina.ruta, "") != "/idioma",
    )

    try:
        dia_expr = func.date(VisitaPagina.created_at)
        ip_expr = func.coalesce(VisitaPagina.ip_hash, "")
        filas_dia = (
            db.query(
                dia_expr.label("dia"),
                func.count().label("vistas"),
                func.count(func.distinct(ip_expr)).label("visitantes"),
            )
            .filter(*filtros)
            .group_by(dia_expr)
            .all()
        )
        if not filas_dia:
            return {**vacio, "disponible": True}

        ruta_limpia = func.trim(func.coalesce(VisitaPagina.ruta, ""))
        ruta_expr = case((ruta_limpia == "", "/"), else_=ruta_limpia)
        filas_paginas = (
            db.query(
                ruta_expr.label("ruta"),
                func.count().label("vistas"),
            )
            .filter(*filtros)
            .group_by(ruta_expr)
            .order_by(func.count().desc(), ruta_expr.asc())
            .limit(PAGINAS_TOP)
            .all()
        )

        filas_referentes = (
            db.query(
                VisitaPagina.referente.label("origen"),
                func.count().label("visitas"),
            )
            .filter(
                *filtros,
                VisitaPagina.referente.isnot(None),
                VisitaPagina.referente != "",
            )
            .group_by(VisitaPagina.referente)
            .order_by(func.count().desc(), VisitaPagina.referente.asc())
            .limit(PAGINAS_TOP)
            .all()
        )
    except Exception:
        # Tabla sin migrar o base no disponible: el panel sigue sin este
        # bloque, sin romper el resto de la analítica. El rollback es
        # obligatorio: sin él la sesión queda en transacción abortada y
        # cualquier consulta posterior falla con
        # ``psycopg.errors.InFailedSqlTransaction`` (el bug que tiraba
        # /admin/analitica entera cuando la tabla visitas_pagina no existe).
        try:
            db.rollback()
        except Exception:
            pass
        return vacio

    vistas_por_dia: dict[date, int] = {}
    visitantes_por_dia: dict[date, int] = {}
    for dia_raw, vistas_raw, visitantes_raw in filas_dia:
        dia = _a_fecha(dia_raw)
        if dia is None:
            continue
        vistas_por_dia[dia] = vistas_por_dia.get(dia, 0) + int(vistas_raw or 0)
        visitantes_por_dia[dia] = visitantes_por_dia.get(dia, 0) + int(visitantes_raw or 0)

    if not vistas_por_dia:
        return {**vacio, "disponible": True}

    serie = [
        {
            "fecha": d,
            "etiqueta": d.strftime("%d %b"),
            "visitantes": visitantes_por_dia.get(d, 0),
            "vistas": vistas_por_dia.get(d, 0),
        }
        for d in _dias_de_serie(desde, hoy_fecha)
    ]

    hace_7dias = hoy_fecha - timedelta(days=6)
    visitantes_ventana = sum(visitantes_por_dia.values())
    visitantes_7d = sum(
        n for d, n in visitantes_por_dia.items() if d >= hace_7dias
    )

    return {
        "dias": ventana,
        "visitantes_hoy": visitantes_por_dia.get(hoy_fecha, 0),
        "visitantes_7d": visitantes_7d,
        "visitantes_ventana": visitantes_ventana,
        "vistas_hoy": vistas_por_dia.get(hoy_fecha, 0),
        "vistas_ventana": sum(vistas_por_dia.values()),
        "serie": serie,
        "paginas_top": [
            {"ruta": _pagina_etiqueta(ruta), "vistas": int(n or 0)}
            for ruta, n in filas_paginas
        ],
        "referentes_top": [
            {"origen": str(origen), "visitas": int(n or 0)}
            for origen, n in filas_referentes
            if origen
        ],
        "disponible": True,
    }


def purgar_visitas_audiencia(
    db, *, dias: int | None = None, hoy: date | datetime | None = None
) -> dict:
    """Elimina filas antiguas y rutas excluidas de ``visitas_pagina``.

    Se ejecuta en ``/api/cron/mantenimiento`` para que la tabla no crezca sin
    techo en disco. Si ``dias == 0``, no se aplica corte por antigüedad.
    """
    retencion = retencion_audiencia_dias() if dias is None else max(0, int(dias))
    if retencion == 0:
        return {"ok": True, "omitido": "retención desactivada", "eliminadas": 0}

    hoy_fecha = _a_fecha(hoy) or date.today()
    corte = _inicio_dia(hoy_fecha - timedelta(days=retencion))
    try:
        eliminadas = (
            db.query(VisitaPagina)
            .filter(
                or_(
                    VisitaPagina.created_at.is_(None),
                    VisitaPagina.created_at < corte,
                    VisitaPagina.ruta == "/idioma",
                    VisitaPagina.ruta.like("/idioma/%"),
                )
            )
            .delete(synchronize_session=False)
        )
        db.commit()
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        logger.warning(
            "No se pudo podar visitas_pagina (¿migración pendiente?).",
            exc_info=True,
        )
        return {"ok": True, "omitido": "tabla no disponible", "eliminadas": 0}

    if eliminadas:
        logger.info(
            "Poda de audiencia: %d fila(s) eliminadas (retención %d días).",
            eliminadas,
            retencion,
        )
    return {
        "ok": True,
        "eliminadas": int(eliminadas or 0),
        "retencion_dias": retencion,
    }
