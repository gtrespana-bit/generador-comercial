# -*- coding: utf-8 -*-
"""Lote 2: «Actuaciones previas» (2 de 3) — protecciones, apeos y servicios.

Mismo criterio que el lote 1. Terminología que conviene no perder:
  · «Puntal» en Norteamérica es shore; en Reino Unido es prop, y la capa de
    variantes ya lo convierte. Aquí se escribe la forma estadounidense.
  · «Fábrica» (de ladrillo) es masonry.
  · «Durmiente de reparto» es spreader beam: reparte la carga del puntal.
  · «Cierre tipo cremallera» es zip door, que es como se llama en obra.
  · «Croquis» es sketch; «listón» es batten; «parales» son posts.
"""

LOTE = {
"Protección de piso terminado durante la ejecución de la obra.":
    "Protection of finished flooring while the works are carried out.",

"Protección de piso existente que permanece, mediante cartón corrugado en rollo solapado y fijado con cinta en las juntas, colocado sobre lámina de polietileno cuando exista riesgo de humedad. Se emplea en reformas parciales donde el piso de las áreas que no se intervienen debe entregarse intacto. Incluye la limpieza previa de la superficie, el extendido y solape del material, el sellado de juntas y del perímetro contra el rodapié, la reposición de las zonas que se deterioren durante la obra, y el retiro y desecho de la protección al finalizar los trabajos. Medido en superficie realmente protegida.":
    "Protection of existing flooring that is to remain, using overlapping rolls of corrugated cardboard taped at the joints, laid over polyethylene sheeting where there is a risk of moisture. Used on partial remodeling projects where the flooring in areas not being worked on has to be handed back undamaged. Includes cleaning the surface beforehand, laying and lapping the material, sealing the joints and the perimeter against the baseboard, replacing any areas that deteriorate during the works, and removing and disposing of the protection when the work finishes. Measured over the area actually protected.",

"Protección de mobiliario y equipos con lámina plástica.":
    "Protection of furniture and equipment with plastic sheeting.",

"Protección de mobiliario, electrodomésticos y equipos que permanecen en el inmueble durante la obra, mediante lámina de polietileno fijada con cinta. Incluye el agrupamiento previo del mobiliario en la zona más alejada del frente de trabajo, su cubrición completa con lámina solapada, el sellado con cinta para impedir la entrada de polvo, la revisión periódica de la protección mientras dure la obra y su retiro y desecho al finalizar. Medido en superficie de mobiliario realmente protegida.":
    "Protection of furniture, appliances and equipment that stay in the building during the works, using polyethylene sheeting held with tape. Includes first moving the furniture together in the area furthest from the work face, covering it completely with lapped sheeting, sealing with tape to keep dust out, checking the protection periodically while the works last, and removing and disposing of it at the end. Measured over the area of furniture actually protected.",

"Barrera antipolvo con lámina plástica y cierre de paso.":
    "Dust barrier in plastic sheeting with an access opening.",

"Barrera provisional de confinamiento de polvo entre la zona de obra y las áreas en uso, formada por bastidor de listón de madera y lámina de polietileno tensada y sellada en todo su perímetro contra piso, paredes y techo, con cierre tipo cremallera para el paso del personal. Es la medida que permite trabajar en un ambiente mientras el resto del inmueble sigue habitado u operativo. Incluye el replanteo, el montaje del bastidor, la colocación y sellado de la lámina, el montaje del cierre de paso, el mantenimiento de la barrera durante la obra y su desmontaje y retiro al finalizar. Medido en superficie de barrera realmente ejecutada.":
    "Temporary dust containment barrier between the work area and the areas still in use, made up of a lumber batten frame with polyethylene sheeting stretched and sealed around its whole perimeter against floor, walls and ceiling, with a zip door for access. This is what allows work to go on in one room while the rest of the building stays occupied and operating. Includes field layout, erecting the frame, fitting and sealing the sheeting, fitting the access opening, maintaining the barrier while the works last, and dismantling and removing it at the end. Measured over the area of barrier actually erected.",

"Cerramiento provisional de vano con lámina de madera.":
    "Temporary closure of an opening with a wood panel.",

"Cerramiento provisional de vano de puerta o ventana mediante lámina de madera contrachapada u OSB sobre bastidor de listón, anclada al vano. Se emplea para cerrar huecos abiertos por demolición o desmontaje de carpintería, protegiendo el interior frente a la intemperie y frente a intrusiones mientras llega la carpintería definitiva. Incluye el replanteo y corte de la lámina, el montaje del bastidor, la fijación al vano con tacos, el sellado perimetral, su mantenimiento durante la obra y el desmontaje al colocar la carpintería definitiva. Medido en superficie de vano realmente cerrada.":
    "Temporary closure of a door or window opening using a plywood or OSB panel on a batten frame, anchored into the opening. Used to close up voids left by demolition or by removing doors and windows, keeping the interior safe from the weather and from intruders until the permanent units arrive. Includes field layout and cutting the panel, building the frame, fastening it into the opening with anchors, sealing around the perimeter, maintaining it while the works last, and taking it down when the permanent units are fitted. Measured over the area of opening actually closed.",

"Cerramiento perimetral provisional de obra con malla de señalización.":
    "Temporary perimeter hoarding with warning mesh.",

"Cerramiento provisional del perímetro de la zona de obra mediante malla plástica de señalización sostenida por parales metálicos o de madera, con señalización de advertencia. Delimita el área de trabajo e impide el paso de personas ajenas, requisito básico de seguridad cuando la obra convive con zonas en uso o da a espacios comunes. Incluye el replanteo, la colocación y arriostramiento de los parales, el tensado y fijación de la malla, la colocación de las señales de advertencia, el mantenimiento durante la obra y el desmontaje y retiro al finalizar. Medido en longitud realmente cerrada.":
    "Temporary enclosure of the perimeter of the work area using plastic warning mesh on steel or lumber posts, with warning signs. It defines the work area and keeps unauthorized people out, a basic safety requirement where the works share the site with areas still in use or open onto common areas. Includes field layout, placing and bracing the posts, stretching and fastening the mesh, putting up the warning signs, maintaining it while the works last, and dismantling and removing it at the end. Measured over the length actually enclosed.",

"Protección de carpintería y aparatos que permanecen en obra.":
    "Protection of doors, windows and fixtures remaining on site.",

"Protección de puertas, ventanas, aparatos sanitarios y elementos terminados que permanecen dentro de la zona de trabajo, mediante lámina plástica y cartón fijados con cinta de baja adherencia que no deje residuo ni dañe los acabados. Incluye el enmascarado de marcos, herrajes y vidrios, la cubrición de los aparatos sanitarios que siguen en servicio, la reposición de la protección deteriorada y su retiro y limpieza al finalizar la obra. Medido en superficie realmente protegida.":
    "Protection of doors, windows, plumbing fixtures and finished elements that remain inside the work area, using plastic sheeting and cardboard held with low-tack tape that leaves no residue and does not damage the finishes. Includes masking frames, hardware and glazing, covering the plumbing fixtures still in service, replacing protection that becomes damaged, and removing it and cleaning up when the works finish. Measured over the area actually protected.",

"Apeo de losa con puntales y durmientes.":
    "Shoring of a slab with shores and spreader beams.",

"Apeo de losa con puntales metálicos y durmientes de reparto. Incluye la colocación de puntales y el arriostramiento. Medido por metro cuadrado apeado.":
    "Shoring of a slab with steel shores and spreader beams. Includes placing the shores and the bracing. Measured per square meter shored.",

"Apeo de viga con puntales.":
    "Shoring of a beam with shores.",

"Apeo de viga con puntales metálicos. Incluye la colocación de puntales y el arriostramiento. Medido por metro lineal apeado.":
    "Shoring of a beam with steel shores. Includes placing the shores and the bracing. Measured per linear meter shored.",

"Apuntalamiento de muro con madera.":
    "Shoring of a wall with lumber.",

"Apuntalamiento de muro con madera y puntales. Incluye la colocación del apuntalamiento. Medido por metro cuadrado apuntalado.":
    "Shoring of a wall with lumber and shores. Includes installing the shoring. Measured per square meter shored.",

"Apeo de cubierta o techo.":
    "Shoring of a roof.",

"Apeo de cubierta o techo durante trabajos de refuerzo. Incluye la colocación de puntales. Medido por metro cuadrado apeado.":
    "Shoring of a roof during strengthening work. Includes placing the shores. Measured per square meter shored.",

"Apeo de dintel durante apertura de vano.":
    "Shoring of a lintel while an opening is formed.",

"Apeo de dintel durante la apertura de vano. Incluye la colocación de puntales. Medido por metro lineal apeado.":
    "Shoring of a lintel while the opening is formed. Includes placing the shores. Measured per linear meter shored.",

"Estabilización de muro con arriostramiento.":
    "Stabilizing a wall with bracing.",

"Estabilización de muro con arriostramiento metálico provisional. Incluye la colocación del arriostramiento. Medido por metro cuadrado estabilizado.":
    "Stabilizing a wall with temporary steel bracing. Includes installing the bracing. Measured per square meter stabilized.",

"Apeo de fachada durante demolición parcial.":
    "Shoring of a facade during partial demolition.",

"Apeo de fachada durante demolición parcial. Incluye la colocación de puntales y arriostramiento. Medido por metro cuadrado apeado.":
    "Shoring of a facade during partial demolition. Includes placing the shores and the bracing. Measured per square meter shored.",

"Apeo de escalera existente.":
    "Shoring of an existing stair.",

"Apeo de escalera existente durante trabajos de refuerzo. Incluye la colocación de puntales. Medido por metro lineal apeado.":
    "Shoring of an existing stair during strengthening work. Includes placing the shores. Measured per linear meter shored.",

"Apeo de losa con torres de carga.":
    "Shoring of a slab with load towers.",

"Apeo de losa con torres de carga metálicas. Incluye la colocación de las torres. Medido por metro cuadrado apeado.":
    "Shoring of a slab with steel load towers. Includes erecting the towers. Measured per square meter shored.",

"Apuntalamiento de talud interior.":
    "Shoring of an internal slope.",

"Apuntalamiento de talud o excavación interior. Incluye la colocación de la entibación. Medido por metro cuadrado apuntalado.":
    "Shoring of an internal slope or excavation. Includes installing the trench sheeting. Measured per square meter shored.",

"Replanteo general de la obra y trazado de ejes.":
    "General field layout of the works and marking of grid lines.",

"Replanteo general de la intervención sobre el inmueble, con trazado de los ejes de tabiquería, los niveles de piso terminado y las cotas de referencia, ejecutado con nivel láser y equipo de medición. Incluye la comprobación de escuadras y de la geometría real frente a la del plano, el marcado de los ejes sobre piso y paramentos, el establecimiento de la cota de nivel de referencia que regirá toda la obra, la señalización de los puntos fijos y la anotación de las discrepancias detectadas respecto al proyecto. Medido en superficie de intervención realmente replanteada.":
    "General field layout of the works in the building, marking the partition grid lines, the finished floor levels and the datum levels, carried out with a laser level and measuring equipment. Includes checking squareness and comparing the actual geometry against the drawing, marking the grid lines on floor and walls, establishing the datum level that will govern the whole job, marking the fixed reference points and noting any discrepancies found against the design. Measured over the area of work actually set out.",

"Replanteo de ejes de muros.":
    "Field layout of wall grid lines.",

"Replanteo de ejes de muros con nivel láser. Incluye el trazado de los ejes. Medido por metro lineal replanteado.":
    "Field layout of wall grid lines with a laser level. Includes marking the lines. Measured per linear meter set out.",

"Replanteo de niveles y pendientes.":
    "Field layout of levels and falls.",

"Replanteo de niveles y pendientes de piso. Incluye el marcado de cotas. Medido por metro lineal replanteado.":
    "Field layout of floor levels and falls. Includes marking the levels. Measured per linear meter set out.",

"Control geométrico de paramentos.":
    "Geometric check of wall and ceiling surfaces.",

"Control geométrico de plomos y niveles de paramentos. Incluye la verificación con nivel láser. Medido por metro cuadrado verificado.":
    "Geometric check that wall and ceiling surfaces are plumb and level. Includes checking with a laser level. Measured per square meter checked.",

"Replanteo de instalaciones.":
    "Field layout of services.",

"Replanteo de instalaciones (eléctrica, sanitaria) con trazado de recorridos. Incluye el marcado. Medido por instalación replanteada.":
    "Field layout of services (electrical, plumbing) with the runs marked. Includes marking. Measured per installation set out.",

"Replanteo de vanos y carpintería.":
    "Field layout of openings and door and window units.",

"Replanteo de vanos y carpintería. Incluye el trazado de las posiciones. Medido por metro lineal replanteado.":
    "Field layout of openings and door and window units. Includes marking the positions. Measured per linear meter set out.",

"Replanteo de cielos rasos.":
    "Field layout of suspended ceilings.",

"Replanteo de cielos rasos y alturas. Incluye el marcado de cotas. Medido por metro cuadrado replanteado.":
    "Field layout of suspended ceilings and their heights. Includes marking the levels. Measured per square meter set out.",

"Replanteo de escalera.":
    "Field layout of a stair.",

"Replanteo de escalera y peldaños. Incluye el trazado de huellas y contrahuellas. Medido por escalera replanteada.":
    "Field layout of a stair and its treads. Includes marking the treads and risers. Measured per stair set out.",

"Control de planitud de pisos.":
    "Flatness check of floors.",

"Control de planitud de pisos con regla y nivel. Incluye la verificación. Medido por metro cuadrado verificado.":
    "Flatness check of floors with a straightedge and level. Includes the check. Measured per square meter checked.",

"Replanteo de desagües y pendientes.":
    "Field layout of drains and falls.",

"Replanteo de desagües y pendientes de piso. Incluye el marcado de las pendientes. Medido por metro lineal replanteado.":
    "Field layout of floor drains and falls. Includes marking the falls. Measured per linear meter set out.",

"Replanteo de particiones.":
    "Field layout of partitions.",

"Replanteo de particiones y tabiques. Incluye el trazado de los ejes. Medido por metro cuadrado replanteado.":
    "Field layout of partitions and partition walls. Includes marking the grid lines. Measured per square meter set out.",
}
