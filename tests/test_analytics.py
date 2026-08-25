"""Pruebas del módulo de medición de audiencia (GA4)."""
from __future__ import annotations

from app import analytics


def test_sin_id_configurado_no_hay_extras(monkeypatch):
    monkeypatch.delenv("COTIZAT_GA_ID", raising=False)
    monkeypatch.delenv("GA_MEASUREMENT_ID", raising=False)
    monkeypatch.delenv("GOOGLE_ANALYTICS_ID", raising=False)
    monkeypatch.delenv("VERCEL_ENV", raising=False)
    monkeypatch.delenv("COTIZAT_ENV", raising=False)
    assert analytics.ga_measurement_id() == ""
    assert analytics.csp_script_src_extra() == ""
    assert analytics.csp_img_src_extra() == ""
    assert analytics.csp_connect_src_extra() == ""


def test_id_ga4_valido(monkeypatch):
    monkeypatch.setenv("COTIZAT_GA_ID", "G-ABCDEF1234")
    assert analytics.ga_measurement_id() == "G-ABCDEF1234"
    assert "googletagmanager.com" in analytics.csp_script_src_extra()
    assert "*.googletagmanager.com" in analytics.csp_script_src_extra()
    assert "google-analytics.com" in analytics.csp_connect_src_extra()
    assert "*.google-analytics.com" in analytics.csp_connect_src_extra()
    assert "google-analytics.com" in analytics.csp_img_src_extra()
    assert "googletagmanager.com" in analytics.csp_img_src_extra()


def test_otros_prefijos_validos(monkeypatch):
    for pid in ("GT-AB12CD", "AW-1234567", "UA-123456-1"):
        monkeypatch.setenv("COTIZAT_GA_ID", pid)
        assert analytics.ga_measurement_id() == pid


def test_id_invalido_no_rompe_csp_ni_js(monkeypatch):
    monkeypatch.delenv("VERCEL_ENV", raising=False)
    monkeypatch.delenv("COTIZAT_ENV", raising=False)
    # Un valor con comillas o HTML jamás debe llegar a la plantilla ni a CSP.
    for pid in ('G-X\\");alert(1)//', "<script>", "", "   ", "G-", "XX-123"):
        monkeypatch.setenv("COTIZAT_GA_ID", pid)
        assert analytics.ga_measurement_id() == "", pid
        assert analytics.csp_script_src_extra() == ""
        assert analytics.csp_img_src_extra() == ""
        assert analytics.csp_connect_src_extra() == ""


def test_espacios_extremos_se_limpian(monkeypatch):
    monkeypatch.setenv("COTIZAT_GA_ID", "  G-PRUEBA1234  ")
    assert analytics.ga_measurement_id() == "G-PRUEBA1234"


def test_comillas_y_snippet_pegado_extraen_el_id(monkeypatch):
    monkeypatch.setenv("COTIZAT_GA_ID", '"G-013NT3ZTHP"')
    assert analytics.ga_measurement_id() == "G-013NT3ZTHP"
    monkeypatch.setenv(
        "COTIZAT_GA_ID",
        "https://www.googletagmanager.com/gtag/js?id=G-013NT3ZTHP",
    )
    assert analytics.ga_measurement_id() == "G-013NT3ZTHP"


def test_alias_de_variable(monkeypatch):
    monkeypatch.delenv("COTIZAT_GA_ID", raising=False)
    monkeypatch.delenv("VERCEL_ENV", raising=False)
    monkeypatch.delenv("COTIZAT_ENV", raising=False)
    monkeypatch.setenv("GA_MEASUREMENT_ID", "G-ALIAS12345")
    assert analytics.ga_measurement_id() == "G-ALIAS12345"
    monkeypatch.delenv("GA_MEASUREMENT_ID", raising=False)
    monkeypatch.setenv("GOOGLE_ANALYTICS_ID", "G-OTRO123456")
    assert analytics.ga_measurement_id() == "G-OTRO123456"


