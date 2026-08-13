import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, event, inspect
from sqlalchemy.orm import declarative_base, sessionmaker
from starlette.requests import Request

from .branding import DATABASE_FILENAME, resolve_data_directory
from .db_config import resolver_database_settings

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

# ``DATABASE_URL`` es la entrada de la futura versión web. Las variables de
# archivo locales continúan funcionando para no romper instalaciones actuales.
DATABASE = resolver_database_settings(DATA_DIR, DATABASE_FILENAME)
DATABASE_URL = DATABASE.url
DATABASE_BACKEND = DATABASE.backend
DATABASE_IS_SQLITE = DATABASE.is_sqlite
DB_PATH = DATABASE.sqlite_path

# Copias de seguridad automáticas y manuales (solo corresponden al modo
# SQLite local; PostgreSQL tendrá backups administrados fuera del proceso).
BACKUPS_DIR = DATA_DIR / "backups"

# Imágenes subidas por el usuario (logo, productos, firmas, proyectos).
# Esta ruta se conserva durante la transición. La versión web la sustituirá
# por una interfaz de almacenamiento de objetos.
UPLOADS_DIR = DATA_DIR / "uploads" if getattr(sys, "frozen", False) else BASE_DIR / "app" / "static" / "uploads"

_engine_options = {"pool_pre_ping": True}
if DATABASE_IS_SQLITE:
    _engine_options["connect_args"] = {"check_same_thread": False}
engine = create_engine(DATABASE_URL, **_engine_options)


if DATABASE_IS_SQLITE:
    @event.listens_for(engine, "connect")
    def _activar_claves_foraneas(dbapi_connection, _connection_record):
        """SQLite no activa FK por defecto; sin esto podían quedar huérfanos."""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(autoflush=False, bind=engine)
Base = declarative_base()


def _autenticar_usuario(db, request: Request):
    """Valida Supabase Auth y sincroniza el perfil local sin guardar tokens."""
    from .auth import (
        AuthenticationRequired,
        OrganizationAccessDenied,
        identity_for_request,
    )
    from .models import VinculoIdentidadError, sincronizar_usuario_auth

    if request is None:
        raise AuthenticationRequired("Inicia sesión para continuar.")
    identidad = identity_for_request(request)
    try:
        usuario = sincronizar_usuario_auth(
            db,
            identidad.auth_user_id,
            identidad.email,
            identidad.name,
            identidad.email_verified,
        )
    except VinculoIdentidadError as exc:
        db.rollback()
        raise OrganizationAccessDenied(str(exc)) from exc
    # El alta/vínculo del perfil es idempotente. Se confirma antes de resolver
    # membresías para que una petición posterior nunca dependa de la sesión
    # física que recibió el callback de Auth.
    db.commit()
    request.state.usuario = usuario
    request.state.supabase_identity = identidad
    db.info["usuario_id"] = usuario.id
    return usuario


def get_authenticated_db(request: Request = None):
    """Sesión autenticada sin exigir todavía una organización activa.

    Se usa exclusivamente para crear/seleccionar empresa. Los datos
    comerciales continúan usando :func:`get_db`.
    """
    db = SessionLocal()
    try:
        if DATABASE_IS_SQLITE:
            yield db
            return
        _autenticar_usuario(db, request)
        yield db
    finally:
        db.close()


def get_db(request: Request = None):
    """Abre una sesión con organización derivada de una membresía autorizada.

    SQLite conserva el espacio fijo para recuperar instalaciones anteriores.
    PostgreSQL nunca acepta ``COTIZAT_ORGANIZATION_ID``: valida Supabase Auth,
    comprueba la membresía y solo entonces activa el filtro ORM.
    """
    db = SessionLocal()
    try:
        if DATABASE_IS_SQLITE:
            organizacion_id = int(os.environ.get("COTIZAT_ORGANIZATION_ID", "1"))
            db.info["organizacion_id"] = organizacion_id
            yield db
            return

        from .auth import OrganizationAccessDenied, OrganizationRequired
        from .models import (
            OrganizacionNoAutorizadaError,
            membresias_activas,
            resolver_membresia_activa,
        )

        usuario = _autenticar_usuario(db, request)
        cookie = request.cookies.get("cotizat_organization_id", "").strip()
        organizacion_solicitada = None
        if cookie:
            try:
                organizacion_solicitada = int(cookie)
            except ValueError as exc:
                raise OrganizationAccessDenied(
                    "La organización seleccionada no es válida."
                ) from exc
        try:
            membresia = resolver_membresia_activa(
                db, usuario.id, organizacion_solicitada
            )
        except OrganizacionNoAutorizadaError as exc:
            raise OrganizationAccessDenied(str(exc)) from exc
        if membresia is None:
            # Cero membresías lleva al alta inicial; varias requieren que el
            # usuario elija explícitamente una para no mezclar contextos.
            request.state.membresias = membresias_activas(db, usuario.id)
            raise OrganizationRequired("Selecciona o crea una organización.")

        db.info["organizacion_id"] = membresia.organizacion_id
        db.info["rol_membresia"] = membresia.rol
        db.info["membresia_id"] = membresia.id
        request.state.membresia = membresia
        request.state.organizacion = membresia.organizacion
        yield db
    finally:
        db.close()


