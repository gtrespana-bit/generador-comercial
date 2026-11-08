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
    assert len(confirmados) >= 37
    # El banco de 2026 acorta la lista de precios sin contraste; el modelo de
    # maquinaria (13 recursos) añade después otras 13 fichas de fuente propia.
    assert sum(1 for f in verificacion.values()
               if f["veredicto"] == "solo_fuente_propia") <= 154
    divergentes = [f for f in verificacion.values() if f["veredicto"] == "divergencia_verificada"]
    assert len(divergentes) >= 50
    assert any(f["familia_independiente"] == "extremadura" for f in divergentes)


def test_las_revisiones_manuales_mandan_sobre_el_cribado():
    correcciones = verificador.revisiones_manuales()
    assert {"MT-BREAKER", "MT-PYL-PASTA", "MT-EXTINTOR", "MT-ANCLA-PIEDRA"} <= set(
        correcciones)
    # El bloque de 20 cm se rechazó mirando la ficha de 25 cm: el rechazo se
    # revirtió porque P01BG200 (20x20x40) existe y es el mismo artículo.
    assert "MT-BLQ-20" not in correcciones
    assert correcciones["MT-EXTINTOR"]["codigo_elegido"] == "P23FJ020"
    verificacion = {f["codigo_recurso"]: f for f in leer(verificador.SALIDA)}
    for codigo in ("MT-BREAKER", "MT-PYL-PASTA"):
        assert verificacion[codigo]["veredicto"] == "divergencia_verificada"
    # La ficha exacta del bloque de 20 cm sí existía: se confirmó, no se descartó.
    assert verificacion["MT-BLQ-20"]["veredicto"] == "ya_confirmado"
    confirmadas = {f["codigo_recurso"]: f
                   for f in leer(DOC / "espana_confirmaciones_2026-11-07.csv")}
    assert confirmadas["MT-BLQ-20"]["codigo_fuente"] == "P01BG200"
    # Confirmar no reescribe el precio: la ficha del banco (0,63) queda como
    # referencia y el precio revisado (0,68) se mantiene dentro del ±15 %.
    assert verificacion["MT-BLQ-20"]["precio_revisado"] == "0.68"
    registro = {f["codigo_recurso"]: f for f in leer(DOC / "espana_2026-11-06.csv")}
    assert "P01BG200" in registro["MT-BLQ-20"]["fuente_observada"]
    for codigo in ("MT-BREAKER", "MT-PYL-PASTA", "MT-EXTINTOR", "MT-ANCLA-PIEDRA"):
        assert verificacion[codigo]["revision_manual"]


def test_confirmaciones_aplicadas_incluyen_la_segunda_base():
    confirmaciones = {f["codigo_recurso"]: f for f in leer(DOC / "espana_confirmaciones_2026-11-07.csv")}
    assert len(confirmaciones) == 19
    extremadura = [c for c, f in confirmaciones.items() if f["fuente"] == "extremadura"]
    assert set(extremadura) == {
        "MT-AGUA-OBRA", "MT-BARNIZ-PISO", "MT-BLQ-10", "MT-BLQ-15", "MT-CINTA-ENM",
        "MT-PERFIL-ACERO", "MT-POLIET", "MT-REGISTRO", "MT-BLQ-20", "MT-CONC-180",
        "MT-CONC-210", "MT-CONC-250", "MT-CONC-300"}
    registro = {f["codigo_recurso"]: f for f in leer(DOC / "espana_2026-11-06.csv")}
    for codigo in extremadura:
        assert registro[codigo]["estado_auditoria"] == "confirmado_referencia"
        assert (DOC / "espana_cribado_extremadura_2026-11-07.csv").exists()
