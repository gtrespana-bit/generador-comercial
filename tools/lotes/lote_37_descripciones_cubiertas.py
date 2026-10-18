# -*- coding: utf-8 -*-
"""Descripciones — Techos y cubiertas (capítulo completo, 130).

Criterios de este lote:
  · «Formación de pendientes» es screed to falls: la capa que decide si la
    cubierta evacúa o empoza, y «contrapendiente» es back fall, el error
    clásico junto a los petos.
  · «Maestras» son screed rails. «Reglado» es screeding y «fratasado» es
    floating. «Afinado» es the final troweling.
  · «Faldón» es roof slope, «limahoya» es valley, «cumbrera» es ridge y
    «limatesa» es hip. «Alero» es eave y el «goterón» es drip edge: sin
    él el agua rodea el canto por capilaridad y chorrea la fachada.
  · «Tragante» es roof drain en Estados Unidos y roof outlet en el Reino
    Unido. «Bajante» es downspout y downpipe. «Canalón» es gutter.
  · «Teja criolla» es barrel tile y su sistema es pan and cover. «Teja
    asfáltica» es asphalt shingle y exige tablero continuo, no listonado.
  · «Remonte» es upstand. «Cubierta invertida» es inverted roof.
  · «Piso técnico sobre pedestales» es paving on adjustable pedestals:
    nivela sobre una base en pendiente y deja la impermeabilización
    registrable levantando una loseta.
"""

