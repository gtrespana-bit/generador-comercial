# Continuidad exacta: staging Vercel + Supabase

Fecha de corte: 13/08/2026 (America/Caracas).

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

Última validación local antes de este documento:

```text
145 passed
```

También pasaron compilación Python, parseo Jinja, `node --check` y
`git diff --check`. `.env` y `presupuestos.db` no forman parte del repositorio.

### Preparación de staging añadida desde el sandbox (14/08/2026)

Sin contactar con Supabase/Vercel (el sandbox no tiene salida TLS a esos
servicios) y sin imprimir secretos, se dejó listo:

- `/healthz` (liveness) y `/readyz` (readiness) sin autenticación. `/readyz`
  verifica configuración de Auth/Storage/`COTIZAT_PUBLIC_URL`, conexión
  PostgreSQL, head de Alembic (`c93e7a4d20f1`) y que el login runtime sea
  miembro no privilegiado de `cotizat_app`; devuelve 503 con `errors` sin
  secretos si algo falta.
- `app/tools/ensure_bucket.py` para verificar o crear `cotizat-private`
  (`public=false`, 12 MB) desde un equipo con salida TLS.
- `docs/APROVISIONAMIENTO_STAGING.md` con el orden A–F paso a paso (backup,
  migraciones, rol runtime idempotente, bucket, variables de Vercel y Auth).

La suite local quedó en `155 passed` y siguen pasando compilación Python,
parseo Jinja con el entorno real, `node --check` y `git diff --check`.

El PR de integración es:

```text
https://github.com/gtrespana-bit/generador-comercial/pull/1
```

Después de fusionarlo, una conversación nueva debe trabajar desde el `main`
resultante y no intentar reconstruir los cambios desde el chat.

## 2. Estado externo conocido y no confirmado todavía

Último estado real conocido de Supabase:

```text
Alembic remoto: 9bca2ad1f6e4
Alembic esperado por el código: c93e7a4d20f1
```

Las revisiones posteriores encadenan Storage privado, invitaciones y RLS. No se
debe afirmar que están aplicadas hasta comprobar `alembic current` contra el
proyecto real.

Pendientes externos:

1. respaldo recuperable de Supabase;
2. `alembic upgrade head` con URL administrativa;
3. login `cotizat_runtime` limitado y miembro de `cotizat_app`;
4. bucket privado `cotizat-private`;
5. proyecto de staging HTTPS en Vercel;
6. Site URL y Redirect URL reales en Supabase Auth;
7. pruebas con dos emails y dos organizaciones;
8. validación de CSP/interacciones en navegador real;
9. rate limiting distribuido antes de escalar a múltiples instancias.

El sandbox de Arena cortó TLS al intentar acceder a Supabase y al descargar
Chromium para Playwright. No repetir esos intentos como si fueran una validación
real: ejecutar las comprobaciones desde Vercel o un equipo con salida TLS.

## 3. Orden obligatorio del siguiente bloque

### Paso A — Integrar y respaldar

1. Fusionar el PR #1.
2. Obtener `main` actualizado.
3. Crear backup administrado o `pg_dump` fuera del repositorio.
4. No guardar dumps, `.env`, URLs con contraseña ni claves en Git.

### Paso B — Aplicar migraciones

Usar solo durante Alembic:

```dotenv
MIGRATION_DATABASE_URL=postgresql://<administrador>@...
```

Ejecutar:

```bash
alembic current
alembic upgrade head
alembic current
```

Resultado obligatorio:

```text
c93e7a4d20f1
```

Retirar `MIGRATION_DATABASE_URL` del entorno después. Nunca debe llegar al
runtime web.

### Paso C — Crear el login runtime

Después de que exista `cotizat_app`:

```sql
CREATE ROLE cotizat_runtime
  LOGIN
  INHERIT
  NOSUPERUSER
  NOCREATEDB
  NOCREATEROLE
  NOREPLICATION
  NOBYPASSRLS;

GRANT cotizat_app TO cotizat_runtime;
```

Asignar la contraseña fuera de Git/chat y verificar:

```sql
SELECT rolname, rolsuper, rolbypassrls, rolinherit
FROM pg_roles
WHERE rolname = 'cotizat_runtime';

SELECT pg_has_role('cotizat_runtime', 'cotizat_app', 'member');
```

Se exige `rolsuper=false`, `rolbypassrls=false`, `rolinherit=true` y membresía
verdadera. `cotizat_runtime` no puede ser propietario de tablas.

