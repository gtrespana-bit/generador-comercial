-- CotizaT — actualización de c2d4e6f8a1b3 a d3e5f7a9c2b4
-- Fase 3 y 4 del panel: web pública gestionable (CMS de landing, avisos,
-- releases, feature flags), CRM ligero (B4) y API keys de operador (A6).
--
-- Idempotente: si ya se aplicó d3e5f7a9c2b4 no falla; si la tabla está en
-- c2d4e6f8a1b3 aplica los cambios; si está en otro punto, aborta.
-- Solo guarda el hash SHA-256 de las API keys; nunca el token en claro.
--
-- Ejecutar una sola vez con el rol administrativo de Supabase/PostgreSQL.

BEGIN;

DO $$
DECLARE
  v_version text;
BEGIN
  SELECT version_num INTO v_version FROM public.alembic_version LIMIT 1;
  IF v_version = 'd3e5f7a9c2b4' THEN
    RAISE NOTICE 'Ya está en d3e5f7a9c2b4: no se vuelve a modificar.';
  ELSIF v_version IS DISTINCT FROM 'c2d4e6f8a1b3' THEN
    RAISE EXCEPTION
      'Se esperaba alembic_version c2d4e6f8a1b3 antes de d3e5f7a9c2b4; se encontró %',
      COALESCE(v_version, '<vacío>');
  END IF;
END
$$;

-- --------------------------------------------------------------------------
-- contenido_web (CMS publicar/descartar)
-- --------------------------------------------------------------------------
CREATE SEQUENCE IF NOT EXISTS public.contenido_web_id_seq;
CREATE TABLE IF NOT EXISTS public.contenido_web (
    id integer NOT NULL DEFAULT nextval('public.contenido_web_id_seq'),
    clave VARCHAR(80) NOT NULL,
    borrador TEXT DEFAULT '{}' NOT NULL,
    publicado TEXT,
    publicado_por VARCHAR(254) DEFAULT '' NOT NULL,
    publicado_at TIMESTAMP WITHOUT TIME ZONE,
    updated_by VARCHAR(254) DEFAULT '' NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (id),
    CONSTRAINT uq_contenido_web_clave UNIQUE (clave)
);
ALTER SEQUENCE public.contenido_web_id_seq OWNED BY public.contenido_web.id;
CREATE INDEX IF NOT EXISTS ix_contenido_web_clave ON public.contenido_web (clave);

REVOKE ALL ON TABLE public.contenido_web FROM PUBLIC;
ALTER TABLE public.contenido_web ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.contenido_web FORCE ROW LEVEL SECURITY;
GRANT SELECT, INSERT, UPDATE ON TABLE public.contenido_web TO cotizat_app;
GRANT USAGE, SELECT ON SEQUENCE public.contenido_web_id_seq TO cotizat_app;

DROP POLICY IF EXISTS cotizat_contenido_web_select_publico ON public.contenido_web;
CREATE POLICY cotizat_contenido_web_select_publico ON public.contenido_web
  FOR SELECT TO cotizat_app
  USING (
    publicado IS NOT NULL OR
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
  );

DROP POLICY IF EXISTS cotizat_contenido_web_insert_operator ON public.contenido_web;
CREATE POLICY cotizat_contenido_web_insert_operator ON public.contenido_web
  FOR INSERT TO cotizat_app
  WITH CHECK (
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
  );

DROP POLICY IF EXISTS cotizat_contenido_web_update_operator ON public.contenido_web;
CREATE POLICY cotizat_contenido_web_update_operator ON public.contenido_web
  FOR UPDATE TO cotizat_app
  USING (
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
  )
  WITH CHECK (
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
  );

-- --------------------------------------------------------------------------
-- avisos_web (banners/avisos públicos)
-- --------------------------------------------------------------------------
CREATE SEQUENCE IF NOT EXISTS public.avisos_web_id_seq;
CREATE TABLE IF NOT EXISTS public.avisos_web (
    id integer NOT NULL DEFAULT nextval('public.avisos_web_id_seq'),
    tipo VARCHAR(30) DEFAULT 'info' NOT NULL,
    nivel VARCHAR(20) DEFAULT 'info' NOT NULL,
    titulo VARCHAR(180) NOT NULL,
    mensaje TEXT DEFAULT '' NOT NULL,
    activo BOOLEAN DEFAULT false NOT NULL,
    inicio DATE,
    fin DATE,
    creado_por VARCHAR(254) DEFAULT '' NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (id)
);
ALTER SEQUENCE public.avisos_web_id_seq OWNED BY public.avisos_web.id;
CREATE INDEX IF NOT EXISTS ix_avisos_web_activo_fechas ON public.avisos_web (activo, inicio, fin);

