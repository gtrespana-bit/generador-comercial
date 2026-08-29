"""Roles de operador y auditoría del panel (Fase 1).

Crea dos tablas del negocio del titular (no de tenant):

- ``public.operadores_producto``: quién administra el producto y con qué rol.
  ``COTIZAT_OPERADORES`` sigue siendo la semilla; esta tabla permite escalarlo
  desde el panel con rol y suspensión.
- ``public.eventos_admin``: auditoría inmutable de las acciones del panel
  (quién concedió, revocó, activó, cambió un rol).

Seguridad en PostgreSQL
-----------------------
``operadores_producto``
- ``SELECT``: sesión de operador **o** el propio correo. La excepción propia
  es necesaria para que un operador añadido por el panel pueda autenticar
  sin tocar la variable de entorno: en ese momento la sesión aún no lleva la
  marca ``cotizat.es_operador``.
- ``INSERT/UPDATE/DELETE``: solo sesión de operador con rol ``superadmin``
  (claim ``cotizat.operador_rol``). Un operador de soporte o analista no
  puede nombrar ni rebajar a nadie.

``eventos_admin``
- ``SELECT/INSERT``: solo sesión de operador. Inmutable: sin ``UPDATE`` ni
  ``DELETE`` (la aplicación nunca los invoca y el rol runtime no los recibe).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b8c2d4e6f0"
down_revision: Union[str, Sequence[str], None] = "e3a5c7d9b1f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

APP_ROLE = "cotizat_app"

IS_OPERATOR = """
  COALESCE(
    pg_catalog.current_setting('cotizat.es_operador', true) = 'on',
    FALSE
  )
"""

IS_SUPERADMIN = """
  COALESCE(
    pg_catalog.current_setting('cotizat.operador_rol', true) = 'superadmin',
    FALSE
  )
"""

MISMO_EMAIL = """
  LOWER(email) = pg_catalog.current_setting('cotizat.auth_email', true)
