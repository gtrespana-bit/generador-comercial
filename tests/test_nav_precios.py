"""«Precios» en la cabecera: cada página apunta al catálogo de su mercado.

El catálogo de precios solo se alcanzaba desde la home del mercado, el pie y
alguna guía. Los 47 000 precios colgaban de un hub que casi no recibía enlaces
internos, y el rastreador llegaba por el sitemap, que es el camino más caro.

Con un elemento de navegación contextual, cada ficha de precios enlaza a su
propio índice de mercado y la cabecera deja de mandar todo el mundo al mismo
sitio: /en-gb/... va a /en-gb/prices, /do/... a /do/precios.
"""
from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers.common import ruta_precios_nav
from app.services import precios_publicos as pp

MERCADOS = sorted(pp.paises_publicados())


def _cliente() -> TestClient:
    return TestClient(app, base_url="https://cotizat.online")


def _enlace_nav(html: str) -> str | None:
    m = re.search(
        r'<a class="nav-item[^"]*" href="([^"]+)">(?:Precios|Prices)</a>', html
    )
    return m.group(1) if m else None


@pytest.mark.parametrize("cc", MERCADOS)
def test_la_home_del_mercado_enlaza_su_catalogo(cc):
    with _cliente() as cliente:
        html = cliente.get(f"/{cc.lower()}/" if cc != "US" else "/en-us/").text
    assert _enlace_nav(html) == pp.ruta_indice(cc), cc


@pytest.mark.parametrize("cc", ["MX", "US", "ES", "DO"])
def test_una_ficha_de_precios_vuelve_a_su_indice(cc):
    indice = pp._indice(cc)  # noqa: SLF001 - solo lectura
    slug_ap = sorted(indice["apartados"])[0]
    slug_p = indice["apartados"][slug_ap]["partidas"][0]["slug"]
    with _cliente() as cliente:
        html = cliente.get(pp.ruta_partida(cc, slug_ap, slug_p)).text
    assert _enlace_nav(html) == pp.ruta_indice(cc)


def test_la_raiz_y_las_rutas_genericas_en_ingles():
    with _cliente() as cliente:
        assert _enlace_nav(cliente.get("/").text) == "/mx/precios"
        assert _enlace_nav(cliente.get("/en/calculadora").text) == "/en-us/prices"
        assert _enlace_nav(cliente.get("/calculadora").text) == "/mx/precios"


def test_la_funcion_no_inventa_rutas():
    assert ruta_precios_nav("/xx/presupuestos") == ""
    assert ruta_precios_nav("/presupuestos") == "/mx/precios"
    assert ruta_precios_nav("/en-zz/prices") == ""
    assert ruta_precios_nav("") == "/mx/precios"


def test_el_enlace_es_el_mismo_en_todas_las_paginas_del_mercado():
    """Cabecera coherente: apartado, partida, mano de obra e índice."""
    indice = pp._indice("MX")  # noqa: SLF001
    slug_ap = sorted(indice["apartados"])[0]
    slug_p = indice["apartados"][slug_ap]["partidas"][0]["slug"]
    rutas = [
        "/mx/precios",
        pp.ruta_apartado("MX", slug_ap),
        pp.ruta_partida("MX", slug_ap, slug_p),
        "/mx/mano-de-obra",
    ]
    with _cliente() as cliente:
        for ruta in rutas:
            assert _enlace_nav(cliente.get(ruta).text) == "/mx/precios", ruta
