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
    for u in ("/ve/", "/co/", "/mx/", "/ec/", "/pe/", "/co/apu", "/mx/remodelacion", "/software-presupuestos"):
        assert u in texto
    assert "xmlns:xhtml" in texto
    assert 'hreflang="es-CO"' in texto
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
