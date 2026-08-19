-- Cotizat / Supabase SQL Editor
-- Migracion Alembic c9d0e1f2a3b4; revision previa obligatoria: b8c9d0e1f2a3
-- Ejecutar en orden. No ejecutar si alembic_version no coincide.
BEGIN;
DO $$ BEGIN
 IF NOT EXISTS (SELECT 1 FROM public.alembic_version WHERE version_num = 'b8c9d0e1f2a3') THEN
  RAISE EXCEPTION 'Revision previa incorrecta: se esperaba b8c9d0e1f2a3';
 END IF;
END $$;
ALTER TABLE public.presupuesto_items ADD COLUMN IF NOT EXISTS moneda varchar(10) DEFAULT 'USD';
ALTER TABLE public.productos ADD COLUMN IF NOT EXISTS moneda varchar(10) DEFAULT 'USD';
ALTER TABLE public.recursos ADD COLUMN IF NOT EXISTS moneda varchar(10) DEFAULT 'USD';
UPDATE public.alembic_version SET version_num = 'c9d0e1f2a3b4' WHERE version_num = 'b8c9d0e1f2a3';
COMMIT;
