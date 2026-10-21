"""Fase 0.2 — registro durable de errores internos.

Lo que importa: (1) la huella se persiste una sola vez y las recurrencias
solo suman; (2) el correo al titular sale solo ante huella nueva o
resucitada de «resuelta», con tope anti-tormenta; (3) la traza guardada no
filtra credenciales y la ruta/mensaje ya vienen saneados; (4) el flag
``COTIZAT_ERRORES_BD`` apaga la persistencia sin tocar el buffer en
memoria; (5) el middleware persiste sin cambiar la semántica del 500; y
(6) el «marcar resuelto» del panel es solo del operador y un fallo que
reaparece se desmarca solo.

La vía PostgreSQL (función SECURITY DEFINER + RLS) se cubre en
``tests/test_postgresql_rls.py``.
"""
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

import app.services.errores_internos as errores_module
from app.database import Base, get_operator_db
from app.main import app
from app.models import ErrorInterno
from app.services.errores_internos import (
    contar_errores,
    huella_de,
    listar_errores_recientes,
    persistir_y_avisar,
    podar_resueltos,
    resumen_activas,
    traza_de,
)
from app.services.operacion import RegistroErroresMiddleware, datos_error

AHORA = datetime(2026, 10, 20, 12, 0)


def _datos(**cambios):
    datos = {
        "metodo": "GET",
        "ruta": "/presupuestos",
        "tipo": "ValueError",
        "mensaje": "boom controlado",
        "traza": "Traceback...\nValueError: boom controlado",
        "ahora": AHORA,
    }
    datos.update(cambios)
    return datos


