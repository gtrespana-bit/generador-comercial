#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Corrige el uso indebido de MT-SOPORTE-AC (soporte de condensadora de aire
acondicionado) en partidas que no son de climatización.

Durante la ampliación se copió MT-SOPORTE-AC en partidas de espejos, vidrios
decorativos y aislamiento de vibraciones. Se sustituye por el recurso
correcto:

- Espejos y vidrios decorativos -> MT-PERNO-ANCLA (fijación mecánica).
- Aislamiento de vibraciones   -> MT-SOPORTE-ANTIVIB (silent block de neopreno).

El soporte de condensadora se conserva en 08.03 / 08.06 / 09.07 (uso correcto).

Uso:
    python3 tools/corregir_soporte_ac.py --aplicar
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
ORIGEN = BASE / "basedatos_partidas" / "datos" / "descompuestos"
RECURSOS = BASE / "basedatos_partidas" / "datos" / "recursos.json"

# codigo -> recurso correcto en lugar de MT-SOPORTE-AC
SUSTITUCIONES = {
    "07.06.01.070": "MT-PERNO-ANCLA",  # espejo de pared
    "07.06.01.190": "MT-PERNO-ANCLA",  # espejo de vestir
    "12.04.01.130": "MT-PERNO-ANCLA",  # revestimiento de espejo
    "12.04.01.190": "MT-PERNO-ANCLA",  # vidrio decorativo lacado
    "10.02.02.060": "MT-SOPORTE-ANTIVIB",  # aislamiento de vibraciones
}


def _asegurar_recurso_antivib() -> None:
    """Crea MT-SOPORTE-ANTIVIB si no existe (silent block de neopreno)."""
    bruto = json.loads(RECURSOS.read_text(encoding="utf-8"))
    materiales = bruto["materiales"]
    if "MT-SOPORTE-ANTIVIB" in materiales:
        return
    materiales["MT-SOPORTE-ANTIVIB"] = {
        "unidad": "ud",
        "descripcion": (
            "Soporte antivibratorio de neopreno (silent block) para aislar "
            "equipos de bombas, compresores y maquinaria, con su tornillería."
        ),
        "precio": 5.0,
        "estado": "provisional",
    }
    RECURSOS.write_text(json.dumps(bruto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    if not args.aplicar:
        print("Modo seco. Usa --aplicar para escribir.")
        for codigo, ref in SUSTITUCIONES.items():
            print(f"  {codigo}: MT-SOPORTE-AC -> {ref}")
        return 0

    _asegurar_recurso_antivib()
    cambiadas = 0
    for ruta in sorted(ORIGEN.glob("*.json")):
        partida = json.loads(ruta.read_text(encoding="utf-8"))
        codigo = partida.get("codigo", "")
        if codigo not in SUSTITUCIONES:
            continue
        recursos = partida.get("recursos", [])
        for r in recursos:
            if r.get("ref") == "MT-SOPORTE-AC":
                r["ref"] = SUSTITUCIONES[codigo]
        partida["recursos"] = recursos
        ruta.write_text(json.dumps(partida, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        cambiadas += 1
        print(f"  {codigo}: MT-SOPORTE-AC -> {SUSTITUCIONES[codigo]}")

    print(f"Corregidas {cambiadas} partidas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
