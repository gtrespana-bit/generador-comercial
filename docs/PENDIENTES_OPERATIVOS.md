# Pendientes operativos (paso por paso)

Fecha: **16/08/2026**. Tareas de paneles externos, sin código. Cada una es
independiente: se pueden hacer en cualquier orden.

Estado al escribir esta guía:

| # | Tarea | Estado |
| --- | --- | --- |
| 1 | Redirect URL `/acceso` + rate limit de emails en Supabase | **pendiente** |
| 2 | Pruebas E2E de Auth | ✅ **completado** (15/08/2026) |
| 3 | `soporte@cotizat.online` | **pendiente** (ver aviso: GoDaddy ya no lo da gratis) |
| 4 | Razón social → `COTIZAT_LEGAL_ENTITY` | **pendiente** (no urgente) |
| 5 | Vercel Hobby → Pro | **aplazado por decisión del usuario** |
| 6 | Panel de operador E1-060: migración `f4c1d8e37a95` + `COTIZAT_OPERADORES` | ✅ **completado** (16/08/2026): script `docs/staging_upgrade_f4c1d8e37a95.sql` aplicado en Supabase, variable en Vercel, panel verificado por el titular en `https://cotizat.online/admin/licencias` |

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

Como la variable no está definida, se muestra a propósito el marcador:

```
[RAZÓN SOCIAL DEL TITULAR — pendiente de registro]
```

Está hecho así **deliberadamente**: es preferible un hueco evidente a publicar
un contrato que parece completo y no dice quién lo firma.

### Qué poner

- **Si constituyes una empresa** → su razón social exacta y, si quieres, el
  RIF: `Inversiones Ejemplo, C.A. (J-XXXXXXXX-X)`.
- **Si operas como persona natural** (perfectamente válido para empezar) → tu
  nombre completo tal como aparece en tu documento de identidad.

Lo que **no** conviene: dejar el marcador cuando cobres al primer cliente. Los
términos son el contrato de servicio; sin titular identificado, quedan cojos.

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
