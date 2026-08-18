# Monitorización y diagnóstico de la operación web (E3-024)

Fecha: **16/08/2026** · Suite: **453 passed, 6 skipped** · Sin migración nueva
(el head al cerrar ese bloque era `a3d7e9c1b5f2`; este bloque no cambió esquema).

> Estado actual: el head es `d6e2f9c4b8a1`; ver
> `docs/PUNTO_DE_CONTINUACION.md`. Esta página conserva el histórico de E3-024.

Con este bloque queda completo el **cierre funcional y operativo de la Etapa 3**
(E3-016 a E3-024). El operador puede ahora ver de un vistazo si el despliegue
está sano y qué errores no capturados están ocurriendo, sin exponer datos de
ningún cliente.

---

## 1. Qué hay y dónde

| Pieza | Ruta / archivo | Acceso |
|---|---|---|
| Liveness (proceso vivo, sin tocar dependencias) | `GET /healthz` | público (ya existía) |
| Readiness (configuración + dependencias + head de Alembic + rol runtime) | `GET /readyz` | público (ya existía) |
| **Panel de operación** | `GET /admin/operacion` | **solo operador** (`COTIZAT_OPERADORES`) |
| Registro de errores no capturados | `app/services/operacion.py` | proceso |
| Middleware de captura | `RegistroErroresMiddleware` (en `main.py`) | transparente |

El panel de licencias (`/admin/licencias`) enlaza con el de operación.

## 2. Panel de operación (`/admin/operacion`)

Tres bloques, todos sin datos de tenant:

1. **Estado del despliegue** — los mismos chequeos de `/readyz`, presentados
   con su estado (ok / error / no aplica). Un 503 de readiness se ve aquí como
   «CON ERRORES» con el detalle de cada chequeo.
2. **Hechos operativos** — backend (`sqlite`/`postgresql`), modo efímero
   (serverless sin escritura en disco), head de Alembic esperado, backend de
   almacenamiento, contador de frecuencia, exigencia de licencias, tiempo del
   proceso activo, errores registrados y operadores configurados.
3. **Errores recientes no capturados** — tabla con última vez, método y ruta,
   tipo, mensaje y ocurrencias, agregados por ruta + tipo + mensaje.

## 3. Registro de errores: qué captura y qué no

- **Captura:** cada excepción que escapa de las rutas (las que hoy terminan
  en un 500 genérico). El middleware la registra y la **relanza intacta**: la
  semántica HTTP no cambia y el 500 lo sigue produciendo el servidor.
- **Privacidad:** la ruta se registra **sin query string** (ahí viajan los
  tokens) y los segmentos con forma de token se sustituyen por `<token>`;
  los mensajes se sanean para no filtrar credenciales (igual que `/readyz`).
- **Acotado:** 200 entradas agregadas como máximo; un fallo en bucle no agota
  la memoria, solo incrementa `ocurrencias`.
- **No captura:** excepciones ya manejadas por la aplicación (errores de
  negocio que devuelven su página con aviso), que son flujo normal.

## 4. Limitación declarada (no escondida)

El registro vive **en la memoria del proceso** y se pierde al reiniciar. En
despliegues serverless cada instancia guarda el suyo. El panel lo dice
explícitamente. Para operación seria con varias instancias, el siguiente paso
sería publicar los errores a un sumidero externo (p. ej. Vercel Log Drains);
queda fuera de este bloque a propósito.

## 5. Verificación

- Pruebas nuevas: `tests/test_operacion.py` (12): agregación y límite del
  registro, saneamiento de tokens y credenciales, middleware que captura y
  relanza (500 intacto), diagnóstico con salud y hechos, panel solo para el
  operador y enlace desde licencias.
- Suite completa: **453 passed, 6 skipped**; 63 plantillas, `compileall`,
  JavaScript, lock (42 paquetes) y `git diff --check` en verde; simulación de
  Vercel read-only correcta. `/healthz` y `/readyz` sin cambios de
  comportamiento.

## 6. Alertas y vigilancia proactiva (E4-023, 19/08/2026)

Hasta ahora la detección de caídas era **reactiva** (alguien entra y ve que
falla). Con E4-023 hay dos capas:

### 6a. Verificación diaria con correo (código, ya operativo)

El mismo cron `/api/cron/mantenimiento` (02:00 UTC) ejecuta los chequeos de
`/readyz` (`app/services/mantenimiento.py` → `ejecutar_verificacion_diaria`).
Si algo falla, envía a **todos los operadores** (`COTIZAT_OPERADORES`) el
correo interno `emails/alerta_operador.{html,txt}` con los errores y el estado
de cada chequeo (sin exponer secretos: el readiness ya los sanea). Es un
correo **interno**: no aparece en el panel «Correos» (`/admin/emails`).

- Si está en verde no escribe a nadie y el resumen del cron lo refleja.
- Sin operadores configurados, no hay a quién escribir (y el resumen lo dice).
- Pruebas en `tests/test_mantenimiento_cron.py`.

### 6b. Vigilante externo de disponibilidad (panel del titular, pendiente)

La verificación diaria solo ve el estado **una vez al día**. Para enterarte de
una caída en minutos, el vigilante externo pide `GET https://cotizat.online/healthz`
(liveness, sin dependencias) cada 1–5 minutos y alerta por email/WhatsApp si
no responde `200`:

1. Crea una cuenta en un monitor de disponibilidad (p. ej. UptimeRobot,
   plan gratuito: 50 monitores a 5 min).
2. Añade un monitor HTTP(S) con URL `https://cotizat.online/healthz`,
   intervalo 5 min, alertas a tu buzón (y a `soporte@cotizat.online` si
   quieres un segundo canal).
3. Marca como **esperado** el 503 de `/readyz` solo si quieres vigilarlo
   también (el 503 es correcto cuando el despliegue no debe recibir tráfico);
   para disponibilidad pura, vigila `/healthz` (siempre 200 si el proceso
   vive).
4. Guarda las credenciales del monitor fuera del repositorio; no añadas el
   monitor como secreto de la app.

## 7. Estado del cierre de Etapa 3

Código completo en la rama (E3-016 a E3-024) y **migraciones `c2f6e8a1d934` y
`a3d7e9c1b5f2` aplicadas y verificadas en Supabase el 16/08/2026** (ver
`docs/PUNTO_DE_CONTINUACION.md` §0ter). Pendiente: desplegar el código de la
rama (hasta entonces `/readyz` del entorno migrado responde 503, esperado) y
ensayar el flujo real en staging. Después, según la puerta de salida del plan:
endurecimiento técnico de la Etapa 4 o el bloque funcional que el titular
decida. Validación comercial y catálogo real siguen aplazados (D-017).
