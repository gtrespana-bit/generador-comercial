# -*- coding: utf-8 -*-
"""Lote 3: «Actuaciones previas» (3 de 3) — servicios provisionales y seguridad.

Terminología eléctrica estadounidense, que es la base del glosario:
  · «Interruptor diferencial» -> ground-fault circuit interrupter (GFCI).
    En Reino Unido es RCD, y la capa de variantes ya lo ajusta.
  · «Protecciones magnetotérmicas» -> circuit breakers.
  · «Cable encauchetado» es el venezolanismo para el cable de goma de obra:
    heavy-duty rubber cable.
  · «Puesta a tierra» -> grounding (GB: earthing).
  · «Botiquín» -> first aid kit; «extintor» -> fire extinguisher.
"""

LOTE = {
"Acometida eléctrica provisional de obra con tablero de protección.":
    "Temporary electrical supply for the works, with a distribution panel.",

"Instalación eléctrica provisional para el suministro de la obra, formada por tablero con interruptor diferencial y protecciones magnetotérmicas, tomas de fuerza y cable encauchetado hasta los frentes de trabajo. Incluye la conexión al punto de suministro autorizado, el montaje y fijación del tablero en lugar protegido y accesible, el tendido del cableado por recorridos que no crucen zonas de paso ni de agua, la puesta a tierra del conjunto, la comprobación del disparo del diferencial antes de la puesta en servicio, el mantenimiento durante la obra y el desmontaje final. Medido por instalación realmente ejecutada.":
    "Temporary electrical installation to supply the works, made up of a distribution panel with a ground-fault circuit interrupter and circuit breakers, power outlets, and heavy-duty rubber cable run to the work faces. Includes connecting to the authorized supply point, mounting and fixing the panel somewhere protected and accessible, running the cable along routes that cross neither walkways nor wet areas, grounding the whole installation, testing that the ground-fault interrupter trips before the system is brought into service, maintaining it while the works last, and dismantling it at the end. Measured per installation actually carried out.",

"Punto de agua provisional de obra.":
    "Temporary water point for the works.",

"Instalación de punto de agua provisional para el amasado de morteros, la limpieza y el consumo de la obra, formado por derivación desde la red existente con llave de paso, manguera reforzada hasta el frente de trabajo y punto de descarga con recogida. Incluye la comprobación de la presión disponible, el montaje de la llave y los accesorios, el tendido de la manguera por recorridos protegidos del tránsito, la previsión de la evacuación del agua utilizada para no inundar zonas terminadas, el mantenimiento durante la obra y el desmontaje final con reposición del punto de toma. Medido por punto realmente instalado.":
    "Installation of a temporary water point for mixing mortar, cleaning and general use on site, made up of a branch off the existing main with a stop valve, a reinforced hose run to the work face, and a discharge point with collection. Includes checking the available pressure, fitting the valve and accessories, running the hose along routes protected from traffic, providing for the run-off so finished areas are not flooded, maintaining it while the works last, and dismantling it at the end and reinstating the draw-off point. Measured per point actually installed.",

"Iluminación provisional de obra.":
    "Temporary site lighting.",

"Iluminación provisional de los frentes de trabajo mediante reflectores de obra sobre soporte o suspendidos, alimentados desde el tablero provisional, garantizando el nivel de luz necesario para trabajar con seguridad y con calidad de acabado. Incluye el reparto de los puntos de luz según los frentes activos, el tendido del cableado, la fijación de los reflectores fuera de las zonas de paso y de proyección de material, su reubicación conforme avanza la obra, la reposición de lámparas y el desmontaje final. Medido en superficie de obra realmente iluminada.":
    "Temporary lighting of the work faces using site floodlights on stands or suspended, fed from the temporary panel, providing the light level needed to work safely and to a good finish. Includes distributing the lighting points among the active work faces, running the cable, fixing the floodlights clear of walkways and of the line of throw of materials, repositioning them as the works progress, replacing lamps, and dismantling at the end. Measured over the area of the works actually lit.",

"Baño portátil de obra, por mes de permanencia.":
    "Portable site toilet, per month on site.",

"Puesta a disposición de baño portátil para el personal de obra, incluido su traslado, emplazamiento, mantenimiento y vaciado periódico durante un mes. Es exigible en obras sin servicios sanitarios utilizables y evita el uso de los del inmueble en reforma. Incluye el transporte y colocación en punto accesible al camión de servicio, el suministro de consumibles, el vaciado y limpieza periódicos y el retiro al finalizar el periodo. Medido por mes de permanencia.":
    "Provision of a portable toilet for the site workforce, including delivery, siting, maintenance and periodic emptying for one month. Required on sites with no usable sanitary facilities, and it keeps the workforce out of the facilities of a building being refurbished. Includes transport and siting at a point the service truck can reach, supplying consumables, periodic emptying and cleaning, and removal at the end of the period. Measured per month on site.",

"Caseta o zona cerrada de acopio de materiales y herramienta, por mes.":
    "Store or enclosed area for materials and tools, per month.",

"Habilitación de una zona cerrada dentro de la obra para el acopio de materiales y el guardado de herramienta, mediante cerramiento de lámina de madera sobre bastidor con puerta y cierre, o mediante la adecuación de un ambiente existente. Incluye el montaje del cerramiento y de la puerta con cerradura, la protección del piso de la zona de acopio, la organización de estanterías o tarimas para separar el material del suelo, el mantenimiento del orden durante el periodo y el desmontaje al finalizar la obra. Medido por mes de permanencia.":
    "Fitting out an enclosed area within the site for storing materials and keeping tools, either by building an enclosure in sheet wood on a frame with a door and lock, or by adapting an existing room. Includes building the enclosure and fitting the door with a lock, protecting the floor of the storage area, providing shelving or pallets to keep materials off the ground, keeping it tidy throughout the period, and dismantling it when the works finish. Measured per month on site.",

"Acometida eléctrica provisional de obra.":
    "Temporary electrical supply for the works.",

"Acometida eléctrica provisional de obra con tablero de protección. Incluye el tendido y el tablero. Medido por acometida ejecutada.":
    "Temporary electrical supply for the works with a distribution panel. Includes running the cable and the panel. Measured per supply actually installed.",

"Punto de agua provisional con llave y manguera.":
    "Temporary water point with a valve and hose.",

"Punto de agua provisional de obra, con llave y manguera. Incluye la conexión y la llave. Medido por punto ejecutado.":
    "Temporary water point for the works, with a valve and hose. Includes the connection and the valve. Measured per point installed.",

"Iluminación provisional con reflectores.":
    "Temporary lighting with floodlights.",

"Iluminación provisional de obra, con reflectores. Incluye la colocación de los reflectores. Medido por punto ejecutado.":
    "Temporary site lighting with floodlights. Includes installing the floodlights. Measured per point installed.",

"Baño portátil de obra, por mes.":
    "Portable site toilet, per month.",

"Alquiler de baño portátil de obra, por mes. Incluye el suministro y la limpieza. Medido por mes de permanencia.":
    "Rental of a portable site toilet, per month. Includes supply and cleaning. Measured per month on site.",

"Caseta de acopio de materiales, por mes.":
    "Materials store, per month.",

"Caseta o zona cerrada de acopio de materiales, por mes. Incluye el montaje y la permanencia. Medido por mes de permanencia.":
    "Store or enclosed area for materials, per month. Includes erection and the period on site. Measured per month on site.",

"Suministro de botiquín de primeros auxilios.":
    "Supply of a first aid kit.",

"Suministro y colocación de botiquín de primeros auxilios de obra. Incluye la dotación y la reposición. Medido por botiquín suministrado.":
    "Supply and siting of a site first aid kit. Includes the contents and restocking them. Measured per kit supplied.",

"Extintor de obra.":
    "Site fire extinguisher.",

"Suministro y colocación de extintor de obra. Incluye la fijación y la señalización. Medido por extintor suministrado.":
    "Supply and siting of a site fire extinguisher. Includes fixing it in place and signing it. Measured per extinguisher supplied.",

"Zona de lavado de herramienta.":
    "Tool wash area.",

"Habilitación de zona de lavado de herramienta. Incluye la conexión de agua y la delimitación. Medido por zona habilitada.":
    "Fitting out an area for washing tools. Includes the water connection and marking out the area. Measured per area fitted out.",

"Acometida provisional de agua.":
    "Temporary water supply.",

"Acometida provisional de agua de obra. Incluye la conexión a la red y la llave general. Medido por acometida ejecutada.":
    "Temporary water supply for the works. Includes connecting to the main and the main stop valve. Measured per supply actually installed.",

"Red provisional de desagüe de obra.":
    "Temporary site drainage.",

"Ejecución de red provisional de desagüe de obra. Incluye la conexión y el tendido. Medido por red ejecutada.":
    "Installation of temporary site drainage. Includes the connection and the pipe run. Measured per system installed.",

"Apuntalamiento de vano durante la apertura de hueco.":
    "Shoring of an opening while it is formed.",

"Apuntalamiento provisional del muro situado sobre un vano que se va a abrir o ampliar, mediante puntales y durmientes que reciben la carga de la fábrica superior mientras se ejecuta la demolición y se coloca el dintel definitivo. Es la operación que evita el colapso de la fábrica al retirar el apoyo. Incluye el replanteo, la apertura de las cajas de apoyo del durmiente en el muro, el montaje y puesta en carga de los puntales a ambas caras, la verificación durante la demolición, la retirada del apeo una vez fraguado y en carga el dintel definitivo y el resane de las cajas de apoyo. Medido por vano realmente apuntalado.":
    "Temporary shoring of the wall over an opening that is to be formed or widened, using shores and spreader beams that carry the load of the masonry above while the demolition is carried out and the permanent lintel is placed. This is what stops the masonry collapsing when its support is removed. Includes setting out, cutting the bearing pockets for the spreader beam into the wall, erecting and loading the shores on both faces, checking them during the demolition, removing the shoring once the permanent lintel has cured and taken load, and patching the bearing pockets. Measured per opening actually shored.",

"Apeo o arriostramiento provisional de muro.":
    "Temporary shoring or bracing of a wall.",

"Apeo o arriostramiento provisional de muro mediante puntales inclinados con durmientes de reparto, para estabilizarlo frente a empujes o vuelco durante los trabajos en su entorno. Debe responder a la instrucción del profesional responsable. Incluye el replanteo de los puntos de apoyo, la preparación de las bases de reparto en el piso, el montaje y puesta en carga de los puntales inclinados, la comprobación periódica de la estabilidad y del apriete, y el desmontaje una vez consolidado el elemento. Medido en superficie de muro realmente apeada.":
    "Temporary shoring or bracing of a wall using raking shores with spreader beams, to stabilize it against thrust or overturning while work goes on around it. Must follow the instruction of the engineer or architect in charge. Includes setting out the bearing points, preparing the spreader bases on the floor, erecting and loading the raking shores, periodically checking stability and tightness, and dismantling once the element has been made good. Measured over the area of wall actually shored.",
}
