"""Unidades de los precios de referencia y conversión entre sistemas.

Por qué existe
--------------
El catálogo de recursos está en métrico: ``h``, ``ud``, ``kg``, ``l``, ``m``,
``m2``, ``m3``. Eso vale para 22 de los 23 mercados. Estados Unidos es el único
que mide en imperial y, por tanto, el único cuyos precios de referencia llegan
en libras, galones, pies y yardas.

Sin este módulo, una matriz de precios estadounidense no se puede importar: el
importador compara la unidad de la fila con la del recurso y rechaza la fila.
Rechazar es lo correcto —meter 40 dólares «el pie cuadrado» en un recurso que
cuenta metros cuadrados daría un precio nueve veces por debajo del real—, pero
deja al mercado estadounidense sin matriz posible.

Lo que hace
-----------
Convierte el PRECIO, no la cantidad. Pasar de «12,50 $/ft²» a «$/m²» no es
multiplicar por 0,0929 sino dividir por él: un metro cuadrado tiene 10,76 pies
cuadrados, así que el precio por metro es 10,76 veces el precio por pie. Los
factores de abajo son los de multiplicar, ya con esa división hecha.

El galón es el caso delicado: el galón estadounidense (3,785 l) y el imperial
británico (4,546 l) no son lo mismo y se escriben igual. Aquí ``gal`` es el
estadounidense porque la conversión solo se aplica a Estados Unidos; el mercado
británico es métrico y nunca pasa por aquí.
"""

from __future__ import annotations

# Alias de escritura -> unidad canónica. Recoge tanto las abreviaturas del
# propio catálogo como las formas en que se escriben las unidades imperiales en
# las tarifas de proveedores.
_ALIAS: dict[str, str] = {
    # Catálogo (misma tabla que usaba el importador).
    "h": "hora", "hr": "hora", "hora": "hora", "horas": "hora",
    "m²": "m2", "m2": "m2",
    "m³": "m3", "m3": "m3",
    "u": "ud", "ud": "ud", "und": "ud", "unidad": "ud", "unidades": "ud",
    "kg": "kg", "l": "l", "m": "m",
    # Imperial (Estados Unidos).
    "lb": "lb", "lbs": "lb", "libra": "lb", "libras": "lb",
    "oz": "oz", "onza": "oz", "onzas": "oz",
    "gal": "gal", "galon": "gal", "galones": "gal", "galón": "gal",
    "ft": "ft", "pie": "ft", "pies": "ft",
    "ft2": "ft2", "sqft": "ft2", "pie2": "ft2", "pies2": "ft2",
    "ft3": "ft3", "cuft": "ft3", "pie3": "ft3", "pies3": "ft3",
    "yd": "yd", "yarda": "yd", "yardas": "yd",
    "yd2": "yd2", "sqyd": "yd2", "yarda2": "yd2",
    "yd3": "yd3", "cuyd": "yd3", "yarda3": "yd3",
    "in": "in", "pulg": "in", "pulgada": "in", "pulgadas": "in",
    "ton": "ton", "tonelada": "ton",
}

#: Factor para pasar el precio de la unidad imperial a la métrica equivalente:
#: ``precio_metrico = precio_imperial * factor``.
_CONVERSION: dict[tuple[str, str], float] = {
    # Masa
    ("lb", "kg"): 2.204622622,      # 1 kg = 2,2046226 lb
    ("oz", "kg"): 35.27396195,      # 1 kg = 35,2739619 oz
    ("ton", "kg"): 0.00110231131,   # 1 short ton (2.000 lb) = 907,18474 kg
    # Volumen
    ("gal", "l"): 0.2641720524,     # 1 gal US = 3,785411784 l
    # Longitud
    ("in", "m"): 39.37007874,       # 1 m = 39,3700787 in
    ("ft", "m"): 3.280839895,       # 1 m = 3,2808399 ft
    ("yd", "m"): 1.093613298,       # 1 m = 1,0936133 yd
    # Superficie
    ("ft2", "m2"): 10.76391042,     # 1 m² = 10,7639104 ft²
    ("yd2", "m2"): 1.195990046,     # 1 m² = 1,1959900 yd²
    # Volumen de obra
    ("ft3", "m3"): 35.31466672,     # 1 m³ = 35,3146667 ft³
    ("yd3", "m3"): 1.307950619,     # 1 m³ = 1,3079506 yd³
}


