"""Políticas RLS versionadas y contexto PostgreSQL por transacción."""
from pathlib import Path
from types import SimpleNamespace

import pytest

import app.database as database_module
from app.database import Base, _aplicar_contexto_postgresql
from app.models import TenantMixin
from migrations.versions import c93e7a4d20f1_add_application_role_and_tenant_rls as migration
from migrations.versions import (
    a3d7e9c1b5f2_baja_organizacion_function as baja_migration,
    b7c4a9e2d31f_license_cutoff_and_operator_visibility as licenses_access_migration,
    c2f6e8a1d934_public_proposal_links as proposal_links_migration,
    d7f2a9c41e63_fix_invitation_select_policy_on_acceptance as invitation_migration,
    d6e2f9c4b8a1_catalog_visibility as catalog_visibility_migration,
    e1a4b7c9d2f0_harden_alembic_version_visibility as alembic_migration,
    e5f2a8d31b6c_add_plan_purchases as plan_purchases_migration,
    f9d4c2a7e5b3_organization_license_info as head_migration,
    a1b2c3d4e5f6_fix_license_info_type_mismatch as hotfix_migration,
    a3d9c1e75b28_prueba_gratuita_registro as prueba_migration,
    b6d9e4c2a8f1_consentimiento_terminos as consentimiento_migration,
    c7f1a3b9d425_compra_periodo_licencia as compra_periodo_migration,
    c8f1a2b3d4e5_add_etiqueta_fiscal_latam as etiqueta_migration,
    d2a7c9e4f1b3_audit_log_and_complete_baja as auditoria_migration,
    d4e2f6a8b0c1_license_info_chained_access as chained_migration,
    d9e2f3a4b5c6_add_tasa_cambio_latam as tasa_migration,
    f4c1d8e37a95_add_operator_licenses as licenses_migration,
    e7b3c1d5a204_market_prices_grants_and_rls as market_prices_migration,
    f8a1b2c3d4e5_catalog_taxonomy_v2 as taxonomy_migration,
)

RAIZ_REPO = Path(__file__).resolve().parent.parent


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
        "proposal_token_hash": "",
        # Sin marca explícita, la sesión NO es de operador: es el valor seguro
        # por omisión y lo que deja vacía la tabla `licencias` bajo RLS.
        "es_operador": "off",
    }
    assert "set_config('cotizat.organization_id'" in sql
    assert "set_config('cotizat.es_operador'" in sql
    assert "set_config('cotizat.proposal_token_hash'" in sql


def test_la_marca_de_operador_solo_se_activa_cuando_el_contexto_lo_declara():
    """`cotizat.es_operador` habilita las políticas RLS de `licencias`.

    Si se activara sola, cualquier sesión vería el registro de licencias de
    todos los clientes; por eso se comprueba en ambos sentidos.
    """
    operador = _FakeConnection()
    _aplicar_contexto_postgresql(operador, {
        "auth_user_id": "id-operador",
        "auth_email": "titular@example.com",
        "es_operador": True,
    })
    assert operador.calls[0][1]["es_operador"] == "on"

    cliente = _FakeConnection()
    _aplicar_contexto_postgresql(cliente, {
        "auth_user_id": "id-cliente",
        "auth_email": "cliente@example.com",
        "organizacion_id": 4,
    })
    assert cliente.calls[0][1]["es_operador"] == "off"

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
    """El head que el runtime exige debe ser el último de la cadena.

    Si divergen, `/readyz` responde 503 en producción: el código espera un
    esquema que la base no tiene todavía (o al revés).
    """
    from migrations.versions import c5d6e7f8a9b0_merge_currency_heads as merge_migration
    assert database_module.EXPECTED_ALEMBIC_HEAD == market_prices_migration.revision
    assert market_prices_migration.down_revision == merge_migration.revision
    assert tasa_migration.revision == "d9e2f3a4b5c6"
    assert tasa_migration.down_revision == etiqueta_migration.revision
    assert etiqueta_migration.down_revision == auditoria_migration.revision
    assert auditoria_migration.down_revision == consentimiento_migration.revision
    assert consentimiento_migration.down_revision == prueba_migration.revision
    assert prueba_migration.down_revision == compra_periodo_migration.revision
    assert compra_periodo_migration.down_revision == chained_migration.revision
    assert chained_migration.down_revision == hotfix_migration.revision
    assert hotfix_migration.down_revision == head_migration.revision
    assert head_migration.down_revision == plan_purchases_migration.revision
    assert plan_purchases_migration.down_revision == catalog_visibility_migration.revision
    assert catalog_visibility_migration.down_revision == taxonomy_migration.revision
    assert taxonomy_migration.down_revision == baja_migration.revision
    assert baja_migration.down_revision == proposal_links_migration.revision
    assert proposal_links_migration.down_revision == licenses_access_migration.revision
    assert licenses_access_migration.down_revision == licenses_migration.revision
    assert licenses_migration.down_revision == alembic_migration.revision
    assert alembic_migration.down_revision == invitation_migration.revision
    assert invitation_migration.down_revision == migration.revision


