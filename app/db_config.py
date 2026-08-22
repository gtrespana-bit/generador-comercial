"""Configuración portable de la base de datos.

La aplicación histórica usa un archivo SQLite local. La versión web usa
``DATABASE_URL`` y PostgreSQL, sin cambiar la lógica de dominio. Mantener esta
resolución en un módulo pequeño evita que rutas y servicios dependan del
proveedor de persistencia.
"""
from dataclasses import dataclass
import os
from pathlib import Path

from sqlalchemy.engine import make_url


@dataclass(frozen=True)
class DatabaseSettings:
    url: str
    backend: str
    sqlite_path: Path | None
    source: str

    @property
    def is_sqlite(self) -> bool:
        return self.backend == "sqlite"

    @property
    def is_postgresql(self) -> bool:
        return self.backend == "postgresql"


def _normalizar_url(url: str) -> str:
    """Usa psycopg 3 y optimiza el puerto del pooler de Supabase.

    - Convierte ``postgres://`` y ``postgresql://`` a ``postgresql+psycopg://``.
    - Si la conexión apunta al pooler de Supabase (``*.pooler.supabase.com``)
      en el puerto 5432 (Session mode, limitado a 15 conexiones) o sin puerto
      explícito, conmuta automáticamente al puerto 6543 (Transaction mode),
      diseñado para entornos serverless y concurrencia web.
    """
    url = url.strip()
    if not url:
        return url
    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]

    try:
        parsed = make_url(url)
        host = (parsed.host or "").lower()
        if "pooler.supabase.com" in host and parsed.port in (5432, None):
            parsed = parsed.set(port=6543)
            url = parsed.render_as_string(hide_password=False)
    except Exception:
        pass

    return url


def resolver_database_settings(data_dir: Path, default_filename: str) -> DatabaseSettings:
    """Resuelve la conexión sin romper las variables históricas.

    Prioridad:
      1. ``DATABASE_URL`` para despliegues web.
      2. ``COTIZAT_DB`` para instalaciones actuales.
      3. ``PRESUPUESTOS_DB`` como alias heredado.
      4. Archivo SQLite predeterminado dentro del directorio de datos.
    """
    database_url = os.environ.get("DATABASE_URL", "").strip()
    if database_url:
        source = "DATABASE_URL"
        url = _normalizar_url(database_url)
    else:
        ruta_configurada = os.environ.get("COTIZAT_DB") or os.environ.get("PRESUPUESTOS_DB")
        ruta = Path(ruta_configurada or (data_dir / default_filename))
        if not ruta.is_absolute():
            ruta = (data_dir / ruta).resolve()
        source = "COTIZAT_DB" if os.environ.get("COTIZAT_DB") else (
            "PRESUPUESTOS_DB" if os.environ.get("PRESUPUESTOS_DB") else "default"
        )
        url = f"sqlite:///{ruta}"

    parsed = make_url(url)
    backend = parsed.get_backend_name()
    sqlite_path = None
    if backend == "sqlite" and parsed.database and parsed.database != ":memory:":
        sqlite_path = Path(parsed.database).resolve()
    return DatabaseSettings(
        url=url,
        backend=backend,
        sqlite_path=sqlite_path,
        source=source,
    )
