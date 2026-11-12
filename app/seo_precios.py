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

import math

from starlette.requests import Request

from . import comparador
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


def _numero_corto(valor, pais: dict) -> str:
    """Solo el número, con los separadores del país y los decimales justos.

    Se redondea **hacia arriba**: en un título «desde 40 MXN» con una partida
    de 39,82 MXN es verdad; «desde 39» sería prometer un precio que no existe.
    Los decimales dependen de la magnitud: redondear a entero un precio de
    0,48 USD por pie cuadrado lo convierte en «1 USD» y parece un error del
    catálogo, así que por debajo de 10 se conservan uno o dos decimales.
    """
    miles = str(pais.get("separador_miles") or ",")
    decimal = str(pais.get("separador_decimal") or ".")
    cantidad = float(valor or 0)
    decimales = 2 if cantidad < 1 else (1 if cantidad < 10 else 0)
    factor = 10 ** decimales
    redondeado = math.ceil(cantidad * factor - 1e-9) / factor
    texto = f"{redondeado:,.{decimales}f}"
    texto = texto.replace(",", "\0").replace(".", decimal).replace("\0", miles)
    if decimales and decimal in texto:
        texto = texto.rstrip("0").rstrip(decimal)
    return texto


def _dinero_corto(valor, pais: dict) -> str:
    """Importe para títulos y descripciones: sin céntimos.

    En un resultado de Google los céntimos gastan caracteres y no aportan
    nada al que busca «cuánto cuesta». La moneda va una sola vez aunque haya
    dos cifras: «40–264 MXN», no «40,00 MXN–264,00 MXN».
    """
    return f"{_numero_corto(valor, pais)} {pais.get('moneda') or ''}".rstrip()


_UNIDADES_TITULO = {
    "m2": "m²", "m²": "m²",
    "m3": "m³", "m³": "m³",
    "ml": "ml", "m": "m",
    "ud": "ud", "ea": "ea",
    "kg": "kg", "l": "l", "h": "h", "t": "t",
}


def _unidad_dominante(partidas: list[dict]) -> tuple[str, float]:
    """Unidad de medida más repetida del apartado y qué proporción representa.

    Un apartado con 26 partidas por m² y 3 por metro lineal todavía se puede
    anunciar por m²; uno con la mitad por m² y la mitad por unidad, no. De ahí
    la proporción: por debajo del 70 % no se escribe ni unidad ni rango doble.
    """
    cuenta: dict[str, int] = {}
    for partida in partidas:
        clave = str(partida.get("unidad") or "").strip().lower()
        # El catálogo escribe «m²» y «m2» para lo mismo: se cuentan juntas o
        # un apartado homogéneo parecería mitad y mitad.
        clave = {"m²": "m2", "m³": "m3"}.get(clave, clave)
        if clave:
            cuenta[clave] = cuenta.get(clave, 0) + 1
    if not cuenta:
        return "", 0.0
    unidad, veces = max(cuenta.items(), key=lambda par: (par[1], par[0]))
    return _UNIDADES_TITULO.get(unidad, unidad), veces / sum(cuenta.values())


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
    """Enlaces hreflang del grupo, solo entre páginas anunciadas.

    Un hreflang que apunta a una página ``noindex`` es un error explícito: el
    grupo entero deja de considerarse fiable. Por eso se filtra con
    ``path_indexable`` —ficha a ficha, no mercado a mercado— en el único punto
    donde nacen estos enlaces; el selector de país visible
    (``_alternates_visibles``) sigue mostrando todos los mercados, que es UX y
    no señal SEO.
    """
    from .services.precios_publicos import path_indexable

    # Destino a destino: desde que un mercado puede estar a medio localizar, la
    # unidad ya no es el mercado sino la ficha. Un hreflang que apunta a una
    # página noindex invalida el grupo entero.
    rutas = [r for r in rutas if path_indexable(r.get("cc"), r.get("path"))]
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


def ruta_calculadora(cc: str, apartado: str = "", cantidad: str = "") -> str:
    """URL de la calculadora, ya apuntando al apartado de esta página.

    Es el enlace de vuelta que faltaba: cada apartado y cada partida mandan
    a la herramienta con su contexto rellenado (país y apartado), y la
    herramienta manda de vuelta a cada partida. Ese ida y vuelta es lo que
    convierte 47.000 páginas sueltas en un silo con una entrada clara.
    """
    from urllib.parse import urlencode

    largo = "en" if (PAISES.get(cc.upper()) or {}).get("idioma") == "en" else "es"
    base = "/en/calculadora" if largo == "en" else "/calculadora"
    parametros = {"cc": cc.upper()}
    if apartado:
        parametros["apartado"] = apartado
    if cantidad:
        parametros["cantidad"] = cantidad
    return f"{base}?{urlencode(parametros)}"


