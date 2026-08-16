"""CotizaT — aplicación local de presupuestos de obra (FastAPI).

Ejecutar con:  python run.py   (o: uvicorn app.main:app)
"""
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import quote
import base64
import csv
import io
import json
import logging
import math
import mimetypes
import os
import re
import shutil
import traceback
import unicodedata
import uuid
import zipfile

log = logging.getLogger("cotizat")

from fastapi import Depends, FastAPI, Form, Request, UploadFile  # noqa: F401 (type hints)
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import UploadFile as UploadFileStarlette
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import or_
from sqlalchemy.orm import Session
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .branding import LEGAL_ENTITY, PRODUCT_NAME, SUPPORT_EMAIL, VALUE_PROPOSITION
from .security import AuthRateLimitMiddleware, WebSecurityMiddleware
from .database import (
    BACKUPS_DIR,
    BASE_DIR,
    DATA_DIR,
    DATABASE_IS_SQLITE,
    DB_PATH,
    PRIVATE_STORAGE_DIR,
    UPLOADS_DIR,
    copia_seguridad_sqlite,
    es_base_valida,
    establecer_contexto_organizacion,
    get_authenticated_db,
    get_db,
    get_operator_db,
    init_db,
    restaurar_base,
)
from .auth import (
    ACCESS_COOKIE,
    ORGANIZATION_COOKIE,
    AuthError,
    AuthenticationRequired,
    AuthNotConfigured,
    InvalidCredentials,
    OrganizationAccessDenied,
    OrganizationRequired,
    RefreshedAuthCookieMiddleware,
    SupabaseAuthClient,
    SupabaseAuthSettings,
    clear_auth_cookies,
    password_reset_redirect_url,
    public_app_url,
    set_auth_cookies,
)
from .models import (
    ESTADOS,
    ORIGENES_LICENCIA,
    ORIGENES_LICENCIA_ETIQUETA,
    ArchivoAlmacenado,
    Capitulo,
    Cliente,
    Configuracion,
    Factura,
    FacturaCapitulo,
    FacturaItem,
    InvitacionOrganizacion,
    Licencia,
    LicenciaSuspendidaError,
    Medicion,
    Membresia,
    NotaSeguimiento,
    Organizacion,
    Partida,
    Plantilla,
    RecetaEstancia,
    Presupuesto,
    Recurso,
    PresupuestoItem,
    PresupuestoVersion,
    Proyecto,
    Usuario,
    CambioAlcance,
    CambioAlcanceItem,
    CategoriaPartida,
    Pago,
    PermisoOrganizacionError,
    AnexoPresupuesto,
    BorradorPresupuesto,
    DescomposicionPartida,
    DescomposicionFila,
    PresupuestoItemProducto,
    Producto,
    asegurar_config,
    crear_organizacion_con_propietario,
    marcar_vencidos,
    membresias_activas,
    proximo_numero,
    proximo_numero_factura,
)
from .services import pdf as pdf_service
from .services.analisis import analizar_catalogo_partidas
from .services.contrato import generar_contrato_pdf
from .services.tiempos import calcular_tiempos_presupuesto, horas_por_unidad_descompuesto
from .services.versions import ESTADOS_CONGELABLES, crear_version, leer_snapshot
from .services.onboarding import (
    ErrorOnboarding,
    completar_onboarding,
    estado_recorrido_inicial,
)
from .services.licencias import (
    DURACIONES,
    GestionLicenciaError,
    cancelar_licencia,
    crear_licencia,
    enviar_avisos_vencimiento,
    exigencia_licencia_activada,
    resumen_organizaciones,
    totales,
)
from .services.recibo_licencia import generar_recibo_licencia_pdf, numero_recibo
from .services.invitations import (
    GestionEquipoError,
    aceptar_invitacion,
    aceptar_invitacion_pendiente,
    actualizar_membresia,
    crear_invitacion,
    exigir_gestor,
    invitaciones_pendientes_para,
    revocar_invitacion,
)
from .services.email import (
    EmailNotConfigured,
    EmailSendError,
    enviar_invitacion_por_email,
)
from .services.importer import (
    ErrorImportacion,
    ETIQUETAS_CAMPOS,
    MAX_FILAS,
    analizar_cype_xlsx,
    analizar_matriz,
    categoria_coste_cype,
    es_formato_cype_xlsx,
    leer_csv,
    leer_texto,
    leer_xlsx,
    normalizar,
    numero_local,
    posiciones_columnas_cype,
    recalcular_descompuesto_cype,
    texto_celda,
    validar_filas,
)
from .services.instalacion_sqlite import (
    ErrorInstalacion,
    LIMITE_BYTES as LIMITE_INSTALACION_BYTES,
    analizar_instalacion,
    importar_instalacion,
)
from .utils import SIMBOLOS, fmt_fecha, fmt_monto, fmt_num, fmt_cantidad
from .storage import (
    StorageError,
    copy_object,
    delete_object,
    file_url,
    get_storage_backend,
    object_key_from_reference,
    read_reference,
    save_object,
    storage_reference,
    validate_tenant_object_key,
)

TEMPLATES = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))
TEMPLATES.env.filters["money"] = fmt_monto
TEMPLATES.env.filters["num"] = fmt_num
TEMPLATES.env.filters["cant"] = fmt_cantidad
TEMPLATES.env.filters["fecha"] = fmt_fecha
TEMPLATES.env.filters["archivo_url"] = file_url
TEMPLATES.env.globals.update(
    product_name=PRODUCT_NAME,
    value_proposition=VALUE_PROPOSITION,
    database_is_sqlite=DATABASE_IS_SQLITE,
    titular_legal=LEGAL_ENTITY,
    email_soporte=SUPPORT_EMAIL,
)


def whatsapp_url(telefono, texto) -> str:
    """Enlace wa.me con mensaje predefinido; vacío si no hay teléfono."""
    digits = "".join(ch for ch in str(telefono or "") if ch.isdigit())
    if not digits:
        return ""
    return f"https://wa.me/{digits}?text={quote(str(texto))}"


TEMPLATES.env.filters["whatsapp"] = whatsapp_url

UPLOADS = UPLOADS_DIR
# Los Excel originales se guardan bajo uploads (consultables/descargables); el
# JSON intermedio del asistente queda fuera de estáticos hasta confirmarse.
IMPORTS_DIR = DATA_DIR / "imports_cype"
EXT_IMG = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
EXT_FICHA_TECNICA = {".pdf"}


def _backup_automatico():
    """Copia semanal del archivo SQLite local; no se aplica a PostgreSQL."""
    if not DATABASE_IS_SQLITE:
        return
    try:
        backups = BACKUPS_DIR
        backups.mkdir(parents=True, exist_ok=True)
        limite = datetime.now().timestamp() - 7 * 86400
        if any(p.suffix == ".zip" and p.stat().st_mtime >= limite for p in backups.glob("auto_*.zip")):
            return
        tmp = backups / "tmp_auto.db"
        copia_seguridad_sqlite(tmp)
        nombre = backups / f"auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        with zipfile.ZipFile(nombre, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(tmp, "presupuestos.db")
            if UPLOADS_DIR.exists():
                for p in sorted(UPLOADS_DIR.rglob("*")):
                    if p.is_file():
                        z.write(p, (Path("uploads") / p.relative_to(UPLOADS_DIR)).as_posix())
            if PRIVATE_STORAGE_DIR.exists():
                for p in sorted(PRIVATE_STORAGE_DIR.rglob("*")):
                    if p.is_file():
                        z.write(p, (Path("private_storage") / p.relative_to(PRIVATE_STORAGE_DIR)).as_posix())
        tmp.unlink(missing_ok=True)
    except Exception:
        pass


@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        init_db()
    except Exception as exc:
        log.error("Fallo al inicializar la base de datos en lifespan: %s", exc)
    # Carpetas locales históricas. En PostgreSQL los archivos viven en el
    # backend privado (Supabase) y en despliegues de solo lectura crear estas
    # carpetas fallaría: se intentan únicamente en SQLite y un fallo no debe
    # impedir el arranque de la aplicación.
    if DATABASE_IS_SQLITE:
        try:
            (UPLOADS / "products").mkdir(parents=True, exist_ok=True)
            (UPLOADS / "signatures").mkdir(parents=True, exist_ok=True)
            (UPLOADS / "importaciones").mkdir(parents=True, exist_ok=True)
        except OSError:
            log.warning(
                "No se pudieron crear las carpetas de subidas en %s: "
                "sistema de archivos de solo lectura.",
                UPLOADS,
            )
    try:
        IMPORTS_DIR.mkdir(parents=True, exist_ok=True)
    except OSError:
        log.warning(
            "No se pudo crear %s: sistema de archivos de solo lectura.",
            IMPORTS_DIR,
        )
    _backup_automatico()
    yield


