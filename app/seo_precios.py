"""Contextos SEO de las páginas públicas de precios (Fase 5).

Construye el contexto Jinja de las tres páginas (índice del país,
apartado, partida) con el mismo contrato que ``seo.contexto_guia``:
``seo`` (title/description/lang), ``canonical_url``, ``hreflang_links``,
``og_image``, ``jsonld_bloques`` y ``crumbs``. Los datos (precios,
descompuesto, guardia de publicación) vienen de
``services.precios_publicos``; aquí solo hay redacción SEO generada
desde esos datos (títulos, descripciones, FAQ) y modelos de vista con
las rutas ya resueltas.

El hreflang enlaza solo variantes regionales reales de la misma
página: la misma partida/apartado en los países donde está publicada
(precios y moneda distintos = el caso de libro de hreflang), con
``x-default`` a la versión de Estados Unidos si existe.
"""

from __future__ import annotations

from starlette.requests import Request

from .paises import PAISES
from .seo import (
    OG_IMAGE,
    hreflang_pais,
    jsonld_breadcrumb,
    jsonld_faq,
    jsonld_organizacion,
    jsonld_website,
    origen_canonico,
    ruta_mercado,
)
from .services import precios_publicos as pp

_MESES_EN = (
    "January", "February", "March", "April", "May", "June", "July",
    "August", "September", "October", "November", "December",
)
_MESES_ES = (
    "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
    "agosto", "septiembre", "octubre", "noviembre", "diciembre",
)


def _mes(fecha_iso: str, lang: str) -> str:
    try:
        anio, mes, _ = str(fecha_iso or "").split("-")
        nombre = (_MESES_EN if lang == "en" else _MESES_ES)[int(mes) - 1]
    except (ValueError, IndexError):
        return ""
    return f"{nombre} {anio}" if lang == "en" else f"{nombre} de {anio}"


def _dinero(valor, pais: dict) -> str:
    """Importe para titulares/FAQ: número con los separadores del país."""
    miles = str(pais.get("separador_miles") or ",")
    decimal = str(pais.get("separador_decimal") or ".")
    texto = f"{float(valor or 0):,.2f}".replace(",", "\0").replace(".", decimal)
    return texto.replace("\0", miles) + f" {pais.get('moneda') or ''}".rstrip()


def _cantidad(valor, decimales: int = 4) -> str:
    texto = f"{float(valor or 0):,.{decimales}f}"
    return texto.rstrip("0").rstrip(".") if "." in texto else texto


def _minuscula_inicial(texto: str) -> str:
    texto = str(texto or "")
    return texto[:1].lower() + texto[1:] if texto else texto


def _recortar(texto: str, maximo: int) -> str:
    texto = " ".join(str(texto or "").split())
    if len(texto) <= maximo:
        return texto
    return texto[:maximo].rsplit(" ", 1)[0].rstrip(" ,;:") + "…"


def _frases(texto: str, maximo: int = 320) -> str:
    salida = ""
    for frase in str(texto or "").split(". "):
        frase = frase.strip()
        if not frase:
            continue
        candidata = f"{salida}. {frase}" if salida else frase
        if salida and len(candidata) > maximo:
            break
        salida = candidata
    return salida if salida.endswith(".") else salida + "."


def _etiqueta_precios(lang: str) -> str:
    return "Unit prices" if lang == "en" else "Precios unitarios"


def _nombre_pais(cc: str, lang: str) -> str:
    pais = PAISES.get(cc) or {}
    if lang == "en":
        return str(pais.get("nombre_en") or pais.get("nombre") or cc)
    return str(pais.get("nombre") or cc)


def _hreflang(origen: str, rutas: list[dict]) -> list[dict]:
    enlaces = [
        {"hreflang": r["hreflang"], "href": origen + r["path"]} for r in rutas
    ]
    por_defecto = next((r for r in rutas if r["cc"] == "US"), rutas[0] if rutas else None)
    if por_defecto is not None:
        enlaces.append(
            {"hreflang": "x-default", "href": origen + por_defecto["path"]}
        )
    return enlaces


