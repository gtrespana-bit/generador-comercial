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
from .services.precios_publicos import paises_publicados as pp_publicados
from .services.precios_publicos import resumen as pp_resumen

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
    """Recorta sin partir palabras y, si puede, cierra en un punto.

    Cortar a mitad de frase deja descripciones del tipo «Descompuesto de
    instalación de barra de apoyo para…», que en el resultado de búsqueda se
    lee como un texto roto. Se prefiere la última frase completa que quepa.
    """
    texto = " ".join(str(texto or "").split())
    if len(texto) <= maximo:
        return texto
    corte = texto[: maximo + 1]
    # Última frase completa dentro del límite (si deja al menos la mitad del
    # espacio aprovechado): el snippet acaba en punto, no en tres puntos.
    frase = max(corte.rfind(". "), corte.rfind(".) "))
    if frase >= maximo * 0.55:
        return corte[: frase + 1]
    return texto[:maximo].rsplit(" ", 1)[0].rstrip(" ,;:") + "…"


# Google corta el título del resultado alrededor de los 60 caracteres y la
# descripción alrededor de 155–160. Pasarse no penaliza, pero todo lo que
# sobra se sustituye por «…» en el snippet: en 47.000 páginas de precios,
# un título de 88 caracteres perdía el precio y el país, que es justo lo
# que hace clic. Estos dos límites y sus variantes evitan eso.
MAX_TITULO = 60
MAX_DESCRIPCION = 155


def _titulo_meta(variantes: list[str], respaldo: str = "", tope: int = 72) -> str:
    """Primer título que cabe en el ancho útil del resultado de Google.

    Las variantes van de la más informativa (nombre + precio + país) a la
    más escueta. Dos pasadas: primero lo que cabe en 60 caracteres; si el
    nombre de la partida es tan largo que nada cabe (ocurre en 1 de cada
    10 fichas), se prefiere una variante natural que Google recortará por
    su cuenta antes que dejarla a medias con unos puntos suspensivos
    nuestros, que no aportan ni ranking ni clic.
    """
    limpias = [" ".join(str(v or "").split()) for v in variantes]
    limpias = [v for v in limpias if v]
    for variante in limpias:
        if len(variante) <= MAX_TITULO:
            return variante
    sin_marca = [v for v in limpias if " | CotizaT" not in v]
    for variante in sin_marca:
        if len(variante) <= tope:
            return variante
    # Respaldo: el nombre de la partida a secas. Mejor un título corto y
    # entero que uno largo cortado a mitad de palabra.
    simple = " ".join(str(respaldo or "").split())
    if simple:
        return simple if len(simple) <= tope else _recortar(simple, tope)
    return _recortar(sin_marca[-1] if sin_marca else limpias[-1], tope)


def _con_marca(variantes: list[str], marca: str = "CotizaT") -> list[str]:
    """Igual que ``variantes`` pero ofreciendo antes la versión con marca.

    La marca va al final y solo si cabe: en un dominio nuevo el espacio del
    título rinde más con la intención («precio unitario en México») que con
    un nombre que aún nadie busca.
    """
    salida: list[str] = []
    for variante in variantes:
        salida.append(f"{variante} | {marca}")
        salida.append(variante)
    return salida


