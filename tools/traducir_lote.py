#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Carga un lote de traducciones completas en las excepciones del glosario.

El glosario traduce términos, y hay textos que ningún glosario puede
resolver: «Ventana de aluminio batiente o proyectante» sale como «Aluminum
window swinging or awning window» porque la sintaxis inglesa no es la
española y las reglas trabajan palabra a palabra. Para esos casos el
glosario ya prevé un fichero de excepciones: cadenas completas traducidas a
mano que ganan siempre y se aplican antes que cualquier regla.

Este es el sitio donde va la traducción del catálogo propiamente dicha, no
un parche: es la fuente de la que salen las tablas de los cinco mercados
anglófonos. La variante de cada país (GB, IE, AU, CA) se aplica después,
sobre la traducción ya correcta, así que una sola traducción sirve a los
cinco.

Comprobaciones antes de escribir:
  · la cadena de origen tiene que existir en el catálogo (si no, es una
    traducción huérfana que nadie va a usar);
  · no se permite una traducción vacía ni igual al origen;
  · se avisa si ya había una traducción distinta, para no pisar trabajo.

Uso como librería:

    sys.path.insert(0, "tools")
    from traducir_lote import cargar_traducciones
    cargar_traducciones({"Suministro y montaje de...": "Supply and installation of..."})

Uso directo:

    python tools/traducir_lote.py lote.json
"""
from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

GLOSARIOS = RAIZ / "basedatos_partidas" / "glosarios"
CATALOGO = RAIZ / "basedatos_partidas" / "salida" / "catalogo_partidas.json"
CAMPOS = ("nombre", "descripcion", "categoria", "subcategoria", "apartado")


# Fragmentos que delatan inglés colado dentro de una cadena de origen en
# español. Son los cierres y las fórmulas que se repiten al final de casi
# todas las descripciones del catálogo, que es justo donde se cuela el dedazo.
_FRAGMENTOS_INGLES = (
    "Measured per", "Includes ", " per square meter", " per meter",
    " per unit", " per set", " per point", " per hour", " per month",
    "Supply and installation", "Installation of the", " by the ",
)


def cadenas_del_catalogo() -> set[str]:
    cat = json.loads(CATALOGO.read_text(encoding="utf-8"))
    return {_nfc(p[c]) for p in cat for c in CAMPOS
            if isinstance(p.get(c), str) and p[c].strip()}


def _nfc(texto: str) -> str:
    """Unicode compuesto, para que una tilde no parta una cadena en dos.

    «Peldaño» escrito con tilde combinante y con «ñ» se ven iguales en
    pantalla pero son dos cadenas distintas, así que una clave así no
    encuentra su original en el catálogo y queda como traducción
    huérfana. Normalizar aquí y al escribir el catálogo cierra el hueco
    por los dos lados.
    """
    return unicodedata.normalize("NFC", texto)


def ruta_excepciones(codigo: str) -> Path:
    return GLOSARIOS / f"{codigo}.excepciones.json"


def cargar_traducciones(lote: dict[str, str], mercado: str = "EN",
                        forzar: bool = False, seco: bool = False) -> int:
    ruta = ruta_excepciones(mercado)
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        datos = {"_comentario": "Traducciones completas, mano a mano.", "cadenas": {}}

    datos.setdefault("cadenas", {})
    tabla: dict[str, str] = datos["cadenas"]
    en_catalogo = cadenas_del_catalogo()

    # Un descuido al teclear un lote cuela a veces un fragmento en inglés
    # dentro de la cadena española («Medido por…» escrito ya como «Measured
    # per…»). La cadena resultante no está en el catálogo, así que solo se
    # detectaba después, como traducción huérfana. Se comprueba aquí, que es
    # donde todavía se sabe de qué lote viene.
    con_ingles = []
    for original in lote:
        for frag in _FRAGMENTOS_INGLES:
            if frag in original:
                con_ingles.append((original, frag))
                break
    if con_ingles:
        print(f"AVISO: {len(con_ingles)} cadenas de origen traen inglés dentro:")
        for texto, frag in con_ingles[:5]:
            i = texto.find(frag)
            print(f'   ...{texto[max(0, i - 45):i + 45]}...   («{frag}»)')
        print("\nNo se escribe nada. Corrígelas y vuelve a cargar.")
        return 0

    nuevas, chocan, huerfanas, vacias = [], [], [], []
    for original, en in lote.items():
        es = _nfc(original)
        if not en or not en.strip():
            vacias.append(es)
            continue
        if es not in en_catalogo:
            huerfanas.append(es)
        if es in tabla:
            if tabla[es] == en:
                continue
            chocan.append((es, tabla[es], en))
            continue
        nuevas.append((es, en))

    if vacias:
        print(f"descartadas {len(vacias)} vacías")
    if huerfanas:
        print(f"AVISO: {len(huerfanas)} no están en el catálogo, no se usarán:")
        for h in huerfanas[:5]:
            print(f"   {h[:90]}")
    if chocan and not forzar:
        print(f"AVISO: {len(chocan)} ya tenían traducción distinta:")
        for es, vieja, nueva in chocan[:5]:
            print(f"   {es[:60]}")
            print(f"      antes: {vieja[:80]}")
            print(f"      ahora: {nueva[:80]}")
        print("\nNo se escribe nada. Usa forzar=True si la nueva es mejor.")
        return 0

    for es, vieja, nueva in chocan:
        tabla[es] = nueva

    if seco:
        print(f"(seco) {len(nuevas)} traducciones nuevas · {len(chocan)} sustituidas")
        return len(nuevas)

    tabla.update(dict(nuevas))
    datos["cadenas"] = dict(sorted(tabla.items()))
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    print(f"✓ {ruta.name}: {len(tabla):,d} cadenas "
          f"(+{len(nuevas):,d} nuevas, {len(chocan)} sustituidas)")
    return len(nuevas)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("lote", help="JSON con {texto_espanol: texto_ingles}")
    ap.add_argument("--mercado", default="EN")
    ap.add_argument("--forzar", action="store_true")
    ap.add_argument("--seco", action="store_true")
    args = ap.parse_args()
    lote = json.loads(Path(args.lote).read_text(encoding="utf-8"))
    cargar_traducciones(lote, mercado=args.mercado, forzar=args.forzar, seco=args.seco)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
