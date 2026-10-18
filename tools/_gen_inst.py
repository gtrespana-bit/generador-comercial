"""Generador del bloque formulaico de descripciones de Instalaciones.

Las 264 cadenas que acaban en «Medido por unidad instalada.» comparten un
puñado de colas fijas en español; sólo cambia la cabeza. Se traduce la cabeza
con un diccionario y se le cose la cola ya traducida.

No escribir claves a mano: las cadenas se leen de tools/_pend_inst.json.
"""
import json
import pathlib

RAIZ = pathlib.Path(__file__).resolve().parent.parent

COLAS = [
    (", con conexión y configuración. Incluye la conexión y la configuración.",
     ", with the connection and configuration. Includes the connection and configuration."),
    (", con conexión y configuración. Incluye la conexión.",
     ", with the connection and configuration. Includes the connection."),
    (", con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha.",
     ", with the connection and setting to work. Includes the connection and setting to work."),
    (", con conexión y puesta en marcha. Incluye la conexión.",
     ", with the connection and setting to work. Includes the connection."),
    (", con montaje y puesta en marcha. Incluye el montaje.",
     ", with assembly and setting to work. Includes the assembly."),
    (", con fijación y señalización. Incluye la fijación y la señalización.",
     ", with fixing and signage. Includes the fixing and signage."),
    (", con fijación y señalización. Incluye la fijación.",
     ", with fixing and signage. Includes the fixing."),
    (", con conexión. Incluye la conexión y la puesta en marcha.",
     ", with the connection. Includes the connection and setting to work."),
    (", con conexión. Incluye la conexión y la fijación.",
     ", with the connection. Includes the connection and fixing."),
    (", con conexión. Incluye la conexión.",
     ", with the connection. Includes the connection."),
    (". Incluye el montaje y la puesta en marcha.",
     ". Includes the assembly and setting to work."),
    (". Incluye la conexión y la fijación.",
     ". Includes the connection and fixing."),
    (". Incluye el montaje del riel y la silla.",
     ". Includes the assembly of the rail and the seat."),
    (". Incluye el montaje del riel y la plataforma.",
     ". Includes the assembly of the rail and the platform."),
]
# El catálogo trae la cabeza con punto («citófono., con conexión…») o sin él
# («equipo de climatización, con conexión…»): se prueban las dos formas.
COLAS = sum([[(c[0], c[1]), ("." + c[0], c[1])] for c in COLAS], [])
COLAS.sort(key=lambda c: -len(c[0]))

CABEZA_ES = "Instalación de "
PIE_ES = "Medido por unidad instalada."
PIE_EN = " Measured per unit installed."

