# -*- coding: utf-8 -*-
"""Nombres de partida — Fundaciones (capítulo completo, 100).

Criterios de este lote:
  · «Concreto pobre de limpieza» es mud slab en Estados Unidos y blinding
    en Reino Unido: la capa pobre que se echa para no manchar el acero.
  · «Zapata aislada» es isolated footing, «corrida» es strip footing y
    «combinada» es combined footing.
  · «Recalce» es underpinning, que es una sola palabra de oficio y no
    tiene traducción literal posible.
  · «Descabezado de pilote» es pile cut-off: se corta la cabeza del pilote
    a la cota del cabezal.
  · «Trasdós» de un muro de contención es la cara que da a la tierra: en
    inglés se dice rear face, y el drenaje que se le pone detrás es
    drainage behind the wall.
  · «Anime» vuelve a ser EPS void formers.
"""

LOTE = {
# ── Mejoramiento del terreno ──────────────────────────────────────────────
"Sustitución de terreno con material granular.":
    "Replacement of unsuitable soil with granular fill.",
"Mejoramiento de suelo con cemento.": "Soil stabilization with cement.",
"Nivelación y compactación de fondo de fundación.":
    "Leveling and compaction of the foundation bearing surface.",
"Riego y compactación de fundación.":
    "Watering and compaction of a foundation.",
"Verificación de capacidad portante.":
    "Verification of the bearing capacity.",
"Mejoramiento de fundación con geotextil.":
    "Improvement of a foundation with a geotextile.",
"Limpieza y saneo de fondo de fundación.":
    "Cleaning and preparation of the foundation bearing surface.",
"Concreto pobre de limpieza bajo fundaciones, 5 cm de espesor.":
    "5 cm mud slab beneath foundations.",
"Concreto pobre de limpieza bajo fundación.":
    "Mud slab beneath a foundation.",

# ── Zapatas ───────────────────────────────────────────────────────────────
"Acero de refuerzo en zapatas y bases.":
    "Reinforcement in footings and bases.",
"Encofrado y desencofrado de zapata.":
    "Formwork and stripping to a footing.",
"Concreto para zapata aislada.": "Concrete for an isolated footing.",
"Concreto para zapata corrida.": "Concrete for a strip footing.",
"Pedestal de concreto armado sobre fundación.":
    "Reinforced concrete pedestal on a foundation.",
"Dado o base de concreto para equipo o máquina.":
    "Concrete base or plinth for equipment or machinery.",
"Recalce de fundación existente.":
    "Underpinning of an existing foundation.",
"Refuerzo y ampliación de zapata existente.":
    "Strengthening and enlargement of an existing footing.",
"Concreto para zapata combinada.": "Concrete for a combined footing.",
"Concreto para zapata de medianería.":
    "Concrete for a party wall footing.",
"Acero de refuerzo en zapata.": "Reinforcement in a footing.",
"Encofrado de zapata.": "Formwork to a footing.",
"Concreto para base de equipo.": "Concrete for an equipment base.",
"Recalce de zapata con concreto.": "Underpinning of a footing in concrete.",
"Refuerzo de zapata existente con acero.":
    "Strengthening of an existing footing with steel.",
"Concreto para pedestal de concreto armado.":
    "Concrete for a reinforced concrete pedestal.",

# ── Vigas de fundación ────────────────────────────────────────────────────
"Acero de refuerzo en vigas de riostra.":
    "Reinforcement in tie beams.",
"Encofrado y desencofrado de viga de riostra.":
    "Formwork and stripping to a tie beam.",
"Concreto para viga de riostra.": "Concrete for a tie beam.",
"Acero de refuerzo en viga de riostra.":
    "Reinforcement in a tie beam.",
"Encofrado de viga de riostra.": "Formwork to a tie beam.",
"Vaciado de concreto en viga de riostra.":
    "Concrete pour in a tie beam.",
"Concreto para viga de fundación.": "Concrete for a foundation beam.",
"Acero de refuerzo en viga de fundación.":
    "Reinforcement in a foundation beam.",
"Viga de riostra con bloque lateral.":
    "Tie beam with a side block.",
"Viga de fundación sobre suelo mejorado.":
    "Foundation beam on improved ground.",
"Encofrado de viga de fundación.": "Formwork to a foundation beam.",
"Concreto para viga de amarre.": "Concrete for a tie beam.",
"Viga de riostra con junta de dilatación.":
    "Tie beam with an expansion joint.",

# ── Losas de fundación ────────────────────────────────────────────────────
"Barrera de vapor de polietileno bajo losa de fundación.":
    "Polyethylene vapor barrier beneath a foundation slab.",
"Acero de refuerzo en losa de fundación.":
    "Reinforcement in a foundation slab.",
"Malla electrosoldada de refuerzo en losa.":
    "Welded wire mesh reinforcement in a slab.",
"Encofrado perimetral de losa de fundación.":
    "Perimeter formwork to a foundation slab.",
"Concreto para losa de fundación.": "Concrete for a foundation slab.",
"Acabado y curado de losa de fundación.":
    "Finishing and curing of a foundation slab.",
"Barrera de vapor bajo losa de fundación.":
    "Vapor barrier beneath a foundation slab.",
"Aislamiento térmico bajo losa de fundación.":
    "Thermal insulation beneath a foundation slab.",
"Colocación de acero en losa de fundación.":
    "Placing of reinforcement in a foundation slab.",
"Malla electrosoldada en losa.": "Welded wire mesh in a slab.",
"Encofrado perimetral de losa.": "Perimeter formwork to a slab.",
"Vaciado de concreto en losa de fundación.":
    "Concrete pour in a foundation slab.",
"Acabado de losa de fundación.": "Finishing of a foundation slab.",
"Losa de fundación aligerada con anime.":
    "Foundation slab lightened with EPS void formers.",
"Junta de dilatación en losa de fundación.":
    "Expansion joint in a foundation slab.",
"Losa de fundación con aditivo impermeabilizante.":
    "Foundation slab with a waterproofing admixture.",

# ── Muros de contención ───────────────────────────────────────────────────
"Encofrado a dos caras de muro de contención.":
    "Double-face formwork to a retaining wall.",
"Acero de refuerzo en muro de contención.":
    "Reinforcement in a retaining wall.",
"Concreto para muro de contención.": "Concrete for a retaining wall.",
"Impermeabilización del trasdós de muro de contención.":
    "Waterproofing of the rear face of a retaining wall.",
"Drenaje de trasdós de muro con tubería y grava.":
    "Drainage behind a wall with pipe and gravel.",
"Encofrado de muro de contención a dos caras.":
    "Double-face formwork to a retaining wall.",
"Colocación de acero en muro de contención.":
    "Placing of reinforcement in a retaining wall.",
"Vaciado de concreto en muro de contención.":
    "Concrete pour in a retaining wall.",
"Impermeabilización de trasdós de muro.":
    "Waterproofing of the rear face of a wall.",
"Drenaje de trasdós con tubería y grava.":
    "Drainage behind a wall with pipe and gravel.",
"Muro de contención con acabado visto.":
    "Retaining wall with an exposed finish.",
"Muro de contención de bloque con refuerzo.":
    "Reinforced blockwork retaining wall.",
"Muro de contención con junta de dilatación.":
    "Retaining wall with an expansion joint.",
"Reparación de muro de contención.": "Repair of a retaining wall.",
"Refuerzo de muro de contención existente.":
    "Strengthening of an existing retaining wall.",

# ── Pilotes ───────────────────────────────────────────────────────────────
"Perforación para pilote vaciado en sitio.":
    "Boring for a cast-in-place pile.",
"Acero de refuerzo en pilote.": "Reinforcement in a pile.",
"Concreto para pilote vaciado en sitio.":
    "Concrete for a cast-in-place pile.",
"Descabezado de pilote.": "Pile cut-off.",
"Cabezal de pilotes de concreto armado.":
    "Reinforced concrete pile cap.",
"Perforación de pilote vaciado en sitio.":
    "Boring of a cast-in-place pile.",
"Colocación de acero en pilote.": "Placing of reinforcement in a pile.",
"Vaciado de concreto en pilote.": "Concrete pour in a pile.",
"Descabezado de pilote de concreto.": "Cut-off of a concrete pile.",
"Concreto para cabezal de pilotes.": "Concrete for a pile cap.",
"Acero de refuerzo en cabezal de pilotes.":
    "Reinforcement in a pile cap.",
"Encofrado de cabezal de pilotes.": "Formwork to a pile cap.",
"Concreto para pilote de sección grande.":
    "Concrete for a large-diameter pile.",
"Pilote con camisa metálica.": "Pile with a steel casing.",
"Concreto para pila de puente.": "Concrete for a bridge pier.",

# ── Drenaje, impermeabilización y refuerzo ────────────────────────────────
"Drenaje perimetral de fundación.":
    "Perimeter drainage to a foundation.",
"Drenaje con canaleta de fundación.":
    "Drainage with a channel at a foundation.",
"Impermeabilización de fundación con manto.":
    "Waterproofing of a foundation with a membrane.",
"Protección de fundación con lámina drenante.":
    "Protection of a foundation with a drainage membrane.",
"Impermeabilización de fundación con geocompuesto de bentonita.":
    "Waterproofing of a foundation with a bentonite geocomposite.",
"Impermeabilización de fundación con cementosa.":
    "Waterproofing of a foundation with a cementitious membrane.",
"Protección de fundación contra raíces.":
    "Protection of a foundation against roots.",
"Impermeabilización de losa de fundación.":
    "Waterproofing of a foundation slab.",
"Reparación de fundación con mortero.":
    "Repair of a foundation with mortar.",
"Reparación de fisuras en fundación.":
    "Repair of cracks in a foundation.",
"Refuerzo de fundación con encamisado.":
    "Strengthening of a foundation by jacketing.",
"Refuerzo de fundación con fibra de carbono.":
    "Strengthening of a foundation with carbon fiber.",
"Refuerzo de zapata con ampliación.":
    "Strengthening of a footing by enlargement.",
"Refuerzo de fundación con micropilotes.":
    "Strengthening of a foundation with micropiles.",
"Refuerzo de fundación con mortero de alta resistencia.":
    "Strengthening of a foundation with high-strength mortar.",
"Refuerzo de fundación con recalce.":
    "Strengthening of a foundation by underpinning.",
}
