"""Fase 2 del panel profesional: ficha de cliente, cobros y notas internas.

Añade la información que el operador necesita para **gestionar** el negocio
(cliente, cobros, renovaciones) sin abrir el aislamiento multi-tenant:

- ``public.notas_operador``: notas internas del panel sobre una organización.
  Es una tabla del **titular** (no de tenant), protegida con RLS de operador y
  sin DELETE: se conserva el historial de gestión.
- ``cotizat_security.admin_resumen_cliente(p_organization_id)``: agregados de
  uso del cliente (clientes, presupuestos, facturas, pagos, totales y último
  acceso). SECURITY DEFINER con guardia ``es_operador``; las sesiones de
  cliente no obtienen nada.
- ``cotizat_security.admin_cobros_cliente(p_organization_id)``: facturas y
  pagos del cliente para el centro de cobros, también solo operador.

Nunca se desactiva el aislamiento: el operador accede a datos de negocio de un
cliente exclusivamente a través de estas funciones guardadas y de las tablas
de licencias/compras del titular.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c2d4e6f8a1b3"
down_revision: Union[str, Sequence[str], None] = "a1b8c2d4e6f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "notas_operador"
APP_ROLE = "cotizat_app"

IS_OPERATOR = """
  COALESCE(
    pg_catalog.current_setting('cotizat.es_operador', true) = 'on',
    FALSE
  )
"""

#: Agregados de uso de un cliente para la ficha del panel. La función solo
#: devuelve cifras (no contenido de presupuestos) y exige marca de operador.
RESUMEN_CLIENTE_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION cotizat_security.admin_resumen_cliente(
  p_organization_id integer
) RETURNS TABLE(
  clientes integer,
  presupuestos integer,
  facturas integer,
  pagos integer,
  total_presupuestado numeric,
  total_cobrado numeric,
  ultimo_acceso timestamp
) LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
  SELECT
    (SELECT COUNT(*) FROM public.clientes
      WHERE organizacion_id = p_organization_id)::integer,
    (SELECT COUNT(*) FROM public.presupuestos
      WHERE organizacion_id = p_organization_id)::integer,
    (SELECT COUNT(*) FROM public.facturas
      WHERE organizacion_id = p_organization_id)::integer,
    (SELECT COUNT(*) FROM public.pagos
      WHERE organizacion_id = p_organization_id)::integer,
    COALESCE((SELECT SUM(p.total_calculado) FROM public.presupuestos p
      WHERE p.organizacion_id = p_organization_id
        AND p.total_calculado > 0), 0)::numeric,
    COALESCE((SELECT SUM(pago.importe) FROM public.pagos pago
      WHERE pago.organizacion_id = p_organization_id
        AND pago.estado = 'confirmado'), 0)::numeric,
    (SELECT MAX(u.ultimo_acceso_at) FROM public.usuarios u
      JOIN public.membresias m ON m.usuario_id = u.id
      WHERE m.organizacion_id = p_organization_id)
  WHERE COALESCE(
    pg_catalog.current_setting('cotizat.es_operador', true) = 'on',
    FALSE
  )
$$
"""

#: Facturas y pagos del cliente para el centro de cobros. Existe una sola
#: función porque el objetivo es la misma lista de movimientos; la columna
#: ``tipo`` distingue factura de pago.
#:
#: ``facturas`` no guarda ``total`` como columna: el total se deriva de sus
#: ``factura_items`` (cantidad × precio_unitario) más impuesto y descuento.
#: Por eso el SELECT lo calcula en SQL, igual que la propiedad Python
#: ``Factura.total``.
COBROS_CLIENTE_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION cotizat_security.admin_cobros_cliente(
  p_organization_id integer
) RETURNS TABLE(
  id integer,
  tipo text,
  numero text,
  fecha date,
  importe numeric,
  moneda text,
  estado text,
  descripcion text
) LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
  SELECT
    f.id::integer,
    'factura'::text,
    f.numero::text,
    f.fecha::date,
    (
      (COALESCE(sub.subtotal, 0) * (1 - COALESCE(f.descuento_pct, 0) / 100.0))
      * (1 + COALESCE(f.impuesto_pct, 0) / 100.0)
    )::numeric,
    f.moneda::text,
    f.estado::text,
    COALESCE(f.titulo, '')::text
  FROM public.facturas f
  LEFT JOIN (
    SELECT fc.factura_id, SUM(fi.cantidad * fi.precio_unitario) AS subtotal
    FROM public.factura_capitulos fc
    JOIN public.factura_items fi ON fi.capitulo_id = fc.id
    GROUP BY fc.factura_id
  ) sub ON sub.factura_id = f.id
  WHERE f.organizacion_id = p_organization_id
    AND COALESCE(
      pg_catalog.current_setting('cotizat.es_operador', true) = 'on',
      FALSE
    )
  UNION ALL
  SELECT
    p.id::integer,
    'pago'::text,
    COALESCE(NULLIF(p.referencia, ''), 'pago-' || p.id::text)::text,
    p.fecha::date,
    COALESCE(p.importe, 0)::numeric,
    p.moneda::text,
    p.estado::text,
    COALESCE(p.notas, '')::text
  FROM public.pagos p
  WHERE p.organizacion_id = p_organization_id
    AND COALESCE(
      pg_catalog.current_setting('cotizat.es_operador', true) = 'on',
      FALSE
    )
  ORDER BY fecha DESC, id DESC
