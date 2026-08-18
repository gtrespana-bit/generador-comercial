# Plantillas de email de Supabase (Auth) con el diseño de CotizaT

Los correos de **autenticación** (alta y recuperación de contraseña) los envía
**Supabase**, no CotizaT. Para que tengan el mismo diseño premium que el resto
de correos de la app, hay que pegar HTML propio en el panel de Supabase.

Esto es configuración de panel, **no código del repositorio**: los archivos
`.html` de `docs/supabase_templates/` son solo la referencia para copiar.

---

## Qué plantillas tocan a CotizaT

| Plantilla de Supabase | Cuándo se envía | Archivo de referencia |
| --- | --- | --- |
| **Confirm signup** | Al registrarse, para verificar el email (alta) | `docs/supabase_templates/confirm_signup.html` |
| **Reset password** | Al pedir recuperar/restablecer la contraseña | `docs/supabase_templates/reset_password.html` |
| **Password changed** *(notificación de seguridad, opcional)* | Después de que la contraseña cambie de verdad | `docs/supabase_templates/password_changed.html` |

### Aclaración sobre «cambio de contraseña»

Hay dos cosas distintas y conviene no confundirlas:

1. **Restablecer contraseña** (`Reset password`): es el correo con el **enlace**
   para elegir una nueva. Es lo que se llama coloquialmente «recuperar
   contraseña».
2. **Contraseña cambiada** (`Password changed`): es una **notificación de
   seguridad** que Supabase envía *después* de que la contraseña cambie, para
   avisar «si no has sido tú, haz algo». Es **opcional** y solo se envía si se
   activa la notificación en el proyecto.

CotizaT usa el flujo de enlace (no OTP), así que las plantillas de alta y
recuperación se apoyan solo en `{{ .ConfirmationURL }}`.

---

## Cómo pegarlas (paso a paso)

1. Supabase → tu proyecto → **Authentication → Email Templates**.
2. Selecciona la plantilla (p. ej. **Confirm signup**).
3. En el campo **Subject**, escribe el asunto:
   - Confirm signup → `Confirma tu email · CotizaT`
   - Reset password → `Restablece tu contraseña · CotizaT`
   - Password changed → `Tu contraseña ha cambiado · CotizaT`
4. En el campo **Body**, borra lo que haya y pega **el contenido completo** del
   archivo `.html` correspondiente.
5. **Save**.

> ⚠️ **No reescribas los placeholders.** `{{ .ConfirmationURL }}`, `{{ .Email }}`
> y `{{ .SiteURL }}` son variables de Supabase que generan el enlace con el
> token y el correo del usuario. Si los cambias, el enlace deja de funcionar y
> el alta o la recuperación se rompen.

---

## Sobre la notificación «Password changed»

Es una notificación de seguridad (categoría distinta en Supabase). Para que se
envíe, debe estar **activada a nivel de proyecto**:

`Supabase → Authentication → Security Notifications` (o equivalente), y activar
«Password changed». Si no está activada, CotizaT sigue funcionando: simplemente
el usuario no recibe el aviso «tu contraseña ha cambiado». Es una decisión de
producto; lo razonable es **activarla** por higiene de seguridad.

Los placeholders que usa el archivo `password_changed.html` son solo
`{{ .Email }}` (el correo del usuario) y un `mailto:` a soporte, así que es
robusto aunque Supabase exponga menos variables en esta categoría.

---

## Mantenimiento

Si el diseño base de los correos de CotizaT cambia
(`app/templates/emails/_base.html`), conviene actualizar estos tres archivos a
mano para que sigan en sintonía. No comparten plantilla (Supabase no entiende
Jinja), así que es una sincronización manual y deliberada.
