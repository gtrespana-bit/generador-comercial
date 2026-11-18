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


# ---------------------------------------------------------------------------
# Contención de egress/Storage (17/11/2026): omitir pruebas vencidas, corregir
# listado de SupabaseStorage y podar visitas_pagina en el cron diario.
# ---------------------------------------------------------------------------


def test_respaldo_automatico_omite_pruebas_vencidas_pero_guarda_recientes(
    entorno_cron_mantenimiento, monkeypatch
):
    from app.models import Licencia

    Session, ids, _storage = entorno_cron_mantenimiento
    hoy = date.today()
    with Session() as db:
        # Org 1: prueba vencida hace 10 días -> se omite.
        db.add(
            Licencia(
                organizacion_id=ids[0],
                estado="vencida",
                origen="prueba",
                inicio=hoy - timedelta(days=17),
                vence=hoy - timedelta(days=10),
            )
        )
        # Org 2: licencia activa -> se respalda.
        db.add(
            Licencia(
                organizacion_id=ids[1],
                estado="activa",
                origen="pago",
                inicio=hoy - timedelta(days=5),
                vence=hoy + timedelta(days=25),
                importe=29.0,
            )
        )
        # Org 3: venció ayer -> todavía recibe su última copia congelada.
        org3 = Organizacion(nombre="Recién vencida", slug="recien-vencida")
        # Org 4: marcada como test -> se omite.
        org4 = Organizacion(nombre="Interna test", slug="interna-test", es_test=True)
        db.add_all([org3, org4])
        db.flush()
        db.add(
            Licencia(
                organizacion_id=org3.id,
                estado="vencida",
                origen="prueba",
                inicio=hoy - timedelta(days=8),
                vence=hoy - timedelta(days=1),
            )
        )
        db.commit()

    with Session() as db:
        db.info["es_operador"] = True
        resumen = mantenimiento.ejecutar_respaldo_automatico(db)

    assert resumen["organizaciones"] == 4
    assert resumen["generados"] == 2
    assert resumen["omitidos"] == 2
    por_nombre = {d["organizacion"]: d["estado"] for d in resumen["detalle"]}
    assert por_nombre == {
        "Constructora 1": "omitido",
        "Constructora 2": "ok",
        "Recién vencida": "ok",
        "Interna test": "omitido",
    }

    # El interruptor permite forzar el barrido completo si hiciera falta.
    monkeypatch.setenv("COTIZAT_RESPALDO_SOLO_ACTIVAS", "false")
    with Session() as db:
        db.info["es_operador"] = True
        forzado = mantenimiento.ejecutar_respaldo_automatico(db)
    assert forzado["generados"] == 4


def test_supabase_storage_list_conserva_la_barra_para_purgar_retencion(
    monkeypatch, tmp_path
):
    import json

    from app.storage import StorageSettings, SupabaseStorage

    storage = SupabaseStorage(
        StorageSettings(
            backend="supabase",
            local_root=tmp_path,
            supabase_url="https://ejemplo.supabase.co",
            secret_key="sb_secret_prueba",  # pragma: allowlist secret
            bucket="cotizat-private",
        )
    )
    monkeypatch.setattr(
        storage,
        "_request",
        lambda *a, **kw: json.dumps(
            [
                {"name": "subcarpeta", "id": None},
                {"name": "cotizat-respaldo-2026-11-01.zip", "id": "obj-1"},
                {"name": "cotizat-respaldo-2026-11-02.zip", "id": "obj-2"},
            ]
        ).encode("utf-8"),
    )
    borradas: list[str] = []
    monkeypatch.setattr(storage, "delete", lambda clave: borradas.append(clave))

    claves = storage.list("organizaciones/7/respaldo_automatico/")
    assert claves == [
        "organizaciones/7/respaldo_automatico/cotizat-respaldo-2026-11-01.zip",
        "organizaciones/7/respaldo_automatico/cotizat-respaldo-2026-11-02.zip",
    ]
    purgadas = mantenimiento._purgar_antiguos(
        storage, 7, retencion=2, fecha=date(2026, 11, 3)
    )
    assert purgadas == [
        "organizaciones/7/respaldo_automatico/cotizat-respaldo-2026-11-01.zip"
    ]
    assert borradas == purgadas