def test_migracion_licencia_suma_el_acceso_encadenado(monkeypatch):
    """El resumen del cliente debe llegar al final de la cadena, no a la
    primera licencia: 4 días + 1 mes → ~34 días, no 4."""
    statements = []
    monkeypatch.setattr(chained_migration.op, "get_bind", lambda: _FakeBind())
    monkeypatch.setattr(
        chained_migration.op, "execute", lambda s: statements.append(str(s))
    )
    chained_migration.upgrade()
    sql = "\n".join(statements)

    # Parte de la licencia que cubre hoy y avanza por las contiguas.
    assert "WITH RECURSIVE" in sql
    assert "l.inicio <= c.fin + 1" in sql
    assert "l.vence > c.fin" in sql
    assert "SELECT MAX(fin)" in sql
    # Sigue exigiendo la guardia del claim de sesión y el mínimo privilegio.
    assert "context_organization_id()" in sql
    assert "REVOKE ALL ON FUNCTION cotizat_security.organization_license_info" in sql
    assert "GRANT EXECUTE ON FUNCTION cotizat_security.organization_license_info" in sql
    assert "TO cotizat_app" in sql

    # El downgrade no restaura el resumen corto: es un no-op documentado.
    downgrade_statements = []
    monkeypatch.setattr(
        chained_migration.op, "execute", lambda s: downgrade_statements.append(str(s))
    )
    chained_migration.downgrade()
    assert downgrade_statements == []


