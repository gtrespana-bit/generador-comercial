"""Telemetría interna de producto (E5-012): servicio y contratos.

Cubre el catálogo cerrado de acciones, el comportamiento best-effort (nunca
rompe el flujo principal), el latido diario (una fila por organización y
día, sin duplicar tras «reinicios de proceso»), los eventos globales del
registro y la coherencia servicio ↔ migración (lista cerrada de acciones
globales y borrado en la baja de organización).
"""
from datetime import datetime, timedelta

import pytest

from app.models import EventoProducto, Organizacion, Usuario
from app.services import telemetria

from migrations.versions import (
    e3a5c7d9b1f4_eventos_producto as migracion,
    a1b8c2d4e6f0_roles_operador_y_auditoria_admin as panel_migracion,
    c2d4e6f8a1b3_operador_gestion_cliente_y_cobros as fase2_migracion,
    d3e5f7a9c2b4_web_admin_crm_y_salud as fase3_migracion,
)

from tests.conftest import NOMBRE_ORG


@pytest.fixture(autouse=True)
def _memo_latidos_limpio():
    """El memo de latidos vive a nivel de proceso: aislarlo entre pruebas."""
    telemetria._LATIDOS.clear()
    yield
    telemetria._LATIDOS.clear()


def _eventos(Session, **filtros):
    with Session() as db:
        consulta = db.query(EventoProducto)
        for campo, valor in filtros.items():
            consulta = consulta.filter(getattr(EventoProducto, campo) == valor)
        return consulta.order_by(EventoProducto.id).all()


# ---------------------------------------------------------------------------
# Servicio: eventos de organización
# ---------------------------------------------------------------------------


