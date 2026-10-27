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


def _texto_sin_toponimos(html: str, cc_pagina: str) -> str:
    """Texto visible sin los nombres propios de los mercados.

    «El Salvador» también es su nombre en inglés (así lo trae el
    registro en ``nombre_en``): sin quitar el topónimo, el detector
    caza su «El» como si fuera prosa sin traducir al aparecer en el
    selector de países de las páginas inglesas.
    """
    texto = _texto(html)
    en = PAISES[cc_pagina]["idioma"] == "en"
    for otro in PUBLICADOS:
        nombre = PAISES[otro].get("nombre_en" if en else "nombre") or ""
        if nombre:
            texto = texto.replace(nombre, " ")
    return texto


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
        es_en = PAISES[cc]["idioma"] == "en"
        resumen = pp.resumen(cc)
        assert resumen["total_partidas"] >= 1000
        for capitulo in resumen["capitulos"]:
            if es_en:
                assert not _restos_es(capitulo["nombre"]), capitulo["nombre"]
            for ap_resumen in capitulo["apartados"]:
                assert ap_resumen["n_partidas"] >= 3
                ficha_ap = pp.apartado(cc, ap_resumen["slug"])
                if es_en:
                    assert not _restos_es(ficha_ap["nombre"]), ficha_ap["nombre"]
                for entrada in ficha_ap["partidas"]:
                    ficha = pp.partida(cc, ap_resumen["slug"], entrada["slug"])
                    assert ficha is not None
                    assert len(ficha["lineas"]) >= 3
                    assert len(ficha["descripcion"]) >= 120
                    assert ficha["pu"] > 0
                    assert ficha["fecha_revision"], "sin fecha de revisión"
                    if es_en:
                        textos = [ficha["titulo"], ficha["descripcion"]] + [
                            linea["nombre"] for linea in ficha["lineas"]
                        ]
                        restos = [r for t in textos for r in _restos_es(t)]
                        assert not restos, (ficha["codigo"], restos[:5])
                    else:
                        # Mercado hispano: la descripción sale del catálogo
                        # nativo + glosario; si algún día saliera en inglés
                        # por un cruce de tablas, esta señal lo caza.
                        assert _restos_es(ficha["descripcion"]), ficha["codigo"]


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


def test_mercados_del_mismo_idioma_no_son_calcos():
    """Dos países del mismo idioma no son el mismo texto con otra bandera.

    La diferenciación regional es la mitad del valor SEO de publicar
    por mercado: glosario propio (interruptor/apagador,
    labor/labour) y precios consultados en cada país. Medido al
    encender la tanda hispana (2026-10-21): ES↔MX difieren en texto
    772 de 1.986 fichas comunes y US↔GB 1.463 de 1.779; el umbral de
    100 deja margen sin convertir el test en decoración.
    """
    por_idioma: dict[str, list[str]] = {}
    for cc in PUBLICADOS:
        por_idioma.setdefault(PAISES[cc]["idioma"], []).append(cc)
    for paises in por_idioma.values():
        if len(paises) < 2:
            continue
        a_cc, b_cc = paises[0], paises[1]
        a = {f["codigo"]: f for f in pp._indice(a_cc)["partidas"].values()}
        b = {f["codigo"]: f for f in pp._indice(b_cc)["partidas"].values()}
        comunes = sorted(set(a) & set(b))
        assert len(comunes) >= 1000, (a_cc, b_cc)
        texto_distinto = sum(
            1
            for c in comunes
            if a[c]["titulo"] != b[c]["titulo"]
            or a[c]["descripcion"] != b[c]["descripcion"]
        )
        assert texto_distinto >= 100, (a_cc, b_cc, texto_distinto)
        precio_distinto = sum(
            1
            for c in comunes
            if a[c]["moneda"] != b[c]["moneda"]
            or abs(a[c]["pu"] - b[c]["pu"]) > 1e-9
        )
        assert precio_distinto >= 0.9 * len(comunes), (a_cc, b_cc)


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
        if PAISES[cc]["idioma"] == "en":
            assert not _restos_es(_texto_sin_toponimos(resp.text, cc)), ruta
            assert not _restos_es(
                _texto_sin_toponimos(indice.text, cc)
            ), pp.ruta_indice(cc)
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
        else:
            # Tema en inglés en mercado hispano -> 301 a /precios.
            mal_tema = cliente_web.get(
                f"/{cc.lower()}/prices", follow_redirects=False
            )
            assert mal_tema.status_code == 301
            assert mal_tema.headers["location"].endswith(pp.ruta_indice(cc))
            # Prefijo /en-cc/ en mercado hispano -> 301 a la canónica.
            con_prefijo = cliente_web.get(
                f"/en-{cc.lower()}/precios", follow_redirects=False
            )
            assert con_prefijo.status_code == 301
            assert con_prefijo.headers["location"].endswith(pp.ruta_indice(cc))
        assert cliente_web.get(ruta + "-no-existe").status_code == 404
        assert cliente_web.get(pp.ruta_indice(cc) + "/no-existe").status_code == 404


