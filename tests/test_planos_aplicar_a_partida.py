"""Regresión: enviar medidas del plano a una partida y budget_id en el editor.

Cubre los tres fallos reportados por el usuario:

1. La página de edición del presupuesto no exponía ``window.BUDGET_ID``
   (siempre ``null``), así que el selector «📐 Añadir desde plano» nunca
   llegaba a pedir las mediciones y mostraba mensajes engañosos.
2. «Enviar a partida» desde el visor aplicaba siempre el valor crudo
   guardado (el suelo), sin dejar elegir perímetro, suelo o paredes, y sin
   confirmar qué se había enviado ni a dónde.
3. Enviar una medida incompatible pasaba desapercibido: ahora la respuesta
   trae un aviso suave de unidades y un concepto autoexplicativo.
"""
from __future__ import annotations

import io
import json
import uuid

import pytest
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient

from app.database import SessionLocal, init_db
from app.main import app
from app.models import (
    Capitulo,
    Cliente,
    PlanoMedicion,
    Presupuesto,
    PresupuestoItem,
    asegurar_config,
)


def _png_plano() -> bytes:
    img = Image.new("RGB", (320, 240), "white")
    d = ImageDraw.Draw(img)
    d.rectangle([40, 40, 280, 200], outline="black", width=5)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture()
def presupuesto_con_partidas():
    """Cliente + presupuesto con dos partidas reales (m² y m)."""
    init_db()
    with SessionLocal() as s:
        cfg = asegurar_config(s)
        s.commit()
        org_id = getattr(cfg, "organizacion_id", 1) or 1
        s.info["organizacion_id"] = org_id
        sufijo = uuid.uuid4().hex[:8]
        cliente = Cliente(nombre=f"Aplicar cliente {sufijo}", organizacion_id=org_id)
        s.add(cliente)
        s.flush()
        presupuesto = Presupuesto(
            numero=f"P-APL-{sufijo}",
            year=2026,
            titulo="Obra con planos",
            client_id=cliente.id,
            organizacion_id=org_id,
        )
        s.add(presupuesto)
        s.flush()
        cap = Capitulo(
            nombre="Capítulo de prueba",
            orden=1,
            presupuesto_id=presupuesto.id,
            organizacion_id=org_id,
        )
        s.add(cap)
        s.flush()
        pintura = PresupuestoItem(
            nombre="Pintura paredes lisas",
            unidad="m2",
            cantidad=1.0,
            precio_unitario=8.0,
            capitulo_id=cap.id,
            organizacion_id=org_id,
        )
        rodapie = PresupuestoItem(
            nombre="Rodapié cerámico",
            unidad="ml",
            cantidad=1.0,
            precio_unitario=4.0,
            capitulo_id=cap.id,
            organizacion_id=org_id,
        )
        s.add_all([pintura, rodapie])
        s.commit()
        s.refresh(presupuesto)
        s.refresh(pintura)
        s.refresh(rodapie)
        ids = (presupuesto.id, pintura.id, rodapie.id)
        yield ids
        s.rollback()


def _plano_calibrado_con_salon(client: TestClient, presupuesto_id: int) -> tuple[int, int]:
    """Sube un plano, lo calibra (1 m = 100 px) y guarda «Salón» 3 m × 3 m.

    Devuelve (plano_id, medicion_id). Con altura 2,5 m la estancia da:
    suelo 9 m², perímetro 12 m, paredes 30 m².
    """
    resp = client.post(
        f"/presupuestos/{presupuesto_id}/planos/upload",
        data={"nombre": "Planta baja"},
        files={"archivo": ("planta.png", _png_plano(), "image/png")},
    )
    assert resp.status_code == 200, resp.text
    plano_id = resp.json()["plano_id"]
    resp = client.post(
        f"/planos/{plano_id}/calibrar",
        json={"distancia_px": 100, "distancia_real": 1.0, "unidad": "m", "altura_libre_m": 2.5},
    )
    assert resp.status_code == 200, resp.text
    resp = client.post(
        f"/planos/{plano_id}/mediciones",
        json={
            "tipo": "area",
            "etiqueta": "Salón",
            "puntos": [[0, 0], [300, 0], [300, 300], [0, 300]],
            "color": "#16a34a",
        },
    )
    assert resp.status_code == 200, resp.text
    medicion = resp.json()["medicion"]
    assert medicion["valor"] == pytest.approx(9.0)
    return plano_id, medicion["id"]


