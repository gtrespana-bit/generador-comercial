#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Aplica una ronda de contraste de precios al cuadro de recursos.

A diferencia de `precios.py aplicar`, que marca los precios como
«confirmado» (dato que da el cliente), este script marca los precios como
«verificado-mercado» y deja escrito el campo `fuente` con la evidencia:
rango observado, conversión de presentación a unidad del cuadro y tiendas
consultadas.

El fichero de evidencia es `datos/contraste_mercado_AAAA-MM.json`. Se
conserva en el repositorio para que cualquiera pueda auditar de dónde sale
cada número y rehacer el contraste dentro de seis meses.

    python3 basedatos_partidas/contraste.py listar   # qué cambiaría
    python3 basedatos_partidas/contraste.py aplicar  # lo escribe

Después:
    python3 basedatos_partidas/descompuestos.py && python3 basedatos_partidas/construir.py
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
RAIZ = BASE.parent
RECURSOS = BASE / "datos" / "recursos.json"
GRUPOS = ("materiales", "maquinaria", "mano_obra")


def fichero_contraste() -> Path:
    candidatos = sorted((BASE / "datos").glob("contraste_mercado_*.json"))
    if not candidatos:
        sys.exit("No hay ningún fichero datos/contraste_mercado_*.json")
    return candidatos[-1]


def localizar(bruto: dict, codigo: str) -> tuple[str, dict] | tuple[None, None]:
    for grupo in GRUPOS:
        ficha = (bruto.get(grupo) or {}).get(codigo)
        if ficha:
            return grupo, ficha
    return None, None


def recorrer(bruto: dict, contraste: dict):
    for codigo, dato in contraste["precios"].items():
        grupo, ficha = localizar(bruto, codigo)
        if ficha is None:
            yield codigo, None, None, None, None, "no existe en el cuadro de recursos"
            continue
        if grupo == "maquinaria":
            yield codigo, grupo, ficha, None, None, "es maquinaria: fuera de alcance por decisión del cliente"
            continue
        antes = float(ficha["precio"])
        ahora = float(dato["precio"])
        var = ((ahora - antes) / antes * 100) if antes else 0.0
        yield codigo, grupo, ficha, antes, ahora, f"{var:+.1f}%"


def informe(bruto: dict, contraste: dict) -> list:
    filas = []
    print(f"Contraste: {contraste.get('_fecha')} · moneda {contraste.get('_moneda')}")
    print(f"{'CÓDIGO':<20}{'ANTES':>10}{'AHORA':>10}  OBSERVACIÓN")
    for codigo, grupo, ficha, antes, ahora, nota in recorrer(bruto, contraste):
        if antes is None:
            print(f"{codigo:<20}{'—':>10}{'—':>10}  {nota}")
            continue
        print(f"{codigo:<20}{antes:>10.4f}{ahora:>10.4f}  {nota}")
        filas.append((codigo, grupo, ficha, antes, ahora))
    return filas


def aplicar() -> int:
    bruto = json.loads(RECURSOS.read_text(encoding="utf-8"))
    ruta = fichero_contraste()
    contraste = json.loads(ruta.read_text(encoding="utf-8"))
    print(f"Fichero de evidencia: {ruta.relative_to(RAIZ)}\n")

    filas = informe(bruto, contraste)
    if not filas:
        print("\nNada que aplicar.")
        return 0

    copia = RECURSOS.with_suffix(f".{datetime.now():%Y%m%d-%H%M%S}.bak.json")
    shutil.copy2(RECURSOS, copia)

    subidas = bajadas = iguales = 0
    for codigo, _grupo, ficha, antes, ahora in filas:
        dato = contraste["precios"][codigo]
        ficha["precio"] = round(ahora, 4)
        ficha["estado"] = "verificado-mercado"
        partes = [dato["fuente"]]
        if dato.get("conversion"):
            partes.append(f"Conversión: {dato['conversion']}.")
        if dato.get("rango_observado"):
            partes.append(f"Rango observado: {dato['rango_observado']}.")
        ficha["fuente"] = " ".join(partes)
        if dato.get("comentario"):
            ficha["nota"] = dato["comentario"]
        if ahora > antes:
            subidas += 1
        elif ahora < antes:
            bajadas += 1
        else:
            iguales += 1

    bruto["_revision"] = (
        f"{datetime.now():%Y-%m} · segunda ronda de contraste de material "
        f"(MercadoLibre VE y EPA Venezuela). Alquiler de equipos sin tocar."
    )
    RECURSOS.write_text(json.dumps(bruto, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nCopia de seguridad -> {copia.name}")
    print(f"{len(filas)} recursos actualizados: {subidas} al alza, {bajadas} a la baja, {iguales} confirmados.")
    print("\nRegenera con:")
    print("  python3 basedatos_partidas/descompuestos.py && python3 basedatos_partidas/construir.py")
    return 0


def listar() -> int:
    bruto = json.loads(RECURSOS.read_text(encoding="utf-8"))
    contraste = json.loads(fichero_contraste().read_text(encoding="utf-8"))
    informe(bruto, contraste)
    return 0


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "listar"
    if modo not in ("listar", "aplicar"):
        sys.exit("Uso: contraste.py [listar|aplicar]")
    raise SystemExit(listar() if modo == "listar" else aplicar())
