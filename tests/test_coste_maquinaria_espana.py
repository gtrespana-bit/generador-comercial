"""Modelo de coste horario de maquinaria: parámetros explícitos y sensibilidad."""
import csv
from decimal import Decimal
from pathlib import Path

from tools import coste_horario_maquinaria_espana as modelo

ROOT = Path(__file__).resolve().parents[1]


def leer(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def test_el_coste_es_amortizacion_mas_energia_mas_consumibles():
    fila = {"precio_adquisicion_sin_iva_eur": "100", "potencia_kw": "1",
            "tasa_mantenimiento": "0.15", "consumibles_eur_h": "0.10"}
    # 100/500 * 1,15 + 1 * 0,20 * 0,6 + 0,10
    assert modelo.coste(fila, Decimal("500"), Decimal("0.20")) == Decimal("0.450")


def test_sin_precio_de_adquisicion_no_se_inventa_coste():
    fila = {"precio_adquisicion_sin_iva_eur": "", "potencia_kw": "1",
            "tasa_mantenimiento": "0.15", "consumibles_eur_h": "0"}
    assert modelo.coste(fila, Decimal("500"), Decimal("0.20")) is None


def test_la_vida_implicita_del_banco_se_deduce_de_su_tarifa():
    fila = {"precio_adquisicion_sin_iva_eur": "149.33", "potencia_kw": "0.79",
            "tasa_mantenimiento": "0.15", "consumibles_eur_h": "0",
            "banda_banco_min_eur_h": "0.84"}
    vida = modelo.vida_implicita(fila, Decimal("0.20"))
    assert Decimal("220") < vida < Decimal("240")


def test_la_tabla_publicada_mantiene_los_precios_actuales():
    publicada = {f["codigo_recurso"]: f for f in leer(modelo.SALIDA)}
    registro = {f["codigo_recurso"]: f
                for f in leer(ROOT / "docs/auditoria_precios/espana_2026-11-06.csv")}
    for codigo, fila in publicada.items():
        # La propuesta no aplica precios: el registro sigue sin precio revisado.
        assert fila["precio_actual_eur_h"] == registro[codigo]["precio_matriz"]
        assert not registro[codigo]["precio_revisado"].strip()
    assert publicada["MQ-TALADRO"]["coste_250h"] == "0.78"
    assert publicada["MQ-MEZCL"]["coste_250h"] == ""
