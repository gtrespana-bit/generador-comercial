"""Envío de presupuestos PDF por email (E3-016)."""
import base64
from datetime import date, datetime
from io import BytesIO
import json

import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import main as main_module
from app.database import Base, get_db
from app.main import app
from app.models import (
    Capitulo,
    Cliente,
    Configuracion,
    Membresia,
    NotaSeguimiento,
    Organizacion,
    Presupuesto,
    PresupuestoItem,
    PresupuestoVersion,
    Usuario,
)
from app.services import email as email_module
from app.storage import read_reference, reset_storage_backend_cache


class _FakeHTTPResponse:
    def __init__(self, body=b'{"id":"resend-presupuesto-1"}'):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, _size=-1):
        return self.body


@pytest.fixture
def presupuesto_web(monkeypatch, tmp_path):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as seed:
        org = Organizacion(nombre="Construcciones Prueba", slug="envio-presupuesto")
        usuario = Usuario(
            auth_user_id="00000000-0000-4000-8000-000000000016",
            email="empresa@example.com",
            nombre="Responsable",
            email_verificado_at=datetime(2026, 8, 16),
        )
        seed.add_all([org, usuario])
        seed.flush()
        seed.info["organizacion_id"] = org.id
        seed.info["rol_membresia"] = "propietario"
        cfg = Configuracion(
            empresa_nombre="Construcciones Prueba",
            empresa_email="respuesta@example.com",
        )
        cliente = Cliente(
            nombre="Cliente Ejemplo",
            email="cliente@example.com",
            pais="Venezuela",
        )
        seed.add_all([cfg, cliente])
        seed.flush()
        presupuesto = Presupuesto(
            numero="P-2026-016",
            year=2026,
            fecha=date(2026, 8, 16),
            titulo="Reforma de baño",
            estado="borrador",
            client_id=cliente.id,
        )
        capitulo = Capitulo(nombre="BAÑO", orden=1)
        capitulo.partidas.append(
            PresupuestoItem(
                nombre="Revestimiento",
                unidad="m2",
                cantidad=10,
                precio_unitario=20,
                orden=1,
            )
        )
        presupuesto.capitulos.append(capitulo)
        seed.add(presupuesto)
        seed.add(Membresia(
            usuario_id=usuario.id,
            organizacion_id=org.id,
            rol="propietario",
        ))
        seed.commit()
        ids = org.id, usuario.id, presupuesto.id

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
        yield Session, ids[2], rol
    finally:
        app.dependency_overrides.pop(get_db, None)
        reset_storage_backend_cache()
        engine.dispose()


def _cliente():
    return TestClient(app, base_url="https://cotizat.test")


def _post(client, **cambios):
    datos = {
        "destinatario": "cliente@example.com",
        "asunto": "Presupuesto P-2026-016 · Reforma de baño",
        "mensaje": "Hola. Adjuntamos la propuesta.",
    }
    datos.update(cambios)
    return client.post(
        "/presupuestos/1/enviar-email",
        data=datos,
        headers={"Origin": "https://cotizat.test"},
        follow_redirects=False,
    )


def test_resend_recibe_pdf_base64_reply_to_y_html_escapado(monkeypatch):
    capturado = {}

    def fake_urlopen(request, timeout):
        capturado["payload"] = json.loads(request.data.decode("utf-8"))
        capturado["timeout"] = timeout
        return _FakeHTTPResponse()

    monkeypatch.setenv("RESEND_API_KEY", "re_prueba")
    monkeypatch.setenv("COTIZAT_EMAIL_FROM", "CotizaT <no-responder@cotizat.test>")
    monkeypatch.setattr(email_module, "urlopen", fake_urlopen)
    pdf = b"%PDF-1.4\ncontenido"

    envio_id = email_module.enviar_presupuesto_por_email(
        email="cliente@example.com",
        asunto="Presupuesto P-001",
        mensaje="Revisa <script>alert(1)</script>",
        empresa_nombre="Constructora",
        cliente_nombre="Cliente",
        presupuesto_numero="P-001",
        presupuesto_titulo="Baño",
        total_texto="200,00 $",
        pdf=pdf,
        nombre_pdf="presupuesto_P-001.pdf",
        responder_a="respuesta@example.com",
    )

    assert envio_id == "resend-presupuesto-1"
    payload = capturado["payload"]
    assert payload["to"] == ["cliente@example.com"]
    assert payload["reply_to"] == "respuesta@example.com"
    assert payload["attachments"][0]["filename"] == "presupuesto_P-001.pdf"
    assert base64.b64decode(payload["attachments"][0]["content"]) == pdf
    assert "<script>" not in payload["html"]
    assert "&lt;script&gt;" in payload["html"]
    assert capturado["timeout"] == 10


