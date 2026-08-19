-- Cotizat / Supabase SQL Editor
-- Migracion Alembic b8c9d0e1f2a3; revision previa obligatoria: a7b8c9d0e1f2
-- Ejecutar en orden. No ejecutar si alembic_version no coincide.
BEGIN;
DO $$ BEGIN
 IF NOT EXISTS (SELECT 1 FROM public.alembic_version WHERE version_num = 'a7b8c9d0e1f2') THEN
  RAISE EXCEPTION 'Revision previa incorrecta: se esperaba a7b8c9d0e1f2';
 END IF;
END $$;
ALTER TABLE public.presupuesto_versiones ADD COLUMN IF NOT EXISTS moneda varchar(10) DEFAULT 'USD';
ALTER TABLE public.presupuesto_versiones ADD COLUMN IF NOT EXISTS moneda_base varchar(10) DEFAULT 'USD';
ALTER TABLE public.presupuesto_versiones ADD COLUMN IF NOT EXISTS tipo_cambio double precision;
ALTER TABLE public.presupuesto_versiones ADD COLUMN IF NOT EXISTS fecha_tipo_cambio date;
ALTER TABLE public.presupuesto_versiones ADD COLUMN IF NOT EXISTS fuente_tipo_cambio varchar(120) DEFAULT '';
ALTER TABLE public.facturas ADD COLUMN IF NOT EXISTS moneda_base varchar(10) DEFAULT 'USD';
ALTER TABLE public.facturas ADD COLUMN IF NOT EXISTS tipo_cambio double precision;
ALTER TABLE public.facturas ADD COLUMN IF NOT EXISTS fecha_tipo_cambio date;
ALTER TABLE public.facturas ADD COLUMN IF NOT EXISTS fuente_tipo_cambio varchar(120) DEFAULT '';
UPDATE public.alembic_version SET version_num = 'b8c9d0e1f2a3' WHERE version_num = 'a7b8c9d0e1f2';
COMMIT;
