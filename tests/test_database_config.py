"""Configuración de persistencia portable para navegador y legado local."""
from pathlib import Path
import os
import subprocess
import sys

from app.db_config import resolver_database_settings
from app.database import EXPECTED_ALEMBIC_HEAD


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
assert 'creada_por_usuario_id' in {
    column['name'] for column in inspector.get_columns('organizaciones')
}
with engine.connect() as connection:
    assert connection.execute(text('SELECT version_num FROM alembic_version')).scalar_one() == __EXPECTED_ALEMBIC_HEAD__
""".replace("__EXPECTED_ALEMBIC_HEAD__", repr(EXPECTED_ALEMBIC_HEAD))
    comprobacion = subprocess.run(
        [sys.executable, "-c", script],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        text=True,
        capture_output=True,
    )
    assert comprobacion.returncode == 0, comprobacion.stderr


def test_normalizar_url_autoajusta_pooler_supabase_a_puerto_transaccion(monkeypatch, tmp_path):
    # Caso 1: Supabase pooler en puerto 5432 (Session mode) -> se conmuta a 6543 (Transaction mode)
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://cotizat_runtime.abc:secret@aws-0-ca-central-1.pooler.supabase.com:5432/postgres?sslmode=require",
    )
    settings = resolver_database_settings(tmp_path, "local.db")
    assert settings.url == (
        "postgresql+psycopg://cotizat_runtime.abc:secret@aws-0-ca-central-1.pooler.supabase.com:6543/postgres?sslmode=require"
    )

    # Caso 2: Supabase pooler sin puerto explícito -> se añade puerto 6543
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgres://cotizat_runtime.abc:secret@aws-0-ca-central-1.pooler.supabase.com/postgres?sslmode=require",
    )
    settings2 = resolver_database_settings(tmp_path, "local.db")
    assert settings2.url == (
        "postgresql+psycopg://cotizat_runtime.abc:secret@aws-0-ca-central-1.pooler.supabase.com:6543/postgres?sslmode=require"
    )

    # Caso 3: Supabase pooler ya en puerto 6543 -> se conserva 6543
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://cotizat_runtime.abc:secret@aws-0-ca-central-1.pooler.supabase.com:6543/postgres?sslmode=require",
    )
    settings3 = resolver_database_settings(tmp_path, "local.db")
    assert settings3.url == (
        "postgresql+psycopg://cotizat_runtime.abc:secret@aws-0-ca-central-1.pooler.supabase.com:6543/postgres?sslmode=require"
    )

    # Caso 4: Conexión directa a PostgreSQL regular (no pooler) en 5432 -> se conserva 5432
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://usuario:secret@db.example.com:5432/cotizat",
    )
    settings4 = resolver_database_settings(tmp_path, "local.db")
    assert settings4.url == "postgresql+psycopg://usuario:secret@db.example.com:5432/cotizat"


def test_verificar_head_alembic_postgresql_eleva_runtime_error_si_tabla_vacia_o_version_diferente(monkeypatch):
    import pytest
    from app.database import _verificar_head_alembic_postgresql, EXPECTED_ALEMBIC_HEAD

    class _FakeResult:
        def __init__(self, value):
            self._value = value

        def scalar_one_or_none(self):
            return self._value

    class _FakeConn:
        def __init__(self, value):
            self._value = value

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def execute(self, stmt):
            return _FakeResult(self._value)

    class _FakeEngine:
        def __init__(self, value):
            self._value = value

        def connect(self):
            return _FakeConn(self._value)

    # Caso 1: tabla vacía (scalar_one_or_none devuelve None)
    monkeypatch.setattr("app.database.engine", _FakeEngine(None))
    with pytest.raises(RuntimeError) as exc_info:
        _verificar_head_alembic_postgresql()
    assert "encontrado: None" in str(exc_info.value)

    # Caso 2: versión diferente
    monkeypatch.setattr("app.database.engine", _FakeEngine("old_version"))
    with pytest.raises(RuntimeError) as exc_info2:
        _verificar_head_alembic_postgresql()
    assert "encontrado: 'old_version'" in str(exc_info2.value)

    # Caso 3: versión correcta
    monkeypatch.setattr("app.database.engine", _FakeEngine(EXPECTED_ALEMBIC_HEAD))
    _verificar_head_alembic_postgresql()  # No debe elevar excepción



RAIZ_REPO = Path(__file__).resolve().parents[1]


def test_expected_head_coincide_con_la_cabeza_real_de_alembic():
    """El head exigido por el runtime no puede quedarse atrás.

    Regresión del 500 del 23/08/2026 en el visor de planos: el PR que añadió
    ``planos_obra.altura_libre_m`` creó la revisión e4b8c2d6a190 pero dejó
    ``EXPECTED_ALEMBIC_HEAD`` en c0d1e2f3a4b5. /readyz siguió verde, el deploy
    se publicó sin migrar y producción reventó con
    ``UndefinedColumn: planos_obra.altura_libre_m`` en cada ``SELECT`` del
    visor. Comparando contra el grafo real de revisiones (no contra un head
    escrito a mano), cualquier migración nueva sin su actualización se
    detecta en CI antes del despliegue.
    """
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    config = Config(str(RAIZ_REPO / "alembic.ini"))
    config.set_main_option("script_location", str(RAIZ_REPO / "migrations"))
    cabezas = ScriptDirectory.from_config(config).get_heads()
    assert len(cabezas) == 1, f"Se esperaba una sola cabeza, hay: {cabezas}"
    assert cabezas[0] == EXPECTED_ALEMBIC_HEAD


def test_head_actual_tiene_sql_de_aplicacion_manual_en_supabase():
    """Cada cabeza nueva debe traer su ``docs/staging_upgrade_<rev>.sql``.

    En producción (Supabase, sin ``MIGRATION_DATABASE_URL`` en Vercel) las
    migraciones se aplican pegando ese archivo en el SQL Editor. El 500 del
    visor de planos ocurrió también porque e4b8c2d6a190 llegó sin él.
    """
    sql = RAIZ_REPO / "docs" / f"staging_upgrade_{EXPECTED_ALEMBIC_HEAD}.sql"
    assert sql.exists(), (
        f"Falta {sql.name}: crea el SQL de aplicación manual para el head "
        f"{EXPECTED_ALEMBIC_HEAD}."
    )
    contenido = sql.read_text(encoding="utf-8")
    assert EXPECTED_ALEMBIC_HEAD in contenido
    assert "UPDATE public.alembic_version" in contenido


def test_auto_reparacion_incluye_altura_libre_de_planos():
    """El arranque best-effort debe curar también el incidente de planos.

    Si otro despliegue llega sin migrar, el primer arranque con una URL con
    permisos DDL crea la columna y la app no vuelve al 500 permanente.
    """
    fuente = (RAIZ_REPO / "app" / "database.py").read_text(encoding="utf-8")
    assert (
        "ALTER TABLE planos_obra ADD COLUMN IF NOT EXISTS altura_libre_m FLOAT"
        in fuente
    )
    # Solo se avanza la marca si la columna existe de verdad (misma regla que
    # recorrido_inicial_oculto): marcar sin crear dejaría el 500 permanente.
    bloque = fuente.split('cur == "c0d1e2f3a4b5"', 1)[1]
    assert "if altura_creada:" in bloque
    assert "version_num = 'e4b8c2d6a190'" in bloque
