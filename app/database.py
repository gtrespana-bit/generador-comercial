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
#
# ``COTIZAT_DATA_DIR`` redirige el directorio de datos completo (base,
# backups, uploads y almacén privado) en modo desarrollo. Lo usan las pruebas
# del recorrido crítico para ejercitar backup/restauración sin tocar los
# datos del desarrollador, igual que ``COTIZAT_DB`` aísla solo el archivo
# SQLite. En modo empaquetado se ignora: la instalación real debe seguir las
# reglas de ``resolve_data_directory``.
_data_dir_configurado = os.environ.get("COTIZAT_DATA_DIR", "").strip()
if getattr(sys, "frozen", False):
    BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    _raiz_datos = Path(
        os.environ.get("LOCALAPPDATA")
        or os.environ.get("APPDATA")
        or str(Path.home())
    )
    DATA_DIR = resolve_data_directory(_raiz_datos)
    _data_dir_configurado = ""
else:
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = Path(_data_dir_configurado).resolve() if _data_dir_configurado else BASE_DIR


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
EXPECTED_ALEMBIC_HEAD = "e4b8c2d6a190"

# Copias de seguridad automáticas y manuales (solo corresponden al modo
# SQLite local; PostgreSQL tendrá backups administrados fuera del proceso).
BACKUPS_DIR = DATA_DIR / "backups"

# Archivos históricos servidos por /static/uploads para compatibilidad.
# En modo efímero (solo lectura) las subidas viven junto al resto de datos
# temporales: el montaje estático del modo SQLite debe apuntar a un
# directorio que exista y sea escribible.
UPLOADS_DIR = (
    DATA_DIR / "uploads"
    if getattr(sys, "frozen", False) or DATOS_EFIMEROS or _data_dir_configurado
    else BASE_DIR / "app" / "static" / "uploads"
)
# Los objetos nuevos del adaptador local nunca cuelgan del montaje estático:
# incluso en desarrollo pasan por el proxy autorizado /archivos/....
PRIVATE_STORAGE_DIR = DATA_DIR / "private_storage"

_engine_options = {"pool_pre_ping": True}
if DATABASE_IS_SQLITE:
    _engine_options["connect_args"] = {"check_same_thread": False}
