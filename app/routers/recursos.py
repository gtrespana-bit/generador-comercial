"""Catálogo de recursos (precios unitarios)."""  # E4-001 — router por dominio

from fastapi import APIRouter

from .common import *  # noqa: F401,F403  (re-exporta modelos, servicios y utilidades)
from ..services import auditoria

router = APIRouter()

# ---------------------------------------------------------------------------
# Recursos / Precios Unitarios (catálogo central)
# ---------------------------------------------------------------------------

CATEGORIAS_RECURSO = ["mano_obra", "materiales", "complementarios", "otros"]
ETIQUETAS_RECURSO = {
    "mano_obra": "Mano de obra",
    "materiales": "Materiales",
    "complementarios": "Costes complementarios",
    "otros": "Equipos y otros",
}

def _datos_recurso(form):
    return {
        "codigo": str(form.get("codigo", "")).strip(),
        "descripcion": str(form.get("descripcion", "")).strip(),
        "unidad": str(form.get("unidad", "ud")).strip() or "ud",
        "categoria": str(form.get("categoria", "otros")).strip().lower() or "otros",
        "grupo": str(form.get("grupo", "")).strip(),
        "precio": max(0.0, _f(form.get("precio"), 0.0)),
        "proveedor": str(form.get("proveedor", "")).strip(),
    }
@router.get("/recursos", response_class=HTMLResponse)
def listar_recursos(request: Request, q: str = "", categoria: str = "", db: Session = Depends(get_db)):
    # Si aún está el catálogo de prueba, se migra al propio (con recursos).
    from ..services.catalogo_propio import asegurar_catalogo_propio
    asegurar_catalogo_propio(db)
    # Sincronización automática en cada vista: crea los recursos que falten
    # desde las descomposiciones (partidas y presupuestos) y actualiza usos.
    # Es idempotente y barato; así los tabs de mano de obra / materiales /
    # complementarios / otros reflejan siempre los recursos que se escriben
    # al crear o editar partidas, sin depender del botón manual.
    _sincronizar_recursos(db)
    query = db.query(Recurso)
    if q.strip():
        like = f"%{q.strip()}%"
        query = query.filter(or_(
            Recurso.codigo.ilike(like),
            Recurso.descripcion.ilike(like),
            Recurso.grupo.ilike(like),
            Recurso.proveedor.ilike(like),
        ))
    if categoria and categoria in CATEGORIAS_RECURSO:
        query = query.filter(Recurso.categoria == categoria)
    recursos = query.order_by(Recurso.categoria, Recurso.descripcion).all()
    from ..services.traduccion import codigo_desde_pais
    from ..services.precios_mercado import resolver_precio
    cfg = _config(db)
    pais = codigo_desde_pais(cfg.empresa_pais or "") or "VE"
    org_id = int(db.info.get("organizacion_id") or 0)
    precios_efectivos = {r.id: resolver_precio(db, r.id, pais, org_id) for r in recursos}
    # Agrupar por categoria
    return TEMPLATES.TemplateResponse(request, "recursos/list.html", {
        "recursos": recursos,
        "q": q,
        "categoria": categoria,
        "categorias": CATEGORIAS_RECURSO,
        "etiquetas": ETIQUETAS_RECURSO,
        "precios_efectivos": precios_efectivos,
        "mercado_codigo": pais,
        "mercado_moneda": cfg.moneda_default or "USD",
    })

@router.get("/recursos/exportar")
def exportar_recursos(formato: str = "csv", db: Session = Depends(get_db)):
    """Exportar catálogo de recursos a CSV o Excel."""
    recursos = db.query(Recurso).order_by(Recurso.categoria, Recurso.descripcion).all()

    if formato.lower() == "excel" or formato.lower() == "xlsx":
        from ..services.excel_export import exportar_catalogo_recursos_excel
        buf = exportar_catalogo_recursos_excel(recursos, ETIQUETAS_RECURSO)
        return Response(
            content=buf.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=recursos.xlsx"},
        )

    filas = [["Código", "Descripción", "Unidad", "Categoría", "Grupo", "Precio", "Usos", "Proveedor", "Última actualización"]]
    for r in recursos:
        filas.append([
            r.codigo or "",
            r.descripcion or "",
            r.unidad or "",
            ETIQUETAS_RECURSO.get(r.categoria, r.categoria),
            r.grupo or "",
            f"{r.precio:.2f}".replace(".", ","),
            r.usos or 0,
            r.proveedor or "",
            r.fecha_actualizacion_precio.isoformat() if r.fecha_actualizacion_precio else "",
        ])
    return _csv_response(filas, "recursos.csv")

