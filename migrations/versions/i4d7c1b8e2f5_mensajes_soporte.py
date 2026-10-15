"""Buzón de soporte: ``public.mensajes_soporte``.

El canal de soporte era el correo a secas. Ahora el cliente escribe desde la
aplicación (botón «Soporte») y el mensaje se guarda aquí **antes** de intentar
el aviso por Resend: si el proveedor falla, el mensaje no se pierde y el panel
lo muestra igualmente. La respuesta se hace desde el buzón de correo, con
``reply_to`` del cliente.

Por qué **no es una tabla de tenant**, aunque tenga ``organizacion_id``:

- Quien escribe puede no tener cuenta (visita en la landing), así que la
  organización es opcional con ``ON DELETE SET NULL``: dar de baja una empresa
  no borra la conversación con esa persona.
- El titular es el único que lee el buzón. En PostgreSQL la política es de
  operador (``cotizat.es_operador``) para SELECT y UPDATE, con INSERT abierto a
  la aplicación para que el formulario público funcione sin sesión — pero
  **forzando** ``estado = 'nuevo'`` y sin permiso de DELETE: un mensaje no se
  borra desde la aplicación, solo se marca.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "i4d7c1b8e2f5"
down_revision: Union[str, Sequence[str], None] = "h1c4b7e9a3d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "mensajes_soporte"
APP_ROLE = "cotizat_app"

IS_OPERATOR = """
  COALESCE(
    pg_catalog.current_setting('cotizat.es_operador', true) = 'on',
    FALSE
  )
"""


def _postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("email", sa.String(length=254), nullable=False, server_default=""),
        sa.Column(
            "organizacion_id",
            sa.Integer(),
            sa.ForeignKey("organizaciones.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "usuario_id",
            sa.Integer(),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("tipo", sa.String(length=20), nullable=False, server_default="consulta"),
        sa.Column("asunto", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("mensaje", sa.Text(), nullable=False, server_default=""),
        sa.Column("pagina", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("estado", sa.String(length=20), nullable=False, server_default="nuevo"),
        sa.Column("nota_interna", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "atendido_por_email", sa.String(length=254), nullable=False, server_default=""
        ),
        sa.Column("atendido_at", sa.DateTime(), nullable=True),
        sa.Column(
            "aviso_enviado", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("ip_hash", sa.String(length=64), nullable=False, server_default=""),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "tipo IN ('consulta', 'problema', 'queja', 'sugerencia', "
            "'facturacion', 'otro')",
            name="ck_mensaje_soporte_tipo_valido",
        ),
        sa.CheckConstraint(
            "estado IN ('nuevo', 'en_proceso', 'resuelto')",
            name="ck_mensaje_soporte_estado_valido",
        ),
    )
    op.create_index(
        "ix_mensajes_soporte_estado", TABLE, ["estado", "created_at"]
    )
    op.create_index("ix_mensajes_soporte_email", TABLE, ["email"])
    op.create_index(
        "ix_mensajes_soporte_org", TABLE, ["organizacion_id", "created_at"]
    )

    if not _postgres():
        # SQLite (escritorio y pruebas) no tiene RLS: el aislamiento lo aporta
        # la aplicación, que solo permite leer el buzón desde el panel.
        return

    op.execute(f"REVOKE ALL ON TABLE public.{TABLE} FROM PUBLIC")
    op.execute(f"ALTER TABLE public.{TABLE} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE public.{TABLE} FORCE ROW LEVEL SECURITY")
    # GRANT sin DELETE: un mensaje no se borra desde la aplicación.
    op.execute(f"GRANT SELECT, INSERT, UPDATE ON TABLE public.{TABLE} TO {APP_ROLE}")
    op.execute(f"GRANT USAGE, SELECT ON SEQUENCE public.{TABLE}_id_seq TO {APP_ROLE}")

    for nombre, accion, clausula in (
        ("cotizat_ms_select_operator", "SELECT", f"USING ({IS_OPERATOR})"),
        ("cotizat_ms_update_operator", "UPDATE", f"USING ({IS_OPERATOR})"),
        # El formulario público no tiene sesión ni marca de operador: puede
        # insertar, pero solo como mensaje nuevo y sin fingir gestión previa.
        (
            "cotizat_ms_insert_publico",
            "INSERT",
            "WITH CHECK (estado = 'nuevo' AND atendido_por_email = '' "
            "AND nota_interna = '')",
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
            "cotizat_ms_select_operator",
            "cotizat_ms_update_operator",
            "cotizat_ms_insert_publico",
        ):
            op.execute(f"DROP POLICY IF EXISTS {nombre} ON public.{TABLE}")
        op.execute(f"ALTER TABLE public.{TABLE} DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_mensajes_soporte_org", table_name=TABLE)
    op.drop_index("ix_mensajes_soporte_email", table_name=TABLE)
    op.drop_index("ix_mensajes_soporte_estado", table_name=TABLE)
    op.drop_table(TABLE)
