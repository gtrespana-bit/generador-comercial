"""Conmutador de idioma ES/EN: rutas, cookie y presencia en la interfaz.

El conmutador no puede limitarse a enlazar ``/en/...``: al volver al español
(no lleva prefijo) la cookie seguiría en inglés y la interfaz no cambiaría. De
ahí la ruta ``/idioma/{lang}``, que escribe la cookie en los dos sentidos.
"""
import re

import pytest
from fastapi.testclient import TestClient

from app.i18n import (
    COOKIE_IDIOMA,
    codigos_pais,
    normalizar_idioma,
    partir_ruta,
    ruta_en_idioma,
    ruta_segura,
    url_cambio_idioma,
)
from app.main import app
from app.seo import es_indexable


# --------------------------------------------------------------------------
# Utilidades de ruta
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    "ruta,esperado",
    [
        ("/", ("", "/")),
        ("/apu", ("", "/apu")),
        ("/mx", ("mx", "/")),
        ("/mx/apu", ("mx", "/apu")),
        ("/es/", ("es", "/")),
        # El formato que ve el navegador, antes de que el middleware lo reescriba.
        ("/en", ("", "/")),
        ("/en/apu", ("", "/apu")),
        ("/en-mx/apu", ("mx", "/apu")),
        ("/en-es/apu", ("es", "/apu")),
        # Un slug que empiece por «en» no es un prefijo de idioma.
        ("/enlaces", ("", "/enlaces")),
    ],
)
def test_partir_ruta(ruta, esperado):
    assert partir_ruta(ruta) == esperado


@pytest.mark.parametrize(
    "ruta,idioma,esperado",
    [
        ("/", "en", "/en"),
        ("/", "es", "/"),
        ("/apu", "en", "/en/apu"),
        ("/apu", "es", "/apu"),
        ("/mx/apu", "en", "/en-mx/apu"),
        ("/mx/apu", "es", "/mx/apu"),
        ("/en-mx/apu", "es", "/mx/apu"),  # ida y vuelta
        ("/en-mx/apu", "en", "/en-mx/apu"),
        ("/presupuestos/nuevo", "en", "/en/presupuestos/nuevo"),
        ("/guia/presupuesto-de-obra", "en", "/en/guia/presupuesto-de-obra"),
        ("/en/", "es", "/"),
    ],
)
def test_ruta_en_idioma(ruta, idioma, esperado):
    assert ruta_en_idioma(ruta, idioma) == esperado


def test_idioma_desconocido_cae_al_espanol():
    assert ruta_en_idioma("/apu", "fr") == "/apu"
    assert normalizar_idioma("en-GB") == "en"


@pytest.mark.parametrize(
    "destino,esperado",
    [
        ("//malo.com/x", "/"),  # relativo a protocolo
        ("http://malo.com/x", "/"),  # absoluto
        ("https://malo.com", "/"),
        ("ftp://x/y", "/"),
        ("/idioma/es", "/"),  # no se permite volver al conmutador
        ("/idioma/en?destino=/apu", "/"),
        ("", "/"),
        ("\\malo", "/"),
        ("/apu", "/apu"),
        ("/apu?a=1", "/apu"),  # la query se reincorpora aparte
        ("/apu#ancla", "/apu"),
    ],
)
def test_ruta_segura_rechaza_lo_que_no_es_interno(destino, esperado):
    assert ruta_segura(destino) == esperado


@pytest.mark.parametrize("destino", ["//malo.com/x", "http://malo.com/x"])
def test_ruta_segura_no_deja_pasar_el_path_de_un_dominio_ajeno(destino):
    """``urlsplit('//malo.com/x').path`` es ``/x``: partir antes de sanear
    convertiría el conmutador en un open redirect."""
    assert ruta_segura(destino) == "/"
    assert ruta_en_idioma(ruta_segura(destino), "en") == "/en"


def test_url_cambio_idioma():
    assert url_cambio_idioma("/apu", "en") == "/idioma/en?destino=/apu"
    assert url_cambio_idioma("/apu", "es") == "/idioma/es?destino=/apu"
    # La query de la página de partida viaja codificada dentro de «destino».
    assert url_cambio_idioma("/presupuestos?estado=borrador", "en") == (
        "/idioma/en?destino=/presupuestos?estado=borrador"
    )
    assert url_cambio_idioma(None, "en") == "/idioma/en?destino=/"


def test_codigos_pais_incluye_los_mercados_con_landing():
    codigos = codigos_pais()
    assert {"mx", "es", "co", "pe", "ar"} <= codigos


