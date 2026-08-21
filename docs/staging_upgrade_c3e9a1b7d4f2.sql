-- CotizaT — c3e9a1b7d4f2: cobro con Stripe (ids en compras_plan).
-- Añade las columnas de Stripe y admite el método ``stripe`` en el CHECK.

BEGIN;

DO $$
DECLARE
  v_version text;
BEGIN
  SELECT version_num INTO v_version FROM public.alembic_version LIMIT 1;
  IF v_version IS DISTINCT FROM 'a4c8e2f7b1d6' THEN
    RAISE EXCEPTION
      'Se esperaba alembic_version a4c8e2f7b1d6 antes de c3e9a1b7d4f2; se encontró %',
      COALESCE(v_version, '<vacío>');
  END IF;
END
$$;

ALTER TABLE public.compras_plan
  ADD COLUMN IF NOT EXISTS stripe_checkout_session_id varchar(255),
  ADD COLUMN IF NOT EXISTS stripe_subscription_id varchar(255),
  ADD COLUMN IF NOT EXISTS stripe_customer_id varchar(255),
  ADD COLUMN IF NOT EXISTS stripe_payment_intent_id varchar(255),
  ADD COLUMN IF NOT EXISTS stripe_invoice_id varchar(255);

CREATE INDEX IF NOT EXISTS ix_compras_plan_stripe_subscription
  ON public.compras_plan (stripe_subscription_id);

CREATE UNIQUE INDEX IF NOT EXISTS uq_compras_plan_stripe_session
  ON public.compras_plan (stripe_checkout_session_id);

CREATE UNIQUE INDEX IF NOT EXISTS uq_compras_plan_stripe_invoice
  ON public.compras_plan (stripe_invoice_id);

ALTER TABLE public.compras_plan DROP CONSTRAINT IF EXISTS ck_compra_metodo_valido;
ALTER TABLE public.compras_plan
  ADD CONSTRAINT ck_compra_metodo_valido
  CHECK (metodo_pago IN ('pago_movil', 'binance', 'kontigo', 'usdt', 'stripe'));

DROP POLICY IF EXISTS cotizat_compra_insert_operator ON public.compras_plan;
CREATE POLICY cotizat_compra_insert_operator ON public.compras_plan
  FOR INSERT TO cotizat_app
  WITH CHECK (
    COALESCE(
      pg_catalog.current_setting('cotizat.es_operador', true) = 'on',
      FALSE
    )
  );

UPDATE public.alembic_version
SET version_num = 'c3e9a1b7d4f2'
WHERE version_num = 'a4c8e2f7b1d6';

COMMIT;

-- Verificación:
-- SELECT version_num FROM public.alembic_version;  -- → c3e9a1b7d4f2
-- SELECT column_name FROM information_schema.columns
-- WHERE table_schema='public' AND table_name='compras_plan'
--   AND column_name LIKE 'stripe_%';
