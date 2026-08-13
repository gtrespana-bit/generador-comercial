"""Motor único de cálculos económicos del presupuesto.

Mantiene el comportamiento actual cuando las funciones avanzadas están
apagadas: todas las partidas son incluidas y solo se aplican descuento e IVA.
Los importes se redondean a dos decimales en cada paso comercial para que la
web, el CSV y el PDF compartan exactamente los mismos resultados.
"""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

_CENT = Decimal("0.01")


def D(value) -> Decimal:
    try:
        return Decimal(str(value or 0))
    except Exception:
        return Decimal("0")


def money(value) -> Decimal:
    return D(value).quantize(_CENT, rounding=ROUND_HALF_UP)


def pct(value) -> Decimal:
    return D(value)


@dataclass(frozen=True)
class Totales:
    subtotal: Decimal
    subtotal_opcional: Decimal
    subtotal_alternativas: Decimal
    base_partidas: Decimal
    costes_adicionales: Decimal
    descuento: Decimal
    base: Decimal
    impuesto: Decimal
    total: Decimal
    coste_interno: Decimal
    margen: Decimal
    margen_pct: Decimal
    # Productos comerciales asociados a las partidas (cerámica,
    # calentadores, electrodomésticos...). Se separan para que el margen de
    # la obra no se distorsione con compras de paso para el cliente.
    total_productos: Decimal = Decimal("0")
    coste_productos: Decimal = Decimal("0")
    margen_productos: Decimal = Decimal("0")
    margen_productos_pct: Decimal = Decimal("0")
    subtotal_obra: Decimal = Decimal("0")
    coste_obra: Decimal = Decimal("0")
    margen_obra: Decimal = Decimal("0")
    margen_obra_pct: Decimal = Decimal("0")


def tipo_partida(partida) -> str:
    tipo = (getattr(partida, "tipo_partida", "included") or "included").lower()
    return tipo if tipo in {"included", "optional", "alternative", "excluded", "provisional", "measurement"} else "included"


def partida_activa(partida) -> bool:
    tipo = tipo_partida(partida)
    if tipo == "excluded":
        return False
    if tipo in {"optional", "alternative"}:
        return bool(getattr(partida, "seleccionada", False))
    return True


def tiene_producto(partida) -> bool:
    """Indica si una partida lleva un producto comercial asociado."""
    return bool(
        getattr(partida, "producto_nombre", "")
        or getattr(partida, "producto_imagen", "")
        or getattr(partida, "producto_precio", None) is not None
    )


def importe_producto_partida(partida) -> Decimal:
    """Importe de venta del producto asociado a una partida."""
    cantidad = D(getattr(partida, "cantidad_total", 0))
    precio = D(getattr(partida, "producto_precio", 0))
    return money(cantidad * precio)


def importe_base_partida(partida) -> Decimal:
    """Importe de venta de la partida sin contar el producto asociado."""
    return money(importe_partida(partida) - importe_producto_partida(partida))


def importe_partida(partida) -> Decimal:
    cantidad = D(getattr(partida, "cantidad_total", 0))
    precio = D(getattr(partida, "precio_unitario", 0))
    return money(cantidad * precio)


def coste_producto_partida(partida) -> Decimal:
    """Coste del producto comercial asociado a una partida."""
    cantidad = D(getattr(partida, "cantidad_total", 0))
    coste_unit = D(getattr(partida, "producto_coste", 0))
    return money(cantidad * coste_unit)


def coste_obra_partida(partida) -> Decimal:
    """Coste interno de obra/materiales, sin contar el producto comercial."""
    cantidad = D(getattr(partida, "cantidad_total", 0))
    descompuesto = getattr(partida, "descomposicion_cype", None)
    if descompuesto is not None and getattr(descompuesto, "coste_directo_unitario", None) is not None:
        if getattr(descompuesto, "origen", "") != "manual":
            return money(cantidad * D(descompuesto.coste_directo_unitario))
        desperdicio = pct(getattr(partida, "desperdicio_pct", 0))
        return money(
            cantidad
            * D(descompuesto.coste_directo_unitario)
            * (Decimal("1") + desperdicio / Decimal("100"))
        )
    materiales = D(getattr(partida, "coste_materiales", 0))
    mano_obra = D(getattr(partida, "coste_mano_obra", 0))
    complementarios = D(getattr(partida, "coste_complementarios", 0))
    otros = D(getattr(partida, "coste_otros", 0))
    desperdicio = pct(getattr(partida, "desperdicio_pct", 0))
    subtotal = materiales + mano_obra + complementarios + otros
    return money(cantidad * subtotal * (Decimal("1") + desperdicio / Decimal("100")))


def coste_partida(partida) -> Decimal:
    return money(coste_obra_partida(partida) + coste_producto_partida(partida))


def beneficio_partida(partida) -> Decimal:
    """Beneficio bruto de una partida = importe de venta − coste interno."""
    return money(importe_partida(partida) - coste_partida(partida))


def margen_partida_pct(partida) -> Decimal:
    """Margen de beneficio (%) de una partida sobre su importe de venta."""
    importe = importe_partida(partida)
    if importe <= 0:
        return Decimal("0")
    beneficio = beneficio_partida(partida)
    return (beneficio / importe * Decimal("100")).quantize(_CENT, rounding=ROUND_HALF_UP)


