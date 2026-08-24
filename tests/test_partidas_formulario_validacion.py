"""Regresión: el guardado de partidas no debe quedar bloqueado por la
validación nativa del navegador sobre controles ocultos.

Los campos de la ficha de partida viven dentro de pestañas ocultas (en el
modal del editor de presupuestos) y de un ``<details>`` plegado (en el
catálogo). Si un control quedaba inválido —stepMismatch de ``step="0.05"``
con valores legítimos como 0,60/0,40 o 0,35, o un decimal pegado con coma—
el navegador no podía enfocarlo y bloqueaba el submit con
«An invalid form control ... is not focusable».

Ahora ambos formularios desactivan la validación nativa (``novalidate``):
la validación real la hacen el JS del modal (nombre obligatorio, con error
visible) y el servidor (nombre y duplicados), y el error del servidor se
muestra dentro del propio formulario del catálogo.
"""
from __future__ import annotations

import re
from urllib.parse import parse_qs, urlsplit

from fastapi.testclient import TestClient

from app.main import app


def test_modal_editor_partida_desactiva_validacion_nativa():
    """El formulario del modal (form-editor-partida) lleva novalidate."""
    with TestClient(app) as client:
        r = client.get("/presupuestos/nuevo")
        assert r.status_code == 200
        assert 'id="form-editor-partida"' in r.text
        m = re.search(r'<form[^>]*id="form-editor-partida"[^>]*>', r.text)
        assert m, "no se encontró la etiqueta del formulario del modal"
        assert "novalidate" in m.group(0)


def test_formulario_catalogo_partida_desactiva_validacion_nativa():
    """El formulario del catálogo (/partidas/nueva) lleva novalidate."""
    with TestClient(app) as client:
        r = client.get("/partidas/nueva")
        assert r.status_code == 200
        m = re.search(r'<form[^>]*class="catalog-editor-form"[^>]*>', r.text)
        assert m, "no se encontró la etiqueta del formulario del catálogo"
        assert "novalidate" in m.group(0)


def test_campos_tiempo_aceptan_cualquier_decimal():
    """Los campos de tiempo no exigen step=0.05 (evita stepMismatch).

    Valores habituales como 0,60/0,40 (reparto 60/40) o 0,35 producen un
    cociente no entero por error de coma flotante y el navegador los daba
    por inválidos.
    """
    with TestClient(app) as client:
        r = client.get("/partidas/nueva")
        for campo in (
            "tiempo_estimado_horas",
            "tiempo_oficial_horas",
            "tiempo_ayudante_horas",
            "tiempo_equipo_horas",
        ):
            m = re.search(r'<input[^>]*name="%s"[^>]*>' % campo, r.text)
            assert m, f"no se encontró el campo {campo}"
            assert 'step="any"' in m.group(0)
            assert 'step="0.05"' not in m.group(0)


def test_guardar_partida_sin_nombre_muestra_el_error_en_la_pagina():
    """Sin validación nativa, el servidor rechaza el nombre vacío y el
    mensaje debe verse en el propio formulario (antes se perdía en la
    redirección y el usuario no recibía ninguna explicación)."""
    with TestClient(app) as client:
        r = client.post("/partidas/nueva", data={"nombre": "   "}, follow_redirects=False)
        assert r.status_code == 303
        loc = r.headers["location"]
        assert "error=" in loc
        error = parse_qs(urlsplit(loc).query)["error"][0]
        assert error

        r2 = client.get("/partidas/nueva?error=" + error)
        assert r2.status_code == 200
        assert error in r2.text
        assert 'class="alert alert-error"' in r2.text
