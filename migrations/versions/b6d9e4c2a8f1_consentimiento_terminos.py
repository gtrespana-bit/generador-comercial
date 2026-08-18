"""Registro de la aceptación de términos y privacidad (E4-038).

Cierra el hueco legal del alta: la pantalla de registro ya decía «al crear una
cuenta aceptas los términos», y la página de términos prometía que «la
aceptación o rechazo registra la versión, el nombre y email declarados y la
fecha y hora», pero nada de eso quedaba anotado. Esta migración lo hace real.

Tres piezas:

1. **Tabla ``consentimientos``** con unicidad (``email``, ``version``): cada
   persona consta una sola vez por versión aceptada, y el registro sobrevive
   al borrado de la organización. Como ``licencias`` o ``pruebas_concedidas``,
   **no es una tabla de tenant** —es información del titular sobre sus
   clientes—, así que lleva RLS de operador: FORCE ROW LEVEL SECURITY y
   políticas que exigen la marca ``cotizat.es_operador``. Sin política de
   DELETE: el registro de aceptación no se borra desde la aplicación.

2. **``cotizat_security.record_consent(...)``**, SECURITY DEFINER. La
   aceptación ocurre en el formulario de registro, **sin sesión todavía**
   (el correo se confirma después), y una sesión de cliente no puede escribir
   la tabla por RLS. La función inserta con la marca de operador elevada de
   forma local a la transacción y restaurada en todas las salidas.

3. **``cotizat_security.obtener_consentimiento(...)``**, SECURITY DEFINER. Es
   la lectura simétrica para que el alta de perfil (``sincronizar_usuario_auth``)
   pueda rellenar la marca «en la cuenta» (``usuarios.acepto_terminos_*``) sin
   abrir la tabla a sesiones de cliente.

Guardas, porque un SECURITY DEFINER mal hecho es un agujero:

- ``SET search_path = pg_catalog, public`` en ambas funciones.
- La elevación de ``cotizat.es_operador`` es local a la transacción y se
  restaura en todas las salidas, incluida la de excepción.
- ``record_consent`` solo inserta filas de consentimiento: no toca licencias,
  usuarios ni nada que conceda acceso; devuelve ``FALSE`` ante parámetros
  vacíos y es idempotente (``ON CONFLICT DO NOTHING``).
- Sin política de borrado y sin permiso de borrado: el registro es inmutable
  desde la aplicación.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "b6d9e4c2a8f1"
down_revision: Union[str, Sequence[str], None] = "a3d9c1e75b28"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


RECORD_CONSENT_SQL = """
CREATE OR REPLACE FUNCTION cotizat_security.record_consent(
  p_email varchar,
  p_nombre varchar,
  p_version varchar,
  p_ip_hash varchar
) RETURNS boolean LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
DECLARE
  v_email varchar;
  v_version varchar;
  v_operador_previo text;
  v_id integer;
BEGIN
  v_email := lower(btrim(COALESCE(p_email, '')));
  v_version := btrim(COALESCE(p_version, ''));
  IF v_email = '' OR v_version = '' THEN
    RETURN FALSE;
  END IF;

  -- Marca de operador durante el cuerpo. Igual que en `a3d9c1e75b28`, quien
  -- aplica la migración es superusuario en Supabase y ya bypassea el FORCE
  -- RLS, así que esto es defensa en profundidad: si algún día el propietario
  -- deja de bypassear, la función sigue satisfaciendo las políticas
  -- `cotizat_*` en lugar de romperse en silencio.
  v_operador_previo := COALESCE(
    pg_catalog.current_setting('cotizat.es_operador', true), 'off'
  );
  PERFORM pg_catalog.set_config('cotizat.es_operador', 'on', true);

  -- Idempotente: la misma persona aceptando la misma versión no duplica
  -- filas; la carrera entre dos altas simultáneas se cierra de forma atómica.
  INSERT INTO public.consentimientos (
    email, nombre, version, ip_hash, aceptado_en
  ) VALUES (
    v_email,
    left(COALESCE(p_nombre, ''), 200),
    left(v_version, 20),
    COALESCE(p_ip_hash, ''),
    (now() AT TIME ZONE 'utc')
  )
  ON CONFLICT (email, version) DO NOTHING
  RETURNING id INTO v_id;

  PERFORM pg_catalog.set_config(
    'cotizat.es_operador', v_operador_previo, true
  );
  RETURN v_id IS NOT NULL;

EXCEPTION WHEN OTHERS THEN
  -- La marca de operador nunca puede sobrevivir a un fallo: si quedara
  -- puesta, el resto de la petición vería la base con privilegios de operador.
  PERFORM pg_catalog.set_config(
    'cotizat.es_operador', COALESCE(v_operador_previo, 'off'), true
  );
  RAISE;
END;
$$
"""

OBTENER_CONSENTIMIENTO_SQL = """
CREATE OR REPLACE FUNCTION cotizat_security.obtener_consentimiento(
  p_email varchar
) RETURNS TABLE(version varchar, aceptado_en timestamp)
LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
DECLARE
  v_email varchar;
  v_operador_previo text;
