#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generador de descompuestos en formato de hoja de descompuesto (estilo CYPE).

El importador del proyecto (`app/services/importer.py`) NO reconoce un
fichero por su origen, sino por su ESTRUCTURA: busca una fila de encabezados
con «Código, Unidad, Descripción, Rendimiento, Precio unitario, Importe» y a
partir de ahí deduce las columnas. Por tanto podemos escribir nosotros ese
mismo layout con datos 100% propios y la aplicación lo detecta igual de bien,
con todos los rendimientos por hora / m² de mano de obra, materiales y
maquinaria intactos.

Este módulo es la pieza que convierte una partida descrita en YAML/JSON
(datos/descompuestos/*.json) en el .xlsx que la app ingiere.

Uso:
    python3 basedatos_partidas/descompuestos.py            # genera todos
    python3 basedatos_partidas/descompuestos.py PRO-ALB-001
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
RAIZ = BASE.parent
ORIGEN = BASE / "datos" / "descompuestos"
SALIDA = BASE / "salida" / "descompuestos"

# Layout de 8 columnas (como DPT020.xlsx): A Código, D Unidad, E Descripción,
# F Rendimiento, G Precio unitario, H Importe.
COL_CODIGO, COL_UNIDAD, COL_DESCRIPCION = 1, 4, 5
COL_RENDIMIENTO, COL_PRECIO, COL_IMPORTE = 6, 7, 8

# Etiquetas de grupo que el clasificador del proyecto entiende
# (_categoria_coste_cype): materiales / equipo y maquinaria / mano de obra /
# costes directos complementarios.
ORDEN_GRUPOS = [
    ("materiales", "Materiales"),
    ("maquinaria", "Equipo y maquinaria"),
    ("mano_obra", "Mano de obra"),
]

F_IMPORTE = "=ROUND(INDIRECT(ADDRESS(ROW()+(0), COLUMN()+(-2), 1))*INDIRECT(ADDRESS(ROW()+(0), COLUMN()+(-1), 1)), 2)"


def _f_subtotal(n: int) -> str:
    partes = ",".join(
        f"INDIRECT(ADDRESS(ROW()+({-i}), COLUMN()+(0), 1))" for i in range(1, n + 1)
    )
    return f"=ROUND(SUM({partes}), 2)"


def _f_base_complementarios(offsets: list[int]) -> str:
    partes = ",".join(
        f"INDIRECT(ADDRESS(ROW()+({o}), COLUMN()+(1), 1))" for o in offsets
    )
    return f"=ROUND(SUM({partes}), 2)"


def _f_total(offsets: list[int]) -> str:
    partes = ",".join(
        f"INDIRECT(ADDRESS(ROW()+({o}), COLUMN()+(0), 1))" for o in offsets
    )
    return f"=ROUND(SUM({partes}), 2)"


F_COMPLEMENTARIOS = "=ROUND(INDIRECT(ADDRESS(ROW()+(0), COLUMN()+(-2), 1))*INDIRECT(ADDRESS(ROW()+(0), COLUMN()+(-1), 1))/100, 2)"


def construir_hoja(partida: dict, ruta: Path) -> dict:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, Side

    wb = Workbook()
    ws = wb.active
    ws.title = partida["codigo"][:31]

    negrita = Font(bold=True)
    ajuste = Alignment(wrap_text=True, vertical="top")
    fino = Side(style="thin", color="999999")

    # --- Cabecera de la partida (filas 3 y 5) ---
    ws.cell(3, 1, partida["codigo"]).font = negrita
    ws.cell(3, 2, partida["unidad"])
    ws.cell(3, 3, partida["titulo"]).font = negrita
    ws.merge_cells(start_row=3, start_column=3, end_row=3, end_column=8)
    ws.cell(5, 1, partida["descripcion"].rstrip() + "\n").alignment = ajuste
    ws.merge_cells(start_row=5, start_column=1, end_row=5, end_column=8)

    # --- Fila de encabezados (fila 8) ---
    encabezados = {
        COL_CODIGO: "Código", COL_UNIDAD: "Unidad", COL_DESCRIPCION: "Descripción",
        COL_RENDIMIENTO: "Rendimiento", COL_PRECIO: "Precio\nunitario", COL_IMPORTE: "Importe",
    }
    for col, texto in encabezados.items():
        celda = ws.cell(8, col, texto)
        celda.font = negrita
        celda.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
        celda.border = Border(top=fino, bottom=fino)

    fila = 9
    indice = 0
    filas_subtotal: list[int] = []   # filas donde queda cada subtotal
    totales: dict[str, float] = {}

    recursos = partida.get("recursos", [])
    for clave, etiqueta in ORDEN_GRUPOS:
        del_grupo = [r for r in recursos if r.get("grupo") == clave]
        if not del_grupo:
            continue
        indice += 1
        ws.cell(fila, COL_CODIGO, indice)
        ws.cell(fila, COL_DESCRIPCION, etiqueta).font = negrita
        fila += 1
        primera = fila
        acumulado = 0.0
        for r in del_grupo:
            rendimiento = float(r["rendimiento"])
            precio = float(r["precio"])
            acumulado += round(rendimiento * precio, 2)
            ws.cell(fila, COL_CODIGO, r["codigo"])
            ws.cell(fila, COL_UNIDAD, r["unidad"])
            ws.cell(fila, COL_DESCRIPCION, r["descripcion"]).alignment = ajuste
            ws.cell(fila, COL_RENDIMIENTO, rendimiento)
            ws.cell(fila, COL_PRECIO, precio)
            ws.cell(fila, COL_IMPORTE, round(rendimiento * precio, 2))
            fila += 1
        ws.cell(fila, COL_RENDIMIENTO, f"Subtotal {etiqueta.lower()}:").font = negrita
        ws.cell(fila, COL_IMPORTE, round(acumulado, 2))
        filas_subtotal.append(fila)
        totales[clave] = round(acumulado, 2)
        fila += 1

    if not filas_subtotal:
        raise ValueError(f"{partida['codigo']}: la partida no tiene recursos.")

    # --- Costes directos complementarios (% sobre la suma de subtotales) ---
    pct = float(partida.get("complementarios_pct", 2))
    indice += 1
    ws.cell(fila, COL_CODIGO, indice)
    ws.cell(fila, COL_DESCRIPCION, "Costes directos complementarios").font = negrita
    fila += 1
    fila_pct = fila
    ws.cell(fila, COL_UNIDAD, "%")
    ws.cell(fila, COL_DESCRIPCION, "Costes directos complementarios")
    ws.cell(fila, COL_RENDIMIENTO, pct)
    base = round(sum(totales.values()), 2)
    ws.cell(fila, COL_PRECIO, base)
    totales["complementarios"] = round(base * pct / 100, 2)
    ws.cell(fila, COL_IMPORTE, totales["complementarios"])
    fila += 1

    # --- Costes directos (1+2+...) ---
    fila_total = fila
    etiqueta_total = "Costes directos (" + "+".join(str(i) for i in range(1, indice + 1)) + "):"
    ws.cell(fila, COL_RENDIMIENTO, etiqueta_total).font = negrita
    ws.cell(fila, COL_IMPORTE, round(sum(totales.values()), 2)).font = negrita
    for col in range(1, 9):
        ws.cell(fila, col).border = Border(top=fino)

    # --- Formato ---
    for col, ancho in zip("ABCDEFGH", (16, 8, 4, 10, 62, 13, 12, 12)):
        ws.column_dimensions[col].width = ancho
    ws.row_dimensions[5].height = 60

    ruta.parent.mkdir(parents=True, exist_ok=True)
    wb.save(ruta)

    total = round(sum(totales.values()), 2)
    return {"totales": totales, "coste_directo": total}


def validar(ruta: Path) -> dict:
    """Comprueba el .xlsx con el lector CYPE real del proyecto."""
    sys.path.insert(0, str(RAIZ))
    from app.services import importer

    datos = ruta.read_bytes()
    if not importer.es_formato_cype_xlsx(datos):
        return {"detectado": False}
    analisis = importer.analizar_cype_xlsx(datos)
    partidas = analisis.get("partidas", [])
    return {"detectado": True, "analisis": analisis, "partidas": partidas}


def main(argv: list[str]) -> int:
    if not ORIGEN.exists():
        sys.exit(f"No existe {ORIGEN}")
    fuentes = sorted(ORIGEN.glob("*.json"))
    if argv:
        fuentes = [f for f in fuentes if f.stem in argv]
    if not fuentes:
        sys.exit("No hay descompuestos que generar.")

    fallos = 0
    for fuente in fuentes:
        partida = json.loads(fuente.read_text(encoding="utf-8"))
        destino = SALIDA / f"{partida['codigo']}.xlsx"
        resumen = construir_hoja(partida, destino)
        print(f"\n{partida['codigo']}  {partida['titulo']}")
        print(f"  archivo        : {destino.relative_to(RAIZ)}")
        for clave, valor in resumen["totales"].items():
            print(f"  {clave:<16}: {valor:>8.2f} €")
        print(f"  {'COSTE DIRECTO':<16}: {resumen['coste_directo']:>8.2f} €")

        v = validar(destino)
        if not v["detectado"]:
            print("  ✗ El proyecto NO lo reconoce como formato de descompuesto")
            fallos += 1
            continue
        leidas = v["partidas"]
        if not leidas:
            print("  ✗ Reconocido, pero sin partidas legibles")
            fallos += 1
            continue
        p = leidas[0]
        costes = p.get("costes", {})
        print(f"  ✓ detectado: código «{p.get('codigo')}», unidad «{p.get('unidad')}», "
              f"{len(p.get('filas', []))} filas")
        print(f"    costes leídos por la app: " + ", ".join(
            f"{k}={v:.2f}" for k, v in costes.items() if isinstance(v, (int, float))))
        horas = sum(float(r["rendimiento"]) for r in partida.get("recursos", [])
                    if r.get("grupo") == "mano_obra")
        print(f"    horas de mano de obra por {partida['unidad']}: {horas:.3f} h")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
