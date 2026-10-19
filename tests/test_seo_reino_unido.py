"""SEO de Reino Unido: contenido de mercado, URLs canónicas y sitemap.

Lo que se fija aquí no es «que la página cargue», sino las decisiones que
hacen que /en-gb/ compita de verdad en Google:

- el cuerpo de la landing y de los hubs es británico y distinto del de
  /en-us/ (no la misma plantilla con el nombre del país cambiado);
- un artículo de mercado tiene una sola URL canónica y no compite consigo
  mismo (/gb/guia/x redirige a /en-gb/guia/x);
- el sitemap no anuncia redirecciones ni URLs duplicadas;
- el hreflang «en» apunta a una URL que responde 200, no a /en/, que es un
  301;
- la página no sale con X-Robots-Tag noindex.
"""
from __future__ import annotations

import json
import re

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.seo import es_indexable
from app.seo_reino_unido import ARTICULOS, ORDEN_ARTICULOS

RUTAS_ARTICULOS = [f"/en-gb/guia/{slug}" for slug in ORDEN_ARTICULOS]


def _cliente():
    return TestClient(app, base_url="https://cotizat.test")


def _tipos_jsonld(html: str) -> set[str]:
    tipos = set()
    for bloque in re.findall(
        r'<script type="application/ld\+json"[^>]*>(.*?)</script>', html, re.S
    ):
        try:
            tipos.add(json.loads(bloque).get("@type"))
        except Exception:
            tipos.add("<<no válido>>")
    return tipos


# ---------------------------------------------------------------------------
# Landing /en-gb/
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "ruta,marca",
    [
        ("/en-gb/", "A UK quote is not a Spanish budget"),
        ("/en-us/", "An estimate is not a bid"),
        ("/en-au/", "prime cost"),
        ("/en-ca/", "holdback"),
        ("/en-ie/", "Relevant Contracts Tax"),
    ],
)
def test_cada_mercado_anglonfono_tiene_cuerpo_propio(ruta, marca):
    """/en-gb/ y /en-us/ no pueden ser la misma página con otro país.

    Las cinco landings anglófonas compartían plantilla y solo cambiaban el
    nombre, la moneda y el impuesto: para Google eran duplicados y para un
    contratista, un folleto genérico.
    """
    with _cliente() as client:
        html = client.get(ruta).text
    assert 'id="for-your-market"' in html, ruta
    assert marca in html, ruta


def test_los_cuerpos_de_los_cinco_mercados_ingleses_no_se_repiten():
    from app.seo_mercados_en import CUERPO as CUERPO_EN
    from app.seo_reino_unido import LANDING_CUERPO as CUERPO_GB

    cuerpos = {"GB": CUERPO_GB, **CUERPO_EN}
    assert set(cuerpos) == {"GB", "US", "AU", "CA", "IE"}
    primeros_titulos = [v[0][0] for v in cuerpos.values()]
    assert len(set(primeros_titulos)) == 5, primeros_titulos
    for codigo, cuerpo in cuerpos.items():
        assert len(cuerpo) >= 4, codigo


def test_la_landing_britanica_habla_de_cis_y_del_vocabulario_de_obra():
    with _cliente() as client:
        gb = client.get("/en-gb/").text
    assert "CIS" in gb and "reverse charge" in gb.lower()
    assert "skirting" in gb.lower()
    assert "A UK quote is not a Spanish budget" in gb


def test_la_descripcion_cabe_en_el_snippet():
    with _cliente() as client:
        html = client.get("/en-gb/").text
    desc = re.search(r'name="description" content="([^"]*)"', html).group(1)
    assert 90 <= len(desc) <= 160, len(desc)


def test_la_faq_britanica_esta_visible_y_en_el_schema():
    with _cliente() as client:
        html = client.get("/en-gb/").text
    assert "FAQPage" in _tipos_jsonld(html)
    assert "Does CotizaT apply CIS deductions on a quote?" in html
    assert "Can I quote a VAT domestic reverse charge job?" in html
    # Y la nota fiscal sigue explicando que el IVA depende de la obra.
    assert "VAT on construction in the United Kingdom depends on the work" in html


