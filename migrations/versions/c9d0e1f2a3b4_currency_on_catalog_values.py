"""Make currency explicit on catalog, product and budget item values."""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "c9d0e1f2a3b4"
down_revision: Union[str, Sequence[str], None] = "b8c9d0e1f2a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for table in ("presupuesto_items", "productos", "recursos"):
        op.add_column(table, sa.Column("moneda", sa.String(length=10), nullable=True, server_default="USD"))


def downgrade() -> None:
    for table in ("recursos", "productos", "presupuesto_items"):
        op.drop_column(table, "moneda")
