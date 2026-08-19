"""Catálogo de partidas."""  # E4-001 — router por dominio

from fastapi import APIRouter
from sqlalchemy import func

from .common import *  # noqa: F401,F403  (re-exporta modelos, servicios y utilidades)
from ..services import auditoria

router = APIRouter()

def _descomposicion_catalogo(form):
    """Lee y recalcula los recursos del análisis de precios del catálogo.

    La tabla es la fuente de verdad: nunca se confía en subtotales enviados
    por el navegador. Cada recurso se guarda con su rendimiento, su precio
    unitario y su importe derivado; los cuatro costes heredados se obtienen
    posteriormente de estas mismas filas.
    """
    filas = []
    claves = ("d_categoria", "d_codigo", "d_unidad", "d_descripcion", "d_rendimiento", "d_precio")
    listas = {k: form.getlist(k) for k in claves}
    total = max((len(v) for v in listas.values()), default=0)

    def val(k, i, defecto=""):
        return listas[k][i] if i < len(listas[k]) else defecto

    etiquetas = {"materiales": "Materiales", "mano_obra": "Mano de obra",
                 "complementarios": "Costes directos complementarios", "otros": "Equipos y otros"}
    for i in range(total):
        categoria = str(val("d_categoria", i, "otros") or "otros").strip()
        if categoria not in etiquetas:
            categoria = "otros"
        codigo, unidad, descripcion = (str(val(k, i) or "").strip() for k in ("d_codigo", "d_unidad", "d_descripcion"))
        if not descripcion and not codigo:
            continue
        rendimiento = max(0.0, _f(val("d_rendimiento", i), 0))
        precio = max(0.0, _f(val("d_precio", i), 0))
        filas.append({
            "tipo": "recurso", "grupo": etiquetas[categoria], "categoria": categoria,
            "codigo": codigo, "unidad": unidad or ("%" if categoria == "complementarios" else "ud"),
            "descripcion": descripcion, "rendimiento": rendimiento,
            "precio": precio, "precio_unitario": precio, "importe": 0.0,
            "numero": len(filas) + 1, "celdas": [], "formulas": {},
        })

    # Reutiliza las reglas de CYPE también para recursos manuales, incluido el
    # complemento porcentual: % × (materiales + mano de obra + otros).
    resultado = recalcular_descompuesto_cype(filas)
    for indice, fila in enumerate(filas):
        fila["importe"] = resultado["importes"].get(indice, 0.0)
        if indice in resultado["precios_complementarios"]:
            fila["precio"] = resultado["precios_complementarios"][indice]
            fila["precio_unitario"] = fila["precio"]
    return filas, resultado["costes"]


def _datos_partida_catalogo(form):
    """Datos opcionales de una partida, concentrados fuera del constructor."""
    horas_txt = str(form.get("tiempo_estimado_horas", "")).strip()
    horas_of = str(form.get("tiempo_oficial_horas", "")).strip()
    horas_ay = str(form.get("tiempo_ayudante_horas", "")).strip()
    horas_eq = str(form.get("tiempo_equipo_horas", "")).strip()
    return {
        "descripcion": str(form.get("descripcion", "")).strip(),
        "precio_unitario": max(0.0, _f(form.get("precio_unitario"))),
        "unidad": str(form.get("unidad", "ud")).strip() or "ud",
        "categoria": str(form.get("categoria", "General")).strip() or "General",
        "codigo_interno": str(form.get("codigo_interno", "")).strip(),
        "subcategoria": str(form.get("subcategoria", "")).strip(),
        "apartado": str(form.get("apartado", "")).strip(),
        "coste_materiales": max(0.0, _f(form.get("coste_materiales"))),
        "coste_mano_obra": max(0.0, _f(form.get("coste_mano_obra"))),
        "coste_complementarios": max(0.0, _f(form.get("coste_complementarios"))),
        "coste_otros": max(0.0, _f(form.get("coste_otros"))),
        "tiempo_estimado_horas": max(0.0, _f(horas_txt)) if horas_txt else None,
        "tiempo_oficial_horas": max(0.0, _f(horas_of)) if horas_of else None,
        "tiempo_ayudante_horas": max(0.0, _f(horas_ay)) if horas_ay else None,
        "tiempo_equipo_horas": max(0.0, _f(horas_eq)) if horas_eq else None,
        "proveedor": str(form.get("proveedor", "")).strip(),
        "rendimiento": str(form.get("rendimiento", "")).strip(),
        "desperdicio_recomendado_pct": max(0.0, min(100.0, _f(form.get("desperdicio_recomendado_pct")))),
        "notas_tecnicas": str(form.get("notas_tecnicas", "")).strip(),
    }


