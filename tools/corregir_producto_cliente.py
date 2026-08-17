#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extrae el equipo que elige el cliente de los descompuestos y lo pasa a
``producto_cliente``.

Regla del proyecto: «El producto que elige el cliente NO va dentro de la
partida». Durante la ampliación, muchas partidas «Instalación de [equipo]»
dejaron el equipo (panel solar, inversor, batería, extintor, cámara, bomba,
ascensor…) DENTRO del descompuesto, inflando el precio y, peor, copiando el
mismo conjunto de recursos entre variantes que no son la misma obra.

Este script:
  1. Detecta las partidas nuevas (sin ``codigo_legacy``) que referencian un
     material de EQUIPO (lista ``EQUIPO``) o que son de elevación (09.16).
  2. Saca esos recursos del descompuesto y los describe en ``producto_cliente``.
  3. Para las partidas de ascensor/plataformas elimina además el
     ``MT-CONS-DEM`` (consumibles de demolición) que quedó por copia/pega.

Uso:
    python3 tools/corregir_producto_cliente.py --reporte   # solo informa
    python3 tools/corregir_producto_cliente.py --aplicar   # escribe los JSON
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
ORIGEN = BASE / "basedatos_partidas" / "datos" / "descompuestos"
RECURSOS = BASE / "basedatos_partidas" / "datos" / "recursos.json"

# Materiales que representan EQUIPO / dispositivo que elige el cliente (su
# modelo, potencia, acabado…). No se incluyen materiales de obra ni
# consumibles (madera, melamina en hoja, cable, tubería, herrajes…).
EQUIPO = {
    "MT-PLANTA-ELEC", "MT-PANEL-SOLAR", "MT-INVERSOR", "MT-BATERIA",
    "MT-BOMBA-AGUA", "MT-HIDRONEUMATICO",
    "MT-ALARMA", "MT-CAMARA-CCTV", "MT-DETECT-HUMO", "MT-EXTINTOR", "MT-GABINETE-MANG",
    "MT-PARARRAYOS-PDA", "MT-PARARRAYOS-PUNTA", "MT-CONT-DESCARGAS",
    "MT-DPS-1", "MT-DPS-2", "MT-DPS-3", "MT-DPS-DATOS",
    "MT-DOM-CENTRAL", "MT-DOM-PASARELA", "MT-DOM-PANEL", "MT-DOM-REPETIDOR",
    "MT-DOM-DIMMER", "MT-DOM-ACTUADOR", "MT-DOM-TECLADO", "MT-DOM-TERMOSTATO",
    "MT-DOM-PERSIANA", "MT-DOM-ENCHUFE", "MT-DOM-SENSOR-GAS", "MT-DOM-SENSOR-MOV",
    "MT-DOM-SENSOR-TEMP", "MT-DOM-SENSOR-LUZ", "MT-DOM-SENSOR-INUND", "MT-DOM-SENSOR-PUERTA",
    "MT-AUTOM-PORTON", "MT-BARRA-APOYO",
}

# Consumibles de demolición que quedaron por copia/pega en partidas que NO son
# demolición (p. ej. instalación de ascensor).
RUIDO_DEMOLICION = {"MT-CONS-DEM"}

PREFIJOS = (
    "instalación de ", "instalacion de ",
    "suministro y colocación de ", "suministro y colocacion de ",
    "suministro e instalación de ", "suministro e instalacion de ",
    "suministro y montaje de ",
    "montaje de ",
    "colocación de ", "colocacion de ",
    "recibido de ",
)

ELEVACION = (
    "ascensor", "montacargas", "elevador", "salvaescaleras", "plataforma",
    "rampa mecánica", "rampa mecanica", "silla salvaescaleras",
)
# Adecuación de hueco/foso es obra civil (no se toca).
NO_ELEVACION = ("adecuación", "adecuacion")


