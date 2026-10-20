"""Contenido SEO profundo del mercado español.

España no comparte estos artículos con el hub hispano: las búsquedas, el
vocabulario, la moneda, las fuentes de precios y el formato BC3 son propios
del mercado. Las cifras de mano de obra se leen de la matriz nacional para
que una actualización del catálogo no deje una tabla SEO antigua.
"""
from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path
from typing import Any

_PAIS_PATH = "/es/"
_CSV_PRECIOS = (
    Path(__file__).resolve().parents[1]
    / "basedatos_partidas"
    / "salida"
    / "precios_recursos_espana.csv"
)


@lru_cache(maxsize=1)
def _precios_espana() -> dict[str, dict[str, str]]:
    """Matriz ES por código; vacío si el artefacto no está en el despliegue."""
    try:
        with _CSV_PRECIOS.open(encoding="utf-8-sig", newline="") as archivo:
            return {
                fila["codigo_recurso"]: fila
                for fila in csv.DictReader(archivo, delimiter=";")
                if fila.get("codigo_recurso")
            }
    except (OSError, csv.Error, KeyError):
        return {}


def _euros(valor: str | float | int) -> str:
    numero = float(valor)
    if numero.is_integer():
        return f"{int(numero)} €"
    return f"{numero:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def _tabla_mano_obra() -> dict[str, Any]:
    """Tabla publicada desde la misma matriz de 388 recursos que usa el producto."""
    precios = _precios_espana()
    oficios = (
        ("MO-OF1-ALB", "Oficial de 1.ª albañil"),
        ("MO-AYU", "Peón o ayudante"),
        ("MO-OF1-PIN", "Oficial pintor"),
        ("MO-OF1-PLO", "Oficial fontanero"),
        ("MO-OF1-ELE", "Oficial electricista"),
        ("MO-OF1-CARPM", "Oficial carpintero de madera"),
    )
    respaldo = {
        "MO-OF1-ALB": (21, 18, 25),
        "MO-AYU": (15, 12, 18),
        "MO-OF1-PIN": (20, 16, 24),
        "MO-OF1-PLO": (23, 19, 27),
        "MO-OF1-ELE": (24, 20, 28),
        "MO-OF1-CARPM": (21, 18, 25),
    }
    filas: list[list[str]] = []
    for codigo, nombre in oficios:
        fila = precios.get(codigo) or {}
        central, minimo, maximo = respaldo[codigo]
        filas.append(
            [
                nombre,
                f"{_euros(fila.get('precio_referencia', central))}/h",
                f"{_euros(fila.get('precio_min', minimo))}–{_euros(fila.get('precio_max', maximo))}/h",
            ]
        )
    return {
        "cabecera": ["Oficio", "Coste empresa de referencia", "Rango nacional"],
        "filas": filas,
        "nota": (
            "Referencia CotizaT de agosto de 2026, sin IVA y antes del margen comercial. "
            "Es coste empresa por hora facturable, no la tarifa final que se cobra al cliente."
        ),
    }


def _tabla_plantilla() -> dict[str, Any]:
    return {
        "cabecera": ["Bloque", "Qué debe contener", "Qué evita"],
        "filas": [
            ["Cabecera", "Empresa, NIF, cliente, obra, número, fecha y validez", "Documentos sin identificar"],
            ["Alcance", "Capítulos, partidas, unidades, cantidades y precio", "Discutir qué estaba incluido"],
            ["Opciones", "Incluido, opcional o alternativa, con producto definido", "Sumar extras por error"],
            ["Resumen", "Base, descuento, impuesto y total", "Totales opacos"],
            ["Condiciones", "Forma de pago, plazo, exclusiones y vigencia", "Acuerdos solo por WhatsApp"],
            ["Versionado", "Número de versión y cambios frente al envío anterior", "Aprobar el PDF equivocado"],
        ],
        "nota": "Un presupuesto comercial no sustituye una factura ni, por sí solo, un contrato de obra.",
    }


