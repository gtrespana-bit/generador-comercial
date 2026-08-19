"""Etiqueta fiscal por país para LatAm (Semana 2 — Bloque A).

Añade `configuracion.etiqueta_id_fiscal` (RIF, NIT, RUT, CUIT, RUC, RFC…)
para que cada organización pueda mostrar su ID fiscal local en clientes,
presupuestos y PDFs. Default RIF preserva instalaciones venezolanas.

No toca `activar_funciones_venezuela`: el alias
`activar_funciones_regionales` mapea a la misma columna en Python
(ver app/models.py), así que no hace falta renombrar la columna física
en este bloque. El _sincronizar_columnas_modelos ya añade la columna en
SQLite; esta migración cubre PostgreSQL.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c8f1a2b3d4e5"
down_revision: Union[str, Sequence[str], None] = "d2a7c9e4f1b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "configuracion",
        sa.Column("etiqueta_id_fiscal", sa.String(length=20), nullable=True, server_default="RIF"),
    )
    # Rellenar filas existentes que quedaron con NULL (server_default no cubre filas ya insertadas en algunos PG setups)
    op.execute("UPDATE configuracion SET etiqueta_id_fiscal = 'RIF' WHERE etiqueta_id_fiscal IS NULL")
    # Hacerla NOT NULL en el futuro es opcional; la dejamos nullable por compat SQLite
    # pero con default Python "RIF" en el modelo.


def downgrade() -> None:
    op.drop_column("configuracion", "etiqueta_id_fiscal")
