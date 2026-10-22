"""Comparador internacional de precios: la misma partida en los 22 mercados.

Por qué existe
--------------
Cada mercado tiene su catálogo, con su moneda y sus precios. Hasta ahora esos
22 catálogos eran 22 silos: nadie podía responder «¿cuánto cuesta esto en
México comparado con España?» sin abrir 22 fichas y convertir a mano.

Y resulta que sí se puede responder con rigor, porque **1 675 partidas
comparten el mismo código en los 22 mercados** (el código 12.05.03.010 es
«Piso cerámico o porcelanato de formato estándar» en México y en los otros 21).
Eso no es una casualidad: los catálogos se construyeron sobre la misma
estructura, así que la comparación es entre la misma unidad de obra.

Cómo se compara
---------------
1. Se toma la cesta de partidas que existen en **todos** los mercados, con la
   misma familia de unidad, excluyendo las de precio alzado (``glb``).
2. Cada precio se normaliza: unidades imperiales → métricas (``sq ft`` → m²,
   ``cu yd`` → m³) y moneda local → USD con la tasa de referencia ya congelada
   en ``app.services.tasa``.
3. Para cada partida se calcula la **mediana** de los 22 precios y, para cada
   mercado, la **mediana de sus cocientes** frente a esa mediana. La mediana
   (no la media) porque un precio mal cargado en un mercado no debe mover el
   índice de todos.

El índice resultante es «100 = mediana internacional». Un mercado con 250
significa que, en la misma cesta de 1 675 partidas y en dólares, sus precios
son 2,5 veces la mediana. Es un dato que hoy no publica nadie con esta base.

Lo que este dato NO es
----------------------
No es un índice de coste de vida ni un IPC: es el nivel de precios *del
catálogo* de cada mercado, que refleja a la vez coste local, productividad,
tipo de cambio y la política de precios del propio catálogo. La página lo dice
en el FAQ, y también dice qué parte del resultado es tipo de cambio.

El tipo de cambio es el punto débil real: la tasa está congelada en
``TASAS_SUGERIDAS`` (ver ``TASAS_ACTUALIZADAS``) y los precios de cada catálogo
en su fecha de revisión. Por eso la página publica ambas fechas y avisa de que
un salto cambiario fuerte mueve el índice aunque la obra no haya cambiado.
"""

from __future__ import annotations

import statistics
from functools import lru_cache

from starlette.requests import Request

from .fechas_texto import mes_anio_es
from .seo import (
    OG_IMAGE,
    jsonld_breadcrumb,
    jsonld_faq,
    jsonld_organizacion,
    jsonld_website,
    origen_canonico,
)
from .services import precios_publicos as pp
from .services.tasa import TASAS_ACTUALIZADAS, TASAS_SUGERIDAS
from .services.unidades_precio import convertir_precio_unidad, normalizar_unidad

#: Fecha de la tasa de cambio usada en la comparación. Se expone aquí para que
#: las plantillas no tengan que importar el servicio de tasas.
TASAS_SUGERIDAS_FECHA = TASAS_ACTUALIZADAS

#: Unidades métricas canónicas a las que se lleva todo antes de comparar.
_METRICAS = ("m2", "m3", "m", "kg", "l", "ud", "hora")

#: Precio alzado: no es una unidad de medida, así que no se compara.
_NO_COMPARABLES = frozenset({"glb", ""})

