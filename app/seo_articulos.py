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
                "De Excel a CotizaT",
                [
                    "Si ya exportas matrices de descompuestos en Excel (.xlsx), importas el archivo y se clasifican materiales, mano de obra y complementarios, sin perder filas. También pegas TSV desde una hoja o importas .bc3 (FIEBDC-3). El catálogo propio trae más de 3.000 partidas descompuestas y cientos de recursos; no empiezas la base de cero.",
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
                    "Más de 3.000 partidas descompuestas en el catálogo propio. Importación desde Excel (.xlsx) o BC3 si ya traes descompuestos.",
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
                    "Cada partida llega descompuesta en materiales, mano de obra y equipo, con rendimiento y precio. Editas un insumo y se recalcula el presupuesto. Más de 3.000 partidas en el catálogo propio; importación desde Excel (.xlsx) o BC3 si ya tienes descompuestos.",
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


ARTICULOS_EN: dict[str, dict] = {}


def ficha_articulo(slug: str, lang: str = "es") -> dict | None:
    slug = str(slug or "").strip()
    if lang == "en" and slug in ARTICULOS_EN:
        return ARTICULOS_EN[slug]
    # Los artículos británicos solo existen en inglés: pedirlos en español
    # devolvería un texto que no está traducido. Los de Estados Unidos,
    # Irlanda, Australia y Canadá viven en su propio módulo con la misma
    # regla.
    if lang == "en":
        from .seo_reino_unido import articulo as _articulo_uk

        uk = _articulo_uk(slug)
        if uk:
            return uk
        from .seo_articulos_mercados_en import articulo as _articulo_mercados_en

        mercado = _articulo_mercados_en(slug)
        if mercado:
            return mercado
    return ARTICULOS.get(slug)


def lista_articulos() -> list[dict]:
    return [ARTICULOS[k] for k in ORDEN_ARTICULOS]


def lista_articulos_en() -> list[dict]:
    """Artículos en inglés, incluidos los de mercado anglófono (GB + 4)."""
    from .seo_reino_unido import ORDEN_ARTICULOS as ORDEN_UK
    from .seo_reino_unido import articulo as _articulo_uk
    from .seo_articulos_mercados_en import ORDEN_ARTICULOS as ORDEN_EN
    from .seo_articulos_mercados_en import articulo as _articulo_mercados_en

    out = [ARTICULOS_EN[k] for k in ORDEN_ARTICULOS if k in ARTICULOS_EN]
    out.extend(_articulo_uk(slug) for slug in ORDEN_UK)
    out.extend(_articulo_mercados_en(slug) for slug in ORDEN_EN)
    return [a for a in out if a]


def articulo_de_pais(codigo: str, lang: str = "es") -> dict | None:
    codigo = str(codigo or "").strip().upper()
    fuente = lista_articulos_en() if lang == "en" else lista_articulos()
    for item in fuente:
        if item.get("pais") == codigo:
            return item
    return None
# This file is appended to seo_articulos.py
ARTICULOS_EN.update({
    "apu-panete-colombia": {
        "slug": "apu-panete-colombia",
        "pais": "CO",
        "pais_nombre": "Colombia",
        "pais_path": "/co/",
        "kicker": "Colombia · APU",
        "title": "CotizaT: how to build a render (panete) APU in Colombia without Excel",
        "h1": "How to build a render (panete) APU in Colombia (without the spreadsheet breaking)",
        "description": (
            "Method for a unit price analysis of render in Colombia: resources, "
            "productivity, COP and 19% VAT. No public-works AIU."
        ),
        "lead": (
            "In Colombia a serious estimate stands on the APU. Render is the example "
            "every remodeler knows: materials, foreman and helper, productivity per m2. "
            "This guide describes the method; CotizaT is the software that runs it in COP, "
            "with NIT and 19% VAT."
        ),
        "secciones": [
            (
                "What a render APU is (and what it is not)",
                [
                    "A unit price analysis breaks a line item's price into resources: kilos or bags of cement, sand, water, foreman hours, helper hours, sometimes scaffolding or mixer. Each line is productivity times price. The sum is the direct cost per m2. The selling price is a different figure: you apply profit.",
                    "That is not public-works AIU nor a tender document. CotizaT does not calculate administration, contingencies or profit for public contracts. If you estimate private remodels or work for an individual or an SAS, the render APU is exactly this flow.",
                ],
            ),
            (
                "Why the render spreadsheet breaks in Bogota or Medellin",
                [
                    "The sheet starts fine: one tab for resources, another for line items, a productivity formula. The problem arrives on Tuesday, when cement or the foreman's hourly rate goes up. You have to find every line item that uses that resource. If you miss one, the Chapinero bathroom comes out at 8% margin and you thought it was 28%.",
                    "The second problem is versioning. You send the PDF, the client asks for another render, you rewrite the sheet and no longer know which file was approved. A connected APU changes the resource once and recalculates the line items in edit. Estimates already sent are not touched.",
                ],
            ),
            (
                "The three blocks of the breakdown",
                [
                    "Materials: what is spent per m2 (with waste if you use it). Labor: productivity in foreman and helper hours. Equipment: only if it applies (mixer, scaffolding). On top of that base you can add complementary direct costs as a percentage. The client does not see that breakdown in the PDF; they see the line item, quantity, price and total.",
                    "Crew hours come from the labor rows. They exist so you do not promise an 80 m2 render by Friday if productivity says otherwise. They are not printed to the client.",
                ],
            ),
            (
                "COP, NIT and 19% VAT",
                [
                    "At signup you choose Colombia and the workspace is born in COP, with NIT and 19% VAT. You can also quote in USD; each estimate freezes its rate. The document's VAT is configured by you: it is not tax advice.",
                    "CotizaT does not issue DIAN electronic invoicing. The estimate is a commercial document. Render is called panete, not friso.",
                ],
            ),
            (
                "From Excel to CotizaT",
                [
                    "If you already export breakdown matrices in Excel (.xlsx), import the file and materials, labor and complementary costs are classified without losing rows. You can also paste TSV from Excel or import .bc3 (FIEBDC-3).",
                    "Launch plan: 89 US$ per year (usual 109) or 9.99 US$ per month the first year. 7 free days, no card.",
                ],
            ),
        ],
        "faq": [
            {"q": "Does CotizaT calculate Colombian AIU?", "a": "No. It is for private remodels and work, not public contracts."},
            {"q": "Does the render come out with Colombian terminology?", "a": "Yes. panete, guardaescoba, andamio, plomero. Not friso or zocalo."},
        ],
    },
    "cotizar-remodelacion-mexico": {
        "slug": "cotizar-remodelacion-mexico",
        "pais": "MX",
        "pais_nombre": "Mexico",
        "pais_path": "/mx/",
        "kicker": "Mexico · quote",
        "title": "CotizaT: from the site visit to a remodel quote in MXN",
        "h1": "From the site visit to a quote in Mexico (in pesos, with your margin)",
        "description": (
            "How to go from a site visit to a remodel quote in Mexico: plaster, "
            "ceiling, product options, MXN and 16% VAT. No CFDI."
        ),
        "lead": (
            "In Mexico the client asks for a quote as much as an estimate. The visit, "
            "the measurements, the plaster, the ceiling and the PDF you resend when "
            "the floor changes. This guide is that trade. CotizaT is born in MXN "
            "with RFC and 16% VAT."
        ),
        "secciones": [
            (
                "The visit is not the document",
                [
                    "You measure the bathroom, note the plaster, the baseboard, the bench if any. In the truck there is still no quote: there are quantities. The document is built afterwards, by sections, with prices and margin.",
                    "If you build that in Word, every change of porcelain is a new file with a worse name. CotizaT seals versions: previous total, new total, what changed.",
                ],
            ),
            (
                "Plaster, ceiling and baseboard: the catalog must speak Mexican",
                [
                    "A contractor in Mexico City or Guadalajara does not search for friso or cielo raso. They search for aplanado, plafon, zoclo, plomeria. CotizaT's catalog is shown in that vocabulary.",
                    "Room packs insert a bathroom or kitchen scaled to the real square meters. Fixed pieces (toilet, vanity) are not multiplied.",
                ],
            ),
            (
                "Margin in pesos, not blind",
                [
                    "Each line item can carry an APU: materials, labor, equipment. You see internal cost and profit in MXN before sending. That is the difference between quoting at 12% and thinking it was 28%.",
                    "The workspace is born in MXN with 16% VAT. If you also quote in dollars, each document freezes its rate. A sent PDF does not change.",
                ],
            ),
            (
                "No CFDI, on purpose",
                [
                    "CotizaT does not issue CFDI. The quote is a commercial document. You keep generating CFDI with your PAC or your accountant. Mixing the two would be promising something the software does not do.",
                    "The client does not register. They receive the PDF by WhatsApp or email. The private link with signature is optional.",
                ],
            ),
            (
                "What the software costs (not the bathroom)",
                [
                    "Launch plan: 89 US$ per year (usual 109) or 9.99 US$ per month the first year. 7 full free days, no card.",
                ],
            ),
        ],
        "faq": [
            {"q": "Is it a quoting program or just a PDF generator?", "a": "It quotes: catalog, sections, quantities, prices, VAT and PDF. The PDF is the output, not the product."},
            {"q": "Can I quote in Mexican pesos?", "a": "Yes. MXN with 16% VAT, or USD with a frozen rate per document."},
        ],
    },
    "metrados-peru": {
        "slug": "metrados-peru",
        "pais": "PE",
        "pais_nombre": "Peru",
        "pais_path": "/pe/",
        "kicker": "Peru · measurements",
        "title": "CotizaT: measurements and APU in soles for Peru",
        "h1": "Measurements and APU in Peru (in soles, with IGV separate from the receipt)",
        "description": (
            "How to build measurements and APU for a remodel in Peru: quantities by zone, "
            "plaster, soles, RUC and 18% IGV. Not an S10 file."
        ),
        "lead": (
            "In Peru a construction estimate starts with the measurement: how many m2, "
            "ml or units each line item takes. The APU says where the price comes from. "
            "CotizaT sums measurements by zone and closes in soles or USD, with RUC and 18% IGV."
        ),
        "secciones": [
            (
                "Measurement first, price afterwards",
                [
                    "Kitchen 8 m2 of plaster, bathroom 4 m2, hallway 6 m2. The line item quantity is the sum. The amount is quantity times price. The margin is calculated before sending, not after.",
                    "That is not an S10 file from the Ministry of Housing. CotizaT is meant for private residential and commercial remodels: the client is an individual or a company, not a public tender.",
                ],
            ),
            (
                "Plaster, ceiling, baseboard, plumber",
                [
                    "The catalog is shown in Peruvian terminology. Sidewalk, not curb. Plumber, not the Venezuelan term. Lima, Arequipa or Trujillo: the vocabulary is the same.",
                    "The PDF goes by WhatsApp. The client does not enter a platform. If they ask for another floor, you resend a version with the new measurement.",
                ],
            ),
            (
                "18% IGV in the document, SUNAT in your system",
                [
                    "You configure 18% (or whatever you apply) and the estimate calculates it. It is not tax advice. The payment receipt is issued by your electronic invoicing system, not by CotizaT.",
                    "You can close in soles or in USD. Each estimate freezes its rate. A sent PDF does not change if the exchange rate moves tomorrow.",
                ],
            ),
            (
                "Editable APU, not a flat list",
                [
                    "Materials, labor and equipment, with productivity. Change cement or the foreman's hourly rate once; the line items in edit recalculate. The estimates already sent do not change.",
                    "More than 3,000 decomposed line items in the own catalog. Import from Excel (.xlsx) or BC3 if you already bring decomposed breakdowns.",
                ],
            ),
        ],
        "faq": [
            {"q": "Does it include measurements?", "a": "Yes. By zone, with sum to the line item quantity. It is not an S10 file."},
            {"q": "Is it for an S10 file?", "a": "No. It is for private remodels. Public works require another flow."},
        ],
    },
    "presupuesto-usd-bs-venezuela": {
        "slug": "presupuesto-usd-bs-venezuela",
        "pais": "VE",
        "pais_nombre": "Venezuela",
        "pais_path": "/ve/",
        "kicker": "Venezuela · USD/Bs",
        "title": "CotizaT: construction estimate in USD with bolivar equivalent",
        "h1": "Estimate in USD and bolivars: the rate freezes, the PDF does not move",
        "description": (
            "How to estimate a remodel in Venezuela in USD or Bs, with a frozen rate, "
            "RIF and 16% VAT. The March PDF does not change in April."
        ),
        "lead": (
            "In Venezuela you discuss in dollars and sometimes collect in bolivars. "
            "The classic mistake is a spreadsheet that updates an estimate already sent. "
            "CotizaT freezes currency and rate in each document. RIF and 16% VAT."
        ),
        "secciones": [
            (
                "Two currencies, one sealed document",
                [
                    "You can quote in USD or in bolivars. The reference rate is stored in that estimate. A PDF sent in March does not change in April.",
                    "If you later make a new version (the client asked for another ceiling), that version has its own rate. History is not overwritten.",
                ],
            ),
            (
                "Render, concrete, ceiling, plumber",
                [
                    "The catalog speaks Venezuelan: Caracas, Valencia, Maracaibo. It is not a translated Spanish software. The RIF appears in the document.",
                    "When materials go up, adjust the catalog by percentage, all or by section, without touching the estimates already sent.",
                ],
            ),
            (
                "WhatsApp is the closing, not another platform",
                [
                    "The client does not register. They receive the PDF. If they ask to remove the porcelain, you edit, a version is created and you copy: previous total, new total, line items added or removed.",
                    "Crew hours and margin stay in the app. The PDF does not carry 5 hours of render: it avoids the impossible claim.",
                ],
            ),
            (
                "Paying the license from Venezuela",
                [
                    "Launch plan: 89 US$ per year. You can pay with Pago movil, Binance, Kontigo, USDT or card. Card activates on confirmation; manual methods are reviewed within 48 business hours.",
                    "We do not publish the price of a cement bag this week. You set that in Resources, where it belongs.",
                ],
            ),
        ],
        "faq": [
            {"q": "Can I estimate in dollars and collect in bolivars?", "a": "Yes. Each document freezes its currency and rate."},
            {"q": "Does it replace the Venezuelan tax invoice?", "a": "No. The estimate is a commercial document. The fiscal invoice is issued through your own means."},
        ],
    },
    "apu-dolares-ecuador": {
        "slug": "apu-dolares-ecuador",
        "pais": "EC",
        "pais_nombre": "Ecuador",
        "pais_path": "/ec/",
        "kicker": "Ecuador · APU",
        "title": "CotizaT: APU in Ecuador, in dollars, with RUC",
        "h1": "APU in Ecuador: native dollars, RUC and 15% VAT",
        "description": (
            "Unit price analysis for contractors in Ecuador: concrete, plaster, "
            "ceiling, USD, RUC and 15% VAT. No SRI invoice."
        ),
        "lead": (
            "Ecuador already quotes in USD. No need to convert afterwards. "
            "CotizaT is born in dollars, with RUC and 15% VAT, and the catalog "
            "speaks concrete, plaster, ceiling, broom and plumber."
        ),
        "secciones": [
            (
                "Native dollars, not an improvised conversion",
                [
                    "The workspace is not born in another currency to then apply a rate. Ecuador uses USD. RUC and 15% VAT are configured at signup.",
                    "Documents are commercial. They do not replace the electronic invoice your SRI may require.",
                ],
            ),
            (
                "What the APU brings on day one",
                [
                    "Each line item arrives decomposed into materials, labor and equipment, with productivity and price. You edit one input and the line items in edit recalculate.",
                    "Concrete, not Venezuelan concrete. Plaster and ceiling, not render and drop ceiling. The vocabulary is that of Quito or Guayaquil.",
                ],
            ),
            (
                "The remodel flow, not the SRI's",
                [
                    "You build the estimate, review margin and crew hours, send the PDF by WhatsApp. If there are changes, you resend previous total, new total and what changed.",
                    "Internal hours do not go to the PDF. Neither does margin. The SRI does not enter CotizaT: your electronic invoicing stays where it is.",
                ],
            ),
            (
                "Software price",
                [
                    "89 US$ per year at launch (usual 109) or 9.99 US$ per month the first year. 7 free days, no card. No lock-in.",
                ],
            ),
        ],
        "faq": [
            {"q": "Is it born in dollars or converted from another currency?", "a": "Born in dollars. Ecuador uses USD natively."},
            {"q": "Does it issue an SRI invoice?", "a": "No. The estimate is a commercial document."},
        ],
    },
})
