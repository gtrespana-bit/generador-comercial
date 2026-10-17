# -*- coding: utf-8 -*-
"""Descripciones — Fundaciones (capítulo completo, 99).

Criterios de este lote:
  · «Zapata aislada» es isolated footing en Estados Unidos y pad
    foundation en el Reino Unido; la «corrida» es strip footing y strip
    foundation.
  · «Concreto pobre de limpieza» es mud slab y blinding: una capa que no
    es estructural sino de ejecución, y que existe para aislar el acero
    del terreno.
  · «Recalce» es underpinning, y se ejecuta por bataches alternos porque
    excavar bajo toda la fundación a la vez provoca el colapso que se
    pretende evitar.
  · «Viga de riostra» son tie beams. «Viga de fundación» es grade beam en
    los Estados Unidos y ground beam en el Reino Unido.
  · «Losa de fundación» es mat foundation en los Estados Unidos y raft
    foundation en el Reino Unido.
  · «Pilote vaciado en sitio» es cast-in-place pile; allí se dice drilled
    shaft y aquí bored pile, y el hormigonado se hace con tubo tremie.
    «Descabezado» es pile cut-off y el «cabezal» es pile cap.
  · El «trasdós» de un muro de contención es su rear face, y el empuje
    que lo tumba casi nunca es el de tierras sino el hidrostático.
"""

