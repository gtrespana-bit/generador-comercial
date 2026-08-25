"""SEO público: canónicas, hreflang, copy por país y páginas de intención.

Un solo origen HTTPS (``COTIZAT_PUBLIC_URL``) alimenta canónicas, Open Graph,
sitemap y robots. Las landings de país viven en ``/co/``, ``/mx/``…; las
páginas de intención (software de presupuestos, APU, remodelación) tienen
URL y texto propios para no competir entre sí ni duplicar la home.

La raíz ``/`` es siempre genérica LatAm: la cookie de país no cambia su
HTML. Google indexa una URL, un contenido.
"""
from __future__ import annotations

import re
from urllib.parse import urlparse

from fastapi import Request

from .branding import PRODUCT_NAME, VALUE_PROPOSITION
from .paises import ORDEN_SELECTOR, PAISES, PAIS_GENERICO, lista_paises

OG_IMAGE = "/static/og-cotizat.png"
SITEMAP_LASTMOD = "2026-08-25"

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
        "/mapa-del-sitio",
        "/guia/presupuesto-de-obra",
        "/guia/analisis-precios-unitarios",
        "/guia/presupuesto-remodelacion",
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
    if p.startswith("/guia/") and p.count("/") == 2:
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


def _dias_prueba_publicos() -> int | None:
    """Días de prueba vigentes, o None si está apagada.

    Las metas y el FAQ no pueden clavar «7 días»: si el titular pone 14 o 0,
    un anuncio fijo sería publicidad falsa (lo comprueba test_prueba_gratuita).
    """
    try:
        from .services.prueba_gratuita import dias_de_prueba, prueba_activada

        if not prueba_activada():
            return None
        return int(dias_de_prueba())
    except Exception:
        return None


_RE_PRUEBA = re.compile(
    r"(?:\s*[,.]?\s*)?(?:\d+\s+días(?:\s+de\s+prueba)?(?:\s+gratis)?(?:\s*,?\s*sin tarjeta)?\.?)",
    re.IGNORECASE,
)


def _aplicar_prueba(ficha: dict) -> dict:
    """Ajusta description y FAQ al estado real de la prueba."""
    n = _dias_prueba_publicos()
    desc = _RE_PRUEBA.sub("", str(ficha.get("description") or "")).strip()
    desc = re.sub(r"\s{2,}", " ", desc).rstrip(" .")
    if n:
        desc = f"{desc}. {n} días gratis, sin tarjeta."
    else:
        desc = desc + "."
    ficha["description"] = desc[:170]

    faqs = []
    for item in ficha.get("faq") or []:
        q = str(item.get("q") or "")
        a = str(item.get("a") or "")
        habla_prueba = (
            "probarlo" in q.lower()
            or "gratis" in a.lower()
            or "días de prueba" in a.lower()
            or "días de acceso" in a.lower()
        )
        if n is None and habla_prueba:
            continue
        if n:
            a = re.sub(r"\d+\s+días", f"{n} días", a)
        faqs.append({**item, "q": q, "a": a})
    ficha["faq"] = faqs
    return ficha


def titulo_publico(oficio: str, donde: str = "") -> str:
    """Título de Google: marca primero, oficio después.

    Quien busca «CotizaT» o ve el snippet tiene que leer de un vistazo qué es
    (software de presupuestos de construcción/obra), no un nombre suelto.
    """
    oficio = str(oficio or "").strip().rstrip(".")
    donde = str(donde or "").strip()
    if donde:
        return f"{PRODUCT_NAME}: {oficio} en {donde}"
    return f"{PRODUCT_NAME}: {oficio}"


# ---------------------------------------------------------------------------
# Copy de la landing por país (title descriptivo, description ≈ 155, H1 único)
# ---------------------------------------------------------------------------

