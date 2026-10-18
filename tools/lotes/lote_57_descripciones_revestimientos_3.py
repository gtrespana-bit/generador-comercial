# -*- coding: utf-8 -*-
"""Descripciones — Revestimientos y acabados (3 de n): frisos y morteros.

El bloque de morteros, donde el español del catálogo es venezolano y el
inglés tiene que ser el del oficio anglosajón sin perder las
distinciones: «friso» y «repello» no son lo mismo y aquí cada uno tiene
su nombre.

Vocabulario aplicado:

· «Friso» es stucco. «Repello» es su capa base cuando se distingue de
  la de acabado: stucco base coat. En el Reino Unido ambos son render,
  y la variante lo ajusta.
· «Maestreado» es screeded: puesto con maestras. «Reglado» es ruling
  off, que es pasar la regla, y no screeding, que ya está usado.
· «Fratasado» es floating y el acabado «a la llana» es trowel finish.
  Son dos acabados distintos y el inglés los distingue.
· «Media caña» es coving, la pieza curva que elimina la arista viva en
  el encuentro de pared con piso.
· «Aplomada» es plumb; «desplome» es out of plumb.
· «Arena cernida» es screened sand y «hidrófugo de masa» es integral
  waterproofing admixture, el que va en la masa y no en la superficie.
· «Curado» es curing, y es la palabra que falta cuando el mortero
  fisura: sin curado no hay mortero que aguante.
· «Boquilla» es grout, el relleno de la junta, y «rejuntado» es
  grouting, la operación.
· «Sondeo por golpeo» es sounding by tapping, como se delimita lo que
  está hueco antes de picar.
· «Proyección» del mortero es spraying y la máquina es spraying
  machine; el rendimiento que menciona la partida es output.
"""

