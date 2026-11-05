-- CotizaT — actualización de t9b4d7e2c5f8 a u1c5e8b3d7a9
-- «Revisar tarifas» deja de ser un muro: se puede posponer o quitar el aviso.
--
-- Por qué: la revisión de tarifas pide confirmar los precios antes de cotizar,
-- y eso está bien porque de ahí sale el importe entero. Pero solo tenía dos
-- desenlaces: confirmar, o no hacer nada. Quien decidía «lo miro la semana que
-- viene» seguía viendo el mismo aviso al día siguiente, y quien ya trabajaba
-- con sus precios no tenía forma de decir «no me lo repitas» sin confirmar
-- tarifas que no había mirado. Un aviso que no se puede quitar acaba siendo un
-- aviso que se ignora.
--
-- Contenido (dos columnas, ninguna confirma precios):
--   1. configuracion.tarifas_recordatorio_pospuesto_hasta (DATE): «ahora no».
--      Un día concreto a partir del cual el aviso vuelve. Se guarda una fecha,
--      no un contador, para que el aviso vuelva aunque nadie entre a la app.
--   2. configuracion.tarifas_recordatorio_silenciado (BOOLEAN, FALSE): «no me
--      lo vuelvas a pedir». El aviso desaparece del panel, del catálogo y de la
--      ficha del presupuesto; la pantalla de revisión sigue en Recursos.
--
-- Uso (Supabase → SQL Editor → New query): pega TODO este archivo y pulsa Run.
-- Debe ejecutarse con una sesión administrativa/propietaria. No uses
-- DATABASE_URL del runtime para aplicar DDL.
-- Comprueba primero la versión con:
--   SELECT version_num FROM public.alembic_version;  -- debe ser t9b4d7e2c5f8
--
-- No borra ni reescribe ningún dato de negocio: dos columnas nuevas con valor
-- por omisión (no reescriben la tabla en PostgreSQL 11+) y ningún UPDATE de
-- datos. Ninguna empresa queda silenciada por defecto: el aviso sigue
-- apareciendo hasta que cada una decida.
BEGIN;

ALTER TABLE public.configuracion
  ADD COLUMN IF NOT EXISTS tarifas_recordatorio_pospuesto_hasta DATE;

ALTER TABLE public.configuracion
  ADD COLUMN IF NOT EXISTS tarifas_recordatorio_silenciado BOOLEAN DEFAULT FALSE;

UPDATE public.alembic_version SET version_num='u1c5e8b3d7a9' WHERE alembic_version.version_num = 't9b4d7e2c5f8';

COMMIT;

-- Verificar: SELECT version_num FROM public.alembic_version; debe devolver u1c5e8b3d7a9.
-- Y que nadie quedó silenciado ni pospuesto:
--   SELECT count(*) FROM public.configuracion WHERE tarifas_recordatorio_silenciado IS TRUE;  -- 0
--   SELECT count(*) FROM public.configuracion WHERE tarifas_recordatorio_pospuesto_hasta IS NOT NULL;  -- 0
--
-- Revertir (si hiciera falta):
--   ALTER TABLE public.configuracion DROP COLUMN tarifas_recordatorio_silenciado;
--   ALTER TABLE public.configuracion DROP COLUMN tarifas_recordatorio_pospuesto_hasta;
--   UPDATE public.alembic_version SET version_num='t9b4d7e2c5f8'
--    WHERE alembic_version.version_num = 'u1c5e8b3d7a9';
