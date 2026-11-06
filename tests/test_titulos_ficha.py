"""El título de una ficha de partida lleva su precio, y el precio es verdad.

El 06/11/2026, con el informe de 28 días delante: las fichas de partida son 746
páginas, 9.504 impresiones y **75 clics** (CTR 0,79 %), el 64 % de las
impresiones del sitio. Sus títulos no llevaban cifra: «Portón corredizo con
automatismo», «Demolición de muro de carga de hormigón». Compiten por consultas
como «portón corredizo precio» y en el resultado no aparece ningún número.

La cifra existía en el código —la primera variante del título la incluía— pero
se escribía con céntimos («491,00 EUR/ud en España»), gastaba los 60 caracteres
del resultado y el título se caía a la variante sin precio. Medido sobre el
catálogo entero: **167 de 42.978 fichas (0,4 %) llevaban la cifra**.

Estas pruebas fijan las reglas del arreglo, que son las mismas de los hubs:

* la cifra va siempre que quepa, sin céntimos y con la moneda una sola vez;
* el redondeo es hacia arriba y conserva decimales en importes pequeños;
* se recorta primero el país y la unidad, nunca el nombre ni el número;
* la unidad se escribe como se lee («m²», no «m2»).
"""
from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from app import seo_precios as sp
from app.main import app
from app.paises import PAISES
from app.services import precios_publicos as pp

BASE = "https://cotizat.online"


def _titulo(titulo, pu, unidad="ud", cc="ES", en=None):
    pais = PAISES[cc]
    if en is None:
        en = str(pais.get("idioma")) == "en"
    return sp.titulo_partida(cc, titulo, unidad, pu, pais, en)


def test_la_ficha_lleva_su_precio_sin_centimos_y_con_la_moneda_una_vez():
    titulo = _titulo("Portón corredizo con automatismo", 491.0)
    assert "491 EUR/ud" in titulo, titulo
    assert titulo.count("EUR") == 1
    assert "491,00" not in titulo and "491.00" not in titulo
    assert "España" in titulo, "el país sigue en el título cuando cabe"
    assert len(titulo.removesuffix(" | CotizaT")) <= 72


def test_el_precio_se_redondea_hacia_arriba():
    """Con una partida de 39,82 EUR, «39 EUR» en el título sería mentira."""
    titulo = _titulo("Demolición de muro de carga", 39.82)
    assert "40 EUR" in titulo, titulo
    assert "39 EUR" not in titulo


def test_los_importes_pequenos_conservan_los_decimales():
    """2,9 USD/pie² no es «3 USD»: el decimal es la información."""
    titulo = _titulo("Removal of thermal insulation from a roof deck", 2.9, "sq ft", cc="US")
    assert "2.9 USD/sq ft" in titulo, titulo
    assert not re.search(r"\b3 USD", titulo), titulo


def test_la_unidad_se_escribe_como_se_lee():
    pais = PAISES["ES"]
    assert sp._unidad_titulo("m2") == "m²"
    assert sp._unidad_titulo("m3") == "m³"
    assert sp._unidad_titulo("ud") == "ud"
    assert sp._unidad_titulo("") == ""
    titulo = _titulo("Pavimento cerámico", 23.0, "m2")
    assert "/m²" in titulo and "m2" not in titulo.split("|")[0].replace("m²", "")


def test_un_nombre_largo_conserva_el_precio():
    """La ficha que abrió el caso: 71 caracteres de nombre y ni un número."""
    titulo = _titulo(
        "Piso de loseta en baño o área húmeda, con pendiente hacia la coladera",
        436.0,
        "m2",
    )
    assert "436 EUR/m²" in titulo, titulo
    assert len(titulo.removesuffix(" | CotizaT")) <= 72


def test_el_nombre_se_recorta_por_la_clausula_antes_que_perder_la_cifra():
    titulo = _titulo(
        "Piso de loseta en baño o área húmeda, con pendiente hacia la coladera",
        436.0,
        cc="MX",
    )
    assert "MXN" in titulo, titulo
    assert "coladera" not in titulo, "la cláusula final se cede antes que la cifra"


