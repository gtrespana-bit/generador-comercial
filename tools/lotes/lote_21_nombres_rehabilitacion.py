# -*- coding: utf-8 -*-
"""Nombres de partida — Rehabilitación energética (capítulo completo, 100).

Criterios de este lote:
  · «Envolvente térmica» es thermal envelope y «puente térmico» es thermal
    bridge: los dos son términos consolidados, no descripciones.
  · «Insuflada» es blown y «proyectada» es sprayed: la celulosa se insufla
    y la lana mineral se proyecta, y en inglés son verbos distintos.
  · «Cubierta fría» es cold roof, la cubierta ventilada sobre el aislamiento.
  · «Cámara sanitaria» es crawl space.
  · «Burlete» es weatherstripping en Estados Unidos y draught seal en
    Reino Unido; «calafateado» es caulking.
  · «Aerotermia» es air source heat pump: no hay traducción literal, es el
    nombre del equipo.
  · «Ventilación mecánica controlada» y «recuperador de calor» son dos
    partidas distintas y aquí se mantienen separadas: el sistema y el equipo.
"""

LOTE = {
# ── Diagnóstico ───────────────────────────────────────────────────────────
"Evaluación energética de la vivienda.": "Energy assessment of a dwelling.",
"Diagnóstico de puentes térmicos.": "Diagnosis of thermal bridges.",
"Auditoría de consumos energéticos.": "Audit of energy consumption.",
"Medición de infiltraciones de aire.": "Measurement of air infiltration.",
"Informe de certificación energética.":
    "Energy performance certificate report.",
"Estudio de viabilidad de energías renovables.":
    "Feasibility study for renewable energy.",
"Medición de espesores de aislamiento existente.":
    "Measurement of the thickness of existing insulation.",
"Inspección de carpintería y vidrios.":
    "Inspection of carpentry and glazing.",
"Levantamiento de la envolvente térmica.":
    "Survey of the thermal envelope.",
"Propuesta de medidas de rehabilitación energética.":
    "Proposal of energy retrofit measures.",
"Seguimiento y medición de ahorro energético.":
    "Monitoring and measurement of energy savings.",

# ── Fachada ───────────────────────────────────────────────────────────────
"Aislamiento de fachada con poliestireno extruido.":
    "Facade insulation with extruded polystyrene.",
"Aislamiento de fachada con lana de roca.":
    "Facade insulation with rock wool.",
"SATE de fachada con poliestireno expandido.":
    "EIFS on a facade with expanded polystyrene.",
"Fachada ventilada con subestructura y aislamiento.":
    "Ventilated facade with a substructure and insulation.",
"Revestimiento de fachada con panel composite.":
    "Facade cladding with sandwich panels.",
"Aislamiento de fachada con lana mineral proyectada.":
    "Facade insulation with sprayed mineral wool.",
"Inyección de aislamiento en cámara de fachada.":
    "Injection of insulation into a facade cavity.",
"Refuerzo de aislamiento en petos y cantos.":
    "Additional insulation at parapets and slab edges.",
"Remate de aislamiento en esquinas y juntas.":
    "Finishing of insulation at corners and joints.",
"Tratamiento de puentes térmicos de fachada.":
    "Treatment of thermal bridges in a facade.",
"Acabado de fachada aislada con mortero.":
    "Stuccoed finish to an insulated facade.",

# ── Cubierta y techo ──────────────────────────────────────────────────────
"Aislamiento de techo con poliestireno extruido.":
    "Roof insulation with extruded polystyrene.",
"Aislamiento de techo con lana de roca.":
    "Roof insulation with rock wool.",
"Aislamiento de cubierta con manta reflectiva.":
    "Roof deck insulation with a reflective membrane.",
"Aislamiento de cubierta plana con lana mineral.":
    "Flat roof insulation with mineral wool.",
"Aislamiento de techo entre viguetas.":
    "Insulation of a roof between joists.",
"Barrera de vapor en cubierta.": "Vapor barrier in a roof.",
"Aislamiento de techo con celulosa insuflada.":
    "Roof insulation with blown cellulose.",
"Refuerzo de aislamiento en cumbrera.": "Additional insulation at the ridge.",
"Aislamiento de lucernario o claraboya.":
    "Insulation of a skylight.",
"Cubierta fría con aislamiento y ventilación.":
    "Cold roof with insulation and ventilation.",
"Aislamiento de techo de entrepiso no acondicionado.":
    "Insulation of the roof over an unconditioned intermediate floor.",

# ── Piso ──────────────────────────────────────────────────────────────────
"Aislamiento de piso con poliestireno.":
    "Floor insulation with polystyrene.",
"Aislamiento de piso con manta reflectiva.":
    "Floor insulation with a reflective membrane.",
"Aislamiento perimetral de piso.": "Perimeter insulation to a floor.",
"Aislamiento de entrepiso entre viviendas.":
    "Insulation of an intermediate floor between dwellings.",
"Aislamiento de piso sobre cámara sanitaria.":
    "Insulation of a floor over a crawl space.",
"Aislamiento de piso de ático.": "Insulation of an attic floor.",
"Banda perimetral en encuentro piso-muro.":
    "Perimeter strip at the floor and wall junction.",
"Aislamiento de piso con panel rígido de lana.":
    "Floor insulation with rigid mineral wool board.",
"Tratamiento de puente térmico en canto de losa.":
    "Treatment of the thermal bridge at a slab edge.",
"Aislamiento de piso de garaje.": "Insulation of a garage floor.",
"Regularización con mortero aislante.": "Leveling with insulating mortar.",

# ── Huecos ────────────────────────────────────────────────────────────────
"Sustitución de ventana por doble acristalamiento.":
    "Replacement of a window with double glazing.",
"Sustitución de ventana por vidrio templado.":
    "Replacement of a window with tempered glass.",
"Sustitución de ventana por vidrio de control solar.":
    "Replacement of a window with solar control glass.",
"Sustitución de ventana con marco aislante.":
    "Replacement of a window with a thermally broken frame.",
"Sellado perimetral de ventanas.": "Perimeter sealing of windows.",
"Sustitución de junta de estanqueidad de ventana.":
    "Replacement of a window weather seal.",
"Calafateado de carpintería exterior.":
    "Caulking of exterior carpentry.",
"Persiana aislante con cajón estanco.":
    "Insulated roller shutter with a sealed box.",
"Sustitución de puerta exterior con aislamiento.":
    "Replacement of an exterior door with an insulated door.",
"Burlete de estanqueidad en puertas.":
    "Weatherstripping to doors.",
"Ventana de doble acristalamiento con gas argón.":
    "Argon-filled double glazed window.",

# ── Protección solar ──────────────────────────────────────────────────────
"Toldo exterior de protección solar.": "Exterior solar protection awning.",
"Persiana enrollable de aluminio para control solar.":
    "Aluminum roller shutter for solar control.",
"Celosía o romanilla de sombreado.": "Shading louver or grille.",
"Pérgola de sombreado exterior.": "Exterior shading pergola.",
"Lámina de control solar en vidrios.":
    "Solar control film on glazing.",
"Cortina térmica interior.": "Interior thermal curtain.",
"Motorización de persiana existente.":
    "Motorization of an existing roller shutter.",
"Automatización de toldo con sensor solar.":
    "Automation of an awning with a solar sensor.",
"Marquesina de sombreado.": "Shading canopy.",
"Vegetación de sombreado de fachada.": "Shading planting on a facade.",
"Película reflectiva en cubierta.": "Reflective film on a roof deck.",

# ── Climatización y ventilación ───────────────────────────────────────────
"Sustitución de equipo de climatización eficiente.":
    "Replacement with high-efficiency HVAC equipment.",
"Termostato programable.": "Programmable thermostat.",
"Limpieza y mantenimiento de climatización.":
    "Cleaning and maintenance of the HVAC system.",
"Aislamiento de conductos de climatización.":
    "Insulation of HVAC ducts.",
"Ventilación mecánica controlada.":
    "Controlled mechanical ventilation system.",
"Recuperador de calor.": "Heat recovery unit.",
"Sustitución de ductos de ventilación.":
    "Replacement of ventilation ducts.",
"Ventilación natural con rejillas regulables.":
    "Natural ventilation with adjustable grilles.",
"Zonificación del sistema de climatización.":
    "Zoning of the HVAC system.",
"Calibración y balanceo del sistema.":
    "Calibration and balancing of the system.",
"Sellado de conductos de climatización.":
    "Sealing of HVAC ducts.",

# ── Iluminación ───────────────────────────────────────────────────────────
"Sustitución de luminarias por LED.":
    "Replacement of light fixtures with LED.",
"Iluminación LED con sensor de presencia.":
    "LED lighting with an occupancy sensor.",
"Tira LED de iluminación eficiente.": "Efficient LED strip lighting.",
"Regulación de iluminación con dimmer.":
    "Lighting control with a dimmer.",
"Sensor de luz natural para iluminación.":
    "Daylight sensor for lighting.",
"Iluminación exterior LED con fotocélula.":
    "Exterior LED lighting with a photocell.",
"Sustitución de lámparas halógenas por LED.":
    "Replacement of halogen lamps with LED.",
"Sistema de control de iluminación por zonas.":
    "Zoned lighting control system.",
"Iluminación de bajo consumo en áreas comunes.":
    "Low-energy lighting in common areas.",
"Verificación de eficiencia de iluminación.":
    "Verification of lighting efficiency.",
"Temporizador de iluminación de zonas comunes.":
    "Timer for lighting in common areas.",

# ── Energía renovable ─────────────────────────────────────────────────────
"Instalación de panel solar fotovoltaico.":
    "Installation of photovoltaic solar panels.",
"Instalación de inversor fotovoltaico.":
    "Installation of a photovoltaic inverter.",
"Instalación de banco de baterías para fotovoltaica.":
    "Installation of a battery bank for a photovoltaic system.",
"Sistema de agua caliente solar.": "Solar water heating system.",
"Estructura soporte de paneles solares.":
    "Support structure for solar panels.",
"Conexión de sistema fotovoltaico a red.":
    "Connection of a photovoltaic system to the grid.",
"Medidor bidireccional de energía.": "Bidirectional energy meter.",
"Aerotermia para agua caliente.":
    "Air source heat pump for domestic hot water.",
"Generación de respaldo con baterías.":
    "Battery backup generation.",
"Monitorización de producción fotovoltaica.":
    "Monitoring of photovoltaic output.",
"Mantenimiento de sistema fotovoltaico.":
    "Maintenance of a photovoltaic system.",
"Estructura de paneles solares sobre techo inclinado.":
    "Support structure for solar panels on a pitched roof.",
}
