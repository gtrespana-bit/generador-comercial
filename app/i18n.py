"""Soporte mínimo de idiomas para CotizaT.

Idiomas soportados: español (es, por defecto) e inglés (en). El idioma se
resuelve desde el prefijo de la URL (/en/, /en-es/, ...) o desde la cookie
``cotizat_lang``. El país se resuelve por separado en el router.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlsplit

IDIOMAS_SOPORTADOS = ("es", "en")
IDIOMA_POR_DEFECTO = "es"
LOCALES_DIR = Path(__file__).resolve().parent / "locales"

# Cookie que fija el idioma de la interfaz. La escribe el middleware cuando la
# ruta trae prefijo /en y el conmutador de idioma cuando el visitante elige
# español (que no tiene prefijo y, por tanto, el middleware no la toca).
COOKIE_IDIOMA = "cotizat_lang"
COOKIE_IDIOMA_MAX_AGE = 365 * 24 * 3600

# /en, /en/..., /en-mx, /en-mx/...
_RE_PREFIJO_EN = re.compile(r"^/en(?:-([A-Za-z]{2}))?(?=$|/)")


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


# --------------------------------------------------------------------------
# Rutas por idioma
# --------------------------------------------------------------------------
# El middleware de idioma reescribe /en-mx/apu en /mx/apu antes de enrutar, así
# que dentro de la aplicación `request.url.path` es SIEMPRE la ruta canónica en
# español. Estos helpers son los dos sentidos del viaje: de la canónica a la que
# ve el navegador (`ruta_en_idioma`) y de lo que envía un enlace a una ruta de
# la que fiarse (`ruta_segura`).


@lru_cache(maxsize=1)
def codigos_pais() -> frozenset[str]:
    """Códigos ISO de dos letras con landing propia (``mx``, ``es``, …)."""
    try:
        from .paises import PAISES
    except Exception:  # pragma: no cover - solo si faltara el módulo
        return frozenset()
    return frozenset(str(c).strip().lower() for c in PAISES)


def partir_ruta(path: str) -> tuple[str, str]:
    """Separa una ruta en ``(país, resto)``.

    Acepta la ruta canónica en español (``/mx/apu``) y la que ve el navegador
    en inglés (``/en-mx/apu``), porque el switcher se pinta antes de que el
    middleware reescriba la petición y los dos formatos llegan aquí.
    """
    p = urlsplit(str(path or "").strip()).path or "/"
    if not p.startswith("/"):
        p = "/" + p
    pais = ""
    m = _RE_PREFIJO_EN.match(p)
    if m:
        if m.group(1):
            pais = m.group(1).lower()
        p = p[m.end():] or "/"
        if not p.startswith("/"):
            p = "/" + p
    if not pais:
        partes = p.strip("/").split("/", 1)
        primero = partes[0].lower() if partes else ""
        if len(primero) == 2 and primero.isalpha() and primero in codigos_pais():
            pais = primero
            p = "/" + partes[1] if len(partes) > 1 and partes[1] else "/"
    return pais, (p or "/")


def ruta_en_idioma(path: str, idioma: str | None = None) -> str:
    """La misma página en el idioma pedido, conservando el país si lo hay.

    ``/apu`` → ``/en/apu`` · ``/mx/apu`` → ``/en-mx/apu`` · ``/`` → ``/en``.
    """
    pais, resto = partir_ruta(path)
    if normalizar_idioma(idioma) == "en":
        prefijo = "/en" + (f"-{pais}" if pais else "")
        return prefijo if resto == "/" else prefijo + resto
    if pais:
        return f"/{pais}" if resto == "/" else f"/{pais}{resto}"
    return resto or "/"


def ruta_segura(destino: str | None) -> str:
    """Sanea el ``?destino=`` del conmutador para que no sea un open redirect.

    Solo se aceptan rutas internas: empiezan por una única barra, no son
    relativas a protocolo (``//malo.com``), no vuelven al propio conmutador y
    se descartan la query y el fragmento, que se reincorporan aparte.
    """
    p = str(destino or "").strip()
    if not p or p.startswith("//"):
        return "/"
    partes = urlsplit(p)
    # Con esquema o dominio no es una ruta interna, aunque su `path` lo parezca
    # (``http://malo.com/x`` tiene path ``/x`` y sería un open redirect).
    if partes.scheme or partes.netloc:
        return "/"
    p = partes.path or "/"
    if not p.startswith("/") or p.startswith("//"):
        return "/"
    if "\\" in p or p.startswith("/idioma"):
        return "/"
    return p


def url_cambio_idioma(destino: str | None, idioma: str | None = None) -> str:
    """Enlace del conmutador: ``/idioma/en?destino=/apu`` (con la query)."""
    lang = normalizar_idioma(idioma)
    objetivo = str(destino or "/")
    return f"/idioma/{lang}?destino={quote(objetivo, safe='/?&=')}"


# ---------------------------------------------------------------------------
# Mensajes de la aplicación
# ---------------------------------------------------------------------------
# Los avisos que el usuario ve (errores de validación, confirmaciones) viven en
# el código en español: los lanzan los servicios como excepciones y los routers
# los pasan como parámetros de la URL (?error=, ?mensaje=) o en el JSON. En
# lugar de propagar claves por cada ``raise``, se traducen al pintarlos: el
# catálogo ``locales/mensajes_<idioma>.json`` va del texto español al texto en
# el idioma de destino, y lo que no esté catalogado se muestra tal cual.
_MENSAJES_DIR = LOCALES_DIR
_RE_PARAM_MENSAJE = re.compile(r"(\{[^{}]*\})")


@lru_cache(maxsize=8)
def _cargar_mensajes(idioma: str) -> dict[str, str]:
    idioma = normalizar_idioma(idioma)
    if idioma == IDIOMA_POR_DEFECTO:
        return {}
    try:
        datos = json.loads((_MENSAJES_DIR / f"mensajes_{idioma}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {k: v for k, v in datos.items() if isinstance(k, str) and isinstance(v, str)}


@lru_cache(maxsize=8)
def _patrones_mensajes(idioma: str) -> tuple[tuple[re.Pattern[str], str], ...]:
    """Mensajes con valores interpolados: ``(regex, plantilla_en)``."""
    patrones: list[tuple[re.Pattern[str], str]] = []
    for es, en in _cargar_mensajes(idioma).items():
        if "{" not in es:
            continue
        trozos = _RE_PARAM_MENSAJE.split(es)
        regex = "".join(
            re.escape(t) if not t.startswith("{") else "(.*)" for t in trozos
        )
        try:
            patrones.append((re.compile("^" + regex + "$", re.S), en))
        except re.error:  # pragma: no cover - catálogo mal formado
            continue
    return tuple(patrones)


def mensaje(texto: object, idioma: str | None = None,
            mercado: dict | None = None) -> str:
    """Traduce un mensaje escrito en español; si no está, lo devuelve igual.

    El catálogo está escrito en inglés de Estados Unidos, como la base del
    glosario de partidas, y ``mercado`` lo ajusta al vocabulario del país:
    un aviso que dice «estimate» en Estados Unidos dice «quote» en el Reino
    Unido, sin necesidad de un segundo catálogo por mercado.
    """
    if texto is None:
        return ""
    s = str(texto)
    lang = normalizar_idioma(idioma)
    if lang == IDIOMA_POR_DEFECTO or not s:
        return s
    catalogo = _cargar_mensajes(lang)
    if not catalogo:
        return s
    from app.services.variante_ingles import aplicar_variante

    def _variar(t: str) -> str:
        return aplicar_variante(t, mercado) if mercado else t

    directo = catalogo.get(s) or catalogo.get(s.strip())
    if directo is not None:
        return _variar(directo)
    for patron, plantilla in _patrones_mensajes(lang):
        m = patron.match(s) or patron.match(s.strip())
        if not m:
            continue
        try:
            return _variar(plantilla.format(*m.groups()))
        except (IndexError, KeyError):
            return _variar(plantilla)
    return s


def mensaje_request(request: object, texto: object) -> str:
    """Traduce ``texto`` al idioma que lleva el ``request``.

    Atajo para los routers que devuelven el error en el JSON de una API: en
    español el texto sale tal cual, así que no cambia nada respecto a antes.
    """
    lang = IDIOMA_POR_DEFECTO
    mercado = None
    try:
        estado = getattr(request, "state", None)
        lang = getattr(estado, "lang", "") or IDIOMA_POR_DEFECTO
        mercado = getattr(estado, "mercado", None)
    except Exception:  # pragma: no cover - request sin state
        lang = IDIOMA_POR_DEFECTO
    return mensaje(texto, lang, mercado)
