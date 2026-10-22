"""El espejo en inglés de los mercados hispanos.

`/en-mx/apu` existe por una razón concreta: el conmutador promete «ver esta
página en inglés» y la superficie pública ignora la cookie para poder
cachearse, así que la única forma de servir la misma página en inglés es una
URL propia. Pero no es una página de mercado: nadie la enlaza, no está en el
sitemap y no tiene hreflang propio.

Hasta ahora salía con `index,follow` y canónica a sí misma. Google la
encontraba por el conmutador y la indexaba: el mismo contenido que `/mx/apu`,
en otro idioma, sin variante declarada. Con 17 mercados hispanos son 17
duplicados por cada hub.

Decisión: la URL se queda (utilidad), pero sale con `noindex, follow` —en la
meta y en la cabecera, que es la que manda si se contradicen—, sin hreflang y
fuera del sitemap. Los mercados de habla inglesa no cambian: ahí el inglés es
el idioma del país y su URL es la canónica.
"""
from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from app.i18n import ruta_en_idioma
from app.main import app
from app.paises import PAISES
from app.seo import (
    MERCADOS_HISPANOS,
    TEMAS,
    es_espejo_de_idioma,
    es_indexable,
    ruta_mercado,
    slug_tema,
)

MERCADOS_EN = tuple(sorted(cc for cc, p in PAISES.items() if p.get("idioma") == "en"))


def _cliente() -> TestClient:
    return TestClient(app, base_url="https://cotizat.online")


def _robots(html: str) -> str:
    m = re.search(r'name="robots" content="([^"]+)"', html)
    return m.group(1) if m else ""


def _alternates(html: str) -> list[str]:
    return re.findall(r'<link rel="alternate" hreflang="([^"]+)"', html)


# ── La regla ────────────────────────────────────────────────────────────────


def test_los_mercados_hispanos_son_los_que_no_hablan_ingles():
    assert MERCADOS_HISPANOS
    assert not (MERCADOS_HISPANOS & set(MERCADOS_EN))
    assert MERCADOS_HISPANOS | set(MERCADOS_EN) == set(PAISES)


@pytest.mark.parametrize("cc", sorted(MERCADOS_HISPANOS))
def test_el_prefijo_en_de_un_mercado_hispano_es_un_espejo(cc):
    corto = cc.lower()
    assert es_espejo_de_idioma(f"/en-{corto}")
    assert es_espejo_de_idioma(f"/en-{corto}/")
    for tema in TEMAS:
        assert es_espejo_de_idioma(f"/en-{corto}/{tema}")


@pytest.mark.parametrize("cc", MERCADOS_EN)
def test_los_mercados_ingleses_no_son_un_espejo(cc):
    corto = cc.lower()
    assert not es_espejo_de_idioma(f"/en-{corto}/")
    for tema in TEMAS:
        assert not es_espejo_de_idioma(f"/en-{corto}/{tema}")


def test_la_home_generica_en_ingles_no_es_un_espejo():
    assert not es_espejo_de_idioma("/en/")
    assert not es_espejo_de_idioma("/en/remodeling")


# ── La página ───────────────────────────────────────────────────────────────


@pytest.mark.parametrize("cc", ["MX", "CO", "ES", "AR"])
@pytest.mark.parametrize("tema", TEMAS)
def test_el_espejo_sirve_la_pagina_pero_no_se_indexa(cc, tema):
    ruta = f"/en-{cc.lower()}/{slug_tema(tema, 'en')}"
    with _cliente() as cliente:
        respuesta = cliente.get(ruta, follow_redirects=False)
    assert respuesta.status_code == 200, ruta
    # Sigue siendo útil: se ve y se puede usar.
    assert 'lang="en' in respuesta.text
    # Pero no compite con la página del mercado.
    assert _robots(respuesta.text).startswith("noindex"), ruta
    assert "follow" in _robots(respuesta.text)
    cabecera = respuesta.headers.get("x-robots-tag") or ""
    assert "noindex" in cabecera
    # ``follow``, no ``nofollow``: sus enlaces al mercado sí deben contar.
    assert "nofollow" not in cabecera


def test_la_meta_y_la_cabecera_dicen_lo_mismo():
    """Si se contradicen, Google aplica la más restrictiva y nadie se enteró."""
    with _cliente() as cliente:
        respuesta = cliente.get("/en-mx/unit-price-analysis")
    cabecera = respuesta.headers.get("x-robots-tag") or ""
    assert _robots(respuesta.text).startswith("noindex")
    assert "noindex" in cabecera


