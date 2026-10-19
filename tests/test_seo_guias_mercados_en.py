"""SEO de los mercados anglófonos: guías long-tail, titulares y duplicados.

Hasta esta sesión solo Reino Unido tenía artículos con URL propia; Estados
Unidos, Irlanda, Australia y Canadá existían en Google solo con landing y
hubs. Estas pruebas fijan el paquete que los iguala:

- 12 artículos (3 por mercado) con 200, title/H1 propios, tablas de datos
  y FAQ/Article en el JSON-LD, enlazados desde su landing y en el sitemap.
- Un artículo bajo el prefijo de otro mercado devuelve 404 (antes 200 con
  la misma página: cinco URLs para un documento).
- Landing y hub ya no comparten <title>, y ninguna meta description de
  mercado se recorta a mitad de frase («…, sales.»).
- Las cifras publicadas son las de las herramientas de coste y el motor
  fiscal (nada de copiar números en dos sitios).
"""
from __future__ import annotations

import html as _html
import importlib.util
import re
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.seo_articulos_mercados_en import ARTICULOS, ORDEN_ARTICULOS, guias_de
from app.services.fiscalidad_eeuu import ESTADOS_EEUU

BASE = Path(__file__).resolve().parents[1]
MERCADOS = ("US", "IE", "AU", "CA")


def _cliente():
    return TestClient(app, base_url="https://cotizat.test")


def _titulo(html: str) -> str:
    m = re.search(r"<title>([^<]*)</title>", html)
    return _html.unescape(m.group(1).strip()) if m else ""


def _descripcion(html: str) -> str:
    m = re.search(r'<meta name="description" content="([^"]*)"', html)
    return m.group(1) if m else ""


def _palabras(html: str) -> int:
    txt = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S)
    return len(re.sub(r"<[^>]+>", " ", txt).split())


# ── Inventario de artículos ──────────────────────────────────────────────

def test_cada_mercado_tiene_tres_guias_en_orden():
    assert len(ARTICULOS) == 12
    assert set(ORDEN_ARTICULOS) == set(ARTICULOS)
    for codigo in MERCADOS:
        guias = guias_de(codigo)
        assert len(guias) == 3, codigo
        for guia in guias:
            assert guia["pais"] == codigo
            assert 40 <= len(guia["title"]) <= 80, guia["slug"]
            assert len(guia["description"]) <= 160, guia["slug"]
            assert len(guia["faq"]) >= 3, guia["slug"]


@pytest.mark.parametrize("slug", ORDEN_ARTICULOS)
def test_articulo_responde_con_schema_y_canonica_propia(slug):
    guia = ARTICULOS[slug]
    cc = guia["pais"].lower()
    with _cliente() as client:
        resp = client.get(f"/en-{cc}/guia/{slug}")
    assert resp.status_code == 200, slug
    html = resp.text
    assert _titulo(html) == guia["title"]
    assert f'<link rel="canonical" href="https://cotizat.test/en-{cc}/guia/{slug}">' in html
    assert '"@type": "Article"' in html or '"@type":"Article"' in html
    assert "FAQPage" in html
    assert _palabras(html) >= 700, slug


def test_guia_de_otro_mercado_es_404():
    """Nada de cinco URLs 200 para el mismo documento."""
    casos = [
        ("/en-us/guia/construction-quote-template-uk", 404),
        ("/en-us/guia/builder-rates-ireland", 404),
        ("/en-gb/guia/builder-rates-ireland", 404),
        ("/en-au/guia/gst-hst-on-construction-canada", 404),
        ("/en-ie/guia/presupuesto-de-obra", 404),  # genérica: vive en /en/
        ("/en/guia/presupuesto-de-obra", 200),
        ("/en-gb/guia/construction-quote-template-uk", 200),
    ]
    with _cliente() as client:
        for ruta, esperado in casos:
            assert client.get(ruta).status_code == esperado, ruta


# ── Tablas de datos ──────────────────────────────────────────────────────

def test_tabla_de_estados_sale_del_motor_fiscal():
    """La guía de sales tax no puede decir otra cosa que el motor."""
    with _cliente() as client:
        html = client.get("/en-us/guia/sales-tax-on-construction-by-state").text
    assert html.count("<tr>") == len(ESTADOS_EEUU) + 1  # cabecera + 51
    for estado in ESTADOS_EEUU:
        assert f"{estado.nombre} ({estado.codigo})" in html
    wa = next(e for e in ESTADOS_EEUU if e.codigo == "WA")
    assert f"{wa.tipo_medio}%" in html
    assert "Tax charged on the full contract price" in html


