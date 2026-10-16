"""Presupuesto de muestra comercial sin datos personales reales (E1-052).

Construye, sobre una base SQLite en memoria y con los mismos modelos y el
mismo motor de PDF de la aplicación, un presupuesto de remodelación
completo y creíble que sirve como «PDF de ejemplo» en la landing
(`/conocer`). Nada de lo que contiene corresponde a una persona, empresa,
dirección o documento real:

  · la empresa es ficticia (RIF de marcador ``J-00000000-0`` y dominio de
    ejemplo reservado ``ejemplo.com``);
  · el cliente es una familia genérica sin documento de identidad;
  · los importes y mediciones son verosímiles pero inventados.

La función :func:`construir` devuelve los bytes del PDF; el ejecutable de
línea de comandos (`tools/generar_presupuesto_muestra.py`) lo escribe en
`app/static/pdf/presupuesto-ejemplo.pdf`, que es el archivo que enlaza la
landing.
"""
from __future__ import annotations

import io
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from ..models import (
    Base,
    Capitulo,
    Cliente,
    Configuracion,
    Medicion,
    Presupuesto,
    PresupuestoItem,
)
from ..paises import resolver_mercado
from . import pdf as pdf_service
from .variante_ingles import aplicar_variante

# ── Identidad ficticia (sin datos personales reales) ─────────────────────
EMPRESA_NOMBRE = "Construcciones El Samán, C.A."
EMPRESA_RIF = "J-00000000-0"          # marcador, imposible de confundir
EMPRESA_EMAIL = "contacto@ejemplo.com"  # dominio de ejemplo reservado (RFC 2606)
EMPRESA_WEB = "www.ejemplo.com"
EMPRESA_TELEFONO = "+58 212 000 0000"
EMPRESA_DIRECCION = "Av. Principal, Centro Empresarial Muestra, Piso 1, Of. 10"
EMPRESA_CIUDAD = "Caracas"
EMPRESA_PAIS = "Venezuela"

CLIENTE_NOMBRE = "Familia Rodríguez"   # nombre genérico, sin documento real
CLIENTE_DIRECCION = "Residencia unifamiliar, Urbanización Los Álamos, Caracas"

NUMERO = "P-2026-001"
TITULO = "Remodelación integral de apartamento — 120 m²"
DIRECCION_OBRA = "Piso 7, Apartamento 7-B, Residencias Los Álamos, Caracas"
FECHA = date(2026, 8, 15)

NOTA_ILUSTRATIVA = (
    "Documento de muestra generado con CotizaT: la empresa, el cliente, la "
    "dirección de la obra y todos los importes son ficticios y no corresponden "
    "a ninguna persona ni empresa real."
)
NOTAS_EXTRA = (
    "\nIncluye mano de obra especializada, materiales de primera calidad y "
    "gestión integral del proyecto. No incluye enseres, decoración ni equipos "
    "de climatización."
)
CONDICIONES = (
    "Forma de pago: 40% de anticipo para inicio, 35% al 50% de avance "
    "certificado y 25% contra entrega.\n"
    "Plazo estimado de ejecución: 12 semanas desde la firma.\n"
    "Garantía de 12 meses en instalaciones y acabados (ver tabla de garantías)."
)

