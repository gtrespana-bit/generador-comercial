-- CotizaT — actualización de g7c8d9e0f1a2 a h1c4b7e9a3d2
--
-- Desglose del precio en el PDF del presupuesto: la casilla «Desglose del
-- precio: productos elegidos y mano de obra» reparte la base imponible entre
-- los productos y materiales elegidos y la mano de obra, los recursos y la
-- ejecución de los trabajos. Nace apagada: ningún presupuesto ya emitido
-- cambia de aspecto.
--
-- Ejecutar una sola vez en el SQL Editor de Supabase con el rol
-- administrativo (nunca con `cotizat_runtime`) y solo si la versión actual es
-- g7c8d9e0f1a2.

BEGIN;

DO $$
DECLARE
  v_version text;
BEGIN
  SELECT version_num INTO v_version FROM public.alembic_version LIMIT 1;
  IF v_version IS DISTINCT FROM 'g7c8d9e0f1a2' THEN
    RAISE EXCEPTION
      'Se esperaba alembic_version g7c8d9e0f1a2 antes de h1c4b7e9a3d2; se encontró %',
      COALESCE(v_version, '<vacío>');
  END IF;
END
$$;

ALTER TABLE public.presupuestos
  ADD COLUMN IF NOT EXISTS mostrar_desglose_precio boolean DEFAULT false;

-- Los presupuestos existentes conservan exactamente su PDF actual.
UPDATE public.presupuestos
SET mostrar_desglose_precio = false
WHERE mostrar_desglose_precio IS NULL;

UPDATE public.alembic_version
SET version_num = 'h1c4b7e9a3d2'
WHERE version_num = 'g7c8d9e0f1a2';

COMMIT;

-- Verificación:
-- SELECT version_num FROM public.alembic_version;
-- SELECT column_name, data_type, column_default
--   FROM information_schema.columns
--  WHERE table_schema = 'public' AND table_name = 'presupuestos'
--    AND column_name = 'mostrar_desglose_precio';
