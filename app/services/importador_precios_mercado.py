"""Importador seguro de la matriz nacional de precios.

Por defecto solo procesa filas con precio y no crea overrides de empresa.
Las filas pendientes se reportan y no se convierten en precios cero.
"""
from __future__ import annotations
import csv
from pathlib import Path
from sqlalchemy.orm import Session
from ..models import Recurso
from .precios_mercado import guardar_precio


def importar_matriz_csv(db: Session, ruta: str | Path, *, aplicar: bool = False, incluir_respaldo: bool = False) -> dict:
    ruta = Path(ruta)
    resultado = {"filas": 0, "aplicables": 0, "creadas_o_actualizadas": 0, "pendientes": 0, "no_encontrados": 0, "errores": []}
    recursos = {r.codigo.strip(): r for r in db.query(Recurso).all() if r.codigo}
    with ruta.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh, delimiter=";")
        for row in reader:
            resultado["filas"] += 1
            precio_raw = str(row.get("precio_referencia") or "").strip()
            if not precio_raw or (row.get("origen") == "base" and not incluir_respaldo):
                resultado["pendientes"] += 1
                continue
            recurso = recursos.get(str(row.get("codigo_recurso") or "").strip())
            if recurso is None:
                resultado["no_encontrados"] += 1
                continue
            try:
                precio = float(precio_raw)
                if precio < 0:
                    raise ValueError("precio negativo")
            except ValueError as exc:
                resultado["errores"].append(f"{row.get('codigo_recurso')}: {exc}")
                continue
            resultado["aplicables"] += 1
            if aplicar:
                guardar_precio(
                    db, recurso.id, row["pais_codigo"], precio, row["moneda"],
                    fuente=row.get("fuente") or "Matriz nacional",
                    confianza=row.get("confianza") or "referencia",
                    fecha_vigencia=None,
                )
                resultado["creadas_o_actualizadas"] += 1
    if aplicar:
        db.commit()
    return resultado
