# Métodos de pago por país y renovación

Fecha de actualización: **21/08/2026**.

## Objetivo

La pantalla comercial no debe ofrecer al cliente medios que no puede usar. En
particular, Pago móvil y Kontigo son canales venezolanos: mostrarlos a una
empresa de México, Colombia o cualquier otro país reduce la confianza y genera
intentos de pago que no se pueden conciliar.

La política actual es deliberadamente conservadora: solo se publican medios de
cobro que están realmente habilitados.

## Matriz vigente

| País desde el que se pagará | Tarjeta Stripe | USDT (TRC-20) | Pago móvil | Binance | Kontigo |
| --- | :---: | :---: | :---: | :---: | :---: |
| Venezuela (`VE`) | Sí, si Stripe está configurado | Sí | Sí | Sí | Sí |
| Resto de países soportados | Sí, si Stripe está configurado | Sí | No | No | No |

Los países soportados proceden de `app/paises.py`. Por ahora, **México y
Colombia** muestran solamente tarjeta/Stripe y USDT. Cuando exista una cuenta,
enlace de cobro y proceso de conciliación operativo para un método local, se
podrá añadir a esta matriz.

> No anunciar Nequi, Daviplata, SPEI, Mercado Pago, Pix, Yape, Plin u otro
> método local hasta que exista un destino de cobro real y un procedimiento de
> verificación para él.

## Recorrido de la persona usuaria

### Página de planes: `GET /pago`

- Incluye el selector **«País desde el que pagarás»**.
- Muestra una tarjeta por cada método permitido para el país seleccionado.
- Los botones de plan transmiten el país mediante `?pais=<código>` a
  `/pago/elegir` y luego al checkout.
- Esta página se mantiene **pública y sin dependencia de organización**. Es
  esencial: una organización con licencia suspendida debe poder abrirla para
  renovar. En esta pantalla el país se resuelve en este orden:
  1. Parámetro `?pais=` válido.
  2. Cookie pública `cotizat_pais` (selector regional de la web).
  3. Venezuela, para compatibilidad si no hay preferencia.

### Checkout: `GET /pago/comprar?plan=…`

- Incluye el mismo selector y muestra el país activo junto a los métodos
  disponibles.
- Si no se proporcionó `?pais=`, toma el país configurado para la empresa en
  `Configuracion.empresa_pais`; admite tanto el código como el nombre almacenado
  en `app/paises.py`.
- Para organizaciones históricas sin país reconocible usa Venezuela como
  compatibilidad.
- Un cliente puede cambiar el selector si su organización está en un país pero
  realizará el pago desde otro. El campo oculto `pais_pago` acompaña al
  formulario manual.

### Validación de servidor

La ocultación visual no es un control de seguridad. `POST /pago/comprar` vuelve
a resolver y validar `pais_pago` y rechaza cualquier método manual que no esté
permitido por `_metodos_para_pais()` en `app/routers/pagos.py`. Por ejemplo, no
puede registrarse un Pago móvil para un pago declarado desde México alterando el
HTML del navegador.

Stripe no usa este formulario: su Checkout alojado se inicia en
`POST /pago/stripe/checkout` y es internacional según la disponibilidad de
Stripe y de la tarjeta del cliente.

## Diseño del bloque de Stripe

Cuando `STRIPE_SECRET_KEY` está configurada, el checkout presenta un bloque
integrado en lugar de un botón aislado:

- Jerarquía de «Pago inmediato» y destino explícito al checkout seguro de
  Stripe.
- Métodos admitidos visibles: Visa, Mastercard, American Express, Apple Pay y
  Google Pay.
- Botón de ancho completo con candado y el importe dinámico del plan.
- Nota de privacidad: los datos de tarjeta no pasan por los servidores de
  CotizaT.
- Estado «Abriendo pago seguro…» que deshabilita el envío duplicado mientras se
  redirige a Stripe.

La configuración operativa de Stripe, webhooks y variables de entorno está en
[`STRIPE.md`](STRIPE.md).

## Renovación de una licencia suspendida

`COTIZAT_EXIGIR_LICENCIA=true` bloquea las pantallas de negocio con una licencia
vencida, pero **no puede bloquear el camino para renovar**.

- La pantalla de suspensión enlaza a `/pago`.
- `/pago` no abre el contexto tenant ni verifica licencia; por ello el enlace
  siempre puede mostrar los planes.
- Las rutas privadas de compra usan `get_db_renovacion` en vez de `get_db`.
  Esta dependencia mantiene autenticación, membresía, organización y RLS, pero
  omite exclusivamente la comprobación de licencia vigente.
- No usar `get_db_renovacion` en rutas que expongan datos de negocio.

Las pruebas de regresión relacionadas están en
`tests/test_licencias_acceso.py`, especialmente el contrato que comprueba las
rutas privadas de compra.

## Operación y despliegue

1. Probar el selector en Venezuela y en al menos México o Colombia.
2. Probar un plan hasta `/pago/comprar` y verificar que el país se conserva.
3. Con una organización suspendida y el corte activado, pulsar **«Renovar mi
   plan»** y comprobar que llega a `/pago` y al checkout.
4. Con Stripe de pruebas configurado, iniciar Checkout y verificar la
   redirección; completar la validación de webhook según `STRIPE.md`.
5. Antes de habilitar un método local nuevo, actualizar simultáneamente:
   - `METODOS_PAGO` y la matriz de `_metodos_para_pais()`.
   - Los datos de destino y campos de comprobante/verificación.
   - Esta documentación y las pruebas de ruta/formulario.

Los commits de esta implementación se trabajaron en la rama de Arena. Para que
lleguen al despliegue de producción configurado sobre `main`, hay que integrar
la rama mediante el proceso habitual de pull request/merge y desplegar `main`.
El merge no es necesario para que el código sea correcto: solo determina qué
rama publica el proveedor de despliegue.
