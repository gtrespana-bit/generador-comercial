"""Rutas públicas: landing, legales, propuestas compartidas y descarga de archivos."""  # E4-001 — router por dominio

from fastapi import APIRouter

from . import common
from .common import *  # noqa: F401,F403  (re-exporta modelos, servicios y utilidades)

router = APIRouter()

@router.get("/archivos/{object_key:path}")
def descargar_archivo_privado(
    object_key: str,
    download: int = 0,
    db: Session = Depends(get_db),
):
    """Proxy privado: autoriza por membresía/tenant antes de leer el objeto."""
    organizacion_id = int(db.info.get("organizacion_id") or 0)
    try:
        key = validate_tenant_object_key(object_key, organizacion_id)
    except StorageError:
        return Response(status_code=404)
    metadata = (
        db.query(ArchivoAlmacenado)
        .filter(ArchivoAlmacenado.object_key == key)
        .first()
    )
    if metadata is None or metadata.categoria == "manifiestos-importacion":
        return Response(status_code=404)
    backend = common.get_storage_backend()
    try:
        contenido = backend.read(key)
    except StorageError:
        return Response(status_code=404)
    nombre = Path(metadata.nombre_original or "archivo").name.replace('"', "")
    disposicion = "attachment" if download else "inline"
    headers = {
        "Cache-Control": "private, max-age=300",
        "Content-Disposition": f"{disposicion}; filename*=UTF-8''{quote(nombre, safe='')}",
        "X-Content-Type-Options": "nosniff",
        "Content-Security-Policy": "sandbox",
        "Cross-Origin-Resource-Policy": "same-origin",
    }
    return Response(
        contenido,
        media_type=metadata.content_type or "application/octet-stream",
        headers=headers,
    )


@router.get("/archivos-legado/{legacy_path:path}")
def descargar_archivo_legado_privado(
    legacy_path: str,
    download: int = 0,
    db: Session = Depends(get_db),
):
    """Compatibilidad web autorizada para referencias locales anteriores."""
    clean = str(legacy_path or "").strip().replace("\\", "/").lstrip("/")
    path = (UPLOADS_DIR / clean).resolve()
    try:
        invalido = (
            not clean
            or "//" in clean
            or ".." in clean.split("/")
            or UPLOADS_DIR.resolve() not in path.parents
            or not path.is_file()
            or path.stat().st_size > 12 * 1024 * 1024
        )
    except OSError:
        invalido = True
    if invalido:
        return Response(status_code=404)
    referencias = {f"uploads/{clean}", f"static/uploads/{clean}", clean}
    if not any(_archivo_referenciado(db, referencia) for referencia in referencias):
        return Response(status_code=404)
    try:
        contenido = path.read_bytes()
    except OSError:
        return Response(status_code=404)
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    disposicion = "attachment" if download else "inline"
    return Response(
        contenido,
        media_type=mime,
        headers={
            "Cache-Control": "private, max-age=300",
            "Content-Disposition": f"{disposicion}; filename*=UTF-8''{quote(path.name, safe='')}",
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "sandbox",
            "Cross-Origin-Resource-Policy": "same-origin",
        },
    )


# ---------------------------------------------------------------------------
# Páginas públicas: landing y legales (E1-018/019/020/056)
# ---------------------------------------------------------------------------
# No tocan datos de tenant ni sesión: solo renderizan contenido estático con
# la identidad del producto. Por eso no dependen de get_db y están declaradas
# como fronteras públicas en la auditoría de protección de rutas.

@router.get("/conocer", response_class=HTMLResponse, include_in_schema=False)
def landing_publica(request: Request):
    """Landing comercial: problema, resultado, público y llamada a demo."""
    return TEMPLATES.TemplateResponse(request, "landing.html", {})


_PAGINAS_LEGALES = {
    "terminos": "legal/terminos.html",
    "privacidad": "legal/privacidad.html",
    "soporte": "legal/soporte.html",
    "licencias": "legal/licencias.html",
    "preguntas": "legal/preguntas.html",
}


@router.get("/legal/{pagina}", response_class=HTMLResponse, include_in_schema=False)
def pagina_legal(pagina: str, request: Request):
    plantilla = _PAGINAS_LEGALES.get(pagina)
    if plantilla is None:
        return Response("Página no encontrada.", status_code=404)
    return TEMPLATES.TemplateResponse(request, plantilla, {})