def _desvincular_clasificacion_si_cambio(partida: Partida, datos: dict) -> None:
    """Evita que una ruta editada a mano siga apuntando al nodo oficial viejo."""
    anterior = (
        partida.categoria or "",
        partida.subcategoria or "",
        partida.apartado or "",
    )
    nueva = (
        datos.get("categoria") or "",
        datos.get("subcategoria") or "",
        datos.get("apartado") or "",
    )
    if anterior != nueva:
        partida.categoria_id = None
        partida.codigo_clasificacion = ""
        partida.version_catalogo = 0

@router.get("/partidas", response_class=HTMLResponse)
def listar_partidas(
    request: Request,
    q: str = "",
    pagina: int = 1,
    vista: str = "activas",
    categoria: str = "",
    subcategoria: str = "",
    db: Session = Depends(get_db),
):
    # La tabla de gestión ya no se pagina en la vista de navegación: el árbol
    # completo se monta contraído y las filas de cada subcapítulo se cargan
    # bajo demanda (ver /partidas/api/filas). Solo la búsqueda y el filtro de
    # una subcategoría concreta renderizan filas en el servidor.
    from ..services.catalogo_propio import asegurar_catalogo_propio
    asegurar_catalogo_propio(db)
    vista = "ocultas" if vista == "ocultas" else "activas"
    categoria = str(categoria or "").strip()
    subcategoria = str(subcategoria or "").strip()
    if subcategoria and not categoria:
        categoria = ""
    q = str(q or "").strip()
    total_ocultas = db.query(Partida).filter(Partida.oculta.is_(True)).count()

    modo_directo = bool(q) or bool(subcategoria)
    por_pagina = 100
    if modo_directo:
        query = db.query(Partida).filter(Partida.oculta.is_(vista == "ocultas"))
        if categoria:
            query = query.filter(Partida.categoria == categoria)
            if subcategoria:
                query = query.filter(Partida.subcategoria == subcategoria)
        if q:
            query, _ = _aplicar_busqueda_catalogo(query, q[:120])
        total_partidas = query.count()
        total_paginas = max(1, math.ceil(total_partidas / por_pagina))
        pagina = max(1, min(int(pagina or 1), total_paginas))
        partidas = query.order_by(
            Partida.categoria,
            Partida.subcategoria,
            Partida.apartado,
            Partida.codigo_interno,
            Partida.ultimo_uso.desc(),
            Partida.nombre,
        ).offset((pagina - 1) * por_pagina).limit(por_pagina).all()
        catalogo_descompuestos = {}
        for partida in partidas:
            try:
                valor = json.loads(partida.descomposicion_json or "[]")
                catalogo_descompuestos[partida.id] = valor.get("filas", []) if isinstance(valor, dict) else valor
            except (TypeError, ValueError):
                catalogo_descompuestos[partida.id] = []
    else:
        partidas = []
        catalogo_descompuestos = {}
        total_partidas = db.query(Partida).filter(
            Partida.oculta.is_(vista == "ocultas")
        ).count()
        total_paginas = 1
        pagina = 1

    # Barra lateral: árbol oficial completo (capítulo → subcapítulo) con el
    # total de partidas por nodo, independiente de la paginación y del filtro
    # activo. La barra es la navegación del catálogo, no un resumen de la
    # página cargada: así se ven siempre los 18 capítulos, contraídos.
    nodos_oficiales = (
        db.query(CategoriaPartida)
        .filter(CategoriaPartida.oficial.is_(True), CategoriaPartida.activa.is_(True))
        .all()
    )
    capitulos = sorted(
        (n for n in nodos_oficiales if n.nivel == 1),
        key=lambda n: n.codigo_completo,
    )
    hijos_por_padre: dict[int, list[CategoriaPartida]] = {}
    for nodo in nodos_oficiales:
        if nodo.nivel == 2 and nodo.parent_id is not None:
            hijos_por_padre.setdefault(nodo.parent_id, []).append(nodo)
    ocultas_filtro = vista == "ocultas"
    conteo_capitulos = dict(
        db.query(Partida.categoria, func.count(Partida.id))
        .filter(Partida.oculta.is_(ocultas_filtro))
        .group_by(Partida.categoria)
        .all()
    )
    conteo_subcapitulos = dict(
        db.query(Partida.subcategoria, func.count(Partida.id))
        .filter(Partida.oculta.is_(ocultas_filtro))
        .group_by(Partida.subcategoria)
        .all()
    )
    arbol_categorias = []
    for capitulo in capitulos:
        subcapitulos = sorted(
            hijos_por_padre.get(capitulo.id, []),
            key=lambda n: n.codigo_completo,
        )
        arbol_categorias.append({
            "categoria": capitulo.categoria,
            "total": int(conteo_capitulos.get(capitulo.categoria, 0)),
            "subcapitulos": [
                {
                    "subcategoria": sub.subcategoria,
                    "nombre": sub.nombre,
                    "total": int(conteo_subcapitulos.get(sub.subcategoria, 0)),
                }
                for sub in subcapitulos
            ],
        })
    return TEMPLATES.TemplateResponse(request, "partidas/list.html", {
        "partidas": partidas,
        "q": q,
        "catalogo_descompuestos": catalogo_descompuestos,
        "arbol_categorias": arbol_categorias,
        "categoria_actual": categoria,
        "subcategoria_actual": subcategoria,
        "total_partidas": total_partidas,
        "pagina": pagina,
        "total_paginas": total_paginas,
        "por_pagina": por_pagina,
        "vista": vista,
        "total_ocultas": total_ocultas,
    })