CABEZAS = {
    # ── domótica, seguridad y comunicaciones ────────────────────────────────
    "actuador de calefacción": "heating actuator",
    "actuador de riego": "irrigation actuator",
    "alarma con sensores": "alarm system with sensors",
    "alarma de incendio": "fire alarm",
    "alarma interior": "internal alarm",
    "alarma perimetral": "perimeter alarm",
    "altavoces": "loudspeakers",
    "amplificador": "amplifier",
    "antena": "antenna",
    "central de incendios": "fire alarm control panel",
    "central domótica con control remoto": "home automation controller with remote control",
    "cine en casa": "home cinema system",
    "citófono": "door entry phone",
    "control de acceso biométrico": "biometric access control",
    "control de acceso": "access control system",
    "cámara con grabador": "camera with a recorder",
    "cámara de comercio": "camera for commercial premises",
    "cámara de entrada": "camera at the entrance",
    "cámara de garaje": "garage camera",
    "cámara de jardín": "garden camera",
    "cámara de local": "camera for premises",
    "cámara de seguridad": "security camera",
    "cámara de terraza": "terrace camera",
    "cámara exterior": "external camera",
    "cámara interior": "internal camera",
    "detector combinado": "combined detector",
    "detector de calor": "heat detector",
    "detector de humo": "smoke detector",
    "detectores en cocina": "detectors in a kitchen",
    "detectores en depósito": "detectors in a store",
    "detectores en dormitorio": "detectors in a bedroom",
    "detectores en escalera": "detectors in a stairwell",
    "detectores en garaje": "detectors in a garage",
    "detectores en pasillo": "detectors in a corridor",
    "detectores en sala": "detectors in a living room",
    "grabador de video": "video recorder",
    "intercomunicación general": "general intercom system",
    "intercomunicador de edificio": "building intercom",
    "intercomunicador de puerta": "door intercom",
    "intercomunicador": "intercom",
    "lector de tarjetas": "card reader",
    "monitor de vigilancia": "surveillance monitor",
    "módulo de control de bomba": "pump control module",
    "panel de alarma": "alarm panel",
    "panel de control táctil": "touch control panel",
    "panel de control": "control panel",
    "pantalla de proyección": "projection screen",
    "portero con video": "video door entry system",
    "portero eléctrico": "electric door release",
    "proyector": "projector",
    "pulsador de alarma": "alarm call point",
    "pulsador de escena inalámbrico": "wireless scene controller",
    "receptor de tv": "television receiver",
    "receptor satelital": "satellite receiver",
    "repetidor de señal cableada": "wired signal repeater",
    "sensor de calidad de aire": "air quality sensor",
    "sensor de consumo eléctrico": "electricity consumption sensor",
    "sensor de movimiento": "motion sensor",
    "sensor de presencia": "occupancy sensor",
    "sensor de puerta y ventana": "door and window sensor",
    "sensor de puerta": "door sensor",
    "sensor de ventana": "window sensor",
    "sirena de alarma": "alarm siren",
    "sirena exterior": "external siren",
    "sirena": "siren",
    "sistema cctv": "CCTV system",
    "sistema de acceso": "access control system",
    "sistema de alarma": "alarm system",
    "sistema de audio multizona": "multi-zone audio system",
    "sistema de audio": "audio system",
    "sistema de cine": "home cinema system",
    "sistema de intercomunicación": "intercom system",
    "sistema de música": "music system",
    "sistema de video": "video system",
    "sonido ambiente": "ambient sound system",
    "sonido de ambiente": "ambient sound system",
    "sonido de dormitorio": "bedroom sound system",
    "sonido de jardín": "garden sound system",
    "sonido de sala": "living room sound system",
    "sonido de terraza": "terrace sound system",
    "teclado de acceso": "access keypad",
    "teatro en casa": "home theatre system",
    "termostato inalámbrico": "wireless thermostat",
    "videoportero con cámara": "video door entry system with a camera",
    "videoportero con monitor": "video door entry system with a monitor",
    "videoportero inalámbrico": "wireless video door entry system",

    # ── climatización ───────────────────────────────────────────────────────
    "equipo cassette": "cassette air conditioning unit",
    "equipo de climatización": "air conditioning unit",
    "equipo de confort": "comfort air conditioning unit",
    "equipo de piso-techo": "floor and ceiling air conditioning unit",
    "equipo de piso": "floor mounted air conditioning unit",
    "equipo de precisión": "precision air conditioning unit",
    "equipo de techo": "ceiling mounted air conditioning unit",
    "equipo de ventana": "window air conditioning unit",
    "equipo multisplit": "multi-split air conditioning system",
    "equipo para comercio": "air conditioning unit for commercial premises",
    "equipo para consultorio": "air conditioning unit for a surgery",
    "equipo para depósito": "air conditioning unit for a store",
    "equipo para dormitorio": "air conditioning unit for a bedroom",
    "equipo para estudio": "air conditioning unit for a study",
    "equipo para garaje": "air conditioning unit for a garage",
    "equipo para habitación": "air conditioning unit for a room",
    "equipo para local": "air conditioning unit for premises",
    "equipo para oficina": "air conditioning unit for an office",
    "equipo para restaurante": "air conditioning unit for a restaurant",
    "equipo para sala": "air conditioning unit for a living room",
    "equipo para terraza": "air conditioning unit for a terrace",
    "equipo split de pared": "wall mounted split air conditioning unit",
    "equipo split inverter": "inverter split air conditioning unit",
    "refrigerante": "refrigerant",
    "rejilla de retorno": "return air grille",
    "rejilla de suministro": "supply air grille",
    "sistema de conductos": "ducted air conditioning system",
    "termostato": "thermostat",
    "unidad condensadora": "condensing unit",
    "unidad interior": "indoor unit",

    # ── ventilación ─────────────────────────────────────────────────────────
    "campana extractora": "range hood",
    "difusor": "diffuser",
    "ducto flexible": "flexible duct",
    "ducto rígido": "rigid duct",
    "extractor de baño": "bathroom extractor fan",
    "extractor de campana": "range hood extractor fan",
    "extractor de cocina": "kitchen extractor fan",
    "rejilla de extracción": "extract grille",
    "rejilla de ventilación": "ventilation grille",
    "ventilación de baño": "bathroom ventilation",
    "ventilación de closet": "closet ventilation",
    "ventilación de cocina": "kitchen ventilation",
    "ventilación de comedor": "dining room ventilation",
    "ventilación de comercio": "ventilation for commercial premises",
    "ventilación de cuarto técnico": "ventilation for a plant room",
    "ventilación de depósito": "ventilation for a store",
    "ventilación de dormitorio": "bedroom ventilation",
    "ventilación de estudio": "study ventilation",
    "ventilación de garaje": "garage ventilation",
    "ventilación de lavandería": "laundry room ventilation",
    "ventilación de local": "ventilation for premises",
    "ventilación de oficina": "office ventilation",
    "ventilación de sala": "living room ventilation",
    "ventilación de sótano": "basement ventilation",
    "ventilación de terraza": "terrace ventilation",
    "ventilador de baño con sensor": "bathroom fan with a sensor",
    "ventilador de pared": "wall fan",
    "ventilador de piso": "pedestal fan",
    "ventilador de techo": "ceiling fan",

    # ── protección contra incendios ─────────────────────────────────────────
    "extintor de co2": "CO2 fire extinguisher",
    "extintor de espuma": "foam fire extinguisher",
    "extintor de polvo": "dry powder fire extinguisher",
    "extintor en cocina": "fire extinguisher in a kitchen",
    "extintor en comercio": "fire extinguisher in commercial premises",
    "extintor en depósito": "fire extinguisher in a store",
    "extintor en garaje": "fire extinguisher in a garage",
    "extintor en local": "fire extinguisher in premises",
    "extintor en oficina": "fire extinguisher in an office",
    "extintor en terraza": "fire extinguisher on a terrace",
    "gabinete de manguera": "hose reel cabinet",
    "hidrante": "hydrant",
    "luminaria de emergencia con señalización": "emergency light fixture with signage",
    "luz de emergencia": "emergency light",
    "rociador": "sprinkler head",
    "señal de salida": "exit sign",
    "señalización de evacuación": "escape route signage",

    # ── bombeo y tanques ────────────────────────────────────────────────────
    "banco de baterías": "battery bank",
    "batería de 200ah": "200 Ah battery",
    "batería de litio": "lithium battery",
    "batería de plomo": "lead-acid battery",
    "batería": "battery",
    "bomba centrífuga": "centrifugal pump",
    "bomba contra incendios": "fire pump",
    "bomba de achique": "sump pump",
    "bomba de agua potable": "potable water pump",
    "bomba de agua residual": "sewage pump",
    "bomba de agua": "water pump",
    "bomba de piscina": "pool pump",
    "bomba de pozo": "well pump",
    "bomba de recirculación": "recirculation pump",
    "bomba de riego": "irrigation pump",
    "bomba de superficie": "surface pump",
    "bomba presurizadora": "booster pump",
    "bomba sumergible": "submersible pump",
    "sistema de bombeo": "pumping system",
    "sistema hidroneumático": "hydropneumatic system",
    "tanque cisterna": "cistern",
    "tanque de agua caliente": "hot water tank",
    "tanque de agua elevado": "elevated water tank",
    "tanque de agua enterrado": "buried water tank",
    "tanque de agua potable": "potable water tank",
    "tanque de presión hidroneumático": "hydropneumatic pressure tank",
    "tanque de presión": "pressure tank",
    "tanque de reserva": "reserve tank",
    "tanque de tormenta": "stormwater tank",
    "tanque elevado": "elevated tank",
    "tanque enterrado": "buried tank",
    "tanque séptico": "septic tank",
    "válvula de flotante": "float valve",

    # ── energía solar y respaldo ────────────────────────────────────────────
    "cableado solar": "solar cabling",
    "estructura de paneles": "panel support structure",
    "inversor aislado": "off-grid inverter",
    "inversor de 3kw": "3 kW inverter",
    "inversor de red": "grid-tie inverter",
    "inversor híbrido": "hybrid inverter",
    "inversor": "inverter",
    "medidor bidireccional": "bidirectional energy meter",
    "panel solar comercial": "commercial solar panel",
    "panel solar de 400w": "400 W solar panel",
    "panel solar doméstico": "domestic solar panel",
    "panel solar en jardín": "solar panel in a garden",
    "panel solar en techo": "roof mounted solar panel",
    "panel solar en terraza": "solar panel on a terrace",
    "panel solar": "solar panel",
    "planta de respaldo": "backup generator",
    "planta eléctrica a gas": "gas fired generator",
    "planta eléctrica diésel": "diesel generator",
    "planta eléctrica": "generator",
    "protecciones solares": "solar system protective devices",
    "regulador de carga": "charge controller",
    "sistema de respaldo": "backup power system",
    "sistema fotovoltaico": "photovoltaic system",
    "sistema solar": "solar system",
    "tablero de transferencia": "transfer switch",

    # ── transporte vertical ─────────────────────────────────────────────────
    "ascensor de 3 paradas": "three-stop elevator",
    "ascensor de 4 paradas": "four-stop elevator",
    "ascensor de 5 paradas": "five-stop elevator",
    "ascensor de 6 paradas": "six-stop elevator",
    "ascensor de alta velocidad": "high-speed elevator",
    "ascensor de carga pesada": "heavy-duty freight elevator",
    "ascensor de carga": "freight elevator",
    "ascensor de dos paradas, con estructura y cabina": "two-stop elevator, with the structure and the car",
    "ascensor de tracción con cuarto de máquinas": "traction elevator with a machine room",
    "ascensor existente": "existing elevator",
    "ascensor panorámico con estructura de vidrio": "panoramic elevator with a glass structure",
    "ascensor para discapacitados": "accessible elevator",
    "ascensor sin cuarto de máquinas": "machine-room-less elevator",
    "ascensor unifamiliar, con estructura, cabina y control": "home elevator, with the structure, the car and the controller",
    "elevador de fachada para accesibilidad": "facade platform lift for accessibility",
    "elevador de plataforma para accesibilidad": "platform lift for accessibility",
    "elevador de silla": "chair lift",
    "montacargas de carga": "freight elevator",
    "montacargas de cocina o servicio": "service lift for a kitchen or for service",
    "montacargas de obra o de servicio": "construction or service hoist",
    "plataforma elevadora vertical para accesibilidad": "vertical platform lift for accessibility",
    "plataforma salvaescaleras": "platform stairlift",
    "rampa mecánica": "moving ramp",
    "salvaescaleras de plataforma": "platform stairlift",
    "salvaescaleras para accesibilidad": "stairlift for accessibility",
    "silla salvaescaleras": "stairlift",
}

