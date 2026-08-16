#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cambiar el precio de un artículo y ver a dónde llega el golpe.

Pensado para un mercado en el que el cemento amanece en 10 y anochece en 20.
Todo el catálogo cuelga de `datos/recursos.json`: se toca un precio ahí y las
540 partidas se recalculan solas. Este programa es el atajo para hacerlo sin
abrir el JSON a mano y, sobre todo, para **ver el impacto antes de aplicarlo**.

    # ¿cómo se llama el recurso del cemento?
    python3 basedatos_partidas/precio.py buscar cemento

    # ¿qué precio tiene y qué partidas dependen de él?
    python3 basedatos_partidas/precio.py ver MT-CEMENTO

    # el saco de 42,5 kg amaneció en 20 USD: simulación
    python3 basedatos_partidas/precio.py fijar MT-CEMENTO 20 --por-saco 42.5

    # convencido: se escribe y se regenera todo
    python3 basedatos_partidas/precio.py fijar MT-CEMENTO 20 --por-saco 42.5 --aplicar

Otras presentaciones: --por-saco KG, --por-galon (3,785 l), --por-rollo M,
--por-lamina M2, --por-unidad N. Sin ninguna de ellas el valor se toma tal
cual, en la unidad del recurso.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
RAIZ = BASE.parent
RECURSOS = BASE / "datos" / "recursos.json"
DESCOMPUESTOS = BASE / "datos" / "descompuestos"
GRUPOS = ("materiales", "maquinaria", "mano_obra")
GALON_EN_LITROS = 3.785


# --------------------------------------------------------------------------- #
# Lectura del cuadro
# --------------------------------------------------------------------------- #

def cargar() -> dict:
    return json.loads(RECURSOS.read_text(encoding="utf-8"))


def plano(bruto: dict) -> dict[str, dict]:
    salida = {}
    for grupo in GRUPOS:
        for codigo, ficha in (bruto.get(grupo) or {}).items():
            salida[codigo] = {**ficha, "_grupo": grupo, "_codigo": codigo}
    return salida


