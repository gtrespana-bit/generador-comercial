BEGIN;

-- Running upgrade 9bca2ad1f6e4 -> 72e6f4d8a1c3

CREATE TABLE archivos_almacenados (
    id SERIAL NOT NULL, 
    object_key VARCHAR(900) NOT NULL, 
    categoria VARCHAR(80) NOT NULL, 
    content_type VARCHAR(150) NOT NULL, 
    tamano_bytes INTEGER NOT NULL, 
    sha256 VARCHAR(64) NOT NULL, 
    nombre_original VARCHAR(300) NOT NULL, 
    metadata_json TEXT NOT NULL, 
    organizacion_id INTEGER NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(organizacion_id) REFERENCES organizaciones (id) ON DELETE RESTRICT, 
    CONSTRAINT ck_archivo_clave_pertenece_organizacion CHECK (object_key LIKE 'organizaciones/' || organizacion_id || '/%'), 
    CONSTRAINT uq_archivo_organizacion_clave UNIQUE (organizacion_id, object_key)
);

CREATE INDEX ix_archivos_almacenados_organizacion_id ON archivos_almacenados (organizacion_id);

CREATE INDEX ix_archivos_organizacion_categoria ON archivos_almacenados (organizacion_id, categoria);

ALTER TABLE archivos_almacenados ENABLE ROW LEVEL SECURITY;

UPDATE alembic_version SET version_num='72e6f4d8a1c3' WHERE alembic_version.version_num = '9bca2ad1f6e4';

-- Running upgrade 72e6f4d8a1c3 -> a84d2f6b91e0

CREATE TABLE invitaciones_organizacion (
    id SERIAL NOT NULL, 
    email VARCHAR(254) NOT NULL, 
    rol VARCHAR(30) NOT NULL, 
    token_hash VARCHAR(64) NOT NULL, 
    invitada_por_usuario_id INTEGER, 
    aceptada_por_usuario_id INTEGER, 
    expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    accepted_at TIMESTAMP WITHOUT TIME ZONE, 
    revoked_at TIMESTAMP WITHOUT TIME ZONE, 
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    organizacion_id INTEGER NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT ck_invitacion_rol_valido CHECK (rol IN ('administrador', 'miembro', 'lectura')), 
    FOREIGN KEY(organizacion_id) REFERENCES organizaciones (id) ON DELETE RESTRICT, 
    FOREIGN KEY(invitada_por_usuario_id) REFERENCES usuarios (id) ON DELETE SET NULL, 
    FOREIGN KEY(aceptada_por_usuario_id) REFERENCES usuarios (id) ON DELETE SET NULL, 
    CONSTRAINT uq_invitacion_token_hash UNIQUE (token_hash)
);

CREATE INDEX ix_invitaciones_organizacion_organizacion_id ON invitaciones_organizacion (organizacion_id);

CREATE INDEX ix_invitaciones_organizacion_email ON invitaciones_organizacion (organizacion_id, email);

ALTER TABLE invitaciones_organizacion ENABLE ROW LEVEL SECURITY;

UPDATE alembic_version SET version_num='a84d2f6b91e0' WHERE alembic_version.version_num = '72e6f4d8a1c3';

-- Running upgrade a84d2f6b91e0 -> c93e7a4d20f1

ALTER TABLE organizaciones ADD COLUMN creada_por_usuario_id INTEGER;

ALTER TABLE organizaciones ADD CONSTRAINT fk_organizaciones_creada_por_usuario FOREIGN KEY(creada_por_usuario_id) REFERENCES usuarios (id) ON DELETE SET NULL;

CREATE INDEX ix_organizaciones_creada_por_usuario_id ON organizaciones (creada_por_usuario_id);

DO $role$
        BEGIN
          IF NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'cotizat_app') THEN
            CREATE ROLE cotizat_app NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE
              NOINHERIT NOREPLICATION NOBYPASSRLS;
          END IF;
        END
        $role$;

ALTER ROLE cotizat_app NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE
          NOINHERIT NOREPLICATION NOBYPASSRLS;

CREATE SCHEMA IF NOT EXISTS cotizat_security;

ALTER SCHEMA cotizat_security OWNER TO CURRENT_USER;

REVOKE CREATE ON SCHEMA public FROM PUBLIC;

REVOKE ALL ON SCHEMA cotizat_security FROM PUBLIC;

GRANT USAGE ON SCHEMA public, cotizat_security TO cotizat_app;

CREATE OR REPLACE FUNCTION cotizat_security.context_auth_user_id()
        RETURNS text LANGUAGE sql STABLE
        SET search_path = pg_catalog, public
        AS $$
          SELECT NULLIF(pg_catalog.current_setting('cotizat.auth_user_id', true), '')
        $$;

CREATE OR REPLACE FUNCTION cotizat_security.context_email()
        RETURNS text LANGUAGE sql STABLE
        SET search_path = pg_catalog, public
        AS $$
          SELECT LOWER(NULLIF(pg_catalog.current_setting('cotizat.auth_email', true), ''))
        $$;

CREATE OR REPLACE FUNCTION cotizat_security.context_organization_id()
        RETURNS integer LANGUAGE sql STABLE
        SET search_path = pg_catalog, public
        AS $$
          SELECT CASE WHEN value ~ '^[1-9][0-9]*$' THEN value::integer END
          FROM (SELECT pg_catalog.current_setting(
            'cotizat.organization_id', true
          ) AS value) AS configured
        $$;

CREATE OR REPLACE FUNCTION cotizat_security.current_user_id()
        RETURNS integer LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
          SELECT u.id
          FROM public.usuarios AS u
          WHERE u.auth_user_id = NULLIF(
            pg_catalog.current_setting('cotizat.auth_user_id', true), ''
          )
          LIMIT 1
        $$;

CREATE OR REPLACE FUNCTION cotizat_security.current_user_email()
        RETURNS text LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
          SELECT LOWER(u.email)
          FROM public.usuarios AS u
          WHERE u.id = cotizat_security.current_user_id()
          LIMIT 1
        $$;

CREATE OR REPLACE FUNCTION cotizat_security.current_user_is_verified()
        RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
          SELECT COALESCE(u.email_verificado_at IS NOT NULL, FALSE)
          FROM public.usuarios AS u
          WHERE u.id = cotizat_security.current_user_id()
          LIMIT 1
        $$;

