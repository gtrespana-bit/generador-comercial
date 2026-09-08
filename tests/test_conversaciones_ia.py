"""Persistencia tenant e interfaz de análisis de las conversaciones del asistente."""
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.models import (
    Base,
    ConversacionIA,
    Membresia,
    MensajeIA,
    Organizacion,
    Usuario,
    usar_organizacion,
)
from app.services.conversaciones_ia import (
    ConversacionIAError,
    eliminar_conversacion,
    exportar_conversacion,
    persistir_respuesta,
    purgar_conversaciones_expiradas,
    registrar_turno,
)
from app.services.panel_chats import (
    exportar_conversaciones,
    listar_conversaciones,
    obtener_conversacion,
)


@pytest.fixture
def Session():
    engine = create_engine("sqlite://")

    @event.listens_for(engine, "connect")
    def _foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    sesion = sessionmaker(bind=engine)
    try:
        yield sesion
    finally:
        engine.dispose()


def _organizaciones(Session):
    with Session() as db:
        usuario = Usuario(email="analista@example.com", nombre="Analista")
        db.add(usuario)
        db.flush()
        org_a = Organizacion(nombre="Obras A", slug="obras-a")
        org_b = Organizacion(nombre="Obras B", slug="obras-b")
        db.add_all([org_a, org_b])
        db.flush()
        db.add_all([
            Membresia(usuario_id=usuario.id, organizacion_id=org_a.id, rol="propietario"),
            Membresia(usuario_id=usuario.id, organizacion_id=org_b.id, rol="propietario"),
        ])
        db.commit()
        return usuario.id, org_a.id, org_b.id


def _sesion_tenant(db, organizacion_id, usuario_id):
    usar_organizacion(db, organizacion_id)
    db.info.update(
        usuario_id=usuario_id,
        auth_email="analista@example.com",
        rol_membresia="propietario",
    )


def test_guarda_turno_antes_de_respuesta_y_reutiliza_idempotencia(Session):
    usuario_id, org_a, _org_b = _organizaciones(Session)
    with Session() as db:
        _sesion_tenant(db, org_a, usuario_id)
        registro = registrar_turno(
            db,
            [{"role": "user", "content": "¿Cómo importo un APU?"}],
            turn_id="turno-1",
            contexto={"pagina": "/presupuestos/nuevo"},
        )
        assert registro.conversacion.usuario_email == "analista@example.com"
        assert [mensaje.rol for mensaje in registro.conversacion.mensajes] == ["user"]
        assert persistir_respuesta(
            db, registro.conversation_id, "Desde partidas, importa el archivo.", turn_id="turno-1"
        )

        reintento = registrar_turno(
            db,
            [{"role": "user", "content": "¿Cómo importo un APU?"}],
            public_id=registro.conversation_id,
            turn_id="turno-1",
        )
        assert reintento.respuesta_existente == "Desde partidas, importa el archivo."
        assert db.query(MensajeIA).count() == 2


def test_reconcilia_historial_completo_sin_duplicarlo(Session):
    usuario_id, org_a, _org_b = _organizaciones(Session)
    with Session() as db:
        _sesion_tenant(db, org_a, usuario_id)
        primero = registrar_turno(
            db, [{"role": "user", "content": "Primera duda"}], turn_id="t1"
        )
        persistir_respuesta(db, primero.conversation_id, "Primera respuesta", turn_id="t1")
        segundo = registrar_turno(
            db,
            [
                {"role": "user", "content": "Primera duda"},
                {"role": "assistant", "content": "Primera respuesta"},
                {"role": "user", "content": "Segunda duda"},
            ],
            public_id=primero.conversation_id,
            turn_id="t2",
        )
        assert segundo.respuesta_existente is None
        assert [fila.contenido for fila in db.query(MensajeIA).order_by(MensajeIA.orden)] == [
            "Primera duda", "Primera respuesta", "Segunda duda"
        ]


def test_el_filtro_tenant_no_permite_reutilizar_chat_de_otra_empresa(Session):
    usuario_id, org_a, org_b = _organizaciones(Session)
    with Session() as db:
        _sesion_tenant(db, org_a, usuario_id)
        de_a = registrar_turno(db, [{"role": "user", "content": "Secreto A"}], turn_id="a")

        _sesion_tenant(db, org_b, usuario_id)
        de_b = registrar_turno(
            db,
            [{"role": "user", "content": "Consulta B"}],
            public_id=de_a.conversation_id,
            turn_id="b",
        )
        assert de_b.conversation_id != de_a.conversation_id
        db.info.pop("organizacion_id")
        db.info["es_operador"] = True
        assert sorted(fila.contenido for fila in db.query(MensajeIA).all()) == [
            "Consulta B", "Secreto A"
        ]


def test_panel_global_filtra_y_exporta_solo_con_operador(Session):
    usuario_id, org_a, org_b = _organizaciones(Session)
    with Session() as db:
        _sesion_tenant(db, org_a, usuario_id)
        a = registrar_turno(db, [{"role": "user", "content": "Duda sobre mediciones"}], turn_id="a")
        persistir_respuesta(db, a.conversation_id, "Respuesta A", turn_id="a")
        _sesion_tenant(db, org_b, usuario_id)
        b = registrar_turno(db, [{"role": "user", "content": "Duda sobre cobros"}], turn_id="b")
        persistir_respuesta(db, b.conversation_id, "Respuesta B", turn_id="b")

        with pytest.raises(PermissionError):
            listar_conversaciones(db)

        db.info.pop("organizacion_id")
        db.info["es_operador"] = True
        datos = listar_conversaciones(db, q="mediciones")
        assert datos["total"] == 1
        assert datos["filas"][0]["conversacion"].public_id == a.conversation_id
        exportado = exportar_conversaciones(db, q="mediciones")
        assert exportado[0]["mensajes"][0]["content"] == "Duda sobre mediciones"
        assert obtener_conversacion(db, b.conversation_id)["organizacion"].nombre == "Obras B"
        assert exportar_conversacion(db, a.conversation_id, global_operador=True)["version"] == 1


def test_la_purga_global_no_se_puede_ejecutar_desde_un_tenant(Session):
    usuario_id, org_a, _org_b = _organizaciones(Session)
    with Session() as db:
        _sesion_tenant(db, org_a, usuario_id)
        registro = registrar_turno(db, [{"role": "user", "content": "Antigua"}], turn_id="old")
        db.query(ConversacionIA).filter_by(id=registro.conversacion.id).update(
            {ConversacionIA.expires_at: datetime.utcnow() - timedelta(days=1)},
            synchronize_session=False,
        )
        db.commit()
        with pytest.raises(ConversacionIAError, match="sesión de operador"):
            purgar_conversaciones_expiradas(db)
        assert db.query(ConversacionIA).count() == 1

        db.info.pop("organizacion_id")
        db.info["es_operador"] = True
        assert purgar_conversaciones_expiradas(db) == 1
        assert db.query(ConversacionIA).count() == 0


def test_eliminacion_de_operador_borra_hilo_y_mensajes(Session):
    usuario_id, org_a, _org_b = _organizaciones(Session)
    with Session() as db:
        _sesion_tenant(db, org_a, usuario_id)
        registro = registrar_turno(db, [{"role": "user", "content": "Borrar"}], turn_id="delete")
        persistir_respuesta(db, registro.conversation_id, "Respuesta", turn_id="delete")
        db.info.pop("organizacion_id")
        db.info["es_operador"] = True
        assert eliminar_conversacion(db, registro.conversation_id, global_operador=True) == (True, org_a)
        assert db.query(ConversacionIA).count() == 0
        assert db.query(MensajeIA).count() == 0
