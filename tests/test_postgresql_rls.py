"""Contratos que solo existen en PostgreSQL: RLS, roles y funciones.

La suite general corre en SQLite, donde no hay RLS ni tipos booleanos
estrictos: tres incidentes de producción del 20/10/2026 fueron invisibles
para ella (el contador de ``/readyz`` con ``boolean = integer`` y los dos
muros del buzón de soporte). Esta batería cubre justamente ese hueco
(hoja de ruta 2026-10-20, fase 0.1) ejecutando los servicios reales como
el rol de producción (``cotizat_runtime``, miembro de `cotizat_app`, sin
bypass) contra un esquema creado por la cadena de migraciones real.

Se activa con ``COTIZAT_TEST_ADMIN_DATABASE_URL`` — la misma convención
que ``test_rls_postgres.py``, que el job de CI por fin ejecuta junto a
este —: la URL **administrativa** de un PostgreSQL desechable (el
servicio de CI o un pgserver local). Sin la variable, el módulo entero
se salta y la suite de SQLite no nota nada. La fixture crea una base
hija, corre ``alembic upgrade head`` desde cero —lo que de paso audita
que la cadena es reconstruible—, crea el login runtime como en el
aprovisionamiento y siembra dos organizaciones.
"""
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import pytest

ADMIN_URL = (os.environ.get("COTIZAT_TEST_ADMIN_DATABASE_URL") or "").strip()
if not ADMIN_URL:
    pytest.skip(
        "Sin COTIZAT_TEST_ADMIN_DATABASE_URL: batería PostgreSQL/RLS desactivada",
        allow_module_level=True,
    )

psycopg = pytest.importorskip("psycopg")

from sqlalchemy import create_engine, update  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

import app.database  # noqa: E402,F401  (registra el listener de claims RLS)
from app.models import (  # noqa: E402
    CompraPlan,
    Licencia,
    Membresia,
    MensajeSoporte,
    Organizacion,
    Usuario,
)

RAIZ = Path(__file__).resolve().parents[1]
_PASSWORD_RUNTIME = "insegura-solo-tests"

# El login runtime del aprovisionamiento (docs/APROVISIONAMIENTO_STAGING.md,
# Paso C), con contraseña solo para la base desechable de esta batería.
_SQL_RUNTIME = f"""
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'cotizat_runtime') THEN
    CREATE ROLE cotizat_runtime
      LOGIN INHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS
      PASSWORD '{_PASSWORD_RUNTIME}';
  END IF;
END
$$;
GRANT cotizat_app TO cotizat_runtime;
"""


def _para_psycopg(url: str) -> str:
    """psycopg a pelo no entiende el ``+driver`` de SQLAlchemy en el esquema.

    La batería hermana (``test_rls_postgres.py``) espera la URL en forma
    ``postgresql+psycopg://``; los ``psycopg.connect`` de la fixture (crear
    y borrar la base hija, crear el rol) necesitan la forma pelada.
    """
    return re.sub(r"^postgresql\+\w+://", "postgresql://", url)


def _url_con(url: str, *, usuario: str | None = None, base: str | None = None) -> str:
    partes = urlsplit(url)
    nombre = usuario or partes.username or ""
    clave = _PASSWORD_RUNTIME if usuario is not None else (partes.password or "")
    host = partes.hostname or ""
    puerto = f":{partes.port}" if partes.port else ""
    credenciales = f"{nombre}:{clave}" if clave else nombre
    netloc = f"{credenciales}@{host}{puerto}" if credenciales else f"{host}{puerto}"
    ruta = f"/{base}" if base else partes.path
    return urlunsplit((partes.scheme, netloc, ruta, partes.query, ""))


