"""SEO público: canónicas, hreflang, copy por país y páginas de intención.

Un solo origen HTTPS (``COTIZAT_PUBLIC_URL``) alimenta canónicas, Open Graph,
sitemap y robots. Las landings de país viven en ``/co/``, ``/mx/``…; las
páginas de intención (software de presupuestos, APU, remodelación) tienen
URL y texto propios para no competir entre sí ni duplicar la home.

La raíz ``/`` es siempre genérica LatAm: la cookie de país no cambia su
HTML. Google indexa una URL, un contenido.
"""
from __future__ import annotations

from urllib.parse import urlparse

from fastapi import Request

from .branding import PRODUCT_NAME, VALUE_PROPOSITION
from .paises import ORDEN_SELECTOR, PAISES, PAIS_GENERICO, lista_paises

OG_IMAGE = "/static/og-cotizat.png"
SITEMAP_LASTMOD = "2026-08-21"

# Temas con URL propia. Cada uno apunta a una intención de búsqueda distinta.
TEMAS = ("software-presupuestos", "apu", "remodelacion")

# Rutas que Google SÍ debe indexar. El resto lleva X-Robots-Tag noindex.
# Se usa también para robots.txt.
_INDEXABLES_EXACTAS = frozenset(
    {
        "/",
        "/como-funciona",
        "/pago",
        "/conocer",
        "/sitemap.xml",
        "/robots.txt",
        "/favicon.ico",
        "/software-presupuestos",
        "/apu",
        "/remodelacion",
    }
)


def origen_canonico(request: Request | None = None) -> str:
    """Origen HTTPS público, nunca el Host de un preview.

    Si ``COTIZAT_PUBLIC_URL`` no está (tests, escritorio), cae al ``base_url``
    de la petición. Nunca inventa un dominio.
    """
    try:
        from .auth import public_app_url

        return public_app_url("/").rstrip("/")
    except Exception:
        if request is not None:
            return str(request.base_url).rstrip("/")
        return "https://cotizat.online"


def url_publica(path: str, request: Request | None = None) -> str:
    """URL absoluta de una ruta pública (siempre con origen canónico)."""
    ruta = str(path or "/")
    if not ruta.startswith("/"):
        ruta = "/" + ruta
    return origen_canonico(request) + ruta


def es_indexable(path: str) -> bool:
    """¿Esta ruta debe aparecer en buscadores?

    Indexamos landings, páginas de intención, legales, planes y estáticos.
    El panel, el login, las propuestas y los archivos privados no.
    """
    p = str(path or "")
    if p in _INDEXABLES_EXACTAS:
        return True
    if p.startswith("/legal/") and p.count("/") == 2:
        return True
    if p.startswith("/static/"):
        return True
    partes = [seg for seg in p.split("/") if seg]
    if not partes:
        return True
    cc = partes[0].lower()
    if cc in {c.lower() for c in ORDEN_SELECTOR}:
        if len(partes) == 1:
            return True
        if len(partes) == 2 and partes[1] in TEMAS:
            return True
        return False
    return False


def hreflang_pais(codigo: str) -> str:
    codigo = str(codigo or "").strip().upper()
    return f"es-{codigo}" if codigo in PAISES else "es"


def ruta_pais(codigo: str, tema: str = "") -> str:
    codigo = str(codigo or "").strip().lower()
    if not codigo:
        return f"/{tema}" if tema else "/"
    if tema:
        return f"/{codigo}/{tema}"
    return f"/{codigo}/"


def enlaces_hreflang(request: Request | None = None, tema: str = "") -> list[dict]:
    """Pares hreflang para una página (home o tema) y sus equivalentes de país."""
    base = origen_canonico(request)
    out = [
        {"hreflang": "x-default", "href": base + ruta_pais("", tema)},
        {"hreflang": "es", "href": base + ruta_pais("", tema)},
    ]
    for pais in lista_paises():
        out.append(
            {
                "hreflang": hreflang_pais(pais["codigo"]),
                "href": base + ruta_pais(pais["codigo"], tema),
            }
        )
    return out


# ---------------------------------------------------------------------------
# Copy de la landing por país (title ≤ 60, description ≈ 155, H1 único)
# ---------------------------------------------------------------------------

