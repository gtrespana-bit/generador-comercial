"""Configuración de persistencia portable para navegador y legado local."""
from pathlib import Path
import os
import subprocess
import sys

from app.db_config import resolver_database_settings


def test_database_url_postgresql_tiene_prioridad_y_usa_psycopg(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", "postgres://user:secret@db.example/cotizat")
    monkeypatch.setenv("COTIZAT_DB", str(tmp_path / "ignorada.db"))
    settings = resolver_database_settings(tmp_path, "local.db")
    assert settings.url == "postgresql+psycopg://user:secret@db.example/cotizat"
    assert settings.backend == "postgresql"
    assert settings.sqlite_path is None
    assert settings.source == "DATABASE_URL"


def test_archivo_sqlite_actual_sigue_soportado(monkeypatch, tmp_path):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("COTIZAT_DB", "empresa.db")
    monkeypatch.delenv("PRESUPUESTOS_DB", raising=False)
    settings = resolver_database_settings(tmp_path, "local.db")
    assert settings.backend == "sqlite"
    assert settings.sqlite_path == (tmp_path / "empresa.db").resolve()
    assert settings.source == "COTIZAT_DB"


def test_alembic_construye_esquema_browser_first_desde_cero(tmp_path):
    db_path = tmp_path / "web.db"
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{db_path}"
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
    resultado = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        text=True,
        capture_output=True,
    )
    assert resultado.returncode == 0, resultado.stderr

    script = """
from sqlalchemy import create_engine, inspect, text
import os
engine = create_engine(os.environ['DATABASE_URL'])
inspector = inspect(engine)
tables = set(inspector.get_table_names())
assert {'alembic_version', 'organizaciones', 'usuarios', 'membresias',
        'clientes', 'presupuestos', 'configuracion', 'archivos_almacenados',
        'invitaciones_organizacion'} <= tables
assert 'auth_user_id' in {column['name'] for column in inspector.get_columns('usuarios')}
with engine.connect() as connection:
    assert connection.execute(text('SELECT version_num FROM alembic_version')).scalar_one() == 'a84d2f6b91e0'
"""
    comprobacion = subprocess.run(
        [sys.executable, "-c", script],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        text=True,
        capture_output=True,
    )
    assert comprobacion.returncode == 0, comprobacion.stderr
