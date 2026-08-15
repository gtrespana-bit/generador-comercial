# Autenticación web con Supabase

CotizaT separa tres responsabilidades que no deben confundirse:

1. **Supabase Auth** valida email/contraseña y emite la sesión.
2. **CotizaT** vincula el UUID de `auth.users` con `usuarios.auth_user_id` y autoriza una organización mediante `membresias`.
3. **SQLAlchemy** activa `organizacion_id` en la sesión, filtra todas las entidades empresariales y rechaza escrituras cruzadas.

La contraseña y los tokens de sesión no se guardan en PostgreSQL. Los tokens se mantienen en cookies `HttpOnly`, `Secure` y `SameSite=Lax`; la clave secreta de Supabase no participa en el login.

## Variables del servidor

```bash
DATABASE_URL=postgresql://<login-runtime-sin-bypassrls>@...
MIGRATION_DATABASE_URL=postgresql://<administrador-solo-durante-alembic>@...
COTIZAT_REQUIRE_RLS_ROLE=true
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_...
COTIZAT_COOKIE_SECURE=true
COTIZAT_PUBLIC_URL=https://cotizat.example.com
```

`SUPABASE_PUBLISHABLE_KEY` tiene privilegios bajos y puede usarse para Auth. No se debe sustituir por `sb_secret_...`, `service_role` ni otra clave que omita RLS. `MIGRATION_DATABASE_URL` se inyecta únicamente al ejecutar Alembic y se retira del proceso web; no debe ser el fallback permanente de `DATABASE_URL`.

Al probar expresamente sobre `http://localhost`, se puede usar `COTIZAT_COOKIE_SECURE=false`. En cualquier preview o despliegue HTTPS debe permanecer en `true`.

## Esquema y migración

La revisión `9bca2ad1f6e4` añade a `usuarios`:

```text
auth_user_id VARCHAR(36) NULL UNIQUE
```

Es nullable para enlazar gradualmente perfiles anteriores. Una vez vinculado un email, CotizaT rechaza que otro UUID intente apropiarse del perfil.

```bash
alembic upgrade head
```

## Flujo

- `/registro`: crea la identidad en Supabase Auth; si el proyecto exige confirmación, solicita verificar el email.
- `/acceso`: inicia sesión contra GoTrue y escribe cookies HttpOnly.
- `/recuperar-acceso`: solicita a GoTrue un enlace sin revelar si el email existe.
- `/restablecer-clave`: consume la sesión temporal `type=recovery`, elimina el fragmento de la barra y actualiza la contraseña directamente en GoTrue.
- `/organizaciones/nueva`: crea la primera organización y una membresía `propietario`.
- `/organizaciones`: enumera solo membresías y organizaciones activas.
- `/organizaciones/{id}/seleccionar`: vuelve a comprobar la membresía antes de escribir la cookie de selección.
- Rutas comerciales: `get_db` ignora `COTIZAT_ORGANIZATION_ID` en PostgreSQL y deriva usuario, rol y organización de la sesión autenticada.
- `/cuenta`: panel de la persona autenticada (perfil, contraseña, organizaciones y cierre de sesión).
- `/salir`: revoca la sesión en GoTrue (`POST /auth/v1/logout`) y elimina access token, refresh token y organización seleccionada.

## Panel de cuenta (`/cuenta`)

Hasta ahora la sesión solo podía cerrarse desde el enlace de la barra lateral y la contraseña únicamente se cambiaba por email de recuperación. El panel reúne las tres operaciones básicas de la cuenta:

- **Perfil**: edita `usuarios.nombre` y sincroniza `user_metadata.name` en Supabase. El email **no** se edita: es la clave del vínculo con `auth.users` y el destinatario de las invitaciones pendientes, así que cambiarlo exigiría reverificación y una transición explícita que todavía no está implementada. Si Supabase falla, el nombre local ya guardado no se revierte: el metadato remoto solo alimenta el nombre mostrado.
- **Contraseña**: exige la contraseña actual y **reautentica** con `grant_type=password` antes de llamar a `PUT /auth/v1/user`. GoTrue aceptaría el cambio solo con el access token, por lo que una sesión robada bastaría para secuestrar la cuenta; la reautenticación cierra ese hueco. Al terminar se borran las cookies y se obliga a iniciar sesión de nuevo. La ruta está incluida en el rate limiter local (`/cuenta/clave`) para que la verificación de la contraseña actual no se convierta en un oráculo de fuerza bruta.
- **Organizaciones**: lista las membresías activas y marca cuál está seleccionada. La cookie de organización se contrasta contra las membresías reales, de modo que una cookie manipulada nunca marca como activa una empresa ajena.

`clear_auth_cookies` acepta la petición para descartar una renovación de token pendiente: sin eso, `RefreshedAuthCookieMiddleware` reescribía las cookies justo después de borrarlas y el cierre de sesión no surtía efecto cuando el access token se había renovado en esa misma petición.

El cierre de sesión es *best-effort* frente a Supabase: si GoTrue no responde, la sesión local se cierra igualmente y nunca se deja al usuario dentro por un fallo del proveedor.

Una membresía `lectura` puede consultar datos, pero el ORM rechaza tanto `flush` como `UPDATE`/`DELETE` masivos.

Para recuperación, `COTIZAT_PUBLIC_URL` debe ser un origen HTTPS fijo y su ruta `https://<origen>/restablecer-clave` debe añadirse a las Redirect URLs permitidas en Supabase Auth. No se deriva desde `Host`, para evitar envenenar el enlace enviado por email. El access token temporal solo cruza el navegador y el backend durante el cambio; no se persiste.

La confirmación de registro usa `redirect_to = https://<origen>/acceso` (en `registrar_cuenta`), así que **esa ruta también debe estar en las Redirect URLs**. Son dos destinos: `/restablecer-clave` (recuperación) y `/acceso` (confirmación de alta). GoTrue valida por coincidencia exacta: sin barra final ni `www`. Si falta alguna, el enlace del email cae al Site URL (`/`) y, aunque `recovery_redirect.js` rescata el fragmento de recuperación, la confirmación de registro puede parecer rota (el usuario no queda confirmado y el login devuelve «Email, contraseña o sesión no válidos»).

### Fallo observado y corregido: el enlace del email llevaba al login

**Causa real (bug propio):** `redirect_to` se enviaba dentro del **cuerpo JSON** de `POST /auth/v1/recover`. GoTrue no lo lee ahí. Su struct `RecoverParams` (`internal/api/recover.go`) solo declara:

```go
type RecoverParams struct {
    Email               string `json:"email"`
    CodeChallenge       string `json:"code_challenge"`
    CodeChallengeMethod string `json:"code_challenge_method"`
}
```

No hay campo `redirect_to`, así que el valor se descartaba **en silencio** (sin error ni aviso) y GoTrue caía al **Site URL**. El cliente oficial `auth-js` lo envía como **parámetro de query** (`src/lib/fetch.ts`: `qs['redirect_to'] = options.redirectTo`).

La corrección envía la URL donde GoTrue sí la lee:

```text
POST /auth/v1/recover?redirect_to=https%3A%2F%2F<origen>%2Frestablecer-clave
body: {"email": "..."}
```

Lo mismo aplicaba a `POST /auth/v1/signup`: `SignupParams` tampoco declara `redirect_to`, por lo que el email de confirmación también caía al Site URL. Corregido igual.

### Fallo observado y corregido: «Supabase no pudo crear la cuenta»

**Síntoma:** el registro, que antes funcionaba, empezó a fallar siempre con ese
mensaje en staging. No era una clave caducada ni configuración perdida: era un
**bug propio de parseo** que se destapó al activar «Confirm email» en el proyecto.

`POST /auth/v1/signup` responde **HTTP 200 con tres formas distintas**
(`internal/api/signup.go`), y solo una anida el usuario bajo `user`:

