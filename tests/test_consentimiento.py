"""E4-038 — Registro de la aceptación de términos y privacidad.

Cubre el flujo completo: el checkbox obligatorio en el registro, el registro
idempotente del consentimiento (tabla + marca en el perfil), el rellenado del
perfil al sincronizar con Auth, la aceptación desde /cuenta para cuentas
antiguas, y los invariantes de seguridad del SQL de la migración (las mismas
redes que el bloque de la prueba gratuita, porque sin PostgreSQL en el entorno
de pruebas no se pueden ejecutar las funciones SECURITY DEFINER de verdad).
"""
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from app import main as main_module  # noqa: F401  (registra las rutas)
from app.auth import (
    ACCESS_COOKIE,
    REFRESH_COOKIE,
    SupabaseAuthClient,
    SupabaseAuthSettings,
)
from app.database import Base, get_authenticated_db
from app.legal import TERMINOS_VERSION
from app.main import app
from app.models import Consentimiento, Usuario, sincronizar_usuario_auth
from app.routers import common
from app.services.consentimiento import (
    aplicar_consentimiento_a_usuario,
    registrar_consentimiento,
)

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


def _tokens():
    return {
        "access_token": "access-token",
        "refresh_token": "refresh-token",
        "expires_in": 3600,
        "user": _identidad(),
    }


# ---------------------------------------------------------------------------
# Servicio (SQLite: el mismo código que corre en escritorio y en las pruebas)
# ---------------------------------------------------------------------------


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    sesion = Session()
    yield sesion
    sesion.close()
    engine.dispose()


def test_el_registro_es_idempotente_por_version(db):
    assert registrar_consentimiento(
        db, email="Fulano@Example.com", nombre="Fulano", version="1.1", ip_hash="abc"
    ) is True
    # Misma versión: no duplica (la unicidad la garantiza la base).
    assert registrar_consentimiento(
        db, email="fulano@example.com", nombre="Fulano", version="1.1", ip_hash="abc"
    ) is False
    assert db.query(Consentimiento).count() == 1
    # Versión distinta: fila nueva (futuro re-consentimiento).
    assert registrar_consentimiento(
        db, email="fulano@example.com", nombre="Fulano", version="2.0"
    ) is True
    assert db.query(Consentimiento).count() == 2


def test_email_vacio_o_version_vacia_no_registran(db):
    assert registrar_consentimiento(db, email="", version="1.1") is False
    assert registrar_consentimiento(db, email="fulano@example.com", version="") is False
    assert db.query(Consentimiento).count() == 0


def test_sincronizar_usuario_auth_rellena_la_marca_desde_el_consentimiento(db):
    registrar_consentimiento(
        db, email="fulano@example.com", nombre="Fulano", version=TERMINOS_VERSION
    )
    usuario = sincronizar_usuario_auth(
        db, "uuid-1", "fulano@example.com", "Fulano", True
    )
    assert usuario.acepto_terminos_version == TERMINOS_VERSION
    assert usuario.acepto_terminos_at is not None


def test_sin_consentimiento_el_perfil_queda_sin_marca(db):
    usuario = sincronizar_usuario_auth(
        db, "uuid-1", "mengana@example.com", "Mengana", True
    )
    assert usuario.acepto_terminos_version == ""
    assert usuario.acepto_terminos_at is None


def test_aplicar_consentimiento_rellena_la_marca_del_perfil(db):
    usuario = sincronizar_usuario_auth(
        db, "uuid-1", "mengana@example.com", "Mengana", True
    )
    assert aplicar_consentimiento_a_usuario(db, usuario) is False

    registrar_consentimiento(
        db, email="mengana@example.com", nombre="Mengana", version=TERMINOS_VERSION
    )
    assert aplicar_consentimiento_a_usuario(db, usuario) is True
    assert usuario.acepto_terminos_version == TERMINOS_VERSION


