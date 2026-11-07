"""Ingesta de una segunda base (BC3 de Extremadura 2026) y su efecto en el cribado."""
import csv
from decimal import Decimal
from pathlib import Path

import pytest

from tools import cribar_precios_espana as cribador
from tools import verificar_precios_espana as verificador

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/auditoria_precios"
CRIBADO = DOC / "espana_cribado_extremadura_2026-11-07.csv"


def leer(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as manejador:
        return list(csv.DictReader(manejador, delimiter=";"))


def bc3(tmp_path, lineas):
    ruta = tmp_path / "base.bc3"
    ruta.write_bytes(b"~V|RIB|FIEBDC-3/2020|24042026|Presto\r\n" + lineas)
    return ruta


def test_adaptador_bc3_respeta_unidades_y_categorias(tmp_path):
    ruta = bc3(tmp_path, b"~C|P01BG180|ud|Bloque de hormigon hueco 10x20x40 cm|0.50|240426|0|\r\n"
                         b"~C|P01BG190|ud|Bloque de hormigon hueco 15x20x40 cm|0.59|240426|0|\r\n"
                         b"~C|Z99XX|m|Sin categoria util|1.00|240426|0|\r\n"
                         b"~D|P04PW170|P01BG180|2|\r\n")
    precios, sha, total = cribador.cargar_bc3(ruta)
    codigos = {p["codigo"] for p in precios}
    assert len(sha) == 64 and int(total) == len(precios) == 2
    assert codigos == {"P01BG180", "P01BG190"}
    assert all(p["categoria"] == "materiales" and p["unidad"] == "ud" for p in precios)


def test_cribado_publicado_de_extremadura_cubre_el_catalogo():
    filas = leer(CRIBADO)
    assert len({f["codigo_recurso"] for f in filas}) == 388
    assert {f["banco"] for f in filas} == {"extremadura"}
    fuertes = [f for f in filas if f["codigo_fuente"]
               and Decimal(f["precision"]) >= Decimal("0.75")
               and f["numeros_compatibles"] == "si"]
    assert len(fuertes) >= 70
    for fila in filas:
        if fila["codigo_fuente"]:
            assert Decimal(fila["ratio"]) > 0


def test_la_base_nueva_aporta_confirmaciones_y_divergencias():
    verificacion = {f["codigo_recurso"]: f for f in leer(verificador.SALIDA)}
    confirmados = {c for c, f in verificacion.items()
                   if f["veredicto"] in {"ya_confirmado", "confirmado_independiente"}}
    assert len(confirmados) >= 32
    # El banco de 2026 acorta la lista de precios sin contraste.
    assert sum(1 for f in verificacion.values()
               if f["veredicto"] == "solo_fuente_propia") <= 125
    divergentes = [f for f in verificacion.values() if f["veredicto"] == "divergencia_verificada"]
    assert len(divergentes) >= 50
    assert any(f["familia_independiente"] == "extremadura" for f in divergentes)


def test_las_revisiones_manuales_mandan_sobre_el_cribado():
    correcciones = verificador.revisiones_manuales()
    assert {"MT-BLQ-20", "MT-BREAKER", "MT-PYL-PASTA"} <= set(correcciones)
    verificacion = {f["codigo_recurso"]: f for f in leer(verificador.SALIDA)}
    for codigo in ("MT-BLQ-20", "MT-BREAKER", "MT-PYL-PASTA"):
        assert verificacion[codigo]["veredicto"] == "divergencia_verificada"
        assert verificacion[codigo]["revision_manual"]


def test_confirmaciones_aplicadas_incluyen_la_segunda_base():
    confirmaciones = {f["codigo_recurso"]: f for f in leer(DOC / "espana_confirmaciones_2026-11-07.csv")}
    assert len(confirmaciones) == 14
    extremadura = [c for c, f in confirmaciones.items() if f["fuente"] == "extremadura"]
    assert set(extremadura) == {"MT-AGUA-OBRA", "MT-BARNIZ-PISO", "MT-BLQ-10", "MT-BLQ-15",
                                "MT-CINTA-ENM", "MT-PERFIL-ACERO", "MT-POLIET", "MT-REGISTRO"}
    registro = {f["codigo_recurso"]: f for f in leer(DOC / "espana_2026-11-06.csv")}
    for codigo in extremadura:
        assert registro[codigo]["estado_auditoria"] == "confirmado_referencia"
        assert (DOC / "espana_cribado_extremadura_2026-11-07.csv").exists()
