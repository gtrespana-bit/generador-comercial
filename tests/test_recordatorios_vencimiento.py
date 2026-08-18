"""Recordatorios automáticos de vencimiento (cron) y su correo premium.

El aviso histórico de vencimiento lo dispara el operador a mano. El
recordatorio, en cambio, lo dispara el programador de Vercel a dos hitos
exactos —5 y 1 día antes de vencer— para que nadie se tope con el corte de
golpe. Lo importante aquí es el **contorno**:

- solo se avisa en los hitos exactos, y una única vez por hito y licencia;
- la ruta del cron no responde sin el secreto compartido;
- el correo es premium y enlaza al checkout, no a un mailto.
"""
from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from app.database import Base, get_cron_db
from app.main import app
from app.models import Licencia, Membresia, Organizacion, Usuario
from app.services import email as email_module
from app.services.licencias import (
    crear_licencia,
    enviar_recordatorios_vencimiento,
    recordatorio_enviado,
)

HOY = date(2026, 8, 17)


def _db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine)()


def _organizacion_con_dueno(db, nombre="Constructora", email="dueno@example.com"):
    organizacion = Organizacion(nombre=nombre, slug=nombre.lower().replace(" ", "-"))
    db.add(organizacion)
    db.flush()
    usuario = Usuario(email=email, nombre="Dueño")
    db.add(usuario)
    db.flush()
    db.add(
        Membresia(
            organizacion_id=organizacion.id, usuario_id=usuario.id, rol="propietario"
        )
    )
    db.commit()
    return organizacion


def _licencia_que_vence_en(db, organizacion, dias_restantes, origen="pago", hoy=HOY):
    """Licencia vigente cuyo acceso termina exactamente dentro de N días."""
    importe = 9.99 if origen == "pago" else 0.0
    licencia = crear_licencia(
        db,
        organizacion_id=organizacion.id,
        origen=origen,
        dias=dias_restantes + 6,
        importe=importe,
        operador_email="titular@example.com",
        inicio=hoy - timedelta(days=5),
    )
    db.commit()
    return licencia


# ---------------------------------------------------------------------------
# El barrido de recordatorios (servicio)
# ---------------------------------------------------------------------------


def test_se_avisa_solo_en_los_hitos_de_5_y_1_dias():
    engine, db = _db()
    try:
        a5 = _organizacion_con_dueno(db, "Cinco Días", "cinco@example.com")
        _licencia_que_vence_en(db, a5, 5)
        a3 = _organizacion_con_dueno(db, "Tres Días", "tres@example.com")
        _licencia_que_vence_en(db, a3, 3)
        a1 = _organizacion_con_dueno(db, "Un Día", "un-dia@example.com")
        _licencia_que_vence_en(db, a1, 1)

        envios = []
        resultado = enviar_recordatorios_vencimiento(
            db, remitente=lambda **kwargs: envios.append(kwargs), hoy=HOY
        )
        db.commit()

        # 5 y 1 entran; 3 no (no es un hito).
        enviados = {
            envio["organizacion_nombre"]: envio for envio in envios
        }
        assert set(enviados) == {"Cinco Días", "Un Día"}
        assert enviados["Cinco Días"]["dias_restantes"] == 5
        assert enviados["Un Día"]["dias_restantes"] == 1
        assert resultado["omitidas"] == []
    finally:
        db.close()
        engine.dispose()


def test_un_hito_no_se_repite_para_la_misma_licencia():
    engine, db = _db()
    try:
        org = _organizacion_con_dueno(db)
        licencia = _licencia_que_vence_en(db, org, 5)

        envios = []
        enviar_recordatorios_vencimiento(
            db, remitente=lambda **kwargs: envios.append(kwargs), hoy=HOY
        )
        db.commit()
        assert len(envios) == 1
        assert recordatorio_enviado(licencia, 5)
        assert "Recordatorio de vencimiento enviado (5 días)" in licencia.notas

        # Volver a barrer el mismo día no reenvía el mismo hito.
        resultado = enviar_recordatorios_vencimiento(
            db, remitente=lambda **kwargs: envios.append(kwargs), hoy=HOY
        )
        assert resultado["omitidas"] == ["Constructora"]
        assert len(envios) == 1
    finally:
        db.close()
        engine.dispose()


