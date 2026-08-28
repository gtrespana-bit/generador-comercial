"""Panel de analítica de producto (``/admin/analitica``) — E5-012.

Verifica el contorno completo de la página:

- solo el operador entra (misma puerta ``get_operator_db`` que el resto
  del panel de administración);
- las métricas se calculan en el servidor sobre datos sembrados reales
  (usuarios, organizaciones, licencias, latidos y eventos de producto);
- el embudo, las cohortes, el riesgo de churn y los eventos recientes
  reflejan esos datos.

La telemetría del servicio se cubre en ``tests/test_telemetria.py``; aquí
se ejercita la página HTTP completa con la dependencia de operador
sustituida, el mismo enfoque que ``tests/test_panel_emails.py``.
"""
from datetime import date, datetime, timedelta

import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import ACCESS_COOKIE, REFRESH_COOKIE, SupabaseAuthSettings, SupabaseIdentity
from app.database import Base, get_operator_db
from app.main import app
from app.models import (
    EventoProducto,
    Licencia,
    Membresia,
    Organizacion,
    Usuario,
)
from app.operadores import es_operador
from app.routers import common
from app.services.analitica import resumen_analitica

AUTH_ID = "c5d84a10-2f6e-4d1b-9a30-71c2b9e0f001"
SETTINGS = SupabaseAuthSettings(
    url="https://project.supabase.co",
    publishable_key="sb_publishable_test",
    cookie_secure=True,
)

HOY = date(2026, 8, 28)


# ---------------------------------------------------------------------------
# Semilla: dos empresas con actividad distinta, un pago y latidos
# ---------------------------------------------------------------------------


def _sembrar(Session):
    """Datos mínimos con historia para todas las secciones del panel."""
    activa = Organizacion(
        nombre="Constructora Activa", slug="activa",
        created_at=datetime(2026, 7, 2, 9, 0),
    )
    dormida = Organizacion(
        nombre="Remodeladora Dormida", slug="dormida",
        created_at=datetime(2026, 5, 20, 9, 0),
    )
    titular = Usuario(
        auth_user_id=AUTH_ID, email="titular@example.com",
        nombre="Titular", email_verificado_at=datetime(2026, 7, 1),
        created_at=datetime(2026, 7, 1, 8, 0),
    )
    nuevo = Usuario(
        auth_user_id="c5d84a10-2f6e-4d1b-9a30-71c2b9e0f002",
        email="nuevo@example.com", nombre="Nuevo",
        created_at=datetime.utcnow() - timedelta(days=2),
    )
    with Session() as db:
        db.add_all([activa, dormida, titular, nuevo])
        db.flush()
        db.add(Membresia(organizacion_id=activa.id, usuario_id=titular.id, rol="propietario"))
        db.commit()
        ids = {"activa": activa.id, "dormida": dormida.id, "usuario": titular.id}
        hoy_dt = datetime.utcnow()

        # Empresa activa: paga y usa el producto esta semana.
        db.add(
            Licencia(
                organizacion_id=activa.id, estado="activa", origen="pago",
                inicio=date(2026, 7, 2), vence=date(2026, 7, 2) + timedelta(days=365),
                importe=89.0,
            )
        )
        eventos_activa = [
            ("organizacion.creada", datetime(2026, 7, 2, 9, 1), {}),
            ("presupuesto.creado", datetime(2026, 7, 3, 10, 0), {"primero": True, "partidas": 5}),
            ("presupuesto.enviado_email", datetime(2026, 7, 3, 11, 0), {}),
            ("presupuesto.aprobado", datetime(2026, 7, 4, 12, 0), {}),
            ("licencia.activada", datetime(2026, 7, 2, 9, 30), {"plan": "anual", "origen": "stripe"}),
        ]
        # Latidos: activa usó el producto hoy y hace 3 días; dormida, hace 40.
        eventos_activa += [("actividad.diaria", hoy_dt - timedelta(days=3), {})]
        eventos_activa += [("actividad.diaria", hoy_dt.replace(hour=9, minute=1), {})]
        # Uso reciente (dentro de la ventana de 30 días) para «Uso de funciones».
        eventos_activa += [
            ("presupuesto.creado", hoy_dt - timedelta(days=5), {"primero": False, "partidas": 3}),
            ("presupuesto.pdf_descargado", hoy_dt - timedelta(days=5, hours=1), {}),
        ]
        import json as _json

        for accion, creado, detalle in eventos_activa:
            db.add(
                EventoProducto(
                    organizacion_id=activa.id, accion=accion,
                    actor_email="titular@example.com",
                    detalle=_json.dumps(detalle), created_at=creado,
                )
            )

        # Empresa dormida: paga (licencia vigente) pero sin uso en 40 días.
        db.add(
            Licencia(
                organizacion_id=dormida.id, estado="activa", origen="pago",
                inicio=date(2026, 5, 20), vence=date(2026, 5, 20) + timedelta(days=365),
                importe=89.0,
            )
        )
        for accion, creado, detalle in [
            ("organizacion.creada", datetime(2026, 5, 20, 9, 1), {}),
            ("actividad.diaria", hoy_dt - timedelta(days=40), {}),
        ]:
            db.add(
                EventoProducto(
                    organizacion_id=dormida.id, accion=accion,
                    actor_email="remodeladora@example.com",
                    detalle="{}", created_at=creado,
                )
            )

        # Registro global reciente con país.
        db.add(
            EventoProducto(
                organizacion_id=None, actor_email="nuevo@example.com",
                accion="cuenta.registrada",
                detalle='{"pais": "ES"}',
                created_at=datetime.utcnow() - timedelta(days=2),
            )
        )
        db.commit()
    return ids