def normalizar_unidad(valor: str | None) -> str:
    """Forma canónica de una unidad, o cadena vacía si no llega nada."""
    texto = str(valor or "").strip()
    if not texto:
        return ""
    return _ALIAS.get(texto, _ALIAS.get(texto.lower(), texto))


def convertir_precio_unidad(
    precio: float, unidad_origen: str | None, unidad_destino: str | None
) -> float | None:
    """Pasa un precio unitario de una unidad a otra.

    Devuelve ``None`` cuando no hay conversión posible, que NO es lo mismo que
    devolver el precio sin tocar: si las unidades son incompatibles y se
    devolviera el importe original, se guardaría un precio correcto en apariencia
    y nueve veces equivocado en la realidad.

    Si las unidades ya coinciden, el precio vuelve intacto.
    """
    origen = normalizar_unidad(unidad_origen)
    destino = normalizar_unidad(unidad_destino)
    if not origen or not destino:
        return None
    if origen == destino:
        return float(precio)
    factor = _CONVERSION.get((origen, destino))
    if factor is None:
        return None
    try:
        return float(precio) * factor
    except (TypeError, ValueError):
        return None


def sistema_unidades_pais(codigo_pais: str | None) -> str:
    """Sistema de medida de un mercado: ``metrico`` o ``imperial``.

    Se apoya en ``app.paises`` para que añadir un mercado nuevo no obligue a
    acordarse de mantener una lista paralela aquí.
    """
    try:
        from ..paises import PAISES

        pais = PAISES.get(str(codigo_pais or "").strip().upper())
        sistema = (pais or {}).get("sistema_unidades") or "metrico"
    except Exception:
        return "metrico"
    return "imperial" if sistema == "imperial" else "metrico"


# ─────────────────────────────────────────────────────────────────────────────
# Capa de documento imperial (EE. UU., Fase 1)
#
# El almacenamiento es siempre métrico: partidas, mediciones, descompuestos y
# catálogo guardan m, m2, m3, kg y l. Lo que cambia en un mercado imperial es
# la SUPERFICIE: el editor, la ficha en pantalla, el PDF y las exportaciones
# enseñan ft, sq ft, cu yd, lb y gal, con la cantidad multiplicada por el
# factor y el precio unitario dividido por él, de modo que el importe de cada
# línea es idéntico en los dos sistemas.
#
# La pieza que hace seguro el viaje de ida y vuelta es que la propia unidad
# es la marca: un payload que llega del editor con unidad «sq ft» trae sus
# cantidades en pies cuadrados por definición, así que al guardar se
# normaliza a m2 sin necesitar banderas en el formulario, en el borrador del
# autoguardado ni en los packs. Una unidad no convertible (ud, glb, h, %, una
# libre del usuario) no se toca jamás.
# ─────────────────────────────────────────────────────────────────────────────

#: Unidad que ve el cliente imperial por cada unidad métrica del catálogo.
UNIDAD_MOSTRADA: dict[str, str] = {
    "m": "ft",
    "m2": "sq ft",
    "m3": "cu yd",
    "kg": "lb",
    "l": "gal",
}

#: cantidad_mostrada = cantidad_metrica * factor. Son los mismos números de
#: ``_CONVERSION``: si 1 m² = 10,7639 ft², el precio $/m² es 10,7639 veces el
#: precio $/ft² y la cantidad en ft² es 10,7639 veces la cantidad en m².
_FACTOR_CANTIDAD: dict[str, float] = {
    "m": _CONVERSION[("ft", "m")],
    "m2": _CONVERSION[("ft2", "m2")],
    "m3": _CONVERSION[("yd3", "m3")],
    "kg": _CONVERSION[("lb", "kg")],
    "l": _CONVERSION[("gal", "l")],
}