def _base(request: Request, cc: str, ruta: str, seo: dict, bloques: list,
          hreflang_links: list, crumbs: list) -> dict:
    from .seo_latam_comercial import ESCENARIOS

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
        "software_comercial_url": ruta_mercado(cc, "software-presupuestos") if cc in ESCENARIOS else "",
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
    fecha de revisión, autor identificable y acceso libre sin registro.

    La ``distribution`` apunta a ``/{cc}/precios.json``, que existe de verdad
    (mismo catálogo, mismos precios). Antes se omitía para no inventar una
    descarga; desde que el endpoint publica el catálogo completo, declararla
    es lo que hace que el ``Dataset`` sea elegible en Google Dataset Search.
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
        "distribution": [
            {
                "@type": "DataDownload",
                "contentUrl": origen + ruta.rstrip("/") + ".json",
                "encodingFormat": "application/json",
                "name": (nombre_ds),
                "inLanguage": hreflang_pais(cc),
            }
        ],
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
    # Un catálogo parcialmente localizado puede tener fichas indexables en
    # apartados que aún son noindex. Enlazarlas directamente desde el índice
    # evita que su descubrimiento dependa del sitemap o de un listado noindex.
    fichas_directas = []
    if not pp.ficha_indexable(cc):
        indice = pp._indice(cc) or {}
        apartados_indexables = {
            slug: pp.apartado_indexable(cc, slug)
            for slug in (indice.get("apartados") or {})
        }
        for (slug_ap, slug), ficha in sorted((indice.get("partidas") or {}).items()):
            if (not apartados_indexables.get(slug_ap)
                    and pp.partida_indexable(cc, slug_ap, slug)):
                fichas_directas.append({
                    "nombre": ficha["titulo"],
                    "ruta": pp.ruta_partida(cc, slug_ap, slug),
                })
    ctx.update(
        {
            "resumen": {**resumen, "capitulos": capitulos},
            "fichas_directas": fichas_directas,
            "mes_revision": mes,
            "alternates": _alternates_visibles(rutas_alternas, cc),
            "faq": faq,
            "calc_url": ruta_calculadora(cc),
            "mano_obra_url": (
                pp.ruta_mano_obra(cc) if pp.oficios_disponibles(cc) else ""
            ),
            "json_url": pp.ruta_json(cc),
            "ruta_comparador": comparador.ruta_comparador(lang),
            "etiqueta_impuesto": etiqueta_impuesto,
            "tipo_impuesto": tipo_impuesto,
        }
    )
    return ctx


_NOMBRE_CORTO = {"US": ("EE. UU.", "the US"), "GB": ("Reino Unido", "the UK")}


def _nombre_corto(cc: str, nombre: str, en: bool) -> str:
    """Nombre del país para cuando el título va justo de espacio.

    «the United States» gasta 12 caracteres más que «the US» y en un título
    que ya lleva una cifra y una unidad eso decide si el número entra o no.
    """
    corto = _NOMBRE_CORTO.get(str(cc or "").upper())
    if not corto:
        return nombre
    return corto[1] if en else corto[0]


def _primera_clausula(apartado: str) -> str:
    """Primera cláusula del nombre del apartado, si sigue siendo descriptiva.

    «Exploratory openings, detection and surveys» ocupa 45 caracteres y deja
    fuera la cifra; «Exploratory openings» dice lo mismo del contenido de la
    página y deja sitio al precio. Solo se usa cuando no cabe el nombre
    completo, y nunca si la cláusula se queda en una o dos palabras sueltas.
    """
    for separador in (", ", " y ", " and ", " / "):
        cabeza = apartado.split(separador)[0].strip()
        if cabeza and cabeza != apartado and len(cabeza.split()) >= 2:
            return cabeza
    return apartado


