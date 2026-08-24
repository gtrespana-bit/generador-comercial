"""Router de planos con detección automática, dibujo y mediciones editables.

Cubre tres modos del plano:

* **subido**: imagen o PDF que se analiza con el detector local.
* **dibujado**: creado desde cero en el editor vectorial.
* **mixto**: combinación de imagen de fondo y geometría vectorial.

El grosor del tabique es transversal: vive en ``PlanoObra.grosor_tabique_cm``
y se usa en la detección, en la métrica y en el render de los muros
dibujados.
"""

from fastapi import APIRouter, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, Response
from sqlalchemy.orm import Session, selectinload
from typing import Any

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
    PlanoElemento,
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
    crear_plano_en_blanco,
    calibrar_plano,
    crear_medicion,
    actualizar_medicion,
    actualizar_altura_plano,
    actualizar_grosor_tabique,
    detectar_espacios_plano,
    guardar_detecciones_automaticas,
    detectar_estancias_sobre_dibujo,
    guardar_detecciones_sobre_dibujo,
    guardar_elemento,
    actualizar_elemento,
    eliminar_elemento,
    metricas_estancia,
    grosor_px_plano,
    renombrar_medicion,
    eliminar_plano,
    eliminar_medicion,
    aplicar_medicion_a_partida,
    calcular_valor_real,
    exportar_plano_dxf,
    filas_csv_mediciones,
    GROSOR_TABIQUE_DEFECTO_CM,
)
from ..services.planos_compat import (
    EsquemaPlanos,
    completar_plano_legacy,
    completar_planos_legacy,
    detectar_esquema_planos,
    opciones_columnas_compatibles,
)

router = APIRouter()


_MENSAJE_MIGRACION_PLANOS = (
    "El editor de planos se está actualizando. Los planos existentes siguen "
    "disponibles, pero esta acción requiere que termine la migración de datos."
)


def _consulta_planos_compatible(
    db: Session,
    esquema: EsquemaPlanos,
    *,
    cargar_elementos: bool = False,
):
    """Consulta ``PlanoObra`` sin seleccionar columnas aún no migradas."""
    opciones = list(opciones_columnas_compatibles(esquema))
    if cargar_elementos and esquema.tiene_tabla_elementos:
        opciones.append(selectinload(PlanoObra.elementos))
    return db.query(PlanoObra).options(*opciones)


def _obtener_plano_compatible(
    db: Session,
    plano_id: int,
    *,
    esquema: EsquemaPlanos | None = None,
) -> PlanoObra | None:
    esquema = esquema or detectar_esquema_planos(db)
    plano = (
        _consulta_planos_compatible(db, esquema, cargar_elementos=True)
        .options(selectinload(PlanoObra.mediciones))
        .filter(PlanoObra.id == plano_id)
        .first()
    )
    if plano is not None:
        completar_plano_legacy(plano, esquema)
    return plano


def _respuesta_migracion_planos_pendiente() -> JSONResponse:
    """Evita un 500 si se intenta escribir el esquema vectorial ausente."""
    return JSONResponse(
        {
            "ok": False,
            "error": _MENSAJE_MIGRACION_PLANOS,
            "codigo": "migracion_planos_pendiente",
        },
        status_code=503,
        headers={"Retry-After": "300"},
    )


@router.get("/planos", response_class=HTMLResponse)
def visor_planos(request: Request, db: Session = Depends(get_db)):
    """Galería global de planos de la organización, agrupada por presupuesto."""
    esquema = detectar_esquema_planos(db)
    planos = completar_planos_legacy(
        _consulta_planos_compatible(db, esquema)
        .options(
            selectinload(PlanoObra.mediciones),
            selectinload(PlanoObra.presupuesto).selectinload(Presupuesto.cliente),
        )
        .order_by(PlanoObra.id.desc())
        .all(),
        esquema,
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
            "esquema_planos_completo": esquema.editor_vectorial_disponible,
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

    esquema = detectar_esquema_planos(db)
    planos = completar_planos_legacy(
        _consulta_planos_compatible(db, esquema, cargar_elementos=True)
        .filter(PlanoObra.presupuesto_id == presupuesto_id)
        .options(selectinload(PlanoObra.mediciones))
        .order_by(PlanoObra.id.desc())
        .all(),
        esquema,
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
            "detectar_automaticamente": False,
            "partidas": partidas,
            "esquema_planos_completo": esquema.editor_vectorial_disponible,
            "cfg": _config(db),
        },
    )


