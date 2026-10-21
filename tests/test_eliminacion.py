"""Solicitud de eliminación total de cuenta y datos (bloque 2).

Cubre el ciclo de la solicitud desde /cuenta: registrarla con
reautenticación, verla pendiente, cancelarla sin contraseña, la
idempotencia y el aviso al buzón del titular. El cliente de GoTrue se
sustituye por un doble (como en ``test_cuenta``): ninguna prueba contacta
con Supabase. La ejecución de la supresión es el bloque 3 y no se prueba
aquí; esto solo registra la petición formal y deja la cuenta usable.
"""
from datetime import datetime
from urllib.parse import unquote

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from app import database as database_module
from app.routers import common
from app.auth import (
    ACCESS_COOKIE,
    REFRESH_COOKIE,
    InvalidCredentials,
    SupabaseAuthClient,
    SupabaseAuthSettings,
)
from app.database import Base, get_authenticated_db
from app.main import app
from app.models import Membresia, Organizacion, SolicitudEliminacion, Usuario
from app.services.eliminacion import hash_email

from migrations.versions import (
    p5f1c8d2a7b4_solicitudes_eliminacion as migracion_eliminacion,
)

AUTH_ID = "1b2c3d4e-5f60-4a7b-8c9d-0e1f2a3b4c5d"
EMAIL = "persona@example.com"
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


