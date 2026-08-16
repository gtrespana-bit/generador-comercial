# Continuidad exacta: staging Vercel + Supabase

Fecha de corte: 14/08/2026 (America/Caracas).

Este documento permite continuar el trabajo desde una conversación nueva sin
depender del historial del chat. Debe leerse junto con
`PLAN_DE_COMERCIALIZACION_Y_EVOLUCION_SAAS.md`, especialmente las secciones 1.3
y 11.

> **Empieza por `docs/PUNTO_DE_CONTINUACION.md`** (corte del 15/08/2026,
> cierre de sesión). Este archivo describe el estado *de fondo* de staging;
> aquel dice **en qué paso exacto se quedó el trabajo** y qué toca hacer a
> continuación. Resumen: PR #18 (rate limiting), PR #19 (emails) y PR #20
> (E1-040 recorrido crítico, E1W-012 importación SQLite→web y paquete
> legal/comercial con landing `/conocer` y páginas `/legal/*`) fusionados;
> el usuario probó las páginas nuevas y aceptó la v1. Quedan la prueba E2E
> de invitaciones y pendientes operativos menores a su cargo.

## 1. Estado confirmado del repositorio

La Etapa 1 local browser-first incluye:

- PostgreSQL y migraciones Alembic sin DDL implícito al arrancar;
- organizaciones, usuarios, membresías y propiedad empresarial;
- aislamiento tenant automático en SQLAlchemy;
- Supabase Auth con cookies HttpOnly, recuperación e invitaciones de un solo uso;
- Storage privado abstraído, metadatos en PostgreSQL y proxy autorizado;
- rol grupal PostgreSQL `cotizat_app`, contexto transaccional y políticas RLS;
- CSRF same-origin, cabeceras defensivas y rate limiting local de Auth;
- CSP con nonce para scripts y estilos, sin `unsafe-inline`;
- ausencia automatizada de handlers HTML, atributos `style`, style API directa y
  sinks de fragmentos HTML;
- auditoría de protección de rutas y ausencia de mutaciones empresariales
  directas en endpoints GET;
- rol `lectura` bloqueado antes de efectos externos de Storage.

Última validación automatizada:

```text
158 passed
```

Siguen pasando compilación Python, parseo Jinja con entorno real, `node --check`
y `git diff --check`. `.env` y `presupuestos.db` no forman parte del repositorio.

### Estado real de staging alcanzado (14/08/2026)

- `/healthz` (liveness) responde **200 OK**: `{"ok": true, "checks": {"status": "alive"}, "errors": []}`.
- `/readyz` (readiness) responde **200 OK**:
  ```json
  {
    "ok": true,
    "checks": {
      "auth": "configurado",
      "storage": "supabase:cotizat-private",
      "public_url": "configurado",
      "database": "postgresql",
      "alembic": "head:f4c1d8e37a95",
      "rol_runtime": "superuser=False, bypassrls=False, inherit=True, cotizat_app=True"
    },
    "errors": []
  }
  ```

> **Actualización 16/08/2026:** el head exigido es ahora `f4c1d8e37a95`
> (E1-060, licencias de operador). La migración se aplicó en Supabase y
> `/readyz` real responde `"alembic": "head:f4c1d8e37a95"` con `"ok": true`
> (ver `docs/PANEL_DE_OPERADOR.md` §5).
- La raíz `/` redirige correctamente a `/acceso` (pantalla de inicio de sesión).
- Diagnóstico y resolución de errores iniciales de Vercel:
  1. `alembic_version` estaba vacía / filtrada por RLS para roles no superusuario.
  2. Se ejecutó `INSERT INTO alembic_version` y `ALTER TABLE public.alembic_version DISABLE ROW LEVEL SECURITY; GRANT SELECT ON TABLE public.alembic_version TO cotizat_app;` en Supabase.
  3. Se corrigió `_verificar_head_alembic_postgresql()` para usar `.scalar_one_or_none()`, calificar explícitamente `public.alembic_version` y atrapar excepciones en `lifespan` de forma defensiva para evitar cierres abruptos 500 en Vercel.

### Cierre del incidente de `alembic_version` (14/08/2026)

