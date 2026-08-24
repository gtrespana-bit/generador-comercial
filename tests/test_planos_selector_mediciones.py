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
from app.routers import planos as router_planos
from app.services.planos_compat import ESQUEMA_PLANOS_LEGACY


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


def test_selector_autodetects_estancias_de_plano_dibujado_sin_mediciones(presupuesto_creado):
    """Un plano dibujado con muros trazados pero sin estancias detectadas se
    materializa solo al abrir el selector: el presupuesto ve los recintos sin
    que el usuario tenga que pasar por el editor a pulsar «Detectar»."""
    with TestClient(app) as client:
        resp = client.post(
            f"/presupuestos/{presupuesto_creado}/planos/blanco",
            json={"nombre": "Desde cero", "grosor_tabique_cm": 10},
        )
        assert resp.status_code == 200, resp.text
        plano_id = resp.json()["plano_id"]

        # Cuadrado cerrado de 4 muros (300 px = 3 m a escala 100 px/m).
        for puntos in (
            [[100, 100], [400, 100]],
            [[400, 100], [400, 400]],
            [[400, 400], [100, 400]],
            [[100, 400], [100, 100]],
        ):
            resp = client.post(
                f"/planos/{plano_id}/elementos",
                json={"tipo": "muro", "puntos": puntos, "grosor_cm": 10},
            )
            assert resp.status_code == 200, resp.text

        # Sin llamar a /detectar: el selector debe autodetectar la estancia.
        resp = client.get(f"/presupuestos/{presupuesto_creado}/planos/mediciones-selector")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        plano = next((p for p in data["planos"] if p["id"] == plano_id), None)
        assert plano is not None
        assert plano["total_muros"] == 4
        assert plano["mediciones"], "El selector debe materializar la estancia dibujada."
        opciones = {o["clave"]: o for o in plano["mediciones"][0]["opciones"]}
        assert opciones["suelo"]["cantidad"] == pytest.approx(8.41, abs=0.1)
        assert opciones["perimetro"]["cantidad"] == pytest.approx(11.6, abs=0.1)


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


def test_rutas_legacy_siguen_disponibles_y_escrituras_nuevas_devuelven_503(
    presupuesto_creado,
    monkeypatch,
):
    """Galerías, selector, datos, calibración y exportes sobreviven al desfase."""
    with TestClient(app) as client:
        respuesta = client.post(
            f"/presupuestos/{presupuesto_creado}/planos/upload",
            data={"nombre": "Plano legacy existente"},
            files={
                "archivo": (
                    "legacy.png",
                    _png_plano_con_habitacion(),
                    "image/png",
                )
            },
        )
        assert respuesta.status_code == 200, respuesta.text
        plano_id = respuesta.json()["plano_id"]
        respuesta = client.post(
            f"/planos/{plano_id}/mediciones",
            json={
                "tipo": "lineal",
                "etiqueta": "Muro existente",
                "puntos": [[0, 0], [100, 0]],
                "color": "#2563eb",
            },
        )
        assert respuesta.status_code == 200, respuesta.text

        # Desde aquí cada petición cree que ve exactamente el esquema físico
        # anterior a f1b2c3d4e5a6. Las opciones ``defer`` siguen actuando sobre
        # el ORM real, aunque SQLite conserve las columnas para el resto del CI.
        monkeypatch.setattr(
            router_planos,
            "detectar_esquema_planos",
            lambda _db: ESQUEMA_PLANOS_LEGACY,
        )

        listado = client.get(f"/presupuestos/{presupuesto_creado}/planos")
        assert listado.status_code == 200, listado.text
        assert "Actualización de planos pendiente" in listado.text
        assert "Plano legacy existente" in listado.text

        galeria = client.get("/planos")
        assert galeria.status_code == 200, galeria.text
        assert "Actualización de planos pendiente" in galeria.text

        selector = client.get(
            f"/presupuestos/{presupuesto_creado}/planos/mediciones-selector"
        )
        assert selector.status_code == 200, selector.text
        assert selector.json()["planos"][0]["grosor_tabique_cm"] == 10.0

        datos = client.get(f"/planos/{plano_id}/datos")
        assert datos.status_code == 200, datos.text
        assert datos.json()["plano"]["origen"] == "subido"
        assert datos.json()["elementos"] == []

        calibracion = client.post(
            f"/planos/{plano_id}/calibrar",
            json={
                "distancia_px": 100,
                "distancia_real": 1.0,
                "unidad": "m",
                "altura_libre_m": 2.5,
                "grosor_tabique_cm": 18,
            },
        )
        assert calibracion.status_code == 200, calibracion.text
        # La calibración histórica se guarda; solo se omite el grosor porque
        # esa columna no existe en el esquema simulado.
        assert calibracion.json()["escala_px_por_metro"] == 100.0
        assert calibracion.json()["grosor_tabique_cm"] == 10.0

        csv = client.get(f"/presupuestos/{presupuesto_creado}/planos/exportar")
        assert csv.status_code == 200, csv.text
        assert csv.headers["content-type"].startswith("text/csv")
        dxf = client.get(f"/planos/{plano_id}/exportar")
        assert dxf.status_code == 200, dxf.text
        assert dxf.headers["content-type"].startswith("application/dxf")

        respuestas_bloqueadas = (
            client.post(
                f"/presupuestos/{presupuesto_creado}/planos/upload",
                data={"nombre": "No disponible"},
                files={
                    "archivo": (
                        "nuevo.png",
                        _png_plano_con_habitacion(),
                        "image/png",
                    )
                },
            ),
            client.post(
                f"/presupuestos/{presupuesto_creado}/planos/blanco",
                json={"nombre": "No disponible"},
            ),
            client.post(
                f"/planos/{plano_id}/grosor",
                json={"grosor_tabique_cm": 18},
            ),
            client.post(
                f"/planos/{plano_id}/elementos",
                json={"tipo": "muro", "puntos": [[0, 0], [10, 0]]},
            ),
        )
        for bloqueada in respuestas_bloqueadas:
            assert bloqueada.status_code == 503, bloqueada.text
            assert bloqueada.json()["codigo"] == "migracion_planos_pendiente"
            assert bloqueada.headers["retry-after"] == "300"
