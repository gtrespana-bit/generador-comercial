"""Tests del wizard de bienvenida tras exponer los 18 países y monedas.

Garantiza que el select de país y el select de moneda del wizard de alta
de empresa (``/bienvenida``) exponen todos los mercados y monedas
disponibles, no un subconjunto hardcodeado.

Regresión: el select listaba solo 5 países (VE/CO/MX/EC/PE) y 5 monedas
(USD/COP/MXN/PEN/VES), por lo que un usuario en España no podía elegir su
país al crear la organización desde el wizard — tenía que hacerlo a mano
desde /configuracion después.
"""
from __future__ import annotations

import json as _json
import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.database import engine
from app.main import app
from app.models import Configuracion


def _opts_de_select(body: str, select_id: str) -> list[tuple[str, str]]:
    """Devuelve la lista (valor, etiqueta) de los <option> de un select."""
    m = re.search(
        r'<select[^>]*id="' + re.escape(select_id) + r'".*?</select>',
        body,
        re.S,
    )
    assert m, f"No encontré el select #{select_id} en /bienvenida"
    return re.findall(
        r'<option[^>]*value="([^"]+)"[^>]*>([^<]*)</option>',
        m.group(0),
    )


def test_bienvenida_lista_los_18_paises_en_el_select(entorno, cliente_web):
    """El select de país del wizard de bienvenida expone los 18 países.

    Regresión: solo listaba 5 (VE/CO/MX/EC/PE). Ahora aparece la lista
    completa incluyendo España, Chile, Argentina y el resto de LatAm.
    """
    Session, _ids, _rol = entorno
    with Session() as db:
        cfg = db.query(Configuracion).first()
        cfg.onboarding_completado = False
        db.commit()
    resp = cliente_web.get("/bienvenida", follow_redirects=False)
    assert resp.status_code == 200, resp.text[:500]
    opts = _opts_de_select(resp.text, "empresa_pais")
    nombres = [l for _v, l in opts]
    for pais in (
        "🇻🇪 Venezuela", "🇨🇴 Colombia", "🇲🇽 México", "🇪🇨 Ecuador",
        "🇵🇪 Perú", "🇨🇱 Chile", "🇦🇷 Argentina", "🇩🇴 República Dominicana",
        "🇺🇾 Uruguay", "🇵🇾 Paraguay", "🇧🇴 Bolivia", "🇵🇦 Panamá",
        "🇨🇷 Costa Rica", "🇬🇹 Guatemala", "🇭🇳 Honduras", "🇸🇻 El Salvador",
        "🇳🇮 Nicaragua", "🇪🇸 España",
    ):
        assert pais in nombres, (
            f"Falta {pais} en el select de /bienvenida. Vistos: {nombres}"
        )
    assert len(nombres) == len(set(nombres)), f"Hay duplicados en {nombres}"


def test_bienvenida_lista_las_monedas_completas(entorno, cliente_web):
    """El select de moneda del wizard expone las monedas completas.

    Regresión: solo había 5 hardcodeadas (USD/COP/MXN/PEN/VES), por lo
    que España no podía elegir EUR al darse de alta.
    """
    Session, _ids, _rol = entorno
    with Session() as db:
        cfg = db.query(Configuracion).first()
        cfg.onboarding_completado = False
        db.commit()
    resp = cliente_web.get("/bienvenida", follow_redirects=False)
    assert resp.status_code == 200, resp.text[:500]
    opts = _opts_de_select(resp.text, "moneda_default")
    valores = [v for v, _l in opts]
    # Monedas mínimas: USD (referencia), EUR (España), y las LatAm con
    # mercado en la lista de países.
    for m in ("USD", "EUR", "COP", "MXN", "PEN", "CLP", "ARS", "VES"):
        assert m in valores, f"Falta la moneda {m} en /bienvenida. Vistas: {valores}"