def _tokens_ok():
    return {
        "access_token": "access-token",
        "refresh_token": "refresh-token",
        "expires_in": 3600,
        "user": {
            "id": AUTH_ID,
            "email": EMAIL,
            "email_confirmed_at": "2026-08-13T00:00:00Z",
            "user_metadata": {"name": "Persona de prueba"},
        },
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
        organizacion = Organizacion(nombre="Constructora", slug="constructora-elim")
        usuario = Usuario(
            auth_user_id=AUTH_ID,
            email=EMAIL,
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

    monkeypatch.setattr(common, "DATABASE_IS_SQLITE", False)

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


def _cliente():
    client = TestClient(app, base_url="https://cotizat.test")
    client.cookies.set(ACCESS_COOKIE, "access-token")
    client.cookies.set(REFRESH_COOKIE, "refresh-token")
    return client


def _aviso_capturado(monkeypatch):
    llamadas = []

    def _fake(**kwargs):
        llamadas.append(kwargs)
        return "aviso-id"

    monkeypatch.setattr(
        "app.services.email.enviar_solicitud_eliminacion_por_email", _fake
    )
    return llamadas


def _solicitudes(Session):
    with Session() as db:
        return db.query(SolicitudEliminacion).order_by(SolicitudEliminacion.id).all()


def _post_solicitar(client, clave="clave-actual", motivo=""):
    return client.post(
        "/cuenta/eliminacion",
        data={"password_actual": clave, "motivo": motivo},
        headers={"Origin": "https://cotizat.test"},
        follow_redirects=False,
    )


# ---------------------------------------------------------------------------
# Panel: formulario, solicitud pendiente y cancelación
# ---------------------------------------------------------------------------

def test_panel_ofrece_solicitar_la_eliminacion(entorno):
    with _cliente() as client:
        respuesta = client.get("/cuenta")
    assert respuesta.status_code == 200
    assert "Eliminar mi cuenta y mis datos" in respuesta.text
    assert 'action="/cuenta/eliminacion"' in respuesta.text
    assert 'name="password_actual"' in respuesta.text
    assert "solicitud de eliminación en curso" not in respuesta.text


def test_solicitar_reautentica_registra_y_avisa(entorno, monkeypatch):
    Session, _usuario_id = entorno
    doble = ClienteAuthDoble([_tokens_ok()])
    monkeypatch.setattr(common, "SupabaseAuthClient", lambda _s=None: doble)
    avisos = _aviso_capturado(monkeypatch)

    with _cliente() as client:
        respuesta = _post_solicitar(client, motivo="Cierro la empresa.")

    assert respuesta.status_code == 303
    assert "Solicitud registrada" in unquote(respuesta.headers["location"])
    # Solo la reautenticación: ningún otro toque a Supabase.
    assert doble.calls == [
        ("POST", "/auth/v1/token?grant_type=password",
         {"email": EMAIL, "password": "clave-actual"}, "")
    ]

    filas = _solicitudes(Session)
    assert len(filas) == 1
    fila = filas[0]
    assert fila.estado == "pendiente"
    assert fila.auth_user_id == AUTH_ID
    assert fila.email == EMAIL
    assert fila.motivo == "Cierro la empresa."
    assert fila.email_hash == hash_email(EMAIL)

    assert len(avisos) == 1
    assert avisos[0]["email"] == EMAIL
    assert avisos[0]["motivo"] == "Cierro la empresa."


def test_clave_incorrecta_no_registra_nada(entorno, monkeypatch):
    Session, _usuario_id = entorno
    doble = ClienteAuthDoble(
        error=InvalidCredentials("Email, contraseña o sesión no válidos.")
    )
    monkeypatch.setattr(common, "SupabaseAuthClient", lambda _s=None: doble)
    avisos = _aviso_capturado(monkeypatch)

    with _cliente() as client:
        respuesta = _post_solicitar(client, clave="equivocada")

    assert respuesta.status_code == 400
    assert _solicitudes(Session) == []
    assert avisos == []


def test_panel_muestra_la_pendiente_y_cancelarla_la_retira(entorno, monkeypatch):
    Session, _usuario_id = entorno
    doble = ClienteAuthDoble([_tokens_ok()])
    monkeypatch.setattr(common, "SupabaseAuthClient", lambda _s=None: doble)
    _aviso_capturado(monkeypatch)

    with _cliente() as client:
        _post_solicitar(client)
        panel = client.get("/cuenta")
        assert "solicitud de eliminación en curso" in panel.text
        assert 'action="/cuenta/eliminacion/cancelar"' in panel.text
        # El formulario de solicitar desaparece mientras hay una pendiente.
        assert 'action="/cuenta/eliminacion"' not in panel.text

        doble.calls.clear()
        respuesta = client.post(
            "/cuenta/eliminacion/cancelar",
            headers={"Origin": "https://cotizat.test"},
            follow_redirects=False,
        )
        assert respuesta.status_code == 303
        assert "cancelada" in unquote(respuesta.headers["location"])
        # Cancelar no reautentica: es la dirección segura.
        assert doble.calls == []

        panel = client.get("/cuenta")
        assert 'action="/cuenta/eliminacion"' in panel.text

    filas = _solicitudes(Session)
    assert len(filas) == 1
    assert filas[0].estado == "cancelada"
    assert filas[0].cancelada_at is not None


def test_segunda_solicitud_no_duplica_ni_exige_clave(entorno, monkeypatch):
    Session, _usuario_id = entorno
    doble = ClienteAuthDoble([_tokens_ok()])
    monkeypatch.setattr(common, "SupabaseAuthClient", lambda _s=None: doble)
    _aviso_capturado(monkeypatch)

    with _cliente() as client:
        _post_solicitar(client)
        doble.calls.clear()
        # Incluso con la clave mal: ya hay una en curso y nada nuevo ocurre.
        doble.error = InvalidCredentials("no debería ni intentarlo")
        respuesta = _post_solicitar(client, clave="lo-que-sea")

    assert respuesta.status_code == 303
    assert "Ya tienes una solicitud" in unquote(respuesta.headers["location"])
    assert doble.calls == []
    assert len(_solicitudes(Session)) == 1


def test_cancelar_sin_pendiente_es_inofensivo(entorno):
    Session, _usuario_id = entorno
    with _cliente() as client:
        respuesta = client.post(
            "/cuenta/eliminacion/cancelar",
            headers={"Origin": "https://cotizat.test"},
            follow_redirects=False,
        )
    assert respuesta.status_code == 303
    assert "No tienes ninguna solicitud" in unquote(respuesta.headers["location"])
    assert _solicitudes(Session) == []


# ---------------------------------------------------------------------------
# Servicio: la marca irreversible del email
# ---------------------------------------------------------------------------

def test_hash_email_es_estable_salado_y_normaliza():
    assert hash_email(" Persona@Example.COM ") == hash_email(EMAIL)
    assert len(hash_email(EMAIL)) == 64
    assert hash_email(EMAIL) != hash_email("otra@example.com")
    # No es el SHA-256 pelado del email: lleva la sal del despliegue.
    import hashlib

    assert hash_email(EMAIL) != hashlib.sha256(EMAIL.encode()).hexdigest()
    assert hash_email("") == ""


# ---------------------------------------------------------------------------
# Migración: definición PostgreSQL (RLS de operador + puertas guardadas)
# ---------------------------------------------------------------------------

def _capturar_upgrade(monkeypatch, *, postgres: bool):
    statements = []
    tablas = []
    monkeypatch.setattr(migracion_eliminacion, "_postgres", lambda: postgres)
    monkeypatch.setattr(
        migracion_eliminacion.op,
        "create_table",
        lambda nombre, *a, **k: tablas.append(nombre),
    )
    monkeypatch.setattr(
        migracion_eliminacion.op, "create_index", lambda *a, **k: None
    )
    monkeypatch.setattr(
        migracion_eliminacion.op,
        "execute",
        lambda statement: statements.append(str(statement)),
    )
    migracion_eliminacion.upgrade()
    return statements, tablas


def test_migracion_postgresql_rls_operador_y_funciones_con_claim(monkeypatch):
    statements, tablas = _capturar_upgrade(monkeypatch, postgres=True)
    assert tablas == ["solicitudes_eliminacion"]
    sql = "\n".join(statements)

    # Tabla del operador: solo SELECT/INSERT/UPDATE y RLS forzado.
    assert "GRANT SELECT, INSERT, UPDATE ON public.solicitudes_eliminacion" in sql
    assert "ALTER TABLE public.solicitudes_eliminacion FORCE ROW LEVEL SECURITY" in sql
    for nombre in ("cotizat_se_select", "cotizat_se_insert", "cotizat_se_update"):
        assert f"CREATE POLICY {nombre} ON public.solicitudes_eliminacion" in sql
    # Sin borrado: la solicitud es el acta y sobrevive a la purga.
    assert "FOR DELETE" not in sql
    assert "cotizat_se_delete" not in sql

    # Las tres puertas del cliente: SECURITY DEFINER con search_path fijo,
    # ejecución solo para el rol de aplicación y guarda de claim.
    for funcion in (
        "solicitar_eliminacion(",
        "solicitud_eliminacion_pendiente(",
        "cancelar_solicitud_eliminacion(",
    ):
        assert f"CREATE OR REPLACE FUNCTION cotizat_security.{funcion}" in sql
    assert sql.count("SECURITY DEFINER") >= 3
    assert sql.count("SET search_path = pg_catalog, public") >= 3
    assert sql.count("current_setting('cotizat.auth_user_id', true)") >= 3
    assert "RAISE EXCEPTION 'La sesión no corresponde a la cuenta indicada.'" in sql
    assert "FROM PUBLIC" in sql
    assert "TO cotizat_app" in sql
    # Idempotencia y cancelación solo de la pendiente propia.
    assert "estado = 'pendiente'" in sql
    assert "SET estado = 'cancelada'" in sql


def test_migracion_en_sqlite_solo_crea_la_tabla(monkeypatch):
    statements, tablas = _capturar_upgrade(monkeypatch, postgres=False)
    assert tablas == ["solicitudes_eliminacion"]
    assert statements == []


def test_migracion_cuelga_del_head_anterior_y_es_el_actual():
    assert migracion_eliminacion.down_revision == "o2e4a6c8b1d3"
    assert migracion_eliminacion.revision == "p5f1c8d2a7b4"
    assert migracion_eliminacion.revision == database_module.EXPECTED_ALEMBIC_HEAD
