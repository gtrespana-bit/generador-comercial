"""El 500 del panel: página propia, referencia rastreable y estado 500 real.

Antes de esto, un fallo no capturado devolvía el texto crudo de Starlette
(«Internal Server Error»): en inglés, sin salidas, sin decir a quién avisar y
sin nada que permitir cruzarlo con la tabla de errores internos. Estas pruebas
fijan las tres piezas:

1. la referencia se deriva de la **huella** del fallo, así que el operador la
   encuentra en la tabla sin una columna nueva;
2. el manejador sirve HTML para un navegador y JSON para una API, siempre con
   ``500`` —nunca 200— y con la referencia en la cabecera;
3. la página no filtra nada del fallo y no depende de la sesión ni de la base.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from starlette.requests import Request

from app.services.errores_internos import huella_de
from app.services.operacion import RegistroErroresMiddleware, referencia_de_error

RAIZ = Path(__file__).resolve().parents[1]


def _peticion(ruta: str = "/admin", acepta: str = "text/html") -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": ruta,
            "query_string": b"",
            "headers": [(b"accept", acepta.encode())],
            "state": {},
        }
    )


def _resolver(respuesta):
    """Consume una respuesta ASGI y devuelve (estado, cabeceras, cuerpo)."""
    mensajes = []

    async def enviar(mensaje):
        mensajes.append(mensaje)

    async def recibir():
        return {"type": "http.request", "body": b"", "more_body": False}

    asyncio.run(respuesta({"type": "http", "method": "GET", "headers": []}, recibir, enviar))
    inicio = mensajes[0]
    cuerpo = b"".join(m.get("body", b"") for m in mensajes[1:])
    return inicio["status"], dict(inicio["headers"]), cuerpo.decode("utf-8", "ignore")


def test_la_referencia_identifica_el_fallo_y_no_la_peticion():
    huella = huella_de("GET", "/admin", "ValueError", "boom")
    assert referencia_de_error(huella) == huella[:10]
    assert len(referencia_de_error(huella)) == 10


def test_sin_huella_la_referencia_sigue_existiendo():
    una, otra = referencia_de_error(), referencia_de_error()
    assert len(una) == len(otra) == 10
    assert una != otra


def test_la_pagina_del_500_es_html_con_referencia_y_estado_real():
    from app.main import _error_interno

    peticion = _peticion("/admin", "text/html")
    peticion.state.referencia_error = "ref-demo-01"
    respuesta = asyncio.run(_error_interno(peticion, RuntimeError("base caída")))
    estado, cabeceras, cuerpo = _resolver(respuesta)
    assert estado == 500
    assert cabeceras[b"x-referencia-error"] == b"ref-demo-01"
    assert "ref-demo-01" in cuerpo
    assert "Algo se rompió" in cuerpo
    # Ni trazas ni mensajes internos en el navegador.
    assert "base caída" not in cuerpo
    assert "Traceback" not in cuerpo


def test_una_api_recibe_json_y_no_html():
    from app.main import _error_interno

    respuesta = asyncio.run(_error_interno(_peticion("/api/presupuestos", "*/*"), RuntimeError("x")))
    estado, cabeceras, cuerpo = _resolver(respuesta)
    assert estado == 500
    assert cuerpo.strip().startswith("{")
    assert "referencia" in cuerpo
    assert cabeceras[b"x-referencia-error"]


def test_si_la_plantilla_falla_el_500_sigue_siendo_un_500(monkeypatch):
    """La página de error no puede convertirse en un segundo 500."""
    from app.main import _error_interno
    from app.routers import common

    class _Roto:
        def TemplateResponse(self, *a, **k):
            raise RuntimeError("jinja roto")

    monkeypatch.setattr(common, "TEMPLATES", _Roto())
    estado, cabeceras, cuerpo = _resolver(
        asyncio.run(_error_interno(_peticion("/admin"), RuntimeError("x")))
    )
    assert estado == 500
    assert "Referencia:" in cuerpo
    assert cabeceras[b"x-referencia-error"]


def test_el_middleware_deja_la_referencia_en_el_estado_de_la_peticion():
    """Así el manejador enseña el mismo id que quedó en la tabla de errores."""
    vistos = {}

    async def app_que_falla(scope, receive, send):
        raise ValueError("revienta siempre")

    middleware = RegistroErroresMiddleware(app_que_falla)

    async def recibir():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def enviar(mensaje):
        pass

    scope = {"type": "http", "method": "GET", "path": "/admin", "headers": [], "state": {}}
    with pytest.raises(ValueError):
        asyncio.run(middleware(scope, recibir, enviar))
    vistos["referencia"] = scope["state"].get("referencia_error")
    assert vistos["referencia"]
    assert vistos["referencia"] == referencia_de_error(
        huella_de("GET", "/admin", "ValueError", "revienta siempre")
    )


def test_la_pagina_500_no_depende_de_la_sesion_ni_de_la_base():
    html = (RAIZ / "app" / "templates" / "500.html").read_text(encoding="utf-8")
    assert "base_admin" not in html
    assert "{% extends" not in html
    assert "noindex" in html
    for prohibido in ("traceback", "secret", "{{ exc"):
        assert prohibido not in html.lower()