CREATE OR REPLACE FUNCTION cotizat_security.membership_role(p_organization_id integer)
        RETURNS text LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
          SELECT m.rol
          FROM public.membresias AS m
          JOIN public.organizaciones AS o ON o.id = m.organizacion_id
          WHERE m.usuario_id = cotizat_security.current_user_id()
            AND m.organizacion_id = p_organization_id
            AND m.activa IS TRUE
            AND o.activa IS TRUE
          LIMIT 1
        $$;

CREATE OR REPLACE FUNCTION cotizat_security.tenant_access(
          p_organization_id integer, p_write boolean
        ) RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
          SELECT COALESCE(
            p_organization_id = cotizat_security.context_organization_id()
            AND cotizat_security.membership_role(p_organization_id) IS NOT NULL
            AND (
              NOT p_write
              OR cotizat_security.membership_role(p_organization_id) <> 'lectura'
            ),
            FALSE
          )
        $$;

CREATE OR REPLACE FUNCTION cotizat_security.can_manage_team(
          p_organization_id integer
        ) RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
          SELECT COALESCE(
            p_organization_id = cotizat_security.context_organization_id()
            AND cotizat_security.membership_role(p_organization_id)
                IN ('propietario', 'administrador'),
            FALSE
          )
        $$;

CREATE OR REPLACE FUNCTION cotizat_security.can_assign_role(
          p_organization_id integer, p_role text
        ) RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
          SELECT COALESCE(
            CASE cotizat_security.membership_role(p_organization_id)
              WHEN 'propietario' THEN p_role IN ('administrador', 'miembro', 'lectura')
              WHEN 'administrador' THEN p_role IN ('miembro', 'lectura')
              ELSE FALSE
            END,
            FALSE
          )
        $$;

CREATE OR REPLACE FUNCTION cotizat_security.can_view_user(p_user_id integer)
        RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
          SELECT COALESCE(
            p_user_id = cotizat_security.current_user_id()
            OR (
              cotizat_security.can_manage_team(
                cotizat_security.context_organization_id()
              )
              AND EXISTS (
                SELECT 1 FROM public.membresias AS m
                WHERE m.usuario_id = p_user_id
                  AND m.organizacion_id =
                      cotizat_security.context_organization_id()
              )
            ),
            FALSE
          )
        $$;

CREATE OR REPLACE FUNCTION cotizat_security.can_create_owner_membership(
          p_organization_id integer, p_user_id integer, p_role text
        ) RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
          SELECT COALESCE(
            p_user_id = cotizat_security.current_user_id()
            AND p_role = 'propietario'
            AND EXISTS (
              SELECT 1 FROM public.organizaciones AS owned
              WHERE owned.id = p_organization_id
                AND owned.creada_por_usuario_id =
                    cotizat_security.current_user_id()
            )
            AND NOT EXISTS (
              SELECT 1 FROM public.membresias AS existing
              WHERE existing.organizacion_id = p_organization_id
            ),
            FALSE
          )
        $$;

CREATE OR REPLACE FUNCTION cotizat_security.has_pending_invitation(
          p_organization_id integer, p_user_id integer, p_role text
        ) RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
          SELECT COALESCE(
            p_user_id = cotizat_security.current_user_id()
            AND EXISTS (
              SELECT 1
              FROM public.invitaciones_organizacion AS invitation
              JOIN public.usuarios AS invited_user
                ON invited_user.id = p_user_id
              WHERE invitation.organizacion_id = p_organization_id
                AND invitation.email = LOWER(invited_user.email)
                AND invited_user.email_verificado_at IS NOT NULL
                AND (p_role IS NULL OR invitation.rol = p_role)
                AND invitation.accepted_at IS NULL
                AND invitation.revoked_at IS NULL
                AND invitation.expires_at > pg_catalog.clock_timestamp()
            ),
            FALSE
          )
        $$;

CREATE OR REPLACE FUNCTION cotizat_security.can_manage_membership(
          p_organization_id integer, p_target_user_id integer, p_target_role text
        ) RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
          SELECT COALESCE(
            CASE cotizat_security.membership_role(p_organization_id)
              WHEN 'propietario' THEN p_target_role <> 'propietario'
              WHEN 'administrador' THEN
                p_target_user_id <> cotizat_security.current_user_id()
                AND p_target_role IN ('miembro', 'lectura')
              ELSE FALSE
            END,
            FALSE
          )
        $$;

ALTER FUNCTION cotizat_security.context_auth_user_id() OWNER TO CURRENT_USER;

REVOKE ALL ON FUNCTION cotizat_security.context_auth_user_id() FROM PUBLIC;

GRANT EXECUTE ON FUNCTION cotizat_security.context_auth_user_id() TO cotizat_app;

ALTER FUNCTION cotizat_security.context_email() OWNER TO CURRENT_USER;

REVOKE ALL ON FUNCTION cotizat_security.context_email() FROM PUBLIC;

GRANT EXECUTE ON FUNCTION cotizat_security.context_email() TO cotizat_app;

ALTER FUNCTION cotizat_security.context_organization_id() OWNER TO CURRENT_USER;

REVOKE ALL ON FUNCTION cotizat_security.context_organization_id() FROM PUBLIC;

GRANT EXECUTE ON FUNCTION cotizat_security.context_organization_id() TO cotizat_app;

ALTER FUNCTION cotizat_security.current_user_id() OWNER TO CURRENT_USER;

REVOKE ALL ON FUNCTION cotizat_security.current_user_id() FROM PUBLIC;

GRANT EXECUTE ON FUNCTION cotizat_security.current_user_id() TO cotizat_app;

ALTER FUNCTION cotizat_security.current_user_email() OWNER TO CURRENT_USER;

REVOKE ALL ON FUNCTION cotizat_security.current_user_email() FROM PUBLIC;

GRANT EXECUTE ON FUNCTION cotizat_security.current_user_email() TO cotizat_app;

ALTER FUNCTION cotizat_security.current_user_is_verified() OWNER TO CURRENT_USER;

REVOKE ALL ON FUNCTION cotizat_security.current_user_is_verified() FROM PUBLIC;

