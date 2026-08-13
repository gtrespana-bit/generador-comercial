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

La revisión `9bca2ad1f6e4`, que añade el vínculo con Supabase Auth, también quedó aplicada en el mismo proyecto. El head vigente allí sigue siendo `9bca2ad1f6e4`. El código tiene como nuevo head `72e6f4d8a1c3` para metadatos de Storage privado, pendiente de aplicar junto con la prueba real del bucket.

## Restricciones actuales

La existencia de PostgreSQL y `organizacion_id` no basta para publicar CotizaT. En SQLite, `COTIZAT_ORGANIZATION_ID` conserva el espacio transitorio para recuperar instalaciones anteriores. En PostgreSQL se ignora: la dependencia HTTP exige Supabase Auth y una membresía activa.

La conexión administrativa `postgres` omite RLS; el aislamiento del backend depende además de la autorización por membresía y del filtro ORM. Falta un rol de aplicación no privilegiado, políticas autorizantes, CSRF y completar la auditoría web. Consulta `docs/AUTENTICACION_SUPABASE.md` y `docs/ALMACENAMIENTO_PRIVADO.md`.

Las copias `.db` y su restauración están desactivadas cuando el backend no es SQLite. La estrategia web será backup administrado y exportación por organización.
