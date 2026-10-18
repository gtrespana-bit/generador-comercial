# -*- coding: utf-8 -*-
"""Nombres de partida — Control de calidad y ensayos (capítulo completo, 80).

Criterios de este lote:
  · «Probeta» de concreto es test cylinder en Estados Unidos y test cube
    en Reino Unido: allí se rompen cubos, aquí cilindros.
  · «Asentamiento» del concreto es slump en los dos sitios; el español
    ya lo traía entre paréntesis.
  · Los ensayos no destructivos de soldadura tienen nombre propio:
    dye penetrant, magnetic particle, ultrasonic, radiographic.
  · «Esclerometría» es rebound hammer test, el nombre del martillo de
    Schmidt en un informe.
  · «Acta de recepción de obra» es taking-over certificate, que es el
    documento y no el acto.
"""

LOTE = {
# ── Materiales ────────────────────────────────────────────────────────────
"Toma de muestras de concreto para ensayo.":
    "Taking of concrete samples for testing.",
"Ensayo de compresión de probeta de concreto.":
    "Compression test of a concrete test cylinder.",
"Ensayo de asentamiento (slump) del concreto.":
    "Slump test of concrete.",
"Ensayo de acero de refuerzo a tracción.":
    "Tensile test of reinforcing steel.",
"Ensayo de compresión de bloques de mampostería.":
    "Compression test of masonry blocks.",
"Ensayo de mortero de pega.": "Test of bedding mortar.",
"Ensayo de granulometría de agregados.":
    "Sieve analysis of aggregates.",
"Control de recubrimiento de armadura.":
    "Checking of concrete cover to reinforcement.",
"Ensayo de resistencia de piso de concreto.":
    "Strength testing of a concrete floor.",
"Verificación de plomos y niveles de muros.":
    "Checking the plumb and level of walls.",

# ── Estructura y soldadura ────────────────────────────────────────────────
"Inspección visual de soldadura.": "Visual inspection of welding.",
"Ensayo de líquidos penetrantes en soldadura.":
    "Dye penetrant testing of welding.",
"Ensayo de partículas magnéticas en soldadura.":
    "Magnetic particle testing of welding.",
"Ensayo ultrasónico de soldadura.": "Ultrasonic testing of welding.",
"Ensayo radiográfico de soldadura.": "Radiographic testing of welding.",
"Prueba de carga de anclaje químico.":
    "Load testing of a chemical anchor.",
"Control de apriete de pernos estructurales.":
    "Checking the tightening of structural bolts.",
"Inspección dimensional de estructura metálica.":
    "Dimensional inspection of steelwork.",
"Ensayo de adherencia de anclaje de fachada.":
    "Pull-out test of a facade anchor.",
"Prueba de carga de estructura de techo.":
    "Load testing of a roof structure.",

# ── Estanqueidad ──────────────────────────────────────────────────────────
"Prueba de estanqueidad de cubierta por inundación.":
    "Ponding test of a roof deck.",
"Prueba de estanqueidad de baño o ducha.":
    "Watertightness test of a bathroom or shower.",
"Prueba de estanqueidad de terraza.":
    "Watertightness test of a terrace.",
"Inspección de membrana impermeabilizante.":
    "Inspection of the waterproofing membrane.",
"Prueba de vacío en solapes de membrana.":
    "Vacuum testing of membrane laps.",
"Prueba de estanqueidad de piscina.":
    "Watertightness test of a swimming pool.",
"Prueba de estanqueidad de tanque.":
    "Watertightness test of a tank.",
"Control de pendientes de evacuación.":
    "Checking of drainage falls.",
"Ensayo de impermeabilización de muro enterrado.":
    "Waterproofing test of a buried wall.",
"Informe de estanqueidad con protocolo.":
    "Watertightness report with a test record.",

# ── Instalaciones sanitarias ──────────────────────────────────────────────
"Prueba hidrostática de tubería de agua.":
    "Hydrostatic test of a water pipe.",
"Prueba de fugas de tubería de gas.":
    "Leak test of a gas pipe.",
"Prueba de desagüe por vaciado.":
    "Drainage test by discharging water.",
"Prueba de ventilación de desagüe.":
    "Test of the drainage vent system.",
"Prueba de presión de la red de agua.":
    "Pressure test of the water system.",
"Verificación de pendientes de desagüe.":
    "Checking of drainage falls.",
"Prueba de estanqueidad de trampa de grasa.":
    "Watertightness test of a grease interceptor.",
"Prueba de funcionamiento de válvulas.":
    "Operational test of valves.",
"Informe de pruebas sanitarias.": "Plumbing test report.",
"Prueba de descarga de inodoro y lavamanos.":
    "Discharge test of a toilet and lavatory.",

# ── Instalaciones eléctricas ──────────────────────────────────────────────
"Medición de resistencia de puesta a tierra.":
    "Measurement of ground resistance.",
"Prueba de continuidad de conductores.":
    "Continuity test of conductors.",
"Prueba de aislamiento de conductores.":
    "Insulation resistance test of conductors.",
"Prueba de disparo de diferenciales.":
    "Tripping test of ground-fault circuit interrupters.",
"Prueba de disparo de termomagnéticos.":
    "Tripping test of circuit breakers.",
"Verificación de polaridad y neutro.":
    "Checking of polarity and neutral.",
"Medición de tensión y frecuencia.":
    "Measurement of voltage and frequency.",
"Prueba de iluminación de circuitos.":
    "Functional test of lighting circuits.",
"Prueba de puesta en marcha de tablero.":
    "Commissioning test of an electrical panel.",
"Informe de pruebas eléctricas.": "Electrical test report.",

# ── Climatización ─────────────────────────────────────────────────────────
"Prueba de vacío de sistema de climatización.":
    "Vacuum test of the HVAC system.",
"Prueba de presión de gas refrigerante.":
    "Pressure test of the refrigerant circuit.",
"Carga de gas refrigerante.": "Charging of refrigerant.",
"Balanceo de caudales de ventilación.":
    "Balancing of ventilation air flows.",
"Prueba de funcionamiento de extractores.":
    "Operational test of extractor fans.",
"Prueba de temperatura de impulsión.":
    "Test of supply air temperature.",
"Limpieza de serpentines y filtros.":
    "Cleaning of coils and filters.",
"Prueba de drenaje de condensados.":
    "Test of the condensate drain.",
"Puesta en servicio de climatización con ajuste.":
    "Commissioning of the HVAC system, including commissioning.",
"Informe de puesta en marcha de climatización.":
    "HVAC commissioning report.",

# ── Ensayos no destructivos y diagnosis ───────────────────────────────────
"Termografía infrarroja de fachada.":
    "Infrared thermography of a facade.",
"Termografía infrarroja de cubierta.":
    "Infrared thermography of a roof deck.",
"Termografía de instalación eléctrica.":
    "Thermography of the electrical installation.",
"Medición de humedad de muros.":
    "Measurement of moisture in walls.",
"Medición de humedad de piso.":
    "Measurement of moisture in a floor.",
"Detección de armadura y tuberías empotradas.":
    "Detection of reinforcement and concealed piping.",
"Inspección de fisuras y diagnóstico estructural.":
    "Inspection of cracks and structural diagnosis.",
"Ensayo de esclerometría en elementos de concreto.":
    "Rebound hammer test of concrete elements.",
"Medición de espesor de recubrimiento.":
    "Measurement of the thickness of the concrete cover.",
"Informe de diagnóstico no destructivo.":
    "Non-destructive testing report.",

# ── Documentación y entrega ───────────────────────────────────────────────
"Protocolo de pruebas de puesta en marcha.":
    "Commissioning test record.",
"Protocolo de entrega de instalaciones.":
    "Handover record for services.",
"Documentación final de obra.": "Final project documentation.",
"Certificación de instalación eléctrica.":
    "Certification of the electrical installation.",
"Certificación de instalación de gas.":
    "Certification of the gas installation.",
"Certificación de impermeabilización.":
    "Certification of the waterproofing.",
"Manual de uso y mantenimiento.":
    "Operation and maintenance manual.",
"Acta de recepción de obra.": "Taking-over certificate.",
"Prueba integral de sistemas.": "Integrated testing of systems.",
"Informe de conformidad con proyecto.":
    "Report of compliance with the design.",
}
