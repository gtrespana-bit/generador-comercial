# Pendientes operativos (paso por paso)

Fecha: **18/08/2026**. Actualizado: **20/08/2026** — las 10 tareas originales
están **completadas**. El cobro con Stripe (código) está listo; faltan claves
y el webhook en el panel (ver §14).

Estado al escribir esta guía:

| # | Tarea | Estado |
| --- | --- | --- |
| 1 | Redirect URL `/acceso` + rate limit de emails en Supabase | ✅ **completado** (16/08/2026, noche) |
| 2 | Pruebas E2E de Auth | ✅ **completado** (15/08/2026) |
| 3 | `soporte@cotizat.online` | ✅ **completado** (18/08/2026): buzón creado en **Zoho** y recibe correos. La app ya apunta a esa dirección; no requiere código |
| 4 | Razón social → `COTIZAT_LEGAL_ENTITY` | ✅ **resuelto provisionalmente** (18/08/2026): se muestra «CotizaT · Presupuestos» (marca operativa, sin identificador). Se completará con la entidad real cuando el titular la defina (ver §4) |
| 5 | Vercel Hobby → Pro | **aplazado por decisión del usuario** (lo indicará él) |
| 6 | Panel de operador E1-060: migración `f4c1d8e37a95` + `COTIZAT_OPERADORES` | ✅ **completado** (16/08/2026): script `docs/staging_upgrade_f4c1d8e37a95.sql` aplicado en Supabase, variable en Vercel, panel verificado por el titular en `https://cotizat.online/admin/licencias` |
| 7 | Migración `a3d9c1e75b28` (prueba gratuita) | ✅ **completado** (18/08/2026): `docs/staging_upgrade_a3d9c1e75b28.sql` aplicado en Supabase |
| 8 | **Activar `COTIZAT_EXIGIR_LICENCIA=true`** | ✅ **completado** (18/08/2026): PR #38 fusionado y desplegado; `COTIZAT_EXIGIR_LICENCIA=true` activado y verificado en `/readyz` (`"licencias": "exigida"`) |
| 9 | **`CRON_SECRET` + cron de recordatorios de vencimiento** | ✅ **completado** (18–19/08/2026): PR #40 fusionado (`c24c2cc`) y desplegado en producción; `CRON_SECRET` (Production) configurado; job verificado por el titular en Vercel (Settings → Cron Jobs: `/api/cron/recordatorios-vencimiento`, `0 13 * * *`); `/readyz` en vivo con `"cron_secret": "configurado"` y `"...:registrada"`. Primera ejecución automática: 19/08, 13:00 UTC (±59 min en Hobby). Detalle en §9 |
| 10 | **Emails de Supabase Auth (alta y recuperación) con el diseño de CotizaT** | ✅ **completado** (18–19/08/2026): plantillas pegadas en Supabase (Authentication → Email Templates): **Confirm signup**, **Reset password** y **Password changed**. Referencia: `docs/SUPABASE_EMAIL_TEMPLATES.md` y `docs/supabase_templates/` (ver §10) |
| 11 | **Operación automática (E4-021/E4-023) — parte de panel** | **código ✅** (19/08/2026: cron `/api/cron/mantenimiento`). **Falta en paneles:** `application/zip` en los MIME del bucket `cotizat-private`, vigilante externo de disponibilidad (p. ej. UptimeRobot sobre `/healthz`) y backups automáticos de Supabase Pro (ver §11) |
| 14 | **Stripe Checkout (tarjeta)** | **código ✅** (20/08/2026). **Falta en paneles:** cuenta Stripe ES, `STRIPE_SECRET_KEY` + `STRIPE_WEBHOOK_SECRET` en Vercel, endpoint `https://cotizat.online/pago/stripe/webhook`, migración `c3e9a1b7d4f2` en Supabase. Guía: `docs/STRIPE.md` |

---

## 1. Supabase: Redirect URL y límite de correos

Son **dos pantallas distintas**, y por eso no aparecía el ajuste del límite: no
está donde se configuran las URLs, sino en su propia página de *Rate Limits*.

### 1a. Redirect URLs (Authentication → URL Configuration)

Ruta directa: `supabase.com/dashboard/project/<tu-proyecto>/auth/url-configuration`

