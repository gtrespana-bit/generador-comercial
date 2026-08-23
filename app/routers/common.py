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
from sqlalchemy.orm import Session, joinedload, load_only, selectinload
from starlette.middleware.gzip import GZipMiddleware
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from ..branding import LEGAL_ENTITY, PRODUCT_NAME, SUPPORT_EMAIL, VALUE_PROPOSITION
from ..security import AuthRateLimitMiddleware, WebSecurityMiddleware, ip_de_request
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
    PrecioRecursoMercado,
    HistorialPrecioRecurso,
    RecetaEstancia,
    Presupuesto,
    Recurso,
    PresupuestoItem,
    PresupuestoVersion,
    Proyecto,
    PlanoObra,
    PlanoMedicion,
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
    suspender_organizacion,
    totales,
)
from ..services.recibo_licencia import (
    generar_recibo_licencia_pdf,
    licencia_de_compra,
    numero_recibo,
)
from ..services.identidad_registro import es_desechable, normalizar_email
from ..services.prueba_gratuita import (
    conceder_prueba,
    dias_de_prueba,
    prueba_activada,
    prueba_ya_usada,
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
from ..services.bc3 import (
    ErrorBC3,
    analizar_bc3,
    bc3_a_filas_cotizat,
    es_formato_bc3,
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
from ..utils import SIMBOLOS, fmt_fecha, fmt_monto, fmt_monto_iso, fmt_num, fmt_cantidad
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
try:
    from ..services.monedas import formato_iso as _formato_iso
    TEMPLATES.env.filters["money_iso"] = _formato_iso
except Exception:  # pragma: no cover
    TEMPLATES.env.filters["money_iso"] = fmt_monto_iso
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

    Se leen de ``basedatos_partidas`` (clasificación, descompuestos y cuadro
    de recursos) sin tocar la base de datos ni la sesión, y se cachean: son
    estáticas entre regeneraciones del catálogo.

    El catálogo no son solo partidas: cada partida llega descompuesta en
    recursos con precio (materiales, mano de obra y equipo), así que el
    número de líneas de precio listas para usar es ``partidas + recursos``
    y el de líneas de análisis (rendimiento × recurso) es la suma de las
    líneas de todos los descompuestos. La landing vende el conjunto.
    """
    from functools import lru_cache

    @lru_cache(maxsize=1)
    def _leer() -> dict:
        def _fallback() -> dict:
            # Nunca romper la aplicación por un recuento de marketing.
            return {
                "partidas": 3000,
                "partidas_txt": "3.000",
                "capitulos": 18,
                "subcapitulos": 172,
                "subcapitulos_txt": "172",
                "apartados": 0,
                "recursos": 392,
                "recursos_txt": "392",
                "materiales": 331,
                "mano_obra": 17,
                "equipo": 44,
                "lineas_descomp": 16127,
                "lineas_descomp_txt": "16.127",
                "lineas_precio": 3392,
                "lineas_precio_txt": "3.392",
                "packs": 0,
                "packs_partidas": 0,
            }

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
            n_partidas = 0
            lineas = 0
            if descompuestos.is_dir():
                for archivo in descompuestos.glob("*.json"):
                    try:
                        n_partidas += 1
                        lineas += len(
                            json.loads(archivo.read_text(encoding="utf-8")).get(
                                "recursos", []
                            )
                        )
                    except Exception:
                        continue
            else:
                return _fallback()
            grupos = {"materiales": 0, "mano_obra": 0, "maquinaria": 0}
            try:
                cuadro = json.loads(
                    (base / "datos" / "recursos.json").read_text(encoding="utf-8")
                )
                for clave, n in (
                    (k, len(cuadro.get(k) or {})) for k in grupos
                ):
                    grupos[clave] = n
            except Exception:
                if not n_partidas:
                    return _fallback()
                grupos = {"materiales": 0, "mano_obra": 0, "maquinaria": 0}
            n_recursos = sum(grupos.values())
            # Packs de estancia de serie (presets del modo demostración).
            packs = packs_partidas = 0
            try:
                from .. import seeds as _seeds

                recetas = list(getattr(_seeds, "RECETAS_DEMO", []) or [])
                packs = len(recetas)
                packs_partidas = sum(
                    len(json.loads(r.get("datos") or "[]")) for r in recetas
                )
            except Exception:
                pass
            lineas_precio = n_partidas + n_recursos

            def _txt(n: int) -> str:
                return f"{n:,}".replace(",", ".")

            return {
                "partidas": n_partidas,
                "partidas_txt": _txt(n_partidas),
                "capitulos": len(capitulos),
                "subcapitulos": subcapitulos,
                "subcapitulos_txt": _txt(subcapitulos),
                "apartados": apartados,
                "recursos": n_recursos,
                "recursos_txt": _txt(n_recursos),
                "materiales": grupos["materiales"],
                "mano_obra": grupos["mano_obra"],
                "equipo": grupos["maquinaria"],
                "lineas_descomp": lineas,
                "lineas_descomp_txt": _txt(lineas),
                "lineas_precio": lineas_precio,
                "lineas_precio_txt": _txt(lineas_precio),
                "packs": packs,
                "packs_partidas": packs_partidas,
            }
        except Exception:
            return _fallback()

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
    # Funciones, no valores: la prueba se puede apagar cambiando
    # COTIZAT_DIAS_PRUEBA sin volver a desplegar, y la página pública tiene que
    # enterarse en el mismo instante. Anunciar «7 días gratis» cuando la prueba
    # ya no se concede sería publicidad falsa servida por nuestra propia caché.
    dias_de_prueba=dias_de_prueba,
    hay_prueba_gratuita=prueba_activada,
)
try:
    from ..services.stripe import stripe_configurado as _stripe_configurado

    TEMPLATES.env.globals["stripe_disponible"] = _stripe_configurado
except Exception:  # pragma: no cover
    TEMPLATES.env.globals["stripe_disponible"] = lambda: False


def whatsapp_url(telefono, texto) -> str:
    """Enlace wa.me con mensaje predefinido; vacío si no hay teléfono."""
    digits = "".join(ch for ch in str(telefono or "") if ch.isdigit())
    if not digits:
        return ""
    return f"https://wa.me/{digits}?text={quote(str(texto))}"


TEMPLATES.env.filters["whatsapp"] = whatsapp_url

# Filtro de traducción de terminología por país (VE base -> CO/MX/EC/PE)
try:
    from ..services.traduccion import traducir as _traducir_termino, codigo_desde_pais as _codigo_pais
    TEMPLATES.env.filters["traducir"] = _traducir_termino
    TEMPLATES.env.globals["codigo_pais"] = _codigo_pais
except Exception:
    pass


def _simbolo_moneda(moneda: str) -> str:
    """Símbolo inequívoco de una moneda ISO para plantillas.

    Doce países de la región usan «$»: se devuelve el prefijo nacional
    (MX$, COL$, US$…) para que un importe nunca parezca de otro país.
    """
    try:
        from ..services.monedas import simbolo as _simbolo_iso

        return _simbolo_iso(moneda)
    except Exception:  # pragma: no cover - degradación defensiva
        clave = str(moneda or "USD").strip()
        if clave == "Bs":
            clave = "VES"
        return SIMBOLOS.get(clave.upper(), clave or "$")


TEMPLATES.env.filters["simbolo"] = _simbolo_moneda
# Mapa de símbolos disponible para JS del editor (moneda libre LatAm). Se
# publican los distintivos (MX$, COL$…) para que el editor no muestre «$» a
# secas en un presupuesto mexicano o colombiano.
try:  # pragma: no cover - import defensivo, igual que el filtro
    from ..services.monedas import MONEDAS as _MONEDAS_ISO, simbolo as _simbolo_iso_mapa

    TEMPLATES.env.globals["simbolos"] = {
        codigo: _simbolo_iso_mapa(codigo) for codigo in _MONEDAS_ISO
    }
except Exception:  # pragma: no cover
    TEMPLATES.env.globals["simbolos"] = SIMBOLOS


def _pais_de_nombre(nombre: str | None) -> dict:
    """Defaults del país a partir de su nombre ('Colombia' -> NIT/COP/+57…).

    Devuelve el genérico LatAm si el nombre no corresponde a un país conocido.
    Única fuente de placeholders locales para los formularios.
    """
    try:
        from ..paises import defaults_para_pais
        from ..services.traduccion import codigo_desde_pais

        return defaults_para_pais(codigo_desde_pais(nombre or "") or None)
    except Exception:
        return {}


TEMPLATES.env.globals["pais_de_nombre"] = _pais_de_nombre

# Tasas verificadas disponibles para placeholders de plantillas
# (app/services/tasa.py); None/ausente = sin sugerencia verificada.
try:
    from ..services.tasa import TASAS_SUGERIDAS as _TASAS_SUGERIDAS

    TEMPLATES.env.globals["tasas_sugeridas"] = _TASAS_SUGERIDAS
except Exception:  # pragma: no cover
    TEMPLATES.env.globals["tasas_sugeridas"] = {}

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
    """Configuración del tenant con fallback si la columna del último merge falta.

    En producción la columna ``recorrido_inicial_oculto`` (migración
    b1c2d3e4f5a6) no existía y cualquier ``SELECT configuracion.*`` explotaba
    con ``UndefinedColumn`` (PostgreSQL, ProgrammingError) o
    ``no such column`` (SQLite, OperationalError). Este helper hace la lectura
    resiliente:

    1. Intenta la query normal.
    2. Si falla por columna faltante, hace rollback, intenta un ``ALTER ...
       IF NOT EXISTS`` best-effort y reintenta.
    3. Si el ALTER no tiene permisos, hace un fallback con ``defer`` para que
       la página no quede 500: la guía seguirá visible pero la app abre.
    """
    from sqlalchemy.exc import DBAPIError, OperationalError, ProgrammingError

    try:
        cfg = db.query(Configuracion).first()
        if cfg is None:
            asegurar_config(db)
            cfg = db.query(Configuracion).first()
        return cfg
    except (ProgrammingError, OperationalError, DBAPIError, Exception) as exc:
        msg = str(exc).lower()
        is_missing = (
            "recorrido_inicial_oculto" in msg
            or "undefinedcolumn" in msg
            or "no such column" in msg
            or "no column" in msg
        )
        # No es nuestro caso: propaga tal cual (pero solo si no menciona la columna)
        if not is_missing:
            # Re-lanza solo si es un DBAPIError que no es por columna faltante
            if isinstance(exc, (ProgrammingError, OperationalError, DBAPIError)):
                raise
            # Para otras excepciones, también propaga
            raise
        try:
            db.rollback()
        except Exception:
            pass
        # Intento de auto-reparación DDL en la misma sesión (puede fallar por RLS/permisos o sintaxis)
        try:
            from sqlalchemy import text as _text

            db.execute(_text("ALTER TABLE configuracion ADD COLUMN IF NOT EXISTS recorrido_inicial_oculto BOOLEAN DEFAULT false"))
            db.commit()
            cfg = db.query(Configuracion).first()
            if cfg is None:
                asegurar_config(db)
                cfg = db.query(Configuracion).first()
            return cfg
        except Exception:
            try:
                db.rollback()
            except Exception:
                pass
        # Fallback sin la columna: defer para que el SELECT no la pida
        try:
            from sqlalchemy.orm import defer
            from sqlalchemy.exc import ProgrammingError as _PE2, OperationalError as _OE2

            cfg = db.query(Configuracion).options(defer(Configuracion.recorrido_inicial_oculto)).first()
            if cfg is None:
                # asegurar_config también haría SELECT con la columna; lo evitamos con SQL directo
                try:
                    asegurar_config(db)
                except (ProgrammingError, OperationalError, _PE2, _OE2, Exception) as e2:
                    msg2 = str(e2).lower()
                    if "recorrido_inicial_oculto" not in msg2 and "undefinedcolumn" not in msg2 and "no such column" not in msg2:
                        raise
                    try:
                        db.rollback()
                    except Exception:
                        pass
                    # Inserta fila mínima si no existe, sin tocar la columna nueva
                    from sqlalchemy import text as _text2

                    org_id = db.info.get("organizacion_id")
                    if org_id is None:
                        # fallback al espacio local 1 si no hay contexto (raro en web con RLS)
                        org_id = 1
                    # Evita duplicar si ya existe (otra transacción la creó)
                    existing = None
                    try:
                        existing = db.query(Configuracion).options(defer(Configuracion.recorrido_inicial_oculto)).first()
                    except Exception:
                        try:
                            db.rollback()
                        except Exception:
                            pass
                    if existing is None:
                        try:
                            db.execute(_text2("INSERT INTO configuracion (organizacion_id, empresa_nombre, empresa_pais) VALUES (:oid, 'Mi Empresa', 'Venezuela') ON CONFLICT DO NOTHING"), {"oid": int(org_id)})
                            db.commit()
                        except Exception:
                            try:
                                db.rollback()
                            except Exception:
                                pass
                cfg = db.query(Configuracion).options(defer(Configuracion.recorrido_inicial_oculto)).first()
            if cfg is not None:
                # Evita que el acceso posterior dispare un SELECT diferido que también fallaría
                if "recorrido_inicial_oculto" not in cfg.__dict__:
                    cfg.__dict__["recorrido_inicial_oculto"] = False
                elif cfg.__dict__.get("recorrido_inicial_oculto") is None:
                    cfg.__dict__["recorrido_inicial_oculto"] = False
                return cfg
        except Exception as fallback_exc:
            log.error("Fallback _config también falló: %s", fallback_exc)
            raise exc from fallback_exc
        raise


def _importe_en_moneda_vista(valor, presupuesto, moneda_vista: str, factor_vista: float):
    """Expresa un importe de un presupuesto en la moneda de la vista.

    Cada presupuesto congela su moneda contractual; el panel y los reportes
    agregan presupuestos de la organización y deben hacerlo en UNA sola
    moneda. El puente es USD usando la tasa congelada del propio presupuesto
    (``tipo_cambio``: unidades de la moneda contractual por USD) y la tasa de
    la organización para llegar a la moneda de la vista.

    Devuelve ``None`` cuando no hay tasa para el puente: nunca se inventa la
    conversión (el llamador excluye ese importe del agregado).
    """
    if valor is None:
        return None
    from ..utils import normalizar_moneda

    moneda_p = normalizar_moneda(presupuesto.moneda or "USD", "USD")
    vista = normalizar_moneda(moneda_vista or "USD", "USD")
    importe = float(valor)
    if moneda_p == vista:
        return importe
    if moneda_p == "USD":
        usd = importe
    else:
        try:
            tasa_p = float(presupuesto.tipo_cambio or 0)
        except (TypeError, ValueError):
            tasa_p = 0.0
        if tasa_p <= 0:
            return None
        usd = importe / tasa_p
    from ..services.tasa import tasa_convertir_precio

    return tasa_convertir_precio(usd, factor_vista)


def _opciones_partidas_presupuesto(incluir_descompuesto: bool = True):
    """Opciones de carga temprana del grafo económico de presupuestos.

    ``p.total``, ``p.subtotal``… recorren capítulos → partidas → mediciones,
    y la plantilla añade ``p.cliente``. Sin estas opciones cada acceso
    dispara consultas perezosas individuales (N+1): una lista de 25
    presupuestos multiplicaba las vueltas a la base por 4-5 por fila. Con
    ``selectinload`` el grafo completo se trae en ~5 consultas fijas.

    El descompuesto CYPE solo hace falta en ficha/PDF. El panel y los
    listados pueden omitirlo: son decenas de miles de filas extra.
    """
    opciones = [
        joinedload(Presupuesto.cliente),
        selectinload(Presupuesto.capitulos)
        .selectinload(Capitulo.partidas)
        .selectinload(PresupuestoItem.mediciones),
    ]
    if incluir_descompuesto:
        opciones.append(
            selectinload(Presupuesto.capitulos)
            .selectinload(Capitulo.partidas)
            .selectinload(PresupuestoItem.descomposicion_cype),
        )
    return tuple(opciones)


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
    """Registra uso sin inflar el contador al volver a guardar un presupuesto.

    El nombre de la línea puede venir traducido al país de la organización, así
    que la maestra se localiza por el índice que reconoce ambas formas (y por
    el id de catálogo cuando la línea lo trae).
    """
    from ..services.busqueda_catalogo import normalizar

    previos = set(nombres_previos or [])
    indice: dict[str, int] | None = None
    for pd in partidas:
        nombre = str(pd.get("nombre", "")).strip()
        if not nombre or nombre in previos:
            continue
        part = None
        catalogo_id = pd.get("catalogo_id") or pd.get("partida_id")
        if catalogo_id:
            try:
                part = db.get(Partida, int(catalogo_id))
            except (TypeError, ValueError):
                part = None
        if part is None:
            if indice is None:
                indice = _indice_nombres_catalogo(db)
            maestra_id = indice.get(normalizar(nombre))
            part = db.get(Partida, maestra_id) if maestra_id else None
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


def _indice_nombres_catalogo(db: Session) -> dict[str, int]:
    """Mapa «nombre normalizado → id» del catálogo, incluida su traducción.

    El catálogo se guarda en terminología venezolana y la interfaz lo muestra
    traducido al país de la organización (friso→pañete, capa de pega→capa de
    pegante…). El presupuesto viaja con el nombre TRADUCIDO, así que buscar la
    partida maestra por igualdad exacta de nombre fallaba siempre fuera de
    Venezuela: cada presupuesto duplicaba en el catálogo la partida que
    acababa de usar. Este índice reconoce las dos formas del nombre.
    """
    from ..services.busqueda_catalogo import normalizar
    from ..services.traduccion import codigo_desde_pais, traducir

    try:
        codigo = codigo_desde_pais(getattr(_config(db), "empresa_pais", ""))
    except Exception:  # pragma: no cover - sin configuración utilizable
        try:
            db.rollback()
        except Exception:
            pass
        codigo = ""
    indice: dict[str, int] = {}
    for pid, nombre in db.query(Partida.id, Partida.nombre).all():
        clave = normalizar(nombre or "")
        if clave:
            indice.setdefault(clave, pid)
        if codigo:
            clave_traducida = normalizar(traducir(nombre or "", codigo))
            if clave_traducida:
                indice.setdefault(clave_traducida, pid)
    return indice


def _vincular_partidas_catalogo(db: Session, presupuesto: Presupuesto):
    """Completa el vínculo con la partida maestra tras guardar el catálogo.

    Las líneas creadas a mano en un presupuesto se convierten en partidas del
    catálogo durante el guardado, pero en ese momento todavía no tenían id de
    catálogo. Esta pasada lo asigna por nombre (el del catálogo o el traducido
    al país de la organización) sin modificar el precio propio de la línea.
    """
    from ..services.busqueda_catalogo import normalizar

    pendientes = [
        p for cap in presupuesto.capitulos for p in cap.partidas
        if not p.partida_catalogo_id and str(p.nombre or "").strip()
    ]
    if not pendientes:
        return
    indice = _indice_nombres_catalogo(db)
    for item in pendientes:
        maestra_id = indice.get(normalizar(item.nombre or ""))
        if maestra_id:
            item.partida_catalogo_id = maestra_id


def _guardar_en_catalogos(db: Session, partidas: list, imagenes_guardadas: dict,
                          moneda=None, tasa=None):
    """Guarda automáticamente en los catálogos las partidas y los productos
    nuevos escritos en el formulario (para poder reutilizarlos a futuro).

    - Partida nueva (nombre que no existe en el catálogo, ni en su forma
      traducida al país de la organización) → se crea con su descripción,
      unidad, precio y categoría.
    - Producto nuevo (nombre que no existe en la base de datos de productos)
      → se crea con su precio, unidad, categoría e imagen.
    Los que ya existen no se modifican.

    Moneda: el presupuesto se edita en su moneda contractual (COP, MXN…) y el
    catálogo se guarda SIEMPRE en la moneda base (USD). Sin deshacer la
    conversión, un presupuesto colombiano escribía «15.299 COP» como si fueran
    dólares y la siguiente vez que se usaba esa partida el editor la volvía a
    multiplicar por la tasa: 47.000.000 COP/m² por demoler un piso.
    """
    _mon_cat, factor = _contexto_moneda(db, moneda, tasa)

    def _base(valor):
        return _a_moneda_base(float(valor or 0.0), factor)

    from ..services.busqueda_catalogo import normalizar

    # La sesión trabaja sin autoflush: recordar las altas de este mismo
    # formulario evita chocar con la restricción UNIQUE si una partida o un
    # producto se repite en dos líneas antes del primer commit.
    indice_catalogo: dict[str, int] | None = None
    partidas_nuevas = set()
    productos_nuevos = set()
    for i, pd in enumerate(partidas):
        nombre = str(pd.get("nombre", "")).strip()
        clave = normalizar(nombre)
        # Una línea que viene del catálogo ya tiene su maestra: no se duplica
        # aunque el usuario le haya retocado el texto.
        ya_del_catalogo = bool(pd.get("catalogo_id") or pd.get("partida_id"))
        if nombre and clave not in partidas_nuevas and not ya_del_catalogo:
            if indice_catalogo is None:
                indice_catalogo = _indice_nombres_catalogo(db)
            if clave not in indice_catalogo:
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
                    precio_unitario=_base(precio_base),
                    unidad=str(pd.get("unidad", "ud")).strip() or "ud",
                    categoria=str(pd.get("categoria", "General")).strip() or "General",
                    codigo_interno=str(pd.get("codigo") or pd.get("codigo_interno") or "").strip(),
                    coste_materiales=_base(pd.get("coste_materiales", 0.0)),
                    coste_mano_obra=_base(pd.get("coste_mano_obra", 0.0)),
                    coste_complementarios=_base(pd.get("coste_complementarios", 0.0)),
                    coste_otros=_base(pd.get("coste_otros", 0.0)),
                    desperdicio_recomendado_pct=pd.get("desperdicio_pct", 0.0) or 0.0,
                ))
                partidas_nuevas.add(clave)

        prod_nombre = str(pd.get("prod_nombre", "")).strip()
        if (prod_nombre and prod_nombre not in productos_nuevos
                and not db.query(Producto).filter(Producto.nombre == prod_nombre).first()):
            imagen = imagenes_guardadas.get(i) or str(pd.get("prod_imagen_actual", "")).strip()
            coste_producto = pd.get("prod_coste")
            db.add(Producto(
                nombre=prod_nombre,
                descripcion="",
                precio_unitario=_base(pd.get("prod_precio") or 0.0),
                precio_compra=(_base(coste_producto) if coste_producto not in (None, "") else None),
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
    Partida.coste_materiales,
    Partida.coste_mano_obra,
    Partida.coste_complementarios,
    Partida.coste_otros,
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
        "moneda": getattr(partida, "moneda", None) or "USD",
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
        # Costes para que el editor calcule el beneficio en la MISMA moneda
        # que el precio (ambos convertidos con el mismo factor).
        "coste_materiales": partida.coste_materiales or 0.0,
        "coste_mano_obra": partida.coste_mano_obra or 0.0,
        "coste_complementarios": partida.coste_complementarios or 0.0,
        "coste_otros": partida.coste_otros or 0.0,
    }


def _etiquetas_catalogo_traducidas(db: Session, textos: list[str]) -> list[str]:
    """Traduce etiquetas del árbol al país de la organización."""
    try:
        from ..services.traduccion import codigo_desde_pais as _codigo, traducir as _trad

        codigo = _codigo(getattr(_config(db), "empresa_pais", ""))
        if not codigo:
            return textos
        return [_trad(t or "", codigo) if t else t for t in textos]
    except Exception:
        return textos


def _arbol_catalogo_editor(db: Session) -> dict:
    """Esqueleto capítulo → subcapítulo → apartado con recuentos, sin hojas."""
    from sqlalchemy import func as _func

    filas = (
        db.query(
            Partida.categoria,
            Partida.subcategoria,
            Partida.apartado,
            _func.count(Partida.id),
        )
        .filter(Partida.oculta.is_(False))
        .group_by(Partida.categoria, Partida.subcategoria, Partida.apartado)
        .all()
    )
    etiquetas = []
    for cat, sub, apt, _n in filas:
        etiquetas.extend([cat or "", sub or "", apt or ""])
    trad = _etiquetas_catalogo_traducidas(db, etiquetas)
    caps: dict[str, dict] = {}
    i = 0
    total = 0
    for cat, sub, apt, n in filas:
        n = int(n or 0)
        total += n
        cat_t, sub_t, apt_t = trad[i], trad[i + 1], trad[i + 2]
        i += 3
        clave_c = cat or ""
        clave_s = sub or ""
        clave_a = apt or ""
        cap = caps.get(clave_c)
        if cap is None:
            cap = {
                "clave": clave_c,
                "nombre": cat_t or "99 Partidas personalizadas",
                "total": 0,
                "subs": {},
            }
            caps[clave_c] = cap
        cap["total"] += n
        subn = cap["subs"].get(clave_s)
        if subn is None:
            subn = {
                "clave": clave_s,
                "nombre": sub_t or "99.01 General",
                "total": 0,
                "apartados": [],
            }
            cap["subs"][clave_s] = subn
        subn["total"] += n
        subn["apartados"].append({
            "clave": clave_a,
            "nombre": apt_t or "99.01.01 Trabajos diversos",
            "total": n,
        })
    capitulos = []
    for cap in sorted(caps.values(), key=lambda c: c["nombre"] or ""):
        subs = []
        for sub in sorted(cap["subs"].values(), key=lambda s: s["nombre"] or ""):
            sub["apartados"] = sorted(sub["apartados"], key=lambda a: a["nombre"] or "")
            subs.append(sub)
        capitulos.append({
            "clave": cap["clave"],
            "nombre": cap["nombre"],
            "total": cap["total"],
            "subs": subs,
        })
    return {"capitulos": capitulos, "total": total}


def _hojas_catalogo_editor(
    db: Session,
    categoria: str = "",
    subcategoria: str = "",
    apartado: str = "",
    moneda: str | None = None,
    tasa: float | None = None,
) -> list[dict]:
    """Hojas de un apartado del árbol, ya convertidas a la moneda del editor."""
    q = (
        db.query(Partida)
        .filter(Partida.oculta.is_(False))
        .options(load_only(*_CAMPOS_INDICE_CATALOGO))
    )
    if categoria:
        q = q.filter(Partida.categoria == categoria)
    else:
        q = q.filter(or_(Partida.categoria.is_(None), Partida.categoria == ""))
    if subcategoria:
        q = q.filter(Partida.subcategoria == subcategoria)
    else:
        q = q.filter(or_(Partida.subcategoria.is_(None), Partida.subcategoria == ""))
    if apartado:
        q = q.filter(Partida.apartado == apartado)
    else:
        q = q.filter(or_(Partida.apartado.is_(None), Partida.apartado == ""))
    partidas = q.order_by(Partida.codigo_interno, Partida.nombre).all()
    try:
        from ..services.tasa import factor_conversion_local, tasa_convertir_precio
        from ..services.traduccion import codigo_desde_pais as _codigo, traducir as _trad

        _cfg = _config(db)
        _cod = _codigo(getattr(_cfg, "empresa_pais", ""))
        if moneda is None:
            moneda = getattr(_cfg, "moneda_default", "USD")
        if tasa is None:
            tasa = getattr(_cfg, "tasa_cambio", None)
        _factor = factor_conversion_local(moneda, tasa)
        out = []
        for _pp in partidas:
            _d = _partida_catalogo_indice(_pp)
            if _cod:
                _d["nombre"] = _trad(_d.get("nombre", ""), _cod)
                _d["categoria"] = _trad(_d.get("categoria", ""), _cod)
                _d["subcategoria"] = _trad(_d.get("subcategoria", ""), _cod)
                _d["apartado"] = _trad(_d.get("apartado", ""), _cod)
            _d["moneda"] = str(moneda or "USD").strip().upper() or "USD"
            if _factor != 1.0:
                _d["precio"] = tasa_convertir_precio(_d.get("precio", 0), _factor)
                for _k in ("coste_materiales", "coste_mano_obra", "coste_complementarios", "coste_otros"):
                    _d[_k] = tasa_convertir_precio(_d.get(_k, 0), _factor)
            out.append(_d)
        return out
    except Exception:
        return [_partida_catalogo_indice(p) for p in partidas]


def _persistir_total_calculado(presupuesto) -> None:
    """Congela el total comercial en la fila del presupuesto."""
    from ..services.calculations import calcular_totales

    try:
        presupuesto.total_calculado = float(calcular_totales(presupuesto).total)
    except Exception:
        pass


def _indice_catalogo_para_editor(db: Session, moneda: str | None = None, tasa: float | None = None) -> list[dict]:
    """Índice ligero del catálogo para el editor de presupuestos.

    Traduce terminología (nombre, categoría, subcategoría, apartado) al país
    de la organización y convierte TODOS los importes (precio y costes) a la
    moneda objetivo con el MISMO factor, para que el beneficio se calcule
    entre cifras comparables y nunca entre USD y moneda local mezclados.

    `moneda`/`tasa` son la moneda y la tasa del presupuesto en edición; si no
    se indican se usan los defaults de la organización.
    """
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
    try:
        from ..services.tasa import factor_conversion_local, tasa_convertir_precio
        from ..services.traduccion import codigo_desde_pais as _codigo, traducir as _trad

        _cfg = _config(db)
        _cod = _codigo(getattr(_cfg, "empresa_pais", ""))
        if moneda is None:
            moneda = getattr(_cfg, "moneda_default", "USD")
        if tasa is None:
            tasa = getattr(_cfg, "tasa_cambio", None)
        _factor = factor_conversion_local(moneda, tasa)
        out = []
        for _pp in partidas:
            _d = _partida_catalogo_indice(_pp)
            if _cod:
                # Traducción VE->país de todo lo visible (nombre y categorías)
                _d["nombre"] = _trad(_d.get("nombre", ""), _cod)
                _d["categoria"] = _trad(_d.get("categoria", ""), _cod)
                _d["subcategoria"] = _trad(_d.get("subcategoria", ""), _cod)
                _d["apartado"] = _trad(_d.get("apartado", ""), _cod)
            # La moneda del registro es la de la vista: el editor la usa para
            # etiquetar el importe y no puede decir «USD» sobre pesos.
            _d["moneda"] = str(moneda or "USD").strip().upper() or "USD"
            if _factor != 1.0:
                # Precio y costes en la MISMA moneda local: sin mezclar USD/COP
                _d["precio"] = tasa_convertir_precio(_d.get("precio", 0), _factor)
                for _k in ("coste_materiales", "coste_mano_obra", "coste_complementarios", "coste_otros"):
                    _d[_k] = tasa_convertir_precio(_d.get(_k, 0), _factor)
            if _cod:
                # Añade términos traducidos al índice buscable para que
                # «pañete» encuentre «friso» y «cimentaciones» encuentre
                # «fundaciones» (búsqueda por el idioma local)
                try:
                    import re as _re
                    import unicodedata as _ucd

                    _trad_bus = _trad(
                        _pp.nombre + " " + (_pp.descripcion or "") + " "
                        + (_pp.categoria or "") + " " + (_pp.subcategoria or ""),
                        _cod,
                    )

                    def _norma(s):
                        s = _ucd.normalize("NFD", s.lower())
                        return "".join(c for c in s if _ucd.category(c) != "Mn")

                    _orig_norm = set(_re.findall(r"[a-z0-9]+", _norma(_d.get("buscable", ""))))
                    for _w in _re.findall(r"[a-z0-9]+", _norma(_trad_bus)):
                        if len(_w) >= 3 and _w not in _orig_norm:
                            _d["buscable"] = (_d["buscable"] + " " + _w)[:380]
                            _orig_norm.add(_w)
                except Exception:
                    pass
            out.append(_d)
        return out
    except Exception:
        pass
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


# ---------------------------------------------------------------------------
# Contexto monetario del editor
#
# El catálogo (partidas, productos y recursos) se guarda en la moneda base
# (USD). Lo que el usuario ve dentro de un presupuesto está en la moneda
# contractual de ese presupuesto. Todo lo que cruza esa frontera —fichas,
# descomposiciones, guardados hacia el catálogo— tiene que convertirse con el
# MISMO factor y en el sentido correcto, o el editor acaba mezclando pesos con
# dólares (total en MXN, precios unitarios en USD).
# ---------------------------------------------------------------------------

def _contexto_moneda(db: Session, moneda=None, tasa=None) -> tuple[str, float]:
    """Devuelve (moneda_visible, factor USD→moneda) para una petición.

    La moneda del presupuesto manda sobre la preferencia de la organización.
    Nunca se inventa una tasa: si se pide una moneda distinta a la de la
    organización sin tasa, el factor es 1.0 y los importes se quedan en la
    moneda base en lugar de mostrar una conversión falsa.
    """
    from ..services.tasa import factor_conversion_local

    try:
        cfg = _config(db)
    except Exception:  # pragma: no cover - sin configuración aún
        try:
            db.rollback()
        except Exception:
            pass
        cfg = None
    moneda_cfg = str(getattr(cfg, "moneda_default", "") or "USD").strip().upper()
    tasa_cfg = getattr(cfg, "tasa_cambio", None)

    codigo = str(moneda or "").strip().upper()
    if not codigo:
        codigo, tasa = moneda_cfg, tasa_cfg
    else:
        try:
            tasa = float(tasa) if tasa not in (None, "") else None
        except (TypeError, ValueError):
            tasa = None
        if not tasa and codigo == moneda_cfg:
            tasa = tasa_cfg
    from ..utils import normalizar_moneda

    vista = normalizar_moneda(codigo or "USD", "USD")
    factor = factor_conversion_local(vista, tasa)
    if factor == 1.0 and vista not in ("USD", "PAB"):
        # Sin tasa válida no se inventa la conversión y tampoco se etiqueta
        # con una divisa que los importes no tienen: se muestra la base
        # (USD). Antes una organización con moneda local sin tasa veía
        # «MXN» sobre cifras guardadas en dólares.
        return "USD", 1.0
    return vista, factor


def _convertir(valor, factor: float):
    """Convierte un importe si es numérico; deja intacto lo que no lo sea."""
    from ..services.tasa import tasa_convertir_precio

    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        return valor
    return tasa_convertir_precio(valor, factor)


#: Campos monetarios de la ficha de una partida del catálogo.
CAMPOS_MONETARIOS_PARTIDA = (
    "precio",
    "precio_unitario",
    "coste_materiales",
    "coste_mano_obra",
    "coste_complementarios",
    "coste_otros",
)


def _ficha_en_moneda(ficha: dict, moneda: str, factor: float) -> dict:
    """Pasa una ficha del catálogo (USD) a la moneda visible del editor.

    Convierte precio, costes y **las filas de la descomposición**: son los
    precios unitarios con los que el editor recalcula la partida, y dejarlos
    en USD hacía que el total y su desglose hablaran monedas distintas.
    """
    ficha = dict(ficha or {})
    ficha["moneda"] = str(moneda or "USD").upper()
    if factor and factor != 1.0:
        for campo in CAMPOS_MONETARIOS_PARTIDA:
            if campo in ficha:
                ficha[campo] = _convertir(ficha[campo], factor)
        descomposicion = ficha.get("descomposicion")
        if isinstance(descomposicion, dict):
            filas = [
                dict(fila) if isinstance(fila, dict) else fila
                for fila in descomposicion.get("filas", [])
            ]
            for fila in filas:
                if not isinstance(fila, dict):
                    continue
                for campo in ("precio", "importe", "coste_unitario"):
                    if campo in fila:
                        fila[campo] = _convertir(fila[campo], factor)
            ficha["descomposicion"] = dict(descomposicion, filas=filas)
    return ficha


def _tarifa_hora_en_moneda(db: Session, cfg, moneda=None, tasa=None) -> float:
    """Tarifa media de mano de obra en la moneda de un presupuesto.

    La tarifa se configura en la moneda de la organización y sirve para estimar
    horas a partir del coste de mano de obra. Si el presupuesto usa otra moneda
    —USD dentro de una empresa mexicana, por ejemplo— habría que dividir pesos
    entre dólares y la estimación de horas saldría multiplicada por la tasa.
    """
    tarifa = float(getattr(cfg, "tarifa_hora_media", 0) or 8.0)
    _mon_cfg, factor_cfg = _contexto_moneda(db)
    _mon_doc, factor_doc = _contexto_moneda(db, moneda, tasa)
    if factor_cfg == factor_doc or not factor_cfg:
        return tarifa
    return max(0.0, tarifa / factor_cfg * factor_doc)


def _a_moneda_base(valor, factor: float):
    """Camino inverso: de la moneda visible del editor a la base del catálogo.

    Sin esto, guardar «3.675 MXN» desde el editor escribía 3.675 **USD** en el
    catálogo y multiplicaba el precio por la tasa en cada edición.
    """
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        return valor
    if not factor or factor == 1.0:
        return valor
    try:
        return max(0.0, float(valor) / float(factor))
    except (TypeError, ValueError, ZeroDivisionError):  # pragma: no cover
        return valor


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
        try:
            db.rollback()
        except Exception:
            pass


#: Control del intervalo mínimo entre sincronizaciones de recursos por
#: organización (ver :func:`_sincronizar_recursos`). ``time`` y ``threading``
#: se importan aquí para no ensanchar el bloque superior.
import threading as _threading
import time as _time

_SYNC_RECURSOS_ULTIMA: dict = {}
_SYNC_RECURSOS_BLOQUEO = _threading.Lock()


def _sincronizar_recursos(db: Session, forzar: bool = True):
    """Crea los Recursos (precios unitarios) que falten desde las
    descomposiciones de partidas y presupuestos, y actualiza sus usos.

    Es idempotente (los recursos existentes no se tocan) y se ejecuta al
    abrir /recursos y tras cada guardado que pueda crear recursos nuevos.
    Así los tabs de mano de obra / materiales / etc. reflejan siempre los
    recursos que se escriben al crear o editar partidas.

    ``forzar=False`` (usado al abrir la vista) respeta un intervalo mínimo
    por organización: la sincronización recorre todos los descompuestos del
    catálogo y, con la base remota del despliegue web, ejecutarla en cada
    visita hacía la página lentísima. Los guardados la fuerzan siempre para
    que un recurso recién escrito aparezca de inmediato.
    """
    if not forzar:
        try:
            ttl_sync = float(os.environ.get("COTIZAT_SYNC_RECURSOS_TTL", "600"))
        except (TypeError, ValueError):
            ttl_sync = 600.0
        if ttl_sync > 0:
            clave_sync = (db.info.get("organizacion_id") or 0, id(db.get_bind()))
            ahora_sync = _time.monotonic()
            with _SYNC_RECURSOS_BLOQUEO:
                if ahora_sync - _SYNC_RECURSOS_ULTIMA.get(clave_sync, 0.0) < ttl_sync:
                    return
                _SYNC_RECURSOS_ULTIMA[clave_sync] = ahora_sync
    try:
        from ..services.recursos import sincronizar_recursos_desde_catalogo
        sincronizar_recursos_desde_catalogo(db)
        _actualizar_usos_recursos(db)
    except Exception:
        # Sin rollback, psycopg deja la transacción abortada y el
        # ``SELECT`` de /recursos revienta con InFailedSqlTransaction.
        log.exception("No se pudieron sincronizar los recursos del catálogo.")
        try:
            db.rollback()
        except Exception:
            pass


# Re-exportación completa (E4-001): los routers hacen ``from .common import *``
# y reciben modelos, servicios, constantes y utilidades sin repetir el bloque
# de imports. Se incluyen también los helpers privados (prefijo ``_``).
__all__ = [name for name in globals() if not name.startswith("__")]