# ---------------------------------------------------------------------------
# 1. El editor de un presupuesto existente expone su id al JavaScript
# ---------------------------------------------------------------------------

def test_editor_presupuesto_expone_budget_id(presupuesto_con_partidas):
    presupuesto_id, _, _ = presupuesto_con_partidas
    with TestClient(app) as client:
        resp = client.get(f"/presupuestos/{presupuesto_id}/editar")
    assert resp.status_code == 200, resp.text[:500]
    # Antes llegaba "null" incluso con presupuesto guardado y el selector de
    # planos no podía funcionar ni enlazar a la página de Planos.
    assert f"window.BUDGET_ID = {presupuesto_id};" in resp.text


def test_editor_nuevo_presupuesto_arranca_sin_budget_id():
    with TestClient(app) as client:
        resp = client.get("/presupuestos/nuevo")
    assert resp.status_code == 200, resp.text[:500]
    assert "window.BUDGET_ID = null;" in resp.text


# ---------------------------------------------------------------------------
# 2. Enviar a partida respeta la magnitud elegida por el usuario
# ---------------------------------------------------------------------------

def test_aplicar_permite_elegir_superficie_de_paredes(presupuesto_con_partidas):
    presupuesto_id, pintura_id, _ = presupuesto_con_partidas
    with TestClient(app) as client:
        plano_id, medicion_id = _plano_calibrado_con_salon(client, presupuesto_id)
        resp = client.post(
            f"/planos/{plano_id}/mediciones/{medicion_id}/aplicar",
            json={"partida_id": pintura_id, "magnitud": "paredes"},
        )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["ok"] is True
    assert data["cantidad"] == pytest.approx(30.0)
    assert data["unidad"] == "m2"
    assert data["magnitud"] == "paredes"
    assert data["concepto"] == "Planta baja · Salón · Superficie de paredes"
    assert data["partida_nombre"] == "Pintura paredes lisas"
    assert data["aviso"] == ""
    # La medición queda persistida en el desglose de la partida destino.
    with SessionLocal() as s:
        fila = s.get(PlanoMedicion, medicion_id)
        assert fila.partida_destino_id == pintura_id
        partida = s.get(PresupuestoItem, pintura_id)
        cantidades = [m.cantidad for m in partida.mediciones]
        assert 30.0 in cantidades


def test_aplicar_permite_elegir_perimetro_y_avisa_unidad_distinta(presupuesto_con_partidas):
    presupuesto_id, pintura_id, _ = presupuesto_con_partidas
    with TestClient(app) as client:
        plano_id, medicion_id = _plano_calibrado_con_salon(client, presupuesto_id)
        resp = client.post(
            f"/planos/{plano_id}/mediciones/{medicion_id}/aplicar",
            json={"partida_id": pintura_id, "magnitud": "perimetro"},
        )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["ok"] is True
    assert data["cantidad"] == pytest.approx(12.0)
    assert data["unidad"] == "m"
    # La partida está en m²: el envío se hace (queda editable), pero el
    # usuario recibe un aviso claro de la diferencia de unidades.
    assert "m" in data["aviso"] and "m2" in data["aviso"]


def test_aplicar_perimetro_a_partida_en_metros_no_avisa(presupuesto_con_partidas):
    presupuesto_id, _, rodapie_id = presupuesto_con_partidas
    with TestClient(app) as client:
        plano_id, medicion_id = _plano_calibrado_con_salon(client, presupuesto_id)
        resp = client.post(
            f"/planos/{plano_id}/mediciones/{medicion_id}/aplicar",
            json={"partida_id": rodapie_id, "magnitud": "perimetro"},
        )
    data = resp.json()
    assert data["ok"] is True
    assert data["cantidad"] == pytest.approx(12.0)
    assert data["aviso"] == ""


def test_aplicar_suelo_y_compatibilidad_sin_magnitud(presupuesto_con_partidas):
    presupuesto_id, pintura_id, _ = presupuesto_con_partidas
    with TestClient(app) as client:
        plano_id, medicion_id = _plano_calibrado_con_salon(client, presupuesto_id)
        resp = client.post(
            f"/planos/{plano_id}/mediciones/{medicion_id}/aplicar",
            json={"partida_id": pintura_id, "magnitud": "suelo"},
        )
        assert resp.json()["cantidad"] == pytest.approx(9.0)
        # Compatibilidad con clientes antiguos: sin magnitud se usa el valor
        # guardado (para un área, su suelo).
        resp = client.post(
            f"/planos/{plano_id}/mediciones/{medicion_id}/aplicar",
            json={"partida_id": pintura_id},
        )
        data = resp.json()
        assert data["ok"] is True
        assert data["cantidad"] == pytest.approx(9.0)
        assert data["magnitud"] == "valor"


