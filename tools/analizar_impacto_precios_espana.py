#!/usr/bin/env python3
"""Impacto del cierre de precios de España sobre el coste de las partidas.

Recalcula el coste directo de cada partida del catálogo con la matriz **anterior**
y con la **actual**, usando exactamente la misma cascada que la aplicación
(importe = rendimiento × precio, redondeo a 2 decimales por recurso, subtotal por
grupo y complementarios), y escribe el delta por partida.

No modifica partidas ni precios: solo mide. Sirve para saber qué parte del
catálogo cambia antes de publicar presupuestos.

Uso:
    python tools/analizar_impacto_precios_espana.py \\
        --anterior /tmp/precios_recursos_espana_antes.csv \\
        --salida docs/auditoria_precios/espana_impacto_partidas_2026-11-07.csv

Para obtener la matriz anterior sin tocar el árbol de trabajo:

    git show HEAD:basedatos_partidas/salida/precios_recursos_espana.csv \\
        > /tmp/precios_recursos_espana_antes.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path

if __package__:
    from .analizar_beneficio_por_pais import cargar_recursos, precio_efectivo, r2
else:
    from analizar_beneficio_por_pais import cargar_recursos, precio_efectivo, r2

ROOT = Path(__file__).resolve().parents[1]
MATRIZ = ROOT / "basedatos_partidas/salida/precios_recursos_espana.csv"
DESCOMPUESTOS = ROOT / "basedatos_partidas/datos/descompuestos"
SALIDA = ROOT / "docs/auditoria_precios/espana_impacto_partidas_2026-11-07.csv"
PAIS = "ES"


def cargar_matriz(path: Path) -> dict[str, tuple[float, str]]:
    """{codigo_recurso: (precio, moneda)} del país español."""
    precios: dict[str, tuple[float, str]] = {}
    with Path(path).open(encoding="utf-8-sig", newline="") as manejador:
        for fila in csv.DictReader(manejador, delimiter=";"):
            if fila["pais_codigo"] != PAIS:
                continue
            try:
                precios[fila["codigo_recurso"]] = (float(fila["precio_referencia"]),
                                                   fila["moneda"])
            except (TypeError, ValueError, KeyError):
                continue
    return precios


def coste(partida: dict, fichas: dict, precios: dict[str, tuple[float, str]]) -> float | None:
    """Misma cascada que la aplicación, con el mapa de precios directo.

    ``precio_efectivo`` espera el mapa del país (no el anidado por país).
    """
    if not partida.get("recursos"):
        return None
    subtotal_grupo: dict[str, float] = {}
    for linea in partida["recursos"]:
        ficha = fichas.get(linea["ref"])
        if ficha is None:
            continue
        precio = precio_efectivo(linea["ref"], fichas, precios, frozenset())
        if precio is None:
            continue
        importe = r2(float(linea["rendimiento"]) * precio)
        grupo = ficha["grupo"]
        subtotal_grupo[grupo] = r2(subtotal_grupo.get(grupo, 0.0) + importe)
    base = 0.0
    for suma in subtotal_grupo.values():
        base = r2(base + suma)
    porcentaje = float(partida.get("complementarios_pct", 0) or 0)
    complementarios = r2(base * porcentaje / 100) if porcentaje else 0.0
    total = base + complementarios
    return total if total > 0 else None


def main() -> int:
    analizador = argparse.ArgumentParser(description=__doc__)
    analizador.add_argument("--anterior", type=Path, required=True,
                            help="matriz de precios anterior (CSV con ';')")
    analizador.add_argument("--actual", type=Path, default=MATRIZ)
    analizador.add_argument("--salida", type=Path, default=SALIDA)
    argumentos = analizador.parse_args()

    fichas = cargar_recursos()
    previos, actuales = cargar_matriz(argumentos.anterior), cargar_matriz(argumentos.actual)
    if set(previos) != set(actuales):
        raise SystemExit("Las dos matrices no cubren los mismos recursos")
    cambiados = {c for c in previos if previos[c][0] != actuales[c][0]}

    filas, deltas = [], []
    for ruta in sorted(DESCOMPUESTOS.glob("*.json")):
        partida = json.loads(ruta.read_text(encoding="utf-8"))
        antes, despues = coste(partida, fichas, previos), coste(partida, fichas, actuales)
        if antes is None or despues is None:
            continue
        usados = [linea["ref"] for linea in partida["recursos"]
                  if linea["ref"] in cambiados and float(linea.get("rendimiento") or 0) > 0]
        filas.append({
            "codigo_partida": partida["codigo"],
            "descripcion": (partida.get("descripcion") or "")[:120],
            "coste_anterior": f"{antes:.2f}",
            "coste_actual": f"{despues:.2f}",
            "delta_eur": f"{despues - antes:+.2f}",
            "delta_pct": f"{(despues / antes - 1) * 100:+.2f}" if antes else "",
            "recursos_afectados": ", ".join(sorted(set(usados))),
        })
        deltas.append(despues / antes - 1 if antes else 0.0)

    argumentos.salida.parent.mkdir(parents=True, exist_ok=True)
    with argumentos.salida.open("w", encoding="utf-8-sig", newline="") as manejador:
        escritor = csv.DictWriter(manejador, fieldnames=list(filas[0]), delimiter=";",
                                  lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(filas)

    afectadas = [d for d in deltas if abs(d) > 1e-9]
    print(f"Recursos con precio nuevo: {len(cambiados)}")
    print(f"Partidas medidas: {len(deltas)}; con coste distinto: {len(afectadas)} "
          f"({len(afectadas) / len(deltas) * 100:.1f} %)")
    if afectadas:
        afectadas.sort()
        print(f"Delta: mediana {statistics.median(afectadas) * 100:+.2f} % · "
              f"p10 {afectadas[len(afectadas) // 10] * 100:+.2f} % · "
              f"p90 {afectadas[len(afectadas) * 9 // 10] * 100:+.2f} % · "
              f"máximo {afectadas[-1] * 100:+.2f} %")
    filas.sort(key=lambda f: -abs(float(f["delta_pct"] or 0)))
    print("Mayores cambios:")
    for fila in filas[:5]:
        print(f"  {fila['codigo_partida']:14}{fila['delta_pct']:>8} %  "
              f"{fila['coste_anterior']:>10} -> {fila['coste_actual']:>10}  "
              f"({fila['descripcion'][:46]})")
    print(f"Escrito {argumentos.salida}; no se ha modificado ninguna partida")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
