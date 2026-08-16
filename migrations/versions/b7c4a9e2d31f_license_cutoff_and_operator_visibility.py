"""Acceso por licencia y visibilidad de operador (E1-060, segunda parte).

Tres piezas que completan el panel de licencias y habilitan el corte
automático de acceso al vencer una licencia:

1. ``cotizat_security.organization_has_license(p_organization_id)``
   Devuelve **solo un booleano**: si la organización tiene hoy una licencia
   vigente (activa y dentro de fechas). Es SECURITY DEFINER porque la sesión
   de un cliente no puede leer ``public.licencias`` —y no debe—, y el corte
   se aplica precisamente a sesiones de cliente. Guardia explícita: el
   parámetro debe coincidir con el claim de organización de la sesión, así
   que nadie puede sondear el estado de licencia de otra empresa.

2. ``cotizat_security.organization_admin_emails(p_organization_id)``
   Devuelve los correos de propietario/administrador activos de la
   organización, para los avisos de vencimiento por correo. Guardia
   explícita: exige la marca de operador de la sesión; una sesión de cliente
   obtiene cero filas.

3. Corrección de la política ``cotizat_org_select`` de ``organizaciones``.
   La versión original (``c93e7a4d20f1``) solo devolvía las organizaciones
   donde el usuario tiene membresía, así que el panel de operador veía
   únicamente las organizaciones del propio titular: las de un cliente
   quedaban invisibles y no se les podía conceder licencia. Ahora la sesión
   marcada como operador también las lista —el panel muestra nombre, período
   y cobro, nunca datos de negocio— sin cambiar nada para sesiones normales.

Como en ``c93e7a4d20f1``, las funciones se reasignan al usuario que aplica la
migración (sesión administrativa), se revocan de PUBLIC y se conceden solo a
``cotizat_app``. En Supabase ese propietario es superusuario, así que el cuerpo
bypassea el FORCE RLS de ``licencias`` sin conceder acceso nuevo a nadie más.
"""
from typing import Sequence, Union

from alembic import op


revision: str = "b7c4a9e2d31f"
down_revision: Union[str, Sequence[str], None] = "f4c1d8e37a95"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


#: ¿Tiene la organización de la sesión una licencia que dé acceso hoy?
#: La guardia del claim impide sondear organizaciones ajenas; sin claim de
#: organización la respuesta es FALSE (``current_setting(..., true)`` da NULL).
ACCESS_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION cotizat_security.organization_has_license(
  p_organization_id integer
) RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
  SELECT COALESCE(
    pg_catalog.current_setting('cotizat.organization_id', true)
      = p_organization_id::text
    AND EXISTS (
      SELECT 1
      FROM public.licencias AS l
      WHERE l.organizacion_id = p_organization_id
        AND l.estado = 'activa'
        AND l.inicio <= CURRENT_DATE
        AND l.vence >= CURRENT_DATE
    ),
    FALSE
  )
$$
"""

#: Correos de los administradores activos de una organización, exclusivamente
#: para que el operador envíe avisos de vencimiento. Sin marca de operador
#: no devuelve nada.
ADMIN_EMAILS_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION cotizat_security.organization_admin_emails(
  p_organization_id integer
) RETURNS TABLE(email varchar) LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
  SELECT u.email
  FROM public.membresias AS m
  JOIN public.usuarios AS u ON u.id = m.usuario_id
  WHERE m.organizacion_id = p_organization_id
    AND m.activa IS TRUE
    AND u.activo IS TRUE
    AND m.rol IN ('propietario', 'administrador')
    AND COALESCE(
      pg_catalog.current_setting('cotizat.es_operador', true) = 'on',
      FALSE
    )
$$
"""

#: La política original exigía membresía propia: el operador era ciego a las
#: organizaciones de sus clientes. El operador las lista para administrar
#: licencias; una sesión de cliente no gana nada con este cambio.
ORG_SELECT_POLICY_SQL = """
CREATE POLICY cotizat_org_select ON public.organizaciones
FOR SELECT TO cotizat_app
USING (
  cotizat_security.membership_role(id) IS NOT NULL
  OR COALESCE(
    pg_catalog.current_setting('cotizat.es_operador', true) = 'on',
    FALSE
  )
)
"""

#: Texto original de ``c93e7a4d20f1``, restaurado al degradar.
_ORG_SELECT_POLICY_ANTERIOR_SQL = """
CREATE POLICY cotizat_org_select ON public.organizaciones
FOR SELECT TO cotizat_app
USING (cotizat_security.membership_role(id) IS NOT NULL)
"""

_FUNCTION_SIGNATURES = (
    "organization_has_license(integer)",
    "organization_admin_emails(integer)",
)


def _postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    if not _postgres():
        # SQLite (escritorio y pruebas): sin RLS ni funciones de seguridad; la
        # comprobación de licencia usa la consulta directa de la aplicación.
        return

    op.execute(ACCESS_FUNCTION_SQL)
    op.execute(ADMIN_EMAILS_FUNCTION_SQL)
    for signature in _FUNCTION_SIGNATURES:
        op.execute(
            f"ALTER FUNCTION cotizat_security.{signature} OWNER TO CURRENT_USER"
        )
        op.execute(
            f"REVOKE ALL ON FUNCTION cotizat_security.{signature} FROM PUBLIC"
        )
        op.execute(
            f"GRANT EXECUTE ON FUNCTION cotizat_security.{signature}"
            " TO cotizat_app"
        )

    op.execute("DROP POLICY IF EXISTS cotizat_org_select ON public.organizaciones")
    op.execute(ORG_SELECT_POLICY_SQL)


def downgrade() -> None:
    if not _postgres():
        return

    op.execute("DROP POLICY IF EXISTS cotizat_org_select ON public.organizaciones")
    op.execute(_ORG_SELECT_POLICY_ANTERIOR_SQL)
    for signature in _FUNCTION_SIGNATURES:
        op.execute(f"DROP FUNCTION IF EXISTS cotizat_security.{signature}")
