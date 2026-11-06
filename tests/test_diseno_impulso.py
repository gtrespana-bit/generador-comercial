"""Regresiones de la extensión del diseño «Impulso» al resto de la web.

La landing aprobada no se toca: las capas pública y de aplicación deben quedar
scopeadas, compartir navy/lima/papel y mantener legibles los estados críticos
(sesión, footer, onboarding y administración).
"""
from pathlib import Path

import tinycss2

RAIZ = Path(__file__).resolve().parents[1]
PUBLIC = (RAIZ / "app/static/css/public.css").read_text(encoding="utf-8")
APP = (RAIZ / "app/static/css/style.css").read_text(encoding="utf-8")
ONBOARDING = (RAIZ / "app/templates/onboarding.html").read_text(encoding="utf-8")
ONBOARDING_EN = (RAIZ / "app/templates/onboarding_en.html").read_text(encoding="utf-8")
# La piel del panel vive en su hoja desde el tramo B (2026-11-06).
ADMIN = (RAIZ / "app/static/css/admin.css").read_text(encoding="utf-8")


def _sin_errores(css: str) -> None:
    errores = [p for p in tinycss2.parse_stylesheet(css, skip_whitespace=True) if p.type == "error"]
    assert not errores, errores


def _contraste(hex1: str, hex2: str) -> float:
    def lum(hex_color: str) -> float:
        hex_color = hex_color.lstrip("#")
        canales = [int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        canales = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in canales]
        return 0.2126 * canales[0] + 0.7152 * canales[1] + 0.0722 * canales[2]

    l1, l2 = lum(hex1), lum(hex2)
    claro, oscuro = max(l1, l2), min(l1, l2)
    return (claro + 0.05) / (oscuro + 0.05)


def test_capas_impulso_parsean_y_no_invaden_la_landing_aprobada():
    _sin_errores(PUBLIC)
    _sin_errores(APP)
    assert "SUPERFICIE PÚBLICA «IMPULSO»" in PUBLIC
    assert "APLICACIÓN «IMPULSO»" in APP
    assert "body:not(.landing-impulso)" in PUBLIC
    assert "body.landing:not(.landing-impulso) .plan" in PUBLIC
    assert "--ct-lime: #c9f24d" in PUBLIC
    assert "--ct-lime: #c9f24d" in APP


def test_sesion_y_footer_mantienen_contraste_sobre_superficies_oscuras():
    assert ".sidebar-session," in APP
    assert ".sidebar-session-nombre { color: #fff; }" in APP
    assert ".sidebar-session-plan.sin { background: rgba(201, 242, 77, .16); color: var(--ct-lime); }" in APP
    assert "body:not(.landing-impulso) .site-footer a:visited" in PUBLIC
    assert _contraste("#c5d2e4", "#061427") >= 4.5
    assert _contraste("#c9f24d", "#061427") >= 4.5
    assert _contraste("#000000", "#c9f24d") >= 4.5


def test_indices_publicos_no_dejan_enlaces_sin_estilo_fuera_de_pantalla():
    # content-visibility:auto en los índices difería el estilo de los enlaces
    # aún no visitados: en móvil aparecían con el azul del navegador y axe
    # los medía contra el footer. Los hubs/mapa deben estar visibles ya.
    assert ".hub-page main > section {" in PUBLIC
    bloque = PUBLIC.split(".hub-page main > section {", 1)[1].split("}", 1)[0]
    assert "content-visibility: visible;" in bloque
    assert "contain-intrinsic-size: auto;" in bloque
    assert "body:not(.landing-impulso) .hub-bloque a:visited" in PUBLIC


def test_tema_del_menu_movil_no_hereda_el_sidebar_oscuro():
    # El botón de tema del cajón móvil vive sobre una superficie clara; solo
    # el botón del sidebar debe recibir tinta marina/lima.
    assert ".sidebar .theme-toggle-btn," in APP
    assert ".sidebar .theme-toggle-label { color: var(--ct-sidebar-muted); }" in APP
    assert "\n.theme-toggle-btn,\n" not in APP
    assert "\n.theme-toggle-label { color: var(--ct-sidebar-muted); }" not in APP


def test_onboarding_y_admin_comparten_la_paleta_aprobada():
    for fuente in (ONBOARDING, ONBOARDING_EN):
        assert "--navy:#061427" in fuente
        assert "--gold:#c9f24d" in fuente
        assert ".btn-primary { background:var(--gold); border-color:var(--gold); color:#000;" in fuente
        assert "#e5ae3c" not in fuente
    assert "--bg-sidebar: #061427" in ADMIN
    assert "--bg-sidebar-active: #c9f24d" in ADMIN
    assert "--text-sidebar-active: #000000" in ADMIN
    assert "#0e2b20" not in ADMIN
    assert "#0b5b38" not in ADMIN


def test_el_resto_del_embudo_mantiene_el_mensaje_de_margen_y_tiempos():
    acceso = (RAIZ / "app/templates/auth/access.html").read_text(encoding="utf-8")
    acceso_en = (RAIZ / "app/templates/auth/access_en.html").read_text(encoding="utf-8")
    pago = (RAIZ / "app/templates/pago.html").read_text(encoding="utf-8")
    pago_en = (RAIZ / "app/templates/pago_en.html").read_text(encoding="utf-8")
    footer = (RAIZ / "app/templates/_footer_publico.html").read_text(encoding="utf-8")
    footer_en = (RAIZ / "app/templates/_footer_publico_en.html").read_text(encoding="utf-8")
    assert "Margen y tiempo de obra por partida y total" in acceso
    assert "Margin and work time per item and total" in acceso_en
    assert pago.count("Margen y tiempo de obra por partida y total") == 2
    assert pago_en.count("Margin and work time per item and total") == 2
    assert "tiempos de obra y PDF profesional" in footer
    assert "work times and professional PDF" in footer_en
