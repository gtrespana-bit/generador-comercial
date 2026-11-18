# Plantillas de email de Supabase (Auth) con el diseño de CotizaT

Los correos de **autenticación** (alta, cambio de email y recuperación de
contraseña) los envía **Supabase**, no CotizaT. Para que tengan el mismo diseño
premium que el resto de correos de la app, hay que pegar HTML propio en el panel
de Supabase.

Esto es configuración de panel, **no código del repositorio**: los archivos
`.html` de `docs/supabase_templates/` son solo la referencia para copiar.

---

## Regla de oro: el enlace nunca apunta a `*.supabase.co`

Los enlaces usan **el dominio propio**:

```
{{ .SiteURL }}/confirmar-email?token_hash={{ .TokenHash }}&type=<signup|recovery|email_change>
```

Motivo: Microsoft SafeLinks (Outlook/365) y el escáner de Gmail abren **todas**
las URLs de un correo antes de entregarlo. Con el enlace antiguo
(`{{ .ConfirmationURL }}`, que apunta a `<proyecto>.supabase.co/auth/v1/verify`)
ese «clic» del escáner **gasta el token de un solo uso** y, cuando la persona
pulsa de verdad, solo ve «enlace caducado». Además, un enlace `supabase.co`
dentro de un correo es una señal de phishing para muchos filtros.

Con el enlace propio, el GET de `/confirmar-email` solo pinta un botón (no habla
con Supabase y no consume nada) y el token se canjea en el **POST**, que solo
dispara una persona.

> ⚠️ **No cambies los placeholders.** `{{ .SiteURL }}`, `{{ .TokenHash }}`,
> `{{ .Email }}` y `{{ .Token }}` los rellena Supabase. Si los reescribes, el
> enlace deja de funcionar y el alta o la recuperación se rompen.
> `{{ .ConfirmationURL }}` **no debe aparecer** en ninguna plantilla: lleva al
> dominio de Supabase.

Requisito en el panel: `https://cotizat.online/confirmar-email` tiene que estar
en **Authentication → URL Configuration → Redirect URLs**, y
`https://cotizat.online` en **Site URL** (`{{ .SiteURL }}` sale de ahí).

---

## Qué plantillas tocan a CotizaT

| Plantilla de Supabase | Cuándo se envía | Archivo de referencia | Enlace |
| --- | --- | --- | --- |
| **Confirm signup** | Al registrarse, para verificar el email | `docs/supabase_templates/confirm_signup.html` | `type=signup` |
| **Reset password** | Al pedir recuperar/restablecer la contraseña | `docs/supabase_templates/reset_password.html` | `type=recovery` |
| **Change email** | Al cambiar el email de la cuenta | `docs/supabase_templates/email_change.html` | `type=email_change` |
| **Password changed** *(aviso de seguridad)* | Después de que la contraseña cambie | `docs/supabase_templates/password_changed.html` | sin enlace |

### Aclaración sobre «cambio de contraseña»

Hay dos cosas distintas y conviene no confundirlas:

1. **Restablecer contraseña** (`Reset password`): es el correo con el **enlace**
   para elegir una nueva. Es lo que se llama coloquialmente «recuperar
   contraseña».
2. **Contraseña cambiada** (`Password changed`): es una **notificación de
   seguridad** que Supabase envía *después* de que la contraseña cambie, para
   avisar «si no has sido tú, haz algo». Es **opcional** y solo se envía si se
   activa la notificación en el proyecto. No lleva enlace ni token: solo
   `{{ .Email }}` y un `mailto:` a soporte.

El **cambio de email** es un flujo de dos correos: el primero confirma la nueva
dirección y el segundo cierra el cambio. CotizaT responde al primer clic con un
mensaje en `/acceso` («revisa tu bandeja») y, al segundo, con la sesión abierta
en `/cuenta`.

---

## Cómo pegarlas (paso a paso)

1. Supabase → tu proyecto → **Authentication → Email Templates**.
2. Selecciona la plantilla (p. ej. **Confirm signup**).
3. En el campo **Subject**, escribe el asunto **en español**:
   - Confirm signup → `Confirma tu email · CotizaT`
   - Reset password → `Restablece tu contraseña · CotizaT`
   - Change email → `Confirma tu nuevo email · CotizaT`
   - Password changed → `Tu contraseña ha cambiado · CotizaT`
