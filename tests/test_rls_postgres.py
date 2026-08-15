"""Regresión end-to-end del bootstrap de organizaciones contra RLS real.

Estas pruebas son las únicas que habrían detectado el fallo de staging
(``psycopg.errors.InsufficientPrivilege: new row violates row-level security
policy for table organizaciones``): reproducen el ``INSERT ... RETURNING`` con
un rol sin ``BYPASSRLS`` y con las políticas realmente aplicadas por Alembic.

Se omiten salvo que exista un PostgreSQL de pruebas. Para ejecutarlas:

    COTIZAT_TEST_ADMIN_DATABASE_URL=postgresql+psycopg://postgres@/postgres \\
        pytest tests/test_rls_postgres.py

La URL debe apuntar a un rol administrador: la prueba crea una base desechable,
aplica las migraciones y crea el rol de runtime limitado.
"""
from __future__ import annotations

import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

sqlalchemy = pytest.importorskip("sqlalchemy")
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
ADMIN_URL = os.environ.get("COTIZAT_TEST_ADMIN_DATABASE_URL", "").strip()

pytestmark = pytest.mark.skipif(
    not ADMIN_URL,
    reason="Define COTIZAT_TEST_ADMIN_DATABASE_URL para ejecutar RLS real.",
)

AUTH_ID = "11111111-1111-4111-8111-111111111111"
EMAIL = "persona@example.com"
RUNTIME_PASSWORD = "pruebas-rls-local"


@pytest.fixture(scope="module")
def entorno_postgres():
    """Base desechable + migraciones + rol runtime sin BYPASSRLS."""
    nombre = f"cotizat_rls_{uuid.uuid4().hex[:10]}"
    admin = create_engine(ADMIN_URL, isolation_level="AUTOCOMMIT")
    with admin.connect() as conexion:
        conexion.execute(text(f'CREATE DATABASE "{nombre}"'))

    # ``make_url`` conserva host, puerto y query (p. ej. ``?host=/tmp/...``)
    # sin romper la URL al cambiar solo la base o el usuario.
    url_base = str(make_url(ADMIN_URL).set(database=nombre))

    entorno = dict(os.environ)
    entorno["MIGRATION_DATABASE_URL"] = url_base
    entorno["DATABASE_URL"] = url_base
    resultado = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=REPO,
        env=entorno,
        capture_output=True,
        text=True,
    )
    assert resultado.returncode == 0, resultado.stderr

    motor_admin = create_engine(url_base, isolation_level="AUTOCOMMIT")
    with motor_admin.connect() as conexion:
        conexion.execute(text("""
            DO $$ BEGIN
              IF NOT EXISTS (
                SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'cotizat_runtime'
              ) THEN
                CREATE ROLE cotizat_runtime LOGIN INHERIT NOSUPERUSER
                  NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
              END IF;
            END $$;
        """))
        conexion.execute(text("GRANT cotizat_app TO cotizat_runtime"))
        conexion.execute(
            text(f"ALTER ROLE cotizat_runtime PASSWORD '{RUNTIME_PASSWORD}'")
        )
        # Identidad ya activa, vinculada y verificada, como en staging.
        conexion.execute(
            text("""
                INSERT INTO usuarios (
                  auth_user_id, email, nombre, activo, email_verificado_at,
                  created_at, updated_at
                )
                VALUES (:auth, :email, 'Persona', TRUE, now(), now(), now())
                ON CONFLICT (email) DO NOTHING
            """),
            {"auth": AUTH_ID, "email": EMAIL},
        )
        usuario_id = conexion.execute(
            text("SELECT id FROM usuarios WHERE email = :email"), {"email": EMAIL}
        ).scalar_one()

    url_runtime = str(
        make_url(url_base).set(
            username="cotizat_runtime", password=RUNTIME_PASSWORD
        )
    )

    yield {
        "runtime_url": url_runtime,
        "usuario_id": usuario_id,
        "admin_url": url_base,
    }

    motor_admin.dispose()
    with admin.connect() as conexion:
        conexion.execute(
            text(f'DROP DATABASE IF EXISTS "{nombre}" WITH (FORCE)')
        )


