"""El panel admin no puede perder contraste sin enterarse.

Origen: #188/#189 rediseñaron el panel y lo dejaron con 41 pares texto/fondo por
debajo de WCAG AA en modo oscuro —el peor, `--text-main` (#e2e8f0) sobre `#fff`,
1,23:1— además de cuatro en modo claro. Ninguna prueba miraba el color, así que
pasó el rebase completo sin que nadie lo viera hasta usarlo.

Estas pruebas no arreglan el panel: congelan la deuda en
`docs/panel_contraste_baseline.json` para que **no crezca**, y obligan a
actualizar el baseline a la baja cuando se arregle. La medición la hace
`tools/auditar_contraste_panel.py`, que lee el CSS real del panel sin navegador.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
HERRAMIENTA = REPO / "tools" / "auditar_contraste_panel.py"
BASELINE = REPO / "docs" / "panel_contraste_baseline.json"


def _informe() -> dict:
    resultado = subprocess.run(
        [sys.executable, str(HERRAMIENTA), "--json"],
        capture_output=True,
        text=True,
        cwd=REPO,
    )
    assert resultado.returncode == 0, resultado.stderr
    return json.loads(resultado.stdout)


@pytest.fixture(scope="module")
def informe() -> dict:
    return _informe()


def test_la_herramienta_encuentra_el_css_del_panel(informe):
    """Si deja de leer el CSS, el resto de pruebas pasaría por vacío."""
    assert informe["reglas"] > 500, "El panel debe aportar cientos de reglas CSS."
    assert informe["tokens_claro"] >= 20, "El panel declara su paleta de color."


def test_el_modo_oscuro_redefine_todos_los_tokens_de_color(informe):
    """Un token sin versión oscura hereda el valor claro y rompe el contraste.

    Es la forma en que este tipo de fallo entra sin hacer ruido: se añade un
    token nuevo a `:root`, se usa en una tarjeta y nadie define su valor para
    `html.dark-mode`.
    """
    assert informe["tokens_oscuro"] >= informe["tokens_claro"] - 1, (
        "El bloque html.dark-mode debe redefinir la paleta completa; faltan "
        f"{informe['tokens_claro'] - informe['tokens_oscuro']} token(s)."
    )


def test_no_aparecen_violaciones_de_contraste_nuevas(informe):
    """WCAG AA (4,5:1) en ambos modos, comparado con la deuda aceptada."""
    assert BASELINE.exists(), (
        "Falta docs/panel_contraste_baseline.json: la deuda aceptada del panel."
    )
    aceptado = json.loads(BASELINE.read_text(encoding="utf-8"))

    nuevas = []
    for modo in ("claro", "oscuro"):
        deuda = set(informe[modo]["claves"])
        permitidas = set(aceptado.get(modo, []))
        nuevas.extend(
            f"[{modo}] {clave}" for clave in sorted(deuda - permitidas)
        )
    assert not nuevas, (
        "El panel ha ganado contraste insuficiente nuevo:\n  "
        + "\n  ".join(nuevas)
        + "\nArregla el par o, si es deliberado, añádelo al baseline."
    )


def test_la_deuda_de_contraste_no_crece(informe):
    """Superficies y colores escritos a mano: el techo solo puede bajar."""
    aceptado = json.loads(BASELINE.read_text(encoding="utf-8"))
    superficies = informe["superficies_literales"]["total"]
    assert superficies <= aceptado["superficies_literales_max"], (
        f"Hay {superficies} superficies de fondo escritas a mano (techo "
        f"{aceptado['superficies_literales_max']}). Cada una es una superficie "
        "que no cambia con el tema: usa un token del panel."
    )
    literales = len(informe["colores_literales"])
    assert literales <= aceptado["colores_literales_max"], (
        f"Hay {literales} colores literales distintos (techo "
        f"{aceptado['colores_literales_max']}): usa los tokens de la paleta."
    )


def test_el_baseline_solo_guarda_deuda_real(informe):
    """Un baseline inflado esconde fallos ya arreglados."""
    aceptado = json.loads(BASELINE.read_text(encoding="utf-8"))
    for modo in ("claro", "oscuro"):
        actuales = set(informe[modo]["claves"])
        obsoletas = set(aceptado.get(modo, [])) - actuales
        assert not obsoletas, (
            f"El baseline de {modo} guarda entradas que ya no existen; "
            "quítalas para que la deuda refleje la realidad:\n  "
            + "\n  ".join(sorted(obsoletas))
        )
