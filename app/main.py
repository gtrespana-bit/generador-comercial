"""CotizaT — aplicación local de presupuestos de obra (FastAPI).

Ejecutar con:  python run.py   (o: uvicorn app.main:app)

Las rutas de negocio viven en ``app/routers/`` (E4-001): este módulo solo
monta la aplicación, los middlewares, los manejadores de excepción, los
estáticos y las rutas de sistema (salud y favicon).
"""
import logging
import zipfile
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

log = logging.getLogger("cotizat")
from .logs import configurar_logs  # noqa: E402  (tras crear el logger)

configurar_logs()

from fastapi import FastAPI, Request  # noqa: E402
from fastapi.exceptions import RequestValidationError  # noqa: E402
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from starlette.middleware.gzip import GZipMiddleware  # noqa: E402
from starlette.types import ASGIApp, Message, Receive, Scope, Send  # noqa: E402

from .auth import (  # noqa: E402
    AuthError,
    AuthenticationRequired,
    AuthNotConfigured,
    OrganizationAccessDenied,
    OrganizationRequired,
    RefreshedAuthCookieMiddleware,
)
from .branding import PRODUCT_NAME  # noqa: E402
from .database import (  # noqa: E402
    BACKUPS_DIR,
    BASE_DIR,
    DATABASE_IS_SQLITE,
    PRIVATE_STORAGE_DIR,
    UPLOADS_DIR,
    copia_seguridad_sqlite,
    init_db,
)
from .models import LicenciaSuspendidaError, PermisoOrganizacionError  # noqa: E402
from .security import AuthRateLimitMiddleware, WebSecurityMiddleware, confia_en_proxy  # noqa: E402
from .services.invitations import GestionEquipoError  # noqa: E402
from .services.operacion import RegistroErroresMiddleware  # noqa: E402
from .storage import StorageError  # noqa: E402

from .routers import (  # noqa: E402
    admin,
    admin_paginas,
    auth,
    clientes,
    configuracion,
    ia,
    inicio,
    pagos,
    partidas,
    plantillas,
    planos,
    presupuestos,
    productos,
    publico,
    recetas,
    recursos,
)
from .routers.common import IMPORTS_DIR, TEMPLATES, UPLOADS  # noqa: E402

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
        # En Vercel solo /tmp es escribible. Las importaciones CYPE intermedias
        # pueden vivir ahí el tiempo de la petición.
        from pathlib import Path as _Path
        import os as _os
        from .routers import common as _common

        tmp_imports = _Path(_os.environ.get("TMPDIR") or "/tmp") / "cotizat_imports_cype"
        try:
            tmp_imports.mkdir(parents=True, exist_ok=True)
            _common.IMPORTS_DIR = tmp_imports
            log.warning(
                "imports_cype redirigido a %s (sistema de archivos de solo lectura).",
                tmp_imports,
            )
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
    # Misma interpretación de COTIZAT_TRUST_PROXY que confia_en_proxy():
    # una única fuente de verdad para la IP del rate-limit y la de auditoría.
    trust_forwarded_for=confia_en_proxy(),
)
app.add_middleware(WebSecurityMiddleware, enforce_csrf=not DATABASE_IS_SQLITE)
# Añadido el último para quedar en la capa exterior: así ve cualquier
# excepción no manejada de las rutas y del resto de middlewares (E3-024).
app.add_middleware(RegistroErroresMiddleware)
# Compresión gzip de HTML/CSS/JS/JSON: la página de partidas (~5 MB sin
# comprimir) viaja a una fracción de su tamaño y la carga se percibe mucho
# más rápida. Queda en la capa más exterior para envolver el resto.
# Se excluyen los binarios ya comprimidos (PDF, Office, imágenes, fuentes):
# volver a comprimirlos solo consume CPU sin reducir el tamaño.
app.add_middleware(
    GZipMiddleware,
    minimum_size=500,
    exclude_content_types=(
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
    ),
)


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


