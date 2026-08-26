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
PUBLIC_CSS = Path("app/static/css/public.css").read_text(encoding="utf-8")
CRITICO = Path("app/templates/_landing_critical.css").read_text(encoding="utf-8")


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

    for hoja in (CSS, PUBLIC_CSS, CRITICO):
        reglas = tinycss2.parse_stylesheet(hoja, skip_whitespace=True, skip_comments=True)
        errores = [r for r in reglas if r.type == "error"]
        assert not errores, [e.message for e in errores[:3]]


# ─────────────────────────────────────────────────────────────────────────────
# Capa móvil premium del sitio público (2026-08-26)
#
# Regresiones que bloquean el reajuste integral de la landing y páginas
# públicas en teléfono: sin viewport-fit=cover la barra de países se pega al
# notch; sin las reglas de APU los subtotales caen a una segunda línea; sin
# la tarjeta de la comparativa la tabla de 720 px obliga a scroll lateral;
# sin el reflujo de la app-bar el botón "PDF" queda recortado en 360 px.
# ─────────────────────────────────────────────────────────────────────────────


def test_landing_lleva_viewport_con_safe_area(cliente_web):
    html = cliente_web.get("/").text
    assert "viewport-fit=cover" in html


def test_css_movil_apu_subtotales_alineados():
    """Celdas vacías de relleno ocultas e importe fijado a la última columna;
    la fila de costes complementarios conserva su porcentaje."""
    assert ".apu-fila.apu-sub > span:nth-child(3)," in PUBLIC_CSS
    assert ".apu-fila.apu-sub:not(.apu-sub-comp) > span:nth-child(2)," in PUBLIC_CSS
    assert ".apu-fila.apu-venta > span:nth-child(3) { display: none; }" in PUBLIC_CSS
    assert ".apu-fila.apu-total > span:last-child { grid-column: 3; }" in PUBLIC_CSS
    assert ".apu-fila.apu-venta > span:last-child { grid-column: 2; }" in PUBLIC_CSS


def test_plantilla_apu_filas_de_subtotal_con_clases():
    contenido = Path("app/templates/landing.html").read_text(encoding="utf-8")
    assert 'class="apu-fila apu-sub apu-sub-comp"' in contenido


def test_css_movil_app_bar_sin_desborde():
    assert ".landing .app-eyebrow { display: none; }" in PUBLIC_CSS
    assert ".landing .app-title { max-width: none; flex: 1 1 auto; }" in PUBLIC_CSS
    assert ".landing .app-total { display: none; }" in PUBLIC_CSS
    assert ".landing .window-ghost { display: none; }" in PUBLIC_CSS


def test_css_movil_pais_bar_compacto_y_sans_zoom_ios():
    assert ".pais-bar-strong { display: none; }" in PUBLIC_CSS
    assert ".pais-bar select { flex: 1 1 auto; width: 100%; min-width: 0; font-size: 16px; }" in PUBLIC_CSS


def test_css_movil_hero_muestra_el_producto_compacto():
    """El panel de control comercial vuelve a verse en móvil (versión compacta)
    y el hero se libera de los 7 chips de mercado (redundantes con la barra
    superior y la sección de países)."""
    assert ".landing .hero-mercados { display: none; }" in PUBLIC_CSS
    assert ".landing .hero-visual { display: flex; padding: 1.5rem 0 0.4rem; }" in PUBLIC_CSS
    assert ".landing .hc-flow { font-size: 0.58rem;" in PUBLIC_CSS


def test_css_critico_sincronizado_con_capa_movil():
    """El CSS del primer viewport refleja la capa móvil: el H1 no se redibuja
    al llegar public.css (los chips de mercado desaparecen con la misma
    media query en ambas hojas)."""
    assert ".landing .hero-mercados{display:none}" in CRITICO


def test_css_movil_comparativa_se_vuelve_tarjetas():
    assert ".landing .comp-tabla thead { display: none; }" in PUBLIC_CSS
    # display:block en tabla+tbody: sin esto las filas en bloque caerían en
    # celdas anónimas de tabla y las tarjetas quedarían en fila horizontal.
    assert (
        ".landing .comp-tabla,\n  .landing .comp-tabla tbody { display: block; }"
        in PUBLIC_CSS
    )
    assert ".landing .comp-tabla tbody tr {" in PUBLIC_CSS
    assert "float: left;" in PUBLIC_CSS
    assert ".landing .comp-who { display: none; }" in PUBLIC_CSS


def test_plantilla_comparativa_lleva_etiquetas_de_columna():
    """Cada celda revela su herramienta (Excel / Generadores / CotizaT) en
    modo tarjeta; en escritorio la etiqueta sigue oculta."""
    contenido = Path("app/templates/landing.html").read_text(encoding="utf-8")
    assert contenido.count('class="comp-who"') == 45


