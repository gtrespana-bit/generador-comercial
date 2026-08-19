-- Cotizat / Supabase SQL Editor
-- Migracion b4c5d6e7f8a9; revision previa obligatoria: a3b4c5d6e7f8
BEGIN;
DO $$ BEGIN
 IF NOT EXISTS (SELECT 1 FROM public.alembic_version WHERE version_num = 'a3b4c5d6e7f8') THEN
  RAISE EXCEPTION 'Revision previa incorrecta: se esperaba a3b4c5d6e7f8';
 END IF;
END $$;
ALTER TABLE public.recursos ADD COLUMN IF NOT EXISTS subtipo varchar(40) DEFAULT '';
ALTER TABLE public.recursos ADD COLUMN IF NOT EXISTS capacidad varchar(80) DEFAULT '';
ALTER TABLE public.recursos ADD COLUMN IF NOT EXISTS modalidad_tarifa varchar(30) DEFAULT 'hora';
ALTER TABLE public.recursos ADD COLUMN IF NOT EXISTS incluye_operador boolean DEFAULT false;
ALTER TABLE public.recursos ADD COLUMN IF NOT EXISTS incluye_combustible boolean DEFAULT false;
ALTER TABLE public.recursos ADD COLUMN IF NOT EXISTS incluye_flete boolean DEFAULT false;
ALTER TABLE public.recursos ADD COLUMN IF NOT EXISTS rendimiento_jornada double precision;
ALTER TABLE public.recursos ADD COLUMN IF NOT EXISTS horas_jornada_recurso double precision DEFAULT 8.0;
UPDATE public.alembic_version SET version_num = 'b4c5d6e7f8a9' WHERE version_num = 'a3b4c5d6e7f8';
COMMIT;
