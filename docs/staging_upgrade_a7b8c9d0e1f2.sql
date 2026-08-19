-- Cotizat / Supabase SQL Editor
-- Migracion Alembic a7b8c9d0e1f2; revision previa obligatoria: f9d4c2a7e5b3
-- Ejecutar en orden. No ejecutar si alembic_version no coincide.
BEGIN;
DO $$ BEGIN
 IF NOT EXISTS (SELECT 1 FROM public.alembic_version WHERE version_num = 'f9d4c2a7e5b3') THEN
  RAISE EXCEPTION 'Revision previa incorrecta: se esperaba f9d4c2a7e5b3';
 END IF;
END $$;
ALTER TABLE public.configuracion ADD COLUMN IF NOT EXISTS moneda_base_catalogo varchar(10) DEFAULT 'USD';
ALTER TABLE public.presupuestos ADD COLUMN IF NOT EXISTS moneda_base varchar(10) DEFAULT 'USD';
ALTER TABLE public.presupuestos ADD COLUMN IF NOT EXISTS fuente_tipo_cambio varchar(120) DEFAULT '';
ALTER TABLE public.proyectos ADD COLUMN IF NOT EXISTS moneda_contractual varchar(10) DEFAULT 'USD';
ALTER TABLE public.proyectos ADD COLUMN IF NOT EXISTS moneda_base varchar(10) DEFAULT 'USD';
ALTER TABLE public.proyectos ADD COLUMN IF NOT EXISTS tipo_cambio double precision;
ALTER TABLE public.proyectos ADD COLUMN IF NOT EXISTS fecha_tipo_cambio date;
ALTER TABLE public.proyectos ADD COLUMN IF NOT EXISTS fuente_tipo_cambio varchar(120) DEFAULT '';
UPDATE public.alembic_version SET version_num = 'a7b8c9d0e1f2' WHERE version_num = 'f9d4c2a7e5b3';
COMMIT;
