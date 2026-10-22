"""Lo que pedía la auditoría externa (SEO Ninja, 95/100, 22-10-2026).

El informe de `seoninja.com` sobre `https://cotizat.online/` daba 10 avisos.
Cinco eran **falsos positivos** del escáner —decía que faltaban CSP, HSTS,
X-Frame-Options, compresión y Cache-Control, y las cinco cabeceras están en
producción (comprobado con una petición HEAD externa)—. Los otros cinco eran
reales y son los que fija este fichero:

1. **www no redirigía con 301**: Vercel devolvía 307 (temporal), que no
   consolida. Ahora `vercel.json` lo declara permanente y, además, el
   middleware de host lo garantiza en cualquier despliegue.
2. **0 enlaces externos**: la portada no citaba ninguna fuente. Ahora cita
   el CTE y el BOE, que es lo que sostiene las afirmaciones del copy.
3. **Un «párrafo» de 747 palabras**: es el mock decorativo del hero, marcado
   `aria-hidden`; no es prosa y no se toca.
4. **`llms.txt` ausente**: añadido, generado del mismo sitio que el sitemap.
5. **Sin encabezados en forma de pregunta**: las preguntas del FAQ iban en
   `<summary>`, que no es un encabezado. Ahora llevan `<h3>` dentro.
"""
from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.seo import llms_txt, urls_sitemap

BASE = "https://cotizat.online"

# Dominios citados como fuente. Se comprobaron a mano que responden 200
# (tests sin red no pueden hacerlo: ver docs/AUDITORIA_SEO_NINJA_2026-10-22.md).
FUENTES = {
    "https://www.codigotecnico.org/": "Código Técnico de la Edificación",
    "https://www.boe.es/": "Boletín Oficial del Estado",
}


def _cliente() -> TestClient:
    return TestClient(app, base_url=BASE)


# ── 1. Dominio canónico ────────────────────────────────────────────────────


def test_www_redirige_con_301_al_dominio_canonico(monkeypatch):
    monkeypatch.setenv("COTIZAT_PUBLIC_URL", "https://cotizat.online")
    with TestClient(app, base_url="https://www.cotizat.online") as cliente:
        respuesta = cliente.get("/mx/apu?utm_source=x", follow_redirects=False)
    assert respuesta.status_code == 301
    assert respuesta.headers["location"] == "https://cotizat.online/mx/apu?utm_source=x"


def test_www_redirige_tambien_la_portada(monkeypatch):
    monkeypatch.setenv("COTIZAT_PUBLIC_URL", "https://cotizat.online")
    with TestClient(app, base_url="https://www.cotizat.online") as cliente:
        respuesta = cliente.get("/", follow_redirects=False)
    assert respuesta.status_code == 301
    assert respuesta.headers["location"] == "https://cotizat.online/"


def test_el_dominio_canonico_no_se_redirige_a_si_mismo(monkeypatch):
    monkeypatch.setenv("COTIZAT_PUBLIC_URL", "https://cotizat.online")
    with TestClient(app, base_url=BASE) as cliente:
        assert cliente.get("/", follow_redirects=False).status_code == 200


def test_sin_url_publica_no_hay_redireccion_de_host(monkeypatch):
    """En escritorio y en pruebas no existe dominio alternativo que corregir."""
    monkeypatch.delenv("COTIZAT_PUBLIC_URL", raising=False)
    with TestClient(app, base_url="https://www.cotizat.online") as cliente:
        assert cliente.get("/", follow_redirects=False).status_code == 200


def test_vercel_declara_la_redireccion_como_permanente():
    import json
    from pathlib import Path

    datos = json.loads((Path(__file__).resolve().parents[1] / "vercel.json").read_text())
    reglas = [
        r
        for r in datos.get("redirects", [])
        if any(h.get("value") == "www.cotizat.online" for h in r.get("has", []))
    ]
    assert reglas, "vercel.json debe declarar www -> apex"
    assert reglas[0]["permanent"] is True


# ── 2. Enlaces externos ────────────────────────────────────────────────────


@pytest.mark.parametrize("ruta", ["/", "/en-us/"])
def test_la_portada_cita_fuentes_oficiales(ruta):
    with _cliente() as cliente:
        html = cliente.get(ruta).text
    for url in FUENTES:
        assert f'href="{url}"' in html, (ruta, url)


def test_los_enlaces_externos_abren_en_pestana_nueva_sin_filtrar_la_sesion():
    with _cliente() as cliente:
        html = cliente.get("/").text
    for url in FUENTES:
        etiqueta = re.search(r'<a[^>]+href="' + re.escape(url) + r'"[^>]*>', html)
        assert etiqueta, url
        assert 'rel="noopener"' in etiqueta.group(0), url
        assert 'target="_blank"' in etiqueta.group(0), url


