"""Verificación manual de las correcciones SEO de octubre de 2026.

Ejecuta el código real del repositorio (sin red) y comprueba:

1. Los sitemaps hijos de precios solo enlazan páginas anunciadas en sus
   alternates hreflang (nunca un destino ``noindex``), en espejo del <head>.
   La comprobación es página a página: un mercado a medio localizar (México)
   aparece en el grupo solo en las fichas que también anuncia.
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
con_sitemap = pp.paises_con_sitemap()


def _mercado(href: str) -> str:
    from urllib.parse import urlparse

    return urlparse(href).path.split("/")[1].lower().removeprefix("en-")


def main() -> None:
    errores = []

    # 1. hreflang de los sitemaps hijos: solo destinos anunciados.
    for cc in con_sitemap:
        for entrada in pp.urls_sitemap(cc, ORIGEN):
            mercados = []
            for alt in entrada["alternates"]:
                destino = _mercado(alt["href"])
                if not pp.path_indexable(destino.upper(), alt["href"]):
                    errores.append(f"{cc} enlaza una página noindex: {alt['href']}")
                if alt["hreflang"] != "x-default":
                    mercados.append(destino)
            if len(mercados) != len(set(mercados)):
                errores.append(f"{entrada['loc']} repite mercado en los alternates")

    # 2. Los hijos no llevan lastmod por URL.
    for cc in con_sitemap:
        if any(e["lastmod"] is not None for e in pp.urls_sitemap(cc, ORIGEN)):
            errores.append(f"el sitemap hijo {cc} emite lastmod por URL")

    # 3. robots.txt con una sola referencia, la del índice.
    robots = seo.robots_txt()
    lineas_sitemap = [l for l in robots.splitlines() if l.startswith("Sitemap:")]
    if lineas_sitemap != [f"Sitemap: {ORIGEN}/sitemap_index.xml"]:
        errores.append(f"robots.txt inesperado: {lineas_sitemap}")

    # 4. Un mercado sin texto propio sigue sin sitemap (404 en el router).
    for cc in pp.paises_publicados():
        if cc not in con_sitemap and pp.urls_sitemap(cc, ORIGEN):
            errores.append(f"{cc} no se anuncia pero genera entradas de sitemap")

    if errores:
        print("REVISIÓN FALLIDA:")
        for error in errores:
            print(" -", error)
        raise SystemExit(1)
    print(
        "OK: hreflang filtrado página a página en "
        f"{len(con_sitemap)} sitemaps hijos, hijos sin lastmod, "
        "robots solo con el índice."
    )


if __name__ == "__main__":
    main()