LOTE = {
    "Preparación de soporte para la colocación de papel tapiz, con resane, lijado e imprimación. Incluye el alisado y la aplicación de la imprimación. Medido por metro cuadrado preparado.":
        "Preparation of the substrate for hanging wallpaper, with patching, sanding and priming. Includes smoothing and applying the primer. Measured per square meter prepared.",

    "Regularización de techo de concreto previo a la instalación de cielo raso o pintura, con mortero o pasta de nivelación. Incluye la corrección de desniveles y el afinado. Medido por metro cuadrado regularizado.":
        "Making a concrete soffit level prior to the installation of a ceiling or painting, with mortar or leveling compound. Includes correcting the unevenness and the finishing. Measured per square meter made level.",

    "Reparación de junta de dilatación en paramento, con retirada del sellado deteriorado y aplicación de sellador elástico. Incluye la limpieza de la junta y el nuevo sellado. Medido por metro lineal reparado.":
        "Repair of a movement joint in a substrate, removing the deteriorated sealant and applying a flexible sealant. Includes cleaning the joint and the new sealing. Measured per meter repaired.",

    "Replanteo y nivelación de paramento con nivel láser previo a friso o enchapado, para garantizar plomos y niveles. Incluye la comprobación con láser y el marcado de maestras. Medido por metro cuadrado nivelado.":
        "Field layout and leveling of a substrate with a laser level prior to stucco or tiling, to guarantee that it is plumb and level. Includes checking with the laser and marking out the screeds. Measured per square meter leveled.",

    "Friso de mortero de cemento y arena cernida sobre paramento interior de bloque o ladrillo, de 1,5 cm de espesor medio, maestreado y acabado a la llana. Incluye limpieza y humedecido previo del soporte, colocación de maestras y cantoneras en esquinas y encuentros, malla de refuerzo en los cambios de material, tendido y reglado del mortero, y acabado fratasado dejando la superficie plana y aplomada, lista para recibir pintura o revestimiento cerámico. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Cement and screened sand stucco over an interior block or brick substrate, 1.5 cm average thickness, screeded and finished with a trowel. Includes cleaning and wetting the substrate beforehand, placing screeds and corner beads at corners and junctions, reinforcing mesh at changes of material, laying and ruling off the mortar, and a floated finish leaving the surface flat and plumb, ready to receive paint or ceramic tiling. Measured by the area actually completed, deducting openings over 1 m².",

    "Friso de mortero de cemento y arena con aditivo hidrófugo de masa, de 2 cm de espesor medio, maestreado y fratasado sobre paramento exterior de bloque o ladrillo. El hidrófugo reduce la absorción capilar del mortero, que es la vía por la que la lluvia batiente termina apareciendo como humedad en la cara interior. Incluye el trabajo desde andamio, la limpieza y humedecido del soporte, la colocación de maestras y cantoneras, la malla de refuerzo en los encuentros de materiales distintos, el tendido y reglado del mortero en dos capas, el fratasado final y el curado durante los primeros días, sin el cual el friso exterior fisura por retracción. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Cement and sand stucco with an integral waterproofing admixture, 2 cm average thickness, screeded and floated over an exterior block or brick substrate. The waterproofing admixture reduces the capillary absorption of the mortar, which is the route by which driving rain ends up appearing as damp on the inner face. Includes working from scaffolding, cleaning and wetting the substrate, placing screeds and corner beads, the reinforcing mesh at the junctions between different materials, laying and ruling off the mortar in two coats, the final floating and curing over the first few days, without which exterior stucco cracks through shrinkage. Measured by the area actually completed, deducting openings over 1 m².",

    "Revestimiento de fachada con friso rústico texturado, aplicado sobre friso base o directamente sobre la mampostería, con acabado obtenido por proyección o por peinado según la textura elegida. Incluye el trabajo desde andamio, la preparación y humedecido del soporte, la aplicación de la capa base, la ejecución de la textura de forma continua por paños completos entre juntas o quiebres para evitar que se marquen las paradas de trabajo, y el curado. La uniformidad del acabado depende de mantener la misma cuadrilla y la misma dosificación en todo el paño. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Textured rustic stucco on a facade, applied over a stucco base coat or directly over the masonry, with the finish obtained by spraying or by combing depending on the texture chosen. Includes working from scaffolding, preparing and wetting the substrate, applying the base coat, working the texture continuously over complete bays between joints or breaks so that the stoppages do not show, and curing. The uniformity of the finish depends on keeping the same crew and the same mix throughout the whole bay. Measured by the area actually completed, deducting openings over 1 m².",

    "Aplicación de mortero impermeabilizante cementoso flexible en dos manos sobre el paramento de zonas de ducha y áreas de contacto directo con agua, como base bajo el enchapado. Es la capa que realmente impide el paso del agua: la cerámica y su boquilla no son estancas, y sin esta base la humedad termina apareciendo en la habitación contigua. Incluye la regularización previa del soporte, el redondeo o refuerzo con banda elástica de los encuentros de pared con piso y de las esquinas, que son los puntos por donde falla el sistema, la aplicación de las dos manos cruzadas respetando el tiempo entre ellas y la prueba de estanqueidad antes de enchapar. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Application of a flexible cementitious waterproofing mortar in two coats to the substrate in shower areas and areas in direct contact with water, as a base beneath the tiling. This is the layer that actually stops the water: ceramic tile and its grout are not watertight, and without this base the damp ends up appearing in the adjoining room. Includes making the substrate level beforehand, rounding off or reinforcing the wall and floor junctions and the corners with flexible tape, which are the points where the system fails, applying the two coats crosswise respecting the time between them and the watertightness test before tiling. Measured by the area actually completed, deducting openings over 1 m².",

    "Regularización de paramento existente mediante repello de mortero de espesor variable, para corregir desplomes, resanar zonas picadas y dejar la superficie apta para recibir el acabado. Se emplea en reforma cuando el friso existente está sano en su mayor parte y solo requiere reparación y nivelación, evitando el picado completo. Incluye el sondeo por golpeo para delimitar y retirar las zonas huecas, la limpieza y humedecido, la aplicación del puente de adherencia en las zonas de mayor espesor, el tendido y reglado del mortero enrasando con el friso existente, y el fratasado dejando una transición imperceptible entre lo nuevo y lo conservado. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Making an existing substrate level by means of a stucco base coat of varying thickness, to correct out of plumb, patch hacked areas and leave the surface fit to receive the finish. It is used in remodeling where the existing stucco is mostly sound and only needs repair and leveling, avoiding hacking off the whole of it. Includes sounding by tapping to mark out and remove the hollow areas, cleaning and wetting, applying the bonding coat in the areas of greater thickness, laying and ruling off the mortar flush with the existing stucco, and floating, leaving an imperceptible transition between the new work and what has been kept. Measured by the area actually completed, deducting openings over 1 m².",

    "Friso de mortero aplicado mediante máquina de proyección, maestreado y fratasado. La proyección mecánica multiplica el rendimiento frente al tendido a mano y mejora la compactación y la adherencia del mortero contra el soporte, por lo que compensa a partir de superficies medianas. Incluye la limpieza y humedecido del soporte, la colocación de maestras y cantoneras, el amasado y bombeo continuo, la proyección por franjas, el reglado, el fratasado y el curado. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Mortar stucco applied by a spraying machine, screeded and floated. Mechanical spraying multiplies the output compared with laying by hand and improves the compaction and the adhesion of the mortar against the substrate, so it pays off from medium sized areas upwards. Includes cleaning and wetting the substrate, placing screeds and corner beads, continuous mixing and pumping, spraying in bands, ruling off, floating and curing. Measured by the area actually completed, deducting openings over 1 m².",

    "Formación de media caña de mortero en el encuentro de pared con piso, para eliminar la arista interior en cocinas, áreas de servicio y locales de higiene exigente. La arista viva es donde se acumula la suciedad y por donde el agua de limpieza penetra bajo el revestimiento; la media caña la elimina y permite el barrido continuo. Incluye la limpieza y humedecido, el tendido del mortero con hidrófugo, la conformación con plantilla y el fratasado dejando la superficie lista para recibir el revestimiento o el sellado. Medido en longitud realmente ejecutada.":
        "Forming a mortar cove at the junction of the wall and the floor, to remove the internal arris in kitchens, service areas and premises with demanding hygiene requirements. The sharp arris is where dirt builds up and where cleaning water gets in under the covering; the cove removes it and allows continuous sweeping. Includes cleaning and wetting, laying the mortar with a waterproofing admixture, shaping it with a template and floating, leaving the surface ready to receive the covering or the sealer. Measured by the length actually completed.",

    "Repello y afinado de la mocheta o arista de un vano de puerta o ventana, con cantonera de refuerzo, dejando la arista recta y aplomada. La arista de un vano es lo primero que se mira al entrar a un ambiente y lo primero que se golpea, de modo que la cantonera no es solo un elemento de guía sino la protección que evita el desconchado permanente. Incluye la limpieza, la colocación y aplomado de la cantonera, el tendido y reglado del mortero a ambas caras y el fratasado. Medido en longitud de arista realmente ejecutada.":
        "Stucco base coat and finishing of the reveal or arris of a door or window opening, with a reinforcing corner bead, leaving the arris straight and plumb. The arris of an opening is the first thing looked at on entering a room and the first thing that gets knocked, so the corner bead is not only a guide but the protection that prevents permanent chipping. Includes the cleaning, placing and plumbing the corner bead, laying and ruling off the mortar on both faces, and floating. Measured by the length of arris actually completed.",
}