# --------------------------------------------------------------------------
# Ruta /idioma/{lang}
# --------------------------------------------------------------------------
@pytest.fixture()
def cliente():
    with TestClient(app) as c:
        yield c


@pytest.mark.parametrize(
    "url,ubicacion,cookie",
    [
        ("/idioma/en?destino=/apu", "/en/apu", "en"),
        ("/idioma/es?destino=/apu", "/apu", "es"),
        ("/idioma/en?destino=/mx/apu", "/en-mx/apu", "en"),
        ("/idioma/es?destino=/mx/apu", "/mx/apu", "es"),
        ("/idioma/en?destino=/", "/en", "en"),
        ("/idioma/es?destino=/en/", "/", "es"),
        ("/idioma/en?destino=/presupuestos", "/en/presupuestos", "en"),
        ("/idioma/xx?destino=/apu", "/apu", "es"),  # idioma inválido → español
    ],
)
def test_cambio_idioma_redirige_y_fija_cookie(cliente, url, ubicacion, cookie):
    r = cliente.get(url, follow_redirects=False)
    assert r.status_code == 307
    assert r.headers["location"] == ubicacion
    assert r.headers["set-cookie"].startswith(f"{COOKIE_IDIOMA}={cookie};")


def test_cambio_idioma_conserva_la_query(cliente):
    r = cliente.get("/idioma/en?destino=/presupuestos?estado=borrador", follow_redirects=False)
    assert r.headers["location"] == "/en/presupuestos?estado=borrador"


@pytest.mark.parametrize(
    "destino",
    ["//malo.com/x", "http://malo.com/x", "https://malo.com", "/idioma/es"],
)
def test_cambio_idioma_no_es_un_open_redirect(cliente, destino):
    r = cliente.get(f"/idioma/en?destino={destino}", follow_redirects=False)
    assert r.status_code == 307
    assert r.headers["location"].startswith("/en")
    assert "malo.com" not in r.headers["location"]


def test_cambio_idioma_no_es_indexable(cliente):
    assert es_indexable("/idioma/en") is False
    r = cliente.get("/idioma/en?destino=/apu", follow_redirects=False)
    assert "noindex" in r.headers.get("x-robots-tag", "")


def test_el_conmutador_es_ida_y_vuelta(cliente):
    """Del español al inglés y de vuelta: la cookie es la que manda cuando no
    hay prefijo, así que el segundo salto tiene que limpiarla."""
    r = cliente.get("/idioma/en?destino=/apu", follow_redirects=False)
    assert r.headers["set-cookie"].startswith(f"{COOKIE_IDIOMA}=en;")
    r = cliente.get("/idioma/es?destino=/apu", follow_redirects=False)
    assert r.headers["set-cookie"].startswith(f"{COOKIE_IDIOMA}=es;")
    assert r.headers["location"] == "/apu"


def test_visitar_en_fija_la_cookie_para_el_resto_de_la_sesion(cliente):
    cliente.get("/en/apu", follow_redirects=True)
    # Sin prefijo, la cookie mantiene el inglés en todo el panel.
    r = cliente.get("/apu", follow_redirects=False)
    assert 'lang="en"' in r.text


# --------------------------------------------------------------------------
# Presencia en la interfaz
# --------------------------------------------------------------------------
MARCA = 'class="idioma-switch"'
ACTIVO = re.compile(r'idioma-switch-opcion is-active[^>]*>([A-Z]{2})<')


@pytest.mark.parametrize(
    "ruta",
    ["/", "/apu", "/mx/", "/en/", "/en/apu", "/como-funciona", "/pago", "/acceso",
     "/recuperar-acceso", "/restablecer-clave"],
)
def test_la_web_publica_lleva_el_conmutador(cliente, ruta):
    r = cliente.get(ruta, follow_redirects=True)
    assert r.status_code == 200
    assert MARCA in r.text, f"{ruta} no pinta el conmutador"


@pytest.mark.parametrize(
    "ruta,cookies,activo",
    [
        ("/", {}, "ES"),
        ("/apu", {"cotizat_lang": "en"}, "EN"),
        ("/en/apu", {}, "EN"),
        ("/en-mx/apu", {}, "EN"),
        ("/acceso", {"cotizat_lang": "en"}, "EN"),
        ("/acceso", {}, "ES"),
    ],
)
def test_el_conmutador_marca_el_idioma_activo(cliente, ruta, cookies, activo):
    with TestClient(app) as c:  # cliente limpio: sin restos de casos anteriores
        for nombre, valor in cookies.items():
            c.cookies.set(nombre, valor)
        r = c.get(ruta, follow_redirects=True)
    marcados = set(ACTIVO.findall(r.text))
    assert marcados == {activo}, f"{ruta} marca {marcados}"


