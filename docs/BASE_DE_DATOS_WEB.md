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

## Restricciones actuales

La existencia de PostgreSQL y `organizacion_id` no basta para publicar CotizaT. Mientras no exista autenticación, la dependencia HTTP utiliza el espacio transitorio configurado por `COTIZAT_ORGANIZATION_ID` (1 por defecto). Esto solo sirve para desarrollo local.

Las copias `.db` y su restauración están desactivadas cuando el backend no es SQLite. La estrategia web será backup administrado y exportación por organización.
