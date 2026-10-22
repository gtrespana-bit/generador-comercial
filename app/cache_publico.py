"""Caché CDN de la superficie pública (Fase 1.2 de la hoja de ruta).

Las páginas públicas (landing, guías, hubs, legal, sitemap, robots) son el
mismo HTML para todo visitante anónimo: el idioma sale SOLO de la URL
(prefijo /en) y el país de la ruta (/{cc}/), nunca de cookies ni de la
sesión. Eso permite que el CDN de Vercel las sirva desde el borde sin tocar
la función ni la base de datos.

¿Por qué no ``Vary: Cookie``? En Vercel, una respuesta con ``Vary: Cookie``
es directamente NO cacheable («vary key denied»): no se escribe ninguna
entrada en el CDN. La única vía es que la URL determine el contenido por
completo, y de eso se encarga ``IdiomaMiddleware`` apoyándose en el
predicado de este módulo. Fuera de esta superficie (panel, /soporte, /pago)
la cookie de idioma sigue mandando como siempre.

El sellado es conservador a propósito (fail-open): la cabecera de caché
compartida solo se añade si la respuesta es un GET 200 de una ruta de la
lista blanca, sin query, la petición no trae cookies de sesión y la
respuesta no fija cookies ni trae ya su propio Cache-Control. Ante
cualquier duda no se toca nada: un fallo aquí jamás debe romper una página
ni, peor, dejar contenido personal en un caché compartido.
"""
from __future__ import annotations

import re
from functools import lru_cache

# 5 minutos frescos en el CDN y un día de red de seguridad: mientras se
# revalida en segundo plano (stale-while-revalidate) o si el origen falla
# (stale-if-error), el borde sigue sirviendo la última copia buena.
CACHE_CONTROL_PUBLICO = (
    "public, max-age=0, s-maxage=300, "
    "stale-while-revalidate=86400, stale-if-error=86400"
)

# Si la petición trae cualquiera de estas cookies es (o fue) un usuario con
# sesión: su respuesta no se sella jamás, aunque la página sea pública.
_COOKIES_SESION = frozenset(
    {
        "cotizat_access_token",
        "cotizat_refresh_token",
        "cotizat_organization_id",
    }
)

_RUTAS_FIJAS = frozenset(
    {
        "/",
        "/conocer",
        "/mapa-del-sitio",
        "/novedades",
        "/como-funciona",
        "/calculadora",
        "/en/calculadora",
        "/robots.txt",
        "/sitemap.xml",
        "/sitemap_index.xml",
    }
)

# Misma forma que reconoce IdiomaMiddleware para el prefijo de idioma.
_RE_PREFIJO_EN = re.compile(r"^/en(?:-([A-Za-z]{2}))?(/.*)?$")


@lru_cache(maxsize=1)
def _patrones() -> tuple[re.Pattern, ...]:
    """Patrones de la lista blanca, desde las fuentes de verdad de la casa.

    Los códigos de país salen de ``app.paises.PAISES`` y los temas de hub de
    ``app.seo.TEMAS``: si mañana nace un mercado o un hub nuevo, entra solo
    (y el test de cobertura contra el sitemap caza cualquier olvido). La
    importación es perezosa para no crear ciclos: este módulo lo importa
    ``app.main`` muy arriba.
    """
    from .paises import PAISES
    from .seo import TEMAS

    cc = "|".join(sorted(re.escape(c.lower()) for c in PAISES))
    temas = "|".join(sorted(re.escape(t) for t in TEMAS))
    return (
        re.compile(r"^/guia/[^/]+$"),
        re.compile(r"^/legal/[^/]+$"),
        re.compile(rf"^/sitemap-precios-(?:{cc})\.xml$"),
        re.compile(rf"^/(?:{cc})/?$"),
        re.compile(rf"^/(?:{cc})/guia/[^/]+$"),
        re.compile(rf"^/(?:{cc})/(?:{temas})$"),
        re.compile(rf"^/(?:{temas})$"),
        # Fase 5: precios públicos por país. País e idioma salen solo de
        # la URL (los datos vienen de ficheros del repo, sin sesión ni
        # cookies), así que cumplen el contrato de esta lista.
        re.compile(rf"^/(?:{cc})/(?:prices|precios)$"),
        re.compile(rf"^/(?:{cc})/(?:prices|precios)/[^/]+$"),
        re.compile(rf"^/(?:{cc})/(?:prices|precios)/[^/]+/[^/]+$"),
        # Comparador internacional: portada, capítulos y descarga.
        # Ojo: ``_normalizar`` quita el prefijo /en, así que la comprobación
        # ve «/prices-comparison» y no «/en/prices-comparison».
        re.compile(r"^/(?:precios-comparados|prices-comparison)(?:/[^/]+|\.json)?$"),
        # Coste horario de la mano de obra por mercado y su descarga JSON.
        re.compile(rf"^/(?:{cc})/(?:labour-rates|mano-de-obra)$"),
        re.compile(rf"^/(?:{cc})/(?:prices|precios)\.json$"),
    )


