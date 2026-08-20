"""Conserva rango y condiciones de cada precio nacional de referencia.

Revision ID: a4c8e2f7b1d6
Revises: b9f4d8a2c6e1
Create Date: 2026-08-20
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a4c8e2f7b1d6"
down_revision: Union[str, Sequence[str], None] = "b9f4d8a2c6e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "precios_recursos_mercado",
        sa.Column("codigo_recurso", sa.String(length=80), nullable=True, server_default=""),
    )
    op.execute(
        """
        UPDATE precios_recursos_mercado AS p
        SET codigo_recurso = r.codigo
        FROM recursos AS r
        WHERE r.id = p.recurso_id
          AND COALESCE(p.codigo_recurso, '') = ''
        """
    )
    op.create_index(
        "ix_precios_recursos_mercado_codigo_recurso",
        "precios_recursos_mercado",
        ["codigo_recurso"],
        unique=False,
    )
    op.add_column("precios_recursos_mercado", sa.Column("precio_min", sa.Float(), nullable=True))
    op.add_column("precios_recursos_mercado", sa.Column("precio_max", sa.Float(), nullable=True))
    op.add_column(
        "precios_recursos_mercado",
        sa.Column("unidad_referencia", sa.String(length=30), nullable=True, server_default=""),
    )
    op.add_column("precios_recursos_mercado", sa.Column("fecha_consulta", sa.Date(), nullable=True))
    op.add_column(
        "precios_recursos_mercado",
        sa.Column("incluye_iva", sa.String(length=20), nullable=True, server_default="por_verificar"),
    )
    op.add_column(
        "precios_recursos_mercado",
        sa.Column("incluye_transporte", sa.String(length=20), nullable=True, server_default="no_confirmado"),
    )
    op.add_column(
        "precios_recursos_mercado",
        sa.Column("observaciones", sa.Text(), nullable=True, server_default=""),
    )


def downgrade() -> None:
    for columna in (
        "observaciones",
        "incluye_transporte",
        "incluye_iva",
        "fecha_consulta",
        "unidad_referencia",
        "precio_max",
        "precio_min",
    ):
        op.drop_column("precios_recursos_mercado", columna)
    op.drop_index(
        "ix_precios_recursos_mercado_codigo_recurso",
        table_name="precios_recursos_mercado",
    )
    op.drop_column("precios_recursos_mercado", "codigo_recurso")
