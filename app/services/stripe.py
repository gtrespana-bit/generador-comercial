"""Cobro con Stripe Checkout (tarjeta, Apple Pay y Google Pay).

Stripe no opera como pasarela local en todos los países de LatAm: la cuenta
del titular es española y cobra en USD. El cliente de cualquier país paga
con tarjeta internacional o billetera (Apple Pay / Google Pay). Los métodos
manuales (Pago móvil, Binance, Kontigo, USDT) se conservan para quien no
pueda usar tarjeta.

Se habla con la API REST de Stripe con ``urllib``, el mismo patrón que
Resend, Auth y Storage: sin SDK y sin regenerar el lock.

Configuración: ``STRIPE_SECRET_KEY`` (sk_test_… / sk_live_…) y
``STRIPE_WEBHOOK_SECRET`` (whsec_…). Sin la primera, el botón de tarjeta
no aparece y el cobro manual sigue siendo el único camino.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import hmac
import json
import logging
import os
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request as UrlRequest, urlopen

from sqlalchemy.orm import Session

from ..branding import PRODUCT_NAME
from ..datos_pago import METODO_STRIPE, plan_info
from ..models import CompraPlan

log = logging.getLogger("cotizat.stripe")

STRIPE_API_URL = "https://api.stripe.com/v1"
STRIPE_API_VERSION = "2024-06-20"
OPERADOR_STRIPE = "stripe@cotizat.local"

#: Intervalo de la suscripción Stripe según el plan publicado.
INTERVALOS_PLAN = {
    "anual": "year",
    "mensual": "month",
}


class StripeNotConfigured(RuntimeError):
    """Faltan las claves de Stripe o no son válidas."""


class StripeError(RuntimeError):
    """La API de Stripe rechazó la petición o no respondió."""


class StripeWebhookError(RuntimeError):
    """La firma del webhook no es válida o el evento no se puede cumplir."""


def _env(nombre: str) -> str:
    return str(os.environ.get(nombre, "")).strip()


@dataclass(frozen=True)
class StripeSettings:
    secret_key: str
    webhook_secret: str = ""

    @classmethod
    def from_environment(cls) -> "StripeSettings":
        secret = _env("STRIPE_SECRET_KEY")
        webhook = _env("STRIPE_WEBHOOK_SECRET")
        if not secret:
            raise StripeNotConfigured(
                "El cobro con tarjeta no está configurado (falta STRIPE_SECRET_KEY)."
            )
        if not secret.startswith(("sk_test_", "sk_live_")):
            raise StripeNotConfigured(
                "STRIPE_SECRET_KEY debe ser una clave de Stripe (sk_test_ o sk_live_)."
            )
        if webhook and not webhook.startswith("whsec_"):
            raise StripeNotConfigured(
                "STRIPE_WEBHOOK_SECRET debe ser un secreto de webhook (whsec_)."
            )
        return cls(secret_key=secret, webhook_secret=webhook)


def stripe_configurado() -> bool:
    """¿Hay clave secreta válida? El botón de tarjeta cuelga de esto."""
    try:
        StripeSettings.from_environment()
        return True
    except StripeNotConfigured:
        return False


def estado_configuracion_stripe() -> tuple[str, str | None]:
    """Describe Stripe para `/readyz`. Nunca hace fallar el readiness."""
    secret = _env("STRIPE_SECRET_KEY")
    webhook = _env("STRIPE_WEBHOOK_SECRET")
    if not secret and not webhook:
        return "no-configurado", None
    try:
        settings = StripeSettings.from_environment()
    except StripeNotConfigured as exc:
        return "mal-configurado", str(exc)
    if not settings.webhook_secret:
        return "sin-webhook", None
    return "configurado", None


def importe_a_centavos(importe: float) -> int:
    """Convierte el importe publicado (USD) a centavos enteros de Stripe."""
    return int(
        (Decimal(str(importe)) * Decimal("100")).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
    )


def _aplanar(valor, prefijo: str = "") -> list[tuple[str, str]]:
    """Form-encoding anidado que espera la API de Stripe."""
    items: list[tuple[str, str]] = []
    if isinstance(valor, dict):
        for clave, hijo in valor.items():
            clave_str = f"{prefijo}[{clave}]" if prefijo else str(clave)
            items.extend(_aplanar(hijo, clave_str))
    elif isinstance(valor, (list, tuple)):
        for indice, hijo in enumerate(valor):
            items.extend(_aplanar(hijo, f"{prefijo}[{indice}]"))
    elif isinstance(valor, bool):
        items.append((prefijo, "true" if valor else "false"))
    elif valor is None:
        return items
    else:
        items.append((prefijo, str(valor)))
    return items


def _llamar_stripe(metodo: str, ruta: str, datos: dict | None = None) -> dict:
    settings = StripeSettings.from_environment()
    cuerpo = urlencode(_aplanar(datos or {})).encode("utf-8") if datos else None
    url = f"{STRIPE_API_URL}/{ruta.lstrip('/')}"
    if metodo == "GET" and datos:
        url = f"{url}?{cuerpo.decode('ascii')}"
        cuerpo = None
    peticion = UrlRequest(
        url,
        data=cuerpo,
        headers={
            "Authorization": f"Bearer {settings.secret_key}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "Stripe-Version": STRIPE_API_VERSION,
            "User-Agent": "CotizaT/1.0",
        },
        method=metodo,
    )
    try:
        with urlopen(peticion, timeout=15) as respuesta:  # noqa: S310 (URL fija)
            crudo = respuesta.read(512 * 1024)
    except HTTPError as exc:
        detalle = ""
        try:
            cuerpo_error = json.loads(exc.read().decode("utf-8"))
            detalle = str((cuerpo_error.get("error") or {}).get("message") or "")
        except Exception:
            detalle = ""
        raise StripeError(detalle or f"Stripe rechazó la petición ({exc.code}).") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise StripeError(
            f"Stripe no respondió ({type(exc).__name__})."
        ) from exc
    try:
        payload = json.loads(crudo.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise StripeError("Stripe devolvió una respuesta inesperada.") from exc
    if not isinstance(payload, dict):
        raise StripeError("Stripe devolvió una respuesta inesperada.")
    return payload


def crear_sesion_checkout(
    *,
    plan: str,
    organizacion_id: int,
    compra_id: int,
    email: str,
    success_url: str,
    cancel_url: str,
) -> dict:
    """Crea una Checkout Session en modo suscripción y devuelve el objeto."""
    ficha = plan_info(plan)
    intervalo = INTERVALOS_PLAN.get(plan)
    if intervalo is None:
        raise StripeError("El plan indicado no admite cobro con tarjeta.")
    centavos = importe_a_centavos(ficha["importe"])
    if centavos < 50:
        raise StripeError("El importe del plan no alcanza el mínimo de Stripe.")
    datos = {
        "mode": "subscription",
        "success_url": success_url,
        "cancel_url": cancel_url,
        "locale": "es",
        "client_reference_id": str(int(organizacion_id)),
        "payment_method_types": ["card"],
        "line_items": [
            {
                "quantity": 1,
                "price_data": {
                    "currency": "usd",
                    "unit_amount": centavos,
                    "recurring": {"interval": intervalo},
                    "product_data": {
                        "name": f"{PRODUCT_NAME} · {ficha['nombre']}",
                    },
                },
            }
        ],
        "metadata": {
            "organizacion_id": str(int(organizacion_id)),
            "plan": plan,
        },
        "subscription_data": {
            "metadata": {
                "organizacion_id": str(int(organizacion_id)),
                "plan": plan,
            }
        },
    }
    if int(compra_id or 0) > 0:
        datos["metadata"]["compra_id"] = str(int(compra_id))
        datos["subscription_data"]["metadata"]["compra_id"] = str(int(compra_id))
    email = str(email or "").strip()
    if email and "@" in email:
        datos["customer_email"] = email[:254]
    sesion = _llamar_stripe("POST", "checkout/sessions", datos)
    if not sesion.get("id") or not sesion.get("url"):
        raise StripeError("Stripe no devolvió la URL de pago.")
    return sesion


def obtener_sesion(session_id: str) -> dict:
    """Lee una Checkout Session por su id."""
    session_id = str(session_id or "").strip()
    if not session_id.startswith("cs_"):
        raise StripeError("La sesión de Stripe no es válida.")
    return _llamar_stripe("GET", f"checkout/sessions/{session_id}")


def verificar_firma_webhook(payload: bytes, firma_header: str) -> dict:
    """Valida Stripe-Signature y devuelve el evento.

    La comparación es en tiempo constante. Un desfase de más de 5 minutos
    se rechaza para no reutilizar un payload interceptado.
    """
    settings = StripeSettings.from_environment()
    if not settings.webhook_secret:
        raise StripeNotConfigured("Falta STRIPE_WEBHOOK_SECRET.")
    if not payload:
        raise StripeWebhookError("El webhook llegó vacío.")
    partes: dict[str, list[str]] = {}
    for trozo in str(firma_header or "").split(","):
        if "=" not in trozo:
            continue
        clave, valor = trozo.split("=", 1)
        partes.setdefault(clave.strip(), []).append(valor.strip())
    try:
        timestamp = int((partes.get("t") or [""])[0])
    except (TypeError, ValueError) as exc:
        raise StripeWebhookError("La firma del webhook no trae marca de tiempo.") from exc
    if abs(int(time.time()) - timestamp) > 300:
        raise StripeWebhookError("La firma del webhook está caducada.")
    firmado = f"{timestamp}.".encode("ascii") + payload
    esperado = hmac.new(
        settings.webhook_secret.encode("utf-8"),
        firmado,
        hashlib.sha256,
    ).hexdigest()
    validas = partes.get("v1") or []
    if not any(hmac.compare_digest(esperado, firma) for firma in validas):
        raise StripeWebhookError("La firma del webhook no coincide.")
    try:
        evento = json.loads(payload.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise StripeWebhookError("El evento de Stripe no es JSON válido.") from exc
    if not isinstance(evento, dict) or not evento.get("type"):
        raise StripeWebhookError("El evento de Stripe no tiene tipo.")
    return evento


def _ids_stripe(objeto: dict) -> dict[str, str]:
    """Extrae ids de sesión, suscripción, cliente, pago y factura."""
    def _id(valor) -> str:
        if isinstance(valor, dict):
            return str(valor.get("id") or "")
        return str(valor or "")

    invoice = objeto.get("invoice")
    payment_intent = objeto.get("payment_intent")
    if isinstance(invoice, dict):
        payment_intent = payment_intent or invoice.get("payment_intent")
    return {
        "session": _id(objeto.get("id") if str(objeto.get("id") or "").startswith("cs_") else ""),
        "subscription": _id(objeto.get("subscription")),
        "customer": _id(objeto.get("customer")),
        "payment_intent": _id(payment_intent),
        "invoice": _id(invoice) if not str(objeto.get("id") or "").startswith("cs_") else _id(invoice),
    }


def _anotar_ids(compra: CompraPlan, objeto: dict) -> None:
    ids = _ids_stripe(objeto)
    if ids["session"] and not compra.stripe_checkout_session_id:
        compra.stripe_checkout_session_id = ids["session"][:255]
    if ids["subscription"]:
        compra.stripe_subscription_id = ids["subscription"][:255]
    if ids["customer"]:
        compra.stripe_customer_id = ids["customer"][:255]
    if ids["payment_intent"]:
        compra.stripe_payment_intent_id = ids["payment_intent"][:255]
    if ids["invoice"]:
        compra.stripe_invoice_id = ids["invoice"][:255]


def _activar_compra_stripe(db: Session, compra: CompraPlan, objeto: dict) -> CompraPlan:
    from .compras import activar_compra

    _anotar_ids(compra, objeto)
    if compra.estado == "activa":
        db.flush()
        return compra
    compra, _licencia = activar_compra(
        db,
        compra_id=compra.id,
        operador_email=OPERADOR_STRIPE,
        exigir_comprobante=False,
    )
    compra._stripe_recien_activada = True  # type: ignore[attr-defined]
    return compra


def _compra_por_sesion(db: Session, session_id: str) -> CompraPlan | None:
    session_id = str(session_id or "").strip()
    if not session_id:
        return None
    return (
        db.query(CompraPlan)
        .filter(CompraPlan.stripe_checkout_session_id == session_id)
        .first()
    )


def _compra_por_factura(db: Session, invoice_id: str) -> CompraPlan | None:
    invoice_id = str(invoice_id or "").strip()
    if not invoice_id:
        return None
    return (
        db.query(CompraPlan)
        .filter(CompraPlan.stripe_invoice_id == invoice_id)
        .first()
    )


def _compra_por_suscripcion(db: Session, subscription_id: str) -> CompraPlan | None:
    subscription_id = str(subscription_id or "").strip()
    if not subscription_id:
        return None
    return (
        db.query(CompraPlan)
        .filter(CompraPlan.stripe_subscription_id == subscription_id)
        .order_by(CompraPlan.id.desc())
        .first()
    )


def cumplir_sesion_checkout(db: Session, sesion: dict) -> CompraPlan | None:
    """Activa la compra asociada a una Checkout Session pagada.

    Idempotente: si la compra ya está activa, solo anota los ids de Stripe.
    """
    if not isinstance(sesion, dict):
        return None
    if str(sesion.get("payment_status") or "") not in {"paid", "no_payment_required"}:
        if str(sesion.get("status") or "") != "complete":
            return None
    session_id = str(sesion.get("id") or "")
    compra = _compra_por_sesion(db, session_id)
    if compra is None:
        metadata = sesion.get("metadata") or {}
        try:
            compra_id = int(metadata.get("compra_id") or 0)
        except (TypeError, ValueError):
            compra_id = 0
        if compra_id:
            compra = db.get(CompraPlan, compra_id)
    if compra is None or compra.metodo_pago != METODO_STRIPE:
        return None
    return _activar_compra_stripe(db, compra, sesion)


def cumplir_factura(db: Session, factura: dict) -> CompraPlan | None:
    """Activa o renueva la licencia correspondiente a una factura pagada.

    La primera factura de la suscripción activa la compra pendiente. Las
    siguientes encadenan una licencia nueva (renovación automática).
    """
    from .compras import crear_compra

    if not isinstance(factura, dict):
        return None
    if not factura.get("paid") and str(factura.get("status") or "") != "paid":
        return None
    invoice_id = str(factura.get("id") or "")
    existente = _compra_por_factura(db, invoice_id)
    if existente is not None:
        return _activar_compra_stripe(db, existente, factura)

    subscription_id = str(factura.get("subscription") or "")
    origen = _compra_por_suscripcion(db, subscription_id)
    if origen is None:
        metadata = factura.get("metadata") or {}
        try:
            compra_id = int(metadata.get("compra_id") or 0)
        except (TypeError, ValueError):
            compra_id = 0
        if compra_id:
            origen = db.get(CompraPlan, compra_id)
    if origen is None or origen.metodo_pago != METODO_STRIPE:
        return None

    if origen.estado == "pendiente":
        return _activar_compra_stripe(db, origen, factura)

    # La primera factura de la suscripción (`subscription_create`) es el
    # mismo cobro que `checkout.session.completed`. Si ya está activa, solo
    # anotamos ids: crear otra compra duplicaría el período pagado.
    motivo = str(factura.get("billing_reason") or "")
    if motivo in {"subscription_create", "subscription_update"}:
        return _activar_compra_stripe(db, origen, factura)

    # Renovación: una compra nueva por cada factura, para que el cliente
    # tenga recibo de cada período. crear_licencia encadena el acceso.
    renovacion = crear_compra(
        db,
        organizacion_id=origen.organizacion_id,
        plan=origen.plan,
        metodo_pago=METODO_STRIPE,
        datos_verificacion={"stripe_invoice": invoice_id},
        comprobante_reference="",
        comprobante_nombre="",
        comprobante_mime="",
        creada_por_usuario_id=origen.creada_por_usuario_id,
        creada_por_email=origen.creada_por_email,
        exigir_comprobante=False,
    )
    renovacion.stripe_subscription_id = origen.stripe_subscription_id
    renovacion.stripe_customer_id = origen.stripe_customer_id
    return _activar_compra_stripe(db, renovacion, factura)


def procesar_evento_webhook(db: Session, evento: dict) -> CompraPlan | None:
    """Cumple el evento de Stripe. Devuelve la compra afectada, o None."""
    tipo = str(evento.get("type") or "")
    objeto = (evento.get("data") or {}).get("object") or {}
    if tipo == "checkout.session.completed":
        return cumplir_sesion_checkout(db, objeto)
    if tipo == "invoice.paid":
        return cumplir_factura(db, objeto)
    if tipo in {"invoice.payment_failed", "customer.subscription.deleted"}:
        # El acceso sigue hasta el vencimiento de la licencia ya concedida.
        # No se borran datos ni se corta el período pagado.
        log.info("Evento Stripe %s ignorado a propósito (no corta el acceso).", tipo)
        return None
    return None
