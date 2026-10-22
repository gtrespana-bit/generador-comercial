"""Calculadora pública de presupuesto por partida y país.

Es la puerta de entrada que faltaba: la consulta «cuánto cuesta X m² de Y» es
la de mayor intención del sector y el sitio no tenía ninguna página que la
respondiera sin registrarse.

Decisiones de diseño (importan más que el código):

1. **No hay recetas inventadas.** La calculadora no estima «una reforma de
   baño» con coeficientes que nadie puede comprobar: parte de un apartado
   real del catálogo del país y multiplica su precio unitario por la cantidad
   que introduce la persona. El resultado es el de las partidas publicadas,
   no una media de folleto.
2. **Rango, no número único.** Un apartado agrupa partidas de precio
   distinto (azulejo normal frente a gran formato). Se muestran el mínimo, la
   media y el máximo reales del apartado, y la tabla de partidas que los
   producen, con su enlace. Quien usa el dato sabe de dónde sale.
3. **La canónica no lleva parámetros.** Todas las combinaciones de país,
   apartado y cantidad son la misma página-herramienta: canonicalizan a
   ``/calculadora``. Sin eso, el formulario generaría miles de URLs
   equivalentes.
4. **Funciona en los 22 mercados** sin curación manual: los apartados salen
   del catálogo publicado de cada país, así que no puede quedarse obsoleta ni
   prometer una partida que ese mercado no tiene.
"""

from __future__ import annotations

import math

from starlette.requests import Request

from .paises import PAISES
from .seo import (
    OG_IMAGE,
    hreflang_pais,
    jsonld_organizacion,
    jsonld_webpage,
    jsonld_website,
    origen_canonico,
    ruta_mercado,
)
from .services import precios_publicos as pp

#: Unidades equivalentes que el catálogo escribe de dos formas (``m²`` y
#: ``m2`` conviven en los mismos apartados). Se agrupan para no ofrecer dos
#: opciones que significan lo mismo.
_UNIDADES = {
    "m2": ("m²", "m2", "sq ft", "sf", "sqft", "ft²"),
    "m3": ("m³", "m3", "cu ft", "cf"),
    "ml": ("ml", "m", "lf", "lin m", "ft"),
    "ud": ("ud", "u", "uds", "ea", "each", "unit"),
    "kg": ("kg", "lb", "lbs", "t", "tn"),
    "h": ("h", "hr", "hour"),
    "día": ("día", "dia", "d", "day"),
}


def _canonica(unidad: str) -> str:
    """Forma canónica de una unidad (``m2`` → ``m²``), para agrupar."""
    texto = str(unidad or "").strip().lower()
    for clave, alias in _UNIDADES.items():
        if texto in (a.lower() for a in alias):
            return clave
    return texto


def _etiqueta_unidad(clave: str, lang: str) -> str:
    """Etiqueta visible de la unidad.

    Se usa **la unidad tal y como la publica el catálogo** («m²» en España y
    México, «sq ft» o «ea» en Estados Unidos) en vez de traducirla: es el
    dato que la persona ve en la ficha de la partida y en su presupuesto. El
    ``clave`` canónico solo sirve para agrupar variantes (m² / m2 / sq ft).
    """
    por_defecto = {
        "m2": "m²" if lang != "en" else "sq ft",
        "m3": "m³" if lang != "en" else "cu ft",
        "ml": "ml" if lang != "en" else "lin ft",
        "ud": "ud" if lang != "en" else "ea",
        "kg": "kg",
        "h": "h" if lang != "en" else "hr",
        "día": "día" if lang != "en" else "day",
    }
    return por_defecto.get(clave, clave)


def _importe(valor: float, pais: dict, decimales: int = 2) -> str:
    """Importe con los separadores del país y su moneda."""
    if valor >= 100_000:
        decimales = 0
    miles = str(pais.get("separador_miles") or ",")
    decimal = str(pais.get("separador_decimal") or ".")
    texto = f"{valor:,.{decimales}f}"
    if miles != "," or decimal != ".":
        texto = texto.replace(",", "\x00").replace(".", decimal).replace("\x00", miles)
    return f"{texto} {pais.get('moneda') or ''}".strip()


def _cantidad(valor: float, pais: dict | None = None) -> str:
    """Cantidad sin ceros de relleno y con el separador decimal del país."""
    if abs(valor - round(valor)) < 1e-9:
        return str(int(round(valor)))
    texto = f"{valor:g}"
    decimal = str((pais or {}).get("separador_decimal") or ".")
    return texto.replace(".", decimal) if decimal != "." else texto