#: Etiqueta estable de cada capítulo del catálogo (código 01–18).
#:
#: El nombre cambia con el idioma del mercado, pero el código es el mismo en
#: los 22: el diccionario fija la URL y el texto de cada capítulo para que la
#: página no dependa de qué mercado esté publicado ni en qué idioma.
CAPITULOS: dict[str, dict[str, str]] = {
    "01": {"es": "Actuaciones previas", "en": "Preliminary work", "slug_es": "actuaciones-previas", "slug_en": "preliminary-work"},
    "02": {"es": "Demoliciones y desmontajes", "en": "Demolition and dismantling", "slug_es": "demoliciones-y-desmontajes", "slug_en": "demolition-and-dismantling"},
    "03": {"es": "Acondicionamiento del terreno", "en": "Earthwork and site preparation", "slug_es": "acondicionamiento-del-terreno", "slug_en": "earthwork-and-site-preparation"},
    "04": {"es": "Cimentaciones", "en": "Foundations", "slug_es": "cimentaciones", "slug_en": "foundations"},
    "05": {"es": "Estructuras", "en": "Structures", "slug_es": "estructuras", "slug_en": "structures"},
    "06": {"es": "Fachadas y particiones", "en": "Facades and partitions", "slug_es": "fachadas-y-particiones", "slug_en": "facades-and-partitions"},
    "07": {"es": "Carpintería, herrería, vidrios y protección solar", "en": "Carpentry, metalwork, glazing and solar shading", "slug_es": "carpinteria-herreria-vidrios-y-proteccion-solar", "slug_en": "carpentry-metalwork-glazing-and-solar-shading"},
    "08": {"es": "Remates y ayudas", "en": "Trim work and builder's work", "slug_es": "remates-y-ayudas", "slug_en": "trim-work-and-builders-work"},
    "09": {"es": "Instalaciones", "en": "Building services (MEP)", "slug_es": "instalaciones", "slug_en": "building-services-mep"},
    "10": {"es": "Aislamientos e impermeabilizaciones", "en": "Insulation and waterproofing", "slug_es": "aislamientos-e-impermeabilizaciones", "slug_en": "insulation-and-waterproofing"},
    "11": {"es": "Techos y cubiertas", "en": "Roofs and roofing", "slug_es": "techos-y-cubiertas", "slug_en": "roofs-and-roofing"},
    "12": {"es": "Revestimientos y acabados", "en": "Coatings and finishes", "slug_es": "revestimientos-y-acabados", "slug_en": "coatings-and-finishes"},
    "13": {"es": "Equipamiento, mobiliario y señalización", "en": "Equipment, furniture and signage", "slug_es": "equipamiento-mobiliario-y-senalizacion", "slug_en": "equipment-furniture-and-signage"},
    "14": {"es": "Obras exteriores y urbanismo", "en": "Exterior and site works", "slug_es": "obras-exteriores-y-urbanismo", "slug_en": "exterior-and-site-works"},
    "15": {"es": "Gestión de residuos y limpieza", "en": "Waste management and cleaning", "slug_es": "gestion-de-residuos-y-limpieza", "slug_en": "waste-management-and-cleaning"},
    "18": {"es": "Rehabilitación energética", "en": "Energy retrofit", "slug_es": "rehabilitacion-energetica", "slug_en": "energy-retrofit"},
}

#: URL del comparador en cada idioma.
RUTAS = {"es": "/precios-comparados", "en": "/en/prices-comparison"}

#: Mercado cuya nomenclatura se usa como referencia de cada idioma.
_BASE = {"es": "MX", "en": "US"}


def ruta_comparador(lang: str = "es") -> str:
    return RUTAS.get(lang if lang in RUTAS else "es")


def ruta_capitulo(lang: str, codigo: str) -> str:
    datos = CAPITULOS.get(str(codigo))
    if not datos:
        return ruta_comparador(lang)
    sufijo = datos["slug_en"] if lang == "en" else datos["slug_es"]
    return f"{ruta_comparador(lang)}/{sufijo}"


def _a_metrica(precio: float, unidad: str) -> tuple[float, str] | None:
    """Precio llevado a unidad métrica canónica, o ``None`` si no se puede."""
    normal = normalizar_unidad(unidad)
    if normal in _NO_COMPARABLES:
        return None
    if normal in _METRICAS:
        return float(precio), normal
    for destino in _METRICAS:
        convertido = convertir_precio_unidad(precio, unidad, destino)
        if convertido is not None:
            return convertido, destino
    return None


