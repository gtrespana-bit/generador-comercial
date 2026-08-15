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

## 2. Lo siguiente: activar Upstash (pasos del usuario)

El código está listo pero **inactivo hasta que existan las variables**. Mientras
tanto `/readyz` publica `rate_limit: memoria`, que en Vercel significa sin
límite efectivo.

El usuario ya creó la cuenta de Upstash el 15/08/2026. Faltan estos pasos:

### Paso 1 — Crear la base

En [console.upstash.com](https://console.upstash.com), pestaña **Redis** →
**+ Create Database**:

- **Name:** `cotizat-ratelimit`
- **Primary Region:** la más cercana al despliegue de Vercel (`us-east-1` es la
  apuesta segura si no se ha tocado la región). No es crítico: en el peor caso
  se agota el timeout de 3 s y cae al contador local.
- **Plan:** **Free** (500.000 comandos/mes, 256 MB, sin tarjeta, permanente).

### Paso 2 — Copiar credenciales

Base → pestaña **REST API**. Aparecen con los mismos nombres que usa el código.

> ⚠️ Upstash muestra **dos** tokens. Hay que copiar `UPSTASH_REDIS_REST_TOKEN`,
> **no** `UPSTASH_REDIS_REST_READ_ONLY_TOKEN`. `INCR` es una escritura: con el
> de solo lectura todos los intentos fallarían y el sistema quedaría degradado a
> memoria **en silencio** (funcionando, pero sin protección real).

### Paso 3 — Tres variables en Vercel

Proyecto → **Settings** → **Environment Variables**, marcando **Production**
(y Preview si se quiere que apliquen también ahí):

| Clave | Valor |
| --- | --- |
| `UPSTASH_REDIS_REST_URL` | la URL del paso 2 (debe ser `https://`) |
| `UPSTASH_REDIS_REST_TOKEN` | el token completo, no el de solo lectura |
| `COTIZAT_REQUIRE_DISTRIBUTED_RATELIMIT` | `true` |

**Añadir las tres juntas.** Si solo se pone la tercera, `/readyz` responderá 503
a propósito: es la red de seguridad para que una configuración a medias no pase
inadvertida.

### Paso 4 — Fusionar el PR #18

Es lo que lleva el código a producción y dispara el despliegue que recoge las
variables. Por eso las variables van **antes** del merge: así no hay ni un
minuto con la configuración a medias.

### Paso 5 — Verificar

En `https://cotizat-generador.vercel.app/readyz` debe aparecer:

```json
"rate_limit": "distribuido:upstash"
```

Diagnóstico de los otros valores posibles:

| Valor | Significa |
| --- | --- |
| `distribuido:upstash` | Correcto. |
| `memoria` | Las variables no llegaron al entorno **Production**. |
| `mal-configurado` | La URL no es `https://` o el token viajó vacío. |

**Prueba funcional opcional:** 11 intentos fallidos seguidos en `/acceso` deben
dar **429** en el undécimo. Aviso: eso bloquea la propia IP en esa ruta durante
5 minutos. En el panel de Upstash el contador de comandos sube casi en tiempo
real, que es la confirmación más directa.

**Consumo:** 2 comandos por intento de login → ~250.000 intentos/mes dentro del
plan gratuito. No se va a rozar.

### Qué anotar cuando esté verificado

En `docs/CONTINUIDAD_STAGING_SUPABASE.md`, sección 2 (estado externo
verificado): que las tres variables están en Vercel y que `/readyz` devuelve
`rate_limit: distribuido:upstash`, con fecha.

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

## 4. Bloques disponibles después de Upstash

Identificados y no elegidos todavía, en el orden en que los recomendaría:

1. **Envío real de emails de invitación.** Hoy `/equipo` muestra el enlace una
   sola vez y hay que copiarlo a mano. Insostenible en cuanto entre el primer
   cliente piloto. *(Este era el siguiente candidato sugerido.)*
2. **E1-040 — pruebas de recorridos críticos.** Criterio de salida de Etapa 1,
   aún en `[~]`.
3. **E1W-012 — importación de instalaciones SQLite hacia la web.**
4. **Paquete legal/comercial:** E1-018 (EULA), E1-019 (privacidad), E1-020
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

Copiar este texto, sin añadir secretos:

> Continúa el proyecto CotizaT. Lee primero `docs/PUNTO_DE_CONTINUACION.md` y
> luego `docs/CONTINUIDAD_STAGING_SUPABASE.md`. No repitas trabajo completado ni
> pidas secretos.
>
> Contexto: el PR #18 (rate limiting distribuido con Upstash) quedó **abierto,
> con CI en verde**, commit `c7d8be2` sobre la base `66f932f`. Ya creé la cuenta
> de Upstash. Los pasos que me tocan a mí están en la sección 2 de
> `docs/PUNTO_DE_CONTINUACION.md`: crear la base, poner tres variables en Vercel,
> fusionar el PR y comprobar que `/readyz` muestra
> `rate_limit: distribuido:upstash`.
>
> **Dime en qué punto de esa lista estoy** y sigue desde ahí. Si ya está
> fusionado y verificado, anótalo en `docs/CONTINUIDAD_STAGING_SUPABASE.md` con
> fecha y pasamos al siguiente bloque.
>
> Los puntos 13-manual y 14 de la matriz siguen **aparcados por decisión mía**
> hasta el final del desarrollo; no me los pidas todavía.
>
> Siguiente bloque sugerido cuando esto cierre: **envío real de emails de
> invitación**, porque hoy `/equipo` obliga a copiar el enlace a mano y eso no
> aguanta un cliente piloto.
