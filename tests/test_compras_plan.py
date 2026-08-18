"""Compra de planes con pago manual: registro, comprobante y activación.

Cubre el flujo E1-059: el cliente elige plan y método, sube su comprobante,
la compra queda pendiente y el operador la activa desde el panel concediendo
la licencia del plan.
"""
from datetime import date, timedelta
import io

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import CompraPlan, Configuracion, Licencia, Membresia, Organizacion, Usuario
from app.services.compras import (
    GestionCompraError,
    activar_compra,
    crear_compra,
    rechazar_compra,
    resumen_compras,
)

AUTH_ID = "7a3c5f9e-2b41-4d8c-a6f3-19e8d0c42b11"


def _png_minimo() -> bytes:
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (8, 8), color=(200, 200, 200)).save(buf, format="PNG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Servicio: registro de compras
# ---------------------------------------------------------------------------


def test_crear_compra_pendiente_con_importe_del_plan(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        compra = crear_compra(
            db,
            organizacion_id=ids[0],
            plan="anual",
            metodo_pago="pago_movil",
            datos_verificacion={"numero_operacion": "OP-123", "banco_origen": "Provincial"},
            comprobante_reference="storage://organizaciones/1/comprobantes/recibo.png",
            comprobante_nombre="recibo.png",
            comprobante_mime="image/png",
            creada_por_usuario_id=ids[1],
            creada_por_email="duena@example.com",
        )
        assert compra.estado == "pendiente"
        assert compra.importe == 89.0  # plan anual
        assert compra.moneda == "USD"
        assert compra.datos_verificacion_dict()["banco_origen"] == "Provincial"


def test_crear_compra_rechaza_plan_desconocido(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        with pytest.raises(GestionCompraError):
            crear_compra(
                db,
                organizacion_id=ids[0],
                plan="vitalicio",
                metodo_pago="binance",
                datos_verificacion={},
                comprobante_reference="storage://x/recibo.png",
                comprobante_nombre="recibo.png",
                comprobante_mime="image/png",
                creada_por_usuario_id=ids[1],
                creada_por_email="duena@example.com",
            )


def test_crear_compra_rechaza_metodo_desconocido(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        with pytest.raises(GestionCompraError):
            crear_compra(
                db,
                organizacion_id=ids[0],
                plan="mensual",
                metodo_pago="paypal",
                datos_verificacion={},
                comprobante_reference="storage://x/recibo.png",
                comprobante_nombre="recibo.png",
                comprobante_mime="image/png",
                creada_por_usuario_id=ids[1],
                creada_por_email="duena@example.com",
            )


def test_crear_compra_exige_comprobante(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        with pytest.raises(GestionCompraError, match="comprobante"):
            crear_compra(
                db,
                organizacion_id=ids[0],
                plan="mensual",
                metodo_pago="usdt",
                datos_verificacion={},
                comprobante_reference="",
                comprobante_nombre="",
                comprobante_mime="",
                creada_por_usuario_id=ids[1],
                creada_por_email="duena@example.com",
            )


# ---------------------------------------------------------------------------
# Servicio: activación y rechazo
# ---------------------------------------------------------------------------


def test_activar_compra_concede_licencia_del_plan(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        compra = crear_compra(
            db,
            organizacion_id=ids[0],
            plan="anual",
            metodo_pago="binance",
            datos_verificacion={"binance_id_origen": "123456", "hash_transaccion": "H-1"},
            comprobante_reference="storage://organizaciones/1/comprobantes/recibo.png",
            comprobante_nombre="recibo.png",
            comprobante_mime="image/png",
            creada_por_usuario_id=ids[1],
            creada_por_email="duena@example.com",
        )
        db.flush()

        compra, licencia = activar_compra(
            db, compra_id=compra.id, operador_email="titular@example.com"
        )
        assert compra.estado == "activa"
        assert compra.licencia_id == licencia.id
        assert licencia.origen == "pago"
        assert licencia.importe == 89.0
        assert licencia.metodo_cobro == "Binance"
        # Duración del plan anual: 1 año desde hoy.
        assert (licencia.vence - licencia.inicio).days >= 364


def test_no_se_activa_dos_veces(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        compra = crear_compra(
            db,
            organizacion_id=ids[0],
            plan="mensual",
            metodo_pago="kontigo",
            datos_verificacion={"numero_operacion": "K-9"},
            comprobante_reference="storage://organizaciones/1/comprobantes/r.png",
            comprobante_nombre="r.png",
            comprobante_mime="image/png",
            creada_por_usuario_id=ids[1],
            creada_por_email="duena@example.com",
        )
        db.flush()
        activar_compra(db, compra_id=compra.id, operador_email="titular@example.com")
        with pytest.raises(GestionCompraError, match="ya está"):
            activar_compra(db, compra_id=compra.id, operador_email="titular@example.com")


def test_rechazar_compra(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        compra = crear_compra(
            db,
            organizacion_id=ids[0],
            plan="mensual",
            metodo_pago="usdt",
            datos_verificacion={"hash_transaccion": "TX-1"},
            comprobante_reference="storage://organizaciones/1/comprobantes/r.png",
            comprobante_nombre="r.png",
            comprobante_mime="image/png",
            creada_por_usuario_id=ids[1],
            creada_por_email="duena@example.com",
        )
        db.flush()
        rechazar_compra(db, compra_id=compra.id, operador_email="titular@example.com")
        assert compra.estado == "rechazada"
        assert compra.revisado_por_email == "titular@example.com"


def test_resumen_compras_incluye_nombre_de_organizacion(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        crear_compra(
            db,
            organizacion_id=ids[0],
            plan="anual",
            metodo_pago="usdt",
            datos_verificacion={},
            comprobante_reference="storage://organizaciones/1/comprobantes/r.png",
            comprobante_nombre="r.png",
            comprobante_mime="image/png",
            creada_por_usuario_id=ids[1],
            creada_por_email="duena@example.com",
        )
        db.flush()
        filas = resumen_compras(db)
        assert len(filas) == 1
        assert filas[0]["organizacion_nombre"] == "Constructora Restaurada"
        assert filas[0]["plan_nombre"] == "Plan anual"


# ---------------------------------------------------------------------------
# Flujo web del cliente (sesión iniciada)
# ---------------------------------------------------------------------------


def _cliente():
    client = TestClient(app, base_url="https://cotizat.test")
    return client


def test_pagina_comprar_muestra_planes_y_metodos(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        db.info["usuario_id"] = ids[1]
        db.info["rol_membresia"] = "propietario"
        _instalar_override(db, ids)
        try:
            with _cliente() as client:
                r = client.get("/pago/comprar?plan=anual")
            assert r.status_code == 200
            assert "Plan anual" in r.text
            assert "Pago m" in r.text
            assert "Binance" in r.text
            assert "Kontigo" in r.text
            assert "USDT" in r.text
            assert "comprobante" in r.text.lower()
        finally:
            _retirar_override()


def test_pagina_comprar_plan_desconocido_redirige(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        db.info["usuario_id"] = ids[1]
        db.info["rol_membresia"] = "propietario"
        _instalar_override(db, ids)
        try:
            with _cliente() as client:
                r = client.get("/pago/comprar?plan=vitalicio", follow_redirects=False)
            assert r.status_code == 303
            assert r.headers["location"].startswith("/pago")
        finally:
            _retirar_override()


def test_registrar_compra_con_comprobante(entorno, monkeypatch, tmp_path):
    Session, ids, _rol = entorno
    monkeypatch.setenv("COTIZAT_STORAGE_BACKEND", "local")
    monkeypatch.setenv("COTIZAT_STORAGE_DIR", str(tmp_path / "storage"))
    from app.storage import reset_storage_backend_cache

    reset_storage_backend_cache()
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        db.info["usuario_id"] = ids[1]
        db.info["rol_membresia"] = "propietario"
        _instalar_override(db, ids)
        try:
            with _cliente() as client:
                r = client.post(
                    "/pago/comprar",
                    data={
                        "plan": "mensual",
                        "metodo_pago": "pago_movil",
                        "banco_origen": "Provincial",
                        "numero_operacion": "OP-777",
                        "fecha_pago": "2026-08-18",
                        "nombre_titular": "Dueña",
                    },
                    files={"comprobante_pago_movil": ("recibo.png", _png_minimo(), "image/png")},
                    follow_redirects=False,
                )
            assert r.status_code == 303
            assert "/pago/confirmacion?id=" in r.headers["location"]
        finally:
            _retirar_override()
            reset_storage_backend_cache()

    with Session() as db:
        compra = db.query(CompraPlan).order_by(CompraPlan.id.desc()).first()
        assert compra is not None
        assert compra.estado == "pendiente"
        assert compra.metodo_pago == "pago_movil"
        assert compra.importe == 9.99
        assert compra.comprobante_reference
        assert compra.datos_verificacion_dict()["numero_operacion"] == "OP-777"


def test_registrar_compra_sin_comprobante_devuelve_error(entorno, monkeypatch, tmp_path):
    Session, ids, _rol = entorno
    monkeypatch.setenv("COTIZAT_STORAGE_BACKEND", "local")
    monkeypatch.setenv("COTIZAT_STORAGE_DIR", str(tmp_path / "storage"))
    from app.storage import reset_storage_backend_cache

    reset_storage_backend_cache()
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        db.info["usuario_id"] = ids[1]
        db.info["rol_membresia"] = "propietario"
        _instalar_override(db, ids)
        try:
            with _cliente() as client:
                r = client.post(
                    "/pago/comprar",
                    data={"plan": "anual", "metodo_pago": "usdt", "hash_transaccion": "TX-1"},
                    follow_redirects=False,
                )
            assert r.status_code == 303
            assert "comprobante" in r.headers["location"]
        finally:
            _retirar_override()
            reset_storage_backend_cache()


def test_registrar_compra_ignora_archivos_de_otros_metodos(entorno, monkeypatch, tmp_path):
    """Cada método publica su propio campo de archivo; el servidor lee solo el
    del método elegido.

    Regresión del bug en que los cuatro paneles compartían ``name="comprobante"``:
    el navegador enviaba una parte vacía por método y el archivo elegido podía
    perderse, rechazando la compra con «Adjunta el comprobante...».
    """
    Session, ids, _rol = entorno
    monkeypatch.setenv("COTIZAT_STORAGE_BACKEND", "local")
    monkeypatch.setenv("COTIZAT_STORAGE_DIR", str(tmp_path / "storage"))
    from app.storage import reset_storage_backend_cache

    reset_storage_backend_cache()
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        db.info["usuario_id"] = ids[1]
        db.info["rol_membresia"] = "propietario"
        _instalar_override(db, ids)
        try:
            with _cliente() as client:
                r = client.post(
                    "/pago/comprar",
                    data={
                        "plan": "anual",
                        "metodo_pago": "usdt",
                        "wallet_origen": "TX-wallet",
                        "hash_transaccion": "TX-1",
                    },
                    files={
                        # Los paneles no elegidos llegan vacíos (como haría un
                        # navegador si no estuvieran deshabilitados).
                        "comprobante_pago_movil": ("", b"", "application/octet-stream"),
                        "comprobante_binance": ("", b"", "application/octet-stream"),
                        "comprobante_kontigo": ("", b"", "application/octet-stream"),
                        "comprobante_usdt": ("recibo.png", _png_minimo(), "image/png"),
                    },
                    follow_redirects=False,
                )
            assert r.status_code == 303
            assert "/pago/confirmacion?id=" in r.headers["location"]
        finally:
            _retirar_override()
            reset_storage_backend_cache()

    with Session() as db:
        compra = db.query(CompraPlan).order_by(CompraPlan.id.desc()).first()
        assert compra is not None
        assert compra.estado == "pendiente"
        assert compra.metodo_pago == "usdt"
        assert compra.comprobante_reference
        assert compra.comprobante_nombre == "recibo.png"


def test_elegir_plan_guarda_cookie_y_redirige():
    """«Contratar plan» recuerda la intención antes de exigir sesión/empresa."""
    with _cliente() as client:
        r = client.get("/pago/elegir?plan=anual", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/pago/comprar?plan=anual"
    assert client.cookies.get("cotizat_plan_pendiente") == "anual"


def test_elegir_plan_desconocido_redirige_a_pago():
    with _cliente() as client:
        r = client.get("/pago/elegir?plan=vitalicio", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/pago"


def test_descartar_plan_limpia_cookie():
    with _cliente() as client:
        # Igual que el usuario real: elige el plan (guarda la cookie) y luego
        # descarta desde el panel.
        client.get("/pago/elegir?plan=anual", follow_redirects=False)
        assert client.cookies.get("cotizat_plan_pendiente") == "anual"
        r = client.post("/pago/descartar", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/inicio"
    assert client.cookies.get("cotizat_plan_pendiente") is None


def test_inicio_muestra_retomar_compra_con_cookie(entorno):
    """Tras crear cuenta y empresa, el panel ofrece retomar la compra elegida."""
    Session, ids, _rol = entorno
    with Session() as db:
        cfg = db.query(Configuracion).first()
        cfg.onboarding_completado = True
        db.commit()
    with _cliente() as client:
        client.cookies.set("cotizat_plan_pendiente", "anual")
        r = client.get("/inicio")
    assert r.status_code == 200
    assert "Retoma tu compra" in r.text
    assert "Plan anual" in r.text
    assert "Continuar compra" in r.text
    assert "/pago/comprar?plan=anual" in r.text


def test_bienvenida_muestra_compra_pendiente(entorno):
    """Nada más crear la organización, la bienvenida avisa de la compra pendiente."""
    Session, ids, _rol = entorno
    # El fixture deja el onboarding sin completar, así que /bienvenida renderiza.
    with _cliente() as client:
        client.cookies.set("cotizat_plan_pendiente", "mensual")
        r = client.get("/bienvenida")
    assert r.status_code == 200
    assert "compra pendiente" in r.text
    assert "Plan mensual" in r.text


def test_inicio_sin_cookie_no_muestra_retomar_compra(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        cfg = db.query(Configuracion).first()
        cfg.onboarding_completado = True
        db.commit()
    with _cliente() as client:
        r = client.get("/inicio")
    assert r.status_code == 200
    assert "Retoma tu compra" not in r.text


def test_confirmacion_muestra_resumen(entorno, monkeypatch, tmp_path):
    Session, ids, _rol = entorno
    monkeypatch.setenv("COTIZAT_STORAGE_BACKEND", "local")
    monkeypatch.setenv("COTIZAT_STORAGE_DIR", str(tmp_path / "storage"))
    from app.storage import reset_storage_backend_cache

    reset_storage_backend_cache()
    compra_id = None
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        db.info["usuario_id"] = ids[1]
        db.info["rol_membresia"] = "propietario"
        compra = crear_compra(
            db,
            organizacion_id=ids[0],
            plan="mensual",
            metodo_pago="kontigo",
            datos_verificacion={"numero_operacion": "K-42"},
            comprobante_reference="storage://organizaciones/1/comprobantes/r.png",
            comprobante_nombre="r.png",
            comprobante_mime="image/png",
            creada_por_usuario_id=ids[1],
            creada_por_email="duena@example.com",
        )
        db.flush()
        compra_id = compra.id

        _instalar_override(db, ids)
        try:
            with _cliente() as client:
                r = client.get(f"/pago/confirmacion?id={compra_id}")
            assert r.status_code == 200
            assert "¡Compra registrada!" in r.text
            assert "Plan mensual" in r.text
            assert "#" + str(compra_id) in r.text
        finally:
            _retirar_override()
            reset_storage_backend_cache()


def _override(db, ids):
    def _get_db(request=None):
        try:
            yield db
        finally:
            pass

    return _get_db


def _instalar_override(db, ids):
    """Sustituye las dos puertas de sesión que usan las rutas de compra.

    El checkout cuelga de ``get_db_renovacion`` (para que una organización
    suspendida pueda renovar), así que overridear solo ``get_db`` dejaría las
    rutas de pago hablando con la base real.
    """
    from app.database import get_db_renovacion

    dependencia = _override(db, ids)
    app.dependency_overrides[get_db] = dependencia
    app.dependency_overrides[get_db_renovacion] = dependencia


def _retirar_override():
    from app.database import get_db_renovacion

    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_db_renovacion, None)


# ---------------------------------------------------------------------------
# Panel del operador: revisión y activación
# ---------------------------------------------------------------------------


def test_un_cliente_normal_no_alcanza_el_panel(entorno, monkeypatch):
    """La ruta /admin/compras exige ser operador (igual que licencias)."""
    Session, ids, _rol = entorno
    monkeypatch.setenv("COTIZAT_OPERADORES", "titular@example.com")
    from app.database import get_operator_db

    with Session() as db:
        app.dependency_overrides[get_operator_db] = _operador_override(
            db, "cliente@example.com", False
        )
        try:
            with _cliente() as client:
                r = client.get("/admin/compras", follow_redirects=False)
            assert r.status_code in (302, 303, 403)
            assert "Compras de plan" not in r.text
        finally:
            app.dependency_overrides.pop(get_operator_db, None)


def test_el_operador_activa_compra_desde_el_panel(entorno, monkeypatch):
    Session, ids, _rol = entorno
    monkeypatch.setenv("COTIZAT_OPERADORES", "titular@example.com")
    from app.database import get_operator_db

    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        compra = crear_compra(
            db,
            organizacion_id=ids[0],
            plan="anual",
            metodo_pago="usdt",
            datos_verificacion={"hash_transaccion": "TX-999"},
            comprobante_reference="storage://organizaciones/1/comprobantes/r.png",
            comprobante_nombre="r.png",
            comprobante_mime="image/png",
            creada_por_usuario_id=ids[1],
            creada_por_email="duena@example.com",
        )
        db.flush()
        compra_id = compra.id

        app.dependency_overrides[get_operator_db] = _operador_override(
            db, "titular@example.com", True
        )
        try:
            with _cliente() as client:
                # Panel: ve la compra pendiente
                r = client.get("/admin/compras")
                assert r.status_code == 200
                assert "#" + str(compra_id) in r.text
                assert "Pendiente" in r.text

                # Activa desde el panel
                r2 = client.post(
                    f"/admin/compras/{compra_id}/activar", follow_redirects=False
                )
                assert r2.status_code == 303
        finally:
            app.dependency_overrides.pop(get_operator_db, None)

    with Session() as db:
        compra = db.get(CompraPlan, compra_id)
        assert compra.estado == "activa"
        assert compra.licencia_id is not None
        licencia = db.get(Licencia, compra.licencia_id)
        assert licencia.origen == "pago"
        assert licencia.importe == 89.0


def _operador_override(db, email, es_operador_flag):
    from starlette.requests import Request
    from app.auth import SupabaseIdentity
    from app.operadores import es_operador

    def _db_operador(request: Request):
        from app.auth import OrganizationAccessDenied

        identidad = SupabaseIdentity(
            auth_user_id=AUTH_ID,
            email=email,
            email_verified=True,
            name="Persona",
        )
        request.state.supabase_identity = identidad
        if not es_operador(identidad.email, email_verificado=identidad.email_verified):
            db.close()
            raise OrganizationAccessDenied("No tienes acceso a esta sección.")
        db.info["auth_email"] = email
        db.info["es_operador"] = True
        try:
            yield db
        finally:
            pass

    return _db_operador


# ---------------------------------------------------------------------------
# Configuración por rol y estado del plan del cliente
# ---------------------------------------------------------------------------


def test_solo_propietario_y_admin_editan_configuracion(entorno, monkeypatch):
    """Un miembro no puede modificar la configuración de la organización."""
    from urllib.parse import unquote
    from app.routers import configuracion as config_router

    Session, ids, rol = entorno
    monkeypatch.setattr(config_router, "DATABASE_IS_SQLITE", False)
    rol["valor"] = "miembro"

    with _cliente() as client:
        r = client.post(
            "/configuracion",
            data={"organizacion_nombre": "Hackeado", "empresa_nombre": "Hackeado"},
            follow_redirects=False,
        )
    assert r.status_code == 303
    assert "Solo propietarios" in unquote(r.headers.get("location", ""))

    with Session() as db:
        org = db.get(Organizacion, ids[0])
        assert org.nombre != "Hackeado"


def test_miembro_ve_configuracion_solo_lectura(entorno, monkeypatch):
    """El formulario sale deshabilitado (fieldset disabled) para no gestores."""
    from app.routers import configuracion as config_router

    Session, ids, rol = entorno
    monkeypatch.setattr(config_router, "DATABASE_IS_SQLITE", False)
    rol["valor"] = "miembro"

    with _cliente() as client:
        r = client.get("/configuracion")
    assert r.status_code == 200
    assert "Solo propietarios y administradores" in r.text
    assert "<fieldset disabled" in r.text


def test_configuracion_muestra_el_plan_del_cliente(entorno):
    """La tarjeta 'Tu plan' refleja licencia vigente con fecha y días."""
    Session, ids, _rol = entorno
    with Session() as db:
        db.add(Licencia(
            organizacion_id=ids[0],
            estado="activa", origen="pago",
            inicio=date(2026, 8, 1), vence=date(2026, 9, 1),
            importe=9.99, metodo_cobro="Pago móvil",
        ))
        db.commit()

    with _cliente() as client:
        r = client.get("/configuracion")
    assert r.status_code == 200
    assert "Tu plan" in r.text
    assert "Plan mensual" in r.text
    assert "Vence el 01/09/2026" in r.text
    assert "día" in r.text  # días restantes


def test_configuracion_muestra_el_total_de_planes_encadenados(entorno):
    """Renovar con días por delante suma: 4 días + 1 mes → ~34 días.

    La tarjeta «Tu plan» debe mostrar el final de la cadena completa, no el
    vencimiento de la primera licencia.
    """
    Session, ids, _rol = entorno
    hoy = date.today()
    with Session() as db:
        db.add(Licencia(
            organizacion_id=ids[0],
            estado="activa", origen="pago",
            inicio=hoy - timedelta(days=2), vence=hoy + timedelta(days=4),
            importe=9.99, metodo_cobro="Pago móvil",
        ))
        # Renovación encadenada: empieza al día siguiente de la anterior.
        db.add(Licencia(
            organizacion_id=ids[0],
            estado="activa", origen="pago",
            inicio=hoy + timedelta(days=5), vence=hoy + timedelta(days=34),
            importe=9.99, metodo_cobro="Pago móvil",
        ))
        db.commit()

    vence_total = (hoy + timedelta(days=34)).strftime("%d/%m/%Y")
    with _cliente() as client:
        r = client.get("/configuracion")
    assert r.status_code == 200
    assert "Tu plan" in r.text
    assert "Plan mensual" in r.text
    assert f"Vence el {vence_total}" in r.text
    assert "34 días restantes" in r.text


# ---------------------------------------------------------------------------
# Recibo del cliente y aviso de activación (E1-059 · cierre del flujo)
# ---------------------------------------------------------------------------


def _compra_activada(db, ids, *, plan="anual", metodo="binance"):
    """Compra ya verificada por el operador, con su licencia concedida."""
    db.info["organizacion_id"] = ids[0]
    compra = crear_compra(
        db,
        organizacion_id=ids[0],
        plan=plan,
        metodo_pago=metodo,
        datos_verificacion={"numero_operacion": "OP-4321"},
        comprobante_reference="storage://organizaciones/1/comprobantes/r.png",
        comprobante_nombre="r.png",
        comprobante_mime="image/png",
        creada_por_usuario_id=ids[1],
        creada_por_email="duena@example.com",
    )
    db.flush()
    compra, licencia = activar_compra(
        db, compra_id=compra.id, operador_email="titular@example.com"
    )
    db.commit()
    return compra, licencia


def test_activar_compra_copia_el_periodo_concedido(entorno):
    """La compra guarda inicio y vencimiento de la licencia que concedió.

    Es la pieza que permite al comprador emitir su recibo sin leer
    `licencias`, que el RLS reserva al operador.
    """
    Session, ids, _rol = entorno
    with Session() as db:
        compra, licencia = _compra_activada(db, ids)
        assert compra.licencia_inicio == licencia.inicio
        assert compra.licencia_vence == licencia.vence


def test_recibo_de_una_compra_pendiente_no_existe(entorno):
    """Sin activación no hay cobro liquidado que documentar."""
    from app.services.licencias import GestionLicenciaError
    from app.services.recibo_licencia import licencia_de_compra

    Session, ids, _rol = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        compra = crear_compra(
            db,
            organizacion_id=ids[0],
            plan="mensual",
            metodo_pago="kontigo",
            datos_verificacion={"numero_operacion": "K-1"},
            comprobante_reference="storage://organizaciones/1/comprobantes/r.png",
            comprobante_nombre="r.png",
            comprobante_mime="image/png",
            creada_por_usuario_id=ids[1],
            creada_por_email="duena@example.com",
        )
        db.flush()
        with pytest.raises(GestionLicenciaError):
            licencia_de_compra(compra)


def test_recibo_del_cliente_es_el_mismo_documento_que_el_del_operador(entorno):
    """El cliente descarga el recibo con la numeración de su licencia."""
    from app.services.recibo_licencia import (
        generar_recibo_licencia_pdf,
        licencia_de_compra,
        numero_recibo,
    )

    Session, ids, _rol = entorno
    with Session() as db:
        compra, licencia = _compra_activada(db, ids)
        vista = licencia_de_compra(compra)
        assert numero_recibo(vista) == numero_recibo(licencia)
        assert vista.importe == licencia.importe
        assert vista.metodo_cobro == licencia.metodo_cobro
        pdf = generar_recibo_licencia_pdf(
            vista, db.get(Organizacion, ids[0])
        ).getvalue()
        assert pdf.startswith(b"%PDF")


def test_el_cliente_descarga_el_recibo_de_su_compra(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        compra, licencia = _compra_activada(db, ids)
        compra_id, licencia_id = compra.id, licencia.id

        db.info["usuario_id"] = ids[1]
        db.info["rol_membresia"] = "propietario"
        _instalar_override(db, ids)
        try:
            with _cliente() as client:
                r = client.get(f"/pago/recibo/{compra_id}.pdf")
        finally:
            _retirar_override()

    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert f"recibo-CT-{licencia_id:06d}-restauracion.pdf" in r.headers[
        "content-disposition"
    ]
    assert r.headers["cache-control"] == "no-store"
    assert r.content.startswith(b"%PDF")


def test_el_recibo_de_otra_organizacion_no_se_alcanza(entorno):
    """El filtro por organización es lo que aísla el recibo, no el id."""
    Session, ids, _rol = entorno
    with Session() as db:
        otra = Organizacion(nombre="Ajena C.A.", slug="ajena")
        db.add(otra)
        db.flush()
        licencia_ajena = Licencia(
            organizacion_id=otra.id,
            estado="activa", origen="pago",
            inicio=date(2026, 8, 1), vence=date(2027, 7, 31),
            importe=89.0, metodo_cobro="Binance",
        )
        db.add(licencia_ajena)
        db.flush()
        compra = CompraPlan(
            organizacion_id=otra.id,
            plan="anual",
            metodo_pago="binance",
            importe=89.0,
            moneda="USD",
            datos_verificacion="{}",
            comprobante_reference="storage://x/r.png",
            estado="activa",
            licencia_id=licencia_ajena.id,
            licencia_inicio=date(2026, 8, 1),
            licencia_vence=date(2027, 7, 31),
            creada_por_email="ajena@example.com",
        )
        db.add(compra)
        db.commit()
        compra_id = compra.id

        db.info["organizacion_id"] = ids[0]
        db.info["usuario_id"] = ids[1]
        db.info["rol_membresia"] = "propietario"
        _instalar_override(db, ids)
        try:
            with _cliente() as client:
                r = client.get(
                    f"/pago/recibo/{compra_id}.pdf", follow_redirects=False
                )
        finally:
            _retirar_override()

    assert r.status_code == 303
    assert not r.content.startswith(b"%PDF")


def test_la_tarjeta_del_plan_ofrece_el_recibo_tras_pagar(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        compra, _licencia = _compra_activada(db, ids)
        compra_id = compra.id

    with _cliente() as client:
        r = client.get("/configuracion")

    assert r.status_code == 200
    assert f"/pago/recibo/{compra_id}.pdf" in r.text
    assert "Descargar recibo" in r.text


def test_la_tarjeta_del_plan_sin_compra_no_ofrece_recibo(entorno):
    """Una licencia de cortesía no tiene cobro que documentar."""
    Session, ids, _rol = entorno
    with Session() as db:
        db.add(Licencia(
            organizacion_id=ids[0],
            estado="activa", origen="cortesia",
            inicio=date(2026, 8, 1), vence=date(2026, 9, 1),
        ))
        db.commit()

    with _cliente() as client:
        r = client.get("/configuracion")

    assert r.status_code == 200
    assert "/pago/recibo/" not in r.text


def test_activar_desde_el_panel_avisa_al_comprador_con_su_recibo(
    entorno, monkeypatch
):
    """El comprador se entera de que su plan quedó activo, y hasta cuándo."""
    Session, ids, _rol = entorno
    monkeypatch.setenv("COTIZAT_OPERADORES", "titular@example.com")
    from app.database import get_operator_db

    enviados = []
    monkeypatch.setattr(
        "app.services.email.enviar_activacion_plan_por_email",
        lambda **kw: enviados.append(kw) or "email-1",
    )

    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        compra = crear_compra(
            db,
            organizacion_id=ids[0],
            plan="anual",
            metodo_pago="pago_movil",
            datos_verificacion={"numero_operacion": "OP-55"},
            comprobante_reference="storage://organizaciones/1/comprobantes/r.png",
            comprobante_nombre="r.png",
            comprobante_mime="image/png",
            creada_por_usuario_id=ids[1],
            creada_por_email="duena@example.com",
        )
        db.flush()
        compra_id = compra.id

        app.dependency_overrides[get_operator_db] = _operador_override(
            db, "titular@example.com", True
        )
        try:
            with _cliente() as client:
                r = client.post(
                    f"/admin/compras/{compra_id}/activar", follow_redirects=False
                )
            assert r.status_code == 303
        finally:
            app.dependency_overrides.pop(get_operator_db, None)

    assert len(enviados) == 1
    aviso = enviados[0]
    assert aviso["email"] == "duena@example.com"
    assert aviso["plan_nombre"] == "Plan anual"
    assert aviso["metodo_nombre"] == "Pago móvil"
    assert aviso["organizacion_nombre"] == "Constructora Restaurada"
    assert aviso["vence"] > aviso["inicio"]
    assert aviso["recibo_pdf"].startswith(b"%PDF")
    assert aviso["recibo_nombre"].startswith("recibo-CT-")


def test_un_fallo_de_correo_no_deshace_la_activacion(entorno, monkeypatch):
    """La licencia ya está concedida: el aviso es cortesía, no condición."""
    Session, ids, _rol = entorno
    monkeypatch.setenv("COTIZAT_OPERADORES", "titular@example.com")
    from app.database import get_operator_db
    from app.services.email import EmailSendError

    def _explota(**_kw):
        raise EmailSendError("Resend caído")

    monkeypatch.setattr(
        "app.services.email.enviar_activacion_plan_por_email", _explota
    )

    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        compra = crear_compra(
            db,
            organizacion_id=ids[0],
            plan="mensual",
            metodo_pago="usdt",
            datos_verificacion={"hash_transaccion": "TX-7"},
            comprobante_reference="storage://organizaciones/1/comprobantes/r.png",
            comprobante_nombre="r.png",
            comprobante_mime="image/png",
            creada_por_usuario_id=ids[1],
            creada_por_email="duena@example.com",
        )
        db.flush()
        compra_id = compra.id

        app.dependency_overrides[get_operator_db] = _operador_override(
            db, "titular@example.com", True
        )
        try:
            with _cliente() as client:
                r = client.post(
                    f"/admin/compras/{compra_id}/activar", follow_redirects=False
                )
            assert r.status_code == 303
        finally:
            app.dependency_overrides.pop(get_operator_db, None)

    with Session() as db:
        compra = db.get(CompraPlan, compra_id)
        assert compra.estado == "activa"
        assert compra.licencia_id is not None
        assert compra.licencia_vence is not None


def test_el_correo_de_activacion_lleva_la_fecha_y_el_recibo(monkeypatch):
    """Contenido del aviso: hasta cuándo llega el plan y el PDF adjunto."""
    import base64
    import json

    from app.services import email as email_module

    capturado = {}

    class _Respuesta:
        def __enter__(self):
            return self

        def __exit__(self, *_a):
            return False

        def read(self, _size=-1):
            return b'{"id":"activacion-1"}'

    def fake_urlopen(request, timeout):  # noqa: ARG001
        capturado.update(json.loads(request.data.decode("utf-8")))
        return _Respuesta()

    monkeypatch.setenv("RESEND_API_KEY", "re_prueba")
    monkeypatch.setenv("COTIZAT_EMAIL_FROM", "CotizaT <no-responder@cotizat.test>")
    monkeypatch.setattr(email_module, "urlopen", fake_urlopen)

    envio_id = email_module.enviar_activacion_plan_por_email(
        email="duena@example.com",
        organizacion_nombre="Constructora Restaurada",
        plan_nombre="Plan anual",
        importe_texto="89,00 $",
        metodo_nombre="Pago móvil",
        inicio=date(2026, 8, 18),
        vence=date(2027, 8, 17),
        recibo_pdf=b"%PDF-1.4\nrecibo",
        recibo_nombre="recibo-CT-000013.pdf",
    )

    assert envio_id == "activacion-1"
    assert capturado["to"] == ["duena@example.com"]
    assert "17/08/2027" in capturado["subject"]
    assert "17/08/2027" in capturado["html"]
    assert "17/08/2027" in capturado["text"]
    assert "Constructora Restaurada" in capturado["html"]
    assert "89,00 $" in capturado["text"]
    adjunto = capturado["attachments"][0]
    assert adjunto["filename"] == "recibo-CT-000013.pdf"
    assert base64.b64decode(adjunto["content"]) == b"%PDF-1.4\nrecibo"


def test_el_aviso_de_activacion_sale_aunque_falte_el_recibo(monkeypatch):
    """El plan activo es la noticia; el PDF, un extra que puede faltar."""
    import json

    from app.services import email as email_module

    capturado = {}

    class _Respuesta:
        def __enter__(self):
            return self

        def __exit__(self, *_a):
            return False

        def read(self, _size=-1):
            return b'{"id":"activacion-2"}'

    def fake_urlopen(request, timeout):  # noqa: ARG001
        capturado.update(json.loads(request.data.decode("utf-8")))
        return _Respuesta()

    monkeypatch.setenv("RESEND_API_KEY", "re_prueba")
    monkeypatch.setenv("COTIZAT_EMAIL_FROM", "CotizaT <no-responder@cotizat.test>")
    monkeypatch.setattr(email_module, "urlopen", fake_urlopen)

    email_module.enviar_activacion_plan_por_email(
        email="duena@example.com",
        organizacion_nombre="Constructora Restaurada",
        plan_nombre="Plan mensual",
        importe_texto="9,99 $",
        metodo_nombre="USDT",
        inicio=date(2026, 8, 18),
        vence=date(2026, 9, 17),
    )

    assert "attachments" not in capturado or not capturado["attachments"]
    assert "17/09/2026" in capturado["html"]


def test_una_organizacion_suspendida_todavia_puede_comprar(entorno, monkeypatch):
    """Prueba de extremo a extremo de la salida de emergencia del corte.

    Con `COTIZAT_EXIGIR_LICENCIA` activa y sin licencia vigente, el cliente
    tiene que poder abrir el checkout: si no, la suspensión sería una trampa
    sin salida (no podría comprar justo lo que necesita para salir de ella).
    """
    monkeypatch.setenv("COTIZAT_EXIGIR_LICENCIA", "true")
    Session, ids, _rol = entorno
    with Session() as db:
        db.info["usuario_id"] = ids[1]
        db.info["rol_membresia"] = "propietario"
        # Solo se sustituye la puerta del checkout: `get_db` sigue siendo la
        # real, así que si la ruta colgara de ella, esto no daría 200.
        from app.database import get_db_renovacion

        app.dependency_overrides[get_db_renovacion] = _override(db, ids)
        try:
            with _cliente() as client:
                r = client.get("/pago/comprar?plan=anual")
        finally:
            app.dependency_overrides.pop(get_db_renovacion, None)

    assert r.status_code == 200
    assert "Acceso suspendido" not in r.text