#: Unidad imperial canónica -> (unidad métrica, factor de cantidad). Se
#: construye invirtiendo ``_CONVERSION`` para no mantener dos tablas: toda
#: unidad imperial que el importador sabe convertir a precio métrico se sabe
#: también normalizar al guardar un documento (ft3, yd, oz… aunque la
#: superficie solo MUESTRE ft, sq ft, cu yd, lb y gal).
_DESDE_MOSTRADA: dict[str, tuple[str, float]] = {
    imperial: (metrica, factor)
    for (imperial, metrica), factor in _CONVERSION.items()
}

# Sinónimos métricos que el selector de unidades ofrece pero que _ALIAS no
# recoge (el «ml» de metro lineal es el caso real del datalist del editor).
_SINONIMOS_METRICOS: dict[str, str] = {
    "ml": "m", "metro": "m", "metros": "m",
    "litro": "l", "litros": "l", "lt": "l",
    "kilo": "kg", "kilos": "kg",
}

_CAMPOS_COSTE = (
    "coste_materiales", "coste_mano_obra", "coste_complementarios", "coste_otros",
)


def _clave_metrica(unidad: str | None) -> str:
    """Clave métrica canónica de una unidad, o «» si no es métrica conocida."""
    clave = normalizar_unidad(unidad)
    if clave in _FACTOR_CANTIDAD:
        return clave
    return _SINONIMOS_METRICOS.get(clave.lower(), "") if clave else ""


def _clave_imperial(unidad: str | None) -> str:
    """Clave imperial canónica («sq ft» -> «ft2»), o «» si no es imperial."""
    texto = str(unidad or "").strip()
    if not texto:
        return ""
    clave = normalizar_unidad(texto)
    if clave in _DESDE_MOSTRADA:
        return clave
    # Las formas con espacio o puntos («sq ft», «cu yd», «sq. ft.») no están
    # en _ALIAS; compactadas («sqft», «cuyd») sí resuelven.
    compacta = texto.lower().replace(" ", "").replace(".", "")
    clave = normalizar_unidad(compacta)
    return clave if clave in _DESDE_MOSTRADA else ""


def factor_cantidad(unidad: str | None) -> float | None:
    """Factor cantidad métrica -> cantidad mostrada, o None si no convierte."""
    clave = _clave_metrica(unidad)
    return _FACTOR_CANTIDAD.get(clave) if clave else None


def metrica_desde_mostrada(unidad: str | None) -> tuple[str, float] | None:
    """(unidad métrica, factor) si la unidad recibida es imperial.

    Con el factor de cantidad: ``cantidad_metrica = cantidad_mostrada /
    factor`` y ``precio_metrico = precio_mostrada * factor``.
    """
    clave = _clave_imperial(unidad)
    return _DESDE_MOSTRADA.get(clave) if clave else None


def es_imperial_codigo(codigo_pais: str | None) -> bool:
    return sistema_unidades_pais(codigo_pais) == "imperial"


def es_imperial_config(cfg) -> bool:
    """¿La empresa configurada pertenece a un mercado imperial?

    Misma puerta que la fiscalidad GB/IE: el nombre de país libre de la
    configuración se resuelve a código ISO con ``codigo_desde_pais``. Si algo
    falla, métrico: enseñar m² de más es un defecto visible; convertir sin
    querer sería un error de dinero.
    """
    try:
        from .traduccion import codigo_desde_pais

        codigo = codigo_desde_pais(getattr(cfg, "empresa_pais", "") or "")
    except Exception:
        return False
    return es_imperial_codigo(codigo)


def _numero(valor) -> float | None:
    if isinstance(valor, bool) or valor is None:
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = str(valor).strip().replace(" ", "")
    if not texto:
        return None
    try:
        return float(texto)
    except ValueError:
        try:
            return float(texto.replace(".", "").replace(",", "."))
        except ValueError:
            return None


# -- conversiones de un solo valor (superficie) -------------------------------

def unidad_mostrada(unidad: str | None, imperial: bool) -> str:
    """Etiqueta de unidad para pantalla/PDF: m2 -> «sq ft» si es imperial."""
    texto = str(unidad or "")
    if not imperial:
        return texto
    clave = _clave_metrica(texto)
    return UNIDAD_MOSTRADA.get(clave, texto) if clave else texto


