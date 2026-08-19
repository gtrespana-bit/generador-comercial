"""Traducción de terminología de obra por país (LatAm) — runtime.

El catálogo base se guarda en venezolano (friso, rodapié, losa, encofrado...).
Los glosarios `basedatos_partidas/glosarios/{CO,MX,EC,PE}.json` contienen
mapeos VE→CO/MX/EC/PE con 70-120 entradas cada uno.

Esta capa NO reescribe archivos: traduce al vuelo al mostrar catálogo,
presupuestos y PDF, respetando mayúscula inicial y plural en -s/-es,
igual que `basedatos_partidas/terminologia.py:sustituir`.

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
    # Normaliza a lista de {de,a}
    out = []
    for c in cambios:
        de = str(c.get("de") or "").strip()
        a = str(c.get("a") or "").strip()
        if de and a and de.lower() != a.lower():
            out.append({"de": de, "a": a})
    return out


def _mismo_caso(origen: str, destino: str) -> str:
    if origen[:1].isupper():
        return destino[:1].upper() + destino[1:]
    return destino


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
    for c in cambios:
        de, a = c["de"], c["a"]
        # Compila por cada término; cachear el regex sería micro-optimización
        # innecesaria para 100 términos y textos de <500 chars.
        patron = re.compile(rf"\b({re.escape(de)})(es|s)?\b", re.IGNORECASE)

        def _rep(m: re.Match, _a=a) -> str:
            plural = m.group(2) or ""
            nuevo = _mismo_caso(m.group(1), _a)
            if not plural:
                return nuevo
            return nuevo + ("es" if nuevo[-1:] not in "aeiou" else "s")

        out = patron.sub(_rep, out)
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
