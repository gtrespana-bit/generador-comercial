"""Fiscalidad británica del presupuesto: CIS e inversión del sujeto pasivo.

Por qué existe este módulo
--------------------------
En el Reino Unido, cobrar una obra no es «precio + IVA». Hay dos reglas que
cambian el importe que llega a la cuenta y que no existen en ningún otro
mercado de CotizaT:

1. **CIS** (Construction Industry Scheme). El contratista retiene un 20 % o un
   30 % de lo que paga al subcontratista y lo ingresa en Hacienda a cuenta del
   impuesto de este. La retención NO se calcula sobre la factura, sino sobre el
   elemento de mano de obra: se descuenta antes el coste de los materiales que
   el subcontratista compró.

2. **Inversión del sujeto pasivo** (VATA 1994 s. 55A). Desde el 1 de marzo de
   2021, el subcontratista que factura a un contratista no añade IVA: lo
   declara el cliente. La factura va sin IVA y con una leyenda obligatoria.

Las dos reglas son del Reino Unido y solo del Reino Unido. Irlanda, Australia,
Canadá y Estados Unidos no las tienen, así que nada de esto se aplica a otros
mercados por mucho que compartan idioma.

Lo que NO hace este módulo
--------------------------
No decide si el cliente es o no usuario final ni si el tipo es el 20 % o el
30 %: eso lo dice Hacienda al verificar al subcontratista y lo confirma el
cliente por escrito. Aquí se aplica la consecuencia de esa decisión, que ya se
ha tomado fuera, y se avisa de lo que falta por confirmar.

Todas las cantidades son ``Decimal`` y entran y salen en la moneda del
documento (libras en el mercado británico).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

# ─────────────────────────────────────────────────────────────────────────────
# Constantes normativas
# ─────────────────────────────────────────────────────────────────────────────

#: Tipos de retención CIS. Los fija Hacienda al verificar al subcontratista:
#: 0 % con *Gross Payment Status*, 20 % registrado y verificado, 30 % si no
#: consta registro o no se puede verificar. No los elige el contratista.
TIPOS_CIS: tuple[Decimal, ...] = (Decimal("0"), Decimal("20"), Decimal("30"))

TIPO_CIS_NO_REGISTRADO = Decimal("30")

IVA_ESTANDAR_GB = Decimal("20")
IVA_REDUCIDO_GB = Decimal("5")

#: ``""`` significa «la regla normal del país» y deja el documento como estaba,
#: así que ningún presupuesto ya emitido cambia de aspecto al desplegar.
TRATAMIENTO_NORMAL = ""
TRATAMIENTO_ESTANDAR = "estandar"
TRATAMIENTO_INVERSION = "inversion_sujeto_pasivo"
TRATAMIENTOS_IVA: tuple[str, ...] = (
    TRATAMIENTO_NORMAL, TRATAMIENTO_ESTANDAR, TRATAMIENTO_INVERSION,
)

#: Leyendas aceptadas por Hacienda. Basta una, pero la expresión «reverse
#: charge» tiene que aparecer en la factura.
LEYENDA_INVERSION = "Reverse charge: VAT Act 1994 Section 55A applies"

_CERO = Decimal("0")


def _d(valor) -> Decimal:
    if valor is None:
        return _CERO
    if isinstance(valor, Decimal):
        return valor
    return Decimal(str(valor))


# ─────────────────────────────────────────────────────────────────────────────
# Resultado
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class FiscalidadGB:
    """Consecuencia económica y documental de las reglas británicas.

    Los importes son los que ve el cliente y los que se cobran, no los
    internos: ``total_a_cobrar`` es lo que efectivamente se ingresa.
    """

    #: ``False`` si el documento no es británico: el llamador debe ignorar el
    #: resto y seguir con su cálculo de siempre.
    aplica: bool = False

    # IVA
    iva_tratamiento: str = TRATAMIENTO_NORMAL
    #: Porcentaje que se aplicaría si no hubiera inversión. Sirve para
    #: informar del importe que el cliente declarará, aunque no se cobre.
    iva_pct: Decimal = _CERO
    #: IVA realmente añadido al documento. Cero con inversión del sujeto pasivo.
    iva_importe: Decimal = _CERO
    #: IVA que el cliente declara por su cuenta. Cero sin inversión.
    iva_invertido: Decimal = _CERO
    leyenda_iva: str = ""

    # CIS
    cis_aplica: bool = False
    cis_tipo: Decimal = _CERO
    #: Elemento de mano de obra: base imponible menos el coste de materiales.
    base_cis: Decimal = _CERO
    #: Coste de materiales que se excluye de la retención. Es coste, no venta:
    #: el margen sobre los materiales sí tributa, como el resto de la obra.
    materiales_excluidos: Decimal = _CERO
    retencion_cis: Decimal = _CERO

    #: Lo que se cobra: base + IVA − retención CIS.
    total_a_cobrar: Decimal = _CERO

    #: Avisos de cumplimiento: lo que falta por confirmar antes de emitir.
    avisos: tuple[str, ...] = field(default_factory=tuple)

    @property
    def con_inversion_sujeto_pasivo(self) -> bool:
        return self.aplica and self.iva_tratamiento == TRATAMIENTO_INVERSION


# ─────────────────────────────────────────────────────────────────────────────
# Inversión del sujeto pasivo: ¿procede?
# ─────────────────────────────────────────────────────────────────────────────

def inversion_sujeto_pasivo_procede(
    *,
    servicio_dentro_de_cis: bool,
    cliente_con_iva: bool,
    cliente_registrado_cis: bool,
    tipo_no_exento: bool,
    cliente_es_usuario_final: bool = False,
    notificacion_escrita: bool = False,
) -> tuple[bool, tuple[str, ...]]:
    """Decide si procede la inversión del sujeto pasivo y explica por qué.

    Se exige que se cumplan TODAS las condiciones. La que más se escapa es la
    del usuario final: si el cliente lo es pero no lo ha notificado por
    escrito, la inversión se aplica igualmente. Es decir, la inversión es la
    regla por defecto y el usuario final es una excepción que hay que invocar.
    """
    motivos: list[str] = []

    if not servicio_dentro_de_cis:
        motivos.append(
            "El servicio no está dentro del ámbito del CIS: se factura con IVA normal."
        )
    if not cliente_con_iva:
        motivos.append(
            "El cliente no está registrado a efectos del IVA: se factura con IVA normal."
        )
    if not cliente_registrado_cis:
        motivos.append(
            "El cliente no está registrado en el CIS: se factura con IVA normal."
        )
    if not tipo_no_exento:
        motivos.append(
            "El servicio es exento (tipo 0 %): la inversión no se aplica."
        )
    if cliente_es_usuario_final and notificacion_escrita:
        motivos.append(
            "El cliente es usuario final y lo ha notificado por escrito: "
            "se factura con IVA normal."
        )

    if motivos:
        return False, tuple(motivos)

    avisos: list[str] = []
    if cliente_es_usuario_final and not notificacion_escrita:
        avisos.append(
            "El cliente dice ser usuario final, pero sin notificación escrita "
            "se aplica la inversión del sujeto pasivo igualmente."
        )
    return True, tuple(avisos)


# ─────────────────────────────────────────────────────────────────────────────
# Cálculo
# ─────────────────────────────────────────────────────────────────────────────

def calcular_fiscalidad_gb(
    *,
    pais_codigo: str | None,
    base_imponible,
    coste_materiales,
    iva_pct,
    iva_tratamiento: str | None = TRATAMIENTO_NORMAL,
    cis_tipo=None,
) -> FiscalidadGB:
    """Aplica CIS e inversión del sujeto pasivo a un documento británico.

    ``base_imponible`` es la base ya con descuento y sin IVA. ``coste_materiales``
    es el COSTE de los materiales, no su precio de venta: Hacienda excluye el
    coste en que incurrió el subcontratista, y el margen sobre los materiales
    sigue sujeto a retención igual que la mano de obra.

    Devuelve una ``FiscalidadGB`` con ``aplica=False`` para cualquier mercado
    que no sea el británico, para que el llamador pueda invocarla siempre sin
    tener que preguntar antes.
    """
    if str(pais_codigo or "").strip().upper() != "GB":
        return FiscalidadGB(aplica=False)

    base = _d(base_imponible)
    materiales = _d(coste_materiales)
    if materiales < 0:
        materiales = _CERO
    # El coste de materiales no puede superar la base: si los datos están mal,
    # se excluye como mucho la base entera y la retención queda a cero.
    if materiales > base:
        materiales = base

    tratamiento = str(iva_tratamiento or TRATAMIENTO_NORMAL).strip()
    if tratamiento not in TRATAMIENTOS_IVA:
        tratamiento = TRATAMIENTO_NORMAL

    tipo_iva = _d(iva_pct)
    if tipo_iva < 0:
        tipo_iva = _CERO

    avisos: list[str] = []

    # ── IVA ──────────────────────────────────────────────────────────────────
    if tratamiento == TRATAMIENTO_INVERSION:
        iva_importe = _CERO
        iva_invertido = (base * tipo_iva / Decimal("100")).quantize(Decimal("0.01"))
        leyenda = LEYENDA_INVERSION
    else:
        iva_importe = (base * tipo_iva / Decimal("100")).quantize(Decimal("0.01"))
        iva_invertido = _CERO
        leyenda = ""
        if tratamiento == TRATAMIENTO_ESTANDAR and tipo_iva not in (
            IVA_ESTANDAR_GB, IVA_REDUCIDO_GB, _CERO
        ):
            avisos.append(
                f"Tipo de IVA {tipo_iva.normalize()} % inhabitual en el Reino Unido; "
                "revíselo antes de emitir."
            )

    # ── CIS ──────────────────────────────────────────────────────────────────
    # La retención se calcula sobre el importe SIN IVA y descontando el coste
    # de los materiales. Aplicarla sobre la factura entera es el error clásico
    # y sale caro: retiene de más al subcontratista.
    cis_aplica = cis_tipo is not None
    base_cis = _CERO
    retencion = _CERO
    tipo_cis = _CERO

    if cis_aplica:
        tipo_cis = _d(cis_tipo)
        if tipo_cis not in TIPOS_CIS:
            avisos.append(
                f"Tipo de retención CIS {tipo_cis.normalize()} % no válido; "
                "Hacienda solo admite 0 %, 20 % y 30 %."
            )
            tipo_cis = _CERO
        base_cis = base - materiales
        retencion = (base_cis * tipo_cis / Decimal("100")).quantize(Decimal("0.01"))
        if tipo_cis == TIPO_CIS_NO_REGISTRADO:
            avisos.append(
                "Retención del 30 %: corresponde a un subcontratista sin "
                "registro CIS verificable. Pídale que se registre y le "
                "verifiquen; mientras tanto, Hacienda le exigirá a usted la "
                "diferencia si aplica el 20 %."
            )
        if materiales <= _CERO and base > _CERO:
            avisos.append(
                "No consta coste de materiales, así que la retención se "
                "calcula sobre el importe íntegro. Si el subcontratista "
                "aportó materiales, hay que descontarlos."
            )

    total_a_cobrar = base + iva_importe - retencion

    return FiscalidadGB(
        aplica=True,
        iva_tratamiento=tratamiento,
        iva_pct=tipo_iva,
        iva_importe=iva_importe,
        iva_invertido=iva_invertido,
        leyenda_iva=leyenda,
        cis_aplica=cis_aplica,
        cis_tipo=tipo_cis,
        base_cis=base_cis,
        materiales_excluidos=materiales,
        retencion_cis=retencion,
        total_a_cobrar=total_a_cobrar,
        avisos=tuple(avisos),
    )
