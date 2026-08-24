"""Tests de humo para el nuevo flujo de planos: grosor, plano en blanco,
detección vectorial y selector de mediciones. Garantiza que la lógica
introducida en este cambio no rompe los flujos previos y que las nuevas
funciones se exponen como se espera.
"""
from __future__ import annotations

import io
from datetime import date

import pytest
from PIL import Image, ImageDraw

from app.database import SessionLocal, init_db
from app.models import (
    Cliente,
    Configuracion,
    PlanoElemento,
    PlanoMedicion,
    PlanoObra,
    Presupuesto,
    asegurar_config,
    asegurar_organizacion_local,
)
from app.services.planos import (
    GROSOR_TABIQUE_DEFECTO_CM,
    actualizar_grosor_tabique,
    crear_plano_en_blanco,
    crear_plano,
    detectar_espacios_plano,
    detectar_estancias_sobre_dibujo,
    guardar_detecciones_sobre_dibujo,
    guardar_elemento,
    grosor_px_plano,
    metricas_estancia,
)


@pytest.fixture()
def db():
    init_db()
    with SessionLocal() as s:
        s.info["organizacion_id"] = 1
        org = asegurar_organizacion_local(s)
        s.info["organizacion_id"] = org.id
        cfg = asegurar_config(s)
        s.commit()
        yield s
        s.rollback()


