# -*- coding: utf-8 -*-
"""Títulos del árbol del catálogo (capítulos, subcapítulos y apartados).

Las descripciones largas ya tenían 75 lotes traducidos a mano, pero los
títulos del árbol —lo primero que ve un usuario inglés al abrir el
catálogo— nunca tuvieron el suyo: salían de la máquina de reglas palabra
a palabra. El resultado incumplía la primera regla de
``docs/GUIA_TRADUCCION_INGLES_CONSTRUCCION.md`` («no traducir palabra por
palabra si el oficio usa otro término»):

  · «Actuaciones previas» salía «Works priors»: el capítulo de trabajos
    preliminares es «Preliminary work».
  · «Acondicionamiento del terreno» salía «Conditioning of the ground»:
    el capítulo contiene desbroce, excavación, rellenos y achique, es
    decir «Earthwork and site preparation» (MasterFormat div. 31).
  · «Protección solar» salía «protection plot» (la regla leía «solar»
    como parcela) y «respaldo» eléctrico como «backrest» (el de una
    silla): son «solar shading» y «backup power».
  · Quedaban palabras sin traducir («salud», «urbanismo», «firmes»,
    «cimbras», «diversas»), gramática rota («elements existings»,
    «foundations deeps», «Installations temporary») y falsos amigos de
    oficio: «aislamiento» de servicios es isolation, no insulation;
    «fondos» de excavación son bottoms, no undercoats; «pasos» de
    instalaciones son penetrations, no steps; «balanceo» (HVAC) es
    balancing, no sway; «aceras» salían «steels» y «brocales», «frames».

Criterios de este lote:

  · Inglés base de EE. UU. (guía §1); ``variante_ingles`` localiza a
    GB/IE/AU/CA después (shoring→propping, field layout→setting out…).
    Por eso «apeos» queda «shoring» en la base y no «propping»: si la
    base ya dijera propping, la variante duplicaría el término.
  · Se conserva la estructura de capítulos del catálogo; solo cambia la
    terminología, con MasterFormat y el uso corriente de estimadores
    como referencia, no la traducción literal.
  · Léxico fijo: remate = trim (flashing en cubierta), ayudas de
    albañilería = builder's work, friso = render (guía §3), techo en el
    capítulo de cubiertas = roof (ceiling es cielo raso), ayudas
    técnicas = technical aids, corrientes débiles = low-voltage.
  · El lote trabaja a nivel de título y se expande a todas las claves
    reales (con y sin numeración) para que el mismo título se traduzca
    igual en los 18 capítulos.

Solo se incluyen los títulos cuya traducción actual es errónea,
agramatical, está sin traducir o usa un término que el oficio no usa.
Los correctos no se tocan.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
_TABLA_EN = RAIZ / "basedatos_partidas" / "salida" / "traducciones" / "EN.json"
_PATRON = re.compile(r"^(\d{2}(?:\.\d{2}){0,2})\s+(.*)$")

TITULOS: dict[str, str] = {
    # ── Capítulos (nivel 1) ──────────────────────────────────────────────
    "Actuaciones previas": "Preliminary work",
    "Demoliciones y desmontajes": "Demolition and dismantling",
    "Acondicionamiento del terreno": "Earthwork and site preparation",
    "Carpintería, herrería, vidrios y protección solar":
        "Carpentry, metalwork, glazing and solar shading",
    "Remates y ayudas": "Trim work and builder's work",
    "Instalaciones": "Building services (MEP)",
    "Techos y cubiertas": "Roofs and roofing",
    "Obras exteriores y urbanismo": "Exterior and site works",
    "Control de calidad y ensayos": "Quality control and testing",
    "Seguridad y salud en obra": "Construction health and safety",
    "Rehabilitación energética": "Energy retrofit",
    # ── 01 · Previas ─────────────────────────────────────────────────────
    "Desconexión de instalaciones": "Disconnection of services",
    "Desconexión y aislamiento de servicios existentes":
        "Disconnection and isolation of existing services",
    "Aislamiento y cierre de servicios": "Service isolation and shut-off",
    "Protección de elementos existentes": "Protection of existing elements",
    "Cerramientos, barreras de polvo y control de accesos":
        "Enclosures, dust barriers and access control",
    "Control de accesos y señalización de obra": "Access control and site signage",
    "Andamios y medios de elevación": "Scaffolding and lifting equipment",
    "Apeos y apuntalamientos": "Shoring and temporary supports",
    "Apeos, apuntalamientos y estabilización provisional":
        "Shoring, temporary supports and temporary stabilization",
    "Replanteo y trazado": "Field layout",
    "Replanteos y control geométrico": "Field layout and geometric control",
    "Instalaciones provisionales y servicios de obra":
        "Temporary installations and site services",
    "Servicios e instalaciones provisionales": "Temporary services and installations",
    "Instalaciones de bienestar": "Welfare facilities",
    "Instalaciones de higiene y bienestar": "Hygiene and welfare facilities",
    # ── 02 · Demoliciones ────────────────────────────────────────────────
    "Paredes, tabiques y apertura de vanos": "Walls, partitions and cutting of openings",
    "Carpintería, herrería, vidrios y protección solar":
        "Carpentry, metalwork, glazing and solar shading",
    "Remates y elementos accesorios": "Trims and accessories",
    "Remates y elementos auxiliares": "Trim and ancillary items",
    "Remates especiales": "Special trims",
    "Instalaciones diversas": "Miscellaneous installations",
    "Techos, cubiertas y drenajes": "Roofs and roof drainage",
    "Pisos y pavimentos": "Floors and paving",
    "Revestimientos y frisos de pared": "Wall finishes and render",
    "Escaleras y sus revestimientos": "Stairs and stair finishes",
    "Obras exteriores, firmes y pavimentos":
        "Exterior works, pavement bases and paving",
    "Bajada y movimiento interno de escombros": "Internal handling and lowering of debris",
    "Bajada, carga y movimiento interno de escombros":
        "Internal handling, lowering and loading of debris",
    "Retiro y transporte de escombro": "Debris removal and haulage",
    # ── 03 · Terreno ─────────────────────────────────────────────────────
    "Limpieza y desbroce": "Clearing and grubbing",
    "Limpieza, desbroce y retiro de capa vegetal":
        "Clearing, grubbing and topsoil stripping",
    "Excavaciones a cielo abierto": "Open-cut excavation",
    "Excavaciones generales": "General excavation",
    "Estabilización de taludes y fondos": "Stabilization of slopes and excavation bottoms",
    "Carga y transporte de tierras": "Loading and haulage of spoil",
    # ── 04 · Fundaciones ─────────────────────────────────────────────────
    "Preparación y mejoramiento del terreno": "Ground preparation and improvement",
    "Mejoramiento y sustitución de terreno": "Ground improvement and replacement",
    "Compactación y nivelación de fundación": "Compaction and leveling of foundation beds",
    "Bases y zapatas": "Spread footings",
    "Vigas de riostra": "Tie beams",
    "Vigas de riostra y vigas de fundación": "Tie beams and foundation beams",
    "Losas de fundación": "Foundation slabs",
    "Pilotes y fundaciones profundas": "Piles and deep foundations",
    "Drenaje de fundaciones": "Foundation drainage",
    # ── 05 · Estructuras ─────────────────────────────────────────────────
    "Encofrados, cimbras y apeos de ejecución": "Formwork, falsework and construction shoring",
    "Encofrados de madera": "Wood formwork",
    "Cimbras y apeos de ejecución": "Falsework and construction shoring",
    "Concreto estructural vaciado en sitio": "Cast-in-place structural concrete",
    "Elementos de concreto armado": "Reinforced concrete elements",
    "Estructuras de madera": "Wood structures",
    "Losas y entrepisos": "Structural floor slabs",
    "Anclajes y conexiones": "Anchors and connections",
    "Anclajes, juntas y conexiones": "Anchors, joints and connections",
    "Inspección de soldaduras, anclajes y estructura": "Inspection of welds, anchors and structure",
    # ── 06 · Fachadas y particiones ──────────────────────────────────────
    "Bloque de concreto": "Concrete masonry units (CMU)",
    "Fachadas de bloque de concreto": "Concrete block facades",
    "Fachadas de bloque o ladrillo": "Block or brick facades",
    "Fachadas de ladrillo visto": "Exposed brick facades",
    "Fachadas de ladrillo y bloque de arcilla": "Brick and clay-block facades",
    "Fachadas de placa de cemento": "Cement-board facades",
    "Fachadas de panel sándwich y chapa": "Sandwich-panel and sheet-metal facades",
    "Fachadas ligeras y revestidas": "Lightweight and clad facades",
    "Fachadas revestidas ligeras": "Lightweight clad facades",
    "Fachadas ventiladas de panel": "Ventilated panel facades",
    "Fachadas ventiladas y sistemas de aislamiento exterior":
        "Ventilated facades and external insulation systems",
    "Fachadas y revestimientos exteriores": "Facades and exterior cladding",
    "Particiones de bloque o ladrillo": "Block or brick partitions",
    "Particiones de yeso laminado y sistemas secos":
        "Gypsum-board partitions and dry construction",
    "Particiones ligeras, móviles y acristaladas": "Lightweight, movable and glazed partitions",
    "Tabiquería de yeso laminado": "Gypsum board partitions",
    "Tabiquería de otros materiales": "Partitions in other materials",
    "Trasdosados y forros": "Wall linings",
    "Trasdosados y forros interiores": "Interior wall linings",
    "Trasdosados autoportantes de placa de yeso laminado":
        "Self-supporting gypsum-board wall linings",
    "Trasdosados directos y forros adheridos": "Direct-bonded wall linings",
    "Defensas y protecciones de fachada": "Facade guards and protection",
    "Limpieza y restauración de paramentos": "Cleaning and restoration of surfaces",
    # ── 07 · Carpintería y vidrios ───────────────────────────────────────
    "Persianas, celosías, mosquiteros y protección solar":
        "Roller shutters, louvers, insect screens and solar shading",
    "Celosías y romanillas": "Louvers and latticework",
    "Celosías, defensas y cerramientos especiales": "Louvers, guards and special enclosures",
    "Ventanas y balconeras": "Windows and balcony doors",
    "Ventanas, balconeras y paños fijos": "Windows, balcony doors and fixed lights",
    "Mamparas de baño": "Shower enclosures",
    "Mamparas de baño y divisiones acristaladas": "Shower enclosures and glazed partitions",
    "Mamparas y tabiques móviles": "Screens and movable partitions",
    "Puertas exteriores y de seguridad": "Exterior and security doors",
    "Herrajes, cerraduras y automatismos": "Hardware, locks and door operators",
    "Automatismos de puertas y portones": "Door and gate automation",
    "Ajuste y reparación de carpintería": "Carpentry adjustment and repair",
    "Barandas y pasamanos": "Railings and handrails",
    "Alféizares y vierteaguas": "Window sills and weather sills",
    "Alféizares, vierteaguas, pasamanos y coronaciones":
        "Window sills, weather sills, handrails and copings",
    "Dinteles y remates de vano": "Lintels and opening trims",
    "Dinteles, frentes de losa y remates de vano": "Lintels, slab edges and opening trims",
    "Frentes de losa y cajones de persiana": "Slab edges and roller-shutter boxes",
    "Rejas, portones y herrería": "Grilles, gates and metalwork",
    "Portones de acceso": "Access gates",
    "Portones y accesos exteriores": "Gates and exterior access",
    "Portones, rejas y cierres metálicos": "Gates, grilles and metal shutters",
    # ── 08 · Remates y ayudas ────────────────────────────────────────────
    "Accesorios, herrajes y ayudas técnicas": "Accessories, hardware and technical aids",
    "Ayudas de albañilería para instalaciones": "Builder's work in connection with services",
    "Forrados y cajones": "Linings and ceiling bulkheads",
    "Forrados, cajones y tapajuntas": "Linings, bulkheads and cover strips",
    "Forros de placa de cemento y protección": "Cement-board linings and protection",
    "Tapajuntas y remates de carpintería": "Cover strips and carpentry trims",
    "Perfiles decorativos, molduras y remates especiales":
        "Decorative profiles, moldings and special trims",
    "Molduras y perfiles decorativos": "Decorative moldings and trims",
    "Molduras y remates de cielo raso": "Suspended-ceiling moldings and trims",
    "Rozas y regatas": "Chases and grooves",
    "Rozas, perforaciones y pasos": "Chases, drilling and penetrations",
    "Perforaciones y pasos": "Drilling and penetrations",
    "Recibido de marcos y premarcos": "Bedding and fixing of frames and subframes",
    "Recibido de equipos y elementos": "Bedding and fixing of equipment and elements",
    "Recibido de marcos, equipos y pequeños elementos":
        "Bedding and fixing of frames, equipment and small items",
    "Bancadas y soportes": "Equipment bases and supports",
    "Bancadas, soportes y bases de equipos": "Equipment bases and supports",
    "Sellados y juntas": "Sealing and joints",
    "Sellados, juntas y encuentros": "Sealing, joints and junctions",
    "Sellado de juntas de construcción": "Sealing of construction joints",
    "Sellado cortafuego de pasos": "Firestopping of penetrations",
    "Sellado cortafuego de pasos de instalaciones": "Firestopping of service penetrations",
    "Encuentros y remates de estanqueidad": "Watertight junctions and flashings",
    # ── 09 · Instalaciones ───────────────────────────────────────────────
    "Aparatos sanitarios y grifería": "Sanitary fixtures and faucets",
    "Instalaciones sanitarias": "Plumbing installations",
    "Pruebas de instalaciones sanitarias": "Plumbing testing",
    "Agua potable y agua caliente": "Domestic cold and hot water",
    "Puntos de agua": "Water outlets",
    "Puntos de desagüe": "Drainage outlets",
    "Desagüe sanitario y aguas pluviales": "Sanitary and rainwater drainage",
    "Tuberías y bajantes de desagüe": "Drainage pipes and stacks",
    "Tuberías y montantes de agua": "Water pipes and risers",
    "Llaves y valvulería": "Valves and fittings",
    "Tanques, bombas e hidroneumáticos": "Tanks, pumps and pressure-boosting systems",
    "Pruebas de climatización, ventilación y balanceo": "HVAC testing and balancing",
    "Pruebas de impermeabilización y estanqueidad": "Waterproofing and watertightness testing",
    "Pruebas eléctricas y de puesta a tierra": "Electrical and grounding tests",
    "Pruebas y puesta en marcha": "Testing and commissioning",
    "Reparación, pruebas y puesta en marcha": "Repair, testing and commissioning",
    "Puesta en marcha, protocolos y documentación final":
        "Commissioning, protocols and final documentation",
    "Acometidas y puesta a tierra": "Utility connections and grounding",
    "Bajantes y puesta a tierra de protección": "Down conductors and protective grounding",
    "Captación y pararrayos": "Lightning protection",
    "Protección contra incendios": "Fire protection",
    "Protección contra incendios durante la obra": "Fire protection during construction",
    "Protección contra rayos y sobretensiones": "Lightning and surge protection",
    "Protectores contra sobretensiones": "Surge protectors",
    "Tableros y protecciones": "Panelboards and protective devices",
    "Puntos, mecanismos y tomacorrientes": "Wiring devices and receptacles",
    "Puntos de control y paneles": "Control points and panels",
    "Corrientes débiles y datos": "Low-voltage and data systems",
    "Alarmas, CCTV y seguridad": "Alarms, CCTV and security",
    "Seguridad, alarmas, CCTV y control de acceso": "Security, alarms, CCTV and access control",
    "Audiovisuales e intercomunicación": "Audiovisual systems and intercom",
    "Audiovisuales, porteros e intercomunicación": "Audiovisual, door entry and intercom systems",
    "Domótica y automatización": "Home and building automation",
    "Actuadores y módulos de control": "Actuators and control modules",
    "Central de control y pasarelas": "Control hub and gateways",
    "Gas doméstico": "Domestic gas",
    "Generación, respaldo y energía solar fotovoltaica":
        "Power generation, backup and solar PV",
    "Sistemas de respaldo eléctrico": "Electrical backup systems",
    "Iluminación eficiente y control": "Efficient lighting and controls",
    "Iluminación interior y exterior": "Interior and exterior lighting",
    "Instalaciones exteriores": "Exterior installations",
    "Ascensores y plataformas": "Elevators and platform lifts",
    "Transporte vertical y accesibilidad mecánica":
        "Vertical transportation and mechanical accessibility",
    "Salvaescaleras y elevadores de accesibilidad": "Stairlifts and platform lifts",
    # ── 10 · Aislamientos e impermeabilizaciones ─────────────────────────
    "Aislamiento acústico y control de vibraciones": "Acoustic insulation and vibration control",
    "Aislamiento térmico y acústico": "Thermal and acoustic insulation",
    "Suelos flotantes y control de vibraciones": "Floating floors and vibration control",
    "Capas separadoras y de protección": "Separating and protection layers",
    "Drenajes, geotextiles y capas separadoras": "Drainage, geotextiles and separating layers",
    "Drenaje exterior": "Exterior drainage",
    "Impermeabilización de baños, cocinas y áreas húmedas":
        "Waterproofing of bathrooms, kitchens and wet areas",
    "Impermeabilización de áreas húmedas": "Waterproofing of wet areas",
    "Impermeabilización de techos y terrazas": "Roof and terrace waterproofing",
    "Impermeabilizantes líquidos y acrílicos": "Liquid-applied and acrylic waterproofing",
    "Tratamiento de filtraciones": "Leak repair and treatment",
    "Tratamiento de filtraciones, humedad y capilaridad":
        "Treatment of leaks, moisture and rising damp",
    "Tratamiento de humedad y capilaridad": "Moisture and rising-damp treatment",
    # ── 11 · Techos y cubiertas ──────────────────────────────────────────
    "Estructura de techo": "Roof structure",
    "Estructuras y soportes de techo": "Roof structures and supports",
    "Cubiertas de teja": "Tile roofs",
    "Cubiertas ligeras y traslúcidas": "Lightweight and translucent roofs",
    "Cubiertas planas transitables y no transitables":
        "Accessible and non-accessible flat roofs",
    "Cubiertas planas y formación de pendientes": "Flat roofs and slope forming",
    "Formación de pendientes y bases": "Slope formation and bases",
    "Canales y registros de drenaje": "Drainage channels and inspection chambers",
    "Canales, bajantes y remates": "Gutters, downpipes and flashings",
    "Canales, bajantes, limahoyas y remates": "Gutters, downpipes, valleys and flashings",
    "Coronaciones y remates de cubierta": "Roof copings and flashings",
    "Claraboyas, lucernarios y accesos": "Skylights, rooflights and roof access",
    "Cielos de PVC y láminas": "PVC and sheet ceilings",
    "Cielos de madera": "Wood ceilings",
    "Cielos desmontables y registrables": "Demountable and accessible ceilings",
    "Cielos rasos desmontables y ligeros": "Demountable lightweight suspended ceilings",
    # ── 12 · Revestimientos y acabados ───────────────────────────────────
    "Frisos y enlucidos de mortero": "Mortar render and plaster",
    "Frisos, enlucidos y revestimientos de mortero": "Render, plaster and mortar finishes",
    "Revestimientos decorativos": "Decorative finishes",
    "Revestimientos decorativos y especiales": "Decorative and special finishes",
    "Revestimientos decorativos y especiales de pared": "Decorative and special wall finishes",
    "Revestimientos, pisos y cielos rasos": "Finishes, floors and suspended ceilings",
    "Revestimiento de escaleras": "Stair finishes",
    "Recubrimientos continuos, industriales y decorativos":
        "Continuous, industrial and decorative coatings",
    "Recubrimientos especiales y decorativos": "Special and decorative coatings",
    "Cerámica y porcelanato en paredes": "Ceramic and porcelain wall tiling",
    "Enchapados de pared de piezas rígidas": "Rigid wall tiling",
    "Piedra natural en paredes": "Natural stone wall cladding",
    "Pastas y acabados de yeso": "Joint compounds and gypsum finishes",
    "Preparación, reparación y regularización de soportes":
        "Preparation, repair and leveling of substrates",
    "Pisos cerámicos y porcelanato": "Ceramic and porcelain tile floors",
    "Pisos continuos de concreto y microcemento": "Continuous concrete and microcement floors",
    "Pisos de madera y laminados": "Wood and laminate floors",
    "Pisos vinílicos y flexibles": "Vinyl and resilient floors",
    "Pisos, pavimentos y sus bases": "Floors, paving and their bases",
    "Escaleras, rodapiés, juntas y remates de piso": "Stairs, baseboards, joints and floor trims",
    "Rodapiés y remates de piso": "Baseboards and floor trims",
    "Pintura exterior": "Exterior painting",
    "Pintura interior": "Interior painting",
    "Pintura y protección de madera y metal": "Painting and protection of wood and metal",
    "Esmaltes y pintura sobre madera y metal": "Enamels and paint for wood and metal",
    "Barnices y protectores de madera": "Varnishes and wood protection",
    "Restauración de madera y elementos decorativos":
        "Restoration of wood and decorative elements",
    "Restauración de madera y vidrio": "Restoration of wood and glass",
    "Tratamientos de protección y restauración de acabados":
        "Protection and restoration treatments for finishes",
    # ── 13 · Equipamiento ────────────────────────────────────────────────
    "Closets y muebles empotrados": "Closets and built-in cabinets",
    "Mobiliario de baño": "Bathroom furniture",
    "Mobiliario y equipamiento de baño": "Bathroom furniture and equipment",
    "Mobiliario fijo diverso": "Miscellaneous fixed furniture",
    "Mesones y topes": "Countertops and worktops",
    "Mesones, topes y salpicaderos": "Countertops, worktops and backsplashes",
    "Electrodomésticos y equipos integrados": "Appliances and integrated equipment",
    "Equipamiento accesible y ayudas técnicas": "Accessible equipment and technical aids",
    "Equipamiento comercial, oficina y áreas comunes":
        "Commercial, office and common-area equipment",
    "Equipamiento deportivo, recreativo y especial":
        "Sports, recreational and special equipment",
    "Elementos exteriores complementarios": "Ancillary exterior elements",
    # ── 14 · Obras exteriores ────────────────────────────────────────────
    "Pavimentos exteriores": "Exterior paving",
    "Aceras, brocales, rampas y escaleras exteriores":
        "Sidewalks, curbs, ramps and exterior stairs",
    "Brocales, aceras y drenajes": "Curbs, sidewalks and drainage",
    "Muros, cercas y cerramientos de parcela": "Boundary walls, fences and enclosures",
    "Cerramientos de parcela": "Boundary fencing and enclosures",
    "Jardinería y tratamiento del terreno": "Landscaping and ground treatment",
    "Redes de riego": "Irrigation networks",
    "Redes exteriores de servicios": "Exterior utility networks",
    "Piscinas y áreas recreativas": "Swimming pools and recreational areas",
    "Pérgolas, jardineras y mobiliario exterior": "Pergolas, planters and outdoor furniture",
    "Señalización interior y exterior": "Interior and exterior signage",
    "Demarcación y señalización pintada": "Line marking and painted signage",
    # ── 15-18 · Residuos, calidad, seguridad, energía ────────────────────
    "Limpieza de obra": "Construction cleaning",
    "Limpieza durante la obra": "Cleaning during construction",
    "Limpieza final y entrega": "Final cleaning and handover",
    "Transporte y disposición autorizada": "Haulage and licensed disposal",
    "Residuos especiales o peligrosos": "Special or hazardous waste",
    "Ensayos de concreto, acero y mampostería": "Concrete, steel and masonry testing",
    "Termografía, humedad y diagnóstico no destructivo":
        "Thermography, moisture and non-destructive diagnosis",
    "Diagnóstico y evaluación energética": "Energy audit and assessment",
    "Equipos de protección individual": "Personal protective equipment (PPE)",
    "Equipos para trabajo en altura": "Work-at-height equipment",
    "Protecciones colectivas": "Collective protective equipment",
    "Líneas de vida y protección en altura": "Lifelines and fall protection",
    "Seguridad en trabajos en altura": "Safety for work at height",
    "Seguridad en excavaciones y espacios confinados":
        "Safety in excavations and confined spaces",
    "Gestión y documentación de seguridad": "Safety management and documentation",
    "Gestión, formación y documentación preventiva":
        "Preventive management, training and documentation",
    "Señalización, delimitación y control de accesos":
        "Signage, demarcation and access control",
    "Mejora de climatización y ventilación": "Upgrading of HVAC and ventilation",
    "Mejora térmica de fachadas": "Thermal upgrading of facades",
    "Mejora térmica de pisos y entrepisos": "Thermal upgrading of floors and floor slabs",
    "Mejora térmica de techos y cubiertas": "Thermal upgrading of roofs",
    "Sistemas de aislamiento térmico exterior (SATE)":
        "External thermal insulation composite systems (ETICS)",
    "Sustitución y mejora de ventanas y vidrios":
        "Window and glazing replacement and upgrading",
    "Protección solar y control de ganancias térmicas":
        "Solar shading and solar-gain control",
    "Incorporación de energías renovables": "Integration of renewable energy",
    "Inspecciones, levantamientos, catas y diagnóstico":
        "Inspections, surveys, exploratory openings and diagnostics",
}


def _expandir() -> dict[str, str]:
    """Lleva cada título corregido a todas sus claves (con/sin número)."""
    cadenas = json.loads(_TABLA_EN.read_text(encoding="utf-8"))["cadenas"]
    lote: dict[str, str] = {}
    for clave, actual in cadenas.items():
        m = _PATRON.match(clave)
        if clave in TITULOS:
            if actual != TITULOS[clave]:
                lote[clave] = TITULOS[clave]
        elif m and m.group(2) in TITULOS:
            nueva = f"{m.group(1)} {TITULOS[m.group(2)]}"
            if actual != nueva:
                lote[clave] = nueva
    return lote


LOTE = _expandir()

if __name__ == "__main__":
    print(f"titulos corregidos: {len(TITULOS)} · claves del lote: {len(LOTE)}")
