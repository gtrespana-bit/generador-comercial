"""Panel de operador: licencias y diagnóstico operativo (excepción multi-tenant)."""  # E4-001 — router por dominio

import hmac

from fastapi import APIRouter, Form

from .common import *  # noqa: F401,F403  (re-exporta modelos, servicios y utilidades)
from ..panel_arquitectura import es_destino_panel
from .admin_paginas import _respuesta as _respuesta_panel, contexto_sistema
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
    actualizar_aviso,
    actualizar_release,
    borrar_crm,
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

#: A dónde devuelve cada acción del panel. Con las áreas agrupadas en pestañas
#: el destino ya no es una ruta suelta: es la pestaña concreta, y se puede
#: sobrescribir con `volver` cuando la acción se disparó desde otra pantalla
#: (la ficha de un cliente, la campana, el buscador).
VOLVER_ESTADO = "/admin/sistema?tab=estado"
VOLVER_CONTRATOS = "/admin/ingresos?tab=contratos"
VOLVER_COMPRAS = "/admin/ingresos?tab=compras"
VOLVER_COBROS = "/admin/ingresos?tab=cobros"
VOLVER_RENOVACIONES = "/admin/ingresos?tab=renovaciones"
VOLVER_EQUIPO = "/admin/sistema?tab=equipo"
VOLVER_ACCESOS = "/admin/sistema?tab=accesos"
VOLVER_AUDITORIA = "/admin/sistema?tab=auditoria"
VOLVER_AUTOMATIZACIONES = "/admin/sistema?tab=automatizaciones"
VOLVER_CORREOS = "/admin/sistema?tab=correos"
VOLVER_CONTENIDO = "/admin/web?tab=contenido"
VOLVER_AVISOS = "/admin/web?tab=avisos"
VOLVER_VERSIONES = "/admin/web?tab=versiones"
VOLVER_DIRECTORIO = "/admin/clientes?tab=directorio"
VOLVER_PIPELINE = "/admin/clientes?tab=pipeline"

#: Ruta del trabajo programado de Vercel (vercel.json → `crons`). Un solo
#: punto de verdad: `tests/test_vercel_cron_config.py` comprueba que la ruta
#: declarada en vercel.json coincide con esta, y /readyz lo publica.
CRON_RECORDATORIOS_PATH = "/api/cron/recordatorios-vencimiento"

#: Ruta del mantenimiento diario (respaldo automático E4-021 + verificación
#: con alerta E4-023). También declarada en vercel.json → `crons`; el plan
#: Hobby admite hasta 2 trabajos diarios, Pro hasta 40.
CRON_MANTENIMIENTO_PATH = "/api/cron/mantenimiento"

