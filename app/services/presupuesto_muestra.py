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
from . import pdf as pdf_service

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
        notas=(
            NOTA_ILUSTRATIVA
            + "\nIncluye mano de obra especializada, materiales de primera "
            "calidad y gestión integral del proyecto. No incluye enseres, "
            "decoración ni equipos de climatización."
        ),
        condiciones=(
            "Forma de pago: 40% de anticipo para inicio, 35% al 50% de avance "
            "certificado y 25% contra entrega.\n"
            "Plazo estimado de ejecución: 12 semanas desde la firma.\n"
            "Garantía de 12 meses en instalaciones y acabados (ver tabla de "
            "garantías)."
        ),
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


def construir() -> bytes:
    """Construye el presupuesto de muestra y devuelve los bytes del PDF."""
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
        db.add(presupuesto)
        db.commit()
        db.refresh(presupuesto)
        buf = pdf_service.generar_pdf(presupuesto, config)
        return buf.getvalue()
    finally:
        db.close()
        engine.dispose()
