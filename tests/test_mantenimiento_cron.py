"""Mantenimiento automático del despliegue (E4-021 / E4-023).

Un único trabajo programado (``/api/cron/mantenimiento``) hace cada día dos
cosas: genera el **respaldo automático por organización** (reutilizando el
paquete verificable de E3-020 y guardándolo en el almacenamiento privado con
retención) y ejecuta la **verificación diaria** de /readyz, alertando por
correo a los operadores si algo falla. Estas pruebas cubren el contorno:

- la ruta del cron existe, responde GET y exige el secreto compartido;
- el barrido genera un zip por organización, respeta el límite de tamaño y
  conserva solo las N copias más recientes;
- la verificación no escribe a nadie cuando todo está en verde y alerta a
  todos los operadores cuando falla.
"""

from datetime import date, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from app.database import Base, get_cron_db
from app.health import HealthStatus
from app.main import app
from app.models import Membresia, Organizacion, Usuario
from app.services import email as email_module
from app.services import mantenimiento
from app.storage import LocalStorage
from app import health as health_module


def _motor_y_sesion():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine)


def _sembrar(db, cantidad=2):
    ids = []
    for n in range(1, cantidad + 1):
        org = Organizacion(nombre=f"Constructora {n}", slug=f"constructora-{n}")
        usuario = Usuario(email=f"dueno{n}@example.com", nombre=f"Dueño {n}")
        db.add_all([org, usuario])
        db.flush()
        db.add(
            Membresia(
                organizacion_id=org.id, usuario_id=usuario.id, rol="propietario"
            )
        )
        db.flush()
        ids.append(org.id)
    db.commit()
    return ids


@pytest.fixture
def entorno_cron_mantenimiento(monkeypatch, tmp_path):
    engine, Session = _motor_y_sesion()
    with Session() as seed:
        ids = _sembrar(seed)
    storage = LocalStorage(tmp_path)
    monkeypatch.setattr(mantenimiento, "SessionLocal", Session)
    monkeypatch.setattr(mantenimiento, "get_storage_backend", lambda: storage)

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
        yield Session, ids, storage
    finally:
        app.dependency_overrides.pop(get_cron_db, None)
        engine.dispose()


def _cliente():
    return TestClient(app, base_url="https://cotizat.test")


# ---------------------------------------------------------------------------
# La ruta del cron
# ---------------------------------------------------------------------------


def test_la_ruta_del_cron_de_mantenimiento_existe_como_get():
    from app.routers import admin

    rutas = {
        getattr(r, "path", None): set(getattr(r, "methods", []) or [])
        for r in admin.router.routes
    }
    assert admin.CRON_MANTENIMIENTO_PATH in rutas, (
        "El cron de mantenimiento no está registrado en admin.router."
    )
    assert "GET" in rutas[admin.CRON_MANTENIMIENTO_PATH]


def test_el_cron_de_mantenimiento_rechaza_sin_secreto(entorno_cron_mantenimiento, monkeypatch):
    monkeypatch.delenv("CRON_SECRET", raising=False)
    with _cliente() as client:
        respuesta = client.get("/api/cron/mantenimiento")
    assert respuesta.status_code == 401

    monkeypatch.setenv("CRON_SECRET", "secreto-correcto")
    with _cliente() as client:
        respuesta = client.get(
            "/api/cron/mantenimiento",
            headers={"Authorization": "Bearer secreto-incorrecto"},
        )
    assert respuesta.status_code == 401


def test_el_cron_de_mantenimiento_responde_con_el_secreto(entorno_cron_mantenimiento, monkeypatch):
    monkeypatch.setenv("CRON_SECRET", "secreto-correcto")
    envios = []
    monkeypatch.setattr(
        email_module, "enviar_alerta_operador", lambda **kw: envios.append(kw) or "id-1"
    )
    monkeypatch.setattr(
        health_module, "_readiness_override",
        lambda: HealthStatus(ok=True, checks={"entorno": "producción"}),
    )

    with _cliente() as client:
        respuesta = client.get(
            "/api/cron/mantenimiento",
            headers={"Authorization": "Bearer secreto-correcto"},
        )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["ok"] is True
    assert cuerpo["respaldo"]["activado"] is True
    assert cuerpo["respaldo"]["generados"] == 2
    assert cuerpo["verificacion"]["ok"] is True
    assert envios == []


# ---------------------------------------------------------------------------
# Respaldo automático (E4-021)
# ---------------------------------------------------------------------------


def test_el_respaldo_automatico_genera_un_zip_por_organizacion(entorno_cron_mantenimiento):
    Session, ids, storage = entorno_cron_mantenimiento
    with Session() as db:
        db.info["es_operador"] = True
        resumen = mantenimiento.ejecutar_respaldo_automatico(db)

    assert resumen["organizaciones"] == 2
    assert resumen["generados"] == 2
    assert resumen["errores"] == 0
    for resultado in resumen["detalle"]:
        assert resultado["estado"] == "ok"
        assert "/respaldo_automatico/" in resultado["clave"]
        assert resultado["clave"].endswith(".zip")
        assert len(resultado["sha256"]) == 64
        assert storage.read(resultado["clave"])  # existe y se lee


