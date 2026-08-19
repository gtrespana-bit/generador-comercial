-- Cotizat / Supabase SQL Editor
-- Migracion Alembic d0e1f2a3b4c5; revision previa obligatoria: c9d0e1f2a3b4
-- Ejecutar en orden. No ejecutar si alembic_version no coincide.
BEGIN;
DO $$ BEGIN
 IF NOT EXISTS (SELECT 1 FROM public.alembic_version WHERE version_num = 'c9d0e1f2a3b4') THEN
  RAISE EXCEPTION 'Revision previa incorrecta: se esperaba c9d0e1f2a3b4';
 END IF;
END $$;
ALTER TABLE public.cambios_alcance ADD COLUMN IF NOT EXISTS moneda varchar(10) DEFAULT 'USD';
ALTER TABLE public.cambio_alcance_items ADD COLUMN IF NOT EXISTS moneda varchar(10) DEFAULT 'USD';
UPDATE public.alembic_version SET version_num = 'd0e1f2a3b4c5' WHERE version_num = 'c9d0e1f2a3b4';
COMMIT;
