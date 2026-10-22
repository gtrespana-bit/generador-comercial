"""Las páginas que traen el tráfico tienen que poder cachearse en el borde.

Las 23 landings de mercado, los 69 hubs de intención y el resto de la
superficie editorial se renderizaban enteras en cada visita de cada buscador
por un detalle: el servidor aprovechaba el render para escribir la cookie de
preferencia (``cotizat_pais``, ``cotizat_lang``), y una respuesta con
``Set-Cookie`` no se guarda en el CDN de Vercel. 92 de las 234 URL del sitemap
—justo las comerciales— llegaban sin ``Cache-Control``.

La preferencia se sigue guardando, ahora desde el navegador: el HTML depende
solo de la URL (eso es lo que hace válido el caché compartido) y el idioma y
el país se escriben en una cookie normal que el panel lee igual.

Lo que se comprueba aquí:

- Ninguna URL del sitemap fija cookies ni deja de sellarse (salvo las dos
  excepciones con motivo: ``/pago`` y ``/soporte``).
- El script de preferencias está en la página y codifica bien la ruta.
- El contenido sigue dependiendo solo de la URL: dos peticiones idénticas
  dan el mismo HTML con o sin cookie de idioma.
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.seo import urls_sitemap

BASE = "https://cotizat.online"

# Rutas del sitemap que sí varían por cookie y por eso no se sellan.
# - /pago: los importes y los métodos de pago salen de cotizat_pais.
# - /soporte: con sesión es el formulario dentro del panel (noindex).
EXCEPCIONES = {"/pago", "/en/pago", "/soporte", "/en/soporte"}

SELLO = "public, max-age=0, s-maxage=300"


def _sellada(respuesta) -> bool:
    return SELLO in (respuesta.headers.get("cache-control") or "")


def _rutas_sitemap() -> list[str]:
    return [urlsplit(e["loc"]).path for e in urls_sitemap()]


# ── El caché ────────────────────────────────────────────────────────────────


def test_la_superficie_comercial_se_sella_entera():
    rutas = [r for r in _rutas_sitemap() if r not in EXCEPCIONES]
    assert len(rutas) > 200
    sin_sello = []
    with TestClient(app, base_url=BASE) as cliente:
        for ruta in rutas:
            respuesta = cliente.get(ruta)
            if respuesta.status_code != 200:
                continue
            if not _sellada(respuesta):
                sin_sello.append(ruta)
    assert not sin_sello, sin_sello


def test_ninguna_pagina_publica_fija_cookies():
    """Un solo ``Set-Cookie`` deja la página fuera del CDN.

    Es la prueba que impide deshacer el arreglo sin enterarse: basta con que
    una vista pública vuelva a llamar a ``set_cookie``.
    """
    with TestClient(app, base_url=BASE) as cliente:
        culpables = []
        for ruta in _rutas_sitemap():
            if ruta in EXCEPCIONES:
                continue
            respuesta = cliente.get(ruta)
            if respuesta.status_code == 200 and "set-cookie" in respuesta.headers:
                culpables.append((ruta, respuesta.headers["set-cookie"]))
    assert not culpables, culpables


@pytest.mark.parametrize("ruta", ["/", "/mx/", "/en-gb/", "/mx/apu", "/co/remodelacion",
                                  "/en-us/unit-price-analysis", "/precios-comparados"])
def test_la_primera_visita_ya_es_cacheable(ruta):
    """La visita del rastreador (sin cookies) es la que más se repite."""
    with TestClient(app, base_url=BASE) as cliente:
        respuesta = cliente.get(ruta)
    assert respuesta.status_code == 200
    assert _sellada(respuesta)
    assert "set-cookie" not in respuesta.headers


def test_las_excepciones_estan_documentadas_y_siguen_siendo_excepcion():
    """Si /pago dejara de depender de la cookie, habría que sacarla de aquí."""
    with TestClient(app, base_url=BASE) as cliente:
        a = cliente.get("/pago", headers={"cookie": "cotizat_pais=MX"}).text
        b = cliente.get("/pago", headers={"cookie": "cotizat_pais=VE"}).text
    assert a != b, "si /pago ya no varía por cookie, puede entrar en el caché"


# ── El contenido no depende de la cookie ────────────────────────────────────


@pytest.mark.parametrize("ruta", ["/mx/apu", "/en-gb/estimating-software", "/", "/en-us/"])
def test_la_cookie_de_idioma_no_cambia_el_html(ruta):
    with TestClient(app, base_url=BASE) as cliente:
        sin = cliente.get(ruta).text
        con = cliente.get(ruta, headers={"cookie": "cotizat_lang=es; cotizat_pais=VE"}).text
    # El mismo documento salvo el nonce del CSP, que cambia en cada respuesta.
    limpiar = lambda h: re.sub(r'nonce="[^"]+"', 'nonce="x"', h)  # noqa: E731
    assert limpiar(sin) == limpiar(con)


# ── El script de preferencias ───────────────────────────────────────────────


@pytest.mark.parametrize("ruta", ["/mx/", "/en-gb/", "/mx/apu", "/en/pago", "/como-funciona"])
def test_la_pagina_publica_escribe_las_preferencias_desde_la_ruta(ruta):
    with TestClient(app, base_url=BASE) as cliente:
        html = cliente.get(ruta).text
    assert "cotizat_pais" in html
    assert "cotizat_lang" in html
    assert "document.cookie" in html
    # Sin nonce, el CSP bloquea el script y la preferencia no se guarda.
    bloque = re.search(r"<script nonce=\"[^\"]+\">(.*?document\.cookie.*?)</script>", html, re.S)
    assert bloque, ruta


def test_el_script_recibe_la_lista_de_mercados():
    """Sin la lista, el script no puede distinguir /mx/ de /legal/."""
    with TestClient(app, base_url=BASE) as cliente:
        html = cliente.get("/mx/").text
    assert '"MX"' in html and '"GB"' in html and '"VE"' in html


def test_el_selector_de_pais_sigue_leyendo_la_cookie():
    """La preferencia es una cookie normal: el servidor la ve aunque la ponga JS.

    Es lo que hace que, tras entrar por /mx/apu, /pago abra ya en México.
    """
    with TestClient(app, base_url=BASE) as cliente:
        mx = cliente.get("/pago", headers={"cookie": "cotizat_pais=MX"}).text
        ve = cliente.get("/pago", headers={"cookie": "cotizat_pais=VE"}).text
    assert 'value="MX" selected' in mx
    assert 'value="VE" selected' in ve
    assert 'value="MX" selected' not in ve


# ── Nada de lo anterior rompió la indexación ────────────────────────────────


@pytest.mark.parametrize("ruta", ["/mx/", "/en-gb/", "/mx/apu", "/en-us/unit-price-analysis"])
def test_la_pagina_sigue_indexandose_y_declarando_su_canonica(ruta):
    with TestClient(app, base_url=BASE) as cliente:
        respuesta = cliente.get(ruta)
    assert respuesta.status_code == 200
    assert respuesta.headers.get("x-robots-tag") is None
    assert f'rel="canonical" href="{BASE}{ruta}"' in respuesta.text
    assert 'name="robots" content="index' in respuesta.text
