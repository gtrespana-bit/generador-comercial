-- CotizaT — actualización de m8e1f4a7b2c5 a n9f2a5b8c3d6
--
-- Fiscalidad estadounidense en el presupuesto: «sales tax» por estado con
-- modo de base imponible (Fase 2 de EE. UU.).
--
-- Tres columnas en `public.presupuestos` y las mismas en `public.facturas`:
--
--   * `estado_codigo`  — estado de la obra («TX», «NY»…). El impuesto sigue
--                        al lugar de la obra, así que vive en el documento.
--   * `us_tax_base`    — sobre qué cae el tipo: 'none' (no se cobra al
--                        cliente), 'materials', 'labor', 'full' o
--                        'gross_receipts'. Vacío = impuesto genérico.
--   * `us_tax_fraccion`— fracción de la base gravada en «gross_receipts»
--                        (Arizona «prime contracting»: 0.65). 1 = íntegra.
--
-- Más dos piezas:
--
--   * `facturas.us_base_gravada` — instantánea de la base gravada al
--     emitir, porque el reparto materiales/mano de obra se estima con los
--     costes del presupuesto y la factura no guarda costes. NULL en
--     documentos sin el motor estadounidense.
--   * `configuracion.empresa_estado_eeuu` — estado habitual de la empresa,
--     que el editor propone en cada presupuesto nuevo.
--
-- Nacen vacías (o a 1), así que ningún documento ya emitido cambia de
-- importe ni de aspecto: el bloque fiscal estadounidense solo actúa
-- cuando `us_tax_base` se rellena en el editor.
--
-- No se reutiliza `impuesto_pct`: ese sigue siendo el tipo —lo único que
-- el resto de mercados necesita— y convertir «8 % sobre materiales» en un
-- porcentaje menor sobre el total rompería en cuanto cambiara una
-- partida. Tampoco `retencion_pct`: esto no es una retención, es el
-- impuesto del documento.
--
-- Ejecutar una sola vez en el SQL Editor de Supabase con el rol
-- administrativo (nunca con `cotizat_runtime` ni con `cotizat_app`) y solo si
-- la versión actual es m8e1f4a7b2c5. Debe ejecutarse ANTES de desplegar
-- el código de la Fase 2: el runtime exige el nuevo head
-- (`EXPECTED_ALEMBIC_HEAD = n9f2a5b8c3d6`).

BEGIN;

DO $$
DECLARE
  v_version text;
BEGIN
  SELECT version_num INTO v_version FROM public.alembic_version LIMIT 1;
  IF v_version IS DISTINCT FROM 'm8e1f4a7b2c5' THEN
    RAISE EXCEPTION
      'Se esperaba alembic_version m8e1f4a7b2c5 antes de n9f2a5b8c3d6; se encontró %',
      COALESCE(v_version, '<vacío>');
  END IF;
END
$$;

ALTER TABLE public.presupuestos
  ADD COLUMN IF NOT EXISTS estado_codigo varchar(2) NOT NULL DEFAULT '',
  ADD COLUMN IF NOT EXISTS us_tax_base varchar(20) NOT NULL DEFAULT '',
  ADD COLUMN IF NOT EXISTS us_tax_fraccion double precision NOT NULL DEFAULT 1;

-- Descarta cualquier valor que el motor no conozca, para que ningún
-- documento pueda aplicar una regla que ningún estado tiene.
UPDATE public.presupuestos
SET us_tax_base = ''
WHERE us_tax_base NOT IN ('', 'none', 'materials', 'labor', 'full', 'gross_receipts');

UPDATE public.presupuestos
SET us_tax_fraccion = 1
WHERE us_tax_fraccion IS NULL OR us_tax_fraccion < 0 OR us_tax_fraccion > 1;

-- Documento de cobro: hereda estado/modo/fracción y congela la base gravada.
ALTER TABLE public.facturas
  ADD COLUMN IF NOT EXISTS estado_codigo varchar(2) NOT NULL DEFAULT '',
  ADD COLUMN IF NOT EXISTS us_tax_base varchar(20) NOT NULL DEFAULT '',
  ADD COLUMN IF NOT EXISTS us_tax_fraccion double precision NOT NULL DEFAULT 1,
  ADD COLUMN IF NOT EXISTS us_base_gravada double precision;

UPDATE public.facturas
SET us_tax_base = ''
WHERE us_tax_base NOT IN ('', 'none', 'materials', 'labor', 'full', 'gross_receipts');

UPDATE public.facturas
SET us_tax_fraccion = 1
WHERE us_tax_fraccion IS NULL OR us_tax_fraccion < 0 OR us_tax_fraccion > 1;

-- Estado habitual de la empresa (solo EE. UU.).
ALTER TABLE public.configuracion
  ADD COLUMN IF NOT EXISTS empresa_estado_eeuu varchar(2) NOT NULL DEFAULT '';

UPDATE public.alembic_version
SET version_num = 'n9f2a5b8c3d6'
WHERE version_num = 'm8e1f4a7b2c5';

COMMIT;

-- Verificación:
-- SELECT version_num FROM public.alembic_version;
--   → n9f2a5b8c3d6
-- SELECT table_name, column_name, data_type, column_default
--   FROM information_schema.columns
--  WHERE table_schema = 'public'
--    AND ((table_name IN ('presupuestos', 'facturas')
--          AND column_name IN ('estado_codigo', 'us_tax_base', 'us_tax_fraccion', 'us_base_gravada'))
--      OR (table_name = 'configuracion' AND column_name = 'empresa_estado_eeuu'))
--  ORDER BY table_name, column_name;
--   → 8 filas (3 en presupuestos, 4 en facturas, 1 en configuracion)
-- SELECT count(*) FROM public.presupuestos
--  WHERE us_tax_base NOT IN ('', 'none', 'materials', 'labor', 'full', 'gross_receipts');
--   → 0
-- Comprobación funcional (empresa con país Estados Unidos y estado habitual
-- Texas en Configuración): crear un presupuesto — el bloque «🇺🇸 Sales tax
-- por estado» propone Texas + «No cobrar al cliente» — y descargar el PDF
-- en inglés:
--   → la fila dice «Sales tax (TX 8.2 %) — not charged to the customer» a
--     0,00 USD, con la leyenda «No sales tax is charged on this contract…»
--     y el total sin el impuesto fantasma de antes.
