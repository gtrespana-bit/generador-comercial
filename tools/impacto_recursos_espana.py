#!/usr/bin/env python3
"""Mide el efecto de un cambio de precios de recursos sobre las partidas.

Compara dos versiones de la matriz de precios de España (antes y después de un
lote de cambios: el modelo de maquinaria o las convenciones de medida) y propaga
la diferencia de cada recurso a las partidas que lo consumen, usando el rendimiento del
descompuesto y el porcentaje de complementarios del propio descompuesto.

Escribe una fila por partida afectada y resume el efecto por máquina. No toca
el catálogo ni la base de datos: es un informe de impacto.

Uso:
    python tools/impacto_recursos_espana.py
    python tools/impacto_recursos_espana.py --antes ruta.csv --despues ruta.csv
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DOC = RAIZ / "docs/auditoria_precios"
FECHA = "2026-11-07"
DESPUES = RAIZ / "basedatos_partidas/salida/precios_recursos_espana.csv"
SALIDA = DOC / f"espana_impacto_lote_{FECHA}.csv"
DESCOMPUESTOS = RAIZ / "basedatos_partidas/datos/descompuestos"
PUBLICOS = RAIZ / "basedatos_partidas/datos/precios_publicos/ES.json"


def leer_precios(path: Path) -> dict[str, Decimal]:
    with path.open(encoding="utf-8-sig", newline="") as manejador:
        return {fila["codigo_recurso"]: Decimal(fila["precio_referencia"])
                for fila in csv.DictReader(manejador, delimiter=";")}


def leer_usos() -> dict[str, list[tuple[str, Decimal, Decimal]]]:
    """Devuelve, por recurso, la lista de (partida, rendimiento, complementarios %)."""
    usos: dict[str, list[tuple[str, Decimal, Decimal]]] = defaultdict(list)
    for ruta in sorted(DESCOMPUESTOS.glob("*.json")):
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        compl = Decimal(str(datos.get("complementarios_pct") or 0))
        for recurso in datos.get("recursos", []):
            rendimiento = Decimal(str(recurso.get("rendimiento") or 0))
            if rendimiento:
                usos[recurso["ref"]].append((datos["codigo"], rendimiento, compl))
    return usos


def precios_partida() -> dict[str, Decimal]:
    datos = json.loads(PUBLICOS.read_text(encoding="utf-8"))
    return {partida["codigo"]: Decimal(str(partida["pu"]))
            for partida in datos["partidas"].values()}


def main() -> int:
    analizador = argparse.ArgumentParser(description=__doc__)
    analizador.add_argument("--antes", type=Path, required=True,
                            help="matriz previa al modelo de maquinaria")
    analizador.add_argument("--despues", type=Path, default=DESPUES)
    analizador.add_argument("--salida", type=Path, default=SALIDA)
    analizador.add_argument("--prefijo", action="append", default=None,
                            help="prefijo de los recursos a medir (repetible). "
                                 "Por defecto, todos los que cambien.")
    argumentos = analizador.parse_args()

    antes = leer_precios(argumentos.antes)
    despues = leer_precios(argumentos.despues)
    usos = leer_usos()
    pu = precios_partida()

    prefijos = argumentos.prefijo
    cambiados = {codigo for codigo in antes
                 if antes[codigo] != despues.get(codigo)
                 and (not prefijos or any(codigo.startswith(p) for p in prefijos))}
    deltas_partida: dict[str, list[tuple[str, Decimal, Decimal]]] = defaultdict(list)
    por_maquina: dict[str, dict] = {}
    for codigo in sorted(cambiados):
        delta = despues[codigo] - antes[codigo]
        afectadas = usos.get(codigo, [])
        efecto = sum(rendimiento * delta * (1 + compl / 100)
                     for _, rendimiento, compl in afectadas)
        por_maquina[codigo] = {"antes": antes[codigo], "despues": despues[codigo],
                               "delta": delta, "partidas": len(afectadas),
                               "efecto": efecto}
        for partida, rendimiento, compl in afectadas:
            deltas_partida[partida].append((codigo, rendimiento * delta * (1 + compl / 100),
                                            rendimiento))

    filas = []
    for partida in sorted(deltas_partida):
        delta = sum(d for _, d, _ in deltas_partida[partida])
        base = pu.get(partida)
        if base is None or base == 0:
            continue
        filas.append({
            "codigo_partida": partida,
            "precio_actual_eur": f"{base:.2f}",
            "delta_eur": f"{delta:.2f}",
            "delta_pct": f"{(delta / base * 100):.1f}",
            "maquinas": " ".join(sorted({c for c, _, _ in deltas_partida[partida]})),
        })
    filas.sort(key=lambda fila: float(fila["delta_pct"]))
    with argumentos.salida.open("w", encoding="utf-8-sig", newline="") as manejador:
        escritor = csv.DictWriter(manejador, fieldnames=list(filas[0]), delimiter=";",
                                  lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(filas)

    print(f"{len(cambiados)} recursos con precio nuevo; {len(filas)} partidas afectadas")
    for codigo, datos in sorted(por_maquina.items(),
                                key=lambda par: par[1]["efecto"]):
        print(f"  {codigo:16} {datos['antes']:>9} → {datos['despues']:>6} EUR/ud | "
              f"{datos['partidas']:>4} partidas | efecto {datos['efecto']:>9.2f} EUR")
    if filas:
        valores = [float(fila["delta_pct"]) for fila in filas]
        print(f"  variación por partida: mínima {min(valores):.1f} %, "
              f"mediana {sorted(valores)[len(valores) // 2]:.1f} %, "
              f"máxima {max(valores):.1f} %")
    destino = argumentos.salida if argumentos.salida.is_absolute() else RAIZ / argumentos.salida
    print(f"Escrito {destino.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
