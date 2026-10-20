"""Dominio canónico único: el host de la petición nunca manda en el SEO.

El 20/10/2026 producción servía por ``www.cotizat.online`` (el borde de
Vercel redirigía el apex al www) mientras canónicas, sitemap, robots y
correos declaraban ``https://cotizat.online``. Estas pruebas fijan la
mitad que vive en el código: con ``COTIZAT_PUBLIC_URL`` en el apex, toda
salida SEO usa el apex aunque la petición llegue por www o por un
preview, y ``/readyz`` delata el host no canónico para poder verificar
el borde sin abrir el panel de Vercel.
"""
from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from app.main import app

APEX = "https://cotizat.online"


@pytest.fixture
def entorno_canonico(monkeypatch):
    monkeypatch.setenv("COTIZAT_PUBLIC_URL", APEX)


@pytest.mark.parametrize(
    "base_url", ["https://www.cotizat.online", "https://preview-xyz.vercel.app"]
)
def test_canonica_y_hreflang_salen_del_apex_aunque_lleguen_por_otro_host(
    entorno_canonico, base_url
):
    with TestClient(app, base_url=base_url) as cliente:
        respuesta = cliente.get("/mx/guia/mano-obra-construccion-mexico")
    assert respuesta.status_code == 200
    ruta = "/mx/guia/mano-obra-construccion-mexico"
    assert f'<link rel="canonical" href="{APEX}{ruta}">' in respuesta.text
    assert f'hreflang="es-MX" href="{APEX}{ruta}"' in respuesta.text
    assert base_url not in respuesta.text.split('rel="canonical"')[1].split(">")[0]


def test_sitemap_y_robots_usan_el_apex(entorno_canonico):
    with TestClient(app, base_url="https://www.cotizat.online") as cliente:
        sitemap = cliente.get("/sitemap.xml").text
        robots = cliente.get("/robots.txt").text
    assert f"<loc>{APEX}/mx/guia/mano-obra-construccion-mexico</loc>" in sitemap
    assert "<loc>https://www.cotizat.online" not in sitemap
    assert f"Sitemap: {APEX}/sitemap.xml" in robots


def test_readyz_publica_el_diagnostico_seo_y_de_host(entorno_canonico):
    with TestClient(app, base_url="https://www.cotizat.online") as cliente:
        respuesta = cliente.get("/readyz")
    checks = respuesta.json()["checks"]
    assert checks["dominio_canonico"] == APEX
    assert checks["host_recibido"] == "www.cotizat.online"
    assert checks["host_es_canonico"].startswith("no")
    assert int(checks["seo_articulos_es"]) == 54
    assert int(checks["seo_sitemap_urls"]) > 150
    assert checks["seo_matriz_latam"].endswith("paises con filas")
    # El conteo de referencias en BD debe EVALUARSE, no degradar: en
    # producción salió «no evaluado» porque la condición de «activo»
    # mezclaba boolean con entero y PostgreSQL la rechazaba.
    assert re.match(r"\d+ referencias nacionales en \d+ paises", checks["precios_bd"])


def test_condicion_activo_una_sola_forma_por_motor(monkeypatch):
    """`activo = 1 OR activo IS TRUE` parecía portable y Postgres la
    rechaza al analizarla. El selector emite una sola forma por motor."""
    from app import health

    monkeypatch.setattr(health, "DATABASE_IS_SQLITE", True)
    assert health._condicion_activo() == "activo = 1"
    monkeypatch.setattr(health, "DATABASE_IS_SQLITE", False)
    assert health._condicion_activo() == "activo IS TRUE"


def test_readyz_por_el_apex_dice_que_el_host_es_canonico(entorno_canonico):
    with TestClient(app, base_url=APEX) as cliente:
        respuesta = cliente.get("/readyz")
    assert respuesta.json()["checks"]["host_es_canonico"] == "si"


def test_x_robots_tag_solo_fuera_de_lo_indexable():
    with TestClient(app, base_url=APEX) as cliente:
        guia = cliente.get("/bo/guia/computos-metricos-presupuesto-bolivia")
        acceso = cliente.get("/acceso")
    assert "noindex" not in (guia.headers.get("x-robots-tag") or "")
    assert "noindex" in (acceso.headers.get("x-robots-tag") or "")