def test_bienvenida_tasa_eur_esta_disponible_en_el_json(entorno, cliente_web):
    """El JSON de tasas inyectado al wizard incluye la tasa EUR verificada
    (≈ 0.8564), para que el placeholder del campo tasa se personalice al
    elegir España.
    """
    Session, _ids, _rol = entorno
    with Session() as db:
        cfg = db.query(Configuracion).first()
        cfg.onboarding_completado = False
        db.commit()
    resp = cliente_web.get("/bienvenida", follow_redirects=False)
    assert resp.status_code == 200, resp.text[:500]
    m = re.search(r'<script id="tasas-data"[^>]*>(.*?)</script>', resp.text, re.S)
    assert m, "No se inyectó el JSON de tasas en /bienvenida"
    tasas = _json.loads(m.group(1))
    assert "EUR" in tasas and tasas["EUR"] == pytest.approx(0.8564), (
        f"Se esperaba EUR=0.8564 en TASAS_SUGERIDAS, visto: {tasas.get('EUR')}"
    )


def test_bienvenida_tiene_boton_tasa_de_hoy(entorno, cliente_web):
    """El wizard de bienvenida incluye un botón «Tasa de hoy» que consulta
    la API /configuracion/tasa-auto para la moneda actual (regression del
    fix de tasa dinámica).
    """
    Session, _ids, _rol = entorno
    with Session() as db:
        cfg = db.query(Configuracion).first()
        cfg.onboarding_completado = False
        db.commit()
    resp = cliente_web.get("/bienvenida", follow_redirects=False)
    assert resp.status_code == 200, resp.text[:500]
    assert 'id="btn-tasa-auto-onb"' in resp.text, (
        "Falta el botón «Tasa de hoy» en el wizard de /bienvenida"
    )
    assert "/configuracion/tasa-auto" in resp.text, (
        "El handler del botón no apunta a /configuracion/tasa-auto"
    )


def test_bienvenida_generico_dice_espana_y_latinoamerica(entorno, cliente_web):
    """El genérico del select de país enuncia el mercado completo.

    Antes decía 'Latinoamérica' (invisibilizando a España). Ahora dice
    'España y Latinoamérica' y mercado 'iberoamericano'.
    """
    Session, _ids, _rol = entorno
    with Session() as db:
        cfg = db.query(Configuracion).first()
        cfg.onboarding_completado = False
        db.commit()
    resp = cliente_web.get("/bienvenida", follow_redirects=False)
    assert resp.status_code == 200
    m = re.search(
        r'<script id="pais-generico-data"[^>]*>(.*?)</script>',
        resp.text,
        re.S,
    )
    assert m
    generico = _json.loads(m.group(1))
    assert generico["nombre"] == "España y Latinoamérica"
    assert generico["mercado"] == "iberoamericano"


def test_landing_18_subdirectorios_responden_y_personalizan(cliente_web):
    """Los 18 países tienen subdirectorio canónico /XX/ que responde 200 y
    personaliza el hero-kicker con el nombre del país. Antes solo 6
    (ve/co/mx/ec/pe/es) lo tenían; el resto caía en 404.
    """
    import re as _re
    esperados = {
        "ve": "Venezuela", "co": "Colombia", "mx": "México", "ec": "Ecuador",
        "pe": "Perú", "cl": "Chile", "ar": "Argentina",
        "do": "República Dominicana", "uy": "Uruguay", "py": "Paraguay",
        "bo": "Bolivia", "pa": "Panamá", "cr": "Costa Rica",
        "gt": "Guatemala", "hn": "Honduras", "sv": "El Salvador",
        "ni": "Nicaragua", "es": "España",
    }
    for subdir, nombre in esperados.items():
        resp = cliente_web.get(f"/{subdir}/", follow_redirects=False)
        assert resp.status_code == 200, (
            f"/{subdir}/ devolvió {resp.status_code}, esperaba 200"
        )
        m = _re.search(r'hero-kicker[^>]*>([^<]+)</span>', resp.text)
        assert m, f"/{subdir}/ no tiene hero-kicker"
        assert nombre in m.group(1), (
            f"/{subdir}/ no personaliza a {nombre}: {m.group(1)}"
        )
