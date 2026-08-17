#!/usr/bin/env python3
"""Migra una sola vez el catálogo CT v1 a la taxonomía numérica v2.

La v1 clasificaba cada partida en dos niveles y usaba ``CT-CC-SS-NNN``.
La v2 conserva el código anterior como trazabilidad, añade un apartado real y
publica códigos ``CC.SS.AA.NNN``. La operación es determinista: las partidas se
ordenan por su código anterior y se numeran de diez en diez dentro de cada
apartado.

Este programa queda en el repositorio como documentación ejecutable de la
migración. Se niega a volver a aplicar sobre una taxonomía v2.
"""
from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
import re
import sys

RAIZ = Path(__file__).resolve().parents[1]
BASE = RAIZ / "basedatos_partidas"
DATOS = BASE / "datos"
DESCOMPUESTOS = DATOS / "descompuestos"
CLASIFICACION = DATOS / "clasificacion.json"
MAPA = DATOS / "mapa_migracion_v2.json"

CAPITULOS: dict[str, tuple[str, dict[str, str]]] = {
    "01": ("Actuaciones previas", {
        "01": "Desconexión y aislamiento de servicios existentes",
        "02": "Inspecciones, levantamientos, catas y diagnóstico",
        "03": "Protección de elementos existentes",
        "04": "Cerramientos, barreras de polvo y control de accesos",
        "05": "Andamios y medios de elevación",
        "06": "Apeos, apuntalamientos y estabilización provisional",
        "07": "Replanteos y control geométrico",
        "08": "Instalaciones provisionales y servicios de obra",
    }),
    "02": ("Demoliciones y desmontajes", {
        "01": "Fundaciones",
        "02": "Estructuras",
        "03": "Fachadas",
        "04": "Paredes y particiones",
        "05": "Carpintería, herrería, vidrios y protección solar",
        "06": "Remates y elementos auxiliares",
        "07": "Instalaciones",
        "08": "Aislamientos e impermeabilizaciones",
        "09": "Techos y cubiertas",
        "10": "Revestimientos, pisos y cielos rasos",
        "11": "Equipamiento y mobiliario fijo",
        "12": "Obras exteriores, firmes y pavimentos",
    }),
    "03": ("Acondicionamiento del terreno", {
        "01": "Limpieza, desbroce y retiro de capa vegetal",
        "02": "Excavaciones a cielo abierto",
        "03": "Zanjas, pozos y excavaciones localizadas",
        "04": "Rellenos, bases y compactación",
        "05": "Drenaje provisional, achique y estabilización",
        "06": "Carga y transporte de tierras",
    }),
    "04": ("Fundaciones", {
        "01": "Preparación y mejoramiento del terreno",
        "02": "Bases y zapatas",
        "03": "Vigas de riostra y vigas de fundación",
        "04": "Losas de fundación",
        "05": "Muros de contención",
        "06": "Pilotes y fundaciones profundas",
        "07": "Drenaje y protección de fundaciones",
        "08": "Reparación y refuerzo de fundaciones",
    }),
    "05": ("Estructuras", {
        "01": "Encofrados, cimbras y apeos de ejecución",
        "02": "Acero de refuerzo",
        "03": "Concreto estructural vaciado en sitio",
        "04": "Estructuras metálicas",
        "05": "Estructuras de madera",
        "06": "Losas y entrepisos",
        "07": "Escaleras y rampas estructurales",
        "08": "Anclajes, juntas y conexiones",
        "09": "Reparación y refuerzo estructural",
    }),
    "06": ("Fachadas y particiones", {
        "01": "Fachadas de bloque o ladrillo",
        "02": "Fachadas ligeras y revestidas",
        "03": "Particiones de bloque o ladrillo",
        "04": "Particiones de yeso laminado y sistemas secos",
        "05": "Particiones ligeras, móviles y acristaladas",
        "06": "Dinteles, frentes de losa y remates de vano",
        "07": "Fachadas ventiladas y sistemas de aislamiento exterior",
        "08": "Celosías, defensas y cerramientos especiales",
        "09": "Limpieza, restauración y tratamiento de fachadas",
    }),
    "07": ("Carpintería, herrería, vidrios y protección solar", {
        "01": "Puertas interiores",
        "02": "Puertas exteriores y de seguridad",
        "03": "Ventanas, balconeras y paños fijos",
        "04": "Portones, rejas y cierres metálicos",
        "05": "Barandas y pasamanos",
        "06": "Vidrios, espejos y cerramientos de vidrio",
        "07": "Mamparas de baño y divisiones acristaladas",
        "08": "Persianas, celosías, mosquiteros y protección solar",
        "09": "Herrajes, cerraduras y automatismos",
        "10": "Ajustes, reparación y restauración",
    }),
    "08": ("Remates y ayudas", {
        "01": "Ayudas de albañilería para instalaciones",
        "02": "Rozas, perforaciones y pasos",
        "03": "Recibido de marcos, equipos y pequeños elementos",
        "04": "Sellados, juntas y encuentros",
        "05": "Alféizares, vierteaguas, pasamanos y coronaciones",
        "06": "Bancadas, soportes y bases de equipos",
        "07": "Forrados, cajones y tapajuntas",
        "08": "Perfiles decorativos, molduras y remates especiales",
        "09": "Sellado cortafuego de pasos de instalaciones",
    }),
    "09": ("Instalaciones", {
        "01": "Agua potable y agua caliente",
        "02": "Desagüe sanitario y aguas pluviales",
        "03": "Instalaciones eléctricas",
        "04": "Iluminación",
        "05": "Telecomunicaciones y datos",
        "06": "Audiovisuales, porteros e intercomunicación",
        "07": "Climatización y refrigeración",
        "08": "Ventilación y extracción",
        "09": "Gas combustible",
        "10": "Protección contra incendios",
        "11": "Seguridad, alarmas, CCTV y control de acceso",
        "12": "Domótica y automatización",
        "13": "Protección contra rayos y sobretensiones",
        "14": "Tanques, bombas e hidroneumáticos",
        "15": "Generación, respaldo y energía solar fotovoltaica",
        "16": "Transporte vertical y accesibilidad mecánica",
        "17": "Reparación, pruebas y puesta en marcha",
    }),
    "10": ("Aislamientos e impermeabilizaciones", {
        "01": "Aislamiento térmico",
        "02": "Aislamiento acústico y control de vibraciones",
        "03": "Impermeabilización de fundaciones y muros enterrados",
        "04": "Impermeabilización de techos y terrazas",
        "05": "Impermeabilización de baños, cocinas y áreas húmedas",
        "06": "Impermeabilización de tanques, piscinas y jardineras",
        "07": "Drenajes, geotextiles y capas separadoras",
        "08": "Sellado de juntas y estanqueidad",
        "09": "Tratamiento de filtraciones, humedad y capilaridad",
    }),
    "11": ("Techos y cubiertas", {
        "01": "Formación de pendientes y bases",
        "02": "Cubiertas planas transitables y no transitables",
        "03": "Cubiertas de teja",
        "04": "Cubiertas de lámina metálica",
        "05": "Cubiertas ligeras y traslúcidas",
        "06": "Estructuras y soportes de techo",
        "07": "Claraboyas, lucernarios y accesos",
        "08": "Canales, bajantes, limahoyas y remates",
        "09": "Reparación y mantenimiento de cubiertas",
    }),
    "12": ("Revestimientos y acabados", {
        "01": "Preparación, reparación y regularización de soportes",
        "02": "Frisos, enlucidos y revestimientos de mortero",
        "03": "Enchapados de pared de piezas rígidas",
        "04": "Revestimientos decorativos y especiales de pared",
        "05": "Pisos, pavimentos y sus bases",
        "06": "Escaleras, rodapiés, juntas y remates de piso",
        "07": "Trasdosados y forros interiores",
        "08": "Cielos rasos continuos",
        "09": "Cielos rasos desmontables y ligeros",
        "10": "Pintura interior",
        "11": "Pintura exterior",
        "12": "Pintura y protección de madera y metal",
        "13": "Recubrimientos continuos, industriales y decorativos",
        "14": "Tratamientos de protección y restauración de acabados",
    }),
    "13": ("Equipamiento, mobiliario y señalización", {
        "01": "Mobiliario de cocina",
        "02": "Mesones, topes y salpicaderos",
        "03": "Mobiliario y equipamiento de baño",
        "04": "Closets, alacenas y almacenamiento fijo",
        "05": "Electrodomésticos y equipos integrados",
        "06": "Equipamiento accesible y ayudas técnicas",
        "07": "Señalización interior y exterior",
        "08": "Equipamiento comercial, oficina y áreas comunes",
        "09": "Equipamiento deportivo, recreativo y especial",
    }),
    "14": ("Obras exteriores y urbanismo", {
        "01": "Pavimentos exteriores",
        "02": "Aceras, brocales, rampas y escaleras exteriores",
        "03": "Drenaje exterior",
        "04": "Muros, cercas y cerramientos de parcela",
        "05": "Portones y accesos exteriores",
        "06": "Jardinería y tratamiento del terreno",
        "07": "Redes de riego",
        "08": "Redes exteriores de servicios",
        "09": "Iluminación exterior",
        "10": "Piscinas y áreas recreativas",
        "11": "Pérgolas, jardineras y mobiliario exterior",
    }),
    "15": ("Gestión de residuos y limpieza", {
        "01": "Clasificación y acopio de residuos",
        "02": "Bajada, carga y movimiento interno de escombros",
        "03": "Contenedores y medios de almacenamiento",
        "04": "Transporte y disposición autorizada",
        "05": "Residuos especiales o peligrosos",
        "06": "Limpieza durante la obra",
        "07": "Limpieza final y entrega",
    }),
    "16": ("Control de calidad y ensayos", {
        "01": "Ensayos de concreto, acero y mampostería",
        "02": "Inspección de soldaduras, anclajes y estructura",
        "03": "Pruebas de impermeabilización y estanqueidad",
        "04": "Pruebas de instalaciones sanitarias",
        "05": "Pruebas eléctricas y de puesta a tierra",
        "06": "Pruebas de climatización, ventilación y balanceo",
        "07": "Termografía, humedad y diagnóstico no destructivo",
        "08": "Puesta en marcha, protocolos y documentación final",
    }),
    "17": ("Seguridad y salud en obra", {
        "01": "Protecciones colectivas",
        "02": "Equipos de protección individual",
        "03": "Señalización, delimitación y control de accesos",
        "04": "Seguridad en trabajos en altura",
        "05": "Seguridad en excavaciones y espacios confinados",
        "06": "Protección contra incendios durante la obra",
        "07": "Instalaciones de higiene y bienestar",
        "08": "Gestión, formación y documentación preventiva",
    }),
    "18": ("Rehabilitación energética", {
        "01": "Diagnóstico y evaluación energética",
        "02": "Mejora térmica de fachadas",
        "03": "Mejora térmica de techos y cubiertas",
        "04": "Mejora térmica de pisos y entrepisos",
        "05": "Sustitución y mejora de ventanas y vidrios",
        "06": "Protección solar y control de ganancias térmicas",
        "07": "Mejora de climatización y ventilación",
        "08": "Iluminación eficiente y control",
        "09": "Incorporación de energías renovables",
    }),
}

