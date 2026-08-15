# Punto exacto de continuación

Fecha de corte: **15/08/2026, noche** (America/Caracas).

Este documento existe para retomar el trabajo desde una conversación nueva sin
depender del historial del chat. Describe **dónde nos quedamos exactamente** y
**qué es lo siguiente**, en ese orden.

Léelo junto con `docs/CONTINUIDAD_STAGING_SUPABASE.md` (estado de staging y
matriz de aceptación) y `PLAN_DE_COMERCIALIZACION_Y_EVOLUCION_SAAS.md`
(secciones 1.3 y 11).

---

## 1. Lo último que se hizo: emails de invitación (código en `main` y verificado)

### Estado exacto (15/08/2026, noche)

El bloque completo de emails está **desplegado y verificado en producción**.
No rehacer ningún paso:

- **PR #19 fusionado en `main`** el 15/08/2026 (merge **`f686e80`**), con los
  commits de la rama `arena/01a00633-generador-comercial`:
  1. `282f9c7` — emails de invitación por Resend con degradación a enlace en
     pantalla (`app/services/email.py`, plantillas `app/templates/emails/`,
     cableado en `crear_invitacion_web`, `checks.email` en `/readyz`,
     12 pruebas en `tests/test_email_invitaciones.py`);
  2. `5679ceb` — docs: el dominio de Vercel no puede usarse en Resend;
  3. `6d99b7d` — docs: guía del dominio (`docs/DOMINIO_COTIZAT_ONLINE.md`).
- **Parte operativa completa** (hecha por el usuario el 15/08/2026): cuenta
  Resend, dominio `cotizat.online` verificado en Resend (SPF/DKIM/MX en
  GoDaddy), y en Vercel Production `RESEND_API_KEY` y
  `COTIZAT_EMAIL_FROM=CotizaT <no-responder@cotizat.online>`.
- **Verificado en producción** (`https://cotizat.online/readyz`, 200 OK):
  `"email": "configurado"`, `"rate_limit": "distribuido:upstash"`,
  `"recovery_redirect_url_esperada": "https://cotizat.online/restablecer-clave"`,
  `"ok": true`, `"errors": []`.
- Suite en verde: **262 passed, 5 skipped**.

