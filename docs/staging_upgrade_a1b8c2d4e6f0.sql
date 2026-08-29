-- CotizaT — actualización de e3a5c7d9b1f4 a a1b8c2d4e6f0
-- Fase 1 del panel: roles de operador (operadores_producto) y auditoría
-- inmutable del panel (eventos_admin), con RLS y grants por rol de aplicación.
-- Ejecutar una sola vez con el rol administrativo de Supabase/PostgreSQL.

BEGIN;

DO $$
DECLARE
  v_version text;
BEGIN
  SELECT version_num INTO v_version FROM public.alembic_version LIMIT 1;
  IF v_version IS DISTINCT FROM 'e3a5c7d9b1f4' THEN
    RAISE EXCEPTION
      'Se esperaba alembic_version e3a5c7d9b1f4 antes de a1b8c2d4e6f0; se encontró %',
      COALESCE(v_version, '<vacío>');
  END IF;
END
$$;

CREATE TABLE public.operadores_producto (
    id SERIAL NOT NULL,
    email VARCHAR(254) NOT NULL,
    rol VARCHAR(30) DEFAULT 'admin' NOT NULL,
    activo BOOLEAN DEFAULT true NOT NULL,
    notas TEXT DEFAULT '' NOT NULL,
    creado_por_email VARCHAR(254) DEFAULT '' NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE,
    updated_at TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (id),
    CONSTRAINT uq_operadores_producto_email UNIQUE (email),
    CONSTRAINT ck_operador_rol_valido CHECK (rol IN ('superadmin', 'admin', 'soporte', 'analista'))
);

CREATE INDEX ix_operadores_producto_email ON public.operadores_producto (email);

CREATE TABLE public.eventos_admin (
    id SERIAL NOT NULL,
    operador_email VARCHAR(254) DEFAULT '' NOT NULL,
    operador_rol VARCHAR(30) DEFAULT '' NOT NULL,
    accion VARCHAR(60) NOT NULL,
    entidad VARCHAR(40) DEFAULT '' NOT NULL,
    entidad_id INTEGER,
    organizacion_id INTEGER,
    detalle TEXT DEFAULT '{}' NOT NULL,
    ip_hash VARCHAR(64) DEFAULT '' NOT NULL,
    resultado VARCHAR(20) DEFAULT 'ok' NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_eventos_admin_organizacion
      FOREIGN KEY (organizacion_id) REFERENCES public.organizaciones (id) ON DELETE RESTRICT
);

CREATE INDEX ix_eventos_admin_fecha ON public.eventos_admin (created_at);
CREATE INDEX ix_eventos_admin_actor ON public.eventos_admin (operador_email, created_at);
CREATE INDEX ix_eventos_admin_org ON public.eventos_admin (organizacion_id, created_at);
CREATE INDEX ix_eventos_admin_accion ON public.eventos_admin (accion, created_at);

REVOKE ALL ON TABLE public.operadores_producto FROM PUBLIC;
ALTER TABLE public.operadores_producto ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.operadores_producto FORCE ROW LEVEL SECURITY;
GRANT SELECT, INSERT, UPDATE ON TABLE public.operadores_producto TO cotizat_app;
GRANT USAGE, SELECT ON SEQUENCE public.operadores_producto_id_seq TO cotizat_app;

DROP POLICY IF EXISTS cotizat_operador_select_own ON public.operadores_producto;
CREATE POLICY cotizat_operador_select_own ON public.operadores_producto
  FOR SELECT TO cotizat_app
  USING (
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
    OR LOWER(email) = pg_catalog.current_setting('cotizat.auth_email', true)
  );

DROP POLICY IF EXISTS cotizat_operador_insert_superadmin ON public.operadores_producto;
CREATE POLICY cotizat_operador_insert_superadmin ON public.operadores_producto
  FOR INSERT TO cotizat_app
  WITH CHECK (
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
    AND COALESCE(pg_catalog.current_setting('cotizat.operador_rol', true) = 'superadmin', FALSE)
  );

DROP POLICY IF EXISTS cotizat_operador_update_superadmin ON public.operadores_producto;
CREATE POLICY cotizat_operador_update_superadmin ON public.operadores_producto
  FOR UPDATE TO cotizat_app
  USING (
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
    AND COALESCE(pg_catalog.current_setting('cotizat.operador_rol', true) = 'superadmin', FALSE)
  )
  WITH CHECK (
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
    AND COALESCE(pg_catalog.current_setting('cotizat.operador_rol', true) = 'superadmin', FALSE)
  );

DROP POLICY IF EXISTS cotizat_operador_delete_superadmin ON public.operadores_producto;
CREATE POLICY cotizat_operador_delete_superadmin ON public.operadores_producto
  FOR DELETE TO cotizat_app
  USING (
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
    AND COALESCE(pg_catalog.current_setting('cotizat.operador_rol', true) = 'superadmin', FALSE)
  );

REVOKE ALL ON TABLE public.eventos_admin FROM PUBLIC;
ALTER TABLE public.eventos_admin ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.eventos_admin FORCE ROW LEVEL SECURITY;
GRANT SELECT, INSERT ON TABLE public.eventos_admin TO cotizat_app;
GRANT USAGE, SELECT ON SEQUENCE public.eventos_admin_id_seq TO cotizat_app;

DROP POLICY IF EXISTS cotizat_evento_admin_select ON public.eventos_admin;
CREATE POLICY cotizat_evento_admin_select ON public.eventos_admin
  FOR SELECT TO cotizat_app
  USING (
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
  );

DROP POLICY IF EXISTS cotizat_evento_admin_insert ON public.eventos_admin;
CREATE POLICY cotizat_evento_admin_insert ON public.eventos_admin
  FOR INSERT TO cotizat_app
  WITH CHECK (
    COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)
  );

UPDATE public.alembic_version
SET version_num = 'a1b8c2d4e6f0'
WHERE version_num = 'e3a5c7d9b1f4';

COMMIT;

-- Verificación:
-- SELECT version_num FROM public.alembic_version;  → a1b8c2d4e6f0
-- \dt public.operadores_producto public.eventos_admin
-- SELECT policyname, tablename, cmd, roles
-- FROM pg_policies
-- WHERE tablename IN ('operadores_producto', 'eventos_admin')
-- ORDER BY tablename, policyname;
--   → operadores_producto: cotizat_operador_select_own / cotizat_operador_*_superadmin
--   → eventos_admin: cotizat_evento_admin_select / cotizat_evento_admin_insert