@router.get("/presupuestos/{presupuesto_id}/planos/mediciones-selector")
def mediciones_selector_presupuesto(presupuesto_id: int, db: Session = Depends(get_db)):
    """Medidas listas para insertar como desglose en una partida.

    La respuesta presenta una estancia como varias magnitudes útiles: suelo,
    perímetro y desarrollo de paredes. Así el editor de presupuestos no tiene
    que copiar a mano el número que ya está calculado en el visor.

    Diagnóstico ampliado (sin filtrar por RLS en SQLite): si la consulta
    inicial no devuelve planos, se comprueba si existen otros presupuestos
    con planos del mismo cliente. Eso le dice al frontend **por qué** el
    selector está vacío (no hay presupuesto, no hay planos, o los planos
    pertenecen a otro presupuesto) en lugar de mostrar el mensaje genérico
    de "sube un plano" que despistaba al usuario.
    """
    presupuesto = db.get(Presupuesto, presupuesto_id)
    if not presupuesto:
        # Diferenciamos claramente "el presupuesto no existe" de "no hay
        # planos" para que el frontend pueda mostrar un mensaje útil.
        return JSONResponse(
            {
                "ok": False,
                "error": "Presupuesto no encontrado.",
                "razon": "presupuesto_inexistente",
                "presupuesto_id": presupuesto_id,
            },
            status_code=404,
        )

    esquema = detectar_esquema_planos(db)
    planos = completar_planos_legacy(
        _consulta_planos_compatible(db, esquema)
        .filter(PlanoObra.presupuesto_id == presupuesto_id)
        .options(selectinload(PlanoObra.mediciones))
        .order_by(PlanoObra.id.desc())
        .all(),
        esquema,
    )

    # Diagnóstico: si la consulta no devuelve nada, miramos si el
    # presupuesto existe pero no tiene planos, o si el filtro tenant
    # del ORM ha descartado filas que sí existen.
    diagnostico: dict[str, Any] = {
        "planos_en_presupuesto": len(planos),
    }
    if not planos:
        conteo_total = (
            db.query(PlanoObra)
            .filter(PlanoObra.presupuesto_id == presupuesto_id)
            .count()
        )
        diagnostico["conteo_total"] = conteo_total
        diagnostico["presupuesto_id"] = presupuesto_id

    resultado: list[dict[str, Any]] = []
    for plano in planos:
        medidas = []
        for med in plano.mediciones:
            opciones: list[dict[str, Any]] = []
            if med.tipo == "area":
                metricas = metricas_estancia(
                    med.puntos(),
                    plano.escala_px_por_metro,
                    plano.altura_m,
                    plano.grosor_tabique_m,
                )
                opciones = [
                    {
                        "clave": "perimetro",
                        "etiqueta": "Perímetro de estancia",
                        "cantidad": metricas["perimetro"] if metricas.get("calibrado") else None,
                        "unidad": "m",
                    },
                    {
                        "clave": "valor",
                        "etiqueta": "Superficie medida",
                        "cantidad": metricas["suelo"] if metricas.get("calibrado") else None,
                        "unidad": "m2",
                    },
                    {
                        "clave": "suelo",
                        "etiqueta": "Superficie de suelo",
                        "cantidad": metricas["suelo"] if metricas.get("calibrado") else None,
                        "unidad": "m2",
                    },
                    {
                        "clave": "paredes",
                        "etiqueta": "Superficie de paredes",
                        "cantidad": metricas["paredes"] if metricas.get("calibrado") else None,
                        "unidad": "m2",
                    },
                ]
            elif med.tipo in {"lineal", "perimetro"}:
                opciones = [{
                    "clave": "valor",
                    "etiqueta": "Medida guardada",
                    "cantidad": med.valor if plano.calibrado else None,
                    "unidad": "m",
                }]
            elif med.tipo == "conteo":
                opciones = [{
                    "clave": "valor",
                    "etiqueta": "Conteo",
                    "cantidad": med.valor,
                    "unidad": "ud",
                }]
            else:
                continue
            medidas.append({
                "id": med.id,
                "etiqueta": med.etiqueta or f"{med.tipo.title()} {med.id}",
                "tipo": med.tipo,
                "opciones": opciones,
                "calibrado": plano.calibrado or med.tipo == "conteo",
            })
        resultado.append({
            "id": plano.id,
            "nombre": plano.nombre,
            "origen": plano.origen or "subido",
            "calibrado": plano.calibrado,
            "grosor_tabique_cm": plano.grosor_tabique_cm,
            "altura_libre_m": plano.altura_m,
            "mediciones": medidas,
        })
    return {"ok": True, "planos": resultado, "diagnostico": diagnostico}