@router.post("/recursos/sincronizar")
def sincronizar_recursos(db: Session = Depends(get_db)):
    from ..services.recursos import sincronizar_recursos_desde_catalogo
    n = sincronizar_recursos_desde_catalogo(db)
    _actualizar_usos_recursos(db)
    return _redirect("/recursos", msg=f"Sincronizados {n} recursos desde descomposiciones existentes." if n else "No hay recursos nuevos para sincronizar.")

@router.get("/recursos/nuevo", response_class=HTMLResponse)
def nuevo_recurso_form(request: Request, _db: Session = Depends(get_db)):
    from ..services.traduccion import codigo_desde_pais
    cfg = _config(_db)
    pais = codigo_desde_pais(cfg.empresa_pais or "") or "VE"
    return TEMPLATES.TemplateResponse(request, "recursos/form.html", {"recurso": None, "categorias": CATEGORIAS_RECURSO, "etiquetas": ETIQUETAS_RECURSO, "mercado_codigo": pais, "mercado_moneda": cfg.moneda_default or "USD", "precio_mercado": None})

@router.post("/recursos/nuevo")
def crear_recurso(
    codigo: str = Form(""),
    descripcion: str = Form(...),
    unidad: str = Form("ud"),
    categoria: str = Form("otros"),
    grupo: str = Form(""),
    precio: str = Form("0"),
    precio_mercado: str = Form(""),
    proveedor: str = Form(""),
    db: Session = Depends(get_db),
):
    if not descripcion.strip():
        return _redirect("/recursos/nuevo", error="La descripción es obligatoria.")
    if categoria not in CATEGORIAS_RECURSO:
        categoria = "otros"
    # Evitar duplicados por clave
    from ..services.recursos import clave_recurso
    clave = clave_recurso(codigo, descripcion, unidad, categoria)
    for existente in db.query(Recurso).all():
        if existente.clave == clave:
            return _redirect("/recursos/nuevo", error="Ya existe un recurso con ese código/descripción.")
    recurso = Recurso(
        codigo=codigo.strip(),
        descripcion=descripcion.strip(),
        unidad=unidad.strip() or "ud",
        categoria=categoria,
        grupo=grupo.strip(),
        precio=max(0.0, _f(precio)),
        proveedor=proveedor.strip(),
    )
    db.add(recurso)
    db.flush()
    if str(precio_mercado or "").strip():
        from ..services.traduccion import codigo_desde_pais
        from ..services.precios_mercado import guardar_precio
        cfg = _config(db)
        pais = codigo_desde_pais(cfg.empresa_pais or "") or "VE"
        guardar_precio(db, recurso.id, pais, _f(precio_mercado), cfg.moneda_default or "USD", organizacion_id=int(db.info.get("organizacion_id") or 0), fuente="Empresa")
    db.commit()
    return _redirect("/recursos", msg="Recurso creado correctamente.")

@router.get("/recursos/{recurso_id}/editar", response_class=HTMLResponse)
def editar_recurso_form(recurso_id: int, request: Request, db: Session = Depends(get_db)):
    recurso = db.get(Recurso, recurso_id)
    if recurso is None:
        return _redirect("/recursos", error="Recurso no encontrado.")
    from ..services.traduccion import codigo_desde_pais
    from ..services.precios_mercado import resolver_precio
    cfg = _config(db)
    pais = codigo_desde_pais(cfg.empresa_pais or "") or "VE"
    precio_mercado = resolver_precio(db, recurso.id, pais, int(db.info.get("organizacion_id") or 0))
    return TEMPLATES.TemplateResponse(request, "recursos/form.html", {"recurso": recurso, "categorias": CATEGORIAS_RECURSO, "etiquetas": ETIQUETAS_RECURSO, "mercado_codigo": pais, "mercado_moneda": cfg.moneda_default or "USD", "precio_mercado": precio_mercado if precio_mercado.origen == "organizacion" else None})

