"""Compras de plan con comprobante (E1-059 cobro manual).

Crea ``public.compras_plan``: el registro de cada compra que un cliente hace
desde la página de pago. Es una tabla **tenant** (la compra pertenece a la
organización que la pagó y el cliente la ve en su confirmación) con una
**excepción de operador**: el titular del producto necesita leerla en el panel
``/admin/compras`` para revisar el comprobante y activar la licencia.

Políticas RLS
-------------
- ``INSERT``: tenant con escritura (la sesión del cliente crea su compra).
- ``SELECT``: tenant (lectura) **o** sesión marcada como operador. Sin la
  marca, la tabla está vacía para cualquier otra sesión.
- ``UPDATE``: solo operador (activar/rechazar). El cliente no edita su compra.
- Sin ``DELETE`` a propósito: el historial de compras se conserva siempre.

El comprobante vive en el almacenamiento privado; la tabla solo guarda la
referencia, el nombre original y el MIME.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e5f2a8d31b6c"
down_revision: Union[str, Sequence[str], None] = "d6e2f9c4b8a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "compras_plan"
APP_ROLE = "cotizat_app"

IS_OPERATOR = """
  COALESCE(
    pg_catalog.current_setting('cotizat.es_operador', true) = 'on',
    FALSE
  )
"""
TENANT_READ = "cotizat_security.tenant_access(organizacion_id, FALSE)"
TENANT_WRITE = "cotizat_security.tenant_access(organizacion_id, TRUE)"


def _postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "organizacion_id",
            sa.Integer(),
            sa.ForeignKey("organizaciones.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("plan", sa.String(length=20), nullable=False),
        sa.Column("metodo_pago", sa.String(length=30), nullable=False),
        sa.Column("importe", sa.Float(), nullable=False, server_default="0"),
        sa.Column("moneda", sa.String(length=10), nullable=False, server_default="USD"),
        sa.Column(
            "datos_verificacion", sa.Text(), nullable=False, server_default="{}"
        ),
        sa.Column(
            "comprobante_reference", sa.String(length=500), nullable=False,
            server_default="",
        ),
        sa.Column(
            "comprobante_nombre", sa.String(length=255), nullable=False,
            server_default="",
        ),
        sa.Column(
            "comprobante_mime", sa.String(length=150), nullable=False,
            server_default="",
        ),
        sa.Column(
            "estado", sa.String(length=20), nullable=False, server_default="pendiente"
        ),
        sa.Column(
            "creada_por_usuario_id",
            sa.Integer(),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "creada_por_email", sa.String(length=254), nullable=False, server_default=""
        ),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column(
            "licencia_id",
            sa.Integer(),
            sa.ForeignKey("licencias.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "revisado_por_email", sa.String(length=254), nullable=False, server_default=""
        ),
        sa.Column("revisado_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "plan IN ('anual', 'mensual')", name="ck_compra_plan_valido"
        ),
        sa.CheckConstraint(
            "metodo_pago IN ('pago_movil', 'binance', 'kontigo', 'usdt')",
            name="ck_compra_metodo_valido",
        ),
        sa.CheckConstraint(
            "estado IN ('pendiente', 'activa', 'rechazada')",
            name="ck_compra_estado_valido",
        ),
        sa.CheckConstraint(
            "importe >= 0", name="ck_compra_importe_no_negativo"
        ),
    )
    op.create_index(
        "ix_compras_plan_estado", TABLE, ["organizacion_id", "estado", "created_at"]
    )

    if not _postgres():
        # SQLite (escritorio y pruebas) no tiene RLS: el aislamiento lo aporta
        # la aplicación (organización activa en la sesión).
        return

    op.execute(f"REVOKE ALL ON TABLE public.{TABLE} FROM PUBLIC")
    op.execute(f"ALTER TABLE public.{TABLE} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE public.{TABLE} FORCE ROW LEVEL SECURITY")
    op.execute(
        f"GRANT SELECT, INSERT, UPDATE ON TABLE public.{TABLE} TO {APP_ROLE}"
    )
    op.execute(
        f"GRANT USAGE, SELECT ON SEQUENCE public.{TABLE}_id_seq TO {APP_ROLE}"
    )

    for nombre, accion, clausula in (
        ("cotizat_compra_select_tenant", "SELECT", f"USING ({TENANT_READ})"),
        ("cotizat_compra_select_operator", "SELECT", f"USING ({IS_OPERATOR})"),
        ("cotizat_compra_insert_tenant", "INSERT", f"WITH CHECK ({TENANT_WRITE})"),
        (
            "cotizat_compra_update_operator",
            "UPDATE",
            f"USING ({IS_OPERATOR}) WITH CHECK ({IS_OPERATOR})",
        ),
    ):
        op.execute(f"DROP POLICY IF EXISTS {nombre} ON public.{TABLE}")
        op.execute(
            f"CREATE POLICY {nombre} ON public.{TABLE} "
            f"FOR {accion} TO {APP_ROLE} {clausula}"
        )


def downgrade() -> None:
    if _postgres():
        for nombre in (
            "cotizat_compra_select_tenant",
            "cotizat_compra_select_operator",
            "cotizat_compra_insert_tenant",
            "cotizat_compra_update_operator",
        ):
            op.execute(f"DROP POLICY IF EXISTS {nombre} ON public.{TABLE}")
        op.execute(f"ALTER TABLE public.{TABLE} DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_compras_plan_estado", table_name=TABLE)
    op.drop_table(TABLE)
