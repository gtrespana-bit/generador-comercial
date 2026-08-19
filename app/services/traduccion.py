"""Traducción de terminología de obra por país (LatAm) — runtime.

El catálogo base se guarda en venezolano (friso, rodapié, losa, encofrado...).
Los glosarios `basedatos_partidas/glosarios/{CO,MX,EC,PE}.json` contienen
mapeos VE→CO/MX/EC/PE con 70-130 entradas cada uno.

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
from functools import lru_cache
from pathlib import Path

# Raíz del repo: app/services -> ../../basedatos_partidas
BASE_GLOSARIOS = Path(__file__).resolve().parents[2] / "basedatos_partidas" / "glosarios"

# Mapeo nombre de país (cfg.empresa_pais) -> código ISO
_NOMBRE_A_CODIGO = {
    "venezuela": "VE",
    "colombia": "CO",
    "méxico": "MX", "mexico": "MX",
    "ecuador": "EC",
    "perú": "PE", "peru": "PE",
    "chile": "CL", "argentina": "AR", "uruguay": "UY",
    "paraguay": "PY", "bolivia": "BO", "república dominicana": "DO",
    "dominicana": "DO", "panamá": "PA", "panama": "PA",
    "costa rica": "CR", "guatemala": "GT", "honduras": "HN",
    "el salvador": "SV", "nicaragua": "NI",
    "latinoamérica": "", "latinoamerica": "",
}

_SIN_ACENTO = str.maketrans("áéíóú", "aeiou")


def codigo_desde_pais(nombre_pais: str | None) -> str:
    if not nombre_pais:
        return ""
    clave = str(nombre_pais).strip().lower()
    # limpia acentos simples para el mapa
    clave = clave.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
    return _NOMBRE_A_CODIGO.get(clave, "")


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


def traducir(texto: str | None, pais_codigo: str | None) -> str:
    """Traduce un texto del catálogo base (VE) al país indicado.

    *Respeta mayúscula inicial y plural en -s/-es.*
    Si el código es vacío/VE o sin glosario, devuelve el texto tal cual.
    """
    if not texto:
        return texto or ""
    codigo = str(pais_codigo or "").strip().upper()
    if not codigo or codigo == "VE":
        return texto
    cambios = _cargar_glosario(codigo)
    if not cambios:
        return texto
    out = texto

    # ---- 1) Frases (con espacios): más largas primero y protegidas ----
    # El texto sustituido se marca con un token sin caracteres de palabra para
    # que los mapeos de palabra posteriores no lo vuelvan a tocar.
    # El plural español de una frase puede aparecer en el sustantivo
    # («paredes de bloque»), en el último término («cielos rasos») o en
    # ambos, así que cada palabra admite un sufijo -es/-s opcional.
    frases = sorted(
        (c for c in cambios if " " in c["de"]),
        key=lambda c: -len(c["de"]),
    )
    reemplazos: list[tuple[str, str]] = []
    n = 0
    for c in frases:
        de, a = c["de"], c["a"]
        grupos = "".join(rf"({re.escape(w)})(es|s)? " for w in de.split(" "))
        patron = re.compile(r"\b" + grupos.rstrip() + r"\b", re.IGNORECASE)

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
    for c in cambios:
        de, a = c["de"], c["a"]
        if " " in de:
            continue
        patron = re.compile(rf"\b({re.escape(de)})(es|s)?\b", re.IGNORECASE)

        def _rep_palabra(m: re.Match, _a: str = a) -> str:
            return _pluralizar(_mismo_caso(m.group(1), _a), m.group(2))

        out = patron.sub(_rep_palabra, out)

    # ---- 3) Restaurar las frases protegidas (tokens más largos primero,
    #          para que "\x01" no pise a "\x01\x01") ----
    for token, valor in reversed(reemplazos):
        out = out.replace(token, valor)
    return out


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
