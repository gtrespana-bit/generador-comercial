"""Catálogo de productos."""  # E4-001 — router por dominio

from fastapi import APIRouter

from .common import *  # noqa: F401,F403  (re-exporta modelos, servicios y utilidades)
from ..services.tasa import tasa_convertir_precio
from ..services import auditoria

router = APIRouter()

def _datos_producto_catalogo(form):
    """Contrato único para altas y ediciones, manteniendo precio_unitario como venta."""
    compra_txt = str(form.get("precio_compra", "")).strip()
    return {
        "descripcion": str(form.get("descripcion", "")).strip(),
        "precio_unitario": max(0.0, _f(form.get("precio_unitario"))),
        "precio_compra": max(0.0, _f(compra_txt)) if compra_txt else None,
        "unidad": str(form.get("unidad", "ud")).strip() or "ud",
        "categoria": str(form.get("categoria", "General")).strip() or "General",
        "marca": str(form.get("marca", "")).strip(),
        "modelo": str(form.get("modelo", "")).strip(),
        "sku": str(form.get("sku", "")).strip(),
        "proveedor": str(form.get("proveedor", "")).strip(),
        "color": str(form.get("color", "")).strip(),
        "acabado": str(form.get("acabado", "")).strip(),
        "formato": str(form.get("formato", "")).strip(),
        "tiempo_entrega_dias": _entero_opcional(form.get("tiempo_entrega_dias")),
        "variantes": str(form.get("variantes", "")).strip(),
    }


async def _guardar_imagenes_galeria(form, prefijo: str, db: Session) -> list[str]:
    rutas = []
    for archivo in form.getlist("imagenes"):
        if isinstance(archivo, UploadFileStarlette) and archivo.filename:
            ruta = await _guardar_imagen(archivo, prefijo, db)
            if ruta:
                rutas.append(ruta)
    return rutas
# ---------------------------------------------------------------------------
# Productos (Catálogo de materiales)
# ---------------------------------------------------------------------------

def _datos_producto_base(db, datos: dict) -> dict:
    """Devuelve los importes del formulario a la moneda base del catálogo."""
    _mon, factor = _contexto_moneda(db)
    if factor == 1.0:
        return datos
    convertidos = dict(datos)
    for campo in ("precio_unitario", "precio_compra"):
        if convertidos.get(campo) is not None:
            convertidos[campo] = _a_moneda_base(convertidos[campo], factor)
    return convertidos


@router.get("/productos", response_class=HTMLResponse)
def listar_productos(request: Request, q: str = "", db: Session = Depends(get_db)):
    query = db.query(Producto)
    if q.strip():
        like = f"%{q.strip()}%"
        query = query.filter(or_(
            Producto.nombre.ilike(like), Producto.categoria.ilike(like), Producto.descripcion.ilike(like),
            Producto.marca.ilike(like), Producto.modelo.ilike(like), Producto.sku.ilike(like),
            Producto.proveedor.ilike(like), Producto.color.ilike(like), Producto.acabado.ilike(like),
        ))
    productos = query.order_by(Producto.categoria, Producto.ultimo_uso.desc(), Producto.nombre).all()
    # El catálogo se guarda en la moneda base; la lista se muestra en la moneda
    # de la organización, igual que la de partidas.
    _mon_p, _factor_p = _contexto_moneda(db)
    if _factor_p != 1.0:
        for _prod in productos:
            _prod.precio_unitario = tasa_convertir_precio(_prod.precio_unitario or 0, _factor_p)
            if _prod.precio_compra is not None:
                _prod.precio_compra = tasa_convertir_precio(_prod.precio_compra, _factor_p)
    return TEMPLATES.TemplateResponse(
        request,
        "productos/list.html",
        {"productos": productos, "q": q, "moneda_vista": _mon_p},
    )