# ── Redacción en inglés ──────────────────────────────────────────────────
# El mismo presupuesto de muestra, con los mismos importes y las mismas
# mediciones, redactado en inglés para la landing `/en/`. La traducción se
# aplica al objeto ya construido (ver `_traducir`), así que la estructura
# —capítulos, partidas, unidades, cantidades y precios— tiene una única
# fuente y no puede desincronizarse entre idiomas.
#
# Los nombres propios (empresa, cliente, ciudades, códigos y unidades) no se
# traducen: están en `_SIN_CAMBIO`. Cualquier otra cadena que aparezca en el
# documento y no esté en `_TEXTO_EN` es un hueco, y la suite lo detecta.
_TEXTO_EN = {
    # ── Cabecera ──
    TITULO: "Full apartment refurbishment — 120 m²",
    DIRECCION_OBRA: "7th floor, Apartment 7-B, Los Álamos Residences, Caracas",
    EMPRESA_DIRECCION: (
        "Main Avenue, Muestra Business Centre, 1st floor, Office 10"
    ),
    CLIENTE_DIRECCION: (
        "Detached house, Los Álamos Residential Park, Caracas"
    ),
    NOTA_ILUSTRATIVA + NOTAS_EXTRA: (
        "Sample document generated with CotizaT: the company, the client, the "
        "site address and all amounts are fictitious and do not refer to any "
        "real person or company."
        "\nIncludes skilled labour, first-quality materials and full project "
        "management. Excludes furniture, soft furnishings and air-conditioning "
        "equipment."
    ),
    CONDICIONES: (
        "Payment terms: 40% deposit to start, 35% at 50% certified progress "
        "and 25% on handover.\n"
        "Estimated programme: 12 weeks from signature.\n"
        "12-month warranty on installations and finishes (see the warranty "
        "table)."
    ),

    # ── Capítulos ──
    "TRABAJOS PREVIOS Y DEMOLICIONES": "PRELIMINARIES AND DEMOLITION",
    "MUROS Y PARTICIONES": "WALLS AND PARTITIONS",
    "PISOS Y REVESTIMIENTOS": "FLOOR AND WALL TILING",
    "COCINA": "KITCHEN",
    "BAÑOS": "BATHROOMS",
    "INSTALACIONES (PLOMERÍA Y ELECTRICIDAD)":
        "SERVICES (PLUMBING AND ELECTRICAL)",
    "PINTURA Y ACABADOS": "PAINTING AND FINISHES",

    # ── 1 · Trabajos previos y demoliciones ──
    "Demolición de tabiquería interior": "Demolition of internal partitions",
    "Demolición de tabiques interiores de bloque de concreto de hasta 20 cm "
    "de espesor, con medios manuales y sin afectar a la estabilidad de los "
    "elementos estructurales contiguos. Incluye carga y retiro de escombros.":
        "Demolition of internal concrete block partitions up to 20 cm thick, "
        "by hand, without affecting the stability of the adjoining structural "
        "elements. Includes loading and removal of waste and debris.",
    "Demolición de revestimientos de pisos y paredes":
        "Removal of existing floor and wall finishes",
    "Levantado de pavimentos cerámicos y revestimientos de paredes existentes, "
    "con medios manuales, y retiro del material a vertedero autorizado.":
        "Lifting of existing ceramic floor and wall finishes by hand and "
        "removal of the material to a licensed tip.",
    "Protección de superficies y limpieza de obra":
        "Protection of surfaces and site cleaning",
    "Protección de áreas que permanecen, montaje de andamios ligeros y "
    "limpieza general de la obra, incluida la retirada de escombros.":
        "Protection of areas that remain in use, erection of light-duty "
        "scaffolding and general site cleaning, including removal of waste "
        "and debris.",

    # ── 2 · Muros y particiones ──
    "Hoja de partición de bloque de concreto de 15 cm":
        "Partition in 15 cm hollow concrete block",
    "Ejecución de tabiques interiores de bloque hueco de concreto vibrado de "
    "15 cm, recibidos con mortero de cemento, con replanteo, plomos y "
    "andamiaje ligero incluidos.":
        "Construction of internal partitions in 15 cm vibrated hollow "
        "concrete block laid in cement mortar, including setting out, "
        "plumbing and light-duty scaffolding.",
    "Pañete / repello de paredes": "Cement render to walls",
    "Repello en mortero de cemento sobre paramentos verticales de hasta 10 mm "
    "de espesor, reglado y sacado de rincones y aristas, medido a cinta "
    "corrida para su posterior pintura.":
        "Cement mortar render to vertical surfaces up to 10 mm thick, ruled "
        "and with angles and arrises formed, measured over the whole surface, "
        "ready for decoration.",
    "Reparación de grietas y nivelación de paramentos":
        "Crack repair and levelling of surfaces",
    "Saneado de grietas y fisuras, aplicación de mortero estructural y "
    "nivelación de paramentos existentes antes del acabado final.":
        "Cutting out and making good cracks and fissures, application of "
        "structural mortar and levelling of existing surfaces before the "
        "final finish.",

    # ── 3 · Pisos y revestimientos ──
    "Solado de porcelanato rectificado gran formato":
        "Large-format rectified porcelain floor tiling",
    "Suministro y colocación de porcelanato rectificado 90x90 cm recibido con "
    "adhesivo cementoso C2 TE y doble encolado, juntas de 2 mm con fragüe "
    "epóxico. Incluye nivelación del soporte y cortes a hilo de agua.":
        "Supply and laying of 90x90 cm rectified porcelain tiles bedded in "
        "C2 TE cementitious adhesive with back-buttering, 2 mm joints pointed "
        "with epoxy grout. Includes levelling of the substrate and wet "
        "cutting.",
    "Zócalo / rodapié de MDF lacado": "Lacquered MDF skirting",
    "Suministro y montaje de rodapié en MDF lacado blanco mate de 10 cm, "
    "fijado con adhesivo de montaje y sellado perimetral con silicona.":
        "Supply and fixing of 10 cm matt white lacquered MDF skirting, bonded "
        "with grab adhesive and perimeter-sealed with silicone.",
    "Revestimiento de paredes con porcelanato 60x120 cm":
        "Wall tiling in 60x120 cm porcelain",
    "Revestimiento interior con piezas de gran formato en capa fina y doble "
    "encolado con adhesivo C2 TE S1. Juntas de 3 mm con fragüe epóxico. No "
    "incluye piezas especiales.":
        "Internal wall tiling in large-format tiles, thin-bed with "
        "back-buttering in C2 TE S1 adhesive. 3 mm joints pointed with epoxy "
        "grout. Excludes special pieces.",

    # ── 4 · Cocina ──
    "Suministro e instalación de mobiliario de cocina":
        "Supply and installation of kitchen units",
    "Montaje de mobiliario de cocina (muebles bajos y altos) en melamina de "
    "alta presión, con herrajes de cierre suave. Incluye nivelación, fijación "
    "y ajuste de puertas y gavetas.":
        "Installation of kitchen units (base and wall units) in high-pressure "
        "melamine with soft-close ironmongery. Includes levelling, fixing and "
        "adjustment of doors and drawers.",
    "Encimera de cuarzo": "Quartz worktop",
    "Suministro e instalación de encimera de cuarzo con acabado pulido, "
    "perfil recto y sellado de uniones, con huecos para fregadero y cocina.":
        "Supply and installation of polished quartz worktop with square edge "
        "and sealed joints, cut out for sink and hob.",
    "Plomería de cocina": "Kitchen plumbing",
    "Instalación de puntos de agua fría y caliente en tubería PPR, con "
    "llaves de corte y desagües nuevos en PVC sanitario para fregadero y "
    "lavaplatos. Incluye material.":
        "Installation of hot and cold water services in PPR pipework, with "
        "isolating valves and new PVC sanitary waste for sink and dishwasher. "
        "Material included.",

    # ── 5 · Baños ──
    "Instalación de plato de ducha": "Shower tray installation",
    "Suministro y colocación de plato de ducha con desagüe, conexión a la "
    "red de evacuación, fijación y sellado con silicona. Totalmente "
    "instalado y probado.":
        "Supply and bedding of shower tray with waste, connection to the "
        "drainage system, fixing and silicone sealing. Fully installed and "
        "tested.",
    "Instalación de inodoro y lavamanos": "WC and washbasin installation",
    "Suministro e instalación de inodoro y lavamanos de porcelana, con "
    "grifería, conexionado, probado y en funcionamiento.":
        "Supply and installation of porcelain WC and washbasin with "
        "brassware, connections, tested and in working order.",
    "Mampara de vidrio templado": "Toughened glass shower screen",
    "Suministro e instalación de mampara de vidrio templado para ducha, con "
    "perfilería, fijación a paredes y sellado con silicona.":
        "Supply and installation of toughened glass shower screen with "
        "framing, fixing to walls and silicone sealing.",

    # ── 6 · Instalaciones ──
    "Instalación de plomería general": "General plumbing installation",
    "Sustitución de red de agua fría y caliente en tubería PPR, llaves de "
    "corte y desagües en PVC sanitario. Incluye pruebas de estanqueidad.":
        "Replacement of the hot and cold water distribution in PPR pipework, "
        "with isolating valves and PVC sanitary waste. Includes watertightness "
        "testing.",
    "Instalación eléctrica (puntos de luz y tomas)":
        "Electrical installation (lighting points and sockets)",
    "Instalación de circuitos, tablero con protecciones, cableado y "
    "mecanismos (interruptores y tomacorrientes) según plano. Incluye "
    "pruebas de funcionamiento.":
        "Installation of circuits, consumer unit with protective devices, "
        "cabling and accessories (switches and socket outlets) to the layout "
        "drawing. Includes functional testing.",
    "Suministro y montaje de luminarias LED":
        "Supply and installation of LED light fittings",
    "Suministro e instalación de luminarias LED empotradas y decorativas, "
    "con conexión, pruebas y certificación de funcionamiento.":
        "Supply and installation of recessed and decorative LED light "
        "fittings, with connection, testing and certification of operation.",

    # ── 7 · Pintura y acabados ──
    "Pintura de paramentos interiores": "Painting of internal walls",
    "Pintado de paramentos verticales con pintura plástica premium acabado "
    "mate, dos manos más imprimación previa, con reparación de "
    "desperfectos menores y lijado entre manos.":
        "Painting of vertical surfaces in premium matt emulsion, two coats "
        "over a priming coat, with making good of minor defects and rubbing "
        "down between coats.",
    "Pintura de techos": "Painting of ceilings",
    "Pintado de techos con pintura plástica premium acabado mate, dos manos "
    "más imprimación previa.":
        "Painting of ceilings in premium matt emulsion, two coats over a "
        "priming coat.",

    # ── Conceptos de medición ──
    "Sala – cocina": "Living room – kitchen",
    "Baño principal": "Main bathroom",
    "Baño de servicio": "Guest bathroom",
    "Pisos": "Floors",
    "Paredes de cocina y baños": "Kitchen and bathroom walls",
    "Tabique cocina": "Kitchen partition",
    "Tabique baño principal": "Main bathroom partition",
    "Tabique baño de servicio": "Guest bathroom partition",
    "Total": "Total",
    "Total + extra por cortes": "Total + extra for cutting",
    "Total + extras": "Total + extras",
    "Cocina (entre muebles)": "Kitchen (between units)",
    "Muebles bajos y altos": "Base and wall units",
    "Encimera": "Worktop",
    "Paredes": "Walls",
    "Techos": "Ceilings",

    # ── Productos asociados y unidades ──
    "Porcelanato rectificado 90x90 cm": "Rectified porcelain tile 90x90 cm",
    "Porcelanato 60x120 cm pulido": "Polished porcelain tile 60x120 cm",
    "Cuarzo Blanco Norte veta sutil": "Blanco Norte quartz, subtle veining",
    "Juego sanitario de porcelana": "Porcelain sanitaryware set",
    "ud": "ea",
    "ml": "m",
}

