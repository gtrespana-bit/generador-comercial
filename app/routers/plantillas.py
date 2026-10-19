"""Plantillas de presupuesto."""  # E4-001 — router por dominio

from fastapi import APIRouter, Request

from .common import *  # noqa: F401,F403  (re-exporta modelos, servicios y utilidades)
from ..i18n import mensaje_request

router = APIRouter()

# ---------------------------------------------------------------------------
# Plantillas de presupuesto
# ---------------------------------------------------------------------------

@router.get("/plantillas", response_class=HTMLResponse)
def listar_plantillas(request: Request, db: Session = Depends(get_db)):
    plantillas = db.query(Plantilla).order_by(Plantilla.nombre).all()
    return TEMPLATES.TemplateResponse(request, "plantillas/list.html", {"plantillas": plantillas})


@router.post("/plantillas")
async def guardar_plantilla(request: Request, db: Session = Depends(get_db)):
    """Guarda la estructura actual del constructor como plantilla."""
    form = await request.form()
    nombre = str(form.get("nombre", "")).strip()
    datos = str(form.get("datos", "")).strip()
    if not nombre:
        return {"ok": False, "error": mensaje_request(request, "El nombre es obligatorio.")}
    if not datos:
        return {"ok": False, "error": mensaje_request(request, "No hay datos que guardar.")}
    try:
        estructura = json.loads(datos)  # validar que sea JSON
    except ValueError:
        return {"ok": False, "error": mensaje_request(request, "Datos inválidos.")}
    # La plantilla se guarda en métrico como todo lo persistente: si el
    # editor trabajaba en imperial («sq ft»), sus partidas se normalizan
    # aquí y al cargarla se vuelve a convertir según el mercado de turno.
    try:
        if isinstance(estructura, list):
            from ..services.unidades_precio import normalizar_partida_a_metrico

            for _cap in estructura:
                if isinstance(_cap, dict):
                    for _pd in _cap.get("partidas") or []:
                        normalizar_partida_a_metrico(_pd)
            datos = json.dumps(estructura, ensure_ascii=False)
    except Exception:
        pass
    existente = db.query(Plantilla).filter(Plantilla.nombre == nombre).first()
    if existente:
        existente.datos = datos
        plantilla = existente
    else:
        plantilla = Plantilla(nombre=nombre, datos=datos)
        db.add(plantilla)
    db.commit()
    return {"ok": True, "id": plantilla.id, "nombre": plantilla.nombre}


@router.get("/plantillas/{plantilla_id}/datos")
def plantilla_datos(request: Request, plantilla_id: int, db: Session = Depends(get_db)):
    plantilla = db.get(Plantilla, plantilla_id)
    if plantilla is None:
        return {"ok": False, "error": mensaje_request(request, "Plantilla no encontrada.")}
    try:
        capitulos = json.loads(plantilla.datos or "[]")
    except ValueError:
        return {"ok": False, "error": mensaje_request(request, "Plantilla corrupta.")}
    try:
        from ..services.unidades_precio import (
            capitulos_editor_a_mostrada,
            es_imperial_config,
        )

        capitulos = capitulos_editor_a_mostrada(
            capitulos, es_imperial_config(_config(db))
        )
    except Exception:
        pass
    return {"ok": True, "nombre": plantilla.nombre, "capitulos": capitulos}


@router.post("/plantillas/{plantilla_id}/eliminar")
def eliminar_plantilla(plantilla_id: int, db: Session = Depends(get_db)):
    plantilla = db.get(Plantilla, plantilla_id)
    if plantilla is None:
        return _redirect("/plantillas", error="Plantilla no encontrada.")
    db.delete(plantilla)
    db.commit()
    return _redirect("/plantillas", msg="Plantilla eliminada.")
