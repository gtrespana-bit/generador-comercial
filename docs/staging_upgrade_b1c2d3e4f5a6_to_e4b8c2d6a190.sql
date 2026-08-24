-- CotizaT — rescate de b1c2d3e4f5a6 a e4b8c2d6a190 (visor de planos 500)
--
-- CASO QUE CUBRE: la marca alembic_version quedó en b1c2d3e4f5a6 aunque el
-- CONTENIDO de b2c3d4e5f6a7 (tablas planos_obra/planos_mediciones) y de
-- c0d1e2f3a4b5 (permisos/RLS, 8 políticas cotizat_planos_*) ya existe en la
-- base. Ocurrió así: la auto-reparación best-effort de un arranque anterior
-- creó las tablas y las políticas, pero el rol de runtime solo tiene SELECT
-- sobre public.alembic_version, así que la marca nunca pudo avanzar.
--
-- Síntoma en producción (23/08/2026): al desplegar el modelo con
-- planos_obra.altura_libre_m sin migrar, cada apertura del visor devolvía 500
-- con ``UndefinedColumn: planos_obra.altura_libre_m does not exist``.
--
-- Confirmación del estado (solo lectura):
--   SELECT version_num FROM public.alembic_version;   -- b1c2d3e4f5a6
--   SELECT table_name FROM information_schema.tables
--   WHERE table_schema='public' AND table_name LIKE 'planos%';  -- 2 filas
--
-- Uso (Supabase → SQL Editor → New query): pega TODO este archivo y pulsa Run.
-- Debe ejecutarse con una sesión administrativa/propietaria. No uses la
-- DATABASE_URL del runtime para aplicar DDL/DCL.
--
-- Si tu versión NO es b1c2d3e4f5a6:
--   · b2c3d4e5f6a7 → aplica docs/staging_upgrade_c0d1e2f3a4b5.sql y luego
--     docs/staging_upgrade_e4b8c2d6a190.sql.
--   · c0d1e2f3a4b5 → aplica solo docs/staging_upgrade_e4b8c2d6a190.sql.
--
-- Todo el contenido es idempotente y va en una transacción: si algo falla,
-- no se aplica a medias.

BEGIN;

-- 0) Guardas: versión esperada y contenido de planos YA presente. Así el
--    avance de marca b1 → e4 no certifica migraciones que no se aplicaron.
DO $check$
DECLARE
  v_tablas integer;
  v_politicas integer;
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM public.alembic_version
    WHERE version_num = 'b1c2d3e4f5a6'
  ) THEN
    RAISE EXCEPTION
      'Se esperaba alembic_version en b1c2d3e4f5a6 (rescate); revisa el comentario de cabecera para otras versiones';
  END IF;
  SELECT count(*) INTO v_tablas
  FROM information_schema.tables
  WHERE table_schema = 'public'
    AND table_name IN ('planos_obra', 'planos_mediciones');
  IF v_tablas <> 2 THEN
    RAISE EXCEPTION
      'Faltan tablas de planos (% de 2): esta base necesita aplicar b2c3d4e5f6a7 completa, no este rescate',
      v_tablas;
  END IF;
  SELECT count(*) INTO v_politicas
  FROM pg_policies
  WHERE schemaname = 'public'
    AND tablename IN ('planos_obra', 'planos_mediciones')
    AND policyname LIKE 'cotizat_planos_%';
  IF v_politicas <> 8 THEN
    RAISE EXCEPTION
      'Faltan políticas cotizat_planos_* (% de 8): esta base necesita revisión manual, no se avanza la marca',
      v_politicas;
  END IF;
END
$check$;

-- 1) Permisos/RLS de c0d1e2f3a4b5 (idempotente: cierra cualquier hueco de
--    GRANT que la reparación de arranque dejara a medias, p. ej. secuencias).
REVOKE ALL ON TABLE public.planos_obra FROM PUBLIC;
ALTER TABLE public.planos_obra ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.planos_obra FORCE ROW LEVEL SECURITY;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.planos_obra TO cotizat_app;

DO $$
DECLARE secuencia text;
BEGIN
  secuencia := pg_get_serial_sequence('public.planos_obra', 'id');
  IF secuencia IS NOT NULL THEN
    EXECUTE format('GRANT USAGE, SELECT ON SEQUENCE %s TO cotizat_app', secuencia);
  END IF;
END $$;

REVOKE ALL ON TABLE public.planos_mediciones FROM PUBLIC;
ALTER TABLE public.planos_mediciones ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.planos_mediciones FORCE ROW LEVEL SECURITY;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.planos_mediciones TO cotizat_app;

DO $$
DECLARE secuencia text;
BEGIN
  secuencia := pg_get_serial_sequence('public.planos_mediciones', 'id');
  IF secuencia IS NOT NULL THEN
    EXECUTE format('GRANT USAGE, SELECT ON SEQUENCE %s TO cotizat_app', secuencia);
  END IF;
