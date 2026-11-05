"""Audiencia de la capa pública: ``public.visitas_pagina`` (E5-012 ampliada).

Tabla de agregado para el panel de administración: cuántos visitantes recibe
el sitio cada día, qué páginas los traen y de qué origen. Se usa en
``/admin/analitica`` para que el operador mire el embudo completo (visitas ->
registros -> empresas -> presupuestos -> cobros) con un dato propio y sin
cookies de terceros.

Diseño:

- La IP nunca se guarda, solo su hash con sal del despliegue
  (``app.security.hash_ip``), igual que el registro de pruebas gratuitas.
- Es de lectura/escritura global: no hereda ``TenantMixin`` ni queda bajo RLS
  de inquilino; la analítica del operador la lee desde su propia sesión.
- Idempotente por si el código arranca antes que la migración en un despliegue.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "w3m9k2p8v1n4"
down_revision: Union[str, Sequence[str], None] = "v2d7f1a6b9c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "visitas_pagina"


def _existe() -> bool:
    try:
        from sqlalchemy import inspect as _inspect

        return TABLE in _inspect(op.get_bind()).get_table_names()
    except Exception:
        return False


def _postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def _permisos_aplicacion() -> None:
    """Concede al rol de aplicación acceso a la tabla y a su secuencia.

    Sin esto la migración crea la tabla como ``postgres`` y en producción el
    runtime (``cotizat_app``) recibe ``permission denied for table
    visitas_pagina`` en cada lectura del panel: las políticas por omisión de
    PostgreSQL no incluyen a ese rol. Es el mismo bloque que llevan el resto
    de migraciones que crean tablas (``planos_obra``, ``pruebas_concedidas``).
    """
    if not _postgres():
        return
    op.execute(f"REVOKE ALL ON TABLE public.{TABLE} FROM PUBLIC")
    # En Supabase los privilegios por omisión del esquema ``public`` incluyen
    # ``anon`` y ``authenticated`` (los roles de la Data API). Esta tabla
    # guarda hashes de IP y rutas visitadas: no debe ser legible desde la API
    # pública. En un PostgreSQL sin esos roles el bloque no hace nada.
    op.execute(
        f"""
        DO $$
        BEGIN
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
            EXECUTE 'REVOKE ALL ON TABLE public.{TABLE} FROM anon';
          END IF;
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
            EXECUTE 'REVOKE ALL ON TABLE public.{TABLE} FROM authenticated';
          END IF;
        END $$
        """
    )
    op.execute(
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.{TABLE} TO cotizat_app"
    )
    op.execute(
        f"GRANT USAGE, SELECT ON SEQUENCE public.{TABLE}_id_seq TO cotizat_app"
    )

    # Supabase crea un disparador (``ensure_rls``) que activa RLS en toda tabla
    # nueva del esquema ``public``. Con RLS y sin políticas, ``cotizat_app`` no
    # puede escribir ni leer: el middleware cuenta la visita, recibe
    # «new row violates row-level security policy», la descarta en silencio y
    # el panel se queda viendo ceros. Las políticas son deliberadamente
    # abiertas porque la tabla no tiene dueño por inquilino (ver el docstring
    # de la migración): el aislamiento lo dan los GRANT, que dejan fuera a
    # ``anon`` y ``authenticated``.
    for nombre, clausula in (
        ("cotizat_visitas_select", " FOR SELECT TO cotizat_app USING (true)"),
        ("cotizat_visitas_insert", " FOR INSERT TO cotizat_app WITH CHECK (true)"),
        (
            "cotizat_visitas_update",
            " FOR UPDATE TO cotizat_app USING (true) WITH CHECK (true)",
        ),
        ("cotizat_visitas_delete", " FOR DELETE TO cotizat_app USING (true)"),
    ):
        op.execute(f"DROP POLICY IF EXISTS {nombre} ON public.{TABLE}")
        op.execute(f"CREATE POLICY {nombre} ON public.{TABLE}{clausula}")



def upgrade() -> None:
    if _existe():
        _permisos_aplicacion()
        return
    op.create_table(
        TABLE,
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ruta", sa.String(length=300), nullable=False),
        sa.Column("ip_hash", sa.String(length=64), nullable=False),
        sa.Column("usuario_agent", sa.String(length=300), nullable=True),
        sa.Column("referente", sa.String(length=300), nullable=True),
        sa.Column(
            "usuario_id",
            sa.Integer(),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "organizacion_id",
            sa.Integer(),
            sa.ForeignKey("organizaciones.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(f"ix_{TABLE}_ruta", TABLE, ["ruta"])
    op.create_index(f"ix_{TABLE}_ip_hash", TABLE, ["ip_hash"])
    op.create_index(f"ix_{TABLE}_created_at", TABLE, ["created_at"])
    _permisos_aplicacion()


def downgrade() -> None:
    if not _existe():
        return
    op.drop_index(f"ix_{TABLE}_created_at", table_name=TABLE)
    op.drop_index(f"ix_{TABLE}_ip_hash", table_name=TABLE)
    op.drop_index(f"ix_{TABLE}_ruta", table_name=TABLE)
    op.drop_table(TABLE)
