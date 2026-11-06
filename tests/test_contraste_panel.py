"""El panel admin no puede perder contraste ni legibilidad sin enterarse.

Origen: #188/#189 rediseñaron el panel y lo dejaron con 41 pares texto/fondo por
debajo de WCAG AA en modo oscuro —el peor, `--text-main` (#e2e8f0) sobre `#fff`,
1,23:1— además de cuatro en modo claro. Ninguna prueba miraba el color, así que
pasó el rebase completo sin que nadie lo viera hasta usarlo.

El tramo A del 2026-11-06 llevó la cuenta a cero. Estas pruebas son la puerta:
la medición la hace `tools/auditar_contraste_panel.py`, que lee el CSS real del
panel sin navegador, y `docs/panel_contraste_baseline.json` guarda la deuda
aceptada (hoy vacía, para que cualquier fallo nuevo se vea).
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

#: Tokens de texto que viven solo en la barra lateral, que es oscura en los dos
#: temas por diseño: no necesitan versión de modo oscuro.
TOKENS_SIDEBAR = {"--text-sidebar", "--text-sidebar-hover", "--text-sidebar-active"}


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


@pytest.fixture(scope="module")
def baseline() -> dict:
    assert BASELINE.exists(), (
        "Falta docs/panel_contraste_baseline.json: la deuda aceptada del panel."
    )
    return json.loads(BASELINE.read_text(encoding="utf-8"))


def test_la_herramienta_encuentra_el_css_del_panel(informe):
    """Si deja de leer el CSS, el resto de pruebas pasaría por vacío."""
    assert informe["reglas"] > 500, "El panel debe aportar cientos de reglas CSS."
    assert informe["tokens_claro"] >= 20, "El panel declara su paleta de color."


def test_todo_token_de_texto_tiene_version_oscura(informe):
    """Un token de texto sin versión oscura hereda el valor claro.

    Es la forma en que este fallo entra sin hacer ruido: se añade un token a
    `:root`, se usa en el `color` de una tarjeta y nadie lo define para
    `html.dark-mode`, así que el texto se queda con el color del tema claro.
    """
    faltan = set(informe["tokens_texto_sin_version_oscura"]) - TOKENS_SIDEBAR
    assert not faltan, (
        "Estos tokens se usan como color de texto y no tienen valor en modo "
        f"oscuro: {sorted(faltan)}. Añádelos al bloque html.dark-mode."
    )


def test_no_hay_tokens_de_color_rotos(informe):
    """Un token que se apunta a sí mismo o a otro que no existe no pinta nada.

    El navegador descarta el valor y el color cae al heredado: es un fallo
    invisible para la vista y para cualquier medición que no resuelva tokens.
    """
    assert not informe["tokens_rotos"], (
        f"Tokens de color sin valor efectivo: {informe['tokens_rotos']}"
    )
    assert not informe["tokens_inexistentes"], (
        "Se usan tokens que no declara la paleta: "
        f"{informe['tokens_inexistentes']}"
    )


def test_no_aparecen_violaciones_de_contraste_nuevas(informe, baseline):
    """WCAG AA (4,5:1) en ambos modos, comparado con la deuda aceptada."""
    nuevas = []
    for modo in ("claro", "oscuro"):
        deuda = set(informe[modo]["claves"])
        permitidas = set(baseline.get(modo, []))
        nuevas.extend(f"[{modo}] {clave}" for clave in sorted(deuda - permitidas))
    assert not nuevas, (
        "El panel ha ganado contraste insuficiente nuevo:\n  "
        + "\n  ".join(nuevas)
        + "\nArregla el par o, si es deliberado, añádelo al baseline."
    )
    assert not informe["claro"]["fallos"], informe["claro"]["fallos"][:5]
    assert not informe["oscuro"]["fallos"], informe["oscuro"]["fallos"][:5]


def test_no_vuelven_las_superficies_fijas_ni_los_colores_a_mano(informe, baseline):
    """Cada fondo a mano es una superficie que no cambia con el tema."""
    superficies = informe["superficies_literales"]["total"]
    assert superficies <= baseline["superficies_literales_max"], (
        f"Hay {superficies} superficies de fondo escritas a mano (techo "
        f"{baseline['superficies_literales_max']}). Usa un token del panel."
    )
    literales = len(informe["colores_literales"])
    assert literales <= baseline["colores_literales_max"], (
        f"Hay {literales} colores literales distintos (techo "
        f"{baseline['colores_literales_max']}): usa los tokens de la paleta."
    )


def test_la_tipografia_usa_la_escala(informe, baseline):
    """Nueve pasos con nombre, no 45 tamaños sueltos repartidos por el CSS."""
    tamanos = informe["tamanos_fuente"]
    fuera = [t for t in tamanos if not t.startswith("var(--t-")]
    assert not fuera, f"Estos font-size no salen de la escala: {fuera}"
    assert len(tamanos) <= baseline.get("tamanos_fuente_max", 9), (
        f"La escala creció a {len(tamanos)} pasos: {tamanos}"
    )


def test_el_baseline_solo_guarda_deuda_real(informe, baseline):
    """Un baseline inflado esconde fallos ya arreglados."""
    for modo in ("claro", "oscuro"):
        actuales = set(informe[modo]["claves"])
        obsoletas = set(baseline.get(modo, [])) - actuales
        assert not obsoletas, (
            f"El baseline de {modo} guarda entradas que ya no existen; "
            "quítalas para que la deuda refleje la realidad:\n  "
            + "\n  ".join(sorted(obsoletas))
        )


HOJA = REPO / "app" / "static" / "css" / "admin.css"
PLANTILLAS = REPO / "app" / "templates" / "admin"


def test_la_piel_del_panel_vive_en_una_hoja_cacheable():
    """Un archivo con huella de versión, no CSS incrustado en cada respuesta.

    Antes del tramo B viajaban ~70 KB de CSS dentro del HTML del panel, sin
    caché posible y con cada pantalla redefiniendo componentes a su manera.
    """
    assert HOJA.exists(), "Falta app/static/css/admin.css, la hoja del panel."
    base = (PLANTILLAS / "base_admin.html").read_text(encoding="utf-8")
    assert "css/admin.css' | asset" in base, (
        "base_admin.html debe cargar la hoja con el filtro asset() para que "
        "viaje con huella de versión y se cachee."
    )
    assert 'class="panel-{{ seccion_activa }}"' in base, (
        "El <body> necesita la clase de área: el CSS de cada pantalla se "
        "prefija con .panel-<área> para no alcanzar a las demás."
    )


def test_ninguna_plantilla_del_panel_vuelve_a_incrustar_estilos():
    """El CSS de una pantalla nueva se añade a admin.css, no al HTML."""
    con_estilos = []
    for ruta in sorted(PLANTILLAS.rglob("*.html")):
        texto = ruta.read_text(encoding="utf-8")
        if "<style" in texto or "extra_css" in texto:
            con_estilos.append(str(ruta.relative_to(REPO)))
    assert not con_estilos, (
        "Estas plantillas del panel vuelven a llevar estilos incrustados: "
        f"{con_estilos}. Muévelos a app/static/css/admin.css."
    )


# --------------------------------------------------------------------------- #
# La medición no puede quedarse ciega
# --------------------------------------------------------------------------- #


def test_el_modo_oscuro_se_mide_con_su_propia_paleta(informe):
    """La auditoría tiene que leer los tokens del modo oscuro, no los del claro.

    El 06/11 (tramo D) se descubrió que el extractor buscaba el texto
    `html.dark-mode` y lo encontraba primero dentro de un comentario del
    encabezado de la hoja, así que devolvía el bloque `:root`. Desde el tramo B
    la auditoría del modo oscuro estaba midiendo la paleta clara y salía
    impecable. Con la extracción arreglada, el oscuro aporta 60 y pico tokens
    propios: si vuelve a caer a cero, esto avisa.
    """
    assert informe["tokens_oscuro"] >= 40, (
        "El modo oscuro tiene que declarar su propia paleta; "
        f"solo se han leído {informe['tokens_oscuro']} tokens."
    )
    # Y no puede ser la misma que la clara: si coinciden, no se leyó el bloque.
    assert informe["tokens_oscuro"] < informe["tokens_claro"] + 1


def test_los_elementos_no_textuales_llegan_a_tres_a_uno(informe):
    """WCAG 1.4.11: bordes de control, anillo de foco y series de gráfico.

    Es el contraste que no se ve fallar mirando: un campo cuyo borde no se
    distingue del fondo, o una barra de gráfico al 85 % de opacidad que se
    queda en 2,95:1, se leen como «diseño limpio» hasta que alguien no
    encuentra el campo.
    """
    for modo in ("claro", "oscuro"):
        filas = informe["componentes"][modo]
        assert len(filas) >= 6, f"faltan mediciones no textuales en {modo}"
        malas = [f for f in filas if not f["ok"]]
        assert not malas, f"{modo}: {malas}"
    assert not informe["componentes_fallos"], informe["componentes_fallos"]
