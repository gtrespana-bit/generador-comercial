# -*- coding: utf-8 -*-
"""Descripciones — Control de calidad y ensayos (capítulo completo, 80).

Criterios de este lote:
  · Cada descripción nombra el equipo con el que se hace la prueba, y en
    inglés ese equipo tiene nombre propio: slump cone, rebound hammer,
    cover meter, torque wrench, ground resistance tester, megohmmeter, anemometer.
    Ninguno se describe; se nombra.
  · «Puntos singulares» en una cubierta son los details: los encuentros,
    los remontes y los desagües, que es donde falla la impermeabilización.
  · «Impulsión y retorno» en climatización son supply y return.
  · «Puesta en marcha» es commissioning y «puesta en servicio» es
    commissioning, que es el momento en que se arranca.
  · «Par de apriete» es torque, no tightening moment.
"""

LOTE = {
# ── Materiales ────────────────────────────────────────────────────────────
"Toma de muestras de concreto fresco en probetas normalizadas para ensayo de resistencia a compresión, con su identificación y curado.":
    "Taking samples of fresh concrete in standard test cylinders for compression strength testing, including identification and curing.",
"Ensayo de resistencia a compresión de probeta de concreto en laboratorio, con emisión de informe.":
    "Compression strength test of a concrete test cylinder in the laboratory, with the issue of a report.",
"Determinación del asentamiento del concreto fresco con el cono de Abrams, para verificar la trabajabilidad.":
    "Determination of the slump of fresh concrete with a slump cone, to check workability.",
"Ensayo de tracción y doblado de muestra de acero de refuerzo, para verificar el límite elástico y la ductilidad.":
    "Tensile and bend test of a sample of reinforcing steel, to verify yield strength and ductility.",
"Ensayo de resistencia a compresión de bloque de mampostería, con emisión de informe.":
    "Compression strength test of a masonry block, with the issue of a report.",
"Ensayo de resistencia del mortero de pega de mampostería, con toma de muestra y laboratorio.":
    "Strength test of masonry bedding mortar, including sampling and laboratory testing.",
"Ensayo granulométrico de agregados (arena, gravilla) para verificar su idoneidad en la mezcla de concreto.":
    "Sieve analysis of aggregates (sand, gravel) to verify their suitability in the concrete mix.",
"Verificación del recubrimiento de la armadura con detector magnético, para garantizar la protección del acero.":
    "Checking the concrete cover to reinforcement with a cover meter, to ensure the steel is protected.",
"Ensayo no destructivo de la resistencia del concreto endurecido mediante esclerómetro, con informe.":
    "Non-destructive testing of the strength of hardened concrete with a rebound hammer, with a report.",
"Verificación de plomos, niveles y escuadras de muros y particiones, con nivel láser.":
    "Checking plumb, level and squareness of walls and partitions with a laser level.",

# ── Soldadura y estructura ────────────────────────────────────────────────
"Inspección visual de cordones de soldadura, verificando continuidad, penetración y ausencia de defectos superficiales.":
    "Visual inspection of weld seams, checking continuity, penetration and the absence of surface defects.",
"Ensayo de líquidos penetrantes para detección de fisuras superficiales en soldaduras, con informe.":
    "Dye penetrant testing to detect surface cracks in welding, with a report.",
"Ensayo de partículas magnéticas para detección de discontinuidades en soldaduras de acero, con informe.":
    "Magnetic particle testing to detect discontinuities in steel welding, with a report.",
"Ensayo ultrasónico de soldaduras estructurales, para detección de defectos internos, con informe.":
    "Ultrasonic testing of structural welds to detect internal defects, with a report.",
"Ensayo radiográfico de soldaduras de alta exigencia, para verificación de calidad interna, con informe.":
    "Radiographic testing of high-integrity welds to verify internal quality, with a report.",
"Prueba de carga de anclaje químico o mecánico, para verificar la capacidad de fijación a la estructura.":
    "Load testing of a chemical or mechanical anchor, to verify its fixing capacity to the structure.",
"Verificación del par de apriete de los pernos de alta resistencia de la estructura, con llave dinamométrica.":
    "Checking the tightening torque of the high-strength bolts of the structure with a torque wrench.",
"Verificación dimensional y de plomos de la estructura metálica montada, con nivel láser.":
    "Dimensional and plumb check of the erected steelwork with a laser level.",
"Ensayo de adherencia o extracción de anclajes de fachada y revestimientos, con informe.":
    "Bond or pull-out test of facade and cladding anchors, with a report.",
"Prueba de carga puntual sobre estructura de techo para verificar su capacidad, con informe.":
    "Point load test on a roof structure to verify its capacity, with a report.",

# ── Estanqueidad ──────────────────────────────────────────────────────────
"Prueba de estanqueidad de cubierta plana por inundación controlada, con registro del nivel y revisión de puntos singulares.":
    "Ponding test of a flat roof under controlled flooding, with the water level recorded and the details inspected.",
"Prueba de estanqueidad de zona húmeda (baño, ducha) por inundación, para verificar la impermeabilización.":
    "Watertightness test of a wet area (bathroom, shower) by flooding, to verify the waterproofing.",
"Prueba de estanqueidad de terraza por inundación, con revisión de desagües y remates.":
    "Watertightness test of a terrace by flooding, including inspection of the outlets and finishings.",
"Inspección visual de la membrana impermeabilizante, verificando solapes, remontes y puntos singulares.":
    "Visual inspection of the waterproofing membrane, checking laps, upstands and details.",
"Prueba de vacío sobre los solapes de la membrana impermeabilizante, para detectar defectos de soldadura.":
    "Vacuum testing of the laps of the waterproofing membrane, to detect defects in the welded joints.",
"Prueba de estanqueidad de piscina por llenado controlado, con registro de pérdidas y revisión del vaso.":
    "Watertightness test of a swimming pool under controlled filling, with the water loss recorded and the pool shell inspected.",
"Prueba de estanqueidad de tanque o depósito por llenado, para verificar la ausencia de fugas.":
    "Watertightness test of a tank or cistern by filling, to verify the absence of leaks.",
"Verificación de las pendientes de evacuación de cubiertas y pisos húmedos, con nivel láser.":
    "Checking the drainage falls of roofs and wet floors with a laser level.",
"Verificación de la impermeabilización de muro enterrado, con inspección y prueba puntual.":
    "Verification of the waterproofing of a buried wall, by inspection and a point test.",
"Emisión de informe de estanqueidad con protocolo de la prueba, para entrega a la propiedad.":
    "Issue of a watertightness report with the test record, for handover to the owner.",

# ── Fontanería ────────────────────────────────────────────────────────────
"Prueba hidrostática de la tubería de agua potable, con presión controlada y verificación de ausencia de fugas.":
    "Hydrostatic test of the potable water pipework under controlled pressure, verifying the absence of leaks.",
"Prueba de estanqueidad de la tubería de gas con manómetro y jabón detector, para verificar la ausencia de fugas.":
    "Tightness test of the gas pipework with a pressure gauge and leak detection solution, to verify the absence of leaks.",
"Prueba de desagüe de aparato sanitario por vaciado controlado, para verificar la correcta evacuación.":
    "Discharge test of a plumbing fixture under controlled discharge, to verify correct drainage.",
"Verificación de la ventilación de la red de desagüe, para evitar sifonado y malos olores.":
    "Verification of the ventilation of the drainage system, to prevent loss of trap seal and odours.",
"Prueba de presión general de la red de agua potable, con bomba de prueba y verificación de uniones.":
    "General pressure test of the potable water system with a test pump, including checking of joints.",
"Verificación de las pendientes de la tubería de desagüe, con nivel láser, para asegurar la evacuación.":
    "Checking the falls of the drainage pipework with a laser level, to ensure proper drainage.",
"Prueba de estanqueidad de la trampa de grasa, con llenado y verificación de ausencia de fugas.":
    "Watertightness test of a grease interceptor by filling and verifying the absence of leaks.",
"Verificación del funcionamiento de válvulas y llaves de corte, con apertura y cierre.":
    "Checking the operation of valves and stopcocks by opening and closing them.",
"Emisión de informe de las pruebas sanitarias realizadas, con protocolo de resultados.":
    "Issue of a report of the plumbing tests carried out, with the test record.",
"Prueba de descarga y funcionamiento de inodoro y lavamanos, verificando llenado, descarga y ausencia de fugas.":
    "Discharge and operation test of a toilet and lavatory, checking filling, discharge and the absence of leaks.",

# ── Electricidad ──────────────────────────────────────────────────────────
"Medición de la resistencia de puesta a tierra con telurómetro, para verificar el valor exigido por la norma.":
    "Measurement of ground resistance with a ground resistance tester, to verify compliance with the value required by the standard.",
"Prueba de continuidad de los conductores de la instalación eléctrica, verificando la ausencia de cortes.":
    "Continuity test of the conductors of the electrical installation, verifying there are no breaks.",
"Prueba de resistencia de aislamiento de los conductores, con megóhmetro, para verificar la ausencia de fugas.":
    "Insulation resistance test of the conductors with a megohmmeter, to verify there is no leakage.",
"Prueba de disparo de los interruptores diferenciales con el botón de test, para verificar su funcionamiento.":
    "Tripping test of the ground-fault circuit interrupters using the test button, to verify their operation.",
"Verificación del disparo de los interruptores termomagnéticos, para comprobar su calibración.":
    "Verification of the tripping of the circuit breakers, to check their calibration.",
"Verificación de la polaridad y correcta conexión del neutro en los tomacorrientes, con comprobador.":
    "Verification of the polarity and correct connection of the neutral at the receptacles with a socket tester.",
"Medición de la tensión y frecuencia de la acometida eléctrica, para verificar la calidad del suministro.":
    "Measurement of the voltage and frequency of the electrical supply, to verify the quality of the service.",
"Verificación del funcionamiento de los circuitos de iluminación, encendiendo y comprobando cada punto.":
    "Verification of the operation of the lighting circuits, switching on and checking each point.",
"Prueba de puesta en marcha del tablero de distribución, con verificación de cada circuito y su rotulado.":
    "Commissioning test of the distribution panel, including verification of each circuit and its labeling.",
"Emisión de informe de las pruebas eléctricas realizadas, con protocolo de mediciones.":
    "Issue of a report of the electrical tests carried out, with the schedule of measurements.",

# ── Climatización ─────────────────────────────────────────────────────────
"Prueba de vacío del circuito frigorífico de climatización, para eliminar humedad y verificar la estanqueidad.":
    "Vacuum test of the HVAC refrigerant circuit, to remove moisture and verify tightness.",
"Prueba de presión del circuito frigorífico con nitrógeno, para detectar fugas antes de la carga.":
    "Pressure test of the refrigerant circuit with nitrogen, to detect leaks before charging.",
"Carga de gas refrigerante del sistema de climatización, con báscula y verificación de presiones.":
    "Charging of refrigerant into the HVAC system, using scales and verifying pressures.",
"Balanceo de los caudales de ventilación, con anemómetro, para verificar la renovación de aire proyectada.":
    "Balancing of the ventilation air flows with an anemometer, to verify the specified air change rate.",
"Verificación del funcionamiento de extractores y ventiladores, con medición de caudal y ruido.":
    "Verification of the operation of extractor fans and ventilators, with measurement of flow and noise.",
"Medición de la temperatura de impulsión y retorno del sistema de climatización, para verificar el rendimiento.":
    "Measurement of the supply and return air temperature of the HVAC system, to verify performance.",
"Limpieza de serpentines y filtros del sistema de climatización, para asegurar el rendimiento.":
    "Cleaning of the coils and filters of the HVAC system, to maintain performance.",
"Verificación del drenaje de condensados del sistema de climatización, para evitar reboses.":
    "Verification of the condensate drain of the HVAC system, to prevent overflow.",
"Puesta en servicio del sistema de climatización completo, con ajuste de parámetros y verificación de rendimiento.":
    "Setting to work of the complete HVAC system, including adjustment of parameters and verification of performance.",
"Emisión de informe de puesta en marcha del sistema de climatización, con protocolo de resultados.":
    "Issue of an HVAC commissioning report, with the record of results.",

# ── Diagnosis no destructiva ──────────────────────────────────────────────
"Inspección termográfica de fachada para detectar puentes térmicos y pérdidas de energía, con informe.":
    "Thermal imaging survey of a facade to detect thermal bridges and heat loss, with a report.",
"Inspección termográfica de cubierta para detectar filtraciones y defectos de aislamiento, con informe.":
    "Thermal imaging survey of a roof to detect water ingress and insulation defects, with a report.",
"Inspección termográfica de la instalación eléctrica para detectar puntos calientes y conexiones defectuosas.":
    "Thermal imaging survey of the electrical installation to detect hot spots and defective connections.",
"Medición del contenido de humedad de muros con higrómetro, para diagnóstico de filtraciones o capilaridad.":
    "Measurement of the moisture content of walls with a moisture meter, to diagnose water ingress or rising damp.",
"Medición del contenido de humedad del piso, para verificar la idoneidad antes de colocar revestimientos.":
    "Measurement of the moisture content of a floor, to verify suitability before laying finishes.",
"Detección de armadura, tuberías y conducciones empotradas con detector, para evitar perforaciones.":
    "Detection of reinforcement, pipework and concealed services with a detector, to avoid drilling into them.",
"Inspección de fisuras en elementos estructurales, con mapeo y diagnóstico de la causa.":
    "Inspection of cracks in structural elements, with mapping and diagnosis of the cause.",
"Ensayo esclerométrico en elementos de concreto para estimar la resistencia, con informe.":
    "Rebound hammer testing of concrete elements to estimate strength, with a report.",
"Medición del espesor de recubrimiento de la armadura con detector magnético, con informe.":
    "Measurement of the thickness of the concrete cover to reinforcement with a cover meter, with a report.",
"Emisión de informe de diagnóstico no destructivo, con resultados de las inspecciones realizadas.":
    "Issue of a non-destructive testing report, with the results of the inspections carried out.",

# ── Documentación y entrega ───────────────────────────────────────────────
"Elaboración del protocolo de pruebas de puesta en marcha de las instalaciones, con firma de las partes.":
    "Preparation of the commissioning test record for the services, for signature by the parties.",
"Elaboración del protocolo de entrega de las instalaciones, con verificación final de cada sistema.":
    "Preparation of the handover record for the services, with final verification of each system.",
"Recopilación y entrega de la documentación final de obra, con planos, garantías y manuales.":
    "Compilation and handover of the final project documentation, including drawings, warranties and manuals.",
"Emisión de la certificación de la instalación eléctrica, con las mediciones y pruebas realizadas.":
    "Issue of the certificate for the electrical installation, with the measurements and tests carried out.",
"Emisión de la certificación de la instalación de gas, con la prueba de estanqueidad y cumplimiento.":
    "Issue of the certificate for the gas installation, with the tightness test and statement of compliance.",
"Emisión de la certificación de la impermeabilización, con las pruebas de estanqueidad realizadas.":
    "Issue of the certificate for the waterproofing, with the watertightness tests carried out.",
"Elaboración del manual de uso y mantenimiento del inmueble, con las pautas de conservación.":
    "Preparation of the operation and maintenance manual for the building, with the maintenance guidance.",
"Elaboración del acta de recepción de obra, con el estado final y los pendientes.":
    "Preparation of the taking-over certificate, recording the final condition and any outstanding items.",
"Prueba integral de todos los sistemas de la obra, coordinando su funcionamiento conjunto.":
    "Integrated testing of all the systems of the works, coordinating their operation together.",
"Emisión del informe de conformidad con el proyecto, verificando que la obra se ajusta a lo contratado.":
    "Issue of the report of compliance with the design, verifying that the works conform to what was contracted.",
}
