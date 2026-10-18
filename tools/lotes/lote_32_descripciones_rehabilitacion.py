# -*- coding: utf-8 -*-
"""Descripciones — Rehabilitación energética (capítulo completo, 100).

Criterios de este lote:
  · «Envolvente térmica» es thermal envelope y «puente térmico» es thermal
    bridge: son los dos términos que sostienen el capítulo entero.
  · «Marco de ruptura de puente térmico» es thermally broken frame, que es
    como se vende la carpintería y como hay que pedirla.
  · «Ventilación mecánica controlada» es mechanical ventilation with heat
    recovery: en el Reino Unido se dice MVHR y en Estados Unidos HRV o
    ERV, pero la descripción de una partida lo escribe entero.
  · «Insuflado» es blown cuando se sopla celulosa en una cámara, y
    «proyectada» es sprayed cuando se proyecta lana mineral.
  · «Cámara sanitaria» es crawl space.
  · El cierre «El vidrio lo elige el cliente» es una nota de medición: en
    un presupuesto inglés se escribe «The glazing is selected by the
    client», porque lo que se está diciendo es que el precio no lo
    incluye.
"""

LOTE = {
# ── Diagnóstico ───────────────────────────────────────────────────────────
"Evaluación energética de la vivienda, con inspección de la envolvente, instalaciones y consumos, y emisión de informe.":
    "Energy assessment of the dwelling, with inspection of the thermal envelope, services and consumption, and the issue of a report.",
"Diagnóstico de puentes térmicos de la envolvente con termografía, para identificar pérdidas de energía.":
    "Diagnosis of thermal bridges in the envelope by thermal imaging, to identify heat loss.",
"Auditoría de los consumos energéticos de la vivienda, con análisis de facturas y propuesta de mejora.":
    "Audit of the energy consumption of the dwelling, with analysis of bills and a proposal for improvement.",
"Medición de las infiltraciones de aire de la vivienda, para evaluar la estanqueidad de la envolvente.":
    "Measurement of the air infiltration of the dwelling, to assess the airtightness of the envelope.",
"Emisión del informe de certificación energética de la vivienda, con la calificación obtenida.":
    "Issue of the energy performance certificate report for the dwelling, with the rating obtained.",
"Estudio de viabilidad de incorporación de energías renovables, con análisis de radiación y consumos.":
    "Feasibility study for the incorporation of renewable energy, with analysis of solar radiation and consumption.",
"Medición de los espesores de aislamiento existentes en la envolvente, con detector.":
    "Measurement of the thickness of the existing insulation in the envelope with a detector.",
"Inspección del estado de la carpintería y vidrios, para evaluar su contribución a las pérdidas térmicas.":
    "Inspection of the condition of the joinery and glazing, to assess their contribution to heat loss.",
"Levantamiento de la envolvente térmica de la vivienda, con medición de superficies y composición.":
    "Survey of the thermal envelope of the dwelling, with measurement of areas and construction.",
"Elaboración de propuesta de medidas de rehabilitación energética, con estimación de ahorros.":
    "Preparation of a proposal of energy refurbishment measures, with an estimate of the savings.",
"Seguimiento y medición del ahorro energético tras la rehabilitación, con comparación de consumos.":
    "Monitoring and measurement of the energy saving after the refurbishment, by comparison of consumption.",

# ── Fachada ───────────────────────────────────────────────────────────────
"Colocación de panel de poliestireno extruido sobre fachada, fijado y con capa de protección.":
    "Installation of extruded polystyrene boards on a facade, fixed and with a protective coating.",
"Colocación de panel de lana de roca sobre fachada, fijado y con capa de protección.":
    "Installation of rock wool boards on a facade, fixed and with a protective coating.",
"Sistema de aislamiento térmico exterior (SATE) de fachada con poliestireno expandido, malla y mortero.":
    "External insulation and finish system (EIFS) to a facade, with expanded polystyrene, mesh and stucco.",
"Ejecución de fachada ventilada con subestructura metálica y aislamiento térmico, con cámara de aire.":
    "Construction of a ventilated facade with a metal support frame and thermal insulation, with an air cavity.",
"Colocación de panel composite sobre fachada, con fijación mecánica, para mejorar el aislamiento y la estética.":
    "Installation of composite panels on a facade, mechanically fixed, to improve insulation and appearance.",
"Proyección de lana mineral aislante sobre fachada, para relleno de cámaras y mejora térmica.":
    "Spraying of insulating mineral wool on a facade, to fill cavities and improve thermal performance.",
"Inyección de aislamiento en la cámara de aire de la fachada, para mejorar la resistencia térmica.":
    "Injection of insulation into the cavity of the facade, to improve thermal resistance.",
"Colocación de refuerzo de aislamiento en petos, cantos y puntos singulares de la fachada.":
    "Installation of additional insulation at parapets, edges and details of the facade.",
"Ejecución de remates de aislamiento en esquinas, juntas y encuentros de la fachada.":
    "Finishing of the insulation at corners, joints and junctions of the facade.",
"Tratamiento de los puentes térmicos de fachada con piezas de aislamiento en los puntos singulares.":
    "Treatment of the thermal bridges of the facade with insulation pieces at the details.",
"Acabado de fachada aislada con mortero de protección y malla, listo para el revestimiento final.":
    "Finishing of an insulated facade with a protective stucco and mesh, ready for the final coating.",

# ── Cubierta y techo ──────────────────────────────────────────────────────
"Colocación de panel de poliestireno extruido sobre el techo, para reducir las pérdidas térmicas.":
    "Installation of extruded polystyrene boards on the roof, to reduce heat loss.",
"Colocación de panel de lana de roca sobre el techo, para mejora del aislamiento térmico y acústico.":
    "Installation of rock wool boards on the roof, to improve thermal and acoustic insulation.",
"Colocación de manta reflectiva de doble burbuja bajo cubierta, para reducir la ganancia de calor.":
    "Installation of double bubble reflective foil beneath the roof, to reduce heat gain.",
"Colocación de panel de lana mineral sobre cubierta plana, previo a la impermeabilización.":
    "Installation of mineral wool boards on a flat roof, before the waterproofing.",
"Colocación de aislamiento entre las viguetas del techo, para eliminar puentes térmicos.":
    "Installation of insulation between the ceiling joists, to eliminate thermal bridges.",
"Colocación de barrera de vapor bajo el aislamiento de cubierta, para evitar condensaciones.":
    "Installation of a vapor control layer beneath the roof insulation, to prevent condensation.",
"Insulfado de celulosa aislante en el espacio bajo cubierta, para mejora térmica y acústica.":
    "Blowing of insulating cellulose into the space beneath the roof, to improve thermal and acoustic performance.",
"Colocación de refuerzo de aislamiento en la cumbrera de la cubierta, para eliminar el puente térmico.":
    "Installation of additional insulation at the ridge of the roof, to eliminate the thermal bridge.",
"Colocación de aislamiento en el perímetro del lucernario o claraboya, para reducir las pérdidas.":
    "Installation of insulation around the perimeter of the rooflight, to reduce heat loss.",
"Ejecución de cubierta fría con aislamiento y cámara ventilada, para reducir la ganancia de calor.":
    "Construction of a cold roof with insulation and a ventilated cavity, to reduce heat gain.",
"Colocación de aislamiento en el techo que separa espacios acondicionados de no acondicionados.":
    "Installation of insulation in the ceiling separating conditioned from unconditioned spaces.",

# ── Piso ──────────────────────────────────────────────────────────────────
"Colocación de panel de poliestireno bajo el piso, para reducir las pérdidas térmicas al terreno.":
    "Installation of polystyrene boards beneath the floor, to reduce heat loss to the ground.",
"Colocación de manta reflectiva bajo el piso, para mejorar el confort y reducir pérdidas.":
    "Installation of reflective foil beneath the floor, to improve comfort and reduce heat loss.",
"Colocación de aislamiento en el perímetro del piso, para evitar el puente térmico con el terreno.":
    "Installation of insulation around the perimeter of the floor, to avoid the thermal bridge to the ground.",
"Colocación de aislamiento en el entrepiso entre viviendas, para mejora térmica y acústica.":
    "Installation of insulation in the floor between dwellings, to improve thermal and acoustic performance.",
"Colocación de aislamiento bajo el piso sobre cámara sanitaria, para evitar pérdidas al exterior.":
    "Installation of insulation beneath the floor over a crawl space, to prevent heat loss to outside.",
"Colocación de aislamiento en el piso del ático, para reducir la pérdida de calor por el techo.":
    "Installation of insulation in the attic floor, to reduce heat loss through the roof.",
"Colocación de banda perimetral elástica en el encuentro piso-muro, para eliminar el puente acústico y térmico.":
    "Installation of an elastic perimeter strip at the floor to wall junction, to eliminate the acoustic and thermal bridge.",
"Colocación de panel rígido de lana mineral bajo el piso, para aislamiento térmico y acústico.":
    "Installation of rigid mineral wool boards beneath the floor, for thermal and acoustic insulation.",
"Tratamiento del puente térmico en el canto del losa, con pieza de aislamiento.":
    "Treatment of the thermal bridge at the edge of the slab, with an insulation piece.",
"Colocación de aislamiento en el piso del garaje, para reducir la pérdida térmica al exterior.":
    "Installation of insulation in the garage floor, to reduce heat loss to outside.",
"Regularización del piso con mortero aligerado aislante, para mejorar la resistencia térmica.":
    "Leveling of the floor with lightweight insulating mortar, to improve thermal resistance.",

# ── Huecos ────────────────────────────────────────────────────────────────
"Sustitución de ventana por doble acristalamiento con cámara de aire, para reducir las pérdidas térmicas. El vidrio lo elige el cliente.":
    "Replacement of a window with double glazing with an air space, to reduce heat loss. The glazing is selected by the client.",
"Sustitución de ventana por vidrio templado de seguridad, para mejora térmica y de resistencia. El vidrio lo elige el cliente.":
    "Replacement of a window with safety tempered glass, to improve thermal performance and strength. The glazing is selected by the client.",
"Sustitución de ventana por vidrio de control solar, para reducir la ganancia térmica. El vidrio lo elige el cliente.":
    "Replacement of a window with solar control glass, to reduce heat gain. The glazing is selected by the client.",
"Sustitución de ventana con marco de ruptura de puente térmico y doble acristalamiento. El sistema lo elige el cliente.":
    "Replacement of a window with a thermally broken frame and double glazing. The system is selected by the client.",
"Sellado del perímetro de las ventanas, para eliminar las infiltraciones de aire.":
    "Sealing of the perimeter of the windows, to eliminate air infiltration.",
"Sustitución de la junta de estanqueidad de las ventanas, para mejorar la hermeticidad.":
    "Replacement of the weather seals of the windows, to improve airtightness.",
"Calafateado y sellado de la carpintería exterior, para eliminar infiltraciones de aire y agua.":
    "Caulking and sealing of the external joinery, to eliminate air and water infiltration.",
"Colocación de persiana aislante con cajón estanco, para mejorar el aislamiento del hueco. La persiana la elige el cliente.":
    "Installation of an insulated roller shutter with a sealed box, to improve the insulation of the opening. The shutter is selected by the client.",
"Sustitución de puerta exterior por una con núcleo aislante, para reducir las pérdidas. La puerta la elige el cliente.":
    "Replacement of an external door with one having an insulated core, to reduce heat loss. The door is selected by the client.",
"Colocación de burlete de estanqueidad en el perímetro de las puertas exteriores, para reducir infiltraciones.":
    "Installation of draught seals around the perimeter of the external doors, to reduce infiltration.",
"Sustitución por ventana de doble acristalamiento con gas argón y marco aislante, de altas prestaciones. El sistema lo elige el cliente.":
    "Replacement with a high performance window with argon-filled double glazing and a thermally broken frame. The system is selected by the client.",

# ── Protección solar ──────────────────────────────────────────────────────
"Colocación de toldo exterior de protección solar, para reducir la ganancia térmica. El toldo lo elige el cliente.":
    "Installation of an external solar shading awning, to reduce heat gain. The awning is selected by the client.",
"Colocación de persiana enrollable de aluminio para control solar. La persiana la elige el cliente.":
    "Installation of an aluminum roller shutter for solar control. The shutter is selected by the client.",
"Colocación de celosía o romanilla de aluminio para sombreado, reduciendo la ganancia solar.":
    "Installation of an aluminum louver screen for shading, reducing solar gain.",
"Ejecución de pérgola de sombreado exterior, para proteger del sol las zonas acristaladas.":
    "Construction of an external shading pergola, to protect glazed areas from the sun.",
"Aplicación de lámina de control solar sobre los vidrios, para reducir la ganancia térmica.":
    "Application of solar control film to the glazing, to reduce heat gain.",
"Colocación de cortina térmica interior, para mejorar el aislamiento del hueco.":
    "Installation of an internal thermal blind, to improve the insulation of the opening.",
"Motorización de persiana existente, con conexión eléctrica y programación. El motor lo elige el cliente.":
    "Motorization of an existing roller shutter, with electrical connection and programming. The motor is selected by the client.",
"Automatización de toldo con sensor solar, para accionamiento automático. El sistema lo elige el cliente.":
    "Automation of an awning with a sun sensor, for automatic operation. The system is selected by the client.",
"Ejecución de marquesina de sombreado sobre ventanas, para reducir la ganancia solar directa.":
    "Construction of a shading canopy over windows, to reduce direct solar gain.",
"Plantación de vegetación trepadora para sombreado de fachada, reduciendo la ganancia térmica. Las plantas las elige el cliente.":
    "Planting of climbing plants to shade the facade, reducing heat gain. The plants are selected by the client.",
"Aplicación de película reflectiva sobre cubierta, para reducir la ganancia de calor solar.":
    "Application of a reflective coating to the roof, to reduce solar heat gain.",

# ── Climatización y ventilación ───────────────────────────────────────────
"Sustitución de equipo de climatización por uno de alta eficiencia, con conexión y puesta en marcha. El equipo lo elige el cliente.":
    "Replacement of HVAC equipment with a high efficiency unit, including connection and commissioning. The unit is selected by the client.",
"Instalación de termostato programable, con conexión y programación. El termostato lo elige el cliente.":
    "Installation of a programmable thermostat, including connection and programming. The thermostat is selected by the client.",
"Limpieza y mantenimiento del sistema de climatización, con limpieza de filtros y serpentines.":
    "Cleaning and maintenance of the HVAC system, including cleaning of the filters and coils.",
"Aislamiento de los conductos de climatización, para evitar pérdidas de energía.":
    "Insulation of the HVAC ductwork, to prevent energy loss.",
"Instalación de sistema de ventilación mecánica controlada, con recuperador de calor. El equipo lo elige el cliente.":
    "Installation of a mechanical ventilation system with heat recovery. The unit is selected by the client.",
"Instalación de recuperador de calor en el sistema de ventilación. El equipo lo elige el cliente.":
    "Installation of a heat recovery unit in the ventilation system. The unit is selected by the client.",
"Sustitución de ductos de ventilación, para mejorar la eficiencia del sistema.":
    "Replacement of the ventilation ducts, to improve the efficiency of the system.",
"Instalación de rejillas de ventilación regulables, para aprovechar la ventilación natural.":
    "Installation of adjustable ventilation grilles, to make use of natural ventilation.",
"Zonificación del sistema de climatización, con compuertas motorizadas y control. El sistema lo elige el cliente.":
    "Zoning of the HVAC system, with motorized dampers and controls. The system is selected by the client.",
"Calibración y balanceo del sistema de climatización, para asegurar el rendimiento óptimo.":
    "Calibration and balancing of the HVAC system, to ensure optimum performance.",
"Sellado de las uniones de los conductos de climatización, para evitar fugas de aire.":
    "Sealing of the joints of the HVAC ductwork, to prevent air leakage.",

# ── Iluminación ───────────────────────────────────────────────────────────
"Sustitución de luminarias por LED de alta eficiencia, con conexión. La luminaria la elige el cliente.":
    "Replacement of light fixtures with high efficiency LED units, including connection. The fixture is selected by the client.",
"Instalación de luminaria LED con sensor de presencia, para ahorro en zonas de paso. La luminaria la elige el cliente.":
    "Installation of an LED light fixture with an occupancy sensor, to save energy in circulation areas. The fixture is selected by the client.",
"Colocación de tira LED de iluminación eficiente, con fuente y perfil. La tira la elige el cliente.":
    "Installation of an efficient LED strip light, with driver and profile. The strip is selected by the client.",
"Instalación de regulador (dimmer) de iluminación, para ajustar el consumo. El regulador lo elige el cliente.":
    "Installation of a lighting dimmer, to adjust consumption. The dimmer is selected by the client.",
"Instalación de sensor de nivel de luz, para regular la iluminación según la luz natural. El sensor lo elige el cliente.":
    "Installation of a daylight sensor, to regulate the lighting according to the natural light. The sensor is selected by the client.",
"Instalación de iluminación exterior LED con fotocélula, para ahorro. La luminaria la elige el cliente.":
    "Installation of LED external lighting with a photocell, to save energy. The fixture is selected by the client.",
"Sustitución de lámpara halógena por LED, con ajuste del portalámparas. La lámpara la elige el cliente.":
    "Replacement of a halogen lamp with LED, including adjustment of the lampholder. The lamp is selected by the client.",
"Instalación de sistema de control de iluminación por zonas, con pulsadores de escena. El sistema lo elige el cliente.":
    "Installation of a zoned lighting control system, with scene controllers. The system is selected by the client.",
"Instalación de luminaria de bajo consumo en áreas comunes. La luminaria la elige el cliente.":
    "Installation of a low energy light fixture in common areas. The fixture is selected by the client.",
"Verificación de la eficiencia del sistema de iluminación, con medición de consumos.":
    "Verification of the efficiency of the lighting system, by measurement of consumption.",
"Instalación de temporizador de iluminación de zonas comunes, para apagado automático. El temporizador lo elige el cliente.":
    "Installation of a time switch for lighting in common areas, for automatic switch-off. The time switch is selected by the client.",

# ── Energía renovable ─────────────────────────────────────────────────────
"Instalación de panel solar fotovoltaico, con estructura y conexión. El panel lo elige el cliente.":
    "Installation of a photovoltaic solar panel, with the support structure and connection. The panel is selected by the client.",
"Instalación de inversor para sistema fotovoltaico, con conexión eléctrica. El inversor lo elige el cliente.":
    "Installation of an inverter for a photovoltaic system, with the electrical connection. The inverter is selected by the client.",
"Instalación de banco de baterías para sistema fotovoltaico, con conexión. Las baterías las elige el cliente.":
    "Installation of a battery bank for a photovoltaic system, with connection. The batteries are selected by the client.",
"Instalación de sistema de agua caliente solar, con conexión hidráulica. El sistema lo elige el cliente.":
    "Installation of a solar water heating system, with the hydraulic connection. The system is selected by the client.",
"Ejecución de estructura soporte de paneles solares, con perfiles y fijación.":
    "Construction of the support structure for solar panels, with profiles and fixings.",
"Conexión del sistema fotovoltaico a la red, con protecciones y puesta en marcha.":
    "Connection of the photovoltaic system to the grid, with protective devices and commissioning.",
"Instalación de medidor bidireccional de energía, para la compensación de excedentes. El medidor lo elige el cliente.":
    "Installation of a bidirectional energy meter, for the settlement of exported energy. The meter is selected by the client.",
"Instalación de sistema de aerotermia para agua caliente. El equipo lo elige el cliente.":
    "Installation of an air source heat pump system for hot water. The unit is selected by the client.",
"Instalación de sistema de respaldo con baterías, para autoconsumo. El sistema lo elige el cliente.":
    "Installation of a battery backup system, for self-consumption. The system is selected by the client.",
"Instalación de sistema de monitorización de la producción fotovoltaica. El sistema lo elige el cliente.":
    "Installation of a monitoring system for photovoltaic generation. The system is selected by the client.",
"Mantenimiento del sistema fotovoltaico, con limpieza de paneles y revisión de conexiones.":
    "Maintenance of the photovoltaic system, including cleaning of the panels and checking of connections.",
"Ejecución de estructura de soporte de paneles solares sobre techo inclinado, con fijación a la cubierta y sellado de los pasos.":
    "Construction of the support structure for solar panels on a pitched roof, with fixing to the roof and sealing of the penetrations.",
}
