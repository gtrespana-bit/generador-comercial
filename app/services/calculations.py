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
    # Productos cuyo coste de compra está informado (importe de venta) y
    # partidas que venden un producto cuyo coste no consta. Sin esa
    # distinción, la venta del material acababa pareciendo beneficio.
    productos_con_coste: Decimal = Decimal("0")
    productos_sin_coste: int = 0
    coste_productos: Decimal = Decimal("0")
    margen_productos: Decimal = Decimal("0")
    margen_productos_pct: Decimal = Decimal("0")
    subtotal_obra: Decimal = Decimal("0")
    coste_obra: Decimal = Decimal("0")
    margen_obra: Decimal = Decimal("0")
    margen_obra_pct: Decimal = Decimal("0")
    # Reparto del precio que ve el cliente (desglose del PDF): importe de
    # venta de los productos elegidos, ya con el descuento comercial repartido
    # proporcionalmente. La parte de obra se deriva como ``base -
    # base_productos`` para que las dos filas del desglose sumen exactamente la
    # base imponible del documento (el céntimo de redondeo lo absorbe la obra).
    base_productos: Decimal = Decimal("0")
    # Coste de los materiales de obra, separado del resto del coste interno.
    # Solo lo necesita el Reino Unido: la retención del CIS se calcula sobre el
    # elemento de mano de obra, así que hay que poder restar los materiales.
    # En cualquier otro mercado se queda a cero y no se usa.
    coste_materiales: Decimal = Decimal("0")
    # EE. UU.: precio de venta estimado de los materiales dentro de la base
    # (la parte de obra repartida por coste + la venta de productos) y la
    # base que el tipo grava según el modo elegido («solo materiales»,
    # «ingresos brutos al 65 %»…). Fuera del motor estadounidense,
    # ``us_base_gravada`` coincide con la base y nadie la lee.
    venta_materiales: Decimal = Decimal("0")
    us_base_gravada: Decimal = Decimal("0")

    @property
    def coste_productos_incompleto(self) -> bool:
        """Hay productos vendidos cuyo coste de compra no consta.

        El margen de productos que se informe será solo el de los productos
        documentados; quien lo muestre debe decirlo, en vez de presentar un
        cero o un beneficio inflado.
        """
        return self.productos_sin_coste > 0


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


def producto_opcion_elegida(partida):
    """Opción de producto que manda hoy en la partida (o ``None``).

    Mismo criterio que usa el precio y el PDF: primero la opción marcada como
    seleccionada y, si no hay ninguna, la que coincide con el nombre del
    producto primario.
    """
    seleccionada = getattr(partida, "producto_seleccionado", None)
    if seleccionada is not None:
        return seleccionada
    opciones = getattr(partida, "productos_opciones", None) or []
    nombre = (getattr(partida, "producto_nombre", "") or "").strip().lower()
    if nombre:
        for opcion in opciones:
            if (getattr(opcion, "nombre", "") or "").strip().lower() == nombre:
                return opcion
    return None


def producto_coste_unitario(partida) -> Decimal | None:
    """Coste de compra por unidad del producto de la partida, o ``None``.

    Prioridad:

      1) el coste congelado en la propia partida (``producto_coste``);
      2) el de la opción elegida entre las alternativas, que es donde vive el
         coste cuando la partida se montó con varios productos a elegir.

    ``None`` significa «no se conoce», que no es lo mismo que un coste de 0:
    sin este dato no se puede calcular el beneficio del producto y la venta
    entera no debe presentarse como margen.
    """
    if not tiene_producto(partida):
        return None
    propio = getattr(partida, "producto_coste", None)
    if _numero_informado(propio):
        return D(propio)
    opcion = producto_opcion_elegida(partida)
    if opcion is not None:
        coste = getattr(opcion, "coste", None)
        if _numero_informado(coste):
            return D(coste)
    return None


def producto_coste_pendiente(partida) -> bool:
    """¿La partida vende un producto del que no se conoce el coste de compra?

    Es la señal que impide calcular un beneficio falso: si el cliente está
    pagando un material cuyo coste no consta, el importe de ese material no es
    beneficio, es un dato que falta.
    """
    if importe_producto_partida(partida) <= 0:
        return False
    return producto_coste_unitario(partida) is None