def _descripcion_equipo(codigo: str) -> str:
    try:
        datos = json.loads(RECURSOS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        datos = {}
    for grupo in ("materiales", "maquinaria", "mano_obra"):
        ficha = datos.get(grupo, {}).get(codigo, {})
        if ficha:
            desc = str(ficha.get("descripcion", "")).strip().rstrip(".")
            return desc or codigo
    return codigo


def _nombre_producto(titulo: str) -> str:
    """Deriva el nombre del producto a partir del título de la partida."""
    t = titulo.strip().rstrip(".")
    tl = t.lower()
    for prefijo in PREFIJOS:
        if tl.startswith(prefijo):
            t = t[len(prefijo):].strip().rstrip(".")
            break
    # Primera letra en mayúscula para el texto del producto.
    t = t[:1].upper() + t[1:]
    return t


def procesar(partida: dict, *, aplicar: bool) -> dict | None:
    """Devuelve un resumen del cambio, o None si la partida no cambia."""
    codigo = partida.get("codigo", "")
    recursos = partida.get("recursos", [])
    refs = {r.get("ref") for r in recursos}

    es_elevacion = codigo.startswith("09.16.") and any(
        e in partida.get("titulo", "").lower() for e in ELEVACION
    ) and not any(n in partida.get("titulo", "").lower() for n in NO_ELEVACION)

    equipo = [r for r in recursos if r.get("ref") in EQUIPO]
    # En elevación el «ruido de demolición» también sale (no es demolición).
    ruido = [r for r in recursos if r.get("ref") in RUIDO_DEMOLICION and es_elevacion]

    if not equipo and not es_elevacion:
        return None

    quitar = {r.get("ref") for r in equipo} | {r.get("ref") for r in ruido}
    conservar = [r for r in recursos if r.get("ref") not in quitar]

    # El nombre del producto se deriva del título de la partida (más concreto
    # y legible que la descripción genérica del material). Caso especial: el
    # automatismo de portón es solo el motor; el portón se fabrica con los
    # materiales que permanecen en la partida.
    if quitar == {"MT-AUTOM-PORTON"}:
        producto = "Automatismo (motor) de portón"
    else:
        producto = _nombre_producto(partida.get("titulo", ""))

    nuevo_pc = {
        "tipo": producto + ", del modelo elegido por el cliente",
        "unidad": "ud",
        "consumo": 1.0,
        "nota": (
            "La partida cubre solo la instalación. El equipo se toma del "
            "catálogo de productos y su precio no está incluido."
        ),
    }

    resumen = {
        "codigo": codigo,
        "titulo": partida.get("titulo", ""),
        "quitados": sorted(quitar),
        "producto": producto,
        "recursos_antes": len(recursos),
        "recursos_despues": len(conservar),
    }

    if aplicar:
        partida["recursos"] = conservar
        partida["producto_cliente"] = nuevo_pc
        # El consumo del equipo ya no forma parte del coste: no se altera margen
        # ni complementarios (la nota ya advierte que no incluye el producto).

    return resumen


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reporte", action="store_true")
    ap.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()
    if not args.reporte and not args.aplicar:
        args.reporte = True

    archivos = sorted(ORIGEN.glob("*.json"))
    cambios = []
    for ruta in archivos:
        try:
            partida = json.loads(ruta.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if partida.get("codigo_legacy"):
            continue  # solo partidas nuevas de la ampliación
        resumen = procesar(partida, aplicar=args.aplicar)
        if resumen is not None:
            cambios.append(resumen)
            if args.aplicar:
                ruta.write_text(
                    json.dumps(partida, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )

    print(f"{'APLICADOS' if args.aplicar else 'DETECTADOS'} {len(cambios)} cambios")
    for c in cambios:
        print(f"  {c['codigo']}  ({c['recursos_antes']}→{c['recursos_despues']} rec) "
              f"-{', '.join(c['quitados']) or '(solo producto)'}  →  producto: {c['producto'][:60]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
