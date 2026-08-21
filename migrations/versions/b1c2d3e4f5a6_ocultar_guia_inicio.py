"""Permite ocultar la «Guía de inicio» del panel por organización.

Añade `configuracion.recorrido_inicial_oculto` (BOOLEAN, 0 por defecto).
Cuando está activo, el dashboard deja de mostrar la tarjeta del recorrido
inicial sin darlo por completado: es la preferencia de quien ya conoce la
aplicación o crea otra organización y no necesita que le recuerden los cinco
pasos. Cada espacio de trabajo conserva su propia marca.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, Sequence[str], None] = "c3e9a1b7d4f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "configuracion",
        sa.Column(
            "recorrido_inicial_oculto",
            sa.Boolean(),
            nullable=True,
            server_default=sa.text("0"),
        ),
    )


def downgrade() -> None:
    op.drop_column("configuracion", "recorrido_inicial_oculto")
