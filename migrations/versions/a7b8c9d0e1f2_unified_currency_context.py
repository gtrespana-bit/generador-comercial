"""Add unified currency context to budgets, projects and organizations."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, Sequence[str], None] = "f9d4c2a7e5b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("configuracion", sa.Column("moneda_base_catalogo", sa.String(length=10), nullable=True, server_default="USD"))
    op.add_column("presupuestos", sa.Column("moneda_base", sa.String(length=10), nullable=True, server_default="USD"))
    op.add_column("presupuestos", sa.Column("fuente_tipo_cambio", sa.String(length=120), nullable=True, server_default=""))
    op.add_column("proyectos", sa.Column("moneda_contractual", sa.String(length=10), nullable=True, server_default="USD"))
    op.add_column("proyectos", sa.Column("moneda_base", sa.String(length=10), nullable=True, server_default="USD"))
    op.add_column("proyectos", sa.Column("tipo_cambio", sa.Float(), nullable=True))
    op.add_column("proyectos", sa.Column("fecha_tipo_cambio", sa.Date(), nullable=True))
    op.add_column("proyectos", sa.Column("fuente_tipo_cambio", sa.String(length=120), nullable=True, server_default=""))


def downgrade() -> None:
    op.drop_column("proyectos", "fuente_tipo_cambio")
    op.drop_column("proyectos", "fecha_tipo_cambio")
    op.drop_column("proyectos", "tipo_cambio")
    op.drop_column("proyectos", "moneda_base")
    op.drop_column("proyectos", "moneda_contractual")
    op.drop_column("presupuestos", "fuente_tipo_cambio")
    op.drop_column("presupuestos", "moneda_base")
    op.drop_column("configuracion", "moneda_base_catalogo")
