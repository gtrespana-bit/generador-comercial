"""Matriz nacional de precios de recursos — Estados Unidos (USD).

La matriz la genera ``tools/generar_matriz_precios_eeuu.py`` desde la
investigación de mercado documentada en
``docs/INVESTIGACION_PRECIOS_ESTADOS_UNIDOS.md``. Estos tests fijan el
contrato: cobertura completa del catálogo, USD sin «sales tax», rangos
válidos y mano de obra a coste empresa estadounidense (medianas
nacionales BLS OEWS + FICA/FUTA/SUTA + workers' compensation por clase
NCCI), nunca a tarifa de subcontrata 1099 ni por arrastre de la base VE
en USD (que la moneda coincida no convierte el precio venezolano en
estadounidense).

Estados Unidos es el único mercado imperial del producto, pero la matriz
se publica **convertida a la unidad métrica del recurso**: la carga por
SQL inserta el precio tal cual (sin conversión), así que una matriz en
$/yd³ o $/ft² corrompería los precios en silencio. El formato nativo
investigado queda citado en la observación de cada ancla.
"""
from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]


def _filas_matriz_eeuu():
    ruta = RAIZ / "basedatos_partidas" / "salida" / "precios_recursos_estados_unidos.csv"
    assert ruta.is_file(), (
        "Falta la matriz de precios US; ejecutar "
        "tools/generar_matriz_precios_eeuu.py"
    )
    with ruta.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh, delimiter=";"))


def _catalogo():
    data = json.loads(
        (RAIZ / "basedatos_partidas" / "datos" / "recursos.json").read_text(
            encoding="utf-8"
        )
    )
    salida = {}
    for categoria in ("mano_obra", "materiales", "maquinaria"):
        for codigo, item in (data.get(categoria) or {}).items():
            if (
                isinstance(item, dict)
                and "descripcion" in item
                and not item.get("composicion")
            ):
                salida[codigo] = item
    return salida


