from decimal import Decimal
from app.services.rendimientos import Cuadrilla, calcular_rendimiento, coste_equipo


def test_cuadrilla_calcula_coste_por_unidad():
    r = calcular_rendimiento(Cuadrilla(oficial_hora=Decimal('10'), ayudante_hora=Decimal('6')), 8, 'm2', 10)
    assert r.coste_jornada == Decimal('140.80')
    assert r.coste_por_unidad == Decimal('17.60')


def test_equipo_respeta_modalidad():
    assert coste_equipo(30, 'viaje', viajes=2) == Decimal('60.00')
    assert coste_equipo(12, 'km', km=10) == Decimal('120.00')
