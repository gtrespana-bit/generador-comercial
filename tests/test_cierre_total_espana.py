"""Cierre total: ningún recurso de España queda sin precio ni sin método declarado."""
import csv
from decimal import Decimal
from pathlib import Path

import pytest

from tools import cerrar_huecos_espana as cierre

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/auditoria_precios"


def leer(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as manejador:
        return list(csv.DictReader(manejador, delimiter=";"))


def contexto():
    return (leer(cierre.DECISIONES), {f["codigo_recurso"] for f in leer(cierre.HUECOS)},
            {f["codigo_recurso"]: f for f in leer(cierre.REGISTRO)})


def test_todos_los_recursos_tienen_precio_revisado_y_la_matriz_no_inventa_ninguno():
    registro = leer(cierre.REGISTRO)
    assert len(registro) == 388
    assert [f["codigo_recurso"] for f in registro if not f["precio_revisado"].strip()] == []
    matriz = leer(ROOT / "basedatos_partidas/salida/precios_recursos_espana.csv")
    assert {f["codigo_recurso"] for f in matriz} == {f["codigo_recurso"] for f in registro}
    assert all(Decimal(f["precio_referencia"]) > 0 for f in matriz)


def test_el_cierre_cubre_los_huecos_uno_a_uno_y_con_metodo_declarado():
    decisiones, huecos, _ = contexto()
    assert len(decisiones) == len(huecos) == 133
    assert {f["codigo_recurso"] for f in decisiones} == huecos
    assert {f["metodo"] for f in decisiones} <= set(cierre.FUENTES)
    assert {f["confianza"] for f in decisiones} <= {"alta", "media", "baja"}
    # Todo cierre lleva criterio escrito y nada lleva el separador del CSV.
    for fila in decisiones:
        assert fila["criterio"].strip()
        assert ";" not in fila["criterio"] and ";" not in fila["referencia"]


def test_los_metodos_de_banco_citan_una_ficha_real_del_banco():
    decisiones, _, _ = contexto()
    with (ROOT / "bases_precios/BCEXTGREM_26_v1.bc3").open(encoding="cp1252",
                                                          errors="replace") as manejador:
        texto = manejador.read()
    con_ficha = [f for f in decisiones if f["metodo"].startswith("banco")]
    assert len(con_ficha) >= 50
    for fila in con_ficha:
        codigos = [c.strip() for c in fila["referencia"].replace("+", " ").split()]
        assert codigos, fila["codigo_recurso"]
        for codigo in codigos:
            assert codigo in texto, f"{fila['codigo_recurso']}: {codigo} no está en la base"


def test_la_horquilla_de_mercado_conserva_el_precio_y_lo_dice():
    decisiones, _, registro = contexto()
    mercado = [f for f in decisiones if f["metodo"] == "mercado_rango"]
    assert len(mercado) >= 30
    for fila in mercado:
        assert not fila["precio"].strip()
        assert "horquilla de mercado" in fila["criterio"]
        assert Decimal(registro[fila["codigo_recurso"]]["precio_matriz"]) > 0


def test_la_horquilla_declarada_contiene_el_precio_adoptado():
    import re
    decisiones, _, registro = contexto()
    for fila in decisiones:
        if fila["metodo"] != "mercado_rango":
            continue
        rango = re.search(r"(\d+(?:[.,]\d+)?)-(\d+(?:[.,]\d+)?) EUR", fila["criterio"])
        assert rango, fila["codigo_recurso"]
        bajo = Decimal(rango.group(1).replace(",", "."))
        alto = Decimal(rango.group(2).replace(",", "."))
        precio = Decimal(registro[fila["codigo_recurso"]]["precio_matriz"])
        # Única excepción admitida: un recurso sin uso cuyo precio propio está por
        # debajo de la banda, declarado expresamente como pendiente de revisión.
        if "debe revisarse" in fila["criterio"]:
            assert precio < bajo
            assert registro[fila["codigo_recurso"]]["partidas_que_lo_usan"] == "0"
            continue
        assert bajo <= precio <= alto, (fila["codigo_recurso"], precio, bajo, alto)


def test_la_maquinaria_solo_se_valora_por_compra_amortizacion_o_por_ficha():
    decisiones, _, _ = contexto()
    metodos = {f["codigo_recurso"]: f["metodo"] for f in decisiones}
    maquinaria = [c for c in metodos if c.startswith("MQ-")]
    assert len(maquinaria) == 20
    for codigo in maquinaria:
        assert metodos[codigo] in {"modelo_propio", "modelo_alquiler", "alquiler_mercado",
                                   "banco", "banco_analogia", "compuesto"}
    # La máquina se compra y se amortiza; el servicio se alquila. No se mezclan.
    assert metodos["MQ-ESMERIL"] == "modelo_propio"
    assert metodos["MQ-BANO-PORT"] == "alquiler_mercado"
    # El modelo propio exige coste de compra explícito en el criterio.
    for codigo in maquinaria:
        if metodos[codigo] == "modelo_propio":
            criterio = next(f["criterio"] for f in decisiones
                            if f["codigo_recurso"] == codigo)
            assert "Compra" in criterio and " EUR" in criterio


def test_el_cierre_no_acepta_decisiones_incompletas_ni_de_recursos_ya_preciados():
    decisiones, huecos, registro = contexto()
    with pytest.raises(ValueError, match="sin decisión"):
        cierre.validar(decisiones[:-1], huecos, registro)
    ajeno = {"codigo_recurso": "MO-OF1", "metodo": "banco", "precio": "1",
             "referencia": "M01", "criterio": "x", "confianza": "alta"}
    with pytest.raises(ValueError, match="ya tenían precio"):
        cierre.validar(decisiones + [ajeno], huecos, registro)
    metodo_raro = dict(decisiones[0], metodo="a_ojo")
    with pytest.raises(ValueError, match="método no reconocido"):
        cierre.validar([metodo_raro] + decisiones[1:], huecos, registro)


def test_aplicar_reescribe_la_adjudicacion_sin_tocar_precios_ya_aplicados():
    decisiones, huecos, registro = contexto()
    adjudicacion = leer(cierre.ADJUDICACION)
    salida, metodos = cierre.construir(decisiones, registro, adjudicacion)
    assert salida == adjudicacion  # idempotente: la tabla ya refleja el cierre
    assert sum(metodos.values()) == 133
    por_codigo = {f["codigo_recurso"]: f for f in salida}
    for fila in decisiones:
        final = por_codigo[fila["codigo_recurso"]]
        assert final["decision"] == cierre.DECISION
        assert final["codigo_fuente"] == (fila["referencia"] or "MERCADO-2026-11-07")
        assert final["fuente"] == cierre.FUENTES[fila["metodo"]]
        assert Decimal(final["precio_adoptado"]) > 0