def _aplicar_contexto(conexion, organizacion_id: str = "") -> None:
    conexion.execute(
        text("""
            SELECT set_config('cotizat.auth_user_id', :auth, true),
                   set_config('cotizat.auth_email', :email, true),
                   set_config('cotizat.organization_id', :org, true)
        """),
        {"auth": AUTH_ID, "email": EMAIL, "org": str(organizacion_id)},
    )


def test_alembic_version_es_legible_por_runtime_y_no_tiene_rls(entorno_postgres):
    """La guardia de arranque funciona con el login real y limitado."""
    from app.database import EXPECTED_ALEMBIC_HEAD

    motor = create_engine(entorno_postgres["runtime_url"])
    with motor.connect() as conexion:
        fila = conexion.execute(text("""
            SELECT c.relrowsecurity, c.relforcerowsecurity,
                   has_table_privilege(
                     current_user, 'public.alembic_version', 'SELECT'
                   ) AS puede_leer,
                   (
                     SELECT version_num
                     FROM public.alembic_version
                   ) AS version_num
            FROM pg_catalog.pg_class AS c
            JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relname = 'alembic_version'
        """)).one()

    assert fila.relrowsecurity is False
    assert fila.relforcerowsecurity is False
    assert fila.puede_leer is True
    assert fila.version_num == EXPECTED_ALEMBIC_HEAD
    motor.dispose()


def test_rls_sigue_rechazando_el_insert_con_returning(entorno_postgres):
    """Documenta la causa raíz: RLS no se relajó, se dejó de usar RETURNING.

    Si algún día esta prueba empieza a fallar significa que alguien debilitó
    ``cotizat_org_select``, que es justo lo que no se debía hacer.
    """
    from psycopg import errors

    motor = create_engine(entorno_postgres["runtime_url"])
    usuario_id = entorno_postgres["usuario_id"]
    with motor.connect() as conexion, conexion.begin():
        _aplicar_contexto(conexion)
        with pytest.raises(sqlalchemy.exc.ProgrammingError) as excinfo:
            conexion.execute(
                text("""
                    INSERT INTO organizaciones (
                      nombre, slug, activa, creada_por_usuario_id,
                      created_at, updated_at
                    )
                    VALUES ('Empresa', :slug, TRUE, :usuario, now(), now())
                    RETURNING organizaciones.id
                """),
                {"slug": f"con-returning-{uuid.uuid4().hex[:8]}", "usuario": usuario_id},
            )
    assert isinstance(excinfo.value.orig, errors.InsufficientPrivilege)
    assert "row-level security policy" in str(excinfo.value.orig)
    motor.dispose()


def test_bootstrap_crea_la_primera_organizacion_bajo_rls(entorno_postgres):
    """El camino corregido completa el alta con el rol limitado real."""
    import app.database as database_module
    from app.models import Configuracion, Membresia, crear_organizacion_con_propietario

    motor = create_engine(entorno_postgres["runtime_url"])
    usuario_id = entorno_postgres["usuario_id"]
    Sesion = sessionmaker(bind=motor)
    slug = f"empresa-uno-{uuid.uuid4().hex[:8]}"

    with Sesion() as db:
        db.info.update({"auth_user_id": AUTH_ID, "auth_email": EMAIL})
        db.execute(text("SELECT 1"))  # abre la transacción y aplica el contexto

        organizacion = crear_organizacion_con_propietario(
            db, nombre="Empresa Uno", slug=slug, usuario_id=usuario_id
        )
        assert organizacion.id is not None

        # Con la membresía ya creada, la organización pasa a ser visible.
        database_module.establecer_contexto_organizacion(db, organizacion.id)
        db.add(Configuracion(organizacion_id=organizacion.id))
        db.commit()

        membresia = db.query(Membresia).filter_by(
            organizacion_id=organizacion.id
        ).one()
        assert membresia.rol == "propietario"
        assert db.query(Configuracion).filter_by(
            organizacion_id=organizacion.id
        ).count() == 1

    motor.dispose()