# El plural no lleva artículo: «Instalación de altavoces» → «Installation of loudspeakers».
SIN_ARTICULO = {"altavoces", "detectores en cocina", "detectores en depósito", "detectores en dormitorio",
                "detectores en escalera", "detectores en garaje", "detectores en pasillo",
                "detectores en sala", "protecciones solares", "refrigerante"}


# ── segundo bloque formulaico ───────────────────────────────────────────────
# «Ejecución de <cabeza>., con <trabajo>. <cola>»
CABEZA2_ES = "Ejecución de "

TRABAJOS = {
    ", con conexión y prueba.": ", with the connection and the tightness test.",
    ", con conexión.": ", with the connection.",
    ", con verificación.": ", with the verification.",
    ", con canalización y conexión.": ", with the containment and the connection.",
}

COLAS2 = {
    "Incluye la conexión y la prueba de estanqueidad. Medido por unidad ejecutado/a.":
        "Includes the connection and the tightness test. Measured per unit completed.",
    "Incluye la conexión y la prueba de estanqueidad. Medido por metro lineal ejecutado/a.":
        "Includes the connection and the tightness test. Measured per linear meter completed.",
    "Incluye la conexión y la fijación. Medido por unidad ejecutada.":
        "Includes the connection and the fixing. Measured per unit completed.",
    "Incluye la verificación y el ajuste. Medido por unidad ejecutada.":
        "Includes the verification and the adjustment. Measured per unit completed.",
    "Incluye el tendido del cable y la conexión. Medido por punto ejecutado.":
        "Includes running the cable and making the connection. Measured per point completed.",
    "Incluye el tendido y la conexión. Medido por punto ejecutado.":
        "Includes running the cable and making the connection. Measured per point completed.",
    "Incluye la conexión. Medido por unidad ejecutado/a.":
        "Includes the connection. Measured per unit completed.",
    "Incluye la conexión. Medido por metro lineal ejecutado/a.":
        "Includes the connection. Measured per linear meter completed.",
}

