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

from .branding import PRODUCT_NAME, value_proposition
from .i18n import normalizar_idioma
from .paises import ORDEN_SELECTOR, PAISES, PAIS_GENERICO, lista_paises

#: Imagen social 1200×630. JPEG y no PNG: la tarjeta es un degradado plano
#: y el PNG pesaba 870 KB (WhatsApp y LinkedIn descartan previews así). El
#: JPEG equivalente son 66 KB sin diferencia visible.
OG_IMAGE = "/static/og-cotizat.jpg"
SITEMAP_LASTMOD = "2026-10-19"

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
        "/novedades",
        "/soporte",
        "/calculadora",
        "/guia/presupuesto-de-obra",
        "/guia/analisis-precios-unitarios",
        "/guia/presupuesto-remodelacion",
        "/precios-comparados",
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


def _es_indexable_precios(resto: str) -> bool:
    """Rutas del catálogo público de precios de un mercado.

    Son ~47 000 URL con dato propio (precio unitario, descompuesto, moneda y
    país) y estaban fuera de la lista blanca: el ``<meta robots>`` decía
    «index» pero la cabecera ``X-Robots-Tag`` decía «noindex» y, cuando las
    dos se contradicen, manda la cabecera. El catálogo entero llevaba tiempo
    fuera del índice sin que ningún test lo detectara.

    Se acepta la forma canónica de cada tipo de página y nada más: un slug
    inventado da 404 en el router, no una página indexable.
    """
    partes = str(resto or "").strip("/").split("/")
    if not partes or not partes[0]:
        return False
    if len(partes) == 1 and partes[0] in {"precios.json", "prices.json"}:
        return True
    if len(partes) == 1 and partes[0] in {"mano-de-obra", "labour-rates"}:
        return True
    if partes[0] not in {"precios", "prices"}:
        return False
    if len(partes) == 1:
        return True
    return len(partes) <= 3 and all(
        re.fullmatch(r"[a-z0-9][a-z0-9-]*", segmento)
        for segmento in partes[1:]
    )


def es_indexable(path: str) -> bool:
    """¿Esta ruta debe aparecer en buscadores?

    Indexamos landings, páginas de intención, legales, planes y estáticos.
    El panel, el login, las propuestas y los archivos privados no.
    """
    p = str(path or "")
    # El prefijo /en (o /en-xx) vive en la URL que ve el navegador: el
    # middleware de idioma lo reescribe después de pasar por aquí, así que
    # hay que reconocerlo para no marcar toda la web en inglés como noindex.
    if p == "/en" or p.startswith("/en/") or p.startswith("/en-"):
        return _es_indexable_en(p)
    if p.endswith((".xml", ".txt", ".json")):
        # Sitemaps (incluidos los hijos de precios), robots.txt y el fichero
        # de IndexNow. No son HTML, pero marcarlos noindex desde el
        # middleware no tiene ningún sentido y confunde al diagnóstico.
        return True
    if p in _INDEXABLES_EXACTAS:
        return True
    if p.startswith("/legal/") and p.count("/") == 2:
        return True
    if p.startswith("/guia/") and p.count("/") == 2:
        return True
    # Comparador internacional (portada y capítulos).
    if p == "/precios-comparados" or (
        p.startswith("/precios-comparados/") and p.count("/") == 2
    ):
        return True
    if p == "/precios-comparados.json":
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
        # Los artículos de mercados hispanos viven en su silo canónico:
        # /es/guia/x, /co/guia/x… La ruta se valida además en el router para
        # que un artículo español bajo /mx/ devuelva 404.
        if len(partes) == 3 and partes[1] == "guia" and re.fullmatch(r"[a-z0-9-]+", partes[2]):
            return True
        # Catalogo de precios del mercado: /mx/precios, /mx/precios/{apartado},
        # /mx/precios/{apartado}/{partida}, /mx/mano-de-obra, /mx/precios.json
        if _es_indexable_precios("/".join(partes[1:])):
            return True
        return False
    return False


# Rutas en inglés equivalentes a las españolas. Si no están aquí, noindex.
_INDEXABLES_EN = frozenset(
    {
        "/en",
        "/en/",
        "/en/como-funciona",
        "/en/pago",
        "/en/soporte",
        "/en/calculadora",
        "/en/mapa-del-sitio",
        "/en/novedades",
        "/en/software-presupuestos",
        "/en/apu",
        "/en/remodelacion",
        "/en/legal/preguntas",
        "/en/legal/terminos",
        "/en/legal/privacidad",
        "/en/legal/soporte",
        "/en/legal/licencias",
    }
)


def _es_indexable_en(p: str) -> bool:
    """¿Es indexable una ruta con prefijo de idioma inglés?"""
    p_sin_query = p.split("?", 1)[0]
    ruta = p_sin_query.rstrip("/") or "/en"
    if ruta in _INDEXABLES_EN:
        return True
    if ruta.startswith("/en/guia/") and ruta.count("/") == 3:
        return True
    if ruta == "/en/prices-comparison" or (
        ruta.startswith("/en/prices-comparison/") and ruta.count("/") == 3
    ):
        return True
    if ruta == "/en/prices-comparison.json":
        return True
    # /en-mx/, /en-mx/apu ... (misma regla que el subdirectorio en español)
    m = re.match(r"^/en-([A-Za-z]{2})(?:/(.*))?$", ruta)
    if m:
        cc = m.group(1).lower()
        if cc not in {c.lower() for c in ORDEN_SELECTOR}:
            return False
        resto = (m.group(2) or "").strip("/")
        if not resto:
            return True
        if resto in TEMAS:
            return True
        # Guías y artículos del mercado: /en-gb/guia/... es la URL canónica
        # de los artículos británicos y sin esta rama quedarían en noindex.
        if re.match(r"^guia/[a-z0-9-]+$", resto):
            return True
        # Mismo catalogo con la URL inglesa: /en-gb/prices, /en-us/labour-rates
        if _es_indexable_precios(resto):
            return True
        return False
    return False


def hreflang_pais(codigo: str) -> str:
    """Etiqueta BCP-47 del mercado: «es-MX», «en-GB», «en-US».

    Se lee del registro porque el idioma es del mercado, no un prefijo:
    durante un tiempo esto devolvió «es-US» y el sitio anunció una versión
    en español de Estados Unidos que no existe.
    """
    codigo = str(codigo or "").strip().upper()
    pais = PAISES.get(codigo)
    if not pais:
        return "es"
    return str(pais.get("locale") or f"{pais.get('idioma', 'es')}-{codigo}")


def ruta_pais(codigo: str, tema: str = "") -> str:
    codigo = str(codigo or "").strip().lower()
    if not codigo:
        return f"/{tema}" if tema else "/"
    if tema:
        return f"/{codigo}/{tema}"
    return f"/{codigo}/"


