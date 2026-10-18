# -*- coding: utf-8 -*-
"""Descripciones — Revestimientos y acabados (4 de n): yesos y acabados finos.

Aquí el español distingue «friso» (la capa de mortero o de yeso) del
«enlucido» (la capa fina que va encima), y el inglés también: stucco o
plaster para la primera y skim coat para la segunda. Se mantiene la
distinción porque son partidas distintas en el catálogo.

Vocabulario aplicado:

· «Friso» de yeso interior es plaster; el de mortero exterior es
  stucco, que es el término americano, y el británico lo dice render.
  En la cola de medición se usa plastered, que sirve en los dos lados
  del Atlántico.
· «Enlucido» es skim coat y su operación es skimming.
· «Bruñido» es burnished: el acabado apretado con la llana hasta que
  la superficie se cierra.
· «Luz rasante» es raking light, la luz que va casi paralela a la
  pared y por eso delata cualquier ondulación.
· «Corte a inglete» es mitring y la moldura «corrida» es continuous.
· «Gotelé» es textured finish: en el Reino Unido se diría artex, pero
  es marca registrada y aquí no se usa.
· «Pasta» es compound cuando alisa y filler cuando rellena; «amasado»
  es mixing y su «tiempo de trabajabilidad» es working time.
· «Enrase» es flushing up, dejar a ras de la superficie existente.
"""

