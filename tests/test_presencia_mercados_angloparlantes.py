"""Presencia de los mercados de habla inglesa en la web pública.

El producto sirve 23 mercados, pero la portada pintaba ``paises[:6]``: los
seis primeros del orden de validación, que son España, Venezuela, Colombia,
México, Ecuador y Perú. Reino Unido, Estados Unidos, Australia, Irlanda y
Canadá no aparecían ni en el hero ni en la tabla de mercados, y la copy
genérica hablaba solo de «España y Latinoamérica».

Estas pruebas fijan que eso no vuelva:

- los cinco mercados anglófonos están en los accesos directos del hero;
- la tabla de la portada enlaza **los 23** mercados, en dos bloques;
- la portada genérica los nombra en el título, el H1, el cuerpo y el FAQ;
- en una página en inglés el bloque anglófono va primero;
- cada landing anglófona tiene título, descripción y cuerpo propios.
"""
from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.paises import (
    MERCADOS_ANGLOPARLANTES,
    mercados_destacados,
    mercados_por_bloque,
)

ANGLOPARLANTES = ("GB", "US", "IE", "AU", "CA")
RUTAS_EN = ("/en-gb/", "/en-us/", "/en-ie/", "/en-au/", "/en-ca/")


def _cliente():
    return TestClient(app, base_url="https://cotizat.test")


def _visible(html: str) -> str:
    """HTML sin los bloques <script> (el blob JSON lleva los dos nombres)."""
    return re.sub(r"<script\b.*?</script>", "", html, flags=re.S)


def _chips(html: str) -> list[str]:
    """Enlaces de los accesos directos del hero, en orden."""
    bloque = re.search(r'<div class="hero-mercados"[^>]*>(.*?)</div>', html, re.S)
    assert bloque, "la portada no pinta el bloque de mercados del hero"
    return re.findall(r'class="hero-mercado"[^>]*href="([^"]+)"', bloque.group(1))


def _filas(html: str) -> list[str]:
    return re.findall(r'class="mercado-fila[^"]*"[^>]*href="([^"]+)"', html)


# ---------------------------------------------------------------------------
# Orden de presentación
# ---------------------------------------------------------------------------

def test_los_cinco_angloparlantes_estan_en_los_accesos_directos():
    for idioma in ("es", "en"):
        codigos = [p["codigo"] for p in mercados_destacados(idioma)]
        for codigo in ANGLOPARLANTES:
            assert codigo in codigos, (idioma, codigo)
        assert len(codigos) == 8


def test_en_espanol_espana_abre_y_en_ingles_abre_eeuu():
    assert mercados_destacados("es")[0]["codigo"] == "ES"
    assert mercados_destacados("en")[0]["codigo"] == "US"


def test_la_tabla_de_la_portada_tiene_los_23_mercados_en_dos_bloques():
    bloques = mercados_por_bloque("es")
    assert [rotulo for rotulo, _ in bloques] == [
        "España y Latinoamérica",
        "Mercados de habla inglesa (precios en GBP, USD, AUD, CAD y EUR)",
    ]
    codigos = [p["codigo"] for _, lista in bloques for p in lista]
    assert len(codigos) == 23
    assert len(set(codigos)) == 23
    assert set(ANGLOPARLANTES) <= set(codigos)


def test_en_ingles_el_bloque_anglonfono_va_primero():
    bloques = mercados_por_bloque("en")
    assert bloques[0][0] == "English-speaking markets"
    assert [p["codigo"] for p in bloques[0][1]] == list(ANGLOPARLANTES)


def test_el_orden_de_validacion_no_cambia():
    """El orden de presentación es otro: ORDEN_SELECTOR sigue intacto."""
    from app.paises import ORDEN_SELECTOR

    assert ORDEN_SELECTOR[0] == "ES"
    assert len(ORDEN_SELECTOR) == 23
    assert MERCADOS_ANGLOPARLANTES == ("GB", "US", "IE", "AU", "CA")


# ---------------------------------------------------------------------------
# Portada genérica en español
# ---------------------------------------------------------------------------

def test_la_portada_generica_da_acceso_a_los_cinco_mercados_ingleses():
    with _cliente() as client:
        html = client.get("/").text
    chips = _chips(_visible(html))
    for ruta in ("/en-gb/", "/en-us/", "/en-ie/", "/en-au/", "/en-ca/"):
        assert ruta in chips, ruta


def test_la_portada_generica_enlaza_todos_los_mercados():
    with _cliente() as client:
        html = _visible(client.get("/").text)
    filas = _filas(html)
    assert len(filas) == 23, filas
    for ruta in ("/es/", "/mx/", "/en-gb/", "/en-us/", "/en-ie/", "/en-au/", "/en-ca/"):
        assert ruta in filas, ruta
    assert "España y Latinoamérica" in html
    assert "Mercados de habla inglesa" in html


