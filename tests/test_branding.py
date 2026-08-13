"""Regresiones de identidad, honestidad comercial y compatibilidad de datos."""
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.branding import PRODUCT_NAME, VALUE_PROPOSITION, resolve_data_directory
from app.database import Base
from app.models import Configuracion, asegurar_config


def test_identidad_comercial_aprobada():
    assert PRODUCT_NAME == "CotizaT"
    assert VALUE_PROPOSITION == (
        "Convierte tu catálogo y tus precios en presupuestos de obra claros, "
        "editables y listos para presentar."
    )


def test_instalacion_nueva_usa_directorio_cotizat(tmp_path):
    assert resolve_data_directory(tmp_path) == tmp_path / "CotizaT"


def test_actualizacion_reutiliza_datos_del_directorio_historico(tmp_path):
    legacy = tmp_path / "Presupuestos"
    legacy.mkdir()
    database = legacy / "presupuestos.db"
    database.write_bytes(b"datos-existentes")

    selected = resolve_data_directory(tmp_path)

    assert selected == legacy
    assert database.read_bytes() == b"datos-existentes"
    assert not (tmp_path / "CotizaT").exists()


def test_directorio_cotizat_con_datos_tiene_prioridad(tmp_path):
    legacy = tmp_path / "Presupuestos"
    legacy.mkdir()
    (legacy / "presupuestos.db").touch()
    current = tmp_path / "CotizaT"
    current.mkdir()
    (current / "presupuestos.db").touch()

    assert resolve_data_directory(tmp_path) == current


def test_configuracion_nueva_no_incluye_datos_privados():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    with Session() as db:
        asegurar_config(db)
        cfg = db.query(Configuracion).one()
        assert cfg.empresa_nombre == "Mi Empresa"
        assert cfg.empresa_telefono == ""
        assert cfg.empresa_email == ""
        assert cfg.empresa_web == ""
        assert cfg.empresa_direccion == ""
    engine.dispose()


def test_actualizacion_no_sobrescribe_configuracion_existente():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    with Session() as db:
        original = Configuracion(
            empresa_nombre="Constructora del cliente",
            empresa_email="cliente@example.com",
        )
        db.add(original)
        db.commit()

        asegurar_config(db)
        cfg = db.query(Configuracion).one()
        assert cfg.empresa_nombre == "Constructora del cliente"
        assert cfg.empresa_email == "cliente@example.com"
    engine.dispose()


def test_inicio_renderiza_marca_y_propuesta_honesta():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as client:
        response = client.get("/")
    assert response.status_code == 200
    assert "Dashboard · CotizaT" in response.text
    assert VALUE_PROPOSITION in response.text
    assert "Sugerir desde catálogo" in response.text
    assert "Autogenerar con IA" not in response.text


def test_interfaz_no_repite_claims_descartados_ni_datos_privados():
    archivos = [
        Path("app/templates/base.html"),
        Path("app/templates/index.html"),
        Path("app/templates/budgets/form.html"),
        Path("app/templates/projects/list.html"),
        Path("app/static/js/editor/generador.js"),
        Path("app/models.py"),
        Path("app/seeds.py"),
        Path("instalador.iss"),
    ]
    contenido = "\n".join(p.read_text(encoding="utf-8") for p in archivos).lower()
    for texto_prohibido in (
        "presupuestos pro",
        "autogenerar con ia",
        "gemelos digitales 3d",
        "remodelat",
        "04227997043",
        "contacto@remodelat.net",
    ):
        assert texto_prohibido not in contenido


def test_documento_de_cobro_declara_que_no_es_fiscal():
    detalle = Path("app/templates/facturas/detail.html").read_text(encoding="utf-8")
    pdf = Path("app/services/pdf.py").read_text(encoding="utf-8")
    assert "Documento comercial no fiscal" in detalle
    assert "No sustituye una factura fiscal" in detalle
    assert "DOCUMENTO DE COBRO" in pdf
    assert "No sustituye una factura fiscal" in pdf


def test_instalador_renombrado_conserva_identificador_de_actualizacion():
    instalador = Path("instalador.iss").read_text(encoding="utf-8")
    assert "AppName=CotizaT" in instalador
    assert "Source: \"dist\\CotizaT.exe\"" in instalador
    assert "AppId=Generador de Presupuestos" in instalador
    assert "{app}\\Presupuestos.exe" in instalador
    assert "%LOCALAPPDATA%\\Presupuestos" in instalador
