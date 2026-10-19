"""Matriz nacional de precios de recursos — Australia (AUD).

La matriz la genera ``tools/generar_matriz_precios_australia.py`` desde la
investigación de mercado documentada en
``docs/INVESTIGACION_PRECIOS_AUSTRALIA.md``. Estos tests fijan el contrato:
cobertura completa del catálogo, AUD sin GST, rangos válidos y mano de obra
a coste empresa australiano (Modern Awards de la Fair Work Commission +
superannuation guarantee + workers compensation), nunca a tarifa de
autónomo (sole trader) ni por conversión de divisa desde la base VE en USD.

Australia es el mercado angloparlante con menos precios públicos: el canal
profesional (Cooper + ABN trade accounts) no publica listas y las grandes
hire companies (Coates/Kennards) tampoco, así que el suelo de anclas
investigadas es menor que en IE: el estudio lo documenta y compensa con
derivados explícitos por recurso allí donde hay evidencia parcial.
"""
from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]


def _filas_matriz_australia():
    ruta = RAIZ / "basedatos_partidas" / "salida" / "precios_recursos_australia.csv"
    assert ruta.is_file(), (
        "Falta la matriz de precios AU; ejecutar "
        "tools/generar_matriz_precios_australia.py"
    )
    with ruta.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh, delimiter=";"))