def ruta_mercado(codigo: str, tema: str = "") -> str:
    """Ruta canónica de un mercado: /mx/apu o /en-gb/apu.

    Los mercados de habla inglesa viven bajo su prefijo (/en-us/, /en-gb/),
    porque su subdirectorio en español no existe: no hay una versión en
    español de la página de Estados Unidos.
    """
    codigo = str(codigo or "").strip().upper()
    pais = PAISES.get(codigo)
    if pais and pais.get("idioma") == "en":
        return ruta_en(codigo, tema)
    return ruta_pais(codigo, tema)


def enlaces_hreflang(request: Request | None = None, tema: str = "") -> list[dict]:
    """Pares hreflang para una página (home o tema) y sus equivalentes de país.

    Una entrada por mercado, con su locale y su ruta. Antes se emitían dos
    por país (es-XX y en-XX) como si todos tuvieran las dos versiones, y así
    se anunciaban variantes inexistentes como «es-US».
    """
    base = origen_canonico(request)
    # «en» apunta a la URL que de verdad se sirve, no a /en/, que es un 301 a
    # /en-us/. Un hreflang que resuelve en redirección se descarta en Search
    # Console y reparte la señal entre dos URLs.
    out = [
        {"hreflang": "x-default", "href": base + ruta_pais("", tema)},
        {"hreflang": "es", "href": base + ruta_pais("", tema)},
        {"hreflang": "en", "href": base + ruta_en("US", tema)},
    ]
    for pais in lista_paises():
        out.append(
            {
                "hreflang": hreflang_pais(pais["codigo"]),
                "href": base + ruta_mercado(pais["codigo"], tema),
            }
        )
    return out


def ruta_en(codigo: str = "", tema: str = "") -> str:
    """Ruta canónica en inglés: /en/, /en-mx/, /en/apu, /en-mx/apu.

    Espejo de :func:`ruta_pais` para el locale inglés. Sin barra final en
    tema (igual que en español) para no encadenar un 307 de ``redirect_slashes``
    que perdería el prefijo de idioma.
    """
    from .seo_en import _ruta_en as _ruta

    return _ruta(codigo, tema)


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

# Mismo ajuste para el copy en inglés: no se puede clavar «7 days free» si
# la prueba está apagada o dura 14 (sería publicidad falsa en ese mercado).
_RE_PRUEBA_EN = re.compile(
    r"(?:\s*[,.]?\s*)?(?:\d+\s+days(?:\s+free)?(?:\s*,?\s*no\s+card(?:\s+required)?)?\.?)",
    re.IGNORECASE,
)


def _aplicar_prueba(ficha: dict, lang: str = "es", incluir_prueba: bool = True) -> dict:
    """Ajusta description y FAQ al estado real de la prueba.

    ``incluir_prueba=False`` deja la descripción sin la coletilla
    comercial: en una guía o un artículo solo sirve para que Google
    corte la frase a mitad.
    """
    en = normalizar_idioma(lang) == "en"
    n = _dias_prueba_publicos()
    patron = _RE_PRUEBA_EN if en else _RE_PRUEBA
    desc = patron.sub("", str(ficha.get("description") or "")).strip()
    desc = re.sub(r"\s{2,}", " ", desc).rstrip(" .")
    # 160 y no 170: Google corta el snippet alrededor de los 155-160
    # caracteres en escritorio, y con la coletilla de la prueba una
    # descripción de 145 acababa en 168 y se veía partida.
    maximo = 160
    sufijo = ""
    if incluir_prueba is not False and n:
        sufijo = f". {n} days free, no card." if en else f". {n} días gratis, sin tarjeta."
    if sufijo:
        # Se recorta la base, no la coletilla: antes se cortaba el texto ya
        # unido y el snippet acababa en «7 días gratis, sin…».
        base = _recortar_a_palabra(desc, maximo - len(sufijo))
        ficha["description"] = base + sufijo
    else:
        ficha["description"] = _recortar_meta(desc + ".", maximo)

    faqs = []
    for item in ficha.get("faq") or []:
        q = str(item.get("q") or "")
        a = str(item.get("a") or "")
        ql = q.lower()
        al = a.lower()
        if en:
            habla_prueba = (
                "try it" in ql
                or "free trial" in al
                or "days free" in al
                or "days of full access" in al
            )
        else:
            habla_prueba = (
                "probarlo" in ql
                or "gratis" in al
                or "días de prueba" in al
                or "días de acceso" in al
            )
        if n is None and habla_prueba:
            continue
        if n:
            a = re.sub(r"\d+\s+days", f"{n} days", a) if en else re.sub(r"\d+\s+días", f"{n} días", a)
        faqs.append({**item, "q": q, "a": a})
    ficha["faq"] = faqs
    return ficha


# Palabras que no pueden quedar colgando al final de una descripción
# recortada: «…, sales.» (corte tras un nombre a mitad de sintagma) o
# «Unit price analysis and.» son el fallo que se evita aquí.
_CONECTORES_FINALES = frozenset(
    "and or the a an with for to in of on at by from "
    "y e o u con de en el la los las un una para por que del al su".split()
)


def _sin_conector_final(t: str) -> str:
    t = t.rstrip(" ,;·.")
    while True:
        ultimo = t.rfind(" ")
        if ultimo <= 0:
            return t
        palabra = t[ultimo + 1 :].strip(" ,;·.").lower()
        if palabra not in _CONECTORES_FINALES:
            return t
        t = t[:ultimo].rstrip(" ,;·.")


def _recortar_a_palabra(texto: str, maximo: int) -> str:
    """Recorta sin dejar palabras partidas y sin añadir puntos suspensivos.

    Se usa para la parte descriptiva cuando después va una coletilla fija:
    el resultado se une con ella y el conjunto cabe en el límite.
    """
    t = re.sub(r"\s{2,}", " ", str(texto or "").strip())
    if len(t) <= maximo:
        return t
    corte = t[:maximo]
    ultimo = corte.rfind(" ")
    if ultimo > maximo * 0.5:
        corte = corte[:ultimo]
    return _sin_conector_final(corte.rstrip(" ,;·."))


def _recortar_meta(texto: str, maximo: int = 160) -> str:
    """Recorta una meta description sin dejar palabras partidas."""
    t = re.sub(r"\s{2,}", " ", str(texto or "").strip())
    if len(t) <= maximo:
        return t
    corte = t[:maximo]
    ultimo = max(corte.rfind(" "), corte.rfind(","))
    if ultimo > maximo * 0.6:
        corte = corte[:ultimo]
    return _sin_conector_final(corte.rstrip(" ,;·").rstrip()) + "…"


