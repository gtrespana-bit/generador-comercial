# -*- coding: utf-8 -*-
"""Descripciones — Acondicionamiento del terreno (capítulo completo, 80).

Criterios de este lote:
  · «Desbroce» es clearing and grubbing en Estados Unidos y site clearance
    en el Reino Unido, y el «descapote» es stripping: retirar el topsoil
    y apartarlo porque se reutiliza.
  · «Refine» es fine grading en Estados Unidos y trimming en el Reino
    Unido: el último repaso que da la cota exacta y la máquina no hace.
  · «Tongada» es layer. «Plancha vibratoria» es plate compactor y
    «compactador de impacto» es rammer.
  · «Humedad óptima» es optimum moisture content y «humectación» es
    moisture conditioning: el relleno se compacta a una humedad, no en
    seco.
  · «Escombro» es debris y «tierra» de excavación es spoil: en inglés no
    son la misma palabra y el precio tampoco.
  · «Volqueta» es dump truck y tipper lorry. «Escombro esponjado» es
    bulked debris.
  · «Acuñado» de una base de piedra es blinding with fine material: se
    cierra la superficie con fino para que la piedra no se mueva.
"""

LOTE = {
# ── Limpieza y desbroce ───────────────────────────────────────────────────
"Limpieza y desbroce manual del terreno, con retiro de maleza, hierba, arbustos y basura acumulada, hasta dejar la superficie despejada para el replanteo. Se emplea en parcelas pequeñas o de acceso restringido donde no entra maquinaria. Incluye el corte de la vegetación con desbrozadora, el arranque manual de raíces superficiales, el recogido y ensacado de los residuos, su traslado al punto de acopio y el barrido final de la superficie. No incluye el transporte del material sobrante a botadero, que se valora en el subcapítulo de transporte de tierras. Medido en superficie realmente desbrozada.":
    "Manual clearing and grubbing of the site, with removal of undergrowth, grass, shrubs and accumulated rubbish, leaving the surface clear for setting out. It is used on small plots or where access is restricted and plant cannot get in. Includes cutting the vegetation with a brush cutter, hand grubbing out surface roots, collecting and bagging the waste, moving it to the stockpile and a final sweep of the surface. It does not include cartage of the surplus material to a spoil site, which is priced in the earthworks haulage subsection. Measured by the area actually cleared.",

"Limpieza y desbroce mecanizado del terreno mediante retroexcavadora o minicargadora, con retiro de maleza, arbustos, raíces y escombro superficial, hasta dejar la superficie despejada y groseramente nivelada. Rinde frente al desbroce manual a partir de superficies medianas y con acceso para maquinaria. Incluye el acordonamiento de la zona de trabajo, el barrido mecánico de la superficie, el amontonamiento del material retirado en el punto de acopio y el repaso manual de los bordes y esquinas donde no alcanza la máquina. No incluye el transporte del material sobrante a botadero, que se valora en el subcapítulo de transporte de tierras. Medido en superficie realmente desbrozada.":
    "Mechanical clearing and grubbing of the site with a backhoe or skid steer loader, with removal of undergrowth, shrubs, roots and surface debris, leaving the surface clear and roughly leveled. It pays off against hand clearing from medium areas upwards and where plant can get in. Includes barring off the working area, mechanical sweeping of the surface, heaping the material removed at the stockpile and hand trimming of the edges and corners the machine cannot reach. It does not include cartage of the surplus material to a spoil site, which is priced in the earthworks haulage subsection. Measured by the area actually cleared.",

"Descapote del terreno mediante retiro de la capa vegetal superficial, de unos 20 cm de espesor medio, hasta alcanzar el terreno firme apto para recibir fundaciones o rellenos. La capa vegetal es compresible y no admite carga, de modo que su retiro es condición previa a cualquier cimentación. Incluye el replanteo del área, la excavación de la capa con medios mecánicos o manuales según el acceso, su amontonamiento separado del resto del material por si el cliente desea reutilizarla en jardinería, y el perfilado de la superficie resultante. No incluye el transporte del material sobrante a botadero, que se valora en el subcapítulo de transporte de tierras. Medido en superficie realmente descapotada.":
    "Stripping of the site by removing the surface layer of topsoil, some 20 cm average thickness, down to firm ground suitable to receive foundations or fill. Topsoil is compressible and will not carry load, so removing it is a precondition of any foundation. Includes setting out the area, excavating the layer by mechanical or manual means depending on access, heaping it separately from the rest of the material in case the client wants to reuse it for landscaping, and trimming the resulting surface. It does not include cartage of the surplus material to a spoil site, which is priced in the earthworks haulage subsection. Measured by the area actually stripped.",

"Retiro de raíces, restos de fundaciones antiguas, tuberías fuera de servicio y demás obstáculos menores que aparecen enterrados al despejar el terreno. Incluye la localización y descubrimiento del obstáculo, su extracción con medios manuales o con retroexcavadora según el tamaño, el corte con motosierra o amoladora cuando sea necesario fragmentarlo, el relleno y compactación del hueco resultante con material del sitio y la separación del material extraído según sea escombro, chatarra o vegetal. No incluye el transporte del material sobrante a botadero, que se valora en el subcapítulo de transporte de tierras. Medido en superficie de terreno realmente sondeada y liberada de obstáculos.":
    "Removal of roots, remains of old foundations, disused pipework and other minor obstructions found buried when the site is cleared. Includes locating and exposing the obstruction, extracting it by hand or with a backhoe depending on size, cutting it with a chainsaw or angle grinder where it has to be broken up, backfilling and compacting the resulting void with material from the site, and separating the material removed as debris, scrap or green waste. It does not include cartage of the surplus material to a spoil site, which is priced in the earthworks haulage subsection. Measured by the area of ground actually probed and cleared of obstructions.",

"Desbroce de vegetación arbustiva y maleza del terreno. Incluye la tala de arbustos y la limpieza. Medido por metro cuadrado desbrozado.":
    "Clearing and grubbing of scrub vegetation and undergrowth from the site. Includes cutting back the shrubs and clearing. Measured per square meter cleared.",

"Desbroce con retiro de capa vegetal y raíces superficiales. Incluye la limpieza y el acopio. Medido por metro cuadrado desbrozado.":
    "Clearing and grubbing, including removal of topsoil and surface roots. Includes clearing and stockpiling. Measured per square meter cleared.",

"Retiro de obstáculos, escombros y basura superficial del terreno. Incluye la limpieza y el acopio. Medido por metro cuadrado limpiado.":
    "Removal of obstructions, debris and surface rubbish from the site. Includes clearing and stockpiling. Measured per square meter cleared.",

"Limpieza y desbroce de terreno en pendiente. Incluye la limpieza manual y mecanizada. Medido por metro cuadrado limpiado.":
    "Clearing and grubbing of sloping ground. Includes clearing by hand and by machine. Measured per square meter cleared.",

"Retiro de tocones y raíces de árboles talados. Incluye la extracción y la limpieza. Medido por unidad retirada.":
    "Removal of stumps and roots of felled trees. Includes extraction and clearing. Measured per unit removed.",

"Descapote y retiro de capa vegetal con control topográfico. Incluye el descapote y el nivelado. Medido por metro cuadrado descapotado.":
    "Stripping and removal of topsoil with survey control. Includes stripping and leveling. Measured per square meter stripped.",

"Limpieza de terreno con restos de demolición. Incluye la retirada y el acopio. Medido por metro cuadrado limpiado.":
    "Clearing of a site with demolition debris. Includes removal and stockpiling. Measured per square meter cleared.",

"Retiro de grama o pavimento vegetal superficial. Incluye el corte y la retirada. Medido por metro cuadrado retirado.":
    "Removal of the surface grass or vegetative cover. Includes cutting and removal. Measured per square meter removed.",

"Limpieza de terreno con maleza alta y vegetación densa. Incluye la limpieza mecanizada. Medido por metro cuadrado limpiado.":
    "Clearing of a site with tall undergrowth and dense vegetation. Includes mechanical clearing. Measured per square meter cleared.",

"Retiro de capa de asfalto superficial del terreno. Incluye el levantado y la retirada. Medido por metro cuadrado retirado.":
    "Removal of a surface layer of asphalt from the site. Includes lifting and removal. Measured per square meter removed.",

# ── Excavación ────────────────────────────────────────────────────────────
"Excavación mecanizada a cielo abierto para vaciado general, rebaje de cota o formación de plataforma, mediante retroexcavadora o minicargadora, en terreno de consistencia media. Incluye el replanteo y marcado de la cota final, la excavación por tongadas, el acopio del material en obra o su carga directa sobre camión, el refine manual de los bordes y taludes, y el control topográfico de la cota alcanzada. No incluye el transporte del material sobrante a botadero, que se valora en el subcapítulo de transporte de tierras. Medido en volumen teórico de excavación según las cotas de proyecto.":
    "Mechanical open-cut excavation for general bulk excavation, reducing levels or forming a platform, with a backhoe or skid steer loader, in ground of medium consistency. Includes setting out and marking the final level, excavating in layers, stockpiling the material on site or loading it directly onto a truck, hand trimming of the edges and slopes, and survey control of the level achieved. It does not include cartage of the surplus material to a spoil site, which is priced in the earthworks haulage subsection. Measured by the theoretical volume of excavation to the design levels.",

"Excavación en terreno de alta compacidad, material cementado o roca, mediante martillo hidráulico montado sobre retroexcavadora, con apoyo de martillo neumático manual en los rincones. Se aplica cuando el rendimiento de la excavación convencional cae por debajo de lo aceptable, circunstancia que debe dejarse acreditada en obra para justificar el cambio de partida. Incluye el fracturado del material, su extracción y acopio, el refine de paredes y fondo, y el control de las vibraciones cuando existan edificaciones colindantes. No incluye el transporte del material sobrante a botadero, que se valora en el subcapítulo de transporte de tierras. Medido en volumen teórico de excavación según las dimensiones de proyecto.":
    "Excavation in ground of high compaction, cemented material or rock, with a hydraulic breaker mounted on a backhoe, with a hand-held pneumatic breaker for the corners. It applies where the output of conventional excavation falls below what is acceptable, a circumstance that must be recorded on site to justify the change of item. Includes breaking up the material, extracting and stockpiling it, trimming the sides and bottom, and controlling vibration where there are adjoining buildings. It does not include cartage of the surplus material to a spoil site, which is priced in the earthworks haulage subsection. Measured by the theoretical volume of excavation to the design dimensions.",

"Excavación para el alojamiento de tanque séptico, sumidero, tanque de agua enterrado o similar, con las dimensiones de proyecto más el sobreancho de trabajo necesario para el montaje y el posterior relleno perimetral. Incluye el replanteo, la excavación con medios mecánicos y refine manual, el perfilado del fondo a la cota exacta de apoyo, la comprobación de la estabilidad de las paredes y su entibado si la profundidad lo exige, y la señalización y cubrición del hueco mientras permanezca abierto. No incluye el transporte del material sobrante a botadero, que se valora en el subcapítulo de transporte de tierras. Medido en volumen teórico de excavación según las dimensiones de proyecto.":
    "Excavation to receive a septic tank, catch basin, buried water tank or similar, to the design dimensions plus the working space needed for installation and subsequent backfilling around it. Includes setting out, excavation by mechanical means with hand trimming, trimming the bottom to the exact bearing level, checking the stability of the sides and sheeting them where the depth requires it, and signing and covering the void while it remains open. It does not include cartage of the surplus material to a spoil site, which is priced in the earthworks haulage subsection. Measured by the theoretical volume of excavation to the design dimensions.",

"Perfilado, refine y compactación del fondo de la excavación hasta dejarlo a la cota exacta, plano y con la densidad requerida para recibir la fundación o la base del pavimento. Incluye la retirada del material suelto y descomprimido del fondo, el refine manual hasta la cota de proyecto, la humectación del terreno hasta la humedad óptima y la compactación con plancha vibratoria o compactador de impacto según el ancho disponible. Medido en superficie de fondo realmente perfilada.":
    "Trimming, fine grading and compaction of the bottom of the excavation, leaving it at the exact level, flat and with the density required to receive the foundation or the base of the paving. Includes removal of loose and disturbed material from the bottom, hand trimming to the design level, moisture conditioning of the ground to optimum moisture content and compaction with a plate compactor or rammer depending on the width available. Measured by the area of the bottom actually trimmed.",

"Agotamiento del agua acumulada en la excavación mediante bomba sumergible con manguera de descarga a punto autorizado, para permitir el trabajo en seco. Se aplica cuando aparece nivel freático, filtraciones o agua de lluvia acumulada. Incluye el emplazamiento de la bomba en el punto bajo, el tendido de la manguera de descarga a un punto donde el vertido no erosione ni inunde otras zonas, la vigilancia del funcionamiento, la limpieza periódica del filtro de aspiración y el retiro del equipo. Medido por hora de funcionamiento efectivo del equipo.":
    "Dewatering of water accumulated in the excavation with a submersible pump and discharge hose to an authorized point, to allow the work to be carried out in the dry. It applies where groundwater, seepage or accumulated rainwater is encountered. Includes siting the pump at the low point, running the discharge hose to a point where the discharge will neither erode nor flood other areas, monitoring the operation, periodic cleaning of the suction strainer and removal of the equipment. Measured per hour of actual operation of the equipment.",

"Excavación manual en el interior de una edificación existente, para rebaje de cota, ejecución de fundaciones de refuerzo o paso de instalaciones enterradas. El rendimiento es muy inferior al de una excavación a cielo abierto por la falta de espacio de maniobra, la imposibilidad de usar maquinaria y la obligación de evacuar el material a mano por el interior del inmueble. Incluye el replanteo, la protección de los ambientes de paso, la excavación por capas con pico y pala, el ensacado del material y su traslado hasta el punto de acopio exterior. No incluye el bote.":
    "Hand excavation inside an existing building, for reducing levels, constructing strengthening foundations or running buried services. Output is far lower than for open-cut excavation because of the lack of room to manoeuvre, the impossibility of using plant and the need to carry the material out by hand through the building. Includes setting out, protecting the circulation areas, excavating in layers with pick and shovel, bagging the material and carrying it to the external stockpile. Disposal is not included.",

"Excavación mecanizada a cielo abierto en terreno blando. Incluye la excavación y el acopio. Medido por metro cúbico excavado.":
    "Mechanical open-cut excavation in soft ground. Includes excavation and stockpiling. Measured per cubic meter excavated.",

"Excavación mecanizada a cielo abierto en terreno duro. Incluye la excavación y el acopio. Medido por metro cúbico excavado.":
    "Mechanical open-cut excavation in hard ground. Includes excavation and stockpiling. Measured per cubic meter excavated.",

"Excavación a cielo abierto con formación de taludes. Incluye la excavación y el perfilado. Medido por metro cúbico excavado.":
    "Open-cut excavation with the formation of battered sides. Includes excavation and trimming. Measured per cubic meter excavated.",

"Perfilado y limpieza manual del fondo de excavación. Incluye la limpieza y el perfilado. Medido por metro cuadrado perfilado.":
    "Hand trimming and cleaning of the bottom of an excavation. Includes cleaning and trimming. Measured per square meter trimmed.",

"Excavación para cimientos de edificación. Incluye la excavación y el acopio. Medido por metro cúbico excavado.":
    "Excavation for the footings of a building. Includes excavation and stockpiling. Measured per cubic meter excavated.",

"Excavación para piscina o tanque enterrado. Incluye la excavación y el acopio. Medido por metro cúbico excavado.":
    "Excavation for a swimming pool or buried tank. Includes excavation and stockpiling. Measured per cubic meter excavated.",

"Excavación de sótano, con retirada de tierras. Incluye la excavación y el acopio. Medido por metro cúbico excavado.":
    "Excavation for a basement, including removal of the spoil. Includes excavation and stockpiling. Measured per cubic meter excavated.",

"Excavación en terreno con presencia de agua, con achique. Incluye la excavación y el achique. Medido por metro cúbico excavado.":
    "Excavation in water-bearing ground, including dewatering. Includes excavation and dewatering. Measured per cubic meter excavated.",

"Excavación de explanada para nivelación del terreno. Incluye la excavación y el acopio. Medido por metro cúbico excavado.":
    "Excavation to formation level for leveling the site. Includes excavation and stockpiling. Measured per cubic meter excavated.",

"Excavación mecanizada a cielo abierto con retiro lateral del material. Incluye la excavación y el acopio del material retirado. Medido por metro cúbico excavado.":
    "Mechanical open-cut excavation with the material cast to one side. Includes excavation and stockpiling of the material removed. Measured per cubic meter excavated.",

# ── Zanjas ────────────────────────────────────────────────────────────────
"Excavación manual en zanja o pozo para fundaciones, en terreno de consistencia media, hasta la cota y con las dimensiones de proyecto. Es la solución habitual en obra de reforma y en ampliaciones donde no hay acceso para maquinaria o el volumen no la justifica. Incluye el replanteo de la zanja, la excavación con pico y pala por capas, el acopio del material a distancia suficiente del borde para no sobrecargarlo, el perfilado de paredes y fondo, y la extracción del material hasta el punto de carga. No incluye el transporte del material sobrante a botadero, que se valora en el subcapítulo de transporte de tierras. Medido en volumen teórico de excavación según las dimensiones de proyecto.":
    "Hand excavation of a trench or pit for foundations, in ground of medium consistency, to the level and to the design dimensions. It is the usual solution on refurbishment work and extensions where plant cannot get in or the volume does not justify it. Includes setting out the trench, excavating in layers with pick and shovel, stockpiling the material far enough back from the edge not to overload it, trimming the sides and bottom, and getting the material out to the loading point. It does not include cartage of the surplus material to a spoil site, which is priced in the earthworks haulage subsection. Measured by the theoretical volume of excavation to the design dimensions.",

"Excavación mecanizada en zanja o pozo para fundaciones mediante retroexcavadora, en terreno de consistencia media, hasta la cota y con las dimensiones de proyecto. Incluye el replanteo, la excavación con la máquina, el acopio del material a distancia suficiente del borde, el refine manual de paredes y fondo que la máquina no puede dar, y la vigilancia durante la excavación para detener los trabajos si aparecen instalaciones enterradas no previstas. No incluye el transporte del material sobrante a botadero, que se valora en el subcapítulo de transporte de tierras. Medido en volumen teórico de excavación según las dimensiones de proyecto.":
    "Mechanical excavation of a trench or pit for foundations with a backhoe, in ground of medium consistency, to the level and to the design dimensions. Includes setting out, excavation by machine, stockpiling the material far enough back from the edge, hand trimming of the sides and bottom that the machine cannot achieve, and watching during excavation so that work stops if unforeseen buried services are found. It does not include cartage of the surplus material to a spoil site, which is priced in the earthworks haulage subsection. Measured by the theoretical volume of excavation to the design dimensions.",

"Excavación manual en zanja de sección reducida para el tendido de tuberías de agua, desagüe o canalizaciones eléctricas enterradas, con la pendiente que exija la instalación. Se ejecuta a mano precisamente porque en zonas construidas el riesgo de romper una instalación existente hace desaconsejable la máquina. Incluye el replanteo del trazado, la excavación por capas con vigilancia continua, el acopio del material junto a la zanja, el perfilado del fondo con la pendiente requerida y el mantenimiento de la zanja señalizada mientras permanezca abierta. No incluye el transporte del material sobrante a botadero, que se valora en el subcapítulo de transporte de tierras. Medido en volumen teórico de excavación según las dimensiones de proyecto.":
    "Hand excavation of a narrow trench for laying water pipes, drains or buried electrical conduits, to the fall required by the service. It is done by hand precisely because in built-up areas the risk of striking an existing service makes the machine inadvisable. Includes setting out the line, excavating in layers under continuous watch, stockpiling the material alongside the trench, trimming the bottom to the required fall and keeping the trench signed while it remains open. It does not include cartage of the surplus material to a spoil site, which is priced in the earthworks haulage subsection. Measured by the theoretical volume of excavation to the design dimensions.",

"Entibado de las paredes de zanja mediante tablones y puntales de madera, para sostener el terreno y permitir el trabajo seguro en el interior. Es obligatorio a partir de la profundidad en que el terreno deja de ser autoestable, y su ausencia es la causa principal de los accidentes graves en zanja. Incluye el montaje del entibado conforme avanza la excavación y nunca después, la colocación de tablones y puntales con el apriete necesario, la revisión diaria del conjunto y tras cada lluvia, y el desmontaje escalonado a medida que se ejecuta el relleno. Medido en superficie de pared de zanja realmente entibada.":
    "Trench sheeting to the sides of the excavation with lumber planks and struts, to support the ground and allow safe work inside. It is mandatory from the depth at which the ground stops being self-supporting, and its absence is the main cause of serious accidents in trenches. Includes installing the sheeting as the excavation advances and never afterwards, placing the planks and struts with the wedging required, daily inspection of the assembly and after every rainfall, and staged removal as the backfill proceeds. Measured by the area of trench face actually sheeted.",

"Excavación de pozo para fundación aislada. Incluye la excavación y el acopio. Medido por metro cúbico excavado.":
    "Excavation of a pit for a pad foundation. Includes excavation and stockpiling. Measured per cubic meter excavated.",

"Excavación de zanja con entibado de madera. Incluye la excavación y el entibado. Medido por metro cúbico excavado.":
    "Excavation of a trench with lumber sheeting. Includes excavation and sheeting. Measured per cubic meter excavated.",

"Excavación de zanja para tubería de drenaje. Incluye la excavación y el perfilado. Medido por metro lineal excavado.":
    "Excavation of a trench for a drainage pipe. Includes excavation and trimming. Measured per meter excavated.",

"Excavación de zanja para tubería de agua. Incluye la excavación y el perfilado. Medido por metro lineal excavado.":
    "Excavation of a trench for a water pipe. Includes excavation and trimming. Measured per meter excavated.",

"Excavación de zanja para canalización eléctrica. Incluye la excavación y el perfilado. Medido por metro lineal excavado.":
    "Excavation of a trench for an electrical conduit. Includes excavation and trimming. Measured per meter excavated.",

"Excavación localizada a mano en interior. Incluye la excavación y la retirada. Medido por metro cúbico excavado.":
    "Localized hand excavation indoors. Includes excavation and removal. Measured per cubic meter excavated.",

"Excavación de zanja para cable de datos o telecomunicaciones. Incluye la excavación. Medido por metro lineal excavado.":
    "Excavation of a trench for a data or telecommunications cable. Includes excavation. Measured per meter excavated.",

"Excavación de zanja para tubería de gas. Incluye la excavación y el perfilado. Medido por metro lineal excavado.":
    "Excavation of a trench for a gas pipe. Includes excavation and trimming. Measured per meter excavated.",

"Excavación de registro o tanquilla enterrada. Incluye la excavación y el acopio. Medido por unidad excavada.":
    "Excavation for a buried inspection chamber. Includes excavation and stockpiling. Measured per unit excavated.",

"Excavación de zanja para fundación corrida. Incluye la excavación y el perfilado. Medido por metro lineal excavado.":
    "Excavation of a trench for a strip footing. Includes excavation and trimming. Measured per meter excavated.",

# ── Rellenos y bases ──────────────────────────────────────────────────────
"Relleno de zanjas, trasdós de muros o rebajes con el propio material procedente de la excavación, siempre que sea apto por no contener materia orgánica ni elementos compresibles, extendido y compactado en capas de 20 cm de espesor máximo. Incluye la selección y cribado grosero del material acopiado, su extendido por tongadas, la humectación hasta la humedad óptima, la compactación de cada capa con compactador de impacto o plancha vibratoria según el espacio, y la comprobación del nivel final. Medido en volumen de relleno compactado según las dimensiones de proyecto.":
    "Backfill to trenches, behind walls or to reduced levels with the material arising from the excavation itself, provided it is suitable through containing no organic matter or compressible elements, spread and compacted in layers not exceeding 20 cm. Includes selecting and rough screening the stockpiled material, spreading it in layers, moisture conditioning to optimum moisture content, compacting each layer with a rammer or plate compactor depending on the space, and checking the final level. Measured by the volume of compacted fill to the design dimensions.",

"Relleno con material granular seleccionado de préstamo, tipo granzón natural, extendido y compactado en capas de 20 cm de espesor máximo, empleado cuando el material del sitio no reúne las condiciones exigidas. Incluye el suministro y puesta en obra del material, su extendido por tongadas, la humectación hasta la humedad óptima, la compactación de cada capa hasta alcanzar la densidad especificada y el control del nivel final. Medido en volumen de relleno compactado según las dimensiones de proyecto.":
    "Backfill with selected imported granular fill, such as natural run of crusher, spread and compacted in layers not exceeding 20 cm, used where the material on site does not meet the requirements. Includes supply and placing of the material, spreading it in layers, moisture conditioning to optimum moisture content, compacting each layer to the specified density and checking the final level. Measured by the volume of compacted fill to the design dimensions.",

"Relleno de zanja de instalaciones con arena lavada, formando la cama de asiento bajo la tubería y el recubrimiento envolvente hasta 20 cm por encima de su generatriz superior, para protegerla de cargas puntuales y del contacto con material grueso. Incluye el suministro y puesta en obra de la arena, la formación de la cama con la pendiente de la instalación, el relleno lateral y superior por capas con compactación manual cuidadosa para no desplazar ni dañar la tubería, y la colocación de la cinta de señalización sobre el recubrimiento. Medido en volumen de arena realmente colocada.":
    "Backfill of a services trench with washed sand, forming the bedding beneath the pipe and the surround up to 20 cm above its crown, to protect it from point loads and from contact with coarse material. Includes supply and placing of the sand, forming the bed to the fall of the service, filling the sides and over the top in layers with careful hand compaction so as not to displace or damage the pipe, and laying warning tape over the surround. Measured by the volume of sand actually placed.",

"Base de piedra picada extendida y compactada bajo pisos, aceras o pavimentos exteriores, con función de capa drenante y de reparto de cargas, y de rotura del ascenso capilar de humedad hacia el piso. Incluye el suministro y puesta en obra de la piedra, su extendido por tongadas de 15 cm, el acuñado con material fino cuando se requiera cerrar la superficie, la compactación con plancha vibratoria y la comprobación del nivel y la planitud finales. Medido en volumen de base compactada según las dimensiones de proyecto.":
    "Crushed stone base spread and compacted beneath floors, sidewalks or external paving, acting as a drainage and load spreading layer and breaking the capillary rise of moisture into the floor. Includes supply and placing of the stone, spreading it in 15 cm layers, blinding with fine material where the surface has to be closed, compaction with a plate compactor and checking the final level and regularity. Measured by the volume of compacted base to the design dimensions.",

"Nivelación y compactación de la superficie del terreno tras el desbroce o el relleno, hasta dejarla a la cota y con la pendiente de proyecto y con la densidad necesaria para recibir la capa siguiente. Incluye el repaso de la superficie con retirada de los puntos altos y aporte en los bajos, la humectación hasta la humedad óptima, la compactación con plancha vibratoria en pasadas cruzadas y la comprobación de cotas y pendientes con nivel láser. Medido en superficie realmente nivelada y compactada.":
    "Leveling and compaction of the surface of the ground after clearing or filling, leaving it at the level and fall of the design and with the density needed to receive the next layer. Includes going over the surface, cutting off the high spots and making up the low ones, moisture conditioning to optimum moisture content, compaction with a plate compactor in crossed passes and checking levels and falls with a laser level. Measured by the area actually leveled and compacted.",

"Relleno compactado en capas con material del sitio. Incluye la extensión y la compactación por capas. Medido por metro cúbico rellenado.":
    "Backfill compacted in layers with material from the site. Includes spreading and compaction in layers. Measured per cubic meter filled.",

"Relleno con material granular de préstamo. Incluye la extensión y la compactación. Medido por metro cúbico rellenado.":
    "Backfill with imported granular fill. Includes spreading and compaction. Measured per cubic meter filled.",

"Base de piedra picada compactada para pavimento. Incluye la extensión y la compactación. Medido por metro cuadrado ejecutado.":
    "Compacted crushed stone base for paving. Includes spreading and compaction. Measured per square meter constructed.",

"Base de arena compactada bajo pavimento. Incluye la extensión y la compactación. Medido por metro cuadrado ejecutado.":
    "Compacted sand base beneath paving. Includes spreading and compaction. Measured per square meter constructed.",

"Nivelación y compactación de subrasante. Incluye la nivelación y la compactación. Medido por metro cuadrado ejecutado.":
    "Leveling and compaction of the subgrade. Includes leveling and compaction. Measured per square meter constructed.",

"Relleno de zanja de instalaciones con arena. Incluye la extensión y la compactación. Medido por metro cúbico rellenado.":
    "Backfill of a services trench with sand. Includes spreading and compaction. Measured per cubic meter filled.",

"Relleno con material de excavación reutilizado, previo cribado. Incluye la extensión y la compactación. Medido por metro cúbico rellenado.":
    "Backfill with reused excavated material, after screening. Includes spreading and compaction. Measured per cubic meter filled.",

"Compactación de terraplén con plancha vibratoria. Incluye la compactación por capas. Medido por metro cuadrado compactado.":
    "Compaction of an embankment with a plate compactor. Includes compaction in layers. Measured per square meter compacted.",

"Relleno estructural con piedra picada compactada. Incluye la extensión y la compactación. Medido por metro cúbico rellenado.":
    "Structural backfill with compacted crushed stone. Includes spreading and compaction. Measured per cubic meter filled.",

# ── Agua y estabilización ─────────────────────────────────────────────────
"Achique de agua en excavación con bomba sumergible. Incluye la colocación de la bomba y el achique. Medido por metro cúbico achicado.":
    "Dewatering of an excavation with a submersible pump. Includes placing the pump and dewatering. Measured per cubic meter pumped out.",

"Drenaje provisional con tubería perforada. Incluye la colocación de la tubería. Medido por metro lineal ejecutado.":
    "Temporary drainage with perforated pipe. Includes laying the pipe. Measured per meter constructed.",

"Ejecución de cuneta provisional de desvío de aguas. Incluye la excavación de la cuneta. Medido por metro lineal ejecutado.":
    "Construction of a temporary intercepting ditch to divert water. Includes excavation of the ditch. Measured per meter constructed.",

"Estabilización de fondo de excavación con capa de piedra. Incluye la colocación y la compactación. Medido por metro cuadrado estabilizado.":
    "Stabilization of the bottom of an excavation with a layer of stone. Includes placing and compaction. Measured per square meter stabilized.",

"Protección de talud con geotextil. Incluye la colocación del geotextil. Medido por metro cuadrado protegido.":
    "Protection of a slope with a geotextile. Includes placing the geotextile. Measured per square meter protected.",

"Estabilización de talud con malla metálica. Incluye la colocación de la malla. Medido por metro cuadrado estabilizado.":
    "Stabilization of a slope with mesh. Includes placing the mesh. Measured per square meter stabilized.",

"Estabilización de fondo de excavación con material granular. Incluye la colocación y la compactación. Medido por metro cuadrado estabilizado.":
    "Stabilization of the bottom of an excavation with granular material. Includes placing and compaction. Measured per square meter stabilized.",

# ── Carga, transporte y suministro ────────────────────────────────────────
"Carga manual del material sobrante de excavación sobre camión volqueta y transporte a botadero autorizado, incluido el canon de vertido, con una distancia media considerada de 25 km. Se emplea cuando el acopio es inaccesible para la maquinaria de carga. Incluye la carga a pala sobre el vehículo, el amarre y cubrición de la carga para evitar derrames durante el trayecto, el traslado, la descarga y la limpieza de la zona de carga. Medido en volumen de material esponjado realmente retirado.":
    "Hand loading of surplus excavated material onto a dump truck and cartage to a licensed spoil site, including the tipping fee, based on an average distance of 25 km. It is used where the stockpile cannot be reached by loading plant. Includes loading onto the vehicle by shovel, sheeting and securing the load to prevent spillage in transit, cartage, tipping and cleaning of the loading area. Measured by the volume of bulked material actually removed.",

"Carga mecanizada del material sobrante de excavación con retroexcavadora sobre camión volqueta y transporte a botadero autorizado, incluido el canon de vertido, con una distancia media considerada de 25 km. Incluye la carga con la máquina, el amarre y cubrición de la carga, el traslado, la descarga, el repaso manual del acopio residual y la limpieza de la zona de carga. Medido en volumen de material esponjado realmente retirado.":
    "Mechanical loading of surplus excavated material with a backhoe onto a dump truck and cartage to a licensed spoil site, including the tipping fee, based on an average distance of 25 km. Includes loading with the machine, sheeting and securing the load, cartage, tipping, hand trimming of the residual stockpile and cleaning of the loading area. Measured by the volume of bulked material actually removed.",

"Traslado interno y acopio provisional en obra del material de excavación apto para ser reutilizado en los rellenos posteriores, evitando el doble coste de botarlo y luego comprar material de préstamo. Incluye el traslado del material al punto de acopio, su amontonamiento con talud estable y alejado de los bordes de excavación, su cubrición con lámina plástica para evitar el lavado por lluvia y el aumento de humedad, y su posterior recuperación para el relleno. Medido en volumen de material realmente acopiado.":
    "Internal movement and temporary stockpiling on site of excavated material suitable for reuse in the later backfill, avoiding the double cost of tipping it and then buying imported fill. Includes moving the material to the stockpile, heaping it with a stable batter and clear of the edges of the excavation, covering it with plastic sheeting to prevent washing out by rain and a rise in moisture content, and recovering it later for the backfill. Measured by the volume of material actually stockpiled.",

"Suministro de material granular de préstamo desde cantera o proveedor autorizado y su transporte y descarga en obra, en el punto de acopio indicado. Incluye la comprobación de la granulometría y la limpieza del material a la llegada, el rechazo de la carga si no cumple, la descarga en el punto acordado y el registro de los volúmenes recibidos por vale de entrega. Medido en volumen de material realmente recibido en obra.":
    "Supply of imported granular fill from a quarry or approved supplier and its cartage and tipping on site at the stockpile indicated. Includes checking the grading and cleanliness of the material on arrival, rejecting the load if it does not comply, tipping at the agreed point and recording the volumes received against the delivery tickets. Measured by the volume of material actually received on site.",

"Traslado interno de tierra, escombro o material a granel con carretilla, desde el frente de trabajo hasta el punto de acopio o de carga, en obras sin acceso para maquinaria. Incluye la habilitación y protección del recorrido, la carga a pala, el traslado con la distancia media de obra, la descarga ordenada en el punto de acopio y la limpieza continua del recorrido, que en un inmueble habitado es obligada y consume tiempo real. Medido en volumen de material realmente trasladado.":
    "Internal movement of spoil, debris or bulk material by wheelbarrow, from the work face to the stockpile or loading point, on work where plant cannot get in. Includes preparing and protecting the route, loading by shovel, carting over the average distance on site, tipping it neatly at the stockpile and continuous cleaning of the route, which in an occupied building is mandatory and takes real time. Measured by the volume of material actually moved.",

"Carga mecanizada de tierra sobrante a camión. Incluye la carga. Medido por metro cúbico cargado.":
    "Mechanical loading of surplus spoil onto a truck. Includes loading. Measured per cubic meter loaded.",

"Transporte de tierra sobrante a botadero. Incluye el transporte y el canon de vertido. Medido por metro cúbico transportado.":
    "Cartage of surplus spoil to a spoil site. Includes cartage and the tipping fee. Measured per cubic meter carted away.",

"Transporte de escombro a vertedero. Incluye el transporte y el canon. Medido por metro cúbico transportado.":
    "Cartage of debris to a disposal site. Includes cartage and the tipping fee. Measured per cubic meter carted away.",

"Acopio de tierra en obra para su reutilización. Incluye el acopio y la protección. Medido por metro cúbico acopiado.":
    "Stockpiling of soil on site for reuse. Includes stockpiling and protection. Measured per cubic meter stockpiled.",

"Suministro y transporte de material de préstamo a obra. Incluye el suministro y el transporte. Medido por metro cúbico suministrado.":
    "Supply and cartage of imported fill to the site. Includes supply and cartage. Measured per cubic meter supplied.",

"Suministro y transporte de arena lavada a obra. Incluye el suministro y el transporte. Medido por metro cúbico suministrado.":
    "Supply and cartage of washed sand to the site. Includes supply and cartage. Measured per cubic meter supplied.",

"Carga manual de tierra sobrante a carretilla o saco. Incluye la carga. Medido por metro cúbico cargado.":
    "Hand loading of surplus spoil into a wheelbarrow or sack. Includes loading. Measured per cubic meter loaded.",

"Transporte interno de material con carretilla. Incluye el traslado. Medido por metro cúbico transportado.":
    "Internal movement of material by wheelbarrow. Includes carting. Measured per cubic meter moved.",

"Suministro y transporte de piedra picada a obra. Incluye el suministro y el transporte. Medido por metro cúbico suministrado.":
    "Supply and cartage of crushed stone to the site. Includes supply and cartage. Measured per cubic meter supplied.",

"Suministro y transporte de gravilla a obra. Incluye el suministro y el transporte. Medido por metro cúbico suministrado.":
    "Supply and cartage of gravel to the site. Includes supply and cartage. Measured per cubic meter supplied.",
}