La migración `e1a4b7c9d2f0` (parent `d7f2a9c41e63`) versiona de forma
permanente el `DISABLE ROW LEVEL SECURITY` y el `GRANT SELECT` de
`public.alembic_version`. Ya está **aplicada en Supabase** y **desplegada en
producción**:

- Supabase confirmó `relrowsecurity = false`, `relforcerowsecurity = false`,
  `cotizat_app_puede_leer = true` y `version_num = e1a4b7c9d2f0`.
- `/readyz` en producción responde **200 OK** con `"alembic":
  "head:e1a4b7c9d2f0"` y `"rol_runtime": "superuser=False, bypassrls=False,
  inherit=True, cotizat_app=True"`.
- El PR **#16** se fusionó en `main` el 14/08/2026 con CI y deploy de Vercel en
  verde.

El incidente queda cerrado: producción y base de datos están alineadas en
`e1a4b7c9d2f0` y el código desplegado espera ese mismo head (el código anterior
fallaría en `/readyz` esperando `d7f2a9c41e63`).

PRs creados en GitHub:
- **PR #3** (fusionado en `main`).
- **PR #4**: `https://github.com/gtrespana-bit/generador-comercial/pull/4` (`fix(staging): asegura lectura de public.alembic_version y atrapa excepciones en lifespan`).
- **PR #16**: `https://github.com/gtrespana-bit/generador-comercial/pull/16` (`fix(db): versiona el endurecimiento de alembic_version`) — **fusionado**.

La nueva conversación debe trabajar desde el `main` resultante (commit
`bb84767`), que ya incluye `e1a4b7c9d2f0`.

## 2. Estado externo verificado de Supabase y Vercel

Estado verificado de Supabase:

```text
Alembic remoto: f4c1d8e37a95 (aplicado el 16/08/2026 con
  docs/staging_upgrade_f4c1d8e37a95.sql; RLS de licencias: true/true, SELECT a cotizat_app)
Rol runtime: cotizat_runtime (NOSUPERUSER, NOBYPASSRLS, INHERIT, miembro de cotizat_app)
Bucket Storage: cotizat-private (privado, 12 MB)
Auth URLs: Site URL https://cotizat.online y Redirect URL https://cotizat.online/restablecer-clave
```

Estado verificado de Vercel:

```text
URL de staging: https://cotizat.online (dominio propio, 15/08/2026);
  alias previo https://cotizat-generador.vercel.app sigue activo.
Variables de entorno: DATABASE_URL, COTIZAT_REQUIRE_RLS_ROLE=true, SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, COTIZAT_STORAGE_BACKEND=supabase, SUPABASE_STORAGE_BUCKET=cotizat-private, SUPABASE_SECRET_KEY, COTIZAT_COOKIE_SECURE=true, COTIZAT_TRUST_PROXY=true, COTIZAT_PUBLIC_URL=https://cotizat.online, UPSTASH_REDIS_REST_URL, UPSTASH_REDIS_REST_TOKEN, COTIZAT_REQUIRE_DISTRIBUTED_RATELIMIT=true, RESEND_API_KEY, COTIZAT_EMAIL_FROM=CotizaT <no-responder@cotizat.online>, COTIZAT_OPERADORES (añadida el 16/08/2026: correo del titular; habilita /admin/licencias).
Panel de operador (E1-060, 16/08/2026): https://cotizat.online/admin/licencias — desplegado y verificado por el titular.
Rate limiting distribuido (verificado el 15/08/2026): las tres variables de
Upstash están en Vercel (Production), el PR #18 está fusionado y `/readyz`
responde `"rate_limit": "distribuido:upstash"` con `"ok": true`.
Resend (15/08/2026): dominio cotizat.online verificado (SPF/DKIM/MX en GoDaddy).
Emails (verificado el 15/08/2026, noche): PR #19 fusionado (merge f686e80) y
`/readyz` de producción responde `"email": "configurado"`.
/healthz: 200 OK
/readyz: 200 OK (recovery_redirect_url_esperada: https://cotizat.online/restablecer-clave)
```

Pendientes explícitos:

1. Pruebas de la matriz de aceptación de la Sección 4 con dos correos y dos organizaciones en la aplicación desplegada.
2. Validación de CSP/interacciones en navegador real durante la matriz.
3. ~~Rate limiting distribuido: código listo (`app/ratelimit.py`).~~ **Resuelto el
   15/08/2026**: base Upstash creada, las tres variables añadidas en Vercel
   (Production) y PR #18 fusionado; `/readyz` responde
   `checks.rate_limit = "distribuido:upstash"` con `"ok": true`.
4. Emails de invitación (ver `docs/EMAILS_INVITACION.md` y
   `docs/DOMINIO_COTIZAT_ONLINE.md`): **código y operativo completos y
   desplegados** (PR #19 fusionado el 15/08/2026, merge `f686e80`; dominio
   cotizat.online verificado en Resend; `RESEND_API_KEY` y
   `COTIZAT_EMAIL_FROM` en Vercel Production; `/readyz` verificado con
   `"email": "configurado"`). **Solo queda la prueba E2E** a cargo del
   usuario: invitación real en `/equipo` → correo desde
   `no-responder@cotizat.online` → aceptarla y comprobar que se consume.
5. ~~Importación explícita de instalaciones SQLite~~ **Resuelto el 15/08/2026**
   (E1W-012): asistente de dos pasos en `/configuracion/importar-instalacion`
   con confirmación explícita y SHA-256 verificado. Las imágenes y archivos
   locales no viajan (la base no los contiene): el asistente lo avisa y el
   usuario los vuelve a subir desde la web cuando los necesite.

Regla invariable:

- nunca configurar `MIGRATION_DATABASE_URL` en runtime;
- nunca usar una conexión `postgres`/administrativa como `DATABASE_URL`;
- nunca poner `service_role`/`sb_secret_` en variables públicas del frontend;
- nunca fijar `COTIZAT_REQUIRE_RLS_ROLE=false` como solución de despliegue.

### Incidencia resuelta: bootstrap de la primera organización bajo RLS (14/08/2026)

La matriz quedó detenida en el punto 2 (crear la organización A). Vercel
registró:

```text
psycopg.errors.InsufficientPrivilege: new row violates row-level security
policy for table "organizaciones"
[SQL: INSERT INTO organizaciones (...) RETURNING organizaciones.id]
```

Causa raíz exacta, reproducida contra un PostgreSQL real con un rol
`NOBYPASSRLS`: **el `WITH CHECK` de `cotizat_org_insert` sí se cumplía**. Lo
que fallaba era el `RETURNING organizaciones.id` que SQLAlchemy añade para
recuperar la clave primaria: `RETURNING` evalúa la política de lectura
`cotizat_org_select` sobre la fila recién insertada, y esa política exige una
membresía que todavía no puede existir (la membresía necesita el `id` de la
organización). Un bootstrap circular.

Corrección aplicada **sin relajar ninguna política**:

- `reservar_id_organizacion()` obtiene el `id` con
  `nextval(pg_get_serial_sequence('public.organizaciones','id'))`. `nextval`
  no lee la tabla, así que ninguna política de fila lo alcanza;
- `crear_organizacion_con_propietario()` inserta con la clave primaria ya
  explícita, por lo que SQLAlchemy **omite el `RETURNING`**, y crea la
  membresía de `propietario` en la misma transacción — justo lo que
  `cotizat_security.can_create_owner_membership` autoriza;
- en SQLite (sin RLS) se conserva el autoincremento del motor.

No se modificaron políticas, roles ni migraciones: la revisión Alembic sigue
siendo `c93e7a4d20f1` y **no hace falta migrar la base de staging**.

Regresión añadida:

- `tests/test_rls.py`: el `INSERT` con `id` explícito no emite `RETURNING`, la
  reserva usa la secuencia sin tocar la tabla, y el endpoint no reintroduce el
  alta directa;
- `tests/test_rls_postgres.py` (nuevo): contra PostgreSQL real con un rol
  `NOBYPASSRLS`, verifica que el `INSERT ... RETURNING` **sigue siendo
  rechazado** (si esa prueba deja de fallar, alguien debilitó
  `cotizat_org_select`) y que el camino corregido completa el alta. Se omite
  salvo que se defina `COTIZAT_TEST_ADMIN_DATABASE_URL`:

  ```bash
  COTIZAT_TEST_ADMIN_DATABASE_URL=postgresql+psycopg://postgres@/postgres \
      pytest tests/test_rls_postgres.py
  ```

