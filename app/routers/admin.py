"""Panel de operador: licencias y diagnóstico operativo (excepción multi-tenant)."""  # E4-001 — router por dominio

import hmac

from fastapi import APIRouter

from .common import *  # noqa: F401,F403  (re-exporta modelos, servicios y utilidades)
from ..database import get_cron_db
from ..datos_pago import PLANES
from ..services import telemetria
from ..services.audit_admin import (
    ACCIONES_LECIBLES,
    resumen_auditoria_admin,
    registrar_evento_admin,
)
from ..services.operadores_admin import (
    GestionEquipoError,
    activar_operador,
    cambiar_rol_operador,
    crear_operador,
    exigir_superadmin,
    listar_operadores,
    suspender_operador,
)
from ..services.panel_busqueda import buscar_global
from ..services.panel_finanzas import resumen_financiero
from ..services.panel_notificaciones import notificaciones_admin
from ..services.web_admin import (
    ESTADOS_CRM_ETIQUETA,
    GestionWebError,
    NIVELES_AVISO,
    TIPOS_AVISO,
    alternar_aviso,
    alternar_release,
    claves_contenido_disponibles,
    crear_api_key,
    crear_aviso,
    crear_release,
    descartar_contenido,
    eliminar_vista,
    guardar_contenido,
    guardar_crm,
    guardar_vista,
    listar_api_keys,
    listar_avisos,
    listar_crm,
    listar_flags,
    listar_releases,
    listar_contenido,
    listar_vistas,
    publicar_contenido,
    resumen_crm,
    revocar_api_key,
)
from ..services.salud_catalogo import analizar_salud_catalogo
from ..models import ROLES_OPERADOR, ROLES_OPERADOR_ETIQUETA

router = APIRouter()

#: Ruta del trabajo programado de Vercel (vercel.json → `crons`). Un solo
#: punto de verdad: `tests/test_vercel_cron_config.py` comprueba que la ruta
#: declarada en vercel.json coincide con esta, y /readyz lo publica.
CRON_RECORDATORIOS_PATH = "/api/cron/recordatorios-vencimiento"

#: Ruta del mantenimiento diario (respaldo automático E4-021 + verificación
#: con alerta E4-023). También declarada en vercel.json → `crons`; el plan
#: Hobby admite hasta 2 trabajos diarios, Pro hasta 40.
CRON_MANTENIMIENTO_PATH = "/api/cron/mantenimiento"

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


def _auditar_admin(
    db: Session,
    request: Request,
    *,
    accion: str,
    entidad: str = "",
    entidad_id: int | None = None,
    organizacion_id: int | None = None,
    detalle: dict | None = None,
    resultado: str = "ok",
) -> None:
    """Anota la acción del operador sin romper el flujo principal (A2)."""
    from ..services.prueba_gratuita import hash_ip

    registrar_evento_admin(
        db,
        accion=accion,
        operador_email=str(db.info.get("auth_email") or ""),
        operador_rol=str(db.info.get("operador_rol") or ""),
        entidad=entidad,
        entidad_id=entidad_id,
        organizacion_id=organizacion_id,
        detalle=detalle,
        ip_hash=hash_ip(ip_de_request(request)),
        resultado=resultado,
    )


def _reintentar_commit(db: Session):
    """Commit best-effort tras auditar (el evento no debe romper la acción)."""
    try:
        db.commit()
    except Exception:
        db.rollback()


def _rol_actual(db: Session) -> str:
    return str(db.info.get("operador_rol") or "").lower()


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


@router.get("/admin/licencias", response_class=HTMLResponse, include_in_schema=False)
def panel_licencias(request: Request, db: Session = Depends(get_operator_db)):
    return _render_licencias(request, db)


@router.get("/admin", response_class=HTMLResponse, include_in_schema=False)
def panel_admin(request: Request, db: Session = Depends(get_operator_db)):
    """Panel de administración premium: clientes, planes y compras en una vista."""
    from ..services.panel_admin import resumen_admin

    resumen = resumen_admin(db)
    finanzas = resumen_financiero(db)
    return TEMPLATES.TemplateResponse(
        request,
        "admin/dashboard.html",
        {
            "resumen": resumen,
            "finanzas": finanzas,
            "operador": db.info.get("auth_email", ""),
            "operador_rol": _rol_actual(db),
            "exigencia_licencias": exigencia_licencia_activada(),
            "msg": request.query_params.get("msg", ""),
            "error": request.query_params.get("error", ""),
        },
        headers={"Cache-Control": "no-store"},
    )


@router.get("/admin/analitica", response_class=HTMLResponse, include_in_schema=False)
def panel_analitica(
    request: Request,
    dias: int = 30,
    db: Session = Depends(get_operator_db),
):
    """Panel de analítica de producto (E5-012): embudo, retención y uso.

    Dato propio del servidor que complementa a Google Analytics (que solo ve
    la capa pública). Solo el operador: las métricas agregan toda la base de
    clientes y no pertenecen a una organización concreta.
    """
    from ..services.analitica import resumen_analitica

    resumen = resumen_analitica(db, dias=dias)
    return TEMPLATES.TemplateResponse(
        request,
        "admin/analitica.html",
        {
            "resumen": resumen,
            "operador": db.info.get("auth_email", ""),
        },
        headers={"Cache-Control": "no-store"},
    )


@router.get("/admin/operacion", response_class=HTMLResponse, include_in_schema=False)
def panel_operacion(request: Request, db: Session = Depends(get_operator_db)):
    """Diagnóstico operativo del despliegue (E3-024), solo para el operador.

    Reutiliza los chequeos de `/readyz` y añade los errores no capturados del
    proceso. Sin datos de tenant: el panel es del producto, no de un cliente.
    """
    diagnostico = diagnostico_operacion()
    return TEMPLATES.TemplateResponse(
        request,
        "admin/operacion.html",
        {
            "diagnostico": diagnostico,
            "operador": db.info.get("auth_email", ""),
        },
        headers={"Cache-Control": "no-store"},
    )


@router.get("/admin/emails", response_class=HTMLResponse, include_in_schema=False)
def panel_emails(request: Request, db: Session = Depends(get_operator_db)):
    """Página para enviar cualquiera de los correos a un buzón y revisarlo.

    Permite al operador ver los correos transaccionales **tal cual llegan** en
    un cliente real (Gmail, Zoho, Outlook), no como se ven en una vista previa.
    El destino por omisión es el propio correo del operador.
    """
    from ..services.correos_prueba import catalogo_correos

    return TEMPLATES.TemplateResponse(
        request,
        "admin/emails.html",
        {
            "correos": catalogo_correos(),
            "operador": db.info.get("auth_email", ""),
            "destino": request.query_params.get("destino", "") or db.info.get("auth_email", ""),
            "msg": request.query_params.get("msg", ""),
            "error": request.query_params.get("error", ""),
        },
        headers={"Cache-Control": "no-store"},
    )


@router.get("/admin/equipo", response_class=HTMLResponse, include_in_schema=False)
def panel_equipo(request: Request, db: Session = Depends(get_operator_db)):
    """Equipo de operadores: roles, altas y suspensiones (A1)."""
    return TEMPLATES.TemplateResponse(
        request,
        "admin/equipo.html",
        {
            "operadores": listar_operadores(db),
            "roles": [(rol, ROLES_OPERADOR_ETIQUETA[rol]) for rol in ROLES_OPERADOR],
            "rol_actual": _rol_actual(db),
            "es_superadmin": _rol_actual(db) == "superadmin",
            "operador": db.info.get("auth_email", ""),
            "msg": request.query_params.get("msg", ""),
            "error": request.query_params.get("error", ""),
        },
        headers={"Cache-Control": "no-store"},
    )


