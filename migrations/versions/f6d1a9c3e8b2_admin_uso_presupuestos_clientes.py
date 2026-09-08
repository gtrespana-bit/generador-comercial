"""Uso real de presupuestos de un cliente para el panel (solo lectura).

El titular necesita ver qué presupuestos genera cada cliente y qué precios
modifica, pero **sin abrir el aislamiento multi-tenant**: el contenido de
tenant sigue bajo RLS y las sesiones de cliente no obtienen nada. Este
merge de migración añade dos funciones ``SECURITY DEFINER`` que el panel
(sesión de operador) usa para leer:

- ``cotizat_security.admin_presupuestos_cliente(p_organization_id)``:
  cabeceras de los presupuestos de una organización (nº, fecha, título,
  cliente final, estado, moneda, total, nº de partidas, alta/actualización).
- ``cotizat_security.admin_presupuesto_items_cliente(p_organization_id,
  p_presupuesto_id DEFAULT 0)``: partidas con cantidad, precio, producto,
  costes y el precio del catálogo al lado (para detectar modificaciones).

Ambas llevan la guardia ``cotizat.es_operador`` como las funciones de la
Fase 2 y solo se conceden a ``cotizat_app``. No hay tablas nuevas ni
escrituras: el operador nunca modifica ni elimina datos de tenant.

Se cuelga de la cabeza vigente ``d3e5f7a9c2b4`` (el grafo ya era lineal;
``f2a3b4c5d6e7`` sigue en la cadena por ``a3b4c5d6e7f8`` → ``b4c5d6e7f8a9``).
"""
from typing import Sequence, Union

from alembic import op

revision: str = "f6d1a9c3e8b2"
down_revision: Union[str, Sequence[str], None] = "d3e5f7a9c2b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

APP_ROLE = "cotizat_app"

IS_OPERATOR = """
  COALESCE(
    pg_catalog.current_setting('cotizat.es_operador', true) = 'on',
    FALSE
  )
"""

#: Cabeceras de los presupuestos de un cliente (nunca contenido de partidas).
PRESUPUESTOS_CLIENTE_FUNCTION_SQL = f"""
CREATE OR REPLACE FUNCTION cotizat_security.admin_presupuestos_cliente(
  p_organization_id integer
) RETURNS TABLE(
  id integer,
  numero text,
  year integer,
  fecha date,
  cliente_nombre text,
  titulo text,
  estado text,
  moneda text,
  moneda_base text,
  tipo_cambio numeric,
  total_calculado numeric,
  es_demo boolean,
  n_items integer,
  created_at timestamp,
  updated_at timestamp
) LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
  SELECT
    p.id::integer,
    p.numero::text,
    p.year::integer,
    p.fecha::date,
    COALESCE(c.nombre, '')::text,
    COALESCE(p.titulo, '')::text,
    p.estado::text,
    p.moneda::text,
    COALESCE(p.moneda_base, 'USD')::text,
    p.tipo_cambio::numeric,
    p.total_calculado::numeric,
    COALESCE(p.es_demo, FALSE)::boolean,
    (
      SELECT COUNT(*)::integer
      FROM public.capitulos ca
      JOIN public.presupuesto_items pi ON pi.capitulo_id = ca.id
      WHERE ca.presupuesto_id = p.id
    ),
    p.created_at::timestamp,
    p.updated_at::timestamp
  FROM public.presupuestos p
  LEFT JOIN public.clientes c ON c.id = p.client_id
  WHERE p.organizacion_id = p_organization_id
    AND {IS_OPERATOR}
  ORDER BY p.fecha DESC, p.id DESC
$$
"""

