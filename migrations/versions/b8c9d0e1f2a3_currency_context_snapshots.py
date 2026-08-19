"""Persist currency context in immutable versions and invoices."""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "b8c9d0e1f2a3"
down_revision: Union[str, Sequence[str], None] = "a7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for table in ("presupuesto_versiones", "facturas"):
        op.add_column(table, sa.Column("moneda_base", sa.String(length=10), nullable=True, server_default="USD"))
        op.add_column(table, sa.Column("tipo_cambio", sa.Float(), nullable=True))
        op.add_column(table, sa.Column("fecha_tipo_cambio", sa.Date(), nullable=True))
        op.add_column(table, sa.Column("fuente_tipo_cambio", sa.String(length=120), nullable=True, server_default=""))
    op.add_column("presupuesto_versiones", sa.Column("moneda", sa.String(length=10), nullable=True, server_default="USD"))


def downgrade() -> None:
    op.drop_column("presupuesto_versiones", "moneda")
    for table in ("facturas", "presupuesto_versiones"):
        op.drop_column(table, "fuente_tipo_cambio")
        op.drop_column(table, "fecha_tipo_cambio")
        op.drop_column(table, "tipo_cambio")
        op.drop_column(table, "moneda_base")