| Situación | Respuesta de GoTrue | Forma del JSON |
| --- | --- | --- |
| Autoconfirm activo | `sendJSON(w, 200, token)` | `{access_token, refresh_token, user:{...}}` |
| Confirmación por email, alta nueva | `sendJSON(w, 200, user)` | usuario **en la raíz**, sin tokens |
| Email ya registrado sin confirmar | `sendJSON(w, 200, sanitizedUser)` | usuario **en la raíz**, `identities: []` |

`sign_up` leía siempre `payload["user"]`, así que los dos últimos casos —ambos
respuestas correctas— se convertían en `InvalidCredentials`. Mientras el
proyecto estuvo en autoconfirm el registro funcionaba; al exigir confirmación,
falló el 100% de las veces.

La corrección acepta el usuario en la raíz cuando no viene envuelto y solo trata
como error una respuesta sin identidad utilizable. El caso «email ya registrado»
se detecta por `identities: []` (el usuario obfuscado que GoTrue devuelve para no
revelar qué direcciones existen) y se expone como `SignupResult.ya_registrado`.

**La bandera no cambia el mensaje que ve la persona.** Diferenciar el aviso
permitiría enumerar qué emails tienen cuenta, justo lo que GoTrue evita. `/registro`
responde siempre lo mismo: revisa tu email para confirmar la cuenta y, si ya tenías
una, inicia sesión o usa «Olvidé mi contraseña».

Cubierto por `tests/test_auth.py`: las tres formas de respuesta más el cuerpo sin
identidad. Con el código anterior, dos de esas pruebas fallan con el mensaje exacto
que se reportó.

Efecto secundario que confundía el diagnóstico: al caer al Site URL (`/`), que exige sesión, la app rebotaba a `/acceso`, y el navegador arrastraba el fragmento en cada salto. Se aterrizaba en:

```text
/acceso?next=/#access_token=...&type=recovery
```

El fragmento (`#…`) **nunca viaja al servidor**, así que ninguna ruta podía leerlo: el login lo ignoraba y el enlace parecía roto aunque el token fuera válido. Esto hacía que el fallo se pareciese mucho a una Redirect URL sin autorizar; conviene descartar primero el formato de la petición.

Tener la Redirect URL autorizada en Authentication → URL Configuration **sigue siendo obligatorio** (GoTrue valida contra esa lista), pero no era la causa aquí. `/readyz` publica el valor exacto esperado en `recovery_redirect_url_esperada`.

Red de seguridad en la aplicación: `app/static/js/recovery_redirect.js` se carga en el login y en el layout general; si detecta `type=recovery` con `access_token` en el fragmento, reenvía a `/restablecer-clave` conservándolo. Un enlace caducado (sin token y con `error`) se desvía a `/recuperar-acceso` con un mensaje claro en lugar de dejar a la persona en el login. El token permanece siempre en el fragmento: no pasa a la query, donde quedaría registrado en logs o en el `Referer`.

## Invitaciones y administración de equipo

La revisión `a84d2f6b91e0` añade `invitaciones_organizacion` y `/equipo` permite administrar miembros con estas reglas:

- propietarios y administradores pueden invitar miembros o usuarios de solo lectura;
- solo la persona propietaria puede otorgar o modificar el rol `administrador`;
- la membresía propietaria no se desactiva, degrada ni transfiere desde esta pantalla;
- cada invitación caduca en 7 días, es de un solo uso y cualquier enlace anterior para el mismo email queda revocado;
- PostgreSQL recibe únicamente SHA-256 del secreto; el token original se muestra una sola vez;
- aceptar exige una sesión Supabase cuyo email verificado coincida exactamente con el invitado;
- la vista pública no consulta la invitación, por lo que no confirma si un token existe, y responde con `Cache-Control: no-store` y `Referrer-Policy: no-referrer`.

Los enlaces se construyen desde `COTIZAT_PUBLIC_URL`, nunca desde `Host`. Aún no hay proveedor transaccional de correo: el gestor debe copiar el enlace y compartirlo por un canal seguro. No se incorporó una clave `service_role` ni se usó el endpoint administrativo de Supabase para simular el envío. Antes de una beta debe integrarse y probarse un canal de email real o establecer un procedimiento operativo controlado.

