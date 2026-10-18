# -*- coding: utf-8 -*-
"""Descripciones — Revestimientos y acabados (12 de n): escaleras y trasdosados.

Vocabulario aplicado:

· «Trasdosado autoportante» es self-supporting lining: una hoja que se
  tiene en pie por sí misma, separada del muro. En inglés británico es
  dry lining, y la variante lo ajusta.
· «Montantes» son studs y los «canales de arranque» son base and head
  tracks, los perfiles de suelo y de techo entre los que se montan.
· «Banda perimetral de estanqueidad» es perimeter sealing strip, la que
  cierra el paso del sonido y del aire por el contorno.
· «Juntas alternadas» son staggered joints, y son las que hacen que una
  doble placa funcione como masa y no como dos hojas.
· «Lana mineral» es mineral wool, y hay que colocarla «sin comprimirla»,
  without compressing it, porque comprimida aísla la mitad.
· «Medianería» es party wall y el vecino de al lado es the adjoining
  property.
· «Remates» de un pasamanos son end caps, y sus «soportes» brackets.
· «Placa de yeso laminado» es drywall, y la resistente a la
  humedad es moisture resistant board.
"""

LOTE = {
    "Revestimiento de peldaño de escalera con lámina o pieza vinílica, con perfil antideslizante. Incluye la preparación del soporte y la colocación del revestimiento. Medido por metro lineal de peldaño.":
        "Covering of a stair tread with a vinyl sheet or tile, with an anti-slip profile. Includes preparing the substrate and laying the covering. Measured per meter of tread.",

    "Suministro y colocación de peldaño prefabricado de concreto sobre estructura existente. Incluye la preparación del soporte, la colocación y el nivelado del peldaño. Medido por unidad de peldaño colocada.":
        "Supply and installation of a precast concrete tread over an existing structure. Includes preparing the substrate, placing and leveling the tread. Measured per tread installed.",

    "Colocación de peldaño de madera flotante sobre escalera existente, con fijación. Incluye la preparación del soporte y la fijación del peldaño. Medido por metro lineal de peldaño.":
        "Fixing of a floating wood tread over an existing stair, with fixing. Includes preparing the substrate and fixing the tread. Measured per meter of tread.",

    "Revestimiento de rampa con pieza antideslizante o sistema de resinas, para circulación segura. Incluye la preparación del soporte y la colocación del revestimiento. Medido por metro cuadrado revestido.":
        "Covering of a ramp with an anti-slip tile or a resin system, for safe circulation. Includes preparing the substrate and laying the covering. Measured per square meter covered.",

    "Colocación de nariz de peldaño de metal (aluminio o acero) con perfil antideslizante. Incluye la fijación del perfil a la nariz del peldaño. Medido por metro lineal de nariz.":
        "Fixing of a metal stair nosing (aluminum or steel) with an anti-slip profile. Includes fixing the profile to the stair nosing. Measured per meter of nosing.",

    "Ejecución de junta de dilatación en escalera, con perfil y sellado elástico. Incluye la colocación del perfil y el sellado de la junta. Medido por metro lineal de junta.":
        "Formation of a movement joint in a stair, with a profile and a flexible sealing. Includes placing the profile and sealing the joint. Measured per meter of joint.",

    "Colocación de pasamanos de madera sobre escalera, con soportes y remates. Incluye la fijación del pasamanos y el acabado. Medido por metro lineal de pasamanos.":
        "Fixing of a wood handrail on a stair, with brackets and end caps. Includes fixing the handrail and the finish. Measured per meter of handrail.",

    "Suministro y montaje de trasdosado autoportante de placa de yeso laminado estándar de 12,5 mm, sobre estructura de acero galvanizado separada del muro, sin aislamiento. Incluye el replanteo de la estructura con montantes cada 60 cm, la fijación de canales de arranque al piso y al techo con banda perimetral de estanqueidad, el atornillado de la placa, el tratamiento de juntas con pasta y cinta, y el remate de encuentros con muros y techo. Medido por metro cuadrado de trasdosado terminado.":
        "Supply and installation of a self-supporting lining of standard 12.5 mm drywall, on a galvanized steel framework held off the wall, without insulation. Includes setting out the framework with studs every 60 cm, fixing the base and head tracks to the floor and to the ceiling with a perimeter sealing strip, screwing the board, treating the joints with compound and tape, and finishing the junctions with the walls and the ceiling. Measured per square meter of lining completed.",

    "Suministro y montaje de trasdosado autoportante de placa de yeso laminado de 12,5 mm con panel de lana mineral de 60 mm en la cámara, para aislamiento térmico y acústico. Incluye la estructura separada del muro, la colocación del panel de lana en la cámara sin comprimirlo, el atornillado de la placa y el tratamiento de juntas. Medido por metro cuadrado de trasdosado terminado.":
        "Supply and installation of a self-supporting lining of 12.5 mm drywall with a 60 mm mineral wool panel in the cavity, for thermal and acoustic insulation. Includes the framework held off the wall, placing the mineral wool panel in the cavity without compressing it, screwing the board and the joint treatment. Measured per square meter of lining completed.",

    "Suministro y montaje de trasdosado autoportante de placa de yeso laminado resistente a la humedad de 12,5 mm, para baños, cocinas y locales con condensación. Incluye la estructura separada del muro, el atornillado de la placa, el tratamiento de juntas con pasta y cinta apropiadas para humedad y el remate de encuentros. Medido por metro cuadrado de trasdosado terminado.":
        "Supply and installation of a self-supporting lining of 12.5 mm moisture resistant drywall, for bathrooms, kitchens and premises subject to condensation. Includes the framework held off the wall, screwing the board, the joint treatment with compound and tape suited to moisture and finishing the junctions. Measured per square meter of lining completed.",

    "Suministro y montaje de trasdosado autoportante con doble placa de yeso laminado de 12,5 mm, para aumentar la masa acústica y la resistencia al impacto. Incluye la estructura separada del muro, el atornillado de las dos placas con juntas alternadas, el tratamiento de juntas en ambas capas y el remate de encuentros. Medido por metro cuadrado de trasdosado terminado.":
        "Supply and installation of a self-supporting lining with a double layer of 12.5 mm drywall, to increase the acoustic mass and the impact resistance. Includes the framework held off the wall, screwing both boards with staggered joints, the joint treatment on both layers and finishing the junctions. Measured per square meter of lining completed.",

    "Suministro y montaje de trasdosado de medianería sobre muro medianero, con estructura autoportante, panel de lana mineral de 60 mm y placa de yeso laminado de 12,5 mm, para aislar del ruido y la humedad del vecino. Incluye la banda perimetral, la colocación del panel, el atornillado de la placa y el tratamiento de juntas. Medido por metro cuadrado de trasdosado terminado.":
        "Supply and installation of a party wall lining over a party wall, with a self-supporting framework, a 60 mm mineral wool panel and 12.5 mm drywall, to insulate against noise and damp from the adjoining property. Includes the perimeter strip, placing the panel, screwing the board and the joint treatment. Measured per square meter of lining completed.",

    "Suministro y montaje de trasdosado autoportante de placa de yeso laminado con refuerzo interior de madera o perfil metálico, para el anclaje posterior de cargas como muebles colgados, televisores o estanterías. Incluye la estructura, la colocación del refuerzo en la posición prevista para las cargas, el atornillado de la placa y el tratamiento de juntas. Medido por metro cuadrado de trasdosado terminado.":
        "Supply and installation of a self-supporting lining of drywall with internal reinforcement in wood or a metal profile, for the later anchoring of loads such as hung cabinets, televisions or shelving. Includes the framework, placing the reinforcement in the position intended for the loads, screwing the board and the joint treatment. Measured per square meter of lining completed.",

    "Trasdosado autoportante con doble placa de yeso laminado y panel de lana mineral en la cámara, para aislamiento térmico y acústico reforzado. Incluye la estructura, la lana, el doble atornillado y el tratamiento de juntas. Medido por metro cuadrado de trasdosado terminado.":
        "Self-supporting lining with a double layer of drywall and a mineral wool panel in the cavity, for reinforced thermal and acoustic insulation. Includes the framework, the wool, the double screwing and the joint treatment. Measured per square meter of lining completed.",
}
