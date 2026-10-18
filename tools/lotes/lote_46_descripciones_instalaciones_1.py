# -*- coding: utf-8 -*-
"""Descripciones — Instalaciones (1 de 4): fontanería de abasto.

Criterios de este lote:
  · La «termofusión» del PPR es heat fusion en los Estados Unidos y
    fusion welding en el Reino Unido.
  · «Llave de paso de esfera» es ball valve y la «llave de escuadra» es
    angle valve. El «embellecedor» es escutcheon.
  · El «anillo de cera» del inodoro es wax ring, y el «tubo de abasto
    flexible» es flexible supply hose.
  · «Roza» es chase y la «rozadora» es wall chaser. El «pasamuros» es
    sleeve.
  · La «trampa de grasa» es grease interceptor en los Estados Unidos y
    grease trap en el Reino Unido, y su tapa tiene que quedar registrable.
  · El «registro de aguas servidas» es inspection chamber cuando es
    registrable a pie y manhole cuando es de mayor tamaño, y su solera
    lleva «media caña», que en inglés es benching: es lo que guía el flujo
    y evita que se sedimente.
"""

LOTE = {
"Instalación de tubería de polipropileno PPR de 20 mm para distribución de agua fría o caliente, empotrada en paramento. Incluye replanteo del trazado, apertura de roza con rozadora eléctrica con captación de polvo, colocación de la tubería con uniones por termofusión, accesorios y piezas especiales, fijación con abrazaderas, prueba de estanqueidad a presión y tapado de roza con mortero de reparación, dejando el paramento listo para su revestimiento. No incluye el acabado final del paramento. Medido en longitud realmente instalada.":
    "Installation of 20 mm polypropylene PPR pipework for hot or cold water distribution, concealed in the wall. Includes setting out the run, cutting the chase with an electric wall chaser with dust extraction, laying the pipework with heat fusion joints, fittings and specials, fixing with pipe clips, pressure testing for watertightness and filling the chase with a repair mortar, leaving the face ready for its finish. It does not include the final finish to the wall. Measured by the length actually installed.",

"Montante o alimentación principal de agua en tubería de polipropileno PPR de 25 mm, con uniones por termofusión, soportes y llaves de sectorización. Incluye el replanteo del recorrido buscando trazados registrables siempre que sea posible, el corte y termofusión, la colocación de soportes con la separación que evita flechas y ruidos por dilatación, los pasos de losa y pared con su pasamuros, la prueba de estanqueidad a presión y el resane. Medido en longitud realmente instalada.":
    "Riser or main water supply in 25 mm polypropylene PPR pipework, with heat fusion joints, supports and isolating valves. Includes setting out the route, looking for accessible runs wherever possible, cutting and fusion, placing the supports at the spacing that prevents sag and noise from thermal expansion, the penetrations through slab and wall with their sleeves, the pressure test for watertightness and making good. Measured by the length actually installed.",

"Sustitución de un tramo de tubería de agua existente en mal estado, con el corte, retiro y reposición del tramo y sus conexiones. En reforma es una intervención muy frecuente al sustituir tramos de hierro galvanizado corroído, y el punto delicado es la unión con la tubería que permanece, que debe hacerse con adaptador compatible entre materiales distintos y no forzando roscas. Incluye el cierre y vaciado de la red, la localización y apertura de roza, el corte y retiro del tramo, la instalación del nuevo con sus adaptadores, la prueba de presión y el resane. Medido en longitud realmente sustituida.":
    "Replacement of a length of existing water pipework in poor condition, cutting out, removing and reinstating the length and its connections. In refurbishment this is a very frequent intervention when replacing corroded galvanised iron, and the delicate point is the joint with the pipework that remains, which must be made with an adapter compatible between the different materials and not by forcing threads. Includes closing down and draining the system, locating and opening the chase, cutting out and removing the length, installing the new one with its adapters, the pressure test and making good. Measured by the length actually replaced.",

"Suministro e instalación de tubería de agua de PPR de 32 mm. Incluye el montaje y la fijación. Medido por metro lineal instalado.":
    "Supply and installation of 32 mm PPR water pipework. Includes assembly and fixing. Measured per meter installed.",
"Suministro e instalación de tubería de agua de cobre. Incluye el montaje y la soldadura. Medido por metro lineal instalado.":
    "Supply and installation of copper water pipework. Includes assembly and soldering. Measured per meter installed.",
"Suministro e instalación de montante de agua de PPR de 32 mm. Incluye el montaje. Medido por metro lineal instalado.":
    "Supply and installation of a 32 mm PPR water riser. Includes assembly. Measured per meter installed.",
"Suministro e instalación de tubería de agua caliente con aislamiento. Incluye el montaje y el aislamiento. Medido por metro lineal instalado.":
    "Supply and installation of insulated hot water pipework. Includes assembly and the insulation. Measured per meter installed.",
"Suministro e instalación de tubería de agua vista. Incluye el montaje y la fijación. Medido por metro lineal instalado.":
    "Supply and installation of surface water pipework. Includes assembly and fixing. Measured per meter installed.",
"Suministro e instalación de tubería de agua de PPR de 40 mm. Incluye el montaje y la fijación. Medido por metro lineal instalado.":
    "Supply and installation of 40 mm PPR water pipework. Includes assembly and fixing. Measured per meter installed.",

"Ejecución de punto de agua para aparato sanitario, formado por las derivaciones de agua fría y caliente en tubería de PPR de 20 mm desde el montante más próximo hasta la salida del aparato, con una longitud media de 2,5 m por punto. Incluye replanteo de la altura y separación normalizadas de las tomas, apertura de roza, montaje de la tubería con uniones por termofusión, codos de salida con refuerzo metálico anclados al paramento, prueba de estanqueidad a presión de la derivación, taponado provisional hasta la instalación del aparato y tapado de roza con mortero de reparación. No incluye la grifería ni el aparato. Medido por punto terminado y probado.":
    "Installation of a water point for a plumbing fixture, comprising the hot and cold branches in 20 mm PPR pipework from the nearest riser to the outlet of the fixture, at an average length of 2.5 m per point. Includes setting out the outlets at the standard height and spacing, cutting the chase, laying the pipework with heat fusion joints, the outlet elbows with a metal reinforcement anchored to the wall, the pressure test for watertightness on the branch, temporarily capping until the fixture is installed, and filling the chase with a repair mortar. It does not include the faucet or the fixture. Measured per point completed and tested.",

"Punto de agua para lavadora, con llave y toma. Incluye la conexión y la llave. Medido por punto ejecutado.":
    "Water point for a washing machine, with a valve and an outlet. Includes the connection and the valve. Measured per point constructed.",
"Punto de agua para calentador. Incluye la conexión y la llave. Medido por punto ejecutado.":
    "Water point for a water heater. Includes the connection and the valve. Measured per point constructed.",
"Punto de agua para nevera con dispensador. Incluye la conexión. Medido por punto ejecutado.":
    "Water point for a refrigerator with a dispenser. Includes the connection. Measured per point constructed.",
"Punto de agua para jardín o exterior. Incluye la conexión y la llave. Medido por punto ejecutado.":
    "Water point for a garden or outside. Includes the connection and the valve. Measured per point constructed.",

"Suministro y montaje de llave de paso de esfera de PPR de 20 mm, empotrada en paramento, para el corte sectorizado del suministro de agua. Incluye apertura del hueco, montaje intercalado en la tubería mediante termofusión, comprobación de la maniobrabilidad del volante, prueba de estanqueidad y resane del paramento, dejando el embellecedor enrasado. Medido por unidad instalada y probada.":
    "Supply and installation of a 20 mm PPR ball valve, concealed in the wall, to isolate the water supply by zone. Includes opening up the recess, fitting it into the pipework by heat fusion, checking that the handle operates, the watertightness test and making good the wall, leaving the escutcheon flush. Measured per unit installed and tested.",

"Instalación de llave de escuadra para aparato sanitario. Incluye la conexión. Medido por unidad instalada.":
    "Installation of an angle valve for a plumbing fixture. Includes the connection. Measured per unit installed.",
"Instalación de válvula de retención. Incluye la conexión. Medido por unidad instalada.":
    "Installation of a check valve. Includes the connection. Measured per unit installed.",
"Instalación de llave general de agua. Incluye la conexión. Medido por unidad instalada.":
    "Installation of a main water shut-off valve. Includes the connection. Measured per unit installed.",

"Instalación de inodoro sobre punto de agua y desagüe previamente ejecutados. Incluye replanteo y presentación de la pieza, montaje del anillo de cera o junta de estanqueidad, anclaje al piso con tornillería inoxidable y tacos, conexión al desagüe, montaje del tanque y sus herrajes internos, conexión de la alimentación mediante tubo de abasto flexible con llave de escuadra, sellado perimetral con silicona sanitaria antihongos, regulación del mecanismo de descarga y prueba de funcionamiento y estanqueidad. El aparato lo elige el cliente y se presupuesta aparte. Medido por unidad instalada y probada.":
    "Installation of a toilet onto a previously constructed water point and waste. Includes setting out and offering up the pan, fitting the wax ring or sealing gasket, anchoring to the floor with stainless steel screws and plugs, connecting to the waste, assembling the cistern and its internal fittings, connecting the supply with a flexible supply hose to an angle valve, sealing the perimeter with mold resistant sanitary silicone, adjusting the flush mechanism and testing the operation and the watertightness. The fixture is selected by the client and priced separately. Measured per unit installed and tested.",

"Instalación de lavamanos, ya sea de pedestal, sobre mesón o suspendido, sobre puntos de agua y desagüe previamente ejecutados. Incluye replanteo de la altura de uso, taladrado y anclaje al paramento o fijación sobre el mueble, montaje de la grifería con sus juntas, conexión de las tomas de agua fría y caliente mediante tubos de abasto flexibles con llaves de escuadra, montaje del desagüe con su válvula y sifón, sellado perimetral con silicona sanitaria, y prueba de funcionamiento, evacuación y estanqueidad. El aparato y la grifería los elige el cliente y se presupuestan aparte. Medido por unidad instalada y probada.":
    "Installation of a lavatory, whether pedestal, countertop or wall hung, onto previously constructed water and waste points. Includes setting out the working height, drilling and anchoring to the wall or fixing to the cabinet, fitting the faucet with its washers, connecting the hot and cold supplies with flexible supply hoses to angle valves, fitting the waste with its valve and trap, sealing the perimeter with sanitary silicone, and testing the operation, the drainage and the watertightness. The fixture and the faucet are selected by the client and priced separately. Measured per unit installed and tested.",

"Instalación de ducha o regadera sobre puntos de agua previamente ejecutados, con su grifería mezcladora, brazo y rociador. Incluye la comprobación de la altura y separación normalizadas de las salidas, el montaje del cuerpo de la grifería con sus excéntricas y juntas, el ajuste del embellecedor contra el enchapado, el sellado perimetral con silicona sanitaria, el montaje del brazo y rociador y la prueba de funcionamiento, temperatura y estanqueidad. El aparato y la grifería los elige el cliente y se presupuestan aparte. Medido por unidad instalada y probada.":
    "Installation of a shower onto previously constructed water points, with its mixer faucet, arm and shower head. Includes checking that the outlets are at the standard height and spacing, fitting the body of the faucet with its eccentric connectors and washers, setting the escutcheon against the tiling, sealing the perimeter with sanitary silicone, fitting the arm and the shower head and testing the operation, the temperature and the watertightness. The fixture and the faucet are selected by the client and priced separately. Measured per unit installed and tested.",

"Instalación de fregadero de cocina sobre mesón, con su grifería, desagüe y sifón. Incluye el replanteo y corte del hueco en el mesón cuando no venga mecanizado, el sellado del canto de corte que en mesones de aglomerado es lo que evita que se hinche con la humedad, el montaje del fregadero con sus clips y sellado perimetral, el montaje de la grifería, la conexión de agua fría y caliente con abastos flexibles y llaves de escuadra, el montaje del desagüe y sifón y la prueba de estanqueidad. El aparato y la grifería los elige el cliente y se presupuestan aparte. Medido por unidad instalada y probada.":
    "Installation of a kitchen sink into a countertop, with its faucet, waste and trap. Includes setting out and cutting the opening in the countertop where it is not pre-cut, sealing the cut edge, which on a chipboard countertop is what stops it swelling with moisture, fitting the sink with its clips and sealing the perimeter, fitting the faucet, connecting the hot and cold with flexible supply hoses and angle valves, fitting the waste and the trap and the watertightness test. The fixture and the faucet are selected by the client and priced separately. Measured per unit installed and tested.",

"Instalación de calentador de agua eléctrico o a gas, con sus soportes, conexiones hidráulicas y elementos de seguridad. Incluye el replanteo y anclaje de los soportes verificando que el paramento resiste el peso del equipo lleno, que es varias veces el del equipo vacío, la conexión de entrada y salida con llaves de corte y uniones desmontables para permitir el mantenimiento, el montaje de la válvula de seguridad con su descarga conducida, la conexión eléctrica o de gas según el tipo, el llenado, la purga y la prueba de funcionamiento. El equipo lo elige el cliente y se presupuesta aparte. Medido por unidad instalada y probada.":
    "Installation of an electric or gas water heater, with its brackets, hydraulic connections and safety devices. Includes setting out and anchoring the brackets, verifying that the wall can carry the weight of the unit full, which is several times that of the unit empty, connecting the inlet and the outlet with shut-off valves and demountable unions to allow maintenance, fitting the safety relief valve with its discharge pipe carried away, the electrical or gas connection according to the type, filling, venting and testing the operation. The unit is selected by the client and priced separately. Measured per unit installed and tested.",

"Montaje del juego de accesorios de baño: toallero, portarrollos, jabonera, percha y repisa, fijados al enchapado. Incluye el replanteo de las alturas y posiciones de uso coordinadas con el despiece del enchapado para taladrar en el centro de la pieza y no sobre la junta ni cerca del canto, donde la cerámica se astilla, el taladrado con broca de vidrio a baja velocidad y sin percusión, la colocación de tacos y el montaje de los accesorios. Los accesorios los elige el cliente y se presupuestan aparte. Medido por juego instalado.":
    "Fitting the set of bathroom accessories: towel rail, toilet paper holder, soap dish, hook and shelf, fixed to the tiling. Includes setting out the heights and positions for use, coordinated with the setting out of the tiling so as to drill at the center of the tile and not on the joint or near the edge, where the ceramic chips, drilling with a glass drill bit at low speed and without hammer action, inserting the plugs and fitting the accessories. The accessories are selected by the client and priced separately. Measured per set installed.",

"Instalación de lavadero o poceta de servicio con su grifería, desagüe y soportes. Incluye la comprobación de la base o soportes que deben resistir el peso de la pieza llena de agua y con ropa, el nivelado, la conexión de la toma de agua con su llave, el montaje del desagüe con sifón, el sellado perimetral contra la pared y la prueba de estanqueidad y evacuación. El aparato y la grifería los elige el cliente y se presupuestan aparte. Medido por unidad instalada.":
    "Installation of a utility sink or service basin with its faucet, waste and supports. Includes checking the base or supports, which have to carry the weight of the unit full of water and laundry, leveling, connecting the water supply with its valve, fitting the waste with the trap, sealing the perimeter against the wall and testing the watertightness and the drainage. The fixture and the faucet are selected by the client and priced separately. Measured per unit installed.",

"Instalación de bidé o de ducha higiénica sobre puntos de agua y desagüe previamente ejecutados. Incluye el replanteo respetando las separaciones mínimas de uso respecto al inodoro y a los paramentos, el anclaje de la pieza, la conexión de agua fría y caliente con sus llaves, el montaje del desagüe y sifón en el caso del bidé, el sellado perimetral y la prueba de funcionamiento y estanqueidad. El aparato y la grifería los elige el cliente y se presupuestan aparte. Medido por unidad instalada.":
    "Installation of a bidet or a hand shower onto previously constructed water and waste points. Includes setting out and respecting the minimum clearances for use from the toilet and from the walls, anchoring the fixture, connecting the hot and cold with their valves, fitting the waste and the trap in the case of the bidet, sealing the perimeter and testing the operation and the watertightness. The fixture and the faucet are selected by the client and priced separately. Measured per unit installed.",

"Instalación de lavamanos con mueble y grifería. Incluye la conexión de agua y desagüe. Medido por unidad instalada.":
    "Installation of a lavatory with a cabinet and a faucet. Includes the water and waste connections. Measured per unit installed.",
"Instalación de inodoro de tanque. Incluye la conexión de agua y desagüe. Medido por unidad instalada.":
    "Installation of a close coupled toilet. Includes the water and waste connections. Measured per unit installed.",
"Instalación de grifería de ducha. Incluye la conexión. Medido por unidad instalada.":
    "Installation of a shower faucet. Includes the connection. Measured per unit installed.",
"Instalación de grifería de lavamanos. Incluye la conexión. Medido por unidad instalada.":
    "Installation of a lavatory faucet. Includes the connection. Measured per unit installed.",
"Instalación de grifería de cocina. Incluye la conexión. Medido por unidad instalada.":
    "Installation of a kitchen faucet. Includes the connection. Measured per unit installed.",
"Instalación de bidé con su grifería y desagüe. Incluye la conexión. Medido por unidad instalada.":
    "Installation of a bidet with its faucet and waste. Includes the connection. Measured per unit installed.",
"Instalación de grifería de bañera. Incluye la conexión. Medido por unidad instalada.":
    "Installation of a bathtub faucet. Includes the connection. Measured per unit installed.",
"Instalación de grifería de ducha exterior. Incluye la conexión. Medido por unidad instalada.":
    "Installation of an external shower faucet. Includes the connection. Measured per unit installed.",

# ── Saneamiento ───────────────────────────────────────────────────────────
"Instalación de tubería de PVC sanitario de 4 pulgadas para red de desagüe, colocada con la pendiente de proyecto. Incluye replanteo, cortes, limpieza y cementado de las uniones, accesorios como codos, yees y sifones, fijación mediante abrazaderas o apoyo sobre cama según el trazado, y prueba de estanqueidad de la red. No incluye la apertura de rozas ni la obra civil de canalización, que se valoran aparte. Medido en longitud realmente instalada.":
    "Installation of 4 inch PVC sanitary pipework for the drainage system, laid to the gradient specified. Includes setting out, cutting, cleaning and solvent cementing the joints, fittings such as bends, wyes and traps, fixing with pipe clips or bearing on a bed according to the run, and testing the system for watertightness. It does not include cutting chases or the civil work for the trench, which are priced separately. Measured by the length actually installed.",

"Instalación de trampa de grasa prefabricada en la red de desagüe de cocina, con sus conexiones de entrada y salida y su tapa registrable. Su función es retener las grasas antes de que lleguen a la red, donde se solidifican y terminan obstruyendo el colector. Incluye la excavación o preparación del alojamiento, la nivelación de la pieza, la conexión de entrada y salida respetando las cotas y el desnivel entre ellas, el macizado perimetral, la colocación de la tapa accesible para su limpieza periódica y la prueba de escurrimiento. Medido por unidad instalada.":
    "Installation of a prefabricated grease interceptor in the kitchen drainage, with its inlet and outlet connections and its removable cover. Its function is to hold back the fats before they reach the system, where they solidify and end up blocking the sewer. Includes excavation or preparing the housing, leveling the unit, connecting the inlet and the outlet respecting the levels and the drop between them, bedding the perimeter, placing the cover so that it stays accessible for periodic cleaning, and the flow test. Measured per unit installed.",

"Construcción o instalación de registro de aguas servidas en la red de desagüe, con su solera con media caña, paredes, tapa hermética y conexiones. El registro debe situarse en los cambios de dirección y en los tramos largos, porque es el único punto por donde se puede desobstruir la red sin romper piso. Incluye la excavación, la solera con la media caña de conducción que guía el flujo y evita la sedimentación, el levantamiento de paredes, el friso interior impermeabilizado, las conexiones con sus cotas y la tapa hermética a nivel de piso. Medido por unidad ejecutada.":
    "Construction or installation of an inspection chamber in the drainage system, with its benched base, walls, airtight cover and connections. The chamber has to be sited at changes of direction and on long runs, because it is the only point from which the system can be cleared without breaking up the floor. Includes excavation, the base with the benching that guides the flow and prevents siltation, building the walls, the waterproofed internal stucco, the connections at their levels and the airtight cover set flush with the floor. Measured per unit constructed.",

"Suministro e instalación de bajante de desagüe de PVC de 2 pulgadas. Incluye el montaje y la fijación. Medido por metro lineal instalado.":
    "Supply and installation of a 2 inch PVC waste stack. Includes assembly and fixing. Measured per meter installed.",
"Suministro e instalación de tubería de desagüe de PVC de 2 pulgadas. Incluye el montaje. Medido por metro lineal instalado.":
    "Supply and installation of 2 inch PVC waste pipework. Includes assembly. Measured per meter installed.",
"Suministro e instalación de montante de desagüe. Incluye el montaje. Medido por metro lineal instalado.":
    "Supply and installation of a waste stack. Includes assembly. Measured per meter installed.",
"Suministro e instalación de bajante de aguas lluvias. Incluye el montaje. Medido por metro lineal instalado.":
    "Supply and installation of a rainwater downpipe. Includes assembly. Measured per meter installed.",
"Suministro e instalación de canalón de aguas lluvias. Incluye el montaje. Medido por metro lineal instalado.":
    "Supply and installation of a rainwater gutter. Includes assembly. Measured per meter installed.",
"Instalación de tragante o sumidero de cubierta. Incluye la conexión. Medido por unidad instalada.":
    "Installation of a roof drain. Includes the connection. Measured per unit installed.",
"Instalación de canal de drenaje lineal. Incluye el montaje. Medido por metro lineal instalado.":
    "Installation of a linear drainage channel. Includes assembly. Measured per meter installed.",
"Ejecución de bajante de desagüe de 6 pulgadas., con conexión. Incluye la conexión y la fijación. Medido por metro lineal ejecutado/a.":
    "Installation of a 6 inch waste stack, with the connection. Includes the connection and fixing. Measured per meter constructed.",
}
