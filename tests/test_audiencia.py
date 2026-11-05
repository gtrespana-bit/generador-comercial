"""El middleware de audiencia debe contar de verdad las visitas públicas.

Motivo (incidente del 05/11/2026): `AudienciaMiddleware` hasheaba la IP con
`ip_de_request`, un nombre que `app/main.py` **nunca importaba**. El
`NameError` saltaba en cada página vista y el `except Exception` del middleware
—que existe para no romper nunca la respuesta del visitante— lo descartaba sin
dejar rastro. Resultado: la tabla `visitas_pagina` se creó, se migró y se
permisionó, y aun así /admin/analitica mostraba cero audiencia siempre.

La prueba recorre el camino real (petición HTTP → middleware → fila) para que
un fallo así no pueda volver a pasar inadvertido: los tests de `resumen_analitica`
parten de filas ya escritas a mano y nunca ejercitaban el middleware.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import VisitaPagina


def _visitas() -> list[VisitaPagina]:
    with SessionLocal() as db:
        return db.query(VisitaPagina).order_by(VisitaPagina.id).all()


def _limpiar() -> None:
    with SessionLocal() as db:
        db.query(VisitaPagina).delete()
        db.commit()


@pytest.fixture(autouse=True)
def _audiencia_limpia():
    _limpiar()
    yield
    _limpiar()


NAVEGADOR = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/140.0",
    "accept": "text/html,application/xhtml+xml",
}


def test_una_visita_publica_queda_registrada_con_ip_hasheada():
    with TestClient(app) as cliente:
        respuesta = cliente.get("/?audiencia=1", headers=NAVEGADOR)
    assert respuesta.status_code == 200

    filas = _visitas()
    assert len(filas) == 1, "la visita pública no se registró"
    visita = filas[0]
    assert visita.ruta == "/"
    # 64 caracteres = SHA-256 en hexadecimal. La IP nunca se guarda en claro.
    assert len(visita.ip_hash) == 64
    assert "127.0.0.1" not in visita.ip_hash
    assert visita.usuario_agent and "firefox" in visita.usuario_agent.lower()


def test_las_rutas_de_sistema_y_de_producto_no_cuentan_como_audiencia():
    with TestClient(app) as cliente:
        cliente.get("/healthz", headers=NAVEGADOR)
        cliente.get("/acceso", headers=NAVEGADOR)
    assert _visitas() == []


def test_un_buscador_no_es_un_visitante():
    with TestClient(app) as cliente:
        cliente.get(
            "/",
            headers={
                "user-agent": "Mozilla/5.0 (compatible; Googlebot/2.1)",
                "accept": "text/html",
            },
        )
    assert _visitas() == []
