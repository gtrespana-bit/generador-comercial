#!/usr/bin/env python3
"""Modelo de coste empresa para la mano de obra australiana (2026).

Replica para Australia el criterio ya adoptado en España, el Reino Unido e
Irlanda (``docs/INVESTIGACION_PRECIOS_IRLANDA.md``): el precio del recurso
de mano de obra es el **coste empresa**, no la tarifa de subcontrata con
beneficio, porque el catálogo aplica un margen del 35 % sobre el coste
directo y usar la tarifa de mercado produciría margen sobre margen.

Salario base ........ Awards de la Fair Work Commission vigentes desde el
                      1 de julio de 2026 (Annual Wage Review 2025-26,
                      +4,75 %): Building and Construction General On-site
                      Award 2020 [MA000020] para los oficios de obra,
                      Electrical Award [MA000025] y Plumbing and Fire
                      Sprinklers Award [MA000036]. Los tres comparten la
                      «standard rate» de 1.119,10 $/semana (CW3 / grado 5 /
                      tradesperson L1): la diferenciación real entre oficios
                      la hacen los pluses (industry, tool, trade).
Cargas .............. Superannuation Guarantee del 12 % sobre las OTE
                      (desde el 1/07/2025, tipo final de la escala),
                      workers compensation de NSW (icare, WIC 411100
                      «House Construction» 4,840 % + 0,110 % de dust
                      diseases = 4,95 %), provisión de long service leave
                      (1,7 %), annual leave loading del 17,5 %, el plus
                      diario de desplazamiento (fares & travel, 22,41 $/día
                      trabajado) y gastos fijos.
Divisor ............. horas trabajadas en obra (no las 1.976 h pagadas):
                      el sistema de RDO australiano paga 38 h/semana pero
                      en obra se trabajan días de 8 h y se devenga 0,4 h/día
                      hacia un día libre pagado cada 4 semanas.

Quedan fuera a propósito:
* El **payroll tax** estatal (NSW: 5,45 % sobre el exceso de 1,2 M$ de
  salarios). El PRSI irlandés y el NIC británico son universales; el payroll
  tax depende del estado y del tamaño de la empresa, y la pyme tipo de
  CotizaT puede estar bajo el umbral. Incluirlo inflaría el coste de quien
  no lo paga; queda documentado en la investigación.
* Las tarifas de **EBA** (convenios de empresa de la obra comercial grande,
  muy superiores al award): el rango +20 % de la matriz cubre parte de esa
  dispersión, pero el suelo publicable es el mínimo legal nacional, igual
  que en Irlanda (−3 % / +20 %).

Uso:
    python3 tools/coste_empresa_australia.py            # tabla
    python3 tools/coste_empresa_australia.py --csv      # CSV
"""

from __future__ import annotations

import argparse
import csv
import sys

# ─────────────────────────────────────────────────────────────────────────────
# 1. Parámetros del ejercicio 2026-27
# ─────────────────────────────────────────────────────────────────────────────

FECHA = "2026-10-19"
MONEDA = "AUD"

# Semana ordinaria de los tres awards: 38 h. En obra se trabajan días de 8 h
# y se devengan 0,4 h por día hacia el RDO (rostered day off): 1 día libre
# pagado cada 4 semanas = 13 al año.
HORAS_SEMANA = 38.0
SEMANAS = 52.0
HORAS_PAGADAS = HORAS_SEMANA * SEMANAS              # 1.976 h
HORAS_DIA_PAGADAS = HORAS_SEMANA / 5.0              # 7,6 h
HORAS_DIA_OBRA = 8.0

DIAS_LABORABLES = 260.0
# Annual leave NES: 4 semanas = 20 días. Festivos NSW 2026: 11 (Año Nuevo,
# Australia Day, Viernes Santo, Sábado y Lunes de Pascua —y Domingo en NSW—,
# ANZAC Day, King's Birthday, Labour Day, Navidad y Boxing Day).
DIAS_VACACIONES = 20.0
DIAS_FESTIVOS = 11.0
# Personal/carer's leave: derecho de 10 días/año; se modela el uso medio
# del sector (5 días), como en Irlanda.
DIAS_BAJA = 5.0
DIAS_RDO = 13.0

DIAS_TRABAJADOS = (
    DIAS_LABORABLES - DIAS_VACACIONES - DIAS_FESTIVOS - DIAS_BAJA - DIAS_RDO
)                                                   # 211 días
HORAS_FACTURABLES = DIAS_TRABAJADOS * HORAS_DIA_OBRA  # 1.688 h en obra