def _miles(valor: int, pais: dict) -> str:
    """Separador de miles del mercado (1.989 en México/España, 1,989 en EE. UU.)."""
    texto = f"{int(valor):,}"
    miles = str(pais.get("separador_miles") or ",")
    return texto if miles == "," else texto.replace(",", miles)


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
    """Selector de país visible: los demás mercados con esta página.

    El nombre va en el idioma de la PÁGINA, no en el del destino: con
    los cinco ingleses coincidían, pero al encender España una página
    en inglés decía «España» y una en español «the United States».
    """
    lang_pagina = str((PAISES.get(cc_actual) or {}).get("idioma") or "es")
    salida = []
    for r in rutas:
        if r["cc"] == cc_actual:
            continue
        pais = PAISES.get(r["cc"]) or {}
        salida.append(
            {
                "cc": r["cc"],
                "bandera": pais.get("bandera") or "",
                "nombre": _nombre_pais(r["cc"], lang_pagina),
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


def _impuesto_texto(pais: dict, lang: str) -> tuple[str, str]:
    """(etiqueta local del impuesto, tipo) tal y como se llama en ese país."""
    etiqueta = (
        pais.get("etiqueta_impuesto_en") if lang == "en" else pais.get("etiqueta_impuesto")
    ) or pais.get("etiqueta_impuesto") or "IVA"
    tipo = pais.get("iva")
    if isinstance(tipo, (int, float)) and float(tipo).is_integer():
        tipo = int(tipo)
    # «I.V.A.» es como se imprime en la factura; en una frase se lee mal y
    # nadie busca con puntos. Para el texto visible se usa «IVA».
    if etiqueta.upper() == etiqueta and "." in etiqueta:
        etiqueta = etiqueta.replace(".", "").strip()
    return etiqueta, str(tipo) if tipo not in (None, "") else ""


def _faq_indice(
    pais: dict,
    lang: str,
    nombre: str,
    moneda: str,
    mes: str,
    total: int,
    total_apartados: int,
    total_capitulos: int,
    etiqueta: str,
    tipo: str,
) -> list[dict]:
    """Preguntas del índice de precios, respondidas con los datos del país.

    No es FAQ de relleno: cada respuesta lleva un dato que cambia de un
    mercado a otro (número de partidas, moneda, nombre y tipo del impuesto
    local, mes de revisión). Es justo lo que se pregunta quien busca
    «precios de construcción en X»: cuántos hay, si llevan impuesto, de
    dónde sale el número y cada cuánto se actualiza.
    """
    total_txt = _miles(total, pais)
    ap_txt = _miles(total_apartados, pais)
    cap_txt = _miles(total_capitulos, pais)
    if lang == "en":
        impuesto = (
            f"The published figures are cost prices and do not include tax. "
            f"When you build an estimate, {etiqueta} ({tipo}%) is calculated "
            f"on top of the taxable base, not inside the unit price."
        )
        if pais.get("codigo") == "US":
            impuesto = (
                "The published figures are cost prices and do not include tax. "
                "Sales tax is set state by state and by county, so CotizaT "
                "applies it on top of the taxable base when you build the estimate."
            )
        return [
            {
                "q": f"How many construction unit prices are published for {nombre}?",
                "a": (
                    f"{total_txt} unit prices, organised into {ap_txt} sections "
                    f"and {cap_txt} chapters, with reference prices in {moneda} "
                    f"reviewed in {mes}."
                ),
            },
            {
                "q": f"Do these {nombre} prices include {etiqueta}?",
                "a": impuesto,
            },
            {
                "q": "What does the cost breakdown of each item show?",
                "a": (
                    "Materials, labour and equipment, each with its yield and its "
                    "unit cost. That is what lets you check where the unit price "
                    "comes from before you put it in a client estimate."
                ),
            },
            {
                "q": "How often are the prices updated?",
                "a": (
                    f"The catalog is revised periodically; the current revision is "
                    f"{mes} and every section shows its own revision date. When the "
                    f"underlying input prices change, the unit price changes with them."
                ),
            },
            {
                "q": "Can I use these prices in my own estimate?",
                "a": (
                    "Yes: they are published as a market reference. Adjust them to "
                    "your area, your crew and your supplier, because a unit price "
                    "in the capital and in a rural area never match."
                ),
            },
        ]
    impuesto = (
        f"Los importes publicados son de coste y no incluyen impuestos. Al "
        f"presupuestar, el {etiqueta} ({tipo} %) se calcula aparte, sobre la base "
        f"imponible, no dentro del precio unitario."
    )
    if pais.get("codigo") == "US":
        impuesto = (
            "Los importes publicados son de coste y no incluyen impuestos. El "
            "impuesto sobre ventas cambia por estado y por condado, así que "
            "CotizaT lo aplica aparte sobre la base imponible al presupuestar."
        )
    return [
        {
            "q": f"¿Cuántos precios unitarios de construcción hay para {nombre}?",
            "a": (
                f"{total_txt} precios unitarios organizados en {ap_txt} apartados "
                f"y {cap_txt} capítulos, con precios de referencia en {moneda} "
                f"revisados en {mes}."
            ),
        },
        {
            "q": f"¿Los precios de {nombre} incluyen {etiqueta}?",
            "a": impuesto,
        },
        {
            "q": "¿Qué muestra el descompuesto de cada partida?",
            "a": (
                "Materiales, mano de obra y maquinaria, cada recurso con su "
                "rendimiento y su coste unitario. Es lo que permite comprobar de "
                "dónde sale el precio antes de meterlo en un presupuesto."
            ),
        },
        {
            "q": "¿Cada cuánto se actualizan los precios?",
            "a": (
                f"El catálogo se revisa de forma periódica; la revisión actual es "
                f"de {mes} y cada apartado muestra su propia fecha. Cuando cambia "
                f"el precio de un insumo, cambia el precio unitario con él."
            ),
        },
        {
            "q": "¿Puedo usar estos precios en mi propio presupuesto?",
            "a": (
                "Sí: se publican como referencia de mercado. Ajústalos a tu zona, "
                "tu cuadrilla y tu proveedor, porque el mismo precio unitario en la "
                "capital y en una zona rural nunca coincide."
            ),
        },
    ]


def jsonld_dataset(
    request: Request,
    *,
    cc: str,
    ruta: str,
    nombre: str,
    lang: str,
    total: int,
    moneda: str,
    mes: str,
) -> dict:
    """El catálogo del país como ``Dataset``.

    Google Dataset Search es un canal gratuito que casi nadie del sector de
    la construcción usa, y esta página cumple los requisitos de verdad: es
    un conjunto de datos publicados, con cobertura geográfica declarada,
    fecha de revisión, autor identificable y acceso libre sin registro. No
    se inventa una descarga que no existe: no se declara ``distribution``.
    """
    origen = origen_canonico(request)
    en = lang == "en"
    if en:
        nombre_ds = f"Construction unit price database for {nombre} ({moneda})"
        descripcion = (
            f"{total} construction unit prices for {nombre}, with the cost "
            f"breakdown of each item (materials, labour and "
            f"equipment). Reference prices in {moneda}, revised {mes}."
        )
        variables = [
            ("Unit price", moneda),
            ("Materials cost", moneda),
            ("Labour cost", moneda),
            ("Equipment cost", moneda),
            ("Yield per crew day", "unit/day"),
        ]
        palabras = ["construction", "unit prices", "cost database", nombre]
    else:
        nombre_ds = f"Base de precios unitarios de construcción de {nombre} ({moneda})"
        descripcion = (
            f"{total} precios unitarios de construcción para {nombre}, con el "
            f"descompuesto de cada partida (materiales, mano de obra y "
            f"maquinaria). Precios de referencia en {moneda}, revisados en {mes}."
        )
        variables = [
            ("Precio unitario", moneda),
            ("Coste de materiales", moneda),
            ("Coste de mano de obra", moneda),
            ("Coste de maquinaria", moneda),
            ("Rendimiento por día de cuadrilla", "ud/día"),
        ]
        palabras = ["construcción", "precios unitarios", "base de precios", nombre]
    return {
        "@context": "https://schema.org",
        "@id": origen + ruta + "#dataset",
        "@type": "Dataset",
        "name": nombre_ds,
        "description": descripcion,
        "url": origen + ruta,
        "creator": {"@id": origen + "/#organization"},
        "publisher": {"@id": origen + "/#organization"},
        "isAccessibleForFree": True,
        "license": origen + ("/en/legal/terminos" if en else "/legal/terminos"),
        "inLanguage": hreflang_pais(cc),
        "spatialCoverage": {"@type": "Country", "name": nombre},
        "temporalCoverage": (mes.split()[-1] if mes else ""),
        "keywords": palabras,
        "variableMeasured": [
            {"@type": "PropertyValue", "name": variable, "unitText": unidad}
            for variable, unidad in variables
        ],
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
        title = _titulo_meta(
            _con_marca(
                [
                    f"Construction unit prices in {nombre} ({_miles(total, pais)} items, {moneda})",
                    f"Construction unit prices in {nombre} ({moneda})",
                    f"Unit prices in {nombre} — {moneda}",
                ]
            ),
            respaldo=f"Unit prices in {nombre}",
        )
        description = (
            f"{_miles(total, pais)} construction unit prices in {nombre} ({moneda}), "
            f"each with its full cost breakdown: materials, labor and equipment. "
            f"Input prices checked {mes}."
        )
        h1 = f"Construction unit prices in {nombre}"
    else:
        title = _titulo_meta(
            _con_marca(
                [
                    f"Precios unitarios en {nombre} ({_miles(total, pais)} partidas)",
                    f"Precios unitarios de construcción en {nombre}",
                    f"Precios de construcción en {nombre}",
                ]
            ),
            respaldo=f"Precios unitarios en {nombre}",
        )
        description = (
            f"{_miles(total, pais)} precios unitarios de construcción en {nombre} "
            f"({moneda}), cada uno con su descompuesto completo de materiales, mano "
            f"de obra y maquinaria. Precios revisados en {mes}."
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
    etiqueta_impuesto, tipo_impuesto = _impuesto_texto(pais, lang)
    faq = _faq_indice(
        pais,
        lang,
        nombre,
        moneda,
        mes,
        total,
        resumen["total_apartados"],
        len(resumen["capitulos"]),
        etiqueta_impuesto,
        tipo_impuesto,
    )
    bloques = [
        jsonld_organizacion(request, lang=lang),
        jsonld_website(request, lang=lang),
        jsonld_breadcrumb(request, crumbs),
        jsonld_dataset(
            request,
            cc=cc,
            ruta=pp.ruta_indice(cc),
            nombre=nombre,
            lang=lang,
            total=total,
            moneda=moneda,
            mes=mes,
        ),
        jsonld_faq(faq),
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
        {"title": title, "description": _recortar(description, MAX_DESCRIPCION),
         "lang": hreflang_pais(cc), "h1": h1},
        bloques, _hreflang(origen_canonico(request), rutas_alternas), crumbs,
    )
    ctx.update(
        {
            "resumen": {**resumen, "capitulos": capitulos},
            "mes_revision": mes,
            "alternates": _alternates_visibles(rutas_alternas, cc),
            "faq": faq,
            "etiqueta_impuesto": etiqueta_impuesto,
            "tipo_impuesto": tipo_impuesto,
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
    # Rango real del apartado en el país: da a la página un dato que no
    # tiene ninguna otra (ni la de otro mercado, ni el hub del capítulo) y
    # que es exactamente lo que busca quien teclea «cuánto cuesta …».
    precios = [
        float(p.get("pu") or 0) for p in ficha["partidas"] if float(p.get("pu") or 0) > 0
    ]
    rango = {}
    if precios:
        rango = {
            "minimo": _dinero(min(precios), pais),
            "maximo": _dinero(max(precios), pais),
            "medio": _dinero(sum(precios) / len(precios), pais),
        }
    if en:
        title = _titulo_meta(
            _con_marca(
                [
                    f"{apartado}: unit prices in {nombre} ({moneda})",
                    f"{apartado} prices in {nombre}",
                    f"{apartado} — {nombre}",
                ]
            ),
            respaldo=apartado,
        )
        if rango:
            description = (
                f"{n} unit prices for {_minuscula_inicial(apartado)} in {nombre}: "
                f"from {rango['minimo']} to {rango['maximo']}, average "
                f"{rango['medio']}. Cost breakdown of every item."
            )
        else:
            description = (
                f"{n} {_minuscula_inicial(apartado)} unit prices for {nombre} in "
                f"{moneda}, each with a full cost breakdown from the CotizaT "
                f"construction catalog."
            )
        h1 = f"{apartado} — unit prices in {nombre}"
    else:
        title = _titulo_meta(
            _con_marca(
                [
                    f"{apartado}: precios unitarios en {nombre}",
                    f"{apartado}: precios en {nombre} ({moneda})",
                    f"{apartado} — precios en {nombre}",
                ]
            ),
            respaldo=apartado,
        )
        if rango:
            description = (
                f"{n} precios unitarios de {_minuscula_inicial(apartado)} en "
                f"{nombre}: de {rango['minimo']} a {rango['maximo']} "
                f"({rango['medio']} de media). Descompuesto de cada partida."
            )
        else:
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
        {"title": title, "description": _recortar(description, MAX_DESCRIPCION),
         "lang": hreflang_pais(cc), "h1": h1},
        bloques, _hreflang(origen, rutas_alternas), crumbs,
    )
    # Herramientas de navegación de la página: sin ellas el apartado era una
    # tabla con un párrafo y dos enlaces, la página más fina del sitio
    # (255–350 palabras) y justo la que compite por «precios de X en Y».
    hermanos: list[dict] = []
    capitulo_nombre = str(ficha.get("capitulo") or "")
    for capitulo in (pp.resumen(cc) or {}).get("capitulos") or []:
        if capitulo.get("codigo") != ficha.get("capitulo_codigo"):
            continue
        capitulo_nombre = str(capitulo.get("nombre") or capitulo_nombre)
        hermanos = [
            {"nombre": a["nombre"], "ruta": pp.ruta_apartado(cc, a["slug"])}
            for a in capitulo.get("apartados") or []
            if a.get("slug") and a["slug"] != slug
        ][:8]
        break
    guia_apu = "/en/guia/analisis-precios-unitarios" if en else "/guia/analisis-precios-unitarios"
    ctx.update(
        {
            "apartado": {**ficha, "partidas": partidas},
            "rango": rango,
            "mes_revision": _mes((pp.resumen(cc) or {}).get("fecha_revision") or "", lang),
            "nombre_pais": nombre,
            "ruta_indice": pp.ruta_indice(cc),
            "guia_apu": guia_apu,
            "capitulo_nombre": capitulo_nombre,
            "apartados_hermanos": hermanos,
            "alternates": _alternates_visibles(rutas_alternas, cc),
        }
    )
    return ctx


def jsonld_ficha_precio(
    request: Request,
    *,
    cc: str,
    ruta: str,
    titulo: str,
    descripcion: str,
    apartado: str,
    fecha_iso: str,
    precio: str,
    unidad: str,
) -> dict:
    """Nodo de la partida como ficha técnica de precio.

    Se usa ``TechArticle`` y no ``Product``/``Offer`` a propósito: el precio
    publicado es una referencia de catálogo, no una oferta comprable, y
    Google exige ofertas reales para los resultados enriquecidos de producto.
    Un ``Offer`` sin compra posible es markup engañoso y arriesga acción
    manual. La ficha técnica, en cambio, describe exactamente lo que es:
    documentación con fecha de revisión, autor e idioma.
    """
    origen = origen_canonico(request)
    lang = hreflang_pais(cc)
    fecha = str(fecha_iso or "")[:10]
    return {
        "@context": "https://schema.org",
        "@type": "TechArticle",
        "@id": origen + ruta + "#article",
        "headline": _recortar(titulo, 110),
        "name": titulo,
        "description": " ".join(str(descripcion or "").split()),
        "url": origen + ruta,
        "mainEntityOfPage": {"@id": origen + ruta},
        "inLanguage": lang,
        "datePublished": fecha,
        "dateModified": fecha,
        "author": {"@id": origen + "/#organization"},
        "publisher": {"@id": origen + "/#organization"},
        "isPartOf": {"@id": origen + "/#website"},
        "about": {"@type": "Thing", "name": apartado},
        "keywords": f"{apartado}, {precio}/{unidad}, {lang}",
    }


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
        title = _titulo_meta(
            _con_marca(
                [
                    f"{titulo} — {pu_txt}/{unidad} in {nombre}",
                    f"{titulo} in {nombre}",
                    f"{titulo} — price in {nombre}",
                ]
            ),
            respaldo=titulo,
        )
        # El precio y los porcentajes van delante: son lo que se compara en
        # el resultado de búsqueda. El nombre cierra la frase, porque ya está
        # en el título y en el H1 y es la parte que puede recortarse.
        description = (
            f"{pu_txt}/{unidad} in {nombre} ({mes}). Materials "
            f"{pct['materiales']}%, labor {pct['mano_obra']}%, equipment "
            f"{pct['maquinaria']}%. Line-by-line cost breakdown from the "
            f"CotizaT catalog."
        )
        h1 = f"{titulo} — price in {nombre}"
    else:
        title = _titulo_meta(
            _con_marca(
                [
                    f"{titulo} — {pu_txt}/{unidad} en {nombre}",
                    f"{titulo} en {nombre}",
                    f"{titulo} — precio unitario en {nombre}",
                    f"{titulo} — precio en {nombre}",
                ]
            ),
            respaldo=titulo,
        )
        description = (
            f"{pu_txt}/{unidad} en {nombre} ({mes}). Materiales "
            f"{pct['materiales']}%, mano de obra {pct['mano_obra']}%, maquinaria "
            f"{pct['maquinaria']}%. Descompuesto línea a línea del catálogo CotizaT."
        )
        h1 = f"{titulo} — precio en {nombre}"

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
        jsonld_ficha_precio(
            request,
            cc=cc,
            ruta=pp.ruta_partida(cc, slug_apartado, slug),
            titulo=titulo,
            descripcion=description,
            apartado=nombre_apartado,
            fecha_iso=ficha.get("fecha_revision") or "",
            precio=pu_txt,
            unidad=unidad,
        ),
        jsonld_faq(faq),
    ]
    ctx = _base(
        request, cc, pp.ruta_partida(cc, slug_apartado, slug),
        {"title": title, "description": _recortar(description, MAX_DESCRIPCION),
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


def _indice_apartados(cc: str) -> dict | None:
    """{slug: nombre} de los apartados publicados del país, en orden."""
    from .services.precios_publicos import apartado as _apartado

    resumen = pp_resumen(cc)
    if not resumen:
        return None
    apartados: dict[str, dict] = {}
    for capitulo in resumen.get("capitulos") or []:
        for ap in capitulo.get("apartados") or []:
            if ap.get("slug"):
                apartados[ap["slug"]] = ap
    return {"apartados": apartados} if apartados else None


def enlaces_catalogo(codigo_pais: str, semilla: str = "", limite: int = 5) -> dict | None:
    """Enlaces contextuales de una guía o hub al catálogo de precios de su país.

    Los 47.000 precios programáticos solo se descubren por el índice del país
    y por los enlaces entre apartados. Las guías —las páginas que primero
    rankean— no enlazaban a ninguna, así que toda su autoridad se quedaba en
    el silo editorial. Aquí se eligen ``limite`` apartados deterministas a
    partir de una semilla (el slug de la guía): cada guía reparte su enlace a
    un tramo distinto del catálogo, en vez de a los mismos cinco de siempre,
    y el resultado es estable entre peticiones y despliegues.

    Devuelve ``None`` si el país no tiene catálogo público.
    """
    cc = str(codigo_pais or "").strip().upper()
    if not cc or cc not in pp_publicados():
        return None
    indice = _indice_apartados(cc)
    if not indice:
        return None
    slugs = sorted(indice["apartados"])
    if not slugs:
        return None
    texto = str(semilla or cc)
    arranque = sum(ord(c) * (i + 1) for i, c in enumerate(texto)) % len(slugs)
    # Salto amplio (no consecutivos): así los enlaces caen en capítulos
    # distintos del catálogo y no todos en la misma letra del alfabeto.
    salto = max(1, len(slugs) // max(1, limite))
    elegidos = [
        slugs[(arranque + i * salto) % len(slugs)] for i in range(min(limite, len(slugs)))
    ]
    vistos: list[str] = []
    for slug in elegidos:
        if slug not in vistos:
            vistos.append(slug)
    pais = PAISES.get(cc) or {}
    return {
        "codigo": cc,
        "nombre": _nombre_pais(cc, "en" if pais.get("idioma") == "en" else "es"),
        "indice": pp.ruta_indice(cc),
        "moneda": pais.get("moneda") or "",
        "apartados": [
            {
                "nombre": (indice["apartados"].get(slug) or {}).get("nombre") or slug,
                "ruta": pp.ruta_apartado(cc, slug),
            }
            for slug in vistos
        ],
    }


def indices_catalogo(lang: str = "es") -> list[dict]:
    """Índices de todos los catálogos públicos, para la landing genérica.

    La home sin país es la página con más autoridad del sitio y no enlazaba
    a ningún catálogo: los 47.000 precios colgaban del índice de cada país y
    del mapa del sitio. Aquí se enumeran los índices para que la home
    reparta autoridad a todos los silos a la vez.
    """
    salida = []
    for cc in sorted(pp_publicados()):
        try:
            ruta = pp.ruta_indice(cc)
        except Exception:
            continue
        salida.append(
            {
                "codigo": cc,
                "nombre": _nombre_pais(cc, lang),
                "moneda": (PAISES.get(cc) or {}).get("moneda") or "",
                "indice": ruta,
            }
        )
    return salida
