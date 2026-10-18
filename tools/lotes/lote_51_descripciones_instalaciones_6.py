# -*- coding: utf-8 -*-
"""Descripciones — Instalaciones (6 de 6): detección, incendios y domótica.

Vocabulario aplicado:

· «Central» de una instalación es control panel (la de incendios es fire
  alarm control panel); el controller es la central domótica.
· «Lazo» es loop, tal cual, en detección de incendios direccionable.
· «Detector autónomo» es standalone detector y «direccionable» es
  addressable detector; son los dos términos del oficio.
· «Red de agua contra incendios» es fire mains.
· «Punto de instalación» para un dispositivo es installation point, que
  es lo que se cobra cuando el aparato lo pone el cliente.
· «Contralmbre... » no: «contraluz» es backlighting, y es el motivo por
  el que una cámara mal colocada no ve nada.
· «Emparejamiento» es pairing, no matching ni coupling.
· «Contacto magnético» es magnetic contact: en seguridad se llama así,
  no magnetic switch.
· «Persiana» en domótica es blind.
"""

LOTE = {
    "Instalación de detector de humo con su base, conexión y prueba, integrado o autónomo según el sistema. Incluye el replanteo de la posición en el techo respetando la separación mínima a paredes, vigas y difusores de aire, ya que colocado junto a una rejilla de impulsión el flujo de aire desvía el humo y retrasa la detección, el montaje de la base, la conexión al lazo o la colocación de la batería en los autónomos, la programación de la dirección cuando corresponda y la prueba con generador de humo. Medido por unidad instalada y probada.":
        "Installation of a smoke detector with its base, connection and test, addressable or standalone depending on the system. Includes the field layout of the position on the ceiling respecting the minimum distance from walls, beams and air diffusers, because placed next to a supply air grille the airflow deflects the smoke and delays detection, mounting the base, connection to the loop or fitting the battery on standalone units, programming the address where applicable and the test with a smoke generator. Measured per unit installed and tested.",

    "Instalación de gabinete contra incendios con su manguera, válvula, boquilla y conexión a la red. Incluye el replanteo en posición visible y accesible del recorrido de evacuación, el empotrado o anclaje del gabinete, la conexión a la red de agua contra incendios con su válvula, el plegado correcto de la manguera para que salga sin enredarse al tirar, la señalización y la prueba de presión y caudal en boquilla. Medido por unidad instalada y probada.":
        "Installation of a fire hose cabinet with its hose, valve, nozzle and connection to the system. Includes the field layout in a visible and accessible position on the escape route, recessing or anchoring the cabinet, connection to the fire mains with its valve, folding the hose correctly so that it pays out without tangling when pulled, the signage and the pressure and flow test at the nozzle. Measured per unit installed and tested.",

    "Punto de instalación para sensor de alarma, cámara de videovigilancia o lector de control de acceso, con su canalización, cableado y caja. Incluye el replanteo de la posición atendiendo al ángulo de cobertura del dispositivo y evitando contraluces en el caso de cámaras, la canalización independiente, el tendido del cable hasta la central o grabador, el conectorizado, el montaje del dispositivo y la prueba de funcionamiento y de cobertura. El equipo lo elige el cliente y se presupuesta aparte. Medido por punto terminado y probado.":
        "Installation point for an alarm sensor, CCTV camera or access control reader, with its containment, cabling and back box. Includes the field layout of the position taking into account the coverage angle of the device and avoiding backlighting in the case of cameras, the independent containment, running the cable through to the control panel or recorder, terminating, mounting the device and the operational and coverage test. The equipment is selected by the client and priced separately. Measured per point completed and tested.",

    "Suministro, instalación y configuración inicial de la central domótica o controlador principal, con su fuente de alimentación y su conexión a la red local. Incluye el replanteo del punto de montaje accesible, la fijación del equipo, la alimentación y conexión de red, la puesta en hora y asignación de dirección, y la verificación de que la central se comunica con los módulos previstos. Medido por central instalada.":
        "Supply, installation and initial configuration of the home automation controller or main controller, with its power supply and its connection to the local network. Includes the field layout of the accessible mounting point, fixing the unit, the power supply and network connection, setting the time and assigning the address, and verifying that the controller communicates with the intended modules. Measured per controller installed.",

    "Suministro e instalación de pasarela de comunicación que integra protocolos de distintos fabricantes con la central domótica. Incluye la elección de la pasarela según los dispositivos a integrar, su montaje junto a la central, la conexión de alimentación y datos, y el emparejamiento y verificación de los dispositivos a través de la pasarela. Medido por pasarela instalada.":
        "Supply and installation of a communication gateway that integrates protocols from different manufacturers with the home automation controller. Includes choosing the gateway according to the devices to be integrated, mounting it next to the controller, the power and data connections, and pairing and verifying the devices through the gateway. Measured per gateway installed.",

    "Suministro e instalación de repetidor o extensor de señal inalámbrica para ampliar la cobertura de la red domótica en viviendas o locales con zonas de baja señal. Incluye la elección del punto de instalación intermedio, la fijación, la alimentación y la verificación de la mejora de cobertura. Medido por repetidor instalado.":
        "Supply and installation of a wireless signal repeater or extender to extend the coverage of the home automation network in dwellings or premises with low signal areas. Includes choosing the intermediate installation point, fixing, the power supply and verifying the improvement in coverage. Measured per repeater installed.",

    "Suministro e instalación de sensor de movimiento o presencia, con su soporte de montaje y su integración en la central domótica. Incluye el replanteo del punto de detección para cubrir la zona prevista, la fijación del soporte, la conexión y el emparejamiento con la central, y la prueba de detección y de alcance. Medido por sensor instalado.":
        "Supply and installation of a motion or occupancy sensor, with its mounting bracket and its integration into the home automation controller. Includes the field layout of the detection point to cover the intended area, fixing the bracket, the connection and pairing with the controller, and the detection and range test. Measured per sensor installed.",

    "Suministro e instalación de sensor magnético de apertura para puertas y ventanas, con su emisor y soporte, integrado en la central domótica. Incluye el replanteo del punto de montaje, la fijación del imán y del emisor alineados, la conexión o emparejamiento y la prueba de apertura y cierre. Medido por sensor instalado.":
        "Supply and installation of a magnetic door and window contact, with its transmitter and bracket, integrated into the home automation controller. Includes the field layout of the mounting point, fixing the magnet and the transmitter in line, the connection or pairing and the opening and closing test. Measured per sensor installed.",

    "Suministro e instalación de sensor de temperatura y humedad ambiente, integrado en la central domótica para la regulación de climatización. Incluye la elección del punto de medición representativo, alejado de fuentes de calor y corrientes, la fijación, el emparejamiento y la verificación de la lectura. Medido por sensor instalado.":
        "Supply and installation of a room temperature and humidity sensor, integrated into the home automation controller for air conditioning control. Includes choosing a representative measurement point, away from heat sources and drafts, fixing, pairing and verifying the reading. Measured per sensor installed.",

    "Suministro e instalación de detector de inundación o fuga de agua por contacto, con aviso a la central domótica. Incluye el replanteo en el punto más bajo de la zona a vigilar, la fijación del sensor, su emparejamiento y la prueba de detección humedeciendo el contacto. Medido por detector instalado.":
        "Supply and installation of a water leak or flood contact detector, with an alarm to the home automation controller. Includes the field layout at the lowest point of the area to be monitored, fixing the sensor, pairing it and the detection test by wetting the contact. Measured per detector installed.",

    "Suministro e instalación de detector de gas doméstico con alarma local y comunicación a la central domótica. Incluye la elección del punto de montaje según la densidad del gas detectado, la fijación, la conexión de alimentación, el emparejamiento y la prueba de detección. Medido por detector instalado.":
        "Supply and installation of a domestic gas detector with a local alarm and communication to the home automation controller. Includes choosing the mounting point according to the density of the gas being detected, fixing, the power connection, pairing and the detection test. Measured per detector installed.",

    "Suministro e instalación de sensor de nivel de luz para automatización de iluminación y persianas, integrado en la central domótica. Incluye el replanteo del punto con exposición representativa, la fijación, el emparejamiento y la calibración del umbral de disparo. Medido por sensor instalado.":
        "Supply and installation of a light level sensor for automation of lighting and blinds, integrated into the home automation controller. Includes the field layout of the point with representative exposure, fixing, pairing and calibration of the trigger threshold. Measured per sensor installed.",

    "Suministro e instalación de módulo de actuación on/off (relé) para control de circuitos de iluminación y cargas, integrado en la central domótica. Incluye el montaje en el tablero o en caja empotrada, la conexión del circuito de potencia y de la señal de control, la configuración y la prueba de conmutación. Medido por módulo instalado.":
        "Supply and installation of an on/off actuator module (relay) for controlling lighting circuits and loads, integrated into the home automation controller. Includes mounting in the panel or in a recessed box, connection of the power circuit and of the control signal, the configuration and the switching test. Measured per module installed.",
}
