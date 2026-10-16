"""Registro de mercados: cada país es independiente, no una variante de otro.

Un mercado no es un idioma: es el paquete completo con el que se emite un
presupuesto en un país (idioma, moneda, impuesto con su nombre legal,
formato de número y de fecha, sistema de unidades y terminología de obra).

La regla que sostienen estas pruebas es que **dos mercados no comparten nada
por herencia**: Reino Unido y Estados Unidos hablan inglés los dos, pero no
comparten moneda, ni impuesto, ni orden de la fecha, ni unidades, ni
vocabulario. Un bloque «en» con variantes cosméticas no vale.
"""
from __future__ import annotations

import pytest

from app.paises import ORDEN_SELECTOR, PAIS_GENERICO, PAISES, defaults_para_pais
from app.services import monedas

# Las ocho dimensiones que definen un mercado. Si falta alguna, el mercado
# está a medias: algo se resolverá por idioma en vez de por país.
DIMENSIONES = (
    "locale",
    "idioma",
    "etiqueta_impuesto",
    "etiqueta_impuesto_en",
    "separador_miles",
    "separador_decimal",
    "formato_fecha",
    "sistema_unidades",
)

# Los cinco mercados de habla inglesa: independientes entre sí.
INGLESES = ("US", "GB", "AU", "CA", "IE")


# ---------------------------------------------------------------------------
# Integridad del registro
# ---------------------------------------------------------------------------

def test_todos_los_mercados_tienen_las_ocho_dimensiones():
    for codigo, pais in PAISES.items():
        for dim in DIMENSIONES:
            assert dim in pais, f"a {codigo} le falta la dimensión {dim!r}"
            assert pais[dim] not in (None, ""), f"{codigo}.{dim} está vacío"


def test_ningun_mercado_repite_locale():
    """Dos mercados con el mismo locale serían el mismo mercado con dos nombres."""
    vistos: dict[str, str] = {}
    for codigo, pais in PAISES.items():
        loc = pais["locale"]
        assert loc not in vistos, (
            f"{codigo} y {vistos[loc]} comparten el locale {loc!r}"
        )
        vistos[loc] = codigo


def test_el_selector_y_el_registro_no_se_desincronizan():
    assert set(ORDEN_SELECTOR) == set(PAISES)
    assert len(ORDEN_SELECTOR) == len(PAISES), "códigos repetidos en el orden"


def test_el_generico_tambien_esta_completo():
    """La reserva para «sin país» necesita las mismas dimensiones."""
    for dim in DIMENSIONES:
        assert dim in PAIS_GENERICO, f"al genérico le falta {dim!r}"


def test_defaults_para_pais_expone_todas_las_dimensiones():
    d = defaults_para_pais("GB")
    for dim in DIMENSIONES:
        assert dim in d, f"defaults_para_pais no expone {dim!r}"
    assert d["idioma"] == "en"
    assert d["etiqueta_impuesto"] == "VAT"
    assert d["sistema_unidades"] == "metrico"


# ---------------------------------------------------------------------------
# Reino Unido y Estados Unidos no pueden compartir bloque
# ---------------------------------------------------------------------------

def test_reino_unido_y_estados_unidos_no_comparten_nada_de_negocio():
    """Mismo idioma, mercado distinto: todo lo que es de país debe diferir."""
    us, gb = PAISES["US"], PAISES["GB"]
    assert us["idioma"] == gb["idioma"] == "en", "los dos son anglófonos"
    for dim in ("moneda", "etiqueta_impuesto", "separador_miles",
                "separador_decimal", "formato_fecha", "sistema_unidades"):
        # Se comparan salvo cuando coinciden por razón de idioma (los
        # separadores son iguales en inglés); lo que no puede coincidir es
        # lo que define al mercado.
        if dim in ("separador_miles", "separador_decimal"):
            continue
        assert us[dim] != gb[dim], (
            f"US y GB comparten {dim} ({us[dim]!r}): son el mismo bloque"
        )


def test_reino_unido_y_estados_unidos_se_diferencian_en_fecha_y_unidades():
    """La fecha y las unidades son la prueba de que separar por idioma no basta."""
    assert PAISES["US"]["formato_fecha"] == "MM/DD/YYYY"
    assert PAISES["GB"]["formato_fecha"] == "DD/MM/YYYY"
    assert PAISES["US"]["sistema_unidades"] == "imperial"
    assert PAISES["GB"]["sistema_unidades"] == "metrico"


