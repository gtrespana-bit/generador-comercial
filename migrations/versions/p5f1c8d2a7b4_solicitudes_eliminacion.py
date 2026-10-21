"""Solicitudes de eliminación total de cuenta y datos (bloque 2).

Cierra el hueco de supresión: hasta ahora un propietario podía dar de baja su
organización (E3-023), pero no existía vía para pedir el borrado de la **cuenta
personal** ni para que el operador lo ejecutara de forma registrada. Esta
migración crea la pieza de registro; la ejecución (purga) es manual del
operador y llega en un bloque posterior.

Tres piezas:

1. **Tabla ``solicitudes_eliminacion``**: la petición formal de supresión con
   su ciclo de vida (``pendiente`` → ``cancelada`` por el propio usuario o
   ``ejecutada`` por el operador). Como ``licencias`` o ``consentimientos``,
   **no es una tabla de tenant** —es información del titular sobre sus
   clientes—, así que lleva RLS de operador: FORCE ROW LEVEL SECURITY y
   políticas que exigen la marca ``cotizat.es_operador``. Sin DELETE: la
   solicitud es el acta de que la supresión se pidió y se hizo, y debe
   sobrevivir a la purga (``usuario_id`` con ``ON DELETE SET NULL``). Al
   ejecutarse, el email en claro desaparece de la base y solo queda
   ``email_hash`` (irreversible), para que el anti-abuso de pruebas siga
   funcionando sin conservar el correo.

2. **``cotizat_security.solicitar_eliminacion(...)``**, SECURITY DEFINER. Una
   sesión de cliente no puede escribir la tabla por RLS, así que la creación
   entra por aquí. Es idempotente: si ya hay una solicitud ``pendiente`` de
   esa persona devuelve su id sin duplicar.

3. **``cotizat_security.solicitud_eliminacion_pendiente(...)``** y
   **``cotizat_security.cancelar_solicitud_eliminacion(...)``**, SECURITY
   DEFINER: la lectura del propio estado para ``/cuenta`` y la cancelación
   por el propio usuario.

Guardas, porque un SECURITY DEFINER mal hecho es un agujero:

- ``SET search_path = pg_catalog, public`` en las tres funciones.
- Las tres exigen que el claim de sesión ``cotizat.auth_user_id`` coincida con
  el ``p_auth_user_id`` recibido: nadie puede pedir, ver ni cancelar la
  supresión de otra persona, ni siquiera conociendo su UUID.
- La elevación de ``cotizat.es_operador`` es local a la transacción y se
  restaura en todas las salidas, incluida la de excepción.
- Las funciones solo tocan ``solicitudes_eliminacion``: no conceden acceso,
  no borran datos y no pueden marcar una solicitud como ejecutada.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "p5f1c8d2a7b4"
down_revision: Union[str, Sequence[str], None] = "o2e4a6c8b1d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


#: Guarda común: el claim de sesión debe ser exactamente la persona afectada.
#: Sin claim (sesión anónima o de sistema) la función no hace nada.
_GUARDA_CLAIM = """
  v_claim := NULLIF(
    pg_catalog.current_setting('cotizat.auth_user_id', true), ''
  );
  IF v_claim IS NULL OR v_claim <> btrim(COALESCE(p_auth_user_id, '')) THEN
    RAISE EXCEPTION 'La sesión no corresponde a la cuenta indicada.';
  END IF;
"""

SOLICITAR_ELIMINACION_SQL = """
CREATE OR REPLACE FUNCTION cotizat_security.solicitar_eliminacion(
  p_usuario_id integer,
  p_auth_user_id varchar,
  p_email varchar,
  p_nombre varchar,
  p_motivo varchar,
  p_email_hash varchar
) RETURNS integer LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
DECLARE
  v_claim text;
  v_email varchar;
  v_operador_previo text;
  v_id integer;
