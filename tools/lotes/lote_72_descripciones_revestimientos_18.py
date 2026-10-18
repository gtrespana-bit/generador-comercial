# -*- coding: utf-8 -*-
"""Descripciones — Revestimientos y acabados (18 de n): pintura exterior.

Vocabulario aplicado:

· «Paño» es bay, y el repaso se hace «por paños completos», by complete
  bays, para que no se marquen las paradas del rodillo.
· «Recubrimiento elastomérico» es elastomeric coating y su virtud es el
  «puenteo de fisuras», crack bridging, que depende del espesor y del
  «consumo», coverage rate, no del número de manos.
· «Coqueras» del concreto son blowholes y las «eflorescencias» son
  efflorescence; el ataque alcalino produce «saponificación»,
  saponification, y por eso hace falta imprimación resistente a álcalis.
· «Salitre» es saltpetre y su «saneado» es removal.
· «Hidrolavado» es pressure washing y la máquina es pressure washer.
· «Reja» y «verja» son railing y gate, y el fondo que las protege es
  anti-corrosion primer.
· «Friso» en exterior es stucco, como en interior, y «friso decorativo»
  pintado es decorative frieze.
· «Medianera» es party wall y el «muro de cerramiento» es enclosing wall.
"""

LOTE = {
    "Repintado integral de vivienda con protección de muebles y desalojo de espacios, con dos manos. Incluye la protección del mobiliario y la aplicación. Medido por metro cuadrado repintado.":
        "Full repainting of a dwelling with protection of furniture and clearing of spaces, with two coats. Includes protecting the furniture and the application. Measured per square meter repainted.",

    "Aplicación de guarda o friso decorativo interior pintado, con una o dos manos. Incluye el enmascarado de la línea y la aplicación. Medido por metro lineal pintado.":
        "Application of a painted decorative border or frieze internally, with one or two coats. Includes masking the line and the application. Measured per meter painted.",

    "Aplicación de dos manos de pintura de caucho para exteriores sobre fachada preparada, con brocha en encuentros y rodillo en paños. Incluye el trabajo desde andamio, la protección de carpinterías y del entorno a pie de fachada, el recorte de perímetros y molduras, la aplicación de las manos respetando el tiempo de secado y evitando pintar bajo sol directo intenso o con amenaza de lluvia, que arruina el acabado, y el repaso final por paños completos para que no se marquen las paradas. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Application of two coats of exterior latex paint on a prepared facade, with a brush at junctions and a roller on the bays. Includes working from scaffolding, protecting the joinery and the surroundings at the foot of the facade, cutting in the perimeters and moldings, applying the coats respecting the drying time and avoiding painting under intense direct sun or with a threat of rain, which ruins the finish, and the final going over by complete bays so that the stops do not show. Measured by the area actually completed, deducting openings larger than 1 m².",

    "Aplicación de recubrimiento elastomérico impermeabilizante en fachada, en dos o tres manos hasta alcanzar el espesor de película que garantiza el puenteo de fisuras. A diferencia de una pintura convencional, su valor está en el espesor: aplicada en capa fina para ahorrar material pierde la elasticidad que justifica su precio y deja de puentear las fisuras. Incluye la preparación del soporte, el tratamiento previo de fisuras mayores con banda, la aplicación de las manos cruzadas respetando el consumo indicado por el fabricante y la verificación del espesor. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Application of an elastomeric waterproofing coating on a facade, in two or three coats until the film thickness that guarantees the bridging of cracks is reached. Unlike a conventional paint, its value lies in the thickness: applied thin to save material it loses the elasticity that justifies its price and stops bridging the cracks. Includes preparing the substrate, the prior treatment of larger cracks with tape, the application of the crossed coats respecting the coverage rate indicated by the manufacturer and the verification of the thickness. Measured by the area actually completed, deducting openings larger than 1 m².",

    "Aplicación de pintura sobre concreto visto, bloque o superficie mineral porosa, con imprimación selladora previa. El concreto joven es fuertemente alcalino y ataca las pinturas convencionales produciendo saponificación y desprendimiento, por lo que hay que respetar el tiempo de curado o emplear imprimación resistente a álcalis. Incluye la limpieza y eliminación de eflorescencias, la imprimación selladora, el resane de coqueras y las manos de acabado. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Application of paint on exposed concrete, block or porous mineral surface, with a previous sealing primer. Young concrete is strongly alkaline and attacks conventional paints, causing saponification and flaking, so the curing time has to be respected or an alkali resistant primer used. Includes the cleaning and removal of efflorescence, the sealing primer, the patching of blowholes and the finish coats. Measured by the area actually completed, deducting openings larger than 1 m².",

    "Aplicación de pintura de caucho exterior sobre friso nuevo, con fondo sellador y tres manos. Incluye la aplicación del fondo, las tres manos de pintura y la protección de ventanas y pisos. Medido por metro cuadrado pintado.":
        "Application of exterior latex paint on new stucco, with a sealing primer and three coats. Includes applying the primer, the three coats of paint and protecting windows and floors. Measured per square meter painted.",

    "Repintado de fachada sobre pintura existente en buen estado, con limpieza y dos manos de pintura de caucho exterior. Incluye la limpieza de la superficie, el repaso de fisuras y las dos manos de acabado. Medido por metro cuadrado repintado.":
        "Repainting of a facade over existing paint in good condition, with cleaning and two coats of exterior latex paint. Includes the cleaning of the surface, the treatment of the cracks and the two finish coats. Measured per square meter repainted.",

    "Aplicación de pintura de caucho exterior con acabado satinado sobre fachada, con dos manos. Incluye la preparación del soporte y las dos manos de acabado satinado. Medido por metro cuadrado pintado.":
        "Application of exterior latex paint with a satin finish on a facade, with two coats. Includes preparing the substrate and the two satin finish coats. Measured per square meter painted.",

    "Aplicación de pintura exterior con acabado texturado o gota sobre fachada, con dos manos. Incluye la preparación del soporte y la aplicación del revestimiento texturado. Medido por metro cuadrado pintado.":
        "Application of exterior paint with a textured or stippled finish on a facade, with two coats. Includes preparing the substrate and applying the textured coating. Measured per square meter painted.",

    "Aplicación de pintura exterior en muro de cerramiento o medianera, con dos manos. Incluye la limpieza de la superficie y las dos manos de pintura de caucho exterior. Medido por metro cuadrado pintado.":
        "Application of exterior paint on an enclosing wall or party wall, with two coats. Includes the cleaning of the surface and the two coats of exterior latex paint. Measured per square meter painted.",

    "Aplicación de pintura exterior en cornisas, aleros y remates de fachada, con dos manos. Incluye la protección de los elementos adyacentes y las dos manos de pintura. Medido por metro cuadrado pintado.":
        "Application of exterior paint on cornices, eaves and facade trim, with two coats. Includes protecting the adjacent elements and the two coats of paint. Measured per square meter painted.",

    "Aplicación de esmalte sobre reja, verja o elemento metálico exterior, con fondo anticorrosivo y dos manos. Incluye la limpieza, el fondo anticorrosivo y las dos manos de esmalte. Medido por metro cuadrado pintado.":
        "Application of enamel paint on an exterior railing, gate or metal element, with an anti-corrosion primer and two coats. Includes the cleaning, the anti-corrosion primer and the two coats of enamel paint. Measured per square meter painted.",

    "Aplicación de puente de adherencia y dos manos de pintura exterior en fachada con soporte irregular. Incluye el puente, las dos manos y la protección del entorno. Medido por metro cuadrado pintado.":
        "Application of a bonding coat and two coats of exterior paint on a facade with an uneven substrate. Includes the bonding coat, the two coats and protecting the surroundings. Measured per square meter painted.",

    "Tratamiento de salitre en muro exterior seguido de dos manos de pintura. Incluye el saneado del salitre, el tratamiento y las dos manos. Medido por metro cuadrado tratado y pintado.":
        "Treatment of saltpetre on an external wall followed by two coats of paint. Includes the removal of the saltpetre, the treatment and the two coats. Measured per square meter treated and painted.",

    "Aplicación de pintura exterior a dos colores en fachada, con enmascarado de la línea de separación. Incluye la aplicación de ambos colores y el remate limpio. Medido por metro cuadrado pintado.":
        "Application of exterior paint in two colors on a facade, with masking of the division line. Includes the application of both colors and the clean finish. Measured per square meter painted.",

    "Hidrolavado previo y dos manos de pintura exterior en fachada. Incluye la limpieza con hidrolavadora, la preparación y las dos manos. Medido por metro cuadrado pintado.":
        "Previous pressure washing and two coats of exterior paint on a facade. Includes the cleaning with a pressure washer, the preparation and the two coats. Measured per square meter painted.",

    "Aplicación de protector anti-graffiti sobre fachada pintada, que facilita la limpieza de pintadas. Incluye la limpieza previa y la aplicación del protector. Medido por metro cuadrado tratado.":
        "Application of an anti-graffiti protector on a painted facade, which makes the cleaning of graffiti easier. Includes the previous cleaning and the application of the protector. Measured per square meter treated.",

    "Aplicación de pintura exterior sobre fachada de bloque de concreto, con fondo y dos manos. Incluye el sellado del bloque, el fondo y las dos manos. Medido por metro cuadrado pintado.":
        "Application of exterior paint on a concrete block facade, with a primer and two coats. Includes the sealing of the block, the primer and the two coats. Measured per square meter painted.",
}
