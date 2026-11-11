-- staging_upgrade_a8f1c3d9e7b2.sql — Aplicación manual en Supabase (SQL Editor)
-- Head a8f1c3d9e7b2: marca de organización de prueba (es_test)
-- Las cuentas marcadas como TEST no cuentan en ninguna métrica del panel
-- admin (MRR, totales, gráficos, embudo, cohortes). Siguen visibles en
-- listados con etiqueta gris. Exclusión completa.
-- Idempotente: se puede pegar dos veces sin duplicar.

-- 1) Columna
ALTER TABLE public.organizaciones ADD COLUMN IF NOT EXISTS es_test BOOLEAN NOT NULL DEFAULT false;

-- 2) Índice
CREATE INDEX IF NOT EXISTS ix_organizaciones_es_test ON public.organizaciones (es_test);

-- 3) Avanzar marca Alembic solo si veníamos de la cabeza anterior
UPDATE public.alembic_version SET version_num = 'a8f1c3d9e7b2' WHERE version_num = 'z3m9k2p8v1n7';

-- 4) Si no había fila de versión (BD fresca con tablas ya creadas), crearla
INSERT INTO public.alembic_version (version_num)
SELECT 'a8f1c3d9e7b2' WHERE NOT EXISTS (SELECT 1 FROM public.alembic_version);

-- Verificación:
-- SELECT column_name FROM information_schema.columns WHERE table_name='organizaciones' AND column_name='es_test';
-- SELECT version_num FROM public.alembic_version;