def cantidad_mostrada(valor, unidad: str | None, imperial: bool) -> float:
    """Cantidad en la unidad de pantalla (la original si no convierte)."""
    numero = _numero(valor)
    if numero is None:
        numero = 0.0
    if not imperial:
        return numero
    factor = factor_cantidad(unidad)
    return round(numero * factor, 4) if factor else numero


def precio_mostrado(valor, unidad: str | None, imperial: bool):
    """Precio por unidad de pantalla. None se conserva (costes sin informar)."""
    if valor is None:
        return None
    numero = _numero(valor)
    if numero is None:
        return valor
    if not imperial:
        return numero
    factor = factor_cantidad(unidad)
    return round(numero / factor, 4) if factor else numero


def rendimiento_mostrado(valor, unidad_partida: str | None, imperial: bool):
    """Recursos por unidad de partida, en la unidad de pantalla.

    El rendimiento es «por unidad de partida»: si la partida se enseña en
    sq ft, el rendimiento por sq ft es el de por m² dividido por el factor.
    El precio del recurso no se toca (sigue siendo $/kg, $/h… en el APU), así
    el coste directo recalculado en pantalla sale en $/sq ft y cuadra con el
    precio enseñado.
    """
    if valor is None:
        return None
    numero = _numero(valor)
    if numero is None:
        return valor
    if not imperial:
        return numero
    factor = factor_cantidad(unidad_partida)
    return round(numero / factor, 6) if factor else numero


def etiqueta_mostrada(etiqueta: str | None, unidad_partida: str | None, imperial: bool) -> str:
    """Unidad de un producto/opción: solo se traduce si es la de la partida.

    El precio del producto se suma POR UNIDAD DE PARTIDA aunque su etiqueta
    diga otra cosa (un grifo «ud» dentro de una partida m2). Convertir esa
    etiqueta a otra unidad la haría mentir; si coincide con la de la partida
    (una baldosa por m2 en una partida m2), acompaña a la conversión.
    """
    texto = str(etiqueta or "")
    if not imperial or not texto:
        return texto
    if _clave_metrica(texto) and _clave_metrica(texto) == _clave_metrica(unidad_partida):
        return unidad_mostrada(texto, imperial)
    return texto


# -- filas de descomposición ---------------------------------------------------

def _es_fila_porcentaje(fila: dict) -> bool:
    return str(fila.get("unidad") or "").strip() == "%"


def _convertir_filas(filas, factor: float, *, a_metrico: bool) -> None:
    """Convierte rendimientos/importes de un descompuesto (in situ).

    - Fila de recurso: el rendimiento es por unidad de partida -> convierte
      como una cantidad inversa (a pantalla ÷, a métrico ×). El precio es
      por unidad DEL RECURSO (kg, h…) y nunca se toca.
    - Fila «%»: el rendimiento es un porcentaje (no convierte); su «precio»
      es la base en dinero por unidad de partida -> convierte como precio.
    - El importe (dinero por unidad de partida) convierte como precio en
      cualquier fila que lo traiga.
    - «celdas»/«formulas» son el espejo crudo de la matriz Excel importada:
      se preservan tal cual, el editor recalcula desde rendimiento×precio.
    """
    if not isinstance(filas, list):
        return
    for fila in filas:
        if not isinstance(fila, dict):
            continue
        # «importe» es dinero por unidad de partida. («coste_unitario» no se
        # toca: su semántica por fila no es única entre productores y tanto
        # el editor como el recálculo CYPE lo derivan de rendimiento×precio.)
        importe = _numero(fila.get("importe"))
        if importe is not None:
            fila["importe"] = round(importe * factor, 6) if a_metrico else round(importe / factor, 4)
        if _es_fila_porcentaje(fila):
            # En la fila % el «precio» es la base monetaria por unidad de
            # partida; viaja duplicado en «precio_unitario» en las filas del
            # catálogo y hay que mover los dos o la fila se contradice.
            for campo_precio in ("precio", "precio_unitario"):
                precio = _numero(fila.get(campo_precio))
                if precio is not None:
                    fila[campo_precio] = (
                        round(precio * factor, 6) if a_metrico else round(precio / factor, 4)
                    )
        elif str(fila.get("tipo") or "recurso") == "recurso":
            rendimiento = _numero(fila.get("rendimiento"))
            if rendimiento is not None:
                fila["rendimiento"] = (
                    round(rendimiento * factor, 6) if a_metrico else round(rendimiento / factor, 6)
                )