class FormulariosUTF8Middleware:
    """Corrige la codificación de formularios urlencoded.

    Starlette decodifica los cuerpos application/x-www-form-urlencoded con
    Latin-1, lo que corrompe los acentos UTF-8 que envía el navegador
    (p. ej. «María» -> «MarÃa»). Este middleware relee el cuerpo, lo
    decodifica como UTF-8 y lo re-codifica a Latin-1 para que el parser
    de Starlette lo reconstruya correctamente.
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope.get("method") in ("POST", "PUT", "PATCH"):
            headers = {
                k.decode("latin-1").lower(): v.decode("latin-1")
                for k, v in scope.get("headers", [])
            }
            if headers.get("content-type", "").startswith("application/x-www-form-urlencoded"):
                cuerpo = bytearray()
                more_body = True
                while more_body:
                    message = await receive()
                    cuerpo.extend(message.get("body", b""))
                    more_body = message.get("more_body", False)
                try:
                    texto = bytes(cuerpo).decode("utf-8")
                    cuerpo = bytearray(texto.encode("latin-1", errors="replace"))
                except UnicodeDecodeError:
                    pass  # el cuerpo ya era Latin-1: se deja igual
                cuerpo_final = bytes(cuerpo)
                enviado = {"ya": False}

                async def receive_utf8() -> Message:
                    if not enviado["ya"]:
                        enviado["ya"] = True
                        return {"type": "http.request", "body": cuerpo_final, "more_body": False}
                    return {"type": "http.request", "body": b"", "more_body": False}

                await self.app(scope, receive_utf8, send)
                return
        await self.app(scope, receive, send)


app = FastAPI(title=PRODUCT_NAME, lifespan=lifespan)
app.add_middleware(FormulariosUTF8Middleware)
app.add_middleware(RefreshedAuthCookieMiddleware)
app.add_middleware(
    AuthRateLimitMiddleware,
    trust_forwarded_for=os.environ.get("COTIZAT_TRUST_PROXY", "").strip().lower()
    in {"1", "true", "yes", "on"},
)
app.add_middleware(WebSecurityMiddleware, enforce_csrf=not DATABASE_IS_SQLITE)


def _respuesta_auth_json(request: Request) -> bool:
    accept = request.headers.get("accept", "")
    return (
        request.url.path.startswith("/api/")
        or "/api/" in request.url.path
        or "application/json" in accept
        or request.headers.get("content-type", "").startswith("application/json")
    )


@app.exception_handler(AuthenticationRequired)
async def _sesion_requerida(request: Request, exc: AuthenticationRequired):
    if _respuesta_auth_json(request):
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=401)
    siguiente = request.url.path
    if request.url.query:
        siguiente += "?" + request.url.query
    return RedirectResponse(f"/acceso?next={quote(siguiente)}", status_code=303)


@app.exception_handler(OrganizationRequired)
async def _organizacion_requerida(request: Request, exc: OrganizationRequired):
    if _respuesta_auth_json(request):
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=403)
    membresias = getattr(request.state, "membresias", [])
    destino = "/organizaciones" if membresias else "/organizaciones/nueva"
    return RedirectResponse(destino, status_code=303)


@app.exception_handler(OrganizationAccessDenied)
async def _organizacion_denegada(request: Request, exc: OrganizationAccessDenied):
    if _respuesta_auth_json(request):
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=403)
    return RedirectResponse(
        f"/organizaciones?error={quote(str(exc))}", status_code=303
    )


@app.exception_handler(AuthNotConfigured)
async def _auth_no_configurada(request: Request, exc: AuthNotConfigured):
    if _respuesta_auth_json(request):
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=503)
    return TEMPLATES.TemplateResponse(
        request,
        "auth/access.html",
        {"error": str(exc), "auth_configured": False, "next": ""},
        status_code=503,
    )


@app.exception_handler(PermisoOrganizacionError)
async def _permiso_organizacion_denegado(
    request: Request, exc: PermisoOrganizacionError
):
    if _respuesta_auth_json(request):
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=403)
    return TEMPLATES.TemplateResponse(
        request,
        "auth/forbidden.html",
        {"error": str(exc)},
        status_code=403,
    )


@app.exception_handler(GestionEquipoError)
async def _gestion_equipo_denegada(request: Request, exc: GestionEquipoError):
    if _respuesta_auth_json(request):
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=403)
    return TEMPLATES.TemplateResponse(
        request,
        "auth/forbidden.html",
        {"error": str(exc)},
        status_code=403,
    )


@app.exception_handler(StorageError)
async def _storage_no_disponible(request: Request, exc: StorageError):
    mensaje = "El almacenamiento privado no está disponible. Inténtalo de nuevo."
    if _respuesta_auth_json(request):
        return JSONResponse({"ok": False, "error": mensaje}, status_code=503)
    return HTMLResponse(
        f"<h1>Almacenamiento no disponible</h1><p>{mensaje}</p>",
        status_code=503,
    )


@app.exception_handler(AuthError)
async def _servicio_auth_no_disponible(request: Request, exc: AuthError):
    if _respuesta_auth_json(request):
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=503)
    return TEMPLATES.TemplateResponse(
        request,
        "auth/access.html",
        {"error": str(exc), "auth_configured": True, "next": ""},
        status_code=503,
    )


@app.exception_handler(LicenciaSuspendidaError)
async def _licencia_suspendida(request: Request, exc: LicenciaSuspendidaError):
    """Organización sin licencia vigente con el corte automático activo.

    Se muestra una pantalla propia y no un redirect: cualquier ruta de
    negocio (incluido `/organizaciones/seleccionar` posterior) debe llegar a
    este mensaje, nunca a una página normal medio rota.
    """
    if _respuesta_auth_json(request):
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=403)
    return TEMPLATES.TemplateResponse(
        request,
        "licencia_suspendida.html",
        {"error": str(exc)},
        status_code=403,
        headers={"Cache-Control": "no-store"},
    )

# SQLite conserva el montaje histórico. En PostgreSQL se bloquea antes del
# montaje general: ningún archivo de usuario puede eludir el proxy autorizado.
# En despliegues de solo lectura (p. ej. Vercel) crear el directorio puede
# fallar; en ese caso se omite el montaje y las rutas heredadas devuelven 404
# en lugar de impedir el arranque de la aplicación.
def _bloquear_upload_estatico_legado(_legacy_path: str) -> Response:
    return Response(status_code=404)

if DATABASE_IS_SQLITE:
    try:
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    except OSError:
        log.warning(
            "No se pudo crear %s: sistema de archivos de solo lectura. "
            "Las rutas /static/uploads devolverán 404.",
            UPLOADS_DIR,
        )
    if UPLOADS_DIR.is_dir():
        app.mount("/static/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")
    else:
        app.get("/static/uploads/{_legacy_path:path}", include_in_schema=False)(
            _bloquear_upload_estatico_legado
        )
else:
    app.get("/static/uploads/{_legacy_path:path}", include_in_schema=False)(
        _bloquear_upload_estatico_legado
    )
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "app" / "static")), name="static")


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> RedirectResponse:
    """Los navegadores piden /favicon.ico por defecto; sin esta ruta cada
    visita deja un 404 ruidoso en los logs del despliegue."""
    return RedirectResponse("/static/icono.png", status_code=307)


# ---------------------------------------------------------------------------
# Salud (sin autenticación; no exponen secretos ni datos de tenant)
# ---------------------------------------------------------------------------

_NO_CACHE = {
    "Cache-Control": "no-store, max-age=0",
    "Pragma": "no-cache",
}


@app.get("/healthz", include_in_schema=False)
def healthz() -> JSONResponse:
    """Liveness: el proceso responde. No depende de la base de datos."""
    from .health import liveness

    return JSONResponse(liveness().to_dict(), headers=_NO_CACHE)


@app.get("/readyz", include_in_schema=False)
def readyz() -> JSONResponse:
    """Readiness: configuración, base de datos y rol runtime están listos.

    Devuelve 503 si el despliegue no debe recibir tráfico (esquema
    desactualizado, rol runtime privilegiado, Auth/Storage sin configurar).
    No imprime secretos: los mensajes se sanean en ``app.health``.
    """
    from .health import run_readiness

    status = run_readiness()
    return JSONResponse(
        status.to_dict(),
        status_code=200 if status.ok else 503,
        headers=_NO_CACHE,
    )


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

@app.get("/archivos/{object_key:path}")
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
    backend = get_storage_backend()
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


@app.get("/archivos-legado/{legacy_path:path}")
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


def _config(db: Session) -> Configuracion:
    cfg = db.query(Configuracion).first()
    if cfg is None:
        asegurar_config(db)
        cfg = db.query(Configuracion).first()
    return cfg


def _tiempos_catalogo(db: Session, presupuesto: Presupuesto | None) -> dict:
    """Mapa partida_catalogo_id → tiempo_estimado_horas del catálogo.

    Se pasa al creador para que el indicador de tiempo estimado pueda usar
    las horas por unidad declaradas en la ficha técnica del catálogo cuando
    la partida no tiene descomposición con rendimientos de tiempo.
    Si el catálogo tiene desglose por rol (oficial/ayudante/equipo) se devuelve
    el dict completo, si no el float total.
    """
    if presupuesto is None:
        return {}
    ids = {
        p.partida_catalogo_id
        for cap in presupuesto.capitulos
        for p in cap.partidas
        if p.partida_catalogo_id
    }
    if not ids:
        return {}
    out = {}
    for c in db.query(Partida).filter(Partida.id.in_(ids)).all():
        # Prefer desglose si existe
        if getattr(c, "tiempo_oficial_horas", None) is not None or getattr(c, "tiempo_ayudante_horas", None) is not None or getattr(c, "tiempo_equipo_horas", None) is not None:
            total = c.tiempo_estimado_horas or 0
            ofi = getattr(c, "tiempo_oficial_horas", None) or 0
            ayu = getattr(c, "tiempo_ayudante_horas", None) or 0
            eq = getattr(c, "tiempo_equipo_horas", None) or 0
            if total == 0 and (ofi or ayu or eq):
                total = (ofi or 0) + (ayu or 0) + (eq or 0)
            if total:
                out[c.id] = {"total": total, "oficial": ofi or 0, "ayudante": ayu or 0, "equipos": eq or 0}
        elif c.tiempo_estimado_horas:
            out[c.id] = c.tiempo_estimado_horas
    return out


def _redirect(url: str, msg: str | None = None, error: str | None = None) -> RedirectResponse:
    if msg:
        url += ("&" if "?" in url else "?") + "msg=" + quote(msg)
    if error:
        url += ("&" if "?" in url else "?") + "error=" + quote(error)
    return RedirectResponse(url, status_code=303)


def _respuesta_pdf(buf, nombre: str, inline: int = 0) -> Response:
    """Envuelve un PDF generado en memoria en una Response con descarga."""
    dispo = "inline" if inline else "attachment"
    return Response(
        content=buf.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'{dispo}; filename="{nombre}"'},
    )


def _generar_pdf_seguro(generador, etiqueta: str):
    """Genera un PDF capturando cualquier error para devolver un mensaje
    legible (y con traza en el log) en lugar de un 500 mudo.

    Devuelve el BytesIO, o una Response de error si algo falla.
    """
    try:
        return generador()
    except Exception:
        log.error("Error generando %s:\n%s", etiqueta, traceback.format_exc())
        return HTMLResponse(
            "<!doctype html><html lang='es'><head><meta charset='utf-8'>"
            "<title>Error generando el PDF</title></head><body><main>"
            "<h2>No se pudo generar el PDF</h2>"
            "<p>Ocurrió un error al generar el documento. Mira el log de la aplicación "
            "(inicio.log o la consola) para ver el detalle, o prueba a actualizar la "
            "aplicación a la última versión.</p></main></body></html>",
            status_code=500,
        )


def _f(valor, defecto=0.0) -> float:
    """Convierte texto de formulario en float con formato local robusto.

    Acepta «12,50», «1.234,56» (formato venezolano/español), «1,234.56»
    (formato inglés) y «1234.56». Si ambos separadores aparecen, el último
    es el decimal; si solo hay coma, es el decimal. Un valor con separador
    de miles mal formado devuelve `defecto` en lugar de un número erróneo.
    """
    texto = str(valor or "").strip()
    if not texto:
        return defecto
    limpio = texto.replace(" ", "").replace("$", "").replace("Bs", "").replace("€", "")
    if "," in limpio and "." in limpio:
        if limpio.rfind(",") > limpio.rfind("."):
            limpio = limpio.replace(".", "").replace(",", ".")
        else:
            limpio = limpio.replace(",", "")
    elif "," in limpio:
        limpio = limpio.replace(",", ".")
    try:
        numero = float(limpio)
        return numero if math.isfinite(numero) else defecto
    except (TypeError, ValueError):
        return defecto


def _validar_alternativas(partidas):
    """Comprueba que un grupo de alternativas no tenga dos opciones activas."""
    activos = {}
    for partida in partidas:
        if partida.get("tipo_partida") != "alternative" or not partida.get("seleccionada"):
            continue
        grupo = partida.get("grupo_alternativa", "").strip()
        if not grupo:
            continue
        if grupo in activos:
            return f"El grupo de alternativa «{grupo}» tiene más de una opción seleccionada."
        activos[grupo] = True
    return ""


def _validar_condiciones_presupuesto(form, partidas):
    """Validación de servidor para evitar importes imposibles o NaN.

    Los atributos min/max del HTML no son una frontera de seguridad: cualquier
    cliente puede enviar un POST manualmente.
    """
    validez = _f(form.get("validez_dias"), 30)
    iva = _f(form.get("impuesto_pct"), 16.0)
    descuento = _f(form.get("descuento_pct"), 0.0)
    tasa = _f(form.get("tipo_cambio"), 0.0) if str(form.get("tipo_cambio", "")).strip() else 0.0
    if not (1 <= validez <= 3650):
        return "La validez debe estar entre 1 y 3650 días."
    if not (0 <= iva <= 100):
        return "El IVA debe estar entre 0 y 100 %."
    if not (0 <= descuento <= 100):
        return "El descuento debe estar entre 0 y 100 %."
    if tasa < 0:
        return "La tasa de cambio no puede ser negativa."
    for campo, etiqueta in (("gastos_indirectos_pct", "gastos indirectos"), ("imprevistos_pct", "imprevistos")):
        valor = _f(form.get(campo), 0)
        if not (0 <= valor <= 100):
            return f"Los {etiqueta} deben estar entre 0 y 100 %."
    for campo, etiqueta in (("transporte_monto", "transporte"), ("otros_cargos_monto", "otros cargos")):
        if _f(form.get(campo), 0) < 0:
            return f"El importe de {etiqueta} no puede ser negativo."
    for partida in partidas:
        if partida.get("precio", 0) < 0 or partida.get("cantidad", 0) < 0:
            return "Los precios y las cantidades no pueden ser negativos."
        if any(cantidad < 0 for _, cantidad in partida.get("mediciones", [])):
            return "Las mediciones no pueden ser negativas."
    return ""


def _categoria_archivo(prefijo: str) -> str:
    raiz = str(prefijo or "").replace("\\", "/").strip("/").split("/", 1)[0]
    return {
        "logo": "logos", "products": "productos", "projects": "fotos-proyecto",
        "partidas": "partidas", "signatures": "firmas",
    }.get(raiz, "anexos")


async def _guardar_imagen(archivo: UploadFile, prefijo: str, db: Session) -> str:
    """Valida una imagen y la guarda mediante el backend privado configurado."""
    nombre = (archivo.filename or "").strip()
    if not nombre:
        return ""
    ext = Path(nombre).suffix.lower()
    if ext not in EXT_IMG:
        return ""
    datos = await archivo.read()
    if not datos or len(datos) > 12 * 1024 * 1024:
        return ""
    try:
        from PIL import Image as PILImage
        with PILImage.open(io.BytesIO(datos)) as imagen:
            formato = str(imagen.format or "").upper()
            ancho, alto = imagen.size
            if ancho <= 0 or alto <= 0 or ancho * alto > 40_000_000:
                return ""
            imagen.verify()
    except Exception:
        return ""
    mime = {
        "PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp",
        "GIF": "image/gif",
    }.get(formato)
    if mime is None:
        return ""
    return save_object(
        db, datos, _categoria_archivo(prefijo), nombre, mime, prefix=prefijo
    ).reference


async def _guardar_ficha_tecnica(
    archivo: UploadFile, prefijo: str, db: Session
) -> str:
    nombre = (archivo.filename or "").strip()
    if not nombre or Path(nombre).suffix.lower() not in EXT_FICHA_TECNICA:
        return ""
    datos = await archivo.read()
    if not datos or len(datos) > 12 * 1024 * 1024 or not datos.startswith(b"%PDF-"):
        return ""
    return save_object(
        db, datos, "fichas-tecnicas", nombre, "application/pdf", prefix=prefijo
    ).reference


def _rutas_galeria(valor, portada: str = "") -> list[str]:
    """Normaliza una galería y acepta referencias privadas o legado local."""
    try:
        rutas = json.loads(valor or "[]") if isinstance(valor, str) else list(valor or [])
    except (TypeError, ValueError):
        rutas = []
    resultado = []
    for ruta in ([portada] if portada else []) + rutas:
        if (
            isinstance(ruta, str)
            and (ruta.startswith("storage://") or ruta.startswith("uploads/"))
            and ruta not in resultado
        ):
            resultado.append(ruta)
    return resultado


def _entero_opcional(valor, minimo=0):
    try:
        numero = int(float(str(valor).replace(",", ".").strip()))
        return numero if numero >= minimo else None
    except (TypeError, ValueError):
        return None


def _archivo_referenciado(db: Session, referencia: str) -> bool:
    """Evita borrar un objeto inmutable que todavía comparte otro registro."""
    if not referencia:
        return False
    campos = (
        (Configuracion, Configuracion.logo),
        (Presupuesto, Presupuesto.foto_proyecto),
        (Presupuesto, Presupuesto.firma_cliente),
        (PresupuestoItem, PresupuestoItem.producto_imagen),
        (PresupuestoItemProducto, PresupuestoItemProducto.imagen),
        (Partida, Partida.imagen),
        (Producto, Producto.imagen),
        (Producto, Producto.ficha_tecnica),
        (AnexoPresupuesto, AnexoPresupuesto.archivo),
        (DescomposicionPartida, DescomposicionPartida.archivo_origen),
    )
    for modelo, campo in campos:
        if db.query(modelo).filter(campo == referencia).first() is not None:
            return True
    for modelo, campo in (
        (Producto, Producto.imagenes),
        (PresupuestoVersion, PresupuestoVersion.datos_snapshot),
        (BorradorPresupuesto, BorradorPresupuesto.datos),
        (Plantilla, Plantilla.datos),
    ):
        if db.query(modelo).filter(campo.contains(referencia)).first() is not None:
            return True
    return False


def _normalizar_referencia_imagen(db: Session, referencia: object) -> str:
    """Acepta solo una imagen ya autorizada para la organización activa."""
    value = str(referencia or "").strip()
    if not value:
        return ""
    try:
        key = object_key_from_reference(value)
    except StorageError:
        return ""
    if key is not None:
        try:
            validate_tenant_object_key(key, int(db.info.get("organizacion_id") or 0))
        except StorageError:
            return ""
        metadata = db.query(ArchivoAlmacenado).filter(ArchivoAlmacenado.object_key == key).first()
        if metadata is None or not metadata.content_type.startswith("image/"):
            return ""
        return storage_reference(key)
    clean = value.lstrip("/")
    if clean.startswith("static/"):
        clean = clean[7:]
    if clean.startswith("uploads/"):
        clean = clean[8:]
    if Path(clean).suffix.lower() not in EXT_IMG:
        return ""
    path = (UPLOADS_DIR / clean).resolve()
    if UPLOADS_DIR.resolve() not in path.parents or not path.is_file():
        return ""
    legacy = f"uploads/{clean}"
    if DATABASE_IS_SQLITE or _archivo_referenciado(db, legacy) or _archivo_referenciado(db, clean):
        return legacy
    return ""


def _borrar_imagen(ruta_rel: str, db: Session):
    if not ruta_rel:
        return
    db.flush()
    if not _archivo_referenciado(db, ruta_rel):
        delete_object(db, ruta_rel)


def _copiar_imagen(ruta_rel: str, prefijo: str, db: Session) -> str:
    if not ruta_rel:
        return ""
    return copy_object(db, ruta_rel, _categoria_archivo(prefijo), prefijo)


def _guardar_firma(data_url: str, db: Session):
    """Valida y guarda una firma PNG dibujada en el navegador."""
    try:
        if not isinstance(data_url, str) or not data_url.startswith("data:image/png;base64,"):
            return ""
        datos = base64.b64decode(data_url.split(",", 1)[1], validate=True)
        if not datos or len(datos) > 2 * 1024 * 1024:
            return ""
        from PIL import Image as PILImage
        with PILImage.open(io.BytesIO(datos)) as imagen:
            if str(imagen.format or "").upper() != "PNG":
                return ""
            ancho, alto = imagen.size
            if ancho <= 0 or alto <= 0 or ancho * alto > 4_000_000:
                return ""
            imagen.verify()
    except Exception:
        return ""
    return save_object(
        db, datos, "firmas", "firma.png", "image/png", prefix="firma"
    ).reference

def _csv_response(filas: list, nombre_archivo: str) -> Response:
    """Respuesta CSV con separador «;» y BOM UTF-8 (Excel en español)."""
    buf = io.StringIO()
    buf.write("\ufeff")
    w = csv.writer(buf, delimiter=";")
    for fila in filas:
        w.writerow(fila)
    return Response(
        content=buf.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{nombre_archivo}"'},
    )


def _registrar_usos(db: Session, partidas: list, nombres_previos: set | None = None):
    """Registra uso sin inflar el contador al volver a guardar un presupuesto."""
    previos = set(nombres_previos or [])
    for pd in partidas:
        nombre = str(pd.get("nombre", "")).strip()
        if not nombre or nombre in previos:
            continue
        part = db.query(Partida).filter(Partida.nombre == nombre).first()
        if part:
            part.usos = (part.usos or 0) + 1
            part.ultimo_uso = datetime.utcnow()
            previos.add(nombre)


def _registrar_usos_productos(db: Session, partidas: list, nombres_previos: set | None = None):
    """Equivalente para productos, usado al guardar el presupuesto real."""
    previos = set(nombres_previos or [])
    for pd in partidas:
        nombre = str(pd.get("prod_nombre", "")).strip()
        if not nombre or nombre in previos:
            continue
        producto = db.query(Producto).filter(Producto.nombre == nombre).first()
        if producto:
            producto.usos = (producto.usos or 0) + 1
            producto.ultimo_uso = datetime.utcnow()
            previos.add(nombre)


def _estado_valido(estado: str) -> bool:
    return estado in ESTADOS


def _categorias(db: Session) -> list[str]:
    """Categorías existentes (partidas + productos) para los datalists."""
    cats = set()
    for (c,) in db.query(Partida.categoria).all():
        if c:
            cats.add(c)
    for (c,) in db.query(Producto.categoria).all():
        if c:
            cats.add(c)
    return sorted(cats)


def _vincular_partidas_catalogo(db: Session, presupuesto: Presupuesto):
    """Completa el vínculo con la partida maestra tras guardar el catálogo.

    Las líneas creadas a mano en un presupuesto se convierten en partidas del
    catálogo durante el guardado, pero en ese momento todavía no tenían id de
    catálogo. Esta pasada lo asigna por nombre (único en el catálogo) sin
    modificar el precio propio de la línea.
    """
    nombres = {p.nombre for cap in presupuesto.capitulos for p in cap.partidas if not p.partida_catalogo_id}
    if not nombres:
        return
    maestras = {p.nombre: p for p in db.query(Partida).filter(Partida.nombre.in_(nombres)).all()}
    for cap in presupuesto.capitulos:
        for item in cap.partidas:
            if item.partida_catalogo_id:
                continue
            maestra = maestras.get(item.nombre)
            if maestra:
                item.partida_catalogo_id = maestra.id


def _guardar_en_catalogos(db: Session, partidas: list, imagenes_guardadas: dict):
    """Guarda automáticamente en los catálogos las partidas y los productos
    nuevos escritos en el formulario (para poder reutilizarlos a futuro).

    - Partida nueva (nombre que no existe en el catálogo) → se crea con su
      descripción, unidad, precio y categoría.
    - Producto nuevo (nombre que no existe en la base de datos de productos)
      → se crea con su precio, unidad, categoría e imagen.
    Los que ya existen no se modifican.
    """
    # La sesión trabaja sin autoflush: recordar las altas de este mismo
    # formulario evita chocar con la restricción UNIQUE si una partida o un
    # producto se repite en dos líneas antes del primer commit.
    partidas_nuevas = set()
    productos_nuevos = set()
    for i, pd in enumerate(partidas):
        nombre = str(pd.get("nombre", "")).strip()
        if (nombre and nombre not in partidas_nuevas
                and not db.query(Partida).filter(Partida.nombre == nombre).first()):
            # El precio de la línea incluye el producto asociado (base +
            # producto). En el catálogo se guarda SOLO la base: el producto
            # es un catálogo aparte y si se guardara el total, al reutilizar
            # la partida y añadir el producto se sumaría dos veces.
            precio_linea = pd.get("precio", 0.0) or 0.0
            precio_producto = pd.get("prod_precio") or 0.0
            precio_base = max(0.0, float(precio_linea) - float(precio_producto))
            db.add(Partida(
                nombre=nombre,
                descripcion=str(pd.get("descripcion", "")).strip(),
                precio_unitario=precio_base,
                unidad=str(pd.get("unidad", "ud")).strip() or "ud",
                categoria=str(pd.get("categoria", "General")).strip() or "General",
                codigo_interno=str(pd.get("codigo") or pd.get("codigo_interno") or "").strip(),
                coste_materiales=pd.get("coste_materiales", 0.0) or 0.0,
                coste_mano_obra=pd.get("coste_mano_obra", 0.0) or 0.0,
                coste_complementarios=pd.get("coste_complementarios", 0.0) or 0.0,
                coste_otros=pd.get("coste_otros", 0.0) or 0.0,
                desperdicio_recomendado_pct=pd.get("desperdicio_pct", 0.0) or 0.0,
            ))
            partidas_nuevas.add(nombre)

        prod_nombre = str(pd.get("prod_nombre", "")).strip()
        if (prod_nombre and prod_nombre not in productos_nuevos
                and not db.query(Producto).filter(Producto.nombre == prod_nombre).first()):
            imagen = imagenes_guardadas.get(i) or str(pd.get("prod_imagen_actual", "")).strip()
            db.add(Producto(
                nombre=prod_nombre,
                descripcion="",
                precio_unitario=pd.get("prod_precio") or 0.0,
                precio_compra=pd.get("prod_coste"),
                unidad=str(pd.get("prod_unidad", "")).strip() or "ud",
                categoria=str(pd.get("prod_categoria", "General")).strip() or "General",
                imagen=imagen,
            ))
            productos_nuevos.add(prod_nombre)


# ---------------------------------------------------------------------------
# Acceso web y selección de organización
# ---------------------------------------------------------------------------

def _next_seguro(valor: object, defecto: str = "/") -> str:
    destino = str(valor or "").strip()
    if (
        not destino.startswith("/")
        or destino.startswith("//")
        or "\\" in destino
        or any(ord(caracter) < 32 for caracter in destino)
    ):
        return defecto
    return destino[:1000]


def _slug_organizacion(nombre: str) -> str:
    normalizado = unicodedata.normalize("NFKD", nombre)
    ascii_texto = "".join(c for c in normalizado if not unicodedata.combining(c))
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_texto.lower()).strip("-")
    return slug[:100] or "organizacion"


def _set_organization_cookie(response: Response, organizacion_id: int) -> None:
    try:
        secure = SupabaseAuthSettings.from_environment().cookie_secure
    except AuthNotConfigured:
        secure = True
    response.set_cookie(
        ORGANIZATION_COOKIE,
        str(organizacion_id),
        max_age=60 * 60 * 24 * 30,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
    )


@app.get("/acceso", response_class=HTMLResponse)
def acceso(request: Request, next: str = ""):
    error = request.query_params.get("error", "")
    mensaje = request.query_params.get("msg", "")
    try:
        SupabaseAuthSettings.from_environment()
        configurado = True
    except AuthNotConfigured as exc:
        configurado = False
        error = error or str(exc)
    return TEMPLATES.TemplateResponse(
        request,
        "auth/access.html",
        {
            "error": error,
            "msg": mensaje,
            "auth_configured": configurado,
            "next": _next_seguro(next),
        },
    )


@app.get("/recuperar-acceso", response_class=HTMLResponse)
def recuperar_acceso_form(request: Request):
    return TEMPLATES.TemplateResponse(
        request,
        "auth/recover.html",
        {
            "error": request.query_params.get("error", ""),
            "msg": request.query_params.get("msg", ""),
        },
    )


@app.post("/recuperar-acceso")
async def solicitar_recuperacion(request: Request):
    form = await request.form()
    email = str(form.get("email") or "").strip()
    mensaje = "Si la cuenta existe, Supabase enviará un enlace para restablecer la contraseña."
    try:
        settings = SupabaseAuthSettings.from_environment()
        redirect_to = password_reset_redirect_url()
        await run_in_threadpool(
            SupabaseAuthClient(settings).request_password_reset,
            email,
            redirect_to,
        )
    except InvalidCredentials:
        # Respuesta deliberadamente indistinguible para no enumerar cuentas.
        pass
    except AuthError as exc:
        return _redirect("/recuperar-acceso", error=str(exc))
    return _redirect("/recuperar-acceso", msg=mensaje)


@app.get("/restablecer-clave", response_class=HTMLResponse)
def restablecer_clave_form(request: Request):
    return TEMPLATES.TemplateResponse(
        request,
        "auth/reset_password.html",
        {"error": request.query_params.get("error", ""), "recovery_token": ""},
    )


@app.post("/restablecer-clave")
async def restablecer_clave(request: Request):
    form = await request.form()
    token = str(form.get("recovery_token") or "").strip()
    password = str(form.get("password") or "")
    confirmation = str(form.get("password_confirmation") or "")
    if password != confirmation:
        return TEMPLATES.TemplateResponse(
            request,
            "auth/reset_password.html",
            {"error": "Las contraseñas no coinciden.", "recovery_token": token},
            status_code=400,
        )
    try:
        settings = SupabaseAuthSettings.from_environment()
        client = SupabaseAuthClient(settings)
        # Verifica primero que el token todavía identifica a un usuario.
        await run_in_threadpool(client.get_user, token)
        await run_in_threadpool(client.update_password, token, password)
    except AuthError:
        return TEMPLATES.TemplateResponse(
            request,
            "auth/reset_password.html",
            {
                "error": "El enlace no es válido o ha caducado. Solicita uno nuevo.",
                "recovery_token": "",
            },
            status_code=400,
        )
    response = RedirectResponse(
        "/acceso?msg=" + quote("Contraseña actualizada. Ya puedes iniciar sesión."),
        status_code=303,
    )
    clear_auth_cookies(response, settings.cookie_secure, request)
    return response


@app.post("/acceso")
async def iniciar_sesion(request: Request):
    form = await request.form()
    destino = _next_seguro(form.get("next"))
    try:
        settings = SupabaseAuthSettings.from_environment()
        tokens = await run_in_threadpool(
            SupabaseAuthClient(settings).sign_in,
            str(form.get("email") or ""),
            str(form.get("password") or ""),
        )
    except AuthError as exc:
        return _redirect(
            f"/acceso?next={quote(destino)}",
            error=str(exc),
        )
    response = RedirectResponse(destino, status_code=303)
    set_auth_cookies(response, tokens, settings.cookie_secure)
    return response


@app.post("/registro")
async def registrar_cuenta(request: Request):
    form = await request.form()
    destino = _next_seguro(form.get("next"), "/organizaciones/nueva")
    password = str(form.get("password") or "")
    password_confirmation = str(form.get("password_confirmation") or "")
    if password != password_confirmation:
        return _redirect("/acceso", error="Las contraseñas no coinciden.")
    try:
        settings = SupabaseAuthSettings.from_environment()
        result = await run_in_threadpool(
            SupabaseAuthClient(settings).sign_up,
            str(form.get("email") or ""),
            password,
            str(form.get("nombre") or ""),
            public_app_url("/acceso"),
        )
    except AuthError as exc:
        return _redirect("/acceso", error=str(exc))
    if result.tokens is None:
        # Mensaje único tanto para el alta nueva como para el email ya
        # registrado: GoTrue oculta a propósito cuál de los dos casos es, y
        # diferenciarlos aquí permitiría enumerar qué emails tienen cuenta.
        return _redirect(
            "/acceso",
            msg=(
                "Revisa tu email y abre el enlace de confirmación para activar la "
                "cuenta. Si ya tenías una cuenta con ese email, inicia sesión con "
                "tu contraseña o usa «Olvidé mi contraseña»."
            ),
        )
    response = RedirectResponse(destino, status_code=303)
    set_auth_cookies(response, result.tokens, settings.cookie_secure)
    return response


@app.post("/salir")
async def cerrar_sesion(request: Request):
    """Cierra la sesión local y revoca el refresh token en Supabase.

    Borrar las cookies basta para el navegador, pero el refresh token seguiría
    siendo válido en GoTrue. La revocación es best-effort: si Supabase no
    responde, la sesión local se cierra igualmente y nunca se deja al usuario
    dentro por un fallo del proveedor.
    """
    response = RedirectResponse("/acceso", status_code=303)
    secure = True
    try:
        settings = SupabaseAuthSettings.from_environment()
        secure = settings.cookie_secure
        access_token = request.cookies.get(ACCESS_COOKIE, "")
        if access_token:
            await run_in_threadpool(
                SupabaseAuthClient(settings).sign_out, access_token
            )
    except AuthNotConfigured:
        pass
    except AuthError:
        log.info("No se pudo revocar la sesión en Supabase; se cierra localmente.")
    clear_auth_cookies(response, secure, request)
    return response


# ---------------------------------------------------------------------------
# Panel de la cuenta (perfil, contraseña y sesión)
# ---------------------------------------------------------------------------

def _render_cuenta(
    request: Request,
    db: Session,
    *,
    msg: str = "",
    error: str = "",
    status_code: int = 200,
):
    """Pinta el panel con el perfil local y las membresías del usuario.

    ``get_authenticated_db`` no resuelve organización activa (el panel debe
    abrirse incluso sin haber elegido empresa), así que la selección se deduce
    aquí de la cookie y se contrasta con las membresías reales: una cookie
    manipulada nunca marca como activa una empresa ajena.
    """
    usuario = db.get(Usuario, db.info["usuario_id"])
    membresias = membresias_activas(db, usuario.id)
    cookie = request.cookies.get(ORGANIZATION_COOKIE, "").strip()
    try:
        seleccionada = int(cookie) if cookie else None
    except ValueError:
        seleccionada = None
    if seleccionada not in {m.organizacion_id for m in membresias}:
        seleccionada = membresias[0].organizacion_id if len(membresias) == 1 else None
    return TEMPLATES.TemplateResponse(
        request,
        "auth/account.html",
        {
            "usuario": usuario,
            "membresias": membresias,
            "organizacion_activa_id": seleccionada,
            "email_verificado": bool(usuario.email_verificado_at),
            "msg": msg,
            "error": error,
        },
        status_code=status_code,
    )


@app.get("/cuenta", response_class=HTMLResponse)
def ver_cuenta(request: Request, db: Session = Depends(get_authenticated_db)):
    if DATABASE_IS_SQLITE:
        return _redirect("/configuracion")
    return _render_cuenta(
        request,
        db,
        msg=request.query_params.get("msg", ""),
        error=request.query_params.get("error", ""),
    )


@app.post("/cuenta/perfil")
async def actualizar_perfil_cuenta(
    request: Request,
    db: Session = Depends(get_authenticated_db),
):
    """Guarda el nombre visible en el perfil local y en Supabase.

    El email no se edita aquí: cambiarlo exige reverificación en Supabase y
    rehacer el vínculo con `usuarios.auth_user_id`, lo que rompería membresías
    e invitaciones pendientes emitidas contra el email anterior.
    """
    if DATABASE_IS_SQLITE:
        return _redirect("/configuracion")
    form = await request.form()
    nombre = str(form.get("nombre") or "").strip()[:200]
    if len(nombre) < 2:
        return _render_cuenta(
            request, db, error="Escribe un nombre de al menos 2 caracteres.",
            status_code=400,
        )
    usuario = db.get(Usuario, db.info["usuario_id"])
    usuario.nombre = nombre
    db.commit()
    try:
        settings = SupabaseAuthSettings.from_environment()
        access_token = request.cookies.get(ACCESS_COOKIE, "")
        if access_token:
            await run_in_threadpool(
                SupabaseAuthClient(settings).update_profile, access_token, nombre
            )
    except AuthError:
        # El perfil local ya quedó guardado: no se revierte por un fallo del
        # metadato remoto, que solo alimenta el nombre mostrado.
        log.info("No se pudo sincronizar el nombre con Supabase.")
    return _redirect("/cuenta", msg="Perfil actualizado.")


@app.post("/cuenta/clave")
async def cambiar_clave_cuenta(
    request: Request,
    db: Session = Depends(get_authenticated_db),
):
    """Cambia la contraseña exigiendo la actual y cierra la sesión."""
    if DATABASE_IS_SQLITE:
        return _redirect("/configuracion")
    form = await request.form()
    actual = str(form.get("password_actual") or "")
    nueva = str(form.get("password") or "")
    confirmacion = str(form.get("password_confirmation") or "")
    if nueva != confirmacion:
        return _render_cuenta(
            request, db, error="Las contraseñas nuevas no coinciden.", status_code=400
        )
    usuario = db.get(Usuario, db.info["usuario_id"])
    try:
        settings = SupabaseAuthSettings.from_environment()
        access_token = request.cookies.get(ACCESS_COOKIE, "")
        await run_in_threadpool(
            SupabaseAuthClient(settings).change_password,
            access_token,
            usuario.email,
            actual,
            nueva,
        )
    except InvalidCredentials as exc:
        return _render_cuenta(request, db, error=str(exc), status_code=400)
    except AuthError as exc:
        return _render_cuenta(request, db, error=str(exc), status_code=503)
    # Cambiar la contraseña invalida las sesiones anteriores: se fuerza un
    # inicio de sesión nuevo en lugar de conservar cookies ya obsoletas.
    response = RedirectResponse(
        "/acceso?msg=" + quote("Contraseña actualizada. Inicia sesión de nuevo."),
        status_code=303,
    )
    clear_auth_cookies(response, settings.cookie_secure, request)
    return response


@app.get("/organizaciones", response_class=HTMLResponse)
def listar_organizaciones_web(
    request: Request,
    db: Session = Depends(get_authenticated_db),
):
    if DATABASE_IS_SQLITE:
        return _redirect("/")
    usuario = db.get(Usuario, db.info["usuario_id"])
    membresias = membresias_activas(db, usuario.id)
    return TEMPLATES.TemplateResponse(
        request,
        "auth/organizations.html",
        {
            "usuario": usuario,
            "membresias": membresias,
            # Sin esto, quien se registra desde una invitación no encuentra
            # ninguna forma de aceptarla dentro de la aplicación.
            "invitaciones": invitaciones_pendientes_para(db, usuario=usuario),
            "error": request.query_params.get("error", ""),
            "msg": request.query_params.get("msg", ""),
        },
        headers={"Cache-Control": "no-store"},
    )


@app.post("/invitaciones/pendientes/{invitacion_id}/aceptar")
def aceptar_invitacion_pendiente_web(
    invitacion_id: int,
    request: Request,
    db: Session = Depends(get_authenticated_db),
):
    """Acepta una invitación ya visible en el panel, sin volver al email.

    El enlace del correo sigue funcionando igual; esta ruta cubre el caso en
    que la persona ya está dentro (típicamente recién registrada y confirmada),
    donde exigir que rebusque el email era un paso muerto.
    """
    if DATABASE_IS_SQLITE:
        return _redirect("/")
    usuario = db.get(Usuario, db.info["usuario_id"])
    identidad = request.state.supabase_identity
    try:
        membresia = aceptar_invitacion_pendiente(
            db,
            invitacion_id=invitacion_id,
            usuario=usuario,
            email_verificado=identidad.email_verified,
        )
        organizacion_id = membresia.organizacion_id
        db.commit()
    except GestionEquipoError as exc:
        db.rollback()
        return _redirect("/organizaciones", error=str(exc))
    except Exception:
        db.rollback()
        log.error(
            "Error aceptando la invitación pendiente:\n%s", traceback.format_exc()
        )
        raise
    response = _redirect(
        "/organizaciones", msg="Invitación aceptada. Ya puedes entrar a la organización."
    )
    _set_organization_cookie(response, organizacion_id)
    return response


@app.get("/organizaciones/nueva", response_class=HTMLResponse)
def nueva_organizacion_web(
    request: Request,
    db: Session = Depends(get_authenticated_db),
):
    if DATABASE_IS_SQLITE:
        return _redirect("/")
    usuario = db.get(Usuario, db.info["usuario_id"])
    pendientes = invitaciones_pendientes_para(db, usuario=usuario)
    # Quien llega aquí por el destino por omisión del registro puede tener una
    # invitación esperando: crear una empresa propia casi nunca es lo que
    # quiere, así que se le ofrece la opción correcta antes de escribir nada.
    if pendientes and not membresias_activas(db, usuario.id):
        return _redirect("/organizaciones")
    return TEMPLATES.TemplateResponse(
        request,
        "auth/organization_new.html",
        {"usuario": usuario, "error": request.query_params.get("error", "")},
    )


@app.post("/organizaciones/nueva")
async def crear_organizacion_web(
    request: Request,
    db: Session = Depends(get_authenticated_db),
):
    if DATABASE_IS_SQLITE:
        return _redirect("/")
    form = await request.form()
    nombre = str(form.get("nombre") or "").strip()[:200]
    if len(nombre) < 2:
        return _redirect(
            "/organizaciones/nueva",
            error="Escribe un nombre válido para la empresa.",
        )
    slug_base = _slug_organizacion(nombre)
    # RLS no debe revelar slugs de otras empresas para buscar un sufijo. Un
    # sufijo aleatorio mantiene la unicidad sin ampliar la lectura global.
    slug = f"{slug_base[:107]}-{uuid.uuid4().hex[:12]}"
    usuario = db.get(Usuario, db.info["usuario_id"])
    # El alta reserva el id desde ``organizaciones_id_seq`` para insertar sin
    # ``RETURNING``: la política ``cotizat_org_select`` exige una membresía que
    # todavía no existe y haría fallar la lectura implícita del INSERT.
    organizacion = crear_organizacion_con_propietario(
        db,
        nombre=nombre,
        slug=slug,
        usuario_id=usuario.id,
    )
    establecer_contexto_organizacion(db, organizacion.id)
    db.add(Configuracion(organizacion_id=organizacion.id))
    db.commit()
    response = RedirectResponse("/bienvenida", status_code=303)
    _set_organization_cookie(response, organizacion.id)
    return response


@app.post("/organizaciones/{organizacion_id}/seleccionar")
def seleccionar_organizacion_web(
    organizacion_id: int,
    db: Session = Depends(get_authenticated_db),
):
    if DATABASE_IS_SQLITE:
        return _redirect("/")
    usuario_id = db.info["usuario_id"]
    membresia = (
        db.query(Membresia)
        .join(Organizacion, Organizacion.id == Membresia.organizacion_id)
        .filter(
            Membresia.usuario_id == usuario_id,
            Membresia.organizacion_id == organizacion_id,
            Membresia.activa.is_(True),
            Organizacion.activa.is_(True),
        )
        .first()
    )
    if membresia is None:
        raise OrganizationAccessDenied(
            "No tienes acceso a la organización seleccionada."
        )
    response = RedirectResponse("/", status_code=303)
    _set_organization_cookie(response, organizacion_id)
    return response


def _render_equipo(
    request: Request,
    db: Session,
    *,
    invitation_link: str = "",
    msg: str = "",
    status_code: int = 200,
):
    organizacion_id = db.info["organizacion_id"]
    actor_rol = db.info["rol_membresia"]
    exigir_gestor(actor_rol)
    membresias = (
        db.query(Membresia)
        .join(Usuario, Usuario.id == Membresia.usuario_id)
        .filter(Membresia.organizacion_id == organizacion_id)
        .order_by(Membresia.activa.desc(), Usuario.email, Membresia.id)
        .all()
    )
    invitaciones = (
        db.query(InvitacionOrganizacion)
        .filter(
            InvitacionOrganizacion.organizacion_id == organizacion_id,
            InvitacionOrganizacion.accepted_at.is_(None),
            InvitacionOrganizacion.revoked_at.is_(None),
        )
        .order_by(InvitacionOrganizacion.created_at.desc())
        .all()
    )
    return TEMPLATES.TemplateResponse(
        request,
        "auth/team.html",
        {
            "membresias": membresias,
            "invitaciones": invitaciones,
            "actor_rol": actor_rol,
            "ahora": datetime.utcnow(),
            "invitation_link": invitation_link,
            "msg": msg or request.query_params.get("msg", ""),
            "error": request.query_params.get("error", ""),
        },
        status_code=status_code,
        headers={"Cache-Control": "no-store"},
    )


@app.get("/equipo", response_class=HTMLResponse)
def gestionar_equipo_web(request: Request, db: Session = Depends(get_db)):
    if DATABASE_IS_SQLITE:
        return _redirect("/")
    return _render_equipo(request, db)


@app.post("/equipo/invitaciones", response_class=HTMLResponse)
async def crear_invitacion_web(request: Request, db: Session = Depends(get_db)):
    if DATABASE_IS_SQLITE:
        return _redirect("/")
    form = await request.form()
    try:
        # Valida primero el origen fijo para no persistir una invitación cuyo
        # enlace no pueda construirse de forma segura.
        public_app_url("/")
        invitacion, token = crear_invitacion(
            db,
            organizacion_id=db.info["organizacion_id"],
            actor_usuario_id=db.info["usuario_id"],
            email=str(form.get("email") or ""),
            rol=str(form.get("rol") or ""),
        )
        invitation_link = public_app_url(f"/invitaciones/{token}")
        db.commit()
    except (GestionEquipoError, AuthNotConfigured) as exc:
        db.rollback()
        return _redirect("/equipo", error=str(exc))

    # La invitación ya está guardada: el correo es un canal de entrega, no la
    # fuente de verdad. Si no hay correo configurado o el proveedor falla, se
    # degrada al comportamiento de siempre: mostrar el enlace una vez en
    # pantalla para copiarlo.
    email_enviado = False
    try:
        organizacion = db.get(Organizacion, db.info["organizacion_id"])
        invitador = db.get(Usuario, db.info["usuario_id"])
        enviar_invitacion_por_email(
            email=invitacion.email,
            enlace=invitation_link,
            organizacion_nombre=organizacion.nombre if organizacion else "",
            invitador_nombre=invitador.nombre if invitador else "",
            invitador_email=invitador.email if invitador else "",
            rol=invitacion.rol,
            caduca_el=invitacion.expires_at,
        )
        email_enviado = True
    except (EmailNotConfigured, EmailSendError) as exc:
        log.info(
            "Invitación para %s sin correo (%s); se muestra el enlace en pantalla.",
            invitacion.email,
            type(exc).__name__,
        )
    if email_enviado:
        return _render_equipo(
            request,
            db,
            msg=(
                f"Invitación enviada a {invitacion.email}. "
                "Revisará su bandeja de entrada para aceptarla."
            ),
        )
    return _render_equipo(
        request,
        db,
        invitation_link=invitation_link,
        msg=(
            f"Invitación creada para {invitacion.email}. No se pudo enviar el "
            "correo: copia el enlace y compártelo por un canal seguro."
        ),
    )


@app.post("/equipo/invitaciones/{invitacion_id}/revocar")
def revocar_invitacion_web(
    invitacion_id: int,
    db: Session = Depends(get_db),
):
    if DATABASE_IS_SQLITE:
        return _redirect("/")
    invitacion = (
        db.query(InvitacionOrganizacion)
        .filter(
            InvitacionOrganizacion.id == invitacion_id,
            InvitacionOrganizacion.organizacion_id == db.info["organizacion_id"],
        )
        .first()
    )
    if invitacion is None:
        return _redirect("/equipo", error="La invitación no existe.")
    try:
        revocar_invitacion(
            db,
            invitacion=invitacion,
            organizacion_id=db.info["organizacion_id"],
            actor_usuario_id=db.info["usuario_id"],
        )
        db.commit()
    except GestionEquipoError as exc:
        db.rollback()
        return _redirect("/equipo", error=str(exc))
    return _redirect("/equipo", msg="Invitación revocada.")


@app.post("/equipo/membresias/{membresia_id}")
async def actualizar_membresia_web(
    membresia_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    if DATABASE_IS_SQLITE:
        return _redirect("/")
    membresia = (
        db.query(Membresia)
        .filter(
            Membresia.id == membresia_id,
            Membresia.organizacion_id == db.info["organizacion_id"],
        )
        .with_for_update()
        .first()
    )
    if membresia is None:
        return _redirect("/equipo", error="La membresía no existe.")
    form = await request.form()
    try:
        actualizar_membresia(
            db,
            membresia=membresia,
            organizacion_id=db.info["organizacion_id"],
            actor_usuario_id=db.info["usuario_id"],
            rol=str(form.get("rol") or ""),
            activa=str(form.get("activa") or "") == "1",
        )
        db.commit()
    except GestionEquipoError as exc:
        db.rollback()
        return _redirect("/equipo", error=str(exc))
    return _redirect("/equipo", msg="Membresía actualizada.")


def _render_invitacion(
    request: Request,
    token: str,
    *,
    error: str = "",
    status_code: int = 200,
    autenticado: bool = False,
    auto_aceptar: bool = False,
):
    return TEMPLATES.TemplateResponse(
        request,
        "auth/invitation.html",
        {
            "token": token,
            "error": error,
            "autenticado": autenticado,
            "auto_aceptar": auto_aceptar,
        },
        status_code=status_code,
        headers={"Cache-Control": "no-store", "Referrer-Policy": "strict-origin-when-cross-origin"},
    )


@app.get("/invitaciones/{token}", response_class=HTMLResponse)
def ver_invitacion_web(request: Request, token: str):
    # La vista pública no consulta la base ni confirma si el token existe.
    token_seguro = token if re.fullmatch(r"[A-Za-z0-9_-]{32,200}", token) else ""
    autenticado = bool(request.cookies.get(ACCESS_COOKIE))
    return _render_invitacion(request, token_seguro, autenticado=autenticado)


@app.get("/invitaciones/{token}/aceptar", response_class=HTMLResponse)
def ver_invitacion_aceptar_web(request: Request, token: str):
    """Página de aceptación servida por GET.

    Después de iniciar sesión, la redirección ``?next=...`` siempre llega por
    GET, así que esta ruta debe existir: sin ella el navegador recibía un
    405 Method Not Allowed porque la única ruta registrada era el POST.
    Si hay sesión, la página autoenvía el POST de aceptación (un clic menos
    tras el login); la validación y el consumo del token los hace el POST,
    protegido por CSRF, así que no se relaja ninguna seguridad.
    """
    # La vista pública no consulta la base ni confirma si el token existe.
    token_seguro = token if re.fullmatch(r"[A-Za-z0-9_-]{32,200}", token) else ""
    autenticado = bool(request.cookies.get(ACCESS_COOKIE))
    return _render_invitacion(
        request,
        token_seguro,
        autenticado=autenticado,
        auto_aceptar=autenticado,
    )


@app.post("/invitaciones/{token}/aceptar")
def aceptar_invitacion_web(
    token: str,
    request: Request,
    db: Session = Depends(get_authenticated_db),
):
    if DATABASE_IS_SQLITE:
        return _redirect("/")
    usuario = db.get(Usuario, db.info["usuario_id"])
    identidad = request.state.supabase_identity
    try:
        membresia = aceptar_invitacion(
            db,
            token=token,
            usuario=usuario,
            email_verificado=identidad.email_verified,
        )
        organizacion_id = membresia.organizacion_id
        db.commit()
    except GestionEquipoError as exc:
        db.rollback()
        return _render_invitacion(
            request,
            token,
            error=str(exc),
            status_code=400,
            autenticado=True,
        )
    except Exception:
        # Un fallo de base/RLS no debe morir como un 500 mudo: la traza queda
        # en el log del despliegue para diagnosticarlo (regresión del 500 al
        # aceptar invitaciones por la política SELECT sobre la fila nueva).
        db.rollback()
        log.error("Error aceptando la invitación:\n%s", traceback.format_exc())
        raise
    response = _redirect(
        "/organizaciones", msg="Invitación aceptada. Ya puedes entrar a la organización."
    )
    _set_organization_cookie(response, organizacion_id)
    return response


# ---------------------------------------------------------------------------
# Primer inicio
# ---------------------------------------------------------------------------

@app.get("/bienvenida", response_class=HTMLResponse)
def bienvenida(request: Request, db: Session = Depends(get_db)):
    cfg = _config(db)
    if cfg.onboarding_completado:
        return _redirect("/")
    return TEMPLATES.TemplateResponse(
        request,
        "onboarding.html",
        {"cfg": cfg, "error": request.query_params.get("error", "")},
    )


@app.post("/bienvenida")
async def finalizar_bienvenida(request: Request, db: Session = Depends(get_db)):
    cfg = _config(db)
    if cfg.onboarding_completado:
        return _redirect("/")
    if not cfg.onboarding_iniciado_at:
        cfg.onboarding_iniciado_at = datetime.utcnow()
        db.commit()
    form = await request.form()
    datos = {
        "empresa_nombre": form.get("empresa_nombre", ""),
        "empresa_legal": form.get("empresa_legal", ""),
        "empresa_rif": form.get("empresa_rif", ""),
        "empresa_pais": form.get("empresa_pais", "Venezuela"),
        "empresa_ciudad": form.get("empresa_ciudad", ""),
        "empresa_direccion": form.get("empresa_direccion", ""),
        "empresa_telefono": form.get("empresa_telefono", ""),
        "empresa_email": form.get("empresa_email", ""),
        "moneda_default": form.get("moneda_default", "USD"),
        "iva_default": _f(form.get("iva_default"), 16.0),
    }
    try:
        cfg = completar_onboarding(db, datos, str(form.get("modo_inicio", "")))
    except ErrorOnboarding as exc:
        return _redirect("/bienvenida", error=str(exc))

    logo = form.get("logo")
    if isinstance(logo, UploadFileStarlette) and logo.filename:
        ruta = await _guardar_imagen(logo, "logo", db)
        if ruta:
            cfg.logo = ruta
            db.commit()
    return _redirect("/", msg="Tu espacio de trabajo está listo. Completa la guía para crear tu primer PDF.")


@app.post("/recorrido/catalogo-revisado")
def marcar_catalogo_revisado(db: Session = Depends(get_db)):
    cfg = _config(db)
    if not cfg.onboarding_catalogo_revisado:
        cfg.onboarding_catalogo_revisado = True
        db.commit()
    return _redirect("/partidas")


# ---------------------------------------------------------------------------
# Páginas públicas: landing y legales (E1-018/019/020/056)
# ---------------------------------------------------------------------------
# No tocan datos de tenant ni sesión: solo renderizan contenido estático con
# la identidad del producto. Por eso no dependen de get_db y están declaradas
# como fronteras públicas en la auditoría de protección de rutas.

@app.get("/conocer", response_class=HTMLResponse, include_in_schema=False)
def landing_publica(request: Request):
    """Landing comercial: problema, resultado, público y llamada a demo."""
    return TEMPLATES.TemplateResponse(request, "landing.html", {})


# ---------------------------------------------------------------------------
# Panel de operador: licencias del producto (E1-060)
#
# Estas rutas son la única excepción al aislamiento multi-tenant, y por eso
# están agrupadas y marcadas. `get_operator_db` exige que el correo autenticado
# y verificado figure en COTIZAT_OPERADORES; en PostgreSQL, además, las
# políticas RLS de `licencias` solo devuelven filas a una sesión marcada como
# operador. El panel muestra datos de licencia (quién, cuánto, hasta cuándo),
# nunca datos de negocio de las organizaciones.
# ---------------------------------------------------------------------------


def _render_licencias(
    request: Request,
    db: Session,
    *,
    msg: str = "",
    error: str = "",
    status_code: int = 200,
):
    filas = resumen_organizaciones(db)
    return TEMPLATES.TemplateResponse(
        request,
        "admin/licencias.html",
        {
            "filas": filas,
            "totales": totales(filas),
            "duraciones": [(clave, texto) for clave, (texto, _) in DURACIONES.items()],
            "origenes": [
                (origen, ORIGENES_LICENCIA_ETIQUETA[origen])
                for origen in ORIGENES_LICENCIA
            ],
            "hoy": date.today(),
            "operador": db.info.get("auth_email", ""),
            # El panel avisa en cabecera si el corte automático está
            # apagado: sin él, una licencia vencida solo es información, no
            # una suspensión real del acceso.
            "exigencia_licencias": exigencia_licencia_activada(),
            "msg": msg or request.query_params.get("msg", ""),
            "error": error or request.query_params.get("error", ""),
        },
        status_code=status_code,
        headers={"Cache-Control": "no-store"},
    )


@app.get("/admin/licencias", response_class=HTMLResponse, include_in_schema=False)
def panel_licencias(request: Request, db: Session = Depends(get_operator_db)):
    return _render_licencias(request, db)


@app.post("/admin/licencias", include_in_schema=False)
async def crear_licencia_web(
    request: Request, db: Session = Depends(get_operator_db)
):
    form = await request.form()
    try:
        crear_licencia(
            db,
            organizacion_id=int(form.get("organizacion_id") or 0),
            origen=str(form.get("origen") or ""),
            duracion=str(form.get("duracion") or ""),
            importe=str(form.get("importe") or 0),
            moneda=str(form.get("moneda") or "USD"),
            metodo_cobro=str(form.get("metodo_cobro") or ""),
            referencia=str(form.get("referencia") or ""),
            notas=str(form.get("notas") or ""),
            operador_email=str(db.info.get("auth_email") or ""),
        )
        db.commit()
    except (GestionLicenciaError, ValueError) as exc:
        db.rollback()
        return _redirect("/admin/licencias", error=str(exc))
    except Exception:
        db.rollback()
        log.error("Error creando la licencia:\n%s", traceback.format_exc())
        raise
    return _redirect("/admin/licencias", msg="Licencia registrada.")


@app.post("/admin/licencias/{licencia_id}/cancelar", include_in_schema=False)
async def cancelar_licencia_web(
    licencia_id: int, request: Request, db: Session = Depends(get_operator_db)
):
    form = await request.form()
    try:
        cancelar_licencia(
            db,
            licencia_id=licencia_id,
            motivo=str(form.get("motivo") or ""),
            operador_email=str(db.info.get("auth_email") or ""),
        )
        db.commit()
    except GestionLicenciaError as exc:
        db.rollback()
        return _redirect("/admin/licencias", error=str(exc))
    except Exception:
        db.rollback()
        log.error("Error cancelando la licencia:\n%s", traceback.format_exc())
        raise
    return _redirect("/admin/licencias", msg="Licencia cancelada.")


@app.get("/admin/licencias/{licencia_id}/recibo.pdf", include_in_schema=False)
def recibo_licencia_web(
    licencia_id: int, request: Request, db: Session = Depends(get_operator_db)
):
    """Descarga el comprobante de pago de una licencia (E1-060).

    Misma puerta del resto del panel: `get_operator_db` + RLS de operador en
    PostgreSQL. Los errores de negocio (licencia inexistente o que no es de
    pago) vuelven al panel como mensaje; no hay nada útil que servir en un 404
    de un panel sin enlaces públicos.
    """
    licencia = db.get(Licencia, licencia_id)
    if licencia is None or licencia.organizacion is None:
        return _redirect("/admin/licencias", error="La licencia indicada no existe.")
    try:
        buffer = generar_recibo_licencia_pdf(licencia, licencia.organizacion)
    except GestionLicenciaError as exc:
        return _redirect("/admin/licencias", error=str(exc))
    nombre_archivo = (
        f"recibo-{numero_recibo(licencia)}-{licencia.organizacion.slug}.pdf"
    )
    return Response(
        buffer.read(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{nombre_archivo}"',
            "Cache-Control": "no-store",
        },
    )


@app.post("/admin/licencias/avisos", include_in_schema=False)
def enviar_avisos_web(request: Request, db: Session = Depends(get_operator_db)):
    """Envía los avisos de vencimiento a las organizaciones por vencer.

    Lo dispara el operador a mano: no hay trabajos programados en un
    despliegue serverless. El envío real lo hace Resend; la licencia queda
    anotada con la fecha y los destinatarios para no reenviar el mismo día.
    """
    from .services.email import EmailNotConfigured, enviar_aviso_licencia

    try:
        resultado = enviar_avisos_vencimiento(db, remitente=enviar_aviso_licencia)
        db.commit()
    except EmailNotConfigured:
        db.rollback()
        return _redirect(
            "/admin/licencias",
            error=(
                "El correo no está configurado: faltan RESEND_API_KEY o "
                "COTIZAT_EMAIL_FROM en el despliegue."
            ),
        )
    except Exception:
        db.rollback()
        log.error("Error enviando avisos de vencimiento:\n%s", traceback.format_exc())
        raise

    partes = []
    if resultado["avisadas"]:
        partes.append(f"{len(resultado['avisadas'])} organización(es) avisada(s)")
    if resultado["omitidas"]:
        partes.append(f"{len(resultado['omitidas'])} ya avisada(s) hoy")
    if resultado["sin_correo"]:
        partes.append(
            "sin correo de administrador: " + ", ".join(resultado["sin_correo"])
        )
    if not partes and not resultado["fallidas"]:
        return _redirect(
            "/admin/licencias",
            msg="Ninguna licencia vence dentro del plazo de aviso.",
        )
    if resultado["fallidas"]:
        detalle = "; ".join(
            f"{nombre}: {exc}" for nombre, exc in resultado["fallidas"]
        )
        if partes:
            partes.append(f"errores: {detalle}")
            return _redirect("/admin/licencias", error=" | ".join(partes))
        return _redirect(
            "/admin/licencias", error=f"No se pudo enviar ningún aviso: {detalle}"
        )
    return _redirect("/admin/licencias", msg="; ".join(partes) + ".")


_PAGINAS_LEGALES = {
    "terminos": "legal/terminos.html",
    "privacidad": "legal/privacidad.html",
    "soporte": "legal/soporte.html",
    "licencias": "legal/licencias.html",
    "preguntas": "legal/preguntas.html",
}


@app.get("/legal/{pagina}", response_class=HTMLResponse, include_in_schema=False)
def pagina_legal(pagina: str, request: Request):
    plantilla = _PAGINAS_LEGALES.get(pagina)
    if plantilla is None:
        return Response("Página no encontrada.", status_code=404)
    return TEMPLATES.TemplateResponse(request, plantilla, {})


# ---------------------------------------------------------------------------
# Inicio
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def inicio(request: Request, db: Session = Depends(get_db)):
    cfg = _config(db)
    if not cfg.onboarding_completado:
        return _redirect("/bienvenida")
    total_presupuestos = db.query(Presupuesto).count()
    total_clientes = db.query(Cliente).count()
    por_estado = {e: db.query(Presupuesto).filter(Presupuesto.estado == e).count() for e in ESTADOS}
    aprobados = db.query(Presupuesto).filter(Presupuesto.estado == "aprobado").all()
    importe_aprobado = sum(p.total for p in aprobados)
    recientes = db.query(Presupuesto).order_by(Presupuesto.id.desc()).limit(6).all()
    # Presupuestos enviados que vencen en los próximos 7 días
    hoy = date.today()
    fin_semana = hoy + timedelta(days=7)
    por_vencer = sum(
        1 for p in db.query(Presupuesto).filter(Presupuesto.estado == "enviado").all()
        if p.validez_dias and hoy <= p.fecha + timedelta(days=p.validez_dias) <= fin_semana
    )
    total_facturas = db.query(Factura).count()
    mes_inicio = hoy.replace(day=1)
    presupuestos_mes = [p for p in db.query(Presupuesto).filter(Presupuesto.fecha >= mes_inicio).all()]
    enviados_mes = sum(1 for p in presupuestos_mes if p.estado in ("enviado", "reenviado"))
    aprobados_mes = [p for p in presupuestos_mes if p.estado in ("aprobado", "aprobado_parcialmente")]
    total_enviados = sum(1 for p in db.query(Presupuesto).all() if p.estado in ("enviado", "reenviado", "aprobado", "aprobado_parcialmente", "en_ejecucion", "finalizado"))
    total_aprobados = sum(1 for p in db.query(Presupuesto).all() if p.estado in ("aprobado", "aprobado_parcialmente", "en_ejecucion", "finalizado"))
    descuentos_concedidos = sum(p.descuento_monto for p in db.query(Presupuesto).all())
    margen_estimado = sum(p.margen for p in db.query(Presupuesto).filter(Presupuesto.estado.in_(["aprobado", "aprobado_parcialmente", "en_ejecucion", "finalizado"])).all())
    proyectos_activos = db.query(Proyecto).filter(Proyecto.estado.in_(["en_ejecucion", "pausado"])).count()
    analisis_precios = analizar_catalogo_partidas(db)
    recorrido_inicial = (
        estado_recorrido_inicial(db, cfg)
        if cfg.onboarding_modo in {"demo", "limpio"}
        else None
    )
    return TEMPLATES.TemplateResponse(
        request,
        "index.html",
        {
            "total_presupuestos": total_presupuestos,
            "total_clientes": total_clientes,
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
        },
    )


@app.post("/presupuestos/actualizar-vencidos")
def actualizar_presupuestos_vencidos(db: Session = Depends(get_db)):
    if db.info.get("rol_membresia") == "lectura":
        return {"ok": True, "actualizados": 0}
    return {"ok": True, "actualizados": marcar_vencidos(db)}


@app.get("/presupuestos/optimizar-precios", response_class=HTMLResponse)
def optimizar_precios(request: Request, db: Session = Depends(get_db)):
    """Análisis real (basado en tus propios datos) de márgenes y precios sin
    revisar en el catálogo de partidas. Reemplaza al antiguo botón que sólo
    mostraba un mensaje fijo sin hacer ningún cálculo."""
    analisis = analizar_catalogo_partidas(db)
    return TEMPLATES.TemplateResponse(request, "budgets/optimizar.html", {"analisis": analisis})


# ---------------------------------------------------------------------------
# Reportes
# ---------------------------------------------------------------------------
@app.get("/reportes", response_class=HTMLResponse)
def reportes(request: Request, desde: str = "", hasta: str = "", db: Session = Depends(get_db)):
    try: inicio = date.fromisoformat(desde) if desde else date.today().replace(day=1)
    except ValueError: inicio = date.today().replace(day=1)
    try: fin = date.fromisoformat(hasta) if hasta else date.today()
    except ValueError: fin = date.today()
    presupuestos = db.query(Presupuesto).filter(Presupuesto.fecha >= inicio, Presupuesto.fecha <= fin).all()
    por_estado = {e: [p for p in presupuestos if p.estado == e] for e in ESTADOS}
    clientes = {}
    for p in presupuestos: clientes[p.cliente.nombre] = clientes.get(p.cliente.nombre, 0) + p.total
    return TEMPLATES.TemplateResponse(request, "reports.html", {"desde": inicio.isoformat(), "hasta": fin.isoformat(), "presupuestos": presupuestos, "por_estado": por_estado, "clientes": sorted(clientes.items(), key=lambda x:x[1], reverse=True), "proyectos": db.query(Proyecto).all()})

@app.get("/reportes/exportar")
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

@app.get("/buscar", response_class=HTMLResponse)
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
        resultados["partidas"] = db.query(Partida).filter(or_(
            Partida.nombre.ilike(like), Partida.descripcion.ilike(like),
            Partida.codigo_interno.ilike(like), Partida.categoria.ilike(like),
            Partida.subcategoria.ilike(like), Partida.proveedor.ilike(like),
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
    return TEMPLATES.TemplateResponse(request, "search.html", {
        "q": q, "consulta": consulta, "resultados": resultados, "total": total,
    })


# ---------------------------------------------------------------------------
# Clientes
# ---------------------------------------------------------------------------

@app.get("/clientes", response_class=HTMLResponse)
def listar_clientes(request: Request, q: str = "", db: Session = Depends(get_db)):
    query = db.query(Cliente)
    if q.strip():
        like = f"%{q.strip()}%"
        query = query.filter(or_(Cliente.nombre.ilike(like), Cliente.rif.ilike(like), Cliente.email.ilike(like)))
    clientes = query.order_by(Cliente.nombre).all()
    return TEMPLATES.TemplateResponse(request, "clients/list.html", {"clientes": clientes, "q": q})


@app.get("/clientes/nuevo", response_class=HTMLResponse)
def nuevo_cliente_form(request: Request, _db: Session = Depends(get_db)):
    return TEMPLATES.TemplateResponse(request, "clients/form.html", {"cliente": None})


@app.post("/clientes/nuevo")
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


@app.get("/clientes/{cliente_id}/editar", response_class=HTMLResponse)
def editar_cliente_form(cliente_id: int, request: Request, db: Session = Depends(get_db)):
    cliente = db.get(Cliente, cliente_id)
    if cliente is None:
        return _redirect("/clientes", error="Cliente no encontrado.")
    return TEMPLATES.TemplateResponse(request, "clients/form.html", {"cliente": cliente})


@app.post("/clientes/{cliente_id}/editar")
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


@app.post("/clientes/{cliente_id}/eliminar")
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


# ---------------------------------------------------------------------------
# Presupuestos
# ---------------------------------------------------------------------------

@app.get("/presupuestos", response_class=HTMLResponse)
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


@app.get("/presupuestos/exportar")
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
        from .services.excel_export import exportar_historial_excel
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
        db.add(Partida(
            nombre=nombre,
            descripcion=str(item.get("descripcion", "")).strip(),
            precio_unitario=precio,
            unidad=str(item.get("unidad", "ud")).strip() or "ud",
            categoria=categoria,
            codigo_interno=str(item.get("codigo") or item.get("codigo_externo") or "").strip(),
            codigo_externo=str(item.get("codigo") or item.get("codigo_externo") or "").strip(),
            descomposicion_json=json.dumps({
                "origen": "cype" if es_cype else "manual",
                "codigo": str(item.get("codigo") or item.get("codigo_externo") or ""),
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


@app.get("/presupuestos/importar", response_class=HTMLResponse)
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


@app.post("/presupuestos/importar/analizar")
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


@app.post("/presupuestos/importar/validar")
async def validar_importacion_presupuesto(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
        resultado, _ = _datos_importacion_desde_payload(payload, db)
        return {"ok": True, **resultado}
    except (ValueError, TypeError, ErrorImportacion) as exc:
        return {"ok": False, "error": str(exc)}


@app.post("/presupuestos/importar/confirmar")
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
            moneda=cfg.moneda_default, impuesto_pct=cfg.iva_default, descuento_pct=0.0,
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


@app.get("/presupuestos/nuevo", response_class=HTMLResponse)
def nuevo_presupuesto_form(request: Request, db: Session = Depends(get_db)):
    cfg = _config(db)
    clientes = db.query(Cliente).order_by(Cliente.nombre).all()
    partidas_catalogo = db.query(Partida).order_by(Partida.ultimo_uso.desc(), Partida.usos.desc(), Partida.nombre).all()
    productos_catalogo = db.query(Producto).order_by(Producto.ultimo_uso.desc(), Producto.usos.desc(), Producto.nombre).all()
    recursos_catalogo = db.query(Recurso).order_by(Recurso.ultimo_uso.desc(), Recurso.usos.desc(), Recurso.descripcion).all()
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


@app.post("/presupuestos/nuevo")
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

    con_portada = bool(form.get("con_portada"))
    mostrar_firmas = bool(form.get("mostrar_firmas"))
    mostrar_resumen_capitulos = bool(form.get("mostrar_resumen_capitulos"))
    mostrar_garantias = bool(form.get("mostrar_garantias"))
    usar_funciones_avanzadas = bool(form.get("usar_funciones_avanzadas"))
    foto_proyecto = ""
    foto_file = form.get("foto_proyecto")
    if isinstance(foto_file, UploadFileStarlette) and foto_file.filename:
        foto_proyecto = await _guardar_imagen(foto_file, f"projects/p_new_{date.today().isoformat()}", db)

    presupuesto = Presupuesto(
        numero=proximo_numero(db, f.year),
        year=f.year,
        fecha=f,
        titulo=str(form.get("titulo", "")).strip(),
        direccion_obra=str(form.get("direccion_obra", "")).strip(),
        codigo_postal=str(form.get("codigo_postal", "")).strip(),
        validez_dias=int(_f(form.get("validez_dias"), 30)),
        moneda=form.get("moneda") if form.get("moneda") in ("USD", "Bs") else "USD",
        tipo_cambio=_f(form.get("tipo_cambio"), None) if str(form.get("tipo_cambio", "")).strip() else None,
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
@app.get("/proyectos", response_class=HTMLResponse)
def listar_proyectos(request: Request, db: Session = Depends(get_db)):
    return TEMPLATES.TemplateResponse(request, "projects/list.html", {"proyectos": db.query(Proyecto).order_by(Proyecto.id.desc()).all()})

@app.post("/presupuestos/{presupuesto_id}/proyecto")
def convertir_proyecto(presupuesto_id: int, db: Session = Depends(get_db)):
    p = db.get(Presupuesto, presupuesto_id)
    if not p or p.estado not in ("aprobado", "aprobado_parcialmente"):
        return _redirect(f"/presupuestos/{presupuesto_id}", error="Solo un presupuesto aprobado puede convertirse en proyecto.")
    existente = db.query(Proyecto).filter_by(presupuesto_id=p.id).first()
    if existente: return _redirect(f"/proyectos/{existente.id}", msg="Este presupuesto ya tiene un proyecto.")
    version = db.query(PresupuestoVersion).filter_by(presupuesto_id=p.id, estado=p.estado).order_by(PresupuestoVersion.numero_version.desc()).first()
    if not version:
        version = crear_version(db, p, "Versión aprobada al convertir en proyecto"); db.flush()
    proyecto = Proyecto(presupuesto_id=p.id, presupuesto_version_id=version.id, nombre=p.titulo or f"Proyecto {p.numero}", fecha_inicio=date.today())
    db.add(proyecto); p.estado = "en_ejecucion"; db.commit()
    return _redirect(f"/proyectos/{proyecto.id}", msg="Proyecto creado desde el presupuesto aprobado.")

@app.get("/proyectos/{proyecto_id}", response_class=HTMLResponse)
def ver_proyecto(proyecto_id: int, request: Request, db: Session = Depends(get_db)):
    proyecto = db.get(Proyecto, proyecto_id)
    if not proyecto: return _redirect("/proyectos", error="Proyecto no encontrado.")
    return TEMPLATES.TemplateResponse(request, "projects/detail.html", {"proyecto": proyecto, "hoy": date.today()})

@app.post("/proyectos/{proyecto_id}/actualizar")
def actualizar_proyecto(proyecto_id: int, nombre: str = Form(""), estado: str = Form("en_ejecucion"), fecha_inicio: str = Form(""), fecha_estimada_fin: str = Form(""), fecha_fin: str = Form(""), notas: str = Form(""), db: Session = Depends(get_db)):
    p = db.get(Proyecto, proyecto_id)
    if not p: return _redirect("/proyectos", error="Proyecto no encontrado.")
    def d(v):
        try: return date.fromisoformat(v) if v else None
        except ValueError: return None
    p.nombre, p.estado, p.fecha_inicio, p.fecha_estimada_fin, p.fecha_fin, p.notas = nombre.strip() or p.nombre, estado, d(fecha_inicio), d(fecha_estimada_fin), d(fecha_fin), notas.strip()
    db.commit(); return _redirect(f"/proyectos/{p.id}", msg="Proyecto actualizado.")

@app.post("/proyectos/{proyecto_id}/cambios")
def crear_cambio(proyecto_id: int, descripcion: str = Form(""), db: Session = Depends(get_db)):
    p = db.get(Proyecto, proyecto_id)
    if not p or not descripcion.strip(): return _redirect(f"/proyectos/{proyecto_id}", error="Describe el cambio de alcance.")
    numero = max((c.numero for c in p.cambios), default=0) + 1
    cambio = CambioAlcance(proyecto_id=p.id, numero=numero, descripcion=descripcion.strip())
    db.add(cambio); db.commit(); return _redirect(f"/proyectos/{p.id}/cambios/{cambio.id}", msg=f"Cambio Nº {numero:03d} creado.")

@app.get("/proyectos/{proyecto_id}/cambios/{cambio_id}", response_class=HTMLResponse)
def editar_cambio(proyecto_id: int, cambio_id: int, request: Request, db: Session = Depends(get_db)):
    c = db.get(CambioAlcance, cambio_id)
    if not c or c.proyecto_id != proyecto_id: return _redirect(f"/proyectos/{proyecto_id}", error="Cambio no encontrado.")
    return TEMPLATES.TemplateResponse(request, "projects/change.html", {"cambio": c, "proyecto": c.proyecto})

@app.post("/proyectos/{proyecto_id}/cambios/{cambio_id}")
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

@app.post("/proyectos/{proyecto_id}/pagos")
def registrar_pago(proyecto_id: int, importe: float = Form(0), fecha: str = Form(""), metodo: str = Form("transferencia"), referencia: str = Form(""), estado: str = Form("confirmado"), notas: str = Form(""), db: Session = Depends(get_db)):
    p=db.get(Proyecto, proyecto_id)
    if not p or importe <= 0: return _redirect(f"/proyectos/{proyecto_id}", error="Indica un importe de pago válido.")
    try: fecha_pago=date.fromisoformat(fecha) if fecha else date.today()
    except ValueError: fecha_pago=date.today()
    db.add(Pago(proyecto_id=p.id, presupuesto_id=p.presupuesto_id, fecha=fecha_pago, importe=importe, moneda=p.presupuesto.moneda, metodo=metodo, referencia=referencia.strip(), estado=estado if estado in ("pendiente","confirmado","anulado") else "confirmado", notas=notas.strip()))
    db.commit(); return _redirect(f"/proyectos/{p.id}", msg="Pago registrado.")


@app.get("/presupuestos/{presupuesto_id}", response_class=HTMLResponse)
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


@app.get("/presupuestos/{presupuesto_id}/tiempos", response_class=HTMLResponse)
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


@app.post("/presupuestos/{presupuesto_id}/tiempos/manual")
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


@app.post("/presupuestos/{presupuesto_id}/tiempos/bulk")
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


@app.get("/presupuestos/{presupuesto_id}/partidas/{partida_id}/descomposicion", response_class=HTMLResponse)
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


@app.post("/presupuestos/{presupuesto_id}/partidas/{partida_id}/descomposicion")
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


@app.post("/presupuestos/{presupuesto_id}/versiones")
def crear_version_manual(presupuesto_id: int, motivo: str = Form(""), db: Session = Depends(get_db)):
    presupuesto = db.get(Presupuesto, presupuesto_id)
    if presupuesto is None:
        return _redirect("/presupuestos", error="Presupuesto no encontrado.")
    version = crear_version(db, presupuesto, motivo or "Versión creada manualmente")
    db.commit()
    return _redirect(f"/presupuestos/{presupuesto_id}#versiones", msg=f"Versión {version.numero_version} congelada.")


@app.get("/presupuestos/{presupuesto_id}/versiones/comparar", response_class=HTMLResponse)
def comparar_versiones(presupuesto_id: int, a: int, b: int, request: Request, db: Session = Depends(get_db)):
    versiones = {v.id: v for v in db.query(PresupuestoVersion).filter_by(presupuesto_id=presupuesto_id).all()}
    va, vb = versiones.get(a), versiones.get(b)
    if not va or not vb:
        return _redirect(f"/presupuestos/{presupuesto_id}#versiones", error="Selecciona dos versiones válidas.")
    return TEMPLATES.TemplateResponse(request, "budgets/compare_versions.html", {"p": va.presupuesto, "a": va, "b": vb, "sa": leer_snapshot(va), "sb": leer_snapshot(vb)})


@app.get("/presupuestos/{presupuesto_id}/versiones/{version_id}", response_class=HTMLResponse)
def ver_version(presupuesto_id: int, version_id: int, request: Request, db: Session = Depends(get_db)):
    version = db.get(PresupuestoVersion, version_id)
    if version is None or version.presupuesto_id != presupuesto_id:
        return _redirect(f"/presupuestos/{presupuesto_id}", error="Versión no encontrada.")
    return TEMPLATES.TemplateResponse(request, "budgets/version.html", {"p": version.presupuesto, "version": version, "snapshot": leer_snapshot(version)})


@app.get("/presupuestos/{presupuesto_id}/exportar")
def exportar_presupuesto(presupuesto_id: int, formato: str = "csv", db: Session = Depends(get_db)):
    """Exportar presupuesto a CSV o Excel con formato profesional."""
    p = db.get(Presupuesto, presupuesto_id)
    if p is None:
        return _redirect("/presupuestos", error="Presupuesto no encontrado.")

    if formato.lower() == "excel" or formato.lower() == "xlsx":
        from .services.excel_export import exportar_presupuesto_excel
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


@app.post("/presupuestos/{presupuesto_id}/notas")
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

@app.post("/presupuestos/{presupuesto_id}/factura")
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


@app.get("/facturas", response_class=HTMLResponse)
def listar_facturas(request: Request, db: Session = Depends(get_db)):
    facturas = db.query(Factura).order_by(Factura.id.desc()).all()
    return TEMPLATES.TemplateResponse(request, "facturas/list.html", {"facturas": facturas})


@app.get("/facturas/{factura_id}", response_class=HTMLResponse)
def ver_factura(factura_id: int, request: Request, db: Session = Depends(get_db)):
    factura = db.get(Factura, factura_id)
    if factura is None:
        return _redirect("/facturas", error="Documento de cobro no encontrado.")
    return TEMPLATES.TemplateResponse(request, "facturas/detail.html", {"f": factura})


@app.get("/facturas/{factura_id}/pdf")
def descargar_pdf_factura(factura_id: int, inline: int = 0, db: Session = Depends(get_db)):
    factura = db.get(Factura, factura_id)
    if factura is None:
        return _redirect("/facturas", error="Documento de cobro no encontrado.")
    resultado = _generar_pdf_seguro(
        lambda: pdf_service.generar_factura_pdf(factura, _config(db)),
        f"el PDF del documento de cobro {factura.numero}",
    )
    if isinstance(resultado, Response) and resultado.status_code != 200:
        return resultado
    return _respuesta_pdf(resultado, f"documento_cobro_{factura.numero}.pdf", inline)


@app.post("/facturas/{factura_id}/estado")
def cambiar_estado_factura(factura_id: int, estado: str = Form(...), db: Session = Depends(get_db)):
    factura = db.get(Factura, factura_id)
    if factura is None:
        return _redirect("/facturas", error="Documento de cobro no encontrado.")
    if estado in ("emitida", "anulada"):
        factura.estado = estado
        db.commit()
        return _redirect(f"/facturas/{factura_id}", msg=f"Documento de cobro marcado como «{estado}».")
    return _redirect(f"/facturas/{factura_id}", error="Estado inválido.")


@app.post("/facturas/{factura_id}/eliminar")
def eliminar_factura(factura_id: int, db: Session = Depends(get_db)):
    factura = db.get(Factura, factura_id)
    if factura is None:
        return _redirect("/facturas", error="Documento de cobro no encontrado.")
    numero = factura.numero
    db.delete(factura)
    db.commit()
    return _redirect("/facturas", msg=f"Documento de cobro {numero} eliminado.")


@app.post("/presupuestos/{presupuesto_id}/borrador")
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


@app.get("/presupuestos/{presupuesto_id}/borrador")
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


@app.get("/presupuestos/{presupuesto_id}/editar", response_class=HTMLResponse)
def editar_presupuesto_form(presupuesto_id: int, request: Request, db: Session = Depends(get_db)):
    presupuesto = db.get(Presupuesto, presupuesto_id)
    if presupuesto is None:
        return _redirect("/presupuestos", error="Presupuesto no encontrado.")
    clientes = db.query(Cliente).order_by(Cliente.nombre).all()
    partidas_catalogo = db.query(Partida).order_by(Partida.ultimo_uso.desc(), Partida.usos.desc(), Partida.nombre).all()
    productos_catalogo = db.query(Producto).order_by(Producto.ultimo_uso.desc(), Producto.usos.desc(), Producto.nombre).all()
    recursos_catalogo = db.query(Recurso).order_by(Recurso.ultimo_uso.desc(), Recurso.usos.desc(), Recurso.descripcion).all()
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


@app.post("/presupuestos/{presupuesto_id}/editar")
async def actualizar_presupuesto(presupuesto_id: int, request: Request, db: Session = Depends(get_db)):
    presupuesto = db.get(Presupuesto, presupuesto_id)
    if presupuesto is None:
        return _redirect("/presupuestos", error="Presupuesto no encontrado.")
    form = await request.form()
    estaba_congelado = presupuesto.estado in ESTADOS_CONGELABLES

    cliente = db.get(Cliente, int(_f(form.get("client_id"))))
    if cliente is None:
        return _redirect(f"/presupuestos/{presupuesto_id}/editar", error="Selecciona un cliente válido.")
    capitulos, partidas = _leer_formulario_presupuesto(form, db)
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
    presupuesto.moneda = form.get("moneda") if form.get("moneda") in ("USD", "Bs") else "USD"
    presupuesto.tipo_cambio = _f(form.get("tipo_cambio"), None) if str(form.get("tipo_cambio", "")).strip() else None
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


@app.post("/presupuestos/{presupuesto_id}/estado")
def cambiar_estado(presupuesto_id: int, estado: str = Form(...), db: Session = Depends(get_db)):
    presupuesto = db.get(Presupuesto, presupuesto_id)
    if presupuesto is None:
        return _redirect("/presupuestos", error="Presupuesto no encontrado.")
    if _estado_valido(estado):
        presupuesto.estado = estado
        if estado in ESTADOS_CONGELABLES:
            crear_version(db, presupuesto, f"Documento marcado como {estado.replace('_', ' ')}")
        db.commit()
        return _redirect(f"/presupuestos/{presupuesto_id}", msg=f"Estado cambiado a «{estado}».")
    return _redirect(f"/presupuestos/{presupuesto_id}", error="Estado inválido.")


@app.post("/presupuestos/{presupuesto_id}/duplicar")
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


@app.post("/presupuestos/{presupuesto_id}/eliminar")
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


@app.post("/presupuestos/{presupuesto_id}/anexos")
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

@app.post("/presupuestos/{presupuesto_id}/anexos/{anexo_id}/eliminar")
def eliminar_anexo(presupuesto_id: int, anexo_id: int, db: Session = Depends(get_db)):
    anexo=db.get(AnexoPresupuesto, anexo_id)
    if not anexo or anexo.presupuesto_id != presupuesto_id: return _redirect(f"/presupuestos/{presupuesto_id}", error="Anexo no encontrado.")
    referencia = anexo.archivo
    db.delete(anexo)
    _borrar_imagen(referencia, db)
    db.commit()
    return _redirect(f"/presupuestos/{presupuesto_id}#anexos", msg="Anexo eliminado.")


@app.post("/presupuestos/{presupuesto_id}/pdf-descargado")
def registrar_pdf_descargado(presupuesto_id: int, db: Session = Depends(get_db)):
    presupuesto = db.get(Presupuesto, presupuesto_id)
    if presupuesto is None:
        return JSONResponse({"ok": False, "error": "Presupuesto no encontrado."}, status_code=404)
    if db.info.get("rol_membresia") == "lectura" or presupuesto.es_demo:
        return {"ok": True, "registrado": False}
    cfg = _config(db)
    if not cfg.onboarding_pdf_descargado:
        cfg.onboarding_pdf_descargado = True
        cfg.primer_pdf_at = datetime.utcnow()
        db.commit()
    return {"ok": True, "registrado": True}


@app.get("/presupuestos/{presupuesto_id}/pdf")
def descargar_pdf(presupuesto_id: int, inline: int = 0, db: Session = Depends(get_db)):
    presupuesto = db.get(Presupuesto, presupuesto_id)
    if presupuesto is None:
        return _redirect("/presupuestos", error="Presupuesto no encontrado.")
    cfg = _config(db)
    resultado = _generar_pdf_seguro(
        lambda: pdf_service.generar_pdf(presupuesto, cfg),
        f"el PDF del presupuesto {presupuesto.numero}",
    )
    if isinstance(resultado, Response) and resultado.status_code != 200:
        return resultado
    return _respuesta_pdf(resultado, f"presupuesto_{presupuesto.numero}.pdf", inline)


@app.get("/presupuestos/{presupuesto_id}/contrato")
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


# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

@app.get("/configuracion", response_class=HTMLResponse)
def ver_configuracion(request: Request, db: Session = Depends(get_db)):
    return TEMPLATES.TemplateResponse(request, "settings.html", {"cfg": _config(db)})


@app.post("/configuracion")
async def guardar_configuracion(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    cfg = _config(db)
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

@app.get("/configuracion/backup")
def descargar_backup():
    """Descarga una copia completa de una instalación SQLite local."""
    if not DATABASE_IS_SQLITE:
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


@app.post("/configuracion/restaurar")
async def restaurar_backup(request: Request):
    if not DATABASE_IS_SQLITE:
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


@app.get("/configuracion/importar-instalacion", response_class=HTMLResponse)
def importar_instalacion_form(request: Request, db: Session = Depends(get_db)):
    """Pantalla del asistente; disponible también en SQLite para probar en local."""
    return TEMPLATES.TemplateResponse(
        request,
        "importar_instalacion.html",
        {"resumen": None, "resultado": None, "rol": db.info.get("rol_membresia")},
    )


@app.post("/configuracion/importar-instalacion/analizar", response_class=HTMLResponse)
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


@app.post("/configuracion/importar-instalacion/confirmar", response_class=HTMLResponse)
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
# Catálogos — partidas y productos
# ---------------------------------------------------------------------------

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
# Partidas (Catálogo reutilizable)
# ---------------------------------------------------------------------------

def _partida_catalogo_json(partida: Partida) -> dict:
    """Contrato único de una partida para el catálogo y el creador.

    El editor de presupuestos consume exactamente la misma ficha y la misma
    descomposición que la pestaña Partidas; no mantiene una versión reducida.
    """
    try:
        descomposicion = json.loads(partida.descomposicion_json or "[]")
    except (TypeError, ValueError):
        descomposicion = []
    if isinstance(descomposicion, list):
        descomposicion = {"origen": "manual", "filas": descomposicion}
    if not isinstance(descomposicion, dict):
        descomposicion = {"origen": "manual", "filas": []}
    return {
        "id": partida.id,
        "nombre": partida.nombre or "",
        "descripcion": partida.descripcion or "",
        "precio": partida.precio_unitario or 0.0,
        "precio_unitario": partida.precio_unitario or 0.0,
        "unidad": partida.unidad or "ud",
        "categoria": partida.categoria or "General",
        "subcategoria": partida.subcategoria or "",
        "codigo": partida.codigo_interno or partida.codigo_externo or "",
        "codigo_interno": partida.codigo_interno or "",
        "codigo_externo": partida.codigo_externo or "",
        "coste_materiales": partida.coste_materiales or 0.0,
        "coste_mano_obra": partida.coste_mano_obra or 0.0,
        "coste_complementarios": partida.coste_complementarios or 0.0,
        "coste_otros": partida.coste_otros or 0.0,
        "tiempo_estimado_horas": partida.tiempo_estimado_horas,
        "tiempo_oficial_horas": getattr(partida, "tiempo_oficial_horas", None),
        "tiempo_ayudante_horas": getattr(partida, "tiempo_ayudante_horas", None),
        "tiempo_equipo_horas": getattr(partida, "tiempo_equipo_horas", None),
        "proveedor": partida.proveedor or "",
        "rendimiento": partida.rendimiento or "",
        "desperdicio_recomendado_pct": partida.desperdicio_recomendado_pct or 0.0,
        "imagen": partida.imagen or "",
        "notas_tecnicas": partida.notas_tecnicas or "",
        "descomposicion": descomposicion,
        "usos": partida.usos or 0,
    }


@app.get("/partidas", response_class=HTMLResponse)
def listar_partidas(request: Request, q: str = "", db: Session = Depends(get_db)):
    query = db.query(Partida)
    if q.strip():
        like = f"%{q.strip()}%"
        query = query.filter(or_(
            Partida.nombre.ilike(like), Partida.categoria.ilike(like),
            Partida.subcategoria.ilike(like), Partida.codigo_interno.ilike(like),
            Partida.proveedor.ilike(like), Partida.descripcion.ilike(like),
        ))
    partidas = query.order_by(Partida.categoria, Partida.subcategoria, Partida.ultimo_uso.desc(), Partida.nombre).all()
    catalogo_descompuestos = {}
    for partida in partidas:
        try:
            valor = json.loads(partida.descomposicion_json or "[]")
            catalogo_descompuestos[partida.id] = valor.get("filas", []) if isinstance(valor, dict) else valor
        except (TypeError, ValueError):
            catalogo_descompuestos[partida.id] = []
    categorias_catalogo = db.query(CategoriaPartida).order_by(CategoriaPartida.categoria, CategoriaPartida.subcategoria).all()
    return TEMPLATES.TemplateResponse(request, "partidas/list.html", {"partidas": partidas, "q": q, "catalogo_descompuestos": catalogo_descompuestos, "categorias_catalogo": categorias_catalogo})


@app.get("/partidas/exportar")
def exportar_partidas(formato: str = "csv", db: Session = Depends(get_db)):
    """Exportar catálogo de partidas a CSV o Excel con formato profesional."""
    partidas = db.query(Partida).order_by(Partida.categoria, Partida.subcategoria, Partida.nombre).all()

    if formato.lower() == "excel" or formato.lower() == "xlsx":
        from .services.excel_export import exportar_catalogo_partidas_excel
        buf = exportar_catalogo_partidas_excel(partidas)
        return Response(
            content=buf.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=partidas.xlsx"},
        )

    filas = [[
        "Código", "Nombre", "Descripción", "Unidad", "Precio unitario", "Categoría", "Subcategoría",
        "Coste materiales", "Coste mano de obra", "Coste complementarios", "Otros costes", "Tiempo estimado (h)", "Proveedor",
        "Rendimiento", "Desperdicio recomendado (%)", "Notas técnicas", "Última actualización de precio", "Usos",
    ]]
    for p in partidas:
        filas.append([
            p.codigo_interno, p.nombre, p.descripcion, p.unidad,
            f"{p.precio_unitario:.2f}".replace(".", ","), p.categoria, p.subcategoria,
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


@app.post("/partidas/categorias")
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


@app.post("/partidas/ajustar")
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
    return _redirect("/partidas", msg=f"Precios ajustados un {fmt_num(pct)} % en {len(partidas)} partidas.")


@app.post("/partidas/{partida_id}/usar")
def usar_partida(partida_id: int, db: Session = Depends(get_db)):
    """Punto de compatibilidad para clientes antiguos del constructor."""
    partida = db.get(Partida, partida_id)
    if partida:
        partida.usos = (partida.usos or 0) + 1
        partida.ultimo_uso = datetime.utcnow()
        db.commit()
    return {"ok": True}


@app.post("/partidas/{partida_id}/actualizar-precio")
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
        partida.precio_unitario = nuevo_precio
        partida.fecha_actualizacion_precio = datetime.utcnow()
        db.commit()
        db.refresh(partida)
    return {"ok": True, "partida": _partida_catalogo_json(partida)}


@app.post("/partidas/guardar-desde-presupuesto")
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


@app.get("/partidas/nueva", response_class=HTMLResponse)
def nueva_partida_form(request: Request, db: Session = Depends(get_db)):
    return TEMPLATES.TemplateResponse(request, "partidas/form.html", {
        "partida": None,
        "categorias": _categorias(db),
    })


@app.post("/partidas/nueva")
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


@app.get("/partidas/{partida_id}/editar", response_class=HTMLResponse)
def editar_partida_form(partida_id: int, request: Request, db: Session = Depends(get_db)):
    partida = db.get(Partida, partida_id)
    if partida is None:
        return _redirect("/partidas", error="Partida no encontrada.")
    return TEMPLATES.TemplateResponse(request, "partidas/form.html", {
        "partida": partida,
        "categorias": _categorias(db),
    })


@app.post("/partidas/{partida_id}/editar")
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
    return _redirect("/partidas", msg="Partida actualizada.")


def _desvincular_partidas_del_catalogo(db: Session, partida_ids) -> None:
    """Corta el vínculo de las líneas de presupuesto con partidas del catálogo.

    ``presupuesto_items.partida_catalogo_id`` solo recuerda de qué partida
    maestra se copió una línea; el precio ya está copiado en la propia línea.
    Borrar una partida del catálogo no debe borrar presupuestos: se anula la
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


