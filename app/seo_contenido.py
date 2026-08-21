"""Textos largos de SEO on-page: cuerpo por país y guías pilar.

Viven aparte de ``app/seo.py`` para no mezclar routing con copy. Cada bloque
es único por mercado o por intención; no se clona cambiando el nombre del país.
"""
from __future__ import annotations

# Cuerpo extra de cada landing. Google necesita texto propio, no solo el H1.
# Cada entrada: lista de (h2, párrafos).
CUERPO_PAIS: dict[str, list[tuple[str, list[str]]]] = {
    "": [
        (
            "Qué es un software de presupuestos de construcción",
            [
                "Un software de presupuestos de construcción no es un Word con tabla. Es la herramienta con la que una constructora o un remodelador arma capítulos, partidas, cantidades, precios, IVA y un PDF que el cliente entiende. CotizaT está hecho para ese oficio en Latinoamérica: catálogo con análisis de precios unitarios, margen interno, horas de cuadrilla y envío por WhatsApp o email.",
                "La mayoría de las empresas de 2 a 15 personas sigue cotizando en Excel. Funciona hasta que sube el cemento, el cliente pide dos cambios y nadie recuerda qué versión se aprobó. CotizaT guarda el catálogo una vez, recalcula en cascada y sella cada envío.",
            ],
        ),
        (
            "Presupuesto de obra, APU y remodelación en un solo flujo",
            [
                "El presupuesto de obra se arma por capítulos. El APU (análisis de precios unitarios) explica de dónde sale cada precio: materiales, mano de obra y equipo, con rendimiento. La remodelación añade packs de estancia y productos con foto. CotizaT cubre los tres sin convertir el editor en un formulario enorme.",
                "El PDF del cliente no lleva costes internos ni horas. Eso queda en la app, para que decidas margen y plazo sin que te reclamen un papel que decía «5 horas».",
            ],
        ),
        (
            "Cinco países, un catálogo, nombres al mostrar",
            [
                "El catálogo es uno. Al elegir Venezuela, Colombia, México, Ecuador o Perú cambian el vocabulario en pantalla, el IVA, el ID fiscal y la moneda de ejemplo. No clonamos cinco bases de precios: evitamos que un mexicano vea «friso» o un colombiano «zoclo».",
                "Si tu mercado aún no está en el selector (Chile, Argentina, España), puedes usar la versión genérica en USD. Abrir un país nuevo exige copy y fiscalidad propios, no un find-and-replace.",
            ],
        ),
    ],
    "VE": [
        (
            "Presupuestos de obra en Venezuela, en USD o bolívares",
            [
                "En Venezuela un presupuesto de remodelación se discute en dólares y a veces se cobra en bolívares. CotizaT cotiza en USD o Bs y congela la tasa de referencia en cada documento. Un PDF enviado en marzo no cambia si en abril se mueve el tipo de cambio.",
                "El espacio nace con RIF e IVA 16 %. El catálogo habla concreto, friso, cielo raso, rodapié y plomero. No es un software español traducido: es el vocabulario de la cuadrilla en Caracas, Valencia o Maracaibo.",
            ],
        ),
        (
            "Inflación, catálogo y WhatsApp",
            [
                "Cuando suben los materiales, puedes ajustar el catálogo por porcentaje —todo o por capítulo— sin reescribir presupuestos ya enviados. El cliente recibe el PDF por WhatsApp, que es como ya cierras. Si pide quitar el porcelanato, editas, se crea una versión y copias un resumen: total anterior, total nuevo y qué cambió.",
                "Los documentos son comerciales, no factura fiscal. El RIF sale en el PDF; la factura la emites por el medio que te corresponda.",
            ],
        ),
        (
            "Pago de la licencia desde Venezuela",
            [
                "El plan de lanzamiento es 89 US$ al año. Desde Venezuela puedes pagar con Pago móvil, Binance, Kontigo, USDT o tarjeta. La tarjeta activa al confirmar; los métodos manuales se revisan en un máximo de 48 horas hábiles.",
            ],
        ),
    ],
    "CO": [
        (
            "Software de APU para constructoras en Colombia",
            [
                "En Colombia el presupuesto serio se sostiene en el APU: rendimiento × precio de cada recurso. CotizaT trae partidas descompuestas en materiales, mano de obra y equipo, editables en COP o USD, con NIT e IVA 19 %. El pañete no se llama friso; el andén no se llama acera.",
                "No es un software de licitación pública ni calcula AIU de contrato estatal. Está pensado para remodelación y obra privada: SAS de 2 a 15 personas que hoy cotizan en Excel y envían por WhatsApp.",
            ],
        ),
        (
            "De Bogotá o Medellín al PDF, sin otra plataforma",
            [
                "El cliente no se registra. Tú armas el presupuesto, revisas margen y horas de cuadrilla, y mandas el PDF. Si llama para cambiar el porcelanato, reenvías una versión clara. El enlace privado con firma es opcional.",
                "La factura electrónica DIAN no la emite CotizaT. El presupuesto es un documento comercial. El IVA 19 % lo configuras tú; no es asesoramiento tributario.",
            ],
        ),
        (
            "Qué no es: licitación pública ni AIU de contrato estatal",
            [
                "CotizaT no arma pliegos, no calcula AIU de obra pública y no sustituye un software de interventoría. Si cotizas remodelación o obra privada para un particular o una SAS, el flujo (APU + PDF + WhatsApp) es el que cubre.",
            ],
        ),
    ],
    "MX": [
        (
            "Programa para cotizar obra y remodelación en México",
            [
                "En México se habla de cotización tanto como de presupuesto. CotizaT arma ambos: capítulos, partidas, análisis de precios unitarios y un PDF con RFC e IVA 16 %, en MXN o USD. El catálogo usa aplanado, plafón, zoclo, plomero y banqueta.",
                "Sirve a contratistas y remodeladores que cotizan vivienda o local comercial. No es Neodata ni un visor BIM. Es el flujo de siempre: visitas, cotizas, mandas el PDF por WhatsApp o correo y reenvías si hay cambios.",
            ],
        ),
        (
            "Pesos, tasa congelada y sin CFDI",
            [
                "El espacio nace en MXN. Cada presupuesto puede llevar su propia tasa si cotizas también en dólares. Un documento enviado no se reescribe si mañana se mueve el tipo de cambio.",
                "CotizaT no emite CFDI. El presupuesto es comercial. El CFDI lo sigues generando con tu PAC o tu contador.",
            ],
        ),
        (
            "De la visita a la cotización, no al visor BIM",
            [
                "El oficio mexicano habla de cotización tanto como de presupuesto. CotizaT cubre esa visita: mediciones, partidas, opciones de producto con foto y un PDF que se reenvía si el cliente cambia el piso. No es Neodata ni un visor de planos.",
            ],
        ),
    ],
    "PE": [
        (
            "Metrados y APU en soles para Perú",
            [
                "En Perú el presupuesto de obra arranca en el metrado: cantidades por partida. CotizaT suma mediciones por zona, aplica el APU (materiales, mano de obra, equipo) y cierra en soles o USD, con RUC e IGV 18 %. El catálogo muestra tarrajeo, cielo raso, zócalo, gasfitero y vereda.",
                "Está pensado para remodelación residencial y comercial pequeña, no para un expediente S10 de obra pública. El PDF se envía por WhatsApp; el cliente no entra a ninguna plataforma.",
            ],
        ),
        (
            "IGV en el documento, comprobante SUNAT aparte",
            [
                "Configuras el 18 % (o el que apliques) y el presupuesto lo calcula. No es asesoramiento tributario. El comprobante de pago SUNAT lo emites con tu sistema autorizado. CotizaT genera el documento comercial que presentas al cliente.",
            ],
        ),
    ],
    "EC": [
        (
            "Presupuestos y APU en dólares para Ecuador",
            [
                "Ecuador cotiza en USD. CotizaT nace en dólares, con RUC e IVA 15 %, y el catálogo habla hormigón, enlucido, tumbado, barredera y gasfitero. Cada partida trae APU editable: rendimientos y precios de recursos.",
                "El flujo es el de un remodelador en Quito o Guayaquil: armas el presupuesto, lo mandas por WhatsApp y, si hay cambios, reenvías una versión con el resumen del total anterior y el nuevo.",
            ],
        ),
        (
            "Sin factura del SRI",
            [
                "Los documentos son comerciales. No sustituyen la factura electrónica que te exija el SRI. El IVA 15 % del presupuesto lo configuras tú.",
            ],
        ),
        (
            "Dólar nativo, no una conversión improvisada",
            [
                "Ecuador ya cotiza en USD. El espacio no nace en otra moneda para luego «convertir». El RUC y el IVA 15 % se configuran al registrarte. Si mañana cambia la alícuota, la pones tú: CotizaT no decide impuestos.",
            ],
        ),
    ],
}


