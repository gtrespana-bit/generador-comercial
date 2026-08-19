"""Tasa de referencia por organización para conversión USD->local (LatAm).

Añade `configuracion.tasa_cambio` (unidades de moneda_default por 1 USD) y
`configuracion.fecha_tasa` para que el catálogo en USD pueda mostrarse
y cotizarse en moneda local sin reescribir precios. NULL = 1 (USD).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d9e2f3a4b5c6"
down_revision: Union[str, Sequence[str], None] = "c8f1a2b3d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("configuracion", sa.Column("tasa_cambio", sa.Float(), nullable=True))
    op.add_column("configuracion", sa.Column("fecha_tasa", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("configuracion", "fecha_tasa")
    op.drop_column("configuracion", "tasa_cambio")