# ---------------------------------------------------------------------------
# Acciones del panel de operador (E1-060)
#
# Este módulo contiene **solo acciones** (POST) y los trabajos programados: las
# pantallas —Hoy, Clientes, Ingresos, Web, Analítica y Sistema— viven en
# `app/routers/admin_paginas.py`. Separarlas es lo que permite que seis pantallas
# sustituyan a las diecisiete rutas planas que había.
#
# Ninguna de estas rutas escapa al control de acceso: son la única excepción al
# aislamiento multi-tenant y por eso están agrupadas y marcadas. `get_operator_db`
# exige que el correo autenticado y verificado figure en COTIZAT_OPERADORES; en
# PostgreSQL, además, las políticas RLS de `licencias` solo devuelven filas a una
# sesión marcada como operador. Después de cada acción se audita y se vuelve a la
# pestaña de origen (`_volver_a`), nunca a una página fija.
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
        return _redirect(VOLVER_EQUIPO, error=str(exc))
    except Exception:
        db.rollback()
        log.error("Error creando operador:\n%s", traceback.format_exc())
        raise
    return _redirect(VOLVER_EQUIPO, msg=f"Operador {operador.email} dado de alta.")


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
        return _redirect(VOLVER_EQUIPO, error=str(exc))
    except Exception:
        db.rollback()
        log.error("Error cambiando rol de operador:\n%s", traceback.format_exc())
        raise
    return _redirect(VOLVER_EQUIPO, msg=f"Rol de {operador.email} actualizado.")


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
        return _redirect(VOLVER_EQUIPO, error=str(exc))
    except Exception:
        db.rollback()
        log.error("Error suspendiendo operador:\n%s", traceback.format_exc())
        raise
    return _redirect(VOLVER_EQUIPO, msg=f"{operador.email} suspendido.")


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
        return _redirect(VOLVER_EQUIPO, error=str(exc))
    except Exception:
        db.rollback()
        log.error("Error activando operador:\n%s", traceback.format_exc())
        raise
    return _redirect(VOLVER_EQUIPO, msg=f"{operador.email} activado.")


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
            f"/admin/sistema?tab=correos&destino={quote(destino)}",
            error="Escribe un email de destino válido.",
        )
    try:
        envio_id = enviar_correo_prueba(slug, destino)
    except ValueError as exc:
        return _redirect(VOLVER_CORREOS, error=str(exc))
    except EmailNotConfigured as exc:
        return _redirect(
            f"/admin/sistema?tab=correos&destino={quote(destino)}",
            error=f"Correo no configurado: {exc}",
        )
    except (EmailSendError, EmailValidationError) as exc:
        log.warning("No se pudo enviar el correo de prueba (%s).", exc)
        return _redirect(
            f"/admin/sistema?tab=correos&destino={quote(destino)}",
            error=f"No se pudo enviar: {exc}",
        )
    except Exception:
        log.error("Error enviando correo de prueba:\n%s", traceback.format_exc())
        return _redirect(
            f"/admin/sistema?tab=correos&destino={quote(destino)}",
            error="Error inesperado enviando el correo de prueba.",
        )
    return _redirect(
        f"/admin/sistema?tab=correos&destino={quote(destino)}",
        msg=f"Correo enviado a {destino} (id {envio_id}).",
    )


#: Importe por omisión de una licencia de pago según su duración, tomado de
#: los planes publicados (`app/datos_pago.py`): así el botón rápido «pago
#: anual» no obliga a teclear 89.00 cada vez, y un importe distinto sigue
#: pudiendo escribirse en el formulario completo.
_IMPORTE_POR_DURACION = {
    ficha["duracion_licencia"]: ficha["importe"] for ficha in PLANES.values()
}


def _importe_formulario(form, origen: str):
    """Importe de una licencia creada desde el panel cuando no se teclea.

    Una licencia de pago sin importe es un error de negocio (``crear_licencia``
    lo rechaza), y el formulario largo no lo pide cuando el precio ya se conoce
    por la duración. La concesión rápida aplicaba esa regla y el alta manual no:
    ahora las dos usan el mismo importe publicado.
    """
    importe = form.get("importe")
    if importe not in (None, ""):
        return str(importe)
    if (origen or "").strip().lower() == "pago":
        return _IMPORTE_POR_DURACION.get(str(form.get("duracion") or "").strip(), 0.0)
    return 0.0

def _volver_a(form, por_omision: str = "/admin") -> str:
    """Destino de la redirección tras una acción, limitado a las páginas del panel.

    Las mismas acciones se disparan desde varias pantallas (la lista de
    contratos, la ficha de un cliente, la campana). Devolver siempre al mismo
    sitio sacaría al operador de donde estaba trabajando, así que cada
    formulario trae su `volver`; se valida contra el mapa de rutas y pestañas
    del panel porque un `volver` libre en un POST es una redirección abierta.
    """
    destino = str((form.get("volver") if form is not None else "") or "").strip()
    return destino if es_destino_panel(destino) else por_omision


