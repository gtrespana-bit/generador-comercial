-- CotizaT staging: login de aplicación limitado (Paso C).
-- Ejecutar en Supabase → SQL Editor DESPUÉS de aplicar docs/staging_migration.sql
-- (que crea el rol sin login `cotizat_app`).
--
-- 1) Decide una contraseña larga y aleatoria para el login runtime y
--    reemplaza CAMBIA_ESTA_CONTRASEÑA_LARGA debajo (solo en tu panel, nunca
--    en el chat ni en Git).
-- 2) Pulsa Run.
-- 3) Ejecuta los dos SELECT de verificación del final.
--
-- Resultado exigido:
--   rolsuper     = false
--   rolbypassrls = false
--   rolinherit   = true
--   miembro de cotizat_app = true

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'cotizat_runtime') THEN
    CREATE ROLE cotizat_runtime
      LOGIN
      INHERIT
      NOSUPERUSER
      NOCREATEDB
      NOCREATEROLE
      NOREPLICATION
      NOBYPASSRLS;
  END IF;
  -- Si el rol ya existía, NO se usa ALTER ROLE con atributos reservados
  -- (SUPERUSER/REPLICATION/BYPASSRLS): el SQL Editor de Supabase cloud no
  -- corre como superuser y ese ALTER fallaría. Si necesitas corregir un rol
  -- existente que tenga SUPERUSER o BYPASSRLS, contacta al propietario del
  -- proyecto; la app lo detectará y se negará a arrancar.
END
$$;

GRANT cotizat_app TO cotizat_runtime;

-- Contraseña (cambia el literal). Usa comillas dollar-quoted para que una
-- contraseña con símbolos o comillas no rompa el SQL.
ALTER ROLE cotizat_runtime WITH LOGIN PASSWORD $cotizat$CAMBIA_ESTA_CONTRASEÑA_LARGA$cotizat$;

-- Verificación (copia y pega el resultado, sin la contraseña):
SELECT rolname, rolsuper, rolbypassrls, rolinherit
FROM pg_catalog.pg_roles
WHERE rolname = 'cotizat_runtime';

SELECT pg_has_role('cotizat_runtime', 'cotizat_app', 'member') AS miembro_cotizat_app;