# Cadenas que NO se traducen: nombres propios, códigos, dominios y unidades
# que se escriben igual en los dos idiomas. Sirve de lista blanca auditora:
# todo lo que no esté aquí ni en `_TEXTO_EN` es un texto sin traducir.
_SIN_CAMBIO = frozenset({
    EMPRESA_NOMBRE, CLIENTE_NOMBRE, EMPRESA_RIF, EMPRESA_EMAIL, EMPRESA_WEB,
    EMPRESA_TELEFONO, EMPRESA_CIUDAD, EMPRESA_PAIS, NUMERO,
    "m", "m2", "USD", "enviado", "",
})

# Campos de cada modelo que contienen texto redactado y se traducen.
_CAMPOS_TEXTO = {
    "Presupuesto": ("titulo", "direccion_obra", "notas", "condiciones"),
    "Capitulo": ("nombre",),
    "PresupuestoItem": ("nombre", "descripcion", "unidad",
                        "producto_nombre", "producto_unidad"),
    "Medicion": ("concepto",),
    "Cliente": ("nombre", "direccion", "pais"),
    "Configuracion": ("empresa_nombre", "empresa_direccion", "empresa_ciudad",
                      "empresa_pais"),
}


def _traducir(*objetos, en: bool = True, mercado: dict | None = None) -> list[str]:
    """Pasa la muestra a inglés y devuelve los textos que no tenían traducción.

    Recorre el presupuesto ya construido (capítulos, partidas y mediciones) y
    sustituye cada texto redactado por su versión inglesa. Sobre esa versión
    aplica además el vocabulario del mercado, porque «skirting» vale para el
    Reino Unido y en Estados Unidos se dice «baseboard».

    Devuelve la lista de huecos —textos que no están ni en :data:`_TEXTO_EN`
    ni en :data:`_SIN_CAMBIO`— para que la suite detecte en cuanto se añada
    una partida nueva y se olvide traducirla.
    """
    huecos: list[str] = []
    if not en:
        return huecos
    vistos: set[int] = set()
    pila = list(objetos)
    while pila:
        obj = pila.pop()
        if obj is None or id(obj) in vistos:
            continue
        vistos.add(id(obj))
        campos = _CAMPOS_TEXTO.get(type(obj).__name__)
        if campos is None:
            continue
        for campo in campos:
            actual = getattr(obj, campo, None) or ""
            if not actual:
                continue
            if actual in _TEXTO_EN:
                traducido = _TEXTO_EN[actual]
                traducido = aplicar_variante(traducido, mercado)
                if traducido != actual:
                    setattr(obj, campo, traducido)
            elif actual not in _SIN_CAMBIO:
                huecos.append(f"{type(obj).__name__}.{campo}: {actual!r}")
        for relacion in ("capitulos", "partidas", "mediciones"):
            hijos = getattr(obj, relacion, None)
            if hijos is not None:
                pila.extend(hijos)
    return huecos


