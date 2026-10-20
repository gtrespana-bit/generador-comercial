# Avisos del negocio y botón de soporte (2026-10)

> Encargo del titular: el panel «tiene mucha información pero nada lógico ni
> fácil de usar», la primera venta se descubrió por un correo de Stripe (no por
> el producto), y los clientes necesitan una forma sencilla de escribir
> (quejas, dudas, ideas). Este documento describe lo que se implementó, dónde
> vive cada pieza y cómo verificarlo.

**Fecha:** 2026-10-15
**Head Alembic:** `j5b8e1c4a9f2` (RLS activo en `alembic_version`; el buzón entra en `i4d7c1b8e2f5`)
**SQL de aplicación manual:** `docs/staging_upgrade_i4d7c1b8e2f5.sql` (buzón) y
`docs/staging_upgrade_j5b8e1c4a9f2.sql` (head)

---

## 1. El problema, en tres huecos

| Hueco | Qué pasaba | Qué se hizo |
|---|---|---|
| **Venta invisible** | Stripe activaba la licencia por webhook y avisaba al **comprador**; al titular no le llegaba nada. La venta aparecía en el panel solo si uno entraba a buscar contratos. | Aviso de venta al buzón del titular + tarjeta «Últimas ventas» en *Hoy* + pestaña *Ingresos → Ventas* con CSV. |
| **Alta invisible** | El registro y la prueba no sonaban en ningún sitio: había que mirar la telemetría. | Aviso de alta (cuenta y empresa en prueba) al buzón del titular + tarjeta «Altas y pruebas» en *Hoy*. |
| **Soporte incómodo** | El único canal era escribir a `soporte@cotizat.online` desde el cliente de correo de cada uno. | Botón de soporte dentro de la aplicación y página pública `/soporte`: el mensaje se guarda, se avisa por correo y el panel lo gestiona. |

El destinatario de los tres avisos es el buzón de soporte
(`COTIZAT_SUPPORT_EMAIL`, por omisión `soporte@cotizat.online`) y se puede
desviar sin tocar el buzón que ven los clientes con `COTIZAT_AVISOS_EMAIL`.

---

## 2. Aviso de venta

**Cuándo sale**

- Webhook de Stripe (`checkout.session.completed` e `invoice.paid`) tras
  conceder la licencia: `app/routers/pagos.py` → `_avisar_venta_stripe`.
  La renovación se distingue del alta (`invoice.paid`), porque en el buzón no
  se lee igual «alta» que «renovación».
- Activación de un comprobante desde el panel: `app/routers/admin.py` →
  `_avisar_venta_manual`.

**Qué lleva** (plantilla `app/templates/emails/venta.{html,txt}`): plan, importe
con moneda, método de cobro, período concedido (inicio → vence), organización,
correo del comprador, número de compra y enlace al libro de ventas. El
`reply_to` es el comprador: responder al aviso contesta al cliente.

**Reglas**

- El correo **nunca** puede deshacer la venta: si Resend no está configurado o
  falla, se registra en el log y la licencia queda concedida igual
  (`app/services/avisos_negocio.py` envuelve todo).
- Se envía fuera del camino crítico cuando la ruta es asíncrona.

---

## 3. Aviso de alta

**Cuándo sale**

- Al crear la cuenta: `app/routers/auth.py` (`/registro`), en un hilo aparte
  para no sumar latencia al alta.
- Al crear la empresa: el mismo módulo, con el nombre de la organización y el
  texto de la prueba concedida (o «sin prueba», si esa identidad ya la gastó).

**Qué lleva** (plantilla `app/templates/emails/registro.{html,txt}`): nombre,
correo, país, origen (registro / prueba / empresa), organización y plazo de
prueba. `reply_to` es la persona que se registró.

---

## 4. Botón de soporte

**Para el cliente**

- Enlace **Soporte** en la barra lateral de la aplicación y botón flotante
  (`.soporte-flotante`) que convive con el lanzador del asistente y pasa
  `?desde=<pantalla>` para que el titular sepa dónde estaba la persona.
- Página `/soporte` con **dos marcos** sobre la misma URL (2026-10-20): sin
  sesión se sirve la página pública indexable (sitemap y SEO intactos); con
  sesión, la variante del panel (`soporte_panel*.html`, barra lateral y nombre
  y correo ya rellenos). Enlazar al cliente logueado a la página de marketing,
  con su botón de «Acceder», le hacía creer que había perdido la sesión.
- El formulario (idéntico en ambas): motivo (duda, problema, queja,
  sugerencia, facturación, otro), asunto y mensaje; muestra los plazos de
  respuesta.
- Antispam: límite de 5 envíos/5 min por IP (`app/security.py`
  `DEFAULT_LIMITS`) y campo trampa invisible.

**Para el titular**

- Pestaña *Clientes → Buzón de soporte*: contadores por estado (Sin atender,
  En proceso, Resuelto), filtros, búsqueda y acciones «Marcar en proceso»,
  «Marcar resuelto», «Reabrir» y nota interna.
- Cada acción queda auditada como `soporte.mensaje_estado`.
- El aviso por correo lleva `reply_to` del cliente: responder desde el buzón
  contesta directamente.

