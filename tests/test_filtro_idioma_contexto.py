"""Los filtros ``t``/``mensaje`` deben resolver el idioma del request.

Las plantillas EN escriben ``| t(_idioma)`` / ``| mensaje(_idioma)``, pero
``_idioma`` solo existe dentro del include ``_idioma_switch.html``: Jinja no
propaga esa asignación al padre, así que llegaba ``Undefined`` y los mensajes
dinámicos (guía de inicio, avisos de auth) salían en español en ``/en/…``.
"""
from jinja2 import Undefined

from app.i18n import mensaje
from app.routers.common import TEMPLATES


class _Estado:
    def __init__(self, lang):
        self.lang = lang


class _Request:
    def __init__(self, lang):
        self.state = _Estado(lang)


def _render(expr, lang, **ctx):
    plantilla = TEMPLATES.env.from_string(expr)
    return plantilla.render(request=_Request(lang), _idioma=Undefined(), **ctx)


def test_mensaje_sin_idioma_explicito_usa_el_del_request():
    assert _render("{{ txt | mensaje(_idioma) }}", "en", txt="Descarga el PDF") == "Download the PDF"
    assert _render("{{ txt | mensaje(_idioma) }}", "es", txt="Descarga el PDF") == "Descarga el PDF"


def test_t_sin_idioma_explicito_usa_el_del_request():
    assert _render("{{ 'nav.plans' | t(_idioma) }}", "en") == "Plans"
    assert _render("{{ 'nav.plans' | t(_idioma) }}", "es") == "Planes"


def test_idioma_explicito_sigue_mandando():
    assert _render("{{ txt | mensaje('en') }}", "es", txt="Descarga el PDF") == "Download the PDF"


def test_guia_de_inicio_y_aviso_de_auth_tienen_traduccion():
    assert mensaje("Abre tu presupuesto y hazlo tuyo", "en") == "Open your estimate and make it yours"
    assert mensaje("Hay 3006 partidas disponibles. Comprueba precios y alcance antes de cotizar.", "en") == (
        "There are 3006 line items available. Check prices and scope before quoting."
    )
    assert mensaje("Supabase Auth todavía no está configurado en el servidor.", "en") == (
        "Supabase Auth is not configured on this server yet."
    )