def _volver_valor(valor, por_omision: str = "/admin") -> str:
    """Destino a partir del valor `volver` ya leído (query, form o dict).

    Las rutas sincrónicas no pueden hacer `await request.form()`, así que
    declaran el campo como parámetro `Form` de FastAPI y lo pasan por aquí.
    """
    destino = str(valor or "").strip()
    return destino if es_destino_panel(destino) else por_omision


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
            importe=_importe_formulario(form, str(form.get("origen") or "")),
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
def enviar_avisos_web(
    request: Request,
    db: Session = Depends(get_operator_db),
    volver: str = Form(""),
):
    """Envía los avisos de vencimiento a las organizaciones por vencer.

    Lo dispara el operador a mano: no hay trabajos programados en un
    despliegue serverless. El envío real lo hace Resend; la licencia queda
    anotada con la fecha y los destinatarios para no reenviar el mismo día.
    """
    from ..services.email import EmailNotConfigured, enviar_aviso_licencia

    destino = _volver_valor(volver, VOLVER_RENOVACIONES)
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
            destino,
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
            destino,
            msg="Ninguna licencia vence dentro del plazo de aviso.",
        )
    if resultado["fallidas"]:
        detalle = "; ".join(
            f"{nombre}: {exc}" for nombre, exc in resultado["fallidas"]
        )
        if partes:
            partes.append(f"errores: {detalle}")
            return _redirect(destino, error=" | ".join(partes))
        return _redirect(
            destino, error=f"No se pudo enviar ningún aviso: {detalle}"
        )
    return _redirect(destino, msg="; ".join(partes) + ".")


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


@router.post("/admin/compras/{compra_id}/activar", include_in_schema=False)
def activar_compra_web(
    compra_id: int,
    request: Request,
    db: Session = Depends(get_operator_db),
    volver: str = Form(""),
):
    """Verifica el comprobante y concede la licencia del plan comprado."""
    from ..services.compras import GestionCompraError, activar_compra

    destino = _volver_valor(volver, VOLVER_COMPRAS)
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
        return _redirect(destino, error=str(exc))
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
        destino,
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
    compra_id: int,
    request: Request,
    db: Session = Depends(get_operator_db),
    volver: str = Form(""),
):
    from ..services.compras import GestionCompraError, rechazar_compra

    destino = _volver_valor(volver, VOLVER_COMPRAS)
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
        return _redirect(destino, error=str(exc))
    except Exception:
        db.rollback()
        log.error("Error rechazando compra #%s:\n%s", compra_id, traceback.format_exc())
        raise
    return _redirect(destino, msg=f"Compra #{compra_id} rechazada.")


@router.post("/admin/avisos/{aviso_id}/editar", include_in_schema=False)
async def avisos_editar(aviso_id: int, request: Request, db: Session = Depends(get_operator_db)):
    """Edita un aviso existente sin borrarlo y volverlo a crear.

    El panel solo tenía «crear» y «ocultar/mostrar»: corregir una tilde en un
    aviso publicado obligaba a crear otro. Se reutiliza el servicio ya probado
    `actualizar_aviso`, que valida tipo, nivel y rango de fechas.
    """
    form = await request.form()
    destino = _volver_a(form, VOLVER_AVISOS)
    try:
        actualizar_aviso(
            db,
            aviso_id,
            campos={
                "tipo": str(form.get("tipo") or ""),
                "nivel": str(form.get("nivel") or ""),
                "titulo": str(form.get("titulo") or ""),
                "mensaje": str(form.get("mensaje") or ""),
                "activo": str(form.get("activo") or "").lower() in {"1", "true", "on", "si"},
                "inicio": _fecha_desde_form(str(form.get("inicio") or "")),
                "fin": _fecha_desde_form(str(form.get("fin") or "")),
            },
            operador_email=str(db.info.get("auth_email") or ""),
        )
        db.commit()
        _auditar_admin(
            db, request, accion="web.aviso_editado", entidad="avisos_web", entidad_id=aviso_id
        )
    except GestionWebError as exc:
        db.rollback()
        return _redirect(destino, error=str(exc))
    except Exception:
        db.rollback()
        log.error("Error editando el aviso #%s:\n%s", aviso_id, traceback.format_exc())
        return _redirect(destino, error="Error inesperado al guardar el aviso.")
    return _redirect(destino, msg="Aviso actualizado.")


