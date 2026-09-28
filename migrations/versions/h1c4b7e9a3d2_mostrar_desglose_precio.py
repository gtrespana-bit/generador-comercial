"""Desglose del precio en el PDF: productos elegidos frente a mano de obra.

``presupuestos.mostrar_desglose_precio`` activa, presupuesto a presupuesto, el
reparto del precio de venta que se imprime en el bloque de totales del PDF:

* una fila con los productos y materiales elegidos por el cliente;
* otra con la mano de obra, los recursos y la ejecución de los trabajos;
* y un IVA aparte, de modo que las dos filas suman exactamente la base
  imponible del documento.

Es un **reparto del precio**, nunca el coste interno ni el margen de la
empresa: esos siguen viviendo solo en «Configuración → Mostrar costes
internos». La columna nace apagada (``false``) para que ningún presupuesto ya
emitido cambie de aspecto al desplegar.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "h1c4b7e9a3d2"
down_revision: Union[str, Sequence[str], None] = "g7c8d9e0f1a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Idempotente: si el hotfix de producción ya creó la columna vía
    # ``ALTER TABLE ... IF NOT EXISTS``, el upgrade no debe abortar.
    bind = op.get_bind()
    try:
        from sqlalchemy import inspect as _inspect

        cols = {c["name"] for c in _inspect(bind).get_columns("presupuestos")}
    except Exception:
        cols = set()
    if "mostrar_desglose_precio" not in cols:
        op.add_column(
            "presupuestos",
            sa.Column(
                "mostrar_desglose_precio",
                sa.Boolean(),
                nullable=True,
                # ``sa.false()`` y no ``sa.text("0")``: PostgreSQL rechaza
                # ``BOOLEAN DEFAULT 0`` y aquí ya ocurrió un incidente de
                # esquema a medio migrar (b1c2d3e4f5a6).
                server_default=sa.false(),
            ),
        )


def downgrade() -> None:
    op.drop_column("presupuestos", "mostrar_desglose_precio")
