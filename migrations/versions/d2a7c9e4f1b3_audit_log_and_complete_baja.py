"""Registro de auditoría inmutable + baja completa (E4-026 / E4-027).

Dos cosas, deliberadamente juntas porque ambas tocan la función de baja:

1. **``public.eventos_auditoria``** — el registro de quién hizo qué:
   cambios de negocio (precios, estados, documentos — E4-026) y sesiones y
   acciones sensibles (login, equipo, respaldo, baja — E4-027).

   - ``organizacion_id`` es *nullable*: los eventos de sesión (login/logout/
     cambio de clave) ocurren sin organización y solo los ve el operador.
   - **Inmutable por construcción**: el rol runtime recibe GRANT de SELECT e
     INSERT, **nunca** UPDATE ni DELETE. No existe política de UPDATE/DELETE.
   - Políticas: INSERT tenant con escritura (solo filas con organización);
     SELECT tenant (filas de la propia organización) o sesión de operador
     (todas, incluidas las globales).
   - Los eventos sin organización entran por
     ``cotizat_security.registrar_evento_global`` (SECURITY DEFINER) con
     **lista cerrada de acciones**: aunque el código llamara mal, la base no
     acepta una acción arbitraria como evento global.

2. **``cotizat_security.baja_organizacion`` actualizada** — corrige un bug
   latente: la función de ``a3d7e9c1b5f2`` no borraba ``compras_plan``
   (añadida después en ``e5f2a8d31b6c``, FK RESTRICT), así que **cualquier
   organización con una compra registrada no podía darse de baja** (el
   DELETE final fallaba por la clave foránea). La versión nueva borra
   ``compras_plan`` y ``eventos_auditoria`` antes de licencias/membresías.

La baja borra el rastro tenant de la organización (coherente con el
«borrado verificado» prometido en E3-023); la constancia de que la baja
ocurrió queda como evento global sin organización, visible solo para el
operador y sin datos del cliente más allá del correo del propietario que la
ejecutó.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d2a7c9e4f1b3"
down_revision: Union[str, Sequence[str], None] = "b6d9e4c2a8f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "eventos_auditoria"
APP_ROLE = "cotizat_app"

IS_OPERATOR = """
  COALESCE(
    pg_catalog.current_setting('cotizat.es_operador', true) = 'on',
    FALSE
  )
"""
TENANT_READ = "cotizat_security.tenant_access(organizacion_id, FALSE)"
TENANT_WRITE = "cotizat_security.tenant_access(organizacion_id, TRUE)"

#: Acciones globales admitidas. Debe coincidir con
#: ``app.services.auditoria.ACCIONES_GLOBALES``.
ACCIONES_GLOBALES_SQL = (
    "'sesion.login', 'sesion.logout', 'cuenta.clave_cambiada', "
    "'organizacion.baja'"
)

REGISTRAR_EVENTO_GLOBAL_SQL = f"""
CREATE OR REPLACE FUNCTION cotizat_security.registrar_evento_global(
  p_email text,
  p_accion text,
  p_ip_hash text DEFAULT '',
  p_detalle text DEFAULT '{{}}'
) RETURNS boolean LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
BEGIN
  IF p_accion IS NULL
     OR p_accion NOT IN ({ACCIONES_GLOBALES_SQL}) THEN
    RETURN FALSE;
  END IF;

  INSERT INTO public.eventos_auditoria (
    organizacion_id, actor_email, actor_rol, accion, entidad,
    detalle, ip_hash, created_at
  ) VALUES (
    NULL,
    LEFT(LOWER(COALESCE(p_email, '')), 254),
    '',
    p_accion,
    '',
    LEFT(COALESCE(NULLIF(p_detalle, ''), '{{}}'), 2000),
    LEFT(COALESCE(p_ip_hash, ''), 64),
    clock_timestamp()
  );
  RETURN TRUE;