@router.post("/admin/equipo/crear", include_in_schema=False)
async def crear_operador_web(request: Request, db: Session = Depends(get_operator_db)):
    form = await request.form()
    try:
        exigir_superadmin(db)
        operador = crear_operador(
            db,
            email=str(form.get("email") or ""),
            rol=str(form.get("rol") or "admin"),
            operador_email=str(db.info.get("auth_email") or ""),
            notas=str(form.get("notas") or ""),
        )
        db.commit()
        _auditar_admin(
            db, request,
            accion="equipo.operador_alta",
            entidad="operador",
            entidad_id=operador.id,
            detalle={"email": operador.email, "rol": operador.rol},
        )
    except (GestionEquipoError, ValueError, TypeError) as exc:
        db.rollback()
        return _redirect("/admin/equipo", error=str(exc))
    except Exception:
        db.rollback()
        log.error("Error creando operador:\n%s", traceback.format_exc())
        raise
    return _redirect("/admin/equipo", msg=f"Operador {operador.email} dado de alta.")


@router.post("/admin/equipo/{operador_id}/rol", include_in_schema=False)
async def rol_operador_web(
    operador_id: int, request: Request, db: Session = Depends(get_operator_db)
):
    form = await request.form()
    try:
        exigir_superadmin(db)
        operador = cambiar_rol_operador(
            db,
            operador_id,
            rol=str(form.get("rol") or ""),
            operador_email=str(db.info.get("auth_email") or ""),
        )
        db.commit()
        _auditar_admin(
            db, request,
            accion="equipo.operador_rol",
            entidad="operador",
            entidad_id=operador.id,
            detalle={"email": operador.email, "rol": operador.rol},
        )
    except (GestionEquipoError, ValueError, TypeError) as exc:
        db.rollback()
        return _redirect("/admin/equipo", error=str(exc))
    except Exception:
        db.rollback()
        log.error("Error cambiando rol de operador:\n%s", traceback.format_exc())
        raise
    return _redirect("/admin/equipo", msg=f"Rol de {operador.email} actualizado.")


@router.post("/admin/equipo/{operador_id}/suspender", include_in_schema=False)
async def suspender_operador_web(
    operador_id: int, request: Request, db: Session = Depends(get_operator_db)
):
    try:
        exigir_superadmin(db)
        operador = suspender_operador(
            db, operador_id,
            operador_email=str(db.info.get("auth_email") or ""),
        )
        db.commit()
        _auditar_admin(
            db, request,
            accion="equipo.operador_suspension",
            entidad="operador",
            entidad_id=operador.id,
            detalle={"email": operador.email},
        )
    except (GestionEquipoError, ValueError, TypeError) as exc:
        db.rollback()
        return _redirect("/admin/equipo", error=str(exc))
    except Exception:
        db.rollback()
        log.error("Error suspendiendo operador:\n%s", traceback.format_exc())
        raise
    return _redirect("/admin/equipo", msg=f"{operador.email} suspendido.")


@router.post("/admin/equipo/{operador_id}/activar", include_in_schema=False)
async def activar_operador_web(
    operador_id: int, request: Request, db: Session = Depends(get_operator_db)
):
    try:
        exigir_superadmin(db)
        operador = activar_operador(
            db, operador_id,
            operador_email=str(db.info.get("auth_email") or ""),
        )
        db.commit()
        _auditar_admin(
            db, request,
            accion="equipo.operador_activacion",
            entidad="operador",
            entidad_id=operador.id,
            detalle={"email": operador.email},
        )
    except (GestionEquipoError, ValueError, TypeError) as exc:
        db.rollback()
        return _redirect("/admin/equipo", error=str(exc))
    except Exception:
        db.rollback()
        log.error("Error activando operador:\n%s", traceback.format_exc())
        raise
    return _redirect("/admin/equipo", msg=f"{operador.email} activado.")


@router.get("/admin/auditoria", response_class=HTMLResponse, include_in_schema=False)
def panel_auditoria(
    request: Request,
    db: Session = Depends(get_operator_db),
    actor: str = "",
    accion: str = "",
    organizacion_id: int | None = None,
):
    """Auditoría de las acciones del propio panel (A2)."""
    eventos = resumen_auditoria_admin(
        db,
        actor=actor,
        accion=accion,
        organizacion_id=organizacion_id,
        limite=250,
    )
    return TEMPLATES.TemplateResponse(
        request,
        "admin/auditoria.html",
        {
            "eventos": eventos,
            "acciones": sorted(ACCIONES_LECIBLES.items()),
            "filtros": {
                "actor": actor,
                "accion": accion,
                "organizacion_id": organizacion_id,
            },
            "operador": db.info.get("auth_email", ""),
            "operador_rol": _rol_actual(db),
            "msg": request.query_params.get("msg", ""),
            "error": request.query_params.get("error", ""),
        },
        headers={"Cache-Control": "no-store"},
    )


@router.get("/admin/buscar", include_in_schema=False)
def buscar_global_web(
    request: Request,
    q: str = "",
    db: Session = Depends(get_operator_db),
):
    """API del buscador global (A3). Solo devuelve datos visibles al operador."""
    return JSONResponse(
        {"q": q, "resultados": buscar_global(db, q)},
        headers={"Cache-Control": "no-store"},
    )


@router.get("/admin/notificaciones", include_in_schema=False)
def notificaciones_web(request: Request, db: Session = Depends(get_operator_db)):
    """API de la campana de notificaciones (A4)."""
    return JSONResponse(
        {"avisos": notificaciones_admin(db)},
        headers={"Cache-Control": "no-store"},
    )


@router.post("/admin/emails/enviar", include_in_schema=False)
async def enviar_correo_prueba_web(
    request: Request, db: Session = Depends(get_operator_db)
):
    """Envía un correo de prueba a la dirección indicada.

    El destino es libre pero validado: el operador es el único que llega aquí
    (`get_operator_db`), y enviar a una dirección arbitraria es exactamente el
    propósito de la página (probar los correos en el buzón de cada uno). No
    expone datos de clientes: los correos llevan datos de ejemplo.
    """
    from ..services.correos_prueba import enviar_correo_prueba
    from ..services.email import (
        EmailNotConfigured,
        EmailSendError,
        EmailValidationError,
    )

    form = await request.form()
    slug = str(form.get("slug") or "").strip()
    destino = str(form.get("destino") or "").strip()

    if not destino or not email_destino_valido(destino):
        return _redirect(
            f"/admin/emails?destino={quote(destino)}",
            error="Escribe un email de destino válido.",
        )
    try:
        envio_id = enviar_correo_prueba(slug, destino)
    except ValueError as exc:
        return _redirect("/admin/emails", error=str(exc))
    except EmailNotConfigured as exc:
        return _redirect(
            f"/admin/emails?destino={quote(destino)}",
            error=f"Correo no configurado: {exc}",
        )
    except (EmailSendError, EmailValidationError) as exc:
        log.warning("No se pudo enviar el correo de prueba (%s).", exc)
        return _redirect(
            f"/admin/emails?destino={quote(destino)}",
            error=f"No se pudo enviar: {exc}",
        )
    except Exception:
        log.error("Error enviando correo de prueba:\n%s", traceback.format_exc())
        return _redirect(
            f"/admin/emails?destino={quote(destino)}",
            error="Error inesperado enviando el correo de prueba.",
        )
    return _redirect(
        f"/admin/emails?destino={quote(destino)}",
        msg=f"Correo enviado a {destino} (id {envio_id}).",
    )


#: Importe por omisión de una licencia de pago según su duración, tomado de
#: los planes publicados (`app/datos_pago.py`): así el botón rápido «pago
#: anual» no obliga a teclear 89.00 cada vez, y un importe distinto sigue
#: pudiendo escribirse en el formulario completo.
_IMPORTE_POR_DURACION = {
    ficha["duracion_licencia"]: ficha["importe"] for ficha in PLANES.values()
}

#: Páginas del panel a las que una acción puede devolver al operador.
#: Se valida contra esta lista en vez de aceptar cualquier URL: un `volver`
#: libre en un formulario es una redirección abierta.
_DESTINOS_PANEL = {"/admin", "/admin/licencias", "/admin/renovaciones", "/admin/cobros"}
_DESTINO_CLIENTE_RE = re.compile(r"^/admin/clientes/\d+$")