CABEZAS2 = {
    # ── gas ─────────────────────────────────────────────────────────────────
    "tubería de gas de cobre": "copper gas piping",
    "tubería de gas de acero": "steel gas piping",
    "punto de gas para estufa": "gas outlet for a cooker",
    "punto de gas para horno": "gas outlet for an oven",
    "punto de gas para calentador": "gas outlet for a water heater",
    "punto de gas para secadora": "gas outlet for a clothes dryer",
    "instalación de regulador de gas": "gas pressure regulator",
    "instalación de medidor de gas": "gas meter",
    "instalación de llave de corte de gas": "gas shut off valve",
    "instalación de detector de gas": "gas detector",
    "instalación de válvula de seguridad": "safety valve",
    "tubería de gas de montante": "gas riser",
    "punto de gas para cocina": "gas outlet for a kitchen",
    "punto de gas para lavandería": "gas outlet for a laundry room",
    "punto de gas para terraza": "gas outlet for a terrace",
    "punto de gas para parrillera": "gas outlet for a barbecue",
    "tubería de gas empotrada": "concealed gas piping",
    "tubería de gas vista": "surface mounted gas piping",
    "acometida de gas": "gas service connection",
    "instalación de gabinete de gas": "gas meter cabinet",
    "prueba de estanqueidad de gas": "gas tightness test",
    "instalación de válvula de exceso de flujo": "excess flow valve",
    "instalación de regulador de alta presión": "high pressure regulator",
    "instalación de regulador de baja presión": "low pressure regulator",
    "tubería de gas flexible": "flexible gas connector",
    "punto de gas para secadora de ropa": "gas outlet for a clothes dryer",
    "punto de gas para calentador de paso": "gas outlet for an instantaneous water heater",
    "tubería de gas de polietileno": "polyethylene gas piping",
    "punto de gas para cocina industrial": "gas outlet for a commercial kitchen",
    "instalación de válvula de gas": "gas valve",

    # ── protección contra rayos ─────────────────────────────────────────────
    "captación de pararrayos en chimenea": "lightning protection air terminal on a chimney",
    "captación de pararrayos en antena": "lightning protection air terminal on an antenna",
    "malla captadora en fachada": "air termination mesh on a facade",
    "captación de pararrayos en cumbrera": "lightning protection air terminal on a ridge",
    "bajante de cobre aislada": "insulated copper down conductor",
    "bajante de aluminio": "aluminum down conductor",
    "toma de tierra de pararrayos": "lightning protection earth electrode",
    "bajante con unión de comprobación": "down conductor with a test joint",
    "toma de tierra en anillo": "ring earth electrode",
    "protector de sobretensión combinado": "combined surge protective device",
    "protector de sobretensión de red": "surge protective device for the mains supply",
    "protector de sobretensión de teléfono": "surge protective device for the telephone line",
    "protector de sobretensión de antena": "surge protective device for the antenna",
    "protector de sobretensión de datos": "surge protective device for the data line",

    # ── puestas en marcha, pruebas y reparaciones ───────────────────────────
    "puesta en marcha de sistema de ventilación": "commissioning of the ventilation system",
    "puesta en marcha de sistema de gas": "commissioning of the gas system",
    "puesta en marcha de sistema de alarma": "commissioning of the alarm system",
    "puesta en marcha de sistema de acceso": "commissioning of the access control system",
    "prueba de presión de gas": "gas pressure test",
    "prueba de aislamiento eléctrico": "electrical insulation resistance test",
    "reparación de bomba de agua": "repair of a water pump",
    "reparación de tanque de agua": "repair of a water tank",
    "reparación de panel solar": "repair of a solar panel",
    "reparación de inversor": "repair of an inverter",
    "reparación de ventilador": "repair of a fan",
    "reparación de extractor": "repair of an extractor fan",

    # ── red de datos ────────────────────────────────────────────────────────
    "rack de telecomunicaciones": "telecommunications rack",
    "patch panel de red": "network patch panel",
    "canalización de datos": "data cabling containment",
    "punto de datos para repetidor": "data outlet for a repeater",
    "punto de datos para acceso": "data outlet for an access point",
    "punto de datos para oficina": "data outlet for an office",
}

