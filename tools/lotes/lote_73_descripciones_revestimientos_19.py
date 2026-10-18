# -*- coding: utf-8 -*-
"""Descripciones — Revestimientos y acabados (19 de n): esmaltes, barnices
y recubrimientos.

Vocabulario aplicado:

· «Herrajes» es hardware, y «hoja» de puerta es door leaf.
· «Esmalte sintético brillante» es gloss synthetic enamel, y el
  «desengrasado» es degreasing.
· Sobre galvanizado hace falta «anclaje mecánico», mechanical key, y
  «imprimación de adherencia», adhesion primer, o un «tratamiento de
  conversión», conversion treatment. Sin ello el acabado se desprende
  «en láminas», in sheets.
· «Sellador de poro» es pore filler y la «veta» es grain: se lija en el
  sentido de la veta, in the direction of the grain.
· «Lasur» es woodstain, y deja ver la veta, let the grain show through.
· «Barniz marino» es marine varnish, el que aguanta la intemperie.
· «Pintura intumescente» es intumescent fire retardant paint.
· El epoxi tiene «tiempo de vida útil de la mezcla», pot life, que es
  corto, y «tiempos de repintado», recoating times, del fabricante.
· «Abrir el poro» es open the pores, y «medir la humedad» medir el
  moisture content del soporte antes deEncerrar el agua debajo.
· En el acabado texturado, la «misma mano» es the same hand: el mismo
  aplicador, la misma herramienta y la misma dosificación.
"""

