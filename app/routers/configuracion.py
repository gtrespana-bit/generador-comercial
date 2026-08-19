"""Configuración, copias de seguridad, importación, respaldo, exportación y baja."""  # E4-001 — router por dominio

from fastapi import APIRouter

from . import common
from .common import *  # noqa: F401,F403  (re-exporta modelos, servicios y utilidades)
from ..services import auditoria

router = APIRouter()

# Configuración
# ---------------------------------------------------------------------------


def _slug_organizacion_unico(db: Session, nombre: str, organizacion_id: int) -> str:
    """Slug legible desde el nombre, único entre organizaciones.

    El slug se usa en nombres de archivo (p. ej. el recibo de licencia), así
    que no puede colisionar con otra organización aunque el nombre se repita.
    """
    base = _slug_organizacion(nombre)[:100] or "organizacion"
    candidato = base
    existentes = {
        slug
        for (slug,) in db.query(Organizacion.slug)
        .filter(Organizacion.slug != "")
        .all()
    }
    contador = 1
    while candidato in existentes and contador < 100:
        candidato = f"{base}-{contador}"
        contador += 1
    return candidato

@router.get("/configuracion", response_class=HTMLResponse)
def ver_configuracion(request: Request, db: Session = Depends(get_db)):
    org = db.get(Organizacion, int(db.info.get("organizacion_id") or 0))
    from ..services.licencias import resumen_licencia_cliente

    licencia = resumen_licencia_cliente(
        db, int(db.info.get("organizacion_id") or 0)
    )
    # Recibo descargable: solo si el plan se pagó por el checkout y la compra
    # guardó su período. Un plan de cortesía o migrado a mano no tiene cobro
    # que documentar, así que la tarjeta no enseña el enlace.
    from ..services.compras import ultima_compra_con_recibo

    compra_recibo = ultima_compra_con_recibo(
        db, int(db.info.get("organizacion_id") or 0)
    )
    # En escritorio (SQLite) no hay membresías: el usuario local es el
    # propietario por definición. En la web solo gestionan propietario/admin.
    puede_editar = DATABASE_IS_SQLITE or puede_gestionar(db)
    return TEMPLATES.TemplateResponse(
        request,
        "settings.html",
        {
            "cfg": _config(db),
            "org_nombre": org.nombre if org else "",
            "puede_editar": puede_editar,
            "licencia": licencia,
            "compra_recibo": compra_recibo,
        },
    )