def _datos_medicion_plano(medicion: PlanoMedicion, plano: PlanoObra | None = None) -> dict:
    puntos = medicion.puntos()
    plano = plano or medicion.plano
    escala = plano.escala_px_por_metro if plano is not None else None
    altura = plano.altura_m if plano is not None else 2.5
    grosor = plano.grosor_tabique_m if plano is not None else None
    extras: dict[str, Any] = {}
    if medicion.tipo in ("area", "perimetro", "volumen"):
        extras["metricas"] = metricas_estancia(puntos, escala, altura, grosor)
    return {
        "id": medicion.id,
        "tipo": medicion.tipo,
        "etiqueta": medicion.etiqueta,
        "valor": medicion.valor,
        "unidad": medicion.unidad,
        "puntos": puntos,
        "color": medicion.color,
        "partida_destino_id": medicion.partida_destino_id,
        **extras,
    }


def _datos_elemento_plano(elemento: PlanoElemento) -> dict:
    return {
        "id": elemento.id,
        "tipo": elemento.tipo,
        "puntos": elemento.puntos(),
        "grosor_cm": elemento.grosor_cm,
        "color": elemento.color,
        "muro_id": elemento.muro_id,
    }


@router.get("/planos/{plano_id}/datos")
def datos_plano(plano_id: int, db: Session = Depends(get_db)):
    plano = _obtener_plano_compatible(db, plano_id)
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
            "altura_libre_m": plano.altura_m,
            "origen": plano.origen or "subido",
            "grosor_tabique_cm": plano.grosor_tabique_cm,
            "grosor_tabique_m": plano.grosor_tabique_m,
            "ancho_lienzo_m": plano.ancho_lienzo_m,
            "alto_lienzo_m": plano.alto_lienzo_m,
        },
        "mediciones": [_datos_medicion_plano(m, plano) for m in plano.mediciones],
        "elementos": [_datos_elemento_plano(e) for e in plano.elementos],
    }


