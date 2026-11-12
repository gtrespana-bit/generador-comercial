"""Cobertura comercial e itinerarios de rastreo de mercados LATAM."""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.paises import ORDEN_SELECTOR, PAISES
from app.seo_latam_comercial import ESCENARIOS
from app.seo_latam_contenido import MERCADOS
from app.services import precios_publicos as pp


@pytest.fixture(scope="module")
def client():
    with TestClient(app, base_url="https://cotizat.test") as cliente:
        yield cliente


def test_escenarios_cubren_exactamente_los_mercados_latinoamericanos():
    latam = {cc for cc in ORDEN_SELECTOR if PAISES[cc]["idioma"] == "es" and cc != "ES"}
    assert set(ESCENARIOS) == set(MERCADOS) == latam
    assert len({escenario[1] for escenario in ESCENARIOS.values()}) == len(latam)


@pytest.mark.parametrize("cc", MERCADOS)
def test_pagina_comercial_local_indexable_y_enlazada(client, cc):
    client.cookies.clear()
    ruta = f"/{cc.lower()}/software-presupuestos"
    respuesta = client.get(ruta)
    assert respuesta.status_code == 200
    assert "noindex" not in respuesta.headers.get("x-robots-tag", "")
    assert f'<link rel="canonical" href="https://cotizat.test{ruta}">' in respuesta.text
    assert f'hreflang="{PAISES[cc]["locale"]}"' in respuesta.text
    for texto in ESCENARIOS[cc]:
        assert texto in respuesta.text
    assert f"<loc>https://cotizat.test{ruta}</loc>" in client.get("/sitemap.xml").text
    assert f'href="{ruta}"' in client.get(f"/{cc.lower()}/").text


def test_ficha_localizada_sin_apartado_indexable_se_enlaza_desde_indice(client, monkeypatch):
    cc = "CO"
    indice = pp._indice(cc)
    slug_ap, slug = next(iter(indice["partidas"]))
    ficha = indice["partidas"][(slug_ap, slug)]
    registro = {ficha["codigo"]: {"titulo": ficha["titulo"]}}
    monkeypatch.setattr(pp, "_localizado", lambda pais: registro if pais == cc else {})
    assert pp.partida_indexable(cc, slug_ap, slug)
    assert not pp.apartado_indexable(cc, slug_ap)
    ruta = pp.ruta_partida(cc, slug_ap, slug)
    client.cookies.clear()
    respuesta = client.get(pp.ruta_indice(cc))
    assert respuesta.status_code == 200
    assert "noindex" not in respuesta.headers.get("x-robots-tag", "")
    assert f'href="{ruta}"' in respuesta.text
    assert ruta in client.get('/sitemap-precios-co.xml').text
    assert "noindex" not in client.get(ruta).headers.get("x-robots-tag", "")


def test_se_priorizan_apartados_indexables_en_puentes_parciales(monkeypatch):
    from app.seo_precios import enlaces_catalogo

    cc = "CO"
    indice = pp._indice(cc)
    slug_ap, apartado = next((slug, ap) for slug, ap in indice["apartados"].items() if len(ap["partidas"]) >= 3)
    codigos = [indice["partidas"][(slug_ap, p["slug"])]["codigo"] for p in apartado["partidas"][:3]]
    monkeypatch.setattr(pp, "_localizado", lambda pais: {c: {} for c in codigos} if pais == cc else {})
    assert pp.apartado_indexable(cc, slug_ap)
    enlaces = enlaces_catalogo(cc, "prueba")
    assert enlaces["apartados"]
    assert all(pp.path_indexable(cc, ap["ruta"]) for ap in enlaces["apartados"])
