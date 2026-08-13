# Autenticación web con Supabase

CotizaT separa tres responsabilidades que no deben confundirse:

1. **Supabase Auth** valida email/contraseña y emite la sesión.
2. **CotizaT** vincula el UUID de `auth.users` con `usuarios.auth_user_id` y autoriza una organización mediante `membresias`.
3. **SQLAlchemy** activa `organizacion_id` en la sesión, filtra todas las entidades empresariales y rechaza escrituras cruzadas.

La contraseña y los tokens de sesión no se guardan en PostgreSQL. Los tokens se mantienen en cookies `HttpOnly`, `Secure` y `SameSite=Lax`; la clave secreta de Supabase no participa en el login.

## Variables del servidor

```bash
DATABASE_URL=postgresql://...
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_...
COTIZAT_COOKIE_SECURE=true
```

`SUPABASE_PUBLISHABLE_KEY` tiene privilegios bajos y puede usarse para Auth. No se debe sustituir por `sb_secret_...`, `service_role` ni otra clave que omita RLS.

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
- `/organizaciones/nueva`: crea la primera organización y una membresía `propietario`.
- `/organizaciones`: enumera solo membresías y organizaciones activas.
- `/organizaciones/{id}/seleccionar`: vuelve a comprobar la membresía antes de escribir la cookie de selección.
- Rutas comerciales: `get_db` ignora `COTIZAT_ORGANIZATION_ID` en PostgreSQL y deriva usuario, rol y organización de la sesión autenticada.
- `/salir`: elimina access token, refresh token y organización seleccionada.

Una membresía `lectura` puede consultar datos, pero el ORM rechaza tanto `flush` como `UPDATE`/`DELETE` masivos.

## RLS: estado y límite actual

El proyecto real confirmó `relrowsecurity = true` y el rol `anon` obtuvo cero partidas sin políticas permisivas. Es una denegación predeterminada correcta.

La conexión Session pooler utilizada para migraciones entra como `postgres`, rol administrativo que omite RLS. Por eso:

- el navegador público queda bloqueado por RLS;
- el backend debe comprobar Auth + membresía y mantener el filtro ORM;
- RLS todavía no es una segunda barrera frente a un error del backend conectado como `postgres`.

Antes de publicar se debe crear un rol de aplicación sin `BYPASSRLS` y políticas basadas en membresías/JWT, o establecer de forma segura los claims por transacción. No se crearán políticas públicas de tipo `USING (true)`.

## Estado de validación real

La revisión `9bca2ad1f6e4` está aplicada y `SUPABASE_URL`/`SUPABASE_PUBLISHABLE_KEY` quedaron configuradas localmente sin entrar en Git. El sandbox actual cierra tanto los puertos PostgreSQL como el TLS hacia dominios Supabase antes de autenticar; por eso la prueba end-to-end de GoTrue debe ejecutarse desde el futuro entorno de despliegue o un runner con esa salida de red. Las pruebas unitarias usan respuestas Auth simuladas y no sustituyen esa comprobación.

## Trabajo de seguridad todavía obligatorio

Esta integración no autoriza por sí sola un despliegue público. Siguen pendientes:

- probar registro/login end-to-end desde un entorno con salida HTTPS a Supabase (la revisión y variables ya están configuradas);
- protección CSRF para todos los formularios mutables;
- cabeceras de seguridad y límites de login;
- recuperación de contraseña y URLs de redirección por entorno;
- gestión de invitaciones y roles administrativos;
- políticas RLS autorizantes para un rol no privilegiado;
- almacenamiento privado de objetos y autorización de descargas.
