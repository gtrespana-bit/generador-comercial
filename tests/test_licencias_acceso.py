"""Corte automático de acceso, recibo PDF y avisos de vencimiento (E1-060).

Segunda parte del registro de licencias: lo que ya no es solo anotar, sino
hacer cumplir. Las pruebas que más importan aquí son las de **contorno**:

- el interruptor (``COTIZAT_EXIGIR_LICENCIA``) está apagado por omisión, así
  ningún despliegue se queda fuera por accidente al actualizar;
- en PostgreSQL la consulta de acceso pasa por una función SECURITY DEFINER
  guardada, porque la sesión del cliente no puede leer ``licencias``;
- el escritorio (SQLite) jamás exige licencia.
"""
from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.requests import Request
from starlette.testclient import TestClient

import app.database as database_module
from app import auth as auth_module
from app import main as main_module
from app.routers import common
from app.auth import (
    ACCESS_COOKIE,
    REFRESH_COOKIE,
    SupabaseAuthSettings,
    SupabaseIdentity,
)
from app.database import Base, get_db, get_operator_db
from app.main import app
from app.models import (
    Licencia,
    LicenciaSuspendidaError,
    Membresia,
    Organizacion,
    Usuario,
)
from app.operadores import es_operador
from app.services.licencias import (
    GestionLicenciaError,
    aviso_enviado_hoy,
    correos_administradores,
    crear_licencia,
    enviar_avisos_vencimiento,
    exigencia_licencia_activada,
    organizacion_tiene_acceso,
)
from app.services.recibo_licencia import (
    generar_recibo_licencia_pdf,
    numero_recibo,
)
from migrations.versions import (
    b7c4a9e2d31f_license_cutoff_and_operator_visibility as migracion,
)

AUTH_ID = "b71f4c98-2ad3-4e15-9c07-6f38ba21d4e5"
SETTINGS = SupabaseAuthSettings(
    url="https://project.supabase.co",
    publishable_key="sb_publishable_test",
    cookie_secure=True,
)
HOY = date(2026, 8, 17)


# ---------------------------------------------------------------------------
# El interruptor de exigencia
# ---------------------------------------------------------------------------


def test_por_defecto_la_exigencia_esta_desactivada(monkeypatch):
    """Valor seguro: actualizar el código nunca cierra un despliegue solo."""
    monkeypatch.delenv("COTIZAT_EXIGIR_LICENCIA", raising=False)
    assert exigencia_licencia_activada() is False


def test_la_exigencia_solo_se_activa_con_valores_claros(monkeypatch):
    for valor in ("true", "1", "on", "si", "sí", " TRUE "):
        monkeypatch.setenv("COTIZAT_EXIGIR_LICENCIA", valor)
        assert exigencia_licencia_activada() is True, valor
    for valor in ("", "false", "0", "off", "2", "quizá"):
        monkeypatch.setenv("COTIZAT_EXIGIR_LICENCIA", valor)
        assert exigencia_licencia_activada() is False, valor


# ---------------------------------------------------------------------------
# ¿Tiene acceso la organización? (consulta directa, sin PostgreSQL)
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


def test_sin_licencia_no_hay_acceso():
    engine, db = _db()
    try:
        organizacion = _organizacion(db)
        assert organizacion_tiene_acceso(db, organizacion.id, hoy=HOY) is False
    finally:
        db.close()
        engine.dispose()


def test_con_licencia_vigente_hay_acceso():
    engine, db = _db()
    try:
        organizacion = _organizacion(db)
        crear_licencia(
            db, organizacion_id=organizacion.id, origen="pago", duracion="1a",
            importe=89, operador_email="t@example.com", hoy=HOY,
        )
        db.commit()
        assert organizacion_tiene_acceso(db, organizacion.id, hoy=HOY) is True
        # El último día cuenta como día de acceso.
        vigente = db.query(Licencia).one()
        assert organizacion_tiene_acceso(
            db, organizacion.id, hoy=vigente.vence
        ) is True
        assert organizacion_tiene_acceso(
            db, organizacion.id, hoy=vigente.vence + timedelta(days=1)
        ) is False
    finally:
        db.close()
        engine.dispose()


