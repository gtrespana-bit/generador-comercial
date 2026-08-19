from types import SimpleNamespace
from decimal import Decimal
from app.services.apu import calcular_apu


def test_apu_recalcula_filas_por_rendimiento_y_precio():
    r = calcular_apu([
        SimpleNamespace(tipo='recurso', categoria='materiales', rendimiento=2, precio_unitario=10, importe=0),
        SimpleNamespace(tipo='recurso', categoria='mano_obra', rendimiento=1.5, precio_unitario=8, importe=0),
    ])
    assert r.materiales == Decimal('20.00')
    assert r.mano_obra == Decimal('12.00')
    assert r.coste_directo == Decimal('32.00')