# -- payloads del editor: normalizar a métrico al guardar ----------------------

def normalizar_partida_a_metrico(partida: dict) -> bool:
    """Pasa una partida del formulario (dict del parser) a métrico, in situ.

    Se guía por la unidad que trae la propia partida: si es imperial, sus
    cantidades vienen en esa unidad. Devuelve True si convirtió algo. Lo que
    no convierte (unidad métrica, ud, glb, libre) queda intacto.
    """
    if not isinstance(partida, dict):
        return False
    destino = metrica_desde_mostrada(partida.get("unidad"))
    if destino is None:
        return False
    metrica, factor = destino
    partida["unidad"] = metrica

    def a_cantidad(valor):
        numero = _numero(valor)
        return round(numero / factor, 6) if numero is not None else valor

    def a_precio(valor):
        if valor is None:
            return None
        numero = _numero(valor)
        return round(numero * factor, 6) if numero is not None else valor

    partida["cantidad"] = a_cantidad(partida.get("cantidad"))
    partida["precio"] = a_precio(partida.get("precio"))
    if "precio_base" in partida:
        partida["precio_base"] = a_precio(partida.get("precio_base"))
    for campo in _CAMPOS_COSTE:
        if campo in partida:
            partida[campo] = a_precio(partida.get(campo))
    for campo in ("prod_precio", "prod_coste"):
        if partida.get(campo) is not None:
            partida[campo] = a_precio(partida.get(campo))
    if partida.get("prod_unidad"):
        destino_prod = metrica_desde_mostrada(partida.get("prod_unidad"))
        if destino_prod is not None and destino_prod[0] == metrica:
            partida["prod_unidad"] = metrica

    mediciones = partida.get("mediciones")
    if isinstance(mediciones, list):
        nuevas = []
        for medicion in mediciones:
            if isinstance(medicion, dict):
                copia = dict(medicion)
                copia["cantidad"] = a_cantidad(copia.get("cantidad"))
                nuevas.append(copia)
            elif isinstance(medicion, (list, tuple)) and len(medicion) >= 2:
                nuevas.append((medicion[0], a_cantidad(medicion[1])))
            else:
                nuevas.append(medicion)
        partida["mediciones"] = nuevas

    opciones = partida.get("productos_opciones")
    if isinstance(opciones, list):
        for opcion in opciones:
            if not isinstance(opcion, dict):
                continue
            # El precio de la opción se suma por unidad de partida: convierte
            # con el factor de la partida, diga lo que diga su etiqueta.
            opcion["precio"] = a_precio(opcion.get("precio"))
            if opcion.get("coste") is not None:
                opcion["coste"] = a_precio(opcion.get("coste"))
            if opcion.get("unidad"):
                destino_op = metrica_desde_mostrada(opcion.get("unidad"))
                if destino_op is not None and destino_op[0] == metrica:
                    opcion["unidad"] = metrica

    descomposicion = partida.get("descomposicion")
    if isinstance(descomposicion, dict):
        _convertir_filas(descomposicion.get("filas"), factor, a_metrico=True)
        if descomposicion.get("unidad"):
            destino_desc = metrica_desde_mostrada(descomposicion.get("unidad"))
            if destino_desc is not None and destino_desc[0] == metrica:
                descomposicion["unidad"] = metrica
    elif isinstance(descomposicion, list):
        _convertir_filas(descomposicion, factor, a_metrico=True)

    meta = partida.get("descomposicion_meta")
    if isinstance(meta, dict) and meta.get("unidad"):
        destino_meta = metrica_desde_mostrada(meta.get("unidad"))
        if destino_meta is not None and destino_meta[0] == metrica:
            meta["unidad"] = metrica
    return True


