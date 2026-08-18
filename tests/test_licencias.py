"""Panel de operador y registro interno de licencias (E1-060).

Este módulo es una excepción deliberada al aislamiento multi-tenant, así que la
prioridad de estas pruebas no es que el panel funcione —eso es lo fácil— sino
que **nadie más que el operador pueda alcanzarlo**.

Las tres barreras que se verifican:

1. `COTIZAT_OPERADORES` decide quién es operador, y la lista vive en el entorno
   (no en una columna que se pueda escribir desde la aplicación).
2. `get_operator_db` rechaza a cualquier sesión que no figure en esa lista.
3. En PostgreSQL, las políticas `cotizat_licencia_*` exigen la marca
   `cotizat.es_operador`, que solo se activa desde la identidad ya validada.
   Aquí se comprueba el SQL de la migración, porque la suite corre en SQLite.
"""
from datetime import date, datetime, timedelta
from types import SimpleNamespace

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
    REFRESH_COOKIE,
    SupabaseAuthSettings,
    SupabaseIdentity,
)
from app.database import Base, get_operator_db
from app.main import app
from app.models import Licencia, Membresia, Organizacion, Usuario
from app.operadores import es_operador, operadores_configurados
from app.services.licencias import (
    GestionLicenciaError,
    cancelar_licencia,
    crear_licencia,
    licencia_vigente,
    licencias_de_organizacion,
    resumen_organizaciones,
    totales,
)
from migrations.versions import f4c1d8e37a95_add_operator_licenses as migracion

AUTH_ID = "b71f4c98-2ad3-4e15-9c07-6f38ba21d4e5"
SETTINGS = SupabaseAuthSettings(
    url="https://project.supabase.co",
    publishable_key="sb_publishable_test",
    cookie_secure=True,
)


# ---------------------------------------------------------------------------
# Quién es operador
# ---------------------------------------------------------------------------


def test_sin_variable_no_hay_ningun_operador(monkeypatch):
    """Valor seguro por omisión: un despliegue nuevo no tiene panel abierto."""
    monkeypatch.delenv("COTIZAT_OPERADORES", raising=False)
    assert operadores_configurados() == frozenset()
    assert not es_operador("cualquiera@example.com")


def test_la_lista_admite_varios_y_normaliza_mayusculas(monkeypatch):
    monkeypatch.setenv(
        "COTIZAT_OPERADORES", " Titular@Example.com , socio@example.com "
    )
    assert operadores_configurados() == {"titular@example.com", "socio@example.com"}
    assert es_operador("TITULAR@example.com")
    assert es_operador("socio@example.com")
    assert not es_operador("otro@example.com")


def test_un_email_sin_verificar_nunca_es_operador(monkeypatch):
    """La pertenencia se decide por dirección: sin confirmarla, no vale.

    De lo contrario bastaría registrar una cuenta con el correo del titular
    para heredar el panel sin controlar el buzón.
    """
    monkeypatch.setenv("COTIZAT_OPERADORES", "titular@example.com")
    assert not es_operador("titular@example.com", email_verificado=False)
    assert es_operador("titular@example.com", email_verificado=True)


def test_no_existe_ninguna_forma_de_nombrar_operadores_desde_la_aplicacion():
    """La escalada a operador no debe ser posible escribiendo en la base.

    Si algún día apareciera una columna `es_operador` en `usuarios`, un fallo de
    autorización bastaría para que alguien se nombrara administrador del
    producto. La lista debe seguir viviendo solo en el entorno.
    """
    columnas = {columna.name for columna in Usuario.__table__.columns}
    assert "es_operador" not in columnas
    assert "operador" not in columnas


# ---------------------------------------------------------------------------
# Reglas del registro (sin HTTP)
# ---------------------------------------------------------------------------


def _db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine)()


def _organizacion(db, nombre="Constructora"):
    organizacion = Organizacion(nombre=nombre, slug=nombre.lower().replace(" ", "-"))
    db.add(organizacion)
    db.commit()
    return organizacion


def test_licencia_de_pago_exige_importe_y_las_cortesias_no_lo_admiten():
    """Mezclar cortesías con ingresos falsearía la facturación del panel."""
    engine, db = _db()
    try:
        organizacion = _organizacion(db)
        with pytest.raises(GestionLicenciaError, match="necesita un importe"):
            crear_licencia(
                db, organizacion_id=organizacion.id, origen="pago",
                duracion="1a", importe=0, operador_email="t@example.com",
            )
        with pytest.raises(GestionLicenciaError, match="cortesía vale 0"):
            crear_licencia(
                db, organizacion_id=organizacion.id, origen="cortesia",
                duracion="1m", importe=50, operador_email="t@example.com",
            )
    finally:
        db.close()
        engine.dispose()