- **Site URL**: `https://cotizat.online`
- **Redirect URLs** — deben estar **estas dos**:
  - `https://cotizat.online/restablecer-clave` (recuperación de contraseña)
  - `https://cotizat.online/acceso` ← **la que falta** (confirmación de registro)

Pulsa **Add URL**, pega la ruta exacta y **Save**.

> GoTrue compara por **coincidencia exacta**: sin barra final, sin `www` y con
> `https`. Si no coincide, descarta el destino y manda el enlace al Site URL —
> que es justo el síntoma que viste («usuario o contraseña erróneo» tras
> confirmar: el email quedaba sin confirmar de verdad).

### 1b. Subir el límite de correos (Authentication → Rate Limits)

**Aquí es donde estaba escondido.** Es una página aparte, hermana de *URL
Configuration*, no un campo dentro de SMTP:

```
Dashboard → tu proyecto → Authentication → Rate Limits
```

Ruta directa: `supabase.com/dashboard/project/<tu-proyecto>/auth/rate-limits`

Busca la fila **«Rate limit for sending emails»** (número de correos por hora)
y súbela a **30**.

Detalles que importan:

- El campo **solo es editable con SMTP personalizado activo**. Como ya
  conectaste Resend, debería dejarte cambiarlo. Si aparece bloqueado, revisa
  que el SMTP siga activado en *Authentication → Emails → SMTP Settings*.
- Con SMTP propio, Supabase ya parte de 30/hora por defecto (en vez de los ~2
  del servicio integrado). Aun así conviene **dejarlo escrito en 30**, para que
  el valor sea explícito y no dependa de un defecto que puede cambiar.
- **No lo subas por encima de lo que aguante tu plan de Resend**: el gratuito
  son 100 correos/día. Si Supabase acepta más de lo que Resend entrega, los
  correos se pierden en el proveedor en vez de rechazarse a tiempo.

### 1c. Cooldown de 60 s (misma página)

En esa misma pantalla está el **intervalo mínimo entre correos al mismo
usuario** (`max_frequency`). Déjalo en **60 segundos**, que ya es el valor por
defecto. Es lo que evita que pulsar «reenviar» tres veces queme la cuota.

### Cómo comprobar que quedó bien

1. Registra una cuenta de prueba con un email tuyo.
2. Abre el enlace de confirmación → debe aterrizar en `/acceso` **y** permitir
   iniciar sesión (antes fallaba aquí).
3. Si algo falla, mira **Vercel → Logs** y busca la línea
   `Supabase Auth <método> <path> -> HTTP <código>: <cuerpo>`: dice la causa
   exacta sin exponerla al usuario.

---

## 3. `soporte@cotizat.online`

> **Aviso antes de empezar.** GoDaddy **retiró el reenvío de correo gratuito**
> que traían los dominios; hoy te empuja a contratar Microsoft 365 (unos
> 6-7 $/mes) aunque solo quieras redirigir una dirección. Merece la pena mirar
> la opción B antes de pagar.

Comprobación del DNS actual de `cotizat.online` (16/08/2026):

- El dominio raíz **no tiene registros MX** → hoy nadie puede recibir correo en
  `@cotizat.online`. Un mensaje a `soporte@` **rebota**.
- Resend está verificado sobre el subdominio **`send.cotizat.online`** (SPF +
  MX de `feedback-smtp.eu-west-1.amazonses.com`), y el DKIM `resend._domainkey`
  cuelga de la raíz. Eso es para **enviar**, no para recibir.

Es decir: **enviar ya funciona; recibir aún no**. Por eso `no-responder@` no
necesita buzón y `soporte@` sí.

### Opción A — GoDaddy (de pago)

`Mis productos → Email y Office → configurar` y crear el buzón
`soporte@cotizat.online`. Es lo más simple si no te importa el coste.

### Opción B — Reenvío gratuito con otro proveedor (recomendada)

Servicios como **forwardemail.net**, **ImprovMX** o **Cloudflare Email Routing**
reenvían gratis a tu correo real. Solo cambian registros DNS; el dominio sigue
en GoDaddy.

Pasos (ejemplo con Forward Email):