def _numero_informado(valor) -> bool:
    """True si el campo trae un número (0 es un dato válido, vacío no)."""
    if valor is None:
        return False
    if isinstance(valor, str):
        return valor.strip() != ""
    return True


def coste_producto_partida(partida) -> Decimal:
    """Coste del producto comercial asociado a una partida.

    Devuelve 0 cuando el coste no se conoce, porque es un sumando del coste
    interno; para distinguir «coste cero» de «coste sin informar» usa
    :func:`producto_coste_unitario` o :func:`producto_coste_pendiente`.
    """
    coste_unit = producto_coste_unitario(partida)
    if coste_unit is None:
        return Decimal("0")
    cantidad = D(getattr(partida, "cantidad_total", 0))
    return money(cantidad * coste_unit)


def _costes_unitarios_campos(partida) -> Decimal:
    materiales = D(getattr(partida, "coste_materiales", 0))
    mano_obra = D(getattr(partida, "coste_mano_obra", 0))
    complementarios = D(getattr(partida, "coste_complementarios", 0))
    otros = D(getattr(partida, "coste_otros", 0))
    return materiales + mano_obra + complementarios + otros


# ---------------------------------------------------------------------------
# Caché del recálculo de descompuestos CYPE
# ---------------------------------------------------------------------------
# ``recalcular_descompuesto_cype`` es una función pura de las filas, pero se
# invoca una vez por partida y otra vez por cada lectura de totales: en un
# presupuesto de 400 partidas con 8 lecturas de totales eran 3 200 llamadas
# (≈1,3 s medidos con cProfile, el mayor coste de CPU del PDF). La clave es el
# contenido de las filas —no la identidad del objeto—, así que una edición
# siempre recalcula y la caché solo ahorra trabajo repetido. El diccionario
# devuelto es de solo lectura para quien lo consume desde aquí.
_CACHE_DESCOMPUESTOS: dict[tuple, dict] = {}
_MAX_CACHE_DESCOMPUESTOS = 256


def _filas_fingerprint(filas) -> tuple:
    return tuple(
        (
            getattr(fila, "tipo", None),
            getattr(fila, "grupo", None),
            getattr(fila, "codigo", None),
            getattr(fila, "unidad", None),
            getattr(fila, "categoria", None),
            getattr(fila, "rendimiento", None),
            getattr(fila, "precio_unitario", None),
        )
        for fila in filas
    )


def recalcular_descompuesto_cacheado(filas) -> dict:
    """Igual que ``importer.recalcular_descompuesto_cype`` pero sin repetir el
    mismo cálculo dentro de la misma generación de documento."""
    clave = _filas_fingerprint(filas)
    resultado = _CACHE_DESCOMPUESTOS.get(clave)
    if resultado is None:
        from .importer import recalcular_descompuesto_cype

        resultado = recalcular_descompuesto_cype(filas)
        if len(_CACHE_DESCOMPUESTOS) >= _MAX_CACHE_DESCOMPUESTOS:
            _CACHE_DESCOMPUESTOS.clear()
        _CACHE_DESCOMPUESTOS[clave] = resultado
    return resultado


def vaciar_cache_descompuestos() -> None:
    """Olvida los recálculos memorizados (pruebas y mantenimiento)."""
    _CACHE_DESCOMPUESTOS.clear()


