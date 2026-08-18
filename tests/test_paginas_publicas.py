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


def test_home_es_la_landing_publica():
    """La raíz («/») es la puerta de entrada pública, no el panel de trabajo."""
    r = _get("/")
    assert r.status_code == 200
    assert "presupuesto" in r.text.lower()
    assert "construcción" in r.text.lower()
    assert "/acceso" in r.text  # enlace a iniciar sesión
    assert "/pago" in r.text  # enlace a la página de planes


def test_landing_publica_sin_sesion():
    r = _get("/conocer")
    assert r.status_code == 200
    # Elementos exigidos por E1-056: problema, resultado, público objetivo y
    # llamada a solicitar demostración.
    assert "presupuesto" in r.text.lower()
    assert "construcción" in r.text.lower()
    assert "mailto:" in r.text
    assert "/pago" in r.text
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


def test_legales_explican_limites_de_enlaces_y_respuesta_declarada():
    privacidad = _get("/legal/privacidad").text.lower()
    terminos = " ".join(_get("/legal/terminos").text.lower().split())
    assert "enlace secreto" in privacidad
    assert "aceptación o rechazo" in privacidad
    assert "identidad" in privacidad and "declarad" in privacidad
    assert "firma electrónica cualificada" in terminos
    assert "no constituye" in terminos


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
    """La identidad publicada es la del branding (marca por omisión, o la
    entidad real si COTIZAT_LEGAL_ENTITY está definida en el entorno)."""
    r = _get("/legal/terminos")
    # Sin COTIZAT_LEGAL_ENTITY, el branding muestra «CotizaT · Presupuestos»
    # (decisión del titular); si el entorno define la entidad, esa es la que
    # aparece. En la suite no está definida.
    import app.branding as branding
    assert branding.LEGAL_ENTITY in r.text
    assert branding.SUPPORT_EMAIL in r.text


# ---------------------------------------------------------------------------
# Preguntas frecuentes (E1-053) y alcance del soporte (E1-054, E1-055)
# ---------------------------------------------------------------------------


def test_preguntas_frecuentes_responde_y_cubre_los_temas_decisivos():
    """La FAQ existe para resolver dudas ANTES de contratar."""
    r = _get("/legal/preguntas")
    assert r.status_code == 200
    for tema in (
        "presupuesto",      # qué es el producto
        "excel",            # importación del catálogo
        "exportar",         # poder marcharse con los datos
        "permanencia",      # compromiso de contratación
        "soporte",          # canal de ayuda
    ):
        assert tema in r.text.lower(), tema


def test_preguntas_frecuentes_no_promete_facturacion_fiscal():
    """El punto más delicado: no puede contradecir a los términos.

    Prometer facturación fiscal en la FAQ sería exactamente la promesa que el
    resto del paquete legal se cuida de no hacer.
    """
    r = _get("/legal/preguntas")
    texto = r.text.lower()
    assert "no" in texto and "factura" in texto
    # Debe declarar el alcance no fiscal de forma explícita.
    assert "documentos comerciales" in texto
    assert "no sustituyen" in texto or "no sustituye" in texto


def test_preguntas_frecuentes_declara_el_acceso_anticipado():
    """Honestidad comercial: el estado real del producto se dice por delante."""
    r = _get("/legal/preguntas")
    assert "acceso anticipado" in r.text.lower()


def test_preguntas_frecuentes_remite_a_los_documentos_vinculantes():
    """Una FAQ no es un contrato; debe decir cuál manda si hay discrepancia."""
    r = _get("/legal/preguntas")
    for enlace in ("/legal/terminos", "/legal/privacidad", "/legal/soporte"):
        assert enlace in r.text, enlace
    assert "prevalecen" in r.text.lower()


def test_la_faq_esta_enlazada_desde_la_landing_y_el_pie_legal():
    """Una FAQ que no se encuentra no resuelve ninguna duda."""
    assert "/legal/preguntas" in _get("/conocer").text
    assert "/legal/preguntas" in _get("/legal/terminos").text


def test_condiciones_de_soporte_delimitan_incluido_y_excluido():
    """E1-054: el alcance del soporte debe estar acotado por escrito.

    Sin la lista de exclusiones, cualquier expectativa es discutible: es la
    parte que evita malentendidos cuando alguien pide asesoría fiscal o que le
    carguemos el catálogo entero.
    """
    r = _get("/legal/soporte")
    texto = r.text.lower()
    assert "qué incluye" in texto and "qué no incluye" in texto
    for excluido in ("fiscal", "a medida", "hardware"):
        assert excluido in texto, excluido
    for incluido in ("configurar", "errores"):
        assert incluido in texto, incluido




def test_procedimiento_de_reporte_pide_evidencia_sin_datos_de_clientes():
    """E1-055: reportar con evidencia, pero sin exponer datos de terceros."""
    r = _get("/legal/soporte")
    texto = r.text.lower()
    assert "reportar un error" in texto
    assert "reproducirlo" in texto
    assert "sin datos personales" in texto


# ---------------------------------------------------------------------------
# Página de planes y métodos de pago
# ---------------------------------------------------------------------------


def test_pagina_pago_responde():
    """La página /pago carga correctamente sin sesión."""
    r = _get("/pago")
    assert r.status_code == 200
    assert "Pago" in r.text
    assert "plan" in r.text.lower()
    # Métodos de pago (la plantilla usa entidades HTML para las tildes)
    assert "Pago m" in r.text
    assert "Binance" in r.text
    assert "Kontigo" in r.text
    assert "USDT" in r.text
    # Planes
    assert "89" in r.text and "109" in r.text
    assert "9,99" in r.text and "12,99" in r.text


def test_pagina_pago_cumple_csp():
    """La página de pago cumple CSP como el resto."""
    import re
    r = _get("/pago")
    assert "content-security-policy" in r.headers
    event_attr = re.compile(r"\son(?:click|change|input|submit)\s*=", re.IGNORECASE)
    assert not event_attr.search(r.text)


def test_pagina_pago_tiene_enlace_a_soporte():
    r = _get("/pago")
    assert "mailto:" in r.text
    assert "/legal" in r.text
    assert "/acceso" in r.text or "Iniciar sesi" in r.text


def test_landing_planes_clickeables_a_pagina_de_pago():
    """Las tarjetas de precios de la home llevan a la página de planes."""
    r = _get("/")
    assert 'class="plan destacado" href="/pago"' in r.text
    assert 'class="plan" href="/pago"' in r.text


def test_landing_enlaza_a_pagina_de_pago():
    """La landing ya no pide demostración: enlaza directamente a planes."""
    r = _get("/")
    assert "/pago" in r.text
    assert "Ver planes" in r.text
    assert "demostración" not in r.text.lower()
