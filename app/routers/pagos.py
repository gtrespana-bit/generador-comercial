"""Compra de planes con pago manual: el cliente elige método, declara la
verificación y adjunta su comprobante (E1-059 cobro manual)."""

from __future__ import annotations

import io
import json
import logging
from datetime import date
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Form, Request

from . import common
from .common import *  # noqa: F401,F403  (re-exporta modelos, servicios y utilidades)
from ..analytics import encolar_purchase_unico
from ..database import get_stripe_webhook_db
from ..services import auditoria
from ..datos_pago import (
    METODO_STRIPE,
    METODOS_PAGO,
    PLANES,
    PLAN_PENDIENTE_COOKIE,
    metodo_info,
    plan_info,
)

router = APIRouter()

log = logging.getLogger("cotizat.pagos")

_EXT_IMG = {".png", ".jpg", ".jpeg", ".webp"}
_MAX_COMPROBANTE = 12 * 1024 * 1024


def _plan_o_redirect(request: Request, plan: str):
    """Devuelve (ficha|None) y redirige a /pago si el plan no existe."""
    try:
        return plan_info(plan)
    except KeyError:
        return None


def _cookie_secure() -> bool:
    """Flag `Secure` de las cookies, coherente con el resto de la app."""
    try:
        return SupabaseAuthSettings.from_environment().cookie_secure
    except AuthNotConfigured:
        return True


def _set_plan_pendiente_cookie(response, plan: str) -> None:
    """Recuerda el plan elegido para retomarlo tras el alta de la cuenta."""
    response.set_cookie(
        PLAN_PENDIENTE_COOKIE,
        plan,
        max_age=60 * 60 * 24 * 7,
        httponly=True,
        secure=_cookie_secure(),
        samesite="lax",
        path="/",
    )


def _metodos_para_pais(codigo_pais: str) -> dict[str, dict]:
    """Devuelve los métodos manuales disponibles en el país de cobro.

    Pago móvil y Kontigo son canales venezolanos. Mientras se habilitan
    cuentas locales en otros mercados, fuera de Venezuela solo se publica
    USDT, que sí puede recibirse internacionalmente. Stripe se procesa aparte.
    """
    if codigo_pais == "VE":
        return METODOS_PAGO
    return {"usdt": METODOS_PAGO["usdt"]}


def _pais_pago(request: Request, db: Session, organizacion) -> str:
    """Resuelve el país de cobro: selector explícito, luego país de la empresa."""
    from ..paises import PAISES

    elegido = str(request.query_params.get("pais") or "").strip().upper()
    if elegido in PAISES:
        return elegido

    if organizacion is not None:
        configuracion = (
            db.query(Configuracion)
            .filter(Configuracion.organizacion_id == organizacion.id)
            .first()
        )
        nombre_original = str(configuracion.empresa_pais if configuracion else "").strip()
        if nombre_original.upper() in PAISES:
            return nombre_original.upper()
        nombre = nombre_original.casefold()
        for codigo, datos in PAISES.items():
            if datos["nombre"].casefold() == nombre:
                return codigo

    # Compatibilidad con organizaciones creadas antes del selector de país.
    return "VE"


def _clear_plan_pendiente_cookie(response) -> None:
    """Elimina la intención de compra (compra completada o descartada)."""
    response.delete_cookie(
        PLAN_PENDIENTE_COOKIE,
        path="/",
        secure=_cookie_secure(),
        httponly=True,
        samesite="lax",
    )


@router.get("/pago/elegir", include_in_schema=False)
def elegir_plan(request: Request, plan: str = "", pais: str = ""):
    """Recuerda el plan elegido y lleva al checkout.

    El checkout exige sesión y organización; esta ruta guarda la intención en
    una cookie ANTES de eso, de modo que sobreviva al registro, la confirmación
    de email y el alta de empresa, y pueda retomarse desde el panel.
    """
    if _plan_o_redirect(request, plan) is None:
        return RedirectResponse("/pago", status_code=303)
    from ..paises import PAISES

    pais_url = str(pais or "").strip().upper()
    sufijo_pais = f"&pais={quote(pais_url)}" if pais_url in PAISES else ""
    response = RedirectResponse(f"/pago/comprar?plan={quote(plan)}{sufijo_pais}", status_code=303)
    _set_plan_pendiente_cookie(response, plan)
    return response


