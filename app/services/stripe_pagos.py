"""Cobro con tarjeta vía Stripe Checkout, en suscripción recurrente.

Diseño (E1-059 → Stripe, 20/08/2026)
------------------------------------
Stripe Checkout (``mode="subscription"``) aloja la página de pago: CotizaT
solo crea una *sesión* desde el backend (con ``STRIPE_SECRET_KEY``), redirige
al cliente y espera las confirmaciones por webhook. Nunca se tocan datos de
tarjeta, así que la carga PCI es mínima (SAQ-A).

Los **precios recurrentes** viven en Stripe (Producto + Prices), referenciados
por su ``price_...`` en las variables ``STRIPE_PRICE_ANUAL`` y
``STRIPE_PRICE_MENSUAL``. Stripe Billing se encarga de cobrar cada período; la
aplicación solo refleja el ``current_period_end`` de la suscripción sobre la
licencia (concesión inicial y renovaciones por ``invoice.paid``).

Flujo:

    checkout  →  POST /pago/stripe/crear-sesion  →  Stripe Checkout (suscripción)
    Stripe cobra → ``checkout.session.completed``  (registra sub_id / customer)
                   ``invoice.paid``                (activa o extiende la licencia)
    Cliente gestiona → POST /pago/stripe/portal    (Customer Portal de Stripe)

El webhook se verifica SIEMPRE con ``STRIPE_WEBHOOK_SECRET``; sin clave no se
firma ningún evento. La activación es idempotente: un reintento de Stripe no
concede una segunda licencia ni acorta el acceso.
"""
from __future__ import annotations

import os
from datetime import date, datetime

#: Moneda de cobro de los planes con tarjeta. Decisión 20/08/2026: todo en
#: USD. Los métodos locales de Stripe (OXXO, PSE, Yape…) exigen moneda local,
#: así que quedan para una fase 2; con USD funciona la tarjeta en todo el mundo.
MONEDA_STRIPE = "usd"


class StripeNoConfigurado(RuntimeError):
    """Stripe no está configurado (falta la clave o un precio) o la librería no está."""


class StripeFirmaInvalida(RuntimeError):
    """La firma del webhook no es válida: no es Stripe quien llama."""


def _clave_secreta() -> str:
    return str(os.environ.get("STRIPE_SECRET_KEY", "") or "").strip()


def _secreto_webhook() -> str:
    return str(os.environ.get("STRIPE_WEBHOOK_SECRET", "") or "").strip()


def _precio_id(plan: str) -> str:
    variable = {"anual": "STRIPE_PRICE_ANUAL", "mensual": "STRIPE_PRICE_MENSUAL"}.get(
        str(plan or "").strip().lower(), ""
    )
    if not variable:
        return ""
    return str(os.environ.get(variable, "") or "").strip()


def stripe_configurado() -> bool:
    """True si hay clave de Stripe y los dos precios recurrentes definidos."""
    return bool(
        _clave_secreta()
        and _precio_id("anual")
        and _precio_id("mensual")
    )


def _importar_stripe():
    try:
        import stripe
    except ImportError as exc:  # pragma: no cover - depende del entorno
        raise StripeNoConfigurado(
            "La biblioteca de Stripe no está instalada en el servidor."
        ) from exc
    return stripe


def crear_sesion_checkout(
    *,
    plan: str,
    ficha: dict,
    organizacion_id: int,
    codigo_pais: str,
    email: str,
    organizacion_nombre: str,
    success_url: str,
    cancel_url: str,
) -> tuple[str, str]:
    """Crea una sesión de Stripe Checkout en modo suscripción.

    Devuelve ``(session_id, url)``. La compra se identifica después por
    ``client_reference_id`` (organización) y por el ``metadata``; el webhook
    localiza la fila pendiente por ``stripe_session_id`` y, una vez creada la
    suscripción, por ``stripe_subscription_id``.
    """
    stripe = _importar_stripe()
    if not stripe_configurado():
        raise StripeNoConfigurado(
            "El pago con tarjeta aún no está configurado. Escríbenos a soporte."
        )

    precio = _precio_id(plan)
    if not precio:
        raise StripeNoConfigurado("El plan indicado no tiene precio en Stripe.")

    producto = f"CotizaT – {ficha.get('nombre') or plan.title()}"
    if organizacion_nombre:
        producto += f" ({organizacion_nombre[:80]})"

    sesion = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": precio, "quantity": 1}],
        customer_email=email or None,
        client_reference_id=str(organizacion_id),
        metadata={
            "organizacion_id": str(organizacion_id),
            "plan": plan,
            "pais": codigo_pais or "",
        },
        subscription_data={"metadata": {"plan": plan}},
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return str(sesion.id), str(sesion.url)


def obtener_suscripcion(subscription_id: str) -> dict:
    """Recupera una suscripción de Stripe y devuelve lo que la app necesita.

    Devuelve ``{"status": str, "current_period_end": date, "customer": str}``.
    Lanza ``StripeNoConfigurado`` si falta la clave; la ruta decide cómo
    degradar.
    """
    stripe = _importar_stripe()
    if not _clave_secreta():
        raise StripeNoConfigurado("Stripe no está configurado en el servidor.")
    stripe.api_key = _clave_secreta()
    sub = stripe.Subscription.retrieve(str(subscription_id))
    fin = int(sub.get("current_period_end") or 0)
    return {
        "id": str(sub.get("id") or ""),
        "status": str(sub.get("status") or ""),
        "current_period_end": (
            datetime.utcfromtimestamp(fin).date() if fin else date.today()
        ),
        "customer": str(sub.get("customer") or ""),
    }


def crear_sesion_portal(customer_id: str, return_url: str) -> str:
    """Crea una sesión del Customer Portal de Stripe y devuelve su URL.

    El portal deja al cliente ver sus facturas y cancelar/reactivar la
    suscripción sin que CotizaT tenga que implementar esa pantalla.
    """
    stripe = _importar_stripe()
    if not _clave_secreta():
        raise StripeNoConfigurado("Stripe no está configurado en el servidor.")
    stripe.api_key = _clave_secreta()
    sesion = stripe.billing_portal.Session.create(
        customer=str(customer_id),
        return_url=return_url,
    )
    return str(sesion.url)


def verificar_evento(payload: bytes, signature_header: str) -> dict:
    """Verifica la firma del webhook y devuelve el evento como dict.

    Lanza ``StripeFirmaInvalida`` si la firma no es válida o si no hay secreto
    configurado. Nunca se procesa un evento sin esta comprobación: es la única
    barrera entre un POST público y la concesión de una licencia.
    """
    stripe = _importar_stripe()
    secreto = _secreto_webhook()
    if not secreto:
        raise StripeFirmaInvalida("El webhook de Stripe no está configurado.")
    try:
        evento = stripe.Webhook.construct_event(
            payload, signature_header, secreto
        )
    except Exception as exc:
        raise StripeFirmaInvalida("Firma del webhook no válida.") from exc
    return dict(evento or {})
