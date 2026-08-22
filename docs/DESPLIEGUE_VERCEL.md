# Despliegue en Vercel

CotizaT se despliega en Vercel como una única función FastAPI (framework
preset **FastAPI**, entrypoint auto-detectado `app/main.py`). El repositorio
incluye `vercel.json` con la configuración base (`maxDuration` de 60 s para
que la generación de PDFs y Excel no caduque en cuentas con límite de tiempo).

## Variables de entorno obligatorias (producción)

Vercel monta el código en un sistema de archivos **de solo lectura**; solo
`/tmp` admite escritura. Por eso la versión web **no puede usar SQLite** y
necesita la configuración PostgreSQL + Supabase descrita en
`docs/BASE_DE_DATOS_WEB.md` y `docs/AUTENTICACION_SUPABASE.md`:

| Variable | Valor |
| --- | --- |
| `DATABASE_URL` | `postgresql://cotizat_runtime.<ref>:…@aws-0-<region>.pooler.supabase.com:6543/postgres?sslmode=require` (Supabase pooler en modo **Transaction**, puerto 6543, login sin privilegios miembro de `cotizat_app`, sin `BYPASSRLS`) |
| `SUPABASE_URL` | `https://tu-proyecto.supabase.co` |
| `SUPABASE_PUBLISHABLE_KEY` | clave `sb_publishable_…` |
| `SUPABASE_SECRET_KEY` | clave `sb_secret_…` (solo backend, nunca en el navegador) |
| `COTIZAT_STORAGE_BACKEND` | `supabase` |
| `SUPABASE_STORAGE_BUCKET` | `cotizat-private` |
| `COTIZAT_PUBLIC_URL` | `https://tu-proyecto.vercel.app` (origen exacto para enlaces de recuperación) |
| `COTIZAT_COOKIE_SECURE` | `true` |
| `COTIZAT_TRUST_PROXY` | `true` (Vercel saneado de `X-Forwarded-For` para el limitador) |
| `COTIZAT_REQUIRE_RLS_ROLE` | `true` |
| `UPSTASH_REDIS_REST_URL` | `https://tu-base.upstash.io` (contador de intentos compartido) |
| `UPSTASH_REDIS_REST_TOKEN` | token REST de Upstash (solo backend) |
| `COTIZAT_REQUIRE_DISTRIBUTED_RATELIMIT` | `true` |

> `MIGRATION_DATABASE_URL` es solo para migrar localmente; **no** debe
> configurarse en Vercel.

> Las tres últimas variables no son opcionales en Vercel. Sin ellas el límite
> de intentos de acceso se cuenta en la memoria de cada invocación, y como cada
> invocación puede ser un proceso nuevo, el contador arranca de cero y deja de
> frenar los intentos de contraseña. Con `COTIZAT_REQUIRE_DISTRIBUTED_RATELIMIT=true`
> el propio `/readyz` avisa respondiendo 503 si faltan.

### Variables vacías o heredadas

Vercel crea variables presentes pero **vacías** si pegas una lista sin valor
o importas un `.env` incompleto. Eso puede romper el arranque (p. ej. una
`COTIZAT_ORGANIZATION_ID` vacía hacía fallar cada petición con 500). La
aplicación ya trata una variable vacía como «no configurada», pero conviene
revisar **Settings → Environment Variables** y eliminar las claves que no
tengan valor real. `COTIZAT_ORGANIZATION_ID` solo aplica al modo SQLite
local: en la versión web con PostgreSQL se ignora y no hace falta definirla.

## Migración del esquema (una vez, antes del primer uso)

La app comprueba al arrancar que PostgreSQL ya tiene el esquema versionado;
si falta o está desfasado, falla con un mensaje claro. El orden completo
(backup, rol runtime limitado, bucket privado, variables y Auth) está en
[`APROVISIONAMIENTO_STAGING.md`](APROVISIONAMIENTO_STAGING.md). Ejecuta desde
tu máquina, usando la URL administrativa **solo** para Alembic:

```bash
MIGRATION_DATABASE_URL=postgresql://administrador:…@host:5432/cotizat \
alembic upgrade head
```

## Endpoints de salud

- `GET /healthz` — liveness: responde 200 si el proceso está vivo (no toca la
  base de datos).