def _numero(texto) -> float:
    """Cantidad escrita por la persona, sin romper la página.

    Acepta coma decimal (``2,5``) y devuelve 0 ante cualquier cosa que no sea
    un número: la calculadora enseña entonces los precios unitarios, que es
    una respuesta útil, en vez de un error 500 por un parámetro retocado a
    mano en la URL.
    """
    try:
        valor = float(str(texto).strip().replace(",", "."))
    except (TypeError, ValueError):
        return 0.0
    if valor != valor:  # NaN
        return 0.0
    return max(0.0, min(valor, 100_000.0))


def _unidades_disponibles(partidas: list[dict]) -> list[dict]:
    """Unidades del apartado, con la grafía original del catálogo."""
    vistas: dict[str, str] = {}
    for partida in partidas:
        clave = _canonica(partida.get("unidad"))
        if clave and clave not in vistas:
            vistas[clave] = str(partida.get("unidad") or clave).strip()
    return [{"clave": clave, "original": original} for clave, original in vistas.items()]


def obras_de(cc: str) -> list[dict]:
    """Capítulos y apartados publicados del país, para el selector.

    Se agrupan por capítulo porque es la forma en que se piensa una obra
    (demoliciones, instalaciones, acabados) y porque un desplegable plano de
    180 apartados no se puede usar.
    """
    resumen = pp.resumen(cc)
    if not resumen:
        return []
    return [
        {
            "codigo": capitulo["codigo"],
            "nombre": capitulo["nombre"],
            "apartados": [
                {"slug": ap["slug"], "nombre": ap["nombre"], "n": ap.get("n_partidas") or 0}
                for ap in capitulo["apartados"]
            ],
        }
        for capitulo in resumen["capitulos"]
        if capitulo["apartados"]
    ]


def _grupos_de(cc: str, slug_apartado: str, partidas: list[dict]) -> dict:
    """Porcentaje de materiales / mano de obra / maquinaria sobre el directo.

    Se pondera por importe (un apartado con una partida de 30.000 y otra de
    300 no se reparte al 50 %) y se toma del descompuesto real de cada
    partida, no de una constante del sector.
    """
    total = 0.0
    acumulado = {"materiales": 0.0, "mano_obra": 0.0, "maquinaria": 0.0}
    for partida in partidas:
        ficha = pp.partida(cc, slug_apartado, partida["slug"])
        if not ficha:
            continue
        # Sobre el coste directo, no sobre el precio final: el PU incluye
        # costes indirectos y complementarios que no son ni material ni
        # mano de obra, y mezclarlos hacía que los porcentajes no sumaran
        # 100 y parecieran un error de cálculo.
        directo = float(ficha.get("directo") or 0)
        if directo <= 0:
            continue
        total += directo
        for grupo in acumulado:
            acumulado[grupo] += float((ficha.get("grupos") or {}).get(grupo) or 0)
    if total <= 0:
        return {}
    porcentajes = {
        grupo: round(100 * valor / total)
        for grupo, valor in acumulado.items()
        if valor > 0
    }
    # El redondeo puede dejar 99 o 101. Se ajusta el grupo mayor para que la
    # suma sea exactamente 100: un reparto que no suma 100 parece un error.
    if porcentajes:
        mayor = max(porcentajes, key=lambda g: porcentajes[g])
        porcentajes[mayor] += 100 - sum(porcentajes.values())
    return porcentajes


_ETIQUETAS_GRUPO = {
    "materiales": ("Materiales", "Materials"),
    "mano_obra": ("Mano de obra", "Labour"),
    "maquinaria": ("Maquinaria", "Equipment"),
}


def _grupos_etiquetados(grupos: dict, lang: str) -> list[dict]:
    """Reparto en el idioma de la página, en orden fijo (no el del dict)."""
    indice = 1 if lang == "en" else 0
    return [
        {"nombre": _ETIQUETAS_GRUPO[clave][indice], "pct": grupos[clave]}
        for clave in ("materiales", "mano_obra", "maquinaria")
        if clave in grupos
    ]


