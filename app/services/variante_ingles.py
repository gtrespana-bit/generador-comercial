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
    "canceled": "cancelled",
    "fiber": "fibre",
    "paneling": "panelling",
    "liter": "litre",
    "per square meter": "per square metre",
    "per cubic meter": "per cubic metre",
    "per linear meter": "per linear metre",
    "per meter": "per metre",
    "color": "colour",
    "aluminum": "aluminium",
    "recognize": "recognise",
    "facade": "façade",
    "troweling": "trowelling",
    "louver": "louvre",
    "stabilized": "stabilised",
    "stabilizing": "stabilising",
    "localized": "localised",
    "localizing": "localising",
    "labeling": "labelling",
    "maneuvering": "manoeuvring",
    "maneuver": "manoeuvre",
    "vapor": "vapour",
    "mold": "mould",
    "molding": "moulding",     # moldura (sustantivo, no «mold» + -ing)
    "matte": "matt",
    "plasticizing": "plasticising",
    "colored": "coloured",     # el grupo de sufijo solo cubre -s y -es
    "gray": "grey",
    "galvanized": "galvanised",
    "neighboring": "neighbouring",
    "neighbor": "neighbour",
    "catalog": "catalogue",
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
    "latex paint": "emulsion paint",
    # Documento comercial: en el Reino Unido lo que un constructor entrega
    # es una «quote», no un «estimate». El participio «estimated» queda a
    # salvo: la clave no lo alcanza porque la palabra no acaba ahí.
    "estimate": "quote",
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
    # El trasdosado no tiene una sola palabra en Estados Unidos: si va
    # pegado al muro es «direct-applied» y si lleva estructura propia,
    # «furred-out». En el Reino Unido las dos cosas se dicen «lining».
    "furred-out drywall wall": "independent drywall wall lining",
    "furred-out party wall": "party wall lining",
    "furred-out wall": "wall lining",
    "furring strips": "battens",
    "furring": "lining",
    "direct-applied drywall": "direct drywall lining",
    "direct-applied board": "direct board lining",
    "direct-applied high hardness drywall": "direct lining of high hardness drywall",
    "direct-applied 12.5 mm drywall": "direct lining of 12.5 mm drywall",
    "backup wall": "inner leaf",
    "fasteners": "fixings",               # herrajes de fijación
    "fastening": "fixing",                # fijación
    "fastened": "fixed",                  # fijado (participio)
    "clay masonry": "clay blockwork",     # fábrica de bloque de arcilla
    "energy retrofit": "energy refurbishment",
    "stripping the formwork": "striking the formwork",  # desencofrado
    "curing and stripping": "curing and striking",
    "the street": "the pavement",         # vía pública ante la parcela
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
    "swing stage": "suspended cradle",    # silleta suspendida de fachada
    "fine grading": "fine trimming",      # refine del fondo de excavación
    "site office": "site hut",            # caseta de obra
    "face brick": "facing brick",         # ladrillo caravista
    "pipe insulation": "pipe lagging",    # coquilla aislante de tubería
    "sod": "turf",                        # grama en panes
    "shoe cabinet": "shoe cupboard",      # zapatero empotrado
    "light fixture": "light fitting",     # luminaria
    "light fixtures": "light fittings",   # luminarias
    "power outlet": "socket outlet",      # punto de fuerza
    "power outlets": "socket outlets",    # puntos de fuerza
    "downspout": "downpipe",              # bajante de aguas de lluvia
    "electrical panel": "consumer unit",  # tablero eléctrico
    "electrical distribution panel": "consumer unit",
    "distribution panel": "consumer unit",
    "ground-fault circuit interrupter": "residual current device",
    "lavatory": "washbasin",              # lavamanos
    "range hood": "cooker hood",          # campana extractora
    "refrigerator": "fridge",             # nevera
    "dryer": "tumble dryer",              # secadora
    "electric range": "electric cooker",  # cocina eléctrica
    "three-way switch": "two-way switch", # interruptor de conmutación
    "cleanout": "inspection chamber",     # registro de aguas servidas
    "mechanical room": "plant room",      # cuarto técnico
    "home theater": "home cinema",        # cine en casa
    "grounding electrode": "earth electrode",
    "semi-gloss": "mid-sheen",            # pintura semibrillo
    "exterior wood": "exterior timber",   # madera exterior
    "interior wood": "interior timber",   # madera interior
    "lumber shutter": "timber shutter",   # persiana de madera
    "walk-in cooler": "cold room",        # cámara frigorífica
    "wood-boring insects": "woodworm",    # carcoma
    "sidewalk": "pavement",               # acera
    "parking lot": "car park",            # estacionamiento
    "insect screen": "fly screen",        # mosquitero
    "scarifying": "scabbling",            # repicado de concreto
    "EIFS": "ETICS",                      # SATE: sigla de cada mercado
    "exterior insulation and finish system":
        "external thermal insulation composite system",
    "bond beam block": "channel block",   # bloque canal
    "wood lintel": "timber lintel",       # dintel de madera
    "overhead garage door": "up-and-over garage door",
    "awning window": "top-hung casement window",
    "wood formwork": "timber formwork",     # encofrado de madera
    "wood purlin": "timber purlin",         # correa de madera
    "wood truss": "timber truss",           # cercha de madera
    "wood joist": "timber joist",           # vigueta de madera
    "structural wood": "structural timber", # madera estructural
    "welded wire mesh": "welded mesh fabric",
    "radiant floor heating": "underfloor heating",
    "fiberglass": "glass fibre",             # fibra de vidrio
    "laundry room": "utility room",          # lavandería
    "sloping fill": "screed to falls",       # pendientado
    "skylight": "rooflight",                 # claraboya, lucernario
    "roof drain": "roof outlet",             # tragante
    "catch basin": "gully",                  # sumidero
    "hose bibb": "garden tap",               # llave de jardín
    "mailbox": "letter box",                 # buzón
    "garbage disposal": "waste disposal unit",
    "bicycle rack": "cycle rack",            # soporte de bicicletas
    "parking lot marking": "car park marking",
    "mud slab": "blinding",                 # concreto pobre de limpieza
    "isolated footing": "pad foundation",   # zapata aislada
    "strip footing": "strip foundation",    # zapata corrida
    "elevator": "lift",                  # ascensor
    "freight elevator": "goods lift",    # ascensor de carga
    "elevator shaft": "lift shaft",      # hueco de ascensor
    "elevator pit": "lift pit",          # foso de ascensor
    "dumbwaiter": "service lift",        # montacargas de cocina
    "test cylinder": "test cube",        # probeta de concreto
    "grease interceptor": "grease trap", # trampa de grasa
    "weatherstripping": "draught seal",  # burlete
    "dump truck": "tipper lorry",                 # volqueta
    "backhoe": "excavator",                       # retroexcavadora
    "plate compactor": "vibrating plate",         # plancha vibratoria
    "brush cutter": "strimmer",                   # desbrozadora
    "occupancy sensor": "presence detector",      # sensor de presencia
    "External insulation and finish system": "External thermal insulation composite system",
    "base cabinet": "base unit",           # mueble bajo de cocina
    "wall cabinet": "wall unit",           # mueble alto de cocina
    "backsplash": "splashback",            # salpicadero
    "medicine cabinet": "bathroom cabinet", # botiquín
    "overmount": "sit-on",                 # lavamanos sobrepuesto
    "closet": "wardrobe",                  # closet empotrado
    "edge banding": "edging tape",         # cantos aplicados
    "drawer slides": "drawer runners",     # correderas
    "shims": "packers",                    # calzos
    "sandwich panel": "composite panel",        # panel sándwich
    "steel shores": "steel props",              # puntales metálicos
    "mat foundation": "raft foundation",          # losa de fundación
    "grade beam": "ground beam",                  # viga de fundación
    "cast-in-place pile": "bored pile",           # pilote vaciado en sitio
    "drilled shaft": "bored pile",                # pilote perforado
    "stirrups": "links",                          # estribos
    "tempered glass": "toughened glass",           # vidrio templado
    "overhead door": "up-and-over door",           # portón levadizo de garaje
    "strike plate": "striking plate",              # cajetín de la cerradura
    "door casing": "architraves",                  # molduras de remate
    "glazed transom": "fanlight",                  # dintel acristalado
    "peephole": "door viewer",                     # mirilla
    "stuccoing": "rendering",               # frisado (gerundio)
    "stuccoed": "rendered",                 # frisado (participio)
    "dabs of adhesive": "dot and dab",      # trasdosado con pelladas

    # ── Instalaciones ──────────────────────────────────────────────────────
    "antenna": "aerial",                    # antena de televisión
    "hoistway": "lift shaft",               # hueco de ascensor
    "transfer switch": "changeover switch",  # tablero de transferencia
    "main distribution board": "main consumer unit",
    "distribution board": "consumer unit",  # tablero eléctrico
    "shut-off valve": "isolating valve",    # llave de corte
    "ground resistance": "earth resistance",
    "ground terminal": "earth terminal",
    "connection to ground": "connection to earth",
    "drainfield": "soakaway",               # campo de infiltración
    "lightning rod": "lightning conductor",
    # «Meter» es «metre» cuando es unidad de longitud y «meter» cuando es
    # contador. La ortografía no puede distinguirlo, así que el compuesto
    # entra aquí para ganar por ser la clave más larga.
    "gas meter": "gas meter",
    "water meter": "water meter",
    "ground fault circuit interrupter": "residual current device",  # diferencial
    "ground fault": "earth fault",

    # ── Oficios (grados del CIJC británico) ────────────────────────────────
    # En EE. UU. el oficial cualificado es «journeyman» y el ayudante
    # «helper». El Reino Unido no usa esas palabras: el Convenio de la
    # Industria de la Construcción (CIJC) clasifica por «craft operative»,
    # «skilled operative» y «general operative», y esos son los términos que
    # aparecen en las nóminas y en las tarifas británicas.
    "Journeyman": "Craft operative",
    "journeyman": "craft operative",
    "Skilled helper": "Skilled operative",
    "skilled helper": "skilled operative",
    "Helper": "General operative",
    "helper": "general operative",

    # ── Residuos y acabados ────────────────────────────────────────────────
    "dumpster": "skip",                      # contenedor de escombro
    "window shades": "blinds",               # persianas
    "stamped concrete": "imprinted concrete",  # concreto estampado
    "stamping mats": "imprinting mats",
    "traffic paint": "line marking paint",   # pintura de demarcación
}

