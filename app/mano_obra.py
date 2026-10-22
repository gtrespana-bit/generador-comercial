"""Coste horario de la mano de obra, por país, sacado del catálogo.

La consulta «cuánto cuesta la hora de un albañil / de un electricista» es una
de las más repetidas del sector y no tenía respuesta en el sitio: los precios
unitarios dicen cuánto cuesta un m² de tabique, no cuánto cuesta la hora.

El dato ya existía, pero escondido: cada partida lleva su descompuesto y en él
están las horas de cada oficio con su coste. Este módulo lo agrega:

- Los recursos de mano de obra del catálogo se llaman «Oficial de 1ª albañil»,
  «Journeyman bricklayer», «Craft operative plumber»… El oficio es el nombre
  sin el grado, así que se extrae con una lista corta de prefijos.
- El coste horario es la media de los precios de ese recurso en todo el
  catálogo del país (los rendimientos no entran aquí: es coste, no producción).
- Se cuenta en cuántas partidas aparece, que es lo que permite ordenar la
  tabla por peso real en la obra y no por orden alfabético.

**Lo que este dato no es**: no es una tabla salarial ni una tarifa de venta.
Es el coste horario que el propio catálogo usa para construir sus precios
unitarios (incluye cargas sociales; no incluye beneficio ni facturación). La
página lo dice tal cual, porque publicar un «sueldo» derivado de esto sería
engañoso en los dos sentidos.

Cada país publica un catálogo distinto, con su moneda y sus costes: el dato es
diferencial por mercado y cambia cuando el catálogo cambia. No hay una tabla
de 22 filas escrita a mano que se quede vieja.
"""

from __future__ import annotations

import re
from functools import lru_cache

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
from .services.precios_publicos import _slug

#: Grados que preceden al oficio en el nombre del recurso. Se quitan para
#: agrupar «Oficial de 1ª albañil» y «Oficial de 2ª albañil» en el mismo
#: oficio (el grado ya lo refleja el coste horario).
_GRADOS = (
    r"^Oficial de 1ª\s+",
    r"^Oficial de 2ª\s+",
    r"^Oficial\s+",
    r"^Journeyman\s+",
    r"^Craft operative\s+",
    r"^Apprentice\s+",
)

#: Recursos que son una cuadrilla genérica, no un oficio con nombre. Se
#: conservan porque son la mayoría de las horas del catálogo, pero no se
#: presentan como «el oficio de ayudante de X».
_GENERICOS = frozenset(
    {"ayudante", "helper", "general operative", "skilled operative", "skilled helper",
     "peon", "peón", "laborer", "labourer"}
)


def _oficio(nombre: str) -> str:
    """Nombre del oficio a partir del recurso de mano de obra del catálogo."""
    limpio = " ".join(str(nombre or "").split()).rstrip(".")
    for patron in _GRADOS:
        if re.match(patron, limpio, re.IGNORECASE):
            limpio = re.sub(patron, "", limpio, flags=re.IGNORECASE)
            break
    limpio = limpio.strip(" .")
    return limpio or "Ayudante"


def _titulo(texto: str) -> str:
    """Primera letra en mayúscula, sin tocar el resto (bricklayer → Bricklayer)."""
    return texto[:1].upper() + texto[1:] if texto else texto


def _importe(valor: float, pais: dict) -> str:
    miles = str(pais.get("separador_miles") or ",")
    decimal = str(pais.get("separador_decimal") or ".")
    decimales = 2 if valor < 1000 else 0
    texto = f"{valor:,.{decimales}f}"
    if miles != "," or decimal != ".":
        texto = texto.replace(",", "\x00").replace(".", decimal).replace("\x00", miles)
    return f"{texto} {pais.get('moneda') or ''}".strip()


