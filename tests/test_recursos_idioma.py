"""Recursos del catálogo en inglés: traducción uno a uno, no por glosario.

Los 388 recursos (mano de obra, materiales y maquinaria) se ven en el listado
de recursos, en su ficha de impacto y en el descompuesto de cada partida. Este
test evita que vuelvan a caer en el motor genérico del glosario, que traduce
término a término y producía calcos del español del tipo «Oficial of 1ª
bricklayer» o «Matching of ventosas of elevation».

Cubre tres cosas:
1. Los 388 recursos tienen traducción propia (``recursos_en.json``).
2. Ninguna traducción deja vocablo español sin traducir.
3. Estados Unidos y Reino Unido reciben su vocabulario, no uno compartido.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
RECURSOS = RAIZ / "basedatos_partidas" / "datos" / "recursos.json"
RECURSOS_EN = RAIZ / "basedatos_partidas" / "datos" / "recursos_en.json"

from app.services.traduccion import traducir  # noqa: E402


def _recursos() -> list[tuple[str, str, str]]:
    """(categoría, código, descripción en español) de cada recurso físico."""
    datos = json.loads(RECURSOS.read_text(encoding="utf-8"))
    salida = []
    for categoria in ("mano_obra", "materiales", "maquinaria"):
        for codigo, item in (datos.get(categoria) or {}).items():
            # Los compuestos no son un recurso: son una receta hecha con otros.
            if not isinstance(item, dict) or "composicion" in item:
                continue
            salida.append((categoria, codigo, item.get("descripcion") or ""))
    return salida


def _traducciones() -> dict[str, str]:
    datos = json.loads(RECURSOS_EN.read_text(encoding="utf-8"))
    salida: dict[str, str] = {}
    for categoria, pares in datos.items():
        if isinstance(pares, dict) and not categoria.startswith("_"):
            salida.update(pares)
    return salida


# Vocablos que NO son inglés. Se excluyen a propósito los cognados que sí lo
# son (panel, control, central, natural, material, interior, exterior, motor,
# mineral, detector, sensor, cable, base, regular, flexible, conductor), para
# que el test señale solo residuo real y no ruido.
VOCABLO_ES = {
    "oficial", "ayudante", "especializado", "colocador", "enchapador", "montador",
    "pintor", "electricista", "cabillero", "armador", "carpintero", "encofrador",
    "soldador", "plomero", "albañil", "vidriero", "jardinero", "peon", "operario",
    "amortizacion", "amortizado", "consumibles", "enmascarar", "adaptadores",
    "empotrar", "empotrada", "gris", "varilla", "antihongos", "polipropileno",
    "pisos", "azulejo", "baldosa", "mortero", "yeso", "laminado", "contrachapado",
    "liston", "rastrel", "montante", "canal", "tornillos", "tacos", "sellador",
    "imprimacion", "pintura", "barniz", "laca", "esmalte", "disolvente",
    "decapante", "cortadora", "batidora", "aspirador", "atornilladora", "lijadora",
    "rozadora", "termofusora", "taladro", "mezcladora", "hormigon", "hormigonera",
    "volqueta", "chofer", "andamio", "borriquetas", "telurometro", "manguera",
    "boquilla", "acoples", "racores", "grifo", "sifon", "desague", "teja",
    "canalon", "bajante", "impermeabilizante", "fieltro", "aislante", "estribos",
    "armadura", "ferralla", "canon", "escombro", "vertedero", "prestamo",
    "zahorra", "arena", "grava", "crucetas", "niveladoras", "separadores",
    "pletina", "tornilleria", "herrajes", "bisagras", "cerrojo", "cerradura",
    "enchufe", "interruptor", "mecanismo", "corrugado", "empalme", "bridas",
    "abrazadera", "anclaje", "quimico", "silicona", "pastas",
}


def _vocablos(texto: str) -> set[str]:
    return set(re.findall(r"[a-záéíóúüñ]{4,}", texto.lower()))


def test_los_388_recursos_tienen_traduccion():
    esperados = {codigo for _, codigo, _ in _recursos()}
    assert len(esperados) == 388
    traducidos = set(_traducciones())
    assert esperados - traducidos == set(), (
        f"Recursos sin traducir: {sorted(esperados - traducidos)}"
    )
    assert traducidos - esperados == set(), (
        f"Traducciones que ya no existen: {sorted(traducidos - esperados)}"
    )


def test_ninguna_traduccion_se_queda_igual():
    originales = {codigo: texto for _, codigo, texto in _recursos()}
    for codigo, traducido in _traducciones().items():
        assert traducido.strip(), f"{codigo}: traducción vacía"
        assert traducido.strip() != originales[codigo].strip(), (
            f"{codigo}: la traducción es igual al original"
        )


@pytest.mark.parametrize("mercado", ["US", "GB"])
def test_sin_vocablo_espanol_en_ingles(mercado):
    for categoria, codigo, original in _recursos():
        texto = traducir(original, mercado)
        residuo = _vocablos(texto) & VOCABLO_ES
        assert not residuo, (
            f"[{mercado}] {codigo}: queda español {sorted(residuo)} en «{texto[:70]}»"
        )


@pytest.mark.parametrize("mercado", ["US", "GB"])
def test_sin_calco_del_espanol(mercado):
    """Tres o más «of» seguidos delatan «de X de Y de Z» calcado del español."""
    for _categoria, codigo, original in _recursos():
        texto = traducir(original, mercado)
        assert len(re.findall(r"\bof\b", texto)) < 3, (
            f"[{mercado}] {codigo}: calco del español en «{texto[:70]}»"
        )


def test_estados_unidos_y_reino_unido_no_comparten_vocabulario():
    """Cada mercado recibe su terminología, no una traducción única.

    Si los dos salieran iguales, la variante no estaría haciendo nada y un
    británico leería «dumpster» donde se dice «skip».
    """
    diferencias = []
    for _categoria, codigo, original in _recursos():
        us = traducir(original, "US")
        gb = traducir(original, "GB")
        if us != gb:
            diferencias.append(codigo)
    # No todos los recursos tienen por qué diferir; basta con que la variante
    # actúe en los que sí tienen vocabulario propio en cada mercado.
    assert len(diferencias) > 50, (
        f"La variante británica apenas actúa: solo {len(diferencias)} recursos difieren"
    )


@pytest.mark.parametrize(
    "codigo,esperado_us,esperado_gb",
    [
        ("MO-OF1-ALB", "Journeyman bricklayer.", "Craft operative bricklayer."),
        ("MO-AYU", "Helper.", "General operative."),
        ("MO-AYU-ESP", "Skilled helper.", "Skilled operative."),
        ("MQ-ATORN", "Electric drywall screw gun",
         "Electric plasterboard screw gun"),
        ("MT-ELE-MECA", "receptacle", "socket outlet"),
        ("MT-TABLERO-PROV", "ground fault circuit interrupter",
         "residual current device"),
        ("MT-CONTENEDOR", "dumpster", "skip"),
        ("MT-PINT-TRAFICO", "Traffic paint", "Line marking paint"),
        ("MQ-ESTAMP", "stamped concrete", "imprinted concrete"),
    ],
)
def test_terminologia_por_mercado(codigo, esperado_us, esperado_gb):
    original = {c: t for _cat, c, t in _recursos()}[codigo]
    assert esperado_us in traducir(original, "US"), (
        f"{codigo} en US: se esperaba «{esperado_us}» en «{traducir(original, 'US')}»"
    )
    assert esperado_gb in traducir(original, "GB"), (
        f"{codigo} en GB: se esperaba «{esperado_gb}» en «{traducir(original, 'GB')}»"
    )


@pytest.mark.parametrize(
    "mercado,oficial,ayudante",
    [
        ("US", "Journeyman bricklayer.", "Helper."),
        ("CA", "Journeyman bricklayer.", "Helper."),   # Canadá dice journeyman
        ("GB", "Craft operative bricklayer.", "General operative."),
        ("IE", "Craft operative bricklayer.", "General operative."),
        ("AU", "Tradesperson bricklayer.", "Labourer."),
    ],
)
def test_grados_laborales_por_mercado(mercado, oficial, ayudante):
    """El oficial cualificado no se llama igual en los cinco mercados.

    «Journeyman» es estadounidense y canadiense; el Reino Unido e Irlanda usan
    los grados del convenio (CIJC) y Australia dice «tradesperson». Compartir
    una sola palabra sería exactamente el bloque por idioma que se descartó.
    """
    originales = {codigo: texto for _cat, codigo, texto in _recursos()}
    assert traducir(originales["MO-OF1-ALB"], mercado) == oficial
    assert traducir(originales["MO-AYU"], mercado) == ayudante


def test_traduccion_por_codigo_ignora_el_texto_libre():
    """En el descompuesto el texto es libre: lo que manda es el código.

    Las filas del descompuesto vienen del Excel que sube el usuario y su
    descripción no tiene por qué coincidir con el catálogo. Traducir ese texto
    caería en el glosario, así que se traduce por código.
    """
    from app.services.traduccion import traducir_recurso_por_codigo as por_codigo

    assert por_codigo("Oficial 1ª albañil (texto del Excel)", "MO-OF1-ALB", "GB") == (
        "Craft operative bricklayer."
    )
    assert por_codigo("cualquier cosa", "MQ-ATORN", "GB") == (
        "Electric plasterboard screw gun, including depreciation and power."
    )


def test_traduccion_por_codigo_no_inventa_si_el_codigo_no_es_del_catalogo():
    """Un recurso propio del cliente se deja como está, no se le inventa inglés."""
    from app.services.traduccion import traducir_recurso_por_codigo as por_codigo

    assert por_codigo("Hormigón HA-25 en zapatas", "ZZ-PARTICULAR-99", "GB") == (
        "Hormigón HA-25 en zapatas"
    )
    assert por_codigo("Mi propio recurso", "", "GB") == "Mi propio recurso"
    assert por_codigo("Sin código", None, "GB") == "Sin código"


def test_las_designaciones_de_norma_se_conservan():
    """C1, C2 TE y CG2 son ISO 13007 / EN 12004: se mantienen, como en el catálogo."""
    originales = {codigo: texto for _cat, codigo, texto in _recursos()}
    for codigo, marca in (("MT-ADH-C2TE", "C2 TE"), ("MT-ADH-C1", "C1"),
                          ("MT-JUN-CG2", "CG2")):
        traducido = traducir(originales[codigo], "GB")
        assert marca in traducido, (
            f"{codigo}: se perdió la designación «{marca}» en «{traducido}»"
        )
