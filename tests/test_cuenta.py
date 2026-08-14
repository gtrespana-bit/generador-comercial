"""Panel de cuenta: perfil, cambio de contraseña y cierre de sesión.

Las rutas se ejercitan sobre SQLite en memoria sustituyendo la dependencia
autenticada, igual que haría PostgreSQL tras validar Supabase. El cliente de
GoTrue se sustituye por un doble que registra las llamadas: ninguna prueba
contacta con Supabase ni necesita credenciales reales.
"""
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.responses import Response
from starlette.testclient import TestClient

from app import main as main_module
from app.auth import (
    ACCESS_COOKIE,
    ORGANIZATION_COOKIE,
    REFRESH_COOKIE,
    AuthError,
    AuthTokens,
    InvalidCredentials,
    SupabaseAuthClient,
    SupabaseAuthSettings,
    SupabaseIdentity,
    clear_auth_cookies,
)
from app.database import Base, get_authenticated_db
from app.main import app
from app.models import Membresia, Organizacion, Usuario

AUTH_ID = "0691d7f2-ae24-4b7f-9e45-87ad16fdc94c"
SETTINGS = SupabaseAuthSettings(
    url="https://project.supabase.co",
    publishable_key="sb_publishable_test",
    cookie_secure=True,
)


class ClienteAuthDoble(SupabaseAuthClient):
    """Registra las llamadas a GoTrue sin salir a la red."""

    def __init__(self, responses=None, error=None):
        super().__init__(SETTINGS)
        self.responses = list(responses or [])
        self.error = error
        self.calls = []

    def _request_json(self, method, path, payload=None, access_token=""):
        self.calls.append((method, path, payload, access_token))
        if self.error is not None:
            raise self.error
        return self.responses.pop(0) if self.responses else {}


def _identidad(email="persona@example.com"):
    return {
        "id": AUTH_ID,
        "email": email,
        "email_confirmed_at": "2026-08-13T00:00:00Z",
        "user_metadata": {"name": "Persona de prueba"},
    }


