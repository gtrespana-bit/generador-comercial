# -*- coding: utf-8 -*-
"""Descripciones — Revestimientos y acabados (15 de n): cielos registrables.

Vocabulario aplicado:

· «Cielo raso registrable» y «desmontable» es suspended ceiling o
  demountable ceiling: el que se levanta pieza a pieza.
· «Perfilería vista en T» es exposed T bar y la «retícula» que forman es
  the grid, colgada del forjado con hangers.
· El «plenum» se dice igual en inglés y es la razón de ser del sistema:
  todo lo que pasa por encima queda registrable.
· «Bandeja perforada con velo» es perforated tray with an acoustic
  fleece: perforada sola no absorbe, hace falta el velo.
· «Encaje a presión» de las láminas de PVC es pushing them together, la
  junta machihembrada que se cierra a mano.
· «Alero» es soffit o overhang, y ahí ni la placa antihumedad aguanta:
  se «descuelga», it sags.
· «Lucernario» y «claraboya» son rooflight y skylight.
"""

LOTE = {
    "Colocación de remate decorativo perimetral de cielo raso, con perfil o moldura. Incluye la fijación del remate y el acabado. Medido por metro lineal de remate.":
        "Installation of a decorative perimeter trim to a ceiling, with a profile or molding. Includes fixing the trim and the finish. Measured per meter of trim.",

    "Cielo raso continuo de placa de yeso con junta de dilatación perimetral o intermedia. Incluye la estructura, la placa, la junta y el tratamiento de juntas. Medido por metro cuadrado ejecutado.":
        "Continuous gypsum board ceiling with a perimeter or intermediate movement joint. Includes the framework, the board, the joint and the joint treatment. Measured per square meter completed.",

    "Cielo raso continuo de placa de yeso resistente a la humedad en baño, con estructura y placa. Incluye la estructura, la placa antihumedad y el tratamiento de juntas. Medido por metro cuadrado ejecutado.":
        "Continuous ceiling of moisture resistant gypsum board in a bathroom, with framework and board. Includes the framework, the moisture resistant board and the joint treatment. Measured per square meter completed.",

    "Cielo raso continuo de placa de yeso con marco y remate para lucernario o claraboya. Incluye la estructura, la placa, el marco del lucernario y el tratamiento de juntas. Medido por metro cuadrado ejecutado.":
        "Continuous gypsum board ceiling with a frame and trim for a rooflight or skylight. Includes the framework, the board, the frame of the rooflight and the joint treatment. Measured per square meter completed.",

    "Cielo raso continuo de placa de yeso con tapa de registro practicable para inspección. Incluye la estructura, la placa, el registro y el tratamiento de juntas. Medido por metro cuadrado ejecutado.":
        "Continuous gypsum board ceiling with an access panel for inspection. Includes the framework, the board, the access panel and the joint treatment. Measured per square meter completed.",

    "Reparación de cielo raso continuo con sustitución de la placa dañada y tratamiento de juntas. Incluye el corte, la reposición de la placa y el acabado. Medido por metro cuadrado reparado.":
        "Repair of a continuous ceiling with replacement of the damaged board and joint treatment. Includes the cutting, the replacement of the board and the finish. Measured per square meter repaired.",

    "Cielo raso registrable formado por paneles de fibra mineral de 60x60 cm apoyados sobre perfilería vista en T suspendida de la losa, con ángulo perimetral. Su ventaja decisiva es el acceso total al plenum: toda la instalación que discurre por encima queda registrable sin romper nada, por lo que es la solución estándar en oficinas y locales. Incluye replanteo y nivelación con láser, ángulo perimetral, montaje de la retícula con tensores, colocación de los paneles y ajuste de los perimetrales mediante corte limpio. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Suspended ceiling formed by 60x60 cm mineral fiber panels laid on exposed T bar sections suspended from the slab, with a perimeter angle. Its decisive advantage is the full access to the plenum: all the services running above stay accessible without breaking anything, so it is the standard solution in offices and commercial premises. Includes setting out and leveling with a laser, the perimeter angle, installing the grid with hangers, laying the panels and fitting the perimeter panels by cutting them clean. Measured by the area actually completed, deducting openings larger than 1 m².",

    "Cielo raso registrable con bandejas o lamas metálicas prelacadas sobre perfilería suspendida. Frente a la fibra mineral resiste mucho mejor la humedad y la limpieza frecuente, lo que lo hace idóneo en cocinas industriales, baños públicos y áreas exteriores protegidas, aunque su comportamiento acústico es peor salvo que se use bandeja perforada con velo. Incluye replanteo y nivelación, perimetral, montaje de la estructura portante, colocación de las bandejas por encaje y ajuste de las piezas perimetrales. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Suspended ceiling with prefinished metal trays or slats on a suspended framework. Compared with mineral fiber it stands up far better to moisture and to frequent cleaning, which makes it ideal in commercial kitchens, public toilets and protected external areas, although its acoustic behavior is worse unless a perforated tray with an acoustic fleece is used. Includes setting out and leveling, the perimeter, installing the supporting framework, laying the trays by fitting them in and adjusting the perimeter pieces. Measured by the area actually completed, deducting openings larger than 1 m².",

    "Cielo raso desmontable de bandeja metálica lineal, con perfilería de suspensión. Incluye la estructura, la colocación de las bandejas y el remate perimetral. Medido por metro cuadrado ejecutado.":
        "Demountable ceiling of linear metal trays, with a suspension framework. Includes the framework, laying the trays and the perimeter trim. Measured per square meter completed.",

    "Cielo raso desmontable de fibra mineral con panel de lana en la cámara, para aislamiento acústico. Incluye la estructura, la lana, los paneles y el remate perimetral. Medido por metro cuadrado ejecutado.":
        "Demountable ceiling of mineral fiber with a wool panel in the cavity, for acoustic insulation. Includes the framework, the wool, the panels and the perimeter trim. Measured per square meter completed.",

    "Cielo raso desmontable de malla o grilla metálica, con perfilería de suspensión. Incluye la estructura, la colocación de los paneles de malla y el remate. Medido por metro cuadrado ejecutado.":
        "Demountable ceiling of metal mesh or grille, with a suspension framework. Includes the framework, laying the mesh panels and the trim. Measured per square meter completed.",

    "Cielo raso desmontable de panel con sistema de clips de fijación rápida. Incluye la estructura, la colocación de los paneles con clips y el remate. Medido por metro cuadrado ejecutado.":
        "Demountable ceiling of panels with a quick release clip system. Includes the framework, laying the panels with clips and the trim. Measured per square meter completed.",

    "Cielo raso con láminas machihembradas de PVC sobre rastrelado o perfilería, con perfiles de remate perimetrales. Es la solución económica y resistente a la humedad más usada en áreas de servicio, porches y baños, con la ventaja de que se limpia con agua y no se mancha. Incluye replanteo y nivelación, montaje del rastrelado, colocación de los perfiles perimetrales, montaje de las láminas por encaje a presión, los cortes de ajuste alrededor de luminarias y el remate final. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Ceiling of interlocking PVC sheets on battens or sections, with perimeter trim profiles. It is the most widely used economical and moisture resistant solution in service areas, porches and bathrooms, with the advantage that it washes with water and does not stain. Includes setting out and leveling, installing the battens, fitting the perimeter profiles, laying the sheets by pushing them together, the fitting cuts around light fittings and the final trim. Measured by the area actually completed, deducting openings larger than 1 m².",

    "Cielo raso en alero, porche o área exterior cubierta, con lámina de PVC o placa de cemento sobre estructura resistente a la humedad. El material y la estructura deben ser aptos para exterior: una placa de yeso laminado, aunque sea resistente a la humedad, no soporta la humedad ambiental permanente de un alero y termina descolgándose. Incluye el replanteo y nivelación, la estructura de perfilería galvanizada, la colocación del material con sus juntas de dilatación, la ventilación de la cámara y el remate perimetral. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Ceiling on a soffit, porch or covered external area, with PVC sheet or cement board on a moisture resistant framework. The material and the framework must be suitable for external use: a gypsum board, even a moisture resistant one, will not stand the permanent ambient humidity of an overhang and ends up sagging. Includes setting out and leveling, the framework of galvanized sections, laying the material with its movement joints, the ventilation of the cavity and the perimeter trim. Measured by the area actually completed, deducting openings larger than 1 m².",

    "Cielo raso de láminas de PVC para baño, cocina o local húmedo, con su perfilería. Incluye la estructura de fijación, la colocación de las láminas y el remate. Medido por metro cuadrado ejecutado.":
        "Ceiling of PVC sheets for a bathroom, kitchen or wet room, with its sections. Includes the fixing framework, laying the sheets and the trim. Measured per square meter completed.",
}