4. En el campo **Body**, borra lo que haya y pega **el contenido completo** del
   archivo `.html` correspondiente.
5. **Save**.

Asuntos breves, sin mayúsculas gritadas, sin signos de exclamación y sin
palabras de promoción: los filtros puntúan peor «¡GRATIS!» que «Confirma tu
email», y el asunto es la mitad de la decisión de abrir o marcar como spam.

---

## Remitente: `soporte@cotizat.online`

En **Authentication → SMTP / Email Settings** (con SMTP propio de Resend):

| Campo | Valor |
| --- | --- |
| Sender name | `CotizaT` |
| Sender email | `soporte@cotizat.online` |
| Reply-to | `soporte@cotizat.online` |

Un buzón con nombre y con respuesta real es una de las señales de
entregabilidad más baratas que existen: el mismo dominio sirve los correos
transaccionales de la app (`COTIZAT_EMAIL_FROM`) y los de Auth, así que el
receptor ve una sola identidad, con SPF, DKIM y DMARC alineados.

---

## Resend: antes de dar por buena la entregabilidad

1. **Dominio verificado** en Resend (`cotizat.online`) con los registros DNS que
   indique el panel (MX/SPF de envío y `resend._domainkey`).
2. **DKIM de 2048 bits.** En Resend → *Domains → cotizat.online → DKIM*, elige
   la clave de **2048 bits** y publica el `resend._domainkey` que genera. Con
   1024 bits algunos filtros restan puntuación; 2048 es el mínimo razonable hoy.
3. **Open Tracking y Click Tracking: DESACTIVADOS.** Reescriben los enlaces del
   correo (`click.resend.com`, píxel de apertura). En un correo transaccional de
   autenticación eso rompe el dominio propio del enlace —volvemos al problema de
   los escáneres—, ensucia la reputación de clics y hace que el `token_hash`
   pase por un tercero. `Resend → Domains → cotizat.online → Tracking`: ambos
   interruptores en **off**.
4. **DMARC.** Publica un registro TXT en `_dmarc.cotizat.online`:

   ```
   v=DMARC1; p=none; rua=mailto:soporte@cotizat.online; adkim=r; aspf=r; fo=1
   ```

   `p=none` mientras se vigilan los informes agregados (`rua`); cuando dos
   semanas seguidas muestren que todo el correo legítimo pasa SPF y DKIM, sube a
   `p=quarantine` y después a `p=reject`. Publicar `p=reject` el primer día, sin
   datos, es la forma más rápida de perder correo legítimo.
5. **Buzones de prueba**: envía un alta y una recuperación a una cuenta de
   Gmail, otra de Outlook y otra de Yahoo, y comprueba que el enlace del botón
   lleva a `https://cotizat.online/confirmar-email?...` y que el clic abre la
   sesión (o el formulario de contraseña nueva).

---

## Sobre la notificación «Password changed»

Es una notificación de seguridad (categoría distinta en Supabase). Para que se
envíe, debe estar **activada a nivel de proyecto**:

`Supabase → Authentication → Security Notifications` (o equivalente), y activar
«Password changed». Si no está activada, CotizaT sigue funcionando: simplemente
el usuario no recibe el aviso «tu contraseña ha cambiado». Es una decisión de
producto; lo razonable es **activarla** por higiene de seguridad.

---

## Mantenimiento

Si el diseño base de los correos de CotizaT cambia
(`app/templates/emails/_base.html`), conviene actualizar estos cuatro archivos a
mano para que sigan en sintonía: color sólido `#0b5b38`, borde `#dce6e1`, texto
de pie con contraste (`#566b61` / `#62776d`), preheader oculto y contacto
`soporte@cotizat.online`. No comparten plantilla (Supabase no entiende Jinja),
así que es una sincronización manual y deliberada.

`tests/test_entregabilidad_email.py` valida estos archivos: falla si aparece
`{{ .ConfirmationURL }}`, cualquier mención a `supabase.co`, `box-shadow` o
`linear-gradient`, o si un enlace no usa `{{ .SiteURL }}/confirmar-email`.
