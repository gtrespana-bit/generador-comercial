"""Baja de organización con borrado verificado (E3-023).

Añade ``cotizat_security.baja_organizacion(p_organization_id)``: borra en una
sola transacción todos los datos de negocio, las licencias, las membresías y
la propia organización. Es SECURITY DEFINER porque la sesión del cliente no
puede borrar ``organizaciones`` (solo tiene política SELECT) y porque conviene
que el borrado sea atómico y no dependa de los permisos fila a fila de RLS.

Guardias dentro de la función (defensa en profundidad; la ruta ya las valida):

- el claim ``cotizat.organization_id`` de la sesión debe coincidir con la
  organización que se quiere borrar;
- ``cotizat_security.membership_role`` debe devolver ``propietario``.

Los archivos del almacenamiento privado NO se borran aquí (viven en Supabase
Storage): la aplicación los elimina por el proxy autorizado ANTES de invocar
esta función, para no dejar objetos huérfanos sin metadatos.

Como en ``b7c4a9e2d31f``: la función se reasigna al usuario que aplica la
migración (sesión administrativa), se revoca de PUBLIC y se concede solo a
``cotizat_app``. En SQLite (escritorio y pruebas) no aplica: la baja se
ejecuta por ORM dentro de la sesión autenticada.
"""
from typing import Sequence, Union

from alembic import op


revision: str = "a3d7e9c1b5f2"
down_revision: Union[str, Sequence[str], None] = "c2f6e8a1d934"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


#: Borrado total en orden hijo → padre (respetando las claves foráneas) con
#: doble guardia: claim de organización y rol de propietario de la sesión.
BAJA_FUNCTION_SQL = """
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
  DELETE FROM public.licencias
    WHERE organizacion_id = p_organization_id;
  DELETE FROM public.membresias
    WHERE organizacion_id = p_organization_id;
  DELETE FROM public.organizaciones
    WHERE id = p_organization_id;
END
$$
"""

_FUNCTION_SIGNATURE = "baja_organizacion(integer)"


def _postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    if not _postgres():
        # SQLite (escritorio y pruebas): la baja se ejecuta por ORM.
        return

    op.execute(BAJA_FUNCTION_SQL)
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
    if not _postgres():
        return

    op.execute(f"DROP FUNCTION IF EXISTS cotizat_security.{_FUNCTION_SIGNATURE}")
