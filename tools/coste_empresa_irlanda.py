#!/usr/bin/env python3
"""Modelo de coste empresa para la mano de obra irlandesa (2026).

Replica para Irlanda el criterio ya adoptado en España y en el Reino Unido
(``docs/INVESTIGACION_PRECIOS_ESPANA.md``,
``docs/INVESTIGACION_PRECIOS_REINO_UNIDO.md``): el precio del recurso de mano
de obra es el **coste empresa**, no la tarifa de autónomo con beneficio,
porque el catálogo aplica un margen del 35 % sobre el coste directo y usar
la tarifa de mercado produciría margen sobre margen.

Salario base ........ Construction Sector SEO (Sectoral Employment Order)
                      vigente desde el 1 de agosto de 2026 para los oficios
                      de obra general. Los SEO eléctrico y mecánico fueron
                      anulados por los tribunales (eléctrico 2020/2022,
                      mecánico 2023), así que electricistas usan la escala
                      pactada AECI/Connect del 16 de febrero de 2026 y
                      fontaneros/climatización la escala Connect del
                      sector mecánico vigente desde el 1 de mayo de 2026.
Cargas .............. PRSI empresa (11,40 % desde el 1 de octubre de 2026,
                      sin techo), CWPS (pensión + muerte en servicio +
                      enfermedad, 36,43 €/semana empresa desde el 3 de
                      agosto de 2026), vacaciones de la industria
                      (builders' holidays), bajas y gastos fijos.
Divisor ............. horas facturables reales (no las horas contratadas),
                      igual que el criterio español de 1.400-1.736 h.

Diferencia deliberada con el Reino Unido: allí el salario adoptado (mediana
ONS) quedaba por encima del mínimo de convenio, así que el rango de la
matriz pudo bajar un 10 %. Aquí la base ES el mínimo legal o pactado, que en
Irlanda es nacional y no admite rebaja regional: el rango de la matriz solo
varía −3 % (estructura de gastos) y +20 % (Dublín y pagas sobre el SEO).

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

FECHA = "2026-10-19"
MONEDA = "EUR"

# Jornada del Construction SEO: 39 h/semana (lunes a viernes). Las escalas
# AECI y Connect usan la misma semana de 39 h.
HORAS_SEMANA = 39.0
SEMANAS = 52.0
HORAS_CONTRATADAS = HORAS_SEMANA * SEMANAS          # 2.028 h
HORAS_DIA = HORAS_SEMANA / 5.0                      # 7,8 h

# Vacaciones: mínimo estatutario de 20 días (4 semanas, Organisation of
# Working Time Act 1997) + 1 día de industria en el calendario de
# builders' holidays de la CIF (el Viernes Santo no es festivo público en
# Irlanda y la industria lo cierra como día de vacaciones) = 21 días
# fijados en periodos cerrados (Navidad, Semana Santa, dos últimas semanas
# de julio…). Festivos públicos: 10 al año.
DIAS_VACACIONES = 21.0
DIAS_FESTIVOS = 10.0
HORAS_VACACIONES = (DIAS_VACACIONES + DIAS_FESTIVOS) * HORAS_DIA  # 241,8 h

# Bajas: 5 días/año, el derecho estatutario de enfermedad retribuida
# vigente en 2026 (Statutory Sick Pay, 70 % con tope de 110 €/día; la
# ampliación a 7-10 días quedó en pausa) y en línea con el absentismo
# medio del sector. El esquema CWPS cubre la enfermedad larga.
DIAS_BAJA = 5.0
HORAS_BAJA = DIAS_BAJA * HORAS_DIA                  # 39,0 h

HORAS_FACTURABLES = HORAS_CONTRATADAS - HORAS_VACACIONES - HORAS_BAJA  # 1.747,2

# PRSI empresa clase A: 11,40 % desde el 1 de octubre de 2026 (11,25 %
# hasta el 30 de septiembre), sobre todo el salario y sin techo. La tasa
# reducida (9,15 %) solo aplica a salarios semanales de hasta 552 €; el
# oficio peor pagado de esta tabla gana 833,43 €/semana (21,37 × 39), así
# que la tasa plena aplica a los 17 oficios.
PRSI_EMPRESA = 0.1140
PRSI_UMBRAL_SEMANAL = 552.0

# CWPS (Construction Workers Pension Scheme), cuota empresa semanal desde
# el 3 de agosto de 2026: pensión 32,89 € + cobertura por muerte en
# servicio 1,17 € + fondo de enfermedad 2,37 € = 36,43 €/semana. El SEO
# impone la afiliación; se cotizan las 52 semanas.
CWPS_EMPRESA_SEMANAL = 36.43
CWPS_ANUAL = CWPS_EMPRESA_SEMANAL * SEMANAS         # 1.894,36 €


# Gastos fijos anuales por operario (equivalentes a los que España agrupa
# como «costes fijos»: EPI, herramienta, gestor de nóminas, formación,
# seguro, previsión de despido). Se expresan por operario y por año.
GASTOS_FIJOS = {
    # Seguro combinado de obra / responsabilidad de empleador prorrateado.
    "seguro_empleador": 250.0,
    # EPI, ropa de trabajo y herramienta menor repuesta cada año.
    "epi_y_herramienta": 400.0,
    # Safe Pass, tarjetas CSCS (planta/andamios) y manual handling.
    "formacion": 180.0,
    # Gestoría de nóminas.
    "gestion_nomina": 120.0,
    # Previsión de despido: la redundancy estatutaria irlandesa devenga 2
    # semanas por año de servicio con tope de 600 €/semana (más 1 semana
    # extra). Se provisiona 1 semana al tope por año: no todo el personal
    # termina cobrándola, y provisionar las 2 semanas íntegras doblaría el
    # criterio usado en España y el Reino Unido (1 semana/año).
    "prevision_despido": 600.0,
}


# ─────────────────────────────────────────────────────────────────────────────
# 2. Escalas salariales irlandesas
#
#    SEO     = Construction Sector Sectoral Employment Order (S.I. del
#              sector de la construcción), mínimos legales desde el
#              1/08/2026 (Workplace Relations Commission).
#    AECI    = escala pactada AECI/Connect para electricistas, 16/02/2026
#              (+3,4 %; el SEO eléctrico fue anulado y no hay orden en
#              vigor, pero la escala es la referencia del sector).
#    CONNECT = escala recomendada Connect para el sector mecánico
#              (fontanería, calefacción, climatización), 01/05/2026
#              (+3,2 %; el SEO mecánico fue anulado en 2023).
# ─────────────────────────────────────────────────────────────────────────────

SEO = {
    # Categoría                        €/hora desde 01/08/2026
    "craftsperson": 23.74,   # albañiles, carpinteros, pintores, yeseros…
    "category_a": 23.03,     # steel fixers, andamistas, operadores de grúa…
    "category_b": 21.37,     # general operatives con más de 2 años
    "new_entrant": 17.28,    # solo los 2 primeros años en la industria
}

AECI = {
    # Años tras completar el aprendizaje   €/hora desde 16/02/2026
    "ano_1": 27.06,
    "ano_2": 27.44,
    "ano_3": 27.60,
    "ano_4": 27.75,
    "ano_5": 27.92,
    "ano_6": 28.04,
    "ano_11": 28.48,         # tope de antigüedad (long service)
}

CONNECT = {
    # Años de oficial cualificado         €/hora desde 01/05/2026
    "ano_1": 28.51,
    "ano_2": 28.92,
    "ano_3": 29.12,
    "ano_4": 29.28,
    "ano_5": 29.45,
    "ano_6": 29.63,
    "ano_10": 30.01,         # tope de antigüedad (long service rate)
}

# Código de recurso -> (oficio irlandés, €/h adoptado, escala de origen)
#
# Criterio: oficial «a mitad de carrera». En el SEO la categoría ya es el
# grado; en las escalas AECI/Connect se adopta el 3.er año de oficial
# cualificado (ni el recién titulado ni el tope de antigüedad). Los
# extremos de cada escala quedan dentro del rango de la matriz.
OFICIOS: dict[str, tuple[str, float, str]] = {
    # Oficial general de obra.
    "MO-OF1":       ("General builder (craftsperson)", SEO["craftsperson"],
                     "SEO craftsperson"),
    # Colocador de pavimentos: el SEO lista expresamente a los floor layers.
    "MO-OF1-PISO":  ("Floor layer", SEO["craftsperson"], "SEO craftsperson"),
    # Enchapador / alicatador: slaters and tilers en la lista del SEO.
    "MO-OF1-ALI":   ("Wall and floor tiler", SEO["craftsperson"],
                     "SEO craftsperson"),
    # Albañil: bricklayers/stone layers en la lista del SEO.
    "MO-OF1-ALB":   ("Bricklayer", SEO["craftsperson"], "SEO craftsperson"),
    # Montador de prefabricados de interior: trabajo de carpintería de
    # taller/obra (joinery) en la práctica irlandesa.
    "MO-OF1-MON":   ("Interior fit-out installer (joiner)",
                     SEO["craftsperson"], "SEO craftsperson"),
    # Ayudante especializado: general operative experto; la categoría A del
    # SEO agrupa los oficios auxiliares cualificados (steel fixers,
    # andamistas avanzados, operadores de planta pesada, banksmen).
    "MO-AYU-ESP":   ("Skilled general operative", SEO["category_a"],
                     "SEO category A"),
    # Peón: general operative con más de 2 años. No se usa la tarifa de
    # new entrant (17,28 €): es un grado temporal de incorporación, no el
    # salario permanente de un peón, y aplicarlo a todas las horas de peón
    # infringiría el SEO a partir del segundo año.
    "MO-AYU":       ("General operative (labourer)", SEO["category_b"],
                     "SEO category B"),
    # Pintor: painters en la lista del SEO.
    "MO-OF1-PIN":   ("Painter and decorator", SEO["craftsperson"],
                     "SEO craftsperson"),
    # Fontanero: sector mecánico (sin SEO en vigor desde 2023).
    "MO-OF1-PLO":   ("Plumber / pipefitter", CONNECT["ano_3"],
                     "Connect mecánico, 3.er año"),
    # Electricista: sin SEO en vigor; escala pactada AECI.
    "MO-OF1-ELE":   ("Electrician", AECI["ano_3"], "AECI, 3.er año"),
    # Cabillero / armador de acero: el SEO clasifica expresamente a los
    # steel fixers en la categoría A, NO como craftsperson. Es la
    # diferencia más llamativa frente a otros mercados y se respeta.
    "MO-OF1-CAB":   ("Steel fixer", SEO["category_a"], "SEO category A"),
    # Carpintero de obra (encofrador): carpenters en la lista del SEO.
    "MO-OF1-CARP":  ("Formwork carpenter / shuttering carpenter",
                     SEO["craftsperson"], "SEO craftsperson"),
    # Soldador: no aparece en la lista de crafts del SEO de construcción;
    # el soldador de tubería/estructura trabaja bajo la referencia del
    # sector mecánico (pipefitter-welder).
    "MO-OF1-SOLD":  ("Welder / pipefitter-welder", CONNECT["ano_3"],
                     "Connect mecánico, 3.er año"),
    # Carpintero de madera estructural: carpenters and joiners del SEO.
    "MO-OF1-CARPM": ("Carpenter and joiner", SEO["craftsperson"],
                     "SEO craftsperson"),
    # Vidriero: glaziers en la lista del SEO.
    "MO-OF1-VIDR":  ("Glazier", SEO["craftsperson"], "SEO craftsperson"),
    # Técnico de refrigeración y climatización: building services,
    # referencia del sector mecánico.
    "MO-OF1-AC":    ("HVAC and refrigeration engineer", CONNECT["ano_3"],
                     "Connect mecánico, 3.er año"),
    # Jardinero: el paisajismo queda fuera del SEO de construcción; se
    # asimila al general operative con experiencia (categoría B).
    "MO-OF1-JARD":  ("Landscape operative", SEO["category_b"],
                     "SEO category B (asimilado)"),
}


# ─────────────────────────────────────────────────────────────────────────────
# 3. Cálculo
# ─────────────────────────────────────────────────────────────────────────────

def coste_empresa(salario_hora: float) -> dict:
    """Coste empresa por hora facturable a partir del salario por hora."""
    salario = salario_hora * HORAS_CONTRATADAS
    # Todos los oficios superan el umbral semanal de la tasa reducida; si
    # algún día se modelara un aprendiz habría que partir la cotización.
    assert salario_hora * HORAS_SEMANA > PRSI_UMBRAL_SEMANAL, (
        "Salario bajo el umbral PRSI: la tasa reducida del 9,15 % exigiría "
        "otro cálculo"
    )
    prsi = salario * PRSI_EMPRESA
    fijos = sum(GASTOS_FIJOS.values())
    total = salario + prsi + CWPS_ANUAL + fijos
    return {
        "salario_anual": salario,
        "prsi": prsi,
        "cwps": CWPS_ANUAL,
        "gastos_fijos": fijos,
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
    for codigo, (oficio, salario, escala) in sorted(OFICIOS.items()):
        c = coste_empresa(salario)
        filas.append({
            "codigo": codigo,
            "oficio": oficio,
            "escala": escala,
            "salario_hora_eur": salario,
            "salario_anual": round(c["salario_anual"], 2),
            "prsi_empresa": round(c["prsi"], 2),
            "cwps": round(c["cwps"], 2),
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
    print(f"Jornada SEO {HORAS_SEMANA:g} h/semana · contratadas "
          f"{HORAS_CONTRATADAS:,.0f} h/año")
    print(f"Vacaciones {DIAS_VACACIONES:g} días + {DIAS_FESTIVOS:g} festivos "
          f"({HORAS_VACACIONES:,.1f} h) · bajas {DIAS_BAJA:g} días "
          f"({HORAS_BAJA:,.1f} h) → facturables {HORAS_FACTURABLES:,.1f} h/año")
    print()
    print(f"{'recurso':<16}{'oficio':<44}{'€/h':>7}{'total/año':>11}"
          f"{'recargo':>9}{'€/h fact.':>11}")
    print("─" * 98)
    for f in filas:
        print(f"{f['codigo']:<16}{f['oficio']:<44}"
              f"{f['salario_hora_eur']:>7.2f}{f['total_anual']:>11,.0f}"
              f"{f['recargo_pct']:>8.1f}%{f['coste_hora_eur']:>11.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
