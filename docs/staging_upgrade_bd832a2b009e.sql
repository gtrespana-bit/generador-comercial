-- CotizaT — actualización de a8f1c3d9e7b2 a bd832a2b009e
-- Fix RLS: el operador debe poder marcar organizaciones como TEST.
--
-- La columna es_test la creó a8f1c3d9e7b2 pero la política cotizat_org_update
-- solo dejaba actualizar a can_manage_team(id). El panel admin actúa como
-- operador (cotizat.es_operador = on) sin membresía en cada org cliente, así
-- que el toggle fallaba silenciosamente (0 filas = "No se pudo actualizar").
--
-- Este parche añade una política permisiva OR: operador puede UPDATE.

BEGIN;

DO $$
BEGIN
  IF (SELECT version_num FROM public.alembic_version LIMIT 1) IS DISTINCT FROM 'a8f1c3d9e7b2' THEN
    RAISE EXCEPTION 'Head inesperado; se esperaba a8f1c3d9e7b2, encontrado %', (SELECT version_num FROM public.alembic_version LIMIT 1);
  END IF;
END $$;

DROP POLICY IF EXISTS cotizat_org_update_operador ON public.organizaciones;
CREATE POLICY cotizat_org_update_operador ON public.organizaciones
  FOR UPDATE TO cotizat_app
  USING (COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', false))
  WITH CHECK (COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', false));

UPDATE public.alembic_version SET version_num = 'bd832a2b009e' WHERE version_num = 'a8f1c3d9e7b2';

COMMIT;

-- Verificar:
-- SELECT version_num FROM public.alembic_version; -- bd832a2b009e
-- SELECT policyname FROM pg_policies WHERE tablename='organizaciones' AND policyname='cotizat_org_update_operador';
