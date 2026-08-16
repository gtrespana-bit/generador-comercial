"""Primer inicio, elección de contenido y guía hasta el primer PDF."""
import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import (
    Cliente,
    Configuracion,
    Organizacion,
    Partida,
    Presupuesto,
    Producto,
    RecetaEstancia,
    asegurar_config,
)
from app.services.onboarding import (
    ErrorOnboarding,
    completar_onboarding,
    estado_recorrido_inicial,
    marcar_instalacion_anterior,
)


def _session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    return engine, Session()


def _datos_empresa():
    return {
        "empresa_nombre": "Construcciones Prueba",
        "empresa_legal": "Construcciones Prueba C.A.",
        "empresa_rif": "J-00000000-0",
        "empresa_pais": "Venezuela",
        "empresa_ciudad": "Valencia",
        "empresa_direccion": "Zona Industrial",
        "empresa_telefono": "+58 412 000 0000",
        "empresa_email": "prueba@example.com",
        "moneda_default": "USD",
        "iva_default": 16,
    }


def test_modo_limpio_no_inyecta_datos_y_no_se_repite():
    engine, db = _session()
    try:
        cfg = completar_onboarding(db, _datos_empresa(), "limpio")
        assert cfg.onboarding_completado is True
        assert cfg.onboarding_modo == "limpio"
        assert cfg.empresa_ciudad == "Valencia"
        assert db.query(Organizacion).filter_by(slug="espacio-local").count() == 1
        assert db.query(Cliente).count() == 0
        assert db.query(Presupuesto).count() == 0
        assert db.query(Partida).count() == 0
        assert db.query(Producto).count() == 0
        assert db.query(RecetaEstancia).count() == 0
        assert cfg.semilla_catalogo_aplicada is True
        assert cfg.semilla_productos_aplicada is True
        assert cfg.semilla_recetas_aplicada is True
        with pytest.raises(ErrorOnboarding):
            completar_onboarding(db, _datos_empresa(), "demo")
    finally:
        db.close()
        engine.dispose()


def test_modo_demo_crea_contenido_ficticio_identificado():
    engine, db = _session()
    try:
        cfg = completar_onboarding(db, _datos_empresa(), "demo")
        assert cfg.onboarding_completado is True
        assert cfg.onboarding_modo == "demo"
        # Catálogo propio de basedatos_partidas (540 partidas + recursos).
        assert db.query(Partida).count() >= 500
        assert db.query(Partida).filter(Partida.codigo_interno.like("CT-%")).count() >= 500
        assert db.query(Producto).count() >= 3
        assert db.query(RecetaEstancia).count() >= 6
        cliente = db.query(Cliente).one()
        presupuesto = db.query(Presupuesto).one()
        assert cliente.es_demo is True
        assert presupuesto.es_demo is True
        assert presupuesto.cliente is cliente
    finally:
        db.close()
        engine.dispose()


def test_reintento_demo_recupera_un_fallo_parcial_sin_duplicar(monkeypatch):
    engine, db = _session()
    try:
        import app.services.onboarding as servicio

        sembrar_productos_real = servicio.sembrar_productos

        def fallar_una_vez(_db):
            raise RuntimeError("fallo simulado tras sembrar catálogo")

        monkeypatch.setattr(servicio, "sembrar_productos", fallar_una_vez)
        with pytest.raises(RuntimeError, match="fallo simulado"):
            completar_onboarding(db, _datos_empresa(), "demo")
        db.expire_all()
        cfg = db.query(Configuracion).one()
        cantidad_parcial = db.query(Partida).count()
        assert cfg.onboarding_completado is False
        assert cfg.onboarding_modo == "demo"
        assert cantidad_parcial >= 500
        with pytest.raises(ErrorOnboarding, match="misma opción"):
            completar_onboarding(db, _datos_empresa(), "limpio")

        monkeypatch.setattr(servicio, "sembrar_productos", sembrar_productos_real)
        cfg = completar_onboarding(db, _datos_empresa(), "demo")
        assert cfg.onboarding_completado is True
        assert db.query(Partida).count() == cantidad_parcial
        assert db.query(Cliente).count() == 1
        assert db.query(Presupuesto).count() == 1
    finally:
        db.close()
        engine.dispose()


