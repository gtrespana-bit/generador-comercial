import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app import storage
from app.database import Base
from app.models import ArchivoAlmacenado, Organizacion, Producto


@pytest.fixture()
def tenant_db(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'storage.db'}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as db:
        db.add_all([
            Organizacion(id=1, nombre="Empresa uno", slug="empresa-uno"),
            Organizacion(id=2, nombre="Empresa dos", slug="empresa-dos"),
        ])
        db.commit()
        db.info["organizacion_id"] = 1
        yield db
    engine.dispose()


def test_claves_privadas_son_canonicas_y_no_admiten_cruce_tenant():
    key = "organizaciones/7/productos/foto.png"
    assert storage.validate_tenant_object_key(key, 7) == key
    assert storage.storage_reference(key) == f"storage://{key}"
    assert storage.object_key_from_reference(f"storage://{key}") == key
    for invalid in (
        "../secreto", "/organizaciones/7/productos/foto.png",
        "organizaciones\\7\\productos\\foto.png",
        "organizaciones/8/productos/foto.png", "organizaciones/7//foto.png",
        "organizaciones/7/productos/foto con espacio.png",
        "organizaciones/7/productos/../foto.png",
    ):
        with pytest.raises(storage.InvalidStorageKey):
            storage.validate_tenant_object_key(invalid, 7)


def test_base_rechaza_metadato_cuya_clave_no_corresponde_al_tenant(tenant_db):
    tenant_db.add(ArchivoAlmacenado(
        organizacion_id=1,
        object_key="organizaciones/2/productos/ajena.png",
        categoria="productos", content_type="image/png", tamano_bytes=1,
        sha256="0" * 64, nombre_original="ajena.png", metadata_json="{}",
    ))
    with pytest.raises(IntegrityError):
        tenant_db.commit()
    tenant_db.rollback()


def test_url_de_archivo_usa_proxy_privado_y_conserva_legado():
    ref = "storage://organizaciones/1/fotos-proyecto/obra-1.png"
    assert storage.file_url(ref) == "/archivos/organizaciones/1/fotos-proyecto/obra-1.png"
    assert storage.file_url(ref, download=True).endswith("?download=1")
    assert storage.file_url("uploads/products/a.png") == "/static/uploads/products/a.png"
    assert storage.file_url("importaciones/a.xlsx") == "/static/uploads/importaciones/a.xlsx"


def test_legado_web_tambien_usa_proxy_autorizado(monkeypatch):
    monkeypatch.setattr(storage, "DATABASE_IS_SQLITE", False)
    assert storage.file_url("uploads/products/a.png") == "/archivos-legado/products/a.png"
    assert storage.file_url("importaciones/a.xlsx") == "/archivos-legado/importaciones/a.xlsx"


def test_postgresql_bloquea_uploads_estaticos_antes_del_montaje_general():
    env = os.environ.copy()
    env["DATABASE_URL"] = "postgresql+psycopg://usuario:clave@localhost:5432/cotizat"
    script = """
from app.main import app
routes = list(app.router.routes)
block = next(i for i, r in enumerate(routes) if getattr(r, 'path', '') == '/static/uploads/{_legacy_path:path}')
static = next(i for i, r in enumerate(routes) if getattr(r, 'path', '') == '/static')
assert block < static
"""
    result = subprocess.run(
        [sys.executable, "-c", script], cwd=Path(__file__).resolve().parents[1],
        env=env, text=True, capture_output=True,
    )
    assert result.returncode == 0, result.stderr


def test_local_storage_no_puede_salir_de_su_raiz(tmp_path):
    backend = storage.LocalStorage(tmp_path / "uploads")
    key = "organizaciones/1/productos/a.bin"
    backend.put(key, b"privado", "application/octet-stream")
    assert backend.read(key) == b"privado"
    assert backend.local_path(key) == (tmp_path / "uploads" / key).resolve()
    with pytest.raises(storage.InvalidStorageKey):
        backend.put("../../fuera", b"x", "text/plain")
    backend.delete(key)
    assert backend.local_path(key) is None


def test_save_object_registra_solo_metadatos_y_aisla_consultas(tenant_db, tmp_path, monkeypatch):
    backend = storage.LocalStorage(tmp_path / "objects")
    monkeypatch.setattr(storage, "get_storage_backend", lambda: backend)
    data = b"\x89PNG\r\ncontenido-de-prueba"
    saved = storage.save_object(
        tenant_db, data, "productos", "muestra.png", "image/png", prefix="catalogo"
    )
    tenant_db.commit()
    metadata = tenant_db.query(ArchivoAlmacenado).one()
    assert metadata.organizacion_id == 1
    assert metadata.object_key == saved.object_key
    assert metadata.content_type == "image/png"
    assert metadata.tamano_bytes == len(data)
    assert metadata.sha256 == hashlib.sha256(data).hexdigest()
    assert metadata.nombre_original == "muestra.png"
    assert metadata.metadata_json == "{}"
    columnas = {c["name"] for c in inspect(tenant_db.bind).get_columns("archivos_almacenados")}
    assert columnas == {
        "id", "object_key", "categoria", "content_type", "tamano_bytes",
        "sha256", "nombre_original", "metadata_json", "organizacion_id",
    }
    assert backend.read(saved.object_key) == data
    assert data not in repr(metadata.__dict__).encode()
    tenant_db.info["organizacion_id"] = 2
    assert tenant_db.query(ArchivoAlmacenado).all() == []


