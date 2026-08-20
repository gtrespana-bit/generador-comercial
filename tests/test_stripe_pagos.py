"""Cobro con Stripe Checkout en suscripción recurrente.

Cubre la decisión 20/08/2026 (Stripe Checkout, suscripción recurrente, todo en
USD, los 5 países del selector):

- Venezuela conserva los canales manuales y añade la tarjeta al final;
  el resto de mercados abre con Stripe y deja la cripto manual de respaldo.
- La compra con Stripe no exige comprobante: nace pendiente, el checkout crea
  la suscripción y ``invoice.paid`` concede/renueva la licencia reflejando el
  ``current_period_end`` (idempotente).
- El webhook verifica la firma siempre; sin firma válida no se concede nada.
"""
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.datos_pago import PLANES, es_metodo_online, metodos_para_pais
from app.database import Base, get_db, get_db_renovacion, get_stripe_webhook_db
from app.main import app
from app.models import CompraPlan, Configuracion, Licencia
from app.services import stripe_pagos
from app.services.compras import (
    GestionCompraError,
    activar_compra_stripe,
    cancelar_compra_stripe,
    compra_por_suscripcion_stripe,
    crear_compra_stripe,
    registrar_sesion_stripe,
)


def _cliente():
    return TestClient(app, base_url="https://cotizat.test")


def _configurar_stripe(monkeypatch):
    """Claves y precios de Stripe: deja la tarjeta disponible en el checkout."""
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_prueba")
    monkeypatch.setenv("STRIPE_PRICE_ANUAL", "price_anual_test")
    monkeypatch.setenv("STRIPE_PRICE_MENSUAL", "price_mensual_test")


# ---------------------------------------------------------------------------
# Métodos por país
# ---------------------------------------------------------------------------


def test_venezuela_conserva_manual_y_anade_tarjeta():
    metodos = metodos_para_pais("VE")
    assert list(metodos) == ["pago_movil", "binance", "kontigo", "usdt", "stripe"]
    assert es_metodo_online("stripe") is True
    assert es_metodo_online("pago_movil") is False
    assert es_metodo_online("paypal") is False  # método inexistente


@pytest.mark.parametrize("codigo", ["CO", "MX", "EC", "PE"])
def test_resto_de_mercados_abre_con_stripe(codigo):
    metodos = metodos_para_pais(codigo)
    assert list(metodos)[0] == "stripe"
    assert "binance" in metodos and "usdt" in metodos
    assert "pago_movil" not in metodos and "kontigo" not in metodos


def test_pais_desconocido_cae_en_generico():
    assert list(metodos_para_pais("")) == ["stripe", "usdt"]
    assert list(metodos_para_pais("ZZ")) == ["stripe", "usdt"]