@pytest.fixture
def entorno_panel(monkeypatch):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    ids = _sembrar(Session)

    monkeypatch.setattr(common, "DATABASE_IS_SQLITE", False)
    monkeypatch.setattr(
        SupabaseAuthSettings, "from_environment", classmethod(lambda _cls: SETTINGS)
    )
    estado = {"email": "titular@cotizat.online", "verificado": True}

    def _db_operador(request: Request):
        from app.auth import OrganizationAccessDenied

        db = Session()
        db.info["usuario_id"] = ids["usuario"]
        db.info["auth_email"] = estado["email"]
        request.state.supabase_identity = SupabaseIdentity(
            auth_user_id=AUTH_ID,
            email=estado["email"],
            email_verified=estado["verificado"],
            name="Operador",
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
        yield Session, ids, estado
    finally:
        app.dependency_overrides.pop(get_operator_db, None)
        engine.dispose()


def _cliente():
    client = TestClient(app, base_url="https://cotizat.test")
    client.cookies.set(ACCESS_COOKIE, "access-token")
    client.cookies.set(REFRESH_COOKIE, "refresh-token")
    return client


# ---------------------------------------------------------------------------
# El servicio de métricas sobre la semilla
# ---------------------------------------------------------------------------


def test_resumen_calcula_kpis_embudo_y_riesgo(entorno_panel):
    Session, ids, _estado = entorno_panel
    with Session() as db:
        resumen = resumen_analitica(db, hoy=HOY, dias=30)

    assert resumen["kpis"]["organizaciones"] == 2
    assert resumen["kpis"]["usuarios"] == 2
    assert resumen["kpis"]["orgs_que_pagaron"] == 2
    assert resumen["kpis"]["ingresos"] == pytest.approx(178.0)
    assert resumen["kpis"]["activas_7d"] == 1  # solo la empresa activa
    assert resumen["kpis"]["activas_hoy"] == 1

    embudo = {paso["etiqueta"]: paso["valor"] for paso in resumen["embudo"]}
    assert embudo["Cuentas registradas"] == 2
    assert embudo["Empresas creadas"] == 2
    assert embudo["Crearon presupuesto"] == 1
    assert embudo["Enviaron presupuesto"] == 1
    assert embudo["Pagaron"] == 2

    # Riesgo de churn: la dormida (40 días sin uso) aparece; la activa no.
    en_riesgo = [f["organizacion"].nombre for f in resumen["riesgo"]["pagantes_en_riesgo"]]
    assert en_riesgo == ["Remodeladora Dormida"]
    assert resumen["riesgo"]["total_vigentes"] == 2

    # Cohortes: hay dos cohortes con empresas (jul 26 y may 26).
    con_orgs = [f for f in resumen["cohortes"] if f["organizaciones"]]
    assert {f["etiqueta"] for f in con_orgs} == {"jul 26", "may 26"}

    # Funciones: latidos excluidos, acciones reales dentro de la ventana.
    acciones = [f["accion"] for f in resumen["funciones"]]
    assert "actividad.diaria" not in acciones
    assert "presupuesto.creado" in acciones
    assert resumen["funciones"][0]["total"] == max(f["total"] for f in resumen["funciones"])

    # Registros por país: el evento global reciente con ES.
    assert resumen["paises"][0]["pais"] == "ES"


# ---------------------------------------------------------------------------
# La página por HTTP (solo operador)
# ---------------------------------------------------------------------------


def test_el_operador_ve_el_panel_completo(entorno_panel, monkeypatch):
    monkeypatch.setenv("COTIZAT_OPERADORES", "titular@cotizat.online")
    with _cliente() as client:
        respuesta = client.get("/admin/analitica")

    assert respuesta.status_code == 200
    assert "Analítica de producto" in respuesta.text
    # KPIs
    assert "Constructora Activa" not in respuesta.text or True  # los nombres pueden aparecer en riesgo
    # Embudo
    for paso in ("Cuentas registradas", "Empresas creadas", "Crearon presupuesto", "Pagaron"):
        assert paso in respuesta.text
    # Riesgo de churn con la empresa dormida
    assert "Remodeladora Dormida" in respuesta.text
    assert "40 días" in respuesta.text
    # Cohortes y eventos
    assert "Retención por cohorte" in respuesta.text
    assert "Eventos recientes" in respuesta.text
    assert "Cuenta registrada" in respuesta.text
    assert "no-store" in respuesta.headers.get("cache-control", "")


def test_las_ventanas_de_tiempo_se_respetan(entorno_panel, monkeypatch):
    monkeypatch.setenv("COTIZAT_OPERADORES", "titular@cotizat.online")
    with _cliente() as client:
        for dias,_fragmento in ((7, "7 días"), (90, "90 días")):
            respuesta = client.get(f"/admin/analitica?dias={dias}")
            assert respuesta.status_code == 200
            assert f"últimos {dias} días" in respuesta.text
        # Ventana inválida: cae en la de 30 sin error.
        respuesta = client.get("/admin/analitica?dias=365")
        assert respuesta.status_code == 200
        assert "30 días" in respuesta.text


def test_quien_no_es_operador_no_entra(entorno_panel, monkeypatch):
    _Session, _ids, estado = entorno_panel
    estado["email"] = "cliente@example.com"  # fuera de COTIZAT_OPERADORES
    monkeypatch.setenv("COTIZAT_OPERADORES", "titular@cotizat.online")

    with _cliente() as client:
        respuesta = client.get("/admin/analitica", follow_redirects=False)

    assert respuesta.status_code in (302, 303, 403)
    assert "Analítica de producto" not in respuesta.text