END
$$
"""

_REGISTRAR_SIGNATURE = "registrar_evento_global(text, text, text, text)"

#: Cuerpo de la baja SIN las tablas nuevas — exactamente el de
#: ``a3d7e9c1b5f2`` — para poder restaurarlo en el downgrade.
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
    _BAJA_DELETES_BASE + _BAJA_DELETES_NUEVAS + _BAJA_DELETES_FINAL
)
BAJA_ANTERIOR_SQL = _baja_function_sql(_BAJA_DELETES_BASE + _BAJA_DELETES_FINAL)

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
            index=True,
        ),
        sa.Column(
            "actor_email", sa.String(length=254), nullable=False, server_default=""
        ),
        sa.Column(
            "actor_rol", sa.String(length=20), nullable=False, server_default=""
        ),
        sa.Column("accion", sa.String(length=60), nullable=False, index=True),
        sa.Column(
            "entidad", sa.String(length=40), nullable=False, server_default=""
        ),
        sa.Column("entidad_id", sa.Integer(), nullable=True),
        sa.Column("detalle", sa.Text(), nullable=False, server_default="{}"),
        sa.Column(
            "ip_hash", sa.String(length=64), nullable=False, server_default=""
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index(
        "ix_eventos_auditoria_org_fecha", TABLE, ["organizacion_id", "created_at"]
    )

    if not _postgres():
        # SQLite (escritorio y pruebas) no tiene RLS: el aislamiento y la
        # inmutabilidad los aporta la aplicación (el servicio solo inserta).
        return

    op.execute(f"REVOKE ALL ON TABLE public.{TABLE} FROM PUBLIC")
    op.execute(f"ALTER TABLE public.{TABLE} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE public.{TABLE} FORCE ROW LEVEL SECURITY")
    # GRANT sin UPDATE ni DELETE: la inmutabilidad no depende del código.
    op.execute(f"GRANT SELECT, INSERT ON TABLE public.{TABLE} TO {APP_ROLE}")
    op.execute(
        f"GRANT USAGE, SELECT ON SEQUENCE public.{TABLE}_id_seq TO {APP_ROLE}"
    )

    for nombre, accion, clausula in (
        (
            "cotizat_evento_select_tenant",
            "SELECT",
            f"USING (organizacion_id IS NOT NULL AND {TENANT_READ})",
        ),
        ("cotizat_evento_select_operator", "SELECT", f"USING ({IS_OPERATOR})"),
        (
            "cotizat_evento_insert_tenant",
            "INSERT",
            f"WITH CHECK (organizacion_id IS NOT NULL AND {TENANT_WRITE})",
        ),
    ):
        op.execute(f"DROP POLICY IF EXISTS {nombre} ON public.{TABLE}")
        op.execute(
            f"CREATE POLICY {nombre} ON public.{TABLE} "
            f"FOR {accion} TO {APP_ROLE} {clausula}"
        )

    op.execute(REGISTRAR_EVENTO_GLOBAL_SQL)
    op.execute(
        f"ALTER FUNCTION cotizat_security.{_REGISTRAR_SIGNATURE} OWNER TO CURRENT_USER"
    )
    op.execute(
        f"REVOKE ALL ON FUNCTION cotizat_security.{_REGISTRAR_SIGNATURE} FROM PUBLIC"
    )
    op.execute(
        f"GRANT EXECUTE ON FUNCTION cotizat_security.{_REGISTRAR_SIGNATURE}"
        f" TO {APP_ROLE}"
    )

    # Baja completa: incorpora compras_plan (bug latente) y eventos_auditoria.
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
        # Restaura la función de baja anterior (sin las tablas nuevas).
        op.execute(BAJA_ANTERIOR_SQL)
        op.execute(
            f"DROP FUNCTION IF EXISTS cotizat_security.{_REGISTRAR_SIGNATURE}"
        )
        for nombre in (
            "cotizat_evento_select_tenant",
            "cotizat_evento_select_operator",
            "cotizat_evento_insert_tenant",
        ):
            op.execute(f"DROP POLICY IF EXISTS {nombre} ON public.{TABLE}")
        op.execute(f"ALTER TABLE public.{TABLE} DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_eventos_auditoria_org_fecha", table_name=TABLE)
    op.drop_table(TABLE)
