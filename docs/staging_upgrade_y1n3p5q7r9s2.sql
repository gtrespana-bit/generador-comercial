-- CotizaT — actualización de x9m2k4p8v1n6 a y1n3p5q7r9s2
-- Índice sobre public.recursos(codigo): el catálogo se busca por código en
-- prácticamente todas sus lecturas y en PostgreSQL la tabla solo tenía índice
-- por id y por organizacion_id, así que cada búsqueda por código recorría la
-- tabla entera (~22.000 filas por organización).
--
-- Por qué existe este archivo: en producción (Supabase) las migraciones se
-- aplican a mano pegando este SQL. El head exigido por el runtime cambia con
-- el despliegue, así que la base tiene que estar en y1n3p5q7r9s2 **antes** de
-- fusionar el código que lo declara.
--
-- Contenido:
--   1. Índice `ix_recursos_codigo` sobre public.recursos (codigo). No es
--      único: el catálogo es multi-tenant y varias organizaciones comparten
--      el mismo código, que es justo lo que el índice acelera.
--   2. Avance de la marca en public.alembic_version.
--
-- Uso (Supabase → SQL Editor → New query): pega TODO este archivo y pulsa Run.
-- Debe ejecutarse con una sesión administrativa/propietaria. No uses
-- DATABASE_URL del runtime para aplicar DDL.
-- Comprueba primero la versión con:
--   SELECT version_num FROM public.alembic_version;  -- debe ser x9m2k4p8v1n6
BEGIN;

DO $$
BEGIN
  IF (SELECT version_num FROM public.alembic_version LIMIT 1) IS DISTINCT FROM 'x9m2k4p8v1n6' THEN
    RAISE EXCEPTION 'Head inesperado; se esperaba x9m2k4p8v1n6';
  END IF;
  IF to_regclass('public.recursos') IS NULL THEN
    RAISE EXCEPTION 'No existe public.recursos; aplica antes las migraciones de catálogo';
  END IF;
END $$;

-- Running upgrade x9m2k4p8v1n6 -> y1n3p5q7r9s2

-- 1) Índice de búsqueda por código. Idempotente por si el código arrancó antes.
CREATE INDEX IF NOT EXISTS ix_recursos_codigo ON public.recursos (codigo);

-- 2) La creación de la tabla ya concede los privilegios; el índice no añade
--    ninguno nuevo, pero se comprueba que el rol de la aplicación puede leerla.
DO $$
BEGIN
  IF NOT has_table_privilege('cotizat_app', 'public.recursos', 'SELECT') THEN
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.recursos TO cotizat_app;
  END IF;
END $$;

UPDATE public.alembic_version
   SET version_num = 'y1n3p5q7r9s2'
 WHERE version_num = 'x9m2k4p8v1n6';

COMMIT;

-- Verificar:
--   SELECT version_num FROM public.alembic_version;                       -- y1n3p5q7r9s2
--   SELECT indexname FROM pg_indexes
--    WHERE schemaname='public' AND tablename='recursos'
--      AND indexname='ix_recursos_codigo';                               -- 1 fila
--   EXPLAIN (ANALYZE, COSTS OFF)
--     SELECT id FROM public.recursos WHERE codigo = 'MT-BLQ-15';
--                                                                         -- Index Scan
--
-- Revertir (si hiciera falta):
--   DROP INDEX IF EXISTS public.ix_recursos_codigo;
--   UPDATE public.alembic_version SET version_num='x9m2k4p8v1n6'
--    WHERE version_num = 'y1n3p5q7r9s2';
