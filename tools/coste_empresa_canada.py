#!/usr/bin/env python3
"""Modelo de coste empresa para la mano de obra canadiense (2026).

Replica para Canadá el criterio ya adoptado en España, el Reino Unido,
Irlanda y Australia (``docs/INVESTIGACION_PRECIOS_IRLANDA.md``): el precio
del recurso de mano de obra es el **coste empresa**, no la tarifa de
subcontrata con beneficio, porque el catálogo aplica un margen del 35 %
sobre el coste directo y usar la tarifa de mercado produciría margen sobre
margen.

Salario base ........ Medianas salariales oficiales del **Job Bank del
                      Gobierno de Canadá** para Ontario (actualizadas el
                      19/11/2025 con periodo de referencia 2023-24 de la
                      Labour Force Survey de Statistics Canada), elevadas
                      un 5 % (≈2,5 %/año) para expresarlas a octubre de
                      2026. Es el mismo enfoque que el Reino Unido (mediana
                      ONS): Canadá **no tiene** una escala legal sectorial
                      como el SEO irlandés o los awards australianos — el
                      mínimo general de Ontario (17,60 $/h) no describe el
                      coste de un oficial —, así que la base publicable es
                      la mediana de mercado, no un suelo legal.
Cargas .............. CPP empresa 5,95 % con exención de 3.500 $ y techo
                      (YMPE 74.600 $ en 2026) + CPP2 del 4 % entre el YMPE
                      y el YAMPE (85.000 $); EI empresa 2,282 % (1,4 × el
                      1,63 % del empleado) con techo de ganancias
                      asegurables de 68.900 $; WSIB de Ontario por clase de
                      construcción (G1 residencial 2,18 $/100 $; G3
                      cimentación/estructura/exterior 3,55; G4
                      instalaciones 1,54; G5 oficios de acabado 2,15);
                      vacation pay del 4 % (mínimo ESA de Ontario) y los
                      9 festivos estatutarios pagados; gastos fijos
                      (beneficios de grupo, EPI, formación, nómina,
                      previsión de terminación ESA).
Divisor ............. horas trabajadas en obra: 260 días − 10 de vacaciones
                      (2 semanas ESA) − 9 festivos − 3 de baja (el ESA da
                      3 días protegidos pero **no pagados**) = 238 días ×
                      8 h = 1.904 h. Es el divisor menos duro de los
                      mercados anglófonos (IE 1.747 h; AU 1.688 h), porque
                      el ESA solo garantiza 2 semanas de vacaciones.

Perfil provincial: **Ontario**. Es el mayor mercado de construcción del
país (~40 % de la actividad) y el único para el que el Job Bank publica
medianas por oficio con la granularidad necesaria. El CPP/EI son federales
(salvo Quebec: QPP/QPIP) y el WSIB es el seguro de Ontario; otras
provincias (WorkSafeBC, WCB Alberta, CNESST) mueven el coste dentro del
rango publicado (−10 % / +25 %).

Quedan fuera, a propósito:
* El **Employer Health Tax** de Ontario (1,95 %): los primeros 1.000.000 $
  de nómina están exentos, así que la pyme tipo de CotizaT no lo paga. Es
  el mismo criterio que con el payroll tax australiano.
* Los paquetes de los **convenios colectivos ICI** (LIUNA 183/527,
  Carpenters' Local 27…): el «total package» sindical del GTA (peón
  ≈54-61 $/h todo incluido, tablas públicas de LIUNA 527) queda un
  35-50 % por encima de este modelo *open-shop*. La matriz representa al
  empleador mediano no sindicalizado; el rango +25 % cubre la dispersión
  regional (Alberta/BC) pero no pretende reproducir el convenio ICI, igual
  que en Australia el suelo publicable era el award y no el EBA.

Uso:
    python3 tools/coste_empresa_canada.py            # tabla
    python3 tools/coste_empresa_canada.py --csv      # CSV
"""

from __future__ import annotations

import argparse
import csv
import sys

# ─────────────────────────────────────────────────────────────────────────────
# 1. Parámetros del ejercicio 2026
# ─────────────────────────────────────────────────────────────────────────────

FECHA = "2026-10-19"
MONEDA = "CAD"

HORAS_SEMANA = 40.0
SEMANAS = 52.0
HORAS_DIA_OBRA = 8.0