def test_notificacion_respuesta_usa_reply_to_del_cliente(monkeypatch):
    capturado = {}

    def fake_urlopen(request, timeout):
        capturado.update(json.loads(request.data.decode("utf-8")))
        return _FakeHTTPResponse(b'{"id":"aviso-respuesta-1"}')

    monkeypatch.setenv("RESEND_API_KEY", "re_prueba")
    monkeypatch.setenv("COTIZAT_EMAIL_FROM", "CotizaT <no-responder@cotizat.test>")
    monkeypatch.setattr(email_module, "urlopen", fake_urlopen)
    envio_id = email_module.enviar_respuesta_propuesta_por_email(
        email="empresa@example.com",
        decision="aceptada",
        empresa_nombre="Constructora",
        cliente_nombre="Familia Ejemplo",
        presupuesto_numero="P-017",
        presupuesto_titulo="Baño",
        version_numero=2,
        respondido_por_nombre="Ana Cliente",
        respondido_por_email="ana@example.com",
        comentario="Conforme <script>alert(1)</script>",
        enlace_interno="https://cotizat.test/presupuestos/17#versiones",
    )
    assert envio_id == "aviso-respuesta-1"
    assert capturado["to"] == ["empresa@example.com"]
    assert capturado["reply_to"] == "ana@example.com"
    assert "Propuesta aceptada" in capturado["subject"]
    assert "V2" in capturado["html"]
    assert "<script>" not in capturado["html"]
    assert "&lt;script&gt;" in capturado["html"]
    assert "https://cotizat.test/presupuestos/17#versiones" in capturado["html"]


def test_formulario_precarga_email_asunto_y_mensaje(presupuesto_web):
    _Session, presupuesto_id, _rol = presupuesto_web
    with _cliente() as client:
        respuesta = client.get(f"/presupuestos/{presupuesto_id}/enviar-email")
    assert respuesta.status_code == 200
    assert 'value="cliente@example.com"' in respuesta.text
    assert "Presupuesto P-2026-016 · Reforma de baño" in respuesta.text
    assert "Construcciones Prueba" in respuesta.text
    assert "Generar PDF y enviar" in respuesta.text


