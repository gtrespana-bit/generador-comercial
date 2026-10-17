# -*- coding: utf-8 -*-
"""Nombres de partida — Gestión de residuos y limpieza (capítulo completo, 50).

Criterios de este lote:
  · «Escombro» es debris cuando se barre y se carga, y spoil cuando es
    tierra de excavación. En inglés no son la misma palabra.
  · «Escombrera» es debris chute, el ducto por el que baja el escombro.
  · «Vertedero autorizado» es licensed disposal site; «canon de vertido»
    es landfill tipping fee, que es la tasa que cobra el vertedero.
  · «Gestor» de residuos es licensed waste carrier: el transportista
    autorizado, no la empresa que gestiona.
  · «Saco big-bag» es bulk bag.
  · «Pulidora» de pisos es scrubbing machine en este contexto, porque lo
    que se pide es fregar, no pulir.
"""

LOTE = {
# ── Clasificación y acopio ────────────────────────────────────────────────
"Zona de acopio y clasificación de residuos.":
    "Waste storage and sorting area.",
"Clasificación y recuperación de material aprovechable.":
    "Sorting and recovery of reusable material.",
"Sacos de rafia para clasificación de residuos.":
    "Heavy-duty woven sacks for sorting waste.",
"Zona de acopio de chatarra metálica.": "Scrap metal storage area.",
"Zona de acopio de cartón y embalajes.":
    "Cardboard and packaging storage area.",
"Zona de acopio de madera y pallets.": "Timber and pallet storage area.",
"Separación selectiva de residuos en origen.":
    "Separation of waste at source.",
"Identificación y etiquetado de contenedores de residuos.":
    "Identification and labeling of waste containers.",

# ── Bajada y carga de escombro ────────────────────────────────────────────
"Bajada de escombro desde plantas altas.":
    "Removal of debris from upper floors.",
"Bajada de escombro por escombrera o ducto.":
    "Removal of debris through a debris chute.",
"Bajada de escombro por medios manuales.":
    "Removal of debris by hand.",
"Bajada de escombro por montacargas.":
    "Removal of debris by hoist.",
"Carga manual de escombro sobre contenedor.":
    "Hand loading of debris into a container.",
"Carga mecánica de escombro sobre vehículo.":
    "Mechanical loading of debris onto a vehicle.",
"Movimiento interno de escombro a zona de acopio.":
    "Internal movement of debris to the storage area.",

# ── Contenedores ──────────────────────────────────────────────────────────
"Contenedor de escombro, por mes de permanencia.":
    "Debris container, per month on site.",
"Contenedor de escombro de 3 m³, por mes.":
    "3 m³ debris container, per month.",
"Contenedor de chatarra metálica.": "Scrap metal container.",
"Contenedor de residuos de madera.": "Timber waste container.",
"Saco big-bag de escombro.": "Bulk bag for debris.",
"Contenedor de residuos mezclados.": "Mixed waste container.",
"Acopio de escombro en sacos apilados.":
    "Storage of debris in stacked sacks.",

# ── Retirada y gestión ────────────────────────────────────────────────────
"Retirada y transporte de escombro a vertedero autorizado.":
    "Removal and cartage of debris to a licensed disposal site.",
"Transporte de escombro a vertedero autorizado.":
    "Cartage of debris to a licensed disposal site.",
"Canon de vertido de escombro mezclado.":
    "Landfill tipping fee for mixed debris.",
"Retirada de chatarra metálica a gestor.":
    "Removal of scrap metal by a licensed waste carrier.",
"Retirada de cartón y embalajes a reciclaje.":
    "Removal of cardboard and packaging for recycling.",
"Retirada de madera y pallets a reciclaje.":
    "Removal of timber and pallets for recycling.",
"Disposición de tierra de excavación.":
    "Disposal of excavated spoil.",

# ── Residuos peligrosos ───────────────────────────────────────────────────
"Retiro de residuos de pinturas y disolventes.":
    "Removal of paint and solvent waste.",
"Retiro de residuos peligrosos menores.":
    "Removal of small quantities of hazardous waste.",
"Retiro de tubos fluorescentes y lámparas.":
    "Removal of fluorescent tubes and lamps.",
"Retiro de baterías y pilas de obra.":
    "Removal of batteries from site.",
"Gestión de aceites y lubricantes usados.":
    "Management of waste oils and lubricants.",
"Neutralización y limpieza de derrame menor.":
    "Neutralization and clean-up of a minor spill.",

# ── Limpieza durante la obra ──────────────────────────────────────────────
"Limpieza periódica durante la ejecución de la obra.":
    "Periodic cleaning during the works.",
"Limpieza diaria de zonas de trabajo.":
    "Daily cleaning of work areas.",
"Limpieza semanal de la obra.": "Weekly cleaning of the site.",
"Limpieza de zonas de paso y accesos.":
    "Cleaning of circulation areas and accesses.",
"Limpieza de restos de mortero y adhesivos.":
    "Cleaning of mortar and adhesive residue.",
"Limpieza de escombro disperso en pisos.":
    "Cleaning of loose debris from floors.",
"Retirada de embalajes de la zona de trabajo.":
    "Removal of packaging from the work area.",

# ── Limpieza final ────────────────────────────────────────────────────────
"Limpieza final de obra.": "Final clean of the works.",
"Limpieza profunda de vidrios y acabados delicados.":
    "Deep cleaning of glazing and delicate finishes.",
"Limpieza final de obra para entrega.":
    "Final clean of the works ahead of handover.",
"Limpieza de vidrios y carpintería.":
    "Cleaning of glazing and joinery.",
"Limpieza de aparatos sanitarios y grifería.":
    "Cleaning of plumbing fixtures and faucets.",
"Limpieza de pisos con pulidora.":
    "Machine scrubbing of floors.",
"Desinfección de zonas húmedas.":
    "Disinfection of wet areas.",
"Retirada final de protecciones y limpieza general.":
    "Final removal of protection and general cleaning.",
}