def test_borrado_conserva_objeto_compartido_hasta_ultima_referencia(tenant_db, tmp_path, monkeypatch):
    from app import main
    backend = storage.LocalStorage(tmp_path / "private")
    monkeypatch.setattr(storage, "get_storage_backend", lambda: backend)
    saved = storage.save_object(tenant_db, b"imagen", "productos", "foto.png", "image/png")
    first = Producto(nombre="Primero", imagen=saved.reference)
    second = Producto(nombre="Segundo", imagen=saved.reference)
    tenant_db.add_all([first, second]); tenant_db.commit()
    tenant_db.delete(first); main._borrar_imagen(saved.reference, tenant_db); tenant_db.commit()
    assert backend.read(saved.object_key) == b"imagen"
    assert tenant_db.query(ArchivoAlmacenado).count() == 1
    tenant_db.delete(second); main._borrar_imagen(saved.reference, tenant_db); tenant_db.commit()
    assert backend.local_path(saved.object_key) is None
    assert tenant_db.query(ArchivoAlmacenado).count() == 0


def test_referencia_oculta_no_puede_inyectar_imagen_de_otro_tenant(tenant_db, tmp_path, monkeypatch):
    from app import main
    backend = storage.LocalStorage(tmp_path / "private")
    monkeypatch.setattr(storage, "get_storage_backend", lambda: backend)
    tenant_db.info["organizacion_id"] = 2
    foreign = storage.save_object(tenant_db, b"imagen", "productos", "foto.png", "image/png")
    tenant_db.commit()
    tenant_db.info["organizacion_id"] = 1
    assert main._normalizar_referencia_imagen(tenant_db, foreign.reference) == ""
    assert main._normalizar_referencia_imagen(
        tenant_db, "storage://organizaciones/1/productos/../secreto.png"
    ) == ""


def test_proxy_privado_rechaza_otra_organizacion(tenant_db, tmp_path, monkeypatch):
    from app import main
    backend = storage.LocalStorage(tmp_path / "private")
    monkeypatch.setattr(storage, "get_storage_backend", lambda: backend)
    monkeypatch.setattr(main, "get_storage_backend", lambda: backend)
    stored = storage.save_object(tenant_db, b"archivo", "anexos", "anexo.pdf", "application/pdf")
    tenant_db.commit()
    ok = main.descargar_archivo_privado(stored.object_key, db=tenant_db)
    assert ok.status_code == 200 and ok.body == b"archivo"
    assert ok.headers["cache-control"].startswith("private")
    assert ok.headers["x-content-type-options"] == "nosniff"
    denied = main.descargar_archivo_privado(
        stored.object_key.replace("organizaciones/1/", "organizaciones/2/"), db=tenant_db
    )
    assert denied.status_code == 404


class _FakeHTTPResponse:
    def __init__(self, body=b"{}", status=200): self.body, self.status = body, status
    def __enter__(self): return self
    def __exit__(self, *_args): return False
    def read(self, _size=-1): return self.body


def _supabase_settings(tmp_path):
    return storage.StorageSettings(
        backend="supabase", local_root=tmp_path,
        supabase_url="https://example.supabase.co",
        secret_key="sb_secret_prueba-no-real", bucket="cotizat-private",
    )


def test_supabase_storage_solo_envia_credencial_desde_backend(tmp_path, monkeypatch):
    requests = []
    def fake_urlopen(request, timeout):
        requests.append((request, timeout)); return _FakeHTTPResponse()
    monkeypatch.setattr(storage, "urlopen", fake_urlopen)
    backend = storage.SupabaseStorage(_supabase_settings(tmp_path))
    backend.put("organizaciones/3/productos/foto-1.png", b"png", "image/png")
    request, timeout = requests[0]
    assert timeout == 20
    assert request.full_url.endswith(
        "/storage/v1/object/cotizat-private/organizaciones/3/productos/foto-1.png"
    )
    assert request.method == "POST"
    assert "Authorization" not in request.headers
    assert request.headers["Apikey"].startswith("sb_secret_")
    assert request.headers["X-upsert"] == "false"
    assert request.data == b"png"


def test_creacion_explicita_de_bucket_siempre_es_privada(tmp_path, monkeypatch):
    requests = []
    def fake_urlopen(request, timeout): requests.append(request); return _FakeHTTPResponse()
    monkeypatch.setattr(storage, "urlopen", fake_urlopen)
    storage.SupabaseStorage(_supabase_settings(tmp_path)).create_private_bucket()
    payload = json.loads(requests[0].data)
    assert requests[0].full_url.endswith("/storage/v1/bucket")
    assert payload["id"] == "cotizat-private" and payload["public"] is False
    assert payload["file_size_limit"] == 12 * 1024 * 1024


def test_supabase_exige_secret_key_y_nunca_publishable(monkeypatch):
    monkeypatch.setenv("COTIZAT_STORAGE_BACKEND", "supabase")
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SECRET_KEY", "sb_publishable_no-es-valida")
    with pytest.raises(storage.StorageNotConfigured, match="sb_secret_"):
        storage.StorageSettings.from_environment()


def test_pdf_materializa_objeto_remoto_en_tmp(tmp_path, monkeypatch):
    class RemoteBackend(storage.StorageBackend):
        name = "supabase"; bucket = "cotizat-private"
        def put(self, object_key, data, content_type): raise AssertionError("no debe escribir")
        def read(self, object_key):
            assert object_key == "organizaciones/1/logos/logo.png"; return b"imagen-remota"
        def delete(self, object_key): raise AssertionError("no debe borrar")
    monkeypatch.setattr(storage, "get_storage_backend", lambda: RemoteBackend())
    monkeypatch.setattr(storage.tempfile, "gettempdir", lambda: str(tmp_path))
    path = storage.materialize_reference("storage://organizaciones/1/logos/logo.png")
    assert path.parent == tmp_path / "cotizat-storage-cache"
    assert path.suffix == ".png" and path.read_bytes() == b"imagen-remota"
