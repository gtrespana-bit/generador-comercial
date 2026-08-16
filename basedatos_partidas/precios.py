#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Revisión de precios en bloque del cuadro de recursos.

Los precios viven SOLO en `datos/recursos.json`; las partidas guardan
rendimientos y referencian recursos por código. Por eso actualizar precios
nunca obliga a tocar una partida: se cambia el cuadro y se regenera.

Dos modos:

    python3 basedatos_partidas/precios.py exportar
        Genera `salida/precios_para_revisar.csv` con todos los recursos,
        ORDENADOS POR IMPACTO: primero los que más peso tienen en el coste
        del catálogo. Se rellena la columna `precio_nuevo` y ya está.

    python3 basedatos_partidas/precios.py aplicar
        Lee ese CSV, vuelca los precios nuevos a recursos.json y marca los
        recursos actualizados como «confirmado». Deja copia de seguridad.

Después basta con:
    python3 basedatos_partidas/descompuestos.py && python3 basedatos_partidas/construir.py
"""
from __future__ import annotations

import csv
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
RAIZ = BASE.parent
RECURSOS = BASE / "datos" / "recursos.json"
DESCOMPUESTOS = BASE / "datos" / "descompuestos"
REVISION = BASE / "salida" / "precios_para_revisar.csv"

CABECERAS = [
    "codigo", "grupo", "descripcion", "unidad", "precio_actual", "moneda",
    "estado", "partidas_que_lo_usan", "peso_en_catalogo_usd", "precio_nuevo", "notas",
]


def cargar() -> dict:
    return json.loads(RECURSOS.read_text(encoding="utf-8"))


def impacto() -> tuple[dict[str, int], dict[str, float]]:
    """Cuenta en cuántas partidas aparece cada recurso y cuánto coste aporta."""
    bruto = cargar()
    precios = {}
    for grupo in ("materiales", "maquinaria", "mano_obra"):
        for cod, ficha in (bruto.get(grupo) or {}).items():
            precios[cod] = float(ficha["precio"])

    usos: dict[str, int] = {}
    peso: dict[str, float] = {}
    for fuente in sorted(DESCOMPUESTOS.glob("*.json")):
        partida = json.loads(fuente.read_text(encoding="utf-8"))
        for linea in partida.get("recursos", []):
            ref = linea.get("ref")
            if not ref:
                continue
            usos[ref] = usos.get(ref, 0) + 1
            peso[ref] = round(
                peso.get(ref, 0.0) + float(linea["rendimiento"]) * precios.get(ref, 0.0), 4
            )
    return usos, peso


def exportar() -> int:
    bruto = cargar()
    moneda = bruto.get("_moneda", "USD")
    usos, peso = impacto()

    filas = []
    for grupo in ("materiales", "maquinaria", "mano_obra"):
        for cod, ficha in (bruto.get(grupo) or {}).items():
            filas.append({
                "codigo": cod,
                "grupo": grupo,
                "descripcion": ficha["descripcion"],
                "unidad": ficha["unidad"],
                "precio_actual": f"{float(ficha['precio']):.4f}",
                "moneda": moneda,
                "estado": ficha.get("estado", ""),
                "partidas_que_lo_usan": usos.get(cod, 0),
                "peso_en_catalogo_usd": f"{peso.get(cod, 0.0):.2f}",
                "precio_nuevo": "",
                "notas": "",
            })

    # Los provisionales de más peso primero: es donde rinde el esfuerzo.
    filas.sort(key=lambda f: (
        f["estado"] == "confirmado",
        -float(f["peso_en_catalogo_usd"]),
        f["codigo"],
    ))

    REVISION.parent.mkdir(parents=True, exist_ok=True)
    with REVISION.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CABECERAS, delimiter=";")
        w.writeheader()
        w.writerows(filas)

    pend = [f for f in filas if f["estado"] != "confirmado"]
    print(f"Exportados {len(filas)} recursos -> {REVISION.relative_to(RAIZ)}")
    print(f"Pendientes de confirmar: {len(pend)}\n")
    print("Los 10 de mayor impacto en el coste del catálogo:")
    print(f"  {'CÓDIGO':<15}{'UD':<5}{'PRECIO':>9}{'USOS':>6}{'PESO':>9}  ESTADO")
    for f in filas[:10]:
        print(f"  {f['codigo']:<15}{f['unidad']:<5}{float(f['precio_actual']):>9.2f}"
              f"{f['partidas_que_lo_usan']:>6}{float(f['peso_en_catalogo_usd']):>9.2f}"
              f"  {f['estado']}")
    print("\nRellena la columna «precio_nuevo» y ejecuta:  python3 basedatos_partidas/precios.py aplicar")
    return 0


def aplicar() -> int:
    if not REVISION.exists():
        sys.exit(f"No existe {REVISION}. Ejecuta primero: precios.py exportar")

    bruto = cargar()
    with REVISION.open(encoding="utf-8-sig", newline="") as fh:
        filas = list(csv.DictReader(fh, delimiter=";"))

    cambios, errores = [], []
    for fila in filas:
        nuevo = (fila.get("precio_nuevo") or "").strip().replace(",", ".")
        if not nuevo:
            continue
        codigo, grupo = fila["codigo"].strip(), fila["grupo"].strip()
        try:
            valor = float(nuevo)
        except ValueError:
            errores.append(f"{codigo}: «{nuevo}» no es un número")
            continue
        if valor < 0:
            errores.append(f"{codigo}: precio negativo")
            continue
        ficha = (bruto.get(grupo) or {}).get(codigo)
        if not ficha:
            errores.append(f"{codigo}: no existe en el grupo «{grupo}»")
            continue
        anterior = float(ficha["precio"])
        if abs(anterior - valor) < 1e-9:
            continue
        ficha["precio"] = round(valor, 4)
        ficha["estado"] = "confirmado"
        if (fila.get("notas") or "").strip():
            ficha["nota"] = fila["notas"].strip()
        variacion = ((valor - anterior) / anterior * 100) if anterior else 0.0
        cambios.append((codigo, anterior, valor, variacion))

    if errores:
        print("Errores (no se ha aplicado nada):")
        for e in errores:
            print("  -", e)
        return 1
    if not cambios:
        print("No hay precios nuevos que aplicar.")
        return 0

    copia = RECURSOS.with_suffix(f".{datetime.now():%Y%m%d-%H%M%S}.bak.json")
    shutil.copy2(RECURSOS, copia)
    bruto["_revision"] = f"{datetime.now():%Y-%m} · actualización en bloque"
    RECURSOS.write_text(json.dumps(bruto, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Copia de seguridad -> {copia.name}")
    print(f"\n{len(cambios)} precios actualizados:")
    print(f"  {'CÓDIGO':<15}{'ANTES':>10}{'AHORA':>10}{'VAR.':>9}")
    for cod, ant, nue, var in cambios:
        print(f"  {cod:<15}{ant:>10.2f}{nue:>10.2f}{var:>8.1f}%")
    print("\nRegenera con:")
    print("  python3 basedatos_partidas/descompuestos.py && python3 basedatos_partidas/construir.py")
    return 0


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "exportar"
    if modo not in ("exportar", "aplicar"):
        sys.exit("Uso: precios.py [exportar|aplicar]")
    raise SystemExit(exportar() if modo == "exportar" else aplicar())
