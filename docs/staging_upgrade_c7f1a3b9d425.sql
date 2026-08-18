-- CotizaT — actualización de d4e2f6a8b0c1 a c7f1a3b9d425
-- La compra guarda el período concedido, para que el propio comprador pueda
-- descargar su recibo en PDF sin leer `licencias` (reservada al operador).
-- Ejecutar una sola vez con el rol administrativo de Supabase/PostgreSQL.

BEGIN;

DO $$
DECLARE
  v_version text;
BEGIN
  SELECT version_num INTO v_version FROM public.alembic_version LIMIT 1;
  IF v_version IS DISTINCT FROM 'd4e2f6a8b0c1' THEN
    RAISE EXCEPTION
      'Se esperaba alembic_version d4e2f6a8b0c1 antes de c7f1a3b9d425; se encontró %',
      COALESCE(v_version, '<vacío>');
  END IF;
END
$$;

ALTER TABLE public.compras_plan
  ADD COLUMN IF NOT EXISTS licencia_inicio date,
  ADD COLUMN IF NOT EXISTS licencia_vence date;

-- Compras ya activadas antes de esta revisión: se recupera el período desde
-- la licencia enlazada, para que su recibo no salga sin fechas.
UPDATE public.compras_plan AS c
SET licencia_inicio = l.inicio,
    licencia_vence = l.vence
FROM public.licencias AS l
WHERE c.licencia_id = l.id
  AND c.licencia_inicio IS NULL;

UPDATE public.alembic_version
SET version_num = 'c7f1a3b9d425'
WHERE version_num = 'd4e2f6a8b0c1';

COMMIT;

-- Verificación:
-- SELECT version_num FROM public.alembic_version;
-- SELECT column_name FROM information_schema.columns
-- WHERE table_schema = 'public' AND table_name = 'compras_plan'
--   AND column_name IN ('licencia_inicio','licencia_vence');
-- SELECT id, estado, licencia_id, licencia_inicio, licencia_vence
-- FROM public.compras_plan ORDER BY id;
