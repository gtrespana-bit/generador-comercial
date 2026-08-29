"""Pruebas de la Fase 2 del panel profesional (B1/B2/B3/B5/A5)."""
from datetime import date, datetime
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import (
    Cliente,
    CompraPlan,
    EventoAdmin,
    Factura,
    Licencia,
    NotaOperador,
    OperadorProducto,
    Organizacion,
    Pago,
    Usuario,
)
from app.services.automatizaciones_admin import (
    GestionAutomatizacionError,
    REGLAS,
    ejecutar_regla,
    estado_automatizaciones,
)
from app.services.panel_busqueda import buscar_global
from app.services.panel_clientes import crear_nota_operador, resumen_cliente
from app.services.panel_cobros import resumen_cobros
from app.services.panel_renovaciones import renovaciones_del_mes


def _db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine)()


def _org(db, nombre="Constructora Fase2", slug="fase2"):
    org = Organizacion(nombre=nombre, slug=slug)
    db.add(org)
    db.commit()
    return org


def _licencia(db, org, *, importe=89.0, inicio=None, vence=None, estado="activa"):
    hoy = date.today()
    lic = Licencia(
        organizacion_id=org.id,
        origen="pago",
        importe=importe,
        inicio=inicio or hoy,
        vence=vence or hoy.replace(year=hoy.year + 1),
        estado=estado,
        creada_por_email="operador@example.com",
    )
    db.add(lic)
    db.commit()
    return lic


def test_resumen_cliente_incluye_plan_cobros_notas_y_actividad():
    engine, db = _db()
    try:
        org = _org(db)
        _licencia(db, org, importe=89.0)
        cliente = Cliente(nombre="Obra Centro", organizacion_id=org.id)
        db.add(cliente)
        db.commit()
        nota = crear_nota_operador(
            db, org.id, contenido="Pedir renovación.", autor_email="jefe@example.com"
        )
        nota_id = nota.id
        evento = EventoAdmin(
            operador_email="jefe@example.com",
            operador_rol="superadmin",
            accion="cliente.nota_creada",
            entidad="organizacion",
            entidad_id=org.id,
            organizacion_id=org.id,
            detalle="{}",
        )
        db.add(evento)
        db.commit()

        ficha = resumen_cliente(db, org.id)
        assert ficha is not None
        assert ficha["organizacion"].id == org.id
        assert len(ficha["licencias"]) == 1
        assert ficha["ingresos"] == 89.0
        assert ficha["agregados"]["clientes"] == 1
        assert len(ficha["notas"]) == 1
        assert ficha["notas"][0].id == nota_id
        assert any(e.accion == "cliente.nota_creada" for e in ficha["eventos_admin"])
        assert ficha["vence_total"] is not None
    finally:
        db.close()
        engine.dispose()


def test_crear_nota_operador_rechaza_vacia_y_cliente_inexistente():
    engine, db = _db()
    try:
        with pytest.raises(ValueError, match="vacía"):
            crear_nota_operador(db, 1, contenido="   ", autor_email="a@b.com")
        with pytest.raises(ValueError, match="no existe"):
            crear_nota_operador(db, 999, contenido="hola", autor_email="a@b.com")
    finally:
        db.close()
        engine.dispose()


def test_resumen_cobros_une_licencias_compras_facturas_y_pagos():
    engine, db = _db()
    try:
        org = _org(db)
        hoy = date.today()
        _licencia(db, org, importe=89.0, inicio=hoy, vence=hoy.replace(year=hoy.year + 1))
        db.add(CompraPlan(
            organizacion_id=org.id,
            plan="anual",
            metodo_pago="stripe",
            importe=89.0,
            moneda="USD",
            estado="activa",
            creada_por_email="cliente@example.com",
        ))
        cliente = Cliente(nombre="Obra Centro", organizacion_id=org.id)
        db.add(cliente)
        db.commit()
        db.add(Factura(
            organizacion_id=org.id,
            numero="F-001",
            year=hoy.year,
            fecha=hoy,
            client_id=cliente.id,
            estado="emitida",
        ))
        db.add(Pago(
            organizacion_id=org.id,
            fecha=hoy,
            importe=50.0,
            moneda="USD",
            estado="confirmado",
            referencia="pago-1",
        ))
        db.commit()

        data = resumen_cobros(db, mes=hoy.replace(day=1), hoy=hoy)
        tipos = {m["tipo"] for m in data["movimientos"]}
        assert {"licencia", "compra", "factura", "pago"} <= tipos
        assert data["ingresos_mes"] == pytest.approx(89.0, abs=0.01)
        assert data["cobrado_mes"] >= 50.0
        assert data["pendientes_mes"] >= 1  # la factura emitida queda pendiente
    finally:
        db.close()
        engine.dispose()