# Mapeo base: (capítulo v1, subcapítulo v1) ->
# (capítulo v2, subcapítulo v2, apartado v2, nombre del apartado).
BASE_MAP: dict[tuple[str, str], tuple[str, str, str, str]] = {
    ("01", "01"): ("01", "03", "01", "Protección de superficies, mobiliario y elementos"),
    ("01", "02"): ("01", "05", "01", "Andamios y medios de elevación"),
    ("01", "03"): ("01", "06", "01", "Apeos y apuntalamientos"),
    ("01", "04"): ("01", "02", "01", "Catas, detección y levantamientos"),
    ("01", "05"): ("01", "08", "01", "Servicios e instalaciones provisionales"),
    ("02", "01"): ("02", "10", "01", "Pisos y pavimentos"),
    ("02", "02"): ("02", "10", "02", "Revestimientos y frisos de pared"),
    ("02", "03"): ("02", "10", "03", "Cielos rasos"),
    ("02", "04"): ("02", "10", "04", "Trasdosados y forros"),
    ("02", "05"): ("02", "10", "05", "Revestimientos decorativos"),
    ("02", "06"): ("02", "10", "06", "Escaleras y sus revestimientos"),
    ("02", "07"): ("02", "03", "01", "Fachadas y revestimientos exteriores"),
    ("02", "08"): ("02", "04", "01", "Paredes, tabiques y apertura de vanos"),
    ("02", "09"): ("02", "05", "01", "Carpintería, herrería y vidrios"),
    ("02", "10"): ("02", "06", "01", "Remates y elementos accesorios"),
    ("02", "11"): ("02", "07", "08", "Instalaciones diversas"),
    ("02", "12"): ("02", "08", "01", "Aislamientos e impermeabilizaciones"),
    ("02", "13"): ("02", "09", "01", "Techos, cubiertas y drenajes"),
    ("02", "14"): ("02", "11", "01", "Equipamiento y mobiliario fijo"),
    ("02", "15"): ("02", "02", "01", "Estructuras"),
    ("02", "16"): ("02", "01", "01", "Fundaciones"),
    ("02", "17"): ("02", "12", "01", "Obras exteriores y urbanismo"),
    ("03", "01"): ("03", "01", "01", "Limpieza y desbroce"),
    ("03", "02"): ("03", "02", "01", "Excavaciones generales"),
    ("03", "03"): ("03", "04", "01", "Rellenos y compactación"),
    ("03", "04"): ("03", "06", "01", "Carga y transporte de tierras"),
    ("04", "01"): ("04", "02", "01", "Bases y zapatas"),
    ("04", "02"): ("04", "03", "01", "Vigas de riostra"),
    ("04", "03"): ("04", "04", "01", "Losas de fundación"),
    ("04", "04"): ("04", "05", "01", "Muros de contención"),
    ("04", "05"): ("04", "06", "01", "Pilotes y fundaciones profundas"),
    ("05", "01"): ("05", "03", "01", "Elementos de concreto armado"),
    ("05", "02"): ("05", "04", "01", "Estructura metálica"),
    ("05", "03"): ("05", "05", "01", "Estructura de madera"),
    ("05", "04"): ("05", "06", "01", "Losas y entrepisos"),
    ("05", "05"): ("05", "07", "01", "Escaleras estructurales"),
    ("05", "06"): ("05", "09", "01", "Refuerzos y reparaciones estructurales"),
    ("06", "01"): ("06", "03", "01", "Bloque de concreto"),
    ("06", "02"): ("06", "03", "02", "Bloque y ladrillo de arcilla"),
    ("06", "03"): ("06", "04", "01", "Tabiquería de yeso laminado"),
    ("06", "04"): ("06", "05", "01", "Tabiquería de otros materiales"),
    ("06", "05"): ("06", "06", "01", "Dinteles y remates de vano"),
    ("06", "06"): ("06", "03", "03", "Mampostería estructural"),
    ("06", "07"): ("06", "06", "02", "Frentes de losa y cajones de persiana"),
    ("06", "08"): ("06", "05", "02", "Mamparas y tabiques móviles"),
    ("06", "09"): ("06", "09", "01", "Limpieza y tratamiento de fachadas"),
    ("07", "01"): ("12", "02", "01", "Frisos y enlucidos de mortero"),
    ("07", "02"): ("12", "02", "02", "Pastas y acabados de yeso"),
    ("07", "03"): ("12", "03", "01", "Cerámica y porcelanato en paredes"),
    ("07", "04"): ("12", "03", "02", "Piedra natural en paredes"),
    ("07", "05"): ("12", "04", "01", "Revestimientos decorativos y especiales"),
    ("08", "01"): ("12", "05", "01", "Bases, afirmados y nivelación"),
    ("08", "02"): ("12", "05", "03", "Pisos cerámicos y porcelanato"),
    ("08", "03"): ("12", "05", "04", "Pisos de piedra, granito y terrazo"),
    ("08", "04"): ("12", "05", "05", "Pisos de madera y laminados"),
    ("08", "05"): ("12", "05", "06", "Pisos vinílicos y flexibles"),
    ("08", "06"): ("12", "05", "07", "Pisos continuos de concreto y microcemento"),
    ("08", "07"): ("12", "06", "01", "Rodapiés y remates de piso"),
    ("08", "08"): ("12", "06", "02", "Revestimiento de escaleras"),
    ("09", "01"): ("12", "08", "01", "Cielos rasos continuos de yeso laminado"),
    ("09", "02"): ("12", "09", "01", "Cielos desmontables y registrables"),
    ("09", "03"): ("12", "09", "02", "Cielos de PVC y láminas"),
    ("09", "04"): ("12", "09", "03", "Cielos de madera"),
    ("09", "05"): ("12", "09", "04", "Molduras y remates de cielo raso"),
    ("10", "01"): ("10", "04", "02", "Manto asfáltico"),
    ("10", "02"): ("10", "04", "03", "Impermeabilizantes líquidos y acrílicos"),
    ("10", "03"): ("10", "05", "01", "Impermeabilización de áreas húmedas"),
    ("10", "04"): ("10", "01", "01", "Aislamiento térmico y acústico"),
    ("11", "01"): ("11", "06", "01", "Estructura de techo"),
    ("11", "02"): ("11", "03", "01", "Cubiertas de teja"),
    ("11", "03"): ("11", "04", "01", "Cubiertas de lámina metálica"),
    ("11", "04"): ("11", "02", "01", "Cubiertas planas y formación de pendientes"),
    ("11", "05"): ("11", "08", "01", "Canales, bajantes y remates"),
    ("12", "01"): ("09", "01", "01", "Tuberías y montantes de agua"),
    ("12", "02"): ("09", "01", "02", "Puntos de agua"),
    ("12", "03"): ("09", "01", "03", "Llaves y valvulería"),
    ("12", "04"): ("09", "01", "04", "Aparatos sanitarios y grifería"),
    ("12", "05"): ("09", "02", "01", "Tuberías y bajantes de desagüe"),
    ("12", "06"): ("09", "02", "02", "Puntos de desagüe"),
    ("12", "07"): ("09", "14", "01", "Tanques, bombas e hidroneumáticos"),
    ("13", "01"): ("09", "03", "04", "Canalizaciones y cableado"),
    ("13", "02"): ("09", "03", "06", "Puntos, mecanismos y tomacorrientes"),
    ("13", "03"): ("09", "03", "03", "Tableros y protecciones"),
    ("13", "04"): ("09", "04", "01", "Iluminación interior y exterior"),
    ("13", "05"): ("09", "03", "01", "Acometidas y puesta a tierra"),
    ("13", "06"): ("09", "05", "01", "Corrientes débiles y datos"),
    ("14", "01"): ("09", "07", "01", "Climatización y ventilación"),
    ("14", "02"): ("09", "09", "01", "Gas doméstico"),
    ("14", "03"): ("09", "10", "01", "Protección contra incendios"),
    ("14", "04"): ("09", "15", "01", "Sistemas de respaldo eléctrico"),
    ("15", "01"): ("07", "01", "01", "Puertas interiores"),
    ("15", "02"): ("07", "02", "01", "Puertas exteriores y de seguridad"),
    ("15", "03"): ("07", "03", "01", "Ventanas y balconeras"),
    ("15", "04"): ("07", "04", "01", "Rejas, portones y herrería"),
    ("15", "05"): ("13", "04", "01", "Closets y muebles empotrados"),
    ("15", "06"): ("07", "06", "01", "Vidrios y espejos"),
    ("15", "07"): ("07", "05", "01", "Barandas y pasamanos"),
    ("16", "01"): ("12", "01", "01", "Preparación de soportes para pintura"),
    ("16", "02"): ("12", "10", "01", "Pintura interior"),
    ("16", "03"): ("12", "11", "01", "Pintura exterior"),
    ("16", "04"): ("12", "12", "01", "Esmaltes y pintura sobre madera y metal"),
    ("16", "05"): ("12", "13", "01", "Recubrimientos especiales y decorativos"),
    ("17", "01"): ("13", "01", "01", "Mobiliario de cocina"),
    ("17", "02"): ("13", "02", "01", "Mesones y topes"),
    ("17", "03"): ("13", "03", "01", "Mobiliario de baño"),
    ("17", "04"): ("13", "06", "01", "Accesorios, herrajes y ayudas técnicas"),
    ("17", "05"): ("13", "08", "01", "Mobiliario fijo diverso"),
    ("18", "01"): ("14", "01", "01", "Pavimentos exteriores"),
    ("18", "02"): ("14", "02", "01", "Brocales, aceras y drenajes"),
    ("18", "03"): ("14", "04", "01", "Cerramientos de parcela"),
    ("18", "04"): ("14", "06", "01", "Jardinería y riego"),
    ("18", "05"): ("14", "08", "01", "Instalaciones exteriores"),
    ("18", "06"): ("14", "11", "01", "Elementos exteriores complementarios"),
    ("19", "01"): ("15", "04", "01", "Retiro y transporte de escombro"),
    ("19", "02"): ("15", "03", "01", "Contenedores y acopio"),
    ("19", "03"): ("15", "07", "01", "Limpieza de obra"),
    ("20", "01"): ("17", "01", "01", "Protecciones colectivas"),
    ("20", "02"): ("17", "02", "01", "Equipos de protección individual"),
    ("20", "03"): ("17", "03", "01", "Señalización y delimitación"),
    ("20", "04"): ("17", "07", "01", "Instalaciones de bienestar"),
    ("20", "05"): ("17", "08", "01", "Gestión y documentación de seguridad"),
}


