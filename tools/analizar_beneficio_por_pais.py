#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Beneficio por partida actualmente vigente, país a país.

Recalcula el APU de las 3.006 partidas del catálogo con los precios de
mercado nacionales (mismos datos que usa la app en
`app/services/precios_partidas.py`) y aplica el mismo criterio de la app:
el margen de la partida base (Venezuela, USD) se conserva y se aplica
sobre el coste directo de mercado del país.

    python3 tools/analizar_beneficio_por_pais.py
"""
from __future__ import annotations

import csv
import json
import statistics
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATOS = BASE / "basedatos_partidas" / "datos"
SALIDA = BASE / "basedatos_partidas" / "salida"
TASA = BASE / "app" / "services" / "tasa.py"

# Tasas verificadas en app/services/tasa.py (2026-08-25): 1 USD -> moneda
TASAS = {
    "USD": 1.0, "PAB": 1.0, "VES": 773.31, "COP": 3128.65, "MXN": 17.06,
    "PEN": 3.37, "EUR": 0.8564, "CLP": 925.90, "ARS": 1497.38,
    "DOP": 58.33, "UYU": 40.21, "PYG": 5946.10, "BOB": 11.55,
    "CRC": 449.39, "GTQ": 7.62, "HNL": 26.82, "NIO": 36.70,
}
NOMBRES = {
    "VE": "Venezuela", "CO": "Colombia", "MX": "México", "PE": "Perú",
    "EC": "Ecuador", "PA": "Panamá", "SV": "El Salvador", "CL": "Chile",
    "AR": "Argentina", "DO": "Rep. Dominicana", "UY": "Uruguay",
    "PY": "Paraguay", "BO": "Bolivia", "CR": "Costa Rica",
    "GT": "Guatemala", "HN": "Honduras", "NI": "Nicaragua", "ES": "España",
}


def r2(x: float) -> float:
    return round(x + 1e-9, 2)


def cargar_recursos() -> dict:
    bruto = json.loads((DATOS / "recursos.json").read_text(encoding="utf-8"))
    salida: dict[str, dict] = {}
    for grupo in ("materiales", "maquinaria", "mano_obra"):
        for codigo, ficha in (bruto.get(grupo) or {}).items():
            salida[codigo] = {**ficha, "grupo": grupo}
    return salida


def cargar_paises() -> dict[str, dict]:
    """{pais: {codigo_recurso: (precio_local, moneda)}} a partir de la matriz
    nacional de referencia (latam_completa + espana)."""
    paises: dict[str, dict] = {}
    for ruta in (SALIDA / "precios_recursos_latam_completa.csv",
                 SALIDA / "precios_recursos_espana.csv"):
        with ruta.open(encoding="utf-8-sig", newline="") as fh:
            for fila in csv.DictReader(fh, delimiter=";"):
                try:
                    precio = float(fila["precio_referencia"])
                except (TypeError, ValueError, KeyError):
                    continue
                paises.setdefault(fila["pais_codigo"], {})[
                    fila["codigo_recurso"]] = (precio, fila["moneda"])
    return paises


def precio_efectivo(codigo: str, fichas: dict, precios_pais: dict,
                    visto: frozenset) -> float | None:
    """Precio del recurso en la moneda del país, resolviendo compuestos."""
    ficha = fichas.get(codigo)
    if ficha is None:
        return None
    comp = ficha.get("composicion")
    if comp:
        total = 0.0
        for pieza in comp:
            ref = pieza["ref"]
            if ref in visto:  # ciclo defensivo
                continue
            sub = precio_efectivo(ref, fichas, precios_pais,
                                  visto | {ref})
            if sub is None:
                return None
            total += float(pieza["cantidad"]) * sub
        return total
    if codigo in precios_pais:
        return float(precios_pais[codigo][0])
    # recurso sin referencia nacional: se convierte el base USD con la tasa
    try:
        return float(ficha["precio"])
    except (KeyError, TypeError, ValueError):
        return None


def coste_partida(partida: dict, fichas: dict, precios_pais: dict,
                  tasa_usd: float) -> float:
    """Coste directo con la cascada CYPE de la app:
    importe = round2(rendimiento × precio) por recurso, subtotal por grupo,
    complementarios = % × suma de subtotales, total = subtotales + compl.
    """
    subtotal_grupo: dict[str, float] = {}
    for linea in partida.get("recursos", []):
        ficha = fichas.get(linea["ref"])
        if ficha is None:
            continue
        precio = precio_efectivo(linea["ref"], fichas, precios_pais, frozenset())
        if precio is None:
            continue
        importe = r2(float(linea["rendimiento"]) * precio)
        subtotal_grupo[ficha["grupo"]] = r2(subtotal_grupo.get(ficha["grupo"], 0.0) + importe)
    base = 0.0
    for suma in subtotal_grupo.values():
        base = r2(base + suma)
    pct = float(partida.get("complementarios_pct", 0) or 0)
    complementarios = r2(base * pct / 100) if pct else 0.0
    return base + complementarios


def main() -> int:
    fichas = cargar_recursos()
    paises = cargar_paises()

    # Catálogo base: precios de venta y desglose de costes guardados
    catalogo: dict[str, dict] = {}
    with (DATOS / "partidas.csv").open(encoding="utf-8", newline="") as fh:
        for fila in csv.DictReader(fh, delimiter=";"):
            catalogo[fila["codigo"]] = fila

    # Descompuestos con sus recursos y rendimientos
    descompuestos: dict[str, dict] = {}
    for ruta in sorted((DATOS / "descompuestos").glob("*.json")):
        p = json.loads(ruta.read_text(encoding="utf-8"))
        descompuestos[p["codigo"]] = p

    print(f"Partidas: {len(descompuestos)} · Catálogo: {len(catalogo)} · "
          f"Precios nacionales en {len(paises)} países · Recursos base: {len(fichas)}\n")

    # ---- Beneficio base por partida (Venezuela, USD) --------------------- #
    filas_resultado: list[dict] = []
    for codigo, partida in descompuestos.items():
        cat = catalogo.get(codigo)
        if not cat:
            continue
        precio = float(cat["precio"])
        coste_base = (
            float(cat.get("coste_materiales") or 0)
            + float(cat.get("coste_mano_obra") or 0)
            + float(cat.get("coste_complementarios") or 0)
            + float(cat.get("coste_otros") or 0)
        )
        # Margen conservado por la app (precios_partidas.py)
        margen = (precio - coste_base) / coste_base if coste_base > 0 else 0.30
        filas_resultado.append({
            "codigo": codigo, "titulo": cat["partida"], "unidad": cat["unidad"],
            "precio_base": precio, "coste_base": coste_base,
            "beneficio_base": precio - coste_base, "margen": margen,
        })

    n = len(filas_resultado)
    b_base = [f["beneficio_base"] for f in filas_resultado]
    m_base = [f["margen"] for f in filas_resultado]

    print("=== BASE DEL CATÁLOGO (Venezuela, USD) ===")
    print(f"Partidas analizadas:            {n}")
    print(f"Beneficio medio por partida:    {statistics.mean(b_base):8.2f} USD")
    print(f"Beneficio mediana por partida:  {statistics.median(b_base):8.2f} USD")
    print(f"Beneficio min / max:            {min(b_base):8.2f} / {max(b_base):.2f} USD")
    print(f"Margen medio sobre coste:       {statistics.mean(m_base)*100:8.2f} %")
    print(f"Margen mediana sobre coste:     {statistics.median(m_base)*100:8.2f} %")
    dist = {}
    for m in m_base:
        clave = f"{round(m*100)}"
        dist[clave] = dist.get(clave, 0) + 1
    print("Distribución de margen: " +
          ", ".join(f"{k}%: {v}" for k, v in sorted(dist.items(), key=lambda kv: int(kv[0]))))
    print(f"Beneficio total del catálogo:   {sum(b_base):12,.0f} USD\n")

    # ---- Beneficio por partida en cada país ------------------------------ #
    print("=== BENEFICIO POR PARTIDA POR PAÍS (margen base conservado) ===")
    print(f"{'País':<16}{'Moneda':<7}{'Beneficio medio (local)':>26}{'Mediana (local)':>20}{'Medio (USD)':>12}{'Total catálogo (USD)':>20}")
    print("-" * 104)

    base_usd = {
        codigo: (float(ficha.get("precio", 0) or 0), "USD")
        for codigo, ficha in fichas.items()
    }
    resultados: list[dict] = []
    orden = ["VE", "CO", "MX", "PE", "EC", "PA", "SV", "CL", "AR", "DO",
             "UY", "PY", "BO", "CR", "GT", "HN", "NI", "ES"]
    for pais in orden:
        if pais == "VE":
            precios = base_usd
            moneda = "USD"
        else:
            if pais not in paises:
                continue
            precios = paises[pais]
            moneda = next(iter(precios.values()))[1]
        tasa_usd = TASAS.get(moneda, 1.0)
        beneficios_local = []
        for f in filas_resultado:
            partida = descompuestos[f["codigo"]]
            coste = coste_partida(partida, fichas, precios, tasa_usd)
            beneficios_local.append(coste * f["margen"])
        medio = statistics.mean(beneficios_local)
        mediana = statistics.median(beneficios_local)
        total = sum(beneficios_local)
        resultados.append({
            "pais": pais, "nombre": NOMBRES.get(pais, pais), "moneda": moneda,
            "medio": medio, "mediana": mediana, "usd": medio / tasa_usd,
            "total_usd": total / tasa_usd, "margen_medio":
            statistics.mean(f["margen"] for f in filas_resultado) * 100,
        })
        print(f"{NOMBRES.get(pais, pais):<16}{moneda:<7}"
              f"{medio:22,.2f} {moneda:<3}{mediana:16,.2f}"
              f"{medio/tasa_usd:12,.2f}{total/tasa_usd:20,.0f}")

    print("-" * 90)
    print("\nNota: el margen % es idéntico en todos los países (se conserva el de la")
    print("partida base VE); solo cambia el beneficio absoluto según el coste local.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
