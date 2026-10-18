# -*- coding: utf-8 -*-
"""Descripciones — Revestimientos y acabados (7 de n): papeles, paneles y
revestimientos continuos.

Vocabulario aplicado:

· «Papel tapiz» es wallpaper y se cuelga, hanging, no se coloca. El
  «pegamento mural» es wallpaper adhesive y el «ajuste del dibujo» es
  pattern match.
· «Plomada» de la primera tira es plumbing the first length: de esa
  sale el aplomado de todas las demás.
· «Estuco veneciano» es Venetian plaster, y su «bruñido» es burnishing
  y su «encerado» waxing.
· «Madera técnica» es engineered wood y «machihembrado» es tongue and
  groove, montado con «encaje a presión», a driven fit.
· «Testa» de la madera es end grain, y es por donde más agua entra.
· «Rastrelado» es battens, y la cámara que dejan es cavity.
· «Microcemento» es microcement sin traducir, que es como se vende en
  todo el mundo.
· «Media pared» rematada con moldura es chair rail, el nombre que tiene
  en inglés ese elemento.
· «Silicona sanitaria» es silicone sealant, la que lleva fungicida.
"""

LOTE = {
    "Restauración de enchapado de piedra natural con reintegración de piezas faltantes y rejuntado. Incluye la reposición de las piezas y el rejuntado del conjunto. Medido por metro cuadrado restaurado.":
        "Restoration of natural stone cladding with the reinstatement of missing pieces and grouting. Includes replacing the pieces and grouting the whole. Measured per square meter restored.",

    "Colocación de papel tapiz sobre paramento interior previamente preparado, con pegamento mural. Incluye la comprobación de que el soporte está liso, seco y con absorción uniforme, condición sin la cual las juntas se abren o se marcan las irregularidades, la aplicación del fondo sellador, el replanteo de la primera plomada, el corte de los paños respetando el ajuste del dibujo, el encolado y colocación con eliminación de burbujas y arrugas, el recorte de los excesos en rodapié y cielo, y la limpieza de restos de pegamento. El papel lo elige el cliente y se presupuesta aparte. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Hanging of wallpaper on an interior substrate previously prepared, with wallpaper adhesive. Includes checking that the substrate is smooth, dry and of uniform absorption, a condition without which the joints open or the irregularities show through, applying the sealing primer, plumbing the first length, cutting the lengths respecting the pattern match, pasting and hanging with the removal of bubbles and creases, trimming the excess at the baseboard and the ceiling, and cleaning off the adhesive residue. The paper is selected by the client and priced separately. Measured by the area actually completed, deducting openings over 1 m².",

    "Acabado decorativo tipo estuco veneciano a la cal, aplicado en varias capas a espátula sobre paramento interior preparado, con bruñido final que produce el brillo característico. Es un trabajo de acabado puro en el que el resultado depende casi por completo de la mano del aplicador, por lo que conviene ejecutar una muestra previa aprobada por el cliente antes de acometer el paño. Incluye la preparación y sellado del soporte, la aplicación de las capas sucesivas con la espátula, el bruñido y el encerado final de protección. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Decorative lime based Venetian plaster finish, applied in several coats with a spatula over a prepared interior substrate, with a final burnishing that produces the characteristic sheen. It is a purely finishing trade where the result depends almost entirely on the hand of the applicator, so a sample approved by the client should be done before starting on the bay. Includes preparing and sealing the substrate, applying the successive coats with the spatula, the burnishing and the final protective waxing. Measured by the area actually completed, deducting openings over 1 m².",

    "Colocación de paneles decorativos de PVC, madera técnica, laminado o material similar sobre paramento interior, montados sobre rastrelado o adheridos según el sistema. Incluye el replanteo del despiece para centrar el paño y evitar piezas estrechas en los bordes, el montaje y nivelación del rastrelado cuando el sistema lo requiera, la colocación de los paneles con su sistema de encaje o adhesivo, el ajuste alrededor de mecanismos y huecos, y la colocación de los perfiles de remate perimetrales. El panel lo elige el cliente y se presupuesta aparte. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Fastening of decorative panels in PVC, engineered wood, laminate or similar material to an interior substrate, mounted on battens or adhered depending on the system. Includes field layout of the layout to center the bay and avoid narrow pieces at the edges, installing and leveling the furring strips where the system requires it, fastening the panels with their interlocking system or adhesive, trimming around fittings and openings, and fitting the perimeter trim profiles. The panel is selected by the client and priced separately. Measured by the area actually completed, deducting openings over 1 m².",

    "Forro de paramento interior con machihembrado de madera montado sobre rastrelado fijado a la pared, con cámara de ventilación posterior. La cámara y el tratamiento preservante son lo que evita que la madera se pudra por la humedad que pueda transmitir el muro, problema habitual cuando el machihembrado se clava directamente contra el paramento. Incluye el replanteo, el montaje y nivelación del rastrelado, la aplicación del preservante en todas las caras y testas, el montaje del machihembrado con encaje a presión, el remate perimetral con molduras y el lijado final. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Tongue and groove wood paneling mounted on furring strips fastened to the wall, with a ventilation cavity behind. The cavity and the preservative treatment are what stop the wood rotting from the damp the wall may transmit, the usual problem when tongue and groove is nailed straight against the substrate. Includes field layout, installing and leveling the furring strips, applying the preservative to every face and to the end grain, fastening the tongue and groove with a driven fit, the perimeter trim with moldings and the final sanding. Measured by the area actually completed, deducting openings over 1 m².",

    "Revestimiento continuo de microcemento en paramento vertical, aplicado en capas sucesivas con malla de refuerzo, con acabado sellado. Ofrece una superficie continua sin juntas, muy demandada en baños y espacios contemporáneos, pero es extremadamente sensible a la calidad del soporte: cualquier fisura o movimiento del paramento se refleja en el acabado. Incluye la comprobación y estabilización del soporte, la imprimación, la aplicación de la capa base con malla, las capas de acabado con la textura elegida, el lijado entre capas y la aplicación de las manos de sellador protector. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Continuous microcement covering on a vertical substrate, applied in successive coats with reinforcing mesh, with a sealed finish. It offers a continuous joint free surface, much in demand in bathrooms and contemporary spaces, but it is extremely sensitive to the quality of the substrate: any crack or movement in the substrate shows through in the finish. Includes checking and stabilizing the substrate, priming, applying the base coat with the mesh, the finishing coats with the chosen texture, sanding between coats and applying the coats of protective sealer. Measured by the area actually completed, deducting openings over 1 m².",

    "Revestimiento de paredes de baño o área húmeda con paneles de PVC o composite machihembrados, con sus perfiles de remate y sellado. Es la alternativa rápida y económica al enchapado cuando no se quiere picar ni esperar fraguados, y se instala sobre el revestimiento existente si está firme, lo que evita por completo la demolición. Incluye la comprobación del soporte, el montaje de los perfiles perimetrales, la colocación de los paneles con encaje a presión y adhesivo, los cortes alrededor de grifería y accesorios y el sellado con silicona sanitaria de todos los encuentros. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Covering of bathroom or wet area walls with interlocking PVC or sandwich panels, with their trim profiles and sealing. It is the quick and economical alternative to tiling when there is no wish to hack off or to wait for the mortar to set, and it is installed over the existing covering if it is sound, which avoids demolition altogether. Includes checking the substrate, fitting the perimeter profiles, fastening the panels with a driven fit and adhesive, the cuts around the faucets and accessories, and sealing every junction with silicone sealant. Measured by the area actually completed, deducting openings over 1 m².",

    "Revestimiento de paramento con tela o textil tensado o adherido, con sus remates. Incluye la preparación del soporte, la colocación del textil y el remate de bordes. Medido por metro cuadrado revestido.":
        "Covering of a substrate with stretched or adhered fabric or textile, with its trim. Includes preparing the substrate, fastening the textile and finishing the edges. Measured per square meter covered.",

    "Revestimiento de paramento con espejo, fijado con adhesivo o soportes. Incluye la preparación del soporte, la colocación del espejo y el remate. Medido por metro cuadrado revestido.":
        "Covering of a substrate with a mirror, fastened with adhesive or brackets. Includes preparing the substrate, fastening the mirror and the finishing. Measured per square meter covered.",

    "Friso decorativo de media pared con moldura o perfil, como elemento de remate entre acabados. Incluye la fijación del perfil y el remate de la unión. Medido por metro lineal de friso.":
        "Decorative chair rail frieze with a molding or profile, as a transition element between finishes. Includes fastening the profile and finishing the joint. Measured per meter of frieze.",

    "Aplicación de estuco a la cal decorativo en paramento interior, con acabado artesanal. Incluye la preparación del soporte y la aplicación del estuco. Medido por metro cuadrado estucado.":
        "Application of decorative lime plaster to an interior substrate, with a hand crafted finish. Includes preparing the substrate and applying the plaster. Measured per square meter plastered.",

    "Revestimiento de paramento con vidrio decorativo lacado o de color, con fijación mecánica. Incluye la preparación del soporte, la fijación del vidrio y el remate. Medido por metro cuadrado revestido.":
        "Covering of a substrate with decorative lacquered or colored glass, with mechanical fastening. Includes preparing the substrate, fastening the glass and the finishing. Measured per square meter covered.",
}
