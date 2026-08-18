"""Regresión: la sesión de BD no debe quedar envenenada tras un error silencioso.

Síntoma histórico
-----------------
Tras añadir el resumen de licencia visible en Configuración y en el menú
lateral, el handler de ``/inicio`` empezó a devolver 500 con
``psycopg.errors.InFailedSqlTransaction: current transaction is aborted,
commands ignored until end of transaction block``.

Causa
-----
``_resumen_licencia_para_request`` envuelve la consulta al resumen de
licencia en ``try/except Exception`` para que un fallo de permisos o de RLS no
tumbe la aplicación. Pero la sesión SQLAlchemy queda con la transacción
aborta-da: psycopg deja de aceptar comandos hasta un ``ROLLBACK``. La
siguiente consulta del handler (trivialmente válida) explota con
``InFailedSqlTransaction`` aunque la causa real ya estuviera silenciada.

Corrección
----------
Hacer ``db.rollback()`` dentro del ``except`` para devolver la sesión a un
estado utilizable antes de que el handler la reuse.

Cómo lo probamos
----------------
La diferencia clave entre SQLite y PostgreSQL es la gestión de transacciones
después de un error: SQLite abre una transacción implícita por sentencia, así
que un SELECT fallido no envenena la siguiente; psycopg mantiene una
transacción hasta el próximo ROLLBACK/COMMIT, así que un SELECT fallido
deja la transacción en estado ``aborted``.

Para no depender de un PostgreSQL real en CI, verificamos directamente que
el helper llama a ``db.rollback()`` cuando la consulta interna falla. Esa
llamada es lo que devuelve la sesión a un estado utilizable en psycopg
(equivalente al que SQLite ya tenía por defecto). Si alguien vuelve a
eliminar el ``rollback`` de dentro del ``except``, este test lo cazará.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def test_resumen_licencia_hace_rollback_si_la_consulta_falla(monkeypatch):
    """El helper debe liberar la transacción cuando el resumen falla."""
    from app.database import _resumen_licencia_para_request
    from app.services import licencias

    engine = create_engine("sqlite://")
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        llamadas_rollback = []

        def _rollback_grabado():
            llamadas_rollback.append("rollback")

        def _consulta_que_falla(*_args, **_kwargs):
            # Excepción de cualquier tipo: el helper la traga y debe
            # hacer rollback antes de devolver el resumen vacío.
            raise RuntimeError("falla simulada del resumen")

        monkeypatch.setattr(licencias, "resumen_licencia_cliente", _consulta_que_falla)
        monkeypatch.setattr(db, "rollback", _rollback_grabado)

        resumen = _resumen_licencia_para_request(db, 6)

        # La excepción se silencia y se devuelve el resumen por defecto.
        assert resumen == {
            "activo": False,
            "plan_label": "",
            "vence": None,
            "dias_restantes": 0,
            "metodo_cobro": "",
        }
        # Y, sobre todo, se pidió a la sesión que abandone la transacción
        # rota. Sin esto, psycopg mantendría ``InFailedSqlTransaction`` y
        # la siguiente consulta del handler reventaría con 500.
        assert llamadas_rollback == ["rollback"]
    finally:
        db.close()


def test_resumen_licencia_rollback_fallido_no_empeora_la_situacion(monkeypatch):
    """Si la propia ``rollback`` falla, devolvemos el resumen vacío igual.

    Cubre el caso patológico en que la conexión ya está cerrada (p. ej.
    timeout en el pool). La siguiente consulta del handler abrirá su propia
    transacción de todas formas.
    """
    from app.database import _resumen_licencia_para_request
    from app.services import licencias

    engine = create_engine("sqlite://")
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        def _consulta_que_falla(*_args, **_kwargs):
            raise RuntimeError("cualquier error del resumen")

        def _rollback_falla():
            raise RuntimeError("conexión ya cerrada")

        monkeypatch.setattr(licencias, "resumen_licencia_cliente", _consulta_que_falla)
        monkeypatch.setattr(db, "rollback", _rollback_falla)

        # La excepción del rollback no debe propagarse: el helper la
        # contiene y devuelve igualmente el resumen por defecto.
        resumen = _resumen_licencia_para_request(db, 1)
        assert resumen["activo"] is False
    finally:
        db.close()