$$
"""

_FUNCTION_SIGNATURES = (
    "admin_resumen_cliente(integer)",
    "admin_cobros_cliente(integer)",
)


def _postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "organizacion_id",
            sa.Integer(),
            sa.ForeignKey("organizaciones.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("contenido", sa.Text(), nullable=False, server_default=""),
        sa.Column("autor_email", sa.String(length=254), nullable=False, server_default=""),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "ix_notas_operador_org_fecha", TABLE, ["organizacion_id", "created_at"]
    )

    if not _postgres():
        # SQLite (escritorio y pruebas) no tiene RLS; el aislamiento lo aporta
        # la aplicación (siempre una sesión de operador).
        return

    # ------------------------------------------------------------------
    # notas_operador: RLS de operador, sin DELETE (el historial se conserva)
    # ------------------------------------------------------------------
    op.execute(f"REVOKE ALL ON TABLE public.{TABLE} FROM PUBLIC")
    op.execute(f"ALTER TABLE public.{TABLE} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE public.{TABLE} FORCE ROW LEVEL SECURITY")
    op.execute(
        f"GRANT SELECT, INSERT, UPDATE ON TABLE public.{TABLE} TO {APP_ROLE}"
    )
    op.execute(f"GRANT USAGE, SELECT ON SEQUENCE public.{TABLE}_id_seq TO {APP_ROLE}")

    for nombre, accion, clausula in (
        ("cotizat_nota_operador_select", "SELECT", f"USING ({IS_OPERATOR})"),
        ("cotizat_nota_operador_insert", "INSERT", f"WITH CHECK ({IS_OPERATOR})"),
        (
            "cotizat_nota_operador_update",
            "UPDATE",
            f"USING ({IS_OPERATOR}) WITH CHECK ({IS_OPERATOR})",
        ),
    ):
        op.execute(f"DROP POLICY IF EXISTS {nombre} ON public.{TABLE}")
        op.execute(
            f"CREATE POLICY {nombre} ON public.{TABLE} "
            f"FOR {accion} TO {APP_ROLE} {clausula}"
        )

    # ------------------------------------------------------------------
    # Funciones SECURITY DEFINER para el panel (agregados y cobros del cliente)
    # ------------------------------------------------------------------
    op.execute(RESUMEN_CLIENTE_FUNCTION_SQL)
    op.execute(COBROS_CLIENTE_FUNCTION_SQL)
    for signature in _FUNCTION_SIGNATURES:
        op.execute(
            f"ALTER FUNCTION cotizat_security.{signature} OWNER TO CURRENT_USER"
        )
        op.execute(
            f"REVOKE ALL ON FUNCTION cotizat_security.{signature} FROM PUBLIC"
        )
        op.execute(
            f"GRANT EXECUTE ON FUNCTION cotizat_security.{signature}"
            f" TO {APP_ROLE}"
        )


def downgrade() -> None:
    if _postgres():
        for signature in _FUNCTION_SIGNATURES:
            op.execute(
                f"DROP FUNCTION IF EXISTS cotizat_security.{signature}"
            )
        for nombre in (
            "cotizat_nota_operador_select",
            "cotizat_nota_operador_insert",
            "cotizat_nota_operador_update",
        ):
            op.execute(f"DROP POLICY IF EXISTS {nombre} ON public.{TABLE}")
        op.execute(f"ALTER TABLE public.{TABLE} DISABLE ROW LEVEL SECURITY")

    op.drop_index("ix_notas_operador_org_fecha", table_name=TABLE)
    op.drop_table(TABLE)