_LANDING: dict[str, dict] = {
    "": {
        "title": "CotizaT | Software de presupuestos de construcción LatAm",
        "description": (
            "Software de presupuestos de construcción y remodelación para "
            "Latinoamérica. Catálogo con APU, margen, tiempos de cuadrilla y "
            "PDF profesional. 7 días gratis, sin tarjeta."
        ),
        "h1": "Software de presupuestos de construcción para Latinoamérica",
        "h1_resalte": "margen, tiempos y cierre",
        "sub": (
            "CotizaT convierte tu catálogo y tus precios en presupuestos de obra "
            "claros, con coste interno, beneficio y horas de cuadrilla. PDF con "
            "tu logo, listo para WhatsApp. Venezuela, Colombia, México, Ecuador y Perú."
        ),
        "kicker": "Sistema comercial para Latinoamérica · Construcción y remodelación",
        "faq": [
            {
                "q": "¿CotizaT sirve para presupuestos de construcción en Latinoamérica?",
                "a": (
                    "Sí. Está hecho para constructoras pequeñas, remodeladores y "
                    "contratistas de Venezuela, Colombia, México, Ecuador y Perú. "
                    "Configuras moneda, IVA e ID fiscal (RIF, NIT, RFC, RUC) al registrarte."
                ),
            },
            {
                "q": "¿Incluye análisis de precios unitarios (APU)?",
                "a": (
                    "Sí. Cada partida del catálogo llega descompuesta en materiales, "
                    "mano de obra y equipo, con rendimiento y precio. Cambias un "
                    "recurso y se recalculan las partidas que lo usan."
                ),
            },
            {
                "q": "¿El cliente tiene que registrarse?",
                "a": (
                    "No. Envías el PDF por WhatsApp o email como ya haces. El "
                    "enlace privado con firma es opcional."
                ),
            },
            {
                "q": "¿Emite facturas fiscales?",
                "a": (
                    "No. Los documentos son comerciales y no sustituyen una factura "
                    "fiscal de tu país. Lo dicen el PDF y los términos."
                ),
            },
        ],
    },
    "VE": {
        "title": "CotizaT | Presupuestos de construcción en Venezuela",
        "description": (
            "Software para presupuestos de obra y remodelación en Venezuela. "
            "Catálogo en USD o Bs, RIF, IVA 16 % y PDF profesional. Prueba 7 "
            "días gratis, sin tarjeta."
        ),
        "h1": "Software de presupuestos de construcción para Venezuela",
        "h1_resalte": "USD o bolívares, con tu margen",
        "sub": (
            "Arma presupuestos de remodelación y obra privada con concreto, friso, "
            "cielo raso y plomería, en USD o Bs, con tasa congelada y RIF. Ves "
            "coste, beneficio y horas de cuadrilla antes de enviar el PDF por WhatsApp."
        ),
        "kicker": "🇻🇪 Sistema comercial para Venezuela · Construcción y remodelación",
        "faq": [
            {
                "q": "¿Puedo cotizar en dólares y mostrar equivalente en bolívares?",
                "a": (
                    "Sí. Cada presupuesto congela su moneda y su tasa de referencia. "
                    "Un PDF antiguo no cambia si mañana se mueve el tipo de cambio."
                ),
            },
            {
                "q": "¿El catálogo habla venezolano?",
                "a": (
                    "Sí: concreto, friso, cielo raso, rodapié, plomero. No es una "
                    "traducción de un software español o mexicano."
                ),
            },
            {
                "q": "¿Cómo se paga desde Venezuela?",
                "a": (
                    "Pago móvil, Binance, Kontigo, USDT o tarjeta. El plan anual "
                    "de lanzamiento es 89 US$."
                ),
            },
            {
                "q": "¿Sustituye la factura fiscal venezolana?",
                "a": (
                    "No. Genera presupuestos y documentos de cobro comerciales. "
                    "La factura fiscal la emites por el medio que te corresponda."
                ),
            },
        ],
    },
    "CO": {
        "title": "CotizaT | Software de presupuestos y APU en Colombia",
        "description": (
            "Software de presupuestos de construcción y APU para Colombia. "
            "NIT, IVA 19 %, COP o USD, pañete y concreto. PDF profesional. "
            "7 días gratis, sin tarjeta."
        ),
        "h1": "Software de presupuestos y APU para constructoras en Colombia",
        "h1_resalte": "análisis de precios unitarios editable",
        "sub": (
            "Presupuesta obra y remodelación en COP o USD, con NIT e IVA 19 %. "
            "Cada partida trae APU real: materiales, mano de obra y equipo. "
            "Terminología colombiana (pañete, andén, sardinel) y PDF listo para WhatsApp."
        ),
        "kicker": "🇨🇴 Sistema comercial para Colombia · Construcción y remodelación",
        "faq": [
            {
                "q": "¿CotizaT calcula APU para Colombia?",
                "a": (
                    "Sí. El catálogo incluye análisis de precios unitarios con "
                    "rendimiento y precio por recurso. Editas el cemento o la hora "
                    "del oficial y se recalcula el presupuesto en COP."
                ),
            },
            {
                "q": "¿Sirve para una SAS de remodelación en Bogotá o Medellín?",
                "a": (
                    "Está pensado para empresas de 2 a 15 personas que hoy cotizan "
                    "en Excel. NIT, IVA 19 % y moneda COP se configuran al registrarte."
                ),
            },
            {
                "q": "¿El cliente tiene que entrar a una plataforma?",
                "a": (
                    "No. Envías el PDF por WhatsApp. El enlace privado es opcional."
                ),
            },
            {
                "q": "¿Emite factura electrónica DIAN?",
                "a": (
                    "No. Los documentos son comerciales. La factura electrónica la "
                    "emites con tu proveedor autorizado."
                ),
            },
        ],
    },
    "MX": {
        "title": "CotizaT | Software para presupuestos de obra en México",
        "description": (
            "Programa para presupuestos de construcción y remodelación en México. "
            "RFC, IVA 16 %, MXN, aplanado y plafón. Catálogo con APU. "
            "7 días gratis, sin tarjeta."
        ),
        "h1": "Software para presupuestos de obra y remodelación en México",
        "h1_resalte": "cotiza en pesos, con tu margen",
        "sub": (
            "Cotiza remodelación y obra privada en MXN o USD, con RFC e IVA 16 %. "
            "Catálogo con análisis de precios unitarios, aplanado, plafón, zoclo y "
            "plomería. PDF con tu logo para WhatsApp o correo."
        ),
        "kicker": "🇲🇽 Sistema comercial para México · Construcción y remodelación",
        "faq": [
            {
                "q": "¿Puedo cotizar en pesos mexicanos?",
                "a": (
                    "Sí. El espacio nace en MXN e IVA 16 %. También puedes emitir "
                    "en USD. Cada presupuesto congela su tasa."
                ),
            },
            {
                "q": "¿El catálogo usa términos de México?",
                "a": (
                    "Sí: concreto, aplanado, plafón, zoclo, plomero, banqueta. "
                    "No verás friso ni cielo raso venezolano."
                ),
            },
            {
                "q": "¿Sustituye el CFDI?",
                "a": (
                    "No. CotizaT no emite facturas fiscales. El presupuesto es un "
                    "documento comercial; el CFDI lo emites por tu medio habitual."
                ),
            },
            {
                "q": "¿Cuánto cuesta?",
                "a": (
                    "89 US$ al año de lanzamiento (habitual 109) o 9,99 US$ al mes "
                    "el primer año. 7 días de prueba sin tarjeta."
                ),
            },
        ],
    },
    "PE": {
        "title": "CotizaT | Presupuestos de obra y metrados en Perú",
        "description": (
            "Software de presupuestos de construcción para Perú. RUC, IGV 18 %, "
            "soles, tarrajeo y metrados con APU. PDF profesional. 7 días gratis, "
            "sin tarjeta."
        ),
        "h1": "Software de presupuestos de obra y metrados para Perú",
        "h1_resalte": "APU, IGV y soles",
        "sub": (
            "Arma presupuestos y metrados de remodelación en soles o USD, con RUC "
            "e IGV 18 %. Catálogo con análisis de precios unitarios, tarrajeo, "
            "cielo raso y gasfitería. PDF listo para WhatsApp."
        ),
        "kicker": "🇵🇪 Sistema comercial para Perú · Construcción y remodelación",
        "faq": [
            {
                "q": "¿Sirve para metrados y APU en Perú?",
                "a": (
                    "Sí. Presupuestas por partidas con cantidades (metrados) y cada "
                    "partida trae APU editable: materiales, mano de obra y equipo."
                ),
            },
            {
                "q": "¿El IGV se calcula solo?",
                "a": (
                    "Configuras 18 % (o el que apliques) y el documento lo calcula. "
                    "No es asesoramiento tributario: la alícuota la pones tú."
                ),
            },
            {
                "q": "¿Habla peruano?",
                "a": (
                    "Tarrajeo, cielo raso, zócalo, gasfitero, vereda. El catálogo "
                    "se muestra con la terminología de Perú."
                ),
            },
            {
                "q": "¿Emite comprobante SUNAT?",
                "a": (
                    "No. Genera presupuestos comerciales. El comprobante de pago "
                    "lo emites con tu sistema autorizado."
                ),
            },
        ],
    },
    "EC": {
        "title": "CotizaT | Software de presupuestos y APU en Ecuador",
        "description": (
            "Software de presupuestos de construcción para Ecuador. RUC, IVA 15 %, "
            "USD, enlucido y tumbado. Catálogo con APU. 7 días gratis, sin tarjeta."
        ),
        "h1": "Software de presupuestos y APU para construcción en Ecuador",
        "h1_resalte": "dólares, RUC e IVA 15 %",
        "sub": (
            "Presupuesta obra y remodelación en USD, con RUC e IVA 15 %. Catálogo "
            "con análisis de precios unitarios, hormigón, enlucido, tumbado y "
            "gasfitería. PDF profesional para WhatsApp."
        ),
        "kicker": "🇪🇨 Sistema comercial para Ecuador · Construcción y remodelación",
        "faq": [
            {
                "q": "¿Está pensado para constructoras en Ecuador?",
                "a": (
                    "Sí. El espacio nace en USD, IVA 15 % y RUC. Terminología "
                    "local: hormigón, enlucido, tumbado, barredera, gasfitero."
                ),
            },
            {
                "q": "¿Incluye APU?",
                "a": (
                    "Cada partida llega descompuesta en recursos con rendimiento y "
                    "precio. Editas un insumo y se recalcula el presupuesto."
                ),
            },
            {
                "q": "¿El cliente firma en línea?",
                "a": (
                    "Puedes enviar un enlace privado opcional. Lo habitual es el "
                    "PDF por WhatsApp, que es como ya cierras."
                ),
            },
            {
                "q": "¿Emite factura del SRI?",
                "a": (
                    "No. Los documentos son comerciales y no sustituyen la factura "
                    "electrónica que te exija el SRI."
                ),
            },
        ],
    },
}


