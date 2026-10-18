#!/usr/bin/env python3
"""Extrae cadenas traducibles de una plantilla Jinja.

Saca el texto visible (entre etiquetas) y los atributos que el usuario lee
(placeholder, title, alt, aria-label, data-confirm, value de botones).

Uso:
    python tools/extraer_textos.py app/templates/productos/list.html
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ATTRS = (
    "placeholder",
    "title",
    "alt",
    "aria-label",
    "data-confirm",
)


def extraer(ruta: Path) -> list[str]:
    html = ruta.read_text(encoding="utf-8")
    # 1) atributos traducibles (comillas dobles y simples)
    fuera: list[str] = []
    for attr in ATTRS:
        fuera += re.findall(rf'{attr}="([^"{{}}]*)"', html)
        fuera += re.findall(rf"{attr}='([^'{{}}]*)'", html)
    # 2) texto visible: fuera de etiquetas y de bloques Jinja
    sin_bloques = re.sub(r"\{[%{].*?[%}]\}", "\x00", html, flags=re.S)
    sin_estilo = re.sub(r"<(script|style)\b.*?</\1>", "\x00", sin_bloques, flags=re.S | re.I)
    sin_coment = re.sub(r"<!--.*?-->", "\x00", sin_estilo, flags=re.S)
    trozos = re.split(r"<[^>]*>", sin_coment)
    fuera += [t for t in trozos if t and "\x00" not in t]
    # 3) limpiar
    out: list[str] = []
    for t in fuera:
        t = t.replace("\n", " ").strip()
        t = re.sub(r"\s{2,}", " ", t)
        if not t:
            continue
        if not re.search(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]", t):
            continue
        out.append(t)
    # únicos, orden estable
    vistos: set[str] = set()
    unicos = []
    for t in out:
        if t not in vistos:
            vistos.add(t)
            unicos.append(t)
    return unicos


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        p = Path(arg)
        print(f"### {p}  ({len(extraer(p))} cadenas)")
        for t in extraer(p):
            print("  " + t)