@router.get("/partidas/api/filas")
def filas_subcategoria_catalogo(
    categoria: str,
    subcategoria: str,
    vista: str = "activas",
    db: Session = Depends(get_db),
):
    """Devuelve las partidas de un subcapítulo como JSON.

    La vista de navegación monta el árbol completo contraído y pide aquí las
    filas de cada subcapítulo solo cuando el usuario lo despliega, para que la
    primera carga sea instantánea aunque el catálogo tenga miles de partidas.
    El navegador construye las filas con el DOM API (sin inyectar HTML), de
    acuerdo con la política CSP estricta del proyecto.
    """
    vista = "ocultas" if vista == "ocultas" else "activas"
    filas = (
        db.query(Partida)
        .filter(
            Partida.oculta.is_(vista == "ocultas"),
            Partida.categoria == categoria,
            Partida.subcategoria == subcategoria,
        )
        .order_by(Partida.apartado, Partida.codigo_interno, Partida.nombre)
        .all()
    )
    partidas = []
    for p in filas:
        try:
            valor = json.loads(p.descomposicion_json or "[]")
            descomp = valor.get("filas", []) if isinstance(valor, dict) else valor
        except (TypeError, ValueError):
            descomp = []
        n_recursos = sum(
            1 for f in descomp
            if isinstance(f, dict) and f.get("tipo") == "recurso"
        )
        partidas.append({
            "id": p.id,
            "nombre": p.nombre or "",
            "descripcion": p.descripcion or "",
            "unidad": p.unidad or "ud",
            "precio": p.precio_unitario or 0.0,
            "categoria": p.categoria or "",
            "subcategoria": p.subcategoria or "",
            "apartado": p.apartado or "",
            "codigo": p.codigo_interno or p.codigo_externo or "",
            "proveedor": p.proveedor or "",
            "usos": p.usos or 0,
            "imagen": bool(p.imagen),
            "es_oficial": bool(p.es_oficial),
            "coste_materiales": p.coste_materiales or 0.0,
            "coste_mano_obra": p.coste_mano_obra or 0.0,
            "coste_complementarios": p.coste_complementarios or 0.0,
            "coste_otros": p.coste_otros or 0.0,
            "recursos": n_recursos,
        })
    return {"ok": True, "partidas": partidas}


@router.get("/partidas/api/buscar")
def buscar_partidas_catalogo_api(
    q: str = "",
    limite: int = 60,
    db: Session = Depends(get_db),
):
    """Búsqueda técnica bajo demanda sin descargar fichas/descompuestos."""
    consulta = str(q or "").strip()[:120]
    limite = max(1, min(int(limite or 60), 100))
    query = db.query(Partida).filter(
        Partida.oculta.is_(False)
    ).options(load_only(*_CAMPOS_INDICE_CATALOGO))
    query, grupos = _aplicar_busqueda_catalogo(query, consulta)
    candidatas = query.order_by(
        Partida.usos.desc(), Partida.ultimo_uso.desc(), Partida.nombre
    ).limit(max(100, min(500, limite * 8))).all() if grupos else []
    partidas = sorted(
        candidatas,
        key=lambda p: (-_puntuar_busqueda_catalogo(p, consulta, grupos), p.nombre),
    )[:limite]
    return {
        "ok": True,
        "q": consulta,
        "resultados": [_partida_catalogo_indice(p) for p in partidas],
    }


