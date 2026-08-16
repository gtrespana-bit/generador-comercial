# Dominio propio: cotizat.online (GoDaddy) → Vercel + Resend + Supabase

Guía operativa para llevar CotizaT a su dominio propio `cotizat.online`
(comprado en GoDaddy el 15/08/2026). Un solo dominio sirve para:

1. **Vercel** — la app deja de vivir solo en `cotizat-generador.vercel.app`.
2. **Resend** — los correos de invitación salen de `no-responder@cotizat.online`
   con verificación SPF/DKIM (entregabilidad real).
3. **Supabase** — Site URL y Redirect URL del nuevo dominio.

> ⚠️ **No cambies los nameservers de GoDaddy a Vercel.** Se mantienen los de
> GoDaddy y se añaden solo registros DNS, porque necesitamos el mismo panel
> para los registros de Resend (SPF/DKIM/MX). Cambiar nameservers rompería
> todo lo demás.

---

## Orden recomendado (evita ventanas rotas)

El dominio nuevo puede convivir con el de Vercel mientras propaga: no hay
corte. El orden evita configurar el correo antes de que la web esté arriba.

## Paso 1 — Vercel: dar de alta el dominio

1. Vercel → proyecto `cotizat-generador` → **Settings → Domains**.
2. **Add** → `cotizat.online` y también `www.cotizat.online`.
3. Vercel mostrará los registros esperados (quedarán en *pending* hasta que
   existan en DNS).

## Paso 2 — GoDaddy: apuntar el dominio a Vercel

En GoDaddy → My Products → `cotizat.online` → **DNS** (o *DNS Records*):

| Tipo | Nombre/Host | Valor | TTL |
| --- | --- | --- | --- |
| A | `@` | `76.76.21.21` | 1 hora / Auto |
| CNAME | `www` | `cname.vercel-dns.com` | 1 hora / Auto |

Antes de guardar:

- **Borra** los registros *parking* que GoDaddy crea por defecto (suele haber
  un A de `@` apuntando a IP de parking tipo `184.168.x.x` y a veces un CNAME
  de `www` a parking). Si quedan dos A para `@`, el tráfico se reparte al azar.
- No toques nada más. No cambies nameservers.

Propagación: de minutos a horas. Vercel valida solo y emite el certificado SSL
automáticamente (suele tardar 5–30 min tras validar).

## Paso 3 — Supabase: URLs del nuevo dominio

Supabase → **Authentication → URL Configuration**:

- **Site URL**: `https://cotizat.online`
- **Redirect URLs**: añadir **las dos** rutas a las que CotizaT manda
  redirigir tras los enlaces por email (GoTrue valida por coincidencia exacta,
  sin barra final ni `www`):
  - `https://cotizat.online/restablecer-clave` (recuperación de contraseña)
  - `https://cotizat.online/acceso` (confirmación de registro)
  (puedes dejar la antigua `https://cotizat-generador.vercel.app/restablecer-clave`
  durante la transición; los enlaces viejos de recuperación siguen funcionando).

Sin esto, el enlace de «restablecer clave» del email redirigiría a la pantalla
de login y parecería roto (`/readyz` publica la URL esperada en
`recovery_redirect_url_esperada` para compararla de un vistazo).

### Límite de correos de Auth (pantalla aparte)

El número de correos por hora **no** está en *URL Configuration* ni dentro de
*SMTP Settings*, sino en **Authentication → Rate Limits**
(`/project/<ref>/auth/rate-limits`). Con SMTP personalizado activo, sube
«Rate limit for sending emails» a **30/hora** y deja el intervalo mínimo entre
correos al mismo usuario en **60 s**. Sin SMTP propio el campo está bloqueado y
el techo son ~2 correos/hora en todo el proyecto.

Paso a paso en `docs/PENDIENTES_OPERATIVOS.md` §1.

## Paso 4 — Vercel: variable pública y despliegue

Project → **Settings → Environment Variables** (Production y Preview):

- `COTIZAT_PUBLIC_URL` → `https://cotizat.online`

Guarda y **redepliega** (un push cualquiera o *Redeploy* en el deployment
actual). Desde entonces `/readyz` debe responder en el dominio nuevo y
`recovery_redirect_url_esperada` debe coincidir con lo configurado en Supabase.

