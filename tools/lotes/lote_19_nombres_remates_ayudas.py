# -*- coding: utf-8 -*-
"""Nombres de partida — Remates y ayudas (capítulo completo, 120).

Criterios de este lote:
  · «Ayuda de albañilería» es builder's work: en un presupuesto
    anglosajón es una partida con nombre propio, la obra de albañilería
    que se hace para que otras instalaciones puedan pasar.
  · «Roza» y «regata» son la misma cosa y en inglés son chase.
  · «Recibido de marco» es bedding and fixing: recibir no es instalar, es
    fijar y ajustar en su sitio lo que ya está colocado.
  · «Sellado cortafuego» es firestopping, una sola palabra de oficio.
  · «Vierteaguas» es weather sill y «alféizar» es window sill: la primera
    echa el agua fuera, la segunda es la repisa interior.
  · «Coronación» de un muro es coping, la pieza que lo remata por arriba.
  · «Tapajuntas» es cover strip, la tira que tapa una junta.
"""

LOTE = {
# ── Ayudas de albañilería ─────────────────────────────────────────────────
"Ayuda de albañilería para instalación eléctrica.":
    "Builder's work for the electrical installation.",
"Ayuda de albañilería para instalación sanitaria.":
    "Builder's work for the plumbing installation.",
"Ayuda de albañilería para climatización.":
    "Builder's work for the HVAC installation.",
"Ayuda de albañilería para gas.": "Builder's work for the gas installation.",
"Ayuda de albañilería para datos y telecomunicaciones.":
    "Builder's work for the data and telecommunications installation.",
"Resane general tras instalaciones.":
    "General patching after the installation of services.",
"Ayuda de albañilería para incendios.":
    "Builder's work for the fire protection installation.",
"Ayuda de albañilería para bombeo.":
    "Builder's work for the pumping installation.",
"Ayuda de albañilería para ventilación.":
    "Builder's work for the ventilation installation.",
"Apertura y tapado de paso en muro.":
    "Opening up and making good a penetration in a wall.",
"Apertura y tapado de paso en losa.":
    "Opening up and making good a penetration in a slab.",
"Ayuda de albañilería para solar.":
    "Builder's work for the solar installation.",
"Resane de rozas y pasos.": "Patching of chases and penetrations.",

# ── Rozas y perforaciones ─────────────────────────────────────────────────
"Roza en pared de bloque para instalación.":
    "Chase in a block wall for services.",
"Roza en muro de concreto.": "Chase in a concrete wall.",
"Regata para tubería en pared.": "Chase for pipework in a wall.",
"Roza en techo.": "Chase in a soffit.",
"Regata para cable en piso.": "Chase for cabling in a floor.",
"Roza en bloque de arcilla.": "Chase in a clay block wall.",
"Perforación de paso en muro.": "Drilling of a penetration in a wall.",
"Perforación de paso en losa.": "Drilling of a penetration in a slab.",
"Perforación de mechinal en muro.":
    "Drilling of a small penetration in a wall.",
"Perforación para anclaje.": "Drilling for an anchor.",
"Paso de conducto en losa.": "Penetration for a duct in a slab.",
"Perforación de hueco para caja.": "Cutting of a recess for a box.",
"Paso de tubería en muro con sello.":
    "Penetration for pipework through a wall, sealed.",

# ── Recibidos ─────────────────────────────────────────────────────────────
"Recibido de marco de puerta.": "Bedding and fixing of a door frame.",
"Recibido de marco de ventana.": "Bedding and fixing of a window frame.",
"Recibido de caja de persiana.":
    "Bedding and fixing of a roller shutter box.",
"Recibido de premarco metálico.": "Bedding and fixing of a metal subframe.",
"Recibido de reja.": "Bedding and fixing of a grille.",
"Recibido de aparato sanitario.":
    "Bedding and fixing of a plumbing fixture.",
"Recibido de mesón de cocina.":
    "Bedding and fixing of a kitchen countertop.",
"Recibido de equipo de aire acondicionado.":
    "Bedding and fixing of an air conditioning unit.",
"Recibido de barra de apoyo.": "Bedding and fixing of a grab bar.",
"Recibido de espejo.": "Bedding and fixing of a mirror.",
"Recibido de tanque de agua.": "Bedding and fixing of a water tank.",
"Recibido de equipo de bombeo.":
    "Bedding and fixing of pumping equipment.",
"Recibido de calentador.": "Bedding and fixing of a water heater.",

# ── Sellados ──────────────────────────────────────────────────────────────
"Sellado de junta con silicona sanitaria.":
    "Sealing of a joint with sanitary silicone.",
"Sellado de junta con poliuretano.":
    "Sealing of a joint with polyurethane.",
"Sellado de encuentro piso-pared.":
    "Sealing of the floor and wall junction.",
"Sellado de junta perimetral de ventana.":
    "Sealing of the perimeter joint of a window.",
"Sellado de junta de bañera.": "Sealing of a bathtub joint.",
"Sellado de junta de mesón.": "Sealing of a countertop joint.",
"Sellado de paso de tubería.": "Sealing of a pipe penetration.",
"Sellado de junta de escalera.": "Sealing of a joint in a stair.",
"Remate de encuentro pared-techo.":
    "Finishing of the wall and ceiling junction.",
"Remate de encuentro de materiales.":
    "Finishing of the junction between materials.",
"Remate de junta de dilatación.": "Finishing of an expansion joint.",
"Remate de encuentro de ducha.": "Finishing of a shower junction.",
"Remate de junta de fachada.": "Finishing of a facade joint.",

# ── Vierteaguas y alféizares ──────────────────────────────────────────────
"Vierteaguas de concreto vaciado en sitio.":
    "Cast-in-place concrete weather sill.",
"Alféizar de piedra.": "Stone window sill.",
"Vierteaguas de mortero.": "Mortar weather sill.",
"Alféizar de mármol.": "Marble window sill.",
"Vierteaguas prefabricado.": "Precast weather sill.",
"Alféizar de madera.": "Wood window sill.",
"Vierteaguas de piedra artificial.": "Cast stone weather sill.",
"Vierteaguas de chapa metálica.": "Sheet metal weather sill.",

# ── Coronaciones ──────────────────────────────────────────────────────────
"Coronación de muro con mortero.": "Coping of a wall in mortar.",
"Coronación de muro con pieza.": "Coping of a wall with precast units.",
"Coronación de peto de cubierta.": "Coping of a roof parapet.",
"Coronación con ladrillo visto.": "Coping in facing brick.",
"Coronación de muro con chapa.": "Coping of a wall with sheet metal.",

# ── Bases y soportes ──────────────────────────────────────────────────────
"Base de concreto para equipo.": "Concrete base for equipment.",
"Bancada para equipo de aire.":
    "Plinth for air conditioning equipment.",
"Base para tanque de agua.": "Base for a water tank.",
"Base para planta eléctrica.": "Base for a generator.",
"Base de concreto para bomba.": "Concrete base for a pump.",
"Base de concreto para cámara.": "Concrete base for a chamber.",
"Soporte metálico para equipo.": "Metal support for equipment.",
"Soporte para condensadora.": "Support for a condensing unit.",
"Base de bomba de agua.": "Base for a water pump.",
"Bancada de madera para equipo.": "Timber plinth for equipment.",
"Soporte de calentador.": "Support for a water heater.",
"Base para hidroneumático.": "Base for a hydropneumatic tank.",
"Soporte de panel solar.": "Support for a solar panel.",

# ── Forrados y cajones ────────────────────────────────────────────────────
"Forrado de tubería con placa de yeso.":
    "Boxing in of pipework with drywall.",
"Cajón para instalaciones.": "Service duct.",
"Falso pilar de placa de yeso.": "False column in drywall.",
"Forrado de viga con placa de yeso.": "Boxing in of a beam with drywall.",
"Forrado de conducto de climatización.": "Enclosure of an HVAC duct.",
"Cajón de persiana interior.": "Interior roller shutter box.",
"Forrado de montante de instalación.":
    "Boxing in of a service riser.",
"Forrado de bajante con placa de cemento.":
    "Boxing in of a downpipe with cement board.",
"Cajón para persiana con registro.":
    "Roller shutter box with an access panel.",

# ── Tapajuntas y molduras ─────────────────────────────────────────────────
"Tapajuntas de madera.": "Wood cover strip.",
"Tapajuntas de aluminio.": "Aluminum cover strip.",
"Tapajuntas de MDF.": "MDF cover strip.",
"Remate de tapajuntas de esquina.": "Finishing of a corner cover strip.",
"Tapajuntas de PVC.": "PVC cover strip.",
"Moldura corrida de yeso.": "Continuous plaster molding.",
"Cornisa de yeso.": "Plaster cornice.",
"Perfil de remate decorativo.": "Decorative finishing profile.",
"Moldura de poliuretano.": "Polyurethane molding.",
"Perfil esquinero decorativo.": "Decorative corner profile.",
"Moldura de techo decorativa.": "Decorative ceiling molding.",
"Perfil de transición decorativo.": "Decorative transition profile.",
"Moldura de madera.": "Wood molding.",
"Remate de cenefa de iluminación.": "Finishing of a lighting cove.",
"Remate especial de fachada.": "Special facade trim.",
"Remate de borde de piso.": "Finishing of a floor edge.",
"Remate de escalera.": "Finishing of a stair.",
"Remate de zócalo decorativo.": "Decorative base trim.",
"Remate especial de cielo raso.": "Special ceiling trim.",

# ── Sellados cortafuego ───────────────────────────────────────────────────
"Sellado cortafuego de paso eléctrico.":
    "Firestopping of an electrical penetration.",
"Sellado cortafuego de paso sanitario.":
    "Firestopping of a plumbing penetration.",
"Sellado cortafuego de conducto.": "Firestopping of a duct.",
"Sellado cortafuego de bandeja portacables.":
    "Firestopping of a cable tray.",
"Sellado cortafuego de tubería de gas.":
    "Firestopping of a gas pipe.",
"Sellado cortafuego de junta lineal.":
    "Firestopping of a linear joint.",
"Sellado cortafuego de paso múltiple.":
    "Firestopping of a multiple penetration.",
"Sellado cortafuego de junta de dilatación.":
    "Firestopping of an expansion joint.",
"Sellado cortafuego de paso de climatización.":
    "Firestopping of an HVAC penetration.",
"Sellado cortafuego de encuentro muro-losa.":
    "Firestopping of a wall and slab junction.",
"Sellado cortafuego de paso de datos.":
    "Firestopping of a data cable penetration.",
"Sellado cortafuego de cierre perimetral.":
    "Firestopping of a perimeter seal.",
"Sellado cortafuego de bandeja.": "Firestopping of a cable tray.",
"Sellado cortafuego de junta de construcción.":
    "Firestopping of a construction joint.",
}
