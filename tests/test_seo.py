"""SEO público: canónicas, hreflang, robots, sitemap y copy por país."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.seo import es_indexable, ficha_landing, ficha_tema, robots_txt


def _cliente():
    return TestClient(app, base_url="https://cotizat.test")


def test_home_es_generica_aunque_haya_cookie_de_pais():
    """La cookie no puede cambiar el HTML de ``/``: una URL, un contenido."""
    with _cliente() as client:
        resp = client.get("/", cookies={"cotizat_pais": "CO"})
    assert resp.status_code == 200
    assert "Latinoamérica" in resp.text
    assert "Software de presupuestos de construcción para Colombia" not in resp.text
    assert 'rel="canonical" href="https://cotizat.test/"' in resp.text
    assert 'hreflang="es-CO"' in resp.text
    assert "application/ld+json" in resp.text


def test_landing_colombia_tiene_title_h1_y_faq_propios():
    with _cliente() as client:
        resp = client.get("/co/")
    assert resp.status_code == 200
    assert "Colombia" in resp.headers.get("content-language", "") or 'lang="es-CO"' in resp.text
    assert "Software de presupuestos y APU para constructoras en Colombia" in resp.text
    assert "NIT" in resp.text
    assert 'rel="canonical" href="https://cotizat.test/co/"' in resp.text
    assert '"@type": "FAQPage"' in resp.text or '"@type":"FAQPage"' in resp.text
    assert "og:image" in resp.text


def test_co_sin_barra_redirige_a_canonica():
    with _cliente() as client:
        resp = client.get("/co", follow_redirects=False)
    assert resp.status_code == 301
    assert resp.headers["location"].endswith("/co/")


def test_hub_apu_colombia_es_unica():
    with _cliente() as client:
        resp = client.get("/co/apu")
    assert resp.status_code == 200
    assert "Análisis de precios unitarios (APU) para Colombia" in resp.text
    assert "software-presupuestos" in resp.text
    assert 'rel="canonical" href="https://cotizat.test/co/apu"' in resp.text


def test_hub_pais_invalido_404():
    with _cliente() as client:
        assert client.get("/xx/apu").status_code == 404
        assert client.get("/co/no-existe").status_code == 404


def test_robots_bloquea_el_panel_y_apunta_al_sitemap():
    with _cliente() as client:
        resp = client.get("/robots.txt")
    assert resp.status_code == 200
    assert "Disallow: /presupuestos" in resp.text
    assert "Disallow: /acceso" in resp.text
    assert "Sitemap: https://cotizat.test/sitemap.xml" in resp.text
    assert resp.headers["content-type"].startswith("text/plain")


def test_sitemap_incluye_paises_temas_y_hreflang():
    with _cliente() as client:
        resp = client.get("/sitemap.xml")
    assert resp.status_code == 200
    texto = resp.text
    for u in ("/ve/", "/co/", "/mx/", "/ec/", "/pe/", "/es/", "/co/apu", "/mx/remodelacion", "/software-presupuestos"):
        assert u in texto
    assert "xmlns:xhtml" in texto
    assert 'hreflang="es-CO"' in texto
    assert 'hreflang="es-ES"' in texto
    assert "/conocer" not in texto


def test_panel_lleva_x_robots_noindex():
    with _cliente() as client:
        resp = client.get("/inicio")
    assert resp.headers.get("x-robots-tag") == "noindex, nofollow, noarchive"


def test_landing_no_lleva_x_robots_noindex():
    with _cliente() as client:
        resp = client.get("/co/")
    assert "noindex" not in (resp.headers.get("x-robots-tag") or "")


def test_es_indexable_cubre_publicas_y_rechaza_privadas():
    assert es_indexable("/")
    assert es_indexable("/co/")
    assert es_indexable("/co/apu")
    assert es_indexable("/legal/preguntas")
    assert es_indexable("/pago")
    assert not es_indexable("/presupuestos")
    assert not es_indexable("/acceso")
    assert not es_indexable("/admin")


def test_fichas_por_pais_no_se_copian_entre_si():
    ve = ficha_landing("VE")
    co = ficha_landing("CO")
    mx = ficha_landing("MX")
    assert ve["h1"] != co["h1"] != mx["h1"]
    assert "Venezuela" in ve["title"]
    assert "Colombia" in co["title"]
    assert "México" in mx["title"]
    apu_co = ficha_tema("CO", "apu")
    apu_mx = ficha_tema("MX", "apu")
    assert apu_co["h1"] != apu_mx["h1"]
    assert robots_txt().startswith("User-agent:")


def test_guias_y_mapa_estan_indexables_y_en_sitemap():
    with _cliente() as client:
        mapa = client.get("/mapa-del-sitio")
        guia = client.get("/guia/analisis-precios-unitarios")
        sm = client.get("/sitemap.xml").text
    assert mapa.status_code == 200
    assert "/guia/presupuesto-de-obra" in mapa.text
    assert guia.status_code == 200
    assert "rendimiento" in guia.text.lower()
    assert "HowTo" in guia.text
    assert "/guia/analisis-precios-unitarios" in sm
    assert "/mapa-del-sitio" in sm
    assert client_get_404()


def client_get_404():
    with _cliente() as client:
        return client.get("/guia/no-existe").status_code == 404


def test_landing_pais_tiene_cuerpo_propio_y_faq_visible():
    with _cliente() as client:
        co = client.get("/co/").text
        mx = client.get("/mx/").text
    assert "Software de APU para constructoras en Colombia" in co
    assert "pañete" in co.lower()
    assert "Programa para cotizar obra y remodelación en México" in mx
    assert "aplanado" in mx.lower()
    assert "Lo que preguntan las empresas de Colombia" in co
    assert "FAQPage" in co


def test_paginas_estaticas_no_heredan_faq_de_la_home():
    """Cómo funciona, planes y mapa no deben publicar el FAQPage de ``/``."""
    pregunta_home = "¿CotizaT sirve para presupuestos de construcción en España y Latinoamérica?"
    with _cliente() as client:
        home = client.get("/").text
        mapa = client.get("/mapa-del-sitio").text
        pago = client.get("/pago").text
        funciona = client.get("/como-funciona").text
        terminos = client.get("/legal/terminos").text
    assert "FAQPage" in home
    assert pregunta_home in home
    assert pregunta_home not in mapa
    assert pregunta_home not in pago
    assert pregunta_home not in funciona
    assert pregunta_home not in terminos
    assert "<title>CotizaT: mapa del sitio" in mapa
    assert "<title>CotizaT: planes del software" in pago
    assert "<title>CotizaT: términos del servicio" in terminos
    assert 'rel="canonical" href="https://cotizat.test/pago"' in pago
    assert 'rel="canonical" href="https://cotizat.test/legal/terminos"' in terminos


def test_guia_howto_lleva_texto_en_los_pasos():
    with _cliente() as client:
        html = client.get("/guia/presupuesto-de-obra").text
    assert "HowToStep" in html
    assert "visor BIM" in html
    assert "Article" in html
    assert 'og:type" content="article"' in html


def test_cuerpos_de_pais_no_son_un_find_and_replace():
    from app.seo_contenido import cuerpo_pais

    titulos = {cuerpo_pais(c)[0][0] for c in ("", "VE", "CO", "MX", "PE", "EC", "ES")}
    assert len(titulos) == 7


def test_hubs_de_intencion_no_son_la_misma_pagina_con_otro_pais():
    with _cliente() as client:
        co = client.get("/co/apu").text
        mx = client.get("/mx/apu").text
        ve = client.get("/ve/software-presupuestos").text
        pe = client.get("/pe/software-presupuestos").text
    assert "AIU" in co
    assert "pañete" in co.lower()
    assert "PAC" in mx or "CFDI" in mx
    assert "bolívares" in ve.lower() or "bolivares" in ve.lower()
    assert "metrado" in pe.lower()
    assert "AIU" not in mx
    assert "friso" not in mx.lower()


def test_faq_legal_publica_schema_propio():
    with _cliente() as client:
        html = client.get("/legal/preguntas").text
    assert "FAQPage" in html
    assert "CotizaT: preguntas frecuentes del software" in html


def test_articulos_de_pais_son_unicos_y_estan_en_sitemap():
    from app.seo_articulos import ORDEN_ARTICULOS, lista_articulos

    assert len(lista_articulos()) == 5
    with _cliente() as client:
        sm = client.get("/sitemap.xml").text
        co = client.get("/guia/apu-panete-colombia")
        mx = client.get("/guia/cotizar-remodelacion-mexico")
        ve = client.get("/guia/presupuesto-usd-bs-venezuela")
        pe = client.get("/guia/metrados-peru")
        ec = client.get("/guia/apu-dolares-ecuador")
        home_co = client.get("/co/").text
    assert co.status_code == mx.status_code == ve.status_code == pe.status_code == ec.status_code == 200
    assert "pañete" in co.text.lower()
    assert "AIU" in co.text
    assert "CFDI" in mx.text
    assert "aplanado" in mx.text.lower()
    assert "tasa" in ve.text.lower()
    assert "metrado" in pe.text.lower()
    assert "SRI" in ec.text
    assert "hormigón" in ec.text.lower() or "hormigon" in ec.text.lower()
    for slug in ORDEN_ARTICULOS:
        assert f"/guia/{slug}" in sm
    assert "/guia/apu-panete-colombia" in home_co
    assert "<title>CotizaT:" in co.text


def test_titulo_empieza_por_marca_y_describe_el_oficio():
    """En Google no puede aparecer solo «CotizaT»: hay que leer qué es."""
    from app.paises import ORDEN_SELECTOR
    from app.seo import TEMAS, ficha_landing, ficha_tema, titulo_publico

    assert titulo_publico("software de presupuestos de construcción").startswith("CotizaT:")
    for codigo in [""] + list(ORDEN_SELECTOR):
        ficha = ficha_landing(codigo)
        assert ficha["title"].startswith("CotizaT:")
        assert "software" in ficha["title"].lower()
        assert "presupuesto" in ficha["title"].lower()
        for tema in TEMAS:
            hub = ficha_tema(codigo, tema)
            assert hub["title"].startswith("CotizaT:")
            assert "software" in hub["title"].lower()
