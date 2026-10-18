# -*- coding: utf-8 -*-
"""Descripciones — Obras exteriores y urbanismo (capítulo completo, 160).

Criterios de este lote:
  · «Acera» es sidewalk en Estados Unidos y pavement en el Reino Unido, y
    el «bordillo» o «brocal» es curb y curb. Son de las pocas palabras del
    catálogo que el cliente lee todos los días.
  · «Adoquín» es paver en Estados Unidos y block paving en el Reino Unido.
    El «confinamiento perimetral» es edge restraint, y es lo que mantiene
    el pavimento trabado.
  · «Escobillado» es broom finish y «allanadora mecánica» es power trowel.
    El escobillado se da en el punto justo de fraguado: pronto se cierra
    la textura y tarde no marca.
  · «Tanquilla» es inspection chamber en el Reino Unido y manhole en
    Estados Unidos cuando es registrable.
  · «Malla ciclónica» es chain link, y los postes que reciben la tensión
    son los straining posts.
  · «Grama en panes» es sod en Estados Unidos y turf en el Reino Unido.
    Se rueda para que arraigue: rolling.
  · «Llave de jardín» es hose bibb y garden tap. «Sumidero» es catch basin
    y gully.
  · «Vaso» de piscina es pool shell, «rebosadero» es overflow channel y
    las «boquillas» son return and suction fittings.
"""

