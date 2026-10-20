"""Validación conjunta del corpus hispano: rutas, datos, silos y ausencia de inventos."""
from __future__ import annotations

import csv
import json
import re
from collections import Counter
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.paises import PAISES
from app.seo import es_indexable, ruta_guia
from app.seo_articulos import articulos_de_pais, ficha_articulo, lista_articulos
from app import seo_latam
from app.seo_latam import MATRIZ, RECURSOS_VE, OFICIOS, guias, importe, tabla_mano_obra
from app.seo_latam_contenido import MERCADOS

NUEVOS = guias()


@pytest.fixture(scope="module")
def _cliente_compartido():
    with TestClient(app, base_url="https://cotizat.test") as client:
        yield client


@pytest.fixture
def cliente(_cliente_compartido):
    # Mantener un único lifespan, pero no heredar la elección de idioma de
    # la comprobación negativa /en-us/ de un caso anterior.
    _cliente_compartido.cookies.clear()
    return _cliente_compartido


def _schemas(texto):
    return [json.loads(s) for s in re.findall(
        r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', texto, re.S
    )]


def test_cobertura_sin_cambiar_la_intencion_de_las_urls_historicas():
    todos = lista_articulos()
    assert len(NUEVOS) == 46
    assert len(todos) == 54
    assert len({a["slug"] for a in todos}) == len(todos)
    assert Counter(a["pais"] for a in todos) == {codigo: 3 for codigo in (*MERCADOS, "ES")}
    assert tuple(MERCADOS) == ("MX", "CO", "PE", "CL", "AR", "VE", "EC", "DO", "PA", "CR", "GT", "HN", "SV", "NI", "UY", "PY", "BO")
    for codigo, perfil in MERCADOS.items():
        if perfil.get("existente"):
            assert ficha_articulo(perfil["existente"])["pais"] == codigo


@pytest.mark.parametrize("articulo", NUEVOS, ids=lambda a: a["slug"])
def test_cada_recurso_tiene_canonica_locale_schema_y_faq_visibles(cliente, articulo):
    codigo, slug = articulo["pais"], articulo["slug"]
    ruta = f"/{codigo.lower()}/guia/{slug}"
    respuesta = cliente.get(ruta)
    assert respuesta.status_code == 200
    html = respuesta.text
    assert ruta_guia(slug) == ruta
    assert es_indexable(ruta)
    assert f'<link rel="canonical" href="https://cotizat.test{ruta}">' in html
    locale = PAISES[codigo]["locale"]
    assert f'lang="{locale}"' in html
    assert f'hreflang="{locale}" href="https://cotizat.test{ruta}"' in html
    assert f'hreflang="x-default" href="https://cotizat.test{ruta}"' in html
    assert html.count("<h1>") == 1
    assert articulo["h1"] in html
    assert 40 <= len(articulo["description"]) <= 160
    assert len(articulo["secciones"]) >= 4
    assert "noindex" not in (respuesta.headers.get("x-robots-tag") or "")
    schemas = _schemas(html)
    assert any(s.get("@type") == "Article" and s.get("inLanguage") == locale for s in schemas)
    assert not any(s.get("@type") == "HowTo" for s in schemas)
    assert any(s.get("@type") == "FAQPage" for s in schemas)
    for item in articulo["faq"]:
        assert item["q"] in html
    for _, enlace in articulo["related"]:
        assert f'href="{enlace}"' in html
    # No publicar accidentalmente el mismo artículo en España u otro silo.
    assert cliente.get(f"/es/guia/{slug}").status_code == 404
    legacy = cliente.get(f"/guia/{slug}", follow_redirects=False)
    assert legacy.status_code == 301
    assert legacy.headers["location"] == ruta
    # Esta petición fija la cookie en inglés; se hace después de la ruta ES.
    assert cliente.get(f"/en-us/guia/{slug}").status_code == 404


@pytest.mark.parametrize("codigo", MERCADOS)
def test_landing_tres_hubs_y_guia_historica_enlazan_el_corpus_local(cliente, codigo):
    propios = articulos_de_pais(codigo)
    paginas = [cliente.get(f"/{codigo.lower()}/{tema}").text for tema in (
        "", "software-presupuestos", "apu", "remodelacion"
    )]
    for articulo in propios:
        ruta = ruta_guia(articulo["slug"])
        assert all(ruta in pagina for pagina in paginas)
    perfil = MERCADOS[codigo]
    if perfil.get("existente"):
        html = cliente.get(ruta_guia(perfil["existente"])).text
        for articulo in propios:
            if articulo["slug"] != perfil["existente"]:
                assert ruta_guia(articulo["slug"]) in html
    assert perfil["labor"] in paginas[0]


def test_sitemap_y_mapa_anuncian_solo_canonicas(cliente):
    sitemap = cliente.get("/sitemap.xml").text
    mapa = cliente.get("/mapa-del-sitio").text
    for articulo in NUEVOS:
        ruta = ruta_guia(articulo["slug"])
        assert sitemap.count(f"<loc>https://cotizat.test{ruta}</loc>") == 1
        assert f"<loc>https://cotizat.test/guia/{articulo['slug']}</loc>" not in sitemap
        assert ruta in mapa


