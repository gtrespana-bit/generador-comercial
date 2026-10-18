"""Datos iniciales y catálogos reutilizables.

- `sembrar_catalogo`: carga el catálogo propio de partidas y recursos
  (`basedatos_partidas/`: 540 partidas, descomposiciones y cuadro de precios)
  cuando la persona elige el modo demo. Es idempotente: no duplica nombres.
- `sembrar_productos`: carga el catálogo demostrativo de productos.
- `sembrar_demo`: sólo cuando no hay presupuestos crea el cliente y el
  presupuesto ficticios (en USD, con capítulos, mediciones y productos).

Terminología del catálogo y del presupuesto de demostración: venezolana
(concreto, plomería, cielo raso, mesón, afirmado, tomacorriente…).
"""
import json
from datetime import date

from sqlalchemy.orm import Session

from .models import (
    Capitulo,
    Cliente,
    Medicion,
    Partida,
    Producto,
    RecetaEstancia,
    Presupuesto,
    PresupuestoItem,
    proximo_numero,
)
from .paises import es_ingles


# ─────────────────────────────────────────────────────────────────────────────
# Demostración en inglés
#
# Las cifras (precios, cantidades, coeficientes) viven una sola vez en el
# cuerpo de cada función: traducirlas sería una fuente segura de desajustes.
# Lo que se traduce es el rótulo, con vocabulario de obra estadounidense real
# (strip-out, tanking, thin-set, skirting, worktop…), no traducción literal.
# Lo que no esté en la tabla se deja como está.
# ─────────────────────────────────────────────────────────────────────────────

