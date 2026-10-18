# -*- coding: utf-8 -*-
"""Descripciones — Revestimientos y acabados (6 de n): piedra natural.

Vocabulario aplicado:

· «Laja» es flagstone, la piedra en chapas irregulares, y «placa» de
  mármol es slab, que es como se llama en cantería al formato grande.
· «A hueso» es butt jointed: colocado pieza contra pieza, sin junta.
· «Resalto» entre piezas es lippage. Es la palabra del oficio y no
  tiene traducción literal que la sustituya.
· «Abrillantado con cristalizador» es buffing with a crystallizing
  agent, el tratamiento químico que saca el brillo del mármol.
· «Lodo» del pulido es slurry, y el «grano decreciente» son los granos
  de los discos, decreasing grit.
· «Fachada ventilada» es ventilated rainscreen facade; en inglés
  americano se dice rainscreen, que es lo que es la cámara.
· «Alta deformabilidad» del adhesivo es high deformability, la clase
  S1 y S2 de la norma europea.
· «Veta» es veining y «a juego» es to match.
· «Canto» de la pieza es edge, y el «alojamiento» del anclaje es
  housing.
"""

LOTE = {
    "Enchapado de paramento con pieza cerámica y junta coloreada decorativa, en capa fina. Incluye la colocación y el rejuntado con mortero de junta coloreado. Medido por metro cuadrado enchapado.":
        "Tiling of a substrate with ceramic tile and a decorative colored joint, in a thin bed. Includes laying and grouting with a colored grout. Measured per square meter tiled.",

    "Enchapado de vaso de piscina con pieza cerámica o mosaico, sobre impermeabilización. Incluye la preparación, la colocación y el rejuntado con mortero apto para inmersión. Medido por metro cuadrado enchapado.":
        "Tiling of a pool shell with ceramic tile or mosaic, over the waterproofing. Includes the preparation, laying and grouting with a mortar suitable for immersion. Measured per square meter tiled.",

    "Colocación en pared de pieza de mármol o granito en capa fina, con adhesivo cementoso blanco de altas prestaciones. El adhesivo blanco no es un capricho: los mármoles claros son translúcidos y un adhesivo gris se transparenta y mancha la pieza de forma irreversible. Incluye la comprobación y regularización del soporte, el replanteo del despiece atendiendo a la veta y al tono para que la composición sea continua, el doble encolado, la nivelación, los cortes con disco refrigerado, el rejuntado con junta mínima a juego y la limpieza con productos no ácidos. La pieza la elige el cliente y se presupuesta aparte. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Fastening of marble or granite to a wall in a thin bed, with a high performance white cementitious adhesive. The white adhesive is not a whim: light marbles are translucent and a grey adhesive shows through and stains the slab irreversibly. Includes checking and making the substrate level, field layout of the layout taking account of the veining and the tone so that the composition runs continuously, back buttering, leveling, cutting with a water cooled disc, grouting with a minimal joint to match and cleaning with non acidic products. The slab is selected by the client and priced separately. Measured by the area actually completed, deducting openings over 1 m².",

    "Colocación de laja o piedra natural de formato irregular en paramento interior o exterior, recibida con mortero o adhesivo de alta deformabilidad según el espesor y el peso de la pieza. Al no existir un despiece regular, el trabajo consiste en componer el paño pieza a pieza buscando el encaje y la distribución de tonos, lo que reduce el rendimiento respecto a cualquier enchapado modular. Incluye la selección y clasificación previa del material, el replanteo del paño, la colocación con junta irregular controlada, el rejuntado o el acabado a hueso según el diseño, la limpieza y la aplicación del sellador hidrofugante. La pieza la elige el cliente y se presupuesta aparte. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Fastening of flagstone or irregular format natural stone to an interior or exterior substrate, bedded in mortar or a high deformability adhesive depending on the thickness and the weight of the piece. As there is no regular layout, the work consists of composing the bay piece by piece looking for the fit and the distribution of tones, which reduces the output compared with any modular tiling. Includes selecting and sorting the material beforehand, field layout of the bay, laying with a controlled irregular joint, grouting or a butt jointed finish depending on the design, cleaning and applying the water repellent sealer. The stone is selected by the client and priced separately. Measured by the area actually completed, deducting openings over 1 m².",

    "Colocación de piezas de piedra natural en fachada mediante anclaje mecánico de acero inoxidable, sin depender del adhesivo como elemento portante. Es la solución obligada a partir de cierta altura, espesor o peso de pieza, donde un enchapado adherido no ofrece seguridad suficiente frente al desprendimiento. Incluye el trabajo desde andamio, el replanteo, el taladrado de los alojamientos en el canto de la pieza y en el soporte, la colocación de los anclajes con su resina, el aplomado y nivelación de cada pieza, el sellado de juntas y la limpieza. La pieza la elige el cliente y se presupuesta aparte. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Fastening of natural stone on a facade by means of stainless steel mechanical anchors, without relying on the adhesive as the load bearing element. It is the required solution beyond a certain height, thickness or weight of slab, where an adhered cladding does not offer sufficient security against the pieces coming away. Includes working from scaffolding, field layout, drilling the housings in the edge of the slab and in the substrate, placing the anchors with their resin, plumbing and leveling each slab, sealing the joints and cleaning. The stone is selected by the client and priced separately. Measured by the area actually completed, deducting openings over 1 m².",

    "Colocación de zócalo de piedra natural a juego con el piso o el paramento, recibido con adhesivo cementoso blanco. Incluye el replanteo de la altura, los cortes a inglete en esquinas y encuentros, la colocación con nivelación, el rejuntado y el sellado de la junta inferior con el piso. La pieza la elige el cliente y se presupuesta aparte. Medido en longitud realmente colocada.":
        "Fastening of a natural stone base to match the floor or the substrate, bedded in white cementitious adhesive. Includes field layout of the height, the mitre cuts at corners and junctions, fastening with leveling, grouting and sealing the bottom joint with the floor. The stone is selected by the client and priced separately. Measured by the length actually installed.",

    "Pulido y abrillantado en obra de enchapado de piedra natural, para igualar el plano entre piezas y recuperar o dar el brillo final. Se ejecuta cuando la piedra se coloca en bruto o cuando los pequeños resaltos entre piezas hacen necesario rectificar el plano completo. Incluye la protección del entorno, el pulido con pasadas sucesivas de grano decreciente con aporte de agua, la recogida y evacuación del lodo generado, el abrillantado con cristalizador, la limpieza y la aplicación del sellador hidrofugante y antimanchas. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Polishing and buffing of natural stone cladding on site, to even out the plane between slabs and to recover or give the final shine. It is carried out when the stone is laid unpolished or when the small lippage between slabs makes it necessary to correct the whole plane. Includes protecting the surroundings, polishing with successive passes of decreasing grit with water, collecting and removing the slurry generated, buffing with a crystallizing agent, cleaning and applying the water repellent and stain resistant sealer. Measured by the area actually completed, deducting openings over 1 m².",

    "Enchapado de paramento con placas de mármol pulido, en capa fina. Incluye la preparación del soporte, la colocación de las placas y el rejuntado. Medido por metro cuadrado enchapado.":
        "Cladding of a substrate with polished marble slabs, in a thin bed. Includes preparing the substrate, fastening the slabs and grouting. Measured per square meter clad.",

    "Pulido y abrillantado de enchapado de mármol en pared, para recuperar el brillo. Incluye el pulido mecánico y el abrillantado final. Medido por metro cuadrado pulido.":
        "Polishing and buffing of marble cladding on a wall, to recover the shine. Includes the mechanical polishing and the final buffing. Measured per square meter polished.",

    "Enchapado de paramento con pieza de piedra natural colocada con junta ancha de mortero. Incluye la preparación del soporte, la colocación y el rejuntado ancho. Medido por metro cuadrado enchapado.":
        "Cladding of a substrate with natural stone laid with a wide mortar joint. Includes preparing the substrate, fastening and the wide grouting. Measured per square meter clad.",

    "Enchapado de fachada ventilada con pieza de piedra natural sobre subestructura de anclaje. Incluye la fijación de los anclajes, la colocación de la pieza y el sellado de juntas abiertas. Medido por metro cuadrado enchapado.":
        "Cladding of a ventilated rainscreen facade with natural stone on an anchoring substructure. Includes fastening the anchors, placing the slab and sealing the open joints. Measured per square meter clad.",
}