else:
    # PostgreSQL / Web:
    # 1. prepare_threshold=None: imprescindible para el pooler de Supabase / PgBouncer
    #    en modo Transaction (puerto 6543), evitando colisiones de prepared statements.
    # 2. pool_recycle=300: renueva conexiones periódicamente para evitar sockets caídos.
    _engine_options["connect_args"] = {"prepare_threshold": None}
    _engine_options["pool_recycle"] = int(os.environ.get("COTIZAT_DB_POOL_RECYCLE", "300"))
    pool_class_cfg = os.environ.get("COTIZAT_DB_POOL_CLASS", "").strip().lower()
    # En Vercel cada invocación es un proceso corto: un pool persistente
    # deja conexiones colgadas en PgBouncer y alarga el arranque. NullPool
    # abre y cierra por petición (el pooler de Supabase ya multiplexa).
    if not pool_class_cfg and os.environ.get("VERCEL"):
        pool_class_cfg = "nullpool"
    if pool_class_cfg == "nullpool":
        from sqlalchemy.pool import NullPool
        _engine_options["poolclass"] = NullPool
    else:
        pool_size_cfg = os.environ.get("COTIZAT_DB_POOL_SIZE", "").strip()
        max_overflow_cfg = os.environ.get("COTIZAT_DB_MAX_OVERFLOW", "").strip()
        if pool_size_cfg:
            try:
                _engine_options["pool_size"] = int(pool_size_cfg)
            except ValueError:
                pass
        if max_overflow_cfg:
            try:
                _engine_options["max_overflow"] = int(max_overflow_cfg)
            except ValueError:
                pass
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
              set_config('cotizat.organization_id', :organization_id, true),
              set_config('cotizat.es_operador', :es_operador, true),
              set_config('cotizat.proposal_token_hash', :proposal_token_hash, true)
        """),
        {
            "auth_user_id": str(info.get("auth_user_id") or ""),
            "auth_email": str(info.get("auth_email") or "").lower(),
            "organization_id": str(info.get("organizacion_id") or ""),
            "proposal_token_hash": str(info.get("proposal_token_hash") or ""),
            # Marca que habilita las políticas RLS de `licencias`. Vale 'on'
            # solo si el correo verificado figura en COTIZAT_OPERADORES; para
            # cualquier sesión de cliente queda en 'off' y la tabla se comporta
            # como si estuviera vacía (revisión f4c1d8e37a95).
            "es_operador": "on" if info.get("es_operador") else "off",
        },
    )


@event.listens_for(OrmSession, "after_begin")
def _restaurar_contexto_postgresql(db, _transaction, connection):
    """Reaplica SET LOCAL tras cada commit en conexiones reutilizadas."""
    _aplicar_contexto_postgresql(connection, db.info)


def _establecer_contexto_identidad(db, identidad) -> None:
    from .operadores import es_operador

    db.info["auth_user_id"] = identidad.auth_user_id
    db.info["auth_email"] = identidad.email
    # La marca de operador se decide aquí, junto a la identidad ya validada por
    # Supabase, y nunca a partir de datos de la petición: así ninguna ruta puede
    # concedérsela por su cuenta.
    db.info["es_operador"] = es_operador(
        identidad.email, email_verificado=identidad.email_verified
    )


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


def get_operator_db(request: Request = None):
    """Sesión autenticada que además exige ser **operador del producto**.

    Es la puerta del panel de administración de licencias. Se apoya en
    ``_autenticar_usuario`` (misma validación de Supabase que el resto) y añade
    la comprobación de la lista ``COTIZAT_OPERADORES``.

    En PostgreSQL la sesión queda marcada con ``cotizat.es_operador``, que es lo
    que habilita las políticas RLS de ``licencias``. Si esta comprobación se
    saltara por un fallo de código, RLS seguiría devolviendo cero filas.
    """
    from .auth import OrganizationAccessDenied

    db = SessionLocal()
    try:
        if DATABASE_IS_SQLITE:
            # Instalación local monousuario: el panel de licencias no aplica.
            raise OrganizationAccessDenied(
                "El panel de licencias solo existe en el despliegue web."
            )
        _autenticar_usuario(db, request)
        if not db.info.get("es_operador"):
            # Mismo mensaje que cualquier otro acceso denegado: no confirma la
            # existencia del panel a quien no debe usarlo.
            raise OrganizationAccessDenied("No tienes acceso a esta sección.")
        yield db
    finally:
        db.close()


def get_stripe_webhook_db():
    """Sesión para el webhook de Stripe.

    Stripe no es una sesión de usuario: la puerta de seguridad es la firma
    ``Stripe-Signature`` que la ruta verifica **antes** de escribir. La
    sesión se marca como operador porque ``compras_plan`` solo admite UPDATE
    de operador (RLS) y ``licencias`` solo se inserta con esa marca. Funciona
    también en SQLite para que la suite pueda ejercitar el cumplimiento.
    """
    db = SessionLocal()
    try:
        db.info["es_operador"] = True
        db.info["auth_email"] = "stripe@cotizat.local"
        yield db
    finally:
        db.close()


def get_cron_db():
    """Sesión para el trabajo programado (cron) del producto.

    El recordatorio de vencimiento necesita leer y actualizar ``licencias``,
    que bajo RLS solo responde a sesiones de operador. Pero el disparador es
    el programador de Vercel, no una sesión de Supabase Auth: la puerta de
    seguridad es el secreto compartido ``CRON_SECRET`` que la ruta del cron
    verifica **antes** de llegar aquí. Esta dependencia solo marca la sesión
    como operador del sistema; nada de lo que hace llega a una ruta pública
    sin ese secreto.
    """
    from .auth import OrganizationAccessDenied

    db = SessionLocal()
    try:
        if DATABASE_IS_SQLITE:
            raise OrganizationAccessDenied(
                "El trabajo programado solo existe en el despliegue web."
            )
        db.info["es_operador"] = True
        db.info["auth_email"] = "sistema@cotizat.local"
        yield db
    finally:
        db.close()


def get_public_proposal_db(token: str):
    """Sesión sin identidad limitada por RLS al hash de un enlace público.

    No activa organización ni usuario. En PostgreSQL la única política que
    puede devolver una fila compara el SHA-256 del token con el claim local de
    esta transacción. Las demás tablas tenant permanecen completamente
    inaccesibles.
    """
    from .services.propuestas import hash_token_propuesta

    db = SessionLocal()
    try:
        db.info["proposal_token_hash"] = hash_token_propuesta(token)
        yield db
    finally:
        db.close()


def _organizacion_sqlite_desde_entorno() -> int:
    """Espacio fijo de SQLite desde ``COTIZAT_ORGANIZATION_ID``.

    Una variable presente pero vacía (típico al copiar listas de variables de
    entorno en plataformas como Vercel) equivale a no configurada: se usa el
    espacio histórico 1. Un valor no numérico sí es un error de configuración
    real y debe fallar con un mensaje claro en lugar de un 500 genérico.
    """
    valor = os.environ.get("COTIZAT_ORGANIZATION_ID", "").strip()
    if not valor:
        return 1
    try:
        return int(valor)
    except ValueError as exc:
        raise ValueError(
            "COTIZAT_ORGANIZATION_ID debe ser un número entero "
            f"(recibido: {valor!r})."
        ) from exc


def get_db_renovacion(request: Request = None):
    """Como :func:`get_db`, pero **sin** el corte por licencia vencida.

    Es la salida de emergencia del corte automático: la única forma de que una
    organización suspendida vuelva a tener licencia es comprarla, así que el
    checkout no puede quedar detrás de la propia suspensión (si no, el cliente
    solo podría renovar escribiendo a soporte).

    Mantiene **todo** lo demás intacto: Supabase Auth, membresía autorizada y
    contexto de organización con RLS. Solo se salta la comprobación de
    vigencia, y por eso se usa exclusivamente en las rutas de compra y en su
    recibo, nunca en rutas que enseñen datos de negocio.
    """
    yield from _abrir_sesion_de_organizacion(request, exigir_licencia=False)


def get_db(request: Request = None):
    """Abre una sesión con organización derivada de una membresía autorizada.

    SQLite conserva el espacio fijo para recuperar instalaciones anteriores.
    PostgreSQL nunca acepta ``COTIZAT_ORGANIZATION_ID``: valida Supabase Auth,
    comprueba la membresía y solo entonces activa el filtro ORM.
    """
    yield from _abrir_sesion_de_organizacion(request, exigir_licencia=True)


def _abrir_sesion_de_organizacion(request: Request, *, exigir_licencia: bool):
    db = SessionLocal()
    try:
        if DATABASE_IS_SQLITE:
            db.info["organizacion_id"] = _organizacion_sqlite_desde_entorno()
            if request is not None:
                # SQLite (escritorio/desarrollo) no tiene Supabase Auth: exponemos
                # una organización y usuario sintéticos para que la barra lateral
                # pueda mostrar el estado del plan (evita el "Sin plan" fantasma
                # cuando sí hay licencia pero el template exigía usuario definido).
                try:
                    from .models import Organizacion as _Org
                    org = db.get(_Org, int(db.info.get("organizacion_id") or 0))
                    if org is not None:
                        request.state.organizacion = org
                        # Usuario sintético local para que el bloque de sesión se renderice
                        from types import SimpleNamespace
                        request.state.usuario = SimpleNamespace(
                            nombre=org.nombre,
                            email="",
                            id=0,
                        )
                        # Membresía sintética para cumplir el check de rol en el template
                        request.state.membresia = SimpleNamespace(
                            rol="propietario",
                            organizacion=org,
                            organizacion_id=org.id,
                        )
                except Exception:
                    pass
                request.state.licencia_resumen = _resumen_licencia_para_request(
                    db, int(db.info.get("organizacion_id") or 0)
                )
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

        # Corte automático de acceso (E1-060): con COTIZAT_EXIGIR_LICENCIA
        # activa, una organización sin licencia vigente no entra a sus
        # pantallas de trabajo. Se aplica aquí, en la única puerta de las
        # rutas de negocio, y solo en el despliegue web: la instalación de
        # escritorio (SQLite) jamás exige licencia. La consulta va a la
        # función SECURITY DEFINER porque la sesión del cliente no puede leer
        # `licencias` por RLS.
        from .models import LicenciaSuspendidaError
        from .services.licencias import (
            exigencia_licencia_activada,
            organizacion_tiene_acceso,
        )

        if (
            exigir_licencia
            and exigencia_licencia_activada()
            and not organizacion_tiene_acceso(db, membresia.organizacion_id)
        ):
            raise LicenciaSuspendidaError(
                f"El acceso de «{membresia.organizacion.nombre}» está "
                "suspendido: su licencia venció o aún no fue activada. Tus "
                "datos siguen guardados; al renovar la licencia todo vuelve "
                "a estar disponible."
            )
        request.state.licencia_resumen = _resumen_licencia_para_request(
            db, membresia.organizacion_id
        )
        yield db
    finally:
        db.close()


def _resumen_licencia_para_request(db, organizacion_id: int) -> dict:
    """Resumen del plan para la sesión actual (sin romper si no hay tabla).

    Si la consulta falla —por permisos, RLS o cualquier otro motivo— se hace
    ``db.rollback()`` antes de devolver el resumen vacío. Sin el rollback, la
    sesión queda con la transacción abortada y la siguiente consulta del
    handler (p. ej. ``_config(db)`` en ``/inicio``) falla con
    ``psycopg.errors.InFailedSqlTransaction`` aunque sea trivialmente válida.
    """
    from .services.licencias import resumen_licencia_cliente

    try:
        return resumen_licencia_cliente(db, organizacion_id)
    except Exception:
        try:
            db.rollback()
        except Exception:
            # Si la propia rollback falla (p. ej. conexión cerrada) la
            # siguiente consulta abrirá una transacción nueva igualmente.
            pass
        # Un fallo al leer la licencia no debe tumbar la aplicación entera.
        return {
            "activo": False,
            "plan_label": "",
            "vence": None,
            "dias_restantes": 0,
            "metodo_cobro": "",
        }


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
            text("SELECT version_num FROM public.alembic_version")
        ).scalar_one_or_none()
    if version != EXPECTED_ALEMBIC_HEAD:
        raise RuntimeError(
            "El esquema PostgreSQL no está en el head requerido "
            f"{EXPECTED_ALEMBIC_HEAD} (encontrado: {version!r}). "
            "Ejecuta `alembic upgrade head` o inserta la versión en `alembic_version`."
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


def _asegurar_permisos_planos_postgres(eng) -> None:
    """Repara permisos de ``planos_*`` si el head fue marcado sin ejecutar DCL.

    Algunas bases quedaron en ``b2c3d4e5f6a7`` por la reparación best-effort de
    arranque, o ejecutaron la creación de tablas sin que el rol runtime heredara
    los GRANT necesarios. Si ``MIGRATION_DATABASE_URL`` apunta al propietario del
    esquema, este bloque deja el visor de planos operativo ya en el siguiente
    arranque; la migración ``c0d1e2f3a4b5`` conserva la reparación versionada.
    """
    statements = [
        "REVOKE ALL ON TABLE public.planos_obra FROM PUBLIC",
        "REVOKE ALL ON TABLE public.planos_mediciones FROM PUBLIC",
        "ALTER TABLE public.planos_obra ENABLE ROW LEVEL SECURITY",
        "ALTER TABLE public.planos_obra FORCE ROW LEVEL SECURITY",
        "ALTER TABLE public.planos_mediciones ENABLE ROW LEVEL SECURITY",
        "ALTER TABLE public.planos_mediciones FORCE ROW LEVEL SECURITY",
        "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.planos_obra TO cotizat_app",
        "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.planos_mediciones TO cotizat_app",
        """
        DO $$ DECLARE secuencia text; BEGIN
          secuencia := pg_get_serial_sequence('public.planos_obra', 'id');
          IF secuencia IS NOT NULL THEN
            EXECUTE format('GRANT USAGE, SELECT ON SEQUENCE %s TO cotizat_app', secuencia);
          END IF;
        END $$
        """,
        """
        DO $$ DECLARE secuencia text; BEGIN
          secuencia := pg_get_serial_sequence('public.planos_mediciones', 'id');
          IF secuencia IS NOT NULL THEN
            EXECUTE format('GRANT USAGE, SELECT ON SEQUENCE %s TO cotizat_app', secuencia);
          END IF;
        END $$
        """,
    ]
    policies = (
        ("planos_obra", "cotizat_planos_obra_select", "SELECT", "USING (cotizat_security.tenant_access(organizacion_id, FALSE))"),
        ("planos_obra", "cotizat_planos_obra_insert", "INSERT", "WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE))"),
        ("planos_obra", "cotizat_planos_obra_update", "UPDATE", "USING (cotizat_security.tenant_access(organizacion_id, TRUE)) WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE))"),
        ("planos_obra", "cotizat_planos_obra_delete", "DELETE", "USING (cotizat_security.tenant_access(organizacion_id, TRUE))"),
        ("planos_mediciones", "cotizat_planos_mediciones_select", "SELECT", "USING (cotizat_security.tenant_access(organizacion_id, FALSE))"),
        ("planos_mediciones", "cotizat_planos_mediciones_insert", "INSERT", "WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE))"),
        ("planos_mediciones", "cotizat_planos_mediciones_update", "UPDATE", "USING (cotizat_security.tenant_access(organizacion_id, TRUE)) WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE))"),
        ("planos_mediciones", "cotizat_planos_mediciones_delete", "DELETE", "USING (cotizat_security.tenant_access(organizacion_id, TRUE))"),
    )
    for table, name, action, clause in policies:
        statements.append(f"DROP POLICY IF EXISTS {name} ON public.{table}")
        statements.append(f"CREATE POLICY {name} ON public.{table} FOR {action} TO cotizat_app {clause}")

    try:
        with eng.begin() as conn:
            existen = conn.execute(text("""
                SELECT count(*) = 2
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name IN ('planos_obra', 'planos_mediciones')
            """)).scalar()
            if not existen:
                logging.getLogger("cotizat").warning(
                    "No se reparan permisos de planos: faltan tablas planos_obra/planos_mediciones. "
                    "Ejecuta `alembic upgrade head`."
                )
                return
            for statement in statements:
                conn.execute(text(statement))
        logging.getLogger("cotizat").info("Permisos/RLS de planos verificados para cotizat_app.")
    except Exception as exc:
        logging.getLogger("cotizat").warning(
            "No se pudieron reparar permisos de planos (ejecuta `alembic upgrade head` con MIGRATION_DATABASE_URL): %s",
            exc,
        )


def _asegurar_esquema_postgres() -> None:
    """Intenta añadir columnas/permisos faltantes tras un deploy sin migrar (best-effort).

    El error reportado en producción es ``UndefinedColumn: configuracion.
    recorrido_inicial_oculto does not exist``: el modelo ya exige la columna
    pero la base de PostgreSQL sigue en el head anterior (c3e9a1b7d4f2) porque
    ``alembic upgrade head`` no se ejecutó. En Vercel el arranque no puede
    quedar 500 hasta que alguien ejecute la migración a mano.

    Se usa ``ADD COLUMN IF NOT EXISTS`` (idempotente) y la URL de migración
    (``MIGRATION_DATABASE_URL``) cuando existe, porque el rol de la app
    (``cotizat_app``) no tiene privilegios DDL. Si el ALTER falla por
    permisos, se deja a la capa de lectura (fallback en ``_config``) que la
    página siga abriendo; el log avisa y la migración manual sigue siendo la
    vía definitiva.
    """
    if DATABASE_IS_SQLITE:
        return
    mig_url = os.environ.get("MIGRATION_DATABASE_URL", "").strip() or DATABASE_URL
    if mig_url:
        from .db_config import _normalizar_url
        mig_url = _normalizar_url(mig_url)
    try:
        from sqlalchemy.pool import NullPool

        mig_connect_args = {"prepare_threshold": None} if not mig_url.startswith("sqlite") else {}
        eng = create_engine(mig_url, poolclass=NullPool, connect_args=mig_connect_args)
        # Cada ALTER va en su PROPIA transacción. Antes compartían un único
        # ``begin()``: bastaba con que la primera sentencia fallara para que
        # PostgreSQL abortara el bloque entero y se perdieran también las
        # columnas siguientes, que eran válidas. Aislarlas hace que un fallo
        # puntual (permisos, tipo) no arrastre a las demás.
        sentencias = (
            # ``DEFAULT false`` y NO ``DEFAULT 0``: PostgreSQL rechaza el
            # literal entero sobre una columna boolean con
            # ``DatatypeMismatch``. Ese error era el origen del 500: el ALTER
            # moría, la columna nunca se creaba y cada ``SELECT
            # configuracion.*`` seguía fallando con ``UndefinedColumn``.
            "ALTER TABLE configuracion ADD COLUMN IF NOT EXISTS recorrido_inicial_oculto BOOLEAN DEFAULT false",
            # Columnas recientes del bloque LatAm: si el salto es mayor que un
            # solo head, también faltarían y producirían el mismo 500.
            "ALTER TABLE configuracion ADD COLUMN IF NOT EXISTS etiqueta_id_fiscal VARCHAR(20) DEFAULT 'RIF'",
            "ALTER TABLE configuracion ADD COLUMN IF NOT EXISTS tasa_cambio FLOAT",
            "ALTER TABLE configuracion ADD COLUMN IF NOT EXISTS fuente_tipo_cambio VARCHAR(120) DEFAULT ''",
            "ALTER TABLE configuracion ADD COLUMN IF NOT EXISTS fecha_tasa DATE",
            "ALTER TABLE presupuestos ADD COLUMN IF NOT EXISTS total_calculado FLOAT",
            # Bloque planos: altura libre de paramentos (head e4b8c2d6a190).
            # El deploy del 23/08/2026 subió el modelo sin ejecutar la
            # migración y cada apertura del visor de planos devolvía 500 con
            # ``UndefinedColumn: planos_obra.altura_libre_m does not exist``.
            "ALTER TABLE planos_obra ADD COLUMN IF NOT EXISTS altura_libre_m FLOAT",
        )
        sin_permiso_ddl = False
        for sentencia in sentencias:
            if sin_permiso_ddl:
                break
            try:
                with eng.begin() as conn:
                    conn.execute(text(sentencia))
            except Exception as exc:  # noqa: PERF203 - cada DDL es independiente
                logging.getLogger("cotizat").warning(
                    "No se pudo aplicar «%s»: %s", sentencia, exc
                )
                # El rol de la app no es dueño de la tabla: los ALTER
                # siguientes fallarán igual y solo alargan el arranque en frío.
                if "InsufficientPrivilege" in type(exc).__name__ or "must be owner" in str(exc):
                    sin_permiso_ddl = True
                    logging.getLogger("cotizat").warning(
                        "Sin permisos DDL en configuracion: se omite el resto de "
                        "ALTER. Ejecuta `alembic upgrade head` con MIGRATION_DATABASE_URL."
                    )
        with eng.begin() as conn:
            # Si la versión sigue en el head anterior y ya añadimos la columna,
            # avanzamos la marca para que el próximo ``alembic upgrade head``
            # no intente crearla de nuevo y falle con "already exists".
            #
            # Solo se avanza si la columna existe DE VERDAD: marcar la revisión
            # como aplicada sin haberla creado (p. ej. si el ALTER falló por
            # permisos) haría que ``alembic upgrade head`` la diera por hecha y
            # la columna no se crearía jamás, dejando el 500 permanente.
            try:
                columna_creada = conn.execute(text("""
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'configuracion'
                      AND column_name = 'recorrido_inicial_oculto'
                """)).first() is not None
                altura_creada = conn.execute(text("""
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'planos_obra'
                      AND column_name = 'altura_libre_m'
                """)).first() is not None
                cur = conn.execute(text("SELECT version_num FROM public.alembic_version")).scalar_one_or_none()
                if not columna_creada:
                    logging.getLogger("cotizat").warning(
                        "La columna recorrido_inicial_oculto sigue sin existir: "
                        "no se avanza alembic_version (ejecuta `alembic upgrade head`)."
                    )
                elif cur == "c3e9a1b7d4f2":
                    conn.execute(text("UPDATE public.alembic_version SET version_num = 'b1c2d3e4f5a6'"))
                    logging.getLogger("cotizat").info("alembic_version avanzada de c3e9a1b7d4f2 a b1c2d3e4f5a6 tras auto-reparación.")
                elif cur == "b1c2d3e4f5a6":
                    # No se puede marcar b2/c0 desde esta reparación: planos
                    # crea tablas, GRANT y políticas RLS. Si se avanzara solo
                    # por haber creado columnas de configuración, Alembic ya no
                    # ejecutaría la migración real y el visor fallaría con
                    # ``permission denied`` o ``undefined table``.
                    logging.getLogger("cotizat").warning(
                        "alembic_version sigue en b1c2d3e4f5a6: no se marca "
                        "planos como aplicado automáticamente. Ejecuta `alembic upgrade head`."
                    )
                elif cur == "c0d1e2f3a4b5":
                    # Sí se puede avanzar a e4b8c2d6a190: a diferencia de
                    # b2/c0 (tablas, GRANT y políticas RLS), esta revisión solo
                    # añade una columna NULL, exactamente el ALTER de arriba.
                    # Se avanza siempre que la columna exista DE VERDAD, para
                    # no repetir el 500 permanente del visor de planos.
                    if altura_creada:
                        conn.execute(text("UPDATE public.alembic_version SET version_num = 'e4b8c2d6a190'"))
                        logging.getLogger("cotizat").info("alembic_version avanzada de c0d1e2f3a4b5 a e4b8c2d6a190 tras auto-reparación.")
                    else:
                        logging.getLogger("cotizat").warning(
                            "Falta planos_obra.altura_libre_m: no se avanza "
                            "alembic_version (ejecuta `alembic upgrade head`)."
                        )
                elif cur is None:
                    logging.getLogger("cotizat").warning(
                        "Base sin alembic_version: no se inserta un head ficticio. "
                        "Ejecuta `alembic upgrade head`."
                    )
            except Exception:
                # La tabla alembic_version puede no ser visible para este rol
                pass
        _asegurar_permisos_planos_postgres(eng)
        eng.dispose()
        logging.getLogger("cotizat").info("Esquema Postgres asegurado (columnas/permisos verificados).")
    except Exception as exc:
        logging.getLogger("cotizat").warning("No se pudo auto-reparar esquema Postgres (se usará fallback de lectura): %s", exc)


def init_db():
    """Inicializa SQLite local o comprueba el esquema versionado de la web.

    Las instalaciones SQLite conservan la migración no destructiva histórica.
    En PostgreSQL el esquema debe aplicarse previamente con Alembic; ejecutar
    DDL implícito al arrancar varias instancias web produciría carreras.

    Tras el merge b1c2d3e4f5a6 la base de producción quedó sin la columna
    ``recorrido_inicial_oculto`` (el deploy subió el código pero no se
    ejecutó ``alembic upgrade head``). El chequeo estricto de head hacía que
    el arranque logueara el error pero la página siguiera 500 por
    ``UndefinedColumn`` en cada ``SELECT configuracion.*``. Ahora se intenta
    una auto-reparación best-effort (ALTER IF NOT EXISTS) antes de verificar
    el head; si no hay permisos, la capa de lectura hace fallback y la app
    no se cae.
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
        # Best-effort: añade columnas que faltan si la migración no se ejecutó
        try:
            _asegurar_esquema_postgres()
        except Exception as exc:
            logging.getLogger("cotizat").warning("Fallo en _asegurar_esquema_postgres: %s", exc)
        # El head debe coincidir, pero un desajuste no debe tumbar la app si
        # las columnas ya fueron reparadas: se loguea y se continúa con fallback
        try:
            _verificar_head_alembic_postgresql()
        except RuntimeError as exc:
            logging.getLogger("cotizat").warning("Head Alembic desactualizado pero columnas aseguradas, la app continúa con fallback: %s", exc)
        try:
            _verificar_rol_aplicacion_postgresql()
        except RuntimeError as exc:
            # El rol incorrecto es un error de despliegue, pero tampoco debe
            # dejar la página 500 si ya está en producción con tráfico
            logging.getLogger("cotizat").warning(str(exc))
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
