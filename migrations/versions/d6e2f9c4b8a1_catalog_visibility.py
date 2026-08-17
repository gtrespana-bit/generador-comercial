"""Visibilidad por organización y actualización incremental del catálogo.

Revision ID: d6e2f9c4b8a1
Revises: f8a1b2c3d4e5
Create Date: 2026-08-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d6e2f9c4b8a1"
down_revision: Union[str, Sequence[str], None] = "f8a1b2c3d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("partidas") as batch:
        batch.add_column(sa.Column("catalogo_uid", sa.String(length=100), nullable=True))
        batch.add_column(sa.Column(
            "es_oficial", sa.Boolean(), nullable=True, server_default=sa.false()
        ))
        batch.add_column(sa.Column(
            "oculta", sa.Boolean(), nullable=True, server_default=sa.false()
        ))
        batch.add_column(sa.Column(
            "version_alta_catalogo", sa.Integer(), nullable=True, server_default="0"
        ))
        batch.create_unique_constraint(
            "uq_partida_organizacion_catalogo_uid",
            ["organizacion_id", "catalogo_uid"],
        )
        batch.create_index("ix_partidas_catalogo_uid", ["catalogo_uid"])
        batch.create_index("ix_partidas_oculta", ["oculta"])


def downgrade() -> None:
    with op.batch_alter_table("partidas") as batch:
        batch.drop_index("ix_partidas_oculta")
        batch.drop_index("ix_partidas_catalogo_uid")
        batch.drop_constraint(
            "uq_partida_organizacion_catalogo_uid", type_="unique"
        )
        batch.drop_column("version_alta_catalogo")
        batch.drop_column("oculta")
        batch.drop_column("es_oficial")
        batch.drop_column("catalogo_uid")
