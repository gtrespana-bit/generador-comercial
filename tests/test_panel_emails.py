"""Página «Correos» del panel de operador: enviar cualquier correo de prueba.

El operador necesita revisar los correos transaccionales tal cual llegan, no en
una vista previa. Esta página le deja enviar cada uno a un buzón arbitrario,
con datos de ejemplo y el mismo remitente y plantillas que producción. Lo
importante aquí es el **contorno**:

- el catálogo es la única fuente de verdad (panel y CLI comparten);
- solo el operador entra (misma puerta ``get_operator_db``);
- el destino se valida y el envío falla con un mensaje, no con un 500.
"""
import json
from datetime import date, datetime

import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import auth as auth_module
from app.auth import ACCESS_COOKIE, REFRESH_COOKIE, SupabaseAuthSettings, SupabaseIdentity
from app.database import Base, get_operator_db
from app.main import app
from app.models import Membresia, Organizacion, Usuario
from app.operadores import es_operador
from app.routers import common
from app.services import correos_prueba

AUTH_ID = "b71f4c98-2ad3-4e15-9c07-6f38ba21d4e5"
SETTINGS = SupabaseAuthSettings(
    url="https://project.supabase.co",
    publishable_key="sb_publishable_test",
    cookie_secure=True,
)


# ---------------------------------------------------------------------------
# El catálogo (fuente de verdad compartida)
# ---------------------------------------------------------------------------


def test_el_catalogo_tiene_los_ocho_correos():
    correos = correos_prueba.catalogo_correos()
    assert len(correos) == 8
    slugs = {c["slug"] for c in correos}
    assert slugs == {
        "recordatorio",
        "aviso",
        "plan_activado",
        "invitacion",
        "presupuesto",
        "respuesta_propuesta",
        "compra",
        "demo",
    }
    for c in correos:
        assert c["titulo"]
        assert c["descripcion"]
        assert c["grupo"] in {"cliente", "interno"}


def test_un_slug_desconocido_se_rechaza():
    with pytest.raises(ValueError):
        correos_prueba.enviar_correo_prueba("no-existe", "a@example.com")


def test_los_correos_internos_aceptan_destino_override(monkeypatch):
    """compra y demo van a soporte en producción; aquí van al destino pedido."""
    import os

    from app.services import email as email_module

    capturado = {}

    def fake_urlopen(request, timeout):
        capturado.update(json.loads(request.data.decode("utf-8")))
        return _Respuesta()

    monkeypatch.setenv("RESEND_API_KEY", "re_prueba")
    monkeypatch.setenv("COTIZAT_EMAIL_FROM", "CotizaT <no-responder@cotizat.test>")
    monkeypatch.setattr(email_module, "urlopen", fake_urlopen)

    correos_prueba.enviar_correo_prueba("compra", "titular@example.com")
    assert capturado["to"] == ["titular@example.com"]

    correos_prueba.enviar_correo_prueba("demo", "titular@example.com")
    assert capturado["to"] == ["titular@example.com"]


class _Respuesta:
    def __enter__(self):
        return self

    def __exit__(self, *_a):
        return False

    def read(self, _size=-1):
        return b'{"id":"resend-test"}'


# ---------------------------------------------------------------------------
# La página por HTTP (solo operador)
# ---------------------------------------------------------------------------


@pytest.fixture
def entorno_panel(monkeypatch):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    with Session() as seed:
        organizacion = Organizacion(nombre="Constructora Cliente", slug="cliente")
        usuario = Usuario(
            auth_user_id=AUTH_ID,
            email="cliente@example.com",
            nombre="Cliente",
            email_verificado_at=datetime(2026, 8, 15),
        )
        seed.add_all([organizacion, usuario])
        seed.flush()
        seed.add(
            Membresia(
                organizacion_id=organizacion.id,
                usuario_id=usuario.id,
                rol="propietario",
            )
        )
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
        request.state.supabase_identity = SupabaseIdentity(
            auth_user_id=AUTH_ID,
            email=estado["email"],
            email_verified=estado["verificado"],
            name="Persona",
        )
        if not es_operador(estado["email"], email_verificado=estado["verificado"]):
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