def _alternates_visibles(rutas: list[dict], cc_actual: str) -> list[dict]:
    """Selector de país visible: los demás mercados con esta página."""
    salida = []
    for r in rutas:
        if r["cc"] == cc_actual:
            continue
        pais = PAISES.get(r["cc"]) or {}
        salida.append(
            {
                "cc": r["cc"],
                "bandera": pais.get("bandera") or "",
                "nombre": _nombre_pais(r["cc"], str(pais.get("idioma") or "es")),
                "href": r["path"],
            }
        )
    return salida


def _base(request: Request, cc: str, ruta: str, seo: dict, bloques: list,
          hreflang_links: list, crumbs: list) -> dict:
    origen = origen_canonico(request)
    return {
        "seo": seo,
        "canonical_url": origen + ruta,
        "hreflang_links": hreflang_links,
        "og_image": origen + OG_IMAGE,
        "jsonld_bloques": bloques,
        "crumbs": crumbs,
        "pais": PAISES[cc],
        "ruta_pais": ruta_mercado(cc),
    }


def contexto_indice(request: Request, cc: str) -> dict | None:
    resumen = pp.resumen(cc)
    if resumen is None:
        return None
    pais = PAISES[cc]
    lang = str(pais.get("idioma") or "es")
    en = lang == "en"
    nombre = _nombre_pais(cc, lang)
    moneda = str(pais.get("moneda") or "")
    mes = _mes(resumen["fecha_revision"], lang)
    total = resumen["total_partidas"]

    if en:
        title = f"Construction unit prices in {nombre} ({total:,} items, {moneda}) | CotizaT"
        description = (
            f"Unit prices for {nombre}: {total:,} construction catalog items "
            f"in {moneda}, each with a full cost breakdown (materials, labor, "
            f"equipment). Input prices checked {mes}."
        )
        h1 = f"Construction unit prices in {nombre}"
    else:
        title = f"Precios unitarios de construcción en {nombre} ({total:,} partidas, {moneda}) | CotizaT"
        description = (
            f"Precios unitarios para {nombre}: {total:,} partidas del catálogo "
            f"en {moneda}, cada una con su descompuesto completo (materiales, "
            f"mano de obra, maquinaria). Precios revisados en {mes}."
        )
        h1 = f"Precios unitarios de construcción en {nombre}"

    capitulos = []
    items = []
    for capitulo in resumen["capitulos"]:
        apartados = []
        for ap in capitulo["apartados"]:
            ruta = pp.ruta_apartado(cc, ap["slug"])
            apartados.append({**ap, "ruta": ruta})
            items.append({"name": ap["nombre"], "url": origen_canonico(request) + ruta})
        capitulos.append({**capitulo, "apartados": apartados})

    rutas_alternas = [
        {"hreflang": hreflang_pais(otro), "cc": otro, "path": pp.ruta_indice(otro)}
        for otro in pp.paises_publicados()
    ]
    crumbs = [
        ("Home" if en else "Inicio", ruta_mercado(cc)),
        (_etiqueta_precios(lang), pp.ruta_indice(cc)),
    ]
    bloques = [
        jsonld_organizacion(request, lang=lang),
        jsonld_website(request, lang=lang),
        jsonld_breadcrumb(request, crumbs),
        {
            "@context": "https://schema.org",
            "@type": "ItemList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": i,
                    "name": item["name"],
                    "url": item["url"],
                }
                for i, item in enumerate(items[:100], start=1)
            ],
        },
    ]
    ctx = _base(
        request, cc, pp.ruta_indice(cc),
        {"title": title, "description": _recortar(description, 300),
         "lang": hreflang_pais(cc), "h1": h1},
        bloques, _hreflang(origen_canonico(request), rutas_alternas), crumbs,
    )
    ctx.update(
        {
            "resumen": {**resumen, "capitulos": capitulos},
            "mes_revision": mes,
            "alternates": _alternates_visibles(rutas_alternas, cc),
        }
    )
    return ctx