def calcular(
    cc: str, slug_apartado: str, cantidad: float, unidad: str = ""
) -> dict | None:
    """Estimación real de un apartado para una cantidad dada."""
    codigo = str(cc or "").strip().upper()
    if codigo not in PAISES:
        return None
    ficha = pp.apartado(codigo, slug_apartado)
    if ficha is None:
        return None
    pais = PAISES[codigo]
    lang = "en" if pais.get("idioma") == "en" else "es"

    disponibles = _unidades_disponibles(ficha["partidas"])
    clave_unidad = (
        _canonica(unidad) if unidad else (disponibles[0]["clave"] if disponibles else "")
    )
    claves = [u["clave"] for u in disponibles]
    if claves and clave_unidad not in claves:
        # Unidad pedida por URL que este apartado no usa: se cae a la suya.
        clave_unidad = claves[0]
    partidas = [
        p
        for p in ficha["partidas"]
        if not clave_unidad or _canonica(p.get("unidad")) == clave_unidad
    ]
    if not partidas:
        partidas = list(ficha["partidas"])

    precios = [float(p["pu"]) for p in partidas if float(p.get("pu") or 0) > 0]
    cantidad = _numero(cantidad)

    lineas = []
    for partida in sorted(partidas, key=lambda p: float(p.get("pu") or 0)):
        pu = float(partida.get("pu") or 0)
        lineas.append(
            {
                "titulo": partida["titulo"],
                "ruta": pp.ruta_partida(codigo, slug_apartado, partida["slug"]),
                "pu": _importe(pu, pais),
                "pu_n": pu,
                "importe": _importe(pu * cantidad, pais) if cantidad else "",
            }
        )

    totales = {}
    if precios and cantidad:
        totales = {
            "minimo": _importe(min(precios) * cantidad, pais),
            "medio": _importe(sum(precios) / len(precios) * cantidad, pais),
            "maximo": _importe(max(precios) * cantidad, pais),
        }

    return {
        "cc": codigo,
        "pais": pais,
        "nombre_pais": pais.get("nombre_en") if lang == "en" else pais.get("nombre"),
        "lang": lang,
        "apartado": {
            "slug": ficha["slug"],
            "nombre": ficha["nombre"],
            "capitulo": ficha.get("capitulo") or "",
            "ruta": pp.ruta_apartado(codigo, ficha["slug"]),
        },
        "unidades": [
            {
                "clave": u["clave"],
                "etiqueta": u["original"] or _etiqueta_unidad(u["clave"], lang),
            }
            for u in disponibles
        ],
        "unidad": clave_unidad,
        "unidad_etiqueta": next(
            (
                u["original"]
                for u in disponibles
                if u["clave"] == clave_unidad and u["original"]
            ),
            _etiqueta_unidad(clave_unidad, lang),
        ),
        "cantidad": cantidad,
        "cantidad_txt": _cantidad(cantidad, pais),
        "lineas": lineas,
        "totales": totales,
        "grupos": _grupos_etiquetados(_grupos_de(codigo, slug_apartado, partidas), lang),
        "indice": pp.ruta_indice(codigo),
        "mes": (pp.resumen(codigo) or {}).get("fecha_revision") or "",
    }


def hermanos_de(cc: str, slug_apartado: str, limite: int = 6) -> list[dict]:
    """Apartados del mismo capítulo, para seguir calculando."""
    resumen = pp.resumen(cc)
    ficha = pp.apartado(cc, slug_apartado)
    if not resumen or not ficha:
        return []
    for capitulo in resumen["capitulos"]:
        if capitulo["codigo"] != ficha.get("capitulo_codigo"):
            continue
        return [
            {"nombre": ap["nombre"], "slug": ap["slug"]}
            for ap in capitulo["apartados"]
            if ap["slug"] != slug_apartado
        ][:limite]
    return []


def _jsonld_herramienta(request: Request, lang: str, ruta: str) -> dict:
    """La calculadora como ``WebApplication`` gratuita.

    Es honesto: la herramienta se usa en el navegador y no cuesta nada. El
    ``Offer`` a 0 es lo que permite que Google la trate como aplicación y no
    como una página de texto más.
    """
    origen = origen_canonico(request)
    en = lang == "en"
    return {
        "@context": "https://schema.org",
        "@id": origen + ruta + "#app",
        "@type": "WebApplication",
        "name": (
            "CotizaT unit price calculator"
            if en
            else "Calculadora de presupuesto de obra de CotizaT"
        ),
        "url": origen + ruta,
        "applicationCategory": "BusinessApplication",
        "operatingSystem": "Web",
        "browserRequirements": "Requires JavaScript off — works server side",
        "isAccessibleForFree": True,
        "inLanguage": "en" if en else "es",
        "offers": {
            "@type": "Offer",
            "price": "0",
            "priceCurrency": "USD",
        },
        "featureList": (
            [
                "Real unit prices from the published catalog",
                "Cost range instead of a single figure",
                "Materials, labour and equipment split",
            ]
            if en
            else [
                "Precios unitarios reales del catálogo publicado",
                "Rango de coste en vez de una cifra única",
                "Reparto de materiales, mano de obra y maquinaria",
            ]
        ),
    }


