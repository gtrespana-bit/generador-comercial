-- CotizaT — actualización de s8a3c6d1f7b9 a t9b4d7e2c5f8
-- «Revisa tus precios antes de cotizar»: fecha de revisión por tarifa.
--
-- Por qué: el generador no inventa precios, los compone con las tarifas de
-- recursos de la empresa. Una empresa que paga 15 US$/h por un oficial y otra
-- que paga 25 US$/h DEBEN cotizar distinto con las mismas mediciones; eso es el
-- producto funcionando. El fallo caro es el de al lado: una cuenta recién
-- creada cotiza con referencias de fábrica (de otro país o de hace meses) y
-- nada se lo dice. El presupuesto sale, parece correcto y el margen se lo come
-- el cliente.
--
-- Contenido:
--   1. configuracion.onboarding_precios_revisados (BOOLEAN, FALSE): la empresa
--      ya pasó por la revisión de tarifas. Permite pedirlo UNA vez, no en cada
--      inicio de sesión.
--   2. recursos.precio_revisado_at (DATETIME): «miré esta tarifa y es la mía»,
--      con fecha. Distinto de «tiene precio»: el catálogo llega con precios,
--      pero no con la certeza de que sean los de esta empresa. Pasados 180 días
--      se vuelve a pedir.
--
-- Uso (Supabase → SQL Editor → New query): pega TODO este archivo y pulsa Run.
-- Debe ejecutarse con una sesión administrativa/propietaria. No uses
-- DATABASE_URL del runtime para aplicar DDL.
-- Comprueba primero la versión con:
--   SELECT version_num FROM public.alembic_version;  -- debe ser s8a3c6d1f7b9
--
-- No borra ni reescribe ningún dato de negocio: dos columnas nuevas con valor
-- por omisión (no reescriben la tabla en PostgreSQL 11+) y ningún UPDATE de
-- datos. Todas las tarifas existentes quedan «sin confirmar» a propósito: es
-- justo lo que hay que preguntar en la siguiente visita.
BEGIN;

ALTER TABLE public.configuracion
  ADD COLUMN IF NOT EXISTS onboarding_precios_revisados BOOLEAN DEFAULT FALSE;

ALTER TABLE public.recursos
  ADD COLUMN IF NOT EXISTS precio_revisado_at TIMESTAMP WITHOUT TIME ZONE;

UPDATE public.alembic_version SET version_num='t9b4d7e2c5f8' WHERE alembic_version.version_num = 's8a3c6d1f7b9';

COMMIT;

-- Verificar: SELECT version_num FROM public.alembic_version; debe devolver t9b4d7e2c5f8.
-- Y que las columnas existen y están a cero:
--   SELECT count(*) FROM public.recursos WHERE precio_revisado_at IS NOT NULL;  -- debe ser 0
--   SELECT onboarding_precios_revisados FROM public.configuracion LIMIT 5;      -- FALSE
--
-- A partir de aquí, la primera vez que cada empresa entre verá el aviso «tu
-- catálogo aún cotiza con precios de referencia» y el paso «Confirma tus
-- tarifas» delante del presupuesto en la guía de inicio.
--
-- Revertir (si hiciera falta):
--   ALTER TABLE public.recursos      DROP COLUMN precio_revisado_at;
--   ALTER TABLE public.configuracion DROP COLUMN onboarding_precios_revisados;
--   UPDATE public.alembic_version SET version_num='s8a3c6d1f7b9'
--    WHERE alembic_version.version_num = 't9b4d7e2c5f8';
