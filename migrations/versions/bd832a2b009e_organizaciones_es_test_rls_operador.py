"""El operador también puede marcar organizaciones como TEST.

La columna ``organizaciones.es_test`` la crea a8f1c3d9e7b2, pero la política
``cotizat_org_update`` solo permitía actualizar a quien puede gestionar el
equipo (``can_manage_team``). El panel admin corre como operador
(``cotizat.es_operador = on``) sin membresía en cada organización cliente,
así que el toggle ``POST /admin/clientes/{id}/alternar-test`` fallaba con
``No se pudo actualizar la marca de prueba`` (0 filas actualizadas por RLS).

Se añade una política permisiva que permite al operador actualizar
organizaciones. Es OR con la existente: un cliente que gestiona su equipo
sigue pudiendo, y el operador también.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "bd832a2b009e"
down_revision: Union[str, Sequence[str], None] = "a8f1c3d9e7b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _is_postgres() -> bool:
    return op.get_context().dialect.name == "postgresql"


def upgrade() -> None:
    if not _is_postgres():
        return
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'cotizat_org_update' AND tablename = 'organizaciones') THEN
            DROP POLICY IF EXISTS cotizat_org_update_operador ON public.organizaciones;
            CREATE POLICY cotizat_org_update_operador ON public.organizaciones
              FOR UPDATE TO cotizat_app
              USING (COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', false))
              WITH CHECK (COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', false));
          END IF;
        END $$;
        """
    )


def downgrade() -> None:
    if not _is_postgres():
        return
    op.execute("DROP POLICY IF EXISTS cotizat_org_update_operador ON public.organizaciones")
