"""Regresiones del Speed Index de la landing.

El filmstrip de Lighthouse (móvil, simulate) estaba en blanco ~4 s y el
Speed Index salía a ~6,8 s con FCP/LCP en ~2 s. La causa no era la red
(88 KiB en 11 peticiones): el primer paint esperaba a public.css (107 KB)
y al layout de ~1.200 nodos, y un preload de Inter que la landing no usa
competía con esa hoja.

Estas aserciones bloquean volver a ese camino: CSS crítico inline, hoja
completa no bloqueante, sin fuente web en el primer viewport, JSON-LD
después del H1 y las secciones pesadas fuera del primer layout.
"""
import re

from fastapi.testclient import TestClient

from app.main import app


def _html():
    with TestClient(app) as client:
        resp = client.get("/")
    assert resp.status_code == 200
    return resp.text, resp.headers


def _fuera_de_noscript(html: str) -> str:
    return re.sub(r"<noscript>.*?</noscript>", "", html, flags=re.S)


def test_landing_pinta_el_hero_sin_esperar_public_css():
    html, headers = _html()
    visible = _fuera_de_noscript(html)

    assert "content-security-policy" in headers
    nonce = headers["content-security-policy"].split("'nonce-", 1)[1].split("'", 1)[0]
    assert f'<style nonce="{nonce}">' in html
    assert "content-visibility:auto" in html.replace(" ", "")
    assert ".landing .hero h1" in html

    assert re.search(
        r'<link rel="preload" href="[^"]*css/public\.css[^"]*" as="style">',
        visible,
    )
    assert re.search(
        r'<link rel="stylesheet" href="[^"]*css/public\.css[^"]*" media="print"',
        visible,
    )
    assert not re.search(
        r'<link rel="stylesheet" href="[^"]*css/public\.css[^"]*"(?!([^>]*media=))',
        visible,
    )
    assert not re.search(r"\son(?:load|error)\s*=", html, re.I)


def test_landing_no_descarga_inter_en_el_primer_viewport():
    html, _ = _html()
    assert "Inter-ExtraBold" not in html
    assert "fonts/Inter" not in html
    assert "@font-face" not in html


def test_jsonld_va_despues_del_h1():
    html, _ = _html()
    h1 = html.find("<h1>")
    jsonld = html.find("application/ld+json")
    assert 0 < h1 < jsonld
    assert html.find("</main>") < jsonld
    assert html.count("application/ld+json") == 5
    assert "FAQPage" in html


def test_landing_de_pais_usa_el_mismo_camino_rapido():
    with TestClient(app) as client:
        html = client.get("/co/").text
    assert "Inter-ExtraBold" not in html
    assert 'media="print"' in html
    assert "content-visibility:auto" in html.replace(" ", "")
    assert html.find("<h1>") < html.find("application/ld+json")


def test_secciones_pesadas_no_entran_en_el_primer_layout():
    css = open("app/static/css/public.css", encoding="utf-8").read()
    assert "content-visibility: auto" in css
    assert ".landing main > section" in css
    assert "content-visibility: hidden" in css
    html, _ = _html()
    assert 'class="tour-slide active"' in html
    assert 'loading="lazy"' in html
    assert "decoding=\"async\"" in html
