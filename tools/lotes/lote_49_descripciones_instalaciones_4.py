# -*- coding: utf-8 -*-
"""Descripciones — Instalaciones (4 de 6): bloque formulaico.

311 cadenas que el catálogo genera combinando unas pocas colas fijas con
una cabeza que nombra el aparato. La cola se traduce una vez y la cabeza
se resuelve con un diccionario, así que lo que cambia de una partida a
otra es sólo el término del oficio.

Criterios de vocabulario aplicados en este bloque:

· «Puesta en marcha» es commissioning; «puesta a tierra» es grounding
  (GB earthing) y el electrode es el electrodo, no la varilla.
· En protección contra rayos se sigue la IEC 62305: air terminal es el
  captador, down conductor la bajante, air termination mesh la malla y
  earth electrode la toma de tierra.
· En gas, «prueba de estanqueidad» es tightness test, «llave de corte»
  es shut-off valve y «acometida» es service connection.
· «Pararrayos» con dispositivo de cebado se traduce como lightning
  conductor, no como lightning rod: la primera es la instalación, la
  segunda es la punta.
· Antena es antenna en inglés americano; antenna es la forma británica y
  la pone la variante.
"""

LOTE = {
    'Ejecución de acometida de gas., con conexión y prueba. Incluye la conexión y la prueba de estanqueidad. Medido por metro lineal ejecutado/a.':
        'Installation of a gas service connection, with the connection and the tightness test. Includes the connection and the tightness test. Measured per linear meter completed.',
    'Ejecución de bajante con unión de comprobación., con conexión. Incluye la conexión y la fijación. Medido por unidad ejecutada.':
        'Installation of a down conductor with a test joint, with the connection. Includes the connection and the fastening. Measured per unit completed.',
    'Ejecución de bajante de aluminio., con conexión. Incluye la conexión y la fijación. Medido por unidad ejecutada.':
        'Installation of an aluminum down conductor, with the connection. Includes the connection and the fastening. Measured per unit completed.',
    'Ejecución de bajante de cobre aislada., con conexión. Incluye la conexión y la fijación. Medido por unidad ejecutada.':
        'Installation of an insulated copper down conductor, with the connection. Includes the connection and the fastening. Measured per unit completed.',
    'Ejecución de canalización de datos., con canalización y conexión. Incluye el tendido del cable y la conexión. Medido por punto ejecutado.':
        'Installation of data cabling containment, with the containment and the connection. Includes running the cable and making the connection. Measured per point completed.',
    'Ejecución de captación de pararrayos en antena., con conexión. Incluye la conexión y la fijación. Medido por unidad ejecutada.':
        'Installation of a lightning protection air terminal on an antenna, with the connection. Includes the connection and the fastening. Measured per unit completed.',
    'Ejecución de captación de pararrayos en chimenea., con conexión. Incluye la conexión y la fijación. Medido por unidad ejecutada.':
        'Installation of a lightning protection air terminal on a chimney, with the connection. Includes the connection and the fastening. Measured per unit completed.',
    'Ejecución de captación de pararrayos en cumbrera., con conexión. Incluye la conexión y la fijación. Medido por unidad ejecutada.':
        'Installation of a lightning protection air terminal on a ridge, with the connection. Includes the connection and the fastening. Measured per unit completed.',
    'Ejecución de instalación de detector de gas., con conexión y prueba. Incluye la conexión y la prueba de estanqueidad. Medido por unidad ejecutado/a.':
        'Installation of a gas detector, with the connection and the tightness test. Includes the connection and the tightness test. Measured per unit completed.',
    'Ejecución de instalación de gabinete de gas., con conexión y prueba. Incluye la conexión y la prueba de estanqueidad. Medido por unidad ejecutado/a.':
        'Installation of a gas meter cabinet, with the connection and the tightness test. Includes the connection and the tightness test. Measured per unit completed.',
    'Ejecución de instalación de llave de corte de gas., con conexión y prueba. Incluye la conexión y la prueba de estanqueidad. Medido por unidad ejecutado/a.':
        'Installation of a gas shut off valve, with the connection and the tightness test. Includes the connection and the tightness test. Measured per unit completed.',
    'Ejecución de instalación de medidor de gas., con conexión y prueba. Incluye la conexión y la prueba de estanqueidad. Medido por unidad ejecutado/a.':
        'Installation of a gas meter, with the connection and the tightness test. Includes the connection and the tightness test. Measured per unit completed.',
    'Ejecución de instalación de regulador de alta presión., con conexión y prueba. Incluye la conexión y la prueba de estanqueidad. Medido por unidad ejecutado/a.':
        'Installation of a high pressure regulator, with the connection and the tightness test. Includes the connection and the tightness test. Measured per unit completed.',
    'Ejecución de instalación de regulador de baja presión., con conexión y prueba. Incluye la conexión y la prueba de estanqueidad. Medido por unidad ejecutado/a.':
        'Installation of a low pressure regulator, with the connection and the tightness test. Includes the connection and the tightness test. Measured per unit completed.',
    'Ejecución de instalación de regulador de gas., con conexión y prueba. Incluye la conexión y la prueba de estanqueidad. Medido por unidad ejecutado/a.':
        'Installation of a gas pressure regulator, with the connection and the tightness test. Includes the connection and the tightness test. Measured per unit completed.',
    'Ejecución de instalación de válvula de exceso de flujo., con conexión y prueba. Incluye la conexión y la prueba de estanqueidad. Medido por unidad ejecutado/a.':
        'Installation of an excess flow valve, with the connection and the tightness test. Includes the connection and the tightness test. Measured per unit completed.',
    'Ejecución de instalación de válvula de gas., con conexión y prueba. Incluye la conexión. Medido por unidad ejecutado/a.':
        'Installation of a gas valve, with the connection and the tightness test. Includes the connection. Measured per unit completed.',
    'Ejecución de instalación de válvula de seguridad., con conexión y prueba. Incluye la conexión y la prueba de estanqueidad. Medido por unidad ejecutado/a.':
        'Installation of a safety valve, with the connection and the tightness test. Includes the connection and the tightness test. Measured per unit completed.',
    'Ejecución de malla captadora en fachada., con conexión. Incluye la conexión y la fijación. Medido por unidad ejecutada.':
        'Installation of air termination mesh on a facade, with the connection. Includes the connection and the fastening. Measured per unit completed.',
    'Ejecución de patch panel de red., con canalización y conexión. Incluye el tendido del cable y la conexión. Medido por punto ejecutado.':
        'Installation of a network patch panel, with the containment and the connection. Includes running the cable and making the connection. Measured per point completed.',
    'Ejecución de protector de sobretensión combinado., con conexión. Incluye la conexión y la fijación. Medido por unidad ejecutada.':
        'Installation of a combined surge protective device, with the connection. Includes the connection and the fastening. Measured per unit completed.',
    'Ejecución de protector de sobretensión de antena., con conexión. Incluye la conexión y la fijación. Medido por unidad ejecutada.':
        'Installation of a surge protective device for the antenna, with the connection. Includes the connection and the fastening. Measured per unit completed.',
    'Ejecución de protector de sobretensión de datos., con conexión. Incluye la conexión y la fijación. Medido por unidad ejecutada.':
        'Installation of a surge protective device for the data line, with the connection. Includes the connection and the fastening. Measured per unit completed.',
    'Ejecución de protector de sobretensión de red., con conexión. Incluye la conexión y la fijación. Medido por unidad ejecutada.':
        'Installation of a surge protective device for the mains supply, with the connection. Includes the connection and the fastening. Measured per unit completed.',
    'Ejecución de protector de sobretensión de teléfono., con conexión. Incluye la conexión y la fijación. Medido por unidad ejecutada.':
        'Installation of a surge protective device for the telephone line, with the connection. Includes the connection and the fastening. Measured per unit completed.',
    'Ejecución de prueba de aislamiento eléctrico., con verificación. Incluye la verificación y el ajuste. Medido por unidad ejecutada.':
        'Electrical insulation resistance test, with the verification. Includes the verification and the adjustment. Measured per unit completed.',
    'Ejecución de prueba de estanqueidad de gas., con conexión y prueba. Incluye la conexión y la prueba de estanqueidad. Medido por unidad ejecutado/a.':
        'Gas tightness test, with the connection and the tightness test. Includes the connection and the tightness test. Measured per unit completed.',
    'Ejecución de prueba de presión de gas., con verificación. Incluye la verificación y el ajuste. Medido por unidad ejecutada.':
        'Gas pressure test, with the verification. Includes the verification and the adjustment. Measured per unit completed.',
    'Ejecución de puesta en marcha de sistema de acceso., con verificación. Incluye la verificación y el ajuste. Medido por unidad ejecutada.':
        'Commissioning of the access control system, with the verification. Includes the verification and the adjustment. Measured per unit completed.',
    'Ejecución de puesta en marcha de sistema de alarma., con verificación. Incluye la verificación y el ajuste. Medido por unidad ejecutada.':
        'Commissioning of the alarm system, with the verification. Includes the verification and the adjustment. Measured per unit completed.',
    'Ejecución de puesta en marcha de sistema de gas., con verificación. Incluye la verificación y el ajuste. Medido por unidad ejecutada.':
        'Commissioning of the gas system, with the verification. Includes the verification and the adjustment. Measured per unit completed.',
    'Ejecución de puesta en marcha de sistema de ventilación., con verificación. Incluye la verificación y el ajuste. Medido por unidad ejecutada.':
        'Commissioning of the ventilation system, with the verification. Includes the verification and the adjustment. Measured per unit completed.',
    'Ejecución de punto de datos para acceso., con canalización y conexión. Incluye el tendido y la conexión. Medido por punto ejecutado.':
        'Installation of a data outlet for an access point, with the containment and the connection. Includes running the cable and making the connection. Measured per point completed.',
    'Ejecución de punto de datos para oficina., con canalización y conexión. Incluye el tendido y la conexión. Medido por punto ejecutado.':
        'Installation of a data outlet for an office, with the containment and the connection. Includes running the cable and making the connection. Measured per point completed.',
    'Ejecución de punto de datos para repetidor., con canalización y conexión. Incluye el tendido y la conexión. Medido por punto ejecutado.':
        'Installation of a data outlet for a repeater, with the containment and the connection. Includes running the cable and making the connection. Measured per point completed.',
    'Ejecución de punto de gas para calentador de paso., con conexión y prueba. Incluye la conexión y la prueba de estanqueidad. Medido por unidad ejecutado/a.':
        'Installation of a gas outlet for an instantaneous water heater, with the connection and the tightness test. Includes the connection and the tightness test. Measured per unit completed.',
    'Ejecución de punto de gas para calentador., con conexión y prueba. Incluye la conexión y la prueba de estanqueidad. Medido por unidad ejecutado/a.':
        'Installation of a gas outlet for a water heater, with the connection and the tightness test. Includes the connection and the tightness test. Measured per unit completed.',
    'Ejecución de punto de gas para cocina industrial., con conexión y prueba. Incluye la conexión. Medido por unidad ejecutado/a.':
        'Installation of a gas outlet for a commercial kitchen, with the connection and the tightness test. Includes the connection. Measured per unit completed.',
    'Ejecución de punto de gas para cocina., con conexión y prueba. Incluye la conexión y la prueba de estanqueidad. Medido por unidad ejecutado/a.':
        'Installation of a gas outlet for a kitchen, with the connection and the tightness test. Includes the connection and the tightness test. Measured per unit completed.',
    'Ejecución de punto de gas para estufa., con conexión y prueba. Incluye la conexión y la prueba de estanqueidad. Medido por unidad ejecutado/a.':
        'Installation of a gas outlet for a cooker, with the connection and the tightness test. Includes the connection and the tightness test. Measured per unit completed.',
    'Ejecución de punto de gas para horno., con conexión y prueba. Incluye la conexión y la prueba de estanqueidad. Medido por unidad ejecutado/a.':
        'Installation of a gas outlet for an oven, with the connection and the tightness test. Includes the connection and the tightness test. Measured per unit completed.',
    'Ejecución de punto de gas para lavandería., con conexión y prueba. Incluye la conexión y la prueba de estanqueidad. Medido por unidad ejecutado/a.':
        'Installation of a gas outlet for a laundry room, with the connection and the tightness test. Includes the connection and the tightness test. Measured per unit completed.',
    'Ejecución de punto de gas para parrillera., con conexión y prueba. Incluye la conexión y la prueba de estanqueidad. Medido por unidad ejecutado/a.':
        'Installation of a gas outlet for a barbecue, with the connection and the tightness test. Includes the connection and the tightness test. Measured per unit completed.',
    'Ejecución de punto de gas para secadora de ropa., con conexión y prueba. Incluye la conexión y la prueba de estanqueidad. Medido por unidad ejecutado/a.':
        'Installation of a gas outlet for a clothes dryer, with the connection and the tightness test. Includes the connection and the tightness test. Measured per unit completed.',
    'Ejecución de punto de gas para secadora., con conexión y prueba. Incluye la conexión y la prueba de estanqueidad. Medido por unidad ejecutado/a.':
        'Installation of a gas outlet for a clothes dryer, with the connection and the tightness test. Includes the connection and the tightness test. Measured per unit completed.',
    'Ejecución de punto de gas para terraza., con conexión y prueba. Incluye la conexión y la prueba de estanqueidad. Medido por unidad ejecutado/a.':
        'Installation of a gas outlet for a terrace, with the connection and the tightness test. Includes the connection and the tightness test. Measured per unit completed.',
    'Ejecución de rack de telecomunicaciones., con canalización y conexión. Incluye el tendido del cable y la conexión. Medido por punto ejecutado.':
        'Installation of a telecommunications rack, with the containment and the connection. Includes running the cable and making the connection. Measured per point completed.',
    'Ejecución de reparación de bomba de agua., con verificación. Incluye la verificación y el ajuste. Medido por unidad ejecutada.':
        'Repair of a water pump, with the verification. Includes the verification and the adjustment. Measured per unit completed.',
    'Ejecución de reparación de extractor., con verificación. Incluye la verificación y el ajuste. Medido por unidad ejecutada.':
        'Repair of an extractor fan, with the verification. Includes the verification and the adjustment. Measured per unit completed.',
    'Ejecución de reparación de inversor., con verificación. Incluye la verificación y el ajuste. Medido por unidad ejecutada.':
        'Repair of an inverter, with the verification. Includes the verification and the adjustment. Measured per unit completed.',
    'Ejecución de reparación de panel solar., con verificación. Incluye la verificación y el ajuste. Medido por unidad ejecutada.':
        'Repair of a solar panel, with the verification. Includes the verification and the adjustment. Measured per unit completed.',
    'Ejecución de reparación de tanque de agua., con verificación. Incluye la verificación y el ajuste. Medido por unidad ejecutada.':
        'Repair of a water tank, with the verification. Includes the verification and the adjustment. Measured per unit completed.',
    'Ejecución de reparación de ventilador., con verificación. Incluye la verificación y el ajuste. Medido por unidad ejecutada.':
        'Repair of a fan, with the verification. Includes the verification and the adjustment. Measured per unit completed.',
    'Ejecución de toma de tierra de pararrayos., con conexión. Incluye la conexión y la fijación. Medido por unidad ejecutada.':
        'Installation of a lightning protection grounding electrode, with the connection. Includes the connection and the fastening. Measured per unit completed.',
    'Ejecución de toma de tierra en anillo., con conexión. Incluye la conexión y la fijación. Medido por unidad ejecutada.':
        'Installation of a ring grounding electrode, with the connection. Includes the connection and the fastening. Measured per unit completed.',
    'Ejecución de tubería de gas de acero., con conexión y prueba. Incluye la conexión y la prueba de estanqueidad. Medido por metro lineal ejecutado/a.':
        'Installation of steel gas piping, with the connection and the tightness test. Includes the connection and the tightness test. Measured per linear meter completed.',
    'Ejecución de tubería de gas de cobre., con conexión y prueba. Incluye la conexión y la prueba de estanqueidad. Medido por metro lineal ejecutado/a.':
        'Installation of copper gas piping, with the connection and the tightness test. Includes the connection and the tightness test. Measured per linear meter completed.',
    'Ejecución de tubería de gas de montante., con conexión y prueba. Incluye la conexión y la prueba de estanqueidad. Medido por metro lineal ejecutado/a.':
        'Installation of a gas riser, with the connection and the tightness test. Includes the connection and the tightness test. Measured per linear meter completed.',
    'Ejecución de tubería de gas de polietileno., con conexión y prueba. Incluye la conexión. Medido por metro lineal ejecutado/a.':
        'Installation of polyethylene gas piping, with the connection and the tightness test. Includes the connection. Measured per linear meter completed.',
    'Ejecución de tubería de gas empotrada., con conexión y prueba. Incluye la conexión y la prueba de estanqueidad. Medido por metro lineal ejecutado/a.':
        'Installation of concealed gas piping, with the connection and the tightness test. Includes the connection and the tightness test. Measured per linear meter completed.',
    'Ejecución de tubería de gas flexible., con conexión y prueba. Incluye la conexión y la prueba de estanqueidad. Medido por metro lineal ejecutado/a.':
        'Installation of flexible gas connector, with the connection and the tightness test. Includes the connection and the tightness test. Measured per linear meter completed.',
    'Ejecución de tubería de gas vista., con conexión y prueba. Incluye la conexión y la prueba de estanqueidad. Medido por metro lineal ejecutado/a.':
        'Installation of surface mounted gas piping, with the connection and the tightness test. Includes the connection and the tightness test. Measured per linear meter completed.',
    'Instalación de actuador de calefacción., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of a heating actuator, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de actuador de riego., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of an irrigation actuator, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de alarma con sensores., con conexión y configuración. Incluye la conexión. Medido por unidad instalada.':
        'Installation of an alarm system with sensors, with the connection and configuration. Includes the connection. Measured per unit installed.',
    'Instalación de alarma de incendio., con fijación y señalización. Incluye la fijación y la señalización. Medido por unidad instalada.':
        'Installation of a fire alarm, with fastening and signage. Includes the fastening and signage. Measured per unit installed.',
    'Instalación de alarma interior., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of an internal alarm, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de alarma perimetral., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of a perimeter alarm, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de altavoces., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of loudspeakers, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de amplificador., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of an amplifier, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de antena., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of an antenna, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de ascensor de 3 paradas., con montaje y puesta en marcha. Incluye el montaje. Medido por unidad instalada.':
        'Installation of a three-stop elevator, with assembly and commissioning. Includes the assembly. Measured per unit installed.',
    'Instalación de ascensor de 4 paradas., con montaje y puesta en marcha. Incluye el montaje. Medido por unidad instalada.':
        'Installation of a four-stop elevator, with assembly and commissioning. Includes the assembly. Measured per unit installed.',
    'Instalación de ascensor de 5 paradas., con montaje y puesta en marcha. Incluye el montaje. Medido por unidad instalada.':
        'Installation of a five-stop elevator, with assembly and commissioning. Includes the assembly. Measured per unit installed.',
    'Instalación de ascensor de 6 paradas., con montaje y puesta en marcha. Incluye el montaje. Medido por unidad instalada.':
        'Installation of a six-stop elevator, with assembly and commissioning. Includes the assembly. Measured per unit installed.',
    'Instalación de ascensor de alta velocidad., con montaje y puesta en marcha. Incluye el montaje. Medido por unidad instalada.':
        'Installation of a high-speed elevator, with assembly and commissioning. Includes the assembly. Measured per unit installed.',
    'Instalación de ascensor de carga pesada., con montaje y puesta en marcha. Incluye el montaje. Medido por unidad instalada.':
        'Installation of a heavy-duty freight elevator, with assembly and commissioning. Includes the assembly. Measured per unit installed.',
    'Instalación de ascensor de carga. Incluye el montaje y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a freight elevator. Includes the assembly and commissioning. Measured per unit installed.',
    'Instalación de ascensor de dos paradas, con estructura y cabina. Incluye el montaje y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a two-stop elevator, with the structure and the car. Includes the assembly and commissioning. Measured per unit installed.',
    'Instalación de ascensor de tracción con cuarto de máquinas. Incluye el montaje y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a traction elevator with a machine room. Includes the assembly and commissioning. Measured per unit installed.',
    'Instalación de ascensor existente., con montaje y puesta en marcha. Incluye el montaje. Medido por unidad instalada.':
        'Installation of an existing elevator, with assembly and commissioning. Includes the assembly. Measured per unit installed.',
    'Instalación de ascensor panorámico con estructura de vidrio. Incluye el montaje y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a panoramic elevator with a glass structure. Includes the assembly and commissioning. Measured per unit installed.',
    'Instalación de ascensor para discapacitados., con montaje y puesta en marcha. Incluye el montaje. Medido por unidad instalada.':
        'Installation of an accessible elevator, with assembly and commissioning. Includes the assembly. Measured per unit installed.',
    'Instalación de ascensor sin cuarto de máquinas. Incluye el montaje y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a machine-room-less elevator. Includes the assembly and commissioning. Measured per unit installed.',
    'Instalación de banco de baterías., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a battery bank, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de batería de 200ah., con conexión. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a 200 Ah battery, with the connection. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de batería de litio., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a lithium battery, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de batería de plomo., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a lead-acid battery, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de batería., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a battery, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de bomba centrífuga., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a centrifugal pump, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de bomba contra incendios., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a fire pump, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de bomba de achique., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a sump pump, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de bomba de agua potable., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a potable water pump, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de bomba de agua residual., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a sewage pump, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de bomba de agua., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a water pump, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de bomba de piscina., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a pool pump, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de bomba de pozo., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a well pump, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de bomba de recirculación., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a recirculation pump, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de bomba de riego., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of an irrigation pump, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de bomba de superficie., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a surface pump, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de bomba presurizadora., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a booster pump, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de bomba presurizadora., con conexión. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a booster pump, with the connection. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de bomba sumergible., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a submersible pump, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de cableado solar., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a solar cabling, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de campana extractora., con conexión. Incluye la conexión y la fijación. Medido por unidad instalada.':
        'Installation of a range hood, with the connection. Includes the connection and fastening. Measured per unit installed.',
    'Instalación de central de incendios., con fijación y señalización. Incluye la fijación y la señalización. Medido por unidad instalada.':
        'Installation of a fire alarm control panel, with fastening and signage. Includes the fastening and signage. Measured per unit installed.',
    'Instalación de central domótica con control remoto., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of a home automation controller with remote control, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de cine en casa., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of a home theater system, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de citófono., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of a door entry phone, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de control de acceso biométrico., con conexión y configuración. Incluye la conexión. Medido por unidad instalada.':
        'Installation of a biometric access control, with the connection and configuration. Includes the connection. Measured per unit installed.',
    'Instalación de control de acceso., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of an access control system, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de cámara con grabador., con conexión y configuración. Incluye la conexión. Medido por unidad instalada.':
        'Installation of a camera with a recorder, with the connection and configuration. Includes the connection. Measured per unit installed.',
    'Instalación de cámara de comercio., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of a camera for commercial premises, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de cámara de entrada., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of a camera at the entrance, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de cámara de garaje., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of a garage camera, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de cámara de jardín., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of a garden camera, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de cámara de local., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of a camera for premises, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de cámara de seguridad., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of a security camera, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de cámara de terraza., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of a terrace camera, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de cámara exterior., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of an external camera, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de cámara interior., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of an internal camera, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de detector combinado., con fijación y señalización. Incluye la fijación. Medido por unidad instalada.':
        'Installation of a combined detector, with fastening and signage. Includes the fastening. Measured per unit installed.',
    'Instalación de detector de calor., con fijación y señalización. Incluye la fijación y la señalización. Medido por unidad instalada.':
        'Installation of a heat detector, with fastening and signage. Includes the fastening and signage. Measured per unit installed.',
    'Instalación de detector de humo., con fijación y señalización. Incluye la fijación y la señalización. Medido por unidad instalada.':
        'Installation of a smoke detector, with fastening and signage. Includes the fastening and signage. Measured per unit installed.',
    'Instalación de detectores en cocina., con fijación y señalización. Incluye la fijación y la señalización. Medido por unidad instalada.':
        'Installation of detectors in a kitchen, with fastening and signage. Includes the fastening and signage. Measured per unit installed.',
    'Instalación de detectores en depósito., con fijación y señalización. Incluye la fijación y la señalización. Medido por unidad instalada.':
        'Installation of detectors in a store, with fastening and signage. Includes the fastening and signage. Measured per unit installed.',
    'Instalación de detectores en dormitorio., con fijación y señalización. Incluye la fijación y la señalización. Medido por unidad instalada.':
        'Installation of detectors in a bedroom, with fastening and signage. Includes the fastening and signage. Measured per unit installed.',
    'Instalación de detectores en escalera., con fijación y señalización. Incluye la fijación y la señalización. Medido por unidad instalada.':
        'Installation of detectors in a stairwell, with fastening and signage. Includes the fastening and signage. Measured per unit installed.',
    'Instalación de detectores en garaje., con fijación y señalización. Incluye la fijación y la señalización. Medido por unidad instalada.':
        'Installation of detectors in a garage, with fastening and signage. Includes the fastening and signage. Measured per unit installed.',
    'Instalación de detectores en pasillo., con fijación y señalización. Incluye la fijación y la señalización. Medido por unidad instalada.':
        'Installation of detectors in a corridor, with fastening and signage. Includes the fastening and signage. Measured per unit installed.',
    'Instalación de detectores en sala., con fijación y señalización. Incluye la fijación y la señalización. Medido por unidad instalada.':
        'Installation of detectors in a living room, with fastening and signage. Includes the fastening and signage. Measured per unit installed.',
    'Instalación de difusor., con conexión. Incluye la conexión y la fijación. Medido por unidad instalada.':
        'Installation of a diffuser, with the connection. Includes the connection and fastening. Measured per unit installed.',
    'Instalación de ducto flexible., con conexión. Incluye la conexión y la fijación. Medido por unidad instalada.':
        'Installation of a flexible duct, with the connection. Includes the connection and fastening. Measured per unit installed.',
    'Instalación de ducto rígido., con conexión. Incluye la conexión y la fijación. Medido por unidad instalada.':
        'Installation of a rigid duct, with the connection. Includes the connection and fastening. Measured per unit installed.',
    'Instalación de elevador de fachada para accesibilidad. Incluye el montaje y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a facade platform lift for accessibility. Includes the assembly and commissioning. Measured per unit installed.',
    'Instalación de elevador de plataforma para accesibilidad. Incluye el montaje y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a platform lift for accessibility. Includes the assembly and commissioning. Measured per unit installed.',
    'Instalación de elevador de silla., con montaje y puesta en marcha. Incluye el montaje. Medido por unidad instalada.':
        'Installation of a chair lift, with assembly and commissioning. Includes the assembly. Measured per unit installed.',
    'Instalación de equipo cassette., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a cassette air conditioning unit, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de equipo de climatización, con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of an air conditioning unit, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de equipo de confort., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a comfort air conditioning unit, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de equipo de piso-techo., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a floor and ceiling air conditioning unit, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de equipo de piso., con conexión y puesta en marcha. Incluye la conexión. Medido por unidad instalada.':
        'Installation of a floor mounted air conditioning unit, with the connection and commissioning. Includes the connection. Measured per unit installed.',
    'Instalación de equipo de precisión., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a precision air conditioning unit, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de equipo de techo., con conexión y puesta en marcha. Incluye la conexión. Medido por unidad instalada.':
        'Installation of a ceiling mounted air conditioning unit, with the connection and commissioning. Includes the connection. Measured per unit installed.',
    'Instalación de equipo de ventana., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a window air conditioning unit, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de equipo multisplit., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a multi-split air conditioning system, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de equipo para comercio., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of an air conditioning unit for commercial premises, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de equipo para consultorio., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of an air conditioning unit for a surgery, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de equipo para depósito., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of an air conditioning unit for a store, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de equipo para dormitorio., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of an air conditioning unit for a bedroom, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de equipo para estudio., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of an air conditioning unit for a study, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de equipo para garaje., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of an air conditioning unit for a garage, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de equipo para habitación., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of an air conditioning unit for a room, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de equipo para local., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of an air conditioning unit for premises, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de equipo para oficina., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of an air conditioning unit for an office, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de equipo para restaurante., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of an air conditioning unit for a restaurant, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de equipo para sala., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of an air conditioning unit for a living room, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de equipo para terraza., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of an air conditioning unit for a terrace, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de equipo split de pared., con conexión y puesta en marcha. Incluye la conexión. Medido por unidad instalada.':
        'Installation of a wall mounted split air conditioning unit, with the connection and commissioning. Includes the connection. Measured per unit installed.',
    'Instalación de equipo split inverter., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of an inverter split air conditioning unit, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de estructura de paneles., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a panel support structure, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de extintor de co2., con fijación y señalización. Incluye la fijación y la señalización. Medido por unidad instalada.':
        'Installation of a CO2 fire extinguisher, with fastening and signage. Includes the fastening and signage. Measured per unit installed.',
    'Instalación de extintor de espuma., con fijación y señalización. Incluye la fijación y la señalización. Medido por unidad instalada.':
        'Installation of a foam fire extinguisher, with fastening and signage. Includes the fastening and signage. Measured per unit installed.',
    'Instalación de extintor de polvo., con fijación y señalización. Incluye la fijación. Medido por unidad instalada.':
        'Installation of a dry powder fire extinguisher, with fastening and signage. Includes the fastening. Measured per unit installed.',
    'Instalación de extintor en cocina., con fijación y señalización. Incluye la fijación y la señalización. Medido por unidad instalada.':
        'Installation of a fire extinguisher in a kitchen, with fastening and signage. Includes the fastening and signage. Measured per unit installed.',
    'Instalación de extintor en comercio., con fijación y señalización. Incluye la fijación y la señalización. Medido por unidad instalada.':
        'Installation of a fire extinguisher in commercial premises, with fastening and signage. Includes the fastening and signage. Measured per unit installed.',
    'Instalación de extintor en depósito., con fijación y señalización. Incluye la fijación y la señalización. Medido por unidad instalada.':
        'Installation of a fire extinguisher in a store, with fastening and signage. Includes the fastening and signage. Measured per unit installed.',
    'Instalación de extintor en garaje., con fijación y señalización. Incluye la fijación y la señalización. Medido por unidad instalada.':
        'Installation of a fire extinguisher in a garage, with fastening and signage. Includes the fastening and signage. Measured per unit installed.',
    'Instalación de extintor en local., con fijación y señalización. Incluye la fijación y la señalización. Medido por unidad instalada.':
        'Installation of a fire extinguisher in premises, with fastening and signage. Includes the fastening and signage. Measured per unit installed.',
    'Instalación de extintor en oficina., con fijación y señalización. Incluye la fijación y la señalización. Medido por unidad instalada.':
        'Installation of a fire extinguisher in an office, with fastening and signage. Includes the fastening and signage. Measured per unit installed.',
    'Instalación de extintor en terraza., con fijación y señalización. Incluye la fijación y la señalización. Medido por unidad instalada.':
        'Installation of a fire extinguisher on a terrace, with fastening and signage. Includes the fastening and signage. Measured per unit installed.',
    'Instalación de extractor de baño., con conexión. Incluye la conexión y la fijación. Medido por unidad instalada.':
        'Installation of a bathroom extractor fan, with the connection. Includes the connection and fastening. Measured per unit installed.',
    'Instalación de extractor de campana., con conexión. Incluye la conexión. Medido por unidad instalada.':
        'Installation of a range hood extractor fan, with the connection. Includes the connection. Measured per unit installed.',
    'Instalación de extractor de cocina., con conexión. Incluye la conexión y la fijación. Medido por unidad instalada.':
        'Installation of a kitchen extractor fan, with the connection. Includes the connection and fastening. Measured per unit installed.',
    'Instalación de gabinete de manguera., con fijación y señalización. Incluye la fijación y la señalización. Medido por unidad instalada.':
        'Installation of a hose reel cabinet, with fastening and signage. Includes the fastening and signage. Measured per unit installed.',
    'Instalación de grabador de video., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of a video recorder, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de hidrante., con fijación y señalización. Incluye la fijación y la señalización. Medido por unidad instalada.':
        'Installation of a hydrant, with fastening and signage. Includes the fastening and signage. Measured per unit installed.',
    'Instalación de intercomunicación general., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of a general intercom system, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de intercomunicador de edificio., con conexión y configuración. Incluye la conexión. Medido por unidad instalada.':
        'Installation of a building intercom, with the connection and configuration. Includes the connection. Measured per unit installed.',
    'Instalación de intercomunicador de puerta., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of a door intercom, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de intercomunicador., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of an intercom, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de inversor aislado., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of an off-grid inverter, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de inversor de 3kw., con conexión. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a 3 kW inverter, with the connection. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de inversor de red., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a grid-tie inverter, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de inversor híbrido., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a hybrid inverter, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de inversor., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of an inverter, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de lector de tarjetas., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of a card reader, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de luminaria de emergencia con señalización. Incluye la conexión y la fijación. Medido por unidad instalada.':
        'Installation of an emergency light fixture with signage. Includes the connection and fastening. Measured per unit installed.',
    'Instalación de luz de emergencia., con fijación y señalización. Incluye la fijación y la señalización. Medido por unidad instalada.':
        'Installation of an emergency light, with fastening and signage. Includes the fastening and signage. Measured per unit installed.',
    'Instalación de medidor bidireccional., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a bidirectional energy meter, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de monitor de vigilancia., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of a surveillance monitor, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de montacargas de carga., con montaje y puesta en marcha. Incluye el montaje. Medido por unidad instalada.':
        'Installation of a freight elevator, with assembly and commissioning. Includes the assembly. Measured per unit installed.',
    'Instalación de montacargas de cocina o servicio. Incluye el montaje y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a dumbwaiter for a kitchen or for service. Includes the assembly and commissioning. Measured per unit installed.',
    'Instalación de montacargas de obra o de servicio. Incluye el montaje y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a construction or service hoist. Includes the assembly and commissioning. Measured per unit installed.',
    'Instalación de módulo de control de bomba., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of a pump control module, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de panel de alarma., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of an alarm panel, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de panel de control táctil., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of a touch control panel, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de panel de control., con conexión y configuración. Incluye la conexión. Medido por unidad instalada.':
        'Installation of a control panel, with the connection and configuration. Includes the connection. Measured per unit installed.',
    'Instalación de panel solar comercial., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a commercial solar panel, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de panel solar de 400w., con conexión. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a 400 W solar panel, with the connection. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de panel solar doméstico., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a domestic solar panel, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de panel solar en jardín., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a solar panel in a garden, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de panel solar en techo., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a roof mounted solar panel, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de panel solar en terraza., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a solar panel on a terrace, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de panel solar., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a solar panel, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de pantalla de proyección., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of a projection screen, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de planta de respaldo., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a backup generator, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de planta eléctrica a gas., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a gas fired generator, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de planta eléctrica diésel., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a diesel generator, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de planta eléctrica., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a generator, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de plataforma elevadora vertical para accesibilidad. Incluye el montaje y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a vertical platform lift for accessibility. Includes the assembly and commissioning. Measured per unit installed.',
    'Instalación de plataforma salvaescaleras., con montaje y puesta en marcha. Incluye el montaje. Medido por unidad instalada.':
        'Installation of a platform stairlift, with assembly and commissioning. Includes the assembly. Measured per unit installed.',
    'Instalación de portero con video., con conexión y configuración. Incluye la conexión. Medido por unidad instalada.':
        'Installation of a video door entry system, with the connection and configuration. Includes the connection. Measured per unit installed.',
    'Instalación de portero eléctrico., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of an electric door release, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de protecciones solares., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of solar system protective devices, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de proyector., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of a projector, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de pulsador de alarma., con fijación y señalización. Incluye la fijación y la señalización. Medido por unidad instalada.':
        'Installation of an alarm call point, with fastening and signage. Includes the fastening and signage. Measured per unit installed.',
    'Instalación de pulsador de escena inalámbrico., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of a wireless scene controller, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de rampa mecánica., con montaje y puesta en marcha. Incluye el montaje. Medido por unidad instalada.':
        'Installation of a moving ramp, with assembly and commissioning. Includes the assembly. Measured per unit installed.',
    'Instalación de receptor de tv., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of a television receiver, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de receptor satelital., con conexión y configuración. Incluye la conexión. Medido por unidad instalada.':
        'Installation of a satellite receiver, with the connection and configuration. Includes the connection. Measured per unit installed.',
    'Instalación de refrigerante., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of refrigerant, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de regulador de carga., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a charge controller, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de rejilla de extracción., con conexión. Incluye la conexión y la fijación. Medido por unidad instalada.':
        'Installation of an extract grille, with the connection. Includes the connection and fastening. Measured per unit installed.',
    'Instalación de rejilla de retorno., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a return air grille, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de rejilla de retorno., con conexión. Incluye la conexión. Medido por unidad instalada.':
        'Installation of a return air grille, with the connection. Includes the connection. Measured per unit installed.',
    'Instalación de rejilla de suministro., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a supply air grille, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de rejilla de ventilación., con conexión. Incluye la conexión y la fijación. Medido por unidad instalada.':
        'Installation of a ventilation grille, with the connection. Includes the connection and fastening. Measured per unit installed.',
    'Instalación de repetidor de señal cableada., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of a wired signal repeater, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de rociador., con fijación y señalización. Incluye la fijación y la señalización. Medido por unidad instalada.':
        'Installation of a sprinkler head, with fastening and signage. Includes the fastening and signage. Measured per unit installed.',
    'Instalación de salvaescaleras de plataforma. Incluye el montaje del riel y la plataforma. Medido por unidad instalada.':
        'Installation of a platform stairlift. Includes the assembly of the rail and the platform. Measured per unit installed.',
    'Instalación de salvaescaleras para accesibilidad. Incluye el montaje del riel y la silla. Medido por unidad instalada.':
        'Installation of a stairlift for accessibility. Includes the assembly of the rail and the seat. Measured per unit installed.',
    'Instalación de sensor de calidad de aire., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of an air quality sensor, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de sensor de consumo eléctrico., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of an electricity consumption sensor, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de sensor de movimiento., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of a motion sensor, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de sensor de presencia., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of an occupancy sensor, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de sensor de puerta y ventana., con conexión y configuración. Incluye la conexión. Medido por unidad instalada.':
        'Installation of a door and window sensor, with the connection and configuration. Includes the connection. Measured per unit installed.',
    'Instalación de sensor de puerta., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of a door sensor, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de sensor de ventana., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of a window sensor, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de señal de salida., con fijación y señalización. Incluye la fijación. Medido por unidad instalada.':
        'Installation of an exit sign, with fastening and signage. Includes the fastening. Measured per unit installed.',
    'Instalación de señalización de evacuación., con fijación y señalización. Incluye la fijación y la señalización. Medido por unidad instalada.':
        'Installation of an escape route signage, with fastening and signage. Includes the fastening and signage. Measured per unit installed.',
    'Instalación de silla salvaescaleras. Incluye el montaje del riel y la silla. Medido por unidad instalada.':
        'Installation of a stairlift. Includes the assembly of the rail and the seat. Measured per unit installed.',
    'Instalación de sirena de alarma., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of an alarm siren, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de sirena exterior., con conexión y configuración. Incluye la conexión. Medido por unidad instalada.':
        'Installation of an external siren, with the connection and configuration. Includes the connection. Measured per unit installed.',
    'Instalación de sirena., con fijación y señalización. Incluye la fijación y la señalización. Medido por unidad instalada.':
        'Installation of a siren, with fastening and signage. Includes the fastening and signage. Measured per unit installed.',
    'Instalación de sistema cctv., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of a CCTV system, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de sistema de acceso., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of an access control system, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de sistema de alarma., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of an alarm system, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de sistema de audio multizona., con conexión y configuración. Incluye la conexión. Medido por unidad instalada.':
        'Installation of a multi-zone audio system, with the connection and configuration. Includes the connection. Measured per unit installed.',
    'Instalación de sistema de audio., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of an audio system, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de sistema de bombeo., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a pumping system, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de sistema de cine., con conexión y configuración. Incluye la conexión. Medido por unidad instalada.':
        'Installation of a home theater system, with the connection and configuration. Includes the connection. Measured per unit installed.',
    'Instalación de sistema de conductos., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a ducted air conditioning system, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de sistema de intercomunicación., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of an intercom system, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de sistema de música., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of a music system, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de sistema de respaldo., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a backup power system, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de sistema de video., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of a video system, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de sistema de video., con conexión y configuración. Incluye la conexión. Medido por unidad instalada.':
        'Installation of a video system, with the connection and configuration. Includes the connection. Measured per unit installed.',
    'Instalación de sistema fotovoltaico., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a photovoltaic system, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de sistema hidroneumático., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a hydropneumatic system, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de sistema solar., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a solar system, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de sonido ambiente., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of an ambient sound system, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de sonido de ambiente., con conexión y configuración. Incluye la conexión. Medido por unidad instalada.':
        'Installation of an ambient sound system, with the connection and configuration. Includes the connection. Measured per unit installed.',
    'Instalación de sonido de dormitorio., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of a bedroom sound system, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de sonido de jardín., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of a garden sound system, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de sonido de sala., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of a living room sound system, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de sonido de terraza., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of a terrace sound system, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de tablero de transferencia., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a transfer switch, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de tanque cisterna., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a cistern, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de tanque de agua caliente., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a hot water tank, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de tanque de agua elevado., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of an elevated water tank, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de tanque de agua enterrado., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a buried water tank, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de tanque de agua potable., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a potable water tank, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de tanque de presión hidroneumático., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a hydropneumatic pressure tank, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de tanque de presión., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a pressure tank, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de tanque de reserva., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a reserve tank, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de tanque de reserva., con conexión. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a reserve tank, with the connection. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de tanque de tormenta., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a stormwater tank, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de tanque elevado., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of an elevated tank, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de tanque enterrado., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a buried tank, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de tanque séptico., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a septic tank, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de teatro en casa., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of a home theater system, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de teclado de acceso., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of an access keypad, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de termostato inalámbrico., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of a wireless thermostat, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de termostato., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a thermostat, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de unidad condensadora., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a condensing unit, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de unidad interior., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of an indoor unit, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
    'Instalación de ventilación de baño., con conexión. Incluye la conexión y la fijación. Medido por unidad instalada.':
        'Installation of a bathroom ventilation, with the connection. Includes the connection and fastening. Measured per unit installed.',
    'Instalación de ventilación de closet., con conexión. Incluye la conexión y la fijación. Medido por unidad instalada.':
        'Installation of a closet ventilation, with the connection. Includes the connection and fastening. Measured per unit installed.',
    'Instalación de ventilación de cocina., con conexión. Incluye la conexión y la fijación. Medido por unidad instalada.':
        'Installation of a kitchen ventilation, with the connection. Includes the connection and fastening. Measured per unit installed.',
    'Instalación de ventilación de comedor., con conexión. Incluye la conexión y la fijación. Medido por unidad instalada.':
        'Installation of a dining room ventilation, with the connection. Includes the connection and fastening. Measured per unit installed.',
    'Instalación de ventilación de comercio., con conexión. Incluye la conexión y la fijación. Medido por unidad instalada.':
        'Installation of a ventilation for commercial premises, with the connection. Includes the connection and fastening. Measured per unit installed.',
    'Instalación de ventilación de cuarto técnico., con conexión. Incluye la conexión y la fijación. Medido por unidad instalada.':
        'Installation of a ventilation for a mechanical room, with the connection. Includes the connection and fastening. Measured per unit installed.',
    'Instalación de ventilación de depósito., con conexión. Incluye la conexión y la fijación. Medido por unidad instalada.':
        'Installation of a ventilation for a store, with the connection. Includes the connection and fastening. Measured per unit installed.',
    'Instalación de ventilación de dormitorio., con conexión. Incluye la conexión y la fijación. Medido por unidad instalada.':
        'Installation of a bedroom ventilation, with the connection. Includes the connection and fastening. Measured per unit installed.',
    'Instalación de ventilación de estudio., con conexión. Incluye la conexión y la fijación. Medido por unidad instalada.':
        'Installation of a study ventilation, with the connection. Includes the connection and fastening. Measured per unit installed.',
    'Instalación de ventilación de garaje., con conexión. Incluye la conexión y la fijación. Medido por unidad instalada.':
        'Installation of a garage ventilation, with the connection. Includes the connection and fastening. Measured per unit installed.',
    'Instalación de ventilación de lavandería., con conexión. Incluye la conexión y la fijación. Medido por unidad instalada.':
        'Installation of a laundry room ventilation, with the connection. Includes the connection and fastening. Measured per unit installed.',
    'Instalación de ventilación de local., con conexión. Incluye la conexión y la fijación. Medido por unidad instalada.':
        'Installation of a ventilation for premises, with the connection. Includes the connection and fastening. Measured per unit installed.',
    'Instalación de ventilación de oficina., con conexión. Incluye la conexión y la fijación. Medido por unidad instalada.':
        'Installation of an office ventilation, with the connection. Includes the connection and fastening. Measured per unit installed.',
    'Instalación de ventilación de sala., con conexión. Incluye la conexión y la fijación. Medido por unidad instalada.':
        'Installation of a living room ventilation, with the connection. Includes the connection and fastening. Measured per unit installed.',
    'Instalación de ventilación de sótano., con conexión. Incluye la conexión y la fijación. Medido por unidad instalada.':
        'Installation of a basement ventilation, with the connection. Includes the connection and fastening. Measured per unit installed.',
    'Instalación de ventilación de terraza., con conexión. Incluye la conexión y la fijación. Medido por unidad instalada.':
        'Installation of a terrace ventilation, with the connection. Includes the connection and fastening. Measured per unit installed.',
    'Instalación de ventilador de baño con sensor., con conexión. Incluye la conexión. Medido por unidad instalada.':
        'Installation of a bathroom fan with a sensor, with the connection. Includes the connection. Measured per unit installed.',
    'Instalación de ventilador de pared., con conexión. Incluye la conexión y la fijación. Medido por unidad instalada.':
        'Installation of a wall fan, with the connection. Includes the connection and fastening. Measured per unit installed.',
    'Instalación de ventilador de piso., con conexión. Incluye la conexión y la fijación. Medido por unidad instalada.':
        'Installation of a pedestal fan, with the connection. Includes the connection and fastening. Measured per unit installed.',
    'Instalación de ventilador de techo., con conexión. Incluye la conexión y la fijación. Medido por unidad instalada.':
        'Installation of a ceiling fan, with the connection. Includes the connection and fastening. Measured per unit installed.',
    'Instalación de videoportero con cámara., con conexión y configuración. Incluye la conexión. Medido por unidad instalada.':
        'Installation of a video door entry system with a camera, with the connection and configuration. Includes the connection. Measured per unit installed.',
    'Instalación de videoportero con monitor., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of a video door entry system with a monitor, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de videoportero inalámbrico., con conexión y configuración. Incluye la conexión y la configuración. Medido por unidad instalada.':
        'Installation of a wireless video door entry system, with the connection and configuration. Includes the connection and configuration. Measured per unit installed.',
    'Instalación de válvula de flotante., con conexión y puesta en marcha. Incluye la conexión y la puesta en marcha. Medido por unidad instalada.':
        'Installation of a float valve, with the connection and commissioning. Includes the connection and commissioning. Measured per unit installed.',
}
