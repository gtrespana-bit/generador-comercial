"""Conversaciones del asistente y lectura restringida para el operador.

La interfaz del Copilot conserva el historial únicamente en memoria. Esta
revisión añade el agregado tenant que permite analizar las dudas reales sin
abrir los datos de una organización a otra:

* ``conversaciones_ia`` guarda la organización, el usuario (si existe), una
  instantánea del correo, título, página de origen y fechas de retención.
* ``mensajes_ia`` guarda cada mensaje de usuario/asistente en orden, con una
  clave de turno para que los reintentos del navegador sean idempotentes.
* PostgreSQL aplica RLS tenant para la aplicación y una política separada de
  operador para ``get_operator_db``. El rol de runtime nunca obtiene acceso
  por el mero hecho de conocer un ``public_id``.

La retención operativa es de 365 días desde el último turno. El trabajo de
mantenimiento purga los agregados vencidos; el panel tampoco muestra una fila
fuera de esa ventana.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "g7c8d9e0f1a2"
down_revision: Union[str, Sequence[str], None] = "f6d1a9c3e8b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

APP_ROLE = "cotizat_app"
CONVERSATIONS_TABLE = "conversaciones_ia"
MESSAGES_TABLE = "mensajes_ia"

IS_OPERATOR = """
  COALESCE(
    pg_catalog.current_setting('cotizat.es_operador', true) = 'on',
    FALSE
  )
