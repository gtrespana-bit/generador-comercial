-- CotizaT — actualización de o2e4a6c8b1d3 a p5f1c8d2a7b4
-- Solicitudes de eliminación total de cuenta y datos (bloque 2: la solicitud).
--
-- Crea `solicitudes_eliminacion` (tabla del operador con RLS, como
-- `consentimientos`) y las funciones SECURITY DEFINER
-- `cotizat_security.solicitar_eliminacion`,
-- `cotizat_security.solicitud_eliminacion_pendiente` y
-- `cotizat_security.cancelar_solicitud_eliminacion`, guardadas por el claim
-- de sesión `cotizat.auth_user_id`: el cliente solo puede crear, ver y
-- cancelar SU solicitud; la ejecución sigue siendo manual del operador.
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
  IF v_version IS DISTINCT FROM 'o2e4a6c8b1d3' THEN
    RAISE EXCEPTION
      'Se esperaba alembic_version o2e4a6c8b1d3 antes de p5f1c8d2a7b4; se encontró %',
      COALESCE(v_version, '<vacío>');
  END IF;
END
$guarda$;


-- Running upgrade o2e4a6c8b1d3 -> p5f1c8d2a7b4

CREATE TABLE solicitudes_eliminacion (
    id SERIAL NOT NULL, 
    usuario_id INTEGER, 
    auth_user_id VARCHAR(36) DEFAULT '' NOT NULL, 
    email VARCHAR(254) DEFAULT '' NOT NULL, 
    nombre VARCHAR(200) DEFAULT '' NOT NULL, 
    motivo TEXT DEFAULT '' NOT NULL, 
    estado VARCHAR(20) DEFAULT 'pendiente' NOT NULL, 
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    cancelada_at TIMESTAMP WITHOUT TIME ZONE, 
    ejecutada_at TIMESTAMP WITHOUT TIME ZONE, 
    ejecutada_por VARCHAR(254) DEFAULT '' NOT NULL, 
    auth_pendiente BOOLEAN DEFAULT false NOT NULL, 
    email_hash VARCHAR(64) DEFAULT '' NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(usuario_id) REFERENCES usuarios (id) ON DELETE SET NULL, 
    CONSTRAINT ck_solic_elim_estado_valido CHECK (estado IN ('pendiente', 'cancelada', 'ejecutada'))
);

CREATE INDEX ix_solicitudes_eliminacion_usuario_id ON solicitudes_eliminacion (usuario_id);

CREATE INDEX ix_solicitudes_eliminacion_email_hash ON solicitudes_eliminacion (email_hash);

CREATE INDEX ix_solic_elim_estado_creada ON solicitudes_eliminacion (estado, created_at);

CREATE INDEX ix_solic_elim_auth ON solicitudes_eliminacion (auth_user_id);

GRANT SELECT, INSERT, UPDATE ON public.solicitudes_eliminacion TO cotizat_app;

GRANT USAGE, SELECT ON SEQUENCE public.solicitudes_eliminacion_id_seq TO cotizat_app;

ALTER TABLE public.solicitudes_eliminacion ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.solicitudes_eliminacion FORCE ROW LEVEL SECURITY;

CREATE POLICY cotizat_se_select ON public.solicitudes_eliminacion FOR SELECT TO cotizat_app USING (COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE));

CREATE POLICY cotizat_se_insert ON public.solicitudes_eliminacion FOR INSERT TO cotizat_app WITH CHECK (COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE));

CREATE POLICY cotizat_se_update ON public.solicitudes_eliminacion FOR UPDATE TO cotizat_app USING (COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)) WITH CHECK (COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE));

CREATE OR REPLACE FUNCTION cotizat_security.solicitar_eliminacion(
  p_usuario_id integer,
  p_auth_user_id varchar,
  p_email varchar,
  p_nombre varchar,
  p_motivo varchar,
  p_email_hash varchar
) RETURNS integer LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
DECLARE
  v_claim text;
  v_email varchar;
  v_operador_previo text;
  v_id integer;
BEGIN

  v_claim := NULLIF(
    pg_catalog.current_setting('cotizat.auth_user_id', true), ''
  );
  IF v_claim IS NULL OR v_claim <> btrim(COALESCE(p_auth_user_id, '')) THEN
    RAISE EXCEPTION 'La sesión no corresponde a la cuenta indicada.';
  END IF;

  v_email := lower(btrim(COALESCE(p_email, '')));
  IF v_email = '' THEN
    RAISE EXCEPTION 'La solicitud necesita el email de la cuenta.';
  END IF;

  -- Marca de operador durante el cuerpo. Igual que en `a3d9c1e75b28`, quien
  -- aplica la migración es superusuario en Supabase y ya bypassea el FORCE
  -- RLS, así que esto es defensa en profundidad: si algún día el propietario
  -- deja de bypassear, la función sigue satisfaciendo las políticas
  -- `cotizat_*` en lugar de romperse en silencio.
  v_operador_previo := COALESCE(
    pg_catalog.current_setting('cotizat.es_operador', true), 'off'
  );
  PERFORM pg_catalog.set_config('cotizat.es_operador', 'on', true);

  -- Idempotente: una segunda solicitud (doble clic, reintento) devuelve la
  -- pendiente que ya existe en lugar de duplicar el acta.
  SELECT id INTO v_id
    FROM public.solicitudes_eliminacion
   WHERE auth_user_id = v_claim
     AND estado = 'pendiente'
   ORDER BY id ASC
   LIMIT 1;

  IF v_id IS NULL THEN
    INSERT INTO public.solicitudes_eliminacion (
      usuario_id, auth_user_id, email, nombre, motivo,
      estado, created_at, email_hash
    ) VALUES (
      p_usuario_id,
      v_claim,
      v_email,
      left(COALESCE(p_nombre, ''), 200),
      left(COALESCE(p_motivo, ''), 4000),
      'pendiente',
      (now() AT TIME ZONE 'utc'),
      left(COALESCE(p_email_hash, ''), 64)
    )
    RETURNING id INTO v_id;
  END IF;

  PERFORM pg_catalog.set_config(
    'cotizat.es_operador', v_operador_previo, true
  );
  RETURN v_id;

