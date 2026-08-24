-- CotizaT — actualización de c0d1e2f3a4b5 a e4b8c2d6a190
-- Añade planos_obra.altura_libre_m (altura libre de paramentos, en metros).
--
-- Origen del incidente del 23/08/2026: el código con la columna nueva se
-- desplegó sin aplicar esta migración y cada apertura del visor de planos
-- respondía 500 con:
--   sqlalchemy.exc.ProgrammingError: (psycopg.errors.UndefinedColumn)
--   column planos_obra.altura_libre_m does not exist
--
-- Uso (Supabase → SQL Editor → New query): pega TODO este archivo y pulsa Run.
-- Debe ejecutarse con una sesión administrativa/propietaria. No uses la
-- DATABASE_URL del runtime para aplicar DDL.
-- Comprueba primero la versión con:
--   SELECT version_num FROM public.alembic_version;
--
-- Va dentro de una transacción: si algo falla, no se aplica a medias.

BEGIN;

DO $check$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM public.alembic_version
    WHERE version_num = 'c0d1e2f3a4b5'
  ) THEN
    RAISE EXCEPTION
      'Se esperaba alembic_version en c0d1e2f3a4b5 antes de aplicar e4b8c2d6a190';
  END IF;
END
$check$;

-- IF NOT EXISTS a propósito (no es el render literal de Alembic): la
-- auto-reparación best-effort del arranque puede haber creado ya la columna
-- si se lanzó con una URL con permisos DDL. Con la forma estricta el ALTER
-- fallaría con DuplicateColumn, la transacción haría rollback y la marca de
-- versión nunca avanzaría.
ALTER TABLE public.planos_obra
  ADD COLUMN IF NOT EXISTS altura_libre_m double precision;

UPDATE public.alembic_version
SET version_num = 'e4b8c2d6a190'
WHERE version_num = 'c0d1e2f3a4b5';

COMMIT;

-- Verificación: debe devolver e4b8c2d6a190
SELECT version_num FROM public.alembic_version;

-- Verificación: una fila con data_type = double precision, is_nullable = YES
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'planos_obra'
  AND column_name = 'altura_libre_m';

-- Verificación final: el visor de planos del presupuesto vuelve a abrir y
-- GET /readyz → {"ok": true, "alembic": "head:e4b8c2d6a190"}
-- (este último, tras desplegar el código con EXPECTED_ALEMBIC_HEAD actualizado).
