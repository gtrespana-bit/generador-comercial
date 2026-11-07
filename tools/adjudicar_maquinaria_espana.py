#!/usr/bin/env python3
"""Convierte la propuesta de coste horario de maquinaria en adjudicación.

Toma la tabla de parámetros y la propuesta calculada (compra / vida útil,
energía, mantenimiento y consumibles) y reescribe, en la tabla de adjudicación
de la auditoría, la decisión de cada máquina que tenga precio propio:

* ``decision = aplicar_fuente_unica_coherente`` (una sola fuente: el modelo);
* ``precio_adoptado`` = coste horario calculado, redondeado a céntimos;
* ``codigo_fuente = MODELO-MQ-<fecha>``, para que el precio quede trazado a la
  ficha de parámetros y no a una tarifa de banco que no existe;
* criterio con la aritmética completa (adquisición, vida, mantenimiento,
  energía, consumibles) y reserva con lo que el modelo *no* acredita.

No toca la base de datos, no ejecuta SQL y no despliega: solo escribe la tabla
de adjudicación que después consume ``cerrar_auditoria_espana.py``.

Uso:
    python tools/adjudicar_maquinaria_espana.py            # simulación
    python tools/adjudicar_maquinaria_espana.py --aplicar  # reescribe la tabla
"""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DOC = RAIZ / "docs/auditoria_precios"
FECHA = "2026-11-07"
PARAMETROS = DOC / f"espana_maquinaria_horaria_parametros_{FECHA}.csv"
PROPUESTA = DOC / f"espana_maquinaria_horaria_propuesta_{FECHA}.csv"
ADJUDICACION = DOC / f"espana_adjudicacion_{FECHA}.csv"
DECISION = "aplicar_fuente_unica_coherente"
CODIGO_FUENTE = f"MODELO-MQ-{FECHA}"
FUENTE = ("Modelo propio de coste horario de maquinaria (compra / vida útil + "
          "mantenimiento + energía + consumibles), ficha "
          f"espana_maquinaria_horaria_parametros_{FECHA}.csv")
RESERVA = ("Estimación propia: no es una tarifa de mercado contrastada ni hay ficha "
           "de banco equivalente. La vida útil es una hipótesis de ingeniería y el "
           "precio de adquisición no incluye financiación, seguro ni transporte.")


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
        return Decimal(texto)
    except InvalidOperation:
        return None


def criterio(propuesta: dict, parametros: dict) -> str:
    """Redacta la aritmética del precio para que se pueda reproducir a mano."""
    return (
        "Modelo de compra y amortización, no de alquiler: "
        f"{parametros['precio_adquisicion_sin_iva_eur']} EUR sin IVA "
        f"({parametros['fuente_precio']}) entre {propuesta['vida_util_h']} h de vida útil, "
        f"con mantenimiento {Decimal(parametros['tasa_mantenimiento'] or '0') * 100:.0f} % "
        f"del valor de compra, energía {parametros['potencia_kw']} kW × 0,20 EUR/kWh × "
        f"factor de carga {parametros['factor_carga'] or '0'} y consumibles "
        f"{parametros['consumibles_eur_h']} EUR/h ({parametros['consumibles_detalle']}). "
        f"Resultado {propuesta['coste_h']} EUR/h (sensibilidad "
        f"{propuesta['coste_vida_mitad']}–{propuesta['coste_vida_doble']} EUR/h al variar "
        f"la vida útil ×0,5–×2)."
    )


def construir(parametros: list[dict], propuesta: list[dict],
              adjudicacion: list[dict]) -> tuple[list[dict], list[str]]:
    fichas = {fila["codigo_recurso"]: fila for fila in parametros}
    calculadas = {fila["codigo_recurso"]: fila for fila in propuesta
                  if fila["coste_h"].strip()}
    avisos: list[str] = []
    salida = []
    for fila in adjudicacion:
        codigo = fila["codigo_recurso"]
        if codigo not in calculadas:
            salida.append(fila)
            continue
        calculo = calculadas[codigo]
        parametro = fichas[codigo]
        precio = numero(calculo["coste_h"]).quantize(Decimal("0.01"),
                                                     rounding=ROUND_HALF_UP)
        actual = numero(fila["precio_matriz"]) or Decimal("0")
        desviacion = ((precio / actual - 1) * 100).quantize(Decimal("0.1")) if actual else None
        if desviacion is None or abs(desviacion) > 50:
            avisos.append(f"{codigo}: el modelo mueve el precio de la matriz un "
                          f"{desviacion} % ({fila['precio_matriz']} → {precio} EUR/h)")
        salida.append({**fila,
                       "decision": DECISION,
                       "precio_adoptado": f"{precio:.2f}",
                       "precio_fuente": parametro["precio_adquisicion_sin_iva_eur"],
                       "fuente": FUENTE,
                       "codigo_fuente": CODIGO_FUENTE,
                       "edicion_fecha": FECHA,
                       "desviacion_pct": "" if desviacion is None else f"{desviacion}",
                       "criterio": criterio(calculo, parametro),
                       "reserva": RESERVA})
    return salida, avisos


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aplicar", action="store_true",
                        help="reescribe la tabla de adjudicación")
    args = parser.parse_args()

    parametros = leer(PARAMETROS)
    propuesta = leer(PROPUESTA)
    adjudicacion = leer(ADJUDICACION)
    salida, avisos = construir(parametros, propuesta, adjudicacion)

    tocadas = [f for f in salida if f["decision"] == DECISION
               and f["codigo_fuente"] == CODIGO_FUENTE]
    print(f"{len(tocadas)} máquinas con precio de modelo propio:")
    for fila in tocadas:
        print(f"  {fila['codigo_recurso']:16} {fila['usos']:>5} usos  "
              f"{fila['precio_matriz']:>10} → {fila['precio_adoptado']:>6} EUR/h "
              f"({fila['desviacion_pct']} %)")
    for aviso in avisos:
        print(f"  AVISO {aviso}")
    if not args.aplicar:
        print("Simulación: no se ha escrito nada. Usa --aplicar para reescribir la tabla.")
        return 0
    escribir(ADJUDICACION, list(adjudicacion[0].keys()), salida)
    print(f"Escrito {ADJUDICACION.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