def test_migracion_rls_cubre_cada_modelo_tenant():
    modelos_tenant = {
        mapper.local_table.name
        for mapper in Base.registry.mappers
        if issubclass(mapper.class_, TenantMixin)
    }
    assert modelos_tenant == set(migration.TENANT_TABLES) | {
        migration.INVITATION_TABLE,
        proposal_links_migration.TABLE,
        plan_purchases_migration.TABLE,
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


def test_migracion_invitaciones_no_hace_nada_fuera_de_postgresql(monkeypatch):
    """La corrección de la política SELECT es solo para PostgreSQL."""
    statements = []
    sqlite_bind = SimpleNamespace(dialect=SimpleNamespace(name="sqlite"))
    monkeypatch.setattr(invitation_migration.op, "get_bind", lambda: sqlite_bind)
    monkeypatch.setattr(invitation_migration.op, "execute", lambda s: statements.append(s))
    invitation_migration.upgrade()
    invitation_migration.downgrade()
    assert statements == []


def test_migracion_invitaciones_sigue_mostrando_la_fila_aceptada_a_quien_la_acepto(monkeypatch):
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


def test_migracion_alembic_version_desactiva_rls_y_concede_lectura(monkeypatch):
    """El runtime puede leer solo el metadato que necesita para readiness."""
    statements = []
    monkeypatch.setattr(alembic_migration.op, "get_bind", lambda: _FakeBind())
    monkeypatch.setattr(alembic_migration.op, "execute", lambda s: statements.append(str(s)))

    alembic_migration.upgrade()
    sql = "\n".join(statements)
    assert "ALTER TABLE public.alembic_version DISABLE ROW LEVEL SECURITY" in sql
    assert "GRANT SELECT ON TABLE public.alembic_version TO cotizat_app" in sql
    assert "INSERT" not in sql.upper()

    downgrade_statements = []
    monkeypatch.setattr(
        alembic_migration.op, "execute", lambda s: downgrade_statements.append(str(s))
    )
    alembic_migration.downgrade()
    revertido = "\n".join(downgrade_statements)
    assert "REVOKE SELECT ON TABLE public.alembic_version FROM cotizat_app" in revertido
    assert "ALTER TABLE public.alembic_version ENABLE ROW LEVEL SECURITY" in revertido


def test_migracion_alembic_version_no_hace_nada_fuera_de_postgresql(monkeypatch):
    statements = []
    sqlite_bind = SimpleNamespace(dialect=SimpleNamespace(name="sqlite"))
    monkeypatch.setattr(alembic_migration.op, "get_bind", lambda: sqlite_bind)
    monkeypatch.setattr(alembic_migration.op, "execute", lambda s: statements.append(s))
    alembic_migration.upgrade()
    alembic_migration.downgrade()
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


def test_la_cadena_de_migraciones_tiene_un_unico_head():
    """Un head duplicado deja `alembic upgrade head` sin poder ejecutarse.

    Se calcula el grafo real desde los archivos: cualquier revisión nueva que
    se cuelgue de un padre ya usado (rama accidental) rompe aquí y no en el
    despliegue.
    """
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    configuracion = Config(str(RAIZ_REPO / "alembic.ini"))
    configuracion.set_main_option("script_location", str(RAIZ_REPO / "migrations"))
    heads = ScriptDirectory.from_config(configuracion).get_heads()

    assert list(heads) == [database_module.EXPECTED_ALEMBIC_HEAD]


def test_toda_tabla_del_modelo_recibe_permisos_del_rol_de_aplicacion():
    """Ninguna tabla puede nacer sin GRANT para `cotizat_app`.

    Es la regresión del fallo de «Nuevo presupuesto»: `precios_recursos_mercado`
    e `historial_precios_recursos` se crearon sin permisos, la consulta moría
    con `permission denied`, la transacción quedaba abortada y la siguiente
    consulta de la página fallaba con `InFailedSqlTransaction`.
    """
    import re

    # Cada migración se lee resolviendo antes sus constantes de módulo
    # (`TABLE = "compras_plan"`), que es como se nombran las tablas en los
    # `GRANT` con f-string.
    concedidas = set(migration.ALL_APP_TABLES)  # revisión inicial, en bloque
    for ruta in sorted((RAIZ_REPO / "migrations" / "versions").glob("*.py")):
        texto = ruta.read_text(encoding="utf-8")
        for nombre, valor in re.findall(
            r'^([A-Z_]+)(?::\s*str)?\s*=\s*"([a-z0-9_]+)"$', texto, re.M
        ):
            texto = texto.replace("{" + nombre + "}", valor)
        for sentencia in re.findall(r"GRANT [^\n]*", texto):
            concedidas.update(re.findall(r"public\.([a-z0-9_]+)", sentencia))

    tablas_modelo = {mapper.local_table.name for mapper in Base.registry.mappers}
    sin_permisos = sorted(tablas_modelo - concedidas)

    assert not sin_permisos, (
        "Tablas sin GRANT para cotizat_app (añade la migración de permisos y "
        f"políticas RLS): {sin_permisos}"
    )


def test_migracion_precios_mercado_concede_permisos_y_aisla_por_organizacion(monkeypatch):
    """Referencia nacional compartida, precio de empresa privado."""
    statements = []
    monkeypatch.setattr(market_prices_migration.op, "get_bind", lambda: _FakeBind())
    monkeypatch.setattr(
        market_prices_migration.op, "execute", lambda s: statements.append(str(s))
    )
    market_prices_migration.upgrade()
    sql = "\n".join(statements)

    for tabla in ("precios_recursos_mercado", "historial_precios_recursos"):
        assert f"REVOKE ALL ON TABLE public.{tabla} FROM PUBLIC" in sql
        assert f"ALTER TABLE public.{tabla} ENABLE ROW LEVEL SECURITY" in sql
        assert f"ALTER TABLE public.{tabla} FORCE ROW LEVEL SECURITY" in sql
        assert f"pg_get_serial_sequence('public.{tabla}', 'id')" in sql

    assert (
        "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE "
        "public.precios_recursos_mercado TO cotizat_app" in sql
    )
    # La secuencia se concede por nombre resuelto: en Supabase la tabla se creó
    # con `GENERATED BY DEFAULT AS IDENTITY` y `<tabla>_id_seq` podría no existir.
    assert "GRANT USAGE, SELECT ON SEQUENCE %s" in sql
    # El histórico es bitácora: nunca se corrige ni se borra.
    assert (
        "GRANT SELECT, INSERT ON TABLE public.historial_precios_recursos "
        "TO cotizat_app" in sql
    )
    assert "UPDATE ON TABLE public.historial_precios_recursos" not in sql

    # Lectura: la referencia nacional (organizacion_id NULL) más la propia.
    assert "organizacion_id IS NULL" in sql
    assert "cotizat_security.tenant_access(organizacion_id, FALSE)" in sql
    # Escritura: solo el precio propio; lo nacional queda para el operador.
    assert "cotizat_security.tenant_access(organizacion_id, TRUE)" in sql
    assert "cotizat.es_operador" in sql
    for politica in (
        "cotizat_precio_mercado_select",
        "cotizat_precio_mercado_insert",
        "cotizat_precio_mercado_update",
        "cotizat_precio_mercado_delete",
        "cotizat_historial_precio_select",
        "cotizat_historial_precio_insert",
    ):
        assert f"CREATE POLICY {politica} " in sql


def test_migracion_precios_mercado_no_hace_nada_fuera_de_postgresql(monkeypatch):
    statements = []
    sqlite_bind = SimpleNamespace(dialect=SimpleNamespace(name="sqlite"))
    monkeypatch.setattr(market_prices_migration.op, "get_bind", lambda: sqlite_bind)
    monkeypatch.setattr(
        market_prices_migration.op, "execute", lambda s: statements.append(s)
    )
    market_prices_migration.upgrade()
    market_prices_migration.downgrade()
    assert statements == []
