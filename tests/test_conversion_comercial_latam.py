"""Promesa comercial, prueba y país coherentes para un comprador de LATAM."""
import json
import re

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader

from app.main import app
from app.paises import PAISES
from app.seo_latam_comercial import ESCENARIOS


@pytest.fixture(scope="module")
def client():
    with TestClient(app, base_url="https://cotizat.test") as cliente:
        yield cliente


@pytest.mark.parametrize("cc", ESCENARIOS)
def test_itinerario_comercial_y_faq_visibles_y_coherentes(client, cc, monkeypatch):
    monkeypatch.setenv("COTIZAT_DIAS_PRUEBA", "14")
    client.cookies.clear()
    html = client.get(f"/{cc.lower()}/software-presupuestos").text
    assert "14 días gratis" in html
    assert "Prepara tus partidas" in html
    assert "Calcula tu propuesta" in html
    assert "Envíala en PDF" in html
    assert "PDF de muestra con datos ficticios de Venezuela en USD" in html
    assert f'href="/pago?pais={cc}"' in html
    assert 'href="/como-funciona"' in html
    assert re.search(r'<noscript><link rel="stylesheet" href="[^"]*css/public\.css', html)
    schemas = [json.loads(item) for item in re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, re.S)]
    faq = next(item for item in schemas if item.get("@type") == "FAQPage")
    preguntas = {item["name"]: item["acceptedAnswer"]["text"] for item in faq["mainEntity"]}
    for pregunta in ("¿Puedo usar mis propios precios para cotizar?", "¿Puedo empezar con una hoja de Excel?", "¿Mi cliente necesita una cuenta para recibir el presupuesto?", "¿CotizaT emite facturas fiscales?"):
        assert pregunta in html and pregunta in preguntas
        assert preguntas[pregunta] in html


@pytest.mark.parametrize("cc", ["MX", "CO", "PE", "AR", "VE"])
def test_pagina_de_planes_respeta_pais_explicito_y_no_la_cookie(client, cc, monkeypatch):
    monkeypatch.setenv("COTIZAT_DIAS_PRUEBA", "7")
    client.cookies.clear()
    client.cookies.set("cotizat_pais", "ES")
    respuesta = client.get(f"/pago?pais={cc}")
    assert respuesta.status_code == 200
    assert re.search(rf'<option value="{cc}"\s+selected', respuesta.text)
    assert f"Verás los medios habilitados para {PAISES[cc]['nombre']}" in respuesta.text
    assert f'href="/acceso?alta=1&amp;origen=planes&amp;pais={cc}"' in respuesta.text
    acceso = client.get(f"/acceso?alta=1&origen=planes&pais={cc}")
    assert re.search(rf'<option value="{cc}"\s+selected', acceso.text)
    assert 'name="origen" value="planes"' in acceso.text


def test_pdf_de_muestra_realmente_es_el_ejemplo_ficticio(client):
    respuesta = client.get("/static/pdf/presupuesto-ejemplo.pdf")
    assert respuesta.status_code == 200
    import io
    texto = " ".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(respuesta.content)).pages)
    assert "ficticios" in texto
    assert "Venezuela" in texto
    assert "USD" in texto


def test_portadas_describen_el_pdf_como_muestra(client):
    client.cookies.clear()
    es = client.get("/mx/").text
    assert "Ver un presupuesto de ejemplo antes de registrarte" in es
    assert "ejemplo ficticio de Venezuela en USD" in es
    assert "coste interno, beneficio, impuesto de tu mercado" not in es
    client.cookies.clear()
    en = client.get("/en-us/").text
    assert "See a sample estimate before you sign up" in en
    assert "fictional Venezuelan data in USD" in en
