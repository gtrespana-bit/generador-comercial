"""Fase 3 y 4 del panel: web pública, CRM ligero, salud de datos y operación.

Tablas del **titular** (no tenant), pensadas para gobernar la web y el
producto desde ``/admin``:

- ``contenido_web``: borrador/versión publicada por clave (landing, legales,
  SEO). Nunca se edita producción directa: el panel escribe un borrador y
  publica/descarta.
- ``avisos_web``: banners/avisos públicos (mantenimiento, legal, versión,
  estado).
- ``releases``: changelog visible en ``/novedades``.
- ``feature_flags``: interruptores de funcionalidad para operadores.
- ``crm_clientes``: estado comercial y próximo contacto por organización.
- ``api_keys_operador``: claves de integración del operador (NUNCA token en
  texto plano: solo ``clave_hash`` con SHA-256).

Seguridad PostgreSQL
--------------------
- ``contenido_web``/``avisos_web``/``releases``: SELECT público solo de lo
  publicado/activo (es contenido web, visible por diseño); escrituras solo
  operador. El borrador nunca sale al público.
- ``feature_flags``/``crm_clientes``/``api_keys_operador``: operador únicamente.
- Ninguna tabla obtiene DELETE: el historial de gestión se conserva.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d3e5f7a9c2b4"
down_revision: Union[str, Sequence[str], None] = "c2d4e6f8a1b3"
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


def _crear_tabla_web(nombre: str):
    raise AssertionError("Usar _crear_tabla(): función de apoyo no aplicable.")


def _crear_tabla(nombre: str, columnas: list):
    op.create_table(nombre, *columnas)


def _rl_simple(nombre: str, *, publico_si: str = None, write: bool = True):
    """Aplica RLS y grants a una tabla del titulares/operador.

    ``publico_si`` es la parte USING para SELECT público; si es ``None`` la
    tabla queda solo para operador.
    """
    op.execute(f"REVOKE ALL ON TABLE public.{nombre} FROM PUBLIC")
    op.execute(f"ALTER TABLE public.{nombre} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE public.{nombre} FORCE ROW LEVEL SECURITY")
    if write:
        op.execute(
            f"GRANT SELECT, INSERT, UPDATE ON TABLE public.{nombre} TO {APP_ROLE}"
        )
    else:
        op.execute(f"GRANT SELECT, INSERT ON TABLE public.{nombre} TO {APP_ROLE}")
    op.execute(
        f"GRANT USAGE, SELECT ON SEQUENCE public.{nombre}_id_seq TO {APP_ROLE}"
    )

    if publico_si:
        op.execute(
            f"DROP POLICY IF EXISTS cotizat_{nombre}_select_publico "
            f"ON public.{nombre}"
        )
        op.execute(
            f"CREATE POLICY cotizat_{nombre}_select_publico ON public.{nombre} "
            f"FOR SELECT TO {APP_ROLE} USING ({publico_si} OR {IS_OPERATOR})"
        )
    else:
        op.execute(
            f"DROP POLICY IF EXISTS cotizat_{nombre}_select_operator "
            f"ON public.{nombre}"
        )
        op.execute(
            f"CREATE POLICY cotizat_{nombre}_select_operator ON public.{nombre} "
            f"FOR SELECT TO {APP_ROLE} USING ({IS_OPERATOR})"
        )

    if write:
        op.execute(
            f"DROP POLICY IF EXISTS cotizat_{nombre}_insert_operator "
            f"ON public.{nombre}"
        )
        op.execute(
            f"CREATE POLICY cotizat_{nombre}_insert_operator ON public.{nombre} "
            f"FOR INSERT TO {APP_ROLE} WITH CHECK ({IS_OPERATOR})"
        )
        op.execute(
            f"DROP POLICY IF EXISTS cotizat_{nombre}_update_operator "
            f"ON public.{nombre}"
        )
        op.execute(
            f"CREATE POLICY cotizat_{nombre}_update_operator ON public.{nombre} "
            f"FOR UPDATE TO {APP_ROLE} USING ({IS_OPERATOR}) "
            f"WITH CHECK ({IS_OPERATOR})"
        )
    else:
        op.execute(
            f"DROP POLICY IF EXISTS cotizat_{nombre}_insert_operator "
            f"ON public.{nombre}"
        )
        op.execute(
            f"CREATE POLICY cotizat_{nombre}_insert_operator ON public.{nombre} "
            f"FOR INSERT TO {APP_ROLE} WITH CHECK ({IS_OPERATOR})"
        )


def upgrade() -> None:
    # ------------------------------------------------------------------
    # contenido_web (CMS publicar/descartar)
    # ------------------------------------------------------------------
    op.create_table(
        "contenido_web",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("clave", sa.String(length=80), nullable=False, unique=True),
        sa.Column("borrador", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("publicado", sa.Text(), nullable=True),
        sa.Column("publicado_por", sa.String(length=254), nullable=False, server_default=""),
        sa.Column("publicado_at", sa.DateTime(), nullable=True),
        sa.Column("updated_by", sa.String(length=254), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_contenido_web_clave", "contenido_web", ["clave"])

    # ------------------------------------------------------------------
    # avisos_web (banners/avisos públicos)
    # ------------------------------------------------------------------
    op.create_table(
        "avisos_web",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tipo", sa.String(length=30), nullable=False, server_default="info"),
        sa.Column("nivel", sa.String(length=20), nullable=False, server_default="info"),
        sa.Column("titulo", sa.String(length=180), nullable=False),
        sa.Column("mensaje", sa.Text(), nullable=False, default=""),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("inicio", sa.Date(), nullable=True),
        sa.Column("fin", sa.Date(), nullable=True),
        sa.Column("creado_por", sa.String(length=254), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_avisos_web_activo_fechas", "avisos_web", ["activo", "inicio", "fin"])

    # ------------------------------------------------------------------
    # releases (changelog)
    # ------------------------------------------------------------------
    op.create_table(
        "releases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("version", sa.String(length=30), nullable=False, unique=True),
        sa.Column("titulo", sa.String(length=200), nullable=False),
        sa.Column("notas", sa.Text(), nullable=False, default=""),
        sa.Column("destacado", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("publicado", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("fecha", sa.Date(), nullable=False, server_default=sa.text("CURRENT_DATE")),
        sa.Column("creado_por", sa.String(length=254), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_releases_pub_fecha", "releases", ["publicado", "fecha"])

    # ------------------------------------------------------------------
    # feature_flags
    # ------------------------------------------------------------------
    op.create_table(
        "feature_flags",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("clave", sa.String(length=80), nullable=False, unique=True),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("descripcion", sa.String(length=300), nullable=False, server_default=""),
        sa.Column("updated_by", sa.String(length=254), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    # ------------------------------------------------------------------
    # crm_clientes (B4)
    # ------------------------------------------------------------------
    op.create_table(
        "crm_clientes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "organizacion_id",
            sa.Integer(),
            sa.ForeignKey("organizaciones.id", ondelete="RESTRICT"),
            nullable=False,
            unique=True,
        ),
        sa.Column("estado", sa.String(length=20), nullable=False, server_default="activo"),
        sa.Column("proximo_contacto", sa.Date(), nullable=True),
        sa.Column("notas", sa.Text(), nullable=False, default=""),
        sa.Column("updated_by", sa.String(length=254), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_crm_clientes_estado", "crm_clientes", ["estado", "proximo_contacto"])

    # ------------------------------------------------------------------
    # vistas_guardadas (A5 completo: filtros persistentes por módulo)
    # ------------------------------------------------------------------
    op.create_table(
        "vistas_guardadas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("modulo", sa.String(length=60), nullable=False),
        sa.Column("filtros", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("columnas", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("creada_por", sa.String(length=254), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_vistas_guardadas_modulo", "vistas_guardadas", ["modulo", "nombre"])

    # ------------------------------------------------------------------
    # api_keys_operador (A6, solo hash de clave)
    # ------------------------------------------------------------------
    op.create_table(
        "api_keys_operador",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("clave_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column("scopes", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("creada_por", sa.String(length=254), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_api_keys_operador_nombre", "api_keys_operador", ["nombre"])

    if not _postgres():
        # SQLite (escritorio y pruebas): sin RLS; la aplicación limita siempre
        # a la sesión de operador (las rutas usan get_operator_db).
        return

    # RLS
    _rl_simple(
        "contenido_web",
        publico_si="publicado IS NOT NULL",
    )
    _rl_simple(
        "avisos_web",
        publico_si="activo IS TRUE",
    )
    _rl_simple(
        "releases",
        publico_si="publicado IS TRUE",
    )
    _rl_simple("vistas_guardadas", publico_si=None)
    _rl_simple("feature_flags", publico_si=None)
    _rl_simple("crm_clientes", publico_si=None)
    _rl_simple("api_keys_operador", publico_si=None)


def downgrade() -> None:
    if _postgres():
        for nombre in (
            "contenido_web", "avisos_web", "releases",
            "vistas_guardadas", "feature_flags", "crm_clientes",
            "api_keys_operador",
        ):
            for prefijo in ("select_publico", "select_operator", "insert_operator", "update_operator"):
                op.execute(
                    f"DROP POLICY IF EXISTS cotizat_{nombre}_{prefijo} "
                    f"ON public.{nombre}"
                )
            op.execute(f"ALTER TABLE public.{nombre} DISABLE ROW LEVEL SECURITY")

    for nombre, indices in (
        ("api_keys_operador", ("ix_api_keys_operador_nombre",)),
        ("crm_clientes", ("ix_crm_clientes_estado",)),
        ("vistas_guardadas", ("ix_vistas_guardadas_modulo",)),
        ("releases", ("ix_releases_pub_fecha",)),
        ("avisos_web", ("ix_avisos_web_activo_fechas",)),
        ("contenido_web", ("ix_contenido_web_clave",)),
    ):
        for indice in indices:
            op.drop_index(indice, table_name=nombre)
        op.drop_table(nombre)
    op.drop_table("feature_flags")
