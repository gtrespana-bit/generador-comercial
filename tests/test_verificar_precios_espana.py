"""Verificación cruzada y confirmaciones de precio (España)."""
import csv
from decimal import Decimal
from pathlib import Path

import pytest

from tools import confirmar_precios_espana as confirmador
from tools import verificar_precios_espana as verificador

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/auditoria_precios"


def leer(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as manejador:
        return list(csv.DictReader(manejador, delimiter=";"))


@pytest.fixture(scope="module")
def verificacion():
    return {f["codigo_recurso"]: f for f in leer(verificador.SALIDA)}


@pytest.fixture(scope="module")
def registro():
    return {f["codigo_recurso"]: f for f in leer(confirmador.REGISTRO)}


def test_familias_documentales_se_distinguen():
    assert verificador.familia("", "https://www.juntadeandalucia.es/x") == "bcca"
    assert verificador.familia("BCCA ed. 2024-01", "") == "bcca"
    assert verificador.familia("Diputación de Palencia", "") == "palencia"
    assert verificador.familia("", "https://www.juntaex.es/documents/x.bc3") == "extremadura"
    assert verificador.familia("", "https://www.boe.es/diario_boe/x") == "modelo_propio"
    assert verificador.familia("Obramat", "https://www.obramat.es/p") == "comercial:www.obramat.es"
    assert verificador.familia("", "") == "desconocida"


def test_una_fuente_que_ya_sostiene_el_precio_no_lo_confirma():
    citadas = verificador.familias_citadas({
        "fuente_observada": "https://www.juntadeandalucia.es/bcca",
        "criterio_revisado": "Referencia BCCA 23,17 EUR/h",
        "evidencia_y_pendientes": "",
        "edicion_fuente": "2024-01",
    })
    assert "bcca" in citadas
    assert not verificador.es_independiente({"familia": "bcca"}, citadas)
    assert verificador.es_independiente({"familia": "palencia"}, citadas)
    # Un comercio nunca confirma por sí solo, aunque no figure en la evidencia.
    assert "comercial:tienda.es" not in verificador.FAMILIAS_CONFIRMAN
    assert not verificador.es_independiente({"familia": "comercial:tienda.es"},
                                            {"comercial"})


def test_matriz_de_verificacion_es_completa_y_coherente(verificacion, registro):
    assert len(verificacion) == len(registro) == 390
    for codigo, fila in verificacion.items():
        assert fila["veredicto"] in {"ya_confirmado", "confirmado_independiente",
                                     "contraste_comercial", "solo_fuente_propia",
                                     "divergencia_verificada", "sin_precio_revisado"}
        if fila["veredicto"] == "contraste_comercial":
            assert fila["familia_independiente"].startswith("comercial")
            assert abs(Decimal(fila["delta_pct"])) <= Decimal("15.0")
        if fila["veredicto"] == "ya_confirmado":
            assert registro[codigo]["estado_auditoria"] == "confirmado_referencia"
        if fila["veredicto"] == "sin_precio_revisado":
            assert not registro[codigo]["precio_revisado"].strip()
        if fila["delta_pct"]:
            assert Decimal(fila["precio_independiente"]) > 0
            assert abs(Decimal(fila["delta_pct"])) >= 0
        if fila["veredicto"] == "confirmado_independiente":
            assert abs(Decimal(fila["delta_pct"])) <= Decimal("15.0")
            assert Decimal(fila["precio_independiente"]) > 0
            assert fila["codigo_independiente"]


def test_la_cola_de_pendientes_cubre_lo_no_confirmado(verificacion):
    pendientes = {f["codigo_recurso"] for f in leer(verificador.PENDIENTES)}
    confirmados = {c for c, f in verificacion.items()
                   if f["veredicto"] in {"ya_confirmado", "confirmado_independiente"}}
    assert pendientes == set(verificacion) - confirmados
    # 371 ya_confirmado + 1 confirmado_independiente en el archivo de
    # verificacion. Los 3 recursos confirmados en el registro pero clasificados
    # como solo_fuente_propia o divergencia_verificada en la verificacion son:
    # MT-ANCLA-PIEDRA, MT-BREAKER, MT-PYL-PASTA (fuente comercial o divergencia
    # verificada, no banco independiente). La cola tiene 19 recursos pendientes.
    assert len(confirmados) == 371
    assert len(pendientes) == 19
    for fila in leer(verificador.PENDIENTES):
        assert fila["que_falta"] and fila["esfuerzo"] in {"alta", "media", "baja"}
    usos = [int(f["usos"]) for f in leer(verificador.PENDIENTES) if f["esfuerzo"] == "alta"]
    assert usos == sorted(usos, reverse=True)


def test_confirmaciones_aplicadas_son_coherentes_con_el_registro(registro):
    filas = leer(confirmador.CONFIRMACIONES)
    assert len(filas) == 321
    for fila in filas:
        recurso = registro[fila["codigo_recurso"]]
        assert recurso["estado_auditoria"] == "confirmado_referencia"
        assert confirmador.MARCA in recurso["evidencia_y_pendientes"]
        assert fila["fuente"] and fila["codigo_fuente"]
        delta = Decimal(fila["precio"]) / Decimal(recurso["precio_revisado"]) - 1
        assert abs(delta) <= Decimal("0.15")


def test_valida_estado_banda_y_duplicados(registro):
    fila = leer(confirmador.CONFIRMACIONES)[0]
    en_revision = {c: dict(r) for c, r in registro.items()
                   if r["estado_auditoria"] == "en_revision" and r["precio_revisado"]}
    codigo = next(iter(en_revision))
    # Fuera de la banda del 15 %: se rechaza.
    revisado = Decimal(en_revision[codigo]["precio_revisado"])
    fuera = dict(fila, codigo_recurso=codigo, precio=str(revisado * 2))
    with pytest.raises(ValueError, match="15"):
        confirmador.validar([fuera], en_revision)
    # Confirmar algo que no está en revisión por este lote: se rechaza.
    confirmado = next(c for c, r in registro.items()
                      if r["estado_auditoria"] == "confirmado_referencia"
                      and confirmador.MARCA not in r["evidencia_y_pendientes"])
    with pytest.raises(ValueError, match="en revisión"):
        confirmador.validar([dict(fila, codigo_recurso=confirmado)], registro)
    # Duplicados y códigos inexistentes.
    with pytest.raises(ValueError, match="duplicado"):
        confirmador.validar([fila, dict(fila)], registro)
    with pytest.raises(ValueError, match="inexistente"):
        confirmador.validar([dict(fila, codigo_recurso="NO-EXISTE")], registro)


def test_aplicar_es_idempotente(registro):
    filas = leer(confirmador.CONFIRMACIONES)
    copia = {c: dict(r) for c, r in registro.items()}
    # Sobre un registro ya confirmado por este lote no hay nada que rehacer.
    orden, cambios = confirmador.aplicar(filas, copia)
    assert cambios == []
    assert orden == [registro[c] for c in sorted(registro)]
    # Y sobre un recurso en revisión la marca se escribe una sola vez.
    en_revision = {c: dict(r) for c, r in registro.items()
                   if r["estado_auditoria"] == "en_revision" and r["precio_revisado"]}
    codigo = next(iter(en_revision))
    fila = dict(filas[0], codigo_recurso=codigo,
                precio=en_revision[codigo]["precio_revisado"])
    primero = confirmador.aplicar([fila], en_revision)
    segundo = confirmador.aplicar([fila], {c: dict(r) for c, r in en_revision.items()})
    assert primero[0] == segundo[0]
    for recurso in primero[0]:
        assert recurso["evidencia_y_pendientes"].count(confirmador.MARCA) <= 1