class _StaticFilesConCaché(StaticFiles):
    """Sirve /static con cabeceras de caché correctas.

    Los navegadores revalidan (``max-age=0, must-revalidate``, con ETag que ya
    añade StaticFiles) para no servir nunca una hoja o script desactualizado
    tras un despliegue. La CDN compartida (Vercel) puede cachear hasta un año
    (``s-maxage``) y responder desde el borde con ``stale-while-revalidate``,
    evitando que cada recurso dispare una invocación serverless en frío.
    """

    async def get_response(self, path: str, scope: Scope):
        response = await super().get_response(path, scope)
        query = scope.get("query_string", b"").decode("latin-1")
        if "v=" in query:
            # URL versionada (huella de despliegue): el contenido no cambia
            # para una versión dada, así que el navegador la cachea para
            # siempre y no vuelve a revalidar jamás.
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        else:
            response.headers["Cache-Control"] = (
                "public, max-age=0, must-revalidate, "
                "s-maxage=31536000, stale-while-revalidate=604800"
            )
        return response


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
app.mount("/static", _StaticFilesConCaché(directory=str(BASE_DIR / "app" / "static")), name="static")


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


@app.exception_handler(RequestValidationError)
async def _validacion_peticion(request: Request, exc: RequestValidationError):
    """Un POST HTML con id inválido no debe devolver JSON crudo al navegador."""
    if _respuesta_auth_json(request):
        return JSONResponse({"detail": exc.errors()}, status_code=422)
    destino = request.headers.get("referer") or "/presupuestos"
    if "presupuesto_id" in str(exc.errors()):
        return RedirectResponse(
            destino.split("?")[0] + "?error=" + quote("No se pudo guardar: el presupuesto no tiene un identificador válido. Usa «Nuevo presupuesto»."),
            status_code=303,
        )
    return RedirectResponse(
        destino.split("?")[0] + "?error=" + quote("Los datos enviados no son válidos."),
        status_code=303,
    )


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
# Routers por dominio (E4-001)
# ---------------------------------------------------------------------------
app.include_router(auth.router)
app.include_router(publico.router)
app.include_router(pagos.router)
app.include_router(admin.router)
# Las pantallas del panel (seis áreas con pestañas) van junto a sus acciones:
# `admin` son las acciones y los cron, `admin_paginas` son las lecturas.
app.include_router(admin_paginas.router)
app.include_router(inicio.router)
app.include_router(clientes.router)
app.include_router(presupuestos.router)
app.include_router(planos.router)
app.include_router(configuracion.router)
app.include_router(partidas.router)
app.include_router(productos.router)
app.include_router(recursos.router)
app.include_router(plantillas.router)
app.include_router(recetas.router)
app.include_router(ia.router)


# ---------------------------------------------------------------------------
# Re-exportación de compatibilidad (E4-001)
# ---------------------------------------------------------------------------
# Algunas pruebas y ``desktop.py`` importan símbolos desde ``app.main``. Estas
# referencias se conservan aquí para no romperlas mientras los llamadores
# migran a ``app.routers.*``.
from .services import pdf as pdf_service  # noqa: F401, E402
from .services.email import EmailSendError  # noqa: F401, E402
from .routers.auth import crear_organizacion_web  # noqa: F401, E402
from .routers.common import (  # noqa: F401, E402
    _borrar_imagen,
    _f,
    _next_seguro,
    _normalizar_referencia_imagen,
)
from .routers.inicio import actualizar_presupuestos_vencidos  # noqa: F401, E402
from .routers.partidas import (  # noqa: F401, E402
    actualizar_precio_partida_desde_presupuesto,
    eliminar_partida,
    guardar_partida_desde_presupuesto,
    restaurar_partida,
)
from .routers.presupuestos import (  # noqa: F401, E402
    _leer_formulario_presupuesto,
    _montar_presupuesto,
    actualizar_presupuesto,
    confirmar_importacion_presupuesto,
    crear_factura,
    crear_presupuesto,
    guardar_borrador_presupuesto,
    leer_borrador_presupuesto,
)
from .routers.publico import descargar_archivo_privado  # noqa: F401, E402