@router.post("/configuracion")
async def guardar_configuracion(request: Request, db: Session = Depends(get_db)):
    if not DATABASE_IS_SQLITE and not puede_gestionar(db):
        return _redirect(
            "/configuracion",
            error="Solo propietarios y administradores pueden modificar la configuración de la organización.",
        )
    form = await request.form()
    cfg = _config(db)
    # Nombre de la organización: el que se muestra en el menú lateral.
    org = db.get(Organizacion, int(db.info.get("organizacion_id") or 0))
    org_nombre = str(form.get("organizacion_nombre", "")).strip()
    org_nombre_anterior = ""
    if org and org_nombre and org_nombre != org.nombre:
        org_nombre_anterior = str(org.nombre or "")
        org.nombre = org_nombre[:200]
        org.slug = _slug_organizacion_unico(db, org_nombre, org.id)
    cfg.empresa_nombre = str(form.get("empresa_nombre", "")).strip() or "Mi Empresa"
    cfg.empresa_legal = str(form.get("empresa_legal", "")).strip()
    cfg.empresa_rif = str(form.get("empresa_rif", "")).strip()
    cfg.empresa_pais = str(form.get("empresa_pais", "Venezuela")).strip() or "Venezuela"
    cfg.empresa_ciudad = str(form.get("empresa_ciudad", "")).strip()
    cfg.empresa_direccion = str(form.get("empresa_direccion", "")).strip()
    cfg.empresa_telefono = str(form.get("empresa_telefono", "")).strip()
    cfg.empresa_email = str(form.get("empresa_email", "")).strip()
    cfg.empresa_web = str(form.get("empresa_web", "")).strip()
    cfg.iva_default = max(0.0, min(_f(form.get("iva_default"), 16.0), 100.0))
    moneda = form.get("moneda_default", "USD")
    cfg.moneda_default = moneda if moneda in ("USD", "Bs") else "USD"
    cfg.validez_default = max(1, min(int(_f(form.get("validez_default"), 30)), 3650))
    cfg.notas_default = str(form.get("notas_default", "")).strip()
    cfg.condiciones_default = str(form.get("condiciones_default", "")).strip()
    cfg.pdf_color = str(form.get("pdf_color", "#04265D")).strip() or "#04265D"
    cfg.logo_ancho_pdf = max(120.0, min(_f(form.get("logo_ancho_pdf"), 360.0), 420.0))
    cfg.con_portada_default = bool(form.get("con_portada_default"))
    cfg.mostrar_firmas_default = bool(form.get("mostrar_firmas_default"))
    cfg.mostrar_resumen_capitulos_default = bool(form.get("mostrar_resumen_capitulos_default"))
    cfg.mostrar_garantias_default = bool(form.get("mostrar_garantias_default"))
    cfg.activar_funciones_avanzadas = bool(form.get("activar_funciones_avanzadas"))
    cfg.mostrar_costes_internos = bool(form.get("mostrar_costes_internos"))
    cfg.mostrar_alternativas = bool(form.get("mostrar_alternativas"))
    cfg.mostrar_cargos_adicionales = bool(form.get("mostrar_cargos_adicionales"))
    cfg.activar_funciones_venezuela = bool(form.get("activar_funciones_venezuela")); cfg.mostrar_numero_control = bool(form.get("mostrar_numero_control")); cfg.mostrar_tasa_cambio = bool(form.get("mostrar_tasa_cambio")); cfg.mostrar_total_bs = bool(form.get("mostrar_total_bs")); cfg.mostrar_retenciones = bool(form.get("mostrar_retenciones")); cfg.mostrar_clausula_cambiaria = bool(form.get("mostrar_clausula_cambiaria")); cfg.datos_bancarios = str(form.get("datos_bancarios", "")).strip()
    cfg.horas_jornada = max(1.0, min(_f(form.get("horas_jornada"), 8.0), 24.0))
    cfg.tarifa_hora_media = max(0.5, _f(form.get("tarifa_hora_media"), 8.0))
    cfg.estimar_tiempo_por_coste = bool(form.get("estimar_tiempo_por_coste"))

    if form.get("quitar_logo"):
        anterior = cfg.logo
        cfg.logo = ""
        _borrar_imagen(anterior, db)
    else:
        logo = form.get("logo")
        if isinstance(logo, UploadFileStarlette) and logo.filename:
            ruta = await _guardar_imagen(logo, "logo", db)
            if ruta:
                anterior = cfg.logo
                cfg.logo = ruta
                _borrar_imagen(anterior, db)

    # Los valores por defecto marcados se aplican también a los presupuestos
    # ya existentes (sólo en sentido activador: si desmarcas una casilla, los
    # presupuestos existentes no se tocan; únicamente afecta a los nuevos).
    cambios = 0
    if cfg.con_portada_default:
        cambios += db.query(Presupuesto).filter(Presupuesto.con_portada.is_(False)).update(
            {Presupuesto.con_portada: True}, synchronize_session=False
        )
    if cfg.mostrar_resumen_capitulos_default:
        cambios += db.query(Presupuesto).filter(Presupuesto.mostrar_resumen_capitulos.is_(False)).update(
            {Presupuesto.mostrar_resumen_capitulos: True}, synchronize_session=False
        )
    if cfg.mostrar_firmas_default:
        cambios += db.query(Presupuesto).filter(Presupuesto.mostrar_firmas.is_(False)).update(
            {Presupuesto.mostrar_firmas: True}, synchronize_session=False
        )
    if cfg.mostrar_garantias_default:
        cambios += db.query(Presupuesto).filter(Presupuesto.mostrar_garantias.is_(False)).update(
            {Presupuesto.mostrar_garantias: True}, synchronize_session=False
        )

    db.commit()
    # E4-026: rastro del cambio (después del commit, best-effort).
    auditoria.registrar_evento(db, "configuracion.actualizada", entidad="configuracion")
    if org_nombre_anterior:
        auditoria.registrar_evento(
            db,
            "organizacion.renombrada",
            entidad="organizacion",
            entidad_id=org.id if org else None,
            detalle={"de": org_nombre_anterior, "a": org_nombre[:200]},
        )
    if cambios:
        plural = "s" if cambios != 1 else ""
        return _redirect(
            "/configuracion",
            msg=f"Configuración guardada. Las opciones marcadas se aplicaron a {cambios} presupuesto{plural} existente{plural}.",
        )
    return _redirect("/configuracion", msg="Configuración guardada.")


