-- CotizaT — actualización de p3f7a1c9d2e4 a q5e1c8a9d3f7
-- Borrado autoservicio de cuenta, supresión de identificadores y reintento
-- de eliminación en Supabase Auth. Ejecutar una sola vez en SQL Editor como
-- administrador únicamente si public.alembic_version indica p3f7a1c9d2e4.
BEGIN;

DO $$
BEGIN
  IF (SELECT version_num FROM public.alembic_version LIMIT 1) IS DISTINCT FROM 'p3f7a1c9d2e4' THEN
    RAISE EXCEPTION 'Head inesperado; se esperaba p3f7a1c9d2e4';
  END IF;
END $$;

-- Running upgrade p3f7a1c9d2e4 -> q5e1c8a9d3f7

ALTER TABLE public.usuarios ADD COLUMN borrado_pendiente BOOLEAN DEFAULT false NOT NULL;

CREATE OR REPLACE FUNCTION cotizat_security.obtener_comprobantes_borrado_usuario(
          p_usuario_id integer,
          p_auth_user_id text,
          p_email text
        ) RETURNS TABLE(organizacion_id integer, referencia text)
        LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
        BEGIN
          IF COALESCE(pg_catalog.current_setting('cotizat.auth_user_id', true), '')
               IS DISTINCT FROM COALESCE(p_auth_user_id, '')
             OR lower(COALESCE(pg_catalog.current_setting('cotizat.auth_email', true), ''))
               IS DISTINCT FROM lower(COALESCE(p_email, ''))
             OR NOT EXISTS (
               SELECT 1 FROM public.usuarios
               WHERE id = p_usuario_id AND auth_user_id = p_auth_user_id
                 AND lower(email) = lower(p_email) AND activo IS TRUE
             ) THEN
            RAISE EXCEPTION 'La cuenta de la solicitud no coincide con la sesión.'
              USING ERRCODE = '42501';
          END IF;
          RETURN QUERY
          SELECT c.organizacion_id, c.comprobante_reference
          FROM public.compras_plan AS c
          WHERE c.comprobante_reference <> ''
            AND (c.creada_por_usuario_id = p_usuario_id
                 OR lower(c.creada_por_email) = lower(p_email));
        END;
        $$;;

REVOKE ALL ON FUNCTION cotizat_security.obtener_comprobantes_borrado_usuario(integer, text, text) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION cotizat_security.obtener_comprobantes_borrado_usuario(integer, text, text) TO cotizat_app;

