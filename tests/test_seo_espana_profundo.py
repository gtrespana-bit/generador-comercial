"""SEO profundo de España y arquitectura de silos para mercados hispanos."""
from __future__ import annotations

import csv
import html as _html
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.seo import es_indexable
from app.seo_espana import ARTICULOS, ORDEN_ARTICULOS, _tabla_mano_obra

BASE = Path(__file__).resolve().parents[1]


def _cliente():
    return TestClient(app, base_url="https://cotizat.test")


def _titulo(html: str) -> str:
    match = re.search(r"<title>([^<]+)</title>", html)
    return _html.unescape(match.group(1)) if match else ""


def _descripcion(html: str) -> str:
    match = re.search(r'<meta name="description" content="([^"]*)"', html)
    return _html.unescape(match.group(1)) if match else ""


def _palabras(html: str) -> int:
    texto = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S)
    return len(re.sub(r"<[^>]+>", " ", texto).split())


def test_espana_tiene_tres_intenciones_long_tail_propias():
    assert len(ARTICULOS) == 3
    assert set(ORDEN_ARTICULOS) == set(ARTICULOS)
    assert {a["pais"] for a in ARTICULOS.values()} == {"ES"}
    assert {a["slug"] for a in ARTICULOS.values()} == {
        "plantilla-presupuesto-reforma-espana",
        "precio-hora-mano-obra-construccion-espana",
        "bc3-presupuestos-reformas-espana",
    }


@pytest.mark.parametrize("slug", ORDEN_ARTICULOS)
def test_articulo_espanol_tiene_canonica_locale_schema_y_contenido(slug):
    articulo = ARTICULOS[slug]
    ruta = f"/es/guia/{slug}"
    with _cliente() as client:
        resp = client.get(ruta)
    assert resp.status_code == 200
    html = resp.text
    assert _titulo(html) == articulo["title"]
    assert len(_descripcion(html)) <= 160
    assert f'<link rel="canonical" href="https://cotizat.test{ruta}">' in html
    assert f'hreflang="es-ES" href="https://cotizat.test{ruta}"' in html
    assert f'hreflang="x-default" href="https://cotizat.test{ruta}"' in html
    assert 'lang="es-ES"' in html
    assert '"@type": "Article"' in html or '"@type":"Article"' in html
    assert '"inLanguage": "es-ES"' in html or '"inLanguage":"es-ES"' in html
    assert "FAQPage" in html
    assert _palabras(html) >= 750
    assert "España" in html
    assert "noindex" not in (resp.headers.get("x-robots-tag") or "")


def test_howto_solo_en_los_dos_procedimientos_espanoles():
    with _cliente() as client:
        plantilla = client.get("/es/guia/plantilla-presupuesto-reforma-espana").text
        bc3 = client.get("/es/guia/bc3-presupuestos-reformas-espana").text
        precios = client.get("/es/guia/precio-hora-mano-obra-construccion-espana").text
    assert "HowTo" in plantilla
    assert "HowTo" in bc3
    assert "HowTo" not in precios


def test_tabla_seo_usa_los_mismos_precios_que_la_matriz_espanola():
    with (BASE / "basedatos_partidas/salida/precios_recursos_espana.csv").open(
        encoding="utf-8-sig"
    ) as archivo:
        matriz = {
            fila["codigo_recurso"]: fila
            for fila in csv.DictReader(archivo, delimiter=";")
            if fila.get("codigo_recurso")
        }
    tabla = _tabla_mano_obra()
    por_oficio = {fila[0]: fila for fila in tabla["filas"]}
    assert por_oficio["Oficial de 1.ª albañil"][1] == f"{matriz['MO-OF1-ALB']['precio_referencia']} €/h"
    assert por_oficio["Peón o ayudante"][1] == f"{matriz['MO-AYU']['precio_referencia']} €/h"
    assert por_oficio["Oficial electricista"][1] == f"{matriz['MO-OF1-ELE']['precio_referencia']} €/h"