END $$;

DROP POLICY IF EXISTS cotizat_planos_obra_select ON public.planos_obra;
CREATE POLICY cotizat_planos_obra_select ON public.planos_obra
  FOR SELECT TO cotizat_app
  USING (cotizat_security.tenant_access(organizacion_id, FALSE));

DROP POLICY IF EXISTS cotizat_planos_obra_insert ON public.planos_obra;
CREATE POLICY cotizat_planos_obra_insert ON public.planos_obra
  FOR INSERT TO cotizat_app
  WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

DROP POLICY IF EXISTS cotizat_planos_obra_update ON public.planos_obra;
CREATE POLICY cotizat_planos_obra_update ON public.planos_obra
  FOR UPDATE TO cotizat_app
  USING (cotizat_security.tenant_access(organizacion_id, TRUE))
  WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

DROP POLICY IF EXISTS cotizat_planos_obra_delete ON public.planos_obra;
CREATE POLICY cotizat_planos_obra_delete ON public.planos_obra
  FOR DELETE TO cotizat_app
  USING (cotizat_security.tenant_access(organizacion_id, TRUE));

DROP POLICY IF EXISTS cotizat_planos_mediciones_select ON public.planos_mediciones;
CREATE POLICY cotizat_planos_mediciones_select ON public.planos_mediciones
  FOR SELECT TO cotizat_app
  USING (cotizat_security.tenant_access(organizacion_id, FALSE));

DROP POLICY IF EXISTS cotizat_planos_mediciones_insert ON public.planos_mediciones;
CREATE POLICY cotizat_planos_mediciones_insert ON public.planos_mediciones
  FOR INSERT TO cotizat_app
  WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

DROP POLICY IF EXISTS cotizat_planos_mediciones_update ON public.planos_mediciones;
CREATE POLICY cotizat_planos_mediciones_update ON public.planos_mediciones
  FOR UPDATE TO cotizat_app
  USING (cotizat_security.tenant_access(organizacion_id, TRUE))
  WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

DROP POLICY IF EXISTS cotizat_planos_mediciones_delete ON public.planos_mediciones;
CREATE POLICY cotizat_planos_mediciones_delete ON public.planos_mediciones
  FOR DELETE TO cotizat_app
  USING (cotizat_security.tenant_access(organizacion_id, TRUE));

-- 2) Índices de b2c3d4e5f6a7: la reparación de arranque crea las tablas vía
--    metadata, que no incluye estos índices compuestos de la migración.
CREATE INDEX IF NOT EXISTS ix_planos_obra_presupuesto
  ON public.planos_obra (presupuesto_id);
CREATE INDEX IF NOT EXISTS ix_planos_obra_org_presupuesto
  ON public.planos_obra (organizacion_id, presupuesto_id);
CREATE INDEX IF NOT EXISTS ix_planos_mediciones_plano
  ON public.planos_mediciones (plano_id);
CREATE INDEX IF NOT EXISTS ix_planos_mediciones_org_plano
  ON public.planos_mediciones (organizacion_id, plano_id);

-- 3) Columna de e4b8c2d6a190 (altura libre de paramentos, en metros).
ALTER TABLE public.planos_obra
  ADD COLUMN IF NOT EXISTS altura_libre_m double precision;

-- 4) Marca final: el contenido de b2, c0 y e4 está ahora verificado presente.
UPDATE public.alembic_version
SET version_num = 'e4b8c2d6a190'
WHERE version_num = 'b1c2d3e4f5a6';

COMMIT;

-- Verificación 1: debe devolver e4b8c2d6a190
SELECT version_num FROM public.alembic_version;

-- Verificación 2: una fila con data_type = double precision, is_nullable = YES
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'planos_obra'
  AND column_name = 'altura_libre_m';

-- Verificación 3: los 4 índices compuestos
SELECT indexname
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('planos_obra', 'planos_mediciones')
  AND indexname LIKE 'ix_planos_%'
ORDER BY indexname;

-- Verificación 4 (informativa): deben aparecer 6 claves foráneas
-- (2 en planos_obra + 4 en planos_mediciones). Si salieran menos, el visor
-- funciona igual, pero conviene revisar las cascadas de borrado.
SELECT conrelid::regclass AS tabla, conname
FROM pg_constraint
WHERE connamespace = 'public'::regnamespace
  AND contype = 'f'
  AND conrelid IN ('public.planos_obra'::regclass, 'public.planos_mediciones'::regclass)
ORDER BY 1;

-- Verificación final: el visor de planos del presupuesto vuelve a abrir y,
-- tras desplegar el código con EXPECTED_ALEMBIC_HEAD actualizado:
-- GET /readyz → {"ok": true, "alembic": "head:e4b8c2d6a190"}
