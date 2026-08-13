import logging
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import Session as OrmSession, declarative_base, sessionmaker
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


def _directorio_escribible(directorio: Path) -> bool:
    """Comprueba que un directorio existe (o puede crearse) y admite escritura."""
    try:
        directorio.mkdir(parents=True, exist_ok=True)
        sonda = directorio / ".cotizat_sonda_escritura"
        sonda.write_text("ok", encoding="utf-8")
        sonda.unlink(missing_ok=True)
        return True
    except OSError:
        return False


# Los despliegues serverless (Vercel y similares) montan el código en un
# sistema de archivos de solo lectura; solo /tmp es escribible. Sin
# ``DATABASE_URL`` no hay dónde persistir en la ubicación habitual, así que
# los datos locales se redirigen a /tmp para que la aplicación arranque (modo
# efímero: cada instancia pierde los datos al reiniciarse). Un despliegue web
# permanente debe configurar ``DATABASE_URL`` (PostgreSQL).
DATOS_EFIMEROS = False
if (
    not os.environ.get("DATABASE_URL", "").strip()
    and not getattr(sys, "frozen", False)
    and not _directorio_escribible(DATA_DIR)
):
    DATOS_EFIMEROS = True
    DATA_DIR = Path(os.environ.get("TMPDIR") or "/tmp") / "cotizat"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "uploads").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "private_storage").mkdir(parents=True, exist_ok=True)
    logging.getLogger("cotizat").warning(
        "Sistema de archivos de solo lectura detectado: los datos locales de "
        "CotizaT se guardan temporalmente en %s y se perderán al reiniciar. "
        "Configura DATABASE_URL (PostgreSQL) para un despliegue web permanente.",
        DATA_DIR,
    )

# ``DATABASE_URL`` es la entrada de la futura versión web. Las variables de
# archivo locales continúan funcionando para no romper instalaciones actuales.
DATABASE = resolver_database_settings(DATA_DIR, DATABASE_FILENAME)
DATABASE_URL = DATABASE.url
DATABASE_BACKEND = DATABASE.backend
DATABASE_IS_SQLITE = DATABASE.is_sqlite
DB_PATH = DATABASE.sqlite_path
EXPECTED_ALEMBIC_HEAD = "c93e7a4d20f1"

# Copias de seguridad automáticas y manuales (solo corresponden al modo
# SQLite local; PostgreSQL tendrá backups administrados fuera del proceso).
BACKUPS_DIR = DATA_DIR / "backups"

# Archivos históricos servidos por /static/uploads para compatibilidad.
# En modo efímero (solo lectura) las subidas viven junto al resto de datos
# temporales: el montaje estático del modo SQLite debe apuntar a un
# directorio que exista y sea escribible.
UPLOADS_DIR = (
    DATA_DIR / "uploads"
    if getattr(sys, "frozen", False) or DATOS_EFIMEROS
    else BASE_DIR / "app" / "static" / "uploads"
)
# Los objetos nuevos del adaptador local nunca cuelgan del montaje estático:
# incluso en desarrollo pasan por el proxy autorizado /archivos/....
PRIVATE_STORAGE_DIR = DATA_DIR / "private_storage"

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


def _aplicar_contexto_postgresql(connection, info: dict) -> None:
    """Instala claims locales a la transacción sin interpolarlos en SQL."""
    if connection.dialect.name != "postgresql":
        return
    connection.execute(
        text("""
            SELECT
              set_config('cotizat.auth_user_id', :auth_user_id, true),
              set_config('cotizat.auth_email', :auth_email, true),
              set_config('cotizat.organization_id', :organization_id, true)
        """),
        {
            "auth_user_id": str(info.get("auth_user_id") or ""),
            "auth_email": str(info.get("auth_email") or "").lower(),
            "organization_id": str(info.get("organizacion_id") or ""),
        },
    )


@event.listens_for(OrmSession, "after_begin")
def _restaurar_contexto_postgresql(db, _transaction, connection):
    """Reaplica SET LOCAL tras cada commit en conexiones reutilizadas."""
    _aplicar_contexto_postgresql(connection, db.info)