def contexto_apartado(request: Request, cc: str, slug: str) -> dict | None:
    ficha = pp.apartado(cc, slug)
    if ficha is None:
        return None
    pais = PAISES[cc]
    lang = str(pais.get("idioma") or "es")
    en = lang == "en"
    nombre = _nombre_pais(cc, lang)
    moneda = str(pais.get("moneda") or "")
    apartado = ficha["nombre"]
    n = len(ficha["partidas"])

    if en:
        title = f"{apartado} — unit prices in {nombre} ({moneda}) | CotizaT"
        description = (
            f"{n} {_minuscula_inicial(apartado)} unit prices for {nombre} in "
            f"{moneda}, each with a full cost breakdown from the CotizaT "
            f"construction catalog."
        )
        h1 = f"{apartado} — unit prices in {nombre}"
    else:
        title = f"{apartado} — precios unitarios en {nombre} ({moneda}) | CotizaT"
        description = (
            f"{n} precios unitarios de {_minuscula_inicial(apartado)} para "
            f"{nombre} en {moneda}, cada uno con su descompuesto completo "
            f"del catálogo CotizaT."
        )
        h1 = f"{apartado} — precios unitarios en {nombre}"

    origen = origen_canonico(request)
    partidas = [
        {**p, "ruta": pp.ruta_partida(cc, slug, p["slug"])}
        for p in ficha["partidas"]
    ]
    rutas_alternas = pp.alternates_apartado(ficha.get("clave") or "")
    crumbs = [
        ("Home" if en else "Inicio", ruta_mercado(cc)),
        (_etiqueta_precios(lang), pp.ruta_indice(cc)),
        (apartado, pp.ruta_apartado(cc, slug)),
    ]
    bloques = [
        jsonld_organizacion(request, lang=lang),
        jsonld_website(request, lang=lang),
        jsonld_breadcrumb(request, crumbs),
        {
            "@context": "https://schema.org",
            "@type": "ItemList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": i,
                    "name": p["titulo"],
                    "url": origen + p["ruta"],
                }
                for i, p in enumerate(partidas[:50], start=1)
            ],
        },
    ]
    ctx = _base(
        request, cc, pp.ruta_apartado(cc, slug),
        {"title": title, "description": _recortar(description, 300),
         "lang": hreflang_pais(cc), "h1": h1},
        bloques, _hreflang(origen, rutas_alternas), crumbs,
    )
    ctx.update(
        {
            "apartado": {**ficha, "partidas": partidas},
            "alternates": _alternates_visibles(rutas_alternas, cc),
        }
    )
    return ctx


def contexto_partida(request: Request, cc: str, slug_apartado: str,
                     slug: str) -> dict | None:
    ficha = pp.partida(cc, slug_apartado, slug)
    if ficha is None:
        return None
    pais = PAISES[cc]
    lang = str(pais.get("idioma") or "es")
    en = lang == "en"
    nombre = _nombre_pais(cc, lang)
    titulo = ficha["titulo"]
    unidad = ficha["unidad"]
    pu_txt = _dinero(ficha["pu"], pais)
    mes = _mes(ficha["fecha_revision"], lang)
    directo = float(ficha["directo"] or 0) or 1.0
    pct = {
        g: round(100 * float(ficha["grupos"].get(g) or 0) / directo)
        for g in ("materiales", "mano_obra", "maquinaria")
    }

    if en:
        title = f"{titulo} — {nombre} unit price {pu_txt}/{unidad} | CotizaT"
        description = (
            f"{titulo}: {pu_txt} per {unidad} in {nombre}. Full unit-price "
            f"breakdown (materials {pct['materiales']}%, labor "
            f"{pct['mano_obra']}%, equipment {pct['maquinaria']}%), inputs "
            f"checked {mes}."
        )
        h1 = f"{titulo} — price in {nombre}"
    else:
        title = f"{titulo} — precio unitario en {nombre} {pu_txt}/{unidad} | CotizaT"
        description = (
            f"{titulo}: {pu_txt} por {unidad} en {nombre}. Descompuesto "
            f"completo (materiales {pct['materiales']}%, mano de obra "
            f"{pct['mano_obra']}%, maquinaria {pct['maquinaria']}%), "
            f"precios revisados en {mes}."
        )
        h1 = f"{titulo} — precio en {nombre}"
    if len(title) > 115:
        title = _recortar(title, 115)

    faq = _faq_partida(ficha, pais, lang, nombre, pu_txt, mes, pct)

    lineas = [
        {
            **linea,
            "rendimiento_txt": _cantidad(linea["rendimiento"], 6),
        }
        for linea in ficha["lineas"]
    ]
    hermanas = [
        {**h, "ruta": pp.ruta_partida(cc, slug_apartado, h["slug"])}
        for h in ficha["hermanas"]
    ]
    origen = origen_canonico(request)
    rutas_alternas = pp.alternates(ficha["codigo"])
    nombre_apartado = (ficha.get("apartado") or {}).get("nombre") or ""
    crumbs = [
        ("Home" if en else "Inicio", ruta_mercado(cc)),
        (_etiqueta_precios(lang), pp.ruta_indice(cc)),
        (nombre_apartado, pp.ruta_apartado(cc, slug_apartado)),
        (titulo, pp.ruta_partida(cc, slug_apartado, slug)),
    ]
    bloques = [
        jsonld_organizacion(request, lang=lang),
        jsonld_website(request, lang=lang),
        jsonld_breadcrumb(request, crumbs),
        jsonld_faq(faq),
    ]
    ctx = _base(
        request, cc, pp.ruta_partida(cc, slug_apartado, slug),
        {"title": title, "description": _recortar(description, 300),
         "lang": hreflang_pais(cc), "h1": h1},
        bloques, _hreflang(origen, rutas_alternas), crumbs,
    )
    ctx.update(
        {
            "partida": {**ficha, "lineas": lineas, "hermanas": hermanas},
            "faq": faq,
            "mes_revision": mes,
            "pct_grupos": pct,
            "horas_txt": _cantidad(ficha["horas_mo"], 4),
            "uds_dia_txt": _cantidad(ficha["uds_dia_cuadrilla"], 1),
            "alternates": _alternates_visibles(rutas_alternas, cc),
            "og_type": "article",
        }
    )
    return ctx


