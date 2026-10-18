#!/usr/bin/env python3
"""Modelo de coste empresa para la mano de obra británica (2026/27).

Replica para el Reino Unido el criterio ya adoptado en España
(``docs/INVESTIGACION_PRECIOS_ESPANA.md``): el precio del recurso de mano de
obra es el **coste empresa**, no la tarifa de autónomo con beneficio, porque el
catálogo aplica un margen del 35 % sobre el coste directo y usar la tarifa de
mercado produciría margen sobre margen.

Salario base ........ ONS ASHE (asalariados, PAYE) mediana por oficio,
                      contrastado con las tarifas mínimas CIJC vigentes desde
                      el 20 de julio de 2026.
Cargas .............. National Insurance empresa, pensión auto-enrolment,
                      CITB levy, vacaciones, bajas y gastos fijos.
Divisor ............. horas facturables reales (no las horas contratadas),
                      igual que el criterio español de 1.400-1.736 h.

Uso:
    python3 tools/coste_empresa_reino_unido.py            # tabla
    python3 tools/coste_empresa_reino_unido.py --csv      # CSV
"""

from __future__ import annotations

import argparse
import csv
import sys

# ─────────────────────────────────────────────────────────────────────────────
# 1. Parámetros del ejercicio 2026/27
# ─────────────────────────────────────────────────────────────────────────────

FECHA = "2026-10-18"
MONEDA = "GBP"

# Jornada del CIJC Working Rule Agreement: 39 h/semana (lunes-jueves 8 h,
# viernes 7 h). Semanas completas del año.
HORAS_SEMANA = 39.0
SEMANAS = 52.0
HORAS_CONTRATADAS = HORAS_SEMANA * SEMANAS          # 2.028 h
HORAS_DIA = HORAS_SEMANA / 5.0                      # 7,8 h

# Vacaciones: 31 días (23 de industria + 8 festivos) desde el 1 de enero de
# 2025 según WR.18. Derecho absoluto que no puede integrarse en el salario base.
DIAS_VACACIONES = 31.0
HORAS_VACACIONES = DIAS_VACACIONES * HORAS_DIA      # 241,8 h

# Bajas: media británica de 4,4 días/año en construcción.
DIAS_BAJA = 4.4
HORAS_BAJA = DIAS_BAJA * HORAS_DIA                  # 34,3 h

HORAS_FACTURABLES = HORAS_CONTRATADAS - HORAS_VACACIONES - HORAS_BAJA  # 1.751,9

# National Insurance empresa (Class 1 secundaria). 15 % sobre lo que exceda del
# secondary threshold, vigente desde el 6 de abril de 2025 y congelado en
# 2026/27 (y hasta 2030/31).
NI_EMPRESA = 0.15
NI_UMBRAL = 5_000.0

# Pensión de auto-enrolment: mínimo legal del 3 % de la banda de ingresos
# computable (6.240-50.270 £ en 2026/27).
PENSION = 0.03
PENSION_BANDA_BAJA = 6_240.0
PENSION_BANDA_ALTA = 50_270.0

# CITB levy: 0,35 % de la nómina PAYE (1,25 % sobre CIS neto, que aquí no
# aplica porque estamos calculando coste de personal asalariado).
CITB = 0.0035


def _pension(salario: float) -> float:
    banda = min(max(salario - PENSION_BANDA_BAJA, 0.0),
                PENSION_BANDA_ALTA - PENSION_BANDA_BAJA)
    return banda * PENSION


# Gastos fijos anuales por operario (equivalentes a los que España agrupa como
# «costes fijos»: EPI, herramienta, gestor de nóminas, formación, seguro,
# previsión de despido). Se expresan por operario y por año.
GASTOS_FIJOS = {
    # Responsabilidad civil de empleador, ~180 £/año para una empresa pequeña.
    "seguro_empleador": 180.0,
    # EPI, ropa de trabajo y herramienta menor repuesta cada año.
    "epi_y_herramienta": 350.0,
    # CSCS, SMSTS/SSSTS y reciclaje.
    "formacion": 150.0,
    # Gestoría de nóminas.
    "gestion_nomina": 100.0,
}
# Previsión de indemnización por despido: una semana por año de servicio,
# amortizada como una semana de salario al año.
SEMANAS_INDEMNIZACION = 1.0


# ─────────────────────────────────────────────────────────────────────────────
# 2. Oficios británicos
#
#    salario_hora = mediana ONS ASHE de asalariados (incluye horas extras).
#    cijc         = tarifa mínima del CIJC Working Rule Agreement vigente desde
#                   el 20 de julio de 2026, para comprobar que el salario de
#                   mercado no queda por debajo del convenio.
# ─────────────────────────────────────────────────────────────────────────────

CIJC = {
    # Clasificación              £/hora desde 20/07/2026
    "general_operative": 13.18,
    "skill_rate_4": 13.30,
    "skill_rate_3": 14.07,
    "skill_rate_2": 15.04,
    "skill_rate_1": 15.61,
    "craft_rate": 16.40,
}

