"""Catálogo de recursos (precios unitarios)."""  # E4-001 — router por dominio

from fastapi import APIRouter

from .common import *  # noqa: F401,F403  (re-exporta modelos, servicios y utilidades)
from ..services import auditoria
from ..services.tasa import tasa_convertir_precio

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

def _norm_recurso(v: str) -> str:
    t = unicodedata.normalize("NFD", str(v or "").strip().lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "", t)


def _fila_coincide_recurso(fila: dict, recurso: Recurso) -> bool:
    if not isinstance(fila, dict):
        return False
    cod_recurso = _norm_recurso(recurso.codigo)
    cod_fila = _norm_recurso(fila.get("codigo"))
    if cod_recurso and cod_fila:
        return cod_recurso == cod_fila
    return (
        _norm_recurso(fila.get("descripcion")) == _norm_recurso(recurso.descripcion)
        and _norm_recurso(fila.get("unidad")) == _norm_recurso(recurso.unidad)
    )


def _partidas_afectadas_por_recurso(db: Session, recurso: Recurso) -> list[dict]:
    afectadas = []
    for partida in db.query(Partida).filter(Partida.oculta.is_(False)).all():
        try:
            raw = json.loads(partida.descomposicion_json or "[]")
            filas = raw.get("filas", []) if isinstance(raw, dict) else raw
        except (TypeError, ValueError):
            filas = []
        total = sum(1 for fila in filas if _fila_coincide_recurso(fila, recurso))
        if total:
            afectadas.append({
                "id": partida.id,
                "nombre": partida.nombre,
                "ruta": partida.ruta_catalogo,
                "filas": total,
            })
    return afectadas


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
    # Sincronización automática: crea los recursos que falten desde las
    # descomposiciones (partidas y presupuestos) y actualiza usos. Es
    # idempotente; en la vista se ejecuta con un intervalo mínimo por
    # organización porque recorre todos los descompuestos y, en el despliegue
    # web con base remota, era la mayor parte del tiempo de carga de la
    # página. Los guardados siguen forzándola para reflejar cambios al instante.
    _sincronizar_recursos(db, forzar=False)
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
    from ..services.precios_mercado import resolver_precios_para_presupuesto_lote
    cfg = _config(db)
    pais = codigo_desde_pais(cfg.empresa_pais or "") or "VE"
    org_id = int(db.info.get("organizacion_id") or 0)
    # UNA consulta para todos los recursos (antes: dos SELECT por recurso).
    # Moneda única de la vista: el catálogo se guarda en USD y TODO lo que ve
    # el usuario (precio base y precio de mercado) se muestra en la moneda de
    # la organización, convertido con la misma tasa. Sin esto la lista
    # mezclaba dólares (base) con la moneda del mercado en la misma tabla.
    moneda_vista, factor_vista = _contexto_moneda(db)
    efectivos = resolver_precios_para_presupuesto_lote(
        db, recursos, pais, org_id or None, moneda_vista,
        tasa_usd_presupuesto=factor_vista,
    )
    precios_vista: dict[int, dict] = {}
    totales_categoria: dict[str, float] = {}
    for r in recursos:
        base_vista = tasa_convertir_precio(r.precio or 0, factor_vista)
        efectivo = efectivos.get(r.id) or {}
        mercado_vista = None
        if efectivo.get("precio") is not None and not efectivo.get("requiere_tasa"):
            mercado_vista = float(efectivo["precio"])
        es_mercado = bool(
            mercado_vista is not None
            and (efectivo.get("origen") or "base") in ("nacional", "organizacion")
        )
        precios_vista[r.id] = {
            "base": base_vista,  # solo interno/fallback, nunca se muestra
            "mercado": mercado_vista if es_mercado else None,
            "origen": efectivo.get("origen", "base"),
            "aviso": efectivo.get("aviso", ""),
            "requiere_tasa": bool(efectivo.get("requiere_tasa")),
        }
        # El total por categoría suma únicamente referencias de mercado o del
        # propio usuario. El precio base (Partida Venezuela convertida) no
        # cuenta: nunca debe contaminar el total visible de un mercado.
        if es_mercado:
            totales_categoria[r.categoria] = (
                totales_categoria.get(r.categoria, 0.0) + mercado_vista
            )
    # Agrupar por categoria
    return TEMPLATES.TemplateResponse(request, "recursos/list.html", {
        "recursos": recursos,
        "q": q,
        "categoria": categoria,
        "categorias": CATEGORIAS_RECURSO,
        "etiquetas": ETIQUETAS_RECURSO,
        "precios_vista": precios_vista,
        "totales_categoria": totales_categoria,
        "moneda_vista": moneda_vista,
        "mercado_codigo": pais,
        "mercado_moneda": cfg.moneda_default or "USD",
    })