def test_en_produccion_usa_el_id_publico_si_falta_la_variable(monkeypatch):
    monkeypatch.delenv("COTIZAT_GA_ID", raising=False)
    monkeypatch.delenv("GA_MEASUREMENT_ID", raising=False)
    monkeypatch.delenv("GOOGLE_ANALYTICS_ID", raising=False)
    monkeypatch.setenv("VERCEL_ENV", "production")
    assert analytics.ga_measurement_id() == analytics.ID_PRODUCCION
    assert "googletagmanager.com" in analytics.csp_script_src_extra()


def test_off_apaga_incluso_en_produccion(monkeypatch):
    monkeypatch.setenv("VERCEL_ENV", "production")
    monkeypatch.setenv("COTIZAT_GA_ID", "off")
    assert analytics.ga_measurement_id() == ""
    assert analytics.csp_script_src_extra() == ""


# ── Integración: etiqueta en el HTML y apertura mínima de CSP ────────────────

def _cabecera_csp(respuesta) -> str:
    return respuesta.headers.get("content-security-policy", "")


def test_sin_id_no_se_renderiza_nada(monkeypatch, cliente_web):
    monkeypatch.delenv("COTIZAT_GA_ID", raising=False)
    monkeypatch.delenv("GA_MEASUREMENT_ID", raising=False)
    monkeypatch.delenv("GOOGLE_ANALYTICS_ID", raising=False)
    monkeypatch.delenv("VERCEL_ENV", raising=False)
    monkeypatch.delenv("COTIZAT_ENV", raising=False)
    r = cliente_web.get("/", follow_redirects=True)
    assert r.status_code == 200
    assert "googletagmanager.com" not in r.text
    csp = _cabecera_csp(r)
    assert "googletagmanager.com" not in csp
    assert "google-analytics.com" not in csp


def test_con_id_se_renderiza_la_etiqueta_y_se_abre_csp(monkeypatch, cliente_web):
    monkeypatch.setenv("COTIZAT_GA_ID", "G-TESTAB1234")
    r = cliente_web.get("/", follow_redirects=True)
    assert r.status_code == 200
    assert "https://www.googletagmanager.com/gtag/js?id=G-TESTAB1234" in r.text
    assert "gtag('config', 'G-TESTAB1234')" in r.text
    assert "<!-- Google tag (gtag.js) -->" in r.text
    csp = _cabecera_csp(r)
    assert "https://www.googletagmanager.com" in csp
    assert "https://www.google-analytics.com" in csp
    assert "https://*.google-analytics.com" in csp
    # Pixel de respaldo: img-src tiene que abrir los mismos hosts.
    img = csp.split("img-src ", 1)[1].split(";", 1)[0]
    assert "https://www.google-analytics.com" in img
    assert "https://*.googletagmanager.com" in img
    # La etiqueta en línea lleva el atributo nonce de la CSP.
    assert 'nonce="' in r.text


def test_etiqueta_va_al_principio_del_head(monkeypatch, cliente_web):
    """El detector de Google recorre los primeros KB: no puede ir tras el CSS."""
    monkeypatch.setenv("COTIZAT_GA_ID", "G-TESTAB1234")
    r = cliente_web.get("/", follow_redirects=True)
    head = r.text.split("</head>", 1)[0]
    pos_gtag = head.find("googletagmanager.com/gtag/js")
    pos_css_critico = head.find("<style")
    assert pos_gtag > 0
    assert pos_gtag < pos_css_critico
    # Una sola etiqueta, no duplicada por _seo_head.
    assert head.count("gtag/js?id=G-TESTAB1234") == 1


def test_id_invalido_no_renderiza_ni_abre(monkeypatch, cliente_web):
    monkeypatch.delenv("VERCEL_ENV", raising=False)
    monkeypatch.delenv("COTIZAT_ENV", raising=False)
    monkeypatch.setenv("COTIZAT_GA_ID", 'G-X\\");alert(1)//')
    r = cliente_web.get("/", follow_redirects=True)
    assert r.status_code == 200
    assert "googletagmanager.com" not in r.text
    assert "googletagmanager.com" not in _cabecera_csp(r)


# ── Eventos de conversión de un solo uso ─────────────────────────────────────

