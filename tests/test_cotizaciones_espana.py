"""Cotizaciones reales de España (lotes 1, 2 y 3): registro, matriz y SQL dicen lo mismo.

El 7 de noviembre los 54 recursos sin ficha de banco se quedaron con el precio
derivado de la matriz. Los tres lotes empiezan a sustituirlos por ofertas publicadas
y comprobadas, con banco donde el banco tiene el artículo. Las pruebas atan las tres piezas para que ninguna se mueva sola:
el registro de decisiones, la matriz de carga y el SQL acotado que se ejecuta en
producción.
"""
import csv
import re
from decimal import Decimal
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
DOC = RAIZ / "docs/auditoria_precios"
FECHA = "2026-11-08"
DECISIONES = DOC / f"espana_decision_cotizaciones_{FECHA}.csv"
OFERTAS = DOC / f"espana_cotizaciones_{FECHA}.csv"
MATRIZ = RAIZ / "basedatos_partidas/salida/precios_recursos_espana.csv"
SQL = DOC / f"cotizaciones_es_{FECHA}.sql"


def leer(ruta: Path) -> list[dict[str, str]]:
    with ruta.open(encoding="utf-8-sig", newline="") as manejador:
        return list(csv.DictReader(manejador, delimiter=";"))


def decisiones() -> dict[str, dict[str, str]]:
    return {f["codigo_recurso"]: f for f in leer(DECISIONES)}


def matriz() -> dict[str, dict[str, str]]:
    return {f["codigo_recurso"]: f for f in leer(MATRIZ)}


def test_el_registro_cotiza_recursos_que_existen_en_la_matriz_espanola():
    registro, catalogo = decisiones(), matriz()
    assert len(registro) == 12
    assert set(registro) <= set(catalogo)
    for codigo, fila in registro.items():
        assert catalogo[codigo]["pais_codigo"] == "ES"
        assert catalogo[codigo]["moneda"] == "EUR"
        assert fila["metodo"] in {"cotizacion_directa", "banco_y_minorista", "banco"}
        assert fila["confianza"] in {"alta", "media", "baja", "referencia", "derivado"}


def test_cada_cotizacion_tiene_banda_coherente_y_precio_positivo():
    for codigo, fila in decisiones().items():
        precio = Decimal(fila["precio"])
        bajo = Decimal(fila["precio_min"])
        alto = Decimal(fila["precio_max"])
        assert precio > 0, codigo
        assert 0 < bajo <= precio <= alto, codigo


def test_la_matriz_publica_la_cotizacion_no_el_valor_derivado():
    catalogo = matriz()
    for codigo, fila in decisiones().items():
        publicada = catalogo[codigo]
        assert Decimal(publicada["precio_referencia"]) == Decimal(fila["precio"]), codigo
        assert Decimal(publicada["precio_min"]) == Decimal(fila["precio_min"]), codigo
        assert Decimal(publicada["precio_max"]) == Decimal(fila["precio_max"]), codigo
        assert publicada["fuente"] == fila["fuente"], codigo
        assert publicada["confianza"] == fila["confianza"], codigo
        assert publicada["fecha_consulta"] == FECHA, codigo
        # Ninguna cotización entra con IVA: la tabla guarda precio de coste.
        assert publicada["incluye_iva"] == "no", codigo
        assert "Cotización real contrastada" in publicada["observaciones"], codigo


def test_el_sql_solo_toca_las_referencias_nacionales_de_esos_recursos():
    texto = SQL.read_text(encoding="utf-8")
    codigos = set(decisiones())
    actualizados = re.findall(r"WHERE codigo_recurso = '([^']+)'", texto)
    assert set(actualizados) == codigos
    assert len(actualizados) == len(codigos), "un UPDATE por recurso, sin duplicados"
    # Cada bloque acota país y excluye overrides de empresas.
    bloques = texto.split("UPDATE public.precios_recursos_mercado")[1:]
    assert len(bloques) == len(codigos)
    for bloque in bloques:
        assert "AND pais_codigo = 'ES'" in bloque
        assert "AND organizacion_id IS NULL" in bloque
    assert "BEGIN;" in texto and "COMMIT;" in texto
    # La comprobación final pide exactamente las filas cotizadas.
    assert f"debe devolver {len(codigos)} filas" in texto