### Paso D — Crear Storage privado

Crear en Supabase Storage:

```text
cotizat-private
```

Debe permanecer `public=false`, con límite de 12 MB. No añadir lectura pública
para `anon`/`authenticated`: el backend usa su secret key y el proxy de CotizaT
es la frontera de autorización.

### Paso E — Crear staging Vercel

Vercel reconoce `app/main.py` como entrada FastAPI. Usar un proyecto separado de
staging, idealmente protegido, con URL estable, por ejemplo:

```text
https://cotizat-staging.vercel.app
```

Variables runtime, solo en el gestor de secretos de Vercel:

```dotenv
DATABASE_URL=postgresql://cotizat_runtime:<secreto>@.../?sslmode=require
COTIZAT_REQUIRE_RLS_ROLE=true
SUPABASE_URL=https://<proyecto>.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_...
COTIZAT_STORAGE_BACKEND=supabase
SUPABASE_STORAGE_BUCKET=cotizat-private
SUPABASE_SECRET_KEY=sb_secret_...
COTIZAT_PUBLIC_URL=https://<staging-estable>
COTIZAT_COOKIE_SECURE=true
COTIZAT_TRUST_PROXY=true
```

Nunca configurar en runtime:

- `MIGRATION_DATABASE_URL`;
- una conexión `postgres`/administrativa como `DATABASE_URL`;
- `service_role` o `sb_secret_` en variables públicas del frontend;
- `COTIZAT_REQUIRE_RLS_ROLE=false` como solución de despliegue.

### Paso F — Configurar Auth

En Supabase Auth:

```text
Site URL: https://<staging-estable>
Redirect URL: https://<staging-estable>/restablecer-clave
```

Hacer redeploy después de fijar las variables.

## 4. Matriz de aceptación real

No declarar staging validado hasta completar con dos correos verificados:

1. usuario A se registra, verifica email e inicia/cierra sesión;
2. A crea organización A y completa onboarding limpio o demo;
3. recuperación de contraseña llega y solo redirige al origen fijo;
4. A sube logo, producto/partida con imagen, anexo y ficha PDF;
5. A crea un presupuesto y genera/descarga PDF;
6. A invita a B y B acepta una sola vez con email coincidente y verificado;
7. B con rol `lectura` puede consultar/descargar pero no crear, editar, borrar ni
   provocar efectos de Storage;
8. al cambiar B a `miembro`, puede escribir en la organización autorizada;
9. crear organización B con nombres/números homónimos no mezcla datos con A;
10. una URL/clave de objeto de A solicitada bajo B devuelve 404;
11. cookies Auth son Secure/HttpOnly y las escrituras cross-site devuelven 403;
12. DevTools no muestra violaciones CSP ni fallos de interacción/estilos;
13. el bucket no entrega objetos sin pasar por CotizaT;
14. el arranque falla si se sustituye temporalmente `DATABASE_URL` por un rol con
    `BYPASSRLS` o fuera de `cotizat_app` (probar sin exponer credenciales).

Usar solo datos ficticios durante esta matriz.

## 5. Qué hacer después de la matriz

Si staging pasa:

1. añadir Redis/Upstash para rate limiting distribuido antes de múltiples
   instancias o exposición pública;
2. automatizar smoke tests HTTPS de Auth/rutas/CSP donde sea viable;
3. diseñar y probar importación explícita de instalaciones SQLite y objetos;
4. continuar E1-012 a E1-014 (usabilidad y medición del recorrido web);
5. preparar beta privada controlada, no lanzamiento abierto.

Si staging falla, corregir primero infraestructura o regresión observada; no
relajar CSRF, CSP, RLS, bucket privado ni la exigencia del rol limitado para
hacer que arranque.

## 6. Mensaje sugerido para iniciar una conversación nueva

Copiar este texto, sin añadir secretos:

> Continúa el proyecto CotizaT desde el `main` que incorpora el PR #1. Lee
> `docs/CONTINUIDAD_STAGING_SUPABASE.md` y
> `PLAN_DE_COMERCIALIZACION_Y_EVOLUCION_SAAS.md`, secciones 1.3 y 11. No repitas
> trabajo ya completado. El siguiente objetivo es preparar y validar staging
> Vercel + Supabase siguiendo el orden del documento. Antes de cambiar código,
> verifica el estado real de Alembic, el rol runtime, el bucket y las variables
> sin imprimir secretos. Mantén como pendientes explícitos Redis/Upstash,
> importación SQLite y validación real con dos organizaciones.
