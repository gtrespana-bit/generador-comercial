"""Presupuestos, proyectos, propuestas, documentos de cobro e importación."""  # E4-001 — router por dominio

from fastapi import APIRouter

from . import common
from .common import *  # noqa: F401,F403  (re-exporta modelos, servicios y utilidades)
from ..services import auditoria
from ..utils import normalizar_moneda
from ..services.monedas import convertir as convertir_moneda

router = APIRouter()

# ---------------------------------------------------------------------------
# Presupuestos
# ---------------------------------------------------------------------------

@router.get("/presupuestos", response_class=HTMLResponse)
def listar_presupuestos(
    request: Request,
    estado: str = "",
    q: str = "",
    desde: str = "",
    hasta: str = "",
    pagina: int = 1,
    db: Session = Depends(get_db),
):
    query = db.query(Presupuesto)
    if _estado_valido(estado):
        query = query.filter(Presupuesto.estado == estado)
    if q.strip():
        like = f"%{q.strip()}%"
        query = query.join(Cliente).filter(or_(Cliente.nombre.ilike(like), Presupuesto.numero.ilike(like)))
    if desde:
        try:
            query = query.filter(Presupuesto.fecha >= date.fromisoformat(desde))
        except ValueError:
            pass
    if hasta:
        try:
            query = query.filter(Presupuesto.fecha <= date.fromisoformat(hasta))
        except ValueError:
            pass
    total = query.count()
    por_pagina = 25
    paginas = max(1, (total + por_pagina - 1) // por_pagina)
    pagina = max(1, min(pagina, paginas))
    presupuestos = (
        query.order_by(Presupuesto.id.desc())
        .offset((pagina - 1) * por_pagina)
        .limit(por_pagina)
        .all()
    )
    return TEMPLATES.TemplateResponse(
        request,
        "budgets/list.html",
        {
            "presupuestos": presupuestos,
            "estado": estado,
            "q": q,
            "desde": desde,
            "hasta": hasta,
            "estados": ESTADOS,
            "total": total,
            "pagina": pagina,
            "paginas": paginas,
        },
    )


@router.get("/presupuestos/exportar")
def exportar_presupuestos(
    formato: str = "csv",
    estado: str = "",
    q: str = "",
    desde: str = "",
    hasta: str = "",
    db: Session = Depends(get_db),
):
    """Exportar historial de presupuestos a CSV o Excel con formato profesional."""
    query = db.query(Presupuesto)
    if _estado_valido(estado):
        query = query.filter(Presupuesto.estado == estado)
    if q.strip():
        like = f"%{q.strip()}%"
        query = query.join(Cliente).filter(or_(Cliente.nombre.ilike(like), Presupuesto.numero.ilike(like)))
    if desde:
        try:
            query = query.filter(Presupuesto.fecha >= date.fromisoformat(desde))
        except ValueError:
            pass
    if hasta:
        try:
            query = query.filter(Presupuesto.fecha <= date.fromisoformat(hasta))
        except ValueError:
            pass

    presupuestos = query.order_by(Presupuesto.id.desc()).all()

    if formato.lower() == "excel" or formato.lower() == "xlsx":
        from ..services.excel_export import exportar_historial_excel
        buf = exportar_historial_excel(presupuestos, _config(db))
        return Response(
            content=buf.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=presupuestos.xlsx"},
        )

    # CSV por defecto
    def num(v):
        return f"{v:.2f}".replace(".", ",")

    filas = [["Número", "Fecha", "Cliente", "Título", "Estado", "Moneda", "Base", "IVA", "Descuento", "Total"]]
    for p in presupuestos:
        filas.append([
            p.numero, p.fecha.isoformat(), p.cliente.nombre, p.titulo, p.estado, p.moneda,
            num(p.base), num(p.impuesto_monto), num(p.descuento_monto), num(p.total),
        ])
    return _csv_response(filas, "presupuestos.csv")


# ---------------------------------------------------------------------------
# Importación de partidas desde CSV / Excel
# ---------------------------------------------------------------------------

_TOKEN_IMPORTACION_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)


def _guardar_importacion_cype(
    archivos: list[tuple[str, bytes]], db: Session
) -> dict:
    """Guarda fuentes y manifiesto CYPE en almacenamiento privado del tenant."""
    if not archivos:
        raise ErrorImportacion("Selecciona al menos un archivo .xlsx de CYPE.")
    token = str(uuid.uuid4())
    analizados = []
    for indice, (nombre_original, contenido) in enumerate(archivos, start=1):
        analizados.append((
            Path(nombre_original or f"partida_{indice}.xlsx").name,
            contenido,
            analizar_cype_xlsx(contenido),
        ))
    referencias = []
    partidas = []
    try:
        for indice, (nombre_limpio, contenido, analisis) in enumerate(analizados, start=1):
            guardado = save_object(
                db, contenido, "importaciones", nombre_limpio,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                exact_filename=f"{token}_{indice}.xlsx",
            )
            referencias.append(guardado.reference)
            for partida in analisis["partidas"]:
                partida["archivo_origen"] = guardado.reference
                partida["nombre_archivo_origen"] = nombre_limpio
                partidas.append(partida)
        manifiesto = {
            "formato": "cype_descompuesto",
            "partidas": partidas,
            "partidas_detectadas": len(partidas),
            "filas_detectadas": sum(len(partida["filas"]) for partida in partidas),
        }
        guardado = save_object(
            db,
            json.dumps(manifiesto, ensure_ascii=False).encode("utf-8"),
            "manifiestos-importacion", f"{token}.json", "application/json",
            exact_filename=f"{token}.json",
        )
        referencias.append(guardado.reference)
        db.commit()
        return {"importacion_id": token, **manifiesto}
    except StorageError as exc:
        for referencia in referencias:
            try:
                delete_object(db, referencia)
            except StorageError:
                pass
        db.rollback()
        raise ErrorImportacion(
            "No se pudo guardar la importación en el almacenamiento privado."
        ) from exc


def _cargar_importacion_cype(importacion_id: object, db: Session) -> dict:
    token = str(importacion_id or "").strip()
    if not _TOKEN_IMPORTACION_RE.fullmatch(token):
        raise ErrorImportacion("La importación CYPE no es válida o ha caducado. Vuelve a analizar el archivo.")
    organizacion_id = int(db.info.get("organizacion_id") or 0)
    key = f"organizaciones/{organizacion_id}/manifiestos-importacion/{token}.json"
    metadata = db.query(ArchivoAlmacenado).filter(ArchivoAlmacenado.object_key == key).first()
    try:
        if metadata is not None:
            contenido = read_reference(storage_reference(key)).decode("utf-8")
        else:
            contenido = (IMPORTS_DIR / f"{token}.json").read_text(encoding="utf-8")
        datos = json.loads(contenido)
    except (OSError, StorageError, UnicodeDecodeError, ValueError) as exc:
        raise ErrorImportacion("La importación CYPE no está disponible. Vuelve a cargar el archivo.") from exc
    if datos.get("formato") != "cype_descompuesto" or not isinstance(datos.get("partidas"), list):
        raise ErrorImportacion("El manifiesto de la importación CYPE no es válido.")
    return datos

def _datos_cype_desde_payload(payload, db: Session):
    """Valida el manifiesto CYPE guardado y resuelve el presupuesto destino."""
    datos = _cargar_importacion_cype(payload.get("importacion_id"), db)
    partidas = datos["partidas"]
    if not partidas:
        raise ErrorImportacion("No se detectaron partidas CYPE para importar.")
    if len(partidas) > MAX_FILAS:
        raise ErrorImportacion(f"La importación contiene más de {MAX_FILAS} partidas.")
    destino_id = int(_f(payload.get("presupuesto_destino_id"), 0))
    destino = db.get(Presupuesto, destino_id) if destino_id else None
    if destino_id and destino is None:
        raise ErrorImportacion("El presupuesto destino ya no existe. Actualiza la página e inténtalo otra vez.")
    capitulo = str(payload.get("capitulo_cype", "")).strip().upper() or "PARTIDAS IMPORTADAS"
    if len(capitulo) > 200:
        raise ErrorImportacion("El capítulo de destino no puede superar 200 caracteres.")

    errores, advertencias = [], []
    codigos_vistos = set()
    for partida in partidas:
        codigo = str(partida.get("codigo", "")).strip()
        nombre = str(partida.get("nombre", "")).strip()
        unidad = str(partida.get("unidad", "")).strip()
        if not codigo or not nombre or not unidad:
            errores.append({"fila": partida.get("fila_cabecera", 0), "mensaje": "Una partida CYPE debe incluir código, unidad y descripción."})
        clave = (normalizar(codigo), str(partida.get("archivo_origen", "")), str(partida.get("hoja", "")))
        if clave in codigos_vistos:
            advertencias.append({"fila": partida.get("fila_cabecera", 0), "mensaje": f"Código «{codigo}» repetido; se conservarán ambas partidas."})
        codigos_vistos.add(clave)
        if not partida.get("filas") or not partida.get("columnas"):
            errores.append({"fila": 0, "mensaje": f"La partida «{codigo or nombre}» no conserva su matriz de filas y columnas."})
        try:
            coste = float(partida.get("coste_directo_unitario", 0))
        except (TypeError, ValueError):
            coste = -1
        if coste < 0:
            errores.append({"fila": partida.get("fila_encabezados", 0), "mensaje": f"El coste directo de «{codigo or nombre}» no es válido."})

    return {
        "mapeo": {},
        "errores": errores,
        "advertencias": advertencias,
        "filas": partidas,
        "capitulo": capitulo,
    }, destino


def _datos_importacion_desde_payload(payload, db: Session):
    """Revalida siempre en servidor el JSON que vuelve del asistente web."""
    if not isinstance(payload, dict):
        raise ErrorImportacion("Los datos de importación no son válidos.")
    if payload.get("formato") == "cype_descompuesto":
        return _datos_cype_desde_payload(payload, db)
    filas = payload.get("filas", [])
    if not isinstance(filas, list) or len(filas) > MAX_FILAS:
        raise ErrorImportacion(f"La importación debe contener entre 1 y {MAX_FILAS} filas.")
    destino_id = int(_f(payload.get("presupuesto_destino_id"), 0))
    destino = db.get(Presupuesto, destino_id) if destino_id else None
    if destino_id and destino is None:
        raise ErrorImportacion("El presupuesto destino ya no existe. Actualiza la página e inténtalo otra vez.")
    existentes = [cap.nombre for cap in destino.capitulos] if destino else []
    resultado = validar_filas(
        filas, payload.get("mapeo", {}), existentes,
        primera_fila=max(1, int(_f(payload.get("primera_fila"), 2))),
    )
    return resultado, destino


def _anexar_filas_importadas(presupuesto: Presupuesto, filas: list[dict]) -> list[PresupuestoItem]:
    """Añade líneas validadas manteniendo capítulos y orden del destino.

    Devuelve los objetos creados para que el importador embebido pueda
    representarlos en el editor sin recargar ni abandonar el presupuesto.
    """
    capitulos = {normalizar(capitulo.nombre): capitulo for capitulo in presupuesto.capitulos}
    orden_capitulo = max((cap.orden or 0 for cap in presupuesto.capitulos), default=0)
    ordenes_partidas = {cap.id: max((part.orden or 0 for part in cap.partidas), default=0) for cap in presupuesto.capitulos if cap.id}
    usa_avanzado = bool(presupuesto.usar_funciones_avanzadas)
    creadas: list[PresupuestoItem] = []
    for fila in filas:
        nombre_capitulo = fila["capitulo"].strip().upper() or "CAPÍTULO GENERAL"
        clave_capitulo = normalizar(nombre_capitulo)
        capitulo = capitulos.get(clave_capitulo)
        if capitulo is None:
            orden_capitulo += 1
            capitulo = Capitulo(nombre=nombre_capitulo, orden=orden_capitulo)
            presupuesto.capitulos.append(capitulo)
            capitulos[clave_capitulo] = capitulo
        # Las relaciones nuevas aún no tienen id; contar sus partidas es el
        # orden correcto hasta que la sesión haga flush.
        clave_orden = capitulo.id if capitulo.id is not None else id(capitulo)
        if clave_orden not in ordenes_partidas:
            ordenes_partidas[clave_orden] = max((part.orden or 0 for part in capitulo.partidas), default=0)
        ordenes_partidas[clave_orden] += 1
        tipo = fila.get("tipo_partida", "included")
        if tipo != "included":
            usa_avanzado = True
        item = PresupuestoItem(
            nombre=fila["nombre"],
            descripcion=fila.get("descripcion", ""),
            unidad=fila.get("unidad", "ud") or "ud",
            cantidad=fila.get("cantidad", 1.0),
            precio_unitario=fila.get("precio", 0.0),
            moneda=presupuesto.moneda or "USD",
            orden=ordenes_partidas[clave_orden],
            tipo_partida=tipo,
            # Incluidas, provisionales y sujetas a medición forman parte del
            # total. Opcionales y alternativas quedan disponibles sin alterar
            # el importe hasta que se seleccionen en el editor.
            seleccionada=tipo in {"included", "provisional", "measurement"},
        )
        capitulo.partidas.append(item)
        creadas.append(item)
    presupuesto.usar_funciones_avanzadas = usa_avanzado
    return creadas


def _anexar_partidas_cype(
    presupuesto: Presupuesto,
    partidas: list[dict],
    nombre_capitulo: str,
    items_creados: list[PresupuestoItem] | None = None,
) -> list[dict]:
    """Convierte descompuestos CYPE en partidas sin aplanar sus filas.

    Cada libro/hoja se crea como una partida presupuestable de cantidad 1.
    «Rendimiento» queda en sus filas de recurso (no se confunde con la
    cantidad de obra), y el coste directo final alimenta los costes internos
    del presupuesto con los mismos redondeos del Excel.
    """
    capitulos = {normalizar(cap.nombre): cap for cap in presupuesto.capitulos}
    clave_capitulo = normalizar(nombre_capitulo)
    capitulo = capitulos.get(clave_capitulo)
    if capitulo is None:
        orden_capitulo = max((cap.orden or 0 for cap in presupuesto.capitulos), default=0) + 1
        capitulo = Capitulo(nombre=nombre_capitulo, orden=orden_capitulo)
        presupuesto.capitulos.append(capitulo)
    orden = max((part.orden or 0 for part in capitulo.partidas), default=0)
    catalogo = []
    for partida in partidas:
        orden += 1
        costes = partida.get("costes") if isinstance(partida.get("costes"), dict) else {}
        coste_materiales = max(0.0, _f(costes.get("materiales"), 0))
        coste_mano_obra = max(0.0, _f(costes.get("mano_obra"), 0))
        coste_complementarios = max(0.0, _f(costes.get("complementarios"), 0))
        coste_otros = max(0.0, _f(costes.get("otros"), 0))
        coste_directo = max(0.0, _f(partida.get("coste_directo_unitario"), 0))
        item = PresupuestoItem(
            codigo_externo=str(partida.get("codigo", "")).strip(),
            nombre=str(partida.get("nombre", "")).strip(),
            descripcion=str(partida.get("descripcion", "")).strip(),
            unidad=str(partida.get("unidad", "")).strip() or "ud",
            cantidad=1.0,
            # El archivo CYPE proporciona coste directo, no una tarifa de
            # venta. Se usa inicialmente como precio para que el presupuesto
            # sea consistente; se puede definir el margen comercial después.
            precio_unitario=coste_directo,
            moneda=presupuesto.moneda or "USD",
            orden=orden,
            coste_materiales=coste_materiales,
            coste_mano_obra=coste_mano_obra,
            coste_complementarios=coste_complementarios,
            coste_otros=coste_otros,
            desperdicio_pct=0.0,
            tipo_partida="included",
            seleccionada=True,
        )
        descomposicion = DescomposicionPartida(
            codigo=item.codigo_externo,
            unidad=item.unidad,
            nombre_hoja=str(partida.get("hoja", "")),
            archivo_origen=str(partida.get("archivo_origen", "")),
            nombre_archivo_origen=str(partida.get("nombre_archivo_origen", "")),
            rango_original=str(partida.get("dimension_original", "")),
            columnas_json=json.dumps(partida.get("columnas", []), ensure_ascii=False),
            rangos_combinados_json=json.dumps(partida.get("rangos_combinados", []), ensure_ascii=False),
            filas_originales_json=json.dumps(partida.get("filas", []), ensure_ascii=False),
            coste_directo_unitario=coste_directo,
            origen="cype",
        )
        for fila in partida.get("filas", []):
            if not isinstance(fila, dict):
                continue
            descomposicion.filas.append(DescomposicionFila(
                orden=max(0, int(_f(fila.get("numero"), 0))),
                numero_fila_excel=max(0, int(_f(fila.get("numero"), 0))),
                tipo=str(fila.get("tipo", "otro"))[:30],
                grupo=str(fila.get("grupo", ""))[:250],
                categoria=str(fila.get("categoria", ""))[:30],
                codigo=str(fila.get("codigo", ""))[:120],
                unidad=str(fila.get("unidad", ""))[:30],
                descripcion=str(fila.get("descripcion", "")),
                rendimiento=numero_local(fila.get("rendimiento")),
                precio_unitario=numero_local(fila.get("precio_unitario")),
                importe=numero_local(fila.get("importe")),
                moneda=str(fila.get("moneda") or getattr(presupuesto, "moneda", "USD")),
                origen_precio=str(fila.get("origen_precio") or "base")[:20],
                confianza_precio=str(fila.get("confianza_precio") or "provisional")[:20],
                fuente_precio=str(fila.get("fuente_precio") or "")[:200],
                celdas_json=json.dumps(fila.get("celdas", []), ensure_ascii=False),
                formulas_json=json.dumps(fila.get("formulas", {}), ensure_ascii=False),
            ))
        item.descomposicion_cype = descomposicion
        capitulo.partidas.append(item)
        if items_creados is not None:
            items_creados.append(item)
        catalogo.append({
            "capitulo": capitulo.nombre,
            "nombre": item.nombre,
            "descripcion": item.descripcion,
            "unidad": item.unidad,
            "cantidad": item.cantidad,
            "precio": item.precio_unitario,
            "categoria": "CYPE",
            "tipo_partida": "included",
            # La entrada de catálogo conserva código y costes para que, al
            # reutilizarla en otro presupuesto, la descomposición ya venga
            # poblada y editable.
            "codigo": item.codigo_externo,
            "coste_materiales": coste_materiales,
            "coste_mano_obra": coste_mano_obra,
            "coste_complementarios": coste_complementarios,
            "coste_otros": coste_otros,
            "desperdicio_pct": 0.0,
            "coste_directo_unitario": coste_directo,
            "filas": partida.get("filas", []),
        })
    return catalogo


def _json_importado(valor, defecto):
    """Lee metadatos JSON de una descomposición sin propagar datos corruptos."""
    if isinstance(valor, type(defecto)):
        return valor
    try:
        resultado = json.loads(valor or "")
    except (TypeError, ValueError):
        return defecto
    return resultado if isinstance(resultado, type(defecto)) else defecto


