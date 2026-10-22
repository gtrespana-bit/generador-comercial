"""Mano de obra por país: coste horario real del catálogo, no una tabla salarial.

La página nace de un dato que ya existía enterrado en el descompuesto de cada
partida: los recursos de mano de obra con su coste por hora. Lo que se prueba
aquí es que lo que se publica es exactamente lo que dice el catálogo, en los
22 mercados, y que la página no promete más de lo que puede sostener:

- Los oficios salen de los recursos del catálogo del país, no de una lista fija.
- La tarifa publicada es el promedio de las líneas de mano de obra que usan
  ese oficio; se comprueba contra una partida concreta, no contra sí misma.
- Los mercados donde todos los oficios comparten tarifa lo dicen (no se puede
  vender como tabla salarial algo que no distingue oficios).
- La descarga JSON trae el catálogo completo y sirve de ``distribution`` al
  ``Dataset``, que antes se declaraba sin descarga real.
"""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.mano_obra import contexto_mano_obra, oficios, ruta_mano_obra
from app.seo_precios import jsonld_dataset
from app.services import precios_publicos as pp

MERCADOS = sorted(pp.paises_publicados())


def _cliente() -> TestClient:
    return TestClient(app, base_url="https://cotizat.online")


def test_hay_mano_de_obra_en_los_22_mercados():
    for cc in MERCADOS:
        lista = oficios(cc)
        assert lista, f"{cc} sin oficios publicados"
        assert len(lista) == 16, f"{cc}: {len(lista)} oficios, se esperaban 16"


@pytest.mark.parametrize("cc", ["MX", "US"])
def test_los_oficios_salen_del_catalogo_del_pais(cc):
    """Cada oficio publicado existe como recurso de mano de obra del catálogo."""
    indice = pp._indice(cc)  # noqa: SLF001 - mismo paquete, solo lectura
    nombres = set()
    for (slug_ap, slug_p) in indice["partidas"]:  # noqa: SLF001
        for linea in pp.partida(cc, slug_ap, slug_p)["lineas"]:
            if linea["grupo"] == "mano_obra":
                nombres.add(linea["nombre"].lower())
    assert nombres, f"{cc} no declara líneas de mano de obra"
    for oficio in oficios(cc):
        # El nombre publicado es el recurso sin el grado (Oficial de 1ª, ...).
        buscado = oficio["nombre"].lower()
        assert any(buscado in nombre for nombre in nombres), (
            f"{cc}: {oficio['nombre']} no aparece en el descompuesto"
        )


@pytest.mark.parametrize("cc", MERCADOS)
def test_cada_partida_queda_cubierta_por_algun_oficio(cc):
    """Si el catálogo lleva mano de obra, la tabla no puede dejarla fuera."""
    total = (pp.resumen(cc) or {}).get("total_partidas") or 0
    suma = sum(o["partidas"] for o in oficios(cc))
    assert suma >= total, f"{cc}: {suma} apariciones para {total} partidas"


@pytest.mark.parametrize("cc", ["MX", "US", "ES", "GB"])
def test_la_tarifa_coincide_con_el_descompuesto(cc):
    """La hora publicada es la que el catálogo aplica en sus partidas."""
    oficio = oficios(cc)[0]
    vista = set()
    for (slug_ap, slug_p) in list(pp._indice(cc)["partidas"])[:200]:  # noqa: SLF001
        for linea in pp.partida(cc, slug_ap, slug_p)["lineas"]:
            if linea["grupo"] == "mano_obra" and oficio["nombre"] in linea["nombre"]:
                vista.add(round(float(linea["precio"]), 2))
    assert vista, f"{cc}: sin líneas para {oficio['nombre']}"
    assert round(oficio["hora"], 2) in vista


@pytest.mark.parametrize("cc", MERCADOS)
def test_orden_por_peso_y_formato_de_moneda(cc):
    lista = oficios(cc)
    assert [o["partidas"] for o in lista] == sorted(
        (o["partidas"] for o in lista), reverse=True
    )
    for oficio in lista:
        assert oficio["partidas"] > 0
        assert oficio["hora"] > 0
        assert oficio["hora_txt"].replace("\u00a0", " ")
        assert len(oficio["capitulos"]) >= 1
        assert oficio["slug"] and oficio["slug"] not in ("", "-")


@pytest.mark.parametrize("cc", MERCADOS)
def test_ruta_canonica_por_idioma(cc):
    ruta = ruta_mano_obra(cc)
    idioma = (pp.PAISES.get(cc) or {}).get("idioma")
    if idioma == "en":
        assert ruta == f"/en-{cc.lower()}/labour-rates"
    else:
        assert ruta == f"/{cc.lower()}/mano-de-obra"


@pytest.mark.parametrize("cc", MERCADOS)
def test_la_pagina_responde_y_es_indexable(cc):
    ruta = pp.ruta_mano_obra(cc)
    with _cliente() as cliente:
        respuesta = cliente.get(ruta)
    assert respuesta.status_code == 200, ruta
    html = respuesta.text
    assert 'name="robots"' in html
    assert "noindex" not in html.split('name="robots"')[1][:80]
    assert f"https://cotizat.online{ruta}" in html  # canonical
    assert 'rel="canonical"' in html
    assert "FAQPage" in html
    assert "BreadcrumbList" in html


def test_no_se_publica_como_tabla_salarial():
    """El FAQ tiene que decir lo que la tabla es y lo que no."""
    with _cliente() as cliente:
        html = cliente.get("/mx/mano-de-obra").text
    assert "tabla salarial" in html
    assert "no incluye" in html.lower() or "No incluye" in html