# Superannuation Guarantee: 12 % de las ordinary time earnings desde el
# 1/07/2025 (último escalón legislado; ATO). Las OTE incluyen el salario
# ordinario con sus pluses «all-purpose» y el leave loading, pero no el
# plus de desplazamiento (gasto reembolsado).
SUPER_GUARANTEE = 0.12

# Annual leave loading de los awards de construcción: 17,5 % sobre las
# 4 semanas de vacaciones (152 h pagadas).
LEAVE_LOADING = 0.175
HORAS_VACACIONES = DIAS_VACACIONES * HORAS_DIA_PAGADAS   # 152 h

# Workers compensation (NSW, icare): WIC 411100 «House Construction»
# 4,840 % + dust diseases contribution 0,110 % = 4,95 % de los salarios.
# Los tipos 2025-26 quedan congelados para 2026-27 (SIRA). Es el coste de
# seguro obligatorio más caro de los cuatro mercados anglófonos.
WORKERS_COMP = 0.0495

# Long service leave: en NSW, 8,67 semanas tras 10 años (y proporcional
# desde los 5 en varios supuestos) ≈ 1,67 % de devengo anual. Se provisiona
# el 1,7 %; los fondos portátiles estatales (p. ej. la levy del 0,35 %
# sobre el coste del proyecto en NSW) gravan el proyecto, no la nómina, y
# por eso no se suman aquí.
LSL_ACCRUAL = 0.017

# Fares and travel pattern allowance (MA000020 cl. 26): 22,41 $ por día
# trabajado en obra (2026). Es un coste empresa real y diario; no forma
# parte de las OTE para la superannuation.
TRAVEL_DIARIO = 22.41

# Plus de industria semanal del Building Award (cl. 22, «all-purpose»):
# 67,15 $ en obra general y 53,72 $ en residential building. Se adopta el
# de obra general (el sector por defecto del award); el residencial queda
# ≈1 % por debajo, dentro del rango publicado de la matriz.
INDUSTRY_GENERAL_SEMANAL = 67.15
INDUSTRY_RESIDENTIAL_SEMANAL = 53.72

# Gastos fijos anuales por operario (equivalentes a los de ES/GB/IE).
GASTOS_FIJOS = {
    # Responsabilidad civil y seguros de obra prorrateados.
    "seguro_responsabilidad": 350.0,
    # EPI, ropa de trabajo y herramienta menor repuesta cada año.
    "epi_y_herramienta": 600.0,
    # White Card, licencias de oficio, formación y tickets de planta.
    "formacion_y_licencias": 250.0,
    # Gestión de nómina y super (Payday Super desde el 1/07/2026).
    "gestion_nomina": 280.0,
    # Previsión de despido: la redundancy NES llega a 16 semanas a los
    # 9-10 años; se provisiona ≈0,6 semana ordinaria por año, en la línea
    # de la semana/año con tope usada en GB e IE.
    "prevision_despido": 750.0,
}


# ─────────────────────────────────────────────────────────────────────────────
# 2. Escalas salariales australianas (desde el 1/07/2026)
#
#    BUILDING  = MA000020 cl. 19.1, tarifas semanales mínimas (weekly hire).
#    TOOL      = pluses semanales de herramienta del mismo award, por
#                oficio (derivados de la pay guide FWO weekly-hire).
#    ELECTRICAL= MA000025 grado 5: 29,45 $/h + industria 41,41 $/sem +
#                herramienta 22,31 $/sem = 31,13 $/h ordinarios.
#    PLUMBING  = MA000036 tradesperson L1 «all-purpose»: 31,63 $/h
#                (base 29,45 + industria, fija especial y plus de oficio;
#                sin el plus de herramienta de 22,96 $/sem, que solo se
#                paga si la empresa exige herramienta propia).
# ─────────────────────────────────────────────────────────────────────────────

BUILDING_SEMANAL = {
    "cw1a": 1013.50,   # nuevo ingreso
    "cw1b": 1033.50,   # tras 3 meses
    "cw1c": 1047.30,   # tras 12 meses
    "cw1d": 1066.00,   # peón experimentado / ayuda directa al oficial
    "cw2": 1087.50,    # operario cualificado (steel fixer, andamista…)
    "cw3": 1119.10,    # tradesperson (standard rate de los tres awards)
}

TOOL_SEMANAL = {
    "carpenter": 41.22,   # carpenter, joiner, tilelayer, floor sander…
    "plasterer": 34.10,   # caster, fixer, floorlayer specialist, plasterer
    "bricklayer": 29.26,
    "painter": 9.89,      # painter, glazier
}

