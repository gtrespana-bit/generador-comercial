"""Fase 5: páginas públicas de precios por país (SEO programático).

El contrato que fijan estas pruebas es la guardia anti-contenido-fino:
ninguna URL existe sin precio completo en el país, descripción en el
idioma del mercado de al menos 120 caracteres, descompuesto de 3+
líneas y cero restos de español en mercados ingleses. El precio
publicado es el de la fórmula del catálogo verificada contra la base,
las canónicas y el hreflang solo enlazan variantes que existen, y el
sitemap principal (el enviado a Search Console) no cambia: cada país
cuelga de su sitemap hijo anunciado en robots.txt.

Los países se encienden en ``services.precios_publicos`` y estas
pruebas iteran sobre los publicados: encender uno nuevo no debería
exigir tocar este fichero.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from app.cache_publico import es_ruta_publica_cacheable
from app.paises import PAISES
from app.seo import hreflang_pais, urls_sitemap
from app.services import precios_publicos as pp

RAIZ = Path(__file__).resolve().parents[1]
DATOS = RAIZ / "basedatos_partidas" / "datos"
SALIDA = RAIZ / "basedatos_partidas" / "salida"

PUBLICADOS = pp.paises_publicados()

# Detector independiente (no reusa el del servicio): si ambos fallan a
# la vez, que sea por motivos distintos.
_RE_PALABRA = re.compile(r"[a-záéíóúñü]+")
_ACENTOS = set("áéíóúñ")
_ES = {
    "de", "la", "el", "con", "para", "por", "los", "las", "una", "del",
    "incluye", "medido", "existente", "obra", "unidad", "precio",
    "partida", "superficie", "mortero", "colocacion", "suministro",
}


def _restos_es(texto: str) -> list[str]:
    return [
        p
        for p in _RE_PALABRA.findall((texto or "").lower())
        if p in _ES or any(c in _ACENTOS for c in p)
    ]


def _texto(html: str) -> str:
    sin_scripts = re.sub(r"<script.*?</script>", " ", html, flags=re.S | re.I)
    return re.sub(r"<[^>]+>", " ", sin_scripts)


def _una_partida(cc: str) -> tuple[str, dict]:
    """(ruta, ficha) de una partida publicable del país, determinista."""
    resumen = pp.resumen(cc)
    ap = resumen["capitulos"][0]["apartados"][0]
    ficha_ap = pp.apartado(cc, ap["slug"])
    slug = ficha_ap["partidas"][0]["slug"]
    return pp.ruta_partida(cc, ap["slug"], slug), pp.partida(cc, ap["slug"], slug)


def test_hay_al_menos_un_pais_publicado():
    assert PUBLICADOS, "PAISES_PRECIOS_PUBLICOS vacío: la Fase 5 estaría apagada"


def test_guardia_ninguna_pagina_fina_ni_con_restos():
    for cc in PUBLICADOS:
        resumen = pp.resumen(cc)
        assert resumen["total_partidas"] >= 1000
        for capitulo in resumen["capitulos"]:
            assert not _restos_es(capitulo["nombre"]), capitulo["nombre"]
            for ap_resumen in capitulo["apartados"]:
                assert ap_resumen["n_partidas"] >= 3
                ficha_ap = pp.apartado(cc, ap_resumen["slug"])
                assert not _restos_es(ficha_ap["nombre"]), ficha_ap["nombre"]
                for entrada in ficha_ap["partidas"]:
                    ficha = pp.partida(cc, ap_resumen["slug"], entrada["slug"])
                    assert ficha is not None
                    assert len(ficha["lineas"]) >= 3
                    assert len(ficha["descripcion"]) >= 120
                    assert ficha["pu"] > 0
                    assert ficha["fecha_revision"], "sin fecha de revisión"
                    textos = [ficha["titulo"], ficha["descripcion"]] + [
                        linea["nombre"] for linea in ficha["lineas"]
                    ]
                    restos = [r for t in textos for r in _restos_es(t)]
                    assert not restos, (ficha["codigo"], restos[:5])


def test_formula_del_pu_contra_los_ficheros():
    """Recalcula un P.U. de US desde el CSV y el JSON, sin el servicio."""
    if "US" not in PUBLICADOS:
        return
    precios = {}
    with (SALIDA / "precios_recursos_estados_unidos.csv").open(
        encoding="utf-8-sig", newline=""
    ) as fh:
        for fila in csv.DictReader(fh, delimiter=";"):
            try:
                precios[fila["codigo_recurso"]] = float(
                    str(fila["precio_referencia"]).replace(",", ".")
                )
            except (KeyError, ValueError):
                continue
    comprobadas = 0
    for ruta in sorted((DATOS / "descompuestos").glob("12.01.*.json")):
        d = json.loads(ruta.read_text(encoding="utf-8"))
        directo = 0.0
        for r in d["recursos"]:
            precio = precios.get(r["ref"], 0)
            if precio <= 0:
                directo = 0.0
                break
            directo += precio * float(r["rendimiento"])
        if directo <= 0:
            continue
        destino = pp.alternates(d["codigo"])
        destino_us = next((a for a in destino if a["cc"] == "US"), None)
        if destino_us is None:
            continue
        slug_ap, slug_p = destino_us["path"].rstrip("/").split("/")[-2:]
        ficha = pp.partida("US", slug_ap, slug_p)
        esperado = directo * (1 + float(d["complementarios_pct"]) / 100) * (
            1 + float(d["margen"])
        )
        from app.services.unidades_precio import precio_mostrado

        esperado = precio_mostrado(esperado, d["unidad"], True)
        assert abs(ficha["pu"] - esperado) < 0.01, d["codigo"]
        comprobadas += 1
        if comprobadas >= 25:
            break
    assert comprobadas >= 10


def test_slugs_unicos_por_pais():
    for cc in PUBLICADOS:
        resumen = pp.resumen(cc)
        slugs_ap = [
            ap["slug"]
            for cap in resumen["capitulos"]
            for ap in cap["apartados"]
        ]
        assert len(slugs_ap) == len(set(slugs_ap)), cc
        assert len(slugs_ap) == resumen["total_apartados"]
        total = 0
        for slug_ap in slugs_ap:
            slugs_p = [p["slug"] for p in pp.apartado(cc, slug_ap)["partidas"]]
            assert len(slugs_p) == len(set(slugs_p)), (cc, slug_ap)
            total += len(slugs_p)
        assert total == resumen["total_partidas"]


def test_rutas_y_canonical(cliente_web):
    for cc in PUBLICADOS:
        ruta, ficha = _una_partida(cc)
        resp = cliente_web.get(ruta)
        assert resp.status_code == 200
        assert f'<link rel="canonical" href="https://cotizat.test{ruta}">' in resp.text
        assert f'<html lang="{hreflang_pais(cc)}">' in resp.text
        assert "BreadcrumbList" in resp.text and "FAQPage" in resp.text
        indice = cliente_web.get(pp.ruta_indice(cc))
        assert indice.status_code == 200
        assert not _restos_es(_texto(resp.text)), ruta
        assert not _restos_es(_texto(indice.text)), pp.ruta_indice(cc)
        if PAISES[cc]["idioma"] == "en":
            # Sin prefijo /en-cc/ -> 301 a la canónica.
            sin_prefijo = cliente_web.get(
                f"/{cc.lower()}/prices", follow_redirects=False
            )
            assert sin_prefijo.status_code == 301
            assert sin_prefijo.headers["location"].endswith(pp.ruta_indice(cc))
            # Segmento en español en mercado inglés -> 301 a /prices.
            mal_tema = cliente_web.get(
                f"/en-{cc.lower()}/precios", follow_redirects=False
            )
            assert mal_tema.status_code == 301
            assert mal_tema.headers["location"].endswith("/prices")
        assert cliente_web.get(ruta + "-no-existe").status_code == 404
        assert cliente_web.get(pp.ruta_indice(cc) + "/no-existe").status_code == 404


def test_pais_sin_publicar_devuelve_404(cliente_web):
    apagados = [c for c in ("GB", "CA", "AU", "IE", "MX", "ES") if c not in PUBLICADOS]
    for cc in apagados:
        prefijo = f"/en-{cc.lower()}" if PAISES[cc]["idioma"] == "en" else f"/{cc.lower()}"
        tema = "prices" if PAISES[cc]["idioma"] == "en" else "precios"
        assert cliente_web.get(f"{prefijo}/{tema}").status_code == 404, cc
    assert cliente_web.get("/xx/prices").status_code == 404


def test_hreflang_solo_variantes_existentes(cliente_web):
    ruta, ficha = _una_partida(PUBLICADOS[0])
    resp = cliente_web.get(ruta)
    # Solo <link rel=alternate>: el selector de idioma del nav lleva
    # hreflang en sus anclajes y eso es UX, no señal SEO.
    presentes = set(
        re.findall(r'<link[^>]*hreflang="([a-z-]+)"', resp.text, flags=re.I)
    )
    esperados = {
        hreflang_pais(a["cc"]) for a in pp.alternates(ficha["codigo"])
    } | {"x-default"}
    assert presentes == esperados
    for cc in ("GB", "CA", "AU", "IE"):
        if cc not in PUBLICADOS:
            assert f"/en-{cc.lower()}/prices/" not in resp.text


def test_sitemaps(cliente_web):
    principal = cliente_web.get("/sitemap.xml")
    assert principal.status_code == 200
    assert principal.text.count("<loc>") == len(urls_sitemap())
    robots = cliente_web.get("/robots.txt").text
    for cc in PUBLICADOS:
        assert f"sitemap-precios-{cc.lower()}.xml" in robots
        hijo = cliente_web.get(f"/sitemap-precios-{cc.lower()}.xml")
        assert hijo.status_code == 200
        resumen = pp.resumen(cc)
        esperado = 1 + resumen["total_apartados"] + resumen["total_partidas"]
        assert hijo.text.count("<loc>") == esperado, cc
    for cc in ("GB", "MX"):
        if cc not in PUBLICADOS:
            r = cliente_web.get(f"/sitemap-precios-{cc.lower()}.xml")
            assert r.status_code == 404


def test_todas_las_urls_del_primer_pais_responden(cliente_web):
    cc = PUBLICADOS[0]
    hijo = cliente_web.get(f"/sitemap-precios-{cc.lower()}.xml").text
    locs = re.findall(r"<loc>https://cotizat\.test([^<]+)</loc>", hijo)
    assert len(locs) > 1000
    malas = []
    for ruta in locs:
        if cliente_web.get(ruta, follow_redirects=False).status_code != 200:
            malas.append(ruta)
    assert not malas, malas[:10]


def test_muestra_de_urls_de_los_demas_paises(cliente_web):
    for cc in PUBLICADOS[1:]:
        hijo = cliente_web.get(f"/sitemap-precios-{cc.lower()}.xml").text
        locs = re.findall(r"<loc>https://cotizat\.test([^<]+)</loc>", hijo)
        paso = max(1, len(locs) // 40)
        for ruta in locs[::paso][:40]:
            assert cliente_web.get(ruta, follow_redirects=False).status_code == 200, ruta


def test_mapa_del_sitio_enlaza_los_catalogos(cliente_web):
    mapa = cliente_web.get("/en/mapa-del-sitio")
    assert mapa.status_code == 200
    for cc in PUBLICADOS:
        if PAISES[cc]["idioma"] == "en":
            assert f'href="{pp.ruta_indice(cc)}"' in mapa.text, cc


def test_no_sombrea_rutas_de_la_app(cliente_web):
    # El router de precios va el ÚLTIMO en main a propósito: sus patrones
    # /{cc}/precios/... capturaban /partidas/precios/anomalos (cc =
    # «partidas») y rompían el botón de reparación de precios. Si esta
    # respuesta vuelve a ser el 404 de precios, el orden se ha roto.
    resp = cliente_web.get("/partidas/precios/anomalos", follow_redirects=False)
    assert not (resp.status_code == 404 and resp.text == "Página no encontrada.")


def test_cache_publica_cubre_las_rutas(cliente_web):
    for cc in PUBLICADOS:
        ruta, _ = _una_partida(cc)
        assert es_ruta_publica_cacheable(pp.ruta_indice(cc)), cc
        assert es_ruta_publica_cacheable(ruta), ruta
        assert es_ruta_publica_cacheable(f"/sitemap-precios-{cc.lower()}.xml")
    # Segundo GET anónimo (las cookies de preferencia ya no cambian):
    # la respuesta llega sellada para el CDN.
    cliente_web.get(pp.ruta_indice(PUBLICADOS[0]))
    sellada = cliente_web.get(pp.ruta_indice(PUBLICADOS[0]))
    assert "s-maxage" in sellada.headers.get("cache-control", "")


def test_los_ficheros_del_servicio_viajan_a_vercel():
    """El fallo de la primera salida de la Fase 5 (2026-10-21).

    Los CSV de precios por país estaban en ``.vercelignore`` (Fase 1.3):
    el servicio los lee en caliente, la CI no pudo cazarlo porque clona
    el repo completo, y en producción todas las páginas devolvieron
    404. Esta prueba lee ``.vercelignore`` y exige que nada de lo que
    el servicio (y la traducción que usa) lee en caliente esté fuera
    del despliegue.
    """
    from fnmatch import fnmatch

    patrones = [
        linea.strip()
        for linea in (RAIZ / ".vercelignore").read_text(encoding="utf-8").splitlines()
        if linea.strip() and not linea.strip().startswith("#")
    ]

    def esta_fuera(ruta_relativa: str) -> bool:
        return any(
            fnmatch(ruta_relativa, patron)
            or ruta_relativa.startswith(patron.rstrip("/") + "/")
            for patron in patrones
        )

    necesarios = sorted(
        p.relative_to(RAIZ).as_posix() for p in SALIDA.glob("precios_recursos_*.csv")
    ) + [
        "basedatos_partidas/datos/recursos.json",
        "basedatos_partidas/datos/recursos_en.json",
        "basedatos_partidas/datos/clasificacion.json",
        # Muestra del directorio de descompuestos (3.006 ficheros).
        "basedatos_partidas/datos/descompuestos/01.01.01.010.json",
        "basedatos_partidas/salida/traducciones/EN.json",
    ]
    assert len(necesarios) >= 10  # cordura: el glob encontró los CSV
    fuera = [n for n in necesarios if esta_fuera(n)]
    assert not fuera, (
        f"Ficheros con lector en caliente excluidos de Vercel: {fuera}. "
        "Si el servicio lee un fichero nuevo, sale de .vercelignore a la vez."
    )
