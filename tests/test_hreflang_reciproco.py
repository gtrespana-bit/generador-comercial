"""hreflang recíproco: si A declara a B, B tiene que declarar a A.

Google no exige reciprocidad para entender un par, pero sí la usa para
validarlo: cuando una URL declara un grupo y las del grupo no la declaran a
ella, el conjunto queda «incoherente» y la señal se descarta —la página se
queda sin variantes y compite sola contra su propia versión en otro idioma—.

Había 78 páginas en esa situación: el hub inglés genérico
(``/en/unit-price-analysis``) declaraba los 26 mercados y ninguno lo
declaraba a él, porque el valor ``en`` apuntaba a ``/en-us/``. El inglés
genérico y el mercado de EE. UU. son dos documentos distintos con dos URLs
distintas, y el mercado ya aporta su propio ``en-US``.

Se comprueba, para todo el sitemap:

- Todas las URL declaradas responden 200 (una variante que redirige se
  descarta igual).
- Todas declaran hreflang.
- Cada una devuelve el mismo conjunto de etiquetas que la página de origen.
- La página de origen aparece en su propio grupo.
"""
from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.seo import urls_sitemap

BASE = "https://cotizat.online"


@pytest.fixture(scope="module")
def alternates():
    """hreflang de cada URL del sitemap y de sus destinos, sin repetir consultas."""
    cache: dict[str, tuple[int, list[tuple[str, str]]]] = {}

    def leer(cliente, url: str):
        if url not in cache:
            ruta = url.replace(BASE, "")
            respuesta = cliente.get(ruta, follow_redirects=False)
            if respuesta.status_code != 200:
                cache[url] = (respuesta.status_code, [])
            else:
                cache[url] = (
                    200,
                    re.findall(
                        r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"',
                        respuesta.text,
                    ),
                )
        return cache[url]

    with TestClient(app, base_url=BASE) as cliente:
        for entrada in urls_sitemap():
            url = entrada["loc"]
            estado, pares = leer(cliente, url)
            if estado != 200:
                continue
            for _etiqueta, destino in pares:
                leer(cliente, destino)
    return cache


def test_los_destinos_del_hreflang_existen(alternates):
    rotos = {
        destino: estado
        for destino, (estado, _pares) in alternates.items()
        if estado != 200
    }
    assert not rotos, list(rotos.items())[:10]


def test_el_grupo_es_reciproco(alternates):
    incoherentes = []
    for url, (estado, pares) in alternates.items():
        if estado != 200 or not pares:
            continue
        propias = {etiqueta for etiqueta, _ in pares}
        for etiqueta, destino in pares:
            estado_destino, pares_destino = alternates[destino]
            if estado_destino != 200:
                continue
            if not pares_destino:
                incoherentes.append((url, etiqueta, destino, "sin hreflang"))
                continue
            if url not in {d for _, d in pares_destino}:
                incoherentes.append((url, etiqueta, destino, "no devuelve"))
            elif {e for e, _ in pares_destino} != propias:
                incoherentes.append((url, destino, "conjunto distinto"))
    assert not incoherentes, incoherentes[:10]


def test_cada_pagina_esta_en_su_propio_grupo(alternates):
    faltan = [
        url
        for url, (estado, pares) in alternates.items()
        if estado == 200 and pares and url not in {d for _, d in pares}
    ]
    assert not faltan, faltan[:10]


@pytest.mark.parametrize(
    "ruta",
    ["/apu", "/mx/apu", "/en/unit-price-analysis", "/en-us/unit-price-analysis"],
)
def test_el_ingles_generico_y_el_mercado_estadounidense_son_documentos_distintos(
    ruta,
):
    """``en`` es el hub inglés sin mercado; «en-US» es el mercado."""
    with TestClient(app, base_url=BASE) as cliente:
        html = cliente.get(ruta).text
    pares = dict(
        (etiqueta, href)
        for etiqueta, href in re.findall(
            r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"', html
        )
    )
    assert pares["en"] == f"{BASE}/en/unit-price-analysis"
    assert pares["en-US"] == f"{BASE}/en-us/unit-price-analysis"
    assert pares["x-default"] == f"{BASE}/apu"
    assert pares["es"] == f"{BASE}/apu"