"""


def _postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    # ------------------------------------------------------------------
    # operadores_producto
    # ------------------------------------------------------------------
    op.create_table(
        "operadores_producto",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("rol", sa.String(length=30), nullable=False, server_default="admin"),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notas", sa.Text(), nullable=False, server_default=""),
        sa.Column("creado_por_email", sa.String(length=254), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("email", name="uq_operadores_producto_email"),
        sa.CheckConstraint(
            "rol IN ('superadmin', 'admin', 'soporte', 'analista')",
            name="ck_operador_rol_valido",
        ),
    )
    op.create_index("ix_operadores_producto_email", "operadores_producto", ["email"])

    # ------------------------------------------------------------------
    # eventos_admin (auditoría del panel)
    # ------------------------------------------------------------------
    op.create_table(
        "eventos_admin",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("operador_email", sa.String(length=254), nullable=False, server_default=""),
        sa.Column("operador_rol", sa.String(length=30), nullable=False, server_default=""),
        sa.Column("accion", sa.String(length=60), nullable=False),
        sa.Column("entidad", sa.String(length=40), nullable=False, server_default=""),
        sa.Column("entidad_id", sa.Integer(), nullable=True),
        sa.Column(
            "organizacion_id",
            sa.Integer(),
            sa.ForeignKey("organizaciones.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("detalle", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("ip_hash", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("resultado", sa.String(length=20), nullable=False, server_default="ok"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_eventos_admin_fecha", "eventos_admin", ["created_at"])
    op.create_index(
        "ix_eventos_admin_actor", "eventos_admin", ["operador_email", "created_at"]
    )
    op.create_index(
        "ix_eventos_admin_org", "eventos_admin", ["organizacion_id", "created_at"]
    )
    op.create_index("ix_eventos_admin_accion", "eventos_admin", ["accion", "created_at"])

    if not _postgres():
        # SQLite (escritorio y pruebas) no tiene RLS; el aislamiento lo aporta
        # la aplicación (siempre una sesión de operador).
        return

    # ------------------------------------------------------------------
    # RLS operadores_producto
    # ------------------------------------------------------------------
    op.execute("REVOKE ALL ON TABLE public.operadores_producto FROM PUBLIC")
    op.execute("ALTER TABLE public.operadores_producto ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE public.operadores_producto FORCE ROW LEVEL SECURITY")
    op.execute(f"GRANT SELECT, INSERT, UPDATE ON TABLE public.operadores_producto TO {APP_ROLE}")
    op.execute(f"GRANT USAGE, SELECT ON SEQUENCE public.operadores_producto_id_seq TO {APP_ROLE}")

    for nombre, accion, clausula in (
        ("cotizat_operador_select_own", "SELECT", f"USING ({IS_OPERATOR} OR {MISMO_EMAIL})"),
        ("cotizat_operador_insert_superadmin", "INSERT", f"WITH CHECK ({IS_OPERATOR} AND {IS_SUPERADMIN})"),
        ("cotizat_operador_update_superadmin", "UPDATE", f"USING ({IS_OPERATOR} AND {IS_SUPERADMIN}) WITH CHECK ({IS_OPERATOR} AND {IS_SUPERADMIN})"),
        ("cotizat_operador_delete_superadmin", "DELETE", f"USING ({IS_OPERATOR} AND {IS_SUPERADMIN})"),
    ):
        op.execute(f"DROP POLICY IF EXISTS {nombre} ON public.operadores_producto")
        op.execute(
            f"CREATE POLICY {nombre} ON public.operadores_producto "
            f"FOR {accion} TO {APP_ROLE} {clausula}"
        )

    # ------------------------------------------------------------------
    # RLS eventos_admin
    # ------------------------------------------------------------------
    op.execute("REVOKE ALL ON TABLE public.eventos_admin FROM PUBLIC")
    op.execute("ALTER TABLE public.eventos_admin ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE public.eventos_admin FORCE ROW LEVEL SECURITY")
    op.execute(f"GRANT SELECT, INSERT ON TABLE public.eventos_admin TO {APP_ROLE}")
    op.execute(f"GRANT USAGE, SELECT ON SEQUENCE public.eventos_admin_id_seq TO {APP_ROLE}")

    for nombre, accion, clausula in (
        ("cotizat_evento_admin_select", "SELECT", f"USING ({IS_OPERATOR})"),
        ("cotizat_evento_admin_insert", "INSERT", f"WITH CHECK ({IS_OPERATOR})"),
    ):
        op.execute(f"DROP POLICY IF EXISTS {nombre} ON public.eventos_admin")
        op.execute(
            f"CREATE POLICY {nombre} ON public.eventos_admin "
            f"FOR {accion} TO {APP_ROLE} {clausula}"
        )


def downgrade() -> None:
    if _postgres():
        for nombre in (
            "cotizat_evento_admin_select",
            "cotizat_evento_admin_insert",
            "cotizat_operador_select_own",
            "cotizat_operador_insert_superadmin",
            "cotizat_operador_update_superadmin",
            "cotizat_operador_delete_superadmin",
        ):
            op.execute(f"DROP POLICY IF EXISTS {nombre} ON public.operadores_producto")
            op.execute(f"DROP POLICY IF EXISTS {nombre} ON public.eventos_admin")
        op.execute("ALTER TABLE public.operadores_producto DISABLE ROW LEVEL SECURITY")
        op.execute("ALTER TABLE public.eventos_admin DISABLE ROW LEVEL SECURITY")

    op.drop_index("ix_eventos_admin_accion", table_name="eventos_admin")
    op.drop_index("ix_eventos_admin_org", table_name="eventos_admin")
    op.drop_index("ix_eventos_admin_actor", table_name="eventos_admin")
    op.drop_index("ix_eventos_admin_fecha", table_name="eventos_admin")
    op.drop_table("eventos_admin")
    op.drop_index("ix_operadores_producto_email", table_name="operadores_producto")
    op.drop_table("operadores_producto")
