"""URLs en inglés: slugs ingleses y consolidación del prefijo interno.

Dos defectos que se tapaban entre sí y que costaban tráfico en los cinco
mercados de habla inglesa (los de mayor valor del sitio):

1. **Slug español en página inglesa.** `/en-us/apu`, `/en-gb/remodelacion`,
   `/en/software-presupuestos`: el slug se ve en el resultado de búsqueda y en
   cada enlace compartido. Una página que compite por «unit price analysis» no
   puede llamarse «apu».

2. **Prefijo interno indexable.** El middleware reescribe `/en-us/apu` a
   `/us/apu` para enrutar, pero `/us/apu` respondía 200 con canonical propia:
   el mismo documento en dos URL, las dos indexables, sin hreflang que las
   uniera. Es contenido duplicado generado por el propio servidor.

Lo que se comprueba aquí:

- Las URL nuevas responden 200 con canonical propia.
- Las antiguas responden **301** a la nueva (nunca 200: un duplicado).
- El prefijo interno (`/us/...`, `/gb/...`, …) responde 301 a la URL pública.
- Los mercados de habla española no cambian de URL.
- El sitemap, el pie, el mapa del sitio y el conmutador de idioma apuntan
  siempre a la URL canónica, no a una redirección.
"""
from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.paises import PAISES
from app.seo import (
    TEMAS,
    TEMAS_EN,
    es_indexable,
    ruta_en,
    ruta_mercado,
    slug_tema,
    tema_desde_slug,
)

MERCADOS_EN = tuple(sorted(cc for cc, p in PAISES.items() if p.get("idioma") == "en"))
MERCADOS_ES = tuple(sorted(cc for cc, p in PAISES.items() if p.get("idioma") != "en"))


def _cliente() -> TestClient:
    return TestClient(app, base_url="https://cotizat.online")


# ── El mapa de slugs ────────────────────────────────────────────────────────


def test_cada_tema_tiene_slug_ingles_y_vuelta_atras():
    for tema in TEMAS:
        en = slug_tema(tema, "en")
        assert en != tema, tema
        assert re.fullmatch(r"[a-z]+(-[a-z]+)*", en), en
        assert tema_desde_slug(en) == tema
        assert tema_desde_slug(tema) == tema
        assert slug_tema(tema, "es") == tema


def test_los_slugs_ingleses_no_se_pisan_con_nada():
    assert len(set(TEMAS_EN.values())) == len(TEMAS_EN)
    assert not (set(TEMAS_EN.values()) & set(TEMAS))


# ── URL canónica ────────────────────────────────────────────────────────────


def test_la_ruta_del_mercado_ingles_usa_el_slug_ingles():
    for cc in MERCADOS_EN:
        for tema in TEMAS:
            ruta = ruta_mercado(cc, tema)
            assert ruta == f"/en-{cc.lower()}/{TEMAS_EN[tema]}", ruta


def test_los_mercados_de_habla_espanola_conservan_su_url():
    for cc in MERCADOS_ES:
        for tema in TEMAS:
            assert ruta_mercado(cc, tema) == f"/{cc.lower()}/{tema}"


def test_la_ruta_generica_en_ingles():
    assert ruta_en("", "apu") == "/en/unit-price-analysis"
    assert ruta_en("US", "remodelacion") == "/en-us/remodeling"


# ── La página ───────────────────────────────────────────────────────────────


@pytest.mark.parametrize("cc", MERCADOS_EN)
@pytest.mark.parametrize("tema", TEMAS)
def test_cada_hub_ingles_responde_con_su_canonica(cc, tema):
    ruta = ruta_mercado(cc, tema)
    with _cliente() as cliente:
        respuesta = cliente.get(ruta)
    assert respuesta.status_code == 200, ruta
    assert f'rel="canonical" href="https://cotizat.online{ruta}"' in respuesta.text
    assert "noindex" not in (respuesta.headers.get("x-robots-tag") or "")
    assert 'lang="en' in respuesta.text


@pytest.mark.parametrize("tema", TEMAS)
def test_el_hub_generico_en_ingles(tema):
    ruta = ruta_en("", tema)
    with _cliente() as cliente:
        respuesta = cliente.get(ruta)
    assert respuesta.status_code == 200
    assert f'rel="canonical" href="https://cotizat.online{ruta}"' in respuesta.text


@pytest.mark.parametrize("tema", TEMAS)
def test_el_slug_espanol_en_un_mercado_ingles_redirige_301(tema):
    with _cliente() as cliente:
        for cc in MERCADOS_EN:
            vieja = f"/en-{cc.lower()}/{tema}"
            respuesta = cliente.get(vieja, follow_redirects=False)
            assert respuesta.status_code == 301, vieja
            assert respuesta.headers["location"] == ruta_mercado(cc, tema)
        # Y el genérico inglés.
        respuesta = cliente.get(f"/en/{tema}", follow_redirects=False)
        assert respuesta.status_code == 301
        assert respuesta.headers["location"] == ruta_en("", tema)


def test_el_slug_ingles_en_un_mercado_espanol_redirige_al_espanol():
    """/mx/remodeling no es una URL: la canónica de ese mercado es /mx/remodelacion."""
    with _cliente() as cliente:
        for tema, slug in TEMAS_EN.items():
            respuesta = cliente.get(f"/mx/{slug}", follow_redirects=False)
            assert respuesta.status_code == 301, slug
            assert respuesta.headers["location"] == f"/mx/{tema}"


def test_los_mercados_espanoles_siguen_igual():
    with _cliente() as cliente:
        for tema in TEMAS:
            respuesta = cliente.get(f"/mx/{tema}", follow_redirects=False)
            assert respuesta.status_code == 200, tema


