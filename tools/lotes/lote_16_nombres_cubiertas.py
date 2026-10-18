# -*- coding: utf-8 -*-
"""Nombres de partida — Techos y cubiertas (capítulo completo, 130).

Criterios de este lote:
  · «Cubierta» es roof cuando es el conjunto y roof deck cuando es la
    superficie que recibe la impermeabilización: en inglés de cubiertas
    son dos palabras distintas y se usan en frases distintas.
  · «Teja criolla» es barrel tile, y su sistema de «canal y cobija» es
    pan and cover. No es mission tile ni S-tile: son piezas distintas.
  · «Pendientado» es sloping fill en Estados Unidos y sloping fill en
    Reino Unido. «Maestras» son screed rails.
  · «Limatesa» es hip y «cumbrera» es ridge. «Caballete» es la pieza que
    remata la cumbrera: ridge cap.
  · «Tragante» es roof drain en Estados Unidos y outlet en Reino Unido.
  · «Solape» es lap. «Remonte» de la impermeabilización es upstand.
  · «Lámina alveolar» de policarbonato es multiwall polycarbonate.
"""

LOTE = {
# ── Formación de pendiente y capas ────────────────────────────────────────
"Pendientado de cubierta con mortero aligerado.":
    "Sloping fill to a roof deck with lightweight mortar.",
"Pendientado de cubierta con concreto ligero.":
    "Sloping fill to a roof deck with lightweight concrete.",
"Regularización de soporte de cubierta plana.":
    "Leveling of the substrate of a flat roof.",
"Base de mortero para cubierta de teja.":
    "Mortar base for a tile roof.",
"Barrera de vapor bajo cubierta.":
    "Vapor barrier beneath a roof deck.",
"Aislamiento térmico de cubierta plana con poliestireno.":
    "Thermal insulation of a flat roof with polystyrene.",
"Aislamiento térmico de cubierta con lana mineral.":
    "Thermal insulation of a roof deck with mineral wool.",
"Capa separadora de geotextil en cubierta.":
    "Geotextile separating layer on a roof deck.",
"Replanteo de pendientes y niveles de cubierta.":
    "Field layout of the falls and levels of a roof deck.",
"Maestras de pendiente para cubierta.":
    "Screed rails for the falls of a roof deck.",
"Relleno aligerado de cubierta con bloques de aliviano.":
    "Lightweight fill to a roof deck with filler blocks.",
"Capa de compresión de cubierta con malla.":
    "Structural topping to a roof deck with mesh.",
"Capa de mortero de protección de aislamiento.":
    "Protective mortar layer over insulation.",
"Junta de dilatación de cubierta.":
    "Expansion joint in a roof deck.",
"Cazuela de recogida para desagüe de cubierta.":
    "Sump for a roof drain.",
"Pendientado de cubierta plana con mortero aligerado.":
    "Sloping fill to a flat roof with lightweight mortar.",
"Torta de cemento de protección de cubierta.":
    "Protective cement screed to a roof deck.",
"Piso flotante sobre pedestales en cubierta.":
    "Pedestal-mounted paving on a roof deck.",

# ── Cubierta plana ────────────────────────────────────────────────────────
"Cubierta plana no transitable con membrana de PVC.":
    "Non-trafficable flat roof with a PVC membrane.",
"Cubierta plana transitable con baldosa.":
    "Trafficable flat roof with paving tiles.",
"Cubierta plana con acabado de gravilla.":
    "Flat roof with a gravel finish.",
"Cubierta invertida con aislamiento exterior.":
    "Inverted roof with external insulation.",
"Cubierta plana con membrana líquida de poliuretano.":
    "Flat roof with a liquid polyurethane membrane.",
"Cubierta plana con impermeabilización acrílica.":
    "Flat roof with acrylic waterproofing.",
"Remonte de impermeabilización en paramento.":
    "Waterproofing upstand against a wall.",
"Encuentro de cubierta con peto o muro.":
    "Junction of a roof deck with a parapet or wall.",
"Prueba de estanqueidad de cubierta plana.":
    "Watertightness test of a flat roof.",
"Protección de membrana con plancha de cemento.":
    "Protection of a membrane with cement boards.",
"Cubierta plana de concreto armado.":
    "Reinforced concrete flat roof.",
"Borde y antepecho de cubierta plana.":
    "Edge and parapet of a flat roof.",

# ── Cubierta de teja ──────────────────────────────────────────────────────
"Cubierta de teja criolla de arcilla.":
    "Clay barrel tile roof.",
"Cubierta de teja asfáltica.":
    "Asphalt shingle roof.",
"Cumbrera y remates de cubierta de teja.":
    "Ridge and trims of a tile roof.",
"Cubierta de teja criolla con canal y cobija.":
    "Barrel tile roof laid pan and cover.",
"Cubierta de teja criolla sobre base continua.":
    "Barrel tile roof on a continuous base.",
"Cubierta de teja asfáltica en shingle.":
    "Asphalt shingle roof.",
"Cubierta de teja de concreto.":
    "Concrete tile roof.",
"Cumbrera y limatesa de cubierta de teja.":
    "Ridge and hip of a tile roof.",
"Alero de cubierta de teja.":
    "Eaves of a tile roof.",
"Listonado para cubierta de teja.":
    "Battens for a tile roof.",
"Sustitución de piezas de cubierta de teja.":
    "Replacement of tiles in a tile roof.",
"Teja de remate de borde con gancho.":
    "Verge tile secured with a clip.",
"Cubierta de teja de zinc acanalada vista.":
    "Exposed corrugated zinc tile roof.",
"Canalón oculto bajo alero de teja.":
    "Concealed gutter beneath a tile eaves.",

# ── Cubierta metálica ─────────────────────────────────────────────────────
"Cubierta de lámina metálica acanalada.":
    "Corrugated metal sheet roof.",
"Cubierta de panel sándwich aislado.":
    "Insulated sandwich panel roof.",
"Cubierta translúcida de policarbonato alveolar.":
    "Translucent multiwall polycarbonate roof.",
"Instalación de domo o claraboya en cubierta.":
    "Installation of a dome or skylight in a roof deck.",
"Cubierta de lámina metálica acanalada galvanizada.":
    "Corrugated galvanized metal sheet roof.",
"Cubierta de lámina metálica prepintada.":
    "Prepainted metal sheet roof.",
"Cubierta de panel sándwich con núcleo de poliuretano.":
    "Sandwich panel roof with a polyurethane core.",
"Cubierta de lámina de zinc con fieltro base.":
    "Zinc sheet roof on an underlayment.",
"Cumbrera y caballete de lámina metálica.":
    "Ridge and ridge cap of a metal sheet roof.",
"Alero de lámina metálica.":
    "Eaves of a metal sheet roof.",
"Solape y sellado de cubierta metálica.":
    "Lapping and sealing of a metal roof.",

# ── Cubierta ligera y translúcida ─────────────────────────────────────────
"Cubierta de lámina de policarbonato alveolar.":
    "Multiwall polycarbonate sheet roof.",
"Cubierta de lámina de policarbonato compacto.":
    "Solid polycarbonate sheet roof.",
"Cubierta de lámina de fibrocemento.":
    "Fiber cement sheet roof.",
"Bajante de aguas lluvias en cubierta metálica.":
    "Rainwater downspout on a metal roof.",
"Canalón de recogida en cubierta metálica.":
    "Collection gutter on a metal roof.",
"Cubierta ligera traslúcida de policarbonato.":
    "Lightweight translucent polycarbonate roof.",
"Cubierta ligera de panel de fibra de vidrio.":
    "Lightweight fiberglass panel roof.",
"Marquesina traslúcida de policarbonato.":
    "Translucent polycarbonate canopy.",
"Cubierta de lona o toldo fijo.":
    "Canvas or fixed awning roof.",
"Cubierta ligera de malla sombra.":
    "Lightweight shade netting roof.",
"Cubierta ligera de lámina de policarbonato curvo.":
    "Lightweight curved polycarbonate sheet roof.",
"Cubierta ligera de lámina de zinc delgada.":
    "Lightweight thin zinc sheet roof.",
"Estructura ligera de apoyo para cubierta translúcida.":
    "Lightweight support structure for a translucent roof.",
"Remate lateral de cubierta translúcida.":
    "Side trim of a translucent roof.",
"Cubierta ligera de panel de policarbonato con junta de estanqueidad.":
    "Lightweight polycarbonate panel roof with sealing joints.",
"Cubierta ligera de paneles de policarbonato multicapa.":
    "Lightweight multiwall polycarbonate panel roof.",
"Tragante en cubierta translúcida.":
    "Roof drain in a translucent roof.",
"Cubierta ligera de teja translúcida de policarbonato.":
    "Lightweight translucent polycarbonate tile roof.",
"Cubierta ligera de lámina de acrílico.":
    "Lightweight acrylic sheet roof.",

# ── Estructura de techo ───────────────────────────────────────────────────
"Estructura metálica de techo.": "Steel roof structure.",
"Estructura de madera de techo.": "Wood roof structure.",
"Estructura metálica de techo a dos aguas.": "Steel gable roof structure.",
"Estructura de madera de techo a dos aguas.": "Wood gable roof structure.",
"Correas de acero para cubierta.": "Steel purlins for a roof.",
"Correas de madera aserrada para cubierta.": "Sawn lumber purlins for a roof.",
"Cercha metálica prefabricada de techo.": "Precast steel roof truss.",
"Viga cumbrera de madera.": "Wood ridge beam.",
"Refuerzo de estructura de techo con angulares.":
    "Strengthening of a roof structure with angle sections.",
"Pintura de protección de estructura de techo.":
    "Protective paint on a roof structure.",
"Tratamiento preservante de estructura de madera.":
    "Preservative treatment of a wood structure.",
"Apuntalamiento de estructura de techo existente.":
    "Shoring of an existing roof structure.",
"Viga de amarre perimetral de cubierta.":
    "Perimeter tie beam of a roof.",
"Anclaje de estructura de techo a la losa.":
    "Anchoring of a roof structure to the slab.",

# ── Claraboyas y seguridad ────────────────────────────────────────────────
"Claraboya o lucernario de policarbonato.":
    "Polycarbonate skylight.",
"Claraboya practicable de cubierta.":
    "Opening skylight in a roof deck.",
"Lucernario corrido de policarbonato.":
    "Continuous polycarbonate skylight.",
"Zócalo de claraboya de concreto.":
    "Concrete skylight curb.",
"Escalera de acceso a cubierta.":
    "Access stair to a roof.",
"Línea de vida horizontal en cubierta.":
    "Horizontal lifeline on a roof.",
"Gancho o anclaje de seguridad en cubierta.":
    "Safety hook or anchor on a roof.",
"Pase de instalaciones por cubierta.":
    "Services penetration through a roof deck.",
"Ventilación de cubierta con rejilla.":
    "Roof ventilation with a grille.",
"Claraboya de vidrio templado.":
    "Tempered glass skylight.",
"Marco perimetral de claraboya.":
    "Perimeter frame of a skylight.",
"Reparación de claraboya existente.":
    "Repair of an existing skylight.",

# ── Evacuación de aguas ───────────────────────────────────────────────────
"Canal de recogida de aguas lluvias.":
    "Rainwater collection channel.",
"Bajante de aguas lluvias.": "Rainwater downspout.",
"Tragante o boquilla de desagüe de cubierta.":
    "Roof drain.",
"Alero y remate de borde de cubierta.":
    "Eaves and edge trim of a roof.",
"Canalón de alero de cubierta.":
    "Eaves gutter of a roof.",
"Bajante de aguas lluvias con fijaciones.":
    "Rainwater downspout with fasteners.",
"Boquilla de desagüe de cubierta con rejilla.":
    "Roof drain with a grille.",
"Remate de borde de cubierta con goterón.":
    "Edge trim of a roof with a drip edge.",

# ── Mantenimiento y reparación ────────────────────────────────────────────
"Limpieza y mantenimiento de cubierta.":
    "Cleaning and maintenance of a roof.",
"Reparación puntual de cubierta.":
    "Localized repair of a roof.",
"Revisión y limpieza de cubierta con informe.":
    "Inspection and cleaning of a roof, with a report.",
"Reparación de membrana de cubierta plana.":
    "Repair of the membrane of a flat roof.",
"Reparación de canal o bajante.":
    "Repair of a channel or downspout.",
"Limpieza de canalones y bajantes.":
    "Cleaning of gutters and downspouts.",
"Reposición de tornillería y solapes de cubierta.":
    "Replacement of fasteners and laps in a roof.",
"Sustitución de lámina de cubierta dañada.":
    "Replacement of a damaged roof sheet.",
"Reparación de faldón de cubierta de lámina.":
    "Repair of a slope of a sheet roof.",
"Reparación de faldón de cubierta de teja.":
    "Repair of a slope of a tile roof.",
"Reparación de impermeabilización de cubierta plana.":
    "Repair of the waterproofing of a flat roof.",
"Revisión general de cubierta con informe.":
    "General inspection of a roof, with a report.",
"Sustitución de cumbrera de cubierta.":
    "Replacement of the ridge of a roof.",
"Reparación de claraboya o lucernario.":
    "Repair of a skylight.",
"Refuerzo de estructura de cubierta existente.":
    "Strengthening of an existing roof structure.",
"Tratamiento anticorrosivo de cubierta metálica.":
    "Anti-corrosion treatment of a metal roof.",
"Reparación de junta de dilatación de cubierta.":
    "Repair of an expansion joint in a roof.",
"Sustitución de bajante de aguas lluvias.":
    "Replacement of a rainwater downspout.",
"Sustitución de canal de recogida de aguas lluvias.":
    "Replacement of a rainwater collection channel.",
"Limpieza de cubierta con hidrolavadora.":
    "Pressure washing of a roof.",
"Pintura impermeabilizante de cubierta metálica.":
    "Waterproofing paint on a metal roof.",
"Sustitución de tragante de cubierta.":
    "Replacement of a roof drain.",
}
