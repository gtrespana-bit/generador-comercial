#!/usr/bin/env python3
"""Modelo de coste empresa para la mano de obra de Estados Unidos (2026).

Replica para Estados Unidos el criterio ya adoptado en España, el Reino
Unido, Irlanda, Australia y Canadá (``docs/INVESTIGACION_PRECIOS_IRLANDA.md``):
el precio del recurso de mano de obra es el **coste empresa**, no la tarifa
de subcontrata con beneficio, porque el catálogo aplica un margen del 35 %
sobre el coste directo y usar la tarifa de mercado produciría margen sobre
margen.

Salario base ........ Medianas nacionales por ocupación del programa
                      **OEWS del Bureau of Labor Statistics (mayo 2025,
                      publicado el 15/05/2026)**, elevadas un 5 % para
                      expresarlas a octubre de 2026 (≈17 meses a ~3,5 %/año,
                      en línea con el ECI de construcción). Estados Unidos
                      no tiene escala legal sectorial (ni awards ni SEO):
                      el salario mínimo federal (7,25 $/h, sin cambio desde
                      2009) no describe el coste de un oficial, así que la
                      base publicable es la mediana de mercado del BLS —
                      salario bruto en tiempo ordinario según registros de
                      nómina, sin horas extra ni beneficios —, igual que la
                      mediana ONS en el Reino Unido o Job Bank en Canadá.
Cargas .............. FICA empresarial 7,65 % (Seguridad Social 6,2 % con
                      base máxima 2026 de 184.500 $ —no vinculante a
                      salarios de oficio— + Medicare 1,45 % sin techo);
                      FUTA neto 0,6 % sobre los primeros 7.000 $ (42 $/año
                      con el crédito completo por el SUTA); SUTA
                      representativo del 2,7 % sobre los primeros 10.000 $
                      (tipo de nuevo empleador más común; las bases
                      estatales van de 7.000 $ a 78.200 $ y la construcción
                      paga tipos de nuevo empleador superiores en varios
                      estados —Pensilvania 2026: 10,5924 %—); **workers'
                      compensation por código de clase NCCI**, la partida
                      que decide el orden entre oficios (carpintería de
                      estructura ≈7,75/100 $, electricidad ≈4,00, acero de
                      refuerzo ≈10,00) tomada de los rangos nacionales
                      publicados en 2026.
Divisor ............. horas trabajadas en obra: 260 días − 10 de
                      vacaciones − 8 festivos − 3 de enfermedad = 239 días
                      × 8 h = 1.912 h, con 2.080 h pagadas (el PTO es
                      política de empresa, no ley federal: 10+8+3 días es
                      el paquete típico modesto del contratista «open
                      shop»; el BLS sitúa el coste del permiso pagado en
                      construcción en torno al 7-8 % del salario, coherente
                      con 168 h de ausencia pagada).

Perfil territorial: **mediana nacional**. La dispersión estatal/metro del
OEWS es de ±20-40 % por ocupación (HVAC: DC 40,57 $/h frente a Arkansas
23,13; jardinería: DC 23,46 frente a Misisipi 15,21) y los paquetes
sindicales de las grandes metros quedan muy por encima; por eso la matriz
publica la mediana nacional con un rango ancho (−15 % / +35 %) y deja el
ajuste fino al override de empresa, igual que Londres queda en el rango
del Reino Unido o BC/Alberta en el de Canadá.

Queda fuera, a propósito, el **seguro médico y la jubilación voluntarios**:
a diferencia de la pensión británica/irlandesa o el super australiano, no
son obligación federal (el mandato ACA solo afecta a empresas de ≥50
equivalentes a tiempo completo). El BLS (ECEC) cifra los beneficios de
seguro en construcción en ~4 $/h trabajada para quien los ofrece: ese
empleador se sitúa hacia el techo del rango publicado. El modelo es, como
en los demás mercados, el coste estatutario completo del empleador medio
«open shop», no el paquete sindical ni la tarifa de subcontrata 1099.

Uso:
    python3 tools/coste_empresa_eeuu.py            # tabla
    python3 tools/coste_empresa_eeuu.py --csv      # CSV
"""

from __future__ import annotations

import argparse
import csv
import sys

# ─────────────────────────────────────────────────────────────────────────────
# 1. Parámetros del ejercicio 2026
# ─────────────────────────────────────────────────────────────────────────────

FECHA = "2026-10-19"
MONEDA = "USD"

