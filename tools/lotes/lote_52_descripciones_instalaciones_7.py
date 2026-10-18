# -*- coding: utf-8 -*-
"""Descripciones — Instalaciones (7 de 8): domótica y protección contra rayos.

Vocabulario aplicado:

· En domótica, scene es la escena y scene controller el «pulsador de
  escenas»; actuator es el actuador y trigger el disparo.
· «Enchufe inteligente» es smart plug, y «carga enchufable» es plug-in
  load.
· «Final de carrera» es limit switch.
· En protección contra rayos se sigue la terminología de la IEC 62305:
  air terminal es el captador, air termination mesh la malla captadora,
  down conductor la bajante y earth termination system la puesta a
  tierra. «Pararrayos con dispositivo de cebado» es early streamer
  emission conductor, que es como se comercializa fuera de España.
· «Cumbrera» es ridge y «paramento» es wall face; las grapas de la
  bajante van separadas de él, stand-off, para no retener humedad.
· «Remate» de cubierta es parapet.
"""

LOTE = {
    "Suministro e instalación de módulo regulador (dimmer) para atenuación de iluminación, integrado en la central domótica. Incluye la verificación de compatibilidad de la carga a regular, el montaje, la conexión, la configuración y la prueba de atenuación en todo el rango. Medido por módulo instalado.":
        "Supply and installation of a dimmer module for lighting control, integrated into the home automation controller. Includes checking the compatibility of the load to be dimmed, mounting, the connection, the configuration and the dimming test across the whole range. Measured per module installed.",

    "Suministro e instalación de módulo de control de persiana, cortina o toldo motorizado, con detección de final de carrera, integrado en la central domótica. Incluye la verificación del motor existente, el montaje del módulo, la conexión, la configuración de los finales de carrera y la prueba de subida y bajada. Medido por módulo instalado.":
        "Supply and installation of a control module for a motorized blind, curtain or awning, with limit switch detection, integrated into the home automation controller. Includes checking the existing motor, mounting the module, the connection, setting the limit switches and the raising and lowering test. Measured per module installed.",

    "Suministro e instalación de módulo de enchufe inteligente para medición y control on/off de cargas enchufables, integrado en la central domótica. Incluye la verificación de la carga a controlar, la conexión o emparejamiento y la prueba de conmutación y medición. Medido por módulo instalado.":
        "Supply and installation of a smart plug module for metering and on/off control of plug-in loads, integrated into the home automation controller. Includes checking the load to be controlled, the connection or pairing and the switching and metering test. Measured per module installed.",

    "Suministro e instalación de termostato inteligente para control de climatización, con programación horaria y comunicación a la central domótica. Incluye la elección del punto de montaje en zona representativa, la fijación, la conexión de alimentación y de la señal de control del equipo de climatización, la configuración de horarios y la prueba de regulación. Medido por termostato instalado.":
        "Supply and installation of a smart thermostat for air conditioning control, with time scheduling and communication to the home automation controller. Includes choosing the mounting point in a representative zone, fastening, the power connection and the control signal connection to the air conditioning unit, setting the schedules and the control test. Measured per thermostat installed.",

    "Suministro e instalación de panel táctil de pared para control y visualización del sistema domótico, con su caja de empotrar. Incluye el replanteo del punto de montaje accesible, la apertura del hueco, el montaje enrasado, la conexión de alimentación y datos, y la configuración de las pantallas y accesos. Medido por panel instalado.":
        "Supply and installation of a wall mounted touch panel for control and display of the home automation system, with its recessed back box. Includes the field layout of the accessible mounting point, cutting the opening, flush mounting, the power and data connections, and configuring the screens and the access levels. Measured per panel installed.",

    "Suministro e instalación de teclado o pulsador de escenas para activación directa de ambientes preconfigurados, integrado en la central domótica. Incluye el montaje en caja empotrada, la conexión, la configuración de las escenas y la prueba de activación. Medido por teclado instalado.":
        "Supply and installation of a keypad or scene controller for direct activation of preconfigured scenes, integrated into the home automation controller. Includes mounting in a recessed box, the connection, configuring the scenes and the activation test. Measured per keypad installed.",

    "Programación de las escenas y automatizaciones del sistema domótico sobre la central configurada: horarios, disparos por sensores y acciones sobre actuadores. Incluye el levantamiento de las rutinas solicitadas por el cliente, la creación y ajuste de cada escena, y la entrega de un listado de las automatizaciones configuradas para su validación. Medido por programación completa del sistema.":
        "Programming of the scenes and automations of the home automation system on the configured controller: schedules, triggers from sensors and actions on actuators. Includes identifying the routines requested by the client, creating and adjusting each scene, and delivering a list of the configured automations for validation. Measured per complete system programming.",

    "Prueba y verificación del sistema domótico completo: comunicación de todos los dispositivos, respuesta de sensores y actuadores, y funcionamiento de las escenas programadas. Incluye la inspección de todas las conexiones, la prueba de cada zona, la corrección de los desajustes detectados y el informe de resultados. Medido por sistema verificado.":
        "Testing and verification of the complete home automation system: communication of all the devices, response of the sensors and actuators, and operation of the programmed scenes. Includes inspecting all the connections, testing each zone, correcting any faults found and the results report. Measured per system verified.",

    "Suministro e instalación de pararrayos con dispositivo de cebado (PDA), sobre mástil en cubierta, con su contador de descargas y conexión a la bajante. Incluye el replanteo del punto de captación para cubrir el volumen protegido, el montaje y arriostramiento del mástil, la fijación de la cabeza captadora, el intercalado del contador de descargas en la bajante, la conexión mecánica y eléctrica al conductor de bajada y la protección anticorrosión de las uniones. Medido por unidad instalada.":
        "Supply and installation of an early streamer emission lightning rod, on a mast on the roof, with its lightning strike counter and connection to the down conductor. Includes the field layout of the air terminal to cover the protected volume, mounting and bracing the mast, fastening the air terminal, inserting the strike counter in the down conductor, the mechanical and electrical connection to the down conductor and corrosion protection of the joints. Measured per unit installed.",

    "Suministro e instalación de pararrayos tipo Franklin de punta simple, sobre soporte en cubierta o remate, con conexión a la bajante. Incluye el replanteo del punto de captación, el montaje del soporte, la fijación de la punta captadora, la conexión al conductor de bajada y la protección de las uniones. Medido por unidad instalada.":
        "Supply and installation of a single point Franklin lightning rod, on a support on the roof or on a parapet, with connection to the down conductor. Includes the field layout of the air terminal, mounting the support, fastening the air terminal, the connection to the down conductor and protection of the joints. Measured per unit installed.",

    "Ejecución de malla captadora sobre cubierta (jaula de Faraday), con conductor de cobre desnudo formando retícula y sus soportes de fijación. Incluye el replanteo de la retícula según la clase de protección requerida, la fijación de los soportes sin perforar la impermeabilización, el tendido del conductor con las uniones soldadas o amordazadas y la conexión a las bajantes en los puntos previstos. Medido por metro cuadrado de cubierta protegida.":
        "Installation of an air termination mesh on the roof (Faraday cage), with bare copper conductor forming a grid and its fastening supports. Includes the field layout of the grid according to the required class of protection, fastening the supports without puncturing the waterproofing, running the conductor with welded or clamped joints and the connection to the down conductors at the intended points. Measured per square meter of roof protected.",

    "Suministro y tendido de conductor captador de cobre desnudo sobre cumbrera y perímetro de cubierta, con sus soportes de fijación. Incluye el replanteo del recorrido, la fijación de los soportes, el tendido del conductor y las uniones a las bajantes. Medido por metro lineal de conductor instalado.":
        "Supply and installation of a bare copper air termination conductor on the ridge and the perimeter of the roof, with its fastening supports. Includes the field layout of the route, fastening the supports, running the conductor and the joints to the down conductors. Measured per linear meter of conductor installed.",

    "Suministro y tendido de bajante de cobre desnudo desde el captador hasta la puesta a tierra, con sus grapas de fijación separadas del paramento. Incluye el replanteo del recorrido más corto y recto, la fijación de las grapas, el tendido del conductor sin dobleces cerrados y la conexión en ambos extremos. Medido por metro lineal de bajante instalada.":
        "Supply and installation of a bare copper down conductor from the air terminal through to the grounding system, with its fastening clips held off the wall face. Includes the field layout of the shortest and straightest route, fastening the clips, running the conductor without tight bends and the connection at both ends. Measured per linear meter of down conductor installed.",
}