Validación automatizada tras la corrección: `164 passed, 3 skipped` sin
PostgreSQL y `167 passed` con PostgreSQL real.

**Confirmado en staging (14/08/2026):** con el PR #6 fusionado, el propietario
creó correctamente la Organización A en la aplicación desplegada. Los puntos 1
y 2 de la matriz quedan superados.

### Punto 3 de la matriz superado: recuperación de contraseña (14/08/2026)

El propietario confirmó el ciclo completo en la aplicación desplegada:

1. `/recuperar-acceso` envía el email de recuperación;
2. el enlace del email aterriza en `/restablecer-clave` con el token en el
   fragmento (ya sin el rebote a `/acceso` descrito en la Sección 23 de la
   hoja de ruta);
3. la contraseña se cambia correctamente;
4. el inicio de sesión con la contraseña nueva funciona.

Con esto queda validada en HTTPS real la corrección de `redirect_to` como
parámetro de query en `POST /auth/v1/recover` y la red de seguridad
`app/static/js/recovery_redirect.js`. La matriz continúa desde el **punto 4**
(subida de logo, imagen de partida/producto, anexo PDF y ficha técnica contra
el bucket privado `cotizat-private`), que es la primera prueba real de
`SupabaseStorage` en despliegue.

### Integración continua y dependencias bloqueadas (14/08/2026)

Los dos últimos fallos (`alembic_version` y bootstrap RLS) se detectaron en
staging, no antes de fusionar. Se añadió la puerta automática que faltaba:

- `docs/ci/ci.yml` se ejecuta en cada pull request y push a `main` o
  `arena/**`, e incluye instalación del lock, coherencia del bloqueo,
  `compileall`, parseo Jinja con el entorno real, `node --check`, revisión de
  espacios en blanco acotada al cambio, simulación del sistema de archivos de
  solo lectura de Vercel (PostgreSQL y SQLite) y `pytest -q`;
- `requirements.txt` y `requirements-dev.txt` fijan cada dependencia con `==`;
  `requirements.lock` guarda el cierre transitivo (41 paquetes). Antes, los
  rangos abiertos permitían que **cada build de Vercel resolviera versiones
  distintas** y rompiera un despliegue estable sin cambios en el repositorio;
- `tools/generar_lock.py` regenera el cierre y `tools/verificar_lock.py` impide
  que un pin cambie sin regenerarlo;
- `tools/verificar_plantillas.py` parsea las 40 plantillas con el entorno Jinja
  real de `app.main`.

Al actualizar una dependencia el procedimiento es: cambiar el pin, ejecutar
`python tools/generar_lock.py`, correr la suite y abrir el pull request.

**Acción manual completada (14/08/2026):** `.github/workflows/ci.yml` se creó
desde la interfaz web de GitHub (commit `24fe1e0` en `main`) y es idéntico a
`docs/ci/ci.yml`. El flujo `CI` está **activo** y su primera ejecución sobre
`main` terminó en verde: job "Pruebas y verificaciones" ✓, run
`31811936947`. La prueba `test_el_flujo_activo_coincide_con_la_definicion_versionada`
(`tests/test_integracion_continua.py`) sigue impidiendo que ambas copias se
separen. Aviso no bloqueante de esa ejecución: GitHub ejecutará
`actions/checkout@v4` y `actions/setup-python@v5` en Node 24 por la
deprecación de Node 20 (actualizar versiones cuando se toque el flujo).

Validación automatizada tras este bloque: `174 passed, 3 skipped`.

### Incidencia resuelta: el registro fallaba con «Supabase no pudo crear la cuenta» (14/08/2026)

El registro, que estaba confirmado como superado (punto 1), empezó a fallar
**siempre** en staging. No era una clave caducada ni configuración perdida: era
un **bug propio de parseo** que se destapó al activar «Confirm email» en el
proyecto Supabase.

`POST /auth/v1/signup` responde **HTTP 200 con tres formas distintas**
(`internal/api/signup.go`) y solo la de autoconfirm anida el usuario bajo la
clave `user`. Con confirmación por email, el usuario viene **en la raíz**;
`sign_up` leía siempre `payload["user"]` y convertía esa respuesta correcta en
`InvalidCredentials`. Detalle completo y tabla de casos en
`docs/AUTENTICACION_SUPABASE.md`.

