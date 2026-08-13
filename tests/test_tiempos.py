"""Pruebas del motor de estimación de tiempos de obra (app/services/tiempos.py)."""
from types import SimpleNamespace

from app.services.tiempos import (
    calcular_tiempos_presupuesto,
    factor_unidad_tiempo,
    horas_por_unidad_descompuesto,
    tiempos_partida,
)


def _fila(tipo="recurso", grupo="MANO DE OBRA", codigo="mo001", unidad="h",
          descripcion="Oficial", rendimiento=None, categoria=""):
    return {
        "tipo": tipo,
        "grupo": grupo,
        "codigo": codigo,
        "unidad": unidad,
        "descripcion": descripcion,
        "rendimiento": rendimiento,
        "precio_unitario": 10,
        "categoria": categoria,
    }


def _partida(cantidad=10, descomp=None, cat_id=None, coste_mo=0, nombre="P",
             capitulo="CAP", tipo="included", seleccionada=True):
    return SimpleNamespace(
        id=1, capitulo=SimpleNamespace(nombre=capitulo), nombre=nombre,
        unidad="m2", cantidad_total=cantidad, coste_mano_obra=coste_mo,
        partida_catalogo_id=cat_id, descomposicion_cype=descomp,
        tipo_partida=tipo, seleccionada=seleccionada,
    )


def _descomp(*filas):
    return SimpleNamespace(filas=list(filas))


# ---------------------------------------------------------------------------
# Factor de unidades
# ---------------------------------------------------------------------------

def test_factor_unidad_tiempo():
    assert factor_unidad_tiempo("h") == 1
    assert factor_unidad_tiempo("H.") == 1
    assert factor_unidad_tiempo("horas") == 1
    assert factor_unidad_tiempo("hrs") == 1
    assert factor_unidad_tiempo("día") == 8
    assert factor_unidad_tiempo("jornada", 9) == 9
    assert factor_unidad_tiempo("Días", 7) == 7
    assert factor_unidad_tiempo("kg") is None
    assert factor_unidad_tiempo("%") is None
    assert factor_unidad_tiempo("") is None
    assert factor_unidad_tiempo(None) is None


# ---------------------------------------------------------------------------
# Descompuesto → horas por unidad
# ---------------------------------------------------------------------------

def test_horas_por_unidad_descompuesto():
    filas = [
        _fila(rendimiento=0.537),                              # oficial: 0,537 h
        _fila(codigo="mo002", descripcion="Peón", unidad="día", rendimiento=0.25),  # 2 h
        _fila(grupo="MATERIALES", codigo="mt001", unidad="kg", rendimiento=8.5),
        _fila(grupo="MAQUINARIA", codigo="mq001", unidad="h", descripcion="Mezcladora", rendimiento=0.1),
        _fila(grupo="COMPLEMENTARIOS", unidad="%", rendimiento=3),
        _fila(tipo="subtotal", grupo="MANO DE OBRA"),
        _fila(tipo="total"),
    ]
    res = horas_por_unidad_descompuesto(filas, 8)
    assert abs(res["mano_obra"] - (0.537 + 0.25 * 8)) < 1e-6
    assert abs(res["equipos"] - 0.1) < 1e-6
    assert abs(res["total"] - (0.537 + 2.0 + 0.1)) < 1e-6
    assert len(res["detalle"]) == 3


def test_horas_por_unidad_ignora_filas_sin_tiempo():
    filas = [
        _fila(grupo="MATERIALES", unidad="kg", rendimiento=8.5),
        _fila(grupo="MATERIALES", unidad="m3", rendimiento=2),
        _fila(tipo="total"),
    ]
    res = horas_por_unidad_descompuesto(filas)
    assert res["total"] == 0
    assert res["detalle"] == []


def test_categoria_explicita_prevalece_sobre_grupo():
    # Aunque el grupo parezca de materiales, la categoría explícita manda.
    fila = _fila(grupo="MATERIALES", categoria="mano_obra", rendimiento=0.5)
    res = horas_por_unidad_descompuesto([fila])
    assert res["mano_obra"] == 0.5
    assert res["equipos"] == 0


# ---------------------------------------------------------------------------
# Prioridad de fuentes por partida
# ---------------------------------------------------------------------------

