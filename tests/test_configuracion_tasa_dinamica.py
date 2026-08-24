"""Tests de la tasa dinámica en /configuracion.

El selector de tasa debe actualizarse al cambiar país o moneda, no
quedarse con el placeholder/label de la moneda anterior. Antes de este
fix, el placeholder seguía siendo el de la moneda anterior y la persona
veía una sugerencia que no correspondía con su moneda actual.
"""
from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient


def _moneda_placeholder_para(body: str) -> str | None:
    """Devuelve el placeholder actual del input de tasa."""
    m = re.search(
        r'<input[^>]*id="input-tasa"[^>]*placeholder="([^"]+)"',
        body,
    )
    return m.group(1) if m else None


def _moneda_label_para(body: str) -> str | None:
    """Devuelve el texto del label de moneda (Tasa de referencia USD → XXX)."""
    m = re.search(
        r'<span[^>]*id="label-tasa-moneda"[^>]*>([^<]+)</span>',
        body,
    )
    return m.group(1) if m else None


def test_settings_placeholder_tasa_coincide_con_moneda_inicial(entorno, cliente_web):
    """Al renderizar la página, el placeholder del input de tasa debe
    corresponder a la moneda configurada (no a una hardcodeada)."""
    Session, _ids, _rol = entorno
    with Session() as db:
        cfg = db.query(__import__("app").models.Configuracion).first()
        cfg.moneda_default = "COP"
        cfg.tasa_cambio = 3128.65
        db.commit()
    resp = cliente_web.get("/configuracion")
    assert resp.status_code == 200
    placeholder = _moneda_placeholder_para(resp.text)
    assert placeholder and "3128.65" in placeholder, (
        f"El placeholder de la tasa para COP debería mencionar 3128.65. "
        f"Visto: {placeholder!r}"
    )
    label = _moneda_label_para(resp.text)
    assert label == "COP", f"El label debería ser COP, visto: {label!r}"


def test_settings_placeholder_tasa_eur(entorno, cliente_web):
    """Para España/EUR el placeholder del input de tasa debe usar la
    tasa verificada de EUR (≈0.8564), no 1.0 de USD ni la del COP.
    """
    Session, _ids, _rol = entorno
    with Session() as db:
        cfg = db.query(__import__("app").models.Configuracion).first()
        cfg.empresa_pais = "España"
        cfg.etiqueta_id_fiscal = "NIF"
        cfg.moneda_default = "EUR"
        cfg.iva_default = 21
        cfg.tasa_cambio = 0.8564
        db.commit()
    resp = cliente_web.get("/configuracion")
    assert resp.status_code == 200
    placeholder = _moneda_placeholder_para(resp.text)
    assert placeholder and "0.8564" in placeholder, (
        f"El placeholder para EUR debería mencionar 0.8564. Visto: {placeholder!r}"
    )
    label = _moneda_label_para(resp.text)
    assert label == "EUR", f"El label debería ser EUR, visto: {label!r}"


def test_settings_hint_tasa_se_inicializa_en_render(entorno, cliente_web):
    """El hint de la tasa (#hint-tasa) debe mostrar el mensaje inicial
    para la moneda configurada, no quedarse vacío.
    """
    Session, _ids, _rol = entorno
    with Session() as db:
        cfg = db.query(__import__("app").models.Configuracion).first()
        cfg.moneda_default = "COP"
        cfg.tasa_cambio = 3128.65
        db.commit()
    resp = cliente_web.get("/configuracion")
    assert resp.status_code == 200
    # El JS escribe el hintTasa en runtime, así que en el HTML renderizado
    # sólo necesitamos asegurar que existe el elemento. Verificamos que
    # el JS contiene la función que lo actualiza y el selector.
    assert 'id="hint-tasa"' in resp.text
    assert 'function refrescarTasaPorMoneda' in resp.text, (
        "Falta la función refrescarTasaPorMoneda en /configuracion"
    )
    assert 'function hintParaMoneda' in resp.text


def test_settings_pais_selector_acepta_los_18_codigos_en_popstate(
    entorno, cliente_web
):
    """El JS de /configuracion (compartido con landing) debe detectar
    cualquier código de país en el popstate. Antes solo aceptaba 6
    (ve|co|mx|ec|pe|es), invisibilizando CL/AR/DO/UY/PY/BO/PA/CR/GT/
    HN/SV/NI en la barra.
    """
    import re as _re
    from pathlib import Path

    js_path = Path(__file__).parent.parent / "app" / "static" / "js" / "pais_selector.js"
    src = js_path.read_text(encoding="utf-8")
    # Quita comentarios para que la asserción no se confunda con menciones
    # dentro de un comentario que explica el cambio.
    src_sin_comentarios = _re.sub(r"//[^\n]*", "", src)
    # El regex de popstate debe construirse dinámicamente desde los países
    # disponibles (Object.keys(mapa).join('|')), no hardcodear 6 códigos.
    assert "ve|co|mx|ec|pe|es" not in src_sin_comentarios, (
        "El popstate de pais_selector.js sigue hardcodeando 6 códigos"
    )
    # Y debe construir el regex desde los códigos reales
    assert "Object.keys(mapa).join" in src, (
        "El popstate no construye el regex desde los códigos disponibles"
    )
