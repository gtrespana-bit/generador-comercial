"""La portada «Impulso» en inglés es la misma página, no solo la misma paleta.

El usuario rechazó expresamente la portada clásica inglesa con navegación y
colores nuevos. Estas pruebas fijan que los cinco mercados anglófonos reciben
el diseño completo (hero, calculadora, tiempos, tour, comparativa, precios y
CTA móvil), que los textos interactivos también hablan inglés y que el contrato
de mercado/SEO no se pierde al compartir plantilla con español.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

RAIZ = Path(__file__).resolve().parents[1]
RUTAS_EN = ("/en-gb/", "/en-us/", "/en-ie/", "/en-au/", "/en-ca/")


def _cliente():
    return TestClient(app, base_url="https://cotizat.test")


def _visible(html: str) -> str:
    html = re.sub(r"<script\b.*?</script>", "", html, flags=re.S)
    html = re.sub(r"<style\b.*?</style>", "", html, flags=re.S)
    html = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    return html


@pytest.mark.parametrize("ruta", RUTAS_EN)
def test_los_cinco_mercados_ingleses_reciben_impulso_completo(ruta):
    with _cliente() as client:
        r = client.get(ruta)
    assert r.status_code == 200
    html = r.text
    assert "landing-impulso" in html
    assert "_landing_impulso.css" not in html or "lp2-hero" in html
    for componente in (
        'id="lp2-hero"',
        'id="lp2-presupuestos"',
        'id="lp2-horas"',
        'id="tiempos-obra"',
        'id="tour-stage"',
        'id="comparativa"',
        'id="precios"',
        'id="lp2-sticky"',
        "lp2-nav-mobile",
        "landing_impulso.js",
        "landing-tour.js",
        "pais_selector.js",
    ):
        assert componente in html, (ruta, componente)
    assert "Stop guessing." in html
    assert "Get paid with margin." in html
    assert "Deja de adivinar" not in _visible(html)


@pytest.mark.parametrize("ruta", RUTAS_EN)
def test_la_portada_inglesa_no_deja_espanol_visible(ruta):
    with _cliente() as client:
        html = _visible(client.get(ruta).text)
    texto = re.sub(r"<[^>]+>", " ", html)
    # La marca operativa legal se publica igual en ambos idiomas.
    texto = texto.replace("CotizaT · Presupuestos", "CotizaT")
    # Tildes/ñ fuera de nombres propios y términos de obra ya traducidos.
    malas = [
        p
        for p in re.findall(r"[A-Za-zÁÉÍÓÚÑáéíóúñü]+", texto)
        if any(c in p for c in "áéíóúñÁÉÍÓÚÑ")
        and p.lower() not in {"bogotá", "pañete", "plafón", "hormigón", "guaraní", "colón", "córdoba", "bolívar"}
    ]
    assert not malas, (ruta, sorted(set(malas)))
    for palabra in (
        "Presupuesto",
        "Presupuestos",
        "Catálogo",
        "Calculadora",
        "Iniciar sesión",
        "Ver planes",
        "Quiero",
        "Días gratis",
        "Mano de obra",
        "Duración",
        "Beneficio",
    ):
        assert palabra not in texto, (ruta, palabra)


@pytest.mark.parametrize("ruta", RUTAS_EN)
def test_ctas_y_pdf_ingleses_conservan_atribucion_y_mercado(ruta):
    with _cliente() as client:
        html = client.get(ruta).text
    codigo = ruta[4:6].upper()
    href = re.search(r'href="(/en/acceso\?[^"]+)"', html)
    assert href, ruta
    url = href.group(1).replace("&amp;", "&")
    assert "origen=landing_impulso" in url
    assert "alta=1" in url
    assert "variante=impulso" in url
    assert f"pais={codigo}" in url
    assert "presupuesto-ejemplo-en.pdf" in html
    assert 'href="/static/pdf/presupuesto-ejemplo.pdf"' not in html
    assert 'href="/en/pago"' in html


def test_el_javascript_de_impulso_es_bilingue():
    js = (RAIZ / "app/static/js/landing_impulso.js").read_text(encoding="utf-8")
    assert 'document.documentElement.lang' in js
    assert 'EN ? "en" : "es"' in js
    assert "h/month" in js
    assert "I want those hours back" in js
    assert "I want to prepare my next estimate" in js
    # El español sigue presente para la portada ES.
    assert "h/mes" in js
    assert "Quiero recuperar esas horas" in js


def test_el_selector_de_pais_no_reescribe_impulso_con_copy_legacy():
    js = (RAIZ / "app/static/js/pais_selector.js").read_text(encoding="utf-8")
    assert 'classList.contains("landing-impulso")' in js
    assert '"/en-us/"' in js
    # La rama Impulso navega al canónico sin reescribir title/meta description.
    rama = js.split('classList.contains("landing-impulso")', 1)[1].split("// Textos dinámicos por id", 1)[0]
    assert "document.title" not in rama
    assert 'meta.setAttribute' not in rama


@pytest.mark.parametrize("ruta", RUTAS_EN)
def test_la_portada_inglesa_mantiene_seis_jsonld_despues_del_main(ruta):
    with _cliente() as client:
        html = client.get(ruta).text
    assert html.count('type="application/ld+json"') == 6
    assert html.rfind("</main>") < html.find('type="application/ld+json"')


@pytest.mark.parametrize("ruta", RUTAS_EN)
def test_el_tour_ingles_ofrece_pausa_accesible(ruta):
    with _cliente() as client:
        html = client.get(ruta).text
    assert 'id="tour-pause"' in html
    assert 'data-label-pause="Pause tour"' in html
    assert 'data-label-play="Resume tour"' in html
    js = (RAIZ / "app/static/js/landing-tour.js").read_text(encoding="utf-8")
    assert "prefers-reduced-motion" in js
    assert "paused" in js
