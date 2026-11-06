"""La landing de Chile y España compite como hub de precios de su mercado.

En la línea base de Search Console (08/10–04/11) /cl/ y /es/ eran las dos
URL con más impresiones del sitio y las que peor rankeaban (posición 67,3 y
63,5): su copy perseguía consultas de *software* («software de presupuestos
y APU en Chile») contra Opus, Neodata y Presto con un dominio de días, y las
consultas de software del sitio se mueven en las posiciones 44–87 sin un
solo clic. La batalla que sí puede ganar esa URL es «precios de
construcción en <país>»: la landing se convierte en el hub de precios del
mercado con el índice de apartados y la cifra real de cada uno, el recuento
en el título y el CTA de la aplicación intacto (playbook §14).

Solo CL y ES. Los otros 20 mercados quedan como están —sus landings
convierten (BO 6 %, NI 8,3 %, DO 9,2 % de CTR en la misma ventana)— y hacen
de grupo de control del experimento.

Contratos que protege este módulo:

* solo CL y ES cambian de intención; el resto conserva su copy comercial;
* el título lleva el recuento real de partidas y la marca al final, dentro
  del ancho útil (≤ 72, si Google corta corta por el final y el número se
  queda a la vista);
* el índice enlaza cada apartado con la misma cifra que promete el título
  de la página de destino (una sola cuenta: ``_medidas_apartado``);
* las cifras usan los separadores del mercado (§12), no los del idioma;
* la página sigue indexable, con su canónica y con el CTA de alta.
"""
from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from app import seo_precios as sp
from app.main import app
from app.paises import ORDEN_SELECTOR, PAISES
from app.seo import ficha_landing
from app.services import precios_publicos as pp

BASE = "https://cotizat.online"

HUBS = ("CL", "ES")


def _cliente() -> TestClient:
    return TestClient(app, base_url=BASE)


def _partidas(precios, unidad="m²"):
    return [
        {"pu": precio, "unidad": unidad, "moneda": "EUR", "slug": f"p{i}", "titulo": f"P{i}"}
        for i, precio in enumerate(precios)
    ]


def _seccion_hub(html: str) -> str:
    """El bloque del hub, del H2 al enlace del índice completo."""
    ini = html.find('id="precios-mercado"')
    fin = html.find("lp2-hub-mas", ini)
    assert ini != -1 and fin != -1, "falta la sección del hub de precios"
    return html[ini:fin]


# ---------------------------------------------------------------------------
# La decisión y su perímetro: CL y ES sí, los demás no
# ---------------------------------------------------------------------------

def test_solo_chile_y_espana_son_landing_hub():
    assert set(sp.LANDING_HUB_PRECIOS) == {"CL", "ES"}
    for codigo in ORDEN_SELECTOR:
        hub = sp.hub_landing(codigo)
        if codigo in HUBS:
            assert hub is not None, f"{codigo}: el hub debería estar servido"
        else:
            assert hub is None, f"{codigo}: no es landing-hub (grupo de control)"


def test_el_resto_de_landing_conserva_su_titulo_comercial():
    """El grupo de control no se toca: título comercial con la marca delante."""
    for codigo in ORDEN_SELECTOR:
        if codigo in HUBS:
            continue
        ficha = ficha_landing(codigo)
        assert ficha["title"].startswith("CotizaT:"), f"{codigo}: {ficha['title']}"


def test_sin_catalogo_la_landing_cae_al_copy_comercial(monkeypatch):
    """Si el artefacto del mercado falta, la ficha no se queda a medias."""
    monkeypatch.setattr(sp, "ficha_hub_landing", lambda _cc: None)
    ficha = ficha_landing("CL")
    assert ficha["title"] == "CotizaT: software de presupuestos y APU en Chile"
    assert ficha["h1"] == "Software de presupuestos y APU para construcción en Chile"


# ---------------------------------------------------------------------------
# El título y la ficha pública
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cc", HUBS)
def test_el_titulo_lleva_el_recuento_real_y_la_marca_al_final(cc):
    resumen = pp.resumen(cc)
    ficha = ficha_landing(cc)
    pais = PAISES[cc]
    total_txt = sp._miles(resumen["total_partidas"], pais)

    titulo = ficha["title"]
    assert total_txt in titulo, f"{cc}: el título no lleva el recuento: {titulo}"
    assert pais["nombre"] in titulo
    assert pais["moneda"] in titulo
    assert titulo.endswith(" | CotizaT"), "la marca se conserva, al final"
    assert len(titulo) <= 72, f"{cc}: {len(titulo)} caracteres"
    # La cifra va antes del corte típico de Google (~60): aunque recorte,
    # el recuento y el país ya se han leído.
    primeros_60 = titulo[:60]
    assert total_txt in primeros_60 and pais["nombre"] in primeros_60

    assert ficha["h1"] == f"Precios de construcción en {pais['nombre']}"
    assert total_txt in ficha["h1_resalte"]
    assert total_txt in ficha["description"]
    assert ficha["canonical_path"] == f"/{cc.lower()}/"


def test_los_dos_hubs_no_comparten_el_titulo():
    """CL y ES son dos páginas distintas, no una con el nombre cambiado."""
    assert ficha_landing("CL")["title"] != ficha_landing("ES")["title"]
    assert "CLP" in ficha_landing("CL")["title"]
    assert "EUR" in ficha_landing("ES")["title"]


# ---------------------------------------------------------------------------
# La cifra del índice es la misma cuenta que el título del hub de apartado
# ---------------------------------------------------------------------------

