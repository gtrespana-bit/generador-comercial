"""Recetas / packs de estancia."""  # E4-001 — router por dominio

from fastapi import APIRouter

from .common import *  # noqa: F401,F403  (re-exporta modelos, servicios y utilidades)

router = APIRouter()

# ---------------------------------------------------------------------------
# Recetas / Packs de Estancia (Armado de capítulos con 1 clic - Fase 12)
# ---------------------------------------------------------------------------

@router.get("/recetas", response_class=HTMLResponse)
def listar_recetas(request: Request, db: Session = Depends(get_db)):
    recetas = db.query(RecetaEstancia).order_by(RecetaEstancia.categoria, RecetaEstancia.nombre).all()
    categorias = {}
    for r in recetas:
        cat = r.categoria or "Otros"
        if cat not in categorias:
            categorias[cat] = []
        try:
            items_cnt = len(json.loads(r.datos or "[]"))
        except Exception:
            items_cnt = 0
        r.items_cnt = items_cnt
        categorias[cat].append(r)
    return TEMPLATES.TemplateResponse(request, "recetas/list.html", {
        "recetas": recetas,
        "categorias": categorias,
    })


@router.get("/recetas/nueva", response_class=HTMLResponse)
def nueva_receta_form(request: Request, _db: Session = Depends(get_db)):
    return TEMPLATES.TemplateResponse(request, "recetas/form.html", {
        "receta": None,
        "items": [],
    })


