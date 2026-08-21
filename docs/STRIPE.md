# Stripe: cobro con tarjeta (E4-034)

Fecha: **20/08/2026**.

Stripe no cubre métodos locales de todos los países (Pago móvil, PSE, Yape,
Zelle). Lo que sí cubre, con una cuenta **española** del titular, es cobrar
con **tarjeta, Apple Pay y Google Pay** a clientes de casi todo el mundo, en
USD. Los métodos manuales de CotizaT se conservan para Venezuela y para quien
no tenga tarjeta internacional.

## Qué hace el código

1. En `/pago/comprar` aparece «Pagar con tarjeta» si `STRIPE_SECRET_KEY` está
   definida.
2. `POST /pago/stripe/checkout` crea una Checkout Session en modo
   **suscripción** (mes o año) y redirige a `checkout.stripe.com`.
3. Stripe avisa a `POST /pago/stripe/webhook` (`checkout.session.completed` e
   `invoice.paid`). La firma `Stripe-Signature` sustituye a la sesión. El
   webhook corre con marca de operador porque RLS solo deja UPDATE de
   `compras_plan` e INSERT de `licencias` al operador.
4. La compra pasa a `activa` y se concede la licencia. Las facturas siguientes
   de la suscripción encadenan una licencia nueva (renovación automática).
5. `/pago/stripe/exito` solo muestra el estado: no activa (la sesión del
   cliente no puede escribir licencias). Si el webhook tarda, recargar.

Un pago fallido **no borra datos**. El acceso dura hasta el vencimiento ya
pagado.

## Pasos en el panel de Stripe

1. Alta en [Stripe](https://dashboard.stripe.com/register?country=ES) con la
   entidad española (autónomo / sociedad). País de la cuenta: **España**.
2. Developers → API keys: copia `sk_test_…` (pruebas) y luego `sk_live_…`.
3. Developers → Webhooks → Add endpoint:
   - URL: `https://cotizat.online/pago/stripe/webhook`
   - Eventos: `checkout.session.completed`, `invoice.paid`,
     `invoice.payment_failed`, `customer.subscription.deleted`
   - Copia el `whsec_…`
4. Settings → Payment methods: deja **Cards** activas. Apple Pay y Google Pay
   salen en Checkout cuando el dominio está verificado
   (Settings → Apple Pay / Google Pay → `cotizat.online`).
5. En Vercel → Environment Variables (Production):
   - `STRIPE_SECRET_KEY=sk_live_…`
   - `STRIPE_WEBHOOK_SECRET=whsec_…`
6. Aplicar `docs/staging_upgrade_c3e9a1b7d4f2.sql` en Supabase **antes** del
   despliegue que contiene este código (`EXPECTED_ALEMBIC_HEAD = c3e9a1b7d4f2`).
7. Redeploy. `/readyz` debe mostrar `"stripe": "configurado"`.

Sin estas variables el botón de tarjeta no aparece: el cobro manual sigue
funcionando.

## Países y presentación del checkout

La tarjeta Stripe se ofrece internacionalmente cuando la clave está configurada.
Los métodos manuales sí se filtran por país: Venezuela ve Pago móvil, Binance,
Kontigo y USDT; el resto de países soportados ve solamente USDT. Las pantallas
`/pago` y `/pago/comprar` incluyen un selector de país y el servidor vuelve a
validar la disponibilidad del método manual antes de registrar la compra.

La matriz, la prioridad de selección de país, el diseño del bloque de Stripe y
el recorrido de renovación se documentan en
[`PAGOS_POR_PAIS.md`](PAGOS_POR_PAIS.md).

## Pruebas

Tarjetas de test de Stripe: `4242 4242 4242 4242`, cualquier fecha futura,
cualquier CVC. En modo test la clave es `sk_test_…` y el webhook se prueba con
`stripe listen --forward-to localhost:8000/pago/stripe/webhook` o con la
suite (`tests/test_stripe.py`).