#: Ancho útil del título en un resultado de Google (≈600 px). Pasarse no
#: penaliza, pero lo que sobra se sustituye por «…» justo donde iba el país,
#: que es la parte que hace clic en una búsqueda local.
MAX_TITULO = 60

#: Versiones cortas del oficio, para que el país quepa en el título.
_OFICIO_CORTO = {
    "software de presupuestos de construcción": "software de presupuestos",
    "software de APU y análisis de precios unitarios": "software de APU",
    "software de presupuestos de remodelación": "software de remodelación",
}


def titulo_publico(oficio: str, donde: str = "") -> str:
    """Título de Google: marca primero, oficio después, país al final.

    Quien busca «CotizaT» o ve el snippet tiene que leer de un vistazo qué es
    (software de presupuestos de construcción/obra), no un nombre suelto.
    Si con la marca no cabe el país («…en República Dominicana» son 21
    caracteres más), se acorta el oficio y, en último caso, se sacrifica la
    marca: el país es la señal que Google usa para la búsqueda local y el
    nombre propio aún no lo busca nadie.
    """
    oficio = str(oficio or "").strip().rstrip(".")
    donde = str(donde or "").strip()
    corto = _OFICIO_CORTO.get(oficio, oficio)
    if donde:
        candidatos = [
            f"{PRODUCT_NAME}: {oficio} en {donde}",
            f"{PRODUCT_NAME}: {corto} en {donde}",
            f"{corto} en {donde}",
        ]
    else:
        candidatos = [f"{PRODUCT_NAME}: {oficio}", f"{PRODUCT_NAME}: {corto}"]
    for candidato in candidatos:
        if len(candidato) <= MAX_TITULO:
            return candidato
    return candidatos[-1]


# ---------------------------------------------------------------------------
# Copy de la landing por país (title descriptivo, description ≈ 155, H1 único)
# ---------------------------------------------------------------------------