def _a_usd(cc: str, precio: float, unidad: str) -> tuple[float, str] | None:
    """Precio en dólares (tasa de referencia congelada) y unidad métrica."""
    metrica = _a_metrica(precio, unidad)
    if metrica is None:
        return None
    moneda = str((pp.PAISES.get(cc) or {}).get("moneda") or "")
    tasa = TASAS_SUGERIDAS.get(moneda)
    if not tasa:
        return None
    valor, unidad_metrica = metrica
    return valor / float(tasa), unidad_metrica


@lru_cache(maxsize=1)
def _datos() -> dict:
    """Cesta común, índices y cifras por capítulo. Se calcula una vez (~1,2 s).

    Todo sale del catálogo publicado: si mañana cambian los precios de un
    mercado, el índice cambia solo. No hay ninguna tabla escrita a mano.
    """
    mercados = sorted(pp.paises_publicados())
    indices = {cc: pp._indice(cc) for cc in mercados}  # noqa: SLF001
    if "MX" not in indices:
        return {"mercados": [], "cesta": {}, "mediana": {}, "indices": {}, "capitulos": {}}

    # 1. Cesta: códigos que existen en los 22 mercados con la misma familia
    #    de unidad. Si en algún mercado falta o la unidad no converge, fuera:
    #    comparar un m² con una unidad suelta daría una tabla falsa.
    cesta: dict[str, dict[str, tuple[float, str]]] = {}
    for codigo in indices["MX"]["por_codigo"]:
        fila: dict[str, tuple[float, str]] = {}
        for cc in mercados:
            destino = indices[cc]["por_codigo"].get(codigo)
            if not destino:
                fila = {}
                break
            ficha = indices[cc]["partidas"][destino]
            valor = _a_usd(cc, float(ficha["pu"]), str(ficha["unidad"]))
            if valor is None:
                fila = {}
                break
            fila[cc] = valor
        if not fila:
            continue
        if len({unidad for _valor, unidad in fila.values()}) != 1:
            continue
        cesta[codigo] = fila

    if not cesta:
        return {"mercados": mercados, "cesta": {}, "mediana": {}, "indices": {}, "capitulos": {}}

    # 2. Mediana internacional de cada partida y cociente de cada mercado.
    mediana = {
        codigo: statistics.median(valor for valor, _u in fila.values())
        for codigo, fila in cesta.items()
    }
    indices_pais = {}
    for cc in mercados:
        cocientes = [
            fila[cc][0] / mediana[codigo]
            for codigo, fila in cesta.items()
            if mediana[codigo] > 0
        ]
        indices_pais[cc] = statistics.median(cocientes) * 100 if cocientes else 0.0

    # 3. Lo mismo por capítulo, para la página de cada capítulo.
    capitulos: dict[str, dict] = {}
    for codigo_cap, etiqueta in CAPITULOS.items():
        codigos = [c for c in cesta if c.split(".")[0] == codigo_cap]
        if not codigos:
            continue
        por_pais = {}
        for cc in mercados:
            cocientes = [
                cesta[c][cc][0] / mediana[c] for c in codigos if mediana[c] > 0
            ]
            por_pais[cc] = statistics.median(cocientes) * 100 if cocientes else 0.0
        capitulos[codigo_cap] = {
            "codigo": codigo_cap,
            "nombre_es": etiqueta["es"],
            "nombre_en": etiqueta["en"],
            "slug_es": etiqueta["slug_es"],
            "slug_en": etiqueta["slug_en"],
            "n": len(codigos),
            "indices": por_pais,
            "codigos": codigos,
        }

    return {
        "mercados": mercados,
        "cesta": cesta,
        "mediana": mediana,
        "indices": indices_pais,
        "capitulos": capitulos,
        "tasa_fecha": TASAS_ACTUALIZADAS,
    }


