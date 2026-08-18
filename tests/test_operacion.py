"""E3-024 — monitorización y diagnóstico de la operación web.

Lo que importa aquí: (1) los errores no capturados quedan registrados sin
exponer secretos (query strings y tokens fuera), con límite acotado y
agregación de ocurrencias; (2) el middleware captura y **relanza** — no cambia
la semántica HTTP de los 500; (3) el diagnóstico reutiliza los chequeos de
`/readyz` sin datos de tenant; y (4) el panel de operación solo lo ve el
operador, con la honestidad declarada de que el registro vive en memoria.
"""
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

import app.database as database_module
import app.services.operacion as operacion_module
from app import main as main_module
from app.routers import common
from app.auth import ACCESS_COOKIE, REFRESH_COOKIE, SupabaseAuthSettings, SupabaseIdentity
from app.database import Base, EXPECTED_ALEMBIC_HEAD, get_operator_db
from app.main import app
from app.models import Membresia, Organizacion, Usuario
from app.operadores import es_operador
from app.services.operacion import (
    MAXIMO_ERRORES,
    RegistroErrores,
    RegistroErroresMiddleware,
    capturar_excepcion,
    diagnostico_operacion,
)

AUTH_ID = "c3a24f92-7e41-4c9e-a1f2-6d8b3e5c7a10"
SETTINGS = SupabaseAuthSettings(
    url="https://project.supabase.co",
    publishable_key="sb_publishable_test",
    cookie_secure=True,
)


@pytest.fixture
def registro_limpio(monkeypatch):
    """Sustituye el registro global del proceso por uno nuevo y lo restaura."""
    nuevo = RegistroErrores()
    monkeypatch.setattr(operacion_module, "REGISTRO_ERRORES", nuevo)
    return nuevo


# ---------------------------------------------------------------------------
# Registro de errores: agregación, límite y saneamiento
# ---------------------------------------------------------------------------

def test_registro_agrega_ocurrencias_y_ordena_por_ultima_vez(registro_limpio):
    base = datetime(2026, 8, 17, 10, 0)
    registro_limpio.registrar("GET", "/presupuestos/1", "ValueError", "boom", base)
    registro_limpio.registrar("GET", "/presupuestos/1", "ValueError", "boom", base + timedelta(minutes=1))
    registro_limpio.registrar("POST", "/presupuestos", "TypeError", "otra", base + timedelta(minutes=2))

    ultimos = registro_limpio.ultimos()
    assert len(ultimos) == 2
    assert ultimos[0].ruta == "/presupuestos"  # la más reciente primero
    assert ultimos[1].ocurrencias == 2
    assert ultimos[1].primera_vez == "17/08/2026 10:00 UTC"
    assert ultimos[1].ultima_vez == "17/08/2026 10:01 UTC"


def test_registro_esta_acotado_sin_perder_los_recientes(registro_limpio):
    for indice in range(MAXIMO_ERRORES + 50):
        registro_limpio.registrar("GET", f"/ruta/{indice}", "ValueError", "x")
    assert len(registro_limpio) == MAXIMO_ERRORES
    ultimos = registro_limpio.ultimos()
    assert ultimos[0].ruta == f"/ruta/{MAXIMO_ERRORES + 49}"  # el más nuevo
    assert all("/ruta/" in e.ruta for e in ultimos)


def test_captura_sanea_query_string_y_segmentos_con_forma_de_token(registro_limpio):
    scope = {
        "type": "http",
        "method": "GET",
        "path": (
            "/invitaciones/AbCdEfGhIjKlMnOpQrStUvWxYz012345/aceptar"
            "?token=secreto&otro=1"
        ),
    }
    capturar_excepcion(scope, ValueError("fallo"))
    (unico,) = registro_limpio.ultimos()
    assert "secreto" not in unico.ruta
    assert "?" not in unico.ruta
    assert "<token>" in unico.ruta
    assert "/invitaciones/<token>/aceptar" in unico.ruta
    assert unico.tipo == "ValueError"
    assert unico.mensaje == "fallo"


def test_mensaje_de_error_no_filtra_credenciales(registro_limpio):
    scope = {"type": "http", "method": "GET", "path": "/x"}
    capturar_excepcion(scope, RuntimeError("postgres://usuario:clave@host/bd rota"))
    (unico,) = registro_limpio.ultimos()
    assert "usuario" not in unico.mensaje
    assert "clave" not in unico.mensaje
    assert unico.mensaje == "host/bd rota"


# ---------------------------------------------------------------------------
# Middleware: captura sin cambiar la semántica HTTP
# ---------------------------------------------------------------------------

def _app_que_estalla():
    async def boom(_request):
        raise ValueError("explosion-controlada")

    async def sana(_request):
        return PlainTextResponse("ok")

    return Starlette(routes=[Route("/boom", boom), Route("/sana", sana)])


def test_middleware_captura_y_relanza_el_500(registro_limpio):
    cliente = TestClient(RegistroErroresMiddleware(_app_que_estalla()), raise_server_exceptions=False)
    respuesta = cliente.get("/boom")
    assert respuesta.status_code == 500
    (unico,) = registro_limpio.ultimos()
    assert unico.metodo == "GET"
    assert unico.ruta == "/boom"
    assert unico.mensaje == "explosion-controlada"


def test_middleware_no_registra_peticiones_sanas(registro_limpio):
    cliente = TestClient(RegistroErroresMiddleware(_app_que_estalla()))
    assert cliente.get("/sana").status_code == 200
    assert len(registro_limpio) == 0


# ---------------------------------------------------------------------------
# Diagnóstico: reutiliza readiness y expone hechos operativos
# ---------------------------------------------------------------------------

