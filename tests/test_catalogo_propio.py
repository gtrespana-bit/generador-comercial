"""Catálogo propio de partidas (basedatos_partidas → app)."""
from __future__ import annotations

import json
import re

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import (
    CategoriaPartida,
    Configuracion,
    Partida,
    Recurso,
    asegurar_config,
)
from app.seeds import sembrar_catalogo
from app.services.catalogo_propio import (
    CATALOGO_VERSION,
    NOMBRES_CATALOGO_PRUEBA,
    actualizar_taxonomia_catalogo_propio,
    asegurar_catalogo_propio,
    construir_catalogo,
    disponible,
    migrar_catalogo_prueba_a_propio,
    sembrar_catalogo_propio,
)


# La ampliación del catálogo extenso (lotes de producción) hace crecer estas
# cifras. Se centralizan aquí para actualizarlas en un solo punto en cada lote.
N_PARTIDAS = 717       # total de partidas oficiales del catálogo
N_LEGACY = 540         # partidas migradas de la v1 con código CT- (no crece)
N_APARTADOS = 161      # apartados de tercer nivel con partidas
N_CATEGORIAS = 18 + 172 + N_APARTADOS


def _session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    asegurar_config(db)
    return engine, db


def test_catalogo_propio_disponible_y_completo():
    assert disponible()
    datos = construir_catalogo()
    assert datos["ok"]
    assert datos["n_partidas"] == N_PARTIDAS
    assert datos["n_recursos"] >= 300
    assert len([c for c in datos["categorias"] if c["nivel"] == 1]) == 18
    assert len([c for c in datos["categorias"] if c["nivel"] == 2]) == 172
    assert len([c for c in datos["categorias"] if c["nivel"] == 3]) == N_APARTADOS

    primera = datos["partidas"][0]
    assert re.fullmatch(r"\d{2}\.\d{2}\.\d{2}\.\d{3}", primera["codigo"])
    assert primera["codigo_legacy"].startswith("CT-")
    assert primera["categoria"].startswith("01 ")
    assert primera["subcategoria"].startswith("01.")
    assert primera["apartado"].startswith("01.")
    filas = json.loads(primera["descomposicion_json"])["filas"]
    assert filas and filas[0]["tipo"] == "recurso"
    assert any(r["codigo"] == "MT-CEMENTO" for r in datos["recursos"])


def test_catalogo_masivo_conserva_codigo_y_tres_niveles():
    from pathlib import Path
    from app.services import importer

    datos = Path("basedatos_partidas/salida/catalogo_partidas.csv").read_bytes()
    matriz = importer.leer_csv(datos)
    analisis = importer.analizar_matriz(matriz, tiene_encabezados=True)
    mapeo = importer.detectar_mapeo(analisis["encabezados"])
    resultado = importer.validar_filas(analisis["filas"], mapeo)
    assert not resultado["errores"]
    assert not resultado["advertencias"]
    assert len(resultado["filas"]) == N_PARTIDAS
    primera = resultado["filas"][0]
    assert re.fullmatch(r"\d{2}\.\d{2}\.\d{2}\.\d{3}", primera["codigo"])
    assert primera["codigo_legacy"].startswith("CT-")
    assert primera["categoria"].startswith("01 ")
    assert primera["subcategoria"].startswith("01.")
    assert primera["apartado"].startswith("01.")


def test_descompuesto_generado_conserva_los_tres_niveles():
    from pathlib import Path
    from app.services.importer import analizar_cype_xlsx

    ruta = next(Path("basedatos_partidas/salida/descompuestos").glob("*.xlsx"))
    partida = analizar_cype_xlsx(ruta.read_bytes())["partidas"][0]
    assert partida["codigo"] == ruta.stem
    assert partida["capitulo"].startswith(ruta.stem[:2] + " ")
    assert partida["subcapitulo"].startswith(ruta.stem[:5] + " ")
    assert partida["apartado"].startswith(ruta.stem[:8] + " ")


