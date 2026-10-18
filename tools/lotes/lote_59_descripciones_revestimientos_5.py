# -*- coding: utf-8 -*-
"""Descripciones — Revestimientos y acabados (5 de n): enchapados cerámicos.

El bloque de alicatados, que es donde el catálogo se pone más técnico y
donde el inglés del oficio tiene vocabulario propio que no se puede
improvisar.

Vocabulario aplicado:

· «Enchapado» es tiling cuando es cerámico. Las designaciones C2 TE y
  CG2 son las de la norma europea de adhesivos y morteros de juntas y
  se dejan tal cual, porque son las que piden las fichas técnicas en
  cualquier mercado.
· «Doble encolado» es back buttering: extender adhesivo también en el
  dorso de la pieza, que en gran formato es obligatorio.
· «Llana dentada» es notched trowel y «crucetas» son spacers.
· «Junta de dilatación» en un alicatado es movement joint, que no es
  lo mismo que expansion joint de estructura.
· «Descolgar» de la pieza en vertical es slide down, y por eso se usan
  sistemas de nivelación: leveling systems.
· «Despiece» es layout y «hilada» es course.
· «Salpicadero» de cocina es backsplash en inglés americano; el
  británico dice splashback y lo pone la variante.
· «Rejuntado» es grouting y el «mortero de juntas» es grout.
· «Cenefa» es border y «listelo» es listello, que en inglés se usa tal
  cual, como se usa «zócalo» en español.
· «Desportillado» es chipping, y el perfil que lo evita es trim.
· «Mosaico vítreo en malla» es glass mosaic on a mesh backing.
"""