@router.get("/productos/exportar")
def exportar_productos(formato: str = "csv", db: Session = Depends(get_db)):
    """Exportar catálogo de productos a CSV o Excel con formato profesional."""
    productos = db.query(Producto).order_by(Producto.categoria, Producto.nombre).all()

    if formato.lower() == "excel" or formato.lower() == "xlsx":
        from ..services.excel_export import exportar_catalogo_productos_excel
        buf = exportar_catalogo_productos_excel(productos)
        return Response(
            content=buf.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=productos.xlsx"},
        )

    filas = [[
        "Nombre", "Marca", "Modelo", "SKU", "Descripción", "Unidad", "Precio compra", "Precio venta",
        "Categoría", "Proveedor", "Color", "Acabado", "Formato", "Entrega (días)", "Variantes",
        "Ficha técnica", "Última actualización de precio", "Usos",
    ]]
    for producto in productos:
        filas.append([
            producto.nombre, producto.marca, producto.modelo, producto.sku, producto.descripcion, producto.unidad,
            "" if producto.precio_compra is None else f"{producto.precio_compra:.2f}".replace(".", ","),
            f"{producto.precio_unitario:.2f}".replace(".", ","), producto.categoria, producto.proveedor,
            producto.color, producto.acabado, producto.formato,
            "" if producto.tiempo_entrega_dias is None else producto.tiempo_entrega_dias,
            producto.variantes, producto.ficha_tecnica,
            producto.fecha_actualizacion_precio.isoformat() if producto.fecha_actualizacion_precio else "",
            producto.usos or 0,
        ])
    return _csv_response(filas, "productos.csv")


@router.post("/productos/ajustar")
def ajustar_precios_productos(porcentaje: str = Form("0"), db: Session = Depends(get_db)):
    pct = _f(porcentaje)
    if pct < -100:
        return _redirect("/productos", error="El porcentaje no puede ser menor que -100.")
    productos = db.query(Producto).all()
    if not productos:
        return _redirect("/productos", error="No hay productos en el catálogo.")
    ahora = datetime.utcnow()
    for producto in productos:
        producto.precio_unitario = round((producto.precio_unitario or 0) * (1 + pct / 100), 2)
        producto.fecha_actualizacion_precio = ahora
    db.commit()
    return _redirect("/productos", msg=f"Precios de venta ajustados un {fmt_num(pct)} % en {len(productos)} productos.")


@router.get("/productos/nuevo", response_class=HTMLResponse)
def nuevo_producto_form(request: Request, db: Session = Depends(get_db)):
    # El formulario trabaja en la moneda de la organización, igual que la lista
    # y que el editor de partidas.
    return TEMPLATES.TemplateResponse(
        request,
        "productos/form.html",
        {"producto": None, "moneda_vista": _contexto_moneda(db)[0]},
    )


