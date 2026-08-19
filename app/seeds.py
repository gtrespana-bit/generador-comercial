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


def sembrar_demo(db: Session):
    """Crea cliente, catálogo y un presupuesto de ejemplo si no hay datos."""
    if db.query(Presupuesto).count() > 0:
        return

    cliente = Cliente(
        nombre="Cliente de demostración",
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
        titulo="Remodelación residencial de demostración",
        direccion_obra="Valencia, Carabobo",
        codigo_postal="",
        validez_dias=30,
        moneda="USD",
        impuesto_pct=16.0,
        descuento_pct=0.0,
        estado="borrador",
        es_demo=True,
        client_id=cliente.id,
        notas=("Presupuesto elaborado con mediciones tomadas en obra. Incluye mano de obra "
               "especializada, materiales de primera calidad y gestión integral del proyecto. "
               "No incluye enseres, decoración ni equipos de climatización."),
        condiciones=("Forma de pago: 40% de anticipo, 35% al 50% de avance certificado y 25% "
                     "contra entrega.\nPlazo estimado de ejecución: 12 semanas desde la firma.\n"
                     "Garantía de 12 meses en instalaciones y acabados."),
    )

    # ---- Capítulo 1: Muros y Particiones ------------------------------
    cap1 = Capitulo(nombre="MUROS Y PARTICIONES", orden=1)
    cap1.partidas.append(_partida(
        "Demolición de partición interior de bloque revestida",
        "Demolición de partición interior de fábrica revestida, formada por bloque de "
        "concreto de hasta 20 cm de espesor, con medios manuales, sin afectar a la "
        "estabilidad de los elementos constructivos contiguos, y carga manual sobre "
        "camión o contenedor. El precio incluye el retiro de escombros a vertedero "
        "autorizado y la protección de áreas adyacentes.",
        "m2", 28.50,
        mediciones=[("Cocina Aprox (4,00 x 2,50)", 10.00), ("Tabique Sala", 4.50)],
        orden=1,
    ))
    cap1.partidas.append(_partida(
        "Apertura de hueco para puerta o ventana",
        "Apertura de hueco en fachada para ventana o puerta mediante medios manuales. "
        "Retirada de escombros hasta planta baja por medios manuales y posterior "
        "retirada a vertedero o punto limpio más cercano por medios mecánicos.",
        "ud", 155.00,
        mediciones=[("Puerta Cocina", 1.00), ("Ventana Salón", 1.00)],
        orden=2,
    ))
    cap1.partidas.append(_partida(
        "Hoja de partición interior de bloque de concreto para revestir",
        "Hoja de partición interior, de hasta 20 cm de espesor, de fábrica de bloque "
        "hueco de concreto vibrado sencillo, con juntas horizontales y verticales de "
        "10 mm, recibida con mortero de cemento. Incluye replanteo, plomos y andamiaje ligero.",
        "m2", 46.00,
        mediciones=[("Muro Habitación Principal", 22.40), ("Muro Baño Zona Grifería", 2.50)],
        orden=3,
    ))
    cap1.partidas.append(_partida(
        "Pañete / Repello de paredes",
        "Repello en mortero de cemento sobre paramentos verticales de hasta 10 mm de "
        "espesor, reglado, sacado de rincones y aristas, medido a cinta corrida, para "
        "nivelar paredes y rematado a buena vista para su posterior pintura.",
        "m2", 17.50,
        mediciones=[("Total", 49.88)],
        orden=4,
    ))
    presupuesto.capitulos.append(cap1)

    # ---- Capítulo 2: Pisos ---------------------------------------------
    cap2 = Capitulo(nombre="PISOS", orden=2)
    cap2.partidas.append(_partida(
        "Solado de porcelanato rectificado gran formato",
        "Suministro y colocación de porcelanato rectificado formato 90x90 cm, "
        "recibido con adhesivo cementoso mejorado C2 TE, doble encolado, juntado "
        "con fragüe epóxico color gris perla, juntas de 2 mm. Incluye nivelación "
        "de soporte, corte a hilo de agua en aristas y protección final del piso.",
        "m2", 68.00,
        mediciones=[("Total + Extra Cortes", 84.60)],
        orden=1,
        prod_nombre="Porcelanato Venetian Grey 90x90 cm rectificado",
        prod_precio=26.50, prod_unidad="m2",
    ))
    cap2.partidas.append(_partida(
        "Zoclo lacado en blanco",
        "Retirada de zoclos existentes, suministro y montaje de zoclo en madera "
        "MDF lacada blanco mate de 10 cm, fijado con adhesivo de montaje y sellado "
        "perimetral con silicona acrílica.",
        "m", 9.80,
        mediciones=[("Total + Extras", 72.00)],
        orden=2,
    ))
    presupuesto.capitulos.append(cap2)

    # ---- Capítulo 3: Cocina --------------------------------------------
    cap3 = Capitulo(nombre="REMODELACIÓN COCINA", orden=3)
    cap3.partidas.append(_partida(
        "Revestimiento interior con porcelanato gran formato",
        "Revestimiento interior con piezas de gran formato. SOPORTE: paramento de "
        "mortero de cemento, vertical, de hasta 3 m de altura. COLOCACIÓN: en capa "
        "fina y mediante doble encolado con adhesivo cementoso mejorado C2 TE S1. "
        "JUNTADO: con fragüe epóxica de altas prestaciones, color blanco, en "
        "juntas de 3 mm. El precio no incluye piezas especiales.",
        "m2", 58.00,
        mediciones=[("Tramo entre mueble bajo y alto", 14.20)],
        orden=1,
        prod_nombre="Porcelanato estilo Calacatta 60x120 cm pulido",
        prod_precio=24.00, prod_unidad="m2",
    ))
    cap3.partidas.append(_partida(
        "Instalación de plomería cocina",
        "Retiro de conexiones antiguas. Instalación de nuevos puntos de agua fría y "
        "caliente en tubería PPR con piezas de conexión y material incluido para "
        "fregadero, lavaplatos y lavadora. Sustitución de llaves de corte y de "
        "desagües antiguos por nuevos desagües en PVC sanitario.",
        "ud", 640.00,
        mediciones=[("Completo", 1.00)],
        orden=2,
    ))
    cap3.partidas.append(_partida(
        "Suministro e instalación de mesón en cuarzo",
        "Suministro e instalación de mesón en cuarzo compacto de 2 cm de espesor, "
        "canto recto pulido, con copete de 10 cm y perforaciones para grifería y "
        "fregadero. Incluye plantillas, fabricación en taller y sellado final.",
        "ml", 389.00,
        mediciones=[("Mesón principal", 3.10)],
        orden=3,
        prod_nombre="Cuarzo Blanco Norte veta sutil",
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
        # Empaquetado sin basedatos_partidas: no se inventa un catálogo de
        # prueba. El usuario importará el suyo o creará partidas a mano.
        pass
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


def sembrar_productos(db: Session):
    """Catálogo inicial de productos (solo una vez, respeta borrados)."""
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

