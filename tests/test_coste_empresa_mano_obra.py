"""Regresión: la mano de obra nacional Latam es coste-empresa, no jornal de mercado.

Revisión ronda 7 (2026-09-08): cada fila MO-* se calcula como
    jornal bruto de mercado × factor (aportes patronales + prestaciones) ÷ 8 h.
El catálogo aplica el margen encima (tarifas = coste), así que la referencia
debe estar por encima del jornal publicado y por debajo de una tarifa de
venta con beneficio.
"""
from __future__ import annotations

import csv
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
MATRIZ = RAIZ / "basedatos_partidas" / "salida" / "precios_recursos_latam.csv"
R7 = "docs/INVESTIGACION_PRECIOS_RONDA_7_COSTE_EMPRESA_MANO_OBRA.md"

# Mismos factores que tools/generar_matriz_precios_latam.py (no importar el
# script: cuelga de rutas relativas).
FACTORES = {
    "CO": 1.45, "PE": 1.45, "MX": 1.46, "EC": 1.35, "CL": 1.25, "AR": 1.50,
    "DO": 1.30, "UY": 1.32, "PY": 1.30, "BO": 1.36, "CR": 1.41, "GT": 1.43,
    "HN": 1.25, "NI": 1.40, "PA": 1.33, "SV": 1.26,
}
TASAS = {
    "CO": 3128.65, "PE": 3.37, "MX": 17.06, "EC": 1.0, "PA": 1.0, "SV": 1.0,
    "CL": 925.90, "AR": 1497.38, "DO": 58.33, "UY": 40.21, "PY": 5946.10,
    "BO": 11.55, "CR": 449.39, "GT": 7.62, "HN": 26.82, "NI": 36.70,
}
JORNAL_OF1 = {
    "CO": 110_000, "PE": 69.75, "MX": 750, "EC": 21.67, "CL": 55_000,
    "AR": 45_624, "DO": 2_000, "UY": 2_412.65, "PY": 125_875, "BO": 270,
    "CR": 13_991.86, "GT": 220, "HN": 800, "NI": 532.6, "PA": 45, "SV": 28,
}
JORNAL_AYU = {
    "CO": 72_500, "PE": 62.80, "MX": 400, "EC": 20.315, "CL": 35_000,
    "AR": 38_808, "DO": 900, "UY": 1_554.29, "PY": 107_627, "BO": 140,
    "CR": 13_523.69, "GT": 130, "HN": 450, "NI": 350, "PA": 35, "SV": 16,
}


def _filas() -> list[dict]:
    with MATRIZ.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh, delimiter=";"))


def _por_recurso(filas: list[dict]) -> dict[str, dict[str, dict]]:
    por: dict[str, dict[str, dict]] = {}
    for fila in filas:
        por.setdefault(fila["codigo_recurso"], {})[fila["pais_codigo"]] = fila
    return por


def test_mano_obra_latam_es_coste_empresa_y_no_jornal() -> None:
    filas = _filas()
    por = _por_recurso(filas)
    for pais in FACTORES:
        factor = FACTORES[pais]
        oficial = por["MO-OF1"][pais]
        ayudante = por["MO-AYU"][pais]
        # Referencia trazable a la ronda 7 y fechada.
        assert oficial["fuente"] == R7
        assert oficial["fecha_consulta"] == "2026-09-08"
        assert "coste-empresa" in oficial["observaciones"].lower()
        assert f"{factor:.2f}" in oficial["observaciones"]
        # Rango válido y jerarquía oficial > ayudante.
        precio = float(oficial["precio_referencia"])
        mn, mx = float(oficial["precio_min"]), float(oficial["precio_max"])
        assert 0 < mn <= precio <= mx
        assert precio > float(ayudante["precio_referencia"])


def test_factores_aplicados_exactos() -> None:
    por = _por_recurso(_filas())
    for pais, factor in FACTORES.items():
        esperado_of1 = round(JORNAL_OF1[pais] * factor / 8, 6)
        esperado_ayu = round(JORNAL_AYU[pais] * factor / 8, 6)
        assert abs(float(por["MO-OF1"][pais]["precio_referencia"]) - esperado_of1) < 1e-4, pais
        assert abs(float(por["MO-AYU"][pais]["precio_referencia"]) - esperado_ayu) < 1e-4, pais


def test_costes_por_hora_en_usd_son_plausibles() -> None:
    """Ni cortos ni pasados: el coste-empresa del oficial queda en ~2,5–10 USD/h."""
    por = _por_recurso(_filas())
    for pais, tasa in TASAS.items():
        oficial_usd = float(por["MO-OF1"][pais]["precio_referencia"]) / tasa
        ayudante_usd = float(por["MO-AYU"][pais]["precio_referencia"]) / tasa
        assert 1.5 <= oficial_usd <= 15, f"{pais}: oficial {oficial_usd:.2f} USD/h"
        assert 0.8 <= ayudante_usd <= 10, f"{pais}: ayudante {ayudante_usd:.2f} USD/h"


def test_especialidades_heredan_el_coste_empresa() -> None:
    por = _por_recurso(_filas())
    # Sin jornal local, la especialidad se deriva del oficial general del país.
    carpintero_co = float(por["MO-OF1-CARP"]["CO"]["precio_referencia"])
    oficial_co = float(por["MO-OF1"]["CO"]["precio_referencia"])
    assert abs(carpintero_co - oficial_co) < 1e-9
    assert "derivado" in por["MO-OF1-CARP"]["CO"]["confianza"]
    assert "coste-empresa" in por["MO-OF1-CARP"]["CO"]["observaciones"].lower()
    # Ayudante especializado = punto medio (oficial + ayudante) factorizado.
    medio = (JORNAL_OF1["CO"] + JORNAL_AYU["CO"]) * FACTORES["CO"] / 16
    assert abs(float(por["MO-AYU-ESP"]["CO"]["precio_referencia"]) - medio) < 1e-6


def test_especialidades_directas_tambien_factorizadas() -> None:
    por = _por_recurso(_filas())
    electricista = float(por["MO-OF1-ELE"]["CO"]["precio_referencia"])
    assert abs(electricista - 125_000 * FACTORES["CO"] / 8) < 1e-6
    soldador_mx = float(por["MO-OF1-SOLD"]["MX"]["precio_referencia"])
    assert abs(soldador_mx - 1_350 * FACTORES["MX"] / 8) < 1e-6


def test_todas_las_filas_mo_conservan_confianza_original() -> None:
    por = _por_recurso(_filas())
    # Jornal local del oficio solo en estos códigos/países (ver ESPECIALIDAD_DIRECTA).
    directos = {"MO-OF1", "MO-OF1-ALB"}
    especiales_directas = {
        ("MO-OF1-ELE", "CO"), ("MO-OF1-PLO", "CO"), ("MO-OF1-PIN", "CO"), ("MO-OF1-SOLD", "CO"),
        ("MO-OF1-ELE", "MX"), ("MO-OF1-PLO", "MX"), ("MO-OF1-PIN", "MX"), ("MO-OF1-SOLD", "MX"),
        ("MO-OF1-ELE", "EC"), ("MO-OF1-PLO", "EC"), ("MO-OF1-PIN", "EC"), ("MO-OF1-SOLD", "EC"),
    }
    confianzas = {"referencia", "derivado"}
    for codigo, por_pais in por.items():
        if not codigo.startswith("MO-"):
            continue
        for pais, fila in por_pais.items():
            assert fila["confianza"] in confianzas, f"{codigo}/{pais}"
            if codigo in directos or (codigo, pais) in especiales_directas:
                assert fila["confianza"] == "referencia", f"{codigo}/{pais}"