def test_los_cinco_mercados_ingleses_son_independientes():
    """Cada uno con su moneda y su impuesto; ninguno hereda de otro."""
    combinaciones = {c: (PAISES[c]["moneda"], PAISES[c]["etiqueta_impuesto"])
                     for c in INGLESES}
    # Al menos cuatro pares moneda+impuesto distintos entre los cinco:
    # GB e IE coinciden en VAT pero no en moneda (GBP frente a EUR).
    assert len(set(combinaciones.values())) >= 4, combinaciones
    assert combinaciones["US"] == ("USD", "Sales tax")
    assert combinaciones["GB"] == ("GBP", "VAT")
    assert combinaciones["AU"] == ("AUD", "GST")
    assert combinaciones["CA"] == ("CAD", "GST/HST")
    assert combinaciones["IE"] == ("EUR", "VAT")


def test_el_vocabulario_de_obra_tambien_es_local():
    """No hay un único glosario inglés: US dice drywall, UK dice plasterboard."""
    assert "drywall" in PAISES["US"]["vocab"]
    assert "plasterboard" in PAISES["GB"]["vocab"]
    # Y el modelo de partición cambia con las unidades.
    assert "baseboard" in PAISES["US"]["vocab"]
    assert "skirting" in PAISES["GB"]["vocab"]


# ---------------------------------------------------------------------------
# Las monedas de los mercados nuevos existen de verdad
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("codigo,esperado", [
    ("GBP", "Libra esterlina"),
    ("AUD", "Dólar australiano"),
    ("CAD", "Dólar canadiense"),
])
def test_las_monedas_de_los_mercados_nuevos_estan_registradas(codigo, esperado):
    """Un mercado con una moneda que el sistema no conoce es un mercado roto."""
    d = monedas.MONEDAS.get(codigo)
    assert d is not None, f"{codigo} no está registrada en monedas.py"
    assert d.nombre == esperado
    assert d.codigo == codigo
    assert d.decimales == 2
    # Y tiene que estar en el catálogo que valida los formularios: si solo
    # está en monedas.py, normalizar_moneda() la convertiría en USD.
    from app.utils import normalizar_moneda, simbolo_moneda

    assert normalizar_moneda(codigo) == codigo
    assert simbolo_moneda(codigo)


def test_todos_los_mercados_usan_una_moneda_que_el_sistema_conoce():
    from app.utils import normalizar_moneda

    for codigo, pais in PAISES.items():
        assert normalizar_moneda(pais["moneda"]) == pais["moneda"], (
            f"{codigo} usa {pais['moneda']!r}, que el sistema no reconoce "
            f"y convertiría en USD en silencio"
        )


def test_formatear_importes_en_las_monedas_nuevas():
    for codigo in ("GBP", "AUD", "CAD"):
        assert monedas.simbolo(codigo), f"{codigo} no tiene símbolo"
        assert monedas.formato_iso(1234.5, codigo, "en") == f"1,234.50 {codigo}"


# ---------------------------------------------------------------------------
# El formato es del mercado, no del idioma
# ---------------------------------------------------------------------------

def test_mexico_no_usa_el_separador_decimal_de_espana():
    """México escribe 1,234.56; España 1.234,56. Los dos son español."""
    assert PAISES["MX"]["idioma"] == PAISES["ES"]["idioma"] == "es"
    assert PAISES["MX"]["separador_decimal"] == "."
    assert PAISES["ES"]["separador_decimal"] == ","
    assert PAISES["MX"]["separador_miles"] == ","
    assert PAISES["ES"]["separador_miles"] == "."


def test_hay_mercados_hispanos_en_los_dos_formatos():
    """Si todos los hispanos compartieran formato, sospecha: alguien los unificó."""
    punto = {c for c, p in PAISES.items()
             if p["idioma"] == "es" and p["separador_decimal"] == "."}
    coma = {c for c, p in PAISES.items()
            if p["idioma"] == "es" and p["separador_decimal"] == ","}
    assert len(punto) >= 5 and len(coma) >= 5, (sorted(punto), sorted(coma))


# ---------------------------------------------------------------------------
# El impuesto se llama como se llama en cada país
# ---------------------------------------------------------------------------

