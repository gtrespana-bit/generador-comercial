"""Alias de país: las URLs que la gente teclea o que quedaron en enlaces viejos.

Nadie escribe ``/co/`` para Colombia ni ``/en-gb/`` para Reino Unido. Escribe
``/colombia``, ``/reino-unido`` o ``/espana``. Hasta ahora esas rutas
devolvían 404: era tráfico perdido y, peor, autoridad perdida si algún enlace
externo, correo o documento antiguo apunta a ellas (un 404 no transfiere
nada; un 301 sí).

Este módulo no crea contenido nuevo: mapea el nombre del país a su código
canónico y deja que el middleware responda 301 a la URL real. Nunca se
anuncia en el sitemap ni se enlaza desde el sitio: es una red de recuperación
para URLs que llegan de fuera.
"""
from __future__ import annotations

import re
from urllib.parse import quote, unquote

#: Nombres de país tal y como se teclean (sin acentos, con y sin ellos, y en
#: los dos idiomas del sitio) → código ISO del registro de mercados.
ALIAS_PAIS: dict[str, str] = {
    # Hispanoamérica
    "venezuela": "VE",
    "colombia": "CO",
    "mexico": "MX",
    "méxico": "MX",
    "peru": "PE",
    "perú": "PE",
    "chile": "CL",
    "argentina": "AR",
    "ecuador": "EC",
    "republica-dominicana": "DO",
    "república-dominicana": "DO",
    "dominican-republic": "DO",
    "rd": "DO",
    "uruguay": "UY",
    "paraguay": "PY",
    "bolivia": "BO",
    "panama": "PA",
    "panamá": "PA",
    "costa-rica": "CR",
    "guatemala": "GT",
    "honduras": "HN",
    "el-salvador": "SV",
    "salvador": "SV",
    "nicaragua": "NI",
    # España
    "espana": "ES",
    "españa": "ES",
    "spain": "ES",
    # Mercados de habla inglesa
    "estados-unidos": "US",
    "eeuu": "US",
    "ee-uu": "US",
    "usa": "US",
    "united-states": "US",
    "reino-unido": "GB",
    "inglaterra": "GB",
    "gran-bretana": "GB",
    "great-britain": "GB",
    "uk": "GB",
    "united-kingdom": "GB",
    "irlanda": "IE",
    "ireland": "IE",
    "australia": "AU",
    "canada": "CA",
    "canadá": "CA",
}

#: Sección equivalente cuando el mercado habla inglés. ``precios`` → ``prices``
#: es la única traducción que hace falta: ``guia`` y ``apu`` se escriben igual
#: en las dos rutas. Lo que no esté aquí cae al índice del mercado, que es un
#: destino vivo; mandar a una ruta traducida a medias acabaría en 404.
_SECCIONES_EN = {
    "precios": "prices",
    "precios-unitarios": "prices",
    "prices": "prices",
    "guia": "guia",
    "guide": "guia",
    "guides": "guia",
    "apu": "apu",
}

#: Rutas que SÍ llevan barra final (raíz y raíz de mercado). El resto se
#: normaliza sin barra: es la forma que declaran la canónica y el sitemap.
_RAIZ_CON_BARRA = re.compile(r"^/(?:[a-z]{2}|en-[a-z]{2})?/$")


def base_mercado(codigo: str) -> str:
    """Prefijo canónico de un mercado: ``/co/`` o ``/en-us/``."""
    from .paises import PAISES

    mercado = PAISES.get(codigo.upper()) or {}
    if mercado.get("idioma") == "en":
        return f"/en-{codigo.lower()}/"
    return f"/{codigo.lower()}/"


def destino_alias(path: str) -> str | None:
    """URL canónica a la que redirigir ``path``, o ``None`` si no es un alias.

    Solo devuelve destinos que existen: la raíz del mercado y las secciones
    que ese mercado publica de verdad. Un alias nunca debe llevar a un 404.
    """
    segmentos = [s for s in path.split("/") if s]
    if not segmentos:
        return None
    codigo = ALIAS_PAIS.get(unquote(segmentos[0]).strip().lower())
    if not codigo:
        return None
    base = base_mercado(codigo)
    resto = segmentos[1:]
    if not resto:
        return base

    from .paises import PAISES

    en = (PAISES.get(codigo) or {}).get("idioma") == "en"
    seccion = unquote(resto[0]).strip().lower()
    if en:
        traducida = _SECCIONES_EN.get(seccion)
        if not traducida:
            return base
        resto = [traducida, *resto[1:]]
    elif seccion not in ("precios", "precios-unitarios", "guia", "apu",
                         "remodelacion", "software-presupuestos"):
        return base
    return base + "/".join(resto)


def normalizar_barra(path: str) -> str | None:
    """Quita la barra final sobrante (``/mx/precios/`` → ``/mx/precios``).

    Starlette responde 307 a esa variante, y un 307 es *temporal*: Google
    conserva las dos URLs en el índice. Un 301 consolida la autoridad en la
    canónica, que es la que anuncian el sitemap y el ``<link rel=canonical>``.
    """
    if len(path) <= 1 or not path.endswith("/"):
        return None
    if _RAIZ_CON_BARRA.match(path):
        return None
    return path.rstrip("/") or "/"


def ubicacion(path: str, query: str = "") -> str:
    """``Location`` seguro para una cabecera HTTP (no-ASCII percent-encoded)."""
    destino = quote(path, safe="/")
    return f"{destino}?{query}" if query else destino
