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


def test_salud_catalogo_agrega_en_sql_sin_cargar_todas_las_partidas(entorno):
    from sqlalchemy import event

    from app.models import Partida
    from app.services.salud_catalogo import _metricas_python, _metricas_sql

    Session, ids, _ = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        ahora = datetime.utcnow()
        db.add_all([
            _p_model(
                organizacion_id=ids[0], nombre="Sin precio ni coste",
                precio_unitario=0, coste_materiales=0,
                fecha_actualizacion_precio=ahora - timedelta(days=120),
                created_at=ahora,
            ),
            _p_model(
                organizacion_id=ids[0], nombre="Margen estrecho",
                precio_unitario=100, coste_materiales=95,
                fecha_actualizacion_precio=ahora,
                tiempo_estimado_horas=0,
            ),
        ])
        db.commit()

        # La agregación SQL conserva exactamente las métricas del algoritmo
        # Python de referencia, pero devuelve una única fila a la aplicación.
        assert _metricas_sql(db) == _metricas_python(db)
        select_count = 0
        bind = db.get_bind()

        def contar_select(_conn, _cursor, statement, _parameters, _context, _executemany):
            nonlocal select_count
            if statement.lstrip().upper().startswith("SELECT"):
                select_count += 1

        event.listen(bind, "before_cursor_execute", contar_select)
        try:
            resultado = analizar_salud_catalogo(db, incluir_anomalias=False)
        finally:
            event.remove(bind, "before_cursor_execute", contar_select)

        assert select_count == 1
        assert resultado["total"] == 3  # incluye la partida base de la fixture
        assert resultado["sin_precio"] == 1
        assert resultado["sin_coste"] == 2
        assert resultado["sin_tiempo"] == 3
        assert resultado["margen_bajo"] == 1
        assert resultado["desactualizadas"] == 1


def test_configuracion_se_reutiliza_durante_una_sesion(entorno):
    from sqlalchemy import event

    from app.routers.common import _config

    Session, ids, _ = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        bind = db.get_bind()
        selects_config = 0

        def contar_select(_conn, _cursor, statement, _parameters, _context, _executemany):
            nonlocal selects_config
            sql = statement.lower()
            if sql.lstrip().startswith("select") and "from configuracion" in sql:
                selects_config += 1

        event.listen(bind, "before_cursor_execute", contar_select)
        try:
            primera = _config(db)
            segunda = _config(db)
        finally:
            event.remove(bind, "before_cursor_execute", contar_select)

        assert primera is segunda
        assert selects_config == 1


def _p_model(**valores):
    """Construye filas ORM manteniendo compactos los casos del agregado SQL."""
    from app.models import Partida

    valores.setdefault("unidad", "ud")
    valores.setdefault("categoria", "Pruebas")
    valores.setdefault("oculta", False)
    valores.setdefault("coste_mano_obra", 0)
    valores.setdefault("coste_complementarios", 0)
    valores.setdefault("coste_otros", 0)
    valores.setdefault("created_at", datetime.utcnow())
    return Partida(**valores)