@router.post("/pago/descartar", include_in_schema=False)
def descartar_plan_pendiente():
    """Descarta la intención de compra recordada en la cookie."""
    response = RedirectResponse("/inicio", status_code=303)
    _clear_plan_pendiente_cookie(response)
    return response


@router.get("/pago/comprar", response_class=HTMLResponse, include_in_schema=False)
def comprar_plan(
    request: Request, plan: str = "", db: Session = Depends(get_db_renovacion)
):
    """Página de compra: resumen del plan + métodos de pago + formulario."""
    ficha = _plan_o_redirect(request, plan)
    if ficha is None:
        return RedirectResponse("/pago", status_code=303)

    organizacion = db.get(Organizacion, int(db.info.get("organizacion_id") or 0))
    usuario = db.get(Usuario, int(db.info.get("usuario_id") or 0))
    from ..services.stripe import stripe_configurado
    from ..paises import PAISES, lista_paises

    pais_pago = _pais_pago(request, db, organizacion)

    return TEMPLATES.TemplateResponse(
        request,
        "pago/comprar.html",
        {
            "plan": plan,
            "plan_ficha": ficha,
            "metodos": _metodos_para_pais(pais_pago),
            "metodos_json": json.dumps(_metodos_para_pais(pais_pago), ensure_ascii=False),
            "pais_pago": PAISES[pais_pago],
            "paises_pago": lista_paises(),
            "organizacion_nombre": organizacion.nombre if organizacion else "",
            "usuario_email": usuario.email if usuario else "",
            "hoy": date.today().isoformat(),
            "error": request.query_params.get("error", ""),
            "stripe_disponible": stripe_configurado(),
        },
    )


def _validar_comprobante(nombre: str, datos: bytes) -> str:
    """Valida imagen o PDF y devuelve el MIME; vacío si no es válido."""
    nombre = str(nombre or "").strip()
    if not nombre:
        return ""
    ext = Path(nombre).suffix.lower()
    if not datos or len(datos) > _MAX_COMPROBANTE:
        return ""
    if ext in _EXT_IMG:
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
        return {
            "PNG": "image/png",
            "JPEG": "image/jpeg",
            "WEBP": "image/webp",
        }.get(formato, "")
    if ext == ".pdf" and datos.startswith(b"%PDF-"):
        return "application/pdf"
    return ""


