-- CotizaT — actualización de c7f1a3b9d425 a a3d9c1e75b28
-- Prueba gratuita de 7 días con registro anti-reciclaje de cuentas.
--
-- Crea `pruebas_concedidas` (registro de qué identidades ya gastaron su
-- prueba, con RLS de operador como `licencias`) y la función SECURITY DEFINER
-- `cotizat_security.grant_trial_license`, que inserta la marca y la licencia
-- en el mismo paso atómico.
--
-- Generado desde la propia migración con `alembic upgrade --sql`, no
-- transcrito a mano: este fichero no puede divergir del código.
--
-- Ejecutar una sola vez con el rol administrativo de Supabase/PostgreSQL.
-- El rol que lo ejecute será el propietario (`OWNER TO CURRENT_USER`) de la
-- función SECURITY DEFINER, y por tanto el privilegio con el que corre: debe
-- ser el rol administrativo, nunca `cotizat_app`.

BEGIN;

DO $guarda$
DECLARE
  v_version text;
BEGIN
  SELECT version_num INTO v_version FROM public.alembic_version LIMIT 1;
  IF v_version IS DISTINCT FROM 'c7f1a3b9d425' THEN
    RAISE EXCEPTION
      'Se esperaba alembic_version c7f1a3b9d425 antes de a3d9c1e75b28; se encontró %',
      COALESCE(v_version, '<vacío>');
  END IF;
END
$guarda$;


-- Running upgrade c7f1a3b9d425 -> a3d9c1e75b28

CREATE TABLE pruebas_concedidas (
    id SERIAL NOT NULL, 
    email_normalizado VARCHAR(254) NOT NULL, 
    email_original VARCHAR(254) DEFAULT '' NOT NULL, 
    organizacion_id INTEGER, 
    licencia_id INTEGER, 
    ip_hash VARCHAR(64) DEFAULT '' NOT NULL, 
    dias INTEGER DEFAULT '0' NOT NULL, 
    created_at TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(organizacion_id) REFERENCES organizaciones (id) ON DELETE SET NULL, 
    FOREIGN KEY(licencia_id) REFERENCES licencias (id) ON DELETE SET NULL, 
    CONSTRAINT uq_prueba_email_normalizado UNIQUE (email_normalizado)
);

CREATE INDEX ix_pruebas_concedidas_creada ON pruebas_concedidas (created_at);

CREATE INDEX ix_pruebas_concedidas_ip ON pruebas_concedidas (ip_hash);

CREATE INDEX ix_pruebas_concedidas_organizacion_id ON pruebas_concedidas (organizacion_id);

CREATE INDEX ix_pruebas_concedidas_licencia_id ON pruebas_concedidas (licencia_id);

GRANT SELECT, INSERT, UPDATE ON public.pruebas_concedidas TO cotizat_app;

GRANT USAGE, SELECT ON SEQUENCE public.pruebas_concedidas_id_seq TO cotizat_app;

ALTER TABLE public.pruebas_concedidas ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.pruebas_concedidas FORCE ROW LEVEL SECURITY;

CREATE POLICY cotizat_prueba_select ON public.pruebas_concedidas FOR SELECT TO cotizat_app USING (COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE));

CREATE POLICY cotizat_prueba_insert ON public.pruebas_concedidas FOR INSERT TO cotizat_app WITH CHECK (COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE));

CREATE POLICY cotizat_prueba_update ON public.pruebas_concedidas FOR UPDATE TO cotizat_app USING (COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE)) WITH CHECK (COALESCE(pg_catalog.current_setting('cotizat.es_operador', true) = 'on', FALSE));

CREATE OR REPLACE FUNCTION cotizat_security.grant_trial_license(
  p_organization_id integer,
  p_email_normalizado varchar,
  p_email_original varchar,
  p_ip_hash varchar,
  p_dias integer
) RETURNS boolean LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
DECLARE
  v_dias integer;
  v_licencia_id integer;
  v_marca_id integer;
  v_operador_previo text;