# ── El prefijo interno ──────────────────────────────────────────────────────


@pytest.mark.parametrize("cc", MERCADOS_EN)
def test_el_prefijo_interno_no_es_una_url_publica(cc):
    """`/us/apu` servía el mismo HTML que `/en-us/apu`, con canonical propia."""
    corto = cc.lower()
    with _cliente() as cliente:
        for resto in ("", "/", "/apu", "/remodelacion", "/software-presupuestos"):
            respuesta = cliente.get(f"/{corto}{resto}", follow_redirects=False)
            assert respuesta.status_code == 301, (corto, resto)
            assert respuesta.headers["location"].startswith(f"/en-{corto}"), resto
            assert "/en-en-" not in respuesta.headers["location"]


def test_el_salto_del_prefijo_interno_ya_traduce_el_slug():
    """Un solo 301: /us/apu -> /en-us/unit-price-analysis, no dos saltos."""
    with _cliente() as cliente:
        respuesta = cliente.get("/us/apu", follow_redirects=False)
        assert respuesta.headers["location"] == "/en-us/unit-price-analysis"
        # Y el destino final responde 200 sin más redirecciones.
        assert cliente.get(respuesta.headers["location"], follow_redirects=False).status_code == 200


def test_el_prefijo_interno_de_un_mercado_espanol_no_se_toca():
    """`/mx/` es la URL pública de México: no se puede confundir con un prefijo interno."""
    with _cliente() as cliente:
        assert cliente.get("/mx/", follow_redirects=False).status_code == 200
        assert cliente.get("/co/apu", follow_redirects=False).status_code == 200


def test_el_salto_conserva_la_query():
    with _cliente() as cliente:
        respuesta = cliente.get("/us/apu?utm_source=bing", follow_redirects=False)
        assert respuesta.headers["location"].endswith("?utm_source=bing")


# ── Enlaces internos, sitemap e indexabilidad ───────────────────────────────


def test_el_sitemap_anuncia_las_urls_nuevas_y_ninguna_vieja():
    from app.seo import urls_sitemap

    urls = [entrada["loc"] for entrada in urls_sitemap()]
    for cc in MERCADOS_EN:
        for tema in TEMAS:
            nueva = "https://cotizat.online" + ruta_mercado(cc, tema)
            assert nueva in urls, nueva
            vieja = f"https://cotizat.online/en-{cc.lower()}/{tema}"
            assert vieja not in urls, vieja
    for tema in TEMAS:
        assert "https://cotizat.online" + ruta_en("", tema) in urls
        assert f"https://cotizat.online/en/{tema}" not in urls


def test_todas_las_urls_de_tema_del_sitemap_responden_200():
    from app.seo import urls_sitemap

    urls = [
        e["loc"]
        for e in urls_sitemap()
        if any(s in e["loc"] for s in (*TEMAS_EN.values(), "restauracion"))
    ]
    assert urls
    with _cliente() as cliente:
        for url in urls:
            ruta = url.replace("https://cotizat.online", "")
            assert cliente.get(ruta, follow_redirects=False).status_code == 200, ruta


@pytest.mark.parametrize("cc", ["US", "GB", "AU", "CA", "IE"])
def test_los_enlaces_internos_ingleses_no_pasan_por_una_redireccion(cc):
    """Un enlace interno a un 301 gasta un salto en cada rastreo."""
    from app.seo import urls_sitemap

    enlaces = [
        e["loc"].replace("https://cotizat.online", "")
        for e in urls_sitemap()
        if e["loc"].startswith("https://cotizat.online/en-")
    ][:8]
    with _cliente() as cliente:
        for ruta in enlaces:
            html = cliente.get(ruta).text
            viejas = [
                f"/en-{cc.lower()}/{tema}"
                for tema in TEMAS
                if f'href="/en-{cc.lower()}/{tema}"' in html
            ]
            assert not viejas, (ruta, viejas)


def test_el_pie_ingles_apunta_a_las_urls_nuevas():
    with _cliente() as cliente:
        html = cliente.get("/en-us/").text
    for tema in TEMAS:
        assert f'href="/en/{tema}"' not in html
    for slug in TEMAS_EN.values():
        assert f'href="/en/{slug}"' in html


def test_el_conmutador_de_idioma_no_manda_a_una_redireccion():
    from app.i18n import ruta_en_idioma

    assert ruta_en_idioma("/apu", "en") == "/en/unit-price-analysis"
    assert ruta_en_idioma("/mx/remodelacion", "en") == "/en-mx/remodeling"
    # Y de vuelta al español.
    assert ruta_en_idioma("/en/unit-price-analysis", "es") == "/apu"
    assert ruta_en_idioma("/en-mx/remodeling", "es") == "/mx/remodelacion"


def test_las_urls_nuevas_son_indexables():
    for cc in MERCADOS_EN:
        for tema in TEMAS:
            assert es_indexable(ruta_mercado(cc, tema)), (cc, tema)
    for tema in TEMAS:
        assert es_indexable(ruta_en("", tema)), tema
    # Y el prefijo interno no cuenta como URL pública.
    assert not es_indexable("/us/apu")


def test_las_urls_nuevas_se_cachean_en_el_cdn():
    from app.cache_publico import es_ruta_publica_cacheable

    for cc in MERCADOS_EN:
        for tema in TEMAS:
            assert es_ruta_publica_cacheable(ruta_mercado(cc, tema)), (cc, tema)
    for tema in TEMAS:
        assert es_ruta_publica_cacheable(ruta_en("", tema)), tema
