# -*- coding: utf-8 -*-
"""Descripciones — Carpintería, herrería, vidrios y protección solar
(capítulo completo, 180).

Criterios de este lote:
  · «Batiente» es casement, «proyectante» es awning window y
    «oscilobatiente» es tilt and turn: tres nombres distintos para tres
    formas de abrir, no tres sinónimos.
  · «Paño fijo» es fixed light. «Junquillo» es glazing bead y el «galce»
    es rabbet en el Reino Unido y rabbet en los Estados Unidos.
  · «Reja» es grille, «barrotes» son bars y la «forja» es wrought iron.
  · «Baranda» es guardrail, que protege, frente a «pasamanos» es
    handrail, que se agarra: en inglés nunca son la misma palabra.
  · «Puerta levadiza» de garaje es up-and-over door en el Reino Unido y
    overhead door en los Estados Unidos.
  · «Burlete» es weatherstripping y draught seal; «mirilla» es peephole y
    «barra antipánico» es panic bar.
  · El vidrio «templado» es tempered glass y no admite ni un corte ni un
    taladro después del temple: todo se define antes de fabricar.
  · «Espejo» con adhesivo ácido se mancha: el adhesivo tiene que ser
    neutro porque el ácido ataca la plata del reverso.
"""

LOTE = {
# ── Puertas interiores ────────────────────────────────────────────────────
"Instalación de puerta de paso interior con su marco, molduras de remate y herrajes de colgar. Incluye la comprobación previa de que el vano está aplomado y a escuadra, sin lo cual la puerta nunca cerrará bien por mucho que se ajuste, el montaje y aplomado del marco con cuñas, su fijación y el relleno del espacio perimetral con espuma o mortero, la colocación de las molduras, el colgado de la hoja con sus bisagras, el ajuste de holguras uniformes y la comprobación de que la hoja se mantiene en cualquier posición. La puerta la elige el cliente y se presupuesta aparte. Medido por unidad instalada.":
    "Installation of an internal passage door with its frame, door casing and hanging hardware. Includes the prior check that the opening is plumb and square, without which the door will never shut properly however much it is adjusted, erecting and plumbing the frame on shims, fastening it and filling the perimeter gap with foam or mortar, fitting the door casing, hanging the leaf on its hinges, adjusting to even reveals and checking that the leaf stays put in any position. The door is selected by the client and priced separately. Measured per unit installed.",

"Instalación de puerta corrediza interior, vista sobre el paramento o embutida en tabique, con su riel, carros y guías. Incluye la comprobación del refuerzo del paramento donde se ancla el riel, que debe soportar el peso de la hoja en voladizo, el montaje y nivelación del riel, el colgado de la hoja con sus carros, la colocación de la guía inferior, el ajuste del recorrido y de los topes, y la comprobación de que la hoja desliza sin rozar en todo el recorrido. La puerta la elige el cliente y se presupuesta aparte. Medido por unidad instalada.":
    "Installation of an internal sliding door, running on the face of the wall or recessed into the partition, with its track, carriers and guides. Includes checking the strengthening of the wall where the track is anchored, since it has to carry the weight of the leaf hung from it, erecting and leveling the track, hanging the leaf on its carriers, fitting the bottom guide, adjusting the travel and the stops, and checking that the leaf slides without dragging over the whole run. The door is selected by the client and priced separately. Measured per unit installed.",

"Instalación de cerradura de embutir con su manija, cilindro y placas, o de herrajes de superficie según el tipo. Incluye el replanteo de la altura normalizada, el mecanizado del alojamiento en la hoja y del cajetín en el marco, el montaje de la cerradura con su frente enrasado, la colocación de manijas y cilindro, el ajuste del picaporte contra el cajetín y la comprobación del cierre y del giro de la llave sin forzar. Medido por unidad instalada.":
    "Installation of a mortise lock with its lever handle, cylinder and plates, or of surface mounted hardware according to the type. Includes field layout at the standard height, mortising the housing in the leaf and the strike plate in the frame, fitting the lock with its faceplate flush, fitting the handles and the cylinder, adjusting the latch against the strike plate and checking that it locks and that the key turns without forcing. Measured per unit installed.",

"Suministro e instalación de puerta de closet abatible o plegable, con sus herrajes, guías y tiradores. Incluye el replanteo y comprobación de las dimensiones reales del hueco, el montaje de las guías y herrajes, el colgado de las hojas, el ajuste de holguras y de la alineación de los frentes cerrados, que es lo que determina el aspecto final del conjunto, y la colocación de tiradores y topes. Medido en superficie realmente ejecutada.":
    "Supply and installation of a hinged or folding closet door, with its hardware, guides and pulls. Includes field layout and checking the actual dimensions of the opening, fitting the guides and hardware, hanging the leaves, adjusting the reveals and the alignment of the closed fronts, which is what determines the final appearance of the whole, and fitting the pulls and stops. Measured by the area actually completed.",

"Instalación de puerta de baño en PVC o aluminio con su marco y herrajes, apta para ambiente húmedo. Frente a la puerta de madera resuelve el problema del hinchamiento y la delaminación del canto inferior por el vapor y el agua de limpieza, que es el fallo típico de las puertas de baño de madera. Incluye la comprobación del vano, el montaje y aplomado del marco, el anclaje, el sellado perimetral, el colgado de la hoja, el ajuste de holguras y el montaje de la cerradura con condena. La puerta la elige el cliente y se presupuesta aparte. Medido por unidad instalada.":
    "Installation of a PVC or aluminum bathroom door with its frame and hardware, suitable for a wet environment. Against a wood door it solves the swelling and delamination of the bottom edge caused by steam and cleaning water, which is the classic failure of wood bathroom doors. Includes checking the opening, erecting and plumbing the frame, anchoring, sealing the perimeter, hanging the leaf, adjusting the reveals and fitting the lock with a privacy turn. The door is selected by the client and priced separately. Measured per unit installed.",

"Suministro y montaje de marco y contramarco metálico en vano de puerta, embebido en la mampostería o anclado al paramento. El contramarco se coloca durante el levantamiento de la pared y queda embebido, de modo que su replanteo y aplomado condicionan toda la carpintería posterior: un contramarco mal aplomado no se corrige después. Incluye el replanteo, el aplomado y arriostramiento provisional, el macizado de las patillas en la fábrica, la protección anticorrosiva y el montaje del marco definitivo. Medido en longitud de perímetro de vano.":
    "Supply and installation of a metal frame and subframe to a door opening, cast into the masonry or anchored to the wall. The subframe is placed as the wall is built and ends up cast in, so its field layout and plumb condition all the carpentry that follows: a subframe that is out of plumb cannot be put right afterwards. Includes field layout, plumbing with temporary bracing, bedding the fastening lugs into the masonry, the anti-corrosion protection and fitting the final frame. Measured by the perimeter length of the opening.",

"Instalación de cerradura electrónica o inteligente en puerta existente, con su mecanizado, montaje, configuración y prueba. Incluye la verificación previa de la compatibilidad del espesor de la hoja y de la distancia del eje, la adaptación del mecanizado existente, el montaje del cuerpo y de los lectores interior y exterior, la conexión de la alimentación, la configuración de usuarios y códigos, la comprobación del funcionamiento del sistema mecánico de emergencia, que debe seguir operando aunque falle la batería, y la entrega al cliente con su instrucción de uso. La cerradura la elige el cliente y se presupuesta aparte. Medido por unidad instalada.":
    "Installation of an electronic or smart lock to an existing door, with its mortising, fitting, configuration and testing. Includes verifying beforehand that it is compatible with the thickness of the leaf and the backset, adapting the existing mortising, fitting the body and the internal and external readers, connecting the power supply, setting up the users and the codes, checking the operation of the mechanical emergency override, which must still work even if the battery fails, and handing over to the client with the operating instructions. The lock is selected by the client and priced separately. Measured per unit installed.",

"Suministro y colocación de puerta interior de madera maciza con su marco y herrajes. Incluye el replanteo, el montaje del marco, la colocación de la hoja y el ajuste de herrajes. Medido por unidad instalada.":
    "Supply and installation of a solid wood internal door with its frame and hardware. Includes field layout, erecting the frame, hanging the leaf and adjusting the hardware. Measured per unit installed.",
"Suministro y colocación de puerta interior enchapada en melamina con marco y herrajes. Incluye el montaje del marco, la colocación de la hoja y el ajuste. Medido por unidad instalada.":
    "Supply and installation of a melamine faced internal door with frame and hardware. Includes erecting the frame, hanging the leaf and adjustment. Measured per unit installed.",
"Suministro y colocación de puerta interior lacada en blanco con marco y herrajes. Incluye el montaje del marco, la colocación de la hoja y el ajuste de herrajes. Medido por unidad instalada.":
    "Supply and installation of a white lacquered internal door with frame and hardware. Includes erecting the frame, hanging the leaf and adjusting the hardware. Measured per unit installed.",
"Suministro y colocación de puerta de vaivén de dos hojas para cocina o área de servicio, con marco y herrajes de vaivén. Incluye el montaje y el ajuste del mecanismo. Medido por unidad instalada.":
    "Supply and installation of a double leaf swing door for a kitchen or service area, with frame and double acting hardware. Includes fitting and adjusting the mechanism. Measured per unit installed.",
"Suministro y colocación de puerta doble de madera para sala o acceso principal interior, con marco y herrajes. Incluye el montaje del marco y la colocación de las dos hojas. Medido por unidad instalada.":
    "Supply and installation of a double wood door for a living room or main internal access, with frame and hardware. Includes erecting the frame and hanging both leaves. Measured per unit installed.",
"Suministro y colocación de puerta de closet corrediza de madera o melamina, con riel y herrajes. Incluye el montaje del riel y la colocación de las hojas. Medido por unidad instalada.":
    "Supply and installation of a wood or melamine sliding closet door, with track and hardware. Includes fitting the track and hanging the leaves. Measured per unit installed.",
"Suministro y colocación de puerta plegable de PVC para closet, con riel y herrajes. Incluye el montaje del riel y la colocación de los paneles. Medido por unidad instalada.":
    "Supply and installation of a PVC folding closet door, with track and hardware. Includes fitting the track and hanging the panels. Measured per unit installed.",
"Suministro y colocación de puerta interior de vidrio templado sin marco, con herrajes de pivote o bisagra. Incluye el montaje de los herrajes y la colocación del vidrio. Medido por unidad instalada.":
    "Supply and installation of a frameless internal tempered glass door, with pivot or hinge fittings. Includes fitting the hardware and installing the glass. Measured per unit installed.",
"Suministro y colocación de puerta interior de madera con panel de vidrio, con marco y herrajes. Incluye el montaje del marco, la colocación de la hoja y el ajuste. Medido por unidad instalada.":
    "Supply and installation of a wood internal door with a glazed panel, with frame and hardware. Includes erecting the frame, hanging the leaf and adjustment. Measured per unit installed.",
"Suministro y colocación de marco de madera para puerta interior, con montaje a plomo y recibido. Incluye el replanteo, el montaje y el recibido del marco. Medido por unidad instalada.":
    "Supply and installation of a wood frame for an internal door, erected plumb and bedded. Includes field layout, erection and bedding the frame. Measured per unit installed.",
"Suministro y colocación de puerta de closet abatible de melamina, con bisagras y herrajes. Incluye el montaje de las hojas y el ajuste de bisagras. Medido por unidad instalada.":
    "Supply and installation of a hinged melamine closet door, with hinges and hardware. Includes hanging the leaves and adjusting the hinges. Measured per unit installed.",
"Suministro y colocación de puerta interior de MDF pintado, con marco y herrajes. Incluye el montaje del marco, la colocación de la hoja y el ajuste. Medido por unidad instalada.":
    "Supply and installation of a painted MDF internal door, with frame and hardware. Includes erecting the frame, hanging the leaf and adjustment. Measured per unit installed.",
"Suministro y colocación de puerta plegable de madera para espacios reducidos, con riel y herrajes. Incluye el montaje del riel y la colocación de los paneles plegables. Medido por unidad instalada.":
    "Supply and installation of a wood folding door for confined spaces, with track and hardware. Includes fitting the track and hanging the folding panels. Measured per unit installed.",
"Suministro y colocación de puerta interior con rejilla de ventilación, con marco y herrajes. Incluye el montaje del marco, la colocación de la hoja y la rejilla. Medido por unidad instalada.":
    "Supply and installation of an internal door with a ventilation grille, with frame and hardware. Includes erecting the frame, hanging the leaf and the grille. Measured per unit installed.",
"Suministro y colocación de puerta de cocina con celosía superior de ventilación, con marco y herrajes. Incluye el montaje y el ajuste. Medido por unidad instalada.":
    "Supply and installation of a kitchen door with a louvered ventilation panel over, with frame and hardware. Includes fitting and adjustment. Measured per unit installed.",
"Suministro y colocación de puerta interior corrediza de vidrio templado, con riel y herrajes. Incluye el montaje del riel y la colocación del vidrio. Medido por unidad instalada.":
    "Supply and installation of an internal sliding tempered glass door, with track and fittings. Includes fitting the track and installing the glass. Measured per unit installed.",
"Suministro y colocación de puerta interior con bisagras ocultas, con marco y herrajes. Incluye el montaje del marco, la colocación de la hoja y el ajuste de bisagras. Medido por unidad instalada.":
    "Supply and installation of an internal door with concealed hinges, with frame and hardware. Includes erecting the frame, hanging the leaf and adjusting the hinges. Measured per unit installed.",
"Suministro y colocación de puerta interior de acero galvanizado, con marco metálico y herrajes. Incluye el montaje del marco y la colocación de la hoja. Medido por unidad instalada.":
    "Supply and installation of a galvanized steel internal door, with a metal frame and hardware. Includes erecting the frame and hanging the leaf. Measured per unit installed.",

# ── Puertas exteriores y de seguridad ─────────────────────────────────────
"Instalación de puerta metálica exterior o de seguridad con su marco, anclajes y cerradura. Por su peso requiere dos operarios y anclaje mecánico al muro, no espuma. Incluye la comprobación del vano, el presentado y aplomado del marco con cuñas, el taladrado y anclaje mecánico en los puntos previstos, el macizado del perímetro con mortero, el colgado y ajuste de la hoja, el montaje de la cerradura de seguridad y la comprobación del cierre en los tres puntos. La puerta la elige el cliente y se presupuesta aparte. Medido por unidad instalada.":
    "Installation of an external metal or security door with its frame, anchors and lock. Given its weight it needs two operatives and mechanical anchoring to the wall, not foam. Includes checking the opening, offering up and plumbing the frame on shims, drilling and mechanical anchoring at the points specified, bedding the perimeter in mortar, hanging and adjusting the leaf, fitting the security lock and checking the three-point locking. The door is selected by the client and priced separately. Measured per unit installed.",

"Instalación de puerta de entrada principal de madera maciza con su marco reforzado, herrajes y cerradura de seguridad. Incluye la comprobación y preparación del vano, el montaje y aplomado del marco con anclaje mecánico, el macizado perimetral, el colgado de la hoja con bisagras reforzadas dimensionadas para su peso, el ajuste de holguras, la colocación de burletes y del umbral, el montaje de la cerradura y la aplicación de protección en el canto inferior y en las testas, que son por donde la madera absorbe humedad y se hincha. La puerta la elige el cliente y se presupuesta aparte. Medido por unidad instalada.":
    "Installation of a solid wood main entrance door with its reinforced frame, hardware and security lock. Includes checking and preparing the opening, erecting and plumbing the frame with mechanical anchoring, bedding the perimeter, hanging the leaf on reinforced hinges sized for its weight, adjusting the reveals, fitting the weatherstripping and the threshold, fitting the lock and applying protection to the bottom edge and to the end grain, which is where wood takes up moisture and swells. The door is selected by the client and priced separately. Measured per unit installed.",

"Suministro y colocación de puerta principal de madera maciza con marco y cerradura de seguridad. Incluye el montaje del marco, la colocación de la hoja y la instalación de la cerradura. Medido por unidad instalada.":
    "Supply and installation of a solid wood main entrance door with frame and security lock. Includes erecting the frame, hanging the leaf and fitting the lock. Measured per unit installed.",
"Suministro y colocación de puerta blindada de seguridad con cerradura multipunto. Incluye el montaje del marco, la colocación de la hoja y el ajuste de la cerradura. Medido por unidad instalada.":
    "Supply and installation of a security door with a multi-point lock. Includes erecting the frame, hanging the leaf and adjusting the lock. Measured per unit installed.",
"Suministro y colocación de puerta exterior de aluminio con vidrio templado y herrajes. Incluye el montaje del marco, la colocación de la hoja y el acristalamiento. Medido por unidad instalada.":
    "Supply and installation of an external aluminum door with tempered glass and hardware. Includes erecting the frame, hanging the leaf and the glazing. Measured per unit installed.",
"Suministro y colocación de puerta de acero para entrada de servicio, con marco metálico y cerradura. Incluye el montaje y la colocación de la hoja. Medido por unidad instalada.":
    "Supply and installation of a steel door for a service entrance, with a metal frame and lock. Includes fitting and hanging the leaf. Measured per unit installed.",
"Suministro y colocación de puerta exterior de PVC con marco y herrajes. Incluye el montaje del marco y la colocación de la hoja. Medido por unidad instalada.":
    "Supply and installation of an external PVC door with frame and hardware. Includes erecting the frame and hanging the leaf. Measured per unit installed.",
"Suministro y colocación de puerta de entrada con espejo o mirilla de seguridad. Incluye el montaje del marco, la colocación de la hoja y la instalación de la mirilla. Medido por unidad instalada.":
    "Supply and installation of an entrance door with a mirror or peephole. Includes erecting the frame, hanging the leaf and fitting the peephole. Measured per unit installed.",
"Suministro y colocación de puerta de acceso con cierra-puertas hidráulico. Incluye el montaje de la hoja, el cierra-puertas y el ajuste de velocidad. Medido por unidad instalada.":
    "Supply and installation of an access door with a hydraulic door closer. Includes hanging the leaf, the door closer and adjusting the closing speed. Measured per unit installed.",
"Suministro y colocación de puerta de reja de acceso con cerradura y herrajes. Incluye el montaje de la reja y la instalación de la cerradura. Medido por unidad instalada.":
    "Supply and installation of an access grille gate with lock and hardware. Includes hanging the grille and fitting the lock. Measured per unit installed.",
"Suministro y colocación de puerta de acceso de acero inoxidable con marco y herrajes. Incluye el montaje del marco y la colocación de la hoja. Medido por unidad instalada.":
    "Supply and installation of a stainless steel access door with frame and hardware. Includes erecting the frame and hanging the leaf. Measured per unit installed.",
"Suministro y colocación de puerta de acceso con barra antipánico. Incluye el montaje de la hoja, la barra antipánico y el ajuste. Medido por unidad instalada.":
    "Supply and installation of an access door with a panic bar. Includes hanging the leaf, the panic bar and adjustment. Measured per unit installed.",
"Suministro y colocación de puerta de acceso con cerradura electrónica de teclado o huella. Incluye el montaje de la hoja y la instalación y programación de la cerradura. Medido por unidad instalada.":
    "Supply and installation of an access door with an electronic keypad or fingerprint lock. Includes hanging the leaf and the installation and programming of the lock. Measured per unit installed.",
"Suministro y colocación de puerta de acceso de madera con panel de vidrio de seguridad. Incluye el montaje del marco, la colocación de la hoja y el acristalamiento. Medido por unidad instalada.":
    "Supply and installation of a wood access door with a safety glass panel. Includes erecting the frame, hanging the leaf and the glazing. Measured per unit installed.",
"Suministro y colocación de puerta de acceso con montante lateral de vidrio fijo. Incluye el montaje del marco, la colocación de la hoja y el montante acristalado. Medido por unidad instalada.":
    "Supply and installation of an access door with a fixed glazed side panel. Includes erecting the frame, hanging the leaf and the glazed side panel. Measured per unit installed.",
"Suministro y colocación de puerta de acceso con dintel de vidrio fijo. Incluye el montaje del marco, la colocación de la hoja y el dintel acristalado. Medido por unidad instalada.":
    "Supply and installation of an access door with a fixed glazed transom. Includes erecting the frame, hanging the leaf and the glazed transom. Measured per unit installed.",
"Suministro y colocación de puerta de acceso de madera con doble cerradura de seguridad. Incluye el montaje de la hoja y la instalación de las dos cerraduras. Medido por unidad instalada.":
    "Supply and installation of a wood access door with two security locks. Includes hanging the leaf and fitting both locks. Measured per unit installed.",
"Suministro y colocación de puerta de acceso de madera con mirilla de seguridad. Incluye el montaje de la hoja y la instalación de la mirilla. Medido por unidad instalada.":
    "Supply and installation of a wood access door with a peephole. Includes hanging the leaf and fitting the peephole. Measured per unit installed.",
"Suministro y colocación de puerta de acceso de madera con refuerzo metálico de seguridad. Incluye el montaje de la hoja, el refuerzo y la cerradura. Medido por unidad instalada.":
    "Supply and installation of a wood access door with a metal security reinforcement. Includes hanging the leaf, the reinforcement and the lock. Measured per unit installed.",

# ── Ventanas ──────────────────────────────────────────────────────────────
"Suministro e instalación de ventana de aluminio corrediza con su marco, hojas, rieles, felpas y acristalamiento. Incluye la toma de medidas en obra del vano ya terminado, nunca del plano, porque la diferencia entre ambos es la causa habitual de ventanas que no entran, el montaje y aplomado del marco con cuñas, el anclaje mecánico, el sellado perimetral exterior con silicona neutra que impide la entrada de agua, el montaje de las hojas, el ajuste de rodamientos y felpas y la comprobación de deslizamiento y cierre. Medido en superficie realmente ejecutada.":
    "Supply and installation of an aluminum sliding window with its frame, sashes, tracks, brush seals and glazing. Includes measuring the finished opening on site, never from the drawing, because the difference between the two is the usual cause of windows that do not fit, erecting and plumbing the frame on shims, mechanical anchoring, sealing the external perimeter with neutral silicone to keep water out, fitting the sashes, adjusting the rollers and brush seals and checking the sliding and the closing. Measured by the area actually completed.",

"Suministro e instalación de ventana de aluminio batiente o proyectante con su marco, hojas, herrajes de apertura y acristalamiento. Frente a la corrediza ofrece mucha mejor estanqueidad al agua y al aire por la compresión de la junta al cerrar, a costa de necesitar espacio de barrido. Incluye la toma de medidas en obra, el montaje y aplomado del marco, el anclaje mecánico, el sellado perimetral, el montaje de las hojas con sus herrajes, el ajuste de la compresión del cierre en todos los puntos y la comprobación de estanqueidad. Medido en superficie realmente ejecutada.":
    "Supply and installation of an aluminum casement or awning window with its frame, sashes, opening hardware and glazing. Against the sliding type it gives far better resistance to water and air because the gasket is compressed on closing, at the cost of needing clear space for the sash to swing. Includes measuring on site, erecting and plumbing the frame, mechanical anchoring, sealing the perimeter, fitting the sashes with their hardware, adjusting the compression of the closing at every point and checking the weathertightness. Measured by the area actually completed.",

"Suministro e instalación de paño fijo de aluminio y vidrio, sin hojas practicables. Incluye la toma de medidas en obra, el montaje y aplomado del marco, el anclaje, el acristalamiento con sus calzos de apoyo y laterales que reparten el peso del vidrio sin transmitirle tensiones puntuales, el acuñado, el sellado perimetral y la limpieza. En paños de gran superficie se verifica el espesor del vidrio conforme a su dimensión y exposición al viento. Medido en superficie realmente ejecutada.":
    "Supply and installation of a fixed aluminum and glass light, without opening sashes. Includes measuring on site, erecting and plumbing the frame, anchoring, glazing with the setting blocks and side blocks that distribute the weight of the glass without transmitting point stresses to it, wedging, sealing the perimeter and cleaning. On large lights the glass thickness is verified against its size and exposure to wind. Measured by the area actually completed.",

"Suministro y colocación de mosquitero con bastidor de aluminio y malla, fijo o corredizo según el tipo de ventana. Incluye la toma de medidas, el montaje del bastidor con la malla tensada sin arrugas, la colocación de las guías o clips de sujeción y la comprobación del ajuste perimetral, ya que una holgura de pocos milímetros anula por completo su función. Medido en superficie realmente ejecutada.":
    "Supply and installation of an insect screen with an aluminum frame and mesh, fixed or sliding according to the type of window. Includes measuring, assembling the frame with the mesh stretched free of creases, fitting the guides or retaining clips and checking the fit around the perimeter, since a gap of a few millimetres defeats its purpose entirely. Measured by the area actually completed.",

"Suministro e instalación de ventana de PVC con refuerzo interior de acero, sus hojas, herrajes y acristalamiento. Frente al aluminio ofrece mejor comportamiento térmico y acústico y no transmite condensación al marco, aunque exige refuerzo interior en hojas grandes porque el perfil por sí solo no tiene rigidez suficiente. Incluye la toma de medidas en obra, el montaje y aplomado del marco, el anclaje mecánico, el sellado perimetral exterior, el montaje de hojas y herrajes, el ajuste de la compresión del cierre y la comprobación de estanqueidad. Medido en superficie realmente ejecutada.":
    "Supply and installation of a PVC window with internal steel reinforcement, its sashes, hardware and glazing. Against aluminum it gives better thermal and acoustic performance and does not pass condensation to the frame, although it needs internal reinforcement on large sashes because the profile on its own has not enough stiffness. Includes measuring on site, erecting and plumbing the frame, mechanical anchoring, sealing the external perimeter, fitting the sashes and hardware, adjusting the compression of the closing and checking the weathertightness. Measured by the area actually completed.",

"Suministro e instalación de celosía o romanilla de aluminio para ventilación permanente, con su marco y malla antiinsectos. Es un elemento muy usado en clima tropical para ventilar cuartos de servicio, depósitos y baños sin ventana practicable. Incluye la toma de medidas del vano, el montaje y aplomado del marco, el anclaje, el sellado perimetral, la colocación de la malla antiinsectos por la cara interior y la comprobación de la sección libre de ventilación. Medido en superficie realmente ejecutada.":
    "Supply and installation of an aluminum louver screen for permanent ventilation, with its frame and insect mesh. It is an element widely used in a tropical climate to ventilate laundry rooms, stores and bathrooms that have no opening window. Includes measuring the opening, erecting and plumbing the frame, anchoring, sealing the perimeter, fitting the insect mesh on the inside face and checking the free ventilation area. Measured by the area actually completed.",

"Suministro y colocación de ventana de aluminio con doble acristalamiento. Incluye el montaje del marco, la colocación de la ventana y el sellado perimetral. Medido por metro cuadrado instalado.":
    "Supply and installation of an aluminum window with double glazing. Includes erecting the frame, installing the window and sealing the perimeter. Measured per square meter installed.",
"Suministro y colocación de ventana de aluminio con vidrio laminado de seguridad. Incluye el montaje del marco, el acristalamiento y el sellado. Medido por metro cuadrado instalado.":
    "Supply and installation of an aluminum window with safety laminated glass. Includes erecting the frame, the glazing and sealing. Measured per square meter installed.",
"Suministro y colocación de ventana de aluminio corrediza con mosquitero integrado. Incluye el montaje del marco, el acristalamiento y el mosquitero. Medido por metro cuadrado instalado.":
    "Supply and installation of an aluminum sliding window with an integrated insect screen. Includes erecting the frame, the glazing and the screen. Measured per square meter installed.",
"Suministro y colocación de balconera de aluminio corrediza con vidrio templado. Incluye el montaje del marco, el acristalamiento y el sellado. Medido por metro cuadrado instalado.":
    "Supply and installation of an aluminum sliding patio door with tempered glass. Includes erecting the frame, the glazing and sealing. Measured per square meter installed.",
"Suministro y colocación de ventana de PVC con doble acristalamiento. Incluye el montaje del marco, el acristalamiento y el sellado. Medido por metro cuadrado instalado.":
    "Supply and installation of a PVC window with double glazing. Includes erecting the frame, the glazing and sealing. Measured per square meter installed.",
"Suministro y colocación de ventana de madera con vidrio y herrajes. Incluye el montaje del marco, el acristalamiento y el sellado. Medido por metro cuadrado instalado.":
    "Supply and installation of a wood window with glass and hardware. Includes erecting the frame, the glazing and sealing. Measured per square meter installed.",
"Suministro y colocación de paño fijo de vidrio templado en fachada, con perfil de fijación. Incluye el montaje del perfil, el acristalamiento y el sellado. Medido por metro cuadrado instalado.":
    "Supply and installation of a fixed tempered glass light in a facade, with a fastening profile. Includes fitting the profile, the glazing and sealing. Measured per square meter installed.",
"Suministro y colocación de ventana proyectante de aluminio con vidrio. Incluye el montaje del marco, el acristalamiento y el sellado. Medido por metro cuadrado instalado.":
    "Supply and installation of an aluminum awning window with glass. Includes erecting the frame, the glazing and sealing. Measured per square meter installed.",
"Suministro y colocación de ventana oscilobatiente de aluminio con vidrio. Incluye el montaje del marco, el acristalamiento y el ajuste del mecanismo. Medido por metro cuadrado instalado.":
    "Supply and installation of an aluminum tilt and turn window with glass. Includes erecting the frame, the glazing and adjusting the mechanism. Measured per square meter installed.",
"Suministro y colocación de ventana de aluminio con rejilla de ventilación integrada. Incluye el montaje del marco, el acristalamiento y la rejilla. Medido por metro cuadrado instalado.":
    "Supply and installation of an aluminum window with an integrated ventilation grille. Includes erecting the frame, the glazing and the grille. Measured per square meter installed.",
"Suministro y colocación de ventana de aluminio a una hoja batiente con vidrio. Incluye el montaje del marco, el acristalamiento y el sellado. Medido por metro cuadrado instalado.":
    "Supply and installation of a single casement aluminum window with glass. Includes erecting the frame, the glazing and sealing. Measured per square meter installed.",
"Suministro y colocación de ventana de madera con celosía de ventilación. Incluye el montaje del marco, el acristalamiento y la celosía. Medido por metro cuadrado instalado.":
    "Supply and installation of a wood window with a louvered ventilation panel. Includes erecting the frame, the glazing and the louvers. Measured per square meter installed.",
"Suministro y colocación de ventana de aluminio a dos hojas corredizas con vidrio. Incluye el montaje del marco, el acristalamiento y el sellado. Medido por metro cuadrado instalado.":
    "Supply and installation of a two sash sliding aluminum window with glass. Includes erecting the frame, the glazing and sealing. Measured per square meter installed.",
"Suministro y colocación de ventana fija de aluminio para local o escaparate. Incluye el montaje del marco, el acristalamiento y el sellado. Medido por metro cuadrado instalado.":
    "Supply and installation of a fixed aluminum window for a shop or a shopfront. Includes erecting the frame, the glazing and sealing. Measured per square meter installed.",
"Suministro y colocación de ventana de aluminio con vidrio esmerilado para privacidad. Incluye el montaje del marco, el acristalamiento y el sellado. Medido por metro cuadrado instalado.":
    "Supply and installation of an aluminum window with frosted glass for privacy. Includes erecting the frame, the glazing and sealing. Measured per square meter installed.",
"Suministro y colocación de ventana de madera corrediza con vidrio. Incluye el montaje del marco, el acristalamiento y el sellado. Medido por metro cuadrado instalado.":
    "Supply and installation of a sliding wood window with glass. Includes erecting the frame, the glazing and sealing. Measured per square meter installed.",
"Suministro y colocación de ventana de PVC corrediza con vidrio. Incluye el montaje del marco, el acristalamiento y el sellado. Medido por metro cuadrado instalado.":
    "Supply and installation of a sliding PVC window with glass. Includes erecting the frame, the glazing and sealing. Measured per square meter installed.",
"Suministro y colocación de ventana de aluminio con apertura a proyección y vidrio. Incluye el montaje del marco, el acristalamiento y el ajuste del mecanismo. Medido por metro cuadrado instalado.":
    "Supply and installation of an aluminum window opening as an awning, with glass. Includes erecting the frame, the glazing and adjusting the mechanism. Measured per square meter installed.",

# ── Rejas y herrería ──────────────────────────────────────────────────────
"Fabricación y montaje de reja de protección metálica con su bastidor y barrotes, anclada al muro. Incluye el replanteo y la toma de medidas en obra, la fabricación del bastidor con sus barrotes a la separación acordada, el tratamiento anticorrosivo, el presentado y anclaje mecánico al muro con pernos embebidos o resina, el resane de los puntos de anclaje y la aplicación de la imprimación y del acabado. En dormitorios conviene prever al menos un paño practicable desde el interior como salida de emergencia. Medido en superficie realmente ejecutada.":
    "Manufacture and installation of a metal security grille with its frame and bars, anchored to the wall. Includes field layout and measuring on site, fabricating the frame with its bars at the spacing agreed, the anti-corrosion treatment, offering up and mechanical anchoring to the wall with cast-in bolts or resin, patching the anchor points and applying the primer and the finish. In bedrooms at least one panel should be openable from the inside as an emergency exit. Measured by the area actually completed.",

"Fabricación y montaje de portón de reja abatible para acceso peatonal o vehicular, con su bastidor, bisagras reforzadas, pasador y cerradura. Incluye la fabricación del bastidor y del marco, el tratamiento anticorrosivo, el montaje del marco anclado a los machones, el colgado con bisagras dimensionadas para el peso, el ajuste de la nivelación para que el portón no se abra o se cierre solo, la colocación de pasador y cerradura y el acabado. Medido en superficie realmente ejecutada.":
    "Manufacture and installation of a hinged grille gate for pedestrian or vehicular access, with its frame, reinforced hinges, latch and lock. Includes fabricating the frame and the surround, the anti-corrosion treatment, fastening the surround anchored to the piers, hanging it on hinges sized for the weight, adjusting the level so that the gate neither swings open nor shuts by itself, fitting the latch and the lock and the finish. Measured by the area actually completed.",

"Fabricación y montaje de estructura metálica menor, tal como marquesinas, pérgolas, soportes de equipos y estructuras auxiliares, con su tratamiento anticorrosivo. Incluye el replanteo, el corte y armado de los perfiles, la soldadura de las uniones con su limpieza de escoria, el tratamiento anticorrosivo, el izado y montaje, el anclaje al soporte y la comprobación geométrica. Medido en peso realmente montado.":
    "Manufacture and installation of minor metalwork, such as canopies, pergolas, equipment supports and ancillary structures, with its anti-corrosion treatment. Includes field layout, cutting and assembling the sections, welding the joints and cleaning off the slag, the anti-corrosion treatment, hoisting and erection, anchoring to the support and the geometric check. Measured by the weight actually erected.",

"Suministro y colocación de reja fija de tubo de acero para ventana, con anclaje a muro. Incluye la fabricación, el montaje y el anclaje. Medido por metro cuadrado instalado.":
    "Supply and installation of a fixed steel tube grille to a window, anchored to the wall. Includes fabrication, installation and anchoring. Measured per square meter installed.",
"Suministro y colocación de reja de tubo con marco para puerta, con bisagras y cerradura. Incluye la fabricación, el montaje y el anclaje. Medido por metro cuadrado instalado.":
    "Supply and installation of a tube grille with a frame to a doorway, with hinges and a lock. Includes fabrication, installation and anchoring. Measured per square meter installed.",
"Suministro y colocación de reja de acero inoxidable para ventana, con anclaje a muro. Incluye la fabricación, el montaje y el anclaje. Medido por metro cuadrado instalado.":
    "Supply and installation of a stainless steel grille to a window, anchored to the wall. Includes fabrication, installation and anchoring. Measured per square meter installed.",
"Suministro y colocación de reja decorativa de forja para ventana, con anclaje a muro. Incluye la fabricación, el montaje y el anclaje. Medido por metro cuadrado instalado.":
    "Supply and installation of a decorative wrought iron grille to a window, anchored to the wall. Includes fabrication, installation and anchoring. Measured per square meter installed.",
"Suministro y colocación de reja batiente de tubo para ventana, con bisagras y cerradura. Incluye la fabricación, el montaje y el anclaje. Medido por metro cuadrado instalado.":
    "Supply and installation of a hinged tube grille to a window, with hinges and a lock. Includes fabrication, installation and anchoring. Measured per square meter installed.",
"Suministro y colocación de cerrajera de protección para ventana, con anclaje a muro. Incluye la fabricación, el montaje y el anclaje. Medido por metro cuadrado instalado.":
    "Supply and installation of a protective metal grille to a window, anchored to the wall. Includes fabrication, installation and anchoring. Measured per square meter installed.",
"Suministro y montaje de estructura metálica menor para marquesina, con perfiles soldados. Incluye la fabricación, el montaje y el anclaje. Medido por metro cuadrado instalado.":
    "Supply and installation of minor metalwork for a canopy, with welded sections. Includes fabrication, installation and anchoring. Measured per square meter installed.",
"Suministro y montaje de portón corredizo metálico para acceso vehicular o peatonal, con su bastidor, riel, ruedas, guías y topes. Incluye la fabricación o recepción del bastidor, la ejecución o comprobación del riel de rodadura perfectamente nivelado, ya que cualquier desnivel hace que el portón corra solo o se atasque, el montaje de las ruedas y guías superiores, el ajuste del recorrido y los topes, la imprimación anticorrosiva y la comprobación de maniobra. Medido en superficie realmente ejecutada.":
    "Supply and installation of a metal sliding gate for vehicular or pedestrian access, with its frame, track, wheels, guides and stops. Includes fabricating or taking delivery of the frame, constructing or checking that the running track is perfectly level, since any unevenness makes the gate run by itself or jam, fitting the wheels and the top guides, adjusting the travel and the stops, the anti-corrosion primer and checking the operation. Measured by the area actually completed.",

"Suministro y colocación de portón corredizo de tubo de acero, con riel, carros y guías. Incluye la fabricación, el montaje del riel y la colocación del portón. Medido por unidad instalada.":
    "Supply and installation of a steel tube sliding gate, with track, carriers and guides. Includes fabrication, fitting the track and hanging the gate. Measured per unit installed.",
"Suministro y colocación de portón batiente de tubo de acero, con bisagras y cerradura. Incluye la fabricación, el montaje y el anclaje. Medido por unidad instalada.":
    "Supply and installation of a hinged steel tube gate, with hinges and a lock. Includes fabrication, installation and anchoring. Measured per unit installed.",
"Suministro y colocación de portón metálico para garaje con marco, de chapa plegada. Incluye la fabricación, el montaje del marco y la colocación de las hojas. Medido por unidad instalada.":
    "Supply and installation of a metal garage door with a frame, in folded sheet. Includes fabrication, erecting the frame and hanging the leaves. Measured per unit installed.",
"Suministro y colocación de portón de acero inoxidable para acceso, con bisagras y cerradura. Incluye la fabricación, el montaje y el anclaje. Medido por unidad instalada.":
    "Supply and installation of a stainless steel access gate, with hinges and a lock. Includes fabrication, installation and anchoring. Measured per unit installed.",
"Suministro y colocación de portón levadizo de garaje, con mecanismo de contrapeso y guías. Incluye la fabricación, el montaje de las guías y la colocación del portón. Medido por unidad instalada.":
    "Supply and installation of an overhead garage door, with a counterbalance mechanism and guides. Includes fabrication, fitting the guides and hanging the door. Measured per unit installed.",
"Suministro y colocación de portón peatonal de reja de tubo, con bisagras y cerradura. Incluye la fabricación, el montaje y el anclaje. Medido por unidad instalada.":
    "Supply and installation of a pedestrian tube grille gate, with hinges and a lock. Includes fabrication, installation and anchoring. Measured per unit installed.",
"Suministro y colocación de portón corredizo de acero con hoja ciega de chapa, con riel y carros. Incluye la fabricación, el montaje del riel y la colocación del portón. Medido por unidad instalada.":
    "Supply and installation of a steel sliding gate with a solid sheet leaf, with track and carriers. Includes fabrication, fitting the track and hanging the gate. Measured per unit installed.",
"Suministro y colocación de portón de dos hojas para acceso vehicular, con bisagras y cerradura. Incluye la fabricación, el montaje y el anclaje. Medido por unidad instalada.":
    "Supply and installation of a two leaf gate for vehicular access, with hinges and a lock. Includes fabrication, installation and anchoring. Measured per unit installed.",
"Suministro y colocación de portón corredizo con motor y automatismo, riel y carros. Incluye la fabricación, el montaje del riel, el motor y la programación. Medido por unidad instalada.":
    "Supply and installation of a sliding gate with motor and automation, track and carriers. Includes fabrication, fitting the track, the motor and the programming. Measured per unit installed.",
"Suministro y colocación de portón batiente de dos hojas con automatismo. Incluye la fabricación, el montaje, los motores y la programación. Medido por unidad instalada.":
    "Supply and installation of a two leaf hinged gate with automation. Includes fabrication, installation, the motors and the programming. Measured per unit installed.",

# ── Barandas y pasamanos ──────────────────────────────────────────────────
"Suministro y montaje de pasamanos de madera sobre baranda existente o directamente sobre pared mediante soportes. Incluye el replanteo de la altura constante siguiendo la pendiente de la escalera, el corte y unión de los tramos con empalmes ocultos, el montaje de los soportes con la separación que evita la flexión, la fijación del pasamanos, el lijado de la unión hasta hacerla imperceptible al tacto, que es como se percibe un pasamanos, y el barnizado. Medido en longitud realmente instalada.":
    "Supply and installation of a wood handrail over an existing guardrail or directly onto a wall on brackets. Includes field layout of a constant height following the pitch of the stair, cutting and joining the lengths with hidden joints, fitting the brackets at the spacing that avoids flexing, fastening the handrail, sanding the joint until it cannot be felt, which is how a handrail is judged, and varnishing. Measured by the length actually installed.",

"Suministro y montaje de baranda o pasamanos de acero inoxidable con sus montantes, tubos y accesorios de unión, anclados al piso o al canto de la losa. Incluye el replanteo, el corte y pulido de los tubos, el montaje de los montantes con sus bases ancladas mecánicamente, el ensamblaje de los tramos con accesorios o soldadura de inoxidable, el pulido de las uniones hasta igualar el acabado del tubo y la comprobación de rigidez frente a empuje horizontal. Medido en longitud realmente instalada.":
    "Supply and installation of a stainless steel guardrail or handrail with its posts, tubes and joint fittings, anchored to the floor or to the edge of the slab. Includes field layout, cutting and polishing the tubes, erecting the posts with their bases mechanically anchored, assembling the runs with fittings or by stainless welding, polishing the joints until they match the finish of the tube and checking the stiffness against horizontal thrust. Measured by the length actually installed.",

"Fabricación y montaje de baranda metálica de protección en balcón, terraza o escalera, con su pasamanos, montantes y barrotes, anclada al piso o al canto de la losa. La altura y la separación entre barrotes no son de diseño libre: responden a criterios de seguridad frente a caída y frente al paso de un niño entre ellos. Incluye la fabricación, el tratamiento anticorrosivo, el replanteo y anclaje mecánico de los montantes, el resane de los anclajes, la comprobación de la rigidez del conjunto frente a empuje horizontal y el acabado. Medido en longitud realmente instalada.":
    "Manufacture and installation of a metal guardrail to a balcony, terrace or stair, with its handrail, posts and bars, anchored to the floor or to the edge of the slab. The height and the spacing of the bars are not free design choices: they answer to safety criteria against falling and against a child passing between them. Includes fabrication, the anti-corrosion treatment, field layout and mechanically anchoring the posts, patching the anchors, checking the stiffness of the assembly against horizontal thrust and the finish. Measured by the length actually installed.",

"Suministro y colocación de pasamanos de madera sobre escalera, con soportes y remates. Incluye la fijación del pasamanos y el acabado. Medido por metro lineal instalado.":
    "Supply and installation of a wood handrail over a stair, with brackets and end caps. Includes fastening the handrail and the finish. Measured per meter installed.",
"Suministro y colocación de pasamanos de acero inoxidable sobre escalera, con soportes. Incluye la fijación del pasamanos y el pulido de uniones. Medido por metro lineal instalado.":
    "Supply and installation of a stainless steel handrail over a stair, with brackets. Includes fastening the handrail and polishing the joints. Measured per meter installed.",
"Suministro y colocación de baranda de acero inoxidable con paño de vidrio templado. Incluye la fijación de la baranda y el acristalamiento. Medido por metro lineal instalado.":
    "Supply and installation of a stainless steel guardrail with tempered glass infill panels. Includes fastening the guardrail and the glazing. Measured per meter installed.",
"Suministro y colocación de baranda de tubo de acero galvanizado, con montantes y pasamanos. Incluye la fabricación, el montaje y el anclaje. Medido por metro lineal instalado.":
    "Supply and installation of a galvanized steel tube guardrail, with posts and handrail. Includes fabrication, installation and anchoring. Measured per meter installed.",
"Suministro y colocación de baranda de acero inoxidable para balcón, con montantes y pasamanos. Incluye la fabricación, el montaje y el anclaje. Medido por metro lineal instalado.":
    "Supply and installation of a stainless steel balcony guardrail, with posts and handrail. Includes fabrication, installation and anchoring. Measured per meter installed.",
"Suministro y colocación de baranda de forja decorativa, con montantes y pasamanos. Incluye la fabricación, el montaje y el anclaje. Medido por metro lineal instalado.":
    "Supply and installation of a decorative wrought iron guardrail, with posts and handrail. Includes fabrication, installation and anchoring. Measured per meter installed.",
"Suministro y colocación de baranda de madera para escalera interior, con montantes y pasamanos. Incluye la fijación de la baranda y el acabado. Medido por metro lineal instalado.":
    "Supply and installation of a wood guardrail to an internal stair, with posts and handrail. Includes fastening the guardrail and the finish. Measured per meter installed.",
"Suministro y colocación de baranda de acero con pasamanos de madera. Incluye la fabricación de la baranda, el montaje y la fijación del pasamanos de madera. Medido por metro lineal instalado.":
    "Supply and installation of a steel guardrail with a wood handrail. Includes fabricating the guardrail, installation and fastening the wood handrail. Measured per meter installed.",
"Suministro y colocación de baranda de protección de cubierta o terraza, con montantes y pasamanos. Incluye la fabricación, el montaje y el anclaje. Medido por metro lineal instalado.":
    "Supply and installation of a guardrail to a roof or terrace, with posts and handrail. Includes fabrication, installation and anchoring. Measured per meter installed.",
"Suministro y colocación de baranda de vidrio templado sin montantes verticales, con perfil inferior de fijación. Incluye la fijación del perfil y el acristalamiento. Medido por metro lineal instalado.":
    "Supply and installation of a tempered glass guardrail without vertical posts, with a bottom fastening channel. Includes fastening the channel and the glazing. Measured per meter installed.",
"Suministro y colocación de baranda de acero inoxidable con pasamanos y tensores horizontales. Incluye la fabricación, el montaje y el tensado. Medido por metro lineal instalado.":
    "Supply and installation of a stainless steel guardrail with a handrail and horizontal tension rods. Includes fabrication, installation and tensioning. Measured per meter installed.",
"Suministro y colocación de pasamanos de acero para escalera exterior, con soportes. Incluye la fijación del pasamanos y la protección anticorrosiva. Medido por metro lineal instalado.":
    "Supply and installation of a steel handrail to an external stair, with brackets. Includes fastening the handrail and the anti-corrosion protection. Measured per meter installed.",
"Suministro y colocación de baranda de aluminio para balcón, con montantes y pasamanos. Incluye la fabricación, el montaje y el anclaje. Medido por metro lineal instalado.":
    "Supply and installation of an aluminum balcony guardrail, with posts and handrail. Includes fabrication, installation and anchoring. Measured per meter installed.",
"Suministro y colocación de baranda de madera para balcón interior, con montantes y pasamanos. Incluye la fijación de la baranda y el acabado. Medido por metro lineal instalado.":
    "Supply and installation of a wood guardrail to an internal balcony, with posts and handrail. Includes fastening the guardrail and the finish. Measured per meter installed.",
"Suministro y colocación de baranda de acero con paño de plancha perforada decorativa. Incluye la fabricación, el montaje y el anclaje. Medido por metro lineal instalado.":
    "Supply and installation of a steel guardrail with decorative perforated sheet infill panels. Includes fabrication, installation and anchoring. Measured per meter installed.",
"Suministro y colocación de baranda de acero inoxidable para piscina o zona húmeda, con montantes y pasamanos. Incluye la fabricación, el montaje y el anclaje. Medido por metro lineal instalado.":
    "Supply and installation of a stainless steel guardrail for a pool or wet area, with posts and handrail. Includes fabrication, installation and anchoring. Measured per meter installed.",
"Suministro y colocación de baranda de acero con relleno de malla metálica. Incluye la fabricación, el montaje y el anclaje. Medido por metro lineal instalado.":
    "Supply and installation of a steel guardrail with wire mesh infill. Includes fabrication, installation and anchoring. Measured per meter installed.",
"Suministro y colocación de baranda de escalera con zanca de madera y pasamanos. Incluye la fijación de la baranda y el acabado. Medido por metro lineal instalado.":
    "Supply and installation of a stair guardrail with a wood stringer and handrail. Includes fastening the guardrail and the finish. Measured per meter installed.",
"Suministro y colocación de baranda de acero galvanizado con pasamanos de madera. Incluye la fabricación, el montaje y la fijación del pasamanos. Medido por metro lineal instalado.":
    "Supply and installation of a galvanized steel guardrail with a wood handrail. Includes fabrication, installation and fastening the handrail. Measured per meter installed.",

# ── Vidrios y espejos ─────────────────────────────────────────────────────
"Suministro y colocación de vidrio en carpintería existente o nueva, con sus calzos, junquillos y sellado. Incluye la toma de medidas del galce con la holgura de dilatación necesaria, ya que un vidrio colocado a presión sin holgura se rompe con la dilatación térmica, la limpieza del galce, la colocación de los calzos de apoyo y laterales en la posición correcta según el tipo de hoja, el acuñado del vidrio, la colocación de junquillos y el sellado perimetral. Medido en superficie realmente ejecutada.":
    "Supply and installation of glass in existing or new carpentry, with its setting blocks, glazing beads and sealing. Includes measuring the rabbet with the expansion clearance needed, since glass fitted tight with no clearance cracks with thermal expansion, cleaning the rabbet, placing the setting blocks and side blocks in the correct position for the type of sash, wedging the glass, fitting the glazing beads and sealing the perimeter. Measured by the area actually completed.",

"Suministro y colocación de espejo con canto pulido, fijado al paramento mediante adhesivo específico y clips de seguridad. El adhesivo debe ser neutro y compatible con el respaldo del espejo: los adhesivos ácidos atacan la plata del reverso y producen manchas negras irreversibles en los bordes al cabo de unos meses. Incluye la comprobación de la planitud del soporte, la aplicación del adhesivo en cordones verticales que permiten la ventilación del reverso, la colocación de los clips o perfiles de seguridad y el sellado perimetral. Medido en superficie realmente ejecutada.":
    "Supply and installation of a mirror with polished edges, fastened to the wall with a specific adhesive and safety clips. The adhesive must be neutral and compatible with the backing of the mirror: acid adhesives attack the silvering on the reverse and produce irreversible black staining at the edges within a few months. Includes checking that the substrate is flat, applying the adhesive in vertical beads that allow the reverse to ventilate, fitting the safety clips or profiles and sealing the perimeter. Measured by the area actually completed.",

"Suministro e instalación de baranda o cerramiento de vidrio templado con sus perfiles de sujeción, pinzas o perfil continuo empotrado, y pasamanos superior. Incluye la comprobación del anclaje y del refuerzo del soporte, que debe estar dimensionado para el empuje horizontal reglamentario, el montaje del perfil o de las pinzas, la colocación y aplomado del vidrio con sus calzos, el acuñado y sellado, y la colocación del pasamanos superior de protección del canto. Medido en superficie realmente ejecutada.":
    "Supply and installation of a tempered glass guardrail or screen with its fastening profiles, clamps or continuous recessed channel, and a top handrail. Includes checking the anchorage and the strengthening of the support, which must be sized for the horizontal thrust required by the regulations, fitting the profile or the clamps, placing and plumbing the glass on its setting blocks, wedging and sealing, and fitting the top handrail that protects the edge. Measured by the area actually completed.",

"Suministro y colocación de vidrio templado en carpintería existente. Incluye la toma de medidas, el corte y la colocación con sellado. Medido por metro cuadrado colocado.":
    "Supply and installation of tempered glass in existing carpentry. Includes measuring, cutting and installation with sealing. Measured per square meter installed.",
"Suministro y colocación de vidrio laminado de seguridad en carpintería. Incluye la toma de medidas, el corte y la colocación. Medido por metro cuadrado colocado.":
    "Supply and installation of safety laminated glass in carpentry. Includes measuring, cutting and installation. Measured per square meter installed.",
"Suministro y colocación de doble acristalamiento en carpintería existente. Incluye la toma de medidas y la colocación con sellado. Medido por metro cuadrado colocado.":
    "Supply and installation of double glazing in existing carpentry. Includes measuring and installation with sealing. Measured per square meter installed.",
"Suministro y colocación de espejo de pared, fijado con adhesivo o soportes. Incluye la preparación del soporte y la colocación del espejo. Medido por metro cuadrado colocado.":
    "Supply and installation of a wall mirror, fastened with adhesive or brackets. Includes preparing the substrate and installing the mirror. Measured per square meter installed.",
"Suministro y colocación de cerramiento de vidrio templado en terraza o balcón, con perfil de fijación. Incluye el montaje del perfil y el acristalamiento. Medido por metro cuadrado instalado.":
    "Supply and installation of a tempered glass screen to a terrace or balcony, with a fastening profile. Includes fitting the profile and the glazing. Measured per square meter installed.",
"Suministro y colocación de muro cortina de vidrio templado con estructura portante. Incluye la estructura, el acristalamiento y el sellado. Medido por metro cuadrado instalado.":
    "Supply and installation of a tempered glass curtain wall with its supporting structure. Includes the structure, the glazing and sealing. Measured per square meter installed.",
"Suministro y colocación de vidrio esmerilado en división interior, para privacidad. Incluye la toma de medidas y la colocación. Medido por metro cuadrado colocado.":
    "Supply and installation of frosted glass in an internal division, for privacy. Includes measuring and installation. Measured per square meter installed.",
"Colocación de vidrio en marco existente, con sustitución del vidrio roto. Incluye la retirada del vidrio roto, la toma de medidas y la colocación del nuevo. Medido por metro cuadrado colocado.":
    "Installation of glass in an existing frame, replacing the broken pane. Includes removing the broken glass, measuring and installing the new. Measured per square meter installed.",
"Suministro y colocación de vidrio blindado de seguridad, con sellado. Incluye la toma de medidas y la colocación. Medido por metro cuadrado colocado.":
    "Supply and installation of security glass, sealed. Includes measuring and installation. Measured per square meter installed.",
"Suministro y colocación de espejo de baño con marco, fijado al paramento. Incluye la preparación del soporte y la colocación. Medido por metro cuadrado colocado.":
    "Supply and installation of a framed bathroom mirror, fastened to the wall. Includes preparing the substrate and installation. Measured per square meter installed.",
"Suministro y colocación de techo de vidrio templado en patio interior, con estructura portante. Incluye la estructura, el acristalamiento y el sellado. Medido por metro cuadrado instalado.":
    "Supply and installation of a tempered glass roof over an internal courtyard, with its supporting structure. Includes the structure, the glazing and sealing. Measured per square meter installed.",
"Suministro y colocación de ventanal de vidrio fijo interior, con perfil de fijación. Incluye el montaje del perfil y el acristalamiento. Medido por metro cuadrado instalado.":
    "Supply and installation of a fixed internal glazed screen, with a fastening profile. Includes fitting the profile and the glazing. Measured per square meter installed.",
"Sustitución del vidrio roto de una ventana, con retirada y colocación del nuevo. Incluye la limpieza del marco, la toma de medidas y la colocación. Medido por metro cuadrado sustituido.":
    "Replacement of a broken window pane, removing it and installing the new one. Includes cleaning the frame, measuring and installation. Measured per square meter replaced.",
"Suministro y colocación de vidrio decorativo grabado o arenado, con sellado. Incluye la toma de medidas y la colocación. Medido por metro cuadrado colocado.":
    "Supply and installation of decorative etched or sandblasted glass, sealed. Includes measuring and installation. Measured per square meter installed.",
"Suministro y colocación de cerramiento de vidrio templado en pasillo o galería, con perfil de fijación. Incluye el montaje del perfil y el acristalamiento. Medido por metro cuadrado instalado.":
    "Supply and installation of a tempered glass screen in a corridor or gallery, with a fastening profile. Includes fitting the profile and the glazing. Measured per square meter installed.",
"Suministro y colocación de espejo de vestir de cuerpo entero, fijado al paramento. Incluye la preparación del soporte y la colocación. Medido por unidad colocado.":
    "Supply and installation of a full length dressing mirror, fastened to the wall. Includes preparing the substrate and installation. Measured per unit installed.",
"Suministro y colocación de vidrio laminado de seguridad en puerta de acceso. Incluye la toma de medidas, el corte y la colocación. Medido por metro cuadrado colocado.":
    "Supply and installation of safety laminated glass in an access door. Includes measuring, cutting and installation. Measured per square meter installed.",

# ── Mamparas ──────────────────────────────────────────────────────────────
"Suministro e instalación de mampara de ducha o baño en vidrio templado, con sus perfiles, herrajes y sellado. El vidrio templado no admite ningún corte ni perforación después del temple, de modo que todas las medidas y taladros deben definirse antes de fabricar: un error de medición obliga a rehacer la pieza completa. Incluye la toma de medidas en obra sobre el enchapado ya terminado, el montaje de perfiles y herrajes, la colocación del vidrio con sus calzos, el ajuste de la puerta y el sellado con silicona sanitaria dejando libre la línea inferior interior para que el agua drene hacia dentro. Medido en superficie realmente ejecutada.":
    "Supply and installation of a tempered glass shower or bath screen, with its profiles, hardware and sealing. Tempered glass admits no cutting or drilling after toughening, so every dimension and every hole must be defined before it is made: an error in measuring means the whole unit has to be remade. Includes measuring on site over the finished tiling, fitting the profiles and hardware, installing the glass on its setting blocks, adjusting the door and sealing with silicone sealant, leaving the inner bottom edge free so that water drains back inside. Measured by the area actually completed.",

"Suministro y colocación de mampara de baño fija de vidrio templado, con perfil y sellado. Incluye la toma de medidas, el montaje del perfil y el acristalamiento. Medido por metro cuadrado instalado.":
    "Supply and installation of a fixed tempered glass bath screen, with profile and sealing. Includes measuring, fitting the profile and the glazing. Measured per square meter installed.",
"Suministro y colocación de mampara de ducha abatible de vidrio templado, con bisagras y sellado. Incluye la toma de medidas, el montaje y el sellado. Medido por metro cuadrado instalado.":
    "Supply and installation of a hinged tempered glass shower panel, with hinges and sealing. Includes measuring, installation and sealing. Measured per square meter installed.",
"Suministro y colocación de mampara de ducha corrediza de vidrio templado, con riel y sellado. Incluye la toma de medidas, el montaje del riel y el sellado. Medido por metro cuadrado instalado.":
    "Supply and installation of a sliding tempered glass shower panel, with track and sealing. Includes measuring, fitting the track and sealing. Measured per square meter installed.",
"Suministro y colocación de división de oficina acristalada, con perfilería y vidrio. Incluye la estructura, el acristalamiento y el sellado. Medido por metro cuadrado instalado.":
    "Supply and installation of a glazed office division, with framing and glass. Includes the structure, the glazing and sealing. Measured per square meter installed.",
"Suministro y colocación de mampara de baño de vidrio templado con perfil de acero inoxidable. Incluye la toma de medidas, el montaje y el sellado. Medido por metro cuadrado instalado.":
    "Supply and installation of a tempered glass bath screen with a stainless steel profile. Includes measuring, installation and sealing. Measured per square meter installed.",
"Suministro y colocación de división de baño con vidrio esmerilado, para privacidad. Incluye el montaje del perfil y el acristalamiento. Medido por metro cuadrado instalado.":
    "Supply and installation of a bathroom division in frosted glass, for privacy. Includes fitting the profile and the glazing. Measured per square meter installed.",
"Suministro y colocación de cabina de ducha completa de vidrio templado, con paneles y puerta. Incluye la toma de medidas, el montaje y el sellado. Medido por metro cuadrado instalado.":
    "Supply and installation of a complete tempered glass shower enclosure, with panels and door. Includes measuring, installation and sealing. Measured per square meter installed.",
"Suministro y colocación de mampara de bañera de vidrio templado, abatible o fija. Incluye la toma de medidas, el montaje y el sellado. Medido por metro cuadrado instalado.":
    "Supply and installation of a tempered glass bath screen, hinged or fixed. Includes measuring, installation and sealing. Measured per square meter installed.",
"Suministro y colocación de separador de cocina con vidrio templado, con perfil de fijación. Incluye el montaje del perfil y el acristalamiento. Medido por metro cuadrado instalado.":
    "Supply and installation of a tempered glass kitchen divider, with a fastening profile. Includes fitting the profile and the glazing. Measured per square meter installed.",
"Suministro y colocación de mampara de ducha de vidrio templado sin perfil, con fijación puntual. Incluye la toma de medidas, el montaje y el sellado. Medido por metro cuadrado instalado.":
    "Supply and installation of a frameless tempered glass shower panel, with point fasteners. Includes measuring, installation and sealing. Measured per square meter installed.",
"Suministro y colocación de mampara divisoria de baño para inodoro, de vidrio templado. Incluye la toma de medidas, el montaje y el sellado. Medido por metro cuadrado instalado.":
    "Supply and installation of a tempered glass toilet partition. Includes measuring, installation and sealing. Measured per square meter installed.",
"Suministro y colocación de cerramiento de ducha a ras de piso, de vidrio templado. Incluye la toma de medidas, el montaje y el sellado. Medido por metro cuadrado instalado.":
    "Supply and installation of a level access tempered glass shower enclosure. Includes measuring, installation and sealing. Measured per square meter installed.",
"Suministro y colocación de mampara de vidrio templado para local comercial, con perfil y puerta. Incluye la estructura, el acristalamiento y el sellado. Medido por metro cuadrado instalado.":
    "Supply and installation of a tempered glass screen for commercial premises, with profile and door. Includes the structure, the glazing and sealing. Measured per square meter installed.",
"Suministro y colocación de mampara de ducha plegable de vidrio templado, con bisagras. Incluye la toma de medidas, el montaje y el sellado. Medido por metro cuadrado instalado.":
    "Supply and installation of a folding tempered glass shower panel, with hinges. Includes measuring, installation and sealing. Measured per square meter installed.",
"Suministro y colocación de separador de ambientes de vidrio templado, con perfil de fijación. Incluye el montaje del perfil y el acristalamiento. Medido por metro cuadrado instalado.":
    "Supply and installation of a tempered glass room divider, with a fastening profile. Includes fitting the profile and the glazing. Measured per square meter installed.",

# ── Protección solar ──────────────────────────────────────────────────────
"Suministro y colocación de persiana enrollable de aluminio con su cajón y cinta. Incluye la toma de medidas, el montaje del cajón y la colocación de la persiana. Medido por metro cuadrado instalado.":
    "Supply and installation of an aluminum roller shutter with its box and strap. Includes measuring, fitting the box and installing the shutter. Measured per square meter installed.",
"Suministro y colocación de persiana enrollable de aluminio motorizada, con mando. Incluye el montaje del cajón, el motor y la programación. Medido por metro cuadrado instalado.":
    "Supply and installation of a motorised aluminum roller shutter, with control. Includes fitting the box, the motor and the programming. Measured per square meter installed.",
"Suministro y colocación de toldo extensible de lona con brazos y soportes. Incluye la toma de medidas, el montaje de los soportes y la colocación del toldo. Medido por metro cuadrado instalado.":
    "Supply and installation of a retractable fabric awning with arms and brackets. Includes measuring, fitting the brackets and installing the awning. Measured per square meter installed.",
"Suministro y colocación de celosía fija de aluminio para ventilación. Incluye la toma de medidas, el montaje y el anclaje. Medido por metro cuadrado instalado.":
    "Supply and installation of a fixed aluminum louver screen for ventilation. Includes measuring, installation and anchoring. Measured per square meter installed.",
"Suministro y colocación de celosía de madera para ventilación. Incluye la toma de medidas, el montaje y el anclaje. Medido por metro cuadrado instalado.":
    "Supply and installation of a wood louver screen for ventilation. Includes measuring, installation and anchoring. Measured per square meter installed.",
"Suministro y colocación de romanilla de aluminio para fachada, con lamas orientables. Incluye la toma de medidas, el montaje y el anclaje. Medido por metro cuadrado instalado.":
    "Supply and installation of an aluminum facade louver screen with adjustable blades. Includes measuring, installation and anchoring. Measured per square meter installed.",
"Suministro y colocación de mosquitero fijo de marco en ventana. Incluye la toma de medidas, el montaje del marco y la colocación de la malla. Medido por metro cuadrado instalado.":
    "Supply and installation of a fixed framed insect screen to a window. Includes measuring, assembling the frame and fitting the mesh. Measured per square meter installed.",
"Suministro y colocación de mosquitero corredizo en ventana o balconera. Incluye la toma de medidas, el montaje del riel y la colocación del mosquitero. Medido por metro cuadrado instalado.":
    "Supply and installation of a sliding insect screen to a window or patio door. Includes measuring, fitting the track and installing the screen. Measured per square meter installed.",
"Suministro y colocación de mosquitero enrollable en ventana. Incluye la toma de medidas, el montaje y el ajuste del mecanismo. Medido por metro cuadrado instalado.":
    "Supply and installation of a roller insect screen to a window. Includes measuring, installation and adjusting the mechanism. Measured per square meter installed.",
"Suministro y colocación de mosquitero para puerta, con marco y malla. Incluye la toma de medidas, el montaje y el ajuste. Medido por metro cuadrado instalado.":
    "Supply and installation of an insect screen to a door, with frame and mesh. Includes measuring, installation and adjustment. Measured per square meter installed.",
"Suministro y colocación de malla antiinsectos en ventana, fijada al marco. Incluye la toma de medidas y la fijación de la malla. Medido por metro cuadrado instalado.":
    "Supply and installation of insect mesh to a window, fastened to the frame. Includes measuring and fastening the mesh. Measured per square meter installed.",

# ── Cerrajería y automatismos ─────────────────────────────────────────────
"Instalación de cerradura de seguridad con cilindro en puerta existente. Incluye la preparación del hueco, el montaje y el ajuste. Medido por unidad instalada.":
    "Installation of a cylinder security lock to an existing door. Includes preparing the housing, fitting and adjustment. Measured per unit installed.",
"Instalación de cerradura electrónica de teclado o huella en puerta existente. Incluye el montaje, la conexión y la programación. Medido por unidad instalada.":
    "Installation of an electronic keypad or fingerprint lock to an existing door. Includes fitting, connection and programming. Measured per unit installed.",
"Sustitución de la cerradura de una puerta, con desmontaje de la anterior y montaje de la nueva. Incluye la retirada y el montaje. Medido por unidad sustituida.":
    "Replacement of a door lock, removing the old one and fitting the new. Includes removal and installation. Measured per unit replaced.",
"Cambio del cilindro de una cerradura existente, manteniendo el cuerpo. Incluye la retirada del cilindro anterior y el montaje del nuevo. Medido por unidad cambiada.":
    "Changing the cylinder of an existing lock, keeping the body. Includes removing the old cylinder and fitting the new. Measured per unit changed.",
"Instalación de herrajes (bisagras, manillas, cerraderos) en puerta. Incluye el montaje y el ajuste. Medido por unidad instalada.":
    "Installation of hardware (hinges, lever handles, strike plates) to a door. Includes fitting and adjustment. Measured per unit installed.",
"Instalación de cierra-puertas hidráulico en puerta, con regulación de velocidad. Incluye el montaje y el ajuste. Medido por unidad instalada.":
    "Installation of a hydraulic door closer to a door, with the closing speed regulated. Includes fitting and adjustment. Measured per unit installed.",
"Instalación de herrajes de corredera (carros, guías, topes) en puerta corrediza. Incluye el montaje y el ajuste. Medido por unidad instalada.":
    "Installation of sliding door hardware (carriers, guides, stops) to a sliding door. Includes fitting and adjustment. Measured per unit installed.",
"Automatización de un portón corredizo existente, con motor, mando y finales de carrera. Incluye el montaje del motor y la programación. Medido por unidad automatizada.":
    "Automation of an existing sliding gate, with motor, control and limit switches. Includes fitting the motor and the programming. Measured per unit automated.",
"Automatización de un portón batiente existente, con motores y mando. Incluye el montaje de los motores y la programación. Medido por unidad automatizada.":
    "Automation of an existing hinged gate, with motors and control. Includes fitting the motors and the programming. Measured per unit automated.",
"Instalación de videoportero con placa exterior y monitor interior. Incluye el cableado, el montaje y la configuración. Medido por unidad instalada.":
    "Installation of a video door entry system with an external panel and an internal monitor. Includes cabling, installation and configuration. Measured per unit installed.",
"Instalación de cerradura con apertura remota o intercomunicación. Incluye el montaje, la conexión y la programación. Medido por unidad instalada.":
    "Installation of a lock with remote release or intercom. Includes fitting, connection and programming. Measured per unit installed.",

# ── Reparación y restauración ─────────────────────────────────────────────
"Ajuste de puerta descolgada o que roza, con reajuste de bisagras. Incluye la comprobación y el reajuste de los herrajes. Medido por unidad ajustada.":
    "Adjustment of a door that has dropped or is binding, by re-adjusting the hinges. Includes checking and re-adjusting the hardware. Measured per unit adjusted.",
"Reparación de puerta con reposición de herrajes deteriorados. Incluye la retirada de los herrajes dañados y el montaje de los nuevos. Medido por unidad reparada.":
    "Repair of a door by replacing deteriorated hardware. Includes removing the damaged hardware and fitting the new. Measured per unit repaired.",
"Reparación de ventana con ajuste de herrajes y mecanismos. Incluye la comprobación y el ajuste. Medido por metro cuadrado reparado.":
    "Repair of a window by adjusting the hardware and mechanisms. Includes checking and adjustment. Measured per square meter repaired.",
"Ajuste de portón corredizo, con reajuste de carros, guías y topes. Incluye la comprobación y el reajuste. Medido por unidad ajustada.":
    "Adjustment of a sliding gate, re-adjusting the carriers, guides and stops. Includes checking and re-adjusting. Measured per unit adjusted.",
"Reparación de reja con sustitución de tramo de tubo dañado. Incluye el corte del tramo, la soldadura del nuevo y el repintado. Medido por metro lineal reparado.":
    "Repair of a grille by replacing a damaged length of tube. Includes cutting out the length, welding in the new and repainting. Measured per meter repaired.",
"Reparación de celosía de aluminio con sustitución de lamas dañadas. Incluye la retirada de las lamas dañadas y la colocación de las nuevas. Medido por unidad reparada.":
    "Repair of an aluminum louver screen by replacing damaged blades. Includes removing the damaged blades and fitting the new. Measured per unit repaired.",
"Reparación de persiana enrollable, con sustitución de cinta o ajuste del mecanismo. Incluye la comprobación y la reparación del mecanismo. Medido por unidad reparada.":
    "Repair of a roller shutter, replacing the strap or adjusting the mechanism. Includes checking and repairing the mechanism. Measured per unit repaired.",
"Restauración de puerta de madera con resane, lijado y acabado. Incluye el resane de golpes, el lijado y el barnizado o pintado. Medido por metro cuadrado restaurado.":
    "Restoration of a wood door by filling, sanding and finishing. Includes filling the dents, sanding and varnishing or painting. Measured per square meter restored.",
"Restauración de ventana de madera con resane, lijado y acabado. Incluye el resane, el lijado y el barnizado o pintado. Medido por metro cuadrado restaurado.":
    "Restoration of a wood window by filling, sanding and finishing. Includes filling, sanding and varnishing or painting. Measured per square meter restored.",
"Restauración de baranda de madera con lijado y barnizado. Incluye la preparación de la superficie y el barnizado. Medido por metro cuadrado restaurado.":
    "Restoration of a wood guardrail by sanding and varnishing. Includes preparing the surface and varnishing. Measured per square meter restored.",
"Sustitución de vidrio roto en carpintería, con retirada del vidrio dañado y colocación del nuevo. Incluye la limpieza del marco, la toma de medidas y la colocación. Medido por metro cuadrado sustituido.":
    "Replacement of broken glass in carpentry, removing the damaged pane and installing the new. Includes cleaning the frame, measuring and installation. Measured per square meter replaced.",
}
