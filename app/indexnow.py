"""IndexNow: avisar a Bing (y con él, a Yahoo) sin esperar al rastreo.

IndexNow es el protocolo con el que un sitio avisa de URLs nuevas o
actualizadas; lo escuchan Bing y los buscadores que se alimentan de su
índice (Yahoo entre ellos). Google no participa: su vía sigue siendo el
sitemap enviado en Search Console.

La clave **no es un secreto**: por diseño del protocolo se publica en
``/{clave}.txt`` para demostrar la propiedad del dominio, igual que el
identificador de GA4 vive en ``app/analytics.py``. Por eso es una
constante del repo y no una variable de entorno: tiene que ser la misma
en cada despliegue y la herramienta de envío (``tools/indexnow.py``) la
lee de aquí.
"""

from __future__ import annotations

#: Clave pública IndexNow (hex). Se sirve tal cual en ``RUTA_CLAVE``.
CLAVE = "31f54838b77f4354a78bf26116d1ec4d"

#: Ruta pública donde los buscadores verifican la propiedad del dominio.
RUTA_CLAVE = f"/{CLAVE}.txt"


#: Origen público por defecto (el mismo que usan los sitemaps).
ORIGEN = "https://cotizat.online"


def urls_precios(origen: str = ORIGEN, cc: str | None = None) -> list[str]:
    """URLs del catálogo de precios, mercado por mercado.

    El sitemap editorial (``app.seo.urls_sitemap``) no incluye el catálogo:
    las ~47 000 fichas de precios viven en ``sitemap-precios-{cc}.xml``. Hasta
    ahora la herramienta de IndexNow solo leía el sitemap editorial, así que
    Bing nunca se enteró de que el catálogo existía. Y justo ahora importa más
    que nunca: el catálogo llevaba tiempo sirviendo ``X-Robots-Tag: noindex``
    por cabecera, y acaba de dejar de hacerlo.

    Orden estable y sin duplicados; una URL por partida, apartado y página de
    mano de obra del mercado.
    """
    from .services import precios_publicos as pp

    vistos: dict[str, None] = {}
    mercados = sorted(pp.paises_publicados())
    if cc:
        codigo = str(cc).strip().upper()
        mercados = [c for c in mercados if c == codigo]
    for codigo in mercados:
        for entrada in pp.urls_sitemap(codigo, origen):
            vistos.setdefault(str(entrada["loc"]), None)
    return list(vistos)