def test_los_impuestos_con_nombre_propio_no_se_traducen_a_vat():
    """IGV, ITBMS, ITBIS e ISV no son «IVA»: son otros impuestos."""
    assert PAISES["PE"]["etiqueta_impuesto"] == "IGV"
    assert PAISES["PA"]["etiqueta_impuesto"] == "ITBMS"
    assert PAISES["DO"]["etiqueta_impuesto"] == "ITBIS"
    assert PAISES["HN"]["etiqueta_impuesto"] == "ISV"
    # Y al mostrarlos en inglés siguen siendo ellos: no existe «VAT peruano».
    for codigo in ("PE", "PA", "DO", "HN"):
        assert PAISES[codigo]["etiqueta_impuesto_en"] == \
            PAISES[codigo]["etiqueta_impuesto"], (
                f"a {codigo} se le tradujo el nombre del impuesto")


def test_el_iva_generico_si_se_dice_vat_en_ingles():
    """Donde el impuesto es el IVA, en inglés se dice VAT (concepto, no nombre)."""
    for codigo in ("ES", "CO", "MX", "CL", "AR"):
        assert PAISES[codigo]["etiqueta_impuesto_en"] == "VAT", codigo


def test_la_tasa_del_impuesto_es_la_de_cada_pais():
    assert PAISES["ES"]["iva"] == 21
    assert PAISES["PA"]["iva"] == 7
    assert PAISES["UY"]["iva"] == 22
    assert PAISES["GB"]["iva"] == 20
    assert PAISES["AU"]["iva"] == 10


def test_irlanda_puede_tener_una_tasa_no_entera():
    """La construcción en Irlanda va al 13,5 %, no al 23 % general."""
    assert PAISES["IE"]["iva"] == 13.5
    assert isinstance(PAISES["IE"]["iva"], float)


# ---------------------------------------------------------------------------
# El identificador fiscal también es local
# ---------------------------------------------------------------------------

def test_cada_mercado_tiene_su_identificador_fiscal():
    assert PAISES["US"]["id_fiscal"] == "EIN"
    assert PAISES["GB"]["id_fiscal"] == "VAT registration number"
    assert PAISES["AU"]["id_fiscal"] == "ABN"
    assert PAISES["CA"]["id_fiscal"] == "BN"
    assert PAISES["ES"]["id_fiscal"] == "NIF"
    assert PAISES["MX"]["id_fiscal"] == "RFC"


# ---------------------------------------------------------------------------
# Un mercado nuevo se tiene que resolver solo
# ---------------------------------------------------------------------------

def test_todo_mercado_se_resuelve_por_su_nombre_oficial():
    """Si un mercado no se resuelve, su empresa se queda sin glosario.

    `traduccion.codigo_desde_pais` mantuvo una lista de países a mano que se
    quedó vieja al dar de alta los mercados ingleses: «Estados Unidos»
    devolvía vacío y la empresa se quedaba sin terminología sin avisar.
    Ahora se deriva del registro, así que un mercado nuevo entra solo.
    """
    from app.services.traduccion import codigo_desde_pais

    for codigo, pais in PAISES.items():
        assert codigo_desde_pais(pais["nombre"]) == codigo, (
            f"{codigo} ({pais['nombre']!r}) no se resuelve: su empresa se "
            f"quedaría sin glosario de terminología"
        )


def test_todo_mercado_se_resuelve_por_su_gentilicio():
    from app.services.traduccion import codigo_desde_pais

    for codigo, pais in PAISES.items():
        assert codigo_desde_pais(pais["mercado"]) == codigo, (
            f"el gentilicio {pais['mercado']!r} no resuelve a {codigo}"
        )


def test_las_formas_colloquiales_de_llamar_a_un_pais_resuelven():
    from app.services.traduccion import codigo_desde_pais

    assert codigo_desde_pais("USA") == "US"
    assert codigo_desde_pais("United States") == "US"
    assert codigo_desde_pais("UK") == "GB"
    assert codigo_desde_pais("England") == "GB"
    assert codigo_desde_pais("México") == codigo_desde_pais("méxico") == "MX"
    assert codigo_desde_pais("Perú") == "PE"
    assert codigo_desde_pais("Canadá") == "CA"
    # «Latinoamérica» no es un país: cae al genérico, que es lo correcto.
    assert codigo_desde_pais("Latinoamérica") == ""


def test_un_pais_desconocido_no_se_inventa():
    from app.services.traduccion import codigo_desde_pais

    assert codigo_desde_pais("") == ""
    assert codigo_desde_pais(None) == ""
    assert codigo_desde_pais("Wakanda") == ""


