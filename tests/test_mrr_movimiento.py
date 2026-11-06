"""El movimiento del MRR: no solo cuánto, sino por qué.

«MRR 1.200 US$» no dice si el negocio crece o se está fugando: un mes puede
cerrar plano con dos altas y dos bajas que se compensan. Estas pruebas fijan la
descomposición estándar —nuevo, expansión, contracción y baja— y, sobre todo,
que **cuadre**: apertura + neto = cierre, con datos mezclados a propósito.

El día de referencia es fijo (15/03/2026) para que las fechas de las licencias
se lean sin depender del calendario de la máquina que corre la suite.
"""
from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, Licencia, Organizacion
from app.services.panel_finanzas import movimiento_mrr, resumen_financiero

HOY = date(2026, 3, 15)


def _db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine)()


def _org(db, nombre: str) -> Organizacion:
    org = Organizacion(nombre=nombre, slug=nombre.lower().replace(" ", "-"))
    db.add(org)
    db.commit()
    return org


def _licencia(db, org, *, importe, inicio, vence, origen="pago", estado="activa"):
    lic = Licencia(
        organizacion_id=org.id,
        origen=origen,
        importe=importe,
        inicio=inicio,
        vence=vence,
        estado=estado,
        creada_por_email="operador@example.com",
    )
    db.add(lic)
    db.commit()
    return lic


@pytest.fixture
def mezcla():
    """Cinco clientes con los cuatro movimientos a la vez.

    Apertura = 28/02/2026, cierre = 15/03/2026 (el mes en curso se mide hoy).
    """
    engine, db = _db()
    try:
        # Nuevo: no existía en la apertura, entra el 2 de marzo (mensual, 25).
        _licencia(db, _org(db, "Nueva"), importe=25.0,
                  inicio=date(2026, 3, 2), vence=date(2026, 4, 2))
        # Expansión: anual de 120 (10/mes) + un extra mensual de 15 desde el 5.
        estable = _org(db, "Estable")
        _licencia(db, estable, importe=120.0,
                  inicio=date(2026, 1, 1), vence=date(2027, 1, 1))
        _licencia(db, estable, importe=15.0,
                  inicio=date(2026, 3, 5), vence=date(2026, 4, 5))
        # Contracción: 35 en la apertura, 5 al cierre (se le va un extra de 30).
        mixta = _org(db, "Mixta")
        _licencia(db, mixta, importe=30.0,
                  inicio=date(2026, 2, 1), vence=date(2026, 3, 1))
        _licencia(db, mixta, importe=60.0,
                  inicio=date(2026, 2, 1), vence=date(2026, 6, 1))
        # Baja: pagaba 50 y no renueva.
        _licencia(db, _org(db, "Se va"), importe=50.0,
                  inicio=date(2026, 2, 1), vence=date(2026, 2, 28))
        # Ruido que no debe contar: cortesía, importe cero y cancelada.
        _licencia(db, _org(db, "Cortesía"), importe=99.0, origen="cortesia",
                  inicio=date(2026, 1, 1), vence=date(2027, 1, 1))
        _licencia(db, _org(db, "Gratis"), importe=0.0,
                  inicio=date(2026, 1, 1), vence=date(2027, 1, 1))
        _licencia(db, _org(db, "Cancelada"), importe=70.0, estado="cancelada",
                  inicio=date(2026, 1, 1), vence=date(2027, 1, 1))
        yield db
    finally:
        db.close()
        engine.dispose()


def test_las_cuatro_piezas_del_mes_cuadran(mezcla):
    datos = movimiento_mrr(mezcla, hoy=HOY)
    mes = datos["mes"]

    assert mes["etiqueta"] == "Mar 2026"
    assert mes["en_curso"] is True
    assert mes["inicio"] == pytest.approx(95.0)   # 35 + 50 + 10
    assert mes["nuevo"] == pytest.approx(25.0)
    assert mes["expansion"] == pytest.approx(15.0)
    assert mes["contraccion"] == pytest.approx(30.0)
    assert mes["baja"] == pytest.approx(50.0)
    assert mes["cierre"] == pytest.approx(55.0)   # 25 + 10 + 15 + 5
    assert mes["neto"] == pytest.approx(-40.0)
    assert mes["cuadra"] is True
    assert datos["cuadra"] is True


def test_cada_movimiento_trae_su_numero_de_clientes(mezcla):
    mes = movimiento_mrr(mezcla, hoy=HOY)["mes"]
    assert mes["clientes_nuevos"] == 1
    assert mes["clientes_baja"] == 1
    assert mes["clientes_expansion"] == 1
    assert mes["clientes_contraccion"] == 1
    # Activos al cierre: la nueva, la estable y la mixta.
    assert mes["clientes_activos"] == 3


def test_la_cortesia_el_cero_y_lo_cancelado_no_son_mrr(mezcla):
    """Solo paga quien paga: ni regalos, ni importes a cero, ni canceladas."""
    mes = movimiento_mrr(mezcla, hoy=HOY)["mes"]
    assert mes["cierre"] == pytest.approx(55.0)
    assert mes["cierre"] < 55.0 + 99.0 + 70.0


def test_el_cierre_del_mes_coincide_con_el_mrr_del_resumen(mezcla):
    """Dos caminos al mismo número: si divergen, uno de los dos miente."""
    movimiento = movimiento_mrr(mezcla, hoy=HOY)
    resumen = resumen_financiero(mezcla, hoy=HOY)
    assert movimiento["mes"]["cierre"] == pytest.approx(resumen["mrr"], abs=0.01)


def test_la_serie_trae_los_meses_pedidos_y_todos_cuadran(mezcla):
    serie = movimiento_mrr(mezcla, hoy=HOY, meses=6)["serie"]
    assert [mes["etiqueta"] for mes in serie] == [
        "Oct 2025", "Nov 2025", "Dic 2025", "Ene 2026", "Feb 2026", "Mar 2026",
    ]
    assert all(mes["cuadra"] for mes in serie)
    # En febrero la bajada sí existía: su cierre incluye lo que en marzo se va.
    febrero = serie[-2]
    assert febrero["cierre"] >= 95.0


def test_el_mes_en_curso_no_cuenta_lo_que_aun_no_ha_pasado(mezcla):
    """Una licencia que empieza el 20 de marzo no es MRR el día 15."""
    _licencia(mezcla, _org(mezcla, "Futura"), importe=80.0,
              inicio=date(2026, 3, 20), vence=date(2026, 4, 20))
    mes = movimiento_mrr(mezcla, hoy=HOY)["mes"]
    assert mes["cierre"] == pytest.approx(55.0)
    assert mes["nuevo"] == pytest.approx(25.0)


def test_sin_clientes_de_pago_el_mes_es_cero_y_no_revienta():
    engine, db = _db()
    try:
        datos = movimiento_mrr(db, hoy=HOY)
        mes = datos["mes"]
        assert mes["inicio"] == 0.0 and mes["cierre"] == 0.0
        assert mes["neto"] == 0.0
        assert mes["variacion"] is None
        assert datos["cuadra"] is True
        assert len(datos["serie"]) == 6
    finally:
        db.close()
        engine.dispose()


def test_la_variacion_del_mes_es_el_neto_sobre_la_apertura(mezcla):
    mes = movimiento_mrr(mezcla, hoy=HOY)["mes"]
    assert mes["variacion"] == pytest.approx(round(-40.0 / 95.0 * 100, 1))
