from types import SimpleNamespace

from app.services.calculations import (
    D,
    beneficio_partida,
    calcular_totales,
    coste_partida,
    margen_partida_pct,
    producto_coste_pendiente,
)


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


def test_producto_sin_coste_no_infla_el_beneficio_de_la_partida():
    """Una partida que vende material sin coste informado no es «todo margen».

    Caso real (presupuesto 47, partida 1276): 100 m2 a 26,50 con 0,70 de coste
    de ejecución y un porcelanato de 25,50/m2 sin coste de compra. Antes el
    beneficio salía 2.580 USD (3.685 % s/coste) porque el material entero
    contaba como margen; ahora el beneficio es el de la parte documentada y la
    partida queda marcada como «producto sin coste».
    """
    partida = _partida(
        cantidad_total=100, precio_unitario=26.5,
        coste_materiales=0.7, coste_mano_obra=0,
        producto_nombre="Porcelanato Venetian Grey", producto_precio=25.5,
    )

    assert producto_coste_pendiente(partida) is True
    assert coste_partida(partida) == D("70")          # solo la parte de obra
    assert beneficio_partida(partida) == D("30")      # 100 × 0,30 documentados
    assert margen_partida_pct(partida) == D("30.00")  # 30 / 100 de base

    totales = calcular_totales(_presupuesto([partida]))

    assert totales.total_productos == D("2550")
    assert totales.coste_productos == D("0")
    assert totales.productos_sin_coste == 1
    assert totales.coste_productos_incompleto is True
    # El material sin coste no aporta margen: el beneficio es el de la obra.
    assert totales.margen_productos == D("0")
    assert totales.margen == totales.margen_obra == D("30")


def test_el_coste_de_la_opcion_elegida_cuenta_para_el_beneficio():
    """El coste puede vivir en la alternativa elegida, no en el primario."""
    elegida = SimpleNamespace(nombre="Porcelanato Gris", precio=25.5, coste=20.0,
                              seleccionado=True)
    descartada = SimpleNamespace(nombre="Porcelanato Blanco", precio=28.0, coste=23.0,
                                 seleccionado=False)
    partida = _partida(
        cantidad_total=100, precio_unitario=26.5, coste_materiales=0.7,
        producto_nombre="Porcelanato Gris", producto_precio=25.5,
        productos_opciones=[elegida, descartada],
    )

    assert producto_coste_pendiente(partida) is False
    assert coste_partida(partida) == D("2070")  # 70 de obra + 2.000 de material

    totales = calcular_totales(_presupuesto([partida]))
    assert totales.productos_sin_coste == 0
    assert totales.coste_productos == D("2000")
    assert totales.margen_productos == D("550")  # 2.550 − 2.000


def test_el_margen_de_productos_se_calcula_sobre_los_productos_documentados():
    """Con dos productos, uno documentado y otro no, el margen es el del primero."""
    documentado = _partida(
        cantidad_total=10, precio_unitario=100, coste_mano_obra=20,
        producto_nombre="Calentador", producto_precio=50, producto_coste=40,
    )
    sin_coste = _partida(
        cantidad_total=10, precio_unitario=30,
        producto_nombre="Grifería", producto_precio=30,
    )

    totales = calcular_totales(_presupuesto([documentado, sin_coste]))

    assert totales.productos_sin_coste == 1
    assert totales.total_productos == D("800")        # 500 + 300
    assert totales.productos_con_coste == D("500")    # solo el documentado
    assert totales.coste_productos == D("400")
    # Beneficio del producto documentado: 500 − 400 = 100.
    assert totales.margen_productos == D("100")
    assert totales.margen_productos_pct == D("20.00")