@app.post("/partidas/{partida_id}/eliminar")
def eliminar_partida(partida_id: int, db: Session = Depends(get_db)):
    partida = db.get(Partida, partida_id)
    if partida is None:
        return _redirect("/partidas", error="Partida no encontrada.")
    referencia = partida.imagen
    _desvincular_partidas_del_catalogo(db, [partida_id])
    db.delete(partida)
    _borrar_imagen(referencia, db)
    db.commit()
    return _redirect("/partidas", msg="Partida eliminada.")

@app.post("/partidas/bulk-delete")
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
    _desvincular_partidas_del_catalogo(db, ids)
    count = 0
    referencias = set()
    for pid in ids:
        p = db.get(Partida, pid)
        if p:
            referencias.add(p.imagen)
            db.delete(p)
            count += 1
    db.flush()
    for referencia in referencias:
        _borrar_imagen(referencia, db)
    db.commit()
    return _redirect("/partidas", msg=f"Se eliminaron {count} partidas.")

@app.post("/partidas/bulk-export-selected")
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

@app.post("/partidas/bulk-move-category")
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
    db.commit()
    return _redirect("/partidas", msg=f"Se movieron {count} partidas a «{new_cat}».")


@app.post("/partidas/bulk-move-subcategory")
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
    db.commit()
    return _redirect("/partidas", msg=f"Se movieron {len(partidas)} partidas a «{categoria} · {subcategoria}».")


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

