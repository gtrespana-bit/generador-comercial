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

    # RLS: solo operador (igual que licencias / pruebas_concedidas).
    # Grants explícitos por tabla (no en bucle con variable) para que
    # tests/test_rls.py los detecte por nombre literal.
    op.execute("REVOKE ALL ON TABLE public.envios_marketing FROM PUBLIC")
    op.execute("ALTER TABLE public.envios_marketing ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE public.envios_marketing FORCE ROW LEVEL SECURITY")
    op.execute("GRANT SELECT, INSERT, UPDATE ON TABLE public.envios_marketing TO cotizat_app")
    op.execute("GRANT USAGE, SELECT ON SEQUENCE public.envios_marketing_id_seq TO cotizat_app")
    op.execute("DROP POLICY IF EXISTS cotizat_envios_marketing_operador ON public.envios_marketing")
    op.execute(
        f"CREATE POLICY cotizat_envios_marketing_operador ON public.envios_marketing "
        f"FOR ALL TO cotizat_app USING ({IS_OPERATOR}) WITH CHECK ({IS_OPERATOR})"
    )

    op.execute("REVOKE ALL ON TABLE public.bajas_marketing FROM PUBLIC")
    op.execute("ALTER TABLE public.bajas_marketing ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE public.bajas_marketing FORCE ROW LEVEL SECURITY")
    op.execute("GRANT SELECT, INSERT, UPDATE ON TABLE public.bajas_marketing TO cotizat_app")
    op.execute("GRANT USAGE, SELECT ON SEQUENCE public.bajas_marketing_id_seq TO cotizat_app")
    op.execute("DROP POLICY IF EXISTS cotizat_bajas_marketing_operador ON public.bajas_marketing")
    op.execute(
        f"CREATE POLICY cotizat_bajas_marketing_operador ON public.bajas_marketing "
        f"FOR ALL TO cotizat_app USING ({IS_OPERATOR}) WITH CHECK ({IS_OPERATOR})"
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