# ---------------------------------------------------------------------------
# Copia de seguridad (descargar / restaurar)
# ---------------------------------------------------------------------------

@router.get("/configuracion/backup")
def descargar_backup():
    """Descarga una copia completa de una instalación SQLite local."""
    if not common.DATABASE_IS_SQLITE:
        return _redirect(
            "/configuracion",
            error="La versión web usa backups administrados; no descarga el archivo completo de PostgreSQL.",
        )
    uploads = UPLOADS_DIR
    tmp_db = BACKUPS_DIR / "tmp_backup.db"
    try:
        copia_seguridad_sqlite(tmp_db)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(tmp_db, "presupuestos.db")
            if uploads.exists():
                for p in sorted(uploads.rglob("*")):
                    if p.is_file():
                        # En desarrollo uploads cuelga de static; en el exe
                        # cuelga directamente de DATA_DIR. En ambos casos el
                        # nombre dentro del ZIP debe ser siempre uploads/....
                        z.write(p, (Path("uploads") / p.relative_to(uploads)).as_posix())
            if PRIVATE_STORAGE_DIR.exists():
                for p in sorted(PRIVATE_STORAGE_DIR.rglob("*")):
                    if p.is_file():
                        z.write(p, (Path("private_storage") / p.relative_to(PRIVATE_STORAGE_DIR)).as_posix())
            z.writestr(
                "LEEME_BACKUP.txt",
                "Copia de seguridad de CotizaT\n"
                "==============================\n"
                f"Creada el {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
                "Para restaurarla: abre la aplicación, ve a Configuración →\n"
                "«Copia de seguridad y restauración» → «Restaurar copia» y\n"
                "selecciona este archivo .zip.\n\n"
                "Contenido:\n"
                "  · presupuestos.db  → todos los datos (clientes, presupuestos,\n"
                "                       partidas, productos, plantillas, configuración)\n"
                "  · uploads/         → archivos históricos compatibles\n"
                "  · private_storage/ → archivos nuevos servidos por el proxy privado\n",
            )
        buf.seek(0)
        nombre = f"backup_presupuestos_{datetime.now().strftime('%Y%m%d_%H%M')}.zip"
        return Response(
            content=buf.getvalue(),
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
        )
    finally:
        try:
            tmp_db.unlink(missing_ok=True)
        except OSError:
            pass


def _extraer_backup_zip(ruta_zip: Path, destino: Path):
    """Extrae SQLite y los almacenes local privado e histórico de un backup.

    Devuelve (ruta_db, ruta_uploads | None, ruta_privada | None). Lanza ValueError si el zip no
    es válido o contiene rutas inseguras (zip slip).
    """
    destino.mkdir(exist_ok=True)
    try:
        with zipfile.ZipFile(ruta_zip) as z:
            db_tmp = None
            for info in z.infolist():
                nombre = info.filename.replace("\\", "/")
                partes = nombre.split("/")
                if nombre.startswith("/") or ".." in partes:
                    raise ValueError("La copia contiene rutas no válidas.")
                if info.is_dir():
                    continue
                archivo_destino = (destino / nombre).resolve()
                try:
                    dentro = Path(os.path.commonpath([
                        str(archivo_destino), str(destino.resolve())
                    ])) == destino.resolve()
                except ValueError:
                    dentro = False
                if not dentro:
                    raise ValueError("La copia contiene rutas no válidas.")
                z.extract(info, destino)
                if nombre == "presupuestos.db" or nombre.endswith("/presupuestos.db"):
                    db_tmp = archivo_destino
        if db_tmp is None or not db_tmp.exists():
            raise ValueError("La copia no contiene el archivo presupuestos.db.")
        uploads_tmp = destino / "uploads"
        private_tmp = destino / "private_storage"
        return (
            db_tmp,
            uploads_tmp if uploads_tmp.is_dir() else None,
            private_tmp if private_tmp.is_dir() else None,
        )
    except zipfile.BadZipFile:
        raise ValueError("El archivo no es un .zip válido.")


