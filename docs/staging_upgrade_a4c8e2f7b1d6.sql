-- CotizaT — a4c8e2f7b1d6: evidencia del precio nacional de referencia.
-- Conserva rango, unidad, fecha, IVA, transporte y observaciones de la matriz.

BEGIN;

DO $$
DECLARE
  v_version text;
BEGIN
  SELECT version_num INTO v_version FROM public.alembic_version LIMIT 1;
  IF v_version IS DISTINCT FROM 'b9f4d8a2c6e1' THEN
    RAISE EXCEPTION
      'Se esperaba alembic_version b9f4d8a2c6e1 antes de a4c8e2f7b1d6; se encontró %',
      COALESCE(v_version, '<vacío>');
  END IF;
END
$$;

ALTER TABLE public.precios_recursos_mercado
  ADD COLUMN IF NOT EXISTS codigo_recurso varchar(80) DEFAULT '',
  ADD COLUMN IF NOT EXISTS precio_min double precision,
  ADD COLUMN IF NOT EXISTS precio_max double precision,
  ADD COLUMN IF NOT EXISTS unidad_referencia varchar(30) DEFAULT '',
  ADD COLUMN IF NOT EXISTS fecha_consulta date,
  ADD COLUMN IF NOT EXISTS incluye_iva varchar(20) DEFAULT 'por_verificar',
  ADD COLUMN IF NOT EXISTS incluye_transporte varchar(20) DEFAULT 'no_confirmado',
  ADD COLUMN IF NOT EXISTS observaciones text DEFAULT '';

UPDATE public.precios_recursos_mercado AS p
SET codigo_recurso = r.codigo
FROM public.recursos AS r
WHERE r.id = p.recurso_id
  AND COALESCE(p.codigo_recurso, '') = '';

CREATE INDEX IF NOT EXISTS ix_precios_recursos_mercado_codigo_recurso
  ON public.precios_recursos_mercado (codigo_recurso);

UPDATE public.alembic_version
SET version_num = 'a4c8e2f7b1d6'
WHERE version_num = 'b9f4d8a2c6e1';

COMMIT;

-- Verificación:
-- SELECT version_num FROM public.alembic_version;  -- → a4c8e2f7b1d6
-- SELECT column_name FROM information_schema.columns
-- WHERE table_schema='public' AND table_name='precios_recursos_mercado'
--   AND column_name IN ('codigo_recurso','precio_min','precio_max',
--     'unidad_referencia','fecha_consulta','incluye_iva',
--     'incluye_transporte','observaciones');