def _contiene(texto: str, *palabras: str) -> bool:
    normal = texto.lower()
    return any(p in normal for p in palabras)


def destino(partida: dict) -> tuple[str, str, str, str]:
    """Clasifica una partida v1 y aplica divisiones evidentes por disciplina."""
    old = str(partida["codigo"])
    trozos = old.split("-")
    clave = (trozos[1], trozos[2])
    base = BASE_MAP.get(clave)
    if base is None:
        raise ValueError(f"Sin mapeo para {old} ({clave[0]}.{clave[1]})")
    titulo = str(partida.get("titulo") or "")

    if clave == ("01", "04") and _contiene(titulo, "replanteo", "trazado de ejes"):
        return ("01", "07", "01", "Replanteo y trazado")
    if clave == ("03", "02") and _contiene(titulo, "zanja", "pozo", "localizada"):
        return ("03", "03", "01", "Zanjas, pozos y excavaciones localizadas")
    if clave == ("02", "11"):
        if _contiene(titulo, "climat", "aire acondicionado"):
            return ("02", "07", "01", "Climatización")
        if _contiene(titulo, "eléct", "tablero", "cable"):
            return ("02", "07", "02", "Instalaciones eléctricas")
        if _contiene(titulo, "ilumin", "luminaria"):
            return ("02", "07", "04", "Iluminación")
        if _contiene(titulo, "sanitari", "fontaner", "tubería", "desagüe"):
            return ("02", "07", "03", "Instalaciones sanitarias")
    if clave == ("13", "01") and _contiene(titulo, "cable", "conductor"):
        return ("09", "03", "05", "Conductores y cableado")
    if clave == ("13", "02") and _contiene(titulo, "interruptor", "tomacorriente", "mecanismo"):
        return ("09", "03", "07", "Interruptores y tomacorrientes")
    if clave == ("13", "05") and _contiene(titulo, "tierra"):
        return ("09", "03", "02", "Puesta a tierra")
    if clave == ("13", "06"):
        if _contiene(titulo, "cctv", "alarma", "seguridad"):
            return ("09", "11", "01", "Alarmas, CCTV y seguridad")
        if _contiene(titulo, "portero", "intercom", "antena", "audiovisual"):
            return ("09", "06", "01", "Audiovisuales e intercomunicación")
    if clave == ("14", "01") and _contiene(titulo, "ventil", "extractor", "extracción"):
        return ("09", "08", "01", "Ventilación y extracción")
    if clave == ("15", "02") and _contiene(titulo, "portón"):
        return ("07", "04", "02", "Portones metálicos")
    if clave == ("15", "04") and _contiene(titulo, "baranda", "pasamanos"):
        return ("07", "05", "02", "Barandas metálicas")
    if clave == ("15", "06") and _contiene(titulo, "mampara"):
        return ("07", "07", "01", "Mamparas de baño")
    if clave == ("16", "05") and _contiene(titulo, "barniz", "madera"):
        return ("12", "12", "02", "Barnices y protectores de madera")
    if clave == ("16", "05") and _contiene(titulo, "demarcación", "señalización"):
        return ("13", "07", "01", "Demarcación y señalización pintada")
    if clave == ("18", "02") and _contiene(titulo, "drenaje", "tanquilla", "canal"):
        return ("14", "03", "01", "Canales y registros de drenaje")
    if clave == ("18", "03") and _contiene(titulo, "portón"):
        return ("14", "05", "01", "Portones de acceso")
    if clave == ("18", "04") and _contiene(titulo, "riego"):
        return ("14", "07", "01", "Riego por goteo y aspersión")
    if clave == ("18", "05") and _contiene(titulo, "ilumin"):
        return ("14", "09", "01", "Iluminación exterior")
    if clave == ("19", "01") and _contiene(titulo, "bajada"):
        return ("15", "02", "01", "Bajada y movimiento interno de escombros")
    if clave == ("19", "02") and _contiene(titulo, "clasificación", "recuperación", "acopio"):
        return ("15", "01", "01", "Clasificación y acopio de residuos")
    if clave == ("19", "03") and _contiene(titulo, "periódica", "durante"):
        return ("15", "06", "01", "Limpieza durante la obra")
    if clave == ("20", "01") and _contiene(titulo, "línea de vida", "altura"):
        return ("17", "04", "01", "Líneas de vida y protección en altura")
    if clave == ("20", "02") and _contiene(titulo, "altura", "arnés"):
        return ("17", "04", "02", "Equipos para trabajo en altura")
    return base