def test_stripe_configurado_exige_clave_y_precios(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    monkeypatch.delenv("STRIPE_PRICE_ANUAL", raising=False)
    monkeypatch.delenv("STRIPE_PRICE_MENSUAL", raising=False)
    assert stripe_pagos.stripe_configurado() is False
    monkeypatch.setenv("STRIPE_PRICE_ANUAL", "price_a")
    monkeypatch.setenv("STRIPE_PRICE_MENSUAL", "price_m")
    assert stripe_pagos.stripe_configurado() is True


# ---------------------------------------------------------------------------
# Registro y activación de la compra con Stripe
# ---------------------------------------------------------------------------


def test_crear_compra_stripe_no_exige_comprobante(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        compra = crear_compra_stripe(
            db,
            organizacion_id=ids[0],
            plan="anual",
            stripe_session_id="cs_test_123",
            pais_codigo="CO",
            creada_por_usuario_id=ids[1],
            creada_por_email="duena@example.com",
        )
        assert compra.estado == "pendiente"
        assert compra.metodo_pago == "stripe"
        assert compra.comprobante_reference == ""
        assert compra.importe == 89.0
        assert compra.moneda == "USD"
        assert compra.stripe_session_id == "cs_test_123"
        assert compra.pais_codigo == "CO"


def test_crear_compra_stripe_exige_sesion(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        with pytest.raises(GestionCompraError, match="sesión"):
            crear_compra_stripe(
                db, organizacion_id=ids[0], plan="mensual", stripe_session_id=""
            )


def test_registrar_sesion_stripe_vincula_suscripcion_y_cliente(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        crear_compra_stripe(
            db, organizacion_id=ids[0], plan="anual", stripe_session_id="cs_1"
        )
        db.flush()
        compra = registrar_sesion_stripe(
            db,
            session_id="cs_1",
            subscription_id="sub_1",
            customer_id="cus_1",
            payment_intent="pi_1",
        )
        assert compra.stripe_subscription_id == "sub_1"
        assert compra.stripe_customer_id == "cus_1"
        assert compra.stripe_payment_intent == "pi_1"


def test_activar_compra_stripe_concede_licencia_del_plan(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        crear_compra_stripe(
            db, organizacion_id=ids[0], plan="anual", stripe_session_id="cs_1"
        )
        registrar_sesion_stripe(
            db, session_id="cs_1", subscription_id="sub_1", customer_id="cus_1"
        )
        db.flush()
        vence = date(2026, 8, 20) + timedelta(days=365)
        compra, licencia = activar_compra_stripe(
            db,
            subscription_id="sub_1",
            vence=vence,
            operador_email="stripe@cotizat.local",
        )
        assert compra.estado == "activa"
        assert compra.licencia_id == licencia.id
        assert licencia.origen == "pago"
        assert licencia.importe == 89.0
        assert licencia.metodo_cobro == "Tarjeta (Stripe)"
        assert licencia.referencia == "sub_1"
        assert licencia.vence == vence
        # Se encadena tras la licencia de cortesía del fixture, así que el
        # inicio puede ser posterior a hoy, pero el vencimiento es el pagado.
        assert licencia.inicio >= date.today()


def test_activar_compra_stripe_es_idempotente(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        crear_compra_stripe(
            db, organizacion_id=ids[0], plan="mensual", stripe_session_id="cs_2"
        )
        registrar_sesion_stripe(db, session_id="cs_2", subscription_id="sub_2")
        db.flush()
        vence = date(2026, 8, 20) + timedelta(days=30)
        compra1, licencia1 = activar_compra_stripe(
            db, subscription_id="sub_2", vence=vence,
            operador_email="stripe@cotizat.local",
        )
        # Reintento del webhook (mismo vence): no duplica ni cambia la licencia.
        compra2, licencia2 = activar_compra_stripe(
            db, subscription_id="sub_2", vence=vence,
            operador_email="stripe@cotizat.local",
        )
        assert compra1.id == compra2.id
        assert licencia1.id == licencia2.id
        licencias_de_pago = db.query(Licencia).filter(
            Licencia.organizacion_id == ids[0], Licencia.origen == "pago"
        ).count()
        assert licencias_de_pago == 1


def test_renovar_extiende_la_licencia_hasta_current_period_end(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        crear_compra_stripe(
            db, organizacion_id=ids[0], plan="mensual", stripe_session_id="cs_3"
        )
        registrar_sesion_stripe(db, session_id="cs_3", subscription_id="sub_3")
        db.flush()
        primer_vence = date(2026, 9, 19)
        _, licencia = activar_compra_stripe(
            db, subscription_id="sub_3", vence=primer_vence,
            operador_email="stripe@cotizat.local",
        )
        assert licencia.vence == primer_vence

        # Renovación mensual: el período pagado llega más lejos.
        segundo_vence = date(2026, 10, 19)
        _, licencia = activar_compra_stripe(
            db, subscription_id="sub_3", vence=segundo_vence,
            operador_email="stripe@cotizat.local",
        )
        assert licencia.vence == segundo_vence
        # Sigue siendo UNA licencia de pago: la renovación la extiende, no crea otra.
        licencias_de_pago = db.query(Licencia).filter(
            Licencia.organizacion_id == ids[0], Licencia.origen == "pago"
        ).count()
        assert licencias_de_pago == 1


def test_activar_compra_stripe_rechaza_suscripcion_desconocida(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        with pytest.raises(GestionCompraError, match="No hay compra"):
            activar_compra_stripe(
                db, subscription_id="sub_nope", vence=date(2027, 1, 1),
                operador_email="stripe@cotizat.local",
            )


def test_cancelar_compra_stripe_la_marca_cancelada(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        crear_compra_stripe(
            db, organizacion_id=ids[0], plan="mensual", stripe_session_id="cs_4"
        )
        registrar_sesion_stripe(db, session_id="cs_4", subscription_id="sub_4")
        db.flush()
        activar_compra_stripe(
            db, subscription_id="sub_4", vence=date(2026, 9, 19),
            operador_email="stripe@cotizat.local",
        )
        compra = cancelar_compra_stripe(
            db, subscription_id="sub_4", operador_email="stripe@cotizat.local"
        )
        assert compra.estado == "cancelada"
        assert compra_por_suscripcion_stripe(db, "sub_4").estado == "cancelada"


# ---------------------------------------------------------------------------
# Creación de la sesión de Checkout (suscripción)
# ---------------------------------------------------------------------------


def test_crear_sesion_sin_configuracion(monkeypatch):
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    with pytest.raises(stripe_pagos.StripeNoConfigurado):
        stripe_pagos.crear_sesion_checkout(
            plan="anual",
            ficha=PLANES["anual"],
            organizacion_id=1,
            codigo_pais="CO",
            email="",
            organizacion_nombre="",
            success_url="https://x.test/s",
            cancel_url="https://x.test/c",
        )


def test_crear_sesion_usa_modo_suscripcion_y_precio_recurrente(monkeypatch):
    import stripe

    class _SesionFalsa:
        id = "cs_test_abc"
        url = "https://checkout.stripe.com/c/pay/cs_test_abc"
        kwargs = {}

        @classmethod
        def create(cls, **kwargs):
            cls.kwargs = kwargs
            return cls()

    _configurar_stripe(monkeypatch)
    monkeypatch.setattr(stripe.checkout, "Session", _SesionFalsa)

    session_id, url = stripe_pagos.crear_sesion_checkout(
        plan="anual",
        ficha=PLANES["anual"],
        organizacion_id=7,
        codigo_pais="CO",
        email="duena@example.com",
        organizacion_nombre="Constructora",
        success_url="https://x.test/s",
        cancel_url="https://x.test/c",
    )

    assert session_id == "cs_test_abc"
    assert url == "https://checkout.stripe.com/c/pay/cs_test_abc"
    assert _SesionFalsa.kwargs["mode"] == "subscription"
    assert _SesionFalsa.kwargs["client_reference_id"] == "7"
    assert _SesionFalsa.kwargs["metadata"]["plan"] == "anual"
    assert _SesionFalsa.kwargs["metadata"]["pais"] == "CO"
    assert _SesionFalsa.kwargs["subscription_data"]["metadata"]["plan"] == "anual"
    linea = _SesionFalsa.kwargs["line_items"][0]
    assert linea["price"] == "price_anual_test"
    assert "price_data" not in linea  # el precio recurrente vive en Stripe


def test_crear_sesion_mensual_usa_su_precio(monkeypatch):
    import stripe

    class _SesionFalsa:
        id = "cs_test_m"
        url = "https://checkout.stripe.com/c/pay/cs_test_m"
        kwargs = {}

        @classmethod
        def create(cls, **kwargs):
            cls.kwargs = kwargs
            return cls()

    _configurar_stripe(monkeypatch)
    monkeypatch.setattr(stripe.checkout, "Session", _SesionFalsa)

    stripe_pagos.crear_sesion_checkout(
        plan="mensual",
        ficha=PLANES["mensual"],
        organizacion_id=7,
        codigo_pais="MX",
        email="",
        organizacion_nombre="",
        success_url="https://x.test/s",
        cancel_url="https://x.test/c",
    )
    assert _SesionFalsa.kwargs["line_items"][0]["price"] == "price_mensual_test"


# ---------------------------------------------------------------------------
# Firma del webhook
# ---------------------------------------------------------------------------


def test_verificar_evento_sin_secreto_rechaza(monkeypatch):
    monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)
    with pytest.raises(stripe_pagos.StripeFirmaInvalida):
        stripe_pagos.verificar_evento(b"{}", "t=1,v1=sig")


def test_verificar_evento_con_firma_invalida_rechaza(monkeypatch):
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_prueba")
    with pytest.raises(stripe_pagos.StripeFirmaInvalida):
        stripe_pagos.verificar_evento(b'{"type":"x"}', "t=abc,v1=deadbeef")


# ---------------------------------------------------------------------------
# Rutas: checkout por país y webhook
# ---------------------------------------------------------------------------


def _instalar_override(db, ids):
    def _get_db(request=None):
        db.info["organizacion_id"] = ids[0]
        db.info["usuario_id"] = ids[1]
        db.info["rol_membresia"] = "propietario"
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_db_renovacion] = _get_db
    app.dependency_overrides[get_stripe_webhook_db] = _get_db


def _retirar_override():
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_db_renovacion, None)
    app.dependency_overrides.pop(get_stripe_webhook_db, None)


def test_checkout_muestra_metodos_de_venezuela(entorno, monkeypatch):
    _configurar_stripe(monkeypatch)
    Session, ids, _rol = entorno
    with Session() as db:
        _instalar_override(db, ids)
        try:
            with _cliente() as client:
                r = client.get("/pago/comprar?plan=anual")
            assert r.status_code == 200
            assert "Pago m" in r.text
            assert "Binance" in r.text
            assert "Kontigo" in r.text
            assert "USDT" in r.text
            assert "Tarjeta (Stripe)" in r.text
        finally:
            _retirar_override()


def test_checkout_muestra_stripe_primero_fuera_de_venezuela(entorno, monkeypatch):
    _configurar_stripe(monkeypatch)
    Session, ids, _rol = entorno
    with Session() as db:
        cfg = db.query(Configuracion).first()
        cfg.empresa_pais = "Colombia"
        db.commit()
        _instalar_override(db, ids)
        try:
            with _cliente() as client:
                r = client.get("/pago/comprar?plan=anual")
            assert r.status_code == 200
            assert "Tarjeta (Stripe)" in r.text
            # Fuera de Venezuela no se ofrecen los canales manuales venezolanos.
            assert "móvil" not in r.text
            assert "Kontigo" not in r.text
            assert "USDT" in r.text  # respaldo cripto
        finally:
            _retirar_override()


def test_checkout_oculta_tarjeta_sin_configuracion(entorno, monkeypatch):
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    Session, ids, _rol = entorno
    with Session() as db:
        _instalar_override(db, ids)
        try:
            with _cliente() as client:
                r = client.get("/pago/comprar?plan=anual")
            assert r.status_code == 200
            assert "Tarjeta (Stripe)" not in r.text
            assert "USDT" in r.text  # el respaldo manual sigue disponible
        finally:
            _retirar_override()


def test_webhook_rechaza_firma_invalida(entorno, monkeypatch):
    Session, ids, _rol = entorno
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_prueba")
    with Session() as db:
        _instalar_override(db, ids)
        try:
            with _cliente() as client:
                r = client.post(
                    "/api/stripe/webhook",
                    content=b'{"type":"checkout.session.completed"}',
                    headers={"Stripe-Signature": "t=abc,v1=deadbeef"},
                )
            assert r.status_code == 400
            assert r.json()["ok"] is False
        finally:
            _retirar_override()


def test_webhook_checkout_completed_activa_compra(entorno, monkeypatch):
    from app.routers import stripe as stripe_router

    Session, ids, _rol = entorno
    compra_id = None
    with Session() as db:
        compra = crear_compra_stripe(
            db,
            organizacion_id=ids[0],
            plan="anual",
            stripe_session_id="cs_webhook_1",
            pais_codigo="CO",
        )
        db.commit()
        compra_id = compra.id

    evento = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_webhook_1",
                "subscription": "sub_webhook_1",
                "customer": "cus_webhook_1",
                "payment_intent": "pi_webhook_1",
            }
        },
    }
    monkeypatch.setattr(stripe_router, "verificar_evento", lambda payload, firma: evento)
    monkeypatch.setattr(
        stripe_router,
        "obtener_suscripcion",
        lambda sub_id: {
            "id": sub_id,
            "status": "active",
            "current_period_end": date(2027, 8, 20),
            "customer": "cus_webhook_1",
        },
    )

    with Session() as db:
        _instalar_override(db, ids)
        try:
            with _cliente() as client:
                r = client.post(
                    "/api/stripe/webhook",
                    content=b'{"type":"checkout.session.completed"}',
                    headers={"Stripe-Signature": "t=abc,v1=sig"},
                )
            assert r.status_code == 200
            assert r.json()["ok"] is True
            assert r.json()["compra"] == compra_id
        finally:
            _retirar_override()

    with Session() as db:
        compra = db.query(CompraPlan).filter(CompraPlan.id == compra_id).first()
        assert compra.estado == "activa"
        assert compra.licencia_id is not None
        assert compra.stripe_subscription_id == "sub_webhook_1"
        assert compra.stripe_customer_id == "cus_webhook_1"
        assert compra.stripe_payment_intent == "pi_webhook_1"


def test_webhook_invoice_paid_extiende_la_licencia(entorno, monkeypatch):
    from app.routers import stripe as stripe_router

    Session, ids, _rol = entorno
    with Session() as db:
        crear_compra_stripe(
            db,
            organizacion_id=ids[0],
            plan="mensual",
            stripe_session_id="cs_webhook_2",
        )
        registrar_sesion_stripe(
            db, session_id="cs_webhook_2", subscription_id="sub_webhook_2"
        )
        activar_compra_stripe(
            db,
            subscription_id="sub_webhook_2",
            vence=date(2026, 9, 19),
            operador_email="stripe@cotizat.local",
        )
        db.commit()

    evento = {
        "type": "invoice.paid",
        "data": {"object": {"id": "in_1", "subscription": "sub_webhook_2"}},
    }
    monkeypatch.setattr(stripe_router, "verificar_evento", lambda payload, firma: evento)
    monkeypatch.setattr(
        stripe_router,
        "obtener_suscripcion",
        lambda sub_id: {
            "id": sub_id,
            "status": "active",
            "current_period_end": date(2026, 10, 19),
            "customer": "cus_webhook_2",
        },
    )

    with Session() as db:
        _instalar_override(db, ids)
        try:
            with _cliente() as client:
                r = client.post(
                    "/api/stripe/webhook",
                    content=b'{"type":"invoice.paid"}',
                    headers={"Stripe-Signature": "t=abc,v1=sig"},
                )
            assert r.status_code == 200
            assert r.json()["ok"] is True
        finally:
            _retirar_override()

    with Session() as db:
        compra = compra_por_suscripcion_stripe(db, "sub_webhook_2")
        assert compra.licencia.vence == date(2026, 10, 19)


def test_webhook_subscription_deleted_cancela_la_compra(entorno, monkeypatch):
    from app.routers import stripe as stripe_router

    Session, ids, _rol = entorno
    with Session() as db:
        crear_compra_stripe(
            db,
            organizacion_id=ids[0],
            plan="mensual",
            stripe_session_id="cs_webhook_3",
        )
        registrar_sesion_stripe(
            db, session_id="cs_webhook_3", subscription_id="sub_webhook_3"
        )
        activar_compra_stripe(
            db,
            subscription_id="sub_webhook_3",
            vence=date(2026, 9, 19),
            operador_email="stripe@cotizat.local",
        )
        db.commit()

    evento = {
        "type": "customer.subscription.deleted",
        "data": {"object": {"id": "sub_webhook_3", "status": "canceled"}},
    }
    monkeypatch.setattr(stripe_router, "verificar_evento", lambda payload, firma: evento)

    with Session() as db:
        _instalar_override(db, ids)
        try:
            with _cliente() as client:
                r = client.post(
                    "/api/stripe/webhook",
                    content=b'{"type":"customer.subscription.deleted"}',
                    headers={"Stripe-Signature": "t=abc,v1=sig"},
                )
            assert r.status_code == 200
        finally:
            _retirar_override()

    with Session() as db:
        compra = compra_por_suscripcion_stripe(db, "sub_webhook_3")
        assert compra.estado == "cancelada"
        # El acceso no se revoca: la licencia sigue hasta el día pagado.
        assert compra.licencia.vence == date(2026, 9, 19)
