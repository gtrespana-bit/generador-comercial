"""El catálogo de precios tiene que ser indexable de verdad, no solo en el meta.

Durante toda la vida del catálogo, ``/mx/precios`` y sus ~47 000 URL hijas
servían ``<meta name="robots" content="index,follow">`` y, a la vez,
``X-Robots-Tag: noindex, nofollow, noarchive``. Cuando las dos instrucciones se
contradicen, Google aplica la cabecera: el catálogo entero estaba fuera del
índice aunque el sitemap lo anunciara y el meta dijera lo contrario.

Estas pruebas vigilan la cabecera, que es la que manda, en las tres
profundidades del catálogo y en los 22 mercados, más las páginas nuevas
(mano de obra y descarga JSON) y las que sí deben seguir fuera del índice.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.seo import es_indexable
from app.services import precios_publicos as pp

MERCADOS = sorted(pp.paises_publicados())


def _cliente() -> TestClient:
    return TestClient(app, base_url="https://cotizat.online")


@pytest.mark.parametrize("cc", MERCADOS)
def test_el_indice_de_precios_del_pais_no_lleva_noindex(cc):
    with _cliente() as cliente:
        respuesta = cliente.get(pp.ruta_indice(cc))
    assert respuesta.status_code == 200
    assert "noindex" not in (respuesta.headers.get("x-robots-tag") or ""), cc
    assert "noindex" not in respuesta.text.split('name="robots"')[1][:120]


@pytest.mark.parametrize("cc", ["MX", "US", "ES", "GB", "CO", "AR"])
def test_apartado_y_partida_tampoco_llevan_noindex(cc):
    indice = pp._indice(cc)  # noqa: SLF001 - solo lectura
    slug_ap = sorted(indice["apartados"])[0]
    apartado = pp.apartado(cc, slug_ap)
    slug_p = apartado["partidas"][0]["slug"]
    for ruta in (
        pp.ruta_apartado(cc, slug_ap),
        pp.ruta_partida(cc, slug_ap, slug_p),
    ):
        with _cliente() as cliente:
            respuesta = cliente.get(ruta)
        assert respuesta.status_code == 200, ruta
        assert "noindex" not in (respuesta.headers.get("x-robots-tag") or ""), ruta


def test_la_descarga_json_y_la_mano_de_obra_son_indexables():
    for ruta in ("/mx/precios.json", "/en-us/prices.json", "/mx/mano-de-obra", "/en-us/labour-rates"):
        with _cliente() as cliente:
            respuesta = cliente.get(ruta)
        assert respuesta.status_code == 200, ruta
        assert "noindex" not in (respuesta.headers.get("x-robots-tag") or ""), ruta


def test_las_rutas_privadas_siguen_fuera_del_indice():
    for ruta in ("/presupuestos", "/acceso", "/admin", "/mx/presupuestos", "/en-us/inicio"):
        with _cliente() as cliente:
            respuesta = cliente.get(ruta)
        if respuesta.status_code in (301, 302, 404):
            continue
        assert "noindex" in (respuesta.headers.get("x-robots-tag") or ""), ruta


def test_la_regla_reconoce_las_formas_canonicas_y_nada_mas():
    assert es_indexable("/mx/precios")
    assert es_indexable("/mx/precios/azulejo-y-porcelanato-en-paredes")
    assert es_indexable("/mx/precios/un-apartado/una-partida")
    assert es_indexable("/en-gb/prices")
    assert es_indexable("/en-us/prices/carpentry-metalwork-glazing-and-solar-shading")
    assert es_indexable("/mx/mano-de-obra")
    assert es_indexable("/en-us/labour-rates")
    assert es_indexable("/mx/precios.json")
    # Ni rutas de más ni prefijos parecidos.
    assert not es_indexable("/mx/precios/a/b/c/d")
    assert not es_indexable("/mx/preciosX")
    assert not es_indexable("/mx/manos-de-obra")
    assert not es_indexable("/mx/precios-2024")
