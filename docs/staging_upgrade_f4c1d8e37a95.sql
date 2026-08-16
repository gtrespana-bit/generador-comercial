-- CotizaT — actualización de e1a4b7c9d2f0 a f4c1d8e37a95
-- E1-060: panel de operador y registro interno de licencias.
-- Crea la tabla `licencias`, la aísla con RLS exigiendo la marca
-- `cotizat.es_operador` y actualiza `alembic_version`.
--
-- Uso (Supabase → SQL Editor → New query): pega TODO este archivo y pulsa Run.
-- Debe ejecutarse con una sesión administrativa/propietaria. No uses
-- DATABASE_URL del runtime para aplicar DDL.
-- Comprueba primero la versión con:
--   SELECT version_num FROM public.alembic_version;
--
-- Va dentro de una transacción: si algo falla, no se aplica a medias.

BEGIN;

DO $check$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM public.alembic_version
    WHERE version_num = 'e1a4b7c9d2f0'
  ) THEN
    RAISE EXCEPTION
      'Se esperaba alembic_version en e1a4b7c9d2f0 antes de aplicar f4c1d8e37a95';
  END IF;
END
$check$;

CREATE TABLE licencias (
    id SERIAL NOT NULL,
    organizacion_id INTEGER NOT NULL,
    estado VARCHAR(20) DEFAULT 'activa' NOT NULL,
    origen VARCHAR(20) DEFAULT 'pago' NOT NULL,
    inicio DATE NOT NULL,
    vence DATE NOT NULL,
    importe FLOAT DEFAULT '0' NOT NULL,
    moneda VARCHAR(10) DEFAULT 'USD' NOT NULL,
    metodo_cobro VARCHAR(80) DEFAULT '',
    referencia VARCHAR(150) DEFAULT '',
    notas TEXT DEFAULT '',
    creada_por_email VARCHAR(254) DEFAULT '' NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE,
    updated_at TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (id),
    CONSTRAINT ck_licencia_estado_valido
      CHECK (estado IN ('activa', 'vencida', 'cancelada')),
    CONSTRAINT ck_licencia_origen_valido
      CHECK (origen IN ('pago', 'prueba', 'cortesia', 'compensacion')),
    CONSTRAINT ck_licencia_importe_no_negativo CHECK (importe >= 0),
    FOREIGN KEY(organizacion_id) REFERENCES organizaciones (id) ON DELETE RESTRICT
);

CREATE INDEX ix_licencias_organizacion_id ON licencias (organizacion_id);

CREATE INDEX ix_licencias_organizacion_inicio ON licencias (organizacion_id, inicio);

REVOKE ALL ON TABLE public.licencias FROM PUBLIC;

ALTER TABLE public.licencias ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.licencias FORCE ROW LEVEL SECURITY;

GRANT SELECT, INSERT, UPDATE ON TABLE public.licencias TO cotizat_app;

GRANT USAGE, SELECT ON SEQUENCE public.licencias_id_seq TO cotizat_app;

-- Las tres políticas exigen la marca de operador: una sesión normal de cliente
-- no ve ni una fila aunque el código llegara a consultarla por error. No se
-- concede DELETE a propósito: una licencia se cancela, no se borra.
DROP POLICY IF EXISTS cotizat_licencia_select ON public.licencias;

CREATE POLICY cotizat_licencia_select ON public.licencias
            FOR SELECT TO cotizat_app
            USING (
  COALESCE(
    pg_catalog.current_setting('cotizat.es_operador', true) = 'on',
    FALSE
  )
);

DROP POLICY IF EXISTS cotizat_licencia_insert ON public.licencias;

CREATE POLICY cotizat_licencia_insert ON public.licencias
            FOR INSERT TO cotizat_app
            WITH CHECK (
  COALESCE(
    pg_catalog.current_setting('cotizat.es_operador', true) = 'on',
    FALSE
  )
);

DROP POLICY IF EXISTS cotizat_licencia_update ON public.licencias;

CREATE POLICY cotizat_licencia_update ON public.licencias
            FOR UPDATE TO cotizat_app
            USING (
  COALESCE(
    pg_catalog.current_setting('cotizat.es_operador', true) = 'on',
    FALSE
  )
) WITH CHECK (
  COALESCE(
    pg_catalog.current_setting('cotizat.es_operador', true) = 'on',
    FALSE
  )
);

UPDATE public.alembic_version
SET version_num = 'f4c1d8e37a95'
WHERE version_num = 'e1a4b7c9d2f0';

COMMIT;

-- Verificación: debe devolver f4c1d8e37a95
SELECT version_num FROM public.alembic_version;

-- Verificación del RLS: rls y force deben ser true; el SELECT debe estar
-- concedido al rol grupal cotizat_app (se comprueba el privilegio del rol,
-- no el de la sesión admin).
SELECT c.relrowsecurity,
       c.relforcerowsecurity,
       has_table_privilege(
         'cotizat_app', 'public.licencias', 'SELECT'
       ) AS cotizat_app_puede_leer
FROM pg_catalog.pg_class AS c
JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace
WHERE n.nspname = 'public' AND c.relname = 'licencias';