CREATE OR REPLACE FUNCTION cotizat_security.suprimir_datos_personales_usuario(
          p_usuario_id integer,
          p_auth_user_id text,
          p_email text
        ) RETURNS void
        LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
        DECLARE
          v_nombre text;
          v_email text;
          v_anonymizado text;
        BEGIN
          IF COALESCE(pg_catalog.current_setting('cotizat.auth_user_id', true), '')
               IS DISTINCT FROM COALESCE(p_auth_user_id, '')
             OR lower(COALESCE(pg_catalog.current_setting('cotizat.auth_email', true), ''))
               IS DISTINCT FROM lower(COALESCE(p_email, '')) THEN
            RAISE EXCEPTION 'La cuenta de la solicitud no coincide con la sesión.'
              USING ERRCODE = '42501';
          END IF;

          SELECT nombre, email INTO v_nombre, v_email
          FROM public.usuarios
          WHERE id = p_usuario_id AND auth_user_id = p_auth_user_id
          FOR UPDATE;
          IF NOT FOUND OR lower(v_email) IS DISTINCT FROM lower(p_email) THEN
            RAISE EXCEPTION 'La cuenta ya no está disponible para borrado.'
              USING ERRCODE = '42501';
          END IF;

          IF EXISTS (
            SELECT 1 FROM public.membresias
            WHERE usuario_id = p_usuario_id AND activa IS TRUE
              AND rol = 'propietario'
          ) THEN
            RAISE EXCEPTION 'Primero deben eliminarse las organizaciones propias.'
              USING ERRCODE = '23503';
          END IF;

          v_anonymizado := 'borrado+' || replace(p_auth_user_id, '-', '')
                            || '@invalid.cotizat';

          -- Conserva las trazas de auditoría, pero desvincula al titular.
          UPDATE public.eventos_auditoria SET
            actor_email = CASE WHEN lower(actor_email) = lower(p_email) THEN '' ELSE actor_email END,
            ip_hash = CASE WHEN lower(actor_email) = lower(p_email) THEN '' ELSE ip_hash END,
            detalle = '{}'
            WHERE lower(actor_email) = lower(p_email)
               OR position(lower(p_email) in lower(detalle)) > 0;
          UPDATE public.eventos_producto SET
            actor_email = CASE WHEN lower(actor_email) = lower(p_email) THEN '' ELSE actor_email END,
            detalle = '{}'
            WHERE lower(actor_email) = lower(p_email)
               OR position(lower(p_email) in lower(detalle)) > 0;
          UPDATE public.eventos_admin SET
            operador_email = CASE WHEN lower(operador_email) = lower(p_email) THEN '' ELSE operador_email END,
            ip_hash = CASE WHEN lower(operador_email) = lower(p_email) THEN '' ELSE ip_hash END,
            detalle = '{}'
            WHERE lower(operador_email) = lower(p_email)
               OR position(lower(p_email) in lower(detalle)) > 0;

          -- Suprime también los metadatos de los comprobantes privados que
          -- el servicio ya eliminó del almacenamiento externo.
          DELETE FROM public.archivos_almacenados AS a
          USING public.compras_plan AS c
          WHERE c.comprobante_reference = 'storage://' || a.object_key
            AND (c.creada_por_usuario_id = p_usuario_id
                 OR lower(c.creada_por_email) = lower(p_email));

          -- Se conservan, si procede, solo los campos contables mínimos; se
          -- eliminan pruebas de pago, adjuntos e identificadores enlazables.
          UPDATE public.compras_plan SET
            creada_por_usuario_id = NULL,
            creada_por_email = '',
            revisado_por_email = '',
            datos_verificacion = '{}',
            comprobante_reference = '',
            comprobante_nombre = '',
            comprobante_mime = '',
            stripe_checkout_session_id = NULL,
            stripe_subscription_id = NULL,
            stripe_customer_id = NULL,
            stripe_payment_intent_id = NULL,
            stripe_invoice_id = NULL
            WHERE creada_por_usuario_id = p_usuario_id
               OR lower(creada_por_email) = lower(p_email)
               OR lower(revisado_por_email) = lower(p_email);
          UPDATE public.organizaciones SET creada_por_usuario_id = NULL
            WHERE creada_por_usuario_id = p_usuario_id;
          UPDATE public.enlaces_propuesta SET creado_por_usuario_id = NULL
            WHERE creado_por_usuario_id = p_usuario_id;

          -- Mensajes de soporte y conversaciones contienen contenido escrito
          -- por la persona; se eliminan, no solo se desvinculan.
          UPDATE public.mensajes_soporte SET
            atendido_por_email = CASE
              WHEN lower(atendido_por_email) = lower(p_email) THEN ''
              ELSE atendido_por_email END,
            nota_interna = CASE
              WHEN position(lower(p_email) in lower(nota_interna)) > 0 THEN ''
              ELSE nota_interna END
            WHERE lower(atendido_por_email) = lower(p_email)
               OR position(lower(p_email) in lower(nota_interna)) > 0;
          DELETE FROM public.mensajes_soporte
            WHERE usuario_id = p_usuario_id OR lower(email) = lower(p_email);
          DELETE FROM public.conversaciones_ia
            WHERE usuario_id = p_usuario_id OR lower(usuario_email) = lower(p_email);
          DELETE FROM public.invitaciones_organizacion
            WHERE lower(email) = lower(p_email)
               OR invitada_por_usuario_id = p_usuario_id
               OR aceptada_por_usuario_id = p_usuario_id;
          DELETE FROM public.consentimientos WHERE lower(email) = lower(p_email);
          DELETE FROM public.pruebas_concedidas
            WHERE lower(email_original) = lower(p_email)
               OR lower(email_normalizado) = lower(p_email);

          -- Esta telemetría operativa no es contenido de negocio: se conserva
          -- el diagnóstico agregable y se purga cualquier texto identificador.
          UPDATE public.errores_internos SET
            usuario_email = '', usuario_nombre = '',
            mensaje = replace(mensaje, p_email, '[suprimido]'),
            traza = replace(traza, p_email, '[suprimido]')
            WHERE lower(usuario_email) = lower(p_email);

          -- Si la persona era operadora, se revoca el acceso y se retira su
          -- email de las filas históricas de administración.
          UPDATE public.operadores_producto SET
            email = v_anonymizado, activo = FALSE, notas = '', creado_por_email = ''
            WHERE lower(email) = lower(p_email);

          -- Retira al usuario de las empresas restantes y conserva solo un
          -- tombstone sin nombre/email para que Auth Admin pueda reintentarse.
          DELETE FROM public.membresias WHERE usuario_id = p_usuario_id;
          UPDATE public.usuarios SET
            email = v_anonymizado,
            nombre = '',
            activo = FALSE,
            borrado_pendiente = TRUE,
            acepto_terminos_version = '',
            acepto_terminos_at = NULL,
            email_verificado_at = NULL,
            ultimo_acceso_at = NULL,
            updated_at = clock_timestamp()
          WHERE id = p_usuario_id;
        END;
        $$;;

