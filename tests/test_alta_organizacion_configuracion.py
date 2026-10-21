"""Alta de una organización en una cuenta que ya tiene otras empresas.

Incidencia reportada por el titular (21/08/2026): al crear una organización
nueva solo se pedían nombre y país y la aplicación entraba directamente al
generador. El asistente de configuración (país, moneda, impuesto, nombre,
logo) no aparecía hasta **volver a entrar** a la organización.

Causa: ``crear_organizacion_web`` enviaba a ``/pago`` cuando la identidad ya
había gastado su prueba gratuita —el caso normal de una cuenta con varias
organizaciones—. El asistente solo se abría más tarde, al pasar por
``/inicio``. Con ``COTIZAT_EXIGIR_LICENCIA`` encendido, además, ``/bienvenida``
quedaba detrás del corte por licencia y una empresa sin plan no podía
configurarse nunca.

Estas pruebas fijan el comportamiento esperado sobre las rutas reales, con las
dependencias de sesión sustituidas (igual que ``tests/test_invitacion_sin_cuenta.py``).
"""
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.requests import Request
from starlette.testclient import TestClient

from app import main as main_module  # noqa: F401  (registra las rutas)
from app.auth import (
    ACCESS_COOKIE,
    ORGANIZATION_COOKIE,
    REFRESH_COOKIE,
    SupabaseAuthSettings,
    SupabaseIdentity,
)
from app.database import Base, get_authenticated_db, get_db, get_db_renovacion
from app.main import app
from app.models import (
    Configuracion,
    Membresia,
    Organizacion,
    Usuario,
    usar_organizacion,
)
from app.routers import common
from app.services.prueba_gratuita import ResultadoPrueba

AUTH_ID = "8a1f0c74-2b6d-4e39-9c58-1d7e3a5b0f42"
SETTINGS = SupabaseAuthSettings(
    url="https://project.supabase.co",
    publishable_key="sb_publishable_test",
    cookie_secure=False,
)


@pytest.fixture
def cuenta_con_empresa(monkeypatch):
    """Cuenta con una empresa ya configurada y la prueba gratuita gastada.

    Es el estado exacto del titular: la cuenta existe, tiene organizaciones y
    una prueba por identidad de correo que ya se consumió con la primera.
    """
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    with Session() as seed:
        usuario = Usuario(
            auth_user_id=AUTH_ID,
            email="constructora@example.com",
            nombre="Ana Titular",
            email_verificado_at=datetime(2026, 8, 20),
        )
        seed.add(usuario)
        seed.flush()
        primera = Organizacion(
            nombre="Constructora Uno", slug="constructora-uno", creada_por_usuario_id=usuario.id
        )
        seed.add(primera)
        seed.flush()
        seed.add(
            Membresia(organizacion_id=primera.id, usuario_id=usuario.id, rol="propietario")
        )
        seed.add(
            Configuracion(
                organizacion_id=primera.id,
                empresa_nombre="Constructora Uno",
                onboarding_completado=True,
                onboarding_modo="demo",
            )
        )
        seed.commit()
        datos = {"usuario_id": usuario.id, "organizacion_id": primera.id}

    # Modo PostgreSQL simulado: el alta de empresa se apaga en SQLite.
    monkeypatch.setattr(common, "DATABASE_IS_SQLITE", False)
    monkeypatch.setattr(
        SupabaseAuthSettings, "from_environment", classmethod(lambda _cls: SETTINGS)
    )
    # La prueba ya se gastó con la primera empresa: es lo que ocurría de verdad
    # y lo que hacía que el alta se fuera a /pago sin configurar nada.
    monkeypatch.setattr(
        "app.routers.auth.conceder_prueba",
        lambda *args, **kwargs: ResultadoPrueba(False, motivo="ya_usada"),
    )

    identidad = SupabaseIdentity(
        auth_user_id=AUTH_ID,
        email="constructora@example.com",
        email_verified=True,
        name="Ana Titular",
    )

    def _db_autenticada(request: Request):
        db = Session()
        db.info["usuario_id"] = datos["usuario_id"]
        request.state.supabase_identity = identidad
        try:
            yield db
        finally:
            db.close()

    def _db_org(request: Request):
        from app.database import _resumen_licencia_para_request

        db = Session()
        db.info["usuario_id"] = datos["usuario_id"]
        cookie = request.cookies.get(ORGANIZATION_COOKIE, "").strip()
        if cookie:
            usar_organizacion(db, int(cookie))
            db.info["rol_membresia"] = "propietario"
            request.state.licencia_resumen = _resumen_licencia_para_request(
                db, int(cookie)
            )
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_authenticated_db] = _db_autenticada
    app.dependency_overrides[get_db] = _db_org
    app.dependency_overrides[get_db_renovacion] = _db_org
    try:
        yield Session, datos
    finally:
        for dependencia in (get_authenticated_db, get_db, get_db_renovacion):
            app.dependency_overrides.pop(dependencia, None)
        engine.dispose()


def _cliente(organizacion_id: int) -> TestClient:
    client = TestClient(app, base_url="https://cotizat.test")
    client.cookies.set(ACCESS_COOKIE, "access-token", domain="cotizat.test", path="/")
    client.cookies.set(REFRESH_COOKIE, "refresh-token", domain="cotizat.test", path="/")
    client.cookies.set(
        ORGANIZATION_COOKIE, str(organizacion_id), domain="cotizat.test", path="/"
    )
    return client


def _crear_organizacion(client, nombre="Constructora Norte", pais="MX"):
    return client.post(
        "/organizaciones/nueva",
        data={"nombre": nombre, "pais": pais},
        follow_redirects=False,
    )


