"""Genera un SQL idempotente para cargar la matriz España en Supabase.

Uso:
    python3 tools/generar_sql_precios_espana.py

La salida se pega en Supabase SQL Editor. Sustituye únicamente referencias
nacionales ES; no toca precios propios de organizaciones ni referencias de
otros países (VE/CO/PE/MX/EC).
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIZ = ROOT / "basedatos_partidas/salida/precios_recursos_espana.csv"
SALIDA = ROOT / "docs/cargar_precios_referencia_espana_2026-08-22.sql"
COLUMNAS = (
    "codigo_recurso", "pais_codigo", "moneda", "precio_referencia",
    "precio_min", "precio_max", "unidad_fuente", "fuente",
    "fecha_consulta", "confianza", "incluye_iva",
    "incluye_transporte", "observaciones",
)


def q(valor: str) -> str:
    """Literal SQL de texto, sin interpolar identificadores."""
    return "'" + str(valor or "").replace("'", "''") + "'"


def n(valor: str) -> str:
    bruto = str(valor or "").strip()
    if not bruto:
        return "NULL"
    numero = float(bruto)
    if numero <= 0:
        raise ValueError(f"Número no positivo: {valor}")
    return format(numero, ".12g")


def generar() -> tuple[int, int]:
    with MATRIZ.open(encoding="utf-8-sig", newline="") as fh:
        filas = list(csv.DictReader(fh, delimiter=";"))
    if not filas:
        raise ValueError("La matriz está vacía")
    faltantes = [c for c in COLUMNAS if c not in filas[0]]
    if faltantes:
        raise ValueError(f"Faltan columnas: {', '.join(faltantes)}")
    claves = {(f["codigo_recurso"], f["pais_codigo"]) for f in filas}
    if len(claves) != len(filas):
        raise ValueError("Claves duplicadas en la matriz")
    codigos = {f["codigo_recurso"] for f in filas}
    if any(f["pais_codigo"] != "ES" or f["moneda"] != "EUR" for f in filas):
        raise ValueError("La matriz debe ser íntegramente ES/EUR")
    if any(not str(f["precio_referencia"] or "").strip() for f in filas):
        raise ValueError("La matriz contiene precios pendientes")

    valores = []
    for f in filas:
        valores.append("(" + ", ".join((
            q(f["codigo_recurso"]), q(f["pais_codigo"]), q(f["moneda"]),
            n(f["precio_referencia"]), n(f["precio_min"]), n(f["precio_max"]),
            q(f["unidad_fuente"]), q(f["fuente"]), q(f["fecha_consulta"]),
            q(f["confianza"]), q(f["incluye_iva"]),
            q(f["incluye_transporte"]), q(f["observaciones"]),
        )) + ")")

    valores_sql = ",\n".join(valores)
    sql = f"""-- CotizaT — carga de precios referenciales nacionales España (EUR).
-- Generado desde basedatos_partidas/salida/precios_recursos_espana.csv.
-- {len(codigos)} recursos × 1 país = {len(filas)} referencias.
--
-- PRECONDICIÓN: la tabla public.precios_recursos_mercado debe existir
-- (migraciones de moneda y recursos por mercado aplicadas en Supabase).
-- ALCANCE: reemplaza solo referencias nacionales ES.
-- NO TOCA: precios propios de organizaciones ni referencias de otros países.

BEGIN;

DO $$
BEGIN
  IF to_regclass('public.precios_recursos_mercado') IS NULL THEN
    RAISE EXCEPTION
      'Falta public.precios_recursos_mercado: aplicar antes las migraciones de moneda y recursos por mercado';
  END IF;
END
$$;

CREATE TEMP TABLE cotizat_precios_espana_stage (
  codigo_recurso varchar(80) NOT NULL,
  pais_codigo varchar(2) NOT NULL,
  moneda varchar(10) NOT NULL,
  precio double precision NOT NULL,
  precio_min double precision NOT NULL,
  precio_max double precision NOT NULL,
  unidad_referencia varchar(30) NOT NULL,
  fuente varchar(200) NOT NULL,
  fecha_consulta date NOT NULL,
  confianza varchar(20) NOT NULL,
  incluye_iva varchar(20) NOT NULL,
  incluye_transporte varchar(20) NOT NULL,
  observaciones text NOT NULL,
  PRIMARY KEY (codigo_recurso, pais_codigo)
) ON COMMIT DROP;

