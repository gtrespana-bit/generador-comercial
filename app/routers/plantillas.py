"""Plantillas de presupuesto."""  # E4-001 — router por dominio

from fastapi import APIRouter

from .common import *  # noqa: F401,F403  (re-exporta modelos, servicios y utilidades)

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
        return {"ok": False, "error": "El nombre es obligatorio."}
    if not datos:
        return {"ok": False, "error": "No hay datos que guardar."}
    try:
        json.loads(datos)  # validar que sea JSON
    except ValueError:
        return {"ok": False, "error": "Datos inválidos."}
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
def plantilla_datos(plantilla_id: int, db: Session = Depends(get_db)):
    plantilla = db.get(Plantilla, plantilla_id)
    if plantilla is None:
        return {"ok": False, "error": "Plantilla no encontrada."}
    try:
        return {"ok": True, "nombre": plantilla.nombre, "capitulos": json.loads(plantilla.datos or "[]")}
    except ValueError:
        return {"ok": False, "error": "Plantilla corrupta."}


@router.post("/plantillas/{plantilla_id}/eliminar")
def eliminar_plantilla(plantilla_id: int, db: Session = Depends(get_db)):
    plantilla = db.get(Plantilla, plantilla_id)
    if plantilla is None:
        return _redirect("/plantillas", error="Plantilla no encontrada.")
    db.delete(plantilla)
    db.commit()
    return _redirect("/plantillas", msg="Plantilla eliminada.")