def test_pais_sin_publicar_devuelve_404(cliente_web):
    # VE no tiene matriz en el repo: aunque la lista de encendidos
    # crezca, sin matriz no puede existir su catálogo público.
    apagados = [c for c in ("GB", "CA", "AU", "IE", "MX", "ES", "VE") if c not in PUBLICADOS]
    for cc in apagados:
        prefijo = f"/en-{cc.lower()}" if PAISES[cc]["idioma"] == "en" else f"/{cc.lower()}"
        tema = "prices" if PAISES[cc]["idioma"] == "en" else "precios"
        assert cliente_web.get(f"{prefijo}/{tema}").status_code == 404, cc
    assert cliente_web.get("/xx/prices").status_code == 404


def test_hreflang_solo_variantes_existentes(cliente_web):
    """El hreflang solo lista mercados con la página indexable.

    Un hreflang hacia una página ``noindex`` invalida el grupo entero, así que
    los mercados silenciados quedan fuera de los ``<link rel=alternate>``. El
    selector de país visible los sigue mostrando: son cosas distintas.
    """
    ruta, ficha = _una_partida(pp.paises_con_catalogo_indexable()[0])
    resp = cliente_web.get(ruta)
    # Solo <link rel=alternate>: el selector de idioma del nav lleva
    # hreflang en sus anclajes y eso es UX, no señal SEO.
    presentes = set(
        re.findall(r'<link[^>]*hreflang="([a-z-]+)"', resp.text, flags=re.I)
    )
    esperados = {
        hreflang_pais(a["cc"])
        for a in pp.alternates(ficha["codigo"])
        if pp.ficha_indexable(a["cc"])
    } | {"x-default"}
    assert presentes == esperados
    for cc in (a["cc"] for a in pp.alternates(ficha["codigo"])):
        if not pp.ficha_indexable(cc):
            assert hreflang_pais(cc) not in presentes, cc
            # Pero la página hermana sigue existiendo y navegable.
            assert f"{pp.ruta_indice(cc)}/" in resp.text or pp.ruta_indice(cc) in resp.text
    for cc in ("GB", "CA", "AU", "IE"):
        if cc not in PUBLICADOS:
            assert f"/en-{cc.lower()}/prices/" not in resp.text


def test_sitemaps(cliente_web):
    """Solo se anuncian los mercados cuyo catálogo es indexable.

    Desde el 23/10/2026 los mercados hispanos que no son España publican sus
    fichas con ``noindex``: anunciarlas sería contradecirse, y un sitemap que
    anuncia páginas noindex es un error que Search Console reporta por cada
    URL. El índice de sitemaps y ``robots.txt`` se recogen solos de la misma
    política.
    """
    anunciados = pp.paises_con_catalogo_indexable()
    silenciados = [cc for cc in PUBLICADOS if cc not in anunciados]

    principal = cliente_web.get("/sitemap.xml")
    assert principal.status_code == 200
    assert principal.text.count("<loc>") == len(urls_sitemap())

    indice = cliente_web.get("/sitemap_index.xml").text
    robots = cliente_web.get("/robots.txt").text
    for cc in anunciados:
        assert f"sitemap-precios-{cc.lower()}.xml" in indice, cc
        hijo = cliente_web.get(f"/sitemap-precios-{cc.lower()}.xml")
        assert hijo.status_code == 200
        resumen = pp.resumen(cc)
        esperado = 1 + resumen["total_apartados"] + resumen["total_partidas"]
        # +1: la página de coste horario de la mano de obra del mercado.
        if pp.oficios_disponibles(cc):
            esperado += 1
        assert hijo.text.count("<loc>") == esperado, cc
    for cc in silenciados:
        assert f"sitemap-precios-{cc.lower()}.xml" not in indice, cc
        r = cliente_web.get(f"/sitemap-precios-{cc.lower()}.xml")
        assert r.status_code == 404, cc
    # robots.txt anuncia el índice (que contiene los hijos); repetir ahí los
    # 23 hijos era lo que presentaba el catálogo de golpe.
    assert "sitemap_index.xml" in robots
    for cc in PUBLICADOS:
        assert f"sitemap-precios-{cc.lower()}.xml" not in robots, cc


