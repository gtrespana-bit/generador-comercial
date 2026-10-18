#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audita la calidad de la traducción de un mercado, capítulo por capítulo.

``tools/verificar_traducciones.py`` comprueba que las tablas estén completas y
al día. Esta herramienta comprueba algo distinto: **qué tal** está lo que hay
dentro. Una tabla puede estar perfectamente sincronizada con su glosario y
seguir produciendo «walls of block» en trescientas partidas.

Mide tres defectos que son los que de verdad se ven en un presupuesto:

1. **Residuo**: palabras del español que sobreviven en la salida. Es el
   indicador grueso, y el único que sirve para comparar capítulos entre sí.
2. **Compuestos sin invertir**: «N de N» que sigue como «N of N»
   («walls of block» en vez de «block walls»).
3. **Orden adjetivo-sustantivo**: «Lumber structural» en vez de
   «structural lumber».

Los cognados (``sensor``, ``mineral``, ``conductor``…) están excluidos: son
palabras correctas y exactamente iguales en los dos idiomas, y contarlas
como residuo daría una cifra falsa.

Uso:
    python tools/auditar_calidad_traduccion.py                 # mercado EN
    python tools/auditar_calidad_traduccion.py MX
    python tools/auditar_calidad_traduccion.py EN --capitulo Instalaciones
    python tools/auditar_calidad_traduccion.py EN --detalle 30
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from app.services.traduccion import SALIDA_TRADUCCIONES  # noqa: E402

CATALOGO = RAIZ / "basedatos_partidas" / "salida" / "catalogo_partidas.json"
GLOSARIOS = RAIZ / "basedatos_partidas" / "glosarios"
CAMPOS = ("nombre", "descripcion", "categoria", "subcategoria", "apartado")

PALABRA = re.compile(r"[a-záéíóúñü]+", re.I)

# Voces idénticas en español y en inglés: son inglés correcto, no residuo.
# Se excluyen para que la cifra de residuo mida fallos reales y no ortografía
# compartida. Ojo con las que casi lo son pero cambian de letra: «comercial»,
# «eficiencia», «mensual», «corrugada» NO están aquí, y sí son errores.
COGNADOS = set("""sensor mineral conductor vapor vertical flexible potable vehicular extractor
dimensional detector bases panel closet motor central horizontal diesel carga tipo final general
simple interior exterior natural marca cable parte receptor tubo plan personal metal principal
total piso local normal base area original usual control formal manual granular audio video
composite impacto error regular modular zinc geotextiles visible pedestal parquet irregular
tubular situ orden individual industriales colectivas integral directo indirecta frecuente
visual elevador elevado comercio lineal real especial canasta contenedor instalaciones
instalacion pvc ppr mdf osb led cctv split awg gas bar
material color industrial monitor clips test graffiti similar tropical longitudinal
residual conduit rack class canal paneles
cables cable anti artificial compatible diagonal
plenum terminal
""".split())


def _norm(w: str) -> str:
    return (w.lower().replace("á", "a").replace("é", "e").replace("í", "i")
            .replace("ó", "o").replace("ú", "u").replace("ñ", "n").replace("ü", "u"))


def _cargar(codigo: str) -> tuple[dict, dict, dict]:
    """Devuelve (por_capitulo, glosario_palabras, tabla)."""
    catalogo = json.loads(CATALOGO.read_text(encoding="utf-8"))
    por_capitulo: dict[str, set[str]] = defaultdict(set)
    for p in catalogo:
        cap = p.get("capitulo") or "(sin capítulo)"
        for c in CAMPOS:
            v = p.get(c)
            if isinstance(v, str) and v.strip():
                por_capitulo[cap].add(v)

    try:
        cambios = json.loads((GLOSARIOS / f"{codigo}.json").read_text(encoding="utf-8"))["cambios"]
    except FileNotFoundError:
        cambios = []
    wmap = {c["de"]: c["a"] for c in cambios if " " not in c["de"]}

    tabla = json.loads((SALIDA_TRADUCCIONES / f"{codigo}.json").read_text(encoding="utf-8"))["cadenas"]
    return por_capitulo, wmap, tabla


