#!/usr/bin/env python3
"""Radiografía de los 23 mercados: ¿se puede encender su catálogo hoy?

Responde, con un número y no con una opinión, la pregunta que dejó abierta el
incidente del 23/10/2026: **¿la ficha de este mercado es un original o es la
española con otro precio?** Si es lo segundo, anunciarla vuelve a presentar a
Google miles de páginas casi iguales, que es lo que hundió el sitio aquel día.

Se ejecuta sobre los ficheros del repositorio (no toca la base, no pide red ni
credenciales) y saca una tabla por mercado con:

* ``estado``: ``referencia`` (España), ``listo``, ``parcial``, ``calco`` o
  ``sin_catalogo``.
* ``partidas``: fichas publicables hoy en ese mercado.
* ``jaccard``: parecido del vocabulario con España (1,00 = calcado).
* ``idénticas``: fichas cuyo texto es literalmente el español.
* ``guías`` y ``editorial``: lo que el mercado tiene además del catálogo.
* ``urls``: cuántas URL nuevas se anunciarían si se encendiera.

Uso:
  python tools/radar_activacion_mercados.py
  python tools/radar_activacion_mercados.py --muestra 0        # todas las fichas
  python tools/radar_activacion_mercados.py --json radar.json
  python tools/radar_activacion_mercados.py --mercado MX

La puerta que abre este radar está en ``tests/test_activacion_mercados.py``:
un mercado no entra en ``MERCADOS_FICHAS_INDEXABLES`` con la prosa española.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from app.services import localizacion, precios_publicos as pp  # noqa: E402

_ETIQUETA = {
    "referencia": "REFERENCIA",
    "listo": "LISTO",
    "parcial": "PARCIAL",
    "calco": "CALCO",
    "sin_catalogo": "SIN CATÁLOGO",
}


def _urls(cc: str) -> int:
    """URLs que se anunciarían si el mercado se encendiera ahora."""
    indice = pp._indice(cc) or {}
    total = 1 + len(indice.get("apartados") or {})
    total += len(indice.get("partidas") or {})
    try:
        if pp.oficios_disponibles(cc):
            total += 1
    except Exception:
        pass
    return total


def _fila_editorial(editorial: dict, guias: int) -> str:
    marcas = []
    if editorial.get("tecnica"):
        marcas.append("técnica")
    if editorial.get("labor"):
        marcas.append("mano de obra")
    if editorial.get("documento"):
        marcas.append("documento")
    if guias:
        marcas.append(f"{guias} guías")
    return ", ".join(marcas) or "—"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="¿Qué mercados pueden encender su catálogo sin repetir el 23/10?",
    )
    parser.add_argument(
        "--muestra",
        type=int,
        default=localizacion.MUESTRA_POR_DEFECTO,
        help=(
            "fichas por mercado a comparar (0 = todas; por defecto "
            f"{localizacion.MUESTRA_POR_DEFECTO})"
        ),
    )
    parser.add_argument("--mercado", help="un solo mercado (MX, CO, ES…)")
    parser.add_argument("--json", metavar="RUTA", help="guardar el resultado en JSON")
    args = parser.parse_args(argv)

    muestra = args.muestra
    if args.mercado:
        filas = [localizacion.veredicto(args.mercado, muestra)]
    else:
        filas = localizacion.radar(muestra)
    if args.json:
        Path(args.json).write_text(
            json.dumps(filas, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    cabecera = (
        f"{'MERCADO':<8} {'ESTADO':<13} {'PARTIDAS':>8} {'JACCARD':>8} "
        f"{'IDÉNTICAS':>9} {'URLS':>6}  EDITORIAL"
    )
    print(cabecera)
    print("-" * len(cabecera))
    for fila in filas:
        cc = fila["mercado"]
        jaccard = "—" if fila["jaccard"] is None else f"{fila['jaccard']:.3f}"
        identicas = (
            "—" if fila["porcentaje_identico"] is None
            else f"{fila['porcentaje_identico']:.1f} %"
        )
        urls = _urls(cc) if fila["publicado"] else 0
        print(
            f"{cc:<8} {_ETIQUETA.get(fila['estado'], fila['estado']):<13} "
            f"{fila['partidas']:>8} {jaccard:>8} {identicas:>9} {urls:>6}  "
            f"{_fila_editorial(fila['editorial'], fila['guias'])}"
        )

    indexables = [
        f["mercado"] for f in filas if f["mercado"] in pp.MERCADOS_FICHAS_INDEXABLES
    ]
    pendientes = [
        f
        for f in filas
        if f["publicado"]
        and not f["referencia"]
        and f["mercado"] not in pp.MERCADOS_FICHAS_INDEXABLES
    ]
    calcos = [f["mercado"] for f in pendientes if f["estado"] == "calco"]
    parciales = [f["mercado"] for f in pendientes if f["estado"] == "parcial"]

    print()
    print(f"Anunciados hoy ({len(indexables)}): {', '.join(indexables) or '—'}")
    try:
        from app.paises import PAISES

        sin_catalogo = [
            cc for cc in PAISES if cc not in pp.PAISES_PRECIOS_PUBLICOS
        ]
    except Exception:  # pragma: no cover - el registro de países siempre existe
        sin_catalogo = []
    if sin_catalogo:
        print(
            f"Sin matriz de precios propia ({len(sin_catalogo)}): "
            f"{', '.join(sin_catalogo)} — sus fichas se sirven con precios base "
            "en USD, así que no hay catálogo que encender."
        )
    if calcos:
        print(f"Calcados, no encender ({len(calcos)}): {', '.join(calcos)}")
    if parciales:
        print(f"A medio localizar ({len(parciales)}): {', '.join(parciales)}")
    orden = localizacion.mercados_por_encender(muestra)
    if orden:
        print(f"Orden propuesto para encender: {' → '.join(orden)}")
    print()
    print(
        "Un mercado pasa a LISTO cuando su prosa deja de ser la española "
        f"(jaccard < {localizacion.UMBRAL_PROPIA:.2f}). No se cambia el umbral: "
        "se escribe el texto del mercado."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