@lru_cache(maxsize=32)
def oficios(codigo_pais: str) -> tuple[dict, ...]:
    """Oficios del catálogo del país, con su coste horario y su peso en obra.

    Se recorre el catálogo publicado una vez por país/proceso (``lru_cache``):
    la agregación cuesta ~0,3 s y el resultado es inmutable hasta el próximo
    despliegue, que es justo cuando cambia el catálogo.
    """
    cc = str(codigo_pais or "").strip().upper()
    indice = pp._indice(cc)  # noqa: SLF001 — misma casa, dato ya en memoria
    if indice is None:
        return ()
    pais = PAISES.get(cc) or {}
    acumulado: dict[str, dict] = {}
    for (slug_ap, slug_p) in indice["partidas"]:
        detalle = pp.partida(cc, slug_ap, slug_p)
        if not detalle:
            continue
        vistos: set[str] = set()
        for linea in detalle["lineas"]:
            if linea.get("grupo") != "mano_obra":
                continue
            nombre = _oficio(linea.get("nombre") or "")
            clave = nombre.lower()
            datos = acumulado.setdefault(
                clave,
                {
                    "nombre": nombre,
                    "precios": [],
                    "partidas": 0,
                    "capitulos": set(),
                },
            )
            try:
                datos["precios"].append(float(linea.get("precio") or 0))
            except (TypeError, ValueError):
                continue
            if clave not in vistos:
                # Una partida puede llevar dos veces el mismo oficio (oficial
                # y ayudante del mismo nombre): se cuenta una vez por partida
                # para que el peso en la tabla sea comparable.
                vistos.add(clave)
                datos["partidas"] += 1
                capitulo = detalle.get("apartado") or {}
                nombre_capitulo = ""
                if isinstance(capitulo, dict):
                    nombre_capitulo = str(capitulo.get("capitulo") or "")
                if nombre_capitulo:
                    datos["capitulos"].add(nombre_capitulo)
    salida = []
    for datos in acumulado.values():
        precios = [p for p in datos["precios"] if p > 0]
        if not precios:
            continue
        salida.append(
            {
                "nombre": _titulo(datos["nombre"]),
                "slug": _slug(datos["nombre"]),
                "hora": sum(precios) / len(precios),
                "hora_txt": _importe(sum(precios) / len(precios), pais),
                "minima": min(precios),
                "maxima": max(precios),
                "partidas": datos["partidas"],
                "capitulos": sorted(datos["capitulos"]),
                "generico": datos["nombre"].lower() in _GENERICOS,
            }
        )
    # Por peso en la obra: primero los oficios que sostienen más partidas.
    salida.sort(key=lambda o: (-o["partidas"], -o["hora"]))
    for posicion, oficio in enumerate(salida, start=1):
        oficio["posicion"] = posicion
    return tuple(salida)


def ruta_mano_obra(codigo_pais: str) -> str:
    """URL canónica del coste de mano de obra de un mercado."""
    cc = str(codigo_pais or "").strip().upper()
    if (PAISES.get(cc) or {}).get("idioma") == "en":
        return f"/en-{cc.lower()}/labour-rates"
    return f"/{cc.lower()}/mano-de-obra"


def enlaces_precios(codigo_pais: str, limite: int = 6) -> list[dict]:
    """Apartados con más peso de mano de obra, para enlazar desde esta página."""
    from .seo_precios import enlaces_catalogo

    catalogo = enlaces_catalogo(codigo_pais, "mano-de-obra", limite)
    return (catalogo or {}).get("apartados") or []


