"""El panel tiene que verse en un móvil y en modo oscuro de verdad.

Origen (tramo D, 06/11/2026). Tres cosas que ni la auditoría de contraste ni el
humo podían ver:

1. **El modo oscuro estaba a medias.** Los colores eran correctos, pero el
   navegador no sabía en qué tema estaba: sin `color-scheme`, el calendario de
   un campo de fecha, los desplegables, las casillas y las barras de
   desplazamiento salían blancos dentro del panel oscuro.
2. **Las rejillas desbordaban en móvil.** `minmax(420px, 1fr)` en una pantalla
   de 360 px no encoge: crea una columna de 420 px y aparece scroll horizontal.
   La solución es `minmax(min(420px, 100%), 1fr)`.
3. **Navegar no daba ninguna señal** hasta que llegaba la página siguiente.

Estas pruebas leen la hoja servida (`app/static/css/admin.css`) y el JavaScript
del panel: son baratas y cubren justo lo que no se ve en una captura.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CSS = (REPO / "app" / "static" / "css" / "admin.css").read_text(encoding="utf-8")
JS = (REPO / "app" / "static" / "js" / "admin-kit.js").read_text(encoding="utf-8")
BASE = (REPO / "app" / "templates" / "admin" / "base_admin.html").read_text(
    encoding="utf-8"
)
SIN_COMENTARIOS = re.sub(r"/\*.*?\*/", "", CSS, flags=re.S)


def _bloque(selector: str) -> str:
    """Cuerpo de la primera regla cuyo selector incluya `selector`."""
    buscado = selector.strip()
    for encabezado, cuerpo in re.findall(r"([^{}]+)\{([^{}]*)\}", SIN_COMENTARIOS):
        if buscado in {parte.strip() for parte in encabezado.split(",")}:
            return cuerpo
    raise AssertionError(f"no se encontró la regla de {selector}")


# --------------------------------------------------------------------------- #
# 1. Modo oscuro de verdad
# --------------------------------------------------------------------------- #


def test_el_navegador_sabe_en_que_tema_esta():
    """`color-scheme` es lo que hace oscuros los controles nativos.

    Sin él, el panel oscuro enseña un calendario blanco al abrir una fecha y una
    barra de desplazamiento blanca pegada al borde: medio modo oscuro.
    """
    assert "color-scheme: light" in _bloque(":root")
    assert "color-scheme: dark" in _bloque("html.dark-mode")


def test_las_casillas_y_la_seleccion_usan_los_colores_del_tema():
    """`accent-color` y `::selection`: dos detalles que delatan un tema a medias."""
    assert "accent-color" in _bloque(":root")
    assert "::selection" in SIN_COMENTARIOS


def test_el_borde_de_un_campo_se_distingue_del_fondo():
    """WCAG 1.4.11 aplicado al sitio donde importa: los controles.

    `--border-color` es un separador decorativo y puede ser suave. El borde de
    un campo identifica el control, así que usa su propio token.
    """
    assert "--borde-control" in _bloque(":root")
    # En el bloque oscuro se redefine: no puede heredar el gris del tema claro.
    oscuro = _bloque("html.dark-mode")
    assert "--borde-control" in oscuro
    # Los campos lo usan de verdad (si no, tener el token no sirve de nada).
    assert "border: 1px solid var(--borde-control)" in SIN_COMENTARIOS


# --------------------------------------------------------------------------- #
# 2. Responsive
# --------------------------------------------------------------------------- #


def test_ninguna_rejilla_desborda_en_una_pantalla_estrecha():
    """Un `minmax` con píxeles fijos no encoge: desborda.

    `minmax(min(420px, 100%), 1fr)` sí: por debajo de 420 px de contenedor la
    columna se queda con el ancho disponible en vez de forzar scroll lateral.
    """
    rigidos = re.findall(r"minmax\(\s*(\d+)px", SIN_COMENTARIOS)
    assert not rigidos, (
        "Estos minmax tienen mínimo fijo y desbordan en móvil: "
        f"{rigidos}. Usa minmax(min(<px>, 100%), 1fr)."
    )


def test_hay_densidad_para_movil():
    """A 480 px o menos el panel se aprieta: menos relleno y botones pulsables."""
    assert "@media (max-width: 480px)" in SIN_COMENTARIOS
    movil = SIN_COMENTARIOS[SIN_COMENTARIOS.index("@media (max-width: 480px)"):]
    assert "min-height: 40px" in movil[:2000], (
        "En móvil los botones necesitan 40 px de alto para el pulgar."
    )


def test_el_movimiento_se_respeta():
    assert "@media (prefers-reduced-motion: reduce)" in SIN_COMENTARIOS


# --------------------------------------------------------------------------- #
# 3. Señal al navegar
# --------------------------------------------------------------------------- #


def test_navegar_da_una_senal_sin_inventar_esqueletos():
    """El panel se pinta en el servidor: la señal es una barra, no un esqueleto.

    Un esqueleto de tarjetas grises prometería datos que llegan después del
    HTML, y aquí no llegan: sería decorado que miente. Lo que sí se percibe es
    que el clic contó.
    """
    assert ".barra-carga" in SIN_COMENTARIOS
    assert "barra-carga" in JS
    assert "admin-kit.js" in BASE
    # Accesibilidad: mientras navega, la región principal se anuncia ocupada.
    assert "aria-busy" in JS