_EN: dict[str, str] = {
    # --- Identidad del documento -------------------------------------------------
    "Cliente de demostración": "Demo client",
    "Remodelación residencial de demostración": "Residential remodel \u2014 demo",
    (
        "Presupuesto elaborado con mediciones tomadas en obra. Incluye mano de obra "
        "especializada, materiales de primera calidad y gestión integral del proyecto. "
        "No incluye enseres, decoración ni equipos de climatización."
    ): (
        "Estimate prepared from measurements taken on site. Includes skilled labour, "
        "premium materials and full project management. Does not include furniture, "
        "decoration or air-conditioning units."
    ),
    (
        "Forma de pago: 40% de anticipo, 35% al 50% de avance certificado y 25% "
        "contra entrega.\nPlazo estimado de ejecución: 12 semanas desde la firma.\n"
        "Garantía de 12 meses en instalaciones y acabados."
    ): (
        "Payment terms: 40% deposit to start, 35% at 50% certified progress and 25% "
        "on handover.\nEstimated completion period: 12 weeks from signature.\n"
        "12-month warranty on installations and finishes."
    ),
    # --- Capítulos ----------------------------------------------------------------
    "MUROS Y PARTICIONES": "WALLS AND PARTITIONS",
    "PISOS": "FLOORING",
    "REMODELACIÓN COCINA": "KITCHEN REMODEL",
    # --- 1 · Muros y particiones ----------------------------------------------------
    "Demolición de partición interior de bloque revestida":
        "Demolition of rendered internal block partition",
    (
        "Demolición de partición interior de fábrica revestida, formada por bloque de "
        "concreto de hasta 20 cm de espesor, con medios manuales, sin afectar a la "
        "estabilidad de los elementos constructivos contiguos, y carga manual sobre "
        "camión o contenedor. El precio incluye el retiro de escombros a vertedero "
        "autorizado y la protección de áreas adyacentes."
    ): (
        "Demolition of a rendered internal masonry partition, built of concrete block "
        "up to 20 cm thick, by hand, without affecting the stability of adjoining "
        "structural elements, including hand loading into a lorry or skip. The price "
        "includes removal of debris to a licensed tip and protection of adjacent areas."
    ),
    "Cocina Aprox (4,00 x 2,50)": "Kitchen approx (4.00 x 2.50)",
    "Tabique Sala": "Living-room partition",
    "Apertura de hueco para puerta o ventana": "Opening formed for door or window",
    (
        "Apertura de hueco en fachada para ventana o puerta mediante medios manuales. "
        "Retirada de escombros hasta planta baja por medios manuales y posterior "
        "retirada a vertedero o punto limpio más cercano por medios mecánicos."
    ): (
        "Formation of an opening in the facade for a window or door by hand. Debris "
        "removed to ground level by hand and then taken to the nearest licensed tip "
        "or recycling point by mechanical means."
    ),
    "Puerta Cocina": "Kitchen door",
    "Ventana Salón": "Living-room window",
    "Hoja de partición interior de bloque de concreto para revestir":
        "Internal concrete block partition leaf, for rendering",
    (
        "Hoja de partición interior, de hasta 20 cm de espesor, de fábrica de bloque "
        "hueco de concreto vibrado sencillo, con juntas horizontales y verticales de "
        "10 mm, recibida con mortero de cemento. Incluye replanteo, plomos y andamiaje ligero."
    ): (
        "Internal partition leaf, up to 20 cm thick, of plain vibrated hollow concrete "
        "blockwork with 10 mm horizontal and vertical joints, laid in cement mortar. "
        "Includes setting out, line and level, and light scaffolding."
    ),
    "Muro Habitación Principal": "Master bedroom wall",
    "Muro Baño Zona Grifería": "Bathroom wall, tap area",
    "Pañete / Repello de paredes": "Wall rendering / plastering",
    (
        "Repello en mortero de cemento sobre paramentos verticales de hasta 10 mm de "
        "espesor, reglado, sacado de rincones y aristas, medido a cinta corrida, para "
        "nivelar paredes y rematado a buena vista para su posterior pintura."
    ): (
        "Cement mortar rendering to vertical surfaces up to 10 mm thick, ruled, with "
        "angles and arises formed, measured overall, to level the walls and finished "
        "to a fair face ready for painting."
    ),
    # --- 2 · Pisos --------------------------------------------------------------------
    "Solado de porcelanato rectificado gran formato":
        "Large-format rectified porcelain floor tiling",
    (
        "Suministro y colocación de porcelanato rectificado formato 90x90 cm, "
        "recibido con adhesivo cementoso mejorado C2 TE, doble encolado, juntado "
        "con fragüe epóxico color gris perla, juntas de 2 mm. Incluye nivelación "
        "de soporte, corte a hilo de agua en aristas y protección final del piso."
    ): (
        "Supply and laying of rectified porcelain tiles, 90x90 cm format, bedded in "
        "improved cementitious adhesive C2 TE with double buttering, pointed with "
        "epoxy grout in pearl grey, 2 mm joints. Includes levelling of the substrate, "
        "wet cutting at arrises and final protection of the floor."
    ),
    "Total + Extra Cortes": "Total + cutting waste",
    "Porcelanato Venetian Grey 90x90 cm rectificado":
        "Venetian Grey rectified porcelain tile 90x90 cm",
    "Zoclo lacado en blanco": "White lacquered skirting",
    (
        "Retirada de zoclos existentes, suministro y montaje de zoclo en madera "
        "MDF lacada blanco mate de 10 cm, fijado con adhesivo de montaje y sellado "
        "perimetral con silicona acrílica."
    ): (
        "Removal of existing skirting, supply and fixing of 10 cm matt white lacquered "
        "MDF skirting, fixed with grab adhesive and sealed around the perimeter with "
        "acrylic silicone."
    ),
    "Total + Extras": "Total + extras",
    # --- 3 · Cocina --------------------------------------------------------------------
    "Revestimiento interior con porcelanato gran formato":
        "Internal large-format porcelain wall tiling",
    (
        "Revestimiento interior con piezas de gran formato. SOPORTE: paramento de "
        "mortero de cemento, vertical, de hasta 3 m de altura. COLOCACIÓN: en capa "
        "fina y mediante doble encolado con adhesivo cementoso mejorado C2 TE S1. "
        "JUNTADO: con fragüe epóxica de altas prestaciones, color blanco, en "
        "juntas de 3 mm. El precio no incluye piezas especiales."
    ): (
        "Internal wall tiling with large-format tiles. BACKGROUND: vertical cement "
        "mortar rendering, up to 3 m high. BEDDING: thin-set, with double buttering "
        "using improved cementitious adhesive C2 TE S1. POINTING: high-performance "
        "epoxy grout, white, 3 mm joints. The price does not include special pieces."
    ),
    "Tramo entre mueble bajo y alto": "Splashback between base and wall units",
    "Porcelanato estilo Calacatta 60x120 cm pulido":
        "Calacatta-style polished porcelain tile 60x120 cm",
    "Instalación de plomería cocina": "Kitchen plumbing installation",
    (
        "Retiro de conexiones antiguas. Instalación de nuevos puntos de agua fría y "
        "caliente en tubería PPR con piezas de conexión y material incluido para "
        "fregadero, lavaplatos y lavadora. Sustitución de llaves de corte y de "
        "desagües antiguos por nuevos desagües en PVC sanitario."
    ): (
        "Removal of existing connections. Installation of new hot and cold water "
        "points in PPR pipe with fittings and materials included for sink, dishwasher "
        "and washing machine. Replacement of isolating valves and existing wastes "
        "with new sanitary PVC wastes."
    ),
    "Completo": "Complete",
    "Suministro e instalación de mesón en cuarzo":
        "Supply and installation of quartz worktop",
    (
        "Suministro e instalación de mesón en cuarzo compacto de 2 cm de espesor, "
        "canto recto pulido, con copete de 10 cm y perforaciones para grifería y "
        "fregadero. Incluye plantillas, fabricación en taller y sellado final."
    ): (
        "Supply and installation of a 20 mm compact quartz worktop with polished "
        "square edge, 100 mm upstand and cut-outs for tap and sink. Includes "
        "templating, workshop fabrication and final sealing."
    ),
    "Mesón principal": "Main worktop",
    "Cuarzo Blanco Norte veta sutil": "Blanco Norte quartz, subtle veining",
    # --- Catálogo de productos de la demo ------------------------------------------------
    "Pisos": "Flooring",
    "Cocina": "Kitchen",
}


def _es_ingles(idioma: str | None) -> bool:
    """Delegado en el registro de mercados, que es la única fuente.
    Así «en-GB» y «en-US» se resuelven como inglés sin duplicar la
    regla en ocho módulos.
    """
    return es_ingles(idioma)


def _t(texto: str, en: bool = False) -> str:
    """Rótulo de la demostración en inglés; si no está catalogado, igual."""
    return _EN.get(texto, texto) if en and texto else texto


def _partida(nombre, descripcion, unidad, precio, mediciones=None, cantidad=0.0, orden=0,
             prod_nombre="", prod_precio=None, prod_unidad=""):
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