def test_el_conmutador_apunta_a_la_misma_pagina_en_el_otro_idioma(cliente):
    r = cliente.get("/mx/apu", follow_redirects=True)
    assert '/idioma/en?destino=/mx/apu' in r.text
    assert '/idioma/es?destino=/mx/apu' in r.text


def test_el_html_lang_coincide_con_el_hreflang_del_pais(cliente):
    """/en-mx/ y /en-mx/apu se anuncian como en-MX; /mx/ como es-MX."""
    pares = [("/en-mx/", "en-MX"), ("/en-mx/apu", "en-MX"), ("/mx/", "es-MX"), ("/en/", "en")]
    for ruta, esperado in pares:
        with TestClient(app) as c:
            r = c.get(ruta, follow_redirects=True)
        m = re.search(r'<html[^>]*lang="([a-zA-Z-]+)"', r.text)
        assert m is not None, ruta
        assert m.group(1) == esperado, f"{ruta} → lang={m.group(1)}"


# ---------------------------------------------------------------------------
# Mensajes de la aplicación
# ---------------------------------------------------------------------------
# Los avisos viven en el código en español (los lanzan los servicios, los
# routers los pasan como ?error= o en el JSON). Se traducen al pintarlos, así
# que estas pruebas fijan el contrato: en español sale exactamente lo que había
# y en inglés sale la versión catalogada (o el original si no está).


def test_mensaje_en_espanol_devuelve_el_texto_original():
    from app.i18n import mensaje

    for texto in ("Datos inválidos.", "No hay una organización activa.", "Sin catalogar."):
        assert mensaje(texto, "es") == texto
        assert mensaje(texto, None) == texto


def test_mensaje_traduce_lo_catalogado():
    from app.i18n import mensaje

    assert mensaje("Datos inválidos.", "en") == "Invalid data."
    assert mensaje("Selecciona un método de pago.", "en") == "Select a payment method."
    assert mensaje("No hay partidas en el catálogo.", "en") == "There are no line items in the catalog."


def test_mensaje_interpola_los_valores_del_original():
    """Los mensajes con valores interpolados conservan esos valores."""
    from app.i18n import mensaje

    assert mensaje("Versión 3 congelada.", "en") == "Version 3 frozen."
    assert mensaje("Notificación enviada a ana@b.com.", "en") == "Notification sent to ana@b.com."
    assert mensaje("No se importó el presupuesto P-7: ese número ya existe.", "en") == (
        "Estimate P-7 was not imported: that number already exists."
    )
    assert mensaje("Stripe no respondió (Timeout).", "en") == "Stripe did not respond (Timeout)."


def test_mensaje_con_varios_valores():
    from app.i18n import mensaje

    assert mensaje(
        "El acceso de ana@b.com ya existe con rol «admin» y no se cambió a «editor».",
        "en",
    ) == "Access for ana@b.com already exists with the «admin» role and was not changed to «editor»."


def test_mensaje_sin_catalogar_se_muestra_igual():
    from app.i18n import mensaje

    assert mensaje("Aviso que nadie catalogó todavía.", "en") == "Aviso que nadie catalogó todavía."


@pytest.mark.parametrize("texto", ["", None])
def test_mensaje_vacio_no_falla(texto):
    from app.i18n import mensaje

    assert mensaje(texto, "en") == ""


def test_mensaje_request_usa_el_idioma_del_request():
    from app.i18n import mensaje_request

    class _Estado:
        lang = "en"

    class _Request:
        state = _Estado()

    assert mensaje_request(_Request(), "Datos inválidos.") == "Invalid data."
    assert mensaje_request(object(), "Datos inválidos.") == "Datos inválidos."
    assert mensaje_request(None, "Datos inválidos.") == "Datos inválidos."


def test_el_filtro_mensaje_esta_disponible_en_las_plantillas():
    from app.routers.common import TEMPLATES

    assert "mensaje" in TEMPLATES.env.globals
    plantilla = TEMPLATES.env.from_string("{{ error | mensaje(_idioma) }}")
    assert plantilla.render(error="Datos inválidos.", _idioma="en") == "Invalid data."
    assert plantilla.render(error="Datos inválidos.", _idioma="es") == "Datos inválidos."


