-- CotizaT — actualización de a3d7e9c1b5f2 a f8a1b2c3d4e5
-- Taxonomía numérica del catálogo: capítulo > subcapítulo > apartado.
-- Ejecutar una sola vez con el rol administrativo de Supabase/PostgreSQL.

BEGIN;

DO $$
DECLARE
  v_version text;
BEGIN
  SELECT version_num INTO v_version FROM public.alembic_version LIMIT 1;
  IF v_version IS DISTINCT FROM 'a3d7e9c1b5f2' THEN
    RAISE EXCEPTION
      'Se esperaba alembic_version a3d7e9c1b5f2 antes de f8a1b2c3d4e5; se encontró %',
      COALESCE(v_version, '<vacío>');
  END IF;
END
$$;

ALTER TABLE public.configuracion
  ADD COLUMN IF NOT EXISTS version_catalogo integer DEFAULT 0;

ALTER TABLE public.categorias_partidas
  ADD COLUMN IF NOT EXISTS parent_id integer,
  ADD COLUMN IF NOT EXISTS codigo_segmento varchar(2) DEFAULT '',
  ADD COLUMN IF NOT EXISTS codigo_completo varchar(8),
  ADD COLUMN IF NOT EXISTS nombre varchar(120) DEFAULT '',
  ADD COLUMN IF NOT EXISTS nivel integer DEFAULT 1,
  ADD COLUMN IF NOT EXISTS orden integer DEFAULT 0,
  ADD COLUMN IF NOT EXISTS ambito varchar(30) DEFAULT 'reforma',
  ADD COLUMN IF NOT EXISTS activa boolean DEFAULT true,
  ADD COLUMN IF NOT EXISTS oficial boolean DEFAULT false;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'fk_categorias_partidas_parent_id'
      AND conrelid = 'public.categorias_partidas'::regclass
  ) THEN
    ALTER TABLE public.categorias_partidas
      ADD CONSTRAINT fk_categorias_partidas_parent_id
      FOREIGN KEY (parent_id)
      REFERENCES public.categorias_partidas(id)
      ON DELETE CASCADE;
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_categoria_partida_organizacion_codigo'
      AND conrelid = 'public.categorias_partidas'::regclass
  ) THEN
    ALTER TABLE public.categorias_partidas
      ADD CONSTRAINT uq_categoria_partida_organizacion_codigo
      UNIQUE (organizacion_id, codigo_completo);
  END IF;
END
$$;

CREATE INDEX IF NOT EXISTS ix_categorias_partidas_parent_id
  ON public.categorias_partidas(parent_id);
CREATE INDEX IF NOT EXISTS ix_categorias_partidas_codigo
  ON public.categorias_partidas(codigo_completo);

ALTER TABLE public.partidas
  ADD COLUMN IF NOT EXISTS apartado varchar(120) DEFAULT '',
  ADD COLUMN IF NOT EXISTS categoria_id integer,
  ADD COLUMN IF NOT EXISTS codigo_clasificacion varchar(20) DEFAULT '',
  ADD COLUMN IF NOT EXISTS codigo_legacy varchar(80) DEFAULT '',
  ADD COLUMN IF NOT EXISTS version_catalogo integer DEFAULT 0;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'fk_partidas_categoria_id'
      AND conrelid = 'public.partidas'::regclass
  ) THEN
    ALTER TABLE public.partidas
      ADD CONSTRAINT fk_partidas_categoria_id
      FOREIGN KEY (categoria_id)
      REFERENCES public.categorias_partidas(id)
      ON DELETE SET NULL;
  END IF;
END
$$;

CREATE INDEX IF NOT EXISTS ix_partidas_categoria_id
  ON public.partidas(categoria_id);

UPDATE public.alembic_version
SET version_num = 'f8a1b2c3d4e5'
WHERE version_num = 'a3d7e9c1b5f2';

COMMIT;

-- Verificación manual recomendada:
-- SELECT version_num FROM public.alembic_version;
-- SELECT column_name FROM information_schema.columns
-- WHERE table_schema = 'public' AND table_name IN ('partidas', 'categorias_partidas')
-- ORDER BY table_name, ordinal_position;
