"""Regresiones de la capa móvil premium (2026-08-19).

Bloquean los arreglos que hacen la web usable y elegante en teléfono:

1. viewport con ``viewport-fit=cover`` (notch / indicador de inicio).
2. Las listas principales se renderizan como ``table-mobile-cards`` con
   ``data-label`` (la capa CSS las convierte en tarjetas ≤700 px).
3. ``style.css`` mantiene la capa móvil: campos de 16 px reales (evita el
   zoom automático de iOS), riel de chips del catálogo, bandeja inferior de
   acciones en lote y modales a pantalla completa.
"""
import re
from pathlib import Path

CSS = Path("app/static/css/style.css").read_text(encoding="utf-8")


def test_base_lleva_viewport_con_safe_area(cliente_web):
    html = cliente_web.get("/inicio").text
    assert 'viewport-fit=cover' in html
    assert 'width=device-width' in html


def test_las_listas_principales_se_marcan_como_tarjetas_moviles(cliente_web):
    """Presupuestos y dashboard traen la tabla-tarjeta con etiquetas."""
    html = cliente_web.get("/presupuestos").text
    assert 'class="table table-mobile-cards"' in html
    assert 'data-label="Cliente"' in html
    assert 'data-label="Total"' in html
    assert 'data-label="Acciones"' in html


def test_plantillas_de_listado_llevan_la_tabla_tarjeta():
    for ruta in (
        "app/templates/budgets/list.html",
        "app/templates/clients/list.html",
        "app/templates/facturas/list.html",
        "app/templates/projects/list.html",
        "app/templates/index.html",
    ):
        contenido = Path(ruta).read_text(encoding="utf-8")
        assert "table-mobile-cards" in contenido, ruta
        assert "data-label=" in contenido, ruta


def test_css_movil_campos_de_16px_para_evitar_zoom_de_ios():
    """Safari acerca la página al enfocar un campo <16px: la regla existe y
    está dentro de una media query de móvil."""
    bloque = re.search(
        r"@media \(max-width: 768px\) \{[^@]*?font-size: 16px !important;",
        CSS,
        re.S,
    )
    assert bloque, "falta la regla de 16px en la capa móvil"


def test_css_movil_catalogo_como_riel_de_chips():
    assert ".cat-sidebar-body .cat-group { display: contents; }" in CSS
    assert "border-radius: 999px" in CSS
    assert ".cat-sidebar-body .subcat-btn" in CSS


def test_css_movil_bandeza_inferior_y_modal_completo():
    assert "bottom: calc(70px + env(safe-area-inset-bottom, 0px))" in CSS
    assert ".modal-overlay { padding: 0; }" in CSS


def test_css_sin_errores_de_sintaxis():
    import tinycss2

    reglas = tinycss2.parse_stylesheet(CSS, skip_whitespace=True, skip_comments=True)
    errores = [r for r in reglas if r.type == "error"]
    assert not errores, [e.message for e in errores[:3]]