REVOKE ALL ON TABLE public.avisos_web FROM PUBLIC;
ALTER TABLE public.avisos_web ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.avisos_web FORCE ROW LEVEL SECURITY;
GRANT SELECT, INSERT, UPDATE ON TABLE public.avisos_web TO cotizat_app;
GRANT USAGE, SELECT ON SEQUENCE public.avisos_web_id_seq TO cotizat_app;

DROP POLICY IF EXISTS cotizat_avisos_web_select_publico ON public.avisos_web;
CREATE POLICY cotizat_avisos_web_select_publico ON public.avisos_web
  FOR SELECT TO cotizat_app
  USING (
    activo IS TRUE OR
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
  );

DROP POLICY IF EXISTS cotizat_avisos_web_insert_operator ON public.avisos_web;
CREATE POLICY cotizat_avisos_web_insert_operator ON public.avisos_web
  FOR INSERT TO cotizat_app
  WITH CHECK (
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
  );

DROP POLICY IF EXISTS cotizat_avisos_web_update_operator ON public.avisos_web;
CREATE POLICY cotizat_avisos_web_update_operator ON public.avisos_web
  FOR UPDATE TO cotizat_app
  USING (
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
  )
  WITH CHECK (
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
  );

-- --------------------------------------------------------------------------
-- releases (changelog)
-- --------------------------------------------------------------------------
CREATE SEQUENCE IF NOT EXISTS public.releases_id_seq;
CREATE TABLE IF NOT EXISTS public.releases (
    id integer NOT NULL DEFAULT nextval('public.releases_id_seq'),
    version VARCHAR(30) NOT NULL,
    titulo VARCHAR(200) NOT NULL,
    notas TEXT DEFAULT '' NOT NULL,
    destacado BOOLEAN DEFAULT false NOT NULL,
    publicado BOOLEAN DEFAULT false NOT NULL,
    fecha DATE DEFAULT CURRENT_DATE NOT NULL,
    creado_por VARCHAR(254) DEFAULT '' NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (id),
    CONSTRAINT uq_releases_version UNIQUE (version)
);
ALTER SEQUENCE public.releases_id_seq OWNED BY public.releases.id;
CREATE INDEX IF NOT EXISTS ix_releases_pub_fecha ON public.releases (publicado, fecha);

REVOKE ALL ON TABLE public.releases FROM PUBLIC;
ALTER TABLE public.releases ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.releases FORCE ROW LEVEL SECURITY;
GRANT SELECT, INSERT, UPDATE ON TABLE public.releases TO cotizat_app;
GRANT USAGE, SELECT ON SEQUENCE public.releases_id_seq TO cotizat_app;

DROP POLICY IF EXISTS cotizat_releases_select_publico ON public.releases;
CREATE POLICY cotizat_releases_select_publico ON public.releases
  FOR SELECT TO cotizat_app
  USING (
    publicado IS TRUE OR
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
  );

DROP POLICY IF EXISTS cotizat_releases_insert_operator ON public.releases;
CREATE POLICY cotizat_releases_insert_operator ON public.releases
  FOR INSERT TO cotizat_app
  WITH CHECK (
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
  );

DROP POLICY IF EXISTS cotizat_releases_update_operator ON public.releases;
CREATE POLICY cotizat_releases_update_operator ON public.releases
  FOR UPDATE TO cotizat_app
  USING (
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
  )
  WITH CHECK (
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
  );

-- --------------------------------------------------------------------------
-- feature_flags (solo operador)
-- --------------------------------------------------------------------------
CREATE SEQUENCE IF NOT EXISTS public.feature_flags_id_seq;
CREATE TABLE IF NOT EXISTS public.feature_flags (
    id integer NOT NULL DEFAULT nextval('public.feature_flags_id_seq'),
    clave VARCHAR(80) NOT NULL,
    activo BOOLEAN DEFAULT false NOT NULL,
    descripcion VARCHAR(300) DEFAULT '' NOT NULL,
    updated_by VARCHAR(254) DEFAULT '' NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (id),
    CONSTRAINT uq_feature_flags_clave UNIQUE (clave)
);
ALTER SEQUENCE public.feature_flags_id_seq OWNED BY public.feature_flags.id;