@router.post("/recetas/nueva")
async def crear_receta(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    nombre = str(form.get("nombre", "")).strip()
    descripcion = str(form.get("descripcion", "")).strip()
    categoria = str(form.get("categoria", "")).strip() or "Baños"
    unidad_base = str(form.get("unidad_base", "")).strip() or "m²"
    try:
        cantidad_base = float(form.get("cantidad_base_default", 10.0) or 10.0)
    except ValueError:
        cantidad_base = 10.0
    datos = str(form.get("datos", "[]")).strip()
    if not nombre:
        return _redirect("/recetas/nueva", error="El nombre del pack es obligatorio.")
    try:
        json.loads(datos)
    except Exception:
        datos = "[]"
    receta = RecetaEstancia(
        nombre=nombre,
        descripcion=descripcion,
        categoria=categoria,
        unidad_base=unidad_base,
        cantidad_base_default=cantidad_base,
        datos=datos,
    )
    db.add(receta)
    db.commit()
    return _redirect("/recetas", msg="✅ Pack de estancia creado correctamente.")


@router.get("/recetas/{receta_id}/editar", response_class=HTMLResponse)
def editar_receta_form(request: Request, receta_id: int, db: Session = Depends(get_db)):
    receta = db.get(RecetaEstancia, receta_id)
    if receta is None:
        return _redirect("/recetas", error="Pack de estancia no encontrado.")
    try:
        items = json.loads(receta.datos or "[]")
    except Exception:
        items = []
    return TEMPLATES.TemplateResponse(request, "recetas/form.html", {
        "receta": receta,
        "items": items,
    })


@router.post("/recetas/{receta_id}/editar")
async def guardar_edicion_receta(request: Request, receta_id: int, db: Session = Depends(get_db)):
    receta = db.get(RecetaEstancia, receta_id)
    if receta is None:
        return _redirect("/recetas", error="Pack de estancia no encontrado.")
    form = await request.form()
    nombre = str(form.get("nombre", "")).strip()
    descripcion = str(form.get("descripcion", "")).strip()
    categoria = str(form.get("categoria", "")).strip() or "Baños"
    unidad_base = str(form.get("unidad_base", "")).strip() or "m²"
    try:
        cantidad_base = float(form.get("cantidad_base_default", 10.0) or 10.0)
    except ValueError:
        cantidad_base = 10.0
    datos = str(form.get("datos", "[]")).strip()
    if not nombre:
        return _redirect(f"/recetas/{receta_id}/editar", error="El nombre del pack es obligatorio.")
    try:
        json.loads(datos)
    except Exception:
        datos = "[]"
    receta.nombre = nombre
    receta.descripcion = descripcion
    receta.categoria = categoria
    receta.unidad_base = unidad_base
    receta.cantidad_base_default = cantidad_base
    receta.datos = datos
    db.commit()
    return _redirect("/recetas", msg="✅ Pack de estancia guardado.")


@router.post("/recetas/{receta_id}/eliminar")
def eliminar_receta(receta_id: int, db: Session = Depends(get_db)):
    receta = db.get(RecetaEstancia, receta_id)
    if receta is None:
        return _redirect("/recetas", error="Pack de estancia no encontrado.")
    db.delete(receta)
    db.commit()
    return _redirect("/recetas", msg="✅ Pack de estancia eliminado.")


@router.post("/recetas/{receta_id}/duplicar")
def duplicar_receta(receta_id: int, db: Session = Depends(get_db)):
    receta = db.get(RecetaEstancia, receta_id)
    if receta is None:
        return _redirect("/recetas", error="Pack de estancia no encontrado.")
    nueva = RecetaEstancia(
        nombre=f"{receta.nombre} (copia)",
        descripcion=receta.descripcion,
        categoria=receta.categoria,
        unidad_base=receta.unidad_base,
        cantidad_base_default=receta.cantidad_base_default,
        datos=receta.datos,
    )
    db.add(nueva)
    db.commit()
    return _redirect("/recetas", msg="✅ Pack de estancia duplicado.")


@router.post("/recetas/restaurar-demo")
def restaurar_recetas_demo(db: Session = Depends(get_db)):
    from ..seeds import sembrar_recetas
    sembrar_recetas(db)
    return _redirect("/recetas", msg="✅ Presets de reforma de lujo verificados y restaurados.")


@router.get("/recetas/api/list")
def api_listar_recetas(db: Session = Depends(get_db)):
    recetas = db.query(RecetaEstancia).order_by(RecetaEstancia.categoria, RecetaEstancia.nombre).all()
    res = []
    for r in recetas:
        try:
            items = json.loads(r.datos or "[]")
        except Exception:
            items = []
        res.append({
            "id": r.id,
            "nombre": r.nombre,
            "descripcion": r.descripcion or "",
            "categoria": r.categoria or "Otros",
            "unidad_base": r.unidad_base or "m²",
            "cantidad_base_default": r.cantidad_base_default or 10.0,
            "items": items,
        })
    return {"ok": True, "recetas": res}


@router.get("/recetas/api/{receta_id}")
def api_detalle_receta(receta_id: int, db: Session = Depends(get_db)):
    r = db.get(RecetaEstancia, receta_id)
    if not r:
        return {"ok": False, "error": "No encontrado"}
    try:
        items = json.loads(r.datos or "[]")
    except Exception:
        items = []
    return {
        "ok": True,
        "receta": {
            "id": r.id,
            "nombre": r.nombre,
            "descripcion": r.descripcion or "",
            "categoria": r.categoria or "Otros",
            "unidad_base": r.unidad_base or "m²",
            "cantidad_base_default": r.cantidad_base_default or 10.0,
            "items": items,
        }
    }


@router.post("/recetas/api/guardar-desde-capitulo")
async def api_guardar_receta_capitulo(request: Request, db: Session = Depends(get_db)):
    """Guarda un capítulo del constructor como una nueva RecetaEstancia."""
    try:
        payload = await request.json()
    except Exception:
        return {"ok": False, "error": "Carga JSON inválida."}
    nombre = str(payload.get("nombre", "")).strip()
    categoria = str(payload.get("categoria", "")).strip() or "Otros"
    unidad_base = str(payload.get("unidad_base", "")).strip() or "m²"
    try:
        cantidad_base = float(payload.get("cantidad_base_default", 10.0) or 10.0)
    except ValueError:
        cantidad_base = 10.0
    calcular_coeficientes = bool(payload.get("calcular_coeficientes", True))
    items_in = payload.get("items", [])
    if not items_in:
        return {"ok": False, "error": "El capítulo no tiene partidas."}
    items_out = []
    for it in items_in:
        try:
            cant = float(it.get("cantidad", 0) or 0)
        except ValueError:
            cant = 1.0
        tipo_calc = "proporcional" if calcular_coeficientes else "fijo"
        coef = round(cant / cantidad_base, 4) if (calcular_coeficientes and cantidad_base > 0) else cant
        items_out.append({
            "nombre": str(it.get("nombre", "")).strip(),
            "descripcion": str(it.get("descripcion", "")).strip(),
            "unidad": str(it.get("unidad", "")).strip() or "und",
            "precio": float(it.get("precio", 0) or 0),
            "categoria": str(it.get("categoria", "")).strip() or "Albañilería y Revestimientos",
            "tipo_calculo": tipo_calc,
            "coeficiente": coef,
            "cantidad_fija": cant,
        })
    rec = RecetaEstancia(
        nombre=nombre or "Nuevo Pack de Estancia",
        categoria=categoria,
        unidad_base=unidad_base,
        cantidad_base_default=cantidad_base,
        datos=json.dumps(items_out, ensure_ascii=False),
    )
    db.add(rec)
    db.commit()
    return {"ok": True, "id": rec.id, "nombre": rec.nombre}
