"""Cobro con tarjeta vía Stripe Checkout: sesión, retorno y webhook.

Tres rutas completan el circuito del pago con tarjeta:

- ``POST /pago/stripe/crear-sesion``: el cliente (con sesión y organización)
  elige pagar con tarjeta; aquí se crea la sesión de Stripe, se registra la
  compra pendiente y se le redirige a la página de pago de Stripe.
- ``GET /pago/stripe/retorno``: página a la que Stripe devuelve al cliente.
  El webhook suele llegar antes, pero no se garantiza: por eso no afirma
  «activado» sin comprobarlo.
- ``POST /api/stripe/webhook``: Stripe avisa del resultado. La ruta es pública
  (sin sesión ni CSRF), pero **verifica la firma** con ``STRIPE_WEBHOOK_SECRET``
  antes de tocar nada; es la única barrera entre un POST cualquiera y la
  concesión de una licencia.
"""
from __future__ import annotations

import logging
from datetime import datetime
from urllib.parse import quote

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from . import common
from .common import *  # noqa: F401,F403  (re-exporta modelos, servicios y utilidades)
from .pagos import codigo_pais_compra
from ..database import get_stripe_webhook_db
from ..datos_pago import PLANES, plan_info
from ..services import auditoria
from ..services.stripe_pagos import (
    StripeFirmaInvalida,
    StripeNoConfigurado,
    crear_sesion_checkout,
    crear_sesion_portal,
    obtener_suscripcion,
    verificar_evento,
)

router = APIRouter()

log = logging.getLogger("cotizat.stripe")

#: Ruta pública del webhook. Exenta de CSRF a propósito (Stripe firma sus
#: propias peticiones); ver ``app/security.py``.
WEBHOOK_PATH = "/api/stripe/webhook"

#: Quién figura como revisor de una compra activada por webhook. No es un
#: usuario real: es la marca de que la activación fue automática por Stripe.
OPERADOR_STRIPE = "stripe@cotizat.local"


def _url_base(request: Request) -> str:
    return str(request.base_url).rstrip("/")


@router.post("/pago/stripe/crear-sesion", include_in_schema=False)
async def crear_sesion(request: Request, db: Session = Depends(get_db_renovacion)):
    """Crea la sesión de Stripe y registra la compra pendiente.

    Responde con un 303 a la URL de pago de Stripe. Si Stripe no está
    configurado o algo falla, vuelve al checkout con el error en la query.
    """
    from ..services.compras import GestionCompraError, crear_compra_stripe

    form = await request.form()
    plan = str(form.get("plan") or "").strip()
    metodo_pago = str(form.get("metodo_pago") or "").strip()
    if plan not in PLANES:
        return RedirectResponse("/pago", status_code=303)
    if metodo_pago != "stripe":
        return RedirectResponse(
            f"/pago/comprar?plan={quote(plan)}&error="
            + quote("Ese método no se paga con tarjeta."),
            status_code=303,
        )

    ficha = plan_info(plan)
    organizacion_id = int(db.info.get("organizacion_id") or 0)
    organizacion = db.get(Organizacion, organizacion_id)
    usuario = db.get(Usuario, int(db.info.get("usuario_id") or 0))
    codigo = codigo_pais_compra(db, request)
    base = _url_base(request)

    try:
        session_id, url = crear_sesion_checkout(
            plan=plan,
            ficha=ficha,
            organizacion_id=organizacion_id,
            codigo_pais=codigo,
            email=usuario.email if usuario else "",
            organizacion_nombre=organizacion.nombre if organizacion else "",
            success_url=f"{base}/pago/stripe/retorno?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base}/pago/comprar?plan={quote(plan)}&error="
            + quote("Pago con tarjeta cancelado."),
        )
    except StripeNoConfigurado as exc:
        return RedirectResponse(
            f"/pago/comprar?plan={quote(plan)}&error={quote(str(exc))}",
            status_code=303,
        )
    except Exception:
        log.error("Error creando la sesión de Stripe:\n%s", traceback.format_exc())
        return RedirectResponse(
            f"/pago/comprar?plan={quote(plan)}&error="
            + quote("No se pudo iniciar el pago con tarjeta. Inténtalo de nuevo."),
            status_code=303,
        )

    try:
        compra = crear_compra_stripe(
            db,
            organizacion_id=organizacion_id,
            plan=plan,
            stripe_session_id=session_id,
            pais_codigo=codigo,
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
        "plan.compra_stripe_iniciada",
        entidad="compra",
        entidad_id=compra.id,
        detalle={"plan": plan, "sesion": session_id},
    )
    return RedirectResponse(url, status_code=303)


