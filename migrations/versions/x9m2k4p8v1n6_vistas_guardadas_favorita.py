"""Vistas guardadas como favoritas (productividad del operador).

Añade la columna booleana ``favorita`` a ``vistas_guardadas`` para que un
operador pueda marcar sus vistas más usadas y acceder a ellas desde una
sección destacada del sidebar sin tener que navegar a cada módulo.

Diseño:
- Por defecto ``favorita = false``: las vistas existentes no cambian de
  comportamiento.
- Idempotente por si el código arranca antes que la migración.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "x9m2k4p8v1n6"
down_revision: Union[str, Sequence[str], None] = "w3m9k2p8v1n4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "vistas_guardadas"


def _existe_columna() -> bool:
    try:
        from sqlalchemy import inspect as _inspect

        cols = {
            c["name"]
            for c in _inspect(op.get_bind()).get_columns(TABLE)
        }
        return "favorita" in cols
    except Exception:
        return False


def upgrade() -> None:
    if _existe_columna():
        return
    op.add_column(
        TABLE,
        sa.Column("favorita", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    if not _existe_columna():
        return
    op.drop_column(TABLE, "favorita")