# Las cabezas del bloque 2 nombren o no un sistema, van sin artículo cuando son
# nombres en plural o incontable: «Ejecución de tubería de gas de cobre».
SIN_ARTICULO2 = {
    "tubería de gas de cobre", "tubería de gas de acero", "tubería de gas empotrada",
    "tubería de gas vista", "tubería de gas flexible", "tubería de gas de polietileno",
    "malla captadora en fachada", "canalización de datos",
}

# Estas cabezas ya nombran la operación: no les pega «Installation of».
SIN_INSTALACION = {
    "puesta en marcha de sistema de ventilación", "puesta en marcha de sistema de gas",
    "puesta en marcha de sistema de alarma", "puesta en marcha de sistema de acceso",
    "prueba de presión de gas", "prueba de aislamiento eléctrico",
    "prueba de estanqueidad de gas",
    "reparación de bomba de agua", "reparación de tanque de agua", "reparación de panel solar",
    "reparación de inversor", "reparación de ventilador", "reparación de extractor",
}


def generar():
    pendientes = json.loads((RAIZ / "tools/_pend_inst.json").read_text(encoding="utf-8"))
    lote, raras = {}, []
    art = {}
    for cabeza, en in CABEZAS.items():
        art[cabeza] = en if cabeza in SIN_ARTICULO else _articulo(en)

    for original in pendientes:
        if original.startswith(CABEZA2_ES):
            en = _bloque2(original)
            if en:
                lote[original] = en
            else:
                raras.append(original)
            continue
        if not original.startswith(CABEZA_ES) or not original.endswith(PIE_ES):
            raras.append(original)
            continue
        cuerpo = original[len(CABEZA_ES):-len(PIE_ES)].rstrip()
        for cola_es, cola_en in COLAS:
            if cuerpo.endswith(cola_es):
                cabeza = cuerpo[:-len(cola_es)]
                if cabeza in CABEZAS:
                    lote[original] = f"Installation of {art[cabeza]}{cola_en}{PIE_EN}"
                else:
                    raras.append(original)
                break
        else:
            raras.append(original)
    return lote, raras


