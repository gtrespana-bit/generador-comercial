"""Datos iniciales y catálogos reutilizables.

- `sembrar_catalogo`: mantiene el catálogo de partidas (se ejecuta en cada
  arranque, es idempotente: crea las que faltan y actualiza las partidas
  «nuevas» especificadas por el usuario si ya existían con datos distintos).
- `sembrar_productos`: catálogo inicial de productos (idempotente).
- `sembrar_demo`: sólo cuando la base de datos está vacía crea el
  presupuesto de ejemplo de remodelación de lujo (en USD, con capítulos,
  mediciones y productos presupuestados).

Catálogo inicial de demostración adaptado al mercado venezolano:
  · "hormigón" → "concreto"
  · "fontanería" → "plomería"
  · "enchufes / tomas" → "tomacorrientes"
  · "toma de telefonía" → "jack telefónico"
  · "toma de antena" → "jack de antena"
  · "enfoscado" → "repello / pañete"
  · "alicate" → "enchape / alicatado"
  · "falso techo" → "cielo raso"
  · "rodapié" → "zoclo"
  · "solera" → "losa"
  · "atezado" → "afirmado"
  · "balconera" → "balconera"
  · "oscilobatiente" → "abrible"
  · "corredera" → "corrediza"
  · "boquilla / rejuntado" → "fragüe / juntado"
  · "lavavajillas" → "lavaplatos"
  · "grifo" → "grifo / llave"
  · "mueble de baño" → "gabinete de baño"
  · "encimera" → "mesón"
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
        pais="Venezuela",
        telefono="",
        email="",
        direccion="Valencia, Carabobo",
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
# Catálogo completo de partidas (basado en el PDF de referencia, adaptado
# al vocabulario venezolano). Se sincroniza en cada arranque creando las
# que falten (sin tocar las que ya existan: respeta las ediciones).
# =========================================================================
CATALOGO_PARTIDAS = [
        # ─ Demoliciones ──────────────────────────────────────────────
        ("Demolición de partición interior de bloque",
         "Demolición de partición interior de fábrica revestida, formada por bloque de concreto de hasta 20 cm de espesor, con medios manuales y carga sobre camión o contenedor. Incluye retiro de escombros a vertedero autorizado.",
         28.50, "m2", "Demoliciones"),
        ("Demolición de pavimento cerámico",
         "Demolición de piso existente en el interior del edificio, de baldosas cerámicas de gres esmaltado, con medios manuales o martillo eléctrico, sin deteriorar los elementos constructivos contiguos. Incluye picado del material de agarre adherido al soporte.",
         14.50, "m2", "Demoliciones"),
        ("Demolición de enchape / alicatado",
         "Demolición de enchape de cerámica, con medios manuales, y carga manual sobre camión o contenedor. Incluye el picado del material de agarre adherido al soporte.",
         13.50, "m2", "Demoliciones"),
        ("Apertura de hueco para puerta o ventana",
         "Apertura de hueco en fachada para ventana o puerta mediante medios manuales. Retirada de escombros hasta planta baja y posterior retirada a vertedero autorizado.",
         155.00, "ud", "Demoliciones"),
        ("Remates tras demoliciones",
         "Remates en paredes y techos tras demoliciones. Incluye reparación de daños menores y nivelación de superficies.",
         330.00, "ud", "Demoliciones"),
        ("Desmontaje de conjunto de mobiliario de cocina",
         "Desmontaje de conjunto de mobiliario de cocina, con medios manuales, sin afectar a la estabilidad de los elementos resistentes, y carga manual sobre camión o contenedor.",
         239.45, "ml", "Demoliciones"),
        ("Desmontaje de aparato sanitario",
         "Desmontaje sanitario existente (inodoro / lavabo / bidé / bañera / ducha). Traslado mediante medios manuales a contenedor y/o vertedero autorizado.",
         25.00, "ud", "Demoliciones"),

        # ── Muros y Particiones ───────────────────────────────────────
        ("Hoja de partición interior de bloque de concreto",
         "Hoja de partición interior, de hasta 20 cm de espesor, de fábrica de bloque hueco de concreto vibrado sencillo, con juntas horizontales y verticales de 10 mm, recibida con mortero de cemento industrial M-5.",
         46.00, "m2", "Muros"),
        ("Pañete / Repello de paredes",
         "Pañete en mortero de cemento sobre paramentos verticales de hasta 10 mm de espesor, reglado, sacado de rincones y aristas, medido a cinta corrida, para nivelar paredes y rematado a buena vista para su posterior pintura o enchape.",
         17.50, "m2", "Muros"),
        ("Pañete de paredes para cocina o baño",
         "Pañete en mortero de cemento sobre paramentos verticales de hasta 10 mm de espesor, reglado, sacado de rincones y aristas, para nivelar paredes y rematado para posterior colocación de material cerámico.",
         14.50, "m2", "Muros"),

        # ── Pisos ─────────────────────────────────────────────────────
        ("Solado de porcelanato rectificado gran formato",
         "Suministro y colocación de porcelanato rectificado de hasta 90x90 cm, recibido con adhesivo cementoso mejorado C2 TE, doble encolado y juntado con fragüe epóxica, juntas de 2 mm. Incluye nivelación de soporte, corte a hilo de agua y protección final.",
         68.00, "m2", "Pisos"),
        ("Solado de baldosas cerámicas en capa fina",
         "Solado de baldosas cerámicas de gres porcelánico, acabado pulido, de hasta 60x120 cm, recibidas con adhesivo cementoso mejorado C2 TE con deslizamiento reducido y tiempo abierto ampliado, con doble encolado y juntadas con mortero de juntas cementoso tipo L para juntas de hasta 3 mm.",
         52.00, "m2", "Pisos"),
        ("Solado de baldosas cerámicas en exterior",
         "Solado de baldosas cerámicas de absorción de agua E<0.5%, grupo BIa, resistencia al deslizamiento Rd>45, clase 3, recibidas con adhesivo C2 TE con doble encolado y juntadas con mortero tipo CG 2 W A, color blanco, para juntas de 2 a 15 mm.",
         56.00, "m2", "Pisos"),
        ("Zoclo lacado en blanco",
         "Retirada de zoclos existentes, suministro y montaje de zoclo en madera MDF lacada blanco mate de 10 cm, fijado con adhesivo de montaje y sellado perimetral con silicona acrílica.",
         9.80, "m", "Pisos"),
        ("Zoclo de madera",
         "Retirada de zoclos antiguos, suministro y montaje de zoclos nuevos en madera color blanco.",
         7.50, "m", "Pisos"),

        # ── Pisos Exteriores ──────────────────────────────────────────
        ("Losa de concreto con malla electrosoldada",
         "Losa de concreto con malla electrosoldada de 20 cm de espesor, realizada con concreto HM-20/B/20/X0 fabricado en central y vertido desde camión, con malla electrosoldada superior como armadura de reparto ME 20x20 Ø 5-5 B 500 T. Incluye panel de poliestireno expandido de 3 cm para juntas de dilatación.",
         28.35, "m2", "Pisos Exteriores"),
        ("Afirmado / Acabado de concreto aligerado",
         "Afirmado / acabado de hasta 8 cm de espesor, de concreto aligerado de cemento y picón fino, con 115 kg de cemento CEM IV/A-P 32,5 N, confeccionado en obra. Incluye banda de panel rígido de poliestireno expandido para juntas perimetrales de dilatación.",
         28.59, "m2", "Pisos Exteriores"),

        # ── Cielos Rasos ──────────────────────────────────────────────
        ("Cielo raso de tablaroca <3m",
         "Suministro y colocación de cielo raso para una altura de techo de 3 m como máximo. Estructura metálica galvanizada, láminas de tablaroca, cinta y masilla, listo para pintar.",
         42.50, "m2", "Cielos Rasos"),
        ("Cielo raso de tablaroca con iluminación indirecta",
         "Suministro y montaje de cielo raso de tablaroca con estructura metálica galvanizada, bandas perimetrales para iluminación indirecta LED y acabado listo para pintar.",
         42.50, "m2", "Cielos Rasos"),
        ("Falso techo de tablaroca con iluminación indirecta",
         "Suministro y montaje de falso techo de tablaroca con estructura metálica galvanizada, bandas perimetrales para iluminación indirecta LED y acabado listo para pintar.",
         42.50, "m2", "Cielos Rasos"),

        # ── Electricidad ──────────────────────────────────────────────
        ("Instalación eléctrica completa vivienda",
         "Red eléctrica de distribución interior con electrificación elevada: cuadro general de mando y protección, circuitos bajo tubo, mecanismos de gama media-alta y certificación de la instalación.",
         3850.00, "ud", "Electricidad"),
        ("Instalar tomacorriente nuevo",
         "Suministro e instalación de tomacorriente nuevo, incluyendo cableado, caja, tapa y mecanismo. Gama media-alta, color blanco.",
         19.21, "ud", "Electricidad"),
        ("Instalación de mecanismo (tomacorriente)",
         "Instalación de mecanismo de tomacorriente. Incluye mecanismo, tapa y embellecedor en color blanco. Conexión a cableado existente.",
         15.49, "ud", "Electricidad"),
        ("Instalación de mecanismo (interruptor)",
         "Instalación de mecanismo de interruptor sencillo. Incluye mecanismo, tapa y embellecedor en color blanco.",
         14.60, "ud", "Electricidad"),
        ("Instalar punto de luz 10A",
         "Suministro e instalación de punto de luz 10A, incluyendo cableado, caja, mecanismo y tapa blanca.",
         16.74, "ud", "Electricidad"),
        ("Colocación de foco / aplique",
         "Colocación de foco o aplique de pared/techo. Incluye mecanismo, cableado desde caja existente y pruebas de funcionamiento.",
         40.00, "ud", "Electricidad"),
        ("Instalar jack telefónico nuevo",
         "Suministro e instalación de jack telefónico nuevo, incluyendo cableado categoría 3, caja, mecanismo y tapa blanca.",
         36.02, "ud", "Electricidad"),
        ("Instalar jack de antena nuevo",
         "Suministro e instalación de jack de antena de TV nuevo, incluyendo cableado coaxial, caja, mecanismo y tapa blanca.",
         26.90, "ud", "Electricidad"),
        ("Cuadro eléctrico provisional de obra",
         "Suministro e instalación de cuadro eléctrico provisional de obra con protecciones adecuadas para la fase de construcción.",
         985.00, "ud", "Electricidad"),

        # ── Plomería ──────────────────────────────────────────────────
        ("Instalación de plomería para baño completo",
         "Instalación de nuevos puntos de agua fría/caliente en tubería multicapa o PPR con piezas de conexión y material incluido. Incluye: lavabo, inodoro, llaves de corte, desagües en PVC 40mm y bote sifónico.",
         675.00, "ud", "Plomería"),
        ("Instalación de plomería para cocina",
         "Retiro de conexiones antiguas. Instalación de nuevos puntos de agua fría/caliente en tubería PPR con piezas de conexión y material incluido para fregadero, lavaplatos y lavadora. Sustitución de llaves de corte y desagües antiguos por nuevos en PVC sanitario.",
         640.00, "ud", "Plomería"),
        ("Instalación interior para lavadora y termo",
         "Instalación interior de plomería para lavadora con dotación para: lavadero, toma y llave de paso para lavadora, realizada con tubo de polipropileno copolímero random (PP-R), serie 2,5, para la red de agua fría y caliente. Incluye material auxiliar para montaje y sujeción.",
         175.00, "ud", "Plomería"),
        ("Instalación de saneamiento",
         "Instalación de red de saneamiento y desagües en PVC sanitario. Incluye tuberías, accesorios, pegamento, soportes y pruebas de estanqueidad.",
         230.00, "ud", "Plomería"),

        # ── Baños ─────────────────────────────────────────────────────
        ("Revestimiento interior con cerámica gran formato",
         "Revestimiento interior con piezas de gran formato. SOPORTE: paramento de mortero de cemento, vertical, de hasta 3 m de altura. COLOCACIÓN: en capa fina y mediante doble encolado con adhesivo cementoso mejorado C2 TE S1, deformable. JUNTADO: con mortero de juntas cementoso mejorado tipo CG 2 W A, color blanco, en juntas de 3 mm.",
         58.00, "m2", "Baños"),
        ("Enchape de azulejo cerámico gran formato",
         "Revestimiento interior con piezas de gran formato de azulejo cerámico. SOPORTE: paramento de mortero de cemento vertical, de hasta 3 m de altura. COLOCACIÓN: en capa fina y mediante doble encolado con adhesivo cementoso mejorado C2 TE S1. JUNTADO: con mortero de juntas cementoso mejorado tipo CG 2 W A, color blanco, en juntas de 3 mm. No incluye piezas especiales.",
         54.00, "m2", "Baños"),
        ("Instalación de plato / base de ducha",
         "Suministro de plato de ducha, con juego de desagüe. Incluso conexión a la red de evacuación existente, fijación del aparato y sellado con silicona. Totalmente instalado, conexionado, probado y en funcionamiento.",
         324.00, "ud", "Baños"),
        ("Suministro y montaje de kit grifo para ducha",
         "Suministro e instalación de kit grifo para ducha. Incluye pequeño material de conexión.",
         184.00, "ud", "Baños"),
        ("Instalación de inodoro",
         "Suministro, colocación e instalación de inodoro tanque bajo/alto, colocado sobre el piso e instalado, conexionado, probado y en funcionamiento.",
         314.00, "ud", "Baños"),
        ("Instalación de mueble / gabinete de baño",
         "Instalación de mueble de baño. Incluye material necesario para su colocación, fijación a pared y conexión de grifería.",
         300.35, "ud", "Baños"),
        ("Suministro e instalación de mampara",
         "Suministro e instalación de mampara de baño. Incluye perfilería, fijación a paredes y sellado con silicona.",
         317.50, "ud", "Baños"),

        # ── Puertas y Ventanas ────────────────────────────────────────
        ("Puerta de entrada blindada",
         "Montaje y suministro de puerta blindada con hoja de 210 x 91 cm formada por dos chapas de acero lacado inyectadas en su interior de poliuretano de alta densidad con un grosor de 57 mm. Cerco metálico 12 cm. Cerradura de seguridad embutida, 3 puntos de cierre (10 bulones) de doble vuelta. Junta de hermetización, bisagra antipalanca, cilindro de seguridad de cinco llaves, manilla y pomo incluido.",
         700.02, "ud", "Puertas"),
        ("Puerta interior de roble con herrajes ocultos",
         "Suministro e instalación de puerta interior maciza de roble europeo, cerco regulable, bisagras ocultas ajustables en 3D, cerradura magnética y tirador de acero cepillado.",
         760.00, "ud", "Puertas"),
        ("Montaje de puerta corrediza de paso",
         "Instalación de puerta de paso corrediza con remates incluidos. Incluye retirada de antigua puerta, guía superior, embellecedor de guía y ajustes finales.",
         323.89, "ud", "Puertas"),
        ("Balconera practicable de aluminio blanca",
         "Balconera de aluminio practicable color blanca. Perfil de 58 mm, 4 cámaras. Cristal 4/16/4 (ahorro energético). Incluye marco, hoja, herrajes y sellado perimetral.",
         465.00, "ud", "Ventanas"),
        ("Ventana PVC abrible blanca",
         "Ventana de PVC abrible (oscilobatiente) sin persiana. Color blanco. Perfil de 70 mm, 6 cámaras. Cristal 4/16/4i con gas argón. Incluye marco, hoja, herrajes y sellado.",
         392.50, "ud", "Ventanas"),
        ("Ventana de aluminio corrediza blanca",
         "Suministro y montaje de ventana de aluminio corrediza en color blanco. Perfil de 60 mm y cristal 4/8/4 tipo Climalit. Incluye marco, hojas, herrajes, sellado y ajustes.",
         397.50, "ud", "Ventanas"),

        # ── Pintura ───────────────────────────────────────────────────
        ("Pintura premium sobre pañete <3m a pistola",
         "Pintado de paramento vertical/horizontal de cemento o yeso, con pintura con acabado liso (2 capas) + imprimación previa. Sobre paramento interior de hasta 3 m de altura. Pintado profesional con pistola. Incluye reparación de desperfectos en paredes y techos siempre y cuando no sean estructurales.",
         6.90, "m2", "Pintura"),
        ("Pintura premium sobre pañete <3m",
         "Pintado de paramentos con pintura plástica premium acabado mate (2 capas) más imprimación previa. Incluye reparación de desperfectos menores, masilla acrílica y lijado entre manos.",
         8.90, "m2", "Pintura"),

        # ── Carpintería / Muebles ─────────────────────────────────────
        ("Montaje de cocina completa",
         "Montaje de cocina incluyendo mobiliario y electrodomésticos. Incluye montaje y adaptación eléctrica y de plomería donde sea necesario.",
         590.00, "ud", "Carpintería"),
        ("Colocación de mobiliario de cocina",
         "Colocación y ajuste de mobiliario de cocina existente. Incluye nivelación, fijación a paredes, ajuste de puertas y gavetas, y sellado de uniones.",
         690.00, "ml", "Carpintería"),

        # ── Actuaciones Previas / Exteriores ──────────────────────────
        ("Grúa para obra",
         "Alquiler de grúa para maniobras de carga y descarga de materiales pesados en obra. Incluye operador y combustible por jornada.",
         4950.00, "ud", "Actuaciones Previas"),
        ("Excavación de zanjas para zapatas <2m",
         "Excavación de zanjas para zapatas de hasta 2 m de profundidad, con medios mecánicos y manuales. Incluye retiro de material excedente y conformación del fondo.",
         25.00, "m3", "Cimentaciones"),
        ("Forjado sanitario ventilado",
         "Suministro y colocación de forjado sanitario ventilado. Incluye vigas, bovedillas, malla de reparto y concreto de compresión. Sistema que permite ventilación del espacio bajo el piso.",
         34.00, "m2", "Cimentaciones"),
        ("Zapatas aisladas de concreto",
         "Suministro y colocación de zapatas aisladas de concreto armado. Incluye excavación, encofrado, acero de refuerzo, concreto y desencofrado.",
         180.00, "m3", "Cimentaciones"),
    ]



# =========================================================================
# Partidas añadidas a petición del usuario (suelos). Si ya existen con los
# mismos datos no se tocan; si existen con datos distintos se actualizan a
# esta especificación.
# =========================================================================
PARTIDAS_NUEVAS = [
    ("Levantado de pavimento laminado",
     "Levantado de pavimento laminado existente en el interior del edificio, de lamas ensambladas con cola, con medios manuales, sin deteriorar los elementos constructivos contiguos, y carga manual sobre camión o contenedor.",
     5.09, "m2", "Demoliciones"),
    ("Preparación y nivelación suelo existente",
     "Comprobación de baldosa por baldosa hasta encontrar baldosas huecas o con algún daño. Las baldosas con daños deberán levantarse, picar lo necesario y aplicación de mortero estructural hasta nivelar completamente el suelo. Se estima que un 10% del piso está con algún daño. El total final puede variar dependiendo de si es más o menos cantidad.",
     22.50, "ud", "Pisos"),
    ("Solado de baldosas cerámicas en capa fina",
     "Solado de baldosas cerámicas de gres porcelánico, acabado pulido, de hasta 60x120 cm, recibidas con adhesivo cementoso mejorado C2 TE con deslizamiento reducido y tiempo abierto ampliado, con doble encolado y juntadas con mortero de juntas cementoso tipo L para juntas de hasta 3 mm.",
     22.50, "m2", "Pisos"),
    ("Rodapie lacado en blanco",
     "Retirada de rodapié existente, suministro y montaje de rodapié en PVC en color blanco (o color a elegir) mate de 10 cm, fijado con adhesivo de montaje y sellado perimetral con silicona acrílica.",
     7.50, "m", "Pisos"),
    ("Material Cerámico para Suelos",
     "Material Cerámico para pisos. En este caso Porcelanato en tamaño 60x60. El precio puede variar dependiendo del material final elegido.",
     22.50, "ud", "Materiales"),
]


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
    """Siembra inicial del catálogo de partidas (solo una vez).

    Tras la primera siembra se marca ``semilla_catalogo_aplicada`` en la
    configuración. Así, si el usuario borra partidas preinstaladas, no
    reaparecerán en la siguiente actualización/inicio. Las partidas
    existentes nunca se sobrescriben para respetar ediciones del usuario.
    """
    from .models import Configuracion
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
    # Si no hay flag pero la BD está vacía, es instalación fresca: sembrar
    gestionadas_aparte = {t[0] for t in PARTIDAS_NUEVAS}
    for nombre, desc, precio, unidad, categoria in CATALOGO_PARTIDAS:
        if nombre in gestionadas_aparte:
            continue  # se gestionan en PARTIDAS_NUEVAS
        if not db.query(Partida).filter(Partida.nombre == nombre).first():
            db.add(Partida(
                nombre=nombre,
                descripcion=desc,
                precio_unitario=precio,
                unidad=unidad,
                categoria=categoria,
            ))
    # Partidas nuevas: solo crear si no existen, nunca sobrescribir
    for nombre, desc, precio, unidad, categoria in PARTIDAS_NUEVAS:
        if not db.query(Partida).filter(Partida.nombre == nombre).first():
            db.add(Partida(
                nombre=nombre,
                descripcion=desc,
                precio_unitario=precio,
                unidad=unidad,
                categoria=categoria,
            ))
    # Marcar semilla como aplicada
    if cfg is not None:
        cfg.semilla_catalogo_aplicada = True
    else:
        # si no había config (caso raro), crear una mínima
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

