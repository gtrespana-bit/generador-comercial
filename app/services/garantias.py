"""Tabla de garantías por familia de obra.

No se garantiza partida a partida: se agrupa lo que hay en el presupuesto
(capítulo + nombre + descripción) en familias habituales de remodelación
(pisos, carpintería, fontanería, electricidad…). Los plazos son de
ejecución / instalación, generosos respecto al mínimo legal o comercial
habitual, y no sustituyen la garantía del fabricante del material.
"""
from __future__ import annotations

import unicodedata
from typing import Iterable


def _norm(texto: str) -> str:
    t = unicodedata.normalize("NFD", (texto or "").lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


# Orden de prioridad: si un texto encaja en varias familias, gana la primera.
# Plazos pensados para remodelación de vivienda (instalación + mano de obra),
# por encima del mínimo habitual y por debajo de una garantía estructural
# de obra nueva (10 años).
FAMILIAS_GARANTIA: list[dict] = [
    {
        "clave": "impermeabilizacion",
        "grupo": "Impermeabilización y cubiertas",
        "plazo": "5 años",
        "alcance": "Estanqueidad de cubiertas, terrazas, duchas y terrazas "
        "transitables ejecutadas por nosotros (membranas, pendientes y "
        "encuentros). No cubre atascos, falta de mantenimiento ni daños "
        "por terceros.",
        "keywords": (
            "impermeab", "cubierta", "azotea", "terraza transitable",
            "membrana", "asfalto", "poliuretano liquido", "sika",
        ),
    },
    {
        "clave": "estructuras",
        "grupo": "Estructuras, tabiques y albañilería",
        "plazo": "5 años",
        "alcance": "Ejecución de estructura, refuerzos, muros, tabiques, "
        "pañetes y obra de fábrica. Incluye fisuras de ejecución. No cubre "
        "asentamiento del edificio preexistente ni movimientos estructurales "
        "ajenos a la obra contratada.",
        "keywords": (
            "estructur", "viga", "columna", "forjado", "losa", "ferral",
            "acero de refuerzo", "encadenado", "dintel", "albanil",
            "muro", "tabique", "tabiquer", "block", "bloque", "ladrillo",
            "hormigon", "concreto", "pañete", "panete", "revoque",
            "obra gruesa", "mamposter", "particion", "cerramiento",
        ),
    },
    {
        "clave": "pisos",
        "grupo": "Pisos, solados y revestimientos",
        "plazo": "5 años",
        "alcance": "Colocación de porcelanato, cerámica, piedra, mármol, "
        "madera de piso y zócalos: adherencia, nivelación y juntas. El "
        "material conserva la garantía del fabricante.",
        "keywords": (
            "piso", "solado", "porcelanato", "ceramica", "azulejo",
            "marmol", "granito", "piedra", "revestim", "alicat",
            "zoclo", "zocalo", "rodapie", "parquet", "laminado",
            "vinilico", "porcelan",
        ),
    },
    {
        "clave": "carpinteria_madera",
        "grupo": "Carpintería de madera (puertas, closets, muebles)",
        "plazo": "3 años",
        "alcance": "Armado, herrajes de instalación, escuadría y acabado de "
        "puertas, closets, vestidores y mobiliario a medida. Excluye "
        "humedad ambiental extrema, golpes y desgaste de uso.",
        "keywords": (
            "carpinter", "closet", "armario", "vestidor", "puerta madera",
            "mueble", "cocina a medida", "gabinete", "melamina",
            "mdf", "chapa", "lacado",
        ),
    },
    {
        "clave": "carpinteria_aluminio",
        "grupo": "Carpintería de aluminio, PVC y vidrio",
        "plazo": "3 años",
        "alcance": "Sellado, escuadría y funcionamiento de ventanas, "
        "mamparas y canceles. El vidrio templado y el herraje de marca "
        "siguen la garantía del fabricante.",
        "keywords": (
            "aluminio", "ventana", "mampara", "cancel", "pvc",
            "vidrier", "cristalera", "fachada ligera",
        ),
    },
    {
        "clave": "fontaneria",
        "grupo": "Fontanería e instalaciones hidrosanitarias",
        "plazo": "5 años",
        "alcance": "Instalación: tuberías, uniones, desagües y puntos de agua "
        "(estanqueidad y funcionamiento). Grifos, pocetas, inodoros, "
        "duchas y demás utensilios: garantía del fabricante.",
        "keywords": (
            "fontan", "plomer", "hidrosanit", "tuberia", "desague",
            "desagüe", "sanitari", "grifer", "llave", "agua caliente",
            "agua fria", "drenaje", "sifon", "inodoro", "lavamanos",
            "ducha", "cisterna",
        ),
    },
    {
        "clave": "electricidad",
        "grupo": "Electricidad e iluminación",
        "plazo": "5 años",
        "alcance": "Instalación: circuitos, tableros, canalizaciones y "
        "puntos de luz. Luminarias, mecanismos (interruptores, tomas) y "
        "equipos electrónicos: garantía del fabricante.",
        "keywords": (
            "electric", "ilumin", "tablero", "breaker", "tomacorriente",
            "interruptor", "cableado", "luminar", "led", "spot",
            "downlight", "punto de luz",
        ),
    },
    {
        "clave": "climatizacion",
        "grupo": "Climatización y ventilación",
        "plazo": "2 años",
        "alcance": "Instalación de equipos de aire acondicionado, extractores "
        "y ductos (anclaje, drenaje de condensados y puesta en marcha). "
        "El equipo en sí mantiene la garantía de fábrica.",
        "keywords": (
            "climatiz", "aire acondicionado", "split", "hvac",
            "ventilacion", "extractor", "ducto", "minisplit",
        ),
    },
    {
        "clave": "gas",
        "grupo": "Instalación de gas",
        "plazo": "5 años",
        "alcance": "Tuberías, uniones y puntos de gas ejecutados por nosotros. "
        "Aparatos (cocina, calentador, caldera): garantía del fabricante.",
        "keywords": (
            "instalacion de gas", "red de gas", "tuberia de gas",
            "punto de gas", "valvula de gas",
        ),
    },
    {
        "clave": "aislamiento",
        "grupo": "Aislamiento térmico y acústico",
        "plazo": "5 años",
        "alcance": "Colocación y continuidad del aislamiento ejecutado "
        "(térmico o acústico). El material sigue la garantía del fabricante.",
        "keywords": (
            "aislamiento", "aislante", "lana de roca", "poliuretano proyectado",
            "acustico", "termico",
        ),
    },
    {
        "clave": "yeso",
        "grupo": "Yeso, drywall y cielos rasos",
        "plazo": "3 años",
        "alcance": "Fijación, juntas y planeidad de tabiques de yeso, "
        "pladur/drywall y cielorrasos. Excluye humedad por filtraciones "
        "ajenas y golpes.",
        "keywords": (
            "drywall", "yeso", "pladur", "cielorraso", "cielo raso",
            "techo falso", "placa de yeso", "gypsum",
        ),
    },
    {
        "clave": "pintura",
        "grupo": "Pintura y acabados superficiales",
        "plazo": "2 años",
        "alcance": "Adherencia y uniformidad de pintura, estuco y barnices "
        "aplicados. No cubre suciedad, humedades posteriores, sol directo "
        "sin mantenimiento ni retoques por uso.",
        "keywords": (
            "pintura", "pintado", "estuco", "barniz", "esmalte",
            "latex", "vinilica",
        ),
    },
    {
        "clave": "vidrio",
        "grupo": "Espejos, vidrios y herrajes decorativos",
        "plazo": "2 años",
        "alcance": "Fijación y sellado de espejos, vidrios decorativos y "
        "herrajes instalados. Roturas por impacto quedan fuera.",
        "keywords": (
            "espejo", "vidrio", "cristal", "herraje", "manijon",
            "bisagra", "cerradur",
        ),
    },
    {
        "clave": "equipamiento",
        "grupo": "Aparatos, sanitarios y electrodomésticos (instalación)",
        "plazo": "2 años",
        "alcance": "Montaje y conexión de sanitarios, grifería y equipos "
        "suministrados e instalados por nosotros. El producto conserva "
        "la garantía del fabricante.",
        "keywords": (
            "aparato", "electrodomest", "calentador", "boiler",
            "campana extractora", "encimera", "horno",
        ),
    },
    {
        "clave": "exteriores",
        "grupo": "Jardinería, riego y exteriores",
        "plazo": "1 año",
        "alcance": "Ejecución de jardinería, riego y pavimentos exteriores. "
        "Plantas vivas: 90 días de prendimiento con riego a cargo del "
        "cliente.",
        "keywords": (
            "jardin", "riego", "cesped", "paisaj", "exteriores",
        ),
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Versión en inglés
#
# La detección se hace sobre el texto del presupuesto, que puede estar en
# cualquiera de los dos idiomas, así que en inglés se buscan las palabras
# clave de los dos lados (las de aquí se suman a las de arriba). Los plazos
# son los mismos: son el compromiso, no el idioma.
# ─────────────────────────────────────────────────────────────────────────────

FAMILIAS_EN: dict[str, dict] = {
    "impermeabilizacion": {
        "grupo": "Waterproofing and roofing",
        "plazo": "5 years",
        "alcance": "Watertightness of roofs, terraces, shower areas and walkable "
        "decks installed by us (membranes, falls and upstands). Does not cover "
        "blockages, lack of maintenance or damage caused by others.",
        "keywords": (
            "waterproof", "roof", "terrace", "deck", "membrane", "tanking",
            "polyurethane", "bitumen", "sealant",
        ),
    },
    "estructuras": {
        "grupo": "Structure, partitions and masonry",
        "plazo": "5 years",
        "alcance": "Execution of the structure, reinforcement, walls, partitions, "
        "rendering and masonry. Includes workmanship cracking. Does not cover "
        "settlement of the existing building or structural movement outside the "
        "works contracted.",
        "keywords": (
            "structur", "beam", "column", "slab", "rebar", "reinforc", "lintel",
            "bricklay", "bricklayer", "wall", "partition", "blockwork", "brick",
            "concrete", "render", "masonry", "screed", "enclosure",
        ),
    },
    "pisos": {
        "grupo": "Flooring, paving and wall tiling",
        "plazo": "5 years",
        "alcance": "Laying of porcelain, ceramic, stone, marble, timber flooring "
        "and skirting: adhesion, levelling and joints. The material keeps its "
        "manufacturer's warranty.",
        "keywords": (
            "floor", "flooring", "tiling", "tile", "porcelain", "ceramic",
            "marble", "granite", "stone", "cladding", "skirting", "baseboard",
            "parquet", "laminate", "vinyl",
        ),
    },
    "carpinteria_madera": {
        "grupo": "Timber joinery (doors, closets, cabinetry)",
        "plazo": "3 years",
        "alcance": "Assembly, fitting hardware, squareness and finish of doors, "
        "closets, walk-in wardrobes and bespoke cabinetry. Excludes extreme "
        "ambient humidity, impact and wear from use.",
        "keywords": (
            "joinery", "carpentry", "closet", "wardrobe", "cabinet", "door",
            "furniture", "kitchen unit", "melamine", "mdf", "veneer", "lacquer",
        ),
    },
    "carpinteria_aluminio": {
        "grupo": "Aluminium, PVC and glass joinery",
        "plazo": "3 years",
        "alcance": "Sealing, squareness and operation of windows, shower screens "
        "and sliding doors. Toughened glass and branded hardware follow the "
        "manufacturer's warranty.",
        "keywords": (
            "aluminium", "aluminum", "window", "shower screen", "pvc", "glazing",
            "curtain wall", "glass",
        ),
    },
    "fontaneria": {
        "grupo": "Plumbing and sanitary installations",
        "plazo": "5 years",
        "alcance": "Installation: pipework, joints, wastes and water outlets "
        "(watertightness and operation). Taps, basins, WCs, showers and other "
        "fittings: manufacturer's warranty.",
        "keywords": (
            "plumb", "sanitary", "pipe", "pipework", "drain", "waste", "tap",
            "faucet", "hot water", "cold water", "sewer", "siphon", "wc",
            "toilet", "basin", "washbasin", "shower", "cistern",
        ),
    },
    "electricidad": {
        "grupo": "Electrical and lighting",
        "plazo": "5 years",
        "alcance": "Installation: circuits, boards, containment and lighting "
        "points. Luminaires, wiring accessories (switches, sockets) and "
        "electronic equipment: manufacturer's warranty.",
        "keywords": (
            "electric", "lighting", "distribution board", "fuse board",
            "consumer unit", "breaker", "breaker panel", "socket",
            "receptacle", "switch", "wiring", "luminaire", "led", "spot",
            "downlight", "light point",
        ),
    },
    "climatizacion": {
        "grupo": "Air conditioning and ventilation",
        "plazo": "2 years",
        "alcance": "Installation of air-conditioning units, extractors and "
        "ductwork (anchoring, condensate drainage and commissioning). The unit "
        "itself keeps its factory warranty.",
        "keywords": (
            "air conditioning", "hvac", "split", "ventilation", "extractor",
            "duct", "minisplit", "cooling",
        ),
    },
    "gas": {
        "grupo": "Gas installation",
        "plazo": "5 years",
        "alcance": "Pipework, joints and gas outlets installed by us. Appliances "
        "(cooker, water heater, boiler): manufacturer's warranty.",
        "keywords": (
            "gas installation", "gas pipe", "gas outlet", "gas valve",
            "gas supply",
        ),
    },
    "aislamiento": {
        "grupo": "Thermal and acoustic insulation",
        "plazo": "5 years",
        "alcance": "Installation and continuity of the insulation carried out "
        "(thermal or acoustic). The material keeps its manufacturer's warranty.",
        "keywords": (
            "insulation", "insulant", "rock wool", "spray polyurethane",
            "acoustic", "thermal",
        ),
    },
    "yeso": {
        "grupo": "Plaster, drywall and ceilings",
        "plazo": "3 years",
        "alcance": "Fixing, jointing and flatness of plasterboard and drywall "
        "partitions and ceilings. Excludes damp from leaks outside our scope and "
        "impact damage.",
        "keywords": (
            "drywall", "plasterboard", "gypsum", "ceiling", "suspended ceiling",
            "stud partition",
        ),
    },
    "pintura": {
        "grupo": "Painting and surface finishes",
        "plazo": "2 years",
        "alcance": "Adhesion and uniformity of applied paint, stucco and "
        "varnishes. Does not cover dirt, later damp, direct sun without "
        "maintenance or touch-ups from use.",
        "keywords": (
            "paint", "painting", "stucco", "varnish", "enamel", "latex",
            "emulsion",
        ),
    },
    "vidrio": {
        "grupo": "Mirrors, glass and decorative hardware",
        "plazo": "2 years",
        "alcance": "Fixing and sealing of mirrors, decorative glass and hardware "
        "installed. Breakage by impact is excluded.",
        "keywords": (
            "mirror", "glass", "crystal", "hardware", "handle", "hinge", "lock",
        ),
    },
    "equipamiento": {
        "grupo": "Appliances, sanitaryware and white goods (installation)",
        "plazo": "2 years",
        "alcance": "Assembly and connection of sanitaryware, taps and equipment "
        "supplied and installed by us. The product keeps its manufacturer's "
        "warranty.",
        "keywords": (
            "appliance", "white goods", "water heater", "boiler",
            "extractor hood", "hob", "oven", "cooker",
        ),
    },
    "exteriores": {
        "grupo": "Landscaping, irrigation and external works",
        "plazo": "1 year",
        "alcance": "Execution of landscaping, irrigation and external paving. "
        "Live plants: 90 days' establishment, with watering the client's "
        "responsibility.",
        "keywords": ("garden", "irrigation", "lawn", "landscap", "external"),
    },
    "general": {
        "grupo": "Remodelling work included",
        "plazo": "2 years",
        "alcance": "Defects in the execution of the work included in this "
        "document. Materials as per manufacturer.",
        "keywords": (),
    },
}



NOTA_LEGAL = (
    "La garantía cubre defectos de ejecución e instalación de los trabajos "
    "incluidos en este presupuesto, a partir de la entrega formal de la obra. "
    "Los materiales y equipos conservan la garantía de su fabricante. Quedan "
    "excluidos el uso indebido, la falta de mantenimiento, las intervenciones "
    "de terceros, las filtraciones o movimientos del inmueble preexistente y "
    "el desgaste normal. Cualquier reclamación se atenderá por escrito y, si "
    "procede, se reparará o repondrá el trabajo defectuoso sin cargo."
)

NOTA_LEGAL_EN = (
    "The warranty covers defects in the execution and installation of the works "
    "included in this estimate, from the formal handover of the works. Materials "
    "and equipment keep their manufacturer's warranty. Excluded are misuse, lack "
    "of maintenance, work carried out by third parties, leaks or movement of the "
    "existing property, and normal wear and tear. Any claim will be handled in "
    "writing and, where applicable, the defective work will be repaired or "
    "replaced at no charge."
)


_EXCLUIR_TEXTO = (
    "demolic", "derribo", "escombro", "limpieza", "desmontaje",
    "desmont", "retiro de", "picado",
)
_EXCLUIR_TEXTO_EN = (
    "demolit", "strip-out", "strip out", "debris", "rubbish", "cleaning",
    "dismantl", "removal of", "hacking", "skip",
)


def _es_ingles(idioma: str | None) -> bool:
    return str(idioma or "es").strip().lower().startswith("en")


def _es_auxiliar_sin_garantia(texto: str, en: bool = False) -> bool:
    """Demolición, picado y limpieza no se garantizan ni contaminan otras familias."""
    n = _norm(texto)
    terminos = _EXCLUIR_TEXTO + _EXCLUIR_TEXTO_EN if en else _EXCLUIR_TEXTO
    return any(k in n for k in terminos)


def _texto_presupuesto(presupuesto, en: bool = False) -> str:
    partes = []
    for cap in getattr(presupuesto, "capitulos", None) or []:
        nombre_cap = cap.nombre or ""
        if _es_auxiliar_sin_garantia(nombre_cap, en):
            continue
        partes.append(nombre_cap)
        for p in cap.partidas or []:
            bloque = " ".join([
                p.nombre or "",
                p.descripcion or "",
                getattr(p, "producto_nombre", "") or "",
            ])
            if _es_auxiliar_sin_garantia(bloque, en):
                continue
            partes.append(bloque)
    return _norm(" ".join(partes))


def _keywords_de(fam: dict, en: bool) -> tuple:
    """En inglés se buscan también las palabras clave en inglés.

    El texto del presupuesto puede estar en cualquiera de los dos idiomas
    (el catálogo base es venezolano), así que en inglés se prueban las dos
    listas: es mejor detectar una familia de más que caer en la tabla
    mínima por un presupuesto que el usuario escribió en inglés.
    """
    if not en:
        return tuple(fam["keywords"])
    extra = FAMILIAS_EN.get(fam["clave"], {}).get("keywords") or ()
    return tuple(fam["keywords"]) + tuple(extra)


def clasificar_familias(presupuesto, idioma: str = "es") -> list[dict]:
    """Devuelve solo las familias presentes en el presupuesto, en orden."""
    en = _es_ingles(idioma)
    texto = _texto_presupuesto(presupuesto, en)
    if not texto.strip():
        return []
    halladas = []
    for fam in FAMILIAS_GARANTIA:
        if any(k in texto for k in _keywords_de(fam, en)):
            ext = FAMILIAS_EN.get(fam["clave"], {}) if en else {}
            halladas.append({
                "clave": fam["clave"],
                "grupo": ext.get("grupo", fam["grupo"]),
                "plazo": ext.get("plazo", fam["plazo"]),
                "alcance": ext.get("alcance", fam["alcance"]),
            })
    return halladas


def nota_legal(idioma: str = "es") -> str:
    """Nota legal de la tabla de garantías en el idioma indicado."""
    return NOTA_LEGAL_EN if _es_ingles(idioma) else NOTA_LEGAL


def familias_para_pdf(presupuesto, idioma: str = "es") -> list[dict]:
    """Familias detectadas, o un conjunto base si no hay coincidencias."""
    halladas = clasificar_familias(presupuesto, idioma)
    if halladas:
        return halladas
    # Presupuesto vacío o nombres poco descriptivos: tabla mínima honesta.
    general = {
        "clave": "general",
        "grupo": "Trabajos de remodelación incluidos",
        "plazo": "2 años",
        "alcance": "Defectos de ejecución de la obra incluida en este "
        "documento. Materiales según fabricante.",
    }
    if _es_ingles(idioma):
        ext = FAMILIAS_EN.get("general", {})
        general = {**general, **{k: v for k, v in ext.items() if k != "keywords"}}
    return [general]