1. Alta en el servicio y añade el dominio `cotizat.online`.
2. En **GoDaddy → Mis productos → DNS de `cotizat.online`**, añade lo que
   indique. Con Forward Email son:

   | Tipo | Nombre | Prioridad | Valor |
   | --- | --- | --- | --- |
   | MX | `@` | 10 | `mx1.forwardemail.net` |
   | MX | `@` | 10 | `mx2.forwardemail.net` |
   | TXT | `@` | — | `forward-email=soporte:tu-correo-real@example.com` |

3. Verifica en el panel del servicio y **envía una prueba** a
   `soporte@cotizat.online` desde otra cuenta.

### Precauciones (importantes)

- **Los MX van en la raíz `@`, y no había ninguno**: no vas a pisar nada. Pero
  **no toques** los registros de `send.cotizat.online` ni el TXT
  `resend._domainkey`: son los que hacen que Resend pueda enviar. Si los borras,
  dejan de salir las invitaciones.
- Si el proveedor te pide **también** un SPF en la raíz (`@`), añádelo sin
  eliminar el de `send.`: son nombres distintos y conviven.

### Después

La dirección ya está publicada en la landing y en los legales, así que **no hay
que tocar código**. Si prefirieras otra dirección, existe la variable
`COTIZAT_SUPPORT_EMAIL` en Vercel para cambiarla sin desplegar código nuevo.

---

## 4. Qué es exactamente `COTIZAT_LEGAL_ENTITY`

Es **el nombre legal de quien opera CotizaT** — la persona o empresa que firma
los términos frente al cliente. No es el nombre comercial: «CotizaT» es la
marca; esto es *quién responde legalmente*.

### Dónde se ve

Se publica en tres sitios (`app/branding.py` la inyecta en las plantillas):

- `/legal/terminos` → «CotizaT es operado por **…**»
- `/legal/privacidad` → «El responsable del tratamiento es **…**»
- Pie de la landing → «© 2026 CotizaT · **…**»

### Qué se ve ahora

Decisión del titular (18/08/2026): la razón social real **no se publica** por
el momento. Como la variable no está definida, se muestra la marca operativa:

```
CotizaT · Presupuestos
```

Profesional y **sin número de identificación** de empresa. Es el valor por
omisión en `app/branding.py`; cuando el titular decida publicar una entidad
registrada, la escribe en `COTIZAT_LEGAL_ENTITY` y sustituye a este texto en
los tres sitios (términos, privacidad y pies).

### Qué poner (cuando se decida publicar la entidad)

- **Si usas la empresa española existente** → su denominación social exacta
  (la razón social tal como figura en el registro), sin inventar identificador.
- **Si operas como persona natural** → tu nombre completo tal como aparece en
  tu documento de identidad.

Lo que **no** conviene: cobrar al primer cliente sin que los términos
identifiquen a quién se paga. Los términos son el contrato de servicio; la
identidad mostrada debe poder sostenerse cuando empiece el cobro.

### Cómo añadirla (cuando la tengas decidida)

1. Vercel → proyecto → **Settings → Environment Variables**.
2. **Add New**: nombre `COTIZAT_LEGAL_ENTITY`, valor la razón social, entorno
   **Production** (y Preview si quieres verla en las vistas previas).
3. **Save** y **redeploy** (las variables se leen al arrancar).
4. Abre `/legal/terminos` y comprueba que el marcador desapareció.

> No es bloqueante para seguir desarrollando. Sí lo es **antes de cobrar**.

---

## 5. Vercel Hobby → Pro (aplazado)

Decisión tuya, y es razonable mientras no haya cobros. Queda anotado el motivo
para no perderlo de vista:

- El plan **Hobby prohíbe el uso comercial** en sus términos. Mientras CotizaT
  esté en desarrollo y sin clientes de pago, no hay problema.
- **El día que cobres al primer cliente**, hay que pasar a **Pro (20 $/mes)**.
  No es una optimización: es cumplir el contrato de la plataforma.

Nada de esto afecta al código ni al despliegue actual.

---

## 8. Activar el cobro: `COTIZAT_EXIGIR_LICENCIA=true`

