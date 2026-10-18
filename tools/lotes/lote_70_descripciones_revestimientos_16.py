# -*- coding: utf-8 -*-
"""Descripciones — Revestimientos y acabados (16 de n): remates de cielo y
pintura interior.

Vocabulario aplicado:

· «Comején» es termite y la «pudrición» es rot: en clima tropical, el
  preservante hay que darlo también en las «testas», end grain, que es
  por donde entra el agua.
· «Borde de sombra» es shadow gap, el encuentro que se deja abierto para
  que la luz salga sin ver la fuente.
· «Cortinero empotrado» es recessed curtain track y su «riel» es rail;
  hay que reforzar la estructura a su altura porque la cortina pesa.
· «Recorte de cantos» es cutting in, y las «manos cruzadas» son crossed
  coats, las que dejan el espesor parejo.
· «Borde húmedo» es wet edge: si se pierde, el solape se marca.
· «Pintura de caucho» es latex paint, y el «fondo sellador» sobre friso
  nuevo es sealing primer.
· «Satinado» es satin y «mate» es matte, y la diferencia entre ambos es
  la que decide el sitio: el satinado aguanta la limpieza, el mate
  disimula el soporte.
· «Fuente» de la cinta LED es driver, y conviene dejarla registrable.
"""

LOTE = {
    "Cielo raso con machihembrado de madera sobre rastrelado suspendido de la losa, con cámara ventilada y tratamiento preservante. En clima tropical la ventilación de la cámara y el preservante en todas las caras, incluidas las testas, son lo que evita el ataque de comején y la pudrición. Incluye replanteo y nivelación del rastrelado, aplicación del preservante, montaje del machihembrado con clavado oculto, remate perimetral con moldura y lijado final. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Ceiling of interlocking wood boards on battens suspended from the slab, with a ventilated cavity and a preservative treatment. In a tropical climate the ventilation of the cavity and the preservative on every face, including the end grain, are what prevent termite attack and rot. Includes field layout and leveling the battens, applying the preservative, installing the interlocking boards with secret nailing, the perimeter trim with molding and the final sanding. Measured by the area actually completed, deducting openings larger than 1 m².",

    "Cielo raso de listones de madera sobre rastreles, con junta abierta o cerrada. Incluye la estructura de fijación, la colocación de los listones y el acabado. Medido por metro cuadrado ejecutado.":
        "Ceiling of wood strips on battens, with an open or closed joint. Includes the fastening framework, laying the strips and the finish. Measured per square meter completed.",

    "Cielo raso de listones de madera con junta abierta, sobre rastreles. Incluye la estructura, la colocación de los listones y el acabado. Medido por metro cuadrado ejecutado.":
        "Ceiling of wood strips with an open joint, on battens. Includes the framework, laying the strips and the finish. Measured per square meter completed.",

    "Suministro y colocación de moldura perimetral de remate en el encuentro del cielo raso con las paredes, de yeso, poliuretano o madera según el acabado. Resuelve la junta entre dos elementos que se mueven de forma independiente, que sin moldura acaba fisurando. Incluye replanteo de la línea con nivel, corte a inglete de esquinas, colocación con pasta o adhesivo, relleno de juntas entre piezas y repaso dejando lista para pintar. Medido en longitud realmente colocada.":
        "Supply and installation of a perimeter molding at the junction of the ceiling with the walls, in gypsum, polyurethane or wood depending on the finish. It resolves the joint between two elements that move independently, which without a molding ends up cracking. Includes field layout of the line with a level, mitring the corners, fastening with compound or adhesive, filling the joints between pieces and going over it to leave it ready to paint. Measured by the length actually installed.",

    "Formación de cornisa perimetral con perfil específico para alojar cinta LED de iluminación indirecta, montada sobre el cielo raso. Incluye el replanteo de la altura y de la separación al techo, que determina la apertura del haz y por tanto el efecto de luz conseguido, el montaje del perfil, el remate de juntas, la previsión del paso del cableado y de la posición de la fuente en un punto registrable, y el acabado listo para pintar. No incluye la cinta LED. Medido en longitud realmente ejecutada.":
        "Formation of a perimeter cornice with a specific profile to house an LED strip for indirect lighting, mounted on the ceiling. Includes field layout of the height and the gap to the soffit, which determines the spread of the beam and therefore the lighting effect achieved, installing the profile, finishing the joints, providing for the cable run and for the position of the driver at an accessible point, and leaving the finish ready to paint. Does not include the LED strip. Measured by the length actually completed.",

    "Formación de cortinero empotrado en el cielo raso, con su nicho, refuerzo estructural y riel. Es un detalle que se decide antes de cerrar el cielo raso y que no admite improvisación posterior: resolverlo después obliga a abrir el cielo terminado. Incluye la coordinación previa del ancho del nicho con el sistema de cortina, el refuerzo de la estructura en la línea del riel para soportar el peso de la cortina, el forrado del nicho, el remate de aristas, el montaje del riel y el repaso listo para pintar. Medido en longitud realmente ejecutada.":
        "Formation of a recessed curtain track in the ceiling, with its recess, structural reinforcement and rail. It is a detail that has to be decided before the ceiling is closed and that does not admit later improvisation: resolving it afterwards means opening the finished ceiling. Includes the prior coordination of the width of the recess with the curtain system, the reinforcement of the framework along the line of the rail to carry the weight of the curtain, lining the recess, finishing the arrises, installing the rail and going over it to leave it ready to paint. Measured by the length actually completed.",

    "Ejecución de borde perimetral de sombra en cielo raso, para alojar iluminación indirecta. Incluye la estructura del borde, el remate y el acabado. Medido por metro lineal de borde.":
        "Formation of a perimeter shadow gap in a ceiling, to house indirect lighting. Includes the framework of the edge, the trim and the finish. Measured per meter of edge.",

    "Colocación de perfil de remate perimetral entre cielo raso y muro, como terminación. Incluye la fijación del perfil y el remate de las uniones. Medido por metro lineal de remate.":
        "Installation of a perimeter trim profile between the ceiling and the wall, as a finish. Includes fastening the profile and finishing the joints. Measured per meter of trim.",

    "Ejecución de borde de sombra perimetral en cielo raso desmontable, para alojar iluminación indirecta. Incluye la estructura del borde y el remate. Medido por metro lineal de borde.":
        "Formation of a perimeter shadow gap in a demountable ceiling, to house indirect lighting. Includes the framework of the edge and the trim. Measured per meter of edge.",

    "Colocación de registro de acceso practicable en cielo raso desmontable, para inspección de instalaciones. Incluye la fijación del registro y el remate. Medido por unidad de registro.":
        "Installation of an access panel in a demountable ceiling, for the inspection of services. Includes fastening the panel and the trim. Measured per unit of access panel.",

    "Cielo raso desmontable con foseado perimetral para ocultar instalaciones y alojar cortinas. Incluye la estructura, los paneles y el foseado perimetral. Medido por metro cuadrado ejecutado.":
        "Demountable ceiling with a perimeter recessed section to conceal services and to house curtains. Includes the framework, the panels and the perimeter recessed section. Measured per square meter completed.",

    "Aplicación de dos manos de pintura de caucho acrílico mate lavable sobre paramento interior previamente preparado e imprimado, aplicada con rodillo y brocha en encuentros y remates, con el lijado intermedio necesario entre manos y respetando los tiempos de secado del fabricante. Incluye protección del entorno, recorte de cantos y esquinas, repasos finales y limpieza del área de trabajo. El color lo elige el cliente. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Application of two coats of washable matte acrylic latex paint on an internal substrate previously prepared and primed, applied with roller and brush at junctions and trim, with the intermediate sanding needed between coats and respecting the manufacturer's drying times. Includes protecting the surroundings, cutting in at edges and corners, final touch-ups and cleaning the work area. The color is selected by the client. Measured by the area actually completed, deducting openings larger than 1 m².",

    "Aplicación de dos manos de pintura de caucho satinada lavable sobre paramento interior preparado. El acabado satinado resiste la limpieza mucho mejor que el mate, lo que lo hace preferible en cocinas, baños, pasillos y áreas infantiles, aunque marca más las irregularidades del soporte, por lo que exige una preparación más cuidada. Incluye la protección del entorno, el recorte de cantos y encuentros a brocha, la aplicación con rodillo en manos cruzadas, el lijado suave intermedio y los repasos finales. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Application of two coats of washable satin latex paint on a prepared internal substrate. The satin finish stands up to cleaning far better than matte, which makes it preferable in kitchens, bathrooms, hallways and children's areas, although it shows the irregularities of the substrate more, so it needs more careful preparation. Includes protecting the surroundings, cutting in at edges and junctions with a brush, applying with a roller in crossed coats, a light intermediate sanding and the final touch-ups. Measured by the area actually completed, deducting openings larger than 1 m².",

    "Aplicación de dos manos de pintura sobre cielo raso previamente preparado, con rodillo de mango extensible y brocha en encuentros. Pintar por encima de la cabeza rinde bastante menos que en pared, obliga a proteger todo el piso y el mobiliario por el goteo y penaliza el acabado si no se mantiene el borde húmedo, ya que los solapes se marcan mucho más con la luz rasante que llega desde las ventanas. Incluye la protección integral del ambiente, el recorte de perímetros, la aplicación en manos cruzadas y los repasos finales. Medido en superficie realmente ejecutada.":
        "Application of two coats of paint on a previously prepared ceiling, with an extension pole roller and a brush at junctions. Painting overhead has a considerably lower output than on a wall, means protecting the whole floor and the furniture against drips and penalizes the finish if a wet edge is not maintained, since the laps show up much more under the raking light that comes in from the windows. Includes the full protection of the room, cutting in the perimeters, applying in crossed coats and the final touch-ups. Measured by the area actually completed.",

    "Aplicación de pintura de caucho sobre friso nuevo interior, con fondo sellador y tres manos de acabado. Incluye la aplicación del fondo, las tres manos de pintura y la protección de pisos y carpintería. Medido por metro cuadrado pintado.":
        "Application of latex paint on a new internal stucco, with a sealing primer and three finish coats. Includes applying the primer, the three coats of paint and protecting floors and carpentry. Measured per square meter painted.",

    "Repintado de paramento interior sobre pintura existente en buen estado, con dos manos de pintura de caucho. Incluye la limpieza superficial, el repaso de pequeños desperfectos y las dos manos de acabado. Medido por metro cuadrado repintado.":
        "Repainting of an internal substrate over existing paint in good condition, with two coats of latex paint. Includes the surface cleaning, the touching up of small defects and the two finish coats. Measured per square meter repainted.",
}
