"""Cobro con Stripe Checkout: sesión, firma del webhook y activación."""
from datetime import date, timedelta
import hashlib
import hmac
import json
import time
from urllib.parse import unquote

import pytest
from fastapi.testclient import TestClient

from app.database import get_db, get_db_renovacion, get_stripe_webhook_db
from app.datos_pago import METODO_STRIPE
from app.main import app
from app.models import CompraPlan, Licencia
from app.services.compras import crear_compra
from app.services.stripe import (
    StripeNotConfigured,
    StripeWebhookError,
    cumplir_sesion_checkout,
    importe_a_centavos,
    procesar_evento_webhook,
    stripe_configurado,
    verificar_firma_webhook,
)


AUTH_ID = "7a3c5f9e-2b41-4d8c-a6f3-19e8d0c42b11"
WEBHOOK_SECRET = "whsec_prueba_de_firma_stripe_123456"


def _cliente():
    return TestClient(app, base_url="https://cotizat.test")


def _instalar_override(db, ids):
    from app.database import get_db_renovacion as renovacion

    def _get_db(request=None):
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[renovacion] = _get_db
    app.dependency_overrides[get_stripe_webhook_db] = _get_db


def _retirar_override():
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_db_renovacion, None)
    app.dependency_overrides.pop(get_stripe_webhook_db, None)


def _firmar(payload: bytes, secret: str = WEBHOOK_SECRET, timestamp: int | None = None) -> str:
    ts = int(timestamp if timestamp is not None else time.time())
    digest = hmac.new(
        secret.encode("utf-8"),
        f"{ts}.".encode("ascii") + payload,
        hashlib.sha256,
    ).hexdigest()
    return f"t={ts},v1={digest}"


def test_importe_a_centavos_redondea_half_up():
    assert importe_a_centavos(89.0) == 8900
    assert importe_a_centavos(9.99) == 999
    assert importe_a_centavos(10.005) == 1001


def test_stripe_no_configurado_sin_clave(monkeypatch):
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)
    assert stripe_configurado() is False


def test_stripe_configurado_con_clave_de_prueba(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_1234567890abcdefghijklmn")
    monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)
    assert stripe_configurado() is True


def test_clave_invalida_no_cuenta_como_configurada(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "pk_test_no_es_secreta")
    assert stripe_configurado() is False


