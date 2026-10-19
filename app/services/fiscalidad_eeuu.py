"""Fiscalidad estadounidense del presupuesto: «sales tax» por estado.

Por qué existe este módulo
--------------------------
En Estados Unidos no hay un impuesto nacional sobre la obra ni una regla
única de «precio + impuesto». Hay tres marcos estatales (el análisis
completo está en ``docs/ANALISIS_MERCADO_ESTADOS_UNIDOS.md`` §4):

1. **Contratista como consumidor final** (la mayoría de los estados): el
   contratista paga el impuesto al comprar los materiales y **no cobra
   «sales tax» al cliente**; la mano de obra que mejora un inmueble no
   se grava. El documento correcto no lleva línea de impuesto.
2. **Se cobra al cliente según el tipo de obra o de contrato** (Nueva
   York, Nueva Jersey, Texas, Carolina del Norte, Colorado…): mejora
   capital exenta frente a reparación gravada, residencial frente a no
   residencial, precio alzado frente a «time-and-materials». La base
   puede ser solo los materiales, solo la mano de obra o el precio
   completo.
3. **Impuesto sobre los ingresos brutos del contratista** (GET de Hawái,
   GRT de Nuevo México, «contractor's excise» de Dakota del Sur, TPT
   «prime contracting» de Arizona sobre el **65 %** del contrato).

Un selector de estado que solo cambiara el porcentaje aplicado al total
sería incorrecto en buena parte del país: cobraría al cliente un
impuesto que no existe. Por eso el estado aporta un **modo de base**
propuesto (``us_tax_base``) y un tipo combinado medio de partida, ambos
editables en cada documento.

Lo que NO hace este módulo
--------------------------
No decide si una obra es «capital improvement» o reparación, ni el tipo
exacto de la obra (depende del condado/ciudad: no mantenemos 11.000
jurisdicciones). Propone el default investigado
(``docs/INVESTIGACION_FISCALIDAD_ESTADOS_UNIDOS.md``), aplica sus
consecuencias aritméticas y avisa de los bifurcaciones conocidas.

La estimación de materiales
---------------------------
En los modos «solo materiales» / «solo mano de obra» hace falta el precio
de venta de los materiales dentro de la base, que el presupuesto no
guarda como tal. Se estima con el reparto de costes del propio documento
—la misma segunda pasada que alimenta el CIS británico—: la parte de
obra de la base se reparte como `coste_materiales / coste_obra` y la
venta de productos cuenta íntegra como materiales (son bienes que se
revenden al cliente). Es una aproximación declarada, no una medición:
sin costes informados no se inventa el reparto y se avisa.

Todas las cantidades son ``Decimal`` y entran y salen en la moneda del
documento (dólares en el mercado estadounidense).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

# ─────────────────────────────────────────────────────────────────────────────
# Modos de base imponible
# ─────────────────────────────────────────────────────────────────────────────

#: ``""`` deja el documento como estaba antes de existir este motor
#: (impuesto genérico sobre la base completa): ningún presupuesto ya
#: emitido cambia al desplegar.
BASE_SIN_MOTOR = ""
#: No se cobra impuesto al cliente (marco «contratista consumidor»).
BASE_NINGUNA = "none"
#: Solo el precio de venta de los materiales.
BASE_MATERIALES = "materials"
#: Solo la mano de obra y los servicios (Kansas comercial).
BASE_MANO_OBRA = "labor"
#: El precio completo: materiales + mano de obra.
BASE_COMPLETA = "full"
#: Ingresos brutos del contratista, con fracción de base (Arizona: 65 %).
BASE_BRUTOS = "gross_receipts"

BASES_US: tuple[str, ...] = (
    BASE_SIN_MOTOR, BASE_NINGUNA, BASE_MATERIALES,
    BASE_MANO_OBRA, BASE_COMPLETA, BASE_BRUTOS,
)

#: Modos que necesitan el reparto materiales/mano de obra.
BASES_CON_REPARTO: tuple[str, ...] = (BASE_MATERIALES, BASE_MANO_OBRA)

_CERO = Decimal("0")
_CENT = Decimal("0.01")
_UNO = Decimal("1")


def _d(valor) -> Decimal:
    if valor is None:
        return _CERO
    if isinstance(valor, Decimal):
        return valor
    return Decimal(str(valor))


# ─────────────────────────────────────────────────────────────────────────────
# Defaults por estado (investigación 19-10-2026)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class EstadoEEUU:
    """Default fiscal de un estado para una reforma de inmueble.

    ``tipo_medio`` es el combinado estatal + local medio de Tax
    Foundation (midyear 2026): un punto de partida editable, no el tipo
    legal de ninguna obra concreta. ``nota`` (en inglés: es la ayuda que
    lee el operador estadounidense) dice cuándo hay que cambiar el modo.
    """

    codigo: str
    nombre: str
    base_defecto: str
    tipo_medio: Decimal
    fraccion_defecto: Decimal = _UNO
    nombre_impuesto: str = "Sales tax"
    nota: str = ""


def _e(codigo, nombre, base, tipo, **kw) -> EstadoEEUU:
    return EstadoEEUU(codigo, nombre, base, Decimal(tipo), **kw)


ESTADOS_EEUU: tuple[EstadoEEUU, ...] = (
    _e("AL", "Alabama", BASE_NINGUNA, "9.46"),
    _e("AK", "Alaska", BASE_NINGUNA, "0", nota="No statewide sales tax; some boroughs and cities levy a local sales tax — check the job location."),
    _e("AZ", "Arizona", BASE_NINGUNA, "8.54", fraccion_defecto=Decimal("0.65"), nombre_impuesto="Transaction privilege tax", nota="Most home remodels are MRRA: tax is paid on the materials and no tax line goes on the invoice. Modification work (additions, structural changes) is prime contracting — switch to Gross receipts (tax base is 65% of the contract price)."),
    _e("AR", "Arkansas", BASE_NINGUNA, "9.48"),
    _e("CA", "California", BASE_NINGUNA, "9.03", nota="You are the consumer of materials. Fixtures you furnish and install are a retail sale — see CDTFA Publication 9."),
    _e("CO", "Colorado", BASE_NINGUNA, "7.89", nota="Lump-sum contracts: no tax charged. Time-and-materials contracts: switch to Materials only and collect tax on the marked-up price of the materials."),
    _e("CT", "Connecticut", BASE_NINGUNA, "6.35", nota="Owner-occupied homes and new construction are exempt. Services to existing commercial or industrial property are generally taxable — see DRS IP 2018(2)."),
    _e("DE", "Delaware", BASE_NINGUNA, "0", nota="Delaware has no sales tax."),
    _e("DC", "District of Columbia", BASE_NINGUNA, "6.00", nota="Contractors are the consumers of the materials they install (DCMR Title 9, §438). Separately stated material sales can be retail sales."),
    _e("FL", "Florida", BASE_NINGUNA, "6.98"),
    _e("GA", "Georgia", BASE_NINGUNA, "7.56"),
    _e("HI", "Hawaii", BASE_BRUTOS, "4.50", nombre_impuesto="General excise tax", nota="GET applies to the full contract amount and may be visibly passed on to the customer. Materials incorporated into the job are taxed at the 0.5% wholesale rate — this estimate uses a single rate; adjust if you split them out."),
    _e("ID", "Idaho", BASE_NINGUNA, "6.03"),
    _e("IL", "Illinois", BASE_NINGUNA, "8.98"),
    _e("IN", "Indiana", BASE_NINGUNA, "7.00", nota="Lump-sum contracts: pay tax on materials. Time-and-materials contracts: switch to Materials only and collect tax on the materials."),
    _e("IA", "Iowa", BASE_NINGUNA, "6.94", nota="Remodeling labor is exempt even when the service is on Iowa's taxable list. Standalone repairs are taxable — switch to Full amount for repair work."),
    _e("KS", "Kansas", BASE_NINGUNA, "8.71", nota="Residential labor and original construction are exempt. Commercial remodeling: switch to Labor only — materials are taxed when you buy them (Pub. KS-1525)."),
    _e("KY", "Kentucky", BASE_NINGUNA, "6.00"),
    _e("LA", "Luisiana", BASE_NINGUNA, "10.13"),
    _e("ME", "Maine", BASE_NINGUNA, "5.50"),
    _e("MD", "Maryland", BASE_NINGUNA, "6.00"),
    _e("MA", "Massachusetts", BASE_NINGUNA, "6.25"),
    _e("MI", "Michigan", BASE_NINGUNA, "6.00"),
    _e("MN", "Minnesota", BASE_NINGUNA, "8.14"),
    _e("MS", "Mississippi", BASE_NINGUNA, "7.06", nombre_impuesto="Contractor's tax", nota="Residential work: pay 7% tax on materials. Non-residential contracts over $10,000 pay the 3.5% contractor's tax on the full contract price — switch to Gross receipts and set the rate to 3.5%."),
    _e("MO", "Missouri", BASE_NINGUNA, "8.44"),
    _e("MT", "Montana", BASE_NINGUNA, "0", nota="Montana has no general sales tax."),
    _e("NE", "Nebraska", BASE_NINGUNA, "6.98", nota="This assumes an Option 1 (consumer) contractor. If you elected Option 2 or 3 as a retailer of building materials, switch to Materials only."),
    _e("NV", "Nevada", BASE_NINGUNA, "8.24"),
    _e("NH", "New Hampshire", BASE_NINGUNA, "0", nota="New Hampshire has no sales tax."),
    _e("NJ", "New Jersey", BASE_NINGUNA, "6.60", nota="Exempt capital improvements are not taxed — get a completed Form ST-8 from the customer. Repairs and maintenance: switch to Full amount (tax on materials and labor)."),
    _e("NM", "New Mexico", BASE_BRUTOS, "7.68", nombre_impuesto="Gross receipts tax", nota="Gross receipts tax applies to construction receipts. The rate depends on where the job is located; some deductions may apply."),
    _e("NY", "New York", BASE_NINGUNA, "8.54", nota="Capital improvements are not taxed — get Form ST-124 from the customer — and you pay tax on the materials. Repairs and maintenance: switch to Full amount."),
    _e("NC", "North Carolina", BASE_NINGUNA, "7.10", nota="Real property contracts (remodeling) are not taxed. Repair, maintenance and installation services are — switch to Full amount for that work."),
    _e("ND", "North Dakota", BASE_NINGUNA, "7.09"),
    _e("OH", "Ohio", BASE_NINGUNA, "7.29", nota="Items that remain tangible personal property after installation (e.g., carpeting) are a retail sale — see Ohio Adm. Code 5703-9-14."),
    _e("OK", "Oklahoma", BASE_NINGUNA, "9.06"),
    _e("OR", "Oregon", BASE_NINGUNA, "0", nota="Oregon has no sales tax."),
    _e("PA", "Pensilvania", BASE_NINGUNA, "6.34"),
    _e("RI", "Rhode Island", BASE_NINGUNA, "7.00"),
    _e("SC", "South Carolina", BASE_NINGUNA, "7.49"),
    _e("SD", "South Dakota", BASE_BRUTOS, "2.00", nombre_impuesto="Contractor's excise tax", nota="The 2% contractor's excise tax applies to the full contract price. Construction services are exempt from sales tax, and you still pay sales or use tax on materials."),
    _e("TN", "Tennessee", BASE_NINGUNA, "9.61"),
    _e("TX", "Texas", BASE_NINGUNA, "8.20", nota="Residential remodeling labor is exempt and, under a lump-sum contract, you pay tax on the materials. Nonresidential repair or remodeling: switch to Full amount. Separated contracts: Materials only. See Comptroller Publication 94-116."),
    _e("UT", "Utah", BASE_NINGUNA, "7.42"),
    _e("VT", "Vermont", BASE_NINGUNA, "6.43"),
    _e("VA", "Virginia", BASE_NINGUNA, "5.77"),
    _e("WA", "Washington", BASE_COMPLETA, "9.57", nota="Retailing construction: charge retail sales tax on the full contract price. The B&O tax is separate and is not shown on this document."),
    _e("WV", "West Virginia", BASE_NINGUNA, "6.60", nota="Work that results in a capital improvement is 'contracting' and is not taxed. Other services to property are taxable — switch to Full amount (TSD-310)."),
    _e("WI", "Wisconsin", BASE_NINGUNA, "5.72"),
    _e("WY", "Wyoming", BASE_NINGUNA, "5.39"),
)

_ESTADO_POR_CODIGO = {e.codigo: e for e in ESTADOS_EEUU}

CODIGOS_ESTADO_EEUU: tuple[str, ...] = tuple(e.codigo for e in ESTADOS_EEUU)


def estado_por_codigo(codigo) -> EstadoEEUU | None:
    return _ESTADO_POR_CODIGO.get(str(codigo or "").strip().upper())


# ─────────────────────────────────────────────────────────────────────────────
# Reparto materiales / mano de obra y base gravada
# ─────────────────────────────────────────────────────────────────────────────

def estimar_venta_materiales(base_obra, base_productos, coste_materiales, coste_obra) -> Decimal:
    """Precio de venta estimado de los materiales dentro de la base.

    La parte de obra se reparte con la proporción del coste
    (``coste_materiales / coste_obra``): los materiales cargan con el
    mismo margen medio que el resto de la obra. La venta de productos
    cuenta íntegra como materiales. Sin coste de obra informado la
    estimación es 0 — no se inventa un reparto — y quien llama avisa.
    """
    obra = _d(base_obra)
    productos = _d(base_productos)
    cm = _d(coste_materiales)
    co = _d(coste_obra)
    venta = productos
    if co > 0 and cm > 0 and obra > 0:
        venta += obra * cm / co
    total = obra + productos
    if venta > total:
        venta = total
    if venta < 0:
        venta = _CERO
    return venta.quantize(_CENT)


def base_gravada_eeuu(modo, base, venta_materiales, fraccion=_UNO) -> Decimal:
    """Base sobre la que se aplica el tipo, según el modo elegido."""
    base = _d(base)
    if base < 0:
        base = _CERO
    modo = str(modo or BASE_SIN_MOTOR).strip()
    if modo == BASE_NINGUNA:
        return _CERO
    if modo == BASE_MATERIALES:
        venta = _d(venta_materiales)
        return min(max(venta, _CERO), base).quantize(_CENT)
    if modo == BASE_MANO_OBRA:
        venta = _d(venta_materiales)
        return (base - min(max(venta, _CERO), base)).quantize(_CENT)
    if modo == BASE_BRUTOS:
        fraccion = _d(fraccion)
        if fraccion < 0:
            fraccion = _CERO
        if fraccion > 1:
            fraccion = _UNO
        return (base * fraccion).quantize(_CENT)
    # `full` y, defensivamente, cualquier valor desconocido ya saneado:
    # el comportamiento genérico de siempre (base completa).
    return base.quantize(_CENT)


# ─────────────────────────────────────────────────────────────────────────────
# Resultado
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class FiscalidadEEUU:
    """Consecuencia documental del «sales tax» estatal.

    Al contrario que el CIS/RCT —retenciones que se descuentan de lo que
    cobra el subcontratista—, este impuesto es **el** impuesto del
    documento: ``impuesto_importe`` es la misma cifra que el motor de
    totales ya sumó a la base, y aquí viajan su etiqueta, su leyenda y
    los avisos. ``total_a_cobrar`` = base + impuesto.
    """

    #: ``False`` si el documento no es estadounidense o no lleva modo:
    #: el llamador sigue con su presentación de siempre.
    aplica: bool = False

    estado_codigo: str = ""
    estado_nombre: str = ""
    modo: str = BASE_SIN_MOTOR
    tipo_pct: Decimal = _CERO
    #: Nombre del tributo («Sales tax», «Gross receipts tax»…).
    nombre_impuesto: str = "Sales tax"
    #: Importe de la base que el tipo grava.
    base_gravada: Decimal = _CERO
    #: Precio de venta estimado de los materiales (modos con reparto).
    venta_materiales: Decimal = _CERO
    impuesto_importe: Decimal = _CERO
    total_a_cobrar: Decimal = _CERO
    #: Leyenda para el cliente (PDF/detalle), en inglés.
    leyenda: str = ""
    #: Avisos para el emisor: bifurcaciones del estado y datos que faltan.
    avisos: tuple[str, ...] = field(default_factory=tuple)

    @property
    def sin_impuesto_al_cliente(self) -> bool:
        return self.aplica and self.modo == BASE_NINGUNA


# ─────────────────────────────────────────────────────────────────────────────
# Cálculo
# ─────────────────────────────────────────────────────────────────────────────

def calcular_fiscalidad_eeuu(
    *,
    pais_codigo: str | None,
    base_imponible,
    venta_materiales=_CERO,
    base_gravada=None,
    tipo_pct=_CERO,
    us_tax_base: str | None = BASE_SIN_MOTOR,
    estado_codigo: str | None = "",
    us_tax_fraccion=_UNO,
) -> FiscalidadEEUU:
    """Aplica el modo de base estadounidense a un documento.

    ``venta_materiales`` la estima quien llama con
    :func:`estimar_venta_materiales`. ``base_gravada`` permite inyectar
    la base congelada de una factura (el documento emitido no se
    recalcula aunque cambie el presupuesto).

    Devuelve ``aplica=False`` fuera de EE. UU. o sin modo elegido, para
    que el llamador pueda invocarla siempre sin preguntar antes.
    """
    if str(pais_codigo or "").strip().upper() != "US":
        return FiscalidadEEUU(aplica=False)

    modo = str(us_tax_base or BASE_SIN_MOTOR).strip()
    if modo not in BASES_US or modo == BASE_SIN_MOTOR:
        return FiscalidadEEUU(aplica=False)

    base = _d(base_imponible)
    if base < 0:
        base = _CERO
    venta = _d(venta_materiales)
    tipo = _d(tipo_pct)
    if tipo < 0:
        tipo = _CERO
    fraccion = _d(us_tax_fraccion)
    if fraccion < 0:
        fraccion = _CERO
    if fraccion > 1:
        fraccion = _UNO

    estado = estado_por_codigo(estado_codigo)
    avisos: list[str] = []

    if estado is None:
        avisos.append(
            "No job state selected: sales tax follows the state where the "
            "work is performed, so pick it before sending this document."
        )

    if base_gravada is not None:
        gravada = _d(base_gravada)
        if gravada < 0:
            gravada = _CERO
        if gravada > base:
            gravada = base
        gravada = gravada.quantize(_CENT)
    else:
        gravada = base_gravada_eeuu(modo, base, venta, fraccion)

    if modo in BASES_CON_REPARTO and base > 0 and venta <= 0 and base_gravada is None:
        avisos.append(
            "No material costs are on file for this estimate, so the "
            "materials/labor split could not be estimated. Add costs to "
            "the line items or set the tax base manually."
        )

    if modo != BASE_NINGUNA and tipo <= 0 and estado is not None and estado.tipo_medio > 0:
        avisos.append(
            f"The tax rate is 0%. The average combined rate in "
            f"{estado.nombre} is about {estado.tipo_medio.normalize()}% — "
            "set the exact rate for the job address."
        )

    impuesto = (gravada * tipo / Decimal("100")).quantize(_CENT)
    nombre_impuesto = estado.nombre_impuesto if estado else "Sales tax"
    st = estado.codigo if estado else ""
    pct_txt = f"{tipo.normalize()}"

    if modo == BASE_NINGUNA:
        if estado is not None and estado.tipo_medio <= 0:
            leyenda = f"{estado.nombre} has no statewide sales tax."
        else:
            leyenda = (
                "No sales tax is charged on this contract. Sales tax on "
                "materials was paid by the contractor when purchased."
            )
    elif modo == BASE_MATERIALES:
        leyenda = f"{nombre_impuesto} ({st} {pct_txt}%) applies to materials only."
    elif modo == BASE_MANO_OBRA:
        leyenda = f"{nombre_impuesto} ({st} {pct_txt}%) applies to labor only."
    elif modo == BASE_BRUTOS:
        if fraccion < 1:
            pct_base = (fraccion * 100).normalize()
            leyenda = f"{nombre_impuesto} ({st} {pct_txt}%) on {pct_base}% of the contract amount."
        else:
            leyenda = f"{nombre_impuesto} ({st} {pct_txt}%) on the full contract amount."
    else:  # BASE_COMPLETA
        leyenda = f"{nombre_impuesto} ({st} {pct_txt}%) applies to the full contract amount (materials and labor)."

    if estado is not None and estado.nota:
        avisos.append(estado.nota)

    return FiscalidadEEUU(
        aplica=True,
        estado_codigo=st,
        estado_nombre=estado.nombre if estado else "",
        modo=modo,
        tipo_pct=tipo,
        nombre_impuesto=nombre_impuesto,
        base_gravada=gravada,
        venta_materiales=venta.quantize(_CENT),
        impuesto_importe=impuesto,
        total_a_cobrar=(base + impuesto).quantize(_CENT),
        leyenda=leyenda,
        avisos=tuple(avisos),
    )
