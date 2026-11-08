"""Identidad del artículo: sinónimos, ficha forzada y huecos clasificados."""
import csv
from decimal import Decimal
from pathlib import Path

import pytest

from tools import auditar_huecos_identidad_espana as auditor
from tools import cerrar_auditoria_espana as cierre
from tools import cribar_precios_espana as cribador
from tools import verificar_precios_espana as verificador

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/auditoria_precios"


def leer(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as manejador:
        return list(csv.DictReader(manejador, delimiter=";"))


def test_los_sinonimos_colapsan_la_misma_familia_de_articulo():
    literal = cribador.tokens("Tornillería estructural de alta resistencia")
    con_sinonimos = cribador.tokens("Tornillería estructural de alta resistencia", True)
    assert "tornilleria" in literal and "tornillo" not in literal
    assert "tornillo" in con_sinonimos
    assert "hormigon" in cribador.tokens("Concreto premezclado", True)
    assert "sierra" in cribador.tokens("Motosierra eléctrica", True)


def test_el_cribado_con_sinonimos_recupera_la_ficha_que_el_nucleo_literal_pierde():
    precios = [
        {"codigo": "P04FAV050", "categoria": "materiales", "unidad": "ud",
         "descripcion": "Tornilleria", "precio": Decimal("1.13"), "edicion": "2026",
         "fecha": "2026", "region": "EX",
         "tokens": {"tornilleria"}},
        {"codigo": "P01UT040", "categoria": "materiales", "unidad": "ud",
         "descripcion": "Tornillo 6,8 cincado + arandela + tuerca autoblocante",
         "precio": Decimal("3.69"), "edicion": "2026", "fecha": "2026", "region": "EX",
         "tokens": {"tornillo", "6", "8", "cincado", "arandela", "tuerca", "autoblocante"}},
    ]
    recursos = [{"codigo_recurso": "MT-TORNILLO-EST", "categoria": "materiales",
                 "unidad": "ud", "partidas_que_lo_usan": "17", "estado_auditoria": "en_revision",
                 "descripcion": "Tornillería estructural de alta resistencia con tuerca y arandelas."}]
    matriz = {"MT-TORNILLO-EST": "7.80"}
    literal = cribador.cribar(recursos, precios, matriz)
    con_sinonimos = cribador.cribar(recursos, precios, matriz, sinonimos=True)
    # El token literal del núcleo ("tornilleria") solo alcanza la ficha genérica.
    assert {f["codigo_fuente"] for f in literal if f["codigo_fuente"]} == {"P04FAV050"}
    # Con sinónimos, la ficha del tornillo estructural entra en la tabla.
    codigos = {f["codigo_fuente"] for f in con_sinonimos if f["codigo_fuente"]}
    assert "P01UT040" in codigos


def test_la_confirmacion_posterior_sobrevive_a_reaplicar_el_cierre():
    texto = ("Cierre 2026-11-07: se adopta el punto operativo. Reserva: sin porte. "
             "Confirmación 2026-11-07: verificación cruzada con el banco (+5,0 %).")
    limpio = cierre.limpiar_marca(texto, cierre.MARCA)
    assert "se adopta el punto operativo" not in limpio
    assert "Confirmación 2026-11-07" in limpio


def test_adoptar_precio_no_degrada_un_recurso_confirmado():
    registro = {"MT-X": {"codigo_recurso": "MT-X", "categoria": "materiales", "unidad": "ud",
                         "usos": "1", "partidas_que_lo_usan": "1",
                         "estado_auditoria": "confirmado_referencia",
                         "precio_revisado": "1.00", "fuente_observada": "",
                         "codigo_fuente": "", "edicion_fuente": "", "ambito_fuente": "",
                         "criterio_revisado": "", "evidencia_y_pendientes": ""}}
    matriz = {"MT-X": {"precio_referencia": Decimal("1.00")}}
    fila = {"codigo_recurso": "MT-X", "categoria": "materiales", "unidad": "ud", "usos": "1",
            "estado_previo": "confirmado_referencia", "precio_matriz": "1.00",
            "precio_revisado_previo": "1.00", "decision": "aplicar_fuente_unica_coherente",
            "precio_adoptado": "1.00", "precio_fuente": "1.00", "fuente": "Guía comercial",
            "codigo_fuente": "G1", "edicion_fecha": "2026", "desviacion_pct": "0.0",
            "criterio": "Precio adoptado.", "reserva": "Sin porte."}
    _, libro = cierre.aplicar([fila], registro, matriz)
    assert libro[0]["estado_final"] == "confirmado_referencia"


def test_la_identidad_forzada_elige_la_ficha_del_mismo_articulo():
    correcciones = verificador.revisiones_manuales()
    assert correcciones["MT-EXTINTOR"]["codigo_elegido"] == "P23FJ020"
    verificacion = {f["codigo_recurso"]: f for f in leer(verificador.SALIDA)}
    # El extintor de 6 kg del recurso, no el de 50 kg que elegía el parecido.
    assert verificacion["MT-EXTINTOR"]["codigo_independiente"] == "P23FJ020"
    assert verificacion["MT-EXTINTOR"]["veredicto"] == "divergencia_verificada"
    # Un anclaje genérico no acredita la pieza de piedra: no se inventa contraste.
    assert verificacion["MT-ANCLA-PIEDRA"]["veredicto"] == "solo_fuente_propia"


def test_el_concreto_se_confirma_por_clase_de_resistencia_sin_cambiar_el_precio():
    verificacion = {f["codigo_recurso"]: f for f in leer(verificador.SALIDA)}
    registro = {f["codigo_recurso"]: f for f in leer(DOC / "espana_2026-11-06.csv")}
    for codigo, ficha in (("MT-CONC-180", "P01HCM003"), ("MT-CONC-210", "P01HCA300"),
                          ("MT-CONC-250", "P01HCA300"), ("MT-CONC-300", "P01HCA320")):
        assert registro[codigo]["estado_auditoria"] == "confirmado_referencia"
        assert ficha in registro[codigo]["fuente_observada"]
        assert verificacion[codigo]["veredicto"] == "ya_confirmado"
    # El precio propio (con puesta en obra) no se sustituye por el de central.
    assert Decimal(registro["MT-CONC-210"]["precio_revisado"]) == Decimal("100.00")


def test_la_tabla_de_huecos_se_reproduce_y_cubre_todos_los_recursos_sin_precio():
    publicada = leer(auditor.SALIDA)
    assert len(publicada) == 133
    assert len({f["codigo_recurso"] for f in publicada}) == 133
    registro = {f["codigo_recurso"]: f for f in leer(DOC / "espana_2026-11-06.csv")}
    sin_precio = {c for c, f in registro.items() if not f["precio_revisado"].strip()}
    assert {f["codigo_recurso"] for f in publicada} == sin_precio
    etiquetas = {f["diagnostico"] for f in publicada}
    assert etiquetas <= {"equivalente_en_la_base", "misma_familia_sin_medida",
                         "solo_parecido_de_nombre", "agregado_por_componentes",
                         "sin_candidato"}
    # Un recurso agregado nunca se etiqueta como artículo único.
    assert all(f["diagnostico"] != "equivalente_en_la_base"
               for f in publicada if f["descripcion_recurso"].lower().startswith(
                   "consumibles de"))


@pytest.mark.parametrize("codigo", ["MQ-ANDAMIO", "MQ-CIZALLA", "MT-CONS-DEM"])
def test_los_huecos_de_alta_frecuencia_estan_clasificados(codigo):
    filas = {f["codigo_recurso"]: f for f in leer(auditor.SALIDA)}
    assert codigo in filas
    assert filas[codigo]["diagnostico"] != "equivalente_en_la_base"
    assert filas[codigo]["motivo"]
