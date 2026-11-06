"""El movimiento del MRR, en la pantalla donde se decide.

El cálculo tiene su propia batería (``test_mrr_movimiento.py``); aquí se
comprueba lo otro: que la tarjeta aparezca en **Ingresos › Cobros del mes**, que
se lea como una cuenta (apertura, sumas, restas, cierre), que diga si cuadra y
que la línea del KPI de **Hoy** explique el cambio en vez de solo enseñarlo.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

from app.models import Licencia


def _sembrar_pago(Session, ids):
    """Un cliente de pago que entra **este** mes: hay «nuevo» que enseñar.

    Si la licencia viniera de antes, el mes estaría plano (mismo MRR en la
    apertura y al cierre) y la línea del KPI diría «sin movimientos», que es
    correcto pero no prueba nada.
    """
    hoy = date.today()
    with Session() as db:
        db.add(Licencia(
            organizacion_id=ids[0],
            estado="activa",
            origen="pago",
            importe=120.0,
            inicio=hoy.replace(day=1),
            vence=hoy + timedelta(days=365),
            creada_por_email="operador@example.com",
            created_at=datetime.utcnow(),
        ))
        db.commit()


def test_la_tarjeta_del_mrr_vive_en_cobros_del_mes(operador, cliente_panel):
    Session, ids = operador
    _sembrar_pago(Session, ids)
    respuesta = cliente_panel.get("/admin/ingresos?tab=cobros")
    assert respuesta.status_code == 200
    html = respuesta.text

    assert "Movimiento del MRR" in html
    for pieza in ("Apertura del mes", "Nuevo", "Expansión", "Contracción", "Bajas", "Cierre"):
        assert pieza in html, f"falta la pieza «{pieza}» en la cuenta del MRR"
    assert "Apertura + neto = cierre" in html
    # El cliente lleva dos meses pagando: el mes no está vacío.
    assert "sin movimientos" not in html.split("Movimiento del MRR")[1][:400]


def test_la_tarjeta_dice_la_verdad_cuando_no_hay_movimientos(operador, cliente_panel):
    """Sin cliente de pago, la tarjeta no inventa: todo a cero y avisa."""
    respuesta = cliente_panel.get("/admin/ingresos?tab=cobros")
    assert respuesta.status_code == 200
    html = respuesta.text
    assert "Movimiento del MRR" in html
    assert "0.00 US$/mes" in html


def test_el_kpi_de_hoy_explica_el_cambio(operador, cliente_panel):
    Session, ids = operador
    _sembrar_pago(Session, ids)
    html = cliente_panel.get("/admin").text
    assert "mrr-kpi-mov" in html
    # La línea lleva las cuatro piezas, no solo el porcentaje.
    tramo = html.split("mrr-kpi-mov")[1][:300]
    for pieza in ("nuevo", "expansión", "baja"):
        assert pieza in tramo, f"la línea del KPI no menciona «{pieza}»"