def contexto_calculadora(
    request: Request,
    cc: str = "",
    apartado: str = "",
    cantidad: str = "",
    unidad: str = "",
) -> dict:
    """Contexto de la página-herramienta (país y cálculo opcionales)."""
    lang = "en" if getattr(request.state, "lang", "es") == "en" else "es"
    en = lang == "en"
    origen = origen_canonico(request)
    ruta = "/en/calculadora" if en else "/calculadora"

    publicados = sorted(pp.paises_publicados())
    codigo = str(cc or "").strip().upper()
    if codigo not in publicados:
        # Sin país elegido se preselecciona uno con catálogo amplio: la
        # herramienta tiene que enseñar un resultado al primer clic.
        codigo = "MX" if "MX" in publicados else (publicados[0] if publicados else "")

    paises = [
        {
            "codigo": c,
            "nombre": (PAISES[c].get("nombre_en") if en else PAISES[c].get("nombre"))
            or PAISES[c].get("nombre")
            or c,
            "bandera": PAISES[c].get("bandera") or "",
        }
        for c in publicados
    ]
    obras = obras_de(codigo) if codigo else []
    slug = str(apartado or "").strip()
    if not slug and obras:
        # Primer apartado por defecto: el más completo de un capítulo de
        # acabados (12) y, si el país no lo tiene, el más completo del
        # catálogo. Abrir la herramienta en un apartado de tres partidas da
        # una primera impresión pobre de un catálogo de 2.000.
        preferido = next((c for c in obras if c["codigo"] == "12"), None)
        candidatos = preferido["apartados"] if preferido else [
            ap for c in obras for ap in c["apartados"]
        ]
        slug = max(candidatos, key=lambda ap: ap["n"])["slug"] if candidatos else ""

    resultado = calcular(codigo, slug, cantidad or 10, unidad) if codigo and slug else None
    if resultado is None and obras:
        # Un slug que no existe en este mercado (los de otro país, o una URL
        # vieja) no debe dejar la herramienta vacía: se cae al primer apartado.
        resultado = calcular(codigo, obras[0]["apartados"][0]["slug"], cantidad or 10, unidad)
        slug = obras[0]["apartados"][0]["slug"]
    hermanos = (
        [
            {
                "nombre": h["nombre"],
                "ruta": pp.ruta_apartado(codigo, h["slug"]),
                "calc": (
                    f"{ruta}?cc={codigo}&apartado={h['slug']}&cantidad={_cantidad(_numero(cantidad) or 10)}"
                ),
            }
            for h in hermanos_de(codigo, slug)
        ]
        if resultado
        else []
    )

    titulo = (
        "Construction cost calculator with real unit prices"
        if en
        else "Calculadora de presupuesto de obra con precios reales"
    )
    descripcion = (
        "Pick a construction item, enter the quantity and get the cost range "
        "from the published unit prices of your country: materials, labour and "
        "equipment included. Free, no sign-up."
        if en
        else (
            "Elige una partida, pon la cantidad y obtén el rango de coste con "
            "los precios unitarios publicados de tu país: materiales, mano de "
            "obra y maquinaria. Gratis y sin registro."
        )
    )

    bloques = [
        jsonld_organizacion(request, lang=lang),
        jsonld_website(request, lang=lang),
        jsonld_webpage(request, ruta, titulo, descripcion, lang=lang),
        _jsonld_herramienta(request, lang, ruta),
    ]

    return {
        "seo": {
            "title": titulo,
            "description": descripcion,
            "lang": lang,
            "h1": titulo,
        },
        "canonical_url": origen + ruta,
        "hreflang_links": [
            {"hreflang": "es", "href": origen + "/calculadora"},
            {"hreflang": "en", "href": origen + "/en/calculadora"},
            {"hreflang": "x-default", "href": origen + "/calculadora"},
        ],
        "og_image": origen + OG_IMAGE,
        "jsonld_bloques": bloques,
        "crumbs": [
            ("Home" if en else "Inicio", "/en-us/" if en else "/"),
            (
                "Construction prices" if en else "Precios de construcción",
                pp.ruta_indice(codigo) if codigo else ruta_mercado("MX"),
            ),
            ("Calculator" if en else "Calculadora", ruta),
        ],
        "ruta": ruta,
        "lang": lang,
        "paises": paises,
        "cc": codigo,
        "obras": obras,
        "resultado": resultado,
        "hermanos": hermanos,
        "cantidad_valor": _cantidad(_numero(cantidad) or 10),
        "ruta_catalogo": pp.ruta_indice(codigo) if codigo else "",
        "moneda": (PAISES.get(codigo) or {}).get("moneda") or "",
        "hreflang_pais": hreflang_pais(codigo) if codigo else "es",
    }
