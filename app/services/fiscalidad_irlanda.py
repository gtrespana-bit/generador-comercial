"""Fiscalidad de la construcción en Irlanda: RCT e inversión del sujeto pasivo.

Dos reglas que un constructor irlandés se encuentra en casi cada factura y
que una aplicación de otro país pasa por alto:

1. **Relevant Contracts Tax (RCT)** — la retención sobre los pagos de los
   contratistas principales a sus subcontratistas (construcción, silvicultura
   y procesado de carne). Los tipos son el 0 %, el 20 % y el 35 %, y no los
   elige nadie del sector: los fija Revenue según el historial fiscal del
   subcontratista y los confirma en la autorización de deducción
   («Deduction Authorisation») que emite en ROS para cada pago. El
   contratista principal tiene que notificar el contrato y **cada pago
   antes de pagarlo**; pagar sin autorización se sanciona con un porcentaje
   del pago que puede llegar al 35 %. La diferencia decisiva frente al CIS
   británico: el RCT se calcula sobre **el importe íntegro sin IVA,
   materiales incluidos**. En el Reino Unido solo se retiene sobre la mano
   de obra; en Irlanda, si cualquier parte del contrato es una operación
   relevante, todos los pagos del contrato están sujetos a RCT («overall
   contract rule»). Descontar los materiales aquí — la costumbre británica —
   retendría de menos en cada factura.

2. **Inversión del sujeto pasivo del IVA** («reverse charge», s. 16(3) de la
   VAT Consolidation Act 2010) — en los servicios de construcción entre un
   subcontratista y un contratista principal, cuando la operación exige
   aplicar RCT (y también entre personas vinculadas), el subcontratista no
   carga IVA: lo declara el contratista principal. La factura tiene que
   llevar el número de IVA del subcontratista y la leyenda «VAT on this
   supply to be accounted for by the Principal Contractor». A un cliente
   particular se le carga IVA normal, al 13,5 % reducido de la construcción.

A ello se suma la **regla de los dos tercios** («two-thirds rule», s. 16(5)):
cuando el IVA es normal y el coste de los bienes incorporados supera los dos
tercios del precio total, toda la operación tributa al tipo de los bienes
(normalmente el 23 %) y no al 13,5 %. El programa no cambia el tipo por su
cuenta — Revenue mide los bienes a su coste para el proveedor, y la cifra
que sale de los análisis de precios es una aproximación sin IVA soportado —
pero lo avisa, porque es exactamente el error que un constructor que factura
suministro e instalación comete sin enterarse.

Este módulo es el equivalente irlandés de :mod:`fiscalidad_reino_unido` y
sigue su misma disciplina: la aplicación **no decide** el tipo de RCT ni si
procede la inversión (eso lo decide Revenue, o lo comprueba el constructor
con su cliente); aplica las consecuencias de la decisión ya tomada y avisa
de lo incoherente. Que el RCT irlandés se parezca al CIS no basta para
reutilizar su código: las bases son opuestas (importe íntegro frente a solo
mano de obra) y compartir el cálculo sería retener mal en uno de los dos
países. Sí se comparte el campo ``iva_tratamiento`` del documento, porque la
elección «IVA normal / inversión del sujeto pasivo» es la misma pregunta en
los dos mercados; la retención, en cambio, tiene su propio campo
(``rct_tipo``) para que ningún documento irlandés herede un tipo británico.

Fuentes: Revenue Ireland — «Relevant Contracts Tax (RCT)»
(revenue.ie/en/self-assessment-and-self-employment/rct/), Tax and Duty
Manuals Part 18-02-01/18-02-04 y «VAT Treatment of construction services»
(VATCA 2010, ss. 16(3), 16(5) y 41(4)); contrastado con guías de Baker
Tilly, Grant Thornton y Coffey & Co. Verificado el 19-10-2026. La
documentación de Revenue prevalece sobre este resumen.
"""
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP

