"""Fase 3 (piloto): una sola plantilla sirve ES y EN desde el catálogo.

Hasta aquí, cada pantalla en inglés era una plantilla gemela
(``forbidden.html`` / ``forbidden_en.html``): 94 ficheros duplicados que
se desincronizan en silencio. El piloto migra tres páginas standalone
de aviso a plantilla única: los textos de interfaz salen de
``app/locales/{es,en}.json`` vía el filtro ``t()`` que ya existía, y el
resolvedor de plantillas —que ya caía a la base si no hay gemela— no
cambia. Los textos ingleses se trasladaron de las gemelas, sin
re-traducir nada.

Frontera explícita: esto es solo la interfaz. Los datos del catálogo y
sus traducciones uno a uno (``basedatos_partidas/datos/recursos_en.json``
y compañía) no se tocan; los sigue guardando ``test_recursos_idioma``.

Las pantallas que extienden ``base.html`` quedan fuera del piloto: su
gemela extiende ``base_en.html`` y migrarlas antes que la base daría
contenido en un idioma dentro del marco del otro.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

RAIZ = Path(__file__).resolve().parents[1]
PLANTILLAS = RAIZ / "app" / "templates"
LOCALES = RAIZ / "app" / "locales"

# Plantillas del piloto con el contexto mínimo que necesitan.
PILOTO = {
    "auth/forbidden.html": {
        "product_name": "CotizaT",
        "error": "No tienes permiso para completar esta acción.",
    },
    "baja_completada.html": {
        "product_name": "CotizaT",
        "nombre": "Obras del Sur",
    },
    "licencia_suspendida.html": {
        "product_name": "CotizaT",
        "error": "La licencia de esta organización está suspendida.",
        "email_soporte": "soporte@cotizat.online",
    },
}

_VALORES = {"nombre": "Obras del Sur", "producto": "CotizaT"}
_RE_CLAVE = re.compile(r"'([\w.]+)'\s*\|\s*t\(")


def _catalogo(idioma: str) -> dict:
    return json.loads((LOCALES / f"{idioma}.json").read_text(encoding="utf-8"))


def _claves_de(nombre: str) -> list[str]:
    fuente = (PLANTILLAS / nombre).read_text(encoding="utf-8")
    return sorted(set(_RE_CLAVE.findall(fuente)))


def _render(nombre: str, idioma: str, contexto: dict) -> str:
    from app.routers.common import TEMPLATES

    peticion = SimpleNamespace(
        state=SimpleNamespace(lang=idioma),
        url=SimpleNamespace(path="/inicio", query=""),
    )
    plantilla = TEMPLATES.env.get_template(nombre)
    return plantilla.render(request=peticion, _idioma=idioma, **contexto)


def _formatear(valor: str) -> str:
    return valor.format(**_VALORES) if "{" in valor else valor


@pytest.mark.parametrize("nombre", sorted(PILOTO))
def test_plantilla_piloto_sirve_ambos_idiomas_desde_el_catalogo(nombre):
    es, en = _catalogo("es"), _catalogo("en")
    html_es = _render(nombre, "es", PILOTO[nombre])
    html_en = _render(nombre, "en", PILOTO[nombre])

    assert '<html lang="es">' in html_es
    assert '<html lang="en">' in html_en
    for clave in _claves_de(nombre):
        # Sin fuga: si la clave faltara en el catálogo, t() la imprimiría.
        assert clave not in html_es
        assert clave not in html_en
        texto_es, texto_en = _formatear(es[clave]), _formatear(en[clave])
        assert texto_es in html_es, clave
        assert texto_en in html_en, clave
        if "{" not in es[clave]:
            assert texto_es not in html_en, clave
            assert texto_en not in html_es, clave


def test_las_claves_del_piloto_estan_en_ambos_catalogos_y_traducidas():
    es, en = _catalogo("es"), _catalogo("en")
    for nombre in PILOTO:
        for clave in _claves_de(nombre):
            assert clave in es, f"{clave} falta en es.json"
            assert clave in en, f"{clave} falta en en.json"
            assert es[clave].strip() and en[clave].strip()
            assert es[clave] != en[clave], f"{clave} sin traducir"


def test_las_gemelas_del_piloto_se_retiraron():
    for nombre in PILOTO:
        gemela = nombre.replace(".html", "_en.html")
        assert not (PLANTILLAS / gemela).exists(), gemela


# Regla de la Fase 3: toda plantilla nueva nace única usando t(). Esta
# lista congela las gemelas que existían al cerrar el piloto; solo puede
# encoger (al migrar una, se borra el fichero y su línea aquí).
GEMELAS_CONGELADAS = frozenset({
    '_asistente_ia_en.html', '_footer_publico_en.html', '_nav_en.html',
    'actividad_en.html', 'auth/access_en.html', 'auth/account_en.html',
    'auth/invitation_en.html', 'auth/organization_new_en.html', 'auth/organizations_en.html',
    'auth/recover_en.html', 'auth/reset_password_en.html', 'auth/team_en.html',
    'baja_en.html', 'base_en.html', 'budgets/compare_versions_en.html',
    'budgets/decomposition_en.html', 'budgets/detail_en.html', 'budgets/form_en.html',
    'budgets/import_en.html', 'budgets/list_en.html', 'budgets/optimizar_en.html',
    'budgets/planos_en.html', 'budgets/public_link_en.html', 'budgets/send_email_en.html',
    'budgets/tiempos_en.html', 'budgets/version_en.html', 'clients/form_en.html',
    'clients/list_en.html', 'como_funciona_en.html', 'emails/alerta_operador_en.html',
    'emails/aviso_licencia_en.html', 'emails/compra_en.html', 'emails/demo_en.html',
    'emails/invitacion_en.html', 'emails/plan_activado_en.html', 'emails/presupuesto_en.html',
    'emails/recordatorio_vencimiento_en.html', 'emails/registro_en.html', 'emails/respuesta_propuesta_en.html',
    'emails/soporte_en.html', 'emails/venta_en.html', 'facturas/detail_en.html',
    'facturas/list_en.html', 'guia_rapida_en.html', 'importar_instalacion_en.html',
    'index_en.html', 'landing_en.html', 'legal/_base_legal_en.html',
    'legal/licencias_en.html', 'legal/preguntas_en.html', 'legal/privacidad_en.html',
    'legal/soporte_en.html', 'legal/terminos_en.html', 'mapa_sitio_en.html',
    'novedades_en.html', 'onboarding_en.html', 'pago/comprar_en.html',
    'pago/confirmacion_en.html', 'pago/exito_stripe_en.html', 'pago/mi_plan_en.html',
    'pago_en.html', 'partidas/_editor_en.html', 'partidas/_fila_en.html',
    'partidas/_thead_en.html', 'partidas/ajustar_preview_en.html', 'partidas/form_en.html',
    'partidas/list_en.html', 'planos/visor_en.html', 'plantillas/list_en.html',
    'productos/form_en.html', 'productos/list_en.html', 'projects/change_en.html',
    'projects/detail_en.html', 'projects/list_en.html', 'public/_nav_en.html',
    'public/proposal_en.html', 'public/proposal_unavailable_en.html', 'recetas/form_en.html',
    'recetas/list_en.html', 'recursos/form_en.html', 'recursos/impacto_en.html',
    'recursos/list_en.html', 'recursos/mercado_en.html', 'reports_en.html',
    'respaldo_en.html', 'search_en.html', 'seo_guia_en.html',
    'seo_hub_en.html', 'settings_en.html', 'soporte_en.html',
    'soporte_panel_en.html',
})


def test_no_nacen_gemelas_nuevas():
    actuales = {
        str(p.relative_to(PLANTILLAS)) for p in PLANTILLAS.rglob("*_en.html")
    }
    nuevas = actuales - GEMELAS_CONGELADAS
    assert not nuevas, (
        f"Gemelas _en nuevas: {sorted(nuevas)}. Desde la Fase 3 las "
        "plantillas nacen únicas usando el catálogo (app/locales) vía t()."
    )
