"""Catálogo propio de partidas (basedatos_partidas → app)."""
from __future__ import annotations

import json

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
    NOMBRES_CATALOGO_PRUEBA,
    asegurar_catalogo_propio,
    construir_catalogo,
    disponible,
    migrar_catalogo_prueba_a_propio,
    sembrar_catalogo_propio,
)


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
    assert datos["n_partidas"] == 540
    assert datos["n_recursos"] >= 300
    assert len(datos["categorias"]) == 121
    primera = datos["partidas"][0]
    assert primera["codigo"].startswith("CT-")
    assert primera["categoria"]
    assert primera["subcategoria"]
    filas = json.loads(primera["descomposicion_json"])["filas"]
    assert filas and filas[0]["tipo"] == "recurso"
    assert any(r["codigo"] == "MT-CEMENTO" for r in datos["recursos"])


def test_sembrar_catalogo_carga_propio():
    engine, db = _session()
    try:
        cfg = db.query(Configuracion).first()
        cfg.semilla_catalogo_aplicada = False
        db.commit()

        sembrar_catalogo(db)

        assert db.query(Partida).count() == 540
        assert db.query(Partida).filter(Partida.codigo_interno.like("CT-%")).count() == 540
        assert db.query(Recurso).count() >= 300
        assert db.query(CategoriaPartida).count() == 121
        assert db.query(Configuracion).first().semilla_catalogo_aplicada is True

        # Idempotente al reintentar la carga directa
        r = sembrar_catalogo_propio(db)
        assert r["partidas"] == 0
        assert db.query(Partida).count() == 540
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

        assert db.query(Partida).count() == 41

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
            Partida.codigo_interno.like("CT-%")
        ).count() == 540
        assert db.query(Recurso).filter(Recurso.codigo == "MT-CEMENTO").count() == 1

        # Ya migrado: asegurar no vuelve a hacer trabajo
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
        assert db.query(Partida).count() == 540
        assert db.query(Partida).filter(
            Partida.codigo_interno == "CT-01-01-010"
        ).count() == 1
        assert db.query(Recurso).count() >= 300
    finally:
        db.close()
        engine.dispose()
