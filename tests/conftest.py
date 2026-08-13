"""Aísla la base global de la aplicación durante toda la suite.

Algunos recorridos HTTP importan ``app.main`` y usan su ``SessionLocal`` real.
La variable debe definirse antes de que pytest importe esos módulos para que
ninguna prueba pueda migrar o modificar ``presupuestos.db`` del desarrollador.
"""
import os
import shutil
import tempfile
from pathlib import Path

import pytest

_TEST_DATA = Path(tempfile.mkdtemp(prefix="cotizat-tests-"))
os.environ["COTIZAT_DB"] = str(_TEST_DATA / "suite.db")
os.environ.pop("DATABASE_URL", None)


@pytest.fixture(scope="session", autouse=True)
def _base_http_aislada():
    """Prepara la demostración que usan las regresiones HTTP históricas."""
    from app.database import SessionLocal, init_db
    from app.models import Configuracion
    from app.services.onboarding import completar_onboarding

    init_db()
    with SessionLocal() as db:
        cfg = db.query(Configuracion).first()
        if not cfg.onboarding_completado:
            completar_onboarding(db, {"empresa_nombre": "Empresa de pruebas"}, "demo")
    yield


def pytest_sessionfinish(session, exitstatus):  # noqa: ARG001
    shutil.rmtree(_TEST_DATA, ignore_errors=True)
