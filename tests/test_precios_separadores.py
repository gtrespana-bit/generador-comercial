"""El precio se escribe con los separadores del mercado, no con los del idioma.

En México, el 06/11/2026, la misma ficha decía tres cosas distintas del mismo
precio:

    cuerpo:  2.460,25 MXN     ← separadores de España
    FAQ:     2,460.25 MXN     ← separadores de México
    título:  2,461 MXN/m³     ← redondeado, correcto

La plantilla llamaba a `money_iso(partida.moneda)` sin pasarle el mercado, así
que el filtro caía al locale de la interfaz: en «es» eso formatea con punto de
miles y coma decimal, que en México se lee mal. Ocho mercados hispanos usan
coma de miles y punto decimal (MX, EC, DO, PA, GT, HN, SV, NI) y son justo los
que no se habían localizado todavía.

Estas pruebas atan el cuerpo de la página al formateador del país: la cifra que
se ve tiene que ser la que produce `formato_iso(..., mercado=PAISES[cc])`, y la
que producía el locale español no puede aparecer en ninguna parte.
"""
from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.paises import PAISES
from app.services import precios_publicos as pp
from app.services.monedas import formato_iso

BASE = "https://cotizat.online"

# Mercados hispanos con coma de miles: los que el locale «es» formatea al revés.
MERCADOS_COMA = ["MX", "EC", "DO", "PA", "GT", "HN", "SV", "NI"]


def _ficha_con_miles(cc: str):
    """Una ficha del mercado cuyo precio pase de mil, indexable si la hay.

    La ficha se sirve aunque el mercado esté a medio localizar (lo que cambia
    es el `noindex`, no el formato), así que la prueba vale para los ocho
    mercados de coma decimal desde hoy y no solo para México.
    """
    indice = pp._indice(cc)
    if not indice:
        return None
    preferida = respaldo = None
    for slug_ap, apartado in indice["apartados"].items():
        for partida in apartado.get("partidas") or []:
            ruta = pp.ruta_partida(cc, slug_ap, partida["slug"])
            caso = (ruta, float(partida["pu"]), partida["moneda"])
            if float(partida["pu"]) >= 1000:
                if preferida is None:
                    preferida = caso
                if pp.partida_indexable(cc, slug_ap, partida["slug"]):
                    return caso
            respaldo = respaldo or caso
    return preferida or respaldo


@pytest.mark.parametrize("cc", MERCADOS_COMA)
def test_la_ficha_usa_los_separadores_del_mercado(cc):
    caso = _ficha_con_miles(cc)
    if not caso:
        pytest.skip(f"{cc} todavía no publica fichas")
    ruta, pu, moneda = caso
    correcta = formato_iso(pu, moneda, "es", PAISES[cc])
    con_locale_es = formato_iso(pu, moneda, "es")
    with TestClient(app, base_url=BASE) as cliente:
        html = cliente.get(ruta).text
    assert correcta in html, f"{cc}: no aparece «{correcta}» en {ruta}"
    if con_locale_es != correcta:
        assert con_locale_es not in html, (
            f"{cc}: sigue saliendo «{con_locale_es}» (locale español) en {ruta}"
        )


@pytest.mark.parametrize("cc", MERCADOS_COMA)
def test_el_mismo_precio_no_se_escribe_de_dos_maneras_en_la_misma_pagina(cc):
    """Antes el cuerpo decía «2.460,25» y la FAQ «2,460.25» en la misma página."""
    caso = _ficha_con_miles(cc)
    if not caso:
        pytest.skip(f"{cc} todavía no publica fichas")
    ruta, pu, moneda = caso
    with TestClient(app, base_url=BASE) as cliente:
        html = cliente.get(ruta).text
    cuerpo = re.search(r'class="precios-pu">([^<]+)<', html)
    assert cuerpo, ruta
    cifra = cuerpo.group(1).strip()
    assert cifra == formato_iso(pu, moneda, "es", PAISES[cc]), (cc, cifra)
    # El cuerpo y la pregunta frecuente comparten la misma cifra textual.
    assert html.count(cifra) >= 2, f"{cc}: «{cifra}» solo aparece una vez"


def test_espana_conserva_sus_separadores():
    ruta = "/es/precios/pavimento-ceramicos-y-porcelanico"
    indice = pp._indice("ES")
    apartado = indice["apartados"].get("pavimento-ceramicos-y-porcelanico")
    assert apartado
    partida = apartado["partidas"][0]
    esperado = formato_iso(partida["pu"], partida["moneda"], "es", PAISES["ES"])
    with TestClient(app, base_url=BASE) as cliente:
        html = cliente.get(ruta).text
    assert esperado in html
    assert "," in esperado  # en España la coma es el decimal


def test_el_hub_de_apartado_tambien_usa_los_separadores_del_mercado():
    indice = pp._indice("MX")
    assert indice
    for slug_ap, apartado in indice["apartados"].items():
        for partida in apartado.get("partidas") or []:
            if float(partida["pu"]) >= 1000:
                pu, moneda = float(partida["pu"]), partida["moneda"]
                break
        else:
            continue
        break
    ruta = pp.ruta_apartado("MX", slug_ap)
    correcta = formato_iso(pu, moneda, "es", PAISES["MX"])
    alternate = formato_iso(pu, moneda, "es")
    with TestClient(app, base_url=BASE) as cliente:
        html = cliente.get(ruta).text
    assert correcta in html, ruta
    assert alternate not in html, f"en {ruta} sigue el locale español: {alternate}"


def test_el_filtro_acepta_el_mercado():
    """La unidad del arreglo: el filtro de plantillas con `mercado=pais`."""
    from app.routers.common import _money_iso

    class _Ctx(dict):
        pass

    ctx = _Ctx(_idioma="es")
    assert _money_iso(ctx, 2460.25, "MXN", mercado=PAISES["MX"]) == "2,460.25 MXN"
    assert _money_iso(ctx, 2460.25, "EUR", mercado=PAISES["ES"]) == "2.460,25 EUR"
    # Sin mercado se mantiene el comportamiento histórico: locale del idioma.
    assert _money_iso(ctx, 2460.25, "MXN") == "2.460,25 MXN"


@pytest.mark.parametrize("cc", ["SV", "MX", "PA", "NI"])
def test_la_tabla_comparativa_no_mezcla_dos_formatos_en_la_misma_fila(cc):
    """En la fila del propio mercado, el dólar y el precio local se escriben igual.

    Antes: «6,97 USD» junto a «6.97 USD/ud». El mismo precio, dos maneras, en
    dos celdas seguidas.
    """
    caso = _ficha_con_miles(cc)
    if not caso:
        pytest.skip(f"{cc} sin fichas")
    ruta, _pu, _moneda = caso
    with TestClient(app, base_url=BASE) as cliente:
        html = cliente.get(ruta).text
    fila = re.search(r'<tr class="cmp-este">(.*?)</tr>', html, re.S)
    if not fila:
        pytest.skip("esta partida no tiene comparativa internacional")
    celdas = re.findall(r"<td>([\d.,]+ [A-Z]{3})", fila.group(1))
    assert len(celdas) >= 2, fila.group(1)[:200]
    decimal = PAISES[cc]["separador_decimal"]
    ajeno = "," if decimal == "." else "."
    for celda in celdas:
        assert not celda.split()[0].endswith(ajeno + "00") and not re.search(
            rf"\{ajeno}\d{{2}} ", celda
        ), f"{cc}: «{celda}» no usa el decimal del mercado en la fila propia"
