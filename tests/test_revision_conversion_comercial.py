"""Contratos entre los anuncios comerciales, el alta y el cobro real."""
import re

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.datos_pago import PLANES
from app.seo import jsonld_software
from app.services import stripe


@pytest.mark.parametrize('ruta', ['/', '/?diseno=clasico', '/es/', '/mx/', '/en-us/', '/pago?pais=ES', '/pago?pais=MX', '/en/pago?pais=ES'])
def test_precios_visibles_son_los_del_cobro_y_no_prometen_un_segundo_precio(ruta):
    with TestClient(app, base_url='https://cotizat.test') as c:
        r = c.get(ruta)
    assert r.status_code == 200
    bloque = re.search(r'<div class="precios">(.*?)</div>\s*</section>', r.text, re.S)
    assert bloque
    texto = bloque.group(1)
    for plan in ('anual', 'mensual'):
        cantidad = f"{PLANES[plan]['importe']:.2f}"
        assert cantidad in texto or cantidad.replace('.', ',') in texto
    assert ' US$' in texto
    assert ' €' not in texto
    assert 'primer año' not in texto and 'first year' not in texto
    assert 'precio habitual' not in texto and 'regular price' not in texto


def test_schema_y_stripe_usan_el_mismo_importe(monkeypatch):
    monkeypatch.setitem(PLANES['anual'], 'importe', 91.25)
    datos = {}
    monkeypatch.setattr(stripe, '_llamar_stripe', lambda metodo, ruta, carga: datos.update(carga) or {'id': 'cs_test', 'url': 'https://checkout.stripe.test/session'})
    stripe.crear_sesion_checkout(plan='anual', organizacion_id=1, compra_id=0, email='x@example.test', success_url='https://example.test/s', cancel_url='https://example.test/c')
    assert datos['line_items'][0]['price_data']['currency'] == 'usd'
    assert datos['line_items'][0]['price_data']['unit_amount'] == 9125
    assert jsonld_software()['offers']['price'] == '91.25'
    with TestClient(app) as c:
        assert '91,25 US$' in c.get('/pago?pais=ES').text


@pytest.mark.parametrize('ruta', ['/acceso', '/en/acceso'])
def test_alta_prioritaria_sin_javascript_y_login_conservado(ruta):
    with TestClient(app) as c:
        alta = c.get(ruta + '?alta=1&pais=CO&origen=software_comercial').text
        login = c.get(ruta).text
    assert alta.index('action="/registro"') < alta.index('action="/acceso"')
    assert login.index('action="/acceso"') < login.index('action="/registro"')
    assert re.search(r'<option value="CO"\s+selected', alta)
    assert 'name="origen" value="software_comercial"' in alta
    assert re.search(r'class="btn btn-primary btn-block" type="submit"[^>]*>[^<]*(Crear|Create)', alta)


@pytest.mark.parametrize('ruta', ['/pago', '/en/pago'])
def test_pago_no_promete_tarjeta_sin_stripe(ruta, monkeypatch):
    from app.routers.common import TEMPLATES
    monkeypatch.setitem(TEMPLATES.env.globals, 'stripe_disponible', lambda: False)
    with TestClient(app) as c:
        html = c.get(ruta).text
    assert 'La tarjeta activa el plan' not in html
    assert 'A card activates the plan' not in html
    assert 'instant activation' not in html
    assert '<noscript><link rel="stylesheet"' in html


def test_menu_movil_enlaza_a_los_planes_y_no_a_rutas_inexistentes():
    with TestClient(app) as c:
        es = c.get('/').text
        en = c.get('/en-us/').text
    assert 'href="/pago">Precios y planes' in es
    assert 'href="/en/pago">Pricing and plans' in en
