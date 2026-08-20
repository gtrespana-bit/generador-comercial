"""Registro de compras de plan y activación manual de licencias (E1-059).

Flujo del piloto con cobro manual:

    Cliente (sesión iniciada) → elige plan y método → declara datos de
    verificación → sube comprobante → queda ``pendiente`` y el titular recibe
    el email con todo (comprobante adjunto). El operador revisa en el panel
    ``/admin/compras`` y activa (crea/renueva la ``Licencia``) o rechaza.

La compra es una tabla tenant (pertenece a la organización compradora). El
operador la lee por la política RLS marcada con ``es_operador``; la sesión de
cliente solo ve las suyas.
"""
from __future__ import annotations

from datetime import datetime
import json
import logging

from sqlalchemy.orm import Session

from ..datos_pago import (
    ESTADOS_COMPRA,
    METODOS_PAGO,
    PLANES,
    metodo_info,
    plan_info,
)
from ..models import CompraPlan, Licencia, Organizacion
from .licencias import (
    GestionLicenciaError,
    crear_licencia,
    crear_licencia_hasta,
    extender_licencia_hasta,
)

log = logging.getLogger("cotizat.compras")


class GestionCompraError(RuntimeError):
    """La operación sobre una compra no respeta las reglas del registro."""


def _plan_valido(plan: str) -> bool:
    return plan in PLANES


def _metodo_valido(metodo: str) -> bool:
    return metodo in METODOS_PAGO


def crear_compra(
    db: Session,
    *,
    organizacion_id: int,
    plan: str,
    metodo_pago: str,
    datos_verificacion: dict,
    comprobante_reference: str,
    comprobante_nombre: str,
    comprobante_mime: str,
    creada_por_usuario_id: int | None,
    creada_por_email: str,
) -> CompraPlan:
    """Registra una compra pendiente con su comprobante.

    No valida el comprobante (eso lo hace la ruta antes de guardarlo en el
    almacenamiento); aquí solo se exige que la referencia exista y que los
    campos de plan/método sean válidos.
    """
    plan = str(plan or "").strip().lower()
    metodo_pago = str(metodo_pago or "").strip().lower()
    if not _plan_valido(plan):
        raise GestionCompraError("El plan indicado no existe.")
    if not _metodo_valido(metodo_pago):
        raise GestionCompraError("El método de pago indicado no existe.")
    if not comprobante_reference:
        raise GestionCompraError(
            "Adjunta el comprobante de pago para continuar."
        )
    if not isinstance(datos_verificacion, dict):
        raise GestionCompraError("Los datos de verificación no son válidos.")

    ficha = plan_info(plan)
    compra = CompraPlan(
        organizacion_id=int(organizacion_id),
        plan=plan,
        metodo_pago=metodo_pago,
        importe=float(ficha["importe"]),
        moneda="USD",
        datos_verificacion=json.dumps(
            datos_verificacion, ensure_ascii=False, separators=(",", ":")
        ),
        comprobante_reference=str(comprobante_reference),
        comprobante_nombre=str(comprobante_nombre or "comprobante"),
        comprobante_mime=str(comprobante_mime or "application/octet-stream"),
        estado="pendiente",
        creada_por_usuario_id=creada_por_usuario_id,
        creada_por_email=str(creada_por_email or ""),
    )
    db.add(compra)
    db.flush()
    return compra


def crear_compra_stripe(
    db: Session,
    *,
    organizacion_id: int,
    plan: str,
    stripe_session_id: str,
    pais_codigo: str = "",
    creada_por_usuario_id: int | None = None,
    creada_por_email: str = "",
) -> CompraPlan:
    """Registra una compra pendiente iniciada en Stripe Checkout.

    A diferencia de ``crear_compra``, no exige comprobante: el pago aún no ha
    ocurrido (se confirma por webhook). La compra nace ``pendiente`` y queda
    localizable por ``stripe_session_id`` para que el webhook la active.
    """
    plan = str(plan or "").strip().lower()
    if not _plan_valido(plan):
        raise GestionCompraError("El plan indicado no existe.")
    if not str(stripe_session_id or "").strip():
        raise GestionCompraError("Falta la sesión de pago de Stripe.")

    ficha = plan_info(plan)
    compra = CompraPlan(
        organizacion_id=int(organizacion_id),
        plan=plan,
        metodo_pago="stripe",
        importe=float(ficha["importe"]),
        moneda="USD",
        datos_verificacion="{}",
        comprobante_reference="",
        comprobante_nombre="",
        comprobante_mime="",
        estado="pendiente",
        creada_por_usuario_id=creada_por_usuario_id,
        creada_por_email=str(creada_por_email or ""),
        stripe_session_id=str(stripe_session_id).strip()[:200],
        pais_codigo=(str(pais_codigo or "").strip().upper()[:2] or None),
    )
    db.add(compra)
    db.flush()
    return compra


