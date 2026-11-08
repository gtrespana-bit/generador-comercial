#!/usr/bin/env python3
"""Clasifica cada recurso sin precio según lo cerca que esté su artículo en el banco.

Responde a una pregunta concreta: cuando un recurso se queda sin precio, ¿es
porque el banco **no tiene** ese artículo o porque no lo estamos encontrando?
Para cada recurso sin precio revisado se toma el mejor candidato del cribado
publicado y se etiqueta el hueco:

``equivalente_en_la_base``
    Una ficha del banco es el mismo artículo (seleccionada a mano en
    ``espana_fuentes_extremadura_identidad_*.csv``): el hueco es de identidad.
``misma_familia_sin_medida``
    El banco tiene la familia pero no la medida o clase del recurso (bloques de
    otra dimensión, hormigón de otra resistencia): falta especificación.
``solo_parecido_de_nombre``
    El candidato comparte palabras pero es otro producto (extintor de 50 kg para
    un recurso de 6 kg): el nombre engaña y no se puede confirmar.
``sin_candidato``
    Ni siquiera hay un candidato débil en el banco: el artículo no está.

El script no toca precios ni estados: escribe una tabla de diagnóstico
reproducible a partir de los CSV ya versionados.

Uso:
    python tools/auditar_huecos_identidad_espana.py
"""
from __future__ import annotations

import csv
import os
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/auditoria_precios"
REGISTRO = DOC / "espana_2026-11-06.csv"
CRIBADO = DOC / "espana_cribado_extremadura_2026-11-07.csv"
# Cribado con sinónimos (tornillería/tornillo, hormigón/concreto, motosierra/
# sierra): recupera fichas que el cribado publicado no ve por el núcleo literal.
EQUIVALENCIAS = DOC / "espana_equivalencias_extremadura_2026-11-07.csv"
IDENTIDAD = DOC / "espana_fuentes_extremadura_identidad_2026-11-07.csv"
SALIDA = DOC / "espana_identidad_huecos_2026-11-07.csv"

PRECISION_MINIMA = Decimal("0.50")


def leer(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as manejador:
        return list(csv.DictReader(manejador, delimiter=";"))


def decimal(valor) -> Decimal | None:
    try:
        return Decimal(str(valor).replace(",", "."))
    except (InvalidOperation, ValueError, AttributeError):
        return None


def es_agregado(descripcion: str) -> bool:
    """¿El recurso es una cesta de artículos en vez de un artículo?"""
    texto = descripcion.strip()
    if texto.lower().startswith(("consumibles de", "juego de", "equipo de", "kit de")):
        return True
    # Enumeración explícita: "Consumibles: puntas, discos y hojas".
    return ":" in texto and texto.split(":", 1)[1].count(",") >= 2


def diagnostico(recurso: dict, candidato: dict | None, elegido: dict | None) -> tuple[str, str]:
    if elegido is not None:
        return ("equivalente_en_la_base",
                "La ficha del banco es el mismo artículo (fijado a mano): "
                + elegido["alcance_y_reservas"])
    if es_agregado(recurso["descripcion"]):
        return ("agregado_por_componentes",
                "El recurso es una cesta de artículos con precios distintos: no admite una "
                "ficha única y debe desglosarse antes de asignar precio.")
    if candidato is None:
        return ("sin_candidato",
                "Ningún precio simple del banco comparte núcleo ni unidad con el recurso.")
    precision = decimal(candidato["precision"]) or Decimal("0")
    if precision < PRECISION_MINIMA:
        return ("solo_parecido_de_nombre",
                "El candidato más próximo comparte palabras sueltas pero no describe el "
                "artículo: no se puede confirmar ni usar como referencia.")
    if candidato["numeros_compatibles"] != "si":
        return ("misma_familia_sin_medida",
                "El banco tiene la familia, pero la medida o clase del candidato no "
                "coincide con la del recurso.")
    return ("misma_familia_sin_medida",
            "El banco tiene la familia con las medidas compatibles, pero la ficha no "
            "acredita la misma especificación; requiere revisión.")


def main() -> int:
    registro = leer(REGISTRO)
    mejores: dict[str, dict] = {}
    for fila in leer(EQUIVALENCIAS if EQUIVALENCIAS.exists() else CRIBADO):
        if not fila["codigo_fuente"] or fila["rango"] != "1":
            continue
        mejores[fila["codigo_recurso"]] = dict(fila, via="sinonimos")
    for fila in leer(CRIBADO):
        if not fila["codigo_fuente"] or fila["rango"] != "1":
            continue
        previo = mejores.get(fila["codigo_recurso"])
        # El cribado publicado manda si su ficha está igual o mejor especificada.
        if previo is None or decimal(fila["precision"]) >= decimal(previo["precision"]):
            mejores[fila["codigo_recurso"]] = dict(fila, via="publicado")
    elegidos = {f["codigo_recurso"]: f for f in leer(IDENTIDAD)} if IDENTIDAD.exists() else {}

    salida = []
    for recurso in registro:
        if recurso["precio_revisado"].strip():
            continue
        codigo = recurso["codigo_recurso"]
        candidato = mejores.get(codigo)
        elegido = elegidos.get(codigo)
        etiqueta, motivo = diagnostico(recurso, candidato, elegido)
        salida.append({
            "codigo_recurso": codigo,
            "categoria": recurso["categoria"],
            "unidad": recurso["unidad"],
            "usos": recurso["partidas_que_lo_usan"],
            "descripcion_recurso": recurso["descripcion"][:120],
            "diagnostico": etiqueta,
            "codigo_fuente": (elegido or candidato or {}).get("codigo_fuente", ""),
            "descripcion_fuente": ((elegido or {}).get("alcance_y_reservas", "")
                                   if elegido else (candidato or {}).get("descripcion_fuente", ""))[:120],
            "precio_fuente": ((elegido or {}).get("precio_eur", "")
                              if elegido else (candidato or {}).get("precio_fuente", "")),
            "precision": (candidato or {}).get("precision", ""),
            "cobertura": (candidato or {}).get("cobertura", ""),
            "numeros_compatibles": (candidato or {}).get("numeros_compatibles", ""),
            "via": (candidato or {}).get("via", ""),
            "motivo": motivo,
        })

    salida.sort(key=lambda f: (-int(f["usos"] or 0), f["codigo_recurso"]))
    if not salida:
        # Auditoría cerrada: no se sobrescribe la tabla publicada, que es el
        # registro histórico de los huecos que existieron y cómo se cerraron.
        print("0 recursos sin precio revisado: la tabla publicada se conserva como "
              f"registro histórico de {len(leer(SALIDA))} huecos ya cerrados.")
        return os.EX_OK
    with SALIDA.open("w", encoding="utf-8-sig", newline="") as manejador:
        escritor = csv.DictWriter(manejador, fieldnames=list(salida[0]), delimiter=";",
                                  lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(salida)

    cuenta: dict[str, int] = {}
    usos: dict[str, int] = {}
    for fila in salida:
        cuenta[fila["diagnostico"]] = cuenta.get(fila["diagnostico"], 0) + 1
        usos[fila["diagnostico"]] = usos.get(fila["diagnostico"], 0) + int(fila["usos"] or 0)
    print(f"{len(salida)} recursos sin precio revisado clasificados:")
    for etiqueta, cuantos in sorted(cuenta.items(), key=lambda kv: -kv[1]):
        print(f"  {etiqueta:28} {cuantos:>4} recursos  {usos[etiqueta]:>5} usos")
    print(f"Escrito {SALIDA.relative_to(ROOT)}; no se ha modificado ningún precio")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
