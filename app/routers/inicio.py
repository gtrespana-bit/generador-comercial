"""Inicio (panel), reportes y búsqueda global."""  # E4-001 — router por dominio

from fastapi import APIRouter

from . import common
from .common import *  # noqa: F401,F403  (re-exporta modelos, servicios y utilidades)
from ..services.salud_catalogo import analizar_salud_catalogo

router = APIRouter()

# ---------------------------------------------------------------------------
# Inicio
# ---------------------------------------------------------------------------

@router.get("/guia-rapida", response_class=HTMLResponse)
def guia_rapida(request: Request):
    return TEMPLATES.TemplateResponse(request, "guia_rapida.html", {})


@router.get("/inicio", response_class=HTMLResponse)
def inicio(request: Request, db: Session = Depends(get_db)):
    cfg = _config(db)
    if not cfg.onboarding_completado:
        return _redirect("/bienvenida")
    hoy = date.today()
    fin_semana = hoy + timedelta(days=7)
    mes_inicio = hoy.replace(day=1)

    # El panel NO hidrata el histórico completo ni los descompuestos CYPE.
    # Eso era lo que hacía /inicio la página más lenta de la app (cada
    # presupuesto arrastraba capítulos, partidas, mediciones y APU).
    from sqlalchemy import func as _func

    estados_aprobados = ("aprobado", "aprobado_parcialmente", "en_ejecucion", "finalizado")
    estados_enviados = ("enviado", "reenviado", *estados_aprobados)
    moneda_panel, factor_panel = common._contexto_moneda(db)

    def _importe_panel(p, valor):
        return common._importe_en_moneda_vista(valor, p, moneda_panel, factor_panel)

    por_estado = {e: 0 for e in ESTADOS}
    for estado, n in db.query(Presupuesto.estado, _func.count(Presupuesto.id)).group_by(Presupuesto.estado):
        por_estado[estado] = int(n or 0)
    total_presupuestos = sum(por_estado.values())
    total_enviados = sum(por_estado.get(e, 0) for e in estados_enviados)
    total_aprobados = sum(por_estado.get(e, 0) for e in estados_aprobados)

    # Cabeceras ligeras para vencimientos y recuentos del mes (sin partidas).
    cabeceras = db.query(
        Presupuesto.id,
        Presupuesto.estado,
        Presupuesto.fecha,
        Presupuesto.validez_dias,
        Presupuesto.moneda,
        Presupuesto.tipo_cambio,
    ).all()
    por_vencer = 0
    presupuestos_mes = 0
    enviados_mes = 0
    aprobados_mes = 0
    for fila in cabeceras:
        if fila.estado == "enviado" and fila.validez_dias and fila.fecha and hoy <= fila.fecha + timedelta(days=fila.validez_dias) <= fin_semana:
            por_vencer += 1
        if fila.fecha and fila.fecha >= mes_inicio:
            presupuestos_mes += 1
            if fila.estado in ("enviado", "reenviado"):
                enviados_mes += 1
            if fila.estado in ("aprobado", "aprobado_parcialmente"):
                aprobados_mes += 1

    # Totales monetarios: columna cacheada; no se hidrata el grafo.
    para_dinero = (
        db.query(Presupuesto)
        .options(load_only(
            Presupuesto.id, Presupuesto.estado, Presupuesto.fecha,
            Presupuesto.moneda, Presupuesto.tipo_cambio, Presupuesto.total_calculado,
        ))
        .filter(Presupuesto.estado.in_(("aprobado", *estados_aprobados)))
        .all()
    )
    importe_aprobado = 0.0
    descuentos_concedidos = 0.0
    margen_estimado = 0.0
    importes_mes = []
    for p in para_dinero:
        cached = p.total_calculado
        if cached is None:
            continue
        total_p = _importe_panel(p, cached)
        if p.estado == "aprobado" and total_p is not None:
            importe_aprobado += total_p
        if p.fecha and p.fecha >= mes_inicio and total_p is not None:
            importes_mes.append(total_p)

    recientes = (
        db.query(Presupuesto)
        .options(joinedload(Presupuesto.cliente))
        .order_by(Presupuesto.id.desc())
        .limit(6)
        .all()
    )
    total_clientes = db.query(Cliente).count()
    total_facturas = db.query(Factura).count()
    proyectos_activos = db.query(Proyecto).filter(Proyecto.estado.in_(["en_ejecucion", "pausado"])).count()
    analisis_precios = analizar_catalogo_partidas(db)
    analisis_precios["alertas"] = (analisis_precios.get("alertas") or [])[:8]
    # El recuento de precios absurdos recorre otra vez las 3.000 partidas:
    # en el panel basta el diagnóstico de columnas (precio/coste/tiempo).
    salud_catalogo = analizar_salud_catalogo(db, incluir_anomalias=False)
    recorrido_inicial = (
        estado_recorrido_inicial(db, cfg)
        if cfg.onboarding_modo in {"demo", "limpio"} and not getattr(cfg, "recorrido_inicial_oculto", False)
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
            # Estos tres valores ya son contadores enteros. No aplicar len():
            # el panel debe abrir también cuando el mes no tiene presupuestos.
            "presupuestos_mes": presupuestos_mes,
            "enviados_mes": enviados_mes,
            "aprobados_mes": aprobados_mes,
            "tasa_aprobacion": round(total_aprobados * 100 / total_enviados, 1) if total_enviados else 0,
            "importe_promedio": sum(importes_mes) / len(importes_mes) if importes_mes else 0,
            "descuentos_concedidos": descuentos_concedidos, "margen_estimado": margen_estimado,
            "proyectos_activos": proyectos_activos,
            "analisis_precios": analisis_precios,
            "salud_catalogo": salud_catalogo,
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
    presupuestos = (
        db.query(Presupuesto)
        .options(*common._opciones_partidas_presupuesto())
        .filter(Presupuesto.fecha >= inicio, Presupuesto.fecha <= fin)
        .all()
    )
    # Reportes en UNA moneda: la de la organización. Cada total se convierte
    # por USD con la tasa congelada del propio presupuesto; sin tasa no se
    # suma (antes se mezclaban monedas distintas bajo una sola etiqueta).
    moneda_vista, factor_vista = common._contexto_moneda(db)
    importe_de = {
        p.id: common._importe_en_moneda_vista(p.total, p, moneda_vista, factor_vista)
        for p in presupuestos
    }
    por_estado = {e: [p for p in presupuestos if p.estado == e] for e in ESTADOS}
    importes_estado = {
        e: sum(importe_de[p.id] or 0 for p in items if importe_de[p.id] is not None)
        for e, items in por_estado.items()
    }
    importe_total = sum(v for v in importe_de.values() if v is not None)
    clientes = {}
    for p in presupuestos:
        convertido = importe_de.get(p.id)
        if convertido is None:
            continue
        clientes[p.cliente.nombre] = clientes.get(p.cliente.nombre, 0) + convertido
    return TEMPLATES.TemplateResponse(request, "reports.html", {"desde": inicio.isoformat(), "hasta": fin.isoformat(), "presupuestos": presupuestos, "por_estado": por_estado, "importes_estado": importes_estado, "importe_total": importe_total, "clientes": sorted(clientes.items(), key=lambda x:x[1], reverse=True), "proyectos": db.query(Proyecto).all(), "moneda_vista": moneda_vista})

@router.get("/reportes/exportar")
def exportar_reporte(tipo: str = "ventas", desde: str = "", hasta: str = "", db: Session = Depends(get_db)):
    try: inicio=date.fromisoformat(desde) if desde else date.min
    except ValueError: inicio=date.min
    try: fin=date.fromisoformat(hasta) if hasta else date.max
    except ValueError: fin=date.max
    ps=(
        db.query(Presupuesto)
        .options(*common._opciones_partidas_presupuesto())
        .filter(Presupuesto.fecha >= inicio, Presupuesto.fecha <= fin)
        .all()
    )
    if tipo == "estados":
        _moneda_e, _factor_e = common._contexto_moneda(db)
        def _total_e(p):
            v = common._importe_en_moneda_vista(p.total, p, _moneda_e, _factor_e)
            return v if v is not None else 0
        filas=[["Estado","Cantidad","Total","Moneda"]]+[[e, len([p for p in ps if p.estado==e]), round(sum(_total_e(p) for p in ps if p.estado==e), 2), _moneda_e] for e in ESTADOS]
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
