"""Políticas RLS versionadas y contexto PostgreSQL por transacción."""
from types import SimpleNamespace

import pytest

import app.database as database_module
from app.database import Base, _aplicar_contexto_postgresql
from app.models import TenantMixin
from migrations.versions import c93e7a4d20f1_add_application_role_and_tenant_rls as migration
from migrations.versions import (
    d7f2a9c41e63_fix_invitation_select_policy_on_acceptance as invitation_migration,
)
from migrations.versions import (
    f9f24d062470_hacer_visible_alembic_version_al_rol_runtime as alembic_visibility_migration,
)


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
    assert database_module.EXPECTED_ALEMBIC_HEAD == alembic_visibility_migration.revision
    assert alembic_visibility_migration.down_revision == invitation_migration.revision
    assert invitation_migration.down_revision == migration.revision


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


def test_migracion_head_no_hace_nada_fuera_de_postgresql(monkeypatch):
    """La corrección de la política SELECT es solo para PostgreSQL."""
    statements = []
    sqlite_bind = SimpleNamespace(dialect=SimpleNamespace(name="sqlite"))
    monkeypatch.setattr(invitation_migration.op, "get_bind", lambda: sqlite_bind)
    monkeypatch.setattr(invitation_migration.op, "execute", lambda s: statements.append(s))
    invitation_migration.upgrade()
    invitation_migration.downgrade()
    assert statements == []


def test_migracion_head_sigue_mostrando_la_fila_aceptada_a_quien_la_acepto(monkeypatch):
    """Regresión estática del 500 en POST /invitaciones/{token}/aceptar.

    PostgreSQL exige que la fila nueva de un UPDATE siga pasando el USING de
    las políticas SELECT. La política del destinatario ya no puede exigir
    ``accepted_at IS NULL`` a secas: la fila aceptada sigue visible para el
    usuario que la aceptó, y el downgrade restaura la versión estricta.
    """
    statements = []
    monkeypatch.setattr(invitation_migration.op, "get_bind", lambda: _FakeBind())
    monkeypatch.setattr(invitation_migration.op, "execute", lambda s: statements.append(str(s)))
    invitation_migration.upgrade()
    sql = "\n".join(statements)

    assert "DROP POLICY IF EXISTS cotizat_invitation_select_recipient" in sql
    compacto = " ".join(sql.split())
    assert (
        "CREATE POLICY cotizat_invitation_select_recipient"
        " ON public.invitaciones_organizacion" in compacto
    )
    assert "FOR SELECT TO cotizat_app" in sql
    # La fila pendiente sigue siendo visible…
    assert "accepted_at IS NULL" in sql
    # …y la aceptada también, solo para quien la aceptó.
    assert "aceptada_por_usuario_id = cotizat_security.current_user_id()" in sql
    # El destinatario sigue sin ver invitaciones revocadas o ajenas.
    assert "email = cotizat_security.current_user_email()" in sql
    assert "revoked_at IS NULL" in sql
    assert "cotizat_security.current_user_is_verified()" in sql

    downgrade_statements = []
    monkeypatch.setattr(
        invitation_migration.op, "execute", lambda s: downgrade_statements.append(str(s))
    )
    invitation_migration.downgrade()
    revertido = "\n".join(downgrade_statements)
    # El rollback restaura la visibilidad estricta previa (sin la rama OR).
    assert "aceptada_por_usuario_id = cotizat_security.current_user_id()" not in revertido
    assert "accepted_at IS NULL" in revertido


# ---------------------------------------------------------------------------
# Regresión: visibilidad de public.alembic_version para el rol runtime
# ---------------------------------------------------------------------------
# /readyz reportaba «alembic: inesperado:sin-version»: el administrador ve la
# fila pero cotizat_runtime (miembro de cotizat_app) obtenía cero filas sin
# error. Con GRANT presente eso solo puede pasar si RLS está activo sobre la
# tabla sin política que autorice a cotizat_app. La migración
# f9f24d062470 apaga RLS sobre alembic_version, elimina políticas residuales
# y garantiza el GRANT SELECT.

def test_migracion_alembic_version_apaga_rls_y_concede_select(monkeypatch):
    statements = []
    monkeypatch.setattr(alembic_visibility_migration.op, "get_bind", lambda: _FakeBind())
    monkeypatch.setattr(
        alembic_visibility_migration.op,
        "execute",
        lambda s: statements.append(str(s)),
    )
    alembic_visibility_migration.upgrade()
    sql = "\n".join(statements)

    assert "ALTER TABLE public.alembic_version DISABLE ROW LEVEL SECURITY" in sql
    assert "ALTER TABLE public.alembic_version NO FORCE ROW LEVEL SECURITY" in sql
    # Elimina cualquier política residual que un bundle manual haya dejado.
    assert "pg_catalog.pg_policies" in sql
    assert "DROP POLICY IF EXISTS %I ON public.alembic_version" in sql
    assert "GRANT SELECT ON TABLE public.alembic_version TO cotizat_app" in sql

    # El downgrade revierte al estado previo (el que producía el bug), de
    # forma que un downgrade+upgrade vuelve a dejar la tabla legible.
    downgrade_statements = []
    monkeypatch.setattr(
        alembic_visibility_migration.op,
        "execute",
        lambda s: downgrade_statements.append(str(s)),
    )
    alembic_visibility_migration.downgrade()
    revertido = "\n".join(downgrade_statements)
    assert "REVOKE SELECT ON TABLE public.alembic_version FROM cotizat_app" in revertido
    assert "ALTER TABLE public.alembic_version ENABLE ROW LEVEL SECURITY" in revertido


