from app.services.planos import calcular_valor_real


def test_calcular_valor_lineal_sin_escala():
    puntos = [[0,0],[100,0]]
    valor, unidad = calcular_valor_real("lineal", puntos, None)
    assert valor == 100
    assert unidad == "px"


def test_calcular_valor_lineal_con_escala():
    puntos = [[0,0],[200,0]]
    # 100 px = 1 m
    escala = 100.0
    valor, unidad = calcular_valor_real("lineal", puntos, escala)
    assert abs(valor - 2.0) < 0.01
    assert unidad == "m"


def test_calcular_area():
    puntos = [[0,0],[100,0],[100,100],[0,100]]
    escala = 100.0  # 100 px =1m => 100px=1m => area 1m2
    valor, unidad = calcular_valor_real("area", puntos, escala)
    assert abs(valor - 1.0) < 0.01
    assert unidad == "m2"


def test_calcular_conteo():
    puntos = [[0,0],[10,10],[20,20]]
    valor, unidad = calcular_valor_real("conteo", puntos, 100.0)
    assert valor == 3
    assert unidad == "ud"


# ------------------------------------------------------------------
# Visor global de planos (/planos) y enlace profundo ?plano=<id>
# ------------------------------------------------------------------
from datetime import date  # noqa: E402

import pytest  # noqa: E402
from fastapi import Request  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import (  # noqa: E402
    Cliente,
    Configuracion,
    Membresia,
    Organizacion,
    Presupuesto,
    Usuario,
)
from app.services.planos import crear_plano  # noqa: E402
from app.storage import reset_storage_backend_cache  # noqa: E402

# PNG 1x1 RGBA válido.
PNG_1x1 = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


@pytest.fixture
def entorno_planos(monkeypatch, tmp_path):
    monkeypatch.setenv("COTIZAT_STORAGE_BACKEND", "local")
    monkeypatch.setenv("COTIZAT_STORAGE_DIR", str(tmp_path / "storage"))
    reset_storage_backend_cache()

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as seed:
        org = Organizacion(nombre="Constructora Planos", slug="constructora-planos")
        usuario = Usuario(
            auth_user_id="00000000-0000-4000-8000-000000000030",
            email="planos@example.com",
            nombre="Medidora",
        )
        seed.add_all([org, usuario])
        seed.flush()
        seed.info["organizacion_id"] = org.id
        seed.info["rol_membresia"] = "propietario"
        cfg = Configuracion(empresa_nombre="Constructora Planos")
        cliente = Cliente(nombre="Cliente Plano")
        seed.add_all([cfg, cliente])
        seed.flush()
        presupuesto = Presupuesto(
            numero="P-2026-031",
            year=2026,
            fecha=date(2026, 8, 20),
            titulo="Local comercial",
            estado="borrador",
            client_id=cliente.id,
        )
        seed.add(presupuesto)
        seed.flush()
        plano_a = crear_plano(seed, presupuesto.id, "Planta baja", "planta.png", PNG_1x1)
        plano_b = crear_plano(seed, presupuesto.id, "Alzado norte", "alzado.png", PNG_1x1)
        seed.add(Membresia(usuario_id=usuario.id, organizacion_id=org.id, rol="propietario"))
        seed.commit()
        ids = (org.id, usuario.id, presupuesto.id, plano_a.id, plano_b.id)

    rol = {"valor": "propietario"}

    def _db(request: Request):
        db = Session()
        db.info["organizacion_id"] = ids[0]
        db.info["usuario_id"] = ids[1]
        db.info["rol_membresia"] = rol["valor"]
        request.state.organizacion = db.get(Organizacion, ids[0])
        request.state.membresia = None
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _db
    try:
        yield Session, ids
    finally:
        app.dependency_overrides.pop(get_db, None)
        reset_storage_backend_cache()
        engine.dispose()


def test_visor_global_lista_planos_agrupados_por_presupuesto(entorno_planos):
    """La galería /planos muestra todos los planos y enlaza al área de medición."""
    _Session, ids = entorno_planos
    client = TestClient(app, base_url="https://cotizat.test")
    resp = client.get("/planos")
    assert resp.status_code == 200
    assert "Visor de planos" in resp.text
    assert "P-2026-031" in resp.text
    assert "Planta baja" in resp.text
    assert "Alzado norte" in resp.text
    # Enlaces profundos a cada plano del grupo.
    assert f"/presupuestos/{ids[2]}/planos?plano={ids[3]}" in resp.text
    assert f"/presupuestos/{ids[2]}/planos?plano={ids[4]}" in resp.text
    # Miniaturas servidas por el endpoint privado de archivos.
    assert f"/planos/{ids[3]}/archivo" in resp.text


def test_area_de_medicion_preselecciona_plano_por_query(entorno_planos):
    """?plano=<id> abre directamente el plano enlazado desde el visor."""
    _Session, ids = entorno_planos
    client = TestClient(app, base_url="https://cotizat.test")
    resp = client.get(f"/presupuestos/{ids[2]}/planos?plano={ids[4]}")
    assert resp.status_code == 200
    assert f"planoActivoId = {ids[4]};" in resp.text


def test_area_de_medicion_ignora_plano_inexistente(entorno_planos):
    """Un ?plano ajeno al presupuesto cae en el plano más reciente."""
    _Session, ids = entorno_planos
    client = TestClient(app, base_url="https://cotizat.test")
    resp = client.get(f"/presupuestos/{ids[2]}/planos?plano=999999")
    assert resp.status_code == 200
    assert f"planoActivoId = {ids[4]};" in resp.text
