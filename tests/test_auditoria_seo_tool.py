"""Herramienta de auditoría SEO: las comprobaciones que son lógica pura.

La herramienta habla por HTTP con el origen desplegado, así que la batería
normal (sin red) no puede ejecutarla de punta a punta. Lo que sí se prueba
aquí es la parte que decide: el muestreo del sitemap, la lectura del
``robots.txt`` y la detección de un cortafuegos de borde delante de
Googlebot. Un fallo en esas tres deja la auditoría en verde con el sitio
bloqueado, que es justo el incidente que la herramienta existe para evitar.
"""
from __future__ import annotations

from tools import auditar_seo_produccion as aud


def test_muestrear_reparte_por_toda_la_lista():
    """La muestra no puede quedarse con la primera letra del catálogo."""
    urls = [f"https://cotizat.online/es/precios/{i}" for i in range(100)]
    muestra = aud.muestrear(urls, 10)
    assert len(muestra) == 10
    assert len(set(muestra)) == 10
    assert muestra[0] == urls[0]
    assert int(muestra[-1].rsplit("/", 1)[1]) > 80


def test_muestrear_sin_limite_devuelve_todo():
    urls = ["https://cotizat.online/", "https://cotizat.online/es/"]
    assert aud.muestrear(urls, 0) == urls
    assert aud.muestrear(urls, 25) == urls


def test_locs_y_deteccion_de_indice():
    indice = (
        '<?xml version="1.0"?><sitemapindex xmlns="http://www.sitemaps.org/schemas/'
        'sitemap/0.9"><sitemap><loc>https://cotizat.online/sitemap.xml</loc></sitemap>'
        "</sitemapindex>"
    )
    urlset = (
        '<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        "<url><loc>https://cotizat.online/es/</loc></url></urlset>"
    )
    assert aud.es_indice(indice) is True
    assert aud.es_indice(urlset) is False
    assert aud.locs_del_xml(indice) == ["https://cotizat.online/sitemap.xml"]
    assert aud.locs_del_xml(urlset) == ["https://cotizat.online/es/"]


def test_robots_de_produccion_no_es_un_fallo():
    """El índice como única referencia es la forma prevista, no un error."""
    cuerpo = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /admin\n"
        "\n"
        "Sitemap: https://cotizat.online/sitemap_index.xml\n"
    )
    problemas, sitemaps = aud.problemas_de_robots(cuerpo, "https://cotizat.online")
    assert problemas == []
    assert len(sitemaps) == 1
    # Y seguir tolerando quien declare varios sitemaps propios (formato antiguo).
    cuerpo_varios = cuerpo + "Sitemap: https://cotizat.online/sitemap.xml\n"
    problemas_varios, _ = aud.problemas_de_robots(
        cuerpo_varios, "https://cotizat.online"
    )
    assert problemas_varios == []


def test_robots_que_bloquea_todo_el_sitio():
    problemas, _sitemaps = aud.problemas_de_robots(
        "User-agent: *\nDisallow: /\n\nSitemap: https://cotizat.online/sitemap.xml\n",
        "https://cotizat.online",
    )
    assert any("bloquea todo" in p for p in problemas)


def test_robots_con_sitemap_de_otro_dominio():
    problemas, _sitemaps = aud.problemas_de_robots(
        "User-agent: *\nAllow: /\nSitemap: https://otro.example/sitemap.xml\n",
        "https://cotizat.online",
    )
    assert any("otro origen" in p for p in problemas)
    assert any("no anuncia /sitemap.xml" in p for p in problemas)


def test_robots_sin_sitemap():
    problemas, sitemaps = aud.problemas_de_robots("User-agent: *\nAllow: /\n", "https://x.test")
    assert sitemaps == []
    assert any("no declara ningún Sitemap" in p for p in problemas)


def test_sonda_googlebot_detecta_el_challenge_del_borde(monkeypatch):
    """Un 200 con «Vercel Security Checkpoint» es un bloqueo, no una página."""

    def pedir_falso(url, timeout, agente=aud.AGENTE):
        assert agente == aud.AGENTE_GOOGLEBOT
        return (
            200,
            {"Content-Type": "text/html; charset=utf-8"},
            "<html><body>Vercel Security Checkpoint</body></html>",
            url,
            [],
        )

    monkeypatch.setattr(aud, "pedir", pedir_falso)
    problemas = aud.sonda_googlebot("https://cotizat.online", ["https://cotizat.online/"], 5)
    assert any("verificación" in p and "WAF" in p for p in problemas)


def test_sonda_googlebot_detecta_un_403(monkeypatch):
    def pedir_falso(url, timeout, agente=aud.AGENTE):
        return 403, {"Content-Type": "text/html"}, "Forbidden", url, []

    monkeypatch.setattr(aud, "pedir", pedir_falso)
    problemas = aud.sonda_googlebot("https://cotizat.online", ["https://cotizat.online/"], 5)
    assert any("HTTP 403" in p for p in problemas)


def test_sonda_googlebot_no_denuncia_una_pagina_normal(monkeypatch):
    def pedir_falso(url, timeout, agente=aud.AGENTE):
        return (
            200,
            {"Content-Type": "text/html; charset=utf-8"},
            "<html><head><title>CotizaT</title></head><body>ok</body></html>",
            url,
            [],
        )

    monkeypatch.setattr(aud, "pedir", pedir_falso)
    assert aud.sonda_googlebot("https://cotizat.online", ["https://cotizat.online/"], 5) == []
