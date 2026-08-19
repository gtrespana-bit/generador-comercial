-- CotizaT — migración b9f4d8a2c6e1: índices de rendimiento.
--
-- Crea los índices de las consultas calientes (catálogo y grafo de
-- presupuestos). PostgreSQL no crea índices automáticos en las claves
-- foráneas: capítulos→partidas→mediciones, facturas, proyectos, cambios y
-- pagos hacían seq-scan bajo RLS en cada página. Con el catálogo completo
-- (~3.000 partidas) el listado de presupuestos paginaba cientos de consultas
-- sin índice por petición.
--
-- Es idempotente (CREATE INDEX IF NOT EXISTS): puede re-ejecutarse sin daño.
-- Ejecutar una sola vez con rol administrativo si la base ya está en
-- e7b3c1d5a204.

BEGIN;

DO $$
DECLARE
  v_version text;
BEGIN
  SELECT version_num INTO v_version FROM public.alembic_version LIMIT 1;
  IF v_version IS DISTINCT FROM 'e7b3c1d5a204' THEN
    RAISE EXCEPTION
      'Se esperaba alembic_version e7b3c1d5a204 antes de b9f4d8a2c6e1; se encontró %',
      COALESCE(v_version, '<vacío>');
  END IF;
END
$$;

-- Catálogo: visibilidad, árbol capítulo/subcapítulo y auditoría de versión.
CREATE INDEX IF NOT EXISTS ix_partidas_org_oculta
  ON public.partidas (organizacion_id, oculta);
CREATE INDEX IF NOT EXISTS ix_partidas_org_clasificacion
  ON public.partidas (organizacion_id, categoria, subcategoria);
CREATE INDEX IF NOT EXISTS ix_partidas_org_version
  ON public.partidas (organizacion_id, version_catalogo);

-- Presupuestos: filtro de estado por organización y join con clientes.
CREATE INDEX IF NOT EXISTS ix_presupuestos_org_estado
  ON public.presupuestos (organizacion_id, estado);
CREATE INDEX IF NOT EXISTS ix_presupuestos_client_id
  ON public.presupuestos (client_id);

-- Grafo del presupuesto (capítulos → partidas → mediciones/productos).
CREATE INDEX IF NOT EXISTS ix_presupuesto_versiones_presupuesto_id
  ON public.presupuesto_versiones (presupuesto_id);
CREATE INDEX IF NOT EXISTS ix_capitulos_presupuesto_id
  ON public.capitulos (presupuesto_id);
CREATE INDEX IF NOT EXISTS ix_presupuesto_items_capitulo_id
  ON public.presupuesto_items (capitulo_id);
CREATE INDEX IF NOT EXISTS ix_presupuesto_items_partida_catalogo_id
  ON public.presupuesto_items (partida_catalogo_id);
CREATE INDEX IF NOT EXISTS ix_mediciones_partida_id
  ON public.mediciones (partida_id);
CREATE INDEX IF NOT EXISTS ix_presupuesto_item_productos_partida_id
  ON public.presupuesto_item_productos (partida_id);
CREATE INDEX IF NOT EXISTS ix_notas_seguimiento_presupuesto_id
  ON public.notas_seguimiento (presupuesto_id);
CREATE INDEX IF NOT EXISTS ix_presupuesto_anexos_presupuesto_id
  ON public.presupuesto_anexos (presupuesto_id);

-- Facturas.
CREATE INDEX IF NOT EXISTS ix_facturas_presupuesto_id
  ON public.facturas (presupuesto_id);
CREATE INDEX IF NOT EXISTS ix_facturas_client_id
  ON public.facturas (client_id);
CREATE INDEX IF NOT EXISTS ix_factura_capitulos_factura_id
  ON public.factura_capitulos (factura_id);
CREATE INDEX IF NOT EXISTS ix_factura_items_capitulo_id
  ON public.factura_items (capitulo_id);

-- Proyectos, cambios de alcance y pagos.
CREATE INDEX IF NOT EXISTS ix_cambios_alcance_proyecto_id
  ON public.cambios_alcance (proyecto_id);
CREATE INDEX IF NOT EXISTS ix_cambio_alcance_items_cambio_id
  ON public.cambio_alcance_items (cambio_id);
CREATE INDEX IF NOT EXISTS ix_pagos_proyecto_id
  ON public.pagos (proyecto_id);
CREATE INDEX IF NOT EXISTS ix_pagos_presupuesto_id
  ON public.pagos (presupuesto_id);
CREATE INDEX IF NOT EXISTS ix_pagos_factura_id
  ON public.pagos (factura_id);

UPDATE public.alembic_version
SET version_num = 'b9f4d8a2c6e1'
WHERE version_num = 'e7b3c1d5a204';

COMMIT;

-- Verificación:
-- SELECT version_num FROM public.alembic_version;  -- → b9f4d8a2c6e1
-- SELECT indexname FROM pg_indexes
-- WHERE schemaname = 'public' AND indexname LIKE 'ix_partidas_%'
-- ORDER BY indexname;  -- → org_oculta, org_clasificacion, org_version…
