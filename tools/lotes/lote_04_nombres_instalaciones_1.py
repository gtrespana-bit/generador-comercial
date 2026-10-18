# -*- coding: utf-8 -*-
"""Nombres de partida — Instalaciones (1 de 4): fontanería y electricidad.

Criterios de este lote:
  · Un nombre de partida en inglés de obra se lee como «qué se hace»:
    «Instalación de inodoro» -> «Toilet installation», no «Installation of
    toilet», que es calco del español.
  · «Punto de agua/desagüe/fuerza» son conexiones: water connection,
    drain connection, power outlet.
  · Se conserva la coma y el remate «incluso …» -> «including …».
"""

LOTE = {
# ── Agua potable ──────────────────────────────────────────────────────────
"Tubería de agua de PPR de 20 mm, empotrada, incluso roza y resane.":
    "20 mm PPR water pipe, concealed, including chasing and patching.",
"Montante de agua de PPR de 25 mm.":
    "25 mm PPR water riser.",
"Sustitución de tramo de tubería de agua existente.":
    "Replacement of a section of existing water pipe.",
"Tubería de agua de PPR de 32 mm.":
    "32 mm PPR water pipe.",
"Tubería de agua de cobre.":
    "Copper water pipe.",
"Montante de agua de PPR de 32 mm.":
    "32 mm PPR water riser.",
"Tubería de agua caliente aislada.":
    "Insulated hot water pipe.",
"Tubería de agua vista.":
    "Exposed water pipe.",
"Tubería de agua de PPR de 40 mm.":
    "40 mm PPR water pipe.",
"Punto de agua fría y caliente para aparato sanitario.":
    "Hot and cold water connection for a plumbing fixture.",
"Punto de agua para lavadora.":
    "Water connection for a washing machine.",
"Punto de agua para calentador.":
    "Water connection for a water heater.",
"Punto de agua para nevera.":
    "Water connection for a refrigerator.",
"Punto de agua para jardín.":
    "Water connection for the garden.",
"Llave de paso de PPR de 20 mm, empotrada.":
    "20 mm PPR stop valve, concealed.",
"Llave de escuadra para aparato.":
    "Angle valve for a fixture.",
"Válvula de retención.":
    "Check valve.",
"Llave general de agua.":
    "Main water shut-off valve.",

# ── Aparatos sanitarios ───────────────────────────────────────────────────
"Instalación de inodoro con su conexión de agua y desagüe.":
    "Toilet installation, including water and drain connections.",
"Instalación de lavamanos con su grifería y desagüe.":
    "Lavatory installation, including faucet and drain.",
"Instalación de ducha o regadera con su grifería.":
    "Shower installation, including faucet.",
"Instalación de fregadero con su grifería.":
    "Kitchen sink installation, including faucet.",
"Instalación de calentador de agua.":
    "Water heater installation.",
"Instalación de accesorios de baño.":
    "Bathroom accessories installation.",
"Instalación de lavadero o poceta de servicio.":
    "Utility sink installation.",
"Instalación de bidé o ducha higiénica.":
    "Bidet or hand shower installation.",
"Instalación de lavamanos con mueble.":
    "Vanity basin installation.",
"Instalación de inodoro de tanque.":
    "Close-coupled toilet installation.",
"Instalación de grifería de ducha.":
    "Shower faucet installation.",
"Instalación de grifería de lavamanos.":
    "Lavatory faucet installation.",
"Instalación de grifería de cocina.":
    "Kitchen faucet installation.",
"Instalación de bidé.":
    "Bidet installation.",
"Instalación de grifería de bañera.":
    "Bathtub faucet installation.",
"Instalación de grifería de ducha exterior.":
    "Outdoor shower faucet installation.",

# ── Desagües ──────────────────────────────────────────────────────────────
"Tubería de desagüe de PVC sanitario de 4 pulgadas.":
    "4 inch PVC sanitary drain pipe.",
"Instalación de trampa de grasa.":
    "Grease interceptor installation.",
"Registro de aguas servidas.":
    "Cleanout on the soil line.",
"Bajante de desagüe de PVC de 2 pulgadas.":
    "2 inch PVC waste stack.",
"Tubería de desagüe de 2 pulgadas.":
    "2 inch drain pipe.",
"Montante de desagüe.":
    "Waste riser.",
"Bajante de aguas de lluvia.":
    "Rainwater downspout.",
"Canalón de aguas lluvias.":
    "Rainwater gutter.",
"Tragante de cubierta.":
    "Roof drain.",
"Canal de drenaje.":
    "Drainage channel.",
"Bajante de desagüe de 6 pulgadas.":
    "6 inch waste stack.",
"Montante de desagüe de cocina.":
    "Kitchen waste riser.",
"Tubería de desagüe de cocina.":
    "Kitchen drain pipe.",
"Tubería de ventilación de desagüe.":
    "Vent pipe.",
"Bajante de aguas servidas.":
    "Soil stack.",
"Punto de desagüe para aparato sanitario.":
    "Drain connection for a plumbing fixture.",
"Punto de desagüe para lavadora.":
    "Drain connection for a washing machine.",
"Punto de desagüe para calentador.":
    "Drain connection for a water heater.",
"Punto de desagüe para nevera.":
    "Drain connection for a refrigerator.",
"Punto de desagüe para ducha.":
    "Shower drain connection.",
"Punto de desagüe para fregadero.":
    "Kitchen sink drain connection.",
"Punto de desagüe para lavamanos.":
    "Lavatory drain connection.",
"Punto de desagüe para inodoro.":
    "Toilet drain connection.",
"Punto de desagüe para bañera.":
    "Bathtub drain connection.",
"Punto de desagüe para bidé.":
    "Bidet drain connection.",
"Punto de desagüe para lavadero.":
    "Utility sink drain connection.",
"Punto de desagüe para cocina.":
    "Kitchen drain connection.",
"Punto de desagüe para terraza.":
    "Terrace drain connection.",
"Punto de desagüe para jardín.":
    "Garden drain connection.",

# ── Electricidad: acometida y protecciones ────────────────────────────────
"Acometida eléctrica desde el punto de suministro.":
    "Electrical service from the supply point.",
"Caja de medidor y protección de servicio.":
    "Meter socket with service protection.",
"Acometida eléctrica subterránea.":
    "Underground electrical service.",
"Puesta a tierra con electrodo.":
    "Grounding with an electrode.",
"Electrodo de puesta a tierra.":
    "Grounding electrode.",
"Tablero eléctrico de distribución.":
    "Electrical distribution panel.",
"Interruptor termomagnético de protección de circuito.":
    "Circuit breaker for branch circuit protection.",
"Interruptor diferencial de protección de personas.":
    "Ground-fault circuit interrupter for personal protection.",
"Revisión y certificación de instalación eléctrica.":
    "Inspection and certification of the electrical installation.",
"Tablero eléctrico con protecciones.":
    "Electrical panel with protective devices.",
"Interruptor termomagnético.":
    "Circuit breaker.",
"Interruptor diferencial.":
    "Ground-fault circuit interrupter.",
"Tablero eléctrico para baño.":
    "Electrical panel for a bathroom.",

# ── Canalizaciones ────────────────────────────────────────────────────────
"Canalización eléctrica en cielo raso o superficie.":
    "Electrical conduit in a suspended ceiling or surface mounted.",
"Canalización eléctrica para equipo de climatización.":
    "Electrical conduit for HVAC equipment.",
"Canalización eléctrica empotrada.":
    "Concealed electrical conduit.",
"Canalización eléctrica en piso.":
    "Electrical conduit in the floor.",
"Canalización eléctrica en techo.":
    "Electrical conduit in the ceiling.",
"Canalización eléctrica empotrada con conduit de 20 mm y conductor 12 AWG.":
    "Concealed electrical conduit, 20 mm, with 12 AWG conductor.",
"Canalización con conductor de 10 AWG.":
    "Conduit with 10 AWG conductor.",

# ── Puntos de fuerza y mecanismos ─────────────────────────────────────────
"Punto de fuerza para electrodoméstico o equipo.":
    "Power outlet for an appliance or piece of equipment.",
"Reubicación de punto eléctrico existente.":
    "Relocation of an existing electrical point.",
"Punto de fuerza para cocina.":
    "Power outlet for the kitchen.",
"Punto de fuerza para secadora.":
    "Power outlet for a dryer.",
"Punto de fuerza para horno.":
    "Power outlet for an oven.",
"Punto de fuerza para cocina eléctrica.":
    "Power outlet for an electric range.",
"Punto de fuerza para secadora eléctrica.":
    "Power outlet for an electric dryer.",
"Punto de interruptor o tomacorriente, incluso caja y mecanismo.":
    "Switch or receptacle point, including box and device.",
"Punto de tomacorriente doble.":
    "Duplex receptacle point.",
"Punto de interruptor doble.":
    "Double switch point.",
"Punto de tomacorriente con USB.":
    "Receptacle point with USB.",
"Punto de interruptor de conmutación.":
    "Three-way switch point.",

# ── Iluminación ───────────────────────────────────────────────────────────
"Instalación de luminaria empotrada en cielo raso.":
    "Recessed light fixture installation in a suspended ceiling.",
"Instalación de luminaria de sobreponer o colgante.":
    "Surface-mounted or pendant light fixture installation.",
"Iluminación lineal con cinta LED.":
    "Linear lighting with LED strip.",
"Instalación de reflector o luminaria de exterior.":
    "Outdoor floodlight or light fixture installation.",
"Punto para ventilador de techo.":
    "Ceiling fan point.",
"Instalación de luminaria LED empotrada.":
    "Recessed LED light fixture installation.",
"Instalación de luminaria de pared.":
    "Wall light fixture installation.",
"Instalación de aplique de exterior.":
    "Outdoor wall light installation.",
"Instalación de luminaria de emergencia.":
    "Emergency light fixture installation.",
"Instalación de foco de piso.":
    "Floor-recessed light installation.",
"Instalación de luminaria de closet.":
    "Closet light fixture installation.",
"Instalación de luminaria de espejo.":
    "Mirror light installation.",
"Instalación de tira LED en zócalo.":
    "LED strip installation in the baseboard.",
"Instalación de luminaria colgante.":
    "Pendant light fixture installation.",
"Instalación de luminaria de techo.":
    "Ceiling light fixture installation.",
"Instalación de reflector con sensor.":
    "Floodlight installation with a sensor.",
"Instalación de luminaria de riel.":
    "Track light installation.",
"Instalación de luminaria de piscina.":
    "Pool light installation.",
"Instalación de luminaria de jardín.":
    "Garden light installation.",
"Instalación de luminaria de garaje.":
    "Garage light fixture installation.",
"Instalación de luminaria de escalera.":
    "Stair light fixture installation.",
"Instalación de luminaria decorativa.":
    "Decorative light fixture installation.",
"Instalación de luminaria de oficina.":
    "Office light fixture installation.",
"Instalación de luminaria de baño.":
    "Bathroom light fixture installation.",
"Instalación de luminaria de cocina.":
    "Kitchen light fixture installation.",
"Instalación de luminaria de sala.":
    "Living room light fixture installation.",
"Instalación de luminaria de dormitorio.":
    "Bedroom light fixture installation.",
"Instalación de luminaria de pasillo.":
    "Hallway light fixture installation.",
"Instalación de luminaria de fachada.":
    "Facade light installation.",
"Instalación de luminaria de terraza.":
    "Terrace light installation.",
"Instalación de luminaria de lavandería.":
    "Laundry room light fixture installation.",
"Instalación de luminaria de recibidor.":
    "Entry hall light fixture installation.",
"Instalación de luminaria de comedor.":
    "Dining room light fixture installation.",
"Instalación de luminaria de estudio.":
    "Study light fixture installation.",
"Instalación de luminaria de emergencia con señal.":
    "Emergency light fixture installation with sign.",
}
