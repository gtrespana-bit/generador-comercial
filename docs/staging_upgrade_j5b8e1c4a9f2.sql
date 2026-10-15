-- CotizaT — actualización de i4d7c1b8e2f5 a j5b8e1c4a9f2
--
-- RLS activo en `public.alembic_version` con lectura para el rol de la
-- aplicación. Cierra el aviso **crítico** del asesor de Supabase
-- «RLS Disabled in Public»: `public` está expuesto a PostgREST, y una tabla sin
-- RLS queda accesible con la clave pública `anon`.
--
-- Por qué estaba desactivado: `e1a4b7c9d2f0` lo desactivó para que el login
-- limitado `cotizat_runtime` pudiera leer la revisión de Alembic en `/readyz`.
-- Con RLS activo y ninguna política, ese login no veía la fila y el readiness
-- respondía «sin-version». La solución correcta no es quitar RLS (lo que abre
-- la tabla a PostgREST) sino dejar RLS activo y autorizar solo la lectura al
-- rol de la aplicación: eso es lo que hace esta revisión.
--
-- Resultado: `anon` y `authenticated` no ven ninguna fila (ni con la clave
-- pública), `cotizat_app` lee la revisión como antes y el propietario
-- (migraciones con la URL administrativa) no queda afectado, porque RLS no se
-- aplica al dueño de la tabla. No se conceden INSERT/UPDATE/DELETE: la marca
-- sigue avanzando solo desde el SQL Editor o con `alembic upgrade head`.
--
-- Ejecutar una sola vez en el SQL Editor de Supabase con el rol
-- administrativo (nunca con `cotizat_runtime` ni con `cotizat_app`) y solo si
-- la versión actual es i4d7c1b8e2f5.

BEGIN;

DO $$
DECLARE
  v_version text;
BEGIN
  SELECT version_num INTO v_version FROM public.alembic_version LIMIT 1;
  IF v_version IS DISTINCT FROM 'i4d7c1b8e2f5' THEN
    RAISE EXCEPTION
      'Se esperaba alembic_version i4d7c1b8e2f5 antes de j5b8e1c4a9f2; se encontró %',
      COALESCE(v_version, '<vacío>');
  END IF;
END
$$;

ALTER TABLE public.alembic_version ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS cotizat_alembic_version_lectura ON public.alembic_version;
CREATE POLICY cotizat_alembic_version_lectura ON public.alembic_version
  FOR SELECT TO cotizat_app
  USING (true);

-- El rol de la aplicación conserva exactamente la lectura que ya tenía.
GRANT SELECT ON TABLE public.alembic_version TO cotizat_app;

-- PostgREST usa `anon`/`authenticated` con la clave pública: se les retira
-- cualquier privilegio sobre la tabla de metadatos, aunque RLS ya los filtra.
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
    EXECUTE 'REVOKE ALL ON TABLE public.alembic_version FROM anon';
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
    EXECUTE 'REVOKE ALL ON TABLE public.alembic_version FROM authenticated';
  END IF;
END
$$;

UPDATE public.alembic_version
SET version_num = 'j5b8e1c4a9f2'
WHERE version_num = 'i4d7c1b8e2f5';

COMMIT;

-- Verificación (los tres valores esperados van en el comentario):
-- SELECT relname, relrowsecurity, relforcerowsecurity
--   FROM pg_class WHERE relname = 'alembic_version';
--   → alembic_version | t | f
-- SELECT policyname, cmd, qual FROM pg_policies
--  WHERE schemaname = 'public' AND tablename = 'alembic_version';
--   → cotizat_alembic_version_lectura | SELECT | true
-- SELECT has_table_privilege('cotizat_app', 'public.alembic_version', 'SELECT')
--        AS app_lee,
--        has_table_privilege('anon', 'public.alembic_version', 'SELECT')
--        AS anon_lee;
--   → app_lee = t, anon_lee = f
-- SELECT version_num FROM public.alembic_version;
--   → j5b8e1c4a9f2
--
-- Y el resto del asesor de seguridad, por si queda alguna otra tabla:
-- SELECT c.relname
--   FROM pg_class c
--   JOIN pg_namespace n ON n.oid = c.relnamespace
--  WHERE n.nspname = 'public' AND c.relkind = 'r' AND NOT c.relrowsecurity
--  ORDER BY 1;
