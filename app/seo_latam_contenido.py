"""Decisiones editoriales locales. No contiene precios ni tipos fiscales.

Cada mercado aporta un problema técnico y un documento distintos; los cinco
mercados con guía histórica la conservan, sin abrir otra URL para su intención.
Las hipótesis editoriales siguen pendientes de contraste GSC/SERP y revisión local.
"""
from __future__ import annotations

# Orden de ejecución del documento de estrategia, no del selector de producto.
MERCADOS = {
    "MX": {
        "slug": "mexico",
        "existente": "cotizar-remodelacion-mexico",
        "labor": "En México conviene separar jornal de albañil, coste de la empresa y destajo por concepto. Un precio por día no define cuántos metros de aplanado se ejecutan ni incluye necesariamente herramienta, traslado o prestaciones. La referencia del catálogo incorpora una estimación de coste empresa; no debe añadirse de nuevo ese mismo recargo. No se dispone aquí de una muestra independiente para CDMX, Monterrey o Guadalajara: estas cifras no son tarifas de esas ciudades.",
        "tecnica": (
            "catalogo-conceptos-apu-mexico",
            "Catálogo de conceptos y APU en México: del alcance al precio",
            "Un catálogo de conceptos no es una lista de insumos. En una cotización mexicana, el concepto describe el trabajo que compra el cliente; el análisis de precios unitarios explica lo que cuesta ejecutarlo. Separar ambos permite cambiar un aplanado sin reconstruir toda la cotización.",
            [
                ("Redactar un concepto que pueda medirse", "Escribe ubicación, soporte, acabado y unidad antes de poner precio. «Aplanado en muro interior» necesita espesor, preparación y criterio de medición; «plafón» necesita sistema, altura y remates. No juntes aplanado, pintura y zoclo en un solo metro cuadrado si después pueden contratarse por separado. La cantidad pertenece al concepto; los consumos de cemento, arena y horas pertenecen a su APU."),
                ("Del rendimiento al consumo por unidad", "Si una cuadrilla termina R m² por jornada de ocho horas, cada integrante consume 8/R horas por m². No introduzcas R como si fueran horas: invertir esa relación dispara el coste. Multiplica los consumos de materiales por sus precios MXN y suma mano de obra y equipo. Las pérdidas de material deben estar identificadas, no escondidas en un rendimiento laboral inflado."),
                ("Revisar la matriz sin prometer compatibilidad universal", "Una hoja de conceptos con precios finales no contiene un descompuesto recuperable. Si importas Excel o BC3, comprueba códigos, unidades y recursos después de la importación. CotizaT no se presenta como Neodata, un expediente de licitación ni un lector automático de planos. La cotización con RFC es un documento comercial: el CFDI y su timbrado siguen fuera de este flujo."),
            ],
        ),
    },
    "CO": {
        "slug": "colombia",
        "existente": "apu-panete-colombia",
        "labor": "En Colombia una hora de oficial no equivale al precio de venta de un metro de pañete. La referencia COP incorpora un modelo de coste empresa, no una liquidación de nómina. La situación contractual y las exenciones pueden alterar el coste real; el presupuesto debe usar los costes de la empresa que ejecutará el trabajo. El AIU no corrige un rendimiento mal calculado ni sustituye los insumos de una partida.",
        "tecnica": (
            "apu-vs-aiu-colombia",
            "APU vs AIU en Colombia: qué calcula cada uno",
            "APU y AIU no son dos nombres para el mismo cálculo. El primero descompone una unidad de obra; el segundo identifica administración, imprevistos y utilidad en un esquema contractual. Confundirlos hace que un presupuesto de remodelación parezca resolver obligaciones que nunca se han calculado.",
            [
                ("El APU responde cuánto cuesta ejecutar una unidad", "Para un pañete, el APU suma cemento, arena, horas del oficial, ayudante y equipo por m². El coste total de esa partida se obtiene multiplicando el coste unitario por la cantidad medida. Eso permite revisar una compra o un rendimiento sin atribuir toda la diferencia a un porcentaje general. Los recursos deben estar expresados en COP y unidades coherentes."),
                ("El AIU depende del contrato, no de una plantilla universal", "Administración, imprevistos y utilidad no se pueden reducir aquí a tres porcentajes válidos para cualquier obra colombiana. Su definición y tratamiento tributario requieren revisar el contrato y el régimen aplicable. Un margen comercial interno de remodelación no demuestra que se haya calculado un AIU contractual ni que el IVA deba aplicarse sobre la misma base."),
                ("Qué hacer en una cotización privada", "Conserva el APU para estudiar el coste y explica el alcance comercial al cliente. Si el encargo exige AIU, interventoría o un formato estatal, haz esa revisión con un profesional y la herramienta adecuada. CotizaT no calcula AIU de contrato estatal, no prepara pliegos SECOP y no emite factura DIAN. Añadir el NIT al PDF no transforma el documento en ninguno de ellos."),
            ],
        ),
    },
    "PE": {
        "slug": "peru",
        "existente": "metrados-peru",
        "labor": "En Perú el metrado determina cantidades, no salarios ni rendimientos. Las referencias en soles son coste empresa modelado y no una tabla salarial normativa de construcción civil. Una cifra única con mínimo y máximo iguales significa que la investigación no aporta dispersión, no que todas las cuadrillas cobren lo mismo. Verifica el régimen y la contratación antes de sustituir el coste de tu gasfitero u operario por una referencia nacional.",
        "tecnica": (
            "apu-tarrajeo-peru",
            "APU de tarrajeo en Perú: metrado, recursos y rendimiento",
            "El tarrajeo se presupuesta después de medir las superficies y definir el acabado. Un total en soles por m² sin espesor, soporte ni rendimiento no permite explicar por qué cambia el precio entre ambientes de la misma obra.",
            [
                ("Cerrar el metrado antes del precio", "Separa muros, cielos y encuentros. Registra largo y altura por ambiente y deja escrito cómo se descuentan vanos y se miden derrames. No apliques a todo el proyecto un criterio de descuento que solo acordaste para una pared. El metrado debe poder reconstruirse desde las dimensiones: si únicamente guardas un total, el siguiente cambio será una discusión sin evidencia."),
                ("Descomponer un metro cuadrado de tarrajeo", "Define preparación, espesor y mezcla antes de calcular consumos de cemento y arena. Introduce horas de operario y ayudante por m²; un rendimiento de cuadrilla en m² por jornada debe convertirse a horas por cada integrante. El transporte interno, el trabajo en altura y la protección de ambientes ocupados pueden requerir recursos o partidas propios. No se deducen solo de la superficie."),
                ("Pasar de coste en soles a documento comercial", "Revisa unidades de compra, pérdidas y precio de proveedor en PEN antes de calcular el precio de venta. El IGV del presupuesto no convierte el APU en un comprobante SUNAT. CotizaT permite trabajar con mediciones y descompuestos, pero no entrega por ello un expediente S10 ni un presupuesto normativo de obra pública. Guarda el criterio de metrado junto al alcance que recibirá el cliente."),
            ],
        ),
    },
    "CL": {
        "slug": "chile",
        "labor": "En Chile no conviene comparar el sueldo líquido de un maestro con el coste hora de una empresa. Las referencias CLP incluyen una aproximación de coste empresa y no calculan una liquidación laboral. Un gasfíter que trabaja por visita puede incluir desplazamiento y un mínimo de servicio que no aparecen en una simple hora de catálogo. El estuco en altura tampoco conserva necesariamente el rendimiento de un paño accesible.",
        "documento": (
            "plantilla-presupuesto-construccion-chile",
            "Plantilla de presupuesto en Chile (CLP)",
            "Un presupuesto en pesos chilenos debe distinguir el trabajo contratado de las decisiones todavía abiertas. Cielo falso, guardapolvo y artefactos no se deben esconder en un único importe de terminaciones si el cliente puede cambiar uno de ellos.",
            [
                ("Capítulos que permitan comparar ofertas", "Separa retiro y preparación, obra base, instalaciones y terminaciones. Cada partida necesita unidad, cantidad, precio CLP y alcance. Indica si el hormigón, la protección del edificio, el retiro de escombros y el traslado de materiales están incluidos. Dos ofertas con el mismo total no son comparables cuando una omite el acceso a un departamento o el retiro final."),
                ("RUT, pesos e impuesto sin confundir el documento", "Identifica empresa, RUT, cliente, dirección y fecha. Usa el código CLP para evitar confundir pesos con dólares y revisa los redondeos visibles. El IVA de referencia del producto no decide el tratamiento de cada obra. Este documento comercial no es una factura SII, un estado de pago normativo ni una acreditación para licitar."),
                ("Opciones y cambios en terminaciones", "Si el cliente aún elige piso o grifería, describe la opción incluida y deja las alternativas separadas. Un cambio de guardapolvo no debería alterar silenciosamente la superficie del cielo falso. Reenvía una versión identificada con alcance y total nuevos; conserva el documento anterior para poder comparar qué se aceptó y qué quedó pendiente."),
            ],
        ),
        "tecnica": (
            "apu-estuco-chile",
            "APU de estuco en Chile: horas, pérdidas y precio en CLP",
            "El estuco requiere una especificación medible, no solamente un valor por m². La mezcla, el espesor y el estado del soporte explican buena parte del consumo y del tiempo de ejecución que debe recoger el APU.",
            [
                ("Distinguir preparación y terminación", "Comprueba si el paño necesita limpieza, reparación o tratamiento de adherencia. Separa esos trabajos cuando no estén incluidos en el estuco contratado. Identifica interior, exterior y altura: un andamio y su montaje no se pagan con el mismo rendimiento de una pared a nivel de piso. El acabado debe quedar descrito para que pintar no parezca automáticamente incluido."),
                ("Consumos y cuadrilla en unidades compatibles", "El mortero puede comprarse preparado o producirse con cemento y áridos. No sumes ambas alternativas al mismo APU. Si el envase declara rendimiento, verifica espesor y soporte de esa ficha antes de trasladarlo a la obra. Calcula las horas de maestro y ayudante por m² de producción útil, con pérdidas de material explícitas y sin duplicarlas en el precio."),
                ("Cerrar CLP sin confundir coste y venta", "La suma de recursos en pesos chilenos es coste directo. Traslados, equipo y condiciones de acceso pueden modificarlo antes del margen. Revisa el total de la partida y no solo su valor unitario redondeado. Esta metodología sirve para estudiar obra privada: no constituye un análisis normativo de licitación ni certifica estados de pago."),
            ],
        ),
    },
    "AR": {
        "slug": "argentina",
        "labor": "En Argentina una referencia de septiembre no es automáticamente un precio vigente en octubre. Las horas ARS de la tabla conservan su fecha de consulta; no se actualizan con un índice inventado ni siguiendo una cotización de dólar implícita. Revisa acuerdos y costes propios antes de enviar. Cambiar la mano de obra del catálogo debe ser una decisión para una nueva propuesta, no una reescritura del PDF ya aceptado.",
        "documento": (
            "actualizar-presupuesto-obra-argentina",
            "Actualizar un presupuesto en Argentina sin perder el PDF enviado",
            "La actualización de precios en pesos argentinos exige separar catálogo vigente, propuesta enviada y cambio aceptado. Si los tres se editan como una sola hoja, deja de existir evidencia de la oferta que recibió el cliente.",
            [
                ("Anotar corte, vigencia y alcance", "Identifica la fecha de los precios y la validez comercial que acuerdas para esa propuesta. No uses una cláusula genérica como sustituto de la revisión de condiciones. Un cambio de cotización de proveedor no equivale por sí solo a un nuevo acuerdo con el cliente. Las condiciones de actualización contractual deben revisarse profesionalmente, no deducirse de un botón del programa."),
                ("Actualizar recursos antes de emitir otra versión", "Pide precios nuevos de cemento, revestimientos y jornales; registra qué insumos cambiaron y cuáles siguen confirmados. Un aumento uniforme a todo el presupuesto puede distorsionar partidas con distinta proporción de materiales y mano de obra. Recalcula el descompuesto de los trabajos que vas a volver a ofertar y revisa los productos elegidos por el cliente por separado."),
                ("Conservar lo enviado y explicar la diferencia", "No sustituyas el archivo anterior conservando el mismo nombre. Emite una nueva versión con fecha, total ARS y descripción de los cambios: precio, cantidad, producto o alcance. El CUIT identifica a la empresa; el PDF comercial no es una factura ARCA. El programa no elige un índice contractual ni aplica automáticamente un mecanismo de redeterminación de obra pública."),
            ],
        ),
        "tecnica": (
            "apu-revoque-argentina",
            "APU de revoque en Argentina con precios fechados en ARS",
            "Un APU de revoque en pesos argentinos debe poder revisarse por recurso y fecha. Un precio final copiado de otra obra no permite saber cuánto cambió el mortero, cuánto la cuadrilla y cuánto el alcance.",
            [
                ("Separar grueso, fino y reparación", "Indica si el trabajo incluye revoque grueso, fino o ambos, sobre qué soporte y con qué espesor. La reparación de un muro existente no tiene por qué rendir como un paño nuevo continuo. Los encuentros con cielorraso, zócalo y aberturas necesitan criterio de medición para no añadirlos informalmente cuando el trabajo ya está contratado."),
                ("Una fecha por referencia, no una lista eterna", "Normaliza las compras a la unidad del recurso y conserva la fecha del proveedor. Si una bolsa tiene otra presentación, compara coste por kilogramo antes de concluir que bajó el material. Las horas de oficial y ayudante deben reflejar la producción posible en esa obra. No conviertas el rendimiento en una reserva oculta para cubrir cualquier aumento futuro."),
                ("Revisar el efecto de una actualización", "Compara el APU anterior con el nuevo antes de cambiar el valor de venta. Un alza de material no se aplica necesariamente al porcentaje de equipo o a un producto que el cliente ya compró. Explica qué referencia se actualizó y mantén el PDF previo. No se ofrece aquí una tabla salarial UOCRA vigente ni una fórmula automática de redeterminación."),
            ],
        ),
    },
    "VE": {
        "slug": "venezuela",
        "existente": "presupuesto-usd-bs-venezuela",
        "labor": "Venezuela usa el cuadro base de recursos USD del producto, no la matriz nacional de coste empresa empleada por los otros dieciséis mercados. Sus tarifas internas no prueban salario, prestaciones ni una banda de mercado. Por eso no se publican como coste empresa comparable. Para cotizar friso, pide la tarifa actual de la cuadrilla y documenta qué incluye; no conviertas una referencia histórica con una supuesta tasa de hoy.",
        "tecnica": (
            "apu-friso-venezuela",
            "APU de friso en Venezuela: recursos en USD y revisión en Bs",
            "El friso se puede estudiar en dólares y presentar en la moneda acordada, pero el coste técnico y la conversión del documento son decisiones distintas. Cambiar una tasa no corrige un consumo de cemento ni un rendimiento mal estimado.",
            [
                ("Definir qué friso se está cotizando", "Separa preparación de superficie, reparación y friso nuevo. Especifica espesor, acabado, altura y condiciones de acceso. Si el presupuesto incluye pintura, déjala como partida distinta cuando su superficie o producto pueda cambiar. Mide paños y vanos con el criterio acordado; un rodapié o un encuentro de cielo raso no se resuelve solo multiplicando el área de piso."),
                ("Construir el coste sin convertir salario en tarifa", "El APU suma consumos de cemento, arena, agua, horas de oficial y ayudante y equipo necesario. Sustituye las tarifas internas por acuerdos actuales de tu cuadrilla y comprueba herramientas, traslado y prestaciones. No se atribuye a esos valores una validación salarial nacional. La pérdida de mezcla y el tiempo improductivo deben justificarse por la ejecución, no por una conversión monetaria."),
                ("Documentar moneda, tasa y revisión", "Si el documento se expresa en bolívares, identifica la tasa de referencia que corresponde al presupuesto y su fecha, según el acuerdo aplicable. No se publica una tasa de hoy ni se promete liquidación tributaria automática. Conserva la versión enviada y emite otra si cambia el alcance. El RIF del PDF no sustituye la factura fiscal venezolana."),
            ],
        ),
    },
    "EC": {
        "slug": "ecuador",
        "existente": "apu-dolares-ecuador",
        "labor": "En Ecuador los recursos de este mercado ya están en USD: no procede convertir la tabla de Panamá o El Salvador por compartir moneda. El coste empresa es un modelo distinto del salario sectorial y debe adaptarse al personal que realmente interviene. Revisa duración de la contratación, beneficios y horas productivas con tu asesor; el catálogo no liquida IESS ni certifica mínimos sectoriales vigentes.",
        "tecnica": (
            "apu-enlucido-ecuador",
            "APU de enlucido en Ecuador: consumos y cuadrilla en USD",
            "El enlucido en dólares no necesita una tasa extranjera para ser local. Necesita precios de proveedor ecuatoriano, especificación de mezcla y una cuadrilla cuyo rendimiento corresponda al soporte y al acceso reales.",
            [
                ("Medir paredes sin confundir tumbado y enlucido", "Registra las superficies verticales y horizontales por separado. El tumbado y los encuentros pueden tener sistema y unidad distintos: no los presupuestes automáticamente con el APU de pared. Identifica espesor, acabado y si se incluye preparación. La reparación de humedad o la corrección de plomos debe quedar expresamente incluida o excluida antes de cerrar la oferta."),
                ("Elegir recursos según el sistema", "Define si compras mortero preparado o si produces la mezcla con insumos separados. Usa precios por unidad compatible y anota flete y descarga cuando no estén incluidos. Las horas de oficial y ayudante dependen de la producción útil; no se obtienen dividiendo una mensualidad por cualquier número de días sin revisar la jornada y el coste empresa."),
                ("USD nativo y documento con RUC", "Comprueba que el recurso y el presupuesto están en USD antes de revisar el margen. El IVA se configura para el documento comercial; no se deduce la tributación de la palabra enlucido. CotizaT no emite factura electrónica SRI. El presupuesto debe explicar alcance, vigencia y cambios aunque el importe no necesite conversión de moneda."),
            ],
        ),
    },
    "DO": {
        "slug": "republica-dominicana",
        "labor": "En República Dominicana hay que distinguir el jornal de albañil, el destajo por block y el coste de una cuadrilla contratada. La tabla DOP no convierte esas tres modalidades en equivalentes. Un mínimo sectorial citado en la investigación histórica no demuestra la tarifa de hoy. La cubicación tampoco determina por sí sola horas o prestaciones: primero hay que definir la unidad ejecutada y después sus recursos.",
        "documento": (
            "cubicacion-presupuesto-republica-dominicana",
            "Cubicación para presupuesto en República Dominicana",
            "Antes de presupuestar una cubicación, aclara si se habla de cantidades previstas o de una valoración de trabajos ejecutados. Esta guía organiza cantidades para una oferta privada; no certifica avances, pagos ni cumplimiento de un contrato público.",
            [
                ("Acordar qué cantidad se está midiendo", "Identifica partida, ubicación, unidad y dimensiones. Un pañete se suele estudiar por superficie; un elemento de hormigón puede requerir volumen; un artefacto puede contarse por unidad. No uses un único término para ocultar esas diferencias. Si se trata de avance de obra, habrá que revisar también período, acumulado y cantidades previamente reconocidas fuera de este ejemplo comercial."),
                ("Relacionar cantidad y precio en DOP", "Para cada cantidad medida, conserva el APU o la justificación del precio unitario. Una pared de block no incluye automáticamente pañete, pintura y plafón. La funda de cemento del proveedor debe normalizarse a la unidad del descompuesto antes de multiplicar consumos. No presupuestes el material por funda si la partida espera kilogramos sin registrar su peso."),
                ("RNC y alcance del documento", "Identifica empresa y cliente, obra, fecha y moneda DOP. Distingue la base, el impuesto configurado y el total, sin presentar un porcentaje como análisis universal de ITBIS en construcción. El presupuesto no es una factura DGII ni una certificación de cubicación contractual. La revisión de ese tratamiento y del uso del término corresponde al profesional local."),
            ],
        ),
        "tecnica": (
            "plantilla-presupuesto-dop-itbis",
            "Presupuesto en pesos dominicanos: alcance e ITBIS",
            "Una plantilla DOP sirve para explicar qué se ofrece y qué queda por decidir. No basta con añadir RD$ a una hoja: el cliente necesita cantidades, productos, exclusiones y una referencia inequívoca del documento que acepta.",
            [
                ("Separar la oferta de la cubicación de avance", "En la oferta, indica cantidades previstas y condiciones de medición. Si el cliente pide un documento de avance, no reutilices el mismo total como si fuera una certificación de obra ejecutada. Esta plantilla no administra retenciones ni valida cubicaciones contractuales; organiza un presupuesto comercial por capítulos y partidas."),
                ("Evitar dobles sumas en plafón y acabados", "Describe el plafón contratado, alturas y remates; separa luminarias o artefactos elegidos como productos si no forman parte del trabajo base. Identifica qué alternativa se incluye en el total y cuáles son opcionales. El pañete y la pintura deben poder revisarse por cantidad sin que cambie accidentalmente el precio de un producto fijo."),
                ("Mostrar impuesto sin prometer liquidación fiscal", "La configuración de ITBIS del producto es una referencia editable, no una decisión jurídica sobre la base de cada contrato. Indica RNC, fecha, vigencia y condiciones de pago, y solicita revisión del tratamiento aplicable. Un PDF comercial con impuesto calculado no emite NCF o e-CF y no sustituye la factura fiscal."),
            ],
        ),
    },
    "PA": {
        "slug": "panama",
        "labor": "En Panamá una tarifa de mercado, un mínimo legal y una tabla de convenio no son intercambiables. La referencia USD del catálogo modela coste empresa; no acredita cumplimiento de un convenio concreto ni sustituye la revisión de categorías, jornada y beneficios. Comprueba además si un subcontratista factura por actividad y aporta sus herramientas. No vuelvas a cargar aportes de planilla sobre una oferta cerrada sin analizar su alcance.",
        "documento": (
            "plantilla-presupuesto-construccion-panama",
            "Plantilla de presupuesto en Panamá (USD)",
            "En una obra privada panameña, el presupuesto debe dejar claro qué incluye el precio en dólares y qué condiciones lo pueden cambiar. La moneda compartida con otros países no hace equivalentes jornales, materiales ni tratamiento tributario.",
            [
                ("Identificar el alcance y el acceso", "Divide preparación, estructura o albañilería, instalaciones y acabados. Registra unidad y cantidad de repello, cielo raso y artefactos, además de retiro y protección. En un edificio, confirma restricciones de acceso, horarios y traslado interno antes de prometer un plazo. El flete o el izado omitidos no se recuperan solo cambiando el margen."),
                ("USD, RUC e ITBMS como datos separados", "Usa USD como moneda del presupuesto y verifica los precios panameños de sus recursos. Identifica RUC y fecha; revisa con tu asesor el tratamiento de ITBMS que corresponda. El porcentaje de referencia del producto no certifica la obligación tributaria de cualquier contrato. El documento comercial no emite factura DGI ni aplica automáticamente convenios laborales."),
                ("Opciones y aceptación por versión", "Distingue productos incluidos, opcionales y alternativas. Si cambia un sanitario, no cambies también las cantidades de repello sin dejarlo registrado. Envía una versión nueva con total y alcance identificados; conserva la anterior. La forma de pago y las exclusiones deben estar escritas, no solo en los mensajes que acompañan al archivo."),
            ],
        ),
        "tecnica": (
            "apu-repello-panama",
            "APU de repello en Panamá: precio USD y revisión de cuadrilla",
            "El repello exige definir superficie y acabado antes de usar una tarifa panameña. Un APU permite distinguir insumos del muro, tiempo de ejecución y condiciones de acceso sin confundir el precio comercial con un jornal de convenio.",
            [
                ("Medir paños y remates", "Especifica espesor, soporte y si el acabado incluye afinado. Registra el criterio para vanos, esquinas y superficies en altura. La preparación de una pared deteriorada debe estar contemplada o separada. No uses el área de piso como sustituto de las superficies reales de repello ni incluyas cielo raso sin comprobar su sistema."),
                ("Revisar coste por integrante", "Convierte el rendimiento de la cuadrilla en horas por m² para cada trabajador. Una jornada de oficial con ayudante no cuesta lo mismo que una jornada de oficial solo. Valida la categoría y el coste aplicable con la empresa; la tabla nacional no es un certificado de mínimos o de convenio. Incluye andamio y traslados cuando sean necesarios."),
                ("Recursos panameños, no precios de otra economía USD", "Normaliza cemento, arena y mortero a sus unidades de consumo. Comprueba disponibilidad, transporte e impuestos en la oferta del proveedor antes de trasladar el precio al APU. Que Ecuador y Panamá usen dólares no permite copiar el mismo coste de enlucido o repello. El margen de venta y el ITBMS del documento se revisan después del coste técnico."),
            ],
        ),
    },
    "CR": {
        "slug": "costa-rica",
        "labor": "En Costa Rica debe separarse salario de referencia, cargas de la empresa y tarifa facturada por el profesional. La tabla CRC no calcula planillas CCSS ni primas individuales de riesgos del trabajo. Un fontanero contratado por servicio puede incorporar visita y herramienta. Pide el alcance de ese servicio antes de compararlo con una hora de coste interno; tampoco supone que se hayan tramitado permisos o responsabilidades CFIA.",
        "documento": (
            "plantilla-presupuesto-construccion-costa-rica",
            "Plantilla de presupuesto en Costa Rica (colones)",
            "Una oferta en colones necesita un alcance entendible y cifras con separadores consistentes. El formato de la plantilla no sustituye permisos, dirección técnica ni revisión fiscal de la obra.",
            [
                ("Partidas con rodapié, cielo raso y repello definidos", "Separa obra base, instalaciones, acabados y servicios. Describe tipo de cielo raso, altura y remates; mide rodapié por su longitud cuando esa sea la unidad contratada. La protección de una vivienda ocupada y el retiro de escombros deben estar expresamente incluidos o excluidos. No dejes esos trabajos bajo una palabra genérica como varios."),
                ("Identificación y formato en CRC", "Identifica empresa y cliente con el documento que corresponda; la etiqueta de producto NITE no significa que toda persona deba usar esa identificación. Revisa importes en colones con coma decimal y punto de miles. Distingue subtotal e impuesto configurado sin convertir el porcentaje de referencia en asesoramiento para cualquier operación."),
                ("Lo comercial no tramita permisos", "Define vigencia, forma de pago y condiciones de cambio. Un PDF CotizaT no gestiona CFIA, APC ni factura electrónica de Hacienda. Si la obra requiere responsabilidades o documentos técnicos adicionales, deben tramitarse por sus vías correspondientes. La aceptación del presupuesto no demuestra que esas obligaciones estén cubiertas."),
            ],
        ),
        "tecnica": (
            "apu-repello-colones-costa-rica",
            "APU de repello en colones: método para Costa Rica",
            "El coste del repello en CRC se construye con consumos y producción real, no convirtiendo un precio final de otro país. Espesor, preparación y acceso deben quedar definidos antes de revisar la referencia nacional.",
            [
                ("Elegir mezcla y espesor", "Distingue mortero preparado de mezcla en obra y evita sumar ambos sistemas. Comprueba el rendimiento del envase para el espesor contratado. Registra reparación de soporte, malla y encuentros si se requieren; no aparecen gratis por medir el paño. El desperdicio se justifica en los materiales que lo sufren, no como recargo repetido a todas las líneas."),
                ("Calcular horas con acceso real", "Convierte m² por jornada a horas por m² de oficial y ayudante. Un paño continuo accesible no rinde como remates junto a instalaciones o trabajo en altura. Añade equipo y montaje si aplica. El coste empresa de referencia debe contrastarse con la contratación real y no reemplaza una liquidación de CCSS o una prima específica de seguros."),
                ("Comparar proveedores en la misma unidad CRC", "Comprueba presentación, transporte y condición tributaria de cada precio. Un saco barato puede contener menos material o excluir entrega. El APU debe terminar en coste por unidad de obra, con el margen comercial separado. Este análisis no equivale a un presupuesto visado ni realiza trámites técnicos CFIA."),
            ],
        ),
    },
    "GT": {
        "slug": "guatemala",
        "labor": "En Guatemala el jornal de mercado no incluye necesariamente todos los costes de una empresa formal. La referencia en quetzales incorpora un modelo con prestaciones; no es una planilla IGSS ni certifica la situación de cada trabajador. El bono 14 y el aguinaldo no deben añadirse dos veces al usar una referencia ya cargada. Para block y repello, comprueba además si la cuadrilla cobra por producción o por jornada.",
        "documento": (
            "plantilla-presupuesto-construccion-guatemala",
            "Plantilla de presupuesto en Guatemala (quetzales)",
            "La plantilla guatemalteca debe distinguir block, repello, cielo falso e instalaciones, con cantidades que el cliente pueda revisar. Poner un total GTQ sin describir esos trabajos no permite comparar alcance ni gestionar cambios.",
            [
                ("Describir obra base y acabados por separado", "La pared de block debe indicar dimensiones, espesor y si incluye refuerzos o solo colocación. El repello y la pintura se estudian como trabajos propios cuando puedan variar. En instalaciones eléctricas, identifica circuitos y elementos como flipones, sin convertir una partida genérica en promesa de diseño técnico completo. La seguridad y el diseño requieren su revisión específica."),
                ("NIT, GTQ y fecha visibles", "Identifica empresa, cliente, obra, fecha y validez. Usa GTQ para evitar confundir el símbolo monetario con dólares. Compara los precios de proveedor por presentación y condición de entrega; no trates una promoción de ferretería como precio nacional permanente. El IVA configurado del documento no lo convierte en una factura FEL."),
                ("Controlar opciones y exclusiones", "Si el cliente elegirá cielo falso o revestimiento después, indica qué opción está incluida y cuánto cambia la alternativa. Deja escritos retiro, limpieza y fletes, además de plazo y forma de pago. Ante un cambio, emite otra versión identificada. CotizaT genera una propuesta comercial y no sustituye el emisor de factura electrónica autorizado."),
            ],
        ),
        "tecnica": (
            "apu-repello-block-guatemala",
            "APU de repello y block en Guatemala: dos partidas en GTQ",
            "Levantar block y repellarlo son trabajos relacionados, pero no un único rendimiento. Separarlos permite medir caras, cambiar espesores y revisar recursos en quetzales sin pagar dos veces el mismo material.",
            [
                ("Una pared, varias superficies", "La colocación del block se mide con el criterio acordado para el muro; el repello depende de cuántas caras se terminan y de sus vanos y remates. No multipliques automáticamente el área de pared por dos si una cara quedará sin repellar. Refuerzos, dinteles y estructura no deben suponerse incluidos por aparecer la palabra block."),
                ("Dos descompuestos sin recursos duplicados", "En colocación, estudia unidades de block, mortero de pega y cuadrilla. En repello, estudia mezcla, espesor y horas de acabado. Si mezclas en obra, no añadas además un mortero preparado completo. Registra el tamaño de la bolsa de cemento y la unidad de arena; el catálogo normaliza consumos, no adivina la presentación de la compra."),
                ("Precio GTQ y revisión de compra", "Compara disponibilidad y entrega entre proveedores de Guatemala con la misma especificación. Los precios de catálogo sirven para iniciar el análisis, no garantizan stock ni descuento por volumen. Separa el coste directo del precio de venta y conserva la fecha de los recursos. El resultado no es un expediente de licitación ni una factura FEL."),
            ],
        ),
    },
    "HN": {
        "slug": "honduras",
        "labor": "En Honduras las referencias investigadas distinguen albañil, ayudante y maestro de obra; no justifican llamar maestro a cualquier hora de oficial. La tabla en lempiras es nacional, no una tarifa certificada de Tegucigalpa o San Pedro Sula. Revisa contratación, herramientas y traslado antes de comparar un jornal ofrecido por una cuadrilla con el coste empresa modelado. Una obra pequeña puede tener mínimos de movilización que la hora no recoge.",
        "documento": (
            "plantilla-presupuesto-construccion-honduras",
            "Plantilla de presupuesto en Honduras (lempiras)",
            "Un presupuesto HNL debe permitir distinguir pared de bloque, repello y acabado. El cliente necesita saber si contrata suministro y colocación o solamente mano de obra, especialmente cuando compra parte de los materiales.",
            [
                ("Aclarar quién aporta cada recurso", "Indica si la empresa suministra cemento, bloque, arena y equipo o si los entrega el cliente. No elimines el control de consumos por tratarse de mano de obra: la espera de material puede cambiar el plazo. Separa partidas de cielo falso, instalaciones y pintura. Define retiro, transporte y limpieza final para que no aparezcan como extras inesperados."),
                ("RTN e importes HNL sin falsas precisiones locales", "Identifica RTN, cliente, obra y fecha. Usa el código de moneda para que una captura por WhatsApp no parezca una oferta en dólares. Las referencias nacionales no prueban el precio exacto de una ciudad. Revisa el ISV que corresponda con tu asesor; la configuración del producto no es una decisión fiscal automática."),
                ("Vigencia y cambios por escrito", "Señala validez de precios, condiciones de pago y supuestos de acceso. Si el cliente cambia bloque o superficie, calcula la nueva cantidad y reenvía una versión distinta, sin editar el archivo ya aprobado. El PDF es comercial: no sustituye una factura SAR ni resuelve obligaciones de contratación laboral."),
            ],
        ),
        "tecnica": (
            "apu-bloque-repello-honduras",
            "APU de pared de bloque y repello en Honduras, en HNL",
            "El coste de una pared depende de la pieza, el refuerzo y el acabado contratado. Un precio por bloque colocado no equivale automáticamente al precio de un metro cuadrado de pared terminada.",
            [
                ("Convertir piezas a superficie con su modulación", "Define el tamaño del bloque y considera juntas antes de calcular unidades por m². Aclara si el precio incluye refuerzo, castillos o dinteles: no se deduce de la pieza. Mide vanos y encuentros de acuerdo con la oferta. El repello de una o dos caras constituye una cantidad distinta de la superficie de colocación."),
                ("Descomponer colocación y acabado", "Separa bloques, mortero de pega y horas de la cuadrilla de los insumos de repello. Revisa sacos de cemento por peso, no solo por nombre de presentación. Si el cliente aporta material, mantén visible qué consumos se necesitan aunque no sean una venta de tu empresa. Transporte y espera de suministro no son idénticos a pérdida de mezcla."),
                ("Usar lempiras con fecha y alcance", "Sustituye referencias por precios HNL de proveedor cuando tengas cotización confirmada. La tabla de mano de obra no garantiza la tarifa de un maestro para cualquier tipo de pared. Contrasta horas y condiciones reales antes de aplicar margen. Este análisis no fija un precio nacional por m² ni emite factura SAR."),
            ],
        ),
    },
    "SV": {
        "slug": "el-salvador",
        "labor": "En El Salvador el uso de dólares no permite tomar como propia una tarifa de Ecuador o Panamá. Las referencias salvadoreñas distinguen coste empresa y jornal de mercado; no liquidan ISSS o AFP por trabajador. Comprueba si el acuerdo de cuadrilla incluye herramienta y desplazamiento. Para comparar una propuesta por obra con una hora interna necesitas conocer producción, alcance y gastos incluidos, no solo dividir su total entre ocho.",
        "documento": (
            "plantilla-presupuesto-construccion-el-salvador",
            "Plantilla de presupuesto en El Salvador (USD)",
            "Un presupuesto salvadoreño en dólares debe explicar qué obra se entrega y con qué cantidades. La identificación fiscal y el impuesto son datos del documento; no sustituyen el desglose comercial ni lo convierten en facturación electrónica.",
            [
                ("Partidas de repello y cielo falso con límites claros", "Define preparación de soporte, espesor y acabado del repello; separa pintura y cielo falso cuando sus cantidades o productos puedan cambiar. Aclara si se incluyen demolición, protección de la vivienda y retiro de escombros. En un trabajo de remodelación, omitir estas tareas puede cambiar más el total que una pequeña variación de material."),
                ("USD salvadoreños, identificación y revisión fiscal", "Identifica empresa, NIT cuando corresponda, cliente, obra y fecha. Aunque la moneda sea USD, utiliza recursos investigados para El Salvador y revisa transporte y presentación. La referencia de IVA del producto es editable y necesita validación para cada operación. El PDF no es un DTE ni una factura del Ministerio de Hacienda."),
                ("Opcionales y versiones que se puedan comparar", "Si hay alternativas de cerámica o sanitario, identifica cuál forma parte del total. No sumes simultáneamente dos opciones excluyentes. Conserva el presupuesto enviado y emite otra versión ante un cambio; explica si varía precio, cantidad o alcance. Anota forma de pago y vigencia, además del total en dólares."),
            ],
        ),
        "tecnica": (
            "apu-repello-el-salvador",
            "APU de repello en El Salvador: recursos locales en dólares",
            "El APU de repello salvadoreño debe combinar precio local y rendimiento propio. Compartir moneda con otros países no implica compartir coste de cuadrilla, mezcla, transporte o condiciones de compra.",
            [
                ("Medición y especificación del repello", "Registra superficies por ambiente con criterio de vanos y remates. Define espesor, soporte y acabado; identifica reparación previa o trabajo en altura. El cielo falso no se incluye como repello solo por ocupar la misma habitación. Si hay que proteger pisos o instalaciones, estudia esos trabajos explícitamente en lugar de confiar en una cifra global por m²."),
                ("Cuadrilla y mezcla por unidad ejecutada", "Selecciona mortero preparado o dosificación en obra. Normaliza los insumos y aplica pérdidas justificadas sin repetirlas en todos los recursos. Convierte la producción de cuadrilla a horas por integrante y por m². Una hora de referencia con coste empresa no es el jornal neto del trabajador ni una tarifa final para facturar un servicio."),
                ("Contrastar USD con proveedores salvadoreños", "Verifica precio, disponibilidad y transporte para la obra que se va a ejecutar. Las referencias documentales del mercado y del sector, incluidas las investigadas sobre CASALCO, no garantizan una cotización vigente de proveedor. Fecha los precios propios, revisa el margen y deja el impuesto para el documento aplicable. El APU no emite DTE ni valida obligaciones laborales."),
            ],
        ),
    },
    "NI": {
        "slug": "nicaragua",
        "labor": "En Nicaragua una referencia mensual de empleo y un jornal de albañil no deben mezclarse sin explicar días y horas. La tabla NIO conserva el modelo de coste empresa de la investigación, no certifica salario mínimo MITRAB vigente ni liquida INSS. Cuando una referencia sea estimada o derivada, se muestra como tal. Contrasta la tarifa del equipo que trabajará en la obra antes de asumir producción y plazo.",
        "documento": (
            "plantilla-presupuesto-construccion-nicaragua",
            "Plantilla de presupuesto en Nicaragua (córdobas)",
            "La oferta en córdobas debe identificar moneda y alcance incluso si algunas compras se negocian en dólares. No mezcles importes NIO y USD en una misma columna ni dejes la conversión implícita en el total.",
            [
                ("Capítulos y materiales con unidad definida", "Separa preparación, albañilería, instalaciones y acabados. Un cielo raso de Gypsum necesita sistema, superficie y remates; no basta con escribir láminas. Para repello y pintura, deja clara la superficie y el estado del soporte. Anota transporte, protección y retiro de desperdicios como incluidos o excluidos para poder comparar la propuesta con otra oferta."),
                ("Compras USD y documento NIO", "Si un proveedor cotiza en dólares, convierte a la moneda del presupuesto con una referencia documentada antes de sumar. Guarda fecha y condición de la compra. Identifica empresa, RUC, cliente y obra; revisa la aplicación del impuesto con quien corresponda. La referencia de IVA del producto no emite factura DGI ni resuelve la tributación de cada encargo."),
                ("Validez y cambio de producto", "Distingue el acabado incluido de alternativas posteriores y define vigencia de precios. Si cambia un sistema de cielo raso, revisa estructura, fijaciones y mano de obra, no solo el precio de la placa. Envía una nueva versión identificada y conserva la anterior; un cambio de moneda o de producto no debe borrar el acuerdo previo."),
            ],
        ),
        "tecnica": (
            "apu-repello-cordobas-nicaragua",
            "APU de repello en córdobas: método para Nicaragua",
            "El precio de repello en NIO se obtiene de insumos y horas coherentes con la especificación. La tasa de una compra en dólares es solo un dato de valoración: no sustituye medición ni productividad de cuadrilla.",
            [
                ("Definir mezcla y soporte", "Establece espesor, preparación y terminación del repello. No uses para reparación puntual el rendimiento de una pared nueva continua. Si compras mezcla preparada, revisa su ficha; si la produces, calcula cemento y arena por unidad compatible. Evita combinar las dos alternativas en el mismo descompuesto porque duplicaría el material principal."),
                ("Normalizar compras y horas", "Convierte los precios de proveedor a NIO y a la unidad del recurso antes de multiplicar. Registra si la entrega incluye transporte. Calcula las horas de oficial y ayudante desde la producción útil y contempla acceso o altura. No sustituyas el coste empresa por un salario mensual de una oferta de empleo dividido entre jornadas arbitrarias."),
                ("Referencias locales con fecha", "La investigación del catálogo recoge referencias nicaragüenses y fuentes de mercado como SINSA y MITRAB según el recurso; no todas son observaciones directas ni tarifas actuales. Contrasta compras y contratación de esta obra y conserva su fecha. Después separa margen e impuesto del coste directo. El resultado no acredita salario mínimo ni produce una factura DGI."),
            ],
        ),
    },
    "UY": {
        "slug": "uruguay",
        "labor": "En Uruguay el régimen de aportación de construcción merece una revisión específica. La tabla UYU procede del modelo histórico de coste empresa del catálogo: no liquida BPS de obra ni acredita que una cifra de laudo incluya o excluya todos los conceptos aplicables. No se publica aquí una calculadora normativa. Antes de ofertar, confirma categoría, período y tratamiento de la contratación con un profesional local.",
        "documento": (
            "plantilla-presupuesto-reforma-uruguay",
            "Plantilla de presupuesto de reforma en Uruguay, en UYU",
            "Una reforma en pesos uruguayos necesita alcance, cantidades y condiciones comerciales claras. El presupuesto no debe dar por resuelto el régimen de aportes de obra ni confundir una propuesta al cliente con documentación laboral.",
            [
                ("Describir revoque, cielorraso e instalaciones", "Organiza preparación, albañilería, sanitario y terminaciones con unidades y cantidades. Indica si el trabajo incluye reparación previa, protección de vivienda y retiro. Un cielorraso nuevo puede requerir estructura y remates que una simple reposición no necesita. La comparación entre ofertas debe hacerse sobre esos trabajos, no únicamente sobre su total."),
                ("RUT y moneda inequívoca", "Identifica empresa, cliente, obra y fecha, usando UYU para evitar confusión con USD. Aclara la moneda de los productos cotizados por proveedores y la referencia utilizada si hay conversión. El IVA de referencia del producto no determina todos los tratamientos de una obra. El PDF comercial no emite comprobante electrónico DGI."),
                ("Dejar BPS y contrato bajo revisión especializada", "No escribas aportes incluidos sin confirmar qué obligaciones, responsables y conceptos comprende esa frase. CotizaT no calcula el régimen BPS de construcción ni tramita inscripciones de obra. Define vigencia, pagos y cambios, y pide revisión profesional cuando correspondan obligaciones específicas. Una nueva propuesta debe conservar trazabilidad frente a la versión enviada."),
            ],
        ),
        "tecnica": (
            "apu-revoque-uruguay",
            "APU de revoque en Uruguay: recursos en pesos uruguayos",
            "El descompuesto de revoque permite estudiar materiales y horas, pero no sustituye el análisis de aportes de una obra uruguaya. La referencia de coste debe revisarse junto con el régimen real de contratación.",
            [
                ("Especificación y superficie del revoque", "Separa reparación, revoque nuevo y terminación fina si sus condiciones son distintas. Define espesor, soporte y caras tratadas; registra vanos y encuentros. El trabajo junto a instalaciones sanitarias o en una vivienda ocupada puede reducir producción y exigir protección adicional. No lo compares sin más con un paño libre de obra nueva."),
                ("Recursos UYU y revisión de la hora", "Normaliza materiales según la presentación que realmente compras y registra transporte. Convierte el rendimiento de cuadrilla en horas por m² de cada categoría. Si una tabla laboral ya incorpora determinados conceptos, verifica su alcance antes de aplicar otro factor. El modelo histórico del catálogo no certifica la liquidación BPS ni la vigencia de un laudo."),
                ("Coste técnico frente a obligación de obra", "El APU aporta una base para decidir precio y producción; no demuestra que estén satisfechas aportaciones, seguros o registros. Conserva la fuente y fecha del coste que adoptes y encarga la revisión específica que requiera el contrato. No se ofrece aquí una fórmula normativa BPS ni un porcentaje válido para todas las reformas."),
            ],
        ),
    },
    "PY": {
        "slug": "paraguay",
        "labor": "En Paraguay la presentación comercial en guaraníes no exige redondear cada operación interna del APU a enteros. La referencia horaria puede conservar precisión de cálculo antes del total mostrado. Distingue esa precisión del salario efectivamente pagado y del precio final. La tabla PYG no liquida IPS ni prestaciones; contrasta la contratación real y no añadas dos veces las cargas ya modeladas en el coste empresa.",
        "documento": (
            "presupuesto-guaranies-sin-decimales-paraguay",
            "Presupuesto de obra en guaraníes sin decimales innecesarios",
            "En una propuesta PYG el cliente debe leer guaraníes, no importes que parezcan dólares ni céntimos que no aportan claridad. El formato visible y la precisión interna de los cálculos cumplen funciones diferentes.",
            [
                ("Mantener precisión hasta el resumen", "Una hora o un consumo por m² puede producir fracciones al calcularse. No redondees prematuramente cada recurso y vuelvas a multiplicar después: acumularías diferencias al aumentar cantidades. Revisa el total del presupuesto y el criterio de presentación antes de enviar. Esta guía no establece una regla fiscal de redondeo ni promete un formato electrónico homologado."),
                ("Partidas con alcance y moneda explícitos", "Separa hormigón, revoque, cielorraso e instalaciones. Indica unidad, cantidad, producto incluido y exclusiones. Identifica empresa, RUC, cliente, obra y fecha; usa PYG para que el símbolo no genere ambigüedad. Si un proveedor cotiza en otra moneda, normaliza el recurso y conserva la referencia de conversión en vez de mezclar columnas."),
                ("Comprobar PDF y cambio de versión", "Antes de compartir el archivo, revisa cómo se muestran separadores, cantidades y total en guaraníes. No se da por probado un PDF local hasta comprobar el documento generado. La configuración de impuesto no convierte el presupuesto en factura SIFEN. Si cambia una cantidad o producto, emite otra versión identificada sin reemplazar silenciosamente la anterior."),
            ],
        ),
        "tecnica": (
            "apu-revoque-paraguay",
            "APU de revoque en Paraguay: consumos y cálculo en PYG",
            "El APU en guaraníes necesita consumos precisos aunque la propuesta comercial se lea sin decimales innecesarios. Redondear primero el cemento, después las horas y después el unitario puede distorsionar el coste de una superficie grande.",
            [
                ("Definir revoque y rendimiento", "Especifica soporte, espesor y acabado. Mide paños y vanos con el criterio acordado y separa preparación si es un trabajo diferente. Calcula la producción útil de oficial y ayudante; el rendimiento de una pared continua no describe necesariamente esquinas, reparaciones o trabajo junto a un cielorraso ya terminado."),
                ("Valorar recursos sin redondeo prematuro", "Convierte materiales a la unidad del descompuesto y conserva precisión de horas y consumos. Normaliza cualquier compra en moneda extranjera a PYG antes de sumar. Las pérdidas deben ser identificables y no duplicarse en un recargo general. El total comercial se revisa al final, no eliminando fracciones de cada operación interna."),
                ("Contrastar costes y obligaciones por separado", "La referencia horaria es un modelo de coste empresa con fecha, no una liquidación de IPS o una tarifa final por m². Revisa los acuerdos de la cuadrilla, transporte y disponibilidad de material. Después fija el margen de venta y el impuesto del documento. El descompuesto y su PDF no sustituyen la emisión fiscal SIFEN."),
            ],
        ),
    },
    "BO": {
        "slug": "bolivia",
        "labor": "En Bolivia conviene separar jornal acordado, coste empresa y tarifa comercial en bolivianos. La referencia nacional BOB no constituye una tabla salarial por ciudad ni liquida aportes o beneficios sociales. Los cómputos métricos aportan cantidades: no resuelven productividad. La Paz, Santa Cruz y Cochabamba pueden requerir contrastes de suministro y ejecución distintos, pero no se inventan aquí precios locales para completar esa información.",
        "documento": (
            "computos-metricos-presupuesto-bolivia",
            "De cómputos métricos a presupuesto de obra en Bolivia",
            "Los cómputos métricos explican cuánto trabajo hay; el APU explica cuánto cuesta ejecutar cada unidad. Mantener esa separación permite corregir una dimensión sin perder el precio y cambiar un insumo sin volver a medir la obra.",
            [
                ("Hacer trazable cada cantidad", "Registra ubicación, dimensiones, unidad y criterio de descuento por partida. Distingue superficies de revoque, volúmenes de hormigón y longitudes de instalaciones. Una cantidad total sin dimensiones no permite revisar el efecto de una abertura nueva. El criterio técnico debe validarse para el encargo: esta guía no impone una norma de medición para obra pública."),
                ("Relacionar cómputo y precio BOB", "Asocia cada cantidad con una partida cuyo alcance y unidad coincidan. El APU recoge materiales, horas y equipo por unidad; su suma se multiplica por el cómputo correspondiente. No uses un precio por m² de otra ciudad como si fuera una referencia validada para la obra. Comprueba proveedor, transporte y condiciones de ejecución reales."),
                ("Identificación comercial y límite fiscal", "El presupuesto debe identificar NIT, cliente, obra, fecha y moneda BOB. El IVA configurado del producto no representa por sí solo el tratamiento tributario boliviano de cualquier contrato o precio de proveedor. Pide revisión local de base e impuesto. El PDF comercial no emite factura SIN ni certifica un expediente normativo."),
            ],
        ),
        "tecnica": (
            "apu-revoque-bolivianos-bolivia",
            "APU de revoque en bolivianos: del cómputo al coste",
            "Un revoque en BOB necesita una cantidad medida y un descompuesto compatible. Copiar el total de otra obra impide distinguir diferencias de espesor, cuadrilla y suministro que cambian el coste real.",
            [
                ("Especificación vinculada al cómputo", "Define soporte, mezcla, espesor y terminación. Mide superficies con sus vanos y remates y separa cielos o reparaciones cuando requieran otro método. Comprueba que la unidad del cómputo coincide con la del APU. Una longitud o un volumen no debe multiplicarse por un precio de superficie solo porque la descripción diga revoque."),
                ("Costear producción y suministro en BOB", "Normaliza bolsas y agregados a la unidad de consumo del recurso. Verifica traslado y descarga, y calcula las horas de cada integrante desde la producción útil. Las condiciones de altura o acceso requieren una estimación de obra; no se aplica aquí un recargo geográfico automático. Las pérdidas de mezcla no sustituyen esos tiempos de ejecución."),
                ("Precio local sin inventar series por ciudad", "Sustituye referencias nacionales por ofertas contrastadas cuando dispongas de ellas. Conserva fecha y especificación para comparar proveedores. No se publican tarifas de La Paz, Santa Cruz o Cochabamba sin evidencia diferenciada. Revisa el margen y el tratamiento fiscal con quien corresponda; el APU no liquida beneficios sociales ni emite factura SIN."),
            ],
        ),
    },
}
