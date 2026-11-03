"""Landing «Impulso»: variante de conversión y su medición.

El rediseño no sustituye a ciegas la portada anterior: convive con ella
bajo ``?diseno=clasico`` para poder comparar, y cada CTA declara de forma
explícita la variante, la intención y el mercado de la visita. Estas
pruebas fijan ese contrato sin depender de JavaScript en el cliente.
"""
from __future__ import annotations

import re

from fastapi.testclient import TestClient

from app.main import app
from app.services import atribucion


def _cliente():
    return TestClient(app, base_url="https://cotizat.test")


def test_la_portada_sirve_impulso_por_defecto():
    with _cliente() as client:
        r = client.get("/")
    assert r.status_code == 200
    assert "landing-impulso" in r.text
    assert "Deja de adivinar" in r.text
    assert "Quiero mi primer presupuesto hoy" in r.text
    assert "origen=landing_impulso" in r.text


def test_la_variante_clasica_sigue_disponible_y_no_compite_en_el_indice():
    with _cliente() as client:
        nueva = client.get("/").text
        clasica = client.get("/?diseno=clasico").text
    assert "landing-impulso" not in clasica
    assert "landing-impulso" in nueva
    assert 'name="robots" content="noindex, follow"' in clasica
    assert 'name="robots" content="index,follow,max-image-preview:large"' in nueva


def test_los_mercados_en_ingles_conservan_su_plantilla_traducida():
    with _cliente() as client:
        html = client.get("/en-us/").text
    assert "landing-impulso" not in html
    assert "English-speaking markets" in html


def test_el_cta_declara_variante_intencion_pais_y_alta_directa():
    with _cliente() as client:
        html = client.get("/co/").text
    href = re.search(r'href="(/acceso\?[^"]+)"', html)
    assert href, "La landing de país no trae CTA de alta"
    URL = href.group(1).replace("&amp;", "&")
    assert "origen=landing_impulso" in URL
    assert "alta=1" in URL
    assert "variante=impulso" in URL
    assert "intencion=tiempo" in URL
    assert "pais=CO" in URL


def test_el_acceso_convierte_la_atribucion_en_campos_ocultos():
    with _cliente() as client:
        r = client.get(
            "/acceso?origen=landing_impulso&alta=1&variante=impulso&intencion=margen"
        )
    assert r.status_code == 200
    assert 'name="origen" value="landing_impulso"' in r.text
    assert 'name="variante" value="impulso"' in r.text
    assert 'name="intencion" value="margen"' in r.text
    assert "autofocus" in r.text


def test_el_acceso_descarta_variante_e_intencion_inventadas():
    with _cliente() as client:
        r = client.get("/acceso?variante=spam&intencion=lo-que-sea")
    assert 'name="variante"' not in r.text
    assert 'name="intencion"' not in r.text
    assert atribucion.normalizar_variante("IMPULSO ") == "impulso"
    assert atribucion.normalizar_intencion("inventada") == ""


def test_la_nueva_landing_conserva_los_contratos_publicos():
    with _cliente() as client:
        html = client.get("/").text
    assert 'class="plan destacado" href="/pago"' in html
    assert 'class="plan" href="/pago"' in html
    assert 'class="mercados-precios"' in html
    assert 'class="tour-slide active"' in html
    assert 'class="fuentes"' in html
    assert "Ver planes" in html
    assert "demostración" not in html.lower()
    assert "mailto:" in html
    assert html.count('class="mercado-fila') == 23


def test_los_eventos_de_conversion_estan_instrumentados():
    with _cliente() as client:
        html = client.get("/").text
    assert 'data-ga-event="cta_hero"' in html
    assert 'data-ga-event="cta_final"' in html
    assert 'data-ga-event="cta_sticky"' in html
    assert 'data-ga-event="cta_tiempos"' in html
    assert "landing_impulso.js" in html


def test_el_tiempo_de_obra_automatico_tiene_un_argumento_propio():
    """No basta con mencionar «plazo»: la landing debe explicar el cálculo
    por partida, la suma por capítulo/total y el ejemplo real de la página."""
    with _cliente() as client:
        html = client.get("/").text
    assert 'id="tiempos-obra"' in html
    assert "Tiempo de obra automático" in html
    assert "De las horas de cada partida" in html
    assert "Por capítulo y total" in html
    assert "Cantidad × horas por unidad" in html
    assert "98 h-hombre" in html
    assert "≈ 6 días" in html
    assert "cuadrilla de 2 · 1 oficial + 1 ayudante" in html
    assert "las partidas sin tiempo se señalan" in html
    assert "¿Calcula el tiempo de obra automáticamente?" in html
    assert "tiempo de obra por partida y total" in html


def test_el_mensaje_de_tiempo_sirve_tambien_en_la_landing_de_pais():
    with _cliente() as client:
        html = client.get("/co/").text
    assert 'id="tiempos-obra"' in html
    assert 'data-ga-event="cta_tiempos"' in html
    assert "¿Calcula el tiempo de obra automáticamente?" in html