def test_la_marca_asentada_no_se_pisa_en_sincronizaciones_posteriores(db):
    """El backfill solo rellena huecos: nunca degrada ni salta de versión solo.

    El cambio de versión es un acto explícito de la persona desde /cuenta
    (registra la fila nueva y actualiza la marca), no algo que ocurra de
    pasada al iniciar sesión.
    """
    usuario = sincronizar_usuario_auth(
        db, "uuid-1", "fulano@example.com", "Fulano", True
    )
    registrar_consentimiento(db, email="fulano@example.com", version="1.1")
    sincronizar_usuario_auth(db, "uuid-1", "fulano@example.com", "Fulano", True)
    assert usuario.acepto_terminos_version == "1.1"

    # Aunque después se registre una versión posterior, la marca del perfil
    # queda en la primera aceptación asentada hasta que la persona acepte
    # explícitamente la nueva versión desde /cuenta.
    registrar_consentimiento(db, email="fulano@example.com", version="2.0")
    sincronizar_usuario_auth(db, "uuid-1", "fulano@example.com", "Fulano", True)
    assert usuario.acepto_terminos_version == "1.1"


def test_un_fallo_de_base_se_reporta_sin_romper_la_llamada(db, monkeypatch):
    """El registro es best-effort: un fallo del motor devuelve False, no lanza."""
    import app.services.consentimiento as modulo

    class _Rota:
        def __init__(self, **_kwargs):
            raise RuntimeError("base caída")

    monkeypatch.setattr(modulo, "Consentimiento", _Rota)
    assert registrar_consentimiento(
        db, email="otra@example.com", version="1.1"
    ) is False


# ---------------------------------------------------------------------------
# HTTP: el registro exige el checkbox y lo registra
# ---------------------------------------------------------------------------


