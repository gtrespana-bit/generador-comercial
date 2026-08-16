#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Informe de cobertura del catálogo.

Recorre la taxonomía completa y marca qué grupos están poblados y cuáles
siguen vacíos, para poder avanzar capítulo por capítulo sin dejar huecos.

    python3 basedatos_partidas/cobertura.py           # resumen por capítulo
    python3 basedatos_partidas/cobertura.py D         # detalle de un capítulo
    python3 basedatos_partidas/cobertura.py --pendientes
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
CLASIFICACION = BASE / "datos" / "clasificacion.json"
DESCOMPUESTOS = BASE / "datos" / "descompuestos"

LLENO, VACIO = "█", "░"


def cargar():
    taxo = json.loads(CLASIFICACION.read_text(encoding="utf-8"))
    partidas = []
    for f in sorted(DESCOMPUESTOS.glob("*.json")):
        partidas.append(json.loads(f.read_text(encoding="utf-8")))
    return taxo, partidas


def por_grupo(partidas):
    m = {}
    for p in partidas:
        m.setdefault(p["grupo"], []).append(p)
    return m


def barra(hechos: int, total: int, ancho: int = 18) -> str:
    if not total:
        return VACIO * ancho
    n = round(hechos / total * ancho)
    return LLENO * n + VACIO * (ancho - n)


def resumen(taxo, partidas):
    mapa = por_grupo(partidas)
    caps = taxo["capitulos"]
    print(f"COBERTURA DEL CATÁLOGO — {len(partidas)} partidas\n")
    print(f"  {'':<3}{'CAPÍTULO':<46}{'GRUPOS':>9}  {'AVANCE':<20}{'PART.':>6}")
    print("  " + "─" * 86)
    tg = th = 0
    for cod, cap in caps.items():
        grupos = [(g, s) for s in cap["subcapitulos"].values() for g in s.get("grupos", {})]
        con = [g for g, _ in grupos if mapa.get(g)]
        n = sum(len(mapa.get(g, [])) for g, _ in grupos)
        tg += len(grupos); th += len(con)
        marca = " " if con else "·"
        print(f"  {marca}{cod:<2}{cap['nombre'][:44]:<46}"
              f"{len(con):>4}/{len(grupos):<4}  {barra(len(con), len(grupos)):<20}{n:>6}")
    print("  " + "─" * 86)
    print(f"  {'':<3}{'TOTAL':<46}{th:>4}/{tg:<4}  {barra(th, tg):<20}{len(partidas):>6}")
    print(f"\n  Grupos declarados sin partidas: {tg - th}")
    print("  Detalle de un capítulo:  python3 basedatos_partidas/cobertura.py D")


def detalle(taxo, partidas, cod_cap):
    mapa = por_grupo(partidas)
    cap = taxo["capitulos"].get(cod_cap)
    if not cap:
        sys.exit(f"El capítulo «{cod_cap}» no existe.")
    print(f"{cod_cap} · {cap['nombre'].upper()}\n")
    for cod_sub, sub in cap["subcapitulos"].items():
        grupos = sub.get("grupos", {})
        n = sum(len(mapa.get(g, [])) for g in grupos)
        estado = "" if n else "   ← sin partidas"
        print(f"  {cod_sub}  {sub['nombre']}  ({n}){estado}")
        if not grupos:
            print(f"       (sin grupos declarados todavía)")
        for cod_gru, nombre in grupos.items():
            lista = sorted(mapa.get(cod_gru, []), key=lambda p: p["codigo"])
            print(f"     {cod_gru}  {nombre}  ({len(lista)})")
            for p in lista:
                pc = " ⊕" if p.get("producto_cliente") else ""
                print(f"        {p['codigo']:<8} {p['unidad']:<3} {p['titulo'][:62]}{pc}")
        print()


def pendientes(taxo, partidas):
    mapa = por_grupo(partidas)
    print("GRUPOS DECLARADOS SIN NINGUNA PARTIDA\n")
    for cod_cap, cap in taxo["capitulos"].items():
        filas = []
        for cod_sub, sub in cap["subcapitulos"].items():
            for cod_gru, nombre in sub.get("grupos", {}).items():
                if not mapa.get(cod_gru):
                    filas.append(f"     {cod_gru:<5} {nombre}")
            if not sub.get("grupos"):
                filas.append(f"     {cod_sub:<5} {sub['nombre']}  (sin grupos declarados)")
        if filas:
            print(f"  {cod_cap} · {cap['nombre']}")
            print("\n".join(filas))
            print()


if __name__ == "__main__":
    taxo, partidas = cargar()
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    if arg == "--pendientes":
        pendientes(taxo, partidas)
    elif arg:
        detalle(taxo, partidas, arg.upper())
    else:
        resumen(taxo, partidas)
