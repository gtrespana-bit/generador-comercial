"""Catálogo numérico con capítulo, subcapítulo y apartado.

Revision ID: f8a1b2c3d4e5
Revises: a3d7e9c1b5f2
Create Date: 2026-08-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f8a1b2c3d4e5"
down_revision: Union[str, Sequence[str], None] = "a3d7e9c1b5f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "configuracion",
        sa.Column("version_catalogo", sa.Integer(), nullable=True, server_default="0"),
    )

    with op.batch_alter_table("categorias_partidas") as batch:
        batch.add_column(sa.Column("parent_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("codigo_segmento", sa.String(length=2), nullable=True))
        batch.add_column(sa.Column("codigo_completo", sa.String(length=8), nullable=True))
        batch.add_column(sa.Column("nombre", sa.String(length=120), nullable=True))
        batch.add_column(sa.Column("nivel", sa.Integer(), nullable=True, server_default="1"))
        batch.add_column(sa.Column("orden", sa.Integer(), nullable=True, server_default="0"))
        batch.add_column(sa.Column("ambito", sa.String(length=30), nullable=True, server_default="reforma"))
        batch.add_column(sa.Column("activa", sa.Boolean(), nullable=True, server_default=sa.true()))
        batch.add_column(sa.Column("oficial", sa.Boolean(), nullable=True, server_default=sa.false()))
        batch.create_foreign_key(
            "fk_categorias_partidas_parent_id",
            "categorias_partidas",
            ["parent_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch.create_unique_constraint(
            "uq_categoria_partida_organizacion_codigo",
            ["organizacion_id", "codigo_completo"],
        )
        batch.create_index("ix_categorias_partidas_parent_id", ["parent_id"])
        batch.create_index("ix_categorias_partidas_codigo", ["codigo_completo"])

    with op.batch_alter_table("partidas") as batch:
        batch.add_column(sa.Column("apartado", sa.String(length=120), nullable=True))
        batch.add_column(sa.Column("categoria_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("codigo_clasificacion", sa.String(length=20), nullable=True))
        batch.add_column(sa.Column("codigo_legacy", sa.String(length=80), nullable=True))
        batch.add_column(sa.Column("version_catalogo", sa.Integer(), nullable=True, server_default="0"))
        batch.create_foreign_key(
            "fk_partidas_categoria_id",
            "categorias_partidas",
            ["categoria_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch.create_index("ix_partidas_categoria_id", ["categoria_id"])


def downgrade() -> None:
    with op.batch_alter_table("partidas") as batch:
        batch.drop_index("ix_partidas_categoria_id")
        batch.drop_constraint("fk_partidas_categoria_id", type_="foreignkey")
        for columna in (
            "version_catalogo",
            "codigo_legacy",
            "codigo_clasificacion",
            "categoria_id",
            "apartado",
        ):
            batch.drop_column(columna)

    with op.batch_alter_table("categorias_partidas") as batch:
        batch.drop_index("ix_categorias_partidas_codigo")
        batch.drop_index("ix_categorias_partidas_parent_id")
        batch.drop_constraint("uq_categoria_partida_organizacion_codigo", type_="unique")
        batch.drop_constraint("fk_categorias_partidas_parent_id", type_="foreignkey")
        for columna in (
            "oficial",
            "activa",
            "ambito",
            "orden",
            "nivel",
            "nombre",
            "codigo_completo",
            "codigo_segmento",
            "parent_id",
        ):
            batch.drop_column(columna)

    op.drop_column("configuracion", "version_catalogo")