def test_cron_mantenimiento_poda_visitas_antiguas(entorno_cron_mantenimiento, monkeypatch):
    from datetime import datetime

    from app.models import VisitaPagina

    Session, _ids, _storage = entorno_cron_mantenimiento
    monkeypatch.setenv("CRON_SECRET", "secreto-correcto")
    monkeypatch.setenv("COTIZAT_AUDIENCIA_RETENCION_DIAS", "30")
    monkeypatch.setattr(
        health_module,
        "_readiness_override",
        lambda: HealthStatus(ok=True, checks={"entorno": "producción"}),
    )

    with Session() as db:
        db.add_all(
            [
                VisitaPagina(
                    ruta="/vieja",
                    ip_hash="a" * 64,
                    created_at=datetime.utcnow() - timedelta(days=45),
                ),
                VisitaPagina(
                    ruta="/idioma/es",
                    ip_hash="b" * 64,
                    created_at=datetime.utcnow(),
                ),
                VisitaPagina(
                    ruta="/reciente",
                    ip_hash="c" * 64,
                    created_at=datetime.utcnow(),
                ),
            ]
        )
        db.commit()

    with _cliente() as client:
        respuesta = client.get(
            "/api/cron/mantenimiento",
            headers={"Authorization": "Bearer secreto-correcto"},
        )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["audiencia_poda"]["ok"] is True
    assert cuerpo["audiencia_poda"]["eliminadas"] == 2
    assert cuerpo["catalogos_hibernados"]["activado"] is True
    with Session() as db:
        assert [v.ruta for v in db.query(VisitaPagina).all()] == ["/reciente"]


def test_cron_mantenimiento_hiberna_catalogos_de_pruebas_vencidas(
    entorno_cron_mantenimiento, monkeypatch
):
    """El cron libera partidas oficiales intactas de pruebas vencidas >7 días."""
    from datetime import datetime

    from app.models import Configuracion, Licencia, Organizacion, Partida
    from app.services.catalogo_propio import CATALOGO_HIBERNADO, CATALOGO_VERSION

    Session, _, _ = entorno_cron_mantenimiento
    monkeypatch.setenv("CRON_SECRET", "secreto-correcto")  # pragma: allowlist secret
    monkeypatch.setenv("COTIZAT_RESPALDO_AUTOMATICO", "false")
    monkeypatch.setenv("COTIZAT_CATALOGO_HIBERNAR_DIAS", "7")
    monkeypatch.setattr(
        health_module,
        "_readiness_override",
        lambda: HealthStatus(ok=True, checks={"entorno": "producción"}),
    )

    antigua = datetime.utcnow() - timedelta(days=20)
    with Session() as db:
        # Org 1 es activa; creamos una prueba vencida hace 12 días con 1 oficial
        # intacta y 1 propia del cliente.
        org = Organizacion(
            nombre="Prueba Caducada",
            slug="prueba-caducada-hib",
            activa=True,
            created_at=antigua,
        )
        db.add(org)
        db.flush()
        db.add(
            Configuracion(
                organizacion_id=org.id,
                empresa_nombre="Prueba Caducada",
                onboarding_completado=True,
                onboarding_modo="demo",
                semilla_catalogo_aplicada=True,
                version_catalogo=CATALOGO_VERSION,
            )
        )
        db.add(
            Licencia(
                organizacion_id=org.id,
                estado="activa",
                origen="prueba",
                inicio=date.today() - timedelta(days=19),
                vence=date.today() - timedelta(days=12),
            )
        )
        db.add_all(
            [
                Partida(
                    organizacion_id=org.id,
                    nombre="Oficial de fábrica",
                    precio_unitario=20.0,
                    es_oficial=True,
                    version_catalogo=CATALOGO_VERSION,
                    catalogo_uid="cp:99.01",
                    descomposicion_json='{"origen": "catalogo_propio", "filas": []}',
                    created_at=antigua,
                    fecha_actualizacion_precio=antigua,
                ),
                Partida(
                    organizacion_id=org.id,
                    nombre="Propia intocable",
                    precio_unitario=55.0,
                    es_oficial=False,
                    version_catalogo=0,
                    descomposicion_json='{"origen": "manual", "filas": []}',
                    created_at=antigua,
                    fecha_actualizacion_precio=antigua,
                ),
            ]
        )
        db.commit()
        org_id = org.id

    with _cliente() as client:
        respuesta = client.get(
            "/api/cron/mantenimiento",
            headers={"Authorization": "Bearer secreto-correcto"},
        )

    assert respuesta.status_code == 200
    hib = respuesta.json()["catalogos_hibernados"]
    assert hib["activado"] is True
    assert hib["organizaciones"] == 1
    assert hib["partidas"] == 1
    with Session() as db:
        nombres = [
            p.nombre
            for p in db.query(Partida).filter_by(organizacion_id=org_id).all()
        ]
        assert nombres == ["Propia intocable"]
        cfg = db.query(Configuracion).filter_by(organizacion_id=org_id).one()
        assert cfg.version_catalogo == CATALOGO_HIBERNADO
