#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Carga un lote de entradas en un glosario, con comprobaciones previas.

Mantener un glosario de varios miles de entradas a base de editar el JSON a
mano acaba mal por tres motivos, y este script existe para los tres:

1. **Pisar una regla anterior.** Las entradas se aplican por orden, así que
   una nueva con la misma clave puede dejar sin efecto una corrección que ya
   estaba hecha. Aquí eso se detiene y se muestra el valor anterior.
2. **Entradas inútiles.** ``"muro": "muro"`` no traduce nada y, peor, ocupa
   la clave y bloquea la regla que sí traduciría esa palabra.
3. **Duplicados.** Al forzar una entrada hay que sustituir la existente, no
   añadir una segunda con la misma clave.

No escribe nada si detecta un choque y no se pide forzarlo.

Uso como librería (lo normal, desde un script de lote):

    sys.path.insert(0, "tools")
    from cargar_glosario import cargar
    cargar({"palabra": "word", ...})            # mercado EN por omisión
    cargar({...}, mercado="CO")                 # otro mercado
    cargar({...}, forzar=True)                  # sobrescribe lo que choque

Uso directo con un JSON de lote:

    python tools/cargar_glosario.py lote.json
    python tools/cargar_glosario.py lote.json --mercado CO --forzar
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DIR_GLOSARIOS = RAIZ / "basedatos_partidas" / "glosarios"


def ruta_glosario(mercado: str) -> Path:
    return DIR_GLOSARIOS / f"{mercado.upper()}.json"


def cargar(lote: dict[str, str], mercado: str = "EN",
           forzar: bool = False, seco: bool = False) -> int:
    """Añade ``lote`` al glosario de ``mercado``. Devuelve cuántas se añadieron."""
    ruta = ruta_glosario(mercado)
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    cambios = datos["cambios"]
    existentes = {c["de"]: c["a"] for c in cambios}

    anadidas: list[dict] = []
    chocan: list[tuple[str, str, str]] = []
    inutiles: list[str] = []
    ignoradas: list[str] = []

    for de, a in lote.items():
        if not a or not a.strip():
            inutiles.append(de)
            continue
        if de == a:
            inutiles.append(de)
            continue
        if de in existentes:
            if existentes[de] == a:
                ignoradas.append(de)
            else:
                chocan.append((de, existentes[de], a))
            continue
        anadidas.append({"de": de, "a": a})

    if inutiles:
        print(f"descartadas {len(inutiles)} vacías o sin efecto: {inutiles}")

    if chocan and not forzar:
        print("AVISO: entradas que ya existen con otro destino.")
        print("       Revísalas; si la nueva es mejor, usa forzar=True\n")
        for de, viejo, nuevo in chocan:
            print(f"   {de!r:30} ya era {viejo!r:26} -> propuesto {nuevo!r}")
        print("\nNo se escribe nada.")
        return 0

    if forzar:
        # Sustituir en el sitio. Añadir una segunda entrada con la misma clave
        # deja un duplicado que el verificador rechaza y que además gana o
        # pierde según el orden, que es justo lo que aquí se quiere evitar.
        for de, _viejo, nuevo in chocan:
            for c in cambios:
                if c["de"] == de:
                    c["a"] = nuevo
                    anadidas.append({"de": de, "a": nuevo})

    if seco:
        print(f"(seco) {ruta.name}: {len(anadidas)} entradas habrían entrado")
        return len(anadidas)

    cambios.extend(anadidas)
    datos["cambios"] = cambios
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    if ignoradas:
        print(f"   {len(ignoradas)} ya estaban igual y se han omitido")
    print(f"✓ {ruta.name}: {len(cambios)} entradas (+{len(anadidas)})")
    return len(anadidas)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("lote", help="JSON con un objeto {origen: destino}")
    ap.add_argument("--mercado", default="EN", help="código del mercado (EN, CO, MX…)")
    ap.add_argument("--forzar", action="store_true",
                    help="sobrescribe las entradas que ya existan")
    ap.add_argument("--seco", action="store_true", help="no escribe, solo informa")
    args = ap.parse_args()

    lote = json.loads(Path(args.lote).read_text(encoding="utf-8"))
    if not isinstance(lote, dict):
        print("El lote debe ser un objeto JSON {origen: destino}.", file=sys.stderr)
        return 1
    cargar(lote, mercado=args.mercado, forzar=args.forzar, seco=args.seco)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
