"""Matriz nacional de precios de recursos — Canadá (CAD).

La matriz la genera ``tools/generar_matriz_precios_canada.py`` desde la
investigación de mercado documentada en
``docs/INVESTIGACION_PRECIOS_CANADA.md``. Estos tests fijan el contrato:
cobertura completa del catálogo, CAD sin GST/HST, rangos válidos y mano
de obra a coste empresa canadiense (medianas Job Bank de Ontario + CPP/EI
federales con techo + WSIB por clase), nunca a tarifa de autónomo ni por
conversión de divisa desde la base VE en USD.

Canadá no tiene escala legal sectorial (ni SEO ni award): la base es la
mediana salarial oficial, como la ONS en el Reino Unido, así que el rango
de mano de obra baja un 10 % (no el −3 % de IE/AU). El perfil provincial
es Ontario; el paquete sindical ICI del GTA queda por encima del rango y
así se documenta, no se disimula.
"""
from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]


def _filas_matriz_canada():
    ruta = RAIZ / "basedatos_partidas" / "salida" / "precios_recursos_canada.csv"
    assert ruta.is_file(), (
        "Falta la matriz de precios CA; ejecutar "
        "tools/generar_matriz_precios_canada.py"
    )
    with ruta.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh, delimiter=";"))


def _modulo_coste_canada():
    ruta = RAIZ / "tools" / "coste_empresa_canada.py"
    spec = importlib.util.spec_from_file_location("coste_empresa_canada", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_matriz_canada_cubre_todos_los_recursos():
    filas = _filas_matriz_canada()
    # Los compuestos se abren en componentes y no son recursos físicos.
    data = json.loads(
        (RAIZ / "basedatos_partidas" / "datos" / "recursos.json").read_text(
            encoding="utf-8"
        )
    )
    esperados = set()
    for categoria in ("mano_obra", "materiales", "maquinaria"):
        for codigo, item in (data.get(categoria) or {}).items():
            if (
                isinstance(item, dict)
                and "descripcion" in item
                and not item.get("composicion")
            ):
                esperados.add(codigo)
    cubiertos = [f["codigo_recurso"] for f in filas]
    assert len(cubiertos) == len(set(cubiertos)), "Códigos duplicados en la matriz CA"
    assert set(cubiertos) == esperados, (
        f"Faltan {sorted(esperados - set(cubiertos))}; "
        f"sobran {sorted(set(cubiertos) - esperados)}"
    )


def test_matriz_canada_es_cad_y_con_rangos_validos():
    filas = _filas_matriz_canada()
    assert filas, "La matriz CA está vacía"
    for f in filas:
        assert f["pais_codigo"] == "CA"
        assert f["moneda"] == "CAD"
        # Toda la matriz es sin GST/HST. En Canadá el precio de estantería
        # ya se publica sin impuestos («+ taxes»), al contrario que en AU.
        assert f["incluye_iva"] in ("no", "no_aplica"), f["codigo_recurso"]
        precio = float(f["precio_referencia"])
        minimo = float(f["precio_min"])
        maximo = float(f["precio_max"])
        assert precio > 0, f"{f['codigo_recurso']} sin precio"
        assert 0 < minimo <= precio <= maximo, f"Rango inválido en {f['codigo_recurso']}"


def test_matriz_canada_mano_obra_a_coste_empresa():
    filas = {f["codigo_recurso"]: f for f in _filas_matriz_canada()}
    oficial = float(filas["MO-OF1"]["precio_referencia"])
    peon = float(filas["MO-AYU"]["precio_referencia"])
    electricista = float(filas["MO-OF1-ELE"]["precio_referencia"])
    fontanero = float(filas["MO-OF1-PLO"]["precio_referencia"])
    cabillero = float(filas["MO-OF1-CAB"]["precio_referencia"])
    albanil = float(filas["MO-OF1-ALB"]["precio_referencia"])
    Carpintero = float(filas["MO-OF1-CARP"]["precio_referencia"])
    # Coste empresa CA 2026 (perfil Ontario): mediana Job Bank del
    # carpintero 33,60 $/h → 42,09 $/h facturable; peón 28,35 → 35,84.
    # Muy por debajo del «total package» sindical ICI del GTA
    # (peón ≈54-61 $/h): la matriz es open-shop mediano, no convenio.
    assert 39 <= oficial <= 46, f"Oficial fuera de coste empresa CA: {oficial}"
    assert 33 <= peon <= 39, f"Peón fuera de coste empresa CA: {peon}"
    assert oficial > peon
    assert electricista > oficial
    assert fontanero > oficial
    # Particularidad canadiense: el rodworker (suboficio del ironworker,
    # mediana más alta del Job Bank) es el oficio más caro de la matriz,
    # por encima incluso del albañil. Es lo contrario que en IE/AU, donde
    # el steel fixer es categoría menor: no «corregir» este orden.
    assert cabillero > albanil > oficial
    # Mismo salario que el oficial general, pero el encofrador cotiza WSIB
    # clase G3 (estructura, 3,55 %) y el general G1 (2,18 %): el coste
    # difiere solo por la clase de seguro.
    assert Carpintero > oficial


def test_matriz_canada_mano_obra_rango_de_mediana():
    """El rango es −10 % / +25 %, no el −3 % / +20 % de IE y AU.

    En Irlanda y Australia la base es el mínimo legal (SEO / award) y no
    admite rebaja regional. En Canadá la base es la mediana salarial de
    Ontario (Job Bank), como la ONS en GB: hay mercado legal por debajo
    (Atlántico, residencial rural) y por encima (GTA, Alberta, BC).
    """
    for f in _filas_matriz_canada():
        if f["categoria"] != "mano_obra":
            continue
        precio = float(f["precio_referencia"])
        minimo = float(f["precio_min"])
        maximo = float(f["precio_max"])
        # Tolerancia por el redondeo a 6 decimales con que se publica el CSV.
        assert minimo == pytest.approx(precio * 0.90, rel=1e-4), f["codigo_recurso"]
        assert maximo == pytest.approx(precio * 1.25, rel=1e-4), f["codigo_recurso"]


def test_matriz_canada_tiene_referencias_y_derivadas():
    filas = _filas_matriz_canada()
    confianzas = {f["confianza"] for f in filas}
    assert "referencia" in confianzas, "No hay anclas observadas"
    assert "derivado" in confianzas, "No hay canasta derivada"
    # Sin filas pendientes: la matriz es carga completa.
    assert all(f["confianza"] in ("referencia", "derivado") for f in filas)
    investigados = sum(1 for f in filas if f["confianza"] == "referencia")
    # Corte 2026-10-19: 52 anclas (17 MO + 8 maquinaria + 27 materiales).
    # El retail canadiense es transparente (Home Depot, HBS), pero planta
    # de hormigón, acero y madera se cotizan por cuenta o por guía.
    assert investigados >= 46, f"Solo {investigados} recursos investigados"


def test_matriz_canada_anclas_clave_investigadas():
    """Precios observados que no deben «derivar» por accidente al regenerar."""
    filas = {f["codigo_recurso"]: f for f in _filas_matriz_canada()}
    esperadas = {
        # Listas de planta GTA 2026 (CBM 245 / Ontario Redi-Mix 266 $/m³).
        "MT-CONC-250": 260.0,
        # Saco de Portland de 40 kg a ≈21,90-24,30 $ → ≈0,56 $/kg.
        "MT-CEMENTO": 0.56,
        # CMU de 8" (190 mm) a 4,19 $ en Ontario, a 2026.
        "MT-BLQ-20": 4.40,
        # CGC 1/2" 4×8 ft a 14-18 $/hoja (2,97 m²) → ≈5,55 $/m².
        "MT-PYL-PLACA125": 5.55,
        # Miniexcavadora 3,5 t + martillo, 550 $/día → $/h de jornada.
        "MQ-RETRO": 68.75,
    }
    for codigo, precio in esperadas.items():
        fila = filas[codigo]
        assert fila["confianza"] == "referencia", codigo
        assert float(fila["precio_referencia"]) == pytest.approx(precio), codigo


def test_coste_empresa_canada_parametros_2026():
    m = _modulo_coste_canada()
    # Divisor: 260 − 10 vacaciones ESA − 9 festivos ON − 3 baja no pagada
    # = 238 días × 8 h; pagadas = trabajadas + festivos = 1.976 h.
    assert m.DIAS_TRABAJADOS == pytest.approx(238.0)
    assert m.HORAS_FACTURABLES == pytest.approx(1904.0)
    assert m.HORAS_PAGADAS == pytest.approx(1976.0)
    assert m.VACATION_PAY == pytest.approx(0.04)
    # CPP/EI 2026 (CRA/CEIC): tipos y techos federales.
    assert m.CPP_TIPO == pytest.approx(0.0595)
    assert m.CPP_YMPE == pytest.approx(74600.0)
    assert m.CPP_YAMPE == pytest.approx(85000.0)
    assert m.EI_TIPO_EMPRESA == pytest.approx(0.02282)
    assert m.EI_TOPE == pytest.approx(68900.0)
    # WSIB Ontario 2026 por clase de construcción.
    assert m.WSIB["G1"] == pytest.approx(0.0218)
    assert m.WSIB["G3"] == pytest.approx(0.0355)
    assert m.WSIB["G4"] == pytest.approx(0.0154)
    # El CPP tiene techo real: a salarios altos paga el máximo legislado
    # (4.230,45 + CPP2 416,00), no un % plano del bruto.
    alto = m.coste_empresa(60.00, m.WSIB["G3"])
    assert alto["cpp"] == pytest.approx(4230.45 + 416.00, abs=0.01)
    assert alto["ei"] == pytest.approx(1572.30, abs=0.01)
    # Oficial general: mediana Job Bank del carpintero (32,00) a 2026.
    salario = m.OFICIOS["MO-OF1"][1]
    assert salario == pytest.approx(33.60)
    coste = m.coste_empresa(salario, m.WSIB["G1"])
    assert coste["coste_hora_facturable"] == pytest.approx(42.09, abs=0.05)
    # Recargo sobre salario ≈ 20,7 %: CPP+EI con techo, WSIB por clase,
    # vacation pay 4 % y el divisor de 238 días. El EHT de Ontario queda
    # fuera (exención de 1 M$ de nómina: la pyme tipo no lo paga).
    assert 18 <= coste["recargo_pct"] <= 24
