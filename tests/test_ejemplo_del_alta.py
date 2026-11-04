"""El camino «ejemplo del alta → presupuesto propio» de punta a punta.

Lo que se mide aquí es la decisión de producto, no un detalle: el 02/11/2026
la base de producción tenía 36 presupuestos de ejemplo sembrados y **ninguno**
convertido en presupuesto real, y 33 de las 41 cuentas reales sin haber creado
nunca uno. El producto llamaba «demostración» al ejemplo, la guía avisaba de
que no contaba y «Duplicar» producía otra copia marcada como demo.

Estas pruebas fijan el comportamiento nuevo: duplicar el ejemplo debe dejar
un presupuesto real y un cliente real, y el recorrido debe reconocerlo.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import seeds
from app.database import get_db
from app.main import app
from app.models import (
    Base,
    Cliente,
    Configuracion,
    EventoProducto,
    Organizacion,
    Presupuesto,
)


@pytest.fixture()
def entorno():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Sesion = sessionmaker(bind=engine, autoflush=False)
    db = Sesion()
    org = Organizacion(nombre="Obra", slug="obra")
    db.add(org)
    db.flush()
    db.add(Configuracion(empresa_nombre="Obra", empresa_pais="España", iva_default=21.0))
    db.info["organizacion_id"] = org.id
    db.info["auth_email"] = "cliente@example.com"
    db.info["rol_membresia"] = "propietario"
    seeds.sembrar_demo(db, "es")
    db.commit()
    try:
        yield Sesion, db, org.id
    finally:
        db.close()
        engine.dispose()


def _cliente_web(Sesion, db):
    """TestClient con la sesión de prueba inyectada (sin Supabase Auth)."""

    def _get_db():
        yield db

    app.dependency_overrides[get_db] = _get_db
    return TestClient(app, base_url="http://testserver")


def test_duplicar_el_ejemplo_produce_un_presupuesto_real(entorno):
    Sesion, db, org_id = entorno
    ejemplo = db.query(Presupuesto).one()
    assert ejemplo.es_demo is True and ejemplo.es_ejemplo is True

    web = _cliente_web(Sesion, db)
    try:
        respuesta = web.post(f"/presupuestos/{ejemplo.id}/duplicar", follow_redirects=False)
    finally:
        app.dependency_overrides.clear()

    assert respuesta.status_code in (200, 303, 307)
    db.expire_all()
    copias = [p for p in db.query(Presupuesto).all() if p.id != ejemplo.id]
    assert len(copias) == 1
    copia = copias[0]
    # Es trabajo del usuario: ni demo ni ejemplo.
    assert copia.es_demo is False
    assert copia.es_ejemplo is False
    # Y conserva las partidas del ejemplo: no nace vacío.
    assert sum(len(c.partidas) for c in copia.capitulos) > 0


def test_duplicar_el_ejemplo_crea_un_cliente_real(entorno):
    """El cliente del ejemplo no puede seguir siendo «de ejemplo» en la copia."""
    Sesion, db, org_id = entorno
    ejemplo = db.query(Presupuesto).one()
    cliente_ejemplo = ejemplo.cliente
    assert cliente_ejemplo.es_demo is True

    web = _cliente_web(Sesion, db)
    try:
        web.post(f"/presupuestos/{ejemplo.id}/duplicar", follow_redirects=False)
    finally:
        app.dependency_overrides.clear()

    db.expire_all()
    copia = (
        db.query(Presupuesto)
        .filter(Presupuesto.id != ejemplo.id)
        .one()
    )
    assert copia.cliente.id != cliente_ejemplo.id
    assert copia.cliente.es_demo is False
    assert copia.cliente.es_ejemplo is False
    # Y el paso «crea un cliente real» ya está cumplido sin escribir nada.
    reales = db.query(Cliente).filter(Cliente.es_demo.is_(False)).count()
    assert reales == 1


def test_duplicar_emite_el_evento_del_embudo(entorno):
    """Duplicar es crear un presupuesto: si no se mide, el embudo miente."""
    Sesion, db, org_id = entorno
    ejemplo = db.query(Presupuesto).one()

    web = _cliente_web(Sesion, db)
    try:
        web.post(f"/presupuestos/{ejemplo.id}/duplicar", follow_redirects=False)
    finally:
        app.dependency_overrides.clear()

    db.expire_all()
    eventos = (
        db.query(EventoProducto)
        .filter(EventoProducto.accion == "presupuesto.creado")
        .all()
    )
    assert len(eventos) == 1
    detalle = eventos[0].detalle_dict()
    assert detalle.get("origen") == "duplicado"
    assert detalle.get("primero") is True
    assert detalle.get("partidas", 0) > 0


def test_duplicar_un_presupuesto_normal_no_crea_cliente_nuevo(entorno):
    """La regla del cliente solo aplica al ejemplo, no a cualquier copia."""
    Sesion, db, org_id = entorno
    cliente = Cliente(nombre="Cliente propio")
    db.add(cliente)
    db.flush()
    propio = Presupuesto(
        numero="P-PROPIO-1",
        year=2026,
        fecha=None,
        titulo="Obra propia",
        client_id=cliente.id,
        es_demo=False,
    )
    from datetime import date

    propio.fecha = date.today()
    db.add(propio)
    db.commit()
    antes = db.query(Cliente).count()

    web = _cliente_web(Sesion, db)
    try:
        web.post(f"/presupuestos/{propio.id}/duplicar", follow_redirects=False)
    finally:
        app.dependency_overrides.clear()

    db.expire_all()
    assert db.query(Cliente).count() == antes
    copia = (
        db.query(Presupuesto)
        .filter(Presupuesto.id != propio.id, Presupuesto.titulo.like("Copia de%"))
        .one()
    )
    assert copia.client_id == cliente.id
    assert copia.es_demo is False


# ---------------------------------------------------------------------------
# La guía de inicio: el presupuesto primero
# ---------------------------------------------------------------------------

def test_la_guia_empieza_por_el_presupuesto_y_no_por_configurar_la_empresa(entorno):
    """7 de 41 llegaron al presupuesto y 2 al PDF: se caían al final.

    El orden anterior era empresa → catálogo → cliente → presupuesto → PDF,
    es decir, tres pasos de preparación antes del único que da valor.
    """
    from app.services.onboarding import estado_recorrido_inicial

    Sesion, db, org_id = entorno
    estado = estado_recorrido_inicial(db)
    claves = [paso["clave"] for paso in estado["pasos"]]
    # Desde el 04/11/2026 delante del presupuesto va un solo paso: confirmar
    # las tarifas. No es preparación, es el dato del que sale el importe; el
    # resto de la configuración sigue después del PDF.
    assert claves[:3] == ["tarifas", "presupuesto", "pdf"]
    assert claves.index("empresa") > claves.index("pdf")


def test_el_paso_del_presupuesto_lleva_al_ejemplo_no_a_un_formulario_vacio(entorno):
    Sesion, db, org_id = entorno
    from app.services.onboarding import estado_recorrido_inicial

    ejemplo = db.query(Presupuesto).one()
    paso = {p["clave"]: p for p in estado_recorrido_inicial(db)["pasos"]}["presupuesto"]
    assert paso["url"] == f"/presupuestos/{ejemplo.id}"
    assert paso["accion"] == "Abrir mi presupuesto"
    assert "partidas" in paso["detalle"]
    assert paso["completo"] is False


def test_el_paso_del_presupuesto_se_completa_al_duplicar(entorno):
    """Duplicar el ejemplo es el gesto que convierte la cuenta en usuario."""
    Sesion, db, org_id = entorno
    from app.services.onboarding import estado_recorrido_inicial

    ejemplo = db.query(Presupuesto).one()
    web = _cliente_web(Sesion, db)
    try:
        web.post(f"/presupuestos/{ejemplo.id}/duplicar", follow_redirects=False)
    finally:
        app.dependency_overrides.clear()

    db.expire_all()
    estado = estado_recorrido_inicial(db)
    paso = {p["clave"]: p for p in estado["pasos"]}["presupuesto"]
    assert paso["completo"] is True


# ---------------------------------------------------------------------------
# El panel no puede volver a enseñar un cero que parece un dato
# ---------------------------------------------------------------------------

def test_el_panel_avisa_cuando_la_telemetria_falla(entorno):
    """Caso real del 02/11/2026: 41 cuentas y «0 presupuestos» en el panel."""
    Sesion, db, org_id = entorno
    from app.services import telemetria
    from app.services.analitica import resumen_analitica

    original = dict(telemetria._ULTIMO_FALLO)
    try:
        telemetria._ULTIMO_FALLO.clear()
        telemetria._ULTIMO_FALLO["presupuesto.creado"] = "OperationalError: boom"
        kpis = resumen_analitica(db)["kpis"]
        assert kpis["telemetria_rota"] is True
        assert kpis["telemetria_fallos"] == [
            {"accion": "presupuesto.creado", "motivo": "OperationalError: boom"}
        ]
    finally:
        telemetria._ULTIMO_FALLO.clear()
        telemetria._ULTIMO_FALLO.update(original)

    # Sin fallos recientes, el cero vuelve a ser un dato y no una alarma.
    kpis = resumen_analitica(db)["kpis"]
    assert kpis["telemetria_rota"] is False
    assert kpis["telemetria_fallos"] == []