def _destino_panel_valido(destino: str) -> bool:
    return destino in _DESTINOS_PANEL or bool(_DESTINO_CLIENTE_RE.match(destino))


def _volver_a(form, por_omision: str = "/admin/licencias") -> str:
    """Destino de la redirección tras una acción, limitado a las páginas del panel.

    Las mismas acciones se disparan desde `/admin` y desde `/admin/licencias`;
    devolver siempre al listado de licencias sacaría al operador de la pantalla
    en la que estaba trabajando. La Fase 2 añade la ficha de cliente, renovaciones
    y cobros como destinos válidos.
    """
    destino = str(form.get("volver") or "").strip()
    return destino if _destino_panel_valido(destino) else por_omision


@router.post("/admin/organizaciones/{organizacion_id}/conceder", include_in_schema=False)
async def conceder_licencia_rapida(
    organizacion_id: int, request: Request, db: Session = Depends(get_operator_db)
):
    """Concede una licencia a una organización concreta, en un solo gesto.

    Es la versión de dos clics de `POST /admin/licencias`: la organización va
    en la URL (viene de la fila en la que está el operador, que ya no tiene que
    buscarla en un desplegable) y el resto son valores por omisión sensatos.
    Cuando el caso es raro —importe atípico, referencia, notas— sigue estando
    el formulario completo.
    """
    form = await request.form()
    destino = _volver_a(form, "/admin")
    origen = str(form.get("origen") or "").strip().lower()
    duracion = str(form.get("duracion") or "").strip()
    importe = form.get("importe")
    if importe in (None, ""):
        # Una licencia de pago exige importe: si no lo indican, se toma el del
        # plan publicado que corresponde a la duración elegida.
        importe = _IMPORTE_POR_DURACION.get(duracion, 0.0) if origen == "pago" else 0.0
    try:
        licencia = crear_licencia(
            db,
            organizacion_id=organizacion_id,
            origen=origen,
            duracion=duracion,
            importe=importe,
            moneda=str(form.get("moneda") or "USD"),
            metodo_cobro=str(form.get("metodo_cobro") or ""),
            referencia=str(form.get("referencia") or ""),
            notas=str(form.get("notas") or ""),
            operador_email=str(db.info.get("auth_email") or ""),
        )
        nombre = licencia.organizacion.nombre if licencia.organizacion else ""
        vence = licencia.vence.strftime("%d/%m/%Y")
        db.commit()
        _auditar_admin(
            db, request,
            accion="licencia.concedida",
            entidad="licencia",
            entidad_id=licencia.id,
            organizacion_id=licencia.organizacion_id,
            detalle={"origen": licencia.origen, "importe": licencia.importe},
        )
    except (GestionLicenciaError, ValueError) as exc:
        db.rollback()
        return _redirect(destino, error=str(exc))
    except Exception:
        db.rollback()
        log.error("Error concediendo la licencia:\n%s", traceback.format_exc())
        raise
    return _redirect(destino, msg=f"{nombre}: acceso concedido hasta el {vence}.")


@router.post(
    "/admin/organizaciones/{organizacion_id}/suspender", include_in_schema=False
)
async def suspender_organizacion_web(
    organizacion_id: int, request: Request, db: Session = Depends(get_operator_db)
):
    """Corta el acceso de una organización cancelando toda su cadena activa.

    Cancelar una sola licencia no corta el acceso si hay renovaciones
    encadenadas detrás: el operador cree haber suspendido y el cliente sigue
    dentro. Por eso el botón «suspender» actúa sobre la cadena completa.
    """
    form = await request.form()
    destino = _volver_a(form, "/admin")
    try:
        canceladas = suspender_organizacion(
            db,
            organizacion_id=organizacion_id,
            motivo=str(form.get("motivo") or ""),
            operador_email=str(db.info.get("auth_email") or ""),
        )
        cuantas = len(canceladas)
        db.commit()
        _auditar_admin(
            db, request,
            accion="licencia.suspendida",
            entidad="organizacion",
            entidad_id=organizacion_id,
            organizacion_id=organizacion_id,
            detalle={"licencias_canceladas": cuantas},
        )
    except GestionLicenciaError as exc:
        db.rollback()
        return _redirect(destino, error=str(exc))
    except Exception:
        db.rollback()
        log.error("Error suspendiendo la organización:\n%s", traceback.format_exc())
        raise
    detalle = "1 licencia" if cuantas == 1 else f"{cuantas} licencias"
    return _redirect(destino, msg=f"Acceso suspendido ({detalle} cancelada/s).")