def test_regalar_un_mes_queda_registrado_como_cortesia_sin_ingreso():
    """El caso que motivó el panel: regalar tiempo sin ensuciar las cifras."""
    engine, db = _db()
    try:
        organizacion = _organizacion(db)
        licencia = crear_licencia(
            db, organizacion_id=organizacion.id, origen="cortesia",
            duracion="1m", notas="Compensación acordada por teléfono.",
            operador_email="titular@example.com", hoy=date(2026, 8, 16),
        )
        db.commit()

        assert licencia.origen == "cortesia"
        assert licencia.importe == 0
        assert licencia.es_ingreso is False
        assert licencia.vence == date(2026, 9, 14)  # 30 días, inclusive
        assert licencia.creada_por_email == "titular@example.com"
    finally:
        db.close()
        engine.dispose()


def test_compensar_una_incidencia_encadena_sin_restar_dias():
    """Renovar a quien aún tiene días no debe quitárselos ni duplicarlos."""
    engine, db = _db()
    try:
        organizacion = _organizacion(db)
        pagada = crear_licencia(
            db, organizacion_id=organizacion.id, origen="pago", duracion="1a",
            importe=89, operador_email="t@example.com", hoy=date(2026, 1, 1),
        )
        db.commit()

        extra = crear_licencia(
            db, organizacion_id=organizacion.id, origen="compensacion",
            duracion="1m", operador_email="t@example.com", hoy=date(2026, 8, 16),
        )
        db.commit()

        # Empieza justo al día siguiente del vencimiento anterior.
        assert extra.inicio == pagada.vence + timedelta(days=1)
        assert extra.vence > pagada.vence
        # La vigente hoy sigue siendo la pagada; la extra espera su turno.
        assert licencia_vigente(db, organizacion.id, hoy=date(2026, 8, 16)) is pagada
    finally:
        db.close()
        engine.dispose()


def test_una_licencia_caducada_se_muestra_vencida_aunque_nadie_la_actualice():
    """Sin procesos programados, el estado debe derivarse al leer."""
    engine, db = _db()
    try:
        organizacion = _organizacion(db)
        crear_licencia(
            db, organizacion_id=organizacion.id, origen="prueba", duracion="7d",
            operador_email="t@example.com", hoy=date(2026, 1, 1),
        )
        db.commit()

        licencias = licencias_de_organizacion(db, organizacion.id, hoy=date(2026, 8, 16))
        assert licencias[0].estado == "vencida"
        assert licencia_vigente(db, organizacion.id, hoy=date(2026, 8, 16)) is None
    finally:
        db.close()
        engine.dispose()


def test_cancelar_conserva_la_fila_y_deja_constancia():
    """El historial es la única fuente de qué se cobró: no se borra."""
    engine, db = _db()
    try:
        organizacion = _organizacion(db)
        licencia = crear_licencia(
            db, organizacion_id=organizacion.id, origen="pago", duracion="1a",
            importe=89, operador_email="t@example.com",
        )
        db.commit()

        cancelar_licencia(
            db, licencia_id=licencia.id, motivo="Reembolso solicitado",
            operador_email="titular@example.com",
            hoy=datetime(2026, 8, 16),
        )
        db.commit()

        assert db.query(Licencia).count() == 1  # sigue existiendo
        assert licencia.estado == "cancelada"
        assert "titular@example.com" in licencia.notas
        assert "Reembolso solicitado" in licencia.notas
        with pytest.raises(GestionLicenciaError, match="ya estaba cancelada"):
            cancelar_licencia(db, licencia_id=licencia.id)
    finally:
        db.close()
        engine.dispose()


def test_el_resumen_incluye_organizaciones_sin_licencia():
    """Son precisamente las que hay que mirar: registradas y sin conceder."""
    engine, db = _db()
    try:
        con = _organizacion(db, "Con licencia")
        _organizacion(db, "Sin licencia")
        crear_licencia(
            db, organizacion_id=con.id, origen="pago", duracion="1a",
            importe=89, operador_email="t@example.com",
        )
        db.commit()

        filas = resumen_organizaciones(db)
        cifras = totales(filas)
        assert cifras["organizaciones"] == 2
        assert cifras["con_licencia"] == 1
        assert cifras["sin_licencia"] == 1
        assert cifras["ingresos"] == 89
    finally:
        db.close()
        engine.dispose()


def test_no_se_puede_conceder_una_licencia_eterna():
    engine, db = _db()
    try:
        organizacion = _organizacion(db)
        with pytest.raises(GestionLicenciaError, match="no puede superar"):
            crear_licencia(
                db, organizacion_id=organizacion.id, origen="cortesia",
                dias=99_999, operador_email="t@example.com",
            )
    finally:
        db.close()
        engine.dispose()


# ---------------------------------------------------------------------------
# Aislamiento en PostgreSQL (SQL de la migración)
# ---------------------------------------------------------------------------


