#!/usr/bin/env python3
"""Verifica que las matrices nacionales de precios del repo estén CARGADAS en la BD.

Compara las matrices oficiales de ``basedatos_partidas/salida/`` (las
mismas fuentes que leen las guías SEO y el importador) con las referencias
nacionales de ``precios_recursos_mercado`` (``organizacion_id IS NULL``) de
la base configurada por entorno (``DATABASE_URL`` o ``COTIZAT_DB``).

Responde, por país: filas esperadas según los CSV, filas presentes en BD,
faltantes, sobrantes y diferencias de precio. Si la matriz LatAm está entre
las verificadas, incluye la sección con los cinco oficios que publican las
guías de mano de obra: si la guía dice un número y la BD tiene otro (o
ninguno), el documento público y el catálogo del usuario cuentan historias
distintas.

Los precios esperados reproducen lo que el importador guarda de verdad:
en mercados imperiales (hoy EE. UU.) la BD conserva el precio ya
convertido a la unidad canónica del recurso, así que la comparación
aplica la misma conversión (``app.services.unidades_precio``) en vez de
acusar diferencias fantasma en cada fila.

Uso:
  python tools/verificar_matrices_bd.py                 # las 7 matrices, base del entorno
  DATABASE_URL=postgresql://… python tools/verificar_matrices_bd.py
  python tools/verificar_matrices_bd.py --csv basedatos_partidas/salida/precios_recursos_espana.csv
  python tools/verificar_matrices_bd.py --detalle 25    # más ejemplos

Sale con código 1 si hay faltantes o diferencias en lo esperado. Solo lee:
no importa, no migra, no escribe. Es el paso 4 del proceso de
actualización (docs/ACTUALIZACION_PRECIOS.md).
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SALIDA = ROOT / "basedatos_partidas/salida"
MATRIZ = SALIDA / "precios_recursos_latam.csv"

# Las matrices oficiales que el producto carga como referencias nacionales.
# No está `precios_recursos_latam_completa.csv`: es la fuente con respaldos
# por tipo de cambio (origen «base»), de la que se deriva la LatAm oficial.
MATRICES_OFICIALES = (
    MATRIZ,
    SALIDA / "precios_recursos_espana.csv",
    SALIDA / "precios_recursos_estados_unidos.csv",
    SALIDA / "precios_recursos_reino_unido.csv",
    SALIDA / "precios_recursos_canada.csv",
    SALIDA / "precios_recursos_irlanda.csv",
    SALIDA / "precios_recursos_australia.csv",
)

RECURSOS_JSON = ROOT / "basedatos_partidas/datos/recursos.json"

# Filas que el importador carga por defecto (app/services/
# importador_precios_mercado.py): confianza válida, fuera pendientes y
# fuera respaldos por tipo de cambio (origen "base", solo con
# --include-fallback). Si el criterio cambia ahí, cambia aquí.
CONFIANZAS = {"confirmado", "referencia", "derivado", "provisional"}


def _numero(valor: str) -> Decimal | None:
    try:
        numero = Decimal(str(valor).replace(",", "."))
    except (InvalidOperation, ValueError):
        return None
    return numero if numero.is_finite() and numero > 0 else None


def _unidades_por_codigo() -> dict[str, str]:
    """Unidad canónica de cada recurso según el catálogo base del repo."""
    try:
        datos = json.loads(RECURSOS_JSON.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    unidades: dict[str, str] = {}
    for grupo, recursos in datos.items():
        if grupo.startswith("_") or not isinstance(recursos, dict):
            continue
        for codigo, recurso in recursos.items():
            if isinstance(recurso, dict):
                unidades[str(codigo)] = str(recurso.get("unidad") or "")
    return unidades


def esperado_csv(
    ruta: Path, unidades: dict[str, str]
) -> tuple[dict[tuple[str, str], dict], int]:
    """Lo que el importador cargaría desde el CSV, sin tocar la BD.

    En un mercado imperial la BD guarda el precio ya convertido a la
    unidad canónica del recurso; aquí se aplica la misma conversión que
    el importador (incluidos mínimo y máximo) para comparar como con
    como. Devuelve también el conteo de filas que el importador habría
    rechazado por no poder convertirlas: no pueden estar en la BD, así
    que no son «esperadas», pero se avisan por si son un error de matriz.
    """
    from app.services.unidades_precio import (
        convertir_precio_unidad,
        normalizar_unidad,
        sistema_unidades_pais,
    )

    esperado: dict[tuple[str, str], dict] = {}
    no_verificables = 0
    with ruta.open(encoding="utf-8-sig", newline="") as archivo:
        for fila in csv.DictReader(archivo, delimiter=";"):
            origen = str(fila.get("origen") or "").strip()
            confianza = str(fila.get("confianza") or "").strip()
            if origen in {"pendiente", "base"} or confianza not in CONFIANZAS:
                continue
            precio = _numero(fila.get("precio_referencia") or "")
            if precio is None:
                continue
            clave = (
                str(fila.get("pais_codigo") or "").strip().upper(),
                str(fila.get("codigo_recurso") or "").strip(),
            )
            if not clave[0] or not clave[1]:
                continue
            precio_min = _numero(fila.get("precio_min") or "")
            precio_max = _numero(fila.get("precio_max") or "")
            if sistema_unidades_pais(clave[0]) == "imperial":
                unidad_fuente = normalizar_unidad(
                    fila.get("unidad_fuente") or ""
                )
                unidad_recurso = normalizar_unidad(unidades.get(clave[1], ""))
                if unidad_fuente != unidad_recurso:
                    factor = convertir_precio_unidad(
                        1.0, unidad_fuente, unidad_recurso
                    )
                    if factor is None:
                        no_verificables += 1
                        continue
                    factor_d = Decimal(str(factor))
                    precio = precio * factor_d
                    if precio_min is not None:
                        precio_min = precio_min * factor_d
                    if precio_max is not None:
                        precio_max = precio_max * factor_d
            esperado[clave] = {
                "precio": precio,
                "min": precio_min,
                "max": precio_max,
                "moneda": str(fila.get("moneda") or "").strip(),
            }
    return esperado, no_verificables


def cargado_bd() -> dict[tuple[str, str], dict]:
    # ORM y no SQL escrito a mano: «activo» es 1/0 en SQLite y boolean en
    # PostgreSQL, y una condición que mezcle ambas formas («= 1 OR IS
    # TRUE») la rechaza el analizador de Postgres. El ORM emite la forma
    # correcta en cada motor.
    from app.database import SessionLocal
    from app.models import PrecioRecursoMercado

    cargado: dict[tuple[str, str], dict] = {}
    with SessionLocal() as db:
        filas = (
            db.query(PrecioRecursoMercado)
            .filter(
                PrecioRecursoMercado.organizacion_id.is_(None),
                PrecioRecursoMercado.activo.is_(True),
                PrecioRecursoMercado.codigo_recurso != "",
            )
            .all()
        )
        for fila in filas:
            cargado[(str(fila.pais_codigo).upper(), str(fila.codigo_recurso))] = {
                "precio": Decimal(str(fila.precio)) if fila.precio is not None else None,
                "min": Decimal(str(fila.precio_min)) if fila.precio_min is not None else None,
                "max": Decimal(str(fila.precio_max)) if fila.precio_max is not None else None,
                "moneda": str(fila.moneda or ""),
            }
    return cargado


def _difiere(a: Decimal | None, b: Decimal | None) -> bool:
    if a is None or b is None:
        return a is not b
    # La BD guarda Float: tolerancia de representación, no de negocio.
    return abs(a - b) > max(Decimal("0.0001"), abs(a) * Decimal("0.000001"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--csv", type=Path, action="append", default=None,
                        help="matriz a verificar (repetible; por defecto, "
                        "las 7 oficiales)")
    parser.add_argument("--detalle", type=int, default=10,
                        help="ejemplos impresos por categoría y país")
    args = parser.parse_args()

    from app.database import DATABASE_IS_SQLITE, DATABASE_URL
    from app.seo_latam import OFICIOS
    from app.seo_latam_contenido import MERCADOS

    destino = "SQLite local" if DATABASE_IS_SQLITE else DATABASE_URL.split("@")[-1]
    rutas = list(args.csv) if args.csv else list(MATRICES_OFICIALES)
    incluye_latam = any(ruta.resolve() == MATRIZ.resolve() for ruta in rutas)
    print(f"Base verificada: {destino}")
    print("CSV esperados:")
    for ruta in rutas:
        mostrado = ruta.relative_to(ROOT) if ruta.is_relative_to(ROOT) else ruta
        print(f"  - {mostrado}")

    unidades = _unidades_por_codigo()
    esperado: dict[tuple[str, str], dict] = {}
    no_verificables = 0
    for ruta in rutas:
        parcial, sin_convertir = esperado_csv(ruta, unidades)
        esperado.update(parcial)
        no_verificables += sin_convertir
    if no_verificables:
        print(f"\nAviso: {no_verificables} filas no serían cargables por el "
              "importador (sin conversión de unidades posible); no se "
              "esperan en la BD.")
    cargado = cargado_bd()
    paises = sorted({p for p, _ in esperado} | {p for p, _ in cargado})

    fallos = 0
    print(f"\n{'Pais':<6} {'CSV':>6} {'BD':>6} {'Faltan':>7} {'Sobran':>7} {'Difieren':>9}")
    print("-" * 48)
    for pais in paises:
        esp = {c: v for (p, c), v in esperado.items() if p == pais}
        hay = {c: v for (p, c), v in cargado.items() if p == pais}
        faltan = sorted(set(esp) - set(hay))
        sobran = sorted(set(hay) - set(esp))
        difieren = [
            c for c in sorted(set(esp) & set(hay))
            if _difiere(esp[c]["precio"], hay[c]["precio"])
            or _difiere(esp[c]["min"], hay[c]["min"])
            or _difiere(esp[c]["max"], hay[c]["max"])
        ]
        fallos += len(faltan) + len(difieren)
        print(f"{pais:<6} {len(esp):>6} {len(hay):>6} {len(faltan):>7} "
              f"{len(sobran):>7} {len(difieren):>9}")
        for etiqueta, codigos in (("faltan", faltan), ("difieren", difieren)):
            for codigo in codigos[: args.detalle]:
                if etiqueta == "faltan":
                    print(f"    falta {codigo} (CSV: {esp[codigo]['precio']} {esp[codigo]['moneda']})")
                else:
                    print(f"    {codigo}: CSV {esp[codigo]['precio']} != BD {hay[codigo]['precio']}")
            if len(codigos) > args.detalle:
                print(f"    … y {len(codigos) - args.detalle} más ({etiqueta})")

    if incluye_latam:
        print(f"\nOficios publicados en las guías ({', '.join(OFICIOS)}):")
        for pais in MERCADOS:
            if pais == "VE":
                print("  VE     sin matriz CSV: la guía usa recursos.json; "
                      "la carga nacional VE se verifica con su SQL propio")
                continue
            estado = []
            for oficio in OFICIOS:
                clave = (pais, oficio)
                if clave not in cargado:
                    estado.append(f"{oficio}=AUSENTE")
                    fallos += 1
                elif clave in esperado and _difiere(esperado[clave]["precio"], cargado[clave]["precio"]):
                    estado.append(f"{oficio}=DISTINTO")
                    fallos += 1
                else:
                    estado.append(f"{oficio}=ok")
            print(f"  {pais:<6} " + "  ".join(estado))

    print("\nResultado:", "SIN DIFERENCIAS" if fallos == 0
          else f"{fallos} diferencias o faltantes que revisar")
    print("Nota: «sobran» no es fallo por sí solo (referencias fuera de las "
          "matrices pedidas o cargas históricas); faltantes y diferencias sí.")
    return 0 if fallos == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
