# -*- coding: utf-8 -*-
"""Descripciones — Revestimientos y acabados (2 de n): preparación y reparación
de soportes.

Son las partidas previas al acabado: preparar, sanear y reparar el
soporte. Aquí es donde se juega el resultado, y las descripciones lo
dicen, así que la explicación se conserva entera.

Vocabulario aplicado:

· «Resane» es patching, y «saneado» es making good cuando se retira lo
  que está mal y cut out cuando se corta.
· «Fisura» es crack y «grieta» es también crack; el matiz del español
  entre ambas no existe en inglés, así que se usa crack para las dos y
  se distingue por el contexto, como se hace en el oficio.
· «Masilla» es filler cuando se rellena y sealant cuando sella; «masilla
  elástica» es flexible sealant, porque lo que hace es acompañar el
  movimiento de la fisura.
· «Banda de refuerzo» es reinforcing tape y «malla de refuerzo» es
  reinforcing mesh: la primera va en la fisura y la segunda en la
  superficie.
· «Cantonera» es corner bead, «arista» es arris y «cajeado» es chasing
  out, que es como se abre una fisura para dar alojamiento al sellador.
· «Puente de adherencia» es bonding coat y «fondo fijador» es
  stabilizing primer, el que consolida un soporte que se deshace.
· «Eflorescencias» es efflorescence, y «hidrolavadora» es pressure
  washer.
· «Fisuras vivas» son live cracks: las que se mueven, y por eso llevan
  banda.
"""

LOTE = {
    "Preparación completa de paramento interior antes de pintar. Incluye protección de pisos, carpintería y mobiliario con plástico y cinta de enmascarar, retirada de partes sueltas, resane de grietas y huecos con masilla de reparación, alisado y lijado hasta obtener superficie uniforme, eliminación del polvo residual y aplicación de una mano de fondo fijador para consolidar el soporte y regular su absorción. Deja el paramento listo para recibir el acabado. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Complete preparation of an interior substrate before painting. Includes protecting floors, joinery and furniture with plastic sheeting and masking tape, removing loose material, patching cracks and holes with repair filler, smoothing and sanding until an even surface is obtained, removing the residual dust and applying one coat of stabilizing primer to consolidate the substrate and even out its absorption. Leaves the substrate ready to receive the finish. Measured by the area actually completed, deducting openings over 1 m².",

    "Preparación de fachada o paramento exterior antes de pintar, con lavado a presión, eliminación de partes sueltas, tratamiento de hongos y aplicación de fondo fijador. En exterior la preparación pesa más que la pintura: aplicada sobre una superficie con moho o con friso disgregado, la mejor pintura se desprende en una temporada de lluvias. Incluye el lavado con hidrolavadora, el raspado de las zonas desprendidas, la aplicación de solución fungicida sobre las manchas de moho con su tiempo de actuación y enjuague, el resane de fisuras y el fondo fijador. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Preparation of a facade or exterior substrate before painting, with pressure washing, removal of loose material, treatment of mold and the application of a stabilizing primer. Outdoors, the preparation matters more than the paint: applied over a surface with mold or with stucco that has broken down, the best paint comes off within a single rainy season. Includes washing with a pressure washer, scraping the areas that have come away, applying a fungicidal solution to the mold patches with its dwell time and rinsing, patching the cracks and the stabilizing primer. Measured by the area actually completed, deducting openings over 1 m².",

    "Apertura, saneado y sellado de fisuras en paramento antes de pintar, con masilla elástica y banda de refuerzo en las de mayor apertura. Pintar sobre una fisura sin tratar solo la disimula unas semanas: reaparece en la misma línea en cuanto el paramento se mueve, y el cliente lo lee como un defecto de la pintura. Incluye el mapeo de las fisuras, su apertura en cajeado para dar alojamiento al sellador, la limpieza y aspirado, la imprimación, el relleno con masilla elástica, el refuerzo con banda en las fisuras vivas y el lijado de la transición. Medido en longitud de fisura realmente tratada.":
        "Opening up, making good and sealing cracks in a substrate before painting, with flexible sealant and reinforcing tape on the wider ones. Painting over an untreated crack only hides it for a few weeks: it reappears along the same line as soon as the substrate moves, and the client reads it as a fault in the paint. Includes mapping the cracks, chasing them out to give the sealant somewhere to sit, cleaning and vacuuming, priming, filling with flexible sealant, reinforcing with tape on the live cracks and sanding the transition. Measured by the length of crack actually treated.",

    "Reparación de grietas en paramento con apertura, colocación de malla de refuerzo y sellado con mortero. Incluye la apertura de la grieta, la malla y el relleno. Medido por metro lineal reparado.":
        "Repair of cracks in a substrate by opening them up, fitting reinforcing mesh and sealing with mortar. Includes opening up the crack, the mesh and the filling. Measured per meter repaired.",

    "Aplicación de puente de adherencia sobre soporte de concreto endurecido previo a la colocación de mortero o enchapado. Incluye la limpieza y la aplicación del puente. Medido por metro cuadrado tratado.":
        "Application of a bonding coat to a hardened concrete substrate prior to laying mortar or tiling. Includes the cleaning and the application of the bonding coat. Measured per square meter treated.",

    "Preparación de soporte para enchapado con mortero de nivelación que garantiza un paramento plano y limpio. Incluye la regularización y el afinado previo a la colocación. Medido por metro cuadrado preparado.":
        "Preparation of the substrate for tiling with leveling mortar, guaranteeing a flat and clean surface. Includes making it level and the finishing prior to laying. Measured per square meter prepared.",

    "Preparación de piso existente para la colocación de un nuevo revestimiento, con raspado, limpieza y nivelación de las irregularidades. Incluye la retirada de restos y la nivelación previa. Medido por metro cuadrado preparado.":
        "Preparation of an existing floor for the laying of a new covering, with scraping, cleaning and leveling out the irregularities. Includes removing the residue and the prior leveling. Measured per square meter prepared.",

    "Resane de paramento interior con masilla para eliminar imperfecciones previo a la pintura. Incluye la aplicación de la masilla y el lijado. Medido por metro cuadrado resanado.":
        "Patching of an interior substrate with filler to remove imperfections prior to painting. Includes applying the filler and sanding. Measured per square meter patched.",

    "Reparación de paramento de concreto deteriorado con mortero de reparación estructural, previo a cualquier acabado. Incluye el saneado de la zona, la aplicación del mortero y el afinado. Medido por metro cuadrado reparado.":
        "Repair of a deteriorated concrete substrate with structural repair mortar, prior to any finish. Includes making good the area, applying the mortar and the finishing. Measured per square meter repaired.",

    "Reparación de esquina o arista de paramento con colocación de cantonera metálica y acabado con mortero o pasta. Incluye la fijación de la cantonera y el remate. Medido por metro lineal de esquina reparada.":
        "Repair of a corner or arris of a substrate by fitting a metal corner bead and finishing with mortar or filler. Includes fixing the corner bead and the finishing. Measured per meter of corner repaired.",

    "Saneado de paramento con eflorescencias salinas, con cepillado, lavado y aplicación de tratamiento neutralizante. Incluye la limpieza de las sales y el tratamiento previo al acabado. Medido por metro cuadrado saneado.":
        "Making good of a substrate with salt efflorescence, with brushing, washing and the application of a neutralizing treatment. Includes cleaning off the salts and the treatment prior to the finish. Measured per square meter made good.",
}