**Orden de garantías (corregido el 2026-10-20):** el correo de aviso se
intenta **primero** y su marca (`aviso_enviado`) viaja en la fila del propio
INSERT: si Resend falla, el mensaje se guarda igual y queda en el panel.
Antes el mensaje se guardaba, se avisaba y la marca se ponía con un UPDATE,
pero la política RLS de `mensajes_soporte` solo permite el INSERT público
(el UPDATE es del operador): **precisamente cuando el correo salía**,
PostgreSQL reducía el UPDATE a 0 filas, el ORM lanzaba `StaleDataError` y el
registro entero hacía rollback — el cliente veía «no hemos podido registrar
tu mensaje» y el mensaje no quedaba ni en el panel. Contratos fijados por
test: ningún UPDATE durante el registro y `/soporte` dentro de la aplicación
con sesión.

**Segunda vuelta (también 2026-10-20, tras desplegar lo anterior).** Con el
orden corregido el correo ya salía, pero el usuario *seguía* viendo el error
y el mensaje no quedaba en el panel: la RLS opone dos muros más al INSERT
público, invisibles en SQLite y reproducidos con PostgreSQL real
(`pgserver`). El flush del ORM emite `INSERT … RETURNING id`, y PostgreSQL
exige que la fila devuelta pase también la política SELECT — reservada al
operador—: «new row violates row-level security policy». Arreglo: el id se
pide antes a la secuencia (`nextval`, sin RLS) y el INSERT no devuelve nada.
Y como el handler lee `fila.id` tras el commit, el servicio expulsa la
instancia de la sesión antes de devolverla: con `expire_on_commit` esa
lectura dispararía un SELECT de refresco que la política reduce a cero
filas, con el mensaje ya guardado. Red de seguridad: tests que cuentan
sentencias (cero UPDATE y cero SQL al leer tras el commit) y
`tests/test_soporte_postgresql.py`, que ejercita el servicio contra un
PostgreSQL efímero con las políticas de la migración (se salta sin
`pgserver`).

**Destino de los avisos:** `COTIZAT_AVISOS_EMAIL` si está fijado; si no,
`soporte@cotizat.online`, que **aún no tiene buzón** (dominio sin registros
MX): hasta crear el buzón o fijar la variable en Vercel, los avisos rebotan
en silencio y solo queda rastro en el panel. `/readyz` publica
`avisos_destino` para comprobarlo sin entrar en Vercel.

---

## 5. Panel: lo que cambia en «Hoy»

- Bloque superior nuevo (`grid-lateral`): **Últimas ventas** (con marca
  «Nueva» para las últimas 48 h, plan, método, automática/manual, renovación) y
  columna lateral con **Altas y pruebas** y **Buzón de soporte**.
- La fila de KPIs empieza por **Ventas del mes** (importe y variación frente al
  mes anterior) y añade **Soporte sin atender**.
- La campana del panel (`/admin/notificaciones`) anuncia ventas, soporte sin
  atender y altas recientes además de lo que ya anunciaba.
- Pestaña nueva *Ingresos → Ventas*: KPIs (hoy, mes, ticket medio, acumulado,
  renovaciones), filtros por período/plan/cobro, búsqueda y CSV de lo que se ve.

---

## 6. Configuración

```bash
# Buzón de los avisos internos. Vacío = COTIZAT_SUPPORT_EMAIL
# (soporte@cotizat.online). Requiere RESEND_API_KEY y COTIZAT_EMAIL_FROM.
COTIZAT_AVISOS_EMAIL=
```

Los tres correos se pueden revisar desde el panel (*Sistema → Correos*) y desde
`tools/enviar_prueba_emails.py`, porque están en el registro
`app/services/correos_prueba.py`.

---

## 7. Despliegue

1. Aplicar `docs/staging_upgrade_i4d7c1b8e2f5.sql` en el SQL Editor de Supabase
   con el rol administrativo (el script aborta si la versión no es
   `h1c4b7e9a3d2` y confirma con `UPDATE public.alembic_version`).
2. Aplicar después `docs/staging_upgrade_j5b8e1c4a9f2.sql` (guardas para
   `i4d7c1b8e2f5`): reactiva RLS en `public.alembic_version` con lectura para
   `cotizat_app` y cierra el aviso crítico del asesor de Supabase. No cambia
   ninguna tabla funcional del buzón.
3. Comprobar `alembic_version` = `j5b8e1c4a9f2`.
4. Opcional: `COTIZAT_AVISOS_EMAIL` si los avisos no deben ir al buzón de
   soporte que ven los clientes.
5. Verificación de humo: enviar un mensaje desde `/soporte` y confirmar que
   aparece en *Clientes → Buzón de soporte* y que llega el correo.

## 8. Cómo verificarlo

```bash
.venv/bin/python -m pytest tests/test_avisos_y_soporte.py -q
.venv/bin/python -m pytest tests/test_stripe.py -q
```

Cubren: el aviso de venta del webhook y de la activación manual, el aviso de
alta por la ruta real de `/registro`, el formulario público (guardado, cebo,
validación), la bandeja del panel con su auditoría, los contadores, la campana,
«Hoy», el libro de ventas y su CSV.
