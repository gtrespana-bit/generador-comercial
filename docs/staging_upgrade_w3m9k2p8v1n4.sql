-- CotizaT — actualización de v2d7f1a6b9c3 a w3m9k2p8v1n4
-- Audiencia de la web pública: la tabla que el panel de operador necesita para
-- mirar el embudo completo (visitas → registros → empresas → presupuestos).
--
-- Por qué existe este archivo: la migración llegó con el código del panel
-- (PR 186) pero sin su SQL de aplicación manual, así que la base de producción
-- se quedó en v2d7f1a6b9c3. El panel pedía `visitas_pagina`, la consulta moría
-- y, al no hacer `rollback`, la sesión quedaba abortada y tumbaba también las
-- consultas siguientes (el 500 de /admin/analitica y parte de /admin).
--
-- Contenido:
--   1. Tabla public.visitas_pagina (una fila por página vista; NUNCA la IP,
--      solo su hash con sal del despliegue).
--   2. Índices por ruta, por hash de IP y por fecha (las tres consultas del
--      panel: qué páginas, cuántos visitantes únicos, serie diaria).
--   3. Permisos para el rol de aplicación (cotizat_app). Sin este bloque la
--      tabla nace siendo de `postgres` y el runtime recibe «permission denied
--      for table visitas_pagina» en cada carga del panel. Es el mismo error que
--      ya ocurrió con planos_obra y precios_recursos_mercado.
--
-- La tabla es global a propósito (no lleva organizacion_id como filtro de
-- lectura): es un agregado de la web pública y no contiene datos de ningún
-- cliente. No guarda la IP, ni el cuerpo de la petición, ni nada que permita
-- identificar a una persona.
--
-- Uso (Supabase → SQL Editor → New query): pega TODO este archivo y pulsa Run.
-- Debe ejecutarse con una sesión administrativa/propietaria. No uses
-- DATABASE_URL del runtime para aplicar DDL.
-- Comprueba primero la versión con:
--   SELECT version_num FROM public.alembic_version;  -- debe ser v2d7f1a6b9c3
BEGIN;

DO $$
BEGIN
  IF (SELECT version_num FROM public.alembic_version LIMIT 1) IS DISTINCT FROM 'v2d7f1a6b9c3' THEN
    RAISE EXCEPTION 'Head inesperado; se esperaba v2d7f1a6b9c3';
  END IF;
END $$;

-- Running upgrade v2d7f1a6b9c3 -> w3m9k2p8v1n4

-- 1) Tabla del agregado de audiencia. La secuencia `visitas_pagina_id_seq` la
--    crea SERIAL con la propia tabla.
CREATE TABLE IF NOT EXISTS public.visitas_pagina (
  id SERIAL PRIMARY KEY,
  ruta VARCHAR(300) NOT NULL,
  ip_hash VARCHAR(64) NOT NULL,
  usuario_agent VARCHAR(300),
  referente VARCHAR(300),
  usuario_id INTEGER REFERENCES public.usuarios(id) ON DELETE SET NULL,
  organizacion_id INTEGER REFERENCES public.organizaciones(id) ON DELETE SET NULL,
  created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2) Índices de las tres lecturas del panel.
CREATE INDEX IF NOT EXISTS ix_visitas_pagina_ruta ON public.visitas_pagina (ruta);
CREATE INDEX IF NOT EXISTS ix_visitas_pagina_ip_hash ON public.visitas_pagina (ip_hash);
CREATE INDEX IF NOT EXISTS ix_visitas_pagina_created_at ON public.visitas_pagina (created_at);

-- 3) El rol de la aplicación escribe (registra la visita) y lee (el panel).
--    La secuencia necesita USAGE propio o el INSERT falla con «permission
--    denied for sequence visitas_pagina_id_seq».
REVOKE ALL ON TABLE public.visitas_pagina FROM PUBLIC;
-- En Supabase los privilegios por omisión de `public` incluyen `anon` y
-- `authenticated` (roles de la Data API). Esta tabla guarda hashes de IP y
-- rutas visitadas: no puede ser legible desde la API pública.
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
    EXECUTE 'REVOKE ALL ON TABLE public.visitas_pagina FROM anon';
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
    EXECUTE 'REVOKE ALL ON TABLE public.visitas_pagina FROM authenticated';
  END IF;
END $$;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.visitas_pagina TO cotizat_app;
GRANT USAGE, SELECT ON SEQUENCE public.visitas_pagina_id_seq TO cotizat_app;

-- 4) Políticas para el rol de la aplicación.
--    Supabase activa RLS automáticamente en toda tabla nueva de `public`
--    (disparador `ensure_rls`). Con RLS y sin políticas, `cotizat_app` no
--    puede escribir ni leer: el middleware contaría la visita, recibiría
--    «new row violates row-level security policy» y el panel vería ceros.
DROP POLICY IF EXISTS cotizat_visitas_select ON public.visitas_pagina;
CREATE POLICY cotizat_visitas_select ON public.visitas_pagina
  FOR SELECT TO cotizat_app USING (true);
DROP POLICY IF EXISTS cotizat_visitas_insert ON public.visitas_pagina;
CREATE POLICY cotizat_visitas_insert ON public.visitas_pagina
  FOR INSERT TO cotizat_app WITH CHECK (true);
DROP POLICY IF EXISTS cotizat_visitas_update ON public.visitas_pagina;
CREATE POLICY cotizat_visitas_update ON public.visitas_pagina
  FOR UPDATE TO cotizat_app USING (true) WITH CHECK (true);
DROP POLICY IF EXISTS cotizat_visitas_delete ON public.visitas_pagina;
CREATE POLICY cotizat_visitas_delete ON public.visitas_pagina
  FOR DELETE TO cotizat_app USING (true);

UPDATE public.alembic_version
   SET version_num = 'w3m9k2p8v1n4'
 WHERE version_num = 'v2d7f1a6b9c3';

COMMIT;

-- Verificar: SELECT version_num FROM public.alembic_version;  -- w3m9k2p8v1n4
-- Y que el runtime puede leerla:
--   SET ROLE cotizat_app; SELECT count(*) FROM public.visitas_pagina; RESET ROLE;
--
-- Revertir (si hiciera falta):
--   DROP TABLE public.visitas_pagina;
--   UPDATE public.alembic_version SET version_num='v2d7f1a6b9c3'
--    WHERE version_num = 'w3m9k2p8v1n4';
