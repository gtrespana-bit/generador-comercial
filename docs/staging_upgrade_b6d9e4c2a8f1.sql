-- CotizaT — actualización de a3d9c1e75b28 a b6d9e4c2a8f1
-- Registro de la aceptación de términos y privacidad (E4-038).
--
-- Crea `consentimientos` (registro de aceptaciones con RLS de operador como
-- `licencias`), las funciones SECURITY DEFINER
-- `cotizat_security.record_consent` y `cotizat_security.obtener_consentimiento`,
-- y las columnas `usuarios.acepto_terminos_*` (marca «en la cuenta»).
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
  IF v_version IS DISTINCT FROM 'a3d9c1e75b28' THEN
    RAISE EXCEPTION
      'Se esperaba alembic_version a3d9c1e75b28 antes de b6d9e4c2a8f1; se encontró %',
      COALESCE(v_version, '<vacío>');
  END IF;
END
$guarda$;


-- Running upgrade a3d9c1e75b28 -> b6d9e4c2a8f1

CREATE TABLE consentimientos (
    id SERIAL NOT NULL, 
    email VARCHAR(254) NOT NULL, 
    nombre VARCHAR(200) DEFAULT '' NOT NULL, 
    version VARCHAR(20) NOT NULL, 
    ip_hash VARCHAR(64) DEFAULT '' NOT NULL, 
    aceptado_en TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT uq_consentimiento_email_version UNIQUE (email, version)
);

CREATE INDEX ix_consentimientos_email ON consentimientos (email);

CREATE INDEX ix_consentimientos_aceptado_en ON consentimientos (aceptado_en);

ALTER TABLE usuarios ADD COLUMN acepto_terminos_version VARCHAR(20) DEFAULT '' NOT NULL;

ALTER TABLE usuarios ADD COLUMN acepto_terminos_at TIMESTAMP WITHOUT TIME ZONE;

GRANT SELECT, INSERT, UPDATE ON public.consentimientos TO cotizat_app;

GRANT USAGE, SELECT ON SEQUENCE public.consentimientos_id_seq TO cotizat_app;

ALTER TABLE public.consentimientos ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.consentimientos FORCE ROW LEVEL SECURITY;

CREATE POLICY cotizat_consentimiento_select ON public.consentimientos FOR SELECT TO cotizat_app USING (COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE));

CREATE POLICY cotizat_consentimiento_insert ON public.consentimientos FOR INSERT TO cotizat_app WITH CHECK (COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE));

CREATE POLICY cotizat_consentimiento_update ON public.consentimientos FOR UPDATE TO cotizat_app USING (COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)) WITH CHECK (COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE));

CREATE OR REPLACE FUNCTION cotizat_security.record_consent(
  p_email varchar,
  p_nombre varchar,
  p_version varchar,
  p_ip_hash varchar
) RETURNS boolean LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
DECLARE
  v_email varchar;
  v_version varchar;
  v_operador_previo text;
  v_id integer;
BEGIN
  v_email := lower(btrim(COALESCE(p_email, '')));
  v_version := btrim(COALESCE(p_version, ''));
  IF v_email = '' OR v_version = '' THEN
    RETURN FALSE;
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

  -- Idempotente: la misma persona aceptando la misma versión no duplica
  -- filas; la carrera entre dos altas simultáneas se cierra de forma atómica.
  INSERT INTO public.consentimientos (
    email, nombre, version, ip_hash, aceptado_en
  ) VALUES (
    v_email,
    left(COALESCE(p_nombre, ''), 200),
    left(v_version, 20),
    COALESCE(p_ip_hash, ''),
    (now() AT TIME ZONE 'utc')
  )
  ON CONFLICT (email, version) DO NOTHING
  RETURNING id INTO v_id;

  PERFORM pg_catalog.set_config(
    'cotizat.es_operador', v_operador_previo, true
  );
  RETURN v_id IS NOT NULL;

EXCEPTION WHEN OTHERS THEN
  -- La marca de operador nunca puede sobrevivir a un fallo: si quedara
  -- puesta, el resto de la petición vería la base con privilegios de operador.
  PERFORM pg_catalog.set_config(
    'cotizat.es_operador', COALESCE(v_operador_previo, 'off'), true
  );
  RAISE;
END;
$$;

ALTER FUNCTION cotizat_security.record_consent(varchar, varchar, varchar, varchar) OWNER TO CURRENT_USER;

REVOKE ALL ON FUNCTION cotizat_security.record_consent(varchar, varchar, varchar, varchar) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION cotizat_security.record_consent(varchar, varchar, varchar, varchar) TO cotizat_app;

CREATE OR REPLACE FUNCTION cotizat_security.obtener_consentimiento(
  p_email varchar
) RETURNS TABLE(version varchar, aceptado_en timestamp)
LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
DECLARE
  v_email varchar;
  v_operador_previo text;
BEGIN
  v_email := lower(btrim(COALESCE(p_email, '')));

  v_operador_previo := COALESCE(
    pg_catalog.current_setting('cotizat.es_operador', true), 'off'
  );
  PERFORM pg_catalog.set_config('cotizat.es_operador', 'on', true);

  RETURN QUERY
    SELECT c.version, c.aceptado_en
      FROM public.consentimientos c
     WHERE c.email = v_email
     ORDER BY c.aceptado_en DESC, c.id DESC
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

ALTER FUNCTION cotizat_security.obtener_consentimiento(varchar) OWNER TO CURRENT_USER;

REVOKE ALL ON FUNCTION cotizat_security.obtener_consentimiento(varchar) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION cotizat_security.obtener_consentimiento(varchar) TO cotizat_app;

UPDATE alembic_version SET version_num='b6d9e4c2a8f1' WHERE alembic_version.version_num = 'a3d9c1e75b28';

COMMIT;

