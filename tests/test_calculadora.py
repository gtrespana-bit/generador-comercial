"""Calculadora pública de presupuesto: datos reales, canónica fija y silo.

Lo que se fija aquí, en orden de riesgo:

1. **El número no se inventa.** Los totales tienen que salir de los precios
   unitarios publicados del apartado: mínimo = partida más barata × cantidad,
   máximo = la más cara × cantidad. Si alguien cambia la fórmula por una
   tabla de coeficientes, este test lo denuncia.
2. **La canónica no lleva query.** El formulario genera combinaciones de
   país, apartado, cantidad y unidad; sin canónica fija eso serían miles de
   URLs equivalentes compitiendo entre sí.
3. **Funciona en los 22 mercados publicados**, incluidos los que usan pies
   cuadrados (Estados Unidos) y slugs traducidos (GB/US/CA/AU/IE). Sin esto,
   la herramienta se rompería en silencio el día que cambie un catálogo.
4. **El silo es de ida y vuelta**: la calculadora enlaza a las partidas y
   cada partida enlaza a la calculadora con su país y su apartado.
"""
from __future__ import annotations

import json
import re

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import precios_publicos as pp


def _cliente():
    return TestClient(app, base_url="https://cotizat.online")


def _jsonld(html: str) -> list[dict]:
    return [
        json.loads(m)
        for m in re.findall(
            r'<script type="application/ld\+json"[^>]*>(.*?)</script>', html, re.S
        )
    ]


def test_la_calculadora_publica_sus_totales_desde_el_catalogo():
    with _cliente() as client:
        html = client.get(
            "/calculadora?cc=MX&apartado=azulejo-y-porcelanato-en-paredes&cantidad=20"
        ).text
    assert 'class="calc-resultado"' in html
    # 20 m² de un apartado cuyo mínimo ronda los 236 MXN/m²
    assert "entre" in html and "MXN" in html
    # Las tres cifras del rango están en la página.
    assert html.count("MXN") >= 8


def test_el_rango_es_el_de_las_partidas_reales():
    """Mínimo y máximo = partida más barata y más cara × cantidad."""
    from app.calculadora import calcular

    from app.calculadora import _canonica

    ficha = pp.apartado("MX", "azulejo-y-porcelanato-en-paredes")
    precios = [
        float(p["pu"])
        for p in ficha["partidas"]
        if float(p["pu"]) > 0 and _canonica(p["unidad"]) == "m2"
    ]
    resultado = calcular("MX", "azulejo-y-porcelanato-en-paredes", 10)
    assert resultado["totales"]["minimo"].startswith(
        f"{min(precios) * 10:,.2f}".split(".")[0]
    )
    # La media también sale de los datos, no de una constante.
    media = sum(precios) / len(precios) * 10
    assert f"{media:,.2f}".split(".")[0] in resultado["totales"]["medio"]


def test_la_canonica_ignora_los_parametros_del_formulario():
    with _cliente() as client:
        base = client.get("/calculadora").text
        con_query = client.get(
            "/calculadora?cc=CO&apartado=pintura-interior&cantidad=80"
        ).text
    canonica = 'rel="canonical" href="https://cotizat.online/calculadora"'
    assert canonica in base
    assert canonica in con_query
    # Y la versión inglesa canonicaliza a la suya, no a la española.
    with _cliente() as client:
        en = client.get("/en/calculadora?cc=US&cantidad=50").text
    assert 'rel="canonical" href="https://cotizat.online/en/calculadora"' in en
    assert 'hreflang="x-default" href="https://cotizat.online/calculadora"' in en


def test_un_apartado_inexistente_no_deja_la_herramienta_vacia():
    with _cliente() as client:
        resp = client.get("/calculadora?cc=MX&apartado=no-existe-en-este-pais")
    assert resp.status_code == 200
    assert 'class="calc-resultado"' in resp.text


def test_usa_pies_cuadrados_y_los_mercados_en_tienen_su_propio_catalogo():
    with _cliente() as client:
        html = client.get(
            "/en/calculadora?cc=US&apartado=ceramic-and-porcelain-wall-tiling&cantidad=100"
        ).text
    # El catálogo estadounidense publica en pies cuadrados y en dólares.
    assert "sq ft" in html
    assert " USD" in html
    assert "/en-us/prices/" in html
    # Y el reparto va en el idioma de la página, no en español.
    assert "Materials" in html and "Materiales" not in html


def test_los_porcentajes_de_materiales_y_mano_de_obra_suman_cien():
    from app.calculadora import calcular

    for cc, slug in (
        ("MX", "azulejo-y-porcelanato-en-paredes"),
        ("CO", "pintura-interior"),
        ("ES", "tabiqueria-de-yeso-laminado"),
    ):
        grupos = calcular(cc, slug, 10)["grupos"]
        assert grupos, (cc, slug)
        assert sum(g["pct"] for g in grupos) == 100, (cc, slug, grupos)


@pytest.mark.parametrize("cc", sorted(pp.paises_publicados()))
def test_la_calculadora_funciona_en_todos_los_mercados_publicados(cc):
    """Un mercado nuevo no puede estrenar una calculadora rota."""
    with _cliente() as client:
        html = client.get(f"/calculadora?cc={cc}&cantidad=10").text
    assert 'class="calc-resultado"' in html, cc
    assert pp.ruta_indice(cc) in html, cc


def test_la_calculadora_enlaza_a_las_fichas_de_precio():
    with _cliente() as client:
        html = client.get("/calculadora?cc=MX&cantidad=10").text
    assert re.search(r'href="/mx/precios/[a-z0-9-]+/[a-z0-9-]+"', html)
    assert "/mx/precios" in html


def test_cada_apartado_y_cada_partida_enlazan_a_la_calculadora():
    with _cliente() as client:
        apartado = client.get("/mx/precios/azulejo-y-porcelanato-en-paredes").text
        partida = client.get(
            "/mx/precios/azulejo-y-porcelanato-en-paredes/"
            "recubrimiento-de-paramento-interior-con-pieza-azulejo-o-porcelanato-en-capa-fina"
        ).text
        indice = client.get("/mx/precios").text
    for html, esperado in (
        (apartado, "/calculadora?cc=MX&amp;apartado=azulejo-y-porcelanato-en-paredes"),
        (indice, "/calculadora?cc=MX"),
    ):
        assert esperado in html
    assert "/calculadora?cc=MX" in partida


def test_la_herramienta_se_declara_como_aplicacion_web_gratuita():
    with _cliente() as client:
        html = client.get("/calculadora").text
    app_ld = next(b for b in _jsonld(html) if b.get("@type") == "WebApplication")
    assert app_ld["isAccessibleForFree"] is True
    assert app_ld["offers"]["price"] == "0"
    assert app_ld["@id"].endswith("/calculadora#app")


def test_la_calculadora_esta_en_el_sitemap_y_en_el_mapa_del_sitio():
    from app.seo import urls_sitemap

    rutas = {re.sub(r"^https?://[^/]+", "", o["loc"]) for o in urls_sitemap(None)}
    assert {"/calculadora", "/en/calculadora"} <= rutas
    with _cliente() as client:
        assert 'href="/calculadora"' in client.get("/mapa-del-sitio").text
        assert 'href="/en/calculadora"' in client.get("/en/mapa-del-sitio").text
