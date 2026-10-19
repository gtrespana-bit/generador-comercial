"""Diagnóstico rápido de calidad de precios del catálogo de partidas.

El resultado solo muestra los datos accionables del catálogo. En una sesión
SQLAlchemy real se calcula con agregados en la base de datos para no traer
miles de fichas a Python en cada visita a /partidas; el recorrido Python queda
como fallback para implementaciones ligeras usadas por herramientas y tests.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session

from ..models import Partida

MARGEN_MINIMO_CATALOGO = 20.0
DIAS_SIN_REVISION = 90


def _coste(p: Partida) -> float:
    return round(
        float(p.coste_materiales or 0)
        + float(p.coste_mano_obra or 0)
        + float(p.coste_complementarios or 0)
        + float(p.coste_otros or 0),
        2,
    )


def _tiene_tiempo(p: Partida) -> bool:
    return any(
        (getattr(p, campo, None) or 0) > 0
        for campo in (
            "tiempo_estimado_horas",
            "tiempo_oficial_horas",
            "tiempo_ayudante_horas",
            "tiempo_equipo_horas",
        )
    )


def _metricas_sql(db: Session) -> tuple[int, int, int, int, int, int]:
    """Una fila agregada sustituye la carga de todos los registros activos."""
    precio = func.coalesce(Partida.precio_unitario, 0.0)
    coste = (
        func.coalesce(Partida.coste_materiales, 0.0)
        + func.coalesce(Partida.coste_mano_obra, 0.0)
        + func.coalesce(Partida.coste_complementarios, 0.0)
        + func.coalesce(Partida.coste_otros, 0.0)
    )
    tiempo_positivo = or_(
        func.coalesce(Partida.tiempo_estimado_horas, 0.0) > 0,
        func.coalesce(Partida.tiempo_oficial_horas, 0.0) > 0,
        func.coalesce(Partida.tiempo_ayudante_horas, 0.0) > 0,
        func.coalesce(Partida.tiempo_equipo_horas, 0.0) > 0,
    )
    limite_fecha = datetime.utcnow() - timedelta(days=DIAS_SIN_REVISION)
    margen_bajo = (
        (precio > 0)
        & (coste > 0)
        & (((precio - coste) / func.nullif(precio, 0) * 100) < MARGEN_MINIMO_CATALOGO)
    )
    fecha_revision = func.coalesce(
        Partida.fecha_actualizacion_precio,
        Partida.created_at,
    )
    fila = (
        db.query(
            func.count(Partida.id),
            func.coalesce(func.sum(case((precio > 0, 1), else_=0)), 0),
            func.coalesce(func.sum(case((coste > 0, 1), else_=0)), 0),
            func.coalesce(func.sum(case((tiempo_positivo, 1), else_=0)), 0),
            func.coalesce(func.sum(case((margen_bajo, 1), else_=0)), 0),
            func.coalesce(func.sum(case((fecha_revision < limite_fecha, 1), else_=0)), 0),
        )
        .filter(Partida.oculta.is_(False))
        .one()
    )
    return tuple(int(valor or 0) for valor in fila)


def _metricas_python(db) -> tuple[int, int, int, int, int, int]:
    """Fallback compatible con sesiones pequeñas o dobles de prueba."""
    from sqlalchemy.orm import load_only

    consulta = db.query(Partida)
    if hasattr(consulta, "options"):
        try:
            consulta = consulta.options(load_only(
                Partida.precio_unitario,
                Partida.coste_materiales,
                Partida.coste_mano_obra,
                Partida.coste_complementarios,
                Partida.coste_otros,
                Partida.tiempo_estimado_horas,
                Partida.tiempo_oficial_horas,
                Partida.tiempo_ayudante_horas,
                Partida.tiempo_equipo_horas,
                Partida.fecha_actualizacion_precio,
                Partida.created_at,
                Partida.oculta,
            ))
        except Exception:
            pass
    if hasattr(consulta, "filter"):
        consulta = consulta.filter(Partida.oculta.is_(False))
    partidas = consulta.all()
    limite_fecha = datetime.utcnow() - timedelta(days=DIAS_SIN_REVISION)
    total = con_precio = con_coste = con_tiempo = margen_bajo = desactualizadas = 0
    for partida in partidas:
        total += 1
        precio = float(partida.precio_unitario or 0)
        coste = _coste(partida)
        if precio > 0:
            con_precio += 1
        if coste > 0:
            con_coste += 1
        if _tiene_tiempo(partida):
            con_tiempo += 1
        if precio > 0 and coste > 0 and (precio - coste) / precio * 100 < MARGEN_MINIMO_CATALOGO:
            margen_bajo += 1
        fecha = partida.fecha_actualizacion_precio or partida.created_at
        if fecha and fecha < limite_fecha:
            desactualizadas += 1
    return total, con_precio, con_coste, con_tiempo, margen_bajo, desactualizadas


def analizar_salud_catalogo(db: Session, incluir_anomalias: bool = True) -> dict:
    """Resume salud y cobertura sin hidratar el catálogo completo en el hot path."""
    if isinstance(db, Session):
        metricas = _metricas_sql(db)
    else:
        metricas = _metricas_python(db)
    total, con_precio, con_coste, con_tiempo, n_margen_bajo, n_desactualizadas = metricas

    if incluir_anomalias:
        from .precios_anomalos import contar_precios_anomalos
        precios_absurdos = contar_precios_anomalos(db)
    else:
        precios_absurdos = 0

    sin_precio = total - con_precio
    sin_coste = total - con_coste
    sin_tiempo = total - con_tiempo
    if total:
        # Pesos simples: precio y coste son lo más crítico; tiempo y revisión
        # completan la confianza sin convertirlo en auditoría pesada.
        score = round(
            (con_precio / total) * 35
            + (con_coste / total) * 35
            + (con_tiempo / total) * 20
            + ((total - n_desactualizadas) / total) * 10
        )
    else:
        score = 0

    if score >= 85:
        estado = "ok"
        titulo = "Catálogo sano"
    elif score >= 65:
        estado = "revisar"
        titulo = "Catálogo utilizable, con puntos a revisar"
    else:
        estado = "riesgo"
        titulo = "Catálogo con datos críticos pendientes"

    problemas = [
        {"clave": "sin_precio", "label": "Sin precio", "count": sin_precio, "url": "/partidas?salud=sin_precio"},
        {"clave": "sin_coste", "label": "Sin coste", "count": sin_coste, "url": "/partidas?salud=sin_coste"},
        {"clave": "margen_bajo", "label": "Margen bajo", "count": n_margen_bajo, "url": "/partidas?salud=margen_bajo"},
        {"clave": "sin_tiempo", "label": "Sin tiempo", "count": sin_tiempo, "url": "/partidas?salud=sin_tiempo"},
        {"clave": "desactualizadas", "label": f"> {DIAS_SIN_REVISION} días", "count": n_desactualizadas, "url": "/partidas?salud=desactualizadas"},
        {"clave": "precio_absurdo", "label": "Precio imposible", "count": precios_absurdos, "url": "/partidas?salud=precio_absurdo"},
    ]
    problemas_visibles = [problema for problema in problemas if problema["count"] > 0]

    return {
        "score": score,
        "estado": estado,
        "titulo": titulo,
        "total": total,
        "con_precio": con_precio,
        "con_coste": con_coste,
        "con_tiempo": con_tiempo,
        "sin_precio": sin_precio,
        "sin_coste": sin_coste,
        "sin_tiempo": sin_tiempo,
        "margen_bajo": n_margen_bajo,
        "desactualizadas": n_desactualizadas,
        # Precios que solo se explican por una conversión de moneda aplicada de
        # más: se ofrecen con un botón de reparación en la vista de catálogo.
        "precio_absurdo": precios_absurdos,
        "problemas": problemas,
        "problemas_visibles": problemas_visibles,
        "requiere_atencion": bool(problemas_visibles),
        "margen_minimo": MARGEN_MINIMO_CATALOGO,
        "dias_sin_revision": DIAS_SIN_REVISION,
    }