def coste_obra_partida(partida) -> Decimal:
    """Coste interno de obra/materiales, sin contar el producto comercial.

    Regla de consistencia con el editor: los campos ``coste_materiales``,
    ``coste_mano_obra``, ``coste_complementarios`` y ``coste_otros`` son la
    fuente visible de coste unitario de la partida. En partidas CYPE se usan
    sin desperdicio porque el coste directo ya viene cerrado por la matriz; en
    partidas manuales/simples sí se aplica el desperdicio. Si una partida CYPE
    antigua no tiene esos campos cargados, se usa como respaldo el
    ``coste_directo_unitario`` de la descomposición.
    """
    cantidad = D(getattr(partida, "cantidad_total", 0))
    descompuesto = getattr(partida, "descomposicion_cype", None)
    subtotal_campos = _costes_unitarios_campos(partida)
    desperdicio = pct(getattr(partida, "desperdicio_pct", 0))

    if descompuesto is not None:
        origen = getattr(descompuesto, "origen", "") or ""
        es_cype = origen != "manual" and (
            getattr(descompuesto, "coste_directo_unitario", None) is not None
            or getattr(descompuesto, "archivo_origen", "")
        )

        # Si hay filas, son la fuente autoritativa. Los campos de coste de la
        # partida son una caché para el editor/listados y pueden quedar viejos
        # en presupuestos creados antes de la última mejora. Recalcular aquí
        # evita que el detalle/PDF diga una rentabilidad distinta a la que se
        # ve en el editor al reconstruir la misma descomposición.
        filas = getattr(descompuesto, "filas", None)
        if filas:
            resultado = recalcular_descompuesto_cacheado(filas)
            directo = D(resultado.get("coste_directo", 0))
            if es_cype:
                return money(cantidad * directo)
            return money(cantidad * directo * (Decimal("1") + desperdicio / Decimal("100")))

        if es_cype:
            if subtotal_campos > 0:
                return money(cantidad * subtotal_campos)
            if getattr(descompuesto, "coste_directo_unitario", None) is not None:
                return money(cantidad * D(descompuesto.coste_directo_unitario))
        else:
            directo = D(descompuesto.coste_directo_unitario) if getattr(descompuesto, "coste_directo_unitario", None) is not None else subtotal_campos
            return money(cantidad * directo * (Decimal("1") + desperdicio / Decimal("100")))

    return money(cantidad * subtotal_campos * (Decimal("1") + desperdicio / Decimal("100")))


def costes_obra_partida(partida) -> dict[str, Decimal]:
    """Reparto del coste de obra de una partida por categoría CYPE.

    Es ``coste_obra_partida`` sin sumar: devuelve el mismo importe total, pero
    separado en ``materiales``, ``mano_obra``, ``complementarios`` y ``otros``.
    Existe porque la retención británica del CIS no se calcula sobre la factura,
    sino sobre el elemento de mano de obra: sin este reparto habría que aplicar
    la retención sobre el importe íntegro y se retendría de más al
    subcontratista, que es exactamente el error que Hacienda persigue.

    Sigue las mismas reglas que ``coste_obra_partida`` (filas autoritativas,
    desperdicio solo en partidas no CYPE) para que la suma de las cuatro
    categorías coincida con el coste que ya se mostraba.

    Cuando una partida no trae desglose —CYPE antigua sin filas y sin campos
    de coste, o una partida simple— el coste conocido se imputa a ``otros``,
    nunca a ``materiales``. Imputarlo a materiales lo excluiría de la retención
    y dejaría al contratista con una retención insuficiente, que es la que
    Hacienda le reclama a él.
    """
    cantidad = D(getattr(partida, "cantidad_total", 0))
    descompuesto = getattr(partida, "descomposicion_cype", None)
    desperdicio = pct(getattr(partida, "desperdicio_pct", 0))
    factor = Decimal("1") + desperdicio / Decimal("100")
    # Import diferido: ``importer`` depende de este módulo y la importación en
    # cabecera cerraría un ciclo.
    from .importer import COSTES_CYPE

    vacio = {categoria: Decimal("0") for categoria in COSTES_CYPE}

    def _desde_campos(con_factor: bool) -> dict[str, Decimal]:
        salida = dict(vacio)
        for categoria in COSTES_CYPE:
            unitario = D(getattr(partida, f"coste_{categoria}", 0))
            salida[categoria] = money(cantidad * unitario * (factor if con_factor else Decimal("1")))
        return salida

    if descompuesto is not None:
        origen = getattr(descompuesto, "origen", "") or ""
        es_cype = origen != "manual" and (
            getattr(descompuesto, "coste_directo_unitario", None) is not None
            or getattr(descompuesto, "archivo_origen", "")
        )
        filas = getattr(descompuesto, "filas", None)

        if filas:
            resultado = recalcular_descompuesto_cacheado(filas)
            costes = resultado.get("costes") or {}
            return {
                categoria: money(cantidad * D(costes.get(categoria, 0)) * (Decimal("1") if es_cype else factor))
                for categoria in COSTES_CYPE
            }

        if es_cype:
            if _costes_unitarios_campos(partida) > 0:
                return _desde_campos(con_factor=False)
            directo = getattr(descompuesto, "coste_directo_unitario", None)
            if directo is not None:
                salida = dict(vacio)
                salida["otros"] = money(cantidad * D(directo))
                return salida

    if _costes_unitarios_campos(partida) > 0:
        return _desde_campos(con_factor=True)
    return dict(vacio)


