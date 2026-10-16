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

# Raíz del repo: app/services -> ../../basedatos_partidas
BASE_GLOSARIOS = Path(__file__).resolve().parents[2] / "basedatos_partidas" / "glosarios"

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
    de, a)``. Los patrones son inmutables y seguros de compartir entre
    llamadas; el estado por llamada (contador de tokens y lista de
    reemplazos) se crea dentro de :func:`traducir`.
    """
    cambios = _cargar_glosario(codigo)
    frases = []
    for c in sorted(
        (c for c in cambios if " " in c["de"]),
        key=lambda c: -len(c["de"]),
    ):
        de, a = c["de"], c["a"]
        grupos = "".join(rf"({re.escape(w)})(es|s)? " for w in de.split(" "))
        patron = re.compile(r"\b" + grupos.rstrip() + r"\b", re.IGNORECASE)
        frases.append((patron, de, a))
    palabras = []
    for c in cambios:
        de, a = c["de"], c["a"]
        if " " in de:
            continue
        patron = re.compile(rf"\b({re.escape(de)})(es|s)?\b", re.IGNORECASE)
        palabras.append((patron, de, a))
    return frases, palabras


@lru_cache(maxsize=32768)
def traducir(texto: str | None, pais_codigo: str | None) -> str:
    """Traduce un texto del catálogo base (VE) al país indicado.

    *Respeta mayúscula inicial y plural en -s/-es.*
    Si el código es vacío/VE o sin glosario, devuelve el texto tal cual.

    El resultado se cachea: el editor traduce las mismas categorías y
    apartados miles de veces al armar el índice, y rehacer el glosario en
    cada llamada era el grueso del tiempo de ``/presupuestos/nuevo``.
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
    reemplazos: list[tuple[str, str]] = []
    n = 0
    for patron, de, a in frases:
        def _rep_frase(m: re.Match, _a: str = a) -> str:
            nonlocal n
            sufijo_primera = m.group(2)
            sufijo_ultima = m.group(len(m.groups()))
            if " " in _a:
                partes_a = _a.split(" ")
                partes_a[0] = _pluralizar(partes_a[0], sufijo_primera)
                partes_a[-1] = _pluralizar(partes_a[-1], sufijo_ultima)
                nuevo = " ".join(partes_a)
            else:
                nuevo = _pluralizar(_a, sufijo_ultima or sufijo_primera)
            nuevo = _mismo_caso(m.group(1) or de, nuevo)
            token = "\x01" * (n + 1)
            reemplazos.append((token, nuevo))
            n += 1
            return token

        out = patron.sub(_rep_frase, out)

    # ---- 2) Palabras sueltas ----
    for patron, de, a in palabras:
        def _rep_palabra(m: re.Match, _a: str = a) -> str:
            return _pluralizar(_mismo_caso(m.group(1), _a), m.group(2))

        out = patron.sub(_rep_palabra, out)

    # ---- 3) Restaurar las frases protegidas (tokens más largos primero,
    #          para que "\x01" no pise a "\x01\x01") ----
    for token, valor in reversed(reemplazos):
        out = out.replace(token, valor)
    return aplicar_variante(out, mercado)


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