# ── Australia ────────────────────────────────────────────────────────────
# Escribe como el Reino Unido, pero la encimera de cocina es «benchtop».
_VOCABULARIO_AU: dict[str, str] = {
    **_VOCABULARIO_GB,
    "countertop": "benchtop",
    "concrete masonry unit": "concrete block",
    # Los grados del CIJC («craft operative», «general operative») son del
    # convenio británico. Australia no los usa: allí el oficial cualificado es
    # «tradesperson» y el ayudante, «labourer». Canadá sí dice «journeyman»,
    # así que no hereda estas dos y se queda con la base estadounidense.
    "Journeyman": "Tradesperson",
    "journeyman": "tradesperson",
    "Skilled helper": "Skilled labourer",
    "skilled helper": "skilled labourer",
    "Helper": "Labourer",
    "helper": "labourer",
}

_VARIANTES: dict[str, dict[str, str]] = {
    "GB": {**_VOCABULARIO_GB, **_ORTOGRAFIA_GB},
    "IE": {**_VOCABULARIO_GB, **_ORTOGRAFIA_GB},
    "AU": {**_VOCABULARIO_AU, **_ORTOGRAFIA_GB},
    "CA": dict(_ORTOGRAFIA_GB),   # vocabulario estadounidense, ortografía británica
}


