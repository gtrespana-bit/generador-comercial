"""Traducción de terminología de obra por país — runtime.

El catálogo base se guarda en venezolano (friso, rodapié, losa, encofrado...).
Los glosarios `basedatos_partidas/glosarios/{CO,MX,EC,PE,ES}.json` contienen
mapeos VE→CO/MX/EC/PE/ES con 70-150 entradas cada uno (ES: castellano
peninsular — hormigón, pladur, falso techo, alicatado, fontanero...).

Esta capa NO reescribe archivos: traduce al vuelo al mostrar catálogo,
presupuestos y PDF, respetando mayúscula inicial y plural en -s/-es,
igual que `basedatos_partidas/terminologia.py:sustituir`.

Reglas de aplicación (importantes para categorías):
1. Primero se aplican las FRASES (entradas con espacios), de más larga a
   más corta, y el texto sustituido queda PROTEGIDO: los mapeos de palabra
   no lo vuelven a tocar. Así «Techos y cubiertas» -> «Cubiertas» no acaba
   en «Cubiertas y cubiertas» por culpa de techo->cubierta.
2. Después se aplican las palabras sueltas.
3. El plural se resuelve sobre la última palabra del destino, con la regla
   española de acentos: andén+es -> andenes, guarnición+es -> guarniciones.
   El glosario EN no usa esa regla sino la inglesa (``_pluralizar_en``): con
   las reglas del español, «partidas» salía como «line itemes».
4. Los glosarios españoles y el inglés no se mezclan: cada texto se traduce
   con un solo glosario, el que corresponda al idioma del mercado.

Uso:
    from app.services.traduccion import traducir, traducir_partida

    traducir("Friso de mortero", "CO") -> "Pañete de mortero"
    traducir_partida(partida, "MX") -> partida con nombre/descripcion traducidos (copia)
"""

from __future__ import annotations

import json
import re
import unicodedata

from ..paises import resolver_mercado
from .variante_ingles import aplicar_variante
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

# Raíz del repo: app/services -> ../../basedatos_partidas
BASE_GLOSARIOS = Path(__file__).resolve().parents[2] / "basedatos_partidas" / "glosarios"
BASE_RECURSOS = Path(__file__).resolve().parents[2] / "basedatos_partidas" / "datos"


# ── Tablas precalculadas ─────────────────────────────────────────────────
# El catálogo ronda las 7.000 cadenas distintas y hay 22 mercados, así que
# caben más de 150.000 pares (texto, mercado): bastante más de lo que aguanta
# la caché LRU de ``traducir``, que acababa desbordando y retraduciendo lo
# que ya había traducido. Estas tablas resuelven el catálogo con una sola
# lectura de diccionario; el glosario queda para lo que no esté en ellas
# (partidas propias del cliente, recién escritas).
#
# Las genera ``tools/generar_traducciones.py`` y las verifica
# ``tools/verificar_traducciones.py``. Son un derivado del catálogo y de los
# glosarios, nunca una fuente: si el catálogo cambia, hay que regenerarlas.
SALIDA_TRADUCCIONES = (Path(__file__).resolve().parents[2]
                       / "basedatos_partidas" / "salida" / "traducciones")


@lru_cache(maxsize=32)
def _cargar_tabla(codigo: str) -> Mapping[str, str]:
    """Tabla precalculada de un mercado; ``{}`` si no hay artefacto.

    Se devuelve de solo lectura: sale de una caché compartida por todas las
    peticiones y una mutación accidental se vería en las demás.
    """
    ruta = SALIDA_TRADUCCIONES / f"{codigo}.json"
    try:
        data = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return MappingProxyType({})
    return MappingProxyType(data.get("cadenas") or {})


@lru_cache(maxsize=32)
def _cargar_excepciones(codigo: str) -> Mapping[str, str]:
    """Correcciones a mano que un glosario no puede expresar.

    Un glosario mapea términos, no sabe que «remate» es *joint finishing* en
    una partida y *coping* en otra, ni que en un andamio el rodapié es una
    tabla de pie. Estas excepciones son cadenas completas, se aplican antes
    que nada y ganan siempre, así que se pueden afinar una a una sin tocar
    las reglas generales ni arriesgar las demás traducciones.
    """
    ruta = BASE_GLOSARIOS / f"{codigo}.excepciones.json"
    try:
        data = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return MappingProxyType({})
    tabla = dict(data.get("cadenas") or {})
    tabla.update(_excepciones_recursos(codigo))
    return MappingProxyType(tabla)


