# -*- coding: utf-8 -*-
"""Variantes del inglés por mercado.

Reino Unido y Estados Unidos no redactan lo mismo: «skirting» y «baseboard»
son la misma pieza, «labour» y «labor» la misma palabra. Un presupuesto que
habla de «countertop» en un mercado que dice «worktop» se delata como
escrito para otra parte. Australia e Irlanda tienen sus propias diferencias,
y Canadá es el caso que parte en dos a quien mira solo el idioma: construye
como Estados Unidos (drywall, baseboard) y escribe como el Reino Unido
(labour, centre).

La redacción base del producto es la de **Estados Unidos** (``_BASE``), que
es además el mercado al que resuelve el idioma «en» a secas. Cada mercado
tiene su tabla y ninguna hereda de otra: Reino Unido e Irlanda comparten
bloque porque de hecho escriben igual, no porque se derive uno del otro.

Este módulo no es un corrector ortográfico general. Es la lista cerrada de
vocabulario de obra que aparece en un presupuesto, que es donde una palabra
mal elegida se nota y donde el catálogo se juega la credibilidad.
"""

from __future__ import annotations

import re

# Redacción con la que están escritos los textos en inglés del producto y el
# glosario del catálogo (basedatos_partidas/glosarios/EN.json).
_BASE = "en-US"

# ── Ortografía británica ─────────────────────────────────────────────────
# La comparten Reino Unido, Irlanda, Australia y Canadá. Canadá escribe
# «labour» y «centre» aunque construya con vocabulario estadounidense, así
# que este bloque es lo único que necesita.
_ORTOGRAFIA_GB: dict[str, str] = {
    "labor": "labour",
    "labors": "labours",
    "leveling": "levelling",
    "leveled": "levelled",
    "center": "centre",
    "centers": "centres",
    "organize": "organise",
    "organized": "organised",
    "organization": "organisation",
    "fiber": "fibre",
    "liter": "litre",
    "meter": "metre",
    "color": "colour",
    "aluminum": "aluminium",
    "recognize": "recognise",
    "facade": "façade",
    "troweling": "trowelling",
    "louver": "louvre",
}

# ── Vocabulario de obra británico ────────────────────────────────────────
# Reino Unido e Irlanda. Cada entrada es una pieza o una operación que en
# Estados Unidos se llama de otra forma; no son sinónimos al tuntún, son los
# términos que usa cada oficio en cada sitio.
_VOCABULARIO_GB: dict[str, str] = {
    # Acabados y pintura
    "baseboard": "skirting",
    "countertop": "worktop",
    "drywall": "plasterboard",
    "flat latex paint": "matt emulsion",
    "latex paint": "emulsion",
    "flat paint": "matt paint",
    "construction adhesive": "grab adhesive",
    "patching": "making good",
    "sanding": "rubbing down",
    "caulk": "silicone",
    "shower panel": "shower screen",
    # Albañilería y estructura
    "stucco": "render",
    "concrete masonry unit": "hollow concrete block",
    "concrete masonry": "blockwork",
    "tempered": "toughened",
    "leveling coat": "screed",
    # Instalaciones
    "receptacles": "socket outlets",
    "receptacle": "socket outlet",
    "breaker panel": "consumer unit",
    "piping": "pipework",
    "shutoff valves": "isolating valves",
    "grounding": "earthing",
    "sanitary drain": "sanitary waste",
    # Cocina y baño
    "cooktop": "hob",
    "faucets": "taps",
    "faucet": "tap",
    # Obra en general
    "remodeling": "refurbishment",
    "remodel": "refurbishment",
    "construction debris": "waste and debris",
    "licensed landfill": "licensed tip",
    "site cleanup": "site clearance",
    "window treatments": "soft furnishings",
    "baseboard heating": "skirting heating",
    # Replanteo, apeos y demolición: operaciones que en cada sitio se llaman
    # distinto. «Field layout» y no «layout» a secas porque «layout» aparece
    # con otro sentido en los textos del producto («the layout drawing») y
    # aquí solo se quiere convertir el replanteo.
    "field layout": "setting out",        # replanteo
    "shoring": "propping",                # apeo de losas y vigas
    "shore": "prop",                      # puntal (Acrow prop)
    "lumber": "timber",                   # madera como material
    "fastening": "fixing",                # fijación
    "debris container": "skip",           # bote del escombro
    "concrete placing": "concreting",     # vaciado del concreto
    "exploratory opening": "opening up",  # cata de reconocimiento
    "gypsum board": "plasterboard",       # placa de yeso laminado
    "hardware": "ironmongery",            # herrajes
    "carpentry": "joinery",               # carpintería de taller
    "formwork removal": "striking",       # desencofrado
    "truck": "lorry",                     # camión
    "curb": "kerb",                       # cordón de acera
    "bathtub": "bath",                    # bañera
}

# ── Australia ────────────────────────────────────────────────────────────
# Escribe como el Reino Unido, pero la encimera de cocina es «benchtop».
_VOCABULARIO_AU: dict[str, str] = {
    **_VOCABULARIO_GB,
    "countertop": "benchtop",
    "concrete masonry unit": "concrete block",
}

_VARIANTES: dict[str, dict[str, str]] = {
    "GB": {**_VOCABULARIO_GB, **_ORTOGRAFIA_GB},
    "IE": {**_VOCABULARIO_GB, **_ORTOGRAFIA_GB},
    "AU": {**_VOCABULARIO_AU, **_ORTOGRAFIA_GB},
    "CA": dict(_ORTOGRAFIA_GB),   # vocabulario estadounidense, ortografía británica
}


def _reemplazar(texto: str, tabla: dict[str, str]) -> str:
    """Aplica una tabla de términos respetando mayúsculas y plural.

    Las claves más largas van primero para que «concrete masonry unit» no se
    quede a medias por haber sustituido antes «concrete masonry».
    """
    for de in sorted(tabla, key=len, reverse=True):
        a = tabla[de]
        # El plural se recoge aparte para no escribir a mano cada forma ni
        # estropear «countertops» -> «worktops».
        patron = re.compile(r"\b" + re.escape(de) + r"((?:s|es)?)\b", re.IGNORECASE)

        def _sustituir(m, a=a):
            original, sufijo = m.group(0), m.group(1)
            if original.isupper() and len(original) > 3:
                salida = a.upper()            # BASEBOARD -> SKIRTING
            elif original[:1].isupper():
                salida = a[:1].upper() + a[1:]  # WC -> Toilet, no WC -> TOILET
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

    Estados Unidos (la base), los mercados hispanos y cualquier mercado sin
    tabla devuelven el texto intacto, así que se puede llamar siempre.
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