Nota de historial: el commit `85e35ae` (solo docs de continuidad, escrito
2 minutos después del merge del PR #19) quedó fuera de `main` y su contenido
ya estaba desactualizado; este documento lo sustituye.

### Lo único pendiente del bloque: prueba E2E de invitaciones

La hará **el usuario por su cuenta** (decidido el 15/08/2026); no requiere
código:

1. Entrar en `https://cotizat.online/equipo` y crear una invitación real a un
   email al que el usuario tenga acceso.
2. Confirmar que llega el correo desde `no-responder@cotizat.online` con el
   enlace de invitación (revisar spam la primera vez).
3. Aceptar la invitación con una cuenta del mismo email y comprobar que se
   consume (un solo uso).
4. Si algo falla: el flujo degrada a enlace en pantalla (no se pierde la
   invitación); revisar el panel de Resend (pestaña Emails) para ver el error
   de entrega, y `docs/EMAILS_INVITACION.md` para el diagnóstico.

Hasta que esa prueba pase, el bloque se considera «desplegado, pendiente de
validación E2E».

---

## 2. Cerrado antes (no rehacer)

### Rate limiting distribuido (15/08/2026)

- **PR #18 fusionado** (merge `7940ce9`). Base Upstash creada y las tres
  variables en Vercel Production: `UPSTASH_REDIS_REST_URL`,
  `UPSTASH_REDIS_REST_TOKEN`, `COTIZAT_REQUIRE_DISTRIBUTED_RATELIMIT=true`.
- Verificado: `/readyz` responde `"rate_limit": "distribuido:upstash"`.
- Diagnóstico si cambiara: `memoria` = variables ausentes; `mal-configurado` =
  URL no https o token vacío.
- Consumo esperado: 2 comandos por intento de login, muy por debajo del plan
  gratuito de Upstash.

Decisiones de diseño de `app/ratelimit.py` que **no conviene reabrir sin
motivo** (razonadas en el docstring del módulo y en `docs/SEGURIDAD_WEB.md`):

- **API REST y no cliente Redis** (serverless no conserva sockets; `urllib`
  evita una dependencia de runtime, mismo patrón que `app/auth.py` y
  `app/storage.py`).
- **Ventana fija por tramo** (`now // ventana` en la clave), no deslizante:
  caduca sola y todo cabe en un viaje (`INCR` + `EXPIRE` en pipeline,
  timeout 3 s).
- **Si Upstash falla, degrada al contador local** (ni fail-open ni
  fail-closed).
- **La IP no viaja en claro**: clave
  `cotizat:rl:<sha256("ruta|ip")[:32]>:<índice>`.
- **Configuración incompleta no impide arrancar**: avisa en
  `checks.rate_limit`; solo `COTIZAT_REQUIRE_DISTRIBUTED_RATELIMIT=true` la
  convierte en error, y nunca bajo SQLite.

### Dominio propio `cotizat.online` (15/08/2026)

- Comprado en GoDaddy; Vercel sirve `cotizat.online` y `www.cotizat.online`
  (DNS: A `@` → `76.76.21.21`, CNAME `www` → `cname.vercel-dns.com`).
- Supabase: Site URL `https://cotizat.online` y Redirect URL
  `https://cotizat.online/restablecer-clave`.
- `COTIZAT_PUBLIC_URL=https://cotizat.online` en Vercel Production, redeploy
  hecho y confirmado en `/readyz`.
- El alias `https://cotizat-generador.vercel.app` sigue activo.
- Guía completa con valores DNS exactos: `docs/DOMINIO_COTIZAT_ONLINE.md`.
- Si el dominio «parpadea»: comprobar en GoDaddy que haya un único registro A
  `@` → `76.76.21.21` (sin el de parking).

---

## 3. Aparcado por decisión del usuario

**Puntos 13-manual y 14 de la matriz de aceptación.** Razón dada: esas pruebas
conviene hacerlas más al final, porque algo validado hoy puede romperse en
cualquiera de los pasos que aún quedan. **No pedir que se ejecuten** hasta que
el desarrollo esté cerrado.

- **13-manual:** pegar la URL pública del objeto Supabase en ventana privada y
  confirmar acceso denegado.
- **14:** sustituir temporalmente `DATABASE_URL` por un rol con
  `SUPERUSER`/`BYPASSRLS` y verificar que `/readyz` responde 503.

Guía operativa en `docs/MATRIZ_PASOS_MANUALES.md` (45-60 min).

---

## 4. Qué es lo siguiente

**E1-040 cerrado el 15/08/2026**: `tests/test_recorrido_critico.py` cubre
sobre HTTP el recorrido completo (instalación limpia → asistente → catálogo,
cliente y presupuesto reales → PDF → backup → pérdida → restauración), la
restauración de una base de versión anterior con re-migración automática, el
backup automático semanal sin duplicados y el rechazo de zips maliciosos
(zip slip). Cada prueba corre contra una instalación aislada mediante la
variable nueva `COTIZAT_DATA_DIR` (solo modo desarrollo; en el .exe se
ignora). Suite: **266 passed, 5 skipped**. El criterio «CI ejecuta las
pruebas y el recorrido crítico está cubierto» pasó a `[x]` en el plan.

**E1W-012 cerrado el 15/08/2026**: importación de instalaciones SQLite hacia
la web con `app/services/instalacion_sqlite.py` y el asistente de dos pasos
en `/configuracion/importar-instalacion` (analizar → resumen honesto →
confirmar con casilla explícita y SHA-256 verificado). No migra demos ni
configuración de empresa, limpia referencias a archivos locales avisando, no
duplica al reimportar y exige rol propietario/administrador. 12 pruebas en
`tests/test_instalacion_sqlite.py`. Suite: **278 passed, 5 skipped**. El
criterio «exportación y migración controlada desde SQLite» pasó a `[x]`.

Los siguientes bloques en orden recomendado:

1. **Paquete legal/comercial:** E1-018 (EULA), E1-019 (privacidad), E1-020
   (licencias de terceros), E1-050 (guía de inicio), E1-056 (landing).

Criterios de salida de Etapa 1 aún abiertos: primer PDF en <20 min por usuario
nuevo, catálogo con procedencia y precios fechados, guía + oferta + contrato +
soporte, tres pruebas de usabilidad externas.

---

## 5. Aviso de plan que conviene tener presente

El plan **Hobby de Vercel prohíbe el uso comercial**. En cuanto CotizaT tenga un
cliente que pague, hace falta **Pro (20 $/mes)**, con independencia del rate
limiting. Además, en Hobby, superar un límite **detiene** el recurso hasta que
se reinicie la ventana (no llega una factura sorpresa, pero sí una caída).

No es urgente con pilotos gratuitos. Sí debe estar en el plan antes de cobrar.

Al cerrar la matriz completa: retirar del `README.md` (línea 14) el aviso de
«todavía no debe publicarse».

---

## 6. Reglas invariables (no negociables)

Heredadas de `docs/CONTINUIDAD_STAGING_SUPABASE.md`:

- nunca configurar `MIGRATION_DATABASE_URL` en runtime;
- nunca usar una conexión `postgres`/administrativa como `DATABASE_URL`;
- nunca poner `service_role`/`sb_secret_` en variables públicas del frontend;
- nunca fijar `COTIZAT_REQUIRE_RLS_ROLE=false` como solución de despliegue;
- si staging falla, corregir el problema observado **sin relajar** CSRF, CSP,
  RLS, bucket privado ni la exigencia del rol limitado;
- usar solo datos ficticios en las pruebas de la matriz;
- toda dependencia nueva exige pin `==` en `requirements.txt` más
  `python tools/generar_lock.py`, o falla `tests/test_dependencias_bloqueadas.py`.

Nota operativa: el token de la app que abre cambios automáticos **carece del
permiso `workflows`**, así que GitHub rechaza pushes de archivos bajo
`.github/workflows/`. Por eso `docs/ci/ci.yml` existe como copia y el workflow
se instaló manualmente.

---

## 7. Mensaje para iniciar la conversación nueva

Copiar tal cual, sin añadir secretos ni tokens:

---

Continúa el proyecto CotizaT. Antes de proponer nada, lee
`docs/PUNTO_DE_CONTINUACION.md` y luego `docs/CONTINUIDAD_STAGING_SUPABASE.md`.
No repitas trabajo ya hecho y no me pidas secretos.

**Dónde quedó todo (15/08/2026, noche).**

- **Rate limiting distribuido: cerrado y verificado.** PR #18 fusionado (merge
  `7940ce9`), variables de Upstash en Vercel y `/readyz` responde
  `"rate_limit": "distribuido:upstash"`.
