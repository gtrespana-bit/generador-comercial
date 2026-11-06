"""Audiencia de la capa pública: visitantes y páginas vistas por día.

Mide lo que Google Analytics 4 ve por fuera (tráfico, páginas, origen) pero
con un dato propio del servidor, sin cookies y sin terceros, desligado de
cuentas. Cada visita de página deja una fila en ``visitas_pagina`` a través
de ``app.main.AudienciaMiddleware``; este servicio solo agrega esas filas para
pintar el panel de analítica.

Todas las funciones son best-effort: si la tabla aún no existe (migración
pendiente) o la lectura falla, devuelven vacíos en lugar de tirar el panel.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta

from ..models import VisitaPagina

#: Páginas más vistas que se enseñan en el panel.
PAGINAS_TOP = 8


def _inicio_dia(dia: date) -> datetime:
    return datetime.combine(dia, time.min)


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


def resumen_audiencia(db, *, dias: int = 30, hoy: date | None = None) -> dict:
    """Visitantes únicos y páginas vistas por día en la ventana.

    Un visitante = un ``ip_hash`` distinto en un día. Nunca se guarda la IP,
    solo su hash.
    """
    vacio = {
        "dias": max(int(dias or 30), 1),
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
    try:
        filas = (
            db.query(
                VisitaPagina.ruta,
                VisitaPagina.ip_hash,
                VisitaPagina.referente,
                VisitaPagina.created_at,
            )
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

    hoy = hoy or date.today()
    ventana = max(int(dias or 30), 1)
    desde = hoy - timedelta(days=ventana - 1)
    desde_utc = _inicio_dia(desde)

    visitas = [f for f in filas if f.created_at and f.created_at >= desde_utc]
    if not visitas:
        return {**vacio, "disponible": True}

    vistas_por_dia: dict[date, int] = defaultdict(int)
    visitantes_por_dia: dict[date, set[str]] = defaultdict(set)
    paginas = Counter()
    referentes = Counter()
    ips_hoy: set[str] = set()
    vistas_hoy = 0
    inicio_hoy = _inicio_dia(hoy)
    hace_7dias = _inicio_dia(hoy - timedelta(days=6))

    for ruta, ip_hash, referente, creado in visitas:
        dia = creado.date()
        vistas_por_dia[dia] += 1
        visitantes_por_dia[dia].add(ip_hash or "")
        paginas[_pagina_etiqueta(ruta)] += 1
        if referente:
            referentes[str(referente)] += 1
        if creado >= inicio_hoy:
            vistas_hoy += 1
            ips_hoy.add(ip_hash or "")

    serie = [
        {
            "fecha": d,
            "etiqueta": d.strftime("%d %b"),
            "visitantes": len(visitantes_por_dia.get(d, ())),
            "vistas": vistas_por_dia.get(d, 0),
        }
        for d in _dias_de_serie(desde, hoy)
    ]

    visitantes_ventana = sum(len(s) for s in visitantes_por_dia.values())
    visitantes_7d = sum(
        len(s) for d, s in visitantes_por_dia.items() if d >= hace_7dias.date()
    )

    return {
        "dias": ventana,
        "visitantes_hoy": len(ips_hoy),
        "visitantes_7d": visitantes_7d,
        "visitantes_ventana": visitantes_ventana,
        "vistas_hoy": vistas_hoy,
        "vistas_ventana": sum(vistas_por_dia.values()),
        "serie": serie,
        "paginas_top": [
            {"ruta": ruta, "vistas": n}
            for ruta, n in paginas.most_common(PAGINAS_TOP)
        ],
        "referentes_top": [
            {"origen": origen, "visitas": n}
            for origen, n in referentes.most_common(PAGINAS_TOP)
        ],
        "disponible": True,
    }
