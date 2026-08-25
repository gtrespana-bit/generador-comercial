#!/bin/bash
# Carga directa vía psql (evita límite del SQL Editor)
# Uso: DATABASE_URL=postgres://... bash docs/cargar_todo_latam_psql.sh
set -e
if [ -z "$DATABASE_URL" ]; then echo "Falta DATABASE_URL"; exit 1; fi
for pais in AR BO CL CO CR DO EC GT HN MX NI PA PE PY SV UY; do
  echo "Cargando $pais..."
  psql "$DATABASE_URL" -f "docs/cargar_precios_referencia_latam_2026-08-25_${pais}.sql"
done
psql "$DATABASE_URL" -f "docs/cargar_precios_referencia_espana_2026-08-25.sql"
echo "Verificación:"
psql "$DATABASE_URL" -c "SELECT pais_codigo, count(*) FROM public.precios_recursos_mercado WHERE organizacion_id IS NULL AND activo IS TRUE GROUP BY pais_codigo ORDER BY pais_codigo;"
