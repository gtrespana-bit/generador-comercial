from types import SimpleNamespace

from app.services.calculations import D, calcular_totales


def _partida(**kwargs):
    datos = {
        "cantidad_total": 1,
        "precio_unitario": 0,
        "producto_nombre": "",
        "producto_precio": None,
        "producto_coste": None,
        "producto_imagen": "",
        "coste_materiales": 0,
        "coste_mano_obra": 0,
        "coste_complementarios": 0,
        "coste_otros": 0,
        "desperdicio_pct": 0,
        "descomposicion_cype": None,
        "tipo_partida": "included",
        "seleccionada": False,
    }
    datos.update(kwargs)
    return SimpleNamespace(**datos)


def _presupuesto(partidas, **kwargs):
    datos = {
        "usar_funciones_avanzadas": True,
        "transporte_monto": 0,
        "otros_cargos_monto": 0,
        "gastos_indirectos_pct": 0,
        "imprevistos_pct": 0,
        "descuento_pct": 0,
        "impuesto_pct": 0,
    }
    datos.update(kwargs)
    return SimpleNamespace(todas_partidas=partidas, **datos)


def test_separa_total_productos_y_beneficio_de_obra():
    presupuesto = _presupuesto([
        # Instalación/mano de obra + producto de paso
        _partida(precio_unitario=1300, coste_materiales=100, coste_mano_obra=100,
                 producto_nombre="Calentador", producto_precio=1000, producto_coste=950),
        # Partida solo de obra
        _partida(precio_unitario=300, coste_materiales=100, coste_mano_obra=80),
    ])

    totales = calcular_totales(presupuesto)

    assert totales.total_productos == D("1000")
    assert totales.subtotal_obra == D("600")
    assert totales.coste_obra == D("380")
    assert totales.coste_productos == D("950")
    assert totales.margen_obra == D("220")
    assert totales.margen_obra_pct == D("36.67")
    assert totales.margen_productos == D("50")
    assert totales.margen_productos_pct == D("5.00")
    assert totales.margen == D("270")
    assert totales.margen_pct == D("16.88")


def test_producto_sin_coste_no_se_computa_como_beneficio():
    presupuesto = _presupuesto([
        _partida(precio_unitario=1000, coste_mano_obra=100,
                 producto_nombre="Cerámica", producto_precio=900),
    ])

    totales = calcular_totales(presupuesto)

    assert totales.total_productos == D("900")
    assert totales.subtotal_obra == D("100")
    assert totales.coste_productos == D("0")
    assert totales.margen_productos == D("0")
    assert totales.margen_productos_pct == D("0")
    assert totales.margen_obra == D("0")
    assert totales.margen == D("0")


def test_descuento_se_reparte_entre_obra_y_productos():
    presupuesto = _presupuesto([
        _partida(precio_unitario=200, coste_materiales=80,
                 producto_nombre="Accesorio", producto_precio=100, producto_coste=90),
    ], descuento_pct=10)

    totales = calcular_totales(presupuesto)

    assert totales.descuento == D("20")
    # Sin costes adicionales: bruto obra=100, bruto productos=100. El descuento
    # de 20 se reparte al 50% entre ambos tramos.
    assert totales.margen_obra == D("10")  # 100 - 80 - 10
    assert totales.margen_productos == D("0")  # 100 - 90 - 10
    assert totales.margen == D("10")


def test_cype_usa_campos_de_coste_visibles_sin_desperdicio():
    descomp = SimpleNamespace(origen="cype", archivo_origen="origen.xlsx", coste_directo_unitario=999)
    presupuesto = _presupuesto([
        _partida(
            cantidad_total=2,
            precio_unitario=180,
            coste_materiales=40,
            coste_mano_obra=30,
            coste_complementarios=10,
            coste_otros=5,
            desperdicio_pct=25,
            descomposicion_cype=descomp,
        ),
    ])

    totales = calcular_totales(presupuesto)

    # El editor muestra 40+30+10+5 = 85/ud y no aplica desperdicio a CYPE.
    # El detalle debe usar la misma fuente visible, no el coste_directo antiguo.
    assert totales.coste_obra == D("170")
    assert totales.margen == D("190")


def test_cype_antiguo_sin_campos_usa_coste_directo_como_respaldo():
    descomp = SimpleNamespace(origen="cype", archivo_origen="origen.xlsx", coste_directo_unitario=85)
    presupuesto = _presupuesto([
        _partida(cantidad_total=2, precio_unitario=180, descomposicion_cype=descomp),
    ])

    totales = calcular_totales(presupuesto)

    assert totales.coste_obra == D("170")
    assert totales.margen == D("190")


def _fila_descomp(**kwargs):
    datos = {
        "tipo": "recurso",
        "grupo": "MATERIALES",
        "codigo": "mt001",
        "unidad": "ud",
        "categoria": "materiales",
        "rendimiento": 1,
        "precio_unitario": 0,
    }
    datos.update(kwargs)
    return SimpleNamespace(**datos)


def test_descomposicion_con_filas_manda_sobre_campos_cache_stale():
    descomp = SimpleNamespace(
        origen="cype",
        archivo_origen="origen.xlsx",
        coste_directo_unitario=999,
        filas=[_fila_descomp(precio_unitario=85)],
    )
    presupuesto = _presupuesto([
        _partida(
            cantidad_total=2,
            precio_unitario=180,
            # Caché vieja: debe ignorarse porque las filas recalculan 85/ud.
            coste_materiales=999,
            descomposicion_cype=descomp,
        ),
    ])

    totales = calcular_totales(presupuesto)

    assert totales.coste_obra == D("170")
    assert totales.margen == D("190")