def _modulo_coste_australia():
    ruta = RAIZ / "tools" / "coste_empresa_australia.py"
    spec = importlib.util.spec_from_file_location("coste_empresa_australia", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_matriz_australia_cubre_todos_los_recursos():
    filas = _filas_matriz_australia()
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
    assert len(cubiertos) == len(set(cubiertos)), "Códigos duplicados en la matriz AU"
    assert set(cubiertos) == esperados, (
        f"Faltan {sorted(esperados - set(cubiertos))}; "
        f"sobran {sorted(set(cubiertos) - esperados)}"
    )


def test_matriz_australia_es_aud_y_con_rangos_validos():
    filas = _filas_matriz_australia()
    assert filas, "La matriz AU está vacía"
    for f in filas:
        assert f["pais_codigo"] == "AU"
        assert f["moneda"] == "AUD"
        # Toda la matriz es sin GST (10 %): las fuentes retail que lo
        # incluyen (Bunnings) se dividen entre 1,1 en el generador.
        assert f["incluye_iva"] in ("no", "no_aplica"), f["codigo_recurso"]
        precio = float(f["precio_referencia"])
        minimo = float(f["precio_min"])
        maximo = float(f["precio_max"])
        assert precio > 0, f"{f['codigo_recurso']} sin precio"
        assert 0 < minimo <= precio <= maximo, f"Rango inválido en {f['codigo_recurso']}"


def test_matriz_australia_mano_obra_a_coste_empresa():
    filas = {f["codigo_recurso"]: f for f in _filas_matriz_australia()}
    oficial = float(filas["MO-OF1"]["precio_referencia"])
    peon = float(filas["MO-AYU"]["precio_referencia"])
    electricista = float(filas["MO-OF1-ELE"]["precio_referencia"])
    fontanero = float(filas["MO-OF1-PLO"]["precio_referencia"])
    cabillero = float(filas["MO-OF1-CAB"]["precio_referencia"])
    ayudante_esp = float(filas["MO-AYU-ESP"]["precio_referencia"])
    albanil = float(filas["MO-OF1-ALB"]["precio_referencia"])
    # Coste empresa AU 2026/27: CW3 ordinario 31,22 $/h → 48,06 $/h
    # facturable; CW1(d) 29,82 → 46,10. Muy por debajo de la tarifa de
    # venta de un tradie (80-120 $/h): ni salario bruto ni venta.
    assert 45 <= oficial <= 52, f"Oficial fuera de coste empresa AU: {oficial}"
    assert 43 <= peon <= 49, f"Peón fuera de coste empresa AU: {peon}"
    assert oficial > peon
    # Los tres awards comparten la «standard rate» CW3/grado 5/L1 de
    # 1.119,10 $/semana; las diferencias salen de los pluses. El
    # electricista (tool+industry propios del MA000025) queda unas
    # décimas POR DEBAJO del oficial general y el plomero por encima:
    # no imponer un orden que el sistema de awards no garantiza.
    assert fontanero > oficial
    assert abs(electricista - oficial) < 1.0
    # Steel fixer y ayudante especializado: ambos CW2 del MA000020.
    assert cabillero == pytest.approx(ayudante_esp)
    assert cabillero < oficial
    # El albañil cobra plus de herramienta (29,26 $/semana) y el oficial
    # general no: debe costar más.
    assert albanil > oficial


def test_matriz_australia_mano_obra_no_baja_del_minimo_legal():
    """El mínimo del rango nunca implica pagar por debajo del award.

    La base es el mínimo legal del Modern Award (weekly hire), como en
    Irlanda con el SEO: solo cabe −3 % de estructura de gastos. Por
    encima, +20 % cubre acuerdos de empresa (EBA) moderados, la dispersión
    entre estados y payroll tax cuando aplica.
    """
    for f in _filas_matriz_australia():
        if f["categoria"] != "mano_obra":
            continue
        precio = float(f["precio_referencia"])
        minimo = float(f["precio_min"])
        maximo = float(f["precio_max"])
        # Tolerancia por el redondeo a 6 decimales con que se publica el CSV.
        assert minimo >= precio * 0.97 - 1e-4, f["codigo_recurso"]
        assert maximo == pytest.approx(precio * 1.20, rel=1e-4), f["codigo_recurso"]


def test_matriz_australia_tiene_referencias_y_derivadas():
    filas = _filas_matriz_australia()
    confianzas = {f["confianza"] for f in filas}
    assert "referencia" in confianzas, "No hay anclas observadas"
    assert "derivado" in confianzas, "No hay canasta derivada"
    # Sin filas pendientes: la matriz es carga completa.
    assert all(f["confianza"] in ("referencia", "derivado") for f in filas)
    investigados = sum(1 for f in filas if f["confianza"] == "referencia")
    # Corte 2026-10-19: 56 anclas (17 MO + maquinaria + materiales). El
    # comercio profesional australiano trabaja con cuentas ABN sin listas
    # públicas (Cooper, Coates, Kennards), así que el suelo es menor que
    # en IE (100) y el resto se cubre con derivados explícitos.
    assert investigados >= 50, f"Solo {investigados} recursos investigados"


def test_matriz_australia_anclas_clave_investigadas():
    """Precios observados que no deben «derivar» por accidente al regenerar."""
    filas = {f["codigo_recurso"]: f for f in _filas_matriz_australia()}
    esperadas = {
        # Listas públicas de mercado (MixHub/BuiltSimple, ago-2026):
        # N25 en NSW $250-370/m³ sin GST según banda «suministro».
        "MT-CONC-250": 325.0,
        # Saco de 20 kg a 9,01-10,70 $ con GST → ~0,45 $/kg sin GST.
        "MT-CEMENTO": 0.45,
        # Bloque Besser de 190 mm a 4,74 $ con GST → 4,31 sin GST.
        "MT-BLQ-20": 4.31,
        # Gyprock 13mm: ~$11,50/m² sin GST (Network Building/Bunnings).
        "MT-PYL-PLACA125": 11.50,
        # Excavadora 3,5t dry hire $470/día sin GST → $/h de jornada.
        "MQ-RETRO": 58.75,
    }
    for codigo, precio in esperadas.items():
        fila = filas[codigo]
        assert fila["confianza"] == "referencia", codigo
        assert float(fila["precio_referencia"]) == pytest.approx(precio), codigo


def test_coste_empresa_australia_parametros_2026():
    m = _modulo_coste_australia()
    # Divisor: 38 h × 52 = 1.976 h pagadas; 211 días trabajados
    # (260 − 20 vacaciones − 11 festivos NSW − 5 baja − 13 RDO) × 8 h.
    assert m.HORAS_PAGADAS == pytest.approx(1976.0)
    assert m.HORAS_FACTURABLES == pytest.approx(1688.0)
    assert m.DIAS_TRABAJADOS == pytest.approx(211.0)
    # Superannuation guarantee al 12 % desde el 1/7/2025; workers comp
    # NSW «House Construction» (WIC 411100) 4,84 % + 0,11 % polvo.
    assert m.SUPER_GUARANTEE == pytest.approx(0.12)
    assert m.WORKERS_COMP == pytest.approx(0.0495)
    assert m.LEAVE_LOADING == pytest.approx(0.175)
    # Building Award MA000020 desde el 1/7/2026 (cl. 19.1, semanales).
    assert m.BUILDING_SEMANAL["cw3"] == pytest.approx(1119.10)
    assert m.BUILDING_SEMANAL["cw2"] == pytest.approx(1087.50)
    assert m.BUILDING_SEMANAL["cw1d"] == pytest.approx(1066.00)
    # Ordinarios «all-purpose» eléctrico (MA000025 g5) y plomero (MA000036 L1).
    assert m.ELECTRICISTA_HORA == pytest.approx(31.13)
    assert m.FONTANERO_HORA == pytest.approx(31.63)
    # El ordinary CW3 con industry allowance general.
    salario = m.OFICIOS["MO-OF1"][1]
    assert salario == pytest.approx((1119.10 + 67.15) / 38.0)
    coste = m.coste_empresa(salario)
    assert coste["coste_hora_facturable"] == pytest.approx(48.06, abs=0.05)
    # Recargo sobre salario ≈ 31,5 %: incluye super 12 %, workers comp
    # 4,95 %, LSL 1,7 %, leave loading, travel y el divisor con RDO.
    # Payroll tax queda fuera (umbral NSW 1,2 M$ → no aplica al perfil).
    assert 28 <= coste["recargo_pct"] <= 35
