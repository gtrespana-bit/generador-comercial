"""Matriz nacional de precios de recursos — Irlanda (EUR).

La matriz la genera ``tools/generar_matriz_precios_irlanda.py`` desde la
investigación de mercado documentada en
``docs/INVESTIGACION_PRECIOS_IRLANDA.md``. Estos tests fijan el contrato:
cobertura completa del catálogo, EUR sin IVA, rangos válidos y mano de obra
a coste empresa irlandés (SEO/AECI/Connect + PRSI + CWPS), nunca a tarifa
de autónomo ni por conversión de divisa desde la base VE en USD.
"""
from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]


def _filas_matriz_irlanda():
    ruta = RAIZ / "basedatos_partidas" / "salida" / "precios_recursos_irlanda.csv"
    assert ruta.is_file(), (
        "Falta la matriz de precios IE; ejecutar "
        "tools/generar_matriz_precios_irlanda.py"
    )
    with ruta.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh, delimiter=";"))


def _modulo_coste_irlanda():
    ruta = RAIZ / "tools" / "coste_empresa_irlanda.py"
    spec = importlib.util.spec_from_file_location("coste_empresa_irlanda", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_matriz_irlanda_cubre_todos_los_recursos():
    filas = _filas_matriz_irlanda()
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
    assert len(cubiertos) == len(set(cubiertos)), "Códigos duplicados en la matriz IE"
    assert set(cubiertos) == esperados, (
        f"Faltan {sorted(esperados - set(cubiertos))}; "
        f"sobran {sorted(set(cubiertos) - esperados)}"
    )


def test_matriz_irlanda_es_eur_y_con_rangos_validos():
    filas = _filas_matriz_irlanda()
    assert filas, "La matriz IE está vacía"
    for f in filas:
        assert f["pais_codigo"] == "IE"
        assert f["moneda"] == "EUR"
        # Toda la matriz es sin IVA: los materiales tributan al 13,5 %
        # (hormigón/bloques) o al 23 %, pero el precio publicado nunca lo
        # incluye; la mano de obra no lleva IVA como recurso.
        assert f["incluye_iva"] in ("no", "no_aplica"), f["codigo_recurso"]
        precio = float(f["precio_referencia"])
        minimo = float(f["precio_min"])
        maximo = float(f["precio_max"])
        assert precio > 0, f"{f['codigo_recurso']} sin precio"
        assert 0 < minimo <= precio <= maximo, f"Rango inválido en {f['codigo_recurso']}"


def test_matriz_irlanda_mano_obra_a_coste_empresa():
    filas = {f["codigo_recurso"]: f for f in _filas_matriz_irlanda()}
    oficial = float(filas["MO-OF1"]["precio_referencia"])
    peon = float(filas["MO-AYU"]["precio_referencia"])
    electricista = float(filas["MO-OF1-ELE"]["precio_referencia"])
    fontanero = float(filas["MO-OF1-PLO"]["precio_referencia"])
    cabillero = float(filas["MO-OF1-CAB"]["precio_referencia"])
    ayudante_esp = float(filas["MO-AYU-ESP"]["precio_referencia"])
    # Coste empresa IE 2026: craft SEO 23,74 €/h → 32,67 €/h facturable;
    # categoría B 21,37 → 29,60. Muy por encima de ES y por debajo de la
    # tarifa de autónomo irlandesa (50-100 €/h): ni jornal ni venta.
    assert 30 <= oficial <= 35, f"Oficial fuera de coste empresa IE: {oficial}"
    assert 27 <= peon <= 32, f"Peón fuera de coste empresa IE: {peon}"
    assert oficial > peon
    # Sin SEO en vigor, las escalas pactadas eléctrica (AECI) y mecánica
    # (Connect) quedan por encima del craft del SEO de construcción.
    assert electricista > oficial
    assert fontanero > electricista
    # Particularidad irlandesa: el SEO clasifica al steel fixer en la
    # categoría A, no como craftsperson. Debe costar como el ayudante
    # especializado y menos que el oficial craft.
    assert cabillero == pytest.approx(ayudante_esp)
    assert cabillero < oficial


def test_matriz_irlanda_mano_obra_no_baja_del_minimo_legal():
    """El mínimo del rango nunca implica pagar por debajo del SEO.

    En el Reino Unido el rango baja un 10 % porque la base (mediana ONS)
    ya está sobre el convenio. En Irlanda la base ES el mínimo legal o
    pactado nacional: solo cabe −3 % de estructura de gastos.
    """
    for f in _filas_matriz_irlanda():
        if f["categoria"] != "mano_obra":
            continue
        precio = float(f["precio_referencia"])
        minimo = float(f["precio_min"])
        maximo = float(f["precio_max"])
        # Tolerancia por el redondeo a 6 decimales con que se publica el CSV.
        assert minimo >= precio * 0.97 - 1e-4, f["codigo_recurso"]
        assert maximo == pytest.approx(precio * 1.20, rel=1e-4), f["codigo_recurso"]


def test_matriz_irlanda_tiene_referencias_y_derivadas():
    filas = _filas_matriz_irlanda()
    confianzas = {f["confianza"] for f in filas}
    assert "referencia" in confianzas, "No hay anclas observadas"
    assert "derivado" in confianzas, "No hay canasta derivada"
    # Sin filas pendientes: la matriz es carga completa.
    assert all(f["confianza"] in ("referencia", "derivado") for f in filas)
    investigados = sum(1 for f in filas if f["confianza"] == "referencia")
    # Corte 2026-10-19: 106 anclas (17 MO + 29 maquinaria + 60 materiales).
    # El suelo deja margen para retirar un ancla dudosa sin romper la suite,
    # pero delata una regeneración que pierda la canasta investigada.
    assert investigados >= 100, f"Solo {investigados} recursos investigados"


def test_matriz_irlanda_anclas_clave_investigadas():
    """Precios observados que no deben «derivar» por accidente al regenerar."""
    filas = {f["codigo_recurso"]: f for f in _filas_matriz_irlanda()}
    esperadas = {
        # Hanly Quarries, único productor de la República con lista pública
        # por m³; DCPL del 5 % ya dentro del precio.
        "MT-CONC-250": 126.0,
        # Saco de 25 kg a 7,72-8,46 € ex IVA (TJ O'Mahony / McMahons).
        "MT-CEMENTO": 0.32,
        # Bloque macizo de 100 mm a 1,37-1,65 € ex IVA.
        "MT-BLQ-10": 1.45,
        # Placa de 12,5 mm: 4,99-6,10 €/m² ex IVA según marca/comercio.
        "MT-PYL-PLACA125": 5.60,
    }
    for codigo, precio in esperadas.items():
        fila = filas[codigo]
        assert fila["confianza"] == "referencia", codigo
        assert float(fila["precio_referencia"]) == pytest.approx(precio), codigo


def test_coste_empresa_irlanda_parametros_2026():
    m = _modulo_coste_irlanda()
    # Jornada y divisor: 39 h × 52 − (21 + 10) días × 7,8 − 5 días × 7,8.
    assert m.HORAS_CONTRATADAS == pytest.approx(2028.0)
    assert m.HORAS_FACTURABLES == pytest.approx(1747.2)
    # PRSI empresa desde el 1/10/2026 y CWPS desde el 3/08/2026.
    assert m.PRSI_EMPRESA == pytest.approx(0.1140)
    assert m.CWPS_EMPRESA_SEMANAL == pytest.approx(36.43)
    # Escalas: SEO 1/08/2026, AECI 16/02/2026, Connect 1/05/2026.
    assert m.SEO["craftsperson"] == pytest.approx(23.74)
    assert m.SEO["category_a"] == pytest.approx(23.03)
    assert m.SEO["category_b"] == pytest.approx(21.37)
    assert m.AECI["ano_3"] == pytest.approx(27.60)
    assert m.CONNECT["ano_3"] == pytest.approx(29.12)
    # El oficio peor pagado ya supera el umbral semanal de la tasa PRSI
    # reducida: la tasa plena aplica a los 17.
    assert m.SEO["category_b"] * m.HORAS_SEMANA > m.PRSI_UMBRAL_SEMANAL
    coste = m.coste_empresa(m.SEO["craftsperson"])
    assert coste["coste_hora_facturable"] == pytest.approx(32.67, abs=0.05)
    # Recargo sobre salario en la banda de ES (19,8 % en GB): ni el ~40 %
    # de convertir la tarifa de autónomo ni un coste sin cargas.
    assert 15 <= coste["recargo_pct"] <= 22
