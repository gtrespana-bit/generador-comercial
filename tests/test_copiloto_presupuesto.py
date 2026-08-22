"""Pruebas de las cuatro herramientas deterministas del copiloto."""
import pytest

from app.models import Base, Configuracion, Organizacion, Partida
from app.services.copiloto_presupuesto import (
    calcular_mediciones_texto,
    detectar_faltantes_alcance,
    preparar_lote_catalogo,
    revisar_borrador_vivo,
)
from app.services.herramientas_ia import resolver_herramienta_ia


def _db(tmp_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(f"sqlite:///{tmp_path}/copiloto.db")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    db.info["organizacion_id"] = 1
    db.add(Organizacion(id=1, nombre="Empresa", slug="empresa"))
    db.add(Configuracion(organizacion_id=1, empresa_nombre="Empresa", moneda_default="USD"))
    db.commit()
    return db


def test_revision_borrador_vivo_detecta_problemas_sin_persistir():
    borrador = [
        {
            "nombre": "DEMOLICIONES",
            "partidas": [
                {
                    "nombre": "Demolición de piso",
                    "unidad": "m2",
                    "cantidad": 10,
                    "precio": 0,
                    "mediciones": [{"concepto": "Baño", "cantidad": 6}],
                    "coste_materiales": 2,
                    "prod_nombre": "Producto demo",
                    "prod_precio": 5,
                    "prod_coste": "",
                },
                {
                    "nombre": "Demolición de piso",
                    "unidad": "unidad-rara",
                    "cantidad": 1,
                    "precio": 1,
                    "coste_mano_obra": 3,
                },
            ],
        },
        {"nombre": "", "partidas": []},
    ]

    revision = revisar_borrador_vivo(borrador)
    codigos_criticos = {item["codigo"] for item in revision["criticos"]}
    codigos_avisos = {item["codigo"] for item in revision["avisos"]}

    assert revision["estado"] == "riesgo"
    assert revision["total_capitulos"] == 2
    assert revision["total_partidas"] == 2
    assert {"sin_precio", "margen_negativo", "capitulo_sin_nombre"}.issubset(codigos_criticos)
    assert {
        "cantidad_mediciones_difiere", "producto_sin_coste", "partida_duplicada",
        "unidad_inusual", "capitulo_vacio",
    }.issubset(codigos_avisos)
    assert revision["score"] < 100


def test_calculo_mediciones_rectangulo_aberturas_y_desperdicio():
    calculo = calcular_mediciones_texto(
        "El baño mide 3 × 2 m, tiene 2,40 m de altura, una puerta de "
        "0,80 × 2,10 m y 10% de desperdicio"
    )
    assert calculo["ok"] is True
    filas = {fila["tipo"]: fila for fila in calculo["filas"]}
    assert filas["piso"]["cantidad"] == pytest.approx(6.0)
    assert filas["rodapie"]["cantidad"] == pytest.approx(9.2)
    assert filas["pared"]["cantidad"] == pytest.approx(22.32)
    assert filas["piso_desperdicio"]["cantidad"] == pytest.approx(6.6)
    assert filas["pared_desperdicio"]["cantidad"] == pytest.approx(24.55)
    assert calculo["descuento_aberturas"] == pytest.approx(1.68)


def test_calculo_mediciones_pide_dimensiones_si_no_las_encuentra():
    resultado = calcular_mediciones_texto("Calcula las paredes del baño")
    assert resultado["ok"] is False
    assert "largo × ancho" in resultado["error"]


def test_preparar_lote_usa_catalogo_y_excluye_partida_existente(tmp_path):
    db = _db(tmp_path)
    nombres = [
        ("PRO-01", "Protección de elementos existentes"),
        ("DEM-01", "Demolición de piso de porcelanato"),
        ("DEM-02", "Picado de pared de porcelanato"),
        ("RES-01", "Acopio de escombros"),
        ("RES-02", "Transporte de escombros"),
    ]
    for codigo, nombre in nombres:
        db.add(Partida(
            organizacion_id=1,
            codigo_interno=codigo,
            nombre=nombre,
            descripcion=nombre,
            unidad="m2",
            precio_unitario=5,
        ))
    db.commit()
    existente = db.query(Partida).filter(Partida.codigo_interno == "DEM-01").one()
    borrador = [{
        "nombre": "DEMOLICIONES",
        "partidas": [{"catalogo_id": existente.id, "nombre": existente.nombre}],
    }]

    lote = preparar_lote_catalogo(
        db,
        "Prepara las partidas necesarias para demolicion de porcelanato",
        borrador,
    )
    codigos = {partida["codigo"] for partida in lote["candidatos"]}
    assert lote["flujo_reconocido"] is True
    assert "DEM-01" not in codigos
    assert {"PRO-01", "DEM-02", "RES-01", "RES-02"}.issubset(codigos)


def test_detector_alcance_propone_partidas_reales(tmp_path):
    db = _db(tmp_path)
    db.add_all([
        Partida(
            organizacion_id=1,
            codigo_interno="SOP-01",
            nombre="Regularización de soporte de piso",
            descripcion="Regularización y nivelación del soporte de piso.",
            unidad="m2",
            precio_unitario=4,
        ),
        Partida(
            organizacion_id=1,
            codigo_interno="IMP-01",
            nombre="Impermeabilización de zona húmeda",
            descripcion="Impermeabilización de zona húmeda en baño.",
            unidad="m2",
            precio_unitario=6,
        ),
    ])
    db.commit()
    borrador = [{
        "nombre": "BAÑO PRINCIPAL",
        "partidas": [{
            "nombre": "Colocación de porcelanato en piso",
            "descripcion": "Colocación de piezas con adhesivo.",
            "unidad": "m2",
            "cantidad": 6,
            "precio": 12,
        }],
    }]

    resultado = detectar_faltantes_alcance(db, borrador)
    claves = {item["clave"] for item in resultado["sugerencias"]}
    codigos = {
        partida["codigo"]
        for item in resultado["sugerencias"]
        for partida in item["partidas"]
    }
    assert {"soporte", "impermeabilizacion"}.issubset(claves)
    assert {"SOP-01", "IMP-01"}.issubset(codigos)
    assert len(resultado["ids_recomendados"]) == 2


def test_chat_resuelve_las_cuatro_herramientas_con_acciones(tmp_path):
    db = _db(tmp_path)
    db.add_all([
        Partida(
            organizacion_id=1,
            codigo_interno="DEM-01",
            nombre="Demolición de piso de porcelanato",
            descripcion="Demolición de piso porcelanato.",
            unidad="m2",
            precio_unitario=5,
        ),
        Partida(
            organizacion_id=1,
            codigo_interno="RES-01",
            nombre="Transporte de escombros",
            descripcion="Transporte de escombros.",
            unidad="m3",
            precio_unitario=8,
        ),
    ])
    db.commit()
    contexto = {
        "pagina": "/presupuestos/9/editar",
        "presupuesto_id": 9,
        "borrador": [{
            "nombre": "DEMOLICIONES",
            "partidas": [{
                "nombre": "Demolición de piso de porcelanato",
                "unidad": "m2", "cantidad": 0, "precio": 0,
            }],
        }],
    }

    revision = resolver_herramienta_ia(db, "Revisa este presupuesto", contexto)
    medicion = resolver_herramienta_ia(
        db, "El baño mide 3 x 2 m y tiene 2,4 m de altura", contexto
    )
    lote = resolver_herramienta_ia(
        db, "Prepara las partidas necesarias para demolicion de porcelanato", contexto
    )
    faltantes = resolver_herramienta_ia(db, "¿Qué falta en el alcance?", contexto)

    assert "borrador visible" in revision
    assert "/api/ia/accion/enfocar-borrador" in revision
    assert "Mediciones calculadas" in medicion
    assert "/api/ia/accion/aplicar-medicion" in medicion
    assert "Lote preparado" in lote or "No encontré partidas nuevas" in lote
    assert "alcance" in faltantes.lower()