Canonical: se usa el apex (`https://cotizat.online`) como dirección oficial.
En Vercel → Domains, marca `cotizat.online` como principal; `www` redirige.

## Paso 5 — Resend: verificar el dominio para correo

1. [resend.com/domains](https://resend.com/domains) → **Add Domain** →
   `cotizat.online`.
2. Resend genera **registros DNS exactos** (SPF, DKIM y MX; opcionalmente
   DMARC). Copia los valores tal cual — cada cuenta genera claves distintas:
   - **MX** (rebotes): nombre `@` (o el que indique), valor tipo
     `feedback-smtp.us-east-1.amazonses.com`, prioridad 10.
   - **SPF** (TXT): nombre `@`, valor tipo
     `v=spf1 include:amazonses.com ~all`.
   - **DKIM** (TXT): nombre `resend._domainkey`, valor que empieza por `p=`.
   - **DMARC** (TXT, opcional): nombre `_dmarc`, `v=DMARC1; p=none;`.
3. Añádelos en GoDaddy → DNS (mismo panel del Paso 2; añadir, no borrar los
   de Vercel).
4. En Resend, pulsa **Verify** en el dominio. Estado `verified` = listo.

> Alternativa con mejor reputación aislada (opcional): verificar el subdominio
> `send.cotizat.online` en lugar del apex. El remitente pasaría a ser
> `no-responder@send.cotizat.online`. No es necesario para empezar.

## Paso 6 — Vercel: variables de correo y despliegue

Project → **Settings → Environment Variables** (Production y Preview):

| Clave | Valor |
| --- | --- |
| `RESEND_API_KEY` | `re_...` (API key de Resend, permiso *sending access*) |
| `COTIZAT_EMAIL_FROM` | `CotizaT <no-responder@cotizat.online>` |

Redeploy. Verificar en `https://cotizat.online/readyz`:

- `"email": "configurado"`
- `"rate_limit": "distribuido:upstash"` (se mantiene)
- `"recovery_redirect_url_esperada": "https://cotizat.online/restablecer-clave"`

## Paso 7 — Verificación final

1. `https://cotizat.online/healthz` y `/readyz` → 200.
2. `https://www.cotizat.online` → redirige a `https://cotizat.online`.
3. Crear una invitación en `/equipo` con un email real → debe llegar el correo
   desde `no-responder@cotizat.online` con el enlace.
4. Recuperación de contraseña → el email llega y el enlace aterriza en
   `https://cotizat.online/restablecer-clave`.
5. Los enlaces antiguos de `cotizat-generador.vercel.app` siguen funcionando
   (Vercel conserva el alias).

## Notas

- **`.online` y entregabilidad**: funciona sin problema para correo
  transaccional. Si más adelante se busca máxima confianza del filtro de spam,
  un `.com` pesa más; no es bloqueante.
- **Plan Hobby de Vercel**: el dominio propio no cambia el plan; el paso a Pro
  sigue siendo obligatorio antes de cobrar (uso comercial prohibido en Hobby).
- **No hay buzones en `cotizat.online`**: los correos que alguien envíe a
  `algo@cotizat.online` rebotarán (no hay MX de recepción). Si algún día se
  quiere un buzón (Google Workspace), se añade entonces y se consolida el SPF.
  - Comprobado el **16/08/2026**: el dominio raíz sigue **sin MX ni TXT**, y
    Resend está verificado sobre **`send.cotizat.online`** (SPF + MX hacia
    `feedback-smtp.eu-west-1.amazonses.com`) con el DKIM `resend._domainkey` en
    la raíz. Enviar funciona; **recibir no**, así que `soporte@cotizat.online`
    todavía rebota.
  - Al montar la recepción, **los MX nuevos van en la raíz `@`** (donde no hay
    nada, así que no se pisa el envío). **No tocar** los registros de
    `send.cotizat.online` ni el TXT `resend._domainkey`: sin ellos dejan de
    salir las invitaciones. Opciones y pasos en
    `docs/PENDIENTES_OPERATIVOS.md` §3.
