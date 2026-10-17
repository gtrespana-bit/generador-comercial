#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Propone compuestos «N de N» -> «N N» para el glosario inglés.

Las entradas compuestas se generaron una vez, a partir del glosario tal y
como estaba aquel día. Desde entonces el glosario ha crecido mucho, así que
hay palabras que ahora se traducen y cuyo compuesto nunca se llegó a crear:
de ahí que sigan saliendo «treatment of damp» o «sensor of level» donde lo
correcto es «damp treatment» y «level sensor».

Este script vuelve a recorrer el catálogo buscando «N1 de N2» con las dos
palabras ya traducidas, y escribe una tabla para revisar:

    python tools/proponer_compuestos.py candidatos.tsv

No toca el glosario. La revisión es obligatoria: el filtro automático acierta
casi siempre, pero falla en los adjetivos y en los nombres de medida, y una
entrada mala («electrical floor») es peor que no tenerla.

Se excluyen:
  · determinantes y partículas («de la», «de un», «de su»…);
  · nombres de medida y partición («metro», «superficie», «parte», «tipo»…),
    porque en inglés esos sí piden «of»;
  · adjetivos y participios, que no pueden ser núcleo de un compuesto.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

CATALOGO = RAIZ / "basedatos_partidas" / "salida" / "catalogo_partidas.json"
GLOSARIO = RAIZ / "basedatos_partidas" / "glosarios" / "EN.json"
CAMPOS = ("nombre", "descripcion", "categoria", "subcategoria", "apartado")

PALABRA = re.compile(r"[a-záéíóúñü]+", re.I)

# Determinantes y partículas: si aparecen, no hay compuesto («de la losa»).
DETERMINANTES = frozenset(
    """el la los las un una unos unas lo su sus este esta estos estas ese esa esos esas
    mi tu su nuestro vuestro cada otro otra otros otras todo toda todos todas mismo misma
    cual cuales quien quienes que cuyo cuya más menos muy ya tan""".split()
)

# Conjunciones: «y de seguridad» no es un compuesto, es una coordinación.
CONJUNCIONES = frozenset("y o e ni pero sino".split())

# Nombres de medida, partición y clase: en inglés conservan «of».
MEDIDA = frozenset(
    """metro centímetro milímetro kilómetro pie pulgada yarda hora día semana mes año
    vez unidad precio coste costo importe superficie área volumen peso capacidad
    parte porcentaje total número cantidad conjunto grupo serie juego tipo clase
    modelo marca nivel altura anchura longitud distancia espesor grosor radio
    diámetro suma diferencia media máximo mínimo proporción razón factor índice
    grado porción tramo lado cara borde extremo""".split()
)

# Terminaciones de adjetivo y participio en español: no son núcleo válido.
SUF_ADJ = ("ado", "ada", "ados", "adas", "ido", "ida", "idos", "idas", "ivo", "iva",
           "ivos", "ivas", "oso", "osa", "osos", "osas", "able", "ibles", "ante",
           "entes", "ico", "ica", "icos", "icas", "al", "ales", "ar", "ares")


def _norm(w: str) -> str:
    return (w.lower().replace("á", "a").replace("é", "e").replace("í", "i")
            .replace("ó", "o").replace("ú", "u").replace("ñ", "n").replace("ü", "u"))


def _singular_en(palabra: str) -> str:
    """Singular inglés del modificador: en un compuesto inglés va en singular."""
    if palabra.endswith("ies") and len(palabra) > 4:
        return palabra[:-3] + "y"
    if re.search(r"(ss|us|is)$", palabra):
        return palabra
    if re.search(r"[^aeiou]es$", palabra) and not re.search(r"(ss|sh|ch|x|z)es$", palabra):
        return palabra[:-1]
    if palabra.endswith("s") and not palabra.endswith(("ss", "us", "is")):
        return palabra[:-1]
    return palabra


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("salida", help="TSV donde escribir los candidatos")
    ap.add_argument("--minimo", type=int, default=1,
                    help="usos mínimos en el catálogo (por omisión 1)")
    args = ap.parse_args()

    catalogo = json.loads(CATALOGO.read_text(encoding="utf-8"))
    cambios = json.loads(GLOSARIO.read_text(encoding="utf-8"))["cambios"]
    wmap = {c["de"]: c["a"] for c in cambios if " " not in c["de"]}
    frases = {c["de"] for c in cambios if " " in c["de"]}

    pares: Counter = Counter()
    for p in catalogo:
        for campo in CAMPOS:
            s = p.get(campo)
            if not isinstance(s, str):
                continue
            w = [_norm(x) for x in PALABRA.findall(s)]
            for i in range(len(w) - 2):
                a, b, d = w[i], w[i + 1], w[i + 2]
                if b != "de" or d in DETERMINANTES or a in DETERMINANTES \
                        or a in CONJUNCIONES:
                    continue
                if a not in wmap or d not in wmap:
                    continue
                if a in MEDIDA or d in MEDIDA:
                    continue
                if a.endswith(SUF_ADJ) or d.endswith(SUF_ADJ):
                    continue
                clave = f"{a} de {d}"
                if clave in frases:
                    continue
                pares[(a, d)] += 1

    filas = []
    for (a, d), usos in pares.most_common():
        if usos < args.minimo:
            continue
        propuesta = f"{_singular_en(wmap[d])} {wmap[a]}"
        filas.append((a, d, wmap[a], wmap[d], propuesta, usos))

    with open(args.salida, "w", encoding="utf-8") as f:
        f.write("origen\tpropuesta\tn1_en\tn2_en\tusos\n")
        for a, d, ea, ed, prop, usos in filas:
            f.write(f"{a} de {d}\t{prop}\t{ea}\t{ed}\t{usos}\n")

    print(f"{len(filas)} candidatos -> {args.salida}")
    print("\nLos 30 más usados, para revisar a ojo:")
    for a, d, ea, ed, prop, usos in filas[:30]:
        print(f"  {usos:3,d}  {a} de {d:18} -> {prop}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
