"""«Mi plan»: el cliente ve su plan, lo renueva y cambia de período.

Hasta el 2026-10-20 quien pagaba no tenía pantalla de plan: solo una tarjeta
enterrada en Configuración y un indicador de texto en la barra lateral. Esta
suite fija el contrato nuevo (`GET /mi-plan` y la renovación con tarjeta):

1. Sin plan, la página ofrece contratar con el precio y la fecha de fin.
2. Con plan, muestra cuál es, hasta cuándo llega y los botones de renovar y
   de cambiar de período **con las fechas encadenadas exactas** (el período
   nuevo empieza al terminar el actual: renovar pronto no quita días).
3. El historial lista las compras de la organización con su recibo, y una
   compra pendiente de verificación se anuncia para que nadie pague dos veces.
4. La renovación automática con Stripe se puede apagar y encender desde la
   página (cancelación al vencer el período, sin cortar lo ya pagado).

Stripe se dobla sustituyendo ``_llamar_stripe``, el mismo patrón que
``tests/test_stripe.py``.
"""
from datetime import date, datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.database import get_db, get_db_renovacion
from app.main import app
from app.models import CompraPlan, Licencia
from app.services.compras import activar_compra, compras_de_organizacion, crear_compra


def _instalar_override(db, ids):
    def _get_db(request=None):
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_db_renovacion] = _get_db


def _retirar_override():
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_db_renovacion, None)


def _preparar_sesion(db, ids):
    db.info["organizacion_id"] = ids[0]
    db.info["usuario_id"] = ids[1]
    db.info["rol_membresia"] = "propietario"


def _fmt(fecha):
    return fecha.strftime("%d/%m/%Y")


# ---------------------------------------------------------------------------
# La página según el estado del plan
# ---------------------------------------------------------------------------


