"""Envío de invitaciones por correo (Resend) y su degradación segura.

Cubre el bloque «envío real de emails de invitación»:

* la configuración desde el entorno (clave `re_...`, remitente válido);
* el POST a la API REST de Resend con Bearer y cuerpo correcto;
* el flujo web completo: correo enviado ⇒ no se muestra el enlace; correo no
  configurado o proveedor caído ⇒ el enlace aparece una vez en pantalla y la
  invitación ya está guardada en la base;
* el estado informativo de `/readyz`.
"""
from datetime import datetime
import json
from urllib.error import HTTPError

import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import main as main_module
from app.routers import common
import app.services.email as email_module
from app.database import Base, get_db
from app.health import readiness
from app.main import app
from app.models import InvitacionOrganizacion, Membresia, Organizacion, Usuario

AUTH_ID = "3a7b2c1d-4e5f-4a6b-8c9d-0e1f2a3b4c5d"


class _FakeHTTPResponse:
    def __init__(self, body=b"{}", status=200):
        self.body, self.status = body, status

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, _size=-1):
        return self.body


@pytest.fixture
def organizacion_con_propietario(monkeypatch):
    """Sesión real con un propietario y la organización activa."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as seed:
        organizacion = Organizacion(nombre="Constructora Piloto", slug="constructora-piloto-email")
        propietario = Usuario(
            auth_user_id=AUTH_ID,
            email="duena@example.com",
            nombre="Dueña",
            email_verificado_at=datetime(2026, 8, 13),
        )
        seed.add_all([organizacion, propietario])
        seed.flush()
        seed.add(
            Membresia(
                usuario_id=propietario.id,
                organizacion_id=organizacion.id,
                rol="propietario",
            )
        )
        seed.commit()
        ids = organizacion.id, propietario.id

    monkeypatch.setattr(common, "DATABASE_IS_SQLITE", False)
    monkeypatch.setenv("COTIZAT_PUBLIC_URL", "https://cotizat.test")
    activa = {"organizacion_id": ids[0], "usuario_id": ids[1]}

    def _db_de_la_organizacion_activa(request: Request):
        db = Session()
        db.info["organizacion_id"] = activa["organizacion_id"]
        db.info["usuario_id"] = activa["usuario_id"]
        db.info["rol_membresia"] = "propietario"
        # El get_db real publica la organización en request.state; la plantilla
        # team.html la usa para el encabezado.
        request.state.organizacion = db.get(Organizacion, activa["organizacion_id"])
        request.state.membresia = None
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _db_de_la_organizacion_activa
    try:
        yield Session, ids
    finally:
        app.dependency_overrides.pop(get_db, None)
        engine.dispose()


def _cliente():
    return TestClient(app, base_url="https://cotizat.test")


def _post_invitacion(client, email="persona@example.com", rol="miembro"):
    return client.post(
        "/equipo/invitaciones",
        data={"email": email, "rol": rol},
        headers={"Origin": "https://cotizat.test"},
        follow_redirects=False,
    )


# ---------------------------------------------------------------- settings


def test_settings_sin_variables_levanta_not_configured(monkeypatch):
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.delenv("COTIZAT_EMAIL_FROM", raising=False)
    with pytest.raises(email_module.EmailNotConfigured):
        email_module.EmailSettings.from_environment()


def test_settings_rechaza_clave_que_no_es_de_resend(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "sb_secret_no-es-resend")
    monkeypatch.setenv("COTIZAT_EMAIL_FROM", "CotizaT <no-responder@cotizat.test>")
    with pytest.raises(email_module.EmailNotConfigured):
        email_module.EmailSettings.from_environment()


def test_settings_rechaza_remitente_invalido(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_clave-de-prueba-no-real")
    monkeypatch.setenv("COTIZAT_EMAIL_FROM", "no-es-un-correo")
    with pytest.raises(email_module.EmailNotConfigured):
        email_module.EmailSettings.from_environment()


def test_settings_acepta_clave_re_y_remitente_valido(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_clave-de-prueba-no-real")
    monkeypatch.setenv("COTIZAT_EMAIL_FROM", "CotizaT <no-responder@cotizat.test>")
    settings = email_module.EmailSettings.from_environment()
    assert settings.api_key == "re_clave-de-prueba-no-real"
    assert settings.from_address == "CotizaT <no-responder@cotizat.test>"


# ------------------------------------------------------------ envío directo


def test_envio_posts_a_resend_con_bearer_y_cuerpo_correcto(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_clave-de-prueba-no-real")
    monkeypatch.setenv("COTIZAT_EMAIL_FROM", "CotizaT <no-responder@cotizat.test>")
    requests = []

    def fake_urlopen(request, timeout):
        requests.append((request, timeout))
        return _FakeHTTPResponse(json.dumps({"id": "envio-123"}).encode("utf-8"))

    monkeypatch.setattr(email_module, "urlopen", fake_urlopen)

    enviado_id = email_module.enviar_invitacion_por_email(
        email="persona@example.com",
        enlace="https://cotizat.test/invitaciones/token-secreto-abc",
        organizacion_nombre="Constructora Piloto",
        invitador_nombre="Dueña",
        invitador_email="duena@example.com",
        rol="miembro",
        caduca_el=datetime(2026, 8, 22),
    )
    assert enviado_id == "envio-123"
    request, timeout = requests[0]
    assert timeout == 10
    assert request.full_url == email_module.RESEND_API_URL
    assert request.method == "POST"
    assert request.headers["Authorization"] == "Bearer re_clave-de-prueba-no-real"
    # urllib guarda las cabeceras con `capitalize()`: "Content-type".
    assert request.headers["Content-type"] == "application/json"

    cuerpo = json.loads(request.data)
    assert cuerpo["from"] == "CotizaT <no-responder@cotizat.test>"
    assert cuerpo["to"] == ["persona@example.com"]
    assert "Constructora Piloto" in cuerpo["subject"]
    assert "token-secreto-abc" in cuerpo["html"]
    assert "Constructora Piloto" in cuerpo["html"]
    assert "token-secreto-abc" in cuerpo["text"]
    assert "22/08/2026" in cuerpo["html"]


def test_envio_propaga_fallo_del_proveedor(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_clave-de-prueba-no-real")
    monkeypatch.setenv("COTIZAT_EMAIL_FROM", "CotizaT <no-responder@cotizat.test>")

    def fake_urlopen(request, timeout):  # noqa: ARG001
        raise HTTPError(request.full_url, 500, "error", {}, None)

    monkeypatch.setattr(email_module, "urlopen", fake_urlopen)
    with pytest.raises(email_module.EmailSendError):
        email_module.enviar_invitacion_por_email(
            email="persona@example.com",
            enlace="https://cotizat.test/invitaciones/token-secreto-abc",
            organizacion_nombre="Constructora Piloto",
            invitador_nombre="Dueña",
            invitador_email="duena@example.com",
            rol="miembro",
            caduca_el=datetime(2026, 8, 22),
        )


# ------------------------------------------------------------ flujo web HTTP


def test_flujo_web_envia_correo_y_no_muestra_el_enlace(organizacion_con_propietario, monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_clave-de-prueba-no-real")
    monkeypatch.setenv("COTIZAT_EMAIL_FROM", "CotizaT <no-responder@cotizat.test>")
    requests = []

    def fake_urlopen(request, timeout):  # noqa: ARG001
        requests.append(request)
        return _FakeHTTPResponse(json.dumps({"id": "envio-web-1"}).encode("utf-8"))

    monkeypatch.setattr(email_module, "urlopen", fake_urlopen)

    with _cliente() as client:
        respuesta = _post_invitacion(client, email="persona@example.com")

    assert respuesta.status_code == 200
    assert "Invitación enviada a persona@example.com" in respuesta.text
    assert "Enlace generado" not in respuesta.text

    # El correo salió con el enlace de un solo uso.
    cuerpo = json.loads(requests[0].data)
    assert "persona@example.com" in cuerpo["to"]
    assert "/invitaciones/" in cuerpo["html"]
    assert "Constructora Piloto" in cuerpo["html"]

    # Y la invitación quedó guardada en la base.
    Session, _ids = organizacion_con_propietario
    with Session() as db:
        fila = (
            db.query(InvitacionOrganizacion)
            .filter(InvitacionOrganizacion.email == "persona@example.com")
            .one()
        )
        assert fila.rol == "miembro"
        assert fila.accepted_at is None
        assert fila.revoked_at is None


def test_flujo_web_sin_configuracion_muestra_el_enlace(organizacion_con_propietario, monkeypatch):
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.delenv("COTIZAT_EMAIL_FROM", raising=False)
    requests = []

    def fake_urlopen(request, timeout):  # noqa: ARG001
        requests.append(request)
        return _FakeHTTPResponse(b"{}")

    monkeypatch.setattr(email_module, "urlopen", fake_urlopen)

    with _cliente() as client:
        respuesta = _post_invitacion(client, email="persona@example.com")

    assert respuesta.status_code == 200
    assert "Enlace generado" in respuesta.text
    assert "No se pudo enviar el correo" in respuesta.text
    assert "persona@example.com" in respuesta.text
    assert requests == [], "sin configuración no debe salir ningún correo"

    Session, _ids = organizacion_con_propietario
    with Session() as db:
        fila = (
            db.query(InvitacionOrganizacion)
            .filter(InvitacionOrganizacion.email == "persona@example.com")
            .one()
        )
        assert fila.email == "persona@example.com"


def test_flujo_web_fallo_del_proveedor_muestra_el_enlace(organizacion_con_propietario, monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_clave-de-prueba-no-real")
    monkeypatch.setenv("COTIZAT_EMAIL_FROM", "CotizaT <no-responder@cotizat.test>")

    def fake_urlopen(request, timeout):  # noqa: ARG001
        raise HTTPError(request.full_url, 500, "error", {}, None)

    monkeypatch.setattr(email_module, "urlopen", fake_urlopen)

    with _cliente() as client:
        respuesta = _post_invitacion(client, email="persona@example.com")

    assert respuesta.status_code == 200
    assert "Enlace generado" in respuesta.text
    assert "No se pudo enviar el correo" in respuesta.text

    Session, _ids = organizacion_con_propietario
    with Session() as db:
        fila = (
            db.query(InvitacionOrganizacion)
            .filter(InvitacionOrganizacion.email == "persona@example.com")
            .one()
        )
        assert fila.email == "persona@example.com"


# ---------------------------------------------------------------- readiness


def test_readyz_informa_email_no_configurado(monkeypatch):
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.delenv("COTIZAT_EMAIL_FROM", raising=False)
    estado = readiness().checks
    assert estado["email"] == "no-configurado"


def test_readyz_informa_email_configurado(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_clave-de-prueba-no-real")
    monkeypatch.setenv("COTIZAT_EMAIL_FROM", "CotizaT <no-responder@cotizat.test>")
    estado = readiness().checks
    assert estado["email"] == "configurado"


def test_readyz_informa_email_mal_configurado(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "no-es-una-clave-resend")
    monkeypatch.setenv("COTIZAT_EMAIL_FROM", "CotizaT <no-responder@cotizat.test>")
    estado = readiness().checks
    assert estado["email"] == "mal-configurado"