def test_cada_decision_se_apoya_en_dos_ofertas_publicadas_con_url():
    ofertas: dict[str, list[dict[str, str]]] = {}
    for fila in leer(OFERTAS):
        ofertas.setdefault(fila["codigo_recurso"], []).append(fila)
    for codigo in decisiones():
        publicadas = ofertas.get(codigo, [])
        assert len(publicadas) >= 2, f"{codigo} sin contraste suficiente"
        for oferta in publicadas:
            assert oferta["url"].startswith("https://"), codigo
            assert oferta["fecha_consulta"] == FECHA, codigo
            assert Decimal(oferta["precio_sin_iva_por_unidad"]) > 0, codigo


def test_la_fuente_y_el_criterio_se_leen_sin_romper_el_csv():
    for codigo, fila in decisiones().items():
        assert fila["fuente"].strip() and fila["criterio"].strip(), codigo
        assert ";" not in fila["fuente"] and ";" not in fila["criterio"], codigo


def test_el_aplicador_rechaza_una_banda_incoherente(tmp_path):
    import importlib.util

    ruta = RAIZ / "tools" / "aplicar_cotizaciones_espana.py"
    especificacion = importlib.util.spec_from_file_location("aplicar_cotizaciones", ruta)
    modulo = importlib.util.module_from_spec(especificacion)
    especificacion.loader.exec_module(modulo)

    buena = {"codigo_recurso": "MT-SOPORTE-AC", "metodo": "cotizacion_directa",
             "precio": "10.98", "precio_min": "7.68", "precio_max": "10.98",
             "confianza": "referencia", "fuente": "x", "criterio": "y"}
    mala = dict(buena, precio="20")
    catalogo = [{"codigo_recurso": "MT-SOPORTE-AC", "pais_codigo": "ES", "moneda": "EUR"}]

    assert "MT-SOPORTE-AC" in modulo.validar([buena], catalogo)
    with pytest.raises(SystemExit):
        modulo.validar([mala], catalogo)
    with pytest.raises(SystemExit):
        modulo.validar([dict(buena, codigo_recurso="MT-NO-EXISTE")], catalogo)
    with pytest.raises(SystemExit):
        modulo.validar([dict(buena, fuente="a;b")], catalogo)


def test_el_lote_2_cotiza_los_tres_recursos_de_mas_uso_que_quedaban():
    """74, 73 y 37 usos: los tres recursos con más partidas detrás."""
    registro = decisiones()
    esperado = {
        # código: (precio adoptado, mínimo, máximo, método)
        "MT-PERFIL-ALUM": ("10.82", "7.54", "14.46", "cotizacion_directa"),
        "MT-SENAL-OBRA": ("9.90", "6.53", "10.74", "cotizacion_directa"),
        "MT-REGUL-GAS": ("15.69", "11.36", "15.69", "banco_y_minorista"),
    }
    for codigo, (precio, minimo, maximo, metodo) in esperado.items():
        fila = registro[codigo]
        assert Decimal(fila["precio"]) == Decimal(precio), codigo
        assert Decimal(fila["precio_min"]) == Decimal(minimo), codigo
        assert Decimal(fila["precio_max"]) == Decimal(maximo), codigo
        assert fila["metodo"] == metodo, codigo
        assert fila["confianza"] == "referencia", codigo


def test_el_lote_2_abre_la_banda_que_repetia_el_precio():
    """Los tres venían con min = precio = max, es decir, sin banda medida."""
    catalogo = matriz()
    for codigo in ("MT-PERFIL-ALUM", "MT-SENAL-OBRA", "MT-REGUL-GAS"):
        fila = catalogo[codigo]
        assert Decimal(fila["precio_min"]) < Decimal(fila["precio_max"]), codigo
        assert "Cotización real contrastada" in fila["observaciones"], codigo


