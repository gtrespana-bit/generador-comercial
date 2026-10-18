# -*- coding: utf-8 -*-
"""Nombres de partida — Aislamientos e impermeabilizaciones (150).

Capítulo completo.

Criterios de este lote:
  · «Manto asfáltico» es bituminous membrane. En el oficio anglosajón
    «felt» se reserva para la lámina tradicional y «membrane» es la
    forma general, así que se usa membrane salvo cuando la lámina es
    literalmente de fieltro asfáltico.
  · «Cubierta» cambia de palabra según de qué se trate: roof deck cuando
    es la superficie que se impermeabiliza, roof cuando es el conjunto.
  · «Peto» es parapet y «remate» es flashing cuando es chapa o banda que
    echa el agua, y trim cuando es puramente estético.
  · «Suelo radiante» es radiant floor heating en Estados Unidos y
    radiant floor heating en Reino Unido.
  · «Humedad ascendente» es rising damp, que es exactamente el término
    británico consagrado; en Estados Unidos se describe, no se nombra.
  · «Lámina nodular» es dimpled membrane, y «manta» es blanket cuando es
    fibra y membrane cuando es una lámina.
"""

LOTE = {
# ── Aislamiento térmico ───────────────────────────────────────────────────
"Aislamiento térmico en cubierta.": "Thermal insulation to a roof deck.",
"Aislamiento acústico en tabique o cielo raso.":
    "Acoustic insulation in a partition or ceiling.",
"Aislamiento térmico reflectivo bajo cubierta.":
    "Reflective thermal insulation beneath a roof.",
"Aislamiento térmico de muro con poliestireno extruido.":
    "Thermal insulation of a wall with extruded polystyrene.",
"Aislamiento térmico de piso con poliestireno.":
    "Thermal insulation of a floor with polystyrene.",
"Aislamiento térmico de muro con lana de roca.":
    "Thermal insulation of a wall with rock wool.",
"Aislamiento térmico de fachada por el exterior.":
    "External thermal insulation of a facade.",
"Aislamiento térmico de cubierta con panel sándwich.":
    "Thermal insulation of a roof deck with sandwich panels.",
"Aislamiento térmico reflectivo en fachada.":
    "Reflective thermal insulation on a facade.",
"Aislamiento térmico de tubería.": "Thermal insulation of piping.",
"Aislamiento térmico de losa con poliestireno.":
    "Thermal insulation of a slab with polystyrene.",
"Aislamiento de pared medianera con lana de roca.":
    "Insulation of a party wall with rock wool.",
"Aislamiento térmico de muro por el interior.":
    "Internal thermal insulation of a wall.",
"Aislamiento térmico bajo techo inclinado.":
    "Thermal insulation beneath a pitched roof.",
"Aislamiento térmico de techo con poliestireno.":
    "Thermal insulation of a roof with polystyrene.",
"Aislamiento térmico de fachada con panel sándwich.":
    "Thermal insulation of a facade with sandwich panels.",
"Aislamiento de puente térmico en vigas.":
    "Insulation of thermal bridges at beams.",
"Aislamiento térmico de suelo radiante.":
    "Thermal insulation of a radiant floor heating system.",
"Aislamiento térmico de depósito de agua.":
    "Thermal insulation of a water tank.",
"Aislamiento térmico de conducto de climatización.":
    "Thermal insulation of an HVAC duct.",
"Aislamiento térmico de cubierta transitable.":
    "Thermal insulation of a trafficable roof deck.",
"Aislamiento térmico de tabique con doble panel.":
    "Thermal insulation of a partition with a double panel.",
"Aislamiento reflectivo de techo metálico.":
    "Reflective insulation to a metal roof.",
"Aislamiento térmico de cámara de aire con reflectivo.":
    "Thermal insulation of an air cavity with a reflective layer.",

# ── Aislamiento acústico ──────────────────────────────────────────────────
"Aislamiento acústico de tabique con lana mineral.":
    "Acoustic insulation of a partition with mineral wool.",
"Aislamiento acústico de medianería.":
    "Acoustic insulation of a party wall.",
"Aislamiento acústico de cielo raso.":
    "Acoustic insulation of a ceiling.",
"Aislamiento acústico de conducto.":
    "Acoustic insulation of a duct.",
"Tratamiento acústico de sala con paneles.":
    "Acoustic treatment of a room with panels.",
"Suelo flotante acústico con manta.":
    "Acoustic floating floor with an underlay.",
"Suelo flotante con panel de lana mineral.":
    "Floating floor on mineral wool panels.",
"Banda perimetral de desolidarización.":
    "Perimeter isolation strip.",
"Aislamiento de impacto en piso.":
    "Impact sound insulation to a floor.",
"Suelo flotante con doble manta acústica.":
    "Floating floor with a double acoustic underlay.",
"Aislamiento de vibraciones en equipo.":
    "Vibration isolation of equipment.",

# ── Impermeabilización de cimentación y muros enterrados ──────────────────
"Impermeabilización de fundación con manto asfáltico.":
    "Waterproofing of a foundation with a bituminous membrane.",
"Impermeabilización de fundación con bentonita.":
    "Waterproofing of a foundation with bentonite.",
"Impermeabilización de muro enterrado con manto.":
    "Waterproofing of a buried wall with a membrane.",
"Impermeabilización de muro enterrado con membrana líquida.":
    "Waterproofing of a buried wall with a liquid membrane.",
"Impermeabilización de muro enterrado con bentonita.":
    "Waterproofing of a buried wall with bentonite.",
"Impermeabilización de muro enterrado con cementosa.":
    "Waterproofing of a buried wall with a cementitious membrane.",
"Protección de impermeabilización con lámina drenante.":
    "Protection of waterproofing with a drainage membrane.",
"Barrera anticapilaridad en arranque de muro.":
    "Damp-proof course at the base of a wall.",
"Impermeabilización de muro enterrado con manto autoadherido.":
    "Waterproofing of a buried wall with a self-adhesive membrane.",
"Impermeabilización de muro enterrado con lámina de PVC.":
    "Waterproofing of a buried wall with a PVC membrane.",
"Sellado de juntas de hormigonado con bentonita.":
    "Sealing of construction joints with bentonite.",
"Impermeabilización de sótano con membrana líquida.":
    "Waterproofing of a basement with a liquid membrane.",
"Impermeabilización de muro enterrado por su cara interior.":
    "Waterproofing of a buried wall from the inside.",

# ── Impermeabilización de cubiertas y terrazas ────────────────────────────
"Impermeabilización de cubierta con manto asfáltico.":
    "Waterproofing of a roof deck with a bituminous membrane.",
"Refuerzo de encuentros y petos en impermeabilización asfáltica.":
    "Reinforcement of junctions and parapets in a bituminous waterproofing.",
"Protección de impermeabilización con capa de gravilla.":
    "Protection of waterproofing with a gravel layer.",
"Impermeabilización de cubierta con doble manto.":
    "Waterproofing of a roof deck with two membrane layers.",
"Impermeabilización de cubierta con manto autoadherido.":
    "Waterproofing of a roof deck with a self-adhesive membrane.",
"Impermeabilización de cubierta con protección de gravilla.":
    "Waterproofing of a roof deck with a gravel protection layer.",
"Impermeabilización de cubierta con membrana de PVC.":
    "Waterproofing of a roof deck with a PVC membrane.",
"Impermeabilización con acrílico elastomérico y malla.":
    "Waterproofing with an elastomeric acrylic and mesh.",
"Impermeabilización con membrana líquida de poliuretano.":
    "Waterproofing with a liquid polyurethane membrane.",
"Impermeabilización con membrana cementosa flexible.":
    "Waterproofing with a flexible cementitious membrane.",
"Sellado de fisuras en cubierta previo a impermeabilización.":
    "Sealing of cracks in a roof deck before waterproofing.",
"Impermeabilización de terraza con membrana líquida.":
    "Waterproofing of a terrace with a liquid membrane.",
"Impermeabilización de balcón con acrílico elastomérico.":
    "Waterproofing of a balcony with an elastomeric acrylic.",
"Impermeabilización de techo con cementosa flexible.":
    "Waterproofing of a roof with a flexible cementitious membrane.",
"Impermeabilización de cubierta con poliurea.":
    "Waterproofing of a roof deck with polyurea.",
"Impermeabilización de peto y remate de cubierta.":
    "Waterproofing of a parapet and roof trim.",
"Impermeabilización de canaleta de cubierta.":
    "Waterproofing of a roof channel.",
"Impermeabilización de techo de concreto.":
    "Waterproofing of a concrete roof.",
"Impermeabilización de terraza con baldosa flotante.":
    "Waterproofing of a terrace with pedestal-mounted pavers.",
"Impermeabilización de techo metálico.":
    "Waterproofing of a metal roof.",
"Impermeabilización de techo de teja.":
    "Waterproofing of a tile roof.",
"Impermeabilización de cubierta invertida.":
    "Waterproofing of an inverted roof.",
"Impermeabilización de losa de techo entre pisos.":
    "Waterproofing of an intermediate roof slab.",
"Impermeabilización de terraza con acabado decorativo.":
    "Waterproofing of a terrace with a decorative finish.",
"Impermeabilización de techo con capa de protección.":
    "Waterproofing of a roof with a protection layer.",
"Impermeabilización de techo de madera.":
    "Waterproofing of a wood roof.",
"Impermeabilización de cubierta con manta reflectiva.":
    "Waterproofing of a roof deck with a reflective membrane.",
"Impermeabilización de remate de chimenea.":
    "Waterproofing of a chimney flashing.",

# ── Impermeabilización de zonas húmedas ───────────────────────────────────
"Impermeabilización de piso de baño o ducha bajo enchapado.":
    "Waterproofing of a bathroom or shower floor beneath the tiling.",
"Impermeabilización de jardinera o maceta de obra.":
    "Waterproofing of a masonry planter.",
"Sellado de pase de tubería en impermeabilización.":
    "Sealing of a pipe penetration in waterproofing.",
"Impermeabilización interior de tanque de agua.":
    "Internal waterproofing of a water tank.",
"Impermeabilización de balcón o terraza transitable.":
    "Waterproofing of a trafficable balcony or terrace.",
"Impermeabilización de muro de ducha.":
    "Waterproofing of a shower wall.",
"Impermeabilización de piso de cocina.":
    "Waterproofing of a kitchen floor.",
"Impermeabilización de lavandería.":
    "Waterproofing of a laundry room.",
"Impermeabilización de zona de bañera.":
    "Waterproofing of a bathtub area.",
"Impermeabilización de cuarto de máquinas.":
    "Waterproofing of a mechanical room.",
"Sellado perimetral de ducha con banda.":
    "Perimeter sealing of a shower with a sealing tape.",
"Impermeabilización de techo de baño.":
    "Waterproofing of a bathroom ceiling.",
"Impermeabilización de piso de ducha con pendiente.":
    "Waterproofing of a sloped shower floor.",
"Impermeabilización de muro de cocina.":
    "Waterproofing of a kitchen wall.",
"Impermeabilización de piso de baño existente.":
    "Waterproofing of an existing bathroom floor.",
"Impermeabilización de sauna o vapor.":
    "Waterproofing of a sauna or steam room.",
"Impermeabilización de piscina interior.":
    "Waterproofing of an indoor swimming pool.",
"Impermeabilización de área de piscina de spa.":
    "Waterproofing of a spa pool area.",
"Impermeabilización de balcón con manta.":
    "Waterproofing of a balcony with a membrane.",
"Impermeabilización de zona de riego interior.":
    "Waterproofing of an internal irrigation area.",
"Impermeabilización de baño con membrana líquida.":
    "Waterproofing of a bathroom with a liquid membrane.",
"Impermeabilización de cocina con membrana líquida.":
    "Waterproofing of a kitchen with a liquid membrane.",
"Impermeabilización de ducha con membrana de PVC.":
    "Waterproofing of a shower with a PVC membrane.",
"Impermeabilización de cuarto húmedo con cementosa.":
    "Waterproofing of a wet room with a cementitious membrane.",
"Impermeabilización de piso de baño con pendiente.":
    "Waterproofing of a sloped bathroom floor.",
"Impermeabilización de baño existente con membrana.":
    "Waterproofing of an existing bathroom with a membrane.",

# ── Piscinas, tanques y fuentes ───────────────────────────────────────────
"Impermeabilización de piscina con membrana líquida.":
    "Waterproofing of a swimming pool with a liquid membrane.",
"Impermeabilización de piscina con cementosa.":
    "Waterproofing of a swimming pool with a cementitious membrane.",
"Impermeabilización de piscina con manto de PVC.":
    "Waterproofing of a swimming pool with a PVC membrane.",
"Impermeabilización de tanque de agua con membrana cementosa.":
    "Waterproofing of a water tank with a cementitious membrane.",
"Impermeabilización de jardinera de obra.":
    "Waterproofing of a masonry planter.",
"Impermeabilización de tanque de concreto.":
    "Waterproofing of a concrete tank.",
"Impermeabilización de piscina con doble membrana.":
    "Waterproofing of a swimming pool with two membrane layers.",
"Impermeabilización de tanque metálico.":
    "Waterproofing of a metal tank.",
"Impermeabilización de piscina elevada.":
    "Waterproofing of a raised swimming pool.",
"Impermeabilización de jardinera con drenaje.":
    "Waterproofing of a planter with drainage.",
"Impermeabilización de piscina de fibra.":
    "Waterproofing of a fiberglass swimming pool.",
"Impermeabilización de fuente ornamental.":
    "Waterproofing of an ornamental fountain.",

# ── Drenaje y capas ───────────────────────────────────────────────────────
"Drenaje perimetral con tubería perforada.":
    "Perimeter drainage with perforated pipe.",
"Colocación de geotextil separador.":
    "Installation of a separating geotextile.",
"Capa drenante con lámina nodular.":
    "Drainage layer with a dimpled membrane.",
"Drenaje de cubierta con canaleta.":
    "Roof drainage with a channel.",
"Drenaje de jardín con tubería perforada.":
    "Garden drainage with perforated pipe.",
"Capa drenante con geocompuesto.":
    "Drainage layer with a geocomposite.",
"Capa separadora de polietileno.":
    "Polyethylene separating layer.",
"Capa de protección con gravilla.":
    "Protection layer of gravel.",
"Capa de protección con mortero.":
    "Protection layer of mortar.",
"Capa separadora geotextil en terraza.":
    "Geotextile separating layer on a terrace.",
"Drenaje de trasdós con geotextil y grava.":
    "Drainage behind a wall with a geotextile and gravel.",
"Capa drenante de cubierta ajardinada.":
    "Drainage layer of a green roof.",

# ── Sellado de juntas ─────────────────────────────────────────────────────
"Sellado de junta de construcción con poliuretano.":
    "Sealing of a construction joint with polyurethane.",
"Sellado de junta de hormigonado con bentonita.":
    "Sealing of a construction joint with bentonite.",
"Sellado de junta con banda de PVC.":
    "Sealing of a joint with a PVC waterstop.",
"Sellado de junta de dilatación en piso.":
    "Sealing of an expansion joint in a floor.",
"Sellado de junta de dilatación en fachada.":
    "Sealing of an expansion joint in a facade.",
"Sellado de junta de dilatación en cubierta.":
    "Sealing of an expansion joint in a roof deck.",
"Sellado de junta en piscina.":
    "Sealing of a joint in a swimming pool.",
"Sellado de junta perimetral de muro.":
    "Sealing of a perimeter joint of a wall.",
"Sellado de paso de instalaciones en muro.":
    "Sealing of a services penetration in a wall.",
"Sellado de junta de encuentro piso-pared.":
    "Sealing of the floor and wall junction.",
"Sellado de junta de dilatación en escalera.":
    "Sealing of an expansion joint in a stair.",
"Sellado de junta en tanque.":
    "Sealing of a joint in a tank.",

# ── Filtraciones y humedades ──────────────────────────────────────────────
"Inyección de resina en fisura.":
    "Resin injection into a crack.",
"Tratamiento de filtración en techo.":
    "Treatment of a leak in a roof.",
"Reparación de filtración en muro enterrado.":
    "Repair of a leak in a buried wall.",
"Tratamiento de filtración en piscina.":
    "Treatment of a leak in a swimming pool.",
"Reparación de filtración en terraza.":
    "Repair of a leak in a terrace.",
"Tratamiento de humedad ascendente por capilaridad.":
    "Treatment of rising damp.",
"Tratamiento antihumedad de muro interior.":
    "Damp-proofing treatment of an interior wall.",
"Saneado de muro con eflorescencias salinas.":
    "Removal of salt efflorescence from a wall.",
"Tratamiento de humedad en sótano.":
    "Damp treatment in a basement.",
"Tratamiento de humedad por condensación.":
    "Treatment of condensation damp.",
"Barrera antihumedad en piso.":
    "Damp-proof membrane in a floor.",
"Tratamiento de humedad en muro de piedra.":
    "Damp treatment in a stone wall.",
}
