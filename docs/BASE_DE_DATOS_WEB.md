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