GRANT EXECUTE ON FUNCTION cotizat_security.current_user_is_verified() TO cotizat_app;

ALTER FUNCTION cotizat_security.membership_role(integer) OWNER TO CURRENT_USER;

REVOKE ALL ON FUNCTION cotizat_security.membership_role(integer) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION cotizat_security.membership_role(integer) TO cotizat_app;

ALTER FUNCTION cotizat_security.tenant_access(integer, boolean) OWNER TO CURRENT_USER;

REVOKE ALL ON FUNCTION cotizat_security.tenant_access(integer, boolean) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION cotizat_security.tenant_access(integer, boolean) TO cotizat_app;

ALTER FUNCTION cotizat_security.can_manage_team(integer) OWNER TO CURRENT_USER;

REVOKE ALL ON FUNCTION cotizat_security.can_manage_team(integer) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION cotizat_security.can_manage_team(integer) TO cotizat_app;

ALTER FUNCTION cotizat_security.can_assign_role(integer, text) OWNER TO CURRENT_USER;

REVOKE ALL ON FUNCTION cotizat_security.can_assign_role(integer, text) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION cotizat_security.can_assign_role(integer, text) TO cotizat_app;

ALTER FUNCTION cotizat_security.can_view_user(integer) OWNER TO CURRENT_USER;

REVOKE ALL ON FUNCTION cotizat_security.can_view_user(integer) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION cotizat_security.can_view_user(integer) TO cotizat_app;

ALTER FUNCTION cotizat_security.can_create_owner_membership(integer, integer, text) OWNER TO CURRENT_USER;

REVOKE ALL ON FUNCTION cotizat_security.can_create_owner_membership(integer, integer, text) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION cotizat_security.can_create_owner_membership(integer, integer, text) TO cotizat_app;

ALTER FUNCTION cotizat_security.has_pending_invitation(integer, integer, text) OWNER TO CURRENT_USER;

REVOKE ALL ON FUNCTION cotizat_security.has_pending_invitation(integer, integer, text) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION cotizat_security.has_pending_invitation(integer, integer, text) TO cotizat_app;

ALTER FUNCTION cotizat_security.can_manage_membership(integer, integer, text) OWNER TO CURRENT_USER;

REVOKE ALL ON FUNCTION cotizat_security.can_manage_membership(integer, integer, text) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION cotizat_security.can_manage_membership(integer, integer, text) TO cotizat_app;

REVOKE ALL ON TABLE public.organizaciones FROM PUBLIC;

ALTER TABLE public.organizaciones ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.organizaciones FORCE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.usuarios FROM PUBLIC;

ALTER TABLE public.usuarios ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.usuarios FORCE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.membresias FROM PUBLIC;

ALTER TABLE public.membresias ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.membresias FORCE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.archivos_almacenados FROM PUBLIC;

ALTER TABLE public.archivos_almacenados ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.archivos_almacenados FORCE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.borradores_presupuesto FROM PUBLIC;

ALTER TABLE public.borradores_presupuesto ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.borradores_presupuesto FORCE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.cambio_alcance_items FROM PUBLIC;

ALTER TABLE public.cambio_alcance_items ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.cambio_alcance_items FORCE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.cambios_alcance FROM PUBLIC;

ALTER TABLE public.cambios_alcance ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.cambios_alcance FORCE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.capitulos FROM PUBLIC;

ALTER TABLE public.capitulos ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.capitulos FORCE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.categorias_partidas FROM PUBLIC;

ALTER TABLE public.categorias_partidas ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.categorias_partidas FORCE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.clientes FROM PUBLIC;

ALTER TABLE public.clientes ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.clientes FORCE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.configuracion FROM PUBLIC;

ALTER TABLE public.configuracion ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.configuracion FORCE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.descomposicion_filas FROM PUBLIC;

ALTER TABLE public.descomposicion_filas ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.descomposicion_filas FORCE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.descomposiciones_partida FROM PUBLIC;

ALTER TABLE public.descomposiciones_partida ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.descomposiciones_partida FORCE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.factura_capitulos FROM PUBLIC;

ALTER TABLE public.factura_capitulos ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.factura_capitulos FORCE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.factura_items FROM PUBLIC;

ALTER TABLE public.factura_items ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.factura_items FORCE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.facturas FROM PUBLIC;

ALTER TABLE public.facturas ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.facturas FORCE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.mediciones FROM PUBLIC;

ALTER TABLE public.mediciones ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.mediciones FORCE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.notas_seguimiento FROM PUBLIC;

ALTER TABLE public.notas_seguimiento ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.notas_seguimiento FORCE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.pagos FROM PUBLIC;

ALTER TABLE public.pagos ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.pagos FORCE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.partidas FROM PUBLIC;

ALTER TABLE public.partidas ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.partidas FORCE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.plantillas FROM PUBLIC;

ALTER TABLE public.plantillas ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.plantillas FORCE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.presupuesto_anexos FROM PUBLIC;

ALTER TABLE public.presupuesto_anexos ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.presupuesto_anexos FORCE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.presupuesto_item_productos FROM PUBLIC;

ALTER TABLE public.presupuesto_item_productos ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.presupuesto_item_productos FORCE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.presupuesto_items FROM PUBLIC;

ALTER TABLE public.presupuesto_items ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.presupuesto_items FORCE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.presupuesto_versiones FROM PUBLIC;

ALTER TABLE public.presupuesto_versiones ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.presupuesto_versiones FORCE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.presupuestos FROM PUBLIC;

ALTER TABLE public.presupuestos ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.presupuestos FORCE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.productos FROM PUBLIC;

ALTER TABLE public.productos ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.productos FORCE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.proyectos FROM PUBLIC;

ALTER TABLE public.proyectos ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.proyectos FORCE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.recetas_estancia FROM PUBLIC;

ALTER TABLE public.recetas_estancia ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.recetas_estancia FORCE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.recursos FROM PUBLIC;

ALTER TABLE public.recursos ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.recursos FORCE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.invitaciones_organizacion FROM PUBLIC;