Este es **el último paso del lanzamiento** y el único que convierte CotizaT en
un producto de pago. Hasta que se dé, todo el sistema de licencias existe y se
ve en el panel, pero **no corta el acceso a nadie**: la comprobación de vigencia
está desactivada por la variable.

### Antes de tocar nada: el orden importa

**Primero se despliega el PR #38, después se activa el interruptor.** No es una
preferencia, es una dependencia real:

- La **prueba gratuita de 7 días** viaja en ese PR. Es lo que cubre a las
  organizaciones recién registradas.
- Si activas el interruptor **sin** ese código desplegado, cada organización
  nueva nace sin licencia de ningún tipo y queda **suspendida desde el primer
  minuto**, antes incluso de ver el producto.

Con el PR desplegado, el registro concede la prueba automáticamente y el orden
deja de ser un problema.

### Lo que NO tienes que temer

**Tú no puedes quedarte fuera de tu propio panel.** El panel de operador
(`/admin/*`) cuelga de `get_operator_db`, que comprueba dos cosas —que estés
autenticado y que tu correo esté en `COTIZAT_OPERADORES`— y **no mira licencias
en ningún momento**. El corte por vigencia vive en `get_db`, que es la sesión
del uso normal del producto.

Dicho de otro modo: aunque tu organización apareciera suspendida, seguirías
entrando en `/admin/licencias` y podrías concederte una licencia de cortesía a
ti mismo. Da igual si lo haces antes o después de activar el interruptor.

### Los pasos

1. Comprueba que el PR #38 está **fusionado y desplegado** en producción.
2. Visita `https://cotizat.online/readyz` y confirma que dice
   `"alembic": "head:a3d9c1e75b28"`. Si dice otra cosa, la migración no está
   aplicada y **no debes continuar**.
3. Vercel → tu proyecto → **Settings → Environment Variables**.
4. Añade o edita `COTIZAT_EXIGIR_LICENCIA` con valor `true`, con el scope
   **Production** marcado. Se aceptan como verdaderos: `1`, `true`, `on`, `si`
   y `sí`; cualquier otra cosa se lee como falso.
5. **Redeploy.** Las variables de entorno no se aplican en caliente: si no
   redespliegas, no cambia nada.
6. Vuelve a `/readyz` y confirma que ahora dice `"licencias": "exigida"`. Si
   sigue diciendo `"no-exigida"`, el redeploy no cogió la variable.

### Cómo revertir, si algo va mal

Pon `COTIZAT_EXIGIR_LICENCIA=false` y vuelve a desplegar. **No borra ni modifica
ningún dato**: la variable solo decide si se comprueba la vigencia de la
licencia. Las licencias, las pruebas concedidas y las compras siguen
exactamente donde estaban, y al reactivar el interruptor todo vuelve a aplicarse
igual. Es una decisión reversible en dos minutos, no un punto de no retorno.

### Qué verán los clientes al vencer

No se quedan encerrados. De las rutas de la aplicación, **144 se cortan y 44
siguen accesibles**, elegidas a propósito para que un cliente vencido pueda
pagar y recuperarse solo: todo `/pago/*`, `/acceso`, el registro, la
recuperación de contraseña, `/cuenta`, `/organizaciones`, las invitaciones, las
páginas legales, `/conocer` y las propuestas públicas que ya hubiera enviado.
Lo que se corta es generar trabajo nuevo. Sus datos siguen ahí, que es
justamente lo que promete el texto público.

---

## 9. Activar el recordatorio automático de vencimiento (cron)

> **✅ COMPLETADO (18–19/08/2026).** El PR #40 se fusionó (`c24c2cc`) y el
> despliegue de **producción** contiene el `vercel.json` con el cron.
> `CRON_SECRET` está añadida en Vercel (Production) y el job **aparece en el
> panel** (Settings → Cron Jobs: `/api/cron/recordatorios-vencimiento`,
> `0 13 * * *`). `/readyz` lo confirma en vivo: `"cron_secret": "configurado"`
> y `"cron": "/api/cron/recordatorios-vencimiento:registrada"`. La primera
> ejecución automática ocurre el **19/08 a las 13:00 UTC** (en Hobby, hasta
> ±59 min más tarde) y quedará visible en Observability → Cron Jobs.
> El resto de esta sección queda como registro de lo hecho y checklist de
> diagnóstico si algún día vuelve a fallar.