@pytest.fixture(scope="module")
def pg():
    """PostgreSQL desechable: migraciones desde cero + roles + semillas."""
    nombre_bd = f"cotizat_ci_{os.getpid()}"
    with psycopg.connect(_para_psycopg(ADMIN_URL), autocommit=True) as conn:
        conn.execute(f'CREATE DATABASE "{nombre_bd}"')
    url_admin_hija = _url_con(ADMIN_URL, base=nombre_bd)

    entorno = dict(
        os.environ,
        MIGRATION_DATABASE_URL=url_admin_hija,
        DATABASE_URL=url_admin_hija,
    )
    resultado = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=str(RAIZ),
        env=entorno,
        capture_output=True,
        text=True,
    )
    assert resultado.returncode == 0, (
        "La cadena de migraciones debe correr desde una base vacía:\n"
        + resultado.stderr[-2000:]
    )

    with psycopg.connect(_para_psycopg(url_admin_hija), autocommit=True) as conn:
        conn.execute(_SQL_RUNTIME)

    from app.db_config import _normalizar_url

    motor_admin = create_engine(_normalizar_url(url_admin_hija))
    url_runtime = _url_con(url_admin_hija, usuario="cotizat_runtime")
    motor_runtime = create_engine(_normalizar_url(url_runtime))

    SesionAdmin = sessionmaker(autoflush=False, bind=motor_admin)
    with SesionAdmin() as db:
        org_a = Organizacion(nombre="Constructora A (PG)", slug="constructora-a-pg")
        org_b = Organizacion(nombre="Constructora B (PG)", slug="constructora-b-pg")
        db.add_all([org_a, org_b])
        db.flush()
        usuario_a = Usuario(
            email="duena-a@pg.test",
            nombre="Dueña A",
            auth_user_id="11111111-1111-4111-8111-111111111111",
        )
        usuario_b = Usuario(
            email="duena-b@pg.test",
            nombre="Dueña B",
            auth_user_id="22222222-2222-4222-8222-222222222222",
        )
        db.add_all([usuario_a, usuario_b])
        db.flush()
        db.add_all(
            [
                Membresia(
                    usuario_id=usuario_a.id,
                    organizacion_id=org_a.id,
                    rol="propietario",
                ),
                Membresia(
                    usuario_id=usuario_b.id,
                    organizacion_id=org_b.id,
                    rol="propietario",
                ),
            ]
        )
        db.commit()
        semillas = {
            "org_a": org_a.id,
            "org_b": org_b.id,
            "usuario_a": usuario_a.id,
            "usuario_b": usuario_b.id,
            "auth_a": usuario_a.auth_user_id,
            "auth_b": usuario_b.auth_user_id,
        }

    datos = {"motor_runtime": motor_runtime, "motor_admin": motor_admin, **semillas}
    yield datos

    motor_runtime.dispose()
    motor_admin.dispose()
    with psycopg.connect(_para_psycopg(ADMIN_URL), autocommit=True) as conn:
        conn.execute(f'DROP DATABASE "{nombre_bd}" WITH (FORCE)')


def _sesion(pg, *, org=None, auth_id="", email="", operador=False):
    """Sesión runtime con los claims que instalaría una petición real."""
    Sesion = sessionmaker(autoflush=False, bind=pg["motor_runtime"])
    db = Sesion()
    if org is not None:
        db.info["organizacion_id"] = int(org)
    db.info["auth_user_id"] = auth_id
    db.info["auth_email"] = email
    db.info["es_operador"] = bool(operador)
    db.info["operador_rol"] = "admin" if operador else ""
    return db


# ---------------------------------------------------------------------------
# Soporte: el incidente del RETURNING, contra las políticas reales
# ---------------------------------------------------------------------------


def test_soporte_publico_inserta_sin_leer_ni_actualizar(pg):
    from app.services.soporte import registrar_mensaje

    db = _sesion(pg)  # sin sesión: como el formulario público
    try:
        fila, aviso_id = registrar_mensaje(
            db,
            nombre="Visitante",
            email="visitante@pg.test",
            tipo="queja",
            mensaje="Esto tiene que llegar al buzón también en PostgreSQL.",
            pagina="/soporte",
            notificar=False,
        )
        db.commit()
        numero = fila.id  # el handler lo lee aquí, tras el commit
        assert isinstance(numero, int) and numero > 0
        assert aviso_id == ""

        # La misma sesión pública no ve el buzón…
        assert db.query(MensajeSoporte).count() == 0
        # …ni puede tocar la fila que acaba de crear.
        afectadas = db.execute(
            update(MensajeSoporte)
            .where(MensajeSoporte.id == numero)
            .values(estado="resuelto")
        ).rowcount
        db.commit()
        assert afectadas == 0
    finally:
        db.close()

    # El operador sí lo lee, y sigue «nuevo».
    db_op = _sesion(pg, operador=True)
    try:
        guardada = db_op.get(MensajeSoporte, numero)
        assert guardada is not None
        assert guardada.estado == "nuevo"
        assert guardada.email == "visitante@pg.test"
    finally:
        db_op.close()


# ---------------------------------------------------------------------------
# Licencias: invisibles para el tenant, resumen por la función guardada
# ---------------------------------------------------------------------------


def test_resumen_licencia_por_funcion_segura(pg):
    from app.services.licencias import crear_licencia, resumen_licencia_cliente

    db_op = _sesion(pg, operador=True)
    try:
        crear_licencia(
            db_op,
            organizacion_id=pg["org_a"],
            origen="pago",
            duracion="1m",
            importe=9.99,
            metodo_cobro="Tarjeta (Stripe)",
            operador_email="titular@pg.test",
        )
        db_op.commit()
    finally:
        db_op.close()

    db = _sesion(pg, org=pg["org_a"], auth_id=pg["auth_a"], email="duena-a@pg.test")
    try:
        # La tabla del titular se comporta como vacía para el cliente…
        assert db.query(Licencia).count() == 0
        # …y el resumen llega por cotizat_security.organization_license_info.
        resumen = resumen_licencia_cliente(db, pg["org_a"])
        assert resumen["activo"] is True
        assert resumen["dias_restantes"] >= 28
        assert resumen["vence"] is not None
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Compras: el tenant compra, el operador activa, el vecino no ve nada
# ---------------------------------------------------------------------------


