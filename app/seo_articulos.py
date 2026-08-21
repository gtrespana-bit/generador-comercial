"""Artículos de país: un oficio, un mercado, un texto.

No son un blog. Cinco URLs, una por país de lanzamiento, escritas para
consultas que una landing no cubre del todo. Cifras del catálogo (más de
3.000 partidas, APU editable). Sin precios de mercado, sin factura fiscal,
sin IA.
"""
from __future__ import annotations

ARTICULOS: dict[str, dict] = {
    "apu-panete-colombia": {
        "slug": "apu-panete-colombia",
        "pais": "CO",
        "pais_nombre": "Colombia",
        "pais_path": "/co/",
        "kicker": "Colombia · APU",
        "title": "CotizaT: cómo armar un APU de pañete en Colombia sin Excel",
        "h1": "Cómo armar un APU de pañete en Colombia (sin que el Excel se rompa)",
        "description": (
            "Método para un análisis de precios unitarios de pañete en Colombia: "
            "recursos, rendimientos, COP e IVA 19 %. Sin AIU de obra pública."
        ),
        "lead": (
            "En Colombia un presupuesto serio se sostiene en el APU. El pañete "
            "es el ejemplo que todo remodelador conoce: materiales, oficial y "
            "ayudante, rendimiento por m². Esta guía describe el método; CotizaT "
            "es el software que lo ejecuta en COP, con NIT e IVA 19 %."
        ),
        "secciones": [
            (
                "Qué es un APU de pañete (y qué no es)",
                [
                    "Un análisis de precios unitarios descompone el precio de una partida en recursos: kilos o bultos de cemento, arena, agua, horas de oficial, horas de ayudante, a veces andamio o mezcladora. Cada línea es rendimiento × precio. La suma es el coste directo por m². El precio de venta es otra cifra: le aplicas beneficio.",
                    "Eso no es AIU de contrato estatal ni un pliego de licitación. CotizaT no calcula administración, imprevistos y utilidad de obra pública. Si cotizas remodelación o obra privada para un particular o una SAS, el APU de pañete sí es este flujo.",
                ],
            ),
            (
                "Por qué el Excel de pañete se rompe en Bogotá o Medellín",
                [
                    "La hoja empieza bien: una pestaña de recursos, otra de partidas, una fórmula de rendimiento. El problema llega el martes, cuando sube el cemento o la hora del oficial. Tienes que buscar cada partida que usa ese recurso. Si olvidas una, el baño de Chapinero sale con margen del 8 % y tú creías que era 28 %.",
                    "El segundo problema es la versión. Mandas el PDF, el cliente pide otro pañete, reescribes la hoja y ya no sabes cuál archivo se aprobó. El APU conectado cambia el recurso una vez y recalcula las partidas en edición. Los presupuestos ya enviados no se tocan.",
                ],
            ),
            (
                "Los tres bloques del descompuesto",
                [
                    "Materiales: lo que se gasta por m² (con desperdicio si lo usas). Mano de obra: rendimiento en horas de oficial y ayudante. Equipo: solo si aplica (mezcladora, andamio). Sobre esa base puedes poner costes directos complementarios en porcentaje. El cliente no ve ese desglose en el PDF; ve la partida, la cantidad, el precio y el total.",
                    "Las horas de cuadrilla salen de las filas de mano de obra. Sirven para no prometer un pañete de 80 m² «para el viernes» si el rendimiento dice otra cosa. No se imprimen al cliente.",
                ],
            ),
            (
                "COP, NIT e IVA 19 %",
                [
                    "Al registrarte eliges Colombia y el espacio nace en COP, con NIT e IVA 19 %. Puedes cotizar también en USD; cada presupuesto congela su tasa. El IVA del documento lo configuras tú: no es asesoramiento tributario.",
                    "La factura electrónica DIAN no la emite CotizaT. El presupuesto es un documento comercial. El pañete se llama pañete, no friso.",
                ],
            ),
            (
                "De CYPE o Excel a CotizaT",
                [
                    "Si ya exportas descompuestos CYPE, importas el .xlsx y se clasifican materiales, mano de obra y complementarios, sin perder filas. También pegas TSV desde una hoja. El catálogo propio trae más de 3.000 partidas descompuestas y cientos de recursos; no empiezas la base de cero.",
                    "El plan de lanzamiento es 89 US$ al año (habitual 109) o 9,99 US$ al mes el primer año. 7 días de prueba, sin tarjeta.",
                ],
            ),
        ],
        "faq": [
            {
                "q": "¿CotizaT calcula AIU colombiano?",
                "a": "No. El APU es de obra privada: recursos, rendimientos y precio de venta. El AIU de contrato estatal no está en el producto.",
            },
            {
                "q": "¿El pañete sale con terminología colombiana?",
                "a": "Sí. El catálogo se muestra con pañete, andén, sardinel. No verás friso venezolano en la URL de Colombia.",
            },
        ],
        "related": [
            ("APU en Colombia", "/co/apu"),
            ("Software de presupuestos en Colombia", "/co/software-presupuestos"),
            ("Qué es un APU (método)", "/guia/analisis-precios-unitarios"),
        ],
    },
    "cotizar-remodelacion-mexico": {
        "slug": "cotizar-remodelacion-mexico",
        "pais": "MX",
        "pais_nombre": "México",
        "pais_path": "/mx/",
        "kicker": "México · Cotización",
        "title": "CotizaT: de la visita a la cotización de remodelación en MXN",
        "h1": "De la visita a la cotización en México (en pesos, con tu margen)",
        "description": (
            "Cómo pasar de la visita a una cotización de remodelación en México: "
            "aplanado, plafón, opciones de producto, MXN e IVA 16 %. Sin CFDI."
        ),
        "lead": (
            "En México el cliente pide una cotización tanto como un presupuesto. "
            "La visita, las medidas, el aplanado, el plafón y el PDF que se "
            "reenvía cuando cambia el piso. Esta guía es ese oficio. CotizaT "
            "nace en MXN, con RFC e IVA 16 %."
        ),
        "secciones": [
            (
                "La visita no es el documento",
                [
                    "Mides el baño, anotas el aplanado, el zoclo, la banqueta si hay. En la camioneta todavía no hay cotización: hay cantidades. La cotización es capítulos, partidas, precio en pesos y un PDF que el cliente puede reenviar a su socio.",
                    "Si armas eso en Word, cada cambio de porcelanato es un archivo nuevo con un nombre peor. CotizaT sella versiones: total anterior, total nuevo, qué se movió.",
                ],
            ),
            (
                "Aplanado, plafón y zoclo: el catálogo tiene que hablar mexicano",
                [
                    "Un contratista en Ciudad de México o Guadalajara no busca «friso» ni «cielo raso». Busca aplanado, plafón, zoclo, plomero, banqueta. El catálogo de CotizaT se muestra con esos nombres. No es Neodata ni un visor BIM: es el flujo comercial de la reforma.",
                    "Los packs de estancia insertan un baño o una cocina escalados a los m². Las piezas fijas (inodoro, mueble) no se multiplican. Los productos van con foto: incluido, opcional o alternativa.",
                ],
            ),
            (
                "Margen en pesos, no a ciegas",
                [
                    "Cada partida puede llevar APU: materiales, mano de obra, equipo. Ves coste interno y beneficio en MXN antes de mandar. El cliente no ve esos números. Si una línea queda por debajo de tu umbral, la app avisa.",
                    "El espacio nace en MXN e IVA 16 %. Si cotizas también en dólares, cada documento congela su tasa. Un PDF enviado no se reescribe si mañana se mueve el tipo de cambio.",
                ],
            ),
            (
                "Sin CFDI, a propósito",
                [
                    "CotizaT no emite CFDI. La cotización es un documento comercial. El CFDI lo sigues generando con tu PAC o tu contador. Mezclar las dos cosas en el mismo PDF es el error que el producto evita.",
                    "El cliente no se registra. Recibe el PDF por WhatsApp o correo. El enlace privado con firma es opcional.",
                ],
            ),
            (
                "Cuánto cuesta el software (no el baño)",
                [
                    "El plan de lanzamiento es 89 US$ al año (habitual 109) o 9,99 US$ al mes el primer año. 7 días de prueba completa, sin tarjeta. El catálogo trae más de 3.000 partidas descompuestas; no publicamos el precio del cemento de la semana porque no somos un índice de mercado.",
                ],
            ),
        ],
        "faq": [
            {
                "q": "¿Es un programa para cotizar o solo un generador de PDF?",
                "a": "Arma la cotización con partidas, APU, opciones de producto y un PDF. No es un visor de planos ni emite CFDI.",
            },
            {
                "q": "¿Puedo cotizar en pesos mexicanos?",
                "a": "Sí. El espacio nace en MXN e IVA 16 %. También puedes emitir en USD, con tasa congelada por documento.",
            },
        ],
        "related": [
            ("Remodelación en México", "/mx/remodelacion"),
            ("Software de presupuestos en México", "/mx/software-presupuestos"),
            ("Cómo presupuestar una remodelación", "/guia/presupuesto-remodelacion"),
        ],
    },
    "metrados-peru": {
        "slug": "metrados-peru",
        "pais": "PE",
        "pais_nombre": "Perú",
        "pais_path": "/pe/",
        "kicker": "Perú · Metrados",
        "title": "CotizaT: metrados y APU en soles para Perú",
        "h1": "Metrados y APU en Perú (en soles, con IGV aparte del comprobante)",
        "description": (
            "Cómo armar metrados y APU de remodelación en Perú: cantidades por "
            "zona, tarrajeo, soles, RUC e IGV 18 %. No es un expediente S10."
        ),
        "lead": (
            "En Perú el presupuesto de obra arranca en el metrado: cuántos m², "
            "ml o und lleva cada partida. El APU dice de dónde sale el precio. "
            "CotizaT suma mediciones por zona y cierra en soles o USD, con RUC "
            "e IGV 18 %."
        ),
        "secciones": [
            (
                "Metrado primero, precio después",
                [
                    "Cocina 8 m² de tarrajeo, baño 4 m², pasadizo 6 m². La cantidad de la partida es la suma. El importe es cantidad × precio unitario. Si el precio unitario viene de un APU, el metrado y el descompuesto viven juntos, no en dos hojas que se desincronizan.",
                    "Eso no es un expediente S10 del Ministerio de Vivienda. CotizaT está pensado para remodelación residencial y comercial pequeña, no para licitación pública.",
                ],
            ),
            (
                "Tarrajeo, cielo raso, zócalo, gasfitero",
                [
                    "El catálogo se muestra con terminología de Perú. Vereda, no banqueta. Gasfitero, no plomero venezolano. Lima, Arequipa o el interior: el oficio es el mismo si cotizas por partidas.",
                    "El PDF va por WhatsApp. El cliente no entra a una plataforma. Si pide otro piso, reenvías una versión con el metrado nuevo y el total nuevo.",
                ],
            ),
            (
                "IGV 18 % en el documento, SUNAT en tu sistema",
                [
                    "Configuras el 18 % (o el que apliques) y el presupuesto lo calcula. No es asesoramiento tributario. El comprobante de pago SUNAT lo emites con tu sistema autorizado. CotizaT genera el documento comercial que presentas al cliente.",
                    "Puedes cerrar en soles o en USD. Cada presupuesto congela su tasa. Un PDF enviado no cambia si mañana se mueve el tipo de cambio.",
                ],
            ),
            (
                "APU editable, no una lista plana",
                [
                    "Materiales, mano de obra y equipo, con rendimiento. Cambias el cemento o la hora del oficial una vez; las partidas en edición se recalculan. Los metrados ya enviados quedan congelados.",
                    "Más de 3.000 partidas descompuestas en el catálogo propio. Importación desde Excel o CYPE si ya traes descompuestos.",
                ],
            ),
        ],
        "faq": [
            {
                "q": "¿Incluye metrados?",
                "a": "Sí: cantidades por partida y por zona. El APU es aparte, editable. El cierre puede ir en soles con IGV 18 %.",
            },
            {
                "q": "¿Sirve para un expediente S10?",
                "a": "No. No es un software de obra pública. Sirve para remodelación y obra privada pequeña.",
            },
        ],
        "related": [
            ("APU en Perú", "/pe/apu"),
            ("Software de presupuestos en Perú", "/pe/software-presupuestos"),
            ("Cómo hacer un presupuesto de obra", "/guia/presupuesto-de-obra"),
        ],
    },
    "presupuesto-usd-bs-venezuela": {
        "slug": "presupuesto-usd-bs-venezuela",
        "pais": "VE",
        "pais_nombre": "Venezuela",
        "pais_path": "/ve/",
        "kicker": "Venezuela · USD y Bs",
        "title": "CotizaT: presupuesto de obra en USD con equivalente en bolívares",
        "h1": "Presupuesto en USD y bolívares: la tasa se congela, el PDF no se mueve",
        "description": (
            "Cómo presupuestar remodelación en Venezuela en USD o Bs, con tasa "
            "congelada, RIF e IVA 16 %. El PDF de marzo no cambia en abril."
        ),
        "lead": (
            "En Venezuela se discute en dólares y a veces se cobra en bolívares. "
            "El error clásico es un Excel que «actualiza» un presupuesto ya "
            "enviado. CotizaT congela moneda y tasa en cada documento. RIF e "
            "IVA 16 % salen en el PDF; no es factura SENIAT."
        ),
        "secciones": [
            (
                "Dos monedas, un documento sellado",
                [
                    "Puedes cotizar en USD o en bolívares. La tasa de referencia queda guardada en ese presupuesto. Un PDF mandado en marzo no cambia si en abril se mueve el tipo de cambio. El cliente y tú miran el mismo papel.",
                    "Si más tarde haces una versión nueva (el cliente pidió otro cielo raso), esa versión tiene su propia tasa. La historia no se reescribe.",
                ],
            ),
            (
                "Friso, concreto, cielo raso, plomero",
                [
                    "El catálogo habla venezolano: Caracas, Valencia, Maracaibo. No es un software español traducido. El RIF sale en el documento. La factura fiscal la emites por el medio que te corresponda.",
                    "Cuando suben los materiales, ajustas el catálogo por porcentaje —todo o por capítulo— sin tocar los presupuestos ya enviados. El APU conectado recalcula las partidas en edición.",
                ],
            ),
            (
                "WhatsApp es el cierre, no otra plataforma",
                [
                    "El cliente no se registra. Recibe el PDF. Si pide quitar el porcelanato, editas, se crea una versión y copias: total anterior, total nuevo, qué cambió. Lo reenvías por el mismo chat.",
                    "Horas de cuadrilla y margen se quedan en la app. El PDF no lleva «5 horas de friso»: evita la reclamación imposible.",
                ],
            ),
            (
                "Pago de la licencia desde Venezuela",
                [
                    "El plan de lanzamiento es 89 US$ al año. Puedes pagar con Pago móvil, Binance, Kontigo, USDT o tarjeta. La tarjeta activa al confirmar; los métodos manuales se revisan en un máximo de 48 horas hábiles. 7 días de prueba, sin tarjeta.",
                    "No publicamos el precio del saco de cemento de esta semana. Eso lo pones tú en Recursos, que es donde tiene que vivir.",
                ],
            ),
        ],
        "faq": [
            {
                "q": "¿Puedo presupuestar en dólares y cobrar en bolívares?",
                "a": "Sí. Cada presupuesto congela su moneda y su tasa. El PDF no se reescribe si mañana se mueve el tipo de cambio.",
            },
            {
                "q": "¿Sustituye la factura fiscal venezolana?",
                "a": "No. Genera presupuestos y documentos de cobro comerciales. El RIF sale en el PDF; la factura la emites por el medio que te corresponda.",
            },
        ],
        "related": [
            ("Software de presupuestos en Venezuela", "/ve/software-presupuestos"),
            ("APU en Venezuela", "/ve/apu"),
            ("Cómo hacer un presupuesto de obra", "/guia/presupuesto-de-obra"),
        ],
    },
    "apu-dolares-ecuador": {
        "slug": "apu-dolares-ecuador",
        "pais": "EC",
        "pais_nombre": "Ecuador",
        "pais_path": "/ec/",
        "kicker": "Ecuador · APU en USD",
        "title": "CotizaT: APU en Ecuador, en dólares, con RUC",
        "h1": "APU en Ecuador: dólares nativos, RUC e IVA 15 %",
        "description": (
            "Análisis de precios unitarios para constructoras en Ecuador: "
            "hormigón, enlucido, tumbado, USD, RUC e IVA 15 %. Sin factura SRI."
        ),
        "lead": (
            "Ecuador ya cotiza en USD. No hace falta «convertir después». "
            "CotizaT nace en dólares, con RUC e IVA 15 %, y el catálogo habla "
            "hormigón, enlucido, tumbado, barredera y gasfitero."
        ),
        "secciones": [
            (
                "Dólar nativo, no una conversión improvisada",
                [
                    "El espacio no nace en otra moneda para luego aplicar una tasa. Ecuador usa USD. El RUC y el IVA 15 % se configuran al registrarte. Si mañana cambia la alícuota, la pones tú: CotizaT no decide impuestos.",
                    "Los documentos son comerciales. No sustituyen la factura electrónica que te exija el SRI.",
                ],
            ),
            (
                "Qué trae el APU el primer día",
                [
                    "Cada partida llega descompuesta en materiales, mano de obra y equipo, con rendimiento y precio. Editas un insumo y se recalcula el presupuesto. Más de 3.000 partidas en el catálogo propio; importación desde Excel o CYPE si ya tienes descompuestos.",
                    "Hormigón, no concreto venezolano. Enlucido y tumbado, no friso y cielo raso. El vocabulario es el de Quito o Guayaquil.",
                ],
            ),
            (
                "El flujo de la reforma, no el del SRI",
                [
                    "Armas el presupuesto, revisas margen y horas de cuadrilla, mandas el PDF por WhatsApp. Si hay cambios, reenvías total anterior y total nuevo. El cliente no se registra.",
                    "Las horas internas no van al PDF. El margen tampoco. El SRI no entra en CotizaT: tu facturación electrónica sigue donde ya la tienes.",
                ],
            ),
            (
                "Precio del software",
                [
                    "89 US$ al año de lanzamiento (habitual 109) o 9,99 US$ al mes el primer año. 7 días de prueba, sin tarjeta. Sin permanencia.",
                ],
            ),
        ],
        "faq": [
            {
                "q": "¿Nace en dólares o convierte desde otra moneda?",
                "a": "Nace en USD. Ecuador cotiza en dólares; no hay una conversión improvisada al registrarte.",
            },
            {
                "q": "¿Emite factura del SRI?",
                "a": "No. Los documentos son comerciales y no sustituyen la factura electrónica que te exija el SRI.",
            },
        ],
        "related": [
            ("APU en Ecuador", "/ec/apu"),
            ("Software de presupuestos en Ecuador", "/ec/software-presupuestos"),
            ("Qué es un APU (método)", "/guia/analisis-precios-unitarios"),
        ],
    },
}

ORDEN_ARTICULOS = (
    "apu-panete-colombia",
    "cotizar-remodelacion-mexico",
    "metrados-peru",
    "presupuesto-usd-bs-venezuela",
    "apu-dolares-ecuador",
)


def ficha_articulo(slug: str) -> dict | None:
    return ARTICULOS.get(str(slug or "").strip())


def lista_articulos() -> list[dict]:
    return [ARTICULOS[k] for k in ORDEN_ARTICULOS]


def articulo_de_pais(codigo: str) -> dict | None:
    codigo = str(codigo or "").strip().upper()
    for item in lista_articulos():
        if item["pais"] == codigo:
            return item
    return None
