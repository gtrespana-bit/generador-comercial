"""¿El catálogo de un mercado es un original o una copia del español?

Esta pieza existe por un incidente concreto y medido: el 21–22/10/2026 se
anunció a los buscadores el catálogo público de los 22 mercados a la vez
(~40 000 URL) y en 48 h el sitio pasó de sus posiciones habituales a la 44 de
media con 0 clics (``docs/DIAGNOSTICO_TRAFICO_CERO_2026-10-23.md``). La causa
que encaja con todos los datos no fue el sitemap: fue **lo que el sitemap
anunciaba** — decenas de miles de fichas casi idénticas entre sí, que es el
patrón que Google llama *contenido generado a escala*. Se apagó el catálogo de
los 16 mercados hispanos con ``noindex`` y la superficie se estabilizó.

El problema de fondo sigue ahí y no se veía en ningún sitio: **la prosa de la
ficha**. Los precios de cada país son propios (``salida/precios_recursos_*.csv``,
matrices de coste-empresa investigadas mercado a mercado), pero el título, la
descripción, los nombres de los recursos y el nombre del apartado son los
mismos que los de España en todos los mercados hispanos. Cambia el número y la
moneda; no cambia el texto. Los mercados de habla inglesa no tienen ese
problema porque su prosa viene traducida de verdad (``services/traduccion``).

Por eso, antes de encender el catálogo de un mercado hay que poder responder
una pregunta con un número, no con una opinión: **¿cuánto se parece su prosa a
la española?** Eso es lo que mide este módulo, sobre las fichas que de verdad
se publican (las que pasan la guardia de ``_partida_publicable``).

La medida
---------
Para cada ficha se toma lo que Google ve como texto —título, descripción,
nombres de los recursos del descompuesto y nombre del apartado— y se compara el
vocabulario del mercado con el de la misma ficha en España, por código de
partida. Dos números:

* ``jaccard``: tamaño de la intersección dividido por la unión de vocabularios.
  Cerca de 1,0 = mismo texto con otro número; cerca de 0,0 = texto propio.
* ``identicas``: proporción de fichas cuyo texto es **exactamente** el español.

Los umbrales son deliberadamente conservadores y se aplican a una muestra
estable (las primeras ``muestra`` partidas por código, no una muestra al azar:
dos ejecuciones tienen que dar el mismo número). No son una verdad absoluta:
son una puerta que impide repetir el 23/10, y se pueden discutir con datos
delante.

Cómo se desbloquea un mercado
-----------------------------
Escribiendo prosa propia, no cambiando el umbral. Cuando una partida tenga
título y descripción propios del mercado (su unidad, su término, su oficio, su
forma de medir), su ``jaccard`` baja. Cuando el mercado entero baje del umbral,
la puerta se abre sola. El día que se quiera encender un mercado sin haber
tocado la prosa, ``tests/test_activacion_mercados.py`` lo impide con un mensaje
que dice exactamente cuánto falta.
"""
from __future__ import annotations

import re
from typing import Iterable

#: Jaccard por debajo del cual la prosa se considera propia del mercado.
#: Los mercados traducidos al inglés andan en 0,02; los hispanos, en 0,97.
UMBRAL_PROPIA = 0.50

#: Jaccard a partir del cual la ficha es, a efectos prácticos, la española con
#: otro número. No es un límite legal: es el diagnóstico que hay que bajar.
UMBRAL_CALCO = 0.85

#: Muestra estable por mercado. Con 200 fichas la media no se mueve entre
#: ejecuciones y el cálculo tarda menos de un segundo por mercado.
MUESTRA_POR_DEFECTO = 200

#: Mercado de referencia: la prosa española es el patrón contra el que se mide.
MERCADO_REFERENCIA = "ES"

_PALABRA = re.compile(r"[0-9a-záéíóúñü]+")


def _vocabulario(texto: str) -> set[str]:
    return set(_PALABRA.findall((texto or "").lower()))


def prosa_de_ficha(ficha: dict | None) -> str:
    """Todo el texto que un buscador lee de una ficha, en un solo hilo.

    Incluye los nombres de los recursos porque son la mitad de la página: si el
    descompuesto se llama igual en los 23 mercados, la página es la misma
    aunque el precio unitario cambie.
    """
    if not ficha:
        return ""
    apartado = ficha.get("apartado") or {}
    partes = [
        str(ficha.get("titulo") or ""),
        str(ficha.get("descripcion") or ""),
        str(apartado.get("nombre") or ""),
    ]
    for linea in ficha.get("lineas") or []:
        partes.append(str(linea.get("nombre") or ""))
    return " ".join(partes)