def test_encolar_evento_exige_ga_y_catalogo(monkeypatch):
    from fastapi import Response

    monkeypatch.delenv("COTIZAT_GA_ID", raising=False)
    monkeypatch.delenv("GA_MEASUREMENT_ID", raising=False)
    monkeypatch.delenv("GOOGLE_ANALYTICS_ID", raising=False)
    monkeypatch.delenv("VERCEL_ENV", raising=False)
    monkeypatch.delenv("COTIZAT_ENV", raising=False)
    r = Response()
    assert not analytics.encolar_evento_ga(r, "sign_up")
    assert "set-cookie" not in r.headers

    monkeypatch.setenv("COTIZAT_GA_ID", "G-TESTAB1234")
    r = Response()
    assert not analytics.encolar_evento_ga(r, "evento_inventado")
    assert "set-cookie" not in r.headers

    for nombre in ("sign_up", "login", "purchase"):
        r = Response()
        assert analytics.encolar_evento_ga(r, nombre)
        assert f"{analytics.GA_COOKIE_EVENTO}={nombre}" in r.headers["set-cookie"]


def test_evento_pendiente_valida_catalogo():
    assert analytics.evento_pendiente({"cotizat_ga_evento": "login"}) == "login"
    assert analytics.evento_pendiente({"cotizat_ga_evento": "no_existo"}) == ""
    assert analytics.evento_pendiente({}) == ""
    assert analytics.evento_pendiente(None) == ""


def test_purchase_solo_se_encola_una_vez(monkeypatch):
    from fastapi import Request, Response

    monkeypatch.setenv("COTIZAT_GA_ID", "G-TESTAB1234")
    scope = {"type": "http", "method": "GET", "path": "/pago/stripe/exito",
             "headers": [], "query_string": b"", "server": ("test", 443),
             "scheme": "https"}
    request = Request(scope)

    r1 = Response()
    assert analytics.encolar_purchase_unico(request, r1)
    cabeceras = [
        v.decode("latin-1") for k, v in r1.headers.raw
        if k.lower() == b"set-cookie"
    ]
    assert any(analytics.GA_MARCADOR_PURCHASE in c for c in cabeceras)
    assert any(analytics.GA_COOKIE_EVENTO in c for c in cabeceras)

    # Segunda visita con el marcador ya puesto: no se vuelve a contar.
    scope["headers"] = [(b"cookie", b"cotizat_ga_purchase=1")]
    request2 = Request(scope)
    r2 = Response()
    assert not analytics.encolar_purchase_unico(request2, r2)


def test_evento_servidor_se_emite_y_la_cookie_se_borra(monkeypatch, cliente_web):
    monkeypatch.setenv("COTIZAT_GA_ID", "G-TESTAB1234")
    r = cliente_web.get(
        "/",
        headers={"Cookie": "cotizat_ga_evento=sign_up"},
        follow_redirects=True,
    )
    assert r.status_code == 200
    assert "gtag('event', \"sign_up\")" in r.text
    borrados = [
        v.decode("latin-1") for k, v in r.headers.raw
        if k.lower() == b"set-cookie"
    ]
    assert any(
        "cotizat_ga_evento=" in c and "Max-Age=0" in c for c in borrados
    ), borrados


def test_sin_evento_encolado_no_se_emite_nada(monkeypatch, cliente_web):
    monkeypatch.setenv("COTIZAT_GA_ID", "G-TESTAB1234")
    r = cliente_web.get("/", follow_redirects=True)
    assert r.status_code == 200
    assert "gtag('event'" not in r.text
    assert "js/ga_eventos.js" in r.text  # el medidor de clics sí se carga


def test_evento_desconocido_no_se_emite(monkeypatch, cliente_web):
    monkeypatch.setenv("COTIZAT_GA_ID", "G-TESTAB1234")
    r = cliente_web.get(
        "/",
        headers={"Cookie": 'cotizat_ga_evento=";alert(1)//'},
        follow_redirects=True,
    )
    assert r.status_code == 200
    assert "gtag('event'" not in r.text
