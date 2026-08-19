"""Inicio (panel), reportes y búsqueda global."""  # E4-001 — router por dominio

from fastapi import APIRouter

from . import common
from .common import *  # noqa: F401,F403  (re-exporta modelos, servicios y utilidades)

router = APIRouter()

# ---------------------------------------------------------------------------
# Inicio
# ---------------------------------------------------------------------------

@router.get("/inicio", response_class=HTMLResponse)
def inicio(request: Request, db: Session = Depends(get_db)):
    cfg = _config(db)
    if not cfg.onboarding_completado:
        return _redirect("/bienvenida")
    hoy = date.today()
    fin_semana = hoy + timedelta(days=7)
    mes_inicio = hoy.replace(day=1)

    # Una sola lectura del histórico: antes cada indicador hacía su propia
    # pasada completa sobre ``presupuestos`` (hasta ~10 consultas a la tabla
    # entera). Con catálogos y presupuestos creciendo, esto se traduce en un
    # dashboard visiblemente más rápido en instalaciones grandes.
    estados_aprobados = ("aprobado", "aprobado_parcialmente", "en_ejecucion", "finalizado")
    estados_enviados = ("enviado", "reenviado", *estados_aprobados)
    todos = db.query(Presupuesto).all()

    total_presupuestos = len(todos)
    por_estado = {e: 0 for e in ESTADOS}
    importe_aprobado = 0.0
    descuentos_concedidos = 0.0
    margen_estimado = 0.0
    total_enviados = 0
    total_aprobados = 0
    por_vencer = 0
    presupuestos_mes = []
    enviados_mes = 0
    aprobados_mes = []
    for p in todos:
        por_estado[p.estado] = por_estado.get(p.estado, 0) + 1
        if p.estado == "aprobado":
            importe_aprobado += p.total or 0
        descuentos_concedidos += p.descuento_monto or 0
        if p.estado in estados_enviados:
            total_enviados += 1
        if p.estado in estados_aprobados:
            total_aprobados += 1
            margen_estimado += p.margen or 0
        if p.estado == "enviado" and p.validez_dias and hoy <= p.fecha + timedelta(days=p.validez_dias) <= fin_semana:
            por_vencer += 1
        if p.fecha and p.fecha >= mes_inicio:
            presupuestos_mes.append(p)
            if p.estado in ("enviado", "reenviado"):
                enviados_mes += 1
            if p.estado in ("aprobado", "aprobado_parcialmente"):
                aprobados_mes.append(p)

    recientes = sorted(todos, key=lambda p: p.id, reverse=True)[:6]
    total_clientes = db.query(Cliente).count()
    total_facturas = db.query(Factura).count()
    proyectos_activos = db.query(Proyecto).filter(Proyecto.estado.in_(["en_ejecucion", "pausado"])).count()
    analisis_precios = analizar_catalogo_partidas(db)
    recorrido_inicial = (
        estado_recorrido_inicial(db, cfg)
        if cfg.onboarding_modo in {"demo", "limpio"}
        else None
    )

    # Intención de compra retomable: si la persona eligió un plan antes de
    # crear su cuenta/organización y todavía no tiene licencia activa, se le
    # ofrece retomar el checkout desde el panel en vez de perder la compra.
    compra_pendiente = ""
    compra_pendiente_ficha = None
    from ..datos_pago import PLANES, PLAN_PENDIENTE_COOKIE, plan_info

    plan_recordado = request.cookies.get(PLAN_PENDIENTE_COOKIE, "").strip()
    if plan_recordado in PLANES:
        resumen = getattr(request.state, "licencia_resumen", None) or {}
        if not resumen.get("activo"):
            compra_pendiente = plan_recordado
            compra_pendiente_ficha = plan_info(plan_recordado)

    return TEMPLATES.TemplateResponse(
        request,
        "index.html",
        {
            "total_presupuestos": total_presupuestos,
            "total_clientes": total_clientes,
            # Los importes del panel se etiquetan con el ISO de la moneda de la
            # organización: «$» no distingue MXN de USD ni de COP.
            "moneda_vista": common._contexto_moneda(db)[0],
            "por_estado": por_estado,
            "importe_aprobado": importe_aprobado,
            "recientes": recientes,
            "estados": ESTADOS,
            "por_vencer": por_vencer,
            "total_facturas": total_facturas,
            "presupuestos_mes": len(presupuestos_mes), "enviados_mes": enviados_mes,
            "aprobados_mes": len(aprobados_mes), "tasa_aprobacion": round(total_aprobados * 100 / total_enviados, 1) if total_enviados else 0,
            "importe_promedio": sum(p.total for p in presupuestos_mes) / len(presupuestos_mes) if presupuestos_mes else 0,
            "descuentos_concedidos": descuentos_concedidos, "margen_estimado": margen_estimado,
            "proyectos_activos": proyectos_activos,
            "analisis_precios": analisis_precios,
            "recorrido_inicial": recorrido_inicial,
            "compra_pendiente": compra_pendiente,
            "compra_pendiente_ficha": compra_pendiente_ficha,
        },
    )