def test_no_se_avisa_a_quien_tiene_tiempo_o_ya_vencio():
    engine, db = _db()
    try:
        con_tiempo = _organizacion_con_dueno(db, "Con Tiempo", "tiempo@example.com")
        _licencia_que_vence_en(db, con_tiempo, 30)
        vencida = _organizacion_con_dueno(db, "Ya Vencida", "vencida@example.com")
        _licencia_que_vence_en(db, vencida, -2)

        envios = []
        resultado = enviar_recordatorios_vencimiento(
            db, remitente=lambda **kwargs: envios.append(kwargs), hoy=HOY
        )

        assert envios == []
        assert resultado["avisadas"] == []
    finally:
        db.close()
        engine.dispose()


def test_un_fallo_del_proveedor_no_se_anota_como_enviado():
    engine, db = _db()
    try:
        org = _organizacion_con_dueno(db)
        licencia = _licencia_que_vence_en(db, org, 1)

        def remitente_roto(**_kwargs):
            raise RuntimeError("proveedor caído")

        resultado = enviar_recordatorios_vencimiento(
            db, remitente=remitente_roto, hoy=HOY
        )
        db.commit()

        assert resultado["fallidas"] == [("Constructora", "proveedor caído")]
        assert not recordatorio_enviado(licencia, 1)  # reintentable mañana
    finally:
        db.close()
        engine.dispose()


def test_el_correo_de_prueba_marca_es_prueba_y_el_de_pago_no():
    engine, db = _db()
    try:
        prueba = _organizacion_con_dueno(db, "Prueba Org", "prueba@example.com")
        _licencia_que_vence_en(db, prueba, 5, origen="prueba")
        pago = _organizacion_con_dueno(db, "Pago Org", "pago@example.com")
        _licencia_que_vence_en(db, pago, 5, origen="pago")

        envios = []
        enviar_recordatorios_vencimiento(
            db, remitente=lambda **kwargs: envios.append(kwargs), hoy=HOY
        )

        por_nombre = {e["organizacion_nombre"]: e for e in envios}
        assert por_nombre["Prueba Org"]["es_prueba"] is True
        assert por_nombre["Prueba Org"]["plan_nombre"] == "Prueba gratuita"
        assert por_nombre["Pago Org"]["es_prueba"] is False
        assert por_nombre["Pago Org"]["plan_nombre"] == "Plan mensual"
    finally:
        db.close()
        engine.dispose()


# ---------------------------------------------------------------------------
# La ruta del cron (secreto compartido)
# ---------------------------------------------------------------------------


@pytest.fixture
def entorno_cron(monkeypatch):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as seed:
        org = Organizacion(nombre="Cliente Cron", slug="cron")
        usuario = Usuario(email="dueno@example.com", nombre="Dueño")
        seed.add_all([org, usuario])
        seed.flush()
        seed.add(
            Membresia(
                organizacion_id=org.id, usuario_id=usuario.id, rol="propietario"
            )
        )
        seed.commit()
        datos = {"organizacion_id": org.id}

    def _db_cron(_request=None):
        db = Session()
        db.info["es_operador"] = True
        db.info["auth_email"] = "sistema@cotizat.local"
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_cron_db] = _db_cron
    try:
        yield Session, datos
    finally:
        app.dependency_overrides.pop(get_cron_db, None)
        engine.dispose()


def _cliente():
    return TestClient(app, base_url="https://cotizat.test")


def test_el_cron_rechaza_sin_secreto_o_con_secreto_incorrecto(entorno_cron, monkeypatch):
    _Session, _datos = entorno_cron
    monkeypatch.setenv("CRON_SECRET", "secreto-correcto")

    with _cliente() as client:
        sin_cabecera = client.get("/api/cron/recordatorios-vencimiento")
        secreto_mal = client.get(
            "/api/cron/recordatorios-vencimiento",
            headers={"Authorization": "Bearer secreto-incorrecto"},
        )

    assert sin_cabecera.status_code == 401
    assert secreto_mal.status_code == 401

    monkeypatch.delenv("CRON_SECRET", raising=False)
    with _cliente() as client:
        sin_secreto = client.get("/api/cron/recordatorios-vencimiento")
    assert sin_secreto.status_code == 401