- **Dominio propio operativo:** `cotizat.online` (GoDaddy) sirviendo la app en
  Vercel; Supabase y `COTIZAT_PUBLIC_URL` apuntando al dominio nuevo.
- **Emails de invitación: código en `main` y desplegado.** PR #19 fusionado
  (merge `f686e80`), Resend configurado con dominio verificado,
  `RESEND_API_KEY` y `COTIZAT_EMAIL_FROM` en Vercel Production, y
  `https://cotizat.online/readyz` verificado con `"email": "configurado"` y
  `"ok": true`.
- **Único pendiente del bloque de emails: la prueba E2E**, que hago yo por mi
  cuenta (invitación real en `/equipo` → correo desde
  `no-responder@cotizat.online` → aceptarla y ver que se consume). Pregúntame
  si ya la hice; si llegó bien, el bloque queda cerrado del todo.

**Empieza por verificar el estado real, no te fíes de este resumen:**

1. `git log --oneline -5` y `git status --short` — ¿árbol limpio con el merge
   `f686e80` presente?
2. Recrea el entorno y corre la suite: `python3 -m venv .venv`,
   `.venv/bin/pip install -r requirements-dev.txt`, `.venv/bin/pytest -q`.
   Deben salir **262 passed, 5 skipped**.
3. Abre `https://cotizat.online/readyz` — debe estar en 200 con
   `"email": "configurado"` y `"rate_limit": "distribuido:upstash"`.

**Aparcado por decisión mía:** los puntos 13-manual y 14 de la matriz de
aceptación, hasta que el desarrollo esté cerrado. No pedirlos todavía.

**Siguientes bloques cuando cierre esto:** 1) E1-040 pruebas de recorridos
críticos; 2) E1W-012 importación de instalaciones SQLite hacia la web;
3) paquete legal/comercial (E1-018/019/020/050/056). Recordar: plan Hobby de
Vercel prohíbe uso comercial → pasar a Pro antes de cobrar.

---