def _partida(nombre, descripcion, unidad, precio, mediciones=None, cantidad=0.0,
             orden=0, prod_nombre="", prod_precio=None, prod_unidad=""):
    p = PresupuestoItem(
        nombre=nombre,
        descripcion=descripcion,
        unidad=unidad,
        precio_unitario=precio,
        cantidad=cantidad,
        orden=orden,
        producto_nombre=prod_nombre,
        producto_precio=prod_precio,
        producto_unidad=prod_unidad,
    )
    for i, (concepto, cant) in enumerate(mediciones or []):
        p.mediciones.append(Medicion(concepto=concepto, cantidad=cant, orden=i))
    return p


def _configuracion() -> Configuracion:
    return Configuracion(
        empresa_nombre=EMPRESA_NOMBRE,
        empresa_rif=EMPRESA_RIF,
        empresa_pais=EMPRESA_PAIS,
        empresa_ciudad=EMPRESA_CIUDAD,
        empresa_direccion=EMPRESA_DIRECCION,
        empresa_telefono=EMPRESA_TELEFONO,
        empresa_email=EMPRESA_EMAIL,
        empresa_web=EMPRESA_WEB,
        pdf_color="#0F4C81",
    )


def _cliente() -> Cliente:
    return Cliente(
        nombre=CLIENTE_NOMBRE,
        rif="",
        pais="Venezuela",
        telefono="",
        email="",
        direccion=CLIENTE_DIRECCION,
        es_demo=True,
    )


