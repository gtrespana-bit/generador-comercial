-- CotizaT — actualización de j5b8e1c4a9f2 a k6c9f2d5b8a3
--
-- Fiscalidad británica en el presupuesto: retención del CIS (Construction
-- Industry Scheme) e inversión del sujeto pasivo del IVA (VATA 1994 s. 55A).
--
-- Dos columnas en `public.presupuestos`:
--
--   * `iva_tratamiento`  — '' regla normal del país (IVA al cliente),
--                          'estandar' IVA confirmado,
--                          'inversion_sujeto_pasivo' el cliente declara el IVA.
--   * `cis_tipo`         — 0, 20 o 30, según el estado que Hacienda haya
--                          asignado al subcontratista al verificarlo.
--                          NULL = el documento no está bajo el CIS.
--
-- Las dos nacen en su valor neutro ('' y NULL), así que ningún presupuesto ya
-- emitido cambia de importe ni de aspecto: el bloque fiscal solo aparece
-- cuando se rellena una de las dos.
--
-- Las mismas dos columnas, más `coste_materiales`, van también a
-- `public.facturas`: la factura es el documento que se declara en el CIS300,
-- así que la retención tiene que constar en ella. El coste de materiales
-- viaja congelado porque `factura_items` no guarda costes y la factura no
-- puede recalcularse contra un presupuesto que puede seguir cambiando.
--
-- No se reutiliza `retencion_pct`: es un porcentaje comercial genérico que
-- solo se rotula en el PDF, mientras que el CIS es una retención legal que se
-- descuenta del importe a cobrar y se declara a Hacienda en el CIS300. Si se
-- hubieran compartido, un descuento comercial acabaría declarándose como
-- retención de Hacienda.
--
-- Ejecutar una sola vez en el SQL Editor de Supabase con el rol
-- administrativo (nunca con `cotizat_runtime` ni con `cotizat_app`) y solo si
-- la versión actual es j5b8e1c4a9f2.

BEGIN;

DO $$
DECLARE
  v_version text;
BEGIN
  SELECT version_num INTO v_version FROM public.alembic_version LIMIT 1;
  IF v_version IS DISTINCT FROM 'j5b8e1c4a9f2' THEN
    RAISE EXCEPTION
      'Se esperaba alembic_version j5b8e1c4a9f2 antes de k6c9f2d5b8a3; se encontró %',
      COALESCE(v_version, '<vacío>');
  END IF;
END
$$;

-- Cadena vacía y no NULL: los documentos anteriores a esta migración se
-- comportan igual que antes sin ningún CASE WHEN adicional en las consultas.
ALTER TABLE public.presupuestos
  ADD COLUMN IF NOT EXISTS iva_tratamiento varchar(30) DEFAULT '';

-- NULL a propósito: «sin CIS» y «CIS al 0 % con Gross Payment Status» son
-- situaciones distintas y no deben confundirse en el CIS300.
ALTER TABLE public.presupuestos
  ADD COLUMN IF NOT EXISTS cis_tipo double precision;

-- Normaliza los valores que hayan podido quedar a NULL por inserciones
-- anteriores a la migración (no debería haber ninguno, pero el NOT NULL
-- implícito del código lo da por hecho).
UPDATE public.presupuestos
SET iva_tratamiento = ''
WHERE iva_tratamiento IS NULL;

-- Descarta cualquier tipo de retención que no sea de los que admite Hacienda,
-- para que ningún documento pueda declarar un porcentaje inexistente.
UPDATE public.presupuestos
SET cis_tipo = NULL
WHERE cis_tipo IS NOT NULL AND cis_tipo NOT IN (0, 20, 30);

-- Documento de cobro: el que se declara en el CIS300.
ALTER TABLE public.facturas
  ADD COLUMN IF NOT EXISTS iva_tratamiento varchar(30) DEFAULT '';
ALTER TABLE public.facturas
  ADD COLUMN IF NOT EXISTS cis_tipo double precision;
ALTER TABLE public.facturas
  ADD COLUMN IF NOT EXISTS coste_materiales double precision DEFAULT 0;

UPDATE public.facturas
SET iva_tratamiento = ''
WHERE iva_tratamiento IS NULL;
UPDATE public.facturas
SET coste_materiales = 0
WHERE coste_materiales IS NULL;
UPDATE public.facturas
SET cis_tipo = NULL
WHERE cis_tipo IS NOT NULL AND cis_tipo NOT IN (0, 20, 30);

UPDATE public.alembic_version
SET version_num = 'k6c9f2d5b8a3'
WHERE version_num = 'j5b8e1c4a9f2';

COMMIT;

-- Verificación:
-- SELECT version_num FROM public.alembic_version;
--   → k6c9f2d5b8a3
-- SELECT column_name, data_type, column_default
--   FROM information_schema.columns
--  WHERE table_schema = 'public' AND table_name = 'presupuestos'
--    AND column_name IN ('iva_tratamiento', 'cis_tipo');
--   → iva_tratamiento | character varying | ''
--   → cis_tipo        | double precision  | <null>
-- SELECT count(*) FROM public.presupuestos
--  WHERE cis_tipo IS NOT NULL AND cis_tipo NOT IN (0, 20, 30);
--   → 0
-- SELECT count(*) FROM public.facturas
--  WHERE cis_tipo IS NOT NULL AND cis_tipo NOT IN (0, 20, 30);
--   → 0
