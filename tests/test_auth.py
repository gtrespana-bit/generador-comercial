"""Supabase Auth se vincula a perfiles y membresías sin confiar en cookies."""
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.requests import Request
from starlette.responses import Response

from app.auth import (
    ACCESS_COOKIE,
    REFRESH_COOKIE,
    AuthNotConfigured,
    InvalidCredentials,
    SupabaseAuthClient,
    SupabaseAuthSettings,
    SupabaseIdentity,
    password_reset_redirect_url,
    public_app_url,
    set_auth_cookies,
)
from app.database import Base
from app.models import (
    Membresia,
    Organizacion,
    OrganizacionNoAutorizadaError,
    Partida,
    PermisoOrganizacionError,
    Usuario,
    VinculoIdentidadError,
    resolver_membresia_activa,
    sincronizar_usuario_auth,
    usar_organizacion,
)

AUTH_ID = "0691d7f2-ae24-4b7f-9e45-87ad16fdc94c"
OTHER_AUTH_ID = "31af6ed4-6959-4bfa-80f2-810d08d1b68c"


class StubAuthClient(SupabaseAuthClient):
    def __init__(self, responses):
        super().__init__(SupabaseAuthSettings(
            url="https://project.supabase.co",
            publishable_key="sb_publishable_test",
            cookie_secure=True,
        ))
        self.responses = list(responses)
        self.calls = []

    def _request_json(self, method, path, payload=None, access_token=""):
        self.calls.append((method, path, payload, access_token))
        return self.responses.pop(0)


def _user_payload(auth_id=AUTH_ID, email="persona@example.com"):
    return {
        "id": auth_id,
        "email": email,
        "email_confirmed_at": "2026-08-13T00:00:00Z",
        "user_metadata": {"name": "Persona de prueba"},
    }


def _token_payload():
    return {
        "access_token": "access-token",
        "refresh_token": "refresh-token",
        "expires_in": 3600,
        "user": _user_payload(),
    }


def _db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine)()


def test_redirect_de_login_solo_admite_rutas_locales():
    from app.main import _next_seguro

    assert _next_seguro("/presupuestos?estado=borrador") == "/presupuestos?estado=borrador"
    assert _next_seguro("https://malicioso.example") == "/"
    assert _next_seguro("//malicioso.example") == "/"
    assert _next_seguro("/\\malicioso.example") == "/"
    assert _next_seguro("/ruta\nSet-Cookie: ataque=1") == "/"


def test_configuracion_auth_exige_url_https_y_clave_publicable(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_PUBLISHABLE_KEY", raising=False)
    with pytest.raises(AuthNotConfigured):
        SupabaseAuthSettings.from_environment()

    monkeypatch.setenv("SUPABASE_URL", "http://project.supabase.co")
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "sb_publishable_test")
    with pytest.raises(AuthNotConfigured):
        SupabaseAuthSettings.from_environment()

    monkeypatch.setenv("SUPABASE_URL", "https://project.supabase.co")
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "sb_secret_no_debe_usarse")
    with pytest.raises(AuthNotConfigured, match="sb_publishable"):
        SupabaseAuthSettings.from_environment()


def test_configuracion_auth_acepta_jwt_legacy_de_anon(monkeypatch):
    """Los proyectos antiguos muestran claves JWT eyJ... (anon); no deben
    rechazarse al arrancar. La firma la valida Supabase, no la app."""
    jwt = "eyJhbGciOiJIUzI1NiJ9.eyJyb2xlIjoiYW5vbiJ9.signature-part-123"
    monkeypatch.setenv("SUPABASE_URL", "https://project.supabase.co")
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", jwt)
    settings = SupabaseAuthSettings.from_environment()
    assert settings.publishable_key == jwt


def test_url_publica_de_recuperacion_es_fija_y_https(monkeypatch):
    monkeypatch.setenv("COTIZAT_PUBLIC_URL", "https://cotizat.example.com")
    assert password_reset_redirect_url() == (
        "https://cotizat.example.com/restablecer-clave"
    )
    assert public_app_url("/invitaciones/token-seguro") == (
        "https://cotizat.example.com/invitaciones/token-seguro"
    )
    monkeypatch.setenv("COTIZAT_PUBLIC_URL", "https://usuario@malicioso.example")
    with pytest.raises(AuthNotConfigured, match="COTIZAT_PUBLIC_URL"):
        password_reset_redirect_url()


def test_recuperacion_usa_endpoints_gotrue_sin_secret_key():
    client = StubAuthClient([{}, _user_payload()])
    redirect = "https://cotizat.example.com/restablecer-clave"

    client.request_password_reset(" Persona@Example.com ", redirect)
    identity = client.update_password("recovery-access-token", "nueva-clave-segura")

    assert client.calls[0] == (
        "POST",
        "/auth/v1/recover",
        {"email": "persona@example.com", "redirect_to": redirect},
        "",
    )
    assert client.calls[1] == (
        "PUT",
        "/auth/v1/user",
        {"password": "nueva-clave-segura"},
        "recovery-access-token",
    )
    assert identity.email == "persona@example.com"


def test_recuperacion_rechaza_password_corta_antes_de_contactar_supabase():
    client = StubAuthClient([])
    with pytest.raises(InvalidCredentials, match="8 caracteres"):
        client.update_password("recovery-token", "corta")
    assert client.calls == []