ALTER TABLE public.invitaciones_organizacion ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.invitaciones_organizacion FORCE ROW LEVEL SECURITY;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.archivos_almacenados TO cotizat_app;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.borradores_presupuesto TO cotizat_app;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.cambio_alcance_items TO cotizat_app;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.cambios_alcance TO cotizat_app;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.capitulos TO cotizat_app;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.categorias_partidas TO cotizat_app;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.clientes TO cotizat_app;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.configuracion TO cotizat_app;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.descomposicion_filas TO cotizat_app;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.descomposiciones_partida TO cotizat_app;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.factura_capitulos TO cotizat_app;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.factura_items TO cotizat_app;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.facturas TO cotizat_app;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.mediciones TO cotizat_app;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.notas_seguimiento TO cotizat_app;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.pagos TO cotizat_app;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.partidas TO cotizat_app;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.plantillas TO cotizat_app;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.presupuesto_anexos TO cotizat_app;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.presupuesto_item_productos TO cotizat_app;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.presupuesto_items TO cotizat_app;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.presupuesto_versiones TO cotizat_app;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.presupuestos TO cotizat_app;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.productos TO cotizat_app;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.proyectos TO cotizat_app;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.recetas_estancia TO cotizat_app;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.recursos TO cotizat_app;

GRANT SELECT, INSERT, UPDATE ON TABLE public.organizaciones, public.usuarios, public.membresias TO cotizat_app;

GRANT SELECT ON TABLE public.alembic_version TO cotizat_app;

GRANT SELECT, INSERT ON TABLE public.invitaciones_organizacion TO cotizat_app;

GRANT UPDATE (accepted_at, aceptada_por_usuario_id, revoked_at) ON TABLE public.invitaciones_organizacion TO cotizat_app;

GRANT USAGE, SELECT ON SEQUENCE public.organizaciones_id_seq TO cotizat_app;

GRANT USAGE, SELECT ON SEQUENCE public.usuarios_id_seq TO cotizat_app;

GRANT USAGE, SELECT ON SEQUENCE public.membresias_id_seq TO cotizat_app;

GRANT USAGE, SELECT ON SEQUENCE public.archivos_almacenados_id_seq TO cotizat_app;

GRANT USAGE, SELECT ON SEQUENCE public.borradores_presupuesto_id_seq TO cotizat_app;

GRANT USAGE, SELECT ON SEQUENCE public.cambio_alcance_items_id_seq TO cotizat_app;

GRANT USAGE, SELECT ON SEQUENCE public.cambios_alcance_id_seq TO cotizat_app;

GRANT USAGE, SELECT ON SEQUENCE public.capitulos_id_seq TO cotizat_app;

GRANT USAGE, SELECT ON SEQUENCE public.categorias_partidas_id_seq TO cotizat_app;

GRANT USAGE, SELECT ON SEQUENCE public.clientes_id_seq TO cotizat_app;

GRANT USAGE, SELECT ON SEQUENCE public.configuracion_id_seq TO cotizat_app;

GRANT USAGE, SELECT ON SEQUENCE public.descomposicion_filas_id_seq TO cotizat_app;

GRANT USAGE, SELECT ON SEQUENCE public.descomposiciones_partida_id_seq TO cotizat_app;

GRANT USAGE, SELECT ON SEQUENCE public.factura_capitulos_id_seq TO cotizat_app;

GRANT USAGE, SELECT ON SEQUENCE public.factura_items_id_seq TO cotizat_app;

GRANT USAGE, SELECT ON SEQUENCE public.facturas_id_seq TO cotizat_app;

GRANT USAGE, SELECT ON SEQUENCE public.mediciones_id_seq TO cotizat_app;

GRANT USAGE, SELECT ON SEQUENCE public.notas_seguimiento_id_seq TO cotizat_app;

GRANT USAGE, SELECT ON SEQUENCE public.pagos_id_seq TO cotizat_app;

GRANT USAGE, SELECT ON SEQUENCE public.partidas_id_seq TO cotizat_app;

GRANT USAGE, SELECT ON SEQUENCE public.plantillas_id_seq TO cotizat_app;

GRANT USAGE, SELECT ON SEQUENCE public.presupuesto_anexos_id_seq TO cotizat_app;

GRANT USAGE, SELECT ON SEQUENCE public.presupuesto_item_productos_id_seq TO cotizat_app;

GRANT USAGE, SELECT ON SEQUENCE public.presupuesto_items_id_seq TO cotizat_app;

GRANT USAGE, SELECT ON SEQUENCE public.presupuesto_versiones_id_seq TO cotizat_app;

GRANT USAGE, SELECT ON SEQUENCE public.presupuestos_id_seq TO cotizat_app;

GRANT USAGE, SELECT ON SEQUENCE public.productos_id_seq TO cotizat_app;

GRANT USAGE, SELECT ON SEQUENCE public.proyectos_id_seq TO cotizat_app;

GRANT USAGE, SELECT ON SEQUENCE public.recetas_estancia_id_seq TO cotizat_app;

GRANT USAGE, SELECT ON SEQUENCE public.recursos_id_seq TO cotizat_app;

GRANT USAGE, SELECT ON SEQUENCE public.invitaciones_organizacion_id_seq TO cotizat_app;

DROP POLICY IF EXISTS cotizat_tenant_select ON public.archivos_almacenados;

DROP POLICY IF EXISTS cotizat_tenant_insert ON public.archivos_almacenados;

DROP POLICY IF EXISTS cotizat_tenant_update ON public.archivos_almacenados;

DROP POLICY IF EXISTS cotizat_tenant_delete ON public.archivos_almacenados;

CREATE POLICY cotizat_tenant_select ON public.archivos_almacenados
            FOR SELECT TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, FALSE));

CREATE POLICY cotizat_tenant_insert ON public.archivos_almacenados
            FOR INSERT TO cotizat_app
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_update ON public.archivos_almacenados
            FOR UPDATE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE))
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_delete ON public.archivos_almacenados
            FOR DELETE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE));

DROP POLICY IF EXISTS cotizat_tenant_select ON public.borradores_presupuesto;

DROP POLICY IF EXISTS cotizat_tenant_insert ON public.borradores_presupuesto;

DROP POLICY IF EXISTS cotizat_tenant_update ON public.borradores_presupuesto;

DROP POLICY IF EXISTS cotizat_tenant_delete ON public.borradores_presupuesto;

CREATE POLICY cotizat_tenant_select ON public.borradores_presupuesto
            FOR SELECT TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, FALSE));

