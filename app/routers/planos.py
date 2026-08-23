"""Router de planos con detección automática y mediciones editables."""

from fastapi import APIRouter, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, Response
from sqlalchemy.orm import Session, selectinload

from .common import (
    TEMPLATES,
    get_db,
    _config,
    _redirect,
    _f,
    _csv_response,
    Depends,
    Presupuesto,
    PlanoObra,
    PlanoMedicion,
    PresupuestoItem,
    ArchivoAlmacenado,
    save_object,
    read_reference,
    storage_reference,
    StorageError,
    log,
)
from ..services.planos import (
    ErrorPlano,
    crear_plano,
    calibrar_plano,
    crear_medicion,
    actualizar_medicion,
    detectar_espacios_plano,
    guardar_detecciones_automaticas,
    renombrar_medicion,
    eliminar_plano,
    eliminar_medicion,
    aplicar_medicion_a_partida,
    calcular_valor_real,
    exportar_plano_dxf,
    filas_csv_mediciones,
)

router = APIRouter()


@router.get("/planos", response_class=HTMLResponse)
def visor_planos(request: Request, db: Session = Depends(get_db)):
    """Galería global de planos de la organización, agrupada por presupuesto."""
    planos = (
        db.query(PlanoObra)
        .options(
            selectinload(PlanoObra.mediciones),
            selectinload(PlanoObra.presupuesto).selectinload(Presupuesto.cliente),
        )
        .order_by(PlanoObra.id.desc())
        .all()
    )

    grupos: list[dict] = []
    indice: dict[int, dict] = {}
    for plano in planos:
        presupuesto = plano.presupuesto
        if presupuesto is None:
            continue
        grupo = indice.get(presupuesto.id)
        if grupo is None:
            grupo = {"presupuesto": presupuesto, "planos": [], "n_mediciones": 0}
            indice[presupuesto.id] = grupo
            grupos.append(grupo)
        grupo["planos"].append(plano)
        grupo["n_mediciones"] += len(plano.mediciones)

    return TEMPLATES.TemplateResponse(
        request,
        "planos/visor.html",
        {
            "grupos": grupos,
            "total_planos": len(planos),
            "planos_calibrados": sum(1 for plano in planos if plano.calibrado),
            "total_mediciones": sum(len(plano.mediciones) for plano in planos),
            "cfg": _config(db),
        },
    )


@router.get("/presupuestos/{presupuesto_id}/planos", response_class=HTMLResponse)
def listar_planos_presupuesto(
    presupuesto_id: int,
    request: Request,
    plano: int = 0,
    detectar: int = 0,
    db: Session = Depends(get_db),
):
    presupuesto = db.get(Presupuesto, presupuesto_id)
    if not presupuesto:
        return _redirect("/presupuestos", error="Presupuesto no encontrado.")

    planos = (
        db.query(PlanoObra)
        .filter(PlanoObra.presupuesto_id == presupuesto_id)
        .options(selectinload(PlanoObra.mediciones))
        .order_by(PlanoObra.id.desc())
        .all()
    )

    # Enlace profundo ?plano=<id> desde el visor global; si no existe, el primero.
    plano_inicial = None
    if plano:
        plano_inicial = next((p for p in planos if p.id == plano), None)
    if plano_inicial is None and planos:
        plano_inicial = planos[0]

    # Partidas para selector de aplicar medición
    partidas = []
    for cap in presupuesto.capitulos:
        for p in cap.partidas:
            partidas.append({"id": p.id, "nombre": p.nombre, "capitulo": cap.nombre, "unidad": p.unidad})

    return TEMPLATES.TemplateResponse(
        request,
        "budgets/planos.html",
        {
            "p": presupuesto,
            "planos": planos,
            "plano_inicial": plano_inicial,
            "detectar_automaticamente": bool(detectar and plano_inicial),
            "partidas": partidas,
            "cfg": _config(db),
        },
    )


def _datos_medicion_plano(medicion: PlanoMedicion) -> dict:
    return {
        "id": medicion.id,
        "tipo": medicion.tipo,
        "etiqueta": medicion.etiqueta,
        "valor": medicion.valor,
        "unidad": medicion.unidad,
        "puntos": medicion.puntos(),
        "color": medicion.color,
        "partida_destino_id": medicion.partida_destino_id,
    }


@router.get("/planos/{plano_id}/datos")
def datos_plano(plano_id: int, db: Session = Depends(get_db)):
    plano = db.get(PlanoObra, plano_id)
    if not plano:
        return JSONResponse({"ok": False, "error": "Plano no encontrado."}, status_code=404)

    return {
        "ok": True,
        "plano": {
            "id": plano.id,
            "presupuesto_id": plano.presupuesto_id,
            "nombre": plano.nombre,
            "archivo": plano.archivo,
            "content_type": plano.content_type,
            "ancho_px": plano.ancho_px,
            "alto_px": plano.alto_px,
            "escala_px_por_metro": plano.escala_px_por_metro,
            "calibracion_px": plano.calibracion_px,
            "calibracion_real": plano.calibracion_real,
            "unidad_calibracion": plano.unidad_calibracion,
            "calibrado": plano.calibrado,
        },
        "mediciones": [_datos_medicion_plano(m) for m in plano.mediciones],
    }


