"""El catálogo de precios: qué se anuncia a Google y qué no, y por qué.

Dos episodios, los dos con la misma lección.

**Primero** (agosto 2026): ``/mx/precios`` y sus ~47 000 URL hijas servían
``<meta name="robots" content="index,follow">`` y, a la vez,
``X-Robots-Tag: noindex``. Cuando las dos instrucciones se contradicen manda la
cabecera, así que el catálogo entero estaba fuera del índice aunque el sitemap
lo anunciara. De aquello queda la prueba de que el meta y la cabecera no pueden
divergir nunca.

**Después** (19/10/2026): con el catálogo ya anunciable, se publicaron de golpe
los 22 mercados. En los 17 hispanos el texto es el mismo —solo cambia la moneda
y el precio—: ~40 000 URL casi idénticas. El 23/10 Google no había indexado ni
una ficha y el sitio entero había caído a la posición 44 de media con 0 clics.
Desde entonces solo se anuncian los mercados de ``MERCADOS_FICHAS_INDEXABLES``;
el resto publica sus páginas con ``noindex, follow``, sin sitemap y sin
hreflang, pero navegables.

Estas pruebas vigilan las dos cosas: que lo anunciado sea indexable y que lo no
anunciado lo diga **en las dos cabeceras a la vez**.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.seo import es_indexable
from app.services import precios_publicos as pp

INDEXABLES = sorted(pp.paises_con_catalogo_indexable())
NO_ANUNCIADOS = sorted(set(pp.paises_publicados()) - set(INDEXABLES))


def _cliente() -> TestClient:
    return TestClient(app, base_url="https://cotizat.online")


def _meta_robots(respuesta) -> str:
    """Contenido del ``<meta name=robots>``, o cadena vacía si no hay."""
    partes = respuesta.text.split('name="robots"', 1)
    if len(partes) < 2:
        return ""
    resto = partes[1]
    inicio = resto.find('content="')
    if inicio == -1:
        return ""
    return resto[inicio + len('content="') :].split('"', 1)[0]


def test_hay_mercados_de_los_dos_tipos():
    """Si la política quedara vacía, las pruebas de abajo no probarían nada."""
    assert INDEXABLES, "ningún mercado anunciado"
    assert NO_ANUNCIADOS, "ningún mercado fuera del anuncio: revisa la política"


@pytest.mark.parametrize("cc", INDEXABLES)
def test_el_catalogo_anunciado_es_indexable_de_verdad(cc):
    """Meta y cabecera dicen «index» en el índice del catálogo del mercado."""
    with _cliente() as cliente:
        respuesta = cliente.get(pp.ruta_indice(cc))
    assert respuesta.status_code == 200
    assert "noindex" not in (respuesta.headers.get("x-robots-tag") or ""), cc
    assert "noindex" not in _meta_robots(respuesta), cc


@pytest.mark.parametrize("cc", INDEXABLES)
def test_apartado_y_partida_anunciados_tampoco_llevan_noindex(cc):
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
        assert "noindex" not in _meta_robots(respuesta), ruta


@pytest.mark.parametrize("cc", NO_ANUNCIADOS)
def test_el_mercado_no_anunciado_lleva_noindex_en_las_dos_cabeceras(cc):
    """La página sigue sirviendo al visitante, pero no compite en el índice.

    Y lo hace sin contradecirse: meta y ``X-Robots-Tag`` dicen lo mismo. Es la
    comprobación que faltaba en el episodio de agosto, cuando divergían.
    """
    indice = pp._indice(cc)  # noqa: SLF001 - solo lectura
    slug_ap = sorted(indice["apartados"])[0]
    ruta_partida = pp.ruta_indice(cc) + "/" + slug_ap
    for ruta in (pp.ruta_indice(cc), ruta_partida):
        with _cliente() as cliente:
            respuesta = cliente.get(ruta)
        assert respuesta.status_code == 200, ruta
        assert "noindex" in (respuesta.headers.get("x-robots-tag") or ""), ruta
        assert "noindex" in _meta_robots(respuesta), ruta


def test_mano_de_obra_y_json_de_un_mercado_no_anunciado():
    if "MX" not in NO_ANUNCIADOS:
        pytest.skip("México está anunciado en la política actual")
    for ruta in ("/mx/precios.json", "/mx/mano-de-obra"):
        with _cliente() as cliente:
            respuesta = cliente.get(ruta)
        assert respuesta.status_code == 200, ruta
        assert "noindex" in (respuesta.headers.get("x-robots-tag") or ""), ruta


def test_la_descarga_json_y_la_mano_de_obra_anunciadas_son_indexables():
    for ruta in (
        "/es/precios.json",
        "/en-us/prices.json",
        "/es/mano-de-obra",
        "/en-us/labour-rates",
    ):
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
    # Anunciados: España y los cinco mercados ingleses.
    assert es_indexable("/es/precios")
    assert es_indexable("/es/precios/azulejo-y-porcelanato-en-paredes")
    assert es_indexable("/es/precios/un-apartado/una-partida")
    assert es_indexable("/es/mano-de-obra")
    assert es_indexable("/es/precios.json")
    assert es_indexable("/en-gb/prices")
    assert es_indexable("/en-us/prices/carpentry-metalwork-glazing-and-solar-shading")
    assert es_indexable("/en-us/labour-rates")
    # No anunciados: el mismo catálogo en un mercado hispano copia de España.
    assert not es_indexable("/mx/precios")
    assert not es_indexable("/mx/precios/azulejo-y-porcelanato-en-paredes")
    assert not es_indexable("/mx/precios/un-apartado/una-partida")
    assert not es_indexable("/mx/mano-de-obra")
    assert not es_indexable("/mx/precios.json")
    # Sus páginas de mercado sí siguen indexables: son las que rankean.
    assert es_indexable("/mx/")
    assert es_indexable("/mx/apu")
    # Ni rutas de más ni prefijos parecidos.
    assert not es_indexable("/es/precios/a/b/c/d")
    assert not es_indexable("/es/preciosX")
    assert not es_indexable("/es/manos-de-obra")
    assert not es_indexable("/es/precios-2024")
