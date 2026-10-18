# -*- coding: utf-8 -*-
"""Descripciones — Revestimientos y acabados (17 de n): pintura, acabados
especiales.

Vocabulario aplicado:

· «Pintura de pizarra» es chalkboard paint y la magnética es magnetic
  paint; el «curado» antes de usarla es curing.
· «Semibrillo» es semi-gloss, el intermedio entre satin y gloss, y es el
  que se pide en zonas de alto tránsito.
· «Mocheta» es reveal: la cara interior del vano, y su «arista» es arris.
· «Guarda» es border y la línea que separa dos colores es division line,
  que se hace enmascarando, masking.
· «Concreto visto» es exposed concrete, y en techo se dice soffit.
· «Depósito» es storage room y «despensa» es pantry, dos palabras que el
  traductor automático suele confundir con almacén.
· «Plantilla» para pintar es stencil, no template: la template es la de
  la media caña.
· «Perlado» es pearlescent y «metalizado» es metallic.
· «Antihongos» y «antimoho» es anti-mold, y «esmalte» es enamel paint.
"""

LOTE = {
    "Aplicación de pintura acrílica antihongos en paramentos de cocina, baño o local con condensación, con dos manos. Incluye la limpieza de la superficie, el tratamiento previo de las zonas afectadas y las dos manos de pintura antimoho. Medido por metro cuadrado pintado.":
        "Application of anti-mold acrylic paint on substrates in kitchens, bathrooms or premises subject to condensation, with two coats. Includes the cleaning of the surface, the prior treatment of the affected areas and the two coats of anti-mold paint. Measured per square meter painted.",

    "Aplicación de pintura de caucho semibrillo lavable en paramentos de alto tránsito, pasillos y áreas de servicio, con dos manos. Incluye la preparación del soporte y las dos manos de acabado semibrillo. Medido por metro cuadrado pintado.":
        "Application of washable semi-gloss latex paint on substrates in high traffic areas, hallways and service areas, with two coats. Includes preparing the substrate and the two semi-gloss finish coats. Measured per square meter painted.",

    "Aplicación de pintura de pizarra efecto tiza en paramento interior, con dos manos sobre fondo preparado. Incluye el fondo sellador, las dos manos de pintura de pizarra y el curado previo a su uso. Medido por metro cuadrado pintado.":
        "Application of chalkboard paint on an internal substrate, with two coats over a prepared base. Includes the sealing primer, the two coats of chalkboard paint and the curing before use. Measured per square meter painted.",

    "Aplicación de pintura magnética como base de pared, previa a la pintura de acabado, con dos manos. Incluye la preparación del soporte y las dos manos de pintura magnética. Medido por metro cuadrado pintado.":
        "Application of magnetic paint as a base coat on a wall, prior to the finish paint, with two coats. Includes preparing the substrate and the two coats of magnetic paint. Measured per square meter painted.",

    "Aplicación de pintura de caucho sobre cielo raso de concreto visto, con fondo sellador y dos manos. Incluye la limpieza, el fondo y las dos manos de acabado, con protección de muros y pisos. Medido por metro cuadrado pintado.":
        "Application of latex paint on an exposed concrete soffit, with a sealing primer and two coats. Includes the cleaning, the primer and the two finish coats, with protection of walls and floors. Measured per square meter painted.",

    "Aplicación de pintura de caucho a dos colores en un mismo paramento, con guarda o línea de separación recta. Incluye la aplicación de ambos colores con enmascarado de la línea y el remate limpio de la unión. Medido por metro cuadrado pintado.":
        "Application of latex paint in two colors on the same substrate, with a border or a straight division line. Includes the application of both colors with masking of the line and the clean finish of the joint. Measured per square meter painted.",

    "Pintura de mocheta, arista y remate interior de vanos de puertas y ventanas, con dos manos de esmalte o caucho. Incluye la protección de las superficies adyacentes y las dos manos de acabado. Medido por metro lineal de mocheta pintada.":
        "Painting of the reveal, arris and internal trim of door and window openings, with two coats of enamel paint or latex paint. Includes protecting the adjacent surfaces and the two finish coats. Measured per meter of reveal painted.",

    "Pintura de franja inferior o rodapié pintado sobre paramento interior, con dos manos de pintura lavable. Incluye el enmascarado de la línea superior y las dos manos de acabado. Medido por metro lineal de franja pintada.":
        "Painting of a lower band or painted baseboard on an internal substrate, with two coats of washable paint. Includes masking the top line and the two finish coats. Measured per meter of band painted.",

    "Aplicación de pintura mineral a base de cal en paramentos interiores de sótanos, depósitos y espacios ventilados, con dos manos. Incluye la preparación del soporte y las dos manos de pintura a la cal. Medido por metro cuadrado pintado.":
        "Application of lime based mineral paint on internal substrates in basements, storage rooms and ventilated spaces, with two coats. Includes preparing the substrate and the two coats of lime paint. Measured per square meter painted.",

    "Aplicación de pintura de caucho en techos o paramentos altos que requieren andamio, con dos manos. Incluye el montaje del andamio, la aplicación de la pintura y la protección del área de trabajo. Medido por metro cuadrado pintado.":
        "Application of latex paint on ceilings or high substrates that require scaffolding, with two coats. Includes erecting the scaffolding, applying the paint and protecting the work area. Measured per square meter painted.",

    "Retoque y repaso puntual de pintura interior en zonas dañadas o desgastadas, con una mano de acabado. Incluye la limpieza de la zona, el resane de pequeños desperfectos y la mano de retoque. Medido por metro cuadrado retocado.":
        "Touching up and localized repair of internal paint in damaged or worn areas, with one finish coat. Includes cleaning the area, the patching of small defects and the touch-up coat. Measured per square meter touched up.",

    "Sellado antihumedad de paramento interior seguido de dos manos de pintura de caucho. Incluye la aplicación del sellador en las zonas con humedad, las dos manos de pintura y la protección del área. Medido por metro cuadrado tratado y pintado.":
        "Damp sealing of an internal substrate followed by two coats of latex paint. Includes applying the sealer in the areas affected by damp, the two coats of paint and protecting the area. Measured per square meter treated and painted.",

    "Aplicación de esmalte lavable en paramentos de cocina, despensa o área de servicio, con dos manos. Incluye la preparación del soporte y las dos manos de esmalte lavable resistente a la limpieza frecuente. Medido por metro cuadrado pintado.":
        "Application of washable enamel paint on substrates in kitchens, pantries or service areas, with two coats. Includes preparing the substrate and the two coats of washable enamel paint resistant to frequent cleaning. Measured per square meter painted.",

    "Aplicación de pintura de señalización de seguridad interior, con franjas y marcas según normativa. Incluye el replanteo de las marcas y la aplicación. Medido por metro cuadrado pintado.":
        "Application of internal safety marking paint, with stripes and markings to the applicable standard. Includes setting out the markings and the application. Measured per square meter painted.",

    "Aplicación de pintura decorativa con plantilla sobre paramento interior, con una o varias manos. Incluye el replanteo del diseño y la aplicación con plantilla. Medido por metro cuadrado pintado.":
        "Application of decorative paint with a stencil on an internal substrate, with one or more coats. Includes setting out the design and applying with a stencil. Measured per square meter painted.",

    "Aplicación de pintura decorativa con acabado perlado o metalizado sobre paramento interior. Incluye la preparación del soporte y la aplicación del acabado. Medido por metro cuadrado pintado.":
        "Application of decorative paint with a pearlescent or metallic finish on an internal substrate. Includes preparing the substrate and applying the finish. Measured per square meter painted.",
}
