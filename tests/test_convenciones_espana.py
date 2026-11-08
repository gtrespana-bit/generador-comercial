"""Convención de medida típica: la política aplicada y su trazabilidad."""
import csv
from decimal import Decimal
from pathlib import Path

from tools import adjudicar_convenciones_espana as convenciones

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/auditoria_precios"


def leer(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def fila(**cambios):
    base = {"codigo_recurso": "MT-PRUEBA", "unidad": "ud", "usos": "10",
            "especificacion_convencional": "Caja 100x100",
            "criterio_convencion": "medida más frecuente",
            "estado": "adoptado_banco", "codigo_fuente": "P15GK010",
            "descripcion_fuente": "Caja registro", "precio_fuente": "1.02",
            "motivo_pendiente": ""}
    base.update(cambios)
    return base


def adjudicacion(**cambios):
    base = {"codigo_recurso": "MT-PRUEBA", "usos": "10", "precio_matriz": "1.253165",
            "decision": "agregado_heterogeneo", "precio_adoptado": "", "precio_fuente": "",
            "fuente": "", "codigo_fuente": "", "edicion_fecha": "", "desviacion_pct": "",
            "criterio": "", "reserva": ""}
    base.update(cambios)
    return base


def test_la_convencion_adoptada_lleva_precio_ficha_y_criterio():
    salida, _ = convenciones.construir([fila()], [adjudicacion()])
    adoptada = salida[0]
    assert adoptada["decision"] == "aplicar_fuente_unica_coherente"
    assert adoptada["precio_adoptado"] == "1.02"
    assert adoptada["codigo_fuente"] == "P15GK010"
    assert "Caja 100x100" in adoptada["criterio"]
    assert "convención" in adoptada["reserva"].lower()


def test_lo_pendiente_no_adopta_precio():
    salida, _ = convenciones.construir([fila(estado="pendiente_cotizacion")],
                                      [adjudicacion()])
    assert salida[0]["precio_adoptado"] == ""
    assert salida[0]["decision"] == "agregado_heterogeneo"


def test_un_salto_grande_se_avisa():
    _, avisos = convenciones.construir([fila()], [adjudicacion(precio_matriz="0.50")])
    assert avisos and "104.0" in avisos[0]


def test_un_salto_pequeno_no_genera_aviso():
    _, avisos = convenciones.construir([fila()], [adjudicacion(precio_matriz="1.00")])
    assert not avisos


def test_la_tabla_de_convenciones_cubre_los_recursos_sin_medida():
    tabla = leer(convenciones.CONVENCIONES)
    assert len(tabla) == 56
    assert len({f["codigo_recurso"] for f in tabla}) == 56
    # Toda fila tiene una especificación escrita: no hay recursos «sin decidir».
    assert all(f["especificacion_convencional"].strip() for f in tabla)
    assert all(f["criterio_convencion"].strip() for f in tabla)


def test_lo_adoptado_esta_en_el_registro_con_su_ficha():
    tabla = {f["codigo_recurso"]: f for f in leer(convenciones.CONVENCIONES)
             if f["estado"] == "adoptado_banco"}
    registro = {f["codigo_recurso"]: f
                for f in leer(DOC / "espana_2026-11-06.csv")}
    for codigo, ficha in tabla.items():
        assert Decimal(registro[codigo]["precio_revisado"]) == Decimal(ficha["precio_fuente"])
        assert ficha["codigo_fuente"] in registro[codigo]["codigo_fuente"]
        assert "convención" in registro[codigo]["criterio_revisado"].lower()


def test_lo_pendiente_sigue_sin_precio_revisado():
    tabla = [f for f in leer(convenciones.CONVENCIONES)
             if f["estado"] == "pendiente_cotizacion"]
    registro = {f["codigo_recurso"]: f
                for f in leer(DOC / "espana_2026-11-06.csv")}
    for ficha in tabla:
        assert not registro[ficha["codigo_recurso"]]["precio_revisado"].strip()
        assert ficha["motivo_pendiente"].strip()
