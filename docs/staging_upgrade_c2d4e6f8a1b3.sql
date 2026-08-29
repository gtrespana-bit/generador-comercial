-- CotizaT — actualización de a1b8c2d4e6f0 a c2d4e6f8a1b3
-- Fase 2 del panel: notas internas de cliente, función de agregados de uso
-- y función de cobros del cliente (solo operador, SECURITY DEFINER).
-- Ejecutar una sola vez con el rol administrativo de Supabase/PostgreSQL.

BEGIN;

DO $$
DECLARE
  v_version text;
BEGIN
  SELECT version_num INTO v_version FROM public.alembic_version LIMIT 1;
  IF v_version IS DISTINCT FROM 'a1b8c2d4e6f0' THEN
    RAISE EXCEPTION
      'Se esperaba alembic_version a1b8c2d4e6f0 antes de c2d4e6f8a1b3; se encontró %',
      COALESCE(v_version, '<vacío>');
  END IF;
END
$$;

CREATE TABLE IF NOT EXISTS public.notas_operador (
    id SERIAL NOT NULL,
    organizacion_id INTEGER NOT NULL,
    contenido TEXT DEFAULT '' NOT NULL,
    autor_email VARCHAR(254) DEFAULT '' NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (id),
    CONSTRAINT fk_notas_operador_organizacion
      FOREIGN KEY (organizacion_id) REFERENCES public.organizaciones (id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS ix_notas_operador_org_fecha
  ON public.notas_operador (organizacion_id, created_at);

REVOKE ALL ON TABLE public.notas_operador FROM PUBLIC;
ALTER TABLE public.notas_operador ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notas_operador FORCE ROW LEVEL SECURITY;
GRANT SELECT, INSERT, UPDATE ON TABLE public.notas_operador TO cotizat_app;
GRANT USAGE, SELECT ON SEQUENCE public.notas_operador_id_seq TO cotizat_app;

DROP POLICY IF EXISTS cotizat_nota_operador_select ON public.notas_operador;
CREATE POLICY cotizat_nota_operador_select ON public.notas_operador
  FOR SELECT TO cotizat_app
  USING (
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
  );

DROP POLICY IF EXISTS cotizat_nota_operador_insert ON public.notas_operador;
CREATE POLICY cotizat_nota_operador_insert ON public.notas_operador
  FOR INSERT TO cotizat_app
  WITH CHECK (
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
  );

DROP POLICY IF EXISTS cotizat_nota_operador_update ON public.notas_operador;
CREATE POLICY cotizat_nota_operador_update ON public.notas_operador
  FOR UPDATE TO cotizat_app
  USING (
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
  )
  WITH CHECK (
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
  );

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
$$;

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
$$;

ALTER FUNCTION cotizat_security.admin_resumen_cliente(integer) OWNER TO CURRENT_USER;
ALTER FUNCTION cotizat_security.admin_cobros_cliente(integer) OWNER TO CURRENT_USER;
REVOKE ALL ON FUNCTION cotizat_security.admin_resumen_cliente(integer) FROM PUBLIC;
REVOKE ALL ON FUNCTION cotizat_security.admin_cobros_cliente(integer) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION cotizat_security.admin_resumen_cliente(integer) TO cotizat_app;
GRANT EXECUTE ON FUNCTION cotizat_security.admin_cobros_cliente(integer) TO cotizat_app;

UPDATE public.alembic_version
SET version_num = 'c2d4e6f8a1b3'
WHERE version_num = 'a1b8c2d4e6f0';

COMMIT;

-- Verificación:
-- SELECT version_num FROM public.alembic_version;  → c2d4e6f8a1b3
-- \d public.notas_operador
-- SELECT policyname, cmd FROM pg_policies WHERE tablename = 'notas_operador';
--   → cotizat_nota_operador_select / cotizat_nota_operador_insert / cotizat_nota_operador_update
-- SELECT proname FROM pg_proc
-- WHERE pronamespace = 'cotizat_security'::regnamespace
--   AND proname IN ('admin_resumen_cliente', 'admin_cobros_cliente');
--   → dos funciones presentes