def test_compra_activacion_y_aislamiento_entre_organizaciones(pg):
    from app.services.compras import (
        activar_compra,
        compras_de_organizacion,
        crear_compra,
    )

    db_a = _sesion(pg, org=pg["org_a"], auth_id=pg["auth_a"], email="duena-a@pg.test")
    try:
        compra = crear_compra(
            db_a,
            organizacion_id=pg["org_a"],
            plan="anual",
            metodo_pago="usdt",
            datos_verificacion={"hash_transaccion": "TX-PG-1"},
            comprobante_reference="storage://tests/comprobante.png",
            comprobante_nombre="comprobante.png",
            comprobante_mime="image/png",
            creada_por_usuario_id=pg["usuario_a"],
            creada_por_email="duena-a@pg.test",
        )
        db_a.commit()
        compra_id = compra.id
        assert compra_id

        # Ni pidiendo todas sin filtro asoma la compra de la vecina (aún no
        # existe la suya: solo debe verse la propia).
        assert [c.id for c in db_a.query(CompraPlan).all()] == [compra_id]
    finally:
        db_a.close()

    db_b = _sesion(pg, org=pg["org_b"], auth_id=pg["auth_b"], email="duena-b@pg.test")
    try:
        assert db_b.query(CompraPlan).count() == 0
        assert compras_de_organizacion(db_b, pg["org_a"]) == []
    finally:
        db_b.close()

    db_op = _sesion(pg, operador=True)
    try:
        compra, licencia = activar_compra(
            db_op, compra_id=compra_id, operador_email="titular@pg.test"
        )
        db_op.commit()
        assert compra.estado == "activa"
        assert licencia.organizacion_id == pg["org_a"]
    finally:
        db_op.close()

    db_a = _sesion(pg, org=pg["org_a"], auth_id=pg["auth_a"], email="duena-a@pg.test")
    try:
        historial = compras_de_organizacion(db_a, pg["org_a"])
        assert [c.id for c in historial] == [compra_id]
        assert historial[0].licencia_vence is not None
    finally:
        db_a.close()


# ---------------------------------------------------------------------------
# /readyz: el contador de precios no debe chocar con el tipo boolean
# ---------------------------------------------------------------------------


def test_check_seo_contra_postgresql_sin_error_de_tipos(pg):
    from app.health import _check_seo

    checks = _check_seo(pg["motor_admin"], "cotizat.online")
    # Sin filas sembradas el contador es 0, pero la sentencia tiene que
    # planificarse: con «activo = 1» PostgreSQL rechazaba el tipo boolean
    # y producción devolvía el error en lugar de la cifra (20/10/2026).
    assert checks["precios_bd"] == "0 referencias nacionales en 0 paises"


# ---------------------------------------------------------------------------
# Errores internos (Fase 0.2): escritura sin sesión, lectura de operador
# ---------------------------------------------------------------------------


def test_errores_internos_funcion_y_rls(pg):
    from datetime import datetime

    from sqlalchemy import text
    from sqlalchemy.exc import ProgrammingError

    from app.models import ErrorInterno
    from app.services.errores_internos import huella_de, marcar_resuelto

    ahora = datetime(2026, 10, 20, 12, 0)
    huella = huella_de("GET", "/boom", "ValueError", "estalla")
    registrar = text(
        "SELECT cotizat_security.registrar_error_interno("
        ":huella, 'GET', '/boom', 'ValueError', 'estalla', 'traza de prueba', "
        ":usuario_email, :usuario_nombre, :ahora)"
    )

    # Sin sesión (claims vacíos, como un 500 anónimo): la función escribe
    # y discrimina huella nueva de repetida; la tabla, invisible.
    db = _sesion(pg)
    try:
        parametros = {
            "huella": huella,
            "usuario_email": "reporter@example.com",
            "usuario_nombre": "Reporter",
            "ahora": ahora,
        }
        assert db.execute(registrar, parametros).scalar() is True
        assert db.execute(registrar, parametros).scalar() is False
        db.commit()
        assert db.query(ErrorInterno).count() == 0
        with pytest.raises(ProgrammingError):
            db.execute(
                text(
                    "INSERT INTO errores_internos (huella, metodo, ruta, tipo, mensaje)"
                    " VALUES ('inyectada', 'GET', '/', 'X', 'y')"
                )
            )
        db.rollback()
    finally:
        db.close()

    # El operador la lee, la suma cuadra y puede marcarla resuelta.
    db_op = _sesion(pg, operador=True, email="titular@pg.test")
    try:
        fila = db_op.query(ErrorInterno).filter_by(huella=huella).one()
        assert fila.ocurrencias == 2
        assert fila.usuario_email == "reporter@example.com"
        assert fila.usuario_nombre == "Reporter"
        marcar_resuelto(db_op, fila.id)
        db_op.commit()
        assert fila.resuelto_en is not None
    finally:
        db_op.close()

    # Si el fallo vuelve, la función lo desmarca y pide avisar de nuevo.
    db = _sesion(pg)
    try:
        assert db.execute(registrar, parametros).scalar() is True
        db.commit()
    finally:
        db.close()
    db_op = _sesion(pg, operador=True, email="titular@pg.test")
    try:
        fila = db_op.query(ErrorInterno).filter_by(huella=huella).one()
        assert fila.ocurrencias == 3
        assert fila.resuelto_en is None
    finally:
        db_op.close()
