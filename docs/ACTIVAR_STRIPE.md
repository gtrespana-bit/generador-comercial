# Activar el cobro con Stripe (suscripciones) — paso a paso

Guía operativa para dejar el cobro con tarjeta funcionando de punta a punta.
El **código ya está implementado y probado** (ver `docs/COBRO_Y_LICENCIAS.md`
§6); lo que queda son pasos en **Stripe**, **Vercel** y **Supabase** que solo
tú puedes hacer porque exigen tus credenciales.

Resumen de qué se cobra: **suscripción recurrente** en **USD** — Plan anual
89 US$/año y Plan mensual 9,99 US$/mes. El cliente puede gestionar (cancelar,
cambiar tarjeta) desde Configuración → «Gestionar suscripción» (Customer
Portal de Stripe).

Duración estimada: **30–45 minutos**. Empieza en modo **test** y no pases a
producción hasta completar el último paso.

---

## 1. Crear los precios recurrentes en Stripe

Con la clave de test en el entorno, ejecuta desde el repo:

```bash
STRIPE_SECRET_KEY=sk_test_... python tools/crear_precios_stripe.py
```

Imprime los dos identificadores:

```
STRIPE_PRICE_ANUAL=price_...
STRIPE_PRICE_MENSUAL=price_...
```

Guárdalos. Alternativa sin terminal: Dashboard → **Catálogo de productos** →
crear producto «CotizaT» con dos precios recurrentes en USD (89,00/año y
9,99/mes) y copiar sus `price_...`.

✅ Correcto si tienes dos códigos `price_...` distintos (uno por plan).

## 2. Registrar el webhook

Dashboard → **Developers → Webhooks → Add endpoint**:

| Campo | Valor |
| --- | --- |
| Endpoint URL | `https://<tu-dominio>/api/stripe/webhook` |
| Events to send | los 5 de abajo |

Eventos que **deben** quedar marcados:

1. `checkout.session.completed`
2. `checkout.session.expired`
3. `invoice.paid`
4. `invoice.payment_failed`
5. `customer.subscription.deleted`

Al guardar, Stripe muestra el **Signing secret** (`whsec_...`). Cópialo: es
`STRIPE_WEBHOOK_SECRET`.

✅ Correcto si tienes un `whsec_...` y los 5 eventos marcados.

## 3. Configurar los reintentos de cobro (dunning)

Dashboard → **Billing** (Configuración de suscripciones) → reglas de reintento.
Define p. ej. **3 reintentos** (a 1, 3 y 7 días) antes de cancelar.

✅ Correcto si una tarjeta que falla no cancela la suscripción al primer intento.

## 4. (Recomendado) Correos de cobro y recuperación de clientes

Dashboard → **Billing → Customer emails**: activa los avisos de «tarjeta a
punto de vencer» y de pago fallido. Evita bajas sin intervención manual.

## 5. Variables de entorno en Vercel

Vercel → tu proyecto → **Settings → Environment Variables** → añadir las 4:

| Variable | Valor |
| --- | --- |
| `STRIPE_SECRET_KEY` | `sk_test_...` |
| `STRIPE_WEBHOOK_SECRET` | `whsec_...` del paso 2 |
| `STRIPE_PRICE_ANUAL` | `price_...` anual |
| `STRIPE_PRICE_MENSUAL` | `price_...` mensual |

Marca las dos primeras como **Sensitive** si Vercel lo ofrece. Redespliega.

✅ Correcto si el checkout (`/pago/comprar`) ya muestra **«Tarjeta (Stripe)»**.
Si no aparece, es que alguna variable falta o quedó mal escrita.

## 6. Aplicar la migración en Supabase

1. Supabase → **SQL Editor → New query**.
2. Pega **todo el contenido** de `docs/staging_upgrade_ab12cd34ef56.sql` y pulsa **Run**.
3. Comprueba:

   ```sql
   SELECT version_num FROM alembic_version;
   ```

   Debe devolver **`ab12cd34ef56`**.

✅ Correcto si `GET /readyz` responde `"ok": true` con
`"alembic": "head:ab12cd34ef56"`.

## 7. Probar el ciclo completo en modo test

```bash
stripe listen --forward-to localhost:8000/api/stripe/webhook
```

Luego, en la app (con las claves de test en el entorno local):

1. Entra a `/pago`, elige plan anual → «Tarjeta (Stripe)».
2. En la página de Stripe paga con la tarjeta de prueba `4242 4242 4242 4242`
   (cualquier CVC y fecha futura).
3. Vuelve a la app: el plan debe quedar **activo** automáticamente.
4. En **Configuración → Tu plan**: debe salir el recibo (PDF) y el botón
   **«Gestionar suscripción»** (abre el Customer Portal).

✅ Correcto si la licencia se activa sola (sin intervención del operador) y el
portal abre.

Para probar la **renovación** en test, crea una suscripción con período de un
día y reenvía el webhook (`invoice.paid`) — o espera al ciclo real.

## 8. Pasar a producción

1. Completar la activación de la cuenta Stripe (datos del negocio + cuenta
   bancaria de la entidad **española**).
2. Crear precios **de producción** (nuevos `price_...` en vivo) y actualizar
   `STRIPE_PRICE_ANUAL` / `STRIPE_PRICE_MENSUAL`.
3. Cambiar `STRIPE_SECRET_KEY` a `sk_live_...` y el webhook a `whsec_live...`.

⚠️ Todo se cobra en **USD**. Los métodos locales de Stripe (OXXO en México,
PSE en Colombia, Yape/Plin en Perú) exigen moneda local y quedan para una
fase 2.

---

## Resumen de variables (para copiar al panel)

```
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ANUAL=price_...
STRIPE_PRICE_MENSUAL=price_...
```

## Si algo falla

- **El checkout no muestra la tarjeta** → falta `STRIPE_SECRET_KEY` o algún
  `STRIPE_PRICE_*`; revisa el paso 5.
- **Se paga pero no se activa** → el webhook no llegó o no está configurado;
  revisa el paso 2 y el log de `/api/stripe/webhook` (responde `ok` solo con
  firma válida). La compra queda visible en `/admin/compras` con su
  `stripe_subscription_id`.
- **`/readyz` en 503** → la migración del paso 6 no está aplicada.
