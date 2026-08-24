"""Test de integración para el endpoint mediciones-selector y los nuevos
endpoints de plano (grosor, plano en blanco, elementos vectoriales).

Los tests crean un cliente + presupuesto + plano **dentro del test**
usando el cliente HTTP (no acceso directo a la BD), porque la suite
comparte el archivo SQLite entre tests. Eso garantiza que cada test
trabaja con sus propios identificadores y que la presencia de datos
históricos de otros tests no afecta al resultado.
"""
from __future__ import annotations

import io
import uuid

import pytest
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient

from app.database import SessionLocal, init_db
from app.main import app
from app.models import (
    Cliente,
    PlanoObra,
    Presupuesto,
    asegurar_config,
    asegurar_organizacion_local,
)


def _png_plano_con_habitacion():
    img = Image.new("RGB", (300, 220), "white")
    d = ImageDraw.Draw(img)
    d.rectangle([60, 60, 240, 160], outline="black", width=6)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture()
def presupuesto_creado():
    """Crea cliente + presupuesto en SQLite y devuelve sus ids.

    Usa identificadores únicos (uuid) y un cliente HTTP para evitar
    colisiones con tests anteriores que comparten la misma base. Crea
    la fila con la organización activa del momento (en caso de que
    tests anteriores hayan cambiado ``db.info['organizacion_id']``).
    """
    init_db()
    with SessionLocal() as s:
        cfg = asegurar_config(s)
        s.commit()
        org_id = getattr(cfg, "organizacion_id", 1) or 1
        s.info["organizacion_id"] = org_id
        sufijo = uuid.uuid4().hex[:8]
        cliente = Cliente(nombre=f"Selector cliente {sufijo}", organizacion_id=org_id)
        s.add(cliente)
        s.flush()
        presupuesto = Presupuesto(
            numero=f"P-SEL-{sufijo}",
            year=2026,
            titulo="Test selector",
            client_id=cliente.id,
            organizacion_id=org_id,
        )
        s.add(presupuesto)
        s.commit()
        s.refresh(presupuesto)
        pid = presupuesto.id
        yield pid
        s.rollback()


def test_selector_devuelve_planos_y_mediciones(presupuesto_creado):
    """Un plano calibrado con una medición de tipo area debe aparecer en
    el selector con magnitudes reales (suelo, perímetro, paredes) ya en m²/m."""
    with TestClient(app) as client:
        # Subimos un plano
        resp = client.post(
            f"/presupuestos/{presupuesto_creado}/planos/upload",
            data={"nombre": "Cocina"},
            files={"archivo": ("cocina.png", _png_plano_con_habitacion(), "image/png")},
        )
        assert resp.status_code == 200, resp.text
        plano_id = resp.json()["plano_id"]

        # Calibramos el plano (1 m = 100 px) y le inyectamos una medición.
        resp = client.post(
            f"/planos/{plano_id}/calibrar",
            json={"distancia_px": 100, "distancia_real": 1.0, "unidad": "m", "altura_libre_m": 2.5, "grosor_tabique_cm": 12},
        )
        assert resp.status_code == 200, resp.text
        # La calibración no crea mediciones, las creamos por API.
        resp = client.post(
            f"/planos/{plano_id}/mediciones",
            json={"tipo": "area", "etiqueta": "Cocina", "puntos": [[0, 0], [100, 0], [100, 100], [0, 100]], "color": "#16a34a"},
        )
        assert resp.status_code == 200, resp.text

        # Selector
        resp = client.get(f"/presupuestos/{presupuesto_creado}/planos/mediciones-selector")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["ok"] is True
        assert data["planos"], "El selector debe devolver al menos un plano."
        plano = data["planos"][0]
        assert plano["calibrado"] is True
        assert plano["grosor_tabique_cm"] == 12
        assert plano["mediciones"], "El plano tiene una medición guardada."
        opciones = plano["mediciones"][0]["opciones"]
        claves = {o["clave"] for o in opciones}
        assert {"suelo", "paredes", "perimetro"} <= claves
        suelo = next(o for o in opciones if o["clave"] == "suelo")
        assert suelo["cantidad"] is not None and suelo["cantidad"] > 0


def test_selector_presupuesto_inexistente_devuelve_404_con_razon(presupuesto_creado):
    """El 404 del selector debe distinguir "no existe" de "no hay planos"."""
    with SessionLocal() as s:
        p = s.get(Presupuesto, presupuesto_creado)
        s.delete(p)
        s.commit()
    with TestClient(app) as client:
        resp = client.get(f"/presupuestos/{presupuesto_creado}/planos/mediciones-selector")
        assert resp.status_code == 404
        body = resp.json()
        assert body.get("razon") == "presupuesto_inexistente"
        assert body.get("ok") is False


