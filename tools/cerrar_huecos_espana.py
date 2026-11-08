#!/usr/bin/env python3
"""Cierra los recursos que quedaban sin precio, con un método declarado por recurso.

Decisión del titular: *no queda ningún recurso sin precio; se busca la mejor manera
para cada uno*. La mejor manera es una jerarquía de evidencia explícita, y cada
recurso lleva escrito de cuál viene:

* ``banco`` — la ficha del banco es el artículo (identidad directa).
* ``banco_analogia`` — la ficha es de la misma familia y unidad, con otra medida o tipo.
* ``modelo_propio`` — maquinaria valorada como compra / vida útil (modelo del 7 de noviembre).
* ``modelo_alquiler`` — equipo que se alquila: tarifa del banco calibrada al uso del catálogo.
* ``compuesto`` — paquete de consumibles valorado por sus componentes.
* ``mercado_rango`` — sin ficha de banco: se mantiene el precio de la matriz porque cae
  dentro de una horquilla de mercado declarada (el criterio lleva la horquilla).

El comando valida que **no falte ningún recurso** de la lista de huecos, escribe la
adjudicación y no toca ni la base de datos ni el SQL.

Uso:
    python tools/cerrar_huecos_espana.py            # simulación
    python tools/cerrar_huecos_espana.py --aplicar  # reescribe la adjudicación
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DOC = RAIZ / "docs/auditoria_precios"
FECHA = "2026-11-07"
DECISIONES = DOC / f"espana_cierre_total_{FECHA}.csv"
HUECOS = DOC / f"espana_identidad_huecos_{FECHA}.csv"
REGISTRO = DOC / f"espana_2026-11-06.csv"
ADJUDICACION = DOC / f"espana_adjudicacion_{FECHA}.csv"
DECISION = "aplicar_fuente_unica_coherente"
BANCO = "Base de Precios de Construcción de Extremadura 2026 (BCEXTGREM_26_v1.bc3)"

FUENTES = {
    "banco": BANCO,
    "banco_analogia": BANCO + " — ficha de familia análoga",
    "modelo_propio": ("Modelo propio de coste horario de maquinaria (compra y "
                      f"amortización) {FECHA}"),
    "modelo_alquiler": BANCO + " — tarifa de alquiler calibrada al rendimiento del catálogo",
    "alquiler_mercado": ("Tarifa de alquiler mensual de mercado 2026 (sin ficha de banco, "
                         "servicio con mantenimiento incluido)"),
    "compuesto": ("Composición con componentes de la Base de Extremadura 2026 y "
                  "precios de tienda"),
    "mercado_rango": ("Precio de la matriz contrastado con horquilla de mercado 2026 "
                      "(sin ficha de banco)"),
}
RESERVAS = {
    "banco": "Identidad directa con la ficha del banco.",
    "banco_analogia": ("La ficha no es el artículo exacto: es la de la misma familia y unidad. "
                       "Sirve como nivel de precio, no como cotización del artículo."),
    "modelo_propio": ("Estimación propia trazable: la vida útil y el precio de compra son "
                      "hipótesis declaradas en la ficha del modelo."),
    "modelo_alquiler": ("Tarifa de alquiler del banco convertida a hora con el rendimiento del "
                        "propio catálogo: si cambia el rendimiento, cambia el precio."),
    "alquiler_mercado": ("No hay tarifa de banco de este servicio: es un alquiler mensual de "
                         "mercado. No se amortiza como máquina porque no se compra."),
    "compuesto": ("Composición declarada: no hay ficha del paquete completo, solo de sus "
                  "componentes."),
    "mercado_rango": ("Sin ficha de banco: se conserva el precio de la matriz por caer dentro "
                      "de la horquilla declarada. Es el grupo con menor evidencia."),
}


def leer(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as manejador:
        return list(csv.DictReader(manejador, delimiter=";"))


def escribir(path: Path, campos: list[str], filas: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as manejador:
        escritor = csv.DictWriter(manejador, fieldnames=campos, delimiter=";",
                                  lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(filas)


def numero(valor) -> Decimal | None:
    texto = str(valor or "").strip().replace(",", ".")
    if not texto:
        return None
    try:
        decimal = Decimal(texto)
    except InvalidOperation:
        return None
    return decimal if decimal > 0 else None


def validar(decisiones: list[dict], huecos: set[str], registro: dict[str, dict]) -> None:
    vistos = set()
    for fila in decisiones:
        codigo = fila["codigo_recurso"]
        if codigo in vistos:
            raise ValueError(f"Recurso duplicado en el cierre: {codigo}")
        vistos.add(codigo)
        if codigo not in registro:
            raise ValueError(f"Recurso inexistente: {codigo}")
        if fila["metodo"] not in FUENTES:
            raise ValueError(f"{codigo}: método no reconocido {fila['metodo']!r}")
        if not fila["criterio"].strip():
            raise ValueError(f"{codigo}: el cierre exige criterio")
        precio = numero(fila["precio"]) or numero(registro[codigo]["precio_matriz"])
        if precio is None:
            raise ValueError(f"{codigo}: sin precio ni en la decisión ni en la matriz")
    faltan = huecos - vistos
    if faltan:
        raise ValueError(f"Recursos sin decisión de cierre: {sorted(faltan)}")
    sobran = vistos - huecos
    if sobran:
        raise ValueError(f"Decisiones para recursos que ya tenían precio: {sorted(sobran)}")


def construir(decisiones: list[dict], registro: dict[str, dict],
              adjudicacion: list[dict]) -> tuple[list[dict], Counter]:
    por_codigo = {fila["codigo_recurso"]: fila for fila in decisiones}
    metodos: Counter = Counter()
    salida = []
    for fila in adjudicacion:
        decision = por_codigo.get(fila["codigo_recurso"])
        if decision is None:
            salida.append(fila)
            continue
        recurso = registro[fila["codigo_recurso"]]
        precio = numero(decision["precio"]) or numero(recurso["precio_matriz"])
        precio = precio.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        actual = numero(fila["precio_matriz"]) or Decimal("0")
        desviacion = ((precio / actual - 1) * 100).quantize(Decimal("0.1")) if actual else None
        metodos[decision["metodo"]] += 1
        salida.append({**fila,
                       "decision": DECISION,
                       "precio_adoptado": f"{precio:.2f}",
                       "precio_fuente": f"{precio:.2f}",
                       "fuente": FUENTES[decision["metodo"]],
                       "codigo_fuente": decision["referencia"] or f"MERCADO-{FECHA}",
                       "edicion_fecha": FECHA,
                       "desviacion_pct": "" if desviacion is None else f"{desviacion}",
                       "criterio": decision["criterio"],
                       "reserva": RESERVAS[decision["metodo"]]})
    return salida, metodos


def main() -> int:
    analizador = argparse.ArgumentParser(description=__doc__,
                                         formatter_class=argparse.RawDescriptionHelpFormatter)
    analizador.add_argument("--decisiones", type=Path, default=DECISIONES)
    analizador.add_argument("--aplicar", action="store_true")
    argumentos = analizador.parse_args()

    decisiones = leer(argumentos.decisiones)
    huecos = {f["codigo_recurso"] for f in leer(HUECOS)}
    registro = {f["codigo_recurso"]: f for f in leer(REGISTRO)}
    adjudicacion = leer(ADJUDICACION)
    validar(decisiones, huecos, registro)
    salida, metodos = construir(decisiones, registro, adjudicacion)

    print(f"{len(decisiones)} recursos cerrados, reparto por método:")
    for metodo, cuantos in metodos.most_common():
        print(f"  {metodo:16} {cuantos:>4}")
    confianza = Counter(f["confianza"] for f in decisiones)
    print(f"  confianza: {dict(confianza)}")
    if not argumentos.aplicar:
        print("Simulación: no se ha escrito nada. Usa --aplicar para reescribir la tabla.")
        return 0
    escribir(ADJUDICACION, list(adjudicacion[0].keys()), salida)
    print(f"Escrito {ADJUDICACION.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