@router.post("/admin/releases/{release_id}/editar", include_in_schema=False)
async def releases_editar(release_id: int, request: Request, db: Session = Depends(get_operator_db)):
    """Corrige una versión publicada desde su propia fila del changelog."""
    form = await request.form()
    destino = _volver_a(form, VOLVER_VERSIONES)
    try:
        actualizar_release(
            db,
            release_id,
            campos={
                "version": str(form.get("version") or ""),
                "titulo": str(form.get("titulo") or ""),
                "notas": str(form.get("notas") or ""),
                "destacado": str(form.get("destacado") or "").lower() in {"1", "true", "on", "si"},
                "publicado": str(form.get("publicado") or "").lower() in {"1", "true", "on", "si"},
                "fecha": _fecha_desde_form(str(form.get("fecha") or "")),
            },
            operador_email=str(db.info.get("auth_email") or ""),
        )
        db.commit()
        _auditar_admin(
            db, request, accion="web.release_editada", entidad="releases", entidad_id=release_id
        )
    except GestionWebError as exc:
        db.rollback()
        return _redirect(destino, error=str(exc))
    except Exception:
        db.rollback()
        log.error("Error editando la versión #%s:\n%s", release_id, traceback.format_exc())
        return _redirect(destino, error="Error inesperado al guardar la versión.")
    return _redirect(destino, msg="Versión actualizada.")


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
# Notas de cliente y ejecución manual de reglas (antes páginas aparte)
# ---------------------------------------------------------------------------


@router.post("/admin/clientes/{organizacion_id}/notas", include_in_schema=False)
async def crear_nota_cliente_web(
    organizacion_id: int,
    request: Request,
    db: Session = Depends(get_operator_db),
):
    """Guarda una nota interna de gestión sobre el cliente (best-effort)."""
    from ..services.panel_clientes import crear_nota_operador

    form = await request.form()
    destino = _volver_a(form, f"/admin/clientes/{organizacion_id}?tab=gestion")
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
        return _redirect(destino, error=str(exc))
    except Exception:
        db.rollback()
        log.error("Error creando nota de cliente #%s:\n%s", organizacion_id, traceback.format_exc())
        return _redirect(destino, error="No se pudo guardar la nota.")
    return _redirect(destino, msg="Nota guardada.")


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
        return _redirect(VOLVER_AUTOMATIZACIONES, error=f"Correo no configurado: {exc}")
    except GestionAutomatizacionError as exc:
        db.rollback()
        return _redirect(VOLVER_AUTOMATIZACIONES, error=str(exc))
    except Exception:
        db.rollback()
        log.error("Error ejecutando automatización %s:\n%s", regla, traceback.format_exc())
        return _redirect(VOLVER_AUTOMATIZACIONES, error="Error inesperado al ejecutar la regla.")

    return _redirect(VOLVER_AUTOMATIZACIONES, msg=f"Regla «{regla}» ejecutada.")


# ---------------------------------------------------------------------------
# La web se gobierna desde el panel (C1/C2/C4/C5, D3): contenido, avisos,
# versiones y flags. Todo se edita en la pantalla de Web y de Sistema › Accesos.
# ---------------------------------------------------------------------------

def _fecha_desde_form(valor: str | None):
    valor = (valor or "").strip()
    if not valor:
        return None
    try:
        return date.fromisoformat(valor)
    except ValueError:
        raise GestionWebError("La fecha indicada no es válida.") from None


@router.post("/admin/web/guardar", include_in_schema=False)
async def web_guardar(request: Request, db: Session = Depends(get_operator_db)):
    form = await request.form()
    clave = str(form.get("clave") or "")
    try:
        campos = json.loads(str(form.get("contenido_json") or "{}"))
    except ValueError:
        return _redirect(f"/admin/web?tab=contenido&clave={quote(clave, safe='')}", error="El contenido no es JSON válido.")
    try:
        guardar_contenido(
            db, clave=clave, campos=campos,
            operador_email=str(db.info.get("auth_email") or ""),
        )
        db.commit()
        _auditar_admin(db, request, accion="web.contenido_guardado", entidad="contenido_web", detalle={"clave": clave})
    except GestionWebError as exc:
        db.rollback()
        return _redirect(f"/admin/web?tab=contenido&clave={quote(clave, safe='')}", error=str(exc))
    except Exception:
        db.rollback()
        return _redirect(VOLVER_CONTENIDO, error="Error inesperado al guardar el contenido.")
    return _redirect(f"/admin/web?tab=contenido&clave={quote(clave, safe='')}", msg="Borrador guardado; aún no es público.")