def test_guia_no_cuenta_registros_demo_como_trabajo_real():
    engine, db = _session()
    try:
        cfg = completar_onboarding(db, _datos_empresa(), "demo")
        estado = estado_recorrido_inicial(db, cfg)
        por_clave = {paso["clave"]: paso for paso in estado["pasos"]}
        assert por_clave["empresa"]["completo"] is True
        assert por_clave["cliente"]["completo"] is False
        assert por_clave["presupuesto"]["completo"] is False
        assert por_clave["pdf"]["completo"] is False

        cliente = Cliente(nombre="Cliente real", es_demo=False)
        db.add(cliente)
        db.flush()
        db.add(Presupuesto(
            numero="P-REAL-001",
            year=2026,
            client_id=cliente.id,
            es_demo=False,
        ))
        cfg.onboarding_catalogo_revisado = True
        cfg.onboarding_pdf_descargado = True
        db.commit()

        estado = estado_recorrido_inicial(db, cfg)
        assert estado["completo"] is True
        assert estado["porcentaje"] == 100
    finally:
        db.close()
        engine.dispose()


def test_actualizacion_anterior_no_sobrescribe_empresa_ni_muestra_asistente():
    engine, db = _session()
    try:
        asegurar_config(db)
        cfg = db.query(Configuracion).one()
        cfg.empresa_nombre = "Empresa ya configurada"
        cfg.empresa_email = "existente@example.com"
        db.commit()

        marcar_instalacion_anterior(db)
        db.refresh(cfg)
        assert cfg.onboarding_completado is True
        assert cfg.onboarding_modo == "existente"
        assert cfg.empresa_nombre == "Empresa ya configurada"
        assert cfg.empresa_email == "existente@example.com"
    finally:
        db.close()
        engine.dispose()


def test_base_nueva_sigue_pendiente_tras_dos_arranques(tmp_path):
    """Cerrar antes de completar el wizard no debe saltárselo al reabrir."""
    db_path = tmp_path / "nueva.db"
    script = """
from app.database import SessionLocal, init_db
from app.models import Cliente, Configuracion, Partida, Presupuesto
init_db()
with SessionLocal() as db:
    cfg = db.query(Configuracion).one()
    assert cfg.onboarding_completado is False
    assert db.query(Cliente).count() == 0
    assert db.query(Presupuesto).count() == 0
    assert db.query(Partida).count() == 0
"""
    env = os.environ.copy()
    env["COTIZAT_DB"] = str(db_path)
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
    for _ in range(2):
        resultado = subprocess.run(
            [sys.executable, "-c", script],
            cwd=Path(__file__).resolve().parents[1],
            env=env,
            text=True,
            capture_output=True,
        )
        assert resultado.returncode == 0, resultado.stderr


def test_init_db_reconoce_base_anterior_y_preserva_empresa(tmp_path):
    db_path = tmp_path / "anterior.db"
    old_engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(bind=old_engine)
    OldSession = sessionmaker(bind=old_engine)
    with OldSession() as db:
        db.add(Configuracion(
            empresa_nombre="Empresa Histórica",
            empresa_email="historica@example.com",
        ))
        db.commit()
    with old_engine.begin() as conn:
        conn.execute(text("ALTER TABLE configuracion DROP COLUMN onboarding_completado"))
    old_engine.dispose()

    script = """
from app.database import SessionLocal, init_db
from app.models import Configuracion
init_db()
with SessionLocal() as db:
    cfg = db.query(Configuracion).one()
    assert cfg.onboarding_completado is True
    assert cfg.onboarding_modo == 'existente'
    assert cfg.empresa_nombre == 'Empresa Histórica'
    assert cfg.empresa_email == 'historica@example.com'
"""
    env = os.environ.copy()
    env["COTIZAT_DB"] = str(db_path)
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
    resultado = subprocess.run(
        [sys.executable, "-c", script],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        text=True,
        capture_output=True,
    )
    assert resultado.returncode == 0, resultado.stderr


