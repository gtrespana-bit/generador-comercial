-- CotizaT — actualización de b6d9e4c2a8f1 a d2a7c9e4f1b3
-- Registro de auditoría inmutable (E4-026 / E4-027) + baja completa.
--
-- Crea `eventos_auditoria` (quién hizo qué: cambios de negocio, sesiones y
-- acciones sensibles) con RLS: INSERT tenant, SELECT tenant u operador, y
-- SIN GRANT de UPDATE/DELETE (inmutable por construcción). Añade la función
-- SECURITY DEFINER `cotizat_security.registrar_evento_global` (eventos de
-- sesión sin organización, lista cerrada de acciones) y ACTUALIZA
-- `cotizat_security.baja_organizacion` para borrar también `compras_plan`
-- (bug latente: una organización con compras no podía darse de baja) y
-- `eventos_auditoria`.
--
-- Generado desde la propia migración con `alembic upgrade --sql`, no
-- transcrito a mano: este fichero no puede divergir del código.
--
-- Ejecutar una sola vez con el rol administrativo de Supabase/PostgreSQL.
-- El rol que lo ejecute será el propietario (`OWNER TO CURRENT_USER`) de las
-- funciones SECURITY DEFINER, y por tanto el privilegio con el que corren:
-- debe ser el rol administrativo, nunca `cotizat_app`.

BEGIN;

DO $guarda$
DECLARE
  v_version text;
BEGIN
  SELECT version_num INTO v_version FROM public.alembic_version LIMIT 1;
  IF v_version IS DISTINCT FROM 'b6d9e4c2a8f1' THEN
    RAISE EXCEPTION
      'Se esperaba alembic_version b6d9e4c2a8f1 antes de d2a7c9e4f1b3; se encontró %',
      COALESCE(v_version, '<vacío>');
  END IF;
END
$guarda$;


-- Running upgrade b6d9e4c2a8f1 -> d2a7c9e4f1b3

CREATE TABLE eventos_auditoria (
    id SERIAL NOT NULL,
    organizacion_id INTEGER,
    actor_email VARCHAR(254) DEFAULT '' NOT NULL,
    actor_rol VARCHAR(20) DEFAULT '' NOT NULL,
    accion VARCHAR(60) NOT NULL,
    entidad VARCHAR(40) DEFAULT '' NOT NULL,
    entidad_id INTEGER,
    detalle TEXT DEFAULT '{}' NOT NULL,
    ip_hash VARCHAR(64) DEFAULT '' NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(organizacion_id) REFERENCES organizaciones (id) ON DELETE RESTRICT
);

CREATE INDEX ix_eventos_auditoria_organizacion_id ON eventos_auditoria (organizacion_id);

CREATE INDEX ix_eventos_auditoria_accion ON eventos_auditoria (accion);

CREATE INDEX ix_eventos_auditoria_org_fecha ON eventos_auditoria (organizacion_id, created_at);

REVOKE ALL ON TABLE public.eventos_auditoria FROM PUBLIC;

ALTER TABLE public.eventos_auditoria ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.eventos_auditoria FORCE ROW LEVEL SECURITY;

GRANT SELECT, INSERT ON TABLE public.eventos_auditoria TO cotizat_app;

GRANT USAGE, SELECT ON SEQUENCE public.eventos_auditoria_id_seq TO cotizat_app;

DROP POLICY IF EXISTS cotizat_evento_select_tenant ON public.eventos_auditoria;

CREATE POLICY cotizat_evento_select_tenant ON public.eventos_auditoria FOR SELECT TO cotizat_app USING (organizacion_id IS NOT NULL AND cotizat_security.tenant_access(organizacion_id, FALSE));

DROP POLICY IF EXISTS cotizat_evento_select_operator ON public.eventos_auditoria;

CREATE POLICY cotizat_evento_select_operator ON public.eventos_auditoria FOR SELECT TO cotizat_app USING (
  COALESCE(
    pg_catalog.current_setting('cotizat.es_operador', true) = 'on',
    FALSE
  )
);

DROP POLICY IF EXISTS cotizat_evento_insert_tenant ON public.eventos_auditoria;

CREATE POLICY cotizat_evento_insert_tenant ON public.eventos_auditoria FOR INSERT TO cotizat_app WITH CHECK (organizacion_id IS NOT NULL AND cotizat_security.tenant_access(organizacion_id, TRUE));

CREATE OR REPLACE FUNCTION cotizat_security.registrar_evento_global(
  p_email text,
  p_accion text,
  p_ip_hash text DEFAULT '',
  p_detalle text DEFAULT '{}'
) RETURNS boolean LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
BEGIN
  IF p_accion IS NULL
     OR p_accion NOT IN ('sesion.login', 'sesion.logout', 'cuenta.clave_cambiada', 'organizacion.baja') THEN
    RETURN FALSE;
  END IF;

  INSERT INTO public.eventos_auditoria (
    organizacion_id, actor_email, actor_rol, accion, entidad,
    detalle, ip_hash, created_at
  ) VALUES (
    NULL,
    LEFT(LOWER(COALESCE(p_email, '')), 254),
    '',
    p_accion,
    '',
    LEFT(COALESCE(NULLIF(p_detalle, ''), '{}'), 2000),
    LEFT(COALESCE(p_ip_hash, ''), 64),
    clock_timestamp()
  );
  RETURN TRUE;
END
$$;

ALTER FUNCTION cotizat_security.registrar_evento_global(text, text, text, text) OWNER TO CURRENT_USER;

REVOKE ALL ON FUNCTION cotizat_security.registrar_evento_global(text, text, text, text) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION cotizat_security.registrar_evento_global(text, text, text, text) TO cotizat_app;

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

  DELETE FROM public.compras_plan
    WHERE organizacion_id = p_organization_id;
  DELETE FROM public.eventos_auditoria
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

GRANT EXECUTE ON FUNCTION cotizat_security.baja_organizacion(integer) TO cotizat_app;

UPDATE alembic_version SET version_num='d2a7c9e4f1b3' WHERE alembic_version.version_num = 'b6d9e4c2a8f1';

COMMIT;
