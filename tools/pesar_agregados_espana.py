#!/usr/bin/env python3
"""Mide cuánto pesa cada recurso agregado en el coste de las partidas que lo usan.

Un recurso agregado («puntas, cinceles y discos») no se puede repreciar sin
inventar su contenido. Lo que sí se puede decidir con datos es *si merece la pena
recomponerlo*: para cada agregado se calcula, partida a partida, qué porcentaje
del coste directo representa (rendimiento × precio / coste directo) y se resume en
peso mediano y número de partidas por encima del 10 % y del 25 %.

Regla de decisión (la del informe `ESPANA_AGREGADOS_DECISION_2026-11-07.md`):

* ``recomponer`` — el peso mediano llega al 10 %, o llega al 5 % y al menos un
  tercio de las partidas supera el 10 %;
* ``documentar`` — el agregado existe pero su precio no mueve el de la partida;
* ``cerrado_por_modelo`` — ya tiene precio propio del modelo de maquinaria.

No toca precios ni descompuestos: solo mide y escribe el informe en CSV.

Uso:
    python tools/pesar_agregados_espana.py
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DOC = RAIZ / "docs/auditoria_precios"
FECHA = "2026-11-07"
MATRIZ = RAIZ / "basedatos_partidas/salida/precios_recursos_espana.csv"
DESCOMPUESTOS = RAIZ / "basedatos_partidas/datos/descompuestos"
PUBLICOS = RAIZ / "basedatos_partidas/datos/precios_publicos/ES.json"
SALIDA = DOC / f"espana_agregados_peso_{FECHA}.csv"

# Los 19 recursos que agrupan varios componentes bajo un solo precio.
AGREGADOS = (
    "MT-CONS-DEM", "MT-OXI-CONS", "MT-HERRAJE-CLOSET", "MT-HERRAJE-PUERTA",
    "MT-CONS-LIMP", "MT-PLO-ACC4", "MT-PLO-DESAG", "MT-PLO-ACC20", "MT-SELLA-PASE",
    "MT-CONS-PULIDO", "MT-SAN-FIJA", "MT-EPP", "MT-ACC-BOMBA", "MQ-RECUP-GAS",
    "MQ-PERF-PILOTE", "MQ-VENT-SUC", "MQ-ESTAMP", "MQ-RODILLO", "MQ-SOLDADORA",
)
# Recursos que en esta ronda ya han recibido precio del modelo de maquinaria.
CERRADOS = {"MQ-RODILLO", "MQ-SOLDADORA"}
UMBRAL = Decimal("10")
UMBRAL_MEDIO = Decimal("5")


def leer_precios() -> dict[str, Decimal]:
    with MATRIZ.open(encoding="utf-8-sig", newline="") as manejador:
        return {fila["codigo_recurso"]: Decimal(fila["precio_referencia"])
                for fila in csv.DictReader(manejador, delimiter=";")}


def leer_usos() -> dict[str, list[tuple[str, Decimal]]]:
    usos: dict[str, list[tuple[str, Decimal]]] = defaultdict(list)
    for ruta in sorted(DESCOMPUESTOS.glob("*.json")):
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        for recurso in datos.get("recursos", []):
            rendimiento = Decimal(str(recurso.get("rendimiento") or 0))
            if rendimiento:
                usos[recurso["ref"]].append((datos["codigo"], rendimiento))
    return usos


def leer_directos() -> dict[str, Decimal]:
    datos = json.loads(PUBLICOS.read_text(encoding="utf-8"))
    return {partida["codigo"]: Decimal(str(partida["directo"]))
            for partida in datos["partidas"].values()}


def decidir(mediana: Decimal, partidas: int, sobre_diez: int) -> str:
    if mediana >= UMBRAL:
        return "recomponer"
    if mediana >= UMBRAL_MEDIO and sobre_diez * 3 >= max(partidas, 1):
        return "recomponer"
    return "documentar"


def main() -> int:
    precios = leer_precios()
    usos = leer_usos()
    directos = leer_directos()

    filas = []
    for codigo in AGREGADOS:
        peso = []
        for partida, rendimiento in usos.get(codigo, []):
            base = directos.get(partida)
            if base:
                peso.append(rendimiento * precios.get(codigo, Decimal("0")) / base * 100)
        peso.sort()
        mediana = peso[len(peso) // 2] if peso else Decimal("0")
        sobre_diez = sum(1 for valor in peso if valor > UMBRAL)
        sobre_veinticinco = sum(1 for valor in peso if valor > 25)
        if codigo in CERRADOS:
            decision = "cerrado_por_modelo"
        else:
            decision = decidir(mediana, len(peso), sobre_diez)
        filas.append({
            "codigo_recurso": codigo,
            "precio_eur": f"{precios.get(codigo, Decimal('0')):.2f}",
            "usos": len(usos.get(codigo, [])),
            "peso_mediano_pct": f"{mediana:.1f}",
            "partidas_sobre_10_pct": sobre_diez,
            "partidas_sobre_25_pct": sobre_veinticinco,
            "decision": decision,
        })
    filas.sort(key=lambda fila: (-int(fila["partidas_sobre_10_pct"]),
                                 -float(fila["peso_mediano_pct"])))

    with SALIDA.open("w", encoding="utf-8-sig", newline="") as manejador:
        escritor = csv.DictWriter(manejador, fieldnames=list(filas[0]), delimiter=";",
                                  lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(filas)

    recomponer = [f for f in filas if f["decision"] == "recomponer"]
    print(f"{len(filas)} agregados medidos; {len(recomponer)} a recomponer")
    for fila in filas:
        print(f"  {fila['codigo_recurso']:20} {fila['usos']:>4} usos  "
              f"peso {fila['peso_mediano_pct']:>6} %  >10 %: {fila['partidas_sobre_10_pct']:>3}  "
              f"{fila['decision']}")
    print(f"Escrito {SALIDA.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