def ficha_landing(codigo: str = "") -> dict:
    """Copy SEO de la landing (genérica o de un país del selector)."""
    codigo = str(codigo or "").strip().upper()
    base = _LANDING.get(codigo) or _LANDING[""]
    pais = PAISES.get(codigo) or PAIS_GENERICO
    return {
        **base,
        "codigo": codigo,
        "lang": hreflang_pais(codigo) if codigo else "es",
        "nombre_pais": pais.get("nombre") or "Latinoamérica",
        "tema": "",
        "canonical_path": ruta_pais(codigo),
    }


# ---------------------------------------------------------------------------
# Páginas de intención: texto único por (país, tema)
# ---------------------------------------------------------------------------

def _bloques_tema(codigo: str, tema: str) -> dict:
    pais = PAISES.get(codigo) or PAIS_GENERICO
    nombre = pais.get("nombre") or "Latinoamérica"
    moneda = pais.get("moneda") or "USD"
    iva = pais.get("iva")
    fiscal = pais.get("id_fiscal") or "ID fiscal"
    vocab = pais.get("vocab") or ""
    ciudad = pais.get("ciudad_ejemplo") or ""

    if tema == "software-presupuestos":
        title = f"Software de presupuestos de construcción en {nombre} | CotizaT"
        if not codigo:
            title = "Software de presupuestos de construcción LatAm | CotizaT"
        h1 = f"Software de presupuestos de construcción en {nombre}"
        lead = (
            f"CotizaT es el software de presupuestos de construcción y remodelación "
            f"para empresas de {nombre}. Catálogo con análisis de precios unitarios, "
            f"{fiscal}, IVA {iva} % y moneda {moneda}. PDF profesional para WhatsApp."
        )
        body = [
            (
                "Qué resuelve",
                f"La mayoría de constructoras pequeñas en {nombre} sigue presupuestando "
                "en Excel o Word. Los precios viven en la cabeza de una persona, el "
                "cliente pide dos cambios y hay que rehacer el documento, y nadie "
                "recuerda qué versión se aprobó. CotizaT guarda tu catálogo, arma el "
                "presupuesto por capítulos y genera un PDF con tu logo.",
            ),
            (
                "Para quién es",
                f"Remodeladores, contratistas y constructoras de 2 a 15 personas en "
                f"{nombre} que hacen varios presupuestos al mes. No es un ERP de obra "
                "pública ni un visor BIM. Es el flujo comercial: cotizar, revisar margen, "
                "enviar y reenviar cambios.",
            ),
            (
                "Qué incluye el primer día",
                "Más de 3.000 partidas descompuestas y cientos de recursos con precio. "
                f"Terminología de {nombre}: {vocab}. Packs de estancia (baño, cocina) "
                "escalados a los m². Importación desde Excel o CYPE.",
            ),
            (
                "Precio",
                "89 US$ al año de lanzamiento (habitual 109) o 9,99 US$ al mes el "
                "primer año. 7 días de prueba completa, sin tarjeta. Sin permanencia.",
            ),
        ]
        description = (
            f"Software de presupuestos de construcción para {nombre}. Catálogo con "
            f"APU, {fiscal}, IVA {iva} % y PDF profesional. 7 días gratis."
        )
        related = [
            ("Análisis de precios unitarios (APU)", ruta_pais(codigo, "apu")),
            ("Presupuestos de remodelación", ruta_pais(codigo, "remodelacion")),
        ]
    elif tema == "apu":
        title = f"Software de APU y análisis de precios unitarios en {nombre} | CotizaT"
        if not codigo:
            title = "Software de APU y análisis de precios unitarios | CotizaT"
        h1 = f"Análisis de precios unitarios (APU) para {nombre}"
        lead = (
            f"CotizaT no es una lista de precios plana. Cada partida llega con APU: "
            f"materiales, mano de obra y equipo, rendimiento y precio, listos para "
            f"editar en {moneda}."
        )
        body = [
            (
                "Qué es un APU en CotizaT",
                "Un análisis de precios unitarios descompone el precio de una partida "
                "en recursos: kilos de cemento, horas de oficial, horas de equipo. "
                "El importe de cada línea es rendimiento × precio unitario. Los "
                "porcentajes de costes directos complementarios se calculan sobre esa base.",
            ),
            (
                f"Por qué importa en {nombre}",
                f"Sin APU cotizas a ciegas: no sabes si el baño de {ciudad or nombre} "
                "te deja 30 % o 8 %. Con APU ves el coste interno, el beneficio y las "
                "horas de cuadrilla antes de enviar. El cliente no ve esos números en el PDF.",
            ),
            (
                "Precios en cascada",
                "Subes el cemento o la hora del oficial una sola vez en Recursos. "
                "Todas las partidas que lo usan se recalculan. Los presupuestos ya "
                "enviados no se tocan: cada versión queda congelada.",
            ),
            (
                "CYPE y Excel",
                "Si ya trabajas con descompuestos CYPE, importas el .xlsx y se "
                "clasifica materiales, mano de obra y complementarios, sin perder filas "
                "ni fórmulas. También pegas TSV desde Excel.",
            ),
        ]
        description = (
            f"Software de APU para {nombre}: análisis de precios unitarios editable, "
            f"rendimientos y precios en cascada. Catálogo propio. 7 días gratis."
        )
        related = [
            ("Software de presupuestos", ruta_pais(codigo, "software-presupuestos")),
            ("Presupuestos de remodelación", ruta_pais(codigo, "remodelacion")),
        ]
    else:  # remodelacion
        title = f"Software de presupuestos de remodelación en {nombre} | CotizaT"
        if not codigo:
            title = "Software de presupuestos de remodelación | CotizaT"
        h1 = f"Presupuestos de remodelación para {nombre}"
        lead = (
            f"Arma el presupuesto de un baño, una cocina o una vivienda completa en "
            f"{nombre} con packs de estancia, productos con foto y un PDF que se "
            f"puede reenviar cuando el cliente pide cambios."
        )
        body = [
            (
                "El flujo real de una reforma",
                "Preparas el presupuesto, lo envías por WhatsApp, el cliente llama, "
                "pide quitar el porcelanato y poner cerámica. En CotizaT editas, se "
                "crea una versión nueva y copias un resumen: total anterior, total "
                "nuevo y qué cambió.",
            ),
            (
                "Packs de estancia",
                "Un baño o una cocina no debería llevar 40 minutos de buscar partidas. "
                "El pack inserta el capítulo completo, escalado a los m² reales. Las "
                "piezas fijas (inodoro, mueble) no se multiplican.",
            ),
            (
                "Opciones para el cliente",
                "Productos incluidos, opcionales o alternativos, con foto. El "
                "presupuesto marca qué se aprobó. Tú no reescribes el documento desde cero.",
            ),
            (
                f"Fiscalidad de {nombre}",
                f"{fiscal}, IVA {iva} %, moneda {moneda}. Los documentos son "
                "comerciales: no son factura fiscal. Lo decimos en el PDF y en los términos.",
            ),
        ]
        description = (
            f"Software para presupuestos de remodelación en {nombre}. Packs de "
            f"estancia, PDF profesional y cambios claros. 7 días gratis."
        )
        related = [
            ("Software de presupuestos", ruta_pais(codigo, "software-presupuestos")),
            ("Análisis de precios unitarios", ruta_pais(codigo, "apu")),
        ]

    faq = [
        {
            "q": f"¿CotizaT sirve para {nombre}?",
            "a": (
                f"Sí. Al registrarte eliges {nombre} y el espacio nace con "
                f"{fiscal}, IVA {iva} % y moneda {moneda}."
            ),
        },
        {
            "q": "¿Puedo probarlo sin pagar?",
            "a": "7 días de acceso completo, sin tarjeta. Una prueba por correo.",
        },
        {
            "q": "¿Cuánto cuesta después?",
            "a": "89 US$ al año de lanzamiento o 9,99 US$ al mes el primer año. Sin permanencia.",
        },
    ]
    return {
        "title": title[:70],
        "description": description[:170],
        "h1": h1,
        "lead": lead,
        "body": body,
        "faq": faq,
        "related": related,
        "codigo": codigo,
        "lang": hreflang_pais(codigo) if codigo else "es",
        "nombre_pais": nombre,
        "tema": tema,
        "canonical_path": ruta_pais(codigo, tema),
        "vocab": vocab,
        "moneda": moneda,
        "iva": iva,
        "id_fiscal": fiscal,
    }