# Palabras que empiezan por vocal escrita pero suenan a consonante, así que
# piden «a» y no «an». Sin esta lista, «a unit» saldría como «an unit».
_CONSONANTE_ESCRITA_COMO_VOCAL = frozenset({
    "unit", "units", "user", "users", "utility", "utilities", "uniform",
    "union", "unique", "one", "once", "euro", "euros", "european", "used",
    "useful", "useless", "uv", "uplift",
})

# Letras cuyo nombre empieza por sonido vocálico: F (ef), H (aitch), L (el),
# M (em), N (en), R (ar), S (es), X (ex), además de las vocales. Una sigla
# que empiece por una de ellas pide «an»: «an HVAC duct», «an MDF architrave».
_LETRA_CON_SONIDO_VOCALICO = frozenset("AEFHILMNORSX")


def _es_sigla(palabra: str) -> bool:
    """¿Secuencia de dos o más mayúsculas, como HVAC, MDF, LED o PVC?"""
    return len(palabra) >= 2 and palabra.isalpha() and palabra.isupper()


def _fijar_articulos(texto: str) -> str:
    """Revisa «a» y «an» después de sustituir vocabulario.

    Cambiar «insect screen» por «fly screen» deja el artículo anterior
    colgado: «removal of an fly screen». Ninguna tabla de términos puede
    preverlo, así que se corrige al final mirando cómo empieza la palabra
    siguiente, no cómo empezaba la que había antes.
    """
    def _ajustar(m) -> str:
        articulo, hueco, palabra = m.group(1), m.group(2), m.group(3)
        if _es_sigla(palabra):
            # «an HVAC» se dice «aitch-vac»; «a PVC» se dice «pee-vee-cee».
            suena_a_vocal = palabra[:1].upper() in _LETRA_CON_SONIDO_VOCALICO
        else:
            suena_a_vocal = (
                palabra[:1].lower() in "aeiou"
                and palabra.lower() not in _CONSONANTE_ESCRITA_COMO_VOCAL
            )
        correcto = "an" if suena_a_vocal else "a"
        if articulo.isupper():
            correcto = correcto.upper()
        elif articulo[:1].isupper():
            correcto = correcto.capitalize()
        return correcto + hueco + palabra

    return re.compile(r"\b(a|an|A|An|AN)(\s+)(\w+)").sub(_ajustar, texto)


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
    return _fijar_articulos(texto)


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