def _mercado_del_href(href: str) -> str:
    """Mercado (cc en minúscula) al que apunta un alternate del sitemap."""
    from urllib.parse import urlparse

    segmento = urlparse(href).path.split("/")[1].lower()
    return segmento.removeprefix("en-")


def test_los_sitemaps_hijos_solo_enlazan_mercados_indexables():
    """El hreflang del sitemap no puede apuntar a una página noindex.

    Es la versión sitemap de ``test_hreflang_solo_variantes_existentes`` (que
    cubre el ``<head>``): un alternate hacia un mercado silenciado invalida el
    clúster hreflang entero, así que los 16 mercados noindex no pueden aparecer
    en ninguno de los seis sitemaps hijos.
    """
    indexables = {cc.lower() for cc in pp.paises_con_catalogo_indexable()}
    assert len(indexables) == 6
    for cc in pp.paises_con_catalogo_indexable():
        entradas = pp.urls_sitemap(cc, "https://cotizat.online")
        assert entradas  # mercado indexable: su sitemap nunca va vacío
        for entrada in entradas:
            mercados = set()
            for alt in entrada["alternates"]:
                if alt["hreflang"] == "x-default":
                    # El destino por defecto también tiene que ser indexable.
                    assert _mercado_del_href(alt["href"]) in indexables, alt
                    continue
                mercado = _mercado_del_href(alt["href"])
                assert mercado in indexables, (cc, entrada["loc"], alt)
                mercados.add(mercado)
            if entrada["alternates"]:
                # 6 mercados indexables + x-default: nunca los 23 de antes.
                assert len(entrada["alternates"]) <= 7, entrada["loc"]
        # La entrada índice del mercado existe en los seis catálogos: su grupo
        # tiene exactamente los seis mercados más x-default.
        entrada_indice = next(
            e for e in entradas if e["loc"].endswith(pp.ruta_indice(cc))
        )
        assert len(entrada_indice["alternates"]) == 7


def test_las_alternates_crudas_siguen_incluyendo_mercados_silenciados():
    """El filtro es del sitemap, no de ``alternates()``.

    El selector de país visible necesita los 22 mercados (es UX, no señal
    SEO): filtrar dentro de ``alternates()`` habría borrado mercados del nav.
    """
    indice_es = pp._indice("ES")
    clave, codigo = None, None
    for (sa, sp), ficha in indice_es["partidas"].items():
        if any(not pp.ficha_indexable(a["cc"]) for a in pp.alternates(ficha["codigo"])):
            clave, codigo = (sa, sp), ficha["codigo"]
            break
    assert codigo is not None
    crudas = pp.alternates(codigo)
    assert any(not pp.ficha_indexable(a["cc"]) for a in crudas)

    # El mismo dato, al pasar por el sitemap, queda filtrado.
    ruta = pp.ruta_partida("ES", clave[0], clave[1])
    entradas = pp.urls_sitemap("ES", "https://cotizat.online")
    entrada = next(e for e in entradas if e["loc"].endswith(ruta))
    assert all(
        pp.ficha_indexable(_mercado_del_href(a["href"]).upper())
        for a in entrada["alternates"]
    )