LOTE = {
    "Friso de yeso en techo interior, con maestras y acabado fino. Incluye la aplicación de la pasta de yeso y el afinado. Medido por metro cuadrado frisado.":
        "Gypsum plaster on an interior ceiling, with screeds and a fine finish. Includes applying the gypsum compound and the finishing. Measured per square meter plastered.",

    "Enlucido de yeso con acabado espatulado fino, para paramentos que requieren máxima lisura. Incluye la aplicación de la pasta y el espatulado. Medido por metro cuadrado enlucido.":
        "Gypsum skim coat with a fine troweled finish, for substrates requiring maximum smoothness. Includes applying the compound and the troweling. Measured per square meter skim coated.",

    "Reparación de juntas de placas de yeso en techo, con pasta y cinta. Incluye el tratamiento de las juntas fisuradas y el lijado. Medido por metro cuadrado reparado.":
        "Repair of the joints between drywall on a ceiling, with compound and tape. Includes treating the cracked joints and sanding. Measured per square meter repaired.",

    "Enchapado de paramento interior en baños, cocinas y áreas húmedas con pieza cerámica o de porcelanato rectificado, sobre soporte previamente frisado y regularizado. Ejecución en capa fina con adhesivo cementoso mejorado C2 TE de deslizamiento reducido aplicado con llana dentada, nivelación mediante crucetas y cuñas, y rejuntado con mortero CG2. Incluye replanteo de hiladas para evitar piezas cortadas en zonas vistas, cortes y taladros para el paso de instalaciones y mecanismos, resolución de encuentros y esquinas, y limpieza final. La pieza la elige el cliente y se presupuesta aparte. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Tiling of an interior substrate in bathrooms, kitchens and wet areas with ceramic or rectified porcelain tile, over a substrate previously plastered and made level. Laid in a thin bed with an improved cementitious adhesive C2 TE with reduced slip applied with a notched trowel, leveled with spacers and wedges, and grouted with a CG2 mortar. Includes setting out the courses to avoid cut tiles in visible areas, cuts and holes for the passage of services and fittings, resolving the junctions and corners, and the final cleaning. The tile is selected by the client and priced separately. Measured by the area actually completed, deducting openings over 1 m².",

    "Colocación en pared de pieza de porcelanato rectificado de gran formato, tipo 60x120 cm o superior, en capa fina con adhesivo cementoso mejorado y doble encolado. En vertical el gran formato exige un soporte perfectamente plano y el empleo de sistemas de nivelación y de apoyo provisional que sostengan la pieza mientras el adhesivo agarra, porque su peso tiende a hacerla descolgar. Incluye la comprobación y regularización previa de la planitud, el replanteo del despiece, el doble encolado, la nivelación con cuñas, los cortes con cortadora de disco refrigerada, el rejuntado y la limpieza final. La pieza la elige el cliente y se presupuesta aparte. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Fixing of large format rectified porcelain tile to a wall, 60x120 cm or larger, in a thin bed with an improved cementitious adhesive and back buttering. On a vertical surface, large format demands a perfectly flat substrate and the use of leveling systems and temporary supports to hold the tile while the adhesive grabs, because its weight tends to make it slide down. Includes checking and correcting the flatness beforehand, setting out the layout, back buttering, leveling with wedges, cutting with a water cooled disc cutter, grouting and the final cleaning. The tile is selected by the client and priced separately. Measured by the area actually completed, deducting openings over 1 m².",

    "Colocación de enchapado cerámico o de porcelanato en fachada o paramento exterior, en capa fina con adhesivo cementoso de altas prestaciones tipo C2 con deslizamiento reducido, con juntas de dilatación en paños y encuentros. En exterior el revestimiento sufre dilataciones térmicas y humedad, de modo que el adhesivo, la junta ancha y las juntas de dilatación dejan de ser opcionales: son lo que impide el desprendimiento de piezas. Incluye el trabajo desde andamio, la comprobación del soporte, el replanteo, el doble encolado, la ejecución de las juntas de dilatación, el rejuntado con mortero para exterior y la limpieza. La pieza la elige el cliente y se presupuesta aparte. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Fixing of ceramic or porcelain tiling on a facade or exterior substrate, in a thin bed with a high performance cementitious adhesive type C2 with reduced slip, with movement joints in the bays and at the junctions. Outdoors the covering suffers thermal movement and moisture, so the adhesive, the wide joint and the movement joints stop being optional: they are what prevents the tiles from coming away. Includes working from scaffolding, checking the substrate, setting out, back buttering, forming the movement joints, grouting with an exterior mortar and cleaning. The tile is selected by the client and priced separately. Measured by the area actually completed, deducting openings over 1 m².",

    "Colocación de cenefa, listelo o pieza decorativa corrida dentro del enchapado cerámico, recibida con adhesivo y rejuntada a juego. Incluye el replanteo de la línea que debe coordinarse con el despiece general para que la cenefa coincida con la junta de las piezas y no obligue a cortes forzados, la colocación pieza a pieza con nivelación, los cortes de ajuste en esquinas y encuentros, el rejuntado y la limpieza. La pieza la elige el cliente y se presupuesta aparte. Medido en longitud realmente colocada.":
        "Fixing of a border, listello or continuous decorative tile within the ceramic tiling, bedded in adhesive and grouted to match. Includes setting out the line, which has to be coordinated with the general layout so that the border lines up with the joint between tiles and does not force awkward cuts, fixing tile by tile with leveling, the adjusting cuts at corners and junctions, grouting and cleaning. The tile is selected by the client and priced separately. Measured by the length actually installed.",

    "Suministro y colocación de perfil de aluminio o PVC de remate, esquinero o transición en el enchapado, recibido con el propio adhesivo bajo el borde de la pieza. Protege la arista del enchapado, que es donde se producen los desportillados, y resuelve el encuentro entre materiales distintos con una línea limpia. Incluye el replanteo, el corte a medida y a inglete en los encuentros, la colocación embebida en el adhesivo antes de asentar la pieza contigua y la limpieza. Medido en longitud realmente colocada.":
        "Supply and installation of an aluminum or PVC trim, angle or transition profile in the tiling, bedded in the adhesive itself under the edge of the tile. It protects the arris of the tiling, which is where chipping occurs, and resolves the junction between different materials with a clean line. Includes setting out, cutting to length and mitring at the junctions, embedding it in the adhesive before bedding the adjacent tile, and cleaning. Measured by the length actually installed.",

    "Enchapado cerámico o de porcelanato en la zona de ducha, colocado sobre la impermeabilización previa con adhesivo de altas prestaciones y rejuntado con mortero apto para inmersión frecuente. El punto de fallo no es la pieza sino los encuentros: el sellado elástico del rincón pared-pared y pared-piso debe ser flexible y no de mortero rígido, porque ahí es donde el movimiento abre la junta y entra el agua. Incluye la comprobación de la impermeabilización, el replanteo de hiladas partiendo del punto más visible, el doble encolado, los cortes alrededor de grifería y jabonera, el rejuntado y el sellado elástico de todos los rincones. La pieza la elige el cliente y se presupuesta aparte. Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Ceramic or porcelain tiling in the shower area, laid over the previous waterproofing with a high performance adhesive and grouted with a mortar suitable for frequent immersion. The point of failure is not the tile but the junctions: the seal at the wall to wall and wall to floor corners must be flexible and not rigid mortar, because that is where movement opens the joint and lets the water in. Includes checking the waterproofing, setting out the courses starting from the most visible point, back buttering, the cuts around the taps and the soap dish, grouting and the flexible sealing of every corner. The tile is selected by the client and priced separately. Measured by the area actually completed, deducting openings over 1 m².",

    "Colocación de rodapié cerámico corrido en la base del paramento, en áreas de servicio, pasillos y zonas de tránsito, para proteger el friso de golpes y de la humedad de la limpieza. Incluye el replanteo de la altura, el corte de las piezas, el encolado, la nivelación, el rejuntado y el sellado de la junta inferior con el piso. La pieza la elige el cliente y se presupuesta aparte. Medido en longitud realmente colocada.":
        "Fixing of a continuous ceramic baseboard at the foot of the substrate, in service areas, corridors and circulation areas, to protect the plaster from knocks and from the moisture of cleaning. Includes setting out the height, cutting the tiles, the adhesive, leveling, grouting and sealing the bottom joint with the floor. The tile is selected by the client and priced separately. Measured by the length actually installed.",

    "Enchapado del salpicadero de cocina entre mesón y muebles altos, con pieza cerámica o porcelanato. Incluye la preparación, la colocación y el rejuntado de la franja. Medido por metro cuadrado enchapado.":
        "Tiling of the kitchen backsplash between the countertop and the wall cabinets, with ceramic or porcelain tile. Includes the preparation, laying and grouting of the band. Measured per square meter tiled.",

    "Enchapado de nicho o repisa de ducha con pieza cerámica o porcelanato, con pendiente de evacuación. Incluye la preparación, la colocación con pendiente y el rejuntado. Medido por metro cuadrado enchapado.":
        "Tiling of a shower niche or shelf with ceramic or porcelain tile, laid to a fall. Includes the preparation, laying to a fall and grouting. Measured per square meter tiled.",

    "Enchapado de paramento con mosaico vítreo en malla, en capa fina. Incluye la preparación del soporte, la colocación del mosaico y el rejuntado. Medido por metro cuadrado enchapado.":
        "Tiling of a substrate with glass mosaic on a mesh backing, in a thin bed. Includes preparing the substrate, fixing the mosaic and grouting. Measured per square meter tiled.",
}