LOTE = {
# ── Pavimentos ────────────────────────────────────────────────────────────
"Piso de concreto exterior de 10 cm de espesor sobre base compactada, con malla de retracción, juntas de control y acabado escobillado antideslizante. El escobillado se ejecuta transversal al sentido de circulación y en el punto justo de fraguado, porque hecho demasiado pronto la textura se cierra y demasiado tarde no marca. Incluye la comprobación de la base, la colocación de la malla sobre separadores, el vaciado y vibrado, el reglado con la pendiente de evacuación, el escobillado, el aserrado de juntas y el curado. Medido en superficie realmente ejecutada.":
    "External concrete slab 10 cm thick on a compacted base, with shrinkage reinforcement, control joints and a non-slip broom finish. The brooming is carried out across the direction of travel and at just the right point of set, because done too soon the texture closes up and too late it leaves no mark. Includes checking the base, placing the mesh on chairs, pouring and vibrating, screeding to the drainage falls, brooming, saw cutting the joints and curing. Measured by the area actually constructed.",

"Pavimento exterior de adoquín de concreto sobre cama de arena y base compactada, con confinamiento perimetral y sellado de juntas con arena. El confinamiento perimetral es lo que mantiene el pavimento trabado: sin un bordillo o brocal que lo contenga, los adoquines del borde se desplazan y el paño entero pierde la trabazón. Incluye el extendido y reglado de la cama de arena, la colocación de los adoquines según el aparejo, el corte de las piezas de ajuste, la compactación con plancha y el barrido y vibrado de arena en las juntas. Medido en superficie realmente ejecutada.":
    "External paving of concrete pavers on a sand bed and compacted base, with edge restraint and the joints filled with sand. The edge restraint is what keeps the paving interlocked: without a curb to contain it the pavers at the edge move out and the whole area loses its interlock. Includes spreading and screeding the laying course, laying the pavers to the bond, cutting the closing units, compacting with a plate and brushing and vibrating sand into the joints. Measured by the area actually constructed.",

"Pavimento exterior de gravilla o piedra decorativa sobre geotextil y base compactada, con confinamiento perimetral. El geotextil separador es lo que impide que la gravilla se hunda en el terreno y que crezca vegetación a través de ella, que son las dos razones por las que este pavimento se degrada. Incluye la nivelación y compactación de la base, la colocación del geotextil con solapes, el extendido de la gravilla con el espesor uniforme de proyecto y el rastrillado final. Medido en superficie realmente ejecutada.":
    "External gravel or decorative stone surface on a geotextile and compacted base, with edge restraint. The separating geotextile is what stops the gravel sinking into the ground and vegetation growing up through it, the two reasons this surface breaks down. Includes leveling and compacting the base, laying the geotextile with laps, spreading the gravel to the uniform thickness specified and the final raking. Measured by the area actually constructed.",

"Rampa de acceso vehicular de concreto armado con acabado antideslizante estriado y su drenaje de pie. Las estrías transversales no son decorativas: en pendiente y con lluvia son lo único que da tracción al vehículo y agarre al peatón. Incluye el replanteo de la pendiente comprobando que el vehículo no roce en los quiebres de entrada y salida, la preparación de la base, la malla, el encofrado lateral, el vaciado y reglado, el estriado transversal, el canal o rejilla de recogida al pie de la rampa que impide que el agua entre al garaje, el aserrado de juntas y el curado. Medido en superficie realmente ejecutada.":
    "Reinforced concrete driveway ramp with a non-slip grooved finish and a drainage channel at the foot. The transverse grooves are not decorative: on a slope and in rain they are the only thing that gives the vehicle grip and the pedestrian purchase. Includes setting out the gradient and checking that the vehicle will not ground at the breaks at the top and bottom, preparing the base, the mesh, the side formwork, pouring and screeding, the transverse grooving, the channel or grate at the foot of the ramp that keeps water out of the garage, saw cutting the joints and curing. Measured by the area actually constructed.",

"Escalera exterior de concreto armado con acabado antideslizante, sobre terreno o estructura, con su fundación corrida. Incluye el replanteo verificando que huella y contrahuella se mantienen constantes en todo el tramo, la fundación, el armado, el encofrado del fondo y de los tabicones de peldaño, el vaciado ascendente con concreto de consistencia seca, el fratasado antideslizante de las huellas, la pendiente de evacuación hacia el exterior en cada peldaño para que no empocen, el curado y el desencofrado. Medido en superficie desarrollando huella y contrahuella.":
    "External reinforced concrete stair with a non-slip finish, on ground or on a structure, with its strip footing. Includes setting out and checking that the going and the rise stay constant over the whole flight, the footing, the reinforcement, the soffit and riser formwork, pouring from the bottom up with a dry mix, floating the treads to a non-slip finish, the fall outwards on each tread so that they do not hold water, curing and striking. Measured by the developed area of treads and risers.",

"Pavimento exterior de concreto con acabado escobillado antideslizante, sobre base compactada, con juntas de retracción. Incluye el vaciado, el acabado y las juntas.":
    "External concrete paving with a non-slip broom finish, on a compacted base, with shrinkage joints. Includes pouring, finishing and the joints.",

"Pavimento exterior de adoquín de concreto sobre cama de arena y base compactada, con confinamiento perimetral. Incluye la colocación, el corte y la compactación.":
    "External paving of concrete pavers on a sand bed and compacted base, with edge restraint. Includes laying, cutting and compaction.",

"Pavimento exterior de gravilla o piedra suelta sobre base nivelada, con geotextil de separación. Incluye el extendido y la nivelación.":
    "External loose gravel or stone surface on a leveled base, with a separating geotextile. Includes spreading and leveling.",

"Ejecución de rampa de acceso vehicular de concreto armado con pendiente y acabado antideslizante. Incluye el encofrado, el armado y el vaciado.":
    "Construction of a reinforced concrete driveway ramp with a gradient and a non-slip finish. Includes formwork, reinforcement and pouring.",

"Ejecución de escalera exterior de concreto armado, con peldaños y descansos. Incluye el encofrado, el armado y el vaciado.":
    "Construction of an external reinforced concrete stair, with steps and landings. Includes formwork, reinforcement and pouring.",

"Pavimento exterior de concreto estampado con moldes y desmoldeante de color, sellado. Incluye el vaciado, el estampado y el sellado.":
    "External stamped concrete paving using mats and a colored release agent, sealed. Includes pouring, stamping and sealing.",

"Pavimento exterior de concreto alisado con allanadora mecánica, para tránsito peatonal y vehicular. Incluye el vaciado y el alisado.":
    "External concrete paving power troweled to a smooth finish, for pedestrian and vehicular traffic. Includes pouring and troweling.",

"Pavimento exterior de lajas de piedra sobre cama de mortero, con juntas rellenadas. Incluye la colocación y el juntado. La piedra la elige el cliente.":
    "External stone flag paving on a mortar bed, with the joints filled. Includes laying and pointing. The stone is selected by the client.",

"Pavimento exterior de baldosa cerámica antideslizante sobre mortero de agarre, con juntas selladas. Incluye la colocación y el juntado. La baldosa la elige el cliente.":
    "External non-slip ceramic tile paving on a bedding mortar, with the joints sealed. Includes laying and grouting. The tile is selected by the client.",

"Ejecución de base de material granular compactado para pavimento exterior, con nivelación y compactación. Incluye el extendido y la compactación.":
    "Construction of a compacted granular base for external paving, leveled and compacted. Includes spreading and compaction.",

"Ejecución de junta de retracción en pavimento de concreto con disco de corte y sellado. Incluye el corte y el sellado.":
    "Formation of a shrinkage joint in concrete paving with a cutting disc and sealant. Includes cutting and sealing.",

# ── Brocales y aceras ─────────────────────────────────────────────────────
"Ejecución de brocal o bordillo de concreto, prefabricado o vaciado en sitio, sobre su dado de apoyo, con juntas selladas. Incluye el replanteo de la línea y de la rasante con cuerda, la excavación y vaciado del dado de apoyo, la colocación de las piezas a nivel y alineación, el macizado lateral que impide su vuelco bajo el empuje del pavimento, el rejuntado y el curado. Medido en longitud realmente ejecutada.":
    "Construction of a concrete curb, precast or cast in place, on its bed, with the joints sealed. Includes setting out the line and level with a string line, excavating and pouring the curb bed, laying the units level and to line, the haunching that stops them overturning under the thrust of the paving, pointing and curing. Measured by the length actually constructed.",

"Acera de concreto de 8 cm sobre base compactada, con juntas de control y acabado antideslizante, con la pendiente transversal de evacuación. Incluye el replanteo de rasantes y pendientes, el encofrado perimetral, la colocación de la malla, el vaciado y reglado, el acabado, el aserrado o formación de juntas de control a la separación indicada y el curado. Medido en superficie realmente ejecutada.":
    "Concrete sidewalk 8 cm thick on a compacted base, with control joints and a non-slip finish, with the cross fall for drainage. Includes setting out levels and falls, the perimeter formwork, placing the mesh, pouring and screeding, the finish, saw cutting or forming the control joints at the spacing indicated and curing. Measured by the area actually constructed.",

"Ejecución de brocal o bordillo de concreto para confinamiento de pavimento, con encofrado y curado. Incluye el vaciado y el acabado.":
    "Construction of a concrete curb to restrain paving, with formwork and curing. Includes pouring and finishing.",

"Ejecución de acera de concreto con acabado escobillado y juntas de retracción. Incluye la base, el vaciado y las juntas.":
    "Construction of a concrete sidewalk with a broom finish and shrinkage joints. Includes the base, pouring and the joints.",

"Ejecución de acera de adoquín sobre cama de arena, con confinamiento perimetral. Incluye la colocación y la compactación.":
    "Construction of a paver sidewalk on a sand bed, with edge restraint. Includes laying and compaction.",

"Ejecución de rampa peatonal exterior de concreto con pendiente de accesibilidad y acabado antideslizante. Incluye el encofrado y el vaciado.":
    "Construction of an external concrete pedestrian ramp with an accessible gradient and a non-slip finish. Includes formwork and pouring.",

"Ejecución de escalera exterior de concreto con previsión de pasamanos. Incluye el encofrado, el armado y el vaciado.":
    "Construction of an external concrete stair with provision for a handrail. Includes formwork, reinforcement and pouring.",

"Colocación de bordillo prefabricado de concreto sobre base de mortero. Incluye la colocación y el rejuntado.":
    "Installation of a precast concrete curb on a mortar bed. Includes laying and pointing.",

"Ejecución de cuneta de concreto para conducción de aguas superficiales, con encofrado y acabado. Incluye el vaciado y el acabado.":
    "Construction of a concrete channel to carry surface water, with formwork and finish. Includes pouring and finishing.",

"Colocación de pasamanos exterior de acero, con fijación y pintura. Incluye la fijación y el acabado.":
    "Installation of an external steel handrail, fixed and painted. Includes fixing and finishing.",

"Colocación de peldaño prefabricado de concreto para escalera exterior. Incluye la colocación y el rejuntado.":
    "Installation of a precast concrete step for an external stair. Includes laying and pointing.",

"Ejecución de acera de piedra o loseta sobre cama de mortero, con juntas rellenadas. Incluye la colocación y el juntado. La piedra la elige el cliente.":
    "Construction of a stone or flag sidewalk on a mortar bed, with the joints filled. Includes laying and pointing. The stone is selected by the client.",

"Ejecución de rampa de acceso con baranda de protección, en concreto y acero. Incluye el vaciado y la baranda.":
    "Construction of an access ramp with a guardrail, in concrete and steel. Includes pouring and the guardrail.",

"Reparación de acera o brocal con resane de concreto y sustitución de tramos dañados. Incluye la demolición parcial y el resane.":
    "Repair of a sidewalk or curb with concrete patching and replacement of damaged sections. Includes partial demolition and patching.",

# ── Drenaje exterior ──────────────────────────────────────────────────────
"Suministro e instalación de canal de drenaje lineal prefabricado con su rejilla, sobre dado de concreto, con conexión a la red de drenaje. Incluye el replanteo de la línea y de la pendiente hacia el punto de descarga, la excavación, el vaciado del dado de apoyo, la colocación del canal a la cota exacta que debe quedar un par de milímetros por debajo del pavimento terminado para que el agua entre y no lo salte, el macizado lateral, la conexión de salida y la colocación de la rejilla. Medido en longitud realmente instalada.":
    "Supply and installation of a precast linear drainage channel with its grate, on a concrete bed, connected to the drainage system. Includes setting out the line and the fall to the discharge point, excavation, pouring the bed, setting the channel to the exact level, which must sit a couple of millimetres below the finished paving so that water enters it rather than riding over it, the haunching, the outlet connection and fitting the grate. Measured by the length actually installed.",

"Construcción de tanquilla o registro de drenaje en mampostería o concreto, con su solera, paredes frisadas, tapa y conexiones. Incluye la excavación, el vaciado de la solera con la media caña de conducción que guía el flujo y evita la sedimentación, el levantamiento de las paredes, el friso interior impermeabilizado, la conexión de las tuberías de entrada y salida con sus cotas y pendientes, la colocación del marco y la tapa a la rasante del pavimento y la prueba de escurrimiento. Medido por unidad ejecutada.":
    "Construction of a drainage inspection chamber in masonry or concrete, with its base slab, stuccoed walls, cover and connections. Includes excavation, pouring the base slab with the benching that guides the flow and prevents siltation, building the walls, the waterproofed internal stucco, connecting the inlet and outlet pipes at their levels and gradients, setting the frame and cover flush with the paving and the flow test. Measured per unit constructed.",

"Colocación de canal de drenaje lineal prefabricado con rejilla, sobre base de mortero. Incluye la colocación y la nivelación.":
    "Installation of a precast linear drainage channel with a grate, on a mortar bed. Includes laying and leveling.",

"Ejecución de tanquilla o registro de drenaje, con base y tapa. Incluye la excavación y la colocación.":
    "Construction of a drainage inspection chamber, with a base and a cover. Includes excavation and installation.",

"Colocación de tubería de drenaje perforada corrugada envuelta en geotextil, sobre cama de gravilla. Incluye la colocación y el relleno.":
    "Installation of perforated corrugated drainage pipe wrapped in geotextile, on a gravel bed. Includes laying and backfilling.",

"Ejecución de pozo de drenaje o sumidero exterior con rejilla, sobre base de concreto. Incluye la excavación y la colocación.":
    "Construction of an external catch basin or drainage pit with a grate, on a concrete base. Includes excavation and installation.",

"Ejecución de canaleta de desagüe de concreto para evacuación de aguas superficiales. Incluye el encofrado y el vaciado.":
    "Construction of a concrete drainage channel to carry off surface water. Includes formwork and pouring.",

"Ejecución de drenaje francés con zanja rellena de gravilla y tubería perforada, envuelta en geotextil. Incluye la excavación y el relleno.":
    "Construction of a French drain, a trench filled with gravel and perforated pipe wrapped in geotextile. Includes excavation and backfilling.",

"Ejecución de sumidero de patio o estacionamiento con rejilla y conexión a drenaje. Incluye la colocación y la conexión.":
    "Construction of a yard or parking catch basin with a grate and connection to the drainage. Includes installation and connection.",

"Limpieza de canal de drenaje exterior con retirada de sedimentos y comprobación del flujo. Incluye la limpieza.":
    "Cleaning of an external drainage channel with removal of silt and checking the flow. Includes cleaning.",

"Reparación de canal de drenaje con sustitución de tramos de rejilla o canal dañados. Incluye la sustitución.":
    "Repair of a drainage channel by replacing damaged sections of grate or channel. Includes replacement.",

"Ejecución de registro de inspección de drenaje con tapa y marco. Incluye la excavación y la colocación.":
    "Construction of a drainage inspection chamber with a cover and frame. Includes excavation and installation.",

"Conexión de drenaje exterior a la red existente, con excavación, empalme y relleno. Incluye la conexión y el relleno.":
    "Connection of external drainage to the existing system, with excavation, the junction and backfilling. Includes connection and backfilling.",

"Colocación de tubería de drenaje de aguas lluvias exterior en PVC, con pendiente y accesorios. Incluye la colocación y el relleno.":
    "Installation of external PVC rainwater drainage pipe, with falls and fittings. Includes laying and backfilling.",

# ── Cerramientos ──────────────────────────────────────────────────────────
"Cerca perimetral de bloque de concreto con sus machones de confinamiento y viga de corona, frisada por ambas caras. Incluye el replanteo de la línea de lindero, la ejecución de la fundación corrida, el levantamiento de la mampostería a nivel y plomo, los machones de confinamiento a la separación de proyecto, la viga de corona, el friso por ambas caras y el remate superior con pendiente que evacúa el agua y protege la coronación. Medido en superficie realmente ejecutada.":
    "Perimeter wall of concrete blocks with its confining piers and ring beam, stuccoed on both faces. Includes setting out the boundary line, constructing the strip footing, building the masonry level and plumb, the confining piers at the spacing specified, the ring beam, the stucco on both faces and the coping with a fall that sheds water and protects the top of the wall. Measured by the area actually constructed.",

"Cerca perimetral de malla ciclónica con sus postes, tensores, alambre de púas de coronación y dados de concreto. Incluye el replanteo de la línea, la excavación y vaciado de los dados de los postes, el aplomado y arriostramiento de los postes de esquina y de tiro que son los que reciben toda la tensión de la malla, el tendido y tensado de la malla con su alambre de amarre, la colocación de los tensores y el remate de coronación. Medido en longitud realmente ejecutada.":
    "Perimeter chain link fence with its posts, straining wires, barbed wire topping and concrete footings. Includes setting out the line, excavating and pouring the post footings, plumbing and bracing the corner and straining posts, which take all the tension of the mesh, running out and tensioning the mesh with its tie wire, fitting the straining wires and the topping. Measured by the length actually constructed.",

"Ejecución de cerca perimetral de bloque de concreto, con columnas de refuerzo y friso. Incluye la mampostería y el friso.":
    "Construction of a perimeter wall of concrete blocks, with strengthening columns and stucco. Includes masonry and stucco.",

"Ejecución de cerca de malla ciclónica sobre postes metálicos, con tensores y alambre de amarre. Incluye la colocación de postes y malla.":
    "Construction of a chain link fence on metal posts, with straining wires and tie wire. Includes installing the posts and the mesh.",

"Ejecución de cerca de tubos metálicos horizontales sobre postes, con pintura anticorrosiva. Incluye el montaje y la pintura.":
    "Construction of a fence of horizontal metal tubes on posts, with anti-corrosion paint. Includes assembly and painting.",

"Ejecución de muro de cerramiento de parcela de bloque de concreto con vigas de amarre. Incluye la mampostería y las vigas.":
    "Construction of a boundary wall to the plot in concrete blocks with tie beams. Includes masonry and the beams.",

"Fabricación e instalación de verja metálica de cerramiento, con barrotes y marco, pintada. Incluye el montaje y la pintura.":
    "Manufacture and installation of a metal railing for the boundary, with bars and a frame, painted. Includes assembly and painting.",

"Ejecución de muro de contención de parcela de concreto armado, con encofrado y drenaje. Incluye el armado, el encofrado y el vaciado.":
    "Construction of a reinforced concrete retaining wall to the plot, with formwork and drainage. Includes reinforcement, formwork and pouring.",

"Ejecución de cerca de reja metálica sobre murete de bloque, con columnas. Incluye el murete y la reja.":
    "Construction of a metal grille fence on a block dwarf wall, with columns. Includes the dwarf wall and the grille.",

"Fabricación e instalación de portillo peatonal de cerramiento metálico, con marco y cerradura. Incluye el montaje y la cerradura.":
    "Manufacture and installation of a metal pedestrian gate in the boundary, with a frame and a lock. Includes assembly and the lock.",

"Reparación de cerca perimetral con sustitución de tramos de malla o postes dañados. Incluye la sustitución.":
    "Repair of a perimeter fence by replacing damaged sections of mesh or posts. Includes replacement.",

"Aplicación de pintura anticorrosiva sobre cerramiento metálico, con limpieza previa. Incluye la preparación y la aplicación.":
    "Application of anti-corrosion paint to a metal boundary, with cleaning beforehand. Includes preparation and application.",

"Ejecución de muro de cerramiento de bloque con acabado de friso exterior. Incluye la mampostería y el friso.":
    "Construction of a block boundary wall with an external stucco finish. Includes masonry and stucco.",

"Ejecución de columna de concreto armado para cerramiento, con encofrado y curado. Incluye el armado y el vaciado.":
    "Construction of a reinforced concrete column for the boundary, with formwork and curing. Includes reinforcement and pouring.",

"Ejecución de base o viga de fundación de muro de cerramiento, con armadura y vaciado. Incluye el armado y el vaciado.":
    "Construction of a footing or foundation beam for a boundary wall, with reinforcement and pouring. Includes reinforcement and pouring.",

"Siembra de cerca viva o seto perimetral con plantas, sobre terreno preparado. Incluye la preparación y la siembra. Las plantas las elige el cliente.":
    "Planting of a perimeter hedge with plants, on prepared ground. Includes preparation and planting. The plants are selected by the client.",

# ── Portones ──────────────────────────────────────────────────────────────
"Fabricación e instalación de portón de acceso vehicular, abatible o corredizo, con su bastidor, forro, herrajes y anclajes. Incluye la fabricación del bastidor reforzado dimensionado para el vano, el tratamiento anticorrosivo, la ejecución o comprobación de los machones o del riel según el tipo de apertura, el montaje y nivelación, el ajuste del recorrido y de los topes, la colocación de la cerradura o pasador y la previsión de la canalización eléctrica si va a motorizarse. Medido en superficie realmente ejecutada.":
    "Manufacture and installation of a vehicular access gate, hinged or sliding, with its frame, facing, hardware and anchors. Includes fabricating the reinforced frame sized for the opening, the anti-corrosion treatment, constructing or checking the piers or the track according to the type of opening, assembly and leveling, adjusting the travel and the stops, fitting the lock or latch and providing the electrical conduit if it is to be motorized. Measured by the area actually constructed.",

"Fabricación e instalación de portón de acceso vehicular metálico, con marco, bisagras y pintura. Incluye el montaje y la pintura. El portón lo elige el cliente.":
    "Manufacture and installation of a metal vehicular access gate, with a frame, hinges and paint. Includes assembly and painting. The gate is selected by the client.",

"Fabricación e instalación de portón corredizo de acceso, con riel y carros. Incluye el montaje y la pintura. El portón lo elige el cliente.":
    "Manufacture and installation of a sliding access gate, with a track and carriers. Includes assembly and painting. The gate is selected by the client.",

"Fabricación e instalación de portón peatonal metálico, con marco y cerradura. Incluye el montaje y la pintura. El portón lo elige el cliente.":
    "Manufacture and installation of a metal pedestrian gate, with a frame and a lock. Includes assembly and painting. The gate is selected by the client.",

"Instalación de motor y automatismo de portón existente, con programación y puesta en marcha. Incluye la instalación. El motor lo elige el cliente.":
    "Installation of a motor and automation to an existing gate, with programming and commissioning. Includes installation. The motor is selected by the client.",

"Instalación de portero eléctrico o videoportero de acceso, con cableado y conexión. Incluye la instalación. El equipo lo elige el cliente.":
    "Installation of a door entry system or video door entry system at the access, with cabling and connection. Includes installation. The unit is selected by the client.",

"Ejecución de base de concreto para poste o guía de portón, con anclajes. Incluye la excavación y el vaciado.":
    "Construction of a concrete base for a gate post or guide, with anchors. Includes excavation and pouring.",

"Ejecución de riel de portón corredizo empotrado en el pavimento, con base de concreto. Incluye la colocación y el nivelado.":
    "Installation of the track of a sliding gate recessed into the paving, on a concrete base. Includes laying and leveling.",

"Reparación de portón de acceso con ajuste de bisagras, sustitución de piezas y pintura. Incluye la revisión y el ajuste.":
    "Repair of an access gate with adjustment of the hinges, replacement of parts and painting. Includes inspection and adjustment.",

"Instalación de cerradura de seguridad en portón de acceso, con fijación y ajuste. Incluye la fijación y el ajuste.":
    "Installation of a security lock on an access gate, fixed and adjusted. Includes fixing and adjustment.",

"Colocación de baranda de acceso peatonal, con fijación y pintura. Incluye la fijación y el acabado.":
    "Installation of a guardrail at a pedestrian access, fixed and painted. Includes fixing and finishing.",

"Fabricación e instalación de portón de malla metálica para acceso, con marco y bisagras. Incluye el montaje. El portón lo elige el cliente.":
    "Manufacture and installation of a wire mesh access gate, with a frame and hinges. Includes assembly. The gate is selected by the client.",

"Colocación de buzón de correspondencia, con fijación o empotrado en el cerramiento. Incluye la fijación.":
    "Installation of a mailbox, fixed to or recessed into the boundary. Includes fixing.",

"Instalación de interruptor o pulsador de apertura de portón, con cableado. Incluye la instalación y la conexión.":
    "Installation of a switch or push button to open the gate, with cabling. Includes installation and connection.",

# ── Jardinería ────────────────────────────────────────────────────────────
"Preparación del terreno y siembra de grama en panes o alfombra, con aporte de tierra abonada, nivelación y primer riego. Incluye la limpieza y descompactación del terreno, el aporte y extendido de la tierra abonada, la nivelación con las pendientes de evacuación para que no queden zonas encharcadas, la colocación de los panes a junta trabada y bien apretados entre sí, el rodillado para asegurar el contacto con el suelo, que es lo que permite que arraigue, y el riego abundante inicial. Medido en superficie realmente ejecutada.":
    "Preparation of the ground and laying sod, with imported topsoil, leveling and the first watering. Includes clearing and loosening the ground, importing and spreading the topsoil, leveling to the drainage falls so that no areas hold water, laying the sods broken bonded and butted tight together, rolling to ensure contact with the soil, which is what lets it root, and the first heavy watering. Measured by the area actually completed.",

"Siembra de arbusto o árbol en hoyo preparado, con aporte de tierra abonada, tutorado y riego inicial. Incluye la apertura del hoyo con dimensiones muy superiores al cepellón, ya que un hoyo justo en terreno compacto actúa como maceta y la raíz no prospera fuera de él, la mejora del fondo, la colocación de la planta a la profundidad correcta sin enterrar el cuello, el relleno con tierra abonada, la formación del alcorque de riego, el tutorado en los árboles y el riego de asiento. La planta la elige el cliente y se presupuesta aparte. Medido por unidad sembrada.":
    "Planting of a shrub or tree in a prepared pit, with imported topsoil, staking and initial watering. Includes digging the pit far larger than the root ball, since a tight pit in compacted ground acts as a pot and the roots will not grow beyond it, improving the bottom, setting the plant at the right depth without burying the collar, backfilling with topsoil, forming the watering basin, staking in the case of trees and watering in. The plant is selected by the client and priced separately. Measured per unit planted.",

"Preparación del terreno y siembra de grama en panes o alfombra, con nivelación y riego inicial. Incluye la preparación y la siembra.":
    "Preparation of the ground and laying sod, with leveling and initial watering. Includes preparation and laying.",

"Siembra de arbusto o árbol con hoyo de plantación, abono y riego. Incluye la excavación y la siembra. La planta la elige el cliente.":
    "Planting of a shrub or tree with a planting pit, topsoil and watering. Includes excavation and planting. The plant is selected by the client.",

"Nivelación y preparación de terreno para jardín, con desbroce, relleno y rastrillado. Incluye la limpieza y la nivelación.":
    "Leveling and preparation of the ground for a garden, with clearing, filling and raking. Includes clearing and leveling.",

"Aplicación de abono y fertilizante sobre área verde, con incorporación al suelo. Incluye la aplicación.":
    "Application of soil conditioner and fertilizer to a planted area, worked into the soil. Includes application.",

"Siembra de plantas ornamentales en área verde, con preparación del suelo y riego. Incluye la siembra. Las plantas las elige el cliente.":
    "Planting of ornamental plants in a planted area, with preparation of the soil and watering. Includes planting. The plants are selected by the client.",

"Ejecución de borde de jardín con brocal o bordillo de concreto. Incluye la colocación y el rejuntado.":
    "Formation of a garden edge with a concrete curb. Includes laying and pointing.",

"Poda y mantenimiento de áreas verdes con retirada de restos vegetales. Incluye la poda y la limpieza.":
    "Pruning and maintenance of planted areas with removal of green waste. Includes pruning and clearing.",

"Riego de implantación de área verde tras la siembra, para asentamiento de la vegetación. Incluye el riego.":
    "Establishment watering of a planted area after planting, to settle the vegetation. Includes watering.",

"Aplicación de tratamiento fitosanitario contra plagas y hongos en área verde. Incluye la aplicación.":
    "Application of pest and disease treatment to a planted area. Includes application.",

"Ejecución de cama de siembra con sustrato abonado, para parterres y áreas de plantación. Incluye el extendido y el rastrillado.":
    "Formation of a planting bed with enriched growing medium, for beds and planted areas. Includes spreading and raking.",

"Siembra de grama en talud o pendiente con fijación, para evitar erosión. Incluye la preparación y la siembra.":
    "Turfing of a slope or bank with anchorage, to prevent erosion. Includes preparation and laying.",

"Reposición de grama dañada con sustitución de panes y riego. Incluye la sustitución y el riego.":
    "Replacement of damaged turf by lifting the sods and relaying, and watering. Includes replacement and watering.",

"Colocación de mulch o acolchado orgánico sobre parterre, para retención de humedad. Incluye el extendido.":
    "Application of mulch over a planting bed, to retain moisture. Includes spreading.",

# ── Riego ─────────────────────────────────────────────────────────────────
"Instalación de red de riego con tubería de polietileno, sus goteros o aspersores, y conexión al punto de agua. Incluye el replanteo del trazado y de la posición de los emisores según el marco de riego de la plantación, la apertura de la zanja poco profunda, el tendido de la tubería, el montaje de los emisores, la purga de la línea antes de colocar los últimos emisores para arrastrar la suciedad que de otro modo los obstruye, la prueba de presión y caudal y el tapado de la zanja. Medido en longitud de red realmente instalada.":
    "Installation of an irrigation system with polyethylene pipe, its drippers or sprinklers, and connection to the water point. Includes setting out the run and the position of the emitters according to the planting layout, opening a shallow trench, laying the pipe, fitting the emitters, flushing the line before fitting the last emitters to carry out the dirt that would otherwise block them, the pressure and flow test and backfilling the trench. Measured by the length of system actually installed.",

"Ejecución de red de riego por goteo o aspersión, con tubería de polietileno y emisores. Incluye la colocación y la conexión.":
    "Installation of a drip or sprinkler irrigation system, with polyethylene pipe and emitters. Includes laying and connection.",

"Ejecución de línea de goteo para parterre, con tubería y goteros. Incluye la colocación y la conexión.":
    "Installation of a drip line for a planting bed, with pipe and drippers. Includes laying and connection.",

"Instalación de aspersor emergente de riego, con conexión a la red. Incluye la colocación y la conexión.":
    "Installation of a pop-up irrigation sprinkler, connected to the system. Includes installation and connection.",

"Instalación de válvula de zona de riego, con conexión a la red. Incluye la colocación y la conexión.":
    "Installation of an irrigation zone valve, connected to the system. Includes installation and connection.",

"Instalación de programador de riego, con conexión eléctrica y programación. Incluye la instalación. El equipo lo elige el cliente.":
    "Installation of an irrigation controller, with the electrical connection and programming. Includes installation. The unit is selected by the client.",

"Ejecución de acometida de riego con llave de corte y conexión a la red. Incluye la conexión y la llave.":
    "Installation of an irrigation service connection with a shut-off valve and connection to the main. Includes connection and the valve.",

"Reparación de red de riego con sustitución de tramos de tubería o emisores dañados. Incluye la sustitución.":
    "Repair of an irrigation system by replacing damaged sections of pipe or emitters. Includes replacement.",

"Conexión de red de riego por goteo a tanque de almacenamiento, con válvula y filtro. Incluye la conexión.":
    "Connection of a drip irrigation system to a storage tank, with a valve and filter. Includes connection.",

"Ejecución de línea de riego para jardín vertical, con goteo y soportes. Incluye la colocación y la conexión.":
    "Installation of an irrigation line for a vertical garden, with drip and supports. Includes laying and connection.",

"Ejecución de punto de riego con llave, manguera y aspersor. Incluye la colocación y la conexión.":
    "Installation of an irrigation point with a tap, hose and sprinkler. Includes installation and connection.",

"Ejecución de red de riego con tubería principal de polietileno y derivaciones. Incluye la colocación y las conexiones.":
    "Installation of an irrigation system with a polyethylene main and branches. Includes laying and the connections.",

"Ejecución de drenaje y purga de red de riego, con válvula de purga. Incluye la colocación y la conexión.":
    "Installation of drainage and flushing to the irrigation system, with a flush valve. Includes installation and connection.",

"Programación y puesta en marcha de sistema de riego, con ajuste de tiempos y revisión de emisores. Incluye la programación.":
    "Programming and commissioning of the irrigation system, with adjustment of the run times and checking of the emitters. Includes programming.",

# ── Servicios exteriores ──────────────────────────────────────────────────
"Punto de agua exterior con su derivación, llave de jardín y remate. Incluye la derivación desde la red con su llave de corte accesible, la canalización enterrada o empotrada, el montaje de la llave de jardín con su rosca para manguera, el anclaje del conjunto para que no gire al maniobrar, que es lo que termina rompiendo la conexión, y la prueba de estanqueidad. Medido por punto terminado y probado.":
    "External water point with its branch, hose bibb and trim. Includes the branch off the main with an accessible shut-off valve, the buried or concealed pipe run, fitting the hose bibb with its hose thread, anchoring the assembly so that it cannot turn when used, which is what eventually breaks the connection, and the tightness test. Measured per point completed and tested.",

"Ejecución de punto de agua exterior con llave de jardín y conexión a la red. Incluye la conexión y la llave.":
    "Installation of an external water point with a hose bibb and connection to the main. Includes connection and the tap.",

"Ejecución de acometida de agua exterior desde la red a la edificación, con tubería y llave de corte. Incluye la conexión.":
    "Installation of an external water service from the main to the building, with pipework and a shut-off valve. Includes connection.",

"Ejecución de punto de desagüe exterior, con conexión a la red de drenaje. Incluye la conexión.":
    "Installation of an external drain point, connected to the drainage system. Includes connection.",

"Ejecución de conexión de gas exterior, con tubería y regulador. Incluye la conexión y la prueba de estanqueidad.":
    "Installation of an external gas connection, with pipework and a regulator. Includes connection and the tightness test.",

"Ejecución de acometida eléctrica exterior con cableado y canalización. Incluye la canalización y el cableado.":
    "Installation of an external electrical service with cabling and conduit. Includes the conduit and the cabling.",

"Ejecución de punto de electricidad exterior con tomacorriente o conexión. Incluye la conexión.":
    "Installation of an external electrical point with a receptacle or connection. Includes connection.",

"Conexión de bomba exterior con tubería, válvula y electricidad. Incluye la conexión hidráulica y eléctrica. La bomba la elige el cliente.":
    "Connection of an external pump with pipework, a valve and the electrical supply. Includes the hydraulic and electrical connections. The pump is selected by the client.",

"Tendido de tubería exterior enterrada para agua o gas, con excavación, colocación y relleno. Incluye la colocación.":
    "Laying of external buried pipe for water or gas, with excavation, laying and backfilling. Includes laying.",

"Ejecución de acometida de aguas servidas exterior, con tubería de PVC y pendiente. Incluye la colocación.":
    "Installation of an external foul water service connection, with PVC pipe and falls. Includes laying.",

"Ejecución de caja de registro de servicios exterior, con base y tapa. Incluye la colocación.":
    "Installation of an external service inspection chamber, with a base and a cover. Includes installation.",

"Ejecución de punto de agua para lavado de vehículo, con llave y manguera. Incluye la conexión.":
    "Installation of a water point for washing vehicles, with a tap and hose. Includes connection.",

"Reparación de red exterior de servicios con sustitución de tramos de tubería dañados. Incluye la sustitución.":
    "Repair of the external services network by replacing damaged sections of pipe. Includes replacement.",

"Ejecución de punto de drenaje de condensados exterior, con tubería y sifón. Incluye la colocación y la conexión.":
    "Installation of an external condensate drain point, with pipework and a trap. Includes installation and connection.",

# ── Iluminación exterior ──────────────────────────────────────────────────
"Punto de iluminación exterior de jardín o acceso, con su canalización enterrada, cableado, caja estanca y base de anclaje de la luminaria. Incluye el replanteo, la apertura de la zanja, la canalización enterrada con cinta de señalización sobre ella, el tendido del conductor apto para intemperie, la ejecución de la base de anclaje, la conexión estanca y la prueba. La luminaria la elige el cliente y se presupuesta aparte. Medido por punto terminado y probado.":
    "External lighting point for a garden or access, with its buried conduit, cabling, weatherproof box and base to anchor the fixture. Includes setting out, opening the trench, the buried conduit with warning tape over it, drawing in a cable rated for external use, constructing the anchorage base, the weatherproof connection and testing. The fixture is selected by the client and priced separately. Measured per point completed and tested.",

"Ejecución de punto de iluminación exterior de jardín, con luminaria, cableado y fijación. Incluye la conexión. La luminaria la elige el cliente.":
    "Installation of an external garden lighting point, with the fixture, cabling and fixing. Includes connection. The fixture is selected by the client.",

"Instalación de poste de iluminación exterior, con base de concreto y conexión. Incluye la cimentación y la conexión. El poste lo elige el cliente.":
    "Installation of an external lighting column, with a concrete base and connection. Includes the footing and the connection. The column is selected by the client.",

"Instalación de reflector exterior de seguridad, con fijación y conexión. Incluye la conexión. El reflector lo elige el cliente.":
    "Installation of an external security floodlight, fixed and connected. Includes connection. The floodlight is selected by the client.",

"Ejecución de iluminación de caminería exterior con balizas o faroles, con cableado. Incluye la conexión. Las luminarias las elige el cliente.":
    "Installation of external path lighting with bollards or lanterns, with cabling. Includes connection. The fixtures are selected by the client.",

"Colocación de tira LED exterior decorativa, con fuente de alimentación y perfil. Incluye la conexión. La tira la elige el cliente.":
    "Installation of a decorative external LED strip, with the driver and profile. Includes connection. The strip is selected by the client.",

"Instalación de fotocélula o sensor crepuscular exterior, con conexión. Incluye la instalación. El sensor lo elige el cliente.":
    "Installation of an external photocell or dusk sensor, connected. Includes installation. The sensor is selected by the client.",

"Instalación de iluminación de fachada con reflectores, con fijación y conexión. Incluye la conexión. Los reflectores los elige el cliente.":
    "Installation of facade lighting with floodlights, fixed and connected. Includes connection. The floodlights are selected by the client.",

"Ejecución de circuito de iluminación exterior, con cableado y canalización. Incluye el cableado.":
    "Installation of an external lighting circuit, with cabling and conduit. Includes cabling.",

"Instalación de aplique de pared exterior, con fijación y conexión. Incluye la conexión. El aplique lo elige el cliente.":
    "Installation of an external wall light, fixed and connected. Includes connection. The fitting is selected by the client.",

"Instalación de iluminación de estacionamiento exterior, con luminaria y conexión. Incluye la conexión. La luminaria la elige el cliente.":
    "Installation of external parking area lighting, with the fixture and connection. Includes connection. The fixture is selected by the client.",

"Reparación de iluminación exterior con sustitución de luminaria o cableado dañado. Incluye la sustitución.":
    "Repair of external lighting by replacing a damaged fixture or cable. Includes replacement.",

"Instalación de temporizador de iluminación exterior, con conexión y programación. Incluye la instalación. El temporizador lo elige el cliente.":
    "Installation of a time switch for external lighting, connected and programmed. Includes installation. The time switch is selected by the client.",

"Instalación de baliza empotrada de piso exterior, con caja y conexión. Incluye la instalación. La baliza la elige el cliente.":
    "Installation of a recessed external marker light, with a box and connection. Includes installation. The fitting is selected by the client.",

# ── Piscina ───────────────────────────────────────────────────────────────
"Ejecución de piscina de concreto armado, con losa de fondo, muros y acabado. Incluye el encofrado, el armado y el vaciado. El revestimiento lo elige el cliente.":
    "Construction of a reinforced concrete swimming pool, with the floor slab, walls and finish. Includes formwork, reinforcement and pouring. The finish is selected by the client.",

"Impermeabilización de piscina con membrana líquida o cementosa, previa al revestimiento. Incluye la imprimación y la aplicación.":
    "Waterproofing of a swimming pool with a liquid or cementitious membrane, before the finish. Includes priming and application.",

"Ejecución de borde o coronación de piscina, con losa de remate y acabado. Incluye el vaciado y el acabado.":
    "Construction of the edge or coping of a swimming pool, with a finishing slab and the finish. Includes pouring and finishing.",

"Ejecución de escalera de piscina de concreto, integrada en el vaso. Incluye el encofrado, el armado y el vaciado.":
    "Construction of a concrete pool step, built into the pool shell. Includes formwork, reinforcement and pouring.",

"Instalación de escalera metálica de piscina, con fijación y anclaje. Incluye la fijación. La escalera la elige el cliente.":
    "Installation of a metal pool ladder, fixed and anchored. Includes fixing. The ladder is selected by the client.",

"Instalación de equipo de filtrado de piscina, con conexión hidráulica. Incluye la conexión. El equipo lo elige el cliente.":
    "Installation of pool filtration equipment, with the hydraulic connection. Includes connection. The equipment is selected by the client.",

"Ejecución de rebosadero de piscina, con canal de recogida y conexión a drenaje. Incluye la ejecución y la conexión.":
    "Construction of a pool overflow channel, with the collection channel and connection to the drainage. Includes construction and connection.",

"Instalación de boquillas de retorno y aspiración de piscina, con conexión hidráulica. Incluye la conexión.":
    "Installation of pool return and suction fittings, with the hydraulic connection. Includes connection.",

"Instalación de ducha exterior de piscina, con conexión de agua. Incluye la conexión. La ducha la elige el cliente.":
    "Installation of an external pool shower, with the water connection. Includes connection. The shower is selected by the client.",

"Instalación de iluminación subacuática de piscina, con cableado y conexión. Incluye la instalación. La luminaria la elige el cliente.":
    "Installation of underwater pool lighting, with cabling and connection. Includes installation. The fixture is selected by the client.",

"Limpieza y puesta en marcha de piscina, con llenado, ajuste químico y puesta en marcha del filtrado. Incluye el llenado y el ajuste.":
    "Cleaning and commissioning of a swimming pool, with filling, chemical balancing and starting up the filtration. Includes filling and balancing.",

"Reparación de vaso de piscina con resane de fisuras y reimpermeabilización puntual. Incluye la reparación.":
    "Repair of a pool shell by filling cracks and local rewaterproofing. Includes repair.",

"Ejecución de cerramiento perimetral de seguridad de piscina, con reja o malla. Incluye la colocación.":
    "Installation of a perimeter safety fence to a swimming pool, with a grille or mesh. Includes installation.",

"Ejecución de pérgola o sombra de área de piscina, con estructura de madera o metálica. Incluye la estructura y el montaje.":
    "Construction of a pergola or shade structure over the pool area, in lumber or steel. Includes the structure and assembly.",

# ── Pérgolas, jardineras y mobiliario ─────────────────────────────────────
"Fabricación y montaje de pérgola de madera tratada para exterior, con sus pilares, vigas, correas y anclajes a la base. En clima tropical el punto de fallo es siempre el encuentro del pilar con el piso: la madera en contacto directo con el concreto absorbe humedad por capilaridad y se pudre desde la base, de modo que debe apoyarse sobre herraje metálico que la separe del piso. Incluye la ejecución de los dados de anclaje, el montaje de los herrajes separadores, el corte y labra de las piezas, el montaje de la estructura con apeo provisional, la fijación con herrajes y el tratamiento preservante en todas las caras y testas. Medido en superficie realmente ejecutada.":
    "Manufacture and assembly of an external pergola in treated lumber, with its posts, beams, purlins and anchors to the base. In a tropical climate the point of failure is always where the post meets the floor: lumber in direct contact with concrete takes up moisture by capillary action and rots from the bottom up, so it must stand on a metal shoe that holds it clear of the floor. Includes forming the anchorage blocks, fitting the post shoes, cutting and shaping the members, erecting the structure with temporary supports, fixing with the hardware and applying preservative to every face and every end grain. Measured by the area actually constructed.",

"Construcción de jardinera de obra en exterior, con su fábrica, friso, impermeabilización interior, drenaje y capa filtrante. Una jardinera sin impermeabilizar y sin drenaje transmite humedad permanente al muro contiguo y encharca la tierra hasta pudrir la raíz, de modo que ambas capas son parte del elemento y no un extra. Incluye la fundación, el levantamiento de la fábrica, el friso exterior, la impermeabilización interior con refuerzo de encuentros, el pase y la tubería de drenaje, la capa de gravilla con geotextil y el remate superior. No incluye el sustrato ni la plantación. Medido en longitud de jardinera.":
    "Construction of a planter externally, with its masonry, stucco, internal waterproofing, drainage and filter layer. A planter without waterproofing and without drainage transmits permanent moisture to the adjoining wall and waterlogs the soil until the roots rot, so both layers are part of the element and not an extra. Includes the footing, building the masonry, the external stucco, the internal waterproofing with reinforcement at the junctions, the sleeve and the drainage pipe, the gravel layer with geotextile and the capping. The growing medium and the planting are not included. Measured by the length of planter.",

"Ejecución de pérgola de madera para exterior, con estructura de vigas y listones tratados. Incluye el armado y el montaje.":
    "Construction of an external lumber pergola, with a structure of beams and treated battens. Includes assembly and erection.",

"Ejecución de jardinera de obra en exterior, de bloque o concreto, con drenaje. Incluye la mampostería y el drenaje.":
    "Construction of an external planter in blockwork or concrete, with drainage. Includes masonry and drainage.",

"Ejecución de pérgola metálica para exterior, con estructura de perfiles y pintura. Incluye el armado y el montaje.":
    "Construction of an external metal pergola, with a structure of sections and paint. Includes assembly and erection.",

"Colocación de jardinera prefabricada exterior, con fijación y drenaje. Incluye la colocación. La jardinera la elige el cliente.":
    "Installation of a precast external planter, fixed and drained. Includes installation. The planter is selected by the client.",

"Ejecución de banco de obra exterior, de concreto o bloque revestido. Incluye la ejecución y el acabado.":
    "Construction of an external bench in concrete or faced blockwork. Includes construction and finishing.",

"Ejecución de mesa de obra exterior, de concreto o bloque revestido. Incluye la ejecución y el acabado.":
    "Construction of an external table in concrete or faced blockwork. Includes construction and finishing.",

"Ejecución de parrillera de obra exterior, de bloque o concreto revestido. Incluye la ejecución.":
    "Construction of an external barbecue in blockwork or faced concrete. Includes construction.",

"Instalación de toldo o sombra exterior fija, con estructura y tensado. Incluye la estructura y el tensado. El toldo lo elige el cliente.":
    "Installation of a fixed external awning or shade, with the structure and tensioning. Includes the structure and tensioning. The awning is selected by the client.",

"Colocación de celosía o romanilla de aluminio en terraza, con marco y fijación. Incluye la colocación.":
    "Installation of an aluminum louver screen on a terrace, with a frame and fixing. Includes installation.",

"Fabricación e instalación de mueble de exterior a medida en madera tratada. Incluye el despiece y el armado.":
    "Manufacture and installation of external furniture to measure in treated lumber. Includes cutting list and assembly.",

"Reparación de pérgola o estructura exterior con sustitución de piezas y tratamiento. Incluye la reparación.":
    "Repair of a pergola or external structure with replacement of members and treatment. Includes repair.",

"Colocación de jardinera de concreto prefabricado, con nivelación y drenaje. Incluye la colocación.":
    "Installation of a precast concrete planter, leveled and drained. Includes installation.",

"Ejecución de pérgola bioclimática exterior, con estructura y lamas orientables. Incluye el montaje. El sistema lo elige el cliente.":
    "Installation of an external louvered roof pergola, with the structure and adjustable louvres. Includes assembly. The system is selected by the client.",
}
