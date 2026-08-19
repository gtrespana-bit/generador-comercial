"""E4-026 / E4-027 — registro de auditoría inmutable.

Cubre el servicio (best-effort, nunca rompe el flujo), los anclajes HTTP
(estados, enlaces, configuración, respaldo, exportación, catálogo), los
eventos globales de sesión, la vista «Actividad» con su permiso, y la
corrección de la baja (compras_plan y eventos_auditoria incluidos en ambos
caminos: ORM/SQLite y función PostgreSQL).
"""
import json
from datetime import date

import pytest

from app.models import CompraPlan, EventoAuditoria, Organizacion, Presupuesto
from app.services import auditoria

from migrations.versions import (
    d2a7c9e4f1b3_audit_log_and_complete_baja as migracion,
)

from tests.conftest import NOMBRE_ORG, ORIGEN


def _eventos(Session, org_id, accion=None):
    with Session() as db:
        consulta = db.query(EventoAuditoria).filter(
            EventoAuditoria.organizacion_id == org_id
        )
        if accion:
            consulta = consulta.filter(EventoAuditoria.accion == accion)
        return consulta.order_by(EventoAuditoria.id).all()


# ---------------------------------------------------------------------------
# Servicio: best-effort y contratos básicos
# ---------------------------------------------------------------------------