def _bloque2(original):
    """«Ejecución de X., con Y. Incluye Z. Medido por …»"""
    resto = original[len(CABEZA2_ES):]
    if " Incluye " not in resto:
        return None
    cabeza_trabajo, cola_es = resto.split(" Incluye ", 1)
    cola_es = "Incluye " + cola_es
    if cola_es not in COLAS2:
        return None
    trabajo_es = None
    for t in TRABAJOS:
        if cabeza_trabajo.endswith(t):
            trabajo_es = t
            break
    if trabajo_es is None:
        return None
    # el catálogo escribe «tubería de gas de cobre., con …»: fuera el punto
    cabeza = cabeza_trabajo[:-len(trabajo_es)].rstrip().rstrip(".")
    if cabeza not in CABEZAS2:
        return None
    en = CABEZAS2[cabeza]
    if cabeza in SIN_INSTALACION:
        return f"{en[0].upper() + en[1:]}{TRABAJOS[trabajo_es]} {COLAS2[cola_es]}"
    if cabeza not in SIN_ARTICULO2:
        en = _articulo(en)
    return f"Installation of {en}{TRABAJOS[trabajo_es]} {COLAS2[cola_es]}"


def _articulo(en):
    return ("an " + en) if en[0] in "aeiouAEIOU" or (en[0].isdigit() and _empieza_por_numero(en)) else ("a " + en)


def _empieza_por_numero(en):
    # «3 kW inverter» se lee «three kW» → a; «200 Ah» se lee «two hundred» → a;
    # «8 in» sería an. Sólo hay 3 kW y 200 Ah en el catálogo, ambos con «a».
    return False


if __name__ == "__main__":
    lote, raras = generar()
    (RAIZ / "tools/_gen_inst.json").write_text(
        json.dumps(lote, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"generadas: {len(lote)}   raras (traducción aparte): {len(raras)}")
    for r in raras:
        print("   -", r[:120])
