# -*- coding: utf-8 -*-
"""Descripciones — Gestión de residuos y limpieza (capítulo completo, 50).

Criterios de este lote:
  · «Bote», en el español de obra de Venezuela y Colombia, es la retirada
    y disposición del escombro: no es el contenedor, es el servicio
    completo de sacarlo y pagar el vertedero.
  · «Escombro esponjado» es bulked debris: el material suelto ocupa más
    que el que estaba en macizo, y se cobra por el volumen suelto.
  · «Volqueta» es dump truck en Estados Unidos y tipper lorry en el
    Reino Unido.
  · «Gestor autorizado» es licensed waste carrier: el transportista
    habilitado, no la planta de destino.
  · «Canon de vertido» es landfill tipping fee.
  · La limpieza final distingue materiales: el desincrustante ácido sobre
    mármol o aluminio anodizado lo mancha para siempre, y eso aparece el
    día de la entrega.
"""

LOTE = {
"Habilitación de zona de acopio y clasificación de residuos de obra, con delimitación, señalización y separación por tipo de material. La clasificación en origen no es solo una exigencia ambiental: permite recuperar el valor de la chatarra y del cartón, y abarata el bote al reducir el volumen de mezcla que va a vertedero. Incluye la delimitación de la zona, la protección del piso, la colocación de los contenedores o sacos por tipo de residuo, su señalización y el mantenimiento del orden durante la obra. Medido en superficie de zona habilitada.":
    "Provision of a waste storage and sorting area on site, delimited, signposted and separated by type of material. Sorting at source is not only an environmental requirement: it recovers the value of the scrap and the cardboard, and it cuts the cost of disposal by reducing the volume of mixed waste going to landfill. Includes delimiting the area, protecting the floor, placing the containers or sacks by type of waste, signage and keeping the area tidy during the works. Measured by the area of the space provided.",

"Clasificación en obra del material procedente de la demolición para separar lo aprovechable de lo desechable, con su acopio diferenciado y gestión. La chatarra, el cobre, el aluminio y el cartón tienen valor de recuperación que puede descontarse del presupuesto o quedar a favor del cliente, y su separación reduce además el volumen que va a vertedero y por tanto el costo del bote. Incluye la separación manual por tipo de material, el acopio diferenciado, la retirada de elementos extraños de la chatarra y la entrega o venta al gestor con su comprobante. Medido en volumen de material realmente clasificado.":
    "Sorting on site of material arising from demolition to separate what can be recovered from what is to be thrown away, with separate storage and management. Scrap, copper, aluminium and cardboard have a recovery value that can be deducted from the price or left to the benefit of the client, and separating them also reduces the volume going to landfill and therefore the cost of disposal. Includes manual separation by type of material, separate storage, removal of foreign items from the scrap and delivery or sale to the licensed waste carrier against a receipt. Measured by the volume of material actually sorted.",

"Suministro de sacos de rafia de alta resistencia para la clasificación y retirada manual de residuos de obra, apilados y etiquetados por tipo de material.":
    "Supply of heavy-duty woven sacks for sorting and manual removal of site waste, stacked and labelled by type of material.",

"Habilitación de zona de acopio de chatarra metálica, delimitada y señalizada, para su venta o entrega a gestor autorizado.":
    "Provision of a scrap metal storage area, delimited and signposted, for sale or delivery to a licensed waste carrier.",

"Habilitación de zona de acopio de cartón y embalajes para su reciclaje, con protección del piso y señalización.":
    "Provision of a cardboard and packaging storage area for recycling, with floor protection and signage.",

"Habilitación de zona de acopio de madera y pallets para su reutilización o reciclaje, delimitada y señalizada.":
    "Provision of a timber and pallet storage area for reuse or recycling, delimited and signposted.",

"Clasificación en origen de los residuos de demolición y desmontaje, separando los recuperables de los de vertedero, para abaratar el bote.":
    "Separation at source of demolition and strip-out waste, separating recoverable material from material for landfill, to cut the cost of disposal.",

"Colocación de identificación y etiquetado sobre los contenedores o zonas de acopio, indicando el tipo de residuo admitido.":
    "Identification and labelling of the containers or storage areas, indicating the type of waste accepted.",

"Bajada de escombro desde plantas altas hasta el punto de acopio o carga, mediante montacargas, tolva o traslado manual, según la accesibilidad de la obra. Es un costo que se olvida sistemáticamente y que en un edificio sin ascensor de obra puede superar al del propio bote. Incluye el ensacado del escombro, su traslado hasta el punto de descenso, la bajada con el medio disponible, el acopio ordenado en planta baja y la limpieza continua de las zonas comunes de paso, que en un edificio habitado es obligada y consume tiempo real. Medido en volumen de escombro esponjado realmente bajado.":
    "Removal of debris from upper floors to the storage or loading point, by hoist, hopper or by hand, depending on access at the site. It is a cost that is consistently forgotten, and in a building without a site hoist it can exceed the cost of disposal itself. Includes bagging the debris, moving it to the point of descent, lowering it by the means available, stacking it neatly at ground level and the continuous cleaning of the common circulation areas, which in an occupied building is mandatory and takes real time. Measured by the volume of bulked debris actually removed.",

"Bajada de escombro desde plantas altas mediante escombrera o ducto vertical, con tolva de recepción y riego para control de polvo.":
    "Removal of debris from upper floors through a debris chute or vertical duct, with a receiving hopper and water spray for dust control.",

"Bajada de escombro desde plantas altas por medios manuales con sacos, hasta la zona de acopio en planta baja.":
    "Removal of debris from upper floors by hand in sacks, to the storage area at ground floor level.",

"Bajada de escombro desde plantas altas mediante montacargas de obra, con carga y descarga manual.":
    "Removal of debris from upper floors by site hoist, with loading and unloading by hand.",

"Carga manual de escombro sobre contenedor o vehículo, con uso de pala y sacos, para su retirada.":
    "Hand loading of debris into a container or vehicle, using shovels and sacks, for removal.",

"Carga mecánica de escombro sobre vehículo o volqueta con equipo adecuado, para su retirada a vertedero.":
    "Mechanical loading of debris onto a vehicle or dump truck with suitable equipment, for removal to landfill.",

"Movimiento interno de escombro desde el punto de generación hasta la zona de acopio, con medios manuales o carretilla.":
    "Internal movement of debris from the point where it arises to the storage area, by hand or by wheelbarrow.",

"Puesta a disposición de contenedor de escombro en obra, con su colocación, retiros y vaciados durante un mes. Incluye la gestión del permiso de ocupación de vía pública cuando el contenedor se sitúa fuera de la parcela, su emplazamiento sobre tacos que protegen el pavimento, la señalización reflectante, los retiros y sustituciones a medida que se llena y el traslado a vertedero autorizado con su canon. Medido por mes de permanencia.":
    "Provision of a debris container on site, including its placing, removals and emptying over one month. Includes obtaining the street occupation permit where the container stands outside the plot, setting it on blocks that protect the pavement, reflective marking, removal and replacement as it fills and cartage to a licensed disposal site with its tipping fee. Measured per month on site.",

"Alquiler mensual de contenedor de escombro de 3 m³, con su colocación y retirada por el gestor.":
    "Monthly hire of a 3 m³ debris container, including delivery and collection by the waste carrier.",

"Alquiler de contenedor destinado a chatarra metálica, con su colocación y retirada para entrega a gestor.":
    "Hire of a container for scrap metal, including delivery and collection for handover to the waste carrier.",

"Alquiler de contenedor destinado a residuos de madera, con su colocación y retirada para reciclaje.":
    "Hire of a container for timber waste, including delivery and collection for recycling.",

"Suministro y colocación de saco big-bag para acopio de escombro, con sus asas de izado para retirada con grúa.":
    "Supply and placing of a bulk bag for storing debris, with lifting loops for removal by crane.",

"Alquiler de contenedor de residuos mezclados no recuperables, con su colocación y retirada a vertedero.":
    "Hire of a container for mixed non-recoverable waste, including delivery and collection for landfill.",

"Acopio de escombro en sacos de rafia apilados en zona delimitada, a la espera de su retirada.":
    "Storage of debris in stacked woven sacks in a delimited area, awaiting removal.",

"Retirada de escombro procedente de demoliciones desde el punto de acopio de la obra y transporte en camión volqueta hasta vertedero o botadero autorizado, incluido el canon de vertido. Incluye la carga manual del escombro sobre el vehículo, el amarre y cubrición de la carga para evitar derrames durante el trayecto, el traslado con una distancia media considerada de 25 km, la descarga y la limpieza de la zona de carga. Medido por metro cúbico de escombro esponjado realmente retirado.":
    "Removal of debris arising from demolition from the storage point on site and cartage by dump truck to a licensed disposal site or spoil site, including the tipping fee. Includes hand loading of the debris onto the vehicle, sheeting and securing the load to prevent spillage in transit, cartage based on an average distance of 25 km, tipping and cleaning of the loading area. Measured per cubic meter of bulked debris actually removed.",

"Transporte de escombro a vertedero o botadero autorizado, con vehículo y canon de vertido incluidos.":
    "Cartage of debris to a licensed disposal site or spoil site, vehicle and tipping fee included.",

"Canon de vertido en vertedero autorizado de escombro mezclado no recuperable.":
    "Landfill tipping fee for mixed non-recoverable debris at a licensed disposal site.",

"Retirada y entrega de chatarra metálica a gestor autorizado, con carga y transporte.":
    "Removal and delivery of scrap metal to a licensed waste carrier, including loading and cartage.",

"Retirada y entrega de cartón y embalajes a planta de reciclaje, con carga y transporte.":
    "Removal and delivery of cardboard and packaging to a recycling plant, including loading and cartage.",

"Retirada y entrega de madera y pallets a planta de reciclaje o reutilización, con carga y transporte.":
    "Removal and delivery of timber and pallets to a recycling or reuse facility, including loading and cartage.",

"Disposición de tierra y material de excavación en botadero autorizado, con canon de vertido.":
    "Disposal of soil and excavated material at a licensed spoil site, including the tipping fee.",

"Recogida y entrega a gestor de residuos de pinturas, disolventes y envases contaminados, con su correcta identificación.":
    "Collection and delivery to a waste carrier of paint, solvent and contaminated container waste, correctly identified.",

"Recogida y entrega a gestor autorizado de residuos peligrosos menores (aerosoles, adhesivos, siliconas).":
    "Collection and delivery to a licensed waste carrier of small quantities of hazardous waste (aerosols, adhesives, sealants).",

"Recogida y entrega a gestor de tubos fluorescentes y lámparas de descarga, residuo con contenido de mercurio.":
    "Collection and delivery to a waste carrier of fluorescent tubes and discharge lamps, waste containing mercury.",

"Recogida y entrega a gestor de baterías y pilas generadas en obra, residuo peligroso.":
    "Collection and delivery to a waste carrier of batteries generated on site, hazardous waste.",

"Recogida y entrega a gestor de aceites y lubricantes usados de la maquinaria, en recipiente estanco.":
    "Collection and delivery to a waste carrier of waste oils and lubricants from plant, in a sealed container.",

"Neutralización y limpieza de derrame menor de sustancia química, con material absorbente y disposición del residuo.":
    "Neutralization and clean-up of a minor spill of a chemical substance, with absorbent material and disposal of the waste.",

"Limpieza periódica de la obra durante su ejecución, con retirada diaria de restos, barrido de los frentes de trabajo y mantenimiento de los recorridos de paso. En obra habitada no es opcional: las zonas comunes y los ambientes en uso deben quedar transitables y limpios al final de cada jornada, y ese tiempo existe aunque nadie lo presupueste. Incluye el barrido y recogida de restos, la retirada del escombro menor al punto de acopio, la limpieza de los recorridos de paso y la revisión de las protecciones al cierre de la jornada. Medido en superficie de obra por el periodo de ejecución.":
    "Periodic cleaning of the site during the works, with daily removal of waste, sweeping of the work faces and maintenance of the circulation routes. On an occupied site it is not optional: common areas and rooms in use must be left passable and clean at the end of each working day, and that time is real even though nobody prices it. Includes sweeping and collecting waste, removal of light debris to the storage point, cleaning of the circulation routes and checking of the protection at the end of the day. Measured by the area of the site over the period of the works.",

"Limpieza diaria de las zonas de trabajo durante la ejecución, con retirada de restos y barrido, para mantener el orden y la seguridad.":
    "Daily cleaning of the work areas during the works, with removal of waste and sweeping, to keep the site tidy and safe.",

"Limpieza semanal general de la obra, con barrido, retirada de escombros menores y organización de materiales.":
    "Weekly general cleaning of the site, with sweeping, removal of light debris and tidying of materials.",

"Limpieza de zonas de paso y accesos de la obra, para mantener la circulación despejada y segura.":
    "Cleaning of the circulation areas and accesses of the site, to keep them clear and safe.",

"Limpieza de restos de mortero y adhesivos de las superficies durante la obra, con rascado y retirada.":
    "Cleaning of mortar and adhesive residue from surfaces during the works, by scraping and removal.",

"Limpieza del escombro disperso en pisos tras los trabajos de demolición y albañilería, con barrido y retirada.":
    "Cleaning of loose debris from floors after demolition and masonry work, by sweeping and removal.",

"Retirada de embalajes y material de desecho de la zona de trabajo, con clasificación para reciclaje.":
    "Removal of packaging and waste material from the work area, sorted for recycling.",

"Limpieza final de la obra terminada, dejando el inmueble en condiciones de entrega. Incluye la retirada de los restos y protecciones, el barrido y aspirado de todas las superficies, la limpieza de pisos con el producto adecuado a cada material, la limpieza de sanitarios, griferías y carpinterías, la retirada de etiquetas y adhesivos de vidrios y aparatos, la limpieza de mecanismos y luminarias y el repaso final de manchas de pintura y de mortero. Medido en superficie de inmueble realmente limpiada.":
    "Final clean of the completed works, leaving the building ready for handover. Includes removal of waste and protection, sweeping and vacuuming of all surfaces, cleaning of floors with the product suited to each material, cleaning of plumbing fixtures, faucets and joinery, removal of labels and adhesive from glazing and appliances, cleaning of switch plates and light fixtures, and a final pass over paint and mortar splashes. Measured by the area of the building actually cleaned.",

"Limpieza profunda de vidrios, espejos, acabados pulidos y superficies delicadas al finalizar la obra. Requiere producto y técnica específicos por material: un desincrustante ácido usado sobre mármol o sobre aluminio anodizado lo mancha de forma irreversible, y ese daño aparece justo el día de la entrega. Incluye la retirada de restos de mortero, silicona y adhesivos con espátula plástica, la limpieza con el producto compatible con cada material, el secado sin dejar marcas y la revisión final. Medido en superficie realmente tratada.":
    "Deep cleaning of glazing, mirrors, polished finishes and delicate surfaces on completion of the works. It requires the product and technique specific to each material: an acid descaler used on marble or on anodized aluminium stains it irreversibly, and that damage appears on the very day of handover. Includes removal of mortar, sealant and adhesive residue with a plastic scraper, cleaning with the product compatible with each material, drying without leaving marks and a final check. Measured by the area actually treated.",

"Limpieza final de obra previa a la entrega, con barrido, retirada de restos y limpieza de todas las superficies.":
    "Final clean of the works ahead of handover, with sweeping, removal of waste and cleaning of all surfaces.",

"Limpieza de vidrios, carpintería y herrajes al final de la obra, con productos adecuados y sin dejar residuos.":
    "Cleaning of glazing, joinery and hardware on completion of the works, with suitable products and leaving no residue.",

"Limpieza de aparatos sanitarios y grifería al final de la obra, con desincrustante y pulido.":
    "Cleaning of plumbing fixtures and faucets on completion of the works, with descaling and polishing.",

"Limpieza de pisos al final de la obra con máquina pulidora, para dejar el acabado listo para la entrega.":
    "Machine scrubbing of floors on completion of the works, to leave the finish ready for handover.",

"Desinfección de zonas húmedas (baños, cocina) al final de la obra, con productos desinfectantes.":
    "Disinfection of wet areas (bathrooms, kitchen) on completion of the works, with disinfectant products.",

"Retirada final de las protecciones de obra y limpieza general, dejando el inmueble en condiciones de entrega.":
    "Final removal of the site protection and general cleaning, leaving the building ready for handover.",
}