# ---------------------------------------------------------------------------
# Ejemplo de la landing en inglés
# ---------------------------------------------------------------------------
# La landing vende con un ejemplo real (partidas, capítulos, APU del catálogo).
# En inglés no basta con traducir el interfaz: los rótulos salen del catálogo
# venezolano y los números se formatean con coma decimal. Estas pruebas fijan
# el contrato: en español todo sigue exactamente igual que antes.


def test_fmt_num_respeta_el_idioma():
    from app.utils import fmt_num

    assert fmt_num(2914.52, 2) == "2.914,52"
    assert fmt_num(2914.52, 2, "es") == "2.914,52"
    assert fmt_num(2914.52, 2, "en") == "2,914.52"
    assert fmt_num(9876543.21, 2, "en") == "9,876,543.21"
    assert fmt_num(9876543.21, 2, "es") == "9.876.543,21"


def test_el_ejemplo_en_ingles_rotula_capitulos_y_partidas():
    from app.services.landing_ejemplo import contexto_ejemplo

    ej = contexto_ejemplo("US", "en")
    caps = [c["titulo"] for c in ej["caps"]]
    assert caps[0] == "01 · Demolition and strip-out"
    assert caps[1] == "02 · Rough-in (bathroom plumbing)"
    nombres = [p["nombre"] for c in ej["caps"] for p in c["partidas"]]
    assert nombres[0] == "Hacking off wall tiling and its setting bed"
    # Ningún rótulo se queda a medias: si algo no está en la tabla, al menos
    # no puede seguir siendo español literal del catálogo.
    assert all("capa de pega" not in n for n in nombres)


def test_el_ejemplo_en_ingles_formatea_los_importes_en_ingles():
    """«2,914.52 US$», no «2.914,52 US$»."""
    from app.services.landing_ejemplo import contexto_ejemplo

    ej = contexto_ejemplo("US", "en")
    assert ej["tot"]["total"] == "2,914.52 US$"
    assert ej["hero"]["total"] == "2,914.52 US$"


def test_el_ejemplo_en_espanol_no_cambia():
    from app.services.landing_ejemplo import contexto_ejemplo

    ej = contexto_ejemplo("US", "es")
    assert ej["caps"][0]["titulo"] == "01 · Demoliciones y desmontajes"
    assert ej["tot"]["total"] == "2.914,52 US$"
    assert ej["empresa"] == "Construcciones Alfa"
    assert ej["iva_txt"] == "I.V.A. (16 %)"
    assert ej["resumen"]["horas"] == "98 h-hombre"


def test_el_ejemplo_en_ingles_traduce_etiquetas_y_unidades():
    from app.services.landing_ejemplo import contexto_ejemplo

    ej = contexto_ejemplo("US", "en")
    assert ej["iva_txt"] == "VAT (16 %)"
    assert ej["resumen"]["horas"] == "98 man-hours"
    assert ej["resumen"]["duracion"] == "≈ 6 days"
    assert ej["resumen"]["cuadrilla"] == "crew of 2 · 1 journeyman + 1 helper"
    # «ud» (unidad) se dice «ea» (each) en un APU en inglés
    assert ej["productos"][2]["cant"] == "1 ea"
    assert ej["productos"][2]["precio"] == "180.00 US$/ea"


def test_el_ejemplo_en_ingles_traduce_el_apu_del_catalogo():
    from app.services.landing_ejemplo import contexto_ejemplo

    ej = contexto_ejemplo("US", "en")
    apu = ej["apu"]
    if not apu["disponible"]:
        import pytest

        pytest.skip("catálogo de descompuestos no disponible")
    assert apu["titulo"] == "Concrete block boundary wall"
    grupos = {f["grupo"] for f in apu["filas"]}
    assert grupos <= {"Material", "Labor", "Equipment"}
    assert any(f["nombre"] == "Journeyman bricklayer, 1st class" for f in apu["filas"])
    assert "man-hours" in apu["horas_mo"]


def test_el_ejemplo_sigue_siendo_por_pais_en_ingles():
    """El idioma traduce los rótulos; el país sigue mandando en moneda e IVA."""
    from app.services.landing_ejemplo import contexto_ejemplo

    us = contexto_ejemplo("US", "en")
    mx = contexto_ejemplo("MX", "en")
    assert us["moneda"] == "USD"
    assert mx["moneda"] == "MXN"
    assert mx["iva_txt"] == "VAT (16 %)"
    # mismos rótulos, distinta moneda
    assert us["caps"][0]["titulo"] == mx["caps"][0]["titulo"]
    assert us["tot"]["total"] != mx["tot"]["total"]