def sembrar_demo(db: Session, idioma: str = "es"):
    """Crea cliente, catálogo y un presupuesto de ejemplo si no hay datos.

    ``idioma`` decide el rótulo de la demostración: capítulos, partidas,
    descripciones, conceptos de medición, notas y condiciones. Las cifras
    (precios, cantidades, unidades) son exactamente las mismas en los dos
    idiomas, porque son el contenido que la persona va a inspeccionar y
    sólo pueden vivir en un sitio.
    """
    en = _es_ingles(idioma)
    if db.query(Presupuesto).count() > 0:
        return

    cliente = Cliente(
        nombre=_t("Cliente de demostración", en),
        rif="",
        pais="",
        telefono="",
        email="",
        direccion="Valencia, Carabobo",
        es_demo=True,
    )
    db.add(cliente)
    db.flush()

    hoy = date.today()
    presupuesto = Presupuesto(
        numero=proximo_numero(db, hoy.year),
        year=hoy.year,
        fecha=hoy,
        titulo=_t("Remodelación residencial de demostración", en),
        direccion_obra="Valencia, Carabobo",
        codigo_postal="",
        validez_dias=30,
        moneda="USD",
        impuesto_pct=16.0,
        descuento_pct=0.0,
        estado="borrador",
        es_demo=True,
        client_id=cliente.id,
        notas=_t(
            "Presupuesto elaborado con mediciones tomadas en obra. Incluye mano de obra "
            "especializada, materiales de primera calidad y gestión integral del proyecto. "
            "No incluye enseres, decoración ni equipos de climatización.",
            en,
        ),
        condiciones=_t(
            "Forma de pago: 40% de anticipo, 35% al 50% de avance certificado y 25% "
            "contra entrega.\nPlazo estimado de ejecución: 12 semanas desde la firma.\n"
            "Garantía de 12 meses en instalaciones y acabados.",
            en,
        ),
    )

    # ---- Capítulo 1: Muros y Particiones ------------------------------
    cap1 = Capitulo(nombre=_t("MUROS Y PARTICIONES", en), orden=1)
    cap1.partidas.append(_partida(
        _t("Demolición de partición interior de bloque revestida", en),
        _t(
            "Demolición de partición interior de fábrica revestida, formada por bloque de "
            "concreto de hasta 20 cm de espesor, con medios manuales, sin afectar a la "
            "estabilidad de los elementos constructivos contiguos, y carga manual sobre "
            "camión o contenedor. El precio incluye el retiro de escombros a vertedero "
            "autorizado y la protección de áreas adyacentes.",
            en,
        ),
        "m2", 28.50,
        mediciones=[(_t("Cocina Aprox (4,00 x 2,50)", en), 10.00), (_t("Tabique Sala", en), 4.50)],
        orden=1,
    ))
    cap1.partidas.append(_partida(
        _t("Apertura de hueco para puerta o ventana", en),
        _t(
            "Apertura de hueco en fachada para ventana o puerta mediante medios manuales. "
            "Retirada de escombros hasta planta baja por medios manuales y posterior "
            "retirada a vertedero o punto limpio más cercano por medios mecánicos.",
            en,
        ),
        "ud", 155.00,
        mediciones=[(_t("Puerta Cocina", en), 1.00), (_t("Ventana Salón", en), 1.00)],
        orden=2,
    ))
    cap1.partidas.append(_partida(
        _t("Hoja de partición interior de bloque de concreto para revestir", en),
        _t(
            "Hoja de partición interior, de hasta 20 cm de espesor, de fábrica de bloque "
            "hueco de concreto vibrado sencillo, con juntas horizontales y verticales de "
            "10 mm, recibida con mortero de cemento. Incluye replanteo, plomos y andamiaje ligero.",
            en,
        ),
        "m2", 46.00,
        mediciones=[(_t("Muro Habitación Principal", en), 22.40), (_t("Muro Baño Zona Grifería", en), 2.50)],
        orden=3,
    ))
    cap1.partidas.append(_partida(
        _t("Pañete / Repello de paredes", en),
        _t(
            "Repello en mortero de cemento sobre paramentos verticales de hasta 10 mm de "
            "espesor, reglado, sacado de rincones y aristas, medido a cinta corrida, para "
            "nivelar paredes y rematado a buena vista para su posterior pintura.",
            en,
        ),
        "m2", 17.50,
        mediciones=[("Total", 49.88)],
        orden=4,
    ))
    presupuesto.capitulos.append(cap1)

    # ---- Capítulo 2: Pisos ---------------------------------------------
    cap2 = Capitulo(nombre=_t("PISOS", en), orden=2)
    cap2.partidas.append(_partida(
        _t("Solado de porcelanato rectificado gran formato", en),
        _t(
            "Suministro y colocación de porcelanato rectificado formato 90x90 cm, "
            "recibido con adhesivo cementoso mejorado C2 TE, doble encolado, juntado "
            "con fragüe epóxico color gris perla, juntas de 2 mm. Incluye nivelación "
            "de soporte, corte a hilo de agua en aristas y protección final del piso.",
            en,
        ),
        "m2", 68.00,
        mediciones=[(_t("Total + Extra Cortes", en), 84.60)],
        orden=1,
        prod_nombre=_t("Porcelanato Venetian Grey 90x90 cm rectificado", en),
        prod_precio=26.50, prod_unidad="m2",
    ))
    cap2.partidas.append(_partida(
        _t("Zoclo lacado en blanco", en),
        _t(
            "Retirada de zoclos existentes, suministro y montaje de zoclo en madera "
            "MDF lacada blanco mate de 10 cm, fijado con adhesivo de montaje y sellado "
            "perimetral con silicona acrílica.",
            en,
        ),
        "m", 9.80,
        mediciones=[(_t("Total + Extras", en), 72.00)],
        orden=2,
    ))
    presupuesto.capitulos.append(cap2)

    # ---- Capítulo 3: Cocina --------------------------------------------
    cap3 = Capitulo(nombre=_t("REMODELACIÓN COCINA", en), orden=3)
    cap3.partidas.append(_partida(
        _t("Revestimiento interior con porcelanato gran formato", en),
        _t(
            "Revestimiento interior con piezas de gran formato. SOPORTE: paramento de "
            "mortero de cemento, vertical, de hasta 3 m de altura. COLOCACIÓN: en capa "
            "fina y mediante doble encolado con adhesivo cementoso mejorado C2 TE S1. "
            "JUNTADO: con fragüe epóxica de altas prestaciones, color blanco, en "
            "juntas de 3 mm. El precio no incluye piezas especiales.",
            en,
        ),
        "m2", 58.00,
        mediciones=[(_t("Tramo entre mueble bajo y alto", en), 14.20)],
        orden=1,
        prod_nombre=_t("Porcelanato estilo Calacatta 60x120 cm pulido", en),
        prod_precio=24.00, prod_unidad="m2",
    ))
    cap3.partidas.append(_partida(
        _t("Instalación de plomería cocina", en),
        _t(
            "Retiro de conexiones antiguas. Instalación de nuevos puntos de agua fría y "
            "caliente en tubería PPR con piezas de conexión y material incluido para "
            "fregadero, lavaplatos y lavadora. Sustitución de llaves de corte y de "
            "desagües antiguos por nuevos desagües en PVC sanitario.",
            en,
        ),
        "ud", 640.00,
        mediciones=[(_t("Completo", en), 1.00)],
        orden=2,
    ))
    cap3.partidas.append(_partida(
        _t("Suministro e instalación de mesón en cuarzo", en),
        _t(
            "Suministro e instalación de mesón en cuarzo compacto de 2 cm de espesor, "
            "canto recto pulido, con copete de 10 cm y perforaciones para grifería y "
            "fregadero. Incluye plantillas, fabricación en taller y sellado final.",
            en,
        ),
        "ml", 389.00,
        mediciones=[(_t("Mesón principal", en), 3.10)],
        orden=3,
        prod_nombre=_t("Cuarzo Blanco Norte veta sutil", en),
        prod_precio=295.00, prod_unidad="ml",
    ))
    presupuesto.capitulos.append(cap3)

    db.add(presupuesto)
    db.commit()


