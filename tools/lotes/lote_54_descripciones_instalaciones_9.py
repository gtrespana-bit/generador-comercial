# -*- coding: utf-8 -*-
"""Descripciones — Instalaciones (9 de 9): respaldo, ascensores, pruebas,
puestas en marcha y reparaciones.

Vocabulario aplicado:

· «Tablero de transferencia» es transfer switch, y su «enclavamiento»
  es interlock: es la pieza que impide que las dos fuentes se conecten
  a la vez, que es de lo que va esta partida.
· «Hueco de ascensor» es hoistway en inglés americano (lift shaft es
  la forma británica, que pone la variante); «foso» es pit y «cabina»
  es car, no cabin.
· «Adecuación» de un hueco es preparation: se deja listo, no se
  construye.
· «Puesta en marcha» es commissioning, así que «sistema puesto en
  marcha» se mide per system commissioned.
· «Desatasco» es clearing the blockage, y «grifería» son faucets en
  inglés americano (taps en británico, que pone la variante).
· «Protecciones» de un tablero son protective devices, que es como se
  llama a los interruptores automáticos en el oficio.
"""

LOTE = {
    "Instalación de sistema de respaldo eléctrico con inversor, banco de baterías y su cableado de potencia. Incluye la comprobación del emplazamiento en cuanto a ventilación del banco de baterías, que emite gases durante la carga y no admite un recinto cerrado, el montaje del soporte o rack, la interconexión de baterías con cable de sección adecuada y torque controlado, la conexión del inversor al tablero con su protección, la configuración de parámetros de carga y la prueba de autonomía. El equipo lo elige el cliente y se presupuesta aparte. Medido por sistema instalado.":
        "Installation of a backup power system with an inverter, a battery bank and its power cabling. Includes checking the location as regards ventilation of the battery bank, which gives off gas while charging and must not be in a sealed enclosure, mounting the support or rack, interconnecting the batteries with cable of adequate cross section and controlled torque, connecting the inverter to the board with its protection, setting the charging parameters and the autonomy test. The equipment is selected by the client and priced separately. Measured per system installed.",

    "Instalación de tablero de transferencia, manual o automática, entre el suministro de red y el sistema de respaldo. La transferencia debe garantizar que ambas fuentes nunca queden conectadas a la vez, condición que protege tanto al equipo de respaldo como al personal de la compañía suministradora que pudiera estar trabajando en la línea. Incluye el montaje del tablero, la conexión de las tres líneas de red, respaldo y carga, la verificación del enclavamiento mecánico o eléctrico, la programación de tiempos en las automáticas y la prueba completa de transferencia y retransferencia. Medido por tablero instalado y probado.":
        "Installation of a manual or automatic transfer switch between the mains supply and the backup system. The transfer must guarantee that both sources are never connected at the same time, a condition that protects both the backup equipment and the supply company personnel who may be working on the line. Includes mounting the board, connecting the three lines of mains, backup and load, verifying the mechanical or electrical interlock, programming the timings on automatic units and the full transfer and retransfer test. Measured per board installed and tested.",

    "Instalación de ascensor unifamiliar, con estructura, cabina y control. Incluye el montaje de la estructura, la cabina y la puesta en marcha. Medido por unidad instalada.":
        "Installation of a home elevator, with the structure, the car and the controller. Includes the assembly of the structure, the car and setting to work. Measured per unit installed.",

    "Adecuación de hueco para ascensor. Incluye la preparación del hueco. Medido por unidad adecuada.":
        "Preparation of the hoistway for an elevator. Includes preparing the hoistway. Measured per hoistway prepared.",

    "Instalación de ascensor hidráulico. Incluye el montaje de la unidad hidráulica y la cabina. Medido por unidad instalada.":
        "Installation of a hydraulic elevator. Includes the assembly of the hydraulic power unit and the car. Measured per unit installed.",

    "Adecuación de foso de ascensor. Incluye la preparación del foso. Medido por unidad adecuada.":
        "Preparation of the elevator pit. Includes preparing the pit. Measured per pit prepared.",

    "Prueba hidráulica de instalación de agua. Incluye la presurización y la verificación. Medido por instalación probada.":
        "Hydraulic test of the water installation. Includes pressurizing and verifying. Measured per installation tested.",

    "Prueba de instalación eléctrica con medición de continuidad y aislamiento. Incluye la medición y el informe. Medido por instalación probada.":
        "Testing of the electrical installation with continuity and insulation measurement. Includes the measurement and the report. Measured per installation tested.",

    "Prueba de estanqueidad de instalación de gas. Incluye la presurización y la verificación. Medido por instalación probada.":
        "Tightness test of the gas installation. Includes pressurizing and verifying. Measured per installation tested.",

    "Puesta en marcha de sistema de climatización. Incluye la verificación y el ajuste. Medido por sistema puesto en marcha.":
        "Commissioning of the air conditioning system. Includes the verification and the adjustment. Measured per system commissioned.",

    "Puesta en marcha de sistema de bombeo. Incluye la verificación y el ajuste. Medido por sistema puesto en marcha.":
        "Commissioning of the pumping system. Includes the verification and the adjustment. Measured per system commissioned.",

    "Puesta en marcha de sistema eléctrico de respaldo. Incluye la verificación y el ajuste. Medido por sistema puesto en marcha.":
        "Commissioning of the backup power system. Includes the verification and the adjustment. Measured per system commissioned.",

    "Puesta en marcha de sistema domótico. Incluye la configuración y la verificación. Medido por sistema puesto en marcha.":
        "Commissioning of the home automation system. Includes the configuration and the verification. Measured per system commissioned.",

    "Puesta en marcha de sistema contra incendios. Incluye la verificación. Medido por sistema puesto en marcha.":
        "Commissioning of the fire protection system. Includes the verification. Measured per system commissioned.",

    "Puesta en marcha de sistema solar fotovoltaico. Incluye la verificación y el ajuste. Medido por sistema puesto en marcha.":
        "Commissioning of the photovoltaic solar system. Includes the verification and the adjustment. Measured per system commissioned.",

    "Reparación de fuga en tubería de agua. Incluye la localización y la reparación. Medido por reparación ejecutada.":
        "Repair of a leak in a water pipe. Includes locating and repairing it. Measured per repair carried out.",

    "Reparación de punto eléctrico averiado. Incluye la localización y la reparación. Medido por reparación ejecutada.":
        "Repair of a faulty electrical point. Includes locating and repairing it. Measured per repair carried out.",

    "Reparación de desagüe obstruido. Incluye la localización y el desatasco. Medido por reparación ejecutada.":
        "Repair of a blocked drain. Includes locating and clearing the blockage. Measured per repair carried out.",

    "Reparación de grifería con sustitución de piezas. Incluye la reparación. Medido por reparación ejecutada.":
        "Repair of faucets with replacement of parts. Includes the repair. Measured per repair carried out.",

    "Reparación de luminaria con sustitución de componentes. Incluye la reparación. Medido por reparación ejecutada.":
        "Repair of a light fixture with replacement of components. Includes the repair. Measured per repair carried out.",

    "Reparación de equipo de climatización. Incluye el diagnóstico y la reparación. Medido por reparación ejecutada.":
        "Repair of an air conditioning unit. Includes the diagnosis and the repair. Measured per repair carried out.",

    "Reparación de tablero eléctrico. Incluye la sustitución de protecciones. Medido por reparación ejecutada.":
        "Repair of an electrical panel. Includes the replacement of the protective devices. Measured per repair carried out.",

    "Reparación de sistema de seguridad o alarma. Incluye el diagnóstico y la reparación. Medido por reparación ejecutada.":
        "Repair of a security or alarm system. Includes the diagnosis and the repair. Measured per repair carried out.",
}
