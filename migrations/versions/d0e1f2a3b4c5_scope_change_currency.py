"""Store contractual currency on scope changes and their items."""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "d0e1f2a3b4c5"
down_revision: Union[str, Sequence[str], None] = "c9d0e1f2a3b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("cambios_alcance", sa.Column("moneda", sa.String(length=10), nullable=True, server_default="USD"))
    op.add_column("cambio_alcance_items", sa.Column("moneda", sa.String(length=10), nullable=True, server_default="USD"))


def downgrade() -> None:
    op.drop_column("cambio_alcance_items", "moneda")
    op.drop_column("cambios_alcance", "moneda")