Corregido en `d4aa7f1`: se acepta el usuario en la raíz y el error se reserva
para respuestas sin identidad utilizable. El caso «email ya registrado» se
detecta por `identities: []` y se expone como `SignupResult.ya_registrado`,
**sin cambiar el mensaje mostrado** (diferenciarlo permitiría enumerar qué
emails tienen cuenta). Cubierto por cuatro pruebas en `tests/test_auth.py`.

> **Aviso operativo para la matriz manual:** el SMTP por defecto de Supabase
> limita a **~2-4 emails por hora**. Los puntos 6-9 exigen registrar y confirmar
> un segundo correo, así que ese tope puede bloquear el recorrido a mitad. Si
> ocurre, configurar un SMTP propio antes de continuar; no relajar «Confirm
> email» para esquivarlo.

## 3. Orden obligatorio del siguiente bloque

> **Punto exacto al 14/08/2026 (última actualización):** puntos 1–9, 11 y 12
> superados en `https://cotizat-generador.vercel.app`: registro, Organización A,
> recuperación de contraseña, subida de logo/imagen/anexo/ficha, descarga del
> PDF, **invitación al Usuario B con rol `lectura`, aceptación de un solo uso
> con email verificado, comprobación de que `lectura` no escribe, ascenso a
> `miembro`, creación de la Organización B con nombres/números homónimos sin
> mezcla de datos con A, cookies Auth HttpOnly/Secure/SameSite=Lax con
> `document.cookie` vacío y desaparición al cerrar sesión, y consola sin
> violaciones CSP** (el rechazo de escrituras cross-site del punto 11 está
> cubierto en CI por `tests/test_web_security.py`). Los puntos **10 y 13 se han
> trasladado a pruebas automáticas** en
> `tests/test_aislamiento_almacenamiento.py`, porque eran comprobaciones
> manuales fáciles de olvidar tras un cambio en el proxy `/archivos/...`: ahora
> CI verifica que un objeto de A devuelve 404 bajo B (también manipulando la
> clave) y que nada del código expone el bucket directamente. La única parte
> del punto 13 que sigue siendo manual, por depender del proyecto Supabase real
> y no del código, es pegar la URL pública del objeto en el navegador y
> confirmar el acceso denegado. La lógica del punto 14 (rechazo de arranque con
> un rol `SUPERUSER`/`BYPASSRLS`) ya está cubierta por `tests/test_rls.py` y
> `tests/test_health.py`.
>
> **Lo siguiente son el punto 14** (rechazo de arranque con un rol
> privilegiado; opcional, lógica cubierta en CI) **y la parte manual del punto
> 13** (URL pública del bucket denegada).

> Punto exacto al 14/08/2026: Pasos A–F completados y verificados. `/healthz` y `/readyz` responden 200 OK en la URL real `https://cotizat-generador.vercel.app`. Resuelta la incidencia de bootstrap de organizaciones bajo RLS y **confirmada en staging la creación de la Organización A** (puntos 1 y 2 de la matriz superados). Añadidos además integración continua y bloqueo de dependencias (ver Sección 2), y **el workflow `CI` ya está activo en GitHub** con su primera ejecución sobre `main` en verde (run `31811936947`); con esto queda cerrada la "Acción manual pendiente" del flujo. **Lo siguiente es continuar la matriz de aceptación de la Sección 4 desde el punto 3** (recuperación de contraseña); el usuario A y la Organización A ya existen, así que no deben repetirse su registro ni su aprovisionamiento.

### Paso A — Fusionar el PR abierto

- PR #4 ya fusionado. El PR vivo es **#11**
  (`https://github.com/gtrespana-bit/generador-comercial/pull/11`), con los
  anexos PDF, el aislamiento verificado en CI, la guía de pasos manuales y el
  arreglo del registro. Checks en verde.
- Fusionarlo en `main` e iniciar la conversación nueva desde el `main`
  actualizado.

### Paso B — Ejecutar la matriz de aceptación manual (Sección 4)

Paso a paso con dos correos (ej. Usuario A y Usuario B):

