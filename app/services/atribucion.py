"""Atribución del alta: de qué página vino cada registro (y si acabó pagando).

El embudo del panel ya contestaba «cuántos se registran y cuántos pagan». Lo
que no contestaba es la pregunta que decide dónde invertir el tiempo: **qué
página trajo a los que pagan**.

El problema real del sitio, con los datos del 02/11/2026, es que el 76 % de
las impresiones viene del catálogo de precios (fichas de partida) y las 46
consultas comerciales —«programa de presupuestos», «APU»— suman 0 clics. Sin
atribución no se puede saber si esos miles de visitantes de partidas se
registran alguna vez o si son visitantes que no volverán.

Diseño:

- **La sección viaja en la URL del CTA** (``/acceso?origen=precios_ficha``),
  no en una cookie: las páginas públicas se sirven desde el CDN de Vercel y
  una respuesta con ``Set-Cookie`` deja de cachearse. El HTML es idéntico para
  todos los visitantes de esa URL, así que el caché se mantiene.
- **Se guarda el mercado y la sección, nunca la URL.** Una ficha es
  ``/es/precios/portones-metalicos/porton-corredizo-con-automatismo``: eso es
  un historial de navegación. Con ``es:precios_ficha`` se responde igual.
- **Solo se lee, no se rastrea**: no hay píxeles, ni identificadores, ni
  llamadas a terceros.
- **Se anota en ``eventos_producto``** (acción ``cuenta.registrada``) como
  campos del ``detalle``: ``origen_mercado`` y ``origen_seccion``. Nada de
  PII adicional.
- **El catálogo de acciones no cambia**, así que no hace falta migración: el
  detalle es un JSON libre que la función ``SECURITY DEFINER`` ya recorta.

Una ficha de partida es
``/es/precios/portones-metalicos/porton-corredizo-con-automatismo``. Guardar
la URL sería guardar un historial de navegación; con mercado + sección
(``es:precios_ficha``) se responde la misma pregunta y se guarda mucho menos.
"""
from __future__ import annotations

import re
from urllib.parse import unquote

#: Secciones que interesan para el negocio. El resto se etiqueta ``otro``:
#: clasificar 47 000 fichas por apartado no aporta nada al panel.
_SECCIONES = (
    ("precios_ficha", re.compile(r"^/[^/]+/(?:precios|prices)/[^/]+/[^/]+/?$")),
    ("precios_hub", re.compile(r"^/[^/]+/(?:precios|prices)/[^/]+/?$")),
    ("precios_indice", re.compile(r"^/[^/]+/(?:precios|prices)/?$")),
    ("comparador", re.compile(r"^/(?:precios-comparados|en/prices-comparison)")),
    ("mano_obra", re.compile(r"^/[^/]+/mano-de-obra")),
    ("calculadora", re.compile(r"^/[^/]+/calculadora|^/calculadora")),
    ("guia", re.compile(r"^/[^/]+/guia/|^/guia/")),
    ("landing_pais", re.compile(r"^/[a-z]{2}(?:-[a-z]{2})?/?$")),
    ("planes", re.compile(r"^/(?:pago|planes)|^/en/pago")),
    ("como_funciona", re.compile(r"^/(?:como-funciona|en/how-it-works)")),
)


def seccion_de(ruta: str) -> str:
    """Sección comercial de una ruta pública.

    ``/es/precios/portones-metalicos/porton-corredizo`` → ``precios_ficha``.
    Nunca devuelve la ruta: eso convertiría la analítica en un historial de
    navegación.
    """
    camino = (ruta or "").split("?")[0].split("#")[0] or "/"
    if camino in ("/", ""):
        return "portada"
    for nombre, patron in _SECCIONES:
        if patron.search(camino):
            return nombre
    return "otro"


def mercado_de(ruta: str) -> str:
    """Prefijo de mercado de la ruta (``es``, ``mx``, ``en-gb``, ``en``)."""
    camino = (ruta or "").split("?")[0].strip("/")
    if not camino:
        return "global"
    primero = camino.split("/")[0].lower()
    if re.fullmatch(r"[a-z]{2}(?:-[a-z]{2})?", primero):
        return primero
    # Rutas sin prefijo de país (/, /precios-comparados, /pago) son globales
    # o del mercado por omisión; el panel no necesita distinguirlas.
    return "global"


def valor_cookie(ruta: str) -> str:
    """Contenido de la cookie para una ruta: ``mercado:seccion``."""
    return f"{mercado_de(ruta)}:{seccion_de(ruta)}"


def leer_origen(valor: str | None) -> dict[str, str]:
    """Convierte el valor de la cookie en el ``detalle`` de telemetría.

    Tolera cookies viejas, vacías o manipuladas: si no encaja en el formato,
    se devuelve un diccionario vacío en vez de un dato inventado.
    """
    crudo = unquote(str(valor or "")).strip()
    if not crudo or len(crudo) > 80:
        return {}
    mercado, _, seccion = crudo.partition(":")
    mercado = re.sub(r"[^a-z\-]", "", mercado.lower())[:12]
    seccion = re.sub(r"[^a-z_]", "", seccion.lower())[:24]
    if not mercado or not seccion:
        return {}
    return {"origen_mercado": mercado, "origen_seccion": seccion}


#: Secciones que un CTA puede declarar por query string. Lista cerrada: un
#: ``?origen=`` inventado no puede inventar una categoría en la analítica.
SECCIONES_CONOCIDAS = frozenset(
    {
        "precios_ficha",
        "precios_hub",
        "precios_indice",
        "comparador",
        "mano_obra",
        "calculadora",
        "guia",
        "landing_pais",
        "planes",
        "como_funciona",
        "portada",
        # La variante nueva de la portada se mide por separado: si el
        # rediseño mejora o empeora el alta, tiene que verse en el panel.
        "landing_impulso",
    }
)

#: Variantes de landing que un CTA puede declarar. Lista cerrada: la URL es
#: pública y cualquier valor inventado acabaría ensuciando la analítica.
VARIANTES_LANDING = frozenset({"impulso", "clasica"})

#: Motivos de llegada de la variante «impulso». Los usa el copy del CTA y
#: llegan al alta como microcompromiso, nunca como dato personal.
INTENCIONES_LANDING = frozenset({"tiempo", "margen", "cierre"})


def normalizar_variante(valor: str | None) -> str:
    """Devuelve una variante del catálogo o cadena vacía."""
    limpio = str(valor or "").strip().lower()
    return limpio if limpio in VARIANTES_LANDING else ""


def normalizar_intencion(valor: str | None) -> str:
    """Devuelve una intención del catálogo o cadena vacía."""
    limpio = str(valor or "").strip().lower()
    return limpio if limpio in INTENCIONES_LANDING else ""
