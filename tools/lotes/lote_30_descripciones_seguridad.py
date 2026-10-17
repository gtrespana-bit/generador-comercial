# -*- coding: utf-8 -*-
"""Descripciones — Seguridad y salud en obra (capítulo completo, 60).

Criterios de este lote:
  · Una barandilla de obra son tres piezas con nombre fijo en inglés:
    top rail, mid rail y toe board. El español las llama pasamanos,
    barra intermedia y rodapié, y el rodapié de obra no es el zócalo de
    un acabado interior: su oficio es impedir que el material se caiga.
  · «Caída a distinto nivel» es fall from height, y la norma lo escribe
    así; no es fall to another level.
  · «Protección colectiva» es collective protective measure y la
    «individual» es PPE: el inglés de seguridad mantiene esa distinción
    en cada frase.
  · «Charla» es toolbox talk cuando es la reunión corta y periódica de
    obra, y safety induction cuando es la de entrada.
  · «Libro de incidencias» es incident log.
  · «Vida útil» de un arnés es service life, y caduca aunque parezca
    nuevo porque la cinta se degrada con el sol.
"""

LOTE = {
"Baranda provisional de protección en bordes de losa, huecos, escaleras y aberturas, con guardacuerpos, pasamanos, barra intermedia y rodapié. Es la protección colectiva que evita las caídas a distinto nivel, que son la primera causa de accidente grave en obra. Debe montarse antes de que exista el riesgo, no después. Incluye el montaje de los guardacuerpos con su fijación, la colocación de pasamanos, barra intermedia y rodapié que impide la caída de material, la revisión periódica del conjunto y su desmontaje cuando se coloque la protección definitiva. Medido en longitud realmente protegida.":
    "Temporary guardrail at the edges of slabs, openings, stairways and voids, with posts, a top rail, a mid rail and a toe board. It is the collective measure that prevents falls from height, the leading cause of serious accidents on site. It must be erected before the risk arises, not afterwards. Includes erecting the guardrail system with its fixings, installing the top rail, mid rail and toe board that stops material falling, periodic inspection of the assembly and its removal once the permanent protection is in place. Measured by the length actually protected.",

"Colocación de red de seguridad en huecos horizontales, patios y perímetros, con sus cuerdas de atado y anclajes. Actúa como protección secundaria cuando no es posible eliminar el riesgo de caída, y su eficacia depende por completo de la resistencia de los anclajes y de que la red no tenga aberturas ni deterioros. Incluye el replanteo de los puntos de anclaje, el montaje de la red con la cuerda perimetral atada en todos los puntos previstos, la revisión periódica y tras cualquier incidente, y el desmontaje. Medido en superficie de red realmente colocada.":
    "Installation of safety netting at horizontal openings, light wells and perimeters, with its tie cords and anchors. It acts as secondary protection where the risk of falling cannot be eliminated, and its effectiveness depends entirely on the strength of the anchors and on the net being free of openings and damage. Includes field layout of the anchor points, installation of the net with the perimeter rope tied at every point specified, periodic inspection and inspection after any incident, and dismantling. Measured by the area of netting actually installed.",

"Colocación de baranda de protección en el perímetro de la losa, con guardacuerpos y rodapié, para prevenir caídas.":
    "Installation of a guardrail around the perimeter of the slab, with posts and a toe board, to prevent falls.",

"Colocación de red de seguridad en hueco de escalera, con cuerdas de atado, para prevenir caídas.":
    "Installation of safety netting in a stairwell opening, with tie cords, to prevent falls.",

"Protección de hueco con tabla resistente y barandilla, señalizada, para prevenir caídas.":
    "Protection of an opening with a resistant board and a guardrail, signposted, to prevent falls.",

"Colocación de marquesina de protección sobre el acceso a la obra, para evitar caída de objetos.":
    "Installation of a protective canopy over the site access, to prevent falling objects.",

"Colocación de red vertical de protección en el borde de losa, con sus soportes.":
    "Installation of vertical safety netting at the edge of a slab, with its supports.",

"Cubrición de huecos de ascensor con tabla y barandilla, para prevenir caídas durante la obra.":
    "Covering of elevator shaft openings with boards and a guardrail, to prevent falls during the works.",

"Suministro de la dotación de equipo de protección individual para un trabajador: casco, botas de seguridad, guantes, lentes, protección auditiva y chaleco reflectante, con su reposición durante la obra. Incluye la entrega documentada de los equipos, que acredita el cumplimiento de la obligación del empleador, la verificación del estado y de la talla, la formación básica sobre su uso y la reposición de los elementos deteriorados a lo largo de la obra. Medido por dotación entregada.":
    "Supply of the set of personal protective equipment for one worker: hard hat, safety boots, gloves, safety glasses, hearing protection and high-visibility vest, with replacement during the works. Includes documented issue of the equipment, which evidences that the employer has met its duty, checking of condition and size, basic training in its use and replacement of damaged items through the works. Measured per set issued.",

"Dotación de casco de seguridad para el personal de obra, conforme a la normativa.":
    "Provision of hard hats for site personnel, in accordance with the regulations.",

"Dotación de guantes y calzado de seguridad para el personal, conforme a la tarea.":
    "Provision of gloves and safety footwear for personnel, appropriate to the task.",

"Dotación de protección ocular (gafas) y auditiva (tapones) para trabajos con riesgo.":
    "Provision of eye protection (goggles) and hearing protection (ear plugs) for work involving risk.",

"Dotación de mascarilla y protección respiratoria para trabajos con polvo o vapores.":
    "Provision of masks and respiratory protection for work with dust or vapours.",

"Dotación de chaleco reflectivo para el personal, para su visibilidad en la obra.":
    "Provision of high-visibility vests for personnel, so that they can be seen on site.",

"Dotación de arnés de seguridad de cuerpo completo para trabajos en altura.":
    "Provision of a full-body safety harness for work at height.",

"Reposición de los equipos de protección individual consumidos o dañados durante la obra.":
    "Replacement of personal protective equipment worn out or damaged during the works.",

"Suministro y colocación del conjunto de señalización de seguridad de la obra: señales de advertencia, obligación, prohibición y emergencia, cinta de delimitación y conos. Incluye el replanteo de la ubicación de cada señal en el punto donde el riesgo es real y visible antes de exponerse a él, la fijación de las señales, la delimitación de las zonas de riesgo y su mantenimiento y reposición durante la obra. Medido por conjunto de señalización instalado.":
    "Supply and installation of the set of safety signage for the site: warning, mandatory, prohibition and emergency signs, barrier tape and cones. Includes siting each sign at the point where the risk is real and visible before anyone is exposed to it, fixing the signs, delimiting the risk areas and maintaining and replacing them during the works. Measured per set of signage installed.",

"Delimitación y acordonamiento de zonas de riesgo dentro de la obra, mediante malla, cinta de peligro, conos o vallas, con su señalización. Incluye el replanteo del perímetro dejando una distancia de seguridad suficiente respecto al riesgo, el montaje de los soportes, el tendido de la malla o cinta, la colocación de la señalización correspondiente y el mantenimiento y reposición mientras dure el riesgo. Medido en longitud realmente delimitada.":
    "Delimitation and barring off of risk areas within the site, using mesh, hazard tape, cones or barriers, with signage. Includes setting out the perimeter leaving a sufficient safety distance from the hazard, erecting the supports, running out the mesh or tape, placing the corresponding signage and maintaining and replacing it for as long as the hazard remains. Measured by the length actually delimited.",

"Colocación de señalización de riesgos (caídas, golpes, electricidad) en la obra.":
    "Installation of hazard signage (falls, impact, electricity) on site.",

"Delimitación de zonas de riesgo con cinta de peligro y conos, para impedir el acceso.":
    "Delimitation of risk areas with hazard tape and cones, to prevent access.",

"Ejecución de cierre perimetral de la obra con malla de señalización, para control de accesos.":
    "Construction of the perimeter fence of the site with hazard netting, for access control.",

"Colocación de señalización de vías de evacuación y salidas de emergencia en la obra.":
    "Installation of signage for escape routes and emergency exits on site.",

"Habilitación de control de accesos a la obra, con registro de entrada del personal.":
    "Provision of access control to the site, with a register of personnel entering.",

"Colocación de iluminación de emergencia en las zonas de paso y evacuación de la obra.":
    "Installation of emergency lighting in the circulation and escape routes on site.",

"Instalación de línea de vida horizontal con sus anclajes extremos, tensor y absorbedor de energía, para el amarre de los arneses en trabajos en cubierta o en altura. Los anclajes extremos deben ir sobre elementos estructurales capaces de resistir la fuerza de una caída, que es muy superior al peso del trabajador: fijarlos a un elemento no estructural convierte el sistema en una falsa sensación de seguridad. Incluye el replanteo, la ejecución de los anclajes, el montaje y tensado de la línea, la comprobación del conjunto y su desmontaje. Medido en longitud de línea instalada.":
    "Installation of a horizontal lifeline with its end anchors, tensioner and shock absorber, for attaching harnesses during work on a roof or at height. The end anchors must be fixed to structural elements able to resist the force of a fall, which is far greater than the weight of the worker: fixing them to a non-structural element turns the system into a false sense of security. Includes setting out, installation of the anchors, erection and tensioning of the line, testing of the assembly and its removal. Measured by the length of lifeline installed.",

"Ejecución de punto de anclaje para línea de vida en cubierta, con fijación a la estructura.":
    "Installation of an anchor point for a lifeline on a roof, fixed to the structure.",

"Dotación de eslinga con absorbedor de energía para el amarre de arneses en trabajos en altura.":
    "Provision of a lanyard with shock absorber for attaching harnesses during work at height.",

"Montaje de andamio con barandilla de protección y rodapié, para trabajos en altura.":
    "Erection of a scaffold with a guardrail and toe board, for work at height.",

"Colocación de red de seguridad horizontal bajo cubierta, para amortiguar caídas.":
    "Installation of horizontal safety netting beneath a roof, to arrest falls.",

"Colocación de escalera de mano con fijación y estabilización, para trabajos puntuales en altura.":
    "Installation of a portable ladder, secured and stabilized, for one-off work at height.",

"Ejecución de punto de anclaje en fachada para trabajos verticales, con fijación a la estructura.":
    "Installation of an anchor point on a facade for vertical work, fixed to the structure.",

"Suministro del equipo de protección individual para trabajo en altura: arnés de cuerpo completo, eslinga con absorbedor de energía y conectores. Incluye la revisión del equipo antes de cada uso y la verificación de su fecha de caducidad, ya que las cintas y costuras se degradan con la radiación solar y el equipo tiene vida útil limitada aunque parezca intacto, la entrega documentada y la formación sobre los puntos de amarre válidos. Medido por equipo entregado.":
    "Supply of personal protective equipment for work at height: full-body harness, lanyard with shock absorber and connectors. Includes inspection of the equipment before each use and checking of its expiry date, since webbing and stitching degrade under solar radiation and the equipment has a limited service life even where it looks intact, documented issue and training in the valid anchor points. Measured per set issued.",

"Entibado de zanja con tablones y puntales, para prevenir desprendimientos durante la excavación.":
    "Trench sheeting with planks and struts, to prevent collapse during excavation.",

"Colocación de barandilla o señalización en el borde de la excavación, para prevenir caídas.":
    "Installation of a guardrail or signage at the edge of an excavation, to prevent falls.",

"Ventilación forzada de espacio confinado antes y durante el trabajo, para asegurar la calidad del aire.":
    "Forced ventilation of a confined space before and during the work, to ensure air quality.",

"Medición de la atmósfera de espacio confinado (oxígeno, gases), con detector, antes del acceso.":
    "Atmospheric testing of a confined space (oxygen, gases) with a detector before entry.",

"Señalización y balizamiento nocturno de zanja abierta, para prevenir accidentes de tránsito.":
    "Signage and night-time marking of an open trench, to prevent traffic accidents.",

"Colocación de escalera de acceso a la excavación, para evacuación segura del personal.":
    "Installation of an access ladder to the excavation, for the safe evacuation of personnel.",

"Suministro y colocación de extintor portátil en la obra, con su señalización.":
    "Supply and installation of a portable fire extinguisher on site, with its signage.",

"Suministro y colocación de extintor de CO2 junto al cuadro eléctrico de obra.":
    "Supply and installation of a CO2 fire extinguisher next to the site electrical panel.",

"Colocación de señalización de extintores y de los medios de extinción de la obra.":
    "Installation of signage for fire extinguishers and the site firefighting equipment.",

"Retirada de material combustible de las zonas de trabajo, para reducir el riesgo de incendio.":
    "Removal of combustible material from the work areas, to reduce the risk of fire.",

"Aplicación de tratamiento ignífugo sobre estructura de madera de obra, para mejorar su resistencia al fuego.":
    "Application of a fire-retardant treatment to a wood structure on site, to improve its fire resistance.",

"Protección contra incendios en trabajos de oxicorte y soldadura, con pantalla y extintor próximo.":
    "Fire protection for oxy-fuel cutting and welding work, with a screen and a fire extinguisher to hand.",

"Habilitación y mantenimiento de la zona de vestuario y comedor del personal de obra, con su mobiliario básico, durante un mes. Incluye la adecuación del espacio, la dotación de mesa, asientos, taquillas o perchas y punto de agua potable, la limpieza periódica y el mantenimiento del orden. Medido por mes de permanencia.":
    "Provision and maintenance of the changing and canteen area for site personnel, with its basic furniture, for one month. Includes fitting out the space, providing a table, seating, lockers or coat hooks and a drinking water point, periodic cleaning and keeping the area tidy. Measured per month provided.",

"Suministro y colocación del botiquín de primeros auxilios de obra, dotado y con reposición durante la ejecución. Incluye la colocación en punto visible, accesible y conocido por todo el personal, la revisión periódica del contenido y de las fechas de caducidad, la reposición de lo consumido y la señalización de su ubicación junto con los teléfonos de emergencia. Medido por botiquín instalado y mantenido.":
    "Supply and installation of the site first aid kit, stocked and replenished during the works. Includes siting it in a visible and accessible place known to all personnel, periodic checking of the contents and expiry dates, replacement of what has been used and signage of its location together with the emergency telephone numbers. Measured per first aid kit installed and maintained.",

"Adecuación de zona de vestuario y comedor de obra, con mobiliario y servicios básicos.":
    "Fitting out of a site changing and canteen area, with furniture and basic services.",

"Alquiler mensual de baño químico portátil, con su mantenimiento y limpieza.":
    "Monthly hire of a portable chemical toilet, including its maintenance and cleaning.",

"Suministro de agua potable para el personal de obra, conforme a la normativa de higiene.":
    "Supply of drinking water for site personnel, in accordance with hygiene regulations.",

"Suministro y dotación de botiquín de primeros auxilios de obra, con su reposición.":
    "Supply and stocking of a site first aid kit, with its replenishment.",

"Reposición del material consumido del botiquín de primeros auxilios durante la obra.":
    "Replenishment of the contents used from the first aid kit during the works.",

"Suministro de camilla de evacuación para la obra, con su ubicación señalizada.":
    "Supply of an evacuation stretcher for the site, with its location signposted.",

"Realización de la charla de inducción en seguridad al personal de obra y de las charlas periódicas durante la ejecución, con su registro de asistencia. El registro firmado es lo que acredita que el trabajador fue informado de los riesgos de su puesto, documento que resulta determinante ante cualquier incidente. Incluye la preparación del contenido según los riesgos reales de la obra, la impartición de la charla inicial y de las periódicas, la entrega de las instrucciones de trabajo seguro y el registro documentado de asistencia. Medido por conjunto de charlas de la obra.":
    "Delivery of the safety induction to site personnel and of the periodic toolbox talks during the works, with an attendance register. The signed register is what evidences that the worker was informed of the risks of his job, a document that proves decisive in the event of any incident. Includes preparation of the content around the real risks of the site, delivery of the initial induction and of the periodic talks, issue of the safe working instructions and the documented attendance record. Measured per set of talks for the site.",

"Elaboración y mantenimiento del plan de seguridad de la obra y de su documentación asociada, con la identificación de riesgos, las medidas preventivas y el registro de las actuaciones. Incluye la redacción del plan adaptado a la obra concreta y no un modelo genérico, la identificación de los riesgos por fase y por tarea, la definición de las protecciones colectivas e individuales, la relación de teléfonos de emergencia y centro asistencial más próximo, el libro de incidencias y la actualización del plan cuando cambien las condiciones de la obra. Medido por plan elaborado y mantenido.":
    "Preparation and maintenance of the site health and safety plan and its associated documentation, with the identification of hazards, the preventive measures and the record of actions taken. Includes writing a plan tailored to the specific site and not a generic template, identifying hazards by phase and by task, defining the collective and personal protective measures, listing the emergency telephone numbers and nearest medical center, keeping an incident log and updating the plan whenever site conditions change. Measured per plan prepared and maintained.",

"Impartición de charla de inducción en seguridad al personal que ingresa a la obra.":
    "Delivery of the safety induction to personnel entering the site.",

"Formación específica al personal para trabajos en altura, con prácticas de uso de EPI.":
    "Specific training for personnel in work at height, with practical use of PPE.",

"Formación al personal en el manejo seguro de equipos y herramientas de obra.":
    "Training for personnel in the safe use of site equipment and tools.",

"Elaboración del plan de seguridad y salud de la obra, con evaluación de riesgos.":
    "Preparation of the health and safety plan for the site, with a risk assessment.",

"Elaboración de la documentación preventiva y registros de seguridad de la obra.":
    "Preparation of the preventive documentation and safety records for the site.",

"Inspección de seguridad periódica de la obra, con emisión de informe de observaciones.":
    "Periodic safety inspection of the site, with the issue of a report of findings.",
}