def _normalizar(path: str) -> str:
    """Quita el prefijo de idioma igual que ``IdiomaMiddleware``.

    ``/en-us/guia/x`` -> ``/us/guia/x``; ``/en/guia/x`` -> ``/guia/x``;
    cualquier otra ruta queda intacta.
    """
    m = _RE_PREFIJO_EN.match(path)
    if not m:
        return path
    pais, resto = m.group(1), m.group(2) or ""
    if pais:
        return "/" + pais.lower() + (resto if resto else "/")
    return resto if resto else "/"


def es_ruta_publica_cacheable(path: str) -> bool:
    """True si la ruta, tal cual llega (con su prefijo /en si lo trae),
    pertenece a la superficie pública cuyo contenido depende solo de la URL.
    """
    try:
        p = _normalizar(path or "")
        if p in _RUTAS_FIJAS:
            return True
        return any(patron.match(p) for patron in _patrones())
    except Exception:
        return False


class CachePublicoMiddleware:
    """Sella ``Cache-Control`` compartido en respuestas públicas anónimas.

    Debe quedar POR FUERA de ``IdiomaMiddleware`` para ver la ruta original
    (antes de quitar el prefijo /en) y el ``Set-Cookie`` definitivo de la
    respuesta; por eso se registra tarde en ``app.main``. No toca el cuerpo
    ni ninguna otra cabecera, y ante cualquier anomalía deja pasar la
    respuesta tal cual.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http" or not self._peticion_cacheable(scope):
            await self.app(scope, receive, send)
            return

        async def send_wrap(message):
            if message.get("type") == "http.response.start":
                try:
                    if message.get("status") == 200:
                        headers = list(message.get("headers", []))
                        nombres = {k.lower() for k, _v in headers}
                        if (
                            b"set-cookie" not in nombres
                            and b"cache-control" not in nombres
                        ):
                            headers.append(
                                (
                                    b"cache-control",
                                    CACHE_CONTROL_PUBLICO.encode("latin-1"),
                                )
                            )
                            message = {**message, "headers": headers}
                except Exception:
                    pass  # fail-open: mejor sin sello que con la página rota
            await send(message)

        await self.app(scope, receive, send_wrap)

    @staticmethod
    def _peticion_cacheable(scope) -> bool:
        try:
            if scope.get("method") != "GET":
                return False
            if scope.get("query_string"):
                return False
            if not es_ruta_publica_cacheable(scope.get("path", "") or ""):
                return False
            for k, v in scope.get("headers", []):
                if k.lower() == b"cookie":
                    nombres = {
                        par.split("=", 1)[0].strip()
                        for par in v.decode("latin-1").split(";")
                        if "=" in par
                    }
                    if nombres & _COOKIES_SESION:
                        return False
            return True
        except Exception:
            return False