def test_prioridad_descompuesto_sobre_catalogo_y_coste():
    descomp = _descomp(_fila(rendimiento=0.5))
    t = tiempos_partida(_partida(descomp=descomp, cat_id=7, coste_mo=999))
    assert t["fuente"] == "descompuesto"
    assert abs(t["horas_por_unidad"] - 0.5) < 1e-9
    assert abs(t["horas"] - 5.0) < 1e-9


def test_fuente_catalogo_cuando_no_hay_filas_de_tiempo():
    descomp = _descomp(_fila(grupo="MATERIALES", unidad="kg", rendimiento=5))
    t = tiempos_partida(
        _partida(descomp=descomp, cat_id=7, coste_mo=999),
        catalogo_tiempos={7: 2.5},
    )
    assert t["fuente"] == "catalogo"
    assert abs(t["horas_por_unidad"] - 2.5) < 1e-9
    assert abs(t["horas"] - 25.0) < 1e-9


def test_fuente_coste_como_ultimo_respaldo():
    t = tiempos_partida(_partida(coste_mo=40), tarifa_hora_media=8)
    assert t["fuente"] == "coste"
    assert abs(t["horas_por_unidad"] - 5.0) < 1e-9
    assert abs(t["horas"] - 50.0) < 1e-9


def test_sin_datos_si_no_hay_nada():
    t = tiempos_partida(_partida(), usar_estimacion_coste=False)
    assert t["fuente"] == "sin_datos"
    assert t["horas"] == 0
    assert t["horas_por_unidad"] == 0


def test_estimacion_por_coste_desactivada():
    t = tiempos_partida(_partida(coste_mo=40), usar_estimacion_coste=False)
    assert t["fuente"] == "sin_datos"


# ---------------------------------------------------------------------------
# Totales del presupuesto
# ---------------------------------------------------------------------------

def _presupuesto(partidas):
    return SimpleNamespace(
        capitulos=[SimpleNamespace(nombre="CAP 1", partidas=partidas)],
        todas_partidas=partidas,
        usar_funciones_avanzadas=True,
    )


def test_totales_solo_suman_partidas_activas():
    descomp = _descomp(_fila(rendimiento=1.0))
    partidas = [
        _partida(cantidad=10, descomp=descomp, nombre="A"),
        _partida(cantidad=5, descomp=descomp, nombre="B", tipo="excluded"),
        _partida(cantidad=5, descomp=descomp, nombre="C", tipo="optional", seleccionada=False),
        _partida(cantidad=4, descomp=descomp, nombre="D", tipo="optional", seleccionada=True),
    ]
    res = calcular_tiempos_presupuesto(_presupuesto(partidas))
    # 10 + 4 unidades × 1 h = 14 h
    assert res["total_horas"] == 14.0
    assert res["n_partidas"] == 4
    assert res["n_partidas_activas"] == 2
    assert res["n_con_datos"] == 2
    assert res["total_dias"] == round(14.0 / 8.0, 1)


def test_desglose_por_capitulo_y_fuentes():
    descomp = _descomp(_fila(rendimiento=2.0))
    partidas = [
        _partida(cantidad=3, descomp=descomp, nombre="A", capitulo="CAP A"),
        _partida(cantidad=1, descomp=descomp, nombre="B", capitulo="CAP B"),
        _partida(cantidad=1, nombre="C", capitulo="CAP B", cat_id=9),
        _partida(cantidad=1, nombre="D", capitulo="CAP B", coste_mo=80),
    ]
    res = calcular_tiempos_presupuesto(
        _presupuesto(partidas),
        tarifa_hora_media=8,
        usar_estimacion_coste=True,
    )
    assert res["total_horas"] == 6 + 2 + 10  # A(3×2) + B(1×2) + D(80/8)
    cap_a = next(c for c in res["capitulos"] if c["nombre"] == "CAP A")
    cap_b = next(c for c in res["capitulos"] if c["nombre"] == "CAP B")
    assert cap_a["horas"] == 6.0
    assert cap_b["horas"] == 12.0
    assert res["resumen_fuentes"]["descompuesto"] == 2
    assert res["resumen_fuentes"]["coste"] == 1
    assert res["resumen_fuentes"]["sin_datos"] == 1
    assert res["sin_datos"] == ["C"]  # catálogo sin tiempo cargado
