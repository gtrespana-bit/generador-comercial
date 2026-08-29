"""Regresiones del cajón de navegación móvil del panel de administración."""
from pathlib import Path


BASE_ADMIN = Path("app/templates/admin/base_admin.html").read_text(encoding="utf-8")
ADMIN_KIT = Path("app/static/js/admin-kit.js").read_text(encoding="utf-8")


def test_hamburguesa_admin_tiene_un_controlador_y_un_destino_accesible():
    """El botón no debe quedarse como marcado inerte: el JS debe controlar
    el mismo sidebar que se desplaza con las reglas responsive del panel."""
    assert 'data-menu-toggle' in BASE_ADMIN
    assert 'aria-controls="sidebar"' in BASE_ADMIN
    assert 'id="sidebar"' in BASE_ADMIN
    assert 'data-menu-fondo' in BASE_ADMIN
    assert 'document.querySelector("[data-menu-toggle]")' in ADMIN_KIT
    assert 'document.body.classList.add("menu-abierto")' in ADMIN_KIT
    assert 'document.body.classList.remove("menu-abierto")' in ADMIN_KIT


def test_menu_admin_cierra_por_fondo_escape_y_navegacion():
    """El cajón móvil debe poder cerrarse con las tres salidas habituales."""
    assert 'menuBackdrop.addEventListener("click", menuCerrar)' in ADMIN_KIT
    assert 'ev.key === "Escape" && menuOpen' in ADMIN_KIT
    assert 'menuSidebar.querySelectorAll("a[href]")' in ADMIN_KIT
    assert 'window.addEventListener("resize"' in ADMIN_KIT


def test_css_admin_bloquea_scroll_mientras_el_cajon_esta_abierto():
    assert 'body.menu-abierto { overflow: hidden; }' in BASE_ADMIN