# Los únicos tres tipos de RCT que existen. Revenue asigna el tipo según el
# historial fiscal del subcontratista: 0 % si lleva tres años al día,
# 20 % el estándar de un subcontratista registrado y 35 % si no está
# registrado o arrastra incumplimientos. Un tipo distinto no es una
# elección válida: es un error, y este módulo lo trata como tal en vez de
# aplicarlo.
TIPOS_RCT = (Decimal("0"), Decimal("20"), Decimal("35"))

TIPO_RCT_SIN_REGISTRO = Decimal("35")
TIPO_RCT_ESTANDAR = Decimal("20")

# Tipo reducido de los servicios de construcción y de los bienes que Revenue
# asimila (hormigón listo para verter y bloques de hormigón). Todo lo demás
# —materiales, andamios, herrajes— tributa al estándar del 23 %.
IVA_CONSTRUCCION_IE = Decimal("13.5")
IVA_ESTANDAR_IE = Decimal("23")

# Tratamientos de IVA que se guardan en el documento, compartidos con el
# Reino Unido: comparten campo (``Presupuesto.iva_tratamiento``) y por tanto
# vocabulario. Cadena vacía = «sin marcar», para que los documentos ya
# emitidos sigan comportándose como siempre (IVA normal).
TRATAMIENTO_ESTANDAR = "estandar"
TRATAMIENTO_INVERSION = "inversion_sujeto_pasivo"
TRATAMIENTOS_IVA_IE = ("", TRATAMIENTO_ESTANDAR, TRATAMIENTO_INVERSION)

# Leyenda que Revenue exige en la factura del subcontratista. Sin ella —y sin
# el número de IVA— el documento no acredita la inversión del sujeto pasivo.
LEYENDA_INVERSION_IE = (
    "VAT on this supply to be accounted for by the Principal Contractor"
)


@dataclass(frozen=True)
class FiscalidadIE:
    """Resultado de aplicar el RCT y el tratamiento de IVA a un documento.

    ``aplica`` es falso fuera de Irlanda: el resto de la aplicación puede
    llamar a :func:`calcular_fiscalidad_ie` sin preguntar antes por el país,
    y un presupuesto español o británico sale intacto.
    """

    aplica: bool
    iva_tratamiento: str = ""
    iva_pct: Decimal = Decimal("0")
    iva_importe: Decimal = Decimal("0")
    # Importe de IVA que el contratista principal se autoliquida. No se cobra
    # ni entra en el total: se informa porque el cliente lo necesita para su
    # casilla T1 y porque «IVA 13,5 %: 0 €» sin explicación parece un error.
    iva_invertido: Decimal = Decimal("0")
    leyenda_iva: str = ""
    rct_aplica: bool = False
    rct_tipo: Decimal | None = None
    # Importe íntegro sin IVA: a diferencia del CIS, los materiales también
    # soportan la retención («overall contract rule»).
    base_rct: Decimal = Decimal("0")
    retencion_rct: Decimal = Decimal("0")
    # Peso de los materiales sobre la base, para la regla de los dos tercios.
    pct_materiales: Decimal = Decimal("0")
    supera_dos_tercios: bool = False
    total_a_cobrar: Decimal = Decimal("0")
    avisos: tuple[str, ...] = field(default_factory=tuple)

    @property
    def con_inversion_sujeto_pasivo(self) -> bool:
        return self.aplica and self.iva_tratamiento == TRATAMIENTO_INVERSION