GUIAS: dict[str, dict] = {
    "presupuesto-de-obra": {
        "slug": "presupuesto-de-obra",
        "title": "CotizaT: cómo hacer un presupuesto de obra paso a paso",
        "h1": "Cómo hacer un presupuesto de obra (sin Excel que se rompe)",
        "description": (
            "Guía para armar un presupuesto de construcción por capítulos y partidas: "
            "cantidades, precios, IVA, PDF y cambios. Con catálogo y APU."
        ),
        "kicker": "Guía",
        "lead": (
            "Un presupuesto de obra claro tiene capítulos, partidas con cantidad y "
            "precio, IVA y un PDF que el cliente puede leer en el móvil. Esta guía "
            "describe el método; CotizaT es el software que lo ejecuta."
        ),
        "secciones": [
            (
                "1. Datos de la empresa y del cliente",
                [
                    "Antes de una partida: nombre comercial, logo, moneda, IVA e ID fiscal. En el cliente: nombre, teléfono o email. Sin eso el PDF no cierra y el envío por WhatsApp no tiene destinatario.",
                    "En CotizaT eliges país al registrarte y el espacio nace con moneda, IVA y etiqueta fiscal (RIF, NIT, RFC, RUC).",
                ],
            ),
            (
                "2. Capítulos, no una lista suelta",
                [
                    "Un presupuesto de baño no es 40 líneas sueltas. Es Demolición, Plomería, Impermeabilización, Revestimientos, Electricidad. Cada capítulo tiene subtotal. El cliente entiende el alcance; tú ves el margen por capítulo.",
                ],
            ),
            (
                "3. Partidas con cantidad, unidad y precio",
                [
                    "Cada partida: nombre, unidad (m², ml, und), cantidad y precio unitario. La cantidad puede ser directa o la suma de mediciones por zona (cocina 8 m², baño 4 m²). El importe es cantidad × precio, redondeado a dos decimales.",
                    "Si la partida viene del catálogo, llega con descripción técnica y, si hay APU, con coste interno. El precio de venta lo pones tú.",
                ],
            ),
            (
                "4. Revisa antes de enviar",
                [
                    "Partidas a precio cero, cantidades a cero, cliente sin teléfono, logo ausente, margen bajo. Un software debe avisarte. El PDF que sale mal se reenvía diez veces.",
                ],
            ),
            (
                "5. PDF, WhatsApp y versiones",
                [
                    "El cliente no quiere una plataforma. Quiere un PDF con tu logo. Lo mandas por WhatsApp o email. Si pide cambios, no reescribas el archivo a ciegas: guarda una versión, cambia, y dile qué se movió y cuál es el nuevo total.",
                ],
            ),
            (
                "Qué no es un presupuesto de obra en CotizaT",
                [
                    "No es un visor BIM, no es un pliego de licitación pública y no es una factura fiscal. Es el documento comercial con el que cierras alcance y precio. La factura la emites por el medio que exija tu país.",
                ],
            ),
        ],
        "faq": [
            {
                "q": "¿Cuánto tarda el primer presupuesto?",
                "a": "Con catálogo cargado, un baño tipo se arma en unos 10 minutos en pruebas con profesionales de construcción. Sin catálogo, el tiempo se va en escribir partidas.",
            },
            {
                "q": "¿El presupuesto es una factura?",
                "a": "No. Es un documento comercial. La factura fiscal se emite por el medio que exija tu país.",
            },
        ],
    },
    "analisis-precios-unitarios": {
        "slug": "analisis-precios-unitarios",
        "title": "CotizaT: qué es un APU y cómo se calcula",
        "h1": "Qué es un análisis de precios unitarios (APU)",
        "description": (
            "Qué es un APU en construcción: recursos, rendimientos, coste directo "
            "y precio de venta. Cómo se edita sin romper el presupuesto."
        ),
        "kicker": "Guía",
        "lead": (
            "El APU explica de dónde sale el precio de una partida. Sin él cotizas "
            "de memoria. Con él ves coste, margen y horas antes de enviar."
        ),
        "secciones": [
            (
                "La fórmula",
                [
                    "Cada recurso del APU tiene rendimiento (cuánto se gasta por unidad de partida) y precio unitario. Importe = rendimiento × precio. Se suman materiales, mano de obra y equipo. Sobre esa base pueden ir costes directos complementarios en porcentaje. El resultado es el coste directo por unidad.",
                    "El precio de venta no es el coste. Le aplicas beneficio. El cliente ve el precio de venta; el coste y el margen se quedan en la app.",
                ],
            ),
            (
                "Por qué el Excel se rompe",
                [
                    "En una hoja, cambiar la hora del oficial implica buscar cada partida que la usa. En un APU conectado, cambias el recurso una vez y se recalculan las partidas. Los presupuestos ya enviados no se tocan: cada versión queda congelada.",
                ],
            ),
            (
                "Horas de cuadrilla",
                [
                    "Las filas de mano de obra con unidad de tiempo (h, jornada) alimentan las horas-hombre. Con la jornada configurada obtienes días de obra. Eso es para planificar, no para imprimirlo al cliente.",
                ],
            ),
            (
                "CYPE y Excel",
                [
                    "Si ya exportas descompuestos CYPE, el .xlsx se puede importar clasificando materiales, mano de obra y complementarios, sin perder filas. También se pega TSV desde Excel.",
                ],
            ),
            (
                "Qué no cubre este APU",
                [
                    "No calcula AIU de contrato estatal colombiano, no exporta BC3/FIEBDC y no lee planos. El APU de CotizaT es el de la obra privada: recursos, rendimientos y precio de venta que tú decides.",
                ],
            ),
        ],
        "faq": [
            {
                "q": "¿CotizaT incluye APU de fábrica?",
                "a": "Sí. El catálogo propio trae partidas descompuestas en recursos con rendimiento y precio, editables.",
            },
            {
                "q": "¿El APU sale en el PDF del cliente?",
                "a": "No por defecto. El PDF lleva partidas, cantidades, precios y totales. El desglose de coste es interno.",
            },
        ],
    },
    "presupuesto-remodelacion": {
        "slug": "presupuesto-remodelacion",
        "title": "CotizaT: cómo presupuestar una remodelación",
        "h1": "Cómo presupuestar una remodelación (baño, cocina, vivienda)",
        "description": (
            "Método para presupuestos de remodelación: packs de estancia, partidas "
            "que no se olvidan, opciones de producto y reenvío de cambios."
        ),
        "kicker": "Guía",
        "lead": (
            "Una reforma se pierde por partidas olvidadas (impermeabilización, pases) "
            "y por cambios que no se documentan. El método es catálogo + pack de "
            "estancia + PDF con versiones."
        ),
        "secciones": [
            (
                "Empieza por la estancia, no por la partida",
                [
                    "Un baño no son 12 búsquedas sueltas. Es un capítulo: demolición, impermeabilización, piso, revestimiento, plomería, sanitario, grifería, iluminación. Un pack de estancia inserta ese capítulo escalado a los m² reales. Las piezas fijas (inodoro, mueble) no se multiplican.",
                ],
            ),
            (
                "Opciones para el cliente",
                [
                    "Incluido, opcional o alternativa, con foto. El cliente elige el porcelanato sin que reescribas el presupuesto. El documento marca qué se aprobó.",
                ],
            ),
            (
                "Lo que no se le enseña al cliente",
                [
                    "Coste interno, margen y horas de cuadrilla. Sirven para que no regales el baño y para no prometer un plazo imposible. El PDF lleva alcance, precios y totales.",
                ],
            ),
            (
                "Cuando llama y pide cambios",
                [
                    "Es el caso real. Editas, se sella una versión nueva y copias: total anterior, total nuevo, partidas añadidas o quitadas. Lo reenvías por el mismo WhatsApp.",
                ],
            ),
            (
                "Qué no es",
                [
                    "No es un software de interiorismo ni un catálogo de una sola tienda. Sirve si cotizas por partidas de construcción y acabados. Si solo vendes muebles sin obra, este no es el flujo.",
                ],
            ),
        ],
        "faq": [
            {
                "q": "¿Cuántos packs incluye CotizaT?",
                "a": "Seis de serie (baño, cocina, suelos, dormitorio, sala, electricidad) y puedes guardar los tuyos desde cualquier capítulo.",
            },
            {
                "q": "¿Sirve para un local comercial?",
                "a": "Sí, si cotizas por partidas. El producto está orientado a remodelación residencial y comercial privada, no a licitación pública.",
            },
        ],
    },
}


