"""Pruebas de la Fase 1 del panel profesional (roles, auditoría, ⌘K, avisos, finanzas)."""
from datetime import date, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import (
    CompraPlan,
    EventoAdmin,
    Licencia,
    Membresia,
    OperadorProducto,
    Organizacion,
    Usuario,
)
from app.operadores import es_operador, rol_operador
from app.services.audit_admin import registrar_evento_admin, resumen_auditoria_admin
from app.services.operadores_admin import (
    GestionEquipoError,
    activar_operador,
    cambiar_rol_operador,
    crear_operador,
    exigir_superadmin,
    listar_operadores,
    suspender_operador,
)
from app.services.panel_busqueda import buscar_global
from app.services.panel_finanzas import resumen_financiero
from app.services.panel_notificaciones import notificaciones_admin


def _db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine)()


def _org(db, nombre="Constructora Test", slug="constructora-test"):
    org = Organizacion(nombre=nombre, slug=slug)
    db.add(org)
    db.commit()
    return org


def _licencia(db, org, *, origen="pago", importe=89.0, inicio=None, vence=None):
    hoy = date.today()
    lic = Licencia(
        organizacion_id=org.id,
        origen=origen,
        importe=importe,
        inicio=inicio or hoy,
        vence=vence or hoy.replace(year=hoy.year + 1),
        creada_por_email="operador@example.com",
    )
    db.add(lic)
    db.commit()
    return lic


def test_env_es_semilla_y_la_base_puede_rebajar(monkeypatch):
    monkeypatch.setenv("COTIZAT_OPERADORES", "jefe@example.com")
    engine, db = _db()
    try:
        fila = OperadorProducto(
            email="jefe@example.com", rol="analista", activo=True,
            creado_por_email="super@example.com",
        )
        db.add(fila)
        db.commit()
        assert es_operador("jefe@example.com", email_verificado=True, db=db)
        assert rol_operador("jefe@example.com", email_verificado=True, db=db) == "analista"

        # Una suspensión manda sobre la semilla del entorno.
        fila.activo = False
        db.commit()
        assert not es_operador("jefe@example.com", email_verificado=True, db=db)
        assert rol_operador("jefe@example.com", email_verificado=True, db=db) == ""
    finally:
        db.close()
        engine.dispose()


def test_crear_cambiar_suspender_activar_operador():
    engine, db = _db()
    try:
        db.info["operador_rol"] = "superadmin"
        op = crear_operador(
            db,
            email="soporte@example.com",
            rol="soporte",
            operador_email="jefe@example.com",
            notas="Atención al cliente.",
        )
        db.commit()
        assert op.activo is True
        assert op.etiqueta_rol == "Soporte"

        cambiar_rol_operador(db, op.id, rol="admin", operador_email="jefe@example.com")
        db.commit()
        assert db.get(OperadorProducto, op.id).rol == "admin"

        suspender_operador(db, op.id, operador_email="jefe@example.com")
        db.commit()
        assert db.get(OperadorProducto, op.id).activo is False

        activar_operador(db, op.id, operador_email="jefe@example.com")
        db.commit()
        assert db.get(OperadorProducto, op.id).activo is True
    finally:
        db.close()
        engine.dispose()


def test_no_se_puede_rebajar_al_ultimo_superadmin():
    engine, db = _db()
    try:
        db.info["operador_rol"] = "superadmin"
        op = crear_operador(db, email="jefe@example.com", rol="superadmin", operador_email="x@example.com")
        db.commit()
        with pytest.raises(GestionEquipoError):
            cambiar_rol_operador(db, op.id, rol="admin", operador_email="x@example.com")
    finally:
        db.close()
        engine.dispose()


def test_solo_superadmin_gestiona_equipo():
    engine, db = _db()
    try:
        db.info["operador_rol"] = "soporte"
        with pytest.raises(GestionEquipoError, match="superadmin"):
            exigir_superadmin(db)
    finally:
        db.close()
        engine.dispose()


def test_listar_operadores_fusiona_env_y_db(monkeypatch):
    monkeypatch.setenv("COTIZAT_OPERADORES", "jefe@example.com")
    engine, db = _db()
    try:
        crear_operador(db, email="analista@example.com", rol="analista", operador_email="jefe@example.com")
        db.commit()
        filas = listar_operadores(db)
        emails = {f["email"] for f in filas}
        assert "jefe@example.com" in emails
        assert "analista@example.com" in emails
        jefe = next(f for f in filas if f["email"] == "jefe@example.com")
        assert jefe["origen"] == "env"
        assert jefe["rol"] == "superadmin"
    finally:
        db.close()
        engine.dispose()