@pytest.mark.parametrize("tema", TEMAS)
def test_el_espejo_no_declara_hreflang(tema):
    with _cliente() as cliente:
        html = cliente.get(f"/en-mx/{slug_tema(tema, 'en')}").text
    assert _alternates(html) == []


@pytest.mark.parametrize("tema", TEMAS)
def test_el_slug_espanol_en_el_espejo_redirige_al_ingles(tema):
    """La URL del espejo también lleva el slug inglés, igual que el resto de /en-xx/."""
    with _cliente() as cliente:
        respuesta = cliente.get(f"/en-mx/{tema}", follow_redirects=False)
    assert respuesta.status_code == 301
    assert respuesta.headers["location"] == f"/en-mx/{slug_tema(tema, 'en')}"


def test_el_espejo_no_esta_en_el_sitemap_ni_cuenta_como_indexable():
    from app.seo import urls_sitemap

    urls = [e["loc"] for e in urls_sitemap()]
    for cc in MERCADOS_HISPANOS:
        assert not [u for u in urls if f"/en-{cc.lower()}/" in u], cc
        assert not [u for u in urls if u.endswith(f"/en-{cc.lower()}")], cc
        assert not es_indexable(f"/en-{cc.lower()}/apu")


@pytest.mark.parametrize("cc", ["MX", "CO", "ES"])
def test_la_pagina_del_mercado_no_cambia(cc):
    ruta = ruta_mercado(cc, "apu")
    with _cliente() as cliente:
        respuesta = cliente.get(ruta, follow_redirects=False)
    assert respuesta.status_code == 200
    assert _robots(respuesta.text).startswith("index")
    assert f'rel="canonical" href="https://cotizat.online{ruta}"' in respuesta.text
    assert respuesta.headers.get("x-robots-tag") is None


@pytest.mark.parametrize("cc", MERCADOS_EN)
def test_los_mercados_ingleses_siguen_indexandose(cc):
    ruta = ruta_mercado(cc, "apu")
    with _cliente() as cliente:
        respuesta = cliente.get(ruta, follow_redirects=False)
    assert _robots(respuesta.text).startswith("index")
    assert respuesta.headers.get("x-robots-tag") is None
    assert _alternates(respuesta.text)


# ── El conmutador ───────────────────────────────────────────────────────────


def test_el_conmutador_traduce_el_slug_del_hub():
    assert ruta_en_idioma("/apu", "en") == "/en/unit-price-analysis"
    assert ruta_en_idioma("/en/unit-price-analysis", "es") == "/apu"
    assert ruta_en_idioma("/mx/remodelacion", "en") == "/en-mx/remodeling"
    assert ruta_en_idioma("/en-mx/remodeling", "es") == "/mx/remodelacion"


def test_el_conmutador_a_espanol_desde_un_mercado_ingles_no_vuelve_al_ingles():
    """Antes devolvía /us/apu, que ahora es un 301 al inglés: el botón no hacía nada."""
    assert ruta_en_idioma("/us/unit-price-analysis", "es") == "/apu"
    assert ruta_en_idioma("/gb/remodelacion", "es") == "/remodelacion"
    assert ruta_en_idioma("/us/", "es") == "/"


def test_el_conmutador_lleva_a_una_pagina_que_existe():
    with _cliente() as cliente:
        destino = cliente.get(
            "/idioma/es?destino=/us/unit-price-analysis", follow_redirects=False
        ).headers["location"]
        assert destino == "/apu"
        respuesta = cliente.get(destino, follow_redirects=False)
    assert respuesta.status_code == 200
    assert re.search(r'<html[^>]*lang="es', respuesta.text)


def test_el_conmutador_a_ingles_desde_un_mercado_hispano_da_ingles():
    with _cliente() as cliente:
        destino = cliente.get(
            "/idioma/en?destino=/mx/unit-price-analysis", follow_redirects=False
        ).headers["location"]
        assert destino == "/en-mx/unit-price-analysis"
        respuesta = cliente.get(destino, follow_redirects=False)
    assert respuesta.status_code == 200
    assert re.search(r'<html[^>]*lang="en', respuesta.text)


def test_el_conmutador_no_es_un_open_redirect():
    with _cliente() as cliente:
        destino = cliente.get(
            "/idioma/en?destino=//malo.com/x", follow_redirects=False
        ).headers["location"]
    assert "malo.com" not in destino
