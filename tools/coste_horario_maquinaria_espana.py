#!/usr/bin/env python3
"""Coste horario de maquinaria con parámetros explícitos y sensibilidad a la vida útil.

El banco de precios no resuelve la maquinaria pequeña: sus tarifas horarias son
heterogéneas (0,84 EUR/h para un taladro de 750 W y 8,11 EUR/h para una
taladradora mecánica) y no publican la vida útil ni la amortización que aplican.
Este comando hace explícito el modelo y mide cuánto depende del parámetro que
más lo mueve: las horas de vida útil.

    coste_hora = adquisición / vida_util * (1 + mantenimiento)
                 + potencia * precio_energia * factor_carga
                 + consumibles

No aplica precios ni cambia estados: escribe una tabla de propuesta.

Uso:
    python tools/coste_horario_maquinaria_espana.py --precio-energia 0.20
"""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/auditoria_precios"
ENTRADA = DOC / "espana_maquinaria_horaria_parametros_2026-11-07.csv"
SALIDA = DOC / "espana_maquinaria_horaria_propuesta_2026-11-07.csv"

# Sensibilidad: la vida útil es el parámetro que más mueve el resultado, así que
# cada ficha se publica con su valor declarado y con la mitad y el doble.
FACTORES_VIDA = (Decimal("0.5"), Decimal("1"), Decimal("2"))


def leer(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as manejador:
        return list(csv.DictReader(manejador, delimiter=";"))


def numero(valor) -> Decimal | None:
    if valor is None or str(valor).strip() == "":
        return None
    try:
        return Decimal(str(valor).replace(",", "."))
    except (InvalidOperation, ValueError):
        return None


def coste(fila: dict, vida: Decimal, energia: Decimal) -> Decimal | None:
    adquisicion = numero(fila["precio_adquisicion_sin_iva_eur"])
    potencia = numero(fila["potencia_kw"])
    mantenimiento = numero(fila["tasa_mantenimiento"]) or Decimal("0")
    consumibles = numero(fila["consumibles_eur_h"]) or Decimal("0")
    carga = numero(fila.get("factor_carga")) or Decimal("0")
    if adquisicion is None or potencia is None or vida <= 0:
        return None
    return (adquisicion / vida * (1 + mantenimiento)
            + potencia * energia * carga + consumibles)


def vida_implicita(fila: dict, energia: Decimal) -> Decimal | None:
    """Horas de vida que implicaría la tarifa baja del banco para esa máquina."""
    adquisicion = numero(fila["precio_adquisicion_sin_iva_eur"])
    potencia = numero(fila["potencia_kw"])
    mantenimiento = numero(fila["tasa_mantenimiento"]) or Decimal("0")
    consumibles = numero(fila["consumibles_eur_h"]) or Decimal("0")
    carga = numero(fila.get("factor_carga")) or Decimal("0")
    banco = numero(fila["banda_banco_min_eur_h"])
    if None in (adquisicion, potencia, banco):
        return None
    resto = banco - potencia * energia * carga - consumibles
    if resto <= 0:
        return None
    return adquisicion * (1 + mantenimiento) / resto


def main() -> int:
    analizador = argparse.ArgumentParser(description=__doc__)
    analizador.add_argument("--precio-energia", type=Decimal, default=Decimal("0.20"),
                            help="EUR/kWh (por defecto 0,20; confirmar con factura)")
    argumentos = analizador.parse_args()
    if argumentos.precio_energia <= 0:
        analizador.error("--precio-energia debe ser positivo")
    energia = argumentos.precio_energia

    salida = []
    for fila in leer(ENTRADA):
        vida = numero(fila["vida_util_h"]) or Decimal("1")
        calculos = [coste(fila, vida * factor, energia) for factor in FACTORES_VIDA]
        implicita = vida_implicita(fila, energia)
        salida.append({
            "codigo_recurso": fila["codigo_recurso"],
            "precio_actual_eur_h": fila["precio_actual_eur_h"],
            "precio_adquisicion_sin_iva_eur": fila["precio_adquisicion_sin_iva_eur"],
            "fuente_precio": fila["fuente_precio"],
            "vida_util_h": fila["vida_util_h"],
            "coste_vida_mitad": f"{calculos[0]:.2f}" if calculos[0] is not None else "",
            "coste_h": f"{calculos[1]:.2f}" if calculos[1] is not None else "",
            "coste_vida_doble": f"{calculos[2]:.2f}" if calculos[2] is not None else "",
            "consumibles_eur_h": fila["consumibles_eur_h"],
            "consumibles_detalle": fila["consumibles_detalle"],
            "vida_implicita_banco_h": f"{implicita:.0f}" if implicita is not None else "",
            "banda_banco_min_eur_h": fila["banda_banco_min_eur_h"],
            "banda_banco_max_eur_h": fila["banda_banco_max_eur_h"],
            "fichas_banco": fila["fichas_banco"],
            "nota": fila["nota"],
        })

    with SALIDA.open("w", encoding="utf-8-sig", newline="") as manejador:
        escritor = csv.DictWriter(manejador, fieldnames=list(salida[0]), delimiter=";",
                                  lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(salida)

    print(f"Energía {energia} EUR/kWh; vida útil por ficha con sensibilidad ×0,5 y ×2")
    for fila in salida:
        print(f"  {fila['codigo_recurso']:16} actual {fila['precio_actual_eur_h']:>9} | modelo "
              f"{fila['coste_vida_mitad']:>5} / {fila['coste_h']:>5} / {fila['coste_vida_doble']:>5} "
              f"(vida {fila['vida_util_h']:>5} h) | banco {fila['banda_banco_min_eur_h'] or '—'}–"
              f"{fila['banda_banco_max_eur_h'] or '—'} | vida implícita "
              f"{fila['vida_implicita_banco_h'] or '—'} h")
    print(f"Escrito {SALIDA.relative_to(ROOT)}; no se ha modificado ningún precio")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
