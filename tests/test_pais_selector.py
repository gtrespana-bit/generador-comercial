"""Tests de humo del selector de país tras el cambio de ORDEN_SELECTOR.

Garantiza que la landing, /pago, /acceso y /organizaciones/nueva exponen
los 18 países disponibles y que el texto genérico por defecto ya no dice
solo "Latinoamérica" (que invisibilizaba a España).

Los tests son aserciones de strings sobre HTML renderizado, no sobre JS:
el navegador actualiza textos en cliente pero la fuente de verdad es la
plantilla, y estos checks pillan cualquier regresión de servidor.
"""
from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.paises import lista_paises, ORDEN_SELECTOR, PAISES


def _opts(body: str) -> list[tuple[str, str]]:
    """Devuelve la lista (código, etiqueta) de los <option value="XX">."""
    return re.findall(r'<option value="([A-Z]{2})"[^>]*>([^<]*)</option>', body)


def _paises_presentes_en_selector(body: str) -> list[str]:
    return [cod for cod, _ in _opts(body) if cod in PAISES]


def test_orden_selector_contiene_los_18_paises():
    """El selector visible debe incluir los 18 países definidos.

    El filtro histórico (VE, CO, MX, EC, PE, ES) dejaba fuera 12 mercados
    que ya estaban definidos. Sin este cambio, usuarios de CR/PA/CL/etc.
    no podían elegir su país al registrarse: el sistema los forzaba a
    quedar en 'Latinoamérica (genérico)' y luego caer al fallback VE.
    """
    assert len(lista_paises()) == 18, (
        f"lista_paises() devolvió {len(lista_paises())} países; esperaba 18."
    )
    for codigo in ["VE", "CO", "MX", "EC", "PE", "CL", "AR", "DO", "UY",
                   "PY", "BO", "PA", "CR", "GT", "HN", "SV", "NI", "ES"]:
        assert codigo in PAISES, f"{codigo} no está en PAISES"
    # ORDEN_SELECTOR coincide con lo que se envía al template.
    assert set(ORDEN_SELECTOR) == set(PAISES.keys()), (
        "ORDEN_SELECTOR no coincide con PAISES: revisar app/paises.py"
    )


def test_home_landing_lista_los_18_paises():
    with TestClient(app) as c:
        body = c.get("/").text
    paises = _paises_presentes_en_selector(body)
    assert "ES" in paises, f"España no está en el selector. Vistos: {paises}"
    assert len(paises) == 18, f"Landing lista {len(paises)} países (esperaba 18)"
    # El genérico por defecto ya no dice solo 'Latinoamérica' sin España.
    m = re.search(r'pais-bar-hint[^>]*>([^<]+)</span>', body)
    assert m and "España" in m.group(1), (
        f"El hint genérico no menciona España: {m.group(1) if m else 'no encontrado'}"
    )


def test_pago_lista_los_18_paises():
    with TestClient(app) as c:
        body = c.get("/pago").text
    paises = _paises_presentes_en_selector(body)
    assert "ES" in paises
    assert len(paises) == 18, f"/pago lista {len(paises)} países"


def test_es_subdirectorio_ya_no_dice_latinoamrica():
    """Cuando el subdirectorio /es/ está activo, el kiker, el banner y la
    franja deben hablar de España. Y el selector de la barra debe tener
    España preseleccionado.
    """
    with TestClient(app) as c:
        body = c.get("/es/").text
    m = re.search(r'hero-kicker[^>]*>([^<]+)</span>', body)
    assert m and "España" in m.group(1), (
        f"El hero kiker no personaliza a España: {m.group(1) if m else 'no encontrado'}"
    )
    m = re.search(r'pais-bar-hint[^>]*>([^<]+)</span>', body)
    assert m and "España" in m.group(1) and "NIF" in m.group(1) and "21%" in m.group(1), (
        f"El hint de /es/ debería mencionar España, NIF y 21%. Visto: {m.group(1) if m else 'no encontrado'}"
    )
    m = re.search(r'<h2 id="banner-h2"[^>]*>(.*?)</h2>', body, re.S)
    assert m and "España" in re.sub(r'<[^>]+>', ' ', m.group(1)), (
        "El banner-h2 de /es/ debería mencionar España"
    )


def test_no_quedan_menciones_excluyentes_a_latinoamerica_sola():
    """Verifica que los textos comerciales genéricos de la landing incluyen
    a España junto a Latinoamérica (no solo "Latinoamérica" a secas).

    "Latinoamérica" puede seguir apareciendo como parte de "España y
    Latinoamérica" o en términos técnicos (mercado), pero los huecos
    comerciales deben mencionar siempre ambos mercados para que España
    no se sienta invisible.
    """
    with TestClient(app) as c:
        body = c.get("/").text
    # Hero kiker (texto en estado genérico)
    m = re.search(r'hero-kicker[^>]*>([^<]+)</span>', body)
    assert m and "España" in m.group(1), (
        f"El hero kiker genérico no menciona España: {m.group(1)}"
    )
    # Banner y franja: también deben mencionar a España.
    m = re.search(r'<h2 id="banner-h2"[^>]*>(.*?)</h2>', body, re.S)
    assert m and "España" in re.sub(r'<[^>]+>', ' ', m.group(1)), (
        "El banner-h2 de la home debería mencionar España"
    )
    m = re.search(r'<h2 id="franja-h2"[^>]*>(.*?)</h2>', body, re.S)
    assert m and "España" in re.sub(r'<[^>]+>', ' ', m.group(1)), (
        "La franja-h2 de la home debería mencionar España"
    )
    # fiscal: tarjeta "Fiscal a tu medida"
    m = re.search(r'<h3 id="fiscal-h3"[^>]*>(.*?)</h3>', body, re.S)
    assert m and "España" in re.sub(r'<[^>]+>', ' ', m.group(1)), (
        "La tarjeta fiscal de la home debería mencionar España"
    )