@router.post("/admin/web/{clave}/publicar", include_in_schema=False)
def web_publicar(clave: str, request: Request, db: Session = Depends(get_operator_db)):
    try:
        publicar_contenido(db, clave=clave, operador_email=str(db.info.get("auth_email") or ""))
        db.commit()
        _auditar_admin(db, request, accion="web.contenido_publicado", entidad="contenido_web", detalle={"clave": clave})
    except GestionWebError as exc:
        db.rollback()
        return _redirect(VOLVER_CONTENIDO, error=str(exc))
    except Exception:
        db.rollback()
        return _redirect(VOLVER_CONTENIDO, error="Error inesperado al publicar.")
    return _redirect(VOLVER_CONTENIDO, msg="Contenido publicado.")


@router.post("/admin/web/{clave}/descartar", include_in_schema=False)
def web_descartar(clave: str, request: Request, db: Session = Depends(get_operator_db)):
    try:
        descartar_contenido(db, clave=clave)
        db.commit()
        _auditar_admin(db, request, accion="web.contenido_descartado", entidad="contenido_web", detalle={"clave": clave})
    except GestionWebError as exc:
        db.rollback()
        return _redirect(VOLVER_CONTENIDO, error=str(exc))
    except Exception:
        db.rollback()
        return _redirect(VOLVER_CONTENIDO, error="Error inesperado al descartar.")
    return _redirect(VOLVER_CONTENIDO, msg="Borrador descartado; se mantiene lo publicado.")


@router.post("/admin/avisos/crear", include_in_schema=False)
async def avisos_crear(request: Request, db: Session = Depends(get_operator_db)):
    form = await request.form()
    destino = _volver_a(form, VOLVER_AVISOS)
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
        return _redirect(destino, error=str(exc))
    except Exception:
        db.rollback()
        return _redirect(destino, error="Error inesperado al crear el aviso.")
    return _redirect(destino, msg="Aviso creado.")


@router.post("/admin/avisos/{aviso_id}/alternar", include_in_schema=False)
def avisos_alternar(
    aviso_id: int,
    request: Request,
    db: Session = Depends(get_operator_db),
    volver: str = Form(""),
):
    destino = _volver_valor(volver, VOLVER_AVISOS)
    activo = str(request.query_params.get("activo", "")).lower() in {"1", "true", "on", "si"}
    try:
        alternar_aviso(db, aviso_id, activo=activo)
        db.commit()
        _auditar_admin(db, request, accion="web.aviso_alternado", entidad="avisos_web", entidad_id=aviso_id, detalle={"activo": activo})
    except GestionWebError as exc:
        db.rollback()
        return _redirect(destino, error=str(exc))
    return _redirect(destino, msg="Estado del aviso actualizado.")


@router.post("/admin/releases/crear", include_in_schema=False)
async def releases_crear(request: Request, db: Session = Depends(get_operator_db)):
    form = await request.form()
    destino = _volver_a(form, VOLVER_VERSIONES)
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
        return _redirect(destino, error=str(exc))
    except Exception:
        db.rollback()
        return _redirect(destino, error="Error inesperado al crear la versión.")
    return _redirect(destino, msg="Versión creada.")


@router.post("/admin/releases/{release_id}/alternar", include_in_schema=False)
def releases_alternar(
    release_id: int,
    request: Request,
    db: Session = Depends(get_operator_db),
    volver: str = Form(""),
):
    destino = _volver_valor(volver, VOLVER_VERSIONES)
    publicado = str(request.query_params.get("publicado", "")).lower() in {"1", "true", "on", "si"}
    try:
        alternar_release(db, release_id, publicado=publicado)
        db.commit()
        _auditar_admin(db, request, accion="web.release_alternada", entidad="releases", entidad_id=release_id, detalle={"publicado": publicado})
    except GestionWebError as exc:
        db.rollback()
        return _redirect(destino, error=str(exc))
    return _redirect(destino, msg="Visibilidad de la versión actualizada.")


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
        return _redirect(VOLVER_ACCESOS, error=str(exc))
    return _redirect(VOLVER_ACCESOS, msg="Feature flag actualizado.")