def contexto_mano_obra(request: Request, codigo_pais: str) -> dict | None:
    """Contexto SEO de la página de coste horario de un mercado."""
    cc = str(codigo_pais or "").strip().upper()
    if cc not in pp.paises_publicados():
        return None
    lista = list(oficios(cc))
    if not lista:
        return None
    pais = PAISES[cc]
    lang = "en" if pais.get("idioma") == "en" else "es"
    en = lang == "en"
    nombre = (pais.get("nombre_en") if en else pais.get("nombre")) or cc
    moneda = str(pais.get("moneda") or "")
    resumen = pp.resumen(cc) or {}
    fecha = resumen.get("fecha_revision") or ""
    try:
        anio, mes_num, _ = str(fecha).split("-")
        meses = (
            ("January", "February", "March", "April", "May", "June", "July",
             "August", "September", "October", "November", "December")
            if en
            else ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
                  "agosto", "septiembre", "octubre", "noviembre", "diciembre")
        )
        mes = f"{meses[int(mes_num) - 1]} {anio}"
    except (ValueError, IndexError):
        mes = ""
    ruta = ruta_mano_obra(cc)
    origen = origen_canonico(request)

    genericos = [o for o in lista if o["generico"]]
    oficios_nombre = [o for o in lista if not o["generico"]]
    mas_caro = max(lista, key=lambda o: o["hora"])
    mas_barato = min(lista, key=lambda o: o["hora"])
    total_partidas = sum(o["partidas"] for o in lista)

    if en:
        title = f"Crew labour rates in {nombre} ({moneda}/hour)"
        description = (
            f"Hourly cost of {len(lista)} trades in {nombre}: "
            f"{mas_caro['nombre']} {mas_caro['hora_txt']}/h, "
            f"{mas_barato['nombre']} {mas_barato['hora_txt']}/h. Taken from the "
            f"published catalog, revised {mes}."
        )
        h1 = f"Construction crew labour rates in {nombre}"
    else:
        title = f"Precio de la mano de obra en {nombre} ({moneda}/hora)"
        description = (
            f"Coste horario de {len(lista)} oficios en {nombre}: "
            f"{mas_caro['nombre']} {mas_caro['hora_txt']}/h, "
            f"{mas_barato['nombre']} {mas_barato['hora_txt']}/h. Sacado del "
            f"catálogo publicado, revisado en {mes}."
        )
        h1 = f"Precio de la mano de obra de construcción en {nombre}"

    crumbs = [
        ("Home" if en else "Inicio", ruta_mercado(cc)),
        ("Construction prices" if en else "Precios de construcción", pp.ruta_indice(cc)),
        ("Labour rates" if en else "Mano de obra", ruta),
    ]

    faq = _faq(pais, lang, nombre, moneda, mes, mas_caro, mas_barato, len(lista))

    bloques = [
        jsonld_organizacion(request, lang=lang),
        jsonld_website(request, lang=lang),
        jsonld_breadcrumb(request, crumbs),
        jsonld_faq(faq),
    ]

    alternates = [
        {
            "cc": otro,
            "hreflang": hreflang_pais(otro),
            "href": origen + ruta_mano_obra(otro),
            "bandera": (PAISES[otro] or {}).get("bandera") or "",
            "nombre": (
                (PAISES[otro] or {}).get("nombre_en")
                if en
                else (PAISES[otro] or {}).get("nombre")
            )
            or otro,
        }
        for otro in sorted(pp.paises_publicados())
        if otro != cc
    ]

    return {
        "seo": {
            "title": title,
            "description": " ".join(description.split())[:155],
            "lang": lang,
            "h1": h1,
        },
        "canonical_url": origen + ruta,
        # Al igual que las páginas de precios, la mano de obra se ofrece en
        # los 22 mercados: cada versión declara las demás para que Google no
        # las trate como duplicados entre países.
        "hreflang_links": [
            {"hreflang": hreflang_pais(otro), "href": origen + ruta_mano_obra(otro)}
            for otro in sorted(pp.paises_publicados())
        ]
        + [
            {
                "hreflang": "x-default",
                "href": origen
                + ruta_mano_obra("US" if "US" in pp.paises_publicados() else cc),
            }
        ],
        "og_image": origen + OG_IMAGE,
        "jsonld_bloques": bloques,
        "crumbs": crumbs,
        "pais": pais,
        "lang": lang,
        "oficios": lista,
        "oficios_nombre": oficios_nombre,
        "genericos": genericos,
        "n_oficios": len(lista),
        "mas_caro": mas_caro,
        "mas_barato": mas_barato,
        "total_partidas": total_partidas,
        "mes": mes,
        "moneda": moneda,
        "nombre_pais": nombre,
        "faq": faq,
        "ruta_indice": pp.ruta_indice(cc),
        "ruta_pais": ruta_mercado(cc),
        "ruta_json": pp.ruta_json(cc),
        "ruta_calculadora": f"/en/calculadora?cc={cc}" if en else f"/calculadora?cc={cc}",
        "ruta_comparador": f"/en/prices-comparison" if en else "/precios-comparados",
        "enlaces_precios": enlaces_precios(cc),
        "alternates": alternates,
    }