LOTE = {
    "Aplicación de friso de mortero de cal sobre paramento interior, con acabado fino. Incluye la preparación de la mezcla, las maestras y el afinado. Medido por metro cuadrado frisado.":
        "Application of lime mortar plaster to an interior substrate, with a fine finish. Includes preparing the mix, the screeds and the finishing. Measured per square meter plastered.",

    "Aplicación de friso en fachada con malla de refuerzo embebida para prevenir fisuración. Incluye la colocación de la malla y la aplicación del mortero. Medido por metro cuadrado frisado.":
        "Application of stucco on a facade with embedded reinforcing mesh to prevent cracking. Includes fitting the mesh and applying the mortar. Measured per square meter plastered.",

    "Aplicación de friso con mortero impermeabilizante en muro de contención o de sótano. Incluye la preparación del soporte y la aplicación del mortero impermeabilizante. Medido por metro cuadrado frisado.":
        "Application of stucco with waterproofing mortar on a retaining wall or basement wall. Includes preparing the substrate and applying the waterproofing mortar. Measured per square meter plastered.",

    "Aplicación de friso de mortero coloreado en paramento interior o exterior, con acabado liso. Incluye las maestras, la aplicación del mortero coloreado y el afinado. Medido por metro cuadrado frisado.":
        "Application of colored mortar plaster to an interior or exterior substrate, with a smooth finish. Includes the screeds, applying the colored mortar and the finishing. Measured per square meter plastered.",

    "Aplicación de friso de mortero con acabado bruñido, para paramentos interiores. Incluye la aplicación del mortero, el bruñido y el afinado final. Medido por metro cuadrado frisado.":
        "Application of mortar plaster with a burnished finish, for interior substrates. Includes applying the mortar, the burnishing and the final finishing. Measured per square meter plastered.",

    "Friso de pasta de yeso de 1,2 cm de espesor medio aplicado sobre paramento interior de mampostería, maestreado y acabado a la llana. Frente al friso de mortero ofrece un acabado más liso y un rendimiento notablemente mayor, pero no admite humedad, por lo que queda descartado en baños, cocinas expuestas y paredes en contacto con el exterior. Incluye la limpieza del soporte, la colocación de maestras y cantoneras, el amasado de la pasta en cantidades ajustadas al tiempo de trabajabilidad, el tendido y reglado, y el acabado a la llana hasta dejar la superficie lista para pintar. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Gypsum plaster of 1.2 cm average thickness applied over an interior masonry substrate, screeded and finished with a trowel. Compared with mortar stucco it offers a smoother finish and a markedly higher output, but it does not tolerate moisture, so it is ruled out in bathrooms, exposed kitchens and walls in contact with the exterior. Includes cleaning the substrate, placing screeds and corner beads, mixing the compound in quantities matched to the working time, laying and ruling off, and finishing with a trowel until the surface is ready to paint. Measured by the area actually completed, deducting openings over 1 m².",

    "Capa de acabado fino de pasta aplicada sobre friso de mortero o de yeso, de 2 a 3 mm de espesor, para obtener una superficie tersa apta para pinturas de alto brillo o para acabados donde cualquier irregularidad se marca con la luz rasante. Incluye la comprobación y el sellado previo del soporte, la aplicación de la pasta en dos manos cruzadas con llana, el lijado entre manos y el lijado final con aspiración, y la revisión con luz rasante para detectar y corregir los defectos que solo aparecen bajo esa iluminación. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Fine finishing coat of compound applied over mortar or gypsum plaster, 2 to 3 mm thick, to obtain a smooth surface suitable for high gloss paints or for finishes where any irregularity shows up under raking light. Includes checking and sealing the substrate beforehand, applying the compound in two crosswise coats with a trowel, sanding between coats and the final sanding with extraction, and going over it under raking light to find and correct the defects that only appear under that lighting. Measured by the area actually completed, deducting openings over 1 m².",

    "Alisado de paramento existente mediante aplicación de pasta de nivelación a llana, para corregir irregularidades menores, marcas de rodillo, gotelé fino o restos de acabados anteriores, dejando la superficie plana. Es la alternativa económica al picado y refriso cuando el paramento está sano pero con textura o defectos superficiales. Incluye el raspado de las partes sueltas, la aplicación del fondo fijador, el extendido de la pasta en una o dos manos según el defecto a corregir, el lijado con aspiración y el repaso final. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Smoothing of an existing substrate by applying leveling compound with a trowel, to correct minor irregularities, roller marks, a fine textured finish or the remains of previous finishes, leaving the surface flat. It is the economical alternative to hacking off and re-plastering when the substrate is sound but has a texture or surface defects. Includes scraping the loose parts, applying the stabilizing primer, spreading the compound in one or two coats depending on the defect to be corrected, sanding with extraction and the final going over. Measured by the area actually completed, deducting openings over 1 m².",

    "Suministro y colocación de moldura decorativa corrida de yeso o poliuretano en el encuentro de pared y cielo raso o como elemento decorativo en paramento, recibida con pasta de agarre. Incluye el replanteo de la línea de referencia con nivel, el corte a inglete de los encuentros en esquinas interiores y exteriores, la colocación con pasta, el relleno y alisado de las juntas entre piezas hasta hacerlas imperceptibles, y el repaso final dejando la moldura lista para pintar. Medido en longitud realmente colocada.":
        "Supply and installation of a continuous decorative molding in plaster or polyurethane at the junction of the wall and the ceiling or as a decorative element on a substrate, bedded in adhesive compound. Includes setting out the reference line with a level, mitring the joints at internal and external corners, fixing with compound, filling and smoothing the joints between lengths until they are imperceptible, and the final going over leaving the molding ready to paint. Measured by the length actually installed.",

    "Reparación de zonas puntuales de friso de yeso deteriorado por golpes, humedades ya resueltas o desprendimientos, con reposición del material y enrase con el friso existente. Incluye la delimitación y retirada del material suelto hasta encontrar friso sano y bien adherido, la limpieza y humedecido del borde, la aplicación del puente de adherencia, la reposición por capas de la pasta, el enrase con la superficie existente y el lijado de la transición. En reparaciones sobre humedades es imprescindible haber eliminado antes la causa, porque de lo contrario la zona vuelve a fallar. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Repair of localized areas of gypsum plaster damaged by knocks, damp that has already been dealt with, or areas that have come away, replacing the material and flushing up with the existing plaster. Includes marking out and removing the loose material until sound, well adhered plaster is found, cleaning and wetting the edge, applying the bonding coat, replacing the compound in layers, flushing up with the existing surface and sanding the transition. On repairs over damp it is essential to have removed the cause beforehand, because otherwise the area fails again. Measured by the area actually completed, deducting openings over 1 m².",

    "Aplicación de friso de yeso proyectado sobre paramento interior, con maestras y afinado. Incluye la preparación del soporte y la aplicación mecánica de la pasta de yeso. Medido por metro cuadrado frisado.":
        "Application of sprayed gypsum plaster to an interior substrate, with screeds and finishing. Includes preparing the substrate and the mechanical application of the gypsum compound. Measured per square meter plastered.",

    "Reparación de friso de yeso en zona amplia, con saneado del área, aplicación de pasta y afinado. Incluye la retirada del material suelto y la reposición del enlucido. Medido por metro cuadrado reparado.":
        "Repair of gypsum plaster over a wide area, making good the area, applying compound and finishing. Includes removing the loose material and replacing the skim coat. Measured per square meter repaired.",

    "Aplicación de friso de yeso con fibra de refuerzo para paramentos con mayor resistencia a la fisuración. Incluye la aplicación de la pasta reforzada y el afinado. Medido por metro cuadrado frisado.":
        "Application of gypsum plaster with reinforcing fiber for substrates with greater resistance to cracking. Includes applying the reinforced compound and the finishing. Measured per square meter plastered.",
}
