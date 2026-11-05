-- CotizaT — actualización de u1c5e8b3d7a9 a v2d7f1a6b9c3
-- Datos bancarios por presupuesto: mantener los de Configuración o escribir unos.
--
-- Por qué: los datos bancarios y métodos de pago se configuran UNA vez para la
-- empresa y salen en todos los presupuestos. Eso funciona mientras todo se cobre
-- en la misma cuenta, pero hay documentos que no encajan: una obra que se cobra
-- en otra cuenta, un cliente extranjero que paga por Zelle o USDT, un anticipo a
-- nombre de un socio. Hasta ahora la única salida era cambiar los datos de la
-- empresa —afectando a TODOS los presupuestos— o corregir el PDF a mano.
--
-- Contenido (una columna, nullable, sin valor por omisión):
--   presupuestos.datos_bancarios TEXT
--     NULL  -> hereda los datos de Configuración (lo que ya hacía todo el
--              mundo: al añadir la columna vacía, ningún documento cambia).
--     ''    -> este presupuesto no muestra datos de pago.
--     texto -> datos propios de este presupuesto.
--
-- No se rellena con el texto general a propósito: copiarlo a cada fila
-- congelaría los datos de hoy y un cambio de cuenta en Configuración dejaría de
-- llegar a los presupuestos nuevos. La herencia se resuelve al generar el
-- documento. Las versiones ya enviadas guardan su propio texto en la
-- instantánea (presupuesto_versiones.datos_snapshot), que este script NO toca.
--
-- Uso (Supabase → SQL Editor → New query): pega TODO este archivo y pulsa Run.
-- Debe ejecutarse con una sesión administrativa/propietaria. No uses
-- DATABASE_URL del runtime para aplicar DDL.
-- Comprueba primero la versión con:
--   SELECT version_num FROM public.alembic_version;  -- debe ser u1c5e8b3d7a9
BEGIN;

ALTER TABLE public.presupuestos
  ADD COLUMN IF NOT EXISTS datos_bancarios TEXT;

UPDATE public.alembic_version SET version_num='v2d7f1a6b9c3' WHERE alembic_version.version_num = 'u1c5e8b3d7a9';

COMMIT;

-- Verificar: SELECT version_num FROM public.alembic_version; debe devolver v2d7f1a6b9c3.
-- Y que ningún presupuesto quedó con datos propios por accidente:
--   SELECT count(*) FROM public.presupuestos WHERE datos_bancarios IS NOT NULL;  -- 0
--
-- Revertir (si hiciera falta):
--   ALTER TABLE public.presupuestos DROP COLUMN datos_bancarios;
--   UPDATE public.alembic_version SET version_num='u1c5e8b3d7a9'
--    WHERE alembic_version.version_num = 'v2d7f1a6b9c3';
