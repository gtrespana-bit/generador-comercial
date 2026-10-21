"""Identidad de usuario en errores internos y amplitud de unidad de producto.

La identidad procede exclusivamente de la sesión validada y el error de
producción evidenció que ``producto_unidad`` también contiene variantes de
producto que superan los veinte caracteres.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "p3f7a1c9d2e4"
down_revision: Union[str, Sequence[str], None] = "o2e4a6c8b1d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLA = "errores_internos"
FUNCION = "registrar_error_interno"
FIRMA_NUEVA = "text, text, text, text, text, text, text, text, timestamp without time zone"
FIRMA_ANTERIOR = "text, text, text, text, text, text, timestamp without time zone"


def _postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def _crear_funcion_con_identidad() -> None:
    op.execute(f"DROP FUNCTION IF EXISTS cotizat_security.{FUNCION}({FIRMA_ANTERIOR})")
    op.execute(
        f"""
        CREATE OR REPLACE FUNCTION cotizat_security.{FUNCION}(
          p_huella text,
          p_metodo text,
          p_ruta text,
          p_tipo text,
          p_mensaje text,
          p_traza text,
          p_usuario_email text,
          p_usuario_nombre text,
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
              usuario_email, usuario_nombre,
              ocurrencias, primera_vez, ultima_vez, resuelto_en
            ) VALUES (
              p_huella,
              left(COALESCE(p_metodo, ''), 10),
              left(COALESCE(NULLIF(p_ruta, ''), '/'), 160),
              left(COALESCE(p_tipo, ''), 120),
              left(COALESCE(p_mensaje, ''), 300),
              COALESCE(p_traza, ''),
              left(COALESCE(p_usuario_email, ''), 254),
              left(COALESCE(p_usuario_nombre, ''), 200),
              1, p_ahora, p_ahora, NULL
            )
            ON CONFLICT (huella) DO UPDATE SET
              ocurrencias = public.errores_internos.ocurrencias + 1,
              ultima_vez = EXCLUDED.ultima_vez,
              traza = EXCLUDED.traza,
              usuario_email = EXCLUDED.usuario_email,
              usuario_nombre = EXCLUDED.usuario_nombre,
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
    op.execute(f"REVOKE ALL ON FUNCTION cotizat_security.{FUNCION}({FIRMA_NUEVA}) FROM PUBLIC")
    op.execute(
        f"GRANT EXECUTE ON FUNCTION cotizat_security.{FUNCION}({FIRMA_NUEVA}) "
        "TO cotizat_app"
    )


def _crear_funcion_anterior() -> None:
    op.execute(f"DROP FUNCTION IF EXISTS cotizat_security.{FUNCION}({FIRMA_NUEVA})")
    op.execute(
        f"""
        CREATE OR REPLACE FUNCTION cotizat_security.{FUNCION}(
          p_huella text, p_metodo text, p_ruta text, p_tipo text,
          p_mensaje text, p_traza text,
          p_ahora timestamp without time zone
        ) RETURNS boolean
        LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
        DECLARE v_avisar boolean;
        BEGIN
          WITH previo AS (
            SELECT resuelto_en IS NOT NULL AS estaba_resuelto
            FROM public.errores_internos WHERE huella = p_huella
          ), upsert AS (
            INSERT INTO public.errores_internos (
              huella, metodo, ruta, tipo, mensaje, traza,
              ocurrencias, primera_vez, ultima_vez, resuelto_en
            ) VALUES (
              p_huella, left(COALESCE(p_metodo, ''), 10),
              left(COALESCE(NULLIF(p_ruta, ''), '/'), 160),
              left(COALESCE(p_tipo, ''), 120), left(COALESCE(p_mensaje, ''), 300),
              COALESCE(p_traza, ''), 1, p_ahora, p_ahora, NULL
            )
            ON CONFLICT (huella) DO UPDATE SET
              ocurrencias = public.errores_internos.ocurrencias + 1,
              ultima_vez = EXCLUDED.ultima_vez,
              traza = EXCLUDED.traza, resuelto_en = NULL
            RETURNING (xmax = 0) AS insertado
          )
          SELECT insertado OR COALESCE((SELECT estaba_resuelto FROM previo), FALSE)
          INTO v_avisar FROM upsert;
          RETURN COALESCE(v_avisar, FALSE);
        END;
        $$;
        """
    )
    op.execute(f"REVOKE ALL ON FUNCTION cotizat_security.{FUNCION}({FIRMA_ANTERIOR}) FROM PUBLIC")
    op.execute(
        f"GRANT EXECUTE ON FUNCTION cotizat_security.{FUNCION}({FIRMA_ANTERIOR}) "
        "TO cotizat_app"
    )


def upgrade() -> None:
    op.add_column(
        TABLA,
        sa.Column("usuario_email", sa.String(254), nullable=False, server_default=""),
    )
    op.add_column(
        TABLA,
        sa.Column("usuario_nombre", sa.String(200), nullable=False, server_default=""),
    )
    if _postgres():
        op.alter_column(
            "presupuesto_items", "producto_unidad",
            existing_type=sa.String(length=20), type_=sa.String(length=120),
            existing_nullable=True,
        )
        _crear_funcion_con_identidad()


def downgrade() -> None:
    if _postgres():
        _crear_funcion_anterior()
        op.alter_column(
            "presupuesto_items", "producto_unidad",
            existing_type=sa.String(length=120), type_=sa.String(length=20),
            existing_nullable=True,
        )
    op.drop_column(TABLA, "usuario_nombre")
    op.drop_column(TABLA, "usuario_email")
