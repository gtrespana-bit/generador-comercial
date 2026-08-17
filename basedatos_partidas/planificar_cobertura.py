#!/usr/bin/env python3
"""Genera la matriz exhaustiva de cobertura de los 18 capítulos.

Fuentes:
- clasificacion.json: árbol aprobado;
- objetivos_cobertura.json: metas y criterios de producto;
- descompuestos/*.json: cobertura real;
- sinonimos_busqueda.json: tesauro por capítulo.

Salidas regenerables:
- salida/matriz_cobertura.json
- salida/matriz_cobertura.csv
- salida/RESUMEN_COBERTURA.md
"""
from __future__ import annotations

from collections import Counter
import csv
import json
import math
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATOS = BASE / "datos"
SALIDA = BASE / "salida"


def _leer(nombre: str) -> dict:
    return json.loads((DATOS / nombre).read_text(encoding="utf-8"))


def _partidas() -> list[dict]:
    return [
        json.loads(ruta.read_text(encoding="utf-8"))
        for ruta in sorted((DATOS / "descompuestos").glob("*.json"))
    ]


def _repartir(total: int, codigos: list[str], actuales: dict[str, int]) -> dict[str, int]:
    """Reparte un total exacto, garantizando suelo a familias aún vacías."""
    n = len(codigos)
    if not n:
        return {}
    suelo = max(2, total // (n * 3))
    base = {codigo: suelo for codigo in codigos}
    restante = total - suelo * n
    if restante < 0:
        # No ocurre con los objetivos actuales, pero mantiene la función total.
        return {codigo: total // n + (i < total % n) for i, codigo in enumerate(codigos)}
    pesos = {codigo: 1.0 + math.sqrt(max(0, actuales.get(codigo, 0))) for codigo in codigos}
    suma = sum(pesos.values()) or 1.0
    cuotas = {codigo: restante * pesos[codigo] / suma for codigo in codigos}
    for codigo in codigos:
        base[codigo] += math.floor(cuotas[codigo])
    faltan = total - sum(base.values())
    orden = sorted(
        codigos,
        key=lambda codigo: (cuotas[codigo] - math.floor(cuotas[codigo]), codigo),
        reverse=True,
    )
    for codigo in orden[:faltan]:
        base[codigo] += 1
    return base


def _estado(actual: int, objetivo: int) -> str:
    if actual == 0:
        return "sin_cobertura"
    proporcion = actual / objetivo if objetivo else 1
    if proporcion < 0.25:
        return "critica"
    if proporcion < 0.60:
        return "parcial"
    if proporcion < 1:
        return "avanzada"
    return "completa"


def construir() -> dict:
    taxonomia = _leer("clasificacion.json")
    objetivos = _leer("objetivos_cobertura.json")
    sinonimos = _leer("sinonimos_busqueda.json")
    partidas = _partidas()
    actuales = Counter((p["capitulo"], p["subcapitulo"]) for p in partidas)
    grupos_por_capitulo = Counter()
    terminos_por_capitulo = Counter()
    for grupo in sinonimos.get("grupos", []):
        cantidad_terminos = 1 + len(grupo.get("alias", []))
        for capitulo in grupo.get("capitulos", []):
            grupos_por_capitulo[str(capitulo)] += 1
            terminos_por_capitulo[str(capitulo)] += cantidad_terminos

    capitulos_salida = []
    filas_prioridad = []
    total_minimo = total_amplio = 0
    for cc, cap in taxonomia["capitulos"].items():
        plan = objetivos["capitulos"][cc]
        subs = cap.get("subcapitulos", {})
        codigos = list(subs)
        actuales_sub = {ss: actuales[(cc, ss)] for ss in codigos}
        meta_min = _repartir(int(plan["objetivo_minimo"]), codigos, actuales_sub)
        incremento = _repartir(
            int(plan["objetivo_amplio"]) - int(plan["objetivo_minimo"]),
            codigos,
            actuales_sub,
        )
        meta_amp = {ss: meta_min[ss] + incremento[ss] for ss in codigos}
        perfil = objetivos["perfiles_operacion"][plan["perfil"]]
        subcapitulos = []
        for ss, sub in subs.items():
            actual = actuales[(cc, ss)]
            minimo = meta_min[ss]
            amplio = meta_amp[ss]
            fila = {
                "codigo": f"{cc}.{ss}",
                "nombre": sub["nombre"],
                "partidas_actuales": actual,
                "apartados_actuales": len(sub.get("apartados", {})),
                "objetivo_minimo": minimo,
                "objetivo_amplio": amplio,
                "brecha_minima": max(0, minimo - actual),
                "brecha_amplia": max(0, amplio - actual),
                "estado": _estado(actual, minimo),
                "operaciones_requeridas": list(perfil),
                "variaciones_requeridas": list(plan["variaciones"]),
            }
            subcapitulos.append(fila)
            filas_prioridad.append({
                "capitulo": cc,
                "capitulo_nombre": cap["nombre"],
                **fila,
            })
        actual_cap = sum(actuales_sub.values())
        minimo_cap = int(plan["objetivo_minimo"])
        amplio_cap = int(plan["objetivo_amplio"])
        total_minimo += minimo_cap
        total_amplio += amplio_cap
        capitulos_salida.append({
            "codigo": cc,
            "nombre": cap["nombre"],
            "partidas_actuales": actual_cap,
            "objetivo_minimo": minimo_cap,
            "objetivo_amplio": amplio_cap,
            "brecha_minima": minimo_cap - actual_cap,
            "brecha_amplia": amplio_cap - actual_cap,
            "subcapitulos": subcapitulos,
            "grupos_sinonimos": grupos_por_capitulo[cc],
            "terminos_sinonimos": terminos_por_capitulo[cc],
        })

    if total_minimo != 3000 or total_amplio != 5000:
        raise ValueError(
            f"Los objetivos deben sumar 3000/5000; hoy suman {total_minimo}/{total_amplio}."
        )
    prioridades = sorted(
        filas_prioridad,
        key=lambda f: (
            f["estado"] != "sin_cobertura",
            -f["brecha_minima"],
            f["codigo"],
        ),
    )
    return {
        "version": 1,
        "ambito": "catalogo_general_venezuela",
        "partidas_actuales": len(partidas),
        "objetivo_minimo": total_minimo,
        "objetivo_amplio": total_amplio,
        "brecha_minima": total_minimo - len(partidas),
        "brecha_amplia": total_amplio - len(partidas),
        "capitulos": capitulos_salida,
        "prioridades": prioridades,
        "tesauro": {
            "grupos": len(sinonimos.get("grupos", [])),
            "terminos": sum(1 + len(g.get("alias", [])) for g in sinonimos.get("grupos", [])),
            "capitulos_cubiertos": len({
                str(c) for g in sinonimos.get("grupos", []) for c in g.get("capitulos", [])
            }),
        },
    }


def escribir(matriz: dict) -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    (SALIDA / "matriz_cobertura.json").write_text(
        json.dumps(matriz, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    with (SALIDA / "matriz_cobertura.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as fh:
        campos = [
            "capitulo", "capitulo_nombre", "codigo", "nombre", "estado",
            "partidas_actuales", "apartados_actuales", "objetivo_minimo",
            "objetivo_amplio", "brecha_minima", "brecha_amplia",
            "operaciones_requeridas", "variaciones_requeridas",
        ]
        writer = csv.DictWriter(fh, fieldnames=campos, delimiter=";", lineterminator="\n")
        writer.writeheader()
        for capitulo in matriz["capitulos"]:
            for sub in capitulo["subcapitulos"]:
                writer.writerow({
                    "capitulo": capitulo["codigo"],
                    "capitulo_nombre": capitulo["nombre"],
                    **{k: v for k, v in sub.items() if k not in {"operaciones_requeridas", "variaciones_requeridas"}},
                    "operaciones_requeridas": " | ".join(sub["operaciones_requeridas"]),
                    "variaciones_requeridas": " | ".join(sub["variaciones_requeridas"]),
                })

    estados = Counter(p["estado"] for p in matriz["prioridades"])
    lineas = [
        "# Resumen de cobertura del catálogo",
        "",
        f"- Partidas actuales: **{matriz['partidas_actuales']}**",
        f"- Objetivo mínimo: **{matriz['objetivo_minimo']}** (brecha {matriz['brecha_minima']})",
        f"- Objetivo amplio: **{matriz['objetivo_amplio']}** (brecha {matriz['brecha_amplia']})",
        f"- Subcapítulos sin cobertura: **{estados['sin_cobertura']}**",
        f"- Subcapítulos en estado crítico: **{estados['critica']}**",
        f"- Tesauro: **{matriz['tesauro']['grupos']} grupos · {matriz['tesauro']['terminos']} términos · {matriz['tesauro']['capitulos_cubiertos']} capítulos**",
        "",
        "## Estado por capítulo",
        "",
        "| Cap. | Capítulo | Actual | Mínimo | Amplio | Brecha mínima |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for cap in matriz["capitulos"]:
        lineas.append(
            f"| {cap['codigo']} | {cap['nombre']} | {cap['partidas_actuales']} | "
            f"{cap['objetivo_minimo']} | {cap['objetivo_amplio']} | {cap['brecha_minima']} |"
        )
    lineas.extend([
        "",
        "## Primeras 30 familias prioritarias",
        "",
        "| Código | Familia | Estado | Actual | Objetivo | Brecha |",
        "|---|---|---|---:|---:|---:|",
    ])
    for fila in matriz["prioridades"][:30]:
        lineas.append(
            f"| {fila['codigo']} | {fila['nombre']} | {fila['estado']} | "
            f"{fila['partidas_actuales']} | {fila['objetivo_minimo']} | {fila['brecha_minima']} |"
        )
    (SALIDA / "RESUMEN_COBERTURA.md").write_text(
        "\n".join(lineas) + "\n", encoding="utf-8"
    )


def main() -> int:
    matriz = construir()
    escribir(matriz)
    print(
        f"Matriz: {matriz['partidas_actuales']} actuales · "
        f"{matriz['objetivo_minimo']} mínimo · {matriz['objetivo_amplio']} amplio"
    )
    print(
        f"Tesauro: {matriz['tesauro']['grupos']} grupos · "
        f"{matriz['tesauro']['terminos']} términos · "
        f"{matriz['tesauro']['capitulos_cubiertos']} capítulos"
    )
    print("Salidas: matriz_cobertura.json, matriz_cobertura.csv, RESUMEN_COBERTURA.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