def _presupuesto(cliente: Cliente) -> Presupuesto:
    p = Presupuesto(
        numero=NUMERO,
        year=FECHA.year,
        fecha=FECHA,
        titulo=TITULO,
        direccion_obra=DIRECCION_OBRA,
        codigo_postal="",
        validez_dias=30,
        moneda="USD",
        impuesto_pct=16.0,
        descuento_pct=0.0,
        estado="enviado",
        es_demo=True,
        client_id=cliente.id,
        mostrar_resumen_capitulos=True,
        mostrar_garantias=True,
        mostrar_firmas=True,
        # El ejemplo público enseña el desglose del precio (productos elegidos
        # frente a mano de obra y ejecución), la función que explica al cliente
        # en qué se va el importe final.
        mostrar_desglose_precio=True,
        notas=NOTA_ILUSTRATIVA + NOTAS_EXTRA,
        condiciones=CONDICIONES,
    )

    # 1 · Trabajos previos y demoliciones
    c1 = Capitulo(nombre="TRABAJOS PREVIOS Y DEMOLICIONES", orden=1)
    c1.partidas.append(_partida(
        "Demolición de tabiquería interior",
        "Demolición de tabiques interiores de bloque de concreto de hasta 20 cm "
        "de espesor, con medios manuales y sin afectar a la estabilidad de los "
        "elementos estructurales contiguos. Incluye carga y retiro de escombros.",
        "m2", 18.50,
        mediciones=[("Sala – cocina", 18.00), ("Baño principal", 7.50), ("Baño de servicio", 5.00)],
        orden=1,
    ))
    c1.partidas.append(_partida(
        "Demolición de revestimientos de pisos y paredes",
        "Levantado de pavimentos cerámicos y revestimientos de paredes existentes, "
        "con medios manuales, y retiro del material a vertedero autorizado.",
        "m2", 12.00,
        mediciones=[("Pisos", 96.00), ("Paredes de cocina y baños", 42.00)],
        orden=2,
    ))
    c1.partidas.append(_partida(
        "Protección de superficies y limpieza de obra",
        "Protección de áreas que permanecen, montaje de andamios ligeros y "
        "limpieza general de la obra, incluida la retirada de escombros.",
        "ud", 450.00, cantidad=1, orden=3,
    ))
    p.capitulos.append(c1)

    # 2 · Muros y particiones
    c2 = Capitulo(nombre="MUROS Y PARTICIONES", orden=2)
    c2.partidas.append(_partida(
        "Hoja de partición de bloque de concreto de 15 cm",
        "Ejecución de tabiques interiores de bloque hueco de concreto vibrado de "
        "15 cm, recibidos con mortero de cemento, con replanteo, plomos y "
        "andamiaje ligero incluidos.",
        "m2", 46.00,
        mediciones=[("Tabique cocina", 12.50), ("Tabique baño principal", 9.00), ("Tabique baño de servicio", 6.50)],
        orden=1,
    ))
    c2.partidas.append(_partida(
        "Pañete / repello de paredes",
        "Repello en mortero de cemento sobre paramentos verticales de hasta 10 mm "
        "de espesor, reglado y sacado de rincones y aristas, medido a cinta "
        "corrida para su posterior pintura.",
        "m2", 17.50, mediciones=[("Total", 84.00)], orden=2,
    ))
    c2.partidas.append(_partida(
        "Reparación de grietas y nivelación de paramentos",
        "Saneado de grietas y fisuras, aplicación de mortero estructural y "
        "nivelación de paramentos existentes antes del acabado final.",
        "m2", 9.50, mediciones=[("Total", 60.00)], orden=3,
    ))
    p.capitulos.append(c2)

    # 3 · Pisos y revestimientos
    c3 = Capitulo(nombre="PISOS Y REVESTIMIENTOS", orden=3)
    c3.partidas.append(_partida(
        "Solado de porcelanato rectificado gran formato",
        "Suministro y colocación de porcelanato rectificado 90x90 cm recibido con "
        "adhesivo cementoso C2 TE y doble encolado, juntas de 2 mm con fragüe "
        "epóxico. Incluye nivelación del soporte y cortes a hilo de agua.",
        "m2", 68.00,
        mediciones=[("Total + extra por cortes", 108.00)],
        orden=1,
        prod_nombre="Porcelanato rectificado 90x90 cm", prod_precio=26.50, prod_unidad="m2",
    ))
    c3.partidas.append(_partida(
        "Zócalo / rodapié de MDF lacado",
        "Suministro y montaje de rodapié en MDF lacado blanco mate de 10 cm, "
        "fijado con adhesivo de montaje y sellado perimetral con silicona.",
        "m", 9.80, mediciones=[("Total + extras", 88.00)], orden=2,
    ))
    c3.partidas.append(_partida(
        "Revestimiento de paredes con porcelanato 60x120 cm",
        "Revestimiento interior con piezas de gran formato en capa fina y doble "
        "encolado con adhesivo C2 TE S1. Juntas de 3 mm con fragüe epóxico. No "
        "incluye piezas especiales.",
        "m2", 58.00,
        mediciones=[("Cocina (entre muebles)", 12.00), ("Baño principal", 22.00), ("Baño de servicio", 16.00)],
        orden=3,
        prod_nombre="Porcelanato 60x120 cm pulido", prod_precio=24.00, prod_unidad="m2",
    ))
    p.capitulos.append(c3)

    # 4 · Cocina
    c4 = Capitulo(nombre="COCINA", orden=4)
    c4.partidas.append(_partida(
        "Suministro e instalación de mobiliario de cocina",
        "Montaje de mobiliario de cocina (muebles bajos y altos) en melamina de "
        "alta presión, con herrajes de cierre suave. Incluye nivelación, fijación "
        "y ajuste de puertas y gavetas.",
        "ml", 690.00, mediciones=[("Muebles bajos y altos", 6.80)], orden=1,
    ))
    c4.partidas.append(_partida(
        "Encimera de cuarzo",
        "Suministro e instalación de encimera de cuarzo con acabado pulido, "
        "perfil recto y sellado de uniones, con huecos para fregadero y cocina.",
        "ml", 460.00, mediciones=[("Encimera", 6.80)], orden=2,
        prod_nombre="Cuarzo Blanco Norte veta sutil", prod_precio=295.00, prod_unidad="ml",
    ))
    c4.partidas.append(_partida(
        "Plomería de cocina",
        "Instalación de puntos de agua fría y caliente en tubería PPR, con "
        "llaves de corte y desagües nuevos en PVC sanitario para fregadero y "
        "lavaplatos. Incluye material.",
        "ud", 640.00, cantidad=1, orden=3,
    ))
    p.capitulos.append(c4)

    # 5 · Baños
    c5 = Capitulo(nombre="BAÑOS", orden=5)
    c5.partidas.append(_partida(
        "Instalación de plato de ducha",
        "Suministro y colocación de plato de ducha con desagüe, conexión a la "
        "red de evacuación, fijación y sellado con silicona. Totalmente "
        "instalado y probado.",
        "ud", 324.00, cantidad=2, orden=1,
    ))
    c5.partidas.append(_partida(
        "Instalación de inodoro y lavamanos",
        "Suministro e instalación de inodoro y lavamanos de porcelana, con "
        "grifería, conexionado, probado y en funcionamiento.",
        "ud", 480.00, cantidad=2, orden=2,
        prod_nombre="Juego sanitario de porcelana", prod_precio=380.00, prod_unidad="ud",
    ))
    c5.partidas.append(_partida(
        "Mampara de vidrio templado",
        "Suministro e instalación de mampara de vidrio templado para ducha, con "
        "perfilería, fijación a paredes y sellado con silicona.",
        "ud", 317.50, cantidad=2, orden=3,
    ))
    p.capitulos.append(c5)

    # 6 · Instalaciones (plomería y electricidad)
    c6 = Capitulo(nombre="INSTALACIONES (PLOMERÍA Y ELECTRICIDAD)", orden=6)
    c6.partidas.append(_partida(
        "Instalación de plomería general",
        "Sustitución de red de agua fría y caliente en tubería PPR, llaves de "
        "corte y desagües en PVC sanitario. Incluye pruebas de estanqueidad.",
        "ud", 1350.00, cantidad=1, orden=1,
    ))
    c6.partidas.append(_partida(
        "Instalación eléctrica (puntos de luz y tomas)",
        "Instalación de circuitos, tablero con protecciones, cableado y "
        "mecanismos (interruptores y tomacorrientes) según plano. Incluye "
        "pruebas de funcionamiento.",
        "ud", 1450.00, cantidad=1, orden=2,
    ))
    c6.partidas.append(_partida(
        "Suministro y montaje de luminarias LED",
        "Suministro e instalación de luminarias LED empotradas y decorativas, "
        "con conexión, pruebas y certificación de funcionamiento.",
        "ud", 980.00, cantidad=1, orden=3,
    ))
    p.capitulos.append(c6)

    # 7 · Pintura y acabados
    c7 = Capitulo(nombre="PINTURA Y ACABADOS", orden=7)
    c7.partidas.append(_partida(
        "Pintura de paramentos interiores",
        "Pintado de paramentos verticales con pintura plástica premium acabado "
        "mate, dos manos más imprimación previa, con reparación de "
        "desperfectos menores y lijado entre manos.",
        "m2", 8.90, mediciones=[("Paredes", 260.00)], orden=1,
    ))
    c7.partidas.append(_partida(
        "Pintura de techos",
        "Pintado de techos con pintura plástica premium acabado mate, dos manos "
        "más imprimación previa.",
        "m2", 9.50, mediciones=[("Techos", 120.00)], orden=2,
    ))
    p.capitulos.append(c7)

    return p


def construir(idioma: str = "es") -> bytes:
    """Construye el presupuesto de muestra y devuelve los bytes del PDF.

    Con `idioma="en"` el documento sale redactado en inglés; con `idioma` un
    mercado concreto («en-US», «en-GB», «en-AU») sale además con el
    vocabulario de ese mercado. El presupuesto, las mediciones y los importes
    son los mismos: cambia la redacción (ver :data:`_TEXTO_EN`).
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    try:
        config = _configuracion()
        cliente = _cliente()
        db.add_all([config, cliente])
        db.flush()
        presupuesto = _presupuesto(cliente)
        # La traducción se aplica sobre el objeto, antes de guardarlo, para
        # que la estructura y las cifras tengan una única fuente.
        mercado = resolver_mercado(idioma)
        huecos = _traducir(presupuesto, cliente, config,
                           en=mercado["idioma"] == "en", mercado=mercado)
        if huecos:
            raise ValueError(
                "La muestra tiene textos sin traducir: " + "; ".join(huecos)
            )
        db.add(presupuesto)
        db.commit()
        db.refresh(presupuesto)
        buf = pdf_service.generar_pdf(presupuesto, config, idioma)
        return buf.getvalue()
    finally:
        db.close()
        engine.dispose()
