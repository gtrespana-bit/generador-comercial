# -*- coding: utf-8 -*-
"""Descripciones — Instalaciones (2 de 4): saneamiento y electricidad.

Criterios de este lote:
  · «Puesta a tierra» es grounding en los Estados Unidos y earthing en el
    Reino Unido, y sin ella el diferencial no tiene el camino de fuga que
    necesita para actuar: los dos elementos funcionan como sistema o no
    funcionan.
  · El «interruptor termomagnético» es circuit breaker y protege la
    instalación; el «diferencial» es ground-fault circuit interrupter en
    los Estados Unidos y residual current device en el Reino Unido, y
    protege a las personas. No son intercambiables.
  · La capacidad del interruptor corresponde al calibre del conductor que
    protege, no al consumo del equipo: sobredimensionarlo convierte el
    cable en el fusible del circuito.
  · «Tomacorriente» es receptacle y el «punto de fuerza» es power outlet.
    El circuito propio de los equipos de alto consumo es dedicated circuit.
  · «Conmutación» es three-way en los Estados Unidos y two-way en el Reino
    Unido.
  · El perfil de aluminio de una cinta LED no es decorativo: es el
    disipador, y sin él la cinta pierde luminosidad y vida útil.
  · La caja de un ventilador de techo tiene que ser fan-rated y anclarse a
    estructura o a un refuerzo: una caja de luminaria no aguanta la
    vibración.
"""

