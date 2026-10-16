"""Conmutador de idioma ES/EN: rutas, cookie y presencia en la interfaz.

El conmutador no puede limitarse a enlazar ``/en/...``: al volver al español
(no lleva prefijo) la cookie seguiría en inglés y la interfaz no cambiaría. De
ahí la ruta ``/idioma/{lang}``, que escribe la cookie en los dos sentidos.
"""
import re

import pytest
from fastapi.testclient import TestClient

from app.i18n import (
    COOKIE_IDIOMA,
    codigos_pais,
    normalizar_idioma,
    partir_ruta,
    ruta_en_idioma,
    ruta_segura,
    url_cambio_idioma,
)
from app.main import app
from app.seo import es_indexable


# --------------------------------------------------------------------------
# Utilidades de ruta
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    "ruta,esperado",
    [
        ("/", ("", "/")),
        ("/apu", ("", "/apu")),
        ("/mx", ("mx", "/")),
        ("/mx/apu", ("mx", "/apu")),
        ("/es/", ("es", "/")),
        # El formato que ve el navegador, antes de que el middleware lo reescriba.
        ("/en", ("", "/")),
        ("/en/apu", ("", "/apu")),
        ("/en-mx/apu", ("mx", "/apu")),
        ("/en-es/apu", ("es", "/apu")),
        # Un slug que empiece por «en» no es un prefijo de idioma.
        ("/enlaces", ("", "/enlaces")),
    ],
)
def test_partir_ruta(ruta, esperado):
    assert partir_ruta(ruta) == esperado


@pytest.mark.parametrize(
    "ruta,idioma,esperado",
    [
        ("/", "en", "/en"),
        ("/", "es", "/"),
        ("/apu", "en", "/en/apu"),
        ("/apu", "es", "/apu"),
        ("/mx/apu", "en", "/en-mx/apu"),
        ("/mx/apu", "es", "/mx/apu"),
        ("/en-mx/apu", "es", "/mx/apu"),  # ida y vuelta
        ("/en-mx/apu", "en", "/en-mx/apu"),
        ("/presupuestos/nuevo", "en", "/en/presupuestos/nuevo"),
        ("/guia/presupuesto-de-obra", "en", "/en/guia/presupuesto-de-obra"),
        ("/en/", "es", "/"),
    ],
)
def test_ruta_en_idioma(ruta, idioma, esperado):
    assert ruta_en_idioma(ruta, idioma) == esperado


def test_idioma_desconocido_cae_al_espanol():
    assert ruta_en_idioma("/apu", "fr") == "/apu"
    assert normalizar_idioma("en-GB") == "en"


@pytest.mark.parametrize(
    "destino,esperado",
    [
        ("//malo.com/x", "/"),  # relativo a protocolo
        ("http://malo.com/x", "/"),  # absoluto
        ("https://malo.com", "/"),
        ("ftp://x/y", "/"),
        ("/idioma/es", "/"),  # no se permite volver al conmutador
        ("/idioma/en?destino=/apu", "/"),
        ("", "/"),
        ("\\malo", "/"),
        ("/apu", "/apu"),
        ("/apu?a=1", "/apu"),  # la query se reincorpora aparte
        ("/apu#ancla", "/apu"),
    ],
)
def test_ruta_segura_rechaza_lo_que_no_es_interno(destino, esperado):
    assert ruta_segura(destino) == esperado


@pytest.mark.parametrize("destino", ["//malo.com/x", "http://malo.com/x"])
def test_ruta_segura_no_deja_pasar_el_path_de_un_dominio_ajeno(destino):
    """``urlsplit('//malo.com/x').path`` es ``/x``: partir antes de sanear
    convertiría el conmutador en un open redirect."""
    assert ruta_segura(destino) == "/"
    assert ruta_en_idioma(ruta_segura(destino), "en") == "/en"


def test_url_cambio_idioma():
    assert url_cambio_idioma("/apu", "en") == "/idioma/en?destino=/apu"
    assert url_cambio_idioma("/apu", "es") == "/idioma/es?destino=/apu"
    # La query de la página de partida viaja codificada dentro de «destino».
    assert url_cambio_idioma("/presupuestos?estado=borrador", "en") == (
        "/idioma/en?destino=/presupuestos?estado=borrador"
    )
    assert url_cambio_idioma(None, "en") == "/idioma/en?destino=/"


def test_codigos_pais_incluye_los_mercados_con_landing():
    codigos = codigos_pais()
    assert {"mx", "es", "co", "pe", "ar"} <= codigos


# --------------------------------------------------------------------------
# Ruta /idioma/{lang}
# --------------------------------------------------------------------------
@pytest.fixture()
def cliente():
    with TestClient(app) as c:
        yield c


