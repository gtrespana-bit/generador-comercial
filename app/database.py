import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

from .branding import DATABASE_FILENAME, resolve_data_directory

# ---------------------------------------------------------------------------
# Rutas: recursos empaquetados vs. datos del usuario
# ---------------------------------------------------------------------------
# - En modo empaquetado (.exe creado con PyInstaller):
#     · BASE_DIR  → _MEIPASS (recursos de solo lectura: plantillas, css,
#                   fuentes, todo lo que viaja dentro del .exe)
#     · DATA_DIR  → %LOCALAPPDATA%\CotizaT en instalaciones nuevas, o la
#                   carpeta histórica %LOCALAPPDATA%\Presupuestos cuando ya
#                   contiene datos de una versión anterior (donde vive todo lo
#                   que el usuario crea: base de datos, imágenes, copias de
#                   seguridad). Así la app instalada puede escribirse sin
#                   permisos de administrador y no pierde datos al
#                   actualizar o desinstalar el programa.
# - En desarrollo: ambos apuntan a la raíz del repositorio.
if getattr(sys, "frozen", False):
    BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    _raiz_datos = Path(
        os.environ.get("LOCALAPPDATA")
        or os.environ.get("APPDATA")
        or str(Path.home())
    )
    DATA_DIR = resolve_data_directory(_raiz_datos)
else:
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR

# COTIZAT_DB permite cambiar la ruta de la base. PRESUPUESTOS_DB se conserva
# como alias para automatizaciones e instalaciones anteriores.
_ruta_db_configurada = os.environ.get("COTIZAT_DB") or os.environ.get("PRESUPUESTOS_DB")
DB_PATH = Path(_ruta_db_configurada or (DATA_DIR / DATABASE_FILENAME))
if not DB_PATH.is_absolute():
    DB_PATH = (DATA_DIR / DB_PATH).resolve()

# Copias de seguridad automáticas y manuales
BACKUPS_DIR = DATA_DIR / "backups"

# Imágenes subidas por el usuario (logo, productos, firmas, proyectos).
# En modo empaquetado viven en DATA_DIR/uploads (no dentro del .exe).
UPLOADS_DIR = DATA_DIR / "uploads" if getattr(sys, "frozen", False) else BASE_DIR / "app" / "static" / "uploads"

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine, "connect")
def _activar_claves_foraneas(dbapi_connection, _connection_record):
    """SQLite no activa FK por defecto; sin esto podían quedar huérfanos."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependencia de FastAPI: abre una sesión por petición."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Crea las tablas, aplica migraciones y siembra los datos de demo."""
    from . import models  # noqa: F401  (registra los modelos en Base)
    from .seeds import sembrar_catalogo, sembrar_demo, sembrar_productos, sembrar_recetas

    Base.metadata.create_all(bind=engine)
    models.migrar(engine)
    with SessionLocal() as db:
        models.asegurar_config(db)
        sembrar_catalogo(db)
        sembrar_productos(db)
        sembrar_recetas(db)
        sembrar_demo(db)


# ---------------------------------------------------------------------------
# Copias de seguridad (descargar / restaurar)
# ---------------------------------------------------------------------------

def copia_seguridad_sqlite(destino: Path) -> None:
    """Copia el archivo de la base usando la API de backup de SQLite.

    Es segura aunque haya conexiones abiertas (la usa el botón
    «Descargar copia de seguridad» de Configuración).
    """
    import sqlite3

    destino.parent.mkdir(parents=True, exist_ok=True)
    if not DB_PATH.exists():
        raise FileNotFoundError(f"No existe la base de datos: {DB_PATH}")
    src = sqlite3.connect(str(DB_PATH))
    dst = sqlite3.connect(str(destino))
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()


def es_base_valida(ruta: Path) -> bool:
    """Comprueba que un archivo sea una base SQLite legible."""
    import sqlite3

    try:
        con = sqlite3.connect(str(ruta))
        try:
            con.execute("SELECT count(*) FROM sqlite_master").fetchone()
            con.execute("PRAGMA integrity_check").fetchone()
        finally:
            con.close()
        return True
    except Exception:
        return False


def restaurar_base(origen: Path, uploads_origen: Path | None = None) -> None:
    """Sustituye la base de datos (y opcionalmente las imágenes) por una copia.

    - Guarda automáticamente una copia de lo actual en `backups/` por si
      hay que volver atrás.
    - Reemplaza el archivo .db de forma atómica y descarta las conexiones
      abiertas, para que las siguientes peticiones usen la base restaurada.
    """
    from . import models  # noqa: F401

    backups = BACKUPS_DIR
    backups.mkdir(parents=True, exist_ok=True)
    marca = datetime.now().strftime("%Y%m%d_%H%M%S")
    prev = backups / f"antes_de_restaurar_{marca}"
    prev.mkdir(parents=True, exist_ok=True)

    if DB_PATH.exists():
        shutil.copy2(DB_PATH, prev / DB_PATH.name)
    uploads_dir = UPLOADS_DIR
    if uploads_dir.exists():
        shutil.copytree(uploads_dir, prev / "uploads")

    engine.dispose()  # cierra conexiones al archivo actual

    # Reemplazo atómico del .db (los conectados al archivo viejo lo siguen
    # viendo intacto; las nuevas conexiones abren el archivo restaurado)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = DB_PATH.with_name(DB_PATH.name + ".restaurando")
    shutil.copy2(origen, tmp)
    os.replace(tmp, DB_PATH)

    if uploads_origen is not None and uploads_origen.is_dir():
        if uploads_dir.exists():
            shutil.rmtree(uploads_dir)
        shutil.copytree(uploads_origen, uploads_dir)

    engine.dispose()

    # Crea las tablas nuevas que pueda necesitar la versión actual y
    # reaplica migraciones: así un backup de una versión anterior queda
    # al día al restaurarlo.
    Base.metadata.create_all(bind=engine)
    models.migrar(engine)
    with SessionLocal() as db:
        models.asegurar_config(db)
