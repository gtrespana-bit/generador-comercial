"""add private storage metadata

Revision ID: 72e6f4d8a1c3
Revises: 9bca2ad1f6e4
Create Date: 2026-08-13 23:55:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "72e6f4d8a1c3"
down_revision: Union[str, Sequence[str], None] = "9bca2ad1f6e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "archivos_almacenados",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("object_key", sa.String(length=900), nullable=False),
        sa.Column("categoria", sa.String(length=80), nullable=False),
        sa.Column("content_type", sa.String(length=150), nullable=False),
        sa.Column("tamano_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("nombre_original", sa.String(length=300), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=False),
        sa.Column("organizacion_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["organizacion_id"], ["organizaciones.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "object_key LIKE 'organizaciones/' || organizacion_id || '/%'",
            name="ck_archivo_clave_pertenece_organizacion",
        ),
        sa.UniqueConstraint(
            "organizacion_id", "object_key", name="uq_archivo_organizacion_clave"
        ),
    )
    op.create_index(
        "ix_archivos_almacenados_organizacion_id",
        "archivos_almacenados", ["organizacion_id"], unique=False,
    )
    op.create_index(
        "ix_archivos_organizacion_categoria",
        "archivos_almacenados", ["organizacion_id", "categoria"], unique=False,
    )
    # Sin política pública: RLS sin políticas deniega roles no privilegiados.
    if op.get_bind().dialect.name == "postgresql":
        op.execute("ALTER TABLE archivos_almacenados ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.drop_index("ix_archivos_organizacion_categoria", table_name="archivos_almacenados")
    op.drop_index("ix_archivos_almacenados_organizacion_id", table_name="archivos_almacenados")
    op.drop_table("archivos_almacenados")