def test_el_schema_nombra_el_pais_en_ingles():
    """«Reino Unido» dentro de un schema en-GB delata el registro español."""
    with _cliente() as client:
        html = client.get("/en-gb/").text
    assert '"@type": "Country", "name": "the United Kingdom"' in html
    assert '"name": "Reino Unido"' not in html


def test_la_landing_declara_su_locale_en_el_schema():
    with _cliente() as client:
        html = client.get("/en-gb/").text
    assert '"inLanguage": "en-GB"' in html


# ---------------------------------------------------------------------------
# Hubs /en-gb/<tema>
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "ruta,fragmento",
    [
        ("/en-gb/software-presupuestos", "preliminaries"),
        ("/en-gb/apu", "Plant, waste and making good"),
        ("/en-gb/remodelacion", "strip-out"),
    ],
)
def test_los_hubs_britanicos_tienen_bloques_de_mercado(ruta, fragmento):
    with _cliente() as client:
        html = client.get(ruta).text
    assert fragmento in html
    assert re.search(r'<html lang="en-GB"', html)


def test_un_hub_ingles_no_mezcla_el_cuerpo_en_espanol():
    """Regresión: la plantilla inglesa pintaba la ficha española debajo."""
    with _cliente() as client:
        html = client.get("/en-gb/apu").text
    visible = re.sub(r"<script\b.*?</script>", "", html, flags=re.S)
    for texto_es in ("Qué es un APU", "Por qué importa", "¿CotizaT sirve"):
        assert texto_es not in visible


def test_los_hubs_listan_los_paises_en_ingles():
    with _cliente() as client:
        html = client.get("/en-gb/apu").text
    visible = re.sub(r"<script\b.*?</script>", "", html, flags=re.S)
    assert "the United Kingdom" in visible
    assert "España" not in visible
    assert "Estados Unidos" not in visible


# ---------------------------------------------------------------------------
# Artículos de cola larga
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("ruta", RUTAS_ARTICULOS)
def test_cada_articulo_britanico_tiene_url_canonica_propia(ruta):
    with _cliente() as client:
        resp = client.get(ruta)
    assert resp.status_code == 200, ruta
    assert resp.headers.get("x-robots-tag") is None, ruta
    html = resp.text
    assert f'rel="canonical" href="https://cotizat.test{ruta}"' in html
    assert re.search(r'<html lang="en-GB"', html)
    tipos = _tipos_jsonld(html)
    assert {"Article", "FAQPage", "BreadcrumbList"} <= tipos
    # Un artículo de fiscalidad no es un tutorial: no se anuncia como HowTo.
    assert "HowTo" not in tipos


@pytest.mark.parametrize("slug", ORDEN_ARTICULOS)
def test_los_articulos_declaran_su_hreflang_de_mercado(slug):
    with _cliente() as client:
        html = client.get(f"/en-gb/guia/{slug}").text
    href = f'https://cotizat.test/en-gb/guia/{slug}'
    assert f'hreflang="en-GB" href="{href}"' in html
    assert f'hreflang="x-default" href="{href}"' in html
    # No se anuncia una versión en español que no existe.
    assert f'hreflang="es" href="https://cotizat.test/guia/{slug}"' not in html


@pytest.mark.parametrize("slug", ORDEN_ARTICULOS)
def test_la_descripcion_de_cada_articulo_cabe_en_el_snippet(slug):
    with _cliente() as client:
        html = client.get(f"/en-gb/guia/{slug}").text
    desc = re.search(r'name="description" content="([^"]*)"', html).group(1)
    assert 80 <= len(desc) <= 160, (slug, len(desc))
    assert "…" not in desc, slug


def test_la_url_sin_prefijo_redirige_a_la_canonica():
    with _cliente() as client:
        slug = ORDEN_ARTICULOS[0]
        resp = client.get(f"/gb/guia/{slug}", follow_redirects=False)
    assert resp.status_code == 301
    assert resp.headers["location"] == f"/en-gb/guia/{slug}"


