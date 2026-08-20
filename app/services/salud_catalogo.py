"""Salud simple del catálogo de partidas.

Diagnóstico intencionalmente compacto: no pretende auditar todo, solo señalar
lo que puede hacer que un presupuesto salga mal (sin precio, sin coste, sin
tiempo, margen bajo o precio viejo).
"""
from __future__ import annotations

from datetime import datetime, timedelta

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
        for campo in ("tiempo_estimado_horas", "tiempo_oficial_horas", "tiempo_ayudante_horas", "tiempo_equipo_horas")
    )


def analizar_salud_catalogo(db: Session) -> dict:
    partidas = db.query(Partida).filter(Partida.oculta.is_(False)).all()
    total = len(partidas)
    limite_fecha = datetime.utcnow() - timedelta(days=DIAS_SIN_REVISION)

    sin_precio = []
    sin_coste = []
    sin_tiempo = []
    margen_bajo = []
    desactualizadas = []
    con_precio = con_coste = con_tiempo = 0

    for p in partidas:
      precio = float(p.precio_unitario or 0)
      coste = _coste(p)
      tiempo_ok = _tiene_tiempo(p)

      if precio > 0:
          con_precio += 1
      else:
          sin_precio.append(p)

      if coste > 0:
          con_coste += 1
      else:
          sin_coste.append(p)

      if tiempo_ok:
          con_tiempo += 1
      else:
          sin_tiempo.append(p)

      if precio > 0 and coste > 0:
          margen = (precio - coste) / precio * 100
          if margen < MARGEN_MINIMO_CATALOGO:
              margen_bajo.append(p)

      fecha = p.fecha_actualizacion_precio or p.created_at
      if fecha and fecha < limite_fecha:
          desactualizadas.append(p)

    if total:
        # Pesos simples: precio y coste son lo más crítico; tiempo y revisión
        # completan la confianza sin convertirlo en auditoría pesada.
        score = round(
            (con_precio / total) * 35
            + (con_coste / total) * 35
            + (con_tiempo / total) * 20
            + ((total - len(desactualizadas)) / total) * 10
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
        {"clave": "sin_precio", "label": "Sin precio", "count": len(sin_precio), "url": "/partidas?salud=sin_precio"},
        {"clave": "sin_coste", "label": "Sin coste", "count": len(sin_coste), "url": "/partidas?salud=sin_coste"},
        {"clave": "margen_bajo", "label": "Margen bajo", "count": len(margen_bajo), "url": "/partidas?salud=margen_bajo"},
        {"clave": "sin_tiempo", "label": "Sin tiempo", "count": len(sin_tiempo), "url": "/partidas?salud=sin_tiempo"},
        {"clave": "desactualizadas", "label": f"> {DIAS_SIN_REVISION} días", "count": len(desactualizadas), "url": "/partidas?salud=desactualizadas"},
    ]
    problemas_visibles = [p for p in problemas if p["count"] > 0]

    return {
        "score": score,
        "estado": estado,
        "titulo": titulo,
        "total": total,
        "con_precio": con_precio,
        "con_coste": con_coste,
        "con_tiempo": con_tiempo,
        "sin_precio": len(sin_precio),
        "sin_coste": len(sin_coste),
        "sin_tiempo": len(sin_tiempo),
        "margen_bajo": len(margen_bajo),
        "desactualizadas": len(desactualizadas),
        "problemas": problemas,
        "problemas_visibles": problemas_visibles,
        "requiere_atencion": bool(problemas_visibles),
        "margen_minimo": MARGEN_MINIMO_CATALOGO,
        "dias_sin_revision": DIAS_SIN_REVISION,
    }