@router.get("/recursos/exportar")
def exportar_recursos(formato: str = "csv", db: Session = Depends(get_db)):
    """Exportar catálogo de recursos a CSV o Excel.

    La exportación, igual que la lista, usa la referencia nacional cuando
    existe: el precio exportado debe ser el del mercado del país, no el precio
    base (Partida Venezuela) convertido con la tasa.
    """
    recursos = db.query(Recurso).order_by(Recurso.categoria, Recurso.descripcion).all()
    from ..services.traduccion import codigo_desde_pais
    from ..services.precios_mercado import resolver_precios_para_presupuesto_lote

    _moneda_x, _factor_x = _contexto_moneda(db)
    _cfg_x = _config(db)
    _pais_x = codigo_desde_pais(getattr(_cfg_x, "empresa_pais", "") or "") or "VE"
    _org_x = int(db.info.get("organizacion_id") or 0) or None
    try:
        efectivos_x = resolver_precios_para_presupuesto_lote(
            db, recursos, _pais_x, _org_x, _moneda_x, tasa_usd_presupuesto=_factor_x,
        )
    except Exception:
        efectivos_x = {}

    def _precio_export(r):
        """Precio visible para exportar: solo mercado o precio propio.

        El precio base del catálogo no se exporta como si fuera un precio de
        mercado; cuando no hay referencia se deja vacío para que el destinatario
        no confunda la partida original convertida con un precio real de país.
        """
        ef = efectivos_x.get(r.id)
        if ef is not None and ef.get("precio") is not None and not ef.get("requiere_tasa"):
            return float(ef["precio"])
        return None

    if formato.lower() == "excel" or formato.lower() == "xlsx":
        from ..services.excel_export import exportar_catalogo_recursos_excel
        buf = exportar_catalogo_recursos_excel(
            recursos, ETIQUETAS_RECURSO, moneda=_moneda_x, factor=1.0,
            precios_efectivos={r.id: _precio_export(r) for r in recursos},
        )
        return Response(
            content=buf.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=recursos.xlsx"},
        )

    # La exportación habla la misma moneda que la página: la de la
    # organización (el catálogo interno sigue en USD).
    filas = [["Código", "Descripción", "Unidad", "Categoría", "Grupo", "Precio", "Moneda", "Usos", "Proveedor", "Última actualización"]]
    for r in recursos:
        filas.append([
            r.codigo or "",
            r.descripcion or "",
            r.unidad or "",
            ETIQUETAS_RECURSO.get(r.categoria, r.categoria),
            r.grupo or "",
            (f"{_precio_export(r):.2f}".replace(".", ",") if _precio_export(r) is not None else ""),
            _moneda_x,
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
    # El formulario edita en la moneda de la organización (igual que la lista
    # y que el editor de partidas); el catálogo sigue guardando USD y el POST
    # deshace la conversión antes de persistir.
    moneda_vista, _factor = _contexto_moneda(_db)
    return TEMPLATES.TemplateResponse(request, "recursos/form.html", {
        "recurso": None,
        "categorias": CATEGORIAS_RECURSO,
        "etiquetas": ETIQUETAS_RECURSO,
        "mercado_codigo": pais,
        "mercado_moneda": cfg.moneda_default or "USD",
        "moneda_vista": moneda_vista,
        "precio_vista": 0,
        "precio_mercado": None,
        "precio_mercado_vista": None,
        "precio_referencia_nacional_vista": None,
    })

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
    subtipo: str = Form(""),
    capacidad: str = Form(""),
    modalidad_tarifa: str = Form("hora"),
    incluye_operador: str = Form(""),
    incluye_combustible: str = Form(""),
    incluye_flete: str = Form(""),
    rendimiento_jornada: str = Form(""),
    db: Session = Depends(get_db),
):
    if not descripcion.strip():
        return _redirect("/recursos/nuevo", error="La descripción es obligatoria.")
    if categoria not in CATEGORIAS_RECURSO:
        categoria = "otros"
    # El formulario edita en la moneda de la organización; el catálogo guarda
    # la base USD. Sin revertir la conversión, «650 COP» quedaba guardado
    # como 650 USD y el precio se multiplicaba por la tasa en cada re-lectura.
    _moneda_c, _factor_c = _contexto_moneda(db)
    precio_base = _a_moneda_base(max(0.0, _f(precio)), _factor_c)
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
        precio=precio_base,
        proveedor=proveedor.strip(),
        subtipo=subtipo.strip(), capacidad=capacidad.strip(), modalidad_tarifa=modalidad_tarifa.strip() or "hora",
        incluye_operador=bool(incluye_operador), incluye_combustible=bool(incluye_combustible), incluye_flete=bool(incluye_flete),
        rendimiento_jornada=_f(rendimiento_jornada, None),
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


@router.get("/recursos/{recurso_id}/impacto", response_class=HTMLResponse)
def impacto_recurso(recurso_id: int, request: Request, db: Session = Depends(get_db)):
    recurso = db.get(Recurso, recurso_id)
    if recurso is None:
        return _redirect("/recursos", error="Recurso no encontrado.")
    partidas = _partidas_afectadas_por_recurso(db, recurso)
    from ..services.traduccion import codigo_desde_pais
    from ..services.precios_mercado import resolver_precio
    _moneda, _factor = _contexto_moneda(db)
    cfg_i = _config(db)
    pais_i = codigo_desde_pais(getattr(cfg_i, "empresa_pais", "") or "") or "VE"
    precio_mercado_i = resolver_precio(db, recurso.id, pais_i, int(db.info.get("organizacion_id") or 0))
    precio_vista_i = None
    if precio_mercado_i is not None and precio_mercado_i.precio is not None and precio_mercado_i.origen != "base":
        from ..utils import normalizar_moneda
        moneda_org_i = normalizar_moneda(_moneda, "USD")
        moneda_mercado_i = normalizar_moneda(precio_mercado_i.moneda or "USD", "USD")
        if moneda_mercado_i == moneda_org_i:
            precio_vista_i = float(precio_mercado_i.precio)
        elif moneda_mercado_i == "USD":
            precio_vista_i = tasa_convertir_precio(precio_mercado_i.precio, _factor)
    return TEMPLATES.TemplateResponse(request, "recursos/impacto.html", {
        "recurso": recurso,
        "precio_vista": precio_vista_i,
        "mercado_codigo": pais_i,
        "partidas_afectadas": partidas,
        "total_filas": sum(p["filas"] for p in partidas),
        "moneda_vista": _moneda,
    })


@router.get("/recursos/{recurso_id}/editar", response_class=HTMLResponse)
def editar_recurso_form(recurso_id: int, request: Request, db: Session = Depends(get_db)):
    recurso = db.get(Recurso, recurso_id)
    if recurso is None:
        return _redirect("/recursos", error="Recurso no encontrado.")
    from ..services.traduccion import codigo_desde_pais
    from ..services.precios_mercado import resolver_precio
    cfg = _config(db)
    pais = codigo_desde_pais(cfg.empresa_pais or "") or "VE"
    org_id_edit = int(db.info.get("organizacion_id") or 0)
    # Referencia nacional y precio propio se consultan por separado para poder
    # mostrar ambos: el nacional es informativo, el propio es el que el usuario
    # puede guardar. La referencia nacional no se edita desde aquí.
    nacional_edit = resolver_precio(db, recurso.id, pais, None)
    propio_edit = resolver_precio(db, recurso.id, pais, org_id_edit)
    # Todo el formulario se edita en la moneda de la organización: el precio
    # base llega convertido y el override de mercado también (cuando su
    # moneda de origen permite el puente). El POST revierte la conversión.
    moneda_vista, factor_vista = _contexto_moneda(db)
    from ..utils import normalizar_moneda
    moneda_org = normalizar_moneda(moneda_vista, "USD")
    precio_vista = tasa_convertir_precio(recurso.precio or 0, factor_vista)

    def _a_vista(resol):
        if resol is None or resol.precio is None:
            return None
        moneda_mercado = normalizar_moneda(resol.moneda or "USD", "USD")
        if moneda_mercado == moneda_org:
            return float(resol.precio)
        if moneda_mercado == "USD":
            return tasa_convertir_precio(resol.precio, factor_vista)
        return None

    precio_mercado_vista = _a_vista(propio_edit) if propio_edit.origen == "organizacion" else None
    precio_referencia_nacional_vista = _a_vista(nacional_edit)
    return TEMPLATES.TemplateResponse(request, "recursos/form.html", {
        "recurso": recurso,
        "categorias": CATEGORIAS_RECURSO,
        "etiquetas": ETIQUETAS_RECURSO,
        "mercado_codigo": pais,
        "mercado_moneda": cfg.moneda_default or "USD",
        "moneda_vista": moneda_vista,
        "precio_vista": precio_vista,
        # Solo se prellena el override propio de la organización; la
        # referencia nacional se consulta, no se edita desde aquí.
        "precio_mercado": propio_edit if propio_edit.origen == "organizacion" else None,
        "precio_mercado_vista": precio_mercado_vista,
        "precio_referencia_nacional_vista": precio_referencia_nacional_vista,
    })

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
    subtipo: str = Form(""),
    capacidad: str = Form(""),
    modalidad_tarifa: str = Form("hora"),
    incluye_operador: str = Form(""),
    incluye_combustible: str = Form(""),
    incluye_flete: str = Form(""),
    rendimiento_jornada: str = Form(""),
    db: Session = Depends(get_db),
):
    recurso = db.get(Recurso, recurso_id)
    if recurso is None:
        return _redirect("/recursos", error="Recurso no encontrado.")
    if not descripcion.strip():
        return _redirect(f"/recursos/{recurso_id}/editar", error="La descripción es obligatoria.")
    if categoria not in CATEGORIAS_RECURSO:
        categoria = "otros"
    # El formulario ya no edita el precio base del catálogo: es el precio de
    # la partida original y no representa el mercado del país. El campo oculto
    # se ignora para no destrozar la plantilla interna ni disparar una
    # propagación accidental al guardar el precio propio de la empresa.
    _moneda_u, _factor_u = _contexto_moneda(db)
    precio_anterior = float(recurso.precio or 0)
    nuevo_precio = precio_anterior
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
    recurso.subtipo = subtipo.strip(); recurso.capacidad = capacidad.strip(); recurso.modalidad_tarifa = modalidad_tarifa.strip() or "hora"
    recurso.incluye_operador = bool(incluye_operador); recurso.incluye_combustible = bool(incluye_combustible); recurso.incluye_flete = bool(incluye_flete)
    recurso.rendimiento_jornada = _f(rendimiento_jornada, None)
    recurso.fecha_actualizacion_precio = datetime.utcnow()
    from ..services.traduccion import codigo_desde_pais
    from ..services.precios_mercado import guardar_precio, eliminar_precio_organizacion
    cfg = _config(db)
    pais = codigo_desde_pais(cfg.empresa_pais or "") or "VE"
    org_id = int(db.info.get("organizacion_id") or 0)
    if str(precio_mercado or "").strip():
        guardar_precio(db, recurso.id, pais, _f(precio_mercado), cfg.moneda_default or "USD", organizacion_id=org_id, fuente="Empresa")
    else:
        # El usuario borró su precio propio: a partir de ahora manda la
        # referencia nacional de mercado.
        eliminar_precio_organizacion(db, recurso.id, pais, org_id)
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
            msg = (f"Recurso actualizado a {fmt_monto(tasa_convertir_precio(nuevo_precio, _factor_u), _moneda_u)}. "
                   f"Afectadas {res['partidas_afectadas']} partidas y {res['filas_presupuesto']} filas de presupuestos.")
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
    # El «nuevo precio» se escribe en la moneda que muestra la página (la de
    # la organización): se revierte a la base USD antes de aplicarlo.
    _moneda_b, _factor_b = _contexto_moneda(db)
    for recurso in recursos:
        anterior = float(recurso.precio or 0)
        if precio_fijo != "":
            try:
                nuevo = _a_moneda_base(max(0.0, float(str(precio_fijo).replace(",", "."))), _factor_b)
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
    """Panel de referencias nacionales y precios de la propia organización.

    ``PrecioRecursoMercado`` no es una tabla ``TenantMixin`` (la referencia
    nacional tiene ``organizacion_id`` nulo), así que el filtro automático de
    organización no la cubre: hay que acotarla explícitamente para no enseñar
    los precios negociados por otras empresas.
    """
    org_id = int(db.info.get("organizacion_id") or 0)
    query = db.query(PrecioRecursoMercado, Recurso).join(Recurso, Recurso.id == PrecioRecursoMercado.recurso_id)
    query = query.filter(or_(
        PrecioRecursoMercado.organizacion_id.is_(None),
        PrecioRecursoMercado.organizacion_id == org_id,
    ))
    if pais.strip(): query = query.filter(PrecioRecursoMercado.pais_codigo == pais.strip().upper())
    if categoria in CATEGORIAS_RECURSO: query = query.filter(Recurso.categoria == categoria)
    filas = query.order_by(PrecioRecursoMercado.pais_codigo, Recurso.categoria, Recurso.descripcion).all()
    return TEMPLATES.TemplateResponse(request, "recursos/mercado.html", {"filas": filas, "pais": pais, "categoria": categoria, "categorias": CATEGORIAS_RECURSO, "es_operador": bool(db.info.get("es_operador"))})

