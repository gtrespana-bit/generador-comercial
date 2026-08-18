"""El resumen del cliente suma el acceso encadenado (d4e2f6a8b0c1).

Cuando una organización renueva con días por delante, ``crear_licencia``
encadena la licencia nueva al día siguiente del vencimiento anterior. La
función ``cotizat_security.organization_license_info`` (revisiones
``f9d4c2a7e5b3`` / ``a1b2c3d4e5f6``) devolvía solo el vencimiento de la
licencia que cubre hoy: si quedaban 4 días y se añadía 1 mes, la barra
lateral y Configuración mostraban «4 d» en vez del total (~34 d).

Esta revisión reemplaza la función por una versión que calcula el **final
de la cadena**: parte de la licencia que da acceso hoy y avanza por las
licencias activas contiguas (la siguiente empieza el día después de que
termine la anterior, con un día de hueco la cadena se rompe) hasta quedarse
con el vencimiento más lejano. Los días restantes se calculan contra ese
final. La etiqueta del plan y el método de cobro siguen saliendo de la
licencia que da acceso hoy.

Misma política que en ``a1b2c3d4e5f6``: la función es SECURITY DEFINER con
la guardia del claim de sesión y se concede solo a ``cotizat_app``.
"""
from typing import Sequence, Union

from alembic import op


revision: str = "d4e2f6a8b0c1"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
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
          v_actual record;
          v_fin date;
        BEGIN
          v_org := cotizat_security.context_organization_id();
          IF p_organization_id IS DISTINCT FROM v_org THEN
            RETURN;
          END IF;

          -- Licencia que da acceso hoy (la primera de la cadena): de ella
          -- salen la etiqueta del plan y el método de cobro.
          SELECT *
          INTO v_actual
          FROM public.licencias l
          WHERE l.organizacion_id = p_organization_id
            AND l.estado = 'activa'
            AND l.inicio <= CURRENT_DATE
            AND l.vence >= CURRENT_DATE
          ORDER BY l.vence DESC
          LIMIT 1;
          IF v_actual.id IS NULL THEN
            RETURN;
          END IF;

          -- Último día del encadenado: las renovaciones empiezan al día
          -- siguiente del vencimiento anterior, así que el acceso llega
          -- hasta el final de la cadena (4 días + 1 mes → ~34 días), no
          -- hasta la primera licencia. `l.vence > c.fin` garantiza
          -- progreso y terminación de la recursión; un día de hueco entre
          -- licencias corta la cadena.
          WITH RECURSIVE cadena AS (
            SELECT v_actual.vence AS fin
            UNION
            SELECT l.vence
            FROM public.licencias l
            JOIN cadena c
              ON l.organizacion_id = p_organization_id
             AND l.estado = 'activa'
             AND l.inicio <= c.fin + 1
             AND l.vence > c.fin
          )
          SELECT MAX(fin) INTO v_fin FROM cadena;
          v_fin := COALESCE(v_fin, v_actual.vence);

          activo := TRUE::boolean;
          plan_label := (CASE
              WHEN v_actual.origen = 'pago'
                   AND round(v_actual.importe::numeric, 2) = 89.00
                THEN 'Plan anual'
              WHEN v_actual.origen = 'pago'
                   AND round(v_actual.importe::numeric, 2) = 9.99
                THEN 'Plan mensual'
              WHEN v_actual.origen = 'pago' THEN 'Plan de pago'
              ELSE COALESCE(NULLIF(v_actual.metodo_cobro, ''), v_actual.origen)
            END)::text;
          vence := v_fin;
          dias_restantes := GREATEST((v_fin - CURRENT_DATE), 0)::integer;
          metodo_cobro := v_actual.metodo_cobro::text;
          RETURN NEXT;
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
    # Downgrade conserva la versión corregida; no restaura el resumen corto.
    if not _postgres():
        return
    # No-op: la función anterior devolvía un vencimiento incompleto.
    pass