_LANDING: dict[str, dict] = {
    "": {
        "title": "CotizaT: software de presupuestos de construcción",
        "description": (
            "Presupuestos de construcción para España, Latinoamérica y mercados "
            "de habla inglesa. Catálogo y fiscalidad por país, APU y PDF."
        ),
        "h1": (
            "Software de presupuestos de obra para España, Latinoamérica y "
            "mercados de habla inglesa"
        ),
        "h1_resalte": "margen, tiempos y cierre",
        "sub": (
            "CotizaT convierte tu catálogo y tus precios en presupuestos de obra "
            "claros, con coste interno, beneficio y horas de cuadrilla. España en "
            "EUR con NIF e IVA 21 %; Latinoamérica con su moneda y su fiscalidad; "
            "Reino Unido en libras con CIS e IVA por tipo de obra; Estados Unidos, "
            "Australia, Irlanda y Canadá con su impuesto, su ID fiscal y su "
            "terminología. PDF con tu logo, listo para WhatsApp."
        ),
        "kicker": (
            "Sistema comercial para España, Latinoamérica, Reino Unido, Estados "
            "Unidos, Australia, Irlanda y Canadá · Construcción y reformas"
        ),
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
                "q": "¿CotizaT sirve también para Reino Unido o Estados Unidos?",
                "a": (
                    "Sí. Reino Unido tiene catálogo en libras, retenciones CIS "
                    "(20 %, 30 % o 0 %) e IVA según el tipo de obra, incluida la "
                    "inversión del sujeto pasivo. Estados Unidos, Australia, Irlanda "
                    "y Canadá tienen su moneda, su impuesto (sales tax, GST/HST, VAT "
                    "irlandés) y el vocabulario de obra de cada país. Eliges mercado "
                    "al entrar y el documento sale con su moneda y su fiscalidad."
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


def ficha_landing(codigo: str = "", lang: str = "es") -> dict:
    """Copy SEO de la landing (genérica o de un país del selector).

    Con ``lang='en'`` devuelve el copy en inglés y la canónica en ``/en/``
    (o ``/en-xx/``), que es la URL que realmente se está sirviendo.
    """
    from .seo_articulos import articulo_de_pais, articulos_de_pais
    from .seo_contenido import cuerpo_pais, lista_guias

    codigo = str(codigo or "").strip().upper()
    lang = normalizar_idioma(lang)
    pais = PAISES.get(codigo) or PAIS_GENERICO
    # En inglés el país se nombra en inglés: «Estados Unidos» en un H2 en
    # inglés delata que el dato venía del registro en español.
    nombre_pais = (
        (pais.get("nombre_en") or pais.get("nombre") or "the United States")
        if lang == "en"
        else (pais.get("nombre") or "Latinoamérica")
    )

    if lang == "en":
        from .seo_en import landing_en as _landing_en
        from .seo_articulos import articulo_de_pais as _articulo_de_pais

        base = _landing_en(codigo)
        cuerpo: list = []
        articulos: list = []
        if codigo == "GB":
            # Reino Unido tiene además artículos de cola larga con URL propia.
            from .seo_reino_unido import cuerpo_landing, guias as _guias_uk

            cuerpo = cuerpo_landing()
            articulos = [
                {"h1": a["h1"], "ruta": f"/en-gb/guia/{a['slug']}"}
                for a in _guias_uk()
            ]
        else:
            # Estados Unidos, Australia, Canadá e Irlanda: sin cuerpo propio
            # sus landings eran la misma página con el nombre cambiado.
            # También tienen artículos de cola larga con URL propia, como
            # Reino Unido (seo_articulos_mercados_en).
            from .seo_mercados_en import cuerpo_landing as _cuerpo_mercado
            from .seo_articulos_mercados_en import guias_de, ruta_articulo

            cuerpo = _cuerpo_mercado(codigo)
            articulos = [
                {"h1": a["h1"], "ruta": ruta_articulo(codigo, a["slug"])}
                for a in guias_de(codigo)
            ]
        return _aplicar_prueba(
            {
                **base,
                "codigo": codigo,
                "lang": f"en-{codigo}" if codigo else "en",
                "nombre_pais": nombre_pais,
                "tema": "",
                "canonical_path": ruta_en(codigo),
                "cuerpo": cuerpo,
                "guias": articulos,
                "articulo": _articulo_de_pais(codigo, lang="en") if codigo else None,
            },
            lang="en",
        )

    base = _LANDING.get(codigo) or _LANDING[""]
    return _aplicar_prueba(
        {
            **base,
            "codigo": codigo,
            "lang": hreflang_pais(codigo) if codigo else "es",
            "nombre_pais": nombre_pais,
            "tema": "",
            "canonical_path": ruta_pais(codigo),
            "cuerpo": cuerpo_pais(codigo),
            "guias": lista_guias(),
            # Todos los artículos del silo, no solo el primero. España abre
            # la estrategia profunda con tres intenciones distintas.
            "articulos_mercado": [
                {**articulo, "ruta": f"/{codigo.lower()}/guia/{articulo['slug']}"}
                for articulo in articulos_de_pais(codigo)
            ],
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
    impuesto = pais.get("etiqueta_impuesto") or "IVA"
    vocab = pais.get("vocab") or ""
    ciudad = pais.get("ciudad_ejemplo") or ""

    if tema == "software-presupuestos":
        # El hub genérico no puede repetir el <title> de la home: son dos
        # URLs distintas compitiendo por la misma consulta de marca y Google
        # termina eligiendo una y marcando la otra como duplicada.
        title = (
            titulo_publico(
                "software de presupuestos de construcción",
                nombre,
            )
            if codigo
            else "CotizaT: software de presupuestos de obra con APU y margen"
        )
        h1 = f"Software de presupuestos de construcción en {nombre}"
        lead = (
            f"CotizaT es el software de presupuestos de construcción y remodelación "
            f"para empresas de {nombre}. Catálogo con análisis de precios unitarios, "
            f"{fiscal}, {impuesto} {iva:g} % y moneda {moneda}. PDF profesional para WhatsApp."
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

    from .seo_articulos import articulos_de_pais
    from .seo_contenido import extra_hub, faq_hub

    body = list(body) + extra_hub(codigo, tema)
    for art in articulos_de_pais(codigo):
        related = list(related) + [
            (art["h1"], f"/{codigo.lower()}/guia/{art['slug']}")
        ]
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
        "description": _recortar_meta(description, 155),
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


def ficha_tema(codigo: str, tema: str, lang: str = "es") -> dict | None:
    codigo = str(codigo or "").strip().upper()
    tema = str(tema or "").strip().lower()
    lang = normalizar_idioma(lang)
    if tema not in TEMAS:
        return None
    if codigo and codigo not in ORDEN_SELECTOR:
        return None

    if lang == "en":
        from .seo_en import tema_en as _tema_en
        from .seo_en import _datos

        bloques = _tema_en(codigo, tema)
        if bloques is None:
            return None
        datos = _datos(codigo)
        return _aplicar_prueba(
            {
                **bloques,
                "codigo": codigo,
                "lang": f"en-{codigo}" if codigo else "en",
                "nombre_pais": datos["nombre"],
                "tema": tema,
                "canonical_path": ruta_en(codigo, tema),
                "vocab": datos["vocabulario"],
                "moneda": datos["moneda_txt"],
                "iva": datos["iva_txt"],
                "id_fiscal": datos["fiscal_txt"],
            },
            lang="en",
        )

    return _bloques_tema(codigo, tema)


def jsonld_organizacion(request: Request | None = None, lang: str = "es") -> dict:
    origen = origen_canonico(request)
    # Los países se nombran en el idioma de la página: un schema en inglés
    # que anuncia «areaServed: Estados Unidos» mezcla los dos idiomas.
    clave_pais = "nombre_en" if lang == "en" else "nombre"
    return {
        "@context": "https://schema.org",
        "@id": origen + "/#organization",
        "@type": "Organization",
        "name": PRODUCT_NAME,
        "legalName": PRODUCT_NAME + " · Presupuestos",
        "url": origen + "/",
        "logo": {
            "@type": "ImageObject",
            "url": origen + "/static/icono-512.png",
            "width": 512,
            "height": 512,
        },
        "image": origen + OG_IMAGE,
        "email": "soporte@cotizat.online",
        "description": value_proposition(lang),
        "areaServed": [{"@type": "Country", "name": PAISES[c][clave_pais]} for c in ORDEN_SELECTOR],
        "contactPoint": {
            "@type": "ContactPoint",
            "email": "soporte@cotizat.online",
            "contactType": "customer support",
            "availableLanguage": ["es", "en"],
        },
    }


def jsonld_website(request: Request | None = None, lang: str = "es") -> dict:
    origen = origen_canonico(request)
    return {
        "@context": "https://schema.org",
        "@id": origen + "/#website",
        "@type": "WebSite",
        "name": PRODUCT_NAME,
        "url": origen + "/",
        "inLanguage": ["es", "es-VE", "es-CO", "es-MX", "es-PE", "es-EC", "es-PA", "es-SV", "es-CL", "es-AR", "es-DO", "es-UY", "es-PY", "es-BO", "es-CR", "es-GT", "es-HN", "es-NI", "es-ES", "en", "en-US", "en-GB"],
        "publisher": {"@id": origen + "/#organization"},
        "description": value_proposition(lang),
    }


def jsonld_software(request: Request | None = None, codigo: str = "", lang: str = "es") -> dict:
    origen = origen_canonico(request)
    lang = normalizar_idioma(lang)
    en = lang == "en"
    pais = PAISES.get(str(codigo or "").upper())
    # El país se nombra en el idioma de la página: un schema en inglés que
    # anuncia «Reino Unido» delata que el dato viene del registro español.
    clave_area = "nombre_en" if en else "nombre"

    def _area(codigo: str) -> dict:
        # ``nombre_en`` está escrito para fluir en una frase («the United
        # Kingdom»); en schema, el nombre del país va sin artículo.
        nombre = (PAISES[codigo].get(clave_area) or PAISES[codigo]["nombre"]).strip()
        if nombre.lower().startswith("the "):
            nombre = nombre[4:]
        return {"@type": "Country", "name": nombre}

    if pais:
        area = _area(str(codigo).upper())
    else:
        # La home genérica no es un país: «Latinoamérica» no es un Country y
        # Search Console lo marcaba como área no válida. Se enumeran los
        # mercados reales, que es lo que el producto cubre de verdad.
        area = [_area(c) for c in ORDEN_SELECTOR]
    if en:
        url_app = origen + ruta_en(codigo)
        url_precio = origen + "/en/pago"
    else:
        url_app = origen + ruta_pais(codigo)
        url_precio = origen + "/pago"
    return {
        "@context": "https://schema.org",
        "@id": url_app + "#software",
        "@type": "SoftwareApplication",
        "name": PRODUCT_NAME,
        "applicationCategory": "BusinessApplication",
        "operatingSystem": "Web",
        "description": value_proposition(lang),
        "url": url_app,
        "image": origen + OG_IMAGE,
        "offers": {
            "@type": "Offer",
            "price": "89.00",
            "priceCurrency": "USD",
            "availability": "https://schema.org/InStock",
            "url": url_precio,
        },
        "areaServed": area,
        "inLanguage": (f"en-{codigo}" if codigo else "en") if en else (hreflang_pais(codigo) if codigo else "es"),
        "brand": {"@type": "Brand", "name": PRODUCT_NAME},
        "featureList": (
            [
                "Construction and remodeling estimates",
                "Unit price analysis (UPA)",
                "Professional PDF ready for WhatsApp",
            ]
            if en
            else [
                "Presupuestos de construcción y remodelación",
                "Análisis de precios unitarios (APU)",
                "PDF profesional para WhatsApp",
            ]
        ),
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


def jsonld_planes(request: Request | None = None, lang: str = "es") -> dict:
    """La suscripción como ``Product`` con ``AggregateOffer``, en /pago.

    A diferencia del catálogo de precios —donde se evita a propósito el
    markup de oferta porque no hay nada que comprar— aquí sí hay una
    compra real: dos planes con importe, moneda y URL de compra. Es la
    única página del sitio con derecho a ese markup, y el resultado
    enriquecido muestra el precio en el resultado de búsqueda, que es
    justo lo que separa un clic de un salto a la competencia.
    """
    from .datos_pago import PLANES

    origen = origen_canonico(request)
    en = lang == "en"
    ruta = "/en/pago" if en else "/pago"
    nombre_planes = {
        "anual": "Annual plan" if en else "Plan anual",
        "mensual": "Monthly plan" if en else "Plan mensual",
    }
    ofertas = []
    for clave, plan in PLANES.items():
        ofertas.append(
            {
                "@type": "Offer",
                "name": nombre_planes.get(clave, plan["nombre"]),
                "price": f"{float(plan['importe']):.2f}",
                "priceCurrency": "USD",
                "availability": "https://schema.org/InStock",
                "url": origen + ruta,
                "itemOffered": {"@id": origen + ruta + "#product"},
            }
        )
    importes = sorted(float(p["importe"]) for p in PLANES.values())
    return {
        "@context": "https://schema.org",
        "@id": origen + ruta + "#product",
        "@type": "Product",
        "name": (
            "CotizaT — construction estimating software"
            if en
            else "CotizaT — software de presupuestos de construcción"
        ),
        "description": value_proposition(lang),
        "image": origen + OG_IMAGE,
        "url": origen + ruta,
        "brand": {"@type": "Brand", "name": PRODUCT_NAME},
        "category": "BusinessApplication" if en else "Software de presupuestos",
        "offers": {
            "@type": "AggregateOffer",
            "priceCurrency": "USD",
            "lowPrice": f"{importes[0]:.2f}",
            "highPrice": f"{importes[-1]:.2f}",
            "offerCount": len(ofertas),
            "offers": ofertas,
        },
    }


def jsonld_webpage(
    request: Request | None,
    path: str,
    title: str,
    description: str = "",
    page_type: str = "WebPage",
    lang: str = "es",
) -> dict:
    """Schema WebPage para una página individual.

    Google lo usa para entender la jerarquía del sitio y la relación
    entre la WebSite y cada página indexable.
    """
    origen = origen_canonico(request)
    data: dict = {
        "@context": "https://schema.org",
        "@type": page_type,
        "name": title,
        "url": origen + path,
        "isPartOf": {"@id": origen + "/#website"},
        "inLanguage": (lang or "es"),
        "dateModified": SITEMAP_LASTMOD,
    }
    if description:
        data["description"] = description
    return data


def jsonld_howto(guia: dict, request: Request | None = None, lang: str = "es") -> dict:
    origen = origen_canonico(request)
    idioma = normalizar_idioma(lang)
    pais_guia = str(guia.get("pais") or "").strip().upper()
    mercado = PAISES.get(pais_guia) or {}
    locale = hreflang_pais(pais_guia) if mercado.get("idioma") == idioma else idioma
    pasos = []
    for i, (titulo, pars) in enumerate(guia.get("secciones") or [], start=1):
        # Las tablas ya son visibles en el HTML, pero serializar su dict como
        # texto produciría un HowToStep ilegible y distinto de lo que ve el
        # usuario. El schema conserva solo los párrafos narrativos.
        texto = " ".join(p for p in (pars or []) if isinstance(p, str) and p).strip()
        paso: dict = {"@type": "HowToStep", "position": i, "name": titulo}
        if texto:
            paso["text"] = texto
        pasos.append(paso)
    return {
        "@context": "https://schema.org",
        "@type": "HowTo",
        "name": guia["h1"],
        "description": guia["description"],
        "url": origen + _ruta_guia(guia["slug"], idioma),
        "inLanguage": locale,
        "step": pasos,
    }


def _ruta_guia(slug: str, lang: str = "es") -> str:
    """Ruta canónica de una guía genérica o de mercado.

    Las guías de método viven en ``/guia/x`` o ``/en/guia/x``. Un artículo
    de país vive dentro de su silo: ``/es/guia/x`` o ``/en-gb/guia/x``. Así
    la URL, las migas, los enlaces y el sitemap expresan la misma entidad.
    """
    idioma = normalizar_idioma(lang)
    from .seo_articulos import ficha_articulo

    articulo = ficha_articulo(slug, idioma) or {}
    pais = str(articulo.get("pais") or "").strip().upper()
    mercado = PAISES.get(pais) or {}
    if pais and mercado.get("idioma") == idioma:
        if idioma == "en":
            return f"/en-{pais.lower()}/guia/{slug}"
        return f"/{pais.lower()}/guia/{slug}"
    if idioma == "en":
        return f"/en/guia/{slug}"
    return f"/guia/{slug}"


def ruta_guia(slug: str, lang: str = "es") -> str:
    """API pública para enlazado interno y pruebas."""
    return _ruta_guia(slug, lang)


def _articulos_en_para_enlazar(pais: str = "") -> list[dict]:
    """Artículos en inglés que se enlazan al pie de una guía en inglés.

    Con cinco mercados publicando artículos, enlazar los dieciséis al pie de
    cada guía sería una granja de enlaces: se enlazan los del propio
    mercado (máximo seis) y, si la guía no es de mercado, los genéricos.
    """
    from .seo_articulos import lista_articulos_en

    pais = str(pais or "").strip().upper()
    todos = lista_articulos_en()
    if pais:
        propios = [a for a in todos if str(a.get("pais") or "").upper() == pais]
        if propios:
            return propios[:6]
    return todos[:6]


def jsonld_articulo(guia: dict, request: Request | None = None, lang: str = "es") -> dict:
    origen = origen_canonico(request)
    lang = normalizar_idioma(lang)
    path = _ruta_guia(guia["slug"], lang)
    locale = lang
    pais_articulo = str(guia.get("pais") or "").strip().upper()
    mercado_articulo = PAISES.get(pais_articulo) or {}
    if pais_articulo and mercado_articulo.get("idioma") == lang:
        locale = hreflang_pais(pais_articulo)
    return {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": guia["h1"],
        "description": guia["description"],
        "inLanguage": locale,
        "url": origen + path,
        "mainEntityOfPage": origen + path,
        "datePublished": SITEMAP_LASTMOD,
        "dateModified": SITEMAP_LASTMOD,
        "author": {"@id": origen + "/#organization"},
        "publisher": {"@id": origen + "/#organization"},
        "image": origen + OG_IMAGE,
    }


def contexto_guia(request: Request, slug: str) -> dict | None:
    from .paises import lista_paises
    from .seo_articulos import lista_articulos
    from .seo_contenido import ficha_guia, lista_guias
    lang = "es"
    try:
        lang = getattr(getattr(request, "state", None), "lang", "es") or "es"
    except Exception:
        lang = "es"
    lang = normalizar_idioma(lang)

    guia = ficha_guia(slug, lang=lang)
    if not guia:
        return None
    origen = origen_canonico(request)
    path = _ruta_guia(guia["slug"], lang)
    en = lang == "en"
    pais_guia = str(guia.get("pais") or "").strip().upper()
    mercado_guia = PAISES.get(pais_guia) if pais_guia else None
    # Un artículo de mercado se anuncia con su locale exacto (es-ES, en-GB)
    # y no inventa traducciones. Solo es de mercado en el idioma nativo de
    # ese país; la traducción histórica de un artículo colombiano sigue en
    # el hub inglés genérico y no suplanta una URL en-CO.
    mercado_especifico = bool(mercado_guia and mercado_guia.get("idioma") == lang)
    locale = hreflang_pais(pais_guia) if mercado_especifico else ("en" if en else "es")
    if mercado_especifico:
        prefijo = f"/en-{pais_guia.lower()}" if en else f"/{pais_guia.lower()}"
    else:
        prefijo = "/en" if en else ""
    seo = _aplicar_prueba(
        {
            "title": guia["title"],
            "description": guia["description"],
            # El locale del mercado (en-GB) y no el idioma a secas: la
            # plantilla lo usa en <html lang> y en og:locale.
            "lang": locale,
            "h1": guia["h1"],
            "canonical_path": path,
            "faq": list(guia.get("faq") or []),
        },
        lang=lang,
        incluir_prueba=False,
    )
    if en:
        crumbs = [("Home", ruta_en("US"))]
        if mercado_especifico:
            crumbs.append((str(guia.get("pais_nombre") or pais_guia), prefijo + "/"))
        crumbs.extend([("Guides", "/en/mapa-del-sitio"), (guia["h1"], path)])
    else:
        crumbs = [("Inicio", "/")]
        if mercado_especifico:
            crumbs.append((str(guia.get("pais_nombre") or pais_guia), prefijo + "/"))
        crumbs.extend([("Guías", "/mapa-del-sitio"), (guia["h1"], path)])
    bloques = [
        jsonld_organizacion(request, lang=lang),
        jsonld_website(request, lang=lang),
        # WebPage, no Article: el Article completo lo emite jsonld_articulo()
        # unas líneas más abajo. Dos nodos Article para la misma URL con
        # fechas y autores distintos es schema duplicado y contradictorio.
        jsonld_webpage(request, path, guia["h1"], guia["description"], "WebPage", lang=locale),
        jsonld_articulo(guia, request, lang=lang),
        jsonld_breadcrumb(request, crumbs),
    ]
    # HowTo solo donde el documento es realmente un procedimiento. Las guías
    # pilar lo son; los artículos de mercado deben declararlo explícitamente.
    if (not mercado_especifico) or bool(guia.get("schema_howto")):
        bloques.append(jsonld_howto(guia, request, lang=lang))
    if seo["faq"]:
        bloques.append(jsonld_faq(seo["faq"]))
    if mercado_especifico and en:
        # Artículo de mercado en su idioma (en-GB): no tiene versión en
        # español, así que se declara con su locale y x-default.
        hreflang = [
            {"hreflang": locale, "href": origen + path},
            {"hreflang": "x-default", "href": origen + path},
        ]
    elif mercado_especifico:
        hreflang = enlaces_guia(guia["slug"], origen)
    else:
        hreflang = enlaces_guia(guia["slug"], origen)
    # Enlaces al catálogo de precios del mercado (Fase 5): las guías son las
    # páginas que primero rankean y no enlazaban a ninguna de las 47.000.
    catalogo = None
    if pais_guia:
        from .seo_precios import enlaces_catalogo

        catalogo = enlaces_catalogo(pais_guia, guia["slug"])
    return {
        "seo": seo,
        "guia": guia,
        "catalogo_precios": catalogo,
        "guias": lista_guias(),
        "guias_en": (
            [
                {"h1": a["h1"], "ruta": _ruta_guia(a["slug"], "en")}
                for a in _articulos_en_para_enlazar(pais_guia)
                if a.get("slug") != guia.get("slug")
            ]
            if en
            else []
        ),
        "articulos": lista_articulos(),
        "paises": lista_paises(),
        "origen_seo": origen,
        "canonical_url": origen + path,
        "hreflang_links": hreflang,
        "og_image": origen + OG_IMAGE,
        "jsonld_bloques": bloques,
        "seo_temas": TEMAS,
        # Prefijo de idioma del artículo. La plantilla no puede deducirlo de
        # la URL porque el middleware ya la ha reescrito.
        "prefijo_guia": prefijo or ("/en" if en else ""),
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
    lang = "es"
    try:
        lang = getattr(getattr(request, "state", None), "lang", "es") or "es"
    except Exception:
        lang = "es"
    lang = normalizar_idioma(lang)
    ficha = (
        ficha_tema(codigo, tema, lang=lang)
        if tema
        else ficha_landing(codigo, lang=lang)
    )
    if ficha is None:
        ficha = ficha_landing(codigo, lang=lang)
    origen = origen_canonico(request)
    canonical = origen + ficha["canonical_path"]
    og_image = origen + OG_IMAGE
    en = lang == "en"
    bloques_ld = [
        jsonld_organizacion(request, lang=lang),
        jsonld_website(request, lang=lang),
        # inLanguage con el locale del mercado (en-GB, es-MX), no con el
        # idioma a secas: es lo que declara la página en <html lang>.
        jsonld_webpage(
            request,
            ficha["canonical_path"],
            ficha["h1"],
            ficha.get("description", ""),
            lang=ficha.get("lang") or lang,
        ),
        jsonld_software(request, codigo, lang=lang),
    ]
    if ficha.get("faq"):
        bloques_ld.append(jsonld_faq(ficha["faq"]))
    if en:
        crumbs = [("Home", ruta_en(""))]
        if codigo:
            crumbs.append((ficha["nombre_pais"], ruta_en(codigo)))
        if tema:
            crumbs.append((ficha["h1"], ficha["canonical_path"]))
    else:
        crumbs = [("Inicio", "/")]
        if codigo:
            crumbs.append((ficha["nombre_pais"], ruta_pais(codigo)))
        if tema:
            crumbs.append((ficha["h1"], ficha["canonical_path"]))
    bloques_ld.append(jsonld_breadcrumb(request, crumbs))
    catalogo = None
    if codigo:
        from .seo_precios import enlaces_catalogo

        catalogo = enlaces_catalogo(codigo, f"{codigo}-{tema}")
    return {
        "seo": ficha,
        "catalogo_precios": catalogo,
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
    "contacto": {
        "path": "/soporte",
        "title": "Soporte de CotizaT: escríbenos y te contestamos",
        "description": (
            "Formulario de soporte de CotizaT: dudas, problemas, quejas o "
            "sugerencias sobre el software de presupuestos. Respuesta por "
            "correo en menos de 24 horas laborables."
        ),
        "h1": "Soporte",
        "software": False,
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
    "novedades": {
        "path": "/novedades",
        "title": "CotizaT: novedades y changelog del software de presupuestos",
        "description": (
            "Novedades y versiones de CotizaT: mejoras del software de "
            "presupuestos de construcción, rendimiento y nuevas funciones."
        ),
        "h1": "Novedades y versiones",
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

    lang = "es"
    try:
        lang = getattr(getattr(request, "state", None), "lang", "es") or "es"
    except Exception:
        lang = "es"
    lang = normalizar_idioma(lang)

    en = lang == "en"
    ficha_en = None
    if en:
        from .seo_en import pagina_estatica_en

        ficha_en = pagina_estatica_en(clave)
    ficha = ficha_en or _PAGINAS_ESTATICAS[clave]
    origen = origen_canonico(request)
    path = ficha["path"]
    seo = _aplicar_prueba(
        {
            "title": ficha["title"],
            "description": ficha["description"],
            "lang": lang,
            "h1": ficha["h1"],
            "canonical_path": path,
            "faq": [] if en else (FAQ_LEGAL if clave == "preguntas" else []),
            "nombre_pais": "Latin America" if en else "Latinoamérica",
        },
        lang=lang,
    )
    bloques = [
        jsonld_organizacion(request, lang=lang),
        jsonld_website(request, lang=lang),
        jsonld_webpage(request, path, ficha["h1"], ficha["description"], lang=lang),
    ]
    if ficha.get("software"):
        bloques.append(jsonld_software(request, "", lang=lang))
    if clave == "pago":
        # Única página con oferta comprable: los dos planes, con importe y
        # moneda reales. El catálogo de precios NO lleva este markup.
        bloques.append(jsonld_planes(request, lang=lang))
    if seo.get("faq"):
        bloques.append(jsonld_faq(seo["faq"]))
    if en:
        crumbs = [("Home", ruta_en("")), (ficha["h1"], path)]
    else:
        crumbs = [("Inicio", "/"), (ficha["h1"], path)]
    bloques.append(jsonld_breadcrumb(request, crumbs))
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

    def add(path: str, priority: str, changefreq: str, tema: str = "", alts: list | None = None) -> None:
        loc = base + path
        # hreflang solo donde hay equivalente real en el otro idioma:
        # home (genérica y de país) y hubs de intención.
        if alts is None:
            alts = enlaces_hreflang(request, tema) if _sitemap_con_hreflang(path, tema) else []
        out.append(
            {
                "loc": loc,
                "lastmod": SITEMAP_LASTMOD,
                "changefreq": changefreq,
                "priority": priority,
                "alternates": alts,
            }
        )

    add("/", "1.0", "weekly")
    # Una sola URL por mercado: la canónica. /gb/ y /en/ son redirecciones
    # 301 a /en-gb/ y /en-us/, y un sitemap no debe anunciar redirecciones
    # (Search Console las marca como «página con redirección» y la autoridad
    # se reparte entre dos URLs).
    for codigo in ORDEN_SELECTOR:
        add(ruta_mercado(codigo), "0.9", "weekly")
    for tema in TEMAS:
        add(ruta_pais("", tema), "0.8", "monthly", tema)
        add(f"/en/{tema}", "0.8", "monthly", tema)
        for codigo in ORDEN_SELECTOR:
            add(ruta_mercado(codigo, tema), "0.8", "monthly", tema)
    # Páginas sueltas con traducción: par es/en explícito.
    for ruta, prio, freq in (
        ("como-funciona", "0.7", "monthly"),
        # Herramienta gratuita: la página con más intención de uso del sitio
        # y la que reparte autoridad a los 47.000 precios.
        ("calculadora", "0.8", "weekly"),
        ("pago", "0.6", "monthly"),
        ("soporte", "0.4", "monthly"),
        ("mapa-del-sitio", "0.4", "monthly"),
        ("novedades", "0.4", "monthly"),
    ):
        ruta_es, ruta_en = f"/{ruta}", f"/en/{ruta}"
        pares = [
            {"hreflang": "es", "href": base + ruta_es},
            {"hreflang": "en", "href": base + ruta_en},
        ]
        add(ruta_es, prio, freq, alts=pares)
        add(ruta_en, prio, freq, alts=pares)
    # Comparador internacional de precios: portada + una página por capítulo de
    # obra, en los dos idiomas. Es el único contenido del sitio que compara los
    # 22 mercados entre sí, y la página que puede captar búsquedas del tipo
    # «precio de la construcción en X vs Y».
    from .comparador import capitulos_publicados, ruta_capitulo, ruta_comparador

    pares_cmp = [
        {"hreflang": "es", "href": base + ruta_comparador("es")},
        {"hreflang": "en", "href": base + ruta_comparador("en")},
    ]
    add(ruta_comparador("es"), "0.9", "weekly", alts=pares_cmp)
    add(ruta_comparador("en"), "0.9", "weekly", alts=pares_cmp)
    for codigo in capitulos_publicados():
        ruta_es = ruta_capitulo("es", codigo)
        ruta_en = ruta_capitulo("en", codigo)
        pares_cap = [
            {"hreflang": "es", "href": base + ruta_es},
            {"hreflang": "en", "href": base + ruta_en},
        ]
        add(ruta_es, "0.7", "monthly", alts=pares_cap)
        add(ruta_en, "0.7", "monthly", alts=pares_cap)

    # Guías pilar (sin país) y artículos de mercado (dentro de su silo) son
    # dos arquitecturas distintas. No se publican artículos españoles bajo
    # /guia/: esa URL histórica redirige a /es/guia/… y no entra al sitemap.
    from .seo_contenido import lista_guias

    for guia in lista_guias():
        add(f"/guia/{guia['slug']}", "0.7", "monthly")

    from .seo_articulos import lista_articulos

    for articulo in lista_articulos():
        pais_articulo = str(articulo.get("pais") or "").strip().upper()
        mercado = PAISES.get(pais_articulo) or {}
        if mercado.get("idioma") != "es":
            continue
        ruta = _ruta_guia(articulo["slug"], "es")
        add(ruta, "0.7", "monthly", alts=enlaces_guia(articulo["slug"], base))
    # Pares es/en de guías traducidas. La ruta española NO siempre es
    # /guia/x: un artículo de mercado vive en su silo (/co/guia/x) y su
    # traducción en el hub inglés (/en/guia/x). Se declaran ambas en los dos
    # sentidos y con x-default (la española); un hreflang de un solo sentido
    # lo descarta Google.
    try:
        from .seo_contenido import GUIAS_EN

        slugs_traducidos = list(GUIAS_EN) + [
            articulo["slug"]
            for articulo in lista_articulos()
            if _tiene_version_en(articulo["slug"])
            and (
                (PAISES.get(str(articulo.get("pais") or "").upper()) or {}).get(
                    "idioma"
                )
                != "en"
            )
        ]
        for slug in dict.fromkeys(slugs_traducidos):
            pares = enlaces_guia(slug, base)
            for ruta in (_ruta_guia(slug, "es"), f"/en/guia/{slug}"):
                existente = next((o for o in out if o["loc"] == base + ruta), None)
                if existente is None:
                    add(ruta, "0.7", "monthly", alts=pares)
                else:
                    existente["alternates"] = pares
    except Exception:
        pass
    # Artículos de mercado con URL propia (/en-gb/guia/...). No tienen
    # versión en español, así que se declaran con su locale y x-default, no
    # como par es/en.
    try:
        from .seo_articulos import lista_articulos_en

        for articulo in lista_articulos_en():
            # Solo artículos de mercado anglófono (GB/US/IE/AU/CA): son los
            # que tienen URL propia bajo su prefijo (/en-gb/guia/...). Las
            # traducciones de artículos hispanos se anuncian por la vía de
            # /en/guia/, no duplicadas aquí.
            _pais_art = PAISES.get(str(articulo.get("pais") or "").upper()) or {}
            if _pais_art.get("idioma") != "en":
                continue
            ruta = _ruta_guia(articulo["slug"], "en")
            if any(o["loc"] == base + ruta for o in out):
                continue
            locale_art = hreflang_pais(articulo["pais"])
            alts = [
                {"hreflang": locale_art, "href": base + ruta},
                {"hreflang": "x-default", "href": base + ruta},
            ]
            add(ruta, "0.7", "monthly", alts=alts)
    except Exception:
        pass
    for legal in ("preguntas", "terminos", "privacidad", "soporte", "licencias"):
        ruta_es = f"/legal/{legal}"
        ruta_en = f"/en/legal/{legal}"
        pares = [
            {"hreflang": "es", "href": base + ruta_es},
            {"hreflang": "en", "href": base + ruta_en},
        ]
        add(ruta_es, "0.3", "yearly", alts=pares)
        add(ruta_en, "0.3", "yearly", alts=pares)
    return out


def enlaces_guia(slug: str, origen: str) -> list[dict]:
    """hreflang de una guía o artículo: español (con su locale), inglés y x-default.

    Fuente única para el <head> y para el sitemap: si divergen, Search
    Console marca el hreflang como incoherente y descarta el par.

    - Guía pilar: ``es`` ↔ ``en`` en /guia/x y /en/guia/x.
    - Artículo de mercado: ``es-CO`` (o el locale del mercado) en su silo
      /co/guia/x ↔ ``en`` en /en/guia/x, que es donde vive su traducción.
    - x-default apunta siempre a la española, que es la que existe.
    """
    from .seo_articulos import ficha_articulo

    articulo = ficha_articulo(slug, "es") or {}
    pais_art = str(articulo.get("pais") or "").strip().upper()
    mercado_art = PAISES.get(pais_art) or {}
    locale_es = hreflang_pais(pais_art) if mercado_art.get("idioma") == "es" else "es"
    ruta_es = origen + _ruta_guia(slug, "es")
    salida = [{"hreflang": locale_es, "href": ruta_es}]
    if _tiene_version_en(slug):
        salida.append({"hreflang": "en", "href": origen + f"/en/guia/{slug}"})
    salida.append({"hreflang": "x-default", "href": ruta_es})
    return salida


def _tiene_version_en(slug: str) -> bool:
    """¿Este artículo hispano tiene traducción inglesa publicada en /en/guia/?"""
    try:
        from .seo_articulos import ficha_articulo
        from .seo_contenido import ficha_guia

        return bool(ficha_articulo(slug, "en") or ficha_guia(slug, lang="en"))
    except Exception:
        return False


def _sitemap_con_hreflang(path: str, tema: str = "") -> bool:
    """¿Esta entrada del sitemap tiene equivalente en el otro idioma?"""
    p = path.rstrip("/") or "/"
    if p in {"/", "/en"}:
        return True
    m = re.match(r"^/en-([A-Za-z]{2})(?:/(.*))?$", p)
    if m:
        cc = m.group(1).lower()
        if cc not in {c.lower() for c in ORDEN_SELECTOR}:
            return False
        resto = (m.group(2) or "").strip("/")
        return (not resto) or (resto in TEMAS)
    if p.startswith("/en/"):
        return p[len("/en/"):] in TEMAS
    if p in {f"/{t}" for t in TEMAS}:
        return True
    if any(p == ruta_pais(c) for c in ORDEN_SELECTOR):
        return True
    if any(p == ruta_pais(c, t) for c in ORDEN_SELECTOR for t in TEMAS):
        return True
    return False


def robots_txt(request: Request | None = None) -> str:
    origen = origen_canonico(request)
    lineas = [
        "User-agent: *",
        "Allow: /",
        "Allow: /static/",
        "Allow: /static/site.webmanifest",
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
        # El índice es la única línea que hace falta: contiene el sitemap
        # principal y los hijos de precios. Se deja también el principal
        # para no romper a quien ya lo tenga enviado en Search Console.
        f"Sitemap: {origen}/sitemap_index.xml",
        f"Sitemap: {origen}/sitemap.xml",
    ]
    # Sitemaps hijos de precios (Fase 5), uno por país publicado. El
    # principal no cambia: es el que Search Console ya conoce.
    try:
        from .services import precios_publicos as _precios_publicos

        for _cc in _precios_publicos.paises_publicados():
            lineas.append(f"Sitemap: {origen}/sitemap-precios-{_cc.lower()}.xml")
    except Exception:
        pass
    lineas.append("")
    return "\n".join(lineas)


def host_publico_valido(host: str) -> bool:
    """True si el Host coincide con COTIZAT_PUBLIC_URL (para diagnóstico)."""
    try:
        publico = origen_canonico()
    except Exception:
        return False
    netloc = urlparse(publico).netloc.lower()
    return bool(netloc) and host.lower().split(":")[0] == netloc.split(":")[0]