@lru_cache(maxsize=None)
def _recurso_en_por_codigo() -> Mapping[str, str]:
    """Índice «código de recurso -> redacción inglesa» de ``recursos_en.json``."""
    try:
        datos = json.loads((BASE_RECURSOS / "recursos_en.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return MappingProxyType({})
    salida: dict[str, str] = {}
    for categoria, pares in datos.items():
        if isinstance(pares, dict) and not str(categoria).startswith("_"):
            for codigo, texto in pares.items():
                if isinstance(texto, str) and texto.strip():
                    salida[str(codigo).strip()] = texto
    return MappingProxyType(salida)


@lru_cache(maxsize=None)
def _recurso_es_por_codigo() -> Mapping[str, str]:
    """Índice del texto original español por código de recurso."""
    try:
        datos = json.loads((BASE_RECURSOS / "recursos.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return MappingProxyType({})
    salida: dict[str, str] = {}
    for categoria, pares in datos.items():
        if isinstance(pares, dict) and not str(categoria).startswith("_"):
            for codigo, recurso in pares.items():
                texto = recurso.get("descripcion") if isinstance(recurso, dict) else None
                if isinstance(texto, str) and texto.strip():
                    salida[str(codigo).strip()] = texto
    return MappingProxyType(salida)


@lru_cache(maxsize=None)
def _excepciones_recursos(codigo: str) -> Mapping[str, str]:
    """Traducciones de los recursos del catálogo, como excepciones de cadena completa.

    Viven en ``basedatos_partidas/datos/recursos_<glosario>.json`` claveadas por
    CÓDIGO de recurso, no por el texto español. El código es estable; el texto
    cambia. Si estuvieran claveadas por el texto, una coma de más en el original
    dejaría el recurso sin traducir y sin avisar, que es exactamente lo que
    pasaba antes de existir este fichero: los 388 recursos caían en el glosario
    genérico y salían como calcos («Oficial of 1ª bricklayer»).

    Aquí se convierten a «texto español -> texto traducido», que es la forma en
    que las excepciones se consultan.
    """
    if codigo != "EN":
        return MappingProxyType({})
    recuros_es = BASE_RECURSOS / "recursos.json"
    traducciones = BASE_RECURSOS / "recursos_en.json"
    try:
        originales = json.loads(recuros_es.read_text(encoding="utf-8"))
        textos = json.loads(traducciones.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return MappingProxyType({})
    salida: dict[str, str] = {}
    for categoria, pares in textos.items():
        if not isinstance(pares, dict) or categoria.startswith("_"):
            continue
        fuente = originales.get(categoria) or {}
        for codigo_recurso, traducido in pares.items():
            original = (fuente.get(codigo_recurso) or {}).get("descripcion")
            if isinstance(original, str) and original.strip() and isinstance(traducido, str):
                salida[original] = traducido
    return MappingProxyType(salida)

# Mapeo nombre de país (cfg.empresa_pais) -> código ISO
# Formas de llamar a un país que no son su nombre oficial: «USA», «UK»,
# «dominicana»... Lo que SÍ es nombre oficial se deriva del registro de
# mercados, abajo.
_ALIAS_PAIS = {
    "usa": "US",
    "us": "US",
    "united states": "US",
    "united states of america": "US",
    "eeuu": "US",
    "uk": "GB",
    "united kingdom": "GB",
    "great britain": "GB",
    "england": "GB",
    "gran bretaña": "GB",
    "australia": "AU",
    "canada": "CA",
    "ireland": "IE",
    "eire": "IE",
    "dominicana": "DO",
    # «Latinoamérica» no es un país: cae al genérico, que es lo correcto.
    "latinoamerica": "",
}


def _sin_acento_minuscula(texto: str) -> str:
    """Minúsculas sin marcas diacríticas: «España» y «Espana» → «espana».

    Se normaliza en NFD y se descartan los diacríticos combinantes, así que
    funciona con cualquier acento y también con la eñe. La versión anterior
    quitaba cinco vocales acentuadas a mano y se dejaba la eñe, lo que
    obligaba a escribir las dos formas de cada país en el diccionario.
    """
    descompuesto = unicodedata.normalize("NFD", str(texto or "").strip().lower())
    return "".join(c for c in descompuesto if not unicodedata.combining(c))


def _construir_nombres() -> dict[str, str]:
    """Nombre oficial (y gentilicio) de cada mercado -> su código.

    Se deriva de `app.paises.PAISES`, que es la única fuente de verdad. Si
    se da de alta un mercado nuevo, se resuelve solo; mantener aquí una
    lista a mano es lo que dejó fuera a los mercados ingleses.
    """
    from ..paises import PAISES

    mapa: dict[str, str] = {}
    for codigo, pais in PAISES.items():
        for clave in (pais.get("nombre"), pais.get("mercado")):
            k = _sin_acento_minuscula(clave)
            if k:
                mapa[k] = codigo
    mapa.update(_ALIAS_PAIS)
    return mapa


_NOMBRE_A_CODIGO = _construir_nombres()

_SIN_ACENTO = str.maketrans("áéíóú", "aeiou")

# El español pierde la tilde al pluralizar en cuanto cambia la sílaba tónica:
# «demolición» -> «demoliciones», «hormigón» -> «hormigones», «mesón» ->
# «mesones». Un patrón que busca «demolición» literal no encuentra nunca
# «demoliciones», así que una familia entera de palabras de obra (todas las
# -ción, -sión y -ón) quedaba sin traducir en plural.
#
# La solución no es duplicar entradas en el glosario sino compilar cada
# palabra con una clase que acepta la vocal con y sin tilde: «hormig[oó]n»
# encuentra las dos formas. Se construye una sola vez (el glosario se
# pre-compila y se cachea), así que no hay coste por partida.
# La flexibilidad va en UN SOLO SENTIDO, y ahí está todo el truco: una vocal
# con tilde en la clave acepta su forma sin tilde, pero una vocal sin tilde
# NO acepta la forma con tilde.
#
#   «hormigón»  -> hormig[oó]n   encuentra «hormigon» y «hormigón»  (bien: es
#                                la misma palabra, el plural pierde la tilde)
#   «closet»    -> closet        NO encuentra «clóset»             (bien: si
#                                la encontrara, re-pluralizaría una palabra ya
#                                traducida y saldría «clósetes»)
#
# La «ü» (desagüe) es un carácter distinto de la «u» acentuada: si la clase no
# la incluye, una clave con ü deja de encontrar su propio texto y se pierden
# las frases protectoras del glosario («Desagüe sanitario» en MX).
_VOCAL_FLEXIBLE = {
    "a": "a", "á": "[aá]",
    "e": "e", "é": "[eé]",
    "i": "i", "í": "[ií]",
    "o": "o", "ó": "[oó]",
    "u": "u", "ú": "[uú]", "ü": "[üu]",
}


_ACENTOS = str.maketrans("áéíóúñüÁÉÍÓÚÑÜ", "aeiounuAEIOUNU")


_PALABRA = re.compile(r"[\wáéíóúñüÁÉÍÓÚÑÜ]+")


def _clave_filtro(palabra: str) -> str:
    """Primera palabra sin acentos y en minúsculas, para descartar patrones.

    Sin acentos por exceso: la flexibilidad de ``_regex_flexible`` solo va en
    un sentido (la forma acentuada admite la sin acento, no al revés), así
    que quitarlos en la clave y en el texto ensancha el filtro y nunca lo
    estrecha. Un filtro que deja pasar de más solo cuesta una comparación;
    uno que deja pasar de menos perdería traducciones.
    """
    # Sin puntuación: hay frases como «Frisos, enlucidos» cuyo primer
    # término lleva coma, y esa coma nunca aparece como palabra del texto,
    # así que el filtro las descartaba y dejaba de traducirlas.
    return "".join(_PALABRA.findall(palabra.lower().translate(_ACENTOS)))


def _regex_flexible(palabra: str) -> str:
    """Expresión regular de una palabra que acepta las vocales con y sin tilde."""
    return "".join(_VOCAL_FLEXIBLE.get(c, re.escape(c)) for c in palabra)


def codigo_desde_pais(nombre_pais: str | None) -> str:
    if not nombre_pais:
        return ""
    return _NOMBRE_A_CODIGO.get(_sin_acento_minuscula(nombre_pais), "")


@lru_cache(maxsize=8)
def _cargar_glosario(codigo: str) -> list[dict]:
    if not codigo or codigo == "VE":
        return []
    ruta = BASE_GLOSARIOS / f"{codigo}.json"
    if not ruta.is_file():
        return []
    try:
        data = json.loads(ruta.read_text(encoding="utf-8"))
    except Exception:
        return []
    cambios = data.get("cambios") or []
    # Normaliza a lista de {de,a}. Las frases (con espacio) se conservan
    # aunque de==a: funcionan como PROTECTORAS (evitan que los mapeos de
    # palabra toquen una expresión que ya es correcta).
    out = []
    for c in cambios:
        de = str(c.get("de") or "").strip()
        a = str(c.get("a") or "").strip()
        if de and a and (" " in de or de.lower() != a.lower()):
            out.append({"de": de, "a": a})
    return out


def _mismo_caso(origen: str, destino: str) -> str:
    if origen[:1].isupper():
        return destino[:1].upper() + destino[1:]
    return destino


def _pluralizar(nuevo: str, sufijo: str | None) -> str:
    """Aplica el plural español a una palabra del destino.

    Reglas de acentos:
      andén -> andenes, guarnición -> guarniciones, plafón -> plafones
      (la tilde cae en plural porque la sílaba tónica cambia)
      menú -> menús, bebé -> bebés (vocal tónica final: se conserva)
    """
    if not sufijo:
        return nuevo
    s = nuevo
    if len(s) >= 2 and s[-1] in "ns" and s[-2] in "áéíóú":
        # andén -> andenes, francés -> franceses (cae la tilde, se conserva la consonante)
        return s[:-2] + s[-2].translate(_SIN_ACENTO) + s[-1] + "es"
    if s[-1:] in "áéíóú":
        # menú -> menús (mantiene la tilde)
        return s + "s"
    return s + ("es" if s[-1:] not in "aeiou" else "s")


# Preposiciones que delatan que el núcleo de un destino con espacios va
# al principio en vez de al final (inglés y español).
_PREPOSICIONES = frozenset({
    "of", "in", "on", "at", "by", "with", "for", "to", "from",
    "de", "del", "en", "a", "con", "para", "por", "sin", "sobre",
})

# Palabras de clase cerrada: artículos, preposiciones, conjunciones y
# pronombres. Son invariables, así que su patrón no puede admitir el sufijo
# de plural (es|s). Sin esto la conjunción «e» generaba el patrón e(es|s)?,
# que casa con «Es» (verbo ser) y convertía «Es la capa que define el nivel»
# en «Ands the layer that define the level»: 74 cadenas del catálogo.
# Las pocas que sí flexionan (la/las, su/sus, lo/los) tienen entrada propia
# en el glosario, así que no pierden nada.
_INVARIABLES = frozenset({
    "a", "al", "con", "de", "del", "desde", "durante", "e", "el", "en",
    "entre", "hasta", "hacia", "la", "las", "lo", "los", "ni", "o", "para",
    "pero", "por", "que", "se", "sin", "sobre", "su", "sus", "tras", "u",
    "un", "una", "y",
})

# Nombres de obra que en inglés no admiten marca de plural. No es una lista
# de «palabras raras»: son los materiales y las operaciones que un contratista
# no pluraliza nunca (se dice «formwork», no «formworks», igual que se dice
# «concrete» y no «concretes»). Incluirlos evita el plural automático cuando
# el español sí marca el plural.
_INCONTABLES_EN = frozenset({
    "concrete", "formwork", "falsework", "plaster", "stucco", "render",
    "mortar", "grout", "screed", "debris", "rubble", "spoil",
    "plastering", "concreting", "waterproofing", "tiling", "plumbing",
    "scaffolding", "shuttering", "formworking",
    "insulation", "drainage", "productivity", "coverage", "equipment",
})


def _pluralizar_en(nuevo: str, sufijo: str | None) -> str:
    """Plural **inglés** del término de destino del glosario EN.

    :func:`_pluralizar` aplica las reglas del español, incluida la de
    «consonante + -es». Con un destino en inglés eso produce barbaridades
    («partidas» -> «line itemes», «albañiles» -> «bricklayeres»,
    «garantías» -> «warrantyes»), así que el glosario EN necesita las reglas
    inglesas y respetar los nombres incontables de obra.
    """
    if not sufijo or not nuevo:
        return nuevo
    s = nuevo
    if s.lower() in _INCONTABLES_EN:
        return s
    bajo = s.lower()
    if re.search(r"(?:ed|ous|ful|less|ish)$", bajo):
        # El inglés no pluraliza adjetivos ni participios. El glosario EN
        # guarda la forma singular, y el patrón casa también con el plural
        # español («tratado» casa con «tratados»), así que sin esto saldrían
        # barbaridades como «treateds», «continuouses» o «exposeds».
        return s
    if re.search(r"(?:s|x|z|ch|sh)$", bajo):
        return s + "es"                      # patch -> patches, box -> boxes
    if re.search(r"[^aeiou]y$", bajo):
        return s[:-1] + "ies"                # warranty -> warranties
    return s + "s"                           # line item -> line items


@lru_cache(maxsize=8)
def _compilar_glosario(codigo: str) -> tuple[list, list]:
    """Pre-compila los patrones de un glosario (frases y palabras sueltas).

    ``traducir`` se llama miles de veces por carga del catálogo (una vez por
    partida, y más de una por partida según la pantalla). Cada llamada
    recompilaba todos los patrones del glosario desde cero: con un glosario
    de ~130 entradas y un catálogo de ~3.000 partidas, eso era el grueso del
    tiempo de carga del editor de presupuestos, de /partidas y de /recursos
    en países con traducción (CO/MX/EC/PE...).

    Devuelve ``(frases, palabras)``: cada elemento es ``(patron_compilado,
    de, a, clave)``, donde ``clave`` es la primera palabra sin acentos y en
    minúsculas. Sirve para descartar de golpe los patrones que no pueden
    casar (véase :func:`_traducir_reglas`). Los patrones son inmutables y
    seguros de compartir entre llamadas; el estado por llamada (contador de
    tokens y lista de reemplazos) se crea dentro de :func:`traducir`.
    """
    cambios = _cargar_glosario(codigo)
    frases = []
    for c in sorted(
        (c for c in cambios if " " in c["de"]),
        key=lambda c: -len(c["de"]),
    ):
        de, a = c["de"], c["a"]
        # Grupos con nombre y no posicionales: los invariables no aportan
        # grupo de sufijo, así que contar posiciones daba el grupo de al lado
        # y pluralizaba con una palabra («sin dañar» -> «without damagings»,
        # «a las» -> «tos thes»). Con nombres, la ausencia se ve a las claras.
        grupos = []
        for i, w in enumerate(de.split(" ")):
            # El sufijo va PEGADO a su palabra: separarlo con un espacio lo
            # convertía en obligatorio y partía los compuestos de tres
            # términos («paredes de bloque» dejaba de casar).
            trozo = rf"(?P<w{i}>{_regex_flexible(w)})"
            if w.lower() not in _INVARIABLES:
                trozo += rf"(?P<s{i}>es|s)?"
            grupos.append(trozo)
        patron = re.compile(r"\b" + " ".join(grupos) + r"\b", re.IGNORECASE)
        frases.append((patron, de, a, _clave_filtro(de.split(" ")[0])))
    # De más larga a más corta, igual que las frases: si no, la forma
    # singular enmascara la plural y la pluraliza con la regla inglesa.
    # «vidrio» casaba con «vidrios» antes que la entrada «vidrios» y daba
    # «glasses»; «metálico» daba «metals» por encima de «metálicos».
    palabras = []
    for c in sorted(
        (c for c in cambios if " " not in c["de"]),
        key=lambda c: -len(c["de"]),
    ):
        de, a = c["de"], c["a"]
        sufijo = "" if de.lower() in _INVARIABLES else r"(?P<s>es|s)?"
        patron = re.compile(rf"\b(?P<w>{_regex_flexible(de)}){sufijo}\b", re.IGNORECASE)
        palabras.append((patron, de, a, _clave_filtro(de)))
    return frases, palabras


def _traducir_reglas(texto: str, mercado: dict, glosario: str) -> str:
    """Aplica el glosario al texto. Es la única implementación.

    La llaman tanto el generador de tablas como el camino lento de
    ``traducir``, así que el artefacto precalculado y el cálculo en vivo no
    pueden divergir. No aplica la variante de inglés: eso se hace una sola
    vez al final, en ``traducir``, para que la tabla del glosario EN sirva a
    los cinco mercados anglófonos.
    """
    excepciones = _cargar_excepciones(glosario)
    if texto in excepciones:
        return excepciones[texto]
    # El plural del término de destino no se forma igual en inglés que en
    # español: con el glosario EN hay que usar las reglas inglesas.
    pluralizar = _pluralizar_en if glosario == "EN" else _pluralizar
    frases, palabras = _compilar_glosario(glosario)
    if not frases and not palabras:
        return texto
    out = texto

    # ---- 1) Frases (con espacios): más largas primero y protegidas ----
    # El texto sustituido se marca con un token sin caracteres de palabra para
    # que los mapeos de palabra posteriores no lo vuelvan a tocar.
    # El plural español de una frase puede aparecer en el sustantivo
    # («paredes de bloque»), en el último término («cielos rasos») o en
    # ambos, así que cada palabra admite un sufijo -es/-s opcional.
    # Prefiltro: un patrón solo puede casar si su primera palabra está en el
    # texto. Calcularlo cuesta una vez por llamada (un conjunto de palabras)
    # y evita miles de re.sub sobre cadenas cortas, que era el coste real:
    # con ~4.500 patrones el camino lento pasaba de ~1,5 ms a ~3,7 ms.
    # Prefijos, no palabras completas: el patrón admite un sufijo -es/-s, así
    # que «instalación» tiene que casar con «instalaciones». Filtrar por
    # palabra exacta fue un error que dejó sin traducir 103 cadenas.
    presentes = set()
    for w in _PALABRA.findall(texto):
        w = w.lower().translate(_ACENTOS)
        for i in range(1, len(w) + 1):
            presentes.add(w[:i])

    reemplazos: list[tuple[str, str]] = []
    n = 0
    for patron, de, a, clave in frases:
        if clave not in presentes:
            continue

        def _rep_frase(m: re.Match, _a: str = a) -> str:
            nonlocal n
            # Los sufijos se buscan por nombre: un invariable no aporta grupo
            # y groupdict() devuelve None en vez del grupo de al lado.
            g = m.groupdict()
            sufijo_primera = g.get("s0")
            sufijo_ultima = g.get(f"s{sum(1 for k in g if k.startswith('w')) - 1}")
            if " " in _a:
                # Dónde cae el plural del núcleo depende de la estructura del
                # destino, no de la del origen:
                #  · Con preposición el núcleo va PRIMERO, igual que en
                #    español: «paredes de bloque» -> «muros en bloque».
                #  · En un compuesto inglés sin preposición el núcleo va al
                #    FINAL: «juntas de dilatación» -> «expansion joints»
                #    (aplicarlo al primer término daba «expansions joint»).
                partes_a = _a.split(" ")
                if any(p.lower() in _PREPOSICIONES for p in partes_a[:-1]):
                    partes_a[0] = pluralizar(partes_a[0], sufijo_primera)
                    partes_a[-1] = pluralizar(partes_a[-1], sufijo_ultima)
                else:
                    # Compuesto inglés: el núcleo del origen es la PRIMERA
                    # palabra («paredes de bloque», «sellado de juntas»), así
                    # que solo su sufijo cuenta. Usar también el de la última
                    # daba «joint sealings» a partir de «sellado de juntas».
                    partes_a[-1] = pluralizar(partes_a[-1], sufijo_primera)
                nuevo = " ".join(partes_a)
            else:
                nuevo = pluralizar(_a, sufijo_ultima or sufijo_primera)
            nuevo = _mismo_caso(m.group(1) or de, nuevo)
            token = "\x01" * (n + 1)
            reemplazos.append((token, nuevo))
            n += 1
            return token

        out = patron.sub(_rep_frase, out)

    # ---- 2) Palabras sueltas ----
    for patron, de, a, clave in palabras:
        if clave not in presentes:
            continue

        def _rep_palabra(m: re.Match, _a: str = a) -> str:
            g = m.groupdict()
            return pluralizar(_mismo_caso(g["w"], _a), g.get("s"))

        out = patron.sub(_rep_palabra, out)

    # ---- 3) Restaurar las frases protegidas (tokens más largos primero,
    #          para que "\x01" no pise a "\x01\x01") ----
    for token, valor in reversed(reemplazos):
        out = out.replace(token, valor)
    return out


@lru_cache(maxsize=32768)
def traducir(texto: str | None, pais_codigo: str | None) -> str:
    """Traduce un texto del catálogo base (VE) al país indicado.

    Si la cadena está en el catálogo, sale de la tabla precalculada con una
    lectura de diccionario; si no (una partida propia del cliente, recién
    escrita), se calcula con el glosario. La variante de inglés se aplica al
    final en los dos caminos, así que una sola tabla EN sirve a los cinco
    mercados anglófonos y cada uno recibe su vocabulario.
    """
    if not texto:
        return texto or ""
    codigo = str(pais_codigo or "").strip().upper()
    if not codigo or codigo == "VE":
        return texto
    mercado = resolver_mercado(codigo)
    # Los cinco mercados ingleses comparten un solo glosario español->inglés:
    # lo que los distingue no es la traducción, sino el vocabulario de obra,
    # y de eso se encarga la variante al final. Sin esto una empresa de
    # Estados Unidos recibía el catálogo en venezolano sin traducir, porque
    # no existe glosarios/US.json.
    glosario = "EN" if mercado["idioma"] == "en" else codigo
    tabla = _cargar_tabla(glosario)
    if texto in tabla:
        out = tabla[texto]
    else:
        out = _traducir_reglas(texto, mercado, glosario)
    return aplicar_variante(out, mercado)


def traducir_recurso_por_codigo(
    texto: str | None, codigo_recurso: str | None, pais_codigo: str | None
) -> str:
    """Traduce un recurso identificado por su código, no por su texto.

    En el descompuesto de una partida la descripción es texto libre: viene del
    Excel que sube el usuario y no tiene por qué coincidir con el catálogo.
    Traducir ese texto «a ojo» cae en el glosario y produce los calcos que se
    quieren evitar, así que ahí el código es la única clave fiable: si el
    recurso es del catálogo se traduce con su redacción propia y, si no, se
    devuelve el texto tal cual, que siempre será mejor que una traducción
    inventada sobre datos que no controlamos.
    """
    if not texto:
        return texto or ""
    mercado = resolver_mercado(str(pais_codigo or "").strip().upper())
    # Solo los mercados anglófonos. En los hispanos el texto ya está en
    # español, que es la lengua base del catálogo, así que se devuelve igual:
    # permite usar el mismo filtro en las dos plantillas (española e inglesa)
    # sin que una de ellas traduzca lo que no debe.
    if mercado.get("idioma") != "en":
        return texto
    codigo = str(codigo_recurso or "").strip()
    if not codigo:
        return texto
    base = _recurso_en_por_codigo().get(codigo)
    if not base:
        return texto
    return aplicar_variante(base, mercado)


def traducir_recurso_para_edicion(
    texto: str | None, codigo_recurso: str | None, pais_codigo: str | None
) -> str:
    """Localiza recursos de catálogo en formularios sin pisar cambios propios.

    La traducción por código es deliberadamente autoritativa para las filas de
    un APU. En un formulario editable, en cambio, solo se sustituye la
    descripción si sigue siendo exactamente la fuente española del catálogo;
    una descripción personalizada (incluida una ya escrita en inglés) se
    conserva para que el usuario pueda guardarla sin pérdidas.
    """
    if not texto:
        return texto or ""
    codigo = str(codigo_recurso or "").strip()
    original = _recurso_es_por_codigo().get(codigo)
    if original and str(texto).strip() == original.strip():
        return traducir_recurso_por_codigo(texto, codigo, pais_codigo)
    return texto


def traducir_partida(partida, pais_codigo: str | None):
    """Devuelve una copia ligera de una Partida/PresupuestoItem con nombre/descripcion traducidos.

    No muta el objeto ORM. Solo traduce campos que ve el cliente.
    """
    if not pais_codigo or str(pais_codigo).upper() in ("", "VE"):
        return partida
    # Copia superficial para no tocar la sesión
    from copy import copy
    copia = copy(partida)
    if hasattr(partida, "nombre"):
        copia.nombre = traducir(getattr(partida, "nombre", ""), pais_codigo)
    if hasattr(partida, "descripcion"):
        copia.descripcion = traducir(getattr(partida, "descripcion", ""), pais_codigo)
    # Campos de categoría visibles
    for campo in ("categoria", "subcategoria", "apartado"):
        if hasattr(partida, campo):
            val = getattr(partida, campo, "")
            if val:
                setattr(copia, campo, traducir(val, pais_codigo))
    return copia
