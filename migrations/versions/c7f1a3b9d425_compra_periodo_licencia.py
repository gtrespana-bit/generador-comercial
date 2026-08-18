"""La compra guarda el período concedido para el recibo del cliente (c7f1a3b9d425).

Al activar una compra el operador concede una ``Licencia``, pero esa tabla
está protegida por RLS de operador (revisión ``f4c1d8e37a95``): la sesión del
comprador no obtiene ni una fila. Hasta ahora el recibo en PDF solo existía en
``/admin/licencias/{id}/recibo.pdf``, es decir, el cliente tenía que pedírselo
al titular por email.

Esta revisión copia el período concedido (``inicio`` y ``vence``) sobre
``compras_plan``, que **sí** es una tabla tenant y el cliente lee con su
propia política RLS. Con eso ``/pago/recibo/{compra_id}.pdf`` puede emitir el
comprobante del propio comprador sin abrir ni un resquicio en el aislamiento
de ``licencias``.

Las dos columnas son anulables a propósito: las compras pendientes o
rechazadas no tienen período, y las compras ya activadas antes de esta
revisión se rellenan desde su licencia enlazada en el mismo paso.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "c7f1a3b9d425"
down_revision: Union[str, Sequence[str], None] = "d4e2f6a8b0c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "compras_plan",
        sa.Column("licencia_inicio", sa.Date(), nullable=True),
    )
    op.add_column(
        "compras_plan",
        sa.Column("licencia_vence", sa.Date(), nullable=True),
    )
    # Compras ya activadas: se recupera el período desde la licencia que se
    # les concedió, para que su recibo no salga vacío.
    op.execute(
        """
        UPDATE compras_plan AS c
        SET licencia_inicio = l.inicio,
            licencia_vence = l.vence
        FROM licencias AS l
        WHERE c.licencia_id = l.id
          AND c.licencia_inicio IS NULL
        """
        if op.get_bind().dialect.name == "postgresql"
        else """
        UPDATE compras_plan
        SET licencia_inicio = (
              SELECT inicio FROM licencias WHERE licencias.id = compras_plan.licencia_id
            ),
            licencia_vence = (
              SELECT vence FROM licencias WHERE licencias.id = compras_plan.licencia_id
            )
        WHERE licencia_id IS NOT NULL AND licencia_inicio IS NULL
        """
    )


def downgrade() -> None:
    op.drop_column("compras_plan", "licencia_vence")
    op.drop_column("compras_plan", "licencia_inicio")
