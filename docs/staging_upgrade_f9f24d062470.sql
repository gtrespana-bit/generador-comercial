-- CotizaT — corrección de visibilidad de alembic_version (d7f2a9c41e63 → f9f24d062470)
-- Arregla /readyz en 503 con «alembic: inesperado:sin-version».
--
-- Uso (Supabase → SQL Editor → New query): pega TODO este archivo y pulsa Run.
-- Es idempotente: puede ejecutarse más de una vez sin dañar nada.
--
-- Síntoma: SELECT version_num FROM alembic_version devuelve el head como
-- administrador, pero el rol runtime cotizat_runtime (miembro de cotizat_app)
-- obtiene cero filas sin error. Con el GRANT SELECT de c93e7a4d20f1 presente,
-- eso solo puede significar RLS activo sobre public.alembic_version sin
-- política que autorice a cotizat_app: RLS oculta la fila al rol de
-- aplicación. alembic_version es metadatos de migración, no datos de tenant.

-- 0) DIAGNÓSTICO (solo lectura): copia estos resultados y pégamelos si el
--    arreglo no dejara /readyz en 200.
--    - relrowsecurity=true con politicas=0 reproduce exactamente el bug.
SELECT c.relrowsecurity, c.relforcerowsecurity,
       count(p.policyname) AS politicas
FROM pg_catalog.pg_class AS c
JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace
LEFT JOIN pg_catalog.pg_policies AS p
       ON p.schemaname = n.nspname AND p.tablename = c.relname
WHERE n.nspname = 'public' AND c.relname = 'alembic_version'
GROUP BY c.relrowsecurity, c.relforcerowsecurity;

SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual
FROM pg_policies
WHERE schemaname = 'public' AND tablename = 'alembic_version';

SELECT grantee, privilege_type
FROM information_schema.role_table_grants
WHERE table_schema = 'public' AND table_name = 'alembic_version'
ORDER BY grantee, privilege_type;

SELECT version_num FROM alembic_version;

-- 1) CORRECCIÓN. Va en una transacción: si algo falla, no se aplica nada.
BEGIN;

-- Asegura la fila de versión previa si la base se montó sin ella (caso
-- histórico de docs/CONTINUIDAD_STAGING_SUPABASE.md).
INSERT INTO alembic_version (version_num)
SELECT 'd7f2a9c41e63'
WHERE NOT EXISTS (SELECT 1 FROM alembic_version);

-- RLS apagado y sin políticas residuales: metadatos de migración legibles
-- por el rol de aplicación.
ALTER TABLE public.alembic_version DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.alembic_version NO FORCE ROW LEVEL SECURITY;

DO $policy$
DECLARE pol record;
BEGIN
  FOR pol IN
    SELECT policyname FROM pg_catalog.pg_policies
    WHERE schemaname = 'public' AND tablename = 'alembic_version'
  LOOP
    EXECUTE format(
      'DROP POLICY IF EXISTS %I ON public.alembic_version', pol.policyname
    );
  END LOOP;
END
$policy$;

GRANT SELECT ON TABLE public.alembic_version TO cotizat_app;

UPDATE alembic_version
SET version_num = 'f9f24d062470'
WHERE version_num = 'd7f2a9c41e63';

COMMIT;

-- 2) VERIFICACIÓN.
--    Debe devolver f9f24d062470 (como administrador).
SELECT version_num FROM alembic_version;

--    Debe devolver relrowsecurity=false y politicas=0.
SELECT c.relrowsecurity, c.relforcerowsecurity,
       count(p.policyname) AS politicas
FROM pg_catalog.pg_class AS c
JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace
LEFT JOIN pg_catalog.pg_policies AS p
       ON p.schemaname = n.nspname AND p.tablename = c.relname
WHERE n.nspname = 'public' AND c.relname = 'alembic_version'
GROUP BY c.relrowsecurity, c.relforcerowsecurity;

--    La prueba definitiva: la misma consulta que ejecuta /readyz, pero como
--    el rol runtime (SET ROLE no necesita contraseña; el SQL Editor corre
--    como superusuario). Debe devolver f9f24d062470, no 0 filas.
SET ROLE cotizat_runtime;
SELECT version_num FROM public.alembic_version;
RESET ROLE;

SET ROLE cotizat_app;
SELECT version_num FROM public.alembic_version;
RESET ROLE;