def normalizar_partidas_a_metrico(partidas) -> None:
    if isinstance(partidas, list):
        for partida in partidas:
            normalizar_partida_a_metrico(partida)


def partida_editor_a_mostrada(partida: dict, imperial: bool) -> dict:
    """Inverso de :func:`normalizar_partida_a_metrico` para payloads guardados.

    Las plantillas de presupuesto almacenan la estructura del editor en
    métrico; al cargarla en un editor imperial hay que enseñarla en pies.
    Devuelve una copia convertida (el dict de origen no se toca).
    """
    if not imperial or not isinstance(partida, dict):
        return partida
    factor = factor_cantidad(partida.get("unidad"))
    if not factor:
        return partida
    import copy

    salida = copy.deepcopy(partida)
    unidad_original = partida.get("unidad")
    salida["unidad"] = UNIDAD_MOSTRADA[_clave_metrica(unidad_original)]

    def a_cantidad(valor):
        numero = _numero(valor)
        return round(numero * factor, 4) if numero is not None else valor

    def a_precio(valor):
        if valor is None:
            return None
        numero = _numero(valor)
        return round(numero / factor, 4) if numero is not None else valor

    salida["cantidad"] = a_cantidad(salida.get("cantidad"))
    salida["precio"] = a_precio(salida.get("precio"))
    if "precio_base" in salida:
        salida["precio_base"] = a_precio(salida.get("precio_base"))
    for campo in _CAMPOS_COSTE:
        if campo in salida:
            salida[campo] = a_precio(salida.get(campo))
    for campo in ("prod_precio", "prod_coste"):
        if salida.get(campo) is not None:
            salida[campo] = a_precio(salida.get(campo))
    if salida.get("prod_unidad"):
        salida["prod_unidad"] = etiqueta_mostrada(
            salida.get("prod_unidad"), unidad_original, True
        )

    mediciones = salida.get("mediciones")
    if isinstance(mediciones, list):
        for medicion in mediciones:
            if isinstance(medicion, dict) and "cantidad" in medicion:
                medicion["cantidad"] = a_cantidad(medicion.get("cantidad"))

    opciones = salida.get("productos_opciones")
    if isinstance(opciones, list):
        for opcion in opciones:
            if not isinstance(opcion, dict):
                continue
            opcion["precio"] = a_precio(opcion.get("precio"))
            if opcion.get("coste") is not None:
                opcion["coste"] = a_precio(opcion.get("coste"))
            if opcion.get("unidad"):
                opcion["unidad"] = etiqueta_mostrada(
                    opcion.get("unidad"), unidad_original, True
                )

    descomposicion = salida.get("descomposicion")
    if isinstance(descomposicion, dict):
        _convertir_filas(descomposicion.get("filas"), factor, a_metrico=False)
        if descomposicion.get("unidad"):
            descomposicion["unidad"] = etiqueta_mostrada(
                descomposicion.get("unidad"), unidad_original, True
            )
    elif isinstance(descomposicion, list):
        _convertir_filas(descomposicion, factor, a_metrico=False)

    meta = salida.get("descomposicion_meta")
    if isinstance(meta, dict) and meta.get("unidad"):
        meta["unidad"] = etiqueta_mostrada(meta.get("unidad"), unidad_original, True)
    return salida


def capitulos_editor_a_mostrada(capitulos, imperial: bool):
    """Estructura de capítulos del editor (plantillas) en unidad de pantalla."""
    if not imperial or not isinstance(capitulos, list):
        return capitulos
    salida = []
    for capitulo in capitulos:
        if not isinstance(capitulo, dict):
            salida.append(capitulo)
            continue
        nuevo = dict(capitulo)
        nuevo["partidas"] = [
            partida_editor_a_mostrada(p, True)
            for p in (capitulo.get("partidas") or [])
        ]
        salida.append(nuevo)
    return salida


# -- payloads hacia el editor: catálogo, productos y recetas -------------------