def coste_partida(partida) -> Decimal:
    """Coste interno de la partida: obra y recursos + producto (si consta)."""
    return money(coste_obra_partida(partida) + coste_producto_partida(partida))


def beneficio_partida(partida) -> Decimal:
    """Beneficio bruto de una partida, sin contar lo que no se conoce.

    Con el coste del producto informado es «venta − coste». Si la partida
    vende un producto sin coste de compra, su importe **no** se cuenta como
    beneficio: se devuelve el margen de la parte documentada (obra y recursos)
    y ``producto_coste_pendiente`` queda marcado para que la ficha lo explique.
    Presentar la venta íntegra del material como margen daría cifras absurdas
    (miles por ciento sobre coste).
    """
    if producto_coste_pendiente(partida):
        return money(importe_base_partida(partida) - coste_obra_partida(partida))
    return money(importe_partida(partida) - coste_partida(partida))


def margen_partida_pct(partida) -> Decimal:
    """Margen de beneficio (%) de una partida sobre la venta que se compara.

    Con productos sin coste informado el porcentaje se calcula sobre la parte
    documentada (la base de obra), para que no mezcle material del que no se
    sabe el coste.
    """
    importe = (
        importe_base_partida(partida) if producto_coste_pendiente(partida)
        else importe_partida(partida)
    )
    if importe <= 0:
        return Decimal("0")
    beneficio = beneficio_partida(partida)
    return (beneficio / importe * Decimal("100")).quantize(_CENT, rounding=ROUND_HALF_UP)


def _pct_sobre_base(beneficio: Decimal, base: Decimal) -> Decimal:
    if base <= 0:
        return Decimal("0")
    return (beneficio / base * Decimal("100")).quantize(_CENT, rounding=ROUND_HALF_UP)


