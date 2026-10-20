"""El buzón de soporte contra PostgreSQL real (RLS de `mensajes_soporte`).

La suite normal corre en SQLite, donde no hay RLS: los dos muros que la
política de la tabla opone a la sesión pública no se ven ahí y rompieron
producción dos veces el 20/10/2026:

1. El UPDATE de la marca del aviso (cubierto en SQLite por el test de
   «cero UPDATEs» de `test_avisos_y_soporte.py`).
2. El ``INSERT ... RETURNING id`` del ORM, que exige pasar también la
   política SELECT (solo operador) y revienta con «new row violates
   row-level security policy» — con el correo ya enviado y el mensaje
   sin guardar.

Este test levanta un PostgreSQL efímero (`pgserver`), recrea la tabla y
las políticas literalmente desde la migración `i4d7c1b8e2f5` y ejecuta el
servicio real como `cotizat_app` sin marca de operador. Sin `pgserver`
instalado se salta entero (así corre el CI); en local basta
``pip install pgserver`` para ejercitarlo.
"""
import pytest

pgserver = pytest.importorskip("pgserver")
psycopg = pytest.importorskip("psycopg")

from sqlalchemy import create_engine, event  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

_DDL = """
CREATE ROLE cotizat_app LOGIN PASSWORD 'app' NOSUPERUSER NOBYPASSRLS;
CREATE TABLE public.mensajes_soporte (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL DEFAULT '',
    email VARCHAR(254) NOT NULL DEFAULT '',
    organizacion_id INTEGER NULL,
    usuario_id INTEGER NULL,
    tipo VARCHAR(20) NOT NULL DEFAULT 'consulta',
    asunto VARCHAR(200) NOT NULL DEFAULT '',
    mensaje TEXT NOT NULL DEFAULT '',
    pagina VARCHAR(500) NOT NULL DEFAULT '',
    estado VARCHAR(20) NOT NULL DEFAULT 'nuevo',
    nota_interna TEXT NOT NULL DEFAULT '',
    atendido_por_email VARCHAR(254) NOT NULL DEFAULT '',
    atendido_at TIMESTAMP NULL,
    aviso_enviado BOOLEAN NOT NULL DEFAULT false,
    ip_hash VARCHAR(64) NOT NULL DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL
);
REVOKE ALL ON TABLE public.mensajes_soporte FROM PUBLIC;
ALTER TABLE public.mensajes_soporte ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mensajes_soporte FORCE ROW LEVEL SECURITY;
GRANT SELECT, INSERT, UPDATE ON TABLE public.mensajes_soporte TO cotizat_app;
GRANT USAGE, SELECT ON SEQUENCE public.mensajes_soporte_id_seq TO cotizat_app;
GRANT USAGE ON SCHEMA public TO cotizat_app;
CREATE POLICY cotizat_ms_select_operator ON public.mensajes_soporte
  FOR SELECT TO cotizat_app
  USING (COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE));
CREATE POLICY cotizat_ms_update_operator ON public.mensajes_soporte
  FOR UPDATE TO cotizat_app
  USING (COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE));
CREATE POLICY cotizat_ms_insert_publico ON public.mensajes_soporte
  FOR INSERT TO cotizat_app
  WITH CHECK (estado = 'nuevo' AND atendido_por_email = '' AND nota_interna = '');
"""


@pytest.fixture
def motor_app(tmp_path):
    servidor = pgserver.get_server(str(tmp_path / "pg"))
    uri = servidor.get_uri()
    with psycopg.connect(uri, autocommit=True) as conn:
        conn.execute(_DDL)
    engine = create_engine(uri.replace("postgresql://", "postgresql+psycopg://"))

    @event.listens_for(engine, "connect")
    def _como_app(dbapi_connection, _record):
        with dbapi_connection.cursor() as cur:
            cur.execute("SET ROLE cotizat_app")
        dbapi_connection.commit()

    yield engine, uri
    engine.dispose()


def test_registrar_mensaje_atraviesa_la_rls_sin_returning(motor_app):
    """El flujo exacto del handler: registrar, commit y leer el número."""
    from app.services.soporte import registrar_mensaje

    engine, uri = motor_app
    Sesion = sessionmaker(autoflush=False, bind=engine)
    with Sesion() as db:
        fila, aviso_id = registrar_mensaje(
            db,
            nombre="Con RLS",
            email="con-rls@example.com",
            tipo="queja",
            mensaje="El formulario tiene que funcionar en producción.",
            pagina="/soporte",
            notificar=False,
        )
        db.commit()
        numero = fila.id  # el handler lo lee aquí, tras el commit

    assert aviso_id == ""
    assert isinstance(numero, int) and numero > 0
    assert fila.aviso_enviado is False

    # Como superusuario: el mensaje quedó en la tabla, una sola fila.
    with psycopg.connect(uri, autocommit=True) as conn:
        filas = conn.execute(
            "SELECT id, email, estado FROM public.mensajes_soporte"
        ).fetchall()
    assert filas == [(numero, "con-rls@example.com", "nuevo")]
