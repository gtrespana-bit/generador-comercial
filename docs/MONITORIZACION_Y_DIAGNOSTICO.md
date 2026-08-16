# Monitorización y diagnóstico de la operación web (E3-024)

Fecha: **16/08/2026** · Suite: **453 passed, 6 skipped** · Sin migración nueva
(el head sigue siendo `a3d7e9c1b5f2`; este bloque no cambia esquema).

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

## 6. Estado del cierre de Etapa 3

Código completo en la rama (E3-016 a E3-024). Pendiente del despliegue
autorizado: aplicar en Supabase las migraciones `c2f6e8a1d934` (propuestas) y
`a3d7e9c1b5f2` (baja), con sus scripts en `docs/staging_upgrade_*.sql`, y
ensayar el flujo real en staging. Después, según la puerta de salida del plan:
endurecimiento técnico de la Etapa 4 o el bloque funcional que el titular
decida. Validación comercial y catálogo real siguen aplazados (D-017).