@pytest.fixture()
def presupuesto(db):
    import uuid
    sufijo = uuid.uuid4().hex[:8]
    cliente = Cliente(nombre=f"Test cliente {sufijo}")
    db.add(cliente)
    db.flush()
    p = Presupuesto(
        numero=f"P-TEST-{sufijo}",
        year=2026,
        fecha=date.today(),
        titulo="Test",
        client_id=cliente.id,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def _png_plano_minimo():
    img = Image.new("RGB", (320, 240), "white")
    d = ImageDraw.Draw(img)
    # Cuadrado cerrado: simulamos una habitación.
    d.rectangle([60, 60, 260, 180], outline="black", width=6)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_grosor_por_defecto_en_plano_subido(db, presupuesto):
    contenido = _png_plano_minimo()
    plano = crear_plano(db, presupuesto_id=presupuesto.id, nombre="Test", archivo_nombre="p.png", contenido=contenido)
    assert plano.grosor_tabique_cm == pytest.approx(GROSOR_TABIQUE_DEFECTO_CM)
    assert plano.origen == "subido"


def test_actualizar_grosor_tabique_acepta_valor_y_lo_redondea(db, presupuesto):
    contenido = _png_plano_minimo()
    plano = crear_plano(db, presupuesto_id=presupuesto.id, nombre="Test", archivo_nombre="p.png", contenido=contenido)
    actualizar_grosor_tabique(db, plano, 15)
    assert plano.grosor_tabique_cm == 15
    assert plano.grosor_tabique_m == pytest.approx(0.15)


def test_actualizar_grosor_tabique_rechaza_valores_absurdos(db, presupuesto):
    contenido = _png_plano_minimo()
    plano = crear_plano(db, presupuesto_id=presupuesto.id, nombre="Test", archivo_nombre="p.png", contenido=contenido)
    actualizar_grosor_tabique(db, plano, -5)
    assert plano.grosor_tabique_cm == GROSOR_TABIQUE_DEFECTO_CM
    actualizar_grosor_tabique(db, plano, 999)
    assert plano.grosor_tabique_cm == GROSOR_TABIQUE_DEFECTO_CM


def test_crear_plano_en_blanco_devuelve_vectorial(db, presupuesto):
    plano = crear_plano_en_blanco(db, presupuesto_id=presupuesto.id, nombre="Mi plano", ancho_lienzo_m=10, alto_lienzo_m=6, grosor_tabique_cm=12)
    assert plano.origen == "dibujado"
    assert plano.grosor_tabique_cm == 12
    assert plano.ancho_lienzo_m == 10
    assert plano.alto_lienzo_m == 6
    assert plano.archivo == ""
    assert plano.content_type == "image/svg+xml"


def test_grosor_px_sin_calibrar_es_por_defecto(db, presupuesto):
    plano = crear_plano_en_blanco(db, presupuesto_id=presupuesto.id, nombre="p", ancho_lienzo_m=8, alto_lienzo_m=5, grosor_tabique_cm=10)
    # Sin escala, devuelve un valor utilizable.
    assert grosor_px_plano(plano) >= 1.0


def test_metricas_estancia_incluye_grosor(db, presupuesto):
    puntos = [[0, 0], [10, 0], [10, 10], [0, 10]]
    m = metricas_estancia(puntos, escala_px_por_m=100.0, altura_m=2.5, grosor_tabique_m=0.10)
    assert m["calibrado"] is True
    assert m["suelo_unidad"] == "m2"
    assert m["altura_m"] == 2.5
    assert m["grosor_tabique_m"] == pytest.approx(0.10)


def test_detectar_espacios_plano_no_falla_con_grosor_explicito(db, presupuesto):
    contenido = _png_plano_minimo()
    candidatos = detectar_espacios_plano(contenido, "image/png", max_espacios=10, grosor_tabique_px=12.0)
    assert isinstance(candidatos, list)


def test_dibujo_y_deteccion_vectorial_basica(db, presupuesto):
    plano = crear_plano_en_blanco(db, presupuesto_id=presupuesto.id, nombre="dibujo", ancho_lienzo_m=8, alto_lienzo_m=6, grosor_tabique_cm=10)
    # Creamos 4 muros en cuadrado cerrado (escala interna 100 px/m).
    guardar_elemento(db, plano, "muro", [[100, 100], [400, 100]], grosor_cm=10)
    guardar_elemento(db, plano, "muro", [[400, 100], [400, 400]], grosor_cm=10)
    guardar_elemento(db, plano, "muro", [[400, 400], [100, 400]], grosor_cm=10)
    guardar_elemento(db, plano, "muro", [[100, 400], [100, 100]], grosor_cm=10)
    db.refresh(plano)

    candidatos = detectar_estancias_sobre_dibujo(plano)
    # Una única estancia, pegada a la cara interior de los muros de 10 cm.
    assert len(candidatos) == 1
    poligono = candidatos[0]["puntos"]
    assert abs(candidatos[0]["area_px2"] - 290 * 290) < 2.0
    assert min(p[0] for p in poligono) == pytest.approx(105.0)
    assert max(p[0] for p in poligono) == pytest.approx(395.0)
    assert min(p[1] for p in poligono) == pytest.approx(105.0)
    assert max(p[1] for p in poligono) == pytest.approx(395.0)

    creadas, omitidas = guardar_detecciones_sobre_dibujo(db, plano, candidatos)
    assert len(creadas) == 1
    assert omitidas == 0
    # Volver a detectar no duplica la estancia.
    creadas2, omitidas2 = guardar_detecciones_sobre_dibujo(db, plano, candidatos)
    assert creadas2 == []
    assert omitidas2 == 1


def test_dibujo_en_cruz_detecta_cuatro_estancias(db, presupuesto):
    plano = crear_plano_en_blanco(db, presupuesto_id=presupuesto.id, nombre="cruz", ancho_lienzo_m=10, alto_lienzo_m=8, grosor_tabique_cm=10)
    guardar_elemento(db, plano, "muro", [[100, 100], [900, 100]], grosor_cm=10)
    guardar_elemento(db, plano, "muro", [[900, 100], [900, 700]], grosor_cm=10)
    guardar_elemento(db, plano, "muro", [[900, 700], [100, 700]], grosor_cm=10)
    guardar_elemento(db, plano, "muro", [[100, 700], [100, 100]], grosor_cm=10)
    guardar_elemento(db, plano, "muro", [[500, 100], [500, 700]], grosor_cm=10)
    guardar_elemento(db, plano, "muro", [[100, 400], [900, 400]], grosor_cm=10)
    db.refresh(plano)

    candidatos = detectar_estancias_sobre_dibujo(plano)
    assert len(candidatos) == 4
    # Cada estancia mide (500-100-10) x (400-100-10) = 390 x 290 px.
    assert all(abs(c["area_px2"] - 390 * 290) < 2.0 for c in candidatos)
