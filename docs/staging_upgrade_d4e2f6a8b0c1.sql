-- CotizaT — migración d4e2f6a8b0c1: el resumen del cliente suma el acceso
-- encadenado (varias licencias activas → tiempo total).
--
-- Antes, si quedaban 4 días de plan y se activaba 1 mes más, la barra
-- lateral y /configuracion mostraban «4 d» (solo la primera licencia).
-- Ahora organization_license_info devuelve el final de la cadena completa
-- (~34 d) con la etiqueta y el método de la licencia vigente.
--
-- Ejecutar una sola vez con rol administrativo si la base ya está en a1b2c3d4e5f6.

BEGIN;

DO $$
DECLARE
  v_version text;
BEGIN
  SELECT version_num INTO v_version FROM public.alembic_version LIMIT 1;
  IF v_version IS DISTINCT FROM 'a1b2c3d4e5f6' THEN
    RAISE EXCEPTION
      'Se esperaba alembic_version a1b2c3d4e5f6 antes de d4e2f6a8b0c1; se encontró %',
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
  v_actual record;
  v_fin date;
BEGIN
  v_org := cotizat_security.context_organization_id();
  IF p_organization_id IS DISTINCT FROM v_org THEN
    RETURN;
  END IF;

  -- Licencia que da acceso hoy (la primera de la cadena): de ella salen
  -- la etiqueta del plan y el método de cobro.
  SELECT *
  INTO v_actual
  FROM public.licencias l
  WHERE l.organizacion_id = p_organization_id
    AND l.estado = 'activa'
    AND l.inicio <= CURRENT_DATE
    AND l.vence >= CURRENT_DATE
  ORDER BY l.vence DESC
  LIMIT 1;
  IF v_actual.id IS NULL THEN
    RETURN;
  END IF;

  -- Último día del encadenado: las renovaciones empiezan al día siguiente
  -- del vencimiento anterior, así que el acceso llega hasta el final de
  -- la cadena (4 días + 1 mes → ~34 días), no hasta la primera licencia.
  -- `l.vence > c.fin` garantiza progreso y terminación de la recursión;
  -- un día de hueco entre licencias corta la cadena.
  WITH RECURSIVE cadena AS (
    SELECT v_actual.vence AS fin
    UNION
    SELECT l.vence
    FROM public.licencias l
    JOIN cadena c
      ON l.organizacion_id = p_organization_id
     AND l.estado = 'activa'
     AND l.inicio <= c.fin + 1
     AND l.vence > c.fin
  )
  SELECT MAX(fin) INTO v_fin FROM cadena;
  v_fin := COALESCE(v_fin, v_actual.vence);

  activo := TRUE::boolean;
  plan_label := (CASE
      WHEN v_actual.origen = 'pago' AND round(v_actual.importe::numeric, 2) = 89.00
        THEN 'Plan anual'
      WHEN v_actual.origen = 'pago' AND round(v_actual.importe::numeric, 2) = 9.99
        THEN 'Plan mensual'
      WHEN v_actual.origen = 'pago' THEN 'Plan de pago'
      ELSE COALESCE(NULLIF(v_actual.metodo_cobro, ''), v_actual.origen)
    END)::text;
  vence := v_fin;
  dias_restantes := GREATEST((v_fin - CURRENT_DATE), 0)::integer;
  metodo_cobro := v_actual.metodo_cobro::text;
  RETURN NEXT;
END;
$$;

REVOKE ALL ON FUNCTION cotizat_security.organization_license_info(integer) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION cotizat_security.organization_license_info(integer) TO cotizat_app;

UPDATE public.alembic_version
SET version_num = 'd4e2f6a8b0c1'
WHERE version_num = 'a1b2c3d4e5f6';

COMMIT;

-- Verificación:
-- SELECT version_num FROM public.alembic_version; -- → d4e2f6a8b0c1
-- BEGIN; SELECT set_config('cotizat.organization_id','6',true);
-- SELECT * FROM cotizat_security.organization_license_info(6); ROLLBACK;
