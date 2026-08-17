"""Enlaces públicos seguros y revocables de propuestas (E3-017)."""
from datetime import date, datetime, timedelta
from io import BytesIO

import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import main as main_module
from app.routers import common
from app.database import Base, get_db, get_public_proposal_db
from app.main import app
from app.models import (
    Capitulo,
    Cliente,
    Configuracion,
    EnlacePropuesta,
    Membresia,
    NotaSeguimiento,
    Organizacion,
    Presupuesto,
    PresupuestoItem,
    PresupuestoVersion,
    Usuario,
)
from app.services.propuestas import (
    crear_enlace_propuesta,
    hash_token_propuesta,
    registrar_respuesta_propuesta,
    resolver_enlace_propuesta,
)
from app.storage import reset_storage_backend_cache
from migrations.versions import c2f6e8a1d934_public_proposal_links as migration


@pytest.fixture
def entorno_enlaces(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as seed:
        org = Organizacion(nombre="Empresa Enlaces", slug="empresa-enlaces")
        usuario = Usuario(
            auth_user_id="00000000-0000-4000-8000-000000000017",
            email="empresa@example.com",
            nombre="Responsable",
            email_verificado_at=datetime(2026, 8, 16),
        )
        seed.add_all([org, usuario])
        seed.flush()
        seed.info["organizacion_id"] = org.id
        seed.info["rol_membresia"] = "propietario"
        cfg = Configuracion(empresa_nombre="Reformas Seguras")
        cliente = Cliente(nombre="Familia Ejemplo", email="familia@example.com")
        seed.add_all([cfg, cliente])
        seed.flush()
        presupuesto = Presupuesto(
            numero="P-2026-017",
            year=2026,
            fecha=date(2026, 8, 16),
            validez_dias=30,
            titulo="Baño principal",
            estado="borrador",
            client_id=cliente.id,
        )
        cap = Capitulo(nombre="BAÑO", orden=1)
        cap.partidas.append(PresupuestoItem(
            nombre="Revestimiento", unidad="m2", cantidad=10,
            precio_unitario=25, orden=1,
        ))
        presupuesto.capitulos.append(cap)
        seed.add(presupuesto)
        seed.add(Membresia(
            usuario_id=usuario.id,
            organizacion_id=org.id,
            rol="propietario",
        ))
        seed.commit()
        ids = org.id, usuario.id, presupuesto.id

    monkeypatch.setenv("COTIZAT_STORAGE_BACKEND", "local")
    reset_storage_backend_cache()
    rol = {"valor": "propietario"}

    def db_privada(request: Request):
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

    def db_publica(token: str):
        db = Session()
        db.info["proposal_token_hash"] = hash_token_propuesta(token)
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = db_privada
    app.dependency_overrides[get_public_proposal_db] = db_publica
    try:
        yield Session, ids, rol
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_public_proposal_db, None)
        reset_storage_backend_cache()
        engine.dispose()


def cliente_web():
    return TestClient(app, base_url="https://cotizat.test")


def crear_desde_web(client, presupuesto_id, dias=30):
    return client.post(
        f"/presupuestos/{presupuesto_id}/enlace-publico",
        data={"duracion_dias": str(dias)},
        headers={"Origin": "https://cotizat.test"},
    )


def extraer_url(html: str) -> str:
    inicio = html.index('value="https://cotizat.test/propuestas/') + len('value="')
    return html[inicio:html.index('"', inicio)]