HORAS_SEMANA = 40.0
SEMANAS = 52.0
HORAS_DIA_OBRA = 8.0

DIAS_LABORABLES = 260.0
DIAS_VACACIONES = 10.0     # PTO típico «open shop» (sin mandato federal)
DIAS_FESTIVOS = 8.0        # festivos pagados habituales del sector privado
DIAS_BAJA = 3.0            # enfermedad (mandatos estatales crecientes)

DIAS_TRABAJADOS = (
    DIAS_LABORABLES - DIAS_VACACIONES - DIAS_FESTIVOS - DIAS_BAJA
)                                                   # 239 días
HORAS_FACTURABLES = DIAS_TRABAJADOS * HORAS_DIA_OBRA  # 1.912 h en obra
HORAS_PAGADAS = DIAS_LABORABLES * HORAS_DIA_OBRA      # 2.080 h (PTO pagado)

# FICA 2026 (SSA, 24/10/2025; IRS Pub. 15): Seguridad Social 6,2 % hasta la
# base salarial de 184.500 $ (máximo 11.439 $ por parte) y Medicare 1,45 %
# sin techo. El Additional Medicare Tax (0,9 %) es solo del empleado.
SS_TIPO = 0.062
SS_BASE = 184500.0
MEDICARE_TIPO = 0.0145

# Desempleo: FUTA 6,0 % sobre los primeros 7.000 $ con crédito de hasta el
# 5,4 % por el impuesto estatal pagado → 0,6 % neto = 42 $/año (fuera de
# estados con «credit reduction»). SUTA: cada estado fija tipo y base; el
# 2,7 % sobre 10.000 $ es el nuevo empleador representativo (máx. 270 $).
FUTA_TIPO_NETO = 0.006
FUTA_BASE = 7000.0
SUTA_TIPO = 0.027
SUTA_BASE = 10000.0

# Workers' compensation por código de clase NCCI ($ por cada 100 $ de
# nómina), puntos medios de los rangos nacionales publicados en 2026
# (guías de tarifas 2026 y tarifas presentadas en Florida/Texas/California:
# Texas presenta ≈1/4 de California/Nueva York; la dispersión estatal queda
# dentro del rango de la matriz). Sin techo salarial relevante.
WC = {
    "carp_general": 0.0675,  # 5651 carpintería comercial/general (rango 5-9)
    "carp_estructura": 0.0775,  # 5403/5645 estructura y vivienda (6-14)
    "carp_interior": 0.0490,   # 5437 remate interior y ebanistería instalada
    "albanileria": 0.0600,     # 5022 masonry (FL 5,22 · WI 6,36 · New York 13,17)
    "hormigon": 0.0750,        # 5213 concrete construction (6-16)
    "electricidad": 0.0400,    # 5190 electrical wiring (3,5-9)
    "fontaneria_hvac": 0.0425,  # 5183 plumbing & HVAC (4-10)
    "pintura": 0.0450,         # 5474 painting (FL 4,48)
    "acero_refuerzo": 0.1000,  # 5059/5102 banda de montaje de acero (>10)
    "drywall": 0.0500,         # 5445 wallboard installation (banda interior)
    "revestimientos": 0.0450,  # 5348 tile / 5478 floor covering
    "vidrieria": 0.0525,       # 5462 glazing
    "soldadura": 0.0550,       # trabajo de metal en obra
    "jardineria": 0.0500,      # 9102 lawn care / landscaping
    "peon_obra": 0.0700,       # peonaje general (banda hormigón/albañilería)
}

# Gastos fijos anuales por operario (equivalentes a los de ES/GB/IE/AU/CA,
# sin plan médico: ver la nota de alcance en la cabecera).
GASTOS_FIJOS = {
    # EPI, ropa de trabajo y herramienta menor repuesta cada año.
    "epi_y_herramienta": 650.0,
    # OSHA 10/30, licencias estatales de oficio y formación continua.
    "formacion_y_licencias": 300.0,
    # Gestión de nómina (941/W-2, «certified payroll» cuando aplica).
    "gestion_nomina": 320.0,
    # Licencia de contratista, «bonding» menor y seguros de herramienta.
    "licencias_y_seguros_menores": 350.0,
}