def _establecer_contexto_identidad(db, identidad) -> None:
    db.info["auth_user_id"] = identidad.auth_user_id
    db.info["auth_email"] = identidad.email


def establecer_contexto_organizacion(db, organizacion_id: int) -> None:
    """Activa el tenant ORM/RLS después de validar o crear su membresía."""
    db.info["organizacion_id"] = int(organizacion_id)
    if db.get_bind().dialect.name == "postgresql":
        # La consulta de membresía ya abrió la transacción; actualiza el claim
        # ahora y el evento lo restaurará en transacciones posteriores.
        db.execute(
            text("SELECT set_config('cotizat.organization_id', :value, true)"),
            {"value": str(organizacion_id)},
        )


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
    # Solo después de que Supabase verificó el token se expone la identidad a
    # PostgreSQL. Las políticas de perfiles permiten entonces alta/vínculo.
    _establecer_contexto_identidad(db, identidad)
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

        establecer_contexto_organizacion(db, membresia.organizacion_id)
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


def _verificar_head_alembic_postgresql() -> None:
    with engine.connect() as connection:
        version = connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one()
    if version != EXPECTED_ALEMBIC_HEAD:
        raise RuntimeError(
            "El esquema PostgreSQL no está en el head requerido "
            f"{EXPECTED_ALEMBIC_HEAD}. Ejecuta `alembic upgrade head`."
        )


def _verificar_rol_aplicacion_postgresql() -> None:
    requerido = os.environ.get("COTIZAT_REQUIRE_RLS_ROLE", "true").strip().lower()
    if DATABASE_IS_SQLITE or requerido in {"0", "false", "no", "off"}:
        return
    with engine.connect() as connection:
        row = connection.execute(text("""
            SELECT r.rolname, r.rolsuper, r.rolbypassrls, r.rolinherit,
                   COALESCE(
                     pg_has_role(r.oid, app_role.oid, 'member'), FALSE
                   ) AS app_member
            FROM pg_catalog.pg_roles AS r
            LEFT JOIN pg_catalog.pg_roles AS app_role
              ON app_role.rolname = 'cotizat_app'
            WHERE r.rolname = current_user
        """)).mappings().one()
    if (
        row["rolsuper"]
        or row["rolbypassrls"]
        or not row["rolinherit"]
        or not row["app_member"]
    ):
        raise RuntimeError(
            "DATABASE_URL debe usar un login no privilegiado miembro de "
            "cotizat_app, con INHERIT y sin SUPERUSER/BYPASSRLS."
        )


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
        with SessionLocal() as db:
            models.asegurar_config(db)
            # Una actualización local no debe interrumpir al usuario con el
            # asistente ni volver a sembrar datos.
            if instalacion_anterior:
                marcar_instalacion_anterior(db)
    else:
        if not inspect(engine).has_table("configuracion"):
            raise RuntimeError(
                "La base PostgreSQL no tiene el esquema de CotizaT. "
                "Ejecuta `alembic upgrade head` antes de iniciar la aplicación."
            )
        _verificar_head_alembic_postgresql()
        _verificar_rol_aplicacion_postgresql()
        # No se consulta ni crea configuración global al arrancar: bajo RLS la
        # configuración nace dentro del tenant después de validar membresía.


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


def restaurar_base(
    origen: Path,
    uploads_origen: Path | None = None,
    private_storage_origen: Path | None = None,
) -> None:
    """Sustituye SQLite y, opcionalmente, ambos almacenes locales por una copia.

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
    private_storage_dir = PRIVATE_STORAGE_DIR
    if private_storage_dir.exists():
        shutil.copytree(private_storage_dir, prev / "private_storage")

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
    if private_storage_origen is not None and private_storage_origen.is_dir():
        if private_storage_dir.exists():
            shutil.rmtree(private_storage_dir)
        shutil.copytree(private_storage_origen, private_storage_dir)

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