@router.post("/pago/comprar", include_in_schema=False)
async def registrar_compra(
    request: Request,
    plan: str = Form(""),
    metodo_pago: str = Form(""),
    db: Session = Depends(get_db_renovacion),
):
    """Registra la compra: guarda comprobante, crea la compra y notifica."""
    from ..services.compras import GestionCompraError, crear_compra
    from ..services.email import (
        EmailNotConfigured,
        EmailValidationError,
        enviar_compra_por_email,
    )
    from ..utils import fmt_monto

    form = await request.form()
    ficha = _plan_o_redirect(request, plan)
    if ficha is None:
        return RedirectResponse("/pago", status_code=303)

    organizacion_id = int(db.info.get("organizacion_id") or 0)
    organizacion = db.get(Organizacion, organizacion_id)
    from ..paises import PAISES

    pais_elegido = str(form.get("pais_pago") or "").strip().upper()
    pais_pago = pais_elegido if pais_elegido in PAISES else _pais_pago(request, db, organizacion)
    metodos_disponibles = _metodos_para_pais(pais_pago)

    try:
        ficha_metodo = metodo_info(metodo_pago)
    except KeyError:
        ficha_metodo = None
    if (
        ficha_metodo is None
        or metodo_pago == METODO_STRIPE
        or metodo_pago not in metodos_disponibles
    ):
        return RedirectResponse(
            f"/pago/comprar?plan={quote(plan)}&error=Selecciona un método de pago.",
            status_code=303,
        )

    # Datos de verificación: solo los campos declarados para el método.
    verificacion = {}
    for campo, _etiqueta, _tipo, _placeholder in ficha_metodo["verificacion"]:
        valor = str(form.get(campo) or "").strip()
        if valor:
            verificacion[campo] = valor[:300]

    # Comprobante. Cada método publica su propio campo de archivo con nombre
    # único (``comprobante_<clave>``), así que se lee solo el del método
    # elegido. Antes, los cuatro paneles compartían ``name="comprobante"`` y el
    # navegador enviaba una parte por cada método (tres vacías); el enlace del
    # ``UploadFile`` resultaba ambiguo y, salvo con el último método, el
    # servidor recibía el archivo vacío y rechazaba la compra con
    # «Adjunta el comprobante de pago para continuar» aunque se hubiera subido.
    datos_comprobante = b""
    nombre_comprobante = ""
    mime_comprobante = ""
    parte = form.get(f"comprobante_{metodo_pago}")
    # ``request.form()`` devuelve un UploadFile cuando el campo trae archivo y
    # una cadena vacía cuando no se seleccionó nada.
    if parte is not None and not isinstance(parte, str):
        nombre_comprobante = Path(parte.filename or "").name[:255]
        datos_comprobante = await parte.read()
        mime_comprobante = _validar_comprobante(nombre_comprobante, datos_comprobante)
        if not mime_comprobante:
            return RedirectResponse(
                f"/pago/comprar?plan={quote(plan)}&error="
                "El comprobante debe ser una imagen (PNG, JPG, WEBP) o un PDF "
                "de hasta 12 MB.",
                status_code=303,
            )

    referencia_comprobante = ""
    if datos_comprobante:
        try:
            guardado = save_object(
                db,
                datos_comprobante,
                "comprobantes",
                nombre_comprobante,
                mime_comprobante,
            )
            referencia_comprobante = guardado.reference
        except StorageError:
            return RedirectResponse(
                f"/pago/comprar?plan={quote(plan)}&error="
                "No se pudo guardar el comprobante. Inténtalo de nuevo.",
                status_code=303,
            )

    organizacion_id = int(db.info.get("organizacion_id") or 0)
    usuario = db.get(Usuario, int(db.info.get("usuario_id") or 0))
    organizacion = db.get(Organizacion, organizacion_id)

    try:
        compra = crear_compra(
            db,
            organizacion_id=organizacion_id,
            plan=plan,
            metodo_pago=metodo_pago,
            datos_verificacion=verificacion,
            comprobante_reference=referencia_comprobante,
            comprobante_nombre=nombre_comprobante,
            comprobante_mime=mime_comprobante,
            creada_por_usuario_id=usuario.id if usuario else None,
            creada_por_email=usuario.email if usuario else "",
        )
        db.commit()
    except GestionCompraError as exc:
        db.rollback()
        return RedirectResponse(
            f"/pago/comprar?plan={quote(plan)}&error={quote(str(exc))}",
            status_code=303,
        )
    auditoria.registrar_evento(
        db,
        "plan.compra_registrada",
        entidad="compra",
        entidad_id=compra.id,
        detalle={"plan": plan, "metodo": metodo_pago},
    )

    # Notificación por email (no bloqueante): la compra ya está registrada.
    try:
        enviar_compra_por_email(
            nombre=usuario.nombre if usuario else "",
            email=usuario.email if usuario else "",
            organizacion_nombre=organizacion.nombre if organizacion else "",
            plan_nombre=ficha["nombre"],
            importe_texto=fmt_monto(ficha["importe"]),
            metodo_nombre=ficha_metodo["nombre"],
            verificacion=verificacion,
            comprobante_nombre=nombre_comprobante,
            comprobante_bytes=datos_comprobante,
        )
    except (EmailNotConfigured, EmailValidationError, StorageError) as exc:
        log.warning("Compra #%s creada sin notificación (%s).", compra.id, exc)

    respuesta = RedirectResponse(f"/pago/confirmacion?id={compra.id}", status_code=303)
    _clear_plan_pendiente_cookie(respuesta)
    return respuesta