LOTE = {
    "Repintado de mantenimiento de fachada, con limpieza, repaso de fisuras y dos manos. Incluye la limpieza, el resane y las dos manos. Medido por metro cuadrado repintado.":
        "Maintenance repainting of a facade, with cleaning, treatment of cracks and two coats. Includes the cleaning, the patching and the two coats. Measured per square meter repainted.",

    "Aplicación de dos manos de esmalte sintético brillante sobre carpintería metálica o de madera, previa preparación del soporte mediante lijado, desengrasado y eliminación de óxido o restos de acabados anteriores. Incluye enmascarado de vidrios, herrajes y paramentos contiguos, aplicación a brocha en perfiles y molduras, lijado suave entre manos y retirada de protecciones. Medido en superficie realmente tratada, midiendo ambas caras por separado.":
        "Application of two coats of gloss synthetic enamel paint on metal or wood joinery, after preparing the substrate by sanding, degreasing and removing rust or remains of previous finishes. Includes masking glass, hardware and adjoining substrates, applying with a brush on profiles and moldings, light sanding between coats and removing the protection. Measured by the surface actually treated, measuring both faces separately.",

    "Aplicación de acabado sobre superficie galvanizada o de aluminio, con imprimación específica de adherencia. Estos soportes son la trampa clásica del pintor: una imprimación anticorrosiva convencional no agarra sobre el galvanizado y el acabado se desprende en láminas al cabo de unos meses, de modo que hace falta desengrasado a fondo e imprimación de adherencia específica o tratamiento de conversión. Incluye el desengrasado, el lijado suave de la superficie para crear anclaje mecánico, la imprimación de adherencia y las dos manos de acabado. Medido en superficie realmente ejecutada.":
        "Application of a finish on a galvanized or aluminum surface, with a specific adhesion primer. These substrates are the painter's classic trap: a conventional anti-corrosion primer will not grip on galvanizing and the finish peels off in sheets after a few months, so thorough degreasing and a specific adhesion primer or a conversion treatment are needed. Includes the degreasing, the light sanding of the surface to create a mechanical key, the adhesion primer and the two finish coats. Measured by the area actually completed.",

    "Aplicación de pintura anticorrosiva sobre estructura metálica, con dos manos de fondo. Incluye la limpieza de la superficie, la preparación anticorrosiva y las dos manos. Medido por metro cuadrado pintado.":
        "Application of anti-corrosion paint on a metal structure, with two primer coats. Includes the cleaning of the surface, the anti-corrosion preparation and the two coats. Measured per square meter painted.",

    "Aplicación de esmalte o pintura anticorrosiva sobre tuberías y conducciones metálicas vistas, con dos manos. Incluye la limpieza y las dos manos de pintura de protección. Medido por metro lineal de tubería pintada.":
        "Application of enamel paint or anti-corrosion paint on exposed metal pipes and conduits, with two coats. Includes the cleaning and the two coats of protective paint. Measured per meter of pipe painted.",

    "Pintura de una puerta de madera con desmontaje y remontaje de herrajes, con fondo y dos manos de esmalte. Incluye la retirada de herrajes, la preparación, la pintura por ambas caras y el remontaje. Medido por hoja de puerta pintada.":
        "Painting of a wood door with removal and refitting of the hardware, with a primer and two coats of enamel paint. Includes the removal of the hardware, the preparation, the painting of both faces and the refitting. Measured per door leaf painted.",

    "Aplicación de barniz de poliuretano o laca sobre carpintería y elementos de madera interiores, en tres manos con lijado intermedio. Incluye el lijado inicial en el sentido de la veta, el desempolvado, la aplicación del sellador de poro, el lijado suave entre manos que es lo que produce el tacto liso del acabado final, y las manos de barniz respetando los tiempos de secado. Medido en superficie realmente tratada, desarrollando todas las caras.":
        "Application of polyurethane varnish or lacquer on internal joinery and wood elements, in three coats with intermediate sanding. Includes the initial sanding in the direction of the grain, dusting off, applying the pore filler, the light sanding between coats which is what produces the smooth feel of the final finish, and the coats of varnish respecting the drying times. Measured by the surface actually treated, taking every face.",

    "Aplicación de barniz marino sobre carpintería de madera exterior, con dos manos. Incluye la preparación de la madera y las dos manos de barniz de alta resistencia a la intemperie. Medido por metro cuadrado barnizado.":
        "Application of marine varnish on external wood joinery, with two coats. Includes preparing the wood and the two coats of varnish of high resistance to weathering. Measured per square meter varnished.",

    "Aplicación de preservante fungicida e insecticida sobre madera estructural o de obra, con una o dos manos. Incluye la preparación de la madera y la aplicación del preservante. Medido por metro cuadrado tratado.":
        "Application of a fungicidal and insecticidal preservative on structural or building lumber, with one or two coats. Includes preparing the wood and applying the preservative. Measured per square meter treated.",

    "Aplicación de lasur decorativo sobre madera exterior, con dos manos que dejan ver la veta. Incluye la preparación de la madera y las dos manos de lasur. Medido por metro cuadrado tratado.":
        "Application of a decorative woodstain on external wood, with two coats that let the grain show through. Includes preparing the wood and the two coats of woodstain. Measured per square meter treated.",

    "Aplicación de tinte o colorante para madera interior, con una o dos manos. Incluye la preparación de la madera y la aplicación del tinte. Medido por metro cuadrado teñido.":
        "Application of stain or wood dye for internal wood, with one or two coats. Includes preparing the wood and applying the stain. Measured per square meter stained.",

    "Aplicación de lasur protector sobre pérgola o madera exterior, con dos manos. Incluye la preparación de la madera y las dos manos de lasur. Medido por metro cuadrado tratado.":
        "Application of a protective woodstain on a pergola or external wood, with two coats. Includes preparing the wood and the two coats of woodstain. Measured per square meter treated.",

    "Aplicación de pintura intumescente ignífuga sobre madera estructural o de acabado. Incluye la preparación y la aplicación de las capas necesarias. Medido por metro cuadrado pintado.":
        "Application of intumescent fire retardant paint on structural or finishing wood. Includes the preparation and the application of the necessary coats. Measured per square meter painted.",

    "Aplicación de pintura epóxica bicomponente sobre piso o paramento, con imprimación y dos manos de acabado, para áreas de tránsito intenso, cocinas industriales y talleres. Exige mezclar los dos componentes en la proporción exacta y aplicar dentro del tiempo de vida útil de la mezcla, que es corto: pasado ese tiempo el producto sigue pareciendo utilizable pero ya no cura correctamente. Incluye la preparación mecánica del soporte para abrir el poro, la medición de humedad, la imprimación, la mezcla controlada y la aplicación de las manos con los tiempos de repintado del fabricante. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Application of a two-component epoxy coating on a floor or substrate, with a primer and two finish coats, for heavy traffic areas, commercial kitchens and workshops. It requires mixing the two components in the exact proportion and applying within the pot life of the mix, which is short: after that time the product still looks usable but no longer cures properly. Includes the mechanical preparation of the substrate to open the pores, the measurement of moisture, the primer, the controlled mixing and the application of the coats with the manufacturer's recoating times. Measured by the area actually completed, deducting openings larger than 1 m².",

    "Aplicación de acabado decorativo texturado sobre paramento interior o exterior, con la técnica y el grano acordados con el cliente. El resultado depende de mantener la misma mano, la misma herramienta y la misma dosificación en todo el paño, por lo que conviene ejecutar una muestra aprobada previamente y no interrumpir el trabajo dentro de un mismo paño. Incluye la preparación y sellado del soporte, la aplicación de la capa base, la ejecución de la textura de forma continua y la protección final cuando el sistema la requiera. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Application of a textured decorative finish on an internal or external substrate, with the technique and the grain agreed with the client. The result depends on keeping the same hand, the same tool and the same dosage throughout the bay, so it is advisable to carry out an approved sample first and not to interrupt the work within the same bay. Includes the preparation and sealing of the substrate, the application of the base coat, the execution of the texture in a continuous operation and the final protection when the system requires it. Measured by the area actually completed, deducting openings larger than 1 m².",

    "Aplicación de recubrimiento de poliuretano bicomponente sobre piso interior, con imprimación y dos capas. Incluye la preparación del soporte, la imprimación y las dos capas de poliuretano. Medido por metro cuadrado recubierto.":
        "Application of a two-component polyurethane coating on an internal floor, with a primer and two coats. Includes preparing the substrate, the primer and the two coats of polyurethane. Measured per square meter coated.",

    "Aplicación de recubrimiento epóxico antideslizante sobre piso interior o exterior, con capa de imprimación y acabado con árido. Incluye la preparación, la imprimación y el acabado antideslizante. Medido por metro cuadrado recubierto.":
        "Application of an anti-slip epoxy coating on an internal or external floor, with a primer coat and a finish with aggregate. Includes the preparation, the primer and the anti-slip finish. Measured per square meter coated.",

    "Aplicación de pintura epóxica sobre paramento vertical, con imprimación y dos manos. Incluye la preparación del soporte, la imprimación y las dos manos de pintura epóxica. Medido por metro cuadrado pintado.":
        "Application of epoxy paint on a vertical substrate, with a primer and two coats. Includes preparing the substrate, the primer and the two coats of epoxy paint. Measured per square meter painted.",
}
