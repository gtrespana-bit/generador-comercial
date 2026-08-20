from types import SimpleNamespace

from app.services.cambios_presupuesto import comparar_snapshot_con_actual


def _snap(total=100, partidas=None):
    return {
        "numero": "P-1",
        "moneda": "USD",
        "cliente": {"nombre": "Juan"},
        "totales": {"total": total},
        "capitulos": [{"nombre": "OBRA", "partidas": partidas or []}],
    }


def _item(nombre, cantidad=1, precio=10, codigo=""):
    return {
        "codigo_externo": codigo,
        "nombre": nombre,
        "unidad": "ud",
        "cantidad_total": cantidad,
        "precio_unitario": precio,
        "importe": cantidad * precio,
    }


def test_detecta_partidas_anadidas_eliminadas_y_modificadas():
    anterior = _snap(100, [_item("Demolición", 1, 50, "A"), _item("Mampara", 1, 50, "B")])
    actual = _snap(130, [_item("Demolición", 2, 55, "A"), _item("Pintura", 1, 20, "C")])

    res = comparar_snapshot_con_actual(anterior, actual, version_numero=1)

    assert res["hay_cambios"] is True
    assert res["diferencia"] == 30
    assert [x["nombre"] for x in res["añadidas"]] == ["Pintura"]
    assert [x["nombre"] for x in res["eliminadas"]] == ["Mampara"]
    assert res["modificadas"][0]["nombre"] == "Demolición"
    campos = {c["campo"] for c in res["modificadas"][0]["cambios"]}
    assert campos == {"cantidad", "precio"}
    assert "Total anterior: 100,00 USD" in res["texto"]
    assert "Nuevo total: 130,00 USD" in res["texto"]
    assert "Adjunto el PDF actualizado." in res["texto"]


def test_no_muestra_cambios_si_snapshot_es_igual():
    anterior = _snap(100, [_item("Demolición", 1, 100, "A")])
    actual = _snap(100, [_item("Demolición", 1, 100, "A")])

    res = comparar_snapshot_con_actual(anterior, actual)

    assert res["hay_cambios"] is False
    assert res["texto"] == ""
