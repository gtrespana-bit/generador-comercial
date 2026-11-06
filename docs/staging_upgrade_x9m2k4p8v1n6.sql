-- CotizaT — actualización de w3m9k2p8v1n4 a x9m2k4p8v1n6
-- Vistas guardadas favoritas: la marca que el operador pone en las vistas de
-- filtros que usa a diario, para tenerlas en una sección propia del sidebar.
--
-- Por qué existe este archivo: en producción (Supabase) las migraciones se
-- aplican a mano pegando este SQL. El head exigido por el runtime cambia con
-- el despliegue, así que la base tiene que estar en x9m2k4p8v1n6 **antes** de
-- fusionar el código que lo declara.
--
-- Contenido:
--   1. Columna `favorita` en public.vistas_guardadas (booleana, NOT NULL,
--      por omisión false: las vistas existentes no cambian de comportamiento).
--   2. Comprobación de que el rol de la aplicación puede leerla y escribirla.
--      Los privilegios de `vistas_guardadas` son de tabla (`GRANT ... ON
--      TABLE` a `cotizat_app`), así que cubren la columna nueva; se verifica
--      en lugar de volver a conceder.
--   3. Avance de la marca en public.alembic_version.
--
-- Uso (Supabase → SQL Editor → New query): pega TODO este archivo y pulsa Run.
-- Debe ejecutarse con una sesión administrativa/propietaria. No uses
-- DATABASE_URL del runtime para aplicar DDL.
-- Comprueba primero la versión con:
--   SELECT version_num FROM public.alembic_version;  -- debe ser w3m9k2p8v1n4
BEGIN;

DO $$
BEGIN
  IF (SELECT version_num FROM public.alembic_version LIMIT 1) IS DISTINCT FROM 'w3m9k2p8v1n4' THEN
    RAISE EXCEPTION 'Head inesperado; se esperaba w3m9k2p8v1n4';
  END IF;
  IF to_regclass('public.vistas_guardadas') IS NULL THEN
    RAISE EXCEPTION 'No existe public.vistas_guardadas; aplica antes las migraciones del panel';
  END IF;
END $$;

-- Running upgrade w3m9k2p8v1n4 -> x9m2k4p8v1n6

-- 1) Columna de la marca. Idempotente por si el código arrancó antes.
ALTER TABLE public.vistas_guardadas
  ADD COLUMN IF NOT EXISTS favorita BOOLEAN NOT NULL DEFAULT false;

-- 2) El runtime lee y escribe la tabla entera con privilegios de tabla.
DO $$
BEGIN
  IF NOT has_table_privilege('cotizat_app', 'public.vistas_guardadas', 'SELECT')
     OR NOT has_table_privilege('cotizat_app', 'public.vistas_guardadas', 'UPDATE') THEN
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.vistas_guardadas TO cotizat_app;
  END IF;
END $$;

UPDATE public.alembic_version
   SET version_num = 'x9m2k4p8v1n6'
 WHERE version_num = 'w3m9k2p8v1n4';

COMMIT;

-- Verificar:
--   SELECT version_num FROM public.alembic_version;                     -- x9m2k4p8v1n6
--   SELECT column_name, data_type, is_nullable, column_default
--     FROM information_schema.columns
--    WHERE table_schema='public' AND table_name='vistas_guardadas'
--      AND column_name='favorita';                                     -- false por omisión
--   SELECT count(*) FROM public.vistas_guardadas WHERE favorita;        -- 0 al empezar
--
-- Revertir (si hiciera falta):
--   ALTER TABLE public.vistas_guardadas DROP COLUMN IF EXISTS favorita;
--   UPDATE public.alembic_version SET version_num='w3m9k2p8v1n4'
--    WHERE version_num = 'x9m2k4p8v1n6';