def _importe(valor: float, pais: dict, decimales: int = 2) -> str:
    miles = str(pais.get("separador_miles") or ",")
    decimal = str(pais.get("separador_decimal") or ".")
    texto = f"{valor:,.{decimales}f}"
    if miles != "," or decimal != ".":
        texto = texto.replace(",", "\x00").replace(".", decimal).replace("\x00", miles)
    return f"{texto} {pais.get('moneda') or ''}".strip()


def fecha_tasas(lang: str = "es") -> str:
    """Fecha de la tasa de cambio lista para una frase, en el idioma pedido."""
    return _fecha_txt(lang)


def _fecha_txt(lang: str) -> str:
    """Fecha de la tasa en el idioma de la página («agosto de 2026»)."""
    iso = TASAS_ACTUALIZADAS
    if lang != "en":
        return mes_anio_es(iso) or iso
    meses = ("January", "February", "March", "April", "May", "June", "July",
             "August", "September", "October", "November", "December")
    try:
        anio, mes = int(iso[:4]), int(iso[5:7])
        return f"{meses[mes - 1]} {anio}"
    except (ValueError, IndexError):
        return iso


def _usd(valor: float, lang: str = "es") -> str:
    """Importe en USD con el separador del idioma: «18,85 USD» / «$18.85»."""
    texto = f"{valor:,.2f}"
    if lang == "en":
        return f"{texto} USD"
    return texto.replace(",", "\x00").replace(".", ",").replace("\x00", "\u00a0") + " USD"


def _limpiar(texto: str, maximo: int = 158) -> str:
    """Descripción de una línea, cortada por palabra y sin cortes a medias."""
    limpio = " ".join(str(texto or "").split())
    if len(limpio) <= maximo:
        return limpio
    corte = limpio[:maximo]
    if " " in corte:
        corte = corte[: corte.rfind(" ")]
    corte = corte.rstrip(" ,;:.")
    return corte + "."


def _miles(valor: int, lang: str) -> str:
    """Miles con el separador del idioma: «1 675» / «1,675»."""
    texto = f"{int(valor):,}".replace(",", "\x00")
    return texto.replace("\x00", "," if lang == "en" else "\u00a0")


def _nombre_en_frase(cc: str, lang: str) -> str:
    """Nombre del mercado para usarlo dentro de una frase, con mayúscula."""
    nombre = _nombre_mercado(cc, lang)
    return nombre[:1].upper() + nombre[1:] if nombre else nombre


def _unidad_txt(unidad: str, lang: str) -> str:
    if lang == "en":
        return {
            "m2": "m²", "m3": "m³", "m": "m", "kg": "kg", "l": "L",
            "ud": "each", "hora": "h",
        }.get(unidad, unidad)
    return {
        "m2": "m²", "m3": "m³", "m": "m", "kg": "kg", "l": "l",
        "ud": "ud", "hora": "h",
    }.get(unidad, unidad)


def _nombre_mercado(cc: str, lang: str) -> str:
    pais = pp.PAISES.get(cc) or {}
    if lang == "en":
        return str(pais.get("nombre_en") or pais.get("nombre") or cc)
    return str(pais.get("nombre") or cc)


def _bandera(cc: str) -> str:
    return str((pp.PAISES.get(cc) or {}).get("bandera") or "")


def ranking(lang: str = "es") -> list[dict]:
    """Los 22 mercados ordenados por nivel de precios del catálogo."""
    datos = _datos()
    filas = [
        {
            "cc": cc,
            "nombre": _nombre_en_frase(cc, lang),
            "bandera": _bandera(cc),
            "indice": round(datos["indices"][cc], 1),
            "ruta": pp.ruta_indice(cc),
        }
        for cc in datos["mercados"]
    ]
    filas.sort(key=lambda f: f["indice"], reverse=True)
    base = datos["indices"].get("MX") or 0
    for fila in filas:
        # Referencia útil para el lector local: cuánto es respecto a su país.
        fila["vs_mx"] = round(fila["indice"] / base, 2) if base else 0
        fila["vs_mediana_pct"] = round(fila["indice"] - 100, 1)
    return filas


