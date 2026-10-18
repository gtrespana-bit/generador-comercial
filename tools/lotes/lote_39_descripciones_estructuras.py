# -*- coding: utf-8 -*-
"""Descripciones — Estructuras (capítulo completo, 170).

Criterios de este lote:
  · «Encofrado» es formwork y «desencofrado» es stripping. La «cimbra» y
    el «apuntalamiento» son falsework y shoring en los Estados Unidos,
    falsework y propping en el Reino Unido.
  · «Cabilla corrugada» es deformed bar, no corrugated bar: lo segundo
    es un falso amigo que en inglés nombra a la chapa ondulada.
  · Los «estribos» son stirrups en los Estados Unidos y links en el Reino
    Unido, y los planos de despiece son los bending schedules.
  · «Desapuntalamiento» es removal of the shoring, y en el Reino Unido
    se dice de-propping; no es «desformwork» ni nada parecido.
  · «Vibrador de aguja» es internal vibrator en los Estados Unidos y
    poker vibrator en el Reino Unido. La «junta fría» es cold joint.
  · «Losa nervada» es ribbed slab y los bloques de aliviano son void
    formers. La «loseta de compresión» es structural topping.
  · «Lámina colaborante» es metal deck. Los «conectores de cortante»
    son shear studs.
  · «Enamisado» de una columna es jacketing, y la «contraflecha» es camber.
  · «Coqueras» es honeycombing y «carbonatación» es carbonation.
"""

