# Punto exacto de continuación

Fecha de corte: **15/08/2026** (America/Caracas).

Este documento existe para retomar el trabajo desde una conversación nueva sin
depender del historial del chat. Describe **dónde nos quedamos exactamente** y
**qué es lo siguiente**, en ese orden.

Léelo junto con `docs/CONTINUIDAD_STAGING_SUPABASE.md` (estado de staging y
matriz de aceptación) y `PLAN_DE_COMERCIALIZACION_Y_EVOLUCION_SAAS.md`
(secciones 1.3 y 11).

---

## 1. Lo último que se hizo: rate limiting distribuido

### El problema que se corrigió

`AuthRateLimitMiddleware` guardaba los intentos de acceso en un `dict` del
proceso. En un servidor único eso funciona; **en Vercel no**: cada invocación
puede ejecutarse en un proceso nuevo, así que el contador arrancaba vacío una y
otra vez. Los «10 intentos cada 5 minutos» de `/acceso` solo se aplicaban entre
peticiones que casualmente cayeran en la misma instancia caliente.

No era un límite laxo: era **un límite inexistente disfrazado de protección**.

### Qué se implementó

`app/ratelimit.py` (nuevo) separa la decisión («¿permito este intento?») de
dónde se guarda la cuenta, detrás de
`hit(identidad, límite, ventana) -> Decision`:

| Backend | Cuándo se usa | Comparte estado |
| --- | --- | --- |
| `MemoryRateLimit` | Escritorio, desarrollo y respaldo ante fallos | No |
| `UpstashRateLimit` | Con las dos variables `UPSTASH_REDIS_REST_*` | Sí |

Decisiones de diseño que **no conviene reabrir sin motivo** (están razonadas en
el docstring del módulo y en `docs/SEGURIDAD_WEB.md`):

- **API REST y no cliente Redis.** Una función serverless no conserva sockets
  entre invocaciones, así que la conexión persistente no aporta; usar `urllib`
  evita sumar una dependencia al runtime, con su pin en `requirements.txt` y la
  regeneración del lock. Mismo patrón que `app/auth.py` y `app/storage.py`.
- **Ventana fija por tramo** (`now // ventana` en la clave), no deslizante:
  caduca sola, renovar el TTL es idempotente y todo cabe en un solo viaje
  (`INCR` + `EXPIRE` en pipeline, timeout 3 s).
- **Si Upstash falla, degrada al contador local.** Ni fail-open (quitaría el
  límite justo cuando el servicio está en apuros) ni fail-closed (dejaría a
  todos fuera por una caída ajena).
- **La IP no viaja en claro** al tercero: la clave es
  `cotizat:rl:<sha256("ruta|ip")[:32]>:<índice>`.
- **Una configuración incompleta no impide arrancar**: avisa `/readyz` con
  `checks.rate_limit`. Solo `COTIZAT_REQUIRE_DISTRIBUTED_RATELIMIT=true` la
  convierte en error, y nunca bajo SQLite, donde un contador por proceso es lo
  correcto.

### Estado del código

