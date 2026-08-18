-- CotizaT — hotfix a1b2c3d4e5f6: corrige organization_license_info
-- Desajuste de tipos varchar(80) vs text que provocaba
--   psycopg.errors.DatatypeMismatch: Returned type varchar does not match text
-- y tumbaba /configuracion y la barra lateral (Sin plan).
-- Ejecutar una sola vez con rol administrativo si la base ya está en f9d4c2a7e5b3.

BEGIN;

DO $$
DECLARE
  v_version text;
BEGIN
  SELECT version_num INTO v_version FROM public.alembic_version LIMIT 1;
  IF v_version IS DISTINCT FROM 'f9d4c2a7e5b3' THEN
    RAISE EXCEPTION
      'Se esperaba alembic_version f9d4c2a7e5b3 antes de a1b2c3d4e5f6; se encontró %',
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
    TRUE::boolean,
    (CASE
      WHEN l.origen = 'pago' AND round(l.importe::numeric, 2) = 89.00
        THEN 'Plan anual'
      WHEN l.origen = 'pago' AND round(l.importe::numeric, 2) = 9.99
        THEN 'Plan mensual'
      WHEN l.origen = 'pago' THEN 'Plan de pago'
      ELSE COALESCE(NULLIF(l.metodo_cobro, ''), l.origen)
    END)::text,
    l.vence,
    GREATEST((l.vence - CURRENT_DATE), 0)::integer,
    l.metodo_cobro::text
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
SET version_num = 'a1b2c3d4e5f6'
WHERE version_num = 'f9d4c2a7e5b3';

COMMIT;

-- Verificación:
-- SELECT version_num FROM public.alembic_version; -- → a1b2c3d4e5f6
-- BEGIN; SELECT set_config('cotizat.organization_id','6',true);
-- SELECT * FROM cotizat_security.organization_license_info(6); ROLLBACK;