# Código de recurso -> (oficio británico, £/h ONS ASHE, clasificación CIJC)
OFICIOS: dict[str, tuple[str, float, str]] = {
    # Oficial general de obra.
    "MO-OF1":       ("General builder (skilled operative)", 17.65, "craft_rate"),
    # Colocador de pavimentos.
    "MO-OF1-PISO":  ("Floor layer (wall and floor tiler)", 17.65, "craft_rate"),
    # Enchapador / alicatador.
    "MO-OF1-ALI":   ("Wall and floor tiler", 17.65, "craft_rate"),
    # Albañil.
    "MO-OF1-ALB":   ("Bricklayer", 16.75, "craft_rate"),
    # Montador de prefabricados de interior.
    "MO-OF1-MON":   ("Interior fit-out installer", 17.04, "skill_rate_1"),
    # Ayudante especializado (oficial de 2ª / improver).
    "MO-AYU-ESP":   ("Improver / skilled labourer", 14.07, "skill_rate_3"),
    # Peón.
    "MO-AYU":       ("General operative (labourer)", 13.50, "general_operative"),
    # Pintor.
    "MO-OF1-PIN":   ("Painter and decorator", 16.58, "craft_rate"),
    # Fontanero / instalador de calefacción.
    "MO-OF1-PLO":   ("Plumber and heating engineer", 18.18, "craft_rate"),
    # Electricista.
    "MO-OF1-ELE":   ("Electrician", 19.20, "craft_rate"),
    # Cabillero / armador de acero.
    "MO-OF1-CAB":   ("Steel fixer", 16.40, "skill_rate_1"),
    # Carpintero de obra (encofrador).
    "MO-OF1-CARP":  ("Formwork carpenter / joiner", 17.04, "craft_rate"),
    # Soldador.
    "MO-OF1-SOLD":  ("Welder / structural steel erector", 18.50, "craft_rate"),
    # Carpintero de madera estructural.
    "MO-OF1-CARPM": ("Carpenter and joiner", 17.04, "craft_rate"),
    # Vidriero.
    "MO-OF1-VIDR":  ("Glazier", 17.04, "craft_rate"),
    # Técnico de refrigeración y climatización.
    "MO-OF1-AC":    ("HVAC and refrigeration engineer", 18.18, "craft_rate"),
    # Jardinero.
    "MO-OF1-JARD":  ("Landscape operative", 15.04, "skill_rate_2"),
}


# ─────────────────────────────────────────────────────────────────────────────
# 3. Cálculo
# ─────────────────────────────────────────────────────────────────────────────

def coste_empresa(salario_hora: float, *, precio_extra_hora: float = 0.0) -> dict:
    """Coste empresa por hora facturable a partir del salario por hora."""
    salario = salario_hora * HORAS_CONTRATADAS
    ni = max(salario - NI_UMBRAL, 0.0) * NI_EMPRESA
    pension = _pension(salario)
    citb = salario * CITB
    fijos = sum(GASTOS_FIJOS.values())
    indemnizacion = salario_hora * HORAS_SEMANA * SEMANAS_INDEMNIZACION
    total = salario + ni + pension + citb + fijos + indemnizacion
    return {
        "salario_anual": salario,
        "ni": ni,
        "pension": pension,
        "citb": citb,
        "gastos_fijos": fijos + indemnizacion,
        "total_anual": total,
        "coste_hora_facturable": total / HORAS_FACTURABLES,
        "coste_hora_contratada": total / HORAS_CONTRATADAS,
        "recargo_pct": (total / salario - 1.0) * 100.0,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", action="store_true")
    args = ap.parse_args(argv)

    filas = []
    for codigo, (oficio, salario, cijc_clave) in sorted(OFICIOS.items()):
        tarifa_cijc = CIJC[cijc_clave]
        base = max(salario, tarifa_cijc)          # nunca por debajo del convenio
        c = coste_empresa(base)
        filas.append({
            "codigo": codigo,
            "oficio": oficio,
            "clasificacion_cijc": cijc_clave,
            "salario_hora_ons": salario,
            "tarifa_cijc": tarifa_cijc,
            "base_adoptada": round(base, 2),
            "salario_anual": round(c["salario_anual"], 2),
            "ni_empresa": round(c["ni"], 2),
            "pension": round(c["pension"], 2),
            "citb": round(c["citb"], 2),
            "gastos_fijos": round(c["gastos_fijos"], 2),
            "total_anual": round(c["total_anual"], 2),
            "recargo_pct": round(c["recargo_pct"], 1),
            "horas_facturables": round(HORAS_FACTURABLES, 1),
            "coste_hora_gbp": round(c["coste_hora_facturable"], 2),
        })

    if args.csv:
        w = csv.DictWriter(sys.stdout, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)
        return 0

    print(f"Modelo de coste empresa — Reino Unido {FECHA}")
    print(f"Jornada CIJC {HORAS_SEMANA:g} h/semana · contratadas {HORAS_CONTRATADAS:,.0f} h/año")
    print(f"Vacaciones {DIAS_VACACIONES:g} días ({HORAS_VACACIONES:,.1f} h) · bajas {DIAS_BAJA:g} "
          f"días ({HORAS_BAJA:,.1f} h) → facturables {HORAS_FACTURABLES:,.1f} h/año")
    print()
    print(f"{'recurso':<16}{'oficio':<40}{'ONS':>7}{'CIJC':>7}{'base':>7}"
          f"{'total/año':>11}{'recargo':>9}{'£/h fact.':>11}")
    print("─" * 108)
    for f in filas:
        print(f"{f['codigo']:<16}{f['oficio']:<40}"
              f"{f['salario_hora_ons']:>7.2f}{f['tarifa_cijc']:>7.2f}{f['base_adoptada']:>7.2f}"
              f"{f['total_anual']:>11,.0f}{f['recargo_pct']:>8.1f}%{f['coste_hora_gbp']:>11.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
