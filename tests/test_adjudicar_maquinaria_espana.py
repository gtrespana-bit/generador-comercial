"""Adjudicación de maquinaria: el modelo se convierte en precio trazado."""
from decimal import Decimal

from tools import adjudicar_maquinaria_espana as adjudicar


def parametro(**cambios):
    fila = {"codigo_recurso": "MQ-PRUEBA", "precio_adquisicion_sin_iva_eur": "100",
            "fuente_precio": "Tienda X", "potencia_kw": "1", "vida_util_h": "500",
            "tasa_mantenimiento": "0.15", "factor_carga": "0.6",
            "consumibles_eur_h": "0.10", "consumibles_detalle": "discos"}
    fila.update(cambios)
    return fila


def propuesta(coste="0.45"):
    return {"codigo_recurso": "MQ-PRUEBA", "vida_util_h": "500", "coste_h": coste,
            "coste_vida_mitad": "0.85", "coste_vida_doble": "0.28"}


def adjudicacion(precio_matriz="1.00", codigo="MQ-PRUEBA"):
    return {"codigo_recurso": codigo, "usos": "10", "precio_matriz": precio_matriz,
            "decision": "requiere_modelo_propio", "precio_adoptado": "",
            "precio_fuente": "", "fuente": "", "codigo_fuente": "",
            "edicion_fecha": "", "desviacion_pct": "", "criterio": "", "reserva": ""}


def test_la_maquina_con_coste_entra_como_fuente_unica():
    salida, avisos = adjudicar.construir([parametro()], [propuesta()], [adjudicacion()])
    fila = salida[0]
    assert fila["decision"] == "aplicar_fuente_unica_coherente"
    assert fila["precio_adoptado"] == "0.45"
    assert fila["codigo_fuente"] == adjudicar.CODIGO_FUENTE
    assert fila["desviacion_pct"] == "-55.0"
    assert "100 EUR sin IVA" in fila["criterio"]
    assert avisos  # un -55 % se avisa, no se aplica en silencio


def test_la_maquina_sin_coste_no_se_toca():
    salida, _ = adjudicar.construir([parametro()], [propuesta(coste="")],
                                    [adjudicacion()])
    assert salida[0]["decision"] == "requiere_modelo_propio"
    assert not salida[0]["precio_adoptado"]


def test_los_recursos_ajenos_a_la_tabla_pasan_intactos():
    otra = adjudicacion(codigo="MT-CEMENTO")
    salida, _ = adjudicar.construir([parametro()], [propuesta()], [otra])
    assert salida[0] is otra


def test_el_precio_se_redondea_a_centimos():
    salida, _ = adjudicar.construir([parametro()], [propuesta(coste="0.445")],
                                    [adjudicacion()])
    assert salida[0]["precio_adoptado"] == "0.45"
    salida, _ = adjudicar.construir([parametro()], [propuesta(coste="0.444")],
                                    [adjudicacion()])
    assert salida[0]["precio_adoptado"] == "0.44"


def test_un_cambio_pequeno_no_genera_aviso():
    _, avisos = adjudicar.construir([parametro()], [propuesta(coste="0.45")],
                                    [adjudicacion(precio_matriz="0.44")])
    assert not avisos
