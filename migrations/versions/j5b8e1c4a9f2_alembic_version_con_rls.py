"""RLS activo en ``public.alembic_version`` con lectura para el rol de la aplicación

Revision ID: j5b8e1c4a9f2
Revises: i4d7c1b8e2f5
Create Date: 2026-10-15 00:00:00

Contexto (cierre de un aviso crítico del asesor de Supabase):

``e1a4b7c9d2f0`` desactivó RLS en ``public.alembic_version`` para que el login
limitado ``cotizat_runtime`` pudiera leer el head en ``/readyz`` si el proyecto
tenía RLS activo en esa tabla. El efecto colateral es el contrario: con RLS
desactivado, el asesor marca la tabla como *RLS Disabled in Public* (crítico),
porque ``public`` está expuesto a PostgREST.

Lo correcto es lo que hacen el resto de las tablas: **RLS activo + una política
que autorice únicamente lo necesario**. Aquí lo necesario es ``SELECT`` para
``cotizat_app`` (el rol del que ``cotizat_runtime`` es miembro), la misma
capacidad que ya concedía el ``GRANT``. No hay política para ``anon`` ni para
``authenticated``: la tabla solo contiene la revisión de Alembic, y ningún rol
público tiene por qué enumerar el esquema. Los permisos de esas dos roles se
revocan además de forma explícita, porque PostgREST las usaría para intentar el
acceso antes de que RLS filtre las filas.

Los ``UPDATE`` best-effort de arranque (``app/database.py``) siguen sin poder
avanzar la marca: el rol runtime nunca tuvo ``UPDATE`` aquí, y esta revisión no
le da más de lo que tenía. Para eso está el script del SQL Editor
(``docs/staging_upgrade_j5b8e1c4a9f2.sql``).
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "j5b8e1c4a9f2"
down_revision: Union[str, Sequence[str], None] = "i4d7c1b8e2f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

VERSION_TABLE = "public.alembic_version"
APP_ROLE = "cotizat_app"
POLICY = "cotizat_alembic_version_lectura"

#: Roles que PostgREST podría intentar usar. En un PostgreSQL sin Supabase no
#: existen: el bloque comprueba cada uno antes de revocar.
REVOCAR_ROLES_EXPUESTOS = f"""
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
    EXECUTE 'REVOKE ALL ON TABLE {VERSION_TABLE} FROM anon';
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
    EXECUTE 'REVOKE ALL ON TABLE {VERSION_TABLE} FROM authenticated';
  END IF;
END
$$;
"""


def _postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    """Activa RLS y autoriza al rol de la aplicación a leer la revisión."""
    if not _postgres():
        return

    # Es una operación del propietario de la tabla (URL administrativa).
    op.execute(f"ALTER TABLE {VERSION_TABLE} ENABLE ROW LEVEL SECURITY")
    op.execute(f"DROP POLICY IF EXISTS {POLICY} ON {VERSION_TABLE}")
    op.execute(
        f"CREATE POLICY {POLICY} ON {VERSION_TABLE} "
        f"FOR SELECT TO {APP_ROLE} USING (true)"
    )
    op.execute(f"GRANT SELECT ON TABLE {VERSION_TABLE} TO {APP_ROLE}")
    op.execute(REVOCAR_ROLES_EXPUESTOS)


def downgrade() -> None:
    """Restaura el estado de ``e1a4b7c9d2f0`` (RLS desactivado y SELECT)."""
    if not _postgres():
        return

    op.execute(f"DROP POLICY IF EXISTS {POLICY} ON {VERSION_TABLE}")
    op.execute(f"ALTER TABLE {VERSION_TABLE} DISABLE ROW LEVEL SECURITY")
    op.execute(f"GRANT SELECT ON TABLE {VERSION_TABLE} TO {APP_ROLE}")
