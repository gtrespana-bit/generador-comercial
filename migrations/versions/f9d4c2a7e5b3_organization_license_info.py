"""Información de licencia visible para el propio cliente (f9d4c2a7e5b3).

La sesión de un cliente no puede leer ``licencias`` (RLS de operador), pero
la aplicación necesita mostrarle si su organización tiene un plan activo, la
fecha de caducidad y los días restantes (p. ej. en Configuración y en el menú
lateral).

Esta revisión crea ``cotizat_security.organization_license_info``, una función
SECURITY DEFINER que solo devuelve la fila de la organización del propio claim
de sesión (``context_organization_id``). Un cliente que intente consultar otra
organización no obtiene filas; el operador no la necesita (lee la tabla
directamente en el panel).
"""
from typing import Sequence, Union

from alembic import op


revision: str = "f9d4c2a7e5b3"
down_revision: Union[str, Sequence[str], None] = "e5f2a8d31b6c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

FUNCION = "organization_license_info"


def _postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    if not _postgres():
        return
    op.execute(
        f"""
        CREATE OR REPLACE FUNCTION cotizat_security.{FUNCION}(
          p_organization_id integer
        ) RETURNS TABLE(
          activo boolean,
          plan_label text,
          vence date,
          dias_restantes integer,
          metodo_cobro text
        ) LANGUAGE plpgsql STABLE SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
        DECLARE
          v_org integer;
        BEGIN
          v_org := cotizat_security.context_organization_id();
          IF p_organization_id IS DISTINCT FROM v_org THEN
            RETURN;
          END IF;
          RETURN QUERY
          SELECT
            TRUE,
            CASE
              WHEN l.origen = 'pago' AND round(l.importe::numeric, 2) = 89.00
                THEN 'Plan anual'
              WHEN l.origen = 'pago' AND round(l.importe::numeric, 2) = 9.99
                THEN 'Plan mensual'
              WHEN l.origen = 'pago' THEN 'Plan de pago'
              ELSE COALESCE(NULLIF(l.metodo_cobro, ''), l.origen)
            END,
            l.vence,
            GREATEST((l.vence - CURRENT_DATE), 0),
            l.metodo_cobro
          FROM public.licencias l
          WHERE l.organizacion_id = p_organization_id
            AND l.estado = 'activa'
            AND l.inicio <= CURRENT_DATE
            AND l.vence >= CURRENT_DATE
          ORDER BY l.vence DESC
          LIMIT 1;
        END;
        $$;
        """
    )
    op.execute(f"REVOKE ALL ON FUNCTION cotizat_security.{FUNCION}(integer) FROM PUBLIC")
    op.execute(
        f"GRANT EXECUTE ON FUNCTION cotizat_security.{FUNCION}(integer) "
        "TO cotizat_app"
    )


def downgrade() -> None:
    if not _postgres():
        return
    op.execute(f"DROP FUNCTION IF EXISTS cotizat_security.{FUNCION}(integer)")