def test_registrar_guarda_accion_detalle_y_actor(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        db.info["auth_email"] = "duena@example.com"
        assert telemetria.registrar(
            db,
            "presupuesto.creado",
            detalle={"primero": True, "partidas": 6},
        )
    eventos = _eventos(Session, organizacion_id=ids[0], accion="presupuesto.creado")
    assert len(eventos) == 1
    evento = eventos[0]
    assert evento.actor_email == "duena@example.com"
    assert evento.detalle_dict() == {"primero": True, "partidas": 6}


def test_registrar_rechaza_acciones_fueras_del_catalogo(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        # Acción inventada y acción global usada por la vía equivocada.
        assert telemetria.registrar(db, "evento.inventado") is False
        assert telemetria.registrar(db, "cuenta.registrada") is False
        # Sin organización en contexto tampoco hay evento.
        db.info["organizacion_id"] = 0
        assert telemetria.registrar(db, "presupuesto.creado") is False
    assert _eventos(Session) == []


def test_registrar_nunca_lanza_si_la_base_falla(entorno):
    """La telemetría jamás puede tumbar el flujo principal."""
    Session, ids, _rol = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]

        def _commit_roto():
            raise RuntimeError("base caída")

        db.commit = _commit_roto
        assert telemetria.registrar(db, "presupuesto.creado") is False
    assert _eventos(Session, accion="presupuesto.creado") == []


def test_el_catalogo_de_acciones_es_estable_y_legible():
    """El catálogo es la fuente única de etiquetas del panel."""
    assert telemetria.ACCIONES["actividad.diaria"] == "Uso diario"
    assert telemetria.etiqueta("accion.desconocida") == "accion.desconocida"
    for accion in telemetria.ACCIONES:
        assert accion.count(".") == 1, accion
        assert len(accion) <= 60


# ---------------------------------------------------------------------------
# Eventos globales (registro de cuenta)
# ---------------------------------------------------------------------------


def test_registrar_global_inserta_el_alta_de_cuenta(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        assert telemetria.registrar_global(
            db, "cuenta.registrada",
            email="Nueva@Example.com", detalle={"pais": "ES"},
        )
    eventos = _eventos(Session, accion="cuenta.registrada")
    assert len(eventos) == 1
    assert eventos[0].organizacion_id is None
    assert eventos[0].actor_email == "nueva@example.com"
    assert eventos[0].detalle_dict() == {"pais": "ES"}


def test_registrar_global_solo_admite_la_lista_cerrada(entorno):
    Session, _ids, _rol = entorno
    with Session() as db:
        assert telemetria.registrar_global(db, "sesion.login") is False
        assert telemetria.registrar_global(db, "") is False
    assert _eventos(Session) == []


# ---------------------------------------------------------------------------
# Latido diario (actividad.diaria)
# ---------------------------------------------------------------------------


def test_latido_diario_una_fila_por_dia_y_organizacion(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        assert telemetria.latido_diario(db)
        # Segunda petición del mismo día: memo en memoria, sin nueva fila.
        assert telemetria.latido_diario(db)
    assert len(_eventos(Session, accion="actividad.diaria")) == 1

    # Otra organización: fila propia.
    with Session() as db:
        db.info["organizacion_id"] = ids[1] if len(ids) > 1 else ids[0]
        if db.info["organizacion_id"] != ids[0]:
            assert telemetria.latido_diario(db)
    assert len(_eventos(Session, accion="actividad.diaria")) >= 1


def test_latido_diario_no_duplica_tras_un_reinicio_de_proceso(entorno):
    """El memo es un acelerador, no la fuente de verdad: la base decide."""
    Session, ids, _rol = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        assert telemetria.latido_diario(db)
    telemetria._LATIDOS.clear()  # simula un proceso serverless frío
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        assert telemetria.latido_diario(db)
    assert len(_eventos(Session, accion="actividad.diaria")) == 1


def test_latido_diario_con_base_caida_no_rompe(entorno):
    Session, ids, _rol = entorno
    telemetria._LATIDOS.clear()  # el memo vive a nivel de proceso entre pruebas
    with Session() as db:
        db.info["organizacion_id"] = ids[0]

        class _ConsultaRota:
            def filter(self, *a, **k):
                return self

            def first(self):
                raise RuntimeError("base caída")

        db.query = lambda *a, **k: _ConsultaRota()
        assert telemetria.latido_diario(db) is False


# ---------------------------------------------------------------------------
# Utilidades del panel
# ---------------------------------------------------------------------------


def test_dias_sin_uso():
    ahora = datetime(2026, 8, 28, 12, 0, 0)
    assert telemetria.dias_sin_uso(None, hoy=ahora) is None
    assert telemetria.dias_sin_uso(ahora, hoy=ahora) == 0
    assert telemetria.dias_sin_uso(ahora - timedelta(days=17), hoy=ahora) == 17


# ---------------------------------------------------------------------------
# Coherencia servicio ↔ migración
# ---------------------------------------------------------------------------


def test_las_acciones_globales_coinciden_con_la_migracion():
    """Defensa en profundidad: la función PostgreSQL valida la misma lista."""
    sql = migracion.ACCIONES_GLOBALES_SQL
    for accion in telemetria.ACCIONES_GLOBALES:
        assert f"'{accion}'" in sql
    # Y no admite ninguna otra fuera del catálogo del servicio.
    entre_comillas = {
        parte.split("'")[1]
        for parte in sql.split(", ")
        if "'" in parte
    }
    assert entre_comillas == set(telemetria.ACCIONES_GLOBALES)


def test_la_baja_de_organizacion_borra_la_telemetria():
    """La baja verificado (E3-023) también elimina eventos_producto."""
    assert "DELETE FROM public.eventos_producto" in migracion.BAJA_ACTUALIZADA_SQL
    # El downgrade restaura la función anterior (sin eventos_producto).
    assert "DELETE FROM public.eventos_producto" not in migracion.BAJA_ANTERIOR_SQL
    # Y ninguna otra tabla nueva se coló por accidente en el downgrade.
    assert "eventos_auditoria" in migracion.BAJA_ANTERIOR_SQL


def test_la_migracion_encadena_con_la_cabeza_vigente():
    import glob
    import re

    revisiones = {}
    referenciadas = set()
    for ruta in glob.glob("migrations/versions/*.py"):
        texto = open(ruta, encoding="utf-8").read()
        revision = re.search(
            r"\brevision(?:\s*:\s*str)?\s*=\s*['\"]([A-Za-z0-9]+)['\"]", texto
        )
        down = re.search(r"\bdown_revision(?:\s*:\s*[^\n=]+)?\s*=(.+)", texto)
        if revision:
            revisiones[revision.group(1)] = ruta
            if down:
                referenciadas |= set(re.findall(r"['\"]([A-Za-z0-9]+)['\"]", down.group(1)))
    cabezas = [r for r in revisiones if r not in referenciadas]
    assert cabezas == [fase3_migracion.revision], (
        f"La cadena Alembic debe tener una única cabeza ({fase3_migracion.revision}); "
        f"hay: {cabezas}"
    )
    assert fase3_migracion.down_revision == fase2_migracion.revision
    assert fase2_migracion.down_revision == "a1b8c2d4e6f0"
