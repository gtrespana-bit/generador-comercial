"""Cobro con Stripe (suscripciones): columnas de la compra y método ``stripe``.

Añade a ``compras_plan`` las piezas que necesita el cobro con tarjeta y la
suscripción recurrente:

- ``stripe_session_id``: la sesión de Stripe Checkout que originó la compra.
  El webhook la usa para localizar la compra pendiente al completar el pago.
- ``stripe_subscription_id``: la suscripción recurrente creada en el checkout.
  Las renovaciones llegan por ``invoice.paid`` y se localizan por esta clave.
- ``stripe_customer_id``: cliente de Stripe (portal de gestión de la
  suscripción).
- ``stripe_payment_intent``: el pago confirmado por Stripe (referencia real).
- ``pais_codigo``: país desde el que se cobró (panel y auditoría).

Además amplía los CHECK de ``metodo_pago`` (admite ``'stripe'``) y de
``estado`` (admite ``'cancelada'`` para suscripciones dadas de baja).

Cuelga de ``a4c8e2f7b1d6`` (evidencia de precios de mercado, head anterior),
no de ``b9f4d8a2c6e1``: así la cadena conserva un único head.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "ab12cd34ef56"
down_revision: Union[str, Sequence[str], None] = "a4c8e2f7b1d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "compras_plan"
CHECK_METODO = "ck_compra_metodo_valido"
CHECK_ESTADO = "ck_compra_estado_valido"


def _postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    op.add_column(TABLE, sa.Column("stripe_session_id", sa.String(length=200), nullable=True))
    op.add_column(TABLE, sa.Column("stripe_payment_intent", sa.String(length=200), nullable=True))
    op.add_column(TABLE, sa.Column("stripe_subscription_id", sa.String(length=200), nullable=True))
    op.add_column(TABLE, sa.Column("stripe_customer_id", sa.String(length=200), nullable=True))
    op.add_column(TABLE, sa.Column("pais_codigo", sa.String(length=2), nullable=True))

    # Búsquedas del webhook de Stripe (sesión y suscripción) sin seq-scan.
    op.create_index("ix_compras_plan_stripe_session", TABLE, ["stripe_session_id"])
    op.create_index("ix_compras_plan_stripe_subscription", TABLE, ["stripe_subscription_id"])

    if not _postgres():
        # SQLite no permite alterar CHECK existentes. El escritorio no usa
        # Stripe, y los modelos crean las tablas nuevas con el CHECK completo.
        return

    op.drop_constraint(CHECK_METODO, TABLE, type_="check")
    op.create_check_constraint(
        CHECK_METODO,
        TABLE,
        "metodo_pago IN ('pago_movil', 'binance', 'kontigo', 'usdt', 'stripe')",
    )
    op.drop_constraint(CHECK_ESTADO, TABLE, type_="check")
    op.create_check_constraint(
        CHECK_ESTADO,
        TABLE,
        "estado IN ('pendiente', 'activa', 'rechazada', 'cancelada')",
    )


def downgrade() -> None:
    op.drop_index("ix_compras_plan_stripe_subscription", table_name=TABLE)
    op.drop_index("ix_compras_plan_stripe_session", table_name=TABLE)
    if _postgres():
        op.drop_constraint(CHECK_ESTADO, TABLE, type_="check")
        op.create_check_constraint(
            CHECK_ESTADO,
            TABLE,
            "estado IN ('pendiente', 'activa', 'rechazada')",
        )
        op.drop_constraint(CHECK_METODO, TABLE, type_="check")
        op.create_check_constraint(
            CHECK_METODO,
            TABLE,
            "metodo_pago IN ('pago_movil', 'binance', 'kontigo', 'usdt')",
        )
    op.drop_column(TABLE, "pais_codigo")
    op.drop_column(TABLE, "stripe_customer_id")
    op.drop_column(TABLE, "stripe_subscription_id")
    op.drop_column(TABLE, "stripe_payment_intent")
    op.drop_column(TABLE, "stripe_session_id")
