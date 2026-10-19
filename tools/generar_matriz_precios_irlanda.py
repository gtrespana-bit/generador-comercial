#!/usr/bin/env python3
"""Genera la matriz de precios de recursos para Irlanda (EUR).

Replica el contrato de ``generar_matriz_precios_reino_unido.py``:

* Los precios base de ``basedatos_partidas/datos/recursos.json`` están en USD y
  tienen ámbito Venezuela, así que ninguna conversión de divisa produce un
  precio irlandés. La matriz se construye desde precios irlandeses reales.
* Las anclas investigadas se publican tal cual, con rango, fuente y fecha; el
  fichero de investigación es ``docs/INVESTIGACION_PRECIOS_IRLANDA.md``.
* El resto de recursos se cubre con un **factor de mercado por familia**,
  calculado como la mediana de la relación entre el precio irlandés investigado
  y el precio base de cada ancla de esa familia. Si una familia no tiene anclas
  se cae al factor de la categoría.
* La mano de obra no usa factores: los 17 oficios salen del modelo de coste
  empresa de ``coste_empresa_irlanda.py``, que parte del Sectoral Employment
  Order del sector de la construcción vigente desde el 1 de agosto de 2026.

Los precios de proveedor irlandés se publican **sin IVA**. En Irlanda el tipo
general es el 23 % y el reducido del 13,5 % aplica a los servicios de
construcción y reforma de vivienda, de modo que mezclar precios con IVA dentro
de un presupuesto sería un error de base.

Uso:
    python3 tools/generar_matriz_precios_irlanda.py
"""
from __future__ import annotations

import csv
import json
import statistics
from dataclasses import dataclass, replace
from pathlib import Path

from coste_empresa_irlanda import (
    HORAS_FACTURABLES,
    OFICIOS,
    SEO,
    coste_empresa,
)

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "basedatos_partidas/datos/recursos.json"
OUT = ROOT / "basedatos_partidas/salida/precios_recursos_irlanda.csv"
FECHA = "2026-10-18"

R_IE = "docs/INVESTIGACION_PRECIOS_IRLANDA.md"
R_GB = "docs/INVESTIGACION_PRECIOS_REINO_UNIDO.md"
METODOLOGIA = "docs/METODOLOGIA_PRECIOS_REFERENCIA_IRLANDA.md"
# EUR/USD 1,1253 (BCE, tipo de referencia del 16/10/2026; Yahoo 1,1242 el
# 17/10) -> 1 USD = 0,8886 EUR. Solo normaliza el precio base antes de aplicar
# el factor de mercado; el resultado queda congelado en EUR y con fecha.
TASAS_CORTE = {"IE": 0.8886}
# EUR/GBP implícito en los dos tipos de referencia (1,3330 USD/GBP y 1,1253
# USD/EUR) para trasladar al mercado irlandés las anclas británicas cuando el
# factor de familia no es representativo.
EUR_POR_GBP = 1.3330 / 1.1253
MATRIZ_GB = ROOT / "basedatos_partidas/salida/precios_recursos_reino_unido.csv"
# Margen en el que se acepta el factor de familia frente al ancla británica
# equivalente. Fuera de él, el factor está midiendo otra cosa (una cámara CCTV
# que hereda el factor del cemento) y se adopta el ancla británica convertida.
BANDA_CONTRASTE_GB = (0.5, 2.0)

OBS_REFERENCIA = (
    "Precio de mercado irlandés observado (sin IVA, sin porte salvo indicación); "
    "puede variar por proveedor, marca, volumen y condado."
)
OBS_DERIVADO = (
    "Precio referencial derivado del factor de mercado de su familia, calculado "
    "sobre la canasta irlandesa investigada; no es una cotización de tienda."
)


@dataclass(frozen=True)
class Referencia:
    precio: float
    minimo: float
    maximo: float
    fuente: str
    confianza: str = "referencia"
    observaciones: str = OBS_REFERENCIA
    incluye_iva: str = "no"
    incluye_transporte: str = "no_confirmado"


