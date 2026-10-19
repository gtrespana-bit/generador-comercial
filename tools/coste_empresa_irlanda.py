#!/usr/bin/env python3
"""Modelo de coste empresa para la mano de obra irlandesa (2026).

Mismo criterio que España y Reino Unido: el precio del recurso de mano de obra
es el **coste empresa**, no la tarifa del autónomo con beneficio, porque el
catálogo aplica después un 35 % de margen sobre el coste directo.

Salario base ........ Construction Sector Sectoral Employment Order (SEO),
                      tarifas vigentes desde el 1 de agosto de 2026:
                      craftsperson 23,74 €/h, categoría A 23,03 €/h,
                      categoría B 21,37 €/h y nuevo entrante 17,28 €/h.
                      El SEO es el suelo legal del sector, no una mediana: en
                      Dublín se paga por encima, y el rango del precio lo
                      recoge en lugar de inventar una prima por oficio.
PRSI empresa ........ 11,40 % desde el 1 de octubre de 2026 (11,25 % antes),
                      sin techo de ingresos ni bonificación.
Pensión ............. 32,89 €/semana por trabajador que impone el propio SEO
                      (1.710,28 €/año), cifra que ya cubre la aportación de
                      auto-enrolamiento del 1,5 %.
Vacaciones .......... 20 días de vacaciones anuales + 9 festivos = 29 días.
Bajas ............... 5 días de baja remunerada estatutaria al 70 %, con tope
                      de 110 €/día.
Despido ............. 2 semanas de salario por año de servicio (statutory
                      redundancy), amortizadas como dos semanas al año.
Divisor ............. horas facturables reales (2.028 h contratadas menos
                      vacaciones y bajas), igual que en España y Reino Unido.

Uso:
    python3 tools/coste_empresa_irlanda.py            # tabla
    python3 tools/coste_empresa_irlanda.py --csv      # CSV
"""

from __future__ import annotations

import argparse
import csv
import sys

# ─────────────────────────────────────────────────────────────────────────────
# 1. Parámetros del ejercicio 2026
# ─────────────────────────────────────────────────────────────────────────────

FECHA = "2026-10-18"
MONEDA = "EUR"

# Jornada del sector de la construcción: 39 h/semana (8 h de lunes a jueves y
# 7 h el viernes), la misma base que usan los convenios de obra irlandeses.
HORAS_SEMANA = 39.0
SEMANAS = 52.0
HORAS_CONTRATADAS = HORAS_SEMANA * SEMANAS          # 2.028 h
HORAS_DIA = HORAS_SEMANA / 5.0                      # 7,8 h

# Vacaciones: 20 días de permiso anual retribuido (Organisation of Working
# Time Act) + 9 festivos. En obra se disfrutan, no se compensan en nómina.
DIAS_VACACIONES = 29.0
HORAS_VACACIONES = DIAS_VACACIONES * HORAS_DIA      # 226,2 h

# Bajas: 5 días de baja remunerada estatutaria al 70 % del salario diario con
# tope de 110 €/día (2026).
DIAS_BAJA = 5.0
HORAS_BAJA = DIAS_BAJA * HORAS_DIA                  # 39,0 h

HORAS_FACTURABLES = HORAS_CONTRATADAS - HORAS_VACACIONES - HORAS_BAJA  # 1.762,8

# PRSI empresa (Class A, tipo estándar) desde el 1 de octubre de 2026.
PRSI_EMPRESA = 0.114
# La aportación patronal al plan de pensiones que fija el SEO de la
# construcción: 32,89 € por semana y trabajador.
PENSION_SEMANAL = 32.89

# Gastos fijos anuales por operario (EPI, herramienta, formación, seguro y
# gestoría de nóminas), equivalentes a los que España agrupa como «costes
# fijos».
GASTOS_FIJOS = {
    # Responsabilidad civil de empleador, póliza de empresa pequeña.
    "seguro_empleador": 220.0,
    # EPI, ropa de trabajo y herramienta menor repuesta cada año.
    "epi_y_herramienta": 380.0,
    # Safe Pass, CSCS y reciclaje de trabajos en altura.
    "formacion": 180.0,
    "gestion_nomina": 120.0,
}
# Indemnización por despido: la ley irlandesa paga dos semanas de salario por
# año de servicio. Se amortiza como dos semanas al año.
SEMANAS_INDEMNIZACION = 2.0


# ─────────────────────────────────────────────────────────────────────────────
# 2. Oficios
#
#    clasificacion = tarifa mínima del SEO vigente desde el 1 de agosto de 2026.
#    El salario de mercado nunca se toma por debajo del SEO; cuando el oficio
#    no aparece con nombre propio en el SEO se usa la categoría que le
#    corresponde por cualificación.
# ─────────────────────────────────────────────────────────────────────────────