## RLS: implementación y límite actual

`c93e7a4d20f1` versiona `cotizat_app` sin login, contraseña ni `BYPASSRLS`, privilegios mínimos, funciones con `search_path` fijo y políticas por tenant/rol. La identidad se instala en la transacción solo después de validar Supabase; la organización se instala solo después de comprobar la membresía. El alta de perfil, la primera organización y la aceptación de invitaciones tienen políticas específicas para no depender de un contexto tenant que todavía no existe.

`d7f2a9c41e63` corrige la aceptación de invitaciones: PostgreSQL evalúa el `USING` de las políticas SELECT como `WITH CHECK` sobre la fila nueva de un UPDATE, y `cotizat_invitation_select_recipient` exigía `accepted_at IS NULL` —justo lo que el UPDATE de aceptación elimina—, lo que producía `InsufficientPrivilege` (500) al pulsar «Aceptar invitación». La política ahora muestra al destinatario su invitación también después de aceptarla (solo si la aceptó él); el consumo del token de un solo uso no cambia.

`e1a4b7c9d2f0` hace permanente el arreglo operativo de `alembic_version`: desactiva RLS en esa tabla de metadatos y concede únicamente `SELECT` a `cotizat_app`. Así el login `cotizat_runtime` puede comprobar el head en `/readyz` sin abrir ningún acceso a datos de tenants. Para SQL Editor está disponible `docs/staging_upgrade_e1a4b7c9d2f0.sql`.

El proyecto real confirmó previamente `relrowsecurity = true` y que `anon` obtuvo cero partidas. Tras el cierre del incidente de invitaciones, Supabase quedó en `d7f2a9c41e63` y el flujo de aceptación se probó con el login runtime limitado. `e1a4b7c9d2f0` ya está **aplicada y desplegada**: Supabase confirmó `relrowsecurity = false`, `relforcerowsecurity = false` y `SELECT` para `cotizat_app` en `public.alembic_version`, y `/readyz` en producción responde `"alembic": "head:e1a4b7c9d2f0"` con `"rol_runtime": "superuser=False, bypassrls=False, inherit=True, cotizat_app=True"`. El PR #16 que versiona este endurecimiento está fusionado en `main`.

## Estado de validación real

Las revisiones hasta `e1a4b7c9d2f0` están aplicadas y desplegadas en el proyecto real. `/healthz` y `/readyz` responden **200 OK** en producción; `/readyz` devuelve `"alembic": "head:e1a4b7c9d2f0"` y `"rol_runtime": "superuser=False, bypassrls=False, inherit=True, cotizat_app=True"`. El PR #16 está fusionado en `main` (commit `bb84767`). La comprobación en producción sustituye la que el sandbox no puede ejecutar (cierra TLS hacia Supabase antes de autenticar).

## Trabajo de seguridad todavía obligatorio

Esta integración no autoriza por sí sola un despliegue público. Cerrado en esta
etapa:

- la migración de invitaciones `d7f2a9c41e63` está aplicada y el flujo de
  aceptación probado (incidente del 500 resuelto);
- el head `e1a4b7c9d2f0` está aplicado y desplegado, y `/readyz` lo confirma con
  el rol runtime no privilegiado.

Siguen pendientes:

- validar el recorrido real de invitaciones con dos emails, incluido su canal de
  entrega (hoy el gestor copia el enlace y lo comparte manualmente);
- sustituir/complementar el límite local por IP con contadores distribuidos
  antes de escalar a varias instancias;
- validar en el navegador HTTPS real la CSP sin `unsafe-inline` y la auditoría
  XSS ya automatizada;
- validar el cruce de lectura/escritura con dos organizaciones y el acceso
  denegado a la URL pública del bucket privado de Storage.

CSRF por origen, cabeceras defensivas, almacenamiento privado y autorización de descargas ya están implementados en código, pero aún requieren validación en el despliegue real.
