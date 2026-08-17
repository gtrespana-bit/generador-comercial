"""Recorrido HTTP de quien acepta una invitación **sin tener cuenta previa**.

Incidencia reportada el 15/08/2026 tras las pruebas E2E de Auth. El recorrido
funcionaba, pero perdía el hilo por el camino:

1. La persona recibe el email y pulsa el enlace.
2. La página le dice, correctamente, que cree una cuenta.
3. Se registra y confirma el email desde el correo de Supabase.
4. Inicia sesión… y aterriza en **«Crea el espacio de tu empresa»**, sin
   ninguna opción para aceptar la invitación que motivó todo.
5. Tiene que volver al correo y pulsar el enlace por **segunda** vez.

Causa raíz: el enlace de confirmación de Supabase apunta al ``redirect_to``
fijo de ``registrar_cuenta`` (``/acceso``), sin conservar el
``?next=/invitaciones/<token>/aceptar``. Al perderse el ``next``, y viviendo el
token únicamente dentro del email, la invitación era invisible desde dentro de
la aplicación.

Estas pruebas fijan el comportamiento corregido sobre las rutas reales, con la
dependencia autenticada sustituida (igual que hace ``tests/test_cuenta.py``):
sin cuentas reales, sin red y sin credenciales.
"""
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.requests import Request
from starlette.testclient import TestClient

from app import main as main_module
from app.routers import common
from app.auth import (
    ACCESS_COOKIE,
    ORGANIZATION_COOKIE,
    REFRESH_COOKIE,
    SupabaseAuthSettings,
    SupabaseIdentity,
)
from app.database import Base, get_authenticated_db
from app.main import app
from app.models import InvitacionOrganizacion, Membresia, Organizacion, Usuario
from app.services.invitations import crear_invitacion

AUTH_ID = "3f8b1c22-9a4d-4a71-8f0e-2d5b7c9e1a03"
SETTINGS = SupabaseAuthSettings(
    url="https://project.supabase.co",
    publishable_key="sb_publishable_test",
    cookie_secure=True,
)


@pytest.fixture
def invitado_recien_registrado(monkeypatch):
    """Usuario con email confirmado, invitación vigente y **sin organización**.

    Es exactamente el estado del paso 4: la cuenta existe y está verificada,
    pero todavía no pertenece a ninguna empresa.
    """
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    with Session() as seed:
        organizacion = Organizacion(nombre="Constructora Anfitriona", slug="anfitriona")
        propietario = Usuario(email="duena@example.com", nombre="Dueña")
        invitado = Usuario(
            auth_user_id=AUTH_ID,
            email="persona@example.com",
            nombre="Persona",
            email_verificado_at=datetime(2026, 8, 15),
        )
        seed.add_all([organizacion, propietario, invitado])
        seed.flush()
        seed.add(
            Membresia(
                organizacion_id=organizacion.id,
                usuario_id=propietario.id,
                rol="propietario",
            )
        )
        seed.commit()
        crear_invitacion(
            seed,
            organizacion_id=organizacion.id,
            actor_usuario_id=propietario.id,
            email=invitado.email,
            rol="miembro",
            ahora=datetime.utcnow(),
            vigencia=timedelta(days=7),
        )
        seed.commit()
        datos = {
            "usuario_id": invitado.id,
            "organizacion_id": organizacion.id,
        }

    # Modo PostgreSQL simulado: las rutas de organización se apagan en SQLite.
    monkeypatch.setattr(common, "DATABASE_IS_SQLITE", False)

    identidad = SupabaseIdentity(
        auth_user_id=AUTH_ID,
        email="persona@example.com",
        email_verified=True,
        name="Persona",
    )

    def _db_autenticada(request: Request):
        db = Session()
        db.info["usuario_id"] = datos["usuario_id"]
        # ``_autenticar_usuario`` deja aquí la identidad ya validada contra
        # GoTrue; las rutas leen ``email_verified`` de ella.
        request.state.supabase_identity = identidad
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_authenticated_db] = _db_autenticada
    monkeypatch.setattr(
        SupabaseAuthSettings, "from_environment", classmethod(lambda _cls: SETTINGS)
    )

    try:
        yield Session, datos
    finally:
        app.dependency_overrides.pop(get_authenticated_db, None)
        engine.dispose()


