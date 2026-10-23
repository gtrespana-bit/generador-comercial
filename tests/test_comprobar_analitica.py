"""La página de autodiagnóstico de GA4.

Existió porque el informe *Tiempo real* de GA4 no mostraba la visita del propio
titular mientras la etiqueta sí viajaba en el HTML. Desde fuera solo se puede
comprobar que la etiqueta **se sirve**; lo que pasa en el navegador (bloqueador,
DNS privado, violación de CSP) no lo ve nadie desde el servidor.

Lo que estas pruebas protegen es lo que la página necesita para servir de algo:
que se renderice con el ID real, que la etiqueta esté completa y que no se
indexe ni se cachee como una página pública más.
"""
from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from app.main import app

RUTA = "/comprobar-analitica"


def _cliente() -> TestClient:
    return TestClient(app, base_url="https://cotizat.online")


def test_la_pagina_responde_y_no_es_indexable():
    with _cliente() as cliente:
        respuesta = cliente.get(RUTA)
    assert respuesta.status_code == 200
    assert "noindex" in (respuesta.headers.get("x-robots-tag") or "")
    assert 'name="robots"' in respuesta.text
    assert "noindex" in respuesta.text.split('name="robots"')[1][:60]


def test_no_se_cachea_como_una_pagina_publica():
    """Un diagnóstico no puede servirse desde el CDN a otro visitante."""
    from app.cache_publico import es_ruta_publica_cacheable

    assert not es_ruta_publica_cacheable(RUTA)
    with _cliente() as cliente:
        respuesta = cliente.get(RUTA)
    assert respuesta.headers.get("cache-control") is None


def test_con_ga_configurado_renderiza_la_etiqueta_completa(monkeypatch):
    monkeypatch.setenv("COTIZAT_GA_ID", "G-TEST12345")
    with _cliente() as cliente:
        respuesta = cliente.get(RUTA)
    html = respuesta.text
    # La etiqueta que se va a diagnosticar tiene que ser la misma que la del
    # sitio; si falta, la página diría «todo bien» sin haber probado nada.
    assert "gtag/js?id=G-TEST12345" in html
    assert "gtag('config', 'G-TEST12345')" in html
    assert "G-TEST12345" in html  # el ID se muestra en la tabla
    # Los hosts abiertos en la CSP se enseñan para poder compararlos con lo
    # que diga el navegador.
    assert "googletagmanager.com" in html


def test_sin_ga_avisa_en_vez_de_mentir(monkeypatch):
    monkeypatch.setenv("COTIZAT_GA_ID", "off")
    with _cliente() as cliente:
        respuesta = cliente.get(RUTA)
    assert respuesta.status_code == 200
    assert "GA está apagado" in respuesta.text
    assert "gtag/js?id=" not in respuesta.text


def test_todos_los_script_y_estilos_llevan_el_mismo_nonce(monkeypatch):
    """La CSP es estricta: un script sin nonce no se ejecuta y el diagnóstico
    se quedaría mudo justo en el caso que tiene que detectar."""
    monkeypatch.setenv("COTIZAT_GA_ID", "G-TEST12345")
    with _cliente() as cliente:
        respuesta = cliente.get(RUTA)
    nonces = set(re.findall(r'nonce="([^"]+)"', respuesta.text))
    assert len(nonces) == 1, "hay scripts o estilos con nonces distintos"
    cabecera = respuesta.headers.get("content-security-policy") or ""
    assert next(iter(nonces)) in cabecera


def test_sin_manejadores_en_linea(monkeypatch):
    """Nada de `onclick=` ni `style=`: la CSP los bloquea y el proyecto no los usa."""
    with _cliente() as cliente:
        html = cliente.get(RUTA).text
    assert not re.search(r"\son[a-z]+\s*=", html)
    assert not re.search(r"\sstyle\s*=", html)


@pytest.mark.parametrize("marca", ["securitypolicyviolation", "ga_diagnostico", "_ga"])
def test_el_diagnostico_mide_lo_que_hace_falta(marca):
    """Los tres indicios que separan «no carga» de «carga y no cuenta»."""
    with _cliente() as cliente:
        html = cliente.get(RUTA).text
    assert marca in html


# ── Estado en /readyz ────────────────────────────────────────────────────────

def test_readyz_informa_del_estado_de_ga(monkeypatch):
    """El operador tiene que poder ver si GA está apagado sin mirar el HTML."""
    from app.health import _check_analitica

    monkeypatch.setenv("COTIZAT_GA_ID", "G-TEST12345")
    texto, error = _check_analitica()
    assert error is None
    assert "G-TEST12345" in texto
    assert "googletagmanager.com" in texto


def test_readyz_no_falla_por_tener_ga_apagado(monkeypatch):
    from app.health import _check_analitica

    monkeypatch.setenv("COTIZAT_GA_ID", "off")
    monkeypatch.delenv("VERCEL_ENV", raising=False)
    texto, error = _check_analitica()
    assert error is None
    assert texto.startswith("off")


# ── La prueba de salida (lo que separa «sitio roto» de «propiedad rota») ─────

def test_la_pagina_prueba_la_salida_de_los_hits(monkeypatch):
    """Sin esta prueba la página diría «todo bien» aunque no saliera un solo hit.

    Es la comprobación que decide el caso: si los hits salen con el `tid`
    correcto, el problema está en la propiedad de GA4 y no en el código.
    """
    monkeypatch.setenv("COTIZAT_GA_ID", "G-TEST12345")
    with _cliente() as cliente:
        html = cliente.get(RUTA).text
    assert "/g/collect" in html
    assert "ga_diag_fetch" in html  # hit propio, independiente de gtag
    assert "hitsSalientes" in html
    assert "client_id de esta visita" in html


def test_la_pagina_permite_copiar_el_informe(monkeypatch):
    """El titular no tiene terminal: el informe se copia y se pega en una consulta."""
    monkeypatch.setenv("COTIZAT_GA_ID", "G-TEST12345")
    with _cliente() as cliente:
        html = cliente.get(RUTA).text
    assert 'id="copiar"' in html
    assert "clipboard" in html
    assert 'id="informe"' in html


def test_explica_donde_comparar_el_id_de_medicion(monkeypatch):
    """La causa más probable es mirar otra propiedad: hay que decirlo con la ruta."""
    with _cliente() as cliente:
        html = cliente.get(RUTA).text
    assert "Flujos de datos" in html
    assert "DebugView" in html
    assert "ID de medición" in html