BEGIN
""" + _GUARDA_CLAIM + """
  v_email := lower(btrim(COALESCE(p_email, '')));
  IF v_email = '' THEN
    RAISE EXCEPTION 'La solicitud necesita el email de la cuenta.';
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

  -- Idempotente: una segunda solicitud (doble clic, reintento) devuelve la
  -- pendiente que ya existe en lugar de duplicar el acta.
  SELECT id INTO v_id
    FROM public.solicitudes_eliminacion
   WHERE auth_user_id = v_claim
     AND estado = 'pendiente'
   ORDER BY id ASC
   LIMIT 1;

  IF v_id IS NULL THEN
    INSERT INTO public.solicitudes_eliminacion (
      usuario_id, auth_user_id, email, nombre, motivo,
      estado, created_at, email_hash
    ) VALUES (
      p_usuario_id,
      v_claim,
      v_email,
      left(COALESCE(p_nombre, ''), 200),
      left(COALESCE(p_motivo, ''), 4000),
      'pendiente',
      (now() AT TIME ZONE 'utc'),
      left(COALESCE(p_email_hash, ''), 64)
    )
    RETURNING id INTO v_id;
  END IF;

  PERFORM pg_catalog.set_config(
    'cotizat.es_operador', v_operador_previo, true
  );
  RETURN v_id;

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

SOLICITUD_PENDIENTE_SQL = """
CREATE OR REPLACE FUNCTION cotizat_security.solicitud_eliminacion_pendiente(
  p_auth_user_id varchar
) RETURNS TABLE(id integer, created_at timestamp, motivo varchar)
LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
DECLARE
  v_claim text;
  v_operador_previo text;
BEGIN
""" + _GUARDA_CLAIM + """
  v_operador_previo := COALESCE(
    pg_catalog.current_setting('cotizat.es_operador', true), 'off'
  );
  PERFORM pg_catalog.set_config('cotizat.es_operador', 'on', true);

  RETURN QUERY
    SELECT s.id, s.created_at, s.motivo::varchar
      FROM public.solicitudes_eliminacion s
     WHERE s.auth_user_id = v_claim
       AND s.estado = 'pendiente'
     ORDER BY s.id ASC
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

CANCELAR_SOLICITUD_SQL = """
CREATE OR REPLACE FUNCTION cotizat_security.cancelar_solicitud_eliminacion(
  p_auth_user_id varchar
) RETURNS boolean LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
DECLARE
  v_claim text;
  v_operador_previo text;
  v_filas integer;
BEGIN
""" + _GUARDA_CLAIM + """
  v_operador_previo := COALESCE(
    pg_catalog.current_setting('cotizat.es_operador', true), 'off'
  );
  PERFORM pg_catalog.set_config('cotizat.es_operador', 'on', true);

  -- Solo la pendiente propia: una ejecutada ya no se puede deshacer y una
  -- cancelada no cambia.
  UPDATE public.solicitudes_eliminacion
     SET estado = 'cancelada',
         cancelada_at = (now() AT TIME ZONE 'utc')
   WHERE auth_user_id = v_claim
     AND estado = 'pendiente';
  GET DIAGNOSTICS v_filas = ROW_COUNT;

  PERFORM pg_catalog.set_config(
    'cotizat.es_operador', v_operador_previo, true
  );
  RETURN v_filas > 0;

EXCEPTION WHEN OTHERS THEN
  PERFORM pg_catalog.set_config(
    'cotizat.es_operador', COALESCE(v_operador_previo, 'off'), true
  );
  RAISE;
