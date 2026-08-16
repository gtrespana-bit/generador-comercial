#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Informe de reparto: cuánto del precio de venta llega al trabajador.

El coste de la mano de obra de este catálogo es una decisión deliberada:
se paga por encima de la tarifa habitual del mercado venezolano. Este
informe cuantifica esa decisión, permite simular escenarios de tarifa y
produce el dato que puede acompañar a una propuesta comercial.

    python3 basedatos_partidas/equidad.py                # informe
    python3 basedatos_partidas/equidad.py --escenario 4.5 3.2 2.8
        (oficial, ayudante especializado, ayudante)
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
RAIZ = BASE.parent

# Tarifa horaria habitual del mercado venezolano, según los tabuladores
# publicados de 2026: oficial 15 USD/día y ayudante 9 USD/día sobre 8 horas.
MERCADO_OFICIAL, MERCADO_AYU_ESP, MERCADO_AYU = 1.88, 1.35, 1.13


def cargar():
    rec = json.loads((BASE / "datos" / "recursos.json").read_text(encoding="utf-8"))
    cla = json.loads((BASE / "datos" / "clasificacion.json").read_text(encoding="utf-8"))
    plano = {c: {**f, "grupo": g}
             for g in ("materiales", "maquinaria", "mano_obra")
             for c, f in rec[g].items()}
    partidas = [json.loads(f.read_text(encoding="utf-8"))
                for f in sorted((BASE / "datos" / "descompuestos").glob("*.json"))]
    return rec, cla, plano, partidas


def tarifa_mercado(codigo: str, propia: float) -> float:
    if codigo.startswith("MO-OF1"):
        return MERCADO_OFICIAL
    if codigo == "MO-AYU-ESP":
        return MERCADO_AYU_ESP
    if codigo == "MO-AYU":
        return MERCADO_AYU
    return propia


def calcular(plano, partidas, escenario=None):
    """Devuelve totales y desglose por capítulo.

    `escenario` sustituye las tarifas propias por (oficial, ayu_esp, ayudante).
    """
    def precio_mo(codigo, base):
        if not escenario:
            return base
        of, ae, ay = escenario
        if codigo.startswith("MO-OF1"):
            return of
        if codigo == "MO-AYU-ESP":
            return ae
        if codigo == "MO-AYU":
            return ay
        return base

    tot = {"coste": 0.0, "mo": 0.0, "coste_mercado": 0.0, "mo_mercado": 0.0, "horas": 0.0}
    cap = collections.defaultdict(lambda: {"coste": 0.0, "mo": 0.0, "horas": 0.0})
    for p in partidas:
        cd = cdm = mo = mom = horas = 0.0
        for l in p["recursos"]:
            ficha = plano[l["ref"]]
            rend, base = float(l["rendimiento"]), float(ficha["precio"])
            if ficha["grupo"] == "mano_obra":
                propio = precio_mo(l["ref"], base)
                mercado = tarifa_mercado(l["ref"], base)
                cd += rend * propio;  mo += rend * propio;  horas += rend
                cdm += rend * mercado; mom += rend * mercado
            else:
                cd += rend * base; cdm += rend * base
        factor = 1 + float(p.get("complementarios_pct", 1)) / 100
        cd *= factor; cdm *= factor
        tot["coste"] += cd; tot["mo"] += mo
        tot["coste_mercado"] += cdm; tot["mo_mercado"] += mom; tot["horas"] += horas
        c = cap[p["capitulo"]]
        c["coste"] += cd; c["mo"] += mo; c["horas"] += horas
    return tot, cap


def informe(escenario=None):
    rec, cla, plano, partidas = cargar()
    tot, cap = calcular(plano, partidas, escenario)
    margen = 1.30
    venta = tot["coste"] * margen
    venta_m = tot["coste_mercado"] * margen

    tarifas = escenario or (
        rec["mano_obra"]["MO-OF1"]["precio"],
        rec["mano_obra"]["MO-AYU-ESP"]["precio"],
        rec["mano_obra"]["MO-AYU"]["precio"],
    )
    etiqueta = "ESCENARIO SIMULADO" if escenario else "TARIFAS ACTUALES"

    print(f"REPARTO DEL PRECIO — {etiqueta}\n")
    print(f"  Oficial de 1ª ............ {tarifas[0]:>6.2f} USD/h   ({tarifas[0]*8:>6.2f} USD/jornada)")
    print(f"  Ayudante especializado ... {tarifas[1]:>6.2f} USD/h   ({tarifas[1]*8:>6.2f} USD/jornada)")
    print(f"  Ayudante ................. {tarifas[2]:>6.2f} USD/h   ({tarifas[2]*8:>6.2f} USD/jornada)")
    print(f"\n  Referencia de mercado venezolano 2026: oficial {MERCADO_OFICIAL*8:.2f} y ayudante {MERCADO_AYU*8:.2f} USD/jornada.")

    print(f"\n  {'':<44}{'PROPIO':>13}{'MERCADO':>13}")
    print("  " + "─" * 70)
    print(f"  {'Coste directo del catálogo':<44}{tot['coste']:>13,.2f}{tot['coste_mercado']:>13,.2f}")
    print(f"  {'De ello, mano de obra':<44}{tot['mo']:>13,.2f}{tot['mo_mercado']:>13,.2f}")
    print(f"  {'Precio de venta (margen 30 %)':<44}{venta:>13,.2f}{venta_m:>13,.2f}")
    print("  " + "─" * 70)
    print(f"  {'LLEGA AL TRABAJADOR':<44}{tot['mo']/venta*100:>12.1f} %{tot['mo_mercado']/venta_m*100:>12.1f} %")

    dif = (tot["coste"] / tot["coste_mercado"] - 1) * 100
    veces = tot["mo"] / tot["mo_mercado"] if tot["mo_mercado"] else 0
    print(f"\n  Se paga {veces:.1f} veces la tarifa de mercado y el precio final sube un {dif:.0f} %.")
    print(f"  Horas de trabajo catalogadas: {tot['horas']:,.1f} h")

    print(f"\n\n  PESO DE LA MANO DE OBRA POR CAPÍTULO\n")
    print(f"  {'CAP':<5}{'CAPÍTULO':<42}{'% M.O.':>9}{'HORAS':>10}")
    print("  " + "─" * 68)
    for c, v in sorted(cap.items(), key=lambda x: -(x[1]["mo"] / x[1]["coste"] if x[1]["coste"] else 0)):
        nombre = cla["capitulos"][c]["nombre"]
        print(f"  {c:<5}{nombre[:40]:<42}{v['mo']/v['coste']*100:>8.1f} %{v['horas']:>10.1f}")

    print("\n  Cuanto mayor es el porcentaje, más pesa en esa partida la decisión de tarifa:")
    print("  en demoliciones y pintura la mano de obra manda; en fundaciones manda el material.")


if __name__ == "__main__":
    esc = None
    if len(sys.argv) > 1 and sys.argv[1] == "--escenario":
        try:
            esc = tuple(float(x) for x in sys.argv[2:5])
            assert len(esc) == 3
        except Exception:
            sys.exit("Uso: equidad.py --escenario <oficial> <ayu_especializado> <ayudante>")
    informe(esc)