INSERT INTO cotizat_precios_espana_stage (
  codigo_recurso, pais_codigo, moneda, precio, precio_min, precio_max,
  unidad_referencia, fuente, fecha_consulta, confianza, incluye_iva,
  incluye_transporte, observaciones
) VALUES
{valores_sql};

DO $$
DECLARE
  v_filas integer;
  v_codigos integer;
  v_ausentes integer;
BEGIN
  SELECT count(*), count(DISTINCT codigo_recurso)
    INTO v_filas, v_codigos
  FROM cotizat_precios_espana_stage;
  IF v_filas <> {len(filas)} OR v_codigos <> {len(codigos)} THEN
    RAISE EXCEPTION
      'Matriz incompleta: % filas y % recursos; se esperaban {len(filas)}/{len(codigos)}',
      v_filas, v_codigos;
  END IF;

  SELECT count(*) INTO v_ausentes
  FROM (
    SELECT DISTINCT s.codigo_recurso
    FROM cotizat_precios_espana_stage AS s
    WHERE NOT EXISTS (
      SELECT 1 FROM public.recursos AS r
      WHERE r.codigo = s.codigo_recurso
    )
  ) AS faltantes;
  IF v_ausentes <> 0 THEN
    RAISE EXCEPTION
      'Hay % códigos de recurso que aún no existen en public.recursos',
      v_ausentes;
  END IF;
END
$$;

-- Reemplazo idempotente de la matriz nacional ES. Los overrides de empresa
-- (organizacion_id IS NOT NULL) y las referencias de otros países quedan intactos.
DELETE FROM public.precios_recursos_mercado AS p
USING cotizat_precios_espana_stage AS s
WHERE p.organizacion_id IS NULL
  AND p.pais_codigo = s.pais_codigo
  AND (
    p.codigo_recurso = s.codigo_recurso
    OR p.recurso_id IN (
      SELECT r.id FROM public.recursos AS r
      WHERE r.codigo = s.codigo_recurso
    )
  );

INSERT INTO public.precios_recursos_mercado (
  recurso_id, codigo_recurso, pais_codigo, organizacion_id,
  precio, moneda, precio_min, precio_max, unidad_referencia,
  fuente, proveedor, confianza, fecha_consulta, fecha_vigencia,
  incluye_iva, incluye_transporte, observaciones,
  fecha_actualizacion, activo
)
SELECT
  recurso.id,
  s.codigo_recurso,
  s.pais_codigo,
  NULL,
  s.precio,
  s.moneda,
  s.precio_min,
  s.precio_max,
  s.unidad_referencia,
  s.fuente,
  '',
  s.confianza,
  s.fecha_consulta,
  NULL,
  s.incluye_iva,
  s.incluye_transporte,
  s.observaciones,
  CURRENT_TIMESTAMP,
  true
FROM cotizat_precios_espana_stage AS s
CROSS JOIN LATERAL (
  SELECT r.id
  FROM public.recursos AS r
  WHERE r.codigo = s.codigo_recurso
  ORDER BY r.id
  LIMIT 1
) AS recurso;

DO $$
DECLARE
  v_cargadas integer;
BEGIN
  SELECT count(*) INTO v_cargadas
  FROM public.precios_recursos_mercado AS p
  JOIN cotizat_precios_espana_stage AS s
    ON s.codigo_recurso = p.codigo_recurso
   AND s.pais_codigo = p.pais_codigo
  WHERE p.organizacion_id IS NULL
    AND p.activo IS TRUE;
  IF v_cargadas <> {len(filas)} THEN
    RAISE EXCEPTION
      'Carga incompleta: % referencias activas; se esperaban {len(filas)}',
      v_cargadas;
  END IF;
END
$$;

COMMIT;

-- Verificación posterior (debe devolver {len(codigos)}):
SELECT pais_codigo, count(*) AS referencias
FROM public.precios_recursos_mercado
WHERE organizacion_id IS NULL
  AND activo IS TRUE
  AND pais_codigo = 'ES'
GROUP BY pais_codigo
ORDER BY pais_codigo;
"""
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(sql, encoding="utf-8")
    return len(filas), len(codigos)


if __name__ == "__main__":
    filas, codigos = generar()
    print(f"SQL generado en {SALIDA}: {filas} filas / {codigos} recursos")
