# -*- coding: utf-8 -*-
"""Nombres de partida — Revestimientos y acabados (3 de 3).

Cierra el capítulo: pintura de exterior y de carpintería, barnices,
recubrimientos de resina y restauración.

Criterios de este lote:
  · «Esmalte» sobre carpintería es enamel paint cuando es sintético y
    water-based enamel cuando es al agua: las dos cosas se piden distinto.
  · «Carpintería» se resuelve como woodwork y metalwork, que es como se
    nombra en inglés lo que se pinta, y no como «carpentry», que el
    estadounidense no usa.
  · «Hidrolavado» e «hidrofugación» son la misma familia de agua a presión
    y repelente: pressure washing y water-repellent treatment.
  · «Granito» vuelve a ser terrazzo cuando va vaciado en sitio.
"""

LOTE = {
# ── Pintura de interior ───────────────────────────────────────────────────
"Sellado antihumedad y pintura interior.":
    "Damp-proof sealing and interior painting.",
"Pintura de paramento de cocina con esmalte lavable.":
    "Washable enamel paint on kitchen surfaces.",
"Pintura ignífuga intumescente interior.":
    "Intumescent fire-resistant paint indoors.",
"Pintura acrílica lavable en cocina.":
    "Washable acrylic paint in a kitchen.",
"Pintura de señalización de seguridad interior.":
    "Interior safety marking paint.",
"Pintura de estructura metálica interior.":
    "Painting of an interior steel structure.",
"Pintura de pared con plantilla decorativa.":
    "Stencilled wall painting.",
"Pintura de techo con rodillo extensible.":
    "Ceiling painting with an extension roller.",
"Pintura satinada de locales de alta humedad.":
    "Satin paint in high-humidity rooms.",
"Pintura de paramento con acabado perlado.":
    "Paint on a surface with a pearl finish.",
"Repintado integral de vivienda con desalojo.":
    "Complete repainting of a dwelling, with the occupants moved out.",
"Pintura de guarda o friso decorativo interior.":
    "Painting of a decorative border or dado indoors.",
"Pintura de sótano o garaje interior.":
    "Painting of a basement or interior garage.",

# ── Pintura de exterior y fachada ─────────────────────────────────────────
"Pintura de caucho para exterior, dos manos.":
    "Exterior latex paint, two coats.",
"Pintura elastomérica impermeabilizante de fachada.":
    "Elastomeric waterproof coating on a facade.",
"Pintura sobre concreto visto o superficie mineral.":
    "Paint on exposed concrete or a mineral surface.",
"Pintura de caucho exterior sobre friso nuevo, tres manos.":
    "Exterior latex paint on new stucco, three coats.",
"Repintado de fachada sobre pintura existente.":
    "Repainting of a facade over existing paint.",
"Pintura de fachada con acabado satinado, dos manos.":
    "Facade paint with a satin finish, two coats.",
"Pintura de fachada con acabado texturado.":
    "Facade paint with a textured finish.",
"Pintura de muro de cerramiento o pared medianera.":
    "Painting of a boundary wall or party wall.",
"Pintura de cornisa, alero y remates de fachada.":
    "Painting of the cornice, eaves and facade trims.",
"Pintura de fachada sobre concreto visto.":
    "Facade paint on exposed concrete.",
"Pintura de fachada con hidrofugante previo.":
    "Facade painting with a prior water-repellent treatment.",
"Pintura de reja, verja o elemento metálico exterior.":
    "Painting of an exterior grille, railing or metal element.",
"Pintura de fachada con puente de adherencia.":
    "Facade painting with a bonding agent.",
"Tratamiento de salitre y pintura de muro exterior.":
    "Treatment of salt efflorescence and painting of an exterior wall.",
"Pintura de fachada a dos colores.":
    "Two-color facade painting.",
"Pintura de zócalo exterior.":
    "Painting of an exterior base.",
"Pintura de cubierta o techo exterior.":
    "Painting of an exterior roof or deck.",
"Pintura de fachada con acabado mate.":
    "Facade paint with a matte finish.",
"Pintura de fachada con hidrolavado previo.":
    "Facade painting after pressure washing.",
"Hidrofugación con siloxano de fachada.":
    "Siloxane water-repellent treatment of a facade.",
"Protector anti-graffiti sobre fachada.":
    "Anti-graffiti protective coating on a facade.",
"Pintura de muro de contención exterior.":
    "Painting of an exterior retaining wall.",
"Pintura de fachada de bloque de concreto.":
    "Facade painting on a concrete block wall.",
"Pintura de portón o puerta metálica exterior.":
    "Painting of an exterior metal gate or door.",
"Pintura de fachada con esquema de mantenimiento.":
    "Facade painting under a maintenance program.",

# ── Esmaltes y barnices ───────────────────────────────────────────────────
"Esmalte sintético sobre carpintería metálica o de madera, dos manos.":
    "Synthetic enamel paint on metal or wood work, two coats.",
"Pintura sobre superficie galvanizada o de aluminio.":
    "Paint on a galvanized or aluminum surface.",
"Esmalte al agua sobre carpintería interior de madera.":
    "Water-based enamel on interior woodwork.",
"Pintura anticorrosiva sobre estructura metálica.":
    "Anti-corrosion paint on a steel structure.",
"Esmalte sobre carpintería metálica exterior.":
    "Enamel paint on exterior metalwork.",
"Pintura de tuberías y conducciones metálicas.":
    "Painting of metal pipes and ductwork.",
"Esmalte sintético sobre madera exterior.":
    "Synthetic enamel paint on exterior wood.",
"Pintura de puerta de madera con desmontaje de herrajes.":
    "Painting of a wood door with the hardware removed.",
"Pintura de mueble de cocina lacado.":
    "Painting of a lacquered kitchen unit.",
"Pintura de closet con esmalte.":
    "Enamel painting of a closet.",
"Pintura de persiana de madera.":
    "Painting of a lumber shutter.",
"Pintura de pasamanos metálico.":
    "Painting of a metal handrail.",
"Pintura de puerta metálica.":
    "Painting of a metal door.",
"Barniz protector sobre madera interior.":
    "Protective varnish on interior wood.",
"Barniz marino sobre madera exterior.":
    "Marine varnish on exterior wood.",
"Laca para carpintería interior de madera.":
    "Lacquer for interior woodwork.",
"Aplicación de preservante fungicida sobre madera estructural.":
    "Application of a fungicidal preservative to structural lumber.",
"Barnizado de barandas y pasamanos de madera.":
    "Varnishing of lumber guardrails and handrails.",
"Protección de madera exterior con lasur.":
    "Protection of exterior wood with a satin wood stain.",
"Aplicación de tinte para madera.":
    "Application of a wood stain.",
"Barnizado de puerta de madera.":
    "Varnishing of a wood door.",
"Protección de madera estructural con barniz.":
    "Protection of structural lumber with varnish.",
"Lasur para pérgola o madera exterior.":
    "Satin wood stain for a pergola or exterior wood.",
"Pintura ignífuga sobre madera.":
    "Fire-retardant paint on wood.",
"Barnizado de mueble de madera exterior.":
    "Varnishing of exterior wood furniture.",
"Laca para puertas de interior.":
    "Lacquer for interior doors.",

# ── Recubrimientos de resina ──────────────────────────────────────────────
"Pintura epóxica sobre piso o paramento.":
    "Epoxy paint on a floor or surface.",
"Acabado decorativo texturado.":
    "Decorative textured finish.",
"Recubrimiento de poliuretano sobre piso.":
    "Polyurethane coating on a floor.",
"Recubrimiento epóxico antideslizante para piso.":
    "Anti-slip epoxy coating for a floor.",
"Pintura epóxica sobre paramento vertical.":
    "Epoxy paint on a vertical surface.",
"Revestimiento de alta resistencia química para laboratorio.":
    "High chemical resistance coating for a laboratory.",
"Pintura de demarcación de pisos industriales.":
    "Line marking paint for industrial floors.",
"Microcemento en techo.":
    "Microcement on a soffit.",
"Membrana de poliurea sobre cubierta.":
    "Polyurea membrane on a roof deck.",
"Recubrimiento epóxico decorativo con escamas.":
    "Decorative flake epoxy coating.",
"Recubrimiento de cuarzo coloreado antideslizante.":
    "Anti-slip colored quartz coating.",
"Recubrimiento antiderrapante de rampa.":
    "Non-slip ramp coating.",
"Sellado de piso de concreto.":
    "Sealing of a concrete floor.",
"Recubrimiento de resina acrílica decorativa.":
    "Decorative acrylic resin coating.",
"Recubrimiento epóxico autodrenante de piso.":
    "Self-draining epoxy floor coating.",
"Recubrimiento de poliuretano cementoso.":
    "Cementitious polyurethane coating.",
"Recubrimiento epóxico en paramento de cocina industrial.":
    "Epoxy coating on the walls of a commercial kitchen.",
"Recubrimiento de resina en cámara frigorífica.":
    "Resin coating in a walk-in cooler.",
"Resalte sanitario de resina en encuentro piso-pared.":
    "Resin sanitary cove at the floor and wall junction.",
"Recubrimiento conductor antiestático de piso.":
    "Anti-static conductive floor coating.",
"Recubrimiento de fachada con mortero acrílico.":
    "Acrylic stucco coating on a facade.",
"Recubrimiento reflectivo de cubierta.":
    "Reflective roof coating.",
"Recubrimiento decorativo texturado de pared.":
    "Decorative textured wall coating.",

# ── Limpieza, protección y restauración ───────────────────────────────────
"Limpieza de fachada con hidrolavadora.":
    "Pressure washing of a facade.",
"Restauración y rejuntado de enchapado existente.":
    "Restoration and re-grouting of existing tiling.",
"Decapado de pintura en paramento.":
    "Paint stripping on a surface.",
"Limpieza química de paramento de piedra.":
    "Chemical cleaning of a stone surface.",
"Restauración de molduras de yeso.":
    "Restoration of plaster moldings.",
"Reintegración de juntas de mármol.":
    "Re-pointing of marble joints.",
"Tratamiento de madera carcomida.":
    "Treatment of lumber damaged by wood-boring insects.",
"Limpieza de paramento de ladrillo visto.":
    "Cleaning of an exposed brick surface.",
"Restauración de papel tapiz.":
    "Restoration of wallpaper.",
"Hidrofugación de fachada de piedra o ladrillo.":
    "Water-repellent treatment of a stone or brick facade.",
"Protección antimanchas de piedra natural.":
    "Stain protection for natural stone.",
"Sellado de fisuras en fachada.":
    "Sealing of cracks in a facade.",
"Tratamiento fungicida de paramento con moho.":
    "Fungicidal treatment of a surface affected by mold.",
"Hidrofugación de cubierta de teja.":
    "Water-repellent treatment of a tile roof.",
"Protección anti-graffiti de fachada pintada.":
    "Anti-graffiti protection for a painted facade.",
"Hidrofugación de paramento de concreto.":
    "Water-repellent treatment of a concrete surface.",
"Restauración de carpintería de madera con decapado y barnizado.":
    "Restoration of woodwork by stripping and varnishing.",
"Cristalizado y abrillantado de piso de piedra.":
    "Crystallization and buffing of a stone floor.",
"Reintegración y pulido de granito vaciado en sitio.":
    "Repair and polishing of cast-in-place terrazzo.",
"Restauración de carpintería de madera con masilla.":
    "Restoration of woodwork with filler.",
"Abrillantado de piso de mármol.":
    "Buffing of a marble floor.",
"Restauración de piso de madera.":
    "Restoration of a wood floor.",
"Limpieza y abrillantado de piso de granito.":
    "Cleaning and buffing of a terrazzo floor.",
"Restauración de enlucido con mortero de cal.":
    "Restoration of a plaster finish with lime mortar.",
}
