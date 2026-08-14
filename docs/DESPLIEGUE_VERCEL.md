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
| `DATABASE_URL` | `postgresql://cotizat_runtime:…@host:5432/cotizat` (login sin privilegios, miembro de `cotizat_app`, sin `BYPASSRLS`) |
| `SUPABASE_URL` | `https://tu-proyecto.supabase.co` |
| `SUPABASE_PUBLISHABLE_KEY` | clave `sb_publishable_…` |
| `SUPABASE_SECRET_KEY` | clave `sb_secret_…` (solo backend, nunca en el navegador) |
| `COTIZAT_STORAGE_BACKEND` | `supabase` |
| `SUPABASE_STORAGE_BUCKET` | `cotizat-private` |
| `COTIZAT_PUBLIC_URL` | `https://tu-proyecto.vercel.app` (origen exacto para enlaces de recuperación) |
| `COTIZAT_COOKIE_SECURE` | `true` |
| `COTIZAT_TRUST_PROXY` | `true` (Vercel saneado de `X-Forwarded-For` para el limitador) |
| `COTIZAT_REQUIRE_RLS_ROLE` | `true` |

> `MIGRATION_DATABASE_URL` es solo para migrar localmente; **no** debe
> configurarse en Vercel.

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

## Subir una versión nueva

Conecta el repositorio a Vercel (o usa `vercel deploy`). Cada `git push`
genera un despliegue; la rama de producción se despliega automáticamente.
No hace falta configurar nada del runtime: `vercel.json` ya declara el
framework y el timeout de la función.