@router.post("/configuracion/restaurar")
async def restaurar_backup(request: Request):
    if not common.DATABASE_IS_SQLITE:
        return _redirect(
            "/configuracion",
            error="La restauración de archivos SQLite está desactivada en la versión web.",
        )
    form = await request.form()
    archivo = form.get("archivo")
    if not isinstance(archivo, UploadFileStarlette) or not archivo.filename:
        return _redirect("/configuracion", error="Selecciona un archivo de copia de seguridad (.zip o .db).")
    ext = Path(archivo.filename).suffix.lower()
    if ext not in (".zip", ".db"):
        return _redirect("/configuracion", error="El archivo debe ser .zip (copia de seguridad) o .db (base de datos).")

    # Volcado a disco por chunks para no cargar todo en memoria
    subida = BACKUPS_DIR / f"subida_{uuid.uuid4().hex[:10]}"
    subida.parent.mkdir(parents=True, exist_ok=True)
    extraido = None
    try:
        with open(subida, "wb") as f:
            while chunk := await archivo.read(1024 * 1024):
                f.write(chunk)

        if ext == ".zip":
            extraido = subida.parent / f"extraido_{uuid.uuid4().hex[:8]}"
            db_tmp, uploads_tmp, private_tmp = _extraer_backup_zip(subida, extraido)
        else:
            db_tmp, uploads_tmp, private_tmp = subida, None, None

        if not es_base_valida(db_tmp):
            return _redirect("/configuracion", error="El archivo no es una base de datos válida.")

        restaurar_base(db_tmp, uploads_tmp, private_tmp)
        return _redirect(
            "/configuracion",
            msg="✅ Copia restaurada correctamente. Antes de restaurar se guardó una copia de lo anterior en la carpeta «backups».",
        )
    except ValueError as e:
        return _redirect("/configuracion", error=str(e))
    finally:
        try:
            subida.unlink(missing_ok=True)
            if extraido is not None:
                shutil.rmtree(extraido, ignore_errors=True)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Importación de una instalación SQLite local hacia la web (E1W-012)
# ---------------------------------------------------------------------------
# Dos pasos: «analizar» muestra un resumen honesto (qué entra, qué se omite y
# por qué) sin escribir nada; «confirmar» exige volver a subir el MISMO
# archivo (SHA-256 verificado) más una casilla de confirmación explícita.
# Nunca se migran datos privados sin acción y confirmación del propietario.


async def _leer_instalacion_subida(request: Request):
    """Archivo subido del formulario, validado en tamaño; None si falta."""
    form = await request.form()
    archivo = form.get("archivo")
    if not isinstance(archivo, UploadFileStarlette) or not archivo.filename:
        return None, form
    contenido = await archivo.read()
    if len(contenido) > LIMITE_INSTALACION_BYTES:
        raise ErrorInstalacion("El archivo supera el límite de 50 MB.")
    return contenido, form


@router.get("/configuracion/importar-instalacion", response_class=HTMLResponse)
def importar_instalacion_form(request: Request, db: Session = Depends(get_db)):
    """Pantalla del asistente; disponible también en SQLite para probar en local."""
    return TEMPLATES.TemplateResponse(
        request,
        "importar_instalacion.html",
        {"resumen": None, "resultado": None, "rol": db.info.get("rol_membresia")},
    )


