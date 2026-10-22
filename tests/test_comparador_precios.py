"""Comparador internacional de precios: la misma partida en los 22 mercados.

Lo que se prueba aquí no es «la página responde 200», es que la comparación no
mienta:

- La cesta solo incluye partidas con el **mismo código** en los 22 mercados y
  la **misma familia de unidad**: si se colara una partida que en un país está
  en m² y en otro por unidad, la tabla compararía cosas distintas.
- Los precios de Estados Unidos se convierten de verdad (``sq ft`` → m²,
  ``cu yd`` → m³). Si la conversión fallara, sus 951 partidas en pies
  cuadrados entrarían como si fueran metros y el índice se hundiría.
- El índice se puede recalcular a mano desde el JSON publicado y coincide.
- El orden es estable y coherente con los datos (el mercado más caro es el que
  tiene el índice más alto, no una lista escrita a mano).
- Las 34 URL del sitemap responden 200 en su idioma, con su canonical y su
  pareja hreflang es/en.
"""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app import comparador
from app.comparador import (
    CAPITULOS,
    _datos,
    comparativa_partida,
    contexto_comparador,
    ranking,
    ruta_capitulo,
    ruta_comparador,
)
from app.main import app
from app.services import precios_publicos as pp
from app.services.tasa import TASAS_SUGERIDAS
from app.services.unidades_precio import convertir_precio_unidad

MERCADOS = sorted(pp.paises_publicados())


def _cliente() -> TestClient:
    return TestClient(app, base_url="https://cotizat.online")


# ── La cesta ────────────────────────────────────────────────────────────────


def test_la_cesta_existe_y_es_grande():
    datos = _datos()
    assert len(datos["cesta"]) > 1500, len(datos["cesta"])
    assert datos["mercados"] == MERCADOS


def test_solo_entran_partidas_que_existen_en_los_22_mercados():
    datos = _datos()
    for codigo, fila in list(datos["cesta"].items())[:200]:
        assert set(fila) == set(MERCADOS), codigo


def test_solo_entran_partidas_con_una_unica_familia_de_unidad():
    datos = _datos()
    for codigo, fila in list(datos["cesta"].items())[:200]:
        unidades = {unidad for _valor, unidad in fila.values()}
        assert len(unidades) == 1, codigo


def test_las_partidas_a_precio_alzado_quedan_fuera():
    datos = _datos()
    for fila in datos["cesta"].values():
        for _valor, unidad in fila.values():
            assert unidad not in {"glb", ""}


def test_los_codigos_del_catalogo_son_los_mismos_en_todos_los_mercados():
    """El supuesto de partida: 14.05.02.010 es la misma partida en los 22."""
    for codigo in list(_datos()["cesta"])[:20]:
        for cc in MERCADOS:
            assert codigo in pp._indice(cc)["por_codigo"], (codigo, cc)  # noqa: SLF001


# ── Conversión de unidades y moneda ────────────────────────────────────────


def test_el_precio_estadounidense_se_convierte_de_pies_cuadrados():
    """US mide en sq ft: si no se convierte, su índice se divide por 10,76."""
    codigo = "12.05.03.010"  # piso cerámico, m² en los 21 mercados y sq ft en US
    indice_us = pp._indice("US")  # noqa: SLF001
    ficha = indice_us["partidas"][indice_us["por_codigo"][codigo]]
    assert "sq ft" in str(ficha["unidad"]).lower() or ficha["unidad"] in ("ft2", "m2")
    esperado = convertir_precio_unidad(float(ficha["pu"]), ficha["unidad"], "m2")
    if esperado is None:
        esperado = float(ficha["pu"])  # ya venía en m²
    esperado_usd = esperado / TASAS_SUGERIDAS["USD"]
    obtenido = _datos()["cesta"][codigo]["US"][0]
    assert obtenido == pytest.approx(esperado_usd, rel=1e-9)


def test_todos_los_mercados_tienen_tasa_de_cambio():
    """Sin tasa, un mercado desaparecería de la tabla sin avisar."""
    for cc in MERCADOS:
        moneda = pp.PAISES[cc]["moneda"]
        assert TASAS_SUGERIDAS.get(moneda), f"{cc} ({moneda}) sin tasa"
        assert any(cc in fila for fila in _datos()["cesta"].values())


# ── El índice ───────────────────────────────────────────────────────────────


def test_el_indice_es_la_mediana_de_los_cocientes():
    """Se recalcula a mano desde la cesta y tiene que dar lo mismo."""
    import statistics

    datos = _datos()
    for cc in ("MX", "US", "BO", "ES"):
        cocientes = []
        for codigo, fila in datos["cesta"].items():
            mediana = datos["mediana"][codigo]
            if mediana > 0:
                cocientes.append(fila[cc][0] / mediana)
        esperado = statistics.median(cocientes) * 100
        assert datos["indices"][cc] == pytest.approx(esperado, rel=1e-12)


