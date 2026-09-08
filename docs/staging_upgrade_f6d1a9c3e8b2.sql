-- CotizaT — actualización de d3e5f7a9c2b4 a f6d1a9c3e8b2
-- Uso real de presupuestos del cliente en el panel (solo lectura, superadmin).
-- Añade dos funciones SECURITY DEFINER que el panel del operador usa para leer
-- presupuestos y partidas de una organización sin abrir el aislamiento
-- multi-tenant. No crea tablas ni escribe en tenant.
-- Ejecutar una sola vez con el rol administrativo de Supabase/PostgreSQL.

BEGIN;

DO $$
DECLARE
  v_version text;
BEGIN
  SELECT version_num INTO v_version FROM public.alembic_version LIMIT 1;
  IF v_version IS DISTINCT FROM 'd3e5f7a9c2b4' THEN
    RAISE EXCEPTION
      'Se esperaba alembic_version d3e5f7a9c2b4 antes de f6d1a9c3e8b2; se encontró %',
      COALESCE(v_version, '<vacío>');
  END IF;
END
$$;

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
    AND COALESCE(
      pg_catalog.current_setting('cotizat.es_operador', true) = 'on',
      FALSE
    )
  ORDER BY p.fecha DESC, p.id DESC
$$;

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
    AND COALESCE(
      pg_catalog.current_setting('cotizat.es_operador', true) = 'on',
      FALSE
    )
  ORDER BY p.id, ca.orden, pi.orden, pi.id
$$;

ALTER FUNCTION cotizat_security.admin_presupuestos_cliente(integer) OWNER TO CURRENT_USER;
ALTER FUNCTION cotizat_security.admin_presupuesto_items_cliente(integer, integer) OWNER TO CURRENT_USER;
REVOKE ALL ON FUNCTION cotizat_security.admin_presupuestos_cliente(integer) FROM PUBLIC;
REVOKE ALL ON FUNCTION cotizat_security.admin_presupuesto_items_cliente(integer, integer) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION cotizat_security.admin_presupuestos_cliente(integer) TO cotizat_app;
GRANT EXECUTE ON FUNCTION cotizat_security.admin_presupuesto_items_cliente(integer, integer) TO cotizat_app;

UPDATE public.alembic_version
SET version_num = 'f6d1a9c3e8b2'
WHERE version_num = 'd3e5f7a9c2b4';

COMMIT;

-- Verificación:
-- SELECT version_num FROM public.alembic_version;  → f6d1a9c3e8b2
-- SELECT proname FROM pg_proc
-- WHERE pronamespace = 'cotizat_security'::regnamespace
--   AND proname IN ('admin_presupuestos_cliente', 'admin_presupuesto_items_cliente');
--   → dos funciones presentes, ambas SECURITY DEFINER
