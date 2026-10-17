# -*- coding: utf-8 -*-
"""Nombres de partida — Acondicionamiento del terreno (capítulo completo, 80).

Criterios de este lote:
  · «Desbroce» es clearing and grubbing en Estados Unidos y site clearance
    en Reino Unido: es la expresión de oficio para dejar el terreno limpio
    de vegetación, no «cleaning».
  · «Descapote» es stripping: se retira la capa vegetal, el topsoil, y se
    aparta porque se reutiliza.
  · «Excavación a cielo abierto» es open-cut excavation.
  · «Entibado» es trench sheeting, la entibación que sostiene las paredes
    de la zanja.
  · «Achique» y «achicamiento» son dewatering: sacar el agua, no achicar
    en el sentido de empequeñecer.
  · «Material de préstamo» es imported fill, el material que se trae de
    fuera porque el de la propia excavación no sirve.
  · «Botadero» es spoil site para la tierra sobrante; «vertedero» es
    disposal site para el escombro. No son lo mismo.
  · «Piedra picada» es crushed stone y «subrasante» es subgrade.
"""

LOTE = {
# ── Limpieza y desbroce ───────────────────────────────────────────────────
"Limpieza y desbroce manual del terreno.":
    "Manual clearing and grubbing of the site.",
"Limpieza y desbroce mecanizado del terreno.":
    "Mechanical clearing and grubbing of the site.",
"Descapote y retiro de capa vegetal.":
    "Stripping and removal of topsoil.",
"Retiro de raíces y obstáculos menores enterrados.":
    "Removal of roots and minor buried obstructions.",
"Desbroce de vegetación arbustiva.":
    "Clearing and grubbing of scrub vegetation.",
"Desbroce con retiro de capa vegetal.":
    "Clearing and grubbing, including removal of topsoil.",
"Retiro de obstáculos y escombros superficiales.":
    "Removal of obstructions and surface debris.",
"Limpieza de terreno en pendiente.":
    "Clearing of sloping ground.",
"Retiro de tocones de árboles.": "Removal of tree stumps.",
"Descapote de terreno con topografía.":
    "Stripping of the site, including survey.",
"Limpieza de terreno con escombros de demolición.":
    "Clearing of a site with demolition debris.",
"Retiro de pavimento vegetal o grama.":
    "Removal of the vegetative cover or grass.",
"Limpieza de terreno con maleza alta.":
    "Clearing of a site with tall undergrowth.",
"Retiro de capa de asfalto superficial.":
    "Removal of a surface layer of asphalt.",

# ── Excavación ────────────────────────────────────────────────────────────
"Excavación mecanizada a cielo abierto.":
    "Mechanical open-cut excavation.",
"Excavación en material duro o roca.":
    "Excavation in hard material or rock.",
"Excavación para tanque séptico, sumidero o tanque enterrado.":
    "Excavation for a septic tank, catch basin or buried tank.",
"Perfilado y compactación del fondo de excavación.":
    "Trimming and compaction of the bottom of an excavation.",
"Achicamiento de agua en excavación.":
    "Dewatering of an excavation.",
"Excavación manual en interiores.": "Hand excavation indoors.",
"Excavación a cielo abierto en terreno blando.":
    "Open-cut excavation in soft ground.",
"Excavación a cielo abierto en terreno duro.":
    "Open-cut excavation in hard ground.",
"Excavación a cielo abierto con taludes.":
    "Open-cut excavation with battered sides.",
"Perfilado y limpieza de fondo de excavación.":
    "Trimming and cleaning of the bottom of an excavation.",
"Excavación para cimientos de edificación.":
    "Excavation for the foundations of a building.",
"Excavación para piscina o tanque.":
    "Excavation for a swimming pool or tank.",
"Excavación de sótano.": "Excavation for a basement.",
"Excavación en terreno con agua.":
    "Excavation in water-bearing ground.",
"Excavación de explanada.": "Excavation to formation level.",
"Excavación a cielo abierto con retiro lateral.":
    "Open-cut excavation with side casting.",
"Excavación localizada a mano en interior.":
    "Localized hand excavation indoors.",
"Excavación de registro enterrado.":
    "Excavation for a buried inspection chamber.",

# ── Zanjas ────────────────────────────────────────────────────────────────
"Excavación manual en zanja para fundaciones.":
    "Hand excavation of a foundation trench.",
"Excavación mecanizada en zanja para fundaciones.":
    "Mechanical excavation of a foundation trench.",
"Excavación manual en zanja para instalaciones enterradas.":
    "Hand excavation of a trench for buried services.",
"Entibado de zanja con madera.":
    "Trench sheeting in lumber.",
"Excavación de pozo para fundación.":
    "Excavation of a pit for a foundation.",
"Excavación de zanja con entibado.":
    "Excavation of a trench with sheeting.",
"Zanja para tubería de drenaje.": "Trench for a drainage pipe.",
"Zanja para tubería de agua.": "Trench for a water pipe.",
"Zanja para tubería eléctrica.": "Trench for an electrical conduit.",
"Zanja para cable de datos.": "Trench for a data cable.",
"Zanja para gas.": "Trench for a gas pipe.",
"Zanja de fundación corrida.": "Trench for a strip footing.",

# ── Rellenos y bases ──────────────────────────────────────────────────────
"Relleno y compactación con material del sitio.":
    "Backfill and compaction with material from the site.",
"Relleno y compactación con material granular de préstamo.":
    "Backfill and compaction with imported granular fill.",
"Relleno de zanja de instalaciones con arena.":
    "Backfill of a services trench with sand.",
"Base de piedra picada compactada.": "Compacted crushed stone base.",
"Nivelación y compactación de terreno.":
    "Leveling and compaction of the ground.",
"Relleno compactado en capas.": "Backfill compacted in layers.",
"Relleno con material granular.": "Backfill with granular material.",
"Base de piedra picada compactada para pavimento.":
    "Compacted crushed stone base for paving.",
"Base de arena compactada.": "Compacted sand base.",
"Nivelación y compactación de subrasante.":
    "Leveling and compaction of the subgrade.",
"Relleno de zanja con arena.": "Backfill of a trench with sand.",
"Relleno con material de excavación reutilizado.":
    "Backfill with reused excavated material.",
"Compactación de terraplén.": "Compaction of an embankment.",
"Relleno estructural con piedra picada.":
    "Structural backfill with crushed stone.",

# ── Agua y estabilización ─────────────────────────────────────────────────
"Achique de agua en excavación.": "Dewatering of an excavation.",
"Drenaje provisional con tubería perforada.":
    "Temporary drainage with perforated pipe.",
"Cuneta provisional de desvío de aguas.":
    "Temporary intercepting ditch.",
"Estabilización de fondo de excavación.":
    "Stabilization of the bottom of an excavation.",
"Protección de talud con geotextil.":
    "Protection of a slope with a geotextile.",
"Estabilización de talud con malla.":
    "Stabilization of a slope with mesh.",
"Estabilización de fondo con material granular.":
    "Stabilization of the bottom with granular material.",

# ── Carga, transporte y suministro ────────────────────────────────────────
"Carga manual y transporte de tierra sobrante a botadero.":
    "Hand loading and cartage of surplus spoil to a spoil site.",
"Carga mecanizada y transporte de tierra sobrante a botadero.":
    "Mechanical loading and cartage of surplus spoil to a spoil site.",
"Acopio provisional de tierra en obra para su reutilización.":
    "Temporary stockpiling of soil on site for reuse.",
"Suministro y transporte de material de préstamo a obra.":
    "Supply and cartage of imported fill to the site.",
"Traslado interno de material con carretilla.":
    "Internal movement of material by wheelbarrow.",
"Carga mecanizada de tierra sobrante.":
    "Mechanical loading of surplus spoil.",
"Transporte de tierra sobrante a botadero.":
    "Cartage of surplus spoil to a spoil site.",
"Transporte de escombro a vertedero.":
    "Cartage of debris to a disposal site.",
"Acopio y reutilización de tierra en obra.":
    "Stockpiling and reuse of soil on site.",
"Suministro de material de préstamo.": "Supply of imported fill.",
"Suministro de arena lavada.": "Supply of washed sand.",
"Carga manual de tierra sobrante.":
    "Hand loading of surplus spoil.",
"Transporte interno con carretilla.":
    "Internal movement by wheelbarrow.",
"Suministro de piedra picada.": "Supply of crushed stone.",
"Suministro de gravilla.": "Supply of gravel.",
}
