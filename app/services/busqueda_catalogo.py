"""Tesauro de búsqueda del catálogo, independiente del texto mostrado.

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


def variantes_consulta(consulta: str) -> list[list[str]]:
    """Grupos AND de variantes OR para una búsqueda SQL.

    ``hormigón pulido`` se convierte, de forma simplificada, en:
    ``[(hormigon, concreto, ...), (pulido,)]``. Cada grupo debe cumplirse, pero
    dentro del grupo basta una variante.
    """
    originales = re.findall(r"[\w.-]+", str(consulta or "").lower(), flags=re.UNICODE)[:6]
    tokens = normalizar(consulta).split()[:6]
    resultado: list[list[str]] = []
    for indice, token in enumerate(tokens):
        original = originales[indice] if indice < len(originales) else token
        variantes = [original]
        if token != original:
            variantes.append(token)
        for grupo in grupos_sinonimos():
            if any(token in termino.split() for termino in grupo["terminos"]):
                for termino in grupo["terminos"]:
                    if termino not in variantes:
                        variantes.append(termino)
        resultado.append(variantes[:16])
    return resultado


def estadisticas_tesauro() -> dict[str, int]:
    grupos = grupos_sinonimos()
    return {
        "grupos": len(grupos),
        "terminos": sum(len(g["terminos"]) for g in grupos),
        "capitulos_cubiertos": len({c for g in grupos for c in g["capitulos"]}),
    }
