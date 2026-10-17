# -*- coding: utf-8 -*-
"""Descripciones — Remates y ayudas (capítulo completo, 120).

Criterios de este lote:
  · «Ayuda de albañilería» es builder's work, que es una partida con
    nombre propio en el mundo anglosajón: el trabajo de albañilería que
    una instalación necesita y que el instalador no hace.
  · «Roza» y «regata» son las dos chase: la ranura que se abre para
    meter una tubería o un cable. «Tapado» es making good, dejar la
    superficie como estaba.
  · «Recibido» es bedding and fixing: fijar con mortero y nivelar.
  · «Sellado cortafuego» es firestopping, una sola palabra, y el material
    es intumescent mastic.
  · «Forrado» es boxing in cuando se oculta una tubería o una viga tras
    una placa.
  · «Alféizar» es window sill y «vierteaguas» es weather sill: el
    alféizar es la pieza interior o la repisa, el vierteaguas es el que
    saca el agua hacia fuera.
"""

LOTE = {
# ── Ayudas de albañilería ─────────────────────────────────────────────────
"Ayuda de albañilería para instalación eléctrica: rozas, tapado y resane. Incluye la apertura de rozas y el resane. Medido por unidad de ayuda.":
    "Builder's work for the electrical installation: chases, making good and patching. Includes forming the chases and making good. Measured per unit of builder's work.",
"Ayuda de albañilería para instalación sanitaria: pasos, tapado y resane. Incluye la apertura de pasos y el resane. Medido por unidad de ayuda.":
    "Builder's work for the plumbing installation: penetrations, making good and patching. Includes forming the penetrations and making good. Measured per unit of builder's work.",
"Ayuda de albañilería para instalación de climatización: pasos y tapado. Incluye la apertura de pasos y el resane. Medido por unidad de ayuda.":
    "Builder's work for the HVAC installation: penetrations and making good. Includes forming the penetrations and making good. Measured per unit of builder's work.",
"Ayuda de albañilería para instalación de gas: rozas y tapado. Incluye la apertura de rozas y el resane. Medido por unidad de ayuda.":
    "Builder's work for the gas installation: chases and making good. Includes forming the chases and making good. Measured per unit of builder's work.",
"Ayuda de albañilería para instalación de datos: pasos y tapado. Incluye la apertura de pasos y el resane. Medido por unidad de ayuda.":
    "Builder's work for the data installation: penetrations and making good. Includes forming the penetrations and making good. Measured per unit of builder's work.",
"Resane general de paramentos tras el paso de instalaciones. Incluye el tapado y el acabado. Medido por metro cuadrado resanado.":
    "General patching of surfaces after the services have been run. Includes making good and finishing. Measured per square meter patched.",
"Ayuda de albañilería para instalación contra incendios: pasos y tapado. Incluye la apertura de pasos y el resane. Medido por unidad de ayuda.":
    "Builder's work for the fire protection installation: penetrations and making good. Includes forming the penetrations and making good. Measured per unit of builder's work.",
"Ayuda de albañilería para instalación de bombeo: bases y pasos. Incluye la formación de bases y el resane. Medido por unidad de ayuda.":
    "Builder's work for the pumping installation: bases and penetrations. Includes forming the bases and making good. Measured per unit of builder's work.",
"Ayuda de albañilería para instalación de ventilación: pasos y tapado. Incluye la apertura de pasos y el resane. Medido por unidad de ayuda.":
    "Builder's work for the ventilation installation: penetrations and making good. Includes forming the penetrations and making good. Measured per unit of builder's work.",
"Apertura y tapado de paso de instalación en muro. Incluye la apertura y el resane. Medido por metro lineal ejecutado.":
    "Forming and making good a penetration for services in a wall. Includes forming the penetration and making good. Measured per meter constructed.",
"Apertura y tapado de paso de instalación en losa. Incluye la apertura y el resane. Medido por metro lineal ejecutado.":
    "Forming and making good a penetration for services in a slab. Includes forming the penetration and making good. Measured per meter constructed.",
"Ayuda de albañilería para instalación solar: bases y pasos. Incluye la formación de bases y el resane. Medido por unidad de ayuda.":
    "Builder's work for the solar installation: bases and penetrations. Includes forming the bases and making good. Measured per unit of builder's work.",
"Resane de rozas y pasos de instalaciones. Incluye el tapado y el acabado. Medido por metro cuadrado resanado.":
    "Patching of chases and service penetrations. Includes making good and finishing. Measured per square meter patched.",

# ── Rozas y perforaciones ─────────────────────────────────────────────────
"Apertura de roza en pared de bloque para instalación. Incluye la ejecución de la roza. Medido por metro lineal ejecutado.":
    "Cutting a chase in a blockwork wall for services. Includes forming the chase. Measured per meter constructed.",
"Apertura de roza en muro de concreto. Incluye la ejecución de la roza. Medido por metro lineal ejecutado.":
    "Cutting a chase in a concrete wall. Includes forming the chase. Measured per meter constructed.",
"Apertura de regata para tubería en pared. Incluye la ejecución de la regata. Medido por metro lineal ejecutado.":
    "Cutting a chase for a pipe in a wall. Includes forming the chase. Measured per meter constructed.",
"Apertura de roza en techo para instalación. Incluye la ejecución de la roza. Medido por metro lineal ejecutado.":
    "Cutting a chase in a ceiling for services. Includes forming the chase. Measured per meter constructed.",
"Apertura de regata para cable en piso. Incluye la ejecución de la regata. Medido por metro lineal ejecutado.":
    "Cutting a chase for a cable in a floor. Includes forming the chase. Measured per meter constructed.",
"Apertura de roza en bloque de arcilla. Incluye la ejecución de la roza. Medido por metro lineal ejecutado.":
    "Cutting a chase in a clay block wall. Includes forming the chase. Measured per meter constructed.",
"Perforación de paso en muro para instalación. Incluye la perforación. Medido por unidad ejecutada.":
    "Drilling a penetration through a wall for services. Includes drilling. Measured per unit constructed.",
"Perforación de paso en losa para instalación. Incluye la perforación. Medido por unidad ejecutada.":
    "Drilling a penetration through a slab for services. Includes drilling. Measured per unit constructed.",
"Perforación de mechinal o hueco de ventilación en muro. Incluye la perforación. Medido por unidad ejecutada.":
    "Forming a weep hole or ventilation opening in a wall. Includes drilling. Measured per unit constructed.",
"Perforación para anclaje en concreto o mampostería. Incluye la perforación. Medido por unidad ejecutada.":
    "Drilling for an anchor in concrete or masonry. Includes drilling. Measured per unit constructed.",
"Ejecución de paso de conducto en losa. Incluye la perforación y el sello. Medido por unidad ejecutada.":
    "Forming a penetration for a duct through a slab. Includes drilling and sealing. Measured per unit constructed.",
"Perforación de hueco para caja de mecanismo. Incluye la perforación. Medido por unidad ejecutada.":
    "Cutting an opening for a back box. Includes drilling. Measured per unit constructed.",
"Ejecución de paso de tubería en muro con sello. Incluye la perforación y el sellado. Medido por unidad ejecutada.":
    "Forming a sealed penetration for a pipe through a wall. Includes drilling and sealing. Measured per unit constructed.",

# ── Recibidos ─────────────────────────────────────────────────────────────
"Recibido de marco o premarco de puerta con mortero. Incluye el recibido y el nivelado. Medido por unidad recibida.":
    "Bedding and fixing a door frame or subframe in mortar. Includes bedding and leveling. Measured per unit fixed.",
"Recibido de marco de ventana con mortero. Incluye el recibido y el nivelado. Medido por unidad recibida.":
    "Bedding and fixing a window frame in mortar. Includes bedding and leveling. Measured per unit fixed.",
"Recibido de caja de persiana en dintel. Incluye el recibido y el acabado. Medido por unidad recibida.":
    "Bedding and fixing a roller shutter box at the lintel. Includes bedding and finishing. Measured per unit fixed.",
"Recibido de premarco metálico de puerta. Incluye el recibido y el nivelado. Medido por unidad recibida.":
    "Bedding and fixing a metal door subframe. Includes bedding and leveling. Measured per unit fixed.",
"Recibido de reja con mortero y anclaje. Incluye el recibido y la fijación. Medido por unidad recibida.":
    "Bedding and fixing a grille in mortar with anchors. Includes bedding and fixing. Measured per unit fixed.",
"Recibido de aparato sanitario con mortero y anclaje. Incluye el recibido y la fijación. Medido por unidad recibida.":
    "Bedding and fixing a plumbing fixture in mortar with anchors. Includes bedding and fixing. Measured per unit fixed.",
"Recibido de mesón de cocina con mortero. Incluye el recibido y el nivelado. Medido por unidad recibida.":
    "Bedding and fixing a kitchen countertop in mortar. Includes bedding and leveling. Measured per unit fixed.",
"Recibido de soporte y equipo de aire acondicionado. Incluye el anclaje del soporte. Medido por unidad recibida.":
    "Fixing the support bracket and air conditioning unit. Includes anchoring the bracket. Measured per unit fixed.",
"Recibido de barra de apoyo de accesibilidad. Incluye el anclaje de la barra. Measured per unit fixed.":
    "Fixing an accessibility grab bar. Includes anchoring the bar. Measured per unit fixed.",
"Recibido de espejo con fijación. Incluye la fijación del espejo. Medido por unidad recibida.":
    "Fixing a mirror. Includes fixing the mirror. Measured per unit fixed.",
"Recibido de tanque de agua con base y fijación. Incluye la formación de base y el recibido. Medido por unidad recibida.":
    "Bedding and fixing a water tank on a base. Includes forming the base and bedding. Measured per unit fixed.",
"Recibido de equipo de bombeo con base. Incluye la formación de base y el recibido. Medido por unidad recibida.":
    "Bedding and fixing pumping equipment on a base. Includes forming the base and bedding. Measured per unit fixed.",
"Recibido de calentador de agua con fijación. Incluye el anclaje y el recibido. Medido por unidad recibida.":
    "Fixing a water heater. Includes anchoring and bedding. Measured per unit fixed.",

# ── Sellados ──────────────────────────────────────────────────────────────
"Sellado de junta con silicona sanitaria. Incluye la limpieza y el sellado. Medido por metro lineal sellado.":
    "Sealing a joint with sanitary silicone. Includes cleaning and sealing. Measured per meter sealed.",
"Sellado de junta con sellador elástico de poliuretano. Incluye la limpieza y el sellado. Medido por metro lineal sellado.":
    "Sealing a joint with an elastic polyurethane sealant. Includes cleaning and sealing. Measured per meter sealed.",
"Sellado del encuentro piso-pared con sellador. Incluye la limpieza y el sellado. Medido por metro lineal sellado.":
    "Sealing the floor to wall junction with sealant. Includes cleaning and sealing. Measured per meter sealed.",
"Sellado de junta perimetral de ventana. Incluye la limpieza y el sellado. Medido por metro lineal sellado.":
    "Sealing the perimeter joint of a window. Includes cleaning and sealing. Measured per meter sealed.",
"Sellado de junta perimetral de bañera o ducha. Incluye la limpieza y el sellado. Medido por metro lineal sellado.":
    "Sealing the perimeter joint of a bathtub or shower. Includes cleaning and sealing. Measured per meter sealed.",
"Sellado de junta de mesón de cocina. Incluye la limpieza y el sellado. Medido por metro lineal sellado.":
    "Sealing the joint of a kitchen countertop. Includes cleaning and sealing. Measured per meter sealed.",
"Sellado de paso de tubería con collarín. Incluye la limpieza y el sellado. Medido por unidad sellada.":
    "Sealing a pipe penetration with a split collar. Includes cleaning and sealing. Measured per unit sealed.",
"Sellado de junta de escalera. Incluye la limpieza y el sellado. Medido por metro lineal sellado.":
    "Sealing the joint of a stair. Includes cleaning and sealing. Measured per meter sealed.",

# ── Remates de encuentro ──────────────────────────────────────────────────
"Remate de encuentro pared-techo con sellador o perfil. Incluye el remate. Medido por metro lineal ejecutado.":
    "Finishing the wall to ceiling junction with sealant or a trim. Includes the finishing. Measured per meter constructed.",
"Remate de encuentro entre materiales distintos. Incluye el sellado. Medido por metro lineal ejecutado.":
    "Finishing the junction between dissimilar materials. Includes sealing. Measured per meter constructed.",
"Remate de junta de dilatación con perfil. Incluye la colocación del perfil. Medido por metro lineal ejecutado.":
    "Finishing an expansion joint with a trim. Includes installing the trim. Measured per meter constructed.",
"Remate de encuentro de zona de ducha. Incluye el sellado y el remate. Medido por metro lineal ejecutado.":
    "Finishing the junctions of a shower area. Includes sealing and finishing. Measured per meter constructed.",
"Remate de junta de fachada con sellador. Incluye el sellado. Medido por metro lineal ejecutado.":
    "Finishing a facade joint with sealant. Includes sealing. Measured per meter constructed.",

# ── Vierteaguas y alféizares ──────────────────────────────────────────────
"Ejecución de vierteaguas de concreto en ventana. Incluye el encofrado y el vaciado. Medido por metro lineal ejecutado.":
    "Formation of a concrete weather sill at a window. Includes formwork and pouring. Measured per meter constructed.",
"Colocación de alféizar de piedra. Incluye la colocación y el rejuntado. Medido por metro lineal ejecutado.":
    "Installation of a stone window sill. Includes bedding and pointing. Measured per meter constructed.",
"Ejecución de vierteaguas de mortero con pendiente. Incluye la formación de la pendiente y el acabado. Medido por metro lineal ejecutado.":
    "Formation of a weather sill in mortar with a fall. Includes forming the fall and finishing. Measured per meter constructed.",
"Colocación de alféizar de mármol. Incluye la colocación y el rejuntado. Medido por metro lineal ejecutado.":
    "Installation of a marble window sill. Includes bedding and pointing. Measured per meter constructed.",
"Colocación de vierteaguas prefabricado de concreto. Incluye la colocación. Medido por metro lineal ejecutado.":
    "Installation of a precast concrete weather sill. Includes bedding. Measured per meter constructed.",
"Colocación de alféizar de madera. Incluye la fijación y el acabado. Medido por metro lineal ejecutado.":
    "Installation of a wood window sill. Includes fixing and finishing. Measured per meter constructed.",
"Colocación de vierteaguas de piedra artificial. Incluye la colocación y el rejuntado. Medido por metro lineal ejecutado.":
    "Installation of a cast stone weather sill. Includes bedding and pointing. Measured per meter constructed.",
"Colocación de vierteaguas de chapa metálica. Incluye la fijación y el sellado. Medido por metro lineal ejecutado.":
    "Installation of a sheet metal weather sill. Includes fixing and sealing. Measured per meter constructed.",

# ── Coronaciones ──────────────────────────────────────────────────────────
"Ejecución de coronación de muro con mortero. Incluye la formación de la coronación. Medido por metro lineal ejecutado.":
    "Formation of a coping to a wall in mortar. Includes forming the coping. Measured per meter constructed.",
"Colocación de pieza de coronación de muro. Incluye la colocación de la pieza. Medido por metro lineal ejecutado.":
    "Installation of a coping unit to a wall. Includes laying the unit. Measured per meter constructed.",
"Ejecución de coronación de peto de cubierta. Incluye la formación de la coronación. Medido por metro lineal ejecutado.":
    "Formation of a coping to a roof parapet. Includes forming the coping. Measured per meter constructed.",
"Ejecución de coronación de muro con ladrillo visto. Incluye la colocación del ladrillo. Medido por metro lineal ejecutado.":
    "Formation of a coping to a wall in facing brick. Includes laying the brick. Measured per meter constructed.",
"Colocación de coronación de muro con chapa metálica. Incluye la fijación y el sellado. Medido por metro lineal ejecutado.":
    "Installation of a sheet metal coping to a wall. Includes fixing and sealing. Measured per meter constructed.",

# ── Bases y bancadas ──────────────────────────────────────────────────────
"Ejecución de base de concreto para equipo. Incluye el vaciado y el acabado. Medido por unidad ejecutada.":
    "Construction of a concrete base for equipment. Includes pouring and finishing. Measured per unit constructed.",
"Ejecución de bancada para unidad condensadora de aire. Incluye el vaciado y los anclajes. Medido por unidad ejecutada.":
    "Construction of a plinth for an air conditioning condensing unit. Includes pouring and the anchors. Measured per unit constructed.",
"Ejecución de base para tanque de agua. Incluye el vaciado y el acabado. Medido por unidad ejecutada.":
    "Construction of a base for a water tank. Includes pouring and finishing. Measured per unit constructed.",
"Ejecución de base para planta eléctrica. Incluye el vaciado y los anclajes. Medido por unidad ejecutada.":
    "Construction of a base for a generator. Includes pouring and the anchors. Measured per unit constructed.",
"Ejecución de base de concreto para bomba. Incluye el vaciado y el acabado. Medido por unidad ejecutada.":
    "Construction of a concrete base for a pump. Includes pouring and finishing. Measured per unit constructed.",
"Ejecución de base de concreto para cámara de seguridad. Incluye el vaciado. Medido por unidad ejecutada.":
    "Construction of a concrete base for a security camera. Includes pouring. Measured per unit constructed.",
"Suministro y colocación de soporte metálico para equipo. Incluye el anclaje del soporte. Medido por unidad colocado.":
    "Supply and installation of a metal support bracket for equipment. Includes anchoring the bracket. Measured per unit installed.",
"Suministro y colocación de soporte para unidad condensadora. Incluye el anclaje del soporte. Medido por unidad colocado.":
    "Supply and installation of a support bracket for a condensing unit. Includes anchoring the bracket. Measured per unit installed.",
"Ejecución de base para bomba de agua. Incluye el vaciado y los anclajes. Medido por unidad ejecutada.":
    "Construction of a base for a water pump. Includes pouring and the anchors. Measured per unit constructed.",
"Ejecución de bancada de madera para equipo. Incluye la estructura de madera. Medido por unidad ejecutada.":
    "Construction of a timber plinth for equipment. Includes the timber frame. Measured per unit constructed.",
"Suministro y colocación de soporte de calentador. Incluye el anclaje. Medido por unidad colocado.":
    "Supply and installation of a support bracket for a water heater. Includes anchoring. Measured per unit installed.",
"Ejecución de base para sistema hidroneumático. Incluye el vaciado y los anclajes. Medido por unidad ejecutada.":
    "Construction of a base for a hydropneumatic system. Includes pouring and the anchors. Measured per unit constructed.",
"Suministro y colocación de estructura de soporte de panel solar. Incluye el anclaje de la estructura. Medido por unidad colocado.":
    "Supply and installation of the support structure for solar panels. Includes anchoring the structure. Measured per unit installed.",

# ── Forrados y cajones ────────────────────────────────────────────────────
"Forrado de tubería o bajante con placa de yeso. Incluye la estructura y la placa. Medido por metro lineal forrado.":
    "Boxing in a pipe or downpipe with gypsum board. Includes the framing and the board. Measured per meter boxed in.",
"Formación de cajón para ocultar instalaciones. Incluye la estructura y la placa. Medido por metro lineal ejecutado.":
    "Formation of a service duct to conceal services. Includes the framing and the board. Measured per meter constructed.",
"Formación de falso pilar de placa de yeso. Incluye la estructura y la placa. Medido por metro lineal ejecutado.":
    "Formation of a false column in gypsum board. Includes the framing and the board. Measured per meter constructed.",
"Forrado de viga con placa de yeso. Incluye la estructura y la placa. Medido por metro cuadrado forrado.":
    "Boxing in a beam with gypsum board. Includes the framing and the board. Measured per square meter boxed in.",
"Forrado de conducto de climatización con placa de yeso. Incluye la estructura y la placa. Medido por metro lineal forrado.":
    "Boxing in an HVAC duct with gypsum board. Includes the framing and the board. Measured per meter boxed in.",
"Formación de cajón de persiana interior. Incluye la estructura y la placa. Medido por metro lineal ejecutado.":
    "Formation of an internal roller shutter box. Includes the framing and the board. Measured per meter constructed.",
"Forrado de montante de instalaciones con placa. Incluye la estructura y la placa. Medido por metro lineal forrado.":
    "Boxing in a services riser with board. Includes the framing and the board. Measured per meter boxed in.",
"Forrado de bajante con placa de cemento. Incluye la estructura y la placa. Medido por metro cuadrado forrado.":
    "Boxing in a downpipe with cement board. Includes the framing and the board. Measured per square meter boxed in.",
"Formación de cajón para persiana con registro. Incluye la estructura y la placa. Medido por metro lineal ejecutado.":
    "Formation of a roller shutter box with an access panel. Includes the framing and the board. Measured per meter constructed.",

# ── Tapajuntas y molduras ─────────────────────────────────────────────────
"Colocación de tapajuntas de madera en puerta o ventana. Incluye la fijación y el acabado. Medido por metro lineal colocado.":
    "Installation of wood architrave to a door or window. Includes fixing and finishing. Measured per meter installed.",
"Colocación de tapajuntas de aluminio. Incluye la fijación. Medido por metro lineal colocado.":
    "Installation of an aluminium cover strip. Includes fixing. Measured per meter installed.",
"Colocación de tapajuntas de MDF. Incluye la fijación. Medido por metro lineal colocado.":
    "Installation of an MDF architrave. Includes fixing. Measured per meter installed.",
"Colocación de remate de tapajuntas de esquina. Incluye la fijación. Medido por metro lineal colocado.":
    "Installation of a corner piece to the architrave. Includes fixing. Measured per meter installed.",
"Colocación de tapajuntas de PVC. Incluye la fijación. Medido por metro lineal colocado.":
    "Installation of a PVC cover strip. Includes fixing. Measured per meter installed.",
"Colocación de moldura corrida de yeso. Incluye la fijación y el acabado. Medido por metro lineal colocado.":
    "Installation of a run of plaster molding. Includes fixing and finishing. Measured per meter installed.",
"Colocación de cornisa de yeso. Incluye la fijación y el acabado. Medido por metro lineal colocado.":
    "Installation of a plaster cornice. Includes fixing and finishing. Measured per meter installed.",
"Colocación de perfil de remate decorativo. Incluye la fijación. Medido por metro lineal colocado.":
    "Installation of a decorative trim. Includes fixing. Measured per meter installed.",
"Colocación de moldura de poliuretano. Incluye la fijación y el acabado. Medido por metro lineal colocado.":
    "Installation of a polyurethane molding. Includes fixing and finishing. Measured per meter installed.",
"Colocación de perfil esquinero decorativo. Incluye la fijación. Medido por metro lineal colocado.":
    "Installation of a decorative corner trim. Includes fixing. Measured per meter installed.",
"Colocación de moldura de techo decorativa. Incluye la fijación y el acabado. Medido por metro lineal colocado.":
    "Installation of a decorative ceiling molding. Includes fixing and finishing. Measured per meter installed.",
"Colocación de perfil de transición decorativo. Incluye la fijación. Medido por metro lineal colocado.":
    "Installation of a decorative transition profile. Includes fixing. Measured per meter installed.",
"Colocación de moldura de madera. Incluye la fijación y el acabado. Medido por metro lineal colocado.":
    "Installation of a wood molding. Includes fixing and finishing. Measured per meter installed.",
"Colocación de remate de cenefa de iluminación indirecta. Incluye la fijación. Medido por metro lineal colocado.":
    "Installation of a pelmet trim for indirect lighting. Includes fixing. Measured per meter installed.",
"Colocación de remate especial de fachada. Incluye la fijación. Medido por metro lineal colocado.":
    "Installation of a special facade trim. Includes fixing. Measured per meter installed.",
"Colocación de remate de borde de piso. Incluye la fijación. Medido por metro lineal colocado.":
    "Installation of a floor edge trim. Includes fixing. Measured per meter installed.",
"Colocación de remate de escalera. Incluye la fijación. Medido por metro lineal colocado.":
    "Installation of a stair edge trim. Includes fixing. Measured per meter installed.",
"Colocación de remate de zócalo decorativo. Incluye la fijación. Medido por metro lineal colocado.":
    "Installation of a decorative baseboard trim. Includes fixing. Measured per meter installed.",
"Colocación de remate especial de cielo raso. Incluye la fijación. Medido por metro lineal colocado.":
    "Installation of a special ceiling trim. Includes fixing. Measured per meter installed.",

# ── Sellados cortafuego ───────────────────────────────────────────────────
"Sellado cortafuego de paso de instalación eléctrica en muro o losa. Incluye la aplicación de la masilla intumescente. Medido por unidad sellado.":
    "Firestopping of an electrical penetration through a wall or slab. Includes the application of intumescent mastic. Measured per unit sealed.",
"Sellado cortafuego de paso de instalación sanitaria. Incluye la aplicación de la masilla. Medido por unidad sellado.":
    "Firestopping of a plumbing penetration. Includes the application of intumescent mastic. Measured per unit sealed.",
"Sellado cortafuego de paso de conducto de ventilación. Incluye la aplicación de la masilla. Medido por unidad sellado.":
    "Firestopping of a ventilation duct penetration. Includes the application of intumescent mastic. Measured per unit sealed.",
"Sellado cortafuego de paso de bandeja portacables. Incluye la aplicación de la masilla. Medido por unidad sellado.":
    "Firestopping of a cable tray penetration. Includes the application of intumescent mastic. Measured per unit sealed.",
"Sellado cortafuego de paso de tubería de gas. Incluye la aplicación de la masilla. Medido por unidad sellado.":
    "Firestopping of a gas pipe penetration. Includes the application of intumescent mastic. Measured per unit sealed.",
"Sellado cortafuego de junta lineal en muro o losa. Incluye la aplicación de la masilla. Medido por metro lineal sellado.":
    "Firestopping of a linear joint in a wall or slab. Includes the application of intumescent mastic. Measured per meter sealed.",
"Sellado cortafuego de paso múltiple de instalaciones. Incluye la aplicación de la masilla. Medido por unidad sellado.":
    "Firestopping of a multiple service penetration. Includes the application of intumescent mastic. Measured per unit sealed.",
"Sellado cortafuego de junta de dilatación. Incluye la aplicación de la masilla. Medido por metro lineal sellado.":
    "Firestopping of an expansion joint. Includes the application of intumescent mastic. Measured per meter sealed.",
"Sellado cortafuego de paso de climatización. Incluye la aplicación de la masilla. Medido por unidad sellado.":
    "Firestopping of an HVAC penetration. Includes the application of intumescent mastic. Measured per unit sealed.",
"Sellado cortafuego del encuentro muro-losa. Incluye la aplicación de la masilla. Medido por metro lineal sellado.":
    "Firestopping of the wall to slab junction. Includes the application of intumescent mastic. Measured per meter sealed.",
"Sellado cortafuego de paso de instalación de datos. Incluye la aplicación de la masilla. Medido por unidad sellado.":
    "Firestopping of a data penetration. Includes the application of intumescent mastic. Measured per unit sealed.",
"Sellado cortafuego de cierre perimetral de paso. Incluye la aplicación de la masilla. Medido por metro lineal sellado.":
    "Firestopping of the perimeter closure of a penetration. Includes the application of intumescent mastic. Measured per meter sealed.",
"Sellado cortafuego de paso de bandeja de cables. Incluye la aplicación de la masilla. Medido por unidad sellado.":
    "Firestopping of a cable tray penetration. Includes the application of intumescent mastic. Measured per unit sealed.",
"Sellado cortafuego de junta de construcción. Incluye la aplicación de la masilla. Medido por metro lineal sellado.":
    "Firestopping of a construction joint. Includes the application of intumescent mastic. Measured per meter sealed.",
}
