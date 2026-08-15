# Aprovisionamiento de staging (Vercel + Supabase)

Esta guía ejecuta el orden obligatorio de
[`CONTINUIDAD_STAGING_SUPABASE.md`](CONTINUIDAD_STAGING_SUPABASE.md) (Pasos A–F)
desde un equipo con salida TLS a Supabase y Vercel. **No** contiene secretos:
las contraseñas y claves se pegan solo en el gestor de secretos (Vercel/SQL
Session), nunca en el chat, el repositorio ni los logs.

Origen: trabajar desde el `main` que incorpora el PR #1 (o una rama efímera
para el backup). El sandbox de Arena no puede contactar con Supabase, así que
estos pasos son manuales.

> **No relajar nunca** CSRF, CSP, RLS, el bucket privado ni
> `COTIZAT_REQUIRE_RLS_ROLE` para «hacer arrancar» staging. Si falla, se
> corrige la infraestructura.

## 0. Verificación previa (sin secretos en el chat)

Antes de tocar nada, confirma que las variables existen en tu gestor de
secretos y que **ninguna** se imprime por pantalla:

```bash
# Solo comprueba presencia/ausencia de claves; no revela valores.
env | grep -E '^(DATABASE_URL|MIGRATION_DATABASE_URL|SUPABASE_URL|SUPABASE_PUBLISHABLE_KEY|SUPABASE_SECRET_KEY|COTIZAT_PUBLIC_URL)=' | cut -d= -f1 | sort
```

La app expone dos fronteras de salud (sin autenticación, sin datos de tenant):

| Endpoint | Uso |
| --- | --- |
| `/healthz` | Liveness: el proceso responde. No toca la base de datos. |
| `/readyz` | Readiness: Auth, Storage, COTIZAT_PUBLIC_URL, conexión PostgreSQL, head de Alembic (`d7f2a9c41e63`) y rol runtime (miembro de `cotizat_app`, `NOSUPERUSER`, `NOBYPASSRLS`, `INHERIT`). |

`/readyz` devuelve **503** si el despliegue no debe recibir tráfico; **200** no
sustituye la matriz de aceptación con dos correos y dos organizaciones.

## Paso A — Integrar y respaldar

1. Fusiona el PR #1 y obtén el `main` actualizado.
2. **Respaldo recuperable antes de migrar**: desde el panel de Supabase,
   Database → Backups → “Create a backup”/descarga, o bien desde un equipo con
   salida TLS (el `.dump` se guarda **fuera** del repositorio):

   ```bash
   # Sustituye <admin> y <host>; la contraseña se pide de forma interactiva
   # para que no quede en el historial del shell. NO la pegues aquí.
   pg_dump "postgresql://<admin>@<host>:5432/postgres?sslmode=require" \
     --format=custom --no-owner --no-privileges \
     --file "backups/cotizat-pre-staging-$(date -u +%Y%m%dT%H%M%SZ).dump"
   ```

3. `backups/`, `*.dump`, `.env` y cualquier URL con contraseña ya están
   excluidos por `.gitignore`. No los fuerces.

## Paso B — Aplicar migraciones

`MIGRATION_DATABASE_URL` se usa **solo** durante Alembic y debe apuntar a un
rol administrativo. Nunca llega al runtime web.

```bash
# Exporta la URL administrativa SOLO en esta terminal/sesión; no la dejes en
# el entorno de Vercel. Pide la contraseña de forma interactiva si puedes.
export MIGRATION_DATABASE_URL='postgresql://<admin>@<host>:5432/postgres?sslmode=require'

alembic current          # antes: c93e7a4d20f1 (conocido) o inferior
alembic upgrade head
alembic current          # OBLIGATORIO que imprima: d7f2a9c41e63

unset MIGRATION_DATABASE_URL
```

Resultado obligatorio documentado:

```text
d7f2a9c41e63
```

## Paso C — Crear el login runtime

Con una sesión SQL administrativa en Supabase (SQL Editor o `psql`), ejecuta
este bloque **idempotente**. La contraseña se asigna en el panel/SQL Session
del propietario, no se pega en el chat:

```sql
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'cotizat_runtime') THEN
    CREATE ROLE cotizat_runtime
      LOGIN
      INHERIT
      NOSUPERUSER
      NOCREATEDB
      NOCREATEROLE
      NOREPLICATION
      NOBYPASSRLS;
  ELSE
    ALTER ROLE cotizat_runtime
      INHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
  END IF;
END
$$;

GRANT cotizat_app TO cotizat_runtime;

-- Asigna la contraseña en el panel de Supabase o con \password cotizat_runtime
-- (psql interactivo). No la escribas en este script ni en el chat.
```

Verificación obligatoria (sin imprimir la contraseña):

