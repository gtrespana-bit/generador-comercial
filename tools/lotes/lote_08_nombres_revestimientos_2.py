# -*- coding: utf-8 -*-
"""Nombres de partida — Revestimientos y acabados (2 de 3).

Criterios de este lote:
  · «Cielo raso continuo» es continuous ceiling cuando va de placa de yeso
    (drywall en Reino Unido, drywall en Estados Unidos) y suspended
    ceiling cuando va en retícula desmontable: en inglés son dos oficios
    distintos y se nombran distinto.
  · «Trasdosado autoportante» es independent wall lining.
  · «Peldaño» es tread, «nariz de peldaño» es stair nosing, y «descansillo»
    o «rellano» es landing.
  · «Rodapié» es baseboard en Estados Unidos y baseboard en Reino Unido: lo
    ajusta después la capa de variantes.
  · «Pintura de caucho» es el venezolanismo de la pintura plástica: latex
    paint en Estados Unidos, latex paint en Reino Unido.
"""

LOTE = {
# ── Pisos: madera, vinílicos y continuos ──────────────────────────────────
"Lijado y barnizado de piso de madera.":
    "Sanding and varnishing of a wood floor.",
"Piso de deck de madera o madera técnica para exterior.":
    "Lumber or composite decking for outdoors.",
"Piso de parquet colocado en espiga.":
    "Herringbone parquet flooring.",
"Piso de bambú encolado.":
    "Glue-down bamboo flooring.",
"Piso vinílico en lámina.":
    "Sheet vinyl flooring.",
"Piso vinílico en baldosa o lama.":
    "Vinyl tile or plank flooring.",
"Piso de caucho o pavimento deportivo.":
    "Rubber or sports flooring.",
"Piso de alfombra o moqueta, encolado o tensado.":
    "Carpet flooring, glue-down or stretched in.",
"Piso de caucho o grama sintética para exterior.":
    "Rubber or artificial grass surfacing for outdoors.",
"Piso vinílico de lujo tipo SPC.":
    "Luxury SPC vinyl flooring.",
"Piso de linóleo encolado.":
    "Glue-down linoleum flooring.",
"Piso de concreto alisado mecánicamente.":
    "Power-troweled concrete floor.",
"Piso de concreto estampado.":
    "Stamped concrete floor.",
"Piso continuo de microcemento.":
    "Seamless microcement floor.",
"Piso epóxico autonivelante.":
    "Self-leveling epoxy flooring.",
"Endurecedor superficial y sellado de piso de concreto.":
    "Surface hardener and sealing of a concrete floor.",
"Piso de cemento pulido llaneteado a mano.":
    "Hand-troweled polished cement floor.",
"Piso de gravilla lavada o chino lavado.":
    "Exposed aggregate flooring.",
"Piso de terrazo pulido en obra.":
    "In-situ polished terrazzo flooring.",
"Piso de concreto coloreado.":
    "Colored concrete floor.",

# ── Rodapiés y remates de piso ────────────────────────────────────────────
"Colocación de rodapié cerámico o de porcelanato.":
    "Ceramic or porcelain baseboard installation.",
"Rodapié de madera o MDF.":
    "Wood or MDF baseboard.",
"Rodapié de mortero con media caña sanitaria.":
    "Mortar baseboard with a sanitary cove.",
"Perfil de transición entre pisos.":
    "Transition strip between floors.",
"Junta de dilatación en piso.":
    "Expansion joint in a floor.",
"Nivelación y remate de umbral entre ambientes.":
    "Leveling and finishing of a threshold between rooms.",
"Rodapié de PVC.":
    "PVC baseboard.",
"Rodapié de piedra natural.":
    "Natural stone baseboard.",
"Rodapié de aluminio.":
    "Aluminum baseboard.",
"Rodapié de PVC con canaleta de instalaciones.":
    "PVC baseboard with a services raceway.",
"Rodapié de madera lacada.":
    "Lacquered wood baseboard.",
"Rodapié de porcelanato rectificado.":
    "Rectified porcelain baseboard.",

# ── Escaleras ─────────────────────────────────────────────────────────────
"Revestimiento de escalera con cerámica o porcelanato.":
    "Stair tiling with ceramic or porcelain tile.",
"Revestimiento de escalera con piedra natural.":
    "Stair cladding with natural stone.",
"Peldaño de madera sobre escalera de concreto.":
    "Wood tread on a concrete stair.",
"Cinta o perfil antideslizante en nariz de peldaño.":
    "Anti-slip strip or profile on a stair nosing.",
"Zócalo escalonado de escalera.":
    "Stepped base to a stair.",
"Peldaño de granito o piedra prefabricada.":
    "Precast terrazzo or stone tread.",
"Revestimiento de peldaño con vinílico.":
    "Vinyl tread covering.",
"Revestimiento de descansillo de escalera.":
    "Landing finish.",
"Peldaño prefabricado de concreto.":
    "Precast concrete tread.",
"Peldaño de madera flotante.":
    "Floating wood tread.",
"Revestimiento de rampa antideslizante.":
    "Anti-slip ramp surfacing.",
"Nariz de peldaño de metal.":
    "Metal stair nosing.",
"Revestimiento de escalera completa con porcelanato.":
    "Complete stair tiling with porcelain tile.",
"Revestimiento de peldaño con piedra recuperada.":
    "Reclaimed stone tread.",
"Revestimiento de rellano con piedra natural.":
    "Natural stone landing finish.",
"Junta de dilatación en escalera.":
    "Expansion joint in a stair.",
"Pasamanos de madera sobre escalera.":
    "Wood handrail on a stair.",

# ── Trasdosados ───────────────────────────────────────────────────────────
"Trasdosado autoportante de placa de yeso laminado estándar.":
    "Standard independent drywall wall lining.",
"Trasdosado autoportante de placa de yeso con aislamiento termoacústico.":
    "Independent drywall wall lining with thermal and acoustic insulation.",
"Trasdosado autoportante con placa resistente a la humedad.":
    "Independent wall lining with moisture-resistant board.",
"Trasdosado autoportante con doble placa para mayor masa acústica.":
    "Independent wall lining with two layers of board for greater acoustic mass.",
"Trasdosado de medianería con aislamiento y placa.":
    "Party wall lining with insulation and board.",
"Trasdosado autoportante con refuerzo interior para anclaje de cargas.":
    "Independent wall lining with internal reinforcement for fastening loads.",
"Trasdosado con doble placa y aislamiento.":
    "Wall lining with two layers of board and insulation.",
"Trasdosado con barrera de vapor.":
    "Wall lining with a vapor barrier.",
"Trasdosado curvo de placa de yeso.":
    "Curved drywall wall lining.",
"Trasdosado con placa perforada acústica.":
    "Wall lining with acoustic perforated board.",
"Formación de cajón para instalaciones en trasdosado.":
    "Formation of a service void in a wall lining.",
"Trasdosado directo de placa de yeso adherida al paramento.":
    "Direct drywall lining bonded to the substrate.",
"Forro de placa de yeso sobre rastreles para cámara de instalaciones.":
    "Drywall lining on battens, forming a service void.",
"Regularización de muro con placa de yeso para ocultar instalaciones.":
    "Evening up a wall with drywall to conceal services.",
"Trasdosado autoportante con placa de alta dureza.":
    "Independent wall lining with high-impact board.",
"Tratamiento de juntas y remates de trasdosado.":
    "Treatment of the joints and finishes of a wall lining.",
"Trasdosado directo con placa de alta dureza.":
    "Direct lining with high-impact board.",
"Forro de placa de yeso sobre estructura para medianería.":
    "Drywall lining on a frame at a party wall.",
"Forro de placa de cemento exterior.":
    "Exterior cement board sheathing.",
"Forro de placa de cemento sobre estructura para área húmeda.":
    "Cement board lining on a frame in a wet area.",
"Forro de placa de cemento como soporte de enchapado en zona de ducha.":
    "Cement board lining as a tiling substrate in a shower area.",
"Forro ignífugo de placa de yeso para protección de instalaciones.":
    "Fire-rated drywall enclosure to protect services.",
"Reparación puntual de trasdosado de placa de yeso.":
    "Localized repair of a drywall wall lining.",
"Forro ignífugo de conducto de instalaciones.":
    "Fire-rated enclosure of a service duct.",
"Forro de placa de cemento en fachada.":
    "Cement board sheathing on a facade.",
"Forro de placa de yeso con registro de acceso.":
    "Drywall lining with an access panel.",
"Reparación de forro de placa de cemento.":
    "Repair of cement board sheathing.",

# ── Cielos rasos de placa ─────────────────────────────────────────────────
"Cielo raso continuo de placa de yeso laminado, estructura oculta suspendida.":
    "Continuous drywall ceiling on a concealed suspension system.",
"Cielo raso de yeso laminado con placa resistente a la humedad.":
    "Drywall ceiling with moisture-resistant board.",
"Cielo raso de yeso laminado con doble placa, acústico.":
    "Acoustic drywall ceiling with two layers of board.",
"Foso o cajón de cortina en cielo raso de yeso laminado.":
    "Curtain recess in a drywall ceiling.",
"Registro practicable en cielo raso.":
    "Access panel in a ceiling.",
"Cielo raso de yeso laminado a doble nivel.":
    "Drywall ceiling at two levels.",
"Cielo raso continuo de yeso con aislamiento acústico.":
    "Continuous drywall ceiling with acoustic insulation.",
"Cielo raso continuo de yeso con placa de alta dureza.":
    "Continuous drywall ceiling with high-impact board.",
"Cielo raso continuo de yeso con placa ignífuga.":
    "Continuous drywall ceiling with fire-rated board.",
"Cielo raso continuo curvo de yeso.":
    "Continuous curved drywall ceiling.",
"Cenefa integrada de iluminación en cielo raso.":
    "Integrated lighting cove in a ceiling.",
"Cielo raso continuo a una pendiente.":
    "Continuous sloped drywall ceiling.",
"Cielo raso de placa de cemento en área húmeda.":
    "Cement board ceiling in a wet area.",
"Reparación de cielo raso de yeso.":
    "Repair of a drywall ceiling.",
"Cielo raso continuo con doble placa y aislamiento.":
    "Continuous ceiling with two layers of board and insulation.",
"Cielo raso continuo con placa perforada acústica.":
    "Continuous ceiling with acoustic perforated board.",
"Cielo raso continuo en voladizo exterior.":
    "Continuous ceiling to an exterior overhang.",
"Cielo raso continuo con foso de iluminación integrada.":
    "Continuous ceiling with an integrated lighting recess.",
"Cielo raso continuo a doble altura.":
    "Continuous double-height ceiling.",
"Remate decorativo perimetral de cielo raso.":
    "Decorative perimeter trim to a ceiling.",
"Cielo raso de placa de yeso en foso de escalera.":
    "Drywall ceiling over a stairwell.",
"Cielo raso continuo con junta de dilatación.":
    "Continuous ceiling with an expansion joint.",
"Cielo raso continuo de placa de yeso en baño.":
    "Continuous drywall ceiling in a bathroom.",
"Cielo raso de placa de yeso con lucernario.":
    "Drywall ceiling with a skylight.",
"Cielo raso continuo con tapa de registro.":
    "Continuous ceiling with an access hatch.",
"Reparación de cielo raso con sustitución de placa.":
    "Repair of a ceiling with board replacement.",

# ── Cielos desmontables y decorativos ─────────────────────────────────────
"Cielo raso desmontable de fibra mineral en retícula vista.":
    "Mineral fiber suspended ceiling with an exposed grid.",
"Cielo raso desmontable de bandeja metálica.":
    "Suspended metal pan ceiling.",
"Cielo desmontable de fibra con perfilería oculta.":
    "Mineral fiber suspended ceiling with a concealed grid.",
"Cielo desmontable de bandeja metálica lineal.":
    "Suspended linear metal pan ceiling.",
"Cielo desmontable con aislamiento acústico.":
    "Suspended ceiling with acoustic insulation.",
"Cielo desmontable de lámina de aluminio.":
    "Suspended aluminum sheet ceiling.",
"Cielo desmontable de malla o grilla.":
    "Suspended mesh or grid ceiling.",
"Cielo desmontable de alta absorción acústica.":
    "Suspended ceiling with high acoustic absorption.",
"Cielo desmontable con sistema de clips.":
    "Suspended ceiling with a clip system.",
"Cielo raso de láminas de PVC.":
    "PVC sheet ceiling.",
"Cielo raso exterior en alero o porche.":
    "Exterior ceiling to an eave or porch.",
"Cielo raso de PVC para baño o cocina.":
    "PVC ceiling for a bathroom or kitchen.",
"Cielo raso de PVC para local comercial.":
    "PVC ceiling for commercial premises.",
"Cielo raso de machihembrado de madera.":
    "Tongued and grooved lumber ceiling.",
"Cielo raso de listones de madera.":
    "Lumber batten ceiling.",
"Cielo raso de paneles acústicos de madera.":
    "Acoustic lumber panel ceiling.",
"Cielo raso de listones de madera con junta abierta.":
    "Lumber batten ceiling with open joints.",
"Cielo raso de tablero decorativo de madera.":
    "Decorative lumber panel ceiling.",
"Moldura perimetral de remate en cielo raso.":
    "Perimeter cornice to a ceiling.",
"Cornisa para iluminación indirecta en cielo raso.":
    "Cornice for indirect lighting in a ceiling.",
"Cortinero empotrado en cielo raso.":
    "Recessed curtain track in a ceiling.",
"Borde perimetral de sombra para iluminación indirecta.":
    "Perimeter shadow gap for indirect lighting.",
"Perfil de remate perimetral entre cielo y muro.":
    "Perimeter trim between a ceiling and a wall.",
"Borde de sombra en cielo desmontable.":
    "Shadow gap in a suspended ceiling.",
"Registro de acceso en cielo desmontable.":
    "Access panel in a suspended ceiling.",
"Cielo desmontable con foseado perimetral.":
    "Suspended ceiling with a perimeter recess.",
"Perfil de cierre entre cielos de distinta cota.":
    "Closing trim between ceilings at different levels.",

# ── Pintura ───────────────────────────────────────────────────────────────
"Pintura de caucho mate lavable en paramento interior, dos manos.":
    "Washable matte latex paint on interior surfaces, two coats.",
"Pintura de caucho satinada lavable en interior, dos manos.":
    "Washable satin latex paint indoors, two coats.",
"Pintura de cielo raso, dos manos.":
    "Ceiling paint, two coats.",
"Pintura de caucho sobre friso nuevo, tres manos.":
    "Latex paint on new plaster, three coats.",
"Repintado de paramento interior sobre pintura existente.":
    "Repainting of interior surfaces over existing paint.",
"Pintura antimoho para cocina y baño.":
    "Anti-mold paint for kitchens and bathrooms.",
"Pintura semibrillo lavable de alto tránsito.":
    "Washable semi-gloss paint for high-traffic areas.",
"Pintura de pizarra efecto tiza en paramento.":
    "Chalkboard paint on a surface.",
"Pintura magnética como base de pared.":
    "Magnetic paint as a wall base coat.",
"Pintura de cielo raso de concreto visto.":
    "Paint on an exposed concrete soffit.",
"Pintura a dos colores con guarda de separación.":
    "Two-color painting with a dividing border.",
"Pintura de mocheta y remate de vanos.":
    "Painting of reveals and opening finishes.",
"Pintura de franja inferior o rodapié pintado.":
    "Painting of the lower band or baseboard.",
"Pintura mineral a base de cal para interiores.":
    "Mineral lime-based paint for interiors.",
"Pintura de techos altos con andamio.":
    "Painting of high ceilings from scaffolding.",
"Retoque y repaso puntual de pintura interior.":
    "Localized touching up of interior paintwork.",
}
