#!/usr/bin/env python3
"""Valida las cotizaciones reales de España y emite el SQL de carga acotado.

El 7 de noviembre los 54 recursos ``mercado_rango`` se quedaron con el precio
derivado de la matriz porque no había ficha de banco ni oferta publicada. Esta
herramienta cierra el paso siguiente: **sustituir ese precio por una cotización
real**, con su fuente, su fecha, su banda medida y la confianza que la evidencia
permite.

El registro de decisiones vive en
``docs/auditoria_precios/espana_decision_cotizaciones_<fecha>.csv`` y tiene una
fila por recurso:

``codigo_recurso;metodo;precio;precio_min;precio_max;confianza;fuente;criterio``

``metodo`` vale una de las tres formas de evidencia que admite este paso:

* ``cotizacion_directa`` — oferta publicada del mismo producto y unidad.
* ``banco_y_minorista`` — el precio se mantiene porque banco y minorista lo
  acotan por abajo y por arriba.
* ``banco`` — la ficha del banco es el artículo (se adopta su precio).

**La matriz no se escribe aquí.** La matriz de España tiene un solo escritor,
``tools/generar_matriz_precios_espana.py``, que lee este mismo registro en la
capa ``referencias_cotizadas_espana()``. Si se escribiera desde dos sitios, la
siguiente regeneración desharía el cambio sin avisar. Por eso este comando
comprueba que la matriz ya refleja el registro y falla si no es así.

Lo que hace, en este orden:

1. Valida el registro: el código existe en la matriz, la moneda es EUR, el
   precio es positivo, la banda es coherente (``min <= precio <= max``), el
   método y la confianza son conocidos y ni fuente ni criterio llevan el
   separador del CSV.
2. Comprueba que la matriz generada coincide con el registro. Si no coincide,
   indica que hay que ejecutar antes el generador.
3. Emite el SQL de carga acotado a esos recursos (no el fichero completo), con
   los valores tomados **de la matriz**, para que producción y repositorio no
   puedan divergir.

Nada de esto toca la base de datos: el SQL se ejecuta aparte.

Uso:
    python tools/aplicar_cotizaciones_espana.py            # valida y resume
    python tools/aplicar_cotizaciones_espana.py --aplicar  # escribe el SQL
"""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DOC = RAIZ / "docs/auditoria_precios"
MATRIZ = RAIZ / "basedatos_partidas/salida/precios_recursos_espana.csv"
FECHA = "2026-11-08"
DECISIONES = DOC / f"espana_decision_cotizaciones_{FECHA}.csv"
SALIDA_SQL = DOC / f"cotizaciones_es_{FECHA}.sql"

COLUMNAS = (
    "codigo_recurso", "descripcion", "categoria", "unidad_fuente", "pais_codigo",
    "moneda", "precio_referencia", "precio_min", "precio_max", "fuente",
    "fecha_consulta", "confianza", "incluye_iva", "incluye_transporte", "origen",
    "observaciones",
)
OBLIGATORIAS = ("codigo_recurso", "metodo", "precio", "precio_min", "precio_max",
                "confianza", "fuente", "criterio")
METODOS = {"cotizacion_directa", "banco_y_minorista", "banco"}
CONFIANZAS = {"alta", "media", "baja", "referencia", "derivado"}
MONEDA = "EUR"


def _leer(ruta: Path, obligatorias: tuple[str, ...] | None = None) -> list[dict[str, str]]:
    with ruta.open(encoding="utf-8-sig", newline="") as manejador:
        filas = list(csv.DictReader(manejador, delimiter=";"))
    if not filas:
        raise SystemExit(f"Fichero vacío: {ruta.name}")
    if obligatorias:
        faltan = [c for c in obligatorias if c not in filas[0]]
        if faltan:
            raise SystemExit(f"{ruta.name}: faltan columnas {', '.join(faltan)}")
    return filas


def _decimal(valor: str, campo: str, codigo: str) -> Decimal:
    texto = str(valor or "").strip().replace(",", ".")
    if not texto:
        raise SystemExit(f"{codigo}: {campo} vacío")
    try:
        numero = Decimal(texto)
    except InvalidOperation:
        raise SystemExit(f"{codigo}: {campo} no numérico ({valor!r})")
    if numero <= 0:
        raise SystemExit(f"{codigo}: {campo} no positivo ({numero})")
    return numero


def validar(decisiones: list[dict[str, str]],
            matriz: list[dict[str, str]]) -> dict[str, dict[str, Decimal]]:
    """Comprueba la coherencia del registro y devuelve los números por código."""
    por_codigo = {f["codigo_recurso"]: f for f in matriz}
    vistos: set[str] = set()
    numeros: dict[str, dict[str, Decimal]] = {}
    for fila in decisiones:
        codigo = (fila["codigo_recurso"] or "").strip()
        if not codigo:
            raise SystemExit("Hay una fila sin codigo_recurso")
        if codigo in vistos:
            raise SystemExit(f"{codigo}: duplicado en el registro")
        vistos.add(codigo)
        if codigo not in por_codigo:
            raise SystemExit(f"{codigo}: no está en la matriz de España")
        if por_codigo[codigo]["moneda"] != MONEDA or por_codigo[codigo]["pais_codigo"] != "ES":
            raise SystemExit(f"{codigo}: la matriz no es ES/{MONEDA}")
        if fila["metodo"] not in METODOS:
            raise SystemExit(f"{codigo}: método desconocido {fila['metodo']!r}")
        if fila["confianza"] not in CONFIANZAS:
            raise SystemExit(f"{codigo}: confianza desconocida {fila['confianza']!r}")
        for campo in ("fuente", "criterio"):
            texto = (fila[campo] or "").strip()
            if not texto:
                raise SystemExit(f"{codigo}: {campo} vacío")
            if ";" in texto:
                raise SystemExit(f"{codigo}: {campo} lleva el separador del CSV")
        precio = _decimal(fila["precio"], "precio", codigo)
        minimo = _decimal(fila["precio_min"], "precio_min", codigo)
        maximo = _decimal(fila["precio_max"], "precio_max", codigo)
        if not minimo <= precio <= maximo:
            raise SystemExit(
                f"{codigo}: banda incoherente (min {minimo} <= precio {precio} <= max {maximo})"
            )
        numeros[codigo] = {"precio": precio, "min": minimo, "max": maximo}
    return numeros