@router.post("/recursos/{recurso_id}/editar")
def actualizar_recurso(
    recurso_id: int,
    codigo: str = Form(""),
    descripcion: str = Form(...),
    unidad: str = Form("ud"),
    categoria: str = Form("otros"),
    grupo: str = Form(""),
    precio: str = Form("0"),
    precio_mercado: str = Form(""),
    proveedor: str = Form(""),
    db: Session = Depends(get_db),
):
    recurso = db.get(Recurso, recurso_id)
    if recurso is None:
        return _redirect("/recursos", error="Recurso no encontrado.")
    if not descripcion.strip():
        return _redirect(f"/recursos/{recurso_id}/editar", error="La descripción es obligatoria.")
    if categoria not in CATEGORIAS_RECURSO:
        categoria = "otros"
    precio_anterior = float(recurso.precio or 0)
    nuevo_precio = max(0.0, _f(precio))
    # Verificar duplicado si cambia clave
    from ..services.recursos import clave_recurso
    nueva_clave = clave_recurso(codigo, descripcion, unidad, categoria)
    for existente in db.query(Recurso).filter(Recurso.id != recurso_id).all():
        if existente.clave == nueva_clave:
            return _redirect(f"/recursos/{recurso_id}/editar", error="Ya existe otro recurso con ese código/descripción.")
    recurso.codigo = codigo.strip()
    recurso.descripcion = descripcion.strip()
    recurso.unidad = unidad.strip() or "ud"
    recurso.categoria = categoria
    recurso.grupo = grupo.strip()
    recurso.precio = nuevo_precio
    recurso.proveedor = proveedor.strip()
    recurso.fecha_actualizacion_precio = datetime.utcnow()
    if str(precio_mercado or "").strip():
        from ..services.traduccion import codigo_desde_pais
        from ..services.precios_mercado import guardar_precio
        cfg = _config(db)
        pais = codigo_desde_pais(cfg.empresa_pais or "") or "VE"
        guardar_precio(db, recurso.id, pais, _f(precio_mercado), cfg.moneda_default or "USD", organizacion_id=int(db.info.get("organizacion_id") or 0), fuente="Empresa")
    # Propagar si cambió precio
    if abs(nuevo_precio - precio_anterior) > 1e-9:
        try:
            from ..services.recursos import propagar_precio_recurso
            res = propagar_precio_recurso(db, recurso, precio_anterior)
            db.commit()
            _actualizar_usos_recursos(db)
            auditoria.registrar_evento(
                db,
                "catalogo.precio_recurso",
                entidad="recurso",
                entidad_id=recurso.id,
                detalle={"de": precio_anterior, "a": nuevo_precio},
            )
            msg = f"Recurso actualizado a {fmt_monto(nuevo_precio, 'USD')}. Afectadas {res['partidas_afectadas']} partidas y {res['filas_presupuesto']} filas de presupuestos."
            return _redirect("/recursos", msg=msg)
        except Exception as e:
            db.commit()
            auditoria.registrar_evento(
                db,
                "catalogo.precio_recurso",
                entidad="recurso",
                entidad_id=recurso.id,
                detalle={"de": precio_anterior, "a": nuevo_precio},
            )
            return _redirect("/recursos", msg=f"Recurso actualizado (propagación parcial: {e}).")
    db.commit()
    _actualizar_usos_recursos(db)
    return _redirect("/recursos", msg="Recurso actualizado.")

@router.post("/recursos/{recurso_id}/eliminar")
def eliminar_recurso(recurso_id: int, db: Session = Depends(get_db)):
    recurso = db.get(Recurso, recurso_id)
    if recurso is None:
        return _redirect("/recursos", error="Recurso no encontrado.")
    db.delete(recurso)
    db.commit()
    return _redirect("/recursos", msg="Recurso eliminado.")

@router.post("/recursos/bulk-ajustar")
def bulk_ajustar_recursos(porcentaje: str = Form("0"), db: Session = Depends(get_db)):
    pct = _f(porcentaje)
    if pct < -100:
        return _redirect("/recursos", error="El porcentaje no puede ser menor que -100.")
    recursos = db.query(Recurso).all()
    if not recursos:
        return _redirect("/recursos", error="No hay recursos.")
    total_filas = 0
    total_partidas = 0
    for recurso in recursos:
        anterior = float(recurso.precio or 0)
        nuevo = round(anterior * (1 + pct/100), 4)
        recurso.precio = nuevo
        recurso.fecha_actualizacion_precio = datetime.utcnow()
        try:
            from ..services.recursos import propagar_precio_recurso
            res = propagar_precio_recurso(db, recurso, anterior)
            total_partidas += res.get("partidas_afectadas", 0)
            total_filas += res.get("filas_presupuesto", 0) + res.get("filas_partidas", 0)
        except Exception:
            pass
    db.commit()
    _actualizar_usos_recursos(db)
    return _redirect("/recursos", msg=f"Precios ajustados {fmt_num(pct)}% en {len(recursos)} recursos. Partidas afectadas: {total_partidas}, filas: {total_filas}.")