@router.post("/planos/{plano_id}/detectar")
def detectar_mediciones_plano(plano_id: int, limite: int = 30, db: Session = Depends(get_db)):
    """Analiza una imagen localmente y guarda sus estancias cerradas como áreas."""
    plano = db.get(PlanoObra, plano_id)
    if not plano or not plano.archivo:
        return JSONResponse({"ok": False, "error": "Plano no encontrado."}, status_code=404)
    limite = max(1, min(int(limite), 30))
    try:
        contenido = read_reference(plano.archivo)
        candidatos = detectar_espacios_plano(contenido, plano.content_type, max_espacios=limite)
        mediciones, omitidas = guardar_detecciones_automaticas(db, plano, candidatos)
    except (ErrorPlano, StorageError) as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=400)
    except Exception:
        log.exception("Error analizando automáticamente el plano %s", plano_id)
        return JSONResponse(
            {"ok": False, "error": "No se pudo analizar automáticamente el plano."},
            status_code=500,
        )
    return {
        "ok": True,
        "analizadas": len(candidatos),
        "nuevas": len(mediciones),
        "omitidas": omitidas,
        "mediciones": [_datos_medicion_plano(m) for m in mediciones],
    }


@router.get("/planos/{plano_id}/archivo")
def descargar_archivo_plano(plano_id: int, db: Session = Depends(get_db)):
    plano = db.get(PlanoObra, plano_id)
    if not plano or not plano.archivo:
        return Response(status_code=404)
    try:
        contenido = read_reference(plano.archivo)
    except StorageError:
        return Response(status_code=404)
    return Response(
        contenido,
        media_type=plano.content_type or "image/png",
        headers={"Cache-Control": "private, max-age=3600"},
    )


@router.post("/presupuestos/{presupuesto_id}/planos/upload")
async def subir_plano(
    presupuesto_id: int,
    request: Request,
    archivo: UploadFile,
    nombre: str = Form(""),
    db: Session = Depends(get_db),
):
    presupuesto = db.get(Presupuesto, presupuesto_id)
    if not presupuesto:
        return JSONResponse({"ok": False, "error": "Presupuesto no encontrado."}, status_code=404)

    if not archivo or not archivo.filename:
        return JSONResponse({"ok": False, "error": "Selecciona un archivo de plano."}, status_code=400)

    contenido = await archivo.read()
    try:
        plano = crear_plano(db, presupuesto_id, nombre, archivo.filename, contenido)
        es_imagen = (plano.content_type or "").startswith("image/")
        query = f"?plano={plano.id}" + ("&detectar=1" if es_imagen else "")
        return {
            "ok": True,
            "plano_id": plano.id,
            "url": f"/presupuestos/{presupuesto_id}/planos{query}",
            "deteccion_automatica": es_imagen,
        }
    except ErrorPlano as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
    except Exception as e:
        log.exception("Error subiendo plano")
        return JSONResponse({"ok": False, "error": "No se pudo guardar el plano."}, status_code=500)


@router.post("/planos/{plano_id}/calibrar")
async def calibrar_plano_endpoint(
    plano_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    plano = db.get(PlanoObra, plano_id)
    if not plano:
        return JSONResponse({"ok": False, "error": "Plano no encontrado."}, status_code=404)

    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "JSON no válido."}, status_code=400)

    try:
        dist_px = float(payload.get("distancia_px", 0))
        dist_real = float(payload.get("distancia_real", 0))
        unidad = str(payload.get("unidad", "m"))
    except (TypeError, ValueError):
        return JSONResponse({"ok": False, "error": "Distancias no válidas."}, status_code=400)

    try:
        calibrar_plano(db, plano, dist_px, dist_real, unidad)
        return {
            "ok": True,
            "escala_px_por_metro": plano.escala_px_por_metro,
            "factor_m": plano.factor_m,
        }
    except ErrorPlano as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@router.post("/planos/{plano_id}/mediciones")
async def crear_medicion_endpoint(
    plano_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    plano = db.get(PlanoObra, plano_id)
    if not plano:
        return JSONResponse({"ok": False, "error": "Plano no encontrado."}, status_code=404)

    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "JSON no válido."}, status_code=400)

    tipo = str(payload.get("tipo", "lineal"))
    etiqueta = str(payload.get("etiqueta", ""))
    puntos = payload.get("puntos", [])
    color = str(payload.get("color", "#ff0000"))
    partida_id = payload.get("partida_destino_id")

    try:
        pid = int(partida_id) if partida_id not in (None, "", 0) else None
    except (TypeError, ValueError):
        pid = None

    try:
        med = crear_medicion(db, plano, tipo, etiqueta, puntos, color, pid)
        return {"ok": True, "medicion": _datos_medicion_plano(med)}
    except ErrorPlano as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@router.put("/planos/{plano_id}/mediciones/{medicion_id}")