def cuerpo_pais(codigo: str) -> list[tuple[str, list[str]]]:
    codigo = str(codigo or "").strip().upper()
    return CUERPO_PAIS.get(codigo) or CUERPO_PAIS[""]


def ficha_guia(slug: str) -> dict | None:
    return GUIAS.get(str(slug or "").strip())


def lista_guias() -> list[dict]:
    return [GUIAS[k] for k in ("presupuesto-de-obra", "analisis-precios-unitarios", "presupuesto-remodelacion")]


# Bloques extra de las URLs /co/apu, /mx/remodelacion… Texto propio, no
# «Colombia» sustituido por «México». Sin esto Google las ve como duplicados.
HUB_EXTRA: dict[tuple[str, str], list[tuple[str, str]]] = {
    ("VE", "software-presupuestos"): [
        (
            "Presupuestar en Venezuela sin que el PDF se mueva con el dólar",
            "El oficio venezolano discute en dólares y a veces cobra en bolívares. CotizaT congela moneda y tasa en cada presupuesto: un PDF de marzo no cambia en abril. El RIF y el IVA 16 % salen en el documento; no es factura SENIAT.",
        ),
        (
            "Vocabulario de la cuadrilla, no de un software español",
            "Concreto, friso, cielo raso, rodapié, plomero. Sirve a remodeladores en Caracas, Valencia o Maracaibo que hoy arman el presupuesto en Excel y lo mandan por WhatsApp.",
        ),
    ],
    ("VE", "apu"): [
        (
            "APU cuando el cemento sube cada mes",
            "En Venezuela el APU sirve para no cotizar de memoria cuando el material se movió. Cambias el recurso una vez y se recalculan las partidas en edición. Los presupuestos ya enviados quedan congelados, con su tasa.",
        ),
        (
            "Horas de cuadrilla, sin imprimirlas al cliente",
            "Las filas de mano de obra alimentan horas internas. El PDF del cliente no las lleva: evitas el «el papel decía 5 horas» en una obra de friso o cielo raso.",
        ),
    ],
    ("VE", "remodelacion"): [
        (
            "Remodelar un baño en Caracas, con cambios por WhatsApp",
            "Pack de baño o cocina, cantidades a los m², productos con foto. Si el cliente pide quitar el porcelanato, reenvías una versión con total anterior y total nuevo. El flujo es PDF, no otra plataforma.",
        ),
    ],
    ("CO", "software-presupuestos"): [
        (
            "Software de presupuestos para una SAS de remodelación",
            "Pensado para empresas de 2 a 15 personas en Colombia que cotizan obra privada en COP, con NIT e IVA 19 %. No es un software de pliego ni de interventoría. El cliente recibe un PDF por WhatsApp.",
        ),
        (
            "Pañete, andén y sardinel, no friso ni acera",
            "El catálogo se muestra con terminología colombiana. Sirve en Bogotá, Medellín o el interior si presupuestas por partidas, no si licitás obra pública.",
        ),
    ],
    ("CO", "apu"): [
        (
            "APU de pañete en COP, no AIU de contrato estatal",
            "El análisis de precios unitarios de CotizaT es rendimiento × precio de materiales, mano de obra y equipo, editable en COP. No calcula AIU de obra pública. Si armas un APU de pañete o concreto para un particular o una SAS, este es el flujo.",
        ),
        (
            "De Excel al descompuesto, sin perder el rendimiento",
            "Importas CYPE o pegas TSV. El oficial y el cemento se editan en Recursos y caen a las partidas. El presupuesto enviado no se reescribe.",
        ),
    ],
    ("CO", "remodelacion"): [
        (
            "Remodelación en Bogotá o Medellín, sin registrar al cliente",
            "Packs de estancia, opciones de producto y PDF. La factura electrónica DIAN la emites aparte. CotizaT cierra alcance y precio de la reforma, no el CF-DIAN.",
        ),
    ],
    ("MX", "software-presupuestos"): [
        (
            "Programa para cotizar obra en pesos mexicanos",
            "En México se pide una cotización tanto como un presupuesto. CotizaT arma capítulos y partidas en MXN, con RFC e IVA 16 %. No es Neodata ni un visor BIM. Es la visita, la cotización y el PDF.",
        ),
        (
            "Aplanado, plafón y zoclo",
            "El catálogo no muestra friso ni cielo raso venezolano. Sirve a contratistas que cotizan vivienda o local comercial y reenvían cambios por WhatsApp o correo.",
        ),
    ],
    ("MX", "apu"): [
        (
            "Análisis de precios unitarios en MXN, editable",
            "Cada partida llega descompuesta. Cambias el cemento o la hora del oficial y se recalcula en pesos. Los documentos enviados congelan su tasa si también cotizas en USD.",
        ),
        (
            "No sustituye un PAC ni un CFDI",
            "El APU explica tu coste interno. El CFDI lo emites con tu PAC. Mezclar las dos cosas en el mismo PDF es el error que CotizaT evita a propósito.",
        ),
    ],
    ("MX", "remodelacion"): [
        (
            "De la visita a la cotización de un baño",
            "Pack de estancia, aplanado, plafón, zoclo y sanitarios con foto. El cliente elige alternativa; tú no reescribes la cotización desde cero. El PDF se reenvía con el resumen de cambios.",
        ),
    ],
    ("PE", "software-presupuestos"): [
        (
            "Presupuestos y metrados en soles",
            "En Perú el presupuesto arranca en el metrado. CotizaT suma cantidades por zona, aplica precio o APU, y cierra en soles o USD, con RUC e IGV 18 %. No es un expediente S10.",
        ),
        (
            "Tarrajeo, zócalo y gasfitero",
            "Terminología de Lima y del resto del país al mostrar. El PDF va por WhatsApp; el cliente no entra a una plataforma.",
        ),
    ],
    ("PE", "apu"): [
        (
            "APU y metrados juntos, no una lista plana",
            "Mides por zona, el APU pone rendimiento y precio, el importe es cantidad × precio unitario. Editas el recurso una vez. El IGV 18 % lo configuras tú; no es asesoramiento tributario.",
        ),
        (
            "Comprobante SUNAT aparte",
            "El presupuesto es comercial. El comprobante de pago lo emites con tu sistema autorizado.",
        ),
    ],
    ("PE", "remodelacion"): [
        (
            "Remodelar en Lima: tarrajeo, cielo raso y gasfitería",
            "Packs de baño y cocina escalados a m². Piezas fijas sin multiplicar. Cambios documentados cuando el cliente pide otra cerámica.",
        ),
    ],
    ("EC", "software-presupuestos"): [
        (
            "Software de presupuestos en dólares para Ecuador",
            "Ecuador ya cotiza en USD. El espacio nace en dólares, con RUC e IVA 15 %, no en otra moneda «para convertir después». Hormigón, enlucido, tumbado, barredera, gasfitero.",
        ),
    ],
    ("EC", "apu"): [
        (
            "APU en USD, con RUC",
            "Descompuestos editables en dólares. El IVA 15 % del documento lo pones tú. No emite factura del SRI.",
        ),
    ],
    ("EC", "remodelacion"): [
        (
            "Reforma en Quito o Guayaquil, PDF por WhatsApp",
            "Pack de estancia, tumbado y enlucido, productos con foto. Si hay cambios, reenvías total anterior y total nuevo. El cliente no se registra.",
        ),
    ],
}