def comprobar_matriz(matriz: list[dict[str, str]],
                     decisiones: list[dict[str, str]],
                     numeros: dict[str, dict[str, Decimal]]) -> None:
    """La matriz tiene que haberse generado ya desde este registro."""
    por_codigo = {f["codigo_recurso"]: f for f in matriz}
    desajustes = []
    for fila in decisiones:
        codigo = fila["codigo_recurso"].strip()
        publicada = por_codigo[codigo]
        if (Decimal(publicada["precio_referencia"]) != numeros[codigo]["precio"]
                or Decimal(publicada["precio_min"]) != numeros[codigo]["min"]
                or Decimal(publicada["precio_max"]) != numeros[codigo]["max"]
                or publicada["fuente"] != fila["fuente"].strip()
                or publicada["fecha_consulta"] != FECHA):
            desajustes.append(codigo)
    if desajustes:
        raise SystemExit(
            "La matriz no refleja el registro en "
            f"{', '.join(sorted(desajustes))}: ejecuta antes "
            "`python tools/generar_matriz_precios_espana.py`"
        )


def _sql_texto(valor: str) -> str:
    return "'" + str(valor).replace("'", "''") + "'"


def generar_sql(decisiones: list[dict[str, str]],
                matriz: list[dict[str, str]]) -> Path:
    por_codigo = {f["codigo_recurso"]: f for f in matriz}
    bloques = []
    for fila in sorted(decisiones, key=lambda f: f["codigo_recurso"].strip()):
        codigo = fila["codigo_recurso"].strip()
        publicada = por_codigo[codigo]
        bloques.append(f"""-- {codigo}: {fila['metodo']} · adopta {publicada['precio_referencia']} EUR ({publicada['fuente']})
UPDATE public.precios_recursos_mercado
   SET precio = {publicada['precio_referencia']},
       precio_min = {publicada['precio_min']},
       precio_max = {publicada['precio_max']},
       moneda = {_sql_texto(publicada['moneda'])},
       confianza = {_sql_texto(publicada['confianza'])},
       incluye_iva = {_sql_texto(publicada['incluye_iva'])},
       fuente = {_sql_texto(publicada['fuente'])},
       fecha_consulta = DATE {_sql_texto(publicada['fecha_consulta'])},
       observaciones = {_sql_texto(publicada['observaciones'])}
 WHERE codigo_recurso = {_sql_texto(codigo)}
   AND pais_codigo = 'ES'
   AND organizacion_id IS NULL;""")

    codigos = ", ".join(_sql_texto(f["codigo_recurso"].strip())
                        for f in sorted(decisiones, key=lambda f: f["codigo_recurso"].strip()))
    sql = f"""-- CotizaT — cotizaciones reales de España, lote 1 ({FECHA}).
-- Generado por tools/aplicar_cotizaciones_espana.py desde
-- docs/auditoria_precios/espana_decision_cotizaciones_{FECHA}.csv y la matriz
-- basedatos_partidas/salida/precios_recursos_espana.csv.
--
-- ALCANCE: solo las referencias nacionales ES (sin organizacion_id) de los
-- {len(decisiones)} recursos cotizados. NO TOCA precios propios de empresas ni otros países.
-- MONEDA: EUR, precios sin IVA (la tabla guarda la moneda de cada mercado).

BEGIN;

{chr(10).join(bloques)}

-- Comprobación: debe devolver {len(decisiones)} filas con la banda coherente.
SELECT codigo_recurso, precio, precio_min, precio_max, moneda, confianza,
       incluye_iva, fecha_consulta
  FROM public.precios_recursos_mercado
 WHERE codigo_recurso IN ({codigos})
   AND pais_codigo = 'ES'
   AND organizacion_id IS NULL
 ORDER BY codigo_recurso;

COMMIT;
"""
    SALIDA_SQL.write_text(sql, encoding="utf-8")
    return SALIDA_SQL


def main(argv: list[str] | None = None) -> int:
    analizador = argparse.ArgumentParser(description=__doc__)
    analizador.add_argument("--aplicar", action="store_true",
                            help="escribe el SQL (por defecto solo valida y resume)")
    argumentos = analizador.parse_args(argv)

    decisiones = _leer(DECISIONES, OBLIGATORIAS)
    matriz = _leer(MATRIZ, COLUMNAS)
    numeros = validar(decisiones, matriz)
    comprobar_matriz(matriz, decisiones, numeros)

    for fila in sorted(decisiones, key=lambda f: f["codigo_recurso"]):
        codigo = fila["codigo_recurso"]
        print(f"{codigo:16s} {numeros[codigo]['precio']:>7} EUR "
              f"[{numeros[codigo]['min']}-{numeros[codigo]['max']}] · {fila['metodo']} "
              f"· {fila['confianza']}")

    if not argumentos.aplicar:
        print(f"\nValidado: {len(decisiones)} recursos coherentes con la matriz. "
              "Usa --aplicar para escribir el SQL.")
        return 0

    salida = generar_sql(decisiones, matriz)
    print(f"\nSQL escrito: {salida.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
