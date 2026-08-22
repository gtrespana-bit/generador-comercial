"""Diccionario de búsqueda y sinónimos del catálogo.

El vocabulario de obra cambia por país, oficio y proveedor. Este módulo hace
bidireccionales los grupos de ``sinonimos_busqueda.json`` para que «hormigón»
encuentre «concreto», «enchufe» encuentre «tomacorriente» y «falso techo»
encuentre «cielo raso» sin alterar la terminología venezolana de las partidas.
"""
from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
import re
import unicodedata

_RAIZ = Path(__file__).resolve().parents[2]
_RUTA = _RAIZ / "basedatos_partidas" / "datos" / "sinonimos_busqueda.json"


def normalizar(texto: str) -> str:
    valor = unicodedata.normalize("NFD", str(texto or "").lower())
    valor = "".join(c for c in valor if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", valor).strip()


@lru_cache(maxsize=1)
def grupos_sinonimos() -> tuple[dict, ...]:
    if not _RUTA.is_file():
        return ()
    bruto = json.loads(_RUTA.read_text(encoding="utf-8"))
    salida = []
    for grupo in bruto.get("grupos", []):
        terminos_originales = [grupo.get("principal", ""), *grupo.get("alias", [])]
        terminos = []
        for termino in terminos_originales:
            limpio = normalizar(termino)
            if limpio and limpio not in terminos:
                terminos.append(limpio)
        if len(terminos) < 2:
            continue
        salida.append({
            "capitulos": tuple(str(c) for c in grupo.get("capitulos", [])),
            "terminos": tuple(terminos),
        })
    return tuple(salida)


def _contiene_frase(texto_normal: str, frase: str) -> bool:
    return f" {frase} " in f" {texto_normal} "


def alias_para_texto(texto: str, capitulo: str = "") -> list[str]:
    """Tokens de sinónimos correspondientes a términos presentes en ``texto``."""
    normal = normalizar(texto)
    if not normal:
        return []
    salida: list[str] = []
    vistos: set[str] = set()
    codigo_cap = str(capitulo or "")[:2]
    for grupo in grupos_sinonimos():
        if codigo_cap and grupo["capitulos"] and codigo_cap not in grupo["capitulos"]:
            continue
        if not any(_contiene_frase(normal, termino) for termino in grupo["terminos"]):
            continue
        for termino in grupo["terminos"]:
            for token in termino.split():
                if len(token) >= 2 and token not in vistos:
                    vistos.add(token)
                    salida.append(token)
    return salida


def _variantes_ortograficas(token: str) -> tuple[str, ...]:
    """Añade grafías frecuentes cuando el usuario omite tildes.

    SQLite no dispone de ``unaccent`` y su ``LIKE`` no considera equivalentes
    ``demolicion`` y ``demolición``. Buena parte de las búsquedas se escriben
    desde el móvil sin tildes, así que resolvemos aquí las terminaciones más
    productivas y algunos términos técnicos habituales. PostgreSQL recibe las
    mismas variantes y mantiene exactamente el mismo comportamiento.
    """
    token = str(token or "").strip().lower()
    if not token:
        return ()
    salida = [token]
    if token.endswith("cion") and len(token) > 5:
        salida.append(token[:-3] + "ión")
    equivalencias = {
        "ceramica": "cerámica",
        "ceramico": "cerámico",
        "ceramicas": "cerámicas",
        "ceramicos": "cerámicos",
        "electrica": "eléctrica",
        "electrico": "eléctrico",
        "mecanica": "mecánica",
        "mecanico": "mecánico",
        "lamina": "lámina",
        "laminas": "láminas",
    }
    con_tilde = equivalencias.get(token)
    if con_tilde:
        salida.append(con_tilde)
    return tuple(dict.fromkeys(salida))


def variantes_consulta(consulta: str) -> list[list[str]]:
    """Grupos AND de variantes OR para una búsqueda SQL.

    ``hormigón pulido`` se convierte, de forma simplificada, en:
    ``[(hormigon, concreto, ...), (pulido,)]``. Cada grupo debe cumplirse, pero
    dentro del grupo basta una variante. También conserva y reconstruye tildes
    frecuentes para que ``demolicion`` encuentre ``Demolición`` en SQLite.
    """
    originales = re.findall(r"[\w.-]+", str(consulta or "").lower(), flags=re.UNICODE)[:6]
    tokens = normalizar(consulta).split()[:6]
    resultado: list[list[str]] = []
    for indice, token in enumerate(tokens):
        original = originales[indice] if indice < len(originales) else token
        variantes = list(_variantes_ortograficas(original))
        for variante in _variantes_ortograficas(token):
            if variante not in variantes:
                variantes.append(variante)
        for grupo in grupos_sinonimos():
            if any(token in termino.split() for termino in grupo["terminos"]):
                for termino in grupo["terminos"]:
                    for variante in _variantes_ortograficas(termino):
                        if variante not in variantes:
                            variantes.append(variante)
        resultado.append(variantes[:20])
    return resultado


def estadisticas_diccionario() -> dict[str, int]:
    grupos = grupos_sinonimos()
    return {
        "grupos": len(grupos),
        "terminos": sum(len(g["terminos"]) for g in grupos),
        "capitulos_cubiertos": len({c for g in grupos for c in g["capitulos"]}),
    }
