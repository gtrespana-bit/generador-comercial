#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Informe de cobertura del catálogo (capítulo › subcapítulo).

    python3 basedatos_partidas/cobertura.py            # resumen
    python3 basedatos_partidas/cobertura.py 02         # detalle de un capítulo
    python3 basedatos_partidas/cobertura.py --pendientes
"""
from __future__ import annotations
import json, sys, collections
from pathlib import Path

BASE = Path(__file__).resolve().parent
CLASIFICACION = BASE / "datos" / "clasificacion.json"
DESCOMPUESTOS = BASE / "datos" / "descompuestos"
LLENO, VACIO = "█", "░"


def cargar():
    taxo = json.loads(CLASIFICACION.read_text(encoding="utf-8"))
    partidas = [json.loads(f.read_text(encoding="utf-8")) for f in sorted(DESCOMPUESTOS.glob("*.json"))]
    return taxo, partidas


def barra(h, t, ancho=18):
    if not t:
        return VACIO * ancho
    n = round(h / t * ancho)
    return LLENO * n + VACIO * (ancho - n)


def resumen(taxo, partidas):
    m = collections.Counter((p["capitulo"], p["subcapitulo"]) for p in partidas)
    caps = taxo["capitulos"]
    print(f"COBERTURA — {len(partidas)} partidas · ámbito «{taxo.get('_ambito')}» · prefijo {taxo.get('_prefijo')}-\n")
    print(f"  {'':<4}{'CAPÍTULO':<44}{'SUBCAP.':>9}  {'AVANCE':<20}{'PART.':>6}")
    print("  " + "─" * 85)
    ts = th = 0
    for cod, cap in caps.items():
        subs = list(cap["subcapitulos"])
        con = [s for s in subs if m[(cod, s)]]
        n = sum(m[(cod, s)] for s in subs)
        ts += len(subs); th += len(con)
        print(f"  {' ' if con else '·'}{cod:<3}{cap['nombre'][:42]:<44}"
              f"{len(con):>4}/{len(subs):<4}  {barra(len(con), len(subs)):<20}{n:>6}")
    print("  " + "─" * 85)
    print(f"  {'':<4}{'TOTAL':<44}{th:>4}/{ts:<4}  {barra(th, ts):<20}{len(partidas):>6}")
    print("\n  Detalle:  python3 basedatos_partidas/cobertura.py 02")


def detalle(taxo, partidas, cod_cap):
    cap = taxo["capitulos"].get(cod_cap)
    if not cap:
        sys.exit(f"El capítulo «{cod_cap}» no existe.")
    print(f"{cod_cap} · {cap['nombre'].upper()}\n")
    for cod_sub, nombre in cap["subcapitulos"].items():
        lista = sorted([p for p in partidas if p["capitulo"] == cod_cap and p["subcapitulo"] == cod_sub],
                       key=lambda p: p["codigo"])
        print(f"  {cod_sub}  {nombre}  ({len(lista)})" + ("" if lista else "   ← sin partidas"))
        for p in lista:
            pc = " ⊕" if p.get("producto_cliente") else ""
            print(f"       {p['codigo']:<15} {p['unidad']:<3} {p['titulo'][:60]}{pc}")
        print()


def pendientes(taxo, partidas):
    m = collections.Counter((p["capitulo"], p["subcapitulo"]) for p in partidas)
    print("SUBCAPÍTULOS SIN NINGUNA PARTIDA\n")
    for cod, cap in taxo["capitulos"].items():
        filas = [f"     {s}  {n}" for s, n in cap["subcapitulos"].items() if not m[(cod, s)]]
        if filas:
            print(f"  {cod} · {cap['nombre']}")
            print("\n".join(filas))
            print()


if __name__ == "__main__":
    taxo, partidas = cargar()
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    if arg == "--pendientes":
        pendientes(taxo, partidas)
    elif arg:
        detalle(taxo, partidas, arg)
    else:
        resumen(taxo, partidas)