def test_registrar_evento_guarda_actor_y_detalle(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        db.info["auth_email"] = "duena@example.com"
        db.info["rol_membresia"] = "propietario"
        assert auditoria.registrar_evento(
            db,
            "presupuesto.estado",
            entidad="presupuesto",
            entidad_id=7,
            detalle={"de": "borrador", "a": "aprobado"},
        )
    eventos = _eventos(Session, ids[0], "presupuesto.estado")
    assert len(eventos) == 1
    evento = eventos[0]
    assert evento.actor_email == "duena@example.com"
    assert evento.actor_rol == "propietario"
    assert evento.entidad == "presupuesto"
    assert evento.entidad_id == 7
    assert evento.detalle_dict() == {"de": "borrador", "a": "aprobado"}


def test_registrar_evento_sin_organizacion_no_inserta(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        assert auditoria.registrar_evento(db, "presupuesto.estado") is False
    assert _eventos(Session, ids[0]) == []


def test_registrar_evento_nunca_lanza_si_la_base_falla(entorno):
    """La auditoría jamás puede tumbar el flujo principal."""
    Session, ids, _rol = entorno
    llamadas = {"rollback": 0}
    with Session() as db:
        db.info["organizacion_id"] = ids[0]

        def _commit_roto():
            raise RuntimeError("base caída")

        rollback_real = db.rollback

        def _rollback():
            llamadas["rollback"] += 1
            rollback_real()

        db.commit = _commit_roto
        db.rollback = _rollback
        assert auditoria.registrar_evento(db, "presupuesto.estado") is False
    assert llamadas["rollback"] == 1


def test_detalle_desmedido_se_descarta_pero_el_evento_queda(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        assert auditoria.registrar_evento(
            db, "configuracion.actualizada", detalle={"x": "a" * 5000}
        )
    evento = _eventos(Session, ids[0], "configuracion.actualizada")[0]
    assert evento.detalle == "{}"


def test_evento_global_rechaza_acciones_fuera_de_la_lista(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        assert (
            auditoria.registrar_evento_global(
                db, "catalogo.precio_partida", email="x@example.com"
            )
            is False
        )
        assert auditoria.registrar_evento_global(
            db, "sesion.login", email="x@example.com", ip_hash="abc"
        )
        globales = (
            db.query(EventoAuditoria)
            .filter(EventoAuditoria.organizacion_id.is_(None))
            .all()
        )
    assert [e.accion for e in globales] == ["sesion.login"]
    assert globales[0].actor_email == "x@example.com"
    assert globales[0].ip_hash == "abc"


def test_anotar_sesion_escribe_con_sesion_propia():
    """El helper de login/logout no depende de la sesión de la petición."""
    from app.database import SessionLocal

    assert auditoria.anotar_sesion("sesion.login", email="Alta@Example.com")
    with SessionLocal() as db:
        evento = (
            db.query(EventoAuditoria)
            .filter(
                EventoAuditoria.organizacion_id.is_(None),
                EventoAuditoria.accion == "sesion.login",
            )
            .order_by(EventoAuditoria.id.desc())
            .first()
        )
        assert evento is not None
        assert evento.actor_email == "alta@example.com"


# ---------------------------------------------------------------------------
# Anclajes HTTP: los cambios reales dejan rastro
# ---------------------------------------------------------------------------

def test_cambio_de_estado_de_presupuesto_deja_rastro(entorno, cliente_web):
    Session, ids, _rol = entorno
    respuesta = cliente_web.post(
        f"/presupuestos/{ids[2]}/estado",
        data={"estado": "en_revision"},
        headers={"Origin": ORIGEN},
        follow_redirects=False,
    )
    assert respuesta.status_code == 303
    eventos = _eventos(Session, ids[0], "presupuesto.estado")
    assert len(eventos) == 1
    assert eventos[0].entidad_id == ids[2]
    assert eventos[0].detalle_dict()["a"] == "en_revision"


def test_estado_invalido_no_deja_rastro(entorno, cliente_web):
    Session, ids, _rol = entorno
    cliente_web.post(
        f"/presupuestos/{ids[2]}/estado",
        data={"estado": "no-existe"},
        headers={"Origin": ORIGEN},
        follow_redirects=False,
    )
    assert _eventos(Session, ids[0], "presupuesto.estado") == []


def test_revocar_enlace_publico_deja_rastro(entorno, cliente_web):
    Session, ids, _rol = entorno
    from app.models import EnlacePropuesta

    with Session() as db:
        enlace = (
            db.query(EnlacePropuesta)
            .filter(EnlacePropuesta.revoked_at.is_(None))
            .first()
        )
        enlace_id = enlace.id
        presupuesto_id = enlace.presupuesto_id
    respuesta = cliente_web.post(
        f"/presupuestos/{presupuesto_id}/enlaces/{enlace_id}/revocar",
        headers={"Origin": ORIGEN},
        follow_redirects=False,
    )
    assert respuesta.status_code == 303
    eventos = _eventos(Session, ids[0], "propuesta.enlace_revocado")
    assert len(eventos) == 1
    assert eventos[0].detalle_dict()["enlace_id"] == enlace_id


def test_guardar_configuracion_y_renombrar_dejan_rastro(entorno, cliente_web):
    Session, ids, _rol = entorno
    respuesta = cliente_web.post(
        "/configuracion",
        data={
            "empresa_nombre": "Empresa Auditada",
            "organizacion_nombre": "Organización Renombrada",
        },
        headers={"Origin": ORIGEN},
        follow_redirects=False,
    )
    assert respuesta.status_code == 303
    assert len(_eventos(Session, ids[0], "configuracion.actualizada")) == 1
    renombres = _eventos(Session, ids[0], "organizacion.renombrada")
    assert len(renombres) == 1
    assert renombres[0].detalle_dict() == {
        "de": NOMBRE_ORG,
        "a": "Organización Renombrada",
    }


def test_respaldo_y_exportacion_dejan_rastro(entorno, cliente_web):
    Session, ids, _rol = entorno
    assert cliente_web.get("/configuracion/respaldo/descargar").status_code == 200
    assert (
        cliente_web.get("/configuracion/exportacion/descargar").status_code == 200
    )
    assert len(_eventos(Session, ids[0], "datos.respaldo_descargado")) == 1
    assert len(_eventos(Session, ids[0], "datos.exportacion_descargada")) == 1


def test_ajuste_masivo_de_precios_deja_rastro(entorno, cliente_web):
    Session, ids, _rol = entorno
    respuesta = cliente_web.post(
        "/partidas/ajustar",
        data={"porcentaje": "5"},
        headers={"Origin": ORIGEN},
        follow_redirects=False,
    )
    assert respuesta.status_code == 303
    eventos = _eventos(Session, ids[0], "catalogo.precios_ajustados")
    assert len(eventos) == 1
    assert eventos[0].detalle_dict()["porcentaje"] == 5.0


# ---------------------------------------------------------------------------
# Vista «Actividad»
# ---------------------------------------------------------------------------

def test_actividad_visible_para_gestion(entorno, cliente_web):
    Session, ids, _rol = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        db.info["auth_email"] = "duena@example.com"
        auditoria.registrar_evento(
            db,
            "presupuesto.estado",
            entidad="presupuesto",
            entidad_id=ids[2],
            detalle={"de": "borrador", "a": "aprobado"},
        )
    pagina = cliente_web.get("/configuracion/actividad")
    assert pagina.status_code == 200
    assert "Registro de actividad" in pagina.text
    assert "duena@example.com" in pagina.text
    assert "Estado del presupuesto" in pagina.text
    assert "borrador → aprobado" in pagina.text


def test_actividad_pagina_y_ordena_lo_reciente_primero(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        for i in range(3):
            auditoria.registrar_evento(
                db, "configuracion.actualizada", entidad_id=i
            )
        eventos, total = auditoria.eventos_de_organizacion(
            db, pagina=1, por_pagina=2
        )
        assert total == 3
        assert [e.entidad_id for e in eventos] == [2, 1]
        eventos2, _ = auditoria.eventos_de_organizacion(db, pagina=2, por_pagina=2)
        assert [e.entidad_id for e in eventos2] == [0]


def test_actividad_no_muestra_eventos_de_otra_organizacion(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        otra = Organizacion(nombre="Ajena", slug="ajena")
        db.add(otra)
        db.commit()
        db.add(
            EventoAuditoria(
                organizacion_id=otra.id,
                accion="configuracion.actualizada",
                actor_email="ajena@example.com",
            )
        )
        db.commit()
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        eventos, total = auditoria.eventos_de_organizacion(db)
        assert total == 0
        assert eventos == []


# ---------------------------------------------------------------------------
# Baja completa: compras_plan (bug corregido) y eventos incluidos
# ---------------------------------------------------------------------------

def test_baja_borra_compras_y_eventos_de_la_organizacion(entorno, cliente_web):
    """Regresión del bug latente: una organización con compras registradas
    no podía darse de baja (FK RESTRICT de compras_plan)."""
    Session, ids, _rol = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        db.info["rol_membresia"] = "propietario"
        db.add(
            CompraPlan(
                plan="mensual",
                metodo_pago="binance",
                importe=9.99,
                creada_por_email="duena@example.com",
            )
        )
        db.commit()
        auditoria.registrar_evento(db, "plan.compra_registrada", entidad="compra")

    respuesta = cliente_web.post(
        "/configuracion/baja/confirmar",
        data={"nombre_confirmado": NOMBRE_ORG, "confirmar": "si"},
        headers={"Origin": ORIGEN},
        follow_redirects=False,
    )
    assert respuesta.status_code == 200

    with Session() as db:
        assert db.get(Organizacion, ids[0]) is None
        assert (
            db.query(CompraPlan)
            .filter(CompraPlan.organizacion_id == ids[0])
            .count()
            == 0
        )
        assert (
            db.query(EventoAuditoria)
            .filter(EventoAuditoria.organizacion_id == ids[0])
            .count()
            == 0
        )


def test_funcion_postgresql_de_baja_incluye_las_tablas_nuevas():
    """La función PG actualizada borra compras_plan y eventos_auditoria; la
    versión restaurada por el downgrade, no (fiel a la original)."""
    assert "DELETE FROM public.compras_plan" in migracion.BAJA_ACTUALIZADA_SQL
    assert (
        "DELETE FROM public.eventos_auditoria" in migracion.BAJA_ACTUALIZADA_SQL
    )
    assert "DELETE FROM public.compras_plan" not in migracion.BAJA_ANTERIOR_SQL
    # El orden importa: las tablas nuevas se borran antes que la organización.
    cuerpo = migracion.BAJA_ACTUALIZADA_SQL
    assert cuerpo.index("compras_plan") < cuerpo.index(
        "DELETE FROM public.organizaciones"
    )


# ---------------------------------------------------------------------------
# Contratos de la migración: inmutabilidad y lista cerrada
# ---------------------------------------------------------------------------

def test_el_rol_runtime_no_recibe_update_ni_delete():
    """La inmutabilidad no depende del código: el GRANT no los incluye."""
    import inspect

    fuente = inspect.getsource(migracion.upgrade)
    assert "GRANT SELECT, INSERT ON TABLE public.eventos_auditoria" in (
        fuente.replace("{TABLE}", "eventos_auditoria")
        .replace('f"', '"')
    ) or "SELECT, INSERT" in fuente
    assert "UPDATE" not in [
        linea.strip()
        for linea in fuente.splitlines()
        if "GRANT" in linea and "TABLE" in linea
    ]


def test_no_existen_politicas_de_update_ni_delete():
    import inspect

    fuente = inspect.getsource(migracion)
    politicas = [
        linea for linea in fuente.splitlines() if "cotizat_evento_" in linea
    ]
    assert politicas, "las políticas deben existir"
    assert not any('"UPDATE"' in linea or '"DELETE"' in linea for linea in politicas)


def test_lista_cerrada_de_acciones_globales_coincide_con_el_servicio():
    """El servicio y la función PostgreSQL validan la misma lista."""
    for accion in auditoria.ACCIONES_GLOBALES:
        assert f"'{accion}'" in migracion.ACCIONES_GLOBALES_SQL
    # Y nada más: la lista SQL no admite acciones que el servicio no declare.
    entre_comillas = {
        parte.strip().strip("'")
        for parte in migracion.ACCIONES_GLOBALES_SQL.split(",")
    }
    assert entre_comillas == set(auditoria.ACCIONES_GLOBALES)