def inversion_sujeto_pasivo_procede_ie(
    *,
    es_servicio_construccion: bool,
    cliente_es_contratista_principal: bool,
    operacion_sujeta_a_rct: bool,
    personas_vinculadas: bool = False,
) -> tuple[bool, tuple[str, ...]]:
    """¿Tiene que ir esta factura sin IVA, por inversión del sujeto pasivo?

    Devuelve el sí/no y los motivos cuando es no. Es la comprobación previa
    que Revenue espera que el subcontratista haga: la inversión solo procede
    en servicios de construcción (a) prestados a un contratista principal en
    una operación que exige aplicar RCT, o (b) entre personas vinculadas
    («connected persons»). A un cliente particular se le carga IVA normal,
    aunque la obra sea idéntica.

    La aplicación no sabe ninguna de estas cosas por sí sola —dependen de
    quién es el cliente y de si el contrato está notificado en ROS—, así que
    esta función ordena la decisión que toma el constructor, no la sustituye.
    """
    avisos: list[str] = []
    if not es_servicio_construccion:
        avisos.append(
            "La inversión del sujeto pasivo en Irlanda solo se aplica a "
            "servicios de construcción (s. 16(3) VATCA 2010)."
        )
        return False, tuple(avisos)
    if personas_vinculadas:
        avisos.append(
            "Entre personas vinculadas la inversión se aplica aunque el "
            "cliente no sea contratista principal, y la regla de los dos "
            "tercios no se aplica a la operación."
        )
        return True, tuple(avisos)
    if not cliente_es_contratista_principal:
        avisos.append(
            "El cliente no es contratista principal: si es un particular, "
            "esta factura lleva IVA normal (13,5 % en construcción)."
        )
        return False, tuple(avisos)
    if not operacion_sujeta_a_rct:
        avisos.append(
            "La operación no está sujeta a RCT: sin contrato relevante, el "
            "IVA es normal aunque el cliente sea contratista principal."
        )
        return False, tuple(avisos)
    return True, ()


