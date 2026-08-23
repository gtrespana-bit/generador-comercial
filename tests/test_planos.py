from app.services.planos import calcular_valor_real


def test_calcular_valor_lineal_sin_escala():
    puntos = [[0,0],[100,0]]
    valor, unidad = calcular_valor_real("lineal", puntos, None)
    assert valor == 100
    assert unidad == "px"


def test_calcular_valor_lineal_con_escala():
    puntos = [[0,0],[200,0]]
    # 100 px = 1 m
    escala = 100.0
    valor, unidad = calcular_valor_real("lineal", puntos, escala)
    assert abs(valor - 2.0) < 0.01
    assert unidad == "m"


def test_calcular_area():
    puntos = [[0,0],[100,0],[100,100],[0,100]]
    escala = 100.0  # 100 px =1m => 100px=1m => area 1m2
    valor, unidad = calcular_valor_real("area", puntos, escala)
    assert abs(valor - 1.0) < 0.01
    assert unidad == "m2"


def test_calcular_conteo():
    puntos = [[0,0],[10,10],[20,20]]
    valor, unidad = calcular_valor_real("conteo", puntos, 100.0)
    assert valor == 3
    assert unidad == "ud"