def _fichas_por_codigo(codigo_pais: str) -> dict[str, tuple[str, str]]:
    """``{código de partida: (slug del apartado, slug de la partida)}``.

    El código (``01.01.01.010``) es lo único estable entre mercados: los slugs
    van en el idioma del mercado y cambian con la traducción.
    """
    from . import precios_publicos as pp

    indice = pp._indice(codigo_pais)
    if not indice:
        return {}
    salida: dict[str, tuple[str, str]] = {}
    for clave, ficha in (indice.get("partidas") or {}).items():
        codigo = str((ficha or {}).get("codigo") or "").strip()
        if codigo:
            salida[codigo] = clave
    return salida


def _muestra(comunes: Iterable[str], muestra: int) -> list[str]:
    ordenados = sorted(comunes)
    if muestra <= 0 or len(ordenados) <= muestra:
        return ordenados
    return ordenados[:muestra]


def huella(codigo_pais: str, muestra: int = MUESTRA_POR_DEFECTO) -> dict:
    """Radiografía de la prosa de un mercado frente a la española.

    Devuelve un diccionario con lo que hace falta para decidir: cuántas fichas
    hay, cuántas se comparan, cuánto se parece el vocabulario y cuántas son
    literalmente la española. ``referencia`` es True para España, que no se
    compara consigo misma.
    """
    from . import precios_publicos as pp

    cc = str(codigo_pais or "").strip().upper()
    base = {
        "mercado": cc,
        "referencia": cc == MERCADO_REFERENCIA,
        "publicado": False,
        "partidas": 0,
        "comparadas": 0,
        "jaccard": None,
        "identicas": None,
        "muestra": 0,
    }
    indice = pp._indice(cc)
    if not indice:
        return base

    por_codigo = _fichas_por_codigo(cc)
    base["publicado"] = True
    base["partidas"] = len(por_codigo)
    base["muestra"] = muestra
    if base["referencia"]:
        return base

    es = _fichas_por_codigo(MERCADO_REFERENCIA)
    comunes = _muestra((c for c in por_codigo if c in es), muestra)
    if not comunes:
        return base

    suma = 0.0
    iguales = 0
    comparadas = 0
    for codigo in comunes:
        ficha = pp.partida(cc, *por_codigo[codigo])
        ficha_es = pp.partida(MERCADO_REFERENCIA, *es[codigo])
        if not ficha or not ficha_es:
            continue
        texto = prosa_de_ficha(ficha)
        texto_es = prosa_de_ficha(ficha_es)
        if texto.strip() == texto_es.strip():
            iguales += 1
        a, b = _vocabulario(texto_es), _vocabulario(texto)
        union = a | b
        suma += (len(a & b) / len(union)) if union else 1.0
        comparadas += 1

    base["comparadas"] = comparadas
    if comparadas:
        base["jaccard"] = round(suma / comparadas, 4)
        base["identicas"] = round(iguales / comparadas, 4)
    return base


def editorial_propio(codigo_pais: str) -> dict:
    """Qué contenido editorial tiene el mercado además del catálogo.

    No entra en la nota de prosa —una guía no arregla 2 000 fichas clonadas—
    pero sí en el orden de encendido: un mercado con guía, nota de mano de obra
    y problema técnico propio se localiza mucho más rápido que uno vacío.
    """
    cc = str(codigo_pais or "").strip().upper()
    salida = {"labor": False, "tecnica": False, "documento": False}
    try:
        from ..seo_latam_contenido import MERCADOS

        perfil = MERCADOS.get(cc) or {}
        salida["labor"] = bool(perfil.get("labor"))
        salida["tecnica"] = bool(perfil.get("tecnica"))
        salida["documento"] = bool(perfil.get("documento"))
    except Exception:  # pragma: no cover - datos editoriales opcionales
        pass
    return salida


def guias_propias(codigo_pais: str) -> int:
    """Artículos de mercado publicados (los que ya viven en su silo)."""
    cc = str(codigo_pais or "").strip().upper()
    try:
        from ..seo_articulos import lista_articulos, lista_articulos_en

        totales: dict[str, int] = {}
        for articulo in list(lista_articulos()) + list(lista_articulos_en()):
            pais = str(articulo.get("pais") or "").strip().upper()
            totales[pais] = totales.get(pais, 0) + 1
        return int(totales.get(cc, 0))
    except Exception:  # pragma: no cover - datos editoriales opcionales
        return 0


