# -*- coding: utf-8 -*-
"""Descripciones — Aislamientos e impermeabilizaciones (capítulo completo, 150).

Criterios de este lote:
  · «Manto asfáltico» es bituminous membrane, y cuando se adhiere con
    soplete se dice torch-applied. «Imprimación» es primer.
  · «Media caña» en un encuentro es angle fillet, y el «remonte» es
    upstand. Los encuentros verticales son donde falla la
    impermeabilización casi siempre, no el paño central.
  · «Lámina drenante nodular» es dimpled drainage membrane y la
    «barrera anticapilaridad» es damp-proof course.
  · «Membrana cementosa flexible» es flexible cementitious membrane, y es
    el sistema de los tanques y las zonas húmedas bajo cerámica porque
    admite contacto permanente con el agua.
  · «Presión negativa» es negative side: impermeabilizar por dentro
    contra el agua que empuja desde fuera, que es mucho más exigente que
    por el trasdós.
  · «Humedad ascendente» es rising damp y «eflorescencias salinas» es
    salt efflorescence. «Hidrofugación» es water repellent treatment.
  · «Coquilla aislante» es pipe insulation en Estados Unidos y pipe
    lagging en el Reino Unido.
"""

LOTE = {
# ── Aislamiento térmico ───────────────────────────────────────────────────
"Colocación de panel de aislamiento térmico sobre la cubierta, bajo la protección o la impermeabilización según el sistema. En clima tropical el aislamiento de cubierta es la medida con mayor impacto sobre el confort y sobre el consumo de aire acondicionado, muy por encima del aislamiento de fachada, porque la cubierta es la superficie que recibe la radiación solar directa durante todo el día. Incluye la nivelación del soporte, la colocación de los paneles a junta contrapeada y encajados sin holguras, ya que cualquier junta abierta es un puente térmico, y su fijación o lastrado. Medido en superficie realmente ejecutada.":
    "Laying thermal insulation boards over the roof deck, beneath the protection or the waterproofing depending on the system. In a tropical climate roof insulation has more impact on comfort and on air conditioning consumption than anything else, far more than facade insulation, because the roof is the surface that takes direct solar radiation all day. Includes leveling the substrate, laying the boards staggered and fitted tight without gaps, since any open joint is a thermal bridge, and fastening or ballasting them. Measured by the area actually constructed.",

"Colocación de aislamiento acústico de lana mineral en la cámara de tabiques de yeso laminado o de cielos rasos suspendidos. El aislamiento absorbe la energía sonora dentro de la cámara, pero su efecto se anula si existen puentes rígidos o pasos de aire: una caja de mecanismo enfrentada a ambos lados del tabique deja pasar más ruido del que el aislamiento retiene. Incluye el corte de los paneles con sobremedida para que queden a presión sin caer, su colocación cubriendo la totalidad de la cámara sin dejar huecos y el sellado de los pasos de instalaciones. Medido en superficie realmente ejecutada.":
    "Laying mineral wool acoustic insulation in the cavity of drywall partitions or suspended ceilings. The insulation absorbs sound energy within the cavity, but its effect is cancelled out if there are rigid bridges or air paths: a back box placed back to back on either side of the partition lets through more noise than the insulation holds back. Includes cutting the boards oversize so that they stay in place by friction without slumping, laying them over the whole cavity leaving no voids and sealing around the service penetrations. Measured by the area actually constructed.",

"Colocación de manta reflectiva de doble burbuja con foil de aluminio bajo la cubierta metálica o de teja, fijada a la estructura con solapes sellados. Actúa por reflexión de la radiación infrarroja, no por resistencia térmica, de modo que necesita una cámara de aire ventilada por debajo para funcionar: pegada contra el cielo raso pierde casi toda su eficacia. Incluye el replanteo, el tendido de las bandas con solape y sellado con cinta de aluminio, su fijación a las correas y el remate en aleros y cumbrera. Medido en superficie realmente ejecutada.":
    "Laying double bubble reflective foil beneath a metal or tiled roof, fastened to the structure with sealed laps. It works by reflecting infrared radiation, not by thermal resistance, so it needs a ventilated air space beneath it to function: laid tight against the ceiling it loses almost all its effectiveness. Includes field layout, running out the sheets with lapped and sealed joints using aluminum tape, fastening to the purlins and the finish at the eaves and ridge. Measured by the area actually constructed.",

"Suministro y colocación de panel de poliestireno extruido (XPS) en muro, adherido o fijado. Incluye la preparación del soporte y la colocación del panel. Medido por metro cuadrado aislado.":
    "Supply and installation of extruded polystyrene (XPS) boards to a wall, bonded or fixed. Includes preparing the substrate and laying the boards. Measured per square meter insulated.",

"Suministro y colocación de panel de poliestireno en piso, previo al afirmado. Incluye la colocación del panel y el remate de juntas. Medido por metro cuadrado aislado.":
    "Supply and installation of polystyrene boards to a floor, before the slab. Includes laying the boards and finishing the joints. Measured per square meter insulated.",

"Suministro y colocación de panel de lana de roca en muro o tabique. Incluye la preparación del soporte y la colocación del panel. Medido por metro cuadrado aislado.":
    "Supply and installation of rock wool boards to a wall or partition. Includes preparing the substrate and laying the boards. Measured per square meter insulated.",

"Suministro y colocación de aislamiento térmico de fachada por el exterior (SATE), con panel y fijación mecánica. Incluye la colocación del panel, la fijación y el remate. Medido por metro cuadrado aislado.":
    "Supply and installation of external wall insulation (EIFS), with boards and mechanical fastening. Includes laying the boards, fastening and the finish. Measured per square meter insulated.",

"Suministro y colocación de panel sándwich aislado en cubierta. Incluye la fijación del panel y el remate de juntas. Medido por metro cuadrado aislado.":
    "Supply and installation of insulated sandwich panels to a roof. Includes fastening the panels and finishing the joints. Measured per square meter insulated.",

"Suministro y colocación de manta reflectiva de doble burbuja en fachada o cubierta. Incluye la colocación y el solape de la manta. Medido por metro cuadrado aislado.":
    "Supply and installation of double bubble reflective foil to a facade or roof. Includes laying and lapping the foil. Measured per square meter insulated.",

"Suministro y colocación de coquilla aislante en tuberías de agua caliente o climatización. Incluye la colocación de la coquilla y el sellado de juntas. Medido por metro lineal aislado.":
    "Supply and installation of pipe insulation to hot water or HVAC piping. Includes fitting the insulation and sealing the joints. Measured per meter insulated.",

"Suministro y colocación de panel de poliestireno en losa, previo al vaciado. Incluye la colocación del panel y el remate. Medido por metro cuadrado aislado.":
    "Supply and installation of polystyrene boards to a slab, before pouring. Includes laying the boards and the finish. Measured per square meter insulated.",

"Suministro y colocación de lana de roca en pared medianera, con estructura de fijación. Incluye la colocación de la lana y el remate. Medido por metro cuadrado aislado.":
    "Supply and installation of rock wool to a party wall, with a support frame. Includes laying the wool and the finish. Measured per square meter insulated.",

"Suministro y colocación de aislamiento térmico de muro por el interior, con panel y placa de yeso. Incluye la estructura, el panel y la placa. Medido por metro cuadrado aislado.":
    "Supply and installation of internal wall insulation, with boards and drywall. Includes the framing, the boards and the board lining. Measured per square meter insulated.",

"Suministro y colocación de aislamiento térmico bajo techo inclinado, con panel de lana o reflectivo. Incluye la colocación del panel y el remate. Medido por metro cuadrado aislado.":
    "Supply and installation of insulation beneath a pitched roof, with wool boards or reflective foil. Includes laying the boards and the finish. Measured per square meter insulated.",

"Suministro y colocación de panel de poliestireno en techo, previo al acabado. Incluye la colocación del panel y el remate. Medido por metro cuadrado aislado.":
    "Supply and installation of polystyrene boards to a ceiling, before the finish. Includes laying the boards and the finish. Measured per square meter insulated.",

"Suministro y colocación de panel sándwich aislado en fachada. Incluye la fijación del panel y el remate de juntas. Medido por metro cuadrado aislado.":
    "Supply and installation of insulated sandwich panels to a facade. Includes fastening the panels and finishing the joints. Measured per square meter insulated.",

"Aislamiento de puente térmico en vigas o pilares, con panel de poliestireno. Incluye la colocación del panel y el remate. Medido por metro cuadrado aislado.":
    "Insulation of a thermal bridge at beams or columns, with polystyrene boards. Includes laying the boards and the finish. Measured per square meter insulated.",

"Suministro y colocación de panel de aislamiento bajo suelo radiante. Incluye la colocación del panel y el remate. Medido por metro cuadrado aislado.":
    "Supply and installation of insulation boards beneath radiant floor heating. Includes laying the boards and the finish. Measured per square meter insulated.",

"Suministro y colocación de aislamiento térmico en depósito de agua. Incluye la colocación del aislamiento y el remate. Medido por metro cuadrado aislado.":
    "Supply and installation of thermal insulation to a water tank. Includes applying the insulation and the finish. Measured per square meter insulated.",

"Suministro y colocación de aislamiento térmico en conducto de climatización. Incluye la colocación del aislamiento y el sellado de juntas. Medido por metro cuadrado aislado.":
    "Supply and installation of thermal insulation to HVAC ductwork. Includes applying the insulation and sealing the joints. Measured per square meter insulated.",

"Suministro y colocación de aislamiento térmico en cubierta transitable, con poliestireno de alta densidad. Incluye la colocación del panel y el remate. Medido por metro cuadrado aislado.":
    "Supply and installation of thermal insulation to a trafficable roof, with high density polystyrene. Includes laying the boards and the finish. Measured per square meter insulated.",

"Suministro y colocación de doble panel de aislamiento térmico en tabique. Incluye la colocación de los paneles y el remate. Medido por metro cuadrado aislado.":
    "Supply and installation of a double layer of thermal insulation boards to a partition. Includes laying the boards and the finish. Measured per square meter insulated.",

"Suministro y colocación de manta reflectiva bajo techo metálico. Incluye la colocación de la manta y el solape. Medido por metro cuadrado aislado.":
    "Supply and installation of reflective foil beneath a metal roof. Includes laying the foil and the laps. Measured per square meter insulated.",

"Suministro y colocación de manta reflectiva en cámara de aire de fachada o cubierta. Incluye la colocación de la manta y el solape. Medido por metro cuadrado aislado.":
    "Supply and installation of reflective foil in the cavity of a facade or roof. Includes laying the foil and the laps. Measured per square meter insulated.",

# ── Aislamiento acústico ──────────────────────────────────────────────────
"Suministro y colocación de lana mineral en tabique o trasdosado, para aislamiento acústico. Incluye la colocación de la lana en la cámara. Medido por metro cuadrado aislado.":
    "Supply and installation of mineral wool in a partition or lining, for acoustic insulation. Includes placing the wool in the cavity. Measured per square meter insulated.",

"Suministro y colocación de aislamiento acústico en pared medianera. Incluye la estructura y la colocación de la lana. Medido por metro cuadrado aislado.":
    "Supply and installation of acoustic insulation to a party wall. Includes the framing and placing the wool. Measured per square meter insulated.",

"Suministro y colocación de lana mineral sobre cielo raso, para aislamiento acústico. Incluye la colocación de la lana sobre la placa. Medido por metro cuadrado aislado.":
    "Supply and installation of mineral wool over a ceiling, for acoustic insulation. Includes laying the wool over the board. Measured per square meter insulated.",

"Suministro y colocación de aislamiento acústico en conductos de ventilación o climatización. Incluye la colocación del aislamiento y el sellado. Medido por metro cuadrado aislado.":
    "Supply and installation of acoustic insulation to ventilation or HVAC ducts. Includes applying the insulation and sealing. Measured per square meter insulated.",

"Suministro y colocación de paneles acústicos en sala, para absorción del sonido. Incluye la fijación de los paneles y el remate. Medido por metro cuadrado tratado.":
    "Supply and installation of acoustic panels in a room, to absorb sound. Includes fastening the panels and the finish. Measured per square meter treated.",

"Suministro y colocación de manta acústica bajo piso flotante o laminado. Incluye la extensión de la manta y el remate. Medido por metro cuadrado colocado.":
    "Supply and installation of acoustic underlay beneath a floating or laminate floor. Includes laying the underlay and the finish. Measured per square meter installed.",

"Suministro y colocación de panel de lana mineral como suelo flotante acústico. Incluye la colocación del panel y el remate. Medido por metro cuadrado colocado.":
    "Supply and installation of mineral wool boards as a floating acoustic floor. Includes laying the boards and the finish. Measured per square meter installed.",

"Colocación de banda perimetral de desolidarización en encuentro piso-pared. Incluye la colocación de la banda y el recorte. Medido por metro lineal colocado.":
    "Installation of a perimeter isolation strip at the floor to wall junction. Includes laying the strip and cutting it to length. Measured per meter installed.",

"Suministro y colocación de aislamiento de impacto en piso, bajo el acabado. Incluye la colocación de la manta o panel y el remate. Medido por metro cuadrado aislado.":
    "Supply and installation of impact sound insulation to a floor, beneath the finish. Includes laying the underlay or boards and the finish. Measured per square meter insulated.",

"Suministro y colocación de doble manta acústica bajo piso, para mayor aislamiento de impacto. Incluye la extensión de las dos mantas y el remate. Medido por metro cuadrado colocado.":
    "Supply and installation of a double layer of acoustic underlay beneath a floor, for greater impact sound insulation. Includes laying both layers and the finish. Measured per square meter installed.",

"Suministro y colocación de soportes antivibratorios en equipos de climatización o bombeo. Incluye el montaje de los soportes y el ajuste. Medido por unidad instalada.":
    "Supply and installation of anti-vibration mounts to HVAC or pumping equipment. Includes fitting the mounts and adjusting them. Measured per unit installed.",

# ── Impermeabilización de cimentación y muros enterrados ──────────────────
"Impermeabilización de fundación con manto asfáltico y imprimación. Incluye la preparación del soporte, la imprimación y la colocación del manto. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a footing with a bituminous membrane and primer. Includes preparing the substrate, priming and laying the membrane. Measured per square meter waterproofed.",

"Impermeabilización de fundación con geocompuesto de bentonita. Incluye la preparación del soporte y la colocación del geocompuesto. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a footing with a bentonite geocomposite. Includes preparing the substrate and laying the geocomposite. Measured per square meter waterproofed.",

"Impermeabilización de muro enterrado con manto asfáltico, por su cara exterior. Incluye la preparación del soporte, la imprimación y la colocación del manto. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a buried wall with a bituminous membrane, applied to the external face. Includes preparing the substrate, priming and laying the membrane. Measured per square meter waterproofed.",

"Impermeabilización de muro enterrado con membrana líquida de poliuretano. Incluye la preparación del soporte y la aplicación de la membrana. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a buried wall with a liquid polyurethane membrane. Includes preparing the substrate and applying the membrane. Measured per square meter waterproofed.",

"Impermeabilización de muro enterrado con geocompuesto de bentonita. Incluye la preparación y la colocación del geocompuesto. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a buried wall with a bentonite geocomposite. Includes preparation and laying the geocomposite. Measured per square meter waterproofed.",

"Impermeabilización de muro enterrado con membrana cementosa flexible. Incluye la preparación del soporte y la aplicación de la membrana. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a buried wall with a flexible cementitious membrane. Includes preparing the substrate and applying the membrane. Measured per square meter waterproofed.",

"Colocación de lámina drenante nodular sobre la impermeabilización del muro enterrado. Incluye la colocación de la lámina y el remate. Medido por metro cuadrado colocado.":
    "Installation of a dimpled drainage membrane over the waterproofing of a buried wall. Includes laying the membrane and the finish. Measured per square meter installed.",

"Colocación de barrera anticapilaridad en el arranque del muro, sobre la fundación. Incluye la colocación de la lámina y el remate. Medido por metro lineal colocado.":
    "Installation of a damp-proof course at the base of the wall, over the footing. Includes laying the membrane and the finish. Measured per meter installed.",

"Impermeabilización de muro enterrado con manto asfáltico autoadherido. Incluye la preparación del soporte y la colocación del manto. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a buried wall with a self-adhesive bituminous membrane. Includes preparing the substrate and laying the membrane. Measured per square meter waterproofed.",

"Impermeabilización de muro enterrado con membrana de PVC armado. Incluye la preparación del soporte y la colocación de la membrana. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a buried wall with a reinforced PVC membrane. Includes preparing the substrate and laying the membrane. Measured per square meter waterproofed.",

"Sellado de juntas de hormigonado en muro enterrado con cordón de bentonita. Incluye la colocación del cordón y el remate. Medido por metro lineal sellado.":
    "Sealing of construction joints in a buried wall with a bentonite waterstop. Includes placing the waterstop and the finish. Measured per meter sealed.",

"Impermeabilización de muro de sótano con membrana líquida por su cara interior. Incluye la preparación del soporte y la aplicación de la membrana. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a basement wall with a liquid membrane applied to the internal face. Includes preparing the substrate and applying the membrane. Measured per square meter waterproofed.",

# ── Impermeabilización de cubierta ────────────────────────────────────────
"Impermeabilización de cubierta con manto asfáltico prefabricado con armadura de poliéster, adherido por soplete sobre imprimación asfáltica, con solapes sellados. Incluye la limpieza y secado del soporte, la comprobación de que las pendientes evacúan realmente hacia los tragantes porque un manto perfecto sobre una cubierta que empoza sigue fallando, la imprimación, el desenrollado y adherido del manto con solapes mínimos de 10 cm, el sellado de todos los bordes y la prueba de estanqueidad por inundación antes de dar por terminada la partida. Medido en superficie realmente ejecutada.":
    "Waterproofing of a roof with a prefabricated bituminous membrane with a polyester reinforcement, torch-applied over a bituminous primer, with the laps sealed. Includes cleaning and drying the substrate, checking that the falls really discharge to the roof drains, because a perfect membrane over a roof that ponds still fails, priming, unrolling and bonding the membrane with laps of at least 10 cm, sealing all the edges and the ponding test before the item is signed off. Measured by the area actually constructed.",

"Refuerzo con banda de manto asfáltico en los encuentros de la cubierta con petos, chimeneas, muros y demás elementos verticales, con formación de media caña en la arista y remonte mínimo de 20 cm sobre el plano de cubierta. Los encuentros verticales son donde falla la impermeabilización casi siempre, no el paño central. Incluye la formación de la media caña con mortero, la imprimación, la colocación de la banda de refuerzo, el remonte y su fijación mecánica superior con perfil y sellado. Medido en longitud de encuentro realmente reforzada.":
    "Reinforcement with a strip of bituminous membrane at the junctions of the roof with parapets, chimneys, walls and other vertical elements, with an angle fillet formed at the arris and an upstand of at least 20 cm above the plane of the roof. The vertical junctions are where waterproofing almost always fails, not the center of the field. Includes forming the angle fillet in mortar, priming, laying the reinforcement strip, the upstand and its mechanical fastening at the top with a bead and sealant. Measured by the length of junction actually reinforced.",

"Colocación de capa de gravilla lavada de protección sobre la impermeabilización de cubierta, con geotextil separador. La gravilla protege el manto de la radiación ultravioleta, que es lo que lo envejece y agrieta, y lo lastra frente a la succión del viento. Incluye la colocación del geotextil separador que impide que la gravilla punce el manto, el extendido de la capa con el espesor uniforme de proyecto y el respeto de las franjas libres alrededor de los tragantes para no obstruirlos. Medido en superficie realmente ejecutada.":
    "Laying a protective layer of washed gravel over the roof waterproofing, on a separating geotextile. The gravel protects the membrane from ultraviolet radiation, which is what ages it and cracks it, and ballasts it against wind uplift. Includes laying the separating geotextile that stops the gravel puncturing the membrane, spreading the layer to the uniform thickness specified and keeping clear margins around the roof drains so as not to block them. Measured by the area actually constructed.",

"Impermeabilización de cubierta con doble manto asfáltico cruzado. Incluye la imprimación y la colocación de las dos capas de manto. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a roof with two cross-laid layers of bituminous membrane. Includes priming and laying both layers of membrane. Measured per square meter waterproofed.",

"Impermeabilización de cubierta con manto asfáltico autoadherido. Incluye la preparación del soporte y la colocación del manto. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a roof with a self-adhesive bituminous membrane. Includes preparing the substrate and laying the membrane. Measured per square meter waterproofed.",

"Impermeabilización de cubierta con manto asfáltico y protección de gravilla. Incluye la imprimación, el manto y la capa de gravilla. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a roof with a bituminous membrane and a gravel protection layer. Includes priming, the membrane and the gravel layer. Measured per square meter waterproofed.",

"Impermeabilización de cubierta con membrana de PVC armado. Incluye la preparación del soporte y la colocación de la membrana. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a roof with a reinforced PVC membrane. Includes preparing the substrate and laying the membrane. Measured per square meter waterproofed.",

"Impermeabilización de cubierta o terraza con recubrimiento acrílico elastomérico aplicado en tres manos con malla de refuerzo intermedia. Es el sistema más usado en reforma por su facilidad de aplicación y de mantenimiento, ya que se repinta sin retirar lo anterior. Su durabilidad depende del espesor final alcanzado: aplicado con menos manos de las indicadas rinde una fracción de su vida útil. Incluye la limpieza y reparación del soporte, la imprimación, la primera mano, el embebido de la malla en fresco, y las manos de acabado hasta el consumo especificado por el fabricante. Medido en superficie realmente ejecutada.":
    "Waterproofing of a roof or terrace with an elastomeric acrylic coating applied in three coats with an intermediate reinforcing mesh. It is the system most used in remodeling because it is easy to apply and to maintain, since it can be recoated without stripping what is there. Its durability depends on the final thickness achieved: applied in fewer coats than specified it gives a fraction of its service life. Includes cleaning and repairing the substrate, priming, the first coat, embedding the mesh while wet, and the finishing coats up to the consumption the manufacturer specifies. Measured by the area actually constructed.",

"Impermeabilización con membrana líquida de poliuretano de alta elasticidad, aplicada en dos manos sobre imprimación, formando una capa continua sin juntas. Frente al acrílico ofrece mayor elasticidad, mejor resistencia al encharcamiento permanente y mayor vida útil, a un costo superior. Incluye la preparación y reparación del soporte, la imprimación, el refuerzo de encuentros y pases con banda, la aplicación de las manos cruzadas respetando el consumo y el tiempo entre capas, y la protección frente al tránsito hasta el curado completo. Medido en superficie realmente ejecutada.":
    "Waterproofing with a high elasticity liquid polyurethane membrane, applied in two coats over a primer, forming a continuous seamless layer. Against acrylic it offers greater elasticity, better resistance to permanent ponding and a longer service life, at a higher cost. Includes preparing and repairing the substrate, priming, reinforcing the junctions and penetrations with a strip, applying the coats crosswise respecting the consumption and the time between coats, and protecting it from traffic until fully cured. Measured by the area actually constructed.",

"Impermeabilización con mortero cementoso flexible bicomponente aplicado en dos manos cruzadas a brocha o llana. A diferencia de los sistemas asfálticos y de poliuretano, admite quedar en contacto permanente con el agua y recibir directamente enchapado encima, por lo que es el sistema de tanques, jardineras y áreas húmedas bajo cerámica. Incluye la saturación previa del soporte, el refuerzo de encuentros y esquinas con banda elástica, la aplicación de las dos manos cruzadas y la prueba de estanqueidad. Medido en superficie realmente ejecutada.":
    "Waterproofing with a two-component flexible cementitious mortar applied in two cross coats by brush or trowel. Unlike bituminous and polyurethane systems, it can stay in permanent contact with water and receive tiling directly on top, which is why it is the system for tanks, planters and wet areas beneath ceramic tile. Includes pre-saturating the substrate, reinforcing the junctions and corners with an elastic strip, applying the two cross coats and the watertightness test. Measured by the area actually constructed.",

"Impermeabilización de muro enterrado por su cara interior mediante mortero cementoso de presión negativa, cuando no es posible excavar para tratarlo por el trasdós. Trabaja contra la presión del agua que empuja desde fuera, situación mucho más exigente que la de una impermeabilización convencional, de modo que exige un producto específico y un soporte perfectamente sano y rugoso. Incluye el picado del revestimiento existente hasta el soporte, el saneado y apertura del poro, el taponado de las vías de agua activas con cemento de fraguado rápido, el refuerzo de encuentros y las manos de mortero de presión negativa. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
    "Waterproofing of a buried wall on its internal face with a negative side cementitious mortar, where it is not possible to excavate to treat it from the external face. It works against the pressure of water pushing from outside, a far more demanding situation than conventional waterproofing, so it requires a specific product and a perfectly sound and rough substrate. Includes hacking off the existing stuccoing back to the substrate, cutting out and opening the pore, plugging active water paths with rapid setting cement, reinforcing the junctions and the coats of negative side mortar. Measured by the area actually constructed, deducting voids over 1 m².",

"Apertura, limpieza y sellado de fisuras en la superficie de cubierta antes de aplicar la impermeabilización, con sellador elástico y banda de refuerzo. Impermeabilizar sobre una fisura sin tratar no la resuelve: el movimiento se transmite a la membrana y la rompe en la misma línea al poco tiempo. Incluye el mapeo de las fisuras, su apertura en forma de cajeado, la limpieza y aspirado, la imprimación, el relleno con sellador elástico y la colocación de la banda de refuerzo embebida. Medido en longitud de fisura realmente tratada.":
    "Opening up, cleaning and sealing cracks in the surface of the roof before applying the waterproofing, with elastic sealant and a reinforcing strip. Waterproofing over an untreated crack does not solve it: the movement is transmitted to the membrane and cracks it along the same line before long. Includes mapping the cracks, chasing them out, cleaning and vacuuming, priming, filling with elastic sealant and laying the embedded reinforcing strip. Measured by the length of crack actually treated.",

"Impermeabilización de terraza transitable con membrana líquida de poliuretano. Incluye la preparación del soporte y la aplicación de la membrana. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a trafficable terrace with a liquid polyurethane membrane. Includes preparing the substrate and applying the membrane. Measured per square meter waterproofed.",

"Impermeabilización de balcón con acrílico elastomérico y malla. Incluye la preparación del soporte y la aplicación del acrílico. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a balcony with elastomeric acrylic and mesh. Includes preparing the substrate and applying the acrylic. Measured per square meter waterproofed.",

"Impermeabilización de techo con membrana cementosa flexible. Incluye la preparación del soporte y la aplicación de la membrana. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a roof with a flexible cementitious membrane. Includes preparing the substrate and applying the membrane. Measured per square meter waterproofed.",

"Impermeabilización de cubierta con membrana de poliurea de aplicación en caliente. Incluye la preparación del soporte y la aplicación. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a roof with a hot applied polyurea membrane. Includes preparing the substrate and application. Measured per square meter waterproofed.",

"Impermeabilización de peto y remate perimetral de cubierta, con banda de refuerzo. Incluye la preparación y la colocación de la banda y el manto. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of the parapet and perimeter trim of a roof, with a reinforcing strip. Includes preparation and laying the strip and the membrane. Measured per square meter waterproofed.",

"Impermeabilización de canaleta o sumidero de cubierta, con refuerzo. Incluye la preparación y la colocación del refuerzo en el punto de desagüe. Medido por unidad impermeabilizada.":
    "Waterproofing of a roof channel or drain, with reinforcement. Includes preparation and placing the reinforcement at the discharge point. Measured per unit waterproofed.",

"Impermeabilización de techo de concreto con membrana líquida, previo al acabado. Incluye la preparación del soporte y la aplicación. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a concrete roof with a liquid membrane, before the finish. Includes preparing the substrate and application. Measured per square meter waterproofed.",

"Impermeabilización de terraza transitable con membrana y protección de baldosa flotante. Incluye la impermeabilización y la colocación de la baldosa sobre pedestales. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a trafficable terrace with a membrane and protection of paving on pedestals. Includes the waterproofing and laying the paving on pedestals. Measured per square meter waterproofed.",

"Impermeabilización de techo metálico con membrana líquida. Incluye la preparación del soporte y la aplicación de la membrana. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a metal roof with a liquid membrane. Includes preparing the substrate and applying the membrane. Measured per square meter waterproofed.",

"Impermeabilización de techo de teja con membrana líquida bajo la teja. Incluye la preparación del soporte y la aplicación. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a tiled roof with a liquid membrane beneath the tiles. Includes preparing the substrate and application. Measured per square meter waterproofed.",

"Impermeabilización de cubierta invertida, con membrana, aislamiento y protección. Incluye la impermeabilización, el aislamiento y la capa de protección. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of an inverted roof, with membrane, insulation and protection. Includes the waterproofing, the insulation and the protective layer. Measured per square meter waterproofed.",

"Impermeabilización de losa de techo entre pisos, previa al acabado. Incluye la preparación del soporte y la aplicación de la membrana. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of an intermediate floor slab, before the finish. Includes preparing the substrate and applying the membrane. Measured per square meter waterproofed.",

"Impermeabilización de terraza con membrana y acabado decorativo antideslizante. Incluye la impermeabilización y el acabado decorativo. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a terrace with a membrane and a decorative non-slip finish. Includes the waterproofing and the decorative finish. Measured per square meter waterproofed.",

"Impermeabilización de techo con membrana y capa de protección de mortero. Incluye la impermeabilización y la capa de protección. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a roof with a membrane and a protective mortar screed. Includes the waterproofing and the protective layer. Measured per square meter waterproofed.",

"Impermeabilización de techo de madera con membrana líquida, previo al acabado. Incluye la preparación del soporte y la aplicación. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a lumber roof with a liquid membrane, before the finish. Includes preparing the substrate and application. Measured per square meter waterproofed.",

"Impermeabilización de cubierta con membrana y manta reflectiva de protección. Incluye la impermeabilización y la colocación de la manta reflectiva. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a roof with a membrane and a protective reflective foil. Includes the waterproofing and laying the reflective foil. Measured per square meter waterproofed.",

"Impermeabilización del remate de chimenea o conducto en cubierta, con refuerzo. Incluye la preparación y la colocación del refuerzo y el manto. Medido por unidad impermeabilizada.":
    "Waterproofing of the flashing of a chimney or duct through a roof, with reinforcement. Includes preparation and placing the reinforcement and the membrane. Measured per unit waterproofed.",

# ── Zonas húmedas y depósitos ─────────────────────────────────────────────
"Impermeabilización del piso de baño, ducha o lavadero con membrana cementosa flexible, con refuerzo de encuentros y tratamiento del sumidero, como base bajo el enchapado. Es la capa que contiene el agua que atraviesa la cerámica y la boquilla, que no son estancas. El punto crítico es el encuentro del piso con la pared y el collarín del sumidero: es por donde falla el 90 % de los baños que filtran al piso inferior. Incluye la saturación del soporte, el refuerzo con banda de todos los encuentros, el tratamiento del sumidero con su collarín, las dos manos cruzadas y la prueba de estanqueidad por inundación antes de enchapar. Medido en superficie realmente ejecutada.":
    "Waterproofing of the floor of a bathroom, shower or laundry room with a flexible cementitious membrane, with the junctions reinforced and the drain treated, as a base beneath the tiling. It is the layer that holds the water that passes through the ceramic tile and the grout, which are not watertight. The critical point is the junction of the floor with the wall and the collar of the drain: that is where 90 % of the bathrooms that leak to the floor below fail. Includes saturating the substrate, reinforcing every junction with a strip, treating the drain with its collar, the two cross coats and the ponding test before tiling. Measured by the area actually constructed.",

"Impermeabilización interior de jardinera o maceta de obra con membrana cementosa flexible y capa drenante, incluida la salida de drenaje. Una jardinera sin impermeabilizar transmite humedad permanente al muro contiguo y termina reventando el friso y la pintura de la cara opuesta. Incluye la regularización interior, el refuerzo de encuentros y esquinas, las manos de membrana, el tratamiento del pase de drenaje, la colocación del geotextil y de la capa drenante de gravilla antes del sustrato. Medido en superficie realmente ejecutada.":
    "Internal waterproofing of a planter with a flexible cementitious membrane and a drainage layer, including the drain outlet. A planter that is not waterproofed transmits permanent moisture to the adjoining wall and ends up blowing the stucco and the paint on the opposite face. Includes preparing the inside, reinforcing the junctions and corners, the coats of membrane, treating the drain penetration, laying the geotextile and the gravel drainage layer before the growing medium. Measured by the area actually constructed.",

"Sellado del paso de tubería, antena, soporte o cualquier elemento que atraviesa la impermeabilización, mediante collarín, banda de refuerzo y masilla elástica. Cada pase es una perforación deliberada en la capa que debe ser estanca, y resolverlo con un simple cordón de silicona es la causa habitual de goteras localizadas. Incluye la limpieza y preparación del entorno del pase, la colocación del collarín o pieza pasamuros, el refuerzo con banda embebida en la impermeabilización, el sellado con masilla elástica compatible y la comprobación. Medido por pase realmente sellado.":
    "Sealing of the penetration of a pipe, antenna, support or any element passing through the waterproofing, with a collar, reinforcing strip and elastic mastic. Every penetration is a deliberate hole in the layer that has to be watertight, and dealing with it using a simple bead of silicone is the usual cause of localized leaks. Includes cleaning and preparing around the penetration, fitting the collar or wall sleeve, reinforcing with a strip embedded in the waterproofing, sealing with a compatible elastic mastic and checking. Measured per penetration actually sealed.",

"Impermeabilización interior de tanque de agua potable con mortero cementoso apto para contacto con agua de consumo, con refuerzo de encuentros y prueba de estanqueidad. El producto debe estar certificado para agua potable: un impermeabilizante común libera compuestos al agua y la inutiliza para consumo. Incluye el vaciado y limpieza del tanque, el saneado y resane de las paredes, el refuerzo con banda de todos los encuentros y de los pases de tubería, las manos de mortero cementoso, el curado, la prueba de estanqueidad por llenado y el lavado y desinfección antes de la puesta en servicio. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
    "Internal waterproofing of a potable water tank with a cementitious mortar suitable for contact with drinking water, with the junctions reinforced and a watertightness test. The product must be certified for potable water: an ordinary waterproofing compound releases compounds into the water and makes it unfit to drink. Includes emptying and cleaning the tank, cutting out and patching the walls, reinforcing every junction and pipe penetration with a strip, the coats of cementitious mortar, curing, the watertightness test by filling and washing and disinfecting before it is brought into service. Measured by the area actually constructed, deducting voids over 1 m².",

"Impermeabilización de balcón o terraza transitable con membrana cementosa flexible bajo el piso de acabado, con refuerzo de encuentros y tratamiento del borde. El punto crítico es el encuentro con el paramento y el remate del borde exterior: la membrana debe remontar por la pared por encima del nivel del piso terminado y morir en el goterón del borde, no cortarse a ras. Incluye la comprobación de las pendientes, el refuerzo de encuentros y desagües, las manos de membrana con el remonte perimetral, la prueba de estanqueidad y la protección hasta recibir el piso. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
    "Waterproofing of a trafficable balcony or terrace with a flexible cementitious membrane beneath the floor finish, with the junctions reinforced and the edge treated. The critical point is the junction with the wall and the finish at the outer edge: the membrane must turn up the wall above the level of the finished floor and terminate at the drip of the edge, not be cut off flush. Includes checking the falls, reinforcing the junctions and drains, the coats of membrane with the perimeter upstand, the watertightness test and protection until the floor is laid. Measured by the area actually constructed, deducting voids over 1 m².",

"Impermeabilización de muro de zona de ducha con membrana cementosa, previa al enchapado. Incluye la preparación del soporte y la aplicación de la membrana. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a shower area wall with a cementitious membrane, before tiling. Includes preparing the substrate and applying the membrane. Measured per square meter waterproofed.",

"Impermeabilización de piso de cocina con membrana líquida o cementosa. Incluye la preparación del soporte y la aplicación. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a kitchen floor with a liquid or cementitious membrane. Includes preparing the substrate and application. Measured per square meter waterproofed.",

"Impermeabilización de piso de lavandería con membrana cementosa. Incluye la preparación del soporte y la aplicación. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a laundry floor with a cementitious membrane. Includes preparing the substrate and application. Measured per square meter waterproofed.",

"Impermeabilización del entorno de la bañera con membrana cementosa, previa al enchapado. Incluye la preparación y la aplicación. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing around a bathtub with a cementitious membrane, before tiling. Includes preparation and application. Measured per square meter waterproofed.",

"Impermeabilización de piso de cuarto de máquinas o área técnica. Incluye la preparación del soporte y la aplicación de la membrana. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of the floor of a mechanical room or technical area. Includes preparing the substrate and applying the membrane. Measured per square meter waterproofed.",

"Sellado perimetral de la zona de ducha con banda de refuerzo en los encuentros. Incluye la colocación de la banda y el sellado. Medido por metro lineal sellado.":
    "Perimeter sealing of a shower area with a reinforcing strip at the junctions. Includes laying the strip and sealing. Measured per meter sealed.",

"Impermeabilización de techo de baño o zona húmeda con membrana cementosa. Incluye la preparación del soporte y la aplicación. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a bathroom ceiling or wet area with a cementitious membrane. Includes preparing the substrate and application. Measured per square meter waterproofed.",

"Impermeabilización de piso de ducha con formación de pendiente y membrana. Incluye la pendiente, la membrana y el sellado. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a shower floor with the fall formed and membrane. Includes the fall, the membrane and sealing. Measured per square meter waterproofed.",

"Impermeabilización de muro de cocina previa al enchapado, con membrana cementosa. Incluye la preparación y la aplicación. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a kitchen wall before tiling, with a cementitious membrane. Includes preparation and application. Measured per square meter waterproofed.",

"Impermeabilización de piso de baño existente, previa a la renovación del acabado. Incluye la preparación del soporte y la aplicación de la membrana. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of an existing bathroom floor, before renewing the finish. Includes preparing the substrate and applying the membrane. Measured per square meter waterproofed.",

"Impermeabilización de paramentos de sauna o baño de vapor con membrana. Incluye la preparación del soporte y la aplicación. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of the walls of a sauna or steam room with a membrane. Includes preparing the substrate and application. Measured per square meter waterproofed.",

"Impermeabilización de piscina interior con membrana cementosa o líquida. Incluye la preparación del soporte y la aplicación. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of an indoor swimming pool with a cementitious or liquid membrane. Includes preparing the substrate and application. Measured per square meter waterproofed.",

"Impermeabilización de área de piscina o spa, previa al enchapado. Incluye la preparación y la aplicación de la membrana. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a pool or spa area, before tiling. Includes preparation and applying the membrane. Measured per square meter waterproofed.",

"Impermeabilización de balcón con manta asfáltica o membrana líquida. Incluye la preparación del soporte y la aplicación. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a balcony with a bituminous membrane or a liquid membrane. Includes preparing the substrate and application. Measured per square meter waterproofed.",

"Impermeabilización de zona de riego o macetero interior. Incluye la preparación del soporte y la aplicación de la membrana. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of an indoor irrigation zone or planter. Includes preparing the substrate and applying the membrane. Measured per square meter waterproofed.",

"Impermeabilización de baño con membrana líquida de poliuretano. Incluye la preparación del soporte y la aplicación. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a bathroom with a liquid polyurethane membrane. Includes preparing the substrate and application. Measured per square meter waterproofed.",

"Impermeabilización de cocina con membrana líquida de poliuretano. Incluye la preparación del soporte y la aplicación. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a kitchen with a liquid polyurethane membrane. Includes preparing the substrate and application. Measured per square meter waterproofed.",

"Impermeabilización de zona de ducha con membrana de PVC armado. Incluye la preparación del soporte y la colocación de la membrana. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a shower area with a reinforced PVC membrane. Includes preparing the substrate and laying the membrane. Measured per square meter waterproofed.",

"Impermeabilización de cuarto húmedo o área de servicio con membrana cementosa. Incluye la preparación del soporte y la aplicación. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a wet room or service area with a cementitious membrane. Includes preparing the substrate and application. Measured per square meter waterproofed.",

"Impermeabilización de piso de baño con formación de pendiente hacia el desagüe. Incluye la pendiente, la membrana y el sellado. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a bathroom floor with a fall formed to the drain. Includes the fall, the membrane and sealing. Measured per square meter waterproofed.",

"Impermeabilización de baño existente, previa a la renovación, con membrana líquida. Incluye la preparación del soporte y la aplicación. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of an existing bathroom with a liquid membrane, before remodeling. Includes preparing the substrate and application. Measured per square meter waterproofed.",

"Impermeabilización del vaso de piscina con membrana líquida de poliuretano. Incluye la preparación del soporte y la aplicación. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a pool shell with a liquid polyurethane membrane. Includes preparing the substrate and application. Measured per square meter waterproofed.",

"Impermeabilización del vaso de piscina con membrana cementosa flexible. Incluye la preparación del soporte y la aplicación. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a pool shell with a flexible cementitious membrane. Includes preparing the substrate and application. Measured per square meter waterproofed.",

"Impermeabilización del vaso de piscina con membrana de PVC armado. Incluye la preparación del soporte y la colocación de la membrana. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a pool shell with a reinforced PVC membrane. Includes preparing the substrate and laying the membrane. Measured per square meter waterproofed.",

"Impermeabilización interior de tanque de agua con membrana cementosa. Incluye la preparación del soporte y la aplicación. Medido por metro cuadrado impermeabilizado.":
    "Internal waterproofing of a water tank with a cementitious membrane. Includes preparing the substrate and application. Measured per square meter waterproofed.",

"Impermeabilización de jardinera o maceta de obra con membrana líquida. Incluye la preparación del soporte y la aplicación. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a planter with a liquid membrane. Includes preparing the substrate and application. Measured per square meter waterproofed.",

"Impermeabilización de tanque de concreto con membrana cementosa flexible. Incluye la preparación del soporte y la aplicación. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a concrete tank with a flexible cementitious membrane. Includes preparing the substrate and application. Measured per square meter waterproofed.",

"Impermeabilización del vaso de piscina con doble membrana líquida. Incluye la preparación y la aplicación de las dos capas. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a pool shell with two liquid membranes. Includes preparation and applying both layers. Measured per square meter waterproofed.",

"Impermeabilización interior de tanque metálico con membrana líquida. Incluye la preparación del soporte y la aplicación. Medido por metro cuadrado impermeabilizado.":
    "Internal waterproofing of a metal tank with a liquid membrane. Includes preparing the substrate and application. Measured per square meter waterproofed.",

"Impermeabilización de piscina elevada o jacuzzi de obra. Incluye la preparación del soporte y la aplicación de la membrana. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a raised pool or built-in hot tub. Includes preparing the substrate and applying the membrane. Measured per square meter waterproofed.",

"Impermeabilización de jardinera con membrana y capa drenante. Incluye la impermeabilización y la colocación del drenaje. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a planter with a membrane and drainage layer. Includes the waterproofing and installing the drainage. Measured per square meter waterproofed.",

"Impermeabilización de piscina de fibra de vidrio con membrana de refuerzo. Incluye la preparación del soporte y la aplicación. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of a glass fiber pool with a reinforcing membrane. Includes preparing the substrate and application. Measured per square meter waterproofed.",

"Impermeabilización de fuente ornamental con membrana líquida. Incluye la preparación del soporte y la aplicación. Medido por metro cuadrado impermeabilizado.":
    "Waterproofing of an ornamental fountain with a liquid membrane. Includes preparing the substrate and application. Measured per square meter waterproofed.",

# ── Drenaje y capas ───────────────────────────────────────────────────────
"Ejecución de drenaje perimetral con tubería perforada y geotextil. Incluye la excavación, la colocación de la tubería y el relleno de grava. Medido por metro lineal ejecutado.":
    "Construction of perimeter drainage with perforated pipe and geotextile. Includes excavation, laying the pipe and backfilling with gravel. Measured per meter constructed.",

"Colocación de geotextil separador bajo rellenos o pavimentos. Incluye la extensión del geotextil y el solape. Medido por metro cuadrado colocado.":
    "Laying a separating geotextile beneath fill or paving. Includes spreading the geotextile and the laps. Measured per square meter installed.",

"Colocación de lámina drenante nodular en muro enterrado. Incluye la colocación de la lámina y el remate. Medido por metro cuadrado colocado.":
    "Installation of a dimpled drainage membrane to a buried wall. Includes laying the membrane and the finish. Measured per square meter installed.",

"Ejecución de drenaje de cubierta con canaleta y bajante. Incluye la colocación de la canaleta y la conexión a la bajante. Medido por metro lineal ejecutado.":
    "Installation of roof drainage with a channel and downspout. Includes laying the channel and connecting it to the downspout. Measured per meter constructed.",

"Ejecución de drenaje de jardín con tubería perforada y geotextil. Incluye la excavación, la colocación de la tubería y el relleno. Medido por metro lineal ejecutado.":
    "Construction of garden drainage with perforated pipe and geotextile. Includes excavation, laying the pipe and backfilling. Measured per meter constructed.",

"Colocación de geocompuesto drenante en muro o cubierta. Incluye la colocación del geocompuesto y el remate. Medido por metro cuadrado colocado.":
    "Installation of a drainage geocomposite to a wall or roof. Includes laying the geocomposite and the finish. Measured per square meter installed.",

"Colocación de capa separadora de polietileno bajo afirmado o impermeabilización. Incluye la extensión de la lámina y el solape. Medido por metro cuadrado colocado.":
    "Laying a polyethylene separating layer beneath a slab or waterproofing. Includes spreading the sheet and the laps. Measured per square meter installed.",

"Colocación de capa de protección de gravilla sobre impermeabilización. Incluye la extensión de la gravilla y el nivelado. Medido por metro cuadrado colocado.":
    "Laying a protective gravel layer over the waterproofing. Includes spreading the gravel and leveling it. Measured per square meter installed.",

"Ejecución de capa de protección de mortero sobre impermeabilización. Incluye la aplicación del mortero y el acabado. Medido por metro cuadrado ejecutado.":
    "Construction of a protective mortar screed over the waterproofing. Includes applying the mortar and the finish. Measured per square meter constructed.",

"Colocación de geotextil separador en terraza, entre impermeabilización y acabado. Incluye la extensión del geotextil y el solape. Medido por metro cuadrado colocado.":
    "Laying a separating geotextile on a terrace, between the waterproofing and the finish. Includes spreading the geotextile and the laps. Measured per square meter installed.",

"Ejecución de drenaje de trasdós de muro con geotextil y grava. Incluye la colocación del geotextil y el relleno de grava. Medido por metro lineal ejecutado.":
    "Construction of drainage to the rear face of a wall with geotextile and gravel. Includes laying the geotextile and backfilling with gravel. Measured per meter constructed.",

"Ejecución de capa drenante en cubierta ajardinada, con geotextil y drenaje. Incluye la colocación del drenaje y el geotextil. Medido por metro cuadrado ejecutado.":
    "Construction of a drainage layer on a green roof, with geotextile and drainage. Includes laying the drainage and the geotextile. Measured per square meter constructed.",

# ── Sellado de juntas ─────────────────────────────────────────────────────
"Sellado de junta de construcción con sellador elástico de poliuretano. Incluye la limpieza de la junta y la aplicación del sellador. Medido por metro lineal sellado.":
    "Sealing a construction joint with an elastic polyurethane sealant. Includes cleaning the joint and applying the sealant. Measured per meter sealed.",

"Sellado de junta de hormigonado con cordón de bentonita expansiva. Incluye la colocación del cordón y el remate. Medido por metro lineal sellado.":
    "Sealing a construction joint with an expansive bentonite waterstop. Includes placing the waterstop and the finish. Measured per meter sealed.",

"Sellado de junta de construcción con banda de PVC. Incluye la colocación de la banda y el remate. Medido por metro lineal sellado.":
    "Sealing a construction joint with a PVC waterstop. Includes placing the waterstop and the finish. Measured per meter sealed.",

"Sellado de junta de dilatación en piso con perfil y sellador elástico. Incluye la limpieza de la junta, la colocación del perfil y el sellado. Medido por metro lineal sellado.":
    "Sealing an expansion joint in a floor with a profile and elastic sealant. Includes cleaning the joint, fitting the profile and sealing. Measured per meter sealed.",

"Sellado de junta de dilatación en fachada con sellador elástico. Incluye la limpieza de la junta y la aplicación del sellador. Medido por metro lineal sellado.":
    "Sealing an expansion joint in a facade with elastic sealant. Includes cleaning the joint and applying the sealant. Measured per meter sealed.",

"Sellado de junta de dilatación en cubierta con banda de refuerzo y sellador. Incluye la colocación de la banda y el sellado. Medido por metro lineal sellado.":
    "Sealing an expansion joint in a roof with a reinforcing strip and sealant. Includes laying the strip and sealing. Measured per meter sealed.",

"Sellado de junta en piscina con sellador apto para inmersión. Incluye la limpieza de la junta y la aplicación del sellador. Medido por metro lineal sellado.":
    "Sealing a joint in a swimming pool with a sealant suitable for immersion. Includes cleaning the joint and applying the sealant. Measured per meter sealed.",

"Sellado de junta perimetral de muro con sellador elástico. Incluye la limpieza de la junta y la aplicación del sellador. Medido por metro lineal sellado.":
    "Sealing the perimeter joint of a wall with elastic sealant. Includes cleaning the joint and applying the sealant. Measured per meter sealed.",

"Sellado de paso de instalaciones en muro o losa, con sellador y collarín. Incluye la preparación del pase y el sellado. Medido por unidad sellada.":
    "Sealing a services penetration through a wall or slab, with sealant and a collar. Includes preparing the penetration and sealing. Measured per unit sealed.",

"Sellado de junta de encuentro piso-pared con sellador sanitario. Incluye la limpieza de la junta y la aplicación del sellador. Medido por metro lineal sellado.":
    "Sealing the floor to wall junction with sanitary sealant. Includes cleaning the joint and applying the sealant. Measured per meter sealed.",

"Sellado de junta de dilatación en escalera con perfil y sellador. Incluye la colocación del perfil y el sellado. Medido por metro lineal sellado.":
    "Sealing an expansion joint in a stair with a profile and sealant. Includes fitting the profile and sealing. Measured per meter sealed.",

"Sellado de junta en tanque de agua con sellador apto para inmersión. Incluye la limpieza de la junta y la aplicación. Medido por metro lineal sellado.":
    "Sealing a joint in a water tank with a sealant suitable for immersion. Includes cleaning the joint and application. Measured per meter sealed.",

# ── Tratamiento de humedades y filtraciones ───────────────────────────────
"Inyección de resina en fisura para sellar filtraciones en muro o losa. Incluye la preparación de la fisura, la colocación de boquillas y la inyección. Medido por metro lineal inyectado.":
    "Injection of resin into a crack to seal water ingress through a wall or slab. Includes preparing the crack, fitting the injection ports and injecting. Measured per meter injected.",

"Tratamiento de filtración en techo con localización, saneado y sellado. Incluye la localización de la filtración, el saneado y el sellado. Medido por metro cuadrado tratado.":
    "Treatment of water ingress through a roof by locating it, cutting out and sealing. Includes locating the ingress, cutting out and sealing. Measured per square meter treated.",

"Reparación de filtración en muro enterrado, con saneado y sellado. Incluye la localización, el saneado y el sellado de la filtración. Medido por metro cuadrado reparado.":
    "Repair of water ingress through a buried wall, by cutting out and sealing. Includes locating, cutting out and sealing the ingress. Measured per square meter repaired.",

"Tratamiento de filtración en piscina, con localización y sellado de la zona. Incluye el vaciado parcial, la localización y el sellado. Medido por metro cuadrado tratado.":
    "Treatment of water ingress in a swimming pool, locating and sealing the area. Includes partial draining, locating and sealing. Measured per square meter treated.",

"Reparación de filtración en terraza, con saneado y aplicación de membrana. Incluye la localización, el saneado y la aplicación. Medido por metro cuadrado reparado.":
    "Repair of water ingress through a terrace, by cutting out and applying a membrane. Includes locating, cutting out and application. Measured per square meter repaired.",

"Tratamiento de humedad ascendente por capilaridad con barrera y saneado. Incluye el saneado del muro y la aplicación de la barrera. Medido por metro cuadrado tratado.":
    "Treatment of rising damp with a barrier and cutting out. Includes cutting out the wall and applying the barrier. Measured per square meter treated.",

"Tratamiento antihumedad de muro interior, con saneado y barrera. Incluye el saneado, la aplicación de la barrera y el remate. Medido por metro cuadrado tratado.":
    "Damp treatment of an internal wall, by cutting out and a barrier. Includes cutting out, applying the barrier and the finish. Measured per square meter treated.",

"Saneado de muro con eflorescencias salinas, con limpieza y tratamiento. Incluye la limpieza de las sales y la aplicación del tratamiento. Medido por metro cuadrado saneado.":
    "Treatment of a wall with salt efflorescence, by cleaning and treatment. Includes removing the salts and applying the treatment. Measured per square meter treated.",

"Tratamiento de humedad en sótano, con saneado y membrana. Incluye la preparación del soporte y la aplicación de la membrana. Medido por metro cuadrado tratado.":
    "Treatment of damp in a basement, by cutting out and a membrane. Includes preparing the substrate and applying the membrane. Measured per square meter treated.",

"Tratamiento de humedad por condensación, con saneado y revestimiento antihumedad. Incluye la limpieza y la aplicación del tratamiento. Medido por metro cuadrado tratado.":
    "Treatment of condensation damp, by cutting out and an anti-condensation coating. Includes cleaning and applying the treatment. Measured per square meter treated.",

"Colocación de barrera antihumedad en piso, previa al acabado. Incluye la extensión de la barrera y el solape. Medido por metro cuadrado colocado.":
    "Laying a damp-proof membrane to a floor, before the finish. Includes spreading the membrane and the laps. Measured per square meter installed.",

"Tratamiento de humedad en muro de piedra, con saneado y hidrofugación. Incluye la limpieza y la aplicación del hidrofugante. Medido por metro cuadrado tratado.":
    "Treatment of damp in a stone wall, by cutting out and a water repellent. Includes cleaning and applying the water repellent. Measured per square meter treated.",
}