_LANDING: dict[str, dict] = {
    "": {
        "title": "CotizaT: software de presupuestos de construcción",
        "description": (
            "Software de presupuestos de construcción y reformas para España y "
            "Latinoamérica. Cada país con su catálogo de precios, IVA y NIF/RIF/RFC. "
            "APU, margen y PDF profesional. 7 días gratis."
        ),
        "h1": "Software de presupuestos de obra para España y Latinoamérica",
        "h1_resalte": "margen, tiempos y cierre",
        "sub": (
            "CotizaT convierte tu catálogo y tus precios en presupuestos de obra "
            "claros, con coste interno, beneficio y horas de cuadrilla. España con "
            "precios en EUR, NIF e IVA 21 %; Latinoamérica con su moneda y fiscalidad. "
            "PDF con tu logo, listo para WhatsApp."
        ),
        "kicker": "Sistema comercial para España y Latinoamérica · Construcción y reformas",
        "faq": [
            {
                "q": "¿CotizaT sirve para presupuestos de construcción en España y Latinoamérica?",
                "a": (
                    "Sí. Está hecho para constructoras pequeñas, reformistas y "
                    "contratistas de España, Venezuela, Colombia, México, Ecuador y Perú. "
                    "Cada país tiene su catálogo de precios, su moneda, su IVA y su ID fiscal "
                    "(NIF, RIF, NIT, RFC, RUC) y se elige al entrar."
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
        "title": "CotizaT: software de presupuestos de obra en Venezuela",
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
        "title": "CotizaT: software de presupuestos y APU en Colombia",
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
        "title": "CotizaT: software de presupuestos de obra en México",
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
        "title": "CotizaT: software de presupuestos y metrados en Perú",
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
        "title": "CotizaT: software de presupuestos y APU en Ecuador",
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
    "PA": {
        "title": "CotizaT: software de presupuestos y APU en Panamá",
        "description": (
            "Software de presupuestos de construcción para Panamá. RUC, ITBMS 7 %, "
            "USD, repello y cielo raso. Catálogo con APU. 7 días gratis, sin tarjeta."
        ),
        "h1": "Software de presupuestos y APU para construcción en Panamá",
        "h1_resalte": "dólares, RUC e ITBMS 7 %",
        "sub": (
            "Presupuesta obra y remodelación en USD, con RUC e ITBMS 7 %. Catálogo "
            "con análisis de precios unitarios, concreto, repello, cielo raso y "
            "plomero. PDF profesional para WhatsApp. Precios de referencia en USD "
            "con fuentes de Panamá (CEMEX, Panablock, HOPSA)."
        ),
        "kicker": "🇵🇦 Sistema comercial para Panamá · Construcción y remodelación",
        "faq": [
            {
                "q": "¿Está pensado para constructoras en Panamá?",
                "a": (
                    "Sí. El espacio nace en USD, ITBMS 7 % y RUC. Terminología "
                    "local: concreto, repello, cielo raso, zócalo, plomero, formaleta."
                ),
            },
            {
                "q": "¿Incluye APU con precios de Panamá?",
                "a": (
                    "Cada partida trae APU editable con referencias nacionales en USD: "
                    "cemento $8.25 por saco 42.5kg, bloque $0.95, arena $34/m3, concreto "
                    "210 $125/m3. El resto es referencia derivada de canasta nacional."
                ),
            },
            {
                "q": "¿El cliente firma en línea?",
                "a": (
                    "Puedes enviar un enlace privado opcional. Lo habitual es el "
                    "PDF por WhatsApp, que es como ya cierras en Ciudad de Panamá o David."
                ),
            },
            {
                "q": "¿Emite factura electrónica de la DGI?",
                "a": (
                    "No. Los documentos son comerciales y no sustituyen la factura "
                    "electrónica que te exija la DGI. El ITBMS 7 % lo configuras tú."
                ),
            },
        ],
    },
    "SV": {
        "title": "CotizaT: software de presupuestos y APU en El Salvador",
        "description": (
            "Software de presupuestos de construcción para El Salvador. NIT, IVA 13 %, "
            "USD, repello y cielo falso. Catálogo con APU. 7 días gratis, sin tarjeta."
        ),
        "h1": "Software de presupuestos y APU para construcción en El Salvador",
        "h1_resalte": "dólares, NIT e IVA 13 %",
        "sub": (
            "Presupuesta obra y remodelación en USD, con NIT e IVA 13 %. Catálogo "
            "con análisis de precios unitarios, concreto, repello, cielo falso y "
            "fontanero. PDF profesional para WhatsApp. Precios de referencia en USD "
            "con fuentes de El Salvador (CASALCO, EPA, Freund)."
        ),
        "kicker": "🇸🇻 Sistema comercial para El Salvador · Construcción y remodelación",
        "faq": [
            {
                "q": "¿Está pensado para constructoras en El Salvador?",
                "a": (
                    "Sí. El espacio nace en USD, IVA 13 % y NIT. Terminología "
                    "local: concreto, repello, cielo falso, zócalo, fontanero, tabla yeso."
                ),
            },
            {
                "q": "¿Incluye APU con precios de El Salvador?",
                "a": (
                    "Cada partida trae APU editable con referencias nacionales en USD: "
                    "cemento $8.73 por saco 42.5kg (CASALCO), bloque $0.40, arena $35/m3, "
                    "grava $45.05/m3, concreto 210 $135.35/m3. El resto es referencia "
                    "derivada de canasta nacional."
                ),
            },
            {
                "q": "¿El cliente firma en línea?",
                "a": (
                    "Puedes enviar un enlace privado opcional. Lo habitual es el "
                    "PDF por WhatsApp, que es como ya cierras en San Salvador o Santa Ana."
                ),
            },
            {
                "q": "¿Emite factura del Ministerio de Hacienda?",
                "a": (
                    "No. Los documentos son comerciales y no sustituyen la factura "
                    "electrónica que te exija Hacienda. El IVA 13 % lo configuras tú."
                ),
            },
        ],
    },
    "CL": {
        "title": "CotizaT: software de presupuestos y APU en Chile",
        "description": (
            "Software de presupuestos de construcción para Chile. RUT, IVA 19 %, "
            "CLP, hormigón y cielo falso. Catálogo con APU. 7 días gratis, sin tarjeta."
        ),
        "h1": "Software de presupuestos y APU para construcción en Chile",
        "h1_resalte": "pesos chilenos, RUT e IVA 19 %",
        "sub": (
            "Presupuesta obra y remodelación en CLP, con RUT e IVA 19 %. Catálogo "
            "con análisis de precios unitarios, hormigón, estuco, cielo falso y "
            "gasfíter. PDF profesional para WhatsApp. Precios de referencia en CLP "
            "con fuentes de Chile (Sodimac, Easy, CChC, GlobalGTC)."
        ),
        "kicker": "🇨🇱 Sistema comercial para Chile · Construcción y remodelación",
        "faq": [
            {
                "q": "¿Está pensado para constructoras en Chile?",
                "a": (
                    "Sí. El espacio nace en CLP, IVA 19 % y RUT. Terminología "
                    "local: hormigón, estuco, cielo falso, guardapolvo, gasfíter, moldaje, fierro."
                ),
            },
            {
                "q": "¿Incluye APU con precios de Chile?",
                "a": (
                    "Cada partida trae APU editable con referencias nacionales en CLP: "
                    "cemento $4.790 por saco 25kg (Sodimac Melón), bloque $1.840, arena $33.190/m3, "
                    "hormigón H25 $110.000/m3. El resto es referencia derivada de canasta nacional."
                ),
            },
            {
                "q": "¿El cliente firma en línea?",
                "a": (
                    "Puedes enviar un enlace privado opcional. Lo habitual es el "
                    "PDF por WhatsApp, que es como ya cierras en Santiago o Concepción."
                ),
            },
            {
                "q": "¿Emite factura electrónica del SII?",
                "a": (
                    "No. Los documentos son comerciales y no sustituyen la factura "
                    "electrónica que te exija el SII. El IVA 19 % lo configuras tú."
                ),
            },
        ],
    },
    "AR": {
        "title": "CotizaT: software de presupuestos y APU en Argentina",
        "description": (
            "Software de presupuestos de construcción para Argentina. CUIT, IVA 21 %, "
            "ARS, hormigón y cielorraso. Catálogo con APU. 7 días gratis, sin tarjeta."
        ),
        "h1": "Software de presupuestos y APU para construcción en Argentina",
        "h1_resalte": "pesos argentinos, CUIT e IVA 21 %",
        "sub": (
            "Presupuesta obra y remodelación en ARS, con CUIT e IVA 21 %. Catálogo "
            "con análisis de precios unitarios, hormigón, revoque, cielorraso y "
            "plomero. PDF profesional para WhatsApp. Precios de referencia en ARS "
            "con fuentes de Argentina (UOCRA, Loma Negra, Holcim, CAMARCO)."
        ),
        "kicker": "🇦🇷 Sistema comercial para Argentina · Construcción y remodelación",
        "faq": [
            {
                "q": "¿Está pensado para constructoras en Argentina?",
                "a": (
                    "Sí. El espacio nace en ARS, IVA 21 % y CUIT. Terminología "
                    "local: hormigón, revoque, cielorraso, zócalo, plomero, hierro, encadenado."
                ),
            },
            {
                "q": "¿Incluye APU con precios de Argentina?",
                "a": (
                    "Cada partida trae APU editable con referencias nacionales en ARS: "
                    "cemento $11.433 por bolsa 50kg (Loma Negra/Holcim), bloque $1.500, arena $33.500/m3, "
                    "hormigón H21 $168.478/m3. El resto es referencia derivada de canasta nacional."
                ),
            },
            {
                "q": "¿El cliente firma en línea?",
                "a": (
                    "Puedes enviar un enlace privado opcional. Lo habitual es el "
                    "PDF por WhatsApp, que es como ya cierras en Buenos Aires o Córdoba."
                ),
            },
            {
                "q": "¿Emite factura electrónica de AFIP?",
                "a": (
                    "No. Los documentos son comerciales y no sustituyen la factura "
                    "electrónica que te exija AFIP. El IVA 21 % lo configuras tú."
                ),
            },
        ],
    },
    "DO": {
        "title": "CotizaT: software de presupuestos y APU en República Dominicana",
        "description": (
            "Software de presupuestos de construcción para República Dominicana. RNC, ITBIS 18 %, "
            "DOP, hormigón y pañete. Catálogo con APU. 7 días gratis, sin tarjeta."
        ),
        "h1": "Software de presupuestos y APU para construcción en República Dominicana",
        "h1_resalte": "pesos dominicanos, RNC e ITBIS 18 %",
        "sub": (
            "Presupuesta obra y remodelación en DOP, con RNC e ITBIS 18 %. Catálogo "
            "con análisis de precios unitarios, hormigón, pañete, plafón y "
            "plomero. PDF profesional para WhatsApp. Precios de referencia en DOP "
            "con fuentes de RD (MOPC, Ferretería Americana, Ferremix, SonProject)."
        ),
        "kicker": "🇩🇴 Sistema comercial para República Dominicana · Construcción y remodelación",
        "faq": [
            {
                "q": "¿Está pensado para constructoras en República Dominicana?",
                "a": (
                    "Sí. El espacio nace en DOP, ITBIS 18 % y RNC. Terminología "
                    "local: hormigón, pañete, plafón, zócalo, plomero, block, varilla."
                ),
            },
            {
                "q": "¿Incluye APU con precios de República Dominicana?",
                "a": (
                    "Cada partida trae APU editable con referencias nacionales en DOP: "
                    "cemento RD$535 por funda 94lb, block 6'' RD$42, arena RD$1.550/m3, grava RD$1.700/m3. "
                    "El resto es referencia derivada de canasta nacional."
                ),
            },
            {
                "q": "¿El cliente firma en línea?",
                "a": (
                    "Puedes enviar un enlace privado opcional. Lo habitual es el "
                    "PDF por WhatsApp, que es como ya cierras en Santo Domingo o Santiago."
                ),
            },
            {
                "q": "¿Emite comprobante fiscal DGII?",
                "a": (
                    "No. Los documentos son comerciales y no sustituyen el comprobante "
                    "fiscal que te exija DGII. El ITBIS 18 % lo configuras tú."
                ),
            },
        ],
    },
    "UY": {
        "title": "CotizaT: software de presupuestos y APU en Uruguay",
        "description": (
            "Software de presupuestos de construcción para Uruguay. RUT, IVA 22 %, "
            "UYU, hormigón y revoque. Catálogo con APU. 7 días gratis, sin tarjeta."
        ),
        "h1": "Software de presupuestos y APU para construcción en Uruguay",
        "h1_resalte": "pesos uruguayos, RUT e IVA 22 %",
        "sub": (
            "Presupuesta obra y remodelación en UYU, con RUT e IVA 22 %. Catálogo "
            "con análisis de precios unitarios, hormigón, revoque, cielorraso y "
            "sanitario. PDF profesional para WhatsApp. Precios de referencia en UYU "
            "con fuentes de Uruguay (SUNCA laudo 2025-2026, Barraca Central, EMAT, Sodimac UY)."
        ),
        "kicker": "🇺🇾 Sistema comercial para Uruguay · Construcción y remodelación",
        "faq": [
            {
                "q": "¿Está pensado para constructoras en Uruguay?",
                "a": (
                    "Sí. El espacio nace en UYU, IVA 22 % y RUT. Terminología "
                    "local: hormigón, revoque, cielorraso, zócalo, sanitario, varilla, malla sima."
                ),
            },
            {
                "q": "¿Incluye APU con precios de Uruguay?",
                "a": (
                    "Cada partida trae APU editable con referencias nacionales en UYU: "
                    "cemento $240 por bolsa 25kg, bloque 15x19x39 $70, arena $1.200/m3, hormigón $5.500/m3. "
                    "El resto es referencia derivada de canasta nacional."
                ),
            },
            {
                "q": "¿El cliente firma en línea?",
                "a": (
                    "Puedes enviar un enlace privado opcional. Lo habitual es el "
                    "PDF por WhatsApp, que es como ya cierras en Montevideo o Maldonado."
                ),
            },
            {
                "q": "¿Emite factura electrónica de DGI?",
                "a": (
                    "No. Los documentos son comerciales y no sustituyen la factura "
                    "electrónica que te exija DGI. El IVA 22 % lo configuras tú."
                ),
            },
        ],
    },
    "PY": {
        "title": "CotizaT: software de presupuestos y APU en Paraguay",
        "description": (
            "Software de presupuestos de construcción para Paraguay. RUC, IVA 10 %, "
            "PYG, hormigón y revoque. Catálogo con APU. 7 días gratis, sin tarjeta."
        ),
        "h1": "Software de presupuestos y APU para construcción en Paraguay",
        "h1_resalte": "guaraníes, RUC e IVA 10 %",
        "sub": (
            "Presupuesta obra y remodelación en PYG, con RUC e IVA 10 %. Catálogo "
            "con análisis de precios unitarios, hormigón, revoque, cielorraso y "
            "plomero. PDF profesional para WhatsApp. Precios de referencia en PYG "
            "con fuentes de Paraguay (MTESS laudo, INC, Costeo.com.py)."
        ),
        "kicker": "🇵🇾 Sistema comercial para Paraguay · Construcción y remodelación",
        "faq": [
            {
                "q": "¿Está pensado para constructoras en Paraguay?",
                "a": (
                    "Sí. El espacio nace en PYG, IVA 10 % y RUC. Terminología "
                    "local: hormigón, revoque, cielorraso, zócalo, plomero, varilla, encadenado. Sin decimales en guaraníes."
                ),
            },
            {
                "q": "¿Incluye APU con precios de Paraguay?",
                "a": (
                    "Cada partida trae APU editable con referencias nacionales en PYG: "
                    "cemento Gs 59.000 por bolsa 50kg, bloque Gs 5.300, piedra bruta Gs 104.000/m3, hormigón Gs 650.000/m3. "
                    "El resto es referencia derivada de canasta nacional."
                ),
            },
            {
                "q": "¿El cliente firma en línea?",
                "a": (
                    "Puedes enviar un enlace privado opcional. Lo habitual es el "
                    "PDF por WhatsApp, que es como ya cierras en Asunción o Ciudad del Este."
                ),
            },
            {
                "q": "¿Emite factura electrónica de la SET?",
                "a": (
                    "No. Los documentos son comerciales y no sustituyen la factura "
                    "electrónica que te exija la SET. El IVA 10 % lo configuras tú."
                ),
            },
        ],
    },
    "BO": {
        "title": "CotizaT: software de presupuestos y APU en Bolivia",
        "description": (
            "Software de presupuestos de construcción para Bolivia. NIT, IVA 13 %, "
            "BOB, hormigón y revoque. Catálogo con APU. 7 días gratis, sin tarjeta."
        ),
        "h1": "Software de presupuestos y APU para construcción en Bolivia",
        "h1_resalte": "bolivianos, NIT e IVA 13 %",
        "sub": (
            "Presupuesta obra y remodelación en BOB, con NIT e IVA 13 %. Catálogo "
            "con análisis de precios unitarios, hormigón, revoque, cielo falso y "
            "plomero. PDF profesional para WhatsApp. Precios de referencia en BOB "
            "con fuentes de Bolivia (SOBOCE, FANCESA, COBOCE, OneEstimate)."
        ),
        "kicker": "🇧🇴 Sistema comercial para Bolivia · Construcción y remodelación",
        "faq": [
            {
                "q": "¿Está pensado para constructoras en Bolivia?",
                "a": (
                    "Sí. El espacio nace en BOB, IVA 13 % y NIT. Terminología "
                    "local: hormigón, revoque, cielo falso, zócalo, plomero, fierro."
                ),
            },
            {
                "q": "¿Incluye APU con precios de Bolivia?",
                "a": (
                    "Cada partida trae APU editable con referencias nacionales en BOB: "
                    "cemento Bs 54 por bolsa 50kg, arena Bs 150/m3, piedra Bs 160/m3, bloque Bs 2.5, hormigón Bs 600/m3. "
                    "El resto es referencia derivada de canasta nacional."
                ),
            },
            {
                "q": "¿El cliente firma en línea?",
                "a": (
                    "Puedes enviar un enlace privado opcional. Lo habitual es el "
                    "PDF por WhatsApp, que es como ya cierras en Santa Cruz o La Paz."
                ),
            },
            {
                "q": "¿Emite factura electrónica del SIN?",
                "a": (
                    "No. Los documentos son comerciales y no sustituyen la factura "
                    "que te exija el SIN. El IVA 13 % lo configuras tú."
                ),
            },
        ],
    },
    "CR": {
        "title": "CotizaT: software de presupuestos y APU en Costa Rica",
        "description": (
            "Software de presupuestos de construcción para Costa Rica. NITE, IVA 13 %, "
            "CRC, concreto y repello. Catálogo con APU. 7 días gratis, sin tarjeta."
        ),
        "h1": "Software de presupuestos y APU para construcción en Costa Rica",
        "h1_resalte": "colones, NITE e IVA 13 %",
        "sub": (
            "Presupuesta obra y remodelación en CRC, con NITE e IVA 13 %. Catálogo "
            "con análisis de precios unitarios, concreto, repello, cielo raso y "
            "fontanero. PDF profesional para WhatsApp. Precios de referencia en CRC "
            "con fuentes de Costa Rica (EPA, Ferconce, CFIA)."
        ),
        "kicker": "🇨🇷 Sistema comercial para Costa Rica · Construcción y remodelación",
        "faq": [
            {
                "q": "¿Está pensado para constructoras en Costa Rica?",
                "a": (
                    "Sí. El espacio nace en CRC, IVA 13 % y NITE. Terminología "
                    "local: concreto, repello, cielo raso, rodapié, fontanero, formaleta."
                ),
            },
            {
                "q": "¿Incluye APU con precios de Costa Rica?",
                "a": (
                    "Cada partida trae APU editable con referencias nacionales en CRC: "
                    "cemento ₡6.750 por saco 50kg, arena ₡27.470/m3, piedra ₡28.000/m3, bloque ₡650, concreto ₡55.000/m3. "
                    "El resto es referencia derivada de canasta nacional."
                ),
            },
            {
                "q": "¿El cliente firma en línea?",
                "a": (
                    "Puedes enviar un enlace privado opcional. Lo habitual es el "
                    "PDF por WhatsApp, que es como ya cierras en San José o Alajuela."
                ),
            },
            {
                "q": "¿Emite factura electrónica de Hacienda?",
                "a": (
                    "No. Los documentos son comerciales y no sustituyen la factura "
                    "electrónica que te exija Hacienda. El IVA 13 % lo configuras tú."
                ),
            },
        ],
    },
    "GT": {
        "title": "CotizaT: software de presupuestos y APU en Guatemala",
        "description": (
            "Software de presupuestos de construcción para Guatemala. NIT, IVA 12 %, "
            "GTQ, concreto y repello. Catálogo con APU. 7 días gratis, sin tarjeta."
        ),
        "h1": "Software de presupuestos y APU para construcción en Guatemala",
        "h1_resalte": "quetzales, NIT e IVA 12 %",
        "sub": (
            "Presupuesta obra y remodelación en GTQ, con NIT e IVA 12 %. Catálogo "
            "con análisis de precios unitarios, concreto, repello, cielo falso y "
            "fontanero. PDF profesional para WhatsApp. Precios de referencia en GTQ "
            "con fuentes de Guatemala (EPA, Cemaco, Construfácil, INE)."
        ),
        "kicker": "🇬🇹 Sistema comercial para Guatemala · Construcción y remodelación",
        "faq": [
            {
                "q": "¿Está pensado para constructoras en Guatemala?",
                "a": (
                    "Sí. El espacio nace en GTQ, IVA 12 % y NIT. Terminología "
                    "local: concreto, repello, cielo falso, zócalo, fontanero, block, varilla, flipón."
                ),
            },
            {
                "q": "¿Incluye APU con precios de Guatemala?",
                "a": (
                    "Cada partida trae APU editable con referencias nacionales en GTQ: "
                    "cemento Q80.25 por saco 42.5kg, block Q5.5, arena Q180/m3, piedrín Q230/m3, concreto Q900/m3. "
                    "El resto es referencia derivada de canasta nacional."
                ),
            },
            {
                "q": "¿El cliente firma en línea?",
                "a": (
                    "Puedes enviar un enlace privado opcional. Lo habitual es el "
                    "PDF por WhatsApp, que es como ya cierras en Ciudad de Guatemala o Quetzaltenango."
                ),
            },
            {
                "q": "¿Emite factura FEL?",
                "a": (
                    "No. Los documentos son comerciales y no sustituyen la factura "
                    "electrónica FEL que te exija la SAT. El IVA 12 % lo configuras tú."
                ),
            },
        ],
    },
    "HN": {
        "title": "CotizaT: software de presupuestos y APU en Honduras",
        "description": (
            "Software de presupuestos de construcción para Honduras. RTN, ISV 15 %, "
            "HNL, concreto y repello. Catálogo con APU. 7 días gratis, sin tarjeta."
        ),
        "h1": "Software de presupuestos y APU para construcción en Honduras",
        "h1_resalte": "lempiras, RTN e ISV 15 %",
        "sub": (
            "Presupuesta obra y remodelación en HNL, con RTN e ISV 15 %. Catálogo "
            "con análisis de precios unitarios, concreto, repello, cielo falso y "
            "fontanero. PDF profesional para WhatsApp. Precios de referencia en HNL "
            "con fuentes de Honduras (CHICO, Argos, Bijao, UNO, La Prensa)."
        ),
        "kicker": "🇭🇳 Sistema comercial para Honduras · Construcción y remodelación",
        "faq": [
            {
                "q": "¿Está pensado para constructoras en Honduras?",
                "a": (
                    "Sí. El espacio nace en HNL, ISV 15 % y RTN. Terminología "
                    "local: concreto, repello, cielo falso, zócalo, fontanero, bloque, varilla."
                ),
            },
            {
                "q": "¿Incluye APU con precios de Honduras?",
                "a": (
                    "Cada partida trae APU editable con referencias nacionales en HNL: "
                    "cemento L215 por saco 42.5kg, bloque L28, arena L500/m3, piedra L550/m3, concreto L4.500/m3. "
                    "El resto es referencia derivada de canasta nacional."
                ),
            },
            {
                "q": "¿El cliente firma en línea?",
                "a": (
                    "Puedes enviar un enlace privado opcional. Lo habitual es el "
                    "PDF por WhatsApp, que es como ya cierras en Tegucigalpa o San Pedro Sula."
                ),
            },
            {
                "q": "¿Emite factura electrónica del SAR?",
                "a": (
                    "No. Los documentos son comerciales y no sustituyen la factura "
                    "electrónica que te exija el SAR. El ISV 15 % lo configuras tú."
                ),
            },
        ],
    },
    "NI": {
        "title": "CotizaT: software de presupuestos y APU en Nicaragua",
        "description": (
            "Software de presupuestos de construcción para Nicaragua. RUC, IVA 15 %, "
            "NIO, concreto y repello. Catálogo con APU. 7 días gratis, sin tarjeta."
        ),
        "h1": "Software de presupuestos y APU para construcción en Nicaragua",
        "h1_resalte": "córdobas, RUC e IVA 15 %",
        "sub": (
            "Presupuesta obra y remodelación en NIO, con RUC e IVA 15 %. Catálogo "
            "con análisis de precios unitarios, concreto, repello, cielo raso y "
            "fontanero. PDF profesional para WhatsApp. Precios de referencia en NIO "
            "con fuentes de Nicaragua (SINSA, Cemex, MITRAB)."
        ),
        "kicker": "🇳🇮 Sistema comercial para Nicaragua · Construcción y remodelación",
        "faq": [
            {
                "q": "¿Está pensado para constructoras en Nicaragua?",
                "a": (
                    "Sí. El espacio nace en NIO, IVA 15 % y RUC. Terminología "
                    "local: concreto, repello, cielo raso, zócalo, fontanero, bloque, varilla, Gypsum."
                ),
            },
            {
                "q": "¿Incluye APU con precios de Nicaragua?",
                "a": (
                    "Cada partida trae APU editable con referencias nacionales en NIO: "
                    "cemento C$522.57 por saco 42.5kg (SINSA), bloque C$32, arena C$600/m3, piedra C$650/m3, concreto C$5.000/m3. "
                    "El resto es referencia derivada de canasta nacional."
                ),
            },
            {
                "q": "¿El cliente firma en línea?",
                "a": (
                    "Puedes enviar un enlace privado opcional. Lo habitual es el "
                    "PDF por WhatsApp, que es como ya cierras en Managua o León."
                ),
            },
            {
                "q": "¿Emite factura electrónica de la DGI?",
                "a": (
                    "No. Los documentos son comerciales y no sustituyen la factura "
                    "electrónica que te exija la DGI. El IVA 15 % lo configuras tú."
                ),
            },
        ],
    },
    "ES": {
        "title": "CotizaT: software de presupuestos de obra y reformas para España",
        "description": (
            "Software para presupuestos de reformas y obra en España. En euros, "
            "NIF, IVA 21 %, hormigón, pladur y fontanería. Catálogo con APU. "
            "7 días gratis, sin tarjeta."
        ),
        "h1": "Software de presupuestos de obra y reformas para España",
        "h1_resalte": "euros, NIF e IVA 21 %",
        "sub": (
            "Cotiza reformas y obra en euros, con NIF, IVA 21 % y la terminología "
            "de la obra española: hormigón, pladur, falso techo, alicatado y "
            "fontanería. Ves el margen, el coste y las horas de tu cuadrilla antes "
            "de enviar un PDF con tu logo por WhatsApp o email."
        ),
        "kicker": "🇪🇸 Sistema comercial para España · Presupuestos de reforma y obra",
        "faq": [
            {
                "q": "¿Está pensado para reformistas y constructoras en España?",
                "a": (
                    "Sí. Es para reformistas, contratistas y pequeñas constructoras "
                    "de 2 a 15 personas que cotizan en euros, con NIF e IVA 21 %. "
                    "Habla tu obra: hormigón, pladur, falso techo, alicatado, fontanería."
                ),
            },
            {
                "q": "¿Incluye análisis de precios unitarios (APU) en euros?",
                "a": (
                    "Cada partida llega descompuesta en materiales, mano de obra y "
                    "equipo, con rendimiento y precio en euros, con referencias de "
                    "mercado españolas. Editas un recurso y se recalcula el presupuesto."
                ),
            },
            {
                "q": "¿El cliente tiene que registrarse?",
                "a": (
                    "No. Envías el PDF por WhatsApp o email como ya haces. El enlace "
                    "privado con firma es opcional."
                ),
            },
            {
                "q": "¿Emite factura con la AEAT?",
                "a": (
                    "No. Genera presupuestos comerciales con NIF e IVA; la factura "
                    "la emites con tu gestoría o tu sistema de facturación."
                ),
            },
            {
                "q": "¿Cuánto cuesta en España?",
                "a": (
                    "89 € al año (habitual 109 €) o 9,99 € al mes el primer año. "
                    "7 días de prueba completa, sin tarjeta y sin permanencia."
                ),
            },
        ],
    },
}


def ficha_landing(codigo: str = "") -> dict:
    """Copy SEO de la landing (genérica o de un país del selector)."""
    from .seo_articulos import articulo_de_pais
    from .seo_contenido import cuerpo_pais, lista_guias

    codigo = str(codigo or "").strip().upper()
    base = _LANDING.get(codigo) or _LANDING[""]
    pais = PAISES.get(codigo) or PAIS_GENERICO
    return _aplicar_prueba(
        {
            **base,
            "codigo": codigo,
            "lang": hreflang_pais(codigo) if codigo else "es",
            "nombre_pais": pais.get("nombre") or "Latinoamérica",
            "tema": "",
            "canonical_path": ruta_pais(codigo),
            "cuerpo": cuerpo_pais(codigo),
            "guias": lista_guias(),
            "articulo": articulo_de_pais(codigo),
        }
    )


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
        title = titulo_publico(
            "software de presupuestos de construcción",
            nombre if codigo else "",
        )
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
                "escalados a los m². Importación desde Excel (.xlsx) y BC3.",
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
        title = titulo_publico(
            "software de APU y análisis de precios unitarios",
            nombre if codigo else "",
        )
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
                "Excel y BC3",
                "Si ya trabajas con matrices de descompuestos en Excel (.xlsx), "
                "importas el archivo y se clasifica materiales, mano de obra y "
                "complementarios, sin perder filas ni fórmulas. También pegas TSV "
                "desde Excel o importas .bc3 (FIEBDC-3).",
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
        title = titulo_publico(
            "software de presupuestos de remodelación",
            nombre if codigo else "",
        )
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

    from .seo_articulos import articulo_de_pais
    from .seo_contenido import extra_hub, faq_hub

    body = list(body) + extra_hub(codigo, tema)
    art = articulo_de_pais(codigo)
    if art:
        related = list(related) + [(art["h1"], "/guia/" + art["slug"])]
    faq_local = faq_hub(codigo, tema)
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
    if faq_local:
        faq = faq_local + faq
    return _aplicar_prueba({
        "title": title,
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
    })


def ficha_tema(codigo: str, tema: str) -> dict | None:
    codigo = str(codigo or "").strip().upper()
    tema = str(tema or "").strip().lower()
    if tema not in TEMAS:
        return None
    if codigo and codigo not in ORDEN_SELECTOR:
        return None
    return _bloques_tema(codigo, tema)


def jsonld_organizacion(request: Request | None = None) -> dict:
    origen = origen_canonico(request)
    return {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": PRODUCT_NAME,
        "legalName": PRODUCT_NAME + " · Presupuestos",
        "url": origen + "/",
        "logo": origen + "/static/icono.png",
        "email": "soporte@cotizat.online",
        "description": VALUE_PROPOSITION,
        "areaServed": [{"@type": "Country", "name": PAISES[c]["nombre"]} for c in ORDEN_SELECTOR],
        "contactPoint": {
            "@type": "ContactPoint",
            "email": "soporte@cotizat.online",
            "contactType": "customer support",
            "availableLanguage": ["es"],
        },
    }


def jsonld_website(request: Request | None = None) -> dict:
    origen = origen_canonico(request)
    return {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": PRODUCT_NAME,
        "url": origen + "/",
        "inLanguage": ["es", "es-VE", "es-CO", "es-MX", "es-PE", "es-EC", "es-PA", "es-SV", "es-CL", "es-AR", "es-DO", "es-UY", "es-PY", "es-BO", "es-CR", "es-GT", "es-HN", "es-NI", "es-ES"],
        "publisher": {"@type": "Organization", "name": PRODUCT_NAME},
        "description": VALUE_PROPOSITION,
    }


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
        "featureList": [
            "Presupuestos de construcción y remodelación",
            "Análisis de precios unitarios (APU)",
            "PDF profesional para WhatsApp",
        ],
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


def jsonld_howto(guia: dict, request: Request | None = None) -> dict:
    origen = origen_canonico(request)
    pasos = []
    for i, (titulo, pars) in enumerate(guia.get("secciones") or [], start=1):
        texto = " ".join(str(p) for p in (pars or []) if p).strip()
        paso: dict = {"@type": "HowToStep", "position": i, "name": titulo}
        if texto:
            paso["text"] = texto
        pasos.append(paso)
    return {
        "@context": "https://schema.org",
        "@type": "HowTo",
        "name": guia["h1"],
        "description": guia["description"],
        "url": origen + "/guia/" + guia["slug"],
        "inLanguage": "es",
        "step": pasos,
    }


def jsonld_articulo(guia: dict, request: Request | None = None) -> dict:
    origen = origen_canonico(request)
    path = "/guia/" + guia["slug"]
    return {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": guia["h1"],
        "description": guia["description"],
        "inLanguage": "es",
        "url": origen + path,
        "mainEntityOfPage": origen + path,
        "dateModified": SITEMAP_LASTMOD,
        "author": {"@type": "Organization", "name": PRODUCT_NAME},
        "publisher": {
            "@type": "Organization",
            "name": PRODUCT_NAME,
            "logo": {"@type": "ImageObject", "url": origen + "/static/icono.png"},
        },
        "image": origen + OG_IMAGE,
    }


def contexto_guia(request: Request, slug: str) -> dict | None:
    from .paises import lista_paises
    from .seo_articulos import lista_articulos
    from .seo_contenido import ficha_guia, lista_guias

    guia = ficha_guia(slug)
    if not guia:
        return None
    origen = origen_canonico(request)
    path = "/guia/" + guia["slug"]
    seo = _aplicar_prueba(
        {
            "title": guia["title"],
            "description": guia["description"],
            "lang": "es",
            "h1": guia["h1"],
            "canonical_path": path,
            "faq": list(guia.get("faq") or []),
        }
    )
    bloques = [
        jsonld_organizacion(request),
        jsonld_website(request),
        jsonld_articulo(guia, request),
        jsonld_howto(guia, request),
        jsonld_breadcrumb(request, [("Inicio", "/"), ("Guías", "/mapa-del-sitio"), (guia["h1"], path)]),
    ]
    if seo["faq"]:
        bloques.append(jsonld_faq(seo["faq"]))
    return {
        "seo": seo,
        "guia": guia,
        "guias": lista_guias(),
        "articulos": lista_articulos(),
        "paises": lista_paises(),
        "origen_seo": origen,
        "canonical_url": origen + path,
        "hreflang_links": [],
        "og_image": origen + OG_IMAGE,
        "jsonld_bloques": bloques,
        "seo_temas": TEMAS,
        "og_type": "article",
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
    bloques_ld = [
        jsonld_organizacion(request),
        jsonld_website(request),
        jsonld_software(request, codigo),
    ]
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


# Páginas públicas que no son landing de país: copy y schema propios.
# No reutilizar ``contexto_seo()`` o heredan el FAQ JSON-LD de la home.
_PAGINAS_ESTATICAS: dict[str, dict] = {
    "como-funciona": {
        "path": "/como-funciona",
        "title": "CotizaT: cómo funciona el software de presupuestos de obra",
        "description": (
            "Guía de CotizaT: catálogo con análisis de precios, presupuestos, "
            "margen, tiempos internos, PDF, WhatsApp, versiones, proyectos y cobros."
        ),
        "h1": "Cómo funciona CotizaT, función por función",
        "software": True,
    },
    "pago": {
        "path": "/pago",
        "title": "CotizaT: planes del software de presupuestos de construcción",
        "description": (
            "Planes anuales y mensuales de CotizaT, software de presupuestos de "
            "construcción. 89 US$/año de lanzamiento. 7 días gratis, sin tarjeta."
        ),
        "h1": "Planes del software de presupuestos de construcción",
        "software": True,
    },
    "mapa-del-sitio": {
        "path": "/mapa-del-sitio",
        "title": "CotizaT: mapa del sitio — software de presupuestos de construcción",
        "description": (
            "Índice de páginas públicas de CotizaT: países, software de "
            "presupuestos, APU, remodelación y guías."
        ),
        "h1": "Mapa del sitio",
        "software": False,
    },
    "terminos": {
        "path": "/legal/terminos",
        "title": "CotizaT: términos del servicio del software de presupuestos",
        "description": (
            "Términos del servicio de CotizaT. Licencia, datos, documentos "
            "comerciales (no factura fiscal) y cancelación sin permanencia."
        ),
        "h1": "Términos del servicio y licencia de uso",
        "software": False,
    },
    "privacidad": {
        "path": "/legal/privacidad",
        "title": "CotizaT: política de privacidad del software de presupuestos",
        "description": (
            "Política de privacidad de CotizaT: qué datos guarda el software de "
            "presupuestos, con quién se procesan y cómo exportarlos o borrarlos."
        ),
        "h1": "Política de privacidad",
        "software": False,
    },
    "soporte": {
        "path": "/legal/soporte",
        "title": "CotizaT: condiciones de soporte del software de presupuestos",
        "description": (
            "Qué incluye el soporte de CotizaT, qué no incluye (asesoría fiscal, "
            "desarrollos a medida) y cómo reportar un error."
        ),
        "h1": "Condiciones de soporte",
        "software": False,
    },
    "licencias": {
        "path": "/legal/licencias",
        "title": "CotizaT: licencias de terceros",
        "description": (
            "Software y tipografías de terceros usadas por CotizaT, con sus "
            "licencias (SIL OFL, FastAPI y demás)."
        ),
        "h1": "Licencias de terceros",
        "software": False,
    },
    "preguntas": {
        "path": "/legal/preguntas",
        "title": "CotizaT: preguntas frecuentes del software de presupuestos",
        "description": (
            "Preguntas sobre CotizaT: prueba gratis, catálogo y APU, PDF, "
            "WhatsApp, precio, factura fiscal y soporte."
        ),
        "h1": "Preguntas frecuentes",
        "software": False,
    },
}


def contexto_pagina_estatica(request: Request, clave: str) -> dict:
    """Canónica, OG y JSON-LD de una página pública que no es landing.

    Sin FAQ heredada de ``/``. El schema de SoftwareApplication solo va
    donde el copy vende el producto (cómo funciona, planes).
    """
    from .seo_contenido import FAQ_LEGAL

    ficha = _PAGINAS_ESTATICAS[clave]
    origen = origen_canonico(request)
    path = ficha["path"]
    seo = _aplicar_prueba(
        {
            "title": ficha["title"],
            "description": ficha["description"],
            "lang": "es",
            "h1": ficha["h1"],
            "canonical_path": path,
            "faq": FAQ_LEGAL if clave == "preguntas" else [],
            "nombre_pais": "Latinoamérica",
        }
    )
    bloques = [
        jsonld_organizacion(request),
        jsonld_website(request),
    ]
    if ficha.get("software"):
        bloques.append(jsonld_software(request, ""))
    if seo.get("faq"):
        bloques.append(jsonld_faq(seo["faq"]))
    bloques.append(
        jsonld_breadcrumb(request, [("Inicio", "/"), (ficha["h1"], path)])
    )
    return {
        "seo": seo,
        "origen_seo": origen,
        "canonical_url": origen + path,
        "hreflang_links": [],
        "og_image": origen + OG_IMAGE,
        "jsonld_bloques": bloques,
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
    add("/mapa-del-sitio", "0.4", "monthly")
    from .seo_contenido import lista_todas_guias

    for guia in lista_todas_guias():
        add(f"/guia/{guia['slug']}", "0.7", "monthly")
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
