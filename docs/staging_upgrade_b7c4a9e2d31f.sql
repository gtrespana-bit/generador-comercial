-- CotizaT — actualización de f4c1d8e37a95 a b7c4a9e2d31f
-- E1-060 (segunda parte): corte automático de acceso, avisos de vencimiento
-- y corrección de la visibilidad del panel de operador.
--
-- Contenido:
--   1. Función cotizat_security.organization_has_license(integer): booleano
--      "¿tiene la organización de la sesión una licencia vigente?" para el
--      corte automático. Guardada por el claim de organización: nadie puede
--      sondear el estado de licencia de otra empresa.
--   2. Función cotizat_security.organization_admin_emails(integer): correos
--      de propietario/administrador activos, solo para sesiones de operador
--      (avisos de vencimiento).
--   3. Política cotizat_org_select corregida: la sesión de operador lista
--      todas las organizaciones (la versión de c93e7a4d20f1 solo mostraba las
--      propias y el panel no podía licenciar a clientes).
--
-- Uso (Supabase → SQL Editor → New query): pega TODO este archivo y pulsa Run.
-- Debe ejecutarse con una sesión administrativa/propietaria. No uses
-- DATABASE_URL del runtime para aplicar DDL.
-- Comprueba primero la versión con:
--   SELECT version_num FROM public.alembic_version;
--
-- Va dentro de una transacción: si algo falla, no se aplica a medias.

BEGIN;

DO $check$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM public.alembic_version
    WHERE version_num = 'f4c1d8e37a95'
  ) THEN
    RAISE EXCEPTION
      'Se esperaba alembic_version en f4c1d8e37a95 antes de aplicar b7c4a9e2d31f';
  END IF;
END
$check$;

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
$$;

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
$$;

ALTER FUNCTION cotizat_security.organization_has_license(integer)
  OWNER TO CURRENT_USER;
ALTER FUNCTION cotizat_security.organization_admin_emails(integer)
  OWNER TO CURRENT_USER;

REVOKE ALL ON FUNCTION cotizat_security.organization_has_license(integer)
  FROM PUBLIC;
REVOKE ALL ON FUNCTION cotizat_security.organization_admin_emails(integer)
  FROM PUBLIC;

GRANT EXECUTE ON FUNCTION cotizat_security.organization_has_license(integer)
  TO cotizat_app;
GRANT EXECUTE ON FUNCTION cotizat_security.organization_admin_emails(integer)
  TO cotizat_app;

-- Corrección de visibilidad del panel: el operador lista todas las
-- organizaciones (nombre, período y cobro; nunca datos de negocio). Para
-- sesiones de cliente la política queda exactamente igual.
DROP POLICY IF EXISTS cotizat_org_select ON public.organizaciones;

CREATE POLICY cotizat_org_select ON public.organizaciones
FOR SELECT TO cotizat_app
USING (
  cotizat_security.membership_role(id) IS NOT NULL
  OR COALESCE(
    pg_catalog.current_setting('cotizat.es_operador', true) = 'on',
    FALSE
  )
);

UPDATE public.alembic_version
SET version_num = 'b7c4a9e2d31f'
WHERE version_num = 'f4c1d8e37a95';

COMMIT;

-- Verificación: debe devolver b7c4a9e2d31f
SELECT version_num FROM public.alembic_version;

-- Verificación de la política corregida: la definición debe incluir la marca
-- de operador.
SELECT pg_get_expr(pol.polqual, pol.polrelid) AS definicion_org_select
FROM pg_catalog.pg_policy AS pol
JOIN pg_catalog.pg_class AS c ON c.oid = pol.polrelid
JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace
WHERE n.nspname = 'public'
  AND c.relname = 'organizaciones'
  AND pol.polname = 'cotizat_org_select';

-- Verificación de las funciones: propietario actual y ejecución revocada al
-- público. El corte solo puede consultar la organización del propio claim:
--   SELECT cotizat_security.organization_has_license(<id>);
-- desde la sesión runtime debe devolver FALSE para una organización ajena.
SELECT p.proname,
       pg_get_userbyid(p.proowner) AS propietario,
       p.prosecdef AS security_definer
FROM pg_catalog.pg_proc AS p
JOIN pg_catalog.pg_namespace AS n ON n.oid = p.pronamespace
WHERE n.nspname = 'cotizat_security'
  AND p.proname IN ('organization_has_license', 'organization_admin_emails');
