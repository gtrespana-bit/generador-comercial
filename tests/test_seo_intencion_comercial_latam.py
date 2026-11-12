"""Intención comercial, conversión y puentes sin nuevas URLs duplicadas."""
import re

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.paises import PAISES
from app.seo_latam_comercial import ESCENARIOS
from app.services import precios_publicos as pp
from app.services.atribucion import SECCIONES_CONOCIDAS


@pytest.fixture(scope="module")
def client():
    with TestClient(app, base_url="https://cotizat.test") as cliente:
        yield cliente


@pytest.mark.parametrize("cc", ESCENARIOS)
def test_generador_comercial_usa_url_existente_y_cta_de_alta(client, cc, monkeypatch):
    monkeypatch.setenv("COTIZAT_DIAS_PRUEBA", "7")
    client.cookies.clear()
    ruta = f"/{cc.lower()}/software-presupuestos"
    respuesta = client.get(ruta)
    html = respuesta.text
    assert respuesta.status_code == 200
    assert f'<link rel="canonical" href="https://cotizat.test{ruta}">' in html
    assert f'hreflang="{PAISES[cc]["locale"]}"' in html
    assert "noindex" not in respuesta.headers.get("x-robots-tag", "")
    assert "generador de presupuestos" in re.search(r"<title>(.*?)</title>", html, re.S).group(1).lower()
    assert f"Generador de presupuestos de construcción en {PAISES[cc]['nombre']}" in html
    assert "programa para cotizar obras" in html.lower()
    assert "software para crear presupuestos de obra" in html.lower()
    assert f'/acceso?alta=1&amp;origen=software_comercial&amp;pais={cc}' in html
    assert f'href="/pago?pais={cc}"' in html
    assert 'href="/static/pdf/presupuesto-ejemplo.pdf"' in html
    assert "software_comercial" in SECCIONES_CONOCIDAS
    acceso = client.get(f"/acceso?alta=1&origen=software_comercial&pais={cc}")
    assert '<input type="hidden" name="origen" value="software_comercial">' in acceso.text
    assert re.search(rf'<option value="{cc}"\s+selected', acceso.text)


def test_prueba_apagada_no_promete_prueba_en_hub_comercial(client, monkeypatch):
    monkeypatch.setenv("COTIZAT_DIAS_PRUEBA", "0")
    client.cookies.clear()
    html = client.get("/co/software-presupuestos").text
    assert "días gratis" not in html
    assert "días de prueba" not in html
    assert 'href="/pago?pais=CO"' in html
    assert "89 US$" not in html


@pytest.mark.parametrize("cc", ["MX", "CO", "PE"])
def test_catalogo_lleva_a_la_pagina_comercial_de_su_pais(client, cc):
    indice = pp._indice(cc)
    slug_ap, slug = next(iter(indice["partidas"]))
    destino = f"/{cc.lower()}/software-presupuestos"
    for ruta in (pp.ruta_indice(cc), pp.ruta_apartado(cc, slug_ap), pp.ruta_partida(cc, slug_ap, slug)):
        client.cookies.clear()
        respuesta = client.get(ruta)
        assert respuesta.status_code == 200
        assert f'href="{destino}"' in respuesta.text
        assert "generador de presupuestos de construcción" in respuesta.text.lower()


def test_catalogo_ingles_no_recibe_puente_en_espanol(client):
    client.cookies.clear()
    html = client.get("/en-us/prices").text
    assert "De esta referencia a tu presupuesto de obra" not in html