# ─────────────────────────────────────────────────────────────────────────────
# 2. Salarios adoptados — medianas OEWS mayo 2025 llevadas a 2026
#
#    Las medianas son las del OEWS de mayo de 2025 (publicado el
#    15/05/2026). `_bls` las eleva un 5 % hasta octubre de 2026. Dos
#    oficios se adoptan directamente a valor corriente de 2026 con la
#    evidencia indicada (sin el +5 %).
# ─────────────────────────────────────────────────────────────────────────────

def _bls(mediana: float) -> float:
    """Mediana OEWS mayo-2025 expresada en $/h de octubre de 2026."""
    return round(mediana * 1.05, 2)


# Código de recurso -> (oficio EE. UU., $/h ordinario adoptado, origen,
#                       clase de workers' compensation)
OFICIOS: dict[str, tuple[str, float, str, str]] = {
    # Oficial general: mediana del carpintero (47-2031), el oficio ancla.
    "MO-OF1":       ("Journeyman carpenter (general)", _bls(29.12),
                     "BLS OEWS 47-2031 mediana 29,12", "carp_general"),
    # Colocador de pavimentos (floor layers, 47-2042).
    "MO-OF1-PISO":  ("Floor layer", _bls(27.15),
                     "BLS OEWS 47-2042 mediana 27,15", "revestimientos"),
    # Enchapador (tile and stone setters, 47-2044).
    "MO-OF1-ALI":   ("Tile and stone setter", _bls(26.77),
                     "BLS OEWS 47-2044 mediana 26,77", "revestimientos"),
    # Albañil de ladrillo y bloque (47-2021).
    "MO-OF1-ALB":   ("Brick/block mason", _bls(29.87),
                     "BLS OEWS 47-2021 mediana 29,87", "albanileria"),
    # Montador de tabiques: instaladores de drywall **y encintadores**
    # (la ocupación combinada del OOH: 59.780 $/año), porque en la obra
    # pequeña el mismo oficial instala y acaba.
    "MO-OF1-MON":   ("Drywall installer and taper", _bls(28.74),
                     "BLS OEWS/OOH 47-2081+2082 mediana 28,74", "drywall"),
    # Ayudante especializado: se adopta la **media** del peón (25,02),
    # que captura al peón experimentado (la mediana es el MO-AYU).
    "MO-AYU-ESP":   ("Skilled construction labourer", _bls(25.02),
                     "BLS OEWS 47-2061 media 25,02", "peon_obra"),
    # Peón (construction laborers, 47-2061).
    "MO-AYU":       ("Construction laborer", _bls(22.66),
                     "BLS OEWS 47-2061 mediana 22,66", "peon_obra"),
    # Pintor de construcción y mantenimiento (47-2141: 49.400 $/año).
    "MO-OF1-PIN":   ("Painter (construction)", _bls(23.75),
                     "BLS OEWS 47-2141 mediana 23,75", "pintura"),
    # Fontanero (47-2152: plumbers, pipefitters and steamfitters).
    "MO-OF1-PLO":   ("Plumber", _bls(30.67),
                     "BLS OEWS 47-2152 mediana 30,67", "fontaneria_hvac"),
    # Electricista (47-2111).
    "MO-OF1-ELE":   ("Electrician", _bls(30.38),
                     "BLS OEWS 47-2111 mediana 30,38", "electricidad"),
    # Cabillero (reinforcing iron and rebar workers, 47-2171): a
    # diferencia de Canadá, el OEWS sí publica su mediana propia.
    "MO-OF1-CAB":   ("Reinforcing ironworker (rodman)", _bls(28.35),
                     "BLS OEWS 47-2171 mediana 28,35", "acero_refuerzo"),
    # Carpintero de obra (encofrado): misma mediana, clase de estructura.
    "MO-OF1-CARP":  ("Formwork carpenter", _bls(29.12),
                     "BLS OEWS 47-2031 mediana 29,12", "carp_estructura"),
    # Soldador (51-4121: welders, cutters, solderers and brazers).
    "MO-OF1-SOLD":  ("Welder", _bls(25.84),
                     "BLS OEWS 51-4121 mediana 25,84", "soldadura"),
    # Ebanista de taller (cabinetmakers and bench carpenters, 51-7011),
    # sistemáticamente por debajo del carpintero de obra.
    "MO-OF1-CARPM": ("Cabinetmaker", _bls(22.44),
                     "BLS OEWS 51-7011 mediana 22,44", "carp_interior"),
    # Vidriero (47-2121: 57.080 $/año).
    "MO-OF1-VIDR":  ("Glazier", _bls(27.44),
                     "BLS OEWS 47-2121 mediana 27,44", "vidrieria"),
    # Técnico de climatización (49-9021).
    "MO-OF1-AC":    ("HVAC mechanic/installer", _bls(29.33),
                     "BLS OEWS 49-9021 mediana 29,33", "fontaneria_hvac"),
    # Jardinero-paisajista oficial: la mediana de landscaping and
    # groundskeeping workers (37-3011, 18,82 $/h = 39.150 $/año) es de
    # mantenimiento; el oficial de «landscape construction» (hardscape)
    # se adopta a 20,50 $/h corrientes (~+9 % sobre la mediana 2025).
    "MO-OF1-JARD":  ("Landscape construction worker", 20.50,
                     "BLS OEWS 37-3011 mediana 18,82 (oficial ≈ +9 %)",
                     "jardineria"),
}