def _partida_importada_para_editor(
    fila: dict,
    formato: str,
    item: PresupuestoItem | None = None,
) -> dict:
    """Representación que entiende ``Partida.crearPartida`` en el navegador.

    Se usa tanto al importar sobre un presupuesto ya guardado (``item`` tiene
    id) como al trabajar en uno nuevo: en este último caso la partida queda en
    el editor y en el catálogo, y se guarda en el presupuesto con el botón
    habitual, conservando también los metadatos CYPE.
    """
    es_cype = formato == "cype_descompuesto"
    costes = fila.get("costes") if isinstance(fila.get("costes"), dict) else {}
    tipo = str(fila.get("tipo_partida", "included") or "included")
    if item is not None:
        tipo = item.tipo_partida or tipo

    datos = {
        "partida_id": item.id if item is not None and item.id is not None else "",
        "codigo_externo": (
            item.codigo_externo if item is not None
            else str(fila.get("codigo") or fila.get("codigo_externo") or "")
        ),
        "tiene_descomposicion_cype": bool(es_cype),
        "nombre_descomposicion_cype": str(fila.get("nombre_archivo_origen", "")),
        "nombre": item.nombre if item is not None else str(fila.get("nombre", "")),
        "descripcion": item.descripcion if item is not None else str(fila.get("descripcion", "")),
        "unidad": item.unidad if item is not None else str(fila.get("unidad", "ud") or "ud"),
        "precio": item.precio_unitario if item is not None else max(
            0.0,
            _f(fila.get("coste_directo_unitario") if es_cype else fila.get("precio"), 0),
        ),
        "cantidad": item.cantidad if item is not None else (1.0 if es_cype else _f(fila.get("cantidad"), 1.0)),
        "categoria": str(fila.get("categoria", "")).strip() or ("CYPE" if es_cype else "General"),
        "tipo_partida": tipo,
        "seleccionada": (
            bool(item.seleccionada) if item is not None
            else tipo in {"included", "provisional", "measurement"}
        ),
        "coste_materiales": (
            item.coste_materiales if item is not None else max(0.0, _f(costes.get("materiales"), 0))
        ),
        "coste_mano_obra": (
            item.coste_mano_obra if item is not None else max(0.0, _f(costes.get("mano_obra"), 0))
        ),
        "coste_complementarios": (
            item.coste_complementarios if item is not None else max(0.0, _f(costes.get("complementarios"), 0))
        ),
        "coste_otros": item.coste_otros if item is not None else max(0.0, _f(costes.get("otros"), 0)),
        "desperdicio_pct": item.desperdicio_pct if item is not None else 0.0,
        "margen_pct": item.margen_pct if item is not None else 0.0,
        "grupo_alternativa": item.grupo_alternativa if item is not None else "",
        "mediciones": [],
        "descomposicion": None,
        "descomposicion_meta": {},
    }
    if not es_cype:
        return datos

    descomp = item.descomposicion_cype if item is not None else None
    if descomp is not None:
        filas = [
            {
                "tipo": f.tipo,
                "grupo": f.grupo,
                "categoria": f.categoria or "",
                "codigo": f.codigo,
                "unidad": f.unidad,
                "descripcion": f.descripcion,
                "rendimiento": f.rendimiento if f.rendimiento is not None else "",
                "precio": f.precio_unitario if f.precio_unitario is not None else "",
                "importe": f.importe if f.importe is not None else "",
                "numero": f.numero_fila_excel,
                "celdas": _json_importado(f.celdas_json, []),
                "formulas": _json_importado(f.formulas_json, {}),
            }
            for f in descomp.filas
        ]
        datos["nombre_descomposicion_cype"] = descomp.nombre_archivo_origen or datos["nombre_descomposicion_cype"]
        datos["descomposicion_meta"] = {
            "origen": descomp.origen or "cype",
            "codigo": descomp.codigo or datos["codigo_externo"],
            "unidad": descomp.unidad or datos["unidad"],
            "hoja": descomp.nombre_hoja or "",
            "archivo_origen": descomp.archivo_origen or "",
            "nombre_archivo_origen": descomp.nombre_archivo_origen or "",
            "rango_original": descomp.rango_original or "",
            "columnas": _json_importado(descomp.columnas_json, []),
            "rangos_combinados": _json_importado(descomp.rangos_combinados_json, []),
        }
    else:
        filas = []
        for f in fila.get("filas", []):
            if not isinstance(f, dict):
                continue
            filas.append({
                "tipo": str(f.get("tipo", "otro")),
                "grupo": str(f.get("grupo", "")),
                "categoria": str(f.get("categoria", "")),
                "codigo": str(f.get("codigo", "")),
                "unidad": str(f.get("unidad", "")),
                "descripcion": str(f.get("descripcion", "")),
                "rendimiento": f.get("rendimiento", ""),
                "precio": f.get("precio_unitario", f.get("precio", "")),
                "importe": f.get("importe", ""),
                "numero": f.get("numero", 0),
                "celdas": f.get("celdas", []),
                "formulas": f.get("formulas", {}),
            })
        datos["descomposicion_meta"] = {
            "origen": "cype",
            "codigo": str(fila.get("codigo", "")),
            "unidad": str(fila.get("unidad", "")),
            "hoja": str(fila.get("hoja", "")),
            "archivo_origen": str(fila.get("archivo_origen", "")),
            "nombre_archivo_origen": str(fila.get("nombre_archivo_origen", "")),
            "rango_original": str(fila.get("dimension_original", "")),
            "columnas": fila.get("columnas", []),
            "rangos_combinados": fila.get("rangos_combinados", []),
        }
    datos["descomposicion"] = {"origen": "cype", "filas": filas}
    return datos


def _capitulos_importados_para_editor(
    resultado: dict,
    formato: str,
    items: list[PresupuestoItem] | None = None,
) -> list[dict]:
    """Agrupa la respuesta de una importación por capítulo para insertarla."""
    agrupados: dict[str, dict] = {}
    items = items or []
    for indice, fila in enumerate(resultado.get("filas", [])):
        if formato == "cype_descompuesto":
            nombre_capitulo = str(resultado.get("capitulo", "PARTIDAS IMPORTADAS"))
        else:
            nombre_capitulo = str(fila.get("capitulo", "CAPÍTULO GENERAL"))
        nombre_capitulo = nombre_capitulo.strip().upper() or "CAPÍTULO GENERAL"
        clave = normalizar(nombre_capitulo)
        if clave not in agrupados:
            agrupados[clave] = {"nombre": nombre_capitulo, "partidas": []}
        item = items[indice] if indice < len(items) else None
        agrupados[clave]["partidas"].append(_partida_importada_para_editor(fila, formato, item))
    return list(agrupados.values())


def _clonar_descomposicion_cype(origen: DescomposicionPartida | None) -> DescomposicionPartida | None:
    """Copia el registro técnico al duplicar un presupuesto, sin tocar el xlsx fuente."""
    if origen is None:
        return None
    copia = DescomposicionPartida(
        codigo=origen.codigo,
        unidad=origen.unidad,
        nombre_hoja=origen.nombre_hoja,
        archivo_origen=origen.archivo_origen,
        nombre_archivo_origen=origen.nombre_archivo_origen,
        rango_original=origen.rango_original,
        columnas_json=origen.columnas_json,
        rangos_combinados_json=origen.rangos_combinados_json,
        filas_originales_json=origen.filas_originales_json,
        coste_directo_unitario=origen.coste_directo_unitario,
        origen=getattr(origen, "origen", "cype") or "cype",
    )
    if origen.filas:
        for fila in origen.filas:
            copia.filas.append(DescomposicionFila(
                orden=fila.orden,
                numero_fila_excel=fila.numero_fila_excel,
                tipo=fila.tipo,
                grupo=fila.grupo,
                categoria=fila.categoria,
                codigo=fila.codigo,
                unidad=fila.unidad,
                descripcion=fila.descripcion,
                rendimiento=fila.rendimiento,
                precio_unitario=fila.precio_unitario,
                importe=fila.importe,
                celdas_json=fila.celdas_json,
                formulas_json=fila.formulas_json,
            ))
    else:
        # Tolerancia para instalaciones donde una versión anterior hubiera
        # conservado el JSON matriz pero no los registros de fila.
        try:
            filas_raw = json.loads(origen.filas_originales_json or "[]")
        except (TypeError, ValueError):
            filas_raw = []
        for fila in filas_raw:
            if not isinstance(fila, dict):
                continue
            numero = max(0, int(_f(fila.get("numero"), 0)))
            copia.filas.append(DescomposicionFila(
                orden=numero,
                numero_fila_excel=numero,
                tipo=str(fila.get("tipo", "otro"))[:30],
                grupo=str(fila.get("grupo", ""))[:250],
                categoria=str(fila.get("categoria", ""))[:30],
                codigo=str(fila.get("codigo", ""))[:120],
                unidad=str(fila.get("unidad", ""))[:30],
                descripcion=str(fila.get("descripcion", "")),
                rendimiento=numero_local(fila.get("rendimiento")),
                precio_unitario=numero_local(fila.get("precio_unitario")),
                importe=numero_local(fila.get("importe")),
                celdas_json=json.dumps(fila.get("celdas", []), ensure_ascii=False),
                formulas_json=json.dumps(fila.get("formulas", {}), ensure_ascii=False),
            ))
    return copia


def _importar_a_catalogo(db: Session, filas: list[dict], formato: str) -> tuple[int, int]:
    """Crea entradas de catálogo de partidas desde un resultado validado.

    Devuelve (creadas, omitidas). Las omitidas ya existen con el mismo
    nombre (el catálogo usa nombre único) y no se duplican. Las partidas
    CYPE conservan su código interno y sus costes por categoría para que,
    al usarlas en un presupuesto, la descomposición aparezca ya poblada.
    """
    creadas = omitidas = 0
    nombres_nuevos = set()
    for item in filas:
        nombre = str(item.get("nombre", "")).strip()
        if not nombre:
            continue
        if nombre in nombres_nuevos or db.query(Partida).filter(Partida.nombre == nombre).first():
            omitidas += 1
            continue
        costes = item.get("costes") if isinstance(item.get("costes"), dict) else {}
        es_cype = formato == "cype_descompuesto" or bool(costes)
        precio = max(0.0, _f(item.get("precio"), 0))
        if precio <= 0:
            precio = max(0.0, _f(item.get("coste_directo_unitario"), 0))
        categoria = str(item.get("categoria", "")).strip()
        # El validador rellena «General» como categoría por defecto; en el
        # catálogo es más útil agrupar por el capítulo del archivo.
        if not categoria or categoria == "General":
            capitulo = str(item.get("capitulo", "")).strip()
            if capitulo and capitulo.upper() != "CAPÍTULO GENERAL":
                categoria = capitulo
            else:
                categoria = "CYPE" if es_cype else "General"
        subcategoria = str(item.get("subcapitulo") or item.get("subcategoria") or "").strip()
        apartado = str(item.get("apartado") or "").strip()
        codigo = str(item.get("codigo") or item.get("codigo_externo") or "").strip()
        codigo_legacy = str(item.get("codigo_legacy") or "").strip()
        es_codigo_v2 = bool(re.fullmatch(r"\d{2}\.\d{2}\.\d{2}\.\d{3}", codigo))
        db.add(Partida(
            nombre=nombre,
            descripcion=str(item.get("descripcion", "")).strip(),
            precio_unitario=precio,
            unidad=str(item.get("unidad", "ud")).strip() or "ud",
            categoria=categoria,
            subcategoria=subcategoria[:80],
            apartado=apartado[:120],
            codigo_interno=codigo,
            codigo_externo=codigo,
            codigo_legacy=codigo_legacy[:80],
            codigo_clasificacion=codigo[:8] if es_codigo_v2 else "",
            version_catalogo=2 if es_codigo_v2 and codigo_legacy.startswith("CT-") else 0,
            descomposicion_json=json.dumps({
                "origen": "cype" if es_cype else "manual",
                "codigo": codigo,
                "codigo_legacy": codigo_legacy,
                "unidad": str(item.get("unidad") or "ud"),
                "filas": item.get("filas", []),
            }, ensure_ascii=False),
            coste_materiales=max(0.0, _f(costes.get("materiales"), 0)),
            coste_mano_obra=max(0.0, _f(costes.get("mano_obra"), 0)),
            coste_complementarios=max(0.0, _f(costes.get("complementarios"), 0)),
            coste_otros=max(0.0, _f(costes.get("otros"), 0)),
            desperdicio_recomendado_pct=0.0,
        ))
        nombres_nuevos.add(nombre)
        creadas += 1
    return creadas, omitidas


@router.get("/presupuestos/importar", response_class=HTMLResponse)
def importar_presupuesto_form(request: Request, destino: str = "", db: Session = Depends(get_db)):
    clientes = db.query(Cliente).order_by(Cliente.nombre).all()
    presupuestos = db.query(Presupuesto).order_by(Presupuesto.id.desc()).limit(100).all()
    # «destino=catalogo» abre el asistente en modo catálogo: las partidas
    # detectadas se guardan en el Catálogo de Partidas (desde el tab Partidas).
    modo_catalogo = destino.strip().lower() == "catalogo"
    return TEMPLATES.TemplateResponse(request, "budgets/import.html", {
        "clientes": clientes,
        "presupuestos": presupuestos,
        "campos_importables": ETIQUETAS_CAMPOS,
        "modo_catalogo": modo_catalogo,
    })


@router.post("/presupuestos/importar/analizar")
async def analizar_importacion_presupuesto(
    request: Request, db: Session = Depends(get_db)
):
    form = await request.form()
    archivos_subidos = [
        archivo for archivo in form.getlist("archivo")
        if isinstance(archivo, UploadFileStarlette) and archivo.filename
    ]
    texto = str(form.get("texto", ""))
    tiene_encabezados = str(form.get("tiene_encabezados", "1")) != "0"
    try:
        if archivos_subidos:
            archivos = []
            for archivo in archivos_subidos:
                contenido = await archivo.read()
                extension = Path(archivo.filename or "").suffix.lower()
                if extension not in {".csv", ".xlsx"}:
                    raise ErrorImportacion("Selecciona archivos .csv o .xlsx.")
                archivos.append((archivo.filename or "", extension, contenido))

            # Varios .xlsx CYPE equivalen a varias partidas. Todos se detectan
            # antes de guardarse: nunca se mezcla una importación parcial con
            # un archivo de otro formato.
            if all(extension == ".xlsx" and es_formato_cype_xlsx(contenido) for _, extension, contenido in archivos):
                resultado = _guardar_importacion_cype(
                    [(nombre, contenido) for nombre, _, contenido in archivos], db
                )
                return {"ok": True, **resultado}
            if len(archivos) > 1:
                raise ErrorImportacion("Solo se pueden cargar varios archivos cuando todos usan el formato CYPE de descompuesto.")

            _nombre, extension, contenido = archivos[0]
            if extension == ".csv":
                matriz = leer_csv(contenido)
            else:
                matriz = leer_xlsx(contenido)
        elif texto.strip():
            matriz = leer_texto(texto)
        else:
            raise ErrorImportacion("Carga un archivo CSV/XLSX o pega las filas desde Excel.")
        resultado = analizar_matriz(matriz, tiene_encabezados)
        return {"ok": True, "formato": "tabular", **resultado, "primera_fila": 2 if tiene_encabezados else 1}
    except ErrorImportacion as exc:
        return {"ok": False, "error": str(exc)}