@router.post("/partidas/api/busqueda-sin-resultados")
async def registrar_busqueda_catalogo_sin_resultados(
    request: Request,
    db: Session = Depends(get_db),
):
    """Métrica interna para cubrir faltantes antes de que generen abandono."""
    try:
        payload = await request.json()
    except (TypeError, ValueError):
        payload = {}
    consulta = re.sub(r"\s+", " ", str(payload.get("q") or "").strip())[:120]
    if len(consulta) >= 2:
        log.warning(
            "catalogo_busqueda_sin_resultados",
            extra={
                "evento": "catalogo_busqueda_sin_resultados",
                "organizacion_id": db.info.get("organizacion_id"),
                "consulta": consulta,
            },
        )
    return {"ok": True}


@router.get("/partidas/{partida_id}/ficha")
def ficha_partida_catalogo(partida_id: int, db: Session = Depends(get_db)):
    """Ficha completa bajo demanda para preview, edición o inserción."""
    partida = db.get(Partida, partida_id)
    if partida is None:
        return JSONResponse(
            status_code=404,
            content={"ok": False, "error": "Partida no encontrada."},
        )
    return {"ok": True, "partida": _partida_catalogo_json(partida)}


@router.get("/partidas/{partida_id}/descomposicion")
def descomposicion_partida(partida_id: int, db: Session = Depends(get_db)):
    """Filas de recursos de una partida del catálogo (carga bajo demanda).

    La página de Partidas ya no emite las ~540 tablas de descomposición en el
    HTML inicial: cada una se pide aquí solo cuando el usuario la despliega,
    lo que reduce el peso y el DOM de la lista a una fracción.
    """
    partida = db.get(Partida, partida_id)
    if partida is None:
        return {"ok": False, "error": "Partida no encontrada."}
    try:
        valor = json.loads(partida.descomposicion_json or "[]")
    except (TypeError, ValueError):
        valor = []
    filas = valor.get("filas", []) if isinstance(valor, dict) else valor
    filas = [f for f in filas if isinstance(f, dict) and f.get("tipo") == "recurso"]
    return {"ok": True, "filas": filas}


@router.get("/partidas/exportar")
def exportar_partidas(
    formato: str = "csv",
    incluir_ocultas: bool = False,
    db: Session = Depends(get_db),
):
    """Exporta las partidas visibles; las ocultas son opt-in."""
    query = db.query(Partida)
    if not incluir_ocultas:
        query = query.filter(Partida.oculta.is_(False))
    partidas = query.order_by(
        Partida.categoria, Partida.subcategoria, Partida.apartado,
        Partida.codigo_interno, Partida.nombre,
    ).all()

    if formato.lower() == "excel" or formato.lower() == "xlsx":
        from ..services.excel_export import exportar_catalogo_partidas_excel
        buf = exportar_catalogo_partidas_excel(partidas)
        return Response(
            content=buf.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=partidas.xlsx"},
        )

    filas = [[
        "Código", "Código anterior", "Nombre", "Descripción", "Unidad", "Precio unitario",
        "Capítulo", "Subcapítulo", "Apartado", "Coste materiales", "Coste mano de obra", "Coste complementarios", "Otros costes", "Tiempo estimado (h)", "Proveedor",
        "Rendimiento", "Desperdicio recomendado (%)", "Notas técnicas", "Última actualización de precio", "Usos",
    ]]
    for p in partidas:
        filas.append([
            p.codigo_interno, p.codigo_legacy, p.nombre, p.descripcion, p.unidad,
            f"{p.precio_unitario:.2f}".replace(".", ","),
            p.categoria, p.subcategoria, p.apartado,
            f"{(p.coste_materiales or 0):.2f}".replace(".", ","),
            f"{(p.coste_mano_obra or 0):.2f}".replace(".", ","),
            f"{(p.coste_complementarios or 0):.2f}".replace(".", ","),
            f"{(p.coste_otros or 0):.2f}".replace(".", ","),
            "" if p.tiempo_estimado_horas is None else str(p.tiempo_estimado_horas).replace(".", ","),
            p.proveedor, p.rendimiento,
            f"{(p.desperdicio_recomendado_pct or 0):.2f}".replace(".", ","),
            p.notas_tecnicas,
            p.fecha_actualizacion_precio.isoformat() if p.fecha_actualizacion_precio else "",
            p.usos or 0,
        ])
    return _csv_response(filas, "partidas.csv")