FAQ_HUB: dict[tuple[str, str], list[dict]] = {
    ("VE", "software-presupuestos"): [
        {
            "q": "¿Puedo presupuestar en USD y cobrar en bolívares?",
            "a": "Sí. Cada presupuesto congela su moneda y su tasa. El PDF no se reescribe si mañana se mueve el tipo de cambio.",
        },
    ],
    ("CO", "apu"): [
        {
            "q": "¿Este APU sirve para un contrato estatal con AIU?",
            "a": "No. CotizaT no calcula AIU ni arma pliegos. El APU es para obra privada y remodelación, en COP, con NIT e IVA 19 %.",
        },
    ],
    ("MX", "remodelacion"): [
        {
            "q": "¿Es un programa para cotizar remodelación en México o solo un generador de PDF?",
            "a": "Arma la cotización con partidas, APU, opciones de producto y un PDF. No es un visor BIM ni emite CFDI.",
        },
    ],
    ("PE", "software-presupuestos"): [
        {
            "q": "¿Incluye metrados?",
            "a": "Sí: cantidades por partida y por zona. El APU es aparte, editable. El cierre puede ir en soles con IGV 18 %.",
        },
    ],
    ("EC", "software-presupuestos"): [
        {
            "q": "¿Nace en dólares o convierte desde otra moneda?",
            "a": "Nace en USD. Ecuador cotiza en dólares; no hay una conversión improvisada al registrarte.",
        },
    ],
}