DIAS_LABORABLES = 260.0
DIAS_VACACIONES = 10.0     # ESA Ontario: 2 semanas (3 tras 5 años)
DIAS_FESTIVOS = 9.0        # Ontario: 9 public holidays pagados
DIAS_BAJA = 3.0            # ESA: 3 días protegidos, NO pagados

DIAS_TRABAJADOS = (
    DIAS_LABORABLES - DIAS_VACACIONES - DIAS_FESTIVOS - DIAS_BAJA
)                                                   # 238 días
HORAS_FACTURABLES = DIAS_TRABAJADOS * HORAS_DIA_OBRA  # 1.904 h en obra
# Horas pagadas a tarifa ordinaria: las trabajadas + los festivos
# estatutarios. Las vacaciones se pagan aparte como «vacation pay» (4 %
# sobre el salario bruto), que es la forma estándar canadiense de liquidar
# las 2 semanas cuando se paga por horas.
HORAS_PAGADAS = HORAS_FACTURABLES + DIAS_FESTIVOS * HORAS_DIA_OBRA  # 1.976 h

VACATION_PAY = 0.04        # mínimo ESA (6 % tras 5 años de servicio)

# CPP 2026 (CRA/ESDC): 5,95 % empresa y empleado, exención básica 3.500 $,
# YMPE 74.600 $ (máximo 4.230,45 $); CPP2 del 4 % entre YMPE e YAMPE
# (85.000 $, máximo 416 $). El techo importa: los oficios de estructura lo
# alcanzan, y un % plano sobrevaloraría su coste.
CPP_TIPO = 0.0595
CPP_EXENCION = 3500.0
CPP_YMPE = 74600.0
CPP2_TIPO = 0.04
CPP_YAMPE = 85000.0

# EI 2026 (CEIC, 12/09/2025): empleado 1,63 % y empresa 1,4 × = 2,282 %,
# con máximo de ganancias asegurables de 68.900 $ (máximo empresa
# 1.572,30 $). Quebec tiene tipo reducido (QPIP aparte); perfil Ontario.
EI_TIPO_EMPRESA = 0.02282
EI_TOPE = 68900.0

# WSIB Ontario 2026, clases de construcción ($ por cada 100 $ de nómina
# asegurable; techo de ganancias asegurables 121.700 $, no vinculante a
# estos salarios). La media de todas las empresas baja a 1,23 $/100 $,
# pero la construcción paga por clase de riesgo.
WSIB_TECHO = 121700.0
WSIB = {
    "G1": 0.0218,   # construcción residencial (general)
    "G3": 0.0355,   # cimentación, estructura y envolvente
    "G4": 0.0154,   # instalaciones del edificio (eléctr., fontanería, HVAC)
    "G5": 0.0215,   # oficios especializados de acabado
}

# Gastos fijos anuales por operario (equivalentes a los de ES/GB/IE/AU,
# más el plan de beneficios de grupo, que en Canadá es la vía habitual de
# cubrir salud/dental porque el sistema público no cubre dental ni
# medicamentos de adultos en Ontario).
GASTOS_FIJOS = {
    # Plan de beneficios de grupo (salud, dental, LTD) de pyme constructora.
    "beneficios_grupo": 2400.0,
    # EPI, ropa de trabajo y herramienta menor repuesta cada año.
    "epi_y_herramienta": 700.0,
    # Working at Heights, WHMIS, licencias de oficio (Skilled Trades Ontario).
    "formacion_y_licencias": 300.0,
    # Gestión de nómina (PDOC, T4, ROE).
    "gestion_nomina": 320.0,
    # Previsión de terminación: el ESA exige 1 semana de aviso por año
    # (más severance tras 5 años en empresas de nómina ≥2,5 M$).
    "prevision_terminacion": 400.0,
}


# ─────────────────────────────────────────────────────────────────────────────
# 2. Salarios adoptados — medianas Job Bank Ontario llevadas a 2026
#
#    Las medianas son las publicadas el 19/11/2025 (referencia 2023-24,
#    LFS / EI Survey Data). `_jb` las eleva un 5 % hasta octubre de 2026.
#    Cuatro oficios no tienen mediana Job Bank directamente utilizable y se
#    valoran a fecha de 2026 con la evidencia indicada en cada caso (sin
#    el +5 %, porque ya son valores corrientes).
# ─────────────────────────────────────────────────────────────────────────────