@pytest.mark.parametrize("codigo", [c for c in MERCADOS if c != "VE"])
def test_cifras_fechas_y_calidad_son_las_del_csv_importado_por_producto(codigo):
    with MATRIZ.open(encoding="utf-8-sig", newline="") as archivo:
        matriz = {
            f["codigo_recurso"]: f for f in csv.DictReader(archivo, delimiter=";")
            if f["pais_codigo"] == codigo
        }
    tabla = tabla_mano_obra(codigo)
    assert len(tabla["filas"]) == len(OFICIOS)
    for codigo_recurso, nombre, central, rango, calidad, fecha in tabla["filas"]:
        fila = matriz[codigo_recurso]
        assert central == importe(fila["precio_referencia"], codigo) + "/h"
        assert fecha == fila["fecha_consulta"]
        if fila["confianza"] == "derivado":
            assert calidad == "Derivado de otro oficio"
        if Decimal(fila["precio_min"]) == Decimal(fila["precio_max"]):
            assert rango == "Sin dispersión documentada"
        else:
            assert importe(fila["precio_min"], codigo) in rango
            assert importe(fila["precio_max"], codigo) in rango
        assert nombre
    assert "no un intervalo estadístico" in tabla["nota"]


@pytest.mark.parametrize("codigo", [c for c in MERCADOS if c != "VE"])
def test_nota_resume_las_fechas_de_consulta_publicadas(codigo):
    """Fase 2: el resumen de frescura resume las fechas que la tabla muestra."""
    from app.fechas_texto import consulta_es

    tabla = tabla_mano_obra(codigo)
    esperado = consulta_es([fila[5] for fila in tabla["filas"]])
    assert esperado
    assert f"Precios consultados {esperado}." in tabla["nota"]


def test_venezuela_no_se_presenta_como_coste_empresa_nacional():
    with RECURSOS_VE.open(encoding="utf-8") as archivo:
        base = json.load(archivo)["mano_obra"]
    tabla = tabla_mano_obra("VE")
    assert tabla["cabecera"][2] == "Tarifa interna"
    for recurso, _, central, rango, calidad, fecha in tabla["filas"]:
        assert central == importe(str(base[recurso]["precio"]), "VE") + "/h"
        assert rango == "No documentado"
        assert "no coste empresa validado" in calidad
    assert "No es una encuesta salarial" in tabla["nota"]


def test_venezuela_deriva_su_revision_de_recursos_json():
    """Fase 2: el mes de revisión sale de la clave `_revision`, no del código."""
    from app.fechas_texto import mes_anio_es

    with RECURSOS_VE.open(encoding="utf-8") as archivo:
        revision = mes_anio_es(str(json.load(archivo).get("_revision") or ""))
    tabla = tabla_mano_obra("VE")
    assert revision
    for *_, fecha in tabla["filas"]:
        assert fecha == f"Revisión del cuadro: {revision}"
    assert f"revisión declarada de {revision}" in tabla["nota"]


def test_ausencia_de_artefactos_no_inventa_referencias(monkeypatch):
    monkeypatch.setattr(seo_latam, "_matriz", lambda: {})
    monkeypatch.setattr(seo_latam, "_base_venezuela", lambda: {})
    for codigo in MERCADOS:
        tabla = tabla_mano_obra(codigo)
        assert tabla["filas"] == []
        assert "Datos no disponibles" in tabla["nota"]
        assert "No hay una pareja" in seo_latam._ejemplo_cuadrilla(codigo)


def test_lector_rechaza_otra_moneda_unidad_datos_invalidos_y_respaldo(tmp_path, monkeypatch):
    ruta = tmp_path / "matriz.csv"
    campos = ["codigo_recurso", "pais_codigo", "moneda", "categoria", "unidad_fuente", "confianza", "precio_referencia"]
    with ruta.open("w", encoding="utf-8", newline="") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=campos, delimiter=";")
        writer.writeheader()
        for codigo, moneda, unidad, confianza, valor in (
            ("ok", "MXN", "h", "referencia", "125"),
            ("divisa", "USD", "h", "referencia", "125"),
            ("unidad", "MXN", "dia", "referencia", "125"),
            ("respaldo", "MXN", "h", "respaldo", "125"),
            ("infinito", "MXN", "h", "referencia", "Infinity"),
            ("nan", "MXN", "h", "referencia", "NaN"),
            ("negativo", "MXN", "h", "referencia", "-1"),
        ):
            writer.writerow(dict(zip(campos, (codigo, "MX", moneda, "mano_obra", unidad, confianza, valor))))
    with monkeypatch.context() as patch:
        patch.setattr(seo_latam, "MATRIZ", ruta)
        seo_latam._matriz.cache_clear()
        try:
            assert set(seo_latam._matriz()["MX"]) == {"ok"}
        finally:
            seo_latam._matriz.cache_clear()


def test_lector_sin_csv_y_sin_json_devuelve_vacio(tmp_path, monkeypatch):
    with monkeypatch.context() as patch:
        patch.setattr(seo_latam, "MATRIZ", tmp_path / "ausente.csv")
        patch.setattr(seo_latam, "RECURSOS_VE", tmp_path / "ausente.json")
        seo_latam._matriz.cache_clear()
        seo_latam._base_venezuela.cache_clear()
        try:
            assert seo_latam._matriz() == {}
            assert seo_latam._base_venezuela() == {}
        finally:
            seo_latam._matriz.cache_clear()
            seo_latam._base_venezuela.cache_clear()


@pytest.mark.parametrize("codigo, esperado", [
    ("MX", "1,234.50 MXN"), ("CO", "1.234,50 COP"),
    ("PE", "1.234,50 PEN"), ("PY", "1.234,50 PYG"),
    ("CR", "1.234,50 CRC"), ("NI", "1,234.50 NIO"),
])
def test_formato_horario_local_conserva_precision_interna(codigo, esperado):
    assert importe("1234.5", codigo) == esperado
