-- CotizaT — actualización de f8a1b2c3d4e5 a d6e2f9c4b8a1
-- Visibilidad por organización y actualización incremental del catálogo.
-- Ejecutar una sola vez con el rol administrativo de Supabase/PostgreSQL.

BEGIN;

DO $$
DECLARE
  v_version text;
BEGIN
  SELECT version_num INTO v_version FROM public.alembic_version LIMIT 1;
  IF v_version IS DISTINCT FROM 'f8a1b2c3d4e5' THEN
    RAISE EXCEPTION
      'Se esperaba alembic_version f8a1b2c3d4e5 antes de d6e2f9c4b8a1; se encontró %',
      COALESCE(v_version, '<vacío>');
  END IF;
END
$$;

ALTER TABLE public.partidas
  ADD COLUMN IF NOT EXISTS catalogo_uid varchar(100),
  ADD COLUMN IF NOT EXISTS es_oficial boolean DEFAULT false,
  ADD COLUMN IF NOT EXISTS oculta boolean DEFAULT false,
  ADD COLUMN IF NOT EXISTS version_alta_catalogo integer DEFAULT 0;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_partida_organizacion_catalogo_uid'
      AND conrelid = 'public.partidas'::regclass
  ) THEN
    ALTER TABLE public.partidas
      ADD CONSTRAINT uq_partida_organizacion_catalogo_uid
      UNIQUE (organizacion_id, catalogo_uid);
  END IF;
END
$$;

CREATE INDEX IF NOT EXISTS ix_partidas_catalogo_uid
  ON public.partidas(catalogo_uid);
CREATE INDEX IF NOT EXISTS ix_partidas_oculta
  ON public.partidas(oculta);

UPDATE public.alembic_version
SET version_num = 'd6e2f9c4b8a1'
WHERE version_num = 'f8a1b2c3d4e5';

COMMIT;

-- Verificación:
-- SELECT version_num FROM public.alembic_version;
-- SELECT column_name FROM information_schema.columns
-- WHERE table_schema = 'public' AND table_name = 'partidas'
--   AND column_name IN ('catalogo_uid','es_oficial','oculta','version_alta_catalogo');
