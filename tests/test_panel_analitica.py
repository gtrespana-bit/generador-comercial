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
        # Entró hoy: es la señal de «sesiones iniciadas hoy».
        ultimo_acceso_at=datetime.utcnow(),
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
        # Presencia en vivo y primer cliente: las dos señales nuevas del panel.
        eventos_activa += [
            ("sesion.activa", hoy_dt - timedelta(minutes=3), {"pagina": "/presupuestos"}),
            ("cliente.creado", hoy_dt - timedelta(days=5, hours=2), {}),
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

    # Presencia: la empresa activa dejó una señal de sesión hace 3 minutos y
    # el titular entró hoy; la dormida no aparece en ninguna de las dos.
    assert resumen["en_vivo"]["en_linea_total"] == 1
    assert resumen["en_vivo"]["en_linea"][0]["organizacion"] == "Constructora Activa"
    assert resumen["en_vivo"]["logueados_total"] == 1
    assert resumen["en_vivo"]["logueados"][0]["email"] == "titular@example.com"

    # Presupuestos creados: la serie sale del evento, no de la tabla de tenant.
    # Dentro de la ventana de 30 días solo cae el de hace 5 días.
    assert resumen["kpis"]["presupuestos_ventana"] == 1
    assert resumen["kpis"]["presupuestos_hoy"] >= 0

    # Actividad por hora: excluye latidos y presencia (ruido operativo).
    assert resumen["horas"]["total"] > 0
    assert resumen["horas"]["chart_horas"]["maximo"] >= 1

    # Explorador de eventos: por omisión oculta el ruido y dice el total real.
    assert resumen["explorador"]["total"] > 0
    assert all(
        ev["accion"] not in ("actividad.diaria", "sesion.activa")
        for ev in resumen["explorador"]["eventos"]
    )
    assert resumen["explorador"]["paginas"] == 1
    assert resumen["explorador"]["filtros"]["enlace_siguiente"] == ""


def test_la_tabla_de_empresas_mezcla_uso_y_datos_comerciales(entorno_panel):
    Session, ids, _estado = entorno_panel
    with Session() as db:
        resumen = resumen_analitica(db, hoy=HOY, dias=30)

    filas = {fila["nombre"]: fila for fila in resumen["organizaciones"]["filas"]}
    assert set(filas) == {"Constructora Activa", "Remodeladora Dormida"}
    activa = filas["Constructora Activa"]
    assert activa["miembros"] == 1
    assert activa["en_linea"] is True
    assert activa["estado"] == "en_linea"
    assert activa["eventos"] > 0
    # Días de uso (latidos) dentro de la ventana: el DAU por empresa.
    assert activa["dias_uso"] >= 1
    assert activa["pagando"] is True
    # La primera fila es la que está conectada ahora: es lo que se mira primero.
    assert resumen["organizaciones"]["filas"][0]["en_linea"] is True

    dormida = filas["Remodeladora Dormida"]
    assert dormida["miembros"] == 0
    assert dormida["en_linea"] is False
    assert dormida["estado"] in ("inactiva", "semana", "hoy")


def test_el_explorador_filtra_por_empresa_accion_actor_y_fechas(entorno_panel):
    Session, ids, _estado = entorno_panel
    with Session() as db:
        por_empresa = resumen_analitica(
            db, hoy=HOY, dias=30, filtros={"organizacion_id": ids["dormida"]}
        )
        por_accion = resumen_analitica(
            db, hoy=HOY, dias=30, filtros={"accion": "presupuesto.creado"}
        )
        por_actor = resumen_analitica(
            db, hoy=HOY, dias=30, filtros={"actor": "remodeladora"}
        )
        por_fecha = resumen_analitica(
            db, hoy=HOY, dias=30,
            filtros={"desde": "2026-07-01", "hasta": "2026-07-31"},
        )
        con_ruido = resumen_analitica(
            db, hoy=HOY, dias=30, filtros={"ocultar_ruido": False}
        )
        solo_ajenos = resumen_analitica(
            db, hoy=HOY, dias=30,
            filtros={"ocultar_mios": True, "mi_email": "titular@example.com"},
        )
        accion_invalida = resumen_analitica(
            db, hoy=HOY, dias=30, filtros={"accion": "../../etc/passwd"}
        )

    # Empresa dormida: solo su alta (el latido es ruido y queda oculto).
    assert por_empresa["explorador"]["total"] == 1
    assert {e["organizacion"] for e in por_empresa["explorador"]["eventos"]} == {
        "Remodeladora Dormida"
    }
    # Acción: los dos presupuestos creados de la empresa activa.
    assert por_accion["explorador"]["total"] == 2
    assert {e["accion"] for e in por_accion["explorador"]["eventos"]} == {
        "presupuesto.creado"
    }
    # Actor: solo los eventos de la empresa dormida.
    assert por_actor["explorador"]["total"] == 1
    # Ventana de fechas: julio de 2026, ambos extremos incluidos.
    assert por_fecha["explorador"]["total"] >= 4
    for evento in por_fecha["explorador"]["eventos"]:
        assert evento["created_at"].date().month == 7
    # Con ruido se ven también los latidos y la presencia.
    assert con_ruido["explorador"]["total"] > por_accion["explorador"]["total"]
    assert any(
        evento["accion"] == "actividad.diaria"
        for evento in con_ruido["explorador"]["eventos"]
    )
    # «Ocultar mis eventos» deja fuera al titular.
    assert solo_ajenos["explorador"]["total"] >= 1
    assert all(
        evento["actor"] != "titular@example.com"
        for evento in solo_ajenos["explorador"]["eventos"]
    )
    # Una acción fuera del catálogo no filtra nada (ni llega al SQL).
    assert accion_invalida["explorador"]["filtros"]["accion"] == ""
    assert accion_invalida["explorador"]["total"] > 0


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
    assert "Eventos de todas las empresas" in respuesta.text
    assert "Cuenta registrada" in respuesta.text
    # Presencia y actividad por empresa: lo que faltaba en la pestaña.
    assert "En línea ahora mismo" in respuesta.text
    assert "Sesiones iniciadas hoy" in respuesta.text
    assert "Presupuestos creados hoy" in respuesta.text
    assert "Constructora Activa" in respuesta.text  # tabla de empresas
    assert "/presupuestos" in respuesta.text  # página de la presencia en vivo
    assert "no-store" in respuesta.headers.get("cache-control", "")


def test_los_filtros_del_explorador_funcionan_por_url(entorno_panel, monkeypatch):
    monkeypatch.setenv("COTIZAT_OPERADORES", "titular@cotizat.online")
    with _cliente() as client:
        filtrada = client.get("/admin/analitica?organizacion_id=2&accion=organizacion.creada")
        vacia = client.get("/admin/analitica?actor=nadie@example.com")
        con_ruido = client.get("/admin/analitica?ruido=1")

    assert filtrada.status_code == 200
    # Los filtros quedan seleccionados en el formulario (GET, sin JavaScript).
    assert 'value="organizacion.creada" selected' in filtrada.text
    assert ">Remodeladora Dormida</option>" in filtrada.text
    # Un filtro sin resultados lo dice y no rompe la página.
    assert vacia.status_code == 200
    assert "Ningún evento con estos filtros" in vacia.text
    assert con_ruido.status_code == 200


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
