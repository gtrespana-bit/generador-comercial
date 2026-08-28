"""Telemetría interna de producto: ``public.eventos_producto`` (E5-012).

Tabla hermana de ``eventos_auditoria`` (misma migración de referencia:
``d2a7c9e4f1b3``) con un propósito distinto: medir cómo se usa el producto
(embudo registro → empresa → presupuesto → cobro, activación, retención y
uso de funciones) con un dato propio del servidor que complementa a GA4.

Diferencias frente a la auditoría:

- **Sin ``ip_hash``**: no hace falta para agregar, así que se minimiza.
- **SELECT solo de operador**: ninguna sesión de tenant lee telemetría;
  el panel de analítica (``/admin/analitica``) es la única consumidora.
- **INSERT de tenant** (eventos de organización, con escritura) **y de
  operador** (activación de licencias desde el panel y webhook de Stripe).
- Los eventos **sin organización** (``cuenta.registrada``) entran por la
  función SECURITY DEFINER ``cotizat_security.registrar_evento_producto_global``
  con lista cerrada de acciones (defensa en profundidad, como la auditoría).

La baja de la organización borra también sus filas de telemetría:
coherente con el «borrado verificado» de E3-023 y con el tratamiento que
ya recibía ``eventos_auditoria``.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e3a5c7d9b1f4"
down_revision: Union[str, Sequence[str], None] = "f1b2c3d4e5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "eventos_producto"
APP_ROLE = "cotizat_app"

IS_OPERATOR = """
  COALESCE(
    pg_catalog.current_setting('cotizat.es_operador', true) = 'on',
    FALSE
  )
"""
TENANT_WRITE = "cotizat_security.tenant_access(organizacion_id, TRUE)"

#: Acciones globales admitidas. Debe coincidir con
#: ``app.services.telemetria.ACCIONES_GLOBALES``.
ACCIONES_GLOBALES_SQL = "'cuenta.registrada'"

REGISTRAR_GLOBAL_SQL = f"""
CREATE OR REPLACE FUNCTION cotizat_security.registrar_evento_producto_global(
  p_email text,
  p_accion text,
  p_detalle text DEFAULT '{{}}'
) RETURNS boolean LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
BEGIN
  IF p_accion IS NULL
     OR p_accion NOT IN ({ACCIONES_GLOBALES_SQL}) THEN
    RETURN FALSE;
  END IF;

  INSERT INTO public.eventos_producto (
    organizacion_id, actor_email, accion, detalle, created_at
  ) VALUES (
    NULL,
    LEFT(LOWER(COALESCE(p_email, '')), 254),
    p_accion,
    LEFT(COALESCE(NULLIF(p_detalle, ''), '{{}}'), 2000),
    clock_timestamp()
  );
  RETURN TRUE;
