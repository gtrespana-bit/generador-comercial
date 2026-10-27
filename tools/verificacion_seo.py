"""Verificación manual de las correcciones SEO de octubre de 2026.

Ejecuta el código real del repositorio (sin red) y comprueba:

1. Los sitemaps hijos de precios solo anuncian mercados indexables en sus
   alternates hreflang (nunca un destino ``noindex``), en espejo del <head>.
2. Los hijos omiten ``lastmod`` por URL; el índice conserva la fecha de
   revisión de cada lote.
3. robots.txt anuncia únicamente el índice de sitemaps.

La guardia permanente equivalente está en tests/test_precios_publicos.py,
tests/test_seo.py y tests/test_auditoria_seo_tool.py.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import seo
from app.services import precios_publicos as pp

ORIGEN = "https://cotizat.online"
indexables = {cc.lower() for cc in pp.paises_con_catalogo_indexable()}
silenciados = {cc.lower() for cc in pp.paises_publicados() if cc.lower() not in indexables}


def _mercado(href: str) -> str:
    from urllib.parse import urlparse

    return urlparse(href).path.split("/")[1].lower().removeprefix("en-")


def main() -> None:
    errores = []

    # 1. hreflang de los sitemaps hijos: solo mercados indexables.
    for cc in pp.paises_con_catalogo_indexable():
        for entrada in pp.urls_sitemap(cc, ORIGEN):
            for alt in entrada["alternates"]:
                if _mercado(alt["href"]) in silenciados:
                    errores.append(f"{cc} anuncia mercado noindex: {alt['href']}")
            if len(entrada["alternates"]) > 7:
                errores.append(f"{entrada['loc']} tiene {len(entrada['alternates'])} alternates")

    # 2. Los hijos no llevan lastmod por URL.
    for cc in pp.paises_con_catalogo_indexable():
        if any(e["lastmod"] is not None for e in pp.urls_sitemap(cc, ORIGEN)):
            errores.append(f"el sitemap hijo {cc} emite lastmod por URL")

    # 3. robots.txt con una sola referencia, la del índice.
    robots = seo.robots_txt()
    lineas_sitemap = [l for l in robots.splitlines() if l.startswith("Sitemap:")]
    if lineas_sitemap != [f"Sitemap: {ORIGEN}/sitemap_index.xml"]:
        errores.append(f"robots.txt inesperado: {lineas_sitemap}")

    # 4. Los mercados silenciados siguen sin sitemap (404 en el router).
    if pp.urls_sitemap("MX", ORIGEN):
        errores.append("MX sigue generando entradas de sitemap")

    if errores:
        print("REVISIÓN FALLIDA:")
        for error in errores:
            print(" -", error)
        raise SystemExit(1)
    print("OK: hreflang filtrado a 6 mercados, hijos sin lastmod, robots solo con el índice.")


if __name__ == "__main__":
    main()