def compra_por_sesion_stripe(db: Session, session_id: str) -> CompraPlan | None:
    """Localiza la compra pendiente de una sesión de Stripe, o ``None``."""
    return (
        db.query(CompraPlan)
        .filter(CompraPlan.stripe_session_id == str(session_id or "").strip())
        .first()
    )


def compra_por_suscripcion_stripe(db: Session, subscription_id: str) -> CompraPlan | None:
    """Localiza la compra de una suscripción de Stripe, o ``None``."""
    return (
        db.query(CompraPlan)
        .filter(CompraPlan.stripe_subscription_id == str(subscription_id or "").strip())
        .first()
    )


def registrar_sesion_stripe(
    db: Session,
    *,
    session_id: str,
    subscription_id: str,
    customer_id: str = "",
    payment_intent: str = "",
) -> CompraPlan:
    """Completa los datos de Stripe de la compra pendiente tras el checkout.

    ``checkout.session.completed`` es el momento en que se conoce la
    suscripción y el cliente creados por Stripe; desde aquí en adelante las
    renovaciones se localizan por ``stripe_subscription_id``.
    """
    compra = compra_por_sesion_stripe(db, session_id)
    if compra is None:
        raise GestionCompraError("No hay compra pendiente para esa sesión de pago.")
    compra.stripe_subscription_id = str(subscription_id or "")[:200]
    compra.stripe_customer_id = str(customer_id or "")[:200]
    if payment_intent:
        compra.stripe_payment_intent = str(payment_intent)[:200]
    db.flush()
    return compra


def activar_compra_stripe(
    db: Session,
    *,
    subscription_id: str,
    vence,
    operador_email: str,
    hoy=None,
) -> tuple[CompraPlan, Licencia]:
    """Concede o extiende la licencia de una suscripción de Stripe.

    ``vence`` es el ``current_period_end`` de la suscripción en Stripe: la
    aplicación no calcula duraciones propias, solo refleja el período pagado.
    Es idempotente: si la licencia ya cubre ``vence`` (reintento del webhook,
    o ``checkout.session.completed`` seguido de ``invoice.paid``), no cambia
    nada. La primera vez crea la licencia; después extiende la misma.
    """
    from datetime import date as _date

    hoy = hoy or _date.today()
    compra = compra_por_suscripcion_stripe(db, subscription_id)
    if compra is None:
        raise GestionCompraError("No hay compra para esa suscripción de Stripe.")
    if compra.metodo_pago != "stripe":
        raise GestionCompraError("La compra no corresponde a un pago con Stripe.")
    if compra.estado == "cancelada":
        # Una suscripción cancelada no se reactiva por un invoice residual.
        return compra, compra.licencia

    # Se lee por id y no por la relación ``compra.licencia``: la relación puede
    # quedar en caché como ``None`` tras el primer flush, y en una renovación
    # (mismo compra, segunda llamada) eso llevaría a crear una segunda licencia.
    licencia = db.get(Licencia, compra.licencia_id) if compra.licencia_id else None
    if licencia is None:
        licencia = crear_licencia_hasta(
            db,
            organizacion_id=compra.organizacion_id,
            vence=vence,
            importe=compra.importe,
            moneda=compra.moneda or "USD",
            metodo_cobro=_etiqueta_metodo("stripe"),
            referencia=str(subscription_id)[:60],
            notas=f"Suscripción de Stripe ({subscription_id}).",
            operador_email=operador_email,
            hoy=hoy,
        )
        compra.licencia_id = licencia.id
        compra.licencia_inicio = licencia.inicio
        compra.licencia_vence = licencia.vence
    else:
        extender_licencia_hasta(licencia, vence, hoy=hoy)
        compra.licencia_vence = licencia.vence

    if compra.estado == "pendiente":
        compra.estado = "activa"
        compra.licencia_inicio = licencia.inicio
        compra.revisado_por_email = str(operador_email or "")
        compra.revisado_at = datetime.utcnow()
    db.flush()
    return compra, licencia


def cancelar_compra_stripe(
    db: Session,
    *,
    subscription_id: str,
    operador_email: str,
) -> CompraPlan | None:
    """Marca como cancelada la compra de una suscripción dada de baja.

    No toca la licencia: el acceso sigue hasta el día ya pagado (igual que
    Stripe deja el servicio activo hasta el final del período en curso).
    """
    compra = compra_por_suscripcion_stripe(db, subscription_id)
    if compra is None:
        return None
    if compra.estado == "cancelada":
        return compra
    compra.estado = "cancelada"
    compra.revisado_por_email = str(operador_email or "")
    compra.revisado_at = datetime.utcnow()
    db.flush()
    return compra


def _exigir_compra(db: Session, compra_id: int) -> CompraPlan:
    compra = db.get(CompraPlan, compra_id)
    if compra is None:
        raise GestionCompraError("La compra indicada no existe.")
    return compra


