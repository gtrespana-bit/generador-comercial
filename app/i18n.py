"""Soporte mínimo de idiomas para CotizaT.

Idiomas soportados: español (es, por defecto) e inglés (en). El idioma se
resuelve desde el prefijo de la URL (/en/, /en-es/, ...) o desde la cookie
``cotizat_lang``. El país se resuelve por separado en el router.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

IDIOMAS_SOPORTADOS = ("es", "en")
IDIOMA_POR_DEFECTO = "es"
LOCALES_DIR = Path(__file__).resolve().parent / "locales"


def normalizar_idioma(valor: str | None) -> str:
    v = (valor or "").strip().lower()
    if v.startswith("en"):
        return "en"
    if v.startswith("es"):
        return "es"
    return IDIOMA_POR_DEFECTO


def idioma_desde_cookie(cookie_header: str | None) -> str:
    if not cookie_header:
        return IDIOMA_POR_DEFECTO
    for parte in cookie_header.split(";"):
        parte = parte.strip()
        if parte.startswith("cotizat_lang="):
            return normalizar_idioma(parte.split("=", 1)[1])
    return IDIOMA_POR_DEFECTO


def idioma_desde_ruta(path: str | None) -> str | None:
    """Extrae el idioma de una ruta con prefijo /en o /en-xx."""
    p = (path or "").strip().lower()
    if p == "/en" or p.startswith("/en/"):
        return "en"
    if p.startswith("/en-"):
        return "en"
    return None


@lru_cache(maxsize=8)
def _cargar_traducciones(idioma: str) -> dict[str, Any]:
    idioma = normalizar_idioma(idioma)
    archivo = LOCALES_DIR / f"{idioma}.json"
    try:
        return json.loads(archivo.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def t(clave: str, idioma: str | None = None, **kwargs: Any) -> str:
    """Traduce una clave; si falta, devuelve la clave (fallback visible)."""
    lang = normalizar_idioma(idioma)
    valor = _cargar_traducciones(lang).get(clave)
    if valor is None and lang != IDIOMA_POR_DEFECTO:
        valor = _cargar_traducciones(IDIOMA_POR_DEFECTO).get(clave)
    if valor is None:
        valor = clave
    if isinstance(valor, str) and kwargs:
        try:
            return valor.format(**kwargs)
        except (KeyError, ValueError):
            return valor
    return valor if isinstance(valor, str) else str(valor)