El recordatorio por email que avisa a 5 y 1 días del vencimiento **solo se
envía si Vercel puede dispararlo**. Es un cron declarado en `vercel.json`
(`/api/cron/recordatorios-vencimiento`, diario a las 13:00 UTC) y Vercel
autentica cada invocación con `Authorization: Bearer $CRON_SECRET`.

### Los pasos (✅ completados el 18–19/08/2026)

1. ✅ Se generó un secreto fuerte (`openssl rand -base64 32`).
2. ✅ `CRON_SECRET` añadida en Vercel → **Settings → Environment Variables** →
   **Add New**: nombre `CRON_SECRET`, valor el secreto generado, entorno
   **Production**.
3. ✅ **Redeploy** hecho (las variables se leen al arrancar; y el cron se
   instala en el despliegue que contiene el `vercel.json` actualizado).
4. ✅ **Cron Jobs** verificado por el titular: aparece
   `recordatorios-vencimiento` (`/api/cron/recordatorios-vencimiento`,
   `0 13 * * *`).
5. ✅ Prueba manual opcional (sustituye el secreto):
   ```bash
   curl -H "Authorization: Bearer TU_SECRETO" \
        https://cotizat.online/api/cron/recordatorios-vencimiento
   ```
   Respuesta esperada: `{"ok": true, "resumen": {...}}`. Sin la cabecera o con
   un secreto incorrecto responde **401**. La primera ejecución automática se
   verá el 19/08 a las 13:00 UTC (±59 min en Hobby).

### Qué NO tienes que temer

- Sin `CRON_SECRET`, la ruta queda cerrada para todo el mundo (401) y Vercel
  no autentica la llamada: nada se envía, nada se rompe.
- El barrido es **idempotente**: cada hito (5 y 1 día) se envía una única vez
  por licencia, así que si Vercel repite una invocación no se duplica el correo.
- No toca datos de negocio: solo lee el vencimiento de las licencias y escribe
  una marca de «enviado» en la propia licencia.

### A qué correos llega

Al propietario y a los administradores activos de cada organización (los mismos
destinatarios que el aviso manual). El correo enlaza a `/pago` para renovar en
un clic y deja `Reply-To: soporte@cotizat.online`, de modo que responder llega
directamente al buzón de Zoho.

### Si el cron no aparece en Vercel (Cron Jobs vacío)

> ✅ **Ya resuelto (19/08/2026): el cron aparece en el panel.** Este checklist
> queda como referencia de diagnóstico por si volviera a pasar.

El cron **no se crea desde el panel**: Vercel lo crea al desplegar, leyendo
`vercel.json` de la raíz del repositorio, y **solo para despliegues de
producción** (un Preview nunca muestra crones). Comprueba en este orden:

1. **¿El despliegue en producción es el que contiene el `vercel.json`?**
   Vercel → tu proyecto → **Deployments**. El que tenga la etiqueta
   *Production* debe ser posterior a la fusión del PR #39 y mostrar el commit
   `455f3fc`. Si solo has desplegado la rama del PR (Preview), el cron no
   existe: fusiona a `main` (o a la rama de producción) y espera el redeploy.
2. **¿El proyecto de Vercel tiene la Root Directory correcta?** Settings →
   General → Root Directory debe ser `/` (o la carpeta que contenga
   `vercel.json`). Si apunta a otra carpeta, Vercel nunca lee el `vercel.json`
   de la raíz.
3. **¿Está `CRON_SECRET` definida?** Settings → Environment Variables →
   `CRON_SECRET` (Production), valor fuerte. Sin ella el cron puede aparecer
   pero cada invocación responde 401. **Redeploy** después de guardarla.
4. **Comprueba desde la propia app** (no requiere entrar al panel):
   ```bash
   curl -s https://cotizat.online/readyz | python -m json.tool
   ```
   En `checks` verás `cron_secret` (`configurado`/`no-configurado`) y `cron`
   (p. ej. `...:registrada`). Si dice `no-configurado`, el problema es la
   variable de entorno, no el código.