END;
$$
"""

_SOLICITAR_SIGNATURE = "solicitar_eliminacion(integer, varchar, varchar, varchar, varchar, varchar)"
_PENDIENTE_SIGNATURE = "solicitud_eliminacion_pendiente(varchar)"
_CANCELAR_SIGNATURE = "cancelar_solicitud_eliminacion(varchar)"

#: Mismo criterio que `consentimientos`: la tabla es del titular, no de los
#: clientes. Sin marca de operador no se ve ni una fila; las escrituras del
#: cliente entran solo por las funciones SECURITY DEFINER de arriba.
_POLITICAS = (
    (
        "cotizat_se_select",
        "FOR SELECT TO cotizat_app USING (%(guard)s)",
    ),
    (
        "cotizat_se_insert",
        "FOR INSERT TO cotizat_app WITH CHECK (%(guard)s)",
    ),
    (
        "cotizat_se_update",
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


def _instalar_funcion(sql: str, signature: str) -> None:
    op.execute(sql)
    op.execute(
        f"ALTER FUNCTION cotizat_security.{signature} OWNER TO CURRENT_USER"
    )
    op.execute(
        f"REVOKE ALL ON FUNCTION cotizat_security.{signature} FROM PUBLIC"
    )
    op.execute(
        f"GRANT EXECUTE ON FUNCTION cotizat_security.{signature}"
        " TO cotizat_app"
    )


def upgrade() -> None:
    op.create_table(
        "solicitudes_eliminacion",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column(
            "auth_user_id",
            sa.String(length=36),
            nullable=False,
            server_default="",
        ),
        sa.Column(
            "email", sa.String(length=254), nullable=False, server_default=""
        ),
        sa.Column(
            "nombre", sa.String(length=200), nullable=False, server_default=""
        ),
        sa.Column("motivo", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "estado",
            sa.String(length=20),
            nullable=False,
            server_default="pendiente",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("cancelada_at", sa.DateTime(), nullable=True),
        sa.Column("ejecutada_at", sa.DateTime(), nullable=True),
        sa.Column(
            "ejecutada_por",
            sa.String(length=254),
            nullable=False,
            server_default="",
        ),
        sa.Column(
            "auth_pendiente",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "email_hash",
            sa.String(length=64),
            nullable=False,
            server_default="",
        ),
        sa.ForeignKeyConstraint(
            ["usuario_id"], ["usuarios.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "estado IN ('pendiente', 'cancelada', 'ejecutada')",
            name="ck_solic_elim_estado_valido",
        ),
    )
    op.create_index(
        "ix_solicitudes_eliminacion_usuario_id",
        "solicitudes_eliminacion",
        ["usuario_id"],
    )
    op.create_index(
        "ix_solicitudes_eliminacion_email_hash",
        "solicitudes_eliminacion",
        ["email_hash"],
    )
    op.create_index(
        "ix_solic_elim_estado_creada",
        "solicitudes_eliminacion",
        ["estado", "created_at"],
    )
    op.create_index(
        "ix_solic_elim_auth", "solicitudes_eliminacion", ["auth_user_id"]
    )

    if not _postgres():
        # SQLite (escritorio y pruebas): sin RLS ni funciones de seguridad.
        # La aplicación escribe directamente y filtra por el usuario.
        return

    op.execute(
        "GRANT SELECT, INSERT, UPDATE ON public.solicitudes_eliminacion"
        " TO cotizat_app"
    )
    op.execute(
        "GRANT USAGE, SELECT ON SEQUENCE"
        " public.solicitudes_eliminacion_id_seq TO cotizat_app"
    )
    op.execute(
        "ALTER TABLE public.solicitudes_eliminacion ENABLE ROW LEVEL SECURITY"
    )
    op.execute(
        "ALTER TABLE public.solicitudes_eliminacion FORCE ROW LEVEL SECURITY"
    )
    for nombre, plantilla in _POLITICAS:
        cuerpo = plantilla % {"guard": _GUARDA_OPERADOR}
        op.execute(
            f"CREATE POLICY {nombre} ON public.solicitudes_eliminacion {cuerpo}"
        )

    _instalar_funcion(SOLICITAR_ELIMINACION_SQL, _SOLICITAR_SIGNATURE)
    _instalar_funcion(SOLICITUD_PENDIENTE_SQL, _PENDIENTE_SIGNATURE)
    _instalar_funcion(CANCELAR_SOLICITUD_SQL, _CANCELAR_SIGNATURE)


def downgrade() -> None:
    if _postgres():
        op.execute(
            f"DROP FUNCTION IF EXISTS cotizat_security.{_CANCELAR_SIGNATURE}"
        )
        op.execute(
            f"DROP FUNCTION IF EXISTS cotizat_security.{_PENDIENTE_SIGNATURE}"
        )
        op.execute(
            f"DROP FUNCTION IF EXISTS cotizat_security.{_SOLICITAR_SIGNATURE}"
        )
        for nombre, _ in _POLITICAS:
            op.execute(
                f"DROP POLICY IF EXISTS {nombre}"
                " ON public.solicitudes_eliminacion"
            )

    op.drop_index("ix_solic_elim_auth", table_name="solicitudes_eliminacion")
    op.drop_index(
        "ix_solic_elim_estado_creada", table_name="solicitudes_eliminacion"
    )
    op.drop_index(
        "ix_solicitudes_eliminacion_email_hash",
        table_name="solicitudes_eliminacion",
    )
    op.drop_index(
        "ix_solicitudes_eliminacion_usuario_id",
        table_name="solicitudes_eliminacion",
    )
    op.drop_table("solicitudes_eliminacion")
