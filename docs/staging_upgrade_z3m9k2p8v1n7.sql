-- CotizaT — actualización de y1n3p5q7r9s2 a z3m9k2p8v1n7
-- Marketing por email: historial de envíos y bajas con un clic.
--
-- Por qué existe este archivo: en producción (Supabase) las migraciones se
-- aplican a mano pegando este SQL. El head exigido por el runtime cambia con
-- el despliegue, así que la base tiene que estar en z3m9k2p8v1n7 **antes** de
-- fusionar el código que lo declara.
--
-- Contenido:
--   1. Tablas `envios_marketing` y `bajas_marketing` (idempotencia y bajas).
--   2. Índices, constraints y RLS solo operador + GRANT a cotizat_app.
--   3. Avance de la marca en public.alembic_version.
--
-- Uso (Supabase → SQL Editor → New query): pega TODO este archivo y pulsa Run.
-- Debe ejecutarse con una sesión administrativa/propietaria. No uses
-- DATABASE_URL del runtime para aplicar DDL.
-- Comprueba primero la versión con:
--   SELECT version_num FROM public.alembic_version;  -- debe ser y1n3p5q7r9s2
BEGIN;

DO $$
BEGIN
  IF (SELECT version_num FROM public.alembic_version LIMIT 1) IS DISTINCT FROM 'y1n3p5q7r9s2' THEN
    RAISE EXCEPTION 'Head inesperado; se esperaba y1n3p5q7r9s2';
  END IF;
END $$;

-- Running upgrade y1n3p5q7r9s2 -> z3m9k2p8v1n7

CREATE TABLE IF NOT EXISTS public.envios_marketing (
    id SERIAL PRIMARY KEY,
    organizacion_id INTEGER REFERENCES public.organizaciones(id) ON DELETE SET NULL,
    email VARCHAR(254) NOT NULL DEFAULT '',
    plantilla VARCHAR(60) NOT NULL DEFAULT '',
    estado VARCHAR(20) NOT NULL DEFAULT 'enviado',
    proveedor_id VARCHAR(120) NOT NULL DEFAULT '',
    enviado_en TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT uq_envio_marketing_org_plantilla UNIQUE (organizacion_id, plantilla)
);
CREATE INDEX IF NOT EXISTS ix_envios_marketing_enviado ON public.envios_marketing (enviado_en);
CREATE INDEX IF NOT EXISTS ix_envios_marketing_email ON public.envios_marketing (email);

CREATE TABLE IF NOT EXISTS public.bajas_marketing (
    id SERIAL PRIMARY KEY,
    email VARCHAR(254) NOT NULL,
    origen VARCHAR(20) NOT NULL DEFAULT 'enlace',
    creada_en TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT uq_baja_marketing_email UNIQUE (email)
);
CREATE INDEX IF NOT EXISTS ix_bajas_marketing_creada ON public.bajas_marketing (creada_en);

-- RLS solo operador
REVOKE ALL ON TABLE public.envios_marketing FROM PUBLIC;
ALTER TABLE public.envios_marketing ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.envios_marketing FORCE ROW LEVEL SECURITY;
GRANT SELECT, INSERT, UPDATE ON TABLE public.envios_marketing TO cotizat_app;
GRANT USAGE, SELECT ON SEQUENCE public.envios_marketing_id_seq TO cotizat_app;
DROP POLICY IF EXISTS cotizat_envios_marketing_operador ON public.envios_marketing;
CREATE POLICY cotizat_envios_marketing_operador ON public.envios_marketing
  FOR ALL TO cotizat_app USING (
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
  ) WITH CHECK (
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
  );

REVOKE ALL ON TABLE public.bajas_marketing FROM PUBLIC;
ALTER TABLE public.bajas_marketing ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bajas_marketing FORCE ROW LEVEL SECURITY;
GRANT SELECT, INSERT, UPDATE ON TABLE public.bajas_marketing TO cotizat_app;
GRANT USAGE, SELECT ON SEQUENCE public.bajas_marketing_id_seq TO cotizat_app;
DROP POLICY IF EXISTS cotizat_bajas_marketing_operador ON public.bajas_marketing;
CREATE POLICY cotizat_bajas_marketing_operador ON public.bajas_marketing
  FOR ALL TO cotizat_app USING (
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
  ) WITH CHECK (
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
  );

UPDATE public.alembic_version
   SET version_num = 'z3m9k2p8v1n7'
 WHERE version_num = 'y1n3p5q7r9s2';

COMMIT;

-- Verificar:
--   SELECT version_num FROM public.alembic_version;  -- z3m9k2p8v1n7
--   SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename IN ('envios_marketing','bajas_marketing');
--   SELECT policyname FROM pg_policies WHERE schemaname='public' AND tablename IN ('envios_marketing','bajas_marketing');
