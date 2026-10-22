"""La marca y sus perfiles sociales son la misma entidad.

Google une cuentas y sitio con ``sameAs`` en el JSON-LD de organización y con
enlaces ``rel="me"``. Sin esa señal, la página de Facebook «CotizaT» y
cotizat.online son dos cosas distintas con el mismo nombre, y el nombre
propio puede resolverse a cualquiera de las dos (o a un homónimo).

Lo que se comprueba aquí:

- El ``sameAs`` aparece en el JSON-LD de todas las plantillas que emiten la
  organización, en español y en inglés, con la URL exacta del perfil.
- El pie enlaza al perfil con ``rel="me"``.
- Los enlaces externos llevan ``rel="noopener"`` y ``target="_blank"``.
- Si hay token de verificación de Meta en el entorno, se emite la etiqueta;
  si no, no se emite nada (el sitio no finge una verificación inexistente).
- La lista de perfiles tiene una sola fuente: ``app/social.py``.
"""
from __future__ import annotations

import json
import re

import pytest
from fastapi.testclient import TestClient

from app import social
from app.main import app

BASE = "https://cotizat.online"
FACEBOOK = "https://www.facebook.com/profile.php?id=61593422986397"


def _cliente() -> TestClient:
    return TestClient(app, base_url=BASE)


def _bloques_jsonld(html: str) -> list[dict]:
    crudos = re.findall(
        r'<script type="application/ld\+json"[^>]*>(.*?)</script>', html, re.S
    )
    salida = []
    for crudo in crudos:
        try:
            datos = json.loads(crudo)
        except ValueError:
            continue
        salida.extend(datos if isinstance(datos, list) else [datos])
    return salida


# ── La fuente única ─────────────────────────────────────────────────────────


def test_el_perfil_de_facebook_esta_en_la_lista():
    assert social.PERFILES["facebook"] == FACEBOOK
    assert FACEBOOK in social.same_as()


def test_same_as_no_repite_urls():
    assert len(social.same_as()) == len(set(social.same_as()))


def test_los_enlaces_del_pie_salen_de_la_misma_lista():
    for enlace in social.enlaces():
        assert enlace["url"] in social.same_as()
        assert enlace["nombre"] == "Facebook"


# ── JSON-LD ─────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "ruta",
    [
        "/",
        "/mx/apu",
        "/en/unit-price-analysis",
        "/en-us/estimating-software",
        "/como-funciona",
        "/precios-comparados",
        "/calculadora",
    ],
)
def test_la_organizacion_declara_sus_perfiles(ruta):
    with _cliente() as cliente:
        html = cliente.get(ruta).text
    organizaciones = [
        b for b in _bloques_jsonld(html) if b.get("@type") == "Organization"
    ]
    assert organizaciones, ruta
    for organizacion in organizaciones:
        assert FACEBOOK in (organizacion.get("sameAs") or []), ruta


def test_el_perfil_se_declara_igual_en_los_dos_idiomas():
    with _cliente() as cliente:
        es = [b for b in _bloques_jsonld(cliente.get("/").text) if b.get("@type") == "Organization"]
        en = [
            b
            for b in _bloques_jsonld(cliente.get("/en-us/").text)
            if b.get("@type") == "Organization"
        ]
    assert es[0]["sameAs"] == en[0]["sameAs"] == social.same_as()


# ── Pie ────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("ruta", ["/", "/mx/", "/en-gb/", "/mx/apu", "/en/pago"])
def test_el_pie_enlaza_al_perfil_con_rel_me(ruta):
    with _cliente() as cliente:
        html = cliente.get(ruta).text
    enlaces = re.findall(r"<a\b[^>]*facebook\.com[^>]*>", html)
    assert enlaces, ruta
    for etiqueta in enlaces:
        assert 'rel="me noopener"' in etiqueta
        assert 'target="_blank"' in etiqueta


def test_el_enlace_del_pie_es_el_mismo_en_los_dos_idiomas():
    with _cliente() as cliente:
        es = re.findall(r'href="(https://www\.facebook\.com[^"]*)"', cliente.get("/mx/").text)
        en = re.findall(
            r'href="(https://www\.facebook\.com[^"]*)"', cliente.get("/en-gb/").text
        )
    assert es == en == [FACEBOOK]


# ── Verificación de dominio de Meta ────────────────────────────────────────


def test_sin_token_no_se_emite_la_etiqueta_de_meta(monkeypatch):
    monkeypatch.delenv("COTIZAT_FACEBOOK_DOMAIN_VERIFICATION", raising=False)
    assert social.verificacion_dominio_meta() == ""
    with _cliente() as cliente:
        html = cliente.get("/").text
    assert "facebook-domain-verification" not in html


def test_con_token_se_emite_la_etiqueta(monkeypatch):
    # Se lee del entorno en cada petición: el titular pega el token en Vercel
    # y no hace falta tocar código ni compartirlo.
    # Sin hexadecimal: un token de ejemplo con pinta de hash lo marca el
    # escáner de secretos de CI (detect-secrets) y rompe la compilación.
    token = "token-de-ejemplo-para-la-prueba"
    monkeypatch.setenv("COTIZAT_FACEBOOK_DOMAIN_VERIFICATION", token)
    assert social.verificacion_dominio_meta() == token
    with _cliente() as cliente:
        html = cliente.get("/").text
    assert f'<meta name="facebook-domain-verification" content="{token}">' in html


def test_la_etiqueta_va_en_todas_las_paginas_publicas(monkeypatch):
    monkeypatch.setenv("COTIZAT_FACEBOOK_DOMAIN_VERIFICATION", "token-de-prueba")
    with _cliente() as cliente:
        for ruta in ("/", "/mx/apu", "/en/pago", "/legal/privacidad"):
            assert "facebook-domain-verification" in cliente.get(ruta).text, ruta
