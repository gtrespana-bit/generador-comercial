"""link Supabase Auth identity

Revision ID: 9bca2ad1f6e4
Revises: 5cda50f97ed9
Create Date: 2026-08-13 23:15:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9bca2ad1f6e4"
down_revision: Union[str, Sequence[str], None] = "5cda50f97ed9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # UUID se conserva como texto para que una copia SQLite pueda importarse y
    # probarse sin depender de un tipo específico de PostgreSQL.
    with op.batch_alter_table("usuarios") as batch_op:
        batch_op.add_column(sa.Column("auth_user_id", sa.String(length=36), nullable=True))
        batch_op.create_unique_constraint(
            "uq_usuarios_auth_user_id", ["auth_user_id"]
        )


def downgrade() -> None:
    with op.batch_alter_table("usuarios") as batch_op:
        batch_op.drop_constraint("uq_usuarios_auth_user_id", type_="unique")
        batch_op.drop_column("auth_user_id")