@router.post("/presupuestos/actualizar-vencidos")
def actualizar_presupuestos_vencidos(db: Session = Depends(get_db)):
    if es_lectura(db):
        return {"ok": True, "actualizados": 0}
    return {"ok": True, "actualizados": common.marcar_vencidos(db)}


@router.get("/presupuestos/optimizar-precios", response_class=HTMLResponse)
def optimizar_precios(request: Request, db: Session = Depends(get_db)):
    """Análisis real (basado en tus propios datos) de márgenes y precios sin
    revisar en el catálogo de partidas. Reemplaza al antiguo botón que sólo
    mostraba un mensaje fijo sin hacer ningún cálculo."""
    analisis = analizar_catalogo_partidas(db)
    # El análisis lee el catálogo (moneda base): se muestra en la moneda de la
    # organización para no comparar dólares con pesos en la misma tabla.
    _mon_o, _factor_o = common._contexto_moneda(db)
    if _factor_o != 1.0:
        for alerta in analisis.get("alertas", []):
            for campo in ("precio_unitario", "coste_unitario"):
                if isinstance(alerta.get(campo), (int, float)):
                    alerta[campo] = common.tasa_convertir_precio(alerta[campo], _factor_o)
    return TEMPLATES.TemplateResponse(
        request,
        "budgets/optimizar.html",
        {"analisis": analisis, "moneda_vista": _mon_o},
    )


# ---------------------------------------------------------------------------
# Reportes
# ---------------------------------------------------------------------------
@router.get("/reportes", response_class=HTMLResponse)
def reportes(request: Request, desde: str = "", hasta: str = "", db: Session = Depends(get_db)):
    try: inicio = date.fromisoformat(desde) if desde else date.today().replace(day=1)
    except ValueError: inicio = date.today().replace(day=1)
    try: fin = date.fromisoformat(hasta) if hasta else date.today()
    except ValueError: fin = date.today()
    presupuestos = db.query(Presupuesto).filter(Presupuesto.fecha >= inicio, Presupuesto.fecha <= fin).all()
    por_estado = {e: [p for p in presupuestos if p.estado == e] for e in ESTADOS}
    clientes = {}
    for p in presupuestos: clientes[p.cliente.nombre] = clientes.get(p.cliente.nombre, 0) + p.total
    return TEMPLATES.TemplateResponse(request, "reports.html", {"desde": inicio.isoformat(), "hasta": fin.isoformat(), "presupuestos": presupuestos, "por_estado": por_estado, "clientes": sorted(clientes.items(), key=lambda x:x[1], reverse=True), "proyectos": db.query(Proyecto).all(), "moneda_vista": common._contexto_moneda(db)[0]})

@router.get("/reportes/exportar")
def exportar_reporte(tipo: str = "ventas", desde: str = "", hasta: str = "", db: Session = Depends(get_db)):
    try: inicio=date.fromisoformat(desde) if desde else date.min
    except ValueError: inicio=date.min
    try: fin=date.fromisoformat(hasta) if hasta else date.max
    except ValueError: fin=date.max
    ps=db.query(Presupuesto).filter(Presupuesto.fecha >= inicio, Presupuesto.fecha <= fin).all()
    if tipo == "estados": filas=[["Estado","Cantidad","Total"]]+[[e, len([p for p in ps if p.estado==e]), sum(p.total for p in ps if p.estado==e)] for e in ESTADOS]
    elif tipo == "proyectos": filas=[["Proyecto","Cliente","Estado","Contratado","Cambios","Pagado","Saldo"]]+[[p.nombre,p.presupuesto.cliente.nombre,p.estado,p.total_contratado,p.total_cambios_aprobados,p.total_pagado,p.saldo_pendiente] for p in db.query(Proyecto).all()]
    else: filas=[["Número","Fecha","Cliente","Estado","Moneda","Total"]]+[[p.numero,p.fecha.isoformat(),p.cliente.nombre,p.estado,p.moneda,p.total] for p in ps]
    return _csv_response(filas, f"reporte_{tipo}.csv")


