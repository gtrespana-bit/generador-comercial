"""Rutas públicas: landing, legales, propuestas compartidas y descarga de archivos."""  # E4-001 — router por dominio

from fastapi import APIRouter, Form, Request

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

@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def home_publica(request: Request):
    """Página de inicio pública: la landing comercial es la puerta de entrada.

    Quien llega sin sesión ve qué ofrece el producto, por qué elegirlo y cómo
    empezar. El panel de trabajo vive en ``/inicio``, ya con sesión iniciada.
    """
    return TEMPLATES.TemplateResponse(request, "landing.html", {})


@router.get("/conocer", response_class=HTMLResponse, include_in_schema=False)
def landing_publica(request: Request):
    """Alias histórico de la landing, conservado para no romper enlaces."""
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


# ---------------------------------------------------------------------------
# Página de planes y métodos de pago
# ---------------------------------------------------------------------------

@router.get("/pago", response_class=HTMLResponse, include_in_schema=False)
def pagina_pago(request: Request):
    """Página pública de planes y métodos de pago.

    Acepta un `msg` en la query para poder explicar cómo se ha llegado aquí:
    quien acaba de crear una organización sin prueba disponible aterriza en
    esta pantalla y merece saber por qué, en vez de encontrarse una lista de
    precios sin contexto.
    """
    return TEMPLATES.TemplateResponse(
        request,
        "pago.html",
        {"msg": request.query_params.get("msg", "")[:300]},
    )


# ---------------------------------------------------------------------------
# Solicitud de demostración (formulario público)
# ---------------------------------------------------------------------------

@router.post("/demo", response_class=RedirectResponse, include_in_schema=False)
async def solicitar_demo(
    request: Request,
    nombre: str = Form(""),
    email: str = Form(""),
    empresa: str = Form(""),
    telefono: str = Form(""),
    presupuestos_mes: str = Form(""),
    mensaje: str = Form(""),
):
    """Recibe la solicitud de demo desde la landing y notifica al equipo.

    Sin autenticación: es un formulario público. Se envía un correo a
    soporte vía Resend con los datos. Si el correo no está configurado,
    la solicitud se pierde silenciosamente (el mailto: sigue como respaldo
    en la plantilla).
    """
    from ..services.email import (
        EmailNotConfigured,
        EmailValidationError,
        enviar_solicitud_demo_por_email,
    )

    nombre = str(nombre or "").strip()
    email = str(email or "").strip().lower()
    empresa = str(empresa or "").strip()
    telefono = str(telefono or "").strip()
    presupuestos_mes = str(presupuestos_mes or "").strip()
    mensaje = str(mensaje or "").strip()

    error = ""
    if not nombre:
        error = "Escribe tu nombre."
    elif not email:
        error = "Escribe tu correo electrónico."
    elif not empresa:
        error = "Escribe el nombre de tu empresa."

    if not error:
        try:
            enviar_solicitud_demo_por_email(
                nombre=nombre,
                email=email,
                empresa=empresa,
                telefono=telefono,
                presupuestos_mes=presupuestos_mes,
                mensaje=mensaje,
            )
        except (EmailNotConfigured, EmailValidationError) as exc:
            error = str(exc)
        except Exception:
            logger = logging.getLogger("cotizat.publico")
            logger.exception("Error al enviar solicitud de demo.")
            error = "Ocurrió un error al enviar tu solicitud. Intenta de nuevo o escríbenos directamente."

    if error:
        return RedirectResponse(
            f"/?demo_error={quote(error)}#demo",
            status_code=303,
        )

    return RedirectResponse(
        f"/?demo_enviado={quote(nombre)}#demo",
        status_code=303,
    )