def test_licencia_cancelada_o_futura_no_da_acceso():
    engine, db = _db()
    try:
        organizacion = _organizacion(db)
        licencia = crear_licencia(
            db, organizacion_id=organizacion.id, origen="cortesia",
            duracion="1m", operador_email="t@example.com", hoy=HOY,
        )
        db.commit()
        assert organizacion_tiene_acceso(db, organizacion.id, hoy=HOY) is True

        licencia.estado = "cancelada"
        db.commit()
        assert organizacion_tiene_acceso(db, organizacion.id, hoy=HOY) is False
    finally:
        db.close()
        engine.dispose()


# ---------------------------------------------------------------------------
# El corte dentro de get_db (camino real del backend web)
# ---------------------------------------------------------------------------


def _peticion_con_organizacion(organizacion_id: int) -> Request:
    return Request({
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [
            (b"cookie", f"cotizat_organization_id={organizacion_id}".encode())
        ],
        "query_string": b"",
        "scheme": "https",
        "server": ("testserver", 443),
        "client": ("testclient", 123),
    })


@pytest.fixture
def entorno_web(monkeypatch):
    """Simula el despliegue web (PostgreSQL) sobre una base SQLite real."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    with Session() as seed:
        organizacion = Organizacion(nombre="Cliente Piloto", slug="piloto")
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

    # El motor de pruebas es SQLite, así que el acceso por licencia usa la
    # consulta directa; en producción iría por la función SECURITY DEFINER.
    monkeypatch.setattr(database_module, "DATABASE_IS_SQLITE", False)
    monkeypatch.setattr(database_module, "SessionLocal", Session)
    monkeypatch.setattr(
        auth_module,
        "identity_for_request",
        lambda _request: SupabaseIdentity(
            AUTH_ID, "cliente@example.com", "Cliente", True
        ),
    )
    try:
        yield Session, datos
    finally:
        engine.dispose()


def test_get_db_no_corta_nada_con_el_interruptor_apagado(entorno_web, monkeypatch):
    """Sin la variable, una organización sin licencia trabaja con normalidad."""
    monkeypatch.delenv("COTIZAT_EXIGIR_LICENCIA", raising=False)
    Session, datos = entorno_web

    dependency = database_module.get_db(
        _peticion_con_organizacion(datos["organizacion_id"])
    )
    db = next(dependency)
    try:
        assert db.info["organizacion_id"] == datos["organizacion_id"]
    finally:
        dependency.close()


def test_get_db_suspende_la_organizacion_sin_licencia(entorno_web, monkeypatch):
    """Con la exigencia activa, sin licencia vigente no se pasa de la puerta."""
    monkeypatch.setenv("COTIZAT_EXIGIR_LICENCIA", "true")
    _Session, datos = entorno_web

    dependency = database_module.get_db(
        _peticion_con_organizacion(datos["organizacion_id"])
    )
    with pytest.raises(LicenciaSuspendidaError, match="Cliente Piloto"):
        next(dependency)
    dependency.close()


def test_get_db_deja_trabajar_con_licencia_vigente(entorno_web, monkeypatch):
    monkeypatch.setenv("COTIZAT_EXIGIR_LICENCIA", "true")
    Session, datos = entorno_web
    with Session() as db:
        crear_licencia(
            db, organizacion_id=datos["organizacion_id"], origen="pago",
            duracion="1a", importe=89, operador_email="t@example.com",
        )
        db.commit()

    dependency = database_module.get_db(
        _peticion_con_organizacion(datos["organizacion_id"])
    )
    db = next(dependency)
    try:
        assert db.info["organizacion_id"] == datos["organizacion_id"]
    finally:
        dependency.close()


def test_el_escritorio_sqlite_jamas_exige_licencia(monkeypatch):
    """Aunque la variable quedara activa por error, el modo local la ignora."""
    monkeypatch.setenv("COTIZAT_EXIGIR_LICENCIA", "true")
    assert database_module.DATABASE_IS_SQLITE is True  # base de la suite

    dependency = database_module.get_db(None)
    db = next(dependency)
    try:
        assert db.info["organizacion_id"] >= 1
    finally:
        dependency.close()


# ---------------------------------------------------------------------------
# La pantalla de "acceso suspendido"
# ---------------------------------------------------------------------------


def _cliente_api():
    client = TestClient(app, base_url="https://cotizat.test")
    client.cookies.set(ACCESS_COOKIE, "access-token")
    client.cookies.set(REFRESH_COOKIE, "refresh-token")
    return client


@pytest.fixture
def dependencia_suspendida():
    def _suspendida(_request: Request):
        raise LicenciaSuspendidaError(
            "El acceso de «Cliente Piloto» está suspendido: su licencia venció "
            "o aún no fue activada."
        )
        yield  # pragma: no cover - nunca se alcanza

    app.dependency_overrides[get_db] = _suspendida
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_la_suspension_explica_que_los_datos_siguen_guardados(dependencia_suspendida):
    with _cliente_api() as client:
        respuesta = client.get("/inicio")

    assert respuesta.status_code == 403
    assert "Acceso suspendido" in respuesta.text
    assert "Cliente Piloto" in respuesta.text
    assert "no se han borrado" in respuesta.text
    assert "soporte@cotizat.online" in respuesta.text
    assert respuesta.headers["cache-control"] == "no-store"


def test_la_suspension_responde_json_a_quien_pide_json(dependencia_suspendida):
    with _cliente_api() as client:
        respuesta = client.get("/inicio", headers={"accept": "application/json"})

    assert respuesta.status_code == 403
    cuerpo = respuesta.json()
    assert cuerpo["ok"] is False
    assert "suspendido" in cuerpo["error"]


# ---------------------------------------------------------------------------
# Recibo PDF de una licencia de pago
# ---------------------------------------------------------------------------


def _licencia_pago(db, organizacion, **kwargs):
    licencia = crear_licencia(
        db, organizacion_id=organizacion.id, origen="pago", duracion="1a",
        importe=89, metodo_cobro="Transferencia", referencia="OP-0001",
        operador_email="titular@example.com", hoy=HOY, **kwargs,
    )
    db.commit()
    return licencia


def test_el_recibo_es_un_pdf_valido_con_numero_estable():
    engine, db = _db()
    try:
        licencia = _licencia_pago(db, _organizacion(db))
        pdf = generar_recibo_licencia_pdf(licencia, licencia.organizacion)

        contenido = pdf.read()
        assert contenido.startswith(b"%PDF")
        assert len(contenido) > 1500  # no es un PDF vacío
        assert numero_recibo(licencia) == f"CT-{licencia.id:06d}"
        # Reproducible: misma licencia → mismo número.
        assert numero_recibo(licencia) == numero_recibo(licencia)
    finally:
        db.close()
        engine.dispose()


def test_las_cortesias_y_pruebas_no_tienen_recibo():
    """Un período regalado no debe poder documentarse como cobro."""
    engine, db = _db()
    try:
        organizacion = _organizacion(db)
        cortesia = crear_licencia(
            db, organizacion_id=organizacion.id, origen="cortesia",
            duracion="1m", operador_email="t@example.com", hoy=HOY,
        )
        db.commit()
        with pytest.raises(GestionLicenciaError, match="no se cobró"):
            generar_recibo_licencia_pdf(cortesia, organizacion)

        cortesia.origen = "pago"
        cortesia.importe = 0
        with pytest.raises(GestionLicenciaError, match="sin importe"):
            generar_recibo_licencia_pdf(cortesia, organizacion)
    finally:
        db.close()
        engine.dispose()


# ---------------------------------------------------------------------------
# Avisos de vencimiento
# ---------------------------------------------------------------------------


def test_solo_reciben_aviso_propietario_y_administrador_activos():
    engine, db = _db()
    try:
        organizacion = _organizacion(db)
        usuarios = {}
        for clave, rol, activo in (
            ("dueno@example.com", "propietario", True),
            ("admin@example.com", "administrador", True),
            ("miembro@example.com", "miembro", True),
            ("lectura@example.com", "lectura", True),
            ("baja@example.com", "administrador", False),
        ):
            usuario = Usuario(email=clave, nombre=clave, activo=activo)
            db.add(usuario)
            db.flush()
            db.add(
                Membresia(
                    organizacion_id=organizacion.id,
                    usuario_id=usuario.id,
                    rol=rol,
                )
            )
            usuarios[clave] = usuario
        db.commit()

        assert correos_administradores(db, organizacion.id) == [
            "dueno@example.com",
            "admin@example.com",
        ]
    finally:
        db.close()
        engine.dispose()


def test_el_aviso_llega_a_los_administradores_y_queda_anotado():
    engine, db = _db()
    try:
        organizacion = _organizacion(db)
        usuario = Usuario(email="dueno@example.com", nombre="Dueño")
        db.add(usuario)
        db.flush()
        db.add(
            Membresia(
                organizacion_id=organizacion.id,
                usuario_id=usuario.id,
                rol="propietario",
            )
        )
        licencia = crear_licencia(
            db, organizacion_id=organizacion.id, origen="pago", duracion="1m",
            importe=9.99, operador_email="t@example.com",
            hoy=HOY - timedelta(days=25),
        )
        db.commit()
        # Le quedan 4 días: entra en la ventana de aviso de 15.

        envios = []
        resultado = enviar_avisos_vencimiento(
            db,
            remitente=lambda **kwargs: envios.append(kwargs),
            hoy=HOY,
        )
        db.commit()

        assert [(correo) for _, correos in resultado["avisadas"] for correo in correos] == [
            "dueno@example.com"
        ]
        assert len(envios) == 1
        assert envios[0]["organizacion_nombre"] == "Constructora"
        assert envios[0]["dias_restantes"] == 4
        assert envios[0]["vence"] == licencia.vence
        assert aviso_enviado_hoy(licencia, HOY)
        assert "Aviso de vencimiento enviado" in licencia.notas

        # El mismo día no se repite aunque el operador vuelva a pulsar.
        resultado = enviar_avisos_vencimiento(
            db, remitente=lambda **kwargs: envios.append(kwargs), hoy=HOY
        )
        assert resultado["omitidas"] == ["Constructora"]
        assert len(envios) == 1

        # Al día siguiente sí volvería a avisar.
        resultado = enviar_avisos_vencimiento(
            db,
            remitente=lambda **kwargs: envios.append(kwargs),
            hoy=HOY + timedelta(days=1),
        )
        assert len(envios) == 2
    finally:
        db.close()
        engine.dispose()


def test_no_se_avisa_a_quien_tiene_tiempo_o_ya_vencio():
    engine, db = _db()
    try:
        con_tiempo = _organizacion(db, "Con Tiempo")
        crear_licencia(
            db, organizacion_id=con_tiempo.id, origen="pago", duracion="1a",
            importe=89, operador_email="t@example.com", hoy=HOY,
        )
        vencida = _organizacion(db, "Ya Vencida")
        crear_licencia(
            db, organizacion_id=vencida.id, origen="prueba", duracion="7d",
            operador_email="t@example.com", hoy=HOY - timedelta(days=30),
        )
        db.commit()

        envios = []
        resultado = enviar_avisos_vencimiento(
            db, remitente=lambda **kwargs: envios.append(kwargs), hoy=HOY
        )

        assert envios == []
        assert resultado["avisadas"] == []
        # La vencida no entra como "por vencer": lo que toca ya no es avisar
        # para renovar a tiempo, sino la conversación de reactivación.
    finally:
        db.close()
        engine.dispose()


def test_un_fallo_del_proveedor_se_reporta_y_no_se_anota_como_enviado():
    engine, db = _db()
    try:
        organizacion = _organizacion(db)
        usuario = Usuario(email="dueno@example.com", nombre="Dueño")
        db.add(usuario)
        db.flush()
        db.add(
            Membresia(
                organizacion_id=organizacion.id,
                usuario_id=usuario.id,
                rol="propietario",
            )
        )
        licencia = crear_licencia(
            db, organizacion_id=organizacion.id, origen="prueba", duracion="7d",
            operador_email="t@example.com", hoy=HOY - timedelta(days=3),
        )
        db.commit()

        def remitente_roto(**_kwargs):
            raise RuntimeError("proveedor caído")

        resultado = enviar_avisos_vencimiento(
            db, remitente=remitente_roto, hoy=HOY
        )
        db.commit()

        assert resultado["fallidas"] == [("Constructora", "proveedor caído")]
        assert resultado["avisadas"] == []
        assert not aviso_enviado_hoy(licencia, HOY)  # puede reintentarse hoy
    finally:
        db.close()
        engine.dispose()


def test_sin_resend_configurado_el_error_se_propaga_al_panel():
    """Falta de configuración no es un fallo por cliente: es una sola causa."""
    from app.services.email import EmailNotConfigured

    engine, db = _db()
    try:
        organizacion = _organizacion(db)
        usuario = Usuario(email="dueno@example.com", nombre="Dueño")
        db.add(usuario)
        db.flush()
        db.add(
            Membresia(
                organizacion_id=organizacion.id,
                usuario_id=usuario.id,
                rol="propietario",
            )
        )
        crear_licencia(
            db, organizacion_id=organizacion.id, origen="prueba", duracion="7d",
            operador_email="t@example.com", hoy=HOY - timedelta(days=3),
        )
        db.commit()

        def sin_configurar(**_kwargs):
            raise EmailNotConfigured("Falta RESEND_API_KEY.")

        with pytest.raises(EmailNotConfigured):
            enviar_avisos_vencimiento(db, remitente=sin_configurar, hoy=HOY)
    finally:
        db.close()
        engine.dispose()


# ---------------------------------------------------------------------------
# El panel por HTTP: recibo y avisos bajo la misma puerta de operador
# ---------------------------------------------------------------------------


@pytest.fixture
def entorno_panel(monkeypatch):
    """Mismo patrón que el de `test_licencias.py`: sesión configurable."""
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
        if not es_operador(
            estado["email"], email_verificado=estado["verificado"]
        ):
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


def test_el_operador_descarga_el_recibo_de_una_licencia_de_pago(
    entorno_panel, monkeypatch
):
    Session, datos, _estado = entorno_panel
    monkeypatch.setenv("COTIZAT_OPERADORES", "titular@example.com")
    with Session() as db:
        licencia = _licencia_pago(db, db.get(Organizacion, datos["organizacion_id"]))
        licencia_id = licencia.id

    with _cliente_api() as client:
        respuesta = client.get(f"/admin/licencias/{licencia_id}/recibo.pdf")

    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"] == "application/pdf"
    disposicion = respuesta.headers["content-disposition"]
    assert f"recibo-CT-{licencia_id:06d}-cliente.pdf" in disposicion
    assert respuesta.content.startswith(b"%PDF")


def test_el_recibo_de_una_cortesia_vuelve_al_panel_con_error(
    entorno_panel, monkeypatch
):
    Session, datos, _estado = entorno_panel
    monkeypatch.setenv("COTIZAT_OPERADORES", "titular@example.com")
    with Session() as db:
        cortesia = crear_licencia(
            db, organizacion_id=datos["organizacion_id"], origen="cortesia",
            duracion="1m", operador_email="titular@example.com",
        )
        db.commit()
        licencia_id = cortesia.id

    with _cliente_api() as client:
        respuesta = client.get(
            f"/admin/licencias/{licencia_id}/recibo.pdf", follow_redirects=False
        )

    assert respuesta.status_code == 303
    assert "error=" in respuesta.headers["location"]


def test_un_cliente_no_descarga_recibos_ni_envia_avisos(entorno_panel, monkeypatch):
    Session, datos, estado = entorno_panel
    monkeypatch.setenv("COTIZAT_OPERADORES", "titular@example.com")
    estado["email"] = "cliente@example.com"  # legítimo, pero no operador
    with Session() as db:
        licencia = _licencia_pago(
            db, db.get(Organizacion, datos["organizacion_id"])
        )
        licencia_id = licencia.id

    with _cliente_api() as client:
        recibo = client.get(
            f"/admin/licencias/{licencia_id}/recibo.pdf", follow_redirects=False
        )
        avisos = client.post("/admin/licencias/avisos", follow_redirects=False)

    assert recibo.status_code in (302, 303, 403)
    assert avisos.status_code in (302, 303, 403)
    assert not recibo.content.startswith(b"%PDF")


def test_el_panel_envia_los_avisos_y_lo_resume(entorno_panel, monkeypatch):
    Session, datos, _estado = entorno_panel
    monkeypatch.setenv("COTIZAT_OPERADORES", "titular@example.com")
    with Session() as db:
        crear_licencia(
            db, organizacion_id=datos["organizacion_id"], origen="prueba",
            duracion="7d", operador_email="titular@example.com",
            hoy=date.today() - timedelta(days=3),
        )
        db.commit()

    envios = []
    monkeypatch.setattr(
        "app.services.email.enviar_aviso_licencia",
        lambda **kwargs: envios.append(kwargs),
    )
    with _cliente_api() as client:
        respuesta = client.post("/admin/licencias/avisos", follow_redirects=False)

    assert respuesta.status_code == 303
    assert "msg=" in respuesta.headers["location"]
    assert [envio["email"] for envio in envios] == ["cliente@example.com"]


def test_el_panel_explica_si_el_correo_no_esta_configurado(
    entorno_panel, monkeypatch
):
    Session, datos, _estado = entorno_panel
    monkeypatch.setenv("COTIZAT_OPERADORES", "titular@example.com")
    with Session() as db:
        crear_licencia(
            db, organizacion_id=datos["organizacion_id"], origen="prueba",
            duracion="7d", operador_email="titular@example.com",
            hoy=date.today() - timedelta(days=3),
        )
        db.commit()

    from app.services.email import EmailNotConfigured

    def sin_configurar(**_kwargs):
        raise EmailNotConfigured("Falta RESEND_API_KEY.")

    monkeypatch.setattr(
        "app.services.email.enviar_aviso_licencia", sin_configurar
    )
    with _cliente_api() as client:
        respuesta = client.post("/admin/licencias/avisos", follow_redirects=False)

    assert respuesta.status_code == 303
    assert "error=" in respuesta.headers["location"]
    assert "RESEND_API_KEY" in respuesta.headers["location"]


def test_el_panel_avisa_cuando_el_corte_esta_desactivado(entorno_panel, monkeypatch):
    """Sin corte automático, una licencia vencida es solo información.

    El aviso se ve dos veces a propósito: en la agenda (donde el operador abre el
    día) y en Ingresos › Contratos (donde concede o suspende). No es redundancia
    de pantallas, es que el aviso esté donde se toma la decisión.
    """
    _Session, _datos, _estado = entorno_panel
    monkeypatch.setenv("COTIZAT_OPERADORES", "titular@example.com")
    monkeypatch.delenv("COTIZAT_EXIGIR_LICENCIA", raising=False)

    with _cliente_api() as client:
        respuesta = client.get("/admin/ingresos?tab=contratos")
        agenda = client.get("/admin")

    assert respuesta.status_code == 200
    assert "corte automático de acceso está" in respuesta.text
    assert "COTIZAT_EXIGIR_LICENCIA" in respuesta.text
    assert "corte automático de acceso está" in agenda.text

    monkeypatch.setenv("COTIZAT_EXIGIR_LICENCIA", "true")
    with _cliente_api() as client:
        respuesta = client.get("/admin/ingresos?tab=contratos")
    assert "corte automático de acceso está" not in respuesta.text


# ---------------------------------------------------------------------------
# La migración: defensas de la función de acceso y de la vista del operador
# ---------------------------------------------------------------------------


def test_la_funcion_de_acceso_es_security_definer_y_esta_guardada():
    """Es la única excepción al «cliente no lee licencias»: devuelve 1 bit."""
    sql = migracion.ACCESS_FUNCTION_SQL
    assert "SECURITY DEFINER" in sql
    assert "STABLE" in sql
    # Guardia por claim: solo responde sobre la organización de la sesión.
    assert "current_setting('cotizat.organization_id', true)" in sql
    assert "FALSE" in sql  # valor seguro por omisión


def test_los_correos_de_administrador_exigen_marca_de_operador():
    sql = migracion.ADMIN_EMAILS_FUNCTION_SQL
    assert "SECURITY DEFINER" in sql
    assert "current_setting('cotizat.es_operador', true)" in sql
    assert "'propietario'" in sql and "'administrador'" in sql
    # Miembros y lectura no reciben avisos de cobro.
    assert "'miembro'" not in sql and "'lectura'" not in sql


def test_la_politica_corregida_mantiene_la_via_de_membresia():
    """El operador gana visibilidad sin quitarle nada a la sesión normal."""
    sql = migracion.ORG_SELECT_POLICY_SQL
    assert "cotizat_security.membership_role(id) IS NOT NULL" in sql
    assert "current_setting('cotizat.es_operador', true)" in sql


def test_upgrade_revoca_al_publico_y_concede_solo_a_cotizat_app():
    import inspect

    codigo = inspect.getsource(migracion.upgrade)
    assert "REVOKE ALL ON FUNCTION" in codigo
    assert "TO cotizat_app" in codigo
    assert "OWNER TO CURRENT_USER" in codigo


def test_el_script_sql_de_supabase_reproduce_la_migracion():
    """El script manual no puede divergir en silencio de la migración."""
    script = (
        main_module.BASE_DIR
        / "docs"
        / "staging_upgrade_b7c4a9e2d31f.sql"
    ).read_text(encoding="utf-8")
    for pieza in (
        "cotizat_security.organization_has_license",
        "cotizat_security.organization_admin_emails",
        "SECURITY DEFINER",
        "GRANT EXECUTE",
        "REVOKE ALL ON FUNCTION",
        "cotizat_org_select",
        "b7c4a9e2d31f",
        "f4c1d8e37a95",  # guarda de versión previa
    ):
        assert pieza in script


# ---------------------------------------------------------------------------
# La salida de emergencia del corte: renovar siempre tiene que ser posible
# ---------------------------------------------------------------------------


def test_la_renovacion_no_queda_detras_del_propio_corte(entorno_web, monkeypatch):
    """Una organización suspendida DEBE poder llegar al checkout.

    Es la trampa obvia del corte automático: si `/pago/comprar` exigiera
    licencia vigente, la única forma de recuperar el acceso sería escribir a
    soporte, porque comprar estaría prohibido justo a quien necesita comprar.
    """
    monkeypatch.setenv("COTIZAT_EXIGIR_LICENCIA", "true")
    _Session, datos = entorno_web

    # La puerta normal sí corta...
    normal = database_module.get_db(
        _peticion_con_organizacion(datos["organizacion_id"])
    )
    with pytest.raises(LicenciaSuspendidaError):
        next(normal)
    normal.close()

    # ...y la de renovación deja pasar, con la organización ya resuelta.
    renovacion = database_module.get_db_renovacion(
        _peticion_con_organizacion(datos["organizacion_id"])
    )
    db = next(renovacion)
    try:
        assert db.info["organizacion_id"] == datos["organizacion_id"]
    finally:
        renovacion.close()


def test_la_renovacion_sigue_exigiendo_sesion_y_membresia(entorno_web, monkeypatch):
    """Saltarse el corte no es saltarse el aislamiento: sin membresía, no entra."""
    monkeypatch.setenv("COTIZAT_EXIGIR_LICENCIA", "true")
    Session, datos = entorno_web
    with Session() as db:
        ajena = Organizacion(nombre="Ajena", slug="ajena")
        db.add(ajena)
        db.commit()
        ajena_id = ajena.id

    dependency = database_module.get_db_renovacion(
        _peticion_con_organizacion(ajena_id)
    )
    with pytest.raises(Exception) as excinfo:
        next(dependency)
    dependency.close()
    assert not isinstance(excinfo.value, LicenciaSuspendidaError)
    assert ajena_id != datos["organizacion_id"]


def test_las_rutas_de_compra_usan_la_puerta_sin_corte():
    """Contrato explícito: el checkout y su recibo cuelgan de get_db_renovacion.

    Si alguien vuelve a ponerlos en `get_db`, el corte automático deja al
    cliente sin forma de renovar por su cuenta y esta prueba lo delata.
    """
    from app.database import get_db, get_db_renovacion

    esperadas = {
        ("/pago/comprar", "GET"),
        ("/pago/comprar", "POST"),
        ("/pago/confirmacion", "GET"),
        ("/pago/recibo/{compra_id}.pdf", "GET"),
        ("/pago/stripe/checkout", "POST"),
        ("/pago/stripe/exito", "GET"),
    }
    def _recorrer(rutas):
        """FastAPI envuelve los routers incluidos; hay que bajar un nivel."""
        for ruta in rutas:
            incluido = getattr(ruta, "original_router", None)
            if incluido is not None:
                yield from _recorrer(incluido.routes)
                continue
            yield ruta

    vistas = set()
    for route in _recorrer(app.routes):
        path = getattr(route, "path", "")
        if not path.startswith("/pago"):
            continue
        dependant = getattr(route, "dependant", None)
        dependencias = {d.call for d in dependant.dependencies} if dependant else set()
        for metodo in (getattr(route, "methods", set()) or set()) - {"HEAD", "OPTIONS"}:
            if (path, metodo) in esperadas:
                vistas.add((path, metodo))
                assert get_db_renovacion in dependencias, (path, metodo)
                assert get_db not in dependencias, (path, metodo)

    assert vistas == esperadas, f"faltan rutas por comprobar: {esperadas - vistas}"


def test_la_pantalla_de_suspension_ofrece_renovar(dependencia_suspendida):
    """El cliente suspendido necesita un botón, no solo un correo de soporte."""
    with _cliente_api() as client:
        respuesta = client.get("/inicio")

    assert respuesta.status_code == 403
    assert 'href="/pago"' in respuesta.text
    assert "Renovar" in respuesta.text