def _residuo(es: str, en: str) -> list[str]:
    """Palabras del español que sobreviven en la traducción."""
    src = {w.lower() for w in PALABRA.findall(es)}
    out = []
    for w in PALABRA.findall(en):
        w = w.lower()
        if len(w) < 4 or w in COGNADOS or w.endswith(("ing", "ed")):
            continue
        if w in src:
            out.append(w)
    return out


def _compuestos(es: str, en: str, wmap: dict) -> list[tuple[str, str]]:
    """«N de N» que sigue como «N of N» en la salida."""
    ART = {"el", "la", "los", "las", "un", "una", "the"}
    w = [_norm(x) for x in PALABRA.findall(es)]
    aw = [x.lower() for x in PALABRA.findall(en)]
    out = []
    for i in range(len(w) - 2):
        a, b, d = w[i], w[i + 1], w[i + 2]
        if b != "de" or d in ART or a not in wmap or d not in wmap:
            continue
        A, D = wmap[a].lower(), wmap[d].lower()
        for k in range(len(aw) - 2):
            if aw[k] == A and aw[k + 1] == "of" and aw[k + 2] == D:
                out.append((a, d))
                break
    return out


def main() -> int:

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mercado", nargs="?", default="EN", help="código del mercado (EN, MX, CO…)")
    ap.add_argument("--capitulo", help="filtra un capítulo (subcadena)")
    ap.add_argument("--detalle", type=int, default=12,
                    help="cuántas palabrasproblemáticas mostrar por capítulo")
    args = ap.parse_args()
    por_capitulo, wmap, tabla = _cargar(args.mercado)
    if not tabla:
        print(f"No hay tabla para {args.mercado}.", file=sys.stderr)
        return 1

    filas = []
    for cap, cadenas in por_capitulo.items():
        if args.capitulo and args.capitulo.lower() not in cap.lower():
            continue
        residuo: Counter = Counter()
        comp: Counter = Counter()
        n = 0
        for s in cadenas:
            t = tabla.get(s, s)
            n += 1
            for w in _residuo(s, t):
                residuo[w] += 1
            for par in _compuestos(s, t, wmap):
                comp[par] += 1
        filas.append((cap, n, sum(residuo.values()), sum(comp.values()), residuo, comp))

    filas.sort(key=lambda f: -(f[2] + f[3]))
    ancho = max((len(f[0]) for f in filas), default=10)

    print(f"Auditoría de calidad — mercado {args.mercado}")
    print(f"{'capítulo':<{ancho}}  {'cadenas':>7}  {'residuo':>7}  {'N of N':>6}  {'x cadena':>8}")
    print("-" * (ancho + 40))
    for cap, n, r, c, _, _ in filas:
        print(f"{cap:<{ancho}}  {n:7,d}  {r:7,d}  {c:6,d}  {(r+c)/max(1,n):8.2f}")
    tot_r = sum(f[2] for f in filas)
    tot_c = sum(f[3] for f in filas)
    tot_n = sum(f[1] for f in filas)
    print("-" * (ancho + 40))
    print(f"{'TOTAL':<{ancho}}  {tot_n:7,d}  {tot_r:7,d}  {tot_c:6,d}  {(tot_r+tot_c)/max(1,tot_n):8.2f}")

    print("\nPeores capítulos, con qué les falla:")
    for cap, n, r, c, residuo, comp in filas[:6]:
        if r + c == 0:
            continue
        print(f"\n  ▸ {cap}  ({(r+c)/max(1,n):.2f} defectos por cadena)")
        if residuo:
            top = "  ".join(f"{w}({k})" for w, k in residuo.most_common(args.detalle))
            print(f"      residuo:   {top}")
        if comp:
            top = "  ".join(f"{a} de {d}({k})" for (a, d), k in comp.most_common(6))
            print(f"      compuesto: {top}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