def test_los_mercados_con_tarifa_unica_lo_dicen():
    """En 12 mercados todos los oficios comparten tarifa: hay que explicarlo."""
    lista = oficios("DO")
    # Ayudante y Ayudante especializado van aparte: el resto son una sola tarifa.
    assert len({round(o["hora"], 2) for o in lista if "Oficial" in o["nombre"]}) <= 1
    assert len({round(o["hora"], 2) for o in lista if "Ayudante" not in o["nombre"]}) == 1
    with _cliente() as cliente:
        html = cliente.get("/do/mano-de-obra").text
    assert "misma cifra" in html


def test_cada_version_declara_las_22_alternativas():
    """Sin hreflang, 22 páginas casi iguales compiten entre sí."""
    with _cliente() as cliente:
        html = cliente.get("/es/mano-de-obra").text
    for cc in MERCADOS:
        assert f"https://cotizat.online{ruta_mano_obra(cc)}" in html, cc
    assert 'hreflang="x-default"' in html


def test_alias_e_idioma_cruzado_redirigen_301():
    with _cliente() as cliente:
        assert (
            cliente.get("/en-us/mano-de-obra", follow_redirects=False).status_code
            == 301
        )
        assert (
            cliente.get("/en-us/mano-de-obra", follow_redirects=False).headers[
                "location"
            ]
            == "/en-us/labour-rates"
        )
        assert (
            cliente.get("/mx/labour-rates", follow_redirects=False).headers["location"]
            == "/mx/mano-de-obra"
        )


def test_pais_no_publicado_404():
    with _cliente() as cliente:
        assert cliente.get("/zz/mano-de-obra").status_code == 404
        assert cliente.get("/zz/precios.json").status_code == 404


@pytest.mark.parametrize("cc", MERCADOS)
def test_descarga_json_del_catalogo(cc):
    with _cliente() as cliente:
        respuesta = cliente.get(pp.ruta_json(cc))
    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"].startswith("application/json")
    assert respuesta.headers["access-control-allow-origin"] == "*"
    assert "s-maxage" in respuesta.headers["cache-control"]
    datos = json.loads(respuesta.text)
    resumen = pp.resumen(cc)
    assert datos["total_partidas"] == resumen["total_partidas"]
    assert datos["total_apartados"] == resumen["total_apartados"]
    assert datos["pais"]["codigo"] == cc
    assert datos["url"].endswith(pp.ruta_indice(cc))
    assert datos["total_capitulos"] == len(resumen["capitulos"])
    partidas = [
        p
        for capitulo in datos["capitulos"]
        for apartado in capitulo["apartados"]
        for p in apartado["partidas"]
    ]
    assert len(partidas) == datos["total_partidas"]
    for p in partidas[:5]:
        assert p["precio_unitario"] > 0
        assert p["url"].startswith("https://cotizat.online/")


def test_el_json_coincide_con_el_html_de_la_partida():
    """El precio de la descarga es el mismo que el de la ficha pública."""
    datos = pp.exportar("MX")
    apartado = datos["capitulos"][0]["apartados"][0]
    partida = apartado["partidas"][0]
    ficha = pp.partida("MX", apartado["slug"], partida["slug"])
    assert partida["precio_unitario"] == round(float(ficha["pu"]), 2)
    with _cliente() as cliente:
        assert cliente.get(partida["url"].replace("https://cotizat.online", "")).status_code == 200


def test_el_dataset_apunta_a_una_descarga_que_existe(monkeypatch):
    monkeypatch.setenv("COTIZAT_PUBLIC_URL", "https://cotizat.online")
    with _cliente() as cliente:
        pedido = cliente.get("/mx/precios")
        dataset = jsonld_dataset(
            pedido.request,
            cc="MX",
            ruta="/mx/precios",
            nombre="México",
            lang="es",
            total=1989,
            moneda="MXN",
            mes="septiembre 2026",
        )
        descarga = dataset["distribution"][0]["contentUrl"]
        assert descarga.endswith("/mx/precios.json")
        assert cliente.get(descarga.replace("https://cotizat.online", "")).status_code == 200


@pytest.mark.parametrize("cc", MERCADOS)
def test_el_sitemap_anuncia_la_pagina_y_no_el_json(cc):
    urls = [x["loc"] for x in pp.urls_sitemap(cc, "https://cotizat.online")]
    assert "https://cotizat.online" + pp.ruta_mano_obra(cc) in urls
    assert not any(u.endswith(".json") for u in urls)
    assert len(urls) == len(set(urls))


@pytest.mark.parametrize("cc", ["MX", "US"])
def test_cache_publico_sella_las_rutas(cc):
    from app import cache_publico

    assert cache_publico.es_ruta_publica_cacheable(pp.ruta_mano_obra(cc))
    assert cache_publico.es_ruta_publica_cacheable(pp.ruta_json(cc))
    assert not cache_publico.es_ruta_publica_cacheable("/acceso")


def test_claves_i18n_completas():
    import json as _json
    from pathlib import Path

    base = Path(__file__).resolve().parent.parent / "app" / "locales"
    es = _json.loads((base / "es.json").read_text(encoding="utf-8"))
    en = _json.loads((base / "en.json").read_text(encoding="utf-8"))
    claves = {k for k in es if k.startswith("mo.")}
    assert claves, "sin claves mo.*"
    assert claves == {k for k in en if k.startswith("mo.")}