@pytest.fixture
def entorno(monkeypatch):
    """BD SQLite con el esquema completo y el correo capturado."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Sesiones = sessionmaker(bind=engine)
    monkeypatch.setattr(errores_module, "SessionLocal", Sesiones)

    enviados: list[dict] = []
    monkeypatch.setattr(
        "app.services.email.enviar_aviso_error_interno_por_email",
        lambda **kw: enviados.append(kw) or "id-de-prueba",
    )
    with errores_module._avisos_lock:
        errores_module._avisos_enviados.clear()
    yield Sesiones, enviados
    engine.dispose()


# ---------------------------------------------------------------------------
# Huella y traza
# ---------------------------------------------------------------------------


def test_huella_es_estable_y_distigue_el_fallo():
    a = huella_de("GET", "/presupuestos", "ValueError", "boom")
    assert a == huella_de("GET", "/presupuestos", "ValueError", "boom")
    assert a != huella_de("POST", "/presupuestos", "ValueError", "boom")
    assert a != huella_de("GET", "/presupuestos", "TypeError", "boom")
    assert len(a) == 64


def test_traza_no_filtra_credenciales_de_urls():
    try:
        raise RuntimeError("postgres://usuario:secreta@host/bd inaccesible")
    except RuntimeError as exc:
        traza = traza_de(exc)
    assert "secreta" not in traza
    assert "RuntimeError" in traza
    assert len(traza) <= errores_module.TRAZA_MAXIMO


# ---------------------------------------------------------------------------
# Persistencia: huella nueva avisa, la repetida solo suma
# ---------------------------------------------------------------------------


def test_primera_ocurrencia_persiste_y_avisa(entorno):
    Sesiones, enviados = entorno
    persistir_y_avisar(_datos())
    with Sesiones() as db:
        fila = db.query(ErrorInterno).one()
        assert fila.ocurrencias == 1
        assert fila.ruta == "/presupuestos"
        assert fila.traza.startswith("Traceback")
        assert fila.resuelto_en is None
    assert len(enviados) == 1
    assert enviados[0]["tipo"] == "ValueError"
    assert enviados[0]["ruta"] == "/presupuestos"
    assert enviados[0]["usuario_email"] == ""


def test_usuario_afectado_se_guarda_se_muestra_y_actualiza_en_recurrencias(entorno):
    Sesiones, enviados = entorno
    persistir_y_avisar(
        _datos(usuario_email="ana@example.com", usuario_nombre="Ana García")
    )
    assert enviados[0]["usuario_email"] == "ana@example.com"
    assert enviados[0]["usuario_nombre"] == "Ana García"

    persistir_y_avisar(
        _datos(
            usuario_email="luis@example.com",
            usuario_nombre="Luis",
            ahora=AHORA + timedelta(minutes=1),
        )
    )
    with Sesiones() as db:
        fila = db.query(ErrorInterno).one()
        assert fila.ocurrencias == 2
        assert fila.usuario_email == "luis@example.com"
        assert fila.usuario_nombre == "Luis"
        assert listar_errores_recientes(db)[0]["usuario_email"] == "luis@example.com"
    assert len(enviados) == 1  # no se reenvía por recurrencia


def test_recurrencia_suma_sin_volver_a_avisar(entorno):
    Sesiones, enviados = entorno
    persistir_y_avisar(_datos())
    persistir_y_avisar(_datos(ahora=AHORA + timedelta(minutes=5)))
    with Sesiones() as db:
        fila = db.query(ErrorInterno).one()
        assert fila.ocurrencias == 2
        assert fila.primera_vez == AHORA
        assert fila.ultima_vez == AHORA + timedelta(minutes=5)
    assert len(enviados) == 1


def test_huellas_distintas_son_filas_distintas(entorno):
    Sesiones, enviados = entorno
    persistir_y_avisar(_datos())
    persistir_y_avisar(_datos(ruta="/inicio", tipo="KeyError"))
    with Sesiones() as db:
        assert contar_errores(db) == 2
    assert len(enviados) == 2


def test_resuelto_que_reaparece_se_desmarca_y_vuelve_a_avisar(entorno):
    Sesiones, enviados = entorno
    persistir_y_avisar(_datos())
    with Sesiones() as db:
        fila = db.query(ErrorInterno).one()
        errores_module.marcar_resuelto(db, fila.id)
        db.commit()
        assert fila.resuelto_en is not None

    persistir_y_avisar(_datos(ahora=AHORA + timedelta(days=1)))
    with Sesiones() as db:
        fila = db.query(ErrorInterno).one()
        assert fila.resuelto_en is None
        assert fila.ocurrencias == 2
    assert len(enviados) == 2  # el aviso inicial y la resurrección


def test_flag_apagado_no_persiste_ni_avisa(entorno, monkeypatch):
    Sesiones, enviados = entorno
    monkeypatch.setenv("COTIZAT_ERRORES_BD", "false")
    persistir_y_avisar(_datos())
    with Sesiones() as db:
        assert contar_errores(db) == 0
    assert enviados == []


def test_tope_anti_tormenta_frena_los_avisos(entorno, monkeypatch):
    Sesiones, enviados = entorno
    monkeypatch.setattr(errores_module, "AVISOS_MAXIMOS_POR_HORA", 2)
    for i in range(4):
        persistir_y_avisar(_datos(ruta=f"/ruta/{i}"))
    with Sesiones() as db:
        assert contar_errores(db) == 4  # se persiste todo…
    assert len(enviados) == 2           # …pero el buzón descansa


def test_persistir_nunca_lanza_aunque_la_bd_falle(monkeypatch):
    def _sesion_rota():
        raise RuntimeError("sin conexión")

    monkeypatch.setattr(errores_module, "SessionLocal", _sesion_rota)
    persistir_y_avisar(_datos())  # no debe propagar


# ---------------------------------------------------------------------------
# Middleware extremo a extremo (y sin coste en el camino feliz)
# ---------------------------------------------------------------------------


def _app_que_estalla():
    async def boom(request):
        from types import SimpleNamespace

        request.state.supabase_identity = SimpleNamespace(
            email="cuenta@example.com", name="Cuenta de prueba"
        )
        raise ValueError("explosion-middleware")

    async def sana(_request):
        return PlainTextResponse("ok")

    return Starlette(routes=[Route("/boom", boom), Route("/sana", sana)])


def test_middleware_persiste_el_500_y_no_toca_las_sanas(entorno):
    Sesiones, enviados = entorno
    cliente = TestClient(
        RegistroErroresMiddleware(_app_que_estalla()),
        raise_server_exceptions=False,
    )
    assert cliente.get("/boom").status_code == 500
    assert cliente.get("/sana").status_code == 200
    with Sesiones() as db:
        fila = db.query(ErrorInterno).one()
        assert fila.ruta == "/boom"
        assert fila.usuario_email == "cuenta@example.com"
        assert fila.usuario_nombre == "Cuenta de prueba"
        assert "explosion-middleware" in fila.traza
    assert len(enviados) == 1
    assert enviados[0]["usuario_email"] == "cuenta@example.com"


def test_datos_error_incluye_traza_saneada():
    try:
        raise ValueError("con-token")
    except ValueError as exc:
        datos = datos_error(
            {"type": "http", "method": "get", "path": "/x?clave=secreto"}, exc
        )
    assert datos["metodo"] == "GET"
    assert datos["ruta"] == "/x"
    assert "ValueError: con-token" in datos["traza"]


def test_datos_error_toma_solo_la_identidad_validada_del_scope():
    from types import SimpleNamespace

    try:
        raise RuntimeError("boom")
    except RuntimeError as exc:
        datos = datos_error(
            {
                "method": "POST",
                "path": "/presupuestos/80/editar",
                "state": {
                    "supabase_identity": SimpleNamespace(
                        email="cliente@example.com", name="Cliente"
                    ),
                    "usuario": SimpleNamespace(
                        email="cliente@example.com", nombre="Cliente"
                    ),
                },
            },
            exc,
        )
    assert datos["usuario_email"] == "cliente@example.com"
    assert datos["usuario_nombre"] == "Cliente"


# ---------------------------------------------------------------------------
# Lecturas del panel y del parte diario
# ---------------------------------------------------------------------------


def test_listado_resumen_y_poda(entorno):
    Sesiones, _ = entorno
    persistir_y_avisar(_datos())
    persistir_y_avisar(
        _datos(ruta="/antigua", ahora=AHORA - timedelta(days=120))
    )
    with Sesiones() as db:
        filas = listar_errores_recientes(db)
        assert [f["ruta"] for f in filas] == ["/presupuestos", "/antigua"]
        assert filas[0]["primera_vez"] == "20/10/2026 12:00 UTC"
        assert contar_errores(db) == 2

        antigua = db.query(ErrorInterno).filter_by(ruta="/antigua").one()
        errores_module.marcar_resuelto(db, antigua.id)
        db.commit()

        activas = resumen_activas(db, horas=24 * 365)
        assert [f["ruta"] for f in activas] == ["/presupuestos"]

        assert podar_resueltos(db, dias=90) == 1
        db.commit()
        assert contar_errores(db) == 1


def test_resumen_diario_del_cron(entorno, monkeypatch):
    Sesiones, _ = entorno
    from app.services.mantenimiento import ejecutar_resumen_errores_internos

    partes: list[dict] = []
    monkeypatch.setattr(
        "app.services.email.enviar_resumen_errores_por_email",
        lambda **kw: partes.append(kw) or "id-parte",
    )
    with Sesiones() as db:
        # Sin errores: trabajo en verde y sin correo.
        assert ejecutar_resumen_errores_internos(db)["resumen_enviado"] is False
    persistir_y_avisar(_datos(ahora=datetime.utcnow()))
    with Sesiones() as db:
        resultado = ejecutar_resumen_errores_internos(db)
    assert resultado == {
        "ok": True,
        "activas_24h": 1,
        "podadas": 0,
        "resumen_enviado": True,
    }
    assert partes and partes[0]["filas"][0]["ruta"] == "/presupuestos"


# ---------------------------------------------------------------------------
# Diagnóstico: fuente BD con caída honesta a memoria
# ---------------------------------------------------------------------------


def test_diagnostico_lee_de_bd_con_sesion(entorno):
    from app.services.operacion import diagnostico_operacion

    Sesiones, _ = entorno
    persistir_y_avisar(_datos())
    with Sesiones() as db:
        diag = diagnostico_operacion(db)
    assert diag["errores_fuente"] == "bd"
    assert diag["hechos"]["errores_registrados"] == 1
    assert diag["errores"][0]["traza"].startswith("Traceback")
    assert "durable" in diag["nota_errores"]

    sin_sesion = diagnostico_operacion()
    assert sin_sesion["errores_fuente"] == "memoria"


# ---------------------------------------------------------------------------
# La acción del panel: solo operador
# ---------------------------------------------------------------------------


@pytest.fixture
def entorno_panel(entorno, monkeypatch):
    """La app real con ``get_operator_db`` sustituido (patrón de test_operacion)."""
    Sesiones, _ = entorno
    monkeypatch.setenv("COTIZAT_OPERADORES", "titular@example.com")
    persistir_y_avisar(_datos())
    with Sesiones() as db:
        error_id = db.query(ErrorInterno).one().id

    from app.auth import OrganizationAccessDenied, SupabaseIdentity
    from app.operadores import es_operador

    estado = {"email": "titular@example.com"}

    def _db_operador(request: Request):
        db = Sesiones()
        identidad = SupabaseIdentity(
            auth_user_id="c3a24f92-7e41-4c9e-a1f2-6d8b3e5c7a10",
            email=estado["email"],
            email_verified=True,
            name="Persona",
        )
        request.state.supabase_identity = identidad
        db.info["auth_email"] = identidad.email
        if not es_operador(identidad.email, email_verificado=True):
            db.close()
            raise OrganizationAccessDenied("No tienes acceso a esta sección.")
        db.info["es_operador"] = True
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_operator_db] = _db_operador
    try:
        yield Sesiones, estado, error_id
    finally:
        app.dependency_overrides.pop(get_operator_db, None)


def test_marcar_resuelto_por_http(entorno_panel):
    Sesiones, _estado, error_id = entorno_panel
    cliente = TestClient(app, raise_server_exceptions=False)
    respuesta = cliente.post(
        f"/admin/sistema/errores/{error_id}/resuelto",
        data={"volver": "/admin/sistema?tab=estado"},
        follow_redirects=False,
    )
    assert respuesta.status_code == 303
    assert "/admin/sistema?tab=estado" in respuesta.headers["location"]
    with Sesiones() as db:
        assert db.get(ErrorInterno, error_id).resuelto_en is not None


def test_marcar_resuelto_exige_operador(entorno_panel):
    Sesiones, estado, error_id = entorno_panel
    estado["email"] = "cliente@example.com"
    cliente = TestClient(app, raise_server_exceptions=False)
    cliente.post(
        f"/admin/sistema/errores/{error_id}/resuelto",
        data={"volver": "/admin/sistema?tab=estado"},
        follow_redirects=False,
    )
    with Sesiones() as db:
        assert db.get(ErrorInterno, error_id).resuelto_en is None