@router.post("/admin/licencias", include_in_schema=False)
async def crear_licencia_web(
    request: Request, db: Session = Depends(get_operator_db)
):
    form = await request.form()
    destino = _volver_a(form)
    try:
        licencia = crear_licencia(
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
        _auditar_admin(
            db, request,
            accion="licencia.creada",
            entidad="licencia",
            entidad_id=licencia.id,
            organizacion_id=licencia.organizacion_id,
            detalle={"origen": licencia.origen, "importe": licencia.importe},
        )
    except (GestionLicenciaError, ValueError) as exc:
        db.rollback()
        return _redirect(destino, error=str(exc))
    except Exception:
        db.rollback()
        log.error("Error creando la licencia:\n%s", traceback.format_exc())
        raise
    return _redirect(destino, msg="Licencia registrada.")


@router.post("/admin/licencias/{licencia_id}/cancelar", include_in_schema=False)
async def cancelar_licencia_web(
    licencia_id: int, request: Request, db: Session = Depends(get_operator_db)
):
    form = await request.form()
    destino = _volver_a(form)
    try:
        licencia = cancelar_licencia(
            db,
            licencia_id=licencia_id,
            motivo=str(form.get("motivo") or ""),
            operador_email=str(db.info.get("auth_email") or ""),
        )
        db.commit()
        _auditar_admin(
            db, request,
            accion="licencia.cancelada",
            entidad="licencia",
            entidad_id=licencia.id,
            organizacion_id=licencia.organizacion_id,
            detalle={"motivo": str(form.get("motivo") or "")[:200]},
        )
    except GestionLicenciaError as exc:
        db.rollback()
        return _redirect(destino, error=str(exc))
    except Exception:
        db.rollback()
        log.error("Error cancelando la licencia:\n%s", traceback.format_exc())
        raise
    return _redirect(destino, msg="Licencia cancelada.")


@router.get("/admin/licencias/{licencia_id}/recibo.pdf", include_in_schema=False)
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


@router.post("/admin/licencias/avisos", include_in_schema=False)
def enviar_avisos_web(request: Request, db: Session = Depends(get_operator_db)):
    """Envía los avisos de vencimiento a las organizaciones por vencer.

    Lo dispara el operador a mano: no hay trabajos programados en un
    despliegue serverless. El envío real lo hace Resend; la licencia queda
    anotada con la fecha y los destinatarios para no reenviar el mismo día.
    """
    from ..services.email import EmailNotConfigured, enviar_aviso_licencia

    try:
        resultado = enviar_avisos_vencimiento(db, remitente=enviar_aviso_licencia)
        db.commit()
        _auditar_admin(
            db, request,
            accion="aviso.licencias_enviadas",
            entidad="aviso",
            detalle={
                "avisadas": len(resultado.get("avisadas", [])),
                "omitidas": len(resultado.get("omitidas", [])),
            },
        )
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


# ---------------------------------------------------------------------------
# Trabajo programado: recordatorios de vencimiento (Vercel Cron)
# ---------------------------------------------------------------------------


def _verificar_cron_secret(request: Request) -> bool:
    """Comprueba que la petición venga del programador de Vercel.

    Vercel añade ``Authorization: Bearer $CRON_SECRET`` a cada invocación del
    cron (si ``CRON_SECRET`` está definido en el proyecto). La comparación es
    en tiempo constante para no filtrar nada por el tiempo de respuesta. Sin
    ``CRON_SECRET`` configurado la ruta queda cerrada para todo el mundo.
    """
    secreto = str(os.environ.get("CRON_SECRET", "")).strip()
    if not secreto:
        return False
    autorizacion = str(request.headers.get("authorization", ""))
    return hmac.compare_digest(autorizacion, f"Bearer {secreto}")


def _resumen_recordatorios(resultado: dict) -> dict:
    """Resumen JSON seguro del barrido, sin emails ni datos de negocio."""
    return {
        "enviados": len(resultado["avisadas"]),
        "organizaciones": [nombre for nombre, _d, _c in resultado["avisadas"]],
        "omitidos": len(resultado["omitidas"]),
        "sin_correo": len(resultado["sin_correo"]),
        "fallidos": [{"organizacion": n, "error": e} for n, e in resultado["fallidas"]],
    }


@router.get(CRON_RECORDATORIOS_PATH, include_in_schema=False)
def cron_recordatorios_vencimiento(
    request: Request, db: Session = Depends(get_cron_db)
):
    """Envía los recordatorios de vencimiento (5 y 1 día antes).

    Lo dispara ``vercel.json`` (``crons``) una vez al día. La ruta solo hace
    este barrido: verifica el secreto, envía los correos pendientes y devuelve
    un resumen. Cualquier otro uso no cuelga de aquí, y sin ``CRON_SECRET`` no
    responde a nadie.
    """
    if not _verificar_cron_secret(request):
        return JSONResponse(
            {"ok": False, "error": "No autorizado."},
            status_code=401,
            headers={"Cache-Control": "no-store"},
        )

    from ..services.email import (
        EmailNotConfigured,
        enviar_recordatorio_vencimiento,
    )
    from ..services.licencias import enviar_recordatorios_vencimiento

    try:
        resultado = enviar_recordatorios_vencimiento(
            db, remitente=enviar_recordatorio_vencimiento
        )
        db.commit()
    except EmailNotConfigured as exc:
        db.rollback()
        return JSONResponse(
            {"ok": False, "error": str(exc)},
            status_code=503,
            headers={"Cache-Control": "no-store"},
        )
    except Exception:
        db.rollback()
        log.error("Error en el recordatorio programado:\n%s", traceback.format_exc())
        return JSONResponse(
            {"ok": False, "error": "Error interno."},
            status_code=500,
            headers={"Cache-Control": "no-store"},
        )

    return JSONResponse(
        {"ok": True, "resumen": _resumen_recordatorios(resultado)},
        headers={"Cache-Control": "no-store"},
    )


@router.get(CRON_MANTENIMIENTO_PATH, include_in_schema=False)
def cron_mantenimiento(request: Request, db: Session = Depends(get_cron_db)):
    """Respaldo automático + verificación diaria con alerta (E4-021/E4-023).

    Un único disparo diario (``vercel.json`` → ``crons``) ejecuta las dos
    tareas de mantenimiento que no dependen de una sesión humana. Misma puerta
    de seguridad que el cron de recordatorios: ``Authorization:
    Bearer $CRON_SECRET``. Devuelve siempre 200 si el trabajo se ejecutó; los
    fallos reales van en el resumen (y en el correo de alerta si la
    verificación no está en verde).
    """
    if not _verificar_cron_secret(request):
        return JSONResponse(
            {"ok": False, "error": "No autorizado."},
            status_code=401,
            headers={"Cache-Control": "no-store"},
        )

    from ..services.mantenimiento import (
        ejecutar_respaldo_automatico,
        ejecutar_verificacion_diaria,
    )

    try:
        respaldo = ejecutar_respaldo_automatico(db)
        db.commit()
    except Exception:
        db.rollback()
        log.error("Error en el respaldo automático del cron:\n%s", traceback.format_exc())
        respaldo = {"ok": False, "error": "Error interno en el respaldo automático."}

    try:
        verificacion = ejecutar_verificacion_diaria()
    except Exception:
        log.error("Error en la verificación diaria del cron:\n%s", traceback.format_exc())
        verificacion = {"ok": False, "error": "Error interno en la verificación."}

    return JSONResponse(
        {"ok": respaldo.get("ok", True) and verificacion.get("ok", True),
         "respaldo": respaldo, "verificacion": verificacion},
        headers={"Cache-Control": "no-store"},
    )


# ---------------------------------------------------------------------------
# Compras de plan: revisión y activación manual (E1-059)
# ---------------------------------------------------------------------------

def _render_compras(
    request: Request,
    db: Session,
    *,
    msg: str = "",
    error: str = "",
    status_code: int = 200,
):
    from ..services.compras import resumen_compras

    return TEMPLATES.TemplateResponse(
        request,
        "admin/compras.html",
        {
            "filas": resumen_compras(db),
            "operador": db.info.get("auth_email", ""),
            "msg": msg or request.query_params.get("msg", ""),
            "error": error or request.query_params.get("error", ""),
        },
        status_code=status_code,
        headers={"Cache-Control": "no-store"},
    )


@router.get("/admin/compras", response_class=HTMLResponse, include_in_schema=False)
def panel_compras(request: Request, db: Session = Depends(get_operator_db)):
    return _render_compras(request, db)


@router.post("/admin/compras/{compra_id}/activar", include_in_schema=False)
def activar_compra_web(
    compra_id: int, request: Request, db: Session = Depends(get_operator_db)
):
    """Verifica el comprobante y concede la licencia del plan comprado."""
    from ..services.compras import GestionCompraError, activar_compra

    try:
        compra_previa = db.get(CompraPlan, compra_id)
        compra, licencia = activar_compra(
            db,
            compra_id=compra_id,
            operador_email=str(db.info.get("auth_email") or ""),
            exigir_comprobante=(
                compra_previa is None
                or compra_previa.metodo_pago != "stripe"
            ),
        )
        db.commit()
        _auditar_admin(
            db, request,
            accion="compra.activada",
            entidad="compra",
            entidad_id=compra.id,
            organizacion_id=compra.organizacion_id,
            detalle={"plan": compra.plan, "licencia": licencia.id},
        )
    except (GestionCompraError, ValueError) as exc:
        db.rollback()
        return _redirect("/admin/compras", error=str(exc))
    except Exception:
        db.rollback()
        log.error("Error activando compra #%s:\n%s", compra_id, traceback.format_exc())
        raise

    # Aviso al comprador (no bloqueante): la licencia ya está concedida y
    # confirmada. Un fallo de correo no puede deshacer una activación ni
    # devolver un error al operador, que ya hizo su parte; se anota en el
    # mensaje para que sepa si tiene que escribir a mano.
    aviso = _avisar_activacion_al_cliente(db, compra, licencia)
    # Telemetría (E5-012): cierre del embudo de cobro por activación manual.
    # La sesión de operador no lleva claim de tenant: organización explícita.
    telemetria.registrar(
        db,
        "licencia.activada",
        organizacion_id=compra.organizacion_id,
        detalle={"plan": compra.plan, "origen": "manual"},
    )
    return _redirect(
        "/admin/compras",
        msg=(
            f"Compra #{compra_id} activada · licencia #{licencia.id} concedida. "
            f"{aviso}"
        ),
    )


def _avisar_activacion_al_cliente(db: Session, compra, licencia) -> str:
    """Envía al comprador el aviso de plan activo con su recibo adjunto.

    Devuelve una frase corta para el mensaje del panel. Nunca lanza: el correo
    es una cortesía sobre una activación que ya está hecha, y dejar al
    operador con un 500 tras haber concedido la licencia sería mucho peor que
    un aviso no entregado.
    """
    from ..datos_pago import PLANES, metodo_info
    from ..services.email import (
        EmailNotConfigured,
        EmailSendError,
        EmailValidationError,
        enviar_activacion_plan_por_email,
    )

    destinatario = str(getattr(compra, "creada_por_email", "") or "").strip()
    if not destinatario:
        return "La compra no guardó email del comprador: avísale tú."

    organizacion = licencia.organizacion or db.get(
        Organizacion, compra.organizacion_id
    )
    plan_nombre = str(PLANES.get(compra.plan, {}).get("nombre") or "Tu plan")
    try:
        metodo_nombre = str(metodo_info(compra.metodo_pago)["nombre"])
    except KeyError:
        metodo_nombre = ""

    # El recibo es opcional: si no se puede generar, el aviso sale igual.
    recibo_pdf = b""
    recibo_nombre = "recibo.pdf"
    try:
        recibo_pdf = generar_recibo_licencia_pdf(licencia, organizacion).read()
        recibo_nombre = f"recibo-{numero_recibo(licencia)}.pdf"
    except Exception:
        log.warning(
            "Compra #%s activada sin recibo adjunto:\n%s",
            compra.id,
            traceback.format_exc(),
        )

    try:
        enviar_activacion_plan_por_email(
            email=destinatario,
            organizacion_nombre=organizacion.nombre if organizacion else "",
            plan_nombre=plan_nombre,
            importe_texto=fmt_monto(compra.importe, compra.moneda or "USD"),
            metodo_nombre=metodo_nombre,
            inicio=licencia.inicio,
            vence=licencia.vence,
            recibo_pdf=recibo_pdf,
            recibo_nombre=recibo_nombre,
        )
    except EmailNotConfigured:
        return f"Correo no configurado: avisa tú a {destinatario}."
    except (EmailValidationError, EmailSendError) as exc:
        log.warning("Aviso de activación no entregado a %s (%s).", destinatario, exc)
        return f"No se pudo avisar a {destinatario}: escríbele tú."
    except Exception:
        log.error(
            "Error inesperado avisando la activación de la compra #%s:\n%s",
            compra.id,
            traceback.format_exc(),
        )
        return f"No se pudo avisar a {destinatario}: escríbele tú."
    return f"Avisado {destinatario} con su recibo."


@router.post("/admin/compras/{compra_id}/rechazar", include_in_schema=False)
def rechazar_compra_web(
    compra_id: int, request: Request, db: Session = Depends(get_operator_db)
):
    from ..services.compras import GestionCompraError, rechazar_compra

    try:
        compra = rechazar_compra(
            db,
            compra_id=compra_id,
            operador_email=str(db.info.get("auth_email") or ""),
        )
        db.commit()
        _auditar_admin(
            db, request,
            accion="compra.rechazada",
            entidad="compra",
            entidad_id=compra_id,
            organizacion_id=compra.organizacion_id,
            detalle={"plan": compra.plan},
        )
    except (GestionCompraError, ValueError) as exc:
        db.rollback()
        return _redirect("/admin/compras", error=str(exc))
    except Exception:
        db.rollback()
        log.error("Error rechazando compra #%s:\n%s", compra_id, traceback.format_exc())
        raise
    return _redirect("/admin/compras", msg=f"Compra #{compra_id} rechazada.")


@router.get("/admin/compras/{compra_id}/comprobante", include_in_schema=False)
def comprobante_compra(
    compra_id: int, request: Request, db: Session = Depends(get_operator_db)
):
    """Devuelve el comprobante adjunto de una compra para revisarlo.

    El operador no tiene la organización del comprador activa, así que no
    puede usar el proxy de tenant ``/archivos/...``; esta ruta lee el objeto
    directamente del almacenamiento privado con la referencia guardada.
    """
    from ..services.compras import (
        GestionCompraError,
        _exigir_compra,
        comprobante_bytes,
    )
    from ..storage import StorageError

    try:
        compra = _exigir_compra(db, compra_id)
        contenido = comprobante_bytes(compra)
    except (GestionCompraError, StorageError):
        return Response("Comprobante no disponible.", status_code=404)
    nombre = Path(compra.comprobante_nombre or "comprobante").name.replace('"', "")
    return Response(
        contenido,
        media_type=compra.comprobante_mime or "application/octet-stream",
        headers={
            "Cache-Control": "private, no-store",
            "Content-Disposition": f'inline; filename="{quote(nombre)}"',
            "X-Content-Type-Options": "nosniff",
        },
    )


# ---------------------------------------------------------------------------
# Fase 2: ficha de cliente, centro de cobros, renovaciones y automatizaciones
# ---------------------------------------------------------------------------


def _mes_parametro(valor: str | None):
    """Convierte ``YYYY-MM`` al primer día del mes; por defecto el actual."""
    hoy = date.today()
    valor = (valor or "").strip()
    if not valor:
        return hoy.replace(day=1)
    try:
        año, mes = (int(parte) for parte in valor.split("-", 1))
        return date(año, mes, 1)
    except (TypeError, ValueError):
        return hoy.replace(day=1)


def _filtrar_clientes(filas, q: str):
    q = (q or "").strip().lower()
    if not q:
        return filas
    return [
        f for f in filas
        if q in f["organizacion"].nombre.lower()
        or q in f["organizacion"].slug.lower()
    ]


def _render_clientes(
    request: Request,
    db: Session,
    *,
    q: str = "",
    msg: str = "",
    error: str = "",
    status_code: int = 200,
):
    from ..services.panel_admin import resumen_admin
    from ..services.panel_renovaciones import proximas_renovaciones

    resumen = resumen_admin(db)
    resumen["filas"] = _filtrar_clientes(resumen["filas"], q)
    resumen["totales"].update({"filtradas": len(resumen["filas"])})
    return TEMPLATES.TemplateResponse(
        request,
        "admin/clientes.html",
        {
            "resumen": resumen,
            "proximas": proximas_renovaciones(db),
            "q": q,
            "operador": db.info.get("auth_email", ""),
            "operador_rol": _rol_actual(db),
            "msg": msg or request.query_params.get("msg", ""),
            "error": error or request.query_params.get("error", ""),
        },
        status_code=status_code,
        headers={"Cache-Control": "no-store"},
    )


@router.get("/admin/clientes", response_class=HTMLResponse, include_in_schema=False)
def panel_clientes(
    request: Request,
    q: str = "",
    db: Session = Depends(get_operator_db),
):
    """Listado de clientes con acceso directo a la ficha completa (B1)."""
    return _render_clientes(request, db, q=q)


@router.get("/admin/clientes/{organizacion_id}", response_class=HTMLResponse, include_in_schema=False)
def ficha_cliente(
    organizacion_id: int,
    request: Request,
    db: Session = Depends(get_operator_db),
):
    """Ficha de cliente: plan, uso, cobros, actividad y notas internas (B1)."""
    from ..services.panel_clientes import resumen_cliente

    ficha = resumen_cliente(db, organizacion_id)
    if ficha is None:
        return _redirect("/admin/clientes", error="El cliente indicado no existe.")
    return TEMPLATES.TemplateResponse(
        request,
        "admin/cliente_detalle.html",
        {
            "ficha": ficha,
            "operador": db.info.get("auth_email", ""),
            "operador_rol": _rol_actual(db),
            "duraciones": [(clave, texto) for clave, (texto, _) in DURACIONES.items()],
            "origenes": [
                (origen, ORIGENES_LICENCIA_ETIQUETA[origen])
                for origen in ORIGENES_LICENCIA
            ],
            "msg": request.query_params.get("msg", ""),
            "error": request.query_params.get("error", ""),
        },
        headers={"Cache-Control": "no-store"},
    )


@router.post("/admin/clientes/{organizacion_id}/notas", include_in_schema=False)
async def crear_nota_cliente_web(
    organizacion_id: int,
    request: Request,
    db: Session = Depends(get_operator_db),
):
    """Guarda una nota interna de gestión sobre el cliente (best-effort)."""
    from ..services.panel_clientes import crear_nota_operador

    form = await request.form()
    try:
        nota = crear_nota_operador(
            db,
            organizacion_id,
            contenido=str(form.get("contenido") or ""),
            autor_email=str(db.info.get("auth_email") or ""),
        )
        db.commit()
        _auditar_admin(
            db, request,
            accion="cliente.nota_creada",
            entidad="organizacion",
            entidad_id=organizacion_id,
            organizacion_id=organizacion_id,
            detalle={"nota_id": nota.id},
        )
    except ValueError as exc:
        db.rollback()
        return _redirect(f"/admin/clientes/{organizacion_id}", error=str(exc))
    except Exception:
        db.rollback()
        log.error("Error creando nota de cliente #%s:\n%s", organizacion_id, traceback.format_exc())
        return _redirect(f"/admin/clientes/{organizacion_id}", error="No se pudo guardar la nota.")
    return _redirect(f"/admin/clientes/{organizacion_id}", msg="Nota guardada.")


@router.get("/admin/clientes.csv", include_in_schema=False)
def exportar_clientes_csv(
    request: Request,
    q: str = "",
    db: Session = Depends(get_operator_db),
):
    """Exporta la vista de clientes (B1/A5) en CSV."""
    from ..services.panel_admin import resumen_admin

    resumen = resumen_admin(db)
    resumen["filas"] = _filtrar_clientes(resumen["filas"], q)
    filas = [["Cliente", "Slug", "Estado", "Plan", "Inicio", "Vence", "Días", "Ingresos"]]
    for f in resumen["filas"]:
        org = f["organizacion"]
        filas.append([
            org.nombre,
            org.slug,
            f["estado_label"],
            f["plan_label"] or "",
            f["inicio"].strftime("%Y-%m-%d") if f["inicio"] else "",
            f["vence"].strftime("%Y-%m-%d") if f["vence"] else "",
            str(f["dias_restantes"]),
            f"{f['ingresos']:.2f}",
        ])
    return _csv_response(filas, "clientes.csv")


@router.get("/admin/cobros", response_class=HTMLResponse, include_in_schema=False)
def panel_cobros(
    request: Request,
    mes: str = "",
    db: Session = Depends(get_operator_db),
):
    """Centro de cobros del mes (B2)."""
    from ..services.panel_cobros import resumen_cobros

    data = resumen_cobros(db, mes=_mes_parametro(mes))
    return TEMPLATES.TemplateResponse(
        request,
        "admin/cobros.html",
        {
            "data": data,
            "operador": db.info.get("auth_email", ""),
            "operador_rol": _rol_actual(db),
            "msg": request.query_params.get("msg", ""),
            "error": request.query_params.get("error", ""),
        },
        headers={"Cache-Control": "no-store"},
    )


@router.get("/admin/cobros.csv", include_in_schema=False)
def exportar_cobros_csv(
    request: Request,
    mes: str = "",
    db: Session = Depends(get_operator_db),
):
    """Exporta el centro de cobros del mes (B2/A5) en CSV."""
    from ..services.panel_cobros import resumen_cobros

    data = resumen_cobros(db, mes=_mes_parametro(mes))
    filas = [["Mes", "Tipo", "Número", "Fecha", "Importe", "Moneda", "Estado", "Cliente"]]
    for m in data["movimientos"]:
        filas.append([
            data["mes"].strftime("%Y-%m"),
            m["tipo"],
            m["numero"],
            m["fecha"].strftime("%Y-%m-%d") if m["fecha"] else "",
            f"{m['importe']:.2f}",
            m["moneda"],
            m["estado"],
            m["organizacion_nombre"],
        ])
    return _csv_response(filas, f"cobros_{data['mes'].strftime('%Y-%m')}.csv")


@router.get("/admin/renovaciones", response_class=HTMLResponse, include_in_schema=False)
def panel_renovaciones(
    request: Request,
    mes: str = "",
    db: Session = Depends(get_operator_db),
):
    """Qué renueva este mes y qué clientes hay que empujar (B3)."""
    from ..services.panel_renovaciones import renovaciones_del_mes

    data = renovaciones_del_mes(db, mes=_mes_parametro(mes))
    return TEMPLATES.TemplateResponse(
        request,
        "admin/renovaciones.html",
        {
            "data": data,
            "operador": db.info.get("auth_email", ""),
            "operador_rol": _rol_actual(db),
            "msg": request.query_params.get("msg", ""),
            "error": request.query_params.get("error", ""),
        },
        headers={"Cache-Control": "no-store"},
    )


@router.get("/admin/renovaciones.csv", include_in_schema=False)
def exportar_renovaciones_csv(
    request: Request,
    mes: str = "",
    db: Session = Depends(get_operator_db),
):
    """Exporta las renovaciones del mes (B3/A5) en CSV."""
    from ..services.panel_renovaciones import renovaciones_del_mes

    data = renovaciones_del_mes(db, mes=_mes_parametro(mes))
    filas = [["Mes", "Cliente", "Vence", "Días", "Importe", "Estado", "Avisado hoy"]]
    for f in data["filas"]:
        filas.append([
            data["mes"].strftime("%Y-%m"),
            f["organizacion"].nombre,
            f["vence"].strftime("%Y-%m-%d"),
            str(f["dias_restantes"]),
            f"{f['importe']:.2f}",
            f["estado"],
            "Sí" if f["avisado_hoy"] else "No",
        ])
    return _csv_response(filas, f"renovaciones_{data['mes'].strftime('%Y-%m')}.csv")


@router.get("/admin/automatizaciones", response_class=HTMLResponse, include_in_schema=False)
def panel_automatizaciones(request: Request, db: Session = Depends(get_operator_db)):
    """Vista de reglas activas y su impacto hoy (B5)."""
    from ..services.automatizaciones_admin import REGLAS, estado_automatizaciones

    return TEMPLATES.TemplateResponse(
        request,
        "admin/automatizaciones.html",
        {
            "reglas": REGLAS,
            "estado": estado_automatizaciones(db),
            "operador": db.info.get("auth_email", ""),
            "operador_rol": _rol_actual(db),
            "msg": request.query_params.get("msg", ""),
            "error": request.query_params.get("error", ""),
        },
        headers={"Cache-Control": "no-store"},
    )


@router.post("/admin/automatizaciones/{regla}/ejecutar", include_in_schema=False)
async def ejecutar_automatizacion_web(
    regla: str,
    request: Request,
    db: Session = Depends(get_operator_db),
):
    """Ejecuta una regla a mano con la misma lógica que el cron (B5)."""
    from ..services.automatizaciones_admin import (
        GestionAutomatizacionError,
        ejecutar_regla,
    )
    from ..services.email import EmailNotConfigured

    from ..services.email import (
        enviar_aviso_licencia,
        enviar_recordatorio_vencimiento,
    )

    remitente = None
    if regla == "avisos_vencimiento":
        remitente = enviar_aviso_licencia
    elif regla == "recordatorios":
        remitente = enviar_recordatorio_vencimiento

    try:
        resultado = ejecutar_regla(db, regla, remitente=remitente)
        db.commit()
        _auditar_admin(
            db, request,
            accion="automatizacion.ejecutada",
            entidad="automatizacion",
            detalle={"regla": regla},
        )
    except EmailNotConfigured as exc:
        db.rollback()
        return _redirect("/admin/automatizaciones", error=f"Correo no configurado: {exc}")
    except GestionAutomatizacionError as exc:
        db.rollback()
        return _redirect("/admin/automatizaciones", error=str(exc))
    except Exception:
        db.rollback()
        log.error("Error ejecutando automatización %s:\n%s", regla, traceback.format_exc())
        return _redirect("/admin/automatizaciones", error="Error inesperado al ejecutar la regla.")

    return _redirect("/admin/automatizaciones", msg=f"Regla «{regla}» ejecutada.")


# ---------------------------------------------------------------------------
# Fase 3: la web se gobierna desde el panel (C1/C2/C4/C5, D3)
# ---------------------------------------------------------------------------

def _fecha_desde_form(valor: str | None):
    valor = (valor or "").strip()
    if not valor:
        return None
    try:
        return date.fromisoformat(valor)
    except ValueError:
        raise GestionWebError("La fecha indicada no es válida.") from None


@router.get("/admin/web", response_class=HTMLResponse, include_in_schema=False)
def panel_web(request: Request, db: Session = Depends(get_operator_db)):
    return TEMPLATES.TemplateResponse(
        request,
        "admin/web.html",
        {
            "contenido": listar_contenido(db),
            "operador": db.info.get("auth_email", ""),
            "msg": request.query_params.get("msg", ""),
            "error": request.query_params.get("error", ""),
        },
        headers={"Cache-Control": "no-store"},
    )


@router.post("/admin/web/guardar", include_in_schema=False)
async def web_guardar(request: Request, db: Session = Depends(get_operator_db)):
    form = await request.form()
    clave = str(form.get("clave") or "")
    try:
        campos = json.loads(str(form.get("contenido_json") or "{}"))
    except ValueError:
        return _redirect(f"/admin/web?clave={quote(clave, safe='')}", error="El contenido no es JSON válido.")
    try:
        guardar_contenido(
            db, clave=clave, campos=campos,
            operador_email=str(db.info.get("auth_email") or ""),
        )
        db.commit()
        _auditar_admin(db, request, accion="web.contenido_guardado", entidad="contenido_web", detalle={"clave": clave})
    except GestionWebError as exc:
        db.rollback()
        return _redirect(f"/admin/web?clave={quote(clave, safe='')}", error=str(exc))
    except Exception:
        db.rollback()
        return _redirect("/admin/web", error="Error inesperado al guardar el contenido.")
    return _redirect(f"/admin/web?clave={quote(clave, safe='')}", msg="Borrador guardado; aún no es público.")


@router.post("/admin/web/{clave}/publicar", include_in_schema=False)
def web_publicar(clave: str, request: Request, db: Session = Depends(get_operator_db)):
    try:
        publicar_contenido(db, clave=clave, operador_email=str(db.info.get("auth_email") or ""))
        db.commit()
        _auditar_admin(db, request, accion="web.contenido_publicado", entidad="contenido_web", detalle={"clave": clave})
    except GestionWebError as exc:
        db.rollback()
        return _redirect("/admin/web", error=str(exc))
    except Exception:
        db.rollback()
        return _redirect("/admin/web", error="Error inesperado al publicar.")
    return _redirect("/admin/web", msg="Contenido publicado.")


@router.post("/admin/web/{clave}/descartar", include_in_schema=False)
def web_descartar(clave: str, request: Request, db: Session = Depends(get_operator_db)):
    try:
        descartar_contenido(db, clave=clave)
        db.commit()
        _auditar_admin(db, request, accion="web.contenido_descartado", entidad="contenido_web", detalle={"clave": clave})
    except GestionWebError as exc:
        db.rollback()
        return _redirect("/admin/web", error=str(exc))
    except Exception:
        db.rollback()
        return _redirect("/admin/web", error="Error inesperado al descartar.")
    return _redirect("/admin/web", msg="Borrador descartado; se mantiene lo publicado.")


@router.get("/admin/avisos", response_class=HTMLResponse, include_in_schema=False)
def panel_avisos(request: Request, db: Session = Depends(get_operator_db)):
    return TEMPLATES.TemplateResponse(
        request,
        "admin/avisos.html",
        {
            "avisos": listar_avisos(db),
            "tipos": list(TIPOS_AVISO),
            "niveles": list(NIVELES_AVISO),
            "operador": db.info.get("auth_email", ""),
            "msg": request.query_params.get("msg", ""),
            "error": request.query_params.get("error", ""),
        },
        headers={"Cache-Control": "no-store"},
    )


@router.post("/admin/avisos/crear", include_in_schema=False)
async def avisos_crear(request: Request, db: Session = Depends(get_operator_db)):
    form = await request.form()
    try:
        inicio = _fecha_desde_form(str(form.get("inicio") or ""))
        fin = _fecha_desde_form(str(form.get("fin") or ""))
        aviso = crear_aviso(
            db,
            tipo=str(form.get("tipo") or ""),
            nivel=str(form.get("nivel") or ""),
            titulo=str(form.get("titulo") or ""),
            mensaje=str(form.get("mensaje") or ""),
            activo=str(form.get("activo") or "").lower() in {"1", "true", "on", "si"},
            inicio=inicio,
            fin=fin,
            operador_email=str(db.info.get("auth_email") or ""),
        )
        db.commit()
        _auditar_admin(db, request, accion="web.aviso_creado", entidad="avisos_web", entidad_id=aviso.id)
    except GestionWebError as exc:
        db.rollback()
        return _redirect("/admin/avisos", error=str(exc))
    except Exception:
        db.rollback()
        return _redirect("/admin/avisos", error="Error inesperado al crear el aviso.")
    return _redirect("/admin/avisos", msg="Aviso creado.")


@router.post("/admin/avisos/{aviso_id}/alternar", include_in_schema=False)
def avisos_alternar(aviso_id: int, request: Request, db: Session = Depends(get_operator_db)):
    form = None
    activo = str(request.query_params.get("activo", "")).lower() in {"1", "true", "on", "si"}
    try:
        alternar_aviso(db, aviso_id, activo=activo)
        db.commit()
        _auditar_admin(db, request, accion="web.aviso_alternado", entidad="avisos_web", entidad_id=aviso_id, detalle={"activo": activo})
    except GestionWebError as exc:
        db.rollback()
        return _redirect("/admin/avisos", error=str(exc))
    return _redirect("/admin/avisos", msg="Estado del aviso actualizado.")


@router.get("/admin/releases", response_class=HTMLResponse, include_in_schema=False)
def panel_releases(request: Request, db: Session = Depends(get_operator_db)):
    return TEMPLATES.TemplateResponse(
        request,
        "admin/releases.html",
        {
            "releases": listar_releases(db),
            "operador": db.info.get("auth_email", ""),
            "msg": request.query_params.get("msg", ""),
            "error": request.query_params.get("error", ""),
        },
        headers={"Cache-Control": "no-store"},
    )


@router.post("/admin/releases/crear", include_in_schema=False)
async def releases_crear(request: Request, db: Session = Depends(get_operator_db)):
    form = await request.form()
    try:
        release = crear_release(
            db,
            version=str(form.get("version") or ""),
            titulo=str(form.get("titulo") or ""),
            notas=str(form.get("notas") or ""),
            destacado=str(form.get("destacado") or "").lower() in {"1", "true", "on", "si"},
            publicado=str(form.get("publicado") or "").lower() in {"1", "true", "on", "si"},
            fecha=_fecha_desde_form(str(form.get("fecha") or "")),
            operador_email=str(db.info.get("auth_email") or ""),
        )
        db.commit()
        _auditar_admin(db, request, accion="web.release_creada", entidad="releases", entidad_id=release.id)
    except GestionWebError as exc:
        db.rollback()
        return _redirect("/admin/releases", error=str(exc))
    except Exception:
        db.rollback()
        return _redirect("/admin/releases", error="Error inesperado al crear la versión.")
    return _redirect("/admin/releases", msg="Versión creada.")


@router.post("/admin/releases/{release_id}/alternar", include_in_schema=False)
def releases_alternar(release_id: int, request: Request, db: Session = Depends(get_operator_db)):
    publicado = str(request.query_params.get("publicado", "")).lower() in {"1", "true", "on", "si"}
    try:
        alternar_release(db, release_id, publicado=publicado)
        db.commit()
        _auditar_admin(db, request, accion="web.release_alternada", entidad="releases", entidad_id=release_id, detalle={"publicado": publicado})
    except GestionWebError as exc:
        db.rollback()
        return _redirect("/admin/releases", error=str(exc))
    return _redirect("/admin/releases", msg="Visibilidad de la versión actualizada.")


@router.get("/admin/flags", response_class=HTMLResponse, include_in_schema=False)
def panel_flags(request: Request, db: Session = Depends(get_operator_db)):
    return TEMPLATES.TemplateResponse(
        request,
        "admin/flags.html",
        {
            "flags": listar_flags(db),
            "operador": db.info.get("auth_email", ""),
            "msg": request.query_params.get("msg", ""),
            "error": request.query_params.get("error", ""),
        },
        headers={"Cache-Control": "no-store"},
    )


@router.post("/admin/flags/{clave}/alternar", include_in_schema=False)
def flags_alternar(clave: str, request: Request, db: Session = Depends(get_operator_db)):
    from ..services.web_admin import actualizar_flag

    activo = str(request.query_params.get("activo", "")).lower() in {"1", "true", "on", "si"}
    try:
        actualizar_flag(
            db, clave=clave, activo=activo,
            operador_email=str(db.info.get("auth_email") or ""),
        )
        db.commit()
        _auditar_admin(db, request, accion="web.flag_cambiado", entidad="feature_flags", detalle={"clave": clave, "activo": activo})
    except GestionWebError as exc:
        db.rollback()
        return _redirect("/admin/flags", error=str(exc))
    return _redirect("/admin/flags", msg="Feature flag actualizado.")


# ---------------------------------------------------------------------------
# Fase 4: CRM ligero (B4), vistas guardadas, salud de datos y API keys (A6)
# ---------------------------------------------------------------------------

@router.get("/admin/crm", response_class=HTMLResponse, include_in_schema=False)
def panel_crm(request: Request, db: Session = Depends(get_operator_db)):
    return TEMPLATES.TemplateResponse(
        request,
        "admin/crm.html",
        {
            "filas": listar_crm(db),
            "resumen": resumen_crm(db),
            "estados": [(clave, etiqueta) for clave, etiqueta in ESTADOS_CRM_ETIQUETA.items()],
            "operador": db.info.get("auth_email", ""),
            "msg": request.query_params.get("msg", ""),
            "error": request.query_params.get("error", ""),
        },
        headers={"Cache-Control": "no-store"},
    )


@router.post("/admin/crm/{organizacion_id}/guardar", include_in_schema=False)
async def crm_guardar(organizacion_id: int, request: Request, db: Session = Depends(get_operator_db)):
    form = await request.form()
    try:
        guardar_crm(
            db,
            organizacion_id=organizacion_id,
            estado=str(form.get("estado") or ""),
            proximo_contacto=_fecha_desde_form(str(form.get("proximo_contacto") or "")),
            notas=str(form.get("notas") or ""),
            operador_email=str(db.info.get("auth_email") or ""),
        )
        db.commit()
        _auditar_admin(db, request, accion="crm.cliente_actualizado", entidad="crm_clientes", organizacion_id=organizacion_id)
    except GestionWebError as exc:
        db.rollback()
        return _redirect("/admin/crm", error=str(exc))
    except Exception:
        db.rollback()
        return _redirect("/admin/crm", error="Error inesperado al guardar el CRM.")
    return _redirect("/admin/crm", msg="Cliente actualizado en el canal.")


@router.get("/admin/vistas", response_class=HTMLResponse, include_in_schema=False)
def panel_vistas(request: Request, db: Session = Depends(get_operator_db)):
    return TEMPLATES.TemplateResponse(
        request,
        "admin/vistas.html",
        {
            "vistas": listar_vistas(db),
            "modulos": ["clientes", "cobros", "renovaciones", "compras", "automatizaciones"],
            "operador": db.info.get("auth_email", ""),
            "msg": request.query_params.get("msg", ""),
            "error": request.query_params.get("error", ""),
        },
        headers={"Cache-Control": "no-store"},
    )


@router.post("/admin/vistas/crear", include_in_schema=False)
async def vistas_crear(request: Request, db: Session = Depends(get_operator_db)):
    form = await request.form()
    try:
        filtros = json.loads(str(form.get("filtros") or "{}"))
        columnas = json.loads(str(form.get("columnas") or "[]"))
        vista = guardar_vista(
            db,
            modulo=str(form.get("modulo") or ""),
            nombre=str(form.get("nombre") or ""),
            filtros=filtros,
            columnas=columnas,
            operador_email=str(db.info.get("auth_email") or ""),
        )
        db.commit()
        _auditar_admin(db, request, accion="admin.vista_guardada", entidad="vistas_guardadas", entidad_id=vista.id)
    except (GestionWebError, ValueError) as exc:
        db.rollback()
        return _redirect("/admin/vistas", error=str(exc) if isinstance(exc, GestionWebError) else "Los filtros o columnas deben ser JSON válido.")
    return _redirect("/admin/vistas", msg="Vista guardada.")


@router.post("/admin/vistas/{vista_id}/eliminar", include_in_schema=False)
def vistas_eliminar(vista_id: int, request: Request, db: Session = Depends(get_operator_db)):
    try:
        eliminar_vista(db, vista_id)
        db.commit()
        _auditar_admin(db, request, accion="admin.vista_eliminada", entidad="vistas_guardadas", entidad_id=vista_id)
    except GestionWebError as exc:
        db.rollback()
        return _redirect("/admin/vistas", error=str(exc))
    return _redirect("/admin/vistas", msg="Vista eliminada.")


@router.get("/admin/salud-datos", response_class=HTMLResponse, include_in_schema=False)
def panel_salud_datos(request: Request, db: Session = Depends(get_operator_db)):
    from ..config import resumen_configuracion

    try:
        salud = analizar_salud_catalogo(db, incluir_anomalias=True)
    except Exception:
        db.rollback()
        salud = {"error": "No se pudo auditar el catálogo sin contexto de cliente."}
    return TEMPLATES.TemplateResponse(
        request,
        "admin/salud_datos.html",
        {
            "salud": salud,
            "configuracion": resumen_configuracion(),
            "operador": db.info.get("auth_email", ""),
            "msg": request.query_params.get("msg", ""),
            "error": request.query_params.get("error", ""),
        },
        headers={"Cache-Control": "no-store"},
    )


@router.get("/admin/api-keys", response_class=HTMLResponse, include_in_schema=False)
def panel_api_keys(request: Request, db: Session = Depends(get_operator_db)):
    return TEMPLATES.TemplateResponse(
        request,
        "admin/api_keys.html",
        {
            "claves": listar_api_keys(db),
            "operador": db.info.get("auth_email", ""),
            "token_nuevo": "",
            "msg": request.query_params.get("msg", ""),
            "error": request.query_params.get("error", ""),
        },
        headers={"Cache-Control": "no-store"},
    )


@router.post("/admin/api-keys/crear", include_in_schema=False)
async def api_keys_crear(request: Request, db: Session = Depends(get_operator_db)):
    form = await request.form()
    scopes = [s.strip() for s in str(form.get("scopes") or "").split(",") if s.strip()]
    try:
        _, token = crear_api_key(
            db,
            nombre=str(form.get("nombre") or ""),
            scopes=scopes,
            operador_email=str(db.info.get("auth_email") or ""),
        )
        db.commit()
        _auditar_admin(db, request, accion="api_key.creada", entidad="api_keys_operador", detalle={"nombre": str(form.get("nombre") or "")[:100]})
        return TEMPLATES.TemplateResponse(
            request,
            "admin/api_keys.html",
            {
                "claves": listar_api_keys(db),
                "operador": db.info.get("auth_email", ""),
                "token_nuevo": token,
                "msg": "Clave creada. Guárdala ahora; no se podrá volver a ver.",
                "error": "",
            },
            headers={"Cache-Control": "no-store"},
        )
    except GestionWebError as exc:
        db.rollback()
        return _redirect("/admin/api-keys", error=str(exc))
    except Exception:
        db.rollback()
        return _redirect("/admin/api-keys", error="Error inesperado al crear la clave.")


@router.post("/admin/api-keys/{api_key_id}/revocar", include_in_schema=False)
def api_keys_revocar(api_key_id: int, request: Request, db: Session = Depends(get_operator_db)):
    try:
        revocar_api_key(db, api_key_id)
        db.commit()
        _auditar_admin(db, request, accion="api_key.revocada", entidad="api_keys_operador", entidad_id=api_key_id)
    except GestionWebError as exc:
        db.rollback()
        return _redirect("/admin/api-keys", error=str(exc))
    return _redirect("/admin/api-keys", msg="Clave revocada.")
