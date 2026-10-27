#!/usr/bin/env python3
"""Auditoría SEO HTTP real (con cabeceras) contra un origen desplegado.

La verificación con lectores de contenido no expone código HTTP,
redirecciones ni cabeceras; esta herramienta sí. Solo usa la biblioteca
estándar: corre igual en el portátil del titular que en CI.

Descubre las URLs desde el ``/sitemap_index.xml`` del propio origen (o del
``/sitemap.xml`` si no hay índice) y comprueba en cada una: cadena de
redirecciones, código final, host final (delata el conflicto apex↔www),
``X-Robots-Tag`` y meta robots, canónica autorreferente, hreflang coherente
con el sitemap, un único ``<h1>`` y JSON-LD válido.

Tres controles cubren lo que de verdad deja un sitio con **cero visitas** de
un día para otro y que ninguna lectura de contenido detecta:

* **Sonda Googlebot**: pide la portada y una URL del sitemap con el
  ``User-Agent`` de Googlebot. Un cortafuegos de borde (WAF, protección de
  bots, «Deployment Protection») devuelve 401/403/challenge al rastreador
  mientras el navegador del titular sigue viendo el sitio perfecto. Es la
  causa número uno de una caída a cero inmediata.
* **Cobertura de todos los sitemaps**: el catálogo público de precios vive en
  ``sitemap-precios-{cc}.xml``, fuera de ``sitemap.xml``. Auditar solo el
  principal deja sin revisar justo las ~47 000 URL que se envían nuevas.
* **Tamaño por fichero**: un sitemap de más de 50 000 URL o 50 MB incumple
  el protocolo y Google descarta el fichero entero.

Uso:
  python tools/auditar_seo_produccion.py                       # https://cotizat.online
  python tools/auditar_seo_produccion.py https://www.cotizat.online
  python tools/auditar_seo_produccion.py http://127.0.0.1:8000 --muestra 10
  python tools/auditar_seo_produccion.py --muestra 0           # todas (lento)

Sale con código 1 si alguna comprobación falla. No escribe nada.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

AGENTE = "CotizaT-AuditoriaSEO/1.0 (+tools/auditar_seo_produccion.py)"

#: El mismo ``User-Agent`` que Google declara para su rastreador. Se usa solo
#: para comprobar que el borde no lo bloquea; no se pide nada privado.
AGENTE_GOOGLEBOT = (
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
)

#: Marcas de una página de verificación/cortafuegos. Si aparecen en la
#: respuesta a Googlebot, el rastreador no está viendo el sitio.
_MARCAS_BLOQUEO = (
    "vercel security checkpoint",
    "checking your browser",
    "just a moment",
    "captcha",
    "enable javascript and cookies to continue",
    "attention required",
    "request blocked",
)

#: Límites del protocolo de sitemaps: por encima, Google ignora el fichero.
_MAX_URLS_SITEMAP = 50_000


class _SinRedirigir(urllib.request.HTTPRedirectHandler):
    """Registra la cadena de redirecciones en lugar de seguirla en silencio."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D102
        return None


def pedir(
    url: str, timeout: float, agente: str = AGENTE
) -> tuple[int, dict, str, str, list[tuple[int, str]]]:
    """GET siguiendo redirecciones a mano. Devuelve (código, cabeceras,
    cuerpo, url_final, [(código, Location)…])."""
    opener = urllib.request.build_opener(_SinRedirigir)
    cadena: list[tuple[int, str]] = []
    actual = url
    for _ in range(10):
        req = urllib.request.Request(
            actual, headers={"User-Agent": agente, "Accept-Encoding": "identity"}
        )
        try:
            with opener.open(req, timeout=timeout) as resp:
                cuerpo = resp.read().decode("utf-8", "replace")
                return resp.status, dict(resp.headers), cuerpo, actual, cadena
        except urllib.error.HTTPError as exc:
            destino = exc.headers.get("Location") if exc.headers else None
            if exc.code in (301, 302, 307, 308) and destino:
                destino = urljoin(actual, destino)
                cadena.append((exc.code, destino))
                actual = destino
                continue
            cuerpo = exc.read().decode("utf-8", "replace") if exc.fp else ""
            return exc.code, dict(exc.headers or {}), cuerpo, actual, cadena
    raise RuntimeError(f"demasiadas redirecciones en {url}")


