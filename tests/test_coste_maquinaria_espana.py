"""Modelo de coste horario de maquinaria: compra, vida útil y sensibilidad."""
import csv
from decimal import Decimal
from pathlib import Path

from tools import coste_horario_maquinaria_espana as modelo

ROOT = Path(__file__).resolve().parents[1]


def leer(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def fila_base(**cambios):
    fila = {"precio_adquisicion_sin_iva_eur": "100", "potencia_kw": "1",
            "tasa_mantenimiento": "0.15", "consumibles_eur_h": "0.10",
            "factor_carga": "0.6"}
    fila.update(cambios)
    return fila


def test_el_coste_es_amortizacion_mas_energia_mas_consumibles():
    # 100/500 * 1,15 + 1 kW * 0,20 * 0,6 + 0,10 de consumibles
    assert (modelo.coste(fila_base(), Decimal("500"), Decimal("0.20"))
            == Decimal("0.450"))


def test_el_factor_de_carga_es_de_la_maquina_no_del_modelo():
    impulsos = modelo.coste(fila_base(factor_carga="0.4"), Decimal("500"), Decimal("0.20"))
    continua = modelo.coste(fila_base(factor_carga="0.8"), Decimal("500"), Decimal("0.20"))
    assert impulsos == Decimal("0.410")
    assert continua == Decimal("0.490")


def test_sin_precio_de_adquisicion_no_se_inventa_coste():
    assert modelo.coste(fila_base(precio_adquisicion_sin_iva_eur=""),
                        Decimal("500"), Decimal("0.20")) is None


def test_la_vida_implicita_del_banco_se_deduce_de_su_tarifa():
    fila = fila_base(consumibles_eur_h="0", banda_banco_min_eur_h="0.84",
                     precio_adquisicion_sin_iva_eur="149.33", potencia_kw="0.79")
    vida = modelo.vida_implicita(fila, Decimal("0.20"))
    assert Decimal("220") < vida < Decimal("240")


def test_la_propuesta_publica_cubre_las_trece_maquinas_y_deja_fuera_el_andamio():
    publicada = {f["codigo_recurso"]: f for f in leer(modelo.SALIDA)}
    con_coste = {codigo for codigo, fila in publicada.items() if fila["coste_h"]}
    assert len(con_coste) == 13
    assert "MQ-ANDAMIO" not in publicada  # se cotiza por m2 y dia: fuera del modelo
    assert publicada["MQ-TALADRO"]["coste_h"] == "1.03"
    assert publicada["MQ-DETECTOR"]["coste_h"] == "0.30"


def test_el_precio_aplicado_en_el_registro_es_el_del_modelo():
    publicada = {f["codigo_recurso"]: f for f in leer(modelo.SALIDA)}
    registro = {f["codigo_recurso"]: f
                for f in leer(ROOT / "docs/auditoria_precios/espana_2026-11-06.csv")}
    for codigo, fila in publicada.items():
        if not fila["coste_h"]:
            continue
        assert registro[codigo]["precio_revisado"] == fila["coste_h"]
        assert "MODELO-MQ-" in registro[codigo]["codigo_fuente"]
        assert "modelo propio" in registro[codigo]["ambito_fuente"].lower()


def test_la_sensibilidad_ordena_las_vidas():
    for fila in leer(modelo.SALIDA):
        if not fila["coste_h"]:
            continue
        assert (Decimal(fila["coste_vida_mitad"]) > Decimal(fila["coste_h"])
                > Decimal(fila["coste_vida_doble"]))
