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
    assert len({f["codigo_recurso"] for f in filas}) == 390
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
    assert len(confirmados) == 371
    # Tras la revisión cruzada exhaustiva, solo 16 recursos quedan como
    # solo_fuente_propia (sin observación bancaria independiente dentro del
    # ±15 %). Todos tienen precio_revisado cumplimentado.
    assert sum(1 for f in verificacion.values()
               if f["veredicto"] == "solo_fuente_propia") == 16
    assert all(f["precio_revisado"].strip() for f in verificacion.values()
               if f["veredicto"] == "solo_fuente_propia")
    divergentes = [f for f in verificacion.values() if f["veredicto"] == "divergencia_verificada"]
    assert len(divergentes) == 2
    assert {d["codigo_recurso"] for d in divergentes} == {"MT-BREAKER", "MT-PYL-PASTA"}
    # Las divergencias verificadas tienen fuentes comerciales (no bancarias),
    # por lo que familia_independiente puede estar vacía.


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
        # MT-BLQ-20 ya estaba confirmado antes de este lote: no aparece en el
        # archivo de confirmaciones de este lote, pero sí en el registro.
        registro = {f["codigo_recurso"]: f for f in leer(DOC / "espana_2026-11-06.csv")}
        assert registro["MT-BLQ-20"]["estado_auditoria"] == "confirmado_referencia"
        assert "P01BG200" in registro["MT-BLQ-20"]["fuente_observada"]
        # Confirmar no reescribe el precio: el precio revisado (0,68) se mantiene
        # dentro del ±15 % de la ficha del banco (0,63).
        assert verificacion["MT-BLQ-20"]["precio_revisado"] == "0.68"
    for codigo in ("MT-BREAKER", "MT-PYL-PASTA", "MT-EXTINTOR", "MT-ANCLA-PIEDRA"):
        assert verificacion[codigo]["revision_manual"]


def test_confirmaciones_aplicadas_incluyen_la_segunda_base():
    confirmaciones = {f["codigo_recurso"]: f for f in leer(DOC / "espana_confirmaciones_2026-11-07.csv")}
    # 53 recursos ya confirmados en el cierre + las 337 confirmaciones cruzadas
    # de esta tabla cubren los 390: no queda ninguno fuera.
    assert len(confirmaciones) == 337
    extremadura = [c for c, f in confirmaciones.items() if f["fuente"] == "extremadura"]
    assert len(extremadura) > 0
    registro = {f["codigo_recurso"]: f for f in leer(DOC / "espana_2026-11-06.csv")}
    for codigo in extremadura:
        assert registro[codigo]["estado_auditoria"] == "confirmado_referencia"
    assert (DOC / "espana_cribado_extremadura_2026-11-07.csv").exists()
