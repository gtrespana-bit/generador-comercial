-- CotizaT — actualización de d7f2a9c41e63 a e1a4b7c9d2f0
-- Hace permanente la corrección de lectura de alembic_version para
-- cotizat_runtime (miembro de cotizat_app y sin BYPASSRLS).
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
    WHERE version_num = 'd7f2a9c41e63'
  ) THEN
    RAISE EXCEPTION
      'Se esperaba alembic_version en d7f2a9c41e63 antes de aplicar e1a4b7c9d2f0';
  END IF;
END
$check$;

-- alembic_version solo contiene metadatos de migración, no datos de tenant.
-- Si RLS está activo, cotizat_runtime puede conectarse pero no ver la fila y
-- /readyz informa «sin-version». El login de runtime solo recibe SELECT.
ALTER TABLE public.alembic_version DISABLE ROW LEVEL SECURITY;
GRANT SELECT ON TABLE public.alembic_version TO cotizat_app;

UPDATE public.alembic_version
SET version_num = 'e1a4b7c9d2f0'
WHERE version_num = 'd7f2a9c41e63';

COMMIT;

-- Verificación: debe devolver e1a4b7c9d2f0
SELECT version_num FROM public.alembic_version;

-- Verificación: ambas columnas deben ser false y la última columna true.
-- Se comprueba el privilegio del rol grupal, no el de la sesión admin.
SELECT c.relrowsecurity,
       c.relforcerowsecurity,
       has_table_privilege(
         'cotizat_app', 'public.alembic_version', 'SELECT'
       ) AS cotizat_app_puede_leer
FROM pg_catalog.pg_class AS c
JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace
WHERE n.nspname = 'public' AND c.relname = 'alembic_version';