1. ~~**Usuario A:** Registro, inicio de sesión y creación de Organización A.~~ **Completado el 14/08/2026.**
2. ~~**Usuario A:** Completar onboarding (demo o limpio).~~ **Completado el 14/08/2026.**
3. ~~**Usuario A:** Probar recuperación de clave (redirect fijo `https://cotizat-generador.vercel.app/restablecer-clave`).~~ **Completado el 14/08/2026:** email recibido, enlace correcto, contraseña cambiada e inicio de sesión con la nueva.
4. ~~**Usuario A:** Cargar logo, partida con imagen, anexo PDF y ficha técnica.~~ **Completado el 14/08/2026.**
5. ~~**Usuario A:** Crear presupuesto y descargar PDF generado.~~ **Completado el 14/08/2026.**
6. ~~**Usuario A → Usuario B:** Invitar a Usuario B con rol `lectura` desde `/equipo`.~~ **Completado el 14/08/2026.**
7. ~~**Usuario B:** Aceptar invitación una sola vez (email verificado). `lectura` consulta/descarga y devuelve 403 en escrituras.~~ **Completado el 14/08/2026.**
8. ~~**Usuario A:** Ascender a B a `miembro`. Verificar que B ya puede crear/editar en Organización A.~~ **Completado el 14/08/2026.**
9. ~~**Usuario B:** Crear Organización B (nombre/números homónimos) y verificar aislamiento total de datos.~~ **Completado el 14/08/2026: sin fuga de datos entre A y B.**
10. ~~**Seguridad de Storage:** Probar que una URL de objeto de la Organización A devuelve 404 para la Organización B.~~ **Cubierto por pruebas automáticas el 14/08/2026** (`tests/test_aislamiento_almacenamiento.py`); queda como confirmación visual opcional en staging.
11. ~~**Cookies/CSRF:** Confirmar cookies HttpOnly/Secure/SameSite, `document.cookie` vacío y desaparición al cerrar sesión.~~ **Completado el 14/08/2026** (el rechazo de escrituras cross-site está cubierto en CI por `tests/test_web_security.py`).
12. ~~**DevTools/CSP:** Ausencia de violaciones Content Security Policy en la consola del navegador.~~ **Completado el 14/08/2026:** se eliminaron dos hojas `<style>` inyectadas sin nonce en `dragdrop.js` y `totales.js` y se validó en el despliegue de la rama.
13. ~~**Bucket privado:** Verificar que el acceso directo al objeto público en Supabase Storage devuelve acceso denegado.~~ **Aprovisionamiento cubierto por pruebas automáticas el 14/08/2026**; falta una única comprobación manual: pegar en el navegador la URL pública del objeto y confirmar que Supabase responde acceso denegado.
14. **Arranque con rol privilegiado:** confirmar que CotizaT se niega a servir si `DATABASE_URL` usa un rol con `SUPERUSER`/`BYPASSRLS` (503 en `/readyz`). ← **siguiente**

### Incidencias resueltas durante el punto 12 (14/08/2026)

