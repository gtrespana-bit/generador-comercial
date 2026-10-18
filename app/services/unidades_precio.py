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