def construir_taxonomia(apartados: dict[tuple[str, str, str], str]) -> dict:
    caps: dict[str, dict] = {}
    for cc, (nombre_cap, subs) in CAPITULOS.items():
        nodos_sub = {}
        for ss, nombre_sub in subs.items():
            nodos_sub[ss] = {
                "nombre": nombre_sub,
                "apartados": {
                    aa: nombre
                    for (cap, sub, aa), nombre in sorted(apartados.items())
                    if cap == cc and sub == ss
                },
            }
        caps[cc] = {"nombre": nombre_cap, "subcapitulos": nodos_sub}
    return {
        "_comentario": (
            "Clasificación numérica propia de CotizaT para reforma y remodelación "
            "en Venezuela. Tres niveles de navegación: capítulo, subcapítulo y apartado."
        ),
        "_version": 2,
        "_prefijo": "",
        "_moneda": "USD",
        "_ambito": "reforma",
        "_formato_codigo": "CC.SS.AA.NNN",
        "_nota_codificacion": (
            "Código visible totalmente numérico y propio. Los códigos CT-CC-SS-NNN "
            "de la versión 1 se conservan en codigo_legacy y mapa_migracion_v2.json."
        ),
        "capitulos": caps,
    }


def main() -> int:
    actual = json.loads(CLASIFICACION.read_text(encoding="utf-8"))
    if int(actual.get("_version") or 1) >= 2:
        print("La clasificación ya está en versión 2; no se modifica nada.")
        return 0

    fuentes = sorted(DESCOMPUESTOS.glob("*.json"))
    partidas = []
    apartados: dict[tuple[str, str, str], str] = {}
    por_ruta: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for fuente in fuentes:
        partida = json.loads(fuente.read_text(encoding="utf-8"))
        legacy = str(partida.get("codigo") or fuente.stem)
        if not re.fullmatch(r"CT-\d{2}-\d{2}-\d{3}", legacy):
            raise ValueError(f"Código v1 no reconocido: {legacy}")
        cc, ss, aa, nombre_apartado = destino(partida)
        apartados[(cc, ss, aa)] = nombre_apartado
        partida["_fuente"] = fuente
        partida["_legacy"] = legacy
        partida["_ruta_v2"] = (cc, ss, aa)
        por_ruta[(cc, ss, aa)].append(partida)
        partidas.append(partida)

    mapa = []
    nuevos: dict[Path, dict] = {}
    for ruta, items in sorted(por_ruta.items()):
        cc, ss, aa = ruta
        for indice, partida in enumerate(sorted(items, key=lambda p: p["_legacy"]), 1):
            nuevo = f"{cc}.{ss}.{aa}.{indice * 10:03d}"
            fuente = partida.pop("_fuente")
            legacy = partida.pop("_legacy")
            partida.pop("_ruta_v2")
            partida["codigo_legacy"] = legacy
            partida["codigo"] = nuevo
            partida["capitulo"] = cc
            partida["subcapitulo"] = ss
            partida["apartado"] = aa
            destino_archivo = DESCOMPUESTOS / f"{nuevo}.json"
            if destino_archivo in nuevos:
                raise ValueError(f"Código v2 duplicado: {nuevo}")
            nuevos[destino_archivo] = partida
            cap_nombre = CAPITULOS[cc][0]
            sub_nombre = CAPITULOS[cc][1][ss]
            mapa.append({
                "codigo_legacy": legacy,
                "codigo": nuevo,
                "titulo": partida.get("titulo", ""),
                "capitulo": {"codigo": cc, "nombre": cap_nombre},
                "subcapitulo": {"codigo": f"{cc}.{ss}", "nombre": sub_nombre},
                "apartado": {
                    "codigo": f"{cc}.{ss}.{aa}",
                    "nombre": apartados[(cc, ss, aa)],
                },
            })

    taxonomia = construir_taxonomia(apartados)
    if len(nuevos) != len(fuentes) or len(mapa) != len(fuentes):
        raise RuntimeError("La migración no conserva el número de partidas")

    # Escribe primero en memoria/archivos nuevos y borra los nombres v1 al final.
    for ruta, partida in nuevos.items():
        ruta.write_text(json.dumps(partida, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    nombres_nuevos = {p.resolve() for p in nuevos}
    for fuente in fuentes:
        if fuente.resolve() not in nombres_nuevos:
            fuente.unlink()

    CLASIFICACION.write_text(
        json.dumps(taxonomia, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    MAPA.write_text(json.dumps({
        "_comentario": "Equivalencias de la taxonomía v1 a la v2; no reutilizar códigos retirados.",
        "_version_origen": 1,
        "_version_destino": 2,
        "partidas": mapa,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        f"Migradas {len(mapa)} partidas a {len(apartados)} apartados, "
        f"{sum(len(s) for _, s in CAPITULOS.values())} subcapítulos y "
        f"{len(CAPITULOS)} capítulos."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
