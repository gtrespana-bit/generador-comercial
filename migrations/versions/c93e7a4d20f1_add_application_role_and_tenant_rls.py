"""add application role and tenant RLS policies

Revision ID: c93e7a4d20f1
Revises: a84d2f6b91e0
Create Date: 2026-08-13 23:59:30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c93e7a4d20f1"
down_revision: Union[str, Sequence[str], None] = "a84d2f6b91e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

APP_ROLE = "cotizat_app"
TENANT_TABLES = (
    "archivos_almacenados",
    "borradores_presupuesto",
    "cambio_alcance_items",
    "cambios_alcance",
    "capitulos",
    "categorias_partidas",
    "clientes",
    "configuracion",
    "descomposicion_filas",
    "descomposiciones_partida",
    "factura_capitulos",
    "factura_items",
    "facturas",
    "mediciones",
    "notas_seguimiento",
    "pagos",
    "partidas",
    "plantillas",
    "presupuesto_anexos",
    "presupuesto_item_productos",
    "presupuesto_items",
    "presupuesto_versiones",
    "presupuestos",
    "productos",
    "proyectos",
    "recetas_estancia",
    "recursos",
)
IDENTITY_TABLES = ("organizaciones", "usuarios", "membresias")
INVITATION_TABLE = "invitaciones_organizacion"
ALL_APP_TABLES = IDENTITY_TABLES + TENANT_TABLES + (INVITATION_TABLE,)


def _function_statements() -> list[str]:
    return [
        """
        CREATE OR REPLACE FUNCTION cotizat_security.context_auth_user_id()
        RETURNS text LANGUAGE sql STABLE
        SET search_path = pg_catalog, public
        AS $$
          SELECT NULLIF(pg_catalog.current_setting('cotizat.auth_user_id', true), '')
        $$
        """,
        """
        CREATE OR REPLACE FUNCTION cotizat_security.context_email()
        RETURNS text LANGUAGE sql STABLE
        SET search_path = pg_catalog, public
        AS $$
          SELECT LOWER(NULLIF(pg_catalog.current_setting('cotizat.auth_email', true), ''))
        $$
        """,
        """
        CREATE OR REPLACE FUNCTION cotizat_security.context_organization_id()
        RETURNS integer LANGUAGE sql STABLE
        SET search_path = pg_catalog, public
        AS $$
          SELECT CASE WHEN value ~ '^[1-9][0-9]*$' THEN value::integer END
          FROM (SELECT pg_catalog.current_setting(
            'cotizat.organization_id', true
          ) AS value) AS configured
        $$
        """,
        """
        CREATE OR REPLACE FUNCTION cotizat_security.current_user_id()
        RETURNS integer LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
          SELECT u.id
          FROM public.usuarios AS u
          WHERE u.auth_user_id = NULLIF(
            pg_catalog.current_setting('cotizat.auth_user_id', true), ''
          )
          LIMIT 1
        $$
        """,
        """
        CREATE OR REPLACE FUNCTION cotizat_security.current_user_email()
        RETURNS text LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
          SELECT LOWER(u.email)
          FROM public.usuarios AS u
          WHERE u.id = cotizat_security.current_user_id()
          LIMIT 1
        $$
        """,
        """
        CREATE OR REPLACE FUNCTION cotizat_security.current_user_is_verified()
        RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
          SELECT COALESCE(u.email_verificado_at IS NOT NULL, FALSE)
          FROM public.usuarios AS u
          WHERE u.id = cotizat_security.current_user_id()
          LIMIT 1
        $$
        """,
        """
        CREATE OR REPLACE FUNCTION cotizat_security.membership_role(p_organization_id integer)
        RETURNS text LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
          SELECT m.rol
          FROM public.membresias AS m
          JOIN public.organizaciones AS o ON o.id = m.organizacion_id
          WHERE m.usuario_id = cotizat_security.current_user_id()
            AND m.organizacion_id = p_organization_id
            AND m.activa IS TRUE
            AND o.activa IS TRUE
          LIMIT 1
        $$
        """,
        """
        CREATE OR REPLACE FUNCTION cotizat_security.tenant_access(
          p_organization_id integer, p_write boolean
        ) RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
          SELECT COALESCE(
            p_organization_id = cotizat_security.context_organization_id()
            AND cotizat_security.membership_role(p_organization_id) IS NOT NULL
            AND (
              NOT p_write
              OR cotizat_security.membership_role(p_organization_id) <> 'lectura'
            ),
            FALSE
          )
        $$
        """,
        """
        CREATE OR REPLACE FUNCTION cotizat_security.can_manage_team(
          p_organization_id integer
        ) RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
          SELECT COALESCE(
            p_organization_id = cotizat_security.context_organization_id()
            AND cotizat_security.membership_role(p_organization_id)
                IN ('propietario', 'administrador'),
            FALSE
          )
        $$
        """,
        """
        CREATE OR REPLACE FUNCTION cotizat_security.can_assign_role(
          p_organization_id integer, p_role text
        ) RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
          SELECT COALESCE(
            CASE cotizat_security.membership_role(p_organization_id)
              WHEN 'propietario' THEN p_role IN ('administrador', 'miembro', 'lectura')
              WHEN 'administrador' THEN p_role IN ('miembro', 'lectura')
              ELSE FALSE
            END,
            FALSE
          )
        $$
        """,
        """
        CREATE OR REPLACE FUNCTION cotizat_security.can_view_user(p_user_id integer)
        RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
          SELECT COALESCE(
            p_user_id = cotizat_security.current_user_id()
            OR (
              cotizat_security.can_manage_team(
                cotizat_security.context_organization_id()
              )
              AND EXISTS (
                SELECT 1 FROM public.membresias AS m
                WHERE m.usuario_id = p_user_id
                  AND m.organizacion_id =
                      cotizat_security.context_organization_id()
              )
            ),
            FALSE
          )
        $$
        """,
        """
        CREATE OR REPLACE FUNCTION cotizat_security.can_create_owner_membership(
          p_organization_id integer, p_user_id integer, p_role text
        ) RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
          SELECT COALESCE(
            p_user_id = cotizat_security.current_user_id()
            AND p_role = 'propietario'
            AND EXISTS (
              SELECT 1 FROM public.organizaciones AS owned
              WHERE owned.id = p_organization_id
                AND owned.creada_por_usuario_id =
                    cotizat_security.current_user_id()
            )
            AND NOT EXISTS (
              SELECT 1 FROM public.membresias AS existing
              WHERE existing.organizacion_id = p_organization_id
            ),
            FALSE
          )
        $$
        """,
        """
        CREATE OR REPLACE FUNCTION cotizat_security.has_pending_invitation(
          p_organization_id integer, p_user_id integer, p_role text
        ) RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
          SELECT COALESCE(
            p_user_id = cotizat_security.current_user_id()
            AND EXISTS (
              SELECT 1
              FROM public.invitaciones_organizacion AS invitation
              JOIN public.usuarios AS invited_user
                ON invited_user.id = p_user_id
              WHERE invitation.organizacion_id = p_organization_id
                AND invitation.email = LOWER(invited_user.email)
                AND invited_user.email_verificado_at IS NOT NULL
                AND (p_role IS NULL OR invitation.rol = p_role)
                AND invitation.accepted_at IS NULL
                AND invitation.revoked_at IS NULL
                AND invitation.expires_at > pg_catalog.clock_timestamp()
            ),
            FALSE
          )
        $$
        """,
        """
        CREATE OR REPLACE FUNCTION cotizat_security.can_manage_membership(
          p_organization_id integer, p_target_user_id integer, p_target_role text
        ) RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
          SELECT COALESCE(
            CASE cotizat_security.membership_role(p_organization_id)
              WHEN 'propietario' THEN p_target_role <> 'propietario'
              WHEN 'administrador' THEN
                p_target_user_id <> cotizat_security.current_user_id()
                AND p_target_role IN ('miembro', 'lectura')
              ELSE FALSE
            END,
            FALSE
          )
        $$
        """,
    ]


def _drop_policy(table: str, name: str) -> str:
    return f"DROP POLICY IF EXISTS {name} ON public.{table}"


def upgrade() -> None:
    with op.batch_alter_table("organizaciones") as batch_op:
        batch_op.add_column(
            sa.Column("creada_por_usuario_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_organizaciones_creada_por_usuario",
            "usuarios",
            ["creada_por_usuario_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index(
            "ix_organizaciones_creada_por_usuario_id",
            ["creada_por_usuario_id"],
            unique=False,
        )

    if op.get_bind().dialect.name != "postgresql":
        return

    op.execute("""
        DO $role$
        BEGIN
          IF NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'cotizat_app') THEN
            CREATE ROLE cotizat_app NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE
              NOINHERIT NOREPLICATION NOBYPASSRLS;
          END IF;
        END
        $role$
    """)
    op.execute("""
        ALTER ROLE cotizat_app NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE
          NOINHERIT NOREPLICATION NOBYPASSRLS
    """)
    op.execute("CREATE SCHEMA IF NOT EXISTS cotizat_security")
    op.execute("ALTER SCHEMA cotizat_security OWNER TO CURRENT_USER")
    op.execute("REVOKE CREATE ON SCHEMA public FROM PUBLIC")
    op.execute("REVOKE ALL ON SCHEMA cotizat_security FROM PUBLIC")
    op.execute("GRANT USAGE ON SCHEMA public, cotizat_security TO cotizat_app")

    for statement in _function_statements():
        op.execute(statement)

    function_signatures = (
        "context_auth_user_id()",
        "context_email()",
        "context_organization_id()",
        "current_user_id()",
        "current_user_email()",
        "current_user_is_verified()",
        "membership_role(integer)",
        "tenant_access(integer, boolean)",
        "can_manage_team(integer)",
        "can_assign_role(integer, text)",
        "can_view_user(integer)",
        "can_create_owner_membership(integer, integer, text)",
        "has_pending_invitation(integer, integer, text)",
        "can_manage_membership(integer, integer, text)",
    )
    for signature in function_signatures:
        op.execute(
            f"ALTER FUNCTION cotizat_security.{signature} OWNER TO CURRENT_USER"
        )
        op.execute(
            f"REVOKE ALL ON FUNCTION cotizat_security.{signature} FROM PUBLIC"
        )
        op.execute(
            f"GRANT EXECUTE ON FUNCTION cotizat_security.{signature} TO cotizat_app"
        )

    for table in ALL_APP_TABLES:
        op.execute(f"REVOKE ALL ON TABLE public.{table} FROM PUBLIC")
        op.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE public.{table} FORCE ROW LEVEL SECURITY")
    for table in TENANT_TABLES:
        op.execute(
            f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.{table} TO cotizat_app"
        )
    op.execute(
        "GRANT SELECT, INSERT, UPDATE ON TABLE public.organizaciones, "
        "public.usuarios, public.membresias TO cotizat_app"
    )
    op.execute("GRANT SELECT ON TABLE public.alembic_version TO cotizat_app")
    op.execute(
        "GRANT SELECT, INSERT ON TABLE public.invitaciones_organizacion TO cotizat_app"
    )
    op.execute(
        "GRANT UPDATE (accepted_at, aceptada_por_usuario_id, revoked_at) "
        "ON TABLE public.invitaciones_organizacion TO cotizat_app"
    )
    for table in ALL_APP_TABLES:
        op.execute(
            f"GRANT USAGE, SELECT ON SEQUENCE public.{table}_id_seq TO cotizat_app"
        )

    for table in TENANT_TABLES:
        for name in (
            "cotizat_tenant_select", "cotizat_tenant_insert",
            "cotizat_tenant_update", "cotizat_tenant_delete",
        ):
            op.execute(_drop_policy(table, name))
        op.execute(f"""
            CREATE POLICY cotizat_tenant_select ON public.{table}
            FOR SELECT TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, FALSE))
        """)
        op.execute(f"""
            CREATE POLICY cotizat_tenant_insert ON public.{table}
            FOR INSERT TO cotizat_app
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE))
        """)
        op.execute(f"""
            CREATE POLICY cotizat_tenant_update ON public.{table}
            FOR UPDATE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE))
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE))
        """)
        op.execute(f"""
            CREATE POLICY cotizat_tenant_delete ON public.{table}
            FOR DELETE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE))
        """)

    for table, policies in {
        "usuarios": ("cotizat_user_select", "cotizat_user_insert", "cotizat_user_update"),
        "organizaciones": (
            "cotizat_org_select", "cotizat_org_insert", "cotizat_org_update",
        ),
        "membresias": (
            "cotizat_membership_select", "cotizat_membership_insert",
            "cotizat_membership_update",
        ),
        INVITATION_TABLE: (
            "cotizat_invitation_select_manager", "cotizat_invitation_select_recipient",
            "cotizat_invitation_insert", "cotizat_invitation_update_manager",
            "cotizat_invitation_update_recipient",
        ),
    }.items():
        for policy in policies:
            op.execute(_drop_policy(table, policy))

    own_user = """
      auth_user_id = cotizat_security.context_auth_user_id()
      OR (
        auth_user_id IS NULL
        AND LOWER(email) = cotizat_security.context_email()
      )
    """
    op.execute(f"""
        CREATE POLICY cotizat_user_select ON public.usuarios
        FOR SELECT TO cotizat_app
        USING (({own_user}) OR cotizat_security.can_view_user(id))
    """)
    op.execute("""
        CREATE POLICY cotizat_user_insert ON public.usuarios
        FOR INSERT TO cotizat_app
        WITH CHECK (
          auth_user_id = cotizat_security.context_auth_user_id()
          AND LOWER(email) = cotizat_security.context_email()
        )
    """)
    op.execute(f"""
        CREATE POLICY cotizat_user_update ON public.usuarios
        FOR UPDATE TO cotizat_app
        USING ({own_user})
        WITH CHECK (
          auth_user_id = cotizat_security.context_auth_user_id()
          AND LOWER(email) = cotizat_security.context_email()
        )
    """)

    op.execute("""
        CREATE POLICY cotizat_org_select ON public.organizaciones
        FOR SELECT TO cotizat_app
        USING (cotizat_security.membership_role(id) IS NOT NULL)
    """)
    op.execute("""
        CREATE POLICY cotizat_org_insert ON public.organizaciones
        FOR INSERT TO cotizat_app
        WITH CHECK (
          cotizat_security.context_auth_user_id() IS NOT NULL
          AND creada_por_usuario_id = cotizat_security.current_user_id()
        )
    """)
    op.execute("""
        CREATE POLICY cotizat_org_update ON public.organizaciones
        FOR UPDATE TO cotizat_app
        USING (cotizat_security.can_manage_team(id))
        WITH CHECK (cotizat_security.can_manage_team(id))
    """)

    op.execute("""
        CREATE POLICY cotizat_membership_select ON public.membresias
        FOR SELECT TO cotizat_app
        USING (
          usuario_id = cotizat_security.current_user_id()
          OR cotizat_security.can_manage_team(organizacion_id)
        )
    """)
    op.execute("""
        CREATE POLICY cotizat_membership_insert ON public.membresias
        FOR INSERT TO cotizat_app
        WITH CHECK (
          cotizat_security.can_create_owner_membership(
            organizacion_id, usuario_id, rol
          )
          OR cotizat_security.has_pending_invitation(
            organizacion_id, usuario_id, rol
          )
        )
    """)
    op.execute("""
        CREATE POLICY cotizat_membership_update ON public.membresias
        FOR UPDATE TO cotizat_app
        USING (
          cotizat_security.can_manage_membership(
            organizacion_id, usuario_id, rol
          )
          OR cotizat_security.has_pending_invitation(
            organizacion_id, usuario_id, NULL
          )
        )
        WITH CHECK (
          (
            cotizat_security.can_manage_membership(
              organizacion_id, usuario_id, rol
            )
            AND cotizat_security.can_assign_role(organizacion_id, rol)
          )
          OR (
            activa IS TRUE
            AND cotizat_security.has_pending_invitation(
              organizacion_id, usuario_id, rol
            )
          )
        )
    """)

    invitation_valid = """
      email = cotizat_security.current_user_email()
      AND cotizat_security.current_user_is_verified()
      AND accepted_at IS NULL
      AND revoked_at IS NULL
      AND expires_at > pg_catalog.clock_timestamp()
    """
    op.execute("""
        CREATE POLICY cotizat_invitation_select_manager
        ON public.invitaciones_organizacion
        FOR SELECT TO cotizat_app
        USING (cotizat_security.can_manage_team(organizacion_id))
    """)
    op.execute(f"""
        CREATE POLICY cotizat_invitation_select_recipient
        ON public.invitaciones_organizacion
        FOR SELECT TO cotizat_app USING ({invitation_valid})
    """)
    op.execute("""
        CREATE POLICY cotizat_invitation_insert
        ON public.invitaciones_organizacion
        FOR INSERT TO cotizat_app
        WITH CHECK (
          cotizat_security.can_manage_team(organizacion_id)
          AND cotizat_security.can_assign_role(organizacion_id, rol)
        )
    """)
    op.execute("""
        CREATE POLICY cotizat_invitation_update_manager
        ON public.invitaciones_organizacion
        FOR UPDATE TO cotizat_app
        USING (cotizat_security.can_manage_team(organizacion_id))
        WITH CHECK (
          cotizat_security.can_manage_team(organizacion_id)
          AND cotizat_security.can_assign_role(organizacion_id, rol)
        )
    """)
    op.execute(f"""
        CREATE POLICY cotizat_invitation_update_recipient
        ON public.invitaciones_organizacion
        FOR UPDATE TO cotizat_app
        USING ({invitation_valid})
        WITH CHECK (
          email = cotizat_security.current_user_email()
          AND accepted_at IS NOT NULL
          AND aceptada_por_usuario_id = cotizat_security.current_user_id()
          AND revoked_at IS NULL
          AND expires_at > pg_catalog.clock_timestamp()
        )
    """)


def _drop_organization_creator() -> None:
    with op.batch_alter_table("organizaciones") as batch_op:
        batch_op.drop_index("ix_organizaciones_creada_por_usuario_id")
        batch_op.drop_constraint(
            "fk_organizaciones_creada_por_usuario", type_="foreignkey"
        )
        batch_op.drop_column("creada_por_usuario_id")


def downgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        _drop_organization_creator()
        return

    policy_names = {
        "usuarios": ("cotizat_user_select", "cotizat_user_insert", "cotizat_user_update"),
        "organizaciones": (
            "cotizat_org_select", "cotizat_org_insert", "cotizat_org_update",
        ),
        "membresias": (
            "cotizat_membership_select", "cotizat_membership_insert",
            "cotizat_membership_update",
        ),
        INVITATION_TABLE: (
            "cotizat_invitation_select_manager", "cotizat_invitation_select_recipient",
            "cotizat_invitation_insert", "cotizat_invitation_update_manager",
            "cotizat_invitation_update_recipient",
        ),
    }
    for table in TENANT_TABLES:
        policy_names[table] = (
            "cotizat_tenant_select", "cotizat_tenant_insert",
            "cotizat_tenant_update", "cotizat_tenant_delete",
        )
    for table, policies in policy_names.items():
        for policy in policies:
            op.execute(_drop_policy(table, policy))

    for table in ALL_APP_TABLES:
        op.execute(f"REVOKE ALL ON TABLE public.{table} FROM cotizat_app")
        op.execute(f"REVOKE ALL ON SEQUENCE public.{table}_id_seq FROM cotizat_app")
        op.execute(f"ALTER TABLE public.{table} NO FORCE ROW LEVEL SECURITY")
        if table not in {"archivos_almacenados", INVITATION_TABLE}:
            op.execute(f"ALTER TABLE public.{table} DISABLE ROW LEVEL SECURITY")

    op.execute("REVOKE SELECT ON TABLE public.alembic_version FROM cotizat_app")
    op.execute("REVOKE USAGE ON SCHEMA public, cotizat_security FROM cotizat_app")
    op.execute("DROP SCHEMA IF EXISTS cotizat_security CASCADE")
    # El rol de clúster se conserva deliberadamente: un downgrade no debe
    # eliminar identidades ni membresías operativas creadas por infraestructura.
    _drop_organization_creator()