def test_diagnostico_incluye_salud_hechos_y_errores(registro_limpio):
    registro_limpio.registrar("GET", "/presupuestos/1", "ValueError", "boom")
    diagnostico = diagnostico_operacion()

    assert "checks" in diagnostico["salud"]
    assert isinstance(diagnostico["salud"]["ok"], bool)
    hechos = diagnostico["hechos"]
    assert hechos["backend"] in {"sqlite", "postgresql"}
    assert hechos["head_esperado"] == EXPECTED_ALEMBIC_HEAD
    assert hechos["storage"]
    assert hechos["rate_limit"]
    assert isinstance(hechos["operadores"], list)
    assert hechos["arrancado_hace_segundos"] >= 0
    assert hechos["errores_registrados"] == 1
    assert diagnostico["errores"][0]["mensaje"] == "boom"
    assert "memoria" in diagnostico["nota_errores"]


# ---------------------------------------------------------------------------
# El panel de operación por HTTP (solo operador)
# ---------------------------------------------------------------------------

@pytest.fixture
def entorno_operador(monkeypatch):
    """Base con una organización y una sesión de operador configurable."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    with Session() as seed:
        organizacion = Organizacion(nombre="Constructora Cliente", slug="operacion")
        usuario = Usuario(
            auth_user_id=AUTH_ID,
            email="cliente@example.com",
            nombre="Cliente",
            email_verificado_at=datetime(2026, 8, 17),
        )
        seed.add_all([organizacion, usuario])
        seed.flush()
        seed.add(Membresia(
            organizacion_id=organizacion.id,
            usuario_id=usuario.id,
            rol="propietario",
        ))
        seed.commit()
        datos = {"usuario_id": usuario.id, "organizacion_id": organizacion.id}

    monkeypatch.setattr(common, "DATABASE_IS_SQLITE", False)
    monkeypatch.setattr(
        SupabaseAuthSettings, "from_environment", classmethod(lambda _cls: SETTINGS)
    )
    estado = {"email": "titular@example.com", "verificado": True}

    def _db_operador(request: Request):
        from app.auth import OrganizationAccessDenied

        db = Session()
        db.info["usuario_id"] = datos["usuario_id"]
        db.info["auth_email"] = estado["email"]
        identidad = SupabaseIdentity(
            auth_user_id=AUTH_ID,
            email=estado["email"],
            email_verified=estado["verificado"],
            name="Persona",
        )
        request.state.supabase_identity = identidad
        if not es_operador(identidad.email, email_verificado=identidad.email_verified):
            db.close()
            raise OrganizationAccessDenied("No tienes acceso a esta sección.")
        db.info["es_operador"] = True
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_operator_db] = _db_operador
    try:
        yield Session, datos, estado
    finally:
        app.dependency_overrides.pop(get_operator_db, None)
        engine.dispose()


def _cliente_operador():
    cliente = TestClient(app, base_url="https://cotizat.test")
    cliente.cookies.set(ACCESS_COOKIE, "access-token")
    cliente.cookies.set(REFRESH_COOKIE, "refresh-token")
    return cliente


def test_un_cliente_normal_no_alcanza_el_panel_de_operacion(entorno_operador, monkeypatch):
    _Session, _datos, estado = entorno_operador
    monkeypatch.setenv("COTIZAT_OPERADORES", "titular@example.com")
    estado["email"] = "cliente@example.com"

    with _cliente_operador() as cliente:
        respuesta = cliente.get("/admin/operacion", follow_redirects=False)

    assert respuesta.status_code in (302, 303, 403)
    assert "Estado del despliegue" not in respuesta.text


def test_el_operador_ve_salud_errores_y_hechos(entorno_operador, monkeypatch, registro_limpio):
    _Session, _datos, _estado = entorno_operador
    monkeypatch.setenv("COTIZAT_OPERADORES", "titular@example.com")
    registro_limpio.registrar("GET", "/presupuestos/<token>/pdf", "ValueError", "explosion")

    with _cliente_operador() as cliente:
        respuesta = cliente.get("/admin/operacion")

    assert respuesta.status_code == 200
    assert respuesta.headers["cache-control"] == "no-store"
    assert "Estado del despliegue" in respuesta.text
    assert "Hechos operativos" in respuesta.text
    assert "explosion" in respuesta.text
    # Jinja2 escapa los corchetes del segmento saneado
    assert "&lt;token&gt;" in respuesta.text
    assert "titular@example.com" in respuesta.text
    # Los chequeos de /readyz aparecen en la tabla
    assert "auth" in respuesta.text or "storage" in respuesta.text
    # La honestidad del registro en memoria está declarada
    assert "memoria de esta instancia" in respuesta.text


def test_el_panel_de_licencias_enlaza_con_operacion(entorno_operador, monkeypatch):
    _Session, _datos, _estado = entorno_operador
    monkeypatch.setenv("COTIZAT_OPERADORES", "titular@example.com")

    with _cliente_operador() as cliente:
        respuesta = cliente.get("/admin/licencias")

    assert respuesta.status_code == 200
    assert "/admin/operacion" in respuesta.text


def test_readyz_sigue_respondiendo_con_el_middleware(entorno_operador):
    # El middleware relanza las excepciones; los puntos de salud no cambian.
    with _cliente_operador() as cliente:
        respuesta = cliente.get("/readyz")
    assert respuesta.status_code in (200, 503)
    body = respuesta.json()
    assert "checks" in body


def test_head_esperado_actual_coincide_con_el_diagnostico():
    # El diagnóstico publica el mismo head que exige el runtime.
    assert diagnostico_operacion()["hechos"]["head_esperado"] == database_module.EXPECTED_ALEMBIC_HEAD