def test_el_cron_envia_con_el_secreto_correcto(entorno_cron, monkeypatch):
    Session, datos = entorno_cron
    monkeypatch.setenv("CRON_SECRET", "secreto-correcto")

    with Session() as db:
        organizacion = db.get(Organizacion, datos["organizacion_id"])
        # El cron trabaja sobre `date.today()`, no sobre una fecha fija.
        _licencia_que_vence_en(db, organizacion, 5, hoy=date.today())

    envios = []
    monkeypatch.setattr(
        email_module,
        "enviar_recordatorio_vencimiento",
        lambda **kwargs: envios.append(kwargs),
    )

    with _cliente() as client:
        respuesta = client.get(
            "/api/cron/recordatorios-vencimiento",
            headers={"Authorization": "Bearer secreto-correcto"},
        )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["ok"] is True
    assert cuerpo["resumen"]["enviados"] == 1
    assert [e["email"] for e in envios] == ["dueno@example.com"]
    assert envios[0]["dias_restantes"] == 5


# ---------------------------------------------------------------------------
# El correo premium (contenido y enlaces)
# ---------------------------------------------------------------------------


class _FakeHTTPResponse:
    def __init__(self, body=b'{"id":"resend-recordatorio-1"}'):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, _size=-1):
        return self.body


def test_el_correo_es_premium_con_cta_al_checkout_y_reply_to_soporte(monkeypatch):
    import json

    capturado = {}

    def fake_urlopen(request, timeout):
        capturado["payload"] = json.loads(request.data.decode("utf-8"))
        return _FakeHTTPResponse()

    monkeypatch.setenv("RESEND_API_KEY", "re_prueba")
    monkeypatch.setenv("COTIZAT_EMAIL_FROM", "CotizaT <no-responder@cotizat.test>")
    monkeypatch.setenv("COTIZAT_PUBLIC_URL", "https://cotizat.test")
    monkeypatch.setattr(email_module, "urlopen", fake_urlopen)

    envio_id = email_module.enviar_recordatorio_vencimiento(
        email="dueno@example.com",
        organizacion_nombre="Constructora",
        plan_nombre="Plan mensual",
        es_prueba=False,
        vence=date(2026, 8, 22),
        dias_restantes=5,
    )

    assert envio_id == "resend-recordatorio-1"
    payload = capturado["payload"]
    assert payload["to"] == ["dueno@example.com"]
    assert payload["reply_to"] == "soporte@cotizat.online"
    assert "vence en 5 días" in payload["subject"]

    html = payload["html"]
    # Marca y cuenta atrás presentes, y el CTA apunta al checkout (no a mailto).
    assert "CotizaT" in html
    assert "5" in html
    assert "días restantes" in html
    assert 'href="https://cotizat.test/pago"' in html
    assert "Renovar mi plan" in html
    assert "no se borran" in html
    # Sin HTML crudo inyectable.
    assert "<script>" not in html

    assert "Renueva tu plan aquí:" in payload["text"]
    assert "https://cotizat.test/pago" in payload["text"]


def test_el_correo_de_prueba_dice_elegir_plan(monkeypatch):
    import json

    capturado = {}

    def fake_urlopen(request, timeout):
        capturado["payload"] = json.loads(request.data.decode("utf-8"))
        return _FakeHTTPResponse()

    monkeypatch.setenv("RESEND_API_KEY", "re_prueba")
    monkeypatch.setenv("COTIZAT_EMAIL_FROM", "CotizaT <no-responder@cotizat.test>")
    monkeypatch.setenv("COTIZAT_PUBLIC_URL", "https://cotizat.test")
    monkeypatch.setattr(email_module, "urlopen", fake_urlopen)

    email_module.enviar_recordatorio_vencimiento(
        email="dueno@example.com",
        organizacion_nombre="Constructora",
        plan_nombre="Prueba gratuita",
        es_prueba=True,
        vence=date(2026, 8, 18),
        dias_restantes=1,
    )

    payload = capturado["payload"]
    assert "Último día de tu acceso" in payload["subject"]
    assert "Elegir un plan" in payload["html"]
    assert "prueba gratuita" in payload["html"]
