"""hacer visible alembic_version al rol runtime

Revision ID: f9f24d062470
Revises: d7f2a9c41e63
Create Date: 2026-08-15

Por qué: /readyz dejó de pasar con «alembic: inesperado:sin-version» en
staging. El administrador ve la fila (SELECT version_num FROM alembic_version
devuelve d7f2a9c41e63), pero el rol limitado cotizat_runtime (miembro de
cotizat_app) obtiene cero filas sin error. La única causa posible en ese
estado es RLS activo sobre public.alembic_version sin política que autorice a
cotizat_app: no es un fallo de GRANT, porque un SELECT sin privilegio habría
terminado en error y /readyz reportaría «error», no «sin-version».

alembic_version es metadatos de migración, no datos de tenant: RLS no le
aporta nada y solo consigue ocultar la fila al rol de aplicación. Esta
migración la deja sin RLS, elimina cualquier política residual que haya podido
quedar de un bundle manual (docs/staging_migration.sql) y garantiza el GRANT
SELECT que ya hacía c93e7a4d20f1.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f9f24d062470"
down_revision: Union[str, Sequence[str], None] = "d7f2a9c41e63"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

APP_ROLE = "cotizat_app"
TABLA = "public.alembic_version"


def upgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return
    # Metadatos de migración: RLS no filtra nada útil y oculta la fila al rol
    # runtime. Idempotente: en bases sanas estos ALTER son no-op.
    op.execute(f"ALTER TABLE {TABLA} DISABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {TABLA} NO FORCE ROW LEVEL SECURITY")
    # Si una base de staging se montó con un bundle manual que dejó políticas
    # sobre la tabla, se eliminan: con RLS apagado son basura inerte y con RLS
    # encendido serían la causa del «sin-version».
    op.execute("""
        DO $policy$
        DECLARE pol record;
        BEGIN
          FOR pol IN
            SELECT policyname FROM pg_catalog.pg_policies
            WHERE schemaname = 'public' AND tablename = 'alembic_version'
          LOOP
            EXECUTE format(
              'DROP POLICY IF EXISTS %I ON public.alembic_version',
              pol.policyname
            );
          END LOOP;
        END
        $policy$
    """)
    op.execute(f"GRANT SELECT ON TABLE {TABLA} TO {APP_ROLE}")


def downgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return
    # Revertir devuelve deliberadamente al estado con el bug: RLS activo y sin
    # SELECT para el rol de aplicación (así el downgrade es simétrico y la
    # regresión queda visible si alguien lo ejecuta en un entorno real).
    op.execute(f"REVOKE SELECT ON TABLE {TABLA} FROM {APP_ROLE}")
    op.execute(f"ALTER TABLE {TABLA} ENABLE ROW LEVEL SECURITY")