class _Cabeza(HTMLParser):
    """Extrae del HTML lo que la auditoría necesita (sin dependencias)."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.canonical: str | None = None
        self.hreflang: dict[str, str] = {}
        self.meta_robots: str | None = None
        self.h1 = 0
        self.ldjson: list[str] = []
        self._en_ld = False

    def handle_starttag(self, tag, attrs):
        datos = {k.lower(): (v or "") for k, v in attrs}
        if tag == "link" and datos.get("rel") == "canonical":
            self.canonical = datos.get("href")
        elif tag == "link" and datos.get("rel") == "alternate" and datos.get("hreflang"):
            self.hreflang[datos["hreflang"]] = datos.get("href", "")
        elif tag == "meta" and datos.get("name", "").lower() == "robots":
            self.meta_robots = datos.get("content", "")
        elif tag == "h1":
            self.h1 += 1
        elif tag == "script" and datos.get("type") == "application/ld+json":
            self._en_ld = True
            self.ldjson.append("")

    def handle_data(self, data):
        if self._en_ld and self.ldjson:
            self.ldjson[-1] += data

    def handle_endtag(self, tag):
        if tag == "script":
            self._en_ld = False


def locs_del_xml(cuerpo: str) -> list[str]:
    """``<loc>`` de un ``<urlset>`` (o los hijos de un ``<sitemapindex>``)."""
    return [loc.strip() for loc in re.findall(r"<loc>(.*?)</loc>", cuerpo, re.S)]


def es_indice(cuerpo: str) -> bool:
    """¿El XML es un ``<sitemapindex>`` en lugar de un ``<urlset>``?"""
    return "<sitemapindex" in cuerpo


def muestrear(urls: list[str], cuantas: int) -> list[str]:
    """Toma ``cuantas`` URLs repartidas por toda la lista.

    Con 47 000 fichas de precios no se pueden pedir todas en cada pasada, y
    quedarse con las primeras N solo revisa una letra del catálogo: el reparto
    salta de forma uniforme para que la muestra caiga en todas las secciones.
    0 o menos significa «todas».
    """
    if cuantas <= 0 or cuantas >= len(urls):
        return list(urls)
    paso = len(urls) / float(cuantas)
    return [urls[int(i * paso)] for i in range(cuantas)]


def problemas_de_robots(cuerpo: str, base: str) -> tuple[list[str], list[str]]:
    """Revisa ``robots.txt``. Devuelve (problemas, sitemaps declarados).

    El origen puede declarar tantos sitemaps como quiera mientras sean suyos:
    el índice más los hijos de precios es la forma prevista, no un error. Lo
    que sí rompe el rastreo es un ``Disallow: /`` para todos, o anunciar
    sitemaps de otro dominio (copia y pega de una plantilla).
    """
    problemas: list[str] = []
    sitemaps = re.findall(r"^Sitemap:\s*(\S+)", cuerpo, re.M | re.I)
    disallow_total = re.search(r"^Disallow:\s*/\s*$", cuerpo, re.M | re.I)
    if disallow_total:
        problemas.append("robots.txt bloquea todo el sitio (Disallow: /)")
    if not sitemaps:
        problemas.append("robots.txt no declara ningún Sitemap")
    propios = [url for url in sitemaps if urlparse(url).netloc == urlparse(base).netloc]
    for url in sitemaps:
        if urlparse(url).netloc != urlparse(base).netloc:
            problemas.append(f"robots.txt anuncia un sitemap de otro origen: {url}")
    # Producción anuncia solo el índice (/sitemap_index.xml), que incluye el
    # principal como primer hijo: cualquiera de las dos URLs satisface la
    # señal de descubrimiento. Exigir la línea /sitemap.xml a secas marcaría
    # como error la forma canónica recomendada por el propio sitio.
    if not any(
        url.rstrip("/").endswith(("/sitemap.xml", "/sitemap_index.xml"))
        for url in propios
    ):
        problemas.append(
            "robots.txt no anuncia /sitemap.xml ni /sitemap_index.xml"
        )
    return problemas, sitemaps


def sitemaps_del_origen(base: str, timeout: float) -> tuple[list[str], list[str]]:
    """Sitemaps a auditar y avisos encontrados al descubrirlos.

    Se prefiere ``/sitemap_index.xml`` porque es el que contiene el principal
    y los de precios; si no existe se cae a ``/sitemap.xml``.
    """
    avisos: list[str] = []
    for ruta in ("/sitemap_index.xml", "/sitemap.xml"):
        codigo, _cab, cuerpo, _final, cadena = pedir(base + ruta, timeout)
        if codigo != 200:
            continue
        if cadena:
            avisos.append(
                f"{ruta} redirige ({cadena[0][0]} -> {cadena[0][1]}); un sitemap "
                "debe servirse en su URL canónica"
            )
        if es_indice(cuerpo):
            hijos = locs_del_xml(cuerpo)
            if hijos:
                return hijos, avisos
            avisos.append(f"{ruta} es un índice sin hijos")
        return [base + ruta], avisos
    raise SystemExit(
        "Ni /sitemap_index.xml ni /sitemap.xml responden 200; no hay auditoría posible."
    )


def urls_del_sitemap(
    base: str, timeout: float
) -> tuple[list[str], dict[str, list[str]], str]:
    codigo, _cab, cuerpo, _final, cadena = pedir(base + "/sitemap.xml", timeout)
    if codigo != 200:
        raise SystemExit(f"El sitemap respondió {codigo}; no hay auditoría posible.")
    if cadena:
        print(f"AVISO: /sitemap.xml redirige ({cadena[0][0]} -> {cadena[0][1]}). "
              "Un sitemap debe servirse en su URL canónica.")
    locs = re.findall(r"<loc>(.*?)</loc>", cuerpo)
    alternates: dict[str, list[str]] = {}
    for bloque in re.findall(r"<url>(.*?)</url>", cuerpo, re.S):
        loc = re.search(r"<loc>(.*?)</loc>", bloque)
        if loc:
            alternates[loc.group(1)] = re.findall(r'href="([^"]+)"', bloque)
    return locs, alternates, cuerpo


def auditar_url(url: str, timeout: float, alternates: dict[str, list[str]]) -> list[str]:
    fallos: list[str] = []
    host_esperado = urlparse(url).hostname
    codigo, cabeceras, cuerpo, final, cadena = pedir(url, timeout)
    if codigo != 200:
        fallos.append(f"HTTP {codigo} (se esperaba 200)")
    if cadena:
        fallos.append(f"redirige: {' -> '.join(f'{c} {d}' for c, d in cadena)}")
    if urlparse(final).hostname != host_esperado:
        fallos.append(f"host final {urlparse(final).hostname} != {host_esperado} de la loc")
    xrobots = (cabeceras.get("X-Robots-Tag") or "").lower()
    if "noindex" in xrobots:
        fallos.append(f"X-Robots-Tag noindex en URL del sitemap: {xrobots}")
    if codigo == 200 and "html" in (cabeceras.get("Content-Type") or ""):
        cabeza = _Cabeza()
        cabeza.feed(cuerpo)
        if cabeza.canonical != url:
            fallos.append(f"canonical {cabeza.canonical!r} != loc")
        if cabeza.meta_robots and "noindex" in cabeza.meta_robots.lower():
            fallos.append(f"meta robots noindex: {cabeza.meta_robots}")
        esperados = set(alternates.get(url) or [])
        if esperados and set(cabeza.hreflang.values()) != esperados:
            fallos.append("hreflang del HTML no coincide con el del sitemap")
        if cabeza.h1 != 1:
            fallos.append(f"{cabeza.h1} elementos <h1> (se espera 1)")
        for bloque in cabeza.ldjson:
            try:
                json.loads(bloque)
            except ValueError:
                fallos.append("JSON-LD no válido")
                break
    return fallos


def sonda_googlebot(base: str, urls: list[str], timeout: float) -> list[str]:
    """Comprueba si el rastreador de Google recibe el sitio o un challenge.

    Se compara con la respuesta que recibe un agente propio: si el agente
    propio ve 200 y Googlebot ve 401/403/429, un cortafuegos de borde está
    bloqueando la indexación aunque el sitio «funcione» en el navegador.
    """
    problemas: list[str] = []
    for url in urls:
        codigo, cabeceras, cuerpo, _final, cadena = pedir(url, timeout, AGENTE_GOOGLEBOT)
        if cadena:
            problemas.append(
                f"Googlebot recibe redirecciones en {url}: "
                f"{' -> '.join(f'{c} {d}' for c, d in cadena)}"
            )
        if codigo != 200:
            problemas.append(f"Googlebot recibe HTTP {codigo} en {url}")
        tipo = (cabeceras.get("Content-Type") or "").lower()
        texto = cuerpo[:4000].lower()
        if "html" in tipo:
            marca = next((m for m in _MARCAS_BLOQUEO if m in texto), "")
            if marca:
                problemas.append(
                    f"Googlebot recibe una página de verificación en {url} "
                    f"(«{marca}»): WAF/protección de bots activa"
                )
        xrobots = (cabeceras.get("X-Robots-Tag") or "").lower()
        if "noindex" in xrobots:
            problemas.append(f"Googlebot recibe X-Robots-Tag noindex en {url}: {xrobots}")
    return problemas


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("base", nargs="?", default="https://cotizat.online",
                        help="origen a auditar (sin barra final)")
    parser.add_argument("--muestra", type=int, default=25,
                        help="URLs a auditar por sitemap (0 = todas; por defecto 25)")
    parser.add_argument("--limite", type=int, default=0,
                        help="tope total de URLs a auditar (0 = sin tope)")
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--sin-googlebot", action="store_true",
                        help="omite la sonda con el User-Agent de Googlebot")
    parser.add_argument("--solo-fallos", action="store_true",
                        help="imprimir únicamente las URLs con problemas")
    args = parser.parse_args()
    base = args.base.rstrip("/")

    print(f"Origen: {base}")
    fallos_totales = 0

    # robots.txt debe anunciar sitemaps de ESTE origen y no bloquear el sitio.
    try:
        codigo, _cab, cuerpo, _final, cadena = pedir(base + "/robots.txt", args.timeout)
    except Exception as exc:  # DNS, TLS, proxy del portátil: no es un fallo SEO
        print(f"No se pudo conectar con {base}: {exc}")
        print("Comprueba la red (o el proxy) antes de interpretar el resultado: "
              "un origen inalcanzable también deja el sitio sin visitas.")
        return 1
    if codigo != 200 or cadena:
        print(f"FALLO robots.txt: HTTP {codigo}, redirecciones={len(cadena)}")
        fallos_totales += 1
    problemas_robots, sitemaps_declarados = problemas_de_robots(cuerpo, base)
    for problema in problemas_robots:
        print(f"FALLO robots.txt: {problema}")
        fallos_totales += 1
    if not problemas_robots:
        print(f"robots.txt: OK ({len(sitemaps_declarados)} sitemaps del mismo origen)")

    # Se auditan todos los sitemaps anunciados por el índice, no solo el
    # principal: el catálogo de precios por país vive en ficheros aparte.
    try:
        sitemaps, avisos = sitemaps_del_origen(base, args.timeout)
    except SystemExit as exc:
        print(f"FALLO {exc}")
        return 1
    except Exception as exc:  # DNS, TLS, proxy del portátil: no es un fallo SEO
        print(f"No se pudo conectar con {base}: {exc}")
        print("Comprueba la red (o el proxy) antes de interpretar el resultado: "
              "un origen inalcanzable también deja el sitio sin visitas.")
        return 1
    for aviso in avisos:
        print(f"AVISO {aviso}")

    por_sitemap: dict[str, list[str]] = {}
    alternates: dict[str, list[str]] = {}
    total_declaradas = 0
    for sitemap in sitemaps:
        codigo, _cab, cuerpo, _final, _cadena = pedir(sitemap, args.timeout)
        if codigo != 200:
            print(f"FALLO sitemap {sitemap}: HTTP {codigo}")
            fallos_totales += 1
            continue
        locs = locs_del_xml(cuerpo)
        total_declaradas += len(locs)
        por_sitemap[sitemap] = locs
        if len(locs) > _MAX_URLS_SITEMAP:
            print(f"FALLO sitemap {sitemap}: {len(locs)} URLs supera el límite "
                  f"de {_MAX_URLS_SITEMAP}; Google descarta el fichero")
            fallos_totales += 1
        if sitemap.rstrip("/").endswith("/sitemap.xml"):
            for bloque in re.findall(r"<url>(.*?)</url>", cuerpo, re.S):
                loc = re.search(r"<loc>(.*?)</loc>", bloque)
                if loc:
                    alternates[loc.group(1)] = re.findall(r'href="([^"]+)"', bloque)

    print(f"Sitemaps: {len(por_sitemap)} con contenido, {total_declaradas} URLs declaradas")
    for sitemap, locs in por_sitemap.items():
        print(f"  {len(locs):>6} URLs  {sitemap}")

    a_auditar: list[str] = []
    for locs in por_sitemap.values():
        a_auditar.extend(muestrear(locs, args.muestra))
    if args.limite:
        a_auditar = a_auditar[: args.limite]
    print(f"Auditando {len(a_auditar)} URLs (muestra de {args.muestra} por sitemap)")

    for url in a_auditar:
        try:
            fallos = auditar_url(url, args.timeout, alternates)
        except Exception as exc:  # red caída en una URL no aborta la auditoría
            fallos = [f"error de red: {exc}"]
        if fallos:
            fallos_totales += len(fallos)
            print(f"FALLO {url}")
            for fallo in fallos:
                print(f"      - {fallo}")
        elif not args.solo_fallos:
            print(f"OK    {url}")

    # Lo que deja el sitio en cero visitas de un día para otro: el rastreador
    # recibe un challenge o un 403 aunque el navegador vea la página perfecta.
    if not args.sin_googlebot:
        objetivos = [base + "/"] + a_auditar[:2]
        problemas_bot = sonda_googlebot(base, objetivos, args.timeout)
        if problemas_bot:
            for problema in problemas_bot:
                print(f"FALLO sonda Googlebot: {problema}")
            fallos_totales += len(problemas_bot)
        else:
            print(f"Sonda Googlebot: OK ({len(objetivos)} URLs vistas como Googlebot)")

    # Controles que no salen del sitemap.
    codigo, cabeceras, cuerpo, _f, _c = pedir(base + "/acceso", args.timeout)
    noindex = "noindex" in (cabeceras.get("X-Robots-Tag") or "").lower() or \
        "noindex" in cuerpo.lower()
    print(f"/acceso: HTTP {codigo}, noindex={'sí' if noindex else 'NO (fallo)'}")
    fallos_totales += 0 if noindex else 1

    codigo, _cab, _cuerpo, _f, _c = pedir(
        base + "/es/guia/mano-obra-construccion-mexico", args.timeout
    )
    print(f"guía de México bajo /es/: HTTP {codigo} (se espera 404)")
    fallos_totales += 0 if codigo == 404 else 1

    print("\nResultado:", "SIN FALLOS" if fallos_totales == 0
          else f"{fallos_totales} fallos")
    return 0 if fallos_totales == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
