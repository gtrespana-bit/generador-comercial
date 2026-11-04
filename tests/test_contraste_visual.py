"""Regresiones del pase de contraste y estados interactivos.

El rediseño no debe volver a dejar texto «invisible» en botones, estados
desactivados, modo oscuro o móvil. Estas pruebas fijan dos contratos:

1. Los pares de tokens semánticos cumplen WCAG AA (4.5:1 para texto y
   3:1 para bordes de controles) en claro y oscuro.
2. Las reglas que causaban los fallos visuales (hover que invertía el
   texto, opacidad en desactivados, landing con especificidad insuficiente,
   resumen móvil recortado y nombres accesibles en inglés) siguen presentes.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
CSS = (RAIZ / "app/static/css/style.css").read_text(encoding="utf-8")
PUBLIC = (RAIZ / "app/static/css/public.css").read_text(encoding="utf-8")
LANDING = (RAIZ / "app/templates/_landing_impulso.css").read_text(encoding="utf-8")
CRITICO = (RAIZ / "app/templates/_landing_critical.css").read_text(encoding="utf-8")


def _bloque(css: str, selector: str) -> str:
    inicio = css.index(selector)
    return css[inicio : css.index("}", inicio)]


def _tokens(css: str, selector: str) -> dict[str, str]:
    bloque = _bloque(css, selector)
    return dict(re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", bloque))


def _rgb(valor: str) -> tuple[float, float, float]:
    valor = valor.strip()
    if valor.startswith("#"):
        h = valor.lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return tuple(int(h[i : i + 2], 16) / 255 for i in (0, 2, 4))  # type: ignore[return-value]
    nums = [float(x) for x in re.findall(r"[\d.]+", valor)[:3]]
    return tuple(x / 255 for x in nums)  # type: ignore[return-value]


def _luminancia(valor: str) -> float:
    def canal(x: float) -> float:
        return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4

    r, g, b = (_rgb(valor))
    return 0.2126 * canal(r) + 0.7152 * canal(g) + 0.0722 * canal(b)


def _compuesta(valor: str, base: str) -> str:
    """Los fondos «soft» oscuros son rgba: se componen sobre la superficie."""
    nums = [float(x) for x in re.findall(r"[\d.]+", valor)]
    if valor.strip().startswith("rgba") and len(nums) == 4:
        fg, alpha = _rgb(valor), nums[3]
        bg = _rgb(base)
        return "#" + "".join(f"{round((f * alpha + b * (1 - alpha)) * 255):02x}" for f, b in zip(fg, bg))
    return valor


def _contraste(a: str, b: str, base: str = "#ffffff") -> float:
    la, lb = _luminancia(a), _luminancia(_compuesta(b, base))
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


@pytest.mark.parametrize("tema", ["light", "dark"])
def test_tokens_de_texto_y_accion_cumplen_aa(tema):
    selector = ":root {" if tema == "light" else '[data-theme="dark"] {'
    t = _tokens(CSS, selector)
    pares_texto = [
        ("--text", "--surface"),
        ("--text-secondary", "--surface"),
        ("--text-soft", "--surface"),
        ("--text-muted", "--surface"),
        ("--text-soft", "--surface-hover"),  # botones desactivados
        ("--text-muted", "--surface-alt"),
        ("--accent", "--surface"),
        ("--on-accent", "--accent"),
        ("--on-accent", "--accent-h"),
        ("--on-danger", "--rose"),
        ("--on-success", "--green"),
        ("--green", "--green-soft"),
        ("--amber", "--amber-soft"),
        ("--rose", "--rose-soft"),
    ]
    for fg, bg in pares_texto:
        assert _contraste(t[fg], t[bg], t["--surface"]) >= 4.5, (tema, fg, bg, t[fg], t[bg])
    assert _contraste(t["--border-control"], t["--surface"]) >= 3.0


def test_botones_primarios_no_invierten_el_texto_en_hover():
    assert "border-color: var(--on-accent)" not in CSS
    assert "border-color: var(--on-accent)" not in PUBLIC
    hover = _bloque(CSS, ".btn-primary:hover {")
    assert "color: var(--on-accent);" in hover
    assert "border-color: var(--accent-h);" in hover
    public_hover = _bloque(PUBLIC, ".btn-primary:hover {")
    assert "color: var(--on-accent);" in public_hover


def test_desactivados_son_legibles_y_no_se_desvanecen():
    for hoja in (CSS, PUBLIC):
        final = hoja[hoja.rindex('.btn:is(:disabled, [aria-disabled="true"]),') :]
        assert "color: var(--text-soft);" in final
        assert "opacity: 1;" in final
        assert "transform: none;" in final
    assert ".autosave-save-now:hover:not(:disabled)" in CSS
    assert ".planos-tool:disabled" in (RAIZ / "app/templates/budgets/planos.html").read_text(encoding="utf-8")
    assert "opacity:1" in (RAIZ / "app/templates/budgets/planos.html").read_text(encoding="utf-8")


def test_landing_gana_a_la_hoja_diferida_y_no_apaga_el_texto():
    assert "body.landing-impulso .hero.lp2-hero .sub.lp2-seo-sub" in LANDING
    assert "--lp2-on-dark-muted: #c5d2e4;" in LANDING
    assert _contraste("#c5d2e4", "#061427") >= 4.5
    assert _contraste("#c9f24d", "#061427") >= 4.5
    assert _contraste("#061427", "#c9f24d") >= 4.5
    assert "color: rgba(255, 255, 255, .45)" not in LANDING
    assert "color: rgba(255, 255, 255, .52)" not in LANDING
    assert "color:var(--on-accent)" in CRITICO.replace(" ", "")


def test_cta_fija_no_hereda_el_texto_apagado_de_la_barra():
    # El mensaje secundario de la barra no puede volver a alcanzar al span
    # del CTA: antes lo dejaba gris claro y pequeño sobre el fondo lima.
    assert "body.landing-impulso .lp2-sticky-int span {" not in LANDING
    assert "body.landing-impulso .lp2-sticky-int > div > span {" in LANDING
    assert "body.landing-impulso .lp2-sticky .lp2-btn-primary," in LANDING
    assert "body.landing-impulso .lp2-sticky .lp2-btn-primary [data-lp2-cta-label] { color: #000; }" in LANDING
    etiqueta = "body.landing-impulso .lp2-sticky .lp2-btn-primary [data-lp2-cta-label] {"
    assert "font-size: inherit;" in _bloque(LANDING[LANDING.rindex(etiqueta) :], etiqueta)
    assert _contraste("#000", "#c9f24d") >= 4.5


def test_resumen_movil_y_cuenta_colapsada_no_se_recortan():
    assert "#card-datos-generales #datos-generales-resumen" in CSS
    assert "#card-datos-generales #btn-toggle-datos" in CSS
    assert "body.collapsed .sidebar-session-info {\n  display: none;" in CSS
    es = (RAIZ / "app/templates/budgets/form.html").read_text(encoding="utf-8")
    en = (RAIZ / "app/templates/budgets/form_en.html").read_text(encoding="utf-8")
    assert "btn.textContent = 'Contraer'" in es and "btn.textContent = 'Expandir'" in es
    assert "btn.textContent = 'Collapse'" in en and "btn.textContent = 'Expand'" in en


def test_enlaces_de_prosa_tienen_subrayado():
    assert ".legal-main :is(p, li) a:not(.btn)" in PUBLIC
    assert ".landing .seo-cuerpo :is(p, li) a:not(.btn)" in PUBLIC
    assert "text-decoration: underline;" in PUBLIC
    assert ".hint a:not(.btn)" in CSS


def test_onboarding_tiene_foco_y_desactivado_legibles():
    for nombre in ("onboarding.html", "onboarding_en.html"):
        html = (RAIZ / "app/templates" / nombre).read_text(encoding="utf-8")
        assert ".btn:focus-visible" in html
        assert ".btn:disabled" in html
        assert "opacity:1" in html
        assert "--border-control:#7b8798" in html


def test_editor_movil_no_tapa_campos_con_el_asistente():
    assert "body.editor-focus .ia-floating-launcher { display: none; }" in CSS
    assert ".editor-ia-chat-btn { display: inline-flex; }" in CSS
    for nombre in ("form.html", "form_en.html"):
        html = (RAIZ / "app/templates/budgets" / nombre).read_text(encoding="utf-8")
        assert 'data-cotizat-click="toggle-ia-chat"' in html
        assert "editor-ia-chat-btn" in html


def test_navegacion_expone_nombre_accesible_en_cada_idioma(cliente_web):
    es = cliente_web.get("/inicio")
    assert es.status_code == 200
    assert '<nav class="sidebar-nav" aria-label="Principal">' in es.text
    en = cliente_web.get("/en/inicio")
    assert en.status_code == 200
    assert '<nav class="sidebar-nav" aria-label="Main">' in en.text
    assert '<nav class="sidebar-nav" aria-label="Principal">' not in en.text
    assert 'aria-label="Open or close menu"' in (RAIZ / "app/templates/_nav_en.html").read_text(encoding="utf-8")


def test_tablas_desplazables_de_modales_son_enfocables():
    for nombre, etiqueta in (
        ("budgets/form.html", "Vista previa del pack de estancia"),
        ("budgets/form_en.html", "Room pack preview"),
        ("partidas/_editor.html", "Desglose de la partida"),
        ("partidas/_editor_en.html", "Line item breakdown"),
    ):
        html = (RAIZ / "app/templates" / nombre).read_text(encoding="utf-8")
        assert f'tabindex="0" role="region" aria-label="{etiqueta}"' in html


def test_hojas_del_pase_siguen_siendo_css_valido():
    import tinycss2

    for hoja in (CSS, PUBLIC, LANDING, CRITICO):
        reglas = tinycss2.parse_stylesheet(hoja, skip_whitespace=True, skip_comments=True)
        errores = [r for r in reglas if r.type == "error"]
        assert not errores, [e.message for e in errores[:3]]
