-- CotizaT — actualización de f1b2c3d4e5a6 a e3a5c7d9b1f4
-- Telemetría interna de producto (E5-012): tabla `eventos_producto`,
-- políticas RLS, función global del registro y baja actualizada.
-- Ejecutar una sola vez con el rol administrativo de Supabase/PostgreSQL.

BEGIN;

DO $$
DECLARE
  v_version text;
BEGIN
  SELECT version_num INTO v_version FROM public.alembic_version LIMIT 1;
  IF v_version IS DISTINCT FROM 'f1b2c3d4e5a6' THEN
    RAISE EXCEPTION
      'Se esperaba alembic_version f1b2c3d4e5a6 antes de e3a5c7d9b1f4; se encontró %',
      COALESCE(v_version, '<vacío>');
  END IF;
END
$$;

CREATE TABLE public.eventos_producto (
  id integer NOT NULL,
  organizacion_id integer NULL REFERENCES public.organizaciones (id) ON DELETE RESTRICT,
  actor_email varchar(254) NOT NULL DEFAULT '',
  accion varchar(60) NOT NULL,
  detalle text NOT NULL DEFAULT '{}',
  created_at timestamp WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE SEQUENCE public.eventos_producto_id_seq
  AS integer START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;
ALTER SEQUENCE public.eventos_producto_id_seq OWNED BY public.eventos_producto.id;
ALTER TABLE public.eventos_producto
  ALTER COLUMN id SET DEFAULT nextval('public.eventos_producto_id_seq');
CREATE INDEX ix_eventos_producto_org_fecha
  ON public.eventos_producto (organizacion_id, created_at);
CREATE INDEX ix_eventos_producto_fecha
  ON public.eventos_producto (created_at);
CREATE INDEX ix_eventos_producto_accion
  ON public.eventos_producto (accion);

-- Inmutable por construcción: solo SELECT e INSERT para el rol runtime.
REVOKE ALL ON TABLE public.eventos_producto FROM PUBLIC;
ALTER TABLE public.eventos_producto ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.eventos_producto FORCE ROW LEVEL SECURITY;
GRANT SELECT, INSERT ON TABLE public.eventos_producto TO cotizat_app;
GRANT USAGE, SELECT ON SEQUENCE public.eventos_producto_id_seq TO cotizat_app;

-- Lectura: solo operador (panel /admin/analitica).
DROP POLICY IF EXISTS cotizat_ep_select_operator ON public.eventos_producto;
CREATE POLICY cotizat_ep_select_operator ON public.eventos_producto
  FOR SELECT TO cotizat_app
  USING (COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE));
-- Escritura: la propia organización (eventos que nacen en la petición) y
-- el operador (activaciones de licencia, webhook de Stripe).
DROP POLICY IF EXISTS cotizat_ep_insert_tenant ON public.eventos_producto;
CREATE POLICY cotizat_ep_insert_tenant ON public.eventos_producto
  FOR INSERT TO cotizat_app
  WITH CHECK (
    organizacion_id IS NOT NULL
    AND cotizat_security.tenant_access(organizacion_id, TRUE)
  );
DROP POLICY IF EXISTS cotizat_ep_insert_operator ON public.eventos_producto;
CREATE POLICY cotizat_ep_insert_operator ON public.eventos_producto
  FOR INSERT TO cotizat_app
  WITH CHECK (COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE));

-- Alta de cuenta sin organización: lista cerrada ('cuenta.registrada').
CREATE OR REPLACE FUNCTION cotizat_security.registrar_evento_producto_global(
  p_email text,
  p_accion text,
  p_detalle text DEFAULT '{}'
) RETURNS boolean LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
BEGIN
  IF p_accion IS NULL
     OR p_accion NOT IN ('cuenta.registrada') THEN
    RETURN FALSE;
  END IF;

  INSERT INTO public.eventos_producto (
    organizacion_id, actor_email, accion, detalle, created_at
  ) VALUES (
    NULL,
    LEFT(LOWER(COALESCE(p_email, '')), 254),
    p_accion,
    LEFT(COALESCE(NULLIF(p_detalle, ''), '{}'), 2000),
    clock_timestamp()
  );
  RETURN TRUE;
END
$$;
ALTER FUNCTION cotizat_security.registrar_evento_producto_global(text, text, text)
  OWNER TO CURRENT_USER;
REVOKE ALL ON FUNCTION cotizat_security.registrar_evento_producto_global(text, text, text)
  FROM PUBLIC;
GRANT EXECUTE ON FUNCTION cotizat_security.registrar_evento_producto_global(text, text, text)
  TO cotizat_app;

-- Baja de organización: incorpora eventos_producto al borrado verificado
-- (misma función que la migración e3a5c7d9b1f4; el cuerpo completo replica
-- la versión vigente de d2a7c9e4f1b3 añadiendo el DELETE nuevo).
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
  DELETE FROM public.compras_plan
    WHERE organizacion_id = p_organization_id;
  DELETE FROM public.eventos_auditoria
    WHERE organizacion_id = p_organization_id;
  DELETE FROM public.eventos_producto
    WHERE organizacion_id = p_organization_id;
  DELETE FROM public.licencias
    WHERE organizacion_id = p_organization_id;
  DELETE FROM public.membresias
    WHERE organizacion_id = p_organization_id;
  DELETE FROM public.organizaciones
    WHERE id = p_organization_id;
END
$$;
ALTER FUNCTION cotizat_security.baja_organizacion(integer) OWNER TO CURRENT_USER;
REVOKE ALL ON FUNCTION cotizat_security.baja_organizacion(integer) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION cotizat_security.baja_organizacion(integer) TO cotizat_app;

UPDATE public.alembic_version
SET version_num = 'e3a5c7d9b1f4'
WHERE version_num = 'f1b2c3d4e5a6';

COMMIT;

-- Verificación:
-- SELECT version_num FROM public.alembic_version;  → e3a5c7d9b1f4
-- SELECT proname, prosecdef FROM pg_proc
-- WHERE pronamespace = 'cotizat_security'::regnamespace
--   AND proname IN ('registrar_evento_producto_global', 'baja_organizacion');
--   → ambas con prosecdef = t
-- SELECT cotizat_security.registrar_evento_producto_global(
--   'prueba@ejemplo.com', 'accion.no_valida');  → f (lista cerrada)
-- SELECT policyname, cmd FROM pg_policies
-- WHERE tablename = 'eventos_producto';
--   → cotizat_ep_select_operator / SELECT
--     cotizat_ep_insert_tenant / INSERT
--     cotizat_ep_insert_operator / INSERT
