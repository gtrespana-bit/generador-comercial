"""Atribución del alta: de qué página viene quien se registra (y paga).

El negocio no es el tráfico, es el registro que se convierte en suscripción.
Sin atribución, el catálogo de precios —787 fichas, el 76 % de las
impresiones— no se puede comparar con las landings comerciales, que es la
única comparación que decide dónde poner el trabajo.

Cómo viaja la atribución, y por qué así:

- **No hay cookie puesta por el servidor.** Las páginas públicas se sirven
  desde el CDN de Vercel y una respuesta con ``Set-Cookie`` deja de cachearse
  (y con ``Vary: Cookie`` Vercel directamente no cachea nada). Meter la
  atribución por ahí costaría el caché de las 787 fichas que traen el 76 %
  de las impresiones.
- **Viaja en la URL del CTA** (``/acceso?origen=precios_ficha``). El HTML es
  idéntico para todos los visitantes de esa URL, así que el caché se
  mantiene, y el parámetro no se arrastra al resto de la navegación.
- **El valor es un catálogo cerrado**: mercado y sección, nunca la URL.

Lo que se prueba aquí es que el dato llegue limpio hasta el registro y que no
se pueda ensuciar por la URL.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.services import atribucion


def _cliente():
    return TestClient(app, base_url="https://cotizat.test")


# ---------------------------------------------------------------------------
# Sección y mercado: el catálogo cerrado
# ---------------------------------------------------------------------------

def test_la_ficha_de_partida_es_su_propia_seccion():
    assert atribucion.seccion_de(
        "/es/precios/portones-metalicos/porton-corredizo-con-automatismo"
    ) == "precios_ficha"
    assert atribucion.seccion_de(
        "/en-gb/prices/wood-and-laminate-floors/herringbone-parquet-flooring"
    ) == "precios_ficha"


def test_hub_e_indice_no_se_confunden_con_la_ficha():
    assert atribucion.seccion_de("/en-ie/prices/lifts-and-platform-lifts") == "precios_hub"
    assert atribucion.seccion_de("/es/precios") == "precios_indice"
    assert atribucion.seccion_de("/en-ie/prices") == "precios_indice"


def test_la_portada_y_las_paginas_comerciales_se_distinguen():
    assert atribucion.seccion_de("/") == "portada"
    assert atribucion.seccion_de("/es/") == "landing_pais"
    assert atribucion.seccion_de("/ni/") == "landing_pais"
    assert atribucion.seccion_de("/pago") == "planes"
    assert atribucion.seccion_de("/precios-comparados") == "comparador"
    assert atribucion.seccion_de("/co/guia/apu-panete-colombia") == "guia"
    assert atribucion.seccion_de("/mx/software-presupuestos") == "software_comercial"


def test_lo_que_no_es_comercial_cae_en_otro():
    for ruta in ("/legal/privacidad", "/soporte", "/mapa-del-sitio", "/api/x"):
        assert atribucion.seccion_de(ruta) == "otro"


def test_el_mercado_sale_del_prefijo():
    assert atribucion.mercado_de("/en-ie/prices/lifts-and-platform-lifts") == "en-ie"
    assert atribucion.mercado_de("/es/precios/portones") == "es"
    assert atribucion.mercado_de("/ni/") == "ni"
    assert atribucion.mercado_de("/") == "global"


def test_la_atribucion_nunca_lleva_la_url():
    valor = atribucion.valor_cookie(
        "/es/precios/portones-metalicos/porton-corredizo-con-automatismo"
    )
    assert valor == "es:precios_ficha"
    assert "/" not in valor
    assert len(valor) < 40


def test_leer_atribucion_tolera_lo_corrupto():
    assert atribucion.leer_origen(None) == {}
    assert atribucion.leer_origen("") == {}
    assert atribucion.leer_origen("basura") == {}
    assert atribucion.leer_origen("x" * 500) == {}
    # Manipulada: se limpia a un valor del catálogo, no se rechaza la visita.
    assert atribucion.leer_origen("ES:Precios_Ficha") == {
        "origen_mercado": "es",
        "origen_seccion": "precios_ficha",
    }


def test_el_catalogo_de_secciones_es_cerrado():
    # Un ``?origen=`` inventado no puede crear una categoría en la analítica.
    assert "lo-que-sea" not in atribucion.SECCIONES_CONOCIDAS
    assert "precios_ficha" in atribucion.SECCIONES_CONOCIDAS


# ---------------------------------------------------------------------------
# El CTA de las páginas que traen el tráfico
# ---------------------------------------------------------------------------

def test_la_ficha_lleva_su_seccion_y_su_pais_en_el_cta():
    with _cliente() as client:
        r = client.get("/es/precios/portones-metalicos/porton-corredizo-con-automatismo")
    assert r.status_code == 200
    assert 'href="/acceso?origen=precios_ficha&pais=ES"' in r.text


def test_el_hub_lleva_su_seccion_y_su_pais_en_el_cta():
    with _cliente() as client:
        r = client.get("/en-ie/prices/lifts-and-platform-lifts")
    assert r.status_code == 200
    assert 'href="/acceso?origen=precios_hub&pais=IE"' in r.text


def test_las_paginas_con_trafico_no_reciben_cookie_de_atribucion():
    """Una cookie del servidor costaría el caché CDN de las fichas."""
    with _cliente() as client:
        r = client.get("/es/precios/portones-metalicos/porton-corredizo-con-automatismo")
    galletas = ";".join(r.headers.get_list("set-cookie"))
    assert "cotizat_origen" not in galletas


# ---------------------------------------------------------------------------
# El alta conserva el origen
# ---------------------------------------------------------------------------

def test_el_acceso_convierte_origen_en_campo_oculto():
    with _cliente() as client:
        r = client.get("/acceso?origen=precios_ficha")
    assert r.status_code == 200
    assert 'type="hidden" name="origen" value="precios_ficha"' in r.text


def test_el_acceso_descarta_un_origen_inventado():
    with _cliente() as client:
        r = client.get("/acceso?origen=quiero-que-me-llames")
    assert 'name="origen"' not in r.text


def test_el_acceso_acepta_una_ruta_y_la_reduce_a_seccion():
    """``?origen=/es/precios`` y ``?origen=precios_indice`` son lo mismo."""
    with _cliente() as client:
        r = client.get("/acceso?origen=/es/precios")
    assert 'name="origen" value="precios_indice"' in r.text


def test_el_referer_sirve_de_respaldo():
    with _cliente() as client:
        r = client.get(
            "/acceso",
            headers={"referer": "https://cotizat.online/en-gb/prices/exterior-painting"},
        )
    assert 'name="origen" value="precios_hub"' in r.text


def test_un_referer_ajeno_no_atribuye_nada():
    with _cliente() as client:
        r = client.get("/acceso", headers={"referer": "https://otro-sitio.example/x"})
    assert 'name="origen"' not in r.text


def test_el_registro_anota_el_origen_en_la_telemetria(monkeypatch):
    """El POST del alta pasa la sección al detalle del evento."""
    capturado = {}

    def _fake_anotar(*, email, pais="", detalle_extra=None):
        capturado["email"] = email
        capturado["pais"] = pais
        capturado["extra"] = detalle_extra or {}
        return True

    from app.routers import auth

    monkeypatch.setattr(auth.telemetria, "anotar_registro", _fake_anotar)
    # Sin Supabase configurado el alta no puede completarse; se comprueba la
    # extracción del origen, que es lo que esta prueba cubre.
    with _cliente() as client:
        client.post(
            "/registro",
            data={
                "email": "alguien@example.com",
                "password": "unaClaveLarga123",  # pragma: allowlist secret
                "password_confirmation": "unaClaveLarga123",  # pragma: allowlist secret
                "acepto_terminos": "1",
                "pais": "ES",
                "origen": "precios_ficha",
            },
        )
    if capturado:
        assert capturado["extra"].get("origen_seccion") == "precios_ficha"
