# Continuidad exacta: staging Vercel + Supabase

Fecha de corte: 14/08/2026 (America/Caracas).

Este documento permite continuar el trabajo desde una conversación nueva sin
depender del historial del chat. Debe leerse junto con
`PLAN_DE_COMERCIALIZACION_Y_EVOLUCION_SAAS.md`, especialmente las secciones 1.3
y 11.

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
      "alembic": "head:e1a4b7c9d2f0",
      "rol_runtime": "superuser=False, bypassrls=False, inherit=True, cotizat_app=True"
    },
    "errors": []
  }
  ```
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
Alembic remoto: e1a4b7c9d2f0
Rol runtime: cotizat_runtime (NOSUPERUSER, NOBYPASSRLS, INHERIT, miembro de cotizat_app)
Bucket Storage: cotizat-private (privado, 12 MB)
Auth URLs: Site URL https://cotizat-generador.vercel.app y Redirect URL https://cotizat-generador.vercel.app/restablecer-clave
```

Estado verificado de Vercel:

```text
URL de staging: https://cotizat-generador.vercel.app
Variables de entorno: DATABASE_URL, COTIZAT_REQUIRE_RLS_ROLE=true, SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, COTIZAT_STORAGE_BACKEND=supabase, SUPABASE_STORAGE_BUCKET=cotizat-private, SUPABASE_SECRET_KEY, COTIZAT_COOKIE_SECURE=true, COTIZAT_TRUST_PROXY=true, COTIZAT_PUBLIC_URL.
/healthz: 200 OK
/readyz: 200 OK
```

Pendientes explícitos:

1. Pruebas de la matriz de aceptación de la Sección 4 con dos correos y dos organizaciones en la aplicación desplegada.
2. Validación de CSP/interacciones en navegador real durante la matriz.
3. Rate limiting distribuido (Redis/Upstash) antes de escalar a múltiples instancias o apertura pública.
4. Importación explícita de instalaciones SQLite e imágenes.

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

> **Punto exacto al 14/08/2026 (última actualización):** puntos 1–8 superados
> en `https://cotizat-generador.vercel.app`: registro, Organización A,
> recuperación de contraseña, subida de logo/imagen/anexo/ficha, descarga del
> PDF, **invitación al Usuario B con rol `lectura`, aceptación de un solo uso
> con email verificado, comprobación de que `lectura` no escribe, y ascenso a
> `miembro`**. Los puntos **10 y 13 se han trasladado a pruebas automáticas**
> en `tests/test_aislamiento_almacenamiento.py`, porque eran comprobaciones
> manuales fáciles de olvidar tras un cambio en el proxy `/archivos/...`: ahora
> CI verifica que un objeto de A devuelve 404 bajo B (también manipulando la
> clave) y que nada del código expone el bucket directamente. La única parte
> del punto 13 que sigue siendo manual, por depender del proyecto Supabase real
> y no del código, es pegar la URL pública del objeto en el navegador y
> confirmar el acceso denegado.
>
> **Lo siguiente es el punto 9** (el Usuario B crea la Organización B con
> nombres/números homónimos y se verifica que no se mezclan datos con A),
> seguido de los puntos 11, 12 y 14.

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
9. **Usuario B:** Crear Organización B (nombre/números homónimos) y verificar aislamiento total de datos. ← **siguiente**
10. ~~**Seguridad de Storage:** Probar que una URL de objeto de la Organización A devuelve 404 para la Organización B.~~ **Cubierto por pruebas automáticas el 14/08/2026** (`tests/test_aislamiento_almacenamiento.py`); queda como confirmación visual opcional en staging.
11. **Cookies/CSRF/DevTools:** Confirmar cookies HttpOnly/Secure/SameSite y ausencia de violaciones CSP en la consola del navegador.
12. ~~**Bucket privado:** Verificar que el acceso directo al objeto público en Supabase Storage devuelve acceso denegado.~~ **Aprovisionamiento cubierto por pruebas automáticas el 14/08/2026**; falta una única comprobación manual: pegar en el navegador la URL pública del objeto y confirmar que Supabase responde acceso denegado.

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
9. crear organización B con nombres/números homónimos no mezcla datos con A;
10. una URL/clave de objeto de A solicitada bajo B devuelve 404 — **cubierto en
    CI** (`tests/test_aislamiento_almacenamiento.py`: recorrido HTTP con dos
    organizaciones, más los intentos de manipular la clave);
11. cookies Auth son Secure/HttpOnly y las escrituras cross-site devuelven 403;
12. DevTools no muestra violaciones CSP ni fallos de interacción/estilos;
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

1. añadir Redis/Upstash para rate limiting distribuido antes de múltiples
   instancias o exposición pública;
2. automatizar smoke tests HTTPS de Auth/rutas/CSP donde sea viable;
3. diseñar y probar importación explícita de instalaciones SQLite y objetos;
4. continuar E1-012 a E1-014 (usabilidad y medición del recorrido web);
5. preparar beta privada controlada, no lanzamiento abierto.

Si staging falla durante la matriz, corregir el problema específico observado sin relajar CSRF, CSP, RLS, bucket privado ni la exigencia del rol limitado.

## 6. Mensaje sugerido para iniciar una conversación nueva

Copiar este texto, sin añadir secretos:

> Continúa el proyecto CotizaT desde el `main` actual (CI en verde). Lee primero
> `docs/CONTINUIDAD_STAGING_SUPABASE.md` y `docs/MATRIZ_PASOS_MANUALES.md`. No
> repitas trabajo completado ni pidas secretos.
>
> El incidente de invitaciones (500 al aceptar) y el de `alembic_version` están
> cerrados: el head es `e1a4b7c9d2f0`, el PR #16 está fusionado y `/readyz`
> responde 200 en producción.
>
> Staging (`https://cotizat-generador.vercel.app`) y Supabase funcionan;
> `/readyz` responde 200. De la matriz de aceptación: **puntos 1-8 superados** en
> staging y **10 y 13 cubiertos en CI** (`tests/test_aislamiento_almacenamiento.py`).
>
> **Voy a ejecutar yo mismo, en el navegador, los pasos manuales que quedan: 9,
> 11, 12, la parte manual del 13 y el 14.** Sigo la guía de
> `docs/MATRIZ_PASOS_MANUALES.md`. Tu papel es acompañarme: resolver los fallos
> que encuentre, interpretar los errores y corregir el código cuando haga falta,
> sin relajar CSRF, CSP, RLS, el bucket privado ni el rol limitado.
>
> Contexto reciente que necesitas: el registro se rompió con «Supabase no pudo
> crear la cuenta» porque `sign_up` solo leía el usuario anidado bajo `user`, y
> GoTrue lo devuelve en la raíz cuando «Confirm email» está activo. Corregido en
> `d4aa7f1`. Ojo con el límite de **~2-4 emails/hora** del SMTP por defecto de
> Supabase: los puntos 6-9 necesitan confirmar un segundo correo y ese tope puede
> frenar el recorrido.
>
> Al terminar la matriz: fusionar el PR pendiente y retirar del `README.md` el
> aviso de «todavía no debe publicarse».