def ficha_tema(codigo: str, tema: str) -> dict | None:
    codigo = str(codigo or "").strip().upper()
    tema = str(tema or "").strip().lower()
    if tema not in TEMAS:
        return None
    if codigo and codigo not in ORDEN_SELECTOR:
        return None
    return _bloques_tema(codigo, tema)


def jsonld_software(request: Request | None = None, codigo: str = "") -> dict:
    origen = origen_canonico(request)
    pais = PAISES.get(str(codigo or "").upper())
    area = {
        "@type": "Country",
        "name": pais["nombre"] if pais else "Latinoamérica",
    }
    return {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": PRODUCT_NAME,
        "applicationCategory": "BusinessApplication",
        "operatingSystem": "Web",
        "description": VALUE_PROPOSITION,
        "url": origen + ruta_pais(codigo),
        "image": origen + OG_IMAGE,
        "offers": {
            "@type": "Offer",
            "price": "89.00",
            "priceCurrency": "USD",
            "availability": "https://schema.org/InStock",
            "url": origen + "/pago",
        },
        "areaServed": area,
        "inLanguage": hreflang_pais(codigo) if codigo else "es",
        "brand": {"@type": "Brand", "name": PRODUCT_NAME},
    }


def jsonld_faq(preguntas: list[dict]) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": item["q"],
                "acceptedAnswer": {"@type": "Answer", "text": item["a"]},
            }
            for item in preguntas
        ],
    }