END
$$
"""

_REGISTRAR_SIGNATURE = (
    "registrar_evento_producto_global(text, text, text)"
)

# ── Función de baja: la versión vigente (d2a7c9e4f1b3) + eventos_producto ──

_BAJA_DELETES_BASE = """
  DELETE FROM public.enlaces_propuesta
    WHERE organizacion_id = p_organization_id;
  DELETE FROM public.pagos
    WHERE organizacion_id = p_organization_id;
  DELETE FROM public.cambio_alcance_items
    WHERE organizacion_id = p_organization_id;
  DELETE FROM public.cambios_alcance
    WHERE organizacion_id = p_organization_id;
  DELETE FROM public.proyectos
    WHERE organizacion_id = p_organization_id;
  DELETE FROM public.notas_seguimiento
    WHERE organizacion_id = p_organization_id;
  DELETE FROM public.presupuesto_anexos
    WHERE organizacion_id = p_organization_id;
  DELETE FROM public.borradores_presupuesto
    WHERE organizacion_id = p_organization_id;
  DELETE FROM public.presupuesto_versiones
    WHERE organizacion_id = p_organization_id;
  DELETE FROM public.descomposicion_filas
    WHERE organizacion_id = p_organization_id;
  DELETE FROM public.descomposiciones_partida
    WHERE organizacion_id = p_organization_id;
  DELETE FROM public.mediciones
    WHERE organizacion_id = p_organization_id;
  DELETE FROM public.presupuesto_item_productos
    WHERE organizacion_id = p_organization_id;
  DELETE FROM public.presupuesto_items
    WHERE organizacion_id = p_organization_id;
  DELETE FROM public.capitulos
    WHERE organizacion_id = p_organization_id;
  DELETE FROM public.presupuestos
    WHERE organizacion_id = p_organization_id;
  DELETE FROM public.factura_items
    WHERE organizacion_id = p_organization_id;
  DELETE FROM public.factura_capitulos
    WHERE organizacion_id = p_organization_id;
  DELETE FROM public.facturas
    WHERE organizacion_id = p_organization_id;
  DELETE FROM public.clientes
    WHERE organizacion_id = p_organization_id;
  DELETE FROM public.partidas
    WHERE organizacion_id = p_organization_id;
  DELETE FROM public.productos
    WHERE organizacion_id = p_organization_id;
  DELETE FROM public.recursos
    WHERE organizacion_id = p_organization_id;
  DELETE FROM public.plantillas
    WHERE organizacion_id = p_organization_id;
  DELETE FROM public.recetas_estancia
    WHERE organizacion_id = p_organization_id;
  DELETE FROM public.categorias_partidas
    WHERE organizacion_id = p_organization_id;
  DELETE FROM public.archivos_almacenados
    WHERE organizacion_id = p_organization_id;
  DELETE FROM public.invitaciones_organizacion
    WHERE organizacion_id = p_organization_id;
  DELETE FROM public.configuracion
    WHERE organizacion_id = p_organization_id;
"""

_BAJA_DELETES_NUEVAS = """
  DELETE FROM public.compras_plan
    WHERE organizacion_id = p_organization_id;
  DELETE FROM public.eventos_auditoria
    WHERE organizacion_id = p_organization_id;
"""

_BAJA_DELETES_FINAL = """
  DELETE FROM public.licencias
    WHERE organizacion_id = p_organization_id;
  DELETE FROM public.membresias
    WHERE organizacion_id = p_organization_id;
  DELETE FROM public.organizaciones
    WHERE id = p_organization_id;
"""


def _baja_function_sql(deletes: str) -> str:
    return f"""
CREATE OR REPLACE FUNCTION cotizat_security.baja_organizacion(
  p_organization_id integer
) RETURNS void LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
DECLARE
  v_role text;