ELECTRICISTA_HORA = 31.13    # MA000025 grado 5, ordinario all-purpose
FONTANERO_HORA = 31.63       # MA000036 tradesperson L1, all-purpose


def _building(nivel: str, tool_semanal: float = 0.0) -> float:
    """Salario ordinario $/h de un nivel del Building Award (weekly hire)."""
    semanal = BUILDING_SEMANAL[nivel] + INDUSTRY_GENERAL_SEMANAL + tool_semanal
    return semanal / HORAS_SEMANA


# Código de recurso -> (oficio australiano, $/h ordinario adoptado, origen)
OFICIOS: dict[str, tuple[str, float, str]] = {
    # Oficial general de obra: CW3 sin plus de herramienta (la empresa la
    # pone), el «standard rate» del sistema de awards.
    "MO-OF1":       ("General tradesperson (CW3)", _building("cw3"),
                     "MA000020 CW3 + industry"),
    # Colocador de pavimentos: floorlayer specialist en la pay guide.
    "MO-OF1-PISO":  ("Floorlayer specialist",
                     _building("cw3", TOOL_SEMANAL["plasterer"]),
                     "MA000020 CW3 + industry + tool"),
    # Enchapador: tilelayer, en el grupo de herramienta alta.
    "MO-OF1-ALI":   ("Wall and floor tiler",
                     _building("cw3", TOOL_SEMANAL["carpenter"]),
                     "MA000020 CW3 + industry + tool"),
    # Albañil: bricklayer con su plus de herramienta propio.
    "MO-OF1-ALB":   ("Bricklayer",
                     _building("cw3", TOOL_SEMANAL["bricklayer"]),
                     "MA000020 CW3 + industry + tool"),
    # Montador de prefabricados de interior: joinery de obra.
    "MO-OF1-MON":   ("Fit-out carpenter / joiner",
                     _building("cw3", TOOL_SEMANAL["carpenter"]),
                     "MA000020 CW3 + industry + tool"),
    # Ayudante especializado: CW2 (operario cualificado, planta menor).
    "MO-AYU-ESP":   ("Skilled construction worker (CW2)", _building("cw2"),
                     "MA000020 CW2 + industry"),
    # Peón: CW1(d), el grado permanente del labourer que asiste al oficial.
    # No se usa CW1(a) (nuevo ingreso): es un grado de incorporación.
    "MO-AYU":       ("Construction labourer (CW1d)", _building("cw1d"),
                     "MA000020 CW1(d) + industry"),
    # Pintor: CW3 con el plus de herramienta menor del oficio.
    "MO-OF1-PIN":   ("Painter", _building("cw3", TOOL_SEMANAL["painter"]),
                     "MA000020 CW3 + industry + tool"),
    # Fontanero: award propio (MA000036), all-purpose publicado.
    "MO-OF1-PLO":   ("Plumber (tradesperson L1)", FONTANERO_HORA,
                     "MA000036 tradesperson L1 all-purpose"),
    # Electricista: award propio (MA000025), grado 5 con pluses.
    "MO-OF1-ELE":   ("Electrician (grade 5)", ELECTRICISTA_HORA,
                     "MA000025 grade 5 + industry + tool"),
    # Cabillero: el Building Award clasifica al steel fixer en CW2, NO como
    # tradesperson — la misma particularidad que el SEO irlandés (Cat. A).
    "MO-OF1-CAB":   ("Steel fixer (CW2)", _building("cw2"),
                     "MA000020 CW2 + industry"),
    # Carpintero de obra (encofrador): carpenter CW3.
    "MO-OF1-CARP":  ("Formwork carpenter",
                     _building("cw3", TOOL_SEMANAL["carpenter"]),
                     "MA000020 CW3 + industry + tool"),
    # Soldador: tradesperson ECW3 del sector metal/ingeniería del award
    # (el «tack welder» auxiliar es CW2; el soldador cualificado, ECW3).
    "MO-OF1-SOLD":  ("Welder (ECW3)", _building("cw3"),
                     "MA000020 ECW3 + industry"),
    # Carpintero de madera estructural.
    "MO-OF1-CARPM": ("Carpenter and joiner",
                     _building("cw3", TOOL_SEMANAL["carpenter"]),
                     "MA000020 CW3 + industry + tool"),
    # Vidriero: glazier, mismo grupo de herramienta que el pintor.
    "MO-OF1-VIDR":  ("Glazier", _building("cw3", TOOL_SEMANAL["painter"]),
                     "MA000020 CW3 + industry + tool"),
    # Técnico de climatización: «plumbing and mechanical services» del
    # MA000036, la misma escala que el fontanero.
    "MO-OF1-AC":    ("Mechanical services / HVAC tradesperson",
                     FONTANERO_HORA,
                     "MA000036 mechanical services L1 all-purpose"),
    # Jardinero-paisajista: el «landscaper» figura expresamente en CW2 en
    # las tablas del Building Award (no es peón CW1).
    "MO-OF1-JARD":  ("Landscaper (CW2)", _building("cw2"),
                     "MA000020 CW2 + industry"),
}


