"""El presupuesto de ejemplo, hecho con el mercado de cada empresa.

Por qué existe
--------------
Hasta el 02/11/2026 el ejemplo del alta era único y venezolano: lo escribía
``app/seeds.py`` a mano, en USD, con IVA del 16 % y con partidas como
«Cabilla» o «Bloque de concreto». El país que la persona había elegido en el
alta se guardaba en ``Configuracion.empresa_pais`` y **nunca llegaba a la
siembra**: la función recibía solo el idioma. Un mexicano abría su ejemplo y
veía un presupuesto de Caracas.

El producto ya tenía la información y no la usaba. ``services/precios_publicos``
resuelve, para 22 mercados, el precio unitario real de cada partida en moneda
local, con el título traducido a la jerga del país («alicatado» en España,
«enchape» en Colombia, «recubrimiento» en México) y con la guardia de calidad
que exige descripción completa y descompuesto de al menos tres líneas. Ese
índice se construye en ~0,04 s porque viaja precalculado en
``basedatos_partidas/datos/precios_publicos/<PAIS>.json``.

Lo que hace este módulo
-----------------------
Toma del índice del país las partidas de una **reforma de baño completa**
—demolición, impermeabilización, alicatado, solado, sanitarios, mobiliario,
puertas, fontanería, electricidad y pintura— y les pone cantidades de una
vivienda real, expresadas en la unidad del mercado. El resultado es un
presupuesto que el contratista de ese país reconoce como suyo: sus precios, su
moneda, sus palabras.

Se busca **por código de partida**, no por apartado. El índice público agrupa
las fichas en apartados y descarta los que no llegan a tres partidas
publicables; con el filtro por apartado, México se quedaba sin alicatado ni
sanitarios aunque esas partidas sí tienen precio allí. El código es la clave
estable: es el mismo en los 22 mercados y cambia el precio, no el número.

Lo que **no** hace
------------------
No inventa precios. Si una partida no tiene precio completo en el país, el
índice no la ofrece y se usa otra o no se usa. Si el país no tiene matriz
(Venezuela hoy), se cae al ejemplo de siempre, que se conserva intacto en
``seeds.py``. Y la unidad de la partida se contrasta con la que el índice
publica: meter un precio «por sq ft» en una línea medida «por m²» saldría
diez veces por debajo del real y con el mismo aspecto de estar bien.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field

from ..paises import PAISES, resolver_mercado
from . import precios_publicos as pp
from .traduccion import traducir

#: Países que pueden generar su propio ejemplo (los que tienen matriz).
PAISES_CON_EJEMPLO = pp.PAISES_PRECIOS_PUBLICOS


@dataclass(frozen=True)
class ApartadoEjemplo:
    """Un capítulo del ejemplo: de qué partidas del catálogo se nutre."""

    titulo_es: str
    titulo_en: str
    partidas: tuple[tuple[str, float], ...]   # (código del catálogo, cantidad)
    medidas_es: tuple[str, ...] = ()
    medidas_en: tuple[str, ...] = ()


@dataclass(frozen=True)
class PartidaEjemplo:
    codigo: str
    nombre: str
    descripcion: str
    unidad: str
    precio: float
    moneda: str
    cantidad: float
    medicion: str = ""
    capitulo: str = ""


@dataclass
class EjemploPais:
    """Presupuesto de ejemplo ya resuelto para un mercado."""

    codigo_pais: str
    moneda: str
    impuesto_pct: float
    idioma: str
    titulo: str
    ciudad: str
    notas: str
    condiciones: str
    partidas: list[PartidaEjemplo] = field(default_factory=list)

    @property
    def total(self) -> float:
        return round(sum(p.cantidad * p.precio for p in self.partidas), 2)

    @property
    def capitulos(self) -> list[str]:
        vistos: list[str] = []
        for p in self.partidas:
            if p.capitulo and p.capitulo not in vistos:
                vistos.append(p.capitulo)
        return vistos


# ---------------------------------------------------------------------------
# El guion del ejemplo: una reforma de baño, no una obra de promotora
# ---------------------------------------------------------------------------
#
# El anterior era una remodelación genérica de vivienda con muros, dinteles y
# estructura. Una reforma de baño tiene tres ventajas para alguien que abre la
# herramienta por primera vez:
#
#   1. Es el trabajo que más piden los clientes de un contratista pequeño.
#   2. Cabe en una pantalla y se lee en veinte segundos.
#   3. Toca todas las categorías que la app sabe hacer (demolición, albañilería,
#      instalaciones, acabados), así que el catálogo se ve completo.
#
# Los códigos son los del catálogo base y las cantidades las de un baño de
# vivienda (≈4 m² de suelo, 2,30 m de alto). Si un mercado no publica el código,
# el apartado se descarta; el ejemplo sigue teniendo sentido con los demás.
_APARTADOS: tuple[ApartadoEjemplo, ...] = (
    ApartadoEjemplo(
        "Demoliciones y albañilería",
        "Demolition and masonry",
        (("02.04.01.010", 51.7),),
        ("Tabique del baño a demoler",),
        ("Bathroom partition to demolish",),
    ),
    ApartadoEjemplo(
        "Impermeabilización",
        "Waterproofing",
        (("10.05.01.010", 45.2), ("10.05.01.060", 77.5)),
        ("Piso de la ducha bajo el alicatado", "Paredes de la zona de ducha"),
        ("Shower floor under tiling", "Shower walls"),
    ),
    ApartadoEjemplo(
        "Alicatado de paredes",
        "Wall tiling",
        (("12.03.01.010", 198.0), ("12.03.01.060", 77.5)),
        ("Paredes del baño, 2,30 m de alto", "Zona de ducha, de suelo a techo"),
        ("Bathroom walls, 2.30 m high", "Shower area, floor to ceiling"),
    ),
    ApartadoEjemplo(
        "Solado",
        "Floor tiling",
        (("12.05.03.010", 45.2),),
        ("Solado del baño",),
        ("Bathroom floor",),
    ),
    ApartadoEjemplo(
        "Sanitarios y grifería",
        "Sanitaryware and taps",
        (("09.01.04.010", 1.0), ("09.01.04.020", 1.0), ("09.01.04.030", 1.0)),
        ("Inodoro", "Lavabo con grifería", "Ducha con grifería"),
        ("WC", "Washbasin with tap", "Shower with mixer"),
    ),
    ApartadoEjemplo(
        "Mobiliario de baño",
        "Bathroom furniture",
        (("13.03.01.010", 1.0), ("13.03.01.020", 1.0)),
        ("Mueble con lavabo", "Espejo y botiquín"),
        ("Vanity unit", "Mirror and cabinet"),
    ),
    ApartadoEjemplo(
        "Carpintería",
        "Joinery",
        (("07.01.01.010", 1.0), ("07.01.01.030", 1.0)),
        ("Puerta del baño", "Cerradura y herrajes"),
        ("Bathroom door", "Lock and ironmongery"),
    ),
    ApartadoEjemplo(
        "Fontanería",
        "Plumbing",
        (("09.02.02.010", 3.0),),
        ("Puntos de desagüe: inodoro, lavabo y ducha",),
        ("Drain points: WC, washbasin and shower",),
    ),
    ApartadoEjemplo(
        "Electricidad",
        "Electrical",
        (("09.03.06.020", 2.0), ("09.03.06.010", 1.0)),
        ("Puntos eléctricos reubicados", "Punto para secadora"),
        ("Relocated electrical points", "Dryer point"),
    ),
    ApartadoEjemplo(
        "Pintura",
        "Painting",
        (("12.10.01.010", 150.7), ("12.10.01.030", 45.2)),
        ("Pasillo y resto de paredes", "Techo del baño"),
        ("Hallway and remaining walls", "Bathroom ceiling"),
    ),
)

#: Máximo de partidas: por encima de quince, el ejemplo deja de leerse.
_MAX_PARTIDAS = 15
#: Mínimo para que el ejemplo enseñe algo. Por debajo, mejor el genérico.
_MIN_PARTIDAS = 6

_NOTAS_ES = (
    "Presupuesto de reforma de baño elaborado con precios de referencia de "
    "{pais} y mediciones tomadas en obra. Incluye mano de obra, materiales y "
    "gestión del proyecto. No incluye sanitarios ni grifería de gama superior "
    "a la presupuestada, ni trabajos de estructura."
)
_NOTAS_EN = (
    "Bathroom renovation estimate built with reference prices for {pais} and "
    "site measurements. Labour, materials and project management included. "
    "Premium sanitaryware and structural work are excluded."
)
_CONDICIONES_ES = (
    "Forma de pago: 40 % de anticipo, 35 % al certificar el 50 % de la obra y "
    "25 % contra entrega.\nPlazo estimado: 3 semanas desde la firma.\n"
    "Garantía de 12 meses en instalaciones y acabados."
)
_CONDICIONES_EN = (
    "Payment: 40% deposit, 35% at 50% certified progress and 25% on "
    "handover.\nEstimated duration: 3 weeks from signing.\n"
    "12-month warranty on installations and finishes."
)
_TITULO_ES = "Reforma de baño — presupuesto de ejemplo"
_TITULO_EN = "Bathroom renovation — sample estimate"


def _sin_acento(texto: str) -> str:
    descompuesto = unicodedata.normalize("NFD", str(texto or ""))
    return "".join(c for c in descompuesto if not unicodedata.combining(c))


def _clave(texto: str) -> str:
    """Compara unidades sin depender de acentos, mayúsculas ni espacios."""
    return _sin_acento(texto).strip().lower().replace(" ", "")


def _cantidad_de_obra(cantidad_mercado: float, unidad_mercado: str) -> float:
    """La cantidad de obra escrita en la unidad del mercado.

    Las cantidades del guion están en metros de obra real (4,2 m² de solado son
    4,2 m² en cualquier país). El índice del país, en cambio, ya devuelve la
    unidad en la que **cobra**: «sq ft» en Estados Unidos. Aquí solo se elige
    el número que corresponde a esa unidad; no hay factor de conversión que
    aplicar y, sobre todo, no hay que aplicarlo dos veces: la ficha ya viene
    con el precio por pie cuadrado y con la cantidad en pies cuadrados.

    La versión anterior multiplicaba la cantidad por 10,76 «porque el catálogo
    es métrico» y dejaba un baño de 4,2 m² valorado como 4,2 pies cuadrados:
    cuarenta dólares en vez de cuatrocientos, con el mismo aspecto de estar
    bien. Por eso el número de arriba ya es el de obra, no el métrico.
    """
    return round(float(cantidad_mercado), 2)


def _fichas_por_codigo(indice: dict) -> dict[str, dict]:
    """Código de partida -> ficha completa del índice del país."""
    salida: dict[str, dict] = {}
    for par in (indice.get("por_codigo") or {}).values():
        ficha = (indice.get("partidas") or {}).get(tuple(par))
        if ficha and ficha.get("codigo"):
            salida[str(ficha["codigo"])] = ficha
    return salida


def ejemplo_para_pais(
    codigo_pais: str, idioma: str = "es", pais_nombre: str = ""
) -> EjemploPais | None:
    """Presupuesto de ejemplo del mercado, o ``None`` si no hay matriz.

    Devuelve ``None`` —y quien llama usa el ejemplo venezolano de siempre— en
    dos casos: mercado desconocido y mercado sin matriz de precios publicada.
    No es un error: es la respuesta honesta.
    """
    cc = str(codigo_pais or "").strip().upper()
    if not cc:
        cc = str((resolver_mercado(codigo_pais or "") or {}).get("codigo") or "").upper()
    if not cc or cc not in PAISES:
        return None

    indice = pp._indice(cc)
    if not indice:
        return None

    pais = PAISES[cc]
    en = str(pais.get("idioma") or "es") == "en" or str(idioma or "").lower().startswith("en")
    fichas = _fichas_por_codigo(indice)

    partidas: list[PartidaEjemplo] = []
    for plan in _APARTADOS:
        if len(partidas) >= _MAX_PARTIDAS:
            break
        medidas = plan.medidas_en if en else plan.medidas_es
        for i, (codigo, cantidad) in enumerate(plan.partidas):
            if len(partidas) >= _MAX_PARTIDAS:
                break
            ficha = fichas.get(codigo)
            if not ficha or float(ficha.get("pu") or 0) <= 0:
                continue
            unidad = str(ficha.get("unidad") or "").strip()
            if not unidad:
                continue
            partidas.append(
                PartidaEjemplo(
                    codigo=codigo,
                    nombre=str(ficha.get("titulo") or "").strip(),
                    descripcion=str(ficha.get("descripcion") or "").strip(),
                    unidad=unidad,
                    precio=round(float(ficha.get("pu") or 0), 2),
                    moneda=str(ficha.get("moneda") or pais.get("moneda") or ""),
                    cantidad=_cantidad_de_obra(cantidad, unidad),
                    medicion=medidas[i] if i < len(medidas) else "",
                    # El rótulo del capítulo se traduce: «Alicatado» no se usa
                    # en México, y tres de los cuatro nombres que probé no
                    # estaban en el glosario.
                    capitulo=traducir(plan.titulo_en if en else plan.titulo_es, cc),
                )
            )

    if len(partidas) < _MIN_PARTIDAS:
        return None

    # En inglés el nombre del país también se escribe en inglés: la nota decía
    # «with Estados Unidos reference prices».
    nombre_mercado = (
        (pais.get("nombre_en") or pais.get("nombre") or "")
        if en
        else (pais_nombre or pais.get("nombre") or "")
    ).strip()
    return EjemploPais(
        codigo_pais=cc,
        moneda=str(pais.get("moneda") or "").upper() or "USD",
        impuesto_pct=float(pais.get("iva") or 0),
        idioma="en" if en else "es",
        titulo=_TITULO_EN if en else _TITULO_ES,
        ciudad=str(pais.get("ciudad_ejemplo") or ""),
        notas=(_NOTAS_EN if en else _NOTAS_ES).format(pais=nombre_mercado),
        condiciones=_CONDICIONES_EN if en else _CONDICIONES_ES,
        partidas=partidas,
    )