def test_sin_plan_ofrece_contratar_con_fechas(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        _preparar_sesion(db, ids)
        _instalar_override(db, ids)
        try:
            with TestClient(app, base_url="https://cotizat.test") as client:
                r = client.get("/mi-plan")
        finally:
            _retirar_override()

    assert r.status_code == 200
    assert "No tienes un plan activo" in r.text
    assert "/pago/comprar?plan=anual" in r.text
    assert "/pago/comprar?plan=mensual" in r.text
    # Sin plan, el año cuenta desde hoy: 365 días de cobertura inclusive.
    assert _fmt(date.today() + timedelta(days=364)) in r.text
    # El menú lateral enlaza a la página (acceso fácil, no solo por URL).
    assert 'href="/mi-plan"' in r.text
    assert "Todavía no hay compras registradas" in r.text


def test_con_plan_mensual_muestra_renovar_y_cambio_encadenado(entorno):
    Session, ids, _rol = entorno
    hoy = date.today()
    vence = hoy + timedelta(days=10)
    with Session() as db:
        _preparar_sesion(db, ids)
        db.add(
            Licencia(
                organizacion_id=ids[0],
                estado="activa",
                origen="pago",
                inicio=hoy - timedelta(days=20),
                vence=vence,
                importe=9.99,
                moneda="USD",
                metodo_cobro="Pago móvil",
                creada_por_email="titular@example.com",
            )
        )
        db.flush()
        _instalar_override(db, ids)
        try:
            with TestClient(app, base_url="https://cotizat.test") as client:
                r = client.get("/mi-plan")
        finally:
            _retirar_override()

    assert r.status_code == 200
    assert "Plan mensual" in r.text
    assert _fmt(vence) in r.text
    assert "no se renueva automáticamente" in r.text  # pago manual
    assert "Renovar plan mensual" in r.text
    assert "Cambiar a plan anual" in r.text
    # El cambio a anual empieza al día siguiente del vencimiento y suma 365.
    inicio_anual = vence + timedelta(days=1)
    assert _fmt(inicio_anual) in r.text
    assert _fmt(inicio_anual + timedelta(days=364)) in r.text


def test_historial_con_recibo_y_aviso_de_compra_pendiente(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        _preparar_sesion(db, ids)
        compra = crear_compra(
            db,
            organizacion_id=ids[0],
            plan="anual",
            metodo_pago="usdt",
            datos_verificacion={"hash_transaccion": "TX-1"},
            comprobante_reference="storage://organizaciones/1/comprobantes/r.png",
            comprobante_nombre="r.png",
            comprobante_mime="image/png",
            creada_por_usuario_id=ids[1],
            creada_por_email="duena@example.com",
        )
        db.flush()
        compra, _licencia = activar_compra(
            db, compra_id=compra.id, operador_email="titular@example.com"
        )
        compra_id = compra.id
        crear_compra(
            db,
            organizacion_id=ids[0],
            plan="mensual",
            metodo_pago="kontigo",
            datos_verificacion={"numero_operacion": "K-7"},
            comprobante_reference="storage://organizaciones/1/comprobantes/r2.png",
            comprobante_nombre="r2.png",
            comprobante_mime="image/png",
            creada_por_usuario_id=ids[1],
            creada_por_email="duena@example.com",
        )
        db.flush()
        _instalar_override(db, ids)
        try:
            with TestClient(app, base_url="https://cotizat.test") as client:
                r = client.get("/mi-plan")
        finally:
            _retirar_override()

    assert r.status_code == 200
    assert "Estamos verificando un pago" in r.text
    assert f"/pago/recibo/{compra_id}.pdf" in r.text
    assert "89.00" in r.text
    assert "Plan anual" in r.text


def test_historial_solo_de_la_propia_organizacion(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        _preparar_sesion(db, ids)
        crear_compra(
            db,
            organizacion_id=ids[0],
            plan="mensual",
            metodo_pago="usdt",
            datos_verificacion={},
            comprobante_reference="storage://organizaciones/1/comprobantes/r.png",
            comprobante_nombre="r.png",
            comprobante_mime="image/png",
            creada_por_usuario_id=ids[1],
            creada_por_email="duena@example.com",
        )
        db.flush()
        propias = compras_de_organizacion(db, ids[0])
        ajenas = compras_de_organizacion(db, ids[0] + 999)
    assert len(propias) == 1
    assert ajenas == []


# ---------------------------------------------------------------------------
# Renovación automática con tarjeta
# ---------------------------------------------------------------------------


def _compra_stripe_activada(db, ids, subscription_id="sub_test_123"):
    compra = crear_compra(
        db,
        organizacion_id=ids[0],
        plan="mensual",
        metodo_pago="stripe",
        datos_verificacion={},
        comprobante_reference="",
        comprobante_nombre="",
        comprobante_mime="",
        creada_por_usuario_id=ids[1],
        creada_por_email="duena@example.com",
        exigir_comprobante=False,
    )
    db.flush()
    compra, _licencia = activar_compra(
        db,
        compra_id=compra.id,
        operador_email="stripe@cotizat.local",
        exigir_comprobante=False,
    )
    compra.stripe_subscription_id = subscription_id
    db.flush()
    return compra


def test_cancelar_renovacion_programa_la_cancelacion_en_stripe(entorno, monkeypatch):
    Session, ids, _rol = entorno
    llamadas = []

    def _doble_stripe(metodo, ruta, datos=None):
        llamadas.append((metodo, ruta, datos))
        return {"id": "sub_test_123", "status": "active", "cancel_at_period_end": True}

    monkeypatch.setattr("app.services.stripe._llamar_stripe", _doble_stripe)

    with Session() as db:
        _preparar_sesion(db, ids)
        _compra_stripe_activada(db, ids)
        _instalar_override(db, ids)
        try:
            with TestClient(app, base_url="https://cotizat.test") as client:
                r = client.post(
                    "/mi-plan/cancelar-renovacion", follow_redirects=False
                )
        finally:
            _retirar_override()

    assert r.status_code == 303
    assert r.headers["location"].startswith("/mi-plan?msg=")
    assert llamadas == [
        ("POST", "subscriptions/sub_test_123", {"cancel_at_period_end": "true"})
    ]


def test_reactivar_renovacion_deshace_la_cancelacion(entorno, monkeypatch):
    Session, ids, _rol = entorno
    llamadas = []

    def _doble_stripe(metodo, ruta, datos=None):
        llamadas.append((metodo, ruta, datos))
        return {"id": "sub_test_123", "status": "active", "cancel_at_period_end": False}

    monkeypatch.setattr("app.services.stripe._llamar_stripe", _doble_stripe)

    with Session() as db:
        _preparar_sesion(db, ids)
        _compra_stripe_activada(db, ids)
        _instalar_override(db, ids)
        try:
            with TestClient(app, base_url="https://cotizat.test") as client:
                r = client.post(
                    "/mi-plan/reactivar-renovacion", follow_redirects=False
                )
        finally:
            _retirar_override()

    assert r.status_code == 303
    assert llamadas == [
        ("POST", "subscriptions/sub_test_123", {"cancel_at_period_end": "false"})
    ]


def test_cancelar_sin_suscripcion_avisa_sin_romper(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        _preparar_sesion(db, ids)
        _instalar_override(db, ids)
        try:
            with TestClient(app, base_url="https://cotizat.test") as client:
                r = client.post(
                    "/mi-plan/cancelar-renovacion", follow_redirects=False
                )
        finally:
            _retirar_override()

    assert r.status_code == 303
    assert "error=" in r.headers["location"]


def test_la_pagina_ensenya_la_renovacion_automatica_de_stripe(entorno, monkeypatch):
    Session, ids, _rol = entorno
    fin = datetime(2026, 12, 5, 12, 0, tzinfo=timezone.utc)

    def _doble_stripe(metodo, ruta, datos=None):
        assert (metodo, ruta) == ("GET", "subscriptions/sub_test_123")
        return {
            "id": "sub_test_123",
            "status": "active",
            "cancel_at_period_end": False,
            "current_period_end": int(fin.timestamp()),
        }

    monkeypatch.setattr("app.services.stripe._llamar_stripe", _doble_stripe)
    # «Configurado» sin fingir una clave en el entorno: la guarda E4-030
    # (detect-secrets con baseline) trata cualquier cadena tipo sk_ como
    # secreto nuevo y tumba el CI.
    monkeypatch.setattr("app.services.stripe.stripe_configurado", lambda: True)

    with Session() as db:
        _preparar_sesion(db, ids)
        _compra_stripe_activada(db, ids)
        _instalar_override(db, ids)
        try:
            with TestClient(app, base_url="https://cotizat.test") as client:
                r = client.get("/mi-plan")
        finally:
            _retirar_override()

    assert r.status_code == 200
    assert "se renueva automáticamente" in r.text
    assert "05/12/2026" in r.text
    assert "Desactivar la renovación automática" in r.text


# ---------------------------------------------------------------------------
# El resumen de la suscripción acepta las dos formas de la API
# ---------------------------------------------------------------------------


def test_resumen_suscripcion_lee_fin_de_periodo_en_raiz_e_items():
    from app.services.stripe import resumen_suscripcion

    marca = int(datetime(2027, 1, 15, tzinfo=timezone.utc).timestamp())
    esperado = date(2027, 1, 15)
    en_raiz = resumen_suscripcion(
        {"status": "active", "cancel_at_period_end": True, "current_period_end": marca}
    )
    en_items = resumen_suscripcion(
        {
            "status": "active",
            "cancel_at_period_end": False,
            "items": {"data": [{"current_period_end": marca}]},
        }
    )
    assert en_raiz == {
        "estado": "active",
        "cancela_al_vencer": True,
        "fin_periodo": esperado,
    }
    assert en_items["fin_periodo"] == esperado
    assert en_items["cancela_al_vencer"] is False
