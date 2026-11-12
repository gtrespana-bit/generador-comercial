"""Escenarios comerciales locales para las páginas de software de LATAM.

No son estudios de mercado ni asesoría fiscal. Son ejemplos de cómo preparar
una propuesta privada; las cifras y obligaciones deben verificarse en cada obra.
"""

ESCENARIOS = {
    "MX": (
        "De catálogo de conceptos a cotización en México",
        "Para cotizar un aplanado, separa preparación, superficie y acabado en conceptos medibles. Registra cantidades en m² y revisa en el APU las horas, el mortero y las herramientas antes de decidir el precio en pesos. Si el cliente cambia el acabado, compara una nueva propuesta con la enviada en lugar de modificar el alcance sin explicarlo.",
        "El RFC identifica a la empresa en el presupuesto comercial; ese PDF no es un CFDI ni incluye timbrado. Si la obra exige un formato de licitación o una matriz específica, comprueba sus requisitos por separado.",
    ),
    "CO": (
        "Presupuestar pañete sin confundir APU y AIU",
        "Separa la medición del pañete de los recursos que cuesta ejecutarlo: mezcla, horas de oficial y ayudante y equipo. Revisa el rendimiento real de la cuadrilla y los precios en COP antes de aplicar tu margen comercial. Documenta si protección, reparación y pintura forman parte de la oferta.",
        "Un margen interno no equivale a un AIU contractual. Si el contrato exige administración, imprevistos y utilidad o un tratamiento tributario específico, revísalos con un profesional. El presupuesto con NIT no es una factura electrónica DIAN.",
    ),
    "PE": (
        "Del metrado de tarrajeo a una propuesta en Perú",
        "Mide muros, cielos y vanos por separado y deja constancia del criterio de descuento. Luego estudia el coste por m² de tarrajeo con los consumos y las horas de tu equipo; el metrado determina cantidades, no el rendimiento de la cuadrilla. Contrasta los insumos en soles con proveedores antes de enviar.",
        "El RUC y el IGV del documento comercial no sustituyen un comprobante SUNAT. Si se necesita un expediente de obra pública o un formato normativo, verifica sus condiciones fuera de esta cotización.",
    ),
    "CL": (
        "Una cotización de terminaciones en Chile",
        "En una remodelación de departamento, separa estuco, pintura, cielo y guardapolvos para que un cambio de terminación no altere silenciosamente toda la oferta. Indica si están incluidos protección de espacios comunes, traslado y retiro de escombros; revisa las cantidades y el total en CLP.",
        "El presupuesto puede identificar a la empresa mediante su RUT. La configuración del impuesto debe revisarse para cada operación: el PDF comercial no es una factura electrónica del SII ni un estado de pago normativo.",
    ),
    "AR": (
        "Cotizar revoque cuando cambian los costes en Argentina",
        "Distingue revoque grueso, fino y reparaciones, y registra los precios de materiales y mano de obra en pesos con su fecha de referencia. Cuando un proveedor actualice un insumo, revisa el efecto sobre las partidas afectadas, no supongas que toda la obra cambia en el mismo porcentaje.",
        "Aclara vigencia y alcance en cada propuesta y conserva la versión enviada antes de emitir otra. El CUIT identifica a la empresa, pero el presupuesto no es una factura ARCA ni una fórmula contractual de redeterminación.",
    ),
    "VE": (
        "Presupuesto de friso en Venezuela: alcance y moneda",
        "Mide los paños y separa preparación, friso y pintura si se contratan de manera independiente. El cuadro base del producto usa USD como referencia interna; confirma la tarifa actual de tu cuadrilla y los precios de materiales antes de usarla para vender.",
        "Si acuerdas presentar importes en bolívares, documenta la tasa utilizada y su fecha según el acuerdo aplicable. Un cambio de tasa no corrige el rendimiento de obra. El presupuesto con RIF no sustituye una factura fiscal.",
    ),
    "EC": (
        "Enlucido y presupuesto en dólares en Ecuador",
        "Separa el enlucido de paredes del trabajo en tumbados y especifica preparación y espesor. Usa cantidades medidas y precios de proveedores ecuatorianos en USD; compartir moneda con otro país no convierte sus costes en una referencia local.",
        "Revisa qué incluye la cuadrilla y el tratamiento del impuesto antes de enviar. El RUC en el PDF comercial no lo convierte en una factura electrónica SRI ni resuelve las obligaciones laborales de la obra.",
    ),
    "DO": (
        "De la cubicación al presupuesto en República Dominicana",
        "Conserva las dimensiones y el criterio de cubicación por ambiente antes de asignar precios a cada partida. Distingue trabajos incluidos, alternativas y retiro de residuos para que el cliente pueda comparar el alcance, no solo el total en pesos dominicanos.",
        "Revisa el ITBIS y las condiciones aplicables con tu asesor. Identificar la empresa en una propuesta no convierte el documento comercial en comprobante fiscal ni sustituye una revisión del contrato.",
    ),
    "PA": (
        "Cotización de repello en Panamá",
        "En una reforma, describe superficie, espesor y preparación del repello por separado de pintura y reparaciones. Calcula los recursos por unidad con costes en USD de tu equipo y proveedores; incorpora acceso, transporte o protección cuando correspondan a esa obra.",
        "El total del presupuesto es una oferta comercial. Confirma el tratamiento del ITBMS para la operación y no presentes el PDF como factura fiscal o documento de licitación homologado.",
    ),
    "CR": (
        "Presupuesto de remodelación en colones",
        "Para comparar alternativas en Costa Rica, detalla partidas de repello, acabados e instalaciones con cantidades y precios en CRC. Explica si el acarreo, la protección y el retiro de residuos están incluidos; dos presupuestos con el mismo total pueden cubrir trabajos distintos.",
        "Comprueba costes y vigencia con tus proveedores y revisa el impuesto aplicable con tu asesor. La propuesta comercial no sustituye una factura electrónica ni acredita cumplimiento de requisitos profesionales.",
    ),
    "GT": (
        "Block y repello en una propuesta en Guatemala",
        "Separa la pared de block del repello: pueden tener unidades, consumos y rendimientos distintos. Mide cada alcance, revisa el precio de materiales y cuadrilla en quetzales y aclara si transporte y desperdicio están incluidos antes de presentar el total.",
        "Incluye los datos de identificación que correspondan y revisa el impuesto de la operación. Un presupuesto en GTQ no es una factura electrónica FEL ni reemplaza la revisión técnica de la obra.",
    ),
    "HN": (
        "Cotizar pared de bloque y repello en Honduras",
        "Calcula por separado mampostería y repello, con cantidades medidas y recursos en lempiras. Define si la oferta incluye preparación, acabados y transporte; revisa las horas de cuadrilla según las condiciones de acceso, en vez de copiar un precio cerrado de otra obra.",
        "Deja por escrito la vigencia y las exclusiones. La identificación fiscal y el impuesto configurado en un presupuesto comercial no lo convierten en factura ni determinan las obligaciones de la empresa.",
    ),
    "SV": (
        "Presupuesto de repello en El Salvador",
        "Aunque el presupuesto se exprese en USD, consulta precios y costes de cuadrilla de El Salvador para la obra concreta. Separa preparación, repello y pintura, y comprueba si el precio incluye traslados, equipo y protección de áreas ocupadas.",
        "Registra cantidades y cambios antes de emitir una nueva propuesta. El PDF comercial no es un documento tributario electrónico; confirma con tu asesor el tratamiento fiscal aplicable.",
    ),
    "NI": (
        "Preparar una propuesta de repello en Nicaragua",
        "Expresa cantidades y precios en córdobas y explica qué superficie, espesor y acabado están incluidos. Convierte el rendimiento diario de cada integrante de la cuadrilla a horas por unidad antes de calcular el coste; añade materiales y equipo pertinentes sin duplicar pérdidas.",
        "Confirma precios y condiciones de pago para la fecha de la oferta. La identificación de la empresa y el impuesto del presupuesto no sustituyen un comprobante fiscal ni asesoría tributaria.",
    ),
    "UY": (
        "Presupuesto de reforma y revoque en Uruguay",
        "Separa revoque, pintura y terminaciones para que el cliente pueda cambiar una sin perder el detalle de las demás. Revisa superficie, preparación y costes de cuadrilla en pesos uruguayos, además de acceso y retiro de escombros cuando afecten la obra.",
        "Una propuesta comercial con datos de la empresa no es una factura electrónica ni liquida aportes laborales. Verifica las condiciones fiscales y contractuales correspondientes antes del envío.",
    ),
    "PY": (
        "Presupuesto de revoque en guaraníes",
        "Detalla soporte, espesor y acabado y mide el revoque separado de las reparaciones. Comprueba las unidades de compra y las horas de cuadrilla en PYG. Conserva la precisión del cálculo interno aunque el importe visible se redondee para la propuesta.",
        "Aclara los trabajos excluidos y la vigencia de los precios consultados. El documento comercial no es una factura electrónica ni determina por sí solo el tratamiento del impuesto.",
    ),
    "BO": (
        "Del cómputo métrico al presupuesto en Bolivia",
        "Anota dimensiones y cantidades por partida antes de valorar el revoque u otros trabajos. El cómputo no aporta por sí solo consumos ni rendimientos: comprueba mezcla, horas de cuadrilla y equipo y después revisa el total en bolivianos.",
        "Deja identificados alcance, exclusiones y vigencia para comparar futuras versiones. El presupuesto comercial no sustituye factura fiscal ni un expediente normativo de contratación pública.",
    ),
}


def bloques_comerciales(codigo: str) -> list[tuple[str, str]]:
    escenario = ESCENARIOS.get(str(codigo or "").upper())
    if not escenario:
        return []
    titulo, ejemplo, limites = escenario
    return [(titulo, ejemplo), ("Alcance del documento comercial", limites)]