# ---------------------------------------------------------------------------
# Búsqueda global
# ---------------------------------------------------------------------------

@router.get("/buscar", response_class=HTMLResponse)
def busqueda_global(request: Request, q: str = "", db: Session = Depends(get_db)):
    """Busca una vez en todas las entidades disponibles y agrupa resultados."""
    consulta = q.strip()[:100]
    resultados = {
        "clientes": [], "presupuestos": [], "facturas": [], "partidas": [],
        "productos": [], "plantillas": [], "recetas": [], "notas": [],
    }
    if consulta:
        like = f"%{consulta}%"
        resultados["clientes"] = db.query(Cliente).filter(or_(
            Cliente.nombre.ilike(like), Cliente.rif.ilike(like), Cliente.email.ilike(like),
            Cliente.telefono.ilike(like), Cliente.direccion.ilike(like),
        )).order_by(Cliente.nombre).limit(12).all()
        resultados["presupuestos"] = db.query(Presupuesto).join(Cliente).filter(or_(
            Presupuesto.numero.ilike(like), Presupuesto.titulo.ilike(like),
            Presupuesto.direccion_obra.ilike(like), Cliente.nombre.ilike(like),
        )).order_by(Presupuesto.id.desc()).limit(12).all()
        resultados["facturas"] = db.query(Factura).join(Cliente).filter(or_(
            Factura.numero.ilike(like), Factura.titulo.ilike(like),
            Factura.direccion_obra.ilike(like), Cliente.nombre.ilike(like),
        )).order_by(Factura.id.desc()).limit(12).all()
        resultados["partidas"] = db.query(Partida).filter(
            Partida.oculta.is_(False)
        ).filter(or_(
            Partida.nombre.ilike(like), Partida.descripcion.ilike(like),
            Partida.codigo_interno.ilike(like), Partida.codigo_legacy.ilike(like),
            Partida.categoria.ilike(like), Partida.subcategoria.ilike(like),
            Partida.apartado.ilike(like), Partida.proveedor.ilike(like),
        )).order_by(Partida.ultimo_uso.desc(), Partida.nombre).limit(12).all()
        resultados["productos"] = db.query(Producto).filter(or_(
            Producto.nombre.ilike(like), Producto.descripcion.ilike(like), Producto.sku.ilike(like),
            Producto.marca.ilike(like), Producto.modelo.ilike(like), Producto.categoria.ilike(like),
            Producto.proveedor.ilike(like),
        )).order_by(Producto.ultimo_uso.desc(), Producto.nombre).limit(12).all()
        resultados["plantillas"] = db.query(Plantilla).filter(Plantilla.nombre.ilike(like)).order_by(Plantilla.nombre).limit(12).all()
        resultados["recetas"] = db.query(RecetaEstancia).filter(or_(
            RecetaEstancia.nombre.ilike(like), RecetaEstancia.descripcion.ilike(like),
            RecetaEstancia.categoria.ilike(like),
        )).order_by(RecetaEstancia.nombre).limit(12).all()
        resultados["notas"] = db.query(NotaSeguimiento).join(Presupuesto).filter(or_(
            NotaSeguimiento.texto.ilike(like), Presupuesto.numero.ilike(like), Presupuesto.titulo.ilike(like),
        )).order_by(NotaSeguimiento.created_at.desc()).limit(12).all()
    total = sum(len(grupo) for grupo in resultados.values())
    # Partidas y productos vienen del catálogo (moneda base): se convierten a
    # la moneda de la organización para que el buscador no muestre dólares
    # sueltos entre importes locales.
    _mon_s, _factor_s = common._contexto_moneda(db)
    if _factor_s != 1.0:
        for _item in list(resultados.get("partidas", [])) + list(resultados.get("productos", [])):
            _item.precio_unitario = common.tasa_convertir_precio(_item.precio_unitario or 0, _factor_s)
    return TEMPLATES.TemplateResponse(request, "search.html", {
        "q": q, "consulta": consulta, "resultados": resultados, "total": total,
        "moneda_vista": _mon_s,
    })
