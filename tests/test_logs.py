"""E4-022 — logs estructurados sin datos sensibles innecesarios.

El modo JSON se activa solo con ``COTIZAT_LOG_JSON`` (apagado por omisión),
es idempotente y **siempre** redacta credenciales embebidas en URLs, tanto en
el mensaje como en las trazas de excepción.
"""
import json
import logging

import pytest

from app.logs import (
    LOGGER_NOMBRE,
    FormatoJSON,
    configurar_logs,
    redactar,
)


def test_redactar_sustituye_credenciales_embebidas():
    assert redactar("postgres://usuario:clave@host/bd rota") == (
        "postgres://<redactado>@host/bd rota"
    )
    # Sin credenciales no se toca nada
    assert redactar("sqlite:///tmp/base.db") == "sqlite:///tmp/base.db"
    assert redactar("mensaje sin urls") == "mensaje sin urls"


def test_formato_json_es_parseable_y_con_campos_esperados():
    formateador = FormatoJSON()
    registro = logging.LogRecord(
        name=LOGGER_NOMBRE, level=logging.ERROR, pathname="x", lineno=1,
        msg="fallo con postgres://usuario:clave@host/bd", args=(), exc_info=None,
    )
    salida = formateador.format(registro)
    payload = json.loads(salida)
    assert payload["level"] == "ERROR"
    assert payload["logger"] == LOGGER_NOMBRE
    assert payload["msg"] == "fallo con postgres://<redactado>@host/bd"
    assert "ts" in payload
    assert "traceback" not in payload


def test_formato_json_incluye_metricas_seguras_del_catalogo():
    formateador = FormatoJSON()
    registro = logging.LogRecord(
        name=LOGGER_NOMBRE, level=logging.WARNING, pathname="x", lineno=1,
        msg="catalogo_busqueda_sin_resultados", args=(), exc_info=None,
    )
    registro.evento = "catalogo_busqueda_sin_resultados"
    registro.organizacion_id = 7
    registro.consulta = "impermeabilización especial"
    payload = json.loads(formateador.format(registro))
    assert payload["evento"] == "catalogo_busqueda_sin_resultados"
    assert payload["organizacion_id"] == 7
    assert payload["consulta"] == "impermeabilización especial"


def test_formato_json_incluye_traza_redactada():
    formateador = FormatoJSON()
    try:
        raise RuntimeError("postgres://usuario:clave@host no responde")
    except RuntimeError:
        import sys

        registro = logging.LogRecord(
            name=LOGGER_NOMBRE, level=logging.ERROR, pathname="x", lineno=1,
            msg="fallo grave", args=(), exc_info=sys.exc_info(),
        )
        salida = formateador.format(registro)
    payload = json.loads(salida)
    assert "RuntimeError" in payload["traceback"]
    assert "usuario:clave" not in payload["traceback"]
    assert "<redactado>" in payload["traceback"]


def test_configuracion_idempotente_y_por_omision_apagada(monkeypatch):
    monkeypatch.delenv("COTIZAT_LOG_JSON", raising=False)
    logger = logging.getLogger(LOGGER_NOMBRE)
    # Estado inicial sin handlers JSON
    for handler in list(logger.handlers):
        if getattr(handler, "_cotizat_json", False):
            logger.removeHandler(handler)

    assert configurar_logs() is False
    assert sum(1 for h in logger.handlers if getattr(h, "_cotizat_json", False)) == 0

    assert configurar_logs(activo=True) is True
    assert configurar_logs(activo=True) is True  # idempotente: no duplica
    json_handlers = [h for h in logger.handlers if getattr(h, "_cotizat_json", False)]
    assert len(json_handlers) == 1

    assert configurar_logs(activo=False) is False
    assert not [h for h in logger.handlers if getattr(h, "_cotizat_json", False)]


def test_variable_de_entorno_activa_el_modo_json(monkeypatch):
    monkeypatch.setenv("COTIZAT_LOG_JSON", "true")
    assert configurar_logs() is True
    monkeypatch.setenv("COTIZAT_LOG_JSON", "off")
    assert configurar_logs() is False