"""
TENANT_READ = "cotizat_security.tenant_access(organizacion_id, FALSE)"
TENANT_WRITE = "cotizat_security.tenant_access(organizacion_id, TRUE)"

# La migración anterior ya contiene la versión completa de la baja de una
# organización (compras + auditoría). Se reutiliza y se le anteponen las dos
# tablas nuevas para no mantener dos copias divergentes del resto del grafo.
try:
    from .d2a7c9e4f1b3_audit_log_and_complete_baja import (  # type: ignore
        BAJA_ACTUALIZADA_SQL as _BAJA_BASE_SQL,
    )
except ImportError:  # Alembic carga los scripts como módulos sin paquete.
    import importlib.util
    from pathlib import Path

    _base_path = Path(__file__).with_name(
        "d2a7c9e4f1b3_audit_log_and_complete_baja.py"
    )
    _base_spec = importlib.util.spec_from_file_location(
        "_cotizat_baja_base", _base_path
    )
    if _base_spec is None or _base_spec.loader is None:  # pragma: no cover
        raise ImportError(f"No se pudo cargar {_base_path}")
    _base_module = importlib.util.module_from_spec(_base_spec)
    _base_spec.loader.exec_module(_base_module)
    _BAJA_BASE_SQL = _base_module.BAJA_ACTUALIZADA_SQL

BAJA_CONVERSACIONES_SQL = _BAJA_BASE_SQL.replace(
    "  DELETE FROM public.licencias",
    """  DELETE FROM public.mensajes_ia
    WHERE organizacion_id = p_organization_id;
  DELETE FROM public.conversaciones_ia
    WHERE organizacion_id = p_organization_id;
  DELETE FROM public.licencias""",
    1,
)


def _postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def _politicas_tenant(table: str) -> tuple[str, ...]:
    return (
        f"cotizat_{table}_select_tenant",
        f"cotizat_{table}_select_operator",
        f"cotizat_{table}_insert_tenant",
        f"cotizat_{table}_update_tenant",
        f"cotizat_{table}_delete_tenant",
        f"cotizat_{table}_update_operator",
        f"cotizat_{table}_delete_operator",
    )


def _instalar_rls(table: str, *, permitir_insert_operator: bool = False) -> None:
    op.execute(f"REVOKE ALL ON TABLE public.{table} FROM PUBLIC")
    op.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE public.{table} FORCE ROW LEVEL SECURITY")
    op.execute(
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.{table} TO {APP_ROLE}"
    )
    op.execute(
        f"GRANT USAGE, SELECT ON SEQUENCE public.{table}_id_seq TO {APP_ROLE}"
    )

    for nombre in _politicas_tenant(table):
        op.execute(f"DROP POLICY IF EXISTS {nombre} ON public.{table}")

    # El FK simple también necesita una comprobación de tenant en el padre:
    # una sesión no debe poder adivinar un ``conversacion_id`` de otra empresa
    # y adjuntarle un mensaje propio.
    comprobacion_padre = ""
    if table == MESSAGES_TABLE:
        comprobacion_padre = (
            " AND EXISTS (SELECT 1 FROM public.conversaciones_ia c "
            "WHERE c.id = conversacion_id "
            f"AND c.organizacion_id = public.{MESSAGES_TABLE}.organizacion_id)"
        )
    condicion_escritura = f"{TENANT_WRITE}{comprobacion_padre}"

    op.execute(f"""
        CREATE POLICY cotizat_{table}_select_tenant ON public.{table}
        FOR SELECT TO {APP_ROLE}
        USING ({TENANT_READ})
    """)
    op.execute(f"""
        CREATE POLICY cotizat_{table}_select_operator ON public.{table}
        FOR SELECT TO {APP_ROLE}
        USING ({IS_OPERATOR})
    """)
    op.execute(f"""
        CREATE POLICY cotizat_{table}_insert_tenant ON public.{table}
        FOR INSERT TO {APP_ROLE}
        WITH CHECK ({condicion_escritura})
    """)
    if permitir_insert_operator:
        op.execute(f"""
            CREATE POLICY cotizat_{table}_update_operator ON public.{table}
            FOR ALL TO {APP_ROLE}
            USING ({IS_OPERATOR})
            WITH CHECK ({IS_OPERATOR})
        """)
    else:
        op.execute(f"""
            CREATE POLICY cotizat_{table}_update_operator ON public.{table}
            FOR UPDATE TO {APP_ROLE}
            USING ({IS_OPERATOR})
            WITH CHECK ({IS_OPERATOR})
        """)
        op.execute(f"""
            CREATE POLICY cotizat_{table}_delete_operator ON public.{table}
            FOR DELETE TO {APP_ROLE}
            USING ({IS_OPERATOR})
        """)
    op.execute(f"""
        CREATE POLICY cotizat_{table}_update_tenant ON public.{table}
        FOR UPDATE TO {APP_ROLE}
        USING ({condicion_escritura})
        WITH CHECK ({condicion_escritura})
    """)
    op.execute(f"""
        CREATE POLICY cotizat_{table}_delete_tenant ON public.{table}
        FOR DELETE TO {APP_ROLE}
        USING ({TENANT_WRITE})
    """)


def upgrade() -> None:
    op.create_table(
        CONVERSATIONS_TABLE,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "organizacion_id",
            sa.Integer(),
            sa.ForeignKey("organizaciones.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("public_id", sa.String(length=64), nullable=False),
        sa.Column(
            "usuario_id",
            sa.Integer(),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("usuario_email", sa.String(length=254), nullable=False, server_default=""),
        sa.Column("titulo", sa.String(length=180), nullable=False, server_default=""),
        sa.Column("pagina_inicio", sa.String(length=240), nullable=False, server_default=""),
        sa.Column("estado", sa.String(length=20), nullable=False, server_default="activa"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "ultimo_mensaje_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        # El servicio fija la fecha exacta desde el último turno. El default
        # portable permite insertar una fila desde una herramienta SQL sin
        # convertir el esquema SQLite en dependiente de INTERVAL de Postgres.
        sa.Column(
            "expires_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint("public_id", name="uq_conversacion_ia_public_id"),
        sa.CheckConstraint(
            "estado IN ('activa', 'archivada')",
            name="ck_conversacion_ia_estado_valido",
        ),
    )
    op.create_index(
        "ix_conversaciones_ia_org_ultimo",
        CONVERSATIONS_TABLE,
        ["organizacion_id", "ultimo_mensaje_at"],
    )
    op.create_index(
        "ix_conversaciones_ia_org_usuario",
        CONVERSATIONS_TABLE,
        ["organizacion_id", "usuario_id"],
    )
    op.create_index(
        "ix_conversaciones_ia_usuario_id",
        CONVERSATIONS_TABLE,
        ["usuario_id"],
    )
    op.create_index(
        "ix_conversaciones_ia_expira",
        CONVERSATIONS_TABLE,
        ["expires_at"],
    )

    op.create_table(
        MESSAGES_TABLE,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "organizacion_id",
            sa.Integer(),
            sa.ForeignKey("organizaciones.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "conversacion_id",
            sa.Integer(),
            sa.ForeignKey("conversaciones_ia.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rol", sa.String(length=20), nullable=False),
        sa.Column("contenido", sa.Text(), nullable=False),
        sa.Column("orden", sa.Integer(), nullable=False),
        sa.Column("turn_id", sa.String(length=80), nullable=True),
        sa.Column("completo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint(
            "rol IN ('user', 'assistant')",
            name="ck_mensaje_ia_rol_valido",
        ),
        sa.CheckConstraint("orden >= 0", name="ck_mensaje_ia_orden_no_negativo"),
        sa.UniqueConstraint(
            "conversacion_id",
            "orden",
            name="uq_mensaje_ia_conversacion_orden",
        ),
        sa.UniqueConstraint(
            "conversacion_id",
            "rol",
            "turn_id",
            name="uq_mensaje_ia_conversacion_turno_rol",
        ),
    )
    op.create_index(
        "ix_mensajes_ia_conversacion_orden",
        MESSAGES_TABLE,
        ["conversacion_id", "orden"],
    )
    op.create_index(
        "ix_mensajes_ia_conversacion_id",
        MESSAGES_TABLE,
        ["conversacion_id"],
    )
    op.create_index(
        "ix_mensajes_ia_org_fecha",
        MESSAGES_TABLE,
        ["organizacion_id", "created_at"],
    )

    if not _postgres():
        return

    _instalar_rls(CONVERSATIONS_TABLE, permitir_insert_operator=False)
    _instalar_rls(MESSAGES_TABLE, permitir_insert_operator=False)

    # La nueva tabla también forma parte del borrado verificado de una cuenta.
    op.execute(BAJA_CONVERSACIONES_SQL)
    op.execute(
        "ALTER FUNCTION cotizat_security.baja_organizacion(integer) OWNER TO CURRENT_USER"
    )
    op.execute(
        "REVOKE ALL ON FUNCTION cotizat_security.baja_organizacion(integer) FROM PUBLIC"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION cotizat_security.baja_organizacion(integer) "
        f"TO {APP_ROLE}"
    )


def downgrade() -> None:
    if _postgres():
        # Al volver a f6 la función de baja no puede conservar referencias a
        # tablas que ya no existen.
        op.execute(_BAJA_BASE_SQL)
        op.execute(
            "ALTER FUNCTION cotizat_security.baja_organizacion(integer) OWNER TO CURRENT_USER"
        )
        op.execute(
            "REVOKE ALL ON FUNCTION cotizat_security.baja_organizacion(integer) FROM PUBLIC"
        )
        op.execute(
            "GRANT EXECUTE ON FUNCTION cotizat_security.baja_organizacion(integer) "
            f"TO {APP_ROLE}"
        )
        for nombre in _politicas_tenant(CONVERSATIONS_TABLE):
            op.execute(
                f"DROP POLICY IF EXISTS {nombre} ON public.{CONVERSATIONS_TABLE}"
            )
        for nombre in _politicas_tenant(MESSAGES_TABLE):
            op.execute(f"DROP POLICY IF EXISTS {nombre} ON public.{MESSAGES_TABLE}")
        op.execute(
            f"ALTER TABLE public.{MESSAGES_TABLE} NO FORCE ROW LEVEL SECURITY"
        )
        op.execute(
            f"ALTER TABLE public.{CONVERSATIONS_TABLE} NO FORCE ROW LEVEL SECURITY"
        )
        op.execute(
            f"REVOKE ALL ON SEQUENCE public.{MESSAGES_TABLE}_id_seq FROM {APP_ROLE}"
        )
        op.execute(
            f"REVOKE ALL ON SEQUENCE public.{CONVERSATIONS_TABLE}_id_seq FROM {APP_ROLE}"
        )
        op.execute(
            f"REVOKE ALL ON TABLE public.{MESSAGES_TABLE} FROM {APP_ROLE}"
        )
        op.execute(
            f"REVOKE ALL ON TABLE public.{CONVERSATIONS_TABLE} FROM {APP_ROLE}"
        )

    op.drop_index("ix_mensajes_ia_org_fecha", table_name=MESSAGES_TABLE)
    op.drop_index("ix_mensajes_ia_conversacion_id", table_name=MESSAGES_TABLE)
    op.drop_index("ix_mensajes_ia_conversacion_orden", table_name=MESSAGES_TABLE)
    op.drop_table(MESSAGES_TABLE)
    op.drop_index("ix_conversaciones_ia_expira", table_name=CONVERSATIONS_TABLE)
    op.drop_index("ix_conversaciones_ia_usuario_id", table_name=CONVERSATIONS_TABLE)
    op.drop_index("ix_conversaciones_ia_org_usuario", table_name=CONVERSATIONS_TABLE)
    op.drop_index("ix_conversaciones_ia_org_ultimo", table_name=CONVERSATIONS_TABLE)
    op.drop_table(CONVERSATIONS_TABLE)