#: Partidas de los presupuestos del cliente, con el precio del catálogo al
#: lado. ``p_presupuesto_id`` = 0 devuelve todas (ficha); un id concreto
#: devuelve solo ese presupuesto (detalle). La comparación de moneda y la
#: clasificación (modificado / ajuste) se hace en el servicio, no aquí, para
#: que SQLite y PostgreSQL apliquen exactamente las mismas reglas.
PRESUPUESTO_ITEMS_CLIENTE_FUNCTION_SQL = f"""
CREATE OR REPLACE FUNCTION cotizat_security.admin_presupuesto_items_cliente(
  p_organization_id integer,
  p_presupuesto_id integer DEFAULT 0
) RETURNS TABLE(
  item_id integer,
  presupuesto_id integer,
  presupuesto_numero text,
  presupuesto_fecha date,
  presupuesto_estado text,
  presupuesto_actualizado timestamp,
  presupuesto_es_demo boolean,
  capitulo text,
  capitulo_orden integer,
  item_orden integer,
  nombre text,
  unidad text,
  cantidad numeric,
  precio_unitario numeric,
  importe numeric,
  moneda text,
  moneda_base text,
  tipo_cambio numeric,
  producto_nombre text,
  producto_precio numeric,
  coste_materiales numeric,
  coste_mano_obra numeric,
  coste_complementarios numeric,
  coste_otros numeric,
  producto_coste numeric,
  margen_pct numeric,
  partida_catalogo_id integer,
  catalogo_nombre text,
  catalogo_precio numeric,
  codigo_externo text,
  tipo_partida text,
  seleccionada boolean
) LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
  SELECT
    pi.id::integer,
    p.id::integer,
    p.numero::text,
    p.fecha::date,
    p.estado::text,
    COALESCE(p.updated_at, p.created_at)::timestamp,
    COALESCE(p.es_demo, FALSE)::boolean,
    ca.nombre::text,
    ca.orden::integer,
    pi.orden::integer,
    COALESCE(pi.nombre, '')::text,
    COALESCE(pi.unidad, 'ud')::text,
    COALESCE(
      (SELECT SUM(m.cantidad) FROM public.mediciones m WHERE m.partida_id = pi.id),
      pi.cantidad, 0
    )::numeric,
    COALESCE(pi.precio_unitario, 0)::numeric,
    (
      COALESCE(
        (SELECT SUM(m.cantidad) FROM public.mediciones m WHERE m.partida_id = pi.id),
        pi.cantidad, 0
      ) * COALESCE(pi.precio_unitario, 0)
    )::numeric,
    COALESCE(pi.moneda, p.moneda, 'USD')::text,
    COALESCE(p.moneda_base, 'USD')::text,
    p.tipo_cambio::numeric,
    COALESCE(pi.producto_nombre, '')::text,
    pi.producto_precio::numeric,
    COALESCE(pi.coste_materiales, 0)::numeric,
    COALESCE(pi.coste_mano_obra, 0)::numeric,
    COALESCE(pi.coste_complementarios, 0)::numeric,
    COALESCE(pi.coste_otros, 0)::numeric,
    pi.producto_coste::numeric,
    COALESCE(pi.margen_pct, 0)::numeric,
    pi.partida_catalogo_id::integer,
    COALESCE(cat.nombre, '')::text,
    cat.precio_unitario::numeric,
    COALESCE(pi.codigo_externo, '')::text,
    COALESCE(pi.tipo_partida, 'included')::text,
    COALESCE(pi.seleccionada, FALSE)::boolean
  FROM public.presupuesto_items pi
  JOIN public.capitulos ca ON ca.id = pi.capitulo_id
  JOIN public.presupuestos p ON p.id = ca.presupuesto_id
  LEFT JOIN public.partidas cat
    ON cat.id = pi.partida_catalogo_id
    AND cat.organizacion_id = p.organizacion_id
  WHERE p.organizacion_id = p_organization_id
    AND (p_presupuesto_id = 0 OR p.id = p_presupuesto_id)
    AND {IS_OPERATOR}
  ORDER BY p.id, ca.orden, pi.orden, pi.id
$$
"""

_FUNCTION_SIGNATURES = (
    "admin_presupuestos_cliente(integer)",
    "admin_presupuesto_items_cliente(integer, integer)",
)


def _postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    if not _postgres():
        # SQLite (escritorio y pruebas) no tiene RLS: la lectura va directa
        # desde el servicio, siempre bajo sesión de operador.
        return

    op.execute(PRESUPUESTOS_CLIENTE_FUNCTION_SQL)
    op.execute(PRESUPUESTO_ITEMS_CLIENTE_FUNCTION_SQL)
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