def test_los_sitemaps_hijos_omiten_lastmod_pero_el_indice_lo_conserva(cliente_web):
    """Sin lastmod veraz por URL, los hijos no lo emiten; el índice sí.

    La fecha de revisión es la del lote completo (idéntica para miles de
    URLs), así que el dato veraz vive una sola vez por hijo en
    ``sitemap_index.xml``. El sitemap principal, con páginas editoriales
    distintas, mantiene su ``lastmod``.
    """
    for cc in pp.paises_con_catalogo_indexable():
        assert all(
            e["lastmod"] is None
            for e in pp.urls_sitemap(cc, "https://cotizat.online")
        )
        hijo = cliente_web.get(f"/sitemap-precios-{cc.lower()}.xml")
        assert hijo.status_code == 200
        assert "<lastmod>" not in hijo.text, cc
    assert "<lastmod>" in cliente_web.get("/sitemap_index.xml").text
    assert "<lastmod>" in cliente_web.get("/sitemap.xml").text


def test_todas_las_urls_del_primer_pais_responden(cliente_web):
    # Se audita un mercado anunciado: los silenciados no tienen sitemap.
    cc = pp.paises_con_catalogo_indexable()[0]
    hijo = cliente_web.get(f"/sitemap-precios-{cc.lower()}.xml").text
    locs = re.findall(r"<loc>https://cotizat\.test([^<]+)</loc>", hijo)
    assert len(locs) > 1000
    malas = []
    for ruta in locs:
        if cliente_web.get(ruta, follow_redirects=False).status_code != 200:
            malas.append(ruta)
    assert not malas, malas[:10]


def test_muestra_de_urls_de_los_demas_paises(cliente_web):
    for cc in pp.paises_con_catalogo_indexable()[1:]:
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
    mapa_es = cliente_web.get("/mapa-del-sitio")
    assert mapa_es.status_code == 200
    for cc in PUBLICADOS:
        if PAISES[cc]["idioma"] != "en":
            assert f'href="{pp.ruta_indice(cc)}"' in mapa_es.text, cc


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
    ] + [
        # Un artefacto por país encendido: la lista se auto-actualiza
        # con el interruptor del servicio.
        f"basedatos_partidas/datos/precios_publicos/{cc}.json"
        for cc in pp.PAISES_PRECIOS_PUBLICOS
    ]
    assert len(necesarios) >= 10  # cordura: el glob encontró los CSV
    fuera = [n for n in necesarios if esta_fuera(n)]
    assert not fuera, (
        f"Ficheros con lector en caliente excluidos de Vercel: {fuera}. "
        "Si el servicio lee un fichero nuevo, sale de .vercelignore a la vez."
    )


def test_el_artefacto_precalculado_coincide_con_el_calculo_en_vivo():
    """Anti-deriva de los JSON precalculados (datos/precios_publicos/).

    Las páginas se sirven desde el artefacto (0,1 s/país) y no desde
    el cálculo en vivo (~21 s los cinco mercados ingleses: en frío,
    Vercel no llegaba a calentar y las páginas salieron con 404 por
    timeout). Si cambian el catálogo, los CSV, las traducciones o los
    países encendidos y nadie regenera
    (``tools/generar_precios_publicos.py``), esta prueba lo caza
    comparando contra el cálculo en vivo.
    """
    for cc in PUBLICADOS:
        artefacto = DATOS / "precios_publicos" / f"{cc}.json"
        assert artefacto.exists(), (
            f"Falta el artefacto de {cc}: "
            "python tools/generar_precios_publicos.py"
        )
        assert pp._indice_desde_artefacto(cc), (
            f"El artefacto de {cc} no carga (JSON dañado o sin partidas)"
        )
        servido = pp._indice(cc)
        vivo = pp._indice_en_vivo(cc)
        assert servido is not None and vivo is not None
        assert servido["total_partidas"] == vivo["total_partidas"], cc
        assert servido["total_apartados"] == vivo["total_apartados"], cc
        assert set(servido["partidas"]) == set(vivo["partidas"]), cc
        assert servido["por_codigo"] == vivo["por_codigo"], cc
        claves = sorted(vivo["partidas"])
        for clave in claves[::97]:  # muestra determinista de todo el país
            a, b = servido["partidas"][clave], vivo["partidas"][clave]
            assert a["titulo"] == b["titulo"], (cc, clave)
            assert a["descripcion"] == b["descripcion"], (cc, clave)
            assert abs(a["pu"] - b["pu"]) < 1e-9, (cc, clave)
            assert len(a["lineas"]) == len(b["lineas"]), (cc, clave)
