"""Correos de marketing: historial de envíos y bajas con un clic.

Cada correo de la secuencia (bienvenida, consejos, win-back) se registra en
``envios_marketing`` para que sea idempotente —aunque el cron se ejecute dos
veces el mismo día, cada plantilla llega una sola vez por organización— y para
auditar qué funcionó sin rebuscar en logs efímeros.

``bajas_marketing`` guarda quién pidió no recibir publicidad. Solo detiene
los correos de marketing; los transaccionales (invitaciones, recibos, avisos
de vencimiento) siguen llegando porque son el servicio contratado, no
publicidad. La baja se pide desde un enlace público con token firmado
(``/baja-marketing``), sin sesión.

Seguridad PostgreSQL
--------------------
Ambas tablas son datos del negocio del titular *sobre* las organizaciones,
igual que ``licencias`` y ``pruebas_concedidas``: nunca son tenant y nunca
las ve una sesión de cliente. Solo el operador puede leerlas; la escritura
entra por el servicio de marketing (sesión con ``cotizat.es_operador = on``).
En SQLite no hay RLS y la app ya filtra por sesión.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "z3m9k2p8v1n7"
down_revision: Union[str, Sequence[str], None] = "y1n3p5q7r9s2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

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
        "envios_marketing",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organizacion_id", sa.Integer(), sa.ForeignKey("organizaciones.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("email", sa.String(length=254), nullable=False, server_default=""),
        sa.Column("plantilla", sa.String(length=60), nullable=False, server_default=""),
        sa.Column("estado", sa.String(length=20), nullable=False, server_default="enviado"),
        sa.Column("proveedor_id", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("enviado_en", sa.DateTime(), nullable=False, server_default=sa.text("clock_timestamp()")),
        sa.UniqueConstraint("organizacion_id", "plantilla", name="uq_envio_marketing_org_plantilla"),
    )
    op.create_index("ix_envios_marketing_enviado", "envios_marketing", ["enviado_en"])
    op.create_index("ix_envios_marketing_email", "envios_marketing", ["email"])

    op.create_table(
        "bajas_marketing",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("origen", sa.String(length=20), nullable=False, server_default="enlace"),
        sa.Column("creada_en", sa.DateTime(), nullable=False, server_default=sa.text("clock_timestamp()")),
        sa.UniqueConstraint("email", name="uq_baja_marketing_email"),
    )
    op.create_index("ix_bajas_marketing_creada", "bajas_marketing", ["creada_en"])

    if not _postgres():
        return

    # RLS: solo operador (igual que licencias / pruebas_concedidas)
    for tabla in ("envios_marketing", "bajas_marketing"):
        op.execute(f"REVOKE ALL ON TABLE public.{tabla} FROM PUBLIC")
        op.execute(f"ALTER TABLE public.{tabla} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE public.{tabla} FORCE ROW LEVEL SECURITY")
        op.execute(f"GRANT SELECT, INSERT, UPDATE ON TABLE public.{tabla} TO {APP_ROLE}")
        op.execute(f"GRANT USAGE, SELECT ON SEQUENCE public.{tabla}_id_seq TO {APP_ROLE}")
        op.execute(
            f"DROP POLICY IF EXISTS cotizat_{tabla}_operador ON public.{tabla}"
        )
        op.execute(
            f"CREATE POLICY cotizat_{tabla}_operador ON public.{tabla} "
            f"FOR ALL TO {APP_ROLE} USING ({IS_OPERATOR}) WITH CHECK ({IS_OPERATOR})"
        )


def downgrade() -> None:
    if _postgres():
        for tabla in ("bajas_marketing", "envios_marketing"):
            op.execute(f"DROP POLICY IF EXISTS cotizat_{tabla}_operador ON public.{tabla}")
            # RLS off antes de borrar para que el downgrade no dependa de la marca
            op.execute(f"ALTER TABLE public.{tabla} DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_bajas_marketing_creada", table_name="bajas_marketing")
    op.drop_table("bajas_marketing")
    op.drop_index("ix_envios_marketing_email", table_name="envios_marketing")
    op.drop_index("ix_envios_marketing_enviado", table_name="envios_marketing")
    op.drop_table("envios_marketing")
