"""Los títulos del árbol en inglés hablan como el oficio, no como la regla.

Hasta el lote 76 (20/10/2026) los capítulos del catálogo salían de la
máquina de reglas palabra a palabra: «Works priors» por Actuaciones
previas, «Conditioning of the ground», «protection plot» por protección
solar, «backrest» por respaldo eléctrico y palabras sin traducir
(«salud», «urbanismo», «firmes»). Estas pruebas leen la tabla generada
que usa la app y fallan si ese clase de residuos reaparece en cualquier
título del árbol, o si un capítulo pierde su traducción cuidada.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
_PATRON = re.compile(r"^\d{2}(?:\.\d{2}){0,2}\s")

# Fragmentos que delatan traducción de máquina en un título: falsos
# plurales («-s» pegada), español sin traducir y falsos amigos ya vistos.
_PROHIBIDOS = (
    "priors", "existings", "deeps", "lineds", "decoratives", "pavings",
    "ventilateds", "laminateds", "floatings", "separatings", "integrateds",
    "backrest", "protection plot", "energy plot", "undercoats", "sway",
    "salud", "urbanismo", "firmes", "cimbras", "diversas", "generales",
    "industriales", "especial", "complementarios", "bienestar",
    "pluviales", "limahoyas", "balconeras", "premarcos", "audiovisuales",
    "redes ", "shorings", "assistances", "finishings",
)


def _titulos() -> dict[str, str]:
    tabla = json.loads(
        (RAIZ / "basedatos_partidas/salida/traducciones/EN.json").read_text(
            encoding="utf-8"
        )
    )
    return {k: v for k, v in tabla["cadenas"].items() if _PATRON.match(k)}


def test_el_arbol_sigue_completo():
    titulos = _titulos()
    assert len(titulos) >= 400


def test_ningun_titulo_lleva_residuos_de_la_maquina_de_reglas():
    malos = [
        (k, v) for k, v in _titulos().items()
        if any(frag in v.lower() for frag in _PROHIBIDOS)
    ]
    assert not malos, f"Títulos con residuos: {malos[:10]}"


def test_capitulos_principales_con_terminologia_de_oficio():
    t = _titulos()
    esperado = {
        "01 Actuaciones previas": "01 Preliminary work",
        "02 Demoliciones y desmontajes": "02 Demolition and dismantling",
        "03 Acondicionamiento del terreno": "03 Earthwork and site preparation",
        "07 Carpintería, herrería, vidrios y protección solar":
            "07 Carpentry, metalwork, glazing and solar shading",
        "08 Remates y ayudas": "08 Trim work and builder's work",
        "09 Instalaciones": "09 Building services (MEP)",
        "11 Techos y cubiertas": "11 Roofs and roofing",
        "14 Obras exteriores y urbanismo": "14 Exterior and site works",
        "16 Control de calidad y ensayos": "16 Quality control and testing",
        "17 Seguridad y salud en obra": "17 Construction health and safety",
        "18 Rehabilitación energética": "18 Energy retrofit",
    }
    for es, en in esperado.items():
        assert t.get(es) == en, f"{es}: {t.get(es)!r} != {en!r}"


def test_los_falsos_amigos_clasicos_no_vuelven():
    t = _titulos()
    # aislamiento de servicios = isolation (insulation es el térmico);
    # respaldo eléctrico = backup; pasos = penetrations; balanceo HVAC.
    assert t["01.01 Desconexión y aislamiento de servicios existentes"] == \
        "01.01 Disconnection and isolation of existing services"
    assert t["09.15 Generación, respaldo y energía solar fotovoltaica"] == \
        "09.15 Power generation, backup and solar PV"
    cortafuego = [v for k, v in t.items() if "Sellado cortafuego de pasos" in k]
    assert cortafuego and all("penetrations" in v for v in cortafuego)
    balanceo = [v for k, v in t.items() if "balanceo" in k]
    assert balanceo and all("balancing" in v for v in balanceo)