def test_crear_enlace_congela_pdf_muestra_secreto_una_vez_y_cambia_estado(
    entorno_enlaces, monkeypatch
):
    Session, ids, _rol = entorno_enlaces
    monkeypatch.setattr(
        main_module.pdf_service,
        "generar_pdf",
        lambda presupuesto, cfg: BytesIO(b"%PDF-1.4\npropuesta publica"),
    )
    monkeypatch.setattr(common, "DATABASE_IS_SQLITE", True)
    with cliente_web() as client:
        respuesta = crear_desde_web(client, ids[2])

    assert respuesta.status_code == 200
    url = extraer_url(respuesta.text)
    token = url.rsplit("/", 1)[-1]
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        presupuesto = db.get(Presupuesto, ids[2])
        enlace = db.query(EnlacePropuesta).one()
        version = db.query(PresupuestoVersion).one()
        assert presupuesto.estado == "enviado"
        assert enlace.token_hash == hash_token_propuesta(token)
        assert token != enlace.token_hash
        assert enlace.pdf_snapshot == version.pdf_snapshot
        assert version.pdf_snapshot.startswith("storage://")
        assert enlace.empresa_nombre == "Reformas Seguras"
        assert enlace.cliente_nombre == "Familia Ejemplo"
        assert db.query(NotaSeguimiento).count() == 1


def test_pagina_publica_y_pdf_solo_exponen_la_propuesta(entorno_enlaces, monkeypatch):
    _Session, ids, _rol = entorno_enlaces
    monkeypatch.setattr(
        main_module.pdf_service,
        "generar_pdf",
        lambda presupuesto, cfg: BytesIO(b"%PDF-1.4\ncontenido exacto"),
    )
    monkeypatch.setattr(common, "DATABASE_IS_SQLITE", True)
    with cliente_web() as client:
        creada = crear_desde_web(client, ids[2])
        url = extraer_url(creada.text)
        pagina = client.get(url)
        pdf = client.get(url + "/pdf")

    assert pagina.status_code == 200
    assert "P-2026-017" in pagina.text
    assert "Familia Ejemplo" in pagina.text
    assert "Baño principal" in pagina.text
    assert "Catálogo" not in pagina.text
    assert "storage://" not in pagina.text
    assert pagina.headers["cache-control"].startswith("no-store")
    assert pagina.headers["referrer-policy"] == "no-referrer"
    assert pagina.headers["x-robots-tag"] == "noindex, nofollow, noarchive"
    assert pdf.status_code == 200
    assert pdf.content == b"%PDF-1.4\ncontenido exacto"
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.headers["cache-control"].startswith("no-store")


def test_token_falso_revocado_y_caducado_responden_igual(entorno_enlaces, monkeypatch):
    Session, ids, _rol = entorno_enlaces
    monkeypatch.setattr(
        main_module.pdf_service,
        "generar_pdf",
        lambda presupuesto, cfg: BytesIO(b"%PDF-1.4\nrevocable"),
    )
    monkeypatch.setattr(common, "DATABASE_IS_SQLITE", True)
    with cliente_web() as client:
        creada = crear_desde_web(client, ids[2])
        url = extraer_url(creada.text)
        falso = client.get("/propuestas/" + "A" * 43)
        with Session() as db:
            db.info["organizacion_id"] = ids[0]
            enlace = db.query(EnlacePropuesta).one()
            enlace_id = enlace.id
        revocada = client.post(
            f"/presupuestos/{ids[2]}/enlaces/{enlace_id}/revocar",
            headers={"Origin": "https://cotizat.test"},
            follow_redirects=False,
        )
        despues = client.get(url)

    assert revocada.status_code == 303
    assert falso.status_code == despues.status_code == 404
    assert "Propuesta no disponible" in falso.text
    assert "Propuesta no disponible" in despues.text
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        assert db.query(EnlacePropuesta).one().revoked_at is not None


