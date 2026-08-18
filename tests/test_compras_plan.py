"""Compra de planes con pago manual: registro, comprobante y activación.

Cubre el flujo E1-059: el cliente elige plan y método, sube su comprobante,
la compra queda pendiente y el operador la activa desde el panel concediendo
la licencia del plan.
"""
from datetime import date
import io

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import CompraPlan, Licencia, Membresia, Organizacion, Usuario
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
        app.dependency_overrides[get_db] = _override(db, ids)
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
            app.dependency_overrides.pop(get_db, None)


def test_pagina_comprar_plan_desconocido_redirige(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        db.info["usuario_id"] = ids[1]
        db.info["rol_membresia"] = "propietario"
        app.dependency_overrides[get_db] = _override(db, ids)
        try:
            with _cliente() as client:
                r = client.get("/pago/comprar?plan=vitalicio", follow_redirects=False)
            assert r.status_code == 303
            assert r.headers["location"].startswith("/pago")
        finally:
            app.dependency_overrides.pop(get_db, None)


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
        app.dependency_overrides[get_db] = _override(db, ids)
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
                    files={"comprobante": ("recibo.png", _png_minimo(), "image/png")},
                    follow_redirects=False,
                )
            assert r.status_code == 303
            assert "/pago/confirmacion?id=" in r.headers["location"]
        finally:
            app.dependency_overrides.pop(get_db, None)
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
        app.dependency_overrides[get_db] = _override(db, ids)
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
            app.dependency_overrides.pop(get_db, None)
            reset_storage_backend_cache()


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

        app.dependency_overrides[get_db] = _override(db, ids)
        try:
            with _cliente() as client:
                r = client.get(f"/pago/confirmacion?id={compra_id}")
            assert r.status_code == 200
            assert "¡Compra registrada!" in r.text
            assert "Plan mensual" in r.text
            assert "#" + str(compra_id) in r.text
        finally:
            app.dependency_overrides.pop(get_db, None)
            reset_storage_backend_cache()


def _override(db, ids):
    def _get_db(request=None):
        try:
            yield db
        finally:
            pass

    return _get_db


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