def veredicto(codigo_pais: str, muestra: int = MUESTRA_POR_DEFECTO) -> dict:
    """¿Puede encenderse hoy el catálogo de este mercado? Y si no, qué falta.

    ``estado`` vale:

    * ``referencia`` — España: es el patrón, no se compara.
    * ``listo`` — prosa suficientemente propia para anunciarse sin repetir el
      23/10.
    * ``parcial`` — hay diferencias reales pero no bastan: localizar el resto.
    * ``calco`` — mismo texto con otro número. No se enciende.
    * ``sin_catalogo`` — el mercado no tiene catálogo publicado (Venezuela no
      tiene matriz propia en el repo; sus fichas se sirven con los precios base
      en USD y no se publican como catálogo).
    """
    h = huella(codigo_pais, muestra)
    cc = h["mercado"]
    salida = {
        **h,
        "editorial": editorial_propio(cc),
        "guias": guias_propias(cc),
        "estado": "sin_catalogo",
        "motivo": "El mercado no tiene catálogo público publicado.",
        "porcentaje_identico": None,
    }
    if h["referencia"]:
        salida["estado"] = "referencia"
        salida["motivo"] = "España es el mercado de referencia de la prosa."
        return salida
    if not h["publicado"]:
        return salida
    if h["jaccard"] is None:
        salida["motivo"] = "No hay fichas comparables con España."
        return salida

    salida["porcentaje_identico"] = round(100 * (h["identicas"] or 0), 1)
    if h["jaccard"] < UMBRAL_PROPIA:
        salida["estado"] = "listo"
        salida["motivo"] = "La prosa es propia del mercado."
    elif h["jaccard"] < UMBRAL_CALCO:
        salida["estado"] = "parcial"
        salida["motivo"] = (
            "Hay texto propio, pero la mayoría de la ficha sigue siendo la "
            "española: falta localizar el resto antes de anunciarla."
        )
    else:
        salida["estado"] = "calco"
        salida["motivo"] = (
            "La ficha es la española con otro precio. Anunciarla repite el "
            "patrón del 23/10: contenido a escala sin valor por mercado."
        )
    return salida


def radar(muestra: int = MUESTRA_POR_DEFECTO) -> list[dict]:
    """Todos los mercados con precio público, con su veredicto.

    El orden es el de ``PAISES_PRECIOS_PUBLICOS`` (el de encendido previsto en
    la docstring del servicio), no el del selector comercial.
    """
    from . import precios_publicos as pp

    return [veredicto(cc, muestra) for cc in pp.PAISES_PRECIOS_PUBLICOS]


def clave_orden(fila: dict) -> tuple:
    """Criterio único de orden para encender mercados, de más a menos listo.

    No es una preferencia: localizar 2 000 fichas de un mercado que ya tiene
    guías, nota de mano de obra y problema técnico propio es mucho más rápido
    (y más difícil de escribir mal) que hacerlo en uno vacío. El número de
    guías va antes que el resto del material porque es el que ya está
    indexado y recibiendo impresiones.
    """
    editorial = fila.get("editorial") or {}
    return (
        {"listo": 0, "parcial": 1, "calco": 2}.get(fila.get("estado"), 3),
        -int(fila.get("guias") or 0),
        -int(bool(editorial.get("tecnica")))
        - int(bool(editorial.get("labor")))
        - int(bool(editorial.get("documento"))),
        fila.get("jaccard") if fila.get("jaccard") is not None else 1.0,
        str(fila.get("mercado") or ""),
    )


def mercados_por_encender(muestra: int = MUESTRA_POR_DEFECTO) -> list[str]:
    """Mercados publicados que aún no se anuncian, de más a menos preparados.

    Criterio: primero los que ya tienen más contenido editorial propio (guías,
    nota de mano de obra, problema técnico local), porque son los que menos
    trabajo necesitan para cruzar la puerta. Desempata la prosa.
    """
    from . import precios_publicos as pp

    pendientes = []
    for fila in radar(muestra):
        if fila["referencia"] or not fila["publicado"]:
            continue
        if fila["mercado"] in pp.MERCADOS_FICHAS_INDEXABLES:
            continue
        pendientes.append(fila)

    return [f["mercado"] for f in sorted(pendientes, key=clave_orden)]

