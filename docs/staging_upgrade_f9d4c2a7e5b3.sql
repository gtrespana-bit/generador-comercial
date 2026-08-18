-- CotizaT — actualización de e5f2a8d31b6c a f9d4c2a7e5b3
-- Información de licencia visible para el propio cliente.
-- Ejecutar una sola vez con el rol administrativo de Supabase/PostgreSQL.

BEGIN;

DO $$
DECLARE
  v_version text;
BEGIN
  SELECT version_num INTO v_version FROM public.alembic_version LIMIT 1;
  IF v_version IS DISTINCT FROM 'e5f2a8d31b6c' THEN
    RAISE EXCEPTION
      'Se esperaba alembic_version e5f2a8d31b6c antes de f9d4c2a7e5b3; se encontró %',
      COALESCE(v_version, '<vacío>');
  END IF;
END
$$;

CREATE OR REPLACE FUNCTION cotizat_security.organization_license_info(
  p_organization_id integer
) RETURNS TABLE(
  activo boolean,
  plan_label text,
  vence date,
  dias_restantes integer,
  metodo_cobro text
) LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
DECLARE
  v_org integer;
BEGIN
  v_org := cotizat_security.context_organization_id();
  IF p_organization_id IS DISTINCT FROM v_org THEN
    RETURN;
  END IF;
  RETURN QUERY
  SELECT
    TRUE,
    CASE
      WHEN l.origen = 'pago' AND round(l.importe::numeric, 2) = 89.00
        THEN 'Plan anual'
      WHEN l.origen = 'pago' AND round(l.importe::numeric, 2) = 9.99
        THEN 'Plan mensual'
      WHEN l.origen = 'pago' THEN 'Plan de pago'
      ELSE COALESCE(NULLIF(l.metodo_cobro, ''), l.origen)
    END,
    l.vence,
    GREATEST((l.vence - CURRENT_DATE), 0),
    l.metodo_cobro
  FROM public.licencias l
  WHERE l.organizacion_id = p_organization_id
    AND l.estado = 'activa'
    AND l.inicio <= CURRENT_DATE
    AND l.vence >= CURRENT_DATE
  ORDER BY l.vence DESC
  LIMIT 1;
END;
$$;

REVOKE ALL ON FUNCTION cotizat_security.organization_license_info(integer) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION cotizat_security.organization_license_info(integer) TO cotizat_app;

UPDATE public.alembic_version
SET version_num = 'f9d4c2a7e5b3'
WHERE version_num = 'e5f2a8d31b6c';

COMMIT;

-- Verificación:
-- SELECT version_num FROM public.alembic_version;
-- SELECT proname, prosecdef FROM pg_proc
-- WHERE proname = 'organization_license_info' AND pronamespace = 'cotizat_security'::regnamespace;
--   → organization_license_info | t
-- BEGIN; SELECT set_config('cotizat.organization_id', '<tu_org_id>', true);
-- SELECT * FROM cotizat_security.organization_license_info(<tu_org_id>); ROLLBACK;
--   → fila con plan_label, vence y dias_restantes si hay licencia vigente; 0 filas si no.