def calcular_fiscalidad_ie(
    *,
    pais_codigo: str,
    base_imponible: Decimal,
    coste_materiales: Decimal = Decimal("0"),
    iva_pct: Decimal,
    iva_tratamiento: str = "",
    rct_tipo: Decimal | None = None,
) -> FiscalidadIE:
    """Aplica el tratamiento de IVA y la retención RCT a un documento irlandés.

    ``iva_tratamiento`` vacío reproduce el comportamiento histórico (IVA
    normal, sin retención si ``rct_tipo`` es ``None``): ningún presupuesto
    irlandés ya emitido cambia de total por llamar a esta función.

    ``coste_materiales`` **no** reduce la base del RCT —en Irlanda retiene el
    importe íntegro—; se recibe para la regla de los dos tercios: con IVA
    normal al 13,5 %, si los bienes superan dos tercios del precio, Revenue
    exige el 23 % sobre todo y este cálculo lo avisa sin tocar el tipo.
    """
    # Los llamantes (PDF, router) pasan lo que tenga el documento: Decimal
    # de los totales, float de las columnas. Se normaliza aquí, una sola vez.
    iva_pct = Decimal(str(iva_pct))
    base = _dinero(Decimal(str(base_imponible)))
    total_sin_fiscalidad = _dinero(base + base * iva_pct / Decimal("100"))

    if (pais_codigo or "").strip().upper() != "IE":
        return FiscalidadIE(
            aplica=False,
            iva_pct=iva_pct,
            iva_importe=_dinero(base * iva_pct / Decimal("100")),
            total_a_cobrar=total_sin_fiscalidad,
        )

    avisos: list[str] = []
    tratamiento = (iva_tratamiento or "").strip()
    if tratamiento not in TRATAMIENTOS_IVA_IE:
        avisos.append(
            f"Tratamiento de IVA no reconocido («{tratamiento}»): se aplica "
            "IVA normal. Los válidos son el régimen normal y la inversión "
            "del sujeto pasivo."
        )
        tratamiento = ""

    inversion = tratamiento == TRATAMIENTO_INVERSION
    iva_calculado = _dinero(base * iva_pct / Decimal("100"))
    iva_importe = Decimal("0") if inversion else iva_calculado
    iva_invertido = iva_calculado if inversion else Decimal("0")

    if inversion and iva_pct == 0:
        # Sin tipo no hay nada que el contratista principal pueda
        # autoliquidarse: casi seguro falta el 13,5 % (o el 23 %).
        avisos.append(
            "Inversión del sujeto pasivo con el tipo de IVA al 0 %: el "
            "contratista principal necesita el tipo (13,5 % en construcción) "
            "para autoliquidar el impuesto."
        )
    if tratamiento == TRATAMIENTO_ESTANDAR and iva_pct not in (
        IVA_CONSTRUCCION_IE,
        IVA_ESTANDAR_IE,
        Decimal("0"),
    ):
        avisos.append(
            f"Un IVA del {iva_pct} % no es un tipo habitual en Irlanda: los "
            "servicios de construcción van al 13,5 %, los materiales al "
            "23 %. Compruebe que no es el tipo de otro país."
        )

    # Regla de los dos tercios: solo muerde con IVA normal. Con inversión,
    # el tipo lo aplica el contratista principal al autoliquidar.
    materiales = min(max(_dinero(coste_materiales), Decimal("0")), base)
    pct_materiales = (
        (materiales / base * Decimal("100")).quantize(
            Decimal("0.1"), rounding=ROUND_HALF_UP
        )
        if base > 0
        else Decimal("0")
    )
    supera_dos_tercios = base > 0 and materiales * 3 > base * 2
    if (
        supera_dos_tercios
        and not inversion
        and iva_pct == IVA_CONSTRUCCION_IE
    ):
        avisos.append(
            "Regla de los dos tercios (s. 16(5) VATCA 2010): los materiales "
            f"son el {pct_materiales} % del importe, más de dos tercios, así "
            "que toda la operación tributa al 23 % de los bienes y no al "
            "13,5 %. Revenue valora los bienes a su coste para usted: esta "
            "cifra sale de los análisis de precios sin IVA soportado, así "
            "que revísela antes de cambiar el tipo."
        )

    rct_aplica = rct_tipo is not None
    retencion = Decimal("0")
    base_rct = Decimal("0")
    tipo_valido: Decimal | None = None
    if rct_aplica:
        rct_tipo = Decimal(str(rct_tipo))
        if rct_tipo not in TIPOS_RCT:
            # Revenue solo conoce 0, 20 y 35. Aplicar un 25 % «a ojo»
            # retendría una cantidad que nadie va a ingresar.
            avisos.append(
                f"El tipo de RCT del {rct_tipo} % no existe: Revenue solo "
                "aplica el 0 %, el 20 % o el 35 %. No se ha retenido nada."
            )
            rct_aplica = False
        else:
            tipo_valido = rct_tipo
            base_rct = base
            retencion = _dinero(base * rct_tipo / Decimal("100"))
            avisos.append(
                "El tipo definitivo lo confirma Revenue en la autorización "
                "de deducción de cada pago (ROS): el contratista principal "
                "debe notificar el contrato y el pago antes de pagar, y "
                "pagar sin autorización puede costarle hasta el 35 % del "
                "importe en sanciones."
            )
            if rct_tipo == TIPO_RCT_SIN_REGISTRO:
                avisos.append(
                    "El 35 % es el tipo de quien no está registrado o "
                    "arrastra incumplimientos: registrarse y ponerse al día "
                    "baja la retención al 20 % o al 0 %."
                )
            if not inversion:
                avisos.append(
                    "Operación sujeta a RCT facturada con IVA: entre "
                    "subcontratista y contratista principal, el IVA va por "
                    "inversión del sujeto pasivo. Cargar IVA aquí sería "
                    "cobrar un impuesto que no procede ingresar."
                )
    if inversion and not rct_aplica:
        avisos.append(
            "Inversión del sujeto pasivo sin RCT marcado: en construcción la "
            "inversión va ligada a operaciones sujetas a RCT o entre "
            "personas vinculadas. Si el cliente es un particular, el IVA es "
            "normal."
        )

    return FiscalidadIE(
        aplica=True,
        iva_tratamiento=tratamiento,
        iva_pct=iva_pct,
        iva_importe=iva_importe,
        iva_invertido=iva_invertido,
        leyenda_iva=LEYENDA_INVERSION_IE if inversion else "",
        rct_aplica=rct_aplica,
        rct_tipo=tipo_valido,
        base_rct=base_rct,
        retencion_rct=retencion,
        pct_materiales=pct_materiales,
        supera_dos_tercios=supera_dos_tercios,
        total_a_cobrar=_dinero(base + iva_importe - retencion),
        avisos=tuple(avisos),
    )


def _dinero(valor: Decimal) -> Decimal:
    """Dos decimales, redondeo comercial: lo que Revenue espera ver."""
    return Decimal(str(valor)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