@pytest.fixture
def entorno(monkeypatch):
    """Sesión autenticada con una organización, en modo PostgreSQL simulado."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as seed:
        organizacion = Organizacion(nombre="Constructora", slug="constructora-cuenta")
        usuario = Usuario(
            auth_user_id=AUTH_ID,
            email="persona@example.com",
            nombre="Persona",
            email_verificado_at=datetime(2026, 8, 13),
        )
        seed.add_all([organizacion, usuario])
        seed.flush()
        seed.add(Membresia(
            usuario_id=usuario.id,
            organizacion_id=organizacion.id,
            rol="propietario",
        ))
        seed.commit()
        usuario_id = usuario.id
        organizacion_id = organizacion.id

    monkeypatch.setattr(main_module, "DATABASE_IS_SQLITE", False)

    def _db_autenticada():
        db = Session()
        db.info["usuario_id"] = usuario_id
        db.info["organizacion_id"] = organizacion_id
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_authenticated_db] = _db_autenticada
    monkeypatch.setattr(
        SupabaseAuthSettings, "from_environment", classmethod(lambda _cls: SETTINGS)
    )
    try:
        yield Session, usuario_id
    finally:
        app.dependency_overrides.pop(get_authenticated_db, None)
        engine.dispose()


def _cliente(entorno):
    client = TestClient(app, base_url="https://cotizat.test")
    client.cookies.set(ACCESS_COOKIE, "access-token")
    client.cookies.set(REFRESH_COOKIE, "refresh-token")
    return client


def test_panel_muestra_perfil_organizaciones_y_salida(entorno):
    with _cliente(entorno) as client:
        response = client.get("/cuenta")
    assert response.status_code == 200
    assert "persona@example.com" in response.text
    assert "Cambiar contraseña" in response.text
    assert 'action="/salir"' in response.text
    assert "Constructora" in response.text


def test_perfil_actualiza_nombre_local_y_metadato_de_supabase(entorno, monkeypatch):
    Session, usuario_id = entorno
    doble = ClienteAuthDoble([_identidad()])
    monkeypatch.setattr(main_module, "SupabaseAuthClient", lambda _s=None: doble)

    with _cliente(entorno) as client:
        response = client.post(
            "/cuenta/perfil",
            data={"nombre": "Nombre Nuevo"},
            headers={"Origin": "https://cotizat.test"},
            follow_redirects=False,
        )

    assert response.status_code == 303
    with Session() as db:
        assert db.get(Usuario, usuario_id).nombre == "Nombre Nuevo"
    assert doble.calls == [
        ("PUT", "/auth/v1/user", {"data": {"name": "Nombre Nuevo"}}, "access-token")
    ]


def test_perfil_no_permite_cambiar_email_ni_nombre_vacio(entorno):
    Session, usuario_id = entorno
    with _cliente(entorno) as client:
        response = client.post(
            "/cuenta/perfil",
            data={"nombre": "A", "email": "otro@example.com"},
            headers={"Origin": "https://cotizat.test"},
        )
    assert response.status_code == 400
    with Session() as db:
        usuario = db.get(Usuario, usuario_id)
        assert usuario.email == "persona@example.com"
        assert usuario.nombre == "Persona"


def test_cambio_de_clave_reautentica_y_cierra_la_sesion(entorno, monkeypatch):
    doble = ClienteAuthDoble([
        {  # reautenticación con la contraseña actual
            "access_token": "access-token",
            "refresh_token": "refresh-token",
            "expires_in": 3600,
            "user": _identidad(),
        },
        _identidad(),  # PUT /auth/v1/user con la contraseña nueva
    ])
    monkeypatch.setattr(main_module, "SupabaseAuthClient", lambda _s=None: doble)

    with _cliente(entorno) as client:
        response = client.post(
            "/cuenta/clave",
            data={
                "password_actual": "clave-actual",
                "password": "clave-nueva-segura",
                "password_confirmation": "clave-nueva-segura",
            },
            headers={"Origin": "https://cotizat.test"},
            follow_redirects=False,
        )

    assert response.status_code == 303
    assert response.headers["location"].startswith("/acceso")
    assert doble.calls[0][1] == "/auth/v1/token?grant_type=password"
    assert doble.calls[0][2] == {
        "email": "persona@example.com",
        "password": "clave-actual",
    }
    assert doble.calls[1] == (
        "PUT", "/auth/v1/user", {"password": "clave-nueva-segura"}, "access-token"
    )
    borradas = " ".join(response.headers.get_list("set-cookie"))
    for cookie in (ACCESS_COOKIE, REFRESH_COOKIE, ORGANIZATION_COOKIE):
        assert f"{cookie}=" in borradas


def test_cambio_de_clave_exige_la_actual_correcta_sin_actualizar(entorno, monkeypatch):
    doble = ClienteAuthDoble(error=InvalidCredentials("Email, contraseña o sesión no válidos."))
    monkeypatch.setattr(main_module, "SupabaseAuthClient", lambda _s=None: doble)

    with _cliente(entorno) as client:
        response = client.post(
            "/cuenta/clave",
            data={
                "password_actual": "equivocada",
                "password": "clave-nueva-segura",
                "password_confirmation": "clave-nueva-segura",
            },
            headers={"Origin": "https://cotizat.test"},
        )

    assert response.status_code == 400
    # Solo se intentó la reautenticación; nunca el cambio de contraseña.
    assert [call[1] for call in doble.calls] == ["/auth/v1/token?grant_type=password"]


def test_cambio_de_clave_valida_confirmacion_y_longitud_antes_de_supabase(
    entorno, monkeypatch
):
    doble = ClienteAuthDoble()
    monkeypatch.setattr(main_module, "SupabaseAuthClient", lambda _s=None: doble)

    with _cliente(entorno) as client:
        distintas = client.post(
            "/cuenta/clave",
            data={
                "password_actual": "clave-actual",
                "password": "clave-nueva-segura",
                "password_confirmation": "otra-cosa",
            },
            headers={"Origin": "https://cotizat.test"},
        )
        corta = client.post(
            "/cuenta/clave",
            data={
                "password_actual": "clave-actual",
                "password": "corta",
                "password_confirmation": "corta",
            },
            headers={"Origin": "https://cotizat.test"},
        )

    assert distintas.status_code == corta.status_code == 400
    assert doble.calls == []


def test_salir_revoca_en_supabase_y_borra_las_cookies(entorno, monkeypatch):
    doble = ClienteAuthDoble()
    monkeypatch.setattr(main_module, "SupabaseAuthClient", lambda _s=None: doble)

    with _cliente(entorno) as client:
        response = client.post(
            "/salir",
            headers={"Origin": "https://cotizat.test"},
            follow_redirects=False,
        )

    assert response.status_code == 303
    assert response.headers["location"] == "/acceso"
    assert doble.calls == [("POST", "/auth/v1/logout", {}, "access-token")]
    borradas = " ".join(response.headers.get_list("set-cookie"))
    for cookie in (ACCESS_COOKIE, REFRESH_COOKIE, ORGANIZATION_COOKIE):
        assert f"{cookie}=" in borradas


def test_salir_cierra_la_sesion_aunque_supabase_falle(entorno, monkeypatch):
    doble = ClienteAuthDoble(error=AuthError("Supabase no responde."))
    monkeypatch.setattr(main_module, "SupabaseAuthClient", lambda _s=None: doble)

    with _cliente(entorno) as client:
        response = client.post(
            "/salir",
            headers={"Origin": "https://cotizat.test"},
            follow_redirects=False,
        )

    assert response.status_code == 303
    borradas = " ".join(response.headers.get_list("set-cookie"))
    assert f"{ACCESS_COOKIE}=" in borradas


def test_cierre_de_sesion_descarta_una_renovacion_pendiente():
    """Sin esto, el middleware reescribiría las cookies recién borradas."""

    class EstadoFalso:
        pass

    class PeticionFalsa:
        def __init__(self):
            self.state = EstadoFalso()

    request = PeticionFalsa()
    request.state.cotizat_refreshed_tokens = AuthTokens(
        access_token="nuevo",
        refresh_token="nuevo-refresh",
        expires_in=3600,
        identity=SupabaseIdentity(AUTH_ID, "persona@example.com", "Persona", True),
    )

    clear_auth_cookies(Response(), True, request)

    assert not hasattr(request.state, "cotizat_refreshed_tokens")


def test_toda_ruta_que_recibe_contrasenas_tiene_rate_limit():
    """Un panel con sesión abierta no debe permitir fuerza bruta sin límite."""
    from app.security import AuthRateLimitMiddleware

    limitadas = set(AuthRateLimitMiddleware.DEFAULT_LIMITS)
    assert {"/acceso", "/registro", "/cuenta/clave"} <= limitadas


def test_cambio_de_clave_rechaza_reutilizar_la_actual():
    doble = ClienteAuthDoble()
    with pytest.raises(InvalidCredentials, match="distinta"):
        doble.change_password(
            "access-token", "persona@example.com", "misma-clave-1", "misma-clave-1"
        )
    assert doble.calls == []
