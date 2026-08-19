"""Índices de rendimiento para las consultas calientes del catálogo y presupuestos.

Revision ID: b9f4d8a2c6e1
Revises: e7b3c1d5a204
Create Date: 2026-08-19

Contexto (auditoría de rendimiento): el despliegue web (PostgreSQL remoto)
carecía de índices para casi todas las claves foráneas —PostgreSQL no crea
índices automáticos en FK— ni para los filtros habituales del catálogo.
Cada carga de /partidas, /presupuestos o la ficha de un presupuesto hacía
seq-scans y joins sin índice bajo RLS. Estos índices cubren:

- partidas: visibilidad por organización, árbol capítulo/subcapítulo y la
  auditoría de versión de catálogo;
- presupuestos: filtro por estado y join con clientes (búsqueda);
- grafo de presupuesto: capítulos → partidas → mediciones/productos y
  tablas dependientes (versiones, anexos, notas, facturas, proyectos,
  cambios de alcance y pagos).

Los nombres coinciden exactamente con los declarados en ``app/models.py``
para que una base nueva (create_all) y una migrada queden idénticas.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "b9f4d8a2c6e1"
down_revision: Union[str, Sequence[str], None] = "e7b3c1d5a204"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (tabla, nombre, columnas) — en el orden en que se crean y se deshacen.
INDICES = [
    ("partidas", "ix_partidas_org_oculta", ["organizacion_id", "oculta"]),
    ("partidas", "ix_partidas_org_clasificacion", ["organizacion_id", "categoria", "subcategoria"]),
    ("partidas", "ix_partidas_org_version", ["organizacion_id", "version_catalogo"]),
    ("presupuestos", "ix_presupuestos_org_estado", ["organizacion_id", "estado"]),
    ("presupuestos", "ix_presupuestos_client_id", ["client_id"]),
    ("presupuesto_versiones", "ix_presupuesto_versiones_presupuesto_id", ["presupuesto_id"]),
    ("capitulos", "ix_capitulos_presupuesto_id", ["presupuesto_id"]),
    ("presupuesto_items", "ix_presupuesto_items_capitulo_id", ["capitulo_id"]),
    ("presupuesto_items", "ix_presupuesto_items_partida_catalogo_id", ["partida_catalogo_id"]),
    ("mediciones", "ix_mediciones_partida_id", ["partida_id"]),
    ("presupuesto_item_productos", "ix_presupuesto_item_productos_partida_id", ["partida_id"]),
    ("notas_seguimiento", "ix_notas_seguimiento_presupuesto_id", ["presupuesto_id"]),
    ("presupuesto_anexos", "ix_presupuesto_anexos_presupuesto_id", ["presupuesto_id"]),
    ("facturas", "ix_facturas_presupuesto_id", ["presupuesto_id"]),
    ("facturas", "ix_facturas_client_id", ["client_id"]),
    ("factura_capitulos", "ix_factura_capitulos_factura_id", ["factura_id"]),
    ("factura_items", "ix_factura_items_capitulo_id", ["capitulo_id"]),
    ("cambios_alcance", "ix_cambios_alcance_proyecto_id", ["proyecto_id"]),
    ("cambio_alcance_items", "ix_cambio_alcance_items_cambio_id", ["cambio_id"]),
    ("pagos", "ix_pagos_proyecto_id", ["proyecto_id"]),
    ("pagos", "ix_pagos_presupuesto_id", ["presupuesto_id"]),
    ("pagos", "ix_pagos_factura_id", ["factura_id"]),
]


def _existentes() -> set[tuple[str, str]]:
    """Pares (tabla, índice) ya presentes, para idempotencia defensiva."""
    try:
        from sqlalchemy import inspect

        insp = inspect(op.get_bind())
        return {
            (tabla, indice["name"])
            for tabla in insp.get_table_names()
            for indice in insp.get_indexes(tabla)
            if indice.get("name")
        }
    except Exception:
        return set()


def upgrade() -> None:
    existentes = _existentes()
    for tabla, nombre, columnas in INDICES:
        if (tabla, nombre) in existentes:
            continue
        op.create_index(nombre, tabla, columnas, unique=False)


def downgrade() -> None:
    for tabla, nombre, _columnas in reversed(INDICES):
        op.drop_index(nombre, table_name=tabla)