BEGIN
  -- La organización debe ser la de la sesión: nadie concede licencias ajenas.
  IF COALESCE(
       pg_catalog.current_setting('cotizat.organization_id', true),
       ''
     ) <> p_organization_id::text THEN
    RETURN FALSE;
  END IF;

  IF COALESCE(p_email_normalizado, '') = '' THEN
    RETURN FALSE;
  END IF;

  v_dias := LEAST(GREATEST(COALESCE(p_dias, 0), 1), 90);

  -- Marca de operador durante el cuerpo. Igual que en `b7c4a9e2d31f`, quien
  -- aplica la migración es superusuario en Supabase y ya bypassea el FORCE RLS
  -- de `licencias`, así que esto es defensa en profundidad: si algún día el
  -- propietario deja de bypassear, la función sigue satisfaciendo las
  -- políticas `cotizat_*` en lugar de romperse en silencio.
  --
  -- Se eleva **aquí y no más abajo** por un motivo de corrección, no de estilo:
  -- la comprobación de licencia previa es un SELECT sobre `licencias`. Si esa
  -- lectura quedara filtrada por RLS devolvería cero filas y la función
  -- concedería prueba a organizaciones que ya la tuvieron: un fallo abierto,
  -- que es el peor tipo.
  --
  -- La elevación es local a la transacción y se restaura en todas las salidas,
  -- incluida la de excepción: la sesión del cliente nunca la hereda.
  v_operador_previo := COALESCE(
    pg_catalog.current_setting('cotizat.es_operador', true), 'off'
  );
  PERFORM pg_catalog.set_config('cotizat.es_operador', 'on', true);

  -- La prueba es para empezar. Si la organización ya tuvo licencia de
  -- cualquier tipo, no hay nada que conceder.
  IF EXISTS (
    SELECT 1 FROM public.licencias WHERE organizacion_id = p_organization_id
  ) THEN
    PERFORM pg_catalog.set_config(
      'cotizat.es_operador', v_operador_previo, true
    );
    RETURN FALSE;
  END IF;

  -- Se marca primero la identidad: si ya constaba, ON CONFLICT no devuelve
  -- fila y salimos sin crear licencia. Esto resuelve la carrera entre dos
  -- altas simultáneas del mismo correo de forma atómica.
  INSERT INTO public.pruebas_concedidas (
    email_normalizado, email_original, organizacion_id, ip_hash, dias, created_at
  ) VALUES (
    p_email_normalizado,
    COALESCE(p_email_original, ''),
    p_organization_id,
    COALESCE(p_ip_hash, ''),
    v_dias,
    (now() AT TIME ZONE 'utc')
  )
  ON CONFLICT (email_normalizado) DO NOTHING
  RETURNING id INTO v_marca_id;

  IF v_marca_id IS NULL THEN
    PERFORM pg_catalog.set_config(
      'cotizat.es_operador', v_operador_previo, true
    );
    RETURN FALSE;
  END IF;

  INSERT INTO public.licencias (
    organizacion_id, estado, origen, inicio, vence,
    importe, moneda, metodo_cobro, referencia, notas,
    creada_por_email, created_at
  ) VALUES (
    p_organization_id,
    'activa',
    'prueba',
    CURRENT_DATE,
    CURRENT_DATE + (v_dias - 1),
    0,
    'USD',
    '',
    '',
    'Prueba gratuita automática al crear la organización.',
    'sistema@cotizat',
    (now() AT TIME ZONE 'utc')
  )
  RETURNING id INTO v_licencia_id;

  UPDATE public.pruebas_concedidas
     SET licencia_id = v_licencia_id
   WHERE id = v_marca_id;

  PERFORM pg_catalog.set_config(
    'cotizat.es_operador', v_operador_previo, true
  );
  RETURN TRUE;

EXCEPTION WHEN OTHERS THEN
  -- La marca de operador nunca puede sobrevivir a un fallo: si quedara puesta,
  -- el resto de la petición vería la base con privilegios de operador.
  PERFORM pg_catalog.set_config(
    'cotizat.es_operador', COALESCE(v_operador_previo, 'off'), true
  );
  RAISE;
END;
$$;

ALTER FUNCTION cotizat_security.grant_trial_license(integer, varchar, varchar, varchar, integer) OWNER TO CURRENT_USER;

REVOKE ALL ON FUNCTION cotizat_security.grant_trial_license(integer, varchar, varchar, varchar, integer) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION cotizat_security.grant_trial_license(integer, varchar, varchar, varchar, integer) TO cotizat_app;

UPDATE alembic_version SET version_num='a3d9c1e75b28' WHERE alembic_version.version_num = 'c7f1a3b9d425';

COMMIT;

-- Verificación:
-- SELECT version_num FROM public.alembic_version;
--   -> a3d9c1e75b28
--
-- La tabla existe y está cerrada a los clientes:
-- SELECT relrowsecurity, relforcerowsecurity FROM pg_class
-- WHERE oid = 'public.pruebas_concedidas'::regclass;
--   -> t | t
-- SELECT polname, polcmd FROM pg_policy
-- WHERE polrelid = 'public.pruebas_concedidas'::regclass ORDER BY polname;
--   -> cotizat_prueba_insert (a), cotizat_prueba_select (r),
--      cotizat_prueba_update (w). Sin política de DELETE: el registro de
--      pruebas gastadas no se borra desde la aplicación.
--
-- La función existe, es SECURITY DEFINER y tiene search_path fijado:
-- SELECT prosecdef, proconfig FROM pg_proc p
-- JOIN pg_namespace n ON n.oid = p.pronamespace
-- WHERE n.nspname = 'cotizat_security' AND p.proname = 'grant_trial_license';
--   -> t | {search_path=pg_catalog,public}
--
-- El propietario NO debe ser el rol de la aplicación:
-- SELECT pg_get_userbyid(proowner) FROM pg_proc p
-- JOIN pg_namespace n ON n.oid = p.pronamespace
-- WHERE n.nspname = 'cotizat_security' AND p.proname = 'grant_trial_license';
--   -> el rol administrativo (postgres), nunca cotizat_app.
--
-- Prueba de humo con una sesión de cliente (sustituye <ORG> por una
-- organización SIN ninguna licencia; deja la transacción sin confirmar):
-- BEGIN;
--   SET LOCAL ROLE cotizat_app;
--   SELECT set_config('cotizat.organization_id', '<ORG>', true);
--   SELECT cotizat_security.grant_trial_license(
--     <ORG>, 'humo@example.com', 'humo@example.com', '', 7);
--     -> t   (la segunda llamada con el mismo correo devuelve f)
--   SELECT current_setting('cotizat.es_operador', true);
--     -> off   (la marca de operador no se filtra fuera de la función)
--   SELECT count(*) FROM public.pruebas_concedidas;
--     -> 0     (el cliente sigue sin poder leer la tabla)
-- ROLLBACK;
