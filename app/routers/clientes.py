"""Clientes."""  # E4-001 — router por dominio

from fastapi import APIRouter

from .common import *  # noqa: F401,F403  (re-exporta modelos, servicios y utilidades)

router = APIRouter()

# ---------------------------------------------------------------------------
# Clientes
# ---------------------------------------------------------------------------

@router.get("/clientes", response_class=HTMLResponse)
def listar_clientes(request: Request, q: str = "", db: Session = Depends(get_db)):
    query = db.query(Cliente)
    if q.strip():
        like = f"%{q.strip()}%"
        query = query.filter(or_(Cliente.nombre.ilike(like), Cliente.rif.ilike(like), Cliente.email.ilike(like)))
    clientes = query.order_by(Cliente.nombre).all()
    return TEMPLATES.TemplateResponse(request, "clients/list.html", {"clientes": clientes, "q": q})


@router.get("/clientes/nuevo", response_class=HTMLResponse)
def nuevo_cliente_form(request: Request, _db: Session = Depends(get_db)):
    return TEMPLATES.TemplateResponse(request, "clients/form.html", {"cliente": None})


@router.post("/clientes/nuevo")
def crear_cliente(
    nombre: str = Form(...),
    rif: str = Form(""),
    pais: str = Form("Venezuela"),
    telefono: str = Form(""),
    email: str = Form(""),
    direccion: str = Form(""),
    db: Session = Depends(get_db),
):
    if not nombre.strip():
        return _redirect("/clientes/nuevo", error="El nombre del cliente es obligatorio.")
    cliente = Cliente(nombre=nombre.strip(), rif=rif.strip(), pais=pais.strip() or "Venezuela",
                      telefono=telefono.strip(), email=email.strip(), direccion=direccion.strip())
    db.add(cliente)
    db.commit()
    return _redirect(f"/clientes/{cliente.id}/editar", msg="Cliente creado correctamente.")


@router.get("/clientes/{cliente_id}/editar", response_class=HTMLResponse)
def editar_cliente_form(cliente_id: int, request: Request, db: Session = Depends(get_db)):
    cliente = db.get(Cliente, cliente_id)
    if cliente is None:
        return _redirect("/clientes", error="Cliente no encontrado.")
    return TEMPLATES.TemplateResponse(request, "clients/form.html", {"cliente": cliente})


@router.post("/clientes/{cliente_id}/editar")
def actualizar_cliente(
    cliente_id: int,
    nombre: str = Form(...),
    rif: str = Form(""),
    pais: str = Form("Venezuela"),
    telefono: str = Form(""),
    email: str = Form(""),
    direccion: str = Form(""),
    db: Session = Depends(get_db),
):
    cliente = db.get(Cliente, cliente_id)
    if cliente is None:
        return _redirect("/clientes", error="Cliente no encontrado.")
    if not nombre.strip():
        return _redirect(f"/clientes/{cliente_id}/editar", error="El nombre del cliente es obligatorio.")
    cliente.nombre = nombre.strip()
    cliente.rif = rif.strip()
    cliente.pais = pais.strip() or "Venezuela"
    cliente.telefono = telefono.strip()
    cliente.email = email.strip()
    cliente.direccion = direccion.strip()
    db.commit()
    return _redirect(f"/clientes/{cliente_id}/editar", msg="Cliente actualizado correctamente.")


@router.post("/clientes/{cliente_id}/eliminar")
def eliminar_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.get(Cliente, cliente_id)
    if cliente is None:
        return _redirect("/clientes", error="Cliente no encontrado.")
    num_presupuestos = db.query(Presupuesto).filter(Presupuesto.client_id == cliente_id).count()
    num_facturas = db.query(Factura).filter(Factura.client_id == cliente_id).count()
    if num_presupuestos or num_facturas:
        detalles = []
        if num_presupuestos:
            detalles.append(f"{num_presupuestos} presupuesto(s)")
        if num_facturas:
            detalles.append(f"{num_facturas} documento(s) de cobro")
        return _redirect(f"/clientes/{cliente_id}/editar",
                         error="No se puede eliminar: tiene " + " y ".join(detalles) + " asociado(s).")
    db.delete(cliente)
    db.commit()
    return _redirect("/clientes", msg="Cliente eliminado.")
