#!/usr/bin/env python3
"""Aplica confirmaciones de precio verificadas de forma independiente (España).

Toma la tabla de confirmaciones que genera ``tools/verificar_precios_espana.py``
y mueve cada recurso de ``en_revision`` a ``confirmado_referencia`` **sin tocar
el precio**: la cifra confirmada es la que ya estaba revisada, y lo que cambia
es la evidencia que la sostiene.

Validación (todo o nada, igual que el cierre):

1. El recurso existe y está ``en_revision`` con precio revisado.
2. La observación independiente cae dentro del ±15 % del precio revisado.
3. La observación trae fuente y código, y no es el mismo documento que originó
   el precio.
4. No hay recursos repetidos en la tabla.

Uso:
    python3 tools/confirmar_precios_espana.py            # valida sin escribir
    python3 tools/confirmar_precios_espana.py --aplicar   # actualiza el registro
"""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal
from pathlib import Path

if __package__:
    from .cerrar_auditoria_espana import decimal, escribir, leer, limpiar_marca, unir
else:
    from cerrar_auditoria_espana import decimal, escribir, leer, limpiar_marca, unir

ROOT = Path(__file__).resolve().parents[1]
REGISTRO = ROOT / "docs/auditoria_precios/espana_2026-11-06.csv"
CONFIRMACIONES = ROOT / "docs/auditoria_precios/espana_confirmaciones_2026-11-07.csv"
FECHA = "2026-11-07"
MARCA = "Confirmación 2026-11-07"
TOLERANCIA = Decimal("0.15")


def validar(filas: list[dict], registro: dict[str, dict]) -> None:
    vistos = set()
    for fila in filas:
        codigo = fila["codigo_recurso"]
        if codigo in vistos:
            raise ValueError(f"Recurso duplicado en las confirmaciones: {codigo}")
        vistos.add(codigo)
        recurso = registro.get(codigo)
        if recurso is None:
            raise ValueError(f"Recurso inexistente: {codigo}")
        if recurso["estado_auditoria"] == "confirmado_referencia" and MARCA in recurso[
                "evidencia_y_pendientes"]:
            continue  # ya aplicada por este mismo lote: reintento idempotente
        if recurso["estado_auditoria"] != "en_revision":
            raise ValueError(f"{codigo}: solo se confirman recursos en revisión "
                             f"(estado actual: {recurso['estado_auditoria']})")
        revisado = decimal(recurso["precio_revisado"], codigo)
        referencia = decimal(fila["precio"], codigo)
        if abs(referencia / revisado - 1) > TOLERANCIA:
            raise ValueError(f"{codigo}: la referencia {referencia} se aleja más del 15 % "
                             f"del precio revisado {revisado}")
        for campo in ("fuente", "codigo_fuente", "criterio"):
            if not fila[campo].strip():
                raise ValueError(f"{codigo}: la confirmación exige {campo}")


def aplicar(filas: list[dict], registro: dict[str, dict]) -> tuple[list[dict], list[str]]:
    cambios = []
    for fila in filas:
        codigo = fila["codigo_recurso"]
        recurso = registro[codigo]
        if recurso["estado_auditoria"] == "confirmado_referencia":
            continue
        texto = f"{MARCA}: {fila['criterio']} Reserva: {fila['reserva']}".strip()
        recurso["estado_auditoria"] = "confirmado_referencia"
        recurso["fecha_revision"] = FECHA
        recurso["fuente_observada"] = unir(recurso["fuente_observada"],
                                          f"{fila['fuente']} ({fila['codigo_fuente']})")
        recurso["evidencia_y_pendientes"] = (
            limpiar_marca(recurso["evidencia_y_pendientes"], MARCA) + " " + texto).strip()
        cambios.append(codigo)
    return [registro[c] for c in sorted(registro)], cambios


def main() -> int:
    analizador = argparse.ArgumentParser(description=__doc__,
                                        formatter_class=argparse.RawDescriptionHelpFormatter)
    analizador.add_argument("--confirmaciones", type=Path, default=CONFIRMACIONES)
    analizador.add_argument("--registro", type=Path, default=REGISTRO)
    analizador.add_argument("--aplicar", action="store_true")
    argumentos = analizador.parse_args()

    filas = leer(argumentos.confirmaciones)
    registro = {f["codigo_recurso"]: f for f in leer(argumentos.registro)}
    validar(filas, registro)
    print(f"Confirmaciones válidas: {len(filas)} "
          f"({sum(int(registro[f['codigo_recurso']]['partidas_que_lo_usan']) for f in filas)} usos)")
    if not argumentos.aplicar:
        print("Comprobación sin escritura. Use --aplicar para actualizar el registro.")
        return 0
    orden, cambios = aplicar(filas, registro)
    campos = list(leer(argumentos.registro)[0])
    escribir(argumentos.registro, campos, orden)
    estados = {}
    for fila in orden:
        estados[fila["estado_auditoria"]] = estados.get(fila["estado_auditoria"], 0) + 1
    print(f"Confirmados: {', '.join(cambios)}")
    print(f"Escrito {argumentos.registro.relative_to(ROOT)}: {estados}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
