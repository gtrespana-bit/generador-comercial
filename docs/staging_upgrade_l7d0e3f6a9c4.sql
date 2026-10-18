-- CotizaT — actualización de k6c9f2d5b8a3 a l7d0e3f6a9c4
--
-- Lectura de operador sobre el catálogo de recursos (panel de matrices de
-- precios).
--
-- El importador de la matriz nacional resuelve cada fila del CSV contra
-- `public.recursos` por código. La sesión del panel de administración
-- autentica al operador y marca `cotizat.es_operador`, pero no activa
-- ninguna organización: la política RLS de tenant (`cotizat_tenant_select`,
-- creada en c93e7a4d20f1) exige `cotizat.organization_id` con valor y una
-- membresía activa, así que el SELECT devolvía cero filas y toda la matriz
-- británica (388 filas) se rechazó como «recurso no encontrado» aunque el
-- catálogo estaba sembrado en la base.
--
-- Se añade una política de SELECT adicional para el rol de aplicación. Las
-- políticas permisivas se combinan con OR: la visibilidad de cada
-- organización sobre sus propios recursos no cambia. Es solo lectura; el
-- operador no crea, modifica ni borra recursos de ninguna empresa. La
-- escritura de las referencias nacionales ya la cubren las políticas de
-- `precios_recursos_mercado` (e7b3c1d5a204).
--
-- Ejecutar una sola vez en el SQL Editor de Supabase con el rol
-- administrativo (nunca con `cotizat_runtime` ni con `cotizat_app`) y solo si
-- la versión actual es k6c9f2d5b8a3.

BEGIN;

DO $$
DECLARE
  v_version text;
BEGIN
  SELECT version_num INTO v_version FROM public.alembic_version LIMIT 1;
  IF v_version IS DISTINCT FROM 'k6c9f2d5b8a3' THEN
    RAISE EXCEPTION
      'Se esperaba alembic_version k6c9f2d5b8a3 antes de l7d0e3f6a9c4; se encontró %',
      COALESCE(v_version, '<vacío>');
  END IF;
END
$$;

DROP POLICY IF EXISTS cotizat_operador_select_recursos ON public.recursos;

CREATE POLICY cotizat_operador_select_recursos ON public.recursos
  FOR SELECT TO cotizat_app
  USING (
    COALESCE(
      pg_catalog.current_setting('cotizat.es_operador', true) = 'on',
      FALSE
    )
  );

UPDATE public.alembic_version
SET version_num = 'l7d0e3f6a9c4'
WHERE version_num = 'k6c9f2d5b8a3';

COMMIT;

-- Verificación:
-- SELECT version_num FROM public.alembic_version;
--   → l7d0e3f6a9c4
-- SELECT polname, polcmd FROM pg_policy
--  WHERE polrelid = 'public.recursos'::regclass
--  ORDER BY polname;
--   → además de las cuatro cotizat_tenant_*, debe aparecer:
--     cotizat_operador_select_recursos | r
-- Comprobación funcional (con la sesión del panel): subir de nuevo
-- `basedatos_partidas/salida/precios_recursos_reino_unido.csv` en
-- Sistema › Matrices de precios y pulsar «Validar sin escribir»:
--   → 388 filas · 388 nuevas · 0 errores