@router.get("/pago/stripe/retorno", response_class=HTMLResponse, include_in_schema=False)
def retorno_stripe(
    request: Request, session_id: str = "", db: Session = Depends(get_db_renovacion)
):
    """Página a la que Stripe devuelve al cliente tras pagar (o abandonar).

    No se fía del ``session_id`` que trae la URL: consulta la compra de la
    organización para saber si el webhook ya la activó.
    """
    organizacion_id = int(db.info.get("organizacion_id") or 0)
    activada = False
    compra = None
    if session_id:
        compra = (
            db.query(CompraPlan)
            .filter(
                CompraPlan.organizacion_id == organizacion_id,
                CompraPlan.stripe_session_id == str(session_id).strip(),
            )
            .first()
        )
        activada = bool(compra is not None and compra.estado == "activa")

    return TEMPLATES.TemplateResponse(
        request,
        "pago/stripe_retorno.html",
        {"activada": activada, "session_id": session_id},
    )


@router.post("/pago/stripe/portal", include_in_schema=False)
async def portal_stripe(request: Request, db: Session = Depends(get_db_renovacion)):
    """Abre el Customer Portal de Stripe para gestionar la suscripción.

    Deja al cliente ver sus facturas, actualizar la tarjeta y cancelar o
    reactivar la suscripción sin que CotizaT implemente esa pantalla.
    """
    organizacion_id = int(db.info.get("organizacion_id") or 0)
    compra = (
        db.query(CompraPlan)
        .filter(
            CompraPlan.organizacion_id == organizacion_id,
            CompraPlan.metodo_pago == "stripe",
            CompraPlan.stripe_customer_id.isnot(None),
        )
        .order_by(CompraPlan.id.desc())
        .first()
    )
    if compra is None or not compra.stripe_customer_id:
        return _redirect(
            "/configuracion",
            error="No hay una suscripción con tarjeta que gestionar.",
        )

    try:
        url = crear_sesion_portal(
            compra.stripe_customer_id,
            return_url=f"{_url_base(request)}/configuracion",
        )
    except StripeNoConfigurado as exc:
        return _redirect("/configuracion", error=str(exc))
    except Exception:
        log.error("Error abriendo el portal de Stripe:\n%s", traceback.format_exc())
        return _redirect(
            "/configuracion",
            error="No se pudo abrir el portal de gestión. Escríbenos a soporte.",
        )
    return RedirectResponse(url, status_code=303)