@router.get("/pago/confirmacion", response_class=HTMLResponse, include_in_schema=False)
def confirmacion_compra(
    request: Request, id: int = 0, db: Session = Depends(get_db_renovacion)
):
    """Página de éxito: la compra quedó registrada y pendiente de verificación."""
    organizacion_id = int(db.info.get("organizacion_id") or 0)
    compra = db.query(CompraPlan).filter(
        CompraPlan.id == id, CompraPlan.organizacion_id == organizacion_id
    ).first()
    if compra is None:
        return RedirectResponse("/pago", status_code=303)
    try:
        plan_ficha = plan_info(compra.plan)
        metodo_ficha = metodo_info(compra.metodo_pago)
    except KeyError:
        return RedirectResponse("/pago", status_code=303)

    return TEMPLATES.TemplateResponse(
        request,
        "pago/confirmacion.html",
        {
            "compra": compra,
            "plan_nombre": plan_ficha["nombre"],
            "metodo_nombre": metodo_ficha["nombre"],
            "importe_texto": fmt_monto(compra.importe),
            "verificacion": compra.datos_verificacion_dict(),
        },
    )


@router.get("/pago/recibo/{compra_id}.pdf", include_in_schema=False)
def recibo_compra_web(
    compra_id: int, request: Request, db: Session = Depends(get_db_renovacion)
):
    """Recibo de una compra activada, descargable por el propio cliente.

    Es el gemelo de `/admin/licencias/{id}/recibo.pdf`, con la misma
    numeración (`CT-000013`) y el mismo PDF, pero armado desde `compras_plan`
    en vez de `licencias`: esta última está cerrada por RLS al operador, así
    que una ruta de cliente nunca puede leerla. El período concedido se copia
    a la compra al activarla justo para esto.

    El filtro por `organizacion_id` es lo que impide leer el recibo de otro:
    una compra ajena simplemente no existe para esta sesión.
    """
    organizacion_id = int(db.info.get("organizacion_id") or 0)
    compra = (
        db.query(CompraPlan)
        .filter(
            CompraPlan.id == compra_id,
            CompraPlan.organizacion_id == organizacion_id,
        )
        .first()
    )
    if compra is None:
        return _redirect("/configuracion", error="Esa compra no existe.")

    organizacion = db.get(Organizacion, organizacion_id)
    if organizacion is None:
        return _redirect("/configuracion", error="Esa compra no existe.")

    try:
        licencia = licencia_de_compra(compra)
        buffer = generar_recibo_licencia_pdf(licencia, organizacion)
    except GestionLicenciaError as exc:
        return _redirect("/configuracion", error=str(exc))
    except Exception:
        log.error(
            "Error generando el recibo de la compra #%s:\n%s",
            compra_id,
            traceback.format_exc(),
        )
        return _redirect(
            "/configuracion",
            error="No se pudo generar el recibo. Escríbenos y te lo enviamos.",
        )

    respuesta = _respuesta_pdf(
        buffer, f"recibo-{numero_recibo(licencia)}-{organizacion.slug}.pdf"
    )
    respuesta.headers["Cache-Control"] = "no-store"
    return respuesta


def _compra_por_sesion_local(db: Session, organizacion_id: int, session_id: str):
    return (
        db.query(CompraPlan)
        .filter(
            CompraPlan.organizacion_id == int(organizacion_id),
            CompraPlan.stripe_checkout_session_id == str(session_id or ""),
        )
        .first()
    )


def _origen_publico(request: Request) -> str:
    """Origen HTTPS para success/cancel de Stripe, nunca desde Host libre."""
    try:
        return public_app_url("/").rstrip("/")
    except AuthNotConfigured:
        return str(request.base_url).rstrip("/")


