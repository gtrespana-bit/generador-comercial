"""Puntos 10 y 13 de la matriz de aceptación, comprobados sin depender de staging.

El punto 10 exige que una clave de objeto de la Organización A devuelva 404
cuando la pide la Organización B, y el 13 que el bucket no entregue objetos
sin pasar por CotizaT. Ambos se validaban a mano contra Supabase: bastaba con
que alguien olvidara repetir la comprobación tras un cambio en el proxy o en
el aprovisionamiento para que la fuga pasara inadvertida.

Estas pruebas ejercitan el recorrido HTTP completo (petición real con sesión y
organización activa, no una llamada directa a la función) y la configuración
del bucket, de modo que la regresión salte en CI en lugar de en producción.
"""
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import main as main_module
from app import storage
from app.database import Base, get_db
from app.main import app
from app.models import Membresia, Organizacion, Usuario

AUTH_ID_A = "5b1cbe9f-8f0b-4d33-9d0e-3d3e1a6f21aa"
AUTH_ID_B = "9f2d7a41-1c55-4c0e-8f77-2a4b6c8d90bb"


@pytest.fixture
def dos_organizaciones(tmp_path, monkeypatch):
    """Dos empresas reales con su propio usuario, en modo PostgreSQL simulado."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as seed:
        a = Organizacion(nombre="Constructora A", slug="constructora-a")
        b = Organizacion(nombre="Constructora B", slug="constructora-b")
        usuario_a = Usuario(
            auth_user_id=AUTH_ID_A, email="a@example.com", nombre="Ana",
            email_verificado_at=datetime(2026, 8, 13),
        )
        usuario_b = Usuario(
            auth_user_id=AUTH_ID_B, email="b@example.com", nombre="Bruno",
            email_verificado_at=datetime(2026, 8, 13),
        )
        seed.add_all([a, b, usuario_a, usuario_b])
        seed.flush()
        seed.add_all([
            Membresia(usuario_id=usuario_a.id, organizacion_id=a.id, rol="propietario"),
            Membresia(usuario_id=usuario_b.id, organizacion_id=b.id, rol="propietario"),
        ])
        seed.commit()
        ids = a.id, b.id

    backend = storage.LocalStorage(tmp_path / "private")
    monkeypatch.setattr(storage, "get_storage_backend", lambda: backend)
    monkeypatch.setattr(main_module, "get_storage_backend", lambda: backend)
    monkeypatch.setattr(main_module, "DATABASE_IS_SQLITE", False)

    activa = {"organizacion_id": ids[0]}

    def _db_de_la_organizacion_activa():
        db = Session()
        db.info["organizacion_id"] = activa["organizacion_id"]
        db.info["rol_membresia"] = "propietario"
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _db_de_la_organizacion_activa
    try:
        yield Session, ids, activa
    finally:
        app.dependency_overrides.pop(get_db, None)
        engine.dispose()


def _cliente():
    return TestClient(app, base_url="https://cotizat.test")


def test_punto_10_un_objeto_de_a_devuelve_404_para_b(dos_organizaciones):
    """Recorrido HTTP: la clave exacta de A no se entrega bajo la sesión de B."""
    Session, (org_a, org_b), activa = dos_organizaciones
    with Session() as db:
        db.info["organizacion_id"] = org_a
        guardado = storage.save_object(
            db, b"%PDF-1.4 planos privados de A", "anexos",
            "planos.pdf", "application/pdf",
        )
        db.commit()

    url = storage.file_url(guardado.reference)
    assert url == "/archivos/" + guardado.object_key

    with _cliente() as client:
        propia = client.get(url)
        assert propia.status_code == 200
        assert propia.content == b"%PDF-1.4 planos privados de A"

        # La misma URL, exacta, con la organización B activa.
        activa["organizacion_id"] = org_b
        ajena = client.get(url)

    assert ajena.status_code == 404
    assert b"planos privados" not in ajena.content


def test_punto_10_b_no_alcanza_el_objeto_de_a_manipulando_la_clave(dos_organizaciones):
    """Ni reescribiendo el identificador ni escapando del prefijo del tenant."""
    Session, (org_a, org_b), activa = dos_organizaciones
    with Session() as db:
        db.info["organizacion_id"] = org_a
        guardado = storage.save_object(
            db, b"contrato de A", "anexos", "contrato.pdf", "application/pdf",
        )
        db.commit()
    cola = guardado.object_key.split("/", 2)[2]

    activa["organizacion_id"] = org_b
    intentos = [
        f"/archivos/organizaciones/{org_a}/{cola}",
        f"/archivos/organizaciones/{org_b}/../organizaciones/{org_a}/{cola}",
        f"/archivos/organizaciones/{org_b}%2f..%2forganizaciones%2f{org_a}/{cola}",
        f"/archivos/organizaciones/0{org_a}/{cola}",
        f"/archivos/organizaciones/{org_a}/{cola}?download=1",
    ]
    with _cliente() as client:
        respuestas = [client.get(intento) for intento in intentos]

    for intento, respuesta in zip(intentos, respuestas):
        assert respuesta.status_code == 404, intento
        assert b"contrato de A" not in respuesta.content, intento


def test_punto_10_el_metadato_de_a_no_aparece_en_las_consultas_de_b(dos_organizaciones):
    """El 404 no depende solo del proxy: el registro tampoco es visible."""
    from app.models import ArchivoAlmacenado

    Session, (org_a, org_b), _activa = dos_organizaciones
    with Session() as db:
        db.info["organizacion_id"] = org_a
        storage.save_object(
            db, b"ficha de A", "fichas-tecnicas", "ficha.pdf", "application/pdf",
        )
        db.commit()

    with Session() as db:
        db.info["organizacion_id"] = org_b
        assert db.query(ArchivoAlmacenado).all() == []


def test_punto_13_el_bucket_se_aprovisiona_privado_y_sin_lectura_anonima():
    """El bucket nunca se declara público: la frontera es el proxy de CotizaT."""
    import inspect as inspeccion

    fuente = inspeccion.getsource(storage.SupabaseStorage.create_private_bucket)
    assert '"public": False' in fuente
    assert "True" not in fuente.split('"public"')[1].split(",")[0]

    from app.tools import ensure_bucket

    verificacion = inspeccion.getsource(ensure_bucket.main)
    # Si el bucket existiera y fuese público, el aprovisionamiento debe fallar.
    assert 'status.get("public") is not False' in verificacion


def test_punto_13_supabase_nunca_expone_una_url_publica_del_objeto(tmp_path):
    """Ninguna ruta de CotizaT construye enlaces a supabase.co para el navegador."""
    settings = storage.StorageSettings(
        backend="supabase", local_root=tmp_path,
        supabase_url="https://ejemplo.supabase.co",
        secret_key="sb_secret_prueba-no-real", bucket="cotizat-private",
    )
    backend = storage.SupabaseStorage(settings)
    assert not hasattr(backend, "public_url")
    assert not hasattr(backend, "signed_url")

    referencia = "storage://organizaciones/1/anexos/planos.pdf"
    url = storage.file_url(referencia)
    assert url.startswith("/archivos/")
    assert "supabase.co" not in url
    assert "/object/public/" not in url


def test_punto_13_ninguna_plantilla_enlaza_al_almacenamiento_remoto():
    """Regresión: una plantilla con la URL del bucket saltaría el proxy."""
    from pathlib import Path

    raiz = Path(__file__).resolve().parents[1] / "app"
    sospechosas = []
    for archivo in list(raiz.rglob("*.html")) + list(raiz.rglob("*.js")):
        texto = archivo.read_text(encoding="utf-8", errors="ignore")
        if "supabase.co/storage" in texto or "/object/public/" in texto:
            sospechosas.append(str(archivo.relative_to(raiz)))
    assert not sospechosas, sospechosas
