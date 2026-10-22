"""Grafo de entidades, pares hreflang y puentes internos hacia el catálogo.

Tres defectos que no rompen una página pero sí el rastreo:

1. El sitemap solo tenía un sentido del par es/en de las guías traducidas y
   dejaba fuera las traducciones de los artículos de mercado.
2. La home y las landings de país no enlazaban a ningún catálogo de precios:
   las ~47.000 URLs programáticas colgaban del índice de cada país.
3. Los nodos JSON-LD no tenían ``@id``, así que Organization, WebSite y
   SoftwareApplication eran tres entidades distintas en cada página.
"""
from __future__ import annotations

import json
import re

from fastapi.testclient import TestClient

from app.main import app
from app.seo import urls_sitemap


def _cliente():
    return TestClient(app, base_url="https://cotizat.test")


def _rutas_sitemap() -> dict:
    """Sitemap indexado por ruta, sea cual sea el origen configurado."""
    return {
        re.sub(r"^https?://[^/]+", "", o["loc"]): o for o in urls_sitemap(None)
    }


def test_sitemap_declara_el_par_es_en_de_una_guia_de_mercado():
    sitemap = _rutas_sitemap()
    es = sitemap["/co/guia/apu-panete-colombia"]["alternates"]
    en = sitemap["/en/guia/apu-panete-colombia"]["alternates"]
    assert es == en
    idiomas = {a["hreflang"] for a in es}
    assert idiomas == {"es-CO", "en", "x-default"}
    # Una guía pilar mantiene su par es/en genérico.
    pilar = sitemap["/guia/presupuesto-de-obra"]["alternates"]
    assert {a["hreflang"] for a in pilar} == {"es", "en", "x-default"}


def test_la_landing_de_pais_enlaza_al_catalogo_de_precios():
    with _cliente() as client:
        html = client.get("/mx/").text
    assert 'class="mercados-precios"' in html
    assert 'href="/mx/precios"' in html
    assert re.search(r'href="/mx/precios/[a-z0-9-]+"', html)


def test_la_home_generica_enlaza_a_los_indices_de_catalogo():
    with _cliente() as client:
        html = client.get("/").text
    assert 'class="mercados-precios"' in html
    assert re.search(r'href="/[a-z]{2}/precios"', html)


def test_la_guia_de_mercado_enlaza_a_sus_precios():
    with _cliente() as client:
        html = client.get("/co/guia/apu-panete-colombia").text
    assert 'href="/co/precios"' in html
    assert re.search(r'href="/co/precios/[a-z0-9-]+"', html)


def test_el_grafo_jsonld_usa_ids_estables():
    with _cliente() as client:
        html = client.get("/co/").text
    bloques = [
        json.loads(m)
        for m in re.findall(
            r'<script type="application/ld\+json"[^>]*>(.*?)</script>', html, re.S
        )
    ]
    por_tipo = {}
    for bloque in bloques:
        for nodo in bloque.get("@graph", [bloque]):
            por_tipo.setdefault(nodo.get("@type"), nodo)
    assert por_tipo["Organization"]["@id"] == "https://cotizat.test/#organization"
    assert por_tipo["WebSite"]["@id"] == "https://cotizat.test/#website"
    app_node = por_tipo["SoftwareApplication"]
    assert app_node["@id"].endswith("/co/#software")
    # areaServed es un país real, no la etiqueta «Latinoamérica».
    assert app_node["areaServed"] == {"@type": "Country", "name": "Colombia"}


def test_la_404_es_html_noindex_y_con_enlaces_de_salida():
    with _cliente() as client:
        resp = client.get("/no-existe")
    assert resp.status_code == 404
    assert resp.headers["content-type"].startswith("text/html")
    assert 'name="robots" content="noindex,follow"' in resp.text
    assert 'rel="canonical"' not in resp.text
    assert 'href="/mapa-del-sitio"' in resp.text