LOTE = {
# ── Preparación del terreno ───────────────────────────────────────────────
"Sustitución de terreno blando con material granular. Incluye la excavación y el relleno compactado. Medido por metro cúbico sustituido.":
    "Replacement of soft ground with granular material. Includes excavation and compacted backfill. Measured per cubic meter replaced.",
"Mejoramiento de suelo con adición de cemento y compactación. Incluye la mezcla y la compactación. Medido por metro cúbico mejorado.":
    "Soil improvement by the addition of cement and compaction. Includes mixing and compaction. Measured per cubic meter improved.",
"Nivelación y compactación del fondo de fundación. Incluye la nivelación y la compactación. Medido por metro cuadrado ejecutado.":
    "Leveling and compaction of the bottom of the footing excavation. Includes leveling and compaction. Measured per square meter constructed.",
"Riego y compactación del fondo de fundación. Incluye el riego y la compactación. Medido por metro cuadrado ejecutado.":
    "Watering and compaction of the bottom of the footing excavation. Includes watering and compaction. Measured per square meter constructed.",
"Verificación de capacidad portante del fondo de fundación. Incluye la comprobación. Medido por metro cuadrado verificado.":
    "Verification of the bearing capacity of the bottom of the footing excavation. Includes the check. Measured per square meter verified.",
"Colocación de geotextil de separación en fondo de fundación. Incluye la colocación del geotextil. Medido por metro cuadrado colocado.":
    "Laying a separating geotextile at the bottom of the footing excavation. Includes laying the geotextile. Measured per square meter installed.",
"Limpieza y saneo del fondo de fundación previo al vaciado. Incluye la limpieza. Medido por metro cuadrado saneado.":
    "Cleaning and preparation of the bottom of the footing excavation before the pour. Includes cleaning. Measured per square meter prepared.",

# ── Zapatas ───────────────────────────────────────────────────────────────
"Capa de concreto pobre de limpieza de 5 cm de espesor medio, vaciada sobre el fondo de excavación antes de armar la fundación. Cumple una función que no es estructural sino de ejecución: aísla el acero del terreno, evita que la tierra contamine el concreto estructural y proporciona una superficie limpia y a nivel donde replantear y apoyar los separadores. Incluye el repaso y compactación del fondo, el vaciado y extendido del concreto, su reglado a nivel y el marcado de los ejes de la fundación sobre la capa endurecida. Medido en superficie realmente ejecutada.":
    "Mud slab of 5 cm average thickness, poured over the bottom of the excavation before the footing is reinforced. It serves a purpose of execution rather than a structural one: it separates the steel from the ground, stops soil contaminating the structural concrete and gives a clean level surface on which to set out and stand the spacers. Includes going over and compacting the bottom, pouring and spreading the concrete, screeding it level and marking the center lines of the footing on the hardened slab. Measured by the area actually constructed.",

"Suministro, corte, doblado, armado y colocación de acero de refuerzo en cabillas corrugadas de límite elástico 4.200 kg/cm2 en zapatas y bases de fundación, según los planos de despiece. Incluye el corte y doblado en obra o el recibo del acero ya elaborado, el armado de las parrillas con amarre de alambre en todos los cruces del perímetro y alternos en el interior, la colocación de separadores para garantizar el recubrimiento especificado por todas las caras, el arriostramiento del armado para que no se desplace durante el vaciado y la revisión del despiece antes de autorizar el concreto. Medido en peso de acero realmente colocado, sin incluir despuntes ni solapes no previstos en el despiece.":
    "Supply, cutting, bending, assembly and placing of deformed bar reinforcement of 4,200 kg/cm² yield strength to footings and foundation bases, to the bending schedules. Includes cutting and bending on site or taking delivery of the steel pre-bent, assembling the mats tied with wire at every intersection around the perimeter and at alternate intersections within, placing spacers to give the specified cover on every face, bracing the cage so that it cannot move during the pour and checking the schedule before the concrete is authorized. Measured by the weight of steel actually placed, excluding offcuts and laps not allowed for in the schedule.",

"Encofrado de las caras laterales de zapata mediante paneles de madera con sus puntales y arriostramientos, y su posterior desencofrado. Incluye el replanteo y montaje de los paneles, la comprobación de escuadras, plomos y dimensiones antes del vaciado, el apuntalamiento y arriostramiento que impide la apertura del encofrado por el empuje del concreto fresco, la aplicación de desmoldeante, el desencofrado cuidadoso una vez alcanzada la resistencia necesaria, y la limpieza y acopio de los paneles para su reutilización. Medido en superficie de encofrado en contacto con el concreto.":
    "Formwork to the sides of a footing using wood panels with shores and bracing, and its subsequent stripping. Includes setting out and erecting the panels, checking the squareness, plumb and dimensions before the pour, the shoring and bracing that stops the formwork opening under the thrust of the wet concrete, applying release agent, careful stripping once the necessary strength has been reached, and cleaning and stacking the panels for reuse. Measured by the area of formwork in contact with the concrete.",

"Concreto premezclado de resistencia 210 kg/cm2 vaciado en zapata aislada, incluida su compactación por vibrado y su curado. Incluye la revisión previa del armado, del encofrado y del recubrimiento, la recepción y comprobación del concreto a la llegada con rechazo de la carga si no cumple el asentamiento, el vaciado por capas evitando la segregación, la compactación con vibrador de aguja sin tocar el armado ni el encofrado, el reglado de la cara superior, el curado durante los primeros días y la toma de probetas cuando el control de calidad lo exija. Medido en volumen teórico según las dimensiones de proyecto.":
    "Ready-mixed concrete of 210 kg/cm² strength poured into an isolated footing, including compaction by vibration and curing. Includes the prior check of the cage, of the formwork and of the cover, taking delivery of and checking the concrete on arrival and rejecting the load if the slump is not right, pouring in layers avoiding segregation, compacting with an internal vibrator without touching the cage or the formwork, screeding the top face, curing over the first few days and taking test cylinders where quality control requires it. Measured by the theoretical volume to the design dimensions.",

"Concreto premezclado de resistencia 210 kg/cm2 vaciado en zapata corrida bajo muro o hilera de columnas, incluida su compactación por vibrado y su curado. El vaciado en zanja continua rinde algo mejor que el de zapatas aisladas por la continuidad del frente de trabajo. Incluye la revisión previa del armado y del recubrimiento, la recepción y comprobación del concreto, el vaciado por capas, la compactación con vibrador de aguja, el reglado de la cara superior a la cota prevista y el curado durante los primeros días. Medido en volumen teórico según las dimensiones de proyecto.":
    "Ready-mixed concrete of 210 kg/cm² strength poured into a strip footing under a wall or a line of columns, including compaction by vibration and curing. Pouring into a continuous trench gives a slightly better output than isolated footings because of the continuity of the working face. Includes the prior check of the cage and of the cover, taking delivery of and checking the concrete, pouring in layers, compacting with an internal vibrator, screeding the top face to the level specified and curing over the first few days. Measured by the theoretical volume to the design dimensions.",

"Pedestal de concreto armado de resistencia 210 kg/cm2 que arranca de la zapata y eleva el apoyo de la columna hasta la cota de arranque, incluidos su encofrado, su vaciado y su curado. Incluye el replanteo sobre la zapata, el montaje y aplomado del encofrado con arriostramiento en las cuatro caras, la comprobación de que las cabillas de espera quedan en su posición y con la longitud de solape prevista, el vaciado y vibrado por capas, el desencofrado y el curado. No incluye el acero de refuerzo, que se valora por su peso. Medido en volumen teórico según las dimensiones de proyecto.":
    "Reinforced concrete pedestal of 210 kg/cm² strength rising from the footing and taking the bearing of the column up to the commencing level, including its formwork, pouring and curing. Includes setting out on the footing, erecting and plumbing the formwork with bracing on all four faces, checking that the starter bars are in position and have the lap length specified, pouring and vibrating in layers, stripping and curing. It does not include the reinforcement, which is priced by weight. Measured by the theoretical volume to the design dimensions.",

"Ejecución de dado o base de concreto armado para el apoyo de equipos, máquinas, tanques o estructuras menores, con su encofrado, armado, vaciado y previsión de pernos de anclaje. Incluye la excavación y compactación del fondo, el encofrado, el armado, la colocación de la plantilla de pernos de anclaje antes del vaciado, que es lo que garantiza que el equipo asiente sin ajustes forzados, el vaciado y vibrado, el curado y el desencofrado. Medido por unidad ejecutada.":
    "Construction of a reinforced concrete plinth or base to carry equipment, machinery, tanks or minor structures, with its formwork, reinforcement, pour and provision for anchor bolts. Includes excavation and compaction of the bottom, the formwork, the reinforcement, placing the anchor bolt template before the pour, which is what guarantees that the equipment beds down without forced adjustment, pouring and vibrating, curing and stripping. Measured per unit constructed.",

"Recalce de fundación existente mediante bataches, para ampliar su superficie de apoyo o descender su cota cuando aparecen asientos o cuando se aumenta la carga sobre la estructura. Se ejecuta por tramos alternos y nunca en continuo: excavar bajo toda la fundación a la vez la deja sin apoyo y provoca el colapso que se pretende evitar. Incluye el estudio y la definición del orden de bataches, la excavación por tramos alternos, el encofrado, el armado con conexión a la fundación existente mediante anclaje químico, el vaciado con mortero de retracción compensada, el acuñado contra la fundación existente y la espera antes de abrir el tramo siguiente. Medido en longitud realmente recalzada.":
    "Underpinning of an existing footing in bays, to widen its bearing area or to lower its level where settlement has appeared or where the load on the structure is being increased. It is carried out in alternate bays and never continuously: excavating under the whole footing at once leaves it without support and causes the collapse it is meant to prevent. Includes the study and the fixing of the order of the bays, excavation in alternate bays, the formwork, the reinforcement tied into the existing footing with chemical anchors, pouring with shrinkage-compensating mortar, wedging against the existing footing and waiting before the next bay is opened. Measured by the length actually underpinned.",

"Refuerzo de zapata existente mediante ampliación de su superficie con una corona de concreto armado conectada al elemento original. Incluye el descubrimiento de la zapata existente, el repicado de su superficie para dar adherencia, la perforación y anclaje químico de los conectores que cosen la ampliación al núcleo, el armado de la corona, el encofrado, el vaciado con concreto de retracción compensada, el curado y el relleno perimetral. Medido en superficie de ampliación realmente ejecutada.":
    "Strengthening of an existing footing by widening its area with a ring of reinforced concrete tied to the original element. Includes exposing the existing footing, hacking its surface to provide a bond, drilling and chemically anchoring the dowels that stitch the widening to the core, reinforcing the ring, the formwork, pouring with shrinkage-compensating concrete, curing and the perimeter backfill. Measured by the area of widening actually constructed.",

"Concreto pobre de limpieza bajo fundación, de 5 cm. Incluye el vaciado y el nivelado. Medido por metro cuadrado ejecutado.":
    "Mud slab beneath a footing, 5 cm thick. Includes pouring and leveling. Measured per square meter constructed.",
"Concreto para zapata combinada. Incluye el vaciado y el vibrado. Medido por metro cúbico ejecutado.":
    "Concrete for a combined footing. Includes pouring and vibrating. Measured per cubic meter constructed.",
"Concreto para zapata de medianería. Incluye el vaciado y el vibrado. Medido por metro cúbico ejecutado.":
    "Concrete for a party wall footing. Includes pouring and vibrating. Measured per cubic meter constructed.",
"Suministro y colocación de acero de refuerzo en zapata. Incluye el corte, el doblado y la colocación. Medido por kilogramo colocado.":
    "Supply and placing of reinforcing steel to a footing. Includes cutting, bending and placing. Measured per kilogram placed.",
"Encofrado y desencofrado de zapata. Incluye el montaje y el desmontaje. Medido por metro cuadrado encofrado.":
    "Formwork and stripping of a footing. Includes erection and dismantling. Measured per square meter formed.",
"Concreto para base o dado de equipo. Incluye el vaciado y el vibrado. Medido por metro cúbico ejecutado.":
    "Concrete for an equipment plinth or base. Includes pouring and vibrating. Measured per cubic meter constructed.",
"Recalce de zapata existente con concreto. Incluye el saneo y el vaciado. Medido por metro cúbico ejecutado.":
    "Underpinning of an existing footing with concrete. Includes cutting out and pouring. Measured per cubic meter constructed.",
"Refuerzo de zapata existente con acero de refuerzo. Incluye el anclaje y la colocación. Medido por kilogramo colocado.":
    "Strengthening of an existing footing with reinforcing steel. Includes anchoring and placing. Measured per kilogram placed.",
"Concreto para pedestal de concreto armado. Incluye el vaciado y el vibrado. Medido por metro cúbico ejecutado.":
    "Concrete for a reinforced concrete pedestal. Includes pouring and vibrating. Measured per cubic meter constructed.",

# ── Vigas de riostra y de fundación ───────────────────────────────────────
"Suministro, corte, doblado, armado y colocación de acero de refuerzo en cabillas corrugadas en vigas de riostra, según los planos de despiece. El armado de viga exige más tiempo por kilogramo que el de zapata por el montaje de los estribos y por el trabajo en zanja estrecha. Incluye el corte y doblado de barras y estribos, el armado de la canasta con la separación de estribos indicada y su reducción en las zonas de confinamiento junto a los apoyos, el amarre con alambre, la colocación de separadores por las cuatro caras, el anclaje o solape con las esperas de las zapatas y la revisión del despiece antes del vaciado. Medido en peso de acero realmente colocado.":
    "Supply, cutting, bending, assembly and placing of deformed bar reinforcement to tie beams, to the bending schedules. Beam reinforcement takes longer per kilogram than footing reinforcement because of the stirrups and the work in a narrow trench. Includes cutting and bending the bars and stirrups, assembling the cage at the stirrup spacing indicated and closing it up in the confinement zones next to the bearings, tying with wire, placing spacers on all four faces, anchoring or lapping with the starter bars from the footings and checking the schedule before the pour. Measured by the weight of steel actually placed.",

"Encofrado de las caras laterales de viga de riostra mediante paneles de madera con puntales y arriostramientos, y su posterior desencofrado. Incluye el replanteo y montaje de los paneles, la comprobación de alineación, plomo y sección antes del vaciado, el arriostramiento que impide la apertura por el empuje del concreto, la aplicación de desmoldeante, el desencofrado una vez alcanzada la resistencia necesaria y la limpieza y acopio de los paneles para su reutilización. Medido en superficie de encofrado en contacto con el concreto.":
    "Formwork to the sides of a tie beam using wood panels with shores and bracing, and its subsequent stripping. Includes setting out and erecting the panels, checking the alignment, plumb and section before the pour, the bracing that stops it opening under the thrust of the concrete, applying release agent, stripping once the necessary strength has been reached and cleaning and stacking the panels for reuse. Measured by the area of formwork in contact with the concrete.",

"Concreto premezclado de resistencia 210 kg/cm2 vaciado en viga de riostra, incluida su compactación por vibrado y su curado. La viga de riostra ata las fundaciones entre sí y es la que absorbe los asientos diferenciales, por lo que su continuidad y la correcta ejecución de los nudos con las zapatas son determinantes. Incluye la revisión previa del armado y del recubrimiento, la recepción del concreto, el vaciado continuo evitando juntas frías en los nudos, la compactación con vibrador de aguja, el reglado de la cara superior y el curado. Medido en volumen teórico según las dimensiones de proyecto.":
    "Ready-mixed concrete of 210 kg/cm² strength poured into a tie beam, including compaction by vibration and curing. The tie beam ties the footings together and is what absorbs differential settlement, so its continuity and the correct execution of the joints with the footings are decisive. Includes the prior check of the cage and of the cover, taking delivery of the concrete, pouring continuously to avoid cold joints at the connections, compacting with an internal vibrator, screeding the top face and curing. Measured by the theoretical volume to the design dimensions.",

"Suministro y colocación de acero de refuerzo en viga de riostra. Incluye el corte, el doblado y la colocación. Medido por kilogramo colocado.":
    "Supply and placing of reinforcing steel to a tie beam. Includes cutting, bending and placing. Measured per kilogram placed.",
"Encofrado y desencofrado de viga de riostra. Incluye el montaje y el desmontaje. Medido por metro cuadrado encofrado.":
    "Formwork and stripping of a tie beam. Includes erection and dismantling. Measured per square meter formed.",
"Concreto para viga de riostra. Incluye el vaciado y el vibrado. Medido por metro cúbico ejecutado.":
    "Concrete for a tie beam. Includes pouring and vibrating. Measured per cubic meter constructed.",
"Concreto para viga de fundación. Incluye el vaciado y el vibrado. Medido por metro cúbico ejecutado.":
    "Concrete for a grade beam. Includes pouring and vibrating. Measured per cubic meter constructed.",
"Suministro y colocación de acero de refuerzo en viga de fundación. Incluye el corte y la colocación. Medido por kilogramo colocado.":
    "Supply and placing of reinforcing steel to a grade beam. Includes cutting and placing. Measured per kilogram placed.",
"Ejecución de viga de riostra con bloque lateral como encofrado perdido. Incluye la colocación del bloque y el vaciado. Medido por metro lineal ejecutado.":
    "Construction of a tie beam using a side block as permanent formwork. Includes laying the block and pouring. Measured per meter constructed.",
"Ejecución de viga de fundación sobre suelo mejorado. Incluye el vaciado y el vibrado. Medido por metro lineal ejecutado.":
    "Construction of a grade beam on improved ground. Includes pouring and vibrating. Measured per meter constructed.",
"Encofrado y desencofrado de viga de fundación. Incluye el montaje y el desmontaje. Medido por metro cuadrado encofrado.":
    "Formwork and stripping of a grade beam. Includes erection and dismantling. Measured per square meter formed.",
"Concreto para viga de amarre. Incluye el vaciado y el vibrado. Medido por metro cúbico ejecutado.":
    "Concrete for a tie beam. Includes pouring and vibrating. Measured per cubic meter constructed.",
"Ejecución de viga de riostra con junta de dilatación. Incluye el vaciado y la formación de la junta. Medido por metro lineal ejecutado.":
    "Construction of a tie beam with an expansion joint. Includes pouring and forming the joint. Measured per meter constructed.",

# ── Losa de fundación ─────────────────────────────────────────────────────
"Colocación de lámina de polietileno de alta densidad sobre la base compactada, como barrera de vapor que impide el ascenso capilar de humedad desde el terreno hacia la losa y el piso terminado. Es una capa barata cuya omisión provoca humedades permanentes en el piso, imposibles de corregir después sin demoler. Incluye la comprobación de que la base no presenta aristas que puedan perforar la lámina, el extendido con solapes de 20 cm sellados con cinta, el remonte en el perímetro hasta la cota superior de la losa y la reparación de cualquier perforación producida durante el armado. Medido en superficie realmente cubierta.":
    "Laying a high density polyethylene sheet over the compacted base as a vapour barrier, to stop the capillary rise of moisture from the ground into the slab and the finished floor. It is a cheap layer whose omission causes permanent damp in the floor that cannot afterwards be put right without demolition. Includes checking that the base presents no arrises that could puncture the sheet, laying it with 20 cm laps sealed with tape, turning it up at the perimeter to the top of the slab and repairing any puncture made while the reinforcement is being placed. Measured by the area actually covered.",

"Suministro, corte, doblado, armado y colocación de acero de refuerzo en cabillas corrugadas en losa de fundación, en parrillas inferior y superior según los planos de despiece. Incluye el corte y doblado, el armado de las parrillas con amarre de alambre, la colocación de separadores inferiores y de caballetes o soportes que mantienen la parrilla superior en su cota durante el vaciado, los refuerzos de borde y de esquina, y la revisión del despiece y del recubrimiento antes de autorizar el concreto. Medido en peso de acero realmente colocado.":
    "Supply, cutting, bending, assembly and placing of deformed bar reinforcement to a mat foundation, in top and bottom mats to the bending schedules. Includes cutting and bending, assembling the mats with wire ties, placing bottom spacers and the chairs or supports that hold the top mat at its level during the pour, the edge and corner reinforcement, and checking the schedule and the cover before the concrete is authorized. Measured by the weight of steel actually placed.",

"Suministro y colocación de malla electrosoldada de acero como refuerzo de losa, sobre separadores que garantizan su posición dentro del espesor. Incluye el replanteo, el corte de los paños, su colocación con los solapes mínimos de dos retículas amarrados con alambre, la colocación de separadores y caballetes, y el repaso de la posición de la malla inmediatamente antes del vaciado, ya que es habitual que quede pisada y apoyada en el fondo, con lo que pierde por completo su función. Medido en superficie realmente reforzada.":
    "Supply and placing of welded wire mesh as slab reinforcement, on spacers that hold it in position within the depth. Includes setting out, cutting the sheets, laying them with a minimum lap of two grids tied with wire, placing the spacers and chairs, and going over the position of the mesh immediately before the pour, since it is common for it to be trodden down onto the bottom, with which it loses its function entirely. Measured by the area actually reinforced.",

"Encofrado del borde perimetral de losa de fundación mediante tablones de madera con estacas y arriostramiento, y su posterior desencofrado. Incluye el replanteo del perímetro, el montaje de los tablones a la cota exacta de la cara superior de la losa, su fijación y arriostramiento contra el empuje del concreto, la aplicación de desmoldeante, el desencofrado y la limpieza y acopio del material. Medido en superficie de encofrado en contacto con el concreto.":
    "Formwork to the perimeter edge of a mat foundation using wood boards with stakes and bracing, and its subsequent stripping. Includes setting out the perimeter, erecting the boards to the exact level of the top of the slab, fixing and bracing them against the thrust of the concrete, applying release agent, stripping and cleaning and stacking the material. Measured by the area of formwork in contact with the concrete.",

"Concreto premezclado de resistencia 250 kg/cm2 vaciado en losa de fundación, incluida su compactación por vibrado. Incluye la revisión previa del armado, de los separadores y de la barrera de vapor, la recepción y comprobación del concreto, el vaciado continuo por franjas evitando las juntas frías, la compactación con vibrador de aguja, el reglado a la cota mediante maestras y el sangrado del agua de exudación antes del acabado. No incluye el acabado superficial ni el curado, que se valoran en la partida siguiente. Medido en volumen teórico según las dimensiones de proyecto.":
    "Ready-mixed concrete of 250 kg/cm² strength poured into a mat foundation, including compaction by vibration. Includes the prior check of the cage, of the spacers and of the vapour barrier, taking delivery of and checking the concrete, pouring continuously in bays avoiding cold joints, compacting with an internal vibrator, screeding to level against screed rails and removing the bleed water before finishing. It does not include the surface finish or the curing, which are priced in the following item. Measured by the theoretical volume to the design dimensions.",

"Acabado superficial de la losa mediante alisado mecánico y su curado posterior. Incluye el reglado y flotado inicial, el alisado con alisadora mecánica en las pasadas necesarias hasta obtener la textura requerida según vaya a recibir un piso adherido o quedar visto, el aserrado de las juntas de retracción en el momento adecuado, y el curado mediante curador de membrana o riego continuo durante los primeros días, sin el cual la losa fisura por retracción plástica por muy bien vaciada que esté. Medido en superficie realmente acabada.":
    "Surface finish of the slab by power troweling and its subsequent curing. Includes the initial screeding and floating, power troweling in as many passes as are needed to obtain the texture required according to whether it is to receive an adhered floor or to be left exposed, saw cutting the shrinkage joints at the right moment, and curing with a curing membrane or continuous watering over the first few days, without which the slab cracks by plastic shrinkage however well it has been poured. Measured by the area actually finished.",

"Colocación de barrera de vapor de polietileno bajo losa. Incluye la extensión y el solape. Medido por metro cuadrado colocado.":
    "Laying a polyethylene vapour barrier beneath the slab. Includes spreading and the laps. Measured per square meter installed.",
"Colocación de aislamiento térmico bajo losa de fundación. Incluye la colocación del panel. Medido por metro cuadrado colocado.":
    "Laying thermal insulation beneath a mat foundation. Includes laying the boards. Measured per square meter installed.",
"Suministro y colocación de acero de refuerzo en losa de fundación. Incluye el corte y la colocación. Medido por kilogramo colocado.":
    "Supply and placing of reinforcing steel to a mat foundation. Includes cutting and placing. Measured per kilogram placed.",
"Encofrado perimetral de losa de fundación. Incluye el montaje y el desmontaje. Medido por metro lineal encofrado.":
    "Perimeter formwork to a mat foundation. Includes erection and dismantling. Measured per meter formed.",
"Concreto para losa de fundación. Incluye el vaciado y el vibrado. Medido por metro cúbico ejecutado.":
    "Concrete for a mat foundation. Includes pouring and vibrating. Measured per cubic meter constructed.",
"Acabado y curado de losa de fundación. Incluye el alisado y el curado. Medido por metro cuadrado ejecutado.":
    "Finishing and curing of a mat foundation. Includes troweling and curing. Measured per square meter constructed.",
"Ejecución de losa de fundación aligerada con anime de poliestireno. Incluye el aligeramiento y el vaciado. Medido por metro cuadrado ejecutado.":
    "Construction of a mat foundation lightweightened with polystyrene void formers. Includes the void formers and pouring. Measured per square meter constructed.",
"Ejecución de junta de dilatación en losa de fundación. Incluye la formación de la junta. Medido por metro lineal ejecutado.":
    "Formation of an expansion joint in a mat foundation. Includes forming the joint. Measured per meter constructed.",
"Ejecución de losa de fundación con aditivo impermeabilizante. Incluye el vaciado con el aditivo. Medido por metro cuadrado ejecutado.":
    "Construction of a mat foundation with a waterproofing admixture. Includes pouring with the admixture. Measured per square meter constructed.",

# ── Muros de contención ───────────────────────────────────────────────────
"Encofrado a dos caras de muro de contención mediante paneles de madera con sus tirantes pasantes, puntales y arriostramientos, y su posterior desencofrado. Incluye el replanteo, el montaje y aplomado de la primera cara, la colocación de los tirantes y separadores que fijan el espesor, el cierre de la segunda cara tras la revisión del armado, el arriostramiento frente al empuje del concreto fresco que en un muro alto es considerable, la aplicación de desmoldeante, el desencofrado y el sellado de los agujeros de los tirantes. Medido en superficie de encofrado en contacto con el concreto, contando ambas caras.":
    "Double faced formwork to a retaining wall using wood panels with through ties, shores and bracing, and its subsequent stripping. Includes setting out, erecting and plumbing the first face, placing the ties and spacers that fix the thickness, closing the second face after the cage has been checked, bracing against the thrust of the wet concrete, which on a tall wall is considerable, applying release agent, stripping and making good the tie holes. Measured by the area of formwork in contact with the concrete, counting both faces.",

"Suministro, corte, doblado, armado y colocación de acero de refuerzo en cabillas corrugadas en muro de contención, según los planos de despiece. Incluye el corte y doblado, el armado de las dos parrillas verticales con sus ganchos de arranque solapados a las esperas de la fundación, el amarre con alambre, la colocación de separadores en ambas caras para garantizar el recubrimiento, los refuerzos de borde y de esquina, y la comprobación de que la parrilla del lado del terreno queda en la cara traccionada correcta, error frecuente y de consecuencias graves. Medido en peso de acero realmente colocado.":
    "Supply, cutting, bending, assembly and placing of deformed bar reinforcement to a retaining wall, to the bending schedules. Includes cutting and bending, assembling the two vertical mats with their starter hooks lapped to the starter bars from the footing, tying with wire, placing spacers on both faces to give the cover, the edge and corner reinforcement, and checking that the mat on the earth side falls on the correct tension face, a frequent error with serious consequences. Measured by the weight of steel actually placed.",

"Concreto premezclado de resistencia 250 kg/cm2 vaciado en muro de contención, incluida su compactación por vibrado y su curado. Incluye la revisión previa del armado, del encofrado y de los recubrimientos, la recepción del concreto, el vaciado por capas de altura limitada y por puntos alternos para no descuadrar el encofrado, el uso de tubo de descarga cuando la altura de caída pueda provocar segregación, la compactación con vibrador de aguja en cada capa, el curado prolongado y el desencofrado una vez alcanzada la resistencia. Medido en volumen teórico según las dimensiones de proyecto.":
    "Ready-mixed concrete of 250 kg/cm² strength poured into a retaining wall, including compaction by vibration and curing. Includes the prior check of the cage, of the formwork and of the cover, taking delivery of the concrete, pouring in layers of limited height and at alternate points so as not to rack the formwork, using a drop chute where the height of fall could cause segregation, compacting each layer with an internal vibrator, extended curing and stripping once the strength has been reached. Measured by the theoretical volume to the design dimensions.",

"Impermeabilización de la cara del muro en contacto con el terreno mediante imprimación y dos manos de emulsión asfáltica, con protección posterior. Es la única oportunidad de ejecutarla: una vez rellenado el trasdós, corregir una filtración obliga a excavar de nuevo. Incluye la limpieza y el repaso de la superficie con eliminación de rebabas y coqueras, la reparación de los agujeros de los tirantes del encofrado, la aplicación de la imprimación, las dos manos de emulsión asfáltica con especial cuidado en el encuentro con la fundación, y la colocación de la lámina de protección antes del relleno. Medido en superficie realmente impermeabilizada.":
    "Waterproofing of the face of the wall in contact with the ground with a primer and two coats of bitumen emulsion, with protection afterwards. It is the only opportunity to do it: once the rear face has been backfilled, correcting a leak means excavating again. Includes cleaning and going over the surface with the removal of fins and honeycombing, making good the formwork tie holes, applying the primer, the two coats of bitumen emulsion with particular care at the junction with the footing, and placing the protection board before backfilling. Measured by the area actually waterproofed.",

"Drenaje longitudinal en la base del trasdós del muro, formado por tubería corrugada perforada envuelta en geotextil y capa de piedra picada de relleno drenante, con salida a punto de evacuación. Su función es eliminar el empuje hidrostático sobre el muro, que es la causa más común del fallo de los muros de contención, mucho más que el empuje de tierras. Incluye la formación del asiento con pendiente hacia la salida, la colocación del geotextil envolvente, el tendido de la tubería, el relleno con piedra picada, el cierre del geotextil y la conexión a la salida de evacuación. Medido en longitud realmente ejecutada.":
    "Longitudinal drainage at the base of the rear face of the wall, of perforated corrugated pipe wrapped in geotextile and a layer of crushed stone as free draining fill, discharging to an outlet. Its function is to remove the hydrostatic pressure on the wall, which is the most common cause of failure in retaining walls, far more so than earth pressure. Includes forming the bearing with a fall to the outlet, laying the wrapping geotextile, laying the pipe, backfilling with crushed stone, closing the geotextile and connecting to the outlet. Measured by the length actually constructed.",

"Encofrado a dos caras de muro de contención. Incluye el montaje y el desmontaje. Medido por metro cuadrado encofrado.":
    "Double faced formwork to a retaining wall. Includes erection and dismantling. Measured per square meter formed.",
"Suministro y colocación de acero de refuerzo en muro de contención. Incluye el corte y la colocación. Medido por kilogramo colocado.":
    "Supply and placing of reinforcing steel to a retaining wall. Includes cutting and placing. Measured per kilogram placed.",
"Concreto para muro de contención. Incluye el vaciado y el vibrado. Medido por metro cúbico ejecutado.":
    "Concrete for a retaining wall. Includes pouring and vibrating. Measured per cubic meter constructed.",
"Impermeabilización del trasdós de muro de contención. Incluye la aplicación de la membrana. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of the rear face of a retaining wall. Includes applying the membrane. Measured per square meter waterproofed.",
"Drenaje de trasdós de muro con tubería y grava. Incluye la tubería y el relleno de grava. Medido por metro lineal ejecutado.":
    "Drainage to the rear face of a wall with pipe and gravel. Includes the pipe and the gravel backfill. Measured per meter constructed.",
"Ejecución de muro de contención con acabado visto. Incluye el vaciado y el acabado. Medido por metro cuadrado ejecutado.":
    "Construction of a retaining wall with an exposed finish. Includes pouring and finishing. Measured per square meter constructed.",
"Ejecución de muro de contención de bloque de concreto con refuerzo. Incluye la mampostería, el refuerzo y el relleno. Medido por metro cuadrado ejecutado.":
    "Construction of a reinforced concrete block retaining wall. Includes the masonry, the reinforcement and the fill. Measured per square meter constructed.",
"Ejecución de muro de contención con junta de dilatación. Incluye el vaciado y la formación de la junta. Medido por metro lineal ejecutado.":
    "Construction of a retaining wall with an expansion joint. Includes pouring and forming the joint. Measured per meter constructed.",
"Reparación de muro de contención con mortero de reparación. Incluye el saneo y la reparación. Medido por metro cuadrado reparado.":
    "Repair of a retaining wall with a repair mortar. Includes cutting out and repair. Measured per square meter repaired.",
"Refuerzo de muro de contención existente. Incluye el refuerzo y el recubrimiento. Medido por metro cuadrado reforzado.":
    "Strengthening of an existing retaining wall. Includes the strengthening and the cover. Measured per square meter strengthened.",

# ── Pilotes ───────────────────────────────────────────────────────────────
"Perforación rotatoria para pilote vaciado en sitio, en terreno de consistencia media, con equipo de perforación y su operador. Incluye el traslado y emplazamiento del equipo, el replanteo y centrado sobre el eje del pilote, la perforación hasta la cota de proyecto con control de la verticalidad, la extracción y acopio del material perforado, la limpieza del fondo de la perforación antes de introducir el armado y la protección o entubado provisional de la boca para evitar desprendimientos. Medido en longitud realmente perforada.":
    "Rotary drilling for a cast-in-place pile, in ground of medium consistency, with the drilling rig and its operator. Includes moving and positioning the rig, setting out and centring on the axis of the pile, drilling to the design level with the verticality controlled, removing and stockpiling the spoil, cleaning the bottom of the bore before the cage is inserted and protecting or temporarily casing the mouth to prevent collapse. Measured by the length actually drilled.",

"Suministro, corte, doblado, armado y colocación de la canasta de acero de refuerzo del pilote, con sus barras longitudinales y su zuncho helicoidal. Incluye el armado de la canasta en superficie, la colocación de separadores circulares que centran la canasta dentro de la perforación y garantizan el recubrimiento, el izado y descenso controlado de la canasta dentro del pilote sin que roce las paredes y arrastre tierra, su suspensión a la cota correcta durante el vaciado y la disposición de las esperas de conexión con el cabezal. Medido en peso de acero realmente colocado.":
    "Supply, cutting, bending, assembly and placing of the reinforcement cage of the pile, with its longitudinal bars and its helical tie. Includes assembling the cage at the surface, fitting circular spacers that center the cage in the bore and give the cover, hoisting and lowering the cage under control into the pile without it scraping the sides and dragging in soil, suspending it at the correct level during the pour and forming the starter bars for the connection to the pile cap. Measured by the weight of steel actually placed.",

"Concreto premezclado de resistencia 250 kg/cm2 vaciado en pilote perforado, colocado mediante tubo tremie o embudo con tubo de descarga. Incluye la comprobación de la limpieza del fondo y de la posición de la canasta, la recepción del concreto con la fluidez adecuada para un vaciado sin vibrado en toda la profundidad, el vaciado continuo desde el fondo hacia arriba sin interrupciones que provoquen discontinuidades, el control del volumen realmente colocado frente al teórico como indicador de posibles sobreanchos o pérdidas, y el rebose de la cabeza para desalojar el concreto contaminado. Medido en volumen teórico según el diámetro y la longitud de proyecto.":
    "Ready-mixed concrete of 250 kg/cm² strength poured into a bored pile, placed by tremie pipe or hopper with a drop tube. Includes checking that the bottom is clean and that the cage is in position, taking delivery of the concrete at a consistency that allows it to be placed without vibration over the full depth, pouring continuously from the bottom upwards without interruptions that would cause discontinuities, comparing the volume actually placed against the theoretical as an indicator of possible overbreak or losses, and overpouring the head to displace the contaminated concrete. Measured by the theoretical volume to the design diameter and length.",

"Demolición de la cabeza del pilote hasta la cota de proyecto, eliminando el concreto contaminado del rebose, y preparación de las esperas de acero para su conexión con el cabezal o la viga de atado. Incluye el marcado de la cota de corte, la demolición con martillo eléctrico sin dañar las barras de espera ni fisurar el concreto que permanece, el enderezado y limpieza de las esperas, el repicado de la superficie de contacto para dar adherencia al elemento superior y el retiro del escombro. Medido por pilote realmente descabezado.":
    "Breaking down the head of the pile to the design level, removing the concrete contaminated by the overpour, and preparing the starter bars for connection to the pile cap or the capping beam. Includes marking the cut-off level, breaking down with an electric breaker without damaging the starter bars or cracking the concrete that remains, straightening and cleaning the starter bars, hacking the contact surface to give a bond to the element above and removing the debris. Measured per pile actually cut off.",

"Cabezal de concreto armado de resistencia 250 kg/cm2 que recibe y reparte la carga de la columna entre el grupo de pilotes, incluidos su encofrado, su vaciado, su vibrado y su curado. Incluye el replanteo sobre las cabezas descabezadas, el montaje y arriostramiento del encofrado, la comprobación de que las esperas de los pilotes quedan embebidas con la longitud de anclaje prevista, el vaciado por capas con vibrado, el desencofrado y el curado. No incluye el acero de refuerzo, que se valora por su peso. Medido en volumen teórico según las dimensiones de proyecto.":
    "Reinforced concrete pile cap of 250 kg/cm² strength that receives the load of the column and distributes it across the group of piles, including its formwork, pouring, vibration and curing. Includes setting out over the cut-off heads, erecting and bracing the formwork, checking that the starter bars from the piles are embedded with the anchorage length specified, pouring in layers with vibration, stripping and curing. It does not include the reinforcement, which is priced by weight. Measured by the theoretical volume to the design dimensions.",

"Perforación para pilote vaciado en sitio. Incluye la perforación. Medido por metro lineal perforado.":
    "Drilling for a cast-in-place pile. Includes drilling. Measured per meter drilled.",
"Suministro y colocación de acero de refuerzo en pilote. Incluye el corte y la colocación. Medido por kilogramo colocado.":
    "Supply and placing of reinforcing steel to a pile. Includes cutting and placing. Measured per kilogram placed.",
"Concreto para pilote vaciado en sitio. Incluye el vaciado. Medido por metro cúbico ejecutado.":
    "Concrete for a cast-in-place pile. Includes pouring. Measured per cubic meter constructed.",
"Descabezado de pilote de concreto. Incluye el corte del acero y el descabezado. Medido por unidad descabezada.":
    "Cutting off the head of a concrete pile. Includes cutting the steel and breaking down the head. Measured per unit cut off.",
"Concreto para cabezal de pilotes. Incluye el vaciado y el vibrado. Medido por metro cúbico ejecutado.":
    "Concrete for a pile cap. Includes pouring and vibrating. Measured per cubic meter constructed.",
"Suministro y colocación de acero de refuerzo en cabezal de pilotes. Incluye el corte y la colocación. Medido por kilogramo colocado.":
    "Supply and placing of reinforcing steel to a pile cap. Includes cutting and placing. Measured per kilogram placed.",
"Encofrado y desencofrado de cabezal de pilotes. Incluye el montaje y el desmontaje. Medido por metro cuadrado encofrado.":
    "Formwork and stripping of a pile cap. Includes erection and dismantling. Measured per square meter formed.",
"Concreto para pilote de gran sección. Incluye el vaciado. Medido por metro cúbico ejecutado.":
    "Concrete for a large diameter pile. Includes pouring. Measured per cubic meter constructed.",
"Ejecución de pilote con camisa metálica recuperable. Incluye la camisa y el vaciado. Medido por metro cuadrado ejecutado.":
    "Construction of a pile with a recoverable steel casing. Includes the casing and pouring. Measured per square meter constructed.",
"Concreto para pila o elemento de fundación profunda. Incluye el vaciado. Medido por metro cúbico ejecutado.":
    "Concrete for a pier or deep foundation element. Includes pouring. Measured per cubic meter constructed.",

# ── Drenaje e impermeabilización ──────────────────────────────────────────
"Ejecución de drenaje perimetral de fundación con tubería perforada. Incluye la tubería y el relleno de grava. Medido por metro lineal ejecutado.":
    "Construction of perimeter drainage to the footing with perforated pipe. Includes the pipe and the gravel backfill. Measured per meter constructed.",
"Drenaje con canaleta prefabricada en fundación. Incluye la colocación de la canaleta. Medido por metro lineal ejecutado.":
    "Drainage with a precast channel at the footing. Includes laying the channel. Measured per meter constructed.",
"Impermeabilización de fundación con manto asfáltico. Incluye la imprimación y el manto. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a footing with a bituminous membrane. Includes the primer and the membrane. Measured per square meter waterproofed.",
"Colocación de lámina drenante sobre impermeabilización de fundación. Incluye la colocación de la lámina. Medido por metro cuadrado colocado.":
    "Installation of a drainage membrane over the waterproofing of a footing. Includes laying the membrane. Measured per square meter installed.",
"Impermeabilización de fundación con geocompuesto de bentonita. Incluye la colocación. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a footing with a bentonite geocomposite. Includes installation. Measured per square meter waterproofed.",
"Impermeabilización de fundación con membrana cementosa flexible. Incluye la aplicación. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a footing with a flexible cementitious membrane. Includes application. Measured per square meter waterproofed.",
"Protección de fundación contra raíces con barrera. Incluye la colocación de la barrera. Medido por metro cuadrado colocado.":
    "Protection of a footing against roots with a barrier. Includes laying the barrier. Measured per square meter installed.",
"Impermeabilización de losa de fundación. Incluye la aplicación de la membrana. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a mat foundation. Includes applying the membrane. Measured per square meter waterproofed.",

# ── Reparación y refuerzo ─────────────────────────────────────────────────
"Reparación de fundación con mortero de reparación estructural. Incluye el saneo y la reparación. Medido por metro cuadrado reparado.":
    "Repair of a footing with a structural repair mortar. Includes cutting out and repair. Measured per square meter repaired.",
"Reparación de fisuras en fundación con inyección de resina. Incluye la inyección. Medido por metro lineal reparado.":
    "Repair of cracks in a footing by resin injection. Includes injection. Measured per meter repaired.",
"Refuerzo de fundación con encamisado de concreto. Incluye el armado y el vaciado. Medido por metro cuadrado reforzado.":
    "Strengthening of a footing with concrete jacketing. Includes reinforcement and pouring. Measured per square meter strengthened.",
"Refuerzo de fundación con lámina de fibra de carbono. Incluye la aplicación. Medido por metro cuadrado reforzado.":
    "Strengthening of a footing with a carbon fiber plate. Includes application. Measured per square meter strengthened.",
"Refuerzo de zapata existente con ampliación de concreto. Incluye el armado y el vaciado. Medido por metro cuadrado reforzado.":
    "Strengthening of an existing footing with a concrete widening. Includes reinforcement and pouring. Measured per square meter strengthened.",
"Refuerzo de fundación con micropilotes. Incluye la perforación y el vaciado. Medido por metro lineal reforzado.":
    "Strengthening of a footing with micropiles. Includes drilling and pouring. Measured per meter strengthened.",
"Refuerzo de fundación con mortero de alta resistencia. Incluye la aplicación. Medido por metro cuadrado reforzado.":
    "Strengthening of a footing with a high strength mortar. Includes application. Measured per square meter strengthened.",
"Refuerzo de fundación con recalce escalonado. Incluye la excavación y el vaciado. Medido por metro cuadrado reforzado.":
    "Strengthening of a footing by staged underpinning. Includes excavation and pouring. Measured per square meter strengthened.",
}
