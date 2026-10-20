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

## 4. Limitación declarada (resuelta el 20/10/2026, Fase 0.2)

El registro original vivía **en la memoria del proceso** y se perdía al
reiniciar; en serverless cada instancia guardaba el suyo. Esa limitación
quedó cerrada con un **sumidero propio** (sin SDK de terceros, para no
pagar coste por petición ni exportar trazas fuera):

- Cada huella (método + ruta saneada + tipo + mensaje) se persiste en la
  tabla `errores_internos` mediante `app/services/errores_internos.py`,
  *best-effort*: solo cuando ya hay un 500, en su propia sesión y sin que
  un fallo del registro pueda romper la respuesta. En PostgreSQL la
  escritura entra por la función SECURITY DEFINER
  `cotizat_security.registrar_error_interno` (el llamante puede no tener
  sesión) y la lectura es solo del operador (RLS).
- La fila guarda la **traza** de la última ocurrencia (redactada: las
  credenciales embebidas en URLs se sustituyen antes de guardarla),
  además de ocurrencias y primera/última vez. El panel (Sistema › Estado)
  lee de la base, muestra la traza bajo demanda y permite marcar la
  huella como **resuelta**; si el fallo reaparece, la marca se limpia
  sola y vuelve a contar como nueva.
- Una huella nueva —o resucitada tras estar resuelta— dispara un correo
  al buzón de avisos (tope anti-tormenta: 5 por hora y proceso). El cron
  diario de mantenimiento envía el parte de huellas activas en las
  últimas 24 h (silencio si no hay ninguna) y poda las resueltas sin
  actividad en 90 días.
- Interruptor: `COTIZAT_ERRORES_BD=false` vuelve al comportamiento
  histórico (solo buffer en memoria). Si la tabla aún no existe (ventana
  entre el despliegue y la migración), la persistencia se omite en
  silencio y el panel cae al buffer declarándolo en la nota.

Lo que sigue sin cubrir este sumidero, a propósito: la caída total de la
plataforma (Vercel o la BD fuera) no genera fila ni correo — eso lo vigila
el monitor externo de `/readyz`— y los errores «controlados» que la
aplicación ya traduce a páginas con aviso no son 500 y no entran aquí.

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