def _cliente():
    client = TestClient(app, base_url="https://cotizat.test")
    client.cookies.set(ACCESS_COOKIE, "access-token")
    client.cookies.set(REFRESH_COOKIE, "refresh-token")
    return client


def test_el_operador_ve_la_pagina_con_los_ocho_correos(entorno_panel, monkeypatch):
    _Session, _datos, _estado = entorno_panel
    monkeypatch.setenv("COTIZAT_OPERADORES", "titular@example.com")

    with _cliente() as client:
        # La página propia ya no existe: es una pestaña de Sistema, y la URL
        # histórica redirige a ella.
        redirección = client.get("/admin/emails", follow_redirects=False)
        assert redirección.status_code == 302
        assert redirección.headers["location"] == "/admin/sistema?tab=correos"
        respuesta = client.get("/admin/sistema?tab=correos")

    assert respuesta.status_code == 200
    assert "Catálogo de correos" in respuesta.text
    assert 'value="titular@example.com"' in respuesta.text  # destino por omisión
    for titulo in (
        "Recordatorio de vencimiento",
        "Aviso de vencimiento (manual)",
        "Plan activado",
        "Invitación a equipo",
        "Envío de presupuesto",
        "Respuesta de propuesta",
        "Notificación de compra",
        "Solicitud de demo",
    ):
        assert titulo in respuesta.text


def test_el_envio_desde_el_panel_redirige_con_confirmacion(entorno_panel, monkeypatch):
    _Session, _datos, _estado = entorno_panel
    monkeypatch.setenv("COTIZAT_OPERADORES", "titular@example.com")

    envios = []
    monkeypatch.setattr(
        correos_prueba,
        "enviar_correo_prueba",
        lambda slug, email: envios.append((slug, email)) or "id-falso",
    )

    with _cliente() as client:
        respuesta = client.post(
            "/admin/emails/enviar",
            data={"slug": "recordatorio", "destino": "titular@example.com"},
            follow_redirects=False,
        )

    assert respuesta.status_code == 303
    assert "msg=" in respuesta.headers["location"]
    assert envios == [("recordatorio", "titular@example.com")]


def test_el_panel_rechaza_un_destino_invalido(entorno_panel, monkeypatch):
    _Session, _datos, _estado = entorno_panel
    monkeypatch.setenv("COTIZAT_OPERADORES", "titular@example.com")

    llamado = {"valor": False}
    monkeypatch.setattr(
        correos_prueba,
        "enviar_correo_prueba",
        lambda slug, email: llamado.__setitem__("valor", True) or "x",
    )

    with _cliente() as client:
        respuesta = client.post(
            "/admin/emails/enviar",
            data={"slug": "recordatorio", "destino": "no-es-email"},
            follow_redirects=False,
        )

    assert respuesta.status_code == 303
    assert "error=" in respuesta.headers["location"]
    assert not llamado["valor"]


def test_un_cliente_no_accede_a_la_pagina_de_correos(entorno_panel, monkeypatch):
    _Session, _datos, estado = entorno_panel
    monkeypatch.setenv("COTIZAT_OPERADORES", "titular@example.com")
    estado["email"] = "cliente@example.com"  # legítimo, pero no operador

    with _cliente() as client:
        pagina = client.get("/admin/emails", follow_redirects=False)
        envio = client.post(
            "/admin/emails/enviar",
            data={"slug": "recordatorio", "destino": "cliente@example.com"},
            follow_redirects=False,
        )

    assert pagina.status_code in (302, 303, 403)
    assert envio.status_code in (302, 303, 403)
    assert "Correos de CotizaT" not in pagina.text