SEO = {
    "craftsperson": 23.74,
    "categoria_a": 23.03,
    "categoria_b": 21.37,
    "nuevo_entrante": 17.28,
}

# Código de recurso -> (oficio irlandés, clasificación SEO)
OFICIOS: dict[str, tuple[str, str]] = {
    "MO-OF1":       ("General operative / tradesperson", "craftsperson"),
    "MO-OF1-PISO":  ("Floor and wall tiler", "craftsperson"),
    "MO-OF1-ALI":   ("Tiler / plasterer", "craftsperson"),
    "MO-OF1-ALB":   ("Bricklayer / blocklayer", "craftsperson"),
    "MO-OF1-MON":   ("Dryliner / partitioner", "craftsperson"),
    "MO-AYU-ESP":   ("Skilled construction operative", "categoria_a"),
    "MO-AYU":       ("General construction operative", "categoria_b"),
    "MO-OF1-PIN":   ("Painter and decorator", "craftsperson"),
    "MO-OF1-PLO":   ("Plumber", "craftsperson"),
    "MO-OF1-ELE":   ("Electrician", "craftsperson"),
    "MO-OF1-CAB":   ("Steel fixer", "craftsperson"),
    "MO-OF1-CARP":  ("Formwork carpenter", "craftsperson"),
    "MO-OF1-SOLD":  ("Welder / steel erector", "craftsperson"),
    "MO-OF1-CARPM": ("Carpenter and joiner", "craftsperson"),
    "MO-OF1-VIDR":  ("Glazier", "craftsperson"),
    "MO-OF1-AC":    ("HVAC and refrigeration engineer", "craftsperson"),
    "MO-OF1-JARD":  ("Landscape operative", "categoria_b"),
}


# ─────────────────────────────────────────────────────────────────────────────
# 3. Cálculo
# ─────────────────────────────────────────────────────────────────────────────

def coste_empresa(salario_hora: float) -> dict:
    """Coste empresa por hora facturable a partir del salario por hora."""
    salario = salario_hora * HORAS_CONTRATADAS
    prsi = salario * PRSI_EMPRESA
    pension = PENSION_SEMANAL * SEMANAS
    fijos = sum(GASTOS_FIJOS.values())
    indemnizacion = salario_hora * HORAS_SEMANA * SEMANAS_INDEMNIZACION
    total = salario + prsi + pension + fijos + indemnizacion
    return {
        "salario_anual": salario,
        "prsi": prsi,
        "pension": pension,
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
    for codigo, (oficio, clasificacion) in sorted(OFICIOS.items()):
        tarifa = SEO[clasificacion]
        c = coste_empresa(tarifa)
        filas.append({
            "codigo": codigo,
            "oficio": oficio,
            "clasificacion_seo": clasificacion,
            "tarifa_seo": tarifa,
            "salario_anual": round(c["salario_anual"], 2),
            "prsi_empresa": round(c["prsi"], 2),
            "pension": round(c["pension"], 2),
            "gastos_fijos": round(c["gastos_fijos"], 2),
            "total_anual": round(c["total_anual"], 2),
            "recargo_pct": round(c["recargo_pct"], 1),
            "horas_facturables": round(HORAS_FACTURABLES, 1),
            "coste_hora_eur": round(c["coste_hora_facturable"], 2),
        })

    if args.csv:
        w = csv.DictWriter(sys.stdout, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)
        return 0

    print(f"Modelo de coste empresa — Irlanda {FECHA}")
    print(f"Jornada {HORAS_SEMANA:g} h/semana · contratadas {HORAS_CONTRATADAS:,.0f} h/año")
    print(f"Vacaciones {DIAS_VACACIONES:g} días ({HORAS_VACACIONES:,.1f} h) · bajas "
          f"{DIAS_BAJA:g} días ({HORAS_BAJA:,.1f} h) → facturables "
          f"{HORAS_FACTURABLES:,.1f} h/año")
    print(f"PRSI empresa {PRSI_EMPRESA:.2%} · pensión SEO {PENSION_SEMANAL:.2f} €/semana")
    print()
    print(f"{'recurso':<16}{'oficio':<36}{'SEO':>8}{'total/año':>11}"
          f"{'recargo':>9}{'€/h fact.':>11}")
    print("─" * 91)
    for f in filas:
        print(f"{f['codigo']:<16}{f['oficio']:<36}{f['tarifa_seo']:>8.2f}"
              f"{f['total_anual']:>11,.0f}{f['recargo_pct']:>8.1f}%"
              f"{f['coste_hora_eur']:>11.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