def _cliente():
    client = TestClient(app, base_url="https://cotizat.test")
    client.cookies.set(ACCESS_COOKIE, "access-token")
    client.cookies.set(REFRESH_COOKIE, "refresh-token")
    return client


def test_tras_iniciar_sesion_la_invitacion_aparece_y_se_puede_aceptar(
    invitado_recien_registrado,
):
    """El paso 4 debe ofrecer la invitación, no solo «crear organización»."""
    Session, datos = invitado_recien_registrado

    with _cliente() as client:
        pagina = client.get("/organizaciones")

    assert pagina.status_code == 200
    assert "Te invitaron a un equipo" in pagina.text
    assert "persona@example.com" in pagina.text
    assert "/invitaciones/pendientes/" in pagina.text
    # El secreto del email nunca se republica en el panel.
    with Session() as db:
        invitacion = db.query(InvitacionOrganizacion).one()
        assert invitacion.token_hash not in pagina.text


def test_aceptar_desde_el_panel_da_de_alta_la_membresia(invitado_recien_registrado):
    """Un clic, sin volver al correo: era el paso 5 que sobraba."""
    Session, datos = invitado_recien_registrado

    with Session() as db:
        invitacion_id = db.query(InvitacionOrganizacion).one().id

    with _cliente() as client:
        respuesta = client.post(
            f"/invitaciones/pendientes/{invitacion_id}/aceptar",
            follow_redirects=False,
        )

    assert respuesta.status_code == 303
    assert respuesta.headers["location"].startswith("/organizaciones")
    # Deja seleccionada la organización recién aceptada.
    assert ORGANIZATION_COOKIE in respuesta.cookies

    with Session() as db:
        membresia = (
            db.query(Membresia)
            .filter(Membresia.usuario_id == datos["usuario_id"])
            .one()
        )
        assert membresia.organizacion_id == datos["organizacion_id"]
        assert membresia.rol == "miembro"
        assert membresia.activa is True
        assert db.query(InvitacionOrganizacion).one().accepted_at is not None


def test_crear_organizacion_redirige_al_panel_si_hay_invitacion_esperando(
    invitado_recien_registrado,
):
    """El destino por omisión del registro no debe empujar a crear empresa.

    Quien fue invitado casi nunca quiere fundar su propia organización: si tiene
    una invitación vigente y ninguna membresía, se le lleva al panel donde puede
    elegir. Crear una empresa sigue estando a un clic.
    """
    with _cliente() as client:
        respuesta = client.get("/organizaciones/nueva", follow_redirects=False)

    assert respuesta.status_code == 303
    assert respuesta.headers["location"] == "/organizaciones"


def test_sin_invitaciones_se_puede_crear_organizacion_con_normalidad(
    invitado_recien_registrado,
):
    """La redirección anterior no debe estorbar al alta normal de una empresa."""
    Session, datos = invitado_recien_registrado
    with Session() as db:
        db.query(InvitacionOrganizacion).delete()
        db.commit()

    with _cliente() as client:
        respuesta = client.get("/organizaciones/nueva")

    assert respuesta.status_code == 200
    assert "Crea el espacio de tu empresa" in respuesta.text


def test_el_panel_de_organizaciones_no_se_cachea(invitado_recien_registrado):
    """Lista invitaciones y membresías: no debe quedar en cachés compartidas."""
    with _cliente() as client:
        respuesta = client.get("/organizaciones")

    assert respuesta.headers["cache-control"] == "no-store"
