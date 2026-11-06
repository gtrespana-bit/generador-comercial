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


# ---------------------------------------------------------------------------
# Regresión del 06/11/2026: con la audiencia por fin escribiendo filas, el
# panel empezó a devolver 500 con
# ``AttributeError: 'datetime.date' object has no attribute 'date'`` en
# ``app/services/audiencia.py``. El trozo de serie diaria solo se ejecuta
# cuando hay visitas, así que con la tabla vacía nunca se había probado.
# ---------------------------------------------------------------------------

from datetime import date, datetime  # noqa: E402

from app.services.analitica import resumen_analitica  # noqa: E402
from app.services.audiencia import resumen_audiencia  # noqa: E402

HOY = date(2026, 11, 5)
AYER = date(2026, 11, 4)


def _sembrar_dos_visitas() -> None:
    with SessionLocal() as db:
        db.add_all(
            [
                VisitaPagina(
                    ruta="/",
                    ip_hash="a" * 64,
                    referente="https://www.google.com/",
                    created_at=datetime(2026, 11, 4, 10, 0),
                ),
                VisitaPagina(
                    ruta="/precios",
                    ip_hash="b" * 64,
                    created_at=datetime(2026, 11, 5, 11, 30),
                ),
                # Segunda visita del mismo visitante: no suma visitante nuevo.
                VisitaPagina(
                    ruta="/precios",
                    ip_hash="b" * 64,
                    created_at=datetime(2026, 11, 5, 12, 0),
                ),
            ]
        )
        db.commit()


def test_la_serie_diaria_se_arma_cuando_hay_visitas():
    _sembrar_dos_visitas()
    with SessionLocal() as db:
        datos = resumen_audiencia(db, dias=7, hoy=HOY)

    assert datos["disponible"] is True
    assert len(datos["serie"]) == 7
    assert datos["serie"][-1]["fecha"] == HOY
    assert datos["serie"][-1]["vistas"] == 2
    assert datos["serie"][-1]["visitantes"] == 1
    assert datos["serie"][-2]["fecha"] == AYER
    assert datos["serie"][-2]["vistas"] == 1
    assert datos["vistas_ventana"] == 3
    assert datos["visitantes_hoy"] == 1
    assert datos["paginas_top"][0] == {"ruta": "/precios", "vistas": 2}


def test_resumen_audiencia_acepta_fechas_y_datetimes():
    """El panel pasa ``date``; la API pública del servicio tolera ambos."""
    _sembrar_dos_visitas()
    with SessionLocal() as db:
        en_dias = resumen_audiencia(db, dias=7, hoy=HOY)
        en_datetimes = resumen_audiencia(
            db, dias=7, hoy=datetime(2026, 11, 5, 18, 0)
        )
    assert len(en_dias["serie"]) == len(en_datetimes["serie"]) == 7
    assert en_dias["vistas_ventana"] == en_datetimes["vistas_ventana"] == 3


def test_el_panel_de_analitica_pinta_la_audiencia_sin_romperse():
    """El 500 real: ``resumen_analitica`` con filas en ``visitas_pagina``."""
    _sembrar_dos_visitas()
    with SessionLocal() as db:
        resumen = resumen_analitica(db, hoy=HOY, dias=30)

    audiencia = resumen["audiencia"]
    assert audiencia["disponible"] is True
    assert audiencia["vistas_ventana"] == 3
    assert audiencia["serie"][-1]["fecha"] == HOY
