"""El título de un hub de apartado lleva la cifra, y la cifra es verdad.

El 02/11/2026 el hub con la segunda cifra de impresiones del sitio
(`/en-ie/prices/lifts-and-platform-lifts`: 63 impresiones, posición 10,2) tenía
**cero clics**. El título era «Lifts and platform lifts: unit prices in Ireland
(EUR)»: un listado que no promete ninguna cifra, compitiendo contra páginas que
sí la dan para la consulta «home lift prices ireland».

La cifra existía en el código pero casi nunca llegaba al título: se escribía con
céntimos y con la moneda dos veces («40,00 EUR–264,00 EUR»), así que no cabía en
los 60 caracteres del resultado y se caía a la variante sin precio. Estas
pruebas fijan las tres reglas del arreglo:

* la cifra va en el título siempre que sea posible, sin céntimos y con la
  moneda una sola vez;
* el rango doble solo se escribe si el apartado es homogéneo —sumar precios de
  m² y de unidad no da un rango— y si la dispersión no lo vuelve inútil;
* el redondeo es hacia arriba y conserva decimales en importes pequeños, para no
  publicar «desde 1 EUR» donde la partida cuesta 0,48.
"""
from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from app import seo_precios as sp
from app.main import app
from app.paises import PAISES
from app.services import precios_publicos as pp

BASE = "https://cotizat.online"


def _partidas(precios, unidad="m²"):
    return [
        {"pu": precio, "unidad": unidad, "moneda": "EUR", "slug": f"p{i}", "titulo": f"P{i}"}
        for i, precio in enumerate(precios)
    ]


def _titulo(partidas, *, cc="ES", apartado="Pintura interior"):
    pais = PAISES[cc]
    nombre = sp._nombre_pais(cc, "en" if str(pais.get("idioma")) == "en" else "es")
    en = str(pais.get("idioma")) == "en"
    return sp.titulo_apartado(cc, apartado, nombre, pais, partidas, en)


def test_el_titulo_lleva_la_cifra_sin_centimos_y_con_la_moneda_una_vez():
    titulo, descripcion = _titulo(_partidas([39.82, 120.0, 263.62]))
    assert "40–264 EUR/m²" in titulo
    assert titulo.count("EUR") == 1
    assert "," not in titulo.split("EUR")[0], "los céntimos no caben en el título"
    assert len(titulo.removesuffix(" | CotizaT")) <= 60
    assert "de 40 a 264 EUR/m²" in descripcion


def test_el_rango_solo_cuando_el_apartado_es_homogeneo():
    mixto = _partidas([10.0, 20.0], "m²") + _partidas([300.0, 400.0], "ud")
    titulo, _ = _titulo(mixto)
    assert "–" not in titulo, titulo  # no se inventa un rango entre m² y unidad
    assert "/m²" not in titulo and "/ud" not in titulo
    assert re.search(r"\d", titulo), titulo  # pero la cifra sigue ahí


def test_una_dispersion_de_100_a_1_no_se_anuncia_como_rango():
    """«0,48–63,68 EUR» no informa de nada y parece un error del catálogo."""
    titulo, _ = _titulo(_partidas([0.48, 0.6, 0.9, 63.68]))
    assert "–" not in titulo, titulo
    assert "de media" in titulo


def test_el_redondeo_es_hacia_arriba_y_no_se_come_los_importes_pequenos():
    """Con una partida de 39,82 EUR, «desde 39» sería prometer un precio falso."""
    titulo, _ = _titulo(_partidas([39.82, 40.0], "ud"))
    assert "40" in titulo and "39" not in titulo

    pequeno, _ = _titulo(_partidas([0.48, 0.52, 0.9]))
    assert "0,5" in pequeno or "0,48" in pequeno, pequeno
    assert not re.search(r"\b1 EUR", pequeno), pequeno


def test_un_nombre_largo_no_se_come_la_cifra():
    """El caso de Irlanda: apartado y país largos, y la cifra desaparecía."""
    partidas = _partidas([750.02, 1200.0, 1991.17], "ea")
    titulo, _ = _titulo(
        partidas, cc="IE", apartado="Lifts and platform lifts"
    )
    assert "751–1,992 EUR/ea" in titulo, titulo

    largo, _ = _titulo(
        _partidas([1.0, 2.0, 30.0], "m²"),
        cc="US",
        apartado="Exploratory openings, detection and surveys",
    )
    assert re.search(r"\d", largo), largo
    assert len(largo.removesuffix(" | CotizaT")) <= 72


@pytest.mark.parametrize("cc", ["ES", "US", "GB", "IE"])
def test_la_mayoria_de_los_hubs_del_catalogo_llevan_cifra(cc):
    """La regresión que importa: que la cifra no vuelva a desaparecer en masa.

    Se mide sobre el catálogo real, no sobre un ejemplo. Antes del arreglo la
    llevaba el 22 % de los hubs; por debajo del 80 % esta prueba falla.
    """
    indice = pp._indice(cc)
    assert indice, cc
    pais = PAISES[cc]
    en = str(pais.get("idioma")) == "en"
    nombre = sp._nombre_pais(cc, "en" if en else "es")
    con_cifra = total = 0
    for slug in indice["apartados"]:
        apartado = pp.apartado(cc, slug)
        if not apartado or not apartado.get("partidas"):
            continue
        titulo, _ = sp.titulo_apartado(
            cc, apartado["nombre"], nombre, pais, apartado["partidas"], en
        )
        total += 1
        con_cifra += bool(re.search(r"\d", titulo))
        assert len(titulo.removesuffix(" | CotizaT")) <= 72, (cc, slug, titulo)
    assert con_cifra / total >= 0.8, f"{cc}: {con_cifra}/{total} con cifra"


def test_el_caso_de_irlanda_en_la_pagina_real():
    """De punta a punta: la URL que tenía 63 impresiones y cero clics."""
    with TestClient(app, base_url=BASE) as cliente:
        respuesta = cliente.get("/en-ie/prices/lifts-and-platform-lifts")
    assert respuesta.status_code == 200
    titulo = re.search(r"<title>(.*?)</title>", respuesta.text, re.S)
    assert titulo
    assert re.search(r"\d", titulo.group(1)), titulo.group(1)
    assert "EUR" in titulo.group(1)