def test_un_articulo_inexistente_es_404_y_no_esta_en_el_sitemap():
    with _cliente() as client:
        resp = client.get("/en-gb/guia/no-existe")
        sitemap = client.get("/sitemap.xml").text
    assert resp.status_code == 404
    assert "no-existe" not in sitemap


def test_los_articulos_britanicos_solo_existen_en_ingles():
    for slug in ORDEN_ARTICULOS:
        with _cliente() as client:
            resp = client.get(f"/guia/{slug}")
        assert resp.status_code == 404, slug


def test_la_landing_enlaza_los_articulos_del_mercado():
    with _cliente() as client:
        html = client.get("/en-gb/").text
    for slug in ORDEN_ARTICULOS:
        assert f"/en-gb/guia/{slug}" in html


def test_los_articulos_se_enlazan_entre_si():
    with _cliente() as client:
        html = client.get("/en-gb/guia/cis-deduction-subcontractors").text
    assert "/en-gb/guia/vat-domestic-reverse-charge-construction" in html
    assert "/en-gb/guia/construction-quote-template-uk" in html


# ---------------------------------------------------------------------------
# Indexabilidad y sitemap
# ---------------------------------------------------------------------------

def test_las_urls_britanicas_son_indexables():
    for ruta in ("/en-gb/", "/en-gb/apu", *RUTAS_ARTICULOS):
        assert es_indexable(ruta), ruta


def test_el_sitemap_no_anuncia_redirecciones():
    """Un sitemap con /gb/ y /en/ hace que Search Console las marque."""
    with _cliente() as client:
        locs = re.findall(r"<loc>(.*?)</loc>", client.get("/sitemap.xml").text)
    for loc in locs:
        assert not re.search(r"/(gb|us|au|ca|ie)/$", loc), loc
        assert not loc.endswith("/en/"), loc
    assert "https://cotizat.test/en-gb/" in locs
    assert "https://cotizat.test/en-us/" in locs


def test_el_sitemap_incluye_los_articulos_britanicos():
    with _cliente() as client:
        texto = client.get("/sitemap.xml").text
    for slug in ORDEN_ARTICULOS:
        assert f"https://cotizat.test/en-gb/guia/{slug}" in texto


def test_el_sitemap_no_tiene_urls_repetidas():
    with _cliente() as client:
        locs = re.findall(r"<loc>(.*?)</loc>", client.get("/sitemap.xml").text)
    assert len(locs) == len(set(locs))


def test_el_hreflang_en_apunta_a_una_url_que_no_redirige():
    with _cliente() as client:
        html = client.get("/en-gb/").text
        destino = re.search(
            r'hreflang="en" href="([^"]+)"', html
        ).group(1)
        assert destino == "https://cotizat.test/en-us/"
        resp = client.get("/en-us/", follow_redirects=False)
    assert resp.status_code == 200


def test_cada_url_britanica_del_sitemap_responde_200():
    with _cliente() as client:
        locs = re.findall(r"<loc>(.*?)</loc>", client.get("/sitemap.xml").text)
        britanicas = [u for u in locs if "/en-gb" in u]
        assert len(britanicas) >= 4
        for url in britanicas:
            ruta = url.replace("https://cotizat.test", "")
            resp = client.get(ruta, follow_redirects=False)
            assert resp.status_code == 200, ruta


def test_el_texto_britanico_usa_su_vocabulario_y_no_el_estadounidense():
    """El cuerpo de /en-gb/ habla de obra británica, no de EE. UU."""
    from app.seo_reino_unido import LANDING_CUERPO

    texto = " ".join(
        [titulo + " " + " ".join(pars) for titulo, pars in LANDING_CUERPO]
    ).lower()
    for termino in (
        "skirting",
        "worktop",
        "plasterboard",
        "consumer unit",
        "call point",
        "cis",
        "reverse charge",
    ):
        assert termino in texto, termino
    # Los términos estadounidenses solo pueden aparecer citados una vez,
    # justo en el párrafo que explica cuáles no se usan («reads worktop, not
    # countertop»). Más de una aparición significa que se colaron como uso.
    for termino_us in ("countertop", "drywall", "faucet", "pull station"):
        assert texto.count(termino_us) <= 1, termino_us
