#!/usr/bin/env python3
"""Auditoría SEO HTTP real (con cabeceras) contra un origen desplegado.

La verificación con lectores de contenido no expone código HTTP,
redirecciones ni cabeceras; esta herramienta sí. Solo usa la biblioteca
estándar: corre igual en el portátil del titular que en CI.

Descubre las URLs desde el ``/sitemap.xml`` del propio origen y comprueba
en cada una: cadena de redirecciones, código final, host final (delata el
conflicto apex↔www), ``X-Robots-Tag`` y meta robots, canónica
autorreferente, hreflang coherente con el sitemap, un único ``<h1>`` y
JSON-LD válido. Controles extra: ``robots.txt`` anuncia el sitemap del
mismo origen, ``/acceso`` sale noindex y una guía pedida bajo el silo de
otro país devuelve 404.

Uso:
  python tools/auditar_seo_produccion.py                       # https://cotizat.online
  python tools/auditar_seo_produccion.py https://www.cotizat.online
  python tools/auditar_seo_produccion.py http://127.0.0.1:8000 --limite 30

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


class _SinRedirigir(urllib.request.HTTPRedirectHandler):
    """Registra la cadena de redirecciones en lugar de seguirla en silencio."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D102
        return None


def pedir(url: str, timeout: float) -> tuple[int, dict, str, str, list[tuple[int, str]]]:
    """GET siguiendo redirecciones a mano. Devuelve (código, cabeceras,
    cuerpo, url_final, [(código, Location)…])."""
    opener = urllib.request.build_opener(_SinRedirigir)
    cadena: list[tuple[int, str]] = []
    actual = url
    for _ in range(10):
        req = urllib.request.Request(
            actual, headers={"User-Agent": AGENTE, "Accept-Encoding": "identity"}
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


def urls_del_sitemap(base: str, timeout: float) -> tuple[list[str], dict[str, list[str]], str]:
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("base", nargs="?", default="https://cotizat.online",
                        help="origen a auditar (sin barra final)")
    parser.add_argument("--limite", type=int, default=0,
                        help="auditar solo las N primeras URLs del sitemap (0 = todas)")
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--solo-fallos", action="store_true",
                        help="imprimir únicamente las URLs con problemas")
    args = parser.parse_args()
    base = args.base.rstrip("/")

    print(f"Origen: {base}")
    fallos_totales = 0

    # robots.txt debe anunciar el sitemap de ESTE origen.
    codigo, _cab, cuerpo, final, cadena = pedir(base + "/robots.txt", args.timeout)
    sitemap_declarado = re.findall(r"^Sitemap:\s*(\S+)", cuerpo, re.M)
    if codigo != 200 or cadena:
        print(f"FALLO robots.txt: HTTP {codigo}, redirecciones={len(cadena)}")
        fallos_totales += 1
    if sitemap_declarado != [base + "/sitemap.xml"]:
        print(f"FALLO robots.txt: Sitemap declarado {sitemap_declarado} != {base}/sitemap.xml")
        fallos_totales += 1
    else:
        print("robots.txt: OK (Sitemap del mismo origen)")

    locs, alternates, _xml = urls_del_sitemap(base, args.timeout)
    print(f"Sitemap: {len(locs)} URLs")
    if args.limite:
        locs = locs[: args.limite]
        print(f"(limitado a las primeras {len(locs)})")

    for url in locs:
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