# ─────────────────────────────────────────────────────────────────────────────
# 3. Cálculo
# ─────────────────────────────────────────────────────────────────────────────

def coste_empresa(salario_hora: float, wc: float = WC["peon_obra"]) -> dict:
    """Coste empresa por hora trabajada a partir del salario ordinario $/h.

    ``bruto`` son las 2.080 h pagadas (el PTO va dentro, como es práctica
    estadounidense). El FICA respeta la base de la Seguridad Social; el
    FUTA/SUTA, sus bases; el workers' compensation se aplica por la clase
    de riesgo del oficio sobre toda la nómina.
    """
    salario = salario_hora * HORAS_PAGADAS
    bruto = salario
    fica = SS_TIPO * min(bruto, SS_BASE) + MEDICARE_TIPO * bruto
    desempleo = (
        FUTA_TIPO_NETO * min(bruto, FUTA_BASE)
        + SUTA_TIPO * min(bruto, SUTA_BASE)
    )
    wc_coste = wc * bruto
    fijos = sum(GASTOS_FIJOS.values())
    total = bruto + fica + desempleo + wc_coste + fijos
    return {
        "salario_anual": salario,
        "fica": fica,
        "desempleo": desempleo,
        "wc": wc_coste,
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
    for codigo, (oficio, salario, escala, clase) in sorted(OFICIOS.items()):
        c = coste_empresa(salario, WC[clase])
        filas.append({
            "codigo": codigo,
            "oficio": oficio,
            "escala": escala,
            "wc_clase": clase,
            "salario_hora_usd": round(salario, 4),
            "salario_anual": round(c["salario_anual"], 2),
            "fica": round(c["fica"], 2),
            "desempleo": round(c["desempleo"], 2),
            "wc": round(c["wc"], 2),
            "gastos_fijos": round(c["gastos_fijos"], 2),
            "total_anual": round(c["total_anual"], 2),
            "recargo_pct": round(c["recargo_pct"], 1),
            "horas_facturables": round(HORAS_FACTURABLES, 1),
            "coste_hora_usd": round(c["coste_hora_facturable"], 2),
        })

    if args.csv:
        w = csv.DictWriter(sys.stdout, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)
        return 0

    print(f"Modelo de coste empresa — Estados Unidos {FECHA} (mediana nacional)")
    print(f"BLS OEWS may-2025 × 1,05 · {HORAS_SEMANA:g} h/semana, "
          f"{HORAS_PAGADAS:,.0f} h pagadas (PTO incluido)")
    print(f"Vacaciones {DIAS_VACACIONES:g} días + {DIAS_FESTIVOS:g} festivos + "
          f"{DIAS_BAJA:g} de baja → {DIAS_TRABAJADOS:,.0f} días trabajados "
          f"= {HORAS_FACTURABLES:,.0f} h facturables/año")
    print(f"FICA SS {SS_TIPO:.1%} (tope {SS_BASE:,.0f} $) + Medicare "
          f"{MEDICARE_TIPO:.2%} · FUTA neto {FUTA_TIPO_NETO:.1%} · SUTA "
          f"{SUTA_TIPO:.1%} · workers' comp por clase NCCI")
    print()
    print(f"{'recurso':<16}{'oficio':<40}{'$ /h':>8}{'total/año':>11}"
          f"{'recargo':>9}{'$ /h fact.':>11}")
    print("─" * 95)
    for f in filas:
        print(f"{f['codigo']:<16}{f['oficio']:<40}"
              f"{f['salario_hora_usd']:>8.2f}{f['total_anual']:>11,.0f}"
              f"{f['recargo_pct']:>8.1f}%{f['coste_hora_usd']:>11.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
