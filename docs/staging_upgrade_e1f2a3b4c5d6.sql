-- Cotizat / Supabase SQL Editor
-- Migracion Alembic e1f2a3b4c5d6; revision previa obligatoria: d0e1f2a3b4c5
-- Ejecutar en orden. No ejecutar si alembic_version no coincide.
BEGIN;
DO $$ BEGIN
 IF NOT EXISTS (SELECT 1 FROM public.alembic_version WHERE version_num = 'd0e1f2a3b4c5') THEN
  RAISE EXCEPTION 'Revision previa incorrecta: se esperaba d0e1f2a3b4c5';
 END IF;
END $$;
ALTER TABLE public.configuracion ADD COLUMN IF NOT EXISTS fuente_tipo_cambio varchar(120) DEFAULT '';
UPDATE public.alembic_version SET version_num = 'e1f2a3b4c5d6' WHERE version_num = 'd0e1f2a3b4c5';
COMMIT;
