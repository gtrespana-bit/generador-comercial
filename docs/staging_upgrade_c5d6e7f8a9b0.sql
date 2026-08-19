-- Cotizat / Supabase SQL Editor
-- Merge de cabezas Alembic después de b4c5d6e7f8a9.
BEGIN;
DO $$ BEGIN
 IF NOT EXISTS (SELECT 1 FROM public.alembic_version WHERE version_num = 'b4c5d6e7f8a9') THEN
  RAISE EXCEPTION 'Revision previa incorrecta: se esperaba b4c5d6e7f8a9';
 END IF;
END $$;
UPDATE public.alembic_version SET version_num = 'c5d6e7f8a9b0' WHERE version_num = 'b4c5d6e7f8a9';
COMMIT;