def test_la_portada_generica_nombra_los_mercados_ingleses_en_el_copy():
    with _cliente() as client:
        html = _visible(client.get("/").text)
    titulo = re.search(r"<title>(.*?)</title>", html).group(1)
    h1 = re.sub(r"<[^>]+>", "", re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S).group(1))
    desc = re.search(r'name="description" content="([^"]*)"', html).group(1)
    assert "mercad" in titulo.lower() or "construcción" in titulo
    assert "habla inglesa" in h1
    assert "habla inglesa" in desc
    # Y el bloque de cuerpo explica cada mercado.
    for nombre in ("Reino Unido", "Estados Unidos", "Australia", "Irlanda", "Canadá"):
        assert nombre in html, nombre


def test_la_portada_generica_responde_a_si_sirve_para_uk_o_eeuu():
    with _cliente() as client:
        html = _visible(client.get("/").text)
    assert "¿CotizaT sirve también para Reino Unido o Estados Unidos?" in html
    assert "CIS" in html and "sales tax" in html.lower()


def test_la_descripcion_de_la_portada_no_se_corta_a_mitad():
    with _cliente() as client:
        html = client.get("/").text
    desc = re.search(r'name="description" content="([^"]*)"', html).group(1)
    assert len(desc) <= 160
    assert "…" not in desc
    assert "gratis" in desc or "tarjeta" in desc


# ---------------------------------------------------------------------------
# Landings en inglés
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("ruta", RUTAS_EN)
def test_en_una_landing_inglesa_el_hero_abre_con_los_cinco_angloparlantes(ruta):
    with _cliente() as client:
        chips = _chips(_visible(client.get(ruta).text))
    # Los cinco primero, y el de la propia página en cabeza.
    assert set(chips[:5]) == {f"/en-{c.lower()}/" for c in ANGLOPARLANTES}, chips
    assert chips[0] == ruta, chips


@pytest.mark.parametrize("ruta", RUTAS_EN)
def test_las_landings_inglesas_enlazan_los_23_mercados(ruta):
    with _cliente() as client:
        html = _visible(client.get(ruta).text)
    assert len(_filas(html)) == 23
    assert "English-speaking markets" in html
    assert "Spain and Latin America" in html


@pytest.mark.parametrize("ruta", RUTAS_EN)
def test_cada_landing_inglesa_tiene_titulo_y_descripcion_propios(ruta):
    with _cliente() as client:
        html = client.get(ruta).text
    titulo = re.search(r"<title>(.*?)</title>", html).group(1)
    desc = re.search(r'name="description" content="([^"]*)"', html).group(1)
    assert titulo.startswith("CotizaT:")
    assert len(desc) <= 160 and "…" not in desc


def test_las_cinco_landings_inglesas_no_comparten_titulo_ni_descripcion():
    with _cliente() as client:
        fichas = []
        for ruta in RUTAS_EN:
            html = client.get(ruta).text
            fichas.append(
                (
                    re.search(r"<title>(.*?)</title>", html).group(1),
                    re.search(r'name="description" content="([^"]*)"', html).group(1),
                    re.sub(
                        r"<[^>]+>", "", re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S).group(1)
                    ),
                )
            )
    titulos = [t for t, _, _ in fichas]
    descripciones = [d for _, d, _ in fichas]
    h1s = [h for _, _, h in fichas]
    assert len(set(titulos)) == 5, titulos
    assert len(set(descripciones)) == 5, descripciones
    assert len(set(h1s)) == 5, h1s


def test_la_portada_inglesa_menciona_los_mercados_y_no_solo_espana():
    """/en-us/ es hoy la puerta de entrada en inglés: no puede hablar solo de España."""
    with _cliente() as client:
        html = _visible(client.get("/en-us/").text)
    for nombre in ("the United Kingdom", "Australia", "Ireland", "Canada"):
        assert nombre in html, nombre


@pytest.mark.parametrize(
    "ruta,marca",
    [
        ("/en-us/", "An estimate is not a bid"),
        ("/en-au/", "prime cost"),
        ("/en-ca/", "holdback"),
        ("/en-ie/", "Relevant Contracts Tax"),
        ("/en-gb/", "CIS"),
    ],
)
def test_cada_landing_inglesa_explica_su_propia_fiscalidad(ruta, marca):
    with _cliente() as client:
        html = _visible(client.get(ruta).text)
    assert marca in html, ruta


# ---------------------------------------------------------------------------
# Rastreo
# ---------------------------------------------------------------------------

def test_el_sitemap_y_la_portada_dan_las_mismas_urls_de_mercado():
    with _cliente() as client:
        html = _visible(client.get("/").text)
        sitemap = client.get("/sitemap.xml").text
    for ruta in ("/en-gb/", "/en-us/", "/en-ie/", "/en-au/", "/en-ca/"):
        assert f'href="{ruta}"' in html, ruta
        assert f"https://cotizat.test{ruta}" in sitemap, ruta


def test_el_mapa_del_sitio_lista_los_mercados_ingleses():
    with _cliente() as client:
        html = _visible(client.get("/en/mapa-del-sitio").text)
    for ruta in RUTAS_EN:
        assert ruta in html, ruta
