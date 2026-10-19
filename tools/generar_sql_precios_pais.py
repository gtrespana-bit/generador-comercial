"""Genera un SQL idempotente de carga de precios referenciales para un mercado.

Un único generador para todos los mercados: antes existía una copia por país
(``generar_sql_precios_espana.py``, ``generar_sql_precios_latam.py``) que solo
se diferenciaban en el nombre del mercado. Se parametriza para que añadir un
mercado no obligue a duplicar 180 líneas de SQL.

Uso:
    python3 tools/generar_sql_precios_pais.py ES
    python3 tools/generar_sql_precios_pais.py GB
    python3 tools/generar_sql_precios_pais.py IE
    python3 tools/generar_sql_precios_pais.py AU
    python3 tools/generar_sql_precios_pais.py CA

La salida se pega en el editor SQL de Supabase. Sustituye únicamente las
referencias nacionales del mercado indicado; no toca precios propios de
organizaciones ni referencias de otros países.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SALIDA_DIR = ROOT / "docs"

COLUMNAS = (
    "codigo_recurso", "pais_codigo", "moneda", "precio_referencia",
    "precio_min", "precio_max", "unidad_fuente", "fuente",
    "fecha_consulta", "confianza", "incluye_iva",
    "incluye_transporte", "observaciones",
)

# mercado -> (nombre en los comentarios del SQL, nombre de la tabla temporal)
MERCADOS = {
    "ES": ("España", "espana"),
    "GB": ("Reino Unido", "reino_unido"),
    "IE": ("Irlanda", "irlanda"),
    "AU": ("Australia", "australia"),
    "CA": ("Canadá", "canada"),
}


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


def generar(mercado: str) -> tuple[int, int, Path]:
    try:
        nombre_mercado, sufijo = MERCADOS[mercado]
    except KeyError:
        raise SystemExit(
            f"Mercado no soportado: {mercado}. Disponibles: {', '.join(sorted(MERCADOS))}"
        )

    matriz = ROOT / f"basedatos_partidas/salida/precios_recursos_{sufijo}.csv"
    if not matriz.exists():
        raise SystemExit(f"No existe la matriz: {matriz.relative_to(ROOT)}")

    with matriz.open(encoding="utf-8-sig", newline="") as fh:
        filas = list(csv.DictReader(fh, delimiter=";"))
    if not filas:
        raise ValueError("La matriz está vacía")

    faltantes = [c for c in COLUMNAS if c not in filas[0]]
    if faltantes:
        raise ValueError(f"Faltan columnas: {', '.join(faltantes)}")

    moneda = {f["moneda"] for f in filas}
    if len(moneda) != 1:
        raise ValueError(f"La matriz mezcla monedas: {sorted(moneda)}")
    moneda = moneda.pop()

    claves = {(f["codigo_recurso"], f["pais_codigo"]) for f in filas}
    if len(claves) != len(filas):
        raise ValueError("Claves duplicadas en la matriz")
    if any(f["pais_codigo"] != mercado for f in filas):
        raise ValueError(f"La matriz debe ser íntegramente {mercado}")
    if any(not str(f["precio_referencia"] or "").strip() for f in filas):
        raise ValueError("La matriz contiene precios pendientes")

    codigos = {f["codigo_recurso"] for f in filas}
    stage = f"cotizat_precios_{sufijo}_stage"
    fecha = filas[0]["fecha_consulta"]

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
    salida = SALIDA_DIR / f"cargar_precios_referencia_{sufijo}_{fecha}.sql"

    sql = f"""-- CotizaT — carga de precios referenciales nacionales {nombre_mercado} ({moneda}).
-- Generado desde basedatos_partidas/salida/precios_recursos_{sufijo}.csv.
-- {len(codigos)} recursos × 1 país = {len(filas)} referencias.
--
-- PRECONDICIÓN: la tabla public.precios_recursos_mercado debe existir
-- (migraciones de moneda y recursos por mercado aplicadas en Supabase).
-- ALCANCE: reemplaza solo referencias nacionales {mercado}.
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

CREATE TEMP TABLE {stage} (
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

INSERT INTO {stage} (
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
  FROM {stage};
  IF v_filas <> {len(filas)} OR v_codigos <> {len(codigos)} THEN
    RAISE EXCEPTION
      'Matriz incompleta: % filas y % recursos; se esperaban {len(filas)}/{len(codigos)}',
      v_filas, v_codigos;
  END IF;

  SELECT count(*) INTO v_ausentes
  FROM (
    SELECT DISTINCT s.codigo_recurso
    FROM {stage} AS s
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

-- Reemplazo idempotente de la matriz nacional {mercado}. Los overrides de empresa
-- (organizacion_id IS NOT NULL) y las referencias de otros países quedan intactos.
DELETE FROM public.precios_recursos_mercado AS p
USING {stage} AS s
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
FROM {stage} AS s
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
  JOIN {stage} AS s
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
  AND pais_codigo = '{mercado}'
GROUP BY pais_codigo
ORDER BY pais_codigo;
"""

    SALIDA_DIR.mkdir(parents=True, exist_ok=True)
    salida.write_text(sql, encoding="utf-8")
    return len(filas), len(codigos), salida


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Uso: python3 tools/generar_sql_precios_pais.py <MERCADO>")
        return 2
    filas, codigos, salida = generar(argv[1].strip().upper())
    print(f"SQL generado en {salida.relative_to(ROOT)}: {filas} filas / {codigos} recursos")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