@router.post("/productos/nuevo")
async def crear_producto(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    nombre = str(form.get("nombre", "")).strip()
    if not nombre:
        return _redirect("/productos/nuevo", error="El nombre es obligatorio.")
    if db.query(Producto).filter(Producto.nombre == nombre).first():
        return _redirect("/productos/nuevo", error="Ya existe un producto con ese nombre.")
    principal = ""
    archivo = form.get("imagen")
    if isinstance(archivo, UploadFileStarlette) and archivo.filename:
        principal = await _guardar_imagen(archivo, "products/cat", db)
    galeria = _rutas_galeria(await _guardar_imagenes_galeria(form, "products/gallery", db), principal)
    ficha = ""
    archivo_ficha = form.get("ficha_tecnica")
    if isinstance(archivo_ficha, UploadFileStarlette) and archivo_ficha.filename:
        ficha = await _guardar_ficha_tecnica(archivo_ficha, "ficha", db)
    # El precio se escribe en la moneda de la organización; el catálogo lo
    # guarda en la moneda base.
    producto = Producto(
        nombre=nombre, imagen=principal, imagenes=json.dumps(galeria), ficha_tecnica=ficha,
        **_datos_producto_base(db, _datos_producto_catalogo(form)),
    )
    db.add(producto)
    db.commit()
    return _redirect("/productos", msg="Producto creado correctamente.")


@router.get("/productos/{producto_id}/editar", response_class=HTMLResponse)
def editar_producto_form(producto_id: int, request: Request, db: Session = Depends(get_db)):
    producto = db.get(Producto, producto_id)
    if producto is None:
        return _redirect("/productos", error="Producto no encontrado.")
    # Se muestra en la moneda de la organización (la misma en que se listó) y
    # el guardado deshace la conversión.
    _mon_e, _factor_e = _contexto_moneda(db)
    if _factor_e != 1.0:
        producto.precio_unitario = tasa_convertir_precio(producto.precio_unitario or 0, _factor_e)
        if producto.precio_compra is not None:
            producto.precio_compra = tasa_convertir_precio(producto.precio_compra, _factor_e)
    return TEMPLATES.TemplateResponse(
        request,
        "productos/form.html",
        {"producto": producto, "moneda_vista": _mon_e},
    )


@router.post("/productos/{producto_id}/editar")
async def actualizar_producto(producto_id: int, request: Request, db: Session = Depends(get_db)):
    producto = db.get(Producto, producto_id)
    if producto is None:
        return _redirect("/productos", error="Producto no encontrado.")
    form = await request.form()
    nombre = str(form.get("nombre", "")).strip()
    if not nombre:
        return _redirect(f"/productos/{producto_id}/editar", error="El nombre es obligatorio.")
    if db.query(Producto).filter(Producto.nombre == nombre, Producto.id != producto_id).first():
        return _redirect(f"/productos/{producto_id}/editar", error="Ya existe otro producto con ese nombre.")

    datos = _datos_producto_base(db, _datos_producto_catalogo(form))
    precio_anterior = producto.precio_unitario or 0
    producto.nombre = nombre
    for campo, valor in datos.items():
        setattr(producto, campo, valor)
    if precio_anterior != producto.precio_unitario:
        producto.fecha_actualizacion_precio = datetime.utcnow()

    galeria_inicial = producto.imagenes_lista
    quitar_galeria = set(form.getlist("quitar_imagenes"))
    galeria = [ruta for ruta in galeria_inicial if ruta not in quitar_galeria]
    principal = producto.imagen if producto.imagen not in quitar_galeria else ""
    if form.get("quitar_imagen"):
        principal = ""
        galeria = [ruta for ruta in galeria if ruta != producto.imagen]
    archivo = form.get("imagen")
    if isinstance(archivo, UploadFileStarlette) and archivo.filename:
        nueva_principal = await _guardar_imagen(archivo, f"products/cat_{producto_id}", db)
        if nueva_principal:
            galeria = [ruta for ruta in galeria if ruta != producto.imagen]
            principal = nueva_principal
            galeria.insert(0, nueva_principal)
    galeria.extend(await _guardar_imagenes_galeria(form, f"products/gallery_{producto_id}", db))
    galeria = _rutas_galeria(galeria, principal)
    if not principal and galeria:
        principal = galeria[0]
    producto.imagen = principal
    producto.imagenes = json.dumps(galeria)

    if form.get("quitar_ficha_tecnica"):
        anterior = producto.ficha_tecnica
        producto.ficha_tecnica = ""
        _borrar_imagen(anterior, db)
    else:
        archivo_ficha = form.get("ficha_tecnica")
        if isinstance(archivo_ficha, UploadFileStarlette) and archivo_ficha.filename:
            nueva_ficha = await _guardar_ficha_tecnica(archivo_ficha, f"ficha_{producto_id}", db)
            if nueva_ficha:
                anterior = producto.ficha_tecnica
                producto.ficha_tecnica = nueva_ficha
                _borrar_imagen(anterior, db)

    for ruta in set(galeria_inicial) - set(galeria):
        _borrar_imagen(ruta, db)
    db.commit()
    if precio_anterior != producto.precio_unitario:
        auditoria.registrar_evento(
            db,
            "catalogo.precio_producto",
            entidad="producto",
            entidad_id=producto.id,
            detalle={"de": precio_anterior, "a": producto.precio_unitario or 0},
        )
    return _redirect("/productos", msg="Producto actualizado.")


@router.post("/productos/{producto_id}/eliminar")
def eliminar_producto(producto_id: int, db: Session = Depends(get_db)):
    producto = db.get(Producto, producto_id)
    if producto is None:
        return _redirect("/productos", error="Producto no encontrado.")
    referencias = set(producto.imagenes_lista)
    referencias.add(producto.ficha_tecnica)
    db.delete(producto)
    for referencia in referencias:
        _borrar_imagen(referencia, db)
    db.commit()
    return _redirect("/productos", msg="Producto eliminado.")

@router.post("/productos/bulk-delete")
async def bulk_delete_productos(request: Request, db: Session = Depends(get_db)):
    ids = []
    try:
        form = await request.form()
        ids = [int(x) for x in form.getlist("ids") if str(x).strip()]
    except Exception:
        pass
    if not ids:
        try:
            data = await request.json()
            ids = [int(x) for x in (data.get("ids") or [])]
        except Exception:
            pass
    if not ids:
        return _redirect("/productos", error="No se seleccionaron productos.")
    count = 0
    referencias = set()
    for pid in ids:
        p = db.get(Producto, pid)
        if p:
            referencias.update(p.imagenes_lista)
            referencias.add(p.ficha_tecnica)
            db.delete(p)
            count += 1
    db.flush()
    for referencia in referencias:
        _borrar_imagen(referencia, db)
    db.commit()
    return _redirect("/productos", msg=f"Se eliminaron {count} productos.")


@router.post("/productos/bulk-export-selected")
async def bulk_export_selected_productos(request: Request, db: Session = Depends(get_db)):
    ids = []
    try:
        form = await request.form()
        ids = [int(x) for x in form.getlist("ids") if str(x).strip()]
    except Exception:
        pass
    if not ids:
        try:
            data = await request.json()
            ids = [int(x) for x in (data.get("ids") or [])]
        except Exception:
            pass
    if not ids:
        return _csv_response([], "productos_seleccionados.csv")

    productos = db.query(Producto).filter(Producto.id.in_(ids)).all()
    filas = [[
        "Nombre", "Marca", "Modelo", "SKU", "Descripción", "Unidad",
        "Precio compra", "Precio venta", "Categoría", "Usos"
    ]]
    for p in productos:
        filas.append([
            p.nombre,
            p.marca or "",
            p.modelo or "",
            p.sku or "",
            p.descripcion or "",
            p.unidad or "",
            "" if p.precio_compra is None else f"{p.precio_compra:.2f}".replace(".", ","),
            f"{p.precio_unitario:.2f}".replace(".", ","),
            p.categoria or "",
            p.usos or 0,
        ])
    return _csv_response(filas, "productos_seleccionados.csv")


@router.post("/productos/bulk-move-category")
async def bulk_move_productos_category(request: Request, db: Session = Depends(get_db)):
    ids = []
    new_cat = ""
    try:
        form = await request.form()
        ids = [int(x) for x in form.getlist("ids") if str(x).strip()]
        new_cat = (form.get("new_category") or "").strip()
    except Exception:
        pass
    if not ids or not new_cat:
        return _redirect("/productos", error="Selecciona productos y una categoría destino.")
    count = 0
    for pid in ids:
        p = db.get(Producto, pid)
        if p:
            p.categoria = new_cat
            count += 1
    db.commit()
    return _redirect("/productos", msg=f"Se movieron {count} productos a «{new_cat}».")