def _es_esquema_anterior_al_onboarding() -> bool:
    """Detecta una base existente creada antes del asistente de primer inicio."""
    inspector = inspect(engine)
    if not inspector.has_table("configuracion"):
        return False
    columnas = {columna["name"] for columna in inspector.get_columns("configuracion")}
    return "onboarding_completado" not in columnas


def init_db():
    """Inicializa SQLite local o comprueba el esquema versionado de la web.

    Las instalaciones SQLite conservan la migración no destructiva histórica.
    En PostgreSQL el esquema debe aplicarse previamente con Alembic; ejecutar
    DDL implícito al arrancar varias instancias web produciría carreras.
    """
    from . import models  # noqa: F401  (registra los modelos en Base)
    from .services.onboarding import marcar_instalacion_anterior

    instalacion_anterior = _es_esquema_anterior_al_onboarding()
    if DATABASE_IS_SQLITE:
        Base.metadata.create_all(bind=engine)
        models.migrar(engine)
    elif not inspect(engine).has_table("configuracion"):
        raise RuntimeError(
            "La base PostgreSQL no tiene el esquema de CotizaT. "
            "Ejecuta `alembic upgrade head` antes de iniciar la aplicación."
        )

    with SessionLocal() as db:
        models.asegurar_config(db)
        # Una actualización no debe interrumpir al usuario con un asistente ni
        # volver a sembrar datos. Solo las bases nuevas conservan el estado
        # pendiente para elegir entre demo e instalación limpia.
        if instalacion_anterior:
            marcar_instalacion_anterior(db)


# ---------------------------------------------------------------------------
# Copias de seguridad (descargar / restaurar)
# ---------------------------------------------------------------------------

class OperacionSoloSQLite(RuntimeError):
    """La operación local solicitada no corresponde al backend web."""


def _exigir_sqlite() -> Path:
    if not DATABASE_IS_SQLITE or DB_PATH is None:
        raise OperacionSoloSQLite(
            "Esta operación solo está disponible en la instalación SQLite local."
        )
    return DB_PATH


def copia_seguridad_sqlite(destino: Path) -> None:
    """Copia el archivo de la base usando la API de backup de SQLite.

    Es segura aunque haya conexiones abiertas (la usa el botón
    «Descargar copia de seguridad» de Configuración).
    """
    import sqlite3

    db_path = _exigir_sqlite()
    destino.parent.mkdir(parents=True, exist_ok=True)
    if not db_path.exists():
        raise FileNotFoundError(f"No existe la base de datos: {db_path}")
    src = sqlite3.connect(str(db_path))
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

    db_path = _exigir_sqlite()
    backups = BACKUPS_DIR
    backups.mkdir(parents=True, exist_ok=True)
    marca = datetime.now().strftime("%Y%m%d_%H%M%S")
    prev = backups / f"antes_de_restaurar_{marca}"
    prev.mkdir(parents=True, exist_ok=True)

    if db_path.exists():
        shutil.copy2(db_path, prev / db_path.name)
    uploads_dir = UPLOADS_DIR
    if uploads_dir.exists():
        shutil.copytree(uploads_dir, prev / "uploads")

    engine.dispose()  # cierra conexiones al archivo actual

    # Reemplazo atómico del .db (los conectados al archivo viejo lo siguen
    # viendo intacto; las nuevas conexiones abren el archivo restaurado)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = db_path.with_name(db_path.name + ".restaurando")
    shutil.copy2(origen, tmp)
    os.replace(tmp, db_path)

    if uploads_origen is not None and uploads_origen.is_dir():
        if uploads_dir.exists():
            shutil.rmtree(uploads_dir)
        shutil.copytree(uploads_origen, uploads_dir)

    engine.dispose()

    # Crea las tablas nuevas que pueda necesitar la versión actual y
    # reaplica migraciones: así un backup de una versión anterior queda
    # al día al restaurarlo.
    instalacion_anterior = _es_esquema_anterior_al_onboarding()
    Base.metadata.create_all(bind=engine)
    models.migrar(engine)
    with SessionLocal() as db:
        models.asegurar_config(db)
        if instalacion_anterior:
            from .services.onboarding import marcar_instalacion_anterior
            marcar_instalacion_anterior(db)
