-- CotizaT — actualización de b2c3d4e5f6a7 a c0d1e2f3a4b5
-- Repara permisos/RLS de planos_obra y planos_mediciones (hotfix de planos).
--
-- La creación de las tablas (b2c3d4e5f6a7) y este hotfix llegaron sin su SQL
-- manual, así que algunas bases se quedaron en b2c3d4e5f6a7. Eso es lo que
-- destapó el incidente del 23/08/2026: al aplicar staging_upgrade_e4b8c2d6a190
-- la guarda rechazó la versión («Se esperaba alembic_version en c0d1e2f3a4b5»).
--
-- Uso (Supabase → SQL Editor → New query): pega TODO este archivo y pulsa Run.
-- Debe ejecutarse con una sesión administrativa/propietaria. No uses la
-- DATABASE_URL del runtime para aplicar DDL/DCL.
-- Comprueba primero la versión con:
--   SELECT version_num FROM public.alembic_version;
--
-- Todas las sentencias son deliberadamente idempotentes (misma filosofía que
-- la migración c0d1e2f3a4b5): pueden ejecutarse sobre una base que ya tenga
-- los permisos bien puestos sin cambiar nada. Va en una transacción: si algo
-- falla, no se aplica a medias.

BEGIN;

DO $check$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM public.alembic_version
    WHERE version_num = 'b2c3d4e5f6a7'
  ) THEN
    RAISE EXCEPTION
      'Se esperaba alembic_version en b2c3d4e5f6a7 antes de aplicar c0d1e2f3a4b5';
  END IF;
END
$check$;

-- 1) Permisos y RLS de planos_obra (orden idéntico a la migración).
REVOKE ALL ON TABLE public.planos_obra FROM PUBLIC;
ALTER TABLE public.planos_obra ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.planos_obra FORCE ROW LEVEL SECURITY;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.planos_obra TO cotizat_app;

DO $$
DECLARE secuencia text;
BEGIN
  secuencia := pg_get_serial_sequence('public.planos_obra', 'id');
  IF secuencia IS NOT NULL THEN
    EXECUTE format('GRANT USAGE, SELECT ON SEQUENCE %s TO cotizat_app', secuencia);
  END IF;
END $$;

-- 2) Permisos y RLS de planos_mediciones.
REVOKE ALL ON TABLE public.planos_mediciones FROM PUBLIC;
ALTER TABLE public.planos_mediciones ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.planos_mediciones FORCE ROW LEVEL SECURITY;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.planos_mediciones TO cotizat_app;

DO $$
DECLARE secuencia text;
BEGIN
  secuencia := pg_get_serial_sequence('public.planos_mediciones', 'id');
  IF secuencia IS NOT NULL THEN
    EXECUTE format('GRANT USAGE, SELECT ON SEQUENCE %s TO cotizat_app', secuencia);
  END IF;
END $$;

-- 3) Políticas por inquilino, limitadas al rol de aplicación.
DROP POLICY IF EXISTS cotizat_planos_obra_select ON public.planos_obra;
CREATE POLICY cotizat_planos_obra_select ON public.planos_obra
  FOR SELECT TO cotizat_app
  USING (cotizat_security.tenant_access(organizacion_id, FALSE));

DROP POLICY IF EXISTS cotizat_planos_obra_insert ON public.planos_obra;
CREATE POLICY cotizat_planos_obra_insert ON public.planos_obra
  FOR INSERT TO cotizat_app
  WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

DROP POLICY IF EXISTS cotizat_planos_obra_update ON public.planos_obra;
CREATE POLICY cotizat_planos_obra_update ON public.planos_obra
  FOR UPDATE TO cotizat_app
  USING (cotizat_security.tenant_access(organizacion_id, TRUE))
  WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

DROP POLICY IF EXISTS cotizat_planos_obra_delete ON public.planos_obra;
CREATE POLICY cotizat_planos_obra_delete ON public.planos_obra
  FOR DELETE TO cotizat_app
  USING (cotizat_security.tenant_access(organizacion_id, TRUE));

DROP POLICY IF EXISTS cotizat_planos_mediciones_select ON public.planos_mediciones;
CREATE POLICY cotizat_planos_mediciones_select ON public.planos_mediciones
  FOR SELECT TO cotizat_app
  USING (cotizat_security.tenant_access(organizacion_id, FALSE));

DROP POLICY IF EXISTS cotizat_planos_mediciones_insert ON public.planos_mediciones;
CREATE POLICY cotizat_planos_mediciones_insert ON public.planos_mediciones
  FOR INSERT TO cotizat_app
  WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

DROP POLICY IF EXISTS cotizat_planos_mediciones_update ON public.planos_mediciones;
CREATE POLICY cotizat_planos_mediciones_update ON public.planos_mediciones
  FOR UPDATE TO cotizat_app
  USING (cotizat_security.tenant_access(organizacion_id, TRUE))
  WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

DROP POLICY IF EXISTS cotizat_planos_mediciones_delete ON public.planos_mediciones;
CREATE POLICY cotizat_planos_mediciones_delete ON public.planos_mediciones
  FOR DELETE TO cotizat_app
  USING (cotizat_security.tenant_access(organizacion_id, TRUE));

UPDATE public.alembic_version
SET version_num = 'c0d1e2f3a4b5'
WHERE version_num = 'b2c3d4e5f6a7';

COMMIT;

-- Verificación: debe devolver c0d1e2f3a4b5
SELECT version_num FROM public.alembic_version;

-- Verificación: 8 políticas cotizat_planos_* sobre las dos tablas
SELECT tablename, policyname, cmd
FROM pg_policies
WHERE schemaname = 'public'
  AND tablename IN ('planos_obra', 'planos_mediciones')
ORDER BY tablename, policyname;

-- Siguiente paso obligatorio: aplicar docs/staging_upgrade_e4b8c2d6a190.sql
-- (alturas libres); sin él el visor sigue devolviendo 500 por la columna
-- planos_obra.altura_libre_m.
