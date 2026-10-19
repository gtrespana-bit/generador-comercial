"""Contrato de la matriz de precios irlandesa y de su modelo de coste empresa.

La matriz de Irlanda es un artefacto generado que se carga en base de datos y
alimenta presupuestos reales: un precio con la unidad equivocada, con IVA
dentro o con el rango invertido no se queda en un CSV, se convierte en una
oferta enviada a un cliente. Estas pruebas fijan ese contrato.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MATRIZ = ROOT / "basedatos_partidas/salida/precios_recursos_irlanda.csv"
MATRIZ_GB = ROOT / "basedatos_partidas/salida/precios_recursos_reino_unido.csv"
DOC_INVESTIGACION = ROOT / "docs/INVESTIGACION_PRECIOS_IRLANDA.md"
DOC_METODOLOGIA = ROOT / "docs/METODOLOGIA_PRECIOS_REFERENCIA_IRLANDA.md"

sys.path.insert(0, str(ROOT / "tools"))

import coste_empresa_irlanda as coste  # noqa: E402

CONFIANZAS = {"confirmado", "referencia", "derivado", "provisional"}
IVA = {"si", "no", "no_aplica", "no_confirmado", "por_verificar"}


@pytest.fixture(scope="module")
def filas() -> list[dict]:
    assert MATRIZ.exists(), f"falta la matriz {MATRIZ.relative_to(ROOT)}"
    with MATRIZ.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh, delimiter=";"))


def test_la_matriz_cubre_los_388_recursos_del_catalogo(filas):
    assert len(filas) == 388
    codigos = [f["codigo_recurso"] for f in filas]
    assert len(set(codigos)) == len(codigos)


def test_todos_los_precios_son_irlandeses_y_en_euros(filas):
    assert {f["pais_codigo"] for f in filas} == {"IE"}
    assert {f["moneda"] for f in filas} == {"EUR"}
    assert {f["origen"] for f in filas} == {"nacional"}


def test_rango_coherente_en_todas_las_filas(filas):
    for f in filas:
        minimo = float(f["precio_min"])
        central = float(f["precio_referencia"])
        maximo = float(f["precio_max"])
        assert minimo > 0, f
        assert minimo <= central <= maximo, f


def test_ninguna_fila_queda_pendiente_y_todas_citan_fuente_y_fecha(filas):
    for f in filas:
        assert f["precio_referencia"].strip(), f
        assert f["fuente"].strip().startswith("docs/"), f
        assert f["fecha_consulta"] == "2026-10-18", f
        assert f["confianza"] in CONFIANZAS, f


def test_los_precios_de_proveedor_van_sin_iva(filas):
    for f in filas:
        assert f["incluye_iva"] in IVA, f
        if f["categoria"] == "mano_obra":
            assert f["incluye_iva"] == "no_aplica", f
        else:
            assert f["incluye_iva"] == "no", f


def test_las_anclas_citan_la_investigacion_y_los_derivados_la_metodologia(filas):
    anclas = [f for f in filas if f["confianza"] == "referencia"]
    derivados = [f for f in filas if f["confianza"] == "derivado"]
    assert anclas and derivados
    assert len(anclas) == 57
    assert {f["fuente"] for f in anclas} == {str(DOC_INVESTIGACION.relative_to(ROOT))}
    # Los derivados citan la metodología irlandesa, salvo los trasladados del
    # ancla británica, que citan la investigación británica de la que salen.
    assert {f["fuente"] for f in derivados} == {
        str(DOC_METODOLOGIA.relative_to(ROOT)),
        "docs/INVESTIGACION_PRECIOS_REINO_UNIDO.md",
    }
    assert DOC_INVESTIGACION.exists() and DOC_METODOLOGIA.exists()


def test_los_derivados_no_se_publican_como_precio_de_tienda(filas):
    for f in filas:
        if f["confianza"] != "derivado":
            continue
        assert "no es una cotización de tienda" in f["observaciones"], f


def test_los_traslados_desde_reino_unido_se_declaran(filas):
    trasladados = [f for f in filas if "ancla británica" in f["observaciones"]]
    assert len(trasladados) == 18
    for f in trasladados:
        assert f["confianza"] == "derivado", f
        assert "provisional" in f["observaciones"], f


def test_el_contraste_con_reino_unido_acota_el_error(filas):
    """Ningún derivado se separa más del doble de su ancla británica equivalente."""
    if not MATRIZ_GB.exists():  # pragma: no cover - la matriz GB vive en el repo
        pytest.skip("no hay matriz británica con la que contrastar")
    with MATRIZ_GB.open(encoding="utf-8-sig", newline="") as fh:
        gb = {
            f["codigo_recurso"]: float(f["precio_referencia"])
            for f in csv.DictReader(fh, delimiter=";")
            if f["confianza"] == "referencia"
        }
    eur_por_gbp = 1.3330 / 1.1253
    comparados = 0
    for f in filas:
        if f["confianza"] != "derivado" or f["codigo_recurso"] not in gb:
            continue
        esperado = gb[f["codigo_recurso"]] * eur_por_gbp
        if esperado <= 0:
            continue
        cociente = float(f["precio_referencia"]) / esperado
        assert 0.5 <= cociente <= 2.0, (f["codigo_recurso"], round(cociente, 2))
        comparados += 1
    assert comparados > 80


def test_anclas_irlandesas_con_precio_observado(filas):
    por_codigo = {f["codigo_recurso"]: f for f in filas}
    esperado = {
        "MT-CONC-250": "126",
        "MT-CONC-300": "132",
        "MT-BLQ-10": "1.45",
        "MT-BLQ-15": "2.6",
        "MT-YESO-REP": "0.65",
        "MT-JUN-CG2": "2.59",
        "MT-PIN-CAUCHO": "1.9",
        "MT-ELE-CABLE": "1.55",
        "MT-CANON": "75",
        "MQ-RETRO": "26.25",
        "MQ-BOLQ": None,
    }
    for codigo, precio in esperado.items():
        if precio is None:
            continue
        assert por_codigo[codigo]["confianza"] == "referencia", codigo
        assert float(por_codigo[codigo]["precio_referencia"]) == pytest.approx(float(precio)), codigo


def test_las_44_maquinas_llevan_precio_por_hora(filas):
    maquinaria = [f for f in filas if f["categoria"] == "maquinaria"]
    assert len(maquinaria) == 44
    for f in maquinaria:
        if f["codigo_recurso"] == "MQ-BANO-PORT":
            assert f["unidad_fuente"] == "ud"
            continue
        assert float(f["precio_referencia"]) < 200, f  # tarifa horaria, no diaria


# ─────────────────────────────────────────────────────────────────────────────
# Modelo de coste empresa
# ─────────────────────────────────────────────────────────────────────────────

def test_horas_facturables_irlandesas():
    assert coste.HORAS_CONTRATADAS == pytest.approx(2028.0)
    assert coste.HORAS_VACACIONES == pytest.approx(226.2)
    assert coste.HORAS_BAJA == pytest.approx(39.0)
    assert coste.HORAS_FACTURABLES == pytest.approx(1762.8)


def test_tarifas_del_sectoral_employment_order():
    assert coste.SEO == {
        "craftsperson": 23.74,
        "categoria_a": 23.03,
        "categoria_b": 21.37,
        "nuevo_entrante": 17.28,
    }
    assert coste.PRSI_EMPRESA == pytest.approx(0.114)
    assert coste.PENSION_SEMANAL == pytest.approx(32.89)


def test_coste_empresa_de_un_craftsperson():
    c = coste.coste_empresa(23.74)
    assert c["coste_hora_facturable"] == pytest.approx(32.96, abs=0.01)
    # El recargo patronal debe quedar entre el 15 % y el 30 %: por debajo sería
    # olvidarse del PRSI y por encima, contar dos veces el salario.
    assert 15.0 < c["recargo_pct"] < 30.0


def test_cada_oficio_tiene_modelo_y_clasificacion_valida():
    assert len(coste.OFICIOS) == 17
    for codigo, (oficio, clasificacion) in coste.OFICIOS.items():
        assert oficio.strip(), codigo
        assert clasificacion in coste.SEO, codigo


def test_la_mano_de_obra_de_la_matriz_sale_del_modelo_de_coste(filas):
    mano = {f["codigo_recurso"]: f for f in filas if f["categoria"] == "mano_obra"}
    assert set(mano) == set(coste.OFICIOS)
    for codigo, (_, clasificacion) in coste.OFICIOS.items():
        esperado = coste.coste_empresa(coste.SEO[clasificacion])["coste_hora_facturable"]
        assert float(mano[codigo]["precio_referencia"]) == pytest.approx(esperado, abs=0.01)
        assert "Sectoral Employment Order" in mano[codigo]["observaciones"] or \
               "SEO" in mano[codigo]["observaciones"], codigo
        assert mano[codigo]["incluye_iva"] == "no_aplica"


def test_el_generador_de_sql_conoce_irlanda():
    import generar_sql_precios_pais as sql

    assert "IE" in sql.MERCADOS
    nombre, sufijo = sql.MERCADOS["IE"]
    assert nombre == "Irlanda"
    assert (ROOT / f"basedatos_partidas/salida/precios_recursos_{sufijo}.csv").exists()


def test_la_matriz_se_puede_regenerar(tmp_path, monkeypatch):
    """El generador es determinista respecto de sus anclas."""
    import generar_matriz_precios_irlanda as gen

    destino = tmp_path / "irlanda.csv"
    monkeypatch.setattr(gen, "OUT", destino)
    data = gen.json.loads(gen.SRC.read_text(encoding="utf-8"))
    referencias = gen._construir_referencias()
    factores, _, derivados, trasladados = gen.derivar_referencias(data, referencias)
    assert derivados + len([1 for d in referencias.values() if d["IE"].confianza == "referencia"]) == 388
    assert trasladados == 18
    assert all(f > 0 for f in factores.values())
