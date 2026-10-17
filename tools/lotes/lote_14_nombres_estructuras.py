# -*- coding: utf-8 -*-
"""Nombres de partida — Estructuras (capítulo completo, 170).

Criterios de este lote:
  · «Encofrado» es formwork y «desencofrado» es stripping. «Cimbra» es
    falsework, la estructura provisional que sostiene el encofrado, que
    no es lo mismo que el molde.
  · «Apuntalamiento» es shoring en Estados Unidos y propping en Reino
    Unido; «puntal» es shore o prop, según el mercado.
  · «Acero de refuerzo» es reinforcement: en un presupuesto se nombra por
    la pieza que arma, «column reinforcement», no por el material.
  · «Losa nervada» es ribbed slab y «losa aligerada» es lightweight slab.
    Los bloques que aligeran son filler blocks y los «casetones» son
    waffle pods, que dan nombre al forjado reticular (waffle slab).
  · «Anime» es el venezolanismo del poliestireno expandido: EPS void
    former en inglés.
  · «Encamisado» de columna es column jacketing.
  · «Conector de cortante» es shear connector y «anclaje químico» es
    chemical anchor.
"""

LOTE = {
# ── Encofrados ────────────────────────────────────────────────────────────
"Encofrado de madera de columna.": "Wood formwork to a column.",
"Encofrado de madera de viga.": "Wood formwork to a beam.",
"Encofrado de losa maciza.": "Formwork to a solid slab.",
"Encofrado de escalera.": "Formwork to a stair.",
"Encofrado de muro de concreto.": "Formwork to a concrete wall.",
"Encofrado de losa de borde.": "Formwork to a slab edge.",
"Encofrado metálico de columna.": "Metal formwork to a column.",
"Encofrado metálico de muro.": "Metal formwork to a wall.",
"Encofrado de losa con sistema modular.": "Formwork to a slab with a modular system.",
"Cimbra y apuntalamiento de losa.": "Falsework and shoring to a slab.",
"Apeo de encofrado de viga.": "Shoring to the formwork of a beam.",
"Encofrado y desencofrado de columna.": "Formwork and stripping to a column.",
"Encofrado y desencofrado de viga.": "Formwork and stripping to a beam.",
"Encofrado a dos caras de pantalla estructural.":
    "Double-face formwork to a structural wall.",
"Encofrado de losa maciza sobre puntales.":
    "Formwork to a solid slab on shores.",
"Encofrado de escalera de concreto armado.":
    "Formwork to a reinforced concrete stair.",
"Encofrado de escalera de concreto.": "Formwork to a concrete stair.",

# ── Acero de refuerzo ─────────────────────────────────────────────────────
"Acero de refuerzo para columna.": "Column reinforcement.",
"Acero de refuerzo para viga.": "Beam reinforcement.",
"Acero de refuerzo en losas.": "Reinforcement in slabs.",
"Acero de refuerzo para escalera.": "Stair reinforcement.",
"Acero de refuerzo en muros.": "Reinforcement in walls.",
"Acero de refuerzo en vigas de amarre.": "Reinforcement in tie beams.",
"Malla electrosoldada para losa.": "Welded wire mesh for a slab.",
"Malla electrosoldada en muro.": "Welded wire mesh in a wall.",
"Acero de refuerzo en pantalla.": "Reinforcement in a structural wall.",
"Acero de refuerzo en dintel.": "Reinforcement in a lintel.",
"Acero de refuerzo en viga de corona.": "Reinforcement in a ring beam.",
"Acero de refuerzo en columnas.": "Reinforcement in columns.",
"Acero de refuerzo en vigas.": "Reinforcement in beams.",
"Acero de refuerzo en pantalla o muro estructural.":
    "Reinforcement in a structural wall.",
"Acero de refuerzo en losa maciza.": "Reinforcement in a solid slab.",
"Acero de refuerzo en escalera.": "Reinforcement in a stair.",
"Colocación de acero en escalera.": "Placing of reinforcement in a stair.",

# ── Concreto ──────────────────────────────────────────────────────────────
"Concreto para columna.": "Concrete for a column.",
"Concreto para viga.": "Concrete for a beam.",
"Vaciado de concreto en columna.": "Concrete pour in a column.",
"Vaciado de concreto en viga.": "Concrete pour in a beam.",
"Vaciado de concreto en losa maciza.": "Concrete pour in a solid slab.",
"Concreto para muro estructural.": "Concrete for a structural wall.",
"Vaciado de concreto en escalera.": "Concrete pour in a stair.",
"Concreto de alta resistencia.": "High-strength concrete.",
"Curado de concreto estructural.": "Curing of structural concrete.",
"Concreto con aditivo plastificante.": "Concrete with a plasticizing admixture.",
"Vaciado de concreto en viga de amarre.": "Concrete pour in a tie beam.",
"Concreto para viga de corona.": "Concrete for a ring beam.",
"Concreto para dintel.": "Concrete for a lintel.",
"Concreto para losa nervada.": "Concrete for a ribbed slab.",
"Acabado de superficie de concreto.": "Finishing of a concrete surface.",
"Concreto para rampa estructural.": "Concrete for a structural ramp.",
"Vaciado de concreto en zapata de medianería.":
    "Concrete pour in a party wall footing.",
"Concreto para losa de entrepiso.": "Concrete for an intermediate floor slab.",
"Concreto para pantalla estructural.": "Concrete for a structural wall.",
"Concreto para losa maciza.": "Concrete for a solid slab.",
"Concreto para escalera de concreto armado.":
    "Concrete for a reinforced concrete stair.",
"Vaciado de concreto en escalera de obra.": "Concrete pour in a site stair.",

# ── Estructura metálica ───────────────────────────────────────────────────
"Suministro y montaje de estructura metálica.":
    "Supply and erection of steelwork.",
"Placa base con pernos de anclaje para columna metálica.":
    "Base plate with anchor bolts for a steel column.",
"Soldadura de conexiones estructurales en obra.":
    "Site welding of structural connections.",
"Imprimación anticorrosiva de estructura metálica.":
    "Anti-corrosion primer on steelwork.",
"Correas metálicas para estructura de techo.":
    "Steel purlins for a roof structure.",
"Montaje de estructura metálica en obra.": "Erection of steelwork on site.",
"Placa base con pernos para columna.": "Base plate with bolts for a column.",
"Soldadura de conexiones estructurales.": "Welding of structural connections.",
"Imprimación anticorrosiva de estructura.": "Anti-corrosion primer on the structure.",
"Correas metálicas para techo.": "Steel purlins for a roof.",
"Estructura metálica para mezzanina.": "Steelwork for a mezzanine.",
"Estructura metálica para cubierta.": "Steelwork for a roof.",
"Columna metálica.": "Steel column.",
"Viga metálica.": "Steel beam.",
"Estructura metálica para escalera.": "Steelwork for a stair.",
"Estructura metálica para marquesina.": "Steelwork for a canopy.",
"Estructura metálica para techo ligero.": "Steelwork for a lightweight roof.",
"Conexión atornillada de estructura.": "Bolted connection of the structure.",
"Estructura metálica con protección anticorrosiva.":
    "Steelwork with anti-corrosion protection.",
"Estructura metálica para entrepiso ligero.":
    "Steelwork for a lightweight intermediate floor.",
"Viga de amarre metálica.": "Steel tie beam.",
"Refuerzo metálico de losa.": "Steel strengthening of a slab.",

# ── Estructura de madera ──────────────────────────────────────────────────
"Suministro y montaje de estructura de madera.":
    "Supply and erection of a wood structure.",
"Correas y viguetas de madera para cubierta o entrepiso.":
    "Wood purlins and joists for a roof or intermediate floor.",
"Tratamiento preservante de madera estructural.":
    "Preservative treatment of structural timber.",
"Herraje o conector metálico para unión de estructura de madera.":
    "Metal connector or hardware for wood structural joints.",
"Montaje de estructura de madera en obra.":
    "Erection of a wood structure on site.",
"Correas de madera para cubierta.": "Wood purlins for a roof.",
"Tratamiento preservante de madera.": "Preservative treatment of timber.",
"Herraje de unión de estructura de madera.":
    "Connector hardware for a wood structure.",
"Viga de madera estructural.": "Structural wood beam.",
"Columna de madera estructural.": "Structural wood column.",
"Entrepiso de madera estructural.": "Structural wood intermediate floor.",
"Cubierta de madera estructural.": "Structural wood roof.",
"Cercha de madera.": "Wood truss.",
"Correa de madera para techo.": "Wood purlin for a roof.",
"Entrepiso de madera con tablero OSB.":
    "Wood intermediate floor with OSB decking.",
"Viga de madera laminada.": "Glue-laminated wood beam.",
"Cubierta de madera con aislamiento.": "Insulated wood roof.",
"Correa de madera con tratamiento.": "Treated wood purlin.",
"Entrepiso de madera con viguetas.": "Wood intermediate floor on joists.",
"Cubierta de madera con teja.": "Tiled wood roof.",

# ── Losas ─────────────────────────────────────────────────────────────────
"Losa nervada con bloques de arcilla de aliviano.":
    "Ribbed slab with clay filler blocks.",
"Losa nervada con bloques de poliestireno de aliviano.":
    "Ribbed slab with polystyrene filler blocks.",
"Losa con viguetas prefabricadas pretensadas.":
    "Slab on precast prestressed joists.",
"Apuntalamiento de losa durante el vaciado y el fraguado.":
    "Shoring of a slab during the pour and curing.",
"Losa mixta con lámina colaborante sobre estructura metálica.":
    "Composite slab with metal decking on a steel frame.",
"Ampliación de losa en voladizo o balcón.":
    "Extension of a slab as a cantilever or balcony.",
"Losa nervada con bloque de arcilla.": "Ribbed slab with clay filler blocks.",
"Losa nervada con bloque de poliestireno.":
    "Ribbed slab with polystyrene filler blocks.",
"Losa con viguetas pretensadas.": "Slab on prestressed joists.",
"Losa mixta con lámina colaborante.": "Composite slab with metal decking.",
"Losa maciza con malla electrosoldada.": "Solid slab with welded wire mesh.",
"Losa aligerada con anime.": "Lightweight slab with EPS void formers.",
"Losa de entrepiso con aislamiento.": "Insulated intermediate floor slab.",
"Losa de cubierta de concreto.": "Concrete roof slab.",
"Losa con juntas de dilatación.": "Slab with expansion joints.",
"Losa de concreto aligerada con bloques.": "Lightweight concrete slab with blocks.",
"Losa de techo con viguetas y bloques.": "Roof slab on joists and filler blocks.",
"Losa de concreto con acero de temperatura.":
    "Concrete slab with shrinkage and temperature reinforcement.",
"Losa de concreto aligerada con casetones.":
    "Lightweight concrete slab with waffle pods.",
"Losa de entrepiso con malla.": "Intermediate floor slab with mesh.",
"Losa de concreto con acabado pulido.": "Polished concrete slab.",
"Losa de concreto con pendiente.": "Sloped concrete slab.",

# ── Escaleras y rampas ────────────────────────────────────────────────────
"Escalera metálica estructural.": "Structural steel stair.",
"Escalera metálica de estructura.": "Structural steel stair.",
"Rampa de concreto estructural.": "Structural concrete ramp.",
"Escalera de concreto con acabado.": "Finished concrete stair.",
"Escalera metálica con peldaños de rejilla.": "Steel stair with grating treads.",
"Rampa metálica estructural.": "Structural steel ramp.",
"Escalera de concreto de dos tramos.": "Two-flight concrete stair.",
"Escalera metálica de caracol.": "Spiral steel stair.",
"Escalera de concreto con descansillo.": "Concrete stair with a landing.",
"Rampa de concreto con bordillo.": "Concrete ramp with a curb.",
"Escalera de concreto reforzada.": "Reinforced concrete stair.",
"Escalera metálica con baranda.": "Steel stair with a guardrail.",
"Rampa de concreto con acabado antideslizante.":
    "Concrete ramp with an anti-slip finish.",
"Escalera de concreto a prueba de fuego.": "Fire-rated concrete stair.",
"Escalera metálica de emergencia.": "Steel fire escape stair.",

# ── Conexiones y anclajes ─────────────────────────────────────────────────
"Anclaje químico de barra en concreto.": "Chemical anchoring of a bar in concrete.",
"Perno de anclaje en concreto.": "Anchor bolt in concrete.",
"Conector de cortante en losa mixta.": "Shear connector in a composite slab.",
"Conexión atornillada con apriete.": "Bolted connection with controlled tightening.",
"Soldadura estructural en obra.": "Structural welding on site.",
"Anclaje mecánico de expansión.": "Mechanical expansion anchor.",
"Anclaje de barra con resina epóxica.": "Anchoring of a bar with epoxy resin.",
"Conexión soldada de placa base.": "Welded connection of a base plate.",
"Junta de dilatación estructural.": "Structural expansion joint.",
"Junta de construcción.": "Construction joint.",
"Junta sísmica estructural.": "Structural seismic joint.",
"Anclaje químico de barra de acero en concreto.":
    "Chemical anchoring of a steel bar in concrete.",

# ── Reparación y refuerzo ─────────────────────────────────────────────────
"Reparación superficial de concreto con mortero estructural.":
    "Surface repair of concrete with structural mortar.",
"Tratamiento pasivante de acero de refuerzo corroído.":
    "Passivating treatment of corroded reinforcement.",
"Inyección de fisuras en concreto con resina epóxica.":
    "Injection of cracks in concrete with epoxy resin.",
"Refuerzo estructural con tejido de fibra de carbono.":
    "Structural strengthening with carbon fiber fabric.",
"Encamisado de columna de concreto armado.":
    "Jacketing of a reinforced concrete column.",
"Refuerzo de losa o viga con perfil metálico.":
    "Strengthening of a slab or beam with a steel section.",
"Reparación de concreto con mortero.": "Repair of concrete with mortar.",
"Tratamiento pasivante de acero corroído.":
    "Passivating treatment of corroded steel.",
"Inyección de fisuras con resina.": "Injection of cracks with resin.",
"Refuerzo con fibra de carbono.": "Strengthening with carbon fiber.",
"Encamisado de columna.": "Column jacketing.",
"Refuerzo de losa con perfil metálico.":
    "Strengthening of a slab with a steel section.",
"Refuerzo de viga con fibra.": "Strengthening of a beam with fiber.",
"Reparación de losa con mortero.": "Repair of a slab with mortar.",
"Refuerzo de muro con encamisado.": "Strengthening of a wall by jacketing.",
"Refuerzo con mortero de alta resistencia.":
    "Strengthening with high-strength mortar.",
"Reparación de columna con mortero.": "Repair of a column with mortar.",
"Refuerzo de losa con fibra.": "Strengthening of a slab with fiber.",
"Refuerzo de estructura con perfil.": "Strengthening of a structure with a section.",
"Reparación de viga con mortero.": "Repair of a beam with mortar.",
"Refuerzo de columna con fibra.": "Strengthening of a column with fiber.",
"Reparación de muro con mortero.": "Repair of a wall with mortar.",
"Refuerzo integral de estructura.": "Overall strengthening of a structure.",
}
