"""Pruebas de los endpoints de salud /healthz y /readyz."""
from fastapi.testclient import TestClient

from app import health as health_module
from app.health import HealthStatus, readiness
from app.main import app


def test_healthz_es_liveness_sin_db():
    with TestClient(app) as client:
        r = client.get("/healthz")
    assert r.status_code == 200
    body = r.json()
    assert body == {"ok": True, "checks": {"status": "alive"}, "errors": []}
    assert "no-store" in r.headers["cache-control"]


def test_readyz_devuelve_200_en_sqlite_local_sin_secretos(monkeypatch):
    # Auth/URL configuradas con valores de placeholder válidos; la base sigue
    # siendo SQLite local. El chequeo no debe abrir conexiones ni imprimir
    # credenciales.
    monkeypatch.setenv("SUPABASE_URL", "https://placeholder.supabase.co")
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "sb_publishable_placeholder")
    monkeypatch.setenv("COTIZAT_PUBLIC_URL", "https://cotizat.example.com")
    with TestClient(app) as client:
        r = client.get("/readyz")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert body["checks"]["database"] == "sqlite-local"
    assert body["checks"]["alembic"] == "no-aplica"
    assert body["checks"]["auth"] == "configurado"
    assert body["checks"]["storage"] == "local"
    # No debe filtrar la URL de conexión ni nada parecido a una contraseña.
    rendered = r.text.lower()
    assert "sqlite:///" not in rendered
    assert "password" not in rendered
    assert "sb_secret" not in rendered
    assert "sb_publishable" not in rendered
    assert "placeholder" not in rendered


def test_readyz_marca_503_sin_auth_configurada(monkeypatch):
    """Sin variables de Auth, readiness falla (no debe silenciar la falta)."""
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_PUBLISHABLE_KEY", raising=False)
    monkeypatch.delenv("COTIZAT_PUBLIC_URL", raising=False)
    with TestClient(app) as client:
        r = client.get("/readyz")
    assert r.status_code == 503
    body = r.json()
    assert body["ok"] is False
    assert any("Auth" in e for e in body["errors"])


def test_readyz_503_si_la_configuracion_esta_incompleta(monkeypatch):
    """Si Auth o Storage no están configurados, readiness falla sin secretos."""

    def fake_readiness():
        return HealthStatus(
            ok=False,
            checks={"auth": "no-configurado", "storage": "no-configurado"},
            errors=[
                "Auth: falta SUPABASE_URL.",
                "Storage: falta SUPABASE_SECRET_KEY.",
            ],
        )

    monkeypatch.setattr(health_module, "_readiness_override", fake_readiness)
    with TestClient(app) as client:
        r = client.get("/readyz")
    assert r.status_code == 503
    body = r.json()
    assert body["ok"] is False
    assert body["errors"]


def test_readiness_con_engine_postgresql_detecta_head_y_rol(monkeypatch):
    """Simula un motor PostgreSQL con head correcto y rol limitado."""
    from app.database import EXPECTED_ALEMBIC_HEAD

    class _Result:
        def __init__(self, value=None, mapping=None):
            self._value = value
            self._mapping = mapping or {}

        def scalar_one_or_none(self):
            return self._value

        def mappings(self):
            return self

        def one(self):
            return self._mapping

    class _Connection:
        def __init__(self, engine):
            self.engine = engine

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def execute(self, statement, parameters=None):
            sql = str(statement)
            if "alembic_version" in sql:
                return _Result(self.engine.version)
            if "pg_roles" in sql:
                return _Result(mapping={
                    "rolname": "cotizat_runtime",
                    "rolsuper": self.engine.rolsuper,
                    "rolbypassrls": self.engine.rolbypassrls,
                    "rolinherit": self.engine.rolinherit,
                    "app_member": self.engine.app_member,
                })
            raise AssertionError(f"SQL inesperado: {sql[:80]}")

    class _FakeEngine:
        def __init__(self, version, *, rolsuper=False, rolbypassrls=False,
                     rolinherit=True, app_member=True):
            self.version = version
            self.rolsuper = rolsuper
            self.rolbypassrls = rolbypassrls
            self.rolinherit = rolinherit
            self.app_member = app_member
            self.disposed = False

        def connect(self):
            return _Connection(self)

        def dispose(self):
            self.disposed = True

    # Forzamos la rama PostgreSQL de readiness y una configuración de
    # Auth/Storage/URL válida para aislar la verificación de DB/rol.
    monkeypatch.setattr(health_module, "DATABASE_IS_SQLITE", False)
    monkeypatch.setattr(health_module, "DATABASE_URL", "postgresql://x", raising=False)
    monkeypatch.setenv("SUPABASE_URL", "https://placeholder.supabase.co")
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "sb_publishable_placeholder")
    monkeypatch.setenv("SUPABASE_SECRET_KEY", "sb_secret_placeholder")
    monkeypatch.setenv("COTIZAT_STORAGE_BACKEND", "supabase")
    monkeypatch.setenv("COTIZAT_PUBLIC_URL", "https://cotizat.example.com")

    good = _FakeEngine(EXPECTED_ALEMBIC_HEAD)
    status = readiness(good)
    assert status.ok is True, status.errors
    assert status.checks["alembic"] == f"head:{EXPECTED_ALEMBIC_HEAD}"
    assert "cotizat_app=True" in status.checks["rol_runtime"]
    assert "superuser=False" in status.checks["rol_runtime"]
    assert "bypassrls=False" in status.checks["rol_runtime"]
    assert status.checks["storage"].startswith("supabase:")
    assert status.checks["auth"] == "configurado"
    assert "sb_secret" not in str(status.to_dict())
    assert "placeholder" not in str(status.to_dict())

    # Head desfasado -> error.
    old = _FakeEngine("9bca2ad1f6e4")
    status = readiness(old)
    assert status.ok is False
    assert any("Esquema" in e for e in status.errors)

    # Rol con BYPASSRLS -> error (aceptación #14).
    privileged = _FakeEngine(EXPECTED_ALEMBIC_HEAD, rolbypassrls=True)
    status = readiness(privileged)
    assert status.ok is False
    assert any("privilegiado" in e for e in status.errors)

    # Rol fuera de cotizat_app -> error.
    outsider = _FakeEngine(EXPECTED_ALEMBIC_HEAD, app_member=False)
    status = readiness(outsider)
    assert status.ok is False
    assert any("cotizat_app" in e for e in status.errors)