def _actualizar_usos_recursos(db: Session):
    try:
        from .services.recursos import actualizar_usos_recursos as _upd
        _upd(db)
    except Exception:
        pass


def _sincronizar_recursos(db: Session):
    """Crea los Recursos (precios unitarios) que falten desde las
    descomposiciones de partidas y presupuestos, y actualiza sus usos.

    Es idempotente (los recursos existentes no se tocan) y se ejecuta al
    abrir /recursos y tras cada guardado que pueda crear recursos nuevos.
    Así los tabs de mano de obra / materiales / etc. reflejan siempre los
    recursos que se escriben al crear o editar partidas.
    """
    try:
        from .services.recursos import sincronizar_recursos_desde_catalogo
        sincronizar_recursos_desde_catalogo(db)
        _actualizar_usos_recursos(db)
    except Exception:
        pass

@app.get("/recursos", response_class=HTMLResponse)
def listar_recursos(request: Request, q: str = "", categoria: str = "", db: Session = Depends(get_db)):
    # Sincronización automática en cada vista: crea los recursos que falten
    # desde las descomposiciones (partidas y presupuestos) y actualiza usos.
    # Es idempotente y barato; así los tabs de mano de obra / materiales /
    # complementarios / otros reflejan siempre los recursos que se escriben
    # al crear o editar partidas, sin depender del botón manual.
    _sincronizar_recursos(db)
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
    # Agrupar por categoria para la vista
    return TEMPLATES.TemplateResponse(request, "recursos/list.html", {
        "recursos": recursos,
        "q": q,
        "categoria": categoria,
        "categorias": CATEGORIAS_RECURSO,
        "etiquetas": ETIQUETAS_RECURSO,
    })