def partidas_destacadas(limite: int = 12, lang: str = "es") -> list[dict]:
    """Partidas de la cesta con mayor diferencia entre el mercado más caro y el más barato.

    Son las que mejor enseñan lo que mueve el precio: materiales importados,
    mano de obra intensiva, equipo especializado. Se eligen por cociente, no
    por importe, para que no salgan siempre las partidas más caras.
    """
    datos = _datos()
    if not datos["cesta"]:
        return []
    filas = []
    base_cc = _BASE.get(lang, "MX")
    for codigo, fila in datos["cesta"].items():
        valores = {cc: valor for cc, (valor, _u) in fila.items()}
        maximo = max(valores.values())
        minimo = min(valores.values())
        if minimo <= 0:
            continue
        caro = max(valores, key=valores.get)
        barato = min(valores, key=valores.get)
        unidad = next(iter(fila.values()))[1]
        filas.append(
            {
                "codigo": codigo,
                "cociente": maximo / minimo,
                "caro": {"cc": caro, "nombre": _nombre_mercado(caro, lang), "usd": valores[caro]},
                "barato": {"cc": barato, "nombre": _nombre_mercado(barato, lang), "usd": valores[barato]},
                "unidad": unidad,
                "unidad_txt": _unidad_txt(unidad, lang),
                "mediana": datos["mediana"][codigo],
                "base": valores.get(base_cc),
            }
        )
    filas.sort(key=lambda f: f["cociente"], reverse=True)
    return filas[:limite]


def _nombre_partida(codigo: str, lang: str) -> str:
    """Nombre de la partida en el idioma de la página (MX o US como base)."""
    cc = _BASE.get(lang, "MX")
    indice = pp._indice(cc)  # noqa: SLF001
    destino = indice["por_codigo"].get(codigo)
    if not destino:
        return codigo
    return str(indice["partidas"][destino]["titulo"])


def comparativa_partida(cc_origen: str, codigo: str, lang: str = "es") -> list[dict]:
    """El precio de esta partida en cada mercado, ordenado de caro a barato.

    Se usa en la ficha de cada partida cuando el código existe en varios
    mercados: convierte 1 675 páginas en una tabla comparativa internacional
    sin inventar una sola cifra, porque el precio es el del catálogo de cada
    país, normalizado a dólares y a unidad métrica.
    """
    datos = _datos()
    fila = datos["cesta"].get(codigo)
    if not fila or len(fila) < 5:
        return []
    unidad = next(iter(fila.values()))[1]
    salida = []
    for cc, (valor, _u) in fila.items():
        indice = pp._indice(cc)  # noqa: SLF001
        destino = indice["por_codigo"].get(codigo)
        if not destino:
            continue
        slug_ap, slug_p = destino
        salida.append(
            {
                "cc": cc,
                "nombre": _nombre_en_frase(cc, lang),
                "bandera": _bandera(cc),
                "usd": valor,
                "usd_txt": _usd(valor),
                "local_txt": _importe(
                    float(indice["partidas"][destino]["pu"]),
                    pp.PAISES.get(cc) or {},
                ),
                "unidad_local": str(indice["partidas"][destino]["unidad"]),
                "ruta": pp.ruta_partida(cc, slug_ap, slug_p),
                "actual": cc == cc_origen,
            }
        )
    salida.sort(key=lambda f: f["usd"], reverse=True)
    return salida


def capitulos_publicados() -> tuple[str, ...]:
    """Capítulos con datos comparables en los 22 mercados.

    No todos los capítulos existen en todos los mercados: «Gestión de residuos
    y limpieza» no está en los cinco mercados de habla inglesa, así que no se
    puede comparar y su URL daría una tabla vacía. Sin dato diferencial no hay
    página (ni entrada en el sitemap): solo se publican los capítulos que
    tienen cesta común.
    """
    return tuple(sorted(_datos()["capitulos"]))