5. **Prueba manual de la ruta** (debe responder 401 sin el secreto, 200 con él):
   ```bash
   curl -i https://cotizat.online/api/cron/recordatorios-vencimiento
   curl -i -H "Authorization: Bearer TU_SECRETO" \
        https://cotizat.online/api/cron/recordatorios-vencimiento
   ```
   Si responde 404, la ruta no está en el despliegue: es un despliegue antiguo.

La suite de CI (`tests/test_vercel_cron_config.py`) verifica además que la ruta
declarada en `vercel.json` sigue existiendo en la aplicación; un cron huérfano
no puede llegar a producción en silencio.

---

## 10. Emails de Supabase Auth (alta y recuperación) — ✅ completado (19/08/2026)

Además de los 8 correos transaccionales que envía CotizaT (ya unificados bajo
el mismo diseño premium, revisables en `/admin/emails`), hay **dos correos que
los envía Supabase directamente**: la **confirmación de alta** (el enlace que
verifica el email al registrarse) y la **recuperación de contraseña**. No son
plantillas de CotizaT: son las plantillas propias de Supabase Auth.

### Recomendación: mantenerlos en Supabase

Sí, déjalos donde están. Son correos del ciclo de vida de la autenticación:
Supabase genera el enlace firmado con el token, y recrearlos en CotizaT
significaría reimplementar la generación de tokens y acoplar la app a algo que
Supabase ya hace bien. No hay beneficio y sí riesgo real de romper el alta o la
recuperación.

El remitente `noreply@` es correcto para estos dos: son correos de un solo uso
que no deben responderse.

### Qué hay del diseño — ✅ hecho (18–19/08/2026)

Las plantillas de Supabase Auth ya **no** usan la genérica por defecto: se
pegaron en el panel las versiones con la identidad de CotizaT. Son tres:

| Plantilla | Cuándo se envía | Archivo de referencia |
| --- | --- | --- |
| **Confirm signup** | Al registrarse, para verificar el email | `docs/supabase_templates/confirm_signup.html` |
| **Reset password** | Al pedir restablecer la contraseña | `docs/supabase_templates/reset_password.html` |
| **Password changed** *(seguridad, opcional)* | Tras cambiar la contraseña | `docs/supabase_templates/password_changed.html` |

Dónde: `Supabase → Authentication → Email Templates`. Los placeholders de
Supabase (`{{ .ConfirmationURL }}`, `{{ .SiteURL }}`, `{{ .Token }}`,
`{{ .Email }}`, `{{ .Data }}`) se conservaron tal cual; **no reescribirlos** si
alguna vez se vuelve a pegar el HTML. Guía paso a paso y mantenimiento:
`docs/SUPABASE_EMAIL_TEMPLATES.md`.

Esto es configuración de panel, **no código del repositorio**: los archivos
`.html` de `docs/supabase_templates/` son solo la referencia para copiar y
deben mantenerse en sintonía con `app/templates/emails/_base.html` si el
diseño base cambia.

---

## 11. Mantenimiento automático (E4-021/E4-023): lo que toca en el panel

El **código** está hecho (cron `/api/cron/mantenimiento`: respaldo automático
por organización + verificación diaria de `/readyz` con alerta por correo a
los operadores). Pasos para dejarlo operativo del todo:

0. **Fusionar el PR del bloque y desplegar** (el cron se instala en el
   despliegue de producción; `CRON_SECRET` ya está configurado).
1. **Bucket `cotizat-private`: NO hay que tocar nada (decisión 19/08/2026).**
   Se dejó **sin** restricción MIME; la app ya valida tamaño/categorías/claves
   y el respaldo automático sube los `.zip` sin problema. Solo si algún día se
   activara «Restrict MIME types», la lista debe incluir `application/zip`.
2. **Sincronizar el flujo de CI (tras fusionar).** El PR actualiza
   `docs/ci/ci.yml` (definición canónica) pero el token del bot no puede tocar
   `.github/workflows/ci.yml` (permiso `workflows`). Ejecutar tras el merge:
   ```bash
   cp docs/ci/ci.yml .github/workflows/ci.yml
   git add .github/workflows/ci.yml
   git commit -m "ci: sincroniza la copia activa con docs/ci/ci.yml"
   git push
   ```
   Hasta entonces el flujo activo es el anterior (sin los pasos E4-030).
   Detalle en `docs/ci/README.md`.