# =========================================================================
# El catálogo de partidas vive en basedatos_partidas/ (540 partidas propias
# con descomposición y cuadro de precios). Se carga con
# app.services.catalogo_propio.sembrar_catalogo_propio. Los listados
# CATALOGO_PARTIDAS / PARTIDAS_NUEVAS se mantienen vacíos por compatibilidad
# con código o tests que los importen; ya no son la fuente de verdad.
# =========================================================================
CATALOGO_PARTIDAS = []
PARTIDAS_NUEVAS = []


# =========================================================================
# Catálogo inicial de productos (se amplía automáticamente con los productos
# nuevos que se escriban al crear presupuestos).
# =========================================================================
PRODUCTOS_DEMO = [
    ("Porcelanato Venetian Grey 90x90 cm rectificado", "", 26.50, "m2", "Pisos"),
    ("Porcelanato estilo Calacatta 60x120 cm pulido", "", 24.00, "m2", "Pisos"),
    ("Cuarzo Blanco Norte veta sutil", "", 295.00, "ml", "Cocina"),
]


def sembrar_catalogo(db: Session):
    """Siembra inicial del catálogo propio de partidas (solo una vez).

    Carga las partidas y recursos de ``basedatos_partidas/`` (540 partidas
    con descomposición completa y cuadro de precios). Tras la primera
    siembra se marca ``semilla_catalogo_aplicada``: si el usuario borra
    partidas preinstaladas no reaparecen. Las partidas existentes nunca se
    sobrescriben.
    """
    from .models import Configuracion
    from .services.catalogo_propio import disponible, sembrar_catalogo_propio

    cfg = db.query(Configuracion).first()
    # Si ya se aplicó la semilla, no volver a inyectar
    if cfg and getattr(cfg, "semilla_catalogo_aplicada", False):
        return
    # Si la BD ya tiene datos (partidas o presupuestos) pero la flag aún es
    # False (BD antigua pre-flag), marcar como aplicada y no reinyectar
    # faltantes (respeta borrados del usuario).
    has_data = False
    try:
        has_data = db.query(Partida).count() > 0 or db.query(Presupuesto).count() > 0
    except Exception:
        has_data = False
    if cfg and has_data and not getattr(cfg, "semilla_catalogo_aplicada", False):
        cfg.semilla_catalogo_aplicada = True
        db.commit()
        return
    # Instalación fresca: cargar el catálogo propio (partidas + recursos).
    if disponible():
        sembrar_catalogo_propio(db)
    else:
        # Una carga no realizada no puede darse por aplicada. Permite
        # reintentar tras corregir el empaquetado del catálogo.
        return
    # Marcar semilla como aplicada
    cfg = db.query(Configuracion).first()
    if cfg is not None:
        cfg.semilla_catalogo_aplicada = True
    else:
        try:
            cfg = Configuracion(semilla_catalogo_aplicada=True)
            db.add(cfg)
        except Exception:
            pass
    db.commit()