@app.get("/recursos/exportar")
def exportar_recursos(formato: str = "csv", db: Session = Depends(get_db)):
    """Exportar catálogo de recursos a CSV o Excel."""
    recursos = db.query(Recurso).order_by(Recurso.categoria, Recurso.descripcion).all()

    if formato.lower() == "excel" or formato.lower() == "xlsx":
        from .services.excel_export import exportar_catalogo_recursos_excel
        buf = exportar_catalogo_recursos_excel(recursos, ETIQUETAS_RECURSO)
        return Response(
            content=buf.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=recursos.xlsx"},
        )

    filas = [["Código", "Descripción", "Unidad", "Categoría", "Grupo", "Precio", "Usos", "Proveedor", "Última actualización"]]
    for r in recursos:
        filas.append([
            r.codigo or "",
            r.descripcion or "",
            r.unidad or "",
            ETIQUETAS_RECURSO.get(r.categoria, r.categoria),
            r.grupo or "",
            f"{r.precio:.2f}".replace(".", ","),
            r.usos or 0,
            r.proveedor or "",
            r.fecha_actualizacion_precio.isoformat() if r.fecha_actualizacion_precio else "",
        ])
    return _csv_response(filas, "recursos.csv")

@app.post("/recursos/sincronizar")
def sincronizar_recursos(db: Session = Depends(get_db)):
    from .services.recursos import sincronizar_recursos_desde_catalogo
    n = sincronizar_recursos_desde_catalogo(db)
    _actualizar_usos_recursos(db)
    return _redirect("/recursos", msg=f"Sincronizados {n} recursos desde descomposiciones existentes." if n else "No hay recursos nuevos para sincronizar.")