def _pct_sobre_base(beneficio: Decimal, base: Decimal) -> Decimal:
    if base <= 0:
        return Decimal("0")
    return (beneficio / base * Decimal("100")).quantize(_CENT, rounding=ROUND_HALF_UP)


def calcular_totales(presupuesto) -> Totales:
    incluido = Decimal("0")
    opcional = Decimal("0")
    alternativas = Decimal("0")
    coste_interno = Decimal("0")
    total_productos = Decimal("0")
    coste_productos = Decimal("0")
    subtotal_obra = Decimal("0")
    coste_obra = Decimal("0")

    avanzadas = bool(getattr(presupuesto, "usar_funciones_avanzadas", False))
    for partida in presupuesto.todas_partidas:
        importe = importe_partida(partida)
        tipo = tipo_partida(partida) if avanzadas else "included"
        activa = partida_activa(partida) if avanzadas else True
        if tipo == "optional":
            opcional += importe
            if activa:
                incluido += importe
        elif tipo == "alternative":
            alternativas += importe
            if activa:
                incluido += importe
        elif activa:
            incluido += importe
        if activa:
            importe_producto = importe_producto_partida(partida) if tiene_producto(partida) else Decimal("0")
            # Si no se conoce el coste del producto, no se debe presentar su
            # venta entera como beneficio. Se deja coste 0, pero el margen de
            # productos solo será fiable cuando ese coste esté cargado.
            coste_producto = coste_producto_partida(partida) if (tiene_producto(partida) and getattr(partida, "producto_coste", None) is not None) else Decimal("0")
            importe_obra = money(importe - importe_producto)
            coste_obra_partida_total = coste_obra_partida(partida)

            coste_interno += money(coste_obra_partida_total + coste_producto)
            total_productos += importe_producto
            coste_productos += coste_producto
            subtotal_obra += importe_obra
            coste_obra += coste_obra_partida_total

    incluido = money(incluido)
    opcional = money(opcional)
    alternativas = money(alternativas)
    # Los opcionales y alternativas se informan, pero no entran en el total
    # hasta que el usuario los marca como seleccionados.
    base_partidas = money(incluido)
    total_productos = money(total_productos)
    coste_productos = money(coste_productos)
    subtotal_obra = money(subtotal_obra)
    coste_obra = money(coste_obra)

    transporte = money(getattr(presupuesto, "transporte_monto", 0))
    otros = money(getattr(presupuesto, "otros_cargos_monto", 0))
    indirectos = money(base_partidas * pct(getattr(presupuesto, "gastos_indirectos_pct", 0)) / 100)
    imprevistos = money(base_partidas * pct(getattr(presupuesto, "imprevistos_pct", 0)) / 100)
    costes_adicionales = money(transporte + otros + indirectos + imprevistos)

    bruto = money(base_partidas + costes_adicionales)
    descuento = money(bruto * pct(getattr(presupuesto, "descuento_pct", 0)) / 100)
    base = money(bruto - descuento)
    impuesto = money(base * pct(getattr(presupuesto, "impuesto_pct", 0)) / 100)
    total = money(base + impuesto)

    # El descuento comercial se reparte proporcionalmente entre obra y
    # productos para que ambos márgenes reflejen el ingreso neto real.
    if bruto > 0:
        bruto_obra = money(subtotal_obra + costes_adicionales)
        bruto_productos = total_productos
        descuento_obra = money(descuento * bruto_obra / bruto)
        descuento_productos = money(descuento * bruto_productos / bruto)
        # Corrección de céntimo por redondeo para que la suma sea exacta.
        diferencia = money(descuento - descuento_obra - descuento_productos)
        descuento_obra = money(descuento_obra + diferencia)
    else:
        bruto_obra = money(subtotal_obra + costes_adicionales)
        bruto_productos = total_productos
        descuento_obra = descuento
        descuento_productos = Decimal("0")

    base_obra = money(bruto_obra - descuento_obra)
    base_productos = money(bruto_productos - descuento_productos)

    # Beneficio real total = obra + productos cuando se conoce el coste de
    # compra de los productos. El IVA NO es beneficio.
    margen_obra = money(base_obra - coste_obra - costes_adicionales)
    margen_productos = money(base_productos - coste_productos) if coste_productos > 0 else Decimal("0")
    margen = money(margen_obra + margen_productos)

    return Totales(
        subtotal=money(incluido),
        subtotal_opcional=opcional,
        subtotal_alternativas=alternativas,
        base_partidas=base_partidas,
        costes_adicionales=costes_adicionales,
        descuento=descuento,
        base=base,
        impuesto=impuesto,
        total=total,
        coste_interno=money(coste_interno),
        margen=margen,
        margen_pct=_pct_sobre_base(margen, base),
        total_productos=total_productos,
        coste_productos=coste_productos,
        margen_productos=margen_productos,
        margen_productos_pct=_pct_sobre_base(margen_productos, base_productos),
        subtotal_obra=subtotal_obra,
        coste_obra=money(coste_obra),
        margen_obra=margen_obra,
        margen_obra_pct=_pct_sobre_base(margen_obra, base_obra),
    )