def test_sembrar_catalogo_carga_arbol_numerico_completo():
    engine, db = _session()
    try:
        cfg = db.query(Configuracion).first()
        cfg.semilla_catalogo_aplicada = False
        db.commit()

        sembrar_catalogo(db)

        assert db.query(Partida).count() == N_PARTIDAS
        assert db.query(Partida).filter(
            Partida.version_catalogo == CATALOGO_VERSION
        ).count() == N_PARTIDAS
        assert db.query(Partida).filter(Partida.codigo_legacy.like("CT-%")).count() == N_LEGACY
        assert db.query(Partida).filter(Partida.es_oficial.is_(True)).count() == N_PARTIDAS
        assert db.query(Partida).filter(Partida.catalogo_uid.isnot(None)).count() == N_PARTIDAS
        assert db.query(Partida).filter(Partida.oculta.is_(True)).count() == 0
        assert db.query(Recurso).count() >= 300
        assert db.query(CategoriaPartida).filter_by(nivel=1, oficial=True).count() == 18
        assert db.query(CategoriaPartida).filter_by(nivel=2, oficial=True).count() == 172
        assert db.query(CategoriaPartida).filter_by(nivel=3, oficial=True).count() == N_APARTADOS
        assert db.query(Partida).filter(Partida.categoria_id.is_(None)).count() == 0
        cfg = db.query(Configuracion).first()
        assert cfg.semilla_catalogo_aplicada is True
        assert cfg.version_catalogo == CATALOGO_VERSION

        # Idempotente al reintentar la carga directa.
        r = sembrar_catalogo_propio(db)
        assert r["partidas"] == 0
        assert db.query(Partida).count() == N_PARTIDAS
        assert db.query(CategoriaPartida).count() == N_CATEGORIAS
    finally:
        db.close()
        engine.dispose()


def test_actualizar_v1_conserva_id_precio_borrados_y_partidas_del_usuario():
    engine, db = _session()
    try:
        fuente = construir_catalogo()["partidas"][0]
        oficial = Partida(
            nombre=fuente["nombre"],
            precio_unitario=987.65,  # ajuste local que no debe sobrescribirse
            unidad=fuente["unidad"],
            categoria="Categoría v1",
            subcategoria="Subcategoría v1",
            codigo_interno=fuente["codigo_legacy"],
            codigo_externo=fuente["codigo_legacy"],
            descomposicion_json=json.dumps({
                "codigo": fuente["codigo_legacy"],
                "filas": [{"tipo": "recurso", "codigo": "LOCAL"}],
            }),
        )
        particular = Partida(
            nombre="Partida hecha por el usuario",
            precio_unitario=50,
            categoria="Mía",
        )
        db.add_all([oficial, particular])
        db.commit()
        id_anterior = oficial.id

        resultado = actualizar_taxonomia_catalogo_propio(db)

        assert resultado["actualizadas"] == 1
        migrada = db.get(Partida, id_anterior)
        assert migrada is oficial
        assert migrada.precio_unitario == 987.65
        assert migrada.codigo_interno == fuente["codigo"]
        assert migrada.codigo_legacy == fuente["codigo_legacy"]
        assert migrada.catalogo_uid == fuente["catalogo_uid"]
        assert migrada.es_oficial is True
        assert migrada.version_alta_catalogo == 2
        assert migrada.apartado == fuente["apartado"]
        assert migrada.categoria_id is not None
        descomp = json.loads(migrada.descomposicion_json)
        assert descomp["codigo"] == fuente["codigo"]
        assert descomp["filas"][0]["codigo"] == "LOCAL"
        migrada.oculta = True
        db.commit()
        actualizar_taxonomia_catalogo_propio(db)
        assert db.get(Partida, id_anterior).oculta is True
        # No reaparecen las otras 539 oficiales que no estaban en la BD.
        assert db.query(Partida).count() == 2
        assert particular.codigo_interno == ""
        assert particular.categoria == "Mía"
    finally:
        db.close()
        engine.dispose()


def test_asegurar_actualiza_catalogo_v1_grande_una_sola_vez():
    engine, db = _session()
    try:
        fuentes = construir_catalogo()["partidas"][:100]
        for item in fuentes:
            db.add(Partida(
                nombre=item["nombre"],
                precio_unitario=item["precio_unitario"],
                unidad=item["unidad"],
                categoria="v1",
                subcategoria="v1",
                codigo_interno=item["codigo_legacy"],
                codigo_externo=item["codigo_legacy"],
            ))
        db.commit()

        resultado = asegurar_catalogo_propio(db)
        assert resultado["actualizadas"] == 100
        assert db.query(Partida).filter(
            Partida.version_catalogo == CATALOGO_VERSION
        ).count() == 100
        assert db.query(Partida).filter(
            Partida.codigo_interno.like("CT-%")
        ).count() == 0
        assert db.query(Configuracion).one().version_catalogo == CATALOGO_VERSION
        assert asegurar_catalogo_propio(db) is None
    finally:
        db.close()
        engine.dispose()