@router.post("/partidas/categorias")
async def crear_categoria_partida(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    categoria = str(form.get("categoria") or "").strip()
    subcategoria = str(form.get("subcategoria") or "").strip()
    if not categoria:
        return _redirect("/partidas", error="Escribe el nombre de la categoría.")
    existe = db.query(CategoriaPartida).filter(
        CategoriaPartida.categoria == categoria, CategoriaPartida.subcategoria == subcategoria
    ).first()
    if not existe:
        db.add(CategoriaPartida(categoria=categoria, subcategoria=subcategoria))
        db.commit()
    etiqueta = f"«{categoria} · {subcategoria}»" if subcategoria else f"«{categoria}»"
    return _redirect("/partidas", msg=f"Creada {etiqueta}. Ya puedes arrastrar partidas a ella.")


@router.post("/partidas/ajustar")
def ajustar_precios(porcentaje: str = Form("0"), db: Session = Depends(get_db)):
    """Aplica un % de ajuste al catálogo; no toca presupuestos ya emitidos."""
    pct = _f(porcentaje)
    if pct < -100:
        return _redirect("/partidas", error="El porcentaje no puede ser menor que -100.")
    partidas = db.query(Partida).all()
    if not partidas:
        return _redirect("/partidas", error="No hay partidas en el catálogo.")
    ahora = datetime.utcnow()
    for partida in partidas:
        partida.precio_unitario = round((partida.precio_unitario or 0) * (1 + pct / 100), 2)
        partida.fecha_actualizacion_precio = ahora
    db.commit()
    auditoria.registrar_evento(
        db,
        "catalogo.precios_ajustados",
        entidad="partida",
        detalle={"porcentaje": pct, "partidas": len(partidas)},
    )
    return _redirect("/partidas", msg=f"Precios ajustados un {fmt_num(pct)} % en {len(partidas)} partidas.")


@router.post("/partidas/{partida_id}/usar")
def usar_partida(partida_id: int, db: Session = Depends(get_db)):
    """Punto de compatibilidad para clientes antiguos del constructor."""
    partida = db.get(Partida, partida_id)
    if partida:
        partida.usos = (partida.usos or 0) + 1
        partida.ultimo_uso = datetime.utcnow()
        db.commit()
    return {"ok": True}


@router.post("/partidas/{partida_id}/actualizar-precio")
async def actualizar_precio_partida_desde_presupuesto(partida_id: int, request: Request, db: Session = Depends(get_db)):
    """Actualiza solo el precio de la partida maestra.

    Se utiliza cuando, al editar una línea dentro de un presupuesto, el
    usuario elige explícitamente «cambiar partida / catálogo». Modifica la
    partida reutilizable para presupuestos futuros, pero **no** recorre ni
    cambia presupuestos ya guardados: esos documentos conservan su propio
    ``precio_unitario`` copiado en ``presupuesto_items``.
    """
    partida = db.get(Partida, partida_id)
    if partida is None:
        return {"ok": False, "error": "Partida del catálogo no encontrada."}
    try:
        payload = await request.json()
    except (TypeError, ValueError):
        payload = {}
    nuevo_precio = _f(payload.get("precio"), 0)
    if nuevo_precio < 0:
        return {"ok": False, "error": "El precio no puede ser negativo."}
    if abs((partida.precio_unitario or 0.0) - nuevo_precio) > 1e-9:
        precio_anterior = partida.precio_unitario or 0.0
        partida.precio_unitario = nuevo_precio
        partida.fecha_actualizacion_precio = datetime.utcnow()
        db.commit()
        db.refresh(partida)
        auditoria.registrar_evento(
            db,
            "catalogo.precio_partida",
            entidad="partida",
            entidad_id=partida.id,
            detalle={"de": precio_anterior, "a": nuevo_precio},
        )
    return {"ok": True, "partida": _partida_catalogo_json(partida)}


@router.post("/partidas/guardar-desde-presupuesto")
async def guardar_partida_desde_presupuesto(request: Request, db: Session = Depends(get_db)):
    """Crea o actualiza el catálogo desde la ficha completa del constructor.

    Usa los mismos lectores, validaciones, cálculo de descomposición e imagen
    que las rutas de la pestaña Partidas. Devuelve JSON para permanecer en el
    presupuesto y seguir trabajando.
    """
    form = await request.form()
    partida_id = int(_f(form.get("partida_catalogo_id"), 0))
    partida = db.get(Partida, partida_id) if partida_id else None
    nombre = str(form.get("nombre", "")).strip()
    if not nombre:
        return {"ok": False, "error": "El nombre de la partida es obligatorio."}
    # Una línea importada o antigua puede no conservar el id del catálogo;
    # su nombre único permite recuperar la misma ficha en vez de duplicarla.
    if partida is None:
        partida = db.query(Partida).filter(Partida.nombre == nombre).first()
    repetida = db.query(Partida).filter(Partida.nombre == nombre)
    if partida is not None:
        repetida = repetida.filter(Partida.id != partida.id)
    if repetida.first():
        return {"ok": False, "error": "Ya existe otra partida con ese nombre."}

    datos = _datos_partida_catalogo(form)
    filas_catalogo, costes_calculados = _descomposicion_catalogo(form)
    if filas_catalogo:
        datos.update({f"coste_{k}": v for k, v in costes_calculados.items()})
    datos["descomposicion_json"] = json.dumps({
        "origen": "manual",
        "codigo": str(form.get("codigo_externo", "")).strip(),
        "unidad": datos["unidad"],
        "filas": filas_catalogo,
    }, ensure_ascii=False)
    datos["codigo_externo"] = str(form.get("codigo_externo", "")).strip()

    if partida is None:
        partida = Partida(nombre=nombre)
        db.add(partida)
        precio_anterior = None
    else:
        precio_anterior = partida.precio_unitario or 0.0
        _desvincular_clasificacion_si_cambio(partida, datos)
    partida.nombre = nombre
    for campo, valor in datos.items():
        setattr(partida, campo, valor)
    if precio_anterior is None or precio_anterior != partida.precio_unitario:
        partida.fecha_actualizacion_precio = datetime.utcnow()

    if form.get("quitar_imagen"):
        anterior = partida.imagen
        partida.imagen = ""
        _borrar_imagen(anterior, db)
    else:
        archivo = form.get("imagen")
        if isinstance(archivo, UploadFileStarlette) and archivo.filename:
            vieja = partida.imagen
            ruta = await _guardar_imagen(archivo, f"partidas/cat_{partida.id or 'nueva'}", db)
            if ruta:
                partida.imagen = ruta
                _borrar_imagen(vieja, db)

    db.commit()
    db.refresh(partida)
    _sincronizar_recursos(db)
    return {"ok": True, "partida": _partida_catalogo_json(partida)}


@router.get("/partidas/nueva", response_class=HTMLResponse)
def nueva_partida_form(request: Request, db: Session = Depends(get_db)):
    return TEMPLATES.TemplateResponse(request, "partidas/form.html", {
        "partida": None,
        "categorias": _categorias(db),
    })


@router.post("/partidas/nueva")
async def crear_partida(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    nombre = str(form.get("nombre", "")).strip()
    if not nombre:
        return _redirect("/partidas/nueva", error="El nombre es obligatorio.")
    if db.query(Partida).filter(Partida.nombre == nombre).first():
        return _redirect("/partidas/nueva", error="Ya existe una partida con ese nombre.")
    datos = _datos_partida_catalogo(form)
    filas_catalogo, costes_calculados = _descomposicion_catalogo(form)
    if filas_catalogo:
        datos.update({f"coste_{k}": v for k, v in costes_calculados.items()})
    datos["descomposicion_json"] = json.dumps({"origen": "manual", "codigo": str(form.get("codigo_externo", "")), "unidad": datos["unidad"], "filas": filas_catalogo}, ensure_ascii=False)
    datos["codigo_externo"] = str(form.get("codigo_externo", "")).strip()
    imagen = ""
    archivo = form.get("imagen")
    if isinstance(archivo, UploadFileStarlette) and archivo.filename:
        imagen = await _guardar_imagen(archivo, "partidas/cat", db)
    partida = Partida(nombre=nombre, imagen=imagen, **datos)
    db.add(partida)
    db.commit()
    _sincronizar_recursos(db)
    return _redirect("/partidas", msg="Partida creada correctamente.")


@router.get("/partidas/{partida_id}/editar", response_class=HTMLResponse)
def editar_partida_form(partida_id: int, request: Request, db: Session = Depends(get_db)):
    partida = db.get(Partida, partida_id)
    if partida is None:
        return _redirect("/partidas", error="Partida no encontrada.")
    return TEMPLATES.TemplateResponse(request, "partidas/form.html", {
        "partida": partida,
        "categorias": _categorias(db),
    })


@router.post("/partidas/{partida_id}/editar")
async def actualizar_partida(partida_id: int, request: Request, db: Session = Depends(get_db)):
    partida = db.get(Partida, partida_id)
    if partida is None:
        return _redirect("/partidas", error="Partida no encontrada.")
    form = await request.form()
    nombre = str(form.get("nombre", "")).strip()
    if not nombre:
        return _redirect(f"/partidas/{partida_id}/editar", error="El nombre es obligatorio.")
    if db.query(Partida).filter(Partida.nombre == nombre, Partida.id != partida_id).first():
        return _redirect(f"/partidas/{partida_id}/editar", error="Ya existe otra partida con ese nombre.")
    datos = _datos_partida_catalogo(form)
    filas_catalogo, costes_calculados = _descomposicion_catalogo(form)
    if filas_catalogo:
        datos.update({f"coste_{k}": v for k, v in costes_calculados.items()})
    datos["descomposicion_json"] = json.dumps({"origen": "manual", "codigo": str(form.get("codigo_externo", "")), "unidad": datos["unidad"], "filas": filas_catalogo}, ensure_ascii=False)
    datos["codigo_externo"] = str(form.get("codigo_externo", "")).strip()
    precio_anterior = partida.precio_unitario or 0
    _desvincular_clasificacion_si_cambio(partida, datos)
    partida.nombre = nombre
    for campo, valor in datos.items():
        setattr(partida, campo, valor)
    if precio_anterior != partida.precio_unitario:
        partida.fecha_actualizacion_precio = datetime.utcnow()
    if form.get("quitar_imagen"):
        anterior = partida.imagen
        partida.imagen = ""
        _borrar_imagen(anterior, db)
    else:
        archivo = form.get("imagen")
        if isinstance(archivo, UploadFileStarlette) and archivo.filename:
            vieja = partida.imagen
            ruta = await _guardar_imagen(archivo, f"partidas/cat_{partida_id}", db)
            if ruta:
                partida.imagen = ruta
                _borrar_imagen(vieja, db)
    db.commit()
    _sincronizar_recursos(db)
    if precio_anterior != partida.precio_unitario:
        auditoria.registrar_evento(
            db,
            "catalogo.precio_partida",
            entidad="partida",
            entidad_id=partida.id,
            detalle={"de": precio_anterior, "a": partida.precio_unitario or 0},
        )
    return _redirect("/partidas", msg="Partida actualizada.")


def _desvincular_partidas_del_catalogo(db: Session, partida_ids) -> None:
    """Corta el vínculo de las líneas de presupuesto con partidas del catálogo.

    ``presupuesto_items.partida_catalogo_id`` solo recuerda de qué partida
    maestra se copió una línea; el precio ya está copiado en la propia línea.
    Borrar una partida personalizada no debe borrar presupuestos: se anula la
    referencia (FK a NULL) antes del borrado para no violar la integridad
    referencial.
    """
    if not partida_ids:
        return
    db.query(PresupuestoItem).filter(
        PresupuestoItem.partida_catalogo_id.in_(partida_ids)
    ).update(
        {PresupuestoItem.partida_catalogo_id: None},
        synchronize_session=False,
    )


def _es_partida_oficial(partida: Partida) -> bool:
    return bool(
        partida.es_oficial
        or partida.catalogo_uid
        or (
            (partida.codigo_legacy or "").startswith("CT-")
            and (partida.version_catalogo or 0) >= 2
        )
    )


@router.post("/partidas/{partida_id}/eliminar")
def eliminar_partida(partida_id: int, db: Session = Depends(get_db)):
    partida = db.get(Partida, partida_id)
    if partida is None:
        return _redirect("/partidas", error="Partida no encontrada.")
    if _es_partida_oficial(partida):
        partida.es_oficial = True
        partida.oculta = True
        db.commit()
        return _redirect(
            "/partidas",
            msg="Partida oficial ocultada para esta organización.",
        )
    referencia = partida.imagen
    _desvincular_partidas_del_catalogo(db, [partida_id])
    db.delete(partida)
    _borrar_imagen(referencia, db)
    db.commit()
    return _redirect("/partidas", msg="Partida personalizada eliminada.")


@router.post("/partidas/{partida_id}/restaurar")
def restaurar_partida(partida_id: int, db: Session = Depends(get_db)):
    partida = db.get(Partida, partida_id)
    if partida is None:
        return _redirect("/partidas?vista=ocultas", error="Partida no encontrada.")
    partida.oculta = False
    db.commit()
    return _redirect(
        "/partidas?vista=ocultas",
        msg="Partida restaurada en el catálogo activo.",
    )

@router.post("/partidas/bulk-delete")
async def bulk_delete_partidas(request: Request, db: Session = Depends(get_db)):
    # Support both regular form post and JSON
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
        return _redirect("/partidas", error="No se seleccionaron partidas.")
    partidas = [p for p in db.query(Partida).filter(Partida.id.in_(ids)).all()]
    oficiales = [p for p in partidas if _es_partida_oficial(p)]
    personalizadas = [p for p in partidas if not _es_partida_oficial(p)]
    if not oficiales and not personalizadas:
        return _redirect("/partidas", error="No se encontraron las partidas seleccionadas.")
    for partida in oficiales:
        partida.es_oficial = True
        partida.oculta = True
    ids_personalizadas = [p.id for p in personalizadas]
    _desvincular_partidas_del_catalogo(db, ids_personalizadas)
    referencias = {p.imagen for p in personalizadas if p.imagen}
    for partida in personalizadas:
        db.delete(partida)
    db.flush()
    for referencia in referencias:
        _borrar_imagen(referencia, db)
    db.commit()
    partes = []
    if oficiales:
        partes.append(f"{len(oficiales)} oficial(es) ocultada(s)")
    if personalizadas:
        partes.append(f"{len(personalizadas)} personalizada(s) eliminada(s)")
    return _redirect("/partidas", msg="; ".join(partes) + ".")


@router.post("/partidas/bulk-restore")
async def bulk_restore_partidas(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    ids = [int(x) for x in form.getlist("ids") if str(x).strip()]
    if not ids:
        return _redirect(
            "/partidas?vista=ocultas", error="No se seleccionaron partidas."
        )
    partidas = db.query(Partida).filter(
        Partida.id.in_(ids), Partida.oculta.is_(True)
    ).all()
    for partida in partidas:
        partida.oculta = False
    db.commit()
    return _redirect(
        "/partidas?vista=ocultas",
        msg=f"Se restauraron {len(partidas)} partidas.",
    )

@router.post("/partidas/bulk-export-selected")
async def bulk_export_selected_partidas(request: Request, db: Session = Depends(get_db)):
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
        return _csv_response([], "partidas_seleccionadas.csv")

    partidas = db.query(Partida).filter(Partida.id.in_(ids)).all()
    filas = [[
        "Código", "Nombre", "Descripción", "Unidad", "Precio unitario", "Categoría",
        "Coste materiales", "Coste mano de obra", "Coste complementarios", "Otros",
        "Usos"
    ]]
    for p in partidas:
        filas.append([
            p.codigo_interno or "",
            p.nombre,
            p.descripcion or "",
            p.unidad,
            f"{p.precio_unitario:.2f}".replace(".", ","),
            p.categoria or "",
            f"{(p.coste_materiales or 0):.2f}".replace(".", ","),
            f"{(p.coste_mano_obra or 0):.2f}".replace(".", ","),
            f"{(p.coste_complementarios or 0):.2f}".replace(".", ","),
            f"{(p.coste_otros or 0):.2f}".replace(".", ","),
            p.usos or 0,
        ])
    return _csv_response(filas, "partidas_seleccionadas.csv")

@router.post("/partidas/bulk-move-category")
async def bulk_move_partidas_category(request: Request, db: Session = Depends(get_db)):
    ids = []
    new_cat = ""
    try:
        form = await request.form()
        ids = [int(x) for x in form.getlist("ids") if str(x).strip()]
        new_cat = (form.get("new_category") or "").strip()
    except Exception:
        pass
    if not ids or not new_cat:
        return _redirect("/partidas", error="Selecciona partidas y una categoría destino.")
    count = 0
    for pid in ids:
        p = db.get(Partida, pid)
        if p:
            p.categoria = new_cat
            count += 1
    # Una categoría nueva no hereda una subcategoría posiblemente ajena.
    for pid in ids:
        p = db.get(Partida, pid)
        if p:
            p.subcategoria = ""
            p.apartado = ""
            p.categoria_id = None
            p.codigo_clasificacion = ""
            p.version_catalogo = 0
    db.commit()
    return _redirect("/partidas", msg=f"Se movieron {count} partidas a «{new_cat}».")


@router.post("/partidas/bulk-move-subcategory")
async def bulk_move_partidas_subcategory(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    ids = [int(x) for x in form.getlist("ids") if str(x).strip()]
    categoria = str(form.get("new_category") or "").strip()
    subcategoria = str(form.get("new_subcategory") or "").strip()
    if not ids or not categoria or not subcategoria:
        return _redirect("/partidas", error="Selecciona partidas, su categoría y una subcategoría destino.")
    partidas = db.query(Partida).filter(Partida.id.in_(ids)).all()
    # La jerarquía se protege en servidor: no se puede saltar entre categorías
    # al cambiar únicamente la subcategoría.
    if len(partidas) != len(set(ids)) or any((p.categoria or "") != categoria for p in partidas):
        return _redirect("/partidas", error="Solo puedes mover a una subcategoría partidas que ya pertenecen a esa categoría.")
    for partida in partidas:
        partida.subcategoria = subcategoria
        partida.apartado = ""
        partida.categoria_id = None
        partida.codigo_clasificacion = ""
        partida.version_catalogo = 0
    db.commit()
    return _redirect("/partidas", msg=f"Se movieron {len(partidas)} partidas a «{categoria} · {subcategoria}».")
