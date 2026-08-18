"""Aísla la base global de la aplicación durante toda la suite.

Algunos recorridos HTTP importan ``app.main`` y usan su ``SessionLocal`` real.
La variable debe definirse antes de que pytest importe esos módulos para que
ninguna prueba pueda migrar o modificar ``presupuestos.db`` del desarrollador.
"""
import os
import shutil
import tempfile
from pathlib import Path

import pytest

_TEST_DATA = Path(tempfile.mkdtemp(prefix="cotizat-tests-"))
os.environ["COTIZAT_DB"] = str(_TEST_DATA / "suite.db")
os.environ.pop("DATABASE_URL", None)


@pytest.fixture(scope="session", autouse=True)
def _base_http_aislada():
    """Prepara la demostración que usan las regresiones HTTP históricas."""
    from app.database import SessionLocal, init_db
    from app.models import Configuracion
    from app.services.onboarding import completar_onboarding

    init_db()
    with SessionLocal() as db:
        cfg = db.query(Configuracion).first()
        if not cfg.onboarding_completado:
            completar_onboarding(db, {"empresa_nombre": "Empresa de pruebas"}, "demo")
    yield


def pytest_sessionfinish(session, exitstatus):  # noqa: ARG001
    shutil.rmtree(_TEST_DATA, ignore_errors=True)


# ---------------------------------------------------------------------------
# Fixtures de los bloques E3-020 a E3-023.
#
# ``entorno`` construye una organización rica (catálogo con archivos en el
# almacenamiento privado, presupuesto con capítulos/mediciones/descomposiciones/
# versión/anexos/notas, enlace respondido y pendiente, factura, proyecto con
# cambios y pagos, licencia, membresías y datos de demostración) sobre una
# SQLite en memoria, y expone (Session, ids, rol) con un override de ``get_db``
# que mantiene el contexto de organización, como en las pruebas de E3-016.
# ---------------------------------------------------------------------------
from datetime import date, datetime

from fastapi import Request
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Bypass rate limit for /demo in tests (3 → 999)
from app.security import AuthRateLimitMiddleware
original_demo_limit = AuthRateLimitMiddleware.DEFAULT_LIMITS.get("/demo", 3)
AuthRateLimitMiddleware.DEFAULT_LIMITS["/demo"] = 999

from app.database import Base, get_db
from app.main import app
from app.models import (
    AnexoPresupuesto,
    CambioAlcance,
    CambioAlcanceItem,
    Capitulo,
    CategoriaPartida,
    Cliente,
    Configuracion,
    DescomposicionFila,
    DescomposicionPartida,
    EnlacePropuesta,
    Factura,
    FacturaCapitulo,
    FacturaItem,
    Licencia,
    Medicion,
    Membresia,
    NotaSeguimiento,
    Organizacion,
    Pago,
    Partida,
    Plantilla,
    Presupuesto,
    PresupuestoItem,
    PresupuestoItemProducto,
    PresupuestoVersion,
    Producto,
    Proyecto,
    RecetaEstancia,
    Recurso,
    Usuario,
)
from app.storage import reset_storage_backend_cache, save_object

ORIGEN = "https://cotizat.test"
AUTH_UUID = "00000000-0000-4000-8000-000000000020"
NOMBRE_ORG = "Constructora Restaurada"