def test_actualizacion_incremental_incorpora_nuevas_y_respeta_ocultas(monkeypatch):
    import app.services.catalogo_propio as servicio

    engine, db = _session()
    try:
        sembrar_catalogo_propio(db)
        oculta = db.query(Partida).filter(Partida.es_oficial.is_(True)).first()
        oculta.oculta = True
        db.commit()

        base = construir_catalogo()
        nueva = dict(base["partidas"][0])
        nueva.update({
            "catalogo_uid": "COTIZAT-V3-PRUEBA-001",
            "codigo": "01.02.01.990",
            "codigo_legacy": "",
            "nombre": "Partida oficial incorporada en versión 3",
            "version_alta_catalogo": 3,
        })
        fake = {**base, "partidas": [*base["partidas"], nueva], "n_partidas": 541}
        monkeypatch.setattr(servicio, "CATALOGO_VERSION", 3)
        monkeypatch.setattr(servicio, "construir_catalogo", lambda: fake)

        resultado = servicio.actualizar_taxonomia_catalogo_propio(db)
        assert resultado["incorporadas"] == 1
        creada = db.query(Partida).filter_by(
            catalogo_uid="COTIZAT-V3-PRUEBA-001"
        ).one()
        assert creada.es_oficial is True
        assert creada.oculta is False
        assert creada.version_alta_catalogo == 3
        assert db.get(Partida, oculta.id).oculta is True
        assert db.query(Configuracion).one().version_catalogo == 3

        # Reintentar la misma versión no duplica ni reactiva nada.
        segundo = servicio.actualizar_taxonomia_catalogo_propio(db)
        assert segundo["incorporadas"] == 0
        assert db.query(Partida).filter_by(
            catalogo_uid="COTIZAT-V3-PRUEBA-001"
        ).count() == 1
        assert db.get(Partida, oculta.id).oculta is True
    finally:
        db.close()
        engine.dispose()


def test_migrar_catalogo_prueba_elimina_antiguas_y_carga_propias():
    engine, db = _session()
    try:
        for nombre in list(NOMBRES_CATALOGO_PRUEBA)[:40]:
            db.add(Partida(
                nombre=nombre, precio_unitario=10.0, unidad="m2", categoria="Test",
            ))
        db.add(Partida(
            nombre="Partida hecha por el usuario",
            precio_unitario=50.0, unidad="ud", categoria="Mia",
        ))
        cfg = db.query(Configuracion).first()
        cfg.semilla_catalogo_aplicada = True
        db.commit()

        resultado = migrar_catalogo_prueba_a_propio(db)
        assert resultado["ok"]
        assert resultado["partidas_prueba_eliminadas"] == 40
        assert db.query(Partida).filter(
            Partida.nombre == "Partida hecha por el usuario"
        ).count() == 1
        assert db.query(Partida).filter(
            Partida.nombre.in_(NOMBRES_CATALOGO_PRUEBA)
        ).count() == 0
        assert db.query(Partida).filter(
            Partida.version_catalogo == CATALOGO_VERSION
        ).count() == N_PARTIDAS
        assert db.query(Recurso).filter(Recurso.codigo == "MT-CEMENTO").count() == 1

        # Ya migrado: asegurar no vuelve a hacer trabajo.
        assert asegurar_catalogo_propio(db) is None
    finally:
        db.close()
        engine.dispose()


def test_asegurar_no_toca_instalacion_limpia():
    engine, db = _session()
    try:
        assert db.query(Partida).count() == 0
        assert asegurar_catalogo_propio(db) is None
        assert db.query(Partida).count() == 0
    finally:
        db.close()
        engine.dispose()


def test_modo_demo_carga_catalogo_propio():
    from app.services.onboarding import completar_onboarding

    engine, db = _session()
    try:
        completar_onboarding(db, {
            "empresa_nombre": "Constructora Catálogo",
            "moneda_default": "USD",
            "iva_default": 16,
        }, "demo")
        assert db.query(Partida).count() == N_PARTIDAS
        assert db.query(Partida).filter(
            Partida.codigo_legacy == "CT-01-01-010"
        ).count() == 1
        assert db.query(Recurso).count() >= 300
    finally:
        db.close()
        engine.dispose()