LOTE = {
# ── Saneamiento: desagües ─────────────────────────────────────────────────
"Ejecución de montante de desagüe de cocina., con conexión. Incluye la conexión y la fijación. Medido por metro lineal ejecutado/a.":
    "Installation of a kitchen waste stack, with the connection. Includes the connection and fixing. Measured per meter constructed.",
"Ejecución de tubería de desagüe de cocina., con conexión. Incluye la conexión y la fijación. Medido por metro lineal ejecutado/a.":
    "Installation of kitchen waste pipework, with the connection. Includes the connection and fixing. Measured per meter constructed.",
"Ejecución de tubería de ventilación de desagüe., con conexión. Incluye la conexión y la fijación. Medido por metro lineal ejecutado/a.":
    "Installation of a drain vent pipe, with the connection. Includes the connection and fixing. Measured per meter constructed.",
"Ejecución de bajante de aguas servidas., con conexión. Incluye la conexión y la fijación. Medido por metro lineal ejecutado/a.":
    "Installation of a soil stack, with the connection. Includes the connection and fixing. Measured per meter constructed.",

"Ejecución de punto de desagüe para aparato sanitario, formado por la derivación en tubería de PVC sanitario desde el aparato hasta la bajante o colector más próximo, con una longitud media de 2 m y la pendiente reglamentaria. Incluye replanteo, apertura del paso en piso o paramento, montaje de la tubería con uniones cementadas, sifón y accesorios, fijación mediante abrazaderas, prueba de estanqueidad con agua, taponado provisional hasta la instalación del aparato y resane del paso. No incluye el aparato. Medido por punto terminado y probado.":
    "Installation of a waste point for a plumbing fixture, comprising the branch in PVC sanitary pipework from the fixture to the nearest stack or collector, at an average length of 2 m and the gradient required. Includes setting out, forming the penetration through floor or wall, laying the pipework with solvent cement joints, the trap and the fittings, fixing with pipe clips, testing for watertightness with water, temporarily capping until the fixture is installed and making good the penetration. It does not include the fixture. Measured per point completed and tested.",

"Punto de desagüe para lavadora. Incluye la conexión. Medido por punto ejecutado.":
    "Waste point for a washing machine. Includes the connection. Measured per point constructed.",
"Punto de desagüe para calentador. Incluye la conexión. Medido por punto ejecutado.":
    "Waste point for a water heater. Includes the connection. Measured per point constructed.",
"Punto de desagüe para nevera o congelador. Incluye la conexión. Medido por punto ejecutado.":
    "Waste point for a refrigerator or freezer. Includes the connection. Measured per point constructed.",
"Punto de desagüe para ducha. Incluye la conexión. Medido por punto ejecutado.":
    "Waste point for a shower. Includes the connection. Measured per point constructed.",
"Punto de desagüe para fregadero. Incluye la conexión. Medido por punto ejecutado.":
    "Waste point for a sink. Includes the connection. Measured per point constructed.",
"Punto de desagüe para lavamanos. Incluye la conexión. Medido por punto ejecutado.":
    "Waste point for a lavatory. Includes the connection. Measured per point constructed.",
"Punto de desagüe para inodoro. Incluye la conexión. Medido por punto ejecutado.":
    "Waste point for a toilet. Includes the connection. Measured per point constructed.",
"Ejecución de punto de desagüe para bañera., con conexión. Incluye la conexión y la fijación. Medido por unidad ejecutado/a.":
    "Installation of a waste point for a bathtub, with the connection. Includes the connection and fixing. Measured per unit constructed.",
"Ejecución de punto de desagüe para bidé., con conexión. Incluye la conexión y la fijación. Medido por unidad ejecutado/a.":
    "Installation of a waste point for a bidet, with the connection. Includes the connection and fixing. Measured per unit constructed.",
"Ejecución de punto de desagüe para lavadero., con conexión. Incluye la conexión y la fijación. Medido por unidad ejecutado/a.":
    "Installation of a waste point for a utility sink, with the connection. Includes the connection and fixing. Measured per unit constructed.",
"Ejecución de punto de desagüe para cocina., con conexión. Incluye la conexión y la fijación. Medido por unidad ejecutado/a.":
    "Installation of a waste point for a kitchen, with the connection. Includes the connection and fixing. Measured per unit constructed.",
"Ejecución de punto de desagüe para terraza., con conexión. Incluye la conexión y la fijación. Medido por unidad ejecutado/a.":
    "Installation of a waste point for a terrace, with the connection. Includes the connection and fixing. Measured per unit constructed.",
"Ejecución de punto de desagüe para jardín., con conexión. Incluye la conexión y la fijación. Medido por unidad ejecutado/a.":
    "Installation of a waste point for a garden, with the connection. Includes the connection and fixing. Measured per unit constructed.",

# ── Acometida y puesta a tierra ───────────────────────────────────────────
"Ejecución de la acometida eléctrica desde el punto de suministro hasta el tablero principal, con conductor de calibre adecuado, canalización y protección de cabecera. Incluye el replanteo del recorrido, la canalización enterrada o vista según el trazado, el tendido del conductor sin empalmes en todo el recorrido, la conexión en ambos extremos, la protección general y la coordinación con la compañía suministradora para la conexión definitiva. Medido por acometida ejecutada.":
    "Installation of the electrical service connection from the point of supply to the main panel, with a conductor of the right size, conduit and the service protective device. Includes setting out the route, the conduit buried or surface mounted according to the run, drawing in the conductor with no joints along the whole run, connecting at both ends, the main protection and coordinating with the supply company for the final connection. Measured per service connection constructed.",

"Montaje de la caja de medidor y de la protección general de servicio, con su base, canalizaciones de entrada y salida y precintado. Incluye el replanteo en la posición y altura que exige la compañía suministradora, requisito sin el cual no se autoriza la conexión, el anclaje de la caja, la entrada de canalizaciones con sus prensaestopas, el montaje de la protección general y la preparación para la inspección y precintado por parte de la compañía. Medido por unidad instalada.":
    "Installation of the meter enclosure and the service protective device, with its base, the inlet and outlet conduits and sealing. Includes setting out at the position and height the supply company requires, a requirement without which the connection is not authorized, anchoring the enclosure, bringing in the conduits with their glands, fitting the main protection and preparing for inspection and sealing by the company. Measured per unit installed.",

"Acometida eléctrica subterránea. Incluye el tendido y la conexión. Medido por acometida ejecutada.":
    "Underground electrical service connection. Includes laying and the connection. Measured per service connection constructed.",

"Ejecución de la puesta a tierra de la instalación mediante electrodo de cobre enterrado, con su conductor de protección, conector y caja de inspección registrable. Sin puesta a tierra efectiva, el interruptor diferencial no dispone del camino de fuga que necesita para actuar, de modo que ambos elementos funcionan como sistema o no funcionan. Incluye la excavación, el hincado del electrodo, la conexión del conductor con conector de compresión, la caja de inspección registrable, el tendido hasta el tablero y la medición de la resistencia de tierra con telurómetro, que es lo que acredita que el sistema sirve. Medido por puesta a tierra ejecutada.":
    "Installation of the grounding of the installation with a buried copper electrode, with its protective conductor, connector and an inspection pit. Without effective grounding, the ground-fault circuit interrupter does not have the leakage path it needs to operate, so the two elements work as a system or do not work at all. Includes excavation, driving the electrode, connecting the conductor with a compression connector, the inspection pit, running to the panel and measuring the ground resistance with a ground resistance tester, which is what proves the system works. Measured per grounding installation constructed.",

"Puesta a tierra con electrodo de cobre. Incluye el hincado y la conexión. Medido por toma ejecutada.":
    "Grounding with a copper electrode. Includes driving it and the connection. Measured per ground electrode constructed.",

# ── Tablero y protecciones ────────────────────────────────────────────────
"Suministro y montaje de tablero eléctrico de distribución empotrado o de sobreponer, con su barraje de neutro y tierra, y espacio de reserva para ampliaciones. Incluye el replanteo en punto accesible y no obstruido, la apertura del hueco y el montaje enrasado, la entrada ordenada de las canalizaciones, el montaje del barraje, la conexión de los circuitos con el conductor peinado e identificado, la colocación del directorio de circuitos rotulado, que es lo que permite a cualquiera localizar una falla sin ir probando, y la prueba de continuidad y aislamiento. Medido por tablero instalado.":
    "Supply and installation of an electrical distribution panel, flush or surface mounted, with its neutral and ground busbars and spare space for additions. Includes setting out at a point that is accessible and not obstructed, forming the recess and mounting flush, bringing the conduits in tidily, fitting the busbars, connecting the circuits with the cables dressed and identified, fitting the labelled circuit schedule, which is what allows anyone to find a fault without testing each one, and the continuity and insulation test. Measured per panel installed.",

"Suministro y montaje de interruptor termomagnético en el tablero, con su conexión e identificación. La capacidad del interruptor debe corresponder al calibre del conductor que protege, no al consumo del equipo: un interruptor sobredimensionado deja de proteger el cable y lo convierte en el fusible del circuito. Incluye el montaje sobre riel, la conexión de fase y su apriete al par, el rotulado del circuito en el directorio y la prueba de disparo. Medido por unidad instalada.":
    "Supply and installation of a circuit breaker in the panel, with its connection and identification. The rating of the breaker has to match the size of the conductor it protects, not the consumption of the equipment: an oversized breaker stops protecting the cable and turns it into the fuse of the circuit. Includes mounting on the rail, connecting the phase and tightening it to torque, labelling the circuit on the schedule and the tripping test. Measured per unit installed.",

"Suministro y montaje de interruptor diferencial de alta sensibilidad en el tablero, con su conexión y prueba. Es el dispositivo que protege a las personas frente al contacto eléctrico: los termomagnéticos protegen la instalación, no a quien la toca. Su instalación es obligada en circuitos de baños, cocinas y exteriores. Incluye el montaje sobre riel, el conexionado de fases y neutro respetando el orden, la comprobación de que ningún neutro del circuito protegido se une aguas abajo con otro circuito, error que provoca disparos intermitentes imposibles de diagnosticar, y la prueba con el botón de test y con equipo de medida. Medido por unidad instalada.":
    "Supply and installation of a high sensitivity ground-fault circuit interrupter in the panel, with its connection and testing. It is the device that protects people against electric shock: circuit breakers protect the installation, not the person who touches it. It is required on circuits for bathrooms, kitchens and outside. Includes mounting on the rail, connecting the phases and the neutral respecting the order, checking that no neutral of the protected circuit is joined downstream to another circuit, an error that causes intermittent tripping impossible to diagnose, and testing with the test button and with measuring equipment. Measured per unit installed.",

"Revisión completa de la instalación eléctrica ejecutada, con medición de continuidad, aislamiento, resistencia de puesta a tierra y prueba de disparo de los diferenciales, y emisión del informe de resultados. Es lo que acredita ante el cliente que la instalación no solo funciona sino que es segura, y el documento que respalda al instalador si más adelante hay una incidencia. Incluye la inspección visual del tablero y de los puntos, las mediciones con equipo calibrado, la comprobación del rotulado de circuitos, las pruebas de disparo y la entrega del informe con los valores obtenidos. Medido por instalación revisada y certificada.":
    "Full review of the electrical installation as built, with measurement of continuity, insulation and ground resistance and tripping test of the ground-fault circuit interrupters, and the issue of a report of results. It is what shows the client that the installation not only works but is safe, and the document that backs the installer if there is an incident later. Includes visual inspection of the panel and of the outlets, measurements with calibrated equipment, checking the labelling of the circuits, the tripping tests and delivery of the report with the values obtained. Measured per installation reviewed and certified.",

"Suministro y montaje de tablero eléctrico con protecciones. Incluye el montaje y la conexión. Medido por unidad instalada.":
    "Supply and installation of an electrical panel with protective devices. Includes assembly and the connection. Measured per unit installed.",
"Instalación de interruptor termomagnético. Incluye la conexión. Medido por unidad instalada.":
    "Installation of a circuit breaker. Includes the connection. Measured per unit installed.",
"Instalación de interruptor diferencial. Incluye la conexión. Medido por unidad instalada.":
    "Installation of a ground-fault circuit interrupter. Includes the connection. Measured per unit installed.",
"Ejecución de tablero eléctrico para baño., con conexión. Incluye la conexión y la fijación. Medido por unidad ejecutada.":
    "Installation of an electrical panel for a bathroom, with the connection. Includes the connection and fixing. Measured per unit constructed.",

# ── Canalizaciones ────────────────────────────────────────────────────────
"Canalización eléctrica no empotrada, tendida por el plenum del cielo raso o vista sobre superficie con tubería conduit y sus abrazaderas, con conductor de cobre. Frente a la canalización empotrada evita el picado y el resane, y deja la instalación registrable, lo que la hace preferible en reforma siempre que el trazado quede oculto. Incluye el replanteo, la fijación de la tubería con abrazaderas a la separación indicada, el tendido de los conductores, la identificación de circuitos y las cajas de derivación en puntos accesibles. Medido en longitud realmente instalada.":
    "Surface electrical conduit run in the ceiling plenum or fixed on the surface with conduit and its clips, with copper conductor. Against concealed conduit it avoids hacking out and making good, and leaves the installation accessible, which makes it preferable in refurbishment provided the run stays hidden. Includes setting out, fixing the conduit with clips at the spacing indicated, drawing in the conductors, identifying the circuits and the junction boxes at accessible points. Measured by the length actually installed.",

"Canalización eléctrica dedicada para equipo de climatización, con su tubería, conductor de calibre adecuado y previsión de la protección independiente en el tablero. Incluye el replanteo del recorrido entre el tablero y la unidad, la apertura de roza o el tendido por plenum, el tendido del conductor dimensionado a la potencia del equipo, el paso a la unidad exterior con su sellado del pase en fachada y la identificación del circuito. Medido en longitud realmente instalada.":
    "Dedicated electrical conduit for air conditioning equipment, with its conduit, a conductor of the right size and provision for the separate protective device in the panel. Includes setting out the route between the panel and the unit, cutting the chase or running in the plenum, drawing in the conductor sized to the power of the unit, the penetration to the outdoor unit with the seal at the facade and identifying the circuit. Measured by the length actually installed.",

"Canalización eléctrica empotrada con conduit. Incluye el tendido del conduit. Medido por metro lineal instalado.":
    "Concealed electrical conduit. Includes laying the conduit. Measured per meter installed.",
"Ejecución de canalización eléctrica en piso., con conexión. Incluye la conexión y la fijación. Medido por unidad ejecutada.":
    "Installation of electrical conduit in the floor, with the connection. Includes the connection and fixing. Measured per unit constructed.",
"Ejecución de canalización eléctrica en techo., con conexión. Incluye la conexión y la fijación. Medido por unidad ejecutada.":
    "Installation of electrical conduit in the ceiling, with the connection. Includes the connection and fixing. Measured per unit constructed.",

"Instalación de canalización eléctrica empotrada formada por tubería conduit corrugada de PVC de 20 mm y tres conductores de cobre THW calibre 12 AWG, incluyendo fase, neutro y tierra. Incluye replanteo del trazado, apertura de roza con rozadora eléctrica con captación de polvo, colocación y fijación del conduit, guiado y tendido de los conductores, identificación de circuitos y tapado de roza con mortero de reparación. No incluye cajas, mecanismos ni el acabado del paramento. Medido en longitud realmente instalada.":
    "Installation of concealed electrical conduit in 20 mm corrugated PVC conduit with three 12 AWG THW copper conductors, comprising phase, neutral and ground. Includes setting out the run, cutting the chase with an electric wall chaser with dust extraction, placing and fixing the conduit, drawing in the conductors, identifying the circuits and filling the chase with a repair mortar. It does not include boxes, accessories or the finish to the wall. Measured by the length actually installed.",

"Canalización eléctrica con conductor de 10 AWG. Incluye el tendido del conductor. Medido por metro lineal instalado.":
    "Electrical conduit with a 10 AWG conductor. Includes drawing in the conductor. Measured per meter installed.",

# ── Puntos de fuerza ──────────────────────────────────────────────────────
"Punto de fuerza dedicado para electrodoméstico o equipo de consumo elevado, con conductor de mayor calibre, su toma específica y protección independiente en el tablero. Los equipos de alto consumo como aire acondicionado, calentador, cocina eléctrica o secadora exigen circuito propio: compartirlo con tomas generales es la causa más frecuente de sobrecalentamiento de conductores. Incluye la canalización, el conductor de calibre adecuado a la potencia, la caja y la toma, el conexionado y la comprobación de continuidad y de caída de tensión. Medido por punto terminado y probado.":
    "Dedicated power outlet for an appliance or equipment of high consumption, with a conductor of larger size, its specific receptacle and a separate protective device in the panel. High consumption equipment such as air conditioning, a water heater, an electric range or a dryer needs its own circuit: sharing it with general purpose receptacles is the most frequent cause of conductors overheating. Includes the conduit, the conductor sized to the power, the box and the receptacle, the connections and checking continuity and voltage drop. Measured per point completed and tested.",

"Reubicación de un punto eléctrico existente, con el traslado de la caja y del mecanismo a la nueva posición y el anulado del punto anterior. Es de las intervenciones más frecuentes en reforma al cambiar la distribución del mobiliario. Incluye el corte y verificación de ausencia de tensión, la apertura de la nueva roza y caja, el desvío del conductor con caja de derivación registrable, ya que un empalme enterrado sin registro es una falla futura imposible de localizar, el montaje del mecanismo en la nueva posición, el tapado y resane de la caja anulada y la prueba. Medido por punto reubicado.":
    "Relocation of an existing electrical point, moving the box and the device to the new position and abandoning the previous point. It is one of the most frequent interventions in refurbishment when the layout of the furniture changes. Includes isolating and verifying dead, forming the new chase and box, diverting the conductor through an accessible junction box, since a buried joint with no access is a future fault impossible to find, fitting the device in the new position, filling in and making good the abandoned box and testing. Measured per point relocated.",

"Punto de fuerza para cocina o electrodoméstico. Incluye la conexión. Medido por punto ejecutado.":
    "Power outlet for a kitchen or an appliance. Includes the connection. Measured per point constructed.",
"Punto de fuerza para secadora. Incluye la conexión. Medido por punto ejecutado.":
    "Power outlet for a dryer. Includes the connection. Measured per point constructed.",
"Punto de fuerza para horno empotrado. Incluye la conexión. Medido por punto ejecutado.":
    "Power outlet for a built-in oven. Includes the connection. Measured per point constructed.",
"Ejecución de punto de fuerza para cocina eléctrica., con conexión. Incluye la conexión y la fijación. Medido por unidad ejecutada.":
    "Installation of a power outlet for an electric range, with the connection. Includes the connection and fixing. Measured per unit constructed.",
"Ejecución de punto de fuerza para secadora eléctrica., con conexión. Incluye la conexión y la fijación. Medido por unidad ejecutada.":
    "Installation of a power outlet for an electric dryer, with the connection. Includes the connection and fixing. Measured per unit constructed.",

"Ejecución de punto eléctrico de interruptor o tomacorriente, formado por caja de mecanismo empotrada, conexionado de los conductores del circuito correspondiente, mecanismo de gama estándar y placa embellecedora. Incluye apertura del hueco de la caja, fijación y enrase con el paramento, conexionado con apriete y verificación de continuidad y polaridad, colocación del mecanismo y comprobación de funcionamiento. Medido por unidad de punto terminado y probado.":
    "Installation of an electrical point for a switch or a receptacle, comprising a flush back box, connection of the conductors of the corresponding circuit, a standard range device and a cover plate. Includes forming the recess for the box, fixing it and setting it flush with the wall, connecting and tightening and checking continuity and polarity, fitting the device and checking the operation. Measured per point completed and tested.",

"Punto de tomacorriente doble. Incluye la caja y el mecanismo. Medido por punto ejecutado.":
    "Duplex receptacle point. Includes the box and the device. Measured per point constructed.",
"Punto de interruptor doble. Incluye la caja y el mecanismo. Medido por punto ejecutado.":
    "Two-gang switch point. Includes the box and the device. Measured per point constructed.",
"Ejecución de punto de tomacorriente con usb., con conexión. Incluye la conexión y la fijación. Medido por unidad ejecutada.":
    "Installation of a receptacle point with USB, with the connection. Includes the connection and fixing. Measured per unit constructed.",
"Ejecución de punto de interruptor de conmutación., con conexión. Incluye la conexión y la fijación. Medido por unidad ejecutada.":
    "Installation of a three-way switch point, with the connection. Includes the connection and fixing. Measured per unit constructed.",

# ── Iluminación ───────────────────────────────────────────────────────────
"Instalación de luminaria empotrada en cielo raso, con su conexión y ajuste. Incluye el replanteo de la posición coordinado con la estructura del cielo raso para no cortar una maestra, el corte del hueco con la herramienta adecuada al material, la conexión con conector rápido dejando holgura de cable para poder bajar la luminaria en un futuro mantenimiento, el montaje con sus muelles o clips y la prueba de encendido. La luminaria la elige el cliente y se presupuesta aparte. Medido por unidad instalada.":
    "Installation of a recessed light fixture in the ceiling, with its connection and adjustment. Includes setting out the position coordinated with the ceiling framing so as not to cut a furring channel, cutting the opening with the tool suited to the material, connecting with a quick connector leaving slack in the cable so that the fixture can be taken down for future maintenance, fitting it with its springs or clips and testing that it lights. The fixture is selected by the client and priced separately. Measured per unit installed.",

"Instalación de luminaria de sobreponer, aplique o colgante, con su fijación y conexión. Incluye el replanteo, la comprobación de que el punto de anclaje soporta el peso de la luminaria, que en colgantes y lámparas de gran formato exige refuerzo previo en el cielo raso, la fijación mecánica, la conexión, el ajuste de altura en colgantes y la prueba de encendido. La luminaria la elige el cliente y se presupuesta aparte. Medido por unidad instalada.":
    "Installation of a surface mounted light fixture, wall light or pendant, with its fixing and connection. Includes setting out, checking that the anchorage point carries the weight of the fixture, which on pendants and large fixtures needs strengthening in the ceiling beforehand, the mechanical fixing, the connection, adjusting the drop on pendants and testing that it lights. The fixture is selected by the client and priced separately. Measured per unit installed.",

"Suministro e instalación de cinta LED con su perfil de aluminio disipador, difusor y fuente de alimentación, para iluminación indirecta en cornisas, bajo muebles o en nichos. El perfil de aluminio no es decorativo: disipa el calor de los diodos, y sin él la cinta pierde luminosidad y vida útil rápidamente. Incluye el replanteo, el montaje del perfil, la colocación de la cinta con corte solo por los puntos marcados, la conexión y el emplazamiento de la fuente en punto registrable, y la prueba. Medido en longitud realmente instalada.":
    "Supply and installation of an LED strip with its aluminum heat sink profile, diffuser and driver, for indirect lighting in cornices, under cabinets or in recesses. The aluminum profile is not decorative: it dissipates the heat from the diodes, and without it the strip loses brightness and service life quickly. Includes setting out, fitting the profile, laying the strip and cutting only at the marked points, the connection and siting the driver at an accessible point, and testing. Measured by the length actually installed.",

"Instalación de reflector o luminaria de exterior, con su soporte, conexión estanca y protección. Incluye la fijación del soporte, la conexión mediante prensaestopas y caja estanca con el grado de protección adecuado a la intemperie, el sellado de la entrada de cable orientando el bucle hacia abajo para que el agua no escurra hacia el interior del equipo, la orientación del haz y la prueba. La luminaria la elige el cliente y se presupuesta aparte. Medido por unidad instalada.":
    "Installation of an external floodlight or light fixture, with its bracket, a weathertight connection and protection. Includes fixing the bracket, connecting through cable glands and a weatherproof box with the ingress protection rating suited to the exposure, sealing the cable entry with the drip loop turned down so that water does not run into the equipment, aiming the beam and testing. The fixture is selected by the client and priced separately. Measured per unit installed.",

"Punto eléctrico para ventilador de techo, con su caja reforzada, canalización, conductor y mando. La caja debe ser específica para ventilador y estar anclada a un elemento estructural o a un refuerzo del cielo raso: una caja de luminaria común no está diseñada para soportar el peso y la vibración de un ventilador en marcha. Incluye el replanteo, el refuerzo del anclaje, la caja específica, la canalización y el conductor con el hilo adicional del control de velocidad, el mecanismo de mando y la prueba. Medido por punto terminado y probado.":
    "Electrical point for a ceiling fan, with its fan-rated box, conduit, conductor and control. The box has to be specifically rated for a fan and anchored to a structural member or to a ceiling brace: an ordinary light fixture box is not designed to carry the weight and the vibration of a fan running. Includes setting out, strengthening the anchorage, the fan-rated box, the conduit and the conductor with the additional core for the speed control, the control device and testing. Measured per point completed and tested.",
}
