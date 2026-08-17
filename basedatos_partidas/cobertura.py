#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Informe de cobertura del catálogo (capítulo › subcapítulo › apartado).

    python3 basedatos_partidas/cobertura.py            # resumen
    python3 basedatos_partidas/cobertura.py 09         # detalle de un capítulo
    python3 basedatos_partidas/cobertura.py --pendientes
"""
from __future__ import annotations
import collections
import json
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
CLASIFICACION = BASE / "datos" / "clasificacion.json"
DESCOMPUESTOS = BASE / "datos" / "descompuestos"
LLENO, VACIO = "█", "░"


def cargar():
    taxo = json.loads(CLASIFICACION.read_text(encoding="utf-8"))
    partidas = [
        json.loads(f.read_text(encoding="utf-8"))
        for f in sorted(DESCOMPUESTOS.glob("*.json"))
    ]
    return taxo, partidas


def barra(h, t, ancho=18):
    if not t:
        return VACIO * ancho
    n = round(h / t * ancho)
    return LLENO * n + VACIO * (ancho - n)


def _rutas(taxo):
    for cc, cap in taxo["capitulos"].items():
        for ss, sub in cap["subcapitulos"].items():
            for aa, nombre in sub.get("apartados", {}).items():
                yield cc, ss, aa, cap, sub, nombre


def resumen(taxo, partidas):
    m = collections.Counter(
        (p["capitulo"], p["subcapitulo"], p["apartado"]) for p in partidas
    )
    caps = taxo["capitulos"]
    print(
        f"COBERTURA — {len(partidas)} partidas · ámbito «{taxo.get('_ambito')}» "
        f"· formato {taxo.get('_formato_codigo', 'CC.SS.AA.NNN')}\n"
    )
    print(f"  {'':<4}{'CAPÍTULO':<42}{'APART.':>9}  {'AVANCE':<20}{'PART.':>6}")
    print("  " + "─" * 83)
    total_apartados = total_con = 0
    for cc, cap in caps.items():
        rutas = [r for r in _rutas(taxo) if r[0] == cc]
        con = [r for r in rutas if m[(r[0], r[1], r[2])]]
        n = sum(m[(r[0], r[1], r[2])] for r in rutas)
        total_apartados += len(rutas)
        total_con += len(con)
        print(
            f"  {' ' if con else '·'}{cc:<3}{cap['nombre'][:40]:<42}"
            f"{len(con):>4}/{len(rutas):<4}  {barra(len(con), len(rutas)):<20}{n:>6}"
        )
    print("  " + "─" * 83)
    print(
        f"  {'':<4}{'TOTAL':<42}{total_con:>4}/{total_apartados:<4}  "
        f"{barra(total_con, total_apartados):<20}{len(partidas):>6}"
    )
    print("\n  Detalle:  python3 basedatos_partidas/cobertura.py 09")


def detalle(taxo, partidas, cod_cap):
    cap = taxo["capitulos"].get(cod_cap)
    if not cap:
        sys.exit(f"El capítulo «{cod_cap}» no existe.")
    print(f"{cod_cap} · {cap['nombre'].upper()}\n")
    for ss, sub in cap["subcapitulos"].items():
        lista_sub = [
            p for p in partidas
            if p["capitulo"] == cod_cap and p["subcapitulo"] == ss
        ]
        print(f"  {cod_cap}.{ss}  {sub['nombre']}  ({len(lista_sub)})")
        for aa, nombre_apartado in sub.get("apartados", {}).items():
            lista = sorted(
                [p for p in lista_sub if p["apartado"] == aa],
                key=lambda p: p["codigo"],
            )
            print(
                f"    {cod_cap}.{ss}.{aa}  {nombre_apartado}  ({len(lista)})"
                + ("" if lista else "   ← sin partidas")
            )
            for p in lista:
                pc = " ⊕" if p.get("producto_cliente") else ""
                print(f"      {p['codigo']:<16} {p['unidad']:<4} {p['titulo'][:60]}{pc}")
        if not sub.get("apartados"):
            print("    — sin apartados definidos")
        print()


def pendientes(taxo, partidas):
    m = collections.Counter(
        (p["capitulo"], p["subcapitulo"], p["apartado"]) for p in partidas
    )
    print("SUBCAPÍTULOS O APARTADOS SIN NINGUNA PARTIDA\n")
    for cc, cap in taxo["capitulos"].items():
        filas = []
        for ss, sub in cap["subcapitulos"].items():
            apartados = sub.get("apartados", {})
            if not apartados:
                filas.append(f"     {cc}.{ss}  {sub['nombre']} (sin apartados)")
                continue
            for aa, nombre in apartados.items():
                if not m[(cc, ss, aa)]:
                    filas.append(f"     {cc}.{ss}.{aa}  {nombre}")
        if filas:
            print(f"  {cc} · {cap['nombre']}")
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