def test_pagina_comprar_sin_stripe_no_muestra_tarjeta(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        db.info["usuario_id"] = ids[1]
        db.info["rol_membresia"] = "propietario"
        _instalar_override(db, ids)
        try:
            with _cliente() as client:
                r = client.get("/pago/comprar?plan=anual")
        finally:
            _retirar_override()
    assert r.status_code == 200
    assert "/pago/stripe/checkout" not in r.text
    assert "Pago m" in r.text


def test_pagina_comprar_con_stripe_muestra_boton_de_tarjeta(entorno, monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_1234567890abcdefghijklmn")
    Session, ids, _rol = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        db.info["usuario_id"] = ids[1]
        db.info["rol_membresia"] = "propietario"
        _instalar_override(db, ids)
        try:
            with _cliente() as client:
                r = client.get("/pago/comprar?plan=anual")
        finally:
            _retirar_override()
    assert r.status_code == 200
    assert "/pago/stripe/checkout" in r.text
    assert "Pagar 89.00 US$ con tarjeta" in r.text
    assert "Pago m" in r.text


def test_checkout_sin_stripe_vuelve_al_manual(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        db.info["usuario_id"] = ids[1]
        db.info["rol_membresia"] = "propietario"
        _instalar_override(db, ids)
        try:
            with _cliente() as client:
                r = client.post(
                    "/pago/stripe/checkout",
                    data={"plan": "anual"},
                    follow_redirects=False,
                )
        finally:
            _retirar_override()
    assert r.status_code == 303
    assert "tarjeta no está disponible" in unquote(r.headers["location"])


def test_checkout_redirige_a_stripe(entorno, monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_1234567890abcdefghijklmn")
    monkeypatch.setenv("COTIZAT_PUBLIC_URL", "https://cotizat.test")

    def fake_sesion(**kwargs):
        assert kwargs["plan"] == "mensual"
        assert kwargs["organizacion_id"] == ids[0]
        return {
            "id": "cs_test_sesion_1",
            "url": "https://checkout.stripe.com/c/pay/cs_test_sesion_1",
        }

    monkeypatch.setattr(
        "app.services.stripe.crear_sesion_checkout", fake_sesion
    )
    Session, ids, _rol = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        db.info["usuario_id"] = ids[1]
        db.info["rol_membresia"] = "propietario"
        _instalar_override(db, ids)
        try:
            with _cliente() as client:
                r = client.post(
                    "/pago/stripe/checkout",
                    data={"plan": "mensual"},
                    follow_redirects=False,
                )
        finally:
            _retirar_override()
    assert r.status_code == 303
    assert r.headers["location"].startswith("https://checkout.stripe.com/")

    with Session() as db:
        compra = db.query(CompraPlan).order_by(CompraPlan.id.desc()).first()
        assert compra is not None
        assert compra.metodo_pago == METODO_STRIPE
        assert compra.estado == "pendiente"
        assert compra.stripe_checkout_session_id == "cs_test_sesion_1"
        assert compra.comprobante_reference == ""


def test_firma_webhook_valida(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_1234567890abcdefghijklmn")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WEBHOOK_SECRET)
    payload = b'{"type":"checkout.session.completed","data":{"object":{}}}'
    evento = verificar_firma_webhook(payload, _firmar(payload))
    assert evento["type"] == "checkout.session.completed"


def test_firma_webhook_caducada(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_1234567890abcdefghijklmn")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WEBHOOK_SECRET)
    payload = b'{"type":"checkout.session.completed"}'
    with pytest.raises(StripeWebhookError, match="caducada"):
        verificar_firma_webhook(payload, _firmar(payload, timestamp=int(time.time()) - 400))


def test_firma_webhook_falsa(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_1234567890abcdefghijklmn")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WEBHOOK_SECRET)
    payload = b'{"type":"checkout.session.completed"}'
    with pytest.raises(StripeWebhookError, match="no coincide"):
        verificar_firma_webhook(
            payload, f"t={int(time.time())},v1={'ab' * 32}"
        )


def test_webhook_sin_secreto_devuelve_503(entorno, monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_1234567890abcdefghijklmn")
    monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)
    Session, ids, _rol = entorno
    with Session() as db:
        _instalar_override(db, ids)
        try:
            with _cliente() as client:
                r = client.post(
                    "/pago/stripe/webhook",
                    content=b"{}",
                    headers={"stripe-signature": "t=1,v1=ab"},
                )
        finally:
            _retirar_override()
    assert r.status_code == 503


def test_webhook_activa_la_licencia(entorno, monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_1234567890abcdefghijklmn")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WEBHOOK_SECRET)
    Session, ids, _rol = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        compra = crear_compra(
            db,
            organizacion_id=ids[0],
            plan="anual",
            metodo_pago=METODO_STRIPE,
            datos_verificacion={},
            comprobante_reference="",
            comprobante_nombre="",
            comprobante_mime="",
            creada_por_usuario_id=ids[1],
            creada_por_email="duena@example.com",
            exigir_comprobante=False,
        )
        compra.stripe_checkout_session_id = "cs_test_pagada"
        db.commit()
        compra_id = compra.id

        evento = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_pagada",
                    "payment_status": "paid",
                    "status": "complete",
                    "subscription": "sub_test_1",
                    "customer": "cus_test_1",
                    "metadata": {"compra_id": str(compra_id), "plan": "anual"},
                }
            },
        }
        payload = json.dumps(evento).encode("utf-8")
        _instalar_override(db, ids)
        try:
            with _cliente() as client:
                r = client.post(
                    "/pago/stripe/webhook",
                    content=payload,
                    headers={"stripe-signature": _firmar(payload)},
                )
        finally:
            _retirar_override()
    assert r.status_code == 200
    assert r.json()["ok"] is True

    with Session() as db:
        compra = db.get(CompraPlan, compra_id)
        assert compra.estado == "activa"
        assert compra.licencia_id is not None
        assert compra.stripe_subscription_id == "sub_test_1"
        licencia = db.get(Licencia, compra.licencia_id)
        assert licencia.origen == "pago"
        assert licencia.importe == 89.0
        assert (licencia.vence - licencia.inicio).days >= 364


def test_cumplir_sesion_es_idempotente(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        compra = crear_compra(
            db,
            organizacion_id=ids[0],
            plan="mensual",
            metodo_pago=METODO_STRIPE,
            datos_verificacion={},
            comprobante_reference="",
            comprobante_nombre="",
            comprobante_mime="",
            creada_por_usuario_id=ids[1],
            creada_por_email="duena@example.com",
            exigir_comprobante=False,
        )
        compra.stripe_checkout_session_id = "cs_test_idem"
        db.flush()
        sesion = {
            "id": "cs_test_idem",
            "payment_status": "paid",
            "status": "complete",
            "subscription": "sub_x",
            "metadata": {"compra_id": str(compra.id)},
        }
        primera = cumplir_sesion_checkout(db, sesion)
        segunda = cumplir_sesion_checkout(db, sesion)
        assert primera.id == segunda.id
        assert primera.estado == "activa"
        assert (
            db.query(Licencia)
            .filter(
                Licencia.organizacion_id == ids[0],
                Licencia.origen == "pago",
            )
            .count()
            == 1
        )


def test_factura_de_renovacion_encadena_licencia(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        compra = crear_compra(
            db,
            organizacion_id=ids[0],
            plan="mensual",
            metodo_pago=METODO_STRIPE,
            datos_verificacion={},
            comprobante_reference="",
            comprobante_nombre="",
            comprobante_mime="",
            creada_por_usuario_id=ids[1],
            creada_por_email="duena@example.com",
            exigir_comprobante=False,
        )
        compra.stripe_checkout_session_id = "cs_test_ren"
        compra.stripe_subscription_id = "sub_ren"
        db.flush()
        cumplir_sesion_checkout(
            db,
            {
                "id": "cs_test_ren",
                "payment_status": "paid",
                "subscription": "sub_ren",
                "metadata": {"compra_id": str(compra.id)},
            },
        )
        evento = {
            "type": "invoice.paid",
            "data": {
                "object": {
                    "id": "in_ren_2",
                    "paid": True,
                    "status": "paid",
                    "subscription": "sub_ren",
                    "billing_reason": "subscription_cycle",
                }
            },
        }
        renovacion = procesar_evento_webhook(db, evento)
        assert renovacion is not None
        assert renovacion.id != compra.id
        assert renovacion.estado == "activa"
        licencias = (
            db.query(Licencia)
            .filter(
                Licencia.organizacion_id == ids[0],
                Licencia.origen == "pago",
            )
            .order_by(Licencia.inicio)
            .all()
        )
        assert len(licencias) == 2
        assert licencias[1].inicio == licencias[0].vence + timedelta(days=1)


def test_primera_factura_no_duplica_la_licencia(entorno):
    """checkout.session.completed y invoice.paid (alta) son el mismo cobro."""
    Session, ids, _rol = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        compra = crear_compra(
            db,
            organizacion_id=ids[0],
            plan="mensual",
            metodo_pago=METODO_STRIPE,
            datos_verificacion={},
            comprobante_reference="",
            comprobante_nombre="",
            comprobante_mime="",
            creada_por_usuario_id=ids[1],
            creada_por_email="duena@example.com",
            exigir_comprobante=False,
        )
        compra.stripe_checkout_session_id = "cs_test_primera"
        compra.stripe_subscription_id = "sub_primera"
        db.flush()
        cumplir_sesion_checkout(
            db,
            {
                "id": "cs_test_primera",
                "payment_status": "paid",
                "subscription": "sub_primera",
                "metadata": {"compra_id": str(compra.id)},
            },
        )
        segunda = procesar_evento_webhook(
            db,
            {
                "type": "invoice.paid",
                "data": {
                    "object": {
                        "id": "in_primera",
                        "paid": True,
                        "status": "paid",
                        "subscription": "sub_primera",
                        "billing_reason": "subscription_create",
                    }
                },
            },
        )
        assert segunda is not None
        assert segunda.id == compra.id
        assert (
            db.query(Licencia)
            .filter(
                Licencia.organizacion_id == ids[0],
                Licencia.origen == "pago",
            )
            .count()
            == 1
        )


def test_csrf_no_bloquea_el_webhook():
    from starlette.applications import Starlette
    from starlette.middleware import Middleware
    from starlette.responses import PlainTextResponse
    from starlette.routing import Route
    from app.security import WebSecurityMiddleware

    async def endpoint(_request):
        return PlainTextResponse("ok")

    app_segura = Starlette(
        routes=[Route("/pago/stripe/webhook", endpoint, methods=["POST"])],
        middleware=[Middleware(WebSecurityMiddleware, enforce_csrf=True)],
    )
    with TestClient(app_segura, base_url="https://cotizat.test") as client:
        r = client.post("/pago/stripe/webhook")
    assert r.status_code == 200


def test_el_webhook_avisa_al_titular_de_la_venta(entorno, monkeypatch):
    """El titular no puede enterarse de un cobro por el banco.

    La primera venta real de 2026-10 se descubrió por un correo de Stripe:
    el webhook activaba la licencia, avisaba al comprador… y al titular no le
    llegaba nada. Este test fija el aviso al buzón de soporte, que es el
    requisito declarado como más prioritario de todo el encargo.
    """
    import os

    from app.services import email as email_module

    capturado = []

    class _Respuesta:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, _size=-1):
            return b'{"id":"venta-1"}'

    def fake_urlopen(request, timeout):  # noqa: ARG001
        capturado.append(json.loads(request.data.decode("utf-8")))
        return _Respuesta()

    monkeypatch.setenv("RESEND_API_KEY", "re_prueba")
    monkeypatch.setenv("COTIZAT_EMAIL_FROM", "CotizaT <no-responder@cotizat.test>")
    monkeypatch.delenv("COTIZAT_AVISOS_EMAIL", raising=False)
    monkeypatch.setattr(email_module, "urlopen", fake_urlopen)
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_1234567890abcdefghijklmn")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WEBHOOK_SECRET)

    Session, ids, _rol = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        compra = crear_compra(
            db,
            organizacion_id=ids[0],
            plan="mensual",
            metodo_pago=METODO_STRIPE,
            datos_verificacion={},
            comprobante_reference="",
            comprobante_nombre="",
            comprobante_mime="",
            creada_por_usuario_id=ids[1],
            creada_por_email="duena@example.com",
            exigir_comprobante=False,
        )
        compra.stripe_checkout_session_id = "cs_test_aviso"
        db.commit()
        compra_id = compra.id

        evento = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_aviso",
                    "payment_status": "paid",
                    "status": "complete",
                    "subscription": "sub_test_aviso",
                    "customer": "cus_test_aviso",
                    "metadata": {"compra_id": str(compra_id), "plan": "mensual"},
                }
            },
        }
        payload = json.dumps(evento).encode("utf-8")
        _instalar_override(db, ids)
        try:
            with _cliente() as client:
                respuesta = client.post(
                    "/pago/stripe/webhook",
                    content=payload,
                    headers={"stripe-signature": _firmar(payload)},
                )
        finally:
            _retirar_override()

    assert respuesta.status_code == 200
    assert capturado, "La venta de Stripe debe avisar al buzón del titular"
    aviso = capturado[-1]
    assert aviso["to"] == ["soporte@cotizat.online"]
    assert "9,99" in aviso["subject"] or "9.99" in aviso["subject"]
    assert aviso["reply_to"] == "duena@example.com"
    assert "mensual" in aviso["html"].lower()
    assert "/admin/ingresos?tab=ventas" in aviso["text"]


# Payloads sintéticos con la estructura de la API 2026; sin datos de clientes.
def _compra_webhook(db, ids):
    compra = crear_compra(
        db, organizacion_id=ids[0], plan="mensual", metodo_pago=METODO_STRIPE,
        datos_verificacion={}, comprobante_reference="", comprobante_nombre="",
        comprobante_mime="", creada_por_usuario_id=ids[1],
        creada_por_email="test@example.test", exigir_comprobante=False,
        stripe_checkout_session_id="cs_test_2026",
    )
    db.flush()
    return compra


def _checkout_2026():
    return {"id": "cs_test_2026", "status": "complete", "payment_status": "paid",
            "subscription": "sub_test_2026", "invoice": "in_test_alta2026",
            "metadata": {"plan": "mensual", "organizacion_id": "999"}}


def _factura_2026(invoice_id="in_test_alta2026", motivo="subscription_create"):
    return {"id": invoice_id, "object": "invoice", "status": "paid",
            "billing_reason": motivo, "metadata": {},
            "parent": {"type": "subscription_details", "subscription_details": {
                "subscription": "sub_test_2026",
                "metadata": {"plan": "mensual", "organizacion_id": "999"},
            }}}


def test_factura_2026_renovacion_y_reintentos_no_duplican(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        compra = _compra_webhook(db, ids)
        cumplir_sesion_checkout(db, _checkout_2026())
        procesar_evento_webhook(db, {"type": "invoice.paid", "data": {"object": _factura_2026()}})
        renovacion_evento = {"type": "invoice.paid", "data": {
            "object": _factura_2026("in_test_ren2026", "subscription_cycle")}}
        renovacion = procesar_evento_webhook(db, renovacion_evento)
        assert renovacion.id != compra.id
        assert renovacion.stripe_invoice_id == "in_test_ren2026"
        assert renovacion.stripe_subscription_id == "sub_test_2026"
        db.commit()
        repetida = procesar_evento_webhook(db, renovacion_evento)
        assert repetida.id == renovacion.id
        assert not repetida._stripe_recien_activada
        assert db.query(Licencia).filter_by(origen="pago").count() == 2


def test_factura_antes_de_checkout_es_reintentable_y_no_se_pierde(entorno):
    from app.services.stripe import StripeFulfillmentPending
    Session, ids, _rol = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        compra = _compra_webhook(db, ids)
        db.commit()
        with pytest.raises(StripeFulfillmentPending):
            procesar_evento_webhook(db, {"type": "invoice.paid", "data": {"object": _factura_2026()}})
        db.rollback()
        cumplir_sesion_checkout(db, _checkout_2026())
        factura = procesar_evento_webhook(db, {"type": "invoice.paid", "data": {"object": _factura_2026()}})
        assert factura.id == compra.id
        assert db.query(Licencia).filter_by(origen="pago").count() == 1


def test_checkout_completo_sin_pago_no_activa(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        compra = _compra_webhook(db, ids)
        sesion = {**_checkout_2026(), "payment_status": "unpaid"}
        assert cumplir_sesion_checkout(db, sesion) is None
        assert compra.estado == "pendiente"
        assert db.query(Licencia).filter_by(origen="pago").count() == 0


def test_factura_reintentada_tras_otras_renovaciones_no_anade_periodos(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        _compra_webhook(db, ids)
        cumplir_sesion_checkout(db, _checkout_2026())
        for invoice_id in ("in_test_ren1", "in_test_ren2", "in_test_ren1", "in_test_alta2026"):
            factura = _factura_2026(invoice_id, "subscription_create" if invoice_id == "in_test_alta2026" else "subscription_cycle")
            procesar_evento_webhook(db, {"type": "invoice.paid", "data": {"object": factura}})
            db.commit()
        assert db.query(Licencia).filter_by(origen="pago").count() == 3
        assert db.query(CompraPlan).filter(CompraPlan.stripe_invoice_id.like("in_test_%")).count() == 3


def test_webhook_factura_sin_asociar_responde_503_no_200(entorno, monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_1234567890abcdefghijklmn")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WEBHOOK_SECRET)
    Session, ids, _rol = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        _compra_webhook(db, ids)
        db.commit()
        evento = {"id": "evt_test_2026", "api_version": "2026-07-29.dahlia",
                  "type": "invoice.paid", "data": {"object": _factura_2026()}}
        payload = json.dumps(evento).encode()
        _instalar_override(db, ids)
        try:
            with _cliente() as client:
                respuesta = client.post("/pago/stripe/webhook", content=payload,
                                        headers={"stripe-signature": _firmar(payload)},
                                        follow_redirects=False)
        finally:
            _retirar_override()
        assert respuesta.status_code == 503
        assert respuesta.headers["retry-after"] == "60"
        assert db.query(Licencia).filter_by(origen="pago").count() == 0


def test_lock_postgres_usa_misma_suscripcion_para_checkout_y_factura():
    from types import SimpleNamespace
    from app.services.stripe import _bloquear_cobro
    llamadas = []
    db = SimpleNamespace(get_bind=lambda: SimpleNamespace(dialect=SimpleNamespace(name="postgresql")),
                         execute=lambda statement, params: llamadas.append((str(statement), params)))
    _bloquear_cobro(db, _checkout_2026())
    _bloquear_cobro(db, _factura_2026())
    assert llamadas[0] == llamadas[1]
    assert "pg_advisory_xact_lock" in llamadas[0][0]


@pytest.mark.parametrize("host", ["https://cotizat.online", "https://www.cotizat.online"])
def test_aplicacion_recibe_post_webhook_sin_redirigir_host(entorno, monkeypatch, host):
    """No reproduce reglas de dominios del proxy/Vercel, que son externas."""
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_1234567890abcdefghijklmn")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WEBHOOK_SECRET)
    Session, ids, _rol = entorno
    with Session() as db:
        _instalar_override(db, ids)
        try:
            with TestClient(app, base_url=host) as client:
                payload = json.dumps({"type": "invoice.created", "data": {"object": {}}}).encode()
                resp = client.post("/pago/stripe/webhook", content=payload,
                                   headers={"stripe-signature": _firmar(payload)}, follow_redirects=False)
                assert resp.status_code == 200
                assert "location" not in resp.headers
                invalida = client.post("/pago/stripe/webhook", content=payload,
                                       headers={"stripe-signature": "incorrecta"}, follow_redirects=False)
                assert invalida.status_code == 400
        finally:
            _retirar_override()
