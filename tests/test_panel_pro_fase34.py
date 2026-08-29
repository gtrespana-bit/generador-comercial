"""Fase 3 y 4 del panel profesional: web gobernable, CRM, vistas y API keys.

Comprueba servicios y rutas clave sin abrir el multi-tenant: todo el nuevo
estado es del titular (contenido, avisos, releases, flags, CRM, vistas,
API keys), no de una organización concreta.
"""
from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from app.database import Base, get_operator_db
from app.main import app
from app.models import Organizacion, Usuario, Membresia
from app.services import web_admin
from app.services.web_admin import (
    ESTADOS_CRM_ETIQUETA,
    GestionWebError,
    actualizar_flag,
    alternar_aviso,
    alternar_release,
    avisos_publicos,
    contenido_publico,
    crear_api_key,
    crear_aviso,
    crear_release,
    descartar_contenido,
    eliminar_vista,
    guardar_contenido,
    guardar_crm,
    guardar_vista,
    listar_api_keys,
    listar_avisos,
    listar_contenido,
    listar_crm,
    listar_flags,
    listar_releases,
    listar_vistas,
    publicar_contenido,
    releases_publicas,
    resumen_crm,
    revocar_api_key,
    verificar_api_key,
)
from app.services.web_publica import contexto_web_publico


def _db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine)()


def _org(db, nombre="Constructora F34", slug="f34"):
    org = Organizacion(nombre=nombre, slug=slug)
    db.add(org)
    db.commit()
    return org


def _operador_email(db):
    return str(db.info.get("auth_email") or "op@example.com")


# ---------------------------------------------------------------------------
# Contenido web: borrador/publicar/descartar
# ---------------------------------------------------------------------------

def test_contenido_se_guarda_como_borrador_y_publica_despues():
    engine, db = _db()
    try:
        guardar_contenido(
            db, clave="landing.hero",
            campos={"titulo": "Presupuestos de obra sin hojas", "cta": "Empezar"},
            operador_email="op@example.com",
        )
        db.commit()
        filas = listar_contenido(db)
        hero = next(f for f in filas if f["clave"] == "landing.hero")
        assert hero["borrador"]["titulo"] == "Presupuestos de obra sin hojas"
        assert hero["publicado"] == {}

        publicar_contenido(db, clave="landing.hero", operador_email="op@example.com")
        db.commit()
        assert contenido_publico(db, "landing.hero")["cta"] == "Empezar"
        assert web_admin.contenido_publico(db, "landing.hero")["titulo"] == "Presupuestos de obra sin hojas"

        descartar_contenido(db, clave="landing.hero")
        db.commit()
        assert contenido_publico(db, "landing.hero")["cta"] == "Empezar"
    finally:
        db.close()
        engine.dispose()


def test_publicar_sin_borrador_falla():
    from app.models import ContenidoWeb

    engine, db = _db()
    try:
        db.add(ContenidoWeb(clave="landing.hero", borrador="{}"))
        db.commit()
        with pytest.raises(GestionWebError, match="No hay borrador"):
            publicar_contenido(db, clave="landing.hero", operador_email="op@example.com")
        with pytest.raises(GestionWebError, match="no existe"):
            descartar_contenido(db, clave="seo.no-existe")
    finally:
        db.close()
        engine.dispose()


# ---------------------------------------------------------------------------
# Avisos y releases: visibilidad pública
# ---------------------------------------------------------------------------

def test_avisos_solo_activos_con_ventana_visible_y_campos_validados():
    engine, db = _db()
    try:
        crear_aviso(db, tipo="mantenimiento", nivel="warning", titulo="Mantenimiento", mensaje="Hoy 22h", activo=True)
        crear_aviso(db, tipo="legal", nivel="info", titulo="Legal", mensaje="Mensaje", activo=False)
        crear_aviso(
            db, tipo="version", nivel="info", titulo="Futuro", mensaje="",
            activo=True,
            inicio=date.today() + timedelta(days=10), fin=date.today() + timedelta(days=20),
        )
        db.commit()
        publicos = avisos_publicos(db)
        assert [a.titulo for a in publicos] == ["Mantenimiento"]

        with pytest.raises(GestionWebError, match="tipo"):
            crear_aviso(db, tipo="otro", nivel="info", titulo="X", mensaje="")
        with pytest.raises(GestionWebError, match="nivel"):
            crear_aviso(db, tipo="info", nivel="otro", titulo="X", mensaje="")
    finally:
        db.close()
        engine.dispose()


def test_releases_solo_publicadas_y_alternar_visibilidad():
    engine, db = _db()
    try:
        r1 = crear_release(db, version="v2.1.0", titulo="Mejoras", notas="Nuevo CMS", publicado=False)
        r2 = crear_release(db, version="v2.0.0", titulo="Base", notas="Lanzamiento", publicado=True, fecha=date(2026, 1, 1))
        db.commit()
        assert [r.version for r in releases_publicas(db)] == ["v2.0.0"]

        alternar_release(db, r1.id, publicado=True)
        db.commit()
        assert [r.version for r in releases_publicas(db)] == ["v2.1.0", "v2.0.0"]
        alternar_release(db, r2.id, publicado=False)
        db.commit()
        assert [r.version for r in releases_publicas(db)] == ["v2.1.0"]
    finally:
        db.close()
        engine.dispose()


