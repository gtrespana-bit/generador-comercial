-- Cotizat / Supabase SQL Editor
-- Migracion e7b3c1d5a204; revision previa obligatoria: c5d6e7f8a9b0
-- Permisos y politicas RLS de precios_recursos_mercado e historial_precios_recursos.
-- Sin esto, /presupuestos/nuevo responde 500 (permission denied -> transaccion abortada).
BEGIN;
DO $$ BEGIN
 IF NOT EXISTS (SELECT 1 FROM public.alembic_version WHERE version_num = 'c5d6e7f8a9b0') THEN
  RAISE EXCEPTION 'Revision previa incorrecta: se esperaba c5d6e7f8a9b0';
 END IF;
END $$;
REVOKE ALL ON TABLE public.precios_recursos_mercado FROM PUBLIC;
ALTER TABLE public.precios_recursos_mercado ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.precios_recursos_mercado FORCE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.historial_precios_recursos FROM PUBLIC;
ALTER TABLE public.historial_precios_recursos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.historial_precios_recursos FORCE ROW LEVEL SECURITY;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.precios_recursos_mercado TO cotizat_app;
GRANT SELECT, INSERT ON TABLE public.historial_precios_recursos TO cotizat_app;
DO $$ DECLARE secuencia text; BEGIN secuencia := pg_get_serial_sequence('public.precios_recursos_mercado', 'id'); IF secuencia IS NOT NULL THEN EXECUTE format('GRANT USAGE, SELECT ON SEQUENCE %s TO cotizat_app', secuencia); END IF; END $$;
DO $$ DECLARE secuencia text; BEGIN secuencia := pg_get_serial_sequence('public.historial_precios_recursos', 'id'); IF secuencia IS NOT NULL THEN EXECUTE format('GRANT USAGE, SELECT ON SEQUENCE %s TO cotizat_app', secuencia); END IF; END $$;
DROP POLICY IF EXISTS cotizat_precio_mercado_select ON public.precios_recursos_mercado;
CREATE POLICY cotizat_precio_mercado_select ON public.precios_recursos_mercado FOR SELECT TO cotizat_app USING (organizacion_id IS NULL OR cotizat_security.tenant_access(organizacion_id, FALSE) OR COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE));
DROP POLICY IF EXISTS cotizat_precio_mercado_insert ON public.precios_recursos_mercado;
CREATE POLICY cotizat_precio_mercado_insert ON public.precios_recursos_mercado FOR INSERT TO cotizat_app WITH CHECK ((organizacion_id IS NOT NULL AND cotizat_security.tenant_access(organizacion_id, TRUE)) OR (organizacion_id IS NULL AND COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)));
DROP POLICY IF EXISTS cotizat_precio_mercado_update ON public.precios_recursos_mercado;
CREATE POLICY cotizat_precio_mercado_update ON public.precios_recursos_mercado FOR UPDATE TO cotizat_app USING ((organizacion_id IS NOT NULL AND cotizat_security.tenant_access(organizacion_id, TRUE)) OR (organizacion_id IS NULL AND COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE))) WITH CHECK ((organizacion_id IS NOT NULL AND cotizat_security.tenant_access(organizacion_id, TRUE)) OR (organizacion_id IS NULL AND COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)));
DROP POLICY IF EXISTS cotizat_precio_mercado_delete ON public.precios_recursos_mercado;
CREATE POLICY cotizat_precio_mercado_delete ON public.precios_recursos_mercado FOR DELETE TO cotizat_app USING ((organizacion_id IS NOT NULL AND cotizat_security.tenant_access(organizacion_id, TRUE)) OR (organizacion_id IS NULL AND COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)));
DROP POLICY IF EXISTS cotizat_historial_precio_select ON public.historial_precios_recursos;
CREATE POLICY cotizat_historial_precio_select ON public.historial_precios_recursos FOR SELECT TO cotizat_app USING (EXISTS (SELECT 1 FROM public.precios_recursos_mercado AS p WHERE p.id = precio_mercado_id AND (p.organizacion_id IS NULL OR cotizat_security.tenant_access(p.organizacion_id, FALSE) OR COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE))));
DROP POLICY IF EXISTS cotizat_historial_precio_insert ON public.historial_precios_recursos;
CREATE POLICY cotizat_historial_precio_insert ON public.historial_precios_recursos FOR INSERT TO cotizat_app WITH CHECK (EXISTS (SELECT 1 FROM public.precios_recursos_mercado AS p WHERE p.id = precio_mercado_id AND ((p.organizacion_id IS NOT NULL AND cotizat_security.tenant_access(p.organizacion_id, TRUE)) OR (p.organizacion_id IS NULL AND COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)))));
UPDATE public.alembic_version SET version_num = 'e7b3c1d5a204' WHERE version_num = 'c5d6e7f8a9b0';
COMMIT;
