"""public proposal links with token-scoped RLS

Revision ID: c2f6e8a1d934
Revises: b7c4a9e2d31f
Create Date: 2026-08-16 12:45:00

El enlace público no abre el tenant. La sesión sin identidad solo puede leer
una fila de ``enlaces_propuesta`` cuando el SHA-256 guardado coincide con el
claim transaccional ``cotizat.proposal_token_hash`` y el enlace sigue vigente.
La fila contiene exclusivamente el subconjunto de datos autorizado para la
página pública y la referencia al PDF congelado; ninguna política pública se
añade a presupuestos, clientes, versiones ni archivos. La respuesta pública
pasa por una función SECURITY DEFINER limitada a las columnas de decisión,
identidad declarada, comentario y fecha: la sesión pública nunca recibe UPDATE
sobre la tabla.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c2f6e8a1d934"
down_revision: Union[str, Sequence[str], None] = "b7c4a9e2d31f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "enlaces_propuesta"
APP_ROLE = "cotizat_app"
PUBLIC_MATCH = """
  token_hash = NULLIF(
    pg_catalog.current_setting('cotizat.proposal_token_hash', true),
    ''
  )
  AND revoked_at IS NULL
  AND expires_at > pg_catalog.clock_timestamp()
"""
TENANT_READ = "cotizat_security.tenant_access(organizacion_id, FALSE)"
TENANT_WRITE = "cotizat_security.tenant_access(organizacion_id, TRUE)"

RECORD_RESPONSE_SQL = """
CREATE OR REPLACE FUNCTION cotizat_security.record_proposal_response(
  p_decision text,
  p_name text,
  p_email text,
  p_comment text
) RETURNS integer LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
DECLARE
  v_id integer;
  v_budget_id integer;
  v_version_id integer;
  v_organization_id integer;
  v_version_number integer;
  v_state_updated integer := 0;
BEGIN
  IF p_decision NOT IN ('aceptada', 'rechazada')
     OR char_length(btrim(COALESCE(p_name, ''))) NOT BETWEEN 2 AND 200
     OR char_length(COALESCE(p_email, '')) > 254
     OR lower(COALESCE(p_email, '')) !~
        '^[^@[:space:]]+@[^@[:space:]]+[.][^@[:space:]]+$'
     OR char_length(COALESCE(p_comment, '')) > 2000 THEN
    RETURN NULL;
  END IF;

  UPDATE public.enlaces_propuesta
  SET respuesta = p_decision,
      respondido_por_nombre = btrim(p_name),
      respondido_por_email = lower(btrim(p_email)),
      respuesta_comentario = btrim(COALESCE(p_comment, '')),
      responded_at = pg_catalog.clock_timestamp()
  WHERE token_hash = NULLIF(
          pg_catalog.current_setting('cotizat.proposal_token_hash', true), ''
        )
    AND respuesta = 'pendiente'
    AND revoked_at IS NULL
    AND expires_at > pg_catalog.clock_timestamp()
  RETURNING id, presupuesto_id, presupuesto_version_id, organizacion_id
  INTO v_id, v_budget_id, v_version_id, v_organization_id;

  IF v_id IS NULL THEN
    RETURN NULL;
  END IF;

  SELECT numero_version INTO v_version_number
  FROM public.presupuesto_versiones
  WHERE id = v_version_id;

  UPDATE public.presupuestos
  SET estado = CASE p_decision
                 WHEN 'aceptada' THEN 'aprobado'
                 ELSE 'rechazado'
               END,
      updated_at = pg_catalog.clock_timestamp()
  WHERE id = v_budget_id
    AND estado IN ('enviado', 'reenviado')
    AND v_version_id = (
      SELECT pv.id
      FROM public.presupuesto_versiones AS pv
      WHERE pv.presupuesto_id = v_budget_id
      ORDER BY pv.numero_version DESC
      LIMIT 1
    );
  GET DIAGNOSTICS v_state_updated = ROW_COUNT;

  UPDATE public.enlaces_propuesta
  SET estado_presupuesto_actualizado = (v_state_updated = 1)
  WHERE id = v_id;

  INSERT INTO public.notas_seguimiento (
    presupuesto_id, texto, created_at, organizacion_id
  ) VALUES (
    v_budget_id,
    'Propuesta V' || COALESCE(v_version_number::text, '?') || ' ' ||
      p_decision || ' por ' || btrim(p_name) || ' (' || lower(btrim(p_email)) || ').',
    pg_catalog.clock_timestamp(),
    v_organization_id
  );

  RETURN v_id;
END
$$
"""

NOTIFICATION_RECIPIENTS_SQL = """
CREATE OR REPLACE FUNCTION cotizat_security.proposal_notification_recipients(
  p_link_id integer
) RETURNS TABLE(email varchar) LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
  SELECT DISTINCT u.email
  FROM public.enlaces_propuesta AS l
  JOIN public.membresias AS m ON m.organizacion_id = l.organizacion_id
  JOIN public.usuarios AS u ON u.id = m.usuario_id
  WHERE l.id = p_link_id
    AND l.token_hash = NULLIF(
      pg_catalog.current_setting('cotizat.proposal_token_hash', true), ''
    )
    AND l.respuesta IN ('aceptada', 'rechazada')
    AND m.activa IS TRUE
    AND m.rol IN ('propietario', 'administrador')
    AND u.activo IS TRUE
$$
"""

MARK_NOTIFICATION_SQL = """
CREATE OR REPLACE FUNCTION cotizat_security.mark_proposal_notification(
  p_link_id integer,
  p_recipients text,
  p_error text
) RETURNS integer LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
DECLARE
  v_id integer;
