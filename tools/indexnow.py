#!/usr/bin/env python3
"""Envía URLs a IndexNow (Bing y, con su índice, Yahoo). Ensayo por defecto.

Sin ``--enviar`` no toca la red: construye exactamente el lote que
enviaría (las URLs del sitemap, desde ``app.seo.urls_sitemap``) y lo
enseña. Con ``--enviar`` hace el POST a ``api.indexnow.org``.

Google no escucha IndexNow: su vía es el sitemap en Search Console.
Esto es solo el acelerador de Bing/Yahoo.

Uso:
  python tools/indexnow.py                    # ensayo: qué se enviaría
  python tools/indexnow.py --limite 10        # ensayo con las 10 primeras
  python tools/indexnow.py --enviar           # envía todo el sitemap
  python tools/indexnow.py --enviar --precios # sitemap + catálogo (47k URL)
  python tools/indexnow.py --enviar --url https://cotizat.online/nueva-guia
                                              # solo esa URL (repetible)

Requisito previo: que la clave ya se sirva en producción
(``https://cotizat.online/{clave}.txt``); si el despliegue aún no
incluye la ruta, IndexNow responderá 403.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

ENDPOINT = "https://api.indexnow.org/indexnow"

# IndexNow admite hasta 10.000 URLs por lote.
MAXIMO_POR_LOTE = 10_000

_SIGNIFICADO = {
    200: "OK: URLs recibidas",
    202: "Aceptado: la clave se verificará después",
    400: "Formato inválido",
    403: "Clave no válida (¿se sirve ya el fichero de la clave?)",
    422: "URLs fuera del host o la clave no coincide con el fichero",
    429: "Demasiadas peticiones (posible spam)",
}


def _lotes(urls: list[str]) -> list[list[str]]:
    return [
        urls[i : i + MAXIMO_POR_LOTE]
        for i in range(0, len(urls), MAXIMO_POR_LOTE)
    ]


def _enviar_lote(payload: dict) -> int:
    peticion = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(peticion, timeout=30) as respuesta:
            return int(respuesta.status)
    except urllib.error.HTTPError as exc:
        return int(exc.code)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--enviar", action="store_true",
        help="envía de verdad (sin esto, solo enseña el lote)",
    )
    parser.add_argument(
        "--limite", type=int, default=None,
        help="solo las N primeras URLs del sitemap",
    )
    parser.add_argument(
        "--url", action="append", default=None,
        help="URL concreta a enviar en vez del sitemap (repetible)",
    )
    parser.add_argument(
        "--precios", action="store_true",
        help="incluye el catálogo de precios (sitemaps sitemap-precios-{cc}.xml)",
    )
    parser.add_argument(
        "--cc", default=None,
        help="con --precios, limita el catálogo a un mercado (MX, US, …)",
    )
    args = parser.parse_args()

    from app.indexnow import CLAVE, RUTA_CLAVE

    if args.url:
        urls = list(args.url)
        origen = "URLs pedidas por --url"
    else:
        from app.seo import urls_sitemap

        urls = [str(entrada["loc"]) for entrada in urls_sitemap()]
        origen = "sitemap completo"
        if args.precios:
            from app.indexnow import urls_precios

            precios = urls_precios(cc=args.cc)
            ya = set(urls)
            urls.extend(u for u in precios if u not in ya)
            etiqueta = f"catálogo de precios de {args.cc}" if args.cc else "catálogo de precios"
            origen = f"{origen} + {etiqueta} ({len(precios)} URL)"
        if args.limite is not None:
            urls = urls[: max(0, args.limite)]
            origen = f"{origen}, primeras {len(urls)}"
    if not urls:
        print("No hay URLs que enviar.")
        return 1

    hosts = {urlparse(u).netloc for u in urls}
    if len(hosts) != 1:
        print(f"Las URLs no comparten un único host: {sorted(hosts)}")
        return 1
    host = hosts.pop()
    ubicacion_clave = f"https://{host}{RUTA_CLAVE}"
    lotes = _lotes(urls)

    print(f"Host:           {host}")
    print(f"Clave (txt):    {ubicacion_clave}")
    print(f"Origen:         {origen}")
    print(f"URLs:           {len(urls)} en {len(lotes)} lote(s)")
    for url in urls[:5]:
        print(f"  - {url}")
    if len(urls) > 5:
        print(f"  … y {len(urls) - 5} más (última: {urls[-1]})")

    if not args.enviar:
        print("\nEnsayo: no se ha enviado nada. Añade --enviar para el POST.")
        return 0

    fallos = 0
    for numero, lote in enumerate(lotes, start=1):
        estado = _enviar_lote(
            {
                "host": host,
                "key": CLAVE,
                "keyLocation": ubicacion_clave,
                "urlList": lote,
            }
        )
        significado = _SIGNIFICADO.get(estado, "respuesta no documentada")
        print(f"Lote {numero}/{len(lotes)} ({len(lote)} URLs): HTTP {estado} — {significado}")
        if estado not in (200, 202):
            fallos += 1
    if fallos:
        print(f"\nResultado: {fallos} lote(s) rechazados.")
        return 1
    print("\nResultado: todo enviado. Bing/Yahoo procesarán la cola a su ritmo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