def jsonld_breadcrumb(request: Request | None, items: list[tuple[str, str]]) -> dict:
    origen = origen_canonico(request)
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i,
                "name": nombre,
                "item": origen + ruta,
            }
            for i, (nombre, ruta) in enumerate(items, start=1)
        ],
    }


def contexto_seo(
    request: Request,
    *,
    codigo: str = "",
    tema: str = "",
) -> dict:
    """Contexto Jinja común: canónica, hreflang, OG y JSON-LD."""
    codigo = str(codigo or "").strip().upper()
    tema = str(tema or "").strip().lower()
    ficha = ficha_tema(codigo, tema) if tema else ficha_landing(codigo)
    if ficha is None:
        ficha = ficha_landing(codigo)
    origen = origen_canonico(request)
    canonical = origen + ficha["canonical_path"]
    og_image = origen + OG_IMAGE
    bloques_ld = [jsonld_software(request, codigo)]
    if ficha.get("faq"):
        bloques_ld.append(jsonld_faq(ficha["faq"]))
    crumbs = [("Inicio", "/")]
    if codigo:
        crumbs.append((ficha["nombre_pais"], ruta_pais(codigo)))
    if tema:
        crumbs.append((ficha["h1"], ficha["canonical_path"]))
    bloques_ld.append(jsonld_breadcrumb(request, crumbs))
    return {
        "seo": ficha,
        "origen_seo": origen,
        "canonical_url": canonical,
        "hreflang_links": enlaces_hreflang(request, tema),
        "og_image": og_image,
        "jsonld_bloques": bloques_ld,
        "seo_temas": TEMAS,
    }