REVOKE ALL ON TABLE public.feature_flags FROM PUBLIC;
ALTER TABLE public.feature_flags ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.feature_flags FORCE ROW LEVEL SECURITY;
GRANT SELECT, INSERT, UPDATE ON TABLE public.feature_flags TO cotizat_app;
GRANT USAGE, SELECT ON SEQUENCE public.feature_flags_id_seq TO cotizat_app;

DROP POLICY IF EXISTS cotizat_feature_flags_select_operator ON public.feature_flags;
CREATE POLICY cotizat_feature_flags_select_operator ON public.feature_flags
  FOR SELECT TO cotizat_app
  USING (
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
  );

DROP POLICY IF EXISTS cotizat_feature_flags_insert_operator ON public.feature_flags;
CREATE POLICY cotizat_feature_flags_insert_operator ON public.feature_flags
  FOR INSERT TO cotizat_app
  WITH CHECK (
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
  );

DROP POLICY IF EXISTS cotizat_feature_flags_update_operator ON public.feature_flags;
CREATE POLICY cotizat_feature_flags_update_operator ON public.feature_flags
  FOR UPDATE TO cotizat_app
  USING (
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
  )
  WITH CHECK (
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
  );

-- --------------------------------------------------------------------------
-- vistas_guardadas (A5 completo, solo operador)
-- --------------------------------------------------------------------------
CREATE SEQUENCE IF NOT EXISTS public.vistas_guardadas_id_seq;
CREATE TABLE IF NOT EXISTS public.vistas_guardadas (
    id integer NOT NULL DEFAULT nextval('public.vistas_guardadas_id_seq'),
    nombre VARCHAR(120) NOT NULL,
    modulo VARCHAR(60) NOT NULL,
    filtros TEXT DEFAULT '{}' NOT NULL,
    columnas TEXT DEFAULT '[]' NOT NULL,
    creada_por VARCHAR(254) DEFAULT '' NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (id)
);
ALTER SEQUENCE public.vistas_guardadas_id_seq OWNED BY public.vistas_guardadas.id;
CREATE INDEX IF NOT EXISTS ix_vistas_guardadas_modulo ON public.vistas_guardadas (modulo, nombre);

REVOKE ALL ON TABLE public.vistas_guardadas FROM PUBLIC;
ALTER TABLE public.vistas_guardadas ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vistas_guardadas FORCE ROW LEVEL SECURITY;
GRANT SELECT, INSERT, UPDATE ON TABLE public.vistas_guardadas TO cotizat_app;
GRANT USAGE, SELECT ON SEQUENCE public.vistas_guardadas_id_seq TO cotizat_app;

DROP POLICY IF EXISTS cotizat_vistas_guardadas_select_operator ON public.vistas_guardadas;
CREATE POLICY cotizat_vistas_guardadas_select_operator ON public.vistas_guardadas
  FOR SELECT TO cotizat_app
  USING (
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
  );

DROP POLICY IF EXISTS cotizat_vistas_guardadas_insert_operator ON public.vistas_guardadas;
CREATE POLICY cotizat_vistas_guardadas_insert_operator ON public.vistas_guardadas
  FOR INSERT TO cotizat_app
  WITH CHECK (
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
  );

DROP POLICY IF EXISTS cotizat_vistas_guardadas_update_operator ON public.vistas_guardadas;
CREATE POLICY cotizat_vistas_guardadas_update_operator ON public.vistas_guardadas
  FOR UPDATE TO cotizat_app
  USING (
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
  )
  WITH CHECK (
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
  );

-- --------------------------------------------------------------------------
-- crm_clientes (B4, solo operador)
-- --------------------------------------------------------------------------
CREATE SEQUENCE IF NOT EXISTS public.crm_clientes_id_seq;
CREATE TABLE IF NOT EXISTS public.crm_clientes (
    id integer NOT NULL DEFAULT nextval('public.crm_clientes_id_seq'),
    organizacion_id integer NOT NULL,
    estado VARCHAR(20) DEFAULT 'activo' NOT NULL,
    proximo_contacto DATE,
    notas TEXT DEFAULT '' NOT NULL,
    updated_by VARCHAR(254) DEFAULT '' NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (id),
    CONSTRAINT uq_crm_clientes_org UNIQUE (organizacion_id),
    CONSTRAINT fk_crm_clientes_organizacion
      FOREIGN KEY (organizacion_id) REFERENCES public.organizaciones (id) ON DELETE RESTRICT
);
ALTER SEQUENCE public.crm_clientes_id_seq OWNED BY public.crm_clientes.id;
CREATE INDEX IF NOT EXISTS ix_crm_clientes_estado ON public.crm_clientes (estado, proximo_contacto);