def ficha_catalogo_a_mostrada(datos: dict, imperial: bool) -> dict:
    """Índice o ficha de una partida del catálogo, en la unidad de pantalla.

    Sirve para el índice ligero, las hojas del árbol, el buscador y la ficha
    completa: todos comparten las claves precio/precio_unitario/costes y,
    cuando existe, la descomposición con sus rendimientos.
    """
    if not imperial or not isinstance(datos, dict):
        return datos
    factor = factor_cantidad(datos.get("unidad"))
    if not factor:
        return datos
    salida = dict(datos)
    salida["unidad"] = UNIDAD_MOSTRADA[_clave_metrica(datos.get("unidad"))]
    for campo in ("precio", "precio_unitario", *_CAMPOS_COSTE):
        numero = _numero(salida.get(campo))
        if numero is not None:
            salida[campo] = round(numero / factor, 4)
    # Las horas son POR UNIDAD de partida (h/m² -> h/sq ft): se mueven como
    # un rendimiento, o la estimación de duración del editor (cantidad ×
    # horas/ud) saldría multiplicada por el factor.
    for campo in (
        "tiempo_estimado_horas", "tiempo_oficial_horas",
        "tiempo_ayudante_horas", "tiempo_equipo_horas",
    ):
        numero = _numero(salida.get(campo))
        if numero is not None:
            salida[campo] = round(numero / factor, 6)
    descomposicion = salida.get("descomposicion")
    if isinstance(descomposicion, dict) and isinstance(descomposicion.get("filas"), list):
        filas = [dict(f) if isinstance(f, dict) else f for f in descomposicion["filas"]]
        _convertir_filas(filas, factor, a_metrico=False)
        nueva = dict(descomposicion, filas=filas)
        if nueva.get("unidad") and _clave_metrica(nueva.get("unidad")) == _clave_metrica(datos.get("unidad")):
            nueva["unidad"] = salida["unidad"]
        salida["descomposicion"] = nueva
    return salida


def normalizar_ficha_catalogo_a_metrico(datos: dict, filas, costes: dict) -> bool:
    """Normaliza el guardado de una ficha del catálogo, in situ.

    Espejo de la normalización de moneda que ya hacen las rutas de Partidas:
    si la unidad que trae el formulario es imperial («sq ft» desde el editor
    estadounidense, o escrita a mano en el CRUD), precio, costes, horas por
    unidad, rendimientos e importes llegan por pie cuadrado y el catálogo
    debe guardarlos por m². Todo escala lineal con el factor, igual que el
    recálculo del descompuesto. Devuelve True si convirtió.
    """
    if not isinstance(datos, dict):
        return False
    destino = metrica_desde_mostrada(datos.get("unidad"))
    if destino is None:
        return False
    metrica, factor = destino
    datos["unidad"] = metrica
    for campo in ("precio_unitario", *_CAMPOS_COSTE,
                  "tiempo_estimado_horas", "tiempo_oficial_horas",
                  "tiempo_ayudante_horas", "tiempo_equipo_horas"):
        numero = _numero(datos.get(campo))
        if numero is not None:
            datos[campo] = round(numero * factor, 6)
    _convertir_filas(filas, factor, a_metrico=True)
    if isinstance(costes, dict):
        for clave in list(costes):
            numero = _numero(costes.get(clave))
            if numero is not None:
                costes[clave] = round(numero * factor, 6)
    return True


def filas_descomposicion_a_mostrada(filas, unidad_partida, imperial: bool):
    """Filas sueltas de un descompuesto (respuesta de la ficha de mercado)."""
    if not imperial or not isinstance(filas, list):
        return filas
    factor = factor_cantidad(unidad_partida)
    if not factor:
        return filas
    salida = [dict(f) if isinstance(f, dict) else f for f in filas]
    _convertir_filas(salida, factor, a_metrico=False)
    return salida


def producto_catalogo_a_mostrado(datos: dict, imperial: bool) -> dict:
    """Producto comercial: su precio es por SU unidad (baldosa por m2…)."""
    if not imperial or not isinstance(datos, dict):
        return datos
    factor = factor_cantidad(datos.get("unidad"))
    if not factor:
        return datos
    salida = dict(datos)
    salida["unidad"] = UNIDAD_MOSTRADA[_clave_metrica(datos.get("unidad"))]
    for campo in ("precio", "precio_unitario", "coste", "precio_compra"):
        numero = _numero(salida.get(campo))
        if numero is not None:
            salida[campo] = round(numero / factor, 4)
    return salida


