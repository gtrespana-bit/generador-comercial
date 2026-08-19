from types import SimpleNamespace
import pytest
from app.services.proyectos_moneda import moneda_proyecto, validar_pago

def test_pago_debe_usar_moneda_contractual():
    proyecto=SimpleNamespace(moneda_contractual='COP', presupuesto=SimpleNamespace(moneda='USD'))
    assert moneda_proyecto(proyecto)=='COP'
    assert validar_pago(proyecto,'COP')=='COP'
    with pytest.raises(ValueError): validar_pago(proyecto,'USD')
