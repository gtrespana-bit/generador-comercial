#!/usr/bin/env python3
"""Lector completo de la Base de Costes de la Construcción de Andalucía (BCCA).

El lector genérico ``cruzar_precios_bc3.leer_bc3`` reconoce solo los códigos con
prefijo ``P`` (materiales), ``M`` (maquinaria) y ``O`` (mano de obra), que es la
nomenclatura de la base de Extremadura. La BCCA usa **otra** nomenclatura
(``A01JF006``, ``CA00220``, ``IC00050``, ``KA00100``, ``U04AA001``…), así que con
aquel lector solo se aprovechaban 196 de sus 15.514 registros de precio: el 1,3 %
del banco.

Este módulo lee la BCCA entera y clasifica cada precio por su unidad y su
descripción, no por el prefijo del código:

* ``mano_obra`` — descripción de oficio (oficial, peón, ayudante, cuadrilla…).
* ``maquinaria`` — unidad ``h`` (y descripción de máquina).
* ``materiales`` — el resto, con unidad de medida física.

Se descartan las ramas del árbol (códigos con ``#``), los conceptos que tienen
descomposición (partidas y auxiliares: su precio incluye instalación y no se
puede comparar con un precio simple), los códigos de relleno sin ningún dígito
(``FJGJKL``, ``HJJHFDF``…: descripción de una palabra y precio redondo), las
unidades no reconocidas y los importes vacíos, nulos o negativos.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

from cruzar_precios_bc3 import Precio, limpiar, unidad

# Oficios: la descripción manda sobre la unidad, porque un oficial también se
# cotiza por hora y no es maquinaria.
OFICIOS = (
    "oficial", "peon", "peón", "ayudante", "cuadrilla", "encargado", "capataz",
    "jefe de equipo", "jefe de obra", "maquinista", "gruista", "soldador",
    "oficialia", "mano de obra", "operario", "especialista",
)
HORA = {"h"}


@dataclass(frozen=True)
class Registro:
    """Un precio simple con la traza de cómo se ha clasificado."""

    codigo: str
    unidad: str
    descripcion: str
    importe: Decimal
    categoria: str
    fecha: str
    familia: str


def _texto(path: Path) -> str:
    bruto = path.read_bytes()
    if bruto.startswith(b"\xef\xbb\xbf"):
        return bruto.decode("utf-8-sig")
    if bruto.startswith((b"\xff\xfe", b"\xfe\xff")):
        return bruto.decode("utf-16")
    try:
        return bruto.decode("utf-8")
    except UnicodeDecodeError:
        return bruto.decode("cp1252", errors="replace")


def clasificar(descripcion: str, unidad_precio: str) -> str | None:
    """Categoría de un precio simple de la BCCA, o ``None`` si no es utilizable."""
    texto = limpiar(descripcion)
    if any(oficio in texto for oficio in OFICIOS):
        return "mano_obra"
    if unidad_precio in HORA:
        return "maquinaria"
    return "materiales"


def familia(codigo: str) -> str:
    """Capítulo de la BCCA (letra inicial del código, sin dígitos)."""
    letra = re.match(r"[A-Za-zÑ]", codigo)
    return letra.group(0).upper() if letra else codigo[:1].upper()


def leer_bcca(path: Path) -> tuple[list[Registro], str]:
    bruto = path.read_bytes()
    sha = hashlib.sha256(bruto).hexdigest()
    registros = re.split(r"~(?=[A-Za-z]\|)", _texto(path))
    conceptos: dict[str, list[str]] = {}
    descripciones: dict[str, str] = {}
    con_descomposicion: set[str] = set()
    for registro in registros:
        partes = registro.split("|")
        if len(partes) < 3:
            continue
        tipo, codigo = partes[0].upper(), partes[1].strip()
        if tipo == "D":
            con_descomposicion.add(codigo)
        elif tipo == "T":
            descripciones[codigo] = " ".join(partes[2].split()) if len(partes) > 2 else ""
        elif tipo == "C" and len(partes) >= 5 and codigo not in conceptos:
            conceptos[codigo] = partes

    salida: list[Registro] = []
    for codigo, partes in conceptos.items():
        if not codigo or "#" in codigo or codigo in con_descomposicion:
            continue
        # El archivo publicado mezcla fichas con código de relleno (FJGJKL,
        # JFJFGFD, HJJHFDF…): descripción de una palabra y precio redondo. No son
        # artículos de la base y no pueden sostener ninguna comparación.
        if not any(c.isdigit() for c in codigo):
            continue
        u = unidad(partes[2].strip())
        if not u:
            continue
        crudo = partes[4].strip()
        if not re.fullmatch(r"\d+(?:[.,]\d+)?", crudo):
            continue
        try:
            importe = Decimal(crudo.replace(",", "."))
        except InvalidOperation:
            continue
        if not importe.is_finite() or importe <= 0:
            continue
        descripcion = partes[3].strip() or descripciones.get(codigo, "")
        categoria = clasificar(descripcion, u)
        if categoria is None:
            continue
        salida.append(Registro(codigo, u, descripcion, importe, categoria,
                               partes[5].strip() if len(partes) > 5 else "",
                               familia(codigo)))
    return salida, sha


def precios(path: Path) -> tuple[list[Precio], str]:
    """Los mismos registros con la forma que espera el cribado."""
    registros, sha = leer_bcca(path)
    return [Precio(r.codigo, r.unidad, r.descripcion, "", r.importe, r.categoria, r.fecha)
            for r in registros], sha


if __name__ == "__main__":
    import sys
    from collections import Counter

    ruta = Path(sys.argv[1] if len(sys.argv) > 1 else "bases_precios/BCCA2023_V02.bc3")
    registros, sha = leer_bcca(ruta)
    print(f"{ruta}: {len(registros)} precios simples; sha256={sha[:16]}…")
    print("por categoría:", Counter(r.categoria for r in registros).most_common())
    print("por unidad:", Counter(r.unidad for r in registros).most_common())
    print("por familia:", Counter(r.familia for r in registros).most_common())
