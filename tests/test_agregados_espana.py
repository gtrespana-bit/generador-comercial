"""Agregados: la decisión de recomponer sale de su peso en el coste directo."""
import csv
from decimal import Decimal
from pathlib import Path

from tools import pesar_agregados_espana as pesos

ROOT = Path(__file__).resolve().parents[1]


def leer(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def test_peso_alto_se_recompone():
    assert pesos.decidir(Decimal("27.4"), 47, 40) == "recomponer"


def test_peso_bajo_no_se_recompone_por_muchos_usos():
    # 398 usos y 1,3 % de peso: usar mucho no es importar mucho.
    assert pesos.decidir(Decimal("1.3"), 398, 0) == "documentar"


def test_peso_medio_con_tercio_de_partidas_afectadas_se_recompone():
    assert pesos.decidir(Decimal("9.4"), 44, 20) == "recomponer"
    assert pesos.decidir(Decimal("9.4"), 44, 10) == "documentar"


def test_el_informe_cubre_los_diecinueve_agregados():
    filas = leer(pesos.SALIDA)
    assert len(filas) == 19
    assert {f["codigo_recurso"] for f in filas} == set(pesos.AGREGADOS)
    recomponer = {f["codigo_recurso"] for f in filas if f["decision"] == "recomponer"}
    assert recomponer == {"MT-HERRAJE-CLOSET", "MT-HERRAJE-PUERTA", "MT-PLO-ACC4",
                          "MT-PLO-DESAG", "MT-SAN-FIJA", "MT-ACC-BOMBA",
                          "MQ-PERF-PILOTE"}


def test_lo_que_cerro_el_modelo_no_se_recompone():
    filas = {f["codigo_recurso"]: f for f in leer(pesos.SALIDA)}
    for codigo in pesos.CERRADOS:
        assert filas[codigo]["decision"] == "cerrado_por_modelo"