def _jb(mediana: float) -> float:
    """Mediana Job Bank 2023-24 expresada en $/h de octubre de 2026."""
    return round(mediana * 1.05, 2)


# Código de recurso -> (oficio canadiense, $/h ordinario adoptado, origen,
#                       clase WSIB)
OFICIOS: dict[str, tuple[str, float, str, str]] = {
    # Oficial general: mediana del carpintero, el oficio «ancla» de la obra
    # canadiense (en Toronto la mediana sube a 36,00 $: rango).
    "MO-OF1":       ("Journeyman carpenter (general)", _jb(32.00),
                     "Job Bank ON mediana carpenter 32,00", "G1"),
    # Colocador de pavimentos (floor covering installer).
    "MO-OF1-PISO":  ("Floor covering installer", _jb(26.00),
                     "Job Bank ON mediana floor covering 26,00", "G5"),
    # Enchapador (tile installer).
    "MO-OF1-ALI":   ("Tile installer", _jb(31.92),
                     "Job Bank ON mediana tile installer 31,92", "G5"),
    # Albañil: la mediana más alta de los oficios de obra general.
    "MO-OF1-ALB":   ("Bricklayer", _jb(38.00),
                     "Job Bank ON mediana bricklayer 38,00", "G3"),
    # Montador de tabiques y falsos techos: instalador/acabador de drywall.
    "MO-OF1-MON":   ("Drywall installer and finisher", _jb(35.48),
                     "Job Bank ON mediana drywall finisher 35,48", "G5"),
    # Ayudante especializado: sin mediana propia; peón de hormigón
    # experimentado (Indeed, sep-2026: 29,83 $/h).
    "MO-AYU-ESP":   ("Skilled construction labourer", 30.00,
                     "Indeed ON concrete labourer 29,83 (2026)", "G1"),
    # Peón: mediana del construction labourer and helper.
    "MO-AYU":       ("Construction labourer", _jb(27.00),
                     "Job Bank ON mediana labourer 27,00", "G1"),
    # Pintor.
    "MO-OF1-PIN":   ("Painter and decorator", _jb(25.00),
                     "Job Bank ON mediana painter 25,00", "G5"),
    # Fontanero con licencia (journeyperson plumber).
    "MO-OF1-PLO":   ("Journeyperson plumber", _jb(32.50),
                     "Job Bank ON mediana plumber 32,50", "G4"),
    # Electricista de construcción y mantenimiento.
    "MO-OF1-ELE":   ("Construction electrician", _jb(34.00),
                     "Job Bank ON mediana electrician 34,00", "G4"),
    # Cabillero: el «reinforcing rodworker» es un suboficio del ironworker
    # (mediana ON 44,34, que mezcla estructura y armadura). Las escalas
    # provinciales que separan ambos (p. ej. Manitoba ICI) ponen la
    # armadura ≈13 % por debajo: 44,34 × 1,05 × 0,87 ≈ 40,50.
    "MO-OF1-CAB":   ("Reinforcing rodworker", 40.50,
                     "Job Bank ON ironworker 44,34 × 0,87 (rodwork)", "G3"),
    # Carpintero de obra (encofrado): misma mediana que el oficial general,
    # pero clase WSIB de estructura.
    "MO-OF1-CARP":  ("Formwork carpenter", _jb(32.00),
                     "Job Bank ON mediana carpenter 32,00", "G3"),
    # Soldador: Job Bank da 28,00 (mezcla manufactura); Indeed Ontario,
    # oct-2026, 30,41. Se adopta 30,00 como valor corriente de obra.
    "MO-OF1-SOLD":  ("Welder", 30.00,
                     "Job Bank ON 28,00 / Indeed ON 30,41 (2026)", "G5"),
    # Carpintero de taller/mueblista: mediana de cabinetmaker (taller,
    # sistemáticamente por debajo del carpintero de obra).
    "MO-OF1-CARPM": ("Cabinetmaker", _jb(25.00),
                     "Job Bank ON mediana cabinetmaker 25,00", "G5"),
    # Vidriero: sin mediana provincial localizada (Job Bank Ottawa:
    # 22,94-43,60); se adopta el nivel de la mediana de BC (≈30 $/h).
    "MO-OF1-VIDR":  ("Glazier", 30.00,
                     "estimado Job Bank (rango ON 22,94-43,60)", "G5"),
    # Técnico de refrigeración y aire acondicionado (313A).
    "MO-OF1-AC":    ("HVAC / refrigeration mechanic", _jb(37.00),
                     "Job Bank ON mediana HVAC mechanic 37,00", "G4"),
    # Jardinero-paisajista de obra: entre el landscape worker (20,96) y el
    # landscaper técnico (31,05); oficial de landscape construction.
    "MO-OF1-JARD":  ("Landscape construction worker", 28.00,
                     "Job Bank ON landscape worker 20,96 – landscaper 31,05",
                     "G5"),
}