def titulo_apartado(
    cc: str,
    apartado: str,
    nombre: str,
    pais: dict,
    partidas: list[dict],
    en: bool,
) -> tuple[str, str]:
    """Título y descripción del hub de apartado, con la cifra dentro.

    «Precios unitarios en España» no promete ninguna cifra y compite contra
    páginas que sí la dan; «de 40 a 264 MXN/m²» responde a la consulta que
    trae al visitante. La cifra tiene que caber en el ancho del resultado, así
    que va sin céntimos y con la moneda una sola vez («40–264 MXN», no
    «40,00 MXN–264,00 MXN»).

    El rango doble solo se escribe si el apartado es homogéneo: sumar precios
    de metro cuadrado y de unidad no da un rango, da un número inventado. Si
    no lo es, se anuncia el mínimo con «desde» y sin unidad.

    El orden de las variantes importa: primero la más informativa, después la
    que conserva el número aunque sea una sola cifra, y solo al final las que
    no dan precio. Antes, cuando el rango no cabía, se caía directamente a la
    versión sin cifra: así se quedaban 120 hubs sin número en el título.
    """
    moneda = str(pais.get("moneda") or "")
    precios = [
        float(partida.get("pu") or 0)
        for partida in partidas
        if float(partida.get("pu") or 0) > 0
    ]
    total = len(partidas)
    unidad, proporcion = _unidad_dominante(partidas)
    homogeneo = bool(precios) and proporcion >= 0.7
    sufijo = f"/{unidad}" if homogeneo and unidad else ""
    rango = rango_prosa = desde = medio = tipico = ""
    if precios:
        bajo = _numero_corto(min(precios), pais)
        alto = _numero_corto(max(precios), pais)
        # Un apartado con una partida de 1 USD y otra de 183 USD no tiene un
        # rango útil: «1–183 USD» parece un error y el «desde 1» del mínimo
        # suelto es peor todavía. Cuando la dispersión pasa de 40 a 1 se
        # anuncia el precio típico (la mediana), que es lo que se busca.
        dispersion = (max(precios) / min(precios)) if min(precios) > 0 else 0
        sesgado = dispersion > 40
        desde = "" if sesgado else f"{bajo} {moneda}{sufijo}"
        if homogeneo and not sesgado:
            rango = f"{bajo}–{alto} {moneda}{sufijo}"
            rango_prosa = f"{bajo} a {alto} {moneda}{sufijo}"
            medio = f"{_numero_corto(sum(precios) / len(precios), pais)} {moneda}{sufijo}"
        if sesgado:
            ordenados = sorted(precios)
            centro = ordenados[len(ordenados) // 2]
            tipico = f"{_numero_corto(centro, pais)} {moneda}{sufijo}"

    # Candidatos de la más informativa a la más escueta. El que cabe se queda:
    # primero con el nombre completo del apartado y el país completo, y solo
    # si no entra se recorta la cláusula del apartado o el nombre del país,
    # nunca la cifra. Antes se saltaba de la versión completa a la que no da
    # precio, que es como se quedaron 1.200 hubs sin número en el título.
    desde_sin_unidad = desde[: -len(sufijo)] if sufijo and desde.endswith(sufijo) else desde
    bases = [apartado]
    clausula = _primera_clausula(apartado)
    if clausula != apartado:
        bases.append(clausula)
    paises = [nombre]
    pais_corto = _nombre_corto(cc, nombre, en)
    if pais_corto != nombre:
        paises.append(pais_corto)

    variantes: list[str] = []
    for base in bases:
        for pais_txt in paises:
            if rango:
                variantes.append(
                    f"{base}: {rango} in {pais_txt}"
                    if en
                    else f"{base}: {rango} en {pais_txt}"
                )
            if desde:
                variantes.append(
                    f"{base}: from {desde} in {pais_txt}"
                    if en
                    else f"{base}: desde {desde} en {pais_txt}"
                )
            if desde_sin_unidad and desde_sin_unidad != desde:
                variantes.append(
                    f"{base}: from {desde_sin_unidad} in {pais_txt}"
                    if en
                    else f"{base}: desde {desde_sin_unidad} en {pais_txt}"
                )
            if tipico:
                variantes.append(
                    f"{base}: avg {tipico} in {pais_txt}"
                    if en
                    else f"{base}: {tipico} de media en {pais_txt}"
                )
    if en:
        variantes += [
            f"{apartado}: unit prices in {nombre} ({moneda})",
            f"{apartado}: prices in {nombre}",
            f"{apartado} — {nombre}",
        ]
        title = _con_marca([_titulo_meta(variantes, respaldo=apartado)])[0]
        if rango:
            description = (
                f"{total} unit prices for {_minuscula_inicial(apartado)} in "
                f"{nombre}: {rango}, average {medio}. Cost breakdown of every "
                "item."
            )
        elif desde:
            description = (
                f"{total} unit prices for {_minuscula_inicial(apartado)} in "
                f"{nombre}: from {desde}. Cost breakdown of every item."
            )
        elif tipico:
            description = (
                f"{total} unit prices for {_minuscula_inicial(apartado)} in "
                f"{nombre}: {tipico} typical, with the full range in the table. "
                "Cost breakdown of every item."
            )
        else:
            description = (
                f"{total} {_minuscula_inicial(apartado)} unit prices for {nombre} "
                f"in {moneda}, each with a full cost breakdown from the CotizaT "
                "construction catalog."
            )
    else:
        variantes += [
            f"{apartado}: precios en {nombre}",
            f"{apartado}: precios en {nombre} ({moneda})",
            f"{apartado} — precios en {nombre}",
        ]
        title = _con_marca([_titulo_meta(variantes, respaldo=apartado)])[0]
        if rango:
            description = (
                f"{total} precios unitarios de {_minuscula_inicial(apartado)} en "
                f"{nombre}: de {rango_prosa} (media {medio}). Descompuesto de "
                "cada partida."
            )
        elif desde:
            description = (
                f"{total} precios unitarios de {_minuscula_inicial(apartado)} en "
                f"{nombre}: desde {desde}. Descompuesto de cada partida."
            )
        elif tipico:
            description = (
                f"{total} precios unitarios de {_minuscula_inicial(apartado)} en "
                f"{nombre}: {tipico} de precio típico, con el rango completo en la "
                "tabla. Descompuesto de cada partida."
            )
        else:
            description = (
                f"{total} precios unitarios de {_minuscula_inicial(apartado)} para "
                f"{nombre} en {moneda}, cada uno con su descompuesto completo del "
                "catálogo CotizaT."
            )
    return title, description


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
    # El título y la descripción del hub salen de una sola función, que se
    # puede probar sin levantar una petición: era la página con más
    # impresiones y menos clics del sitio (63 impresiones, posición 10,2, cero
    # clics en Irlanda) y el arreglo tiene que poder medirse.
    title, description = titulo_apartado(
        cc, apartado, nombre, pais, ficha["partidas"], en
    )
    h1 = (
        f"{apartado} — unit prices in {nombre}"
        if en
        else f"{apartado} — precios unitarios en {nombre}"
    )

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
            "obras_relacionadas": apartados_relacionados(cc, slug),
            "calc_url": ruta_calculadora(cc, slug),
            "mano_obra_url": (
                pp.ruta_mano_obra(cc) if pp.oficios_disponibles(cc) else ""
            ),
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


def _unidad_titulo(unidad: str) -> str:
    """Unidad de medida en la forma que se lee en un título.

    El catálogo guarda «m2»; en un resultado de Google eso parece un error de
    tecleo, así que se escribe «m²». Las unidades que no están en el mapa se
    dejan tal cual: inventar una abreviatura sería peor que la del catálogo.
    """
    clave = str(unidad or "").strip().lower()
    if not clave:
        return ""
    clave = {"m²": "m2", "m³": "m3"}.get(clave, clave)
    return _UNIDADES_TITULO.get(clave, str(unidad).strip())


def titulo_partida(
    cc: str,
    titulo: str,
    unidad: str,
    pu,
    pais: dict,
    en: bool,
) -> str:
    """Título de la ficha de partida, con la cifra dentro.

    «Portón corredizo con automatismo» no responde a quien busca «cuánto
    cuesta»; «Portón corredizo con automatismo — 491 EUR/ud en España» sí, y
    esa diferencia es la que se mide en el CTR de 9.500 impresiones al mes.

    La cifra se escribe como en los hubs: sin céntimos, con la moneda una sola
    vez y redondeando hacia arriba. El precio con céntimos («491,00 EUR») es
    lo que dejaba fuera la cifra: gastaba ocho caracteres de más y el título
    se caía a la variante sin precio.

    Orden de las variantes: primero nombre completo con precio, unidad y país;
    después se recorta el país, luego la unidad y solo al final se renuncia al
    número. El nombre de la partida es lo último que se toca, porque es lo que
    coincide con la consulta; cuando ni así cabe, se prueba su primera cláusula
    («Piso de loseta en baño, con pendiente hacia la coladera» → «Piso de
    loseta en baño»), que es la parte que la gente escribe.
    """
    base_titulo = " ".join(str(titulo or "").split())
    if not base_titulo:
        return ""
    moneda = str(pais.get("moneda") or "").strip()
    cifra = _numero_corto(pu, pais) if moneda else ""
    ud = _unidad_titulo(unidad)
    con_unidad = f"{cifra} {moneda}/{ud}" if cifra and ud else (f"{cifra} {moneda}" if cifra else "")
    sin_unidad = f"{cifra} {moneda}" if cifra else ""
    nombre = _nombre_pais(cc, str(pais.get("idioma") or ("en" if en else "es")))
    corto = _nombre_corto(cc, nombre, en)
    paises = [nombre] + ([corto] if corto and corto != nombre else [])
    preposicion = "in" if en else "en"

    bases = [base_titulo]
    clausula = _primera_clausula(base_titulo)
    if clausula and clausula != base_titulo:
        bases.append(clausula)

    con_cifra: list[str] = []
    for base in bases:
        for pais_txt in paises:
            if con_unidad:
                con_cifra.append(f"{base} — {con_unidad} {preposicion} {pais_txt}")
        if con_unidad:
            con_cifra.append(f"{base} — {con_unidad}")
        for pais_txt in paises:
            if sin_unidad:
                con_cifra.append(f"{base} — {sin_unidad} {preposicion} {pais_txt}")
    # Las variantes con precio se eligen aparte y no con `_titulo_meta`: ese
    # ayudante prefiere lo que cabe en 60 caracteres, y en una ficha eso supone
    # tirar el país teniendo sitio hasta 72. El país es lo que distingue la
    # misma partida en veintidós mercados y, si Google recorta, recorta por el
    # final: el número queda a la vista.
    elegido = next((v for v in con_cifra if len(v) <= 72), "")
    if not elegido:
        # Sin sitio ni para la cifra más corta: se cede el número, no el nombre.
        sin_cifra = (
            [f"{base_titulo} in {nombre}", f"{base_titulo} — price in {nombre}"]
            if en
            else [
                f"{base_titulo} en {nombre}",
                f"{base_titulo} — precio unitario en {nombre}",
                f"{base_titulo} — precio en {nombre}",
            ]
        )
        elegido = _titulo_meta(sin_cifra, respaldo=base_titulo)
    # La marca solo si no empuja el título fuera del ancho útil: en las fichas
    # el nombre de la partida ya gasta casi todo el espacio.
    con_marca = f"{elegido} | CotizaT"
    return con_marca if len(con_marca) <= 72 else elegido


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
    # La cifra del título y la de la descripción tienen que ser la misma: si el
    # título dice «491 EUR/ud» y la descripción «491,00 EUR/ud», el resultado
    # parece descuidado. Los céntimos se quedan en el cuerpo de la ficha.
    pu_serif = _dinero_corto(ficha["pu"], pais)
    # «m2» en la descripción es el nombre del campo, no una unidad: el
    # catálogo guarda ASCII y el lector espera «m²».
    ud_serif = _unidad_titulo(unidad) or str(unidad or "")
    mes = _mes(ficha["fecha_revision"], lang)
    directo = float(ficha["directo"] or 0) or 1.0
    pct = {
        g: round(100 * float(ficha["grupos"].get(g) or 0) / directo)
        for g in ("materiales", "mano_obra", "maquinaria")
    }

    if en:
        title = titulo_partida(cc, titulo, unidad, ficha["pu"], pais, True)
        # El precio y los porcentajes van delante: son lo que se compara en
        # el resultado de búsqueda. El nombre cierra la frase, porque ya está
        # en el título y en el H1 y es la parte que puede recortarse.
        description = (
            f"{pu_serif}/{ud_serif} in {nombre} ({mes}). Materials "
            f"{pct['materiales']}%, labor {pct['mano_obra']}%, equipment "
            f"{pct['maquinaria']}%. Line-by-line cost breakdown from the "
            f"CotizaT catalog."
        )
        h1 = f"{titulo} — price in {nombre}"
    else:
        title = titulo_partida(cc, titulo, unidad, ficha["pu"], pais, False)
        description = (
            f"{pu_serif}/{ud_serif} en {nombre} ({mes}). Materiales "
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
    # ¿Esta partida tiene el mismo código en otros mercados? Si sí, la ficha
    # lleva la tabla de precios por país (comparador internacional).
    codigo_comparador = str(ficha.get("codigo") or "")
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
            "calc_url": ruta_calculadora(cc, slug_apartado),
            "mano_obra_url": (
                pp.ruta_mano_obra(cc) if pp.oficios_disponibles(cc) else ""
            ),
            "comparativa": comparador.comparativa_partida(cc, ficha["codigo"], lang),
            "ruta_comparador": (
                comparador.ruta_comparador(lang)
                if codigo_comparador
                else ""
            ),
            "tasa_fecha": comparador.fecha_tasas(lang),
            "nombre_pais": _nombre_pais(cc, lang),
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


#: Capítulos que van juntos en una obra real, por código de capítulo (los
#: códigos 01–18 significan lo mismo en los 22 mercados, aunque el nombre
#: esté traducido). Es el criterio que usa un jefe de obra: quien
#: impermeabiliza una cubierta va a necesitar el aislamiento y el remate; quien
#: levanta un tabique, el yeso y la pintura. Sin este grafo, cada apartado
#: solo se enlazaba con los de su propio capítulo y la autoridad se quedaba
#: atrapada en 16 islas por país.
_AFINIDAD_CAPITULOS: dict[str, tuple[str, ...]] = {
    "01": ("02", "15"),
    "02": ("15", "01"),
    "03": ("04", "14"),
    "04": ("05", "03"),
    "05": ("04", "06"),
    "06": ("12", "10", "08"),
    "07": ("06", "18"),
    "08": ("06", "09"),
    "09": ("13", "08", "10"),
    "10": ("11", "12", "06"),
    "11": ("10", "05"),
    "12": ("06", "10", "13"),
    "13": ("09", "12"),
    "14": ("03", "11"),
    "15": ("02", "01"),
    "17": ("01", "02"),
    "18": ("07", "10"),
}


def apartados_relacionados(codigo_pais: str, slug: str, limite: int = 3) -> list[dict]:
    """Apartados de capítulos afines, elegidos de forma determinista.

    Se toman ``limite`` apartados de los capítulos que de verdad acompañan a
    esta obra y se eligen con un desplazamiento derivado del slug: cada
    apartado reparte su enlace a un tramo distinto del capítulo afín, en vez
    de que los 2.000 apartados de un país apunten siempre a los mismos tres.
    Estable entre peticiones y despliegues (nada de enlaces aleatorios).
    """
    cc = str(codigo_pais or "").strip().upper()
    resumen = pp_resumen(cc)
    if not resumen:
        return []
    ficha = pp.apartado(cc, slug)
    if not ficha:
        return []
    propio = str(ficha.get("capitulo_codigo") or "")
    afines = _AFINIDAD_CAPITULOS.get(propio, ())
    candidatos: list[dict] = []
    for codigo_capitulo in afines:
        for capitulo in resumen.get("capitulos") or []:
            if capitulo.get("codigo") != codigo_capitulo:
                continue
            candidatos.extend(
                {
                    "nombre": ap["nombre"],
                    "slug": ap["slug"],
                    "capitulo": capitulo.get("nombre") or "",
                    "ruta": pp.ruta_apartado(cc, ap["slug"]),
                }
                for ap in capitulo.get("apartados") or []
                if ap.get("slug") and ap["slug"] != slug
            )
    if not candidatos:
        return []
    arranque = sum(ord(c) * (i + 1) for i, c in enumerate(str(slug))) % len(candidatos)
    salto = max(1, len(candidatos) // max(1, limite))
    elegidos: list[dict] = []
    vistos: set[str] = set()
    for i in range(limite * 4):
        if len(elegidos) >= limite:
            break
        candidato = candidatos[(arranque + i * salto) % len(candidatos)]
        if candidato["slug"] in vistos:
            continue
        vistos.add(candidato["slug"])
        elegidos.append(candidato)
    return elegidos


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
    # En mercados a medio localizar, favorecer apartados realmente indexables
    # sin ocultar el catálogo al usuario cuando todavía no hay ninguno.
    if not pp.ficha_indexable(cc):
        indexables = [slug for slug in slugs if pp.apartado_indexable(cc, slug)]
        if indexables:
            slugs = indexables
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
        "mano_obra": pp.ruta_mano_obra(cc) if pp.oficios_disponibles(cc) else "",
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
                "mano_obra": (
                    pp.ruta_mano_obra(cc) if pp.oficios_disponibles(cc) else ""
                ),
            }
        )
    return salida