def test_migracion_alembic_version_no_hace_nada_fuera_de_postgresql(monkeypatch):
    statements = []
    sqlite_bind = SimpleNamespace(dialect=SimpleNamespace(name="sqlite"))
    monkeypatch.setattr(
        alembic_visibility_migration.op, "get_bind", lambda: sqlite_bind
    )
    monkeypatch.setattr(
        alembic_visibility_migration.op,
        "execute",
        lambda s: statements.append(s),
    )
    alembic_visibility_migration.upgrade()
    alembic_visibility_migration.downgrade()
    assert statements == []


# ---------------------------------------------------------------------------
# Regresión: bootstrap de la primera organización bajo RLS
# ---------------------------------------------------------------------------
# Vercel falló con ``psycopg.errors.InsufficientPrivilege: new row violates
# row-level security policy for table organizaciones`` en
# ``INSERT ... RETURNING organizaciones.id``. El ``WITH CHECK`` de
# ``cotizat_org_insert`` se cumplía; lo que fallaba era el ``RETURNING``, que
# evalúa ``cotizat_org_select`` sobre la fila recién insertada cuando todavía
# no existe la membresía que esa política exige.

def test_insert_de_organizacion_con_id_explicito_no_emite_returning():
    """El id preasignado es lo que elimina el RETURNING que RLS rechazaba."""
    from sqlalchemy.dialects import postgresql

    from app.models import Organizacion

    tabla = Organizacion.__table__
    dialecto = postgresql.dialect()

    sin_id = str(
        tabla.insert().values(nombre="Empresa", slug="empresa").compile(dialect=dialecto)
    )
    con_id = str(
        tabla.insert()
        .values(id=42, nombre="Empresa", slug="empresa")
        .compile(dialect=dialecto)
    )

    # Comportamiento por defecto que provocaba el fallo en staging.
    assert "RETURNING organizaciones.id" in sin_id
    # Con la clave primaria explícita PostgreSQL ya no necesita leer la fila.
    assert "RETURNING" not in con_id
    assert con_id.startswith("INSERT INTO organizaciones (id,")


def test_reservar_id_organizacion_usa_la_secuencia_sin_tocar_la_tabla():
    """``nextval`` no pasa por ninguna política de fila."""
    from app.models import reservar_id_organizacion

    ejecutadas = []

    class _Resultado:
        def scalar_one(self):
            return 77

    class _FakeDb:
        def get_bind(self):
            return _FakeBind()

        def execute(self, statement, *_args, **_kwargs):
            ejecutadas.append(str(statement))
            return _Resultado()

    assert reservar_id_organizacion(_FakeDb()) == 77
    assert len(ejecutadas) == 1
    sql = ejecutadas[0]
    assert "nextval" in sql
    assert "organizaciones" in sql and "id" in sql
    # La reserva jamás debe leer la tabla protegida por RLS.
    assert "FROM public.organizaciones" not in sql
    assert "SELECT" in sql.upper() and "INSERT" not in sql.upper()


def test_reservar_id_organizacion_no_aplica_a_sqlite():
    """SQLite local no tiene RLS: conserva el autoincremento del motor."""
    from app.models import reservar_id_organizacion

    class _SqliteDb:
        def get_bind(self):
            return SimpleNamespace(dialect=SimpleNamespace(name="sqlite"))

        def execute(self, *_args, **_kwargs):  # pragma: no cover - no debe usarse
            raise AssertionError("SQLite no debe reservar ids desde una secuencia")

    assert reservar_id_organizacion(_SqliteDb()) is None


def test_crear_organizacion_con_propietario_deja_membresia_en_la_misma_transaccion():
    """El alta es atómica: sin la membresía, la organización sería invisible."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.models import (
        Membresia,
        Organizacion,
        Usuario,
        crear_organizacion_con_propietario,
    )

    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as db:
        usuario = Usuario(email="propietaria@example.com", nombre="Propietaria")
        db.add(usuario)
        db.flush()

        organizacion = crear_organizacion_con_propietario(
            db, nombre="Empresa Uno", slug="empresa-uno-abc", usuario_id=usuario.id
        )
        db.commit()

        assert organizacion.id is not None
        guardada = db.get(Organizacion, organizacion.id)
        assert guardada.creada_por_usuario_id == usuario.id
        assert guardada.activa is True

        membresia = db.query(Membresia).filter_by(
            organizacion_id=organizacion.id
        ).one()
        # ``cotizat_security.can_create_owner_membership`` solo autoriza esta
        # combinación exacta: el creador, como propietario, y sin membresías
        # previas en la organización.
        assert (membresia.usuario_id, membresia.rol, membresia.activa) == (
            usuario.id,
            "propietario",
            True,
        )


def test_endpoint_de_alta_usa_el_bootstrap_sin_returning():
    """El endpoint no debe reintroducir el ``Organizacion(...)`` directo."""
    import inspect

    import app.main as main

    fuente = inspect.getsource(main.crear_organizacion_web)
    assert "crear_organizacion_con_propietario(" in fuente
    assert "db.add(organizacion)" not in fuente