@app.get("/recursos/nuevo", response_class=HTMLResponse)
def nuevo_recurso_form(request: Request, _db: Session = Depends(get_db)):
    return TEMPLATES.TemplateResponse(request, "recursos/form.html", {"recurso": None, "categorias": CATEGORIAS_RECURSO, "etiquetas": ETIQUETAS_RECURSO})

@app.post("/recursos/nuevo")
def crear_recurso(
    codigo: str = Form(""),
    descripcion: str = Form(...),
    unidad: str = Form("ud"),
    categoria: str = Form("otros"),
    grupo: str = Form(""),
    precio: str = Form("0"),
    proveedor: str = Form(""),
    db: Session = Depends(get_db),
):
    if not descripcion.strip():
        return _redirect("/recursos/nuevo", error="La descripción es obligatoria.")
    if categoria not in CATEGORIAS_RECURSO:
        categoria = "otros"
    # Evitar duplicados por clave
    from .services.recursos import clave_recurso
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
        precio=max(0.0, _f(precio)),
        proveedor=proveedor.strip(),
    )
    db.add(recurso)
    db.commit()
    return _redirect("/recursos", msg="Recurso creado correctamente.")

@app.get("/recursos/{recurso_id}/editar", response_class=HTMLResponse)
def editar_recurso_form(recurso_id: int, request: Request, db: Session = Depends(get_db)):
    recurso = db.get(Recurso, recurso_id)
    if recurso is None:
        return _redirect("/recursos", error="Recurso no encontrado.")
    return TEMPLATES.TemplateResponse(request, "recursos/form.html", {"recurso": recurso, "categorias": CATEGORIAS_RECURSO, "etiquetas": ETIQUETAS_RECURSO})

