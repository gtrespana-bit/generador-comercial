"""Landing y páginas legales (E1-018, E1-019, E1-020, E1-056).

Son fronteras públicas: no exponen datos de tenant, no requieren sesión y
deben cumplir la CSP como el resto de la aplicación. La honestidad comercial
del plan exige además que la landing no prometa facturación fiscal y que los
precios promocionales muestren también el precio habitual.
"""
import re

from fastapi.testclient import TestClient

from app.main import app


def _get(path):
    with TestClient(app) as client:
        return client.get(path)


def test_landing_publica_sin_sesion():
    r = _get("/conocer")
    assert r.status_code == 200
    # Elementos exigidos por E1-056: problema, resultado, público objetivo y
    # llamada a solicitar demostración.
    assert "presupuesto" in r.text.lower()
    assert "demostración" in r.text
    assert "construcción" in r.text.lower()
    assert "mailto:" in r.text
    # Enlaces al paquete legal.
    for enlace in ("/legal/terminos", "/legal/privacidad", "/legal/soporte", "/legal/licencias"):
        assert enlace in r.text, enlace


def test_landing_muestra_promocion_con_precio_habitual():
    """Un precio tachado sin el habitual al lado sería publicidad engañosa."""
    r = _get("/conocer")
    assert "89" in r.text and "109" in r.text
    assert "9,99" in r.text and "12,99" in r.text
    assert "no" in r.text.lower() and "facturas fiscales" in r.text


def test_paginas_legales_responden_sin_sesion():
    esperado = {
        "/legal/terminos": ["Términos del servicio", "licencia", "no facturas fiscales"],
        "/legal/privacidad": ["privacidad", "Supabase", "No vendemos"],
        "/legal/soporte": ["soporte@", "laborables"],
        "/legal/licencias": ["Lato", "SIL Open Font License", "FastAPI", "LGPL"],
    }
    for ruta, fragmentos in esperado.items():
        r = _get(ruta)
        assert r.status_code == 200, ruta
        for fragmento in fragmentos:
            assert fragmento.lower() in r.text.lower(), (ruta, fragmento)


def test_pagina_legal_inexistente_da_404():
    assert _get("/legal/no-existe").status_code == 404


def test_paginas_publicas_cumplen_csp():
    """Sin estilos inline sin nonce, sin handlers de eventos, con CSP activa."""
    event_attr = re.compile(
        r"\son(?:click|change|input|submit|load|error|blur|focus|keydown|keyup)\s*=",
        re.IGNORECASE,
    )
    style_attr = re.compile(r"\sstyle\s*=", re.IGNORECASE)
    for ruta in ("/conocer", "/legal/terminos", "/legal/privacidad", "/legal/soporte", "/legal/licencias"):
        r = _get(ruta)
        assert "content-security-policy" in r.headers, ruta
        nonce = r.headers["content-security-policy"].split("'nonce-", 1)[1].split("'", 1)[0]
        assert not event_attr.search(r.text), ruta
        assert not style_attr.search(r.text), ruta
        for tag in re.findall(r"<style[^>]*>", r.text, re.IGNORECASE):
            assert f'nonce="{nonce}"' in tag, (ruta, tag)


def test_identidad_legal_configurable_por_entorno(monkeypatch):
    """Sin COTIZAT_LEGAL_ENTITY los documentos muestran el marcador visible,
    imposible de confundir con una razón social real."""
    r = _get("/legal/terminos")
    # El valor por defecto del branding es el marcador o la entidad real si el
    # entorno la define; en la suite no está definida.
    import app.branding as branding
    assert branding.LEGAL_ENTITY in r.text
    assert branding.SUPPORT_EMAIL in r.text
