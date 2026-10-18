# -*- coding: utf-8 -*-
"""Nombres de partida — Instalaciones (2 de 4): datos, clima, ventilación y gas.

Criterios de este lote:
  · «Punto de datos/telefonía/televisión» son tomas: data outlet,
    telephone outlet, TV outlet. «Punto» solo se queda como «point» cuando
    de verdad es un punto de la instalación («Punto de red inalámbrica»).
  · «Videoportero» y «citófono» son video intercom y door entry intercom;
    no son lo mismo y en inglés tampoco.
  · Climatización se dice HVAC en inglés de obra, y «split» se escribe igual.
  · «Depósito» es storeroom, no deposit.
"""

LOTE = {
# ── Datos y telecomunicaciones ────────────────────────────────────────────
"Punto de datos, telefonía o televisión.":
    "Data, telephone or TV outlet.",
"Punto de timbre con su pulsador.":
    "Doorbell point with push button.",
"Punto de datos para computadora.":
    "Data outlet for a computer.",
"Punto de teléfono.":
    "Telephone outlet.",
"Punto de televisión.":
    "TV outlet.",
"Punto de red inalámbrica.":
    "Wireless access point.",
"Punto de datos doble.":
    "Double data outlet.",
"Punto de fibra óptica.":
    "Fiber optic outlet.",
"Punto de datos en piso.":
    "Floor data outlet.",
"Punto de datos en pared.":
    "Wall data outlet.",
"Rack de telecomunicaciones.":
    "Telecommunications rack.",
"Patch panel de red.":
    "Network patch panel.",
"Canalización de datos.":
    "Data cabling conduit.",
"Punto de datos para televisor.":
    "Data outlet for a television.",
"Punto de datos para impresora.":
    "Data outlet for a printer.",
"Punto de datos para cámara.":
    "Data outlet for a camera.",
"Punto de datos para audio.":
    "Data outlet for audio.",
"Punto de datos para domótica.":
    "Data outlet for the home automation system.",
"Punto de teléfono adicional.":
    "Additional telephone outlet.",
"Punto de televisión adicional.":
    "Additional TV outlet.",
"Punto de datos en techo.":
    "Data outlet in the ceiling.",
"Punto de datos en cielo raso.":
    "Data outlet in the suspended ceiling.",
"Punto de datos en oficina.":
    "Office data outlet.",
"Punto de datos en dormitorio.":
    "Bedroom data outlet.",
"Punto de datos en sala.":
    "Living room data outlet.",
"Punto de datos en estudio.":
    "Study data outlet.",
"Punto de datos en comedor.":
    "Dining room data outlet.",
"Punto de datos en terraza.":
    "Terrace data outlet.",
"Punto de datos para consola.":
    "Data outlet for a games console.",
"Punto de datos para router.":
    "Data outlet for a router.",
"Punto de datos para repetidor.":
    "Data outlet for a repeater.",
"Punto de datos para acceso.":
    "Data outlet for access control.",
"Punto de datos para oficina.":
    "Data outlet for an office.",

# ── Intercomunicación y audio ─────────────────────────────────────────────
"Instalación de videoportero o citófono.":
    "Video intercom or door entry intercom installation.",
"Instalación de intercomunicador.":
    "Intercom installation.",
"Instalación de videoportero con monitor.":
    "Video intercom installation with monitor.",
"Instalación de citófono.":
    "Door entry intercom installation.",
"Instalación de portero eléctrico.":
    "Electric door entry system installation.",
"Instalación de sistema de audio.":
    "Audio system installation.",
"Instalación de sistema de video.":
    "Video system installation.",
"Instalación de sonido ambiente.":
    "Background sound system installation.",
"Instalación de teatro en casa.":
    "Home theater installation.",
"Instalación de proyector.":
    "Projector installation.",
"Instalación de pantalla de proyección.":
    "Projection screen installation.",
"Instalación de altavoces.":
    "Speaker installation.",
"Instalación de amplificador.":
    "Amplifier installation.",
"Instalación de receptor de TV.":
    "TV receiver installation.",
"Instalación de antena.":
    "Antenna installation.",
"Instalación de sistema de intercomunicación.":
    "Intercom system installation.",
"Instalación de videoportero inalámbrico.":
    "Wireless video intercom installation.",
"Instalación de intercomunicador de puerta.":
    "Door intercom installation.",
"Instalación de sistema de música.":
    "Music system installation.",
"Instalación de cine en casa.":
    "Home theater installation.",
"Instalación de sonido de sala.":
    "Living room sound system installation.",
"Instalación de sonido de dormitorio.":
    "Bedroom sound system installation.",
"Instalación de sonido de terraza.":
    "Terrace sound system installation.",
"Instalación de sonido de jardín.":
    "Garden sound system installation.",
"Instalación de intercomunicación general.":
    "General intercom installation.",
"Instalación de videoportero con cámara.":
    "Video intercom installation with camera.",
"Instalación de intercomunicador de edificio.":
    "Building intercom installation.",
"Instalación de portero con video.":
    "Video door entry installation.",
"Instalación de sistema de audio multizona.":
    "Multi-zone audio system installation.",
"Instalación de sonido de ambiente.":
    "Ambient sound system installation.",
"Instalación de receptor satelital.":
    "Satellite receiver installation.",
"Instalación de sistema de cine en casa.":
    "Home theater system installation.",

# ── Climatización ─────────────────────────────────────────────────────────
"Instalación de equipo de aire acondicionado tipo split.":
    "Split system air conditioner installation.",
"Tubería frigorífica y drenaje para climatización.":
    "Refrigerant piping and drain for the HVAC system.",
"Mantenimiento y limpieza de equipo de climatización.":
    "Maintenance and cleaning of HVAC equipment.",
"Instalación de equipo split inverter.":
    "Inverter split system installation.",
"Instalación de equipo multisplit.":
    "Multi-split system installation.",
"Instalación de equipo de ventana.":
    "Window air conditioner installation.",
"Instalación de equipo de piso-techo.":
    "Floor-ceiling air conditioner installation.",
"Instalación de equipo cassette.":
    "Cassette air conditioner installation.",
"Instalación de unidad interior.":
    "Indoor unit installation.",
"Instalación de unidad condensadora.":
    "Condensing unit installation.",
"Tubería frigorífica y drenaje.":
    "Refrigerant piping and drain.",
"Carga de refrigerante.":
    "Refrigerant charge.",
"Instalación de termostato.":
    "Thermostat installation.",
"Instalación de sistema de conductos.":
    "Ducted system installation.",
"Instalación de rejilla de suministro.":
    "Supply grille installation.",
"Instalación de rejilla de retorno.":
    "Return grille installation.",
"Instalación de equipo de precisión.":
    "Precision air conditioning unit installation.",
"Instalación de equipo de confort.":
    "Comfort cooling unit installation.",
"Instalación de equipo para dormitorio.":
    "Bedroom air conditioning unit installation.",
"Instalación de equipo para sala.":
    "Living room air conditioning unit installation.",
"Instalación de equipo para oficina.":
    "Office air conditioning unit installation.",
"Instalación de equipo para comercio.":
    "Retail air conditioning unit installation.",
"Instalación de equipo para restaurante.":
    "Restaurant air conditioning unit installation.",
"Instalación de equipo para local.":
    "Air conditioning unit installation for commercial premises.",
"Instalación de equipo para consultorio.":
    "Air conditioning unit installation for a consulting room.",
"Instalación de equipo para habitación.":
    "Air conditioning unit installation for a bedroom.",
"Instalación de equipo para estudio.":
    "Air conditioning unit installation for a study.",
"Instalación de equipo para terraza.":
    "Terrace air conditioning unit installation.",
"Instalación de equipo para garaje.":
    "Garage air conditioning unit installation.",
"Instalación de equipo para depósito.":
    "Storeroom air conditioning unit installation.",
"Instalación de equipo split de pared.":
    "Wall-mounted split system installation.",
"Instalación de equipo de techo.":
    "Ceiling-mounted air conditioning unit installation.",
"Instalación de equipo de piso.":
    "Floor-mounted air conditioning unit installation.",

# ── Ventilación ───────────────────────────────────────────────────────────
"Instalación de extractor o ventilador.":
    "Exhaust fan or ventilator installation.",
"Ducto de ventilación.":
    "Ventilation duct.",
"Rejilla de ventilación en pared o cielo raso.":
    "Ventilation grille in a wall or suspended ceiling.",
"Instalación de extractor de baño.":
    "Bathroom exhaust fan installation.",
"Instalación de extractor de cocina.":
    "Kitchen exhaust fan installation.",
"Instalación de ventilador de techo.":
    "Ceiling fan installation.",
"Instalación de ventilador de pared.":
    "Wall fan installation.",
"Instalación de ventilador de piso.":
    "Floor fan installation.",
"Instalación de campana extractora.":
    "Range hood installation.",
"Instalación de ducto flexible.":
    "Flexible duct installation.",
"Instalación de ducto rígido.":
    "Rigid duct installation.",
"Instalación de rejilla de ventilación.":
    "Ventilation grille installation.",
"Instalación de rejilla de extracción.":
    "Exhaust grille installation.",
"Instalación de difusor.":
    "Diffuser installation.",
"Instalación de ventilación de baño.":
    "Bathroom ventilation installation.",
"Instalación de ventilación de cocina.":
    "Kitchen ventilation installation.",
"Instalación de ventilación de sótano.":
    "Basement ventilation installation.",
"Instalación de ventilación de garaje.":
    "Garage ventilation installation.",
"Instalación de ventilación de depósito.":
    "Storeroom ventilation installation.",
"Instalación de ventilación de lavandería.":
    "Laundry room ventilation installation.",
"Instalación de ventilación de closet.":
    "Closet ventilation installation.",
"Instalación de ventilación de cuarto técnico.":
    "Mechanical room ventilation installation.",
"Instalación de ventilación de sala.":
    "Living room ventilation installation.",
"Instalación de ventilación de dormitorio.":
    "Bedroom ventilation installation.",
"Instalación de ventilación de estudio.":
    "Study ventilation installation.",
"Instalación de ventilación de comedor.":
    "Dining room ventilation installation.",
"Instalación de ventilación de terraza.":
    "Terrace ventilation installation.",
"Instalación de ventilación de local.":
    "Ventilation installation for commercial premises.",
"Instalación de ventilación de comercio.":
    "Retail ventilation installation.",
"Instalación de ventilación de oficina.":
    "Office ventilation installation.",
"Instalación de extractor de campana.":
    "Range hood exhaust installation.",
"Instalación de ventilador de baño con sensor.":
    "Bathroom fan installation with a sensor.",
"Instalación de rejilla de retorno de aire.":
    "Air return grille installation.",

# ── Gas ───────────────────────────────────────────────────────────────────
"Tubería de gas doméstico.":
    "Domestic gas pipe.",
"Punto de gas para cocina o calentador.":
    "Gas connection for a range or water heater.",
"Regulador, medidor y protección de instalación de gas.":
    "Regulator, meter and protection for the gas installation.",
"Tubería de gas de cobre.":
    "Copper gas pipe.",
"Tubería de gas de acero.":
    "Steel gas pipe.",
"Punto de gas para estufa.":
    "Gas connection for a range.",
"Punto de gas para horno.":
    "Gas connection for an oven.",
"Punto de gas para calentador.":
    "Gas connection for a water heater.",
"Punto de gas para secadora.":
    "Gas connection for a dryer.",
}
