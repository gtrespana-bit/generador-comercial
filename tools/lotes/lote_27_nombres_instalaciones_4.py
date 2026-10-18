# -*- coding: utf-8 -*-
"""Nombres de partida — Instalaciones (4 de 4): bombeo, generación,
transporte vertical y puesta en marcha. Cierra el capítulo y el catálogo.

Criterios de este lote:
  · «Ascensor» es elevator en Estados Unidos y lift en Reino Unido. Es la
    pareja más visible de todo el catálogo: se ve en cada presupuesto y
    en cada cartel, y equivocarse delata al instante.
  · «Montacargas» es dos cosas distintas: dumbwaiter cuando sube comida o
    platos entre plantas de una cocina, y freight elevator cuando sube
    carga. El español usa la misma palabra y el inglés no.
  · «Salvaescaleras» es stairlift, una sola palabra.
  · «Puesta en marcha» es commissioning: no es «start-up», es el proceso
    completo de probar, ajustar y dejar el sistema en servicio.
  · «Planta eléctrica» es generator, no electric plant.
  · «Inversor de red» es grid-tie inverter y «aislado» es off-grid
    inverter; «híbrido» es hybrid inverter.
"""

LOTE = {
# ── Protectores de sobretensión ───────────────────────────────────────────
"Protector de sobretensión combinado.": "Combined surge protector.",
"Protector de sobretensión de red.": "Mains surge protector.",
"Protector de sobretensión de teléfono.": "Telephone line surge protector.",
"Protector de sobretensión de antena.": "Antenna surge protector.",
"Protector de sobretensión de datos.": "Data line surge protector.",

# ── Tanques ───────────────────────────────────────────────────────────────
"Instalación de tanque de agua.": "Water tank installation.",
"Instalación de tanque séptico prefabricado.":
    "Precast septic tank installation.",
"Instalación de tanque elevado.": "Elevated tank installation.",
"Instalación de tanque enterrado.": "Buried tank installation.",
"Instalación de tanque de presión.": "Pressure tank installation.",
"Instalación de válvula de flotante.": "Float valve installation.",
"Instalación de tanque de reserva.": "Reserve tank installation.",
"Instalación de tanque de agua caliente.":
    "Hot water tank installation.",
"Instalación de tanque séptico.": "Septic tank installation.",
"Instalación de tanque de tormenta.": "Stormwater tank installation.",
"Instalación de tanque cisterna.": "Cistern installation.",
"Instalación de tanque de agua potable.":
    "Potable water tank installation.",
"Instalación de tanque de agua elevado.":
    "Elevated water tank installation.",
"Instalación de tanque de agua enterrado.":
    "Buried water tank installation.",
"Instalación de tanque de presión hidroneumático.":
    "Hydropneumatic pressure tank installation.",
"Instalación de tanque de reserva de agua.":
    "Reserve water tank installation.",

# ── Bombas ────────────────────────────────────────────────────────────────
"Instalación de bomba centrífuga de agua.":
    "Centrifugal water pump installation.",
"Instalación de sistema hidroneumático.":
    "Hydropneumatic system installation.",
"Instalación de bomba de agua.": "Water pump installation.",
"Instalación de bomba sumergible.": "Submersible pump installation.",
"Instalación de bomba presurizadora.": "Booster pump installation.",
"Instalación de bomba de achique.": "Sump pump installation.",
"Instalación de bomba de recirculación.":
    "Recirculation pump installation.",
"Instalación de sistema de bombeo.": "Pumping system installation.",
"Instalación de bomba de piscina.": "Pool pump installation.",
"Instalación de bomba de pozo.": "Well pump installation.",
"Instalación de bomba contra incendios.": "Fire pump installation.",
"Instalación de bomba de riego.": "Irrigation pump installation.",
"Instalación de bomba centrífuga.": "Centrifugal pump installation.",
"Instalación de bomba de superficie.": "Surface pump installation.",
"Instalación de bomba de agua potable.":
    "Potable water pump installation.",
"Instalación de bomba de agua residual.": "Sewage pump installation.",
"Sistema hidroneumático de presión constante.":
    "Constant pressure hydropneumatic system.",
"Instalación de bomba presurizadora de agua.":
    "Water booster pump installation.",

# ── Generación de respaldo y solar ────────────────────────────────────────
"Instalación de planta eléctrica de respaldo.":
    "Backup generator installation.",
"Instalación de sistema de respaldo con inversor y baterías.":
    "Backup system installation with an inverter and batteries.",
"Tablero de transferencia entre red y respaldo.":
    "Transfer switch between the mains and the backup supply.",
"Instalación de panel solar.": "Solar panel installation.",
"Instalación de inversor.": "Inverter installation.",
"Instalación de batería.": "Battery installation.",
"Instalación de planta eléctrica.": "Generator installation.",
"Instalación de tablero de transferencia.":
    "Transfer switch installation.",
"Instalación de regulador de carga.": "Charge controller installation.",
"Instalación de sistema solar.": "Solar system installation.",
"Instalación de banco de baterías.": "Battery bank installation.",
"Instalación de inversor híbrido.": "Hybrid inverter installation.",
"Instalación de panel solar en techo.": "Roof solar panel installation.",
"Instalación de panel solar en terraza.":
    "Solar panel installation on a terrace.",
"Instalación de panel solar en jardín.":
    "Solar panel installation in a garden.",
"Instalación de estructura de paneles.":
    "Installation of the panel support structure.",
"Instalación de cableado solar.": "Solar cabling installation.",
"Instalación de protecciones solares.":
    "Installation of solar system protective devices.",
"Instalación de medidor bidireccional.":
    "Bidirectional meter installation.",
"Instalación de sistema de respaldo.": "Backup system installation.",
"Instalación de planta de respaldo.":
    "Backup generator installation.",
"Instalación de batería de litio.": "Lithium battery installation.",
"Instalación de batería de plomo.": "Lead-acid battery installation.",
"Instalación de inversor de red.": "Grid-tie inverter installation.",
"Instalación de inversor aislado.": "Off-grid inverter installation.",
"Instalación de sistema fotovoltaico.":
    "Photovoltaic system installation.",
"Instalación de panel solar doméstico.":
    "Domestic solar panel installation.",
"Instalación de panel solar comercial.":
    "Commercial solar panel installation.",
"Instalación de planta eléctrica diésel.":
    "Diesel generator installation.",
"Instalación de planta eléctrica a gas.": "Gas generator installation.",
"Instalación de panel solar de 400W.":
    "400 W solar panel installation.",
"Instalación de inversor de 3kW.": "3 kW inverter installation.",
"Instalación de batería de 200Ah.": "200 Ah battery installation.",

# ── Ascensors y transporte vertical ───────────────────────────────────────
"Instalación de ascensor unifamiliar.":
    "Installation of a residential elevator.",
"Instalación de ascensor de dos paradas.":
    "Installation of a two-stop elevator.",
"Instalación de montacargas.": "Installation of a freight elevator.",
"Instalación de plataforma elevadora.":
    "Installation of a platform lift.",
"Adecuación de hueco de ascensor.":
    "Adaptation of an elevator shaft.",
"Instalación de ascensor panorámico.":
    "Installation of a panoramic elevator.",
"Instalación de ascensor de carga.":
    "Installation of a freight elevator.",
"Instalación de ascensor hidráulico.":
    "Installation of a hydraulic elevator.",
"Instalación de ascensor de tracción.":
    "Installation of a traction elevator.",
"Instalación de ascensor sin cuarto de máquinas.":
    "Installation of a machine-room-less elevator.",
"Instalación de montacargas de cocina.":
    "Installation of a dumbwaiter.",
"Adecuación de foso de ascensor.":
    "Adaptation of an elevator pit.",
"Instalación de ascensor de 3 paradas.":
    "Installation of a three-stop elevator.",
"Instalación de ascensor de 4 paradas.":
    "Installation of a four-stop elevator.",
"Instalación de ascensor de 5 paradas.":
    "Installation of a five-stop elevator.",
"Instalación de ascensor de 6 paradas.":
    "Installation of a six-stop elevator.",
"Instalación de ascensor para discapacitados.":
    "Installation of an accessible elevator.",
"Instalación de ascensor de carga pesada.":
    "Installation of a heavy-duty freight elevator.",
"Modernización de ascensor existente.":
    "Modernization of an existing elevator.",
"Instalación de ascensor de alta velocidad.":
    "Installation of a high-speed elevator.",
"Instalación de montacargas de carga.":
    "Installation of a freight elevator.",
"Instalación de salvaescaleras.": "Installation of a stairlift.",
"Instalación de elevador de plataforma.":
    "Installation of a platform lift.",
"Instalación de salvaescaleras de plataforma.":
    "Installation of a platform stairlift.",
"Instalación de elevador de fachada.":
    "Installation of a facade lift.",
"Instalación de silla salvaescaleras.":
    "Installation of a seated stairlift.",
"Instalación de plataforma salvaescaleras.":
    "Installation of a platform stairlift.",
"Instalación de elevador de silla.":
    "Installation of a chair lift.",
"Instalación de rampa mecánica.":
    "Installation of an inclined moving walkway.",

# ── Pruebas y puesta en marcha ────────────────────────────────────────────
"Prueba hidráulica de instalación de agua.":
    "Hydraulic test of the water installation.",
"Prueba de instalación eléctrica.":
    "Testing of the electrical installation.",
"Prueba de instalación de gas.": "Testing of the gas installation.",
"Puesta en marcha de sistema de climatización.":
    "Commissioning of the HVAC system.",
"Puesta en marcha de sistema de bombeo.":
    "Commissioning of the pumping system.",
"Puesta en marcha de sistema eléctrico de respaldo.":
    "Commissioning of the electrical backup system.",
"Puesta en marcha de sistema domótico.":
    "Commissioning of the home automation system.",
"Puesta en marcha de sistema contra incendios.":
    "Commissioning of the fire protection system.",
"Puesta en marcha de sistema solar.":
    "Commissioning of the solar system.",
"Puesta en marcha de sistema de ventilación.":
    "Commissioning of the ventilation system.",
"Puesta en marcha de sistema de gas.":
    "Commissioning of the gas system.",
"Puesta en marcha de sistema de alarma.":
    "Commissioning of the alarm system.",
"Puesta en marcha de sistema de acceso.":
    "Commissioning of the access control system.",
"Prueba de presión de gas.": "Pressure test of the gas installation.",
"Prueba de aislamiento eléctrico.":
    "Insulation resistance test of the electrical installation.",

# ── Reparaciones ──────────────────────────────────────────────────────────
"Reparación de fuga de tubería.": "Repair of a pipe leak.",
"Reparación de punto eléctrico.":
    "Repair of an electrical outlet.",
"Reparación de desagüe obstruido.": "Clearing of a blocked drain.",
"Reparación de grifería.": "Repair of a faucet.",
"Reparación de luminaria.": "Repair of a light fixture.",
"Reparación de equipo de climatización.":
    "Repair of HVAC equipment.",
"Reparación de tablero eléctrico.":
    "Repair of an electrical panel.",
"Reparación de sistema de seguridad.":
    "Repair of the security system.",
"Reparación de bomba de agua.": "Repair of a water pump.",
"Reparación de tanque de agua.": "Repair of a water tank.",
"Reparación de panel solar.": "Repair of a solar panel.",
"Reparación de inversor.": "Repair of an inverter.",
"Reparación de ventilador.": "Repair of a fan.",
"Reparación de extractor.": "Repair of an extractor fan.",
}
