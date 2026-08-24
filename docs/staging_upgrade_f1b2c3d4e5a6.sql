-- Aplicación manual en Supabase para el head f1b2c3d4e5a6
-- Esquema del editor vectorial de planos.
--
-- 1. Añade a planos_obra: origen, grosor_tabique_cm, ancho_lienzo_m,
--    alto_lienzo_m (las columnas que pide el modelo del visor).
-- 2. Crea planos_elementos (muros / huecos / líneas auxiliares) con sus
--    índices, GRANT al rol de aplicación y políticas RLS por organización.
--
-- Es idempotente (ADD COLUMN IF NOT EXISTS / CREATE TABLE IF NOT EXISTS) y
-- avanza la marca a f1b2c3d4e5a6 solo si veníamos de e4b8c2d6a190. Si el
-- arranque ya auto-reparó la base y la marca está en f1b2c3d4e5a6, el script
-- no hace nada.

BEGIN;

DO $$ BEGIN
  IF (SELECT version_num FROM public.alembic_version) NOT IN ('e4b8c2d6a190', 'f1b2c3d4e5a6') THEN
    RAISE EXCEPTION 'La base está en %. Este script solo aplica desde e4b8c2d6a190.',
      (SELECT version_num FROM public.alembic_version);
  END IF;
END $$;

-- Columnas del modelo PlanoObra (editor desde cero).
ALTER TABLE public.planos_obra ADD COLUMN IF NOT EXISTS origen VARCHAR(20) NOT NULL DEFAULT 'subido';
ALTER TABLE public.planos_obra ADD COLUMN IF NOT EXISTS grosor_tabique_cm DOUBLE PRECISION NOT NULL DEFAULT 10;
ALTER TABLE public.planos_obra ADD COLUMN IF NOT EXISTS ancho_lienzo_m DOUBLE PRECISION;
ALTER TABLE public.planos_obra ADD COLUMN IF NOT EXISTS alto_lienzo_m DOUBLE PRECISION;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_plano_origen_valido') THEN
    ALTER TABLE public.planos_obra ADD CONSTRAINT ck_plano_origen_valido
      CHECK (origen IN ('subido', 'dibujado', 'mixto'));
  END IF;
END $$;

-- Tabla del editor vectorial.
CREATE TABLE IF NOT EXISTS public.planos_elementos (
    id SERIAL PRIMARY KEY,
    plano_id INTEGER NOT NULL REFERENCES public.planos_obra(id) ON DELETE CASCADE,
    organizacion_id INTEGER NOT NULL REFERENCES public.organizaciones(id) ON DELETE RESTRICT,
    tipo VARCHAR(20) NOT NULL DEFAULT 'muro',
    puntos_json TEXT NOT NULL DEFAULT '[]',
    grosor_cm DOUBLE PRECISION DEFAULT 10,
    color VARCHAR(20) DEFAULT '#1f2937',
    muro_id INTEGER REFERENCES public.planos_elementos(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_planos_elementos_plano ON public.planos_elementos (plano_id);
CREATE INDEX IF NOT EXISTS ix_planos_elementos_org_plano ON public.planos_elementos (organizacion_id, plano_id);
CREATE INDEX IF NOT EXISTS ix_planos_elementos_muro ON public.planos_elementos (muro_id);

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_plano_elemento_tipo_valido') THEN
    ALTER TABLE public.planos_elementos ADD CONSTRAINT ck_plano_elemento_tipo_valido
      CHECK (tipo IN ('muro', 'hueco', 'linea_auxiliar'));
  END IF;
END $$;

-- Permisos y RLS.
REVOKE ALL ON TABLE public.planos_elementos FROM PUBLIC;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.planos_elementos TO cotizat_app;
DO $$ DECLARE secuencia text; BEGIN
  secuencia := pg_get_serial_sequence('public.planos_elementos', 'id');
  IF secuencia IS NOT NULL THEN
    EXECUTE format('GRANT USAGE, SELECT ON SEQUENCE %s TO cotizat_app', secuencia);
  END IF;
END $$;
ALTER TABLE public.planos_elementos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.planos_elementos FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS cotizat_planos_elementos_select ON public.planos_elementos;
CREATE POLICY cotizat_planos_elementos_select ON public.planos_elementos
  FOR SELECT TO cotizat_app
  USING (cotizat_security.tenant_access(organizacion_id, FALSE));

DROP POLICY IF EXISTS cotizat_planos_elementos_insert ON public.planos_elementos;
CREATE POLICY cotizat_planos_elementos_insert ON public.planos_elementos
  FOR INSERT TO cotizat_app
  WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

DROP POLICY IF EXISTS cotizat_planos_elementos_update ON public.planos_elementos;
CREATE POLICY cotizat_planos_elementos_update ON public.planos_elementos
  FOR UPDATE TO cotizat_app
  USING (cotizat_security.tenant_access(organizacion_id, TRUE))
  WITH CHECK (cotizat_security.tenant_access(organizacion_id, TRUE));

DROP POLICY IF EXISTS cotizat_planos_elementos_delete ON public.planos_elementos;
CREATE POLICY cotizat_planos_elementos_delete ON public.planos_elementos
  FOR DELETE TO cotizat_app
  USING (cotizat_security.tenant_access(organizacion_id, TRUE));

UPDATE public.alembic_version
SET version_num = 'f1b2c3d4e5a6'
WHERE version_num = 'e4b8c2d6a190';

COMMIT;
