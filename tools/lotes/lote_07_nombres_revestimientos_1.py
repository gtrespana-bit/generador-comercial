# -*- coding: utf-8 -*-
"""Nombres de partida — Revestimientos y acabados (1 de 3).

Criterios de este lote:
  · «Paramento» es substrate cuando se prepara y face cuando se describe:
    «Preparación de paramento» es substrate preparation.
  · «Friso» y «repello» son los venezolanismos de los revestimientos de
    mortero. El friso es la capa de acabado (plaster en Estados Unidos,
    stucco en Reino Unido) y el repello es la capa base (base coat).
  · «Enchapado» es tiling: es alicatado, no chapeado ni revestimiento.
  · «Capa fina» es thin-set y «capa gruesa» es thick-bed, que es como se
    llaman los dos sistemas de colocación en inglés de obra.
  · «Granito» vaciado en sitio es terrazzo, no granite.
  · «Laja» es flagstone.
"""

LOTE = {
# ── Preparación de soportes ───────────────────────────────────────────────
"Preparación de paramento interior para pintura: resane, alisado y fondo.":
    "Preparation of interior surfaces for painting: patching, smoothing and undercoat.",
"Preparación de paramento exterior para pintura.":
    "Preparation of exterior surfaces for painting.",
"Sellado de fisuras en paramento previo a pintura.":
    "Sealing of cracks in a surface before painting.",
"Regularización de paramento con mortero de nivelación.":
    "Leveling of a surface with leveling mortar.",
"Picado y limpieza de paramento deteriorado.":
    "Chipping out and cleaning a deteriorated surface.",
"Imprimación selladora de paramento poroso.":
    "Sealing primer on a porous surface.",
"Reparación de grietas con malla de refuerzo.":
    "Repair of cracks with reinforcement mesh.",
"Nivelación puntual de paramento con pasta.":
    "Localized leveling of a surface with compound.",
"Tratamiento antihumedad de paramento previo a pintura.":
    "Damp-proofing treatment of a surface before painting.",
"Puente de adherencia sobre soporte de concreto.":
    "Bonding agent on a concrete substrate.",
"Preparación de soporte de enchapado con mortero.":
    "Preparation of the mortar substrate for tiling.",
"Preparación de piso existente para nuevo revestimiento.":
    "Preparation of an existing floor for a new finish.",
"Preparación de soporte de madera para pintura.":
    "Preparation of a wood substrate for painting.",
"Resane de paramento interior con masilla.":
    "Patching of an interior surface with filler.",
"Reparación de paramento de concreto con mortero.":
    "Repair of a concrete surface with mortar.",
"Preparación de soporte de yeso con sellador.":
    "Preparation of a plaster substrate with sealer.",
"Limpieza de paramento con agua a presión.":
    "Pressure washing of a surface.",
"Rasqueteado de friso existente deteriorado.":
    "Scraping off deteriorated existing plaster.",
"Reparación de esquina con cantonera.":
    "Repair of a corner with a corner bead.",
"Saneado de paramento con eflorescencias.":
    "Removal of efflorescence from a surface.",
"Preparación de soporte para microcemento.":
    "Preparation of the substrate for microcement.",
"Preparación de soporte para papel tapiz.":
    "Preparation of the substrate for wallpaper.",
"Regularización de techo previo a cielo raso.":
    "Leveling of the soffit before the suspended ceiling.",
"Eliminación de restos de adhesivo en paramento.":
    "Removal of adhesive residue from a surface.",
"Reparación de junta de dilatación en paramento.":
    "Repair of an expansion joint in a surface.",
"Tratamiento de óxido en paramento de concreto.":
    "Rust treatment on a concrete surface.",
"Nivelación de paramento con nivel láser.":
    "Leveling of a surface with a laser level.",
"Preparación de soporte de metal para pintura.":
    "Preparation of a metal substrate for painting.",

# ── Revoques y frisos ─────────────────────────────────────────────────────
"Friso de mortero maestreado sobre paramento interior, 1,5 cm de espesor.":
    "Screeded cement plaster on interior surfaces, 1.5 cm thick.",
"Friso de mortero con hidrófugo en paramento exterior.":
    "Water-repellent cement plaster on exterior surfaces.",
"Friso rústico texturado en fachada.":
    "Textured rustic stucco on the facade.",
"Mortero impermeabilizante en área húmeda, base para enchapado.":
    "Waterproofing mortar in wet areas, as a base for tiling.",
"Regularización y repello de paramento existente.":
    "Leveling and base coat on an existing surface.",
"Friso de mortero proyectado mecánicamente.":
    "Machine-applied cement plaster.",
"Media caña sanitaria en encuentro de pared y piso.":
    "Sanitary cove at the wall and floor junction.",
"Repello y afinado de mocheta o arista de vano.":
    "Base coat and finishing of a reveal or opening arris.",
"Friso de mortero sobre bloque de concreto.":
    "Cement plaster on a concrete block wall.",
"Friso de mortero de cal tradicional.":
    "Traditional lime plaster.",
"Repello de paramento exterior con acabado liso.":
    "Base coat on exterior surfaces with a smooth finish.",
"Friso con malla de refuerzo en fachada.":
    "Cement plaster with reinforcement mesh on the facade.",
"Friso de mortero en techo.":
    "Cement plaster on a soffit.",
"Friso de nivelación en columnas y vigas.":
    "Leveling plaster on columns and beams.",
"Friso impermeabilizante en muro de contención.":
    "Waterproofing stucco on a retaining wall.",
"Friso de mortero coloreado en paramento.":
    "Colored cement plaster on a surface.",
"Friso de mortero en zonas estrechas y mochetas.":
    "Cement plaster in narrow areas and reveals.",
"Friso bruñido de mortero.":
    "Burnished cement plaster.",
"Friso de mortero sobre muro de piedra.":
    "Cement plaster on a stone wall.",
"Friso de pasta de yeso en paramento interior.":
    "Gypsum plaster on interior surfaces.",
"Estucado fino de pasta sobre friso.":
    "Fine skim coat of compound over plaster.",
"Alisado de paramento con pasta de nivelación.":
    "Smoothing of a surface with leveling compound.",
"Moldura decorativa corrida de yeso.":
    "Continuous decorative plaster molding.",
"Reparación puntual de friso de yeso.":
    "Localized repair of gypsum plaster.",
"Friso de yeso proyectado.":
    "Machine-applied gypsum plaster.",
"Enlucido de yeso sobre bloque.":
    "Gypsum skim coat on concrete masonry.",
"Reparación de friso de yeso en zona amplia.":
    "Repair of gypsum plaster over a large area.",
"Friso de yeso con fibra de refuerzo.":
    "Gypsum plaster with reinforcing fiber.",
"Enlucido de yeso sobre muro de ladrillo.":
    "Gypsum skim coat on a brick wall.",
"Friso de yeso en techo.":
    "Gypsum plaster on a soffit.",
"Enlucido de yeso con acabado espatulado.":
    "Gypsum skim coat with a troweled finish.",
"Reparación de junta de yeso en techo.":
    "Repair of a drywall joint in a ceiling.",

# ── Enchapados cerámicos y pétreos ────────────────────────────────────────
"Enchapado de paramento interior con pieza cerámica o porcelanato, en capa fina.":
    "Interior wall tiling with ceramic or porcelain tile, thin-set.",
"Enchapado de porcelanato de gran formato en pared.":
    "Large-format porcelain wall tiling.",
"Enchapado cerámico en fachada o paramento exterior.":
    "Ceramic tiling on a facade or exterior surface.",
"Cenefa o listelo decorativo en enchapado.":
    "Decorative border or listello in tiling.",
"Perfil de remate, esquinero o transición en enchapado.":
    "Finishing, corner or transition profile in tiling.",
"Enchapado de zona de ducha sobre impermeabilización.":
    "Tiling of a shower area over the waterproofing.",
"Rodapié cerámico de pared.":
    "Ceramic baseboard.",
"Enchapado de pared con junta mínima.":
    "Wall tiling with a minimal joint.",
"Enchapado en espiga o espina de pescado.":
    "Herringbone tiling.",
"Enchapado con pieza de formato largo tipo metro.":
    "Tiling with a long brick-format tile.",
"Enchapado de salpicadero de cocina entre muebles, en capa fina.":
    "Kitchen backsplash tiling between units, thin-set.",
"Enchapado de nicho o repisa de ducha.":
    "Tiling of a shower niche or shelf.",
"Enchapado de frente de bañera con pieza cerámica, en capa fina.":
    "Tiling of a bathtub surround with ceramic tile, thin-set.",
"Enchapado de mosaico vítreo en pared.":
    "Glass mosaic wall tiling.",
"Enchapado con junta coloreada decorativa.":
    "Tiling with a decorative colored grout.",
"Enchapado de columna con pieza cerámica, en capa fina.":
    "Column tiling with ceramic tile, thin-set.",
"Enchapado de gres porcelánico técnico.":
    "Technical porcelain stoneware tiling.",
"Enchapado de piscina con pieza cerámica.":
    "Swimming pool tiling with ceramic tile.",
"Enchapado de mármol o granito en pared, colocación en capa fina.":
    "Marble or granite wall cladding, thin-set.",
"Enchapado de laja o piedra natural irregular.":
    "Flagstone or irregular natural stone cladding.",
"Enchapado de piedra natural con anclaje mecánico.":
    "Natural stone cladding with mechanical anchors.",
"Zócalo de piedra natural.":
    "Natural stone base.",
"Pulido y abrillantado de enchapado de piedra natural.":
    "Polishing and buffing of natural stone cladding.",
"Enchapado de mármol pulido en pared.":
    "Polished marble wall cladding.",
"Enchapado de piedra con junta seca.":
    "Stone cladding with a dry joint.",
"Enchapado de piedra con anclaje mecánico en fachada.":
    "Stone cladding with mechanical anchors on a facade.",
"Pulido de enchapado de mármol en pared.":
    "Polishing of marble wall cladding.",
"Enchapado de piedra con junta ancha de mortero.":
    "Stone cladding with a wide mortar joint.",
"Enchapado de piedra en fachada ventilada.":
    "Stone cladding on a ventilated facade.",
"Enchapado de mármol en zócalo o mocheta.":
    "Marble cladding on a base or reveal.",
"Restauración de enchapado de piedra con reintegración.":
    "Restoration of stone cladding with replacement of missing pieces.",

# ── Otros revestimientos ──────────────────────────────────────────────────
"Revestimiento de paramento con papel tapiz.":
    "Wall surfacing with wallpaper.",
"Estuco veneciano o acabado decorativo mineral.":
    "Venetian plaster or decorative mineral finish.",
"Revestimiento de paramento con paneles decorativos.":
    "Wall surfacing with decorative panels.",
"Forro de pared con machihembrado de madera.":
    "Wall lining with tongued and grooved boarding.",
"Revestimiento continuo de microcemento en paramento vertical.":
    "Seamless microcement coating on a vertical surface.",
"Revestimiento de pared de baño con paneles de PVC.":
    "Bathroom wall cladding with PVC panels.",
"Revestimiento textil de pared.":
    "Textile wall covering.",
"Revestimiento de corcho en pared.":
    "Cork wall covering.",
"Revestimiento de piedra decorativa ligera.":
    "Lightweight decorative stone cladding.",
"Panel 3D decorativo en pared.":
    "Decorative 3D wall panel.",
"Revestimiento de lámina acrílica o policarbonato decorativo.":
    "Decorative acrylic or polycarbonate sheet cladding.",
"Aplacado de metal decorativo en pared.":
    "Decorative metal paneling on a wall.",
"Revestimiento de espejo en pared.":
    "Mirror wall cladding.",
"Friso decorativo de media pared.":
    "Decorative dado-height wall finish.",
"Revestimiento de ladrillo visto decorativo.":
    "Decorative exposed brick cladding.",
"Revestimiento de madera con acabado lacado.":
    "Wood cladding with a lacquered finish.",
"Estuco a la cal decorativo.":
    "Decorative lime plaster.",
"Revestimiento de fibra natural tejida.":
    "Woven natural fiber wall covering.",
"Revestimiento de vidrio decorativo lacado.":
    "Decorative lacquered glass cladding.",
"Revestimiento de bambú.":
    "Bamboo cladding.",
"Revestimiento de tablero OSB decorativo.":
    "Decorative OSB panel cladding.",
"Mural decorativo pintado a mano.":
    "Hand-painted decorative mural.",
"Revestimiento de gres porcelánico imitación madera.":
    "Wood-effect porcelain stoneware cladding.",
"Revestimiento de metal expandido decorativo.":
    "Decorative expanded metal cladding.",
"Revestimiento de plancha de melamina.":
    "Melamine panel cladding.",
"Microcemento en techo decorativo.":
    "Decorative microcement on a soffit.",
"Revestimiento de placas de cemento decorativo.":
    "Decorative cement board cladding.",
"Revestimiento de panel perforado acústico decorativo.":
    "Decorative acoustic perforated panel cladding.",

# ── Nivelación y pisos ────────────────────────────────────────────────────
"Nivelación con mortero autonivelante de 5 mm de espesor medio.":
    "Leveling with self-leveling mortar, 5 mm average thickness.",
"Afirmado de mortero de nivelación, 4 cm de espesor.":
    "4 cm leveling bed of mortar.",
"Afirmado de concreto sobre terreno, 8 cm de espesor.":
    "8 cm concrete bed on the ground.",
"Nivelación con mortero seco compactado.":
    "Leveling with compacted semi-dry mortar.",
"Preparación y puente de adherencia sobre losa existente.":
    "Preparation and bonding agent on an existing slab.",
"Reparación y parcheo puntual de piso existente.":
    "Localized repair and patching of an existing floor.",
"Afirmado de concreto aligerado.":
    "Lightweight concrete bed.",
"Relleno de nivelación con mortero seco.":
    "Leveling fill with semi-dry mortar.",
"Piso cerámico o porcelanato de formato estándar, en capa fina.":
    "Ceramic or porcelain tile flooring, standard format, thin-set.",
"Piso de porcelanato de gran formato, en capa fina.":
    "Large-format porcelain tile flooring, thin-set.",
"Piso cerámico en área húmeda con pendiente a desagüe.":
    "Ceramic tile flooring in a wet area, laid to fall to the drain.",
"Piso cerámico en terraza o área exterior.":
    "Ceramic tile flooring on a terrace or outdoor area.",
"Piso cerámico colocado en capa gruesa sobre mortero.":
    "Ceramic tile flooring laid thick-bed on mortar.",
"Piso de baldosa hidráulica o mosaico de cemento.":
    "Cement or encaustic tile flooring.",
"Piso cerámico con guarda o cenefa.":
    "Ceramic tile flooring with a border.",
"Piso de porcelanato rectificado en capa fina.":
    "Rectified porcelain tile flooring, thin-set.",
"Piso de mármol o granito en capa fina.":
    "Marble or granite flooring, thin-set.",
"Piso de granito vaciado en sitio.":
    "Cast-in-place terrazzo flooring.",
"Piso de laja o piedra natural irregular.":
    "Flagstone or irregular natural stone flooring.",
"Piso de baldosa de granito prefabricado.":
    "Precast terrazzo tile flooring.",
"Pulido y abrillantado de piso de piedra existente.":
    "Polishing and buffing of an existing stone floor.",
"Piso de mármol en placa grande.":
    "Large-format marble slab flooring.",
"Piso de piedra natural a junta mínima.":
    "Natural stone flooring with a minimal joint.",
"Piso laminado flotante con manta acústica.":
    "Floating laminate flooring with acoustic underlay.",
"Piso de madera maciza clavada sobre rastreles.":
    "Solid wood flooring nailed to battens.",
"Piso de parquet encolado sobre afirmado.":
    "Parquet flooring bonded to the leveling bed.",
}