```sql
SELECT rolname, rolsuper, rolbypassrls, rolinherit
FROM pg_roles
WHERE rolname = 'cotizat_runtime';
-- Se exige: rolsuper=false, rolbypassrls=false, rolinherit=true.

SELECT pg_has_role('cotizat_runtime', 'cotizat_app', 'member');  -- true
```

Restricciones:

- `cotizat_runtime` **no** puede ser propietario de tablas (lo crea Alembic con
  el rol administrativo).
- No uses `postgres`, `service_role` ni un login con `BYPASSRLS` como
  `DATABASE_URL`.

## Paso D — Storage privado `cotizat-private`

El bucket debe ser `public=false` y con límite de 12 MB. No añadas políticas
públicas para `anon`/`authenticated`: el backend usa la clave `sb_secret_` y
el proxy `/archivos/...` es la frontera de autorización.

Puedes crearlo desde el panel (Storage → New bucket: `cotizat-private`,
**Private**, file size limit 12 MB) o con el siguiente helper desde un equipo
con salida TLS (usa la clave secret en una variable de entorno, no en
argumentos visibles):

```bash
export SUPABASE_URL='https://<proyecto>.supabase.co'
read -s SUPABASE_SECRET_KEY   # sb_secret_...; no se imprime
export SUPABASE_SECRET_KEY
python -m app.tools.ensure_bucket   # verifica o crea cotizat-private
unset SUPABASE_SECRET_KEY
```

Compruebo que el bucket quedó privado (la respuesta debe incluir
`"public": false`):

```bash
# Requiere SUPABASE_URL y SUPABASE_SECRET_KEY exportados.
python -m app.tools.ensure_bucket --check
```

## Paso E — Proyecto de staging en Vercel

- Proyecto **separado** de producción, idealmente con Deployment Protection
  activada (Vercel Authentication) para que no sea público antes de pasar la
  matriz.
- Vercel detecta `app/main.py` como entrada FastAPI; `vercel.json` ya declara
  el framework y `maxDuration` de 60 s.
- URL estable, por ejemplo `https://cotizat-staging.vercel.app`.

Variables **solo** en Settings → Environment Variables (entorno Production/
Preview del proyecto de staging):

```dotenv
DATABASE_URL=postgresql://cotizat_runtime:<secreto>@<host>:5432/postgres?sslmode=require
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

Nunca configures en runtime:

- `MIGRATION_DATABASE_URL`;
- una conexión `postgres`/administrativa como `DATABASE_URL`;
- `service_role` ni `sb_secret_` en variables públicas del frontend;
- `COTIZAT_REQUIRE_RLS_ROLE=false` como atajo.

Después de fijar las variables, haz un redeploy. Abre:

```text
https://<staging-estable>/healthz   # 200 {"ok": true, ...}
https://<staging-estable>/readyz    # 200 {"ok": true, ...}
```

Si `/readyz` responde 503, lee sus `errors`: indicará si falta el head de
Alembic, el rol runtime es privilegiado, falta configurar Auth/Storage o
falta `COTIZAT_PUBLIC_URL`.

## Paso F — Auth (Site URL y Redirect URL)

En Supabase → Authentication → URL Configuration:

```text
Site URL:      https://<staging-estable>
Redirect URL:  https://<staging-estable>/restablecer-clave
```

La Redirect URL debe coincidir carácter a carácter (esquema, dominio, ruta, sin
barra final). Si falta, Supabase **no da error**: descarta `redirect_to`, envía
el enlace al Site URL y el correo de recuperación acaba en la pantalla de
login. Comprueba el valor exacto que espera la app en `/readyz`, campo
`recovery_redirect_url_esperada`.

Haz un nuevo redeploy de Vercel después de guardar.

## Aceptación real (matriz)

Antes de declarar staging validado, ejecuta la matriz de 14 puntos de
`CONTINUIDAD_STAGING_SUPABASE.md` §4 con **dos correos verificados** y
**dos organizaciones**, usando solo datos ficticios. En particular:

- cookies `Secure`/`HttpOnly` y 403 en escrituras cross-site;
- el objeto de A devuelve 404 bajo B;
- DevTools sin violaciones CSP;
- el bucket no entrega objetos sin pasar por CotizaT;
- el arranque falla si se sustituye temporalmente `DATABASE_URL` por un rol
  con `BYPASSRLS` o fuera de `cotizat_app` (pruébalo sin exponer
  credenciales; `/readyz` también debe pasar a 503 con ese rol).

## Pendientes explícitos (no bloquean el staging inicial)

- Redis/Upstash para rate limiting distribuido antes de múltiples instancias
  o exposición pública.
- Importación explícita de instalaciones SQLite y sus objetos
  (E1W-012).
- Smoke tests HTTPS automatizados de Auth/rutas/CSP donde sea viable.
- Validación real de CSP/interacciones en navegador.
