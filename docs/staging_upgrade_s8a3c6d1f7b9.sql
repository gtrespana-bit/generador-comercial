-- CotizaT — actualización de r7f2b1d4e8a6 a s8a3c6d1f7b9
-- El ejemplo del alta deja de ser una maqueta y pasa a ser material de trabajo.
--
-- Contenido:
--   1. Columna presupuestos.es_ejemplo y clientes.es_ejemplo (BOOLEAN NOT
--      NULL DEFAULT FALSE). Dice de dónde salió un documento; NO cambia qué
--      cuenta como negocio (eso sigue siendo es_demo).
--   2. Marca como ejemplo los documentos que sembró el alta hasta hoy.
--
-- Medido en producción el 02/11/2026: 36 presupuestos de ejemplo sembrados y
-- ninguno convertido en presupuesto real; 33 de las 41 cuentas reales sin
-- haber creado nunca uno. El ejemplo se llamaba «de demostración», la guía
-- avisaba de que no contaba y «Duplicar» producía otra copia demo.
--
-- Uso (Supabase → SQL Editor → New query): pega TODO este archivo y pulsa Run.
-- Debe ejecutarse con una sesión administrativa/propietaria. No uses
-- DATABASE_URL del runtime para aplicar DDL.
-- Comprueba primero la versión con:
--   SELECT version_num FROM public.alembic_version;  -- debe ser r7f2b1d4e8a6
--
-- No borra ni reescribe ningún dato de negocio: añade dos columnas con valor
-- por omisión (no reescribe la tabla en PostgreSQL 11+) y pone a TRUE una
-- bandera en las filas que ya estaban marcadas como demo.
BEGIN;

ALTER TABLE public.presupuestos
  ADD COLUMN IF NOT EXISTS es_ejemplo BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE public.clientes
  ADD COLUMN IF NOT EXISTS es_ejemplo BOOLEAN NOT NULL DEFAULT FALSE;

-- Los documentos sembrados por `sembrar_demo` son los únicos que llevan
-- es_demo = TRUE, así que la marca es inequívoca.
UPDATE public.presupuestos SET es_ejemplo = TRUE WHERE es_demo IS TRUE;
UPDATE public.clientes    SET es_ejemplo = TRUE WHERE es_demo IS TRUE;

UPDATE public.alembic_version SET version_num='s8a3c6d1f7b9' WHERE alembic_version.version_num = 'r7f2b1d4e8a6';

COMMIT;

-- Verificar: SELECT version_num FROM public.alembic_version; debe devolver s8a3c6d1f7b9.
-- Y que la marca cayó solo en los ejemplos:
--   SELECT es_demo, es_ejemplo, count(*) FROM public.presupuestos GROUP BY 1,2;
-- Debe salir una fila (TRUE, TRUE, n) con los ejemplos y (FALSE, FALSE, m)
-- con el trabajo real. Cualquier otra combinación indica datos raros.
--
-- Revertir (si hiciera falta):
--   ALTER TABLE public.presupuestos DROP COLUMN es_ejemplo;
--   ALTER TABLE public.clientes    DROP COLUMN es_ejemplo;
--   UPDATE public.alembic_version SET version_num='r7f2b1d4e8a6'
--    WHERE alembic_version.version_num = 's8a3c6d1f7b9';