def _modulo_coste_eeuu():
    ruta = RAIZ / "tools" / "coste_empresa_eeuu.py"
    spec = importlib.util.spec_from_file_location("coste_empresa_eeuu", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_matriz_eeuu_cubre_todos_los_recursos():
    filas = _filas_matriz_eeuu()
    esperados = set(_catalogo())
    cubiertos = [f["codigo_recurso"] for f in filas]
    assert len(cubiertos) == len(set(cubiertos)), "Códigos duplicados en la matriz US"
    assert set(cubiertos) == esperados, (
        f"Faltan {sorted(esperados - set(cubiertos))}; "
        f"sobran {sorted(set(cubiertos) - esperados)}"
    )


def test_matriz_eeuu_es_usd_sin_impuesto_y_con_rangos_validos():
    filas = _filas_matriz_eeuu()
    assert filas, "La matriz US está vacía"
    for f in filas:
        assert f["pais_codigo"] == "US"
        assert f["moneda"] == "USD"
        # Toda la matriz es sin «sales tax»: el precio publicado en
        # EE. UU. es siempre antes de impuestos.
        assert f["incluye_iva"] in ("no", "no_aplica"), f["codigo_recurso"]
        precio = float(f["precio_referencia"])
        minimo = float(f["precio_min"])
        maximo = float(f["precio_max"])
        assert precio > 0, f"{f['codigo_recurso']} sin precio"
        assert 0 < minimo <= precio <= maximo, f"Rango inválido en {f['codigo_recurso']}"


def test_matriz_eeuu_se_publica_en_unidades_del_recurso():
    """Mercado imperial, matriz en la unidad métrica del catálogo.

    La ruta de carga por SQL (``tools/generar_sql_precios_pais.py``)
    inserta ``precio`` tal cual, sin la conversión imperial que sí hace
    el importador del panel. Si la matriz se publicara en $/yd³ o
    $/ft², esos números quedarían guardados como $/m³ o $/m². Por eso
    ``unidad_fuente`` debe ser siempre la unidad del recurso y la
    conversión vive en el generador, citada en observaciones.
    """
    catalogo = _catalogo()
    for f in _filas_matriz_eeuu():
        assert f["unidad_fuente"] == catalogo[f["codigo_recurso"]]["unidad"], (
            f"{f['codigo_recurso']}: la matriz US debe publicarse en la "
            "unidad del recurso, no en la unidad imperial investigada"
        )


def test_matriz_eeuu_mano_obra_a_coste_empresa():
    filas = {f["codigo_recurso"]: f for f in _filas_matriz_eeuu()}
    oficial = float(filas["MO-OF1"]["precio_referencia"])
    peon = float(filas["MO-AYU"]["precio_referencia"])
    electricista = float(filas["MO-OF1-ELE"]["precio_referencia"])
    fontanero = float(filas["MO-OF1-PLO"]["precio_referencia"])
    cabillero = float(filas["MO-OF1-CAB"]["precio_referencia"])
    Carpintero = float(filas["MO-OF1-CARP"]["precio_referencia"])
    jardinero = float(filas["MO-OF1-JARD"]["precio_referencia"])
    # Coste empresa US 2026 (mediana nacional OEWS): carpintero
    # 30,58 $/h → 39,07 $/h trabajada; peón 23,79 → 30,68. Muy por
    # debajo de la tarifa facturada de un GC o del paquete sindical de
    # una gran metro: la matriz es el empleador «open shop» mediano.
    assert 36 <= oficial <= 42, f"Oficial fuera de coste empresa US: {oficial}"
    assert 28 <= peon <= 33, f"Peón fuera de coste empresa US: {peon}"
    assert oficial > peon
    # El fontanero es el oficio más caro de la matriz (mediana OEWS más
    # alta y clase de workers' comp benigna); el electricista le sigue.
    assert fontanero > electricista > oficial
    # El cabillero cobra una mediana OEWS menor que el carpintero
    # (28,35 < 29,12) pero su workers' comp (≈10 $/100 $ frente a
    # 6,75) le devuelve el coste a la par del oficial general.
    assert cabillero >= oficial
    # Mismo salario que el oficial general, pero el encofrador va a la
    # clase de estructura (7,75 frente a 6,75): cuesta más solo por el
    # seguro.
    assert Carpintero > oficial
    assert jardinero < peon


def test_matriz_eeuu_mano_obra_rango_de_mediana():
    """El rango es −15 % / +35 %: la base es la mediana nacional OEWS.

    La dispersión estatal/metro del BLS es de ±20-40 % por ocupación
    (HVAC: DC 40,57 $/h frente a Arkansas 23,13), la mayor de los cinco
    mercados anglófonos; un rango estrecho fingiría una precisión que
    la mediana nacional no tiene.
    """
    for f in _filas_matriz_eeuu():
        if f["categoria"] != "mano_obra":
            continue
        precio = float(f["precio_referencia"])
        minimo = float(f["precio_min"])
        maximo = float(f["precio_max"])
        # Tolerancia por el redondeo a 6 decimales con que se publica el CSV.
        assert minimo == pytest.approx(precio * 0.85, rel=1e-4), f["codigo_recurso"]
        assert maximo == pytest.approx(precio * 1.35, rel=1e-4), f["codigo_recurso"]


def test_matriz_eeuu_tiene_referencias_y_derivadas():
    filas = _filas_matriz_eeuu()
    confianzas = {f["confianza"] for f in filas}
    assert "referencia" in confianzas, "No hay anclas observadas"
    assert "derivado" in confianzas, "No hay canasta derivada"
    # Sin filas pendientes: la matriz es carga completa.
    assert all(f["confianza"] in ("referencia", "derivado") for f in filas)
    investigados = sum(1 for f in filas if f["confianza"] == "referencia")
    # Corte 2026-10-19: 52 anclas (17 MO + 8 maquinaria + 27 materiales).
    assert investigados >= 46, f"Solo {investigados} recursos investigados"


def test_matriz_eeuu_anclas_clave_investigadas():
    """Precios observados que no deben «derivar» por accidente al regenerar."""
    filas = {f["codigo_recurso"]: f for f in _filas_matriz_eeuu()}
    esperadas = {
        # 3.000 PSI a 152 $/yd³ de lista → 198,81 $/m³.
        "MT-CONC-210": 198.81,
        # Saco de Portland de 94 lb a 19,00 $ → 0,446 $/kg.
        "MT-CEMENTO": 0.446,
        # CMU de 8×8×16" a 2,40 $ de estantería nacional.
        "MT-BLQ-20": 2.40,
        # USG ½" 4×8 ft a 15,00 $/hoja (2,967 m²) → 5,05 $/m².
        "MT-PYL-PLACA125": 5.05,
        # Miniexcavadora + martillo, 475 $/día → $/h de jornada.
        "MQ-RETRO": 59.375,
    }
    for codigo, precio in esperadas.items():
        fila = filas[codigo]
        assert fila["confianza"] == "referencia", codigo
        assert float(fila["precio_referencia"]) == pytest.approx(precio), codigo


def test_coste_empresa_eeuu_parametros_2026():
    m = _modulo_coste_eeuu()
    # Divisor: 260 − 10 vacaciones − 8 festivos − 3 baja = 239 días × 8 h;
    # pagadas 2.080 h (el PTO va dentro, práctica estadounidense).
    assert m.DIAS_TRABAJADOS == pytest.approx(239.0)
    assert m.HORAS_FACTURABLES == pytest.approx(1912.0)
    assert m.HORAS_PAGADAS == pytest.approx(2080.0)
    # FICA/FUTA/SUTA 2026 (SSA 24/10/2025; IRS Pub. 15).
    assert m.SS_TIPO == pytest.approx(0.062)
    assert m.SS_BASE == pytest.approx(184500.0)
    assert m.MEDICARE_TIPO == pytest.approx(0.0145)
    assert m.FUTA_TIPO_NETO == pytest.approx(0.006)
    assert m.SUTA_TIPO == pytest.approx(0.027)
    # Workers' compensation por clase NCCI: la electricidad es de las
    # benignas y el acero de refuerzo de las caras, como en Canadá con
    # el WSIB pero con más spread.
    assert m.WC["electricidad"] == pytest.approx(0.040)
    assert m.WC["acero_refuerzo"] == pytest.approx(0.100)
    assert m.WC["carp_estructura"] > m.WC["carp_general"]
    # Los topes son reales: a 100 $/h el bruto (208.000 $) supera la
    # base de la Seguridad Social y paga el máximo legislado (11.439 $),
    # mientras Medicare sigue sin techo; FUTA+SUTA quedan en 312 $.
    alto = m.coste_empresa(100.00, m.WC["peon_obra"])
    assert alto["fica"] == pytest.approx(11439.00 + 0.0145 * 208000.0, abs=0.01)
    assert alto["desempleo"] == pytest.approx(42.00 + 270.00, abs=0.01)
    # Oficial general: mediana OEWS del carpintero (29,12) a oct-2026.
    salario = m.OFICIOS["MO-OF1"][1]
    assert salario == pytest.approx(30.58)
    coste = m.coste_empresa(salario, m.WC["carp_general"])
    assert coste["coste_hora_facturable"] == pytest.approx(39.07, abs=0.05)
    # Recargo sobre el salario ≈ 17 %: FICA 7,65 %, desempleo testimonial
    # (312 $/año), workers' comp 6,75 % y el divisor de 239 días. Sin
    # seguro médico: no es obligación federal para la pyme (el BLS lo
    # cifra en ~4 $/h para quien lo ofrece: techo del rango).
    assert 14 <= coste["recargo_pct"] <= 21
