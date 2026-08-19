-- CotizaT — migración d9e2f3a4b5c6: tasa de referencia USD→moneda local (LatAm S2).
--
-- Añade configuracion.tasa_cambio (unidades de moneda_default por 1 USD) y
-- configuracion.fecha_tasa. NULL = 1 (USD): el catálogo en USD puede
-- mostrarse y cotizarse en COP/MXN/PEN… sin reescribir precios.
--
-- Ejecutar una sola vez con rol administrativo si la base ya está en c8f1a2b3d4e5.

BEGIN;

DO $$
DECLARE
  v_version text;
BEGIN
  SELECT version_num INTO v_version FROM public.alembic_version LIMIT 1;
  IF v_version IS DISTINCT FROM 'c8f1a2b3d4e5' THEN
    RAISE EXCEPTION
      'Se esperaba alembic_version c8f1a2b3d4e5 antes de d9e2f3a4b5c6; se encontró %',
      COALESCE(v_version, '<vacío>');
  END IF;
END
$$;

ALTER TABLE public.configuracion
  ADD COLUMN tasa_cambio double precision;

ALTER TABLE public.configuracion
  ADD COLUMN fecha_tasa date;

UPDATE public.alembic_version
SET version_num = 'd9e2f3a4b5c6'
WHERE version_num = 'c8f1a2b3d4e5';

COMMIT;

-- Verificación:
-- SELECT version_num FROM public.alembic_version;  -- → d9e2f3a4b5c6
-- SELECT column_name, data_type FROM information_schema.columns
-- WHERE table_schema = 'public' AND table_name = 'configuracion'
--   AND column_name IN ('tasa_cambio', 'fecha_tasa');
-- GET /readyz → {"ok": true, "alembic": "head:d9e2f3a4b5c6"}