def test_el_perfil_de_aluminio_mantiene_precio_y_gana_evidencia():
    """Dos distribuidores lo enmarcan (7,54-14,46 €/kg): no hay que moverlo."""
    catalogo = matriz()
    fila = catalogo["MT-PERFIL-ALUM"]
    assert Decimal(fila["precio_referencia"]) == Decimal("10.82")
    assert Decimal(fila["precio_min"]) <= Decimal("10.82") <= Decimal(fila["precio_max"])
    ofertas = [o for o in leer(OFERTAS) if o["codigo_recurso"] == "MT-PERFIL-ALUM"]
    assert {o["tienda"] for o in ofertas} >= {"Arialpro", "Proycsa"}


def test_el_lote_3_cotiza_los_cuatro_recursos_de_mas_uso_que_quedaban():
    """17, 17, 13 y 9 usos: los cuatro últimos con partidas detrás."""
    registro = decisiones()
    esperado = {
        # código: (precio adoptado, mínimo, máximo, método)
        "MT-SELLA-PASE": ("9.96", "4.50", "17.20", "cotizacion_directa"),
        "MT-RIEL-CORRED": ("15.95", "5.12", "20.62", "cotizacion_directa"),
        "MT-SAN-FIJA": ("8.90", "5.65", "8.90", "banco_y_minorista"),
        "MT-AISL-REFLECT": ("3.60", "2.32", "4.25", "cotizacion_directa"),
    }
    for codigo, (precio, minimo, maximo, metodo) in esperado.items():
        fila = registro[codigo]
        assert Decimal(fila["precio"]) == Decimal(precio), codigo
        assert Decimal(fila["precio_min"]) == Decimal(minimo), codigo
        assert Decimal(fila["precio_max"]) == Decimal(maximo), codigo
        assert fila["metodo"] == metodo, codigo
        assert fila["confianza"] == "referencia", codigo


def test_el_riel_corredizo_es_el_unico_que_mantiene_precio_en_el_lote_3():
    """El recurso no distingue armario de puerta pesada: la banda lo enmarca."""
    catalogo = matriz()
    fila = catalogo["MT-RIEL-CORRED"]
    assert Decimal(fila["precio_referencia"]) == Decimal("15.95")
    assert Decimal(fila["precio_min"]) == Decimal("5.12")
    assert Decimal(fila["precio_max"]) == Decimal("20.62")
    assert Decimal(fila["precio_min"]) < Decimal("15.95") < Decimal(fila["precio_max"])
    # Los otros tres sí se mueven respecto al derivado del 7 de noviembre.
    for codigo, antes in (("MT-SELLA-PASE", "5.24"), ("MT-SAN-FIJA", "5.47"),
                          ("MT-AISL-REFLECT", "3.65")):
        assert Decimal(catalogo[codigo]["precio_referencia"]) != Decimal(antes), codigo


def test_el_kilo_de_anillo_de_cera_sostiene_el_kit_sanitario():
    """El anillo solo (5,65) ya supera el derivado 5,47: la horquilla era baja."""
    ofertas = [o for o in leer(OFERTAS) if o["codigo_recurso"] == "MT-SAN-FIJA"]
    assert len(ofertas) == 2
    assert {o["tienda"] for o in ofertas} == {"Bricosanitarios", "Banco BCCA 2024-01"}
    anillo = next(o for o in ofertas if o["tienda"] == "Bricosanitarios")
    assert Decimal(anillo["precio_sin_iva_por_unidad"]) > Decimal("5.47")
    decision = decisiones()["MT-SAN-FIJA"]
    assert Decimal(decision["precio"]) == sum(
        Decimal(o["precio_sin_iva_por_unidad"]) for o in ofertas
    ).quantize(Decimal("0.01"))