@pytest.mark.parametrize(
    "url,ubicacion,cookie",
    [
        ("/idioma/en?destino=/apu", "/en/apu", "en"),
        ("/idioma/es?destino=/apu", "/apu", "es"),
        ("/idioma/en?destino=/mx/apu", "/en-mx/apu", "en"),
        ("/idioma/es?destino=/mx/apu", "/mx/apu", "es"),
        ("/idioma/en?destino=/", "/en", "en"),
        ("/idioma/es?destino=/en/", "/", "es"),
        ("/idioma/en?destino=/presupuestos", "/en/presupuestos", "en"),
        ("/idioma/xx?destino=/apu", "/apu", "es"),  # idioma inválido → español
    ],
)
def test_cambio_idioma_redirige_y_fija_cookie(cliente, url, ubicacion, cookie):
    r = cliente.get(url, follow_redirects=False)
    assert r.status_code == 307
    assert r.headers["location"] == ubicacion
    assert r.headers["set-cookie"].startswith(f"{COOKIE_IDIOMA}={cookie};")


def test_cambio_idioma_conserva_la_query(cliente):
    r = cliente.get("/idioma/en?destino=/presupuestos?estado=borrador", follow_redirects=False)
    assert r.headers["location"] == "/en/presupuestos?estado=borrador"


@pytest.mark.parametrize(
    "destino",
    ["//malo.com/x", "http://malo.com/x", "https://malo.com", "/idioma/es"],
)
def test_cambio_idioma_no_es_un_open_redirect(cliente, destino):
    r = cliente.get(f"/idioma/en?destino={destino}", follow_redirects=False)
    assert r.status_code == 307
    assert r.headers["location"].startswith("/en")
    assert "malo.com" not in r.headers["location"]


def test_cambio_idioma_no_es_indexable(cliente):
    assert es_indexable("/idioma/en") is False
    r = cliente.get("/idioma/en?destino=/apu", follow_redirects=False)
    assert "noindex" in r.headers.get("x-robots-tag", "")


def test_el_conmutador_es_ida_y_vuelta(cliente):
    """Del español al inglés y de vuelta: la cookie es la que manda cuando no
    hay prefijo, así que el segundo salto tiene que limpiarla."""
    r = cliente.get("/idioma/en?destino=/apu", follow_redirects=False)
    assert r.headers["set-cookie"].startswith(f"{COOKIE_IDIOMA}=en;")
    r = cliente.get("/idioma/es?destino=/apu", follow_redirects=False)
    assert r.headers["set-cookie"].startswith(f"{COOKIE_IDIOMA}=es;")
    assert r.headers["location"] == "/apu"


def test_visitar_en_fija_la_cookie_para_el_resto_de_la_sesion(cliente):
    cliente.get("/en/apu", follow_redirects=True)
    # Sin prefijo, la cookie mantiene el inglés en todo el panel.
    r = cliente.get("/apu", follow_redirects=False)
    assert 'lang="en"' in r.text


# --------------------------------------------------------------------------
# Presencia en la interfaz
# --------------------------------------------------------------------------
MARCA = 'class="idioma-switch"'
ACTIVO = re.compile(r'idioma-switch-opcion is-active[^>]*>([A-Z]{2})<')


@pytest.mark.parametrize(
    "ruta",
    ["/", "/apu", "/mx/", "/en/", "/en/apu", "/como-funciona", "/pago", "/acceso",
     "/recuperar-acceso", "/restablecer-clave"],
)
def test_la_web_publica_lleva_el_conmutador(cliente, ruta):
    r = cliente.get(ruta, follow_redirects=True)
    assert r.status_code == 200
    assert MARCA in r.text, f"{ruta} no pinta el conmutador"


@pytest.mark.parametrize(
    "ruta,cookies,activo",
    [
        ("/", {}, "ES"),
        ("/apu", {"cotizat_lang": "en"}, "EN"),
        ("/en/apu", {}, "EN"),
        ("/en-mx/apu", {}, "EN"),
        ("/acceso", {"cotizat_lang": "en"}, "EN"),
        ("/acceso", {}, "ES"),
    ],
)
def test_el_conmutador_marca_el_idioma_activo(cliente, ruta, cookies, activo):
    with TestClient(app) as c:  # cliente limpio: sin restos de casos anteriores
        for nombre, valor in cookies.items():
            c.cookies.set(nombre, valor)
        r = c.get(ruta, follow_redirects=True)
    marcados = set(ACTIVO.findall(r.text))
    assert marcados == {activo}, f"{ruta} marca {marcados}"


def test_el_conmutador_apunta_a_la_misma_pagina_en_el_otro_idioma(cliente):
    r = cliente.get("/mx/apu", follow_redirects=True)
    assert '/idioma/en?destino=/mx/apu' in r.text
    assert '/idioma/es?destino=/mx/apu' in r.text


def test_el_html_lang_coincide_con_el_hreflang_del_pais(cliente):
    """/en-mx/ y /en-mx/apu se anuncian como en-MX; /mx/ como es-MX."""
    pares = [("/en-mx/", "en-MX"), ("/en-mx/apu", "en-MX"), ("/mx/", "es-MX"), ("/en/", "en")]
    for ruta, esperado in pares:
        with TestClient(app) as c:
            r = c.get(ruta, follow_redirects=True)
        m = re.search(r'<html[^>]*lang="([a-zA-Z-]+)"', r.text)
        assert m is not None, ruta
        assert m.group(1) == esperado, f"{ruta} → lang={m.group(1)}"
