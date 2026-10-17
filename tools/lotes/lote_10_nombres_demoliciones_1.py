# -*- coding: utf-8 -*-
"""Nombres de partida — Demoliciones y desmontajes (1 de 2).

Criterios de este lote:
  · «Demolición» es demolition cuando se rompe y «desmontaje» es removal
    cuando se quita sin romper, o dismantling cuando la pieza es una
    estructura que se desarma.
  · «Picado» es chipping off: se pica un revestimiento, no se demuele.
  · «Apertura de vano» es formation of an opening; «roza» es chase, que es
    la palabra de oficio para la ranura de una instalación.
  · «Tabique» es partition y «muro» es wall: la diferencia de grosor y de
    función que en inglés se mantiene.
  · «Sobrecimiento» es plinth, «viga de corona» es ring beam,
    «concreto ciclópeo» es rubble concrete.
"""

LOTE = {
# ── Cimentación ───────────────────────────────────────────────────────────
"Demolición de losa de fundación de concreto armado.":
    "Demolition of a reinforced concrete foundation slab.",
"Demolición de viga de riostra o muro de contención de concreto.":
    "Demolition of a concrete tie beam or retaining wall.",
"Demolición de zapata o pedestal de concreto armado.":
    "Demolition of a reinforced concrete footing or pedestal.",
"Demolición de muro de sótano de concreto armado.":
    "Demolition of a reinforced concrete basement wall.",
"Demolición de platea de fundación.":
    "Demolition of a raft foundation.",
"Corte y demolición de viga de fundación.":
    "Cutting and demolition of a foundation beam.",
"Demolición de cabezal de pilote.":
    "Demolition of a pile cap.",
"Demolición de fundación de mampostería.":
    "Demolition of a masonry foundation.",
"Corte de muro de fundación con disco.":
    "Saw cutting of a foundation wall.",
"Demolición de sobrecimiento de concreto.":
    "Demolition of a concrete plinth.",
"Demolición de base de concreto ciclópeo.":
    "Demolition of a rubble concrete base.",
"Apertura de hueco en losa de fundación.":
    "Formation of an opening in a foundation slab.",
"Demolición de muro de piedra de fundación.":
    "Demolition of a stone foundation wall.",
"Desmontaje de encofrado perdido en fundación.":
    "Removal of permanent formwork in a foundation.",
"Demolición de viga de corona de fundación.":
    "Demolition of a foundation ring beam.",
"Demolición de pedestal de concreto armado.":
    "Demolition of a reinforced concrete pedestal.",
"Demolición de losa de piso de sótano.":
    "Demolition of a basement floor slab.",
"Demolición de contrapiso de fundación.":
    "Demolition of a foundation subfloor.",

# ── Estructura ────────────────────────────────────────────────────────────
"Desmontaje de estructura metálica.":
    "Dismantling of a steel structure.",
"Demolición de columna de concreto armado.":
    "Demolition of a reinforced concrete column.",
"Demolición de viga de concreto armado.":
    "Demolition of a reinforced concrete beam.",
"Demolición de losa de entrepiso maciza o nervada.":
    "Demolition of a solid or ribbed intermediate floor slab.",
"Apertura de hueco en losa de concreto armado.":
    "Formation of an opening in a reinforced concrete slab.",
"Desmontaje de estructura de madera.":
    "Dismantling of a lumber structure.",
"Corte de concreto con disco de diamante.":
    "Cutting of concrete with a diamond blade.",
"Demolición de escalera estructural de concreto armado.":
    "Demolition of a structural reinforced concrete stair.",
"Demolición de viga de amarre.":
    "Demolition of a tie beam.",
"Demolición de losa nervada.":
    "Demolition of a ribbed slab.",
"Demolición de muro estructural de concreto.":
    "Demolition of a structural concrete wall.",
"Desmontaje de correa o viga metálica.":
    "Removal of a steel purlin or beam.",
"Demolición de losa de concreto con nervios.":
    "Demolition of a ribbed concrete slab.",
"Demolición de columna de concreto.":
    "Demolition of a concrete column.",
"Corte de losa para escalera o montacargas.":
    "Cutting of a slab for a stair or lift.",
"Demolición de mezzanina de concreto.":
    "Demolition of a concrete mezzanine.",
"Desmontaje de celosía o cercha metálica.":
    "Dismantling of a steel lattice or truss.",
"Demolición de losa de techo de concreto.":
    "Demolition of a concrete roof slab.",
"Demolición de contrafuerte de concreto.":
    "Demolition of a concrete buttress.",
"Desmontaje de losa colaborante metálica.":
    "Removal of a composite metal deck.",
"Demolición de muro de carga de concreto.":
    "Demolition of a load-bearing concrete wall.",

# ── Fachada ───────────────────────────────────────────────────────────────
"Desmontaje de baranda o pasamanos de balcón.":
    "Removal of a balcony guardrail or handrail.",
"Desmontaje de reja de protección en fachada.":
    "Removal of a protective grille on a facade.",
"Demolición de muro de fachada de bloque o ladrillo.":
    "Demolition of a blockwork or brick facade wall.",
"Desmontaje de cerramiento ligero de láminas metálicas.":
    "Removal of lightweight metal sheet cladding.",
"Picado de salpicado o graniplast en fachada.":
    "Chipping off a textured render from a facade.",
"Picado de mortero monocapa en fachada.":
    "Chipping off a single-coat render from a facade.",
"Desmontaje de muro cortina de vidrio.":
    "Removal of a glass curtain wall.",
"Desmontaje de revestimiento de fachada ventilada.":
    "Removal of a ventilated facade cladding.",
"Desmontaje de celosía de fachada.":
    "Removal of a facade screen.",
"Demolición de muro de fachada de concreto.":
    "Demolition of a concrete facade wall.",
"Desmontaje de revestimiento de piedra en fachada.":
    "Removal of stone cladding from a facade.",
"Demolición de muro de fachada de mampostería.":
    "Demolition of a masonry facade wall.",
"Desmontaje de panel sándwich de fachada.":
    "Removal of a facade sandwich panel.",
"Picado de aplacado cerámico de fachada.":
    "Chipping off ceramic cladding from a facade.",
"Desmontaje de bajante o canalón de fachada.":
    "Removal of a facade downpipe or gutter.",
"Demolición de cornisa o remate de fachada.":
    "Demolition of a facade cornice or trim.",
"Desmontaje de marquesina de fachada.":
    "Removal of a facade canopy.",
"Demolición de antepecho de fachada.":
    "Demolition of a facade parapet.",
"Desmontaje de persiana de fachada.":
    "Removal of a facade shutter.",
"Picado de friso de fachada.":
    "Chipping off render from a facade.",
"Desmontaje de publicidad o letrero de fachada.":
    "Removal of an advertising sign from a facade.",

# ── Tabiquería y particiones ──────────────────────────────────────────────
"Demolición de tabique de bloque o ladrillo, incluidos sus revestimientos.":
    "Demolition of a blockwork or brick partition, including its finishes.",
"Demolición de tabique de yeso laminado y su estructura.":
    "Demolition of a plasterboard partition and its framing.",
"Demolición de muro de concreto no estructural.":
    "Demolition of a non-structural concrete wall.",
"Apertura de vano en pared de bloque o ladrillo.":
    "Formation of an opening in a blockwork or brick wall.",
"Demolición de tabique de bloque de vidrio.":
    "Demolition of a glass block partition.",
"Apertura de nicho u hornacina en pared.":
    "Formation of a recess in a wall.",
"Demolición de tabique de placa de cemento.":
    "Demolition of a cement board partition.",
"Demolición de pared de mampostería estructural.":
    "Demolition of a structural masonry wall.",
"Demolición de tabique de ladrillo macizo.":
    "Demolition of a solid brick partition.",
"Demolición de tabique de bloque de arcilla.":
    "Demolition of a clay block partition.",
"Demolición de tabique de madera.":
    "Demolition of a lumber partition.",
"Demolición de tabique de panel liviano.":
    "Demolition of a lightweight panel partition.",
"Apertura de rozas en pared para instalaciones.":
    "Formation of chases in a wall for services.",
"Demolición de muro de bloque de concreto.":
    "Demolition of a concrete block wall.",
"Demolición de tabique de doble placa de yeso.":
    "Demolition of a double plasterboard partition.",
"Apertura de vano en muro de concreto.":
    "Formation of an opening in a concrete wall.",
"Demolición de tabique de bloque de vidrio existente.":
    "Demolition of an existing glass block partition.",
"Demolición de pared de bloques con armado.":
    "Demolition of a reinforced blockwork wall.",
"Demolición de tabique de fibra o panel.":
    "Demolition of a fiber or panel partition.",
"Apertura de roza en muro de concreto.":
    "Formation of a chase in a concrete wall.",
"Demolición de pared de ladrillo a la vista.":
    "Demolition of a face brick wall.",

# ── Carpintería y elementos de hueco ──────────────────────────────────────
"Desmontaje de closet o mueble empotrado.":
    "Removal of a closet or built-in unit.",
"Desmontaje de reja o protector metálico interior.":
    "Removal of an interior grille or protective guard.",
"Retiro de vidrio de carpintería existente.":
    "Removal of glass from existing joinery.",
"Desmontaje de puerta interior con su marco.":
    "Removal of an interior door and frame.",
"Desmontaje de puerta exterior o metálica con su marco.":
    "Removal of an exterior or metal door and frame.",
"Desmontaje de ventana con su marco.":
    "Removal of a window and frame.",
"Desmontaje de puerta interior corrediza.":
    "Removal of an interior sliding door.",
"Desmontaje de puerta plegable.":
    "Removal of a folding door.",
"Desmontaje de marco de puerta.":
    "Removal of a door frame.",
"Desmontaje de ventana de aluminio.":
    "Removal of an aluminum window.",
"Desmontaje de ventana de madera.":
    "Removal of a lumber window.",
"Desmontaje de persiana enrollable.":
    "Removal of a roller shutter.",
"Desmontaje de mosquitero.":
    "Removal of an insect screen.",
"Desmontaje de puerta blindada.":
    "Removal of a security door.",
"Desmontaje de portón corredizo.":
    "Removal of a sliding gate.",
"Desmontaje de reja de protección.":
    "Removal of a protective grille.",
"Desmontaje de baranda metálica.":
    "Removal of a metal guardrail.",
"Desmontaje de celosía o romanilla.":
    "Removal of a lattice or metal grille.",
"Retiro de vidrio de fachada.":
    "Removal of glass from a facade.",
"Desmontaje de mampara de baño.":
    "Removal of a shower screen.",
"Desmontaje de caja de persiana.":
    "Removal of a roller shutter box.",
"Desmontaje de alféizar o repisa de ventana.":
    "Removal of a window sill or ledge.",
"Demolición de dintel prefabricado o cargadero.":
    "Demolition of a precast lintel.",
"Desmontaje de pasamanos de escalera.":
    "Removal of a stair handrail.",
"Desmontaje de canalón de alero.":
    "Removal of an eaves gutter.",
"Desmontaje de remate o tapajuntas.":
    "Removal of a trim or cover flashing.",
"Demolición de vierteaguas.":
    "Demolition of a weather sill.",
"Desmontaje de pasamanos metálico.":
    "Removal of a metal handrail.",
"Desmontaje de moldura decorativa.":
    "Removal of a decorative molding.",
"Desmontaje de zócalo o rodapié.":
    "Removal of a base.",
"Demolición de cornisa de yeso.":
    "Demolition of a plaster cornice.",
"Desmontaje de cumbrera o remate de techo.":
    "Removal of a ridge or roof trim.",
"Desmontaje de canaleta de drenaje.":
    "Removal of a drainage channel.",
"Desmontaje de soporte de aparato de aire.":
    "Removal of an air conditioning unit bracket.",
"Desmontaje de antepecho de metal.":
    "Removal of a metal sill rail.",
"Demolición de bancada de equipo.":
    "Demolition of an equipment plinth.",
"Desmontaje de rejilla de ventilación.":
    "Removal of a ventilation grille.",
"Desmontaje de tapa de registro.":
    "Removal of an access cover.",
"Desmontaje de soporte de toldo.":
    "Removal of an awning bracket.",

# ── Instalaciones ─────────────────────────────────────────────────────────
"Desmontaje de equipo de aire acondicionado tipo split.":
    "Removal of a split air conditioning unit.",
"Desmontaje de unidad condensadora de aire.":
    "Removal of a condensing unit.",
"Desmontaje de red eléctrica y sus mecanismos.":
    "Removal of the electrical installation and its accessories.",
"Desmontaje de tablero eléctrico.":
    "Removal of an electrical panel.",
"Desmontaje de bandeja portacables.":
    "Removal of a cable tray.",
"Desmontaje de canalización eléctrica vista.":
    "Removal of surface electrical conduit.",
"Desmontaje de red de tuberías de agua o desagüe.":
    "Removal of a water or drainage pipework system.",
"Desmontaje de aparato sanitario y su grifería.":
    "Removal of a plumbing fixture and its faucet.",
"Desmontaje de tubería de agua de PPR.":
    "Removal of PPR water pipe.",
"Desmontaje de tubería de desagüe.":
    "Removal of a drainage pipe.",
"Desmontaje de grifería.":
    "Removal of a faucet.",
"Desmontaje de luminaria.":
    "Removal of a light fixture.",
"Desmontaje de lámpara de techo.":
    "Removal of a ceiling light.",
"Desmontaje de fregadero y su grifería.":
    "Removal of a kitchen sink and its faucet.",
"Desmontaje de calentador de agua.":
    "Removal of a water heater.",
}