def normalizar_pack_a_metrico(items, unidad_base: str, cantidad_base: float):
    """Normaliza «guardar capítulo como pack» al vuelo, antes de persistir.

    El capítulo llega tal y como se ve en el editor: si la unidad base es
    imperial («sq ft»), la medida base y las cantidades/precios de los
    ítems están en imperial. Se mutan los dicts (recién parseados del JSON)
    y se devuelve ``(unidad_base_metrica, cantidad_base_metrica)`` para que
    el cálculo de coeficientes posterior trabaje ya en métrico y el pack
    quede reutilizable en cualquier mercado. Cada ítem convierte por SU
    unidad (la base solo manda en la medida de la estancia).
    """
    base = str(unidad_base or "").strip() or "m²"
    try:
        cantidad = float(cantidad_base or 0)
    except (TypeError, ValueError):
        cantidad = 0.0
    destino_base = metrica_desde_mostrada(base)
    if destino_base is not None:
        base, factor_base = destino_base
        if cantidad:
            cantidad = round(cantidad / factor_base, 6)
    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue
            destino = metrica_desde_mostrada(item.get("unidad"))
            if destino is None:
                continue
            metrica, factor = destino
            item["unidad"] = metrica
            numero = _numero(item.get("cantidad"))
            if numero is not None:
                item["cantidad"] = round(numero / factor, 6)
            for campo in ("precio", "prod_precio", "prod_coste"):
                numero = _numero(item.get(campo))
                if numero is not None:
                    item[campo] = round(numero * factor, 6)
            if item.get("prod_unidad"):
                destino_prod = metrica_desde_mostrada(item.get("prod_unidad"))
                if destino_prod is not None and destino_prod[0] == metrica:
                    item["prod_unidad"] = metrica
    return base, cantidad


def receta_a_mostrada(receta: dict, imperial: bool) -> dict:
    """Pack de estancia en la unidad de pantalla.

    La medida base (los m² de la estancia) y cada ítem convierten con su
    propio factor; el coeficiente —cantidad del ítem por unidad base— se
    reescala con el cociente de ambos factores para que, al insertar el
    pack con una medida en sq ft, salgan las cantidades en sq ft correctas.
    Los ítems que ya vinieran en unidad imperial (guardados a mano en el
    CRUD de recetas) se dejan como están: su unidad ya dice la verdad.
    """
    if not imperial or not isinstance(receta, dict):
        return receta
    salida = dict(receta)
    base = receta.get("unidad_base") or "m²"
    factor_base = factor_cantidad(base)
    if factor_base:
        salida["unidad_base"] = UNIDAD_MOSTRADA[_clave_metrica(base)]
        por_defecto = _numero(receta.get("cantidad_base_default"))
        if por_defecto is not None:
            salida["cantidad_base_default"] = round(por_defecto * factor_base, 4)
    items = []
    for item in receta.get("items") or []:
        if not isinstance(item, dict):
            items.append(item)
            continue
        nuevo = dict(item)
        factor_item = factor_cantidad(item.get("unidad"))
        if factor_item:
            nuevo["unidad"] = UNIDAD_MOSTRADA[_clave_metrica(item.get("unidad"))]
            for campo in ("precio", "prod_precio", "prod_coste"):
                numero = _numero(nuevo.get(campo))
                if numero is not None:
                    nuevo[campo] = round(numero / factor_item, 4)
            fija = _numero(nuevo.get("cantidad_fija"))
            if fija is not None:
                nuevo["cantidad_fija"] = round(fija * factor_item, 4)
            coeficiente = _numero(nuevo.get("coeficiente"))
            if coeficiente is not None:
                divisor = factor_base or 1.0
                nuevo["coeficiente"] = round(coeficiente * factor_item / divisor, 6)
            if nuevo.get("prod_unidad"):
                nuevo["prod_unidad"] = etiqueta_mostrada(
                    nuevo.get("prod_unidad"), item.get("unidad"), imperial
                )
        items.append(nuevo)
    salida["items"] = items
    return salida

