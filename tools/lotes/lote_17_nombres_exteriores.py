# -*- coding: utf-8 -*-
"""Nombres de partida — Obras exteriores y urbanismo (capítulo completo, 160).

Criterios de este lote:
  · «Acera» es sidewalk en Estados Unidos y pavement en Reino Unido, así
    que la base es sidewalk y la variante británica pone pavement. Donde
    el español dice «pavimento» se usa paving, que es la palabra neutra
    para la superficie y evita el choque.
  · «Sumidero» es catch basin en Estados Unidos y gully en Reino Unido.
  · «Grama en panes» es sod y turf, y «grama» a secas es lawn.
  · «Llave de jardín» es hose bibb en Estados Unidos y garden tap en
    Reino Unido.
  · «Vaso de piscina» es pool shell, «coronación» es coping y
    «rebosadero» es overflow channel. «Boquillas de retorno y aspiración»
    son return and suction fittings.
  · «Buzón» es mailbox en Estados Unidos y letter box en Reino Unido.
"""

LOTE = {
# ── Pavimentos ────────────────────────────────────────────────────────────
"Piso de concreto exterior con acabado escobillado.":
    "Exterior concrete floor with a broom finish.",
"Pavimento de adoquín de concreto.": "Concrete paver paving.",
"Pavimento de gravilla o piedra suelta.": "Gravel or loose stone paving.",
"Rampa de acceso vehicular de concreto.": "Concrete vehicular access ramp.",
"Escalera exterior de concreto.": "Exterior concrete stair.",
"Piso de concreto exterior alisado.": "Power-troweled exterior concrete floor.",
"Pavimento de adoquín con confinamiento.":
    "Paver paving restrained with an edge.",
"Pavimento de gravilla compactada.": "Compacted gravel paving.",
"Rampa vehicular de concreto armado.": "Reinforced concrete vehicular ramp.",
"Escalera exterior de concreto armado.": "Exterior reinforced concrete stair.",
"Pavimento de concreto estampado.": "Stamped concrete paving.",
"Pavimento de concreto alisado con allanadora.":
    "Power-troweled concrete paving.",
"Pavimento de lajas de piedra.": "Flagstone paving.",
"Pavimento de baldosa exterior antideslizante.":
    "Anti-slip exterior tile paving.",
"Base compactada para pavimento exterior.":
    "Compacted base for exterior paving.",
"Junta de retracción en pavimento de concreto.":
    "Contraction joint in concrete paving.",

# ── Aceras, bordillos y escaleras ─────────────────────────────────────────
"Brocal o bordillo de concreto.": "Concrete curb.",
"Acera de concreto.": "Concrete sidewalk.",
"Bordillo de concreto vaciado en sitio.": "Cast-in-place concrete curb.",
"Acera de concreto con juntas.": "Concrete sidewalk with joints.",
"Acera de adoquín.": "Paver sidewalk.",
"Rampa peatonal exterior.": "Exterior pedestrian ramp.",
"Escalera exterior de concreto con pasamanos.":
    "Exterior concrete stair with a handrail.",
"Bordillo prefabricado de concreto.": "Precast concrete curb.",
"Cuneta de concreto para drenaje.": "Concrete roadside gutter.",
"Pasamanos exterior de acero.": "Exterior steel handrail.",
"Peldaño de escalera exterior prefabricado.":
    "Precast exterior stair tread.",
"Acera de piedra o loseta.": "Stone or flag sidewalk.",
"Rampa de acceso con baranda.": "Access ramp with a guardrail.",
"Reparación de acera o brocal.": "Repair of a sidewalk or curb.",

# ── Drenaje exterior ──────────────────────────────────────────────────────
"Canal de drenaje lineal con rejilla.":
    "Linear drainage channel with a grille.",
"Tanquilla o registro de drenaje.":
    "Drainage manhole or inspection chamber.",
"Canal de drenaje con rejilla metálica.":
    "Drainage channel with a metal grille.",
"Registro de drenaje con tapa.": "Drainage inspection chamber with a cover.",
"Tubería de drenaje perforada con geotextil.":
    "Perforated drainage pipe wrapped in a geotextile.",
"Pozo de drenaje o sumidero exterior.":
    "Exterior drainage pit or catch basin.",
"Canaleta de desagüe de concreto.": "Concrete drainage channel.",
"Drenaje francés con gravilla.": "French drain with gravel.",
"Sumidero de patio o estacionamiento.":
    "Catch basin in a yard or parking lot.",
"Limpieza y mantenimiento de drenaje exterior.":
    "Cleaning and maintenance of exterior drainage.",
"Reparación de canal de drenaje.": "Repair of a drainage channel.",
"Registro de inspección de drenaje.": "Drainage inspection chamber.",
"Conexión de drenaje a red existente.":
    "Connection of drainage to an existing system.",
"Tubería de drenaje de aguas lluvias exterior.":
    "Exterior rainwater drainage pipe.",

# ── Cerramientos ──────────────────────────────────────────────────────────
"Cerca perimetral de bloque.": "Perimeter blockwork fence.",
"Cerca de malla ciclónica.": "Chain-link fence.",
"Cerca de bloque con columnas.": "Blockwork fence with piers.",
"Cerca de malla ciclónica sobre postes.": "Chain-link fence on posts.",
"Cerca de tubos metálicos.": "Metal tube fence.",
"Muro de cerramiento de parcela de bloque.": "Blockwork boundary wall.",
"Verja metálica de cerramiento.": "Metal railing fence.",
"Muro de contención de parcela.": "Retaining wall to a plot.",
"Cerca de reja sobre murete de bloque.":
    "Grille fence on a blockwork dwarf wall.",
"Portillo peatonal de cerramiento.": "Pedestrian gate in a boundary wall.",
"Reparación de cerca perimetral.": "Repair of a perimeter fence.",
"Pintura de cerramiento metálico.": "Painting of a metal fence.",
"Muro de cerramiento con acabado de friso.":
    "Boundary wall with a rendered finish.",
"Columna de cerramiento de concreto.": "Concrete boundary pier.",
"Base de muro de cerramiento.": "Base of a boundary wall.",
"Cerca viva o seto perimetral.": "Perimeter hedge.",

# ── Portones y accesos ────────────────────────────────────────────────────
"Portón de acceso vehicular.": "Vehicular access gate.",
"Portón vehicular corredizo.": "Sliding vehicular gate.",
"Portón corredizo de acceso.": "Sliding access gate.",
"Portón peatonal de acceso.": "Pedestrian access gate.",
"Motorización de portón existente.":
    "Motorization of an existing gate.",
"Portero eléctrico o videoportero de acceso.":
    "Door entry intercom or video intercom at an access.",
"Base de concreto para poste de portón.":
    "Concrete base for a gate post.",
"Riel de portón corredizo empotrado.":
    "Recessed track for a sliding gate.",
"Reparación de portón de acceso.": "Repair of an access gate.",
"Cerradura de portón de acceso.": "Lock for an access gate.",
"Baranda de acceso peatonal.": "Guardrail to a pedestrian access.",
"Portón de malla para acceso.": "Mesh access gate.",
"Buzón de correspondencia empotrado.": "Recessed mailbox.",
"Interruptor de apertura de portón.": "Gate release switch.",

# ── Jardinería ────────────────────────────────────────────────────────────
"Preparación de tierra y siembra de grama.":
    "Soil preparation and grass seeding.",
"Siembra de arbusto o árbol.": "Planting of a shrub or tree.",
"Siembra de grama en panes.": "Laying sod.",
"Plantación de árbol ornamental.": "Planting of an ornamental tree.",
"Nivelación y preparación de terreno para jardín.":
    "Leveling and preparation of the ground for a garden.",
"Abono y fertilización de área verde.":
    "Fertilizing of a planted area.",
"Siembra de plantas ornamentales.": "Planting of ornamental plants.",
"Borde de jardín con brocal.": "Garden edging with a curb.",
"Poda y mantenimiento de áreas verdes.":
    "Pruning and maintenance of planted areas.",
"Riego de implantación de área verde.":
    "Establishment watering of a planted area.",
"Tratamiento fitosanitario de área verde.":
    "Pest and disease treatment of a planted area.",
"Cama de siembra con sustrato.": "Seedbed with growing medium.",
"Siembra de grama en talud o pendiente.":
    "Grass seeding on a slope or embankment.",
"Reposición de grama dañada.": "Reinstatement of damaged grass.",
"Mulch o acolchado de parterre.": "Mulch on a planting bed.",

# ── Riego ─────────────────────────────────────────────────────────────────
"Red de riego por goteo o aspersión.":
    "Drip or sprinkler irrigation system.",
"Red de riego por aspersión.": "Sprinkler irrigation system.",
"Línea de goteo para parterre.": "Drip line for a planting bed.",
"Aspersor emergente de riego.": "Pop-up sprinkler.",
"Válvula de zona de riego.": "Irrigation zone valve.",
"Programador de riego.": "Irrigation controller.",
"Acometida de riego con llave de corte.":
    "Irrigation service connection with a shut-off valve.",
"Reparación de red de riego.": "Repair of an irrigation system.",
"Conexión de riego por goteo a tanque.":
    "Connection of drip irrigation to a tank.",
"Línea de riego para jardín vertical.":
    "Irrigation line for a vertical garden.",
"Punto de riego con manguera y aspersor.":
    "Hose and sprinkler point.",
"Red de riego con tubería principal.":
    "Irrigation system with a main pipe.",
"Drenaje y purga de red de riego.":
    "Draining and purging of an irrigation system.",
"Programación y puesta en marcha de riego.":
    "Programming and commissioning of an irrigation system.",

# ── Servicios exteriores ──────────────────────────────────────────────────
"Punto de agua exterior con llave de jardín.":
    "Exterior water point with a hose bibb.",
"Punto de agua exterior con manguera.": "Exterior water point with a hose.",
"Acometida de agua exterior.": "Exterior water service connection.",
"Punto de desagüe exterior.": "Exterior drain point.",
"Conexión de gas exterior.": "Exterior gas connection.",
"Acometida eléctrica exterior.": "Exterior electrical service connection.",
"Punto de electricidad exterior.": "Exterior power point.",
"Conexión de bomba exterior.": "Connection of an exterior pump.",
"Tendido de tubería exterior enterrada.":
    "Laying of buried exterior pipework.",
"Acometida de aguas servidas exterior.":
    "Exterior sanitary sewer connection.",
"Caja de registro de servicios exterior.":
    "Exterior services inspection chamber.",
"Punto de agua para lavado de vehículo.":
    "Water point for vehicle washing.",
"Reparación de red exterior de servicios.":
    "Repair of an exterior services network.",
"Punto de drenaje de condensados exterior.":
    "Exterior condensate drain point.",

# ── Iluminación exterior ──────────────────────────────────────────────────
"Punto de iluminación exterior de jardín.": "Garden lighting point.",
"Iluminación exterior de caminería.": "Exterior pathway lighting.",
"Poste de iluminación exterior.": "Exterior lighting pole.",
"Reflector exterior de seguridad.": "Exterior security floodlight.",
"Iluminación de caminería exterior.": "Exterior pathway lighting.",
"Tira LED exterior decorativa.": "Decorative exterior LED strip.",
"Fotocélula o sensor crepuscular exterior.":
    "Exterior photocell or dusk-to-dawn sensor.",
"Iluminación de fachada con reflectores.":
    "Facade lighting with floodlights.",
"Circuito de iluminación exterior.": "Exterior lighting circuit.",
"Aplique de pared exterior.": "Exterior wall light.",
"Iluminación de estacionamiento exterior.":
    "Exterior parking lot lighting.",
"Reparación de iluminación exterior.": "Repair of exterior lighting.",
"Temporizador de iluminación exterior.": "Exterior lighting timer.",
"Baliza empotrada de piso exterior.":
    "Recessed inground light for exterior floors.",

# ── Piscina ───────────────────────────────────────────────────────────────
"Piscina de concreto armado.": "Reinforced concrete swimming pool.",
"Impermeabilización de piscina.": "Waterproofing of a swimming pool.",
"Borde o coronación de piscina.": "Pool coping.",
"Escalera de piscina de concreto.": "Concrete pool stair.",
"Escalera metálica de piscina.": "Steel pool ladder.",
"Equipo de filtrado de piscina.": "Pool filtration equipment.",
"Rebosadero de piscina.": "Pool overflow channel.",
"Boquillas de retorno y aspiración de piscina.":
    "Pool return and suction fittings.",
"Ducha exterior de piscina.": "Exterior pool shower.",
"Iluminación subacuática de piscina.": "Underwater pool lighting.",
"Limpieza y puesta en marcha de piscina.":
    "Cleaning and commissioning of a swimming pool.",
"Reparación de vaso de piscina.": "Repair of a pool shell.",
"Cerramiento perimetral de piscina.": "Perimeter pool fence.",
"Pérgola o sombra de área de piscina.":
    "Pergola or shade structure over a pool area.",

# ── Mobiliario exterior ───────────────────────────────────────────────────
"Pérgola de madera para exterior.": "Exterior wood pergola.",
"Jardinera de obra en exterior.": "Exterior masonry planter.",
"Pérgola de madera tratada.": "Treated wood pergola.",
"Jardinera de bloque revestido.": "Clad blockwork planter.",
"Pérgola metálica para exterior.": "Exterior metal pergola.",
"Jardinera prefabricada exterior.": "Precast exterior planter.",
"Banco de obra exterior.": "Exterior masonry bench.",
"Mesa de obra exterior.": "Exterior masonry table.",
"Parrillera de obra exterior.": "Exterior masonry barbecue.",
"Toldo o sombra exterior fija.": "Fixed exterior awning or shade.",
"Cerramiento de terraza con celosía.": "Terrace screen with louvers.",
"Mueble de exterior a medida.": "Custom-built exterior furniture.",
"Reparación de pérgola o estructura exterior.":
    "Repair of a pergola or exterior structure.",
"Jardinera de concreto prefabricado.": "Precast concrete planter.",
"Pérgola bioclimática exterior.": "Exterior louvered roof pergola.",
}