def test_envio_exitoso_congela_version_pdf_y_constancia(
    presupuesto_web, monkeypatch
):
    Session, presupuesto_id, _rol = presupuesto_web
    capturado = {}

    def fake_enviar(**kwargs):
        capturado.update(kwargs)
        return "resend-ok-016"

    monkeypatch.setattr(main_module, "enviar_presupuesto_por_email", fake_enviar)
    monkeypatch.setattr(
        main_module.pdf_service,
        "generar_pdf",
        lambda presupuesto, cfg: BytesIO(b"%PDF-1.4\npresupuesto enviado"),
    )

    with _cliente() as client:
        respuesta = client.post(
            f"/presupuestos/{presupuesto_id}/enviar-email",
            data={
                "destinatario": "cliente@example.com",
                "asunto": "Propuesta de baño",
                "mensaje": "Hola. Adjuntamos la propuesta.",
            },
            headers={"Origin": "https://cotizat.test"},
            follow_redirects=False,
        )

    assert respuesta.status_code == 303
    assert capturado["pdf"].startswith(b"%PDF-")
    assert capturado["responder_a"] == "respuesta@example.com"
    with Session() as db:
        db.info["organizacion_id"] = 1
        presupuesto = db.get(Presupuesto, presupuesto_id)
        version = db.query(PresupuestoVersion).filter_by(
            presupuesto_id=presupuesto_id
        ).one()
        nota = db.query(NotaSeguimiento).filter_by(
            presupuesto_id=presupuesto_id
        ).one()
        assert presupuesto.estado == "enviado"
        assert version.estado == "enviado"
        assert version.numero_version == 1
        assert version.pdf_snapshot.startswith("storage://organizaciones/1/presupuestos/")
        assert read_reference(version.pdf_snapshot) == b"%PDF-1.4\npresupuesto enviado"
        assert "cliente@example.com" in nota.texto
        assert "resend-ok-016" in nota.texto


def test_fallo_del_proveedor_no_cambia_estado_ni_crea_version(
    presupuesto_web, monkeypatch
):
    Session, presupuesto_id, _rol = presupuesto_web
    monkeypatch.setattr(
        main_module,
        "enviar_presupuesto_por_email",
        lambda **_kwargs: (_ for _ in ()).throw(email_module.EmailSendError("Resend no respondió.")),
    )
    monkeypatch.setattr(
        main_module.pdf_service,
        "generar_pdf",
        lambda presupuesto, cfg: BytesIO(b"%PDF-1.4\nfallo"),
    )

    with _cliente() as client:
        respuesta = client.post(
            f"/presupuestos/{presupuesto_id}/enviar-email",
            data={
                "destinatario": "cliente@example.com",
                "asunto": "Propuesta de baño",
                "mensaje": "Mensaje de prueba",
            },
            headers={"Origin": "https://cotizat.test"},
        )

    assert respuesta.status_code == 502
    assert "Resend no respondió" in respuesta.text
    with Session() as db:
        db.info["organizacion_id"] = 1
        assert db.get(Presupuesto, presupuesto_id).estado == "borrador"
        assert db.query(PresupuestoVersion).count() == 0
        assert db.query(NotaSeguimiento).count() == 0


def test_rol_lectura_no_contacta_proveedor(presupuesto_web, monkeypatch):
    _Session, presupuesto_id, rol = presupuesto_web
    rol["valor"] = "lectura"
    llamado = {"valor": False}

    def fake_enviar(**_kwargs):
        llamado["valor"] = True
        return "no-debe-ocurrir"

    monkeypatch.setattr(main_module, "enviar_presupuesto_por_email", fake_enviar)
    with _cliente() as client:
        respuesta = client.post(
            f"/presupuestos/{presupuesto_id}/enviar-email",
            data={
                "destinatario": "cliente@example.com",
                "asunto": "Propuesta",
                "mensaje": "Mensaje",
            },
            headers={"Origin": "https://cotizat.test"},
        )
    assert respuesta.status_code == 403
    assert not llamado["valor"]


def test_email_invalido_se_rechaza_antes_de_generar_pdf(presupuesto_web, monkeypatch):
    _Session, presupuesto_id, _rol = presupuesto_web
    generado = {"valor": False}

    def fake_pdf(*_args):
        generado["valor"] = True
        return BytesIO(b"%PDF-1.4")

    monkeypatch.setattr(main_module.pdf_service, "generar_pdf", fake_pdf)
    with _cliente() as client:
        respuesta = client.post(
            f"/presupuestos/{presupuesto_id}/enviar-email",
            data={
                "destinatario": "no-es-email",
                "asunto": "Propuesta",
                "mensaje": "Mensaje",
            },
            headers={"Origin": "https://cotizat.test"},
        )
    assert respuesta.status_code == 400
    assert "email de destino válido" in respuesta.text
    assert not generado["valor"]