CREATE POLICY cotizat_tenant_insert ON public.borradores_presupuesto
            FOR INSERT TO cotizat_app
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_update ON public.borradores_presupuesto
            FOR UPDATE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE))
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_delete ON public.borradores_presupuesto
            FOR DELETE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE));

DROP POLICY IF EXISTS cotizat_tenant_select ON public.cambio_alcance_items;

DROP POLICY IF EXISTS cotizat_tenant_insert ON public.cambio_alcance_items;

DROP POLICY IF EXISTS cotizat_tenant_update ON public.cambio_alcance_items;

DROP POLICY IF EXISTS cotizat_tenant_delete ON public.cambio_alcance_items;

CREATE POLICY cotizat_tenant_select ON public.cambio_alcance_items
            FOR SELECT TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, FALSE));

CREATE POLICY cotizat_tenant_insert ON public.cambio_alcance_items
            FOR INSERT TO cotizat_app
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_update ON public.cambio_alcance_items
            FOR UPDATE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE))
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_delete ON public.cambio_alcance_items
            FOR DELETE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE));

DROP POLICY IF EXISTS cotizat_tenant_select ON public.cambios_alcance;

DROP POLICY IF EXISTS cotizat_tenant_insert ON public.cambios_alcance;

DROP POLICY IF EXISTS cotizat_tenant_update ON public.cambios_alcance;

DROP POLICY IF EXISTS cotizat_tenant_delete ON public.cambios_alcance;

CREATE POLICY cotizat_tenant_select ON public.cambios_alcance
            FOR SELECT TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, FALSE));

CREATE POLICY cotizat_tenant_insert ON public.cambios_alcance
            FOR INSERT TO cotizat_app
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_update ON public.cambios_alcance
            FOR UPDATE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE))
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_delete ON public.cambios_alcance
            FOR DELETE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE));

DROP POLICY IF EXISTS cotizat_tenant_select ON public.capitulos;

DROP POLICY IF EXISTS cotizat_tenant_insert ON public.capitulos;

DROP POLICY IF EXISTS cotizat_tenant_update ON public.capitulos;

DROP POLICY IF EXISTS cotizat_tenant_delete ON public.capitulos;

CREATE POLICY cotizat_tenant_select ON public.capitulos
            FOR SELECT TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, FALSE));

CREATE POLICY cotizat_tenant_insert ON public.capitulos
            FOR INSERT TO cotizat_app
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_update ON public.capitulos
            FOR UPDATE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE))
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_delete ON public.capitulos
            FOR DELETE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE));

DROP POLICY IF EXISTS cotizat_tenant_select ON public.categorias_partidas;

DROP POLICY IF EXISTS cotizat_tenant_insert ON public.categorias_partidas;

DROP POLICY IF EXISTS cotizat_tenant_update ON public.categorias_partidas;

DROP POLICY IF EXISTS cotizat_tenant_delete ON public.categorias_partidas;

CREATE POLICY cotizat_tenant_select ON public.categorias_partidas
            FOR SELECT TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, FALSE));

CREATE POLICY cotizat_tenant_insert ON public.categorias_partidas
            FOR INSERT TO cotizat_app
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_update ON public.categorias_partidas
            FOR UPDATE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE))
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_delete ON public.categorias_partidas
            FOR DELETE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE));

DROP POLICY IF EXISTS cotizat_tenant_select ON public.clientes;

DROP POLICY IF EXISTS cotizat_tenant_insert ON public.clientes;

DROP POLICY IF EXISTS cotizat_tenant_update ON public.clientes;

DROP POLICY IF EXISTS cotizat_tenant_delete ON public.clientes;

CREATE POLICY cotizat_tenant_select ON public.clientes
            FOR SELECT TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, FALSE));

CREATE POLICY cotizat_tenant_insert ON public.clientes
            FOR INSERT TO cotizat_app
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_update ON public.clientes
            FOR UPDATE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE))
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_delete ON public.clientes
            FOR DELETE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE));

DROP POLICY IF EXISTS cotizat_tenant_select ON public.configuracion;

DROP POLICY IF EXISTS cotizat_tenant_insert ON public.configuracion;

DROP POLICY IF EXISTS cotizat_tenant_update ON public.configuracion;

DROP POLICY IF EXISTS cotizat_tenant_delete ON public.configuracion;

CREATE POLICY cotizat_tenant_select ON public.configuracion
            FOR SELECT TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, FALSE));

CREATE POLICY cotizat_tenant_insert ON public.configuracion
            FOR INSERT TO cotizat_app
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_update ON public.configuracion
            FOR UPDATE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE))
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_delete ON public.configuracion
            FOR DELETE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE));

DROP POLICY IF EXISTS cotizat_tenant_select ON public.descomposicion_filas;

DROP POLICY IF EXISTS cotizat_tenant_insert ON public.descomposicion_filas;

DROP POLICY IF EXISTS cotizat_tenant_update ON public.descomposicion_filas;

DROP POLICY IF EXISTS cotizat_tenant_delete ON public.descomposicion_filas;

CREATE POLICY cotizat_tenant_select ON public.descomposicion_filas
            FOR SELECT TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, FALSE));

CREATE POLICY cotizat_tenant_insert ON public.descomposicion_filas
            FOR INSERT TO cotizat_app
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_update ON public.descomposicion_filas
            FOR UPDATE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE))
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_delete ON public.descomposicion_filas
            FOR DELETE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE));

DROP POLICY IF EXISTS cotizat_tenant_select ON public.descomposiciones_partida;

DROP POLICY IF EXISTS cotizat_tenant_insert ON public.descomposiciones_partida;

DROP POLICY IF EXISTS cotizat_tenant_update ON public.descomposiciones_partida;

DROP POLICY IF EXISTS cotizat_tenant_delete ON public.descomposiciones_partida;

CREATE POLICY cotizat_tenant_select ON public.descomposiciones_partida
            FOR SELECT TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, FALSE));

CREATE POLICY cotizat_tenant_insert ON public.descomposiciones_partida
            FOR INSERT TO cotizat_app
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_update ON public.descomposiciones_partida
            FOR UPDATE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE))
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_delete ON public.descomposiciones_partida
            FOR DELETE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE));

