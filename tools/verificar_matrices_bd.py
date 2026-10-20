#!/usr/bin/env python3
"""Verifica que la matriz nacional de precios del repo esté CARGADA en la BD.

Compara ``basedatos_partidas/salida/precios_recursos_latam.csv`` (la misma
fuente que leen las guías SEO y el importador) con las referencias
nacionales de ``precios_recursos_mercado`` (``organizacion_id IS NULL``) de
la base configurada por entorno (``DATABASE_URL`` o ``COTIZAT_DB``).

Responde, por país: filas esperadas según el CSV, filas presentes en BD,
faltantes, sobrantes y diferencias de precio. Incluye una sección con los
cinco oficios que publican las guías de mano de obra: si la guía dice un
número y la BD tiene otro (o ninguno), el documento público y el catálogo
del usuario cuentan historias distintas.

Uso:
  python tools/verificar_matrices_bd.py                 # base del entorno
  DATABASE_URL=postgresql://… python tools/verificar_matrices_bd.py
  python tools/verificar_matrices_bd.py --detalle 25    # más ejemplos

Sale con código 1 si hay faltantes o diferencias en lo esperado. Solo lee:
no importa, no migra, no escribe.
"""
from __future__ import annotations

import argparse
import csv
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

MATRIZ = ROOT / "basedatos_partidas/salida/precios_recursos_latam.csv"

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


def esperado_csv(ruta: Path) -> dict[tuple[str, str], dict]:
    esperado: dict[tuple[str, str], dict] = {}
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
            esperado[clave] = {
                "precio": precio,
                "min": _numero(fila.get("precio_min") or ""),
                "max": _numero(fila.get("precio_max") or ""),
                "moneda": str(fila.get("moneda") or "").strip(),
            }
    return esperado


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
    parser.add_argument("--csv", type=Path, default=MATRIZ)
    parser.add_argument("--detalle", type=int, default=10,
                        help="ejemplos impresos por categoría y país")
    args = parser.parse_args()

    from app.database import DATABASE_IS_SQLITE, DATABASE_URL
    from app.seo_latam import OFICIOS
    from app.seo_latam_contenido import MERCADOS

    destino = "SQLite local" if DATABASE_IS_SQLITE else DATABASE_URL.split("@")[-1]
    print(f"Base verificada: {destino}")
    print(f"CSV esperado:    {args.csv.relative_to(ROOT)}")

    esperado = esperado_csv(args.csv)
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
    print("Nota: «sobran» no es fallo por sí solo (matrices de otros mercados "
          "o cargas históricas); faltantes y diferencias sí.")
    return 0 if fallos == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
