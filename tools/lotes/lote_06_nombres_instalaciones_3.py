# -*- coding: utf-8 -*-
"""Nombres de partida — Instalaciones (3 de 4): gas, incendios, seguridad,
domótica y protección contra rayos.

Criterios de este lote:
  · Protección contra incendios con el nombre que usa el oficio:
    «pulsador de alarma» es manual pull station, «rociador» es sprinkler,
    «central de incendios» es fire alarm control panel.
  · Protección contra rayos: «pararrayos» es air terminal o lightning rod
    según el tipo, «bajante» aquí es down conductor (no downspout, que es
    el de aguas de lluvia), y «sobretensión transitoria» es surge.
  · «Depósito» es storeroom; «local» son commercial premises.
"""

LOTE = {
# ── Gas ───────────────────────────────────────────────────────────────────
"Instalación de regulador de gas.": "Gas regulator installation.",
"Instalación de medidor de gas.": "Gas meter installation.",
"Instalación de llave de corte de gas.": "Gas shut-off valve installation.",
"Instalación de detector de gas.": "Gas detector installation.",
"Instalación de válvula de seguridad.": "Safety valve installation.",
"Tubería de gas de montante.": "Gas riser.",
"Punto de gas para cocina.": "Gas connection for the kitchen.",
"Punto de gas para lavandería.": "Gas connection for the laundry room.",
"Punto de gas para terraza.": "Gas connection for the terrace.",
"Punto de gas para parrillera.": "Gas connection for a barbecue grill.",
"Tubería de gas empotrada.": "Concealed gas pipe.",
"Tubería de gas vista.": "Exposed gas pipe.",
"Acometida de gas.": "Gas service connection.",
"Instalación de gabinete de gas.": "Gas cabinet installation.",
"Prueba de estanqueidad de gas.": "Gas tightness test.",
"Instalación de válvula de exceso de flujo.": "Excess flow valve installation.",
"Instalación de regulador de alta presión.": "High-pressure regulator installation.",
"Instalación de regulador de baja presión.": "Low-pressure regulator installation.",
"Tubería de gas flexible.": "Flexible gas pipe.",
"Punto de gas para secadora de ropa.": "Gas connection for a clothes dryer.",
"Punto de gas para calentador de paso.": "Gas connection for a tankless water heater.",
"Tubería de gas de polietileno.": "Polyethylene gas pipe.",
"Punto de gas para cocina industrial.": "Gas connection for a commercial kitchen.",
"Instalación de válvula de gas.": "Gas valve installation.",

# ── Protección contra incendios ───────────────────────────────────────────
"Suministro y colocación de extintor portátil.":
    "Supply and installation of a portable fire extinguisher.",
"Instalación de detector de humo y alarma.": "Smoke detector and alarm installation.",
"Instalación de gabinete contra incendios.": "Fire equipment cabinet installation.",
"Instalación de extintor de CO2.": "CO2 fire extinguisher installation.",
"Instalación de extintor de espuma.": "Foam fire extinguisher installation.",
"Instalación de detector de humo.": "Smoke detector installation.",
"Instalación de detector de calor.": "Heat detector installation.",
"Instalación de alarma de incendio.": "Fire alarm installation.",
"Instalación de pulsador de alarma.": "Manual fire alarm pull station installation.",
"Instalación de sirena.": "Siren installation.",
"Instalación de luz de emergencia.": "Emergency light installation.",
"Instalación de señalización de evacuación.": "Exit signage installation.",
"Instalación de rociador.": "Sprinkler installation.",
"Instalación de gabinete de manguera.": "Fire hose cabinet installation.",
"Instalación de hidrante.": "Hydrant installation.",
"Instalación de central de incendios.": "Fire alarm control panel installation.",
"Instalación de detectores en dormitorio.": "Detector installation in a bedroom.",
"Instalación de detectores en cocina.": "Detector installation in a kitchen.",
"Instalación de detectores en garaje.": "Detector installation in a garage.",
"Instalación de detectores en depósito.": "Detector installation in a storeroom.",
"Instalación de detectores en sala.": "Detector installation in a living room.",
"Instalación de detectores en pasillo.": "Detector installation in a hallway.",
"Instalación de detectores en escalera.": "Detector installation in a stair.",
"Instalación de extintor en cocina.": "Fire extinguisher installation in a kitchen.",
"Instalación de extintor en garaje.": "Fire extinguisher installation in a garage.",
"Instalación de extintor en local.":
    "Fire extinguisher installation in commercial premises.",
"Instalación de extintor en comercio.": "Fire extinguisher installation in a shop.",
"Instalación de extintor en oficina.": "Fire extinguisher installation in an office.",
"Instalación de extintor en depósito.":
    "Fire extinguisher installation in a storeroom.",
"Instalación de extintor en terraza.": "Fire extinguisher installation on a terrace.",
"Instalación de extintor de polvo.": "Dry powder fire extinguisher installation.",
"Instalación de detector combinado.": "Combination detector installation.",
"Instalación de señal de salida.": "Exit sign installation.",

# ── Seguridad y videovigilancia ───────────────────────────────────────────
"Punto de alarma, cámara o control de acceso.":
    "Point for an alarm, camera or access control device.",
"Instalación de alarma perimetral.": "Perimeter alarm installation.",
"Instalación de alarma interior.": "Interior alarm installation.",
"Instalación de cámara de seguridad.": "Security camera installation.",
"Instalación de cámara exterior.": "Outdoor camera installation.",
"Instalación de cámara interior.": "Indoor camera installation.",
"Instalación de grabador de video.": "Video recorder installation.",
"Instalación de monitor de vigilancia.": "Surveillance monitor installation.",
"Instalación de control de acceso.": "Access control installation.",
"Instalación de lector de tarjetas.": "Card reader installation.",
"Instalación de teclado de acceso.": "Access keypad installation.",
"Instalación de sensor de puerta.": "Door sensor installation.",
"Instalación de sensor de ventana.": "Window sensor installation.",
"Instalación de sensor de movimiento.": "Motion sensor installation.",
"Instalación de sirena de alarma.": "Alarm siren installation.",
"Instalación de panel de alarma.": "Alarm panel installation.",
"Instalación de sistema CCTV.": "CCTV system installation.",
"Instalación de sistema de alarma.": "Alarm system installation.",
"Instalación de sistema de acceso.": "Access control system installation.",
"Instalación de cámara de garaje.": "Garage camera installation.",
"Instalación de cámara de entrada.": "Entrance camera installation.",
"Instalación de cámara de terraza.": "Terrace camera installation.",
"Instalación de cámara de jardín.": "Garden camera installation.",
"Instalación de cámara de local.": "Camera installation in commercial premises.",
"Instalación de cámara de comercio.": "Shop camera installation.",
"Instalación de alarma con sensores.": "Alarm installation with sensors.",
"Instalación de cámara con grabador.": "Camera installation with a recorder.",
"Instalación de control de acceso biométrico.":
    "Biometric access control installation.",
"Instalación de sensor de puerta y ventana.": "Door and window sensor installation.",
"Instalación de sirena exterior.": "Outdoor siren installation.",
"Instalación de panel de control.": "Control panel installation.",
"Instalación de sistema de video vigilancia.": "Video surveillance system installation.",

# ── Domótica ──────────────────────────────────────────────────────────────
"Central domótica con configuración inicial.":
    "Home automation controller with initial configuration.",
"Pasarela de comunicación entre protocolos.": "Gateway between protocols.",
"Repetidor de señal inalámbrica para la red domótica.":
    "Wireless signal repeater for the home automation network.",
"Central domótica con control remoto.":
    "Home automation controller with remote control.",
"Repetidor de señal cableada.": "Wired signal repeater.",
"Sensor de movimiento para iluminación y alarmas.":
    "Motion sensor for lighting and alarms.",
"Sensor magnético de apertura de puerta o ventana.":
    "Magnetic door or window contact.",
"Sensor de temperatura y humedad ambiente.":
    "Ambient temperature and humidity sensor.",
"Detector de inundación o fuga de agua.": "Flood or water leak detector.",
"Detector de gas doméstico con alarma.": "Domestic gas detector with alarm.",
"Sensor de nivel de luz para automatización.":
    "Light level sensor for automation.",
"Sensor de calidad de aire.": "Air quality sensor.",
"Sensor de consumo eléctrico.": "Power consumption sensor.",
"Sensor de presencia.": "Occupancy sensor.",
"Módulo de actuación on/off para circuitos de iluminación.":
    "On/off actuator module for lighting circuits.",
"Módulo regulador para atenuación de iluminación.": "Dimmer module for lighting.",
"Módulo de control de persiana o cortina motorizada.":
    "Control module for a motorized blind or curtain.",
"Módulo de enchufe inteligente para cargas enchufables.":
    "Smart plug module for plug-in loads.",
"Termostato inteligente para control de climatización.":
    "Smart thermostat for HVAC control.",
"Actuador de calefacción.": "Heating actuator.",
"Actuador de riego.": "Irrigation actuator.",
"Módulo de control de bomba.": "Pump control module.",
"Panel táctil de pared para el sistema domótico.":
    "Wall-mounted touch panel for the home automation system.",
"Teclado de escenas para activación directa.":
    "Scene keypad for direct activation.",
"Panel de control táctil.": "Touch control panel.",
"Pulsador de escena inalámbrico.": "Wireless scene push button.",
"Termostato inalámbrico.": "Wireless thermostat.",
"Programación de escenas y automatizaciones.":
    "Programming of scenes and automations.",
"Prueba y verificación del sistema domótico.":
    "Testing and verification of the home automation system.",

# ── Protección contra rayos ───────────────────────────────────────────────
"Pararrayos con dispositivo de cebado sobre mástil en cubierta.":
    "Early streamer emission air terminal on a mast on the roof.",
"Pararrayos tipo Franklin de punta simple sobre soporte.":
    "Franklin lightning rod, single point, on a support.",
"Malla captadora de cubierta para protección contra rayos.":
    "Roof air-termination network for lightning protection.",
"Conductor captador de cumbrera y perímetro de cubierta.":
    "Air-termination conductor along the ridge and roof perimeter.",
"Captación de pararrayos en chimenea.":
    "Air terminal on a chimney for lightning protection.",
"Captación de pararrayos en antena.": "Air terminal on an antenna.",
"Malla captadora en fachada.": "Air-termination network on the facade.",
"Captación de pararrayos en cumbrera.": "Air terminal along the ridge.",
"Bajante de cobre desnudo con fijaciones.":
    "Bare copper down conductor with fasteners.",
"Bajante con contador de descargas y mando de comprobación.":
    "Down conductor with strike counter and test joint.",
"Puesta a tierra dedicada para protección contra rayos.":
    "Dedicated grounding for lightning protection.",
"Unión equipotencial de la bajante con la red de tierra general.":
    "Equipotential bonding of the down conductor to the general grounding system.",
"Bajante de cobre aislada.": "Insulated copper down conductor.",
"Bajante de aluminio.": "Aluminum down conductor.",
"Toma de tierra de pararrayos.": "Grounding electrode for lightning protection.",
"Bajante con unión de comprobación.": "Down conductor with test joint.",
"Toma de tierra en anillo.": "Ring grounding electrode.",
"Protector contra sobretensiones transitorias tipo 1 en tablero principal.":
    "Type 1 surge protective device at the main panel.",
"Protector contra sobretensiones transitorias tipo 2 en tablero secundario.":
    "Type 2 surge protective device at the subpanel.",
"Protector contra sobretensiones tipo 3 para equipos sensibles.":
    "Type 3 surge protective device for sensitive equipment.",
"Protector contra sobretensiones para línea de datos y telecomunicaciones.":
    "Surge protective device for data and telecommunications lines.",
"Prueba y verificación del sistema de protección contra rayos.":
    "Testing and verification of the lightning protection system.",
}
