# -*- coding: utf-8 -*-
"""Variantes del inglés por mercado.

Reino Unido y Estados Unidos no redactan lo mismo: «skirting» y «baseboard»
son la misma pieza, «labour» y «labor» la misma palabra, y un presupuesto
que habla de «matt emulsion» en un mercado que dice «flat latex paint» se
delata como escrito para otra parte. Lo mismo pasa con Australia, que dice
«benchtop» donde el Reino Unido dice «worktop».

Este módulo aplica, sobre un texto ya redactado en inglés, las divergencias
del mercado de destino. No es un corrector ortográfico general: es la lista
cerrada de vocabulario de obra que aparece en un presupuesto, que es donde
una palabra mal elegida se nota y donde el catálogo se juega la credibilidad.

La redacción base del producto es británica (``_BASE``), así que Reino Unido
e Irlanda no necesitan ninguna sustitución.
"""

from __future__ import annotations

import re

# Redacción con la que están escritos los textos en inglés del producto.
_BASE = "en-GB"

# ── Vocabulario de obra: Estados Unidos y Canadá comparten materiales ────
# Canadá construye como Estados Unidos (drywall, baseboard) aunque escriba
# como el Reino Unido (labour, centre), así que este bloque es común.
_US_VOCABULARIO: dict[str, str] = {
    # Carpintería y acabados
    "skirting": "baseboard",
    "worktop": "countertop",
    "matt": "flat",
    "emulsion": "latex paint",
    "arrises": "edges",
    "making good": "patching",
    "rubbing down": "sanding",
    "grab adhesive": "construction adhesive",
    "silicone sealing": "caulk sealing",
    # Aparatos sanitarios y cocina
    "WC": "toilet",
    "washbasin": "sink",
    "brassware": "faucets",
    "hob": "cooktop",
    "sanitary waste": "sanitary drain",
    "shower screen": "shower panel",
    # Instalaciones
    "consumer unit": "breaker panel",
    "socket outlets": "receptacles",
    "sockets": "receptacles",
    "socket": "receptacle",
    "pipework": "piping",
    "isolating valves": "shutoff valves",
    "earthing": "grounding",
    # Albañilería y estructura
    "render": "stucco",
    "rendering": "stucco",
    "screed": "leveling coat",
    "toughened": "tempered",
    "hollow concrete block": "concrete masonry unit",
    "blockwork": "concrete masonry",
    # Obra en general
    "refurbishment": "remodel",
    "refurbish": "remodel",
    "waste and debris": "construction debris",
    "licensed tip": "licensed landfill",
    "site clearance": "site cleanup",
    "programme": "schedule",
    "soft furnishings": "window treatments",
}

# ── Ortografía: solo Estados Unidos ──────────────────────────────────────
# Canadá escribe «labour», «centre» y «programme» como el Reino Unido.
_US_ORTOGRAFIA: dict[str, str] = {
    "labour": "labor",
    "labours": "labors",
    "Centre": "Center",
    "centre": "center",
    "organis": "organiz",  # organised/organization -> organized/organization
    "ourite": "orite",     # favourite -> favorite
    "levelling": "leveling",
    "levelled": "leveled",
    "metre": "meter",
    "litre": "liter",
    "fibre": "fiber",
}

# ── Australia ────────────────────────────────────────────────────────────
# Escribe como el Reino Unido, pero la encimera se llama «benchtop».
_AU_VOCABULARIO: dict[str, str] = {
    "worktop": "benchtop",
    "hollow concrete block": "concrete block",
}

_VARIANTES: dict[str, dict[str, str]] = {
    "US": {**_US_VOCABULARIO, **_US_ORTOGRAFIA},
    "CA": dict(_US_VOCABULARIO),
    "AU": dict(_AU_VOCABULARIO),
}


def _reemplazar(texto: str, tabla: dict[str, str]) -> str:
    """Aplica una tabla de términos respetando mayúsculas y plural.

    Las claves más largas van primero para que «sanitary waste» no se quede
    a medias por haber sustituido antes «waste».
    """
    for de in sorted(tabla, key=len, reverse=True):
        a = tabla[de]
        # El plural se recoge aparte para no inventar «baseboards» a mano
        # ni estropear «emulsions» -> «latex paints».
        patron = re.compile(r"\b" + re.escape(de) + r"((?:s|es)?)\b", re.IGNORECASE)

        def _sustituir(m, a=a):
            original, sufijo = m.group(0), m.group(1)
            if original.isupper() and len(original) > 3:
                salida = a.upper()            # SKIRTING -> BASEBOARD
            elif original[:1].isupper():
                salida = a[:1].upper() + a[1:]  # WC -> Toilet (no WC -> TOILET)
            else:
                salida = a
            return salida + sufijo

        texto = patron.sub(_sustituir, texto)
    return texto


def variante_de(mercado) -> str:
    """Variante de inglés de un mercado: «en-US», «en-GB», «en-AU»…"""
    return str((mercado or {}).get("locale") or _BASE).strip()


def aplicar_variante(texto: str | None, mercado: dict | None) -> str:
    """Ajusta un texto en inglés al vocabulario del mercado de destino.

    Los mercados hispanos y los que escriben en inglés británico (la base)
    devuelven el texto intacto, así que se puede llamar siempre sin miedo.
    """
    if not texto:
        return texto or ""
    tabla = _VARIANTES.get(str((mercado or {}).get("codigo") or "").upper())
    if not tabla:
        return texto
    return _reemplazar(texto, tabla)


def necesita_variante(mercado: dict | None) -> bool:
    """¿Este mercado se aparta de la redacción base?"""
    return str((mercado or {}).get("codigo") or "").upper() in _VARIANTES