BEGIN
  v_email := lower(btrim(COALESCE(p_email, '')));

  v_operador_previo := COALESCE(
    pg_catalog.current_setting('cotizat.es_operador', true), 'off'
  );
  PERFORM pg_catalog.set_config('cotizat.es_operador', 'on', true);

  RETURN QUERY
    SELECT c.version, c.aceptado_en
      FROM public.consentimientos c
     WHERE c.email = v_email
     ORDER BY c.aceptado_en DESC, c.id DESC
     LIMIT 1;

  PERFORM pg_catalog.set_config(
    'cotizat.es_operador', v_operador_previo, true
  );

EXCEPTION WHEN OTHERS THEN
  PERFORM pg_catalog.set_config(
    'cotizat.es_operador', COALESCE(v_operador_previo, 'off'), true
  );
  RAISE;
END;
$$
"""

_RECORD_SIGNATURE = "record_consent(varchar, varchar, varchar, varchar)"
_OBTENER_SIGNATURE = "obtener_consentimiento(varchar)"

#: Mismo criterio que ``licencias`` y ``pruebas_concedidas``: la tabla es del
#: titular, no de los clientes. Sin marca de operador no se ve ni una fila.
_POLITICAS = (
    (
        "cotizat_consentimiento_select",
        "FOR SELECT TO cotizat_app USING (%(guard)s)",
    ),
    (
        "cotizat_consentimiento_insert",
        "FOR INSERT TO cotizat_app WITH CHECK (%(guard)s)",
    ),
    (
        "cotizat_consentimiento_update",
        "FOR UPDATE TO cotizat_app USING (%(guard)s) WITH CHECK (%(guard)s)",
    ),
)

_GUARDA_OPERADOR = (
    "COALESCE("
    "pg_catalog.current_setting('cotizat.es_operador', true) = 'on',"
    " FALSE)"
)


def _postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    op.create_table(
        "consentimientos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column(
            "nombre", sa.String(length=200), nullable=False, server_default=""
        ),
        sa.Column("version", sa.String(length=20), nullable=False),
        sa.Column(
            "ip_hash", sa.String(length=64), nullable=False, server_default=""
        ),
        sa.Column(
            "aceptado_en",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", "version", name="uq_consentimiento_email_version"),
    )
    op.create_index("ix_consentimientos_email", "consentimientos", ["email"])
    op.create_index(
        "ix_consentimientos_aceptado_en", "consentimientos", ["aceptado_en"]
    )

    op.add_column(
        "usuarios",
        sa.Column(
            "acepto_terminos_version",
            sa.String(length=20),
            nullable=False,
            server_default="",
        ),
    )
    op.add_column(
        "usuarios",
        sa.Column("acepto_terminos_at", sa.DateTime(), nullable=True),
    )

    if not _postgres():
        # SQLite (escritorio y pruebas): sin RLS ni funciones de seguridad.
        # La aplicación escribe directamente y la unicidad sigue protegiendo.
        return

    op.execute(
        "GRANT SELECT, INSERT, UPDATE ON public.consentimientos TO cotizat_app"
    )
    op.execute(
        "GRANT USAGE, SELECT ON SEQUENCE public.consentimientos_id_seq"
        " TO cotizat_app"
    )
    op.execute("ALTER TABLE public.consentimientos ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE public.consentimientos FORCE ROW LEVEL SECURITY")
    for nombre, plantilla in _POLITICAS:
        cuerpo = plantilla % {"guard": _GUARDA_OPERADOR}
        op.execute(
            f"CREATE POLICY {nombre} ON public.consentimientos {cuerpo}"
        )

    op.execute(RECORD_CONSENT_SQL)
    op.execute(
        f"ALTER FUNCTION cotizat_security.{_RECORD_SIGNATURE} OWNER TO CURRENT_USER"
    )
    op.execute(
        f"REVOKE ALL ON FUNCTION cotizat_security.{_RECORD_SIGNATURE} FROM PUBLIC"
    )
    op.execute(
        f"GRANT EXECUTE ON FUNCTION cotizat_security.{_RECORD_SIGNATURE}"
        " TO cotizat_app"
    )

    op.execute(OBTENER_CONSENTIMIENTO_SQL)
    op.execute(
        f"ALTER FUNCTION cotizat_security.{_OBTENER_SIGNATURE} OWNER TO CURRENT_USER"
    )
    op.execute(
        f"REVOKE ALL ON FUNCTION cotizat_security.{_OBTENER_SIGNATURE} FROM PUBLIC"
    )
    op.execute(
        f"GRANT EXECUTE ON FUNCTION cotizat_security.{_OBTENER_SIGNATURE}"
        " TO cotizat_app"
    )


def downgrade() -> None:
    if _postgres():
        op.execute(
            f"DROP FUNCTION IF EXISTS cotizat_security.{_OBTENER_SIGNATURE}"
        )
        op.execute(
            f"DROP FUNCTION IF EXISTS cotizat_security.{_RECORD_SIGNATURE}"
        )
        for nombre, _ in _POLITICAS:
            op.execute(
                f"DROP POLICY IF EXISTS {nombre} ON public.consentimientos"
            )

    op.drop_index("ix_consentimientos_aceptado_en", table_name="consentimientos")
    op.drop_index("ix_consentimientos_email", table_name="consentimientos")
    op.drop_table("consentimientos")
    op.drop_column("usuarios", "acepto_terminos_at")
    op.drop_column("usuarios", "acepto_terminos_version")
