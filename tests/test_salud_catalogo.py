from datetime import datetime, timedelta
from types import SimpleNamespace

from app.services.salud_catalogo import analizar_salud_catalogo


class _Query:
    def __init__(self, items):
        self.items = items
    def filter(self, *args, **kwargs):
        return self
    def all(self):
        return self.items


class _DB:
    def __init__(self, items):
        self.items = items
    def query(self, model):
        return _Query(self.items)


def _p(precio=100, coste=60, tiempo=1, dias=0):
    return SimpleNamespace(
        precio_unitario=precio,
        coste_materiales=coste,
        coste_mano_obra=0,
        coste_complementarios=0,
        coste_otros=0,
        tiempo_estimado_horas=tiempo,
        tiempo_oficial_horas=None,
        tiempo_ayudante_horas=None,
        tiempo_equipo_horas=None,
        fecha_actualizacion_precio=datetime.utcnow() - timedelta(days=dias),
        created_at=datetime.utcnow(),
        oculta=False,
    )


def test_salud_catalogo_sano():
    res = analizar_salud_catalogo(_DB([_p(), _p(precio=200, coste=120, tiempo=2)]))
    assert res["estado"] == "ok"
    assert res["score"] == 100
    assert res["sin_precio"] == 0
    assert res["sin_coste"] == 0
    assert res["sin_tiempo"] == 0


def test_salud_catalogo_detecta_problemas_accionables():
    res = analizar_salud_catalogo(_DB([
        _p(precio=0, coste=0, tiempo=0, dias=120),
        _p(precio=100, coste=95, tiempo=0),
    ]))
    claves = {p["clave"] for p in res["problemas_visibles"]}
    assert res["estado"] in {"riesgo", "revisar"}
    assert {"sin_precio", "sin_coste", "sin_tiempo", "margen_bajo", "desactualizadas"}.issubset(claves)
    assert res["sin_tiempo"] == 2
    assert res["margen_bajo"] == 1
