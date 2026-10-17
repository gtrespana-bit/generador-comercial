# -*- coding: utf-8 -*-
"""Descripciones — Actuaciones previas (capítulo completo, 35).

Criterios de este lote:
  · Las descripciones son las que explican por qué se cobra algo, y en
    inglés de obra se escriben en infinitivo o en gerundio según lo que
    siga: «Includes …» y «Measured per …» cierran casi todas.
  · «Desapeo escalonado» es the staged removal of the shoring: el apeo no
    se quita, se retira por fases cuando el elemento ya resiste.
  · «Durmiente de reparto» es spreader beam, la viga que reparte la carga
    del puntal sobre el elemento.
  · «Arriostramiento» es tying in cuando sujeta el andamio a la fachada y
    bracing cuando arriostra la propia estructura.
  · «Silleta suspendida» es swing stage en Estados Unidos y suspended
    cradle en Reino Unido, y aquí la seguridad depende del anclaje.
"""

LOTE = {
"Traslado del mobiliario y enseres del cliente desde la zona de obra hasta un ambiente de acopio dentro del mismo inmueble, con su protección y su devolución al finalizar. En reforma de vivienda habitada es una tarea real que consume jornadas y que casi nunca se presupuesta, de modo que sale del bolsillo del constructor. Incluye el desmontaje de lo que lo requiera, el traslado con protección de pisos y esquinas en el recorrido, el apilado ordenado y cubierto en la zona de acopio, y el traslado de vuelta y montaje al terminar. Medido en superficie realmente ejecutada.":
    "Removal of the client's furniture and belongings from the work area to a storage room within the same building, protected, and returned when the work is finished. In an occupied dwelling under refurbishment this is real work that takes days and is almost never priced, so it comes out of the builder's pocket. Includes dismantling whatever needs it, moving it with protection to floors and corners along the route, stacking it neatly and covered in the storage room, and moving and reassembling everything on completion. Measured by the area actually carried out.",

"Colocación de malla de protección en la fachada o en el andamio, para retener la caída de material y polvo hacia la vía pública o hacia las propiedades vecinas. Es exigible siempre que se trabaje en altura sobre zonas de paso, y su ausencia es motivo habitual de paralización por parte de la autoridad municipal. Incluye el izado, el tendido de los paños solapados, su atado a la estructura del andamio en todo el perímetro, la revisión periódica de amarres tras episodios de viento y el desmontaje. Medido en superficie realmente ejecutada.":
    "Installation of protective netting on the facade or on the scaffold, to contain falling material and dust towards the public highway or neighbouring property. It is required whenever work at height is carried out over areas in use, and its absence is a common reason for the local authority to stop the work. Includes hoisting, hanging the overlapping sheets, tying them to the scaffold structure around the whole perimeter, periodic checking of the ties after windy weather and dismantling. Measured by the area actually carried out.",

"Montaje de puerta provisional con cierre en el acceso a la zona de obra, para separar el área de trabajo de la zona en uso y controlar el acceso. Incluye el bastidor, el forro con lámina de madera, las bisagras y el cierre con candado, la banda de sellado perimetral que impide el paso de polvo, la señalización de acceso restringido y el desmontaje al finalizar. Medido por unidad instalada.":
    "Installation of a temporary lockable door at the entrance to the work area, to separate it from the area in use and control access. Includes the frame, the wood sheet facing, the hinges and the padlock hasp, the perimeter sealing strip that keeps dust out, the restricted access signage and dismantling on completion. Measured per unit installed.",

"Protección de escalera existente durante la obra. Incluye la colocación de protección en huellas y barandas. Medido por metro cuadrado protegido.":
    "Protection of an existing stair during the works. Includes protection to the treads and handrails. Measured per square meter protected.",

"Protección de ventanas y vidrios existentes durante la obra. Incluye la colocación de lámina protectora. Medido por metro cuadrado protegido.":
    "Protection of existing windows and glazing during the works. Includes the application of protective film. Measured per square meter protected.",

"Protección de puerta existente durante la obra. Incluye el forrado con cartón o lámina. Medido por metro cuadrado protegido.":
    "Protection of an existing door during the works. Includes covering with cardboard or sheet. Measured per square meter protected.",

"Protección de baranda o pasamanos existente. Incluye el forrado con lámina. Medido por metro lineal protegido.":
    "Protection of an existing guardrail or handrail. Includes covering with sheet. Measured per meter protected.",

"Protección de cielo raso existente durante la obra. Incluye la colocación de lámina protectora. Medido por metro cuadrado protegido.":
    "Protection of an existing ceiling during the works. Includes the installation of protective sheeting. Measured per square meter protected.",

"Protección de zócalo o rodapié existente. Incluye el forrado con cartón. Medido por metro lineal protegido.":
    "Protection of an existing baseboard. Includes covering with cardboard. Measured per meter protected.",

"Protección de sanitarios y grifería existente durante la obra. Incluye el forrado con lámina y cartón. Medido por unidad protegida.":
    "Protection of existing plumbing fixtures and faucets during the works. Includes covering with sheet and cardboard. Measured per unit protected.",

"Protección de mesón o mueble de cocina existente. Incluye el forrado con cartón y lámina. Medido por metro cuadrado protegido.":
    "Protection of an existing kitchen countertop or cabinet. Includes covering with cardboard and sheet. Measured per square meter protected.",

"Colocación de barrera antipolvo con lámina plástica. Incluye la fijación de la lámina y el cierre. Medido por metro cuadrado colocado.":
    "Installation of a dust barrier of plastic sheeting. Includes fixing the sheeting and the closure. Measured per square meter installed.",

"Cerramiento provisional de vano con lámina de madera. Incluye la fijación de la lámina. Medido por metro cuadrado cerrado.":
    "Temporary closing off of an opening with a wood panel. Includes fixing the panel. Measured per square meter closed off.",

"Colocación de junta de estanqueidad antipolvo en vano. Incluye la fijación de la junta. Medido por metro lineal colocado.":
    "Installation of a dust-tight seal around an opening. Includes fixing the seal. Measured per meter installed.",

"Colocación de mampara antipolvo con puerta de paso. Incluye la estructura y la lámina. Medido por metro cuadrado colocado.":
    "Installation of a dust screen with a door. Includes the frame and the sheeting. Measured per square meter installed.",

"Señalización y delimitación de la zona de obra. Incluye la colocación de señalización y cintas. Medido por metro cuadrado delimitado.":
    "Signage and delimitation of the work area. Includes the placing of signs and barrier tape. Measured per square meter delimited.",

"Instalación de control de acceso a zona de obra. Incluye la señalización y la delimitación del acceso. Medido por acceso habilitado.":
    "Installation of access control to the work area. Includes signage and delimitation of the access. Measured per access point provided.",

"Colocación de cartel informativo de obra. Incluye la fijación del cartel. Medido por unidad colocado.":
    "Installation of a site information board. Includes fixing the board. Measured per unit installed.",

"Andamio tubular metálico apoyado en fachada, con plataformas de trabajo, barandas, rodapiés y escalera interior de acceso, incluido su montaje, el primer mes de permanencia y su desmontaje. Incluye el estudio previo del apoyo y del arriostramiento a fachada, el montaje por personal competente, la colocación de las protecciones colectivas, la revisión del conjunto antes de la puesta en servicio y tras cualquier modificación, el desmontaje ordenado y el retiro del material. No incluye la permanencia adicional más allá del primer mes, que se valora en la partida siguiente. Medido en superficie de fachada realmente cubierta por el andamio.":
    "Tubular steel scaffold bearing on the facade, with working platforms, guardrails, toe boards and an internal access stair, including its erection, the first month on hire and its dismantling. Includes the prior assessment of the bearing and of the ties to the facade, erection by competent personnel, the installation of the collective protective measures, inspection of the whole assembly before it is brought into service and after any modification, orderly dismantling and removal of the material. It does not include hire beyond the first month, which is priced in the following item. Measured by the area of facade actually covered by the scaffold.",

"Permanencia de andamio tubular de fachada más allá del primer mes ya incluido en la partida de montaje, con las revisiones periódicas del conjunto que exige mantenerlo en servicio. Incluye la inspección mensual de apoyos, arriostramientos, plataformas y protecciones colectivas, el reapriete de uniones, la reposición de los elementos deteriorados y el registro de las revisiones. Medido en superficie de andamio por cada mes adicional de permanencia.":
    "Hire of a tubular facade scaffold beyond the first month already included in the erection item, with the periodic inspections that keeping it in service requires. Includes the monthly inspection of bearings, ties, platforms and collective protective measures, retightening of the couplings, replacement of damaged components and recording of the inspections. Measured by the area of scaffold for each additional month on hire.",

"Andamio interior rodante o plataforma sobre borriquetas para trabajos en altura en interiores, tales como cielos rasos, frisos de pared alta y pintura. Incluye el traslado del equipo a obra, su montaje y nivelación, la colocación de barandas cuando la altura de trabajo lo exija, los desplazamientos y ajustes de altura sucesivos a lo largo de la jornada, el desmontaje y el retiro. Medido en superficie de techo o de paramento realmente atendida desde el andamio.":
    "Mobile indoor scaffold or trestle platform for work at height indoors, such as ceilings, plaster on high walls and painting. Includes delivery of the equipment to site, its erection and leveling, the installation of guardrails where the working height requires it, successive repositioning and height adjustment through the working day, dismantling and removal. Measured by the area of ceiling or wall surface actually reached from the scaffold.",

"Puesta a disposición de montacargas o pluma de obra para el descenso de escombro y la subida de materiales en obras en planta alta, incluido un mes de permanencia. Incluye el traslado del equipo, su montaje y anclaje, la verificación de la carga máxima admisible y del punto de apoyo, la señalización y acordonamiento de la zona de descarga, la revisión periódica de cables y frenos, el desmontaje y el retiro. Medido por mes de permanencia del equipo en obra.":
    "Provision of a site hoist or crane for lowering debris and raising materials on works above ground floor level, including one month on hire. Includes delivery of the equipment, its erection and anchoring, verification of the maximum permissible load and of the bearing point, signage and barring off of the landing area, periodic inspection of ropes and brakes, dismantling and removal. Measured per month of the equipment on site.",

"Puesta a disposición de andamio colgante o silleta suspendida para trabajos puntuales en fachada donde no se justifica el montaje de andamio tubular. Su seguridad depende por completo de los puntos de anclaje en cubierta y del uso obligatorio de línea de vida independiente del equipo de suspensión, requisito que no admite excepción. Incluye el estudio y ejecución de los anclajes, el montaje del equipo, la prueba de carga previa, la revisión diaria de cables y frenos, el uso durante el periodo y el desmontaje. Medido en superficie realmente ejecutada.":
    "Provision of a swing stage or suspended cradle for one-off work on a facade where erecting a tubular scaffold is not justified. Its safety depends entirely on the anchor points on the roof and on the mandatory use of a lifeline independent of the suspension equipment, a requirement that admits no exception. Includes the assessment and installation of the anchors, erection of the equipment, the proof load test beforehand, daily inspection of ropes and brakes, use over the period and dismantling. Measured by the area actually carried out.",

"Montaje, alquiler y desmontaje de andamio tubular de fachada con plataformas. Incluye el montaje, la permanencia y el desmontaje. Medido por metro cuadrado montado.":
    "Erection, hire and dismantling of a tubular facade scaffold with working platforms. Includes erection, hire and dismantling. Measured per square meter erected.",

"Montaje y uso de andamio colgante o silleta para trabajos en fachada. Incluye el montaje y la operación. Medido por metro cuadrado de fachada atendida.":
    "Erection and use of a swing stage for work on a facade. Includes erection and operation. Measured per square meter of facade reached.",

"Montaje y uso de andamio interior móvil o sobre borriquetas. Incluye el montaje y la operación. Medido por metro cuadrado de superficie atendida.":
    "Erection and use of a mobile or trestle scaffold indoors. Includes erection and operation. Measured per square meter of surface reached.",

"Montaje y uso de andamio de borriquetas para trabajos interiores. Incluye el montaje y la operación. Medido por metro cuadrado de superficie atendida.":
    "Erection and use of a trestle scaffold for indoor work. Includes erection and operation. Measured per square meter of surface reached.",

"Montaje de andamio de fachada con red de seguridad. Incluye el andamio y la red. Medido por metro cuadrado montado.":
    "Erection of a facade scaffold with safety netting. Includes the scaffold and the netting. Measured per square meter erected.",

"Montaje de andamio de fachada con malla de protección. Incluye el andamio y la malla. Medido por metro cuadrado montado.":
    "Erection of a facade scaffold with debris netting. Includes the scaffold and the netting. Measured per square meter erected.",

"Uso de plataforma elevadora móvil de tijera para trabajos en altura. Incluye la operación. Medido por metro cuadrado de superficie atendida.":
    "Use of a mobile scissor lift for work at height. Includes operation. Measured per square meter of surface reached.",

"Uso de plataforma elevadora articulada para trabajos en altura. Incluye la operación. Medido por metro cuadrado de superficie atendida.":
    "Use of an articulated boom lift for work at height. Includes operation. Measured per square meter of surface reached.",

"Colocación de escalera de acceso provisional a la zona de obra. Incluye el montaje de la escalera. Medido por metro lineal colocado.":
    "Installation of a temporary access ladder to the work area. Includes erection of the ladder. Measured per meter installed.",

"Ejecución de rampa provisional de acceso a la obra. Incluye la formación de la rampa. Medido por metro cuadrado ejecutado.":
    "Construction of a temporary access ramp to the site. Includes forming the ramp. Measured per square meter constructed.",

"Apeo provisional de losa mediante puntales metálicos telescópicos sobre durmientes de reparto en cabeza y base, para sostener la estructura mientras se ejecutan demoliciones, aperturas de hueco o refuerzos. Su ejecución debe responder a un cálculo o a la instrucción expresa del profesional responsable, que define la separación y la carga de los puntales. Incluye el replanteo de la retícula de apeo, la colocación de los durmientes, el montaje y puesta en carga de los puntales sin forzar la estructura, la verificación de la verticalidad y del apoyo, el mantenimiento y revisión durante los trabajos y el desapeo escalonado una vez alcanzada la resistencia prevista. Medido en superficie de losa realmente apeada.":
    "Temporary shoring of a slab with telescopic steel shores on spreader beams at head and base, to support the structure while demolition, openings or strengthening are carried out. It must be carried out to a calculation or to the express instruction of the responsible professional, who defines the spacing and the load on the shores. Includes field layout of the shoring grid, placing the spreader beams, erecting and loading the shores without forcing the structure, checking plumb and bearing, maintenance and inspection during the works, and the staged removal of the shoring once the specified strength has been reached. Measured by the area of slab actually shored.",

"Apeo provisional de viga mediante puntales metálicos telescópicos con durmiente de reparto en cabeza, dispuestos a ambos lados del elemento a intervenir. Debe responder a un cálculo o a la instrucción del profesional responsable. Incluye el replanteo de los puntos de apeo, la colocación de los durmientes, el montaje y puesta en carga progresiva de los puntales, la comprobación de que la carga se transmite a un apoyo con capacidad suficiente en el nivel inferior, la revisión durante los trabajos y el desapeo escalonado. Medido en longitud de viga realmente apeada.":
    "Temporary shoring of a beam with telescopic steel shores and a spreader beam at the head, placed on both sides of the element being worked on. It must be carried out to a calculation or to the instruction of the responsible professional. Includes field layout of the shoring points, placing the spreader beams, erecting and progressively loading the shores, checking that the load is transferred to a bearing of sufficient capacity at the level below, inspection during the works and the staged removal of the shoring. Measured by the length of beam actually shored.",
}