def test_aplicar_rechaza_magnitud_inventada_y_ccero(presupuesto_con_partidas):
    presupuesto_id, pintura_id, _ = presupuesto_con_partidas
    with TestClient(app) as client:
        plano_id, medicion_id = _plano_calibrado_con_salon(client, presupuesto_id)
        resp = client.post(
            f"/planos/{plano_id}/mediciones/{medicion_id}/aplicar",
            json={"partida_id": pintura_id, "magnitud": "volumen"},
        )
        assert resp.status_code == 400
        assert "Magnitud" in resp.json()["error"]


# ---------------------------------------------------------------------------
# 3. Sin calibrar no se envían medidas fantasma (era «lo que le da la gana»)
# ---------------------------------------------------------------------------

def test_aplicar_area_sin_calibrar_exige_calibraje(presupuesto_con_partidas):
    presupuesto_id, pintura_id, _ = presupuesto_con_partidas
    with TestClient(app) as client:
        resp = client.post(
            f"/presupuestos/{presupuesto_id}/planos/upload",
            data={"nombre": "Sin calibrar"},
            files={"archivo": ("planta.png", _png_plano(), "image/png")},
        )
        plano_id = resp.json()["plano_id"]
        resp = client.post(
            f"/planos/{plano_id}/mediciones",
            json={"tipo": "area", "etiqueta": "Zona", "puntos": [[0, 0], [50, 0], [50, 50], [0, 50]], "color": "#16a34a"},
        )
        medicion_id = resp.json()["medicion"]["id"]
        resp = client.post(
            f"/planos/{plano_id}/mediciones/{medicion_id}/aplicar",
            json={"partida_id": pintura_id, "magnitud": "paredes"},
        )
        assert resp.status_code == 400
        assert "Calibra" in resp.json()["error"]


def test_aplicar_lineal_sin_calibrar_exige_calibraje_pero_conteo_no(presupuesto_con_partidas):
    presupuesto_id, pintura_id, rodapie_id = presupuesto_con_partidas
    with TestClient(app) as client:
        resp = client.post(
            f"/presupuestos/{presupuesto_id}/planos/upload",
            data={"nombre": "Sin calibrar 2"},
            files={"archivo": ("planta.png", _png_plano(), "image/png")},
        )
        plano_id = resp.json()["plano_id"]
        resp = client.post(
            f"/planos/{plano_id}/mediciones",
            json={"tipo": "lineal", "etiqueta": "Muro", "puntos": [[0, 0], [80, 0]], "color": "#16a34a"},
        )
        lineal_id = resp.json()["medicion"]["id"]
        resp = client.post(
            f"/planos/{plano_id}/mediciones/{lineal_id}/aplicar",
            json={"partida_id": rodapie_id},
        )
        assert resp.status_code == 400
        assert "Calibra" in resp.json()["error"]

        resp = client.post(
            f"/planos/{plano_id}/mediciones",
            json={"tipo": "conteo", "etiqueta": "Puntos de luz", "puntos": [[10, 10], [20, 20], [30, 30]], "color": "#16a34a"},
        )
        conteo_id = resp.json()["medicion"]["id"]
        resp = client.post(
            f"/planos/{plano_id}/mediciones/{conteo_id}/aplicar",
            json={"partida_id": pintura_id},
        )
        data = resp.json()
        assert data["ok"] is True
        assert data["cantidad"] == pytest.approx(3.0)
        assert data["unidad"] == "ud"


def test_aplicar_partida_de_otro_presupuesto_sigue_rechazada(presupuesto_con_partidas):
    presupuesto_id, pintura_id, _ = presupuesto_con_partidas
    with TestClient(app) as client:
        plano_id, medicion_id = _plano_calibrado_con_salon(client, presupuesto_id)
        resp = client.post(
            f"/planos/{plano_id}/mediciones/{medicion_id}/aplicar",
            json={"partida_id": 999999, "magnitud": "suelo"},
        )
        assert resp.status_code == 400