@router.post("/configuracion/importar-instalacion/analizar", response_class=HTMLResponse)
async def analizar_instalacion_subida(request: Request, db: Session = Depends(get_db)):
    try:
        contenido, _form = await _leer_instalacion_subida(request)
        if contenido is None:
            return _redirect(
                "/configuracion/importar-instalacion",
                error="Selecciona la copia de seguridad (.zip) o la base (.db) de tu instalación.",
            )
        resumen = analizar_instalacion(db, contenido)
    except (ErrorInstalacion, PermisoOrganizacionError) as exc:
        return _redirect("/configuracion/importar-instalacion", error=str(exc))
    return TEMPLATES.TemplateResponse(
        request,
        "importar_instalacion.html",
        {"resumen": resumen, "resultado": None, "rol": db.info.get("rol_membresia")},
    )


@router.post("/configuracion/importar-instalacion/confirmar", response_class=HTMLResponse)
async def confirmar_instalacion_subida(request: Request, db: Session = Depends(get_db)):
    try:
        contenido, form = await _leer_instalacion_subida(request)
        if contenido is None:
            return _redirect(
                "/configuracion/importar-instalacion",
                error="Vuelve a seleccionar el archivo para confirmar la importación.",
            )
        if str(form.get("confirmar", "")).strip() != "si":
            return _redirect(
                "/configuracion/importar-instalacion",
                error="Marca la casilla de confirmación para importar tus datos.",
            )
        sha256 = str(form.get("sha256", "")).strip()
        if not sha256:
            return _redirect(
                "/configuracion/importar-instalacion",
                error="Falta el análisis previo: analiza el archivo antes de confirmar.",
            )
        resultado = importar_instalacion(db, contenido, sha256_esperado=sha256)
        db.commit()
    except (ErrorInstalacion, PermisoOrganizacionError) as exc:
        db.rollback()
        return _redirect("/configuracion/importar-instalacion", error=str(exc))
    _sincronizar_recursos(db)
    return TEMPLATES.TemplateResponse(
        request,
        "importar_instalacion.html",
        {"resumen": None, "resultado": resultado, "rol": db.info.get("rol_membresia")},
    )


# ---------------------------------------------------------------------------
# Respaldo y restauración web completos por organización (E3-020 / E3-021)
# ---------------------------------------------------------------------------
# La copia web es un paquete verificable (manifest + SHA-256 por archivo) que
# funciona igual en PostgreSQL y en SQLite. La restauración conserva el flujo
# de dos pasos de E1W-012: analizar (sin escribir nada) y confirmar exigiendo
# volver a subir el MISMO archivo más una casilla de confirmación explícita.


async def _leer_respaldo_subido(request: Request) -> tuple[Path, str, dict]:
    """Streaming a /tmp (serverless-safe). Devuelve (ruta temporal, sha256, form)."""
    form = await request.form()
    archivo = form.get("archivo")
    if not isinstance(archivo, UploadFileStarlette) or not archivo.filename:
        raise ErrorRespaldo("Selecciona el archivo de copia de seguridad (.zip).")
    destino = Path(tempfile.gettempdir()) / f"cotizat-respaldo-{uuid.uuid4().hex}.zip"
    digesto = hashlib.sha256()
    total = 0
    try:
        with open(destino, "wb") as archivo_local:
            while chunk := await archivo.read(1024 * 1024):
                total += len(chunk)
                if total > LIMITE_RESPALDO_BYTES:
                    raise ErrorRespaldo("El archivo supera el límite de 300 MB.")
                digesto.update(chunk)
                archivo_local.write(chunk)
        if total == 0:
            raise ErrorRespaldo("El archivo de copia está vacío.")
    except Exception:
        destino.unlink(missing_ok=True)
        raise
    return destino, digesto.hexdigest(), form


@router.get("/configuracion/respaldo", response_class=HTMLResponse)
def respaldo_web_form(request: Request, db: Session = Depends(get_db)):
    """Pantalla del respaldo web: descargar copia y restaurar en dos pasos."""
    if not puede_gestionar(db):
        return _redirect(
            "/configuracion",
            error="Solo propietarios y administradores pueden gestionar el respaldo completo.",
        )
    return TEMPLATES.TemplateResponse(
        request,
        "respaldo.html",
        {"resumen": None, "resultado": None, "rol": db.info.get("rol_membresia")},
    )


