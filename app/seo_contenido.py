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
            "Qué es un software de presupuestos de obra",
            [
                "Un software de presupuestos de construcción no es un Word con tabla. Es la herramienta con la que una constructora o un reformista arma capítulos, partidas, cantidades, precios, IVA y un PDF que el cliente entiende. CotizaT está hecho para ese oficio en España y Latinoamérica: catálogo con análisis de precios unitarios, margen interno, horas de cuadrilla y envío por WhatsApp o email.",
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
            "Cada país, su propio catálogo de precios",
            [
                "No es un catálogo genérico con un rate. Cada mercado tiene su referencia: España en EUR con NIF e IVA 21 % y terminología de reforma (pladur, falso techo, alicatado, fontanería); Colombia en COP con NIT e IVA 19 % (pañete, guardaescoba); México en MXN con RFC e IVA 16 %; Venezuela en USD o Bs con RIF e IVA 16 %.",
                "Por eso el país se elige al entrar, y por eso CotizaT no conviertes \"friso\" a \"pañete\" con un find-and-replace: la landing, el ejemplo, el IVA, el ID fiscal y las referencias de precios cambian con el país. Elegir bien tu mercado no es cosmético; es lo que hace que los precios sean los de tu obra.",
            ],
        ),
        (
            "España, primer mercado europeo",
            [
                "España tiene un hueco claro para el pequeño reformista: cotizar reformas en EUR, con NIF, IVA 21 % y un presupuesto que el cliente pueda enviar a un albañil o a una gestoría. CotizaT nace con vocabulario español (pladur, falso techo, alicatado, fontanero), referencias nacionales en euros y BC3/FIEBDC-3 para quien trabaja con bases de precios.",
                "El resto de mercados hispanos sigue siendo el foco: Venezuela, Colombia, México, Ecuador, Perú, Chile y Argentina. Todo corre en una sola aplicación, sin duplicar catálogos.",
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
    "PA": [
        (
            "Presupuestos y APU en dólares para Panamá",
            [
                "Panamá cotiza en USD (balboa PAB paridad 1:1). CotizaT nace en dólares, con RUC e ITBMS 7 %, y el catálogo habla concreto, repello, cielo raso, zócalo y plomero. Cada partida trae APU editable: rendimientos y precios de recursos con referencias nacionales de Panamá.",
                "El flujo es el de un remodelador en Ciudad de Panamá, San Miguelito o David: armas el presupuesto, lo mandas por WhatsApp y, si hay cambios, reenvías una versión con el resumen del total anterior y el nuevo. Precios de referencia: cemento $8.25 por saco 42.5kg, bloque $0.95, arena $34/m3, concreto 210 $125/m3.",
            ],
        ),
        (
            "Sin factura electrónica DGI, con ITBMS 7 %",
            [
                "Los documentos son comerciales. No sustituyen la factura electrónica que te exija la DGI. El ITBMS 7 % del presupuesto lo configuras tú; no es asesoramiento tributario.",
            ],
        ),
        (
            "Dólar nativo y formaleta, no conversión improvisada",
            [
                "Panamá ya cotiza en USD. El espacio no nace en otra moneda para luego «convertir». El RUC y el ITBMS 7 % se configuran al registrarte. Terminología local: repello (no friso), zócalo (no rodapié), formaleta (no encofrado), varilla (no cabilla).",
            ],
        ),
    ],
    "SV": [
        (
            "Presupuestos y APU en dólares para El Salvador",
            [
                "El Salvador cotiza en USD desde 2001. CotizaT nace en dólares, con NIT e IVA 13 %, y el catálogo habla concreto, repello, cielo falso, zócalo y fontanero. Cada partida trae APU editable: rendimientos y precios de recursos con referencias nacionales de El Salvador.",
                "El flujo es el de un remodelador en San Salvador, Santa Ana o San Miguel: armas el presupuesto, lo mandas por WhatsApp y, si hay cambios, reenvías una versión con el resumen del total anterior y el nuevo. Precios de referencia: cemento $8.73 por saco 42.5kg (CASALCO), bloque $0.40, arena $35/m3, grava $45.05/m3, concreto 210 $135.35/m3.",
            ],
        ),
        (
            "Sin factura del Ministerio de Hacienda, con IVA 13 %",
            [
                "Los documentos son comerciales. No sustituyen la factura electrónica que te exija Hacienda. El IVA 13 % del presupuesto lo configuras tú; no es asesoramiento tributario.",
            ],
        ),
        (
            "Dólar nativo y tabla yeso, no conversión improvisada",
            [
                "El Salvador ya cotiza en USD. El espacio no nace en otra moneda para luego «convertir». El NIT y el IVA 13 % se configuran al registrarte. Terminología local: repello (no friso), cielo falso (no cielo raso), zócalo (no rodapié), fontanero (no plomero), tabla yeso (no drywall), varilla / hierro corrugado (no cabilla).",
            ],
        ),
    ],
    "CL": [
        (
            "Presupuestos y APU en pesos chilenos para Chile",
            [
                "Chile cotiza en CLP. CotizaT nace en pesos chilenos, con RUT e IVA 19 %, y el catálogo habla hormigón, estuco, cielo falso, guardapolvo y gasfíter. Cada partida trae APU editable: rendimientos y precios de recursos con referencias nacionales de Chile.",
                "El flujo es el de un remodelador en Santiago, Valparaíso o Concepción: armas el presupuesto, lo mandas por WhatsApp y, si hay cambios, reenvías una versión con el resumen del total anterior y el nuevo. Precios de referencia: cemento $4.790 por saco 25kg (Sodimac Melón), bloque $1.840, arena $33.190/m3, hormigón H25 $110.000/m3.",
            ],
        ),
        (
            "Sin factura del SII, con IVA 19 %",
            [
                "Los documentos son comerciales. No sustituyen la factura electrónica que te exija el SII. El IVA 19 % del presupuesto lo configuras tú; no es asesoramiento tributario.",
            ],
        ),
        (
            "Pesos chilenos y moldaje, no conversión improvisada",
            [
                "Chile ya cotiza en CLP. El espacio no nace en USD para luego «convertir» con una tasa inventada: nace en CLP con tasa verificada 925.90 CLP/USD. Terminología local: hormigón (no concreto), estuco (no friso), cielo falso (no cielo raso), guardapolvo (no rodapié), gasfíter (no plomero), moldaje (no encofrado), fierro (no cabilla), ampolleta (no bombillo), volcanita (no drywall).",
            ],
        ),
    ],
    "AR": [
        (
            "Presupuestos y APU en pesos argentinos para Argentina",
            [
                "Argentina cotiza en ARS. CotizaT nace en pesos argentinos, con CUIT e IVA 21 %, y el catálogo habla hormigón, revoque, cielorraso, zócalo y plomero. Cada partida trae APU editable: rendimientos y precios de recursos con referencias nacionales de Argentina.",
                "El flujo es el de un remodelador en Buenos Aires, Córdoba o Rosario: armas el presupuesto, lo mandas por WhatsApp y, si hay cambios, reenvías una versión con el resumen del total anterior y el nuevo. Precios de referencia: cemento $11.433 por bolsa 50kg (Loma Negra/Holcim), bloque $1.500, arena $33.500/m3, hormigón H21 $168.478/m3.",
            ],
        ),
        (
            "Sin factura AFIP, con IVA 21 %",
            [
                "Los documentos son comerciales. No sustituyen la factura electrónica que te exija AFIP. El IVA 21 % del presupuesto lo configuras tú; no es asesoramiento tributario. El CUIT sale en el PDF.",
            ],
        ),
        (
            "Pesos argentinos y Durlock, no conversión improvisada",
            [
                "Argentina ya cotiza en ARS. El espacio no nace en USD para luego «convertir» con una tasa inventada: nace en ARS con tasa verificada 1497.38 ARS/USD. Terminología local: hormigón (no concreto), revoque (no friso), cielorraso (no cielo raso), zócalo (no rodapié), plomero (también sanitarista), hierro redondo / malla sima / pastina (no cabilla / electrosoldada / fragüe), mesada (no mesón), canilla (no grifo), térmica (no breaker), Durlock (no drywall), placard (no closet).",
            ],
        ),
    ],
    "DO": [
        (
            "Presupuestos y APU en pesos dominicanos para República Dominicana",
            [
                "República Dominicana cotiza en DOP. CotizaT nace en pesos dominicanos, con RNC e ITBIS 18 %, y el catálogo habla hormigón, pañete, plafón, zócalo y plomero. Cada partida trae APU editable con referencias nacionales de RD.",
                "El flujo es el de un remodelador en Santo Domingo, Santiago o La Romana: armas el presupuesto, lo mandas por WhatsApp y, si hay cambios, reenvías una versión con el resumen del total anterior y el nuevo. Precios de referencia: cemento RD$535 por funda 94lb, block 6'' RD$42, arena RD$1.550/m3, grava RD$1.700/m3.",
            ],
        ),
        (
            "Sin comprobante DGII, con ITBIS 18 %",
            [
                "Los documentos son comerciales. No sustituyen el comprobante fiscal que te exija DGII. El ITBIS 18 % del presupuesto lo configuras tú; no es asesoramiento tributario.",
            ],
        ),
        (
            "Pesos dominicanos y sheetrock, no conversión improvisada",
            [
                "RD ya cotiza en DOP. El espacio no nace en USD para luego «convertir» con tasa inventada: nace en DOP con tasa verificada 58.33 DOP/USD. Terminología local: hormigón (no concreto), pañete (no friso), plafón (no cielo raso), zócalo (no rodapié), plomero, block (no bloque), varilla (no cabilla), sheetrock (no drywall).",
            ],
        ),
    ],
    "UY": [
        (
            "Presupuestos y APU en pesos uruguayos para Uruguay",
            [
                "Uruguay cotiza en UYU. CotizaT nace en pesos uruguayos, con RUT e IVA 22 %, y el catálogo habla hormigón, revoque, cielorraso, zócalo y sanitario. Cada partida trae APU editable con referencias nacionales de Uruguay.",
                "El flujo es el de un remodelador en Montevideo, Canelones o Maldonado: armas el presupuesto, lo mandas por WhatsApp y, si hay cambios, reenvías una versión con el resumen del total anterior y el nuevo. Precios de referencia: cemento $240 por bolsa 25kg, bloque 15x19x39 $70, arena $1.200/m3, hormigón $5.500/m3.",
            ],
        ),
        (
            "Sin factura DGI, con IVA 22 %",
            [
                "Los documentos son comerciales. No sustituyen la factura electrónica que te exija DGI. El IVA 22 % del presupuesto lo configuras tú; no es asesoramiento tributario.",
            ],
        ),
        (
            "Pesos uruguayos y Durlock, no conversión improvisada",
            [
                "Uruguay ya cotiza en UYU. El espacio no nace en USD para luego «convertir» con tasa inventada: nace en UYU con tasa verificada 40.21 UYU/USD. Terminología local: hormigón (no concreto), revoque (no friso), cielorraso (no cielo raso), zócalo (no rodapié), sanitario (no plomero), varilla / hierro / malla electrosoldada, mesada (no mesón), canilla (no grifo), térmica (no breaker), Durlock (no drywall), placard (no closet).",
            ],
        ),
    ],
    "PY": [
        (
            "Presupuestos y APU en guaraníes para Paraguay",
            [
                "Paraguay cotiza en PYG, sin decimales. CotizaT nace en guaraníes, con RUC e IVA 10 %, y el catálogo habla hormigón, revoque, cielorraso, zócalo y plomero. Cada partida trae APU editable con referencias nacionales de Paraguay.",
                "El flujo es el de un remodelador en Asunción, Ciudad del Este o Encarnación: armas el presupuesto, lo mandas por WhatsApp y, si hay cambios, reenvías una versión con el resumen del total anterior y el nuevo. Precios de referencia: cemento Gs 59.000 por bolsa 50kg, bloque Gs 5.300, piedra bruta Gs 104.000/m3, hormigón Gs 650.000/m3.",
            ],
        ),
        (
            "Sin factura SET, con IVA 10 % y guaraníes sin decimales",
            [
                "Los documentos son comerciales. No sustituyen la factura electrónica que te exija la SET. El IVA 10 % del presupuesto lo configuras tú. Los importes en guaraníes se muestran sin decimales, como es norma local.",
            ],
        ),
        (
            "Guaraníes nativos y Durlock, no conversión improvisada",
            [
                "Paraguay ya cotiza en PYG. El espacio no nace en USD para luego «convertir» con tasa inventada: nace en PYG con tasa verificada 5946.10 PYG/USD. Terminología local: hormigón (no concreto), revoque (no friso), cielorraso (no cielo raso), zócalo (no rodapié), plomero, varilla (no cabilla), mesada (no mesón), canilla (no grifo), llave térmica (no breaker), Durlock (no drywall), placard (no closet).",
            ],
        ),
    ],
    "ES": [
        (
            "Software de presupuestos para reformas y obra en España",
            [
                "En España el presupuesto de una reforma se discute en euros, con IVA y NIF en el documento. CotizaT arma capítulos, partidas y análisis de precios unitarios en EUR, con IVA 21 % configurable. El catálogo muestra hormigón, pladur, falso techo, alicatado y fontanería; no «concreto» ni «friso».",
                "Está pensado para reformistas, contratistas y pequeñas constructoras de 2 a 15 personas que hoy cotizan en Excel o Word. No es un Presto ni un Arquímedes de licitación pública: es el flujo comercial de una reforma —medir, presupuestar, enviar y reenviar cambios.",
            ],
        ),
        (
            "Del visado a la obra, con BC3 y medición sobre planos",
            [
                "El cliente no entra a ninguna plataforma. Tú mides, armas el presupuesto por capítulos, revisas margen y horas de cuadrilla, y mandas el PDF por WhatsApp o email. Si el cliente cambia el solado, editas, se crea una versión y reenvías con el resumen de qué cambió.",
                "CotizaT importa BC3 (FIEBDC-3): capítulos, partidas, mediciones y precios. También mide sobre planos en modo manual asistido —subes PNG/JPG/PDF, calibras escala y sacas líneas, áreas y conteos sin IA ni coste por uso. Si trabajas licitación pública que exige exportar BC3 con certificaciones y residuos, aún no es tu software; si haces reforma residencial y comercial que recibe BC3 del arquitecto, el flujo es el que ya usas.",
            ],
        ),
        (
            "IVA y NIF en el documento, factura aparte",
            [
                "Configuras el IVA (21 % general, o el reducido que apliques) y el presupuesto lo calcula. No es asesoramiento fiscal. El NIF o CIF sale en el PDF. La factura la emites con tu sistema o tu gestor; CotizaT genera el presupuesto comercial que presentas al cliente.",
            ],
        ),
        (
            "Euros nativos, no una conversión del catálogo",
            [
                "Los recursos del catálogo tienen referencias de mercado en euros para España, y el presupuesto puede nacer directamente en EUR. Si prefieres trabajar en USD como referencia, cada documento congela su tasa: un PDF de marzo no cambia en abril aunque se mueva el tipo de cambio.",
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
                "Excel y BC3",
                [
                    "Si ya exportas matrices de descompuestos en Excel (.xlsx), se pueden importar clasificando materiales, mano de obra y complementarios, sin perder filas. También se pega TSV desde Excel o se importa .bc3 (FIEBDC-3).",
                ],
            ),
            (
                "Qué no cubre este APU",
                [
                    "No calcula AIU de contrato estatal colombiano y no exporta BC3/FIEBDC con certificaciones. Sí importa BC3 de arquitectos y sí mide sobre planos en modo manual asistido (sin IA). El APU de CotizaT es el de la obra privada: recursos, rendimientos y precio de venta que tú decides.",
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
    slug = str(slug or "").strip()
    if slug in GUIAS:
        return GUIAS[slug]
    from .seo_articulos import ficha_articulo

    return ficha_articulo(slug)


def lista_guias() -> list[dict]:
    return [GUIAS[k] for k in ("presupuesto-de-obra", "analisis-precios-unitarios", "presupuesto-remodelacion")]


def lista_todas_guias() -> list[dict]:
    from .seo_articulos import lista_articulos

    return lista_guias() + lista_articulos()


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
            "Importas el .xlsx o pegas TSV. El oficial y el cemento se editan en Recursos y caen a las partidas. El presupuesto enviado no se reescribe.",
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
    ("PA", "software-presupuestos"): [
        (
            "Software de presupuestos en dólares para Panamá",
            "Panamá ya cotiza en USD (PAB paridad 1:1). El espacio nace en dólares, con RUC e ITBMS 7 %, no en otra moneda «para convertir después». Concreto, repello, cielo raso, zócalo, plomero, formaleta.",
        ),
    ],
    ("PA", "apu"): [
        (
            "APU en USD, con RUC e ITBMS 7 %",
            "Descompuestos editables en dólares con referencias de Panamá: cemento $8.25/saco, bloque $0.95, arena $34/m3. El ITBMS 7 % del documento lo pones tú. No emite factura DGI.",
        ),
    ],
    ("PA", "remodelacion"): [
        (
            "Reforma en Ciudad de Panamá o David, PDF por WhatsApp",
            "Pack de estancia, repello y cielo raso, productos con foto. Si hay cambios, reenvías total anterior y total nuevo. El cliente no se registra.",
        ),
    ],
    ("SV", "software-presupuestos"): [
        (
            "Software de presupuestos en dólares para El Salvador",
            "El Salvador ya cotiza en USD desde 2001. El espacio nace en dólares, con NIT e IVA 13 %, no en otra moneda «para convertir después». Concreto, repello, cielo falso, zócalo, fontanero, tabla yeso.",
        ),
    ],
    ("SV", "apu"): [
        (
            "APU en USD, con NIT e IVA 13 %",
            "Descompuestos editables en dólares con referencias de El Salvador: cemento $8.73/saco CASALCO, bloque $0.40, arena $35/m3, concreto $135.35/m3. El IVA 13 % lo pones tú. No emite factura Hacienda.",
        ),
    ],
    ("SV", "remodelacion"): [
        (
            "Reforma en San Salvador o Santa Ana, PDF por WhatsApp",
            "Pack de estancia, repello y cielo falso, productos con foto. Si hay cambios, reenvías total anterior y total nuevo. El cliente no se registra.",
        ),
    ],
    ("CL", "software-presupuestos"): [
        (
            "Software de presupuestos en pesos chilenos para Chile",
            "Chile ya cotiza en CLP, con RUT e IVA 19 %. El espacio nace en CLP, no en USD «para convertir después». Hormigón, estuco, cielo falso, guardapolvo, gasfíter, moldaje, fierro.",
        ),
    ],
    ("CL", "apu"): [
        (
            "APU en CLP, con RUT e IVA 19 %",
            "Descompuestos editables en pesos chilenos con referencias de Chile: cemento $4.790/saco 25kg, bloque $1.840, arena $33.190/m3, hormigón $110.000/m3. El IVA 19 % lo pones tú. No emite factura SII.",
        ),
    ],
    ("CL", "remodelacion"): [
        (
            "Reforma en Santiago o Concepción, PDF por WhatsApp",
            "Pack de estancia, estuco y cielo falso, productos con foto. Si hay cambios, reenvías total anterior y total nuevo. El cliente no se registra.",
        ),
    ],
    ("AR", "software-presupuestos"): [
        (
            "Software de presupuestos en pesos argentinos para Argentina",
            "Argentina ya cotiza en ARS, con CUIT e IVA 21 %. El espacio nace en ARS, no en USD «para convertir después». Hormigón, revoque, cielorraso, zócalo, plomero, hierro.",
        ),
    ],
    ("AR", "apu"): [
        (
            "APU en ARS, con CUIT e IVA 21 %",
            "Descompuestos editables en pesos argentinos con referencias de Argentina: cemento $11.433/bolsa 50kg, bloque $1.500, arena $33.500/m3, hormigón H21 $168.478/m3. El IVA 21 % lo pones tú. No emite factura AFIP.",
        ),
    ],
    ("AR", "remodelacion"): [
        (
            "Reforma en Buenos Aires o Córdoba, PDF por WhatsApp",
            "Pack de estancia, revoque y cielorraso, productos con foto. Si hay cambios, reenvías total anterior y total nuevo. El cliente no se registra.",
        ),
    ],
    ("DO", "software-presupuestos"): [
        (
            "Software de presupuestos en pesos dominicanos para República Dominicana",
            "RD ya cotiza en DOP, con RNC e ITBIS 18 %. El espacio nace en DOP, no en USD «para convertir después». Hormigón, pañete, plafón, zócalo, plomero, block, varilla, sheetrock.",
        ),
    ],
    ("DO", "apu"): [
        (
            "APU en DOP, con RNC e ITBIS 18 %",
            "Descompuestos editables en pesos dominicanos con referencias de RD: cemento RD$535/funda 94lb, block RD$42, arena RD$1.550/m3. El ITBIS 18 % lo pones tú. No emite comprobante DGII.",
        ),
    ],
    ("DO", "remodelacion"): [
        (
            "Reforma en Santo Domingo o Santiago, PDF por WhatsApp",
            "Pack de estancia, pañete y plafón, productos con foto. Si hay cambios, reenvías total anterior y total nuevo. El cliente no se registra.",
        ),
    ],
    ("UY", "software-presupuestos"): [
        (
            "Software de presupuestos en pesos uruguayos para Uruguay",
            "Uruguay ya cotiza en UYU, con RUT e IVA 22 %. El espacio nace en UYU, no en USD «para convertir después». Hormigón, revoque, cielorraso, zócalo, sanitario.",
        ),
    ],
    ("UY", "apu"): [
        (
            "APU en UYU, con RUT e IVA 22 %",
            "Descompuestos editables en pesos uruguayos con referencias de Uruguay: cemento $240/bolsa 25kg, bloque $70, arena $1.200/m3, hormigón $5.500/m3. El IVA 22 % lo pones tú. No emite factura DGI.",
        ),
    ],
    ("UY", "remodelacion"): [
        (
            "Reforma en Montevideo o Maldonado, PDF por WhatsApp",
            "Pack de estancia, revoque y cielorraso, productos con foto. Si hay cambios, reenvías total anterior y total nuevo. El cliente no se registra.",
        ),
    ],
    ("PY", "software-presupuestos"): [
        (
            "Software de presupuestos en guaraníes para Paraguay",
            "Paraguay ya cotiza en PYG sin decimales, con RUC e IVA 10 %. El espacio nace en PYG, no en USD «para convertir después». Hormigón, revoque, cielorraso, zócalo, plomero.",
        ),
    ],
    ("PY", "apu"): [
        (
            "APU en PYG, con RUC e IVA 10 %",
            "Descompuestos editables en guaraníes con referencias de Paraguay: cemento Gs 59.000/bolsa 50kg, bloque Gs 5.300, piedra Gs 104.000/m3, hormigón Gs 650.000/m3. El IVA 10 % lo pones tú. Sin decimales en PYG.",
        ),
    ],
    ("PY", "remodelacion"): [
        (
            "Reforma en Asunción o Ciudad del Este, PDF por WhatsApp",
            "Pack de estancia, revoque y cielorraso, productos con foto. Si hay cambios, reenvías total anterior y total nuevo. El cliente no se registra.",
        ),
    ],
    ("BO", "software-presupuestos"): [
        (
            "Software de presupuestos en bolivianos para Bolivia",
            "Bolivia ya cotiza en BOB, con NIT e IVA 13 %. El espacio nace en BOB, no en USD «para convertir después». Hormigón, revoque, cielo falso, zócalo, plomero, fierro.",
        ),
    ],
    ("BO", "apu"): [
        (
            "APU en BOB, con NIT e IVA 13 %",
            "Descompuestos editables en bolivianos con referencias de Bolivia: cemento Bs 54/bolsa 50kg, arena Bs 150/m3, piedra Bs 160/m3, bloque Bs 2.5, hormigón Bs 600/m3. El IVA 13 % lo pones tú.",
        ),
    ],
    ("BO", "remodelacion"): [
        (
            "Reforma en Santa Cruz o La Paz, PDF por WhatsApp",
            "Pack de estancia, revoque y cielo falso, productos con foto. Si hay cambios, reenvías total anterior y total nuevo. El cliente no se registra.",
        ),
    ],
    ("CR", "software-presupuestos"): [
        (
            "Software de presupuestos en colones para Costa Rica",
            "Costa Rica ya cotiza en CRC, con NITE e IVA 13 %. El espacio nace en CRC, no en USD «para convertir después». Concreto, repello, cielo raso, rodapié, fontanero, formaleta.",
        ),
    ],
    ("CR", "apu"): [
        (
            "APU en CRC, con NITE e IVA 13 %",
            "Descompuestos editables en colones con referencias de Costa Rica: cemento ₡6.750/saco 50kg, arena ₡27.470/m3, piedra ₡28.000/m3, bloque ₡650, concreto ₡55.000/m3. El IVA 13 % lo pones tú.",
        ),
    ],
    ("CR", "remodelacion"): [
        (
            "Reforma en San José o Alajuela, PDF por WhatsApp",
            "Pack de estancia, repello y cielo raso, productos con foto. Si hay cambios, reenvías total anterior y total nuevo. El cliente no se registra.",
        ),
    ],
    ("GT", "software-presupuestos"): [
        (
            "Software de presupuestos en quetzales para Guatemala",
            "Guatemala ya cotiza en GTQ, con NIT e IVA 12 %. El espacio nace en GTQ, no en USD «para convertir después». Concreto, repello, cielo falso, zócalo, fontanero, block, flipón.",
        ),
    ],
    ("GT", "apu"): [
        (
            "APU en GTQ, con NIT e IVA 12 %",
            "Descompuestos editables en quetzales con referencias de Guatemala: cemento Q80.25/saco 42.5kg, block Q5.5, arena Q180/m3, piedrín Q230/m3, concreto Q900/m3. El IVA 12 % lo pones tú. No emite factura FEL.",
        ),
    ],
    ("GT", "remodelacion"): [
        (
            "Reforma en Ciudad de Guatemala o Quetzaltenango, PDF por WhatsApp",
            "Pack de estancia, repello y cielo falso, productos con foto. Si hay cambios, reenvías total anterior y total nuevo. El cliente no se registra.",
        ),
    ],
    ("HN", "software-presupuestos"): [
        (
            "Software de presupuestos en lempiras para Honduras",
            "Honduras ya cotiza en HNL, con RTN e ISV 15 %. El espacio nace en HNL, no en USD «para convertir después». Concreto, repello, cielo falso, zócalo, fontanero.",
        ),
    ],
    ("HN", "apu"): [
        (
            "APU en HNL, con RTN e ISV 15 %",
            "Descompuestos editables en lempiras con referencias de Honduras: cemento L215/saco 42.5kg, bloque L28, arena L500/m3, piedra L550/m3, concreto L4.500/m3. El ISV 15 % lo pones tú.",
        ),
    ],
    ("HN", "remodelacion"): [
        (
            "Reforma en Tegucigalpa o San Pedro Sula, PDF por WhatsApp",
            "Pack de estancia, repello y cielo falso, productos con foto. Si hay cambios, reenvías total anterior y total nuevo. El cliente no se registra.",
        ),
    ],
    ("NI", "software-presupuestos"): [
        (
            "Software de presupuestos en córdobas para Nicaragua",
            "Nicaragua ya cotiza en NIO, con RUC e IVA 15 %. El espacio nace en NIO, no en USD «para convertir después». Concreto, repello, cielo raso, zócalo, fontanero.",
        ),
    ],
    ("NI", "apu"): [
        (
            "APU en NIO, con RUC e IVA 15 %",
            "Descompuestos editables en córdobas con referencias de Nicaragua: cemento C$522.57/saco 42.5kg SINSA, bloque C$32, arena C$600/m3, piedra C$650/m3, concreto C$5.000/m3. El IVA 15 % lo pones tú.",
        ),
    ],
    ("NI", "remodelacion"): [
        (
            "Reforma en Managua o León, PDF por WhatsApp",
            "Pack de estancia, repello y cielo raso, productos con foto. Si hay cambios, reenvías total anterior y total nuevo. El cliente no se registra.",
        ),
    ],
    ("ES", "software-presupuestos"): [
        (
            "Presupuestar reformas en euros, con NIF e IVA",
            "El oficio español presupuesta en euros. CotizaT nace con EUR, IVA 21 % y NIF, y congela la tasa en cada documento si también trabajas en USD. Hormigón, pladur, falso techo, alicatado, fontanero.",
        ),
    ],
    ("ES", "apu"): [
        (
            "APU en euros, con precios de mercado españoles",
            "Descompuestos editables en EUR: materiales, mano de obra y equipo con referencias de mercado en euros. El IVA del documento lo configuras tú; no es asesoramiento fiscal.",
        ),
    ],
    ("ES", "remodelacion"): [
        (
            "Reforma de piso en Madrid o Valencia, PDF por WhatsApp",
            "Pack de baño o cocina, cantidades a los m², productos con foto. Si el cliente cambia el solado, reenvías total anterior y total nuevo. El cliente no se registra.",
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
    ("PA", "software-presupuestos"): [
        {
            "q": "¿Nace en dólares o convierte desde otra moneda?",
            "a": "Nace en USD. Panamá cotiza en dólares (PAB paridad 1:1); no hay conversión improvisada al registrarte.",
        },
    ],
    ("PA", "apu"): [
        {
            "q": "¿Los precios del APU son de mercado panameño?",
            "a": "Sí: cemento $8.25/saco, bloque $0.95, arena $34/m3, concreto 210 $125/m3 con fuentes de Panamá, más 382 referencias derivadas de canasta nacional en USD.",
        },
    ],
    ("SV", "software-presupuestos"): [
        {
            "q": "¿Nace en dólares o convierte desde otra moneda?",
            "a": "Nace en USD. El Salvador cotiza en dólares desde 2001; no hay conversión improvisada al registrarte.",
        },
    ],
    ("SV", "apu"): [
        {
            "q": "¿Los precios del APU son de mercado salvadoreño?",
            "a": "Sí: cemento $8.73/saco CASALCO, bloque $0.40, arena $35/m3, grava $45.05/m3, concreto $135.35/m3 con fuentes de El Salvador, más referencias derivadas de canasta nacional en USD.",
        },
    ],
    ("CL", "software-presupuestos"): [
        {
            "q": "¿Nace en pesos chilenos o convierte desde dólares?",
            "a": "Nace en CLP. Chile cotiza en pesos chilenos; no hay conversión improvisada al registrarte. Tasa verificada 925.90 CLP/USD.",
        },
    ],
    ("CL", "apu"): [
        {
            "q": "¿Los precios del APU son de mercado chileno?",
            "a": "Sí: cemento $4.790/saco 25kg Sodimac, bloque $1.840, arena $33.190/m3, hormigón H25 $110.000/m3 con fuentes de Chile, más referencias derivadas de canasta nacional en CLP.",
        },
    ],
    ("AR", "software-presupuestos"): [
        {
            "q": "¿Nace en pesos argentinos o convierte desde dólares?",
            "a": "Nace en ARS. Argentina cotiza en pesos argentinos; no hay conversión improvisada al registrarte. Tasa verificada 1497.38 ARS/USD.",
        },
    ],
    ("AR", "apu"): [
        {
            "q": "¿Los precios del APU son de mercado argentino?",
            "a": "Sí: cemento $11.433/bolsa 50kg Loma Negra/Holcim, bloque $1.500, arena $33.500/m3, hormigón H21 $168.478/m3 con fuentes de Argentina, más referencias derivadas de canasta nacional en ARS.",
        },
    ],
    ("DO", "software-presupuestos"): [
        {
            "q": "¿Nace en pesos dominicanos o convierte desde dólares?",
            "a": "Nace en DOP. RD cotiza en pesos dominicanos; no hay conversión improvisada al registrarte. Tasa verificada 58.33 DOP/USD.",
        },
    ],
    ("DO", "apu"): [
        {
            "q": "¿Los precios del APU son de mercado dominicano?",
            "a": "Sí: cemento RD$535/funda 94lb, block RD$42, arena RD$1.550/m3, grava RD$1.700/m3 con fuentes de RD, más referencias derivadas de canasta nacional en DOP.",
        },
    ],
    ("UY", "software-presupuestos"): [
        {
            "q": "¿Nace en pesos uruguayos o convierte desde dólares?",
            "a": "Nace en UYU. Uruguay cotiza en pesos uruguayos; no hay conversión improvisada al registrarte. Tasa verificada 40.21 UYU/USD.",
        },
    ],
    ("UY", "apu"): [
        {
            "q": "¿Los precios del APU son de mercado uruguayo?",
            "a": "Sí: cemento $240/bolsa 25kg, bloque $70, arena $1.200/m3, hormigón $5.500/m3 con fuentes de Uruguay, más referencias derivadas de canasta nacional en UYU.",
        },
    ],
    ("PY", "software-presupuestos"): [
        {
            "q": "¿Nace en guaraníes o convierte desde dólares?",
            "a": "Nace en PYG sin decimales. Paraguay cotiza en guaraníes; no hay conversión improvisada al registrarte. Tasa verificada 5946.10 PYG/USD.",
        },
    ],
    ("PY", "apu"): [
        {
            "q": "¿Los precios del APU son de mercado paraguayo?",
            "a": "Sí: cemento Gs 59.000/bolsa 50kg, bloque Gs 5.300, piedra Gs 104.000/m3, hormigón Gs 650.000/m3 con fuentes de Paraguay, más referencias derivadas de canasta nacional en PYG sin decimales.",
        },
    ],
    ("BO", "software-presupuestos"): [
        {
            "q": "¿Nace en bolivianos o convierte desde dólares?",
            "a": "Nace en BOB. Bolivia cotiza en bolivianos; no hay conversión improvisada al registrarte. Tasa verificada 11.55 BOB/USD.",
        },
    ],
    ("BO", "apu"): [
        {
            "q": "¿Los precios del APU son de mercado boliviano?",
            "a": "Sí: cemento Bs 54/bolsa 50kg, arena Bs 150/m3, piedra Bs 160/m3, bloque Bs 2.5, hormigón Bs 600/m3 con fuentes de Bolivia, más referencias derivadas de canasta nacional en BOB.",
        },
    ],
    ("CR", "software-presupuestos"): [
        {
            "q": "¿Nace en colones o convierte desde dólares?",
            "a": "Nace en CRC. Costa Rica cotiza en colones; no hay conversión improvisada al registrarte. Tasa verificada 449.39 CRC/USD.",
        },
    ],
    ("CR", "apu"): [
        {
            "q": "¿Los precios del APU son de mercado costarricense?",
            "a": "Sí: cemento ₡6.750/saco 50kg, arena ₡27.470/m3, piedra ₡28.000/m3, bloque ₡650, concreto ₡55.000/m3 con fuentes de Costa Rica, más referencias derivadas de canasta nacional en CRC.",
        },
    ],
    ("GT", "software-presupuestos"): [
        {
            "q": "¿Nace en quetzales o convierte desde dólares?",
            "a": "Nace en GTQ. Guatemala cotiza en quetzales; no hay conversión improvisada al registrarte. Tasa verificada 7.62 GTQ/USD.",
        },
    ],
    ("GT", "apu"): [
        {
            "q": "¿Los precios del APU son de mercado guatemalteco?",
            "a": "Sí: cemento Q80.25/saco 42.5kg, block Q5.5, arena Q180/m3, piedrín Q230/m3, concreto Q900/m3 con fuentes de Guatemala, más referencias derivadas de canasta nacional en GTQ.",
        },
    ],
    ("HN", "software-presupuestos"): [
        {
            "q": "¿Nace en lempiras o convierte desde dólares?",
            "a": "Nace en HNL. Honduras cotiza en lempiras; no hay conversión improvisada al registrarte. Tasa verificada 26.82 HNL/USD.",
        },
    ],
    ("HN", "apu"): [
        {
            "q": "¿Los precios del APU son de mercado hondureño?",
            "a": "Sí: cemento L215/saco 42.5kg, bloque L28, arena L500/m3, piedra L550/m3, concreto L4.500/m3 con fuentes de Honduras, más referencias derivadas de canasta nacional en HNL.",
        },
    ],
    ("NI", "software-presupuestos"): [
        {
            "q": "¿Nace en córdobas o convierte desde dólares?",
            "a": "Nace en NIO. Nicaragua cotiza en córdobas; no hay conversión improvisada al registrarte. Tasa verificada 36.70 NIO/USD.",
        },
    ],
    ("NI", "apu"): [
        {
            "q": "¿Los precios del APU son de mercado nicaragüense?",
            "a": "Sí: cemento C$522.57/saco 42.5kg SINSA, bloque C$32, arena C$600/m3, piedra C$650/m3, concreto C$5.000/m3 con fuentes de Nicaragua, más referencias derivadas de canasta nacional en NIO.",
        },
    ],
    ("ES", "software-presupuestos"): [
        {
            "q": "¿Emite factura con SII o TicketBAI?",
            "a": "No. Genera presupuestos comerciales con NIF e IVA; la factura la emites con tu sistema o tu gestor.",
        },
    ],
    ("ES", "apu"): [
        {
            "q": "¿Los precios del APU son de mercado español?",
            "a": "Sí: los recursos traen referencias nacionales en EUR (con rango, fuente y fecha), editables. No son una cotización exacta de tienda.",
        },
    ],
    ("ES", "remodelacion"): [
        {
            "q": "¿Sirve para una reforma de piso o solo para obra nueva?",
            "a": "Está pensado para reformas y obra privada: packs de estancia, alicatado, falso techo y fontanería, con PDF por WhatsApp.",
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