def sembrar_productos(db: Session, idioma: str = "es"):
    """Catálogo inicial de productos (solo una vez, respeta borrados)."""
    en = _es_ingles(idioma)
    from .models import Configuracion
    cfg = db.query(Configuracion).first()
    if cfg and getattr(cfg, "semilla_productos_aplicada", False):
        return
    has_data = False
    try:
        has_data = db.query(Producto).count() > 0
    except Exception:
        has_data = False
    if cfg and has_data and not getattr(cfg, "semilla_productos_aplicada", False):
        cfg.semilla_productos_aplicada = True
        db.commit()
        return
    for nombre, desc, precio, unidad, categoria in PRODUCTOS_DEMO:
        nombre = _t(nombre, en)
        categoria = _t(categoria, en)
        if not db.query(Producto).filter(Producto.nombre == nombre).first():
            db.add(Producto(
                nombre=nombre,
                descripcion=desc,
                precio_unitario=precio,
                unidad=unidad,
                categoria=categoria,
            ))
    if cfg is not None:
        cfg.semilla_productos_aplicada = True
    db.commit()


RECETAS_DEMO = [
    {
        "nombre": "Baño Principal de Lujo",
        "descripcion": "Reforma integral de baño principal con acabados de alta gama, plomería nueva, revestimiento porcelánico e iluminación empotrada.",
        "categoria": "Baños",
        "unidad_base": "m²",
        "cantidad_base_default": 8.0,
        "datos": json.dumps([
            {
                "nombre": "Demolición de revestimiento y piso existente",
                "descripcion": "Picado de azulejos y pavimento existente, carga manual y transporte de escombros a botadero autorizado.",
                "unidad": "m²",
                "precio": 12.50,
                "categoria": "Albañilería y Revestimientos",
                "tipo_calculo": "proporcional",
                "coeficiente": 1.0,
            },
            {
                "nombre": "Impermeabilización de zona húmeda con membrana elástica",
                "descripcion": "Aplicación de membrana líquida de poliuretano y malla de fibra en suelo y muros del área de ducha.",
                "unidad": "m²",
                "precio": 18.50,
                "categoria": "Albañilería y Revestimientos",
                "tipo_calculo": "proporcional",
                "coeficiente": 0.6,
            },
            {
                "nombre": "Preparación y nivelación de contrapiso para solado",
                "descripcion": "Mortero de regularización y nivelación para recibir baldosas en capa fina.",
                "unidad": "m²",
                "precio": 9.50,
                "categoria": "Albañilería y Revestimientos",
                "tipo_calculo": "proporcional",
                "coeficiente": 1.0,
            },
            {
                "nombre": "Solado porcelánico antideslizante 60x120 en capa fina",
                "descripcion": "Suministro y colocación de pavimento porcelánico rectificado, pegado con mortero cola impermeable y juntas de fragüe.",
                "unidad": "m²",
                "precio": 42.00,
                "categoria": "Pisos y Revestimientos",
                "tipo_calculo": "proporcional",
                "coeficiente": 1.0,
            },
            {
                "nombre": "Revestimiento / Enchape mural porcelánico de gran formato",
                "descripcion": "Revestimiento de paredes de baño en porcelánico rectificado esmaltado, incluyendo cortes y cantoneras.",
                "unidad": "m²",
                "precio": 46.00,
                "categoria": "Pisos y Revestimientos",
                "tipo_calculo": "proporcional",
                "coeficiente": 3.2,
            },
            {
                "nombre": "Cielo raso continuo de yeso laminado hidrófugo",
                "descripcion": "Techo falso con placas resistentes a la humedad (placa verde), emplastecido y preparado para pintar.",
                "unidad": "m²",
                "precio": 32.00,
                "categoria": "Albañilería y Revestimientos",
                "tipo_calculo": "proporcional",
                "coeficiente": 1.0,
            },
            {
                "nombre": "Puntos de plomería agua fría/caliente y desagües termofusión",
                "descripcion": "Instalación completa de tubería en polipropileno termofusión para lavabos, ducha e inodoro.",
                "unidad": "pto",
                "precio": 65.00,
                "categoria": "Fontanería / Plomería",
                "tipo_calculo": "fijo",
                "cantidad_fija": 4.0,
            },
            {
                "nombre": "Iluminación empotrada LED estanca IP65 en techo",
                "descripcion": "Suministro e instalación de downlight LED orientable estanco para zona húmeda.",
                "unidad": "und",
                "precio": 35.00,
                "categoria": "Electricidad e Iluminación",
                "tipo_calculo": "fijo",
                "cantidad_fija": 4.0,
            },
            {
                "nombre": "Suministro e instalación de inodoro suspendido con cisterna empotrada",
                "descripcion": "Inodoro de porcelana vitrificada suspendido con estructura metálica y placa de pulsación de diseño.",
                "unidad": "und",
                "precio": 480.00,
                "categoria": "Piezas Sanitarias",
                "tipo_calculo": "fijo",
                "cantidad_fija": 1.0,
            },
            {
                "nombre": "Mueble de baño de lujo con doble lavabo y mesón de cuarzo",
                "descripcion": "Mueble suspendido lacado mate con encimera de cuarzo y lavabos sobre encimera integrados.",
                "unidad": "und",
                "precio": 850.00,
                "categoria": "Carpintería y Muebles",
                "tipo_calculo": "fijo",
                "cantidad_fija": 1.0,
            },
            {
                "nombre": "Grifería monocomando empotrada acabado negro mate / cepillado",
                "descripcion": "Grifería mural monocomando para lavabos y ducha con cartucho cerámico y desviador.",
                "unidad": "und",
                "precio": 190.00,
                "categoria": "Piezas Sanitarias",
                "tipo_calculo": "fijo",
                "cantidad_fija": 2.0,
            },
            {
                "nombre": "Mampara de ducha de cristal templado 8mm y herrajes de acero",
                "descripcion": "Mampara corredera y panel fijo a medida de vidrio de seguridad transparente tratamiento antical.",
                "unidad": "und",
                "precio": 520.00,
                "categoria": "Piezas Sanitarias",
                "tipo_calculo": "fijo",
                "cantidad_fija": 1.0,
            }
        ], ensure_ascii=False)
    },
    {
        "nombre": "Cocina Integral de Lujo con Isla",
        "descripcion": "Reforma integral de cocina con solado porcelánico, mesón/tope de cuarzo, iluminación LED y circuitos de fuerza dedicados.",
        "categoria": "Cocinas",
        "unidad_base": "m²",
        "cantidad_base_default": 15.0,
        "datos": json.dumps([
            {
                "nombre": "Demolición de cocina existente y retiro de revestimientos",
                "descripcion": "Demolición de mesones antiguos, azulejos, mobiliario viejo y recogida y botadero autorizado.",
                "unidad": "m²",
                "precio": 15.00,
                "categoria": "Albañilería y Revestimientos",
                "tipo_calculo": "proporcional",
                "coeficiente": 1.0,
            },
            {
                "nombre": "Preparación y regularización de superficies para revestimientos",
                "descripcion": "Friso / repello maestreado con mortero de cemento para recibir nuevos cerámicos.",
                "unidad": "m²",
                "precio": 11.00,
                "categoria": "Albañilería y Revestimientos",
                "tipo_calculo": "proporcional",
                "coeficiente": 1.0,
            },
            {
                "nombre": "Solado porcelánico rectificado formato 120x120 cm",
                "descripcion": "Suministro y colocación de gres porcelánico gran formato antideslizante con junta epóxica anti-manchas.",
                "unidad": "m²",
                "precio": 55.00,
                "categoria": "Pisos y Revestimientos",
                "tipo_calculo": "proporcional",
                "coeficiente": 1.0,
            },
            {
                "nombre": "Revestimiento de salpicadero / backsplash en piedra sinterizada",
                "descripcion": "Revestimiento continuo entre mesón y gabinetes superiores en placa de Neolith o Cuarzo Silestone.",
                "unidad": "m²",
                "precio": 95.00,
                "categoria": "Pisos y Revestimientos",
                "tipo_calculo": "proporcional",
                "coeficiente": 0.35,
            },
            {
                "nombre": "Circuitos eléctricos de fuerza independientes (Horno, Cocina, Microondas)",
                "descripcion": "Cableado y tomacorrientes con protección termomagnética individual para artefactos de alto consumo.",
                "unidad": "pto",
                "precio": 85.00,
                "categoria": "Electricidad e Iluminación",
                "tipo_calculo": "fijo",
                "cantidad_fija": 3.0,
            },
            {
                "nombre": "Puntos de plomería para fregadero, lavaplatos y fabricador de hielo",
                "descripcion": "Instalación de abastos de agua, llaves de paso angulares y desagües sifonados.",
                "unidad": "pto",
                "precio": 70.00,
                "categoria": "Fontanería / Plomería",
                "tipo_calculo": "fijo",
                "cantidad_fija": 2.0,
            },
            {
                "nombre": "Iluminación en techo y tiras LED cálidas bajo gabinetes",
                "descripcion": "Iluminación arquitectónica difusa para zona de trabajo de cocina con perfil aluminio y difusor.",
                "unidad": "m²",
                "precio": 28.00,
                "categoria": "Electricidad e Iluminación",
                "tipo_calculo": "proporcional",
                "coeficiente": 1.0,
            },
            {
                "nombre": "Tope / mesón de cocina e isla en cuarzo o piedra sinterizada",
                "descripcion": "Suministro, corte, regrueso y montaje de tope de 2 cm en cuarzo con huecos bajo cubierta para fregadero.",
                "unidad": "ml",
                "precio": 260.00,
                "categoria": "Carpintería y Muebles",
                "tipo_calculo": "fijo",
                "cantidad_fija": 6.5,
            }
        ], ensure_ascii=False)
    },
    {
        "nombre": "Reforma Integral de Suelos y Pisos de Lujo",
        "descripcion": "Sustitución general de pavimentos residenciales con porcelánico de gran formato, autonivelante y rodapié lacado.",
        "categoria": "Suelos",
        "unidad_base": "m²",
        "cantidad_base_default": 100.0,
        "datos": json.dumps([
            {
                "nombre": "Levantado y retirada de pavimento existente y zócalos",
                "descripcion": "Desprendimiento mecánico de pisos viejos y transporte a escombrera.",
                "unidad": "m²",
                "precio": 6.50,
                "categoria": "Albañilería y Revestimientos",
                "tipo_calculo": "proporcional",
                "coeficiente": 1.0,
            },
            {
                "nombre": "Preparación de contrapiso con pasta autonivelante de alta resistencia",
                "descripcion": "Aplicación de imprimación y mortero autonivelante de endurecimiento rápido hasta 10mm.",
                "unidad": "m²",
                "precio": 12.00,
                "categoria": "Albañilería y Revestimientos",
                "tipo_calculo": "proporcional",
                "coeficiente": 1.0,
            },
            {
                "nombre": "Solado de porcelánico 120x120 cm o madera laminada hidrófuga AC5",
                "descripcion": "Suministro e instalación en capa fina de pavimento de gran formato con mortero adhesivo C2TE y cuñas de nivelación.",
                "unidad": "m²",
                "precio": 48.00,
                "categoria": "Pisos y Revestimientos",
                "tipo_calculo": "proporcional",
                "coeficiente": 1.05,
            },
            {
                "nombre": "Fragüe / Juntado con lechada epóxica anti-manchas impermeable",
                "descripcion": "Rejuntado de juntas entre baldosas con mortero epóxico impermeable e inalterable.",
                "unidad": "m²",
                "precio": 4.50,
                "categoria": "Pisos y Revestimientos",
                "tipo_calculo": "proporcional",
                "coeficiente": 1.0,
            },
            {
                "nombre": "Rodapié / zoclo lacado en blanco o empotrado minimalista",
                "descripcion": "Suministro e instalación fijado con adhesivo de montaje, incluyendo sellado superior de juntas.",
                "unidad": "ml",
                "precio": 14.00,
                "categoria": "Carpintería y Muebles",
                "tipo_calculo": "proporcional",
                "coeficiente": 0.85,
            }
        ], ensure_ascii=False)
    },
    {
        "nombre": "Dormitorio Principal Suite con Vestidor",
        "descripcion": "Acabados de lujo en dormitorio, iluminación escenográfica, tomacorrientes USB y vestidor a medida.",
        "categoria": "Habitaciones",
        "unidad_base": "m²",
        "cantidad_base_default": 24.0,
        "datos": json.dumps([
            {
                "nombre": "Alisado general de paredes y preparación para pintura premium",
                "descripcion": "Masillado de muros, lijado mecánico e imprimación selladora.",
                "unidad": "m²",
                "precio": 9.50,
                "categoria": "Albañilería y Revestimientos",
                "tipo_calculo": "proporcional",
                "coeficiente": 2.8,
            },
            {
                "nombre": "Pintura plástica satinada lavable de alta gama (3 manos)",
                "descripcion": "Aplicación de pintura acrílica premium satinada resistente a roces en colores según diseño.",
                "unidad": "m²",
                "precio": 8.00,
                "categoria": "Albañilería y Revestimientos",
                "tipo_calculo": "proporcional",
                "coeficiente": 2.8,
            },
            {
                "nombre": "Cielo raso con foso perimetral para iluminación indirecta",
                "descripcion": "Techo falso de yeso laminado con candileja para foseado LED decorativo.",
                "unidad": "m²",
                "precio": 36.00,
                "categoria": "Albañilería y Revestimientos",
                "tipo_calculo": "proporcional",
                "coeficiente": 1.0,
            },
            {
                "nombre": "Pavimento de madera laminada alta gama con base acústica",
                "descripcion": "Suministro e instalación flotante de piso laminado AC5 con manta acústica anti-humedad.",
                "unidad": "m²",
                "precio": 44.00,
                "categoria": "Pisos y Revestimientos",
                "tipo_calculo": "proporcional",
                "coeficiente": 1.0,
            },
            {
                "nombre": "Puntos eléctricos de tomacorrientes de cabecera con puertos USB-C",
                "descripcion": "Mecanismos de lujo empotrados en zona de veladores con puertos USB integrados.",
                "unidad": "pto",
                "precio": 42.00,
                "categoria": "Electricidad e Iluminación",
                "tipo_calculo": "fijo",
                "cantidad_fija": 8.0,
            },
            {
                "nombre": "Vestidor / closet modular a medida lacado mate de diseño",
                "descripcion": "Suministro y montaje de closet modular con cajoneras, barras LED iluminadas y herrajes de cierre suave.",
                "unidad": "ml",
                "precio": 420.00,
                "categoria": "Carpintería y Muebles",
                "tipo_calculo": "fijo",
                "cantidad_fija": 4.5,
            }
        ], ensure_ascii=False)
    },
    {
        "nombre": "Sala / Comedor de Alta Gama con Luz Indirecta",
        "descripcion": "Reforma de área social de la vivienda con techos arquitectónicos de luz indirecta, pisos de gran formato y pintura premium.",
        "categoria": "Habitaciones",
        "unidad_base": "m²",
        "cantidad_base_default": 40.0,
        "datos": json.dumps([
            {
                "nombre": "Cielo raso arquitectónico de yeso con candileja de luz indirecta",
                "descripcion": "Techo de escayola / yeso laminado con cajetes perimetrales para ocultar tiras LED decorativas.",
                "unidad": "m²",
                "precio": 38.00,
                "categoria": "Albañilería y Revestimientos",
                "tipo_calculo": "proporcional",
                "coeficiente": 1.0,
            },
            {
                "nombre": "Alisado general de muros e imprimación selladora",
                "descripcion": "Masillado general y lijado para lograr superficie lisa perfecta sin imperfecciones.",
                "unidad": "m²",
                "precio": 9.50,
                "categoria": "Albañilería y Revestimientos",
                "tipo_calculo": "proporcional",
                "coeficiente": 2.5,
            },
            {
                "nombre": "Pintura satinada premium lavable en muros y mate en techo",
                "descripcion": "Aplicación a rodillo y pistola de 3 manos de pintura plástica vinílica de alta adherencia.",
                "unidad": "m²",
                "precio": 8.00,
                "categoria": "Albañilería y Revestimientos",
                "tipo_calculo": "proporcional",
                "coeficiente": 3.5,
            },
            {
                "nombre": "Solado porcelánico gran formato rectificado color neutro",
                "descripcion": "Suministro e instalación en salón y comedor de porcelánico de gran formato en capa fina.",
                "unidad": "m²",
                "precio": 52.00,
                "categoria": "Pisos y Revestimientos",
                "tipo_calculo": "proporcional",
                "coeficiente": 1.0,
            },
            {
                "nombre": "Sistema de iluminación escenográfica LED regulable (Dimmable)",
                "descripcion": "Circuitos e instalación de tiras LED y downlights regulables en intensidad por zona.",
                "unidad": "m²",
                "precio": 22.00,
                "categoria": "Electricidad e Iluminación",
                "tipo_calculo": "proporcional",
                "coeficiente": 1.0,
            }
        ], ensure_ascii=False)
    },
    {
        "nombre": "Instalación Eléctrica e Iluminación Residencial Completa",
        "descripcion": "Renovación total de electricidad, tablero de protecciones y circuitos LED según normativa.",
        "categoria": "Electricidad",
        "unidad_base": "m²",
        "cantidad_base_default": 120.0,
        "datos": json.dumps([
            {
                "nombre": "Tablero eléctrico general de 24 circuitos con protecciones",
                "descripcion": "Tablero empotrado con interruptor principal, disyuntores diferenciales y térmicos por circuito.",
                "unidad": "und",
                "precio": 650.00,
                "categoria": "Electricidad e Iluminación",
                "tipo_calculo": "fijo",
                "cantidad_fija": 1.0,
            },
            {
                "nombre": "Circuitos generales de iluminación LED con cable de cobre antiflama",
                "descripcion": "Canalización y cableado libre de halógenos para puntos de luz en estancias.",
                "unidad": "pto",
                "precio": 55.00,
                "categoria": "Electricidad e Iluminación",
                "tipo_calculo": "proporcional",
                "coeficiente": 0.15,
            },
            {
                "nombre": "Circuitos de tomacorrientes generales y especiales de fuerza",
                "descripcion": "Tomacorrientes polarizados y con protección a tierra con placas de diseño contemporáneo.",
                "unidad": "pto",
                "precio": 48.00,
                "categoria": "Electricidad e Iluminación",
                "tipo_calculo": "proporcional",
                "coeficiente": 0.25,
            },
            {
                "nombre": "Downlights LED minimalistas empotrados de bajo consumo",
                "descripcion": "Suministro y colocación de focos LED 9W/12W luz cálida o neutra alta fidelidad cromática.",
                "unidad": "und",
                "precio": 32.00,
                "categoria": "Electricidad e Iluminación",
                "tipo_calculo": "proporcional",
                "coeficiente": 0.20,
            },
            {
                "nombre": "Tiras de iluminación LED cálida en candilejas y cortineros",
                "descripcion": "Suministro e instalación de perfil de aluminio con tira LED 24V y fuente de alimentación.",
                "unidad": "ml",
                "precio": 24.00,
                "categoria": "Electricidad e Iluminación",
                "tipo_calculo": "proporcional",
                "coeficiente": 0.25,
            }
        ], ensure_ascii=False)
    }
]


def sembrar_recetas(db: Session):
    """Catálogo inicial de Recetas / Packs de Estancia de remodelación (idempotente)."""
    from .models import Configuracion, RecetaEstancia
    cfg = db.query(Configuracion).first()
    if cfg and getattr(cfg, "semilla_recetas_aplicada", False):
        return
    has_data = False
    try:
        has_data = db.query(RecetaEstancia).count() > 0
    except Exception:
        has_data = False
    if cfg and has_data and not getattr(cfg, "semilla_recetas_aplicada", False):
        cfg.semilla_recetas_aplicada = True
        db.commit()
        return
    for rec in RECETAS_DEMO:
        if not db.query(RecetaEstancia).filter(RecetaEstancia.nombre == rec["nombre"]).first():
            db.add(RecetaEstancia(
                nombre=rec["nombre"],
                descripcion=rec["descripcion"],
                categoria=rec["categoria"],
                unidad_base=rec["unidad_base"],
                cantidad_base_default=rec["cantidad_base_default"],
                datos=rec["datos"],
            ))
    if cfg is not None:
        cfg.semilla_recetas_aplicada = True
    db.commit()