@router.post("/planos/{plano_id}/detectar")
def detectar_mediciones_plano(plano_id: int, limite: int = 30, db: Session = Depends(get_db)):
    """Analiza una imagen localmente y guarda sus estancias cerradas como áreas.

    Para planos ``subido``/``mixto`` corre el detector raster sobre la
    imagen de fondo. Para planos ``dibujado`` (sin imagen) corre el
    detector vectorial sobre los muros creados por el usuario. En
    ambos casos el grosor declarado por el usuario participa en la
    generación de la barrera y en el ajuste de bordes compartidos.
    """
    esquema = detectar_esquema_planos(db)
    plano = _obtener_plano_compatible(db, plano_id, esquema=esquema)
    if not plano:
        return JSONResponse({"ok": False, "error": "Plano no encontrado."}, status_code=404)
    limite = max(1, min(int(limite), 30))

    if plano.origen == "dibujado" and not esquema.editor_vectorial_disponible:
        return _respuesta_migracion_planos_pendiente()
    if plano.origen == "dibujado":
        try:
            candidatos = detectar_estancias_sobre_dibujo(plano)
            mediciones, omitidas = guardar_detecciones_sobre_dibujo(db, plano, candidatos)
        except ErrorPlano as exc:
            return JSONResponse({"ok": False, "error": str(exc)}, status_code=400)
        return {
            "ok": True,
            "analizadas": len(candidatos),
            "nuevas": len(mediciones),
            "omitidas": omitidas,
            "mediciones": [_datos_medicion_plano(m, plano) for m in mediciones],
            "modo": "vectorial",
        }

    if not plano.archivo:
        return JSONResponse(
            {"ok": False, "error": "Este plano no tiene imagen para analizar."},
            status_code=400,
        )
    try:
        contenido = read_reference(plano.archivo)
        grosor_px = grosor_px_plano(plano)
        candidatos = detectar_espacios_plano(
            contenido,
            plano.content_type,
            max_espacios=limite,
            grosor_tabique_px=grosor_px,
        )
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
        "mediciones": [_datos_medicion_plano(m, plano) for m in mediciones],
        "modo": "raster",
        "grosor_tabique_px": grosor_px_plano(plano),
    }