@router.get("/configuracion/respaldo/descargar")
def descargar_respaldo_web(db: Session = Depends(get_db)):
    """Descarga el paquete completo y verificable de la organización activa."""
    if not puede_gestionar(db):
        return _redirect(
            "/configuracion",
            error="Solo propietarios y administradores pueden descargar el respaldo completo.",
        )
    try:
        contenido = generar_respaldo(db)
    except ErrorRespaldo as exc:
        return _redirect("/configuracion/respaldo", error=str(exc))
    nombre = f"cotizat_respaldo_{datetime.now().strftime('%Y%m%d_%H%M')}.zip"
    auditoria.registrar_evento(db, "datos.respaldo_descargado", entidad="respaldo")
    return Response(
        content=contenido,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{nombre}"',
            "Cache-Control": "no-store",
        },
    )


@router.post("/configuracion/respaldo/restaurar", response_class=HTMLResponse)
async def analizar_respaldo_subido(request: Request, db: Session = Depends(get_db)):
    """Paso 1: analiza y verifica la copia sin escribir nada."""
    if not puede_gestionar(db):
        return _redirect(
            "/configuracion",
            error="Solo propietarios y administradores pueden restaurar el respaldo completo.",
        )
    ruta_temporal = None
    try:
        ruta_temporal, sha256, _form = await _leer_respaldo_subido(request)
        resumen = analizar_respaldo(db, ruta_temporal)
        resumen.sha256_paquete = sha256
    except (ErrorRespaldo, PermisoOrganizacionError) as exc:
        return _redirect("/configuracion/respaldo", error=str(exc))
    finally:
        if ruta_temporal is not None:
            ruta_temporal.unlink(missing_ok=True)
    return TEMPLATES.TemplateResponse(
        request,
        "respaldo.html",
        {"resumen": resumen, "resultado": None, "rol": db.info.get("rol_membresia")},
    )


@router.post("/configuracion/respaldo/restaurar/confirmar", response_class=HTMLResponse)
async def confirmar_respaldo_subido(request: Request, db: Session = Depends(get_db)):
    """Paso 2: mismo archivo + confirmación explícita; ejecuta la restauración."""
    if not puede_gestionar(db):
        return _redirect(
            "/configuracion",
            error="Solo propietarios y administradores pueden restaurar el respaldo completo.",
        )
    ruta_temporal = None
    try:
        ruta_temporal, sha256, form = await _leer_respaldo_subido(request)
        if str(form.get("confirmar", "")).strip() != "si":
            raise ErrorRespaldo(
                "Marca la casilla de confirmación para restaurar la copia."
            )
        esperado = str(form.get("sha256", "")).strip()
        if not esperado:
            raise ErrorRespaldo(
                "Falta el análisis previo: analiza la copia antes de confirmar."
            )
        if sha256 != esperado:
            raise ErrorRespaldo(
                "El archivo no es el mismo que analizaste. Vuelve a analizarlo y "
                "sube exactamente ese archivo para confirmar."
            )
        resultado = restaurar_respaldo(db, ruta_temporal)
        db.commit()
    except (ErrorRespaldo, PermisoOrganizacionError) as exc:
        db.rollback()
        return _redirect("/configuracion/respaldo", error=str(exc))
    finally:
        if ruta_temporal is not None:
            ruta_temporal.unlink(missing_ok=True)
    auditoria.registrar_evento(
        db, "datos.restauracion_ejecutada", entidad="respaldo"
    )
    _sincronizar_recursos(db)
    return TEMPLATES.TemplateResponse(
        request,
        "respaldo.html",
        {"resumen": None, "resultado": resultado, "rol": db.info.get("rol_membresia")},
    )


# ---------------------------------------------------------------------------
# Exportación portátil (E3-022) y baja de organización (E3-023)
# ---------------------------------------------------------------------------