DROP POLICY IF EXISTS cotizat_tenant_select ON public.factura_capitulos;

DROP POLICY IF EXISTS cotizat_tenant_insert ON public.factura_capitulos;

DROP POLICY IF EXISTS cotizat_tenant_update ON public.factura_capitulos;

DROP POLICY IF EXISTS cotizat_tenant_delete ON public.factura_capitulos;

CREATE POLICY cotizat_tenant_select ON public.factura_capitulos
            FOR SELECT TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, FALSE));

CREATE POLICY cotizat_tenant_insert ON public.factura_capitulos
            FOR INSERT TO cotizat_app
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_update ON public.factura_capitulos
            FOR UPDATE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE))
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_delete ON public.factura_capitulos
            FOR DELETE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE));

DROP POLICY IF EXISTS cotizat_tenant_select ON public.factura_items;

DROP POLICY IF EXISTS cotizat_tenant_insert ON public.factura_items;

DROP POLICY IF EXISTS cotizat_tenant_update ON public.factura_items;

DROP POLICY IF EXISTS cotizat_tenant_delete ON public.factura_items;

CREATE POLICY cotizat_tenant_select ON public.factura_items
            FOR SELECT TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, FALSE));

CREATE POLICY cotizat_tenant_insert ON public.factura_items
            FOR INSERT TO cotizat_app
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_update ON public.factura_items
            FOR UPDATE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE))
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_delete ON public.factura_items
            FOR DELETE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE));

DROP POLICY IF EXISTS cotizat_tenant_select ON public.facturas;

DROP POLICY IF EXISTS cotizat_tenant_insert ON public.facturas;

DROP POLICY IF EXISTS cotizat_tenant_update ON public.facturas;

DROP POLICY IF EXISTS cotizat_tenant_delete ON public.facturas;

CREATE POLICY cotizat_tenant_select ON public.facturas
            FOR SELECT TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, FALSE));

CREATE POLICY cotizat_tenant_insert ON public.facturas
            FOR INSERT TO cotizat_app
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_update ON public.facturas
            FOR UPDATE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE))
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_delete ON public.facturas
            FOR DELETE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE));

DROP POLICY IF EXISTS cotizat_tenant_select ON public.mediciones;

DROP POLICY IF EXISTS cotizat_tenant_insert ON public.mediciones;

DROP POLICY IF EXISTS cotizat_tenant_update ON public.mediciones;

DROP POLICY IF EXISTS cotizat_tenant_delete ON public.mediciones;

CREATE POLICY cotizat_tenant_select ON public.mediciones
            FOR SELECT TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, FALSE));

CREATE POLICY cotizat_tenant_insert ON public.mediciones
            FOR INSERT TO cotizat_app
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_update ON public.mediciones
            FOR UPDATE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE))
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_delete ON public.mediciones
            FOR DELETE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE));

DROP POLICY IF EXISTS cotizat_tenant_select ON public.notas_seguimiento;

DROP POLICY IF EXISTS cotizat_tenant_insert ON public.notas_seguimiento;

DROP POLICY IF EXISTS cotizat_tenant_update ON public.notas_seguimiento;

DROP POLICY IF EXISTS cotizat_tenant_delete ON public.notas_seguimiento;

CREATE POLICY cotizat_tenant_select ON public.notas_seguimiento
            FOR SELECT TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, FALSE));

CREATE POLICY cotizat_tenant_insert ON public.notas_seguimiento
            FOR INSERT TO cotizat_app
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_update ON public.notas_seguimiento
            FOR UPDATE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE))
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_delete ON public.notas_seguimiento
            FOR DELETE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE));

DROP POLICY IF EXISTS cotizat_tenant_select ON public.pagos;

DROP POLICY IF EXISTS cotizat_tenant_insert ON public.pagos;

DROP POLICY IF EXISTS cotizat_tenant_update ON public.pagos;

DROP POLICY IF EXISTS cotizat_tenant_delete ON public.pagos;

CREATE POLICY cotizat_tenant_select ON public.pagos
            FOR SELECT TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, FALSE));

CREATE POLICY cotizat_tenant_insert ON public.pagos
            FOR INSERT TO cotizat_app
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_update ON public.pagos
            FOR UPDATE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE))
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_delete ON public.pagos
            FOR DELETE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE));

DROP POLICY IF EXISTS cotizat_tenant_select ON public.partidas;

DROP POLICY IF EXISTS cotizat_tenant_insert ON public.partidas;

DROP POLICY IF EXISTS cotizat_tenant_update ON public.partidas;

DROP POLICY IF EXISTS cotizat_tenant_delete ON public.partidas;

CREATE POLICY cotizat_tenant_select ON public.partidas
            FOR SELECT TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, FALSE));

CREATE POLICY cotizat_tenant_insert ON public.partidas
            FOR INSERT TO cotizat_app
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_update ON public.partidas
            FOR UPDATE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE))
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_delete ON public.partidas
            FOR DELETE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE));

DROP POLICY IF EXISTS cotizat_tenant_select ON public.plantillas;

DROP POLICY IF EXISTS cotizat_tenant_insert ON public.plantillas;

DROP POLICY IF EXISTS cotizat_tenant_update ON public.plantillas;

DROP POLICY IF EXISTS cotizat_tenant_delete ON public.plantillas;

CREATE POLICY cotizat_tenant_select ON public.plantillas
            FOR SELECT TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, FALSE));

CREATE POLICY cotizat_tenant_insert ON public.plantillas
            FOR INSERT TO cotizat_app
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_update ON public.plantillas
            FOR UPDATE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE))
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_delete ON public.plantillas
            FOR DELETE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE));

DROP POLICY IF EXISTS cotizat_tenant_select ON public.presupuesto_anexos;

DROP POLICY IF EXISTS cotizat_tenant_insert ON public.presupuesto_anexos;

DROP POLICY IF EXISTS cotizat_tenant_update ON public.presupuesto_anexos;

DROP POLICY IF EXISTS cotizat_tenant_delete ON public.presupuesto_anexos;

CREATE POLICY cotizat_tenant_select ON public.presupuesto_anexos
            FOR SELECT TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, FALSE));

