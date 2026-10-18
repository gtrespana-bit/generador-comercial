# Stripe: cobro con tarjeta (E4-034)

Fecha de la guía original: **20/08/2026**.

> **Actualización 28/09/2026:** el código de esta rama exige Alembic
> `h1c4b7e9a3d2`; la guía original más abajo menciona el head histórico de
> Stripe (`c3e9a1b7d4f2`). No apliques ese SQL aislado sobre un esquema más
> reciente. Verifica primero el head remoto y usa
> [`APROVISIONAMIENTO_STAGING.md`](APROVISIONAMIENTO_STAGING.md) para migrar.
> El estado de las claves, webhook y cuenta Stripe de producción no se pudo
> verificar desde el repositorio.

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
   - URL: `https://www.cotizat.online/pago/stripe/webhook`
   - Eventos: `checkout.session.completed`, `invoice.paid`,
     `checkout.session.async_payment_succeeded`,
     `invoice.payment_failed`, `customer.subscription.deleted`
   - Copia el `whsec_…`
4. Settings → Payment methods: deja **Cards** activas. Apple Pay y Google Pay
   salen en Checkout cuando el dominio está verificado
   (Settings → Apple Pay / Google Pay → `cotizat.online`).
5. En Vercel → Environment Variables (Production):
   - `STRIPE_SECRET_KEY=sk_live_…`
   - `STRIPE_WEBHOOK_SECRET=whsec_…`
6. Llevar Supabase al head esperado por el despliegue (`h1c4b7e9a3d2` en esta
   rama) con el procedimiento de
   [`APROVISIONAMIENTO_STAGING.md`](APROVISIONAMIENTO_STAGING.md). La
   migración `c3e9a1b7d4f2` forma parte de la cadena histórica de Stripe; no la
   vuelvas a aplicar como paso aislado sobre una base más reciente.
7. Redeploy y comprobar que `/readyz` informa `"stripe": "configurado"`.

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


## Incidente 18/10/2026: 308 y eventos pendientes

### Diagnóstico confirmado por los registros aportados

Stripe enviaba a `https://cotizat.online/pago/stripe/webhook` y recibía **308**
a `https://www.cotizat.online/pago/stripe/webhook`. El evento no quedaba
entregado. Cobrar en Stripe y activar la licencia en CotizaT son pasos distintos.
Esta redirección no se arregla devolviendo 200 desde el código si la petición
no llega a la aplicación. No añadir un 200 ficticio ni desactivar la firma.

Además se corrigieron en el servicio:

- Lectura del formato moderno `invoice.parent.subscription_details` (API del
  ejemplo: `2026-07-29.dahlia`), manteniendo el formato anterior.
- Conservación de `invoice.id` para deduplicar facturas reenviadas.
- Respuesta 503 reintentable para cobros identificados como CotizaT que aún no
  tienen compra asociada; no se busca una empresa por email ni se concede una
  licencia solo por `organizacion_id` de metadata.
- Exclusión de Checkout `complete` pero `unpaid`; soporte al evento asíncrono
  de pago confirmado si se habilita ese método en el futuro.
- Serialización transaccional PostgreSQL por suscripción mediante advisory lock.
  Una factura y una sesión de la misma suscripción comparten el bloqueo.

### Recuperación operativa (requiere acceso a Stripe/Vercel y producción)

1. En Stripe, **modo activo**, editar el destino existente para usar exactamente
   `https://www.cotizat.online/pago/stripe/webhook` (sin barra final). No crear
   un segundo destino ni eliminar el actual mientras existan entregas pendientes.
2. Confirmar que ese host apunta al despliegue correcto y no tiene protección
   de acceso, reglas WAF o redirecciones sobre el POST del webhook. Un GET en
   el navegador no comprueba la entrega: la ruta solo admite POST.
3. Confirmar en Vercel Production que `STRIPE_SECRET_KEY` pertenece a la cuenta
   activa correcta y `STRIPE_WEBHOOK_SECRET` al **destino editado**. Revisarlos
   únicamente en los paneles seguros, nunca copiarlos al chat, logs o repositorio.
   Si se cambia un secreto/variable, redesplegar. No rotar claves sin necesidad.
4. Desplegar las correcciones del servicio antes de reenviar las facturas de
   formato moderno. Cambiar la URL por sí solo no corrige su procesamiento.
5. Para cada suscripción afectada, reenviar primero `checkout.session.completed`
   pagado y después `invoice.paid` inicial. Continuar con las facturas de
   renovación en orden cronológico. Si la factura llega primero, el nuevo 503
   pide reintento hasta que se pueda asociar a la compra.
6. Revisar la nueva entrega: debe devolver **200**, sin 3xx. Un 400 de firma
   requiere comprobar el secreto del destino; un 503 pide revisar configuración
   o asociación; un 500 requiere logs del despliegue. No insistir a ciegas.
7. Verificar en CotizaT que la compra, organización, plan y licencia son los
   correctos, y contrastar vencimientos y número de períodos con las facturas
   realmente pagadas. Un 200 por sí solo no demuestra la activación.
8. Reenviar otra vez el mismo evento y comprobar que no aumenta el número de
   compras/licencias ni el vencimiento. **Reenviar un evento no crea otro cobro**;
   no crear nuevas sesiones de Checkout para recuperar pagos ya realizados.
9. Revisar **todos** los eventos fallidos del destino, no solo los dos ejemplos.
   El correo aportado indica fin de reintentos el **24/10/2026 a las 15:48:28 UTC**.
   No esperar a ese plazo para recuperar las entregas y confirmar el acceso.

Los dos eventos del ejemplo corresponden a una misma suscripción y a la misma
factura inicial: **no son dos pagos distintos**. Hay que identificar también el
segundo cobro mencionado por el titular. Si el servicio antiguo llegó a duplicar
licencias, la corrección evita nuevas duplicaciones pero no borra automáticamente
licencias históricas: su conciliación requiere revisar cobros y acceso real.

### Alcance de la verificación

Las pruebas automatizadas cubren payloads sintéticos de formato antiguo y
moderno, firmas inválidas, factura antes de Checkout, reintentos de renovaciones,
Checkout impagado y respuesta HTTP reintentable. El bloqueo PostgreSQL se prueba
por la clave SQL compartida; la concurrencia real debe validarse en staging con
PostgreSQL. La suite local no verifica DNS, dominio canónico, Vercel, secretos ni
licencias reales de producción.