def test_la_resolucion_tolera_acentos_y_enhe():
    """«Espana» sin eñe y «España» son el mismo país.

    La normalización antigua quitaba cinco vocales acentuadas a mano y se
    dejaba la eñe, así que había que escribir las dos formas de cada país.
    Ahora se normaliza en Unicode y Funciona con cualquier acento.
    """
    from app.services.traduccion import codigo_desde_pais

    for escrito, esperado in (("España", "ES"), ("españa", "ES"),
                              ("Espana", "ES"), ("espana", "ES"),
                              ("México", "MX"), ("Mexico", "MX"),
                              ("Perú", "PE"), ("Peru", "PE"),
                              ("Canadá", "CA"), ("Canada", "CA")):
        assert codigo_desde_pais(escrito) == esperado, (
            f"{escrito!r} debería resolver a {esperado!r}"
        )


def test_ningun_mercado_choca_con_otro_al_normalizar():
    """Si dos nombres normalizan igual, uno de los dos queda inalcanzable."""
    from app.services.traduccion import _sin_acento_minuscula

    vistos: dict[str, list[str]] = {}
    for codigo, pais in PAISES.items():
        vistos.setdefault(_sin_acento_minuscula(pais["nombre"]), []).append(codigo)
    choques = {k: v for k, v in vistos.items() if len(v) > 1}
    assert not choques, f"nombres que colisionan al normalizar: {choques}"


# ── Resolución de mercado ────────────────────────────────────────────────
# De una cadena de idioma, un locale o un nombre de país sale el mercado
# completo. Nada de esto puede depender de un prefijo: «en-GB» y «en-US»
# empiezan igual y no son el mismo mercado.

@pytest.mark.parametrize(
    "clave,codigo",
    [
        ("en", "US"),        # inglés a secas: el mercado por defecto
        ("en-US", "US"), ("en-GB", "GB"), ("en-AU", "AU"),
        ("en-CA", "CA"), ("en-IE", "IE"),
        ("es", "ES"), ("es-MX", "MX"), ("es-CO", "CO"),
        ("GB", "GB"), ("mx", "MX"),
        ("Reino Unido", "GB"), ("España", "ES"), ("Australia", "AU"),
    ],
)
def test_resolver_mercado_encuentra_el_pais(clave, codigo):
    from app.paises import resolver_mercado

    assert resolver_mercado(clave)["codigo"] == codigo


@pytest.mark.parametrize("clave", [None, "", "zz", "kl", "Marte"])
def test_resolver_mercado_desconocido_cae_al_generico(clave):
    from app.paises import PAIS_GENERICO, resolver_mercado

    assert resolver_mercado(clave) is PAIS_GENERICO


def test_resolver_mercado_devuelve_las_ocho_dimensiones():
    from app.paises import resolver_mercado

    for clave in ("en-US", "en-GB", "es-MX", "es"):
        assert all(d in resolver_mercado(clave) for d in DIMENSIONES)


def test_el_idioma_se_lee_del_mercado_no_del_prefijo():
    """«en-GB» e «en-US» son inglés; «es-MX» es español. Nada de startswith."""
    from app.paises import es_ingles, idioma_de

    assert idioma_de("en-GB") == "en" and idioma_de("en-US") == "en"
    assert idioma_de("es-MX") == "es" and idioma_de("es-CO") == "es"
    assert es_ingles("en-GB") and es_ingles("en-AU") and not es_ingles("es-MX")


# ── Formato por mercado, no por idioma ───────────────────────────────────

def test_mexico_y_espana_no_escriben_los_numeros_igual():
    """Los dos hablan español; México separa como EE. UU. y España no."""
    from app.paises import resolver_mercado
    from app.utils import fmt_monto_iso

    assert fmt_monto_iso(35041.65, "MXN", mercado=resolver_mercado("es-MX")) \
        == "35,041.65 MXN"
    assert fmt_monto_iso(35041.65, "EUR", mercado=resolver_mercado("es-ES")) \
        == "35.041,65 EUR"


