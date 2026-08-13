"""Políticas RLS versionadas y contexto PostgreSQL por transacción."""
from types import SimpleNamespace

import pytest

import app.database as database_module
from app.database import Base, _aplicar_contexto_postgresql
from app.models import TenantMixin
from migrations.versions import c93e7a4d20f1_add_application_role_and_tenant_rls as migration


class _FakeConnection:
    def __init__(self, dialect="postgresql"):
        self.dialect = SimpleNamespace(name=dialect)
        self.calls = []

    def execute(self, statement, parameters):
        self.calls.append((str(statement), parameters))


class _FakeBind:
    dialect = SimpleNamespace(name="postgresql")


class _FakeBatch:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def add_column(self, *_args, **_kwargs):
        pass

    def create_foreign_key(self, *_args, **_kwargs):
        pass

    def create_index(self, *_args, **_kwargs):
        pass


def test_contexto_postgresql_usa_parametros_y_limpia_valores_ausentes():
    connection = _FakeConnection()
    auth_id = "0691d7f2-ae24-4b7f-9e45-87ad16fdc94c"
    _aplicar_contexto_postgresql(connection, {
        "auth_user_id": auth_id,
        "auth_email": "Persona@Example.com",
        "organizacion_id": 27,
    })

    assert len(connection.calls) == 1
    sql, parameters = connection.calls[0]
    assert auth_id not in sql
    assert "persona@example.com" not in sql
    assert parameters == {
        "auth_user_id": auth_id,
        "auth_email": "persona@example.com",
        "organization_id": "27",
    }
    assert "set_config('cotizat.organization_id'" in sql

    sqlite = _FakeConnection("sqlite")
    _aplicar_contexto_postgresql(sqlite, {})
    assert sqlite.calls == []


def test_arranque_rechaza_rol_que_omite_rls(monkeypatch):
    class Result:
        def mappings(self):
            return self

        def one(self):
            return {
                "rolname": "postgres",
                "rolsuper": False,
                "rolbypassrls": True,
                "rolinherit": True,
                "app_member": True,
            }

    class Connection:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def execute(self, _statement):
            return Result()

    class Engine:
        def connect(self):
            return Connection()

    monkeypatch.setattr(database_module, "DATABASE_IS_SQLITE", False)
    monkeypatch.setattr(database_module, "engine", Engine())
    monkeypatch.setenv("COTIZAT_REQUIRE_RLS_ROLE", "true")
    with pytest.raises(RuntimeError, match="BYPASSRLS"):
        database_module._verificar_rol_aplicacion_postgresql()


def test_head_exigido_por_runtime_coincide_con_alembic():
    assert database_module.EXPECTED_ALEMBIC_HEAD == migration.revision


def test_migracion_rls_cubre_cada_modelo_tenant():
    modelos_tenant = {
        mapper.local_table.name
        for mapper in Base.registry.mappers
        if issubclass(mapper.class_, TenantMixin)
    }
    assert modelos_tenant == set(migration.TENANT_TABLES) | {
        migration.INVITATION_TABLE
    }


def test_migracion_crea_rol_sin_login_password_ni_bypass(monkeypatch):
    statements = []
    monkeypatch.setattr(migration.op, "get_bind", lambda: _FakeBind())
    monkeypatch.setattr(migration.op, "batch_alter_table", lambda *_a, **_k: _FakeBatch())
    monkeypatch.setattr(migration.op, "execute", lambda statement: statements.append(str(statement)))

    migration.upgrade()
    sql = "\n".join(statements)
    upper = sql.upper()

    assert "CREATE ROLE COTIZAT_APP NOLOGIN" in upper
    assert "NOBYPASSRLS" in upper
    assert "PASSWORD" not in upper
    assert "GRANT USAGE ON SCHEMA PUBLIC, COTIZAT_SECURITY TO COTIZAT_APP" in upper
    assert "GRANT SELECT ON TABLE PUBLIC.ALEMBIC_VERSION TO COTIZAT_APP" in upper
    assert "FORCE ROW LEVEL SECURITY" in upper
    assert "COTIZAT.AUTH_USER_ID" in upper
    assert "COTIZAT.ORGANIZATION_ID" in upper

    for table in migration.TENANT_TABLES:
        assert f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY" in sql
        assert f"CREATE POLICY cotizat_tenant_select ON public.{table}" in sql
        assert f"CREATE POLICY cotizat_tenant_insert ON public.{table}" in sql
        assert f"CREATE POLICY cotizat_tenant_update ON public.{table}" in sql
        assert f"CREATE POLICY cotizat_tenant_delete ON public.{table}" in sql

    assert "CREATE POLICY cotizat_user_insert ON public.usuarios" in sql
    assert "CREATE POLICY cotizat_membership_insert ON public.membresias" in sql
    assert "owned.creada_por_usuario_id" in sql
    assert "cotizat_security.has_pending_invitation" in sql
    assert "invited_user.email_verificado_at IS NOT NULL" in sql
    assert "cotizat_security.current_user_is_verified()" in sql
    assert "CREATE POLICY cotizat_invitation_update_recipient" in sql


def test_migracion_rls_no_hace_nada_fuera_de_postgresql(monkeypatch):
    statements = []
    sqlite_bind = SimpleNamespace(dialect=SimpleNamespace(name="sqlite"))
    monkeypatch.setattr(migration.op, "get_bind", lambda: sqlite_bind)
    monkeypatch.setattr(migration.op, "batch_alter_table", lambda *_a, **_k: _FakeBatch())
    monkeypatch.setattr(migration.op, "execute", lambda statement: statements.append(statement))
    migration.upgrade()
    assert statements == []