@app.post("/recursos/{recurso_id}/editar")
def actualizar_recurso(
    recurso_id: int,
    codigo: str = Form(""),
    descripcion: str = Form(...),
    unidad: str = Form("ud"),
    categoria: str = Form("otros"),
    grupo: str = Form(""),
    precio: str = Form("0"),
    proveedor: str = Form(""),
    db: Session = Depends(get_db),
):
    recurso = db.get(Recurso, recurso_id)
    if recurso is None:
        return _redirect("/recursos", error="Recurso no encontrado.")
    if not descripcion.strip():
        return _redirect(f"/recursos/{recurso_id}/editar", error="La descripción es obligatoria.")
    if categoria not in CATEGORIAS_RECURSO:
        categoria = "otros"
    precio_anterior = float(recurso.precio or 0)
    nuevo_precio = max(0.0, _f(precio))
    # Verificar duplicado si cambia clave
    from .services.recursos import clave_recurso
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
    recurso.fecha_actualizacion_precio = datetime.utcnow()
    # Propagar si cambió precio
    if abs(nuevo_precio - precio_anterior) > 1e-9:
        try:
            from .services.recursos import propagar_precio_recurso
            res = propagar_precio_recurso(db, recurso, precio_anterior)
            db.commit()
            _actualizar_usos_recursos(db)
            msg = f"Recurso actualizado a {fmt_monto(nuevo_precio, 'USD')}. Afectadas {res['partidas_afectadas']} partidas y {res['filas_presupuesto']} filas de presupuestos."
            return _redirect("/recursos", msg=msg)
        except Exception as e:
            db.commit()
            return _redirect("/recursos", msg=f"Recurso actualizado (propagación parcial: {e}).")
    db.commit()
    _actualizar_usos_recursos(db)
    return _redirect("/recursos", msg="Recurso actualizado.")

