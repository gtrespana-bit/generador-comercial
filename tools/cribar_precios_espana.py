#!/usr/bin/env python3
"""Cribado masivo de recursos españoles contra un banco de precios BCCA/CERP.

Sustituye la búsqueda manual de un recurso por lote: lee el registro de
auditoría, la matriz local y el archivo ``basicos.json`` del banco abierto
CERP (precios BCCA de Andalucía) y propone candidatos **ordenados por
precisión**, no por coincidencia de palabras sueltas.

La ordenación por precisión exige que el candidato sea un subconjunto
razonable del texto del recurso (``precision``) y que comparta el núcleo
(primera palabra significativa). Se conservan además ``cobertura``, la
compatibilidad de números (medidas, diámetros, espesores) y la desviación
frente al precio actual de la matriz.

Este comando **no aplica precios ni cambia estados**: genera una tabla de
revisión que después se adjudica de forma explícita en
``docs/auditoria_precios/espana_adjudicacion_2026-11-07.csv`` y se aplica con
``tools/cerrar_auditoria_espana.py``.

Cómo obtener el banco (no se descarga solo, para que quede trazado):

    curl -L https://codeload.github.com/cerptech/cerp-items-data/tar.gz/refs/tags/v0.7.0 \
        | tar -xz -C /tmp && ls /tmp/cerp-items-data-*/data/basicos.json

El comando imprime versión y ``sha256`` del archivo usado: anotarlos en el
informe de cierre para que el cribado sea reproducible.

Uso:
    python tools/cribar_precios_espana.py \
        --basicos /ruta/al/basicos.json \
        --salida docs/auditoria_precios/espana_cribado_bcca_2026-11-07.csv
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path

if __package__:
    from .cruzar_precios_bc3 import leer_bc3, limpiar, unidad
else:
    from cruzar_precios_bc3 import leer_bc3, limpiar, unidad

ROOT = Path(__file__).resolve().parents[1]
AUDITORIA = ROOT / "docs/auditoria_precios/espana_2026-11-06.csv"
MATRIZ = ROOT / "basedatos_partidas/salida/precios_recursos_espana.csv"
SALIDA = ROOT / "docs/auditoria_precios/espana_cribado_bcca_2026-11-07.csv"
EDICION_ESPERADA = "2024-01"

# Palabras que no distinguen producto y que, si se exigen, producen falsos positivos.
GENERICAS = {
    "tipo", "clase", "uso", "obra", "obras", "material", "materiales", "equipo",
    "sistema", "elemento", "elementos", "vario", "varios", "general", "generico",
    "incluida", "incluido", "incluye", "amortizacion", "consumo", "consumos",
    "ud", "u", "m", "m2", "m3", "kg", "l", "h", "mm", "cm",
}
TIPOS = {"material": "materiales", "machinery": "maquinaria", "labor": "mano_obra"}


def tokens(texto: str) -> list[str]:
    """Tokens significativos, sin acentos y sin plurales triviales."""
    salida = []
    for palabra in re.findall(r"[a-z]+|\d+(?:[.,]\d+)?", limpiar(texto)):
        palabra = palabra.replace(",", ".")
        if palabra in GENERICAS:
            continue
        if len(palabra) < 3 and not palabra.isdigit():
            continue
        salida.append(palabra[:-1] if len(palabra) > 5 and palabra.endswith("s") else palabra)
    return salida


def numeros(tokens_: list[str]) -> set[str]:
    return {t for t in tokens_ if re.fullmatch(r"\d+(?:\.\d+)?", t)}


def decimal(valor) -> Decimal | None:
    if valor is None or valor == "":
        return None
    try:
        numero = Decimal(str(valor).replace(",", "."))
    except (InvalidOperation, ValueError):
        return None
    return numero if numero.is_finite() and numero > 0 else None


def cargar_basicos(path: Path) -> tuple[list[dict], str, str]:
    """Extrae los precios simples BCCA en euros con unidad reconocida."""
    bruto = path.read_bytes()
    sha = hashlib.sha256(bruto).hexdigest()
    raiz = json.loads(bruto)
    if not isinstance(raiz, dict) or not isinstance(raiz.get("items"), list):
        raise ValueError("Formato CERP inválido")
    precios = []
    for item in raiz["items"]:
        categoria = TIPOS.get(item.get("kind"))
        lista = item.get("prices") or []
        # Se excluyen descomposiciones, tarifas múltiples y unidades no reconocidas.
        if not categoria or item.get("bom") or len(lista) != 1:
            continue
        precio = lista[0]
        alcance = precio.get("scope") or {}
        valor = decimal(precio.get("value"))
        un = unidad(item.get("unit") or "")
        if (precio.get("source") != "bcca" or precio.get("currency") != "EUR"
                or not precio.get("sourceCode") or not valor or not un):
            continue
        if alcance.get("country") != "ES" or not str(alcance.get("region") or ""):
            continue
        texto = item.get("summary") or ""
        precios.append({
            "codigo": precio["sourceCode"],
            "categoria": categoria,
            "unidad": un,
            "descripcion": texto,
            "precio": valor,
            "edicion": str(precio.get("edition") or ""),
            "fecha": str(precio.get("date") or ""),
            "region": str(alcance.get("region")),
            "tokens": set(tokens(texto)),
        })
    if not precios:
        raise ValueError("El banco no contiene precios simples utilizables")
    return precios, sha, str(raiz.get("version") or "")


def cargar_bc3(path: Path) -> tuple[list[dict], str, str]:
    """Adapta una base FIEBDC-3 al mismo formato que el banco abierto CERP.

    Se reutiliza el lector de BC3 ya probado (excluye descomposiciones, precios
    por zona y unidades no reconocidas) para que el cribado sea idéntico.
    """
    import hashlib as _hashlib

    precios_bc3, sha = leer_bc3(path)
    if not precios_bc3:
        raise ValueError("El BC3 no contiene precios simples utilizables")
    precios = []
    for p in precios_bc3:
        texto = f"{p.descripcion} {p.texto}".strip()
        precios.append({
            "codigo": p.codigo,
            "categoria": p.categoria,
            "unidad": p.unidad,
            "descripcion": p.descripcion or p.texto,
            "precio": p.importe,
            "edicion": "",
            "fecha": p.fecha_fuente,
            "region": "EX",
            "tokens": set(tokens(p.descripcion or p.texto)),
        })
    return precios, sha, str(len(precios))


def cribar(recursos: list[dict], precios: list[dict], precio_matriz: dict,
           limite: int = 5) -> list[dict]:
    """Propone candidatos por recurso, ordenados por precisión y cobertura."""
    frecuencia = Counter(t for p in precios for t in p["tokens"])
    total = len(precios)

    def idf(token: str) -> float:
        return math.log((total + 1) / (1 + frecuencia[token])) + 1

    salida = []
    for recurso in recursos:
        tokens_recurso = tokens(recurso["descripcion"])
        if not tokens_recurso:
            continue
        conjunto = set(tokens_recurso)
        nucleo = tokens_recurso[0]
        numeros_recurso = numeros(tokens_recurso)
        matriz = decimal(precio_matriz.get(recurso["codigo_recurso"]))
        candidatos = []
        for precio in precios:
            if precio["categoria"] != recurso["categoria"] or precio["unidad"] != recurso["unidad"]:
                continue
            if nucleo not in precio["tokens"]:
                continue
            comunes = precio["tokens"] & conjunto
            if not comunes:
                continue
            peso_comun = sum(idf(t) for t in comunes)
            precision = peso_comun / sum(idf(t) for t in precio["tokens"])
            cobertura = peso_comun / sum(idf(t) for t in conjunto)
            numeros_ok = numeros_recurso <= precio["tokens"]
            ratio = (precio["precio"] / matriz) if matriz else None
            candidatos.append((precision, cobertura, numeros_ok, precio, ratio))
        candidatos.sort(key=lambda x: (-x[0], -x[1], x[3]["codigo"]))
        if not candidatos:
            salida.append({
                "codigo_recurso": recurso["codigo_recurso"], "categoria": recurso["categoria"],
                "unidad": recurso["unidad"], "usos": recurso["partidas_que_lo_usan"],
                "estado_auditoria": recurso["estado_auditoria"],
                "precio_matriz": str(matriz) if matriz else "",
                "rango": "", "codigo_fuente": "", "descripcion_fuente": "",
                "precio_fuente": "", "edicion_fuente": "", "fecha_precio": "",
                "precision": "", "cobertura": "", "numeros_compatibles": "",
                "ratio": "", "alerta": "sin_candidato",
            })
            continue
        for rango, (precision, cobertura, numeros_ok, precio, ratio) in enumerate(candidatos[:limite], 1):
            alerta = []
            if not numeros_ok:
                alerta.append("numeros_diferentes")
            if ratio is not None and not (Decimal("0.5") <= ratio <= Decimal("2")):
                alerta.append("desviacion_fuerte")
            salida.append({
                "codigo_recurso": recurso["codigo_recurso"], "categoria": recurso["categoria"],
                "unidad": recurso["unidad"], "usos": recurso["partidas_que_lo_usan"],
                "estado_auditoria": recurso["estado_auditoria"],
                "precio_matriz": str(matriz) if matriz else "",
                "rango": rango, "codigo_fuente": precio["codigo"],
                "descripcion_fuente": precio["descripcion"],
                "precio_fuente": str(precio["precio"]),
                "edicion_fuente": precio["edicion"], "fecha_precio": precio["fecha"],
                "precision": f"{precision:.4f}", "cobertura": f"{cobertura:.4f}",
                "numeros_compatibles": "si" if numeros_ok else "no",
                "ratio": f"{ratio:.4f}" if ratio is not None else "",
                "alerta": ";".join(alerta),
            })
    return salida


def leer_registro(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as manejador:
        return list(csv.DictReader(manejador, delimiter=";"))


def leer_matriz(path: Path) -> dict:
    filas = {}
    for fila in leer_registro(path):
        if fila["pais_codigo"] != "ES":
            continue
        if fila["codigo_recurso"] in filas:
            raise ValueError(f"Matriz duplicada: {fila['codigo_recurso']}")
        filas[fila["codigo_recurso"]] = fila["precio_referencia"]
    return filas


def main() -> int:
    analizador = argparse.ArgumentParser(description=__doc__)
    analizador.add_argument("--basicos", type=Path,
                            help="basicos.json del banco abierto CERP (precios BCCA)")
    analizador.add_argument("--bc3", type=Path,
                            help="base FIEBDC-3 (p. ej. Extremadura 2026) en lugar de CERP")
    analizador.add_argument("--banco", default="bcca",
                            help="familia documental del banco cribado (bcca, extremadura…)")
    analizador.add_argument("--edicion", default=EDICION_ESPERADA,
                            help="edición que se anota en la tabla de candidatos")
    analizador.add_argument("--salida", type=Path, default=SALIDA)
    analizador.add_argument("--limite", type=int, default=5)
    argumentar = analizador.parse_args()
    if not 1 <= argumentar.limite <= 50:
        analizador.error("--limite debe estar entre 1 y 50")
    if bool(argumentar.basicos) == bool(argumentar.bc3):
        analizador.error("indique --basicos o --bc3, pero no ambos")
    if argumentar.bc3:
        precios, sha, version = cargar_bc3(argumentar.bc3)
        version = f"BC3 {argumentar.banco} ({version} precios simples)"
    else:
        precios, sha, version = cargar_basicos(argumentar.basicos)
    recursos = leer_registro(AUDITORIA)
    filas = cribar(recursos, precios, leer_matriz(MATRIZ), argumentar.limite)
    for fila in filas:
        fila["banco"] = argumentar.banco
        if argumentar.banco != "bcca":
            fila["edicion_fuente"] = argumentar.edicion
            fila["fecha_precio"] = fila["fecha_precio"] or argumentar.edicion
    argumentar.salida.parent.mkdir(parents=True, exist_ok=True)
    with argumentar.salida.open("w", encoding="utf-8-sig", newline="") as manejador:
        escritor = csv.DictWriter(manejador, fieldnames=list(filas[0]), delimiter=";",
                                  lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(filas)
    con_nucleo = {f["codigo_recurso"] for f in filas if f["codigo_fuente"]}
    fuertes = {f["codigo_recurso"] for f in filas
               if f["codigo_fuente"] and Decimal(f["precision"]) >= Decimal("0.75")
               and f["numeros_compatibles"] == "si"}
    print(f"CERP {version}; sha256={sha}; precios simples utilizables={len(precios)}")
    print(f"{len(recursos)} recursos; {len(con_nucleo)} con candidato de núcleo común; "
          f"{len(fuertes)} con precisión >= 0,75 y números compatibles")
    print(f"Escrito {argumentar.salida}; candidatos sin adjudicar, no se ha modificado ningún precio")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