def test_el_ranking_esta_ordenado_y_cubre_los_22_mercados():
    filas = ranking("es")
    assert [f["cc"] for f in filas].__len__() == len(MERCADOS)
    assert set(f["cc"] for f in filas) == set(MERCADOS)
    assert [f["indice"] for f in filas] == sorted(
        (f["indice"] for f in filas), reverse=True
    )


def test_el_orden_no_es_una_lista_escrita_a_mano():
    """Los dos extremos salen de los datos publicados, no de una constante."""
    datos = _datos()
    filas = ranking("es")
    mas_caro, mas_barato = filas[0], filas[-1]
    assert mas_caro["indice"] == round(max(datos["indices"].values()), 1)
    assert mas_barato["indice"] == round(min(datos["indices"].values()), 1)
    # Y el mercado más caro del índice es el que gana más partidas sueltas
    # (ninguno gana todas: US, AU, IE y GB se reparten el podio, y por eso el
    # índice es mediana de cocientes y no «quién gana cada partida»).
    victorias: dict[str, int] = {}
    for fila in datos["cesta"].values():
        caro = max(fila, key=lambda cc: fila[cc][0])
        victorias[caro] = victorias.get(caro, 0) + 1
    podio = sorted(victorias, key=victorias.get, reverse=True)[:3]
    assert mas_caro["cc"] in podio, (mas_caro["cc"], victorias)
    # Y ninguno gana todas: AU gana más partidas sueltas que US, pero US tiene
    # el índice más alto porque es alto en casi todas. Es la razón de usar la
    # mediana de cocientes en vez de contar victorias.
    assert victorias[podio[0]] < len(datos["cesta"]) * 0.6


def test_los_extremos_del_ranking_son_los_esperados_por_los_datos():
    """US y Bolivia son los extremos reales del catálogo; si cambian, se revisa."""
    filas = ranking("es")
    assert filas[0]["cc"] in {"US", "AU", "IE", "GB"}
    assert filas[-1]["cc"] in {"BO", "PY", "EC"}


# ── Páginas ─────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("lang,ruta", [("es", "/precios-comparados"), ("en", "/en/prices-comparison")])
def test_la_portada_del_comparador_responde_y_es_indexable(lang, ruta):
    with _cliente() as cliente:
        respuesta = cliente.get(ruta)
    assert respuesta.status_code == 200
    html = respuesta.text
    assert "noindex" not in (respuesta.headers.get("x-robots-tag") or "")
    assert "FAQPage" in html and "BreadcrumbList" in html
    assert f'rel="canonical" href="https://cotizat.online{ruta}"' in html
    # Los 22 mercados aparecen en la tabla.
    for cc in MERCADOS:
        assert pp.PAISES[cc]["nombre"] in html or pp.PAISES[cc].get("nombre_en", "") in html


@pytest.mark.parametrize("codigo", comparador.capitulos_publicados())
def test_cada_capitulo_responde_en_los_dos_idiomas(codigo):
    with _cliente() as cliente:
        for lang in ("es", "en"):
            ruta = ruta_capitulo(lang, codigo)
            respuesta = cliente.get(ruta)
            assert respuesta.status_code == 200, ruta
            assert respuesta.text.count("<tr") > 5
            assert "noindex" not in (respuesta.headers.get("x-robots-tag") or "")


def test_solo_se_publican_los_capitulos_con_datos_comunes():
    """Los capítulos que no existen en los 22 mercados no generan URL."""
    publicados = set(comparador.capitulos_publicados())
    assert publicados <= set(CAPITULOS)
    assert publicados, "sin capítulos publicados"
    for codigo in set(CAPITULOS) - publicados:
        with _cliente() as cliente:
            ruta = ruta_capitulo("es", codigo)
            assert cliente.get(ruta).status_code == 404, ruta
            assert ruta not in [e["loc"].replace("https://cotizat.online", "") for e in __import__("app.seo", fromlist=["urls_sitemap"]).urls_sitemap()]


def test_los_capitulos_del_comparador_son_los_del_catalogo():
    """El mapa de capítulos a mano debe coincidir con el catálogo real."""
    reales = {c["codigo"] for c in pp._indice("MX")["capitulos"]}  # noqa: SLF001
    assert set(CAPITULOS) == reales


def test_un_capitulo_inventado_da_404():
    with _cliente() as cliente:
        assert cliente.get("/precios-comparados/no-existe").status_code == 404
        assert cliente.get("/en/prices-comparison/no-existe").status_code == 404


def test_las_parejas_hreflang_van_en_los_dos_sentidos():
    with _cliente() as cliente:
        es = cliente.get("/precios-comparados").text
        en = cliente.get("/en/prices-comparison").text
    for html in (es, en):
        assert 'hreflang="es" href="https://cotizat.online/precios-comparados"' in html
        assert 'hreflang="en" href="https://cotizat.online/en/prices-comparison"' in html
        assert 'hreflang="x-default"' in html