LOTE = {
# ── Encofrados: descripciones cortas ──────────────────────────────────────
"Encofrado y desencofrado de columna de concreto con madera. Incluye el montaje, el desencofrado y la limpieza. Medido por metro cuadrado encofrado.":
    "Formwork and stripping of a concrete column in lumber. Includes erection, stripping and cleaning. Measured per square meter formed.",
"Encofrado y desencofrado de viga de concreto con madera. Incluye el montaje y el desencofrado. Medido por metro cuadrado encofrado.":
    "Formwork and stripping of a concrete beam in lumber. Includes erection and stripping. Measured per square meter formed.",
"Encofrado de losa maciza sobre puntales con madera. Incluye el montaje de puntales y tablero. Medido por metro cuadrado encofrado.":
    "Formwork to a solid slab on shores in lumber. Includes erecting the shores and the decking. Measured per square meter formed.",
"Encofrado y desencofrado de escalera de concreto con madera. Incluye el montaje del encofrado de huellas y contrahuellas. Medido por metro cuadrado encofrado.":
    "Formwork and stripping of a concrete stair in lumber. Includes erecting the formwork to the treads and risers. Measured per square meter formed.",
"Encofrado a dos caras de muro de concreto con madera. Incluye el montaje y el desencofrado. Medido por metro cuadrado encofrado.":
    "Double faced formwork to a concrete wall in lumber. Includes erection and stripping. Measured per square meter formed.",
"Encofrado de borde de losa de concreto. Incluye el montaje del encofrado lateral. Medido por metro lineal encofrado.":
    "Edge formwork to a concrete slab. Includes erecting the side formwork. Measured per meter formed.",
"Encofrado metálico modular de columna. Incluye el montaje, el desencofrado y la limpieza. Medido por metro cuadrado encofrado.":
    "Modular steel formwork to a column. Includes erection, stripping and cleaning. Measured per square meter formed.",
"Encofrado metálico modular de muro. Incluye el montaje y el desencofrado. Medido por metro cuadrado encofrado.":
    "Modular steel formwork to a wall. Includes erection and stripping. Measured per square meter formed.",
"Encofrado de losa con sistema modular de puntales y tablero metálico. Incluye el montaje del sistema. Medido por metro cuadrado encofrado.":
    "Formwork to a slab with a modular system of shores and steel decking. Includes erecting the system. Measured per square meter formed.",
"Cimbra y apuntalamiento de losa durante el vaciado. Incluye la colocación de puntales. Medido por metro cuadrado apuntalado.":
    "Falsework and shoring of a slab during the pour. Includes placing the shores. Measured per square meter shored.",
"Apeo y soporte de encofrado de viga. Incluye la colocación de puntales. Medido por metro cuadrado apeado.":
    "Shoring and support to the formwork of a beam. Includes placing the shores. Measured per square meter shored.",

# ── Armadura: descripciones cortas ────────────────────────────────────────
"Suministro y colocación de acero de refuerzo en columnas. Incluye el corte, el doblado y la colocación. Medido por kilogramo colocado.":
    "Supply and placing of reinforcing steel to columns. Includes cutting, bending and placing. Measured per kilogram placed.",
"Suministro y colocación de acero de refuerzo en vigas. Incluye el corte y la colocación. Medido por kilogramo colocado.":
    "Supply and placing of reinforcing steel to beams. Includes cutting and placing. Measured per kilogram placed.",
"Suministro y colocación de acero de refuerzo en losas. Incluye el corte y la colocación. Medido por kilogramo colocado.":
    "Supply and placing of reinforcing steel to slabs. Includes cutting and placing. Measured per kilogram placed.",
"Suministro y colocación de acero de refuerzo en escalera. Incluye el corte y la colocación. Medido por kilogramo colocado.":
    "Supply and placing of reinforcing steel to a stair. Includes cutting and placing. Measured per kilogram placed.",
"Suministro y colocación de acero de refuerzo en muros. Incluye el corte y la colocación. Medido por kilogramo colocado.":
    "Supply and placing of reinforcing steel to walls. Includes cutting and placing. Measured per kilogram placed.",
"Suministro y colocación de acero de refuerzo en vigas de amarre. Incluye el corte y la colocación. Medido por kilogramo colocado.":
    "Supply and placing of reinforcing steel to tie beams. Includes cutting and placing. Measured per kilogram placed.",
"Colocación de malla electrosoldada de refuerzo en losa. Incluye la colocación y el solape. Medido por metro cuadrado colocado.":
    "Placing welded wire mesh reinforcement to a slab. Includes placing and the laps. Measured per square meter placed.",
"Colocación de malla electrosoldada de refuerzo en muro. Incluye la colocación y el solape. Medido por metro cuadrado colocado.":
    "Placing welded wire mesh reinforcement to a wall. Includes placing and the laps. Measured per square meter placed.",
"Suministro y colocación de acero de refuerzo en pantalla o muro estructural. Incluye el corte y la colocación. Medido por kilogramo colocado.":
    "Supply and placing of reinforcing steel to a structural wall. Includes cutting and placing. Measured per kilogram placed.",
"Suministro y colocación de acero de refuerzo en dintel. Incluye el corte y la colocación. Medido por kilogramo colocado.":
    "Supply and placing of reinforcing steel to a lintel. Includes cutting and placing. Measured per kilogram placed.",
"Suministro y colocación de acero de refuerzo en viga de corona. Incluye el corte y la colocación. Medido por kilogramo colocado.":
    "Supply and placing of reinforcing steel to a ring beam. Includes cutting and placing. Measured per kilogram placed.",

# ── Concreto armado: pormenorizadas ───────────────────────────────────────
"Suministro, corte, doblado, armado y colocación de acero de refuerzo en cabillas corrugadas de límite elástico 4.200 kg/cm2 en columnas, según los planos de despiece. El rendimiento por kilogramo es de los más bajos del acero de obra por el trabajo en vertical y por la cantidad de estribos. Incluye el corte y doblado de barras y estribos, el armado de la canasta con la separación de estribos indicada y su reducción en las zonas de confinamiento de los extremos, el amarre con alambre en todos los cruces, el solape con las esperas de la fundación o del nivel inferior respetando la longitud prevista, la colocación de separadores en las cuatro caras y el aplomado y arriostramiento del armado antes del encofrado. Medido en peso de acero realmente colocado.":
    "Supply, cutting, bending, assembly and placing of deformed bar reinforcement of 4,200 kg/cm² yield strength to columns, to the bending schedules. Output per kilogram is among the lowest of any reinforcement on site because of the vertical work and the number of stirrups. Includes cutting and bending the bars and stirrups, assembling the cage at the stirrup spacing indicated and closing it up in the confinement zones at the ends, tying with wire at every intersection, lapping with the starter bars from the footing or the level below at the specified lap length, placing spacers on all four faces and plumbing and bracing the cage before the formwork. Measured by the weight of steel actually placed.",

"Encofrado de columna mediante paneles de madera con abrazaderas, puntales y arriostramiento, y su posterior desencofrado. Incluye el replanteo sobre el nivel, el montaje de los paneles alrededor del armado, el aplomado en las dos direcciones y su arriostramiento, la comprobación de la escuadría y del recubrimiento, la aplicación de desmoldeante, la previsión de la ventana de limpieza en la base, el desencofrado una vez alcanzada la resistencia y la limpieza y acopio de los paneles para su reutilización. Medido en superficie de encofrado en contacto con el concreto.":
    "Formwork to a column using lumber panels with clamps, shores and bracing, and its subsequent stripping. Includes setting out from the level, erecting the panels around the cage, plumbing in both directions and bracing, checking the section size and the cover, applying release agent, providing a clean-out opening at the base, stripping once the strength has been reached and cleaning and stacking the panels for reuse. Measured by the area of formwork in contact with the concrete.",

"Concreto premezclado de resistencia 250 kg/cm2 vaciado en columna, incluida su compactación por vibrado y su curado. Incluye la limpieza del fondo del encofrado por la ventana prevista antes de cerrarla, la recepción y comprobación del concreto, el vaciado por capas de altura limitada empleando tubo de descarga para evitar la segregación por caída libre, la compactación con vibrador de aguja en cada capa sin tocar el armado, el enrase de la cabeza dejando la superficie rugosa para la junta con la viga superior, el desencofrado y el curado. Medido en volumen teórico según las dimensiones de proyecto.":
    "Ready-mixed concrete of 250 kg/cm² strength poured into a column, including compaction by vibration and curing. Includes cleaning the bottom of the formwork through the opening provided before closing it, taking delivery of and checking the concrete, pouring in layers of limited height using a drop chute to avoid segregation from free fall, compacting each layer with an internal vibrator without touching the cage, striking off the head and leaving the surface rough for the joint with the beam above, stripping and curing. Measured by the theoretical volume to the design dimensions.",

"Suministro, corte, doblado, armado y colocación de acero de refuerzo en cabillas corrugadas en vigas, según los planos de despiece. Incluye el corte y doblado de barras y estribos, el armado de la canasta con la separación de estribos indicada y su reducción en las zonas de confinamiento junto a los apoyos, la disposición del refuerzo superior sobre los apoyos y del inferior en el centro del vano conforme al diagrama de momentos, el amarre con alambre, la colocación de separadores, el anclaje en los nudos con las columnas y la revisión del despiece antes de autorizar el vaciado. Medido en peso de acero realmente colocado.":
    "Supply, cutting, bending, assembly and placing of deformed bar reinforcement to beams, to the bending schedules. Includes cutting and bending the bars and stirrups, assembling the cage at the stirrup spacing indicated and closing it up in the confinement zones next to the supports, placing the top steel over the supports and the bottom steel at mid span in accordance with the bending moment diagram, tying with wire, placing spacers, anchoring into the joints with the columns and checking the schedule before the pour is authorized. Measured by the weight of steel actually placed.",

"Encofrado de viga mediante fondo y laterales de madera sobre puntales, con sus arriostramientos, y su posterior desencofrado. Es el encofrado más laborioso de la estructura por el apuntalamiento y la nivelación del fondo. Incluye el replanteo de la cota inferior, el montaje y nivelación del fondo sobre puntales con la contraflecha prevista, el montaje y aplomado de los laterales, la comprobación de sección y alineación, la aplicación de desmoldeante, el desencofrado escalonado retirando primero los laterales y manteniendo el fondo y los puntales hasta alcanzar la resistencia de proyecto, y la limpieza y acopio del material. Medido en superficie de encofrado en contacto con el concreto.":
    "Formwork to a beam with a lumber soffit and sides on shores, with its bracing, and its subsequent stripping. It is the most laborious formwork in the structure because of the shoring and the leveling of the soffit. Includes setting out the soffit level, erecting and leveling the soffit on shores with the camber specified, erecting and plumbing the sides, checking the section and alignment, applying release agent, staged stripping taking down the sides first and keeping the soffit and the shores in place until the specified strength is reached, and cleaning and stacking the material. Measured by the area of formwork in contact with the concrete.",

"Concreto premezclado de resistencia 250 kg/cm2 vaciado en viga, incluida su compactación por vibrado y su curado. Incluye la revisión previa del armado, del apuntalamiento y del recubrimiento, la recepción y comprobación del concreto, el vaciado continuo evitando juntas frías y respetando la posición de las juntas de construcción previstas en el tercio central del vano, la compactación con vibrador de aguja, el reglado de la cara superior, el curado y el desapuntalamiento escalonado una vez alcanzada la resistencia. Medido en volumen teórico según las dimensiones de proyecto.":
    "Ready-mixed concrete of 250 kg/cm² strength poured into a beam, including compaction by vibration and curing. Includes the prior check of the cage, of the shoring and of the cover, taking delivery of and checking the concrete, pouring continuously to avoid cold joints and respecting the position of the construction joints specified in the middle third of the span, compacting with an internal vibrator, screeding the top face, curing and the staged removal of the shoring once the strength has been reached. Measured by the theoretical volume to the design dimensions.",

"Suministro, corte, doblado, armado y colocación de acero de refuerzo en cabillas corrugadas en pantalla o muro estructural de concreto armado, en dos parrillas verticales, según los planos de despiece. Incluye el corte y doblado, el armado de ambas parrillas con sus barras verticales y horizontales, la colocación de los ganchos o grapas de unión entre parrillas que impiden su separación durante el vaciado, el solape con las esperas del nivel inferior, la disposición de los refuerzos de borde y de los elementos de confinamiento en los extremos, la colocación de separadores en ambas caras y la revisión del despiece. Medido en peso de acero realmente colocado.":
    "Supply, cutting, bending, assembly and placing of deformed bar reinforcement in two vertical mats to a structural concrete wall, to the bending schedules. Includes cutting and bending, assembling both mats with their vertical and horizontal bars, placing the tie hooks or chairs between the mats that stop them spreading during the pour, lapping with the starter bars from the level below, placing the edge reinforcement and the confinement elements at the ends, placing spacers on both faces and checking the schedule. Measured by the weight of steel actually placed.",

"Encofrado a dos caras de pantalla o muro estructural mediante paneles de madera con tirantes pasantes, puntales y arriostramientos, y su posterior desencofrado. Incluye el replanteo, el montaje y aplomado de la primera cara, la colocación de los tirantes y separadores de espesor, el cierre de la segunda cara tras la revisión del armado, el arriostramiento frente al empuje del concreto fresco, la aplicación de desmoldeante, el desencofrado y el sellado de los agujeros de los tirantes. Medido en superficie de encofrado en contacto con el concreto, contando ambas caras.":
    "Double faced formwork to a structural wall using lumber panels with through ties, shores and bracing, and its subsequent stripping. Includes setting out, erecting and plumbing the first face, placing the ties and thickness spacers, closing the second face after the cage has been checked, bracing against the thrust of the wet concrete, applying release agent, stripping and making good the tie holes. Measured by the area of formwork in contact with the concrete, counting both faces.",

"Concreto premezclado de resistencia 250 kg/cm2 vaciado en pantalla o muro estructural, incluida su compactación por vibrado y su curado. Incluye la revisión previa del armado, del encofrado y de los recubrimientos, la recepción del concreto, el vaciado por capas de altura limitada y por puntos alternos para no descuadrar el encofrado, el empleo de tubo de descarga para evitar la segregación, la compactación con vibrador de aguja en cada capa, el curado prolongado y el desencofrado una vez alcanzada la resistencia. Medido en volumen teórico según las dimensiones de proyecto.":
    "Ready-mixed concrete of 250 kg/cm² strength poured into a structural wall, including compaction by vibration and curing. Includes the prior check of the cage, of the formwork and of the cover, taking delivery of the concrete, pouring in layers of limited height and at alternate points so as not to rack the formwork, using a drop chute to avoid segregation, compacting each layer with an internal vibrator, extended curing and stripping once the strength has been reached. Measured by the theoretical volume to the design dimensions.",

# ── Concreto: descripciones cortas ────────────────────────────────────────
"Concreto estructural para columna, vaciado en sitio. Incluye el vaciado y el vibrado. Medido por metro cúbico ejecutado.":
    "Structural concrete for a column, cast in place. Includes pouring and vibrating. Measured per cubic meter constructed.",
"Concreto estructural para viga, vaciado en sitio. Incluye el vaciado y el vibrado. Medido por metro cúbico ejecutado.":
    "Structural concrete for a beam, cast in place. Includes pouring and vibrating. Measured per cubic meter constructed.",
"Concreto estructural para losa maciza. Incluye el vaciado y el vibrado. Medido por metro cúbico ejecutado.":
    "Structural concrete for a solid slab. Includes pouring and vibrating. Measured per cubic meter constructed.",
"Concreto estructural para muro o pantalla. Incluye el vaciado y el vibrado. Medido por metro cúbico ejecutado.":
    "Structural concrete for a structural wall. Includes pouring and vibrating. Measured per cubic meter constructed.",
"Concreto estructural para escalera. Incluye el vaciado y el vibrado. Medido por metro cúbico ejecutado.":
    "Structural concrete for a stair. Includes pouring and vibrating. Measured per cubic meter constructed.",
"Concreto estructural de alta resistencia (300 kg/cm2). Incluye el vaciado y el vibrado. Medido por metro cúbico ejecutado.":
    "High strength structural concrete (300 kg/cm²). Includes pouring and vibrating. Measured per cubic meter constructed.",
"Curado de concreto estructural con membrana de curado. Incluye la aplicación del curador. Medido por metro cuadrado curado.":
    "Curing of structural concrete with a curing membrane. Includes applying the curing compound. Measured per square meter cured.",
"Concreto estructural con aditivo plastificante. Incluye el vaciado con el aditivo. Medido por metro cúbico ejecutado.":
    "Structural concrete with a plasticizing admixture. Includes pouring with the admixture. Measured per cubic meter constructed.",
"Concreto estructural para viga de amarre. Incluye el vaciado y el vibrado. Medido por metro cúbico ejecutado.":
    "Structural concrete for a tie beam. Includes pouring and vibrating. Measured per cubic meter constructed.",
"Concreto estructural para viga de corona. Incluye el vaciado y el vibrado. Medido por metro cúbico ejecutado.":
    "Structural concrete for a ring beam. Includes pouring and vibrating. Measured per cubic meter constructed.",
"Concreto estructural para dintel. Incluye el vaciado y el vibrado. Medido por metro cúbico ejecutado.":
    "Structural concrete for a lintel. Includes pouring and vibrating. Measured per cubic meter constructed.",
"Concreto estructural para losa nervada. Incluye el vaciado y el vibrado. Medido por metro cúbico ejecutado.":
    "Structural concrete for a ribbed slab. Includes pouring and vibrating. Measured per cubic meter constructed.",
"Acabado de superficie de concreto estructural. Incluye el alisado y el acabado. Medido por metro cuadrado acabado.":
    "Finishing of the surface of structural concrete. Includes troweling and finishing. Measured per square meter finished.",
"Concreto estructural para rampa. Incluye el vaciado y el vibrado. Medido por metro cúbico ejecutado.":
    "Structural concrete for a ramp. Includes pouring and vibrating. Measured per cubic meter constructed.",
"Concreto estructural para zapata de medianería. Incluye el vaciado y el vibrado. Medido por metro cúbico ejecutado.":
    "Structural concrete for a party wall footing. Includes pouring and vibrating. Measured per cubic meter constructed.",
"Concreto estructural para losa de entrepiso. Incluye el vaciado y el vibrado. Medido por metro cúbico ejecutado.":
    "Structural concrete for an intermediate floor slab. Includes pouring and vibrating. Measured per cubic meter constructed.",

# ── Estructura metálica ───────────────────────────────────────────────────
"Suministro, izado y montaje de estructura metálica de acero formada por perfiles laminados, con sus cartelas, rigidizadores y elementos de conexión, montada mediante soldadura y tornillería estructural. Incluye la recepción y verificación del material contra los planos de taller, el replanteo y comprobación de la posición de las placas base, el izado con grúa y el presentado de las piezas, el aplomado y nivelación provisional mediante arriostramientos y tornillos de montaje, la ejecución de las uniones definitivas, la verificación geométrica del conjunto montado y la retirada de los elementos provisionales. No incluye la protección anticorrosiva ni la protección contra incendios. Medido en peso de estructura realmente montada.":
    "Supply, hoisting and erection of structural steelwork of rolled sections, with its gussets, stiffeners and connection elements, erected by welding and structural bolting. Includes taking delivery of and checking the material against the shop drawings, setting out and checking the position of the base plates, hoisting by crane and offering up the members, provisional plumbing and leveling using bracing and erection bolts, making the final connections, the geometric check of the assembled frame and removing the temporary elements. It does not include anti-corrosion protection or fire protection. Measured by the weight of steelwork actually erected.",

"Placa base de acero con sus pernos de anclaje, cartelas y nivelación con grout de retracción compensada, para el apoyo de columna metálica sobre fundación de concreto. Incluye el replanteo preciso de la posición de los pernos, que es la operación crítica del conjunto porque un error aquí obliga a rehacer anclajes en concreto endurecido, la colocación de la plantilla de pernos antes del vaciado de la fundación o el anclaje químico posterior, el nivelado de la placa mediante cuñas o tuercas de nivelación, el relleno del espacio bajo la placa con grout fluido sin retracción, el apriete de tuercas al par especificado y la protección del conjunto. Medido por unidad realmente ejecutada.":
    "Steel base plate with its anchor bolts, gussets and leveling on non-shrink grout, to carry a steel column on a concrete footing. Includes the precise setting out of the position of the bolts, the critical operation of the whole assembly because an error here means cutting out and redoing anchors in hardened concrete, placing the bolt template before the footing is poured or chemically anchoring afterwards, leveling the plate on wedges or leveling nuts, filling the space beneath the plate with fluid non-shrink grout, tightening the nuts to the specified torque and protecting the assembly. Measured per unit actually constructed.",

"Ejecución de cordón de soldadura de conexión estructural en obra, con preparación de bordes, precalentamiento cuando el espesor lo requiera y limpieza entre pasadas. Incluye la limpieza y preparación de las superficies a unir con esmerilado hasta metal sano, el punteado y verificación de la posición antes del cordón definitivo, la ejecución de la soldadura en las pasadas necesarias según el espesor, la eliminación de escoria entre pasadas, la inspección visual del cordón terminado y el retoque de la protección anticorrosiva en la zona afectada por el calor. Medido en longitud de cordón realmente ejecutado.":
    "Structural connection weld run on site, with edge preparation, preheat where the thickness requires it and cleaning between runs. Includes cleaning and preparing the faces to be joined by grinding back to sound metal, tacking and checking the position before the final run, depositing the weld in as many runs as the thickness requires, removing slag between runs, visual inspection of the finished weld and touching up the anti-corrosion protection in the heat affected zone. Measured by the length of weld actually deposited.",

"Preparación de la superficie y aplicación de dos manos de imprimación anticorrosiva sobre estructura metálica. La durabilidad del recubrimiento depende mucho más de la preparación previa que de la calidad de la pintura, de modo que el grado de limpieza alcanzado es lo determinante. Incluye la eliminación de óxido, calamina, grasa y restos de escoria mediante cepillo de púas y esmerilado, el desengrasado, la aplicación de la primera mano cubriendo aristas, cantos y zonas de difícil acceso que son las que primero fallan, el respeto del tiempo de repintado y la aplicación de la segunda mano. Medido en superficie realmente tratada, desarrollando todas las caras del perfil.":
    "Preparation of the surface and application of two coats of anti-corrosion primer to structural steelwork. The durability of the coating depends far more on the preparation than on the quality of the paint, so the degree of cleanliness achieved is what decides it. Includes removing rust, mill scale, grease and slag residue with a wire brush and by grinding, degreasing, applying the first coat over the arrises, edges and awkward areas, which are the first to fail, respecting the recoat time and applying the second coat. Measured by the area actually treated, taking every face of the section.",

"Suministro y montaje de correas metálicas de perfil conformado para el soporte de la cubierta, fijadas a la estructura principal mediante tornillería o soldadura, con sus tensores y separadores. Incluye la recepción y verificación del material, el replanteo de la separación entre correas según la luz admisible del material de cubrición, el izado y presentado, la fijación a la estructura principal, la colocación de los tensores que evitan el pandeo lateral y la comprobación de la alineación y del plano de apoyo de la cubierta. Medido en peso realmente montado.":
    "Supply and erection of cold formed steel purlins to support the roof covering, fixed to the main structure by bolting or welding, with their sag rods and spacers. Includes taking delivery of and checking the material, setting out the purlin spacing according to the permissible span of the roof covering, hoisting and offering up, fixing to the main structure, placing the sag rods that prevent lateral buckling and checking the alignment and the plane of support for the roof covering. Measured by the weight actually erected.",

"Suministro y montaje de estructura metálica. Incluye el izado, el montaje y el atornillado. Medido por kilogramo montado.":
    "Supply and erection of structural steelwork. Includes hoisting, erection and bolting. Measured per kilogram erected.",
"Suministro y colocación de placa base con pernos de anclaje para columna metálica. Incluye el replanteo, el anclaje y el montaje. Medido por unidad colocada.":
    "Supply and installation of a base plate with anchor bolts for a steel column. Includes setting out, anchoring and installation. Measured per unit installed.",
"Soldadura de conexiones estructurales en obra. Incluye la soldadura y la limpieza. Medido por metro lineal soldado.":
    "Welding of structural connections on site. Includes welding and cleaning. Measured per meter welded.",
"Imprimación anticorrosiva de estructura metálica. Incluye la limpieza y la imprimación. Medido por metro cuadrado imprimado.":
    "Anti-corrosion primer to structural steelwork. Includes cleaning and priming. Measured per square meter primed.",
"Suministro y colocación de correas metálicas para estructura de techo. Incluye el montaje y la fijación. Medido por metro lineal colocado.":
    "Supply and installation of steel purlins for a roof structure. Includes erection and fixing. Measured per meter installed.",
"Suministro y montaje de estructura metálica para mezzanina. Incluye el montaje y la fijación. Medido por metro cuadrado montado.":
    "Supply and erection of structural steelwork for a mezzanine. Includes erection and fixing. Measured per square meter erected.",
"Suministro y montaje de estructura metálica para cubierta. Incluye el montaje y la fijación. Medido por metro cuadrado montado.":
    "Supply and erection of structural steelwork for a roof. Includes erection and fixing. Measured per square meter erected.",
"Suministro y montaje de columna metálica. Incluye el izado, el montaje y la fijación. Medido por metro lineal montado.":
    "Supply and erection of a steel column. Includes hoisting, erection and fixing. Measured per meter erected.",
"Suministro y montaje de viga metálica. Incluye el izado, el montaje y la fijación. Medido por metro lineal montado.":
    "Supply and erection of a steel beam. Includes hoisting, erection and fixing. Measured per meter erected.",
"Suministro y montaje de estructura metálica para escalera. Incluye el montaje y la fijación. Medido por metro cuadrado montado.":
    "Supply and erection of structural steelwork for a stair. Includes erection and fixing. Measured per square meter erected.",
"Suministro y montaje de estructura metálica para marquesina. Incluye el montaje y la fijación. Medido por metro cuadrado montado.":
    "Supply and erection of structural steelwork for a canopy. Includes erection and fixing. Measured per square meter erected.",
"Suministro y montaje de estructura metálica para techo ligero. Incluye el montaje y la fijación. Medido por metro cuadrado montado.":
    "Supply and erection of structural steelwork for a lightweight roof. Includes erection and fixing. Measured per square meter erected.",
"Ejecución de conexión atornillada estructural. Incluye el montaje y el apriete. Medido por conexión ejecutada.":
    "Bolted structural connection. Includes assembly and tightening. Measured per connection completed.",
"Suministro y montaje de estructura metálica con protección anticorrosiva completa. Incluye el montaje y la protección. Medido por metro cuadrado montado.":
    "Supply and erection of structural steelwork with full anti-corrosion protection. Includes erection and protection. Measured per square meter erected.",
"Suministro y montaje de estructura metálica para entrepiso ligero. Incluye el montaje y la fijación. Medido por metro cuadrado montado.":
    "Supply and erection of structural steelwork for a lightweight intermediate floor. Includes erection and fixing. Measured per square meter erected.",
"Suministro y montaje de viga de amarre metálica. Incluye el montaje y la fijación. Medido por metro lineal montado.":
    "Supply and erection of a steel tie beam. Includes erection and fixing. Measured per meter erected.",
"Refuerzo metálico de losa con perfiles. Incluye el montaje del refuerzo. Medido por metro cuadrado reforzado.":
    "Strengthening of a slab with steel sections. Includes installing the strengthening. Measured per square meter strengthened.",

# ── Estructura de madera ──────────────────────────────────────────────────
"Suministro y montaje de estructura de madera aserrada formada por vigas, pares y tirantes, con uniones ejecutadas mediante herrajes metálicos o ensambles tradicionales. Incluye la recepción y verificación de la escuadría, la humedad y la ausencia de defectos que comprometan la capacidad, el corte y labra de las piezas, el presentado y ajuste de las uniones, el izado y montaje con apeo provisional, la fijación definitiva, la comprobación geométrica del conjunto y el ajuste de contraflechas. No incluye el tratamiento preservante ni los herrajes, que se valoran aparte. Medido en volumen de madera realmente colocada.":
    "Supply and erection of a sawn lumber structure of beams, rafters and ties, with joints made using metal connectors or traditional carpentry joints. Includes taking delivery of and checking the section sizes, the moisture content and the absence of defects that would compromise capacity, cutting and shaping the members, offering up and fitting the joints, hoisting and erecting with temporary supports, final fixing, the geometric check of the assembly and adjusting the camber. It does not include the preservative treatment or the connectors, which are priced separately. Measured by the volume of lumber actually placed.",

"Suministro y montaje de correas o viguetas de madera para el soporte de cubierta o entrepiso, fijadas a la estructura principal con herrajes o clavado. Incluye la recepción y selección de las piezas, el replanteo de la separación entre ejes, el corte a medida, el presentado y nivelación, la fijación a los apoyos, la colocación de los arriostramientos o crucetas que impiden el vuelco lateral y la comprobación del plano de apoyo. Medido en longitud realmente colocada.":
    "Supply and installation of lumber purlins or joists to support a roof covering or intermediate floor, fixed to the main structure with connectors or nailing. Includes taking delivery of and selecting the pieces, setting out the spacing between centers, cutting to length, offering up and leveling, fixing to the bearings, placing the bracing or blocking that prevents lateral overturning and checking the plane of support. Measured by the length actually installed.",

"Aplicación de tratamiento preservante fungicida e insecticida sobre madera estructural, mediante dos manos a brocha o por inmersión. En clima tropical este tratamiento no es opcional: la madera sin proteger tiene una vida útil corta frente al comején y a los hongos de pudrición. Incluye el lijado y limpieza previa de la superficie, la aplicación de la primera mano con especial atención a testas, ensambles y zonas de apoyo que son las de mayor riesgo, el respeto del tiempo de absorción y la aplicación de la segunda mano. Medido en superficie realmente tratada, desarrollando todas las caras.":
    "Application of fungicidal and insecticidal preservative to structural lumber, in two coats by brush or by dipping. In a tropical climate this treatment is not optional: unprotected lumber has a short service life against termites and rot fungi. Includes sanding and cleaning the surface beforehand, applying the first coat with particular attention to the end grain, the joints and the bearing areas, which carry the greatest risk, respecting the absorption time and applying the second coat. Measured by the area actually treated, taking every face.",

"Suministro y colocación de herraje metálico galvanizado de unión en estructura de madera, tal como estribo, placa, ángulo o conector de pares, con su tornillería específica. Incluye el replanteo de la posición, el pretaladrado de la madera con el diámetro correcto para no fisurarla, la colocación del herraje, el atornillado o clavado con la totalidad de los agujeros ocupados, requisito del que depende la capacidad declarada del herraje, y la comprobación del apriete. Medido por unidad realmente colocada.":
    "Supply and installation of galvanized metal connectors in a lumber structure, such as a joist hanger, plate, angle or rafter connector, with the specified fasteners. Includes setting out the position, pre-drilling the lumber to the correct diameter so as not to split it, placing the connector, screwing or nailing with every hole filled, a requirement on which the declared capacity of the connector depends, and checking the tightness. Measured per unit actually installed.",

"Suministro y montaje de estructura de madera. Incluye el montaje y la fijación. Medido por metro cúbico montado.":
    "Supply and erection of a lumber structure. Includes erection and fixing. Measured per cubic meter erected.",
"Suministro y colocación de correas de madera para cubierta. Incluye la colocación y la fijación. Medido por metro lineal colocado.":
    "Supply and installation of lumber purlins for a roof. Includes installation and fixing. Measured per meter installed.",
"Tratamiento preservante de madera estructural. Incluye la aplicación del preservante. Medido por metro cuadrado tratado.":
    "Preservative treatment of structural lumber. Includes applying the preservative. Measured per square meter treated.",
"Suministro y colocación de herraje o conector para unión de estructura de madera. Incluye la colocación del herraje. Medido por unidad colocado.":
    "Supply and installation of hardware or connectors for joints in a lumber structure. Includes placing the connector. Measured per unit installed.",
"Suministro y colocación de viga de madera estructural. Incluye la colocación y la fijación. Medido por metro lineal colocado.":
    "Supply and installation of a structural lumber beam. Includes installation and fixing. Measured per meter installed.",
"Suministro y colocación de columna de madera estructural. Incluye la colocación y la fijación. Medido por metro lineal colocado.":
    "Supply and installation of a structural lumber column. Includes installation and fixing. Measured per meter installed.",
"Ejecución de entrepiso de madera estructural. Incluye la estructura y el tablero. Medido por metro cuadrado ejecutado.":
    "Construction of a structural lumber intermediate floor. Includes the structure and the decking. Measured per square meter constructed.",
"Ejecución de cubierta de madera estructural. Incluye la estructura de la cubierta. Medido por metro cuadrado ejecutado.":
    "Construction of a structural lumber roof. Includes the roof structure. Measured per square meter constructed.",
"Suministro y montaje de cercha de madera. Incluye el montaje y la fijación. Medido por metro cuadrado montado.":
    "Supply and erection of a lumber truss. Includes erection and fixing. Measured per square meter erected.",
"Suministro y colocación de correa de madera para techo. Incluye la colocación y la fijación. Medido por metro lineal colocado.":
    "Supply and installation of a lumber purlin for a roof. Includes installation and fixing. Measured per meter installed.",
"Ejecución de entrepiso de madera con tablero OSB. Incluye la estructura y el tablero. Medido por metro cuadrado ejecutado.":
    "Construction of a lumber intermediate floor with OSB decking. Includes the structure and the decking. Measured per square meter constructed.",
"Suministro y colocación de viga de madera laminada. Incluye la colocación y la fijación. Medido por metro lineal colocado.":
    "Supply and installation of a glue laminated lumber beam. Includes installation and fixing. Measured per meter installed.",
"Ejecución de cubierta de madera con aislamiento térmico. Incluye la estructura y el aislamiento. Medido por metro cuadrado ejecutado.":
    "Construction of a lumber roof with thermal insulation. Includes the structure and the insulation. Measured per square meter constructed.",
"Suministro y colocación de correa de madera con tratamiento preservante. Incluye la colocación y el tratamiento. Medido por metro lineal colocado.":
    "Supply and installation of a treated lumber purlin. Includes installation and treatment. Measured per meter installed.",
"Ejecución de entrepiso de madera con viguetas. Incluye la estructura y el tablero. Medido por metro cuadrado ejecutado.":
    "Construction of a lumber intermediate floor on joists. Includes the structure and the decking. Measured per square meter constructed.",
"Ejecución de cubierta de madera preparada para teja. Incluye la estructura y el entablado. Medido por metro cuadrado ejecutado.":
    "Construction of a lumber roof ready for tiling. Includes the structure and the boarding. Measured per square meter constructed.",

# ── Losas ─────────────────────────────────────────────────────────────────
"Encofrado de losa maciza mediante tablero de madera sobre soleras y puntales metálicos, con su nivelación y contraflecha, y su posterior desencofrado. Incluye el replanteo de la cota inferior, el montaje de la retícula de puntales con la separación indicada, la colocación de soleras y del tablero, la nivelación del conjunto con la contraflecha prevista, el sellado de juntas del tablero para evitar la pérdida de lechada, la aplicación de desmoldeante, el desencofrado escalonado manteniendo los puntales de seguridad hasta alcanzar la resistencia de proyecto, y la limpieza y acopio del material. Medido en superficie de encofrado en contacto con el concreto.":
    "Formwork to a solid slab using lumber decking on sole plates and steel shores, leveled and with camber, and its subsequent stripping. Includes setting out the soffit level, erecting the grid of shores at the spacing indicated, placing the sole plates and the decking, leveling the assembly with the camber specified, sealing the joints of the decking to prevent loss of grout, applying release agent, staged stripping keeping the safety shores in place until the specified strength is reached, and cleaning and stacking the material. Measured by the area of formwork in contact with the concrete.",

"Suministro, corte, doblado, armado y colocación de acero de refuerzo en cabillas corrugadas en losa maciza, en parrillas inferior y superior según los planos de despiece. Incluye el corte y doblado, el armado de las parrillas con amarre de alambre, la colocación de separadores inferiores y de caballetes que sostienen la parrilla superior en su cota, los refuerzos sobre los apoyos y en los bordes de huecos, y el repaso de la posición del armado inmediatamente antes del vaciado. Medido en peso de acero realmente colocado.":
    "Supply, cutting, bending, assembly and placing of deformed bar reinforcement to a solid slab, in top and bottom mats to the bending schedules. Includes cutting and bending, assembling the mats with wire ties, placing bottom spacers and the chairs that hold the top mat at its level, the reinforcement over the supports and around the edges of openings, and going over the position of the cage immediately before the pour. Measured by the weight of steel actually placed.",

"Concreto premezclado de resistencia 250 kg/cm2 vaciado en losa maciza de entrepiso o techo, incluida su compactación por vibrado y su curado. Incluye la revisión previa del encofrado, del apuntalamiento, del armado y de los recubrimientos, la recepción y comprobación del concreto, el vaciado continuo por franjas evitando juntas frías, la compactación con vibrador de aguja, el reglado a la cota mediante maestras, el flotado de la superficie y el curado durante los primeros días. Medido en volumen teórico según las dimensiones de proyecto.":
    "Ready-mixed concrete of 250 kg/cm² strength poured into a solid intermediate floor or roof slab, including compaction by vibration and curing. Includes the prior check of the formwork, of the shoring, of the cage and of the cover, taking delivery of and checking the concrete, pouring continuously in bays to avoid cold joints, compacting with an internal vibrator, screeding to level against screed rails, floating the surface and curing over the first few days. Measured by the theoretical volume to the design dimensions.",

"Losa nervada de entrepiso o techo formada por nervios de concreto armado y bloques de arcilla de aliviano, con su loseta de compresión y malla de retracción. Incluye el encofrado y apuntalamiento del fondo, la colocación de los bloques de aliviano dejando el ancho de nervio previsto, el armado de los nervios con su refuerzo inferior y superior, la colocación de la malla electrosoldada de la loseta de compresión, el vaciado y vibrado del concreto, el reglado, el curado y el desapuntalamiento escalonado. Medido en superficie de losa realmente ejecutada.":
    "Ribbed intermediate floor or roof slab of reinforced concrete ribs with clay void formers, with its structural topping and shrinkage mesh. Includes formwork and shoring to the soffit, placing the void formers leaving the rib width specified, reinforcing the ribs with their top and bottom steel, placing the welded wire mesh of the structural topping, pouring and vibrating the concrete, screeding, curing and the staged removal of the shoring. Measured by the area of slab actually constructed.",

"Losa nervada de entrepiso o techo formada por nervios de concreto armado y bloques de poliestireno expandido de aliviano, con su loseta de compresión y malla de retracción. Frente al bloque de arcilla reduce notablemente el peso propio de la losa, lo que repercute en el dimensionado de vigas, columnas y fundaciones, y mejora el aislamiento térmico. Incluye el encofrado y apuntalamiento, la colocación de los bloques, el armado de los nervios, la malla de la loseta de compresión, el vaciado y vibrado, el reglado, el curado y el desapuntalamiento escalonado. Medido en superficie de losa realmente ejecutada.":
    "Ribbed intermediate floor or roof slab of reinforced concrete ribs with expanded polystyrene void formers, with its structural topping and shrinkage mesh. Against the clay block it reduces the self weight of the slab considerably, which shows up in the sizing of the beams, columns and foundations, and improves the thermal insulation. Includes formwork and shoring, placing the formers, reinforcing the ribs, the mesh to the structural topping, pouring and vibrating, screeding, curing and the staged removal of the shoring. Measured by the area of slab actually constructed.",

"Losa de entrepiso o techo formada por viguetas prefabricadas pretensadas, bloques de aliviano, loseta de compresión y malla de retracción. Al trabajar la vigueta como elemento resistente durante el montaje, el apuntalamiento necesario es mucho menor que en una losa nervada tradicional, lo que acelera la ejecución. Incluye el replanteo y colocación de las viguetas sobre sus apoyos con la entrega mínima requerida, el apuntalamiento intermedio, la colocación de los bloques, el armado de negativos sobre apoyos, la malla de la loseta, el vaciado y vibrado, el curado y el desapuntalamiento escalonado. Medido en superficie de losa realmente ejecutada.":
    "Intermediate floor or roof slab of precast prestressed joists, void formers, a structural topping and shrinkage mesh. Because the joist acts as a structural element during erection, far less shoring is needed than for a traditional ribbed slab, which speeds up the work. Includes setting out and placing the joists on their bearings with the minimum bearing length required, intermediate shoring, placing the blocks, the hogging reinforcement over the supports, the mesh to the topping, pouring and vibrating, curing and the staged removal of the shoring. Measured by the area of slab actually constructed.",

"Apuntalamiento de losa mediante puntales metálicos telescópicos sobre durmientes de reparto, dimensionado para soportar el peso del concreto fresco, del encofrado y de las cargas de ejecución, y mantenido hasta que la losa alcanza la resistencia de proyecto. El desapuntalamiento prematuro es una de las causas más frecuentes de flechas excesivas y de fisuración permanente. Incluye el replanteo de la retícula, la colocación de durmientes en cabeza y base, el montaje y puesta en carga de los puntales, la comprobación de que la carga se transmite a un nivel inferior con capacidad suficiente, la revisión durante el vaciado y el desapuntalamiento escalonado. Medido en superficie de losa realmente apuntalada.":
    "Shoring of a slab with telescopic steel shores on spreader beams, sized to carry the weight of the wet concrete, of the formwork and of the construction loads, and kept in place until the slab reaches the specified strength. Premature removal of the shoring is one of the most frequent causes of excessive deflection and permanent cracking. Includes setting out the grid, placing spreader beams at head and base, erecting and loading the shores, checking that the load is transferred to a level below of sufficient capacity, inspection during the pour and the staged removal of the shoring. Measured by the area of slab actually shored.",

"Losa de entrepiso con lámina colaborante de acero galvanizado sobre estructura metálica, con malla de retracción y capa de compresión de concreto. La lámina actúa a la vez como encofrado perdido y como armadura inferior, lo que elimina el encofrado y el apuntalamiento en la mayoría de las luces y acelera notablemente la ejecución. Incluye la colocación y fijación de las láminas a las vigas, la soldadura de los conectores de cortante que hacen trabajar solidariamente el acero y el concreto, el cierre de bordes, la malla, el vaciado y reglado del concreto y el curado. Medido en superficie realmente ejecutada.":
    "Intermediate floor slab of galvanized metal deck on structural steelwork, with shrinkage mesh and a concrete topping. The deck acts at once as permanent formwork and as the bottom reinforcement, which removes the need for formwork and shoring over most spans and speeds the work up considerably. Includes laying and fixing the deck to the beams, welding the shear studs that make the steel and the concrete act compositely, closing the edges, the mesh, pouring and screeding the concrete and curing. Measured by the area actually constructed.",

"Ampliación de losa existente en voladizo o formación de balcón, con conexión a la estructura mediante anclaje químico de las barras de continuidad. La conexión es el punto crítico: un voladizo trabaja con el acero en la cara superior y con la longitud de anclaje completa dentro de la losa existente, de modo que la profundidad y la posición de las perforaciones no admiten aproximaciones. Incluye el apeo, el repicado y limpieza del borde existente, la perforación y anclaje químico de las barras, el armado, el encofrado sobre puntales, el vaciado y vibrado, el curado y el desapeo escalonado. Medido en superficie realmente ejecutada.":
    "Extension of an existing slab as a cantilever or the formation of a balcony, tied into the structure by chemically anchoring the continuity bars. The connection is the critical point: a cantilever works with the steel in the top face and with the full anchorage length within the existing slab, so the depth and the position of the holes admit no approximation. Includes shoring, hacking back and cleaning the existing edge, drilling and chemically anchoring the bars, the reinforcement, the formwork on shores, pouring and vibrating, curing and the staged removal of the shoring. Measured by the area actually constructed.",

"Ejecución de losa nervada con bloques de arcilla de aliviano. Incluye la colocación de bloques y el vaciado. Medido por metro cuadrado ejecutado.":
    "Construction of a ribbed slab with clay void formers. Includes placing the formers and pouring. Measured per square meter constructed.",
"Ejecución de losa nervada con bloques de poliestireno de aliviano. Incluye la colocación de bloques y el vaciado. Medido por metro cuadrado ejecutado.":
    "Construction of a ribbed slab with polystyrene void formers. Includes placing the formers and pouring. Measured per square meter constructed.",
"Ejecución de losa con viguetas prefabricadas pretensadas. Incluye la colocación de viguetas y el vaciado. Medido por metro cuadrado ejecutado.":
    "Construction of a slab with precast prestressed joists. Includes placing the joists and pouring. Measured per square meter constructed.",
"Ejecución de losa mixta con lámina colaborante sobre estructura metálica. Incluye la lámina y el vaciado. Medido por metro cuadrado ejecutado.":
    "Construction of a composite slab with metal deck on structural steelwork. Includes the deck and pouring. Measured per square meter constructed.",
"Ejecución de losa maciza con malla electrosoldada. Incluye la malla y el vaciado. Medido por metro cuadrado ejecutado.":
    "Construction of a solid slab with welded wire mesh. Includes the mesh and pouring. Measured per square meter constructed.",
"Ejecución de losa aligerada con anime de poliestireno. Incluye el aligeramiento y el vaciado. Medido por metro cuadrado ejecutado.":
    "Construction of a slab lightweightened with polystyrene void formers. Includes the void formers and pouring. Measured per square meter constructed.",
"Ejecución de losa de entrepiso con aislamiento térmico. Incluye el aislamiento y el vaciado. Medido por metro cuadrado ejecutado.":
    "Construction of an intermediate floor slab with thermal insulation. Includes the insulation and pouring. Measured per square meter constructed.",
"Ejecución de losa de cubierta de concreto. Incluye el vaciado y el acabado. Medido por metro cuadrado ejecutado.":
    "Construction of a concrete roof slab. Includes pouring and finishing. Measured per square meter constructed.",
"Ejecución de losa con juntas de dilatación. Incluye la formación de las juntas. Medido por metro cuadrado ejecutado.":
    "Construction of a slab with expansion joints. Includes forming the joints. Measured per square meter constructed.",
"Ejecución de losa de concreto aligerada con bloques. Incluye la colocación de bloques y el vaciado. Medido por metro cuadrado ejecutado.":
    "Construction of a concrete slab lightweightened with blocks. Includes placing the blocks and pouring. Measured per square meter constructed.",
"Ejecución de losa de techo con viguetas y bloques de aliviano. Incluye la colocación y el vaciado. Medido por metro cuadrado ejecutado.":
    "Construction of a roof slab with joists and void formers. Includes installation and pouring. Measured per square meter constructed.",
"Ejecución de losa de concreto con acero de temperatura. Incluye el acero y el vaciado. Medido por metro cuadrado ejecutado.":
    "Construction of a concrete slab with shrinkage and temperature steel. Includes the steel and pouring. Measured per square meter constructed.",
"Ejecución de losa de concreto aligerada con casetones. Incluye la colocación de casetones y el vaciado. Medido por metro cuadrado ejecutado.":
    "Construction of a concrete slab lightweightened with waffle pods. Includes placing the pods and pouring. Measured per square meter constructed.",
"Ejecución de losa de entrepiso con malla electrosoldada. Incluye la malla y el vaciado. Medido por metro cuadrado ejecutado.":
    "Construction of an intermediate floor slab with welded wire mesh. Includes the mesh and pouring. Measured per square meter constructed.",
"Ejecución de losa de concreto con acabado pulido. Incluye el vaciado y el pulido. Medido por metro cuadrado ejecutado.":
    "Construction of a concrete slab with a polished finish. Includes pouring and polishing. Measured per square meter constructed.",
"Ejecución de losa de concreto con pendiente de evacuación. Incluye la formación de la pendiente y el vaciado. Medido por metro cuadrado ejecutado.":
    "Construction of a concrete slab with drainage falls. Includes forming the falls and pouring. Measured per square meter constructed.",

# ── Escaleras y rampas ────────────────────────────────────────────────────
"Encofrado de escalera de concreto armado, comprendiendo el fondo de la losa inclinada sobre puntales, los laterales de cierre y los tabicones de formación de peldaños, y su posterior desencofrado. Es de los encofrados más laboriosos por la geometría inclinada y por el replanteo de la huella y la contrahuella, que debe ser exacto y constante porque cualquier diferencia entre peldaños se percibe al caminar y compromete la seguridad. Incluye el replanteo, el montaje y nivelación del fondo, los laterales, los tabicones de peldaño, el arriostramiento, el desmoldeante, el desencofrado y la limpieza del material. Medido en superficie de encofrado en contacto con el concreto.":
    "Formwork to a reinforced concrete stair, comprising the soffit of the inclined slab on shores, the closing sides and the riser boards that form the steps, and its subsequent stripping. It is one of the most laborious formwork items because of the inclined geometry and the setting out of the going and the rise, which must be exact and constant because any difference between steps is felt when walking and compromises safety. Includes setting out, erecting and leveling the soffit, the sides, the riser boards, the bracing, the release agent, stripping and cleaning the material. Measured by the area of formwork in contact with the concrete.",

"Suministro, corte, doblado, armado y colocación de acero de refuerzo en cabillas corrugadas en escalera de concreto armado, según los planos de despiece. Incluye el corte y doblado, el armado de la parrilla principal de la losa inclinada con su refuerzo de reparto, la disposición de los refuerzos en los quiebres de la geometría donde el trazado del acero debe respetar el sentido de las tracciones, el anclaje en los apoyos de arranque y llegada, el amarre con alambre y la colocación de separadores. Medido en peso de acero realmente colocado.":
    "Supply, cutting, bending, assembly and placing of deformed bar reinforcement to a reinforced concrete stair, to the bending schedules. Includes cutting and bending, assembling the main mat of the inclined slab with its distribution steel, placing the reinforcement at the breaks in the geometry where the line of the steel must follow the direction of the tension, anchoring at the bearings at the foot and the head, tying with wire and placing spacers. Measured by the weight of steel actually placed.",

"Concreto premezclado de resistencia 250 kg/cm2 vaciado en escalera, incluida su compactación por vibrado y su curado. El vaciado en pendiente exige un concreto de consistencia más seca de lo habitual para que no escurra por la rampa, y debe ejecutarse de forma ascendente desde el arranque. Incluye la revisión previa del encofrado, el apuntalamiento y el armado, la recepción del concreto con el asentamiento adecuado, el vaciado ascendente por peldaños, la compactación con vibrador, el fratasado de huellas y contrahuellas, el curado y el desapuntalamiento escalonado. Medido en volumen teórico según las dimensiones de proyecto.":
    "Ready-mixed concrete of 250 kg/cm² strength poured into a stair, including compaction by vibration and curing. Pouring on a slope needs a drier mix than usual so that it does not run down the flight, and it must be done working upwards from the foot. Includes the prior check of the formwork, the shoring and the cage, taking delivery of the concrete at the right slump, pouring upwards step by step, compacting with a vibrator, floating the treads and risers, curing and the staged removal of the shoring. Measured by the theoretical volume to the design dimensions.",

"Suministro y montaje de escalera metálica estructural formada por zancas de perfil laminado, peldaños y descansos, con sus anclajes a la estructura. Incluye la verificación en obra de las cotas reales de arranque y llegada antes de la fabricación, paso imprescindible porque una escalera metálica no admite ajustes en sitio, el izado y presentado de las zancas, su nivelación y aplomado, la ejecución de las uniones soldadas o atornilladas, el montaje de peldaños y descansos y la comprobación de que huella y contrahuella se mantienen constantes en todo el tramo. No incluye barandas ni el acabado del peldaño. Medido en peso realmente montado.":
    "Supply and erection of a structural steel stair of rolled section stringers, treads and landings, with its anchors to the structure. Includes checking the actual levels at the foot and the head on site before fabrication, an essential step because a steel stair admits no adjustment in place, hoisting and offering up the stringers, leveling and plumbing them, making the welded or bolted connections, fitting the treads and landings and checking that the going and the rise stay constant over the whole flight. It does not include the guardrails or the finish to the treads. Measured by the weight actually erected.",

"Encofrado y desencofrado de escalera de concreto armado. Incluye el montaje del encofrado. Medido por metro cuadrado encofrado.":
    "Formwork and stripping of a reinforced concrete stair. Includes erecting the formwork. Measured per square meter formed.",
"Suministro y colocación de acero de refuerzo en escalera. Incluye el corte y la colocación. Medido por kilogramo colocado.":
    "Supply and placing of reinforcing steel to a stair. Includes cutting and placing. Measured per kilogram placed.",
"Concreto estructural para escalera. Incluye el vaciado y el vibrado. Medido por metro cúbico ejecutado.":
    "Structural concrete for a stair. Includes pouring and vibrating. Measured per cubic meter constructed.",
"Suministro y montaje de escalera metálica estructural. Incluye el montaje y la fijación. Medido por metro cuadrado montado.":
    "Supply and erection of a structural steel stair. Includes erection and fixing. Measured per square meter erected.",
"Ejecución de rampa de concreto estructural. Incluye el vaciado y el acabado. Medido por metro cuadrado ejecutado.":
    "Construction of a structural concrete ramp. Includes pouring and finishing. Measured per square meter constructed.",
"Ejecución de escalera de concreto con acabado. Incluye el vaciado y el acabado. Medido por metro cuadrado ejecutado.":
    "Construction of a concrete stair with a finish. Includes pouring and finishing. Measured per square meter constructed.",
"Suministro y montaje de escalera metálica con peldaños de rejilla. Incluye el montaje. Medido por metro cuadrado montado.":
    "Supply and erection of a steel stair with grating treads. Includes erection. Measured per square meter erected.",
"Suministro y montaje de rampa metálica estructural. Incluye el montaje. Medido por metro cuadrado montado.":
    "Supply and erection of a structural steel ramp. Includes erection. Measured per square meter erected.",
"Ejecución de escalera de concreto de dos tramos. Incluye el vaciado. Medido por metro cuadrado ejecutado.":
    "Construction of a concrete stair in two flights. Includes pouring. Measured per square meter constructed.",
"Suministro y montaje de escalera metálica de caracol. Incluye el montaje. Medido por metro cuadrado montado.":
    "Supply and erection of a steel spiral stair. Includes erection. Measured per square meter erected.",
"Ejecución de escalera de concreto con descansillo. Incluye el vaciado. Medido por metro cuadrado ejecutado.":
    "Construction of a concrete stair with a landing. Includes pouring. Measured per square meter constructed.",
"Ejecución de rampa de concreto con bordillo. Incluye el vaciado y el bordillo. Medido por metro cuadrado ejecutado.":
    "Construction of a concrete ramp with a curb. Includes pouring and the curb. Measured per square meter constructed.",
"Ejecución de escalera de concreto reforzada. Incluye el vaciado y el refuerzo. Medido por metro cuadrado ejecutado.":
    "Construction of a strengthened concrete stair. Includes pouring and the strengthening. Measured per square meter constructed.",
"Suministro y montaje de escalera metálica con baranda. Incluye el montaje de la escalera y la baranda. Medido por metro cuadrado montado.":
    "Supply and erection of a steel stair with a guardrail. Includes erecting the stair and the guardrail. Measured per square meter erected.",
"Ejecución de rampa de concreto con acabado antideslizante. Incluye el vaciado y el acabado. Medido por metro cuadrado ejecutado.":
    "Construction of a concrete ramp with a non-slip finish. Includes pouring and finishing. Measured per square meter constructed.",
"Ejecución de escalera de concreto a prueba de fuego. Incluye el vaciado. Medido por metro cuadrado ejecutado.":
    "Construction of a fire resisting concrete stair. Includes pouring. Measured per square meter constructed.",
"Suministro y montaje de escalera metálica de emergencia. Incluye el montaje. Medido por metro cuadrado montado.":
    "Supply and erection of a steel escape stair. Includes erection. Measured per square meter erected.",

# ── Anclajes y juntas ─────────────────────────────────────────────────────
"Ejecución de anclaje químico de barra de acero en concreto. Incluye la perforación y la inyección. Medido por anclaje ejecutado.":
    "Installation of a chemical anchor for a steel bar in concrete. Includes drilling and injection. Measured per anchor installed.",
"Colocación de perno de anclaje en concreto. Incluye la perforación y la colocación. Medido por perno colocado.":
    "Installation of an anchor bolt in concrete. Includes drilling and installation. Measured per bolt installed.",
"Colocación de conector de cortante soldable en losa mixta. Incluye la soldadura del conector. Medido por conector colocado.":
    "Installation of a welded shear stud to a composite slab. Includes welding the stud. Measured per stud installed.",
"Soldadura estructural en obra. Incluye la soldadura y la limpieza. Medido por metro lineal soldado.":
    "Structural welding on site. Includes welding and cleaning. Measured per meter welded.",
"Colocación de anclaje mecánico de expansión en concreto. Incluye la perforación y la colocación. Medido por anclaje colocado.":
    "Installation of an expansion anchor in concrete. Includes drilling and installation. Measured per anchor installed.",
"Ejecución de anclaje de barra con resina epóxica. Incluye la perforación y la inyección. Medido por anclaje ejecutado.":
    "Installation of a bar anchor with epoxy resin. Includes drilling and injection. Measured per anchor installed.",
"Ejecución de conexión soldada de placa base. Incluye la soldadura. Medido por metro lineal soldado.":
    "Welded connection to a base plate. Includes welding. Measured per meter welded.",
"Ejecución de junta de dilatación estructural. Incluye la formación de la junta. Medido por metro lineal ejecutado.":
    "Formation of a structural expansion joint. Includes forming the joint. Measured per meter constructed.",
"Ejecución de junta de construcción en elemento de concreto. Incluye la formación de la junta. Medido por metro lineal ejecutado.":
    "Formation of a construction joint in a concrete element. Includes forming the joint. Measured per meter constructed.",
"Ejecución de junta sísmica estructural. Incluye la formación de la junta. Medido por metro lineal ejecutado.":
    "Formation of a structural seismic joint. Includes forming the joint. Measured per meter constructed.",

# ── Reparación y refuerzo ─────────────────────────────────────────────────
"Reparación de concreto deteriorado por coqueras, desprendimientos o carbonatación, mediante saneado del área y reposición con mortero tixotrópico de reparación estructural, de 3 cm de espesor medio. Incluye la delimitación del área con corte perimetral perpendicular para evitar bordes en bisel que se desprenden, el picado del concreto suelto hasta alcanzar concreto sano, la limpieza y saturación del soporte, la aplicación del puente de adherencia, la reposición del mortero por capas respetando el espesor máximo por capa y el curado del material aplicado. Medido en superficie realmente reparada.":
    "Repair of concrete damaged by honeycombing, spalling or carbonation, by cutting out the area and reinstating with a thixotropic structural repair mortar, 3 cm average thickness. Includes defining the area with a square perimeter cut to avoid feather edges that come away, hacking out the loose concrete back to sound concrete, cleaning and saturating the substrate, applying the bonding coat, reinstating the mortar in layers respecting the maximum thickness per layer and curing the material applied. Measured by the area actually repaired.",

"Limpieza y tratamiento del acero de refuerzo afectado por corrosión, descubierto tras el saneado del concreto, mediante cepillado hasta grado de limpieza adecuado y aplicación de recubrimiento pasivante con inhibidor. Es el paso que decide si la reparación dura: si se repone el mortero sobre acero oxidado, la corrosión continúa por debajo y vuelve a reventar el recubrimiento en pocos años. Incluye el descubrimiento del acero en todo su perímetro dejando espacio libre por detrás de la barra, la eliminación del óxido con cepillo de púas y esmeril, la valoración de la pérdida de sección y el aviso al proyectista si supera lo admisible, y la aplicación de dos manos de pasivante. Medido en superficie de elemento realmente tratada.":
    "Cleaning and treatment of corroded reinforcement exposed after the concrete has been cut out, by brushing to a suitable standard of cleanliness and applying a passivating coating with inhibitor. It is the step that decides whether the repair lasts: if the mortar is reinstated over rusted steel, corrosion continues underneath and blows the cover again within a few years. Includes exposing the steel around its whole perimeter leaving a gap behind the bar, removing the rust with a wire brush and by grinding, assessing the loss of section and notifying the designer if it exceeds what is permissible, and applying two coats of passivator. Measured by the area of element actually treated.",

"Sellado y restitución del monolitismo de fisuras en elementos de concreto mediante inyección de resina epóxica de baja viscosidad a través de boquillas. Incluye el mapeo previo y el registro del ancho y recorrido de las fisuras, la determinación de si la fisura está viva o estabilizada, ya que inyectar con resina rígida una fisura en movimiento provoca su reaparición junto al sello, la limpieza del recorrido, la colocación de boquillas y el sellado superficial del labio, la inyección progresiva de boquilla en boquilla hasta rebose en la siguiente, el fraguado y el retiro de boquillas y sello con repaso de la superficie. Medido en longitud de fisura realmente inyectada.":
    "Sealing and restoring the monolithic action of cracks in concrete elements by injecting low viscosity epoxy resin through injection ports. Includes mapping beforehand and recording the width and the run of the cracks, determining whether the crack is live or dormant, since injecting a moving crack with a rigid resin makes it reappear alongside the seal, cleaning the run, fitting the ports and sealing the surface of the crack, injecting progressively from port to port until it appears at the next, setting, and removing the ports and the seal and making good the surface. Measured by the length of crack actually injected.",

"Refuerzo de elemento estructural de concreto mediante encolado de tejido de fibra de carbono con resina epóxica de saturación. Aporta capacidad a flexión o a cortante sin apenas añadir peso ni modificar la geometría, lo que lo hace idóneo en rehabilitación donde no se puede aumentar la sección. Incluye la regularización y lijado del soporte hasta obtener una superficie plana y sin lechada, el redondeo de las aristas por las que ha de doblar el tejido, la imprimación, la aplicación de la resina de saturación, la colocación del tejido en la dirección de las tracciones eliminando burbujas con rodillo, la segunda capa de resina y el curado. Medido en superficie de tejido realmente colocada.":
    "Strengthening of a structural concrete element by bonding carbon fiber fabric with a saturating epoxy resin. It adds flexural or shear capacity with almost no added weight and no change to the geometry, which makes it ideal in refurbishment where the section cannot be increased. Includes preparing and sanding the substrate to a flat surface free of laitance, rounding the arrises over which the fabric has to bend, priming, applying the saturating resin, laying the fabric in the direction of the tension and rolling out the air bubbles, the second coat of resin and curing. Measured by the area of fabric actually applied.",

"Refuerzo de columna existente mediante encamisado de concreto armado, aumentando su sección con una capa perimetral de concreto con su propio armado, conectada al núcleo original. Incluye el apeo previo de la estructura que descarga la columna, el repicado de la superficie existente para dar adherencia, la perforación y anclaje químico de los conectores que cosen el encamisado al núcleo, el armado longitudinal y de estribos de confinamiento, el encofrado, el vaciado con concreto de retracción compensada o mortero fluido dado el reducido espesor, el curado y el desapeo escalonado. Medido en longitud de columna realmente encamisada.":
    "Strengthening of an existing column by reinforced concrete jacketing, increasing its section with a perimeter layer of concrete with its own reinforcement, tied to the original core. Includes shoring the structure beforehand to take the load off the column, hacking the existing surface to provide a bond, drilling and chemically anchoring the dowels that stitch the jacket to the core, the longitudinal reinforcement and the confinement stirrups, the formwork, pouring with shrinkage-compensating concrete or a fluid mortar given the small thickness, curing and the staged removal of the shoring. Measured by the length of column actually jacketed.",

"Anclaje de barra de acero en elemento de concreto existente mediante resina epóxica bicomponente inyectada en perforación, para conexión de elementos nuevos a la estructura existente. Incluye el replanteo del punto evitando la armadura existente mediante detección previa, la perforación con el diámetro y la profundidad especificados por el fabricante de la resina, la limpieza del taladro mediante soplado y cepillado repetidos, operación de la que depende por completo la capacidad del anclaje y que es la que más se omite en obra, la inyección de la resina desde el fondo, la introducción de la barra con giro y el respeto del tiempo de curado antes de cargarla. Medido por unidad realmente ejecutada.":
    "Anchoring of a steel bar into an existing concrete element with two-component epoxy resin injected into the hole, to connect new elements to the existing structure. Includes setting out the point and avoiding the existing reinforcement by scanning beforehand, drilling to the diameter and depth specified by the resin manufacturer, cleaning the hole by repeated blowing out and brushing, the operation on which the capacity of the anchor depends entirely and the one most often skipped on site, injecting the resin from the bottom, inserting the bar with a twisting motion and respecting the curing time before loading it. Measured per unit actually constructed.",

"Refuerzo de losa o viga de concreto mediante perfil metálico dispuesto bajo el elemento, conectado con anclajes químicos y con mortero de nivelación en el contacto. Es la solución más rápida cuando hay que aumentar la capacidad de un losa existente sin engrosarlo por arriba. Incluye el apeo previo del elemento a reforzar, la nivelación de la cara inferior, la perforación y anclaje químico, el izado y presentado del perfil, el relleno del contacto con grout sin retracción que garantiza la transmisión de carga, ya que un perfil que no toca no refuerza, el apriete de los anclajes y la protección anticorrosiva. Medido en longitud de refuerzo realmente ejecutada.":
    "Strengthening of a concrete slab or beam with a steel section placed beneath the element, connected with chemical anchors and with a leveling mortar at the interface. It is the quickest solution when the capacity of an existing slab has to be increased without thickening it from above. Includes shoring the element to be strengthened beforehand, leveling the soffit, drilling and chemical anchoring, hoisting and offering up the section, filling the interface with non-shrink grout to guarantee the transfer of load, since a section that does not bear does not strengthen, tightening the anchors and anti-corrosion protection. Measured by the length of strengthening actually constructed.",

"Reparación superficial de concreto con mortero estructural. Incluye el saneo y la reparación. Medido por metro cuadrado reparado.":
    "Surface repair of concrete with a structural mortar. Includes cutting out and repair. Measured per square meter repaired.",
"Tratamiento pasivante de acero de refuerzo corroído. Incluye la limpieza y el tratamiento. Medido por metro cuadrado tratado.":
    "Passivating treatment of corroded reinforcement. Includes cleaning and treatment. Measured per square meter treated.",
"Inyección de fisuras en concreto con resina epóxica. Incluye la inyección. Medido por metro lineal inyectado.":
    "Injection of cracks in concrete with epoxy resin. Includes injection. Measured per meter injected.",
"Refuerzo estructural con tejido de fibra de carbono. Incluye la aplicación. Medido por metro cuadrado reforzado.":
    "Structural strengthening with carbon fiber fabric. Includes application. Measured per square meter strengthened.",
"Encamisado de columna de concreto armado. Incluye el armado y el vaciado. Medido por metro cuadrado encamisado.":
    "Reinforced concrete jacketing of a column. Includes reinforcement and pouring. Measured per square meter jacketed.",
"Refuerzo de losa o viga con perfil metálico. Incluye el montaje del refuerzo. Medido por metro cuadrado reforzado.":
    "Strengthening of a slab or beam with a steel section. Includes installing the strengthening. Measured per square meter strengthened.",
"Refuerzo de viga con lámina de fibra de carbono. Incluye la aplicación. Medido por metro cuadrado reforzado.":
    "Strengthening of a beam with a carbon fiber plate. Includes application. Measured per square meter strengthened.",
"Reparación de losa con mortero estructural. Incluye el saneo y la reparación. Medido por metro cuadrado reparado.":
    "Repair of a slab with a structural mortar. Includes cutting out and repair. Measured per square meter repaired.",
"Refuerzo de muro con encamisado de concreto. Incluye el armado y el vaciado. Medido por metro cuadrado reforzado.":
    "Strengthening of a wall with concrete jacketing. Includes reinforcement and pouring. Measured per square meter strengthened.",
"Refuerzo con mortero de alta resistencia. Incluye la aplicación. Medido por metro cuadrado reforzado.":
    "Strengthening with a high strength mortar. Includes application. Measured per square meter strengthened.",
"Reparación de columna con mortero estructural. Incluye el saneo y la reparación. Medido por metro cuadrado reparado.":
    "Repair of a column with a structural mortar. Includes cutting out and repair. Measured per square meter repaired.",
"Refuerzo de losa con lámina de fibra de carbono. Incluye la aplicación. Medido por metro cuadrado reforzado.":
    "Strengthening of a slab with a carbon fiber plate. Includes application. Measured per square meter strengthened.",
"Refuerzo de estructura con perfil metálico. Incluye el montaje del refuerzo. Medido por metro cuadrado reforzado.":
    "Strengthening of a structure with steel sections. Includes installing the strengthening. Measured per square meter strengthened.",
"Reparación de viga con mortero estructural. Incluye el saneo y la reparación. Medido por metro cuadrado reparado.":
    "Repair of a beam with a structural mortar. Includes cutting out and repair. Measured per square meter repaired.",
"Refuerzo de columna con lámina de fibra de carbono. Incluye la aplicación. Medido por metro cuadrado reforzado.":
    "Strengthening of a column with a carbon fiber plate. Includes application. Measured per square meter strengthened.",
"Reparación de muro estructural con mortero. Incluye el saneo y la reparación. Medido por metro cuadrado reparado.":
    "Repair of a structural wall with mortar. Includes cutting out and repair. Measured per square meter repaired.",
"Refuerzo integral de estructura con combinación de técnicas. Incluye la reparación y el refuerzo. Medido por metro cuadrado reforzado.":
    "Integral strengthening of a structure combining techniques. Includes repair and strengthening. Measured per square meter strengthened.",
}
