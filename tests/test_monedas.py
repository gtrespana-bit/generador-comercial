from app.services.monedas import (
    MONEDA_BASE_CATALOGO,
    MONEDA_COMERCIAL_COTIZAT,
    contexto,
    formato_iso,
    moneda_valida,
)


def test_dominios_comerciales_y_catalogo_son_usd():
    assert MONEDA_COMERCIAL_COTIZAT == "USD"
    assert MONEDA_BASE_CATALOGO == "USD"


def test_monedas_latam_validas_y_ves_no_visible():
    assert moneda_valida("COP")
    assert moneda_valida("PEN")
    assert not moneda_valida("VES")
    assert moneda_valida("VES", visible=False)


def test_formato_usa_codigo_iso_y_decimales_de_moneda():
    assert formato_iso(32000, "COP") == "32.000 COP"
    assert formato_iso(1250, "USD") == "1.250,00 USD"
    assert formato_iso(1250, "CLP") == "1.250 CLP"


def test_conversion_no_aplica_doble_conversion_y_exige_tasa():
    from decimal import Decimal
    from app.services.monedas import convertir
    assert convertir(10, "USD", "COP", 3200) == Decimal("32000")
    assert convertir(32000, "COP", "USD", tasa_usd_origen=3200) == Decimal("10.00")
    try:
        convertir(10, "USD", "COP")
    except ValueError as exc:
        assert "Falta tasa" in str(exc)
    else:
        raise AssertionError("debe exigir tasa")


def test_validar_tasa_rechaza_tasa_no_positiva():
    from app.services.monedas import validar_tasa
    validar_tasa("USD", "USD", None)
    try:
        validar_tasa("USD", "COP", 0)
    except ValueError as exc:
        assert "tasa positiva" in str(exc)
    else:
        raise AssertionError("debe rechazar tasa cero")


def test_contexto_es_serializable_y_expone_base_y_contrato():
    assert contexto("COP", base="USD", tasa=3200, fuente="manual") == {
        "moneda_base": "USD",
        "moneda_contractual": "COP",
        "decimales": 0,
        "simbolo_auxiliar": "$",
        "tipo_cambio": 3200,
        "fecha_tipo_cambio": None,
        "fuente_tipo_cambio": "manual",
    }
