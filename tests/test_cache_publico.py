"""Caché CDN de la superficie pública (Fase 1.2).

Contrato fijado por estas pruebas:

* El predicado de rutas acepta TODAS las URLs del sitemap (y sus
  alternantes hreflang): si nace una página pública nueva y no entra en
  la lista blanca, esto se rompe y obliga a decidirlo a conciencia.
* El predicado rechaza todo lo demás (sesión, pago, soporte, estáticos,
  archivos): ahí jamás debe haber caché compartida.
* En la superficie pública el idioma sale SOLO de la URL (la cookie se
  ignora): es la condición para que una URL tenga un único contenido
  cacheable. Fuera de ella (/soporte) la cookie sigue mandando.
* La cabecera de caché solo se sella en GET 200 anónimos, sin query y
  sin Set-Cookie en la respuesta. Las cookies de preferencia (idioma y
  país) solo se fijan si cambian: la primera visita las guarda y las
  siguientes pueden poblar el CDN.
"""
from __future__ import annotations

from urllib.parse import urlsplit

import pytest

from app.cache_publico import es_ruta_publica_cacheable
from app.seo import urls_sitemap


# ---------------------------------------------------------------------------
# Predicado: cobertura total del sitemap
# ---------------------------------------------------------------------------


# Están en el sitemap pero su HTML varía por cookie o por query: jamás
# deben sellarse como cacheables.
# - /soporte: el idioma sigue saliendo de la cookie (es un formulario).
# - /pago: los métodos de pago salen de la cookie cotizat_pais y acepta
#   ?msg= con el motivo de la llegada.
EXCEPCIONES_SITEMAP = {"/pago", "/soporte", "/en/pago", "/en/soporte"}


def test_predicado_cubre_todo_el_sitemap():
    entradas = urls_sitemap()
    assert len(entradas) >= 190  # cordura: no estamos validando una lista vacía
    rutas = set()
    for entrada in entradas:
        rutas.add(urlsplit(entrada["loc"]).path)
        for alternante in entrada.get("alternates") or []:
            rutas.add(urlsplit(alternante["href"]).path)
    fuera = {r for r in rutas if not es_ruta_publica_cacheable(r)}
    assert fuera == EXCEPCIONES_SITEMAP, (
        "La brecha entre el sitemap y la lista blanca cambió: "
        f"fuera={sorted(fuera)}, documentadas={sorted(EXCEPCIONES_SITEMAP)}. "
        "Si nace una página pública nueva hay que decidirlo a conciencia: "
        "o entra en app/cache_publico.py (y su idioma saldrá solo de la "
        "URL) o se añade aquí como excepción con su motivo."
    )


@pytest.mark.parametrize(
    "ruta",
    [
        "/",
        "/conocer",
        "/mapa-del-sitio",
        "/novedades",
        "/como-funciona",
        "/robots.txt",
        "/sitemap.xml",
        "/ve",
        "/co/",
        "/en-us/",
        "/en-gb/apu",
        "/guia/como-hacer-un-presupuesto-de-obra",
        "/mx/guia/costo-metro-cuadrado",
        "/software-presupuestos",
        "/mx/remodelacion",
        "/en-mx/software-presupuestos",
        "/legal/privacidad",
    ],
)
def test_predicado_acepta_la_superficie_publica(ruta):
    assert es_ruta_publica_cacheable(ruta)


@pytest.mark.parametrize(
    "ruta",
    [
        "/soporte",
        "/pago",
        "/inicio",
        "/idioma/en",
        "/idioma/es",
        "/static/estilos.css",
        "/archivos/abc/foto.png",
        "/archivos-legado/foto.png",
        "/readyz",
        "/healthz",
        "/en-us/soporte",
        "/guia",
        "/guia/",
        "/xx/",
        "/xx/guia/abc",
        "/admin",
        "/mx/guia",
    ],
)
def test_predicado_rechaza_fuera_de_la_superficie(ruta):
    assert not es_ruta_publica_cacheable(ruta)


# ---------------------------------------------------------------------------
# Comportamiento HTTP: sello, guardas e idioma por URL
# ---------------------------------------------------------------------------


def _sellada(respuesta) -> bool:
    cc = respuesta.headers.get("cache-control", "")
    return cc.startswith("public") and "s-maxage=300" in cc


def test_home_anonima_se_sella(cliente_web):
    r = cliente_web.get("/")
    assert r.status_code == 200
    assert '<html lang="es">' in r.text
    assert _sellada(r)


def test_home_ignora_la_cookie_de_idioma(cliente_web):
    # Una URL, un contenido: con cookie «en», la home cacheable sigue
    # sirviendo la versión en español que indica la URL.
    r = cliente_web.get("/", headers={"cookie": "cotizat_lang=en"})
    assert r.status_code == 200
    assert '<html lang="es">' in r.text
    assert _sellada(r)


def test_primera_visita_en_fija_preferencias_sin_sellar(cliente_web):
    r = cliente_web.get("/en-us/")
    assert r.status_code == 200
    assert '<html lang="en-US">' in r.text
    assert "cotizat_lang=en" in r.headers.get("set-cookie", "")
    assert not _sellada(r)  # con Set-Cookie nunca se sella


def test_visita_en_con_preferencias_no_refija_y_se_sella(cliente_web):
    r = cliente_web.get(
        "/en-us/", headers={"cookie": "cotizat_lang=en; cotizat_pais=US"}
    )
    assert r.status_code == 200
    assert '<html lang="en-US">' in r.text
    assert "set-cookie" not in r.headers
    assert _sellada(r)


def test_no_se_refija_la_cookie_de_idioma(cliente_web):
    # Falta la de país (se fijará), pero la de idioma ya vale «en»:
    # re-fijarla seria el Set-Cookie que impide poblar el caché.
    r = cliente_web.get("/en-us/", headers={"cookie": "cotizat_lang=en"})
    assert r.status_code == 200
    assert "cotizat_lang" not in r.headers.get("set-cookie", "")


def test_hub_de_pais_con_cookie_puesta_se_sella(cliente_web):
    r = cliente_web.get(
        "/mx/software-presupuestos", headers={"cookie": "cotizat_pais=MX"}
    )
    assert r.status_code == 200
    assert "set-cookie" not in r.headers
    assert _sellada(r)


def test_landing_pais_primera_visita_fija_cookie_sin_sellar(cliente_web):
    r = cliente_web.get("/co/")
    assert r.status_code == 200
    assert "cotizat_pais=CO" in r.headers.get("set-cookie", "")
    assert not _sellada(r)


def test_con_sesion_nunca_se_sella(cliente_web):
    r = cliente_web.get("/", headers={"cookie": "cotizat_access_token=falso"})
    assert r.status_code == 200
    assert not _sellada(r)


def test_robots_y_sitemap_sellados(cliente_web):
    assert _sellada(cliente_web.get("/robots.txt"))
    assert _sellada(cliente_web.get("/sitemap.xml"))


def test_redireccion_con_query_no_se_sella(cliente_web):
    r = cliente_web.get("/?pais=ES", follow_redirects=False)
    assert r.status_code == 301
    assert not _sellada(r)


def test_soporte_queda_fuera_y_la_cookie_manda(cliente_web):
    r = cliente_web.get("/soporte")
    assert r.status_code == 200
    assert '<html lang="es">' in r.text
    assert not _sellada(r)

    r_en = cliente_web.get("/soporte", headers={"cookie": "cotizat_lang=en"})
    assert r_en.status_code == 200
    assert '<html lang="en">' in r_en.text  # fuera de la superficie, cookie manda
    assert not _sellada(r_en)
