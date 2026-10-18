# -*- coding: utf-8 -*-
"""Descripciones — Instalaciones (3 de 4): luminarias y red de datos.

Bloque escrito con plantilla porque el catálogo repite la misma cola en
cada variante. La cola se respeta literalmente y solo cambia la cabeza,
que es lo que nombra el elemento instalado.

«Luminaria» es light fixture, el «aplique» es wall light y el «reflector»
es floodlight. El «punto de datos» es data outlet, y su canalización tiene
que ser independiente de la de fuerza: el paralelismo con conductores de
potencia induce interferencias que degradan la señal.
"""

LOTE = {
    "Instalación de luminaria led empotrada., con conexión y fijación. Incluye la conexión eléctrica y la fijación. Medido por unidad instalada.":
        "Installation of a recessed LED light fixture, with the connection and fastening. Includes the electrical connection and fastening. Measured per unit installed.",
    "Instalación de luminaria de pared., con conexión y fijación. Incluye la conexión eléctrica y la fijación. Medido por unidad instalada.":
        "Installation of a wall light fixture, with the connection and fastening. Includes the electrical connection and fastening. Measured per unit installed.",
    "Instalación de aplique de exterior., con conexión y fijación. Incluye la conexión eléctrica y la fijación. Medido por unidad instalada.":
        "Installation of an external wall light, with the connection and fastening. Includes the electrical connection and fastening. Measured per unit installed.",
    "Instalación de luminaria de emergencia., con conexión y fijación. Incluye la conexión eléctrica y la fijación. Medido por unidad instalada.":
        "Installation of an emergency light fixture, with the connection and fastening. Includes the electrical connection and fastening. Measured per unit installed.",
    "Instalación de foco de piso., con conexión y fijación. Incluye la conexión eléctrica y la fijación. Medido por unidad instalada.":
        "Installation of a floor uplight, with the connection and fastening. Includes the electrical connection and fastening. Measured per unit installed.",
    "Instalación de luminaria de closet., con conexión y fijación. Incluye la conexión eléctrica y la fijación. Medido por unidad instalada.":
        "Installation of a closet light fixture, with the connection and fastening. Includes the electrical connection and fastening. Measured per unit installed.",
    "Instalación de luminaria de espejo., con conexión y fijación. Incluye la conexión eléctrica y la fijación. Medido por unidad instalada.":
        "Installation of a mirror light, with the connection and fastening. Includes the electrical connection and fastening. Measured per unit installed.",
    "Instalación de tira led en zócalo., con conexión y fijación. Incluye la conexión eléctrica y la fijación. Medido por unidad instalada.":
        "Installation of an LED strip in the baseboard, with the connection and fastening. Includes the electrical connection and fastening. Measured per unit installed.",
    "Instalación de luminaria colgante., con conexión y fijación. Incluye la conexión eléctrica y la fijación. Medido por unidad instalada.":
        "Installation of a pendant light fixture, with the connection and fastening. Includes the electrical connection and fastening. Measured per unit installed.",
    "Instalación de luminaria de techo., con conexión y fijación. Incluye la conexión eléctrica y la fijación. Medido por unidad instalada.":
        "Installation of a ceiling light fixture, with the connection and fastening. Includes the electrical connection and fastening. Measured per unit installed.",
    "Instalación de reflector con sensor., con conexión y fijación. Incluye la conexión eléctrica y la fijación. Medido por unidad instalada.":
        "Installation of a sensor floodlight, with the connection and fastening. Includes the electrical connection and fastening. Measured per unit installed.",
    "Instalación de luminaria de riel., con conexión y fijación. Incluye la conexión eléctrica y la fijación. Medido por unidad instalada.":
        "Installation of a track light fixture, with the connection and fastening. Includes the electrical connection and fastening. Measured per unit installed.",
    "Instalación de luminaria de piscina., con conexión y fijación. Incluye la conexión eléctrica y la fijación. Medido por unidad instalada.":
        "Installation of a pool light fixture, with the connection and fastening. Includes the electrical connection and fastening. Measured per unit installed.",
    "Instalación de luminaria de jardín., con conexión y fijación. Incluye la conexión eléctrica y la fijación. Medido por unidad instalada.":
        "Installation of a garden light fixture, with the connection and fastening. Includes the electrical connection and fastening. Measured per unit installed.",
    "Instalación de luminaria de garaje., con conexión y fijación. Incluye la conexión eléctrica y la fijación. Medido por unidad instalada.":
        "Installation of a garage light fixture, with the connection and fastening. Includes the electrical connection and fastening. Measured per unit installed.",
    "Instalación de luminaria de escalera., con conexión y fijación. Incluye la conexión eléctrica y la fijación. Medido por unidad instalada.":
        "Installation of a stair light fixture, with the connection and fastening. Includes the electrical connection and fastening. Measured per unit installed.",
    "Instalación de luminaria decorativa., con conexión y fijación. Incluye la conexión eléctrica y la fijación. Medido por unidad instalada.":
        "Installation of a decorative light fixture, with the connection and fastening. Includes the electrical connection and fastening. Measured per unit installed.",
    "Instalación de luminaria de oficina., con conexión y fijación. Incluye la conexión eléctrica y la fijación. Medido por unidad instalada.":
        "Installation of an office light fixture, with the connection and fastening. Includes the electrical connection and fastening. Measured per unit installed.",
    "Instalación de luminaria de baño., con conexión y fijación. Incluye la conexión eléctrica y la fijación. Medido por unidad instalada.":
        "Installation of a bathroom light fixture, with the connection and fastening. Includes the electrical connection and fastening. Measured per unit installed.",
    "Instalación de luminaria de cocina., con conexión y fijación. Incluye la conexión eléctrica y la fijación. Medido por unidad instalada.":
        "Installation of a kitchen light fixture, with the connection and fastening. Includes the electrical connection and fastening. Measured per unit installed.",
    "Instalación de luminaria de sala., con conexión y fijación. Incluye la conexión eléctrica y la fijación. Medido por unidad instalada.":
        "Installation of a living room light fixture, with the connection and fastening. Includes the electrical connection and fastening. Measured per unit installed.",
    "Instalación de luminaria de dormitorio., con conexión y fijación. Incluye la conexión eléctrica y la fijación. Medido por unidad instalada.":
        "Installation of a bedroom light fixture, with the connection and fastening. Includes the electrical connection and fastening. Measured per unit installed.",
    "Instalación de luminaria de pasillo., con conexión y fijación. Incluye la conexión eléctrica y la fijación. Medido por unidad instalada.":
        "Installation of a corridor light fixture, with the connection and fastening. Includes the electrical connection and fastening. Measured per unit installed.",
    "Instalación de luminaria de fachada., con conexión y fijación. Incluye la conexión eléctrica y la fijación. Medido por unidad instalada.":
        "Installation of a facade light fixture, with the connection and fastening. Includes the electrical connection and fastening. Measured per unit installed.",
    "Instalación de luminaria de terraza., con conexión y fijación. Incluye la conexión eléctrica y la fijación. Medido por unidad instalada.":
        "Installation of a terrace light fixture, with the connection and fastening. Includes the electrical connection and fastening. Measured per unit installed.",
    "Instalación de luminaria de lavandería., con conexión y fijación. Incluye la conexión eléctrica y la fijación. Medido por unidad instalada.":
        "Installation of a laundry room light fixture, with the connection and fastening. Includes the electrical connection and fastening. Measured per unit installed.",
    "Instalación de luminaria de recibidor., con conexión y fijación. Incluye la conexión eléctrica y la fijación. Medido por unidad instalada.":
        "Installation of a hall light fixture, with the connection and fastening. Includes the electrical connection and fastening. Measured per unit installed.",
    "Instalación de luminaria de comedor., con conexión y fijación. Incluye la conexión eléctrica y la fijación. Medido por unidad instalada.":
        "Installation of a dining room light fixture, with the connection and fastening. Includes the electrical connection and fastening. Measured per unit installed.",
    "Instalación de luminaria de estudio., con conexión y fijación. Incluye la conexión eléctrica y la fijación. Medido por unidad instalada.":
        "Installation of a study light fixture, with the connection and fastening. Includes the electrical connection and fastening. Measured per unit installed.",
    "Ejecución de punto de datos para computadora., con canalización y conexión. Incluye el tendido del cable y la conexión. Medido por punto ejecutado.":
        "Installation of a data outlet for a computer, with conduit and connection. Includes laying the cable and the connection. Measured per point constructed.",
    "Ejecución de punto de teléfono., con canalización y conexión. Incluye el tendido del cable y la conexión. Medido por punto ejecutado.":
        "Installation of a telephone outlet, with conduit and connection. Includes laying the cable and the connection. Measured per point constructed.",
    "Ejecución de punto de televisión., con canalización y conexión. Incluye el tendido del cable y la conexión. Medido por punto ejecutado.":
        "Installation of a television outlet, with conduit and connection. Includes laying the cable and the connection. Measured per point constructed.",
    "Ejecución de punto de red inalámbrica., con canalización y conexión. Incluye el tendido del cable y la conexión. Medido por punto ejecutado.":
        "Installation of a wireless access point outlet, with conduit and connection. Includes laying the cable and the connection. Measured per point constructed.",
    "Ejecución de punto de datos doble., con canalización y conexión. Incluye el tendido del cable y la conexión. Medido por punto ejecutado.":
        "Installation of a double data outlet, with conduit and connection. Includes laying the cable and the connection. Measured per point constructed.",
    "Ejecución de punto de fibra óptica., con canalización y conexión. Incluye el tendido del cable y la conexión. Medido por punto ejecutado.":
        "Installation of a fiber optic outlet, with conduit and connection. Includes laying the cable and the connection. Measured per point constructed.",
    "Ejecución de punto de datos en piso., con canalización y conexión. Incluye el tendido del cable y la conexión. Medido por punto ejecutado.":
        "Installation of a data outlet in the floor, with conduit and connection. Includes laying the cable and the connection. Measured per point constructed.",
    "Ejecución de punto de datos en pared., con canalización y conexión. Incluye el tendido del cable y la conexión. Medido por punto ejecutado.":
        "Installation of a data outlet in the wall, with conduit and connection. Includes laying the cable and the connection. Measured per point constructed.",
    "Ejecución de punto de datos para televisor., con canalización y conexión. Incluye el tendido del cable y la conexión. Medido por punto ejecutado.":
        "Installation of a data outlet for a television, with conduit and connection. Includes laying the cable and the connection. Measured per point constructed.",
    "Ejecución de punto de datos para impresora., con canalización y conexión. Incluye el tendido del cable y la conexión. Medido por punto ejecutado.":
        "Installation of a data outlet for a printer, with conduit and connection. Includes laying the cable and the connection. Measured per point constructed.",
    "Ejecución de punto de datos para cámara., con canalización y conexión. Incluye el tendido del cable y la conexión. Medido por punto ejecutado.":
        "Installation of a data outlet for a camera, with conduit and connection. Includes laying the cable and the connection. Measured per point constructed.",
    "Ejecución de punto de datos para audio., con canalización y conexión. Incluye el tendido del cable y la conexión. Medido por punto ejecutado.":
        "Installation of a data outlet for audio, with conduit and connection. Includes laying the cable and the connection. Measured per point constructed.",
    "Ejecución de punto de datos para domótica., con canalización y conexión. Incluye el tendido del cable y la conexión. Medido por punto ejecutado.":
        "Installation of a data outlet for home automation, with conduit and connection. Includes laying the cable and the connection. Measured per point constructed.",
    "Ejecución de punto de teléfono adicional., con canalización y conexión. Incluye el tendido del cable y la conexión. Medido por punto ejecutado.":
        "Installation of an additional telephone outlet, with conduit and connection. Includes laying the cable and the connection. Measured per point constructed.",
    "Ejecución de punto de televisión adicional., con canalización y conexión. Incluye el tendido del cable y la conexión. Medido por punto ejecutado.":
        "Installation of an additional television outlet, with conduit and connection. Includes laying the cable and the connection. Measured per point constructed.",
    "Ejecución de punto de datos en techo., con canalización y conexión. Incluye el tendido del cable y la conexión. Medido por punto ejecutado.":
        "Installation of a data outlet in the ceiling, with conduit and connection. Includes laying the cable and the connection. Measured per point constructed.",
    "Ejecución de punto de datos en cielo raso., con canalización y conexión. Incluye el tendido del cable y la conexión. Medido por punto ejecutado.":
        "Installation of a data outlet in the suspended ceiling, with conduit and connection. Includes laying the cable and the connection. Measured per point constructed.",
    "Ejecución de punto de datos en oficina., con canalización y conexión. Incluye el tendido del cable y la conexión. Medido por punto ejecutado.":
        "Installation of a data outlet in an office, with conduit and connection. Includes laying the cable and the connection. Measured per point constructed.",
    "Ejecución de punto de datos en dormitorio., con canalización y conexión. Incluye el tendido del cable y la conexión. Medido por punto ejecutado.":
        "Installation of a data outlet in a bedroom, with conduit and connection. Includes laying the cable and the connection. Measured per point constructed.",
    "Ejecución de punto de datos en sala., con canalización y conexión. Incluye el tendido del cable y la conexión. Medido por punto ejecutado.":
        "Installation of a data outlet in a living room, with conduit and connection. Includes laying the cable and the connection. Measured per point constructed.",
    "Ejecución de punto de datos en estudio., con canalización y conexión. Incluye el tendido del cable y la conexión. Medido por punto ejecutado.":
        "Installation of a data outlet in a study, with conduit and connection. Includes laying the cable and the connection. Measured per point constructed.",
    "Ejecución de punto de datos en comedor., con canalización y conexión. Incluye el tendido del cable y la conexión. Medido por punto ejecutado.":
        "Installation of a data outlet in a dining room, with conduit and connection. Includes laying the cable and the connection. Measured per point constructed.",
    "Ejecución de punto de datos en terraza., con canalización y conexión. Incluye el tendido del cable y la conexión. Medido por punto ejecutado.":
        "Installation of a data outlet on a terrace, with conduit and connection. Includes laying the cable and the connection. Measured per point constructed.",
    "Ejecución de punto de datos para consola., con canalización y conexión. Incluye el tendido y la conexión. Medido por punto ejecutado.":
        "Installation of a data outlet for a games console, with conduit and connection. Includes laying the cable and the connection. Measured per point constructed.",
    "Ejecución de punto de datos para router., con canalización y conexión. Incluye el tendido y la conexión. Medido por punto ejecutado.":
        "Installation of a data outlet for a router, with conduit and connection. Includes laying the cable and the connection. Measured per point constructed.",
}
