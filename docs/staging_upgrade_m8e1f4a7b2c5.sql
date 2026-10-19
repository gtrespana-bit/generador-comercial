-- CotizaT — actualización de l7d0e3f6a9c4 a m8e1f4a7b2c5
--
-- Fiscalidad irlandesa en el presupuesto: retención RCT (Relevant Contracts
-- Tax) e inversión del sujeto pasivo del IVA (VATCA 2010 s. 16(3)).
--
-- Una columna en `public.presupuestos`:
--
--   * `rct_tipo` — 0, 20 o 35, el tipo que Revenue asigna al subcontratista
--                  según su historial fiscal y confirma en la autorización
--                  de deducción de cada pago (ROS).
--                  NULL = el documento no está bajo RCT.
--
-- La misma columna va también a `public.facturas`: la retención se hereda
-- al convertir el presupuesto, porque es contra la factura contra lo que
-- Revenue autoriza la deducción.
--
-- Nace en NULL, así que ningún documento ya emitido cambia de importe ni de
-- aspecto: el bloque fiscal irlandés solo aparece cuando la columna se
-- rellena. Y NULL no es 0: «sin RCT» y «RCT al 0 % por historial limpio»
-- son situaciones distintas (con el 0 % sí hay contrato notificado y
-- autorización, solo que la retención sale a cero).
--
-- No hace falta columna nueva para la inversión del sujeto pasivo: reutiliza
-- `iva_tratamiento` de la migración británica (k6c9f2d5b8a3), porque la
-- pregunta —¿declara el cliente el IVA en vez de cargarse en factura?— es la
-- misma en los dos mercados. Lo que sí es propio es `rct_tipo`, y no se
-- reutiliza `cis_tipo`: el CIS retiene sobre la mano de obra (descuenta los
-- materiales de la base) y el RCT sobre el importe íntegro sin IVA,
-- materiales incluidos. Compartir columna invitaría a aplicar la base
-- contraria en Irlanda.
--
-- Ejecutar una sola vez en el SQL Editor de Supabase con el rol
-- administrativo (nunca con `cotizat_runtime` ni con `cotizat_app`) y solo si
-- la versión actual es l7d0e3f6a9c4.

BEGIN;

DO $$
DECLARE
  v_version text;
BEGIN
  SELECT version_num INTO v_version FROM public.alembic_version LIMIT 1;
  IF v_version IS DISTINCT FROM 'l7d0e3f6a9c4' THEN
    RAISE EXCEPTION
      'Se esperaba alembic_version l7d0e3f6a9c4 antes de m8e1f4a7b2c5; se encontró %',
      COALESCE(v_version, '<vacío>');
  END IF;
END
$$;

-- NULL a propósito: «sin RCT» y «RCT al 0 %» no deben confundirse en ROS.
ALTER TABLE public.presupuestos
  ADD COLUMN IF NOT EXISTS rct_tipo double precision;

-- Descarta cualquier tipo que Revenue no conozca, para que ningún documento
-- pueda mostrar una retención con un porcentaje inexistente.
UPDATE public.presupuestos
SET rct_tipo = NULL
WHERE rct_tipo IS NOT NULL AND rct_tipo NOT IN (0, 20, 35);

-- Documento de cobro: el que hereda la retención.
ALTER TABLE public.facturas
  ADD COLUMN IF NOT EXISTS rct_tipo double precision;

UPDATE public.facturas
SET rct_tipo = NULL
WHERE rct_tipo IS NOT NULL AND rct_tipo NOT IN (0, 20, 35);

UPDATE public.alembic_version
SET version_num = 'm8e1f4a7b2c5'
WHERE version_num = 'l7d0e3f6a9c4';

COMMIT;

-- Verificación:
-- SELECT version_num FROM public.alembic_version;
--   → m8e1f4a7b2c5
-- SELECT table_name, column_name, data_type, column_default
--   FROM information_schema.columns
--  WHERE table_schema = 'public' AND table_name IN ('presupuestos', 'facturas')
--    AND column_name = 'rct_tipo';
--   → presupuestos | rct_tipo | double precision | <null>
--   → facturas     | rct_tipo | double precision | <null>
-- SELECT count(*) FROM public.presupuestos
--  WHERE rct_tipo IS NOT NULL AND rct_tipo NOT IN (0, 20, 35);
--   → 0
-- SELECT count(*) FROM public.facturas
--  WHERE rct_tipo IS NOT NULL AND rct_tipo NOT IN (0, 20, 35);
--   → 0
-- Comprobación funcional (empresa con país Irlanda): abrir un presupuesto,
-- marcar RCT 20 % e inversión del sujeto pasivo en el bloque «🇮🇪 Fiscalidad
-- irlandesa» del editor y descargar el PDF en inglés:
--   → el IVA va a 0 con la leyenda «VAT on this supply to be accounted for
--     by the Principal Contractor» y aparece «RCT DEDUCTION (20.0 %)» sobre
--     el importe íntegro sin IVA.
