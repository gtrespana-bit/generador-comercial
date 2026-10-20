"""Registro durable de errores internos: ``public.errores_internos``.

Fase 0.2 de la hoja de ruta 2026-10-20. El registro de excepciones no
capturadas vivía en un buffer **en memoria** (``app/services/operacion.py``):
en el despliegue serverless cada instancia guarda el suyo y se pierde al
reiniciar, así que un 500 de madrugada era invisible a la mañana siguiente.
Esta tabla es el sumidero propio —sin SDK de terceros— que el propio panel
declaraba como siguiente paso.

Diseño de acceso (es telemetría del sistema, no datos de tenant):

- **Una fila por huella** (sha256 de método + ruta saneada + tipo +
  mensaje). El mismo fallo repetido solo suma ``ocurrencias`` y refresca
  la traza. ``resuelto_en`` lo marca el operador; una recurrencia lo
  limpia y la huella vuelve a contar como nueva para el aviso.
- **La escritura no usa claims**: el middleware captura la excepción en
  cualquier contexto (un 500 anónimo no tiene sesión), así que en lugar
  de una política de INSERT abierta —que permitiría inyectar filas con
  cualquier contenido— la única puerta es la función SECURITY DEFINER
  ``cotizat_security.registrar_error_interno``, que hace el UPSERT por
  huella y devuelve si toca avisar por correo (huella nueva o resucitada
  tras estar resuelta). El rol de aplicación recibe EXECUTE y **ningún**
  INSERT directo sobre la tabla.
- **Leer, marcar resuelto y podar: solo el operador** (el mismo claim
  ``cotizat.es_operador`` del buzón de soporte). Las trazas pueden llevar
  fragmentos de SQL o rutas internas: son para los ojos del titular.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "o2e4a6c8b1d3"
down_revision: Union[str, Sequence[str], None] = "n9f2a5b8c3d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "errores_internos"
APP_ROLE = "cotizat_app"
FUNCION = "registrar_error_interno"
FIRMA = "text, text, text, text, text, text, timestamp without time zone"

IS_OPERATOR = """
  COALESCE(
    pg_catalog.current_setting('cotizat.es_operador', true) = 'on',
    FALSE
  )
"""


def _postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("huella", sa.String(length=64), nullable=False, unique=True),
        sa.Column("metodo", sa.String(length=10), nullable=False, server_default=""),
        sa.Column("ruta", sa.String(length=160), nullable=False, server_default="/"),
        sa.Column("tipo", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("mensaje", sa.String(length=300), nullable=False, server_default=""),
        sa.Column("traza", sa.Text(), nullable=False, server_default=""),
        sa.Column("ocurrencias", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "primera_vez",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "ultima_vez",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("resuelto_en", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_errores_internos_ultima", TABLE, ["ultima_vez"])
    op.create_index(
        "ix_errores_internos_pendientes", TABLE, ["resuelto_en", "ultima_vez"]
    )

    if not _postgres():
        # SQLite (escritorio y pruebas) no tiene RLS ni funciones: el
        # servicio hace el UPSERT con SQLAlchemy y el aislamiento lo
        # aporta la aplicación (solo el panel del operador lee la tabla).
        return

    op.execute(f"REVOKE ALL ON TABLE public.{TABLE} FROM PUBLIC")
    op.execute(f"ALTER TABLE public.{TABLE} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE public.{TABLE} FORCE ROW LEVEL SECURITY")
    # Sin INSERT: la escritura entra solo por la función de más abajo.
    op.execute(f"GRANT SELECT, UPDATE, DELETE ON TABLE public.{TABLE} TO {APP_ROLE}")

    for nombre, accion, clausula in (
        ("cotizat_ei_select_operator", "SELECT", f"USING ({IS_OPERATOR})"),
        (
            "cotizat_ei_update_operator",
            "UPDATE",
            f"USING ({IS_OPERATOR}) WITH CHECK ({IS_OPERATOR})",
        ),
        ("cotizat_ei_delete_operator", "DELETE", f"USING ({IS_OPERATOR})"),
    ):
        op.execute(
            f"DROP POLICY IF EXISTS {nombre} ON public.{TABLE}"
        )
        op.execute(
            f"CREATE POLICY {nombre} ON public.{TABLE} "
            f"FOR {accion} TO {APP_ROLE} {clausula}"
        )

    # UPSERT por huella. Devuelve «hay que avisar»: TRUE si la fila es
    # nueva (xmax = 0) o si existía marcada como resuelta y el fallo ha
    # vuelto. La CTE ``previo`` comparte la instantánea de la sentencia y
    # no ve el efecto del UPSERT, así que lee el estado anterior real.
    op.execute(
        f"""
        CREATE OR REPLACE FUNCTION cotizat_security.{FUNCION}(
          p_huella text,
          p_metodo text,
          p_ruta text,
          p_tipo text,
          p_mensaje text,
          p_traza text,
          p_ahora timestamp without time zone
        ) RETURNS boolean
        LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
        DECLARE
          v_avisar boolean;
        BEGIN
          WITH previo AS (
            SELECT resuelto_en IS NOT NULL AS estaba_resuelto
            FROM public.errores_internos
            WHERE huella = p_huella
          ), upsert AS (
            INSERT INTO public.errores_internos (
              huella, metodo, ruta, tipo, mensaje, traza,
              ocurrencias, primera_vez, ultima_vez, resuelto_en
            ) VALUES (
              p_huella,
              left(COALESCE(p_metodo, ''), 10),
              left(COALESCE(NULLIF(p_ruta, ''), '/'), 160),
              left(COALESCE(p_tipo, ''), 120),
              left(COALESCE(p_mensaje, ''), 300),
              COALESCE(p_traza, ''),
              1, p_ahora, p_ahora, NULL
            )
            ON CONFLICT (huella) DO UPDATE SET
              ocurrencias = public.errores_internos.ocurrencias + 1,
              ultima_vez = EXCLUDED.ultima_vez,
              traza = EXCLUDED.traza,
              resuelto_en = NULL
            RETURNING (xmax = 0) AS insertado
          )
          SELECT insertado
                 OR COALESCE((SELECT estaba_resuelto FROM previo), FALSE)
          INTO v_avisar
          FROM upsert;
          RETURN COALESCE(v_avisar, FALSE);
        END;
        $$;
        """
    )
    op.execute(
        f"REVOKE ALL ON FUNCTION cotizat_security.{FUNCION}({FIRMA}) FROM PUBLIC"
    )
    op.execute(
        f"GRANT EXECUTE ON FUNCTION cotizat_security.{FUNCION}({FIRMA}) TO {APP_ROLE}"
    )


def downgrade() -> None:
    if _postgres():
        op.execute(
            f"DROP FUNCTION IF EXISTS cotizat_security.{FUNCION}({FIRMA})"
        )
    op.drop_index("ix_errores_internos_pendientes", table_name=TABLE)
    op.drop_index("ix_errores_internos_ultima", table_name=TABLE)
    op.drop_table(TABLE)