def test_tabla_seo_deriva_su_fecha_de_la_matriz_espanola():
    """Fase 2: la nota ya no lleva el mes escrito a mano; sale de los datos.

    Antes decía «de agosto de 2026» como literal: al reconsultar la matriz
    habría seguido diciendo agosto para siempre. Ahora el mes se deriva de
    las `fecha_consulta` de los oficios publicados.
    """
    from app.fechas_texto import consulta_es

    with (BASE / "basedatos_partidas/salida/precios_recursos_espana.csv").open(
        encoding="utf-8-sig"
    ) as archivo:
        matriz = {
            fila["codigo_recurso"]: fila
            for fila in csv.DictReader(archivo, delimiter=";")
            if fila.get("codigo_recurso")
        }
    oficios = (
        "MO-OF1-ALB", "MO-AYU", "MO-OF1-PIN",
        "MO-OF1-PLO", "MO-OF1-ELE", "MO-OF1-CARPM",
    )
    esperado = consulta_es(
        [matriz[c]["fecha_consulta"] for c in oficios if c in matriz]
    )
    tabla = _tabla_mano_obra()
    assert esperado  # la matriz vigente documenta sus consultas
    assert f"Precios consultados {esperado}." in tabla["nota"]


def test_url_historica_redirige_al_silo_y_no_duplica_documento():
    casos = {
        "/guia/plantilla-presupuesto-reforma-espana": "/es/guia/plantilla-presupuesto-reforma-espana",
        "/guia/apu-panete-colombia": "/co/guia/apu-panete-colombia",
        "/guia/cotizar-remodelacion-mexico": "/mx/guia/cotizar-remodelacion-mexico",
    }
    with _cliente() as client:
        for antigua, canonica in casos.items():
            resp = client.get(antigua, follow_redirects=False)
            assert resp.status_code == 301
            assert resp.headers["location"] == canonica
            assert client.get(canonica).status_code == 200


def test_un_articulo_no_se_puede_publicar_bajo_otro_pais():
    with _cliente() as client:
        assert client.get("/mx/guia/plantilla-presupuesto-reforma-espana").status_code == 404
        assert client.get("/co/guia/precio-hora-mano-obra-construccion-espana").status_code == 404
        assert client.get("/es/guia/apu-panete-colombia").status_code == 404


def test_sitemap_solo_anuncia_las_canonicas_de_pais():
    with _cliente() as client:
        sitemap = client.get("/sitemap.xml").text
    for slug in ORDEN_ARTICULOS:
        assert f"<loc>https://cotizat.test/es/guia/{slug}</loc>" in sitemap
        assert f"<loc>https://cotizat.test/guia/{slug}</loc>" not in sitemap
    assert "<loc>https://cotizat.test/co/guia/apu-panete-colombia</loc>" in sitemap
    assert "<loc>https://cotizat.test/guia/apu-panete-colombia</loc>" not in sitemap


def test_landing_y_hubs_de_espana_enlazan_el_corpus_completo():
    with _cliente() as client:
        paginas = [
            client.get("/es/").text,
            client.get("/es/software-presupuestos").text,
            client.get("/es/apu").text,
            client.get("/es/remodelacion").text,
            client.get("/mapa-del-sitio").text,
        ]
    for slug in ORDEN_ARTICULOS:
        ruta = f"/es/guia/{slug}"
        assert ruta in paginas[0]
        assert ruta in paginas[-1]
        # Cada hub de intención refuerza el silo completo.
        assert all(ruta in pagina for pagina in paginas[1:4])


def test_rutas_de_guias_de_pais_son_indexables():
    assert es_indexable("/es/guia/plantilla-presupuesto-reforma-espana")
    assert es_indexable("/co/guia/apu-panete-colombia")
    assert not es_indexable("/es/guia/")
    assert not es_indexable("/xx/guia/plantilla-presupuesto-reforma-espana")