- `GET /readyz` — readiness: comprueba la configuración de Auth, Storage y
  `COTIZAT_PUBLIC_URL`, la conexión PostgreSQL, el head de Alembic esperado y
  que el rol runtime sea un miembro no privilegiado de `cotizat_app`
  (`NOSUPERUSER`, `NOBYPASSRLS`, `INHERIT`).

Devuelve `200` cuando está listo y `503` con un array `errors` (sin secretos)
si el despliegue no debe recibir tráfico. Las respuestas llevan
`Cache-Control: no-store` para que los balanceadores no cacheen un estado
viejo. Un `200` en `/readyz` no sustituye la matriz de aceptación con dos
correos y dos organizaciones.

## ¿Qué pasa si no configuras `DATABASE_URL`?

Antes, la aplicación ni siquiera arrancaba (error 500 en todas las rutas)
porque intentaba crear `app/static/uploads` en el sistema de solo lectura.
Ahora:

- Con `DATABASE_URL` (PostgreSQL): arranca con normalidad; ninguna escritura
  local. Las rutas heredadas `/static/uploads/*` devuelven 404 y los archivos
  pasan por el proxy privado `/archivos/…` (Supabase Storage).
- Sin `DATABASE_URL`: arranca en **modo efímero** — los datos SQLite se
  guardan en `/tmp/cotizat` y **se pierden al reiniciar** cada instancia.
  Sirve solo para previsualizar el despliegue; producción siempre con
  PostgreSQL.

## Trabajo programado (cron de recordatorios)

> **Estado (19/08/2026): operativo.** PR #40 fusionado y desplegado en
> producción, `CRON_SECRET` en Production y job visible en Settings → Cron
> Jobs; primera ejecución automática el 19/08 a las 13:00 UTC. Lo siguiente
> sigue valiendo como referencia de funcionamiento y diagnóstico.

Dos trabajos programados disparan Vercel Cron desde `vercel.json` → `crons`
(el plan Hobby admite hasta 2 trabajos diarios; Pro hasta 40):

| Trabajo | Ruta | Horario | Qué hace |
|---|---|---|---|
| Recordatorios de vencimiento | `/api/cron/recordatorios-vencimiento` | `0 13 * * *` (13:00 UTC) | Emails a 5 y 1 día del vencimiento de licencia |
| Mantenimiento diario (E4-021/E4-023) | `/api/cron/mantenimiento` | `0 2 * * *` (02:00 UTC) | Respaldo automático por organización + verificación de `/readyz` con alerta por correo a los operadores |

Ambas rutas viven en `app/routers/admin.py` (`tests/test_vercel_cron_config.py`
comprueba en CI que cada ruta declarada existe y responde GET, y que su
horario es válido para Hobby).

- Autenticación: cada invocación lleva `Authorization: Bearer $CRON_SECRET`;
  sin esa variable en el proyecto, las rutas responden 401 y no hacen nada.

**Para que el cron exista hacen falta tres cosas a la vez** (si falta una, la
pestaña Cron Jobs de Vercel puede aparecer vacía o el cron fallar al ejecutarse):

1. El despliegue de **producción** (no un Preview) debe contener el
   `vercel.json` con `crons`: se crea en el despliegue, no en el panel.
2. `CRON_SECRET` añadida en **Settings → Environment Variables** (Production)
   con un valor fuerte (`openssl rand -base64 32`).
3. **Redeploy** después de añadir la variable (se lee al arrancar).

Verificación rápida desde el despliegue (no hace falta entrar al panel):

```bash
curl -s https://tu-proyecto.vercel.app/readyz | python -m json.tool
```

En `checks` aparecen `cron_secret` (`configurado`/`no-configurado`) y `cron`
(p. ej. `/api/cron/recordatorios-vencimiento:registrada`). Si `cron_secret` es
`no-configurado`, el cron nunca podrá autenticarse aunque aparezca en el panel.

## Subir una versión nueva

Conecta el repositorio a Vercel (o usa `vercel deploy`). Cada `git push`
genera un despliegue; la rama de producción se despliega automáticamente.
No hace falta configurar nada del runtime: `vercel.json` ya declara el
framework y el timeout de la función.
