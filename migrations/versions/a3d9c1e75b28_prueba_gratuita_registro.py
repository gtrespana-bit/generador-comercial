"""Prueba gratuita de 7 días con registro anti-reciclaje de cuentas.

Dos piezas:

1. **Tabla ``pruebas_concedidas``** con restricción única sobre el correo
   normalizado. Es el registro de qué identidades ya gastaron su prueba, y
   sobrevive al borrado de la organización: la prueba se consumió igual.
   Como ``licencias``, **no es una tabla de tenant** —es información del
   negocio del titular sobre sus clientes—, así que lleva RLS de operador:
   FORCE ROW LEVEL SECURITY y políticas que exigen la marca
   ``cotizat.es_operador``. Ninguna sesión de cliente la lee ni la escribe.

2. **``cotizat_security.grant_trial_license(...)``**, SECURITY DEFINER. Sin
   ella la prueba automática sería imposible: quien se registra es un cliente,
   y la RLS de ``f4c1d8e37a95`` reserva toda escritura sobre ``licencias`` a
   sesiones de operador. La función inserta **la licencia y la marca a la vez**;
   si se hicieran por separado, una caída entre ambas dejaría o una prueba que
   se puede repetir indefinidamente, o un cliente marcado y sin sus días.

Guardias de la función, porque un SECURITY DEFINER mal hecho es un agujero:

- Solo concede a la organización del claim de la sesión
  (``cotizat.organization_id``), así que nadie regala licencias a terceros.
- Solo crea licencias con ``origen='prueba'``, importe 0 y duración acotada:
  aunque se llame con parámetros hostiles, no puede fabricar un año de acceso
  de pago.
- No concede si la organización ya tuvo **cualquier** licencia: la prueba es
  para empezar, no para encadenar.
- Devuelve ``FALSE`` en vez de fallar cuando la identidad ya gastó su prueba;
  el conflicto se resuelve con ``ON CONFLICT DO NOTHING``, que es atómico y
  cierra la carrera entre dos altas simultáneas.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "a3d9c1e75b28"
down_revision: Union[str, Sequence[str], None] = "c7f1a3b9d425"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


#: Tope duro dentro de la propia base: el parámetro de días no puede convertir
#: una prueba en una licencia perpetua ni aunque la aplicación se equivoque.
_MAXIMO_DIAS_PRUEBA = 90

TRIAL_FUNCTION_SQL = f"""
CREATE OR REPLACE FUNCTION cotizat_security.grant_trial_license(
  p_organization_id integer,
  p_email_normalizado varchar,
  p_email_original varchar,
  p_ip_hash varchar,
  p_dias integer
) RETURNS boolean LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
DECLARE
  v_dias integer;
  v_licencia_id integer;
  v_marca_id integer;
  v_operador_previo text;
BEGIN
  -- La organización debe ser la de la sesión: nadie concede licencias ajenas.
  IF COALESCE(
       pg_catalog.current_setting('cotizat.organization_id', true),
       ''
     ) <> p_organization_id::text THEN
    RETURN FALSE;
  END IF;

  IF COALESCE(p_email_normalizado, '') = '' THEN
    RETURN FALSE;
  END IF;

  v_dias := LEAST(GREATEST(COALESCE(p_dias, 0), 1), {_MAXIMO_DIAS_PRUEBA});

  -- Marca de operador durante el cuerpo. Igual que en `b7c4a9e2d31f`, quien
  -- aplica la migración es superusuario en Supabase y ya bypassea el FORCE RLS
  -- de `licencias`, así que esto es defensa en profundidad: si algún día el
  -- propietario deja de bypassear, la función sigue satisfaciendo las
  -- políticas `cotizat_*` en lugar de romperse en silencio.
  --
  -- Se eleva **aquí y no más abajo** por un motivo de corrección, no de estilo:
  -- la comprobación de licencia previa es un SELECT sobre `licencias`. Si esa
  -- lectura quedara filtrada por RLS devolvería cero filas y la función
  -- concedería prueba a organizaciones que ya la tuvieron: un fallo abierto,
  -- que es el peor tipo.
  --
  -- La elevación es local a la transacción y se restaura en todas las salidas,
  -- incluida la de excepción: la sesión del cliente nunca la hereda.
  v_operador_previo := COALESCE(
    pg_catalog.current_setting('cotizat.es_operador', true), 'off'
  );
  PERFORM pg_catalog.set_config('cotizat.es_operador', 'on', true);

  -- La prueba es para empezar. Si la organización ya tuvo licencia de
  -- cualquier tipo, no hay nada que conceder.
  IF EXISTS (
    SELECT 1 FROM public.licencias WHERE organizacion_id = p_organization_id
  ) THEN
    PERFORM pg_catalog.set_config(
      'cotizat.es_operador', v_operador_previo, true
    );
    RETURN FALSE;
  END IF;

  -- Se marca primero la identidad: si ya constaba, ON CONFLICT no devuelve
  -- fila y salimos sin crear licencia. Esto resuelve la carrera entre dos
  -- altas simultáneas del mismo correo de forma atómica.
  INSERT INTO public.pruebas_concedidas (
    email_normalizado, email_original, organizacion_id, ip_hash, dias, created_at
  ) VALUES (
    p_email_normalizado,
    COALESCE(p_email_original, ''),
    p_organization_id,
    COALESCE(p_ip_hash, ''),
    v_dias,
    (now() AT TIME ZONE 'utc')
  )
  ON CONFLICT (email_normalizado) DO NOTHING
  RETURNING id INTO v_marca_id;

  IF v_marca_id IS NULL THEN
    PERFORM pg_catalog.set_config(
      'cotizat.es_operador', v_operador_previo, true
    );
    RETURN FALSE;
  END IF;

  INSERT INTO public.licencias (
    organizacion_id, estado, origen, inicio, vence,
    importe, moneda, metodo_cobro, referencia, notas,
    creada_por_email, created_at
  ) VALUES (
    p_organization_id,
    'activa',
    'prueba',
    CURRENT_DATE,
    CURRENT_DATE + (v_dias - 1),
    0,
    'USD',
    '',
    '',
    'Prueba gratuita automática al crear la organización.',
    'sistema@cotizat',
    (now() AT TIME ZONE 'utc')
  )
  RETURNING id INTO v_licencia_id;

  UPDATE public.pruebas_concedidas
     SET licencia_id = v_licencia_id
   WHERE id = v_marca_id;

  PERFORM pg_catalog.set_config(
    'cotizat.es_operador', v_operador_previo, true
  );
  RETURN TRUE;