def ref(precio, minimo, maximo, fuente=R_IE, **kwargs) -> Referencia:
    precio, minimo, maximo = map(float, (precio, minimo, maximo))
    if minimo <= 0 or maximo < minimo or not minimo <= precio <= maximo:
        raise ValueError(f"Rango inválido: {minimo} <= {precio} <= {maximo}")
    return Referencia(precio, minimo, maximo, fuente, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Mano de obra — modelo de coste empresa irlandés
# ─────────────────────────────────────────────────────────────────────────────

def referencias_mano_obra() -> dict[str, dict[str, Referencia]]:
    salida: dict[str, dict[str, Referencia]] = {}
    for codigo, (oficio, clasificacion) in OFICIOS.items():
        tarifa = SEO[clasificacion]
        coste = coste_empresa(tarifa)["coste_hora_facturable"]
        # El rango recoge la dispersión real del país: del oeste y los condados
        # con menos obra (−8 %) al área de Dublín (+20 %). El SEO es el suelo,
        # no la tarifa de mercado.
        salida[codigo] = {
            "IE": ref(
                coste,
                coste * 0.92,
                coste * 1.20,
                R_IE,
                incluye_iva="no_aplica",
                incluye_transporte="no_aplica",
                observaciones=(
                    f"Coste empresa por hora facturable. {oficio}. Tarifa SEO de la "
                    f"construcción vigente desde el 01/08/2026 ({clasificacion.replace('_', ' ')}: "
                    f"{tarifa:.2f} €/h) + PRSI empresa 11,40 % + pensión SEO 32,89 €/semana "
                    f"+ vacaciones (29 días) y bajas, todo dividido por "
                    f"{HORAS_FACTURABLES:,.0f} h facturables/año. No es tarifa de "
                    f"autónomo: el catálogo ya aplica un 35 % de margen sobre el coste "
                    f"directo."
                ),
            )
        }
    return salida


# ─────────────────────────────────────────────────────────────────────────────
# 2. Maquinaria — tarifas de alquiler irlandesas
#
#    El alquiler irlandés se cotiza por día de 8 horas. Se adopta el día y se
#    publica el equivalente horario. Excluye IVA, combustible y operador salvo
#    que el recurso lo indique.
# ─────────────────────────────────────────────────────────────────────────────

def _alquiler(dia, minimo, maximo, nota="") -> Referencia:
    return ref(
        dia / 8.0, minimo / 8.0, maximo / 8.0, R_IE,
        observaciones=(
            f"Alquiler irlandés {minimo:.0f}-{maximo:.0f} €/día (jornada de 8 h), "
            f"sin IVA ni combustible. {nota}".strip()
        ),
    )


MAQUINARIA: dict[str, Referencia] = {
    # Movimiento de tierras
    "MQ-RETRO": _alquiler(210, 160, 300, "Miniexcavadora de 3 t con martillo hidráulico "
                                          "(150 €/día la máquina + 60 €/día el martillo)."),
    "MQ-COMPACT-SALTO": _alquiler(55, 40, 70, "Pisón de zanja tipo canguro."),
    "MQ-PLANCHA-COMP": _alquiler(45, 36, 60, "Plancha compactadora vibratoria."),
    "MQ-MART-NEUM": _alquiler(95, 72, 130, "Martillo neumático con compresor."),
    # Hormigón
    "MQ-MEZCL": _alquiler(35, 28, 48, "Hormigonera eléctrica de un saco."),
    # Acceso y elevación
    "MQ-ANDAMIO": _alquiler(45, 36, 65, "Torre móvil de aluminio de 2,2 m (tarifa diaria)."),
    # Limpieza
    "MQ-ASPIR": _alquiler(45, 34, 60, "Aspirador industrial clase M."),
    # Medición
    "MQ-NIVEL-LASER": _alquiler(50, 40, 72, "Nivel láser rotativo autonivelante."),
    # Transporte
    "MQ-VOLQ": _alquiler(480, 380, 620, "Camión volqueta de 6 m³ **con chofer**."),
    # Unidad distinta: el baño portátil se alquila por mes.
    "MQ-BANO-PORT": ref(
        175, 140, 230, R_IE,
        observaciones=(
            "Alquiler mensual de baño portátil de obra con mantenimiento "
            "(recurso medido en unidades, no en horas). Sin IVA."
        ),
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# 3. Materiales — precios de proveedor irlandés (sin IVA)
# ─────────────────────────────────────────────────────────────────────────────

MATERIALES: dict[str, Referencia] = {
    # ── Hormigón y áridos ────────────────────────────────────────────────────
    "MT-CONC-180": ref(100, 92, 115, R_IE,
                       observaciones="Hormigón premezclado C16/20 puesto en obra; el precio "
                                     "depende de la planta y del volumen mínimo (3-4 m³)."),
    "MT-CONC-210": ref(112, 100, 126, R_IE,
                       observaciones="Hormigón premezclado C20/25 (≈210 kg/cm²) puesto en obra."),
    "MT-CONC-250": ref(126, 115, 140, R_IE,
                       observaciones="Hormigón premezclado C25/30: 126,00 €/m³ ex IVA en "
                                     "Hanly Quarries."),
    "MT-CONC-300": ref(132, 122, 150, R_IE,
                       observaciones="Hormigón premezclado C28/35-C30/37: 132,00 €/m³ ex IVA "
                                     "en Hanly Quarries."),
    "MT-CEMENTO": ref(0.30, 0.26, 0.34, R_IE,
                      observaciones="Cemento Irish Cement en saco de 25 kg: 9,25-10,16 € con "
                                    "IVA, es decir 7,52-8,26 € ex IVA (0,30-0,33 €/kg)."),
    "MT-ARENA": ref(45, 32, 65, R_IE,
                    observaciones="Arena lavada: 28 €/m³ suelta en cantera y 50,81 € ex IVA el "
                                  "big bag de ~1 t, que sale mucho más caro por m³."),
    "MT-GRAVILLA": ref(48, 38, 62, R_IE,
                       observaciones="Árido grueso 10-20 mm por m³ suelto."),
    "MT-PIEDRA-PIC": ref(42, 32, 55, R_IE,
                         observaciones="Árido triturado / clause 804 por m³ suelto."),
    "MT-MAT-PRESTAMO": ref(36, 28, 48, R_IE,
                           observaciones="Material granular seleccionado (clause 804 / MOT "
                                         "Type 1), por m³."),
    "MT-AGUA-OBRA": ref(2.40, 1.90, 3.00, R_IE,
                        observaciones="Agua de obra; tarifa industrial por m³."),
    # ── Fábrica y bloques ────────────────────────────────────────────────────
    # El bloque irlandés es de 440×215 mm, igual que el británico, pero el
    # formato de 100 mm se vende suelto y sin palé en la mayoría de proveedores.
    "MT-BLQ-10": ref(1.45, 1.25, 1.85, R_IE,
                     observaciones="Bloque sólido de hormigón 440×215×100 mm 7,5 N: "
                                   "1,37-1,50 € ex IVA la unidad."),
    "MT-BLQ-12": ref(2.05, 1.80, 2.60, R_IE,
                     observaciones="Bloque de hormigón de 140 mm (bloque de 6\")."),
    "MT-BLQ-15": ref(2.60, 2.30, 3.20, R_IE,
                     observaciones="Bloque hueco de 215 mm (bloque de 9\"): 2,60 € ex IVA la "
                                   "unidad en TJ O'Mahony."),
    # ── Yeso laminado, placa y trasdosado ────────────────────────────────────
    "MT-PYL-PLACA125": ref(6.40, 5.40, 8.00, R_IE,
                           observaciones="Placa Gyproc Wallboard 2438×1200×12,5 mm: 18,84 € "
                                         "ex IVA la hoja de 2,93 m²."),
    "MT-PYL-PLACA": ref(7.60, 6.40, 9.50, R_IE,
                        observaciones="Placa de yeso laminado de 15 mm, por m² (hoja de 8×4)."),
    "MT-PYL-PLACA-IG": ref(8.45, 7.20, 10.60, R_IE,
                           observaciones="Placa Gyproc Fireline de 12,5 mm: 24,35 € la hoja "
                                         "en tarifa profesional, 8,31 €/m²."),
    "MT-PYL-LANA": ref(7.20, 5.60, 9.50, R_IE,
                       observaciones="Lana mineral: rollo Knauf Earthwool de 200 mm para "
                                     "5,50 m² a 54,99 € con IVA (≈7,20 €/m² ex IVA)."),
    "MT-YESO-REP": ref(0.65, 0.55, 0.85, R_IE,
                       observaciones="Yeso de enlucido Gyproc Skimcoat de 25 kg: 16,22-17,44 € "
                                     "ex IVA el saco."),
    "MT-PASTA-YESO": ref(0.68, 0.55, 0.90, R_IE,
                         observaciones="Pasta de agarre de base yeso, por kg."),
    "MT-PYL-PASTA": ref(0.75, 0.60, 1.00, R_IE,
                        observaciones="Compuesto de juntas Gyproc de 25 kg a 17,03 € ex IVA, "
                                      "por kg."),
    # ── Cerámica y adhesivos ─────────────────────────────────────────────────
    "MT-ADH-C2TE": ref(1.33, 1.15, 1.60, R_IE,
                       observaciones="Adhesivo cementoso flexible C2 TE de 20 kg: 26,56 € ex "
                                     "IVA (Arc Proflex)."),
    "MT-ADH-C1": ref(0.83, 0.70, 1.00, R_IE,
                     observaciones="Adhesivo cementoso estándar de 20 kg: 16,50 € ex IVA "
                                   "(Arc Rapid Set)."),
    "MT-JUN-CG2": ref(2.59, 2.20, 3.20, R_IE,
                      observaciones="Mortero de juntas CG2 de 5 kg: 12,97 € ex IVA (Technik "
                                    "TGS)."),
    "MT-GROUT": ref(2.30, 1.90, 2.90, R_IE,
                    observaciones="Lechada de juntas por kg, formato profesional de 10 kg."),
    # ── Pintura ──────────────────────────────────────────────────────────────
    "MT-PIN-CAUCHO": ref(1.90, 1.60, 2.40, R_IE,
                         observaciones="Pintura plástica mate 10 L: 20,95 € con IVA (Leyland "
                                       "Retail), ≈1,70 €/L ex IVA."),
    "MT-PIN-FONDO": ref(2.30, 1.90, 3.00, R_IE,
                        observaciones="Imprimación acrílica de fondo, por litro."),
    # ── Madera ───────────────────────────────────────────────────────────────
    "MT-MADERA-LISTON": ref(2.60, 2.10, 3.40, R_IE,
                            observaciones="Listón de madera de obra de 100×44 mm: 12,47 € ex "
                                          "IVA la pieza de 4,8 m (blanco de pino sin cepillar)."),
    # ── Electricidad ─────────────────────────────────────────────────────────
    "MT-ELE-CABLE": ref(1.55, 1.30, 1.90, R_IE,
                        observaciones="Cable bipolar con tierra de 2,5 mm², 100 m: 152,80 € "
                                      "ex IVA la bobina."),
    # ── Residuos ─────────────────────────────────────────────────────────────
    # La tasa de vertedero es de 85 €/t y la de valorización de 10 €/t desde
    # marzo de 2026. Un contenedor de 6 yardas (~4,6 m³) cuesta 349 € con IVA.
    "MT-CANON": ref(75, 55, 105, R_IE,
                    observaciones="Retirada y vertido de escombro mezclado por m³: contenedor "
                                  "de 6 yardas a 349 € con IVA, más tasa de vertedero de "
                                  "85 €/t y de valorización de 10 €/t."),
    "MT-CANON-TIERRA": ref(45, 32, 62, R_IE,
                           observaciones="Retirada de tierra y material de excavación, por m³, "
                                         "con tasa de valorización."),
}


# ─────────────────────────────────────────────────────────────────────────────
# 4. Ensamblado
# ─────────────────────────────────────────────────────────────────────────────

def _familia(codigo: str) -> str:
    """Familia de mercado: el prefijo del código, con un mínimo de dos tramos."""
    partes = codigo.split("-")
    if len(partes) < 2:
        return codigo
    return "-".join(partes[:2])


def _construir_referencias() -> dict[str, dict[str, Referencia]]:
    referencias: dict[str, dict[str, Referencia]] = {}
    referencias.update(referencias_mano_obra())
    for tabla in (MAQUINARIA, MATERIALES):
        for codigo, dato in tabla.items():
            if codigo in referencias:
                raise ValueError(f"{codigo} definido dos veces")
            referencias[codigo] = {"IE": dato}
    return referencias


def iter_recursos(data):
    for categoria in ("mano_obra", "materiales", "maquinaria"):
        for codigo, item in (data.get(categoria) or {}).items():
            if not isinstance(item, dict) or "descripcion" not in item:
                continue
            # Los compuestos se abren en sus componentes y no existen como
            # recurso físico en la base de datos de la aplicación.
            if item.get("composicion"):
                continue
            yield codigo, categoria, item


def _anclas_britanicas() -> dict[str, float]:
    """Anclas británicas investigadas, en EUR, para contrastar los derivados.

    La matriz británica es otro artefacto generado del repositorio: si no está,
    el contraste se omite en lugar de romper la construcción.
    """
    if not MATRIZ_GB.exists():
        return {}
    with MATRIZ_GB.open(encoding="utf-8-sig", newline="") as fh:
        return {
            fila["codigo_recurso"]: float(fila["precio_referencia"]) * EUR_POR_GBP
            for fila in csv.DictReader(fh, delimiter=";")
            if fila.get("confianza") == "referencia" and fila.get("precio_referencia")
        }


def derivar_referencias(data, referencias):
    """Cubre los recursos sin ancla con un factor por familia.

    El factor es la mediana de (precio irlandés investigado / precio base
    convertido) de las anclas de esa familia. Si la familia no tiene anclas se
    usa la mediana de la categoría.
    """
    fichas = {c: (cat, item) for c, cat, item in iter_recursos(data)}

    por_familia: dict[tuple[str, str], list[float]] = {}
    por_categoria: dict[str, list[float]] = {}
    for codigo, por_pais in referencias.items():
        ficha = fichas.get(codigo)
        dato = por_pais.get("IE")
        if ficha is None or dato is None or dato.confianza != "referencia":
            continue
        categoria = ficha[0]
        if categoria == "mano_obra":
            continue
        base_local = float(ficha[1]["precio"]) * TASAS_CORTE["IE"]
        if base_local <= 0:
            continue
        razon = dato.precio / base_local
        por_categoria.setdefault(categoria, []).append(razon)
        por_familia.setdefault((categoria, _familia(codigo)), []).append(razon)

    factores_familia = {k: statistics.median(v) for k, v in por_familia.items()}
    factores_categoria = {k: statistics.median(v) for k, v in por_categoria.items()}
    anclas_gb = _anclas_britanicas()

    derivados = 0
    trasladados = 0
    for codigo, categoria, item in iter_recursos(data):
        if categoria == "mano_obra":
            continue
        if referencias.get(codigo, {}).get("IE") is not None:
            continue
        base_local = float(item["precio"]) * TASAS_CORTE["IE"]
        factor = factores_familia.get((categoria, _familia(codigo)))
        origen = f"familia {_familia(codigo)}"
        if factor is None:
            factor = factores_categoria[categoria]
            origen = f"categoría {categoria}"
        precio = base_local * factor
        referencia_gb = anclas_gb.get(codigo)
        bajo, alto = BANDA_CONTRASTE_GB
        if referencia_gb and not bajo <= precio / referencia_gb <= alto:
            # El factor de la familia no representa a este recurso: se adopta el
            # ancla británica convertida y se dice de dónde viene.
            precio = referencia_gb
            referencias.setdefault(codigo, {})["IE"] = ref(
                precio, precio * 0.85, precio * 1.20, R_GB,
                confianza="derivado",
                observaciones=(
                    "Sin precio irlandés observado todavía: se traslada el ancla "
                    f"británica investigada convertida a {EUR_POR_GBP:.4f} EUR/GBP, "
                    "porque el factor de la familia se separaba más del doble de ese "
                    "valor (regla en docs/METODOLOGIA_PRECIOS_REFERENCIA_IRLANDA.md). "
                    "Referencia provisional, no es una cotización de tienda."
                ),
            )
            trasladados += 1
            derivados += 1
            continue
        referencias.setdefault(codigo, {})["IE"] = replace(
            ref(precio, precio * 0.80, precio * 1.25, METODOLOGIA,
                confianza="derivado", observaciones=OBS_DERIVADO),
            observaciones=f"{OBS_DERIVADO} Factor {factor:.3f} de la {origen}.",
        )
        derivados += 1
    return factores_familia, factores_categoria, derivados, trasladados


def _numero(valor: float) -> str:
    return f"{valor:.6f}".rstrip("0").rstrip(".")


def main() -> int:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    referencias = _construir_referencias()
    (factores_familia, factores_categoria,
     derivados, trasladados) = derivar_referencias(data, referencias)

    filas = []
    for codigo, categoria, item in iter_recursos(data):
        dato = referencias.get(codigo, {}).get("IE")
        if dato is None:
            raise SystemExit(f"Sin referencia para {codigo}")
        filas.append({
            "codigo_recurso": codigo,
            "descripcion": item["descripcion"],
            "categoria": categoria,
            "unidad_fuente": item["unidad"],
            "pais_codigo": "IE",
            "moneda": "EUR",
            "precio_referencia": _numero(dato.precio),
            "precio_min": _numero(dato.minimo),
            "precio_max": _numero(dato.maximo),
            "fuente": dato.fuente,
            "fecha_consulta": FECHA,
            "confianza": dato.confianza,
            "incluye_iva": dato.incluye_iva,
            "incluye_transporte": dato.incluye_transporte,
            "origen": "nacional",
            "observaciones": dato.observaciones,
        })

    campos = list(filas[0].keys())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        # Saltos LF, como las matrices de España y LatAm: el CSV se versiona y
        # CRLF mete un carácter de más en cada línea del diff.
        w = csv.DictWriter(fh, fieldnames=campos, delimiter=";", lineterminator="\n")
        w.writeheader()
        w.writerows(filas)

    total = len(filas)
    investigados = sum(1 for f in filas if f["confianza"] == "referencia")
    print(f"Matriz irlandesa escrita en {OUT.relative_to(ROOT)}")
    print(f"  {total} recursos · {investigados} investigados "
          f"({investigados / total:.0%}) · {derivados} derivados "
          f"({trasladados} trasladados del ancla británica)")
    print(f"  tasa de corte: 1 USD = {TASAS_CORTE['IE']:.4f} EUR (EUR/USD 1,1253, 16/10/2026)")
    print()
    print("  Factores por categoría (mediana de precio irlandés / base convertida):")
    for categoria, factor in sorted(factores_categoria.items()):
        print(f"    {categoria:12s} {factor:8.3f}")
    print()
    print(f"  Familias con ancla propia: {len(factores_familia)}")
    for (categoria, familia), factor in sorted(factores_familia.items()):
        n = len([1 for c, d in referencias.items()
                 if d.get("IE") and d["IE"].confianza == "referencia"
                 and _familia(c) == familia and c in
                 {x for x, cat, _ in iter_recursos(data) if cat == categoria}])
        print(f"    {familia:22s} {factor:8.3f}  ({n} anclas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