# ─────────────────────────────────────────────────────────────────────────────
# 3. Cálculo
# ─────────────────────────────────────────────────────────────────────────────

def coste_empresa(salario_hora: float, wsib: float = WSIB["G1"]) -> dict:
    """Coste empresa por hora trabajada a partir del salario ordinario $/h.

    ``bruto`` es la base de cotización: horas trabajadas + festivos
    estatutarios, más el vacation pay del 4 %. El CPP respeta la exención,
    el YMPE y el CPP2; el EI, su techo; el WSIB se aplica por la clase de
    riesgo del oficio.
    """
    salario = salario_hora * HORAS_PAGADAS
    vacation_pay = salario * VACATION_PAY
    bruto = salario + vacation_pay
    cpp = (
        CPP_TIPO * min(max(bruto - CPP_EXENCION, 0.0), CPP_YMPE - CPP_EXENCION)
        + CPP2_TIPO * min(max(bruto - CPP_YMPE, 0.0), CPP_YAMPE - CPP_YMPE)
    )
    ei = EI_TIPO_EMPRESA * min(bruto, EI_TOPE)
    wsib_coste = wsib * min(bruto, WSIB_TECHO)
    fijos = sum(GASTOS_FIJOS.values())
    total = bruto + cpp + ei + wsib_coste + fijos
    return {
        "salario_anual": salario,
        "vacation_pay": vacation_pay,
        "cpp": cpp,
        "ei": ei,
        "wsib": wsib_coste,
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
        c = coste_empresa(salario, WSIB[clase])
        filas.append({
            "codigo": codigo,
            "oficio": oficio,
            "escala": escala,
            "wsib_clase": clase,
            "salario_hora_cad": round(salario, 4),
            "salario_anual": round(c["salario_anual"], 2),
            "vacation_pay": round(c["vacation_pay"], 2),
            "cpp": round(c["cpp"], 2),
            "ei": round(c["ei"], 2),
            "wsib": round(c["wsib"], 2),
            "gastos_fijos": round(c["gastos_fijos"], 2),
            "total_anual": round(c["total_anual"], 2),
            "recargo_pct": round(c["recargo_pct"], 1),
            "horas_facturables": round(HORAS_FACTURABLES, 1),
            "coste_hora_cad": round(c["coste_hora_facturable"], 2),
        })

    if args.csv:
        w = csv.DictWriter(sys.stdout, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)
        return 0

    print(f"Modelo de coste empresa — Canadá {FECHA} (perfil Ontario)")
    print(f"Job Bank ON (19/11/2025) × 1,05 · {HORAS_SEMANA:g} h/semana, "
          f"{HORAS_PAGADAS:,.0f} h pagadas (trabajo + festivos) + vacation "
          f"pay {VACATION_PAY:.0%}")
    print(f"Vacaciones {DIAS_VACACIONES:g} días + {DIAS_FESTIVOS:g} festivos + "
          f"{DIAS_BAJA:g} de baja (no pagados) → {DIAS_TRABAJADOS:,.0f} días "
          f"trabajados = {HORAS_FACTURABLES:,.0f} h facturables/año")
    print(f"CPP {CPP_TIPO:.2%} (tope YMPE {CPP_YMPE:,.0f} $) + CPP2 "
          f"{CPP2_TIPO:.0%} · EI empresa {EI_TIPO_EMPRESA:.3%} "
          f"(tope {EI_TOPE:,.0f} $) · WSIB por clase G1-G5")
    print()
    print(f"{'recurso':<16}{'oficio':<40}{'$ /h':>8}{'total/año':>11}"
          f"{'recargo':>9}{'$ /h fact.':>11}")
    print("─" * 95)
    for f in filas:
        print(f"{f['codigo']:<16}{f['oficio']:<40}"
              f"{f['salario_hora_cad']:>8.2f}{f['total_anual']:>11,.0f}"
              f"{f['recargo_pct']:>8.1f}%{f['coste_hora_cad']:>11.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