@pytest.fixture
def entorno(monkeypatch, tmp_path):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _fk(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as db:
        org = Organizacion(nombre=NOMBRE_ORG, slug="restauracion")
        duena = Usuario(
            auth_user_id=AUTH_UUID,
            email="duena@example.com",
            nombre="Dueña",
            email_verificado_at=datetime(2026, 8, 16),
        )
        miembro = Usuario(
            auth_user_id="00000000-0000-4000-8000-000000000021",
            email="miembro@example.com",
            nombre="Miembro",
        )
        db.add_all([org, duena, miembro])
        db.flush()
        db.info["organizacion_id"] = org.id
        db.info["rol_membresia"] = "propietario"

        configuracion = Configuracion(
            empresa_nombre=NOMBRE_ORG,
            iva_default=18.0,
            moneda_default="Bs",
            validez_default=45,
        )
        cliente = Cliente(nombre="Cliente Restaurado", rif="J-12345678-9", email="c@example.com")
        cliente_demo = Cliente(nombre="Cliente Demo", es_demo=True)
        db.add_all([configuracion, cliente, cliente_demo])

        # Catálogo con archivo en storage
        logo_bytes = b"PNG-logotipo-empresa"
        guardado_logo = save_object(db, logo_bytes, "logos", "logo.png", "image/png")
        # Mismo contenido con otra clave: la copia debe deduplicarlo por SHA-256
        guardado_foto = save_object(db, logo_bytes, "fotos-proyecto", "foto.jpg", "image/jpeg")
        partida = Partida(
            nombre="Cerámica esmaltada", precio_unitario=12.0, unidad="m2",
            categoria="Albañilería", imagen=guardado_logo.reference,
        )
        producto = Producto(
            nombre="Porcelanato gris", precio_unitario=45.0, unidad="m2",
            imagen=guardado_logo.reference,
        )
        recurso = Recurso(codigo="MO001", descripcion="Oficial", unidad="hora",
                          categoria="mano_obra", precio=6.5)
        categoria = CategoriaPartida(categoria="Albañilería", subcategoria="Muros")
        plantilla = Plantilla(nombre="Baño básico", datos="[]")
        receta = RecetaEstancia(nombre="Baño principal", datos="[]")
        db.add_all([partida, producto, recurso, categoria, plantilla, receta])
        db.flush()

        presupuesto = Presupuesto(
            numero="P-2026-020", year=2026, fecha=date(2026, 8, 16),
            titulo="Reforma de baño", estado="aprobado", client_id=cliente.id,
            foto_proyecto=guardado_foto.reference,
        )
        demo = Presupuesto(
            numero="P-DEMO-001", year=2026, fecha=date(2026, 8, 16),
            titulo="Presupuesto de ejemplo", estado="borrador",
            client_id=cliente.id, es_demo=True,
        )
        capitulo = Capitulo(nombre="BAÑO", orden=1)
        item = PresupuestoItem(
            nombre="Revestimiento", unidad="m2", cantidad=10,
            precio_unitario=20, orden=1,
        )
        item.mediciones.append(Medicion(concepto="Paredes", cantidad=8, orden=1))
        item.productos_opciones.append(PresupuestoItemProducto(
            nombre="Porcelanato gris", precio=45.0, seleccionado=True, orden=1,
        ))
        item.descomposicion_cype = DescomposicionPartida(
            codigo="D-01", unidad="m2", coste_directo_unitario=15.0,
            archivo_origen=guardado_logo.reference, nombre_archivo_origen="cype.xlsx",
        )
        capitulo.partidas.append(item)
        presupuesto.capitulos.append(capitulo)
        db.add_all([presupuesto, demo])
        db.flush()

        version = PresupuestoVersion(
            presupuesto_id=presupuesto.id, numero_version=1,
            estado="aprobada", total=200.0, datos_snapshot="{}",
            pdf_snapshot=guardado_logo.reference,
        )
        db.add_all([
            version,
            AnexoPresupuesto(presupuesto_id=presupuesto.id, nombre="Plano.pdf",
                             archivo=guardado_logo.reference),
            NotaSeguimiento(
                presupuesto_id=presupuesto.id,
                texto="Llamé al cliente y confirmó el alcance.",
                created_at=datetime(2026, 8, 16, 12, 0),
            ),
        ])
        db.flush()

        descomposicion = (
            db.query(DescomposicionPartida).filter(
                DescomposicionPartida.partida_id == item.id).first()
        )
        db.add(DescomposicionFila(
            descomposicion_id=descomposicion.id, orden=1, tipo="material",
            descripcion="Cerámica", rendimiento=1.0, precio_unitario=12.0,
            importe=12.0,
        ))

        # Enlace con respuesta histórica + enlace pendiente (no deben viajar)
        db.add_all([
            EnlacePropuesta(
                presupuesto_id=presupuesto.id,
                presupuesto_version_id=version.id,
                presupuesto_version_numero=1,
                token_hash="a" * 64, token_prefix="prefijoresp",
                pdf_snapshot=guardado_logo.reference,
                empresa_nombre=NOMBRE_ORG,
                cliente_nombre="Cliente Restaurado",
                presupuesto_numero="P-2026-020",
                presupuesto_titulo="Reforma de baño",
                total=200.0, moneda="Bs",
                fecha_presupuesto=date(2026, 8, 16),
                valido_hasta=date(2026, 9, 15),
                expires_at=datetime(2026, 9, 15, 23, 59),
                respuesta="aceptada",
                respondido_por_nombre="Cliente Restaurado",
                respondido_por_email="c@example.com",
                respuesta_comentario="Aprobado, empezamos el lunes.",
                responded_at=datetime(2026, 8, 16, 13, 30),
            ),
            EnlacePropuesta(
                presupuesto_id=presupuesto.id,
                presupuesto_version_id=version.id,
                presupuesto_version_numero=1,
                token_hash="b" * 64, token_prefix="prefijopend",
                pdf_snapshot=guardado_logo.reference,
                empresa_nombre=NOMBRE_ORG,
                cliente_nombre="Cliente Restaurado",
                presupuesto_numero="P-2026-020",
                presupuesto_titulo="Reforma de baño",
                total=200.0, moneda="Bs",
                fecha_presupuesto=date(2026, 8, 16),
                valido_hasta=date(2026, 9, 15),
                expires_at=datetime(2026, 9, 15, 23, 59),
            ),
        ])

        factura = Factura(
            numero="F-2026-001", year=2026, fecha=date(2026, 8, 16),
            titulo="Anticipo baño", estado="emitida", client_id=cliente.id,
        )
        factura_capitulo = FacturaCapitulo(nombre="ANTICIPO", orden=1)
        factura_capitulo.partidas.append(FacturaItem(
            nombre="Anticipo 50%", unidad="global", cantidad=1,
            precio_unitario=100, orden=1,
        ))
        factura.capitulos.append(factura_capitulo)
        db.add(factura)
        db.flush()

        proyecto = Proyecto(
            presupuesto_id=presupuesto.id, presupuesto_version_id=version.id,
            nombre="Baño Cliente Restaurado", estado="en_ejecucion",
        )
        proyecto.cambios.append(CambioAlcance(
            numero=1, descripcion="Cambio de grifería", estado="aprobado",
            diferencia_total=30.0,
            items=[CambioAlcanceItem(
                tipo="agregado", nombre="Grifería", cantidad=1, precio_unitario=30,
            )],
        ))
        proyecto.pagos.append(Pago(
            fecha=date(2026, 8, 16), importe=100.0, moneda="Bs",
            metodo="transferencia", referencia="REF-1", estado="confirmado",
        ))
        db.add(proyecto)
        db.flush()
        # Pago vinculado solo a la factura (sin proyecto): clave natural parcial
        db.add(Pago(
            factura_id=factura.id, fecha=date(2026, 8, 16), importe=100.0,
            moneda="Bs", metodo="transferencia", referencia="REF-2",
            estado="confirmado",
        ))

        # Lo que NUNCA debe viajar: licencias
        db.add(Licencia(
            organizacion_id=org.id,
            estado="activa", origen="cortesia",
            inicio=date(2026, 8, 1), vence=date(2026, 9, 1),
            creada_por_email="operador@example.com",
        ))

        db.add(Membresia(usuario_id=duena.id, organizacion_id=org.id, rol="propietario"))
        db.add(Membresia(usuario_id=miembro.id, organizacion_id=org.id, rol="miembro"))
        db.commit()
        ids = (org.id, duena.id, presupuesto.id)

    monkeypatch.setenv("COTIZAT_STORAGE_BACKEND", "local")
    monkeypatch.setenv("COTIZAT_STORAGE_DIR", str(tmp_path / "storage"))
    reset_storage_backend_cache()
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
        yield Session, ids, rol
    finally:
        app.dependency_overrides.pop(get_db, None)
        reset_storage_backend_cache()
        engine.dispose()


@pytest.fixture
def cliente_web():
    return TestClient(app, base_url=ORIGEN)