def test_reino_unido_y_estados_unidos_no_escriben_la_fecha_igual():
    """Los dos hablan inglés; solo EE. UU. pone el mes primero."""
    import datetime

    from app.paises import resolver_mercado
    from app.utils import fmt_fecha

    fecha = datetime.date(2026, 8, 15)
    assert fmt_fecha(fecha, mercado=resolver_mercado("en-US")) == "08/15/2026"
    assert fmt_fecha(fecha, mercado=resolver_mercado("en-GB")) == "15/08/2026"
    assert fmt_fecha(fecha, mercado=resolver_mercado("en-AU")) == "15/08/2026"
    assert fmt_fecha(fecha, mercado=resolver_mercado("es-MX")) == "15/08/2026"


def test_sin_mercado_el_formato_sigue_dependiendo_del_idioma():
    """Quien no pase mercado no ve cambios: es la red de seguridad."""
    import datetime

    from app.utils import fmt_fecha, fmt_monto_iso

    assert fmt_monto_iso(35041.65, "USD", idioma="es") == "35.041,65 USD"
    assert fmt_monto_iso(35041.65, "USD", idioma="en") == "35,041.65 USD"
    assert fmt_fecha(datetime.date(2026, 8, 15), idioma="es") == "15/08/2026"


# ── El impuesto se llama como se llama en cada mercado ───────────────────

@pytest.mark.parametrize(
    "clave,esperado",
    [
        ("en-US", "Sales tax"), ("en-GB", "VAT"), ("en-AU", "GST"),
        ("en-CA", "GST/HST"), ("en-IE", "VAT"),
        ("es-ES", "I.V.A."), ("es-PE", "IGV"), ("es-DO", "ITBIS"),
        ("es-PA", "ITBMS"), ("es-HN", "ISV"),
    ],
)
def test_etiqueta_del_impuesto_por_mercado(clave, esperado):
    from app.services.excel_export import _etiqueta_impuesto

    assert _etiqueta_impuesto(clave) == esperado


# ── Variante del inglés: EE. UU. no redacta como el Reino Unido ──────────

def test_la_muestra_en_us_no_habla_ingles_britanico():
    """El mismo presupuesto, redactado para dos mercados, no dice lo mismo."""
    import io

    from pypdf import PdfReader

    from app.services.presupuesto_muestra import construir

    gb = "".join(p.extract_text() or ""
                 for p in PdfReader(io.BytesIO(construir("en-GB"))).pages)
    us = "".join(p.extract_text() or ""
                 for p in PdfReader(io.BytesIO(construir("en-US"))).pages)

    assert "skirting" in gb and "baseboard" not in gb
    assert "baseboard" in us and "skirting" not in us
    assert "skilled labour" in gb and "skilled labor" in us
    assert "VAT (" in gb and "Sales tax (" in us


def test_canada_escribe_como_el_reino_unido_y_construye_como_ee_uu():
    """Canadá es el caso que parte en dos a quien mira solo el idioma."""
    from app.paises import resolver_mercado
    from app.services.variante_ingles import aplicar_variante

    ca = resolver_mercado("en-CA")
    texto = aplicar_variante(
        "Lacquered MDF skirting, skilled labour, quartz worktop", ca)
    # Vocabulario de obra: estadounidense. Ortografía: británica.
    assert "baseboard" in texto and "countertop" in texto
    assert "labour" in texto


def test_australia_llama_benchtop_a_la_encimera():
    from app.paises import resolver_mercado
    from app.services.variante_ingles import aplicar_variante

    au = aplicar_variante("Quartz worktop", resolver_mercado("en-AU"))
    assert "benchtop" in au


def test_la_variante_respeta_mayusculas_y_plural():
    from app.paises import resolver_mercado
    from app.services.variante_ingles import aplicar_variante

    us = resolver_mercado("en-US")
    assert aplicar_variante("WC and washbasin installation", us) \
        == "Toilet and sink installation"     # sigla: sin gritar
    assert aplicar_variante("premium matt emulsions", us) \
        == "premium flat latex paints"        # plural al final
    assert aplicar_variante("SKIRTING AND WORKTOP", us) \
        == "BASEBOARD AND COUNTERTOP"         # versalitas: todo en mayúsculas


def test_reino_unido_e_irlanda_no_llevan_variante():
    """La redacción base es británica: no hay nada que ajustar."""
    from app.paises import resolver_mercado
    from app.services.variante_ingles import aplicar_variante, necesita_variante

    for clave in ("en-GB", "en-IE", "es-ES", "es-MX"):
        mercado = resolver_mercado(clave)
        assert not necesita_variante(mercado), clave
        assert aplicar_variante("skirting, labour", mercado) == "skirting, labour"
