# Envío de emails de invitación

Bloque «envío real de emails de invitación» (elegido tras el rate limiting
distribuido). Hasta ahora, al invitar a una persona, `/equipo` mostraba el
enlace **una sola vez** en pantalla y había que copiarlo a mano y enviarlo por
un canal externo. Con este bloque, el correo sale automáticamente por Resend y
el enlace en pantalla queda solo como respaldo.

## Cómo funciona

1. `/equipo/invitaciones` crea la invitación y la **guarda en la base primero**
   (el correo es un canal de entrega, no la fuente de verdad).
2. Si `RESEND_API_KEY` y `COTIZAT_EMAIL_FROM` están configuradas, se envía el
   correo con el enlace de un solo uso, el rol asignado y la fecha de
   caducidad (7 días).
3. Si **no** están configuradas, o el proveedor falla (timeout, 5xx, respuesta
   inesperada), el flujo **degrada sin romper**: la invitación sigue guardada
   y la pantalla muestra el enlace una vez, el comportamiento de siempre.

## Variables de entorno

| Clave | Valor | Notas |
| --- | --- | --- |
| `RESEND_API_KEY` | `re_...` | Clave de la API de Resend. **EXCLUSIVA del backend**, nunca en el frontend. Debe empezar por `re_`. |
| `COTIZAT_EMAIL_FROM` | `CotizaT <no-responder@tu-dominio.com>` | Dirección de un **dominio verificado** en Resend. Para probar sin dominio: `onboarding@resend.dev`, con la limitación de abajo. |

Sin las dos, el sistema funciona exactamente como antes (enlace en pantalla).

## ¿Puedo usar el dominio de Vercel? No

No se puede verificar `cotizat-generador.vercel.app` en Resend: ese subdominio
lo controla Vercel, no nosotros. Resend exige añadir registros DNS (SPF/DKIM)
en el proveedor del dominio, y eso solo puede hacerse sobre un dominio propio.
Un remitente como `no-responder@cotizat-generador.vercel.app` **rebotaría**.

Para probar **sin comprar dominio todavía** existe `onboarding@resend.dev`:
funciona al instante, pero **solo entrega correos al email con el que
registraste la cuenta de Resend**. Sirve para validar la integración de
extremo a extremo (crear una invitación dirigida a tu propio email y verla
llegar), no para invitar a un cliente real.

Para un piloto real se necesita un dominio propio. No es un requisito solo de
Resend: la aplicación tampoco debería quedarse en `*.vercel.app` para uso
comercial (ver el aviso del plan Hobby en `docs/PUNTO_DE_CONTINUACION.md`).
Un mismo dominio sirve para las tres cosas: dominio personalizado en Vercel,
verificación en Resend y (opcional) SMTP personalizado en Supabase para los
correos de Auth (confirmación de registro y recuperación de clave).

## Preparar Resend (una vez)

El dominio propio ya está comprado: **`cotizat.online` (GoDaddy)**. La guía
completa y ordenada (Vercel → Supabase → Resend → variables) está en
`docs/DOMINIO_COTIZAT_ONLINE.md`. Resumen del lado de Resend:

1. Crear cuenta en [resend.com](https://resend.com) (plan gratuito:
   100 correos/día, 3.000/mes; una invitación es un correo).
2. [resend.com/domains](https://resend.com/domains) → **Add Domain** →
   `cotizat.online`.
3. Copiar los registros DNS que muestra Resend (SPF, DKIM y MX) y añadirlos en
   GoDaddy → DNS. Pulsar **Verify** en Resend cuando estén propagados.
4. **API Keys → Create API Key** con permiso de envío (`sending access`).
   Copiar la clave `re_...`.
5. En Vercel → Project → Settings → Environment Variables (Production, y
   Preview si se quiere probar en previews): añadir las dos variables.
6. El despliegue siguiente las recoge. Verificar en `/readyz` que aparece
   `"email": "configurado"` (informativo: no hace fallar el readiness).

Sin dominio propio (solo prueba): `onboarding@resend.dev` como
`COTIZAT_EMAIL_FROM` — solo llegan correos al email de la cuenta de Resend.

## Verificación

- `/readyz` publica `checks.email`:
  - `configurado` → las dos variables están bien.
  - `no-configurado` → faltan las dos: todo sigue funcionando con enlace en
    pantalla.
  - `mal-configurado` → hay alguna variable pero inválida (clave sin `re_`,
    remitente mal formado, etc.).
- Prueba funcional: crear una invitación en `/equipo` con un email real y
  confirmar que llega el correo con el enlace; al aceptarlo con una cuenta del
  mismo email verificado, la invitación se consume.
- Prueba de degradación: quitar `RESEND_API_KEY` y repetir: la pantalla debe
  mostrar el enlace y el mensaje «No se pudo enviar el correo».

## Seguridad

- El token de la invitación viaja solo en el correo y en el enlace mostrado
  una vez en pantalla; en la base solo se guarda su SHA-256 (igual que antes).
- La clave `re_...` nunca llega al navegador.
- El correo incluye la organización, el rol y el invitador; quien no esperaba
  la invitación puede ignorarla: caduca sola y no se usa ningún dato suyo.
- Las plantillas de correo (`app/templates/emails/`) se excluyen de la
  verificación CSP de plantillas web a propósito: los clientes de correo
  descartan hojas externas y exigen estilos en línea (ver
  `tests/test_web_security.py`).

## Código

- `app/services/email.py` — configuración, cliente REST de Resend (urllib,
  sin dependencias nuevas) y `enviar_invitacion_por_email`.
- `app/templates/emails/invitacion.html` / `.txt` — plantillas del correo.
- `app/main.py` — cableado en `crear_invitacion_web` con degradación.
- `app/health.py` — chequeo informativo `checks.email` en `/readyz`.
- `tests/test_email_invitaciones.py` — 12 pruebas (configuración, payload,
  flujo web con correo, sin configuración, proveedor caído, readiness).