BEGIN
  UPDATE public.enlaces_propuesta
  SET notificacion_destinatarios = left(COALESCE(p_recipients, ''), 2000),
      notificacion_error = left(COALESCE(p_error, ''), 1000),
      notificacion_enviada_at = CASE
        WHEN COALESCE(p_recipients, '') <> '' AND COALESCE(p_error, '') = ''
        THEN pg_catalog.clock_timestamp()
        ELSE NULL
      END
  WHERE id = p_link_id
    AND token_hash = NULLIF(
      pg_catalog.current_setting('cotizat.proposal_token_hash', true), ''
    )
    AND respuesta IN ('aceptada', 'rechazada')
  RETURNING id INTO v_id;
  RETURN v_id;
END
$$
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
        ),
        sa.Column(
            "presupuesto_id",
            sa.Integer(),
            sa.ForeignKey("presupuestos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "presupuesto_version_id",
            sa.Integer(),
            sa.ForeignKey("presupuesto_versiones.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("presupuesto_version_numero", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("token_prefix", sa.String(length=12), nullable=False, server_default=""),
        sa.Column("pdf_snapshot", sa.String(length=900), nullable=False),
        sa.Column("empresa_nombre", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("cliente_nombre", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("presupuesto_numero", sa.String(length=20), nullable=False, server_default=""),
        sa.Column("presupuesto_titulo", sa.String(length=250), nullable=False, server_default=""),
        sa.Column("total", sa.Float(), nullable=False, server_default="0"),
        sa.Column("moneda", sa.String(length=10), nullable=False, server_default="USD"),
        sa.Column("fecha_presupuesto", sa.Date(), nullable=False),
        sa.Column("valido_hasta", sa.Date(), nullable=False),
        sa.Column(
            "creado_por_usuario_id",
            sa.Integer(),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("respuesta", sa.String(length=20), nullable=False, server_default="pendiente"),
        sa.Column("respondido_por_nombre", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("respondido_por_email", sa.String(length=254), nullable=False, server_default=""),
        sa.Column("respuesta_comentario", sa.Text(), nullable=False, server_default=""),
        sa.Column("responded_at", sa.DateTime(), nullable=True),
        sa.Column("estado_presupuesto_actualizado", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("notificacion_enviada_at", sa.DateTime(), nullable=True),
        sa.Column("notificacion_destinatarios", sa.Text(), nullable=False, server_default=""),
        sa.Column("notificacion_error", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "length(token_hash) = 64",
            name="ck_enlace_propuesta_token_hash_sha256",
        ),
        sa.CheckConstraint(
            "respuesta IN ('pendiente', 'aceptada', 'rechazada')",
            name="ck_enlace_propuesta_respuesta_valida",
        ),
        sa.UniqueConstraint("token_hash", name="uq_enlace_propuesta_token_hash"),
    )
    op.create_index(
        "ix_enlaces_propuesta_organizacion_id",
        TABLE,
        ["organizacion_id"],
        unique=False,
    )
    op.create_index(
        "ix_enlaces_propuesta_presupuesto_creado",
        TABLE,
        ["presupuesto_id", "created_at"],
        unique=False,
    )

    if not _postgres():
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

    policies = {
        "cotizat_proposal_select_tenant": (
            "SELECT", f"USING ({TENANT_READ})"
        ),
        "cotizat_proposal_select_public": (
            "SELECT", f"USING ({PUBLIC_MATCH})"
        ),
        "cotizat_proposal_insert_tenant": (
            "INSERT", f"WITH CHECK ({TENANT_WRITE})"
        ),
        "cotizat_proposal_update_tenant": (
            "UPDATE", f"USING ({TENANT_WRITE}) WITH CHECK ({TENANT_WRITE})"
        ),
    }
    for name, (action, clause) in policies.items():
        op.execute(f"DROP POLICY IF EXISTS {name} ON public.{TABLE}")
        op.execute(f"""
            CREATE POLICY {name} ON public.{TABLE}
            FOR {action} TO {APP_ROLE}
            {clause}
        """)

    op.execute(RECORD_RESPONSE_SQL)
    op.execute(NOTIFICATION_RECIPIENTS_SQL)
    op.execute(MARK_NOTIFICATION_SQL)
    for signature in (
        "record_proposal_response(text, text, text, text)",
        "proposal_notification_recipients(integer)",
        "mark_proposal_notification(integer, text, text)",
    ):
        op.execute(
            f"ALTER FUNCTION cotizat_security.{signature} OWNER TO CURRENT_USER"
        )
        op.execute(
            f"REVOKE ALL ON FUNCTION cotizat_security.{signature} FROM PUBLIC"
        )
        op.execute(
            f"GRANT EXECUTE ON FUNCTION cotizat_security.{signature} TO cotizat_app"
        )


def downgrade() -> None:
    if _postgres():
        for signature in (
            "record_proposal_response(text, text, text, text)",
            "proposal_notification_recipients(integer)",
            "mark_proposal_notification(integer, text, text)",
        ):
            op.execute(
                f"DROP FUNCTION IF EXISTS cotizat_security.{signature}"
            )
        for name in (
            "cotizat_proposal_select_tenant",
            "cotizat_proposal_select_public",
            "cotizat_proposal_insert_tenant",
            "cotizat_proposal_update_tenant",
        ):
            op.execute(f"DROP POLICY IF EXISTS {name} ON public.{TABLE}")
    op.drop_index(
        "ix_enlaces_propuesta_presupuesto_creado", table_name=TABLE
    )
    op.drop_index("ix_enlaces_propuesta_organizacion_id", table_name=TABLE)
    op.drop_table(TABLE)
