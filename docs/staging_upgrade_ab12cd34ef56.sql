-- CotizaT — migración ab12cd34ef56: cobro con Stripe (suscripciones).
--
-- Añade a compras_plan las columnas del cobro con tarjeta y la suscripción
-- recurrente, amplía los CHECK (método 'stripe' y estado 'cancelada') y crea
-- los índices para las búsquedas del webhook.
--
-- Es idempotente (ADD COLUMN IF NOT EXISTS / CREATE INDEX IF NOT EXISTS):
-- puede re-ejecutarse sin daño.
-- Ejecutar una sola vez con el rol administrativo de Supabase si la base ya
-- está en a4c8e2f7b1d6 (SQL Editor → New query → pegar → Run). Aplica después
-- de docs/staging_upgrade_a4c8e2f7b1d6.sql.

BEGIN;

DO $$
DECLARE
  v_version text;
BEGIN
  SELECT version_num INTO v_version FROM public.alembic_version LIMIT 1;
  IF v_version IS DISTINCT FROM 'a4c8e2f7b1d6' THEN
    RAISE EXCEPTION
      'Se esperaba alembic_version a4c8e2f7b1d6 antes de ab12cd34ef56; se encontró %',
      COALESCE(v_version, '<vacío>');
  END IF;
END
$$;

ALTER TABLE public.compras_plan
  ADD COLUMN IF NOT EXISTS stripe_session_id varchar(200),
  ADD COLUMN IF NOT EXISTS stripe_payment_intent varchar(200),
  ADD COLUMN IF NOT EXISTS stripe_subscription_id varchar(200),
  ADD COLUMN IF NOT EXISTS stripe_customer_id varchar(200),
  ADD COLUMN IF NOT EXISTS pais_codigo varchar(2);

-- Método de pago: se añade 'stripe' a los canales manuales del piloto.
ALTER TABLE public.compras_plan DROP CONSTRAINT IF EXISTS ck_compra_metodo_valido;
ALTER TABLE public.compras_plan
  ADD CONSTRAINT ck_compra_metodo_valido
  CHECK (metodo_pago IN ('pago_movil', 'binance', 'kontigo', 'usdt', 'stripe'));

-- Estado: se añade 'cancelada' (suscripción dada de baja).
ALTER TABLE public.compras_plan DROP CONSTRAINT IF EXISTS ck_compra_estado_valido;
ALTER TABLE public.compras_plan
  ADD CONSTRAINT ck_compra_estado_valido
  CHECK (estado IN ('pendiente', 'activa', 'rechazada', 'cancelada'));

-- Búsquedas del webhook de Stripe (sesión y suscripción) sin seq-scan.
CREATE INDEX IF NOT EXISTS ix_compras_plan_stripe_session
  ON public.compras_plan (stripe_session_id);
CREATE INDEX IF NOT EXISTS ix_compras_plan_stripe_subscription
  ON public.compras_plan (stripe_subscription_id);

UPDATE public.alembic_version
SET version_num = 'ab12cd34ef56'
WHERE version_num = 'a4c8e2f7b1d6';

COMMIT;

-- Verificación:
-- SELECT version_num FROM public.alembic_version;  -- → ab12cd34ef56
-- SELECT column_name FROM information_schema.columns
-- WHERE table_schema = 'public' AND table_name = 'compras_plan'
--   AND column_name IN ('stripe_session_id','stripe_payment_intent',
--                       'stripe_subscription_id','stripe_customer_id','pais_codigo')
-- ORDER BY column_name;
-- SELECT indexname FROM pg_indexes
-- WHERE schemaname = 'public' AND tablename = 'compras_plan'
-- ORDER BY indexname;  -- → ix_compras_plan_stripe_session, ix_compras_plan_stripe_subscription