# Preguntas de /legal/preguntas para JSON-LD (mismas respuestas que el HTML).
FAQ_LEGAL: list[dict] = [
    {
        "q": "¿Qué es exactamente CotizaT?",
        "a": "Una aplicación web para presupuestos de construcción y remodelación: catálogo con costes y APU, presupuestos por capítulos, margen interno y PDF por WhatsApp o email. No es un generador de documentos sueltos.",
    },
    {
        "q": "¿CotizaT emite facturas fiscales?",
        "a": "No. Los presupuestos y documentos de cobro son comerciales. No sustituyen una factura fiscal (DIAN, CFDI, SUNAT, SRI u otra).",
    },
    {
        "q": "¿Puedo probarlo antes de pagar?",
        "a": "Sí. 7 días de acceso completo, sin tarjeta. Una prueba por correo.",
    },
    {
        "q": "¿El cliente tiene que registrarse?",
        "a": "No. Envías el PDF por WhatsApp o email. El enlace privado es opcional.",
    },
    {
        "q": "¿Cuánto cuesta?",
        "a": "89 US$ al año de lanzamiento (habitual 109) o 9,99 US$ al mes el primer año. Sin permanencia.",
    },
]


def extra_hub(codigo: str, tema: str) -> list[tuple[str, str]]:
    return list(HUB_EXTRA.get((str(codigo or "").strip().upper(), str(tema or "").strip().lower()), ()))


def faq_hub(codigo: str, tema: str) -> list[dict]:
    return list(FAQ_HUB.get((str(codigo or "").strip().upper(), str(tema or "").strip().lower()), ()))