def test_renovaciones_del_mes_detecta_lo_que_vence_ahora():
    engine, db = _db()
    try:
        org = _org(db)
        hoy = date.today()
        mes = hoy.replace(day=1)
        # Vence el día 15 del mes actual.
        if hoy.day < 15:
            vence = mes.replace(day=15)
        else:
            if mes.month == 12:
                mes2 = mes.replace(year=mes.year + 1, month=1, day=1)
            else:
                mes2 = mes.replace(month=mes.month + 1, day=1)
            vence = mes2
        _licencia(db, org, importe=9.99, inicio=vence.replace(day=1), vence=vence)

        data = renovaciones_del_mes(db, mes=vence.replace(day=1), hoy=hoy)
        assert data["total"] >= 1
        assert any(
            f["organizacion_id"] == org.id and f["vence"] == vence
            for f in data["filas"]
        )
    finally:
        db.close()
        engine.dispose()


def test_automatizaciones_estado_y_regla_invalida():
    engine, db = _db()
    try:
        assert len(REGLAS) >= 4
        estado = estado_automatizaciones(db)
        assert "por_renovar" in estado
        assert "recordatorios_hoy" in estado
        with pytest.raises(GestionAutomatizacionError, match="no existe"):
            ejecutar_regla(db, "no-existe")
    finally:
        db.close()
        engine.dispose()


def test_migracion_fase2_defiende_notas_y_cobros_con_operador():
    fuente = Path(
        "migrations/versions/c2d4e6f8a1b3_operador_gestion_cliente_y_cobros.py"
    ).read_text()
    assert "notas_operador" in fuente
    assert "GRANT SELECT, INSERT, UPDATE ON TABLE public.{TABLE}" in fuente
    assert "cotizat_nota_operador_select" in fuente
    assert "cotizat_nota_operador_insert" in fuente
    assert "cotizat_nota_operador_update" in fuente
    assert "admin_resumen_cliente" in fuente
    assert "admin_cobros_cliente" in fuente
    assert "SECURITY DEFINER" in fuente
    assert "cotizat.es_operador" in fuente
    # Regresión del SQL de Supabase: `facturas` no tiene columna `total`.
    assert "COALESCE(f.total, 0)" not in fuente
    assert "factura_items" in fuente


def test_buscador_global_enlaza_a_ficha_de_cliente():
    engine, db = _db()
    try:
        org = _org(db, nombre="Andina Fase2", slug="andina-fase2")
        resultados = buscar_global(db, "andina-fase2")
        cliente = next(r for r in resultados if r["tipo"] == "cliente")
        assert cliente["url"] == f"/admin/clientes/{org.id}"
    finally:
        db.close()
        engine.dispose()


def test_notas_operador_no_son_tenant_y_query_por_org():
    engine, db = _db()
    try:
        org1 = _org(db, "Cliente Uno", "cliente-uno")
        org2 = _org(db, "Cliente Dos", "cliente-dos")
        crear_nota_operador(db, org1.id, contenido="solo uno", autor_email="op@x.com")
        db.commit()
        notas1 = db.query(NotaOperador).filter(
            NotaOperador.organizacion_id == org1.id
        ).all()
        notas2 = db.query(NotaOperador).filter(
            NotaOperador.organizacion_id == org2.id
        ).all()
        assert len(notas1) == 1
        assert notas2 == []
    finally:
        db.close()
        engine.dispose()