def test_la_migracion_protege_licencias_con_rls_de_operador(monkeypatch):
    """Las políticas deben exigir la marca de operador, no la organización."""
    sentencias = []
    monkeypatch.setattr(
        migracion.op, "get_bind",
        lambda: SimpleNamespace(dialect=SimpleNamespace(name="postgresql")),
    )
    monkeypatch.setattr(migracion.op, "execute", lambda s: sentencias.append(str(s)))
    monkeypatch.setattr(migracion.op, "create_table", lambda *a, **k: None)
    monkeypatch.setattr(migracion.op, "create_index", lambda *a, **k: None)

    migracion.upgrade()
    sql = "\n".join(sentencias)

    assert "ENABLE ROW LEVEL SECURITY" in sql
    assert "FORCE ROW LEVEL SECURITY" in sql
    for accion in ("select", "insert", "update"):
        assert f"CREATE POLICY cotizat_licencia_{accion}" in sql
    # La condición es la marca de operador, nunca la organización de la sesión.
    assert "cotizat.es_operador" in sql
    assert "cotizat.organization_id" not in sql
    # Una licencia se cancela, no se borra: sin privilegio de DELETE.
    assert "DELETE" not in sql.upper()


def test_la_marca_de_operador_no_se_activa_por_defecto():
    """`current_setting(..., true)` devuelve NULL si nadie declaró la marca."""
    assert "COALESCE" in migracion.IS_OPERATOR
    assert "FALSE" in migracion.IS_OPERATOR


# ---------------------------------------------------------------------------
# El panel por HTTP
# ---------------------------------------------------------------------------


@pytest.fixture
def entorno(monkeypatch):
    """Base con dos organizaciones y una sesión configurable."""
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
        identidad = SupabaseIdentity(
            auth_user_id=AUTH_ID,
            email=estado["email"],
            email_verified=estado["verificado"],
            name="Persona",
        )
        request.state.supabase_identity = identidad
        # Se reproduce la comprobación real de `get_operator_db`.
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


def _cliente():
    client = TestClient(app, base_url="https://cotizat.test")
    client.cookies.set(ACCESS_COOKIE, "access-token")
    client.cookies.set(REFRESH_COOKIE, "refresh-token")
    return client


def test_un_cliente_normal_no_alcanza_el_panel(entorno, monkeypatch):
    """La prueba que más importa de todo el módulo."""
    Session, datos, estado = entorno
    monkeypatch.setenv("COTIZAT_OPERADORES", "titular@example.com")
    estado["email"] = "cliente@example.com"  # usuario legítimo, pero no operador

    with _cliente() as client:
        respuesta = client.get("/admin/licencias", follow_redirects=False)

    assert respuesta.status_code in (302, 303, 403)
    assert "Panel de operador" not in respuesta.text


def test_el_operador_ve_el_panel_con_las_organizaciones(entorno, monkeypatch):
    Session, datos, estado = entorno
    monkeypatch.setenv("COTIZAT_OPERADORES", "titular@example.com")

    with _cliente() as client:
        respuesta = client.get("/admin/licencias")

    assert respuesta.status_code == 200
    assert "Panel de operador" in respuesta.text
    assert "Constructora Cliente" in respuesta.text
    assert respuesta.headers["cache-control"] == "no-store"


def test_el_operador_concede_una_prueba_desde_el_panel(entorno, monkeypatch):
    Session, datos, estado = entorno
    monkeypatch.setenv("COTIZAT_OPERADORES", "titular@example.com")

    with _cliente() as client:
        respuesta = client.post(
            "/admin/licencias",
            data={
                "organizacion_id": str(datos["organizacion_id"]),
                "origen": "prueba",
                "duracion": "7d",
                "importe": "0",
                "moneda": "USD",
                "notas": "Prueba inicial",
            },
            follow_redirects=False,
        )

    assert respuesta.status_code == 303
    with Session() as db:
        licencia = db.query(Licencia).one()
        assert licencia.origen == "prueba"
        assert licencia.importe == 0
        assert licencia.creada_por_email == "titular@example.com"


def test_un_error_de_negocio_vuelve_al_panel_con_el_mensaje(entorno, monkeypatch):
    """Una licencia de pago sin importe no puede pasar."""
    Session, datos, estado = entorno
    monkeypatch.setenv("COTIZAT_OPERADORES", "titular@example.com")

    with _cliente() as client:
        respuesta = client.post(
            "/admin/licencias",
            data={
                "organizacion_id": str(datos["organizacion_id"]),
                "origen": "pago",
                "duracion": "1a",
                "importe": "0",
            },
            follow_redirects=False,
        )

    assert respuesta.status_code == 303
    assert "error=" in respuesta.headers["location"]
    with Session() as db:
        assert db.query(Licencia).count() == 0


def test_el_panel_no_expone_datos_de_negocio_del_cliente(entorno, monkeypatch):
    """El panel informa de licencias, no da acceso a los datos del cliente."""
    Session, datos, estado = entorno
    monkeypatch.setenv("COTIZAT_OPERADORES", "titular@example.com")

    with Session() as db:
        from app.models import Cliente

        db.add(
            Cliente(
                organizacion_id=datos["organizacion_id"],
                nombre="Cliente Confidencial S.A.",
            )
        )
        db.commit()

    with _cliente() as client:
        respuesta = client.get("/admin/licencias")

    assert "Cliente Confidencial" not in respuesta.text