def test_css_movil_botones_a_ancho_completo():
    assert ".landing .acciones { flex-direction: column; align-items: stretch; gap: 0.6rem; }" in PUBLIC_CSS
    assert ".landing .acciones .btn { width: 100%;" in PUBLIC_CSS


def test_css_movil_footer_respeta_safe_area():
    assert "env(safe-area-inset-bottom, 0px)" in PUBLIC_CSS


# ─────────────────────────────────────────────────────────────────────────────
# Navegación móvil completa: barra inferior + hoja de menú (2026-08-26)
#
# El antiguo flujo móvil (botón hamburguesa pequeño en la esquina superior)
# escondía la mayoría de las secciones y quedaba fuera del alcance del pulgar.
# Ahora la barra inferior tiene un botón «Menú» que abre una hoja con TODAS
# las secciones, un buscador de secciones, accesos rápidos para crear y el
# bloque de cuenta (cuenta, organización, tema, salir). Escritorio intacto.
# ─────────────────────────────────────────────────────────────────────────────


def test_barra_inferior_abre_hoja_menu_con_todas_las_secciones(cliente_web):
    html = cliente_web.get("/inicio").text
    assert 'id="boton-menu-movil"' in html
    assert 'aria-controls="menu-movil"' in html
    assert 'aria-haspopup="dialog"' in html
    assert 'id="menu-movil"' in html
    assert 'role="dialog"' in html
    # Secciones sin pestaña propia en la barra: deben llegar vía menú.
    for destino in ('href="/clientes"', 'href="/recursos"', 'href="/facturas"', 'href="/configuracion"'):
        assert destino in html, destino


def test_hoja_menu_trae_buscador_y_accesos_para_crear(cliente_web):
    html = cliente_web.get("/inicio").text
    assert 'id="menu-movil-filtro"' in html
    for destino in (
        "href=\"/presupuestos/nuevo\"",
        "href=\"/clientes/nuevo\"",
        "href=\"/partidas/nueva\"",
        "href=\"/recursos/nuevo\"",
        "href=\"/productos/nuevo\"",
        "href=\"/recetas/nueva\"",
    ):
        assert destino in html, destino


def test_hoja_menu_incluye_cuenta_organizacion_tema_y_salir(cliente_web):
    html = cliente_web.get("/inicio").text
    assert "menu-movil-usuario" in html
    assert 'href="/cuenta"' in html
    assert 'href="/organizaciones"' in html
    assert "theme-toggle-btn" in html
    assert 'action="/salir"' in html


def test_menu_movil_clona_el_sidebar_unica_fuente_de_verdad():
    """La hoja reutiliza la navegación del sidebar (incluye condicionales de
    rol como «Equipo» y el estado activo) en vez de duplicar enlaces."""
    js = Path("app/static/js/menu_movil.js").read_text(encoding="utf-8")
    assert '#app-sidebar nav' in js
    assert "cloneNode(true)" in js
    assert "menu-movil-filtro" in js
    base = Path("app/templates/base.html").read_text(encoding="utf-8")
    assert "js/menu_movil.js" in base


def test_css_movil_hoja_menu_alcanzable_y_comoda():
    assert ".bottom-nav button.bottom-nav-menu" in CSS
    # La hoja es un bottom-sheet con safe-area y cuerpo desplazable.
    assert "max-height: calc(90dvh - env(safe-area-inset-top, 0px))" in CSS
    assert (
        "padding: 0.7rem 0.9rem calc(0.7rem + env(safe-area-inset-bottom, 0px));"
        in CSS
    )
    assert "overscroll-behavior: contain" in CSS
    # El filtro usa 16px reales para no disparar el zoom de iOS.
    assert ".menu-movil-buscar input {" in CSS
    bloque = CSS.split(".menu-movil-buscar input {", 1)[1].split("}", 1)[0]
    assert "font-size: 16px !important;" in bloque
    # Objetivos táctiles generosos en la rejilla de secciones.
    assert ".menu-movil-nav nav a {" in CSS
    assert "min-height: 68px" in CSS
    # El atributo hidden manda aunque la hoja use display:flex.
    assert ".menu-movil [hidden] { display: none !important; }" in CSS


def test_css_movil_retira_el_hamburguesa_de_la_esquina():
    """En móvil ya no se muestra el botón flotante superior: la navegación
    vive en la barra inferior (al alcance del pulgar y sin tapar el título)."""
    assert ".mobile-nav-toggle { display: none; }" in CSS


def test_hoja_menu_no_existe_en_escritorio():
    """Capa base fuera de media queries a display:none (patrón
    .editor-mobile-bar) + guarda explícita ≥769px."""
    assert ".menu-movil,\n.menu-movil-backdrop { display: none; }" in CSS
    guard = CSS.rsplit("@media (min-width: 769px)", 1)[1]
    assert ".menu-movil," in guard
    assert "display: none !important" in guard