def test_el_respaldo_conserva_solo_la_retencion_configurada(entorno_cron_mantenimiento, monkeypatch):
    Session, ids, storage = entorno_cron_mantenimiento
    monkeypatch.setenv("COTIZAT_RESPALDO_RETENCION", "5")
    org_id = ids[0]
    prefijo = f"organizaciones/{org_id}/respaldo_automatico/"
    for delta in range(20, 0, -1):
        fecha = (date.today() - timedelta(days=delta)).isoformat()
        storage.put(prefijo + f"cotizat-respaldo-{fecha}.zip", b"copia-antigua", "application/zip")
    viejas = storage.list(prefijo)
    assert len(viejas) == 20

    with Session() as db:
        db.info["es_operador"] = True
        mantenimiento.ejecutar_respaldo_automatico(db)

    restantes = storage.list(prefijo)
    assert len(restantes) == 5
    # La más reciente es la de hoy y se conservan las 4 anteriores más nuevas.
    assert any(c.endswith(f"cotizat-respaldo-{date.today().isoformat()}.zip") for c in restantes)


def test_el_respaldo_omitido_por_tamano_no_rompe_el_barrido(entorno_cron_mantenimiento, monkeypatch):
    Session, _ids, storage = entorno_cron_mantenimiento
    monkeypatch.setenv("COTIZAT_RESPALDO_MAX_MB", "1")
    monkeypatch.setattr(
        mantenimiento, "generar_respaldo", lambda db: b"x" * (2 * 1024 * 1024)
    )
    with Session() as db:
        db.info["es_operador"] = True
        resumen = mantenimiento.ejecutar_respaldo_automatico(db)

    assert resumen["generados"] == 0
    assert resumen["omitidos"] == 2
    assert all(r["estado"] == "omitido" for r in resumen["detalle"])
    assert "límite" in resumen["detalle"][0]["motivo"]


def test_el_respaldo_se_apaga_con_el_interruptor(entorno_cron_mantenimiento, monkeypatch):
    Session, _ids, storage = entorno_cron_mantenimiento
    monkeypatch.setenv("COTIZAT_RESPALDO_AUTOMATICO", "false")
    with Session() as db:
        db.info["es_operador"] = True
        resumen = mantenimiento.ejecutar_respaldo_automatico(db)

    assert resumen["activado"] is False
    assert resumen["generados"] == 0
    assert storage.list("") == []


# ---------------------------------------------------------------------------
# Verificación diaria con alerta (E4-023)
# ---------------------------------------------------------------------------


def test_verificacion_ok_no_envia_correo(monkeypatch):
    monkeypatch.setenv("COTIZAT_OPERADORES", "op@example.com,op2@example.com")
    monkeypatch.setattr(
        health_module, "_readiness_override",
        lambda: HealthStatus(ok=True, checks={"entorno": "producción"}),
    )
    envios = []
    monkeypatch.setattr(
        email_module, "enviar_alerta_operador", lambda **kw: envios.append(kw) or "id"
    )
    resumen = mantenimiento.ejecutar_verificacion_diaria()
    assert resumen["ok"] is True
    assert resumen["alertas_enviadas"] == 0
    assert envios == []


def test_verificacion_fallida_alerta_a_todos_los_operadores(monkeypatch):
    monkeypatch.setenv("COTIZAT_OPERADORES", "op@example.com,op2@example.com")
    monkeypatch.setattr(
        health_module, "_readiness_override",
        lambda: HealthStatus(
            ok=False, checks={"entorno": "producción"},
            errors=["Auth: no-configurado", "Storage: no-configurado"],
        ),
    )
    envios = []
    monkeypatch.setattr(
        email_module, "enviar_alerta_operador",
        lambda **kw: envios.append(kw) or "id",
    )
    resumen = mantenimiento.ejecutar_verificacion_diaria()
    assert resumen["ok"] is False
    assert resumen["errores"] == ["Auth: no-configurado", "Storage: no-configurado"]
    assert resumen["alertas_enviadas"] == 2
    assert [e["email"] for e in envios] == ["op2@example.com", "op@example.com"]
    assert envios[0]["errores"] == resumen["errores"]


def test_verificacion_sin_operadores_no_rompe(monkeypatch):
    monkeypatch.setenv("COTIZAT_OPERADORES", "")
    monkeypatch.setattr(
        health_module, "_readiness_override",
        lambda: HealthStatus(ok=False, checks={}, errors=["Algo falló"]),
    )
    resumen = mantenimiento.ejecutar_verificacion_diaria()
    assert resumen["ok"] is False
    assert resumen["alertas_enviadas"] == 0