REVOKE ALL ON FUNCTION cotizat_security.suprimir_datos_personales_usuario(integer, text, text) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION cotizat_security.suprimir_datos_personales_usuario(integer, text, text) TO cotizat_app;

CREATE OR REPLACE FUNCTION cotizat_security.desvincular_eventos_admin_baja()
        RETURNS trigger
        LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
        BEGIN
          UPDATE public.eventos_admin
          SET organizacion_id = NULL
          WHERE organizacion_id = OLD.id;
          RETURN OLD;
        END;
        $$;;

CREATE TRIGGER trg_desvincular_eventos_admin_baja
        BEFORE DELETE ON public.organizaciones
        FOR EACH ROW EXECUTE FUNCTION cotizat_security.desvincular_eventos_admin_baja();

CREATE OR REPLACE FUNCTION cotizat_security.obtener_borrados_pendientes(
          p_limite integer DEFAULT 50
        ) RETURNS TABLE(usuario_id integer, auth_user_id text)
        LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
        BEGIN
          IF COALESCE(pg_catalog.current_setting('cotizat.es_operador', true), '')
               IS DISTINCT FROM 'on' THEN
            RAISE EXCEPTION 'No autorizado para consultar borrados pendientes.'
              USING ERRCODE = '42501';
          END IF;
          RETURN QUERY
          SELECT u.id, u.auth_user_id
          FROM public.usuarios AS u
          WHERE u.borrado_pendiente IS TRUE
          ORDER BY u.id
          LIMIT GREATEST(1, LEAST(COALESCE(p_limite, 50), 200));
        END;
        $$;;

REVOKE ALL ON FUNCTION cotizat_security.obtener_borrados_pendientes(integer) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION cotizat_security.obtener_borrados_pendientes(integer) TO cotizat_app;

CREATE OR REPLACE FUNCTION cotizat_security.finalizar_borrado_cuenta(
          p_usuario_id integer,
          p_auth_user_id text
        ) RETURNS boolean
        LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
        DECLARE v_borrada integer;
        BEGIN
          IF COALESCE(pg_catalog.current_setting('cotizat.auth_user_id', true), '')
               IS DISTINCT FROM COALESCE(p_auth_user_id, '')
             AND COALESCE(pg_catalog.current_setting('cotizat.es_operador', true), '')
               IS DISTINCT FROM 'on' THEN
            RAISE EXCEPTION 'No autorizado para finalizar el borrado.'
              USING ERRCODE = '42501';
          END IF;
          DELETE FROM public.usuarios
          WHERE id = p_usuario_id
            AND auth_user_id = p_auth_user_id
            AND borrado_pendiente IS TRUE;
          GET DIAGNOSTICS v_borrada = ROW_COUNT;
          RETURN v_borrada = 1;
        END;
        $$;;

REVOKE ALL ON FUNCTION cotizat_security.finalizar_borrado_cuenta(integer, text) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION cotizat_security.finalizar_borrado_cuenta(integer, text) TO cotizat_app;

UPDATE public.alembic_version SET version_num='q5e1c8a9d3f7' WHERE alembic_version.version_num = 'p3f7a1c9d2e4';

COMMIT;


-- Verificar: SELECT version_num FROM public.alembic_version; debe devolver q5e1c8a9d3f7.