def test_la_cifra_del_listado_sigue_las_reglas_del_titulo():
    pais = PAISES["ES"]
    # Homogéneo: rango con la unidad.
    assert sp.cifra_apartado(_partidas([39.82, 120.0, 263.62]), pais) == "40–264 EUR/m²"
    # Mezcla de unidades: «desde» sin unidad.
    mixto = _partidas([10.0, 20.0], "m²") + _partidas([300.0, 400.0], "ud")
    assert sp.cifra_apartado(mixto, pais) == "desde 10 EUR"
    # Dispersión >40:1: mediana como precio típico, no un rango inútil.
    sesgado = _partidas([1.0, 50.0, 183.0], "m²")
    assert sp.cifra_apartado(sesgado, pais) == "50 EUR/m² de media"
    # En inglés, para el espejo /en-xx/ (noindex, pero se sirve).
    assert sp.cifra_apartado(sesgado, pais, "en") == "avg 50 EUR/m²"


def test_el_hub_usa_la_misma_cuenta_en_lista_y_titulo():
    """La cifra del enlace coincide con la que promete el título del destino."""
    hub = sp.hub_landing("ES")
    pais = PAISES["ES"]
    vistos = 0
    for capitulo in hub["capitulos"]:
        for ap in capitulo["apartados"]:
            ficha = pp.apartado("ES", ap["ruta"].rsplit("/", 1)[-1])
            medidas = sp._medidas_apartado(ficha["partidas"], pais)
            esperada = (
                medidas["rango"]
                or (f"desde {medidas['desde']}" if medidas["desde"] else "")
                or (f"{medidas['tipico']} de media" if medidas["tipico"] else "")
            )
            assert ap["cifra"] == esperada, f"{ap['nombre']}: {ap['cifra']} != {esperada}"
            vistos += 1
    assert vistos == hub["apartados_total"]


# ---------------------------------------------------------------------------
# La página servida: hub, CTA, canónica e indexabilidad intactas
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cc,moneda", [("CL", "CLP"), ("ES", "EUR")])
def test_la_landing_sirve_el_hub_con_cifras_del_mercado(cc, moneda):
    with _cliente() as cliente:
        resp = cliente.get(f"/{cc.lower()}/")
    assert resp.status_code == 200
    assert "X-Robots-Tag" not in resp.headers or "noindex" not in resp.headers.get(
        "X-Robots-Tag", ""
    )
    html = resp.text
    assert 'rel="canonical" href="https://cotizat.online/' + cc.lower() + '/"' in html
    # El CTA de la aplicación sigue estando: el plan no renuncia a la venta.
    assert "/acceso" in html
    pais = PAISES[cc]
    assert pais["id_fiscal"] in html  # NIF / RUT no desaparecen del copy

    # La página vende primero el software: problema, propuesta de valor,
    # producto, comparativa y planes preceden al recurso de precios; el CTA
    # final queda después para cerrar el recorrido de conversión.
    hub_pos = html.index('id="precios-mercado"')
    for section_id in (
        "problema", "valor-antes", "producto", "comparativa", "precios"
    ):
        assert html.index(f'id="{section_id}"') < hub_pos
    assert hub_pos < html.index('id="pago"')

    hub = _seccion_hub(html)
    # Todos los apartados del mercado enlazados desde el hub.
    enlaces = re.findall(rf'href="/{cc.lower()}/precios/([a-z0-9-]+)"', hub)
    resumen = pp.resumen(cc)
    assert len(enlaces) == resumen["total_apartados"], (
        f"{cc}: {len(enlaces)} enlaces para {resumen['total_apartados']} apartados"
    )
    # Cada enlace promete una cifra en la moneda del mercado…
    cifras = re.findall(r'<span class="lp2-hub-cifra">([^<]+)</span>', hub)
    assert len(cifras) == resumen["total_apartados"]
    assert all(moneda in cifra for cifra in cifras)
    # …con los separadores del mercado (§12): miles con punto en CL y ES.
    assert re.search(rf"\d\.\d{{3}}.*{moneda}", hub), f"{cc}: sin separador de miles del mercado"
    # El puente final apunta al índice completo del mercado.
    assert f'href="/{cc.lower()}/precios"' in html


def test_las_landings_de_control_no_tienen_hub():
    """México y Colombia (control) no cambian: sin hub, con su puente."""
    with _cliente() as cliente:
        for cc in ("mx", "co"):
            html = cliente.get(f"/{cc}/").text
            assert 'id="precios-mercado"' not in html
            assert 'class="mercados-precios"' in html


def test_el_jsonld_webpage_y_el_faq_sobreviven_al_cambio():
    import json

    with _cliente() as cliente:
        html = cliente.get("/es/").text
    bloques = [
        json.loads(b)
        for b in re.findall(
            r'<script type="application/ld\+json"[^>]*>(.*?)</script>', html, re.S
        )
    ]
    tipos = {b.get("@type") for b in bloques}
    assert "FAQPage" in tipos
    webpage = next(b for b in bloques if b.get("@type") == "WebPage")
    assert "Precios de construcción en España" in webpage.get("name", "")


def test_el_indice_del_catalogo_no_se_toca():
    """/es/precios sigue siendo el índice del silo, con su propio título."""
    with _cliente() as cliente:
        resp = cliente.get("/es/precios")
    assert resp.status_code == 200
    titulo = re.search(r"<title>(.*?)</title>", resp.text, re.S).group(1)
    assert "Precios unitarios en España" in titulo
