"""add secure organization invitations

Revision ID: a84d2f6b91e0
Revises: 72e6f4d8a1c3
Create Date: 2026-08-13 23:59:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a84d2f6b91e0"
down_revision: Union[str, Sequence[str], None] = "72e6f4d8a1c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "invitaciones_organizacion",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("rol", sa.String(length=30), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("invitada_por_usuario_id", sa.Integer(), nullable=True),
        sa.Column("aceptada_por_usuario_id", sa.Integer(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("accepted_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("organizacion_id", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "rol IN ('administrador', 'miembro', 'lectura')",
            name="ck_invitacion_rol_valido",
        ),
        sa.ForeignKeyConstraint(
            ["organizacion_id"], ["organizaciones.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["invitada_por_usuario_id"], ["usuarios.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["aceptada_por_usuario_id"], ["usuarios.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash", name="uq_invitacion_token_hash"),
    )
    op.create_index(
        "ix_invitaciones_organizacion_organizacion_id",
        "invitaciones_organizacion",
        ["organizacion_id"],
        unique=False,
    )
    op.create_index(
        "ix_invitaciones_organizacion_email",
        "invitaciones_organizacion",
        ["organizacion_id", "email"],
        unique=False,
    )
    # No se abre ninguna política pública. El rol de aplicación y las políticas
    # autorizantes se versionarán juntos para no crear una ventana permisiva.
    if op.get_bind().dialect.name == "postgresql":
        op.execute("ALTER TABLE invitaciones_organizacion ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.drop_index(
        "ix_invitaciones_organizacion_email",
        table_name="invitaciones_organizacion",
    )
    op.drop_index(
        "ix_invitaciones_organizacion_organizacion_id",
        table_name="invitaciones_organizacion",
    )
    op.drop_table("invitaciones_organizacion")