REVOKE ALL ON TABLE public.crm_clientes FROM PUBLIC;
ALTER TABLE public.crm_clientes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.crm_clientes FORCE ROW LEVEL SECURITY;
GRANT SELECT, INSERT, UPDATE ON TABLE public.crm_clientes TO cotizat_app;
GRANT USAGE, SELECT ON SEQUENCE public.crm_clientes_id_seq TO cotizat_app;

DROP POLICY IF EXISTS cotizat_crm_clientes_select_operator ON public.crm_clientes;
CREATE POLICY cotizat_crm_clientes_select_operator ON public.crm_clientes
  FOR SELECT TO cotizat_app
  USING (
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
  );

DROP POLICY IF EXISTS cotizat_crm_clientes_insert_operator ON public.crm_clientes;
CREATE POLICY cotizat_crm_clientes_insert_operator ON public.crm_clientes
  FOR INSERT TO cotizat_app
  WITH CHECK (
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
  );

DROP POLICY IF EXISTS cotizat_crm_clientes_update_operator ON public.crm_clientes;
CREATE POLICY cotizat_crm_clientes_update_operator ON public.crm_clientes
  FOR UPDATE TO cotizat_app
  USING (
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
  )
  WITH CHECK (
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
  );

-- --------------------------------------------------------------------------
-- api_keys_operador (A6, solo hash SHA-256 de la clave)
-- --------------------------------------------------------------------------
CREATE SEQUENCE IF NOT EXISTS public.api_keys_operador_id_seq;
CREATE TABLE IF NOT EXISTS public.api_keys_operador (
    id integer NOT NULL DEFAULT nextval('public.api_keys_operador_id_seq'),
    nombre VARCHAR(100) NOT NULL,
    clave_hash VARCHAR(64) NOT NULL,
    scopes TEXT DEFAULT '[]' NOT NULL,
    activo BOOLEAN DEFAULT true NOT NULL,
    creada_por VARCHAR(254) DEFAULT '' NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_used_at TIMESTAMP WITHOUT TIME ZONE,
    revoked_at TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (id),
    CONSTRAINT uq_api_keys_operador_hash UNIQUE (clave_hash)
);
ALTER SEQUENCE public.api_keys_operador_id_seq OWNED BY public.api_keys_operador.id;
CREATE INDEX IF NOT EXISTS ix_api_keys_operador_nombre ON public.api_keys_operador (nombre);

REVOKE ALL ON TABLE public.api_keys_operador FROM PUBLIC;
ALTER TABLE public.api_keys_operador ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.api_keys_operador FORCE ROW LEVEL SECURITY;
GRANT SELECT, INSERT, UPDATE ON TABLE public.api_keys_operador TO cotizat_app;
GRANT USAGE, SELECT ON SEQUENCE public.api_keys_operador_id_seq TO cotizat_app;

DROP POLICY IF EXISTS cotizat_api_keys_operador_select_operator ON public.api_keys_operador;
CREATE POLICY cotizat_api_keys_operador_select_operator ON public.api_keys_operador
  FOR SELECT TO cotizat_app
  USING (
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
  );

DROP POLICY IF EXISTS cotizat_api_keys_operador_insert_operator ON public.api_keys_operador;
CREATE POLICY cotizat_api_keys_operador_insert_operator ON public.api_keys_operador
  FOR INSERT TO cotizat_app
  WITH CHECK (
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
  );

DROP POLICY IF EXISTS cotizat_api_keys_operador_update_operator ON public.api_keys_operador;
CREATE POLICY cotizat_api_keys_operador_update_operator ON public.api_keys_operador
  FOR UPDATE TO cotizat_app
  USING (
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
  )
  WITH CHECK (
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
  );

-- --------------------------------------------------------------------------
-- Marca de revisión
-- --------------------------------------------------------------------------
UPDATE public.alembic_version
   SET version_num = 'd3e5f7a9c2b4'
 WHERE version_num = 'c2d4e6f8a1b3';

COMMIT;
