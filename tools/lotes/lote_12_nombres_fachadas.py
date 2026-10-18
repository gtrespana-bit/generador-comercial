# -*- coding: utf-8 -*-
"""Nombres de partida — Fachadas y particiones (capítulo completo, 180).

Criterios de este lote:
  · «Fachada de bloque» es concrete masonry facade, no block facade: concrete masonry es
    la palabra de oficio para la fábrica de bloques, igual que brickwork
    lo es para la de ladrillo.
  · «Tabique» es partition; «división» es divider, porque son piezas
    distintas y el presupuesto las cobra aparte.
  · SATE es la sigla española del aislamiento exterior por el exterior. En
    Estados Unidos ese sistema es EIFS (exterior insulation and finish
    system) y en Reino Unido es ETICS: la sigla española no se traduce, se
    sustituye por la que usa cada mercado.
  · «Bloque canal» es bond beam block en Estados Unidos y channel block en
    Reino Unido.
  · «Celosía» sobre fachada es louver screen, y «cerramiento de lamas
    orientables» es adjustable louver screen.
  · «Verdín» es algae, «proyección de arena» es sandblasting.
"""

LOTE = {
# ── Fachadas de fábrica ───────────────────────────────────────────────────
"Fachada de bloque de concreto de 15 cm.":
    "15 cm concrete masonry facade.",
"Fachada de bloque de concreto de 20 cm.":
    "20 cm concrete masonry facade.",
"Fachada de bloque de concreto con friso.":
    "Concrete concrete masonry facade with stucco.",
"Fachada de bloque de concreto con acabado a la vista.":
    "Concrete concrete masonry facade with an exposed finish.",
"Fachada de bloque de concreto con refuerzo.":
    "Reinforced concrete masonry facade.",
"Fachada de bloque de concreto de 12 cm.":
    "12 cm concrete masonry facade.",
"Fachada de bloque de arcilla de 15 cm.":
    "15 cm clay masonry facade.",
"Fachada de ladrillo macizo de arcilla.":
    "Solid clay brick facade.",
"Fachada de bloque de arcilla con friso.":
    "Clay concrete masonry facade with stucco.",
"Fachada de ladrillo visto.":
    "Face brick facade.",
"Fachada de ladrillo visto con juntas coloreadas.":
    "Face brick facade with colored mortar joints.",
"Fachada de ladrillo visto con cámara.":
    "Face brick facade with a cavity.",

# ── Fachadas ligeras ──────────────────────────────────────────────────────
"Fachada ligera de placa de cemento.":
    "Lightweight cement board facade.",
"Fachada ligera de placa de cemento con aislamiento.":
    "Lightweight cement board facade with insulation.",
"Fachada ligera de placa de cemento exterior.":
    "Lightweight exterior cement board facade.",
"Fachada de panel sándwich.":
    "Sandwich panel facade.",
"Fachada de chapa metálica perfilada.":
    "Profiled metal sheet facade.",
"Fachada de panel sándwich con remates.":
    "Sandwich panel facade with trims.",
"Fachada de chapa con aislamiento.":
    "Metal sheet facade with insulation.",
"Fachada de chapa metálica con junta alzada.":
    "Standing seam metal sheet facade.",
"Fachada revestida con lámina de aluminio.":
    "Aluminum sheet clad facade.",
"Fachada revestida con placa fenólica.":
    "Phenolic panel clad facade.",
"Fachada revestida con listones de madera.":
    "Lumber batten clad facade.",
"Fachada revestida con gres porcelánico.":
    "Porcelain stoneware clad facade.",

# ── Paredes y tabiques de bloque ──────────────────────────────────────────
"Tabique de bloque de concreto de 10 cm, recibido con mortero de pega.":
    "10 cm concrete block partition, laid in bedding mortar.",
"Pared de bloque de concreto de 15 cm.":
    "15 cm concrete block wall.",
"Pared de bloque de concreto de 20 cm.":
    "20 cm concrete block wall.",
"Pared de bloque de concreto a la vista.":
    "Exposed concrete block wall.",
"Machón o columna de confinamiento en pared de bloque.":
    "Pier or confining column in a block wall.",
"Viga de corona o de amarre en pared de bloque.":
    "Ring beam or tie beam in a block wall.",
"Pared de bloque de concreto de 12 cm.":
    "12 cm concrete block wall.",
"Tabique de bloque de concreto con friso.":
    "Concrete block partition with stucco.",
"Tabique de bloque de concreto de 15 cm con friso.":
    "15 cm concrete block partition with stucco.",
"Tabique de bloque de concreto con refuerzo.":
    "Reinforced concrete block partition.",
"Tabique de bloque de concreto a media altura.":
    "Half-height concrete block partition.",
"Tabique de bloque de concreto con juntas finas.":
    "Thin-joint concrete block partition.",
"Tabique de bloque de concreto con viga de amarre.":
    "Concrete block partition with a tie beam.",
"Tabique de bloque de concreto con cámara de instalaciones.":
    "Concrete block partition with a service void.",
"Tabique de bloque de concreto con junta de dilatación.":
    "Concrete block partition with an expansion joint.",
"Pared de bloque de arcilla de 10 cm.":
    "10 cm clay block wall.",
"Pared de bloque de arcilla de 15 cm.":
    "15 cm clay block wall.",
"Pared de ladrillo macizo de arcilla.":
    "Solid clay brick wall.",
"Pared de ladrillo de arcilla a la vista.":
    "Exposed clay brick wall.",
"Tabique de bloque de arcilla con friso.":
    "Clay block partition with stucco.",
"Tabique de ladrillo macizo.":
    "Solid brick partition.",
"Tabique de bloque de arcilla a media altura.":
    "Half-height clay block partition.",
"Tabique de bloque de arcilla de 15 cm.":
    "15 cm clay block partition.",
"Tabique de ladrillo visto interior.":
    "Interior face brick partition.",

# ── Mampostería estructural ───────────────────────────────────────────────
"Pared de mampostería estructural de bloque de concreto de 15 cm.":
    "15 cm structural concrete masonry wall.",
"Pared de mampostería estructural de bloque de concreto de 20 cm.":
    "20 cm structural concrete masonry wall.",
"Viga dintel de mampostería estructural con bloque canal.":
    "Lintel beam in structural masonry with a bond beam block.",
"Refuerzo de celda vertical con acero y relleno de concreto.":
    "Reinforcement of a vertical cell with steel and concrete fill.",
"Mampostería estructural de bloque de 10 cm.":
    "10 cm structural concrete masonry.",
"Mampostería estructural de bloque de 15 cm.":
    "15 cm structural concrete masonry.",
"Mampostería estructural de bloque de 20 cm.":
    "20 cm structural concrete masonry.",
"Mampostería estructural con bloque canal.":
    "Structural masonry with a bond beam block.",
"Mampostería estructural de bloque de arcilla.":
    "Structural clay masonry.",

# ── Tabiques de placa de yeso ─────────────────────────────────────────────
"Tabique autoportante de placa de yeso laminado 15+70+15, doble placa por cara.":
    "Self-supporting drywall partition, 15+70+15, two layers of board on each face.",
"Tabique autoportante de yeso laminado 12,5+70+12,5, placa simple.":
    "Self-supporting drywall partition, 12.5+70+12.5, single layer of board.",
"Tabique de yeso laminado con placa resistente a la humedad.":
    "Drywall partition with moisture-resistant board.",
"Trasdosado autoportante de yeso laminado.":
    "Independent drywall wall lining.",
"Trasdosado directo de placa de yeso laminado pegada al muro.":
    "Direct drywall lining bonded to a wall.",
"Refuerzo interior para anclaje de cargas en tabique de yeso laminado.":
    "Internal reinforcement for fastening loads in a drywall partition.",
"Tabique de yeso laminado con aislamiento acústico.":
    "Drywall partition with acoustic insulation.",
"Tabique de yeso laminado con placa de alta dureza.":
    "Drywall partition with high-impact board.",
"Tabique de yeso laminado con placa ignífuga.":
    "Drywall partition with fire-rated board.",
"Tabique de yeso laminado en zona húmeda.":
    "Drywall partition in a wet area.",
"Tabique de yeso laminado de gran altura.":
    "Full-height drywall partition.",
"Tabique de yeso laminado con banda perimetral.":
    "Drywall partition with a perimeter sealing tape.",
"Trasdosado autoportante con lana.":
    "Independent wall lining with mineral wool.",
"Trasdosado directo de placa de yeso.":
    "Direct drywall lining.",
"Tabique de yeso laminado con doble placa.":
    "Drywall partition with two layers of board.",
"Tabique de yeso laminado con refuerzo de cargas.":
    "Drywall partition with load fastening reinforcement.",
"Tabique de yeso laminado curvo.":
    "Curved drywall partition.",
"Tabique de yeso laminado con cajón de instalaciones.":
    "Drywall partition with a service void.",
"Tabique de yeso laminado con junta de dilatación.":
    "Drywall partition with an expansion joint.",
"Tabique de yeso laminado con placa perforada.":
    "Drywall partition with perforated board.",
"Tabique de yeso laminado en áticos.":
    "Drywall partition in an attic.",
"Tabique de yeso laminado con cámara para instalaciones.":
    "Drywall partition with a service void.",
"Tabique de yeso laminado de una sola placa.":
    "Drywall partition with a single layer of board.",
"Tabique de yeso laminado con placa de alta dureza doble.":
    "Drywall partition with two layers of high-impact board.",
"Tabique de yeso laminado con bastidor de madera.":
    "Drywall partition on a lumber frame.",

# ── Otras particiones y mamparas ──────────────────────────────────────────
"Pared de bloque de vidrio.":
    "Glass block wall.",
"Tabique de placa de cemento sobre estructura metálica.":
    "Cement board partition on a metal frame.",
"Tabique de paneles livianos prefabricados.":
    "Partition of lightweight prefabricated panels.",
"División liviana de machihembrado de madera.":
    "Lightweight tongued and grooved lumber divider.",
"Tabique de placa de cemento con aislamiento.":
    "Cement board partition with insulation.",
"Tabique de panel liviano prefabricado.":
    "Partition of a lightweight prefabricated panel.",
"División de machihembrado de madera.":
    "Tongued and grooved lumber divider.",
"División de bloques de vidrio.":
    "Glass block divider.",
"División liviana de placa de cemento.":
    "Lightweight cement board divider.",
"División liviana con revestimiento de melamina.":
    "Lightweight melamine faced divider.",
"División liviana con panel de PVC.":
    "Lightweight PVC panel divider.",
"Mampara divisoria de oficina.":
    "Office partition.",
"Tabique móvil o plegable.":
    "Movable or folding partition.",
"Mampara divisoria de oficina con puerta.":
    "Office partition with a door.",
"Mampara acristalada de oficina.":
    "Glazed office partition.",
"Tabique móvil o plegable acústico.":
    "Acoustic movable or folding partition.",
"Mampara divisoria con panel de vidrio.":
    "Partition with a glass panel.",
"Mampara de oficina con panel textil.":
    "Office partition with a fabric panel.",
"Tabique móvil corredero.":
    "Sliding movable partition.",
"Mampara de baño de vidrio esmerilado.":
    "Frosted glass bathroom screen.",
"Mampara de oficina con doble acristalamiento.":
    "Office partition with double glazing.",
"Mampara de ducha a ras de piso.":
    "Walk-in shower panel.",
"Mampara divisoria con vidrio laminado.":
    "Partition with laminated glass.",
"Tabique plegable de paneles.":
    "Folding panel partition.",
"Mampara de oficina con perfilería vista.":
    "Office partition with exposed framing.",

# ── Dinteles, jambas y remates de vano ────────────────────────────────────
"Dintel prefabricado de concreto sobre vano.":
    "Precast concrete lintel over an opening.",
"Dintel de concreto armado vaciado en sitio.":
    "Cast-in-place reinforced concrete lintel.",
"Brocal o antepecho de ventana.":
    "Window sill or apron.",
"Formación de jambas y mochetas de vano.":
    "Formation of the jambs and reveals of an opening.",
"Remate y sellado del encuentro de pared con estructura.":
    "Finishing and sealing of the junction between a wall and the structure.",
"Dintel de concreto armado encofrado en sitio.":
    "Cast-in-site reinforced concrete lintel.",
"Dintel de bloque canal con refuerzo.":
    "Reinforced bond beam block lintel.",
"Formación de jambas y mochetas de vano con mortero.":
    "Formation of the jambs and reveals of an opening in mortar.",
"Brocal o antepecho de ventana de concreto.":
    "Concrete window sill or apron.",
"Remate y sellado de encuentro pared-estructura.":
    "Finishing and sealing of the wall and structure junction.",
"Remate de vano con perfil de aluminio.":
    "Finishing of an opening with an aluminum profile.",
"Dintel metálico para vano.":
    "Steel lintel for an opening.",
"Vierteaguas de concreto.":
    "Concrete weather sill.",
"Remate de mocheta con cantonera.":
    "Finishing of a reveal with a corner bead.",
"Dintel de madera para vano.":
    "Wood lintel for an opening.",
"Remate de vano con piedra artificial.":
    "Finishing of an opening with cast stone.",
"Refuerzo de vano con perfil de acero.":
    "Reinforcement of an opening with a steel profile.",
"Dintel prefabricado de concreto armado.":
    "Precast reinforced concrete lintel.",

# ── Frente de losa ────────────────────────────────────────────────────────
"Tratamiento y remate de frente de losa en fachada.":
    "Treatment and finishing of the slab edge on a facade.",
"Cajón de persiana en dintel de ventana.":
    "Roller shutter box in a window lintel.",
"Tratamiento de frente de losa en fachada.":
    "Treatment of the slab edge on a facade.",
"Cajón de persiana en dintel con registro.":
    "Roller shutter box in a lintel, with an access panel.",
"Remate de frente de losa con perfil.":
    "Finishing of the slab edge with a profile.",
"Cajón de persiana aislado.":
    "Insulated roller shutter box.",
"Remate de losa con cornisa.":
    "Finishing of a slab edge with a cornice.",
"Remate de frente de losa con aislamiento.":
    "Finishing of the slab edge with insulation.",

# ── Fachada ventilada y SATE ──────────────────────────────────────────────
"Fachada ventilada de panel composite.":
    "Ventilated facade of sandwich panels.",
"Fachada ventilada de gres porcelánico.":
    "Ventilated facade of porcelain stoneware.",
"Fachada ventilada de piedra natural.":
    "Ventilated facade of natural stone.",
"Fachada ventilada de fibrocemento.":
    "Ventilated facade of fiber cement.",
"Fachada ventilada de listones de madera.":
    "Ventilated facade of lumber battens.",
"Sistema de aislamiento térmico exterior (SATE).":
    "Exterior insulation and finish system (EIFS).",
"SATE con acabado acrílico.":
    "EIFS with an acrylic finish.",
"SATE con panel de alta densidad.":
    "EIFS with a high-density board.",
"SATE en fachada con remates.":
    "EIFS on a facade, including trims.",
"SATE con lana mineral.":
    "EIFS with mineral wool.",
"SATE de zócalo con panel de alta densidad.":
    "EIFS on a base with a high-density board.",
"SATE de muro con acabado texturado.":
    "EIFS on a wall with a textured finish.",

# ── Celosías y defensas ───────────────────────────────────────────────────
"Celosía de fachada de aluminio.":
    "Aluminum facade louver screen.",
"Celosía de fachada de madera.":
    "Lumber facade louver screen.",
"Celosía cerámica de fachada.":
    "Ceramic facade louver screen.",
"Cerramiento de lamas orientables.":
    "Adjustable louver screen.",
"Celosía metálica decorativa.":
    "Decorative metal louver screen.",
"Celosía de fachada de acero.":
    "Steel facade louver screen.",
"Cerramiento de fachada con lamas de PVC.":
    "Facade screen with PVC louvers.",
"Malla de protección de fachada.":
    "Protective facade mesh.",
"Barandilla de fachada con defensa.":
    "Facade guardrail with a protective barrier.",
"Protección de fachada contra impactos.":
    "Facade impact protection.",
"Defensa de fachada con reja.":
    "Facade guard with a grille.",
"Defensa de fachada de acero inoxidable.":
    "Stainless steel facade guard.",

# ── Limpieza, protección y restauración de fachada ────────────────────────
"Limpieza de fachada con hidrolavado.":
    "Pressure washing of a facade.",
"Tratamiento fungicida de fachada contra moho y verdín.":
    "Fungicidal treatment of a facade against mold and algae.",
"Limpieza química de fachada y eliminación de manchas.":
    "Chemical cleaning of a facade and removal of stains.",
"Aplicación de hidrofugante incoloro en fachada.":
    "Application of a clear water repellent to a facade.",
"Limpieza de fachada con proyección de arena.":
    "Sandblasting of a facade.",
"Limpieza de fachada con cepillado en seco.":
    "Dry brushing of a facade.",
"Limpieza de fachada con hidrolavado a presión.":
    "Pressure washing of a facade.",
"Tratamiento fungicida de fachada.":
    "Fungicidal treatment of a facade.",
"Eliminación de grafitis en fachada.":
    "Removal of graffiti from a facade.",
"Eliminación de eflorescencias en fachada.":
    "Removal of efflorescence from a facade.",
"Reparación de fisuras en fachada.":
    "Repair of cracks in a facade.",
"Restauración de friso de fachada.":
    "Restoration of facade stucco.",
"Restauración de revestimiento de fachada.":
    "Restoration of facade cladding.",
"Aplicación de hidrofugante en fachada.":
    "Application of a water repellent to a facade.",
"Protección anti-graffiti de fachada.":
    "Anti-graffiti protection for a facade.",
"Limpieza química de fachada de piedra.":
    "Chemical cleaning of a stone facade.",
"Limpieza de fachada de ladrillo visto.":
    "Cleaning of a face brick facade.",
"Restauración de juntas de fachada.":
    "Restoration of facade joints.",
"Tratamiento de humedad en fachada.":
    "Damp treatment on a facade.",
"Reparación de muro de fachada.":
    "Repair of a facade wall.",
"Limpieza de fachada con agua a baja presión.":
    "Low-pressure washing of a facade.",
"Restauración de moldura de fachada.":
    "Restoration of a facade molding.",
"Tratamiento anticarbónico de fachada.":
    "Anti-carbonation treatment of a facade.",
}