@router.post("/recursos/bulk-ajustar-seleccion")
async def bulk_ajustar_recursos_seleccion(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    ids = [int(x) for x in form.getlist("ids") if str(x).strip().isdigit()]
    porcentaje = _f(form.get("porcentaje"), 0)
    precio_fijo = form.get("precio_fijo", "").strip()
    if not ids:
        return _redirect("/recursos", error="Selecciona al menos un recurso.")
    recursos = db.query(Recurso).filter(Recurso.id.in_(ids)).all()
    if not recursos:
        return _redirect("/recursos", error="No se encontraron recursos seleccionados.")
    total_partidas = 0
    total_filas = 0
    for recurso in recursos:
        anterior = float(recurso.precio or 0)
        if precio_fijo != "":
            try:
                nuevo = max(0.0, float(str(precio_fijo).replace(",", ".")))
            except ValueError:
                continue
        else:
            nuevo = round(anterior * (1 + porcentaje/100), 4)
        if abs(nuevo - anterior) < 1e-9:
            continue
        recurso.precio = nuevo
        recurso.fecha_actualizacion_precio = datetime.utcnow()
        try:
            from ..services.recursos import propagar_precio_recurso
            res = propagar_precio_recurso(db, recurso, anterior)
            total_partidas += res.get("partidas_afectadas", 0)
            total_filas += res.get("filas_presupuesto", 0) + res.get("filas_partidas", 0)
        except Exception:
            pass
    db.commit()
    _actualizar_usos_recursos(db)
    if precio_fijo != "":
        return _redirect("/recursos", msg=f"Precio fijado a {precio_fijo} en {len(recursos)} recursos. Partidas afectadas: {total_partidas}.")
    return _redirect("/recursos", msg=f"Ajustados {len(recursos)} recursos {fmt_num(porcentaje)}%. Partidas afectadas: {total_partidas}.",)

@router.post("/recursos/bulk-delete")
async def bulk_delete_recursos(request: Request, db: Session = Depends(get_db)):
    ids = []
    try:
        form = await request.form()
        ids = [int(x) for x in form.getlist("ids") if str(x).strip().isdigit()]
    except Exception:
        pass
    if not ids:
        try:
            data = await request.json()
            ids = [int(x) for x in (data.get("ids") or [])]
        except Exception:
            pass
    if not ids:
        return _redirect("/recursos", error="No se seleccionaron recursos.")
    count = 0
    for rid in ids:
        r = db.get(Recurso, rid)
        if r:
            db.delete(r)
            count += 1
    db.commit()
    return _redirect("/recursos", msg=f"Se eliminaron {count} recursos.")

@router.get("/recursos/mercado", response_class=HTMLResponse)
def panel_precios_mercado(request: Request, pais: str = "", categoria: str = "", db: Session = Depends(get_db)):
    """Panel de referencias nacionales y precios de organización."""
    from ..services.precios_mercado import PrecioRecursoMercado
    query = db.query(PrecioRecursoMercado, Recurso).join(Recurso, Recurso.id == PrecioRecursoMercado.recurso_id)
    if pais.strip(): query = query.filter(PrecioRecursoMercado.pais_codigo == pais.strip().upper())
    if categoria in CATEGORIAS_RECURSO: query = query.filter(Recurso.categoria == categoria)
    filas = query.order_by(PrecioRecursoMercado.pais_codigo, Recurso.categoria, Recurso.descripcion).all()
    return TEMPLATES.TemplateResponse(request, "recursos/mercado.html", {"filas": filas, "pais": pais, "categoria": categoria, "categorias": CATEGORIAS_RECURSO})

@router.post("/recursos/mercado")
def guardar_precio_mercado(
    recurso_id: int = Form(...), pais_codigo: str = Form(...), precio: str = Form(...), moneda: str = Form(...),
    organizacion: str = Form("0"), fuente: str = Form(""), confianza: str = Form("referencia"), db: Session = Depends(get_db)
):
    from ..services.precios_mercado import guardar_precio
    org_id = int(db.info.get("organizacion_id") or 0) if organizacion == "1" else None
    guardar_precio(db, recurso_id, pais_codigo, _f(precio), moneda, organizacion_id=org_id, fuente=fuente, confianza=confianza)
    db.commit()
    return _redirect("/recursos/mercado", msg="Precio de mercado guardado.")