def contexto_comparador(request: Request, codigo_capitulo: str | None = None, lang: str = "es") -> dict | None:
    """Contexto de la página del comparador (portada o capítulo)."""
    datos = _datos()
    if not datos["cesta"]:
        return None
    en = lang == "en"
    origen = origen_canonico(request)

    if codigo_capitulo:
        capitulo = datos["capitulos"].get(str(codigo_capitulo))
        if not capitulo:
            return None
        nombre_cap = capitulo["nombre_en"] if en else capitulo["nombre_es"]
        n = capitulo["n"]
        n_txt = _miles(n, lang)
        title = (
            f"{nombre_cap}: prices in 22 countries"
            if en
            else f"{nombre_cap}: precios en 22 países"
        )
        description = (
            f"{n_txt} {nombre_cap.lower()} items with their price in 22 countries, in USD. "
            f"Index 100 = international median."
            if en
            else f"{n_txt} partidas de «{nombre_cap.lower()}» con su precio en 22 países, "
            f"en dólares. Índice 100 = mediana internacional."
        )
        h1 = (
            f"{nombre_cap}: the same items in 22 countries"
            if en
            else f"{nombre_cap}: las mismas partidas en 22 países"
        )
        ruta = ruta_capitulo(lang, codigo_capitulo)
        filas = sorted(
            (
                {
                    "cc": cc,
                    "nombre": _nombre_en_frase(cc, lang),
                    "bandera": _bandera(cc),
                    "indice": round(valor, 1),
                    "ruta": pp.ruta_indice(cc),
                }
                for cc, valor in capitulo["indices"].items()
            ),
            key=lambda f: f["indice"],
            reverse=True,
        )
        mayor = filas[0] if filas else None
        menor = filas[-1] if filas else None
        partidas = []
        for cod in sorted(capitulo["codigos"]):
            fila = datos["cesta"][cod]
            valores = {cc: v for cc, (v, _u) in fila.items()}
            unidad = next(iter(fila.values()))[1]
            caro_cc = max(valores, key=valores.get)
            barato_cc = min(valores, key=valores.get)
            partidas.append(
                {
                    "codigo": cod,
                    "nombre": _nombre_partida(cod, lang),
                    "unidad_txt": _unidad_txt(unidad, lang),
                    "mediana_txt": _usd(datos["mediana"][cod]),
                    "mediana_usd": _usd(datos["mediana"][cod], lang),
                    "min_usd": _usd(valores[barato_cc], lang),
                    "max_usd": _usd(valores[caro_cc], lang),
                    "caro": {"cc": caro_cc, "nombre": _nombre_mercado(caro_cc, lang),
                             "usd": valores[caro_cc]},
                    "barato": {"cc": barato_cc, "nombre": _nombre_mercado(barato_cc, lang),
                               "usd": valores[barato_cc]},
                    "cociente": round(valores[caro_cc] / valores[barato_cc], 1)
                    if valores[barato_cc] > 0
                    else 0,
                }
            )
        partidas.sort(key=lambda p: p["cociente"], reverse=True)
    else:
        filas = ranking(lang)
        mayor, menor = filas[0], filas[-1]
        n = len(datos["cesta"])
        n_txt = _miles(n, lang)
        title = (
            "Construction prices in 22 countries, compared"
            if en
            else "Precios de construcción en 22 países, comparados"
        )
        # Descripciones medidas: meta description útil ≤ ~160 caracteres. Se
        # nombra el extremo caro y el barato porque es lo que hace clic.
        description = (
            f"{n_txt} construction items, same code in 22 countries, in USD. "
            f"Index 100 = median. Priciest: {_nombre_en_frase(mayor['cc'], lang)}. "
            f"Cheapest: {_nombre_en_frase(menor['cc'], lang)}."
            if en
            else f"{n_txt} partidas de obra con el mismo código en 22 países, en dólares. "
            f"Índice 100 = mediana internacional. Más caro: {mayor['nombre']}. "
            f"Más barato: {menor['nombre']}."
        )
        h1 = (
            "Construction prices by country: the same works, 22 markets"
            if en
            else "Precios de construcción por país: las mismas obras en 22 mercados"
        )
        ruta = ruta_comparador(lang)
        partidas = partidas_destacadas(10, lang)
        for p in partidas:
            p["nombre"] = _nombre_partida(p["codigo"], lang)
            p["unidad_txt"] = _unidad_txt(p["unidad"], lang)
            p["mediana_txt"] = _usd(p["mediana"], lang)
            p["caro_txt"] = _usd(p["caro"]["usd"], lang)
            p["barato_txt"] = _usd(p["barato"]["usd"], lang)
            p["cociente_txt"] = f"{p['cociente']:.1f}×".replace(".", "," if not en else ".")

    crumbs = [
        ("Home" if en else "Inicio", "/en-us/" if en else "/"),
        ("Price comparison" if en else "Comparador de precios", ruta_comparador(lang)),
    ]
    if codigo_capitulo:
        crumbs.append((nombre_cap, ruta))

    faq = _faq(lang, n, mayor, menor, datos)
    bloques = [
        jsonld_organizacion(request, lang=lang),
        jsonld_website(request, lang=lang),
        jsonld_breadcrumb(request, crumbs),
        jsonld_faq(faq),
    ]

    capitulos = sorted(
        (
            {
                "codigo": c["codigo"],
                "nombre": c["nombre_en"] if en else c["nombre_es"],
                "ruta": ruta_capitulo(lang, c["codigo"]),
                "n": c["n"],
                "indice_mayor": round(max(c["indices"].values()), 1),
                "indice_menor": round(min(c["indices"].values()), 1),
            }
            for c in datos["capitulos"].values()
        ),
        key=lambda c: c["codigo"],
    )

    return {
        "seo": {
            "title": title,
            "description": _limpiar(description),
            "lang": lang,
            "h1": h1,
        },
        "canonical_url": origen + ruta,
        "hreflang_links": [
            {"hreflang": "es", "href": origen + (ruta_capitulo("es", codigo_capitulo) if codigo_capitulo else ruta_comparador("es"))},
            {"hreflang": "en", "href": origen + (ruta_capitulo("en", codigo_capitulo) if codigo_capitulo else ruta_comparador("en"))},
            {
                "hreflang": "x-default",
                "href": origen + (ruta_capitulo("es", codigo_capitulo) if codigo_capitulo else ruta_comparador("es")),
            },
        ],
        "og_image": origen + OG_IMAGE,
        "jsonld_bloques": bloques,
        "crumbs": crumbs,
        "lang": lang,
        "filas": filas[:22] if not codigo_capitulo else filas,
        "mayor": mayor,
        "menor": menor,
        "n_partidas": n,
        "n_partidas_txt": _miles(n, lang),
        "n_mercados": len(datos["mercados"]),
        "capitulos": capitulos,
        "partidas": partidas,
        "faq": faq,
        "tasa_fecha": _fecha_txt(lang),
        "ruta_comparador": ruta_comparador(lang),
        "ruta_capitulo_actual": ruta if codigo_capitulo else "",
        "nombre_capitulo": nombre_cap if codigo_capitulo else "",
        "cesta_capitulos": len(datos["capitulos"]),
    }