LOTE = {
# ── Formación de pendientes y soporte ─────────────────────────────────────
"Formación de pendientes sobre base de cubierta con mortero de cemento aligerado con arcilla expandida o poliestireno, para dirigir el agua hacia los puntos de desagüe. Incluye el replanteo de maestras, el relleno hasta espesores crecientes y el fratasado final de la superficie.":
    "Screed to falls over the roof deck in cement mortar lightweightened with expanded clay or polystyrene, to direct water to the drainage points. Includes setting out screed rails, laying the fill to increasing thicknesses and the final floating of the surface.",

"Formación de pendientes con concreto ligero de baja resistencia sobre cubierta plana, para crear la caída hacia tragantes o canales. Incluye el encofrado perimetral, el extendido y reglado con maestras y el curado de la superficie.":
    "Formation of falls in low strength lightweight concrete on a flat roof, to create the drop towards the roof drains or channels. Includes the perimeter formwork, spreading and screeding to rails and curing the surface.",

"Regularización del soporte de una cubierta plana existente con mortero de nivelación, eliminando ondulaciones antes de impermeabilizar. Incluye la limpieza del soporte, el maestreado y el afinado final.":
    "Preparation of the substrate of an existing flat roof with a leveling screed, removing undulations before waterproofing. Includes cleaning the substrate, screeding to rails and the final troweling.",

"Base continua de mortero de cemento sobre el faldón para recibir cubierta de teja o lámina, con malla de refuerzo en los encuentros. Incluye el extendido, reglado y afinado.":
    "Continuous cement mortar bed over the roof slope to receive tiling or sheeting, with reinforcing mesh at the junctions. Includes spreading, screeding and finishing.",

"Colocación de lámina de polietileno como barrera de vapor bajo el aislamiento de cubierta, con solapes sellados y remontes en los paramentos. Incluye la limpieza del soporte y el sellado de los encuentros.":
    "Laying a polyethylene sheet as a vapor control layer beneath the roof insulation, with sealed laps and upstands at the walls. Includes cleaning the substrate and sealing the junctions.",

"Colocación de paneles rígidos de poliestireno expandido sobre cubierta plana, a matajuntas, para aislamiento térmico previo a la impermeabilización. Incluye el replanteo, el corte y la colocación a junta cerrada.":
    "Laying rigid expanded polystyrene boards on a flat roof, tightly butted, for thermal insulation before the waterproofing. Includes setting out, cutting and laying with closed joints.",

"Colocación de panel de lana mineral rígida sobre cubierta plana o faldón, para aislamiento térmico y acústico. Incluye el replanteo, corte y colocación a junta cerrada con fijación.":
    "Laying rigid mineral wool boards on a flat roof or roof slope, for thermal and acoustic insulation. Includes setting out, cutting and laying with closed joints and fixing.",

"Colocación de geotextil no tejido como capa separadora entre aislamiento y membrana impermeabilizante. Incluye el extendido, los solapes y el recorte en los encuentros.":
    "Laying a non-woven geotextile as a separating layer between the insulation and the waterproofing membrane. Includes spreading, the laps and cutting in at the junctions.",

"Replanteo topográfico de las pendientes, cotas y puntos de desagüe de una cubierta, con nivel láser y maestras de referencia. Incluye el marcado de las líneas de cumbrera y limahoyas.":
    "Setting out the falls, levels and drainage points of a roof by survey, with a laser level and reference rails. Includes marking the ridge and valley lines.",

"Ejecución de maestras de mortero para definir la pendiente y el espesor del relleno de cubierta. Incluye el replanteo, la ejecución de las maestras y el reglado entre ellas.":
    "Formation of mortar screed rails to define the fall and the thickness of the roof filling. Includes setting out, forming the rails and screeding between them.",

"Relleno aligerado de formación de pendientes con bloques de arcilla o poliestireno colocados en seco, previo a la capa de compresión. Incluye el replanteo y la colocación a rompejuntas.":
    "Lightweight fill to form falls, of clay or polystyrene blocks laid dry, before the structural topping. Includes setting out and laying to a staggered bond.",

"Capa de compresión de mortero armado con malla electrosoldada sobre relleno aligerado de cubierta, para repartir cargas. Incluye el extendido, el embebido de la malla y el fratasado.":
    "Reinforced mortar structural topping with welded wire mesh over lightweight roof fill, to spread loads. Includes spreading, embedding the mesh and floating.",

"Capa de mortero de protección sobre el aislamiento térmico de cubierta, previa a la impermeabilización, para dar soporte y continuidad. Incluye el extendido y fratasado.":
    "Protective mortar screed over the roof insulation, before the waterproofing, to give support and continuity. Includes spreading and floating.",

"Ejecución de junta de dilatación en cubierta plana con perfil de junta, fondo de junta y sellado elástico. Incluye la apertura o previsión del hueco, la colocación del fondo y el sellado.":
    "Formation of an expansion joint in a flat roof with a joint profile, backer rod and elastic sealant. Includes forming or allowing for the opening, placing the backer rod and sealing.",

"Ejecución de cazuela o sumidero de desagüe en el punto bajo de la pendiente de cubierta, con conexión a la bajante y sellado de la impermeabilización. Incluye la apertura del hueco y la fijación.":
    "Formation of a drainage sump at the low point of the roof fall, connected to the downpipe and sealed into the waterproofing. Includes forming the opening and fixing.",

"Formación de pendientes en cubierta plana mediante relleno de mortero aligerado, con el espesor variable necesario para dirigir el agua hacia los tragantes con la pendiente mínima de proyecto. Es la capa que determina si la cubierta evacúa o empoza, y el error más común es dejar pendiente insuficiente o contrapendientes junto a los petos. Incluye el replanteo de las líneas de limatesa y de los puntos bajos en los tragantes, la colocación de maestras, el extendido y reglado del mortero, el fratasado y el curado. Medido en superficie realmente ejecutada.":
    "Formation of falls on a flat roof with a lightweight mortar fill, to the varying thickness needed to direct water to the roof drains at the minimum gradient specified. It is the layer that decides whether the roof drains or ponds, and the commonest mistake is to leave too little fall or to create back falls next to the parapets. Includes setting out the hip lines and the low points at the drains, placing screed rails, spreading and screeding the mortar, floating and curing. Measured by the area actually constructed.",

"Capa de mortero de protección sobre la impermeabilización de cubierta plana, armada con malla y con juntas de retracción, que protege el manto del tránsito y de la radiación. Debe ejecutarse sobre una capa separadora: si se vacía directamente sobre la impermeabilización, la retracción del mortero arrastra y desgarra el manto. Incluye la colocación de la lámina separadora, la malla de retracción, el vaciado y reglado del mortero, la ejecución de las juntas de retracción en paños y contra los petos, el fratasado y el curado. Medido en superficie realmente ejecutada.":
    "Protective mortar screed over the waterproofing of a flat roof, reinforced with mesh and with shrinkage joints, protecting the membrane from traffic and from radiation. It must be laid on a separating layer: if it is poured directly onto the waterproofing, the shrinkage of the mortar drags on the membrane and tears it. Includes laying the separating sheet, the shrinkage mesh, pouring and screeding the mortar, forming shrinkage joints in bays and against the parapets, floating and curing. Measured by the area actually constructed.",

"Piso técnico exterior formado por losetas apoyadas sobre pedestales regulables sobre la impermeabilización de la cubierta, sin adherencia ni perforación. Su ventaja es doble: nivela el piso final sobre una base en pendiente y deja la impermeabilización registrable, ya que basta levantar las losetas para inspeccionarla o repararla. Incluye el replanteo de la retícula, la colocación de las bases protectoras sobre el manto, el montaje y regulación de los pedestales, la colocación de las losetas y el ajuste de las piezas perimetrales. Medido en superficie realmente ejecutada.":
    "External paving on adjustable pedestals laid over the roof waterproofing, without adhesive or fixing through it. It has a double advantage: it levels the finished surface over a sloped base and it leaves the waterproofing accessible, since lifting the slabs is enough to inspect or repair it. Includes setting out the grid, placing the protective pads on the membrane, assembling and adjusting the pedestals, laying the slabs and fitting the perimeter pieces. Measured by the area actually constructed.",

# ── Impermeabilización ────────────────────────────────────────────────────
"Impermeabilización de cubierta plana no transitable con membrana de PVC armado con poliéster, soldada en los solapes y remontada en los paramentos. Incluye imprimación, solapes soldados y remontes.":
    "Waterproofing of a non-trafficable flat roof with a polyester reinforced PVC membrane, welded at the laps and turned up at the walls. Includes priming, welded laps and upstands.",

"Cubierta plana transitable acabada con baldosa cerámica antideslizante sobre mortero de agarre, con juntas selladas y pendiente a desagües. Incluye la base de mortero, la colocación y el juntado.":
    "Trafficable flat roof finished with non-slip ceramic tile on a bedding mortar, with sealed joints and falls to the drains. Includes the mortar bed, laying and grouting.",

"Cubierta plana no transitable con acabado de gravilla lavada de protección sobre membrana impermeabilizante. Incluye el extendido de la gravilla en capa uniforme sobre la membrana.":
    "Non-trafficable flat roof finished with a protective layer of washed gravel over the waterproofing membrane. Includes spreading the gravel in an even layer over the membrane.",

"Cubierta plana invertida con aislamiento rígido colocado sobre la membrana impermeabilizante y protegido con gravilla. Incluye la colocación del aislamiento y la capa de protección.":
    "Inverted flat roof with rigid insulation laid over the waterproofing membrane and protected with gravel. Includes laying the insulation and the protective layer.",

"Impermeabilización de cubierta plana con membrana líquida de poliuretano de aplicación en frío, con refuerzo de malla en los puntos singulares. Incluye imprimación y dos manos de membrana.":
    "Waterproofing of a flat roof with a cold applied liquid polyurethane membrane, reinforced with mesh at the details. Includes priming and two coats of membrane.",

"Impermeabilización de cubierta plana con resina acrílica elastomérica en frío, reforzada con velo de fibra en los encuentros. Incluye imprimación y dos manos.":
    "Waterproofing of a flat roof with a cold applied elastomeric acrylic resin, reinforced with a fiber fleece at the junctions. Includes priming and two coats.",

"Ejecución del remonte de la membrana impermeabilizante en el paramento perimetral de la cubierta, con banda de refuerzo y sellado de la entrega. Incluye la preparación del soporte y el sellado.":
    "Forming the upstand of the waterproofing membrane at the perimeter wall of the roof, with a reinforcement strip and the top edge sealed. Includes preparing the substrate and sealing.",

"Refuerzo y sellado del encuentro entre la cubierta plana y el peto o muro perimetral, con banda elástica y membrana. Incluye la limpieza, el refuerzo y el remate.":
    "Reinforcement and sealing of the junction between the flat roof and the parapet or perimeter wall, with an elastic strip and membrane. Includes cleaning, reinforcement and the finish.",

"Prueba de estanqueidad de la cubierta plana por inundación controlada, con registro del nivel y revisión de puntos singulares. Incluye el taponado de desagües, el llenado y la inspección.":
    "Ponding test of the flat roof under controlled flooding, with the water level recorded and the details inspected. Includes plugging the drains, filling and inspection.",

"Colocación de plancha de cemento o loseta de protección sobre membrana impermeabilizante de cubierta transitable, recibida sobre soportes. Incluye el replanteo y la colocación.":
    "Laying cement boards or protective slabs over the waterproofing membrane of a trafficable roof, bedded on supports. Includes setting out and laying.",

"Cubierta plana de losa de concreto armado vaciada en sitio, con encofrado, armadura de refuerzo y curado. Incluye el encofrado, el armado y el vaciado con vibrado.":
    "Cast-in-place reinforced concrete flat roof slab, with formwork, reinforcement and curing. Includes formwork, reinforcement and pouring with vibration.",

"Ejecución de peto o antepecho perimetral de concreto armado en cubierta plana, con encofrado y curado. Incluye el armado, el encofrado y el vaciado.":
    "Construction of a reinforced concrete parapet to a flat roof, with formwork and curing. Includes reinforcement, formwork and pouring.",

# ── Cubierta de teja ──────────────────────────────────────────────────────
"Cubierta con teja criolla de arcilla cocida sobre listonado o base continua, recibida con mortero en aleros, cumbreras y bordes, y colocada en seco en el faldón. Incluye el replanteo de las hiladas para que la teja de remate no quede recortada, la colocación de la teja canal y cobija con el solape que exige la pendiente, el recibido con mortero de las piezas de borde que son las que levanta el viento, la formación de cumbreras y limatesas y la limpieza final. Medido en superficie realmente ejecutada.":
    "Roof covering of fired clay barrel tiles on battens or a continuous bed, bedded in mortar at the eaves, ridges and edges and laid dry on the slope. Includes setting out the courses so that the closing tile is not cut, laying the pan and cover tiles with the lap the gradient requires, bedding the edge tiles in mortar, which are the ones the wind lifts, forming the ridges and hips and the final clean. Measured by the area actually constructed.",

"Cubierta con teja asfáltica tipo shingle clavada sobre tablero continuo con fieltro asfáltico de base. Requiere un tablero continuo y firme, no un simple listonado, porque la teja asfáltica no tiene rigidez propia y copia cualquier irregularidad del soporte. Incluye la colocación del fieltro con solapes, el replanteo de hiladas, el clavado de las piezas con el número de clavos y la posición indicados por el fabricante, ya que de ello depende la resistencia al viento, la formación de cumbreras con piezas específicas y los remates de borde con perfil metálico. Medido en superficie realmente ejecutada.":
    "Roof covering of asphalt shingles nailed to a continuous deck over asphalt felt. It needs a continuous firm deck, not simply battens, because an asphalt shingle has no stiffness of its own and follows every irregularity in the substrate. Includes laying the felt with laps, setting out the courses, nailing the shingles with the number and position of nails the manufacturer specifies, since wind resistance depends on it, forming the ridges with purpose-made units and the edge finishes with metal trim. Measured by the area actually constructed.",

"Formación de cumbrera, limatesa o remate lateral en cubierta de teja, con piezas específicas recibidas con mortero y sellado. Es la línea por la que entra el agua cuando está mal resuelta, y también la que primero levanta el viento. Incluye el replanteo, la nivelación de la línea de cumbrera, la colocación de las piezas con solape en el sentido contrario a los vientos dominantes, el recibido con mortero y el sellado de los encuentros. Medido en longitud realmente ejecutada.":
    "Formation of a ridge, hip or verge on a tiled roof, with purpose-made units bedded in mortar and sealed. It is the line through which water gets in when it is badly detailed, and also the first the wind lifts. Includes setting out, leveling the ridge line, laying the units lapping against the prevailing wind, bedding in mortar and sealing the junctions. Measured by the length actually constructed.",

"Cubierta de teja criolla de arcilla colocada a canal y cobija sobre listonado, con recibido de aleros y cumbreras con mortero. Incluye el replanteo, la colocación y los remates.":
    "Roof covering of clay barrel tiles laid pan and cover on battens, with the eaves and ridges bedded in mortar. Includes setting out, laying and the finishings.",

"Cubierta de teja criolla de arcilla recibida con mortero sobre base continua, sin listonado, para pendientes medias. Incluye la base, la colocación y los remates.":
    "Roof covering of clay barrel tiles bedded in mortar on a continuous bed, without battens, for medium pitches. Includes the bed, laying and the finishings.",

"Cubierta de teja asfáltica en shingle sobre base continua, clavada y con los solapes de fábrica. Incluye el fieltro base, la colocación y los remates de cumbrera.":
    "Roof covering of asphalt shingles on a continuous bed, nailed with the factory laps. Includes the base felt, laying and the ridge finishings.",

"Cubierta de teja de concreto perfilada sobre listonado, clavada o atornillada, con remates de alero y cumbrera. Incluye el replanteo y la colocación.":
    "Roof covering of profiled concrete tiles on battens, nailed or screwed, with eaves and ridge finishings. Includes setting out and laying.",

"Formación de cumbrera y limatesa en cubierta de teja con piezas de remate recibidas con mortero, para cierre estanco del faldón. Incluye el recibido y el sellado.":
    "Formation of the ridge and hips on a tiled roof with purpose-made units bedded in mortar, to close the slope weathertight. Includes bedding and sealing.",

"Ejecución de alero perimetral en cubierta de teja, con piezas de borde recibidas y canal de recogida. Incluye el remate del faldón y la fijación.":
    "Formation of the perimeter eaves on a tiled roof, with the edge units bedded and a collection channel. Includes finishing the slope and fixing.",

"Colocación de listonado de madera sobre la estructura para recibir la cubierta de teja, con separación según el solape de la pieza. Incluye el replanteo y la fijación.":
    "Fixing lumber battens over the structure to receive the roof tiling, spaced according to the lap of the unit. Includes setting out and fixing.",

"Sustitución de piezas de teja rotas o desplazadas en el faldón, sin tocar la estructura. Incluye el levantado de las piezas dañadas y la recolocación con mortero en los remates.":
    "Replacement of broken or displaced tiles on the slope, without touching the structure. Includes lifting the damaged units and relaying them in mortar at the finishings.",

"Colocación de teja de borde o de remate de alero con gancho de fijación, para evitar el levantamiento por viento. Incluye la fijación mecánica de cada pieza.":
    "Laying edge or eaves closing tiles with a fixing clip, to prevent wind uplift. Includes mechanically fixing each unit.",

"Cubierta de teja metálica acanalada imitación teja sobre correas, atornillada con solapes laterales y de cabecera. Incluye el replanteo y la fijación.":
    "Roof covering of corrugated tile-effect metal sheet on purlins, screwed with side and end laps. Includes setting out and fixing.",

"Ejecución de canalón oculto bajo el alero de cubierta de teja, para recogida de aguas lluvias, con su soporte y conexión a bajante. Incluye la fijación y los remates.":
    "Installation of a concealed gutter beneath the eaves of a tiled roof, to collect rainwater, with its support and connection to the downpipe. Includes fixing and the finishings.",

# ── Cubierta metálica y ligera ────────────────────────────────────────────
"Cubierta con lámina metálica acanalada galvanizada o prepintada, fijada a las correas con tornillos autoperforantes con arandela de neopreno. El tornillo debe apretarse hasta comprimir la arandela sin deformar la lámina: apretado de más, la arandela se degrada y filtra; de menos, no sella. Incluye el replanteo del solape lateral y longitudinal en el sentido contrario a los vientos dominantes, la colocación y alineación de las láminas, la fijación en cresta de onda, el sellado de los solapes y los remates de alero, cumbrera y borde. Medido en superficie realmente ejecutada.":
    "Roof covering of galvanized or prefinished corrugated metal sheet, fixed to the purlins with self-drilling screws and neoprene washers. The screw must be tightened until the washer is compressed without deforming the sheet: overtightened, the washer degrades and leaks; undertightened, it does not seal. Includes setting out the side and end laps against the prevailing wind, placing and aligning the sheets, fixing on the crown of the corrugation, sealing the laps and the eaves, ridge and edge finishings. Measured by the area actually constructed.",

"Cubierta con panel sándwich de doble chapa metálica y núcleo aislante de poliuretano, fijado a las correas con tornillería específica y juntas machihembradas selladas. Resuelve en una sola operación la cubrición, el aislamiento térmico y el acabado interior, lo que compensa su mayor costo de material frente a la lámina simple con aislamiento aparte. Incluye el replanteo, el izado y colocación de los paneles con encaje entre ellos, el sellado de las juntas, la fijación y los remates de cumbrera, alero y borde con piezas específicas. Medido en superficie realmente ejecutada.":
    "Roof covering of sandwich panels with two metal faces and a polyurethane insulating core, fixed to the purlins with purpose-made fasteners and sealed tongue and groove joints. It resolves the covering, the thermal insulation and the internal finish in a single operation, which offsets its higher material cost against plain sheeting with separate insulation. Includes setting out, hoisting and placing the panels with the joints engaged, sealing the joints, fixing and the ridge, eaves and edge finishings with purpose-made units. Measured by the area actually constructed.",

"Cubierta o lucernario con lámina de policarbonato alveolar sobre estructura, con perfiles de unión y sellado de alveolos. Los alveolos deben quedar sellados con cinta microperforada en la parte inferior y estanca en la superior, y orientados en el sentido de la pendiente: si se cierran mal, se llenan de condensación y polvo y la lámina se vuelve opaca en pocos meses. Incluye el replanteo, el corte, la colocación con la cara protegida contra la radiación ultravioleta hacia el exterior, el sellado de alveolos, el montaje de los perfiles de unión y los remates. Medido en superficie realmente ejecutada.":
    "Roof covering or rooflight of multiwall polycarbonate sheet on a structure, with joint profiles and the cells sealed. The cells must be sealed with micro-perforated tape at the bottom and airtight tape at the top, and run in the direction of the fall: if they are closed badly they fill with condensation and dust and the sheet turns opaque within months. Includes setting out, cutting, placing with the face protected against ultraviolet radiation to the outside, sealing the cells, fitting the joint profiles and the finishings. Measured by the area actually constructed.",

"Instalación de domo o claraboya en cubierta, con su zócalo de realce, sellado e integración en la impermeabilización. El zócalo de realce no es opcional: un domo instalado a ras del plano de cubierta acaba filtrando en cuanto el agua remansa, de modo que debe elevarse por encima del nivel máximo de agua previsible. Incluye la apertura del hueco con refuerzo del borde, la ejecución del zócalo de realce, la integración de la impermeabilización remontando por el zócalo, la colocación del domo con su sellado perimetral y la prueba de estanqueidad. Medido por unidad instalada.":
    "Installation of a dome or skylight in a roof, with its upstand curb, sealed and integrated into the waterproofing. The upstand curb is not optional: a dome set flush with the plane of the roof ends up leaking as soon as water ponds, so it must be raised above the maximum foreseeable water level. Includes forming the opening with the edge reinforced, building the upstand curb, integrating the waterproofing turned up the curb, placing the dome with its perimeter seal and the watertightness test. Measured per unit installed.",

"Cubierta de lámina metálica acanalada galvanizada sobre correas, atornillada con solapes laterales y de cabecera. Incluye el replanteo, la fijación y los remates.":
    "Roof covering of galvanized corrugated metal sheet on purlins, screwed with side and end laps. Includes setting out, fixing and the finishings.",

"Cubierta de lámina metálica acanalada prepintada sobre correas, atornillada con solapes y remates laterales. Incluye el replanteo y la fijación.":
    "Roof covering of prefinished corrugated metal sheet on purlins, screwed with laps and side finishings. Includes setting out and fixing.",

"Cubierta de panel sándwich con núcleo de poliuretano sobre correas, con junta machihembrada y fijación con tornillo autoperforante. Incluye el replanteo y los remates.":
    "Roof covering of sandwich panels with a polyurethane core on purlins, with tongue and groove joints fixed with self-drilling screws. Includes setting out and the finishings.",

"Cubierta de lámina metálica con fieltro o membrana bajo lámina sobre base continua, para evitar condensaciones. Incluye la colocación de la barrera y la lámina.":
    "Roof covering of metal sheet with a felt or membrane beneath, on a continuous deck, to prevent condensation. Includes laying the barrier and the sheeting.",

"Remate de cumbrera o caballete en cubierta de lámina metálica, con pieza de remate atornillada y sellada. Incluye la colocación y el sellado.":
    "Ridge or ridge cap finish on a metal sheet roof, with a purpose-made capping screwed and sealed. Includes placing and sealing.",

"Ejecución de alero en cubierta de lámina metálica, con perfil de remate de borde atornillado. Incluye el replanteo, corte y fijación.":
    "Formation of the eaves on a metal sheet roof, with a screw-fixed edge trim. Includes setting out, cutting and fixing.",

"Sellado de solapes y remates de cubierta metálica con sellador elástico y tornillos de recambio, para eliminar filtraciones. Incluye la limpieza y el sellado.":
    "Sealing the laps and finishings of a metal roof with elastic sealant and replacement screws, to stop leaks. Includes cleaning and sealing.",

"Cubierta ligera translúcida de policarbonato alveolar sobre perfiles, con junta de unión y fijación atornillada. Incluye el replanteo y la colocación.":
    "Lightweight translucent roof covering of multiwall polycarbonate on framing, with joint strips and screw fixing. Includes setting out and laying.",

"Cubierta ligera de lámina de policarbonato compacto para marquesinas y toldos, con perfiles y fijación. Incluye el replanteo y la colocación.":
    "Lightweight roof covering of solid polycarbonate sheet for canopies and awnings, with framing and fixing. Includes setting out and laying.",

"Cubierta de lámina de fibrocemento ondulada sobre correas, atornillada con solapes. Incluye el replanteo, la fijación y los remates.":
    "Roof covering of corrugated fiber cement sheet on purlins, screwed with laps. Includes setting out, fixing and the finishings.",

"Ejecución de bajante de PVC para aguas lluvias en cubierta metálica, con abrazaderas y conexión al canalón. Incluye la fijación y los accesorios.":
    "Installation of a PVC rainwater downpipe to a metal roof, with brackets and connection to the gutter. Includes fixing and the fittings.",

"Ejecución de canalón de PVC o lámina galvanizada en el alero de cubierta metálica, con soportes y pendiente a bajante. Incluye la fijación y los remates.":
    "Installation of a PVC or galvanized sheet gutter at the eaves of a metal roof, with brackets and a fall to the downpipe. Includes fixing and the finishings.",

"Cubierta ligera translúcida de policarbonato alveolar sobre perfilería, para iluminación natural de galerías y terrazas. Incluye la estructura de apoyo, la colocación y los remates.":
    "Lightweight translucent roof covering of multiwall polycarbonate on framing, for natural light to galleries and terraces. Includes the support structure, laying and the finishings.",

"Cubierta ligera translúcida de panel de fibra de vidrio ondulado sobre correas, para zonas de trabajo o lavado. Incluye la colocación y la fijación.":
    "Lightweight translucent roof covering of corrugated glass fiber panels on purlins, for work or washing areas. Includes laying and fixing.",

"Marquesina traslúcida de policarbonato sobre estructura metálica ligera, con pendiente y canal de recogida. Incluye la estructura, la colocación y los remates.":
    "Translucent polycarbonate canopy on a lightweight metal structure, with a fall and a collection channel. Includes the structure, laying and the finishings.",

"Cubierta ligera de lona tensada sobre estructura, para sombreado de terrazas y estacionamientos. Incluye la estructura de apoyo, el tensado y los anclajes.":
    "Lightweight tensioned fabric roof on a structure, for shading terraces and parking areas. Includes the support structure, tensioning and the anchors.",

"Cubierta de malla sombra tensada sobre estructura para áreas recreativas, con cables y anclajes. Incluye la estructura y el tensado de la malla.":
    "Tensioned shade netting on a structure for recreation areas, with cables and anchors. Includes the structure and tensioning the netting.",

"Cubierta ligera de policarbonato curvo para claraboyas y lucernarios de pasillo. Incluye la perfilería de apoyo y la colocación.":
    "Lightweight curved polycarbonate roof covering for skylights and corridor rooflights. Includes the support framing and laying.",

"Cubierta ligera de lámina metálica delgada para cobertizos y áreas de servicio, sobre correas de madera. Incluye la colocación y la fijación.":
    "Lightweight thin metal sheet roof covering for sheds and service areas, on lumber purlins. Includes laying and fixing.",

"Estructura metálica ligera de perfiles para apoyo de cubierta translúcida, con pintura anticorrosiva y fijaciones. Incluye el armado y el montaje.":
    "Lightweight metal framing to support a translucent roof covering, with anti-corrosion paint and fixings. Includes assembly and erection.",

"Ejecución de remate lateral y de borde en cubierta translúcida, con perfil de remate y sellado. Incluye la fijación y el sellado.":
    "Formation of the verge and edge trim on a translucent roof, with a trim and sealant. Includes fixing and sealing.",

"Cubierta ligera de policarbonato alveolar con perfiles de unión estancos, para galerías expuestas a lluvia. Incluye la colocación y el sellado de juntas.":
    "Lightweight multiwall polycarbonate roof covering with weathertight joint profiles, for galleries exposed to rain. Includes laying and sealing the joints.",

"Cubierta ligera de policarbonato multicapa de gran espesor para cerramiento de techos con alta exigencia térmica. Incluye la perfilería y la colocación.":
    "Lightweight multiwall polycarbonate roof covering of high thickness for roofs with a high thermal requirement. Includes the framing and laying.",

"Colocación de tragante o sumidero de desagüe en cubierta translúcida, con conexión a bajante y sellado. Incluye la apertura y la fijación.":
    "Installation of a roof drain in a translucent roof, connected to the downpipe and sealed. Includes forming the opening and fixing.",

"Cubierta ligera de teja translúcida de policarbonato imitación teja, para iluminación natural manteniendo la estética de teja. Incluye la colocación y fijación.":
    "Lightweight translucent polycarbonate tile-effect roof covering, for natural light while keeping the appearance of tiling. Includes laying and fixing.",

"Cubierta ligera de lámina acrílica translúcida sobre perfiles, para lucernarios y marquesinas. Incluye la perfilería y la colocación.":
    "Lightweight translucent acrylic sheet roof covering on framing, for rooflights and canopies. Includes the framing and laying.",

# ── Estructura de techo ───────────────────────────────────────────────────
"Suministro y montaje de estructura metálica de techo formada por cerchas, vigas y correas de perfil laminado o conformado, con sus conexiones soldadas o atornilladas y su imprimación anticorrosiva. Incluye la verificación de los apoyos y de las placas base, el izado y presentado de las piezas, el arriostramiento provisional durante el montaje, la ejecución de las uniones definitivas, la comprobación geométrica de niveles y pendientes y el retoque de la protección anticorrosiva en las zonas afectadas por la soldadura. Medido en peso realmente montado.":
    "Supply and erection of a metal roof structure of trusses, beams and purlins in rolled or cold formed sections, with welded or bolted connections and an anti-corrosion primer. Includes checking the bearings and the base plates, hoisting and offering up the members, temporary bracing during erection, making the final connections, the geometric check of levels and falls and touching up the anti-corrosion protection where it has been affected by welding. Measured by the weight actually erected.",

"Suministro y montaje de estructura de madera de techo formada por pares, correas y tirantes, con uniones mediante herrajes metálicos, y su tratamiento preservante. Incluye la selección de las piezas verificando escuadría y ausencia de defectos, el corte y labra, el izado y montaje con apeo provisional, la fijación con herrajes, la aplicación del preservante en todas las caras y muy especialmente en las testas y zonas de apoyo, y la comprobación de niveles y pendientes. Medido en superficie realmente ejecutada.":
    "Supply and erection of a lumber roof structure of rafters, purlins and ties, with metal connector joints, and its preservative treatment. Includes selecting the members and checking the section sizes and the absence of defects, cutting and shaping, hoisting and erecting with temporary supports, fixing with the hardware, applying preservative to every face and particularly to the end grain and the bearing areas, and checking levels and falls. Measured by the area actually constructed.",

"Estructura metálica de cerchas y correas para cubierta a dos aguas, con perfiles de acero, soldada y pintada. Incluye el armado en taller y el montaje en obra.":
    "Metal roof structure of trusses and purlins for a gable roof, in steel sections, welded and painted. Includes shop fabrication and erection on site.",

"Estructura de madera para cubierta con pares, tirantes y correas, con herrajes de unión y tratamiento preservante. Incluye el armado y el montaje.":
    "Timber roof structure with rafters, ties and purlins, with connector hardware and preservative treatment. Includes assembly and erection.",

"Colocación de correas de acero sobre las cerchas para apoyo de la cubierta, con fijación soldada o atornillada. Incluye el replanteo y la fijación.":
    "Fixing steel purlins over the trusses to support the roof covering, welded or bolted. Includes setting out and fixing.",

"Colocación de correas de madera sobre la estructura para apoyo de la cubierta, con fijación mecánica. Incluye el replanteo y la fijación.":
    "Fixing lumber purlins over the structure to support the roof covering, mechanically fixed. Includes setting out and fixing.",

"Montaje de cercha metálica prefabricada para cubierta, con izado y fijación a los apoyos. Incluye el replanteo de apoyo y la fijación.":
    "Erection of a prefabricated metal roof truss, hoisted and fixed to its bearings. Includes setting out the bearings and fixing.",

"Colocación de viga cumbrera de madera en la parte superior de la cubierta, para apoyo de los pares. Incluye el replanteo y la fijación.":
    "Fixing a lumber ridge beam at the top of the roof, to carry the rafters. Includes setting out and fixing.",

"Refuerzo de estructura de techo con angulares de acero atornillados, para rigidizar nudos o corregir deformaciones. Incluye la fijación.":
    "Strengthening a roof structure with bolted steel angles, to stiffen joints or correct deformation. Includes fixing.",

"Aplicación de pintura anticorrosiva sobre estructura metálica de techo, con limpieza previa y dos manos. Incluye la preparación de la superficie.":
    "Application of anti-corrosion paint to a metal roof structure, with cleaning beforehand and two coats. Includes preparation of the surface.",

"Aplicación de preservante fungicida e insecticida sobre estructura de madera de techo, con dos manos. Incluye la limpieza y el tratamiento.":
    "Application of fungicidal and insecticidal preservative to a lumber roof structure, in two coats. Includes cleaning and treatment.",

"Apuntalamiento provisional de estructura de techo durante la reparación, con puntales metálicos y durmientes de reparto. Incluye el montaje y el desmontaje.":
    "Temporary shoring of a roof structure during repair, with steel shores and spreader beams. Includes erection and dismantling.",

"Ejecución de viga de amarre perimetral de concreto armado en el apoyo de la cubierta, con encofrado y curado. Incluye el armado y el vaciado.":
    "Construction of a perimeter reinforced concrete tie beam at the roof bearing, with formwork and curing. Includes reinforcement and pouring.",

"Anclaje químico o mecánico de la estructura de techo a la losa o viga de apoyo, con pernos de anclaje. Incluye el taladrado y la fijación.":
    "Chemical or mechanical anchoring of the roof structure to the slab or supporting beam, with anchor bolts. Includes drilling and fixing.",

# ── Claraboyas y accesos ──────────────────────────────────────────────────
"Instalación de claraboya o lucernario de policarbonato sobre cubierta, con zócalo, fijación y sellado. Incluye la apertura del hueco y la colocación.":
    "Installation of a polycarbonate skylight or rooflight over the roof, with an upstand, fixing and sealing. Includes forming the opening and placing.",

"Instalación de claraboya practicable de cubierta con mecanismo de apertura, para ventilación y acceso. Incluye la fijación y el sellado.":
    "Installation of an opening rooflight with a mechanism, for ventilation and access. Includes fixing and sealing.",

"Ejecución de lucernario corrido de policarbonato en cubierta, con zócalo y perfiles de remate. Incluye la estructura y la colocación.":
    "Construction of a continuous polycarbonate rooflight in the roof, with an upstand and trim profiles. Includes the structure and laying.",

"Ejecución de zócalo de concreto perimetral para apoyo de claraboya o lucernario, con encofrado y curado. Incluye el armado y el vaciado.":
    "Construction of a perimeter concrete upstand to carry a skylight or rooflight, with formwork and curing. Includes reinforcement and pouring.",

"Colocación de escalera fija de acceso a cubierta, con anclajes y fijación a la estructura. Incluye el replanteo y el montaje.":
    "Installation of a fixed ladder giving access to the roof, anchored and fixed to the structure. Includes setting out and assembly.",

"Instalación de línea de vida horizontal en cubierta con cable y anclajes, para trabajos en altura. Incluye la fijación de los postes y el tensado.":
    "Installation of a horizontal lifeline on the roof with cable and anchors, for work at height. Includes fixing the posts and tensioning.",

"Colocación de gancho o anclaje de seguridad en cubierta para amarre de línea de vida, con fijación a la estructura. Incluye el taladrado y la fijación.":
    "Installation of a safety hook or anchor on the roof to attach a lifeline, fixed to the structure. Includes drilling and fixing.",

"Ejecución de pase de instalaciones (tubería, cable) a través de la cubierta, con sellado y refuerzo de la impermeabilización. Incluye la apertura y el sellado.":
    "Forming a penetration for services (pipe, cable) through the roof, sealed and with the waterproofing reinforced. Includes forming the opening and sealing.",

"Instalación de rejilla o ventosa de ventilación de cubierta, para evitar condensaciones en el espacio bajo cubierta. Incluye la apertura y la fijación.":
    "Installation of a roof vent grille or terminal, to prevent condensation in the roof space. Includes forming the opening and fixing.",

"Instalación de claraboya de vidrio templado sobre cubierta, con marco y sellado estructural. Incluye la fijación y el sellado.":
    "Installation of a tempered glass skylight over the roof, with a frame and structural sealing. Includes fixing and sealing.",

"Ejecución de marco perimetral de apoyo de claraboya en chapa plegada o perfil, con fijación y sellado. Incluye el replanteo y la fijación.":
    "Construction of a perimeter frame to carry a skylight, in folded sheet or section, fixed and sealed. Includes setting out and fixing.",

"Reparación de claraboya existente con sustitución del sellado y de piezas dañadas. Incluye la limpieza, el sellado y la fijación.":
    "Repair of an existing skylight by replacing the sealant and damaged parts. Includes cleaning, sealing and fixing.",

# ── Evacuación de aguas ───────────────────────────────────────────────────
"Suministro y montaje de canal de recogida de aguas lluvias en alero, con sus soportes, uniones, tapas y conexión a bajante. La pendiente hacia la bajante es lo que decide si el canal evacúa o rebosa: un canal montado a nivel se llena de agua y de hojas y termina desbordando sobre la fachada. Incluye el replanteo con la pendiente mínima hacia el punto de desagüe, la colocación de los soportes con la separación indicada, el montaje del canal, el sellado de uniones, la colocación de tapas de extremo y la conexión a la bajante. Medido en longitud realmente montada.":
    "Supply and installation of a rainwater gutter at the eaves, with its brackets, unions, stop ends and connection to the downpipe. The fall towards the downpipe is what decides whether the gutter drains or overflows: a gutter set level fills with water and leaves and ends up discharging over the facade. Includes setting out to the minimum fall to the outlet, fixing the brackets at the spacing specified, assembling the gutter, sealing the unions, fitting the stop ends and connecting to the downpipe. Measured by the length actually installed.",

"Suministro y montaje de bajante de aguas lluvias en PVC, con sus abrazaderas, codos y conexión a la red de drenaje. Incluye el replanteo del recorrido, la fijación de las abrazaderas al paramento con la separación indicada, el montaje de los tramos con sus codos de arranque y de pie, el sellado de las uniones y la conexión a la tanquilla o punto de vertido, evitando la descarga libre contra el piso que erosiona y salpica la fachada. Medido en longitud realmente montada.":
    "Supply and installation of a PVC rainwater downpipe, with its brackets, bends and connection to the drainage system. Includes setting out the run, fixing the brackets to the wall at the spacing specified, assembling the lengths with the offset and shoe bends, sealing the joints and connecting to the inspection chamber or discharge point, avoiding a free discharge onto the ground, which erodes it and splashes the facade. Measured by the length actually installed.",

"Suministro y montaje de tragante, boquilla o sumidero de cubierta con su rejilla guardahojas, integrado en la impermeabilización. Es el punto por el que sale toda el agua de la cubierta y también el que más falla, ya sea por obstrucción o por un sellado deficiente del encuentro con el manto. Incluye la formación del rebaje en el punto bajo, la colocación de la pieza con su ala embebida entre las capas de impermeabilización, el sellado del encuentro, la colocación de la rejilla y la comprobación de evacuación mediante prueba con agua. Medido por unidad instalada.":
    "Supply and installation of a roof drain with its leaf guard, integrated into the waterproofing. It is the point through which all the water leaves the roof and also the one that fails most, whether through blockage or through a poor seal at the junction with the membrane. Includes forming the recess at the low point, placing the unit with its flange embedded between the layers of waterproofing, sealing the junction, fitting the grate and checking the discharge with a water test. Measured per unit installed.",

"Formación del alero y del remate del borde de cubierta, con su pieza de terminación, goterón y sellado. El goterón es lo que separa el agua del paramento: sin él, el agua rodea el canto por capilaridad y escurre por la fachada dejando el chorreado sucio característico bajo los aleros mal resueltos. Incluye el replanteo, la colocación de la pieza de remate con su vuelo, la formación del goterón, el sellado del encuentro con la cubierta y con el paramento y la fijación. Medido en longitud realmente ejecutada.":
    "Formation of the eaves and the edge trim of the roof, with the closing unit, drip edge and sealant. The drip edge is what breaks the water away from the wall: without it the water runs round the edge by capillary action and down the facade, leaving the characteristic staining below badly detailed eaves. Includes setting out, placing the trim with its projection, forming the drip, sealing the junction with the roof and with the wall and fixing. Measured by the length actually constructed.",

"Colocación de canal de PVC o lámina galvanizada en el alero, con soportes y pendiente a bajante. Incluye el replanteo, la fijación y los remates.":
    "Installation of a PVC or galvanized sheet gutter at the eaves, with brackets and a fall to the downpipe. Includes setting out, fixing and the finishings.",

"Ejecución de bajante de PVC para aguas lluvias, con abrazaderas y conexión al canalón. Incluye la fijación y los accesorios.":
    "Installation of a PVC rainwater downpipe, with brackets and connection to the gutter. Includes fixing and the fittings.",

"Colocación de tragante o boquilla de desagüe en cubierta, con conexión a la bajante y sellado de la impermeabilización. Incluye la apertura y la fijación.":
    "Installation of a roof drain, connected to the downpipe and sealed into the waterproofing. Includes forming the opening and fixing.",

"Ejecución de alero y remate de borde de cubierta, con perfil de remate y sellado. Incluye la fijación y el sellado.":
    "Formation of the eaves and edge trim of the roof, with a trim and sealant. Includes fixing and sealing.",

# ── Mantenimiento y reparación ────────────────────────────────────────────
"Limpieza y mantenimiento de cubierta, con retirada de hojas, sedimentos y vegetación, desobstrucción de canales y tragantes, y revisión del estado general. Es la intervención preventiva más rentable que existe en una edificación: la mayoría de las filtraciones de cubierta no se deben al fallo de la impermeabilización sino a un tragante obstruido que provoca el remanso del agua. Incluye el barrido y retirada de residuos, la limpieza de canales y bajantes, la comprobación de evacuación con agua, la revisión visual de encuentros y pases y el informe de las reparaciones que se detecten necesarias. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
    "Cleaning and maintenance of a roof, with removal of leaves, silt and vegetation, clearing of gutters and drains and a review of the general condition. It is the most cost-effective preventive work there is in a building: most roof leaks are not caused by a failure of the waterproofing but by a blocked drain that makes the water back up. Includes sweeping and removing waste, cleaning the gutters and downpipes, checking the discharge with water, visual inspection of the junctions and penetrations and a report of the repairs found necessary. Measured by the area actually completed, deducting voids over 1 m².",

"Reparación puntual de cubierta en zonas con filtración localizada, con saneado del área, reposición de la impermeabilización y refuerzo del punto de fallo. Incluye la localización del origen real de la filtración, que rara vez coincide con el punto donde aparece la mancha en el techo porque el agua recorre la losa antes de caer, el saneado del área afectada, la imprimación, la reposición del sistema con solape amplio sobre lo existente, el refuerzo del punto singular y la prueba de estanqueidad. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
    "Localized repair of a roof where there is a local leak, cutting out the area, replacing the waterproofing and reinforcing the point of failure. Includes locating the real origin of the leak, which rarely coincides with the point where the stain appears on the ceiling because the water travels across the slab before it drips, cutting out the affected area, priming, reinstating the system with a generous lap onto the existing, reinforcing the detail and the watertightness test. Measured by the area actually completed, deducting voids over 1 m².",

"Limpieza de cubierta con retirada de hojas, sedimentos y revisión de desagües y remates, con informe de estado. Incluye la limpieza de canales y tragantes.":
    "Cleaning of a roof with removal of leaves and silt and inspection of the drains and finishings, with a condition report. Includes cleaning the gutters and drains.",

"Reparación puntual de cubierta con sustitución del tramo dañado de membrana o lámina, con sellado de solapes. Incluye la limpieza y el sellado.":
    "Localized repair of a roof by replacing the damaged length of membrane or sheeting, with the laps sealed. Includes cleaning and sealing.",

"Reparación de canal o bajante de aguas lluvias con sustitución de tramos y accesorios dañados. Incluye el desmontaje parcial y la reposición.":
    "Repair of a rainwater gutter or downpipe by replacing damaged lengths and fittings. Includes partial dismantling and reinstatement.",

"Limpieza de canalones y bajantes con retirada de sedimentos y comprobación de la evacuación. Incluye la limpieza y el informe.":
    "Cleaning of gutters and downpipes with removal of silt and checking the discharge. Includes cleaning and the report.",

"Reposición de tornillería y sellado de solapes de cubierta metálica, para eliminar filtraciones. Incluye la sustitución y el sellado.":
    "Replacement of the fixings and sealing of the laps of a metal roof, to stop leaks. Includes replacement and sealing.",

"Sustitución de lámina de cubierta metálica dañada, con desmontaje de la pieza y colocación de la nueva. Incluye el desmontaje y la reposición.":
    "Replacement of a damaged metal roof sheet, taking down the old one and laying the new. Includes dismantling and reinstatement.",

"Reparación de faldón de cubierta de lámina metálica con sustitución de tramos y sellado de solapes. Incluye el desmontaje y la reposición.":
    "Repair of a metal roof slope by replacing lengths and sealing the laps. Includes dismantling and reinstatement.",

"Reparación de faldón de cubierta de teja con sustitución de piezas rotas o desplazadas. Incluye el levantado y la recolocación.":
    "Repair of a tiled roof slope by replacing broken or displaced units. Includes lifting and relaying.",

"Reparación de impermeabilización de cubierta plana con aplicación de membrana líquida sobre la zona dañada, con refuerzo de malla. Incluye la preparación y el sellado.":
    "Repair of the waterproofing of a flat roof by applying a liquid membrane over the damaged area, reinforced with mesh. Includes preparation and sealing.",

"Revisión general de cubierta con inspección de remates, desagües y estructura, y emisión de informe de estado y recomendaciones. Incluye la inspección visual.":
    "General survey of a roof with inspection of the finishings, drains and structure, and the issue of a condition report and recommendations. Includes visual inspection.",

"Sustitución de cumbrera o remate superior de cubierta dañado, con desmontaje y colocación de la nueva pieza. Incluye el recibido y el sellado.":
    "Replacement of a damaged ridge or capping, taking down the old and laying the new unit. Includes bedding and sealing.",

"Reparación de claraboya o lucernario con sustitución del sellado y de piezas dañadas. Incluye la limpieza y el sellado.":
    "Repair of a skylight or rooflight by replacing the sealant and damaged parts. Includes cleaning and sealing.",

"Refuerzo de estructura de cubierta existente con angulares o perfiles atornillados, para rigidizar. Incluye la fijación.":
    "Strengthening an existing roof structure with bolted angles or sections, to stiffen it. Includes fixing.",

"Aplicación de tratamiento anticorrosivo sobre cubierta metálica, con limpieza previa y dos manos. Incluye la preparación de la superficie.":
    "Application of anti-corrosion treatment to a metal roof, with cleaning beforehand and two coats. Includes preparation of the surface.",

"Reparación de junta de dilatación de cubierta con sustitución del sellado y del fondo de junta. Incluye la limpieza y el sellado.":
    "Repair of a roof expansion joint by replacing the sealant and the backer rod. Includes cleaning and sealing.",

"Sustitución de bajante de aguas lluvias dañada, con desmontaje y colocación de la nueva. Incluye la fijación y los accesorios.":
    "Replacement of a damaged rainwater downpipe, taking down the old and installing the new. Includes fixing and the fittings.",

"Sustitución de canal de recogida de aguas lluvias dañado, con desmontaje y colocación del nuevo. Incluye la fijación y los remates.":
    "Replacement of a damaged rainwater gutter, taking down the old and installing the new. Includes fixing and the finishings.",

"Limpieza de cubierta con agua a presión para eliminar suciedad, hongos y sedimentos, previa a la impermeabilización o pintura. Incluye la limpieza a presión.":
    "Cleaning of a roof with a pressure washer to remove dirt, mold and silt, before waterproofing or painting. Includes pressure washing.",

"Aplicación de pintura impermeabilizante elastomérica sobre cubierta metálica, con dos manos. Incluye la limpieza y la aplicación.":
    "Application of an elastomeric waterproofing coating to a metal roof, in two coats. Includes cleaning and application.",

"Sustitución de tragante o boquilla de desagüe de cubierta dañado, con desmontaje y colocación del nuevo. Incluye la fijación y el sellado.":
    "Replacement of a damaged roof drain, taking down the old and installing the new. Includes fixing and sealing.",
}