def test_nuevo_enlace_revoca_el_anterior(entorno_enlaces):
    Session, ids, _rol = entorno_enlaces
    ahora = datetime(2026, 8, 16, 12, 0)
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        p = db.get(Presupuesto, ids[2])
        cfg = db.query(Configuracion).one()
        v1 = PresupuestoVersion(
            presupuesto_id=p.id, numero_version=1, fecha=ahora,
            estado="enviado", total=p.total, datos_snapshot="{}",
            pdf_snapshot="storage://organizaciones/1/presupuestos/v1.pdf",
        )
        v2 = PresupuestoVersion(
            presupuesto_id=p.id, numero_version=2, fecha=ahora,
            estado="reenviado", total=p.total, datos_snapshot="{}",
            pdf_snapshot="storage://organizaciones/1/presupuestos/v2.pdf",
        )
        db.add_all([v1, v2])
        db.flush()
        primero, token1 = crear_enlace_propuesta(
            db, presupuesto=p, version=v1, config=cfg,
            creado_por_usuario_id=ids[1], duracion_dias=30, ahora=ahora,
        )
        segundo, token2 = crear_enlace_propuesta(
            db, presupuesto=p, version=v2, config=cfg,
            creado_por_usuario_id=ids[1], duracion_dias=30,
            ahora=ahora + timedelta(minutes=1),
        )
        db.commit()
        assert primero.revoked_at == ahora + timedelta(minutes=1)
        assert segundo.revoked_at is None
        assert resolver_enlace_propuesta(db, token=token1, ahora=ahora + timedelta(minutes=2)) is None
        assert resolver_enlace_propuesta(db, token=token2, ahora=ahora + timedelta(minutes=2)).id == segundo.id


def test_rol_lectura_no_genera_pdf_ni_enlace(entorno_enlaces, monkeypatch):
    Session, ids, rol = entorno_enlaces
    rol["valor"] = "lectura"
    generado = {"valor": False}

    def fake_pdf(*_args):
        generado["valor"] = True
        return BytesIO(b"%PDF-1.4")

    monkeypatch.setattr(main_module.pdf_service, "generar_pdf", fake_pdf)
    with cliente_web() as client:
        respuesta = crear_desde_web(client, ids[2])
    assert respuesta.status_code == 403
    assert not generado["valor"]
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        assert db.query(EnlacePropuesta).count() == 0


def test_aceptacion_publica_registra_identidad_version_y_una_sola_respuesta(
    entorno_enlaces, monkeypatch
):
    Session, ids, _rol = entorno_enlaces
    monkeypatch.setattr(
        main_module.pdf_service,
        "generar_pdf",
        lambda presupuesto, cfg: BytesIO(b"%PDF-1.4\\naceptacion"),
    )
    monkeypatch.setattr(common, "DATABASE_IS_SQLITE", True)
    avisos = []
    monkeypatch.setattr(
        common,
        "enviar_respuesta_propuesta_por_email",
        lambda **kwargs: avisos.append(kwargs) or "aviso-aceptacion-1",
    )
    with cliente_web() as client:
        creada = crear_desde_web(client, ids[2])
        url = extraer_url(creada.text)
        respuesta = client.post(
            url + "/responder",
            data={
                "decision": "aceptada",
                "nombre": "Ana Cliente",
                "email": "ana@example.com",
                "comentario": "Acepto el alcance indicado.",
                "declaracion": "confirmada",
            },
            headers={"Origin": "https://cotizat.test"},
            follow_redirects=False,
        )
        pagina = client.get(url)
        repetida = client.post(
            url + "/responder",
            data={
                "decision": "rechazada",
                "nombre": "Ana Cliente",
                "email": "ana@example.com",
                "comentario": "Cambio de opinión",
                "declaracion": "confirmada",
            },
            headers={"Origin": "https://cotizat.test"},
        )

    assert respuesta.status_code == 303
    assert pagina.status_code == 200
    assert "Propuesta aceptada" in pagina.text
    assert "Ana Cliente" in pagina.text
    assert "Aceptar propuesta" not in pagina.text
    assert repetida.status_code == 400
    assert "ya fue respondida" in repetida.text
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        enlace = db.query(EnlacePropuesta).one()
        assert enlace.respuesta == "aceptada"
        assert enlace.respondido_por_nombre == "Ana Cliente"
        assert enlace.respondido_por_email == "ana@example.com"
        assert enlace.respuesta_comentario == "Acepto el alcance indicado."
        assert enlace.responded_at is not None
        assert enlace.presupuesto_version_numero == 1
        assert enlace.estado_presupuesto_actualizado is True
        assert enlace.notificacion_enviada_at is not None
        assert enlace.notificacion_destinatarios == "empresa@example.com"
        assert enlace.notificacion_error == ""
        assert db.get(Presupuesto, ids[2]).estado == "aprobado"
        assert db.query(NotaSeguimiento).count() == 2
    assert len(avisos) == 1
    assert avisos[0]["email"] == "empresa@example.com"
    assert avisos[0]["respondido_por_email"] == "ana@example.com"
    assert avisos[0]["version_numero"] == 1