3. **Vigilante externo de disponibilidad (E4-023).** Crea un monitor HTTP(S) en
   un servicio gratuito (p. ej. UptimeRobot) sobre
   `https://cotizat.online/healthz`, intervalo 5 min, alertas a tu buzón. La
   verificación diaria ve el estado una vez al día; el vigilante te entera de
   una caída en minutos. Pasos en `docs/MONITORIZACION_Y_DIAGNOSTICO.md` §6b.
4. **Backups de Supabase (capa de infraestructura, opcional recomendado).** El
   plan **Pro** de Supabase incluye backups automáticos diarios del proyecto
   (base + Storage). Al contratarlo (está pendiente junto con Vercel Hobby →
   Pro), verifica en Supabase → Database → Backups que están activos. El
   respaldo automático de la app (paso de código) sigue siendo útil: es
   portátil y restaurable desde la propia aplicación.

**Verificación rápida del código (sin entrar al panel):**

```bash
curl -i https://cotizat.online/api/cron/mantenimiento        # 401 sin el secreto
curl -i -H "Authorization: Bearer TU_SECRETO" \
     https://cotizat.online/api/cron/mantenimiento           # 200: {"ok":…, "respaldo":…, "verificacion":…}
```

---

## 12. Consentimiento de términos registrado (E4-038): aplicar la migración

El **código** está hecho (checkbox obligatorio en el registro, tabla
`consentimientos` con RLS de operador, funciones SECURITY DEFINER, marca
`usuarios.acepto_terminos_*` visible en `/cuenta`). Falta **aplicar la
migración a Supabase**, un paso de una vez:

1. Abrir `Supabase → SQL Editor → New query`.
2. Pegar el contenido de `docs/staging_upgrade_b6d9e4c2a8f1.sql` (generado con
   `alembic upgrade --sql`: incluye la guarda que comprueba que la base está
   en `a3d9c1e75b28` antes de aplicar, y actualiza `alembic_version`).
3. Ejecutar. Verificar tras el despliegue que `/readyz` sigue en verde
   (comprueba `EXPECTED_ALEMBIC_HEAD = b6d9e4c2a8f1`).

**Sin la migración aplicada, la app no arranca en PostgreSQL** (el runtime
exige la cabeza exacta). El orden seguro: primero este SQL, luego el despliegue
del PR que contiene el código.

**Simulacro de caída y recuperación (E4-043) y plan de incidentes (E4-032):**
documentos listos en `docs/SIMULACRO_CAIDA_Y_RECUPERACION.md` y
`docs/PLAN_DE_RESPUESTA_A_INCIDENTES.md`. Primera ejecución del simulacro
recomendada antes del día final de tests (D-019); el plan de incidentes se
revisa en ese simulacro.

## 13. Registro de auditoría (E4-026/E4-027): aplicar la migración

**Estado (19/08/2026):** ✅ código completo en la rama del bloque; ⚠️ la
migración `d2a7c9e4f1b3` queda **pendiente de aplicar en Supabase** al
fusionar su PR.

1. Supabase → SQL Editor → New query.
2. Pegar el contenido de `docs/staging_upgrade_d2a7c9e4f1b3.sql` (generado con
   `alembic upgrade --sql`: incluye la guarda que comprueba que la base está
   en `b6d9e4c2a8f1` antes de aplicar, y actualiza `alembic_version`).
3. Ejecutar con el rol administrativo (las funciones SECURITY DEFINER deben
   quedar con propietario administrativo, nunca `cotizat_app`).
4. Verificar tras el despliegue que `/readyz` está en verde
   (`EXPECTED_ALEMBIC_HEAD = d2a7c9e4f1b3`) y que
   `/configuracion/actividad` registra eventos al cambiar un estado.

Qué trae: la tabla inmutable `eventos_auditoria` (quién cambió precios,
estados, documentos, equipo y datos; sin GRANT de UPDATE/DELETE), la función
`registrar_evento_global` (eventos de sesión, lista cerrada) y la función de
baja **corregida**: ahora borra también `compras_plan` (sin esto, una
organización con compras registradas no puede darse de baja) y
`eventos_auditoria`.