def test_invitado_acepta_invitacion_bajo_rls(entorno_postgres):
    """Flujo completo de invitación con el rol limitado real.

    Regresión del 500 de producción en ``POST /invitaciones/{token}/aceptar``:
    PostgreSQL evalúa el ``USING`` de las políticas SELECT como ``WITH CHECK``
    sobre la fila nueva del UPDATE que marca la invitación como aceptada. La
    política del destinatario exigía ``accepted_at IS NULL`` —justo lo que el
    UPDATE elimina— y la reclamación moría con ``InsufficientPrivilege: new
    row violates row-level security policy``.
    """
    import app.database as database_module
    from app.models import Membresia, Usuario, crear_organizacion_con_propietario
    from app.services.invitations import (
        GestionEquipoError,
        aceptar_invitacion,
        crear_invitacion,
    )

    dueña_auth = "33333333-3333-4333-8333-333333333333"
    dueña_email = "duena@example.com"
    admin = create_engine(
        entorno_postgres["admin_url"], isolation_level="AUTOCOMMIT"
    )
    with admin.connect() as conexion:
        conexion.execute(text("""
            INSERT INTO usuarios (
              auth_user_id, email, nombre, activo, email_verificado_at,
              created_at, updated_at
            )
            VALUES (:auth, :email, 'Dueña', TRUE, now(), now(), now())
            ON CONFLICT (email) DO NOTHING
        """), {"auth": dueña_auth, "email": dueña_email})
        dueña_id = conexion.execute(
            text("SELECT id FROM usuarios WHERE email = :email"),
            {"email": dueña_email},
        ).scalar_one()
    admin.dispose()

    motor = create_engine(entorno_postgres["runtime_url"])
    Sesion = sessionmaker(bind=motor)

    def contexto(db, auth_user_id, email, organizacion_id=None):
        db.info.update({"auth_user_id": auth_user_id, "auth_email": email})
        db.execute(text("SELECT 1"))  # abre la transacción e instala el contexto
        if organizacion_id is not None:
            database_module.establecer_contexto_organizacion(db, organizacion_id)

    # 1) La dueña crea su organización (flujo ya verificado).
    with Sesion() as db:
        contexto(db, dueña_auth, dueña_email)
        organizacion = crear_organizacion_con_propietario(
            db,
            nombre="Constructora RLS",
            slug=f"constructora-rls-{uuid.uuid4().hex[:8]}",
            usuario_id=dueña_id,
        )
        database_module.establecer_contexto_organizacion(db, organizacion.id)
        db.commit()
        organizacion_id = organizacion.id

    # 2) La dueña invita al usuario verificado del fixture.
    with Sesion() as db:
        contexto(db, dueña_auth, dueña_email, organizacion_id)
        invitacion, token = crear_invitacion(
            db,
            organizacion_id=organizacion_id,
            actor_usuario_id=dueña_id,
            email=EMAIL,
            rol="miembro",
        )
        assert invitacion.id is not None
        db.commit()

    # 3) El invitado acepta SIN organización activa (el POST que fallaba).
    invitado_id = entorno_postgres["usuario_id"]
    with Sesion() as db:
        contexto(db, AUTH_ID, EMAIL)
        usuario = db.get(Usuario, invitado_id)
        assert usuario is not None
        membresia = aceptar_invitacion(
            db, token=token, usuario=usuario, email_verificado=True
        )
        assert membresia.organizacion_id == organizacion_id
        assert membresia.rol == "miembro"
        db.commit()

    # 4) El token es de un solo uso: reaceptar se rechaza sin 500.
    with Sesion() as db:
        contexto(db, AUTH_ID, EMAIL)
        usuario = db.get(Usuario, invitado_id)
        with pytest.raises(GestionEquipoError, match="no es válida"):
            aceptar_invitacion(
                db, token=token, usuario=usuario, email_verificado=True
            )
        db.rollback()

    # 5) La membresía quedó activa y visible para el propio invitado.
    with Sesion() as db:
        contexto(db, AUTH_ID, EMAIL)
        membresias = (
            db.query(Membresia)
            .filter(
                Membresia.usuario_id == invitado_id,
                Membresia.organizacion_id == organizacion_id,
            )
            .all()
        )
        assert [(m.rol, m.activa) for m in membresias] == [("miembro", True)]

    # 6) Una invitación dirigida a otro email sigue siendo invisible para el
    #    destinatario del fixture (la corrección no amplía esa frontera).
    from app.models import InvitacionOrganizacion
    from app.services.invitations import actualizar_membresia, revocar_invitacion

    with Sesion() as db:
        contexto(db, dueña_auth, dueña_email, organizacion_id)
        _, token_ajena = crear_invitacion(
            db,
            organizacion_id=organizacion_id,
            actor_usuario_id=dueña_id,
            email="otra.persona@example.com",
            rol="miembro",
        )
        db.commit()

    with Sesion() as db:
        contexto(db, AUTH_ID, EMAIL)
        visibles = (
            db.query(InvitacionOrganizacion)
            .filter(InvitacionOrganizacion.token_hash == _hash_de(token_ajena))
            .count()
        )
        assert visibles == 0

    # 7) Membresía desactivada + nueva invitación: se reactiva sin duplicar.
    with Sesion() as db:
        contexto(db, dueña_auth, dueña_email, organizacion_id)
        membresia_activa = (
            db.query(Membresia)
            .filter(
                Membresia.usuario_id == invitado_id,
                Membresia.organizacion_id == organizacion_id,
            )
            .with_for_update()
            .one()
        )
        actualizar_membresia(
            db,
            membresia=membresia_activa,
            organizacion_id=organizacion_id,
            actor_usuario_id=dueña_id,
            rol="miembro",
            activa=False,
        )
        db.commit()

    # 8) La primera de las nuevas invitaciones se revoca: debe ser invisible.
    #    La segunda se acepta y reactiva la membresía con el nuevo rol.
    with Sesion() as db:
        contexto(db, dueña_auth, dueña_email, organizacion_id)
        revocada, token_revocada = crear_invitacion(
            db,
            organizacion_id=organizacion_id,
            actor_usuario_id=dueña_id,
            email=EMAIL,
            rol="lectura",
        )
        revocar_invitacion(
            db,
            invitacion=revocada,
            organizacion_id=organizacion_id,
            actor_usuario_id=dueña_id,
        )
        _, token_reactivacion = crear_invitacion(
            db,
            organizacion_id=organizacion_id,
            actor_usuario_id=dueña_id,
            email=EMAIL,
            rol="lectura",
        )
        db.commit()

    with Sesion() as db:
        contexto(db, AUTH_ID, EMAIL)
        assert (
            db.query(InvitacionOrganizacion)
            .filter(InvitacionOrganizacion.token_hash == _hash_de(token_revocada))
            .count()
            == 0
        )

    with Sesion() as db:
        contexto(db, AUTH_ID, EMAIL)
        usuario = db.get(Usuario, invitado_id)
        reactivada = aceptar_invitacion(
            db, token=token_reactivacion, usuario=usuario, email_verificado=True
        )
        assert reactivada.activa is True
        assert reactivada.rol == "lectura"
        db.commit()

    with Sesion() as db:
        contexto(db, AUTH_ID, EMAIL)
        membresias = (
            db.query(Membresia)
            .filter(
                Membresia.usuario_id == invitado_id,
                Membresia.organizacion_id == organizacion_id,
            )
            .all()
        )
        assert [(m.rol, m.activa) for m in membresias] == [("lectura", True)]

    motor.dispose()


def _hash_de(token: str) -> str:
    """Mismo hash SHA-256 que guarda el servicio (los tokens no se persisten)."""
    import hashlib

    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def test_el_rol_de_runtime_no_puede_saltarse_rls(entorno_postgres):
    """Garantiza que la prueba anterior no pasó por privilegios de más."""
    motor = create_engine(entorno_postgres["runtime_url"])
    with motor.connect() as conexion:
        fila = conexion.execute(text("""
            SELECT rolsuper, rolbypassrls
            FROM pg_catalog.pg_roles WHERE rolname = current_user
        """)).one()
    assert fila.rolsuper is False
    assert fila.rolbypassrls is False
    motor.dispose()