def test_selector_sin_planos_incluye_diagnostico(presupuesto_creado):
    """Cuando el presupuesto existe pero no tiene planos, el selector lo
    dice con un diagnóstico claro (no el genérico 'sube un plano' del bug
    original)."""
    with TestClient(app) as client:
        resp = client.get(f"/presupuestos/{presupuesto_creado}/planos/mediciones-selector")
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["planos"] == []
        assert body["diagnostico"]["planos_en_presupuesto"] == 0


def test_crear_plano_en_blanco_devuelve_url(presupuesto_creado):
    with TestClient(app) as client:
        resp = client.post(
            f"/presupuestos/{presupuesto_creado}/planos/blanco",
            json={"nombre": "Mi plano", "ancho_lienzo_m": 10, "alto_lienzo_m": 6, "grosor_tabique_cm": 12},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["ok"] is True
        assert body["plano_id"] > 0
        assert "plano=" in body["url"]
        # Verificamos en BD que la fila está bien persistida.
        with SessionLocal() as s:
            plano = s.get(PlanoObra, body["plano_id"])
            assert plano is not None
            assert plano.origen == "dibujado"
            assert plano.grosor_tabique_cm == 12
            assert plano.ancho_lienzo_m == 10
            assert plano.alto_lienzo_m == 6


def test_actualizar_grosor_endpoint(presupuesto_creado):
    with TestClient(app) as client:
        resp = client.post(
            f"/presupuestos/{presupuesto_creado}/planos/upload",
            data={"nombre": "Test"},
            files={"archivo": ("t.png", _png_plano_con_habitacion(), "image/png")},
        )
        plano_id = resp.json()["plano_id"]
        resp = client.post(f"/planos/{plano_id}/grosor", json={"grosor_tabique_cm": 18})
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["grosor_tabique_cm"] == 18


def test_calibrar_acepta_grosor(presupuesto_creado):
    with TestClient(app) as client:
        resp = client.post(
            f"/presupuestos/{presupuesto_creado}/planos/upload",
            data={"nombre": "Test"},
            files={"archivo": ("t.png", _png_plano_con_habitacion(), "image/png")},
        )
        plano_id = resp.json()["plano_id"]
        resp = client.post(
            f"/planos/{plano_id}/calibrar",
            json={"distancia_px": 100, "distancia_real": 1.0, "unidad": "m", "altura_libre_m": 2.5, "grosor_tabique_cm": 20},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["grosor_tabique_cm"] == 20


def test_crear_y_actualizar_y_eliminar_elemento(presupuesto_creado):
    """Ciclo vectorial completo: muro + puerta + actualizar + eliminar."""
    with TestClient(app) as client:
        resp = client.post(
            f"/presupuestos/{presupuesto_creado}/planos/blanco",
            json={"nombre": "Vectorial", "ancho_lienzo_m": 10, "alto_lienzo_m": 8, "grosor_tabique_cm": 10},
        )
        plano_id = resp.json()["plano_id"]

        # Crear muro
        resp = client.post(
            f"/planos/{plano_id}/elementos",
            json={"tipo": "muro", "puntos": [[10, 10], [100, 10]], "grosor_cm": 12, "color": "#1f2937"},
        )
        assert resp.status_code == 200, resp.text
        elem = resp.json()["elemento"]
        assert elem["tipo"] == "muro"
        assert elem["grosor_cm"] == 12
        muro_id = elem["id"]

        # Crear puerta asociada
        resp = client.post(
            f"/planos/{plano_id}/elementos",
            json={"tipo": "hueco", "puntos": [[50, 5, "puerta", 60, 20]], "muro_id": muro_id},
        )
        assert resp.status_code == 200
        puerta = resp.json()["elemento"]
        assert puerta["muro_id"] == muro_id

        # Actualizar grosor del muro
        resp = client.put(
            f"/planos/{plano_id}/elementos/{muro_id}",
            json={"puntos": [[10, 10], [100, 10]], "grosor_cm": 18, "color": "#0f172a"},
        )
        assert resp.status_code == 200
        assert resp.json()["elemento"]["grosor_cm"] == 18

        # Datos del plano traen los 2 elementos
        resp = client.get(f"/planos/{plano_id}/datos")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["elementos"]) == 2
        assert body["plano"]["origen"] == "dibujado"
        assert body["plano"]["grosor_tabique_cm"] == 10
        assert body["plano"]["ancho_lienzo_m"] == 10
        assert body["plano"]["alto_lienzo_m"] == 8

        # Eliminar la puerta
        resp = client.delete(f"/planos/{plano_id}/elementos/{puerta['id']}")
        assert resp.status_code == 200
        # Eliminar el muro
        resp = client.delete(f"/planos/{plano_id}/elementos/{muro_id}")
        assert resp.status_code == 200

        # Comprobación final: el plano no tiene ya elementos
        resp = client.get(f"/planos/{plano_id}/datos")
        assert resp.json()["elementos"] == []