def _coste_empresa(modulo: str, clave: str) -> tuple[str, float]:
    spec = importlib.util.spec_from_file_location(modulo, BASE / f"tools/{modulo}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    nombre, salario = m.OFICIOS[clave][0], m.OFICIOS[clave][1]
    return nombre, float(salario)


def _precio_matriz(ruta: str, codigo: str) -> float:
    import csv

    with open(BASE / "basedatos_partidas" / "salida" / ruta, encoding="utf-8") as f:
        for fila in csv.DictReader(f, delimiter=";"):
            if fila["codigo_recurso"] == codigo:
                return float(fila["precio_referencia"])
    raise AssertionError(codigo)


@pytest.mark.parametrize(
    "ruta_guia,csv,clave",
    [
        ("/en-us/guia/construction-labor-cost-per-hour", "precios_recursos_estados_unidos.csv", "MO-OF1-PLO"),
        ("/en-ie/guia/builder-rates-ireland", "precios_recursos_irlanda.csv", "MO-OF1-ELE"),
        ("/en-au/guia/tradie-hourly-rates-australia", "precios_recursos_australia.csv", "MO-OF1-PLO"),
        ("/en-ca/guia/construction-labour-rates-canada", "precios_recursos_canada.csv", "MO-OF1-ELE"),
    ],
)
def test_las_cifras_de_mano_obra_son_las_de_la_matriz(ruta_guia, csv, clave):
    coste = _precio_matriz(csv, clave)
    with _cliente() as client:
        html = client.get(ruta_guia).text
    assert f"{coste:.2f}" in html, (ruta_guia, coste)


# ── Titulares y descripciones ────────────────────────────────────────────

@pytest.mark.parametrize("cc", ["us", "ie", "au", "ca", "gb"])
def test_landing_y_hub_no_comparten_title(cc):
    with _cliente() as client:
        landing = client.get(f"/en-{cc}/").text
        hub = client.get(f"/en-{cc}/software-presupuestos").text
    assert _titulo(landing) != _titulo(hub)
    for html in (landing, hub):
        desc = _descripcion(html)
        assert len(desc) <= 160
        # La coletilla entra entera: nada de «…, sales.» ni «analysis and.»
        assert desc.endswith("no card."), desc
        assert not desc.replace(". 7 days free, no card.", "").rstrip().endswith((" and", " or", " sales"))


def test_landing_usa_el_oficio_local():
    esperados = {
        "us": "US contractors",
        "ie": "Irish builders",
        "au": "tradies",
        "ca": "Canadian contractors",
    }
    with _cliente() as client:
        for cc, fragmento in esperados.items():
            html = client.get(f"/en-{cc}/").text
            assert fragmento in _titulo(html), cc


def test_descripcion_venezuela_no_queda_colgada():
    """Regresión del recortador: «Unit price analysis and.» no vale."""
    with _cliente() as client:
        html = client.get("/en-ve/").text
    assert "analysis and." not in _descripcion(html)


# ── Enlazado y sitemap ───────────────────────────────────────────────────

def test_cada_landing_enlaza_sus_guias():
    with _cliente() as client:
        for codigo in MERCADOS:
            html = client.get(f"/en-{codigo.lower()}/").text
            for guia in guias_de(codigo):
                assert f"/en-{codigo.lower()}/guia/{guia['slug']}" in html, guia["slug"]


def test_sitemap_anuncia_las_16_guias_de_mercado():
    with _cliente() as client:
        locs = re.findall(r"<loc>([^<]+)</loc>", client.get("/sitemap.xml").text)
    for guia in ARTICULOS.values():
        ruta = f"/en-{guia['pais'].lower()}/guia/{guia['slug']}"
        assert any(loc.endswith(ruta) for loc in locs), ruta
    assert any(loc.endswith("/en-gb/guia/cis-deduction-subcontractors") for loc in locs)


def test_hubs_con_cuerpo_de_mercado():
    """Los hubs dejan de ser el texto genérico de ~570 palabras."""
    with _cliente() as client:
        for cc in ("us", "ie", "au", "ca"):
            html = client.get(f"/en-{cc}/software-presupuestos").text
            assert _palabras(html) >= 750, cc
            assert f"/en-{cc}/guia/" in html  # related a sus artículos


def test_mapa_en_enlaza_guias_de_mercado():
    with _cliente() as client:
        html = client.get("/en/mapa-del-sitio").text
    assert "/en-us/guia/sales-tax-on-construction-by-state" in html
    assert "/en-gb/guia/construction-quote-template-uk" in html
    assert "/en-au/guia/tradie-hourly-rates-australia" in html


def test_keep_reading_solo_del_mismo_mercado():
    with _cliente() as client:
        html = client.get("/en-ie/guia/vat-on-construction-ireland").text
    assert "/en-ie/guia/builder-rates-ireland" in html
    # No enlaza la granja completa de los otros cuatro mercados.
    assert "/en-us/guia/construction-labor-cost-per-hour" not in html
    assert "/en-gb/guia/cis-deduction-subcontractors" not in html


def test_ortografia_us_en_articulos_us():
    """Los artículos de EE. UU. escriben «labor» y «license», no «labour»."""
    for guia in guias_de("US"):
        texto = str(guia)
        assert "labour" not in texto, guia["slug"]
    with _cliente() as client:
        cuerpo = client.get("/en-us/").text
    assert "colours" not in cuerpo  # marcador barato; el fuerte va arriba
