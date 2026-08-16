"""Licencias del producto y marca de operador (E1-060).

Crea ``public.licencias``, el registro interno de licencias que el titular usa
para conceder acceso, regalar meses o compensar una incidencia.

Por qué esta tabla es distinta a todas las demás
------------------------------------------------
El resto de tablas de negocio son *tenant*: llevan ``organizacion_id`` y sus
políticas comparan ese valor con la organización activa de la sesión. Una
licencia también apunta a una organización, pero **no pertenece a ella**: es
información del titular del producto *sobre* un cliente (cuánto paga, hasta
cuándo, por qué). Aplicarle la política de tenant la haría visible al propio
cliente, que es justo lo contrario de lo que se necesita.

Por eso `licencias` estrena su propio criterio de acceso: la sesión debe estar
marcada como **operador**. La marca viaja en el claim local
``cotizat.es_operador``, que la aplicación solo activa cuando el correo
autenticado y verificado figura en ``COTIZAT_OPERADORES`` (ver
``app/operadores.py``). Un cliente nunca la lleva, así que para él la tabla
está vacía aunque una consulta llegara a alcanzarla.

Defensa en profundidad, no confianza en el código
-------------------------------------------------
La lista de operadores es una variable de entorno, no una columna: no se puede
escalar privilegios escribiendo en la base. Y aunque la comprobación de Python
fallara, RLS seguiría negando las filas. Las dos barreras son independientes.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f4c1d8e37a95"
down_revision: Union[str, Sequence[str], None] = "e1a4b7c9d2f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "licencias"
APP_ROLE = "cotizat_app"

#: Verdadero solo si la sesión declaró la marca de operador. ``current_setting``
#: con ``true`` devuelve NULL si el claim no existe, así que el valor por
#: omisión de cualquier sesión —incluida la de un cliente— es FALSE.
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
        sa.Column(
            "organizacion_id",
            sa.Integer(),
            sa.ForeignKey("organizaciones.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("estado", sa.String(length=20), nullable=False, server_default="activa"),
        sa.Column("origen", sa.String(length=20), nullable=False, server_default="pago"),
        sa.Column("inicio", sa.Date(), nullable=False),
        sa.Column("vence", sa.Date(), nullable=False),
        sa.Column("importe", sa.Float(), nullable=False, server_default="0"),
        sa.Column("moneda", sa.String(length=10), nullable=False, server_default="USD"),
        sa.Column("metodo_cobro", sa.String(length=80), server_default=""),
        sa.Column("referencia", sa.String(length=150), server_default=""),
        sa.Column("notas", sa.Text(), server_default=""),
        sa.Column("creada_por_email", sa.String(length=254), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "estado IN ('activa', 'vencida', 'cancelada')",
            name="ck_licencia_estado_valido",
        ),
        sa.CheckConstraint(
            "origen IN ('pago', 'prueba', 'cortesia', 'compensacion')",
            name="ck_licencia_origen_valido",
        ),
        sa.CheckConstraint("importe >= 0", name="ck_licencia_importe_no_negativo"),
    )
    op.create_index(
        "ix_licencias_organizacion_inicio", TABLE, ["organizacion_id", "inicio"]
    )

    if not _postgres():
        # SQLite (escritorio y pruebas) no tiene RLS: el aislamiento lo aporta
        # la comprobación de operador en la aplicación.
        return

    op.execute(f"REVOKE ALL ON TABLE public.{TABLE} FROM PUBLIC")
    op.execute(f"ALTER TABLE public.{TABLE} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE public.{TABLE} FORCE ROW LEVEL SECURITY")
    op.execute(
        f"GRANT SELECT, INSERT, UPDATE ON TABLE public.{TABLE} TO {APP_ROLE}"
    )
    # Sin DELETE a propósito: una licencia se cancela, no se borra. Conservar el
    # historial es lo que permite reconstruir qué se cobró y cuándo.
    op.execute(
        f"GRANT USAGE, SELECT ON SEQUENCE public.{TABLE}_id_seq TO {APP_ROLE}"
    )

    for accion, clausula in (
        ("SELECT", f"USING ({IS_OPERATOR})"),
        ("INSERT", f"WITH CHECK ({IS_OPERATOR})"),
        ("UPDATE", f"USING ({IS_OPERATOR}) WITH CHECK ({IS_OPERATOR})"),
    ):
        nombre = f"cotizat_licencia_{accion.lower()}"
        op.execute(f"DROP POLICY IF EXISTS {nombre} ON public.{TABLE}")
        op.execute(f"""
            CREATE POLICY {nombre} ON public.{TABLE}
            FOR {accion} TO {APP_ROLE}
            {clausula}
        """)


def downgrade() -> None:
    if _postgres():
        for accion in ("select", "insert", "update"):
            op.execute(
                f"DROP POLICY IF EXISTS cotizat_licencia_{accion} ON public.{TABLE}"
            )
    op.drop_index("ix_licencias_organizacion_inicio", table_name=TABLE)
    op.drop_table(TABLE)
