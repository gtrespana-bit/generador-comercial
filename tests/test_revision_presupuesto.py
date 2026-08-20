from datetime import date
from types import SimpleNamespace

from app.services.revision_presupuesto import revisar_presupuesto_antes_de_enviar


def _cliente(email="cliente@example.com", telefono=""):
    return SimpleNamespace(id=1, nombre="Cliente", email=email, telefono=telefono)


def _partida(nombre="Partida", precio=100, cantidad=2, costes=True, margen=35):
    return SimpleNamespace(
        nombre=nombre,
        precio_unitario=precio,
        cantidad_total=cantidad,
        tipo_partida="included",
        seleccionada=True,
        tiene_costes=costes,
        margen_beneficio_pct=margen,
    )


def _presupuesto(partidas, **kw):
    return SimpleNamespace(
        id=1,
        cliente=kw.get("cliente", _cliente()),
        capitulos=[SimpleNamespace(partidas=partidas)],
        todas_partidas=partidas,
        fecha=kw.get("fecha", date.today()),
        validez_dias=kw.get("validez_dias", 30),
        moneda=kw.get("moneda", "USD"),
        margen_pct=kw.get("margen_pct", 30),
        versiones=kw.get("versiones", [SimpleNamespace(numero_version=1)]),
    )


def _cfg(logo="logo.png"):
    return SimpleNamespace(logo=logo)


def test_revision_lista_presupuesto_sano():
    p = _presupuesto([_partida()])
    tiempos = {"n_partidas_activas": 1, "n_con_datos": 1, "total_dias_duracion": 3.5}
    rev = revisar_presupuesto_antes_de_enviar(p, cfg=_cfg(), tiempos=tiempos)
    assert rev["estado"] == "listo"
    assert rev["puede_enviar"] is True
    assert not rev["criticos"]
    assert rev["score"] == 100


def test_revision_detecta_criticos_y_avisos_accionables():
    p = _presupuesto(
        [_partida(nombre="Sin precio", precio=0, cantidad=0, costes=False)],
        cliente=_cliente(email="", telefono=""),
        versiones=[],
        margen_pct=0,
    )
    tiempos = {"n_partidas_activas": 1, "n_con_datos": 0, "total_dias_duracion": 0}
    rev = revisar_presupuesto_antes_de_enviar(p, cfg=_cfg(logo=""), tiempos=tiempos)
    claves_criticas = {i["clave"] for i in rev["criticos"]}
    claves_aviso = {i["clave"] for i in rev["recomendaciones"]}
    assert rev["estado"] == "riesgo"
    assert rev["puede_enviar"] is False
    assert {"precios", "cantidades", "costes"}.issubset(claves_criticas)
    assert {"contacto", "tiempos", "logo", "version"}.issubset(claves_aviso)
    assert rev["url_principal"]