def _faq(lang: str, n: int, mayor: dict, menor: dict, datos: dict) -> list[dict]:
    tasa_fecha = datos.get("tasa_fecha") or ""
    if lang == "en":
        return [
            {
                "q": "Are these really the same items in every country?",
                "a": (
                    f"Yes. The comparison only uses the {n} items that share the exact same code "
                    "in all 22 catalogs, so the same work unit is being priced: same definition, "
                    "same unit, same cost structure."
                ),
            },
            {
                "q": "Why is the index in USD and not in local currency?",
                "a": (
                    "Because comparing pesos with euros directly says nothing. Prices are "
                    f"converted to USD with the reference rate dated {tasa_fecha}. If the exchange "
                    "rate of a country moves sharply, its index moves even if construction did not: "
                    "the page shows both dates so the difference is visible."
                ),
            },
            {
                "q": "What does the index mean?",
                "a": (
                    "100 is the international median of the basket. A market at 250 has catalog "
                    f"prices 2.5 times the median. {mayor['nombre']} is the most expensive and "
                    f"{menor['nombre']} the cheapest of the 22."
                ),
            },
            {
                "q": "Is this a cost-of-living index?",
                "a": (
                    "No. It measures the price level of each market's construction catalog, which "
                    "mixes local cost, productivity, exchange rate and the catalog's own pricing "
                    "policy. It is a reference for benchmarking, not an official statistic."
                ),
            },
        ]
    return [
        {
            "q": "¿Son de verdad las mismas partidas en todos los países?",
            "a": (
                f"Sí. La comparación usa solo las {n} partidas que comparten el mismo código "
                "exacto en los 22 catálogos, así que se está comparando la misma unidad de obra: "
                "misma definición, misma unidad y misma estructura de coste."
            ),
        },
        {
            "q": "¿Por qué el índice va en dólares y no en moneda local?",
            "a": (
                "Porque comparar pesos con euros directamente no dice nada. Los precios se pasan "
                f"a USD con la tasa de referencia del {tasa_fecha}. Si el tipo de cambio de un país "
                "se mueve con fuerza, su índice se mueve aunque la obra no haya cambiado: la página "
                "publica las dos fechas para que la diferencia se vea."
            ),
        },
        {
            "q": "¿Qué significa el índice?",
            "a": (
                "100 es la mediana internacional de la cesta. Un mercado con 250 tiene los precios "
                f"del catálogo 2,5 veces por encima de la mediana. {mayor['nombre']} es el más caro "
                f"y {menor['nombre']} el más barato de los 22."
            ),
        },
        {
            "q": "¿Es un índice de coste de vida?",
            "a": (
                "No. Mide el nivel de precios del catálogo de construcción de cada mercado, que "
                "mezcla coste local, productividad, tipo de cambio y la política de precios del "
                "propio catálogo. Es una referencia para comparar, no una estadística oficial."
            ),
        },
    ]


