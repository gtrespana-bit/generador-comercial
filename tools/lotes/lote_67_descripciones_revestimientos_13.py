# -*- coding: utf-8 -*-
"""Descripciones — Revestimientos y acabados (13 de n): trasdosados y forros.

Vocabulario aplicado:

· «Trasdosado directo» es el que va pegado al muro: direct lining,
  adherido «en pelladas», in dabs, que es como se aplica el adhesivo de
  yeso y como se dice en inglés.
· «Forro» es lining cuando va sobre estructura; «cajón» o «falso pilar»
  para ocultar instalaciones es boxed section o false pier.
· «Obra húmeda» es wet trades: todo lo que hay que esperar a que seque,
  y que es justo lo que estos sistemas evitan.
· «Placa resistente al fuego» es fire rated board y el forro que se
  hace con ella es fire resistant lining.
· «Registro de acceso practicable» es access panel, y es la pieza que
  convierte un trasdosado registrable en uno que hay que romper.
· «Pasos de instalaciones» son service penetrations, y su sellado es lo
  que mantiene la resistencia al fuego del conjunto.
· «Cabezas de tornillo» son screw heads y se cubren con filling, como
  las juntas.
"""

LOTE = {
    "Trasdosado autoportante de placa de yeso laminado con barrera de vapor en la cámara, para paramentos expuestos a humedad. Incluye la estructura, la barrera de vapor, la placa y el tratamiento de juntas. Medido por metro cuadrado de trasdosado terminado.":
        "Self-supporting lining of drywall with a vapor barrier in the cavity, for substrates exposed to moisture. Includes the framework, the vapor barrier, the board and the joint treatment. Measured per square meter of lining completed.",

    "Trasdosado autoportante curvo de placa de yeso laminado conformada según el radio de diseño. Incluye la estructura curva, la placa conformada y el tratamiento de juntas. Medido por metro cuadrado de trasdosado terminado.":
        "Self-supporting curved lining of drywall shaped to the design radius. Includes the curved framework, the shaped board and the joint treatment. Measured per square meter of lining completed.",

    "Trasdosado autoportante con placa de yeso perforada acústica, para mejorar la absorción del local. Incluye la estructura, la placa perforada y el tratamiento de juntas. Medido por metro cuadrado de trasdosado terminado.":
        "Self-supporting lining with perforated acoustic drywall, to improve the absorption of the room. Includes the framework, the perforated board and the joint treatment. Measured per square meter of lining completed.",

    "Formación de cajón o falso pilar de placa de yeso laminado para ocultar instalaciones dentro del trasdosado. Incluye la estructura del cajón, la placa y el tratamiento de juntas. Medido por metro lineal de cajón.":
        "Formation of a boxed section or false pier in drywall to conceal services inside the lining. Includes the framework of the boxed section, the board and the joint treatment. Measured per meter of boxed section.",

    "Suministro y colocación de trasdosado directo de placa de yeso laminado de 12,5 mm adherida al paramento con pasta de agarre, sin estructura metálica. Incluye la comprobación de que el muro no tenga humedad activa, la aplicación de la pasta en pelladas, la presentación de la placa a plomo, el tratamiento de juntas y el remate de encuentros. Medido por metro cuadrado de trasdosado terminado.":
        "Supply and installation of a direct lining of 12.5 mm drywall bonded to the substrate with adhesive compound, without a metal framework. Includes checking that the wall has no active damp, applying the compound in dabs, placing the board plumb, the joint treatment and finishing the junctions. Measured per square meter of lining completed.",

    "Suministro y montaje de forro de placa de yeso laminado de 12,5 mm sobre rastreles fijados al muro, creando una cámara mínima para el paso de instalaciones. Incluye la fijación de los rastreles a plomo con tacos, el paso de las instalaciones por la cámara, el atornillado de la placa y el tratamiento de juntas. Medido por metro cuadrado de forro terminado.":
        "Supply and installation of a lining of 12.5 mm drywall on battens fixed to the wall, creating a minimum cavity for running services. Includes fixing the battens plumb with plugs, running the services through the cavity, screwing the board and the joint treatment. Measured per square meter of lining completed.",

    "Suministro y montaje de placa de yeso laminado de 12,5 mm sobre rastreles para regularizar un muro y ocultar instalaciones vistas sin recurrir a obra húmeda. Incluye el replanteo, la fijación de los rastreles, el paso y protección de las instalaciones, el atornillado de la placa y el tratamiento de juntas. Medido por metro cuadrado de paramento regularizado.":
        "Supply and installation of 12.5 mm drywall on battens to make a wall level and to conceal exposed services without resorting to wet trades. Includes setting out, fixing the battens, running and protecting the services, screwing the board and the joint treatment. Measured per square meter of substrate made level.",

    "Acabado de juntas y remates de un trasdosado de placa de yeso laminado ya montado, como trabajo independiente. Incluye el repaso de las juntas con pasta y cinta, el masillado de cabezas de tornillo, el lijado de las uniones y el remate de encuentros con muros y techo. Medido por metro cuadrado de superficie tratada.":
        "Finishing of the joints and trim of an already installed drywall lining, as a separate item. Includes going over the joints with compound and tape, filling the screw heads, sanding the joints and finishing the junctions with the walls and the ceiling. Measured per square meter of surface treated.",

    "Trasdosado directo de placa de yeso de alta dureza adherida al paramento con pasta de agarre, para zonas de impacto. Incluye la aplicación de la pasta, la presentación de la placa y el tratamiento de juntas. Medido por metro cuadrado de trasdosado terminado.":
        "Direct lining of high hardness drywall bonded to the substrate with adhesive compound, for impact areas. Includes applying the compound, placing the board and the joint treatment. Measured per square meter of lining completed.",

    "Suministro y montaje de forro de placa de cemento reforzada con fibra sobre estructura metálica, para áreas húmedas y locales expuestos a salpicaduras. Incluye la estructura separada del muro, el atornillado de la placa con tornillos apropiados, el tratamiento de juntas con malla y el sellado de encuentros. Medido por metro cuadrado de forro terminado.":
        "Supply and installation of a lining of fiber cement board on a metal framework, for wet areas and premises exposed to splashing. Includes the framework held off the wall, screwing the board with the appropriate screws, the joint treatment with mesh and sealing the junctions. Measured per square meter of lining completed.",

    "Suministro y montaje de forro de placa de cemento reforzada con fibra sobre estructura, como soporte del enchapado en zona de ducha o bañera. Incluye la estructura, el atornillado de la placa, el tratamiento de juntas con malla y el sellado de las uniones previo a la impermeabilización y el enchapado. Medido por metro cuadrado de forro terminado.":
        "Supply and installation of a lining of fiber cement board on a framework, as a substrate for tiling in a shower or bath area. Includes the framework, screwing the board, the joint treatment with mesh and sealing the joints prior to the waterproofing and the tiling. Measured per square meter of lining completed.",

    "Suministro y montaje de forro ignífugo de placa de yeso laminado resistente al fuego de 15 mm, sobre estructura metálica, para protección de instalaciones, conductos o estructura. Incluye la estructura, el atornillado de la placa, el tratamiento de juntas y el sellado de los pasos de instalaciones. Medido por metro cuadrado de forro terminado.":
        "Supply and installation of a fire resistant lining of 15 mm fire rated drywall, on a metal framework, for the protection of services, ducts or structure. Includes the framework, screwing the board, the joint treatment and sealing the service penetrations. Measured per square meter of lining completed.",

    "Reparación puntual de un trasdosado o forro de placa de yeso laminado dañado por golpe o humedad localizada. Incluye el corte del tramo afectado, la sustitución de la placa en la zona, el tratamiento de juntas del parche y el lijado para dejar la superficie lista para pintar. Medido por reparación ejecutada.":
        "Localized repair of a drywall lining or enclosure damaged by a knock or by localized damp. Includes cutting out the affected length, replacing the board in the area, the joint treatment of the patch and sanding to leave the surface ready to paint. Measured per repair carried out.",

    "Forro ignífugo de placa de yeso resistente al fuego para protección de conductos e instalaciones verticales. Incluye la estructura, la placa ignífuga y el sellado de pasos. Medido por metro cuadrado de forro terminado.":
        "Fire resistant lining of fire rated drywall for the protection of ducts and vertical services. Includes the framework, the fire rated board and sealing the penetrations. Measured per square meter of lining completed.",

    "Forro de placa de yeso laminado con registro de acceso practicable, para inspección de instalaciones ocultas. Incluye la estructura, la placa, el registro y el tratamiento de juntas. Medido por metro cuadrado de forro terminado.":
        "Lining of drywall with an access panel for the inspection of concealed services. Includes the framework, the board, the access panel and the joint treatment. Measured per square meter of lining completed.",
}
