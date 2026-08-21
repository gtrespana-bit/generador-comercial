"""Ids de Stripe en compras_plan y método ``stripe``.

Revision ID: c3e9a1b7d4f2
Revises: a4c8e2f7b1d6
Create Date: 2026-08-20
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3e9a1b7d4f2"
down_revision: Union[str, Sequence[str], None] = "a4c8e2f7b1d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "compras_plan"


def _postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    op.add_column(
        TABLE,
        sa.Column("stripe_checkout_session_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        TABLE,
        sa.Column("stripe_subscription_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        TABLE,
        sa.Column("stripe_customer_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        TABLE,
        sa.Column("stripe_payment_intent_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        TABLE,
        sa.Column("stripe_invoice_id", sa.String(length=255), nullable=True),
    )
    op.create_index(
        "ix_compras_plan_stripe_subscription",
        TABLE,
        ["stripe_subscription_id"],
        unique=False,
    )
    op.create_index(
        "uq_compras_plan_stripe_session",
        TABLE,
        ["stripe_checkout_session_id"],
        unique=True,
    )
    op.create_index(
        "uq_compras_plan_stripe_invoice",
        TABLE,
        ["stripe_invoice_id"],
        unique=True,
    )
    if not _postgres():
        return
    op.drop_constraint("ck_compra_metodo_valido", TABLE, type_="check")
    op.create_check_constraint(
        "ck_compra_metodo_valido",
        TABLE,
        "metodo_pago IN ('pago_movil', 'binance', 'kontigo', 'usdt', 'stripe')",
    )
    # Renovaciones de Stripe: el webhook (sesión de operador) inserta una
    # compra nueva por cada factura periódica. Hasta ahora INSERT era solo
    # del tenant.
    op.execute("DROP POLICY IF EXISTS cotizat_compra_insert_operator ON public.compras_plan")
    op.execute(
        """
        CREATE POLICY cotizat_compra_insert_operator ON public.compras_plan
          FOR INSERT TO cotizat_app
          WITH CHECK (
            COALESCE(
              pg_catalog.current_setting('cotizat.es_operador', true) = 'on',
              FALSE
            )
          )
        """
    )


def downgrade() -> None:
    if _postgres():
        op.execute("DROP POLICY IF EXISTS cotizat_compra_insert_operator ON public.compras_plan")
        op.drop_constraint("ck_compra_metodo_valido", TABLE, type_="check")
        op.create_check_constraint(
            "ck_compra_metodo_valido",
            TABLE,
            "metodo_pago IN ('pago_movil', 'binance', 'kontigo', 'usdt')",
        )
    op.drop_index("uq_compras_plan_stripe_invoice", table_name=TABLE)
    op.drop_index("uq_compras_plan_stripe_session", table_name=TABLE)
    op.drop_index("ix_compras_plan_stripe_subscription", table_name=TABLE)
    op.drop_column(TABLE, "stripe_invoice_id")
    op.drop_column(TABLE, "stripe_payment_intent_id")
    op.drop_column(TABLE, "stripe_customer_id")
    op.drop_column(TABLE, "stripe_subscription_id")
    op.drop_column(TABLE, "stripe_checkout_session_id")