async def actualizar_medicion_endpoint(
    plano_id: int,
    medicion_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    plano = db.get(PlanoObra, plano_id)
    med = db.get(PlanoMedicion, medicion_id)
    if not plano or not med or med.plano_id != plano_id:
        return JSONResponse({"ok": False, "error": "Medición no encontrada."}, status_code=404)
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "JSON no válido."}, status_code=400)
    try:
        med = actualizar_medicion(
            db,
            plano,
            med,
            str(payload.get("tipo", med.tipo)),
            str(payload.get("etiqueta", med.etiqueta or "")),
            payload.get("puntos", med.puntos()),
            str(payload.get("color", med.color or "#ff0000")),
        )
        return {"ok": True, "medicion": _datos_medicion_plano(med)}
    except ErrorPlano as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@router.post("/planos/{plano_id}/mediciones/{medicion_id}/aplicar")
async def aplicar_medicion_endpoint(
    plano_id: int,
    medicion_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    med = db.get(PlanoMedicion, medicion_id)
    if not med or med.plano_id != plano_id:
        return JSONResponse({"ok": False, "error": "Medición no encontrada."}, status_code=404)

    try:
        payload = await request.json()
        partida_id = int(payload.get("partida_id", 0))
    except Exception:
        return JSONResponse({"ok": False, "error": "Partida no válida."}, status_code=400)

    try:
        res = aplicar_medicion_a_partida(db, med, partida_id)
        return res
    except ErrorPlano as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@router.delete("/planos/{plano_id}")
def borrar_plano_endpoint(plano_id: int, db: Session = Depends(get_db)):
    plano = db.get(PlanoObra, plano_id)
    if not plano:
        return JSONResponse({"ok": False, "error": "Plano no encontrado."}, status_code=404)
    presupuesto_id = plano.presupuesto_id
    eliminar_plano(db, plano)
    return {"ok": True, "presupuesto_id": presupuesto_id}


@router.delete("/planos/{plano_id}/mediciones/{medicion_id}")
def borrar_medicion_endpoint(plano_id: int, medicion_id: int, db: Session = Depends(get_db)):
    med = db.get(PlanoMedicion, medicion_id)
    if not med or med.plano_id != plano_id:
        return JSONResponse({"ok": False, "error": "Medición no encontrada."}, status_code=404)
    eliminar_medicion(db, med)
    return {"ok": True}


@router.post("/planos/{plano_id}/mediciones/{medicion_id}/eliminar")
def borrar_medicion_post(plano_id: int, medicion_id: int, db: Session = Depends(get_db)):
    med = db.get(PlanoMedicion, medicion_id)
    if not med or med.plano_id != plano_id:
        return JSONResponse({"ok": False, "error": "Medición no encontrada."}, status_code=404)
    eliminar_medicion(db, med)
    return {"ok": True}


@router.post("/planos/{plano_id}/mediciones/{medicion_id}/renombrar")
async def renombrar_medicion_endpoint(
    plano_id: int,
    medicion_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    med = db.get(PlanoMedicion, medicion_id)
    if not med or med.plano_id != plano_id:
        return JSONResponse({"ok": False, "error": "Medición no encontrada."}, status_code=404)
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "JSON no válido."}, status_code=400)
    try:
        med = renombrar_medicion(db, med, str(payload.get("etiqueta", "")))
        return {"ok": True, "etiqueta": med.etiqueta}
    except ErrorPlano as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@router.get("/presupuestos/{presupuesto_id}/planos/exportar")
def exportar_mediciones_presupuesto(
    presupuesto_id: int,
    formato: str = "csv",
    db: Session = Depends(get_db),
):
    """CSV con todas las mediciones de todos los planos del presupuesto."""
    presupuesto = db.get(Presupuesto, presupuesto_id)
    if not presupuesto:
        return _redirect("/presupuestos", error="Presupuesto no encontrado.")
    filas = filas_csv_mediciones(presupuesto)
    if len(filas) <= 1:
        return _redirect(
            f"/presupuestos/{presupuesto_id}/planos",
            error="Este presupuesto no tiene mediciones que exportar.",
        )
    return _csv_response(filas, f"mediciones_{presupuesto.numero}.csv")


@router.get("/planos/{plano_id}/exportar")
def exportar_plano_endpoint(
    plano_id: int,
    formato: str = "dxf",
    db: Session = Depends(get_db),
):
    """DXF con las mediciones del plano para AutoCAD/LibreCAD/BricsCAD."""
    plano = db.get(PlanoObra, plano_id)
    if not plano:
        return JSONResponse({"ok": False, "error": "Plano no encontrado."}, status_code=404)
    if (formato or "dxf").lower() != "dxf":
        return JSONResponse({"ok": False, "error": "Formato no soportado."}, status_code=400)
    try:
        dxf = exportar_plano_dxf(plano)
    except ErrorPlano as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
    nombre = "".join(c for c in plano.nombre if c.isalnum() or c in "-_ ")[:40].strip() or f"plano_{plano.id}"
    return Response(
        content=dxf,
        media_type="application/dxf",
        headers={
            "Content-Disposition": f'attachment; filename="mediciones_{nombre}.dxf"',
        },
    )