@pytest.fixture
def entorno(monkeypatch):
    """Sesión autenticada en modo PostgreSQL simulado (misma receta que test_cuenta)."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as seed:
        usuario = Usuario(
            auth_user_id=AUTH_ID,
            email="persona@example.com",
            nombre="Persona",
            email_verificado_at=datetime(2026, 8, 13),
        )
        seed.add(usuario)
        seed.commit()
        usuario_id = usuario.id

    monkeypatch.setattr(common, "DATABASE_IS_SQLITE", False)

    def _db_autenticada():
        db = Session()
        db.info["usuario_id"] = usuario_id
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


def _cliente_registro(ip):
    """Cliente con dirección propia: el rate limit de /registro es por IP."""
    return TestClient(app, base_url="https://cotizat.test", client=(ip, 50000))


def test_el_registro_sin_checkbox_no_crea_cuenta(monkeypatch):
    """Sin aceptación no hay alta: ni siquiera se llama a Supabase."""

    def _no_debe_llamarse(*_a, **_k):
        raise AssertionError("No se debe contactar con Supabase sin aceptación.")

    monkeypatch.setattr(
        SupabaseAuthSettings, "from_environment", classmethod(lambda _cls: SETTINGS)
    )
    monkeypatch.setattr(common, "SupabaseAuthClient", _no_debe_llamarse)

    with _cliente_registro("192.0.2.10") as client:
        response = client.post(
            "/registro",
            data={
                "email": "fulano@example.com",
                "password": "clave-larga-segura",
                "password_confirmation": "clave-larga-segura",
                "nombre": "Fulano",
            },
            headers={"origin": "https://cotizat.test"},
            follow_redirects=False,
        )

    assert response.status_code == 303
    destino = response.headers["location"]
    assert destino.startswith("/acceso?error=")
    assert "aceptar" in destino.lower()
    from app.database import SessionLocal

    with SessionLocal() as db:
        assert db.query(Consentimiento).filter_by(email="fulano@example.com").count() == 0


def test_el_registro_con_checkbox_registra_el_consentimiento(monkeypatch):
    monkeypatch.setenv("COTIZAT_PUBLIC_URL", "https://cotizat.online")
    doble = ClienteAuthDoble([_tokens()])
    monkeypatch.setattr(
        SupabaseAuthSettings, "from_environment", classmethod(lambda _cls: SETTINGS)
    )
    monkeypatch.setattr(common, "SupabaseAuthClient", lambda _s=None: doble)

    with _cliente_registro("192.0.2.11") as client:
        response = client.post(
            "/registro",
            data={
                "email": "mengana@example.com",
                "password": "clave-larga-segura",
                "password_confirmation": "clave-larga-segura",
                "nombre": "Mengana",
                "acepto_terminos": "1",
            },
            headers={"origin": "https://cotizat.test"},
            follow_redirects=False,
        )

    assert response.status_code == 303
    assert doble.calls, "Debe haberse contactado con Supabase para crear la cuenta."
    from app.database import SessionLocal

    with SessionLocal() as db:
        fila = (
            db.query(Consentimiento)
            .filter_by(email="mengana@example.com")
            .order_by(Consentimiento.id.desc())
            .first()
        )
        assert fila is not None
        assert fila.version == TERMINOS_VERSION
        assert fila.nombre == "Mengana"


def test_el_registro_registra_aunque_el_correo_requiera_confirmacion(monkeypatch):
    """Con confirmación por email (tokens None) la aceptación ya queda anotada."""
    monkeypatch.setenv("COTIZAT_PUBLIC_URL", "https://cotizat.online")
    doble = ClienteAuthDoble([{"user": _identidad()}])  # sin tokens
    monkeypatch.setattr(
        SupabaseAuthSettings, "from_environment", classmethod(lambda _cls: SETTINGS)
    )
    monkeypatch.setattr(common, "SupabaseAuthClient", lambda _s=None: doble)

    with _cliente_registro("192.0.2.12") as client:
        response = client.post(
            "/registro",
            data={
                "email": "quiensea@example.com",
                "password": "clave-larga-segura",
                "password_confirmation": "clave-larga-segura",
                "nombre": "Quien Sea",
                "acepto_terminos": "1",
            },
            headers={"origin": "https://cotizat.test"},
            follow_redirects=False,
        )

    assert response.status_code == 303
    assert "email" in response.headers["location"]  # revisa el correo
    from app.database import SessionLocal

    with SessionLocal() as db:
        fila = (
            db.query(Consentimiento)
            .filter_by(email="quiensea@example.com")
            .first()
        )
        assert fila is not None
        assert fila.version == TERMINOS_VERSION


# ---------------------------------------------------------------------------
# HTTP: panel de cuenta — estado y aceptación para cuentas antiguas
# ---------------------------------------------------------------------------


def test_panel_de_cuenta_muestra_el_estado_del_consentimiento(entorno):
    with _cliente(entorno) as client:
        response = client.get("/cuenta")

    assert response.status_code == 200
    assert "Términos y privacidad" in response.text
    # Sin marca: se ofrece la aceptación.
    assert 'action="/cuenta/consentimiento"' in response.text
    assert "Todavía no consta tu aceptación" in response.text


def test_panel_de_cuenta_muestra_version_y_fecha_si_ya_acepto(entorno):
    Session, usuario_id = entorno
    with Session() as db:
        usuario = db.get(Usuario, usuario_id)
        registrar_consentimiento(
            db, email=usuario.email, nombre=usuario.nombre, version=TERMINOS_VERSION
        )
        aplicar_consentimiento_a_usuario(db, usuario)
        db.commit()

    with _cliente(entorno) as client:
        response = client.get("/cuenta")

    assert response.status_code == 200
    assert TERMINOS_VERSION in response.text
    assert "Aceptaste la versión" in response.text
    assert 'action="/cuenta/consentimiento"' not in response.text


def test_aceptar_desde_cuenta_registra_y_marca(entorno):
    Session, usuario_id = entorno

    with _cliente(entorno) as client:
        response = client.post(
            "/cuenta/consentimiento",
            headers={"origin": "https://cotizat.test"},
            follow_redirects=False,
        )

    assert response.status_code == 303
    assert response.headers["location"].startswith("/cuenta")
    with Session() as db:
        usuario = db.get(Usuario, usuario_id)
        assert usuario.acepto_terminos_version == TERMINOS_VERSION
        assert usuario.acepto_terminos_at is not None
        fila = (
            db.query(Consentimiento).filter_by(email=usuario.email).first()
        )
        assert fila is not None
        assert fila.version == TERMINOS_VERSION


# ---------------------------------------------------------------------------
# Invariantes del SQL de la migración (la red que queda sin PostgreSQL real)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def migracion():
    from migrations.versions import b6d9e4c2a8f1_consentimiento_terminos as m

    return m


def test_las_funciones_fijan_su_search_path(migracion):
    for sql in (migracion.RECORD_CONSENT_SQL, migracion.OBTENER_CONSENTIMIENTO_SQL):
        assert "SET search_path = pg_catalog, public" in sql


def test_record_consent_no_puede_conceder_nada(migracion):
    """El consentimiento es un registro, no un privilegio."""
    sql = migracion.RECORD_CONSENT_SQL
    # Solo inserta en consentimientos.
    assert "INSERT INTO public.consentimientos" in sql
    assert "licencias" not in sql
    assert "usuarios" not in sql
    # Parámetros vacíos → FALSE, nunca una fila basura.
    assert "IF v_email = '' OR v_version = '' THEN" in sql
    assert "RETURN FALSE" in sql


def test_record_consent_es_idempotente(migracion):
    sql = migracion.RECORD_CONSENT_SQL
    assert "ON CONFLICT (email, version) DO NOTHING" in sql
    assert "RETURNING id INTO v_id" in sql
    assert "RETURN v_id IS NOT NULL" in sql


def test_record_consent_restaura_la_marca_de_operador_en_todas_las_salidas(migracion):
    """Tras elevar `cotizat.es_operador` no puede quedar puesta en ninguna salida."""
    sql = migracion.RECORD_CONSENT_SQL
    cuerpo = sql.split("PERFORM pg_catalog.set_config('cotizat.es_operador', 'on', true);")[1]
    restauraciones = (
        cuerpo.count("'cotizat.es_operador', v_operador_previo, true")
        + cuerpo.count("'cotizat.es_operador', COALESCE(v_operador_previo, 'off'), true")
    )
    # Salidas tras la elevación: éxito y excepción.
    assert restauraciones == 2, f"salidas sin restaurar: {restauraciones} de 2"
    assert "EXCEPTION WHEN OTHERS THEN" in sql
    assert "RAISE;" in sql


def test_obtener_consentimiento_eleva_y_restaura(migracion):
    sql = migracion.OBTENER_CONSENTIMIENTO_SQL
    assert "RETURN QUERY" in sql
    assert "FROM public.consentimientos c" in sql
    assert "ORDER BY c.aceptado_en DESC, c.id DESC" in sql
    assert "LIMIT 1" in sql
    assert "EXCEPTION WHEN OTHERS THEN" in sql


def test_la_tabla_esta_cerrada_a_los_clientes(migracion):
    """Como `licencias` y `pruebas_concedidas`: sin marca de operador, nada."""
    fuente = open(migracion.__file__, encoding="utf-8").read()
    assert "ENABLE ROW LEVEL SECURITY" in fuente
    assert "FORCE ROW LEVEL SECURITY" in fuente
    # Sin política ni permiso de borrado: el registro es inmutable.
    assert "cotizat_consentimiento_delete" not in fuente
    assert "FOR DELETE" not in fuente
    assert "GRANT DELETE" not in fuente


def test_las_funciones_son_de_propiedad_administrativa_y_solo_para_la_app(migracion):
    fuente = open(migracion.__file__, encoding="utf-8").read()
    assert fuente.count("OWNER TO CURRENT_USER") == 2
    assert fuente.count("REVOKE ALL ON FUNCTION") == 2
    assert fuente.count("GRANT EXECUTE ON FUNCTION") == 2


def test_la_migracion_encadena_con_la_cabeza_anterior(migracion):
    from app.database import EXPECTED_ALEMBIC_HEAD
    from migrations.versions import (
        c8f1a2b3d4e5_add_etiqueta_fiscal_latam as etiqueta_migracion,
        d2a7c9e4f1b3_audit_log_and_complete_baja as auditoria_migracion,
        d9e2f3a4b5c6_add_tasa_cambio_latam as tasa_migracion,
    )

    # El consentimiento ya no es la cabeza: tras el registro de auditoría
    # (E4-026/027) vienen las migraciones LatAm (S2) de etiqueta fiscal y
    # tasa de referencia; la última es lo que el runtime exige.
    from migrations.versions import (
        c5d6e7f8a9b0_merge_currency_heads as merge_migracion,
        e7b3c1d5a204_market_prices_grants_and_rls as precios_migracion,
    )
    # La cabeza conserva ahora toda la evidencia del precio nacional; cuelga
    # de los índices de rendimiento y del hotfix de permisos/RLS.
    from migrations.versions import (
        a4c8e2f7b1d6_market_price_evidence as evidencia_migracion,
        b9f4d8a2c6e1_rendimiento_indices_calientes as indices_migracion,
        c3e9a1b7d4f2_stripe_checkout as stripe_migracion,
        b1c2d3e4f5a6_ocultar_guia_inicio as ocultar_migracion,
        b2c3d4e5f6a7_add_planos_obra as planos_migration,
        c0d1e2f3a4b5_fix_planos_permissions as permisos_planos_migration,
        d1e2f3a4b5c6_planos_elementos_permissions as elementos_migracion,
        e4b8c2d6a190_planos_altura_libre as altura_migracion,
        f1b2c3d4e5a6_planos_vectoriales_schema as vectorial_migracion,
        e3a5c7d9b1f4_eventos_producto as telemetria_migracion,
        a1b8c2d4e6f0_roles_operador_y_auditoria_admin as panel_migracion,
        c2d4e6f8a1b3_operador_gestion_cliente_y_cobros as fase2_migracion,
        d3e5f7a9c2b4_web_admin_crm_y_salud as fase3_migracion,
    )
    # Fase 3 (web + CRM + salud/operación) es ahora la cabeza.
    assert fase3_migracion.revision == EXPECTED_ALEMBIC_HEAD
    assert fase3_migracion.down_revision == fase2_migracion.revision
    assert fase2_migracion.down_revision == panel_migracion.revision
    assert panel_migracion.down_revision == telemetria_migracion.revision
    assert telemetria_migracion.down_revision == vectorial_migracion.revision
    assert vectorial_migracion.down_revision == altura_migracion.revision
    assert altura_migracion.down_revision == elementos_migracion.revision
    assert elementos_migracion.down_revision == permisos_planos_migration.revision
    assert permisos_planos_migration.down_revision == planos_migration.revision
    assert planos_migration.down_revision == ocultar_migracion.revision
    assert ocultar_migracion.down_revision == stripe_migracion.revision
    assert stripe_migracion.down_revision == evidencia_migracion.revision
    assert evidencia_migracion.down_revision == indices_migracion.revision
    assert indices_migracion.down_revision == precios_migracion.revision
    assert precios_migracion.down_revision == merge_migracion.revision
    assert tasa_migracion.down_revision == etiqueta_migracion.revision
    assert etiqueta_migracion.down_revision == auditoria_migracion.revision
    assert auditoria_migracion.down_revision == migracion.revision
    assert migracion.down_revision == "a3d9c1e75b28"


# ---------------------------------------------------------------------------
# Plantillas: el formulario pide la aceptación y la página de términos
# muestra la versión que se registra
# ---------------------------------------------------------------------------


def test_el_formulario_de_registro_exige_el_checkbox():
    fuente = open(
        "app/templates/auth/access.html", encoding="utf-8"
    ).read()
    assert 'name="acepto_terminos"' in fuente
    assert "required" in fuente


def test_la_pagina_de_terminos_muestra_la_version_registrada():
    fuente = open("app/templates/legal/terminos.html", encoding="utf-8").read()
    assert "{{ terminos_version }}" in fuente
    assert "{{ terminos_version_fecha }}" in fuente
