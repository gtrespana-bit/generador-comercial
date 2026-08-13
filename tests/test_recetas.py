import json
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal, init_db
from app.models import RecetaEstancia

client = TestClient(app)


def test_recetas_endpoints():
    init_db()
    
    # 1. Verificar listado principal
    res = client.get("/recetas")
    assert res.status_code == 200
    assert "Packs de Estancia" in res.text
    assert "Baño Principal de Lujo" in res.text

    # 2. Verificar API listado JSON
    res_api = client.get("/recetas/api/list")
    assert res_api.status_code == 200
    data = res_api.json()
    assert data["ok"] is True
    recetas = data["recetas"]
    assert len(recetas) >= 6
    bano = next(r for r in recetas if "Baño Principal de Lujo" in r["nombre"])
    assert bano["cantidad_base_default"] == 8.0
    assert len(bano["items"]) == 12

    # 3. Crear nueva receta por POST
    items_demo = [
        {"nombre": "Demolición test", "unidad": "m²", "precio": 10.0, "tipo_calculo": "proporcional", "coeficiente": 1.0}
    ]
    res_post = client.post("/recetas/nueva", data={
        "nombre": "Estancia Prueba Automatizada",
        "descripcion": "Pack creado en test",
        "categoria": "Habitaciones",
        "unidad_base": "m²",
        "cantidad_base_default": "12.0",
        "datos": json.dumps(items_demo)
    }, follow_redirects=False)
    assert res_post.status_code in (302, 303)

    # Verificar en DB
    db = SessionLocal()
    try:
        r = db.query(RecetaEstancia).filter(RecetaEstancia.nombre == "Estancia Prueba Automatizada").first()
        assert r is not None
        assert r.cantidad_base_default == 12.0
        r_id = r.id
    finally:
        db.close()

    # 4. Verificar API detalle
    res_det = client.get(f"/recetas/api/{r_id}")
    assert res_det.status_code == 200
    det = res_det.json()
    assert det["ok"] is True
    assert det["receta"]["nombre"] == "Estancia Prueba Automatizada"

    # 5. Guardar desde capítulo vía API
    res_cap = client.post("/recetas/api/guardar-desde-capitulo", json={
        "nombre": "Cocina Guardada del Editor",
        "categoria": "Cocinas",
        "unidad_base": "m²",
        "cantidad_base_default": 10.0,
        "calcular_coeficientes": True,
        "items": [
            {"nombre": "Cerámica piso", "cantidad": 10.0, "precio": 45.0, "unidad": "m²"},
            {"nombre": "Grifería cocina", "cantidad": 1.0, "precio": 120.0, "unidad": "und"}
        ]
    })
    assert res_cap.status_code == 200
    res_cap_data = res_cap.json()
    assert res_cap_data["ok"] is True

    # 6. Duplicar y eliminar receta
    res_dup = client.post(f"/recetas/{r_id}/duplicar", follow_redirects=False)
    assert res_dup.status_code in (302, 303)

    # Ver edición GET / POST
    res_ed_get = client.get(f"/recetas/{r_id}/editar")
    assert res_ed_get.status_code == 200
    assert "Estancia Prueba Automatizada" in res_ed_get.text

    res_ed_post = client.post(f"/recetas/{r_id}/editar", data={
        "nombre": "Estancia Editada en Test",
        "descripcion": "Descripción cambiada",
        "categoria": "Habitaciones",
        "unidad_base": "m²",
        "cantidad_base_default": "15.0",
        "datos": json.dumps([
            {"nombre": "Partida 1 editada", "unidad": "m²", "precio": 12.0, "tipo_calculo": "proporcional", "coeficiente": 1.0}
        ])
    }, follow_redirects=False)
    assert res_ed_post.status_code in (302, 303)

    # 7. Buscar receta en búsqueda global
    res_busc = client.get("/buscar?q=Editada")
    assert res_busc.status_code == 200
    assert "Packs de Estancia" in res_busc.text
    assert "Estancia Editada en Test" in res_busc.text

    # 8. Restaurar presets de demo
    res_rest = client.post("/recetas/restaurar-demo", follow_redirects=False)
    assert res_rest.status_code in (302, 303)

    res_del = client.post(f"/recetas/{r_id}/eliminar", follow_redirects=False)
    assert res_del.status_code in (302, 303)
