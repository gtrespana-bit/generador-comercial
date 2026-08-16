"""Logs estructurados sin datos sensibles innecesarios (E4-022).

Por omisión el logger ``cotizat`` sigue escribiendo texto plano como siempre.
Con ``COTIZAT_LOG_JSON=true`` cada línea pasa a ser un objeto JSON con marca de
tiempo, nivel, logger, mensaje y (si la hubo) la traza de la excepción. Eso
permite que Vercel o cualquier sumidero los indexe sin parseo ad hoc.

La **redacción** se aplica siempre, en ambos modos: las credenciales dentro de
URLs (``esquema://usuario:clave@host``) se sustituyen por ``<redactado>`` en el
mensaje y en las trazas. No se intenta adivinar qué es secreto: solo el patrón
inequívoco de credenciales embebidas en una conexión.
"""
from __future__ import annotations

import json
import logging
import os
import re
import traceback

#: user:password embebidos en una URL de conexión.
_CREDENCIAL_EN_URL = re.compile(r"://[^/@\s]+:[^/@\s]+@")

LOGGER_NOMBRE = "cotizat"


def redactar(texto: str) -> str:
    """Sustituye credenciales embebidas en URLs por un marcador."""
    return _CREDENCIAL_EN_URL.sub("://<redactado>@", str(texto))


class FormatoJSON(logging.Formatter):
    """Una línea JSON por registro, con la traza redactada si existe."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": redactar(record.getMessage()),
        }
        if record.exc_info:
            payload["traceback"] = redactar(
                "".join(traceback.format_exception(*record.exc_info))
            )
        return json.dumps(payload, ensure_ascii=False)


def configurar_logs(activo: bool | None = None) -> bool:
    """Activa (o desactiva) el formato JSON del logger ``cotizat``.

    Idempotente: volver a llamarla no duplica el handler. ``activo=None`` lee
    ``COTIZAT_LOG_JSON``; el valor seguro por omisión es apagado, para no
    cambiar el formato de los despliegues existentes sin quererlo.
    """
    if activo is None:
        activo = os.environ.get("COTIZAT_LOG_JSON", "").strip().lower() in {
            "1", "true", "yes", "on",
        }
    logger = logging.getLogger(LOGGER_NOMBRE)
    for handler in list(logger.handlers):
        if getattr(handler, "_cotizat_json", False):
            logger.removeHandler(handler)
    if activo:
        handler = logging.StreamHandler()
        handler._cotizat_json = True  # marca para la limpieza idempotente
        handler.setFormatter(FormatoJSON())
        logger.addHandler(handler)
    return activo