@router.post("/recursos/mercado")
def guardar_precio_mercado(
    recurso_id: int = Form(...), pais_codigo: str = Form(...), precio: str = Form(...), moneda: str = Form(...),
    organizacion: str = Form("0"), fuente: str = Form(""), confianza: str = Form("referencia"), db: Session = Depends(get_db)
):
    from ..services.precios_mercado import guardar_precio
    if organizacion == "1":
        org_id = int(db.info.get("organizacion_id") or 0)
        if org_id <= 0:
            return _redirect("/recursos/mercado", error="No hay una organización activa para guardar el precio.")
    else:
        # ``organizacion_id`` nulo es la referencia nacional: la comparten todas
        # las empresas del país, así que solo la edita el equipo del producto.
        if not db.info.get("es_operador"):
            return _redirect("/recursos/mercado", error="Solo el equipo de Cotizat puede editar las referencias nacionales.")
        org_id = None
    try:
        guardar_precio(
            db, recurso_id, pais_codigo, _f(precio), moneda,
            organizacion_id=org_id, fuente=fuente, confianza=confianza,
        )
        db.commit()
    except ValueError as exc:
        db.rollback()
        return _redirect("/recursos/mercado", error=str(exc))
    return _redirect("/recursos/mercado", msg="Precio de mercado guardado.")