def urls_sitemap(request: Request | None = None) -> list[dict]:
    """Entradas del sitemap: loc, lastmod, changefreq, priority, xhtml hreflang."""
    base = origen_canonico(request)
    out: list[dict] = []

    def add(path: str, priority: str, changefreq: str, tema: str = "") -> None:
        loc = base + path
        alts = enlaces_hreflang(request, tema) if (
            path == "/" or path.endswith("/") or any(path.endswith("/" + t) or path == f"/{t}" for t in TEMAS)
        ) else []
        # hreflang solo en home de país/genérica y en páginas de tema
        usar_alts = (
            path in {"/", "/software-presupuestos", "/apu", "/remodelacion"}
            or any(path == ruta_pais(c) for c in ORDEN_SELECTOR)
            or any(path == ruta_pais(c, t) for c in ORDEN_SELECTOR for t in TEMAS)
        )
        out.append(
            {
                "loc": loc,
                "lastmod": SITEMAP_LASTMOD,
                "changefreq": changefreq,
                "priority": priority,
                "alternates": alts if usar_alts else [],
            }
        )

    add("/", "1.0", "weekly")
    for codigo in ORDEN_SELECTOR:
        add(ruta_pais(codigo), "0.9", "weekly")
    for tema in TEMAS:
        add(ruta_pais("", tema), "0.8", "monthly", tema)
        for codigo in ORDEN_SELECTOR:
            add(ruta_pais(codigo, tema), "0.8", "monthly", tema)
    add("/como-funciona", "0.7", "monthly")
    add("/pago", "0.6", "monthly")
    for legal in ("preguntas", "terminos", "privacidad", "soporte", "licencias"):
        add(f"/legal/{legal}", "0.3", "yearly")
    return out