def exportar() -> dict:
    """El comparador como conjunto de datos descargable."""
    datos = _datos()
    mercados = [
        {
            "codigo": cc,
            "nombre": _nombre_mercado(cc, "es"),
            "moneda": (pp.PAISES.get(cc) or {}).get("moneda"),
            "indice": round(datos["indices"][cc], 1),
            "catalogo": "https://cotizat.online" + pp.ruta_indice(cc),
        }
        for cc in datos["mercados"]
    ]
    partidas = []
    for codigo in sorted(datos["cesta"]):
        fila = datos["cesta"][codigo]
        unidad = next(iter(fila.values()))[1]
        partidas.append(
            {
                "codigo": codigo,
                "nombre": _nombre_partida(codigo, "es"),
                "unidad": unidad,
                "mediana_usd": round(datos["mediana"][codigo], 4),
                "precios_usd": {cc: round(valor, 4) for cc, (valor, _u) in sorted(fila.items())},
            }
        )
    return {
        "nombre": "Comparador internacional de precios de construcción",
        "descripcion": (
            f"{len(partidas)} partidas de obra con el mismo código en los 22 mercados, "
            "en dólares y unidad métrica. Índice 100 = mediana internacional."
        ),
        "fecha_tasas": datos.get("tasa_fecha"),
        "base": "USD",
        "licencia": "https://cotizat.online/legal/terminos",
        "autor": {"nombre": "CotizaT", "url": "https://cotizat.online/"},
        "url": "https://cotizat.online" + ruta_comparador("es"),
        "mercados": mercados,
        "partidas": partidas,
    }
