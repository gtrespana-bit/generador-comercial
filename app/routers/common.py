"""Utilidades, plantillas y constantes compartidas por los routers (E4-001).

Reúne el bloque de imports, el entorno Jinja (``TEMPLATES``) y los helpers
que usan varios dominios. Los routers importan todo desde aquí con
``from .common import *``, de ahí el ``__all__`` final.
"""
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import quote
import base64
import csv
import hashlib
import io
import json
import logging
import math
import mimetypes
import os
import re
import shutil
import tempfile
import traceback
import unicodedata
import uuid
import zipfile

log = logging.getLogger("cotizat")
from ..logs import configurar_logs  # noqa: E402  (tras crear el logger)

configurar_logs()

from fastapi import Depends, FastAPI, Form, Request, UploadFile  # noqa: F401 (type hints)
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import UploadFile as UploadFileStarlette
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import or_
from sqlalchemy.orm import Session, load_only
from starlette.middleware.gzip import GZipMiddleware
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from ..branding import LEGAL_ENTITY, PRODUCT_NAME, SUPPORT_EMAIL, VALUE_PROPOSITION
from ..security import AuthRateLimitMiddleware, WebSecurityMiddleware
from ..database import (
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
    get_db_renovacion,
    get_operator_db,
    get_public_proposal_db,
    init_db,
    restaurar_base,
)
from ..auth import (
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
from ..models import (
    ESTADOS,
    ORIGENES_LICENCIA,
    ORIGENES_LICENCIA_ETIQUETA,
    ArchivoAlmacenado,
    Capitulo,
    Cliente,
    CompraPlan,
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
    EnlacePropuesta,
    PresupuestoItemProducto,
    Producto,
    asegurar_config,
    crear_organizacion_con_propietario,
    marcar_vencidos,
    membresias_activas,
    proximo_numero,
    proximo_numero_factura,
)
from ..services import pdf as pdf_service
from ..services.analisis import analizar_catalogo_partidas
from ..services.contrato import generar_contrato_pdf
from ..services.tiempos import calcular_tiempos_presupuesto, horas_por_unidad_descompuesto
from ..services.versions import ESTADOS_CONGELABLES, crear_version, leer_snapshot
from ..services.onboarding import (
    ErrorOnboarding,
    completar_onboarding,
    estado_recorrido_inicial,
)
from ..services.licencias import (
    DURACIONES,
    GestionLicenciaError,
    cancelar_licencia,
    crear_licencia,
    enviar_avisos_vencimiento,
    exigencia_licencia_activada,
    resumen_organizaciones,
    totales,
)
from ..services.recibo_licencia import (
    generar_recibo_licencia_pdf,
    licencia_de_compra,
    numero_recibo,
)
from ..services.propuestas import (
    DURACIONES_ENLACE,
    GestionEnlacePropuestaError,
    crear_enlace_propuesta,
    destinatarios_respuesta_propuesta,
    marcar_notificacion_respuesta,
    registrar_respuesta_propuesta,
    resolver_enlace_propuesta,
    revocar_enlace_propuesta,
)
from ..services.invitations import (
    GestionEquipoError,
    aceptar_invitacion,
    aceptar_invitacion_pendiente,
    actualizar_membresia,
    crear_invitacion,
    exigir_gestor,
    invitaciones_pendientes_para,
    revocar_invitacion,
)
from ..services.email import (
    EmailNotConfigured,
    EmailSendError,
    EmailValidationError,
    email_destino_valido,
    enviar_invitacion_por_email,
    enviar_presupuesto_por_email,
    enviar_respuesta_propuesta_por_email,
)
from ..services.importer import (
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
from ..services.instalacion_sqlite import (
    ErrorInstalacion,
    LIMITE_BYTES as LIMITE_INSTALACION_BYTES,
    analizar_instalacion,
    importar_instalacion,
)
from ..services.respaldo import (
    ErrorRespaldo,
    LIMITE_RESPALDO_BYTES,
    generar_respaldo,
)
from ..services.restauracion import analizar_respaldo, restaurar_respaldo
from ..services.exportacion import generar_exportacion
from ..services.baja import BajaError, ejecutar_baja, resumen_baja
from ..services.operacion import (
    RegistroErroresMiddleware,
    diagnostico_operacion,
)
from ..permisos import es_lectura, es_propietario, puede_gestionar
from ..utils import SIMBOLOS, fmt_fecha, fmt_monto, fmt_num, fmt_cantidad
from ..storage import (
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


def _static_version() -> str:
    """Huella corta y estable para cachear los estáticos con URLs versionadas.

    En Vercel se deriva del commit desplegado; en local, del HEAD de git. Cada
    despliegue produce una versión distinta, así que cambiar un CSS/JS cambia
    su URL y el navegador lo descarga una sola vez (inmutable).
    """
    version = os.environ.get("VERCEL_GIT_COMMIT_SHA") or os.environ.get("COTIZAT_BUILD_ID", "")
    version = version.strip()
    if version:
        return version[:12]
    try:
        import subprocess
        out = subprocess.run(
            ["git", "rev-parse", "--short=12", "HEAD"],
            cwd=str(BASE_DIR), capture_output=True, text=True, timeout=5,
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except Exception:
        pass
    return "dev"


STATIC_VERSION = _static_version()


def _asset_url(path: str) -> str:
    """URL de un recurso estático con la huella de versión (?v=...)."""
    p = str(path or "").lstrip("/")
    return f"/static/{p}?v={STATIC_VERSION}"


def cifras_catalogo() -> dict:
    """Cifras del catálogo propio para la landing y el marketing.

    Se leen de ``basedatos_partidas`` (clasificación y descompuestos) sin
    tocar la base de datos ni la sesión, y se cachean: son estáticas entre
    regeneraciones del catálogo.
    """
    from functools import lru_cache

    @lru_cache(maxsize=1)
    def _leer() -> dict:
        try:
            base = Path(__file__).resolve().parents[2] / "basedatos_partidas"
            descompuestos = base / "datos" / "descompuestos"
            clasif = json.loads(
                (base / "datos" / "clasificacion.json").read_text(encoding="utf-8")
            )
            capitulos = clasif.get("capitulos", {})
            subcapitulos = sum(len(c.get("subcapitulos", {})) for c in capitulos.values())
            apartados = sum(
                len(s.get("apartados", {}))
                for c in capitulos.values()
                for s in c.get("subcapitulos", {}).values()
            )
            n_partidas = len(list(descompuestos.glob("*.json"))) if descompuestos.is_dir() else 0
            return {
                "partidas": n_partidas,
                "partidas_txt": f"{n_partidas:,}".replace(",", "."),
                "capitulos": len(capitulos),
                "subcapitulos": subcapitulos,
                "subcapitulos_txt": f"{subcapitulos:,}".replace(",", "."),
                "apartados": apartados,
            }
        except Exception:
            # Nunca romper la aplicación por un recuento de marketing.
            return {
                "partidas": 3000,
                "partidas_txt": "3.000",
                "capitulos": 18,
                "subcapitulos": 172,
                "subcapitulos_txt": "172",
                "apartados": 0,
            }

    return _leer()


TEMPLATES.env.filters["asset"] = _asset_url
TEMPLATES.env.globals["STATIC_VERSION"] = STATIC_VERSION
TEMPLATES.env.globals.update(
    product_name=PRODUCT_NAME,
    value_proposition=VALUE_PROPOSITION,
    database_is_sqlite=DATABASE_IS_SQLITE,
    titular_legal=LEGAL_ENTITY,
    email_soporte=SUPPORT_EMAIL,
    catalogo=cifras_catalogo,
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
def _respuesta_auth_json(request: Request) -> bool:
    accept = request.headers.get("accept", "")
    return (
        request.url.path.startswith("/api/")
        or "/api/" in request.url.path
        or "application/json" in accept
        or request.headers.get("content-type", "").startswith("application/json")
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

_CAMPOS_INDICE_CATALOGO = (
    Partida.id,
    Partida.nombre,
    Partida.descripcion,
    Partida.precio_unitario,
    Partida.unidad,
    Partida.categoria,
    Partida.subcategoria,
    Partida.apartado,
    Partida.codigo_clasificacion,
    Partida.codigo_legacy,
    Partida.codigo_interno,
    Partida.codigo_externo,
    Partida.usos,
    Partida.ultimo_uso,
)

_PALABRAS_VACIAS_INDICE = frozenset({
    "para", "con", "sin", "desde", "hasta", "sobre", "entre", "incluye",
    "incluido", "incluida", "mediante", "segun", "cada", "obra", "trabajo",
    "ejecucion", "suministro", "colocacion", "formacion", "parte", "zona",
    "elemento", "sistema", "material", "existente", "terminado", "total",
})


def _texto_indice_catalogo(partida: Partida) -> str:
    """Índice compacto de sinónimos: busca sin enviar descripciones."""
    bruto = " ".join((
        partida.nombre or "",
        partida.descripcion or "",
        partida.categoria or "",
        partida.subcategoria or "",
        partida.apartado or "",
        partida.codigo_interno or "",
        partida.codigo_legacy or "",
    ))
    normal = unicodedata.normalize("NFD", bruto.lower())
    normal = "".join(c for c in normal if unicodedata.category(c) != "Mn")
    palabras = re.findall(r"[a-z0-9]+", normal)
    unicas: list[str] = []
    vistas: set[str] = set()
    for palabra in palabras:
        if len(palabra) < 3 or palabra in _PALABRAS_VACIAS_INDICE or palabra in vistas:
            continue
        vistas.add(palabra)
        unicas.append(palabra)
        if len(unicas) >= 24:
            break
    from ..services.busqueda_catalogo import alias_para_texto
    capitulo = (partida.codigo_clasificacion or partida.categoria or "")[:2]
    for alias in alias_para_texto(bruto, capitulo):
        if alias in vistas:
            continue
        vistas.add(alias)
        unicas.append(alias)
        if len(unicas) >= 40:
            break
    return " ".join(unicas)[:320]


def _partida_catalogo_indice(partida: Partida) -> dict:
    """Registro pequeño para árboles/buscadores de hasta 5.000 partidas."""
    codigo = partida.codigo_interno or partida.codigo_externo or ""
    return {
        "id": partida.id,
        "nombre": partida.nombre or "",
        "precio": partida.precio_unitario or 0.0,
        "unidad": partida.unidad or "ud",
        "categoria": partida.categoria or "99 Partidas personalizadas",
        "subcategoria": partida.subcategoria or "",
        "apartado": partida.apartado or "",
        "codigo_clasificacion": partida.codigo_clasificacion or "",
        "codigo_legacy": partida.codigo_legacy or "",
        "codigo": codigo,
        "codigo_interno": partida.codigo_interno or "",
        "codigo_externo": partida.codigo_externo or "",
        "usos": partida.usos or 0,
        "ultimo_uso": partida.ultimo_uso.isoformat() if partida.ultimo_uso else "",
        "buscable": _texto_indice_catalogo(partida),
    }


def _indice_catalogo_para_editor(db: Session) -> list[dict]:
    partidas = (
        db.query(Partida)
        .filter(Partida.oculta.is_(False))
        .options(load_only(*_CAMPOS_INDICE_CATALOGO))
        .order_by(
            Partida.categoria,
            Partida.subcategoria,
            Partida.apartado,
            Partida.codigo_interno,
            Partida.nombre,
        )
        .all()
    )
    return [_partida_catalogo_indice(partida) for partida in partidas]


def _aplicar_busqueda_catalogo(query, consulta: str):
    """Aplica AND entre palabras y OR entre sinónimos/campos."""
    from ..services.busqueda_catalogo import variantes_consulta
    grupos = variantes_consulta(consulta)
    campos = (
        Partida.nombre,
        Partida.descripcion,
        Partida.categoria,
        Partida.subcategoria,
        Partida.apartado,
        Partida.codigo_interno,
        Partida.codigo_legacy,
        Partida.proveedor,
    )
    for variantes in grupos:
        condiciones = []
        for variante in variantes:
            like = f"%{variante[:40]}%"
            condiciones.extend(campo.ilike(like) for campo in campos)
        query = query.filter(or_(*condiciones))
    return query, grupos


def _puntuar_busqueda_catalogo(partida: Partida, consulta: str, grupos: list[list[str]]) -> float:
    from ..services.busqueda_catalogo import normalizar
    nombre = normalizar(partida.nombre or "")
    ruta = normalizar(" ".join((
        partida.categoria or "", partida.subcategoria or "", partida.apartado or ""
    )))
    descripcion = normalizar(partida.descripcion or "")
    consulta_normal = normalizar(consulta)
    puntuacion = min(partida.usos or 0, 50) * 0.1
    if consulta_normal and consulta_normal in nombre:
        puntuacion += 120
    for variantes in grupos:
        mejor = 0
        for variante in variantes:
            termino = normalizar(variante)
            if not termino:
                continue
            if nombre.startswith(termino):
                mejor = max(mejor, 70)
            elif termino in nombre:
                mejor = max(mejor, 50)
            elif termino in ruta:
                mejor = max(mejor, 30)
            elif termino in descripcion:
                mejor = max(mejor, 5)
        puntuacion += mejor
    return puntuacion


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
        "apartado": partida.apartado or "",
        "codigo_clasificacion": partida.codigo_clasificacion or "",
        "codigo_legacy": partida.codigo_legacy or "",
        "catalogo_uid": partida.catalogo_uid or "",
        "es_oficial": bool(partida.es_oficial),
        "oculta": bool(partida.oculta),
        "version_alta_catalogo": partida.version_alta_catalogo or 0,
        "ruta": partida.ruta_catalogo,
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

def _actualizar_usos_recursos(db: Session):
    try:
        from ..services.recursos import actualizar_usos_recursos as _upd
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
        from ..services.recursos import sincronizar_recursos_desde_catalogo
        sincronizar_recursos_desde_catalogo(db)
        _actualizar_usos_recursos(db)
    except Exception:
        pass

# Re-exportación completa (E4-001): los routers hacen ``from .common import *``
# y reciben modelos, servicios, constantes y utilidades sin repetir el bloque
# de imports. Se incluyen también los helpers privados (prefijo ``_``).
__all__ = [name for name in globals() if not name.startswith("__")]