def _avisar_activacion_stripe(db: Session, compra, licencia) -> None:
    """Avisa al comprador; nunca lanza (el cobro ya está cumplido)."""
    from ..services.email import (
        EmailNotConfigured,
        EmailSendError,
        EmailValidationError,
        enviar_activacion_plan_por_email,
    )

    destinatario = str(getattr(compra, "creada_por_email", "") or "").strip()
    if not destinatario:
        return
    organizacion = db.get(Organizacion, compra.organizacion_id)
    recibo_pdf = b""
    recibo_nombre = "recibo.pdf"
    try:
        recibo_pdf = generar_recibo_licencia_pdf(licencia, organizacion).read()
        recibo_nombre = f"recibo-{numero_recibo(licencia)}.pdf"
    except Exception:
        log.warning(
            "Compra Stripe #%s activada sin recibo adjunto:\n%s",
            compra.id,
            traceback.format_exc(),
        )
    try:
        enviar_activacion_plan_por_email(
            email=destinatario,
            organizacion_nombre=organizacion.nombre if organizacion else "",
            plan_nombre=plan_info(compra.plan)["nombre"],
            importe_texto=fmt_monto(compra.importe, compra.moneda or "USD"),
            metodo_nombre=metodo_info(METODO_STRIPE)["nombre"],
            inicio=licencia.inicio,
            vence=licencia.vence,
            recibo_pdf=recibo_pdf,
            recibo_nombre=recibo_nombre,
        )
    except (EmailNotConfigured, EmailValidationError, EmailSendError) as exc:
        log.warning("Aviso Stripe no entregado a %s (%s).", destinatario, exc)
    except Exception:
        log.error(
            "Error avisando la activación Stripe de la compra #%s:\n%s",
            compra.id,
            traceback.format_exc(),
        )


@router.post("/pago/stripe/checkout", include_in_schema=False)
def stripe_checkout(
    request: Request,
    plan: str = Form(""),
    db: Session = Depends(get_db_renovacion),
):
    """Crea la Checkout Session y redirige a Stripe.

    La compra queda pendiente hasta que Stripe confirme el cobro por
    webhook. Sin STRIPE_SECRET_KEY se vuelve al checkout manual.
    """
    from ..services.compras import GestionCompraError, crear_compra
    from ..services.stripe import (
        StripeError,
        StripeNotConfigured,
        crear_sesion_checkout,
        stripe_configurado,
    )

    ficha = _plan_o_redirect(request, plan)
    if ficha is None:
        return RedirectResponse("/pago", status_code=303)
    if not stripe_configurado():
        return RedirectResponse(
            f"/pago/comprar?plan={quote(plan)}&error="
            "El pago con tarjeta no está disponible ahora. Usa un método manual.",
            status_code=303,
        )

    organizacion_id = int(db.info.get("organizacion_id") or 0)
    usuario = db.get(Usuario, int(db.info.get("usuario_id") or 0))
    try:
        # La sesión de Stripe se crea ANTES de insertar la compra: RLS no
        # deja al cliente hacer UPDATE de ``compras_plan``, así que el id
        # de Checkout tiene que nacer en el INSERT.
        origen = _origen_publico(request)
        sesion = crear_sesion_checkout(
            plan=plan,
            organizacion_id=organizacion_id,
            compra_id=0,
            email=usuario.email if usuario else "",
            success_url=(
                origen
                + "/pago/stripe/exito?session_id={CHECKOUT_SESSION_ID}"
            ),
            cancel_url=origen + f"/pago/comprar?plan={quote(plan)}",
        )
        compra = crear_compra(
            db,
            organizacion_id=organizacion_id,
            plan=plan,
            metodo_pago=METODO_STRIPE,
            datos_verificacion={},
            comprobante_reference="",
            comprobante_nombre="",
            comprobante_mime="",
            creada_por_usuario_id=usuario.id if usuario else None,
            creada_por_email=usuario.email if usuario else "",
            exigir_comprobante=False,
            stripe_checkout_session_id=str(sesion["id"]),
        )
        db.commit()
    except (GestionCompraError, StripeNotConfigured, StripeError) as exc:
        db.rollback()
        return RedirectResponse(
            f"/pago/comprar?plan={quote(plan)}&error={quote(str(exc))}",
            status_code=303,
        )
    except Exception:
        db.rollback()
        log.error("Error creando la sesión de Stripe:\n%s", traceback.format_exc())
        return RedirectResponse(
            f"/pago/comprar?plan={quote(plan)}&error="
            "No se pudo abrir el pago con tarjeta. Inténtalo de nuevo.",
            status_code=303,
        )
    auditoria.registrar_evento(
        db,
        "plan.compra_registrada",
        entidad="compra",
        entidad_id=compra.id,
        detalle={"plan": plan, "metodo": METODO_STRIPE},
    )
    respuesta = RedirectResponse(str(sesion["url"]), status_code=303)
    _clear_plan_pendiente_cookie(respuesta)
    return respuesta


