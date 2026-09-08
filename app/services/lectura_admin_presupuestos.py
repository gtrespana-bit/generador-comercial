"""Funciones PostgreSQL para la lectura auditada de presupuestos en el panel.

La lectura del contenido comercial de una organización no puede ejecutarse como
una consulta ORM normal desde el panel de operador: las políticas RLS de las
tablas de tenant solo permiten a miembros de esa organización. Estas funciones
``SECURITY DEFINER`` son la ventana mínima de solo lectura para el superadmin.

La migración ``f6d1a9c3e8b2`` es la vía normal de instalación. Este módulo
conserva además el SQL y una verificación idempotente para que el arranque pueda
recuperar una base que recibió el despliegue web antes de que se aplicara esa
migración. La recuperación usa exclusivamente ``MIGRATION_DATABASE_URL`` (o
una conexión que ya tenga privilegios DDL), nunca el rol runtime de la app.
"""
from __future__ import annotations

from sqlalchemy import text

APP_ROLE = "cotizat_app"

IS_OPERATOR = """
  COALESCE(
    pg_catalog.current_setting('cotizat.es_operador', true) = 'on',
    FALSE
  )
"""

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

FUNCTION_SIGNATURES = (
    "admin_presupuestos_cliente(integer)",
    "admin_presupuesto_items_cliente(integer, integer)",
)


def funciones_lectura_admin_disponibles(connection) -> bool:
    """Indica si las dos funciones existen y el rol runtime puede ejecutarlas."""
    disponibles = connection.execute(text("""
        WITH requeridas(oid) AS (
          VALUES
            (pg_catalog.to_regprocedure(
              'cotizat_security.admin_presupuestos_cliente(integer)'
            )),
            (pg_catalog.to_regprocedure(
              'cotizat_security.admin_presupuesto_items_cliente(integer, integer)'
            ))
        )
        SELECT COUNT(*)
        FROM requeridas
        WHERE oid IS NOT NULL
          AND pg_catalog.has_function_privilege('cotizat_app', oid, 'EXECUTE')
    """)).scalar()
    return int(disponibles or 0) == len(FUNCTION_SIGNATURES)


def instalar_funciones_lectura_admin(connection) -> None:
    """Crea o repara la ventana de lectura y sus privilegios, idempotentemente.

    Debe invocarse únicamente con la conexión de migración, propiedad del
    esquema. No acepta datos de petición ni interpolación de valores externos.
    """
    connection.execute(text(PRESUPUESTOS_CLIENTE_FUNCTION_SQL))
    connection.execute(text(PRESUPUESTO_ITEMS_CLIENTE_FUNCTION_SQL))
    for signature in FUNCTION_SIGNATURES:
        connection.execute(text(
            f"ALTER FUNCTION cotizat_security.{signature} OWNER TO CURRENT_USER"
        ))
        connection.execute(text(
            f"REVOKE ALL ON FUNCTION cotizat_security.{signature} FROM PUBLIC"
        ))
        connection.execute(text(
            f"GRANT EXECUTE ON FUNCTION cotizat_security.{signature} TO {APP_ROLE}"
        ))