def sin_tildes(texto: str) -> str:
    t = unicodedata.normalize("NFD", str(texto or "").lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def precio_efectivo(codigo: str, fichas: dict[str, dict]) -> float:
    """Precio real, resolviendo los recursos compuestos."""
    ficha = fichas[codigo]
    comp = ficha.get("composicion")
    if not comp:
        return float(ficha["precio"])
    return round(sum(float(c["cantidad"]) * precio_efectivo(c["ref"], fichas) for c in comp), 4)


def dependientes(codigo: str, fichas: dict[str, dict]) -> list[str]:
    """Recursos compuestos que llevan este recurso dentro, en cascada."""
    encontrados: list[str] = []
    frontera = {codigo}
    while frontera:
        nueva = set()
        for cod, ficha in fichas.items():
            if cod in encontrados or cod in frontera:
                continue
            refs = {c["ref"] for c in (ficha.get("composicion") or [])}
            if refs & frontera:
                nueva.add(cod)
        encontrados.extend(sorted(nueva))
        frontera = nueva
    return encontrados


def partidas_afectadas(codigos: set[str]) -> list[tuple[str, str, float]]:
    """(código, título, coste directo) de las partidas que usan esos recursos."""
    salida = []
    for ruta in sorted(DESCOMPUESTOS.glob("*.json")):
        partida = json.loads(ruta.read_text(encoding="utf-8"))
        refs = {linea.get("ref") for linea in partida.get("recursos", [])}
        if refs & codigos:
            salida.append((partida["codigo"], partida.get("titulo", ""), 0.0))
    return salida


# --------------------------------------------------------------------------- #
# Cálculo de coste de una partida (mismo criterio que descompuestos.py)
# --------------------------------------------------------------------------- #

def coste_partida(partida: dict, fichas: dict[str, dict]) -> float:
    directo = 0.0
    for linea in partida.get("recursos", []):
        ref = linea.get("ref")
        rend = float(linea["rendimiento"])
        if ref:
            directo += rend * precio_efectivo(ref, fichas)
        else:
            directo += rend * float(linea.get("precio", 0.0))
    pct = float(partida.get("complementarios_pct", 1))
    return round(directo * (1 + pct / 100.0), 2)


# --------------------------------------------------------------------------- #
# Órdenes
# --------------------------------------------------------------------------- #

def orden_buscar(texto: str) -> int:
    fichas = plano(cargar())
    aguja = sin_tildes(texto)
    hits = [
        (cod, f) for cod, f in fichas.items()
        if aguja in sin_tildes(cod) or aguja in sin_tildes(f["descripcion"])
    ]
    if not hits:
        print(f"Ningún recurso coincide con «{texto}».")
        return 1
    print(f"{len(hits)} recurso(s) coinciden con «{texto}»:\n")
    print(f"  {'CÓDIGO':<20}{'UD':<6}{'PRECIO':>10}  DESCRIPCIÓN")
    for cod, f in sorted(hits):
        marca = " (compuesto)" if f.get("composicion") else ""
        print(f"  {cod:<20}{f['unidad']:<6}{precio_efectivo(cod, fichas):>10.4f}  {f['descripcion'][:58]}{marca}")
    return 0


def orden_ver(codigo: str) -> int:
    fichas = plano(cargar())
    if codigo not in fichas:
        print(f"No existe el recurso «{codigo}». Prueba: precio.py buscar {codigo}")
        return 1
    f = fichas[codigo]
    deps = dependientes(codigo, fichas)
    alcance = {codigo, *deps}
    partidas = partidas_afectadas(alcance)

    print(f"{codigo} — {f['descripcion']}")
    print(f"  unidad          : {f['unidad']}")
    print(f"  precio          : {precio_efectivo(codigo, fichas):.4f} USD/{f['unidad']}")
    print(f"  estado          : {f.get('estado', '—')}")
    if f.get("fuente"):
        print(f"  fuente          : {f['fuente'][:120]}")
    if f.get("composicion"):
        print("  se calcula con  :")
        for c in f["composicion"]:
            sub = fichas[c["ref"]]
            print(f"      {c['cantidad']:>10.4f} {sub['unidad']:<4} × {precio_efectivo(c['ref'], fichas):>8.4f}  {c['ref']}")
    if deps:
        print(f"  entra dentro de : {', '.join(deps)}")
    print(f"\n  Partidas que se recalculan si cambia: {len(partidas)}")
    for cod, titulo, _ in partidas[:12]:
        print(f"      {cod}  {titulo[:66]}")
    if len(partidas) > 12:
        print(f"      … y {len(partidas) - 12} más")
    return 0


def orden_fijar(codigo: str, valor: float, args) -> int:
    bruto = cargar()
    fichas = plano(bruto)
    if codigo not in fichas:
        print(f"No existe el recurso «{codigo}». Prueba: precio.py buscar {codigo}")
        return 1
    ficha = fichas[codigo]
    if ficha.get("composicion"):
        print(f"«{codigo}» es un recurso compuesto: su precio sale de sus componentes.")
        print("Cambia el precio de alguno de ellos:")
        for c in ficha["composicion"]:
            print(f"   {c['ref']}")
        return 1

    # Presentación comercial -> unidad del cuadro
    divisor, etiqueta = 1.0, f"por {ficha['unidad']}"
    if args.por_saco:
        divisor, etiqueta = args.por_saco, f"por saco de {args.por_saco:g} kg"
    elif args.por_galon:
        divisor, etiqueta = GALON_EN_LITROS, "por galón (3,785 l)"
    elif args.por_rollo:
        divisor, etiqueta = args.por_rollo, f"por rollo de {args.por_rollo:g} m"
    elif args.por_lamina:
        divisor, etiqueta = args.por_lamina, f"por lámina de {args.por_lamina:g} m²"
    elif args.por_unidad:
        divisor, etiqueta = args.por_unidad, f"por paquete de {args.por_unidad:g} ud"
    nuevo = round(valor / divisor, 6)
    anterior = float(ficha["precio"])

    print(f"{codigo} — {ficha['descripcion'][:70]}")
    print(f"  precio indicado : {valor:.4f} USD {etiqueta}")
    print(f"  en unidad {ficha['unidad']:<5} : {anterior:.4f} -> {nuevo:.4f} USD"
          f"   ({(nuevo - anterior) / anterior * 100:+.1f} %)" if anterior else "")

    # Simulación sobre las partidas
    fichas_nuevas = {c: dict(f) for c, f in fichas.items()}
    fichas_nuevas[codigo]["precio"] = nuevo
    alcance = {codigo, *dependientes(codigo, fichas)}
    filas = []
    for ruta in sorted(DESCOMPUESTOS.glob("*.json")):
        partida = json.loads(ruta.read_text(encoding="utf-8"))
        refs = {l.get("ref") for l in partida.get("recursos", [])}
        if not (refs & alcance):
            continue
        antes = coste_partida(partida, fichas)
        ahora = coste_partida(partida, fichas_nuevas)
        if abs(ahora - antes) >= 0.005:
            filas.append((partida["codigo"], partida.get("titulo", ""), antes, ahora))
    filas.sort(key=lambda r: -(abs(r[3] - r[2]) / r[2] if r[2] else 0))

    print(f"\n  {len(filas)} partidas cambian de precio.")
    if filas:
        print(f"\n  {'PARTIDA':<16}{'ANTES':>9}{'AHORA':>9}{'VAR.':>8}  TÍTULO")
        for cod, titulo, antes, ahora in filas[:15]:
            var = (ahora - antes) / antes * 100 if antes else 0
            print(f"  {cod:<16}{antes:>9.2f}{ahora:>9.2f}{var:>7.1f}%  {titulo[:44]}")
        if len(filas) > 15:
            print(f"  … y {len(filas) - 15} más")
        total_antes = sum(f[2] for f in filas)
        total_ahora = sum(f[3] for f in filas)
        print(f"\n  Suma de esas partidas: {total_antes:,.2f} -> {total_ahora:,.2f} USD "
              f"({(total_ahora - total_antes) / total_antes * 100:+.1f} %)")

    if not args.aplicar:
        print("\n  [SIMULACIÓN] No se ha escrito nada. Añade --aplicar para confirmar.")
        return 0

    copia = RECURSOS.with_suffix(f".{datetime.now():%Y%m%d-%H%M%S}.bak.json")
    shutil.copy2(RECURSOS, copia)
    destino = bruto[ficha["_grupo"]][codigo]
    destino["precio"] = nuevo
    if args.nota:
        destino["nota"] = args.nota
    destino["fecha_precio"] = f"{datetime.now():%Y-%m-%d}"
    bruto["_revision"] = f"{datetime.now():%Y-%m-%d} · {codigo} a {nuevo:.4f} USD/{ficha['unidad']}"
    RECURSOS.write_text(json.dumps(bruto, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  Escrito. Copia de seguridad: {copia.name}")

    if args.sin_regenerar:
        print("  Regenera cuando quieras con:")
        print("    python3 basedatos_partidas/descompuestos.py && python3 basedatos_partidas/construir.py")
        return 0

    print("  Regenerando las 540 partidas…")
    for script in ("descompuestos.py", "construir.py"):
        res = subprocess.run(
            [sys.executable, str(BASE / script)], cwd=RAIZ,
            capture_output=True, text=True,
        )
        if res.returncode != 0:
            print(res.stdout[-2000:]); print(res.stderr[-2000:])
            return res.returncode
    print("  Listo. Catálogo y hojas de descompuesto actualizados.")
    return 0


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        description="Cambia el precio de un recurso y propaga a todas las partidas.",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__,
    )
    sub = p.add_subparsers(dest="orden", required=True)

    b = sub.add_parser("buscar", help="Busca un recurso por código o descripción")
    b.add_argument("texto")

    v = sub.add_parser("ver", help="Muestra el precio y a qué partidas afecta")
    v.add_argument("codigo")

    f = sub.add_parser("fijar", help="Fija un precio nuevo (simula si no se pasa --aplicar)")
    f.add_argument("codigo")
    f.add_argument("valor", type=float)
    f.add_argument("--por-saco", type=float, default=0, metavar="KG")
    f.add_argument("--por-galon", action="store_true")
    f.add_argument("--por-rollo", type=float, default=0, metavar="M")
    f.add_argument("--por-lamina", type=float, default=0, metavar="M2")
    f.add_argument("--por-unidad", type=float, default=0, metavar="N")
    f.add_argument("--nota", default="")
    f.add_argument("--aplicar", action="store_true", help="Escribe el cambio")
    f.add_argument("--sin-regenerar", action="store_true")

    args = p.parse_args(argv)
    if args.orden == "buscar":
        return orden_buscar(args.texto)
    if args.orden == "ver":
        return orden_ver(args.codigo.strip().upper())
    return orden_fijar(args.codigo.strip().upper(), args.valor, args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