La revisión de la consola del creador destapó dos fallos reales, corregidos en
la rama `arena/01a00312-generador-comercial` (PR #17) y validados en el
despliegue de la rama:

1. **Violaciones CSP.** `editor/dragdrop.js` y `editor/totales.js` creaban
   elementos `<style>` con `textContent` sin asignarles el nonce de la
   respuesta, así que la CSP estricta (`style-src 'self' 'nonce-…' + Google
   Fonts`) los bloqueaba. Esos estilos ya vivían en `style.css` o se aplican
   por la utilidad `CotizatStyles` (hoja con nonce vía CSSOM), así que la
   inyección era redundante y se eliminó. Se añadió una prueba que exige nonce
   a cualquier `<style>` dinámico (`tests/test_web_security.py`).
2. **500 al borrar una partida del catálogo.** `eliminar_partida` y
   `bulk_delete_partidas` borraban la fila de `partidas` sin desvincular las
   líneas de `presupuesto_items` que la referencian, y PostgreSQL respondía
   `ForeignKeyViolation`. Como `partida_catalogo_id` solo recuerda el origen de
   la copia (el precio ya vive en la línea), ahora se anula la referencia antes
   del borrado y el presupuesto sobrevive intacto. Regresión en
   `tests/test_app.py` con las FK de SQLite activadas.

## 4. Matriz de aceptación real

No declarar staging validado hasta completar los 14 puntos con dos correos verificados:

1. usuario A se registra, verifica email e inicia/cierra sesión;
2. A crea organización A y completa onboarding limpio o demo;
3. recuperación de contraseña llega y solo redirige al origen fijo;
4. A sube logo, producto/partida con imagen, anexo y ficha PDF;
5. A crea un presupuesto y genera/descarga PDF;
6. A invita a B y B acepta una sola vez con email coincidente y verificado —
   **superado en staging (14/08/2026)**;
7. B con rol `lectura` puede consultar/descargar pero no crear, editar, borrar ni
   provocar efectos de Storage — **superado en staging (14/08/2026)**;
8. al cambiar B a `miembro`, puede escribir en la organización autorizada —
   **superado en staging (14/08/2026)**;
9. crear organización B con nombres/números homónimos no mezcla datos con A —
   **superado en staging (14/08/2026)**;
10. una URL/clave de objeto de A solicitada bajo B devuelve 404 — **cubierto en
    CI** (`tests/test_aislamiento_almacenamiento.py`: recorrido HTTP con dos
    organizaciones, más los intentos de manipular la clave);
11. cookies Auth son Secure/HttpOnly y las escrituras cross-site devuelven 403 —
    **superado en staging (14/08/2026)** (cookies comprobadas en navegador;
    rechazo cross-site cubierto en CI por `tests/test_web_security.py`);
12. DevTools no muestra violaciones CSP ni fallos de interacción/estilos —
    **superado en staging (14/08/2026)** (dos hojas `<style>` dinámicas sin
    nonce eliminadas y validado en el despliegue de la rama);
13. el bucket no entrega objetos sin pasar por CotizaT — **cubierto en CI** en
    todo lo que depende del código (el bucket se aprovisiona `public=false`,
    no existe generación de URL pública ni firmada, y ninguna plantilla enlaza
    a `supabase.co/storage`); **queda pendiente** la comprobación manual de que
    la URL pública del objeto responde acceso denegado en el proyecto real;
14. el arranque falla si se sustituye temporalmente `DATABASE_URL` por un rol con
    `BYPASSRLS` o fuera de `cotizat_app` (probar sin exponer credenciales).

Usar solo datos ficticios durante esta matriz.

## 5. Qué hacer después de la matriz

Si staging pasa la matriz:

1. activar el rate limiting distribuido en Vercel (el código ya está: basta
   crear la base en Upstash y definir `UPSTASH_REDIS_REST_URL`,
   `UPSTASH_REDIS_REST_TOKEN` y `COTIZAT_REQUIRE_DISTRIBUTED_RATELIMIT=true`;
   comprobar después que `/readyz` muestra `rate_limit: distribuido:upstash`);
2. automatizar smoke tests HTTPS de Auth/rutas/CSP donde sea viable;
3. diseñar y probar importación explícita de instalaciones SQLite y objetos;
4. continuar E1-012 a E1-014 (usabilidad y medición del recorrido web);
5. preparar beta privada controlada, no lanzamiento abierto.

Si staging falla durante la matriz, corregir el problema específico observado sin relajar CSRF, CSP, RLS, bucket privado ni la exigencia del rol limitado.

## 6. Mensaje sugerido para iniciar una conversación nueva

El mensaje vigente y el punto exacto de continuación están en
**`docs/PUNTO_DE_CONTINUACION.md`** (corte del 15/08/2026), secciones 2 y 7.

Resumen para no tener que abrirlo: el bloque de **rate limiting distribuido**
quedó terminado en el **PR #18**, abierto y con CI en verde (commit `c7d8be2`,
250 passed / 5 skipped). Falta solo la parte operativa: crear la base en
Upstash, añadir las tres variables en Vercel (**antes** del merge, porque
producción despliega desde `main`), fusionar el PR y comprobar que `/readyz`
devuelve `rate_limit: distribuido:upstash`.

Los puntos 13-manual y 14 de la matriz siguen **aparcados por decisión del
usuario** hasta que el desarrollo esté cerrado: validarlos ahora no sirve de
nada si un paso posterior los rompe.