def test_http_primer_inicio_redirige_y_completa_modo_limpio(tmp_path):
    db_path = tmp_path / "http.db"
    script = """
from fastapi.testclient import TestClient
from app.main import app
with TestClient(app) as client:
    inicio = client.get('/', follow_redirects=False)
    assert inicio.status_code == 303
    assert inicio.headers['location'] == '/bienvenida'
    wizard = client.get('/bienvenida')
    assert wizard.status_code == 200
    assert 'Empezar en limpio' in wizard.text
    from app.database import SessionLocal
    from app.models import Configuracion
    with SessionLocal() as db:
        assert db.query(Configuracion).one().onboarding_iniciado_at is None
    fin = client.post('/bienvenida', data={
        'empresa_nombre': 'Empresa HTTP',
        'empresa_pais': 'Venezuela',
        'empresa_ciudad': 'Valencia',
        'moneda_default': 'USD',
        'iva_default': '16',
        'modo_inicio': 'limpio',
    }, follow_redirects=False)
    assert fin.status_code == 303
    with SessionLocal() as db:
        assert db.query(Configuracion).one().onboarding_iniciado_at is not None
    panel = client.get('/')
    assert panel.status_code == 200
    assert 'Llega a tu primer PDF en cinco pasos' in panel.text
    assert 'action="/recorrido/catalogo-revisado"' in panel.text
    review = client.post('/recorrido/catalogo-revisado', follow_redirects=False)
    assert review.status_code == 303 and review.headers['location'] == '/partidas'
    with SessionLocal() as db:
        assert db.query(Configuracion).one().onboarding_catalogo_revisado is True
"""
    env = os.environ.copy()
    env["COTIZAT_DB"] = str(db_path)
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
    resultado = subprocess.run(
        [sys.executable, "-c", script],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        text=True,
        capture_output=True,
    )
    assert resultado.returncode == 0, resultado.stderr


def test_pdf_demo_y_vista_previa_no_completan_el_ultimo_paso(tmp_path):
    db_path = tmp_path / "pdf.db"
    script = """
from fastapi.testclient import TestClient
from app.database import SessionLocal
from app.main import app
from app.models import Cliente, Configuracion, Presupuesto
with TestClient(app) as client:
    fin = client.post('/bienvenida', data={
        'empresa_nombre': 'Empresa PDF',
        'empresa_pais': 'Venezuela',
        'moneda_default': 'USD',
        'iva_default': '16',
        'modo_inicio': 'demo',
    }, follow_redirects=False)
    assert fin.status_code == 303
    with SessionLocal() as db:
        demo_id = db.query(Presupuesto).filter(Presupuesto.es_demo.is_(True)).one().id
        real_cliente = Cliente(nombre='Cliente real', es_demo=False)
        db.add(real_cliente)
        db.flush()
        real = Presupuesto(numero='P-PDF-001', year=2026, client_id=real_cliente.id, es_demo=False)
        db.add(real)
        db.commit()
        real_id = real.id
    assert client.get(f'/presupuestos/{demo_id}/pdf').status_code == 200
    with SessionLocal() as db:
        assert db.query(Configuracion).one().onboarding_pdf_descargado is False
    assert client.get(f'/presupuestos/{real_id}/pdf?inline=1').status_code == 200
    with SessionLocal() as db:
        assert db.query(Configuracion).one().onboarding_pdf_descargado is False
    assert client.get(f'/presupuestos/{real_id}/pdf').status_code == 200
    with SessionLocal() as db:
        assert db.query(Configuracion).one().onboarding_pdf_descargado is False
    tracked = client.post(f'/presupuestos/{real_id}/pdf-descargado')
    assert tracked.status_code == 200 and tracked.json()['registrado'] is True
    with SessionLocal() as db:
        cfg = db.query(Configuracion).one()
        assert cfg.onboarding_pdf_descargado is True
        assert cfg.primer_pdf_at is not None
"""
    env = os.environ.copy()
    env["COTIZAT_DB"] = str(db_path)
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
    resultado = subprocess.run(
        [sys.executable, "-c", script],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        text=True,
        capture_output=True,
    )
    assert resultado.returncode == 0, resultado.stderr


def test_plantilla_de_bienvenida_explica_ambos_modos():
    contenido = Path("app/templates/onboarding.html").read_text(encoding="utf-8")
    assert "Empezar con un ejemplo" in contenido
    assert "Empezar en limpio" in contenido
    assert "No añade clientes, presupuestos, productos, partidas ni packs" in contenido
    assert "no envía estos datos a un servicio de IA" in contenido
