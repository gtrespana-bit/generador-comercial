"""Alias de país, barra final y datos estructurados por mercado.

Cubre lo que no rompe la web pero sí frena el tráfico:

- Las URLs que la gente teclea o dejó en enlaces viejos (`/colombia`,
  `/reino-unido/precios`) devolvían 404; un 404 no transfiere autoridad, un
  301 sí.
- La barra final sobrante respondía 307 (temporal), así que Google mantenía
  las dos URLs. Ahora es 301 a la canónica.
- El catálogo de cada país se declara como `Dataset` y responde las dudas
  locales (impuesto con su nombre y tipo reales) en un FAQ visible.
- `/pago` es la única página con oferta comprable: lleva `Product` con
  `AggregateOffer` a los importes reales de los planes.
"""
from __future__ import annotations

import json
import re

import pytest
from fastapi.testclient import TestClient

from app.main import app


def _cliente():
    return TestClient(app, base_url="https://cotizat.online")


@pytest.mark.parametrize(
    "alias, destino",
    [
        ("/colombia", "/co/"),
        ("/colombia/", "/co/"),
        ("/mexico", "/mx/"),
        ("/espana", "/es/"),
        ("/españa", "/es/"),
        ("/peru", "/pe/"),
        ("/republica-dominicana", "/do/"),
        ("/estados-unidos", "/en-us/"),
        ("/usa", "/en-us/"),
        ("/reino-unido", "/en-gb/"),
        ("/uk", "/en-gb/"),
        ("/canada", "/en-ca/"),
    ],
)
def test_alias_de_pais_redirige_301_a_la_canonica(alias, destino):
    with _cliente() as client:
        resp = client.get(alias, follow_redirects=False)
    assert resp.status_code == 301
    assert resp.headers["location"] == destino


def test_alias_con_seccion_conserva_la_intencion():
    with _cliente() as client:
        assert client.get("/mexico/precios", follow_redirects=False).headers[
            "location"
        ] == "/mx/precios"
        assert client.get("/estados-unidos/precios", follow_redirects=False).headers[
            "location"
        ] == "/en-us/prices"
        # Una sección que ese mercado no publica cae a su portada, nunca a un 404.
        assert client.get("/mexico/blog", follow_redirects=False).headers[
            "location"
        ] == "/mx/"


def test_el_alias_resuelve_en_un_solo_salto():
    """301 → 200: dos saltos diluyen el rastreo y se pierde el 10 % en cada uno."""
    with _cliente() as client:
        destino = client.get("/colombia", follow_redirects=False).headers["location"]
        assert client.get(destino, follow_redirects=False).status_code == 200


def test_la_barra_final_sobrante_es_301_no_307():
    with _cliente() as client:
        for ruta, canonica in (
            ("/mx/precios/", "/mx/precios"),
            ("/mx/precios/aislamiento-acustico/", "/mx/precios/aislamiento-acustico"),
        ):
            resp = client.get(ruta, follow_redirects=False)
            assert resp.status_code == 301, ruta
            assert resp.headers["location"] == canonica
        # Las raíces de mercado SÍ llevan barra: no se tocan.
        assert client.get("/co/", follow_redirects=False).status_code == 200
        assert client.get("/en-us/", follow_redirects=False).status_code == 200


def _jsonld(html: str) -> list[dict]:
    return [
        json.loads(m)
        for m in re.findall(
            r'<script type="application/ld\+json"[^>]*>(.*?)</script>', html, re.S
        )
    ]


def test_el_indice_de_precios_se_declara_como_dataset_del_pais():
    with _cliente() as client:
        html = client.get("/mx/precios").text
    dataset = next(b for b in _jsonld(html) if b.get("@type") == "Dataset")
    assert dataset["spatialCoverage"] == {"@type": "Country", "name": "México"}
    assert dataset["inLanguage"] == "es-MX"
    assert dataset["isAccessibleForFree"] is True
    assert dataset["license"].endswith("/legal/terminos")
    assert dataset["@id"].endswith("/mx/precios#dataset")
    assert {v["name"] for v in dataset["variableMeasured"]} >= {"Precio unitario"}


def test_el_faq_del_indice_usa_el_impuesto_local_de_cada_pais():
    """ITBIS en República Dominicana, IGV en Perú, IVA en México."""
    esperado = {
        "/mx/precios": ("México", "IVA", "16"),
        "/do/precios": ("República Dominicana", "ITBIS", "18"),
        "/pe/precios": ("Perú", "IGV", "18"),
        "/en-ca/prices": ("Canada", "GST/HST", "5"),
    }
    with _cliente() as client:
        for ruta, (pais, impuesto, tipo) in esperado.items():
            html = client.get(ruta).text
            faq = next(b for b in _jsonld(html) if b.get("@type") == "FAQPage")
            preguntas = [q["name"] for q in faq["mainEntity"]]
            respuestas = " ".join(q["acceptedAnswer"]["text"] for q in faq["mainEntity"])
            assert any(pais in p for p in preguntas), (ruta, preguntas)
            assert impuesto in respuestas, (ruta, impuesto)
            assert f"{tipo} %" in respuestas or f"({tipo}%)" in respuestas, ruta


def test_el_faq_del_indice_es_visible_en_la_pagina():
    """El schema sin el texto visible es markup huérfano: Google lo ignora."""
    with _cliente() as client:
        html = client.get("/mx/precios").text
    assert 'class="precios-faq"' in html
    assert html.count("<details>") >= 5


def test_pago_declara_una_oferta_comprable_real():
    with _cliente() as client:
        html = client.get("/pago").text
    producto = next(b for b in _jsonld(html) if b.get("@type") == "Product")
    oferta = producto["offers"]
    assert oferta["@type"] == "AggregateOffer"
    assert oferta["priceCurrency"] == "USD"
    assert float(oferta["lowPrice"]) == 9.99
    assert float(oferta["highPrice"]) == 89.0
    assert oferta["offerCount"] == 2
    assert all(o["url"].endswith("/pago") for o in oferta["offers"])


def test_el_catalogo_de_precios_no_finge_una_oferta_comercial():
    """Un Offer sin compra posible es markup engañoso: aquí no se emite."""
    with _cliente() as client:
        html = client.get("/mx/precios").text
    tipos = {b.get("@type") for b in _jsonld(html)}
    assert "Product" not in tipos
    assert "Offer" not in tipos
    assert "AggregateOffer" not in tipos
