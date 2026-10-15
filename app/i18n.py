"""Soporte mínimo de idiomas para CotizaT.

Por ahora: español (es, por defecto) e inglés (en). El idioma se resuelve
desde el prefijo de la URL (/en/...) o desde la cookie ``cotizat_lang``.
"""
from __future__ import annotations

IDIOMAS_SOPORTADOS = ("es", "en")
IDIOMA_POR_DEFECTO = "es"


def normalizar_idioma(valor: str | None) -> str:
    v = (valor or "").strip().lower()
    if v.startswith("en"):
        return "en"
    return "es"


def idioma_desde_cookie(cookie_header: str | None) -> str:
    if not cookie_header:
        return IDIOMA_POR_DEFECTO
    for parte in cookie_header.split(";"):
        parte = parte.strip()
        if parte.startswith("cotizat_lang="):
            return normalizar_idioma(parte.split("=", 1)[1])
    return IDIOMA_POR_DEFECTO