def test_login_y_refresh_consumen_los_endpoints_de_gotrue():
    client = StubAuthClient([_token_payload(), _token_payload()])

    login = client.sign_in(" Persona@Example.com ", "no-se-registra")
    refreshed = client.refresh("refresh-token")

    assert login.identity == SupabaseIdentity(
        AUTH_ID, "persona@example.com", "Persona de prueba", True
    )
    assert refreshed.access_token == "access-token"
    assert client.calls[0] == (
        "POST",
        "/auth/v1/token?grant_type=password",
        {"email": "persona@example.com", "password": "no-se-registra"},
        "",
    )
    assert client.calls[1][1] == "/auth/v1/token?grant_type=refresh_token"


def test_tokens_quedan_en_cookies_httponly_secure():
    client = StubAuthClient([_token_payload()])
    response = Response()

    set_auth_cookies(response, client.sign_in("persona@example.com", "clave"), True)

    cookies = response.headers.getlist("set-cookie")
    assert any(value.startswith(f"{ACCESS_COOKIE}=") for value in cookies)
    assert any(value.startswith(f"{REFRESH_COOKIE}=") for value in cookies)
    assert all("HttpOnly" in value and "Secure" in value and "SameSite=lax" in value for value in cookies)


def test_identidad_supabase_se_vincula_por_email_una_sola_vez():
    engine, db = _db()
    try:
        anterior = Usuario(email="persona@example.com", nombre="Perfil anterior")
        db.add(anterior)
        db.commit()

        usuario = sincronizar_usuario_auth(
            db, AUTH_ID, "PERSONA@example.com", "Nombre de Auth", True
        )
        db.commit()

        assert usuario.id == anterior.id
        assert usuario.auth_user_id == AUTH_ID
        assert usuario.nombre == "Perfil anterior"
        assert isinstance(usuario.email_verificado_at, datetime)

        with pytest.raises(VinculoIdentidadError):
            sincronizar_usuario_auth(
                db, OTHER_AUTH_ID, "persona@example.com", "Intruso", True
            )
    finally:
        db.close()
        engine.dispose()


def test_cookie_de_organizacion_solo_resuelve_membresias_activas():
    engine, db = _db()
    try:
        usuario = Usuario(auth_user_id=AUTH_ID, email="persona@example.com")
        a = Organizacion(nombre="Empresa A", slug="auth-empresa-a")
        b = Organizacion(nombre="Empresa B", slug="auth-empresa-b")
        db.add_all([usuario, a, b])
        db.flush()
        miembro_a = Membresia(
            usuario_id=usuario.id, organizacion_id=a.id, rol="miembro"
        )
        db.add(miembro_a)
        db.commit()

        assert resolver_membresia_activa(db, usuario.id).id == miembro_a.id
        assert resolver_membresia_activa(db, usuario.id, a.id).id == miembro_a.id
        with pytest.raises(OrganizacionNoAutorizadaError):
            resolver_membresia_activa(db, usuario.id, b.id)
    finally:
        db.close()
        engine.dispose()


def test_dependencia_postgresql_deriva_tenant_de_membresia_no_de_variable(
    monkeypatch,
):
    import app.auth as auth_module
    import app.database as database_module

    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as seed:
        organizacion = Organizacion(nombre="Autorizada", slug="autorizada")
        usuario = Usuario(auth_user_id=AUTH_ID, email="persona@example.com")
        seed.add_all([organizacion, usuario])
        seed.flush()
        seed.add(Membresia(
            usuario_id=usuario.id,
            organizacion_id=organizacion.id,
            rol="administrador",
        ))
        seed.commit()
        organizacion_id = organizacion.id

    monkeypatch.setattr(database_module, "DATABASE_IS_SQLITE", False)
    monkeypatch.setattr(database_module, "SessionLocal", Session)
    monkeypatch.setattr(
        auth_module,
        "identity_for_request",
        lambda _request: SupabaseIdentity(
            AUTH_ID, "persona@example.com", "Persona", True
        ),
    )
    monkeypatch.setenv("COTIZAT_ORGANIZATION_ID", "999999")
    request = Request({
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [(b"cookie", f"cotizat_organization_id={organizacion_id}".encode())],
        "query_string": b"",
        "scheme": "https",
        "server": ("testserver", 443),
        "client": ("testclient", 123),
    })

    dependency = database_module.get_db(request)
    db = next(dependency)
    try:
        assert db.info["auth_user_id"] == AUTH_ID
        assert db.info["auth_email"] == "persona@example.com"
        assert db.info["organizacion_id"] == organizacion_id
        assert db.info["rol_membresia"] == "administrador"
        assert request.state.usuario.auth_user_id == AUTH_ID
    finally:
        dependency.close()
        engine.dispose()


def test_rol_lectura_bloquea_flush_y_dml_masivo():
    engine, db = _db()
    try:
        organizacion = Organizacion(nombre="Solo lectura", slug="solo-lectura")
        db.add(organizacion)
        db.commit()
        usar_organizacion(db, organizacion.id)
        db.info["rol_membresia"] = "lectura"

        db.add(Partida(nombre="No permitida"))
        with pytest.raises(PermisoOrganizacionError, match="solo lectura"):
            db.commit()
        db.rollback()

        db.info.pop("rol_membresia")
        db.add(Partida(nombre="Existente"))
        db.commit()
        db.info["rol_membresia"] = "lectura"
        with pytest.raises(PermisoOrganizacionError, match="solo lectura"):
            db.query(Partida).update({Partida.nombre: "Cambio"})
    finally:
        db.close()
        engine.dispose()
