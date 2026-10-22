"""Grafo de afinidad entre apartados: obras que van juntas, sin islas.

El sitio tenía 16 capítulos por país y los enlaces internos de cada apartado
no salían de su propio capítulo. Resultado: la autoridad se quedaba repartida
en 16 islas de ~180 apartados y ninguna conectaba «impermeabilizar» con
«alicatar», que es como se piensa una obra de verdad.

Lo que se comprueba aquí:

- Cada apartado enlaza a apartados de **otros** capítulos (nunca al suyo).
- Los capítulos afines existen en los 22 mercados publicados.
- La selección es determinista (dos llamadas iguales dan lo mismo) y está
  repartida (apartados hermanos no apuntan todos a los mismos tres destinos).
- Los enlaces responden 200: un grafo interno con 404 es peor que no tenerlo.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.seo_precios import _AFINIDAD_CAPITULOS, apartados_relacionados
from app.services import precios_publicos as pp


def _cliente():
    return TestClient(app, base_url="https://cotizat.online")


def _codigos_capitulo(cc: str) -> list[str]:
    return [c["codigo"] for c in (pp.resumen(cc) or {}).get("capitulos") or []]


@pytest.mark.parametrize("cc", sorted(pp.paises_publicados()))
def test_los_capitulos_afines_existen_en_todos_los_mercados(cc):
    """Un capítulo afín que no existe en el país dejaría enlaces vacíos."""
    codigos = set(_codigos_capitulo(cc))
    for origen, afines in _AFINIDAD_CAPITULOS.items():
        if origen not in codigos:
            continue
        assert codigos & set(afines), (cc, origen, afines)


@pytest.mark.parametrize("cc", ["MX", "CO", "ES", "US", "GB", "DO"])
def test_cada_apartado_enlaza_fuera_de_su_capitulo(cc):
    resumen = pp.resumen(cc)
    vistos = 0
    for capitulo in resumen["capitulos"]:
        for ap in capitulo["apartados"]:
            relacionadas = apartados_relacionados(cc, ap["slug"])
            assert relacionadas, (cc, ap["slug"])
            vistos += 1
            for relacionada in relacionadas:
                assert relacionada["slug"] != ap["slug"]
                assert relacionada["capitulo"] != capitulo["nombre"], (
                    cc,
                    ap["slug"],
                    relacionada,
                )
            if vistos >= 40:
                return


def test_la_seleccion_es_determinista():
    primera = apartados_relacionados("MX", "impermeabilizacion-de-areas-humedas")
    segunda = apartados_relacionados("MX", "impermeabilizacion-de-areas-humedas")
    assert primera == segunda


def test_reparte_enlaces_entre_apartados_hermanos():
    """Dos apartados del mismo capítulo no deben apuntar a los mismos tres."""
    destinos = set()
    for slug in (
        "azulejo-y-porcelanato-en-paredes",
        "pisos-ceramicos-y-porcelanato",
        "pintura-interior",
        "pintura-exterior",
    ):
        destinos.add(tuple(r["slug"] for r in apartados_relacionados("MX", slug)))
    assert len(destinos) >= 3, destinos


def test_los_enlaces_del_grafo_responden_200():
    with _cliente() as client:
        for cc, slug in (
            ("MX", "impermeabilizacion-de-areas-humedas"),
            ("CO", "pintura-interior"),
            ("US", "ceramic-and-porcelain-wall-tiling"),
        ):
            for relacionada in apartados_relacionados(cc, slug):
                assert client.get(relacionada["ruta"]).status_code == 200, relacionada


def test_la_pagina_muestra_el_bloque_y_sus_enlaces():
    with _cliente() as client:
        html = client.get("/mx/precios/impermeabilizacion-de-areas-humedas").text
    assert "Obras que van con esta" in html
    for relacionada in apartados_relacionados("MX", "impermeabilizacion-de-areas-humedas"):
        assert relacionada["ruta"] in html