- **PR #18** — <https://github.com/gtrespana-bit/generador-comercial/pull/18>
- Rama `arena/01a00341-generador-comercial`, commit **`c7d8be2`**, sobre la base
  `66f932f` (= merge del PR #17).
- **CI en verde**, Vercel Preview correcto, sin conflictos (`MERGEABLE`/`CLEAN`).
- Suite: **250 passed, 5 skipped** (antes del bloque eran 228).
- 14 archivos: `app/ratelimit.py` y `tests/test_ratelimit_distribuido.py`
  nuevos; el resto son el cableado en `app/security.py` y `app/health.py`, más
  documentación.

**Al fusionar el PR, producción despliega desde `main` y recoge las variables.**
*(Hecho: el merge `7940ce9` desplegó y `/readyz` confirma `distribuido:upstash`.)*

### Aviso: el check «Vercel» del último commit aparece en rojo

El segundo commit del PR (`becf758`, este mismo documento) **solo toca archivos
markdown** y aun así el check de Vercel quedó en `failure`, con la descripción
**«Deployment was blocked»**. El commit anterior, `c7d8be2`, que sí tocaba
código, desplegó correctamente («Deployment has completed»).

«Blocked» significa que Vercel **ni siquiera empezó a construir**: no es un
fallo de compilación ni de las pruebas. `vercel.json` no cambió y no hay
`ignoreCommand` ni `.vercelignore`. La suite sigue en **250 passed, 5 skipped**
y el check «Pruebas y verificaciones» está en **pass**.

Lo más probable es un tope del lado de la cuenta —el plan Hobby limita los
despliegues diarios— o una protección de despliegue activada en el proyecto.
**No pude confirmarlo**: desde el entorno donde se trabajó no hay salida de red
hacia `api.vercel.com`, y el token de GitHub no tiene permiso para leer la API
de deployments (403).

Qué hacer antes de fusionar: abrir el panel de Vercel y mirar por qué se bloqueó
ese despliegue concreto. Si es el límite diario, se resuelve solo al día
siguiente. **Conviene comprobarlo** porque el merge a `main` dispara justamente
el despliegue de producción que debe recoger las variables de Upstash; si los
despliegues siguen bloqueados, el merge no publicaría nada y `/readyz` seguiría
mostrando el estado antiguo.

---

## 2. Resuelto: rate limiting distribuido activo (15/08/2026)

El bloque está **cerrado y verificado**. No rehacer ningún paso:

1. **Base Upstash creada** por el usuario (15/08/2026).
2. **Las tres variables están en Vercel** (Production): `UPSTASH_REDIS_REST_URL`,
   `UPSTASH_REDIS_REST_TOKEN` y `COTIZAT_REQUIRE_DISTRIBUTED_RATELIMIT=true`.
3. **PR #18 fusionado** en `main` (merge `7940ce9`); producción desplegó desde
   `main` y recogió las variables.
4. **Verificado el 15/08/2026**: `https://cotizat-generador.vercel.app/readyz`
   responde `200` con `"rate_limit": "distribuido:upstash"` y `"ok": true`, y
   `"errors": []`. Diagnóstico: `memoria` = variables ausentes en Production;
   `mal-configurado` = URL no https o token vacío. (Ya no aplican.)
5. Anotado en `docs/CONTINUIDAD_STAGING_SUPABASE.md` (sección 2).

Consumo esperado: 2 comandos por intento de login, muy por debajo del plan
gratuito de Upstash.

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

## 4. En curso: emails de invitación — todo operativo hecho, falta fusionar el código

### Estado exacto (15/08/2026, tarde)

**Parte operativa: COMPLETA por el usuario** ✅

- **Dominio propio comprado**: `cotizat.online` (GoDaddy).
- **Vercel**: dominios `cotizat.online` y `www.cotizat.online` añadidos; la app
  ya responde en `https://cotizat.online` (`/healthz` y `/readyz` 200 OK).
  DNS en GoDaddy: A `@` → `76.76.21.21`, CNAME `www` → `cname.vercel-dns.com`
  (comprobar que no quede un A duplicado de parking si la web «parpadea»).
- **Supabase**: Site URL `https://cotizat.online` y Redirect URL
  `https://cotizat.online/restablecer-clave` configuradas.
- **`COTIZAT_PUBLIC_URL=https://cotizat.online`** en Vercel (Production) y
  **redeploy hecho** → `/readyz` ya reporta
  `recovery_redirect_url_esperada: https://cotizat.online/restablecer-clave`.
- **Resend**: cuenta creada, dominio `cotizat.online` añadido y **verificado**
  (SPF/DKIM/MX publicados en GoDaddy; DKIM confirmado público:
  `resend._domainkey.cotizat.online` TXT visible).
- **Vercel (Production)**: `RESEND_API_KEY` y
  `COTIZAT_EMAIL_FROM=CotizaT <no-responder@cotizat.online>` añadidas.

**Parte de código: lista pero SIN FUSIONAR — este es el único paso pendiente** ⚠️

- El código de emails vive en la rama **`arena/01a00633-generador-comercial`**,
  HEAD **`6d99b7d`**, ya subida a GitHub (3 commits sobre `main`):
  1. `282f9c7` — emails de invitación por Resend con degradación a enlace en
     pantalla (`app/services/email.py`, plantillas, cableado en
     `crear_invitacion_web`, `checks.email` en `/readyz`, 12 pruebas en
     `tests/test_email_invitaciones.py`; suite **262 passed, 5 skipped**);
  2. `5679ceb` — docs: el dominio de Vercel no puede usarse en Resend;
  3. `6d99b7d` — docs: guía del dominio (`docs/DOMINIO_COTIZAT_ONLINE.md`).
- **`main` sigue en `7940ce9`** (merge del PR #18). Producción despliega desde
  `main`, por eso `/readyz` de `cotizat.online` **NO muestra `"email"` todavía**
  aunque las variables ya estén en Vercel. El `"email": "configurado"` que vio
  el usuario era el preview de Vercel de la rama, no producción.

### Lo inmediato (único paso que falta)

1. **Fusionar la rama `arena/01a00633-generador-comercial` a `main`** (PR o
   merge manual como el #18). El despliegue de producción recoge las variables
   ya existentes y el `checks.email`.
2. Verificar `https://cotizat.online/readyz` → debe aparecer
   `"email": "configurado"` (y seguir `"rate_limit": "distribuido:upstash"`).
3. **Prueba E2E final**: crear una invitación real en `/equipo` con un email
   al que el usuario tenga acceso; confirmar que llega el correo desde
   `no-responder@cotizat.online` con el enlace de invitación; aceptarla con
   una cuenta del mismo email verificado y comprobar que se consume.
4. Opcional: si el dominio «parpadea», revisar en GoDaddy que haya un único
   registro A `@` → `76.76.21.21` (sin el de parking).

Hasta que se fusione, el flujo funciona igual que antes (enlace en pantalla).

Bloques posteriores, en orden recomendado:

1. **E1-040 — pruebas de recorridos críticos.** Criterio de salida de Etapa 1,
   aún en `[~]`.
2. **E1W-012 — importación de instalaciones SQLite hacia la web.**
3. **Paquete legal/comercial:** E1-018 (EULA), E1-019 (privacidad), E1-020
   (licencias de terceros), E1-050 (guía de inicio), E1-056 (landing).

Criterios de salida de Etapa 1 aún abiertos: primer PDF en <20 min por usuario
nuevo, catálogo con procedencia y precios fechados, exportación/migración desde
SQLite, guía + oferta + contrato + soporte, recorrido crítico cubierto en CI,
tres pruebas de usabilidad externas.

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

**Dónde quedó todo (15/08/2026).**

- **Rate limiting distribuido: cerrado y verificado.** Base Upstash creada,
  tres variables en Vercel, PR #18 fusionado (merge `7940ce9` en `main`) y
  `/readyz` responde `"rate_limit": "distribuido:upstash"` con `"ok": true`.
- **Dominio propio operativo:** `cotizat.online` (GoDaddy) apuntando a Vercel;
  la app responde en `https://cotizat.online` y `www`. Supabase con Site URL y
  Redirect URL del dominio nuevo. `COTIZAT_PUBLIC_URL=https://cotizat.online`
  en Vercel y redeploy hecho (confirmado en `/readyz`:
  `recovery_redirect_url_esperada: https://cotizat.online/restablecer-clave`).
- **Emails de invitación — TODO lo operativo está hecho y verificado por el
  usuario:** cuenta Resend creada, dominio `cotizat.online` verificado en
  Resend (SPF/DKIM/MX en GoDaddy), y en Vercel Production ya están
  `RESEND_API_KEY` y `COTIZAT_EMAIL_FROM=CotizaT <no-responder@cotizat.online>`.
- **PERO el código de emails NO está en `main` todavía.** Vive en la rama
  `arena/01a00633-generador-comercial` (HEAD `6d99b7d`, 3 commits sobre
  `main`: `282f9c7` código, `5679ceb` y `6d99b7d` docs), ya subida a GitHub.
  `main` sigue en `7940ce9`, así que el `/readyz` de producción NO muestra
  `"email"` aunque las variables ya existen. El `"email": "configurado"` que
  vio el usuario era el preview de Vercel de la rama.
- **Lo único que falta en el bloque de emails:** fusionar la rama
  `arena/01a00633-generador-comercial` a `main` (PR o merge manual, como el
  #18); el despliegue de producción recoge las variables y `/readyz` debe
  mostrar `"email": "configurado"`. Después, prueba E2E final: crear una
  invitación real en `/equipo` con un email del usuario y confirmar que llega
  desde `no-responder@cotizat.online`.

**Empieza por verificar el estado real, no te fíes de este resumen:**

1. `git log --oneline -5` y `git status --short` — ¿árbol en la rama
   `arena/01a00633-generador-comercial` con `6d99b7d` presente?
2. `git ls-remote origin arena/01a00633-generador-comercial` — ¿la rama está
   en GitHub con el mismo commit?
3. Recrea el entorno y corre la suite: `python3 -m venv .venv`,
   `.venv/bin/pip install -r requirements-dev.txt`, `.venv/bin/pytest -q`.
   Deben salir **262 passed, 5 skipped**.
4. Abre `https://cotizat.online/readyz` — debe estar en 200 con
   `rate_limit: distribuido:upstash`; fíjate si ya aparece `"email"` (si el
   merge ya se hizo) o no (si sigue pendiente).
5. Pregunta al usuario si ya fusionó la rama a `main` antes de hacer nada con
   el código; si no, es el siguiente paso (él decide PR o merge manual).

**Aparcado por decisión del usuario:** los puntos 13-manual y 14 de la matriz
de aceptación, hasta que el desarrollo esté cerrado. No pedirlos todavía.

**Siguientes bloques cuando cierre esto:** 1) E1-040 pruebas de recorridos
críticos; 2) E1W-012 importación de instalaciones SQLite hacia la web;
3) paquete legal/comercial (E1-018/019/020/050/056). Recordar: plan Hobby de
Vercel prohíbe uso comercial → pasar a Pro antes de cobrar.

---