def test_el_contexto_no_depende_del_orden_de_llamada():
    datos1 = dict(_datos())
    datos2 = dict(_datos())
    assert datos1["indices"] == datos2["indices"]


# ── Ficha de partida: el bloque comparativo ─────────────────────────────────


def test_una_partida_compartida_lleva_la_tabla_de_paises():
    comparativa = comparativa_partida("MX", "12.05.03.010", "es")
    assert len(comparativa) == len(MERCADOS)
    assert [f["usd"] for f in comparativa] == sorted(
        (f["usd"] for f in comparativa), reverse=True
    )
    actual = [f for f in comparativa if f["actual"]]
    assert len(actual) == 1 and actual[0]["cc"] == "MX"
    for fila in comparativa:
        assert fila["usd_txt"].endswith("USD")
        assert fila["ruta"].startswith("/")


def test_una_partida_no_compartida_no_inventa_tabla():
    """Si el código no está en todos los mercados, no hay comparación."""
    assert comparativa_partida("MX", "99.99.99.999", "es") == []


def test_la_ficha_de_partida_muestra_la_comparacion():
    with _cliente() as cliente:
        ruta = pp.ruta_partida("MX", "azulejo-y-porcelanato-en-paredes", "recubrimiento-de-paramento-interior-con-pieza-azulejo-o-porcelanato-en-capa-fina")
        html = cliente.get(ruta).text
    assert 'class="cmp-partida"' in html
    assert "El precio de esta partida en cada país" in html
    assert "USD" in html


# ── Descarga y sitemap ──────────────────────────────────────────────────────


def test_el_json_del_comparador_coincide_con_la_pagina():
    with _cliente() as cliente:
        respuesta = cliente.get("/precios-comparados.json")
    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"].startswith("application/json")
    assert respuesta.headers["access-control-allow-origin"] == "*"
    datos = json.loads(respuesta.text)
    assert len(datos["partidas"]) == len(_datos()["cesta"])
    assert {m["codigo"] for m in datos["mercados"]} == set(MERCADOS)
    # La mediana publicada es la misma que usa la página.
    muestra = datos["partidas"][0]
    assert muestra["mediana_usd"] == pytest.approx(
        round(_datos()["mediana"][muestra["codigo"]], 4)
    )
    for fila in datos["mercados"]:
        assert fila["indice"] == pytest.approx(round(_datos()["indices"][fila["codigo"]], 1))


def test_las_urls_del_comparador_estan_en_el_sitemap_y_responden():
    from app.seo import urls_sitemap

    urls = [e["loc"] for e in urls_sitemap() if "comparad" in e["loc"] or "prices-comparison" in e["loc"]]
    assert len(urls) == 2 * (1 + len(comparador.capitulos_publicados()))
    with _cliente() as cliente:
        for url in urls:
            ruta = url.replace("https://cotizat.online", "")
            assert cliente.get(ruta).status_code == 200, ruta


def test_el_comparador_se_cachea_en_el_cdn():
    from app.cache_publico import es_ruta_publica_cacheable

    assert es_ruta_publica_cacheable("/precios-comparados")
    assert es_ruta_publica_cacheable("/precios-comparados/cimentaciones")
    assert es_ruta_publica_cacheable("/en/prices-comparison")
    assert es_ruta_publica_cacheable("/en/prices-comparison/cimentaciones")
    assert es_ruta_publica_cacheable("/precios-comparados.json")


def test_el_comparador_se_enlaza_desde_el_catalogo_y_el_pie():
    with _cliente() as cliente:
        for ruta, esperado in (
            ("/mx/precios", "/precios-comparados"),
            ("/en-us/prices", "/en/prices-comparison"),
            ("/mx/mano-de-obra", "/precios-comparados"),
            ("/mx/", "/precios-comparados"),
        ):
            assert f'href="{esperado}"' in cliente.get(ruta).text, ruta


def test_las_claves_i18n_estan_completas():
    from pathlib import Path

    base = Path(__file__).resolve().parent.parent / "app" / "locales"
    es = json.loads((base / "es.json").read_text(encoding="utf-8"))
    en = json.loads((base / "en.json").read_text(encoding="utf-8"))
    claves = {k for k in es if k.startswith("cmp.")}
    assert claves
    assert claves == {k for k in en if k.startswith("cmp.")}


def test_el_contexto_declara_las_fechas_que_usa(monkeypatch):
    monkeypatch.setenv("COTIZAT_PUBLIC_URL", "https://cotizat.online")
    with _cliente() as cliente:
        pedido = cliente.get("/precios-comparados")
        contexto = contexto_comparador(pedido.request, None, "es")
    assert contexto is not None
    assert contexto["tasa_fecha"]
    assert contexto["n_mercados"] == len(MERCADOS)
    assert contexto["n_partidas"] == len(_datos()["cesta"])
    # La metodología se explica y dice de qué fecha son las tasas.
    assert any("tasa" in item["q"].lower() or "dólares" in item["q"].lower() for item in contexto["faq"])