@router.get("/pago/stripe/exito", response_class=HTMLResponse, include_in_schema=False)
def stripe_exito(
    request: Request,
    session_id: str = "",
    db: Session = Depends(get_db_renovacion),
):
    """Página de retorno de Stripe. Solo lee: el webhook es quien activa.

    RLS reserva UPDATE de compras_plan e INSERT de licencias al operador.
    La sesión del cliente no puede cumplir el cobro; si el webhook aún no
    llegó, se muestra «confirmando» y basta recargar.
    """
    organizacion_id = int(db.info.get("organizacion_id") or 0)
    compra = _compra_por_sesion_local(db, organizacion_id, session_id)
    if compra is None or compra.organizacion_id != organizacion_id:
        return RedirectResponse("/pago", status_code=303)

    try:
        plan_ficha = plan_info(compra.plan)
        metodo_ficha = metodo_info(compra.metodo_pago)
    except KeyError:
        return RedirectResponse("/pago", status_code=303)

    activada = compra.estado == "activa"
    response = TEMPLATES.TemplateResponse(
        request,
        "pago/exito_stripe.html",
        {
            "compra": compra,
            "plan_nombre": plan_ficha["nombre"],
            "metodo_nombre": metodo_ficha["nombre"],
            "importe_texto": fmt_monto(compra.importe),
            "activada": activada,
        },
    )
    if activada:
        # Conversión GA4: el evento purchase se emite una sola vez por
        # navegador aunque la página de éxito se recargue.
        encolar_purchase_unico(request, response)
    return response


@router.post("/pago/stripe/webhook", include_in_schema=False)
async def stripe_webhook(
    request: Request, db: Session = Depends(get_stripe_webhook_db)
):
    """Recibe eventos de Stripe. Autenticado por firma, no por sesión."""
    from ..services.stripe import (
        StripeNotConfigured,
        StripeWebhookError,
        procesar_evento_webhook,
        verificar_firma_webhook,
    )

    cuerpo = await request.body()
    firma = request.headers.get("stripe-signature", "")
    try:
        evento = verificar_firma_webhook(cuerpo, firma)
        compra = procesar_evento_webhook(db, evento)
        if compra is not None:
            db.commit()
            if (
                getattr(compra, "_stripe_recien_activada", False)
                and compra.licencia_id
            ):
                licencia = db.get(Licencia, compra.licencia_id)
                if licencia is not None:
                    _avisar_activacion_stripe(db, compra, licencia)
        else:
            db.rollback()
    except StripeNotConfigured as exc:
        db.rollback()
        return JSONResponse(
            {"ok": False, "error": str(exc)},
            status_code=503,
            headers={"Cache-Control": "no-store"},
        )
    except StripeWebhookError as exc:
        db.rollback()
        return JSONResponse(
            {"ok": False, "error": str(exc)},
            status_code=400,
            headers={"Cache-Control": "no-store"},
        )
    except Exception:
        db.rollback()
        log.error("Error en el webhook de Stripe:\n%s", traceback.format_exc())
        return JSONResponse(
            {"ok": False, "error": "Error interno."},
            status_code=500,
            headers={"Cache-Control": "no-store"},
        )
    return JSONResponse({"ok": True}, headers={"Cache-Control": "no-store"})
