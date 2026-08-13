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


NOTA_LEGAL = (
    "La garantía cubre defectos de ejecución e instalación de los trabajos "
    "incluidos en este presupuesto, a partir de la entrega formal de la obra. "
    "Los materiales y equipos conservan la garantía de su fabricante. Quedan "
    "excluidos el uso indebido, la falta de mantenimiento, las intervenciones "
    "de terceros, las filtraciones o movimientos del inmueble preexistente y "
    "el desgaste normal. Cualquier reclamación se atenderá por escrito y, si "
    "procede, se reparará o repondrá el trabajo defectuoso sin cargo."
)


_EXCLUIR_TEXTO = (
    "demolic", "derribo", "escombro", "limpieza", "desmontaje",
    "desmont", "retiro de", "picado",
)


def _es_auxiliar_sin_garantia(texto: str) -> bool:
    """Demolición, picado y limpieza no se garantizan ni contaminan otras familias."""
    n = _norm(texto)
    return any(k in n for k in _EXCLUIR_TEXTO)


def _texto_presupuesto(presupuesto) -> str:
    partes = []
    for cap in getattr(presupuesto, "capitulos", None) or []:
        nombre_cap = cap.nombre or ""
        if _es_auxiliar_sin_garantia(nombre_cap):
            continue
        partes.append(nombre_cap)
        for p in cap.partidas or []:
            bloque = " ".join([
                p.nombre or "",
                p.descripcion or "",
                getattr(p, "producto_nombre", "") or "",
            ])
            if _es_auxiliar_sin_garantia(bloque):
                continue
            partes.append(bloque)
    return _norm(" ".join(partes))


def clasificar_familias(presupuesto) -> list[dict]:
    """Devuelve solo las familias presentes en el presupuesto, en orden."""
    texto = _texto_presupuesto(presupuesto)
    if not texto.strip():
        return []
    halladas = []
    for fam in FAMILIAS_GARANTIA:
        if any(k in texto for k in fam["keywords"]):
            halladas.append({
                "clave": fam["clave"],
                "grupo": fam["grupo"],
                "plazo": fam["plazo"],
                "alcance": fam["alcance"],
            })
    return halladas


def familias_para_pdf(presupuesto) -> list[dict]:
    """Familias detectadas, o un conjunto base si no hay coincidencias."""
    halladas = clasificar_familias(presupuesto)
    if halladas:
        return halladas
    # Presupuesto vacío o nombres poco descriptivos: tabla mínima honesta.
    return [
        {
            "clave": "general",
            "grupo": "Trabajos de remodelación incluidos",
            "plazo": "2 años",
            "alcance": "Defectos de ejecución de la obra incluida en este "
            "documento. Materiales según fabricante.",
        }
    ]