ARTICULOS: dict[str, dict[str, Any]] = {
    "plantilla-presupuesto-reforma-espana": {
        "slug": "plantilla-presupuesto-reforma-espana",
        "pais": "ES",
        "pais_nombre": "España",
        "pais_path": _PAIS_PATH,
        "kicker": "España · Presupuesto de reforma",
        "title": "CotizaT: plantilla de presupuesto de reforma en España",
        "h1": "Plantilla de presupuesto de reforma: qué debe llevar en España",
        "description": (
            "Estructura completa de un presupuesto de reforma en España: capítulos, "
            "partidas, mediciones, IVA, condiciones, opciones y control de versiones."
        ),
        "lead": (
            "Una plantilla útil no es una tabla con cantidad y precio. Tiene que dejar "
            "claro quién presupuesta, qué obra se hará, qué queda fuera, cómo se mide, "
            "cuánto dura la oferta y qué versión ha aceptado el cliente. Esta es la "
            "estructura que necesita una empresa de reformas en España antes de enviar "
            "el PDF por correo o WhatsApp."
        ),
        "schema_howto": True,
        "secciones": [
            (
                "1. La cabecera identifica empresa, cliente y obra",
                [
                    "Empieza por la razón social o el nombre profesional, NIF, dirección y datos de contacto. Añade los datos del cliente y la dirección exacta de la obra: una misma persona puede pedir una reforma para una vivienda distinta de su domicilio. El documento necesita además número, fecha de emisión y plazo de validez. Esa combinación permite encontrarlo meses después y evita que una captura parcial circule sin contexto.",
                    "El número del presupuesto debe ser estable y la revisión debe tener su propia versión. Cambiar el total de PRES-024 y sobrescribir el PDF anterior elimina la prueba de qué se ofreció primero. Es mejor conservar PRES-024, versión 1 y versión 2, con fecha y un resumen de cambios.",
                    {"tabla": _tabla_plantilla()},
                ],
            ),
            (
                "2. Divide el alcance en capítulos que el cliente reconozca",
                [
                    "Una reforma integral se entiende mejor por capítulos: trabajos previos y demolición, albañilería, fontanería, electricidad, revestimientos, pintura, carpintería y gestión de residuos. Dentro van las partidas. «Reforma de baño» como una sola línea no dice si incluye impermeabilización, retirada de escombro, cambio de llaves, falso techo o mecanismos eléctricos.",
                    "El capítulo ordena la conversación comercial y también el coste. Si el cliente pide aplazar la carpintería, puedes separar ese bloque sin rehacer la reforma completa. Para la empresa, el mismo orden permite comparar el peso de materiales, mano de obra y equipo y detectar dónde se está perdiendo margen.",
                ],
            ),
            (
                "3. Cada partida necesita unidad, medición y descripción",
                [
                    "La partida debe responder tres preguntas: qué se ejecuta, cuánto se ejecuta y en qué unidad se paga. Un alicatado puede medirse en m²; una puerta, por unidad; una rozadura, en metros. La descripción debe fijar preparación, suministro, colocación y retirada si forman parte del precio. Una cifra sin alcance es solo una invitación a discutir después.",
                    "La cantidad puede salir de una medición por estancias o de un plano. Conviene guardar la medición que la justifica: largo por alto de cada pared, superficie de suelo o número de mecanismos. Así, cuando cambian 18 m² por 21 m², se corrige la cantidad y no se inventa un incremento redondo.",
                ],
            ),
            (
                "4. Separa coste interno, margen y precio que ve el cliente",
                [
                    "El análisis de precios unitarios descompone cada partida en materiales, horas de mano de obra y equipo. Esa información sirve para calcular el coste, las horas y el beneficio, pero no tiene por qué aparecer en el PDF comercial. El cliente necesita alcance, cantidad, precio unitario e importe; la empresa necesita saber si ese importe deja margen.",
                    "Aplicar un porcentaje a una tarifa que ya incluía beneficio produce margen sobre margen. En mano de obra española conviene partir de coste empresa por hora facturable —salario, Seguridad Social y costes asociados— y aplicar después el margen comercial decidido por la empresa. Los materiales deben aclarar si la referencia incluye transporte e IVA.",
                ],
            ),
            (
                "5. Incluido, opcional y alternativa no significan lo mismo",
                [
                    "Una mampara incluida suma al total. Un mueble opcional se muestra, pero no suma hasta que el cliente lo elige. Dos porcelánicos alternativos no pueden sumarse a la vez. Marcar cada caso evita el presupuesto inflado que parece caro porque contiene tres opciones como si fueran simultáneas.",
                    "Cuando un producto concreto condiciona el precio, añade marca, modelo, medida o una asignación máxima. «Grifería: 250 € de suministro» es más controlable que «grifería incluida». Si el cliente elige una pieza de 430 €, la diferencia se convierte en un cambio visible, no en una pérdida silenciosa.",
                ],
            ),
            (
                "6. Impuesto, descuentos y total deben poder auditarse",
                [
                    "El resumen tiene que mostrar base, descuento si existe, tipo impositivo configurado y total. En España el tipo general es 21 %, pero determinadas obras en vivienda pueden cumplir condiciones para un tipo reducido. La herramienta debe dejar elegir el tipo que corresponde al caso; no decidirlo por el profesional. El presupuesto no sustituye asesoramiento fiscal ni la factura.",
                    "Evita escribir un total manual que no se pueda reconstruir. Si cambia una partida, la base y el impuesto deben recalcularse. Un redondeo final puede ser válido, pero debe quedar identificado como ajuste o descuento y no oculto en una línea cualquiera.",
                ],
            ),
            (
                "7. Condiciones: vigencia, pagos, plazo y exclusiones",
                [
                    "Indica cuánto tiempo se mantiene el precio, qué anticipo se propone, qué hitos generan pagos y cuándo comienza el plazo. Distingue días de trabajo de una fecha cerrada si la obra depende de permisos, disponibilidad de materiales o trabajos de terceros. Especifica también si licencias, tasas, proyecto técnico, contenedores o suministros provisionales están incluidos.",
                    "Las exclusiones no deben ser una letra pequeña defensiva. Son parte del alcance: trabajos en elementos ocultos, reparación de patologías no visibles, retirada de amianto o muebles fuera de la zona de obra requieren valoración aparte. Decirlo antes protege a ambas partes.",
                ],
            ),
            (
                "8. Envía un PDF, pero conserva la versión editable",
                [
                    "El PDF es la copia que el cliente puede abrir y reenviar sin tener Excel. La fuente editable debe permanecer en un sistema que conserve catálogo, precios, mediciones y versiones. Si el cliente cambia el pavimento, crea una revisión y acompáñala con total anterior, total nuevo, partidas añadidas y retiradas.",
                    "CotizaT aplica este flujo con catálogo español en euros, NIF, IVA configurable, capítulos, APU, opciones de producto y PDF con logo. No emite la factura fiscal: convierte la información técnica y comercial de la reforma en un presupuesto trazable.",
                ],
            ),
        ],
        "faq": [
            {
                "q": "¿Una plantilla de presupuesto de reforma sirve como factura?",
                "a": "No. El presupuesto es una oferta comercial. La factura se emite con el sistema fiscal o la gestoría que corresponda y con sus requisitos propios.",
            },
            {
                "q": "¿Hay que mostrar el coste y el margen al cliente?",
                "a": "No. Es información interna. El PDF puede mostrar partida, unidad, cantidad, precio e importe sin revelar el coste de recursos ni el beneficio.",
            },
            {
                "q": "¿Debo aplicar siempre IVA 21 % a una reforma?",
                "a": "El 21 % es el tipo general; algunas obras en vivienda pueden cumplir requisitos para un tipo reducido. El profesional debe confirmar el tipo aplicable y configurarlo para cada documento.",
            },
            {
                "q": "¿Cómo se presentan dos acabados para que el cliente elija?",
                "a": "Como alternativas, no como dos partidas incluidas. Solo la alternativa elegida debe sumar al total; un producto opcional tampoco suma hasta ser aceptado.",
            },
        ],
        "related": [
            ("Software de presupuestos de reformas en España", "/es/software-presupuestos"),
            ("Presupuestos de remodelación en España", "/es/remodelacion"),
            ("Precio por hora de la mano de obra en España", "/es/guia/precio-hora-mano-obra-construccion-espana"),
            ("Cómo hacer un presupuesto de obra", "/guia/presupuesto-de-obra"),
        ],
    },
    "precio-hora-mano-obra-construccion-espana": {
        "slug": "precio-hora-mano-obra-construccion-espana",
        "pais": "ES",
        "pais_nombre": "España",
        "pais_path": _PAIS_PATH,
        "kicker": "España · Mano de obra 2026",
        "title": "CotizaT: precio hora de mano de obra en España (2026)",
        "h1": "Precio por hora de la mano de obra de construcción en España (2026)",
        "description": (
            "Coste empresa por hora de albañil, peón, pintor, fontanero y electricista "
            "en España en 2026, con rangos y método para convertirlo en precio de venta."
        ),
        "lead": (
            "El precio de una hora puede significar salario, coste para la empresa o "
            "tarifa facturada al cliente. Mezclarlos duplica el margen o deja una obra "
            "sin beneficio. Esta tabla usa coste empresa por hora facturable, que es la "
            "base correcta para construir un APU y aplicar después gastos y margen."
        ),
        "schema_howto": False,
        "secciones": [
            (
                "Referencias nacionales de coste empresa por hora",
                [
                    "CotizaT mantiene 388 recursos españoles en EUR. Para la mano de obra se contrastaron el Convenio General del Sector de la Construcción 2024–2026, tablas provinciales, salario bruto, cotizaciones empresariales y horas realmente facturables. El valor central no es lo que cobra un autónomo al cliente: es lo que cuesta disponer de esa hora productiva antes del beneficio.",
                    {"tabla": _tabla_mano_obra()},
                    "Los rangos no son un error. Madrid, Barcelona, Baleares, País Vasco y Navarra pueden situarse en la zona alta; zonas con menor coste o contratos estables pueden acercarse a la baja. La referencia nacional es un punto de partida editable, no una tarifa obligatoria ni una cotización de proveedor.",
                ],
            ),
            (
                "Salario, coste empresa y tarifa de venta son tres cifras",
                [
                    "El salario bruto remunera al trabajador. El coste empresa añade Seguridad Social, pagas, vacaciones, bajas, prevención, EPI, herramientas, gestoría y tiempo que se paga pero no se factura. La tarifa de venta añade estructura, riesgo y beneficio. Una búsqueda de «precio albañil hora» puede devolver cualquiera de las tres sin explicarlo.",
                    "Por eso 21 €/h para un oficial de primera no significa que el cliente deba recibir una línea a 21 €/h. Es el coste directo de referencia. Si la empresa carga gastos generales y beneficio con un factor comercial, la tarifa resultante será superior. Guardar directamente 32 €/h como coste y volver a aplicar margen sería cobrar beneficio dos veces y distorsionaría cada partida.",
                ],
            ),
            (
                "Cómo pasar del coste por hora al APU de una partida",
                [
                    "Una partida no suele consumir una hora completa por unidad. Si ejecutar un m² necesita 0,54 h de oficial y 0,30 h de peón, la mano de obra directa se calcula multiplicando cada rendimiento por su coste horario. Después se suman materiales, equipo y costes directos complementarios. El resultado es el coste directo por m².",
                    "La productividad manda tanto como la tarifa. Dos cuadrillas con el mismo coste horario pueden producir precios distintos si una coloca más metros al día. Copiar una tarifa sin revisar el rendimiento no localiza un APU; solo cambia una celda. Conviene medir rendimientos propios y mantener la referencia nacional como control.",
                ],
            ),
            (
                "Ejemplo: oficial y ayudante en una unidad de reforma",
                [
                    "Con referencias centrales de 21 €/h para oficial y 15 €/h para ayudante, 0,54 h de oficial aportan 11,34 € y 0,30 h de ayudante aportan 4,50 €. La mano de obra directa sería 15,84 € por unidad antes de materiales, equipo, complementarios y margen. Si el rendimiento real cambia, la partida cambia aunque el precio por hora siga igual.",
                    "Este desglose permite ver las horas totales del presupuesto. Cien unidades con esos rendimientos consumen 54 horas de oficial y 30 de ayudante. Esa información sirve para planificar la cuadrilla; no hace falta imprimirla en el PDF del cliente.",
                ],
            ),
            (
                "Qué debe incluir un coste empresa razonable",
                [
                    "Como mínimo: salario bruto anual, cotizaciones a cargo de la empresa, vacaciones y festivos, prevención y seguros, EPI y herramienta menor. Para obtener coste por hora facturable se divide entre horas productivas, no entre todas las horas teóricas del calendario. Desplazamientos, espera, compras y preparación reducen las horas que realmente se pueden vender.",
                    "Los costes de oficina, vehículo general, captación comercial y administración pueden tratarse como gastos generales en lugar de cargarlos dentro de cada oficio. Lo importante es no olvidarlos ni contarlos dos veces. La estructura debe ser estable para poder comparar el margen de dos presupuestos.",
                ],
            ),
            (
                "IVA y margen no forman parte del coste horario de la tabla",
                [
                    "Los importes mostrados son antes de IVA y antes del margen comercial. El impuesto se calcula sobre el documento con el tipo que corresponda. El beneficio se aplica según la política de la empresa. Mezclar el IVA dentro del recurso de mano de obra impide que la base imponible del presupuesto se entienda y se audite.",
                    "Tampoco son tarifas mínimas, máximas ni recomendaciones salariales. Cada convenio provincial, categoría, contrato y especialidad puede cambiar el coste real. La empresa debe reemplazar la referencia por sus nóminas y sus horas productivas cuando dispone de esos datos.",
                ],
            ),
            (
                "Actualizar una vez y recalcular todas las partidas",
                [
                    "La ventaja de un catálogo conectado es que el recurso «Oficial de 1.ª albañil» se guarda una vez. Cuando su coste pasa de 21 a 22 €/h, todas las partidas en edición que lo usan pueden recalcularse con sus rendimientos. No hace falta localizar la misma tarifa en decenas de hojas de Excel.",
                    "Los presupuestos ya enviados deben permanecer congelados. Actualizar el catálogo no puede cambiar retroactivamente el PDF aceptado por un cliente. CotizaT separa la referencia nacional, el precio propio de la empresa y la versión concreta de cada presupuesto para conservar esa trazabilidad.",
                ],
            ),
            (
                "De la referencia nacional a tu precio real",
                [
                    "Empieza con el rango nacional, sustituye salario y cargas por los de tu empresa, calcula horas facturables prudentes y contrasta el resultado con trabajos cerrados. Si una partida consume siempre más horas que el APU, corrige el rendimiento. Si el coste está bien pero el margen desaparece, revisa gastos generales, desperdicio y precio de venta.",
                    "La utilidad de una referencia no está en prometer que un electricista cuesta exactamente 24 € en toda España. Está en evitar una conversión desde dólares, documentar el orden de magnitud y ofrecer una base coherente que el reformista puede hacer suya.",
                ],
            ),
        ],
        "faq": [
            {
                "q": "¿Cuánto cuesta una hora de oficial de primera en España en 2026?",
                "a": "Como coste empresa nacional de referencia, 21 €/h, con rango de 18 a 25 €/h. La tarifa final facturada al cliente será mayor porque incorpora estructura y beneficio.",
            },
            {
                "q": "¿La tabla incluye IVA?",
                "a": "No. Son costes de recurso antes de IVA y margen. El impuesto se aplica después en el presupuesto con el tipo que corresponda.",
            },
            {
                "q": "¿Por qué un electricista aparece más caro que un albañil?",
                "a": "La matriz refleja salarios, especialización y costes de mercado distintos: 24 €/h de referencia para electricista frente a 21 €/h para oficial albañil.",
            },
            {
                "q": "¿Puedo usar la cifra como tarifa para mi cliente?",
                "a": "No directamente. Primero calcula tu coste real, añade gastos generales, riesgo y beneficio, y comprueba el rendimiento de la partida. La tabla es una referencia de coste empresa.",
            },
        ],
        "related": [
            ("APU para reformas en España", "/es/apu"),
            ("Plantilla de presupuesto de reforma", "/es/guia/plantilla-presupuesto-reforma-espana"),
            ("Qué es un análisis de precios unitarios", "/guia/analisis-precios-unitarios"),
        ],
    },
    "bc3-presupuestos-reformas-espana": {
        "slug": "bc3-presupuestos-reformas-espana",
        "pais": "ES",
        "pais_nombre": "España",
        "pais_path": _PAIS_PATH,
        "kicker": "España · BC3 / FIEBDC",
        "title": "CotizaT: cómo usar BC3 en presupuestos de reformas",
        "h1": "BC3 en presupuestos de reformas: importar, revisar y volver a exportar",
        "description": (
            "Qué contiene un archivo BC3, cómo importar capítulos, partidas, "
            "descompuestos y mediciones, y qué revisar antes de exportar el presupuesto."
        ),
        "lead": (
            "BC3 no es una hoja de cálculo ni una base de precios concreta: es un "
            "formato de intercambio FIEBDC. Permite recibir un presupuesto técnico, "
            "conservar capítulos, partidas y descompuestos, localizarlo con los costes "
            "de la empresa y devolver una versión que otras herramientas puedan abrir."
        ),
        "schema_howto": True,
        "secciones": [
            (
                "1. Qué es BC3 y qué problema resuelve",
                [
                    "Un archivo BC3 representa conceptos de una obra y sus relaciones: capítulos, partidas, recursos, precios, rendimientos y mediciones. En España se usa para intercambiar presupuestos entre bases de precios y programas como CYPE, Presto y otras aplicaciones compatibles con FIEBDC. El formato evita reconstruir cientos de líneas copiando desde un PDF.",
                    "No garantiza que dos programas entiendan todas las extensiones privadas del mismo modo. El núcleo —conceptos, árbol, descompuestos y mediciones— es interoperable; certificaciones, pliegos, adjuntos o campos particulares pueden necesitar revisión. Por eso importar no debe ser un botón ciego: primero hay que previsualizar qué se ha detectado.",
                ],
            ),
            (
                "2. Comprueba que el archivo es un presupuesto, no una base completa",
                [
                    "Antes de cargarlo, revisa el tamaño y el alcance. Una base de precios regional completa puede contener decenas de miles de conceptos que no pertenecen a una obra. Para cotizar una reforma interesa el presupuesto o la selección de partidas del proyecto. Un fichero más pequeño se valida mejor y no llena el catálogo comercial de recursos que nunca se usarán.",
                    "CotizaT acepta un BC3 cada vez, hasta 8 MB, y exige registros válidos de versión, conceptos y descomposición. Lee ANSI o UTF-8 y tolera punto o coma decimal. Si faltan partidas importables o el fichero solo contiene capítulos vacíos, lo rechaza con un mensaje en lugar de crear un presupuesto sin contenido.",
                ],
            ),
            (
                "3. Previsualiza capítulos, partidas y avisos",
                [
                    "La vista previa debe mostrar cuántas partidas entrarán, en qué capítulos, qué códigos se repiten y si alguna fila carece de nombre o unidad. Los capítulos y subcapítulos conservan el orden de aparición. Las partidas reciben su código, unidad, texto, precio y descompuesto cuando existe.",
                    "Los avisos no significan siempre que el archivo esté mal. Dos capítulos pueden usar códigos parecidos o una partida puede llegar sin mediciones. Lo importante es decidir si se importa y completar después la cantidad, en vez de convertir silenciosamente un dato ausente en cero definitivo.",
                ],
            ),
            (
                "4. Localiza recursos y precios para España",
                [
                    "Un BC3 puede traer precios de otra fecha, otra provincia o incluso otra moneda. Importar la estructura no obliga a aceptar sus cifras. Contrasta materiales, mano de obra y maquinaria con los recursos propios de la empresa o con referencias nacionales en EUR. Conserva el rendimiento técnico y sustituye el precio solo cuando ambos conceptos representen lo mismo.",
                    "La terminología también importa. Para un presupuesto español conviene revisar que las partidas se presenten como hormigón, enfoscado, falso techo, alicatado y fontanería. El código técnico puede conservarse, pero el texto comercial debe ser comprensible para el cliente que recibe el PDF.",
                ],
            ),
            (
                "5. No confundas coste directo con precio de venta",
                [
                    "Muchas bases BC3 publican costes directos o precios de ejecución material, no el precio comercial final de una pequeña reforma. Comprueba qué incluye cada concepto: auxiliares, costes indirectos, desperdicio, transporte, beneficio e impuesto. Aplicar margen sobre una cifra que ya lo incorpora duplica componentes; no aplicarlo sobre un coste puro elimina el beneficio.",
                    "En CotizaT el descompuesto sirve como APU interno. Los recursos generan coste y horas; la empresa decide el precio de venta y el margen. El PDF del cliente puede mostrar solo capítulos y partidas, sin revelar la composición interna.",
                ],
            ),
            (
                "6. Revisa las mediciones antes de emitir el PDF",
                [
                    "El BC3 puede incluir líneas de medición con comentario, unidades y factores. Verifica que el total coincide con el plano y con el alcance real de la reforma. Una medición heredada de proyecto no sabe qué zonas ha excluido el cliente ni qué demolición apareció durante la visita.",
                    "Si no hay medición importable, añade cantidades por estancia o mide sobre el plano. Guarda el origen de la cantidad. Cuando el cliente reduce el alicatado, será posible explicar el cambio de m² y no solo presentar un total diferente.",
                ],
            ),
            (
                "7. Convierte el presupuesto técnico en una oferta comercial",
                [
                    "El archivo técnico organiza la obra; la oferta necesita además datos de empresa y cliente, NIF, dirección, validez, opciones, forma de pago, impuesto y condiciones. Añade productos alternativos o partidas opcionales sin sumarlos al total hasta que se elijan. Revisa el margen y las horas antes de generar el documento.",
                    "Este paso es la diferencia entre abrir un BC3 y vender una reforma. El cliente no tiene por qué instalar un programa compatible: recibe un PDF claro con el alcance que va a contratar. La fuente BC3 queda detrás como estructura editable y trazable.",
                ],
            ),
            (
                "8. Exporta FIEBDC-3 y conserva también el PDF",
                [
                    "CotizaT exporta el presupuesto a BC3 FIEBDC-3/2020 en ANSI con conceptos, árbol y mediciones. Es útil para devolver el trabajo a un técnico o abrirlo en otra herramienta compatible. Antes de enviarlo, comprueba códigos, capítulos y unidades; cada receptor puede aplicar validaciones distintas.",
                    "El BC3 no sustituye el PDF comercial y el PDF no sustituye el BC3. El primero mantiene estructura y datos reutilizables; el segundo fija lo que se ofreció al cliente en una versión legible. Conservar ambos, junto con la versión del presupuesto, evita depender de un único programa o de una captura de pantalla.",
                ],
            ),
        ],
        "faq": [
            {
                "q": "¿BC3 es un formato exclusivo de CYPE?",
                "a": "No. BC3 es un formato de intercambio FIEBDC utilizado por distintas bases de precios y programas. Cada aplicación puede añadir campos propios, pero el núcleo es interoperable.",
            },
            {
                "q": "¿CotizaT importa mediciones y descompuestos?",
                "a": "Sí. El importador procesa capítulos, partidas, relaciones de descomposición, recursos y líneas de medición presentes en el archivo válido.",
            },
            {
                "q": "¿Puedo importar una base de precios completa?",
                "a": "El flujo está pensado para un presupuesto de obra, no para una base masiva. Conviene exportar del programa de origen solo la obra o selección que se va a cotizar.",
            },
            {
                "q": "¿El BC3 exportado sustituye el presupuesto PDF?",
                "a": "No. El BC3 sirve para intercambio técnico; el PDF es el documento comercial legible que se envía al cliente. Lo recomendable es conservar los dos.",
            },
        ],
        "related": [
            ("Software de presupuestos en España", "/es/software-presupuestos"),
            ("Análisis de precios unitarios en España", "/es/apu"),
            ("Plantilla de presupuesto de reforma", "/es/guia/plantilla-presupuesto-reforma-espana"),
            ("Cómo importar Excel de CYPE", "/como-funciona"),
        ],
    },
}

ORDEN_ARTICULOS: tuple[str, ...] = (
    "plantilla-presupuesto-reforma-espana",
    "precio-hora-mano-obra-construccion-espana",
    "bc3-presupuestos-reformas-espana",
)


def articulo(slug: str) -> dict[str, Any] | None:
    return ARTICULOS.get(str(slug or "").strip())


def guias() -> list[dict[str, Any]]:
    return [ARTICULOS[slug] for slug in ORDEN_ARTICULOS]


def ruta_articulo(slug: str) -> str:
    return f"/es/guia/{str(slug or '').strip()}"