def test_respuesta_exige_declaracion_y_datos_validos(entorno_enlaces, monkeypatch):
    Session, ids, _rol = entorno_enlaces
    monkeypatch.setattr(
        main_module.pdf_service,
        "generar_pdf",
        lambda presupuesto, cfg: BytesIO(b"%PDF-1.4\\nvalidacion"),
    )
    monkeypatch.setattr(common, "DATABASE_IS_SQLITE", True)
    with cliente_web() as client:
        creada = crear_desde_web(client, ids[2])
        url = extraer_url(creada.text)
        sin_declarar = client.post(
            url + "/responder",
            data={
                "decision": "rechazada",
                "nombre": "Ana Cliente",
                "email": "ana@example.com",
            },
            headers={"Origin": "https://cotizat.test"},
        )
        email_invalido = client.post(
            url + "/responder",
            data={
                "decision": "rechazada",
                "nombre": "Ana Cliente",
                "email": "incorrecto",
                "declaracion": "confirmada",
            },
            headers={"Origin": "https://cotizat.test"},
        )

    assert sin_declarar.status_code == 400
    assert "autorizado" in sin_declarar.text
    assert email_invalido.status_code == 400
    assert "email válido" in email_invalido.text
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        enlace = db.query(EnlacePropuesta).one()
        assert enlace.respuesta == "pendiente"
        assert enlace.responded_at is None


def test_respuesta_de_version_antigua_no_sobrescribe_estado_actual(entorno_enlaces):
    Session, ids, _rol = entorno_enlaces
    ahora = datetime(2026, 8, 16, 14, 0)
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        p = db.get(Presupuesto, ids[2])
        p.estado = "enviado"
        cfg = db.query(Configuracion).one()
        v1 = PresupuestoVersion(
            presupuesto_id=p.id, numero_version=1, fecha=ahora,
            estado="enviado", total=p.total, datos_snapshot="{}",
            pdf_snapshot="storage://organizaciones/1/presupuestos/antigua.pdf",
        )
        db.add(v1)
        db.flush()
        enlace, _token = crear_enlace_propuesta(
            db, presupuesto=p, version=v1, config=cfg,
            creado_por_usuario_id=ids[1], duracion_dias=30, ahora=ahora,
        )
        v2 = PresupuestoVersion(
            presupuesto_id=p.id, numero_version=2, fecha=ahora + timedelta(minutes=1),
            estado="reenviado", total=p.total + 10, datos_snapshot="{}",
            pdf_snapshot="storage://organizaciones/1/presupuestos/nueva.pdf",
        )
        db.add(v2)
        db.flush()
        p.estado = "reenviado"
        registrar_respuesta_propuesta(
            db,
            enlace=enlace,
            decision="aceptada",
            nombre="Cliente Versión Antigua",
            email="version@example.com",
            ahora=ahora + timedelta(minutes=2),
        )
        db.commit()
        assert enlace.respuesta == "aceptada"
        assert enlace.estado_presupuesto_actualizado is False
        assert p.estado == "reenviado"