EXCEPTION WHEN OTHERS THEN
  -- La marca de operador nunca puede sobrevivir a un fallo: si quedara
  -- puesta, el resto de la petición vería la base con privilegios de operador.
  PERFORM pg_catalog.set_config(
    'cotizat.es_operador', COALESCE(v_operador_previo, 'off'), true
  );
  RAISE;
END;
$$;

ALTER FUNCTION cotizat_security.solicitar_eliminacion(integer, varchar, varchar, varchar, varchar, varchar) OWNER TO CURRENT_USER;

REVOKE ALL ON FUNCTION cotizat_security.solicitar_eliminacion(integer, varchar, varchar, varchar, varchar, varchar) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION cotizat_security.solicitar_eliminacion(integer, varchar, varchar, varchar, varchar, varchar) TO cotizat_app;

CREATE OR REPLACE FUNCTION cotizat_security.solicitud_eliminacion_pendiente(
  p_auth_user_id varchar
) RETURNS TABLE(id integer, created_at timestamp, motivo varchar)
LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
DECLARE
  v_claim text;
  v_operador_previo text;
BEGIN

  v_claim := NULLIF(
    pg_catalog.current_setting('cotizat.auth_user_id', true), ''
  );
  IF v_claim IS NULL OR v_claim <> btrim(COALESCE(p_auth_user_id, '')) THEN
    RAISE EXCEPTION 'La sesión no corresponde a la cuenta indicada.';
  END IF;

  v_operador_previo := COALESCE(
    pg_catalog.current_setting('cotizat.es_operador', true), 'off'
  );
  PERFORM pg_catalog.set_config('cotizat.es_operador', 'on', true);

  RETURN QUERY
    SELECT s.id, s.created_at, s.motivo::varchar
      FROM public.solicitudes_eliminacion s
     WHERE s.auth_user_id = v_claim
       AND s.estado = 'pendiente'
     ORDER BY s.id ASC
     LIMIT 1;

  PERFORM pg_catalog.set_config(
    'cotizat.es_operador', v_operador_previo, true
  );

EXCEPTION WHEN OTHERS THEN
  PERFORM pg_catalog.set_config(
    'cotizat.es_operador', COALESCE(v_operador_previo, 'off'), true
  );
  RAISE;
END;
$$;

ALTER FUNCTION cotizat_security.solicitud_eliminacion_pendiente(varchar) OWNER TO CURRENT_USER;

REVOKE ALL ON FUNCTION cotizat_security.solicitud_eliminacion_pendiente(varchar) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION cotizat_security.solicitud_eliminacion_pendiente(varchar) TO cotizat_app;

CREATE OR REPLACE FUNCTION cotizat_security.cancelar_solicitud_eliminacion(
  p_auth_user_id varchar
) RETURNS boolean LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
DECLARE
  v_claim text;
  v_operador_previo text;
  v_filas integer;
BEGIN

  v_claim := NULLIF(
    pg_catalog.current_setting('cotizat.auth_user_id', true), ''
  );
  IF v_claim IS NULL OR v_claim <> btrim(COALESCE(p_auth_user_id, '')) THEN
    RAISE EXCEPTION 'La sesión no corresponde a la cuenta indicada.';
  END IF;

  v_operador_previo := COALESCE(
    pg_catalog.current_setting('cotizat.es_operador', true), 'off'
  );
  PERFORM pg_catalog.set_config('cotizat.es_operador', 'on', true);

  -- Solo la pendiente propia: una ejecutada ya no se puede deshacer y una
  -- cancelada no cambia.
  UPDATE public.solicitudes_eliminacion
     SET estado = 'cancelada',
         cancelada_at = (now() AT TIME ZONE 'utc')
   WHERE auth_user_id = v_claim
     AND estado = 'pendiente';
  GET DIAGNOSTICS v_filas = ROW_COUNT;

  PERFORM pg_catalog.set_config(
    'cotizat.es_operador', v_operador_previo, true
  );
  RETURN v_filas > 0;

EXCEPTION WHEN OTHERS THEN
  PERFORM pg_catalog.set_config(
    'cotizat.es_operador', COALESCE(v_operador_previo, 'off'), true
  );
  RAISE;
END;
$$;

ALTER FUNCTION cotizat_security.cancelar_solicitud_eliminacion(varchar) OWNER TO CURRENT_USER;

REVOKE ALL ON FUNCTION cotizat_security.cancelar_solicitud_eliminacion(varchar) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION cotizat_security.cancelar_solicitud_eliminacion(varchar) TO cotizat_app;

UPDATE public.alembic_version SET version_num = 'p5f1c8d2a7b4' WHERE version_num = 'o2e4a6c8b1d3';

COMMIT;