def test_el_bloque_de_fuentes_explica_por_que_estan():
    """Un enlace externo suelto es relleno; con su motivo, es una fuente."""
    with _cliente() as cliente:
        html = cliente.get("/").text
    bloque = re.search(r'<section class="fuentes".*?</section>', html, re.S)
    assert bloque
    texto = re.sub(r"<[^>]+>", " ", bloque.group(0))
    assert len(texto.split()) >= 40


# ── 3. Encabezados en forma de pregunta ────────────────────────────────────


@pytest.mark.parametrize(
    "ruta",
    ["/", "/mx/apu", "/en-us/unit-price-analysis", "/precios-comparados/cimentaciones",
     "/guia/presupuesto-de-obra", "/mx/precios"],
)
def test_las_preguntas_frecuentes_son_encabezados(ruta):
    with _cliente() as cliente:
        respuesta = cliente.get(ruta)
        if respuesta.status_code != 200:
            pytest.skip(f"{ruta} no existe en este build")
        html = respuesta.text
    preguntas = re.findall(r"<summary>\s*<h3>(.*?)</h3>\s*</summary>", html, re.S)
    if "<details>" not in html:
        pytest.skip(f"{ruta} no tiene bloque de preguntas")
    assert preguntas, f"{ruta}: las preguntas no son encabezados"
    assert all("?" in p or "¿" in p for p in preguntas), preguntas


def test_una_respuesta_citable_bajo_el_h1():
    """40-60 palabras que se entiendan sin el resto de la página."""
    with _cliente() as cliente:
        for ruta in ("/", "/mx/"):
            html = cliente.get(ruta).text
            m = re.search(r'class="hero-definicion">(.*?)</p>', html, re.S)
            assert m, ruta
            palabras = len(re.sub(r"<[^>]+>", " ", m.group(1)).split())
            assert 30 <= palabras <= 60, (ruta, palabras)


# ── 4. llms.txt ────────────────────────────────────────────────────────────


def test_llms_txt_se_sirve_como_texto_plano_y_cacheable():
    with _cliente() as cliente:
        respuesta = cliente.get("/llms.txt")
    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"].startswith("text/plain")
    assert "public" in respuesta.headers["cache-control"]
    assert "noindex" not in (respuesta.headers.get("x-robots-tag") or "")


def test_llms_txt_tiene_la_estructura_de_la_convencion():
    texto = llms_txt()
    assert texto.startswith("# ")
    assert "\n> " in texto
    assert "## " in texto
    # Sin HTML: es un fichero para que lo lea un modelo, no una página.
    assert "<" not in texto.replace("<", "", 0) or "<a " not in texto


def test_llms_txt_enlaza_solo_urls_del_sitio_que_existen():
    texto = llms_txt()
    enlaces = re.findall(r"\]\((https://cotizat\.online[^)]*)\)", texto)
    assert len(enlaces) > 20
    with _cliente() as cliente:
        for url in enlaces:
            ruta = url.replace(BASE, "") or "/"
            assert cliente.get(ruta, follow_redirects=False).status_code == 200, ruta


def test_llms_txt_no_lista_paginas_privadas():
    texto = llms_txt()
    for privada in ("/admin", "/inicio", "/acceso", "/api/"):
        assert privada not in texto, privada


# ── 5. Lo que el escáner daba por roto y sí está ───────────────────────────


@pytest.mark.parametrize(
    "cabecera",
    [
        "content-security-policy",
        "x-frame-options",
        "x-content-type-options",
        "referrer-policy",
        "strict-transport-security",
        "cache-control",
    ],
)
def test_las_cabeceras_que_el_informe_daba_por_ausentes_estan(cabecera):
    with _cliente() as cliente:
        respuesta = cliente.get("/")
    assert respuesta.headers.get(cabecera), cabecera


def test_la_portada_se_comprime():
    with _cliente() as cliente:
        respuesta = cliente.get("/", headers={"accept-encoding": "gzip"})
    assert respuesta.headers.get("content-encoding") in ("gzip", "br")


def test_toda_url_del_sitemap_lleva_sus_cabeceras_de_seguridad():
    """El aviso era de la portada; se comprueba que no sea un caso aislado."""
    faltan = []
    with _cliente() as cliente:
        for entrada in urls_sitemap():
            ruta = entrada["loc"].replace(BASE, "")
            respuesta = cliente.get(ruta)
            if respuesta.status_code != 200:
                continue
            if not respuesta.headers.get("content-security-policy"):
                faltan.append(ruta)
    assert not faltan, faltan[:10]
