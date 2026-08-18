"""Panel de operador: licencias y diagnóstico operativo (excepción multi-tenant)."""  # E4-001 — router por dominio

from fastapi import APIRouter

from .common import *  # noqa: F401,F403  (re-exporta modelos, servicios y utilidades)

router = APIRouter()

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


@router.get("/admin/licencias", response_class=HTMLResponse, include_in_schema=False)
def panel_licencias(request: Request, db: Session = Depends(get_operator_db)):
    return _render_licencias(request, db)


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


@router.post("/admin/licencias", include_in_schema=False)
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


@router.post("/admin/licencias/{licencia_id}/cancelar", include_in_schema=False)
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
        _compra, licencia = activar_compra(
            db,
            compra_id=compra_id,
            operador_email=str(db.info.get("auth_email") or ""),
        )
        db.commit()
    except (GestionCompraError, ValueError) as exc:
        db.rollback()
        return _redirect("/admin/compras", error=str(exc))
    except Exception:
        db.rollback()
        log.error("Error activando compra #%s:\n%s", compra_id, traceback.format_exc())
        raise
    return _redirect(
        "/admin/compras",
        msg=f"Compra #{compra_id} activada · licencia #{licencia.id} concedida.",
    )


@router.post("/admin/compras/{compra_id}/rechazar", include_in_schema=False)
def rechazar_compra_web(
    compra_id: int, request: Request, db: Session = Depends(get_operator_db)
):
    from ..services.compras import GestionCompraError, rechazar_compra

    try:
        rechazar_compra(
            db,
            compra_id=compra_id,
            operador_email=str(db.info.get("auth_email") or ""),
        )
        db.commit()
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
