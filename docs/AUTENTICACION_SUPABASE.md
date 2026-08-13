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
- `/salir`: elimina access token, refresh token y organización seleccionada.

Una membresía `lectura` puede consultar datos, pero el ORM rechaza tanto `flush` como `UPDATE`/`DELETE` masivos.

Para recuperación, `COTIZAT_PUBLIC_URL` debe ser un origen HTTPS fijo y su ruta `https://<origen>/restablecer-clave` debe añadirse a las Redirect URLs permitidas en Supabase Auth. No se deriva desde `Host`, para evitar envenenar el enlace enviado por email. El access token temporal solo cruza el navegador y el backend durante el cambio; no se persiste.

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

El proyecto real confirmó previamente `relrowsecurity = true` y que `anon` obtuvo cero partidas. Sin embargo, su head continúa en `9bca2ad1f6e4`: allí la conexión usada por el backend/migraciones todavía entra como `postgres` y omite RLS. La nueva migración y el login limitado no se han probado contra ese PostgreSQL. Consulta el procedimiento y sus límites en `docs/BASE_DE_DATOS_WEB.md`.

## Estado de validación real

La revisión `9bca2ad1f6e4` está aplicada en el proyecto real. El checkout actual no contiene `.env` (Arena lo recreó al reanudar la sesión) y el sandbox cierra tanto PostgreSQL como TLS hacia Supabase antes de autenticar; por eso registro, login, recuperación e invitaciones deben probarse desde el futuro despliegue o un runner con esa salida. Las pruebas unitarias simuladas no sustituyen esa comprobación.

## Trabajo de seguridad todavía obligatorio

Esta integración no autoriza por sí sola un despliegue público. Siguen pendientes:

- probar registro/login/recuperación end-to-end desde un entorno con salida HTTPS a Supabase;
- configurar `COTIZAT_PUBLIC_URL` y la Redirect URL real en Supabase;
- sustituir/complementar el límite local por IP ya implementado con contadores distribuidos antes de escalar a varias instancias (el rate limit de Supabase tampoco sustituye el control de aplicación);
- aplicar/probar la migración de invitaciones y validar el recorrido real con dos emails, incluido su canal de entrega;
- aplicar y probar `c93e7a4d20f1` con un login runtime realmente no privilegiado y dos organizaciones;
- retirar `unsafe-inline` de estilos (scripts ya usan nonce) y completar auditoría XSS;
- aplicar/probar la migración y el bucket privado de Storage real.

CSRF por origen, cabeceras defensivas, almacenamiento privado y autorización de descargas ya están implementados en código, pero aún requieren validación en el despliegue real.