def test_fallo_de_aviso_no_pierde_respuesta_y_admite_reintento(
    entorno_enlaces, monkeypatch
):
    Session, ids, _rol = entorno_enlaces
    monkeypatch.setattr(
        main_module.pdf_service,
        "generar_pdf",
        lambda presupuesto, cfg: BytesIO(b"%PDF-1.4\\nreintento"),
    )
    monkeypatch.setattr(common, "DATABASE_IS_SQLITE", True)
    monkeypatch.setattr(
        common,
        "enviar_respuesta_propuesta_por_email",
        lambda **_kwargs: (_ for _ in ()).throw(
            main_module.EmailSendError("Proveedor temporalmente caído.")
        ),
    )
    with cliente_web() as client:
        creada = crear_desde_web(client, ids[2])
        url = extraer_url(creada.text)
        respuesta = client.post(
            url + "/responder",
            data={
                "decision": "rechazada",
                "nombre": "Cliente Prueba",
                "email": "cliente@example.com",
                "comentario": "No procede.",
                "declaracion": "confirmada",
            },
            headers={"Origin": "https://cotizat.test"},
            follow_redirects=False,
        )
    assert respuesta.status_code == 303
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        enlace = db.query(EnlacePropuesta).one()
        enlace_id = enlace.id
        assert enlace.respuesta == "rechazada"
        assert enlace.notificacion_enviada_at is None
        assert "Proveedor temporalmente caído" in enlace.notificacion_error
        assert db.get(Presupuesto, ids[2]).estado == "rechazado"

    monkeypatch.setattr(
        common,
        "enviar_respuesta_propuesta_por_email",
        lambda **_kwargs: "aviso-reintentado",
    )
    with cliente_web() as client:
        reintento = client.post(
            f"/presupuestos/{ids[2]}/enlaces/{enlace_id}/notificar",
            headers={"Origin": "https://cotizat.test"},
            follow_redirects=False,
        )
    assert reintento.status_code == 303
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        enlace = db.get(EnlacePropuesta, enlace_id)
        assert enlace.notificacion_enviada_at is not None
        assert enlace.notificacion_error == ""
        assert enlace.notificacion_destinatarios == "empresa@example.com"


def test_migracion_rls_publica_solo_select_por_hash_vigente(monkeypatch):
    statements = []

    class Bind:
        class dialect:
            name = "postgresql"

    class Batch:
        def __enter__(self): return self
        def __exit__(self, *_args): return False

    monkeypatch.setattr(migration.op, "get_bind", lambda: Bind())
    monkeypatch.setattr(migration.op, "execute", lambda sql: statements.append(str(sql)))
    monkeypatch.setattr(migration.op, "create_table", lambda *_a, **_k: None)
    monkeypatch.setattr(migration.op, "create_index", lambda *_a, **_k: None)

    migration.upgrade()
    sql = "\n".join(statements).upper()
    assert "FORCE ROW LEVEL SECURITY" in sql
    assert "CREATE POLICY COTIZAT_PROPOSAL_SELECT_PUBLIC" in sql
    assert "COTIZAT.PROPOSAL_TOKEN_HASH" in sql
    assert "REVOKED_AT IS NULL" in sql
    assert "EXPIRES_AT >" in sql
    assert "FOR UPDATE TO COTIZAT_APP" not in sql.split(
        "CREATE POLICY COTIZAT_PROPOSAL_SELECT_PUBLIC", 1
    )[1].split("CREATE POLICY", 1)[0]
    assert "GRANT SELECT, INSERT, UPDATE" in sql
    assert "DELETE" not in next(
        line for line in sql.splitlines() if "GRANT SELECT" in line
    )
    assert "CREATE OR REPLACE FUNCTION COTIZAT_SECURITY.RECORD_PROPOSAL_RESPONSE" in sql
    assert "SECURITY DEFINER" in sql
    assert "RESPUESTA = 'PENDIENTE'" in sql
    assert "GRANT EXECUTE ON FUNCTION" in sql
    assert "PROPOSAL_NOTIFICATION_RECIPIENTS" in sql
    assert "MARK_PROPOSAL_NOTIFICATION" in sql
    assert "ESTADO_PRESUPUESTO_ACTUALIZADO" in sql
    assert "AND V_VERSION_ID =" in sql
    # No existe política UPDATE pública: respuesta y aviso pasan por funciones limitadas.
    assert "PROPOSAL_UPDATE_PUBLIC" not in sql
