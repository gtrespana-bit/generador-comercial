#!/usr/bin/env python3
"""Previsualiza o importa la matriz nacional de precios LatAm.

Uso seguro por defecto:
  python tools/importar_precios_mercado.py

Aplicación explícita a la base configurada:
  python tools/importar_precios_mercado.py --apply
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.database import SessionLocal, init_db
init_db()
from app.services.importador_precios_mercado import importar_matriz_csv

ROOT = Path(__file__).resolve().parents[1]
MATRIZ = ROOT / "basedatos_partidas/salida/precios_recursos_latam.csv"

parser = argparse.ArgumentParser()
parser.add_argument("--apply", action="store_true", help="guardar precios; sin esta opción solo hace dry-run")
parser.add_argument("--csv", type=Path, default=MATRIZ)
args = parser.parse_args()

db = SessionLocal()
try:
    resultado = importar_matriz_csv(db, args.csv, aplicar=args.apply)
    modo = "APLICADA" if args.apply else "DRY-RUN"
    print(modo, resultado)
finally:
    db.close()