@router.get("/configuracion/exportacion/descargar")
def descargar_exportacion_organizacion(db: Session = Depends(get_db)):
    """Exportación legible y verificable: CSV por tabla, archivos con nombre y
    el respaldo completo embebido, para llevarse los datos fuera de CotizaT."""
    if not puede_gestionar(db):
        return _redirect(
            "/configuracion",
            error="Solo propietarios y administradores pueden descargar la exportación completa.",
        )
    try:
        contenido = generar_exportacion(db)
    except ErrorRespaldo as exc:
        return _redirect("/configuracion/respaldo", error=str(exc))
    nombre = f"cotizat_exportacion_{datetime.now().strftime('%Y%m%d_%H%M')}.zip"
    auditoria.registrar_evento(
        db, "datos.exportacion_descargada", entidad="exportacion"
    )
    return Response(
        content=contenido,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{nombre}"',
            "Cache-Control": "no-store",
        },
    )


@router.get("/configuracion/actividad", response_class=HTMLResponse)
def ver_actividad(request: Request, pagina: int = 1, db: Session = Depends(get_db)):
    """Registro de actividad de la organización (E4-026 / E4-027).

    Solo propietario/administrador: es la trazabilidad de quién cambió
    precios, documentos, estados y equipo. El registro es inmutable (la
    aplicación solo inserta) y se muestra paginado, lo más reciente primero.
    """
    if not DATABASE_IS_SQLITE and not puede_gestionar(db):
        return _redirect(
            "/configuracion",
            error="Solo propietarios y administradores pueden ver el registro de actividad.",
        )
    por_pagina = 50
    eventos, total = auditoria.eventos_de_organizacion(
        db, pagina=pagina, por_pagina=por_pagina
    )
    paginas = max(1, (total + por_pagina - 1) // por_pagina)
    return TEMPLATES.TemplateResponse(
        request,
        "actividad.html",
        {
            "eventos": eventos,
            "total": total,
            "pagina": max(1, int(pagina or 1)),
            "paginas": paginas,
            "acciones_legibles": auditoria.ACCIONES_LEGIBLES,
        },
    )


@router.get("/configuracion/baja", response_class=HTMLResponse)
def baja_organizacion_form(request: Request, db: Session = Depends(get_db)):
    """Pantalla de baja: resumen de lo que se borrará y confirmación por
    escrito del nombre exacto de la organización. Solo el propietario."""
    if not es_propietario(db):
        return _redirect(
            "/configuracion",
            error="Solo el propietario puede dar de baja la organización.",
        )
    try:
        resumen = resumen_baja(db)
    except BajaError as exc:
        return _redirect("/configuracion", error=str(exc))
    return TEMPLATES.TemplateResponse(
        request,
        "baja.html",
        {"resumen": resumen, "rol": db.info.get("rol_membresia")},
    )


@router.post("/configuracion/baja/confirmar", response_class=HTMLResponse)
async def confirmar_baja_organizacion(request: Request, db: Session = Depends(get_db)):
    """Ejecuta la baja verificada. Tras el borrado no hay organización que
    consultar, así que se responde directamente con la página de completado
    (sin redirect) y se retira la cookie de organización."""
    if not es_propietario(db):
        return _redirect(
            "/configuracion",
            error="Solo el propietario puede dar de baja la organización.",
        )
    form = await request.form()
    try:
        nombre = ejecutar_baja(
            db,
            nombre_confirmado=str(form.get("nombre_confirmado", "")),
            confirmar=str(form.get("confirmar", "")) == "si",
        )
    except (BajaError, PermisoOrganizacionError) as exc:
        db.rollback()
        return _redirect("/configuracion/baja", error=str(exc))
    # Constancia de la baja como evento global (los eventos tenant de la
    # organización acaban de borrarse con ella; este queda para el operador).
    auditoria.anotar_sesion(
        "organizacion.baja",
        email=str(db.info.get("auth_email") or ""),
        request=request,
    )
    response = TEMPLATES.TemplateResponse(
        request,
        "baja_completada.html",
        {"nombre": nombre},
    )
    response.delete_cookie("cotizat_organization_id")
    response.headers["Cache-Control"] = "no-store"
    return response