def calcular_totales(presupuesto, con_costes_categoria: bool = False) -> Totales:
    """Totales del presupuesto.

    ``con_costes_categoria`` añade el reparto del coste por categoría CYPE,
    que hoy solo necesita el Reino Unido para la retención del CIS. Se deja
    apagado por defecto porque recorre las descomposiciones por segunda vez y
    el PDF ya es el camino más pesado de la aplicación.

    Excepción: el motor estadounidense en modo «solo materiales» o «solo
    mano de obra» fuerza esa pasada él mismo, porque de ella depende el
    propio impuesto (no un dato informativo): quien llame sin pedirla
    —p. ej. al congelar ``total_calculado``— seguiría obteniendo la
    cifra correcta.
    """
    modo_us = str(getattr(presupuesto, "us_tax_base", "") or "").strip()
    necesita_categoria = con_costes_categoria or modo_us in ("materials", "labor")
    incluido = Decimal("0")
    opcional = Decimal("0")
    alternativas = Decimal("0")
    coste_interno = Decimal("0")
    total_productos = Decimal("0")
    productos_con_coste = Decimal("0")
    coste_productos = Decimal("0")
    productos_sin_coste = 0
    subtotal_obra = Decimal("0")
    coste_obra = Decimal("0")
    coste_materiales = Decimal("0")

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
            # El coste de compra puede vivir en la partida o en la opción de
            # producto elegida. Cuando no consta en ninguno de los dos sitios
            # no se inventa nada: la venta del producto no se suma como
            # beneficio y la partida queda contada aparte para poder avisar.
            coste_unitario_producto = producto_coste_unitario(partida) if tiene_producto(partida) else None
            if importe_producto > 0 and coste_unitario_producto is None:
                productos_sin_coste += 1
            elif coste_unitario_producto is not None:
                productos_con_coste += importe_producto
            coste_producto = (
                money(D(getattr(partida, "cantidad_total", 0)) * coste_unitario_producto)
                if coste_unitario_producto is not None else Decimal("0")
            )
            importe_obra = money(importe - importe_producto)
            coste_obra_partida_total = coste_obra_partida(partida)

            if necesita_categoria:
                coste_materiales += costes_obra_partida(partida)["materiales"]
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
    productos_con_coste = money(productos_con_coste)
    coste_productos = money(coste_productos)
    subtotal_obra = money(subtotal_obra)
    coste_obra = money(coste_obra)
    coste_materiales = money(coste_materiales)

    transporte = money(getattr(presupuesto, "transporte_monto", 0))
    otros = money(getattr(presupuesto, "otros_cargos_monto", 0))
    indirectos = money(base_partidas * pct(getattr(presupuesto, "gastos_indirectos_pct", 0)) / 100)
    imprevistos = money(base_partidas * pct(getattr(presupuesto, "imprevistos_pct", 0)) / 100)
    costes_adicionales = money(transporte + otros + indirectos + imprevistos)

    bruto = money(base_partidas + costes_adicionales)
    descuento = money(bruto * pct(getattr(presupuesto, "descuento_pct", 0)) / 100)
    base = money(bruto - descuento)

    # El descuento comercial se reparte proporcionalmente entre obra y
    # productos para que ambos márgenes reflejen el ingreso neto real.
    # (Se calcula antes del impuesto porque el motor estadounidense
    # necesita la base de obra y la de productos por separado para
    # estimar el precio de venta de los materiales; el reparto no
    # depende del impuesto, así que el resto de mercados no cambia.)
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

    # Impuesto. Con el motor estadounidense activo (modo elegido en el
    # documento) el tipo no cae sobre la base completa sino sobre la que
    # el estado grava: nada en los estados «contratista consumidor»,
    # solo materiales, solo mano de obra, o una fracción de los ingresos
    # brutos. Sin modo —todos los demás mercados y los documentos
    # anteriores— el cálculo es el de siempre.
    tipo_impuesto = pct(getattr(presupuesto, "impuesto_pct", 0))
    if modo_us in ("none", "materials", "labor", "full", "gross_receipts"):
        from .fiscalidad_eeuu import base_gravada_eeuu, estimar_venta_materiales

        venta_materiales = estimar_venta_materiales(
            base_obra, base_productos, coste_materiales, coste_obra
        )
        us_base_gravada = base_gravada_eeuu(
            modo_us, base, venta_materiales,
            getattr(presupuesto, "us_tax_fraccion", 1.0),
        )
        impuesto = money(us_base_gravada * tipo_impuesto / 100)
    else:
        venta_materiales = Decimal("0")
        us_base_gravada = base
        impuesto = money(base * tipo_impuesto / 100)
    total = money(base + impuesto)

    # Los productos cuyo coste de compra NO consta quedan fuera del margen:
    # su venta no es beneficio (es un dato que falta) y tampoco se puede
    # decir que su margen sea 0. El margen de productos se calcula, pues,
    # sobre los productos cuyo coste sí se conoce, con su parte proporcional
    # del descuento comercial; ``productos_sin_coste`` avisa de los pendientes.
    if bruto > 0:
        descuento_productos_con_coste = money(descuento * productos_con_coste / bruto)
    else:
        descuento_productos_con_coste = Decimal("0")
    base_productos_con_coste = money(productos_con_coste - descuento_productos_con_coste)

    # Beneficio real total = obra + productos documentados. El IVA NO es
    # beneficio: es un impuesto que se recauda y se entrega.
    margen_obra = money(base_obra - coste_obra - costes_adicionales)
    margen_productos = money(base_productos_con_coste - coste_productos)
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
        productos_con_coste=productos_con_coste,
        productos_sin_coste=productos_sin_coste,
        coste_productos=coste_productos,
        margen_productos=margen_productos,
        margen_productos_pct=_pct_sobre_base(margen_productos, base_productos_con_coste),
        subtotal_obra=subtotal_obra,
        coste_obra=money(coste_obra),
        margen_obra=margen_obra,
        margen_obra_pct=_pct_sobre_base(margen_obra, base_obra),
        base_productos=base_productos,
        coste_materiales=coste_materiales,
        venta_materiales=venta_materiales,
        us_base_gravada=us_base_gravada,
    )
