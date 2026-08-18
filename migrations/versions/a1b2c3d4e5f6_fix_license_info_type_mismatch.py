"""Corrige desajuste de tipos en organization_license_info (hotfix 18/08/2026).

El despliegue f9d4c2a7e5b3 fallaba con
  psycopg.errors.DatatypeMismatch: Returned type character varying(80)
  does not match expected type text in column 5.

`licencias.metodo_cobro` es varchar(80) y `licencias.origen` varchar(20);
la función declaraba RETURNS TABLE(..., text) pero devolvía varchar sin
cast explícito, lo que PostgreSQL considera incompatible en RETURN QUERY.
El mismo problema afectaba al CASE de plan_label y al GREATEST.
Este hotfix recrea la función con casts explícitos ::text / ::integer /
::boolean, idéntica a la versión corregida de f9d4c2a7e5b3, de forma que
las bases ya migradas queden reparadas y el próximo `alembic upgrade head`
no necesite intervención manual.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "f9d4c2a7e5b3"
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
            TRUE::boolean,
            (CASE
              WHEN l.origen = 'pago' AND round(l.importe::numeric, 2) = 89.00
                THEN 'Plan anual'
              WHEN l.origen = 'pago' AND round(l.importe::numeric, 2) = 9.99
                THEN 'Plan mensual'
              WHEN l.origen = 'pago' THEN 'Plan de pago'
              ELSE COALESCE(NULLIF(l.metodo_cobro, ''), l.origen)
            END)::text,
            l.vence,
            GREATEST((l.vence - CURRENT_DATE), 0)::integer,
            l.metodo_cobro::text
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
    # Downgrade deja la versión corregida; no restaura el bug.
    if not _postgres():
        return
    # No-op: mantener la función corregida también en downgrade.
    pass
