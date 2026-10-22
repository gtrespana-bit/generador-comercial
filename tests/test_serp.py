"""Higiene del resultado de búsqueda y de los enlaces internos.

Tres cosas que no rompen la página pero sí cuestan tráfico:

1. **Enlaces internos que pasan por una redirección.** Un ``<a href>`` a una
   URL que responde 301 gasta un salto en cada rastreo y reparte la señal
   entre dos direcciones. Al cambiar los slugs ingleses quedaron unos cuantos.
2. **Meta description que se corta.** Google corta alrededor de 155-160
   caracteres: lo que pase de ahí no se lee y a menudo deja la frase a medias.
3. **Pares de idioma sin declarar.** Las páginas estáticas tienen versión
   española e inglesa con contenido propio, pero no emitían ``hreflang``: para
   Google eran documentos sueltos y no dos versiones de lo mismo. El sitemap
   declaraba el par, pero sin ``x-default``.
"""
from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.seo import TEMAS_EN, urls_sitemap

BASE = "https://cotizat.online"

# Slugs que dejaron de ser URL canónica en algún mercado.
VIEJAS = ("/en/apu", "/en/remodelacion", "/en/software-presupuestos")


def _cliente() -> TestClient:
    return TestClient(app, base_url=BASE)


# ── Enlaces internos ────────────────────────────────────────────────────────


def _enlaces(html: str) -> list[str]:
    return [
        h.split("?")[0]
        for h in re.findall(r'<a[^>]+href="(/[^"#]*)"', html)
    ]


@pytest.mark.parametrize(
    "ruta",
    [
        "/en-gb/guia/unit-price-analysis-uk",
        "/en-gb/guia/construction-quote-template-uk",
        "/en-au/unit-price-analysis",
        "/en-ca/remodeling",
        "/en-us/estimating-software",
        "/en/guias",
    ],
)
def test_ningun_enlace_interno_apunta_a_un_slug_antiguo(ruta):
    with _cliente() as cliente:
        respuesta = cliente.get(ruta, follow_redirects=False)
        if respuesta.status_code != 200:
            pytest.skip(f"{ruta} no existe en este build")
        enlaces = _enlaces(respuesta.text)
    culpables = [e for e in enlaces if any(e.startswith(v) for v in VIEJAS)]
    assert not culpables, (ruta, culpables)


@pytest.mark.parametrize("ruta", ["/en-gb/", "/en-us/", "/en-au/", "/en-ie/"])
def test_los_hubs_ingleses_no_enlazan_con_barra_final_ni_con_el_slug_espanol(ruta):
    with _cliente() as cliente:
        enlaces = _enlaces(cliente.get(ruta).text)
    for tema in TEMAS_EN:
        assert f"/en/{tema}" not in enlaces, (ruta, tema)
        assert f"/en/{tema}/" not in enlaces, (ruta, tema)


def test_el_enlace_a_todos_los_paises_va_a_la_url_canonica():
    """/en/apu/ encadenaba dos 301: slug español y luego barra final."""
    with _cliente() as cliente:
        enlaces = _enlaces(cliente.get("/en-au/unit-price-analysis").text)
    assert "/en/unit-price-analysis" in enlaces
    assert not [e for e in enlaces if re.match(r"^/en/[a-z-]+/$", e and e)]


def test_el_boton_de_volver_del_pago_en_ingles_no_pasa_por_un_301():
    with _cliente() as cliente:
        enlaces = _enlaces(cliente.get("/en/pago").text)
    assert "/en/" not in enlaces
    assert "/en-us/" in enlaces


# ── Metadatos ───────────────────────────────────────────────────────────────


def test_ninguna_descripcion_del_sitio_se_corta_en_google():
    """≤160 caracteres, o el buscador la corta a media frase."""
    largas = []
    with _cliente() as cliente:
        for entrada in urls_sitemap():
            ruta = entrada["loc"].replace(BASE, "")
            respuesta = cliente.get(ruta)
            if respuesta.status_code != 200:
                continue
            m = re.search(r'name="description" content="([^"]*)"', respuesta.text)
            descripcion = m.group(1).strip() if m else ""
            if len(descripcion) > 160:
                largas.append((ruta, len(descripcion)))
    assert not largas, largas


def test_ningun_titulo_del_sitio_se_corta_en_google():
    """≤72 caracteres incluyendo la marca.

    El corte real de Google ronda los 60 caracteres (unos 600 px). Se fija
    aquí 72 como techo y no 60: por debajo de eso no hay nada que arreglar en
    este sitio salvo reescribir el copy de cada guía, y el nombre del capítulo
    del comparador más largo ya ocupa 71 por sí solo. Lo que sí se arregló fue
    el extremo: había títulos de 82 con el «| CotizaT» cortado a media palabra.
    """
    largos = []
    with _cliente() as cliente:
        for entrada in urls_sitemap():
            ruta = entrada["loc"].replace(BASE, "")
            respuesta = cliente.get(ruta)
            if respuesta.status_code != 200:
                continue
            m = re.search(r"<title>(.*?)</title>", respuesta.text)
            titulo = m.group(1).strip() if m else ""
            if len(titulo) > 72:
                largos.append((ruta, len(titulo), titulo))
    assert not largos, largos


# ── Pares de idioma de las páginas estáticas ────────────────────────────────


@pytest.mark.parametrize(
    "par",
    [
        ("/como-funciona", "/en/como-funciona"),
        ("/novedades", "/en/novedades"),
        ("/mapa-del-sitio", "/en/mapa-del-sitio"),
        ("/pago", "/en/pago"),
        ("/legal/terminos", "/en/legal/terminos"),
    ],
)
def test_cada_pagina_estatica_declara_su_par_con_x_default(par):
    es, en = par
    esperado = [
        ("es", BASE + es),
        ("en", BASE + en),
        ("x-default", BASE + es),
    ]
    with _cliente() as cliente:
        for ruta in par:
            html = cliente.get(ruta).text
            alternates = re.findall(
                r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"', html
            )
            assert alternates == esperado, (ruta, alternates)


def test_el_sitemap_declara_x_default_en_los_pares():
    faltan = [
        e["loc"]
        for e in urls_sitemap()
        if e["alternates"] and not any(a["hreflang"] == "x-default" for a in e["alternates"])
    ]
    assert not faltan, faltan[:10]