BEGIN
  IF COALESCE(
    pg_catalog.current_setting('cotizat.organization_id', true), ''
  ) <> p_organization_id::text THEN
    RAISE EXCEPTION
      'La baja no coincide con la organización de la sesión.'
      USING ERRCODE = '42501';
  END IF;

  v_role := cotizat_security.membership_role(p_organization_id);
  IF v_role IS DISTINCT FROM 'propietario' THEN
    RAISE EXCEPTION
      'Solo el propietario puede dar de baja la organización.'
      USING ERRCODE = '42501';
  END IF;
{deletes}
END
$$
"""


BAJA_ACTUALIZADA_SQL = _baja_function_sql(
    _BAJA_DELETES_BASE
    + _BAJA_DELETES_NUEVAS
    + "  DELETE FROM public.eventos_producto"
    " WHERE organizacion_id = p_organization_id;\n"
    + _BAJA_DELETES_FINAL
)
BAJA_ANTERIOR_SQL = _baja_function_sql(
    _BAJA_DELETES_BASE + _BAJA_DELETES_NUEVAS + _BAJA_DELETES_FINAL
)

_BAJA_SIGNATURE = "baja_organizacion(integer)"


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
            nullable=True,
        ),
        sa.Column(
            "actor_email", sa.String(length=254), nullable=False, server_default=""
        ),
        # El índice de `accion` se crea explícito más abajo: `index=True`
        # aquí duplicaría el índice en SQLite (create_table lo materializa).
        sa.Column("accion", sa.String(length=60), nullable=False),
        sa.Column("detalle", sa.Text(), nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index(
        "ix_eventos_producto_org_fecha", TABLE, ["organizacion_id", "created_at"]
    )
    op.create_index("ix_eventos_producto_fecha", TABLE, ["created_at"])
    op.create_index("ix_eventos_producto_accion", TABLE, ["accion"])

    if not _postgres():
        # SQLite (escritorio y pruebas) no tiene RLS: el aislamiento y la
        # inmutabilidad los aporta la aplicación (el servicio solo inserta).
        return

    op.execute(f"REVOKE ALL ON TABLE public.{TABLE} FROM PUBLIC")
    op.execute(f"ALTER TABLE public.{TABLE} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE public.{TABLE} FORCE ROW LEVEL SECURITY")
    # GRANT sin UPDATE ni DELETE: inmutabilidad por construcción.
    op.execute(f"GRANT SELECT, INSERT ON TABLE public.{TABLE} TO {APP_ROLE}")
    op.execute(
        f"GRANT USAGE, SELECT ON SEQUENCE public.{TABLE}_id_seq TO {APP_ROLE}"
    )

    for nombre, accion, clausula in (
        # Lectura: solo el operador (el panel de analítica). Ningún tenant
        # consulta telemetría.
        ("cotizat_ep_select_operator", "SELECT", f"USING ({IS_OPERATOR})"),
        # Escritura de la propia organización (eventos que nacen en la
        # petición del cliente) y de operador (activaciones, webhook).
        (
            "cotizat_ep_insert_tenant",
            "INSERT",
            f"WITH CHECK (organizacion_id IS NOT NULL AND {TENANT_WRITE})",
        ),
        ("cotizat_ep_insert_operator", "INSERT", f"WITH CHECK ({IS_OPERATOR})"),
    ):
        op.execute(f"DROP POLICY IF EXISTS {nombre} ON public.{TABLE}")
        op.execute(
            f"CREATE POLICY {nombre} ON public.{TABLE} "
            f"FOR {accion} TO {APP_ROLE} {clausula}"
        )

    op.execute(REGISTRAR_GLOBAL_SQL)
    op.execute(
        f"ALTER FUNCTION cotizat_security.{_REGISTRAR_SIGNATURE}"
        " OWNER TO CURRENT_USER"
    )
    op.execute(
        f"REVOKE ALL ON FUNCTION cotizat_security.{_REGISTRAR_SIGNATURE}"
        " FROM PUBLIC"
    )
    op.execute(
        f"GRANT EXECUTE ON FUNCTION cotizat_security.{_REGISTRAR_SIGNATURE}"
        f" TO {APP_ROLE}"
    )

    # Baja completa: incorpora eventos_producto al borrado verificado.
    op.execute(BAJA_ACTUALIZADA_SQL)
    op.execute(
        f"ALTER FUNCTION cotizat_security.{_BAJA_SIGNATURE} OWNER TO CURRENT_USER"
    )
    op.execute(
        f"REVOKE ALL ON FUNCTION cotizat_security.{_BAJA_SIGNATURE} FROM PUBLIC"
    )
    op.execute(
        f"GRANT EXECUTE ON FUNCTION cotizat_security.{_BAJA_SIGNATURE}"
        f" TO {APP_ROLE}"
    )


def downgrade() -> None:
    if _postgres():
        # Restaura la función de baja anterior (sin eventos_producto).
        op.execute(BAJA_ANTERIOR_SQL)
        op.execute(
            f"DROP FUNCTION IF EXISTS cotizat_security.{_REGISTRAR_SIGNATURE}"
        )
        for nombre in (
            "cotizat_ep_select_operator",
            "cotizat_ep_insert_tenant",
            "cotizat_ep_insert_operator",
        ):
            op.execute(f"DROP POLICY IF EXISTS {nombre} ON public.{TABLE}")
        op.execute(f"ALTER TABLE public.{TABLE} DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_eventos_producto_fecha", table_name=TABLE)
    op.drop_index("ix_eventos_producto_org_fecha", table_name=TABLE)
    op.drop_index("ix_eventos_producto_accion", table_name=TABLE)
    op.drop_table(TABLE)