def _faq(
    pais: dict,
    lang: str,
    nombre: str,
    moneda: str,
    mes: str,
    mas_caro: dict,
    mas_barato: dict,
    n: int,
) -> list[dict]:
    en = lang == "en"
    etiqueta = (
        (pais.get("etiqueta_impuesto_en") if en else pais.get("etiqueta_impuesto"))
        or "VAT"
    )
    if en:
        return [
            {
                "q": f"How much does a construction crew hour cost in {nombre}?",
                "a": (
                    f"The catalog prices {n} trades. The most expensive hour is "
                    f"{mas_caro['nombre']} at {mas_caro['hora_txt']}, and the "
                    f"cheapest is {mas_barato['nombre']} at {mas_barato['hora_txt']}. "
                    f"Figures revised {mes}."
                ),
            },
            {
                "q": "Is this a wage table?",
                "a": (
                    "No. It is the hourly cost the catalog uses to build its unit "
                    "prices: it includes the crew's cost to the contractor, not "
                    "what a worker takes home, and it excludes your margin. To "
                    "pass this cost on you still have to add indirect costs and "
                    "profit."
                ),
            },
            {
                "q": f"Does this cost include {etiqueta}?",
                "a": (
                    f"No. {etiqueta} is applied on the taxable base when you "
                    "build the estimate, on top of the cost price."
                ),
            },
            {
                "q": "Why do several trades show the same hourly cost?",
                "a": (
                    "Because in this market the catalog uses the same reference "
                    "rate for several trades at the same level. Where the rates "
                    "differ is in the crew yield: a bricklayer and a painter can "
                    "cost the same per hour and produce very different amounts of "
                    "work per day, which is what changes the unit price."
                ),
            },
        ]
    return [
        {
            "q": f"¿Cuánto cuesta la hora de una cuadrilla en {nombre}?",
            "a": (
                f"El catálogo publica {n} oficios. La hora más cara es de "
                f"{mas_caro['nombre']}, a {mas_caro['hora_txt']}, y la más barata "
                f"es la de {mas_barato['nombre']}, a {mas_barato['hora_txt']}. "
                f"Cifras revisadas en {mes}."
            ),
        },
        {
            "q": "¿Es esto una tabla de salarios?",
            "a": (
                "No. Es el coste horario que el catálogo usa para construir sus "
                "precios unitarios: incluye el coste de la cuadrilla para la "
                "empresa, no lo que cobra el trabajador, y no incluye tu "
                "beneficio. Para pasarlo a un presupuesto todavía hay que añadir "
                "costes indirectos y margen."
            ),
        },
        {
            "q": f"¿Este coste incluye {etiqueta}?",
            "a": (
                f"No. {etiqueta} se aplica sobre la base imponible al "
                "presupuestar, por encima del precio de coste."
            ),
        },
        {
            "q": "¿Por qué varios oficios salen con el mismo coste horario?",
            "a": (
                "Porque en este mercado el catálogo usa la misma tarifa de "
                "referencia para varios oficios del mismo nivel. Donde cambia el "
                "resultado es en el rendimiento: un albañil y un pintor pueden "
                "costar lo mismo por hora y producir cantidades de obra muy "
                "distintas al día, que es lo que mueve el precio unitario."
            ),
        },
    ]
