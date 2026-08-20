# Base de datos de la versión web

CotizaT mantiene dos caminos explícitos durante la transición:

- **desarrollo/compatibilidad local:** SQLite mediante `COTIZAT_DB`;
- **aplicación web:** PostgreSQL mediante `DATABASE_URL`.

`DATABASE_URL` siempre tiene prioridad. Las URL `postgres://` y `postgresql://` se normalizan al driver Psycopg 3.

## Crear el esquema web

```bash
export DATABASE_URL='postgresql://usuario:clave@servidor:5432/cotizat'
alembic upgrade head
uvicorn app.main:app
```

La aplicación no crea tablas PostgreSQL durante el arranque. Si falta el esquema, se detiene con un mensaje explícito. Esto evita que varias instancias intenten modificarlo simultáneamente.

## Crear una base SQLite aislada para desarrollo

```bash
export COTIZAT_DB=/tmp/cotizat-desarrollo.db
unset DATABASE_URL
python run.py
```

La migración SQLite histórica continúa siendo no destructiva y coloca los datos anteriores en el `Espacio local`. No convierte por sí sola ese archivo en una cuenta web.

## Dependencias

- `requirements.txt`: runtime web y herramientas de migración.
- `requirements-desktop.txt`: compatibilidad temporal con pywebview/Windows.

## Alembic

```bash
# Estado actual
alembic current

# Aplicar versiones pendientes
alembic upgrade head

# Generar una revisión después de modificar modelos
alembic revision --autogenerate -m "descripcion"
```

Toda revisión autogenerada debe inspeccionarse. No se debe ejecutar `create_all` como sustituto de Alembic en PostgreSQL.

## Validación en Supabase

El 13 de agosto de 2026 se aplicó la baseline `5cda50f97ed9` en un proyecto Supabase real. La prueba creó dos organizaciones con una partida homónima, modificó el precio de una de ellas y confirmó los valores desde dos conexiones PostgreSQL físicas diferentes (`pg_backend_pid` distinto). RLS automático quedó activo y el rol `anon` vio cero partidas.

La revisión `9bca2ad1f6e4`, que añade el vínculo con Supabase Auth, también quedó aplicada en el mismo proyecto. El entorno real está en `e1a4b7c9d2f0`, con Storage privado, invitaciones, las políticas RLS/rol de aplicación, la corrección de visibilidad de la invitación aceptada y la lectura segura de `alembic_version` aplicados y verificados con el login runtime limitado. `/readyz` en producción confirma `"alembic": "head:e1a4b7c9d2f0"` y `"rol_runtime": "superuser=False, bypassrls=False, inherit=True, cotizat_app=True"`.

**Actualización 16/08/2026:** el head actual de producción es `f4c1d8e37a95` (E1-060, tabla `licencias` de operador con RLS propia; aplicada con `docs/staging_upgrade_f4c1d8e37a95.sql`). `/readyz` real responde `"alembic": "head:f4c1d8e37a95"` con `ok: true`. Ver `docs/PANEL_DE_OPERADOR.md`.

**Actualización 18/08/2026:** el head de producción pasó a `d4e2f6a8b0c1` (el resumen del plan suma las licencias encadenadas; aplicada con `docs/staging_upgrade_d4e2f6a8b0c1.sql`). `/readyz` respondió `"alembic": "head:d4e2f6a8b0c1"` con `ok: true` tras ese despliegue.

**Actualización 18/08/2026 (tarde):** el head exigido por el runtime pasa a `c7f1a3b9d425` (`compras_plan.licencia_inicio` y `compras_plan.licencia_vence`, para que el comprador descargue su recibo sin leer `licencias`, tabla reservada al operador por RLS). **Pendiente de aplicar en Supabase** con `docs/staging_upgrade_c7f1a3b9d425.sql`; hasta entonces `/readyz` responderá 503 (la guarda de head funciona así a propósito). La migración incluye backfill: las compras ya activadas recuperan su período desde la licencia enlazada.