def test_registrar_evento_admin_inmutable_y_sin_secretos():
    engine, db = _db()
    try:
        org = _org(db)
        ok = registrar_evento_admin(
            db,
            accion="licencia.concedida",
            operador_email="Jefe@Example.com",
            operador_rol="superadmin",
            entidad="licencia",
            entidad_id=7,
            organizacion_id=org.id,
            detalle={"importe": 89, "password": "secreto"},
        )
        assert ok is True
        evento = db.query(EventoAdmin).one()
        assert evento.operador_email == "jefe@example.com"
        assert "secreto" not in evento.detalle
        assert evento.accion == "licencia.concedida"
        assert evento.resultado == "ok"

        eventos = resumen_auditoria_admin(db, accion="licencia.concedida")
        assert len(eventos) == 1
    finally:
        db.close()
        engine.dispose()


def test_buscador_global_devuelve_cliente_licencia_y_operador():
    engine, db = _db()
    try:
        org = _org(db, nombre="Constructora Andina", slug="andina")
        _licencia(db, org, importe=89, vence=date.today().replace(year=date.today().year + 1))
        crear_operador(db, email="soporte@correo.com", rol="soporte", operador_email="jefe@example.com")
        db.commit()

        resultados = buscar_global(db, "andina")
        assert any(r["tipo"] == "cliente" and r["titulo"] == "Constructora Andina" for r in resultados)
        assert any(r["tipo"] == "licencia" for r in resultados)

        resultados_op = buscar_global(db, "correo.com")
        assert any(r["tipo"] == "operador" and r["titulo"] == "soporte@correo.com" for r in resultados_op)
    finally:
        db.close()
        engine.dispose()


def test_finanzas_mrr_arr_ltv_y_renovaciones():
    engine, db = _db()
    try:
        org_a = _org(db, "Cliente A", "cliente-a")
        org_b = _org(db, "Cliente B", "cliente-b")
        hoy = date.today()
        # A: anual activo (89/12 MRR). B: mensual activo (9.99 MRR).
        _licencia(db, org_a, importe=89.0, inicio=hoy, vence=hoy.replace(year=hoy.year + 1))
        _licencia(db, org_b, importe=9.99, inicio=hoy, vence=hoy.replace(month=hoy.month + 1))

        datos = resumen_financiero(db, hoy=hoy)
        assert datos["mrr"] == pytest.approx(89.0 / 12 + 9.99, abs=0.01)
        assert datos["arr"] == pytest.approx(round((89.0 / 12 + 9.99) * 12, 2), abs=0.01)
        assert datos["clientes_con_pago"] == 2
        assert datos["tasa_pago"] == 100.0
        assert datos["ltv_medio"] == pytest.approx((89.0 + 9.99) / 2, abs=0.01)
        assert datos["ticket_medio"] == pytest.approx((89.0 + 9.99) / 2, abs=0.01)
        assert len(datos["serie"]) == 6
    finally:
        db.close()
        engine.dispose()


def test_notificaciones_detectan_compra_pendiente_y_renovacion():
    engine, db = _db()
    try:
        org = _org(db)
        hoy = date.today()
        from datetime import timedelta
        _licencia(db, org, importe=9.99, inicio=hoy, vence=hoy + timedelta(days=10))
        db.add(
            CompraPlan(
                organizacion_id=org.id,
                plan="anual",
                metodo_pago="pago_movil",
                importe=89.0,
                moneda="USD",
                estado="pendiente",
                creada_por_email="cliente@example.com",
            )
        )
        db.commit()
        avisos = notificaciones_admin(db, hoy=hoy)
        assert any(a["tipo"] == "compra" for a in avisos)
        assert any(a["tipo"] == "renovacion" for a in avisos)
    finally:
        db.close()
        engine.dispose()


def test_migracion_defiende_el_panel_con_rls():
    from pathlib import Path

    fuente = Path("migrations/versions/a1b8c2d4e6f0_roles_operador_y_auditoria_admin.py").read_text()
    assert "cotizat_operador_select_own" in fuente
    assert "cotizat.operador_rol" in fuente
    assert "cotizat_evento_admin_select" in fuente
    assert "cotizat_evento_admin_insert" in fuente