# ---------------------------------------------------------------------------
# CRM ligero (B4), vistas guardadas y API keys (A6)
# ---------------------------------------------------------------------------


@router.post("/admin/crm/{organizacion_id}/guardar", include_in_schema=False)
async def crm_guardar(organizacion_id: int, request: Request, db: Session = Depends(get_operator_db)):
    form = await request.form()
    destino = _volver_a(form, VOLVER_PIPELINE)
    estado = str(form.get("estado") or "").strip().lower()
    try:
        if estado:
            guardar_crm(
                db,
                organizacion_id=organizacion_id,
                estado=estado,
                proximo_contacto=_fecha_desde_form(str(form.get("proximo_contacto") or "")),
                notas=str(form.get("notas") or ""),
                operador_email=str(db.info.get("auth_email") or ""),
            )
            detalle = {"estado": estado}
        else:
            # «Sin asignar» no es un estado: borra la ficha comercial para que
            # el cliente salga del embudo tal y como entró.
            borrar_crm(db, organizacion_id=organizacion_id)
            detalle = {"estado": "", "accion": "borrado"}
        db.commit()
        _auditar_admin(db, request, accion="crm.cliente_actualizado", entidad="crm_clientes",
                       organizacion_id=organizacion_id, detalle=detalle)
    except GestionWebError as exc:
        db.rollback()
        return _redirect(destino, error=str(exc))
    except Exception:
        db.rollback()
        return _redirect(destino, error="Error inesperado al guardar el CRM.")
    return _redirect(destino, msg="Cliente actualizado en el canal.")


@router.post("/admin/vistas/crear", include_in_schema=False)
async def vistas_crear(request: Request, db: Session = Depends(get_operator_db)):
    form = await request.form()
    destino = _volver_a(form, VOLVER_DIRECTORIO)
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
        return _redirect(destino, error=str(exc) if isinstance(exc, GestionWebError) else "Los filtros o columnas deben ser JSON válido.")
    return _redirect(destino, msg="Vista guardada en su lista.")


@router.post("/admin/vistas/{vista_id}/eliminar", include_in_schema=False)
def vistas_eliminar(
    vista_id: int,
    request: Request,
    db: Session = Depends(get_operator_db),
    volver: str = Form(""),
):
    destino = _volver_valor(volver, VOLVER_DIRECTORIO)
    try:
        eliminar_vista(db, vista_id)
        db.commit()
        _auditar_admin(db, request, accion="admin.vista_eliminada", entidad="vistas_guardadas", entidad_id=vista_id)
    except GestionWebError as exc:
        db.rollback()
        return _redirect(destino, error=str(exc))
    return _redirect(destino, msg="Vista eliminada.")


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
        # El token solo existe en esta respuesta: no viaja por la URL ni se
        # guarda en sesión, así que recargar la página ya no lo muestra.
        return _respuesta_panel(
            request,
            "sistema.html",
            contexto_sistema(request, db, pestana="accesos",
                             msg="Clave creada. Guárdala ahora; no se podrá volver a ver.",
                             extra={"token_nuevo": token}),
        )
    except GestionWebError as exc:
        db.rollback()
        return _redirect(VOLVER_ACCESOS, error=str(exc))
    except Exception:
        db.rollback()
        return _redirect(VOLVER_ACCESOS, error="Error inesperado al crear la clave.")


@router.post("/admin/api-keys/{api_key_id}/revocar", include_in_schema=False)
def api_keys_revocar(api_key_id: int, request: Request, db: Session = Depends(get_operator_db)):
    try:
        revocar_api_key(db, api_key_id)
        db.commit()
        _auditar_admin(db, request, accion="api_key.revocada", entidad="api_keys_operador", entidad_id=api_key_id)
    except GestionWebError as exc:
        db.rollback()
        return _redirect(VOLVER_ACCESOS, error=str(exc))
    return _redirect(VOLVER_ACCESOS, msg="Clave revocada.")
