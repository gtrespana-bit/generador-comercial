-- CotizaT — migración c8f1a2b3d4e5: etiqueta del ID fiscal por país (LatAm S2).
--
-- Añade configuracion.etiqueta_id_fiscal (RIF, NIT, RUT, CUIT, RUC, RFC…)
-- para que clientes, presupuestos y PDFs muestren el nombre local del ID
-- fiscal en lugar de «RIF» fijo. Default 'RIF' preserva instalaciones
-- venezolanas existentes.
--
-- Ejecutar una sola vez con rol administrativo si la base ya está en d2a7c9e4f1b3.

BEGIN;

DO $$
DECLARE
  v_version text;
BEGIN
  SELECT version_num INTO v_version FROM public.alembic_version LIMIT 1;
  IF v_version IS DISTINCT FROM 'd2a7c9e4f1b3' THEN
    RAISE EXCEPTION
      'Se esperaba alembic_version d2a7c9e4f1b3 antes de c8f1a2b3d4e5; se encontró %',
      COALESCE(v_version, '<vacío>');
  END IF;
END
$$;

ALTER TABLE public.configuracion
  ADD COLUMN etiqueta_id_fiscal varchar(20) DEFAULT 'RIF';

-- El DEFAULT de columna no rellena filas ya insertadas en algunos setups.
UPDATE public.configuracion
SET etiqueta_id_fiscal = 'RIF'
WHERE etiqueta_id_fiscal IS NULL;

UPDATE public.alembic_version
SET version_num = 'c8f1a2b3d4e5'
WHERE version_num = 'd2a7c9e4f1b3';

COMMIT;

-- Verificación:
-- SELECT version_num FROM public.alembic_version;  -- → c8f1a2b3d4e5
-- SELECT column_name, data_type, column_default FROM information_schema.columns
-- WHERE table_schema = 'public' AND table_name = 'configuracion'
--   AND column_name = 'etiqueta_id_fiscal';