def activar_compra(
    db: Session,
    *,
    compra_id: int,
    operador_email: str,
    hoy=None,
) -> tuple[CompraPlan, Licencia]:
    """Verifica una compra pendiente y concede la licencia del plan.

    Valida que la compra esté pendiente (no se puede activar dos veces),
    llama a ``crear_licencia`` con el importe real del plan y enlaza la
    licencia resultante a la compra. Devuelve ``(compra, licencia)``.
    """
    from datetime import date

    hoy = hoy or date.today()
    compra = _exigir_compra(db, compra_id)
    if compra.estado != "pendiente":
        raise GestionCompraError(
            f"La compra ya está {compra.etiqueta_estado.lower()}."
        )
    if not compra.comprobante_reference:
        raise GestionCompraError(
            "La compra no tiene comprobante adjunto; no se puede activar."
        )

    ficha = plan_info(compra.plan)
    licencia = crear_licencia(
        db,
        organizacion_id=compra.organizacion_id,
        origen="pago",
        duracion=ficha["duracion_licencia"],
        importe=compra.importe,
        moneda=compra.moneda or "USD",
        metodo_cobro=_etiqueta_metodo(compra.metodo_pago),
        referencia=_referencia_compra(compra),
        notas=(
            f"Activación de compra #{compra.id} "
            f"({compra.plan}, {compra.etiqueta_estado})."
        ),
        operador_email=operador_email,
        hoy=hoy,
    )
    compra.estado = "activa"
    compra.licencia_id = licencia.id
    # El período se copia sobre la compra a propósito: `licencias` la reserva
    # el RLS al operador, así que sin esta copia el comprador no podría emitir
    # su propio recibo. Además congela lo cobrado aunque la licencia cambie.
    compra.licencia_inicio = licencia.inicio
    compra.licencia_vence = licencia.vence
    compra.revisado_por_email = str(operador_email or "")
    compra.revisado_at = datetime.utcnow()
    db.flush()
    return compra, licencia


def rechazar_compra(
    db: Session,
    *,
    compra_id: int,
    operador_email: str,
) -> CompraPlan:
    """Rechaza una compra pendiente (comprobante inválido, pago incompleto…)."""
    compra = _exigir_compra(db, compra_id)
    if compra.estado != "pendiente":
        raise GestionCompraError(
            f"La compra ya está {compra.etiqueta_estado.lower()}."
        )
    compra.estado = "rechazada"
    compra.revisado_por_email = str(operador_email or "")
    compra.revisado_at = datetime.utcnow()
    db.flush()
    return compra


def _etiqueta_metodo(metodo: str) -> str:
    return metodo_info(metodo)["nombre"]


def _referencia_compra(compra: CompraPlan) -> str:
    """Referencia corta para la licencia: plan + método + operación/ID."""
    datos = compra.datos_verificacion_dict()
    claves = (
        "numero_operacion",
        "hash_transaccion",
        "binance_id_origen",
        "wallet_origen",
    )
    for clave in claves:
        valor = str(datos.get(clave) or "").strip()
        if valor:
            return valor[:60]
    return f"compra-{compra.id}"


def resumen_compras(db: Session) -> list[dict]:
    """Compras para el panel del operador, de la más reciente a la más antigua.

    Incluye el nombre de la organización compradora (la compra guarda solo el
    id; el panel lo enriquece para que el operador sepa a quién activar).
    """
    compras = db.query(CompraPlan).order_by(CompraPlan.created_at.desc()).all()
    organizaciones = {
        org.id: org for org in db.query(Organizacion).all()
    }
    filas = []
    for compra in compras:
        org = organizaciones.get(compra.organizacion_id)
        filas.append(
            {
                "compra": compra,
                "organizacion_nombre": org.nombre if org else "—",
                "plan_nombre": plan_info(compra.plan)["nombre"],
                "metodo_nombre": _etiqueta_metodo(compra.metodo_pago),
                "verificacion": compra.datos_verificacion_dict(),
            }
        )
    return filas


def ultima_compra_con_recibo(db: Session, organizacion_id: int) -> CompraPlan | None:
    """Última compra activada de una organización, o ``None`` si no hay.

    La usa la tarjeta «Tu plan» para ofrecer el recibo al cliente. Solo se
    consulta ``compras_plan`` (tabla tenant): la sesión del comprador no puede
    leer ``licencias``, y este es justo el motivo por el que la compra guarda
    su propio período.
    """
    return (
        db.query(CompraPlan)
        .filter(
            CompraPlan.organizacion_id == int(organizacion_id),
            CompraPlan.estado == "activa",
            CompraPlan.licencia_id.isnot(None),
            CompraPlan.licencia_vence.isnot(None),
        )
        .order_by(CompraPlan.created_at.desc(), CompraPlan.id.desc())
        .first()
    )


def comprobante_bytes(compra: CompraPlan) -> bytes:
    """Lee los bytes del comprobante desde el almacenamiento privado."""
    from ..storage import read_reference, StorageError

    if not compra.comprobante_reference:
        raise StorageError("La compra no tiene comprobante adjunto.")
    return read_reference(compra.comprobante_reference)


def estados_validos() -> tuple[str, ...]:
    return ESTADOS_COMPRA