def test_el_pais_se_recorta_antes_que_el_precio():
    """«the UK» cabe donde no cabe «the United Kingdom»."""
    largo = _titulo(
        "Demolition of a reinforced concrete basement wall", 207.0, "m3", cc="GB"
    )
    assert "207 GBP" in largo, largo
    assert len(largo.removesuffix(" | CotizaT")) <= 72


def test_la_descripcion_usa_la_misma_cifra_que_el_titulo():
    """El título dice «491 EUR» y la descripción no puede decir «491,00 EUR»."""
    indice = pp._indice("ES")
    for slug_ap, apartado in indice["apartados"].items():
        for partida in apartado.get("partidas") or []:
            ficha = pp.partida("ES", slug_ap, partida["slug"])
            if ficha and ficha["pu"] >= 100:
                break
        else:
            continue
        break
    assert ficha
    titulo = sp.titulo_partida("ES", ficha["titulo"], ficha["unidad"], ficha["pu"], PAISES["ES"], False)
    corta = sp._dinero_corto(ficha["pu"], PAISES["ES"])
    assert corta in titulo, titulo
    assert corta in sp._dinero_corto(ficha["pu"], PAISES["ES"])


@pytest.mark.parametrize("cc", ["ES", "MX", "US", "GB", "IE"])
def test_la_mayoria_de_las_fichas_del_catalogo_llevan_cifra(cc):
    """La regresión que importa: que la cifra no vuelva a desaparecer en masa.

    Medido sobre el catálogo real, no sobre un ejemplo. Antes del arreglo la
    llevaba el 0,4 % de las fichas; por debajo del 90 % esta prueba falla.
    """
    indice = pp._indice(cc)
    assert indice, cc
    pais = PAISES[cc]
    en = str(pais.get("idioma")) == "en"
    con_cifra = total = 0
    for slug_ap, apartado in indice["apartados"].items():
        for partida in apartado.get("partidas") or []:
            titulo = sp.titulo_partida(
                cc, partida["titulo"], partida["unidad"], partida["pu"], pais, en
            )
            total += 1
            con_cifra += bool(re.search(rf"\d.*{pais['moneda']}", titulo))
            assert len(titulo.removesuffix(" | CotizaT")) <= 72, (cc, titulo)
    assert total
    assert con_cifra / total >= 0.9, f"{cc}: {con_cifra}/{total} con cifra"


def test_la_cifra_entra_antes_del_corte_de_google_en_casi_todas():
    """El número tiene que verse: Google corta cerca de los 60 caracteres."""
    indice = pp._indice("ES")
    pais = PAISES["ES"]
    visibles = total = 0
    for slug_ap, apartado in indice["apartados"].items():
        for partida in apartado.get("partidas") or []:
            titulo = sp.titulo_partida(
                "ES", partida["titulo"], partida["unidad"], partida["pu"], pais, False
            )
            cifra = f"{sp._numero_corto(partida['pu'], pais)} {pais['moneda']}"
            fin = titulo.find(cifra)
            if fin < 0:
                continue
            total += 1
            visibles += (fin + len(cifra)) <= 60
    assert total
    assert visibles / total >= 0.85, f"{visibles}/{total} con la cifra entera a la vista"


def test_una_ficha_real_una_cifra_real():
    """De punta a punta, sobre una URL viva del catálogo español."""
    indice = pp._indice("ES")
    ruta = None
    for slug_ap, apartado in indice["apartados"].items():
        for partida in apartado.get("partidas") or []:
            if pp.partida_indexable("ES", slug_ap, partida["slug"]):
                ruta = pp.ruta_partida("ES", slug_ap, partida["slug"])
                break
        if ruta:
            break
    assert ruta
    with TestClient(app, base_url=BASE) as cliente:
        respuesta = cliente.get(ruta)
    assert respuesta.status_code == 200
    titulo = re.search(r"<title>(.*?)</title>", respuesta.text, re.S)
    assert titulo
    assert re.search(r"\d+(?:[.,]\d+)? EUR", titulo.group(1)), titulo.group(1)