EXCEPTION WHEN OTHERS THEN
  -- La marca de operador nunca puede sobrevivir a un fallo: si quedara puesta,
  -- el resto de la petición vería la base con privilegios de operador.
  PERFORM pg_catalog.set_config(
    'cotizat.es_operador', COALESCE(v_operador_previo, 'off'), true
  );
  RAISE;
END;
$$
"""

_FUNCTION_SIGNATURE = (
    "grant_trial_license(integer, varchar, varchar, varchar, integer)"
)

#: Mismo criterio que ``licencias``: la tabla es del titular, no de los
#: clientes. Sin marca de operador no se ve ni una fila.
_POLITICAS = (
    (
        "cotizat_prueba_select",
        "FOR SELECT TO cotizat_app USING (%(guard)s)",
    ),
    (
        "cotizat_prueba_insert",
        "FOR INSERT TO cotizat_app WITH CHECK (%(guard)s)",
    ),
    (
        "cotizat_prueba_update",
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
        "pruebas_concedidas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email_normalizado", sa.String(length=254), nullable=False),
        sa.Column(
            "email_original",
            sa.String(length=254),
            nullable=False,
            server_default="",
        ),
        sa.Column("organizacion_id", sa.Integer(), nullable=True),
        sa.Column("licencia_id", sa.Integer(), nullable=True),
        sa.Column(
            "ip_hash", sa.String(length=64), nullable=False, server_default=""
        ),
        sa.Column("dias", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["organizacion_id"], ["organizaciones.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["licencia_id"], ["licencias.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email_normalizado", name="uq_prueba_email_normalizado"),
    )
    op.create_index(
        "ix_pruebas_concedidas_creada", "pruebas_concedidas", ["created_at"]
    )
    op.create_index("ix_pruebas_concedidas_ip", "pruebas_concedidas", ["ip_hash"])
    op.create_index(
        "ix_pruebas_concedidas_organizacion_id",
        "pruebas_concedidas",
        ["organizacion_id"],
    )
    op.create_index(
        "ix_pruebas_concedidas_licencia_id", "pruebas_concedidas", ["licencia_id"]
    )

    if not _postgres():
        # SQLite (escritorio y pruebas): sin RLS ni funciones de seguridad. La
        # aplicación escribe directamente y la unicidad sigue protegiendo.
        return

    op.execute("GRANT SELECT, INSERT, UPDATE ON public.pruebas_concedidas TO cotizat_app")
    op.execute(
        "GRANT USAGE, SELECT ON SEQUENCE public.pruebas_concedidas_id_seq"
        " TO cotizat_app"
    )
    op.execute("ALTER TABLE public.pruebas_concedidas ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE public.pruebas_concedidas FORCE ROW LEVEL SECURITY")
    for nombre, plantilla in _POLITICAS:
        cuerpo = plantilla % {"guard": _GUARDA_OPERADOR}
        op.execute(
            f"CREATE POLICY {nombre} ON public.pruebas_concedidas {cuerpo}"
        )

    op.execute(TRIAL_FUNCTION_SQL)
    op.execute(
        f"ALTER FUNCTION cotizat_security.{_FUNCTION_SIGNATURE} OWNER TO CURRENT_USER"
    )
    op.execute(
        f"REVOKE ALL ON FUNCTION cotizat_security.{_FUNCTION_SIGNATURE} FROM PUBLIC"
    )
    op.execute(
        f"GRANT EXECUTE ON FUNCTION cotizat_security.{_FUNCTION_SIGNATURE}"
        " TO cotizat_app"
    )


def downgrade() -> None:
    if _postgres():
        op.execute(
            f"DROP FUNCTION IF EXISTS cotizat_security.{_FUNCTION_SIGNATURE}"
        )
        for nombre, _ in _POLITICAS:
            op.execute(
                f"DROP POLICY IF EXISTS {nombre} ON public.pruebas_concedidas"
            )

    op.drop_index("ix_pruebas_concedidas_licencia_id", table_name="pruebas_concedidas")
    op.drop_index(
        "ix_pruebas_concedidas_organizacion_id", table_name="pruebas_concedidas"
    )
    op.drop_index("ix_pruebas_concedidas_ip", table_name="pruebas_concedidas")
    op.drop_index("ix_pruebas_concedidas_creada", table_name="pruebas_concedidas")
    op.drop_table("pruebas_concedidas")