@app.post("/recursos/{recurso_id}/eliminar")
def eliminar_recurso(recurso_id: int, db: Session = Depends(get_db)):
    recurso = db.get(Recurso, recurso_id)
    if recurso is None:
        return _redirect("/recursos", error="Recurso no encontrado.")
    db.delete(recurso)
    db.commit()
    return _redirect("/recursos", msg="Recurso eliminado.")

@app.post("/recursos/bulk-ajustar")
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
            from .services.recursos import propagar_precio_recurso
            res = propagar_precio_recurso(db, recurso, anterior)
            total_partidas += res.get("partidas_afectadas", 0)
            total_filas += res.get("filas_presupuesto", 0) + res.get("filas_partidas", 0)
        except Exception:
            pass
    db.commit()
    _actualizar_usos_recursos(db)
    return _redirect("/recursos", msg=f"Precios ajustados {fmt_num(pct)}% en {len(recursos)} recursos. Partidas afectadas: {total_partidas}, filas: {total_filas}.")

@app.post("/recursos/bulk-ajustar-seleccion")
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
    for recurso in recursos:
        anterior = float(recurso.precio or 0)
        if precio_fijo != "":
            try:
                nuevo = max(0.0, float(str(precio_fijo).replace(",", ".")))
            except ValueError:
                continue
        else:
            nuevo = round(anterior * (1 + porcentaje/100), 4)
        if abs(nuevo - anterior) < 1e-9:
            continue
        recurso.precio = nuevo
        recurso.fecha_actualizacion_precio = datetime.utcnow()
        try:
            from .services.recursos import propagar_precio_recurso
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

@app.post("/recursos/bulk-delete")
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



# ---------------------------------------------------------------------------
# Productos (Catálogo de materiales)
# ---------------------------------------------------------------------------

@app.get("/productos", response_class=HTMLResponse)
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
    return TEMPLATES.TemplateResponse(request, "productos/list.html", {"productos": productos, "q": q})


@app.get("/productos/exportar")
def exportar_productos(formato: str = "csv", db: Session = Depends(get_db)):
    """Exportar catálogo de productos a CSV o Excel con formato profesional."""
    productos = db.query(Producto).order_by(Producto.categoria, Producto.nombre).all()

    if formato.lower() == "excel" or formato.lower() == "xlsx":
        from .services.excel_export import exportar_catalogo_productos_excel
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


@app.post("/productos/ajustar")
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


@app.get("/productos/nuevo", response_class=HTMLResponse)
def nuevo_producto_form(request: Request, _db: Session = Depends(get_db)):
    return TEMPLATES.TemplateResponse(request, "productos/form.html", {"producto": None})


@app.post("/productos/nuevo")
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
    producto = Producto(
        nombre=nombre, imagen=principal, imagenes=json.dumps(galeria), ficha_tecnica=ficha,
        **_datos_producto_catalogo(form),
    )
    db.add(producto)
    db.commit()
    return _redirect("/productos", msg="Producto creado correctamente.")


@app.get("/productos/{producto_id}/editar", response_class=HTMLResponse)
def editar_producto_form(producto_id: int, request: Request, db: Session = Depends(get_db)):
    producto = db.get(Producto, producto_id)
    if producto is None:
        return _redirect("/productos", error="Producto no encontrado.")
    return TEMPLATES.TemplateResponse(request, "productos/form.html", {"producto": producto})


@app.post("/productos/{producto_id}/editar")
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

    datos = _datos_producto_catalogo(form)
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
    return _redirect("/productos", msg="Producto actualizado.")


@app.post("/productos/{producto_id}/eliminar")
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

@app.post("/productos/bulk-delete")
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


@app.post("/productos/bulk-export-selected")
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


@app.post("/productos/bulk-move-category")
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


# ---------------------------------------------------------------------------
# Plantillas de presupuesto
# ---------------------------------------------------------------------------

@app.get("/plantillas", response_class=HTMLResponse)
def listar_plantillas(request: Request, db: Session = Depends(get_db)):
    plantillas = db.query(Plantilla).order_by(Plantilla.nombre).all()
    return TEMPLATES.TemplateResponse(request, "plantillas/list.html", {"plantillas": plantillas})


@app.post("/plantillas")
async def guardar_plantilla(request: Request, db: Session = Depends(get_db)):
    """Guarda la estructura actual del constructor como plantilla."""
    form = await request.form()
    nombre = str(form.get("nombre", "")).strip()
    datos = str(form.get("datos", "")).strip()
    if not nombre:
        return {"ok": False, "error": "El nombre es obligatorio."}
    if not datos:
        return {"ok": False, "error": "No hay datos que guardar."}
    try:
        json.loads(datos)  # validar que sea JSON
    except ValueError:
        return {"ok": False, "error": "Datos inválidos."}
    existente = db.query(Plantilla).filter(Plantilla.nombre == nombre).first()
    if existente:
        existente.datos = datos
        plantilla = existente
    else:
        plantilla = Plantilla(nombre=nombre, datos=datos)
        db.add(plantilla)
    db.commit()
    return {"ok": True, "id": plantilla.id, "nombre": plantilla.nombre}


@app.get("/plantillas/{plantilla_id}/datos")
def plantilla_datos(plantilla_id: int, db: Session = Depends(get_db)):
    plantilla = db.get(Plantilla, plantilla_id)
    if plantilla is None:
        return {"ok": False, "error": "Plantilla no encontrada."}
    try:
        return {"ok": True, "nombre": plantilla.nombre, "capitulos": json.loads(plantilla.datos or "[]")}
    except ValueError:
        return {"ok": False, "error": "Plantilla corrupta."}


@app.post("/plantillas/{plantilla_id}/eliminar")
def eliminar_plantilla(plantilla_id: int, db: Session = Depends(get_db)):
    plantilla = db.get(Plantilla, plantilla_id)
    if plantilla is None:
        return _redirect("/plantillas", error="Plantilla no encontrada.")
    db.delete(plantilla)
    db.commit()
    return _redirect("/plantillas", msg="Plantilla eliminada.")


# ---------------------------------------------------------------------------
# Recetas / Packs de Estancia (Armado de capítulos con 1 clic - Fase 12)
# ---------------------------------------------------------------------------

@app.get("/recetas", response_class=HTMLResponse)
def listar_recetas(request: Request, db: Session = Depends(get_db)):
    recetas = db.query(RecetaEstancia).order_by(RecetaEstancia.categoria, RecetaEstancia.nombre).all()
    categorias = {}
    for r in recetas:
        cat = r.categoria or "Otros"
        if cat not in categorias:
            categorias[cat] = []
        try:
            items_cnt = len(json.loads(r.datos or "[]"))
        except Exception:
            items_cnt = 0
        r.items_cnt = items_cnt
        categorias[cat].append(r)
    return TEMPLATES.TemplateResponse(request, "recetas/list.html", {
        "recetas": recetas,
        "categorias": categorias,
    })


@app.get("/recetas/nueva", response_class=HTMLResponse)
def nueva_receta_form(request: Request, _db: Session = Depends(get_db)):
    return TEMPLATES.TemplateResponse(request, "recetas/form.html", {
        "receta": None,
        "items": [],
    })


@app.post("/recetas/nueva")
async def crear_receta(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    nombre = str(form.get("nombre", "")).strip()
    descripcion = str(form.get("descripcion", "")).strip()
    categoria = str(form.get("categoria", "")).strip() or "Baños"
    unidad_base = str(form.get("unidad_base", "")).strip() or "m²"
    try:
        cantidad_base = float(form.get("cantidad_base_default", 10.0) or 10.0)
    except ValueError:
        cantidad_base = 10.0
    datos = str(form.get("datos", "[]")).strip()
    if not nombre:
        return _redirect("/recetas/nueva", error="El nombre del pack es obligatorio.")
    try:
        json.loads(datos)
    except Exception:
        datos = "[]"
    receta = RecetaEstancia(
        nombre=nombre,
        descripcion=descripcion,
        categoria=categoria,
        unidad_base=unidad_base,
        cantidad_base_default=cantidad_base,
        datos=datos,
    )
    db.add(receta)
    db.commit()
    return _redirect("/recetas", msg="✅ Pack de estancia creado correctamente.")


@app.get("/recetas/{receta_id}/editar", response_class=HTMLResponse)
def editar_receta_form(request: Request, receta_id: int, db: Session = Depends(get_db)):
    receta = db.get(RecetaEstancia, receta_id)
    if receta is None:
        return _redirect("/recetas", error="Pack de estancia no encontrado.")
    try:
        items = json.loads(receta.datos or "[]")
    except Exception:
        items = []
    return TEMPLATES.TemplateResponse(request, "recetas/form.html", {
        "receta": receta,
        "items": items,
    })


@app.post("/recetas/{receta_id}/editar")
async def guardar_edicion_receta(request: Request, receta_id: int, db: Session = Depends(get_db)):
    receta = db.get(RecetaEstancia, receta_id)
    if receta is None:
        return _redirect("/recetas", error="Pack de estancia no encontrado.")
    form = await request.form()
    nombre = str(form.get("nombre", "")).strip()
    descripcion = str(form.get("descripcion", "")).strip()
    categoria = str(form.get("categoria", "")).strip() or "Baños"
    unidad_base = str(form.get("unidad_base", "")).strip() or "m²"
    try:
        cantidad_base = float(form.get("cantidad_base_default", 10.0) or 10.0)
    except ValueError:
        cantidad_base = 10.0
    datos = str(form.get("datos", "[]")).strip()
    if not nombre:
        return _redirect(f"/recetas/{receta_id}/editar", error="El nombre del pack es obligatorio.")
    try:
        json.loads(datos)
    except Exception:
        datos = "[]"
    receta.nombre = nombre
    receta.descripcion = descripcion
    receta.categoria = categoria
    receta.unidad_base = unidad_base
    receta.cantidad_base_default = cantidad_base
    receta.datos = datos
    db.commit()
    return _redirect("/recetas", msg="✅ Pack de estancia guardado.")


@app.post("/recetas/{receta_id}/eliminar")
def eliminar_receta(receta_id: int, db: Session = Depends(get_db)):
    receta = db.get(RecetaEstancia, receta_id)
    if receta is None:
        return _redirect("/recetas", error="Pack de estancia no encontrado.")
    db.delete(receta)
    db.commit()
    return _redirect("/recetas", msg="✅ Pack de estancia eliminado.")


@app.post("/recetas/{receta_id}/duplicar")
def duplicar_receta(receta_id: int, db: Session = Depends(get_db)):
    receta = db.get(RecetaEstancia, receta_id)
    if receta is None:
        return _redirect("/recetas", error="Pack de estancia no encontrado.")
    nueva = RecetaEstancia(
        nombre=f"{receta.nombre} (copia)",
        descripcion=receta.descripcion,
        categoria=receta.categoria,
        unidad_base=receta.unidad_base,
        cantidad_base_default=receta.cantidad_base_default,
        datos=receta.datos,
    )
    db.add(nueva)
    db.commit()
    return _redirect("/recetas", msg="✅ Pack de estancia duplicado.")


@app.post("/recetas/restaurar-demo")
def restaurar_recetas_demo(db: Session = Depends(get_db)):
    from .seeds import sembrar_recetas
    sembrar_recetas(db)
    return _redirect("/recetas", msg="✅ Presets de reforma de lujo verificados y restaurados.")


@app.get("/recetas/api/list")
def api_listar_recetas(db: Session = Depends(get_db)):
    recetas = db.query(RecetaEstancia).order_by(RecetaEstancia.categoria, RecetaEstancia.nombre).all()
    res = []
    for r in recetas:
        try:
            items = json.loads(r.datos or "[]")
        except Exception:
            items = []
        res.append({
            "id": r.id,
            "nombre": r.nombre,
            "descripcion": r.descripcion or "",
            "categoria": r.categoria or "Otros",
            "unidad_base": r.unidad_base or "m²",
            "cantidad_base_default": r.cantidad_base_default or 10.0,
            "items": items,
        })
    return {"ok": True, "recetas": res}


@app.get("/recetas/api/{receta_id}")
def api_detalle_receta(receta_id: int, db: Session = Depends(get_db)):
    r = db.get(RecetaEstancia, receta_id)
    if not r:
        return {"ok": False, "error": "No encontrado"}
    try:
        items = json.loads(r.datos or "[]")
    except Exception:
        items = []
    return {
        "ok": True,
        "receta": {
            "id": r.id,
            "nombre": r.nombre,
            "descripcion": r.descripcion or "",
            "categoria": r.categoria or "Otros",
            "unidad_base": r.unidad_base or "m²",
            "cantidad_base_default": r.cantidad_base_default or 10.0,
            "items": items,
        }
    }


@app.post("/recetas/api/guardar-desde-capitulo")
async def api_guardar_receta_capitulo(request: Request, db: Session = Depends(get_db)):
    """Guarda un capítulo del constructor como una nueva RecetaEstancia."""
    try:
        payload = await request.json()
    except Exception:
        return {"ok": False, "error": "Carga JSON inválida."}
    nombre = str(payload.get("nombre", "")).strip()
    categoria = str(payload.get("categoria", "")).strip() or "Otros"
    unidad_base = str(payload.get("unidad_base", "")).strip() or "m²"
    try:
        cantidad_base = float(payload.get("cantidad_base_default", 10.0) or 10.0)
    except ValueError:
        cantidad_base = 10.0
    calcular_coeficientes = bool(payload.get("calcular_coeficientes", True))
    items_in = payload.get("items", [])
    if not items_in:
        return {"ok": False, "error": "El capítulo no tiene partidas."}
    items_out = []
    for it in items_in:
        try:
            cant = float(it.get("cantidad", 0) or 0)
        except ValueError:
            cant = 1.0
        tipo_calc = "proporcional" if calcular_coeficientes else "fijo"
        coef = round(cant / cantidad_base, 4) if (calcular_coeficientes and cantidad_base > 0) else cant
        items_out.append({
            "nombre": str(it.get("nombre", "")).strip(),
            "descripcion": str(it.get("descripcion", "")).strip(),
            "unidad": str(it.get("unidad", "")).strip() or "und",
            "precio": float(it.get("precio", 0) or 0),
            "categoria": str(it.get("categoria", "")).strip() or "Albañilería y Revestimientos",
            "tipo_calculo": tipo_calc,
            "coeficiente": coef,
            "cantidad_fija": cant,
        })
    rec = RecetaEstancia(
        nombre=nombre or "Nuevo Pack de Estancia",
        categoria=categoria,
        unidad_base=unidad_base,
        cantidad_base_default=cantidad_base,
        datos=json.dumps(items_out, ensure_ascii=False),
    )
    db.add(rec)
    db.commit()
    return {"ok": True, "id": rec.id, "nombre": rec.nombre}