**Actualización 19/08/2026:** el head exigido por el runtime pasa a `d9e2f3a4b5c6` (apertura LatAm S2: `configuracion.etiqueta_id_fiscal` con default `RIF`, y `configuracion.tasa_cambio` + `configuracion.fecha_tasa` para convertir el catálogo USD a moneda local). El patch de esta sesión **solo** trae esas dos migraciones; sin embargo, los registros de sesiones anteriores indican que en Supabase podían quedar pendientes hasta cuatro scripts previos (ver tabla). Cada `staging_upgrade_*.sql` trae una guarda que comprueba la versión anterior y aborta si no coincide, así que es imposible aplicarlos fuera de orden. Las instalaciones SQLite locales no requieren nada: el sincronizador de columnas del modelo las añade solo.

Orden completo desde la última base verificada (`d4e2f6a8b0c1`, 18/08) hasta el head nuevo:

| # | Script (ejecutar en orden) | Sella | Requiere |
|---|---|---|---|
| 1 | `docs/staging_upgrade_c7f1a3b9d425.sql` | `c7f1a3b9d425` | `d4e2f6a8b0c1` |
| 2 | `docs/staging_upgrade_a3d9c1e75b28.sql` | `a3d9c1e75b28` | `c7f1a3b9d425` |
| 3 | `docs/staging_upgrade_b6d9e4c2a8f1.sql` | `b6d9e4c2a8f1` | `a3d9c1e75b28` |
| 4 | `docs/staging_upgrade_d2a7c9e4f1b3.sql` | `d2a7c9e4f1b3` | `b6d9e4c2a8f1` |
| 5 | `docs/staging_upgrade_c8f1a2b3d4e5.sql` | `c8f1a2b3d4e5` | `d2a7c9e4f1b3` |
| 6 | `docs/staging_upgrade_d9e2f3a4b5c6.sql` | `d9e2f3a4b5c6` | `c8f1a2b3d4e5` |

Para saber cuántos faltan: `SELECT version_num FROM public.alembic_version;` en Supabase SQL Editor y ejecutar solo los que estén **después** del valor devuelto. Alternativa sin ambigüedad: `MIGRATION_DATABASE_URL=postgresql://administrador:…@host:5432/cotizat alembic upgrade head` aplica todo lo pendiente en orden. Hasta completar la cadena, `/readyz` responde 503 (la guarda de head funciona así a propósito).

**Actualización 19/08/2026 (verificado por el titular):** Supabase responde `alembic_version = d9e2f3a4b5c6` y la comprobación estructural confirma el esquema completo: `columnas_latam = 3` (`etiqueta_id_fiscal`, `tasa_cambio`, `fecha_tasa` en `configuracion`), `tablas_previas = 3` (`pruebas_concedidas`, `consentimientos`, `eventos_auditoria`) y `columnas_compra = 2` (`licencia_inicio`, `licencia_vence` en `compras_plan`). **Base de datos lista; falta solo el despliegue del código** (PR hacia `main` → Vercel) para que el runtime deje de esperar `d2a7c9e4f1b3` y exija `d9e2f3a4b5c6`. Tras el deploy, verificar `GET /readyz → {"ok": true, "alembic": "head:d9e2f3a4b5c6"}`.

**Actualización 19/08/2026 (auditoría de rendimiento):** el head exigido por el runtime pasó a `b9f4d8a2c6e1` (22 índices de las consultas calientes: catálogo, presupuestos y todas las FK del grafo; PostgreSQL no crea índices automáticos en FK). Aplicar con `docs/staging_upgrade_b9f4d8a2c6e1.sql` (guarda de versión previa `e7b3c1d5a204`, idempotente). Detalles y mediciones antes/después en [`RENDIMIENTO_AUDITORIA_2026-08-19.md`](RENDIMIENTO_AUDITORIA_2026-08-19.md).