@router.post(WEBHOOK_PATH, include_in_schema=False)
async def webhook_stripe(
    request: Request, db: Session = Depends(get_stripe_webhook_db)
):
    """Recibe los eventos de Stripe y mantiene compra y licencia al día.

    Público por diseño (Stripe no tiene sesión de la app), pero la firma se
    verifica siempre. La concesión/renovación es idempotente: un reintento de
    Stripe no duplica la licencia ni acorta el acceso.

    Eventos atendidos (los que hay que registrar en el Dashboard):

    - ``checkout.session.completed``: se conoce la suscripción y el cliente;
      si ya está pagada (status active/trialing) se concede el acceso.
    - ``invoice.paid``: el cobro de un período (primero o renovación) quedó
      confirmado; se extiende la licencia hasta ``current_period_end``.
    - ``invoice.payment_failed``: se registra; no se revoca (el acceso dura
      hasta el día pagado, igual que Stripe).
    - ``customer.subscription.deleted``: se marca la compra como cancelada.
    - ``checkout.session.expired``: el cliente abandonó el pago.
    """
    from ..services.compras import (
        GestionCompraError,
        activar_compra_stripe,
        cancelar_compra_stripe,
        registrar_sesion_stripe,
    )

    payload = await request.body()
    firma = str(request.headers.get("stripe-signature") or "")
    try:
        evento = verificar_evento(payload, firma)
    except StripeFirmaInvalida as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=400)

    tipo = str(evento.get("type") or "")
    datos = (evento.get("data") or {}).get("object") or {}

    if tipo == "checkout.session.completed":
        session_id = str(datos.get("id") or "")
        subscription_id = str(datos.get("subscription") or "")
        customer_id = str(datos.get("customer") or "")
        payment_intent = str(datos.get("payment_intent") or "")
        try:
            registrar_sesion_stripe(
                db,
                session_id=session_id,
                subscription_id=subscription_id,
                customer_id=customer_id,
                payment_intent=payment_intent,
            )
            db.commit()
        except GestionCompraError as exc:
            db.rollback()
            log.warning("Sesión de Stripe sin compra pendiente: %s", exc)
            return JSONResponse({"ok": False, "error": str(exc)}, status_code=200)

        if subscription_id:
            # Si el primer cobro ya está confirmado, se concede el acceso; si
            # no, lo hará `invoice.paid` en unos segundos.
            try:
                sub = obtener_suscripcion(subscription_id)
                if str(sub.get("status") or "") in {"active", "trialing"}:
                    compra, licencia = activar_compra_stripe(
                        db,
                        subscription_id=subscription_id,
                        vence=sub["current_period_end"],
                        operador_email=OPERADOR_STRIPE,
                    )
                    db.commit()
                    return JSONResponse(
                        {
                            "ok": True,
                            "compra": compra.id,
                            "licencia": licencia.id if licencia else None,
                        }
                    )
            except (StripeNoConfigurado, GestionCompraError) as exc:
                db.rollback()
                log.warning("Suscripción de Stripe no activada aún: %s", exc)
        return JSONResponse({"ok": True, "pendiente": True})

    if tipo == "invoice.paid":
        subscription_id = str(datos.get("subscription") or "")
        if subscription_id:
            try:
                sub = obtener_suscripcion(subscription_id)
                compra, licencia = activar_compra_stripe(
                    db,
                    subscription_id=subscription_id,
                    vence=sub["current_period_end"],
                    operador_email=OPERADOR_STRIPE,
                )
                db.commit()
                return JSONResponse(
                    {
                        "ok": True,
                        "compra": compra.id,
                        "licencia": licencia.id if licencia else None,
                    }
                )
            except (StripeNoConfigurado, GestionCompraError) as exc:
                db.rollback()
                log.warning("Factura de Stripe no aplicada: %s", exc)
                return JSONResponse({"ok": False, "error": str(exc)}, status_code=200)
            except Exception:
                db.rollback()
                log.error("Error procesando invoice.paid:\n%s", traceback.format_exc())
                return JSONResponse({"ok": False, "error": "Error interno."}, status_code=500)
        return JSONResponse({"ok": True, "ignorado": True})

    if tipo == "invoice.payment_failed":
        # No se revoca el acceso: dura hasta el día pagado. Solo queda trazado.
        log.warning(
            "Factura de Stripe impagada: subscription=%s invoice=%s",
            datos.get("subscription"),
            datos.get("id"),
        )
        return JSONResponse({"ok": True})

    if tipo == "customer.subscription.deleted":
        subscription_id = str(datos.get("id") or "")
        cancelar_compra_stripe(
            db, subscription_id=subscription_id, operador_email=OPERADOR_STRIPE
        )
        db.commit()
        return JSONResponse({"ok": True})

    if tipo == "checkout.session.expired":
        # El cliente abandonó el pago: la compra pendiente queda rechazada para
        # que el panel del operador no espere un cobro que no llegará.
        session_id = str(datos.get("id") or "")
        compra = (
            db.query(CompraPlan)
            .filter(
                CompraPlan.stripe_session_id == session_id,
                CompraPlan.estado == "pendiente",
            )
            .first()
        )
        if compra is not None:
            compra.estado = "rechazada"
            compra.revisado_por_email = OPERADOR_STRIPE
            compra.revisado_at = datetime.utcnow()
            db.commit()
        return JSONResponse({"ok": True})

    # Otros eventos (refunds, disputes…): acuse de recibo, no se toca nada.
    return JSONResponse({"ok": True, "ignorado": True})