@router.post("/presupuestos/importar/validar")
async def validar_importacion_presupuesto(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
        resultado, _ = _datos_importacion_desde_payload(payload, db)
        return {"ok": True, **resultado}
    except (ValueError, TypeError, ErrorImportacion) as exc:
        return {"ok": False, "error": str(exc)}


@router.post("/presupuestos/importar/confirmar")
async def confirmar_importacion_presupuesto(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
        resultado, destino = _datos_importacion_desde_payload(payload, db)
    except (ValueError, TypeError, ErrorImportacion) as exc:
        return {"ok": False, "error": str(exc)}
    if resultado["errores"]:
        return {"ok": False, "error": "Corrige los errores de validación antes de importar.", "errores": resultado["errores"]}
    if not resultado["filas"]:
        return {"ok": False, "error": "No hay filas válidas para importar."}

    modo = str(payload.get("modo", "")).strip().lower()
    formato = str(payload.get("formato", ""))

    # Modo catálogo (botón del tab Partidas): las partidas se guardan en el
    # catálogo reutilizable, sin crear ni modificar ningún presupuesto.
    if modo == "catalogo":
        creadas, omitidas = _importar_a_catalogo(db, resultado["filas"], formato)
        db.commit()
        _sincronizar_recursos(db)
        mensaje = f"Se importaron {creadas} partida(s) al catálogo."
        if omitidas:
            mensaje += f" {omitidas} ya existían y no se duplicaron."
        return {
            "ok": True,
            "url": f"/partidas?msg={quote(mensaje)}",
            "importadas": creadas,
            "advertencias": resultado["advertencias"],
        }

    # En un presupuesto todavía nuevo no existe id al que anexar. El modo
    # embebido guarda las partidas en el catálogo ahora mismo y devuelve su
    # estructura al editor; el presupuesto las persistirá con su guardado
    # normal, sin abandonar esta pantalla.
    if modo == "editor_inline" and destino is None:
        creadas_catalogo, omitidas_catalogo = _importar_a_catalogo(db, resultado["filas"], formato)
        db.flush()
        catalogo_editor = [
            _partida_catalogo_json(partida)
            for fila in resultado["filas"]
            if (partida := db.query(Partida).filter(Partida.nombre == str(fila.get("nombre", "")).strip()).first())
        ]
        capitulos_editor = _capitulos_importados_para_editor(resultado, formato)
        db.commit()
        _sincronizar_recursos(db)
        mensaje = (
            f"{len(resultado['filas'])} partida(s) añadida(s) al presupuesto. "
            "Ya están guardadas en el catálogo; guarda el presupuesto cuando termines."
        )
        return {
            "ok": True,
            "permanecer_en_editor": True,
            "presupuesto_guardado": False,
            "capitulos": capitulos_editor,
            "importadas": len(resultado["filas"]),
            "catalogo_creadas": creadas_catalogo,
            "catalogo_omitidas": omitidas_catalogo,
            "catalogo": catalogo_editor,
            "mensaje": mensaje,
            "advertencias": resultado["advertencias"],
        }

    if destino is None:
        cliente = db.get(Cliente, int(_f(payload.get("client_id"), 0)))
        if cliente is None:
            return {"ok": False, "error": "Selecciona un cliente para crear el nuevo presupuesto."}
        cfg = _config(db)
        hoy = date.today()
        destino = Presupuesto(
            numero=proximo_numero(db, hoy.year), year=hoy.year, fecha=hoy,
            titulo=str(payload.get("titulo", "")).strip(), validez_dias=cfg.validez_default,
            moneda=cfg.moneda_default, moneda_base=getattr(cfg, "moneda_base_catalogo", None) or "USD", tipo_cambio=cfg.tasa_cambio, fecha_tipo_cambio=cfg.fecha_tasa, fuente_tipo_cambio=getattr(cfg, "fuente_tipo_cambio", "") or "", impuesto_pct=cfg.iva_default, descuento_pct=0.0,
            estado="borrador", notas=cfg.notas_default, condiciones=cfg.condiciones_default,
            con_portada=cfg.con_portada_default,
            mostrar_firmas=cfg.mostrar_firmas_default,
            mostrar_resumen_capitulos=cfg.mostrar_resumen_capitulos_default,
            mostrar_garantias=cfg.mostrar_garantias_default,
            client_id=cliente.id,
        )
        db.add(destino)
        mensaje = "Presupuesto creado e importado"
    else:
        mensaje = f"Se importaron partidas en {destino.numero}"

    items_importados: list[PresupuestoItem] = []
    if formato == "cype_descompuesto":
        _anexar_partidas_cype(
            destino,
            resultado["filas"],
            resultado["capitulo"],
            items_creados=items_importados,
        )
    else:
        items_importados = _anexar_filas_importadas(destino, resultado["filas"])
    db.flush()

    # La misma operación deja cada partida disponible para presupuestos
    # futuros. Para CYPE se conserva en el catálogo su descomposición, no solo
    # el nombre y el precio.
    creadas_catalogo, omitidas_catalogo = _importar_a_catalogo(db, resultado["filas"], formato)
    db.flush()
    catalogo_editor = [
        _partida_catalogo_json(partida)
        for fila in resultado["filas"]
        if (partida := db.query(Partida).filter(Partida.nombre == str(fila.get("nombre", "")).strip()).first())
    ]
    _registrar_usos(db, resultado["filas"])
    capitulos_editor = _capitulos_importados_para_editor(resultado, formato, items_importados)
    mensaje_final = f"{mensaje}: {len(resultado['filas'])} partida(s)."
    db.commit()
    _sincronizar_recursos(db)

    if modo == "editor_inline":
        return {
            "ok": True,
            "permanecer_en_editor": True,
            "presupuesto_guardado": True,
            "presupuesto_id": destino.id,
            "capitulos": capitulos_editor,
            "importadas": len(resultado["filas"]),
            "catalogo_creadas": creadas_catalogo,
            "catalogo_omitidas": omitidas_catalogo,
            "catalogo": catalogo_editor,
            "mensaje": (
                f"{len(resultado['filas'])} partida(s) añadida(s) y guardada(s) "
                "en el presupuesto y en el catálogo."
            ),
            "advertencias": resultado["advertencias"],
        }

    redirect_url = f"/presupuestos/{destino.id}?msg={quote(mensaje_final)}"
    # Para CYPE (subidas de uno en uno habitualmente): abre directamente la
    # descomposición de la última partida creada para que se puedan ajustar
    # rendimientos, precios, etc. inmediatamente.
    if formato == "cype_descompuesto" and items_importados:
        last_item = items_importados[-1]
        if getattr(last_item, "descomposicion_cype", None):
            redirect_url = f"/presupuestos/{destino.id}/partidas/{last_item.id}/descomposicion?msg={quote(mensaje_final)}"

    return {
        "ok": True,
        "url": redirect_url,
        "importadas": len(resultado["filas"]),
        "advertencias": resultado["advertencias"],
    }


@router.get("/presupuestos/nuevo", response_class=HTMLResponse)
def _recursos_editor_mercado(db, recursos, cfg, moneda, tasa):
    from ..services.traduccion import codigo_desde_pais
    from ..services.precios_mercado import resolver_precio_para_presupuesto
    pais = codigo_desde_pais(getattr(cfg, "empresa_pais", "") or "") or "VE"
    org_id = int(db.info.get("organizacion_id") or 0)
    salida = []
    for r in recursos:
        item = {"id": r.id, "codigo": r.codigo, "descripcion": r.descripcion, "unidad": r.unidad, "categoria": r.categoria, "grupo": r.grupo, "precio": r.precio, "moneda": getattr(r, "moneda", None) or "USD", "proveedor": r.proveedor, "usos": r.usos}
        try:
            efectivo = resolver_precio_para_presupuesto(db, r.id, pais, org_id, moneda, tasa_mercado_a_usd=None, tasa_usd_presupuesto=tasa)
            if efectivo.get("precio") is not None and not efectivo.get("requiere_tasa"):
                item["precio"] = efectivo["precio"]
                item["moneda"] = efectivo["moneda"]
            item["origen_precio"] = efectivo.get("origen", "base")
            item["confianza_precio"] = efectivo.get("confianza", "")
            item["aviso_precio"] = efectivo.get("aviso", "")
        except Exception:
            item["origen_precio"] = "base"
            item["confianza_precio"] = "respaldo"
            item["aviso_precio"] = "Verifica el precio con tu proveedor"
        salida.append(item)
    return salida


def nuevo_presupuesto_form(request: Request, db: Session = Depends(get_db)):
    from ..services.catalogo_propio import asegurar_catalogo_propio
    asegurar_catalogo_propio(db)
    cfg = _config(db)
    clientes = db.query(Cliente).order_by(Cliente.nombre).all()
    partidas_catalogo = _indice_catalogo_para_editor(db, cfg.moneda_default, cfg.tasa_cambio)
    productos_catalogo = db.query(Producto).order_by(Producto.ultimo_uso.desc(), Producto.usos.desc(), Producto.nombre).all()
    recursos_base = db.query(Recurso).order_by(Recurso.ultimo_uso.desc(), Recurso.usos.desc(), Recurso.descripcion).all()
    recursos_catalogo = _recursos_editor_mercado(db, recursos_base, cfg, cfg.moneda_default, cfg.tasa_cambio)
    plantillas = db.query(Plantilla).order_by(Plantilla.nombre).all()
    return TEMPLATES.TemplateResponse(
        request,
        "budgets/form.html",
        {
            "presupuesto": None,
            "clientes": clientes,
            "cfg": cfg,
            "hoy": date.today(),
            "partidas_catalogo": partidas_catalogo,
            "productos_catalogo": productos_catalogo,
            "recursos_catalogo": recursos_catalogo,
            "categorias": _categorias(db),
            "plantillas": plantillas,
            "estados": ESTADOS,
            "campos_importables": ETIQUETAS_CAMPOS,
            "tiempos_catalogo": {},
        },
    )


def _leer_formulario_presupuesto(form, db: Session | None = None):
    """Interpreta el formulario anidado de capítulos/partidas/mediciones.

    Devuelve (datos_generales, capitulos) donde capitulos es una lista de
    dicts: {"nombre": str, "partidas": [{"nombre", "unidad", "precio",
    "cantidad", "descripcion", "prod_*", "mediciones": [(concepto, cant)],
    "descomposicion": [filas de costes editadas en el generador]}]}
    """
    # El editor modular mantiene la estructura en memoria. Al enviar el
    # formulario la serializa en un único campo JSON; esto evita desalinear
    # capítulos, partidas, mediciones o descompuestos al insertar desde Excel
    # sin recargar la página. Se conserva debajo el lector de campos paralelos
    # para compatibilidad con clientes/versiones anteriores.
    estructura_raw = form.get("estructura_json")
    if estructura_raw:
        try:
            estructura = json.loads(str(estructura_raw))
        except (TypeError, ValueError):
            estructura = None
        if isinstance(estructura, list) and len(estructura) <= MAX_FILAS:
            capitulos_json = []
            partidas_json = []
            imagenes = form.getlist("p_prod_imagen")
            indice_partida = 0
            for ci, cap in enumerate(estructura):
                if not isinstance(cap, dict):
                    continue
                nombre_capitulo = str(cap.get("nombre", "")).strip()
                capitulos_json.append({"nombre": nombre_capitulo, "partidas": []})
                partidas_cap = cap.get("partidas", [])
                if not isinstance(partidas_cap, list):
                    continue
                for pd in partidas_cap:
                    if not isinstance(pd, dict) or len(partidas_json) >= MAX_FILAS:
                        continue
                    meds = []
                    for medicion in pd.get("mediciones", []):
                        if not isinstance(medicion, dict):
                            continue
                        cantidad = _f(medicion.get("cantidad"), 0)
                        if str(medicion.get("cantidad", "")).strip():
                            meds.append((str(medicion.get("concepto", "")).strip(), cantidad))
                    descomposicion_datos = pd.get("descomposicion", [])
                    if isinstance(descomposicion_datos, dict):
                        filas_descomposicion = descomposicion_datos.get("filas", [])
                    else:
                        filas_descomposicion = descomposicion_datos
                    if not isinstance(filas_descomposicion, list):
                        filas_descomposicion = []
                    meta = pd.get("descomposicion_meta", {})
                    if not isinstance(meta, dict):
                        meta = {}
                    archivo = imagenes[indice_partida] if indice_partida < len(imagenes) else None
                    productos_opciones = []
                    for opcion in (pd.get("productos_opciones") or []):
                        if not isinstance(opcion, dict):
                            continue
                        # Cada opción es un candidato de producto. Su imagen
                        # puede llegar como archivo adjunto (UploadFile) o como
                        # ruta ya guardada en el servidor.
                        productos_opciones.append({
                            "id": int(_f(opcion.get("id"), 0)) or None,
                            "nombre": str(opcion.get("nombre", "")).strip(),
                            "precio": _f(opcion.get("precio"), 0),
                            "coste": _f(opcion.get("coste"), None) if str(opcion.get("coste", "")).strip() else None,
                            "unidad": str(opcion.get("unidad", "")).strip(),
                            "categoria": str(opcion.get("categoria", "")).strip(),
                            "marca": str(opcion.get("marca", "")).strip(),
                            "modelo": str(opcion.get("modelo", "")).strip(),
                            "sku": str(opcion.get("sku", "")).strip(),
                            "color": str(opcion.get("color", "")).strip(),
                            "acabado": str(opcion.get("acabado", "")).strip(),
                            "descripcion": str(opcion.get("descripcion", "")).strip(),
                            "imagen_actual": _normalizar_referencia_imagen(
                                db, opcion.get("imagen", "")
                            ),
                            "seleccionado": bool(opcion.get("seleccionado", False)),
                            "orden": int(_f(opcion.get("orden"), 0)),
                        })
                    partidas_json.append({
                        "cap": len(capitulos_json) - 1,
                        "id": int(_f(pd.get("partida_id"), 0)) or None,
                        "catalogo_id": int(_f(pd.get("catalogo_id"), 0)) or None,
                        "codigo_externo": str(pd.get("codigo_externo", "")).strip(),
                        "nombre": str(pd.get("nombre", "")).strip(),
                        "unidad": str(pd.get("unidad", "ud")).strip() or "ud",
                        "precio": _f(pd.get("precio")),
                        "cantidad": _f(pd.get("cantidad")),
                        "descripcion": str(pd.get("descripcion", "")).strip(),
                        "categoria": str(pd.get("categoria", "")).strip(),
                        "prod_nombre": str(pd.get("prod_nombre", "")).strip(),
                        "prod_precio": _f(pd.get("prod_precio"), None) if str(pd.get("prod_precio", "")).strip() else None,
                        "prod_coste": _f(pd.get("prod_coste"), None) if str(pd.get("prod_coste", "")).strip() else None,
                        "prod_unidad": str(pd.get("prod_unidad", "")).strip(),
                        "prod_categoria": str(pd.get("prod_categoria", "")).strip(),
                        "prod_imagen_actual": _normalizar_referencia_imagen(
                            db, pd.get("prod_imagen", "")
                        ),
                        "prod_imagen_file": archivo,
                        "tipo_partida": str(pd.get("tipo_partida", "included")).strip() or "included",
                        "seleccionada": bool(pd.get("seleccionada", False)),
                        "coste_materiales": _f(pd.get("coste_materiales")),
                        "coste_mano_obra": _f(pd.get("coste_mano_obra")),
                        "coste_complementarios": _f(pd.get("coste_complementarios")),
                        "coste_otros": _f(pd.get("coste_otros")),
                        "desperdicio_pct": _f(pd.get("desperdicio_pct")),
                        "margen_pct": _f(pd.get("margen_pct")),
                        "grupo_alternativa": str(pd.get("grupo_alternativa", "")).strip(),
                        "mediciones": meds,
                        "descomposicion": [f for f in filas_descomposicion if isinstance(f, dict)],
                        "descomposicion_meta": meta,
                        "productos_opciones": productos_opciones,
                    })
                    indice_partida += 1
            return capitulos_json, partidas_json

    caps_nombres = [c.strip() for c in form.getlist("cap_nombre")]
    part_cap = [int(_f(x, -1)) for x in form.getlist("p_cap")]
    nombres = form.getlist("p_nombre")
    ids_partidas = form.getlist("p_id")
    unidades = form.getlist("p_unidad")
    precios = form.getlist("p_precio")
    cantidades = form.getlist("p_cantidad")
    descripciones = form.getlist("p_descripcion")
    categorias = form.getlist("p_categoria")
    prod_nombres = form.getlist("p_prod_nombre")
    prod_precios = form.getlist("p_prod_precio")
    prod_costes = form.getlist("p_prod_coste")
    prod_unidades = form.getlist("p_prod_unidad")
    prod_categorias = form.getlist("p_prod_categoria")
    prod_actual = form.getlist("p_prod_imagen_actual")
    tipos = form.getlist("p_tipo_partida")
    seleccionadas = form.getlist("p_seleccionada")
    costes_materiales = form.getlist("p_coste_materiales")
    costes_mano_obra = form.getlist("p_coste_mano_obra")
    costes_complementarios = form.getlist("p_coste_complementarios")
    costes_otros = form.getlist("p_coste_otros")
    desperdicios = form.getlist("p_desperdicio_pct")
    margenes = form.getlist("p_margen_pct")
    grupos_alternativa = form.getlist("p_grupo_alternativa")
    m_partida = [int(_f(x, -1)) for x in form.getlist("m_partida")]
    m_concepto = form.getlist("m_concepto")
    m_cantidad = form.getlist("m_cantidad")
    # Filas de descomposición de costes (recursos del generador)
    d_partida = [int(_f(x, -1)) for x in form.getlist("d_partida")]
    d_tipo = form.getlist("d_tipo")
    d_grupo = form.getlist("d_grupo")
    d_categoria = form.getlist("d_categoria")
    d_codigo = form.getlist("d_codigo")
    d_unidad = form.getlist("d_unidad")
    d_descripcion = form.getlist("d_descripcion")
    d_rendimiento = form.getlist("d_rendimiento")
    d_precio = form.getlist("d_precio")
    d_numero = form.getlist("d_numero")
    d_celdas = form.getlist("d_celdas")
    d_formulas = form.getlist("d_formulas")

    def en(lista, i, defecto=""):
        return lista[i] if i < len(lista) else defecto

    # Mantiene los índices originales de capítulo y los rehúye tras filtrar
    # los que quedaron sin nombre → las partidas no se desalinean.
    mapa = {viejo: nuevo for nuevo, viejo in enumerate(i for i, n in enumerate(caps_nombres) if n)}
    capitulos = [{"nombre": caps_nombres[viejo], "partidas": []} for viejo in mapa.values()]
    catalogo_ids = form.getlist("p_catalogo_id")
    partidas = []
    # Filas de descomposición agrupadas por partida (orden del formulario)
    filas_por_partida: dict[int, list[dict]] = {}
    for j, owner in enumerate(d_partida):
        if owner < 0:
            continue
        filas_por_partida.setdefault(owner, []).append({
            "tipo": str(en(d_tipo, j, "recurso")),
            "grupo": str(en(d_grupo, j, "")),
            "categoria": str(en(d_categoria, j, "")),
            "codigo": str(en(d_codigo, j, "")),
            "unidad": str(en(d_unidad, j, "")),
            "descripcion": str(en(d_descripcion, j, "")),
            "rendimiento": en(d_rendimiento, j, ""),
            "precio": en(d_precio, j, ""),
            "numero": en(d_numero, j, ""),
            "celdas": en(d_celdas, j, "[]"),
            "formulas": en(d_formulas, j, "{}"),
        })
    for i in range(len(nombres)):
        meds = []
        for j, owner in enumerate(m_partida):
            if owner == i and str(en(m_cantidad, j)).strip():
                meds.append((str(en(m_concepto, j)).strip(), _f(en(m_cantidad, j))))
        imagenes = form.getlist("p_prod_imagen")
        cap_orig = part_cap[i] if i < len(part_cap) else -1
        partidas.append({
            "cap": mapa.get(cap_orig, -1),
            "id": int(_f(en(ids_partidas, i), 0)) or None,
            "catalogo_id": int(_f(en(catalogo_ids, i), 0)) or None,
            "nombre": str(en(nombres, i)).strip(),
            "unidad": str(en(unidades, i, "ud")).strip() or "ud",
            "precio": _f(en(precios, i)),
            "cantidad": _f(en(cantidades, i)),
            "descripcion": str(en(descripciones, i)).strip(),
            "categoria": str(en(categorias, i)).strip(),
            "prod_nombre": str(en(prod_nombres, i)).strip(),
            "prod_precio": _f(en(prod_precios, i), None) if str(en(prod_precios, i)).strip() else None,
            "prod_coste": _f(en(prod_costes, i), None) if str(en(prod_costes, i)).strip() else None,
            "prod_unidad": str(en(prod_unidades, i)).strip(),
            "prod_categoria": str(en(prod_categorias, i)).strip(),
            "prod_imagen_actual": _normalizar_referencia_imagen(
                db, en(prod_actual, i)
            ),
            "prod_imagen_file": imagenes[i] if i < len(imagenes) else None,
            "tipo_partida": str(en(tipos, i, "included")).strip() or "included",
            "seleccionada": str(en(seleccionadas, i)).strip().lower() in {"1", "true", "si", "sí"},
            "coste_materiales": _f(en(costes_materiales, i)),
            "coste_mano_obra": _f(en(costes_mano_obra, i)),
            "coste_complementarios": _f(en(costes_complementarios, i)),
            "coste_otros": _f(en(costes_otros, i)),
            "desperdicio_pct": _f(en(desperdicios, i)),
            "margen_pct": _f(en(margenes, i)),
            "grupo_alternativa": str(en(grupos_alternativa, i)).strip(),
            "mediciones": meds,
            "descomposicion": filas_por_partida.get(i, []),
            # El camino legacy (form paralelo) no soporta opciones múltiples:
            # la lista queda vacía y se mantiene el producto primario.
            "productos_opciones": [],
        })
    return capitulos, partidas


def _sincronizar_celdas_descompuesto(filas):
    """Actualiza las celdas de la matriz (JSON) con los valores recalculados.

    Las posiciones de columna se derivan de la fila de encabezados
    conservada (misma lógica que en la importación); si la descomposición
    es manual no hay encabezado y no se toca ninguna celda.
    """
    encabezado = next((fila for fila in filas if fila.tipo == "encabezado"), None)
    if encabezado is None:
        return
    try:
        posiciones = posiciones_columnas_cype(json.loads(encabezado.celdas_json or "[]"))
    except (TypeError, ValueError):
        posiciones = {}
    if not posiciones:
        return
    for fila in filas:
        if fila.tipo not in ("recurso", "subtotal", "total"):
            continue
        try:
            celdas = json.loads(fila.celdas_json or "[]")
        except (TypeError, ValueError):
            continue
        cambios = {"importe": fila.importe}
        if fila.tipo == "recurso":
            cambios = {"rendimiento": fila.rendimiento, "precio": fila.precio_unitario, "importe": fila.importe}
        for campo, valor in cambios.items():
            columna = posiciones.get(campo)
            if columna is None or columna >= len(celdas) or valor is None:
                continue
            celdas[columna] = texto_celda(valor)
        fila.celdas_json = json.dumps(celdas, ensure_ascii=False)


def _construir_descomposicion_desde_form(pd: dict, descomposicion_origen):
    """Reconstruye la descomposición de costes de una partida desde el
    constructor (que envía todas sus filas).

    Devuelve ``(DescomposicionPartida | None, costes: dict)``. La
    descomposición se reconstruye completa en cada guardado —igual que
    capítulos, partidas y mediciones— y la cascada de costes (importes,
    subtotales, % complementarios y coste directo) se recalcula con las
    mismas reglas del formato CYPE. Las filas importadas conservan su matriz
    (celdas y fórmulas) pasando intactas por el formulario.
    """
    filas_form = pd.get("descomposicion") or []
    if not filas_form:
        return None, {}
    meta = pd.get("descomposicion_meta") if isinstance(pd.get("descomposicion_meta"), dict) else {}
    es_cype = bool(
        (descomposicion_origen is not None and (
            getattr(descomposicion_origen, "archivo_origen", "")
            or getattr(descomposicion_origen, "origen", "") == "cype"
        ))
        or meta.get("origen") == "cype"
        or meta.get("archivo_origen")
    )

    def origen_o_meta(atributo, clave, defecto=""):
        valor = getattr(descomposicion_origen, atributo, "") if descomposicion_origen else ""
        return valor or meta.get(clave) or defecto

    columnas = origen_o_meta("columnas_json", "columnas", [])
    rangos = origen_o_meta("rangos_combinados_json", "rangos_combinados", [])
    if not isinstance(columnas, str):
        columnas = json.dumps(columnas if isinstance(columnas, list) else [], ensure_ascii=False)
    if not isinstance(rangos, str):
        rangos = json.dumps(rangos if isinstance(rangos, list) else [], ensure_ascii=False)

    descomposicion = DescomposicionPartida(
        codigo=origen_o_meta("codigo", "codigo", str(pd.get("codigo_externo", ""))),
        unidad=origen_o_meta("unidad", "unidad", str(pd.get("unidad", ""))),
        nombre_hoja=origen_o_meta("nombre_hoja", "hoja"),
        archivo_origen=origen_o_meta("archivo_origen", "archivo_origen"),
        nombre_archivo_origen=origen_o_meta("nombre_archivo_origen", "nombre_archivo_origen"),
        rango_original=origen_o_meta("rango_original", "rango_original"),
        columnas_json=columnas,
        rangos_combinados_json=rangos,
        filas_originales_json="[]",
        coste_directo_unitario=0.0,
        origen="cype" if es_cype else "manual",
    )
    filas = []
    for orden, fr in enumerate(filas_form, start=1):
        celdas_valor = fr.get("celdas") or []
        formulas_valor = fr.get("formulas") or {}
        celdas_raw = celdas_valor if isinstance(celdas_valor, str) else json.dumps(celdas_valor, ensure_ascii=False)
        formulas_raw = formulas_valor if isinstance(formulas_valor, str) else json.dumps(formulas_valor, ensure_ascii=False)
        try:
            json.loads(celdas_raw)
        except (TypeError, ValueError):
            celdas_raw = "[]"
        try:
            json.loads(formulas_raw)
        except (TypeError, ValueError):
            formulas_raw = "{}"
        filas.append(DescomposicionFila(
            orden=orden,
            numero_fila_excel=max(0, int(_f(fr.get("numero"), 0))),
            tipo=str(fr.get("tipo") or "recurso")[:30] or "recurso",
            grupo=str(fr.get("grupo") or "")[:250],
            categoria=str(fr.get("categoria") or "")[:30],
            codigo=str(fr.get("codigo") or "")[:120],
            unidad=str(fr.get("unidad") or "")[:30],
            descripcion=str(fr.get("descripcion") or ""),
            rendimiento=numero_local(fr.get("rendimiento")),
            precio_unitario=numero_local(fr.get("precio")),
            importe=numero_local(fr.get("importe")),
            celdas_json=celdas_raw,
            formulas_json=formulas_raw,
        ))
    resultado = recalcular_descompuesto_cype(filas)
    for indice, fila in enumerate(filas):
        if indice in resultado["importes"]:
            fila.importe = resultado["importes"][indice]
        if indice in resultado["subtotales"]:
            fila.importe = resultado["subtotales"][indice]
        if indice in resultado["precios_complementarios"]:
            fila.precio_unitario = resultado["precios_complementarios"][indice]
        if fila.tipo == "total":
            fila.importe = resultado["coste_directo"]
    _sincronizar_celdas_descompuesto(filas)
    descomposicion.filas = filas
    descomposicion.filas_originales_json = json.dumps([
        {
            "numero": fila.numero_fila_excel,
            "celdas": json.loads(fila.celdas_json or "[]"),
            "formulas": json.loads(fila.formulas_json or "{}"),
            "tipo": fila.tipo,
            "grupo": fila.grupo,
            "categoria": fila.categoria,
            "codigo": fila.codigo,
            "unidad": fila.unidad,
            "descripcion": fila.descripcion,
            "rendimiento": fila.rendimiento,
            "precio_unitario": fila.precio_unitario,
            "importe": fila.importe,
        }
        for fila in filas
    ], ensure_ascii=False)
    descomposicion.coste_directo_unitario = resultado["coste_directo"]
    return descomposicion, resultado["costes"]


def _montar_presupuesto(presupuesto, capitulos, partidas, imagenes_guardadas, imagenes_opciones=None):
    """Rellena capítulos/partidas/mediciones en el objeto Presupuesto.

    El constructor web recrea las filas al guardar. Antes de hacerlo se toman
    las descomposiciones CYPE de las partidas que siguen presentes (por id) y
    se vuelven a enlazar al nuevo objeto; así editar el presupuesto o cambiar
    el orden no pierde ninguna fila técnica de origen. Las descomposiciones
    (CYPE o manuales) se reconstruyen desde las filas que envía el formulario
    y su cascada de costes se recalcula en el servidor.
    """
    descomposiciones_existentes = {
        part.id: part.descomposicion_cype
        for capitulo in presupuesto.capitulos
        for part in capitulo.partidas
        if part.id is not None and part.descomposicion_cype is not None
    }
    # Preservar tiempos manuales aunque el formulario no los envíe (son gestionados desde /tiempos)
    tiempos_manuales_existentes = {
        part.id: (
            part.tiempo_manual_horas,
            part.tiempo_manual_oficial_horas,
            part.tiempo_manual_ayudante_horas,
            part.tiempo_manual_equipo_horas,
        )
        for capitulo in presupuesto.capitulos
        for part in capitulo.partidas
        if part.id is not None and any(v is not None for v in (part.tiempo_manual_horas, part.tiempo_manual_oficial_horas, part.tiempo_manual_ayudante_horas, part.tiempo_manual_equipo_horas))
    }
    presupuesto.capitulos.clear()
    hubs = []
    for ci, cap in enumerate(capitulos):
        c = Capitulo(nombre=cap["nombre"].strip().upper(), orden=ci + 1)
        presupuesto.capitulos.append(c)
        hubs.append(c)
    orden_p = {}
    for i, pd in enumerate(partidas):
        if pd["cap"] < 0 or pd["cap"] >= len(hubs) or not pd["nombre"]:
            continue
        cap = hubs[pd["cap"]]
        orden_p[pd["cap"]] = orden_p.get(pd["cap"], 0) + 1
        item = PresupuestoItem(
            nombre=pd["nombre"],
            partida_catalogo_id=pd.get("catalogo_id"),
            descripcion=pd["descripcion"],
            unidad=pd["unidad"],
                precio_unitario=pd["precio"],
                moneda=presupuesto.moneda or "USD",
                cantidad=pd["cantidad"],
            orden=orden_p[pd["cap"]],
            producto_nombre=pd["prod_nombre"],
            producto_precio=pd["prod_precio"],
            producto_coste=pd.get("prod_coste"),
            producto_unidad=pd["prod_unidad"],
            producto_imagen=imagenes_guardadas.get(i, pd["prod_imagen_actual"]),
            tipo_partida=pd.get("tipo_partida", "included"),
            seleccionada=bool(pd.get("seleccionada", False)),
            coste_materiales=pd.get("coste_materiales", 0.0),
            coste_mano_obra=pd.get("coste_mano_obra", 0.0),
            coste_complementarios=pd.get("coste_complementarios", 0.0),
            coste_otros=pd.get("coste_otros", 0.0),
            desperdicio_pct=pd.get("desperdicio_pct", 0.0),
            margen_pct=pd.get("margen_pct", 0.0),
            grupo_alternativa=pd.get("grupo_alternativa", ""),
        )
        # Preservar tiempo manual asignado desde /tiempos aunque el formulario del editor no lo envíe
        pid_manual = pd.get("id")
        if pid_manual in tiempos_manuales_existentes:
            m_h, m_of, m_ay, m_eq = tiempos_manuales_existentes[pid_manual]
            item.tiempo_manual_horas = m_h
            item.tiempo_manual_oficial_horas = m_of
            item.tiempo_manual_ayudante_horas = m_ay
            item.tiempo_manual_equipo_horas = m_eq
        descomposicion_origen = descomposiciones_existentes.get(pd.get("id"))
        descomposicion, costes = _construir_descomposicion_desde_form(pd, descomposicion_origen)
        if descomposicion is not None:
            # No se mueve el mismo ORM object: al borrar la partida antigua,
            # SQLAlchemy aplicaría su cascade y borraría sus filas hijas.
            # Se reconstruye la descomposición desde el formulario (con los
            # rendimientos/precios ya editados) y se recalcula su cascada.
            item.codigo_externo = descomposicion.codigo or ""
            item.descomposicion_cype = descomposicion
            item.coste_materiales = max(0.0, costes.get("materiales", 0.0))
            item.coste_mano_obra = max(0.0, costes.get("mano_obra", 0.0))
            item.coste_complementarios = max(0.0, costes.get("complementarios", 0.0))
            item.coste_otros = max(0.0, costes.get("otros", 0.0))
        elif descomposicion_origen is not None:
            # Cliente antiguo sin filas en el formulario: se conserva la
            # matriz CYPE tal cual. Las manuales sin filas significan que el
            # usuario eliminó todos sus recursos: no se restauran.
            if getattr(descomposicion_origen, "origen", "") == "cype" or descomposicion_origen.archivo_origen:
                descomposicion = _clonar_descomposicion_cype(descomposicion_origen)
                item.codigo_externo = descomposicion_origen.codigo or ""
                item.descomposicion_cype = descomposicion
        for mi, (concepto, cant) in enumerate(pd["mediciones"]):
            item.mediciones.append(Medicion(concepto=concepto, cantidad=cant, orden=mi + 1))
        # Opciones de producto (varios productos para elegir). Se crean como
        # filas aparte para que la partida pueda mostrar un menú de
        # alternativas en el PDF. Solo se persisten las opciones que tengan
        # al menos un nombre no vacío.
        opciones_creadas_en_partida = 0
        for opcion in (pd.get("productos_opciones") or []):
            if not isinstance(opcion, dict):
                continue
            if not str(opcion.get("nombre", "")).strip():
                continue
            # El índice de la opción es LOCAL a la partida (0, 1, 2...). Se
            # busca contra el diccionario global (partida_global_idx, op_idx)
            # para localizar la imagen nueva subida, si la hay.
            imagen_opcion = str(opcion.get("imagen_actual", "")).strip()
            if imagenes_opciones:
                nueva = imagenes_opciones.get((i, opciones_creadas_en_partida))
                if nueva:
                    imagen_opcion = nueva
            item.productos_opciones.append(PresupuestoItemProducto(
                nombre=str(opcion.get("nombre", "")).strip(),
                descripcion=str(opcion.get("descripcion", "")).strip(),
                precio=_f(opcion.get("precio"), 0),
                coste=_f(opcion.get("coste"), None) if str(opcion.get("coste", "")).strip() else None,
                unidad=str(opcion.get("unidad", "")).strip(),
                categoria=str(opcion.get("categoria", "")).strip(),
                marca=str(opcion.get("marca", "")).strip(),
                modelo=str(opcion.get("modelo", "")).strip(),
                sku=str(opcion.get("sku", "")).strip(),
                color=str(opcion.get("color", "")).strip(),
                acabado=str(opcion.get("acabado", "")).strip(),
                imagen=imagen_opcion,
                seleccionado=bool(opcion.get("seleccionado", False)),
                orden=int(_f(opcion.get("orden"), 0)) or 0,
            ))
            opciones_creadas_en_partida += 1
        # Sanear: si quedó más de una opción marcada, nos quedamos con la
        # primera para mantener la coherencia visual del PDF.
        vistos = 0
        for op in item.productos_opciones:
            if op.seleccionado:
                vistos += 1
                if vistos > 1:
                    op.seleccionado = False
        cap.partidas.append(item)


@router.post("/presupuestos/nuevo")
async def crear_presupuesto(request: Request, db: Session = Depends(get_db)):
    form = await request.form()

    cliente = db.get(Cliente, int(_f(form.get("client_id"))))
    if cliente is None:
        return _redirect("/presupuestos/nuevo", error="Selecciona un cliente válido.")
    capitulos, partidas = _leer_formulario_presupuesto(form, db)
    capitulos = [c for c in capitulos if c["nombre"]]
    if not capitulos:
        return _redirect("/presupuestos/nuevo", error="Agrega al menos un capítulo con nombre.")
    if not any(p["nombre"] for p in partidas):
        return _redirect("/presupuestos/nuevo", error="Agrega al menos una partida con nombre.")
    error_condiciones = _validar_condiciones_presupuesto(form, partidas)
    error_alternativas = _validar_alternativas(partidas)
    if error_condiciones or error_alternativas:
        return _redirect("/presupuestos/nuevo", error=error_condiciones or error_alternativas)

    try:
        f = date.fromisoformat(form.get("fecha", "")) if form.get("fecha") else date.today()
    except ValueError:
        f = date.today()
    estado = form.get("estado", "borrador")
    try:
        fecha_tipo_cambio = date.fromisoformat(form.get("fecha_tipo_cambio")) if form.get("fecha_tipo_cambio") else None
    except ValueError:
        fecha_tipo_cambio = None
    # Si no viene fecha pero sí usamos tasa de cfg, usa fecha_tasa de cfg
    try:
        cfg_fecha = getattr(_config(db), "fecha_tasa", None) if 'cfg' not in locals() else getattr(cfg, "fecha_tasa", None)
    except Exception:
        cfg_fecha = None
    if fecha_tipo_cambio is None and cfg_fecha:
        # Si el form no trae fecha pero el presupuesto usará tasa de cfg, hereda su fecha
        _tipo_form_vacio = not str(form.get("tipo_cambio", "")).strip()
        _fecha_form_vacia = not str(form.get("fecha_tipo_cambio", "")).strip()
        if _tipo_form_vacio and _fecha_form_vacia:
            fecha_tipo_cambio = cfg_fecha

    con_portada = bool(form.get("con_portada"))
    mostrar_firmas = bool(form.get("mostrar_firmas"))
    mostrar_resumen_capitulos = bool(form.get("mostrar_resumen_capitulos"))
    mostrar_garantias = bool(form.get("mostrar_garantias"))
    usar_funciones_avanzadas = bool(form.get("usar_funciones_avanzadas"))
    foto_proyecto = ""
    foto_file = form.get("foto_proyecto")
    if isinstance(foto_file, UploadFileStarlette) and foto_file.filename:
        foto_proyecto = await _guardar_imagen(foto_file, f"projects/p_new_{date.today().isoformat()}", db)

    cfg = _config(db)
    presupuesto = Presupuesto(
        numero=proximo_numero(db, f.year),
        year=f.year,
        fecha=f,
        titulo=str(form.get("titulo", "")).strip(),
        direccion_obra=str(form.get("direccion_obra", "")).strip(),
        codigo_postal=str(form.get("codigo_postal", "")).strip(),
        validez_dias=int(_f(form.get("validez_dias"), 30)),
        moneda=("USD" if str(cfg.empresa_pais or "").strip().lower() == "venezuela" and normalizar_moneda(form.get("moneda"), "USD") == "VES" else normalizar_moneda(form.get("moneda"), "USD")),
        tipo_cambio=(_f(form.get("tipo_cambio"), None) if str(form.get("tipo_cambio", "")).strip() else None) or (cfg.tasa_cambio if getattr(cfg, "tasa_cambio", None) and str(form.get("tipo_cambio", "")).strip() == "" and getattr(cfg, "moneda_default", "USD") not in ("USD", "PAB") else None),
        fuente_tipo_cambio=str(form.get("fuente_tipo_cambio", "") or getattr(cfg, "fuente_tipo_cambio", "") or "").strip()[:120],
        impuesto_pct=_f(form.get("impuesto_pct"), 16.0),
        descuento_pct=_f(form.get("descuento_pct"), 0.0),
        estado=estado if _estado_valido(estado) else "borrador",
        notas=str(form.get("notas", "")).strip(),
        condiciones=str(form.get("condiciones", "")).strip(),
        con_portada=con_portada,
        foto_proyecto=foto_proyecto,
        mostrar_firmas=mostrar_firmas,
        mostrar_resumen_capitulos=mostrar_resumen_capitulos,
        mostrar_garantias=mostrar_garantias,
        usar_funciones_avanzadas=usar_funciones_avanzadas,
        gastos_indirectos_pct=_f(form.get("gastos_indirectos_pct")),
        imprevistos_pct=_f(form.get("imprevistos_pct")),
        transporte_monto=_f(form.get("transporte_monto")),
        otros_cargos_monto=_f(form.get("otros_cargos_monto")),
        estilo_pdf=form.get("estilo_pdf") if form.get("estilo_pdf") in ("elegante", "tecnica", "minimalista", "corporativa", "compacta", "editorial") else "elegante",
        mostrar_ahorro=bool(form.get("mostrar_ahorro")), incluir_anexos=bool(form.get("incluir_anexos")),
        numero_control=str(form.get("numero_control", "")).strip(), fecha_tipo_cambio=fecha_tipo_cambio, retencion_pct=_f(form.get("retencion_pct")), operacion_exenta=bool(form.get("operacion_exenta")), clausula_cambiaria=str(form.get("clausula_cambiaria", "")).strip(),
        client_id=cliente.id,
    )
    # Imágenes de producto subidas
    imagenes = {}
    for i, pd in enumerate(partidas):
        archivo = pd.get("prod_imagen_file")
        if isinstance(archivo, UploadFileStarlette) and archivo.filename:
            ruta = await _guardar_imagen(archivo, f"products/tmp_{i}_{date.today().isoformat()}", db)
            if ruta:
                imagenes[i] = ruta
    # Imágenes nuevas de las opciones múltiples de producto. Cada archivo
    # viaja con un input paralelo `p_opcion_imagen_idx` con el formato
    # "<partida_idx_global>:<opcion_idx>". Esto permite reconstruir qué opción
    # concreta de qué partida recibe cada imagen subida.
    imagenes_opciones = {}
    for archivo_op, idx_str in zip(
        form.getlist("p_opcion_imagen"),
        form.getlist("p_opcion_imagen_idx"),
    ):
        if not (isinstance(archivo_op, UploadFileStarlette) and archivo_op.filename):
            continue
        ruta = await _guardar_imagen(archivo_op, f"products/opc_{date.today().isoformat()}_{len(imagenes_opciones)}", db)
        if ruta and idx_str and ":" in idx_str:
            p_idx, o_idx = idx_str.split(":", 1)
            imagenes_opciones[(int(p_idx), int(o_idx))] = ruta

    # Firma digital del cliente (si la dibujaron en el formulario)
    firma = form.get("firma_cliente")
    if isinstance(firma, str) and firma.startswith("data:image/png;base64,"):
        presupuesto.firma_cliente = _guardar_firma(firma, db)

    _montar_presupuesto(presupuesto, capitulos, partidas, imagenes, imagenes_opciones)
    db.add(presupuesto)
    _guardar_en_catalogos(db, partidas, imagenes)
    db.flush()  # hace visibles las entradas nuevas antes de registrar el uso
    _vincular_partidas_catalogo(db, presupuesto)
    _registrar_usos(db, partidas)
    _registrar_usos_productos(db, partidas)
    db.commit()
    _sincronizar_recursos(db)
    return _redirect(f"/presupuestos/{presupuesto.id}", msg=f"Presupuesto {presupuesto.numero} creado.")


# ---------------------------------------------------------------------------
# Proyectos, cambios de alcance y pagos
# ---------------------------------------------------------------------------
@router.get("/proyectos", response_class=HTMLResponse)
def listar_proyectos(request: Request, db: Session = Depends(get_db)):
    return TEMPLATES.TemplateResponse(request, "projects/list.html", {"proyectos": db.query(Proyecto).order_by(Proyecto.id.desc()).all()})

@router.post("/presupuestos/{presupuesto_id}/proyecto")
def convertir_proyecto(presupuesto_id: int, db: Session = Depends(get_db)):
    p = db.get(Presupuesto, presupuesto_id)
    if not p or p.estado not in ("aprobado", "aprobado_parcialmente"):
        return _redirect(f"/presupuestos/{presupuesto_id}", error="Solo un presupuesto aprobado puede convertirse en proyecto.")
    existente = db.query(Proyecto).filter_by(presupuesto_id=p.id).first()
    if existente: return _redirect(f"/proyectos/{existente.id}", msg="Este presupuesto ya tiene un proyecto.")
    version = db.query(PresupuestoVersion).filter_by(presupuesto_id=p.id, estado=p.estado).order_by(PresupuestoVersion.numero_version.desc()).first()
    if not version:
        version = crear_version(db, p, "Versión aprobada al convertir en proyecto"); db.flush()
    proyecto = Proyecto(
        presupuesto_id=p.id,
        presupuesto_version_id=version.id,
        nombre=p.titulo or f"Proyecto {p.numero}",
        fecha_inicio=date.today(),
        moneda_contractual=p.moneda or "USD",
        moneda_base=getattr(p, "moneda_base", None) or "USD",
        tipo_cambio=p.tipo_cambio,
        fecha_tipo_cambio=p.fecha_tipo_cambio,
        fuente_tipo_cambio=getattr(p, "fuente_tipo_cambio", "") or "",
    )
    db.add(proyecto); p.estado = "en_ejecucion"; db.commit()
    return _redirect(f"/proyectos/{proyecto.id}", msg="Proyecto creado desde el presupuesto aprobado.")

@router.get("/proyectos/{proyecto_id}", response_class=HTMLResponse)
def ver_proyecto(proyecto_id: int, request: Request, db: Session = Depends(get_db)):
    proyecto = db.get(Proyecto, proyecto_id)
    if not proyecto: return _redirect("/proyectos", error="Proyecto no encontrado.")
    return TEMPLATES.TemplateResponse(request, "projects/detail.html", {"proyecto": proyecto, "hoy": date.today()})

@router.post("/proyectos/{proyecto_id}/actualizar")
def actualizar_proyecto(proyecto_id: int, nombre: str = Form(""), estado: str = Form("en_ejecucion"), fecha_inicio: str = Form(""), fecha_estimada_fin: str = Form(""), fecha_fin: str = Form(""), notas: str = Form(""), db: Session = Depends(get_db)):
    p = db.get(Proyecto, proyecto_id)
    if not p: return _redirect("/proyectos", error="Proyecto no encontrado.")
    def d(v):
        try: return date.fromisoformat(v) if v else None
        except ValueError: return None
    p.nombre, p.estado, p.fecha_inicio, p.fecha_estimada_fin, p.fecha_fin, p.notas = nombre.strip() or p.nombre, estado, d(fecha_inicio), d(fecha_estimada_fin), d(fecha_fin), notas.strip()
    db.commit(); return _redirect(f"/proyectos/{p.id}", msg="Proyecto actualizado.")

@router.post("/proyectos/{proyecto_id}/cambios")
def crear_cambio(proyecto_id: int, descripcion: str = Form(""), db: Session = Depends(get_db)):
    p = db.get(Proyecto, proyecto_id)
    if not p or not descripcion.strip(): return _redirect(f"/proyectos/{proyecto_id}", error="Describe el cambio de alcance.")
    numero = max((c.numero for c in p.cambios), default=0) + 1
    cambio = CambioAlcance(
        proyecto_id=p.id,
        numero=numero,
        descripcion=descripcion.strip(),
        moneda=p.moneda or "USD",
    )
    db.add(cambio); db.commit(); return _redirect(f"/proyectos/{p.id}/cambios/{cambio.id}", msg=f"Cambio Nº {numero:03d} creado.")

@router.get("/proyectos/{proyecto_id}/cambios/{cambio_id}", response_class=HTMLResponse)
def editar_cambio(proyecto_id: int, cambio_id: int, request: Request, db: Session = Depends(get_db)):
    c = db.get(CambioAlcance, cambio_id)
    if not c or c.proyecto_id != proyecto_id: return _redirect(f"/proyectos/{proyecto_id}", error="Cambio no encontrado.")
    return TEMPLATES.TemplateResponse(request, "projects/change.html", {"cambio": c, "proyecto": c.proyecto})

@router.post("/proyectos/{proyecto_id}/cambios/{cambio_id}")
async def guardar_cambio(proyecto_id: int, cambio_id: int, request: Request, db: Session = Depends(get_db)):
    c = db.get(CambioAlcance, cambio_id)
    if not c or c.proyecto_id != proyecto_id: return _redirect(f"/proyectos/{proyecto_id}", error="Cambio no encontrado.")
    f = await request.form(); c.descripcion=str(f.get("descripcion", "")).strip(); c.notas=str(f.get("notas", "")).strip(); c.estado=str(f.get("estado", "borrador"))
    c.items.clear()
    total=0.0
    for tipo,nombre,cantidad,precio in zip(f.getlist("tipo"), f.getlist("nombre"), f.getlist("cantidad"), f.getlist("precio")):
        if not str(nombre).strip(): continue
        q, pu = _f(cantidad), _f(precio); item=CambioAlcanceItem(tipo=tipo if tipo in ("agregado","eliminado") else "agregado", nombre=str(nombre).strip(), cantidad=q, precio_unitario=pu); c.items.append(item); total += item.importe * (-1 if item.tipo == "eliminado" else 1)
    c.diferencia_total=round(total,2); db.commit(); return _redirect(f"/proyectos/{proyecto_id}", msg="Cambio de alcance guardado.")

@router.post("/proyectos/{proyecto_id}/pagos")
def registrar_pago(proyecto_id: int, importe: float = Form(0), fecha: str = Form(""), metodo: str = Form("transferencia"), referencia: str = Form(""), estado: str = Form("confirmado"), notas: str = Form(""), db: Session = Depends(get_db)):
    p=db.get(Proyecto, proyecto_id)
    if not p or importe <= 0: return _redirect(f"/proyectos/{proyecto_id}", error="Indica un importe de pago válido.")
    try: fecha_pago=date.fromisoformat(fecha) if fecha else date.today()
    except ValueError: fecha_pago=date.today()
    db.add(Pago(proyecto_id=p.id, presupuesto_id=p.presupuesto_id, fecha=fecha_pago, importe=importe, moneda=p.presupuesto.moneda, metodo=metodo, referencia=referencia.strip(), estado=estado if estado in ("pendiente","confirmado","anulado") else "confirmado", notas=notas.strip()))
    db.commit(); return _redirect(f"/proyectos/{p.id}", msg="Pago registrado.")


def _datos_envio_presupuesto(presupuesto: Presupuesto, cfg: Configuracion) -> dict[str, str]:
    """Valores iniciales del formulario de entrega por correo."""
    cliente_nombre = (presupuesto.cliente.nombre or "").strip()
    empresa_nombre = (cfg.empresa_nombre or "").strip() or PRODUCT_NAME
    titulo = (presupuesto.titulo or "").strip()
    asunto = f"Presupuesto {presupuesto.numero}"
    if titulo:
        asunto += f" · {titulo}"
    saludo = f"Hola {cliente_nombre}," if cliente_nombre else "Hola,"
    mensaje = (
        f"{saludo}\n\n"
        f"Te enviamos adjunto el presupuesto {presupuesto.numero}"
        f"{f' para {titulo}' if titulo else ''}.\n\n"
        "Quedamos atentos a cualquier duda o comentario.\n\n"
        f"Saludos,\n{empresa_nombre}"
    )
    return {
        "destinatario": (presupuesto.cliente.email or "").strip().lower(),
        "asunto": asunto[:200],
        "mensaje": mensaje[:5000],
    }


def _estado_despues_de_enviar(estado: str) -> str:
    if estado in {"borrador", "en_revision"}:
        return "enviado"
    if estado in {"enviado", "cambios_solicitados", "reenviado", "vencido"}:
        return "reenviado"
    return estado


def _pagina_envio_presupuesto(
    request: Request,
    presupuesto: Presupuesto,
    cfg: Configuracion,
    datos: dict[str, str] | None = None,
    error: str = "",
    status_code: int = 200,
):
    return TEMPLATES.TemplateResponse(
        request,
        "budgets/send_email.html",
        {
            "p": presupuesto,
            "cfg": cfg,
            "datos": datos or _datos_envio_presupuesto(presupuesto, cfg),
            "error_envio": error,
        },
        status_code=status_code,
    )


@router.get("/presupuestos/{presupuesto_id}/enviar-email", response_class=HTMLResponse)
def formulario_envio_presupuesto(
    presupuesto_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    presupuesto = db.get(Presupuesto, presupuesto_id)
    if presupuesto is None:
        return _redirect("/presupuestos", error="Presupuesto no encontrado.")
    return _pagina_envio_presupuesto(request, presupuesto, _config(db))


@router.post("/presupuestos/{presupuesto_id}/enviar-email", response_class=HTMLResponse)
def enviar_presupuesto_email_web(
    presupuesto_id: int,
    request: Request,
    destinatario: str = Form(""),
    asunto: str = Form(""),
    mensaje: str = Form(""),
    db: Session = Depends(get_db),
):
    """Genera, congela y entrega el PDF; un fallo no cambia el presupuesto."""
    presupuesto = db.get(Presupuesto, presupuesto_id)
    if presupuesto is None:
        return _redirect("/presupuestos", error="Presupuesto no encontrado.")
    cfg = _config(db)
    datos = {
        "destinatario": str(destinatario or "").strip().lower(),
        "asunto": str(asunto or "").strip(),
        "mensaje": str(mensaje or "").strip(),
    }
    if es_lectura(db):
        return _pagina_envio_presupuesto(
            request, presupuesto, cfg, datos,
            "Tu rol es de solo lectura y no permite enviar documentos.", 403,
        )
    if presupuesto.estado in {"cancelado", "archivado"}:
        return _pagina_envio_presupuesto(
            request, presupuesto, cfg, datos,
            "Un presupuesto cancelado o archivado no se puede enviar.", 400,
        )
    if not email_destino_valido(datos["destinatario"]):
        return _pagina_envio_presupuesto(
            request, presupuesto, cfg, datos,
            "Escribe un email de destino válido.", 400,
        )
    if not datos["asunto"] or len(datos["asunto"]) > 200 or "\n" in datos["asunto"] or "\r" in datos["asunto"]:
        return _pagina_envio_presupuesto(
            request, presupuesto, cfg, datos,
            "El asunto es obligatorio y admite hasta 200 caracteres.", 400,
        )
    if not datos["mensaje"] or len(datos["mensaje"]) > 5000:
        return _pagina_envio_presupuesto(
            request, presupuesto, cfg, datos,
            "El mensaje es obligatorio y admite hasta 5.000 caracteres.", 400,
        )

    estado_anterior = presupuesto.estado
    presupuesto.estado = _estado_despues_de_enviar(estado_anterior)
    resultado = _generar_pdf_seguro(
        lambda: common.pdf_service.generar_pdf(presupuesto, cfg),
        f"el PDF para enviar del presupuesto {presupuesto.numero}",
    )
    if isinstance(resultado, Response):
        db.rollback()
        return _pagina_envio_presupuesto(
            request, presupuesto, cfg, datos,
            "No se pudo generar el PDF. Revisa el presupuesto e inténtalo de nuevo.", 500,
        )
    pdf_bytes = resultado.getvalue()
    nombre_pdf = f"presupuesto_{presupuesto.numero}.pdf"
    try:
        proveedor_id = common.enviar_presupuesto_por_email(
            email=datos["destinatario"],
            asunto=datos["asunto"],
            mensaje=datos["mensaje"],
            empresa_nombre=cfg.empresa_nombre,
            cliente_nombre=presupuesto.cliente.nombre,
            presupuesto_numero=presupuesto.numero,
            presupuesto_titulo=presupuesto.titulo,
            total_texto=fmt_monto_iso(presupuesto.total, presupuesto.moneda),
            pdf=pdf_bytes,
            nombre_pdf=nombre_pdf,
            responder_a=cfg.empresa_email,
        )
    except (EmailNotConfigured, EmailValidationError, EmailSendError) as exc:
        db.rollback()
        return _pagina_envio_presupuesto(
            request, presupuesto, cfg, datos, str(exc), 502,
        )

    version = crear_version(
        db,
        presupuesto,
        f"Presupuesto enviado por email a {datos['destinatario']}",
    )
    db.flush()
    try:
        version.pdf_snapshot = save_object(
            db,
            pdf_bytes,
            "presupuestos",
            nombre_pdf,
            "application/pdf",
            prefix=f"presupuesto-{presupuesto.id}-v{version.numero_version}",
            metadata={
                "presupuesto_id": presupuesto.id,
                "version_id": version.id,
                "numero_version": version.numero_version,
                "destinatario": datos["destinatario"],
                "resend_id": proveedor_id,
            },
        ).reference
    except StorageError as exc:
        # El correo ya salió: no se le dice al usuario que reintente y termine
        # enviando un duplicado. La versión JSON y la constancia se conservan.
        log.error(
            "Presupuesto %s enviado, pero no se guardó el PDF congelado: %s",
            presupuesto.numero,
            exc,
        )
    db.add(NotaSeguimiento(
        presupuesto_id=presupuesto.id,
        texto=(
            f"Presupuesto enviado por email a {datos['destinatario']} · "
            f"V{version.numero_version} · proveedor {proveedor_id}."
        ),
    ))
    db.commit()
    auditoria.registrar_evento(
        db,
        "presupuesto.enviado",
        entidad="presupuesto",
        entidad_id=presupuesto.id,
        detalle={
            "destinatario": datos["destinatario"],
            "version": version.numero_version,
        },
    )
    return _redirect(
        f"/presupuestos/{presupuesto_id}#versiones",
        msg=(
            f"Presupuesto enviado a {datos['destinatario']} y congelado como "
            f"versión {version.numero_version}."
        ),
    )


def _url_publica_propuesta(request: Request, token: str) -> str:
    ruta = f"/propuestas/{token}"
    if common.DATABASE_IS_SQLITE:
        return str(request.base_url).rstrip("/") + ruta
    return public_app_url(ruta)


def _url_interna_presupuesto(request: Request, presupuesto_id: int) -> str:
    ruta = f"/presupuestos/{presupuesto_id}#versiones"
    if common.DATABASE_IS_SQLITE:
        return str(request.base_url).rstrip("/") + ruta
    return public_app_url(ruta)


def _notificar_respuesta_propuesta(
    request: Request,
    db: Session,
    enlace: EnlacePropuesta,
) -> tuple[list[str], str]:
    """Envía a propietarios/administradores; la respuesta ya está confirmada."""
    try:
        destinatarios = destinatarios_respuesta_propuesta(db, enlace=enlace)
    except GestionEnlacePropuestaError as exc:
        destinatarios = []
        error = str(exc)
    else:
        error = "" if destinatarios else "La organización no tiene destinatarios administrativos activos."

    ya_enviados = {
        email.strip().lower()
        for email in str(enlace.notificacion_destinatarios or "").split(",")
        if email.strip()
    }
    enviados = sorted(ya_enviados)
    fallos = []
    if not error:
        for destinatario in destinatarios:
            if destinatario in ya_enviados:
                continue
            try:
                common.enviar_respuesta_propuesta_por_email(
                    email=destinatario,
                    decision=enlace.respuesta,
                    empresa_nombre=enlace.empresa_nombre,
                    cliente_nombre=enlace.cliente_nombre,
                    presupuesto_numero=enlace.presupuesto_numero,
                    presupuesto_titulo=enlace.presupuesto_titulo,
                    version_numero=enlace.presupuesto_version_numero,
                    respondido_por_nombre=enlace.respondido_por_nombre,
                    respondido_por_email=enlace.respondido_por_email,
                    comentario=enlace.respuesta_comentario,
                    enlace_interno=_url_interna_presupuesto(
                        request, enlace.presupuesto_id
                    ),
                )
                enviados.append(destinatario)
            except (EmailNotConfigured, EmailValidationError, EmailSendError) as exc:
                fallos.append(f"{destinatario}: {exc}")
        if fallos:
            error = "; ".join(fallos)[:1000]
    try:
        marcar_notificacion_respuesta(
            db,
            enlace=enlace,
            destinatarios=enviados,
            error=error,
        )
        db.commit()
    except GestionEnlacePropuestaError:
        db.rollback()
        log.error(
            "Respuesta de propuesta %s registrada, pero no se pudo guardar "
            "la constancia de notificación.",
            enlace.presupuesto_numero,
        )
    return enviados, error


def _pagina_enlaces_propuesta(
    request: Request,
    presupuesto: Presupuesto,
    db: Session,
    *,
    enlace_creado: str = "",
    error: str = "",
    status_code: int = 200,
):
    enlaces = (
        db.query(EnlacePropuesta)
        .filter(EnlacePropuesta.presupuesto_id == presupuesto.id)
        .order_by(EnlacePropuesta.created_at.desc())
        .all()
    )
    return TEMPLATES.TemplateResponse(
        request,
        "budgets/public_link.html",
        {
            "p": presupuesto,
            "enlaces": enlaces,
            "duraciones": DURACIONES_ENLACE,
            "enlace_creado": enlace_creado,
            "error_enlace": error or request.query_params.get("error", ""),
            "mensaje_enlace": request.query_params.get("msg", ""),
            "ahora": datetime.utcnow(),
        },
        status_code=status_code,
    )


@router.get("/presupuestos/{presupuesto_id}/enlace-publico", response_class=HTMLResponse)
def gestionar_enlace_publico(
    presupuesto_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    presupuesto = db.get(Presupuesto, presupuesto_id)
    if presupuesto is None:
        return _redirect("/presupuestos", error="Presupuesto no encontrado.")
    return _pagina_enlaces_propuesta(request, presupuesto, db)


@router.post("/presupuestos/{presupuesto_id}/enlace-publico", response_class=HTMLResponse)
def crear_enlace_publico_web(
    presupuesto_id: int,
    request: Request,
    duracion_dias: int = Form(30),
    db: Session = Depends(get_db),
):
    """Congela el PDF y crea un secreto revocable; nunca publica el bucket."""
    presupuesto = db.get(Presupuesto, presupuesto_id)
    if presupuesto is None:
        return _redirect("/presupuestos", error="Presupuesto no encontrado.")
    if es_lectura(db):
        return _pagina_enlaces_propuesta(
            request, presupuesto, db,
            error="Tu rol es de solo lectura y no permite crear enlaces.",
            status_code=403,
        )
    if duracion_dias not in DURACIONES_ENLACE:
        return _pagina_enlaces_propuesta(
            request, presupuesto, db,
            error="La duración del enlace no es válida.",
            status_code=400,
        )
    if presupuesto.estado in {"cancelado", "archivado"}:
        return _pagina_enlaces_propuesta(
            request, presupuesto, db,
            error="Un presupuesto cancelado o archivado no puede publicarse.",
            status_code=400,
        )

    cfg = _config(db)
    presupuesto.estado = _estado_despues_de_enviar(presupuesto.estado)
    resultado = _generar_pdf_seguro(
        lambda: common.pdf_service.generar_pdf(presupuesto, cfg),
        f"el PDF público del presupuesto {presupuesto.numero}",
    )
    if isinstance(resultado, Response):
        db.rollback()
        return _pagina_enlaces_propuesta(
            request, presupuesto, db,
            error="No se pudo generar el PDF de la propuesta.",
            status_code=500,
        )
    pdf_bytes = resultado.getvalue()
    version = crear_version(db, presupuesto, "Versión publicada mediante enlace seguro")
    db.flush()
    try:
        version.pdf_snapshot = save_object(
            db,
            pdf_bytes,
            "presupuestos",
            f"presupuesto_{presupuesto.numero}.pdf",
            "application/pdf",
            prefix=f"presupuesto-{presupuesto.id}-v{version.numero_version}",
            metadata={
                "presupuesto_id": presupuesto.id,
                "version_id": version.id,
                "numero_version": version.numero_version,
                "destino": "enlace-publico",
            },
        ).reference
        enlace, token = crear_enlace_propuesta(
            db,
            presupuesto=presupuesto,
            version=version,
            config=cfg,
            creado_por_usuario_id=db.info.get("usuario_id"),
            duracion_dias=duracion_dias,
        )
        db.add(NotaSeguimiento(
            presupuesto_id=presupuesto.id,
            texto=(
                f"Enlace público creado para V{version.numero_version}; "
                f"caduca el {enlace.expires_at.strftime('%d/%m/%Y %H:%M')}."
            ),
        ))
        url_creada = _url_publica_propuesta(request, token)
        db.commit()
    except (AuthNotConfigured, StorageError, GestionEnlacePropuestaError) as exc:
        db.rollback()
        return _pagina_enlaces_propuesta(
            request, presupuesto, db, error=str(exc), status_code=500,
        )
    auditoria.registrar_evento(
        db,
        "propuesta.enlace_creado",
        entidad="presupuesto",
        entidad_id=presupuesto.id,
        detalle={"enlace_id": enlace.id, "caduca": str(enlace.expires_at or "")},
    )
    return _pagina_enlaces_propuesta(
        request,
        presupuesto,
        db,
        enlace_creado=url_creada,
    )


@router.post("/presupuestos/{presupuesto_id}/enlaces/{enlace_id}/revocar")
def revocar_enlace_publico_web(
    presupuesto_id: int,
    enlace_id: int,
    db: Session = Depends(get_db),
):
    if es_lectura(db):
        return _redirect(
            f"/presupuestos/{presupuesto_id}/enlace-publico",
            error="Tu rol es de solo lectura y no permite revocar enlaces.",
        )
    enlace = db.get(EnlacePropuesta, enlace_id)
    if enlace is None or enlace.presupuesto_id != presupuesto_id:
        return _redirect(
            f"/presupuestos/{presupuesto_id}/enlace-publico",
            error="Enlace no encontrado.",
        )
    revocar_enlace_propuesta(db, enlace=enlace)
    db.add(NotaSeguimiento(
        presupuesto_id=presupuesto_id,
        texto=f"Enlace público {enlace.token_prefix}… revocado.",
    ))
    db.commit()
    auditoria.registrar_evento(
        db,
        "propuesta.enlace_revocado",
        entidad="presupuesto",
        entidad_id=presupuesto_id,
        detalle={"enlace_id": enlace.id},
    )
    return _redirect(
        f"/presupuestos/{presupuesto_id}/enlace-publico",
        msg="Enlace revocado. Ya no permite consultar la propuesta.",
    )


@router.post("/presupuestos/{presupuesto_id}/enlaces/{enlace_id}/notificar")
def reintentar_notificacion_propuesta_web(
    presupuesto_id: int,
    enlace_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    if not puede_gestionar(db):
        return _redirect(
            f"/presupuestos/{presupuesto_id}/enlace-publico",
            error="Solo propietarios y administradores pueden reenviar la notificación.",
        )
    enlace = db.get(EnlacePropuesta, enlace_id)
    if (
        enlace is None
        or enlace.presupuesto_id != presupuesto_id
        or enlace.respuesta == "pendiente"
    ):
        return _redirect(
            f"/presupuestos/{presupuesto_id}/enlace-publico",
            error="No existe una respuesta notificable.",
        )
    enviados, error = _notificar_respuesta_propuesta(request, db, enlace)
    if error:
        return _redirect(
            f"/presupuestos/{presupuesto_id}/enlace-publico",
            error=f"La respuesta sigue guardada, pero falló la notificación: {error}",
        )
    return _redirect(
        f"/presupuestos/{presupuesto_id}/enlace-publico",
        msg=f"Notificación enviada a {', '.join(enviados)}.",
    )


def _respuesta_propuesta_no_disponible(request: Request):
    return TEMPLATES.TemplateResponse(
        request,
        "public/proposal_unavailable.html",
        {},
        status_code=404,
        headers={
            "Cache-Control": "no-store, max-age=0",
            "Pragma": "no-cache",
            "Referrer-Policy": "no-referrer",
        },
    )


def _pagina_propuesta_publica(
    request: Request,
    enlace: EnlacePropuesta,
    token: str,
    *,
    error: str = "",
    datos: dict[str, str] | None = None,
    status_code: int = 200,
):
    return TEMPLATES.TemplateResponse(
        request,
        "public/proposal.html",
        {
            "propuesta": enlace,
            "token": token,
            "error_respuesta": error,
            "datos_respuesta": datos or {
                "nombre": enlace.cliente_nombre,
                "email": "",
                "comentario": "",
            },
        },
        status_code=status_code,
        headers={
            "Cache-Control": "no-store, max-age=0",
            "Pragma": "no-cache",
            "Referrer-Policy": "no-referrer",
            "X-Robots-Tag": "noindex, nofollow, noarchive",
        },
    )


@router.get("/propuestas/{token}", response_class=HTMLResponse)
def ver_propuesta_publica(
    token: str,
    request: Request,
    db: Session = Depends(get_public_proposal_db),
):
    enlace = resolver_enlace_propuesta(db, token=token)
    if enlace is None:
        return _respuesta_propuesta_no_disponible(request)
    return _pagina_propuesta_publica(request, enlace, token)


@router.post("/propuestas/{token}/responder", response_class=HTMLResponse)
def responder_propuesta_publica(
    token: str,
    request: Request,
    decision: str = Form(""),
    nombre: str = Form(""),
    email: str = Form(""),
    comentario: str = Form(""),
    declaracion: str = Form(""),
    db: Session = Depends(get_public_proposal_db),
):
    enlace = resolver_enlace_propuesta(db, token=token)
    if enlace is None:
        return _respuesta_propuesta_no_disponible(request)
    datos = {
        "nombre": str(nombre or "").strip(),
        "email": str(email or "").strip().lower(),
        "comentario": str(comentario or "").strip(),
    }
    if declaracion != "confirmada":
        return _pagina_propuesta_publica(
            request, enlace, token,
            error="Confirma que estás autorizado para responder esta propuesta.",
            datos=datos,
            status_code=400,
        )
    try:
        registrar_respuesta_propuesta(
            db,
            enlace=enlace,
            decision=decision,
            nombre=datos["nombre"],
            email=datos["email"],
            comentario=datos["comentario"],
        )
        db.commit()
        _notificar_respuesta_propuesta(request, db, enlace)
    except GestionEnlacePropuestaError as exc:
        db.rollback()
        enlace = resolver_enlace_propuesta(db, token=token)
        if enlace is None:
            return _respuesta_propuesta_no_disponible(request)
        return _pagina_propuesta_publica(
            request, enlace, token, error=str(exc), datos=datos, status_code=400,
        )
    return _redirect(f"/propuestas/{token}")


@router.get("/propuestas/{token}/pdf")
def ver_pdf_propuesta_publica(
    token: str,
    request: Request,
    download: int = 0,
    db: Session = Depends(get_public_proposal_db),
):
    enlace = resolver_enlace_propuesta(db, token=token)
    if enlace is None:
        return Response(status_code=404, headers=_NO_CACHE)
    try:
        contenido = read_reference(enlace.pdf_snapshot)
    except StorageError:
        return Response(status_code=404, headers=_NO_CACHE)
    nombre = re.sub(r"[^A-Za-z0-9_.-]+", "-", enlace.presupuesto_numero) or "propuesta"
    disposicion = "attachment" if download else "inline"
    return Response(
        contenido,
        media_type="application/pdf",
        headers={
            "Cache-Control": "no-store, max-age=0",
            "Pragma": "no-cache",
            "Referrer-Policy": "no-referrer",
            "X-Robots-Tag": "noindex, nofollow, noarchive",
            "Content-Disposition": f'{disposicion}; filename="presupuesto_{nombre}.pdf"',
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "sandbox",
            "Cross-Origin-Resource-Policy": "same-origin",
        },
    )


@router.get("/presupuestos/{presupuesto_id}", response_class=HTMLResponse)
def ver_presupuesto(presupuesto_id: int, request: Request, db: Session = Depends(get_db)):
    presupuesto = db.get(Presupuesto, presupuesto_id)
    if presupuesto is None:
        return _redirect("/presupuestos", error="Presupuesto no encontrado.")
    hoy = date.today()
    fecha_vencimiento = presupuesto.fecha + timedelta(days=presupuesto.validez_dias or 30)
    cfg = _config(db)
    tiempos = calcular_tiempos_presupuesto(
        presupuesto,
        db=db,
        horas_jornada=cfg.horas_jornada or 8.0,
        tarifa_hora_media=cfg.tarifa_hora_media or 8.0,
        usar_estimacion_coste=bool(cfg.estimar_tiempo_por_coste),
    )
    tiempos_por_partida = {
        t["partida_id"]: t
        for t in tiempos["partidas"]
        if t["partida_id"] is not None and t["fuente"] != "sin_datos"
    }
    return TEMPLATES.TemplateResponse(
        request,
        "budgets/detail.html",
        {
            "p": presupuesto,
            "estados": ESTADOS,
            "cfg": cfg,
            "versiones": presupuesto.versiones,
            "fecha_vencimiento": fecha_vencimiento,
            "dias_restantes": (fecha_vencimiento - hoy).days,
            "tiempos": tiempos,
            "tiempos_por_partida": tiempos_por_partida,
        },
    )


@router.get("/presupuestos/{presupuesto_id}/tiempos", response_class=HTMLResponse)
def ver_tiempos_presupuesto(presupuesto_id: int, request: Request, db: Session = Depends(get_db)):
    """Detalle completo de la estimación de tiempos de ejecución de la obra."""
    presupuesto = db.get(Presupuesto, presupuesto_id)
    if presupuesto is None:
        return _redirect("/presupuestos", error="Presupuesto no encontrado.")
    cfg = _config(db)
    tiempos = calcular_tiempos_presupuesto(
        presupuesto,
        db=db,
        horas_jornada=cfg.horas_jornada or 8.0,
        tarifa_hora_media=cfg.tarifa_hora_media or 8.0,
        usar_estimacion_coste=bool(cfg.estimar_tiempo_por_coste),
    )
    return TEMPLATES.TemplateResponse(
        request,
        "budgets/tiempos.html",
        {
            "p": presupuesto,
            "cfg": cfg,
            "tiempos": tiempos,
        },
    )


@router.post("/presupuestos/{presupuesto_id}/tiempos/manual")
async def guardar_tiempo_manual(presupuesto_id: int, request: Request, db: Session = Depends(get_db)):
    """Guarda el tiempo manual de una partida (horas por unidad) desde la página de tiempos.

    Acepta tanto FormData como JSON. Campos: partida_id, horas, horas_oficial, horas_ayudante, horas_equipo.
    Si solo se envía horas (total), se reparte automáticamente 60% oficial / 40% ayudante.
    Enviar horas=0 o vacío borra el override manual y vuelve a la estimación automática.
    """
    presupuesto = db.get(Presupuesto, presupuesto_id)
    if presupuesto is None:
        return {"ok": False, "error": "Presupuesto no encontrado."}
    # Soporta JSON y form-urlencoded
    data = {}
    ctype = request.headers.get("content-type", "")
    if "application/json" in ctype:
        try:
            data = await request.json()
        except Exception:
            data = {}
    else:
        try:
            form = await request.form()
            data = {k: form.get(k) for k in form.keys()}
        except Exception:
            try:
                data = await request.json()
            except Exception:
                data = {}
    try:
        partida_id = int(str(data.get("partida_id") or data.get("partida") or 0))
    except (TypeError, ValueError):
        return {"ok": False, "error": "Partida no válida."}
    partida = db.get(PresupuestoItem, partida_id)
    if partida is None or partida.capitulo is None or partida.capitulo.presupuesto_id != presupuesto.id:
        return {"ok": False, "error": "Partida no encontrada."}

    def _parse_horas(key):
        raw = data.get(key)
        if raw is None or str(raw).strip() == "":
            return None
        try:
            v = _f(raw, None)
            if v is None:
                return None
            if isinstance(v, float) and not math.isfinite(v):
                return None
            return max(0.0, float(v))
        except Exception:
            return None

    horas = _parse_horas("horas") if "horas" in data else _parse_horas("tiempo_manual_horas")
    h_of = _parse_horas("horas_oficial") if "horas_oficial" in data else _parse_horas("tiempo_manual_oficial_horas")
    h_ay = _parse_horas("horas_ayudante") if "horas_ayudante" in data else _parse_horas("tiempo_manual_ayudante_horas")
    h_eq = _parse_horas("horas_equipo") if "horas_equipo" in data else _parse_horas("tiempo_manual_equipo_horas")
    # Compat: si envían horas_por_unidad, horas_total, etc.
    if horas is None and h_of is None and h_ay is None and h_eq is None:
        # Intentar leer campos con prefijo manual_
        for alt in ["h_oficial", "h_ayudante", "h_equipo", "oficial", "ayudante", "equipo"]:
            if alt in data and _parse_horas(alt) is not None:
                if "oficial" in alt:
                    h_of = _parse_horas(alt)
                elif "ayudante" in alt:
                    h_ay = _parse_horas(alt)
                elif "equipo" in alt:
                    h_eq = _parse_horas(alt)

    # Si todos vacíos -> borrar manual (volver a automático)
    if horas is None and h_of is None and h_ay is None and h_eq is None:
        partida.tiempo_manual_horas = None
        partida.tiempo_manual_oficial_horas = None
        partida.tiempo_manual_ayudante_horas = None
        partida.tiempo_manual_equipo_horas = None
        db.commit()
        return {"ok": True, "borrado": True}

    # Si solo horas total, repartir; si hay desglose, priorizar desglose
    if h_of is None and h_ay is None and h_eq is None and horas is not None:
        # total único
        partida.tiempo_manual_horas = horas
        partida.tiempo_manual_oficial_horas = None
        partida.tiempo_manual_ayudante_horas = None
        partida.tiempo_manual_equipo_horas = None
    else:
        # desglose
        # Si horas total también viene, y desglose vacío, usar horas; si desglose presente, ignorar total suelto y calcular total como suma
        if horas is not None and h_of is None and h_ay is None and h_eq is None:
            partida.tiempo_manual_horas = horas
            partida.tiempo_manual_oficial_horas = None
            partida.tiempo_manual_ayudante_horas = None
            partida.tiempo_manual_equipo_horas = None
        else:
            # Guardar desglose; total se deja None y se calculará por suma
            partida.tiempo_manual_horas = None
            partida.tiempo_manual_oficial_horas = h_of
            partida.tiempo_manual_ayudante_horas = h_ay
            partida.tiempo_manual_equipo_horas = h_eq
            # Si todos los desgloses son 0 y horas también 0, interpretamos como borrar
            if (h_of or 0) == 0 and (h_ay or 0) == 0 and (h_eq or 0) == 0 and (horas or 0) == 0:
                # Si explícitamente enviaron 0, lo guardamos como 0 (partida con 0 horas)
                pass
    db.commit()
    # Devolver estimación recalculada para feedback instantáneo
    cfg = _config(db)
    t = calcular_tiempos_presupuesto(presupuesto, db=db, horas_jornada=cfg.horas_jornada or 8.0, tarifa_hora_media=cfg.tarifa_hora_media or 8.0, usar_estimacion_coste=bool(cfg.estimar_tiempo_por_coste))
    partida_t = next((x for x in t["partidas"] if x["partida_id"] == partida_id), None)
    return {"ok": True, "tiempos": t, "partida": partida_t}


@router.post("/presupuestos/{presupuesto_id}/tiempos/bulk")
async def guardar_tiempos_bulk(presupuesto_id: int, request: Request, db: Session = Depends(get_db)):
    """Asignación masiva rápida para partidas sin datos."""
    presupuesto = db.get(Presupuesto, presupuesto_id)
    if presupuesto is None:
        return {"ok": False, "error": "Presupuesto no encontrado."}
    try:
        payload = await request.json()
    except Exception:
        return {"ok": False, "error": "JSON no válido."}
    items = payload.get("items") if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        return {"ok": False, "error": "Formato no válido."}
    h_of_default = _f(payload.get("horas_oficial"), None) if isinstance(payload, dict) else None
    h_ay_default = _f(payload.get("horas_ayudante"), None) if isinstance(payload, dict) else None
    h_eq_default = _f(payload.get("horas_equipo"), None) if isinstance(payload, dict) else None
    horas_default = _f(payload.get("horas"), None) if isinstance(payload, dict) else None
    updated = 0
    for it in items:
        if not isinstance(it, dict):
            continue
        try:
            pid = int(it.get("partida_id") or it.get("id") or 0)
        except (TypeError, ValueError):
            continue
        p = db.get(PresupuestoItem, pid)
        if p is None or p.capitulo is None or p.capitulo.presupuesto_id != presupuesto.id:
            continue
        # Prioridad: valores en el item individual, si no los default del payload
        h = _f(it.get("horas"), horas_default) if horas_default is not None or it.get("horas") is not None else None
        h_of = _f(it.get("horas_oficial"), h_of_default) if h_of_default is not None or it.get("horas_oficial") is not None else None
        h_ay = _f(it.get("horas_ayudante"), h_ay_default) if h_ay_default is not None or it.get("horas_ayudante") is not None else None
        h_eq = _f(it.get("horas_equipo"), h_eq_default) if h_eq_default is not None or it.get("horas_equipo") is not None else None
        # Si no hay nada, omitir
        if h is None and h_of is None and h_ay is None and h_eq is None:
            continue
        if h_of is None and h_ay is None and h_eq is None and h is not None:
            p.tiempo_manual_horas = max(0.0, float(h))
            p.tiempo_manual_oficial_horas = None
            p.tiempo_manual_ayudante_horas = None
            p.tiempo_manual_equipo_horas = None
        else:
            p.tiempo_manual_horas = None
            p.tiempo_manual_oficial_horas = max(0.0, float(h_of)) if h_of is not None else None
            p.tiempo_manual_ayudante_horas = max(0.0, float(h_ay)) if h_ay is not None else None
            p.tiempo_manual_equipo_horas = max(0.0, float(h_eq)) if h_eq is not None else None
        updated += 1
    db.commit()
    cfg = _config(db)
    t = calcular_tiempos_presupuesto(presupuesto, db=db, horas_jornada=cfg.horas_jornada or 8.0, tarifa_hora_media=cfg.tarifa_hora_media or 8.0, usar_estimacion_coste=bool(cfg.estimar_tiempo_por_coste))
    return {"ok": True, "actualizadas": updated, "tiempos": t}


@router.get("/presupuestos/{presupuesto_id}/partidas/{partida_id}/descomposicion", response_class=HTMLResponse)
def ver_descomposicion_partida(presupuesto_id: int, partida_id: int, request: Request, db: Session = Depends(get_db)):
    """Muestra la matriz CYPE guardada sin volver a transformar el Excel."""
    presupuesto = db.get(Presupuesto, presupuesto_id)
    if presupuesto is None:
        return _redirect("/presupuestos", error="Presupuesto no encontrado.")
    partida = db.get(PresupuestoItem, partida_id)
    if partida is None or partida.capitulo is None or partida.capitulo.presupuesto_id != presupuesto.id:
        return _redirect(f"/presupuestos/{presupuesto_id}", error="Partida no encontrada.")
    descomposicion = partida.descomposicion_cype
    if descomposicion is None:
        return _redirect(f"/presupuestos/{presupuesto_id}", error="Esta partida no tiene un descompuesto CYPE asociado.")
    # Las filas creadas o editadas a mano pueden llevar una categoría de
    # coste explícita (elegida en el generador); se respeta sobre la derivada
    # del grupo/código para que los cálculos de la página coincidan.
    def _categoria_fila(fila):
        propia = str(getattr(fila, "categoria", "") or "").strip()
        if propia in {"materiales", "mano_obra", "complementarios", "otros"}:
            return propia
        return categoria_coste_cype(fila.grupo, fila.codigo)

    categorias = {fila.id: _categoria_fila(fila) for fila in descomposicion.filas if fila.tipo == "recurso"}
    grupos_categoria: dict[str, str] = {}
    for fila in descomposicion.filas:
        if fila.tipo == "recurso":
            grupos_categoria.setdefault(fila.grupo or "", _categoria_fila(fila))
    cfg = _config(db)
    tiempos = horas_por_unidad_descompuesto(descomposicion.filas, cfg.horas_jornada or 8.0)
    return TEMPLATES.TemplateResponse(request, "budgets/decomposition.html", {
        "p": presupuesto,
        "part": partida,
        "d": descomposicion,
        "categorias": categorias,
        "grupos_categoria": grupos_categoria,
        "tiempos_descompuesto": tiempos,
        "horas_jornada": cfg.horas_jornada or 8.0,
        "simbolo_moneda": SIMBOLOS.get(presupuesto.moneda, presupuesto.moneda),
    })


@router.post("/presupuestos/{presupuesto_id}/partidas/{partida_id}/descomposicion")
async def recalcular_descomposicion_partida(presupuesto_id: int, partida_id: int, request: Request, db: Session = Depends(get_db)):
    """Recalcula la cascada de costes tras editar rendimientos/precios.

    Cada recurso cuesta Rendimiento × Precio unitario por unidad de partida;
    los subtotales, complementarios (%) y el coste directo se derivan con las
    mismas reglas que las fórmulas del Excel original. Persiste los valores
    en la matriz, en los gastos de la partida y en el coste interno usado por
    el presupuesto.
    """
    presupuesto = db.get(Presupuesto, presupuesto_id)
    if presupuesto is None:
        return _redirect("/presupuestos", error="Presupuesto no encontrado.")
    partida = db.get(PresupuestoItem, partida_id)
    if partida is None or partida.capitulo is None or partida.capitulo.presupuesto_id != presupuesto.id:
        return _redirect(f"/presupuestos/{presupuesto_id}", error="Partida no encontrada.")
    descomposicion = partida.descomposicion_cype
    if descomposicion is None:
        return _redirect(f"/presupuestos/{presupuesto_id}", error="Esta partida no tiene un descompuesto CYPE asociado.")

    form = await request.form()
    filas = list(descomposicion.filas)

    # 1) Aplicar las ediciones: solo recursos. En la fila de porcentaje el
    #    precio es derivado (base de los demás subtotales) y no se edita.
    for fila in filas:
        if fila.tipo != "recurso":
            continue
        rendimiento_txt = form.get(f"rend_{fila.id}")
        precio_txt = form.get(f"precio_{fila.id}")
        if rendimiento_txt is None and precio_txt is None:
            continue
        rendimiento_nuevo = numero_local(rendimiento_txt)
        if rendimiento_nuevo is not None and rendimiento_nuevo >= 0:
            fila.rendimiento = rendimiento_nuevo
        if str(fila.unidad or "").strip() != "%":
            precio_nuevo = numero_local(precio_txt)
            if precio_nuevo is not None and precio_nuevo >= 0:
                fila.precio_unitario = precio_nuevo

    # 2) Recalcular la cascada completa con las reglas del formato.
    resultado = recalcular_descompuesto_cype(filas)
    for indice, fila in enumerate(filas):
        if indice in resultado["importes"]:
            fila.importe = resultado["importes"][indice]
        if indice in resultado["subtotales"]:
            fila.importe = resultado["subtotales"][indice]
        if indice in resultado["precios_complementarios"]:
            fila.precio_unitario = resultado["precios_complementarios"][indice]
        if fila.tipo == "total":
            fila.importe = resultado["coste_directo"]

    # 3) Mantener la matriz completa (celdas) sincronizada con los valores.
    _sincronizar_celdas_descompuesto(filas)

    # 4) Gastos de la partida y coste directo unitario.
    costes = resultado["costes"]
    partida.coste_materiales = max(0.0, costes.get("materiales", 0.0))
    partida.coste_mano_obra = max(0.0, costes.get("mano_obra", 0.0))
    partida.coste_complementarios = max(0.0, costes.get("complementarios", 0.0))
    partida.coste_otros = max(0.0, costes.get("otros", 0.0))
    descomposicion.coste_directo_unitario = resultado["coste_directo"]
    if form.get("ajustar_precio_venta"):
        partida.precio_unitario = resultado["coste_directo"]

    # 5) El JSON de matriz que alimenta versiones/clonados, sincronizado.
    descomposicion.filas_originales_json = json.dumps([
        {
            "numero": fila.numero_fila_excel,
            "celdas": json.loads(fila.celdas_json or "[]"),
            "formulas": json.loads(fila.formulas_json or "{}"),
            "tipo": fila.tipo,
            "grupo": fila.grupo,
            "categoria": fila.categoria,
            "codigo": fila.codigo,
            "unidad": fila.unidad,
            "descripcion": fila.descripcion,
            "rendimiento": fila.rendimiento,
            "precio_unitario": fila.precio_unitario,
            "importe": fila.importe,
        }
        for fila in filas
    ], ensure_ascii=False)

    db.commit()
    return _redirect(
        f"/presupuestos/{presupuesto_id}/partidas/{partida_id}/descomposicion",
        msg=f"Costes recalculados. Coste directo: {fmt_monto(resultado['coste_directo'], presupuesto.moneda)} / {descomposicion.unidad or partida.unidad}.",
    )


@router.post("/presupuestos/{presupuesto_id}/versiones")
def crear_version_manual(presupuesto_id: int, motivo: str = Form(""), db: Session = Depends(get_db)):
    presupuesto = db.get(Presupuesto, presupuesto_id)
    if presupuesto is None:
        return _redirect("/presupuestos", error="Presupuesto no encontrado.")
    version = crear_version(db, presupuesto, motivo or "Versión creada manualmente")
    db.commit()
    return _redirect(f"/presupuestos/{presupuesto_id}#versiones", msg=f"Versión {version.numero_version} congelada.")


@router.get("/presupuestos/{presupuesto_id}/versiones/comparar", response_class=HTMLResponse)
def comparar_versiones(presupuesto_id: int, a: int, b: int, request: Request, db: Session = Depends(get_db)):
    versiones = {v.id: v for v in db.query(PresupuestoVersion).filter_by(presupuesto_id=presupuesto_id).all()}
    va, vb = versiones.get(a), versiones.get(b)
    if not va or not vb:
        return _redirect(f"/presupuestos/{presupuesto_id}#versiones", error="Selecciona dos versiones válidas.")
    return TEMPLATES.TemplateResponse(request, "budgets/compare_versions.html", {"p": va.presupuesto, "a": va, "b": vb, "sa": leer_snapshot(va), "sb": leer_snapshot(vb)})


@router.get("/presupuestos/{presupuesto_id}/versiones/{version_id}", response_class=HTMLResponse)
def ver_version(presupuesto_id: int, version_id: int, request: Request, db: Session = Depends(get_db)):
    version = db.get(PresupuestoVersion, version_id)
    if version is None or version.presupuesto_id != presupuesto_id:
        return _redirect(f"/presupuestos/{presupuesto_id}", error="Versión no encontrada.")
    return TEMPLATES.TemplateResponse(request, "budgets/version.html", {"p": version.presupuesto, "version": version, "snapshot": leer_snapshot(version)})


@router.get("/presupuestos/{presupuesto_id}/exportar")
def exportar_presupuesto(presupuesto_id: int, formato: str = "csv", db: Session = Depends(get_db)):
    """Exportar presupuesto a CSV o Excel con formato profesional."""
    p = db.get(Presupuesto, presupuesto_id)
    if p is None:
        return _redirect("/presupuestos", error="Presupuesto no encontrado.")

    if formato.lower() == "excel" or formato.lower() == "xlsx":
        from ..services.excel_export import exportar_presupuesto_excel
        buf = exportar_presupuesto_excel(p, _config(db))
        return Response(
            content=buf.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="presupuesto_{p.numero}.xlsx"'},
        )

    # CSV por defecto
    def num(v):
        return f"{v:.2f}".replace(".", ",")

    filas = [["Capítulo", "Partida", "Descripción", "Unidad", "Cantidad", "Precio unitario", "Importe"]]
    for cap in p.capitulos:
        for part in cap.partidas:
            filas.append([
                cap.nombre, part.nombre, part.descripcion, part.unidad,
                num(part.cantidad_total), num(part.precio_unitario), num(part.importe),
            ])
    filas.append([])
    filas.append(["BASE IMPONIBLE", "", "", "", "", "", num(p.base)])
    if p.descuento_pct:
        filas.append(["DESCUENTO (" + f"{p.descuento_pct:.1f}".replace(".", ",") + " %)", "", "", "", "", "", "- " + num(p.descuento_monto)])
    filas.append([f"I.V.A. ({p.impuesto_pct:.1f} %)", "", "", "", "", "", num(p.impuesto_monto)])
    filas.append(["TOTAL", "", "", "", "", "", num(p.total)])
    return _csv_response(filas, f"presupuesto_{p.numero}.csv")


@router.post("/presupuestos/{presupuesto_id}/notas")
def agregar_nota(presupuesto_id: int, texto: str = Form(""), db: Session = Depends(get_db)):
    presupuesto = db.get(Presupuesto, presupuesto_id)
    if presupuesto is None:
        return _redirect("/presupuestos", error="Presupuesto no encontrado.")
    texto = texto.strip()
    if not texto:
        return _redirect(f"/presupuestos/{presupuesto_id}#notas", error="Escribe el texto de la nota.")
    db.add(NotaSeguimiento(presupuesto_id=presupuesto.id, texto=texto))
    db.commit()
    return _redirect(f"/presupuestos/{presupuesto_id}#notas", msg="Nota añadida.")


# ---------------------------------------------------------------------------
# Documentos de cobro no fiscales (rutas históricas /facturas)
# ---------------------------------------------------------------------------

@router.post("/presupuestos/{presupuesto_id}/factura")
def crear_factura(presupuesto_id: int, db: Session = Depends(get_db)):
    presupuesto = db.get(Presupuesto, presupuesto_id)
    if presupuesto is None:
        return _redirect("/presupuestos", error="Presupuesto no encontrado.")
    if presupuesto.estado != "aprobado":
        return _redirect(f"/presupuestos/{presupuesto_id}",
                         error="Solo se puede crear el documento de cobro desde un presupuesto «aprobado».")
    ya = db.query(Factura).filter(Factura.presupuesto_id == presupuesto.id).first()
    if ya:
        return _redirect(f"/facturas/{ya.id}", msg="Este presupuesto ya tiene un documento de cobro asociado.")

    año = date.today().year
    # La factura queda vinculada a una versión aprobada concreta; si procede
    # de una base anterior sin versión, se crea la instantánea ahora.
    version = db.query(PresupuestoVersion).filter_by(presupuesto_id=presupuesto.id, estado="aprobado").order_by(PresupuestoVersion.numero_version.desc()).first()
    if version is None:
        version = crear_version(db, presupuesto, "Versión aprobada usada para el documento de cobro")
        db.flush()
    factura = Factura(
        numero=proximo_numero_factura(db, año),
        year=año,
        fecha=date.today(),
        titulo=presupuesto.titulo,
        direccion_obra=presupuesto.direccion_obra,
        codigo_postal=presupuesto.codigo_postal,
        moneda=presupuesto.moneda,
        moneda_base=getattr(presupuesto, "moneda_base", None) or "USD",
        tipo_cambio=presupuesto.tipo_cambio,
        fecha_tipo_cambio=presupuesto.fecha_tipo_cambio,
        fuente_tipo_cambio=getattr(presupuesto, "fuente_tipo_cambio", "") or "",
        impuesto_pct=presupuesto.impuesto_pct,
        descuento_pct=presupuesto.descuento_pct,
        notas=presupuesto.notas,
        condiciones=presupuesto.condiciones,
        presupuesto_id=presupuesto.id,
        presupuesto_version_id=version.id,
        client_id=presupuesto.client_id,
    )
    for cap_o in presupuesto.capitulos:
        cap_c = FacturaCapitulo(nombre=cap_o.nombre, orden=cap_o.orden)
        factura.capitulos.append(cap_c)
        for part_o in cap_o.partidas:
            # La factura debe reflejar EXACTAMENTE el total del presupuesto
            # aprobado: se facturan solo las partidas que forman parte de su
            # total (mismo filtro que calculations.calcular_totales). Las
            # opcionales/alternativas no seleccionadas y las excluidas NO se
            # facturan: incluirlas inflaba la factura respecto del documento
            # aprobado.
            tipo = (part_o.tipo_partida or "included").lower()
            if tipo == "excluded":
                continue
            if tipo in ("optional", "alternative") and not part_o.seleccionada:
                continue
            cap_c.partidas.append(FacturaItem(
                nombre=part_o.nombre,
                descripcion=part_o.descripcion,
                unidad=part_o.unidad,
                cantidad=part_o.cantidad_total,
                precio_unitario=part_o.precio_unitario,
                orden=part_o.orden,
            ))
    db.add(factura)
    db.commit()
    return _redirect(f"/facturas/{factura.id}", msg=f"Documento de cobro {factura.numero} creado desde el presupuesto {presupuesto.numero}.")


@router.get("/facturas", response_class=HTMLResponse)
def listar_facturas(request: Request, db: Session = Depends(get_db)):
    facturas = db.query(Factura).order_by(Factura.id.desc()).all()
    return TEMPLATES.TemplateResponse(request, "facturas/list.html", {"facturas": facturas})


@router.get("/facturas/{factura_id}", response_class=HTMLResponse)
def ver_factura(factura_id: int, request: Request, db: Session = Depends(get_db)):
    factura = db.get(Factura, factura_id)
    if factura is None:
        return _redirect("/facturas", error="Documento de cobro no encontrado.")
    return TEMPLATES.TemplateResponse(request, "facturas/detail.html", {"f": factura})


@router.get("/facturas/{factura_id}/pdf")
def descargar_pdf_factura(factura_id: int, inline: int = 0, db: Session = Depends(get_db)):
    factura = db.get(Factura, factura_id)
    if factura is None:
        return _redirect("/facturas", error="Documento de cobro no encontrado.")
    resultado = _generar_pdf_seguro(
        lambda: common.pdf_service.generar_factura_pdf(factura, _config(db)),
        f"el PDF del documento de cobro {factura.numero}",
    )
    if isinstance(resultado, Response) and resultado.status_code != 200:
        return resultado
    return _respuesta_pdf(resultado, f"documento_cobro_{factura.numero}.pdf", inline)


@router.post("/facturas/{factura_id}/estado")
def cambiar_estado_factura(factura_id: int, estado: str = Form(...), db: Session = Depends(get_db)):
    factura = db.get(Factura, factura_id)
    if factura is None:
        return _redirect("/facturas", error="Documento de cobro no encontrado.")
    if estado in ("emitida", "anulada"):
        estado_anterior = str(factura.estado or "")
        factura.estado = estado
        db.commit()
        auditoria.registrar_evento(
            db,
            "factura.estado",
            entidad="factura",
            entidad_id=factura_id,
            detalle={"de": estado_anterior, "a": estado},
        )
        return _redirect(f"/facturas/{factura_id}", msg=f"Documento de cobro marcado como «{estado}».")
    return _redirect(f"/facturas/{factura_id}", error="Estado inválido.")


@router.post("/facturas/{factura_id}/eliminar")
def eliminar_factura(factura_id: int, db: Session = Depends(get_db)):
    factura = db.get(Factura, factura_id)
    if factura is None:
        return _redirect("/facturas", error="Documento de cobro no encontrado.")
    numero = factura.numero
    db.delete(factura)
    db.commit()
    return _redirect("/facturas", msg=f"Documento de cobro {numero} eliminado.")


@router.post("/presupuestos/{presupuesto_id}/borrador")
async def guardar_borrador_presupuesto(presupuesto_id: int, request: Request, db: Session = Depends(get_db)):
    """Autoguardado del editor: persiste el borrador de la estructura.

    El navegador envía {capitulos, ts} cada pocos segundos mientras hay
    cambios. El borrador es independiente del presupuesto guardado: solo se
    usa para recuperar trabajo si la página se cierra sin guardar, y se
    borra al hacer un guardado completo del formulario.
    """
    presupuesto = db.get(Presupuesto, presupuesto_id)
    if presupuesto is None:
        return {"ok": False, "error": "Presupuesto no encontrado."}
    try:
        payload = await request.json()
    except (TypeError, ValueError):
        return {"ok": False, "error": "Datos inválidos."}
    capitulos = payload.get("capitulos")
    if capitulos is None:
        # Borrado explícito del borrador (botón «Descartar»).
        db.query(BorradorPresupuesto).filter(BorradorPresupuesto.presupuesto_id == presupuesto_id).delete()
        db.commit()
        return {"ok": True, "ts": None}
    if not isinstance(capitulos, list) or len(capitulos) > MAX_FILAS:
        return {"ok": False, "error": "Estructura no válida."}
    try:
        datos_json = json.dumps({"capitulos": capitulos, "ts": int(payload.get("ts") or 0)}, ensure_ascii=False)
    except (TypeError, ValueError):
        return {"ok": False, "error": "Datos no serializables."}
    if len(datos_json) > 5 * 1024 * 1024:  # 5 MB máx. de borrador
        return {"ok": False, "error": "El borrador es demasiado grande."}
    borrador = db.query(BorradorPresupuesto).filter(BorradorPresupuesto.presupuesto_id == presupuesto_id).first()
    if borrador is None:
        borrador = BorradorPresupuesto(presupuesto_id=presupuesto_id, datos=datos_json)
        db.add(borrador)
    else:
        borrador.datos = datos_json
    db.commit()
    return {"ok": True, "ts": int(payload.get("ts") or 0)}


@router.get("/presupuestos/{presupuesto_id}/borrador")
def leer_borrador_presupuesto(presupuesto_id: int, db: Session = Depends(get_db)):
    """Devuelve el borrador del autoguardado (si existe)."""
    borrador = db.query(BorradorPresupuesto).filter(BorradorPresupuesto.presupuesto_id == presupuesto_id).first()
    if borrador is None:
        return {"ok": False}
    try:
        datos = json.loads(borrador.datos or "{}")
    except (TypeError, ValueError):
        datos = {}
    if not isinstance(datos, dict) or not isinstance(datos.get("capitulos"), list):
        return {"ok": False}
    return {"ok": True, "ts": datos.get("ts", 0), "capitulos": datos["capitulos"]}


@router.get("/presupuestos/{presupuesto_id}/editar", response_class=HTMLResponse)
def editar_presupuesto_form(presupuesto_id: int, request: Request, db: Session = Depends(get_db)):
    presupuesto = db.get(Presupuesto, presupuesto_id)
    if presupuesto is None:
        return _redirect("/presupuestos", error="Presupuesto no encontrado.")
    from ..services.catalogo_propio import asegurar_catalogo_propio
    asegurar_catalogo_propio(db)
    clientes = db.query(Cliente).order_by(Cliente.nombre).all()
    partidas_catalogo = _indice_catalogo_para_editor(db, presupuesto.moneda, presupuesto.tipo_cambio)
    productos_catalogo = db.query(Producto).order_by(Producto.ultimo_uso.desc(), Producto.usos.desc(), Producto.nombre).all()
    cfg = _config(db)
    recursos_base = db.query(Recurso).order_by(Recurso.ultimo_uso.desc(), Recurso.usos.desc(), Recurso.descripcion).all()
    recursos_catalogo = _recursos_editor_mercado(db, recursos_base, cfg, presupuesto.moneda, presupuesto.tipo_cambio)
    plantillas = db.query(Plantilla).order_by(Plantilla.nombre).all()
    # Borrador del autoguardado: solo se ofrece si es más reciente que el
    # último guardado del presupuesto (updated_at).
    borrador_servidor = None
    try:
        borrador = db.query(BorradorPresupuesto).filter(BorradorPresupuesto.presupuesto_id == presupuesto_id).first()
        if borrador is not None:
            datos = json.loads(borrador.datos or "{}")
            if isinstance(datos, dict) and isinstance(datos.get("capitulos"), list):
                # Date.now() del navegador viene en milisegundos; se compara
                # en UTC con el momento del último guardado del presupuesto.
                ts_borrador = datetime.utcfromtimestamp(float(datos.get("ts") or 0) / 1000.0)
                ts_guardado = (presupuesto.updated_at or presupuesto.created_at or datetime.utcnow())
                if ts_borrador > ts_guardado:
                    borrador_servidor = datos
    except Exception:
        borrador_servidor = None
    return TEMPLATES.TemplateResponse(
        request,
        "budgets/form.html",
        {
            "presupuesto": presupuesto,
            "clientes": clientes,
            "cfg": _config(db),
            "hoy": date.today(),
            "partidas_catalogo": partidas_catalogo,
            "productos_catalogo": productos_catalogo,
            "recursos_catalogo": recursos_catalogo,
            "categorias": _categorias(db),
            "plantillas": plantillas,
            "estados": ESTADOS,
            "campos_importables": ETIQUETAS_CAMPOS,
            "borrador_servidor": borrador_servidor,
            "tiempos_catalogo": _tiempos_catalogo(db, presupuesto),
        },
    )


@router.post("/presupuestos/{presupuesto_id}/editar")
async def actualizar_presupuesto(presupuesto_id: int, request: Request, db: Session = Depends(get_db)):
    presupuesto = db.get(Presupuesto, presupuesto_id)
    if presupuesto is None:
        return _redirect("/presupuestos", error="Presupuesto no encontrado.")
    form = await request.form()
    estaba_congelado = presupuesto.estado in ESTADOS_CONGELABLES
    moneda_nueva = normalizar_moneda(form.get("moneda"), "USD")
    moneda_anterior = normalizar_moneda(presupuesto.moneda, "USD")
    cambio_moneda = moneda_nueva != moneda_anterior
    confirmado_moneda = str(form.get("confirmar_cambio_moneda", "0")) == "1"
    if cambio_moneda and estaba_congelado:
        return _redirect(f"/presupuestos/{presupuesto_id}/editar", error="Un presupuesto enviado o aprobado no puede cambiar de moneda; crea una nueva versión.")
    if cambio_moneda and not confirmado_moneda:
        return _redirect(f"/presupuestos/{presupuesto_id}/editar", error="Confirma expresamente el cambio de moneda para convertir los importes.")

    cliente = db.get(Cliente, int(_f(form.get("client_id"))))
    if cliente is None:
        return _redirect(f"/presupuestos/{presupuesto_id}/editar", error="Selecciona un cliente válido.")
    capitulos, partidas = _leer_formulario_presupuesto(form, db)
    if cambio_moneda:
        tasa_origen = presupuesto.tipo_cambio if moneda_anterior != "USD" else 1
        tasa_destino = _f(form.get("tipo_cambio"), None) if str(form.get("tipo_cambio", "")).strip() else None
        if moneda_nueva != "USD" and (tasa_destino is None or tasa_destino <= 0):
            return _redirect(f"/presupuestos/{presupuesto_id}/editar", error=f"Indica una tasa positiva para convertir {moneda_anterior} a {moneda_nueva}.")
        if moneda_anterior != "USD" and (tasa_origen is None or tasa_origen <= 0):
            return _redirect(f"/presupuestos/{presupuesto_id}/editar", error=f"El presupuesto no tiene una tasa válida de origen ({moneda_anterior}); no se puede convertir automáticamente.")
        for partida in partidas:
            for clave in ("precio", "coste_materiales", "coste_mano_obra", "coste_complementarios", "coste_otros", "prod_precio", "prod_coste"):
                if partida.get(clave) is not None:
                    partida[clave] = float(convertir_moneda(partida[clave], moneda_anterior, moneda_nueva, tasa_destino, tasa_origen))
    capitulos = [c for c in capitulos if c["nombre"]]
    if not capitulos:
        return _redirect(f"/presupuestos/{presupuesto_id}/editar", error="Agrega al menos un capítulo con nombre.")
    if not any(p["nombre"] for p in partidas):
        return _redirect(f"/presupuestos/{presupuesto_id}/editar", error="Agrega al menos una partida.")
    error_condiciones = _validar_condiciones_presupuesto(form, partidas)
    error_alternativas = _validar_alternativas(partidas)
    if error_condiciones or error_alternativas:
        return _redirect(f"/presupuestos/{presupuesto_id}/editar", error=error_condiciones or error_alternativas)

    try:
        f = date.fromisoformat(form.get("fecha", "")) if form.get("fecha") else date.today()
    except ValueError:
        f = date.today()
    estado = form.get("estado", presupuesto.estado)

    presupuesto.client_id = cliente.id
    presupuesto.fecha = f
    presupuesto.titulo = str(form.get("titulo", "")).strip()
    presupuesto.direccion_obra = str(form.get("direccion_obra", "")).strip()
    presupuesto.codigo_postal = str(form.get("codigo_postal", "")).strip()
    presupuesto.validez_dias = int(_f(form.get("validez_dias"), 30))
    presupuesto.moneda = "USD" if str(cfg.empresa_pais or "").strip().lower() == "venezuela" and normalizar_moneda(form.get("moneda"), "USD") == "VES" else normalizar_moneda(form.get("moneda"), "USD")
    presupuesto.tipo_cambio = _f(form.get("tipo_cambio"), None) if str(form.get("tipo_cambio", "")).strip() else None
    presupuesto.fuente_tipo_cambio = str(form.get("fuente_tipo_cambio", "") or "").strip()[:120]
    presupuesto.impuesto_pct = _f(form.get("impuesto_pct"), 16.0)
    presupuesto.descuento_pct = _f(form.get("descuento_pct"), 0.0)
    presupuesto.estado = estado if _estado_valido(estado) else presupuesto.estado
    presupuesto.notas = str(form.get("notas", "")).strip()
    presupuesto.condiciones = str(form.get("condiciones", "")).strip()
    presupuesto.con_portada = bool(form.get("con_portada"))
    presupuesto.mostrar_firmas = bool(form.get("mostrar_firmas"))
    presupuesto.mostrar_resumen_capitulos = bool(form.get("mostrar_resumen_capitulos"))
    presupuesto.mostrar_garantias = bool(form.get("mostrar_garantias"))
    presupuesto.usar_funciones_avanzadas = bool(form.get("usar_funciones_avanzadas"))
    presupuesto.gastos_indirectos_pct = _f(form.get("gastos_indirectos_pct"))
    presupuesto.imprevistos_pct = _f(form.get("imprevistos_pct"))
    presupuesto.transporte_monto = _f(form.get("transporte_monto"))
    presupuesto.otros_cargos_monto = _f(form.get("otros_cargos_monto"))
    presupuesto.estilo_pdf = form.get("estilo_pdf") if form.get("estilo_pdf") in ("elegante", "tecnica", "minimalista", "corporativa", "compacta", "editorial") else "elegante"
    presupuesto.mostrar_ahorro = bool(form.get("mostrar_ahorro"))
    presupuesto.incluir_anexos = bool(form.get("incluir_anexos"))
    presupuesto.numero_control = str(form.get("numero_control", "")).strip(); presupuesto.retencion_pct = _f(form.get("retencion_pct")); presupuesto.operacion_exenta = bool(form.get("operacion_exenta")); presupuesto.clausula_cambiaria = str(form.get("clausula_cambiaria", "")).strip()
    try: presupuesto.fecha_tipo_cambio = date.fromisoformat(form.get("fecha_tipo_cambio")) if form.get("fecha_tipo_cambio") else None
    except ValueError: presupuesto.fecha_tipo_cambio = None

    if form.get("quitar_foto_proyecto"):
        anterior = presupuesto.foto_proyecto
        presupuesto.foto_proyecto = ""
        _borrar_imagen(anterior, db)
    else:
        foto_file = form.get("foto_proyecto")
        if isinstance(foto_file, UploadFileStarlette) and foto_file.filename:
            ruta = await _guardar_imagen(foto_file, f"projects/p{presupuesto_id}_{date.today().isoformat()}", db)
            if ruta:
                anterior = presupuesto.foto_proyecto
                presupuesto.foto_proyecto = ruta
                _borrar_imagen(anterior, db)

    # Imágenes: limpia las antiguas que se dejen de usar y guarda las nuevas
    antiguas = [p.producto_imagen for cap in presupuesto.capitulos for p in cap.partidas]
    antiguas_opciones = [
        opcion.imagen
        for cap in presupuesto.capitulos
        for partida in cap.partidas
        for opcion in partida.productos_opciones
    ]
    imagenes = {}
    for i, pd in enumerate(partidas):
        archivo = pd.get("prod_imagen_file")
        if isinstance(archivo, UploadFileStarlette) and archivo.filename:
            ruta = await _guardar_imagen(archivo, f"products/p{presupuesto_id}_{i}_{date.today().isoformat()}", db)
            if ruta:
                imagenes[i] = ruta
    # Imágenes nuevas de las opciones múltiples: cada archivo viene
    # acompañado de un input paralelo `p_opcion_imagen_idx` con el formato
    # "<partida_idx_global>:<opcion_idx>".
    imagenes_opciones = {}
    for archivo_op, idx_str in zip(
        form.getlist("p_opcion_imagen"),
        form.getlist("p_opcion_imagen_idx"),
    ):
        if not (isinstance(archivo_op, UploadFileStarlette) and archivo_op.filename):
            continue
        ruta = await _guardar_imagen(archivo_op, f"products/opc_p{presupuesto_id}_{len(imagenes_opciones)}", db)
        if ruta and idx_str and ":" in idx_str:
            p_idx, o_idx = idx_str.split(":", 1)
            imagenes_opciones[(int(p_idx), int(o_idx))] = ruta

    # Firma digital del cliente
    if form.get("quitar_firma"):
        anterior = presupuesto.firma_cliente
        presupuesto.firma_cliente = ""
        _borrar_imagen(anterior, db)
    else:
        firma = form.get("firma_cliente")
        if isinstance(firma, str) and firma.startswith("data:image/png;base64,"):
            nueva_firma = _guardar_firma(firma, db)
            if nueva_firma:
                anterior = presupuesto.firma_cliente
                presupuesto.firma_cliente = nueva_firma
                _borrar_imagen(anterior, db)

    # Nombres ya presentes (para no inflar usos al volver a guardar sin cambios).
    nombres_previos = {p.nombre for cap in presupuesto.capitulos for p in cap.partidas}
    productos_previos = {p.producto_nombre for cap in presupuesto.capitulos for p in cap.partidas}

    _montar_presupuesto(presupuesto, capitulos, partidas, imagenes, imagenes_opciones)
    db.flush()
    nuevas = {p.producto_imagen for cap in presupuesto.capitulos for p in cap.partidas}
    nuevas_opciones = {
        opcion.imagen
        for cap in presupuesto.capitulos
        for partida in cap.partidas
        for opcion in partida.productos_opciones
    }
    for ruta in antiguas:
        if ruta and ruta not in nuevas:
            _borrar_imagen(ruta, db)
    for ruta in antiguas_opciones:
        if ruta and ruta not in nuevas_opciones:
            _borrar_imagen(ruta, db)
    _guardar_en_catalogos(db, partidas, imagenes)
    db.flush()
    _vincular_partidas_catalogo(db, presupuesto)
    _registrar_usos(db, partidas, nombres_previos)
    _registrar_usos_productos(db, partidas, productos_previos)
    if estaba_congelado or presupuesto.estado in ESTADOS_CONGELABLES:
        crear_version(db, presupuesto, str(form.get("motivo_version", "")).strip() or "Cambios guardados en una nueva versión")
    db.commit()
    # El guardado completo del formulario deja sin efecto el borrador del
    # autoguardado (ya no hay cambios pendientes que recuperar).
    db.query(BorradorPresupuesto).filter(BorradorPresupuesto.presupuesto_id == presupuesto_id).delete()
    db.commit()
    _sincronizar_recursos(db)
    return _redirect(f"/presupuestos/{presupuesto_id}", msg="Presupuesto actualizado.")


@router.post("/presupuestos/{presupuesto_id}/estado")
def cambiar_estado(presupuesto_id: int, estado: str = Form(...), db: Session = Depends(get_db)):
    presupuesto = db.get(Presupuesto, presupuesto_id)
    if presupuesto is None:
        return _redirect("/presupuestos", error="Presupuesto no encontrado.")
    if _estado_valido(estado):
        estado_anterior = str(presupuesto.estado or "")
        presupuesto.estado = estado
        if estado in ESTADOS_CONGELABLES:
            crear_version(db, presupuesto, f"Documento marcado como {estado.replace('_', ' ')}")
        db.commit()
        auditoria.registrar_evento(
            db,
            "presupuesto.estado",
            entidad="presupuesto",
            entidad_id=presupuesto_id,
            detalle={"de": estado_anterior, "a": estado},
        )
        return _redirect(f"/presupuestos/{presupuesto_id}", msg=f"Estado cambiado a «{estado}».")
    return _redirect(f"/presupuestos/{presupuesto_id}", error="Estado inválido.")


@router.post("/presupuestos/{presupuesto_id}/duplicar")
def duplicar_presupuesto(presupuesto_id: int, db: Session = Depends(get_db)):
    original = db.get(Presupuesto, presupuesto_id)
    if original is None:
        return _redirect("/presupuestos", error="Presupuesto no encontrado.")

    año_actual = date.today().year
    nuevo_num = proximo_numero(db, año_actual)

    copia = Presupuesto(
        numero=nuevo_num,
        year=año_actual,
        fecha=date.today(),
        titulo=f"Copia de {original.titulo}" if original.titulo else "Copia de Presupuesto",
        direccion_obra=original.direccion_obra,
        codigo_postal=original.codigo_postal,
        validez_dias=original.validez_dias,
        moneda=original.moneda,
        tipo_cambio=original.tipo_cambio,
        impuesto_pct=original.impuesto_pct,
        descuento_pct=original.descuento_pct,
        estado="borrador",
        notas=original.notas,
        condiciones=original.condiciones,
        con_portada=original.con_portada,
        foto_proyecto=_copiar_imagen(original.foto_proyecto, "projects/dup", db) or original.foto_proyecto,
        mostrar_firmas=original.mostrar_firmas,
        mostrar_resumen_capitulos=original.mostrar_resumen_capitulos,
        mostrar_garantias=getattr(original, "mostrar_garantias", False),
        firma_cliente=_copiar_imagen(original.firma_cliente, "signatures/dup", db) or original.firma_cliente,
        usar_funciones_avanzadas=original.usar_funciones_avanzadas,
        gastos_indirectos_pct=original.gastos_indirectos_pct,
        imprevistos_pct=original.imprevistos_pct,
        transporte_monto=original.transporte_monto,
        otros_cargos_monto=original.otros_cargos_monto,
        estilo_pdf=original.estilo_pdf, mostrar_ahorro=original.mostrar_ahorro, incluir_anexos=original.incluir_anexos,
        numero_control=original.numero_control, fecha_tipo_cambio=original.fecha_tipo_cambio,
        retencion_pct=original.retencion_pct, operacion_exenta=original.operacion_exenta,
        clausula_cambiaria=original.clausula_cambiaria,
        client_id=original.client_id,
    )

    for cap_o in original.capitulos:
        cap_c = Capitulo(nombre=cap_o.nombre, orden=cap_o.orden)
        copia.capitulos.append(cap_c)
        for part_o in cap_o.partidas:
            part_c = PresupuestoItem(
                codigo_externo=part_o.codigo_externo,
                partida_catalogo_id=part_o.partida_catalogo_id,
                nombre=part_o.nombre,
                descripcion=part_o.descripcion,
                unidad=part_o.unidad,
                cantidad=part_o.cantidad,
                precio_unitario=part_o.precio_unitario,
                moneda=part_o.moneda or copia.moneda or "USD",
                orden=part_o.orden,
                producto_nombre=part_o.producto_nombre,
                producto_precio=part_o.producto_precio,
                producto_coste=part_o.producto_coste,
                producto_unidad=part_o.producto_unidad,
                producto_imagen=_copiar_imagen(part_o.producto_imagen, "products/dup", db) or part_o.producto_imagen,
                tipo_partida=part_o.tipo_partida,
                seleccionada=part_o.seleccionada,
                coste_materiales=part_o.coste_materiales,
                coste_mano_obra=part_o.coste_mano_obra,
                coste_complementarios=part_o.coste_complementarios,
                coste_otros=part_o.coste_otros,
                desperdicio_pct=part_o.desperdicio_pct,
                margen_pct=part_o.margen_pct,
                grupo_alternativa=part_o.grupo_alternativa,
                mostrar_en_pdf=part_o.mostrar_en_pdf,
                tiempo_manual_horas=part_o.tiempo_manual_horas,
                tiempo_manual_oficial_horas=part_o.tiempo_manual_oficial_horas,
                tiempo_manual_ayudante_horas=part_o.tiempo_manual_ayudante_horas,
                tiempo_manual_equipo_horas=part_o.tiempo_manual_equipo_horas,
            )
            cap_c.partidas.append(part_c)
            descomposicion_copia = _clonar_descomposicion_cype(part_o.descomposicion_cype)
            if descomposicion_copia is not None:
                part_c.descomposicion_cype = descomposicion_copia
            for med_o in part_o.mediciones:
                med_c = Medicion(
                    concepto=med_o.concepto,
                    cantidad=med_o.cantidad,
                    orden=med_o.orden,
                )
                part_c.mediciones.append(med_c)
            # Opciones múltiples de producto: se duplican con su propia imagen
            # (copiada para no compartir el archivo con el presupuesto original).
            for opc_o in (part_o.productos_opciones or []):
                part_c.productos_opciones.append(PresupuestoItemProducto(
                    nombre=opc_o.nombre,
                    descripcion=opc_o.descripcion,
                    precio=opc_o.precio,
                    coste=opc_o.coste,
                    unidad=opc_o.unidad,
                    categoria=opc_o.categoria,
                    marca=opc_o.marca,
                    modelo=opc_o.modelo,
                    sku=opc_o.sku,
                    color=opc_o.color,
                    acabado=opc_o.acabado,
                    imagen=_copiar_imagen(opc_o.imagen, "products/dup_opc", db) or opc_o.imagen,
                    seleccionado=opc_o.seleccionado,
                    orden=opc_o.orden,
                ))

    db.add(copia)
    db.commit()
    return _redirect(f"/presupuestos/{copia.id}/editar", msg=f"Presupuesto duplicado correctamente como {copia.numero}.")


@router.post("/presupuestos/{presupuesto_id}/eliminar")
def eliminar_presupuesto(presupuesto_id: int, db: Session = Depends(get_db)):
    presupuesto = db.get(Presupuesto, presupuesto_id)
    if presupuesto is None:
        return _redirect("/presupuestos", error="Presupuesto no encontrado.")
    numero = presupuesto.numero
    referencias = {presupuesto.foto_proyecto, presupuesto.firma_cliente}
    referencias.update(anexo.archivo for anexo in presupuesto.anexos)
    for cap in presupuesto.capitulos:
        for p in cap.partidas:
            referencias.add(p.producto_imagen)
            referencias.update(opcion.imagen for opcion in p.productos_opciones)
            if p.descomposicion_cype:
                referencias.add(p.descomposicion_cype.archivo_origen)
    db.delete(presupuesto)
    db.flush()
    for referencia in referencias:
        _borrar_imagen(referencia, db)
    db.commit()
    return _redirect("/presupuestos", msg=f"Presupuesto {numero} eliminado.")


@router.post("/presupuestos/{presupuesto_id}/anexos")
async def agregar_anexo(presupuesto_id: int, request: Request, db: Session = Depends(get_db)):
    presupuesto = db.get(Presupuesto, presupuesto_id)
    if not presupuesto: return _redirect("/presupuestos", error="Presupuesto no encontrado.")
    form = await request.form(); archivo = form.get("archivo")
    if not isinstance(archivo, UploadFileStarlette) or not archivo.filename or Path(archivo.filename).suffix.lower() != ".pdf":
        return _redirect(f"/presupuestos/{presupuesto_id}", error="Selecciona un anexo PDF válido.")
    contenido = await archivo.read()
    if not contenido or len(contenido) > 12 * 1024 * 1024 or not contenido.startswith(b"%PDF-"):
        return _redirect(f"/presupuestos/{presupuesto_id}", error="El anexo PDF no es válido o supera 12 MB.")
    referencia = save_object(
        db, contenido, "anexos", archivo.filename, "application/pdf",
        prefix=f"presupuesto-{presupuesto.id}",
    ).reference
    db.add(AnexoPresupuesto(
        presupuesto_id=presupuesto.id,
        nombre=str(form.get("nombre") or archivo.filename)[:250],
        archivo=referencia,
    ))
    db.commit()
    return _redirect(f"/presupuestos/{presupuesto_id}#anexos", msg="Anexo añadido.")

@router.post("/presupuestos/{presupuesto_id}/anexos/{anexo_id}/eliminar")
def eliminar_anexo(presupuesto_id: int, anexo_id: int, db: Session = Depends(get_db)):
    anexo=db.get(AnexoPresupuesto, anexo_id)
    if not anexo or anexo.presupuesto_id != presupuesto_id: return _redirect(f"/presupuestos/{presupuesto_id}", error="Anexo no encontrado.")
    referencia = anexo.archivo
    db.delete(anexo)
    _borrar_imagen(referencia, db)
    db.commit()
    return _redirect(f"/presupuestos/{presupuesto_id}#anexos", msg="Anexo eliminado.")


@router.post("/presupuestos/{presupuesto_id}/pdf-descargado")
def registrar_pdf_descargado(presupuesto_id: int, db: Session = Depends(get_db)):
    presupuesto = db.get(Presupuesto, presupuesto_id)
    if presupuesto is None:
        return JSONResponse({"ok": False, "error": "Presupuesto no encontrado."}, status_code=404)
    if es_lectura(db) or presupuesto.es_demo:
        return {"ok": True, "registrado": False}
    cfg = _config(db)
    if not cfg.onboarding_pdf_descargado:
        cfg.onboarding_pdf_descargado = True
        cfg.primer_pdf_at = datetime.utcnow()
        db.commit()
    return {"ok": True, "registrado": True}


@router.get("/presupuestos/{presupuesto_id}/pdf")
def descargar_pdf(presupuesto_id: int, inline: int = 0, db: Session = Depends(get_db)):
    presupuesto = db.get(Presupuesto, presupuesto_id)
    if presupuesto is None:
        return _redirect("/presupuestos", error="Presupuesto no encontrado.")
    cfg = _config(db)
    resultado = _generar_pdf_seguro(
        lambda: common.pdf_service.generar_pdf(presupuesto, cfg),
        f"el PDF del presupuesto {presupuesto.numero}",
    )
    if isinstance(resultado, Response) and resultado.status_code != 200:
        return resultado
    return _respuesta_pdf(resultado, f"presupuesto_{presupuesto.numero}.pdf", inline)


@router.get("/presupuestos/{presupuesto_id}/contrato")
def descargar_contrato(presupuesto_id: int, inline: int = 0, db: Session = Depends(get_db)):
    """Genera un contrato de servicios real en PDF a partir del presupuesto.

    Reemplaza a los antiguos botones "Generar Contrato (IA)" / "Generar
    Contrato Smart", que sólo mostraban un mensaje fijo sin producir ningún
    documento."""
    presupuesto = db.get(Presupuesto, presupuesto_id)
    if presupuesto is None:
        return _redirect("/presupuestos", error="Presupuesto no encontrado.")
    resultado = _generar_pdf_seguro(
        lambda: generar_contrato_pdf(presupuesto, _config(db)),
        f"el contrato del presupuesto {presupuesto.numero}",
    )
    if isinstance(resultado, Response) and resultado.status_code != 200:
        return resultado
    return _respuesta_pdf(resultado, f"contrato_{presupuesto.numero}.pdf", inline)