**Actualización 20/08/2026 (evidencia de precios):** el head actual es
`a4c8e2f7b1d6`. Después de `b9f4d8a2c6e1`, aplicar
`docs/staging_upgrade_a4c8e2f7b1d6.sql`; añade código estable, rango, unidad,
fecha, IVA, transporte y observaciones a los precios nacionales. Mientras no
se aplique, `/readyz` responde 503 para impedir ejecutar código nuevo sobre un
esquema que perdería esa evidencia.

## Rol de runtime y migraciones

`c93e7a4d20f1` crea `cotizat_app` como rol grupal `NOLOGIN`, `NOSUPERUSER` y `NOBYPASSRLS`; deliberadamente no contiene contraseña. El login de runtime debe crearse fuera de Git, con una contraseña generada en el gestor de secretos del proveedor, y recibir únicamente:

```sql
GRANT cotizat_app TO cotizat_runtime;
```

`cotizat_runtime` debe conservar `INHERIT` y no puede ser propietario de tablas, superusuario ni tener `BYPASSRLS`. La migración se ejecuta con `MIGRATION_DATABASE_URL` administrativa; el proceso web recibe solo `DATABASE_URL` del login limitado. PostgreSQL exige este control por defecto: CotizaT aborta el arranque si el esquema no está en `e1a4b7c9d2f0` o detecta un rol privilegiado, sin `INHERIT` o ajeno a `cotizat_app`. `COTIZAT_REQUIRE_RLS_ROLE=false` queda exclusivamente como escape explícito de diagnóstico, no como configuración publicable.

La URL administrativa no debe configurarse en el servicio web después de migrar. No se guardan contraseñas en migraciones, documentación ni Git.

## Contexto y políticas RLS

Después de validar el access token con Supabase, SQLAlchemy instala `cotizat.auth_user_id` y `cotizat.auth_email` mediante `set_config(..., true)` parametrizado. Solo después de resolver una membresía activa instala `cotizat.organization_id`. Un evento `after_begin` reaplica esos valores en cada transacción tras un commit; al ser locales a la transacción, el pool no hereda el tenant anterior.

Las políticas versionadas:

- fuerzan RLS en todas las tablas empresariales y exigen contexto + membresía activa;
- permiten lectura al rol `lectura`, pero reservan escrituras para los demás roles;
- limitan perfiles al UUID/email autenticado y permiten a gestores ver únicamente integrantes de la organización seleccionada;
- permiten crear una organización solo vinculándola a su creador y crear la primera membresía propietaria solo para ese creador;
- permiten altas/reactivaciones posteriores únicamente mediante una invitación vigente para el email verificado;
- protegen invitaciones con reglas distintas para gestores y destinatarios y mantienen inmutables sus campos sensibles mediante privilegios por columna.

Las funciones auxiliares viven en `cotizat_security`, tienen `search_path` fijo y dejan de ser ejecutables por `PUBLIC`. Esto constituye una segunda barrera frente a filtros ORM olvidados, pero no convierte una inyección SQL arbitraria en inocua: los GUC de PostgreSQL no son credenciales. Deben mantenerse consultas parametrizadas, privilegios mínimos, auditoría y pruebas de penetración.

## Restricciones actuales

La existencia de PostgreSQL, RLS versionado y `organizacion_id` todavía no basta para publicar CotizaT. En SQLite, `COTIZAT_ORGANIZATION_ID` conserva el espacio transitorio para recuperar instalaciones anteriores. En PostgreSQL se ignora: la dependencia HTTP exige Supabase Auth y una membresía activa.

El RLS ya está aplicado y validado en el proyecto real con el login limitado
(`superuser=False, bypassrls=False, inherit=True, cotizat_app=True`). Queda
pendiente ejecutar cruces reales de lectura/escritura con dos organizaciones en
navegador, y la prueba manual de que la URL pública del bucket privado niega el
acceso.

Las copias `.db` y su restauración están desactivadas cuando el backend no es SQLite. La estrategia web será backup administrado y exportación por organización. Consulta también `docs/AUTENTICACION_SUPABASE.md`, `docs/ALMACENAMIENTO_PRIVADO.md` y `docs/SEGURIDAD_WEB.md`.