# ─────────────────────────────────────────────────────────────────────────────
# 3. Cálculo
# ─────────────────────────────────────────────────────────────────────────────

def coste_empresa(salario_hora: float) -> dict:
    """Coste empresa por hora trabajada a partir del salario ordinario $/h.

    ``salario_hora`` es la tarifa ordinaria «all-purpose» (base + pluses de
    industria y herramienta), que es como los awards definen el salario a
    todos los efectos (vacaciones, RDO y superannuation incluidos).
    """
    salario = salario_hora * HORAS_PAGADAS
    leave_loading = LEAVE_LOADING * salario_hora * HORAS_VACACIONES
    ote = salario + leave_loading
    superann = ote * SUPER_GUARANTEE
    workers_comp = ote * WORKERS_COMP
    lsl = ote * LSL_ACCRUAL
    travel = TRAVEL_DIARIO * DIAS_TRABAJADOS
    fijos = sum(GASTOS_FIJOS.values())
    total = salario + leave_loading + superann + workers_comp + lsl + travel + fijos
    return {
        "salario_anual": salario,
        "leave_loading": leave_loading,
        "super": superann,
        "workers_comp": workers_comp,
        "lsl": lsl,
        "travel": travel,
        "gastos_fijos": fijos,
        "total_anual": total,
        "coste_hora_facturable": total / HORAS_FACTURABLES,
        "coste_hora_pagada": total / HORAS_PAGADAS,
        "recargo_pct": (total / salario - 1.0) * 100.0,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", action="store_true")
    args = ap.parse_args(argv)

    filas = []
    for codigo, (oficio, salario, escala) in sorted(OFICIOS.items()):
        c = coste_empresa(salario)
        filas.append({
            "codigo": codigo,
            "oficio": oficio,
            "escala": escala,
            "salario_hora_aud": round(salario, 4),
            "salario_anual": round(c["salario_anual"], 2),
            "leave_loading": round(c["leave_loading"], 2),
            "superannuation": round(c["super"], 2),
            "workers_comp": round(c["workers_comp"], 2),
            "lsl": round(c["lsl"], 2),
            "travel": round(c["travel"], 2),
            "gastos_fijos": round(c["gastos_fijos"], 2),
            "total_anual": round(c["total_anual"], 2),
            "recargo_pct": round(c["recargo_pct"], 1),
            "horas_facturables": round(HORAS_FACTURABLES, 1),
            "coste_hora_aud": round(c["coste_hora_facturable"], 2),
        })

    if args.csv:
        w = csv.DictWriter(sys.stdout, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)
        return 0

    print(f"Modelo de coste empresa — Australia {FECHA}")
    print(f"Awards FWC desde 1/07/2026 · {HORAS_SEMANA:g} h/semana pagadas "
          f"({HORAS_PAGADAS:,.0f} h/año), días de obra de {HORAS_DIA_OBRA:g} h")
    print(f"Vacaciones {DIAS_VACACIONES:g} días + {DIAS_FESTIVOS:g} festivos + "
          f"{DIAS_BAJA:g} de baja + {DIAS_RDO:g} RDO → {DIAS_TRABAJADOS:,.0f} días "
          f"trabajados = {HORAS_FACTURABLES:,.0f} h facturables/año")
    print(f"Super {SUPER_GUARANTEE:.0%} · workers comp {WORKERS_COMP:.2%} · "
          f"LSL {LSL_ACCRUAL:.1%} · travel {TRAVEL_DIARIO:.2f} $/día")
    print()
    print(f"{'recurso':<16}{'oficio':<44}{'$ /h':>8}{'total/año':>11}"
          f"{'recargo':>9}{'$ /h fact.':>11}")
    print("─" * 99)
    for f in filas:
        print(f"{f['codigo']:<16}{f['oficio']:<44}"
              f"{f['salario_hora_aud']:>8.2f}{f['total_anual']:>11,.0f}"
              f"{f['recargo_pct']:>8.1f}%{f['coste_hora_aud']:>11.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