CREATE POLICY cotizat_tenant_insert ON public.presupuesto_anexos
            FOR INSERT TO cotizat_app
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_update ON public.presupuesto_anexos
            FOR UPDATE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE))
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_delete ON public.presupuesto_anexos
            FOR DELETE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE));

DROP POLICY IF EXISTS cotizat_tenant_select ON public.presupuesto_item_productos;

DROP POLICY IF EXISTS cotizat_tenant_insert ON public.presupuesto_item_productos;

DROP POLICY IF EXISTS cotizat_tenant_update ON public.presupuesto_item_productos;

DROP POLICY IF EXISTS cotizat_tenant_delete ON public.presupuesto_item_productos;

CREATE POLICY cotizat_tenant_select ON public.presupuesto_item_productos
            FOR SELECT TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, FALSE));

CREATE POLICY cotizat_tenant_insert ON public.presupuesto_item_productos
            FOR INSERT TO cotizat_app
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_update ON public.presupuesto_item_productos
            FOR UPDATE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE))
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_delete ON public.presupuesto_item_productos
            FOR DELETE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE));

DROP POLICY IF EXISTS cotizat_tenant_select ON public.presupuesto_items;

DROP POLICY IF EXISTS cotizat_tenant_insert ON public.presupuesto_items;

DROP POLICY IF EXISTS cotizat_tenant_update ON public.presupuesto_items;

DROP POLICY IF EXISTS cotizat_tenant_delete ON public.presupuesto_items;

CREATE POLICY cotizat_tenant_select ON public.presupuesto_items
            FOR SELECT TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, FALSE));

CREATE POLICY cotizat_tenant_insert ON public.presupuesto_items
            FOR INSERT TO cotizat_app
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_update ON public.presupuesto_items
            FOR UPDATE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE))
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_delete ON public.presupuesto_items
            FOR DELETE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE));

DROP POLICY IF EXISTS cotizat_tenant_select ON public.presupuesto_versiones;

DROP POLICY IF EXISTS cotizat_tenant_insert ON public.presupuesto_versiones;

DROP POLICY IF EXISTS cotizat_tenant_update ON public.presupuesto_versiones;

DROP POLICY IF EXISTS cotizat_tenant_delete ON public.presupuesto_versiones;

CREATE POLICY cotizat_tenant_select ON public.presupuesto_versiones
            FOR SELECT TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, FALSE));

CREATE POLICY cotizat_tenant_insert ON public.presupuesto_versiones
            FOR INSERT TO cotizat_app
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_update ON public.presupuesto_versiones
            FOR UPDATE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE))
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_delete ON public.presupuesto_versiones
            FOR DELETE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE));

DROP POLICY IF EXISTS cotizat_tenant_select ON public.presupuestos;

DROP POLICY IF EXISTS cotizat_tenant_insert ON public.presupuestos;

DROP POLICY IF EXISTS cotizat_tenant_update ON public.presupuestos;

DROP POLICY IF EXISTS cotizat_tenant_delete ON public.presupuestos;

CREATE POLICY cotizat_tenant_select ON public.presupuestos
            FOR SELECT TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, FALSE));

CREATE POLICY cotizat_tenant_insert ON public.presupuestos
            FOR INSERT TO cotizat_app
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_update ON public.presupuestos
            FOR UPDATE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE))
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_delete ON public.presupuestos
            FOR DELETE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE));

DROP POLICY IF EXISTS cotizat_tenant_select ON public.productos;

DROP POLICY IF EXISTS cotizat_tenant_insert ON public.productos;

DROP POLICY IF EXISTS cotizat_tenant_update ON public.productos;

DROP POLICY IF EXISTS cotizat_tenant_delete ON public.productos;

CREATE POLICY cotizat_tenant_select ON public.productos
            FOR SELECT TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, FALSE));

CREATE POLICY cotizat_tenant_insert ON public.productos
            FOR INSERT TO cotizat_app
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_update ON public.productos
            FOR UPDATE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE))
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_delete ON public.productos
            FOR DELETE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE));

DROP POLICY IF EXISTS cotizat_tenant_select ON public.proyectos;

DROP POLICY IF EXISTS cotizat_tenant_insert ON public.proyectos;

DROP POLICY IF EXISTS cotizat_tenant_update ON public.proyectos;

DROP POLICY IF EXISTS cotizat_tenant_delete ON public.proyectos;

CREATE POLICY cotizat_tenant_select ON public.proyectos
            FOR SELECT TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, FALSE));

CREATE POLICY cotizat_tenant_insert ON public.proyectos
            FOR INSERT TO cotizat_app
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_update ON public.proyectos
            FOR UPDATE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE))
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_delete ON public.proyectos
            FOR DELETE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE));

DROP POLICY IF EXISTS cotizat_tenant_select ON public.recetas_estancia;

DROP POLICY IF EXISTS cotizat_tenant_insert ON public.recetas_estancia;

DROP POLICY IF EXISTS cotizat_tenant_update ON public.recetas_estancia;

DROP POLICY IF EXISTS cotizat_tenant_delete ON public.recetas_estancia;

CREATE POLICY cotizat_tenant_select ON public.recetas_estancia
            FOR SELECT TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, FALSE));

CREATE POLICY cotizat_tenant_insert ON public.recetas_estancia
            FOR INSERT TO cotizat_app
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_update ON public.recetas_estancia
            FOR UPDATE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE))
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_delete ON public.recetas_estancia
            FOR DELETE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE));

DROP POLICY IF EXISTS cotizat_tenant_select ON public.recursos;

DROP POLICY IF EXISTS cotizat_tenant_insert ON public.recursos;

DROP POLICY IF EXISTS cotizat_tenant_update ON public.recursos;

DROP POLICY IF EXISTS cotizat_tenant_delete ON public.recursos;

CREATE POLICY cotizat_tenant_select ON public.recursos
            FOR SELECT TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, FALSE));

CREATE POLICY cotizat_tenant_insert ON public.recursos
            FOR INSERT TO cotizat_app
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_update ON public.recursos
            FOR UPDATE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE))
            WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE POLICY cotizat_tenant_delete ON public.recursos
            FOR DELETE TO cotizat_app
            USING (cotizat_security.tenant_access(organizacion_id, TRUE));

DROP POLICY IF EXISTS cotizat_user_select ON public.usuarios;

