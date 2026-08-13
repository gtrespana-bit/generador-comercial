"""Análisis interno de precios del catálogo propio.

Este módulo reemplaza el antiguo botón de "Optimización Asistida" que sólo
mostraba un mensaje fijo (no consultaba ninguna base de datos ni servicio
externo). En su lugar, analiza el catálogo de partidas que el propio negocio
ya cargó: compara el precio de venta contra el costo interno (materiales +
mano de obra + complementarios + otros) para detectar partidas con margen
bajo o con el precio sin revisar hace mucho tiempo.

No hay ninguna fuente de datos externa ni "mercado global": todo sale de la
información que el usuario ya introdujo en /partidas.
"""
from datetime import datetime

from sqlalchemy.orm import Session

from ..models import Partida

MARGEN_MINIMO_PCT = 15.0
DIAS_SIN_REVISAR = 180


def analizar_catalogo_partidas(
    db: Session,
    margen_minimo: float = MARGEN_MINIMO_PCT,
    dias_desactualizado: int = DIAS_SIN_REVISAR,
) -> dict:
    """Analiza app.models.Partida (catálogo propio) y devuelve alertas reales.

    Una partida sólo se evalúa si tiene datos de costo interno cargados
    (materiales/mano de obra/complementarios/otros); si no los tiene, no se
    puede saber su margen y se cuenta aparte como "sin datos de costo".
    """
    partidas = db.query(Partida).order_by(Partida.categoria, Partida.nombre).all()
    ahora = datetime.utcnow()

    alertas = []
    margenes = []

    for p in partidas:
        coste_unit = (
            (p.coste_materiales or 0)
            + (p.coste_mano_obra or 0)
            + (p.coste_complementarios or 0)
            + (p.coste_otros or 0)
        )
        if coste_unit <= 0 or not p.precio_unitario:
            continue

        coste_unit *= 1 + (p.desperdicio_recomendado_pct or 0) / 100
        margen_pct = round((p.precio_unitario - coste_unit) / p.precio_unitario * 100, 1)
        margenes.append(margen_pct)

        motivos = []
        if margen_pct < margen_minimo:
            motivos.append(f"Margen de {margen_pct}% (por debajo del {margen_minimo:.0f}% de referencia)")

        fecha_precio = p.fecha_actualizacion_precio or p.created_at
        dias = (ahora - fecha_precio).days if fecha_precio else None
        if dias is not None and dias > dias_desactualizado:
            motivos.append(f"Precio sin revisar hace {dias} días")

        if motivos:
            alertas.append(
                {
                    "id": p.id,
                    "nombre": p.nombre,
                    "categoria": p.categoria or "General",
                    "precio_unitario": round(p.precio_unitario, 2),
                    "coste_unitario": round(coste_unit, 2),
                    "margen_pct": margen_pct,
                    "motivos": motivos,
                }
            )

    alertas.sort(key=lambda a: a["margen_pct"])

    por_categoria: dict[str, int] = {}
    for a in alertas:
        por_categoria[a["categoria"]] = por_categoria.get(a["categoria"], 0) + 1
    categoria_mas_afectada = max(por_categoria, key=por_categoria.get) if por_categoria else None

    return {
        "total_partidas": len(partidas),
        "evaluadas": len(margenes),
        "sin_datos_costo": len(partidas) - len(margenes),
        "alertas": alertas,
        "margen_promedio": round(sum(margenes) / len(margenes), 1) if margenes else None,
        "margen_minimo": margen_minimo,
        "dias_desactualizado": dias_desactualizado,
        "categoria_mas_afectada": categoria_mas_afectada,
    }