def _faq_partida(ficha: dict, pais: dict, lang: str, nombre_pais: str,
                 pu_txt: str, mes: str, pct: dict) -> list[dict]:
    titulo = ficha["titulo"]
    titulo_min = _minuscula_inicial(titulo)
    unidad = ficha["unidad"]
    faq: list[dict] = []
    if lang == "en":
        faq.append(
            {
                "q": f"How much does {titulo_min} cost in {nombre_pais}?",
                "a": (
                    f"The CotizaT catalog reference price is {pu_txt} per "
                    f"{unidad}, with input prices last checked in {mes}. The "
                    f"direct cost splits into {pct['materiales']}% materials, "
                    f"{pct['mano_obra']}% labor and {pct['maquinaria']}% "
                    f"equipment, before a typical contractor margin. Your "
                    f"final quote will vary with site conditions, quantities "
                    f"and your suppliers' prices."
                ),
            }
        )
        faq.append(
            {
                "q": "What does this unit price include?",
                "a": _frases(ficha["descripcion"]),
            }
        )
        if ficha["horas_mo"] > 0:
            faq.append(
                {
                    "q": f"How long does {titulo_min} take?",
                    "a": (
                        f"About {_cantidad(ficha['horas_mo'], 4)} man-hours "
                        f"per {unidad}. A two-person crew completes roughly "
                        f"{_cantidad(ficha['uds_dia_cuadrilla'], 1)} {unidad} "
                        f"per working day."
                    ),
                }
            )
    else:
        faq.append(
            {
                "q": f"¿Cuánto cuesta {titulo_min} en {nombre_pais}?",
                "a": (
                    f"El precio de referencia del catálogo CotizaT es "
                    f"{pu_txt} por {unidad}, con los precios de los insumos "
                    f"revisados en {mes}. El coste directo se reparte en "
                    f"{pct['materiales']}% materiales, {pct['mano_obra']}% "
                    f"mano de obra y {pct['maquinaria']}% maquinaria, antes "
                    f"de un margen típico de contratista. Tu presupuesto "
                    f"final variará según la obra, las cantidades y tus "
                    f"proveedores."
                ),
            }
        )
        faq.append(
            {
                "q": "¿Qué incluye este precio unitario?",
                "a": _frases(ficha["descripcion"]),
            }
        )
        if ficha["horas_mo"] > 0:
            faq.append(
                {
                    "q": f"¿Cuánto tiempo lleva {titulo_min}?",
                    "a": (
                        f"Unas {_cantidad(ficha['horas_mo'], 4)} horas-hombre "
                        f"por {unidad}. Una cuadrilla de dos personas completa "
                        f"aproximadamente "
                        f"{_cantidad(ficha['uds_dia_cuadrilla'], 1)} {unidad} "
                        f"por jornada."
                    ),
                }
            )
    return faq
