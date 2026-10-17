# -*- coding: utf-8 -*-
"""Descripciones — Equipamiento, mobiliario y señalización (capítulo
completo, 140).

Criterios de este lote:
  · «Mueble bajo» y «mueble alto» de cocina son base cabinet y wall
    cabinet, y esa es la pareja que ordena el capítulo.
  · «Mesón» es countertop en Estados Unidos, worktop en el Reino Unido y
    benchtop en Australia. La base puede ser cualquiera en un sitio y
    sonar rara en otro, así que la base es la americana y la variante
    hace el resto.
  · «Salpicadero» es backsplash en Estados Unidos y splashback en el
    Reino Unido. «Placa de cocción» es cooktop y hob. «Campana
    extractora» es range hood y cooker hood.
  · «Closet empotrado» es built-in closet en Estados Unidos y built-in
    wardrobe en el Reino Unido.
  · «Despiece» es cutting list, «canto aplicado» es edge banding y
    «corredera» es drawer slide. «Frentes con holguras uniformes» son
    door fronts with even reveals: reveals es la palabra de oficio para
    la holgura vista entre puertas.
  · «Tomar plantilla» es templating: el mesón de piedra se mide sobre el
    mueble ya instalado, nunca sobre plano.
  · «Flechar» de una repisa es sag. «Felpa» de una corredera es brush
    seal.
"""