DROP POLICY IF EXISTS cotizat_user_insert ON public.usuarios;

DROP POLICY IF EXISTS cotizat_user_update ON public.usuarios;

DROP POLICY IF EXISTS cotizat_org_select ON public.organizaciones;

DROP POLICY IF EXISTS cotizat_org_insert ON public.organizaciones;

DROP POLICY IF EXISTS cotizat_org_update ON public.organizaciones;

DROP POLICY IF EXISTS cotizat_membership_select ON public.membresias;

DROP POLICY IF EXISTS cotizat_membership_insert ON public.membresias;

DROP POLICY IF EXISTS cotizat_membership_update ON public.membresias;

DROP POLICY IF EXISTS cotizat_invitation_select_manager ON public.invitaciones_organizacion;

DROP POLICY IF EXISTS cotizat_invitation_select_recipient ON public.invitaciones_organizacion;

DROP POLICY IF EXISTS cotizat_invitation_insert ON public.invitaciones_organizacion;

DROP POLICY IF EXISTS cotizat_invitation_update_manager ON public.invitaciones_organizacion;

DROP POLICY IF EXISTS cotizat_invitation_update_recipient ON public.invitaciones_organizacion;

CREATE POLICY cotizat_user_select ON public.usuarios
        FOR SELECT TO cotizat_app
        USING ((
      auth_user_id = cotizat_security.context_auth_user_id()
      OR (
        auth_user_id IS NULL
        AND LOWER(email) = cotizat_security.context_email()
      )
    ) OR cotizat_security.can_view_user(id));

CREATE POLICY cotizat_user_insert ON public.usuarios
        FOR INSERT TO cotizat_app
        WITH CHECK (
          auth_user_id = cotizat_security.context_auth_user_id()
          AND LOWER(email) = cotizat_security.context_email()
        );

CREATE POLICY cotizat_user_update ON public.usuarios
        FOR UPDATE TO cotizat_app
        USING (
      auth_user_id = cotizat_security.context_auth_user_id()
      OR (
        auth_user_id IS NULL
        AND LOWER(email) = cotizat_security.context_email()
      )
    )
        WITH CHECK (
          auth_user_id = cotizat_security.context_auth_user_id()
          AND LOWER(email) = cotizat_security.context_email()
        );

CREATE POLICY cotizat_org_select ON public.organizaciones
        FOR SELECT TO cotizat_app
        USING (cotizat_security.membership_role(id) IS NOT NULL);

CREATE POLICY cotizat_org_insert ON public.organizaciones
        FOR INSERT TO cotizat_app
        WITH CHECK (
          cotizat_security.context_auth_user_id() IS NOT NULL
          AND creada_por_usuario_id = cotizat_security.current_user_id()
        );

CREATE POLICY cotizat_org_update ON public.organizaciones
        FOR UPDATE TO cotizat_app
        USING (cotizat_security.can_manage_team(id))
        WITH CHECK (cotizat_security.can_manage_team(id));

CREATE POLICY cotizat_membership_select ON public.membresias
        FOR SELECT TO cotizat_app
        USING (
          usuario_id = cotizat_security.current_user_id()
          OR cotizat_security.can_manage_team(organizacion_id)
        );

CREATE POLICY cotizat_membership_insert ON public.membresias
        FOR INSERT TO cotizat_app
        WITH CHECK (
          cotizat_security.can_create_owner_membership(
            organizacion_id, usuario_id, rol
          )
          OR cotizat_security.has_pending_invitation(
            organizacion_id, usuario_id, rol
          )
        );

CREATE POLICY cotizat_membership_update ON public.membresias
        FOR UPDATE TO cotizat_app
        USING (
          cotizat_security.can_manage_membership(
            organizacion_id, usuario_id, rol
          )
          OR cotizat_security.has_pending_invitation(
            organizacion_id, usuario_id, NULL
          )
        )
        WITH CHECK (
          (
            cotizat_security.can_manage_membership(
              organizacion_id, usuario_id, rol
            )
            AND cotizat_security.can_assign_role(organizacion_id, rol)
          )
          OR (
            activa IS TRUE
            AND cotizat_security.has_pending_invitation(
              organizacion_id, usuario_id, rol
            )
          )
        );

CREATE POLICY cotizat_invitation_select_manager
        ON public.invitaciones_organizacion
        FOR SELECT TO cotizat_app
        USING (cotizat_security.can_manage_team(organizacion_id));

CREATE POLICY cotizat_invitation_select_recipient
        ON public.invitaciones_organizacion
        FOR SELECT TO cotizat_app USING (
      email = cotizat_security.current_user_email()
      AND cotizat_security.current_user_is_verified()
      AND accepted_at IS NULL
      AND revoked_at IS NULL
      AND expires_at > pg_catalog.clock_timestamp()
    );

CREATE POLICY cotizat_invitation_insert
        ON public.invitaciones_organizacion
        FOR INSERT TO cotizat_app
        WITH CHECK (
          cotizat_security.can_manage_team(organizacion_id)
          AND cotizat_security.can_assign_role(organizacion_id, rol)
        );

CREATE POLICY cotizat_invitation_update_manager
        ON public.invitaciones_organizacion
        FOR UPDATE TO cotizat_app
        USING (cotizat_security.can_manage_team(organizacion_id))
        WITH CHECK (
          cotizat_security.can_manage_team(organizacion_id)
          AND cotizat_security.can_assign_role(organizacion_id, rol)
        );

CREATE POLICY cotizat_invitation_update_recipient
        ON public.invitaciones_organizacion
        FOR UPDATE TO cotizat_app
        USING (
      email = cotizat_security.current_user_email()
      AND cotizat_security.current_user_is_verified()
      AND accepted_at IS NULL
      AND revoked_at IS NULL
      AND expires_at > pg_catalog.clock_timestamp()
    )
        WITH CHECK (
          email = cotizat_security.current_user_email()
          AND accepted_at IS NOT NULL
          AND aceptada_por_usuario_id = cotizat_security.current_user_id()
          AND revoked_at IS NULL
          AND expires_at > pg_catalog.clock_timestamp()
        );

UPDATE alembic_version SET version_num='c93e7a4d20f1' WHERE alembic_version.version_num = 'a84d2f6b91e0';

COMMIT;