# ---------------------------------------------------------------------------
# Flags, vistas guardadas y CRM
# ---------------------------------------------------------------------------

def test_flags_vistas_y_crm_son_del_operador():
    engine, db = _db()
    try:
        org = _org(db)
        actualizar_flag(db, clave="cms", activo=True, operador_email="op@example.com")
        db.commit()
        assert next(f for f in listar_flags(db) if f["clave"] == "cms")["activo"] is True

        vista = guardar_vista(
            db, modulo="cobros", nombre="Pendientes",
            filtros={"estado": "pendiente"}, columnas=["organizacion", "importe"],
            operador_email="op@example.com",
        )
        db.commit()
        assert listar_vistas(db)[0].filtros_dict() == {"estado": "pendiente"}
        eliminar_vista(db, vista.id)
        db.commit()
        assert listar_vistas(db) == []

        guardar_crm(
            db, organizacion_id=org.id, estado="riesgo",
            proximo_contacto=date.today(), notas="Renovar contrato",
            operador_email="op@example.com",
        )
        db.commit()
        assert listar_crm(db)[0]["estado"] == "riesgo"
        assert resumen_crm(db)["por_estado"] == {"riesgo": 1}
        assert resumen_crm(db)["proximos"][0]["organizacion"].id == org.id
    finally:
        db.close()
        engine.dispose()


# ---------------------------------------------------------------------------
# API keys: hash, rotación y revocación
# ---------------------------------------------------------------------------

def test_api_keys_solo_guardan_hash_y_verifican_token():
    engine, db = _db()
    try:
        clave, token = crear_api_key(db, nombre="Cron", scopes=["cobros.leer"], operador_email="op@example.com")
        db.commit()
        assert clave.clave_hash != token
        assert len(clave.clave_hash) == 64
        assert verificar_api_key(db, token) is not None
        assert verificar_api_key(db, "cotizat_inventada") is None

        revocar_api_key(db, clave.id)
        db.commit()
        assert verificar_api_key(db, token) is None
        assert listar_api_keys(db)[0]["activo"] is False
    finally:
        db.close()
        engine.dispose()


# ---------------------------------------------------------------------------
# Rutas del panel (una sola pasada por cada bloque)
# ---------------------------------------------------------------------------

@pytest.fixture
def entorno_admin(monkeypatch):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as seed:
        org = Organizacion(nombre="Org F34", slug="org-f34")
        usuario = Usuario(auth_user_id="auth-f34", email="u@example.com", nombre="U")
        seed.add_all([org, usuario])
        seed.flush()
        seed.add(Membresia(organizacion_id=org.id, usuario_id=usuario.id, rol="propietario"))
        seed.commit()
        datos = {"organizacion_id": org.id, "usuario_id": usuario.id}

    def _db_operador():
        db = Session()
        db.info["es_operador"] = True
        db.info["auth_email"] = "op@example.com"
        db.info["operador_rol"] = "superadmin"
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_operator_db] = _db_operador
    try:
        yield TestClient(app), Session, datos
    finally:
        app.dependency_overrides.pop(get_operator_db, None)
        engine.dispose()


def test_novedades_publica_renderiza(cliente_web):
    respuesta = cliente_web.get("/novedades")
    assert respuesta.status_code == 200
    assert "Novedades y versiones" in respuesta.text


def test_rutas_fase3_y_4_renderizan_sin_error(entorno_admin):
    cliente, Session, datos = entorno_admin
    with Session() as db:
        guardar_contenido(db, clave="landing.hero", campos={"titulo": "Hola"}, operador_email="op@example.com")
        publicar_contenido(db, clave="landing.hero", operador_email="op@example.com")
        crear_aviso(db, tipo="info", nivel="info", titulo="Banner", mensaje="", activo=True)
        crear_release(db, version="v9.0", titulo="Nueva", notas="", publicado=True)
        actualizar_flag(db, clave="cms", activo=True, operador_email="op@example.com")
        guardar_crm(db, organizacion_id=datos["organizacion_id"], estado="activo", proximo_contacto=None, notas="", operador_email="op@example.com")
        guardar_vista(db, modulo="clientes", nombre="Todos", filtros={}, columnas=[], operador_email="op@example.com")
        db.commit()

    for ruta in ("/admin/web", "/admin/avisos", "/admin/releases", "/admin/flags",
                 "/admin/crm", "/admin/vistas", "/admin/salud-datos", "/admin/api-keys"):
        respuesta = cliente.get(ruta)
        assert respuesta.status_code == 200, f"{ruta} devolvió {respuesta.status_code}"
        assert respuesta.headers["cache-control"] == "no-store"
