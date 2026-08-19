"""Store source of organization reference exchange rate."""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "e1f2a3b4c5d6"
down_revision: Union[str, Sequence[str], None] = "d0e1f2a3b4c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("configuracion", sa.Column("fuente_tipo_cambio", sa.String(length=120), nullable=True, server_default=""))


def downgrade() -> None:
    op.drop_column("configuracion", "fuente_tipo_cambio")
