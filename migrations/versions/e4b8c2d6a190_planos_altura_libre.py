"""Altura libre de paredes en planos de obra.

Permite estimar m² de paramentos (perímetro × altura) sin tocar la
geometría de cada estancia.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e4b8c2d6a190"
down_revision: Union[str, Sequence[str], None] = "d1e2f3a4b5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("planos_obra", sa.Column("altura_libre_m", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("planos_obra", "altura_libre_m")
