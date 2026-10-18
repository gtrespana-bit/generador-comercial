# -*- coding: utf-8 -*-
"""Descripciones — Revestimientos y acabados (14 de n): cielos rasos.

Vocabulario aplicado:

· «Cielo raso continuo» es continuous ceiling, el de placa suspendida,
  frente al de bandejas registrables.
· La «perfiles» que forman la estructura son furring channels, la
  «varilla» que cuelga es hanger rod y la «horquilla» que la engancha
  es clip. El «ángulo perimetral» es perimeter angle.
· «Nivelación con manguera» es leveling with a water level, y con láser
  with a laser.
· «Desolidarizado» es isolated, y es la condición de la que depende el
  aislamiento: un «puente rígido» es a rigid bridge, y un solo tornillo
  basta para crearlo.
· «Foso» y «cajón» perimetral para ocultar cortina o luz son recessed
  pocket y perimeter box section; la «cenefa» que lo corona es cornice.
· «Juntas contrapeadas» son staggered joints, como en el trasdosado.
· «Guardacantos» es corner bead, el perfil que remata la arista.
· «Alero» exterior es external soffit, y ahí la placa de cemento aguanta
  lo que la de yeso no.
"""

LOTE = {
    "Cielo raso continuo formado por una placa de yeso laminado de 12,5 mm atornillada a estructura oculta de perfilería de acero galvanizado, suspendida de la losa mediante varilla y horquilla, con ángulo perimetral en todo el contorno. Incluye replanteo y nivelación con manguera o láser, colocación del perímetro, montaje y nivelación de las maestras, atornillado de las placas, tratamiento de juntas con cinta y pasta, lijado hasta dejar la superficie lista para pintar, y previsión de los huecos de luminarias y rejillas. Medido en superficie realmente ejecutada.":
        "Continuous ceiling formed by a 12.5 mm drywall screwed to a concealed framework of galvanized steel sections, suspended from the slab by hanger rod and clip, with a perimeter angle around the whole edge. Includes setting out and leveling with a water level or a laser, fitting the perimeter, installing and leveling the furring channels, screwing the boards, the joint treatment with tape and compound, sanding until the surface is ready to paint, and forming the openings for light fittings and grilles. Measured by the area actually completed.",

    "Cielo raso continuo con placa de yeso laminado resistente a la humedad de 12,5 mm sobre estructura oculta suspendida, para baños, cocinas y áreas de servicio. La placa resistente a la humedad soporta la condensación y la humedad ambiental, pero no una filtración: si hay gotera desde la losa superior hay que resolverla antes, porque ninguna placa la aguanta. Incluye replanteo y nivelación, ángulo perimetral, montaje y nivelación de maestras, atornillado de placas, tratamiento de juntas con cinta y pasta, lijado y previsión de huecos de luminarias y rejillas. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Continuous ceiling of 12.5 mm moisture resistant drywall on a concealed suspended framework, for bathrooms, kitchens and service areas. The moisture resistant board withstands condensation and ambient humidity, but not a leak: if there is water coming through from the slab above it has to be dealt with first, because no board will take it. Includes setting out and leveling, the perimeter angle, installing and leveling the furring channels, screwing the boards, the joint treatment with tape and compound, sanding and forming the openings for light fittings and grilles. Measured by the area actually completed, deducting openings larger than 1 m².",

    "Cielo raso continuo con doble placa de yeso laminado sobre estructura suspendida con horquillas antivibratorias y lana mineral en la cámara, para reducir la transmisión de ruido aéreo y de impacto desde la planta superior. La mejora acústica depende tanto de la masa de la doble placa como de que la estructura quede desolidarizada: si un solo tornillo hace puente rígido con la losa, el aislamiento cae. Incluye replanteo, ángulo perimetral con banda elástica, montaje de la estructura con elementos antivibratorios, colocación de la lana, atornillado de las dos capas a juntas contrapeadas, tratamiento de juntas y lijado. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Continuous ceiling with a double layer of drywall on a framework suspended with anti-vibration clips and mineral wool in the cavity, to reduce the transmission of airborne and impact noise from the floor above. The acoustic improvement depends as much on the mass of the double board as on the framework being isolated: if a single screw makes a rigid bridge to the slab, the insulation drops. Includes setting out, the perimeter angle with an elastic strip, installing the framework with anti-vibration elements, placing the wool, screwing the two layers with staggered joints, the joint treatment and sanding. Measured by the area actually completed, deducting openings larger than 1 m².",

    "Formación de foso o cajón perimetral en cielo raso de yeso laminado para alojar cortinas, persianas o iluminación oculta. Incluye el replanteo de la línea y de la profundidad del cajón coordinada con el ancho del sistema de cortina, el montaje de la estructura de refuerzo, el forrado con placa por las tres caras, el tratamiento de juntas y aristas con perfil guardacantos, el lijado y la previsión de registro para el mecanismo. Medido en longitud realmente ejecutada.":
        "Formation of a recessed pocket or perimeter box section in a drywall ceiling to house curtains, blinds or concealed lighting. Includes setting out the line and the depth of the pocket coordinated with the width of the curtain system, installing the reinforcing framework, lining it with board on the three faces, the joint and arris treatment with corner bead, sanding and forming an access opening for the mechanism. Measured by the length actually completed.",

    "Suministro y colocación de tapa de registro practicable en cielo raso, para acceso a llaves de paso, cajas de conexión, equipos de climatización o cualquier elemento que requiera mantenimiento. Colocarlo es la diferencia entre revisar una llave en dos minutos o romper el cielo raso. Incluye el replanteo coordinado con la posición real del elemento a registrar, el corte del hueco, el refuerzo del borde con perfilería, el montaje del marco enrasado con la placa y el ajuste de la tapa. Medido por unidad colocada.":
        "Supply and installation of an access panel in a ceiling, for access to shut-off valves, junction boxes, air conditioning units or any element that needs maintenance. Fitting one is the difference between checking a valve in two minutes and breaking open the ceiling. Includes setting out coordinated with the real position of the element to be accessed, cutting the opening, reinforcing the edge with sections, fitting the frame flush with the board and adjusting the panel. Measured per unit installed.",

    "Cielo raso de yeso laminado con dos o más niveles, formando escalones, nichos o bandejas, con su estructura de refuerzo en los cambios de plano. Cada cambio de nivel supone un frente vertical que hay que estructurar, forrar por dos caras y rematar con guardacantos, lo que multiplica el trabajo frente a un cielo plano de la misma superficie. Incluye el replanteo de las líneas de quiebre, la estructura de ambos planos y de los frentes, el forrado, el tratamiento de juntas y aristas con perfil, el lijado y la previsión de registros e iluminación. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Drywall ceiling with two or more levels, forming steps, niches or trays, with its reinforcing framework at the changes of plane. Each change of level means a vertical face that has to be framed, lined on two faces and finished with corner bead, which multiplies the work compared with a flat ceiling of the same area. Includes setting out the break lines, the framework of both planes and of the faces, the lining, the joint and arris treatment with bead, sanding and forming the openings for access panels and lighting. Measured by the area actually completed, deducting openings larger than 1 m².",

    "Cielo raso continuo de placa de yeso laminado con panel de lana mineral en la cámara, para aislamiento acústico. Incluye la estructura suspendida, la lana y la placa con su tratamiento de juntas. Medido por metro cuadrado ejecutado.":
        "Continuous ceiling of drywall with a mineral wool panel in the cavity, for acoustic insulation. Includes the suspended framework, the wool and the board with its joint treatment. Measured per square meter completed.",

    "Cielo raso continuo de placa de yeso laminado resistente al fuego, para protección de estructura e instalaciones. Incluye la estructura suspendida, la placa ignífuga y el tratamiento de juntas. Medido por metro cuadrado ejecutado.":
        "Continuous ceiling of fire rated drywall, for the protection of structure and services. Includes the suspended framework, the fire rated board and the joint treatment. Measured per square meter completed.",

    "Cielo raso continuo curvo de placa de yeso laminado, con estructura conformada según el diseño. Incluye la estructura curva, la placa conformada y el tratamiento de juntas. Medido por metro cuadrado ejecutado.":
        "Continuous curved ceiling of drywall, with a framework shaped to the design. Includes the curved framework, the shaped board and the joint treatment. Measured per square meter completed.",

    "Ejecución de cenefa o foso perimetral integrado en el cielo raso de yeso para iluminación indirecta. Incluye la estructura del foso, la placa y el remate. Medido por metro lineal de cenefa.":
        "Formation of a cornice or perimeter recess integrated in the gypsum ceiling for indirect lighting. Includes the framework of the recess, the board and the trim. Measured per meter of cornice.",

    "Cielo raso continuo de yeso a una pendiente o inclinado, con estructura conformada al faldón. Incluye la estructura inclinada, la placa y el tratamiento de juntas. Medido por metro cuadrado ejecutado.":
        "Continuous gypsum ceiling on a slope or inclined, with a framework shaped to the pitch. Includes the inclined framework, the board and the joint treatment. Measured per square meter completed.",

    "Cielo raso continuo de doble placa de yeso laminado con panel de lana mineral, para aislamiento acústico y térmico reforzado. Incluye la estructura suspendida, la lana, la doble placa y el tratamiento de juntas. Medido por metro cuadrado ejecutado.":
        "Continuous ceiling with a double layer of drywall and a mineral wool panel, for reinforced acoustic and thermal insulation. Includes the suspended framework, the wool, the double board and the joint treatment. Measured per square meter completed.",

    "Cielo raso continuo de placa de yeso perforada acústica, para locales que requieren absorción. Incluye la estructura suspendida, la placa perforada y el tratamiento de juntas. Medido por metro cuadrado ejecutado.":
        "Continuous ceiling of perforated acoustic drywall, for premises that require absorption. Includes the suspended framework, the perforated board and the joint treatment. Measured per square meter completed.",

    "Cielo raso continuo de placa de cemento reforzada con fibra en voladizo o alero exterior. Incluye la estructura, la placa de cemento y el sellado de juntas. Medido por metro cuadrado ejecutado.":
        "Continuous ceiling of fiber cement board on a cantilever or external soffit. Includes the framework, the cement board and sealing the joints. Measured per square meter completed.",

    "Cielo raso continuo de placa de yeso con foso integrado para iluminación empotrada. Incluye la estructura, el foso, la placa y el tratamiento de juntas. Medido por metro cuadrado ejecutado.":
        "Continuous drywall ceiling with an integrated recess for recessed lighting. Includes the framework, the recess, the board and the joint treatment. Measured per square meter completed.",
}