def test_una_empresa_nueva_siempre_entra_al_asistente_de_configuracion(
    cuenta_con_empresa,
):
    """El alta lleva a /bienvenida aunque la prueba ya esté gastada.

    Era el fallo: sin prueba, el alta saltaba a la página de planes y la
    organización nacía sin pasar por la configuración inicial.
    """
    _Session, datos = cuenta_con_empresa

    with _cliente(datos["organizacion_id"]) as client:
        respuesta = _crear_organizacion(client)

    assert respuesta.status_code == 303
    assert respuesta.headers["location"].startswith("/bienvenida"), (
        respuesta.headers["location"]
    )


def test_el_asistente_pinta_el_formulario_con_los_datos_del_alta(cuenta_con_empresa):
    """País, moneda, IVA y nombre llegan ya puestos: no se piden dos veces."""
    Session, datos = cuenta_con_empresa

    with _cliente(datos["organizacion_id"]) as client:
        alta = _crear_organizacion(client)
        nueva_organizacion_id = None
        for cookie in alta.headers.get_list("set-cookie"):
            if cookie.startswith(ORGANIZATION_COOKIE):
                nueva_organizacion_id = int(cookie.split("=", 1)[1].split(";", 1)[0])
    assert nueva_organizacion_id is not None

    with _cliente(nueva_organizacion_id) as client:
        pagina = client.get("/bienvenida")

    assert pagina.status_code == 200
    assert 'id="onboarding-form"' in pagina.text
    # El nombre comercial escrito en el alta aparece en el asistente.
    assert 'value="Constructora Norte"' in pagina.text
    # Y el país elegido viaja ya seleccionado con sus valores por defecto.
    assert 'value="México" selected' in pagina.text
    assert 'value="MXN" selected' in pagina.text

    with Session() as db:
        cfg = (
            db.query(Configuracion)
            .filter(Configuracion.organizacion_id == nueva_organizacion_id)
            .one()
        )
        assert cfg.onboarding_completado is False
        assert cfg.empresa_nombre == "Constructora Norte"
        assert cfg.empresa_pais == "México"
        assert cfg.moneda_default == "MXN"
        assert cfg.iva_default == 16
        assert cfg.etiqueta_id_fiscal == "RFC"


def test_el_asistente_no_queda_detras_del_corte_por_licencia():
    """Contrato: /bienvenida usa la puerta sin corte, no `get_db`.

    Una organización recién creada sin prueba no tiene licencia. Con
    ``COTIZAT_EXIGIR_LICENCIA`` encendido, `get_db` la dejaría en la pantalla
    de suspensión y no podría configurarse; el plan se pide al terminar.
    """
    esperadas = {("/bienvenida", "GET"), ("/bienvenida", "POST")}

    def _recorrer(rutas):
        """FastAPI envuelve los routers incluidos; hay que bajar un nivel."""
        for ruta in rutas:
            incluido = getattr(ruta, "original_router", None)
            if incluido is not None:
                yield from _recorrer(incluido.routes)
                continue
            yield ruta

    vistas = set()
    for ruta in _recorrer(app.routes):
        path = getattr(ruta, "path", "")
        if path != "/bienvenida":
            continue
        dependencias = {d.call for d in ruta.dependant.dependencies}
        for metodo in (getattr(ruta, "methods", set()) or set()) - {"HEAD", "OPTIONS"}:
            if (path, metodo) not in esperadas:
                continue
            vistas.add((path, metodo))
            assert get_db_renovacion in dependencias, (path, metodo)
            assert get_db not in dependencias, (path, metodo)
    assert vistas == esperadas


def test_terminar_el_asistente_sin_licencia_lleva_a_elegir_plan(
    cuenta_con_empresa, monkeypatch
):
    """Con el corte encendido, tras configurarse se ofrece el plan, no la suspensión."""
    _Session, datos = cuenta_con_empresa
    monkeypatch.setenv("COTIZAT_EXIGIR_LICENCIA", "true")

    with _cliente(datos["organizacion_id"]) as client:
        alta = _crear_organizacion(client)
        for cookie in alta.headers.get_list("set-cookie"):
            if cookie.startswith(ORGANIZATION_COOKIE):
                nueva_organizacion_id = int(cookie.split("=", 1)[1].split(";", 1)[0])

    with _cliente(nueva_organizacion_id) as client:
        fin = client.post(
            "/bienvenida",
            data={
                "empresa_nombre": "Constructora Norte",
                "empresa_pais": "México",
                "moneda_default": "MXN",
                "iva_default": "16",
                "modo_inicio": "limpio",
            },
            follow_redirects=False,
        )

    assert fin.status_code == 303
    assert fin.headers["location"].startswith("/pago")


def test_terminar_el_asistente_sin_corte_entra_al_panel(cuenta_con_empresa, monkeypatch):
    """Sin el corte encendido el destino sigue siendo el panel de siempre."""
    _Session, datos = cuenta_con_empresa
    monkeypatch.delenv("COTIZAT_EXIGIR_LICENCIA", raising=False)

    with _cliente(datos["organizacion_id"]) as client:
        alta = _crear_organizacion(client)
        for cookie in alta.headers.get_list("set-cookie"):
            if cookie.startswith(ORGANIZATION_COOKIE):
                nueva_organizacion_id = int(cookie.split("=", 1)[1].split(";", 1)[0])

    with _cliente(nueva_organizacion_id) as client:
        fin = client.post(
            "/bienvenida",
            data={
                "empresa_nombre": "Constructora Norte",
                "empresa_pais": "México",
                "moneda_default": "MXN",
                "iva_default": "16",
                "modo_inicio": "limpio",
            },
            follow_redirects=False,
        )

    assert fin.status_code == 303
    assert fin.headers["location"].startswith("/inicio")
