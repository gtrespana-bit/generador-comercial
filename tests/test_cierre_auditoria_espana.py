"""Cierre de la auditoría de precios de España: validación y trazabilidad."""
import csv
import json
from decimal import Decimal
from pathlib import Path

import pytest

from tools import cerrar_auditoria_espana as cierre
from tools import cribar_precios_espana as cribador
from tools import generar_matriz_precios_espana as generador

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/auditoria_precios"
FECHA = "2026-11-07"


def leer(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as manejador:
        return list(csv.DictReader(manejador, delimiter=";"))


def cotizados_despues_del_cierre() -> set[str]:
    """Recursos cuyo precio ya manda un registro posterior al cierre del 7.

    El cierre del 7 de noviembre es historia: describe con qué evidencia se
    cerró cada recurso ese día. El 8 de noviembre se abrió el registro de
    cotizaciones reales, que tiene prioridad en el generador de la matriz. Un
    recurso que aparece en él ya no tiene que coincidir con el libro del
    cierre, y la prueba no debe exigírselo: lo que sí se comprueba, en
    `test_cotizaciones_espana.py`, es que la matriz y ese registro digan lo
    mismo.
    """
    registro = DOC / "espana_decision_cotizaciones_2026-11-08.csv"
    return {f["codigo_recurso"] for f in leer(registro)}


@pytest.fixture(scope="module")
def datos():
    registro = {r["codigo_recurso"]: r for r in leer(cierre.REGISTRO)}
    matriz = {r["codigo_recurso"]: r for r in leer(cierre.MATRIZ) if r["pais_codigo"] == "ES"}
    adjudicacion = leer(cierre.ADJUDICACION)
    libro = {r["codigo_recurso"]: r for r in leer(cierre.LIBRO)}
    referencias = {r["codigo_recurso"]: r for r in leer(cierre.REFERENCIAS)}
    return registro, matriz, adjudicacion, libro, referencias


def test_adjudicacion_valida_y_completa(datos):
    registro, matriz, adjudicacion, _, _ = datos
    cierre.validar(adjudicacion, registro, matriz)
    pendientes = {c for c, r in registro.items() if r["estado_auditoria"] == "pendiente"}
    assert not pendientes, "el cierre no deja recursos pendientes"
    for fila in adjudicacion:
        if fila["decision"] in cierre.APLICA:
            assert Decimal(fila["precio_adoptado"]) > 0
            assert fila["fuente"].strip() and fila["criterio"].strip()
        if fila["decision"] in cierre.CONFIRMA:
            previo = Decimal(fila["precio_revisado_previo"])
            assert abs(Decimal(fila["precio_fuente"]) / previo - 1) <= cierre.TOLERANCIA_CONFIRMA


def test_libro_coincide_con_registro_y_matriz(datos):
    registro, matriz, adjudicacion, libro, _ = datos
    assert len(libro) == len(adjudicacion)
    for codigo, fila in libro.items():
        # El libro fija el estado del cierre; una confirmación posterior (con su
        # marca en el registro) solo puede haberlo elevado a confirmado.
        if fila["estado_final"] != registro[codigo]["estado_auditoria"]:
            assert registro[codigo]["estado_auditoria"] == "confirmado_referencia"
            assert "Confirmación 2026-11-07" in registro[codigo]["evidencia_y_pendientes"]
        assert fila["fecha_revision"] == FECHA
        if codigo in cotizados_despues_del_cierre():
            # Precio posterior, con su propia evidencia y su propia prueba.
            continue
        assert Decimal(fila["precio_final"]) == Decimal(matriz[codigo]["precio_referencia"])
        assert cierre.MARCA in registro[codigo]["evidencia_y_pendientes"]
        if fila["decision"] in cierre.APLICA:
            assert Decimal(registro[codigo]["precio_revisado"]) == Decimal(fila["precio_final"])
            assert fila["fuente"] in registro[codigo]["fuente_observada"]
        if fila["decision"] == "confirmar_referencia":
            assert registro[codigo]["estado_auditoria"] == "confirmado_referencia"


def test_las_referencias_aceptadas_alimentan_el_generador(datos):
    _, matriz, _, libro, referencias = datos
    generadas = generador.referencias_cierre_2026_11_07()
    assert set(generadas) == set(referencias)
    posteriores = cotizados_despues_del_cierre() & set(generadas)
    assert posteriores, "el registro posterior debe tener su capa propia"
    for codigo, dado in generadas.items():
        precio = Decimal(referencias[codigo]["precio"])
        if codigo in posteriores:
            # El generador aplica primero el cierre y después la cotización, así
            # que la matriz ya no se atribuye a la revisión del 7 de noviembre:
            # la fuente es la oferta publicada, aunque el precio no cambie.
            assert matriz[codigo]["fuente"] != generador.REVISION_CIERRE
            continue
        assert Decimal(str(dado["ES"].precio)) == precio
        assert Decimal(matriz[codigo]["precio_referencia"]) == precio
        assert matriz[codigo]["fuente"] == generador.REVISION_CIERRE
        assert libro[codigo]["decision"] in cierre.APLICA


def test_el_cierre_es_idempotente(datos):
    registro, matriz, adjudicacion, _, _ = datos
    primera = cierre.aplicar(adjudicacion, {c: dict(r) for c, r in registro.items()},
                             {c: dict(r) for c, r in matriz.items()})
    segunda = cierre.aplicar(adjudicacion, {c: dict(r) for c, r in registro.items()},
                             {c: dict(r) for c, r in matriz.items()})
    assert primera == segunda
    # Sobre el registro ya cerrado no se duplican marcas ni fuentes.
    tercera = cierre.aplicar(adjudicacion, {c: dict(r) for c, r in registro.items()},
                             {c: dict(r) for c, r in matriz.items()})
    assert primera == tercera
    for referencia in primera[0]:
        codigo = referencia["codigo_recurso"]
        assert registro[codigo]["fuente_observada"].count(referencia["fuente"]) == 1


def test_rechaza_decisiones_invalidas(datos):
    registro, matriz, adjudicacion, _, _ = datos
    base = dict(adjudicacion[0])
    casos = [
        dict(base, decision="inventada"),
        dict(base, decision="aplicar_media_dos_bancos", precio_adoptado=""),
        dict(base, decision="aplicar_media_dos_bancos", precio_adoptado="0"),
    ]
    for caso in casos:
        with pytest.raises(ValueError):
            cierre.validar([caso], registro, matriz)
    with pytest.raises(ValueError):
        cierre.validar([base, dict(base)], registro, matriz)
    # Sin decisión para un recurso no confirmado, el cierre está incompleto.
    # El registro ya no deja ninguno en revisión (el cierre confirmó los 390),
    # así que ese estado se prepara sobre una copia de un recurso real.
    en_revision = {c: dict(r) for c, r in registro.items()}
    codigo = next(iter(en_revision))
    en_revision[codigo]["estado_auditoria"] = "en_revision"
    sin_decision = [f for f in adjudicacion if f["codigo_recurso"] != codigo]
    with pytest.raises(ValueError, match="sin decisión"):
        cierre.validar(sin_decision, en_revision, matriz)


def test_confirmacion_fuera_de_banda_se_rechaza(datos):
    registro, matriz, adjudicacion, _, _ = datos
    # Fila sintética para probar rechazo de confirmación fuera de banda,
    # construida sobre un recurso real de materiales con unidad ud.
    ref = next(r for r in registro.values()
               if r["categoria"] == "materiales" and r["unidad"] == "ud")
    base = {
        "codigo_recurso": ref["codigo_recurso"],
        "categoria": ref["categoria"],
        "unidad": ref["unidad"],
        "usos": ref["partidas_que_lo_usan"],
        "estado_previo": "en_revision",
        "precio_matriz": ref["precio_revisado"],
        "precio_revisado_previo": ref["precio_revisado"],
        "decision": "confirmar_referencia",
        "precio_adoptado": "",
        "precio_fuente": "20.00",
        "fuente": "extremadura",
        "codigo_fuente": "P01XXXX",
        "edicion_fecha": "2026",
        "desviacion_pct": "+100.0",
        "criterio": "Prueba de rechazo fuera de banda",
        "reserva": "",
    }
    fuera = dict(base, precio_fuente=str(Decimal(base["precio_revisado_previo"]) * 2))
    with pytest.raises(ValueError, match="banda"):
        cierre.validar([fuera], registro, matriz)


def test_cribado_filtra_y_ordena_por_precision(tmp_path):
    precio = {"currency": "EUR", "date": "2022-12", "edition": "2024-01", "source": "bcca",
              "scope": {"country": "ES", "region": "AND"}, "value": 5.43}

    def item(**cambios):
        base = {"kind": "material", "unit": "m2", "summary": "PLACA DE YESO LAMINADO DE 15 mm",
                "text": "", "bom": [], "prices": [dict(precio, sourceCode="FP01300")]}
        base.update(cambios)
        return base

    archivo = tmp_path / "basicos.json"
    archivo.write_text(json.dumps({"version": "prueba", "items": [
        item(),
        item(prices=[dict(precio, sourceCode="OTRO", source="cype")]),
        item(prices=[dict(precio, sourceCode="DUP")] * 2),
        item(summary="PLACA DE YESO LAMINADO DE 10 mm",
             prices=[dict(precio, sourceCode="FP01100", value=4.58)]),
        item(kind="auxiliary"),
        item(unit="t"),
    ]}), encoding="utf-8")
    precios, sha, version = cribador.cargar_basicos(archivo)
    assert version == "prueba" and len(sha) == 64
    assert sorted(p["codigo"] for p in precios) == ["FP01100", "FP01300"]
    recursos = [{"codigo_recurso": "MT-PYL-PLACA", "categoria": "materiales", "unidad": "m2",
                 "descripcion": "Placa de yeso laminado estándar de 15 mm", "partidas_que_lo_usan": "4",
                 "estado_auditoria": "en_revision"}]
    filas = cribador.cribar(recursos, precios, {"MT-PYL-PLACA": "3.49"})
    assert [f["codigo_fuente"] for f in filas] == ["FP01300", "FP01100"]
    assert filas[0]["numeros_compatibles"] == "si"
    assert Decimal(filas[0]["ratio"]) > Decimal("1.5")
    # El candidato de 10 mm no comparte los números del recurso.
    assert filas[1]["numeros_compatibles"] == "no"
    recursos[0]["descripcion"] = "Placa de yeso laminado de 10 mm"
    filas = cribador.cribar(recursos, precios, {"MT-PYL-PLACA": "3.49"})
    assert filas[0]["codigo_fuente"] == "FP01100" and filas[0]["numeros_compatibles"] == "si"
    recursos[0]["descripcion"] = "Tornillo autoperforante"
    filas = cribador.cribar(recursos, precios, {"MT-PYL-PLACA": "3.49"})
    assert filas[0]["alerta"] == "sin_candidato"


def test_cribado_publicado_cubre_el_catalogo():
    filas = leer(DOC / "espana_cribado_bcca_2026-11-07.csv")
    codigos = {f["codigo_recurso"] for f in filas}
    assert len(codigos) == 390
    assert set(filas[0]) == {
        "codigo_recurso", "categoria", "unidad", "usos", "estado_auditoria", "precio_matriz",
        "rango", "codigo_fuente", "descripcion_fuente", "precio_fuente", "edicion_fuente",
        "fecha_precio", "precision", "cobertura", "numeros_compatibles", "ratio", "alerta"}
    fuentes = {f["edicion_fuente"] for f in filas if f["codigo_fuente"]}
    assert fuentes == {"2024-01"}
    for fila in filas:
        if fila["codigo_fuente"]:
            assert Decimal(fila["precision"]) <= 1 and Decimal(fila["cobertura"]) <= 1
            assert fila["numeros_compatibles"] in {"si", "no"}


def test_impacto_recalcula_la_cascada_de_la_aplicacion():
    from tools import analizar_impacto_precios_espana as impacto

    fichas = {
        "MO-OF1-ELE": {"grupo": "mano_obra", "precio": 1.0},
        "MT-CABLE": {"grupo": "materiales", "precio": 1.0},
        "MT-COMP": {"grupo": "materiales", "composicion": [
            {"ref": "MT-CABLE", "cantidad": 2}, {"ref": "MO-OF1-ELE", "cantidad": 1}]},
    }
    partida = {"codigo": "X", "recursos": [
        {"ref": "MO-OF1-ELE", "rendimiento": 2}, {"ref": "MT-COMP", "rendimiento": 1}],
        "complementarios_pct": 10}
    anterior = {"MO-OF1-ELE": (20.0, "EUR"), "MT-CABLE": (3.0, "EUR")}
    actual = {"MO-OF1-ELE": (23.18, "EUR"), "MT-CABLE": (3.0, "EUR")}
    # 2 × 20 + (2 × 3 + 20) = 66; +10 % de complementarios = 72,60
    assert impacto.coste(partida, fichas, anterior) == pytest.approx(72.60)
    # 2 × 23,18 + (2 × 3 + 23,18) = 75,54; +10 % = 83,094
    assert impacto.coste(partida, fichas, actual) == pytest.approx(83.09)
    # Un recurso sin precio en la matriz y sin ficha no rompe el cálculo.
    assert impacto.coste({"codigo": "Y", "recursos": []}, fichas, actual) is None


def test_el_impacto_publicado_es_coherente():
    from tools import analizar_impacto_precios_espana as impacto

    filas = leer(DOC / "espana_impacto_partidas_2026-11-07.csv")
    partidas = {ruta.stem for ruta in impacto.DESCOMPUESTOS.glob("*.json")}
    assert len(filas) == len(partidas) == 3008
    assert len({f["codigo_partida"] for f in filas}) == len(filas)
    movidas = [f for f in filas if Decimal(f["delta_pct"] or "0") != 0]
    assert len(movidas) == 1452
    for fila in movidas:
        assert fila["recursos_afectados"]
        assert Decimal(fila["coste_actual"]) == (Decimal(fila["coste_anterior"])
                                                 + Decimal(fila["delta_eur"]))
