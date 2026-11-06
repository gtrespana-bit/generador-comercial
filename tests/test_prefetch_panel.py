"""El panel precarga la página a la que vas antes de que hagas clic.

Se resuelve con *Speculation Rules* —una regla que el navegador ejecuta solo— y
no con JavaScript propio ni con una reescritura del panel. La lista es blanca y
la construye el servidor con los enlaces de navegación que ya conoce (las seis
áreas y las pestañas del área activa): pasar el puntero por encima de un enlace
de acción no debe disparar nada.
"""
from __future__ import annotations

import json
import re

from fastapi.testclient import TestClient

from app.main import app


def _reglas(html: str) -> dict:
    """Extrae y valida el JSON de la regla de especulación de la página."""
    encontrado = re.search(
        r'<script type="speculationrules" nonce="([^"]+)">(.*?)</script>', html, re.S
    )
    assert encontrado, "la página del panel no trae reglas de precarga"
    assert encontrado.group(1), "la regla sin `nonce` la bloquea la CSP"
    return json.loads(encontrado.group(2))


def test_el_panel_precarga_sus_secciones_al_pasar_el_raton(operador, cliente_panel):
    respuesta = cliente_panel.get("/admin")
    assert respuesta.status_code == 200
    reglas = _reglas(respuesta.text)
    assert "prerender" not in reglas, "prerender ejecutaría la página entera: no"
    prefetch = reglas["prefetch"]
    assert len(prefetch) == 1
    assert prefetch[0]["source"] == "list"
    assert prefetch[0]["eagerness"] == "moderate"
    urls = prefetch[0]["urls"]
    for area in ("/admin", "/admin/clientes", "/admin/ingresos", "/admin/web",
                 "/admin/analitica", "/admin/sistema"):
        assert area in urls, f"falta {area} en la lista de precarga"


def test_las_pestanas_del_area_activa_tambien_se_precargan(operador, cliente_panel):
    respuesta = cliente_panel.get("/admin/ingresos")
    assert respuesta.status_code == 200
    urls = _reglas(respuesta.text)["prefetch"][0]["urls"]
    assert any("tab=" in url for url in urls), urls


def test_la_lista_no_lleva_enlaces_de_accion(operador, cliente_panel):
    """Pasar el ratón por encima no debe preparar un cambio de estado."""
    urls = _reglas(cliente_panel.get("/admin").text)["prefetch"][0]["urls"]
    peligrosas = ("salir", "activar", "conceder", "revocar", "borrar", "eliminar",
                  "reenviar", "publicar", "/api/")
    for url in urls:
        assert not any(p in url for p in peligrosas), url


def test_sin_sesion_no_se_precargan_paginas_del_panel():
    """La precarga de una página que redirige al acceso sería trabajo perdido."""
    anonimo = TestClient(app, base_url="https://cotizat.test", raise_server_exceptions=False)
    respuesta = anonimo.get("/admin", follow_redirects=False)
    assert respuesta.status_code in (303, 307, 401, 403)