def robots_txt(request: Request | None = None) -> str:
    origen = origen_canonico(request)
    lineas = [
        "User-agent: *",
        "Allow: /",
        "Allow: /static/",
        "Disallow: /acceso",
        "Disallow: /registro",
        "Disallow: /recuperar-acceso",
        "Disallow: /restablecer-clave",
        "Disallow: /inicio",
        "Disallow: /cuenta",
        "Disallow: /presupuestos",
        "Disallow: /partidas",
        "Disallow: /recursos",
        "Disallow: /clientes",
        "Disallow: /productos",
        "Disallow: /proyectos",
        "Disallow: /facturas",
        "Disallow: /plantillas",
        "Disallow: /recetas",
        "Disallow: /reportes",
        "Disallow: /buscar",
        "Disallow: /configuracion",
        "Disallow: /equipo",
        "Disallow: /organizaciones",
        "Disallow: /admin",
        "Disallow: /bienvenida",
        "Disallow: /pago/comprar",
        "Disallow: /pago/elegir",
        "Disallow: /pago/stripe",
        "Disallow: /propuestas",
        "Disallow: /invitaciones",
        "Disallow: /archivos",
        "Disallow: /api/",
        "Disallow: /demo",
        "",
        f"Sitemap: {origen}/sitemap.xml",
        "",
    ]
    return "\n".join(lineas)


def host_publico_valido(host: str) -> bool:
    """True si el Host coincide con COTIZAT_PUBLIC_URL (para diagnóstico)."""
    try:
        publico = origen_canonico()
    except Exception:
        return False
    netloc = urlparse(publico).netloc.lower()
    return bool(netloc) and host.lower().split(":")[0] == netloc.split(":")[0]