LOTE = {
# ── Cocina ────────────────────────────────────────────────────────────────
"Fabricación e instalación de mueble bajo de cocina en melamina, con su estructura, puertas, gavetas, entrepaños y zócalo. Incluye la toma de medidas en obra comprobando plomos y escuadras, el despiece y corte con cantos aplicados, la previsión de los huecos y recortes para el paso de tuberías y tomas eléctricas antes del montaje, el armado de los módulos, la nivelación mediante patas regulables, la unión entre módulos, el montaje de puertas y gavetas con sus correderas y la regulación de frentes hasta obtener holguras uniformes. Medido en longitud de frente de mueble.":
    "Manufacture and installation of a melamine kitchen base cabinet, with its carcass, doors, drawers, shelves and plinth. Includes measuring on site and checking plumb and square, preparing the cutting list and cutting with edge banding, allowing for the openings and cut-outs for pipework and electrical outlets before assembly, assembling the units, leveling on adjustable legs, joining the units together, fitting the doors and drawers with their slides and adjusting the fronts until the reveals are even. Measured by the length of cabinet front.",

"Fabricación e instalación de mueble alto de cocina en melamina, con su estructura, puertas y entrepaños, colgado del paramento. Incluye la comprobación de que el paramento soporta la carga, ya que un mueble alto cargado pesa bastante y en tabique de yeso laminado exige refuerzo interior previo, el replanteo de la altura útil coordinada con el mesón y el salpicadero, el montaje del riel o de los soportes de colgar, el armado y colgado de los módulos, la nivelación y unión entre ellos, el montaje de puertas con bisagras regulables y la regulación de frentes. Medido en longitud de frente de mueble.":
    "Manufacture and installation of a melamine kitchen wall cabinet, with its carcass, doors and shelves, hung from the wall. Includes checking that the wall can carry the load, since a loaded wall cabinet is heavy and on a plasterboard partition needs internal strengthening beforehand, setting out the working height in coordination with the countertop and backsplash, fitting the hanging rail or brackets, assembling and hanging the units, leveling and joining them, fitting the doors on adjustable hinges and adjusting the fronts. Measured by the length of cabinet front.",

"Fabricación e instalación de isla o península de cocina, con su estructura, muebles a una o dos caras, y previsión de instalaciones. Incluye la coordinación previa de los puntos de agua, desagüe y electricidad que deben quedar dentro de la isla y que se ejecutan antes del piso, punto que si se pasa por alto obliga a picar el piso terminado, el anclaje de la estructura al piso para que no se desplace, el armado y nivelación de los módulos, el montaje de puertas y gavetas y los remates laterales. No incluye el mesón. Medido en longitud de isla.":
    "Manufacture and installation of a kitchen island or peninsula, with its carcass, cabinets to one or both faces, and provision for services. Includes prior coordination of the water, waste and electrical points that have to fall within the island and are installed before the floor, a point which if overlooked means breaking out the finished floor, anchoring the carcass to the floor so that it cannot move, assembling and leveling the units, fitting the doors and drawers and the end panels. The countertop is not included. Measured by the length of island.",

"Instalación de campana extractora de cocina, con su anclaje, conducción de salida al exterior y conexión eléctrica. Una campana cuya descarga se queda dentro del mueble alto o del cielo raso no extrae nada: recircula el aire graso y lo condensa donde descarga. Incluye el replanteo de la altura sobre la placa según el tipo de cocción, el anclaje al mueble o al paramento, la conducción de salida hasta el exterior con su rejilla y compuerta antirretorno, la conexión eléctrica y la prueba de funcionamiento y caudal. El equipo lo elige el cliente y se presupuesta aparte. Medido por unidad instalada.":
    "Installation of a kitchen range hood, with its fixing, the discharge duct to outside and the electrical connection. A hood that discharges into the wall cabinet or the ceiling extracts nothing: it recirculates greasy air and condenses it wherever it discharges. Includes setting out the height above the cooktop according to the type of cooking, fixing to the cabinet or to the wall, the discharge duct to outside with its grille and backdraft damper, the electrical connection and testing the operation and the flow rate. The unit is selected by the client and priced separately. Measured per unit installed.",

"Instalación de electrodoméstico empotrado en mueble de cocina, tal como horno, placa de cocción, microondas o lavavajillas, con sus conexiones. Incluye la verificación de que el hueco del mueble corresponde a las dimensiones y a la ventilación que exige el fabricante, requisito que si se ignora provoca sobrecalentamiento y la pérdida de la garantía, el ajuste del hueco si procede, el encastre y fijación del equipo, la conexión eléctrica, hidráulica o de gas según el caso y la puesta en marcha con prueba. El equipo lo elige el cliente y se presupuesta aparte. Medido por unidad instalada.":
    "Installation of a built-in appliance in a kitchen cabinet, such as an oven, cooktop, microwave or dishwasher, with its connections. Includes verifying that the cabinet opening matches the dimensions and the ventilation the manufacturer requires, a requirement which if ignored causes overheating and voids the warranty, adjusting the opening where necessary, fitting and fixing the appliance, the electrical, hydraulic or gas connection as applicable and setting it to work and testing it. The appliance is selected by the client and priced separately. Measured per unit installed.",

"Fabricación e instalación de alacena o despensa de cocina de altura completa, con sus entrepaños, gavetas o sistema extraíble. Incluye la toma de medidas en obra, el despiece y corte con cantos aplicados, el armado y anclaje del cuerpo al paramento y al piso, la nivelación, el montaje de entrepaños y de los sistemas extraíbles con sus guías, el montaje de puertas con su regulación y el remate superior contra el cielo raso. Medido en longitud de frente de alacena.":
    "Manufacture and installation of a full height kitchen pantry, with its shelves, drawers or pull-out system. Includes measuring on site, preparing the cutting list and cutting with edge banding, assembling and anchoring the carcass to the wall and to the floor, leveling, fitting the shelves and the pull-out systems with their runners, fitting the doors and adjusting them and the trim at the top against the ceiling. Measured by the length of pantry front.",

"Fabricación e instalación de mueble bajo de cocina en melamina, con puertas, gavetas y zócalo. Incluye toma de medidas, despiece, armado, nivelación y regulación de frentes.":
    "Manufacture and installation of a melamine kitchen base cabinet, with doors, drawers and plinth. Includes measuring, cutting list, assembly, leveling and adjustment of the fronts.",

"Fabricación e instalación de mueble alto de cocina en melamina, con puertas y entrepaños. Incluye despiece, armado y fijación a la pared.":
    "Manufacture and installation of a melamine kitchen wall cabinet, with doors and shelves. Includes cutting list, assembly and fixing to the wall.",

"Fabricación e instalación de isla o península de cocina en melamina, con mesón y gavetas. Incluye el armado, la nivelación y la fijación.":
    "Manufacture and installation of a melamine kitchen island or peninsula, with countertop and drawers. Includes assembly, leveling and fixing.",

"Instalación de campana extractora de cocina con conexión a la extracción y fijación. Incluye el replanteo y la fijación. El equipo lo elige el cliente.":
    "Installation of a kitchen range hood connected to the extract and fixed. Includes setting out and fixing. The unit is selected by the client.",

"Instalación de electrodoméstico empotrado (horno, lavaplatos, etc.) con conexión de agua, desagüe y electricidad según el equipo. Incluye la nivelación y la conexión.":
    "Installation of a built-in appliance (oven, dishwasher, etc.) with water, waste and electrical connections as required by the unit. Includes leveling and connection.",

"Fabricación e instalación de alacena o despensa de cocina en melamina, con entrepaños y puertas. Incluye el despiece y el armado.":
    "Manufacture and installation of a melamine kitchen pantry, with shelves and doors. Includes cutting list and assembly.",

"Fabricación e instalación de mueble bajo de cocina con hueco para fregadero, en melamina. Incluye el despiece, armado y el recorte para el fregadero.":
    "Manufacture and installation of a melamine kitchen base cabinet with an opening for the sink. Includes cutting list, assembly and the cut-out for the sink.",

"Fabricación e instalación de mueble de esquinero de cocina en melamina, con sistema de acceso al fondo. Incluye el despiece y el armado.":
    "Manufacture and installation of a melamine corner kitchen cabinet, with access to the back of the corner. Includes cutting list and assembly.",

"Fabricación e instalación de mueble de despensa con gavetas y entrepaños regulables, en melamina. Incluye el despiece y el armado.":
    "Manufacture and installation of a melamine pantry unit with drawers and adjustable shelves. Includes cutting list and assembly.",

"Fabricación y colocación de tapa de mesón de cocina en madera o melamina, con cantos aplicados. Incluye el despiece y la fijación.":
    "Manufacture and installation of a wood or melamine countertop, with edge banding. Includes cutting list and fixing.",

"Colocación de faldón o panel de remate entre mesón y mueble alto de cocina, en melamina o material a juego. Incluye el corte y la fijación.":
    "Installation of an infill panel between the countertop and the wall cabinet, in melamine or a matching material. Includes cutting and fixing.",

"Reparación de mueble de cocina con ajuste de herrajes, sustitución de piezas y regulación de frentes. Incluye la revisión y el ajuste.":
    "Repair of a kitchen cabinet with adjustment of the hardware, replacement of parts and adjustment of the fronts. Includes inspection and adjustment.",

# ── Mesones ───────────────────────────────────────────────────────────────
"Suministro e instalación de mesón de granito, cuarzo o piedra natural sobre muebles o estructura de apoyo, con su canto trabajado y los recortes de fregadero y placa. Incluye la plantilla en obra tomada sobre los muebles ya instalados y nivelados, nunca sobre medidas de plano, el mecanizado de recortes y del canto en taller, el transporte y presentado de las piezas, el nivelado con calzos, la unión de tramos con adhesivo al tono y el sellado perimetral contra la pared. El material lo elige el cliente y se presupuesta aparte. Medido en longitud de mesón.":
    "Supply and installation of a granite, quartz or natural stone countertop onto cabinets or a supporting structure, with its profiled edge and the sink and cooktop cut-outs. Includes templating on site off the cabinets once installed and leveled, never off dimensions from a drawing, machining the cut-outs and the edge in the workshop, transport and offering up of the pieces, leveling on shims, joining lengths with colour-matched adhesive and sealing the perimeter against the wall. The material is selected by the client and priced separately. Measured by the length of countertop.",

"Ejecución de mesón de concreto armado vaciado en sitio, con su estructura de apoyo, revestido con el acabado elegido. Es la solución tradicional y la más económica cuando el acabado es cerámico o de granito vaciado. Incluye la ejecución de la estructura de apoyo, el encofrado y armado del tablero, el vaciado y curado, la conformación de los huecos de fregadero y placa, el desencofrado y la regularización de la superficie lista para recibir el revestimiento. No incluye el revestimiento de acabado. Medido en longitud de mesón.":
    "Construction of a cast-in-place reinforced concrete countertop with its supporting structure, faced with the finish chosen. It is the traditional solution and the most economical where the finish is ceramic tile or cast-in-place terrazzo. Includes construction of the supporting structure, formwork and reinforcement of the slab, pouring and curing, forming the sink and cooktop openings, striking the formwork and preparing the surface ready to receive the finish. The finishing material is not included. Measured by the length of countertop.",

"Ejecución del salpicadero o zócalo posterior del mesón, en el mismo material del tablero o en el acabado elegido, con su sellado inferior. El sellado de la junta entre salpicadero y mesón es lo que impide que el agua se filtre por detrás y arruine el mueble bajo, que es el fallo más habitual en cocinas. Incluye el corte a medida, la colocación con adhesivo, el ajuste a las irregularidades de la pared, el sellado de la junta inferior con silicona sanitaria y el remate de esquinas. Medido en longitud realmente ejecutada.":
    "Construction of the backsplash or upstand to the countertop, in the same material as the top or in the finish chosen, with the bottom joint sealed. Sealing the joint between the backsplash and the countertop is what stops water getting in behind and ruining the base cabinet, the most common failure in kitchens. Includes cutting to size, bedding in adhesive, taking up the irregularities of the wall, sealing the bottom joint with sanitary silicone and finishing the corners. Measured by the length actually constructed.",

"Suministro e instalación de tope o mesón en el área de lavado o de servicio, con su recorte para el lavadero y su canto trabajado. Incluye la plantilla en obra sobre la base ya nivelada, el mecanizado del recorte, el presentado y nivelado, el sellado del canto de corte que es por donde el material absorbe humedad en un área permanentemente mojada, la fijación y el sellado perimetral contra la pared. El material lo elige el cliente y se presupuesta aparte. Medido en longitud de tope.":
    "Supply and installation of a countertop in the laundry or utility area, with its cut-out for the sink and its profiled edge. Includes templating on site off the base once leveled, machining the cut-out, offering up and leveling, sealing the cut edge, which is where the material takes up moisture in a permanently wet area, fixing and sealing the perimeter against the wall. The material is selected by the client and priced separately. Measured by the length of countertop.",

"Suministro y colocación de mesón de granito, cuarzo o piedra natural, con corte, cantos y perforaciones para fregadero. Incluye plantillas, corte y sellado. La piedra la elige el cliente.":
    "Supply and installation of a granite, quartz or natural stone countertop, cut and profiled and drilled for the sink. Includes templating, cutting and sealing. The stone is selected by the client.",

"Ejecución de mesón de concreto armado revestido, con encofrado y acabado. Incluye el armado, el vaciado y el acabado de la superficie.":
    "Construction of a reinforced concrete countertop with a facing, with formwork and finish. Includes reinforcement, pouring and finishing of the surface.",

"Colocación de salpicadero de mesón en el mismo material del mesón o revestimiento, con sellado de juntas. Incluye la fijación y el sellado.":
    "Installation of a countertop backsplash in the same material as the countertop or in the facing, with the joints sealed. Includes fixing and sealing.",

"Ejecución de tope o mesón de área de lavado en concreto o piedra, con pendiente al desagüe. Incluye el armado y el acabado.":
    "Construction of a concrete or stone countertop in the laundry area, with a fall to the drain. Includes reinforcement and finishing.",

"Colocación de mesón de cuarzo compacto con canto recto pulido y perforaciones. Incluye plantillas, corte y sellado. El cuarzo lo elige el cliente.":
    "Installation of an engineered quartz countertop with a polished square edge and the drill holes. Includes templating, cutting and sealing. The quartz is selected by the client.",

"Ejecución de mesón de granito vaciado en sitio, con encofrado, mezcla de grano y acabado pulido. Incluye el armado, el vaciado y el pulido.":
    "Construction of a cast-in-place terrazzo countertop, with formwork, the aggregate mix and a polished finish. Includes reinforcement, pouring and polishing.",

"Perforación de mesón de piedra o cuarzo para grifería o fregadero, con broca diamantada y refrigeración. Incluye el replanteo y el corte.":
    "Drilling a stone or quartz countertop for the faucet or sink, with a diamond core bit and water cooling. Includes setting out and cutting.",

"Pulido y abrillantado de mesón de piedra natural, con discos diamantados y sellador. Incluye la limpieza y el pulido.":
    "Polishing and buffing a natural stone countertop with diamond pads and sealer. Includes cleaning and polishing.",

"Sellado de juntas y encuentros de mesón con silicona sanitaria, para evitar filtraciones. Incluye la limpieza y el sellado.":
    "Sealing the joints and junctions of a countertop with sanitary silicone, to prevent water ingress. Includes cleaning and sealing.",

"Reparación de mesón de piedra con resane de fisuras, pulido y sellado. Incluye la reparación y el acabado.":
    "Repair of a stone countertop by filling cracks, polishing and sealing. Includes repair and finishing.",

"Ejecución de estructura de soporte de mesón en perfil metálico o mampostería, para apoyo del mesón. Incluye la fijación y el nivelado.":
    "Construction of a countertop support structure in metal sections or masonry, to carry the countertop. Includes fixing and leveling.",

"Colocación de salpicadero de vidrio o acrílico sobre mesón, con fijación y sellado. Incluye el corte y la fijación.":
    "Installation of a glass or acrylic backsplash over the countertop, fixed and sealed. Includes cutting and fixing.",

# ── Baño ──────────────────────────────────────────────────────────────────
"Fabricación o suministro e instalación de mueble de baño con su lavamanos integrado o sobrepuesto, colgado o de pie. Incluye la comprobación del refuerzo del paramento en los muebles suspendidos, que soportan el peso del mueble más el del lavamanos lleno, el replanteo de la altura útil, la previsión de los recortes de paso de desagüe y abastos, el anclaje, la nivelación, el montaje de puertas y gavetas con su regulación y el sellado perimetral contra la pared. El mueble y el lavamanos los elige el cliente y se presupuestan aparte. Medido por unidad instalada.":
    "Manufacture or supply and installation of a bathroom vanity unit with an integrated or overmount basin, wall hung or floor standing. Includes checking the strengthening of the wall for wall hung units, which carry the weight of the unit plus that of the basin when full, setting out the working height, allowing for the cut-outs for the waste and the supplies, anchoring, leveling, fitting the doors and drawers with adjustment and sealing the perimeter against the wall. The unit and the basin are selected by the client and priced separately. Measured per unit installed.",

"Instalación de espejo y botiquín de baño, fijados al paramento con sus anclajes. Incluye el replanteo de la altura de uso y de su centrado respecto al lavamanos, el taladrado sobre el enchapado con broca de vidrio a baja velocidad y sin percusión, evitando la junta y los cantos donde la pieza se astilla, la colocación de tacos, el montaje y nivelación y el sellado perimetral cuando corresponda. El espejo o botiquín lo elige el cliente y se presupuesta aparte. Medido por unidad instalada.":
    "Installation of a bathroom mirror and medicine cabinet, fixed to the wall with their anchors. Includes setting out the height in use and centring it over the basin, drilling through the tiling with a glass drill bit at low speed and without hammer action, avoiding the joint and the edges where the tile chips, inserting the wall plugs, fixing and leveling and sealing the perimeter where applicable. The mirror or cabinet is selected by the client and priced separately. Measured per unit installed.",

"Suministro e instalación de mesón de baño en piedra, cuarzo o material compacto, sobre mueble o estructura, con el recorte del lavamanos y su canto trabajado. Incluye la plantilla en obra sobre el mueble ya instalado, el mecanizado del recorte según sea lavamanos sobrepuesto, empotrado o bajo mesón, el presentado y nivelado, el sellado del canto de corte y el sellado perimetral contra la pared. El material lo elige el cliente y se presupuesta aparte. Medido en longitud de mesón.":
    "Supply and installation of a stone, quartz or solid surface vanity top onto a unit or structure, with the basin cut-out and its profiled edge. Includes templating on site off the unit once installed, machining the cut-out for an overmount, recessed or undermount basin, offering up and leveling, sealing the cut edge and sealing the perimeter against the wall. The material is selected by the client and priced separately. Measured by the length of vanity top.",

"Fabricación e instalación de mueble de baño con hueco para lavamanos, en melamina hidrófuga. Incluye el despiece, armado y fijación.":
    "Manufacture and installation of a moisture resistant melamine bathroom vanity unit with an opening for the basin. Includes cutting list, assembly and fixing.",

"Colocación de espejo y botiquín de baño, con fijación y sellado. Incluye el replanteo y la fijación. El espejo lo elige el cliente.":
    "Installation of a bathroom mirror and medicine cabinet, fixed and sealed. Includes setting out and fixing. The mirror is selected by the client.",

"Colocación de mesón de baño sobre mueble o estructura, con perforación para lavamanos y sellado. Incluye la colocación y el sellado.":
    "Installation of a vanity top onto a unit or structure, drilled for the basin and sealed. Includes installation and sealing.",

"Fabricación e instalación de mueble de baño suspendido, con fijación a la pared mediante escuadras. Incluye el armado y la fijación.":
    "Manufacture and installation of a wall hung bathroom vanity unit, fixed to the wall on brackets. Includes assembly and fixing.",

"Instalación de botiquín de baño empotrado, con apertura del hueco y fijación. Incluye la apertura y el remate del hueco.":
    "Installation of a recessed bathroom cabinet, including forming the opening and fixing. Includes forming and finishing the opening.",

"Instalación de espejo de baño con iluminación integrada, con conexión eléctrica y fijación. Incluye la conexión y la fijación.":
    "Installation of a bathroom mirror with integral lighting, with the electrical connection and fixing. Includes connection and fixing.",

"Colocación de repisa de baño en melamina o madera, con fijación a la pared. Incluye el corte y la fijación.":
    "Installation of a melamine or wood bathroom shelf, fixed to the wall. Includes cutting and fixing.",

"Fabricación e instalación de gabinete alto de baño en melamina hidrófuga, con puertas y entrepaños. Incluye el despiece y el armado.":
    "Manufacture and installation of a moisture resistant melamine bathroom wall cabinet, with doors and shelves. Includes cutting list and assembly.",

"Colocación de accesorio de baño (toallero, jabonera, percha) con fijación a la pared. Incluye el replanteo y la fijación.":
    "Installation of a bathroom accessory (towel rail, soap dish, hook) fixed to the wall. Includes setting out and fixing.",

"Fabricación e instalación de mueble de lavadero con hueco para fregadero, en melamina hidrófuga. Incluye el despiece y el armado.":
    "Manufacture and installation of a moisture resistant melamine laundry unit with an opening for the sink. Includes cutting list and assembly.",

"Aplicación de lámina o recubrimiento impermeable sobre mueble de baño, para proteger la melamina de la humedad. Incluye el corte y la fijación.":
    "Application of a waterproof sheet or coating to a bathroom cabinet, to protect the melamine from moisture. Includes cutting and fixing.",

"Reparación de mueble de baño con ajuste de herrajes y sustitución de piezas dañadas. Incluye la revisión y el ajuste.":
    "Repair of a bathroom cabinet with adjustment of the hardware and replacement of damaged parts. Includes inspection and adjustment.",

"Colocación de espejo de cuerpo entero de baño, con fijación y sellado. Incluye el replanteo y la fijación. El espejo lo elige el cliente.":
    "Installation of a full length bathroom mirror, fixed and sealed. Includes setting out and fixing. The mirror is selected by the client.",

# ── Closets ───────────────────────────────────────────────────────────────
"Fabricación e instalación de closet empotrado a medida en tablero de melamina, con su estructura, entrepaños, barras y cajones, según despiece acordado. Incluye la toma de medidas en obra comprobando plomos y escuadras del hueco, el despiece y corte de los tableros con cantos aplicados, el montaje de la estructura nivelada y aplomada mediante calzos, el ajuste al paramento con tapajuntas que absorbe las irregularidades del muro, el montaje de entrepaños, barras y cajones con sus correderas y la regulación final. Medido en superficie de frente de closet.":
    "Manufacture and installation of a built-in closet to measure in melamine board, with its carcass, shelves, hanging rails and drawers, to the cutting list agreed. Includes measuring on site and checking the opening for plumb and square, preparing the cutting list and cutting the boards with edge banding, erecting the carcass level and plumb on shims, taking up the irregularities of the wall with a scribe, fitting the shelves, rails and drawers with their slides and the final adjustment. Measured by the area of closet front.",

"Suministro y montaje de puerta corrediza de closet con su riel superior e inferior, carros, hojas y tiradores. Incluye la nivelación del riel superior, que es el que soporta el peso y del que depende que las hojas no se descuelguen ni rocen, el montaje de la guía inferior, el colgado de las hojas con sus carros regulables, el ajuste de la verticalidad y del solape entre hojas y la colocación de topes y felpas. Medido en superficie realmente ejecutada.":
    "Supply and installation of a sliding closet door with its top and bottom tracks, carriers, door leaves and pulls. Includes leveling the top track, which carries the weight and on which it depends that the leaves neither drop nor drag, fitting the bottom guide, hanging the leaves on their adjustable carriers, adjusting the verticality and the overlap between leaves and fitting the stops and brush seals. Measured by the area actually carried out.",

"Fabricación y montaje de entrepaños, cajoneras, zapateras y organizadores interiores de closet en melamina, con sus soportes y herrajes. Incluye el despiece según la distribución acordada, el corte y canteado, el replanteo de las alturas útiles, el montaje de soportes y entrepaños nivelados, el montaje de cajones con sus correderas y la regulación de frentes. Medido en longitud de entrepaño u organizador realmente instalado.":
    "Manufacture and fitting of melamine closet shelves, drawer units, shoe storage and internal organisers, with their supports and hardware. Includes preparing the cutting list to the layout agreed, cutting and edging, setting out the working heights, fitting the supports and shelves level, fitting the drawers on their slides and adjusting the fronts. Measured by the length of shelf or organiser actually installed.",

"Fabricación e instalación de closet empotrado a medida en melamina, con puertas, entrepaños y barra de colgar. Incluye el despiece y el armado.":
    "Manufacture and installation of a built-in closet to measure in melamine, with doors, shelves and a hanging rail. Includes cutting list and assembly.",

"Fabricación y colocación de puerta corrediza de closet, con riel superior e inferior y carros. Incluye el montaje y la regulación.":
    "Manufacture and installation of a sliding closet door, with top and bottom tracks and carriers. Includes assembly and adjustment.",

"Colocación de entrepaños y organizadores interiores de closet, con soportes regulables. Incluye el corte y la fijación.":
    "Installation of closet shelves and internal organisers, with adjustable supports. Includes cutting and fixing.",

"Fabricación e instalación de closet de vestidor con cajoneras, barras y entrepaños, en melamina. Incluye el despiece y el armado.":
    "Manufacture and installation of a melamine walk-in closet with drawer units, hanging rails and shelves. Includes cutting list and assembly.",

"Fabricación y colocación de puerta abatible de closet, con bisagras y tirador. Incluye el montaje y la regulación.":
    "Manufacture and installation of a hinged closet door, with hinges and a pull. Includes assembly and adjustment.",

"Colocación de barra de colgar y soportes de closet, con fijación a los laterales. Incluye el replanteo y la fijación.":
    "Installation of a hanging rail and closet supports, fixed to the sides. Includes setting out and fixing.",

"Fabricación e instalación de zapatero empotrado en melamina, con entrepaños inclinados. Incluye el despiece y el armado.":
    "Manufacture and installation of a built-in melamine shoe cabinet, with sloping shelves. Includes cutting list and assembly.",

"Fabricación e instalación de alacena o armario de almacenamiento en melamina, con puertas y entrepaños. Incluye el despiece y el armado.":
    "Manufacture and installation of a melamine storage cupboard, with doors and shelves. Includes cutting list and assembly.",

"Fabricación e instalación de mueble de dormitorio a medida (gavetero) en melamina, con gavetas y tiradores. Incluye el despiece y el armado.":
    "Manufacture and installation of a melamine bedroom unit to measure (chest of drawers), with drawers and pulls. Includes cutting list and assembly.",

"Colocación de entrepaño flotante de pared en melamina, con soportes ocultos. Incluye el replanteo, el corte y la fijación.":
    "Installation of a melamine floating wall shelf, on concealed supports. Includes setting out, cutting and fixing.",

"Fabricación y colocación de puerta de closet con espejo integrado, con bisagras o corredera. Incluye el montaje y la regulación.":
    "Manufacture and installation of a closet door with an integrated mirror, hinged or sliding. Includes assembly and adjustment.",

"Colocación de organizador de alacena con canastillas extraíbles y soportes. Incluye la fijación y la regulación.":
    "Installation of a pantry organiser with pull-out baskets and supports. Includes fixing and adjustment.",

"Reparación de closet o armario con ajuste de puertas, sustitución de herrajes y regulación. Incluye la revisión y el ajuste.":
    "Repair of a closet or cupboard with adjustment of the doors, replacement of hardware and adjustment. Includes inspection and adjustment.",

# ── Electrodomésticos ─────────────────────────────────────────────────────
"Instalación de horno empotrado con conexión eléctrica de fuerza y fijación en el módulo. Incluye la conexión y la fijación. El equipo lo elige el cliente.":
    "Installation of a built-in oven with the power connection and fixing into the unit. Includes connection and fixing. The appliance is selected by the client.",

"Instalación de lavaplatos empotrado con conexión de agua, desagüe y electricidad. Incluye la nivelación y la conexión. El equipo lo elige el cliente.":
    "Installation of a built-in dishwasher with water, waste and electrical connections. Includes leveling and connection. The appliance is selected by the client.",

"Instalación de nevera empotrada con conexión eléctrica y fijación en el módulo. Incluye la conexión y la fijación. El equipo lo elige el cliente.":
    "Installation of a built-in refrigerator with the electrical connection and fixing into the unit. Includes connection and fixing. The appliance is selected by the client.",

"Instalación de cocina eléctrica empotrada con circuito de fuerza dedicado y fijación. Incluye la conexión y la fijación. El equipo lo elige el cliente.":
    "Installation of a built-in range with a dedicated power circuit and fixing. Includes connection and fixing. The appliance is selected by the client.",

"Instalación de microondas empotrado con conexión eléctrica y fijación. Incluye la conexión y la fijación. El equipo lo elige el cliente.":
    "Installation of a built-in microwave with the electrical connection and fixing. Includes connection and fixing. The appliance is selected by the client.",

"Instalación de calentador de agua eléctrico con conexión hidráulica y eléctrica. Incluye la conexión y la fijación. El equipo lo elige el cliente.":
    "Installation of an electric water heater with the hydraulic and electrical connections. Includes connection and fixing. The appliance is selected by the client.",

"Instalación de calentador de agua a gas con conexión de gas, agua y evacuación. Incluye la conexión y la fijación. El equipo lo elige el cliente.":
    "Installation of a gas water heater with the gas, water and flue connections. Includes connection and fixing. The appliance is selected by the client.",

"Instalación de extractor de aire de cocina con conducto de evacuación y fijación. Incluye la conexión y la fijación. El equipo lo elige el cliente.":
    "Installation of a kitchen extractor fan with the discharge duct and fixing. Includes connection and fixing. The appliance is selected by the client.",

"Ejecución de punto de conexión de gas para cocina, con tubería, llave de corte y prueba de estanqueidad. Incluye la conexión y la prueba.":
    "Installation of a gas connection point for the kitchen, with pipework, a shut-off valve and a tightness test. Includes connection and testing.",

"Ejecución de circuito eléctrico de fuerza para cocina, con cableado, protección y toma. Incluye el cableado y la conexión.":
    "Installation of a power circuit for the kitchen, with cabling, protection and an outlet. Includes cabling and connection.",

"Instalación de lavadora con conexión de agua, desagüe y electricidad. Incluye la nivelación y la conexión. El equipo lo elige el cliente.":
    "Installation of a washing machine with water, waste and electrical connections. Includes leveling and connection. The appliance is selected by the client.",

"Instalación de secadora con conexión eléctrica y de evacuación. Incluye la conexión y la fijación. El equipo lo elige el cliente.":
    "Installation of a dryer with the electrical and discharge connections. Includes connection and fixing. The appliance is selected by the client.",

"Instalación de triturador de cocina con conexión de desagüe y electricidad. Incluye la conexión y la fijación. El equipo lo elige el cliente.":
    "Installation of a garbage disposal with the waste and electrical connections. Includes connection and fixing. The appliance is selected by the client.",

"Instalación de filtro de agua de cocina con conexión a la red y fijación. Incluye la conexión y la fijación. El equipo lo elige el cliente.":
    "Installation of a kitchen water filter connected to the mains and fixed. Includes connection and fixing. The appliance is selected by the client.",

# ── Accesibilidad ─────────────────────────────────────────────────────────
"Suministro e instalación de barra de apoyo de acero inoxidable en baño accesible, anclada al paramento. El anclaje es lo crítico: una barra de apoyo debe resistir el peso completo de una persona apoyándose o cayendo sobre ella, de modo que la fijación con tacos plásticos sobre yeso laminado sin refuerzo interior no cumple ninguna función más que decorativa. Incluye la comprobación o ejecución del refuerzo del soporte, el replanteo de la altura y posición normalizadas, el taladrado, el anclaje mecánico o químico según el soporte y la prueba de carga. Medido por unidad instalada.":
    "Supply and installation of a stainless steel grab bar in an accessible bathroom, anchored to the wall. The anchorage is the critical part: a grab bar has to take the full weight of a person leaning on it or falling against it, so fixing it with plastic plugs into plasterboard without internal strengthening serves no purpose beyond the decorative. Includes checking or providing the strengthening of the backing, setting out the standard height and position, drilling, mechanical or chemical anchoring depending on the substrate and load testing. Measured per unit installed.",

"Suministro y montaje del juego de accesorios y herrajes complementarios del mobiliario: tiradores, organizadores, bisagras de cierre suave, sistemas de elevación y topes. Incluye el replanteo, el pretaladrado con plantilla para garantizar la alineación de los tiradores en todos los frentes, que es lo que se nota a simple vista en un mueble bien terminado, el montaje y la regulación final de cierres y amortiguadores. Medido por juego instalado.":
    "Supply and fitting of the set of complementary accessories and hardware for the cabinetry: pulls, organisers, soft close hinges, lift systems and stops. Includes setting out, pilot drilling with a jig to ensure the pulls line up across every front, which is what is immediately obvious in a well finished cabinet, fitting and final adjustment of the catches and soft closers. Measured per set installed.",

"Colocación de barra de apoyo de acero inoxidable para accesibilidad en baño, con fijación reforzada a la pared. Incluye el replanteo y la fijación.":
    "Installation of a stainless steel accessibility grab bar in a bathroom, with strengthened fixing to the wall. Includes setting out and fixing.",

"Colocación de juego de accesorios y herrajes de mobiliario (tiradores, bisagras, soportes), con fijación. Incluye el replanteo y la fijación.":
    "Installation of a set of cabinet accessories and hardware (pulls, hinges, supports), fixed. Includes setting out and fixing.",

"Colocación de asiento abatible de ducha para accesibilidad, con fijación reforzada. Incluye el replanteo y la fijación. El asiento lo elige el cliente.":
    "Installation of a folding shower seat for accessibility, with strengthened fixing. Includes setting out and fixing. The seat is selected by the client.",

"Colocación de barra de apoyo en ducha o bañera para accesibilidad, con fijación reforzada. Incluye el replanteo y la fijación.":
    "Installation of a grab bar in a shower or bathtub for accessibility, with strengthened fixing. Includes setting out and fixing.",

"Colocación de barra de apoyo abatible o fija en inodoro, con fijación reforzada. Incluye el replanteo y la fijación.":
    "Installation of a folding or fixed grab bar at a toilet, with strengthened fixing. Includes setting out and fixing.",

"Colocación de pasamanos de acero inoxidable en pasillo para accesibilidad, con fijación reforzada. Incluye el replanteo y la fijación.":
    "Installation of a stainless steel handrail in a corridor for accessibility, with strengthened fixing. Includes setting out and fixing.",

"Colocación de rampa portátil de acceso para accesibilidad, con anclaje y fijación. Incluye la colocación y el anclaje.":
    "Installation of a portable access ramp for accessibility, anchored and fixed. Includes placing and anchoring.",

"Instalación de alarma o timbre de asistencia de baño para accesibilidad, con cableado y pulsador. Incluye la instalación y la conexión.":
    "Installation of an assistance alarm or call bell in a bathroom for accessibility, with cabling and a push button. Includes installation and connection.",

"Colocación de soporte de ducha teléfono accesible, con fijación reforzada. Incluye el replanteo y la fijación.":
    "Installation of an accessible hand shower holder, with strengthened fixing. Includes setting out and fixing.",

"Colocación de placa de rotulación en braille para accesibilidad, con fijación. Incluye el replanteo y la fijación.":
    "Installation of a braille sign plate for accessibility, fixed. Includes setting out and fixing.",

"Instalación de elevador de piscina o bañera para accesibilidad, con anclaje y fijación. Incluye la fijación. El equipo lo elige el cliente.":
    "Installation of a pool or bath lift for accessibility, anchored and fixed. Includes fixing. The unit is selected by the client.",

"Reparación de barra de apoyo con refijación o sustitución de anclajes. Incluye la revisión y la refijación.":
    "Repair of a grab bar by refixing or replacing the anchors. Includes inspection and refixing.",

# ── Señalización ──────────────────────────────────────────────────────────
"Demarcación de líneas, símbolos y zonas en piso con pintura de tráfico, para estacionamientos, circulaciones y áreas de seguridad. Incluye la limpieza y desengrasado de la franja, el replanteo y encintado de las líneas, la aplicación de la pintura en dos manos con el espesor que garantiza la durabilidad frente al rodado, el retiro de la cinta en fresco para obtener el borde limpio y el acordonamiento hasta el secado. Medido en longitud de línea realmente ejecutada.":
    "Marking out of lines, symbols and areas on the floor with traffic paint, for parking, circulation and safety areas. Includes cleaning and degreasing the strip, setting out and masking the lines, applying the paint in two coats at the thickness that gives durability under traffic, removing the tape while the paint is wet to get a clean edge and barring off until dry. Measured by the length of line actually marked.",

"Pintado de demarcación y señalización en piso con pintura de tráfico, con plantillas y enmascarado. Incluye la limpieza y la aplicación.":
    "Painting of floor marking and signage with traffic paint, using stencils and masking. Includes cleaning and application.",

"Colocación de señal de evacuación y emergencia, con fijación y rotulación. Incluye el replanteo y la fijación.":
    "Installation of an escape and emergency sign, fixed and lettered. Includes setting out and fixing.",

"Colocación de señal de identificación de áreas y zonas interiores, con fijación. Incluye el replanteo y la fijación.":
    "Installation of a sign identifying interior areas and zones, fixed. Includes setting out and fixing.",

"Colocación de directorio de planta con rotulación, con fijación. Incluye el replanteo y la fijación.":
    "Installation of a floor directory with lettering, fixed. Includes setting out and fixing.",

"Colocación de señal exterior de parcela o local, con fijación y anclaje. Incluye el replanteo y la fijación.":
    "Installation of an external sign for the plot or premises, fixed and anchored. Includes setting out and fixing.",

"Colocación de señal de prohibición o advertencia, con fijación. Incluye el replanteo y la fijación.":
    "Installation of a prohibition or warning sign, fixed. Includes setting out and fixing.",

"Pintado de demarcación de puestos de estacionamiento con pintura de tráfico. Incluye el replanteo y la aplicación.":
    "Painting of parking bay markings with traffic paint. Includes setting out and application.",

"Colocación de señalización de escaleras y pasamanos, con fijación. Incluye el replanteo y la fijación.":
    "Installation of signage for stairs and handrails, fixed. Includes setting out and fixing.",

"Colocación de placa de identificación de puerta, con fijación. Incluye el replanteo y la fijación.":
    "Installation of a door identification plate, fixed. Includes setting out and fixing.",

"Colocación de señal fotoluminiscente de evacuación, con fijación. Incluye el replanteo y la fijación.":
    "Installation of a photoluminescent escape sign, fixed. Includes setting out and fixing.",

"Pintado de demarcación de zona de seguridad con pintura de tráfico y plantillas. Incluye la limpieza y la aplicación.":
    "Painting of safety zone markings with traffic paint and stencils. Includes cleaning and application.",

"Colocación de rotulación corporativa de fachada, con anclaje y fijación. Incluye el replanteo y la fijación.":
    "Installation of corporate signage on a facade, anchored and fixed. Includes setting out and fixing.",

"Colocación de señalización de extintores y equipos de seguridad, con fijación. Incluye el replanteo y la fijación.":
    "Installation of signage for fire extinguishers and safety equipment, fixed. Includes setting out and fixing.",

# ── Mobiliario fijo y comercial ───────────────────────────────────────────
"Fabricación e instalación de repisa o estantería fija en melamina o madera, con sus soportes anclados al paramento. Incluye el replanteo de la altura y de la separación entre soportes en función del espesor del tablero y de la carga prevista, ya que una repisa con soportes demasiado separados flecha de forma permanente, el anclaje de los soportes con el sistema adecuado al tipo de muro, el corte y canteado del tablero, su colocación y nivelación y el remate de cantos vistos. Medido en longitud realmente instalada.":
    "Manufacture and installation of a fixed shelf or shelving unit in melamine or wood, with its supports anchored to the wall. Includes setting out the height and the spacing of the supports according to the thickness of the board and the load expected, since a shelf with supports too far apart sags permanently, anchoring the supports with the system suited to the type of wall, cutting and edging the board, placing and leveling it and finishing the exposed edges. Measured by the length actually installed.",

"Fabricación e instalación de mueble fijo a medida en melamina o madera, según despiece acordado con el cliente, para recibidores, salas, escritorios u otros usos. Incluye la toma de medidas en obra, el despiece y corte con cantos aplicados, el armado de la estructura, el anclaje y nivelación al paramento y al piso, el montaje de puertas, gavetas y entrepaños con sus herrajes, la regulación de frentes y el remate con tapajuntas que absorbe las irregularidades del muro. Medido en superficie de frente de mueble.":
    "Manufacture and installation of a fixed cabinet to measure in melamine or wood, to the cutting list agreed with the client, for entrance halls, living rooms, desks or other uses. Includes measuring on site, preparing the cutting list and cutting with edge banding, assembling the carcass, anchoring and leveling it to the wall and to the floor, fitting the doors, drawers and shelves with their hardware, adjusting the fronts and finishing with a scribe that takes up the irregularities of the wall. Measured by the area of cabinet front.",

"Fabricación y colocación de repisa o estantería fija, en melamina o madera, con fijación a la pared. Incluye el corte y la fijación.":
    "Manufacture and installation of a fixed shelf or shelving unit, in melamine or wood, fixed to the wall. Includes cutting and fixing.",

"Fabricación e instalación de mueble fijo a medida en melamina, con puertas y entrepaños. Incluye el despiece y el armado.":
    "Manufacture and installation of a fixed cabinet to measure in melamine, with doors and shelves. Includes cutting list and assembly.",

"Instalación de mampara divisoria de oficina, con perfilería y paneles. Incluye el replanteo y el montaje. El sistema lo elige el cliente.":
    "Installation of an office partition screen, with framing and panels. Includes setting out and assembly. The system is selected by the client.",

"Fabricación e instalación de mostrador de atención en melamina o madera, con mesón. Incluye el despiece y el armado.":
    "Manufacture and installation of a reception counter in melamine or wood, with a countertop. Includes cutting list and assembly.",

"Montaje de estantería metálica de almacén, con niveles y fijación. Incluye el replanteo y el montaje.":
    "Assembly of metal warehouse shelving, with the levels and fixing. Includes setting out and assembly.",

"Fabricación e instalación de mueble de recepción en melamina, con mesón y frentes. Incluye el despiece y el armado.":
    "Manufacture and installation of a melamine reception unit, with a countertop and fronts. Includes cutting list and assembly.",

"Montaje de taquilla o casillero de personal, con fijación. Incluye el montaje y la fijación.":
    "Assembly of staff lockers, fixed. Includes assembly and fixing.",

"Fabricación e instalación de barra de bar o cafetería en melamina o madera, con mesón. Incluye el despiece y el armado.":
    "Manufacture and installation of a bar or cafeteria counter in melamine or wood, with a countertop. Includes cutting list and assembly.",

"Fabricación e instalación de mueble de vitrina expositora con vidrio y puertas. Incluye el despiece y el armado.":
    "Manufacture and installation of a glazed display cabinet with doors. Includes cutting list and assembly.",

"Colocación de panel de corcho o pizarra de oficina, con fijación a la pared. Incluye el replanteo y la fijación.":
    "Installation of a cork or whiteboard panel in an office, fixed to the wall. Includes setting out and fixing.",

"Fabricación e instalación de mostrador de exhibición comercial, en melamina con vidrio. Incluye el despiece y el armado.":
    "Manufacture and installation of a commercial display counter, in melamine with glass. Includes cutting list and assembly.",

"Montaje de góndola o estantería comercial, con niveles y fijación. Incluye el replanteo y el montaje.":
    "Assembly of gondola shelving or shop shelving, with the levels and fixing. Includes setting out and assembly.",

"Fabricación e instalación de mueble de área común en melamina, con asiento o superficie de apoyo. Incluye el despiece y el armado.":
    "Manufacture and installation of a melamine unit for a common area, with seating or a work surface. Includes cutting list and assembly.",

"Reparación de mobiliario fijo comercial con ajuste de herrajes y sustitución de piezas. Incluye la revisión y el ajuste.":
    "Repair of commercial fitted furniture with adjustment of the hardware and replacement of parts. Includes inspection and adjustment.",

"Fabricación e instalación de asiento o banqueta fija en melamina o madera, con fijación. Incluye el despiece y la fijación.":
    "Manufacture and installation of fixed seating or a bench in melamine or wood, fixed. Includes cutting list and fixing.",

# ── Deportivo y exterior ──────────────────────────────────────────────────
"Instalación de equipamiento de parque infantil, con anclaje al piso y fijación. Incluye la fijación. El equipo lo elige el cliente.":
    "Installation of playground equipment, anchored to the ground and fixed. Includes fixing. The equipment is selected by the client.",

"Pintado de cancha deportiva con demarcación de líneas y pintura de tráfico. Incluye la limpieza y la aplicación.":
    "Painting of a sports court with line markings and traffic paint. Includes cleaning and application.",

"Instalación de aro o tablero de baloncesto, con fijación a poste o pared. Incluye la fijación. El equipo lo elige el cliente.":
    "Installation of a basketball hoop or backboard, fixed to a post or wall. Includes fixing. The equipment is selected by the client.",

"Instalación de red o portería deportiva, con anclaje y fijación. Incluye la fijación. El equipo lo elige el cliente.":
    "Installation of a sports net or goal, anchored and fixed. Includes fixing. The equipment is selected by the client.",

"Instalación de aparato de gimnasio exterior, con anclaje y fijación. Incluye la fijación. El equipo lo elige el cliente.":
    "Installation of external exercise equipment, anchored and fixed. Includes fixing. The equipment is selected by the client.",

"Colocación de banca de descanso exterior, con anclaje y fijación. Incluye la fijación. El mobiliario lo elige el cliente.":
    "Installation of an external bench, anchored and fixed. Includes fixing. The furniture is selected by the client.",

"Colocación de mesa de picnic exterior, con anclaje y fijación. Incluye la fijación. El mobiliario lo elige el cliente.":
    "Installation of an external picnic table, anchored and fixed. Includes fixing. The furniture is selected by the client.",

"Instalación de portería de fútbol sala, con anclaje y fijación. Incluye la fijación. El equipo lo elige el cliente.":
    "Installation of an indoor soccer goal, anchored and fixed. Includes fixing. The equipment is selected by the client.",

"Instalación de columpio o tobogán de parque, con anclaje y fijación. Incluye la fijación. El equipo lo elige el cliente.":
    "Installation of a park swing or slide, anchored and fixed. Includes fixing. The equipment is selected by the client.",

"Instalación de equipo de gimnasio interior, con anclaje y fijación. Incluye la fijación. El equipo lo elige el cliente.":
    "Installation of indoor gym equipment, anchored and fixed. Includes fixing. The equipment is selected by the client.",

"Colocación de banca de jugadores de cancha, con anclaje y fijación. Incluye la fijación. El mobiliario lo elige el cliente.":
    "Installation of a team bench for a court, anchored and fixed. Includes fixing. The furniture is selected by the client.",

"Instalación de equipamiento de juegos de salón (mesa de billar, etc.), con nivelación y fijación. Incluye la instalación. El equipo lo elige el cliente.":
    "Installation of recreation equipment for a games room (billiard table, etc.), leveled and fixed. Includes installation. The equipment is selected by the client.",

"Colocación de soporte de bicicletas exterior, con anclaje y fijación. Incluye la fijación. El mobiliario lo elige el cliente.":
    "Installation of an external bicycle rack, anchored and fixed. Includes fixing. The furniture is selected by the client.",

"Pintado de demarcación de cancha deportiva con líneas y pintura de tráfico. Incluye el replanteo y la aplicación.":
    "Painting of sports court line markings with traffic paint. Includes setting out and application.",

"Instalación de equipamiento recreativo de área común, con anclaje y fijación. Incluye la fijación. El equipo lo elige el cliente.":
    "Installation of recreation equipment for a common area, anchored and fixed. Includes fixing. The equipment is selected by the client.",
}