@router.get("/planos/{plano_id}/archivo")
def descargar_archivo_plano(plano_id: int, db: Session = Depends(get_db)):
    plano = _obtener_plano_compatible(db, plano_id)
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
    # El INSERT ORM incluye las cuatro columnas nuevas aun para un plano
    # raster. Si falta cualquiera, responde de forma explícita en vez de dejar
    # que PostgreSQL genere UndefinedColumn y un 500.
    esquema = detectar_esquema_planos(db)
    if not esquema.columnas_vectoriales_completas:
        return _respuesta_migracion_planos_pendiente()

    if not archivo or not archivo.filename:
        return JSONResponse({"ok": False, "error": "Selecciona un archivo de plano."}, status_code=400)

    contenido = await archivo.read()
    try:
        plano = crear_plano(db, presupuesto_id, nombre, archivo.filename, contenido)
        es_imagen = (plano.content_type or "").startswith("image/")
        return {
            "ok": True,
            "plano_id": plano.id,
            "url": f"/presupuestos/{presupuesto_id}/planos?plano={plano.id}",
            "deteccion_automatica": False,
            "requiere_calibracion": True,
            "es_imagen": es_imagen,
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
    esquema = detectar_esquema_planos(db)
    plano = _obtener_plano_compatible(db, plano_id, esquema=esquema)
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
        altura_raw = payload.get("altura_libre_m")
        altura = float(altura_raw) if altura_raw not in (None, "") else None
        grosor_raw = payload.get("grosor_tabique_cm")
        grosor_cm = float(grosor_raw) if grosor_raw not in (None, "") else None
    except (TypeError, ValueError):
        return JSONResponse({"ok": False, "error": "Distancias no válidas."}, status_code=400)

    try:
        # Calibrar (funcionalidad histórica) sigue disponible durante la
        # ventana de migración. Solo se omite el ajuste del grosor si su
        # columna física aún no existe; el valor seguro sigue siendo 10 cm.
        if grosor_cm is not None and esquema.tiene_columna("grosor_tabique_cm"):
            actualizar_grosor_tabique(db, plano, grosor_cm)
        calibrar_plano(db, plano, dist_px, dist_real, unidad, altura)
        return {
            "ok": True,
            "escala_px_por_metro": plano.escala_px_por_metro,
            "factor_m": plano.factor_m,
            "altura_libre_m": plano.altura_m,
            "grosor_tabique_cm": plano.grosor_tabique_cm,
            "grosor_tabique_px": grosor_px_plano(plano),
        }
    except ErrorPlano as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@router.post("/planos/{plano_id}/mediciones")
async def crear_medicion_endpoint(
    plano_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    plano = _obtener_plano_compatible(db, plano_id)
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
        return {"ok": True, "medicion": _datos_medicion_plano(med, plano)}
    except ErrorPlano as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@router.put("/planos/{plano_id}/mediciones/{medicion_id}")
async def actualizar_medicion_endpoint(
    plano_id: int,
    medicion_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    plano = _obtener_plano_compatible(db, plano_id)
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
        return {"ok": True, "medicion": _datos_medicion_plano(med, plano)}
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


@router.post("/planos/{plano_id}/altura")
async def actualizar_altura_endpoint(
    plano_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    plano = _obtener_plano_compatible(db, plano_id)
    if not plano:
        return JSONResponse({"ok": False, "error": "Plano no encontrado."}, status_code=404)
    try:
        payload = await request.json()
        altura = float(payload.get("altura_libre_m", 0))
    except Exception:
        return JSONResponse({"ok": False, "error": "Altura no válida."}, status_code=400)
    try:
        actualizar_altura_plano(db, plano, altura)
        return {
            "ok": True,
            "altura_libre_m": plano.altura_m,
            "mediciones": [_datos_medicion_plano(m, plano) for m in plano.mediciones],
        }
    except ErrorPlano as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@router.delete("/planos/{plano_id}")
def borrar_plano_endpoint(plano_id: int, db: Session = Depends(get_db)):
    plano = _obtener_plano_compatible(db, plano_id)
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
    esquema = detectar_esquema_planos(db)
    planos = completar_planos_legacy(
        _consulta_planos_compatible(db, esquema, cargar_elementos=True)
        .filter(PlanoObra.presupuesto_id == presupuesto_id)
        .options(
            selectinload(PlanoObra.mediciones).selectinload(
                PlanoMedicion.partida_destino
            )
        )
        .order_by(PlanoObra.id)
        .all(),
        esquema,
    )
    filas = filas_csv_mediciones(presupuesto, planos=planos)
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
    plano = _obtener_plano_compatible(db, plano_id)
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


# --------------------------------------------------------------------------- #
# Planos creados desde cero (editor vectorial)
# --------------------------------------------------------------------------- #

@router.post("/presupuestos/{presupuesto_id}/planos/blanco")
async def crear_plano_blanco(
    presupuesto_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Crea un plano vectorial vacío que el usuario dibujará en el editor.

    El cliente manda ``nombre``, ``ancho_lienzo_m``, ``alto_lienzo_m`` y
    opcionalmente ``grosor_tabique_cm``. Devuelve la ficha del plano
    recién creado para que el visor entre directamente en modo edición.
    """
    presupuesto = db.get(Presupuesto, presupuesto_id)
    if not presupuesto:
        return JSONResponse({"ok": False, "error": "Presupuesto no encontrado."}, status_code=404)
    esquema = detectar_esquema_planos(db)
    if not esquema.editor_vectorial_disponible:
        return _respuesta_migracion_planos_pendiente()
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    nombre = str(payload.get("nombre") or "").strip()[:250]
    ancho_m = payload.get("ancho_lienzo_m")
    alto_m = payload.get("alto_lienzo_m")
    grosor = payload.get("grosor_tabique_cm", GROSOR_TABIQUE_DEFECTO_CM)

    try:
        plano = crear_plano_en_blanco(
            db,
            presupuesto_id,
            nombre,
            float(ancho_m) if ancho_m is not None else 12.0,
            float(alto_m) if alto_m is not None else 8.0,
            float(grosor) if grosor is not None else GROSOR_TABIQUE_DEFECTO_CM,
        )
    except ErrorPlano as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
    return {
        "ok": True,
        "plano_id": plano.id,
        "url": f"/presupuestos/{presupuesto_id}/planos?plano={plano.id}",
    }


@router.post("/planos/{plano_id}/grosor")
async def actualizar_grosor_endpoint(
    plano_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Cambia el grosor típico del tabique del plano (en centímetros)."""
    esquema = detectar_esquema_planos(db)
    if not esquema.tiene_columna("grosor_tabique_cm"):
        return _respuesta_migracion_planos_pendiente()
    plano = _obtener_plano_compatible(db, plano_id, esquema=esquema)
    if not plano:
        return JSONResponse({"ok": False, "error": "Plano no encontrado."}, status_code=404)
    try:
        payload = await request.json()
        grosor = float(payload.get("grosor_tabique_cm", 0))
    except Exception:
        return JSONResponse({"ok": False, "error": "Grosor no válido."}, status_code=400)
    try:
        actualizar_grosor_tabique(db, plano, grosor)
    except ErrorPlano as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
    return {
        "ok": True,
        "grosor_tabique_cm": plano.grosor_tabique_cm,
        "grosor_tabique_m": plano.grosor_tabique_m,
        "grosor_tabique_px": grosor_px_plano(plano),
    }


@router.post("/planos/{plano_id}/elementos")
async def crear_elemento_endpoint(
    plano_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Crea un muro / hueco / línea auxiliar en el plano."""
    esquema = detectar_esquema_planos(db)
    if not esquema.editor_vectorial_disponible:
        return _respuesta_migracion_planos_pendiente()
    plano = _obtener_plano_compatible(db, plano_id, esquema=esquema)
    if not plano:
        return JSONResponse({"ok": False, "error": "Plano no encontrado."}, status_code=404)
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "JSON no válido."}, status_code=400)
    try:
        elem = guardar_elemento(
            db,
            plano,
            str(payload.get("tipo", "")),
            payload.get("puntos") or [],
            payload.get("grosor_cm"),
            str(payload.get("color", "#1f2937")),
            payload.get("muro_id"),
        )
    except ErrorPlano as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
    return {"ok": True, "elemento": _datos_elemento_plano(elem)}


@router.put("/planos/{plano_id}/elementos/{elemento_id}")
async def actualizar_elemento_endpoint(
    plano_id: int,
    elemento_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    esquema = detectar_esquema_planos(db)
    if not esquema.editor_vectorial_disponible:
        return _respuesta_migracion_planos_pendiente()
    plano = _obtener_plano_compatible(db, plano_id, esquema=esquema)
    elem = db.get(PlanoElemento, elemento_id)
    if not plano or not elem or elem.plano_id != plano_id:
        return JSONResponse({"ok": False, "error": "Elemento no encontrado."}, status_code=404)
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "JSON no válido."}, status_code=400)
    try:
        elem = actualizar_elemento(
            db,
            plano,
            elem,
            payload.get("puntos") or [],
            payload.get("grosor_cm"),
            payload.get("color"),
        )
    except ErrorPlano as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
    return {"ok": True, "elemento": _datos_elemento_plano(elem)}


@router.delete("/planos/{plano_id}/elementos/{elemento_id}")
def eliminar_elemento_endpoint(
    plano_id: int,
    elemento_id: int,
    db: Session = Depends(get_db),
):
    esquema = detectar_esquema_planos(db)
    if not esquema.editor_vectorial_disponible:
        return _respuesta_migracion_planos_pendiente()
    plano = _obtener_plano_compatible(db, plano_id, esquema=esquema)
    elem = db.get(PlanoElemento, elemento_id)
    if not plano or not elem or elem.plano_id != plano_id:
        return JSONResponse({"ok": False, "error": "Elemento no encontrado."}, status_code=404)
    eliminar_elemento(db, plano, elem)
    return {"ok": True}
