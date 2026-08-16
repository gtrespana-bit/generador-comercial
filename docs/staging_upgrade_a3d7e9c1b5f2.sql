-- CotizaT — actualización de c2f6e8a1d934 a a3d7e9c1b5f2
-- E3-023: función de baja de organización con borrado verificado.
-- Ejecutar únicamente en Supabase SQL Editor con sesión administrativa.
-- No usar DATABASE_URL del runtime para aplicar DDL.
--
-- La función borra en una transacción todos los datos de negocio, licencias,
-- membresías y la propia organización, con doble guardia: el claim de
-- organización de la sesión y el rol de propietario. Los archivos del
-- almacenamiento privado los borra la aplicación por el proxy autorizado
-- ANTES de invocar la función.

BEGIN;

DO $check$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM public.alembic_version
    WHERE version_num = 'c2f6e8a1d934'
  ) THEN
    RAISE EXCEPTION
      'Se esperaba alembic_version c2f6e8a1d934 antes de a3d7e9c1b5f2';
  END IF;
END
$check$;

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
$$;

ALTER FUNCTION cotizat_security.baja_organizacion(integer) OWNER TO CURRENT_USER;
REVOKE ALL ON FUNCTION cotizat_security.baja_organizacion(integer) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION cotizat_security.baja_organizacion(integer)
  TO cotizat_app;

UPDATE public.alembic_version
SET version_num = 'a3d7e9c1b5f2'
WHERE version_num = 'c2f6e8a1d934';

COMMIT;

-- Verificación: una sola fila con el nuevo head.
SELECT version_num FROM public.alembic_version;

-- Verificación de la función: propietario, SECURITY DEFINER y sin ejecución
-- pública.
SELECT p.proname,
       pg_get_userbyid(p.proowner) AS propietario,
       p.prosecdef AS security_definer
FROM pg_catalog.pg_proc AS p
JOIN pg_catalog.pg_namespace AS n ON n.oid = p.pronamespace
WHERE n.nspname = 'cotizat_security'
  AND p.proname = 'baja_organizacion';
