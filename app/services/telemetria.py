"""Telemetría interna de producto: embudo, activación y retención (E5-012).

Complementa Google Analytics 4 con un dato **propio y del servidor**. GA4
mide la capa pública (tráfico, fuentes, tiempo en página) pero se pierde
todo lo que ocurre tras el login: bloqueadores y consentimiento recortan
las conversiones, la retención máxima es de 14 meses y sus datos no deben
ligarse a cuentas. Aquí lo que se guarda es el mínimo agregado que permite
responder las preguntas del plan comercial (E5: «retención a 3, 6 y 12
meses», «uso recurrente y reducción de abandono»):

- ``cuenta.registrada`` — embudo, paso 1 (evento global, sin organización).
- ``organizacion.creada`` — embudo, paso 2.
- ``actividad.diaria`` — **latido**: una fila por organización y día con
  uso. Es la base de activos por día (DAU por empresa), cohortes de
  retención y riesgo de churn.
- ``presupuesto.creado`` / ``aprobado`` / ``enviado_email`` /
  ``pdf_descargado`` — el ciclo de valor del producto.
- ``importacion.confirmada`` — adopción del importador CYPE/BC3.
- ``pago.compra_registrada`` / ``pago.checkout_iniciado`` /
  ``licencia.activada`` — el embudo de cobro.
- ``equipo.invitacion_enviada`` — señal de crecimiento intra-empresa.

Reglas heredadas de la auditoría (no negociables):

1. **La telemetría jamás rompe el flujo principal**: todas las funciones son
   best-effort, capturan cualquier excepción, hacen ``rollback`` de su
   propio intento y devuelven ``False``/``None``.
2. **Se anota después del commit del cambio principal.**
3. **El detalle nunca lleva datos sensibles** ni de clientes de la
   organización: solo métricas de negocio (plan, país, nº de partidas).
4. **Sin PII innecesaria**: no se guarda IP (ni hash). El ``actor_email``
   es el de la sesión autenticada, dato que el operador ya ve en el panel.
5. **Catálogo cerrado**: la base (PostgreSQL) valida las acciones globales
   contra una lista fija; el servicio valida todo el resto.
"""
from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta

from sqlalchemy import text

from ..models import EventoProducto

log = logging.getLogger("cotizat.telemetria")

#: Catálogo cerrado de acciones (fuente única de verdad). El panel de
#: analítica usa estas etiquetas para pintar nombre legibles.
ACCIONES: dict[str, str] = {
    "cuenta.registrada": "Cuenta registrada",
    "organizacion.creada": "Empresa creada",
    "actividad.diaria": "Uso diario",
    "presupuesto.creado": "Presupuesto creado",
    "presupuesto.aprobado": "Presupuesto aprobado",
    "presupuesto.enviado_email": "Presupuesto enviado por email",
    "presupuesto.pdf_descargado": "PDF de presupuesto descargado",
    "importacion.confirmada": "Importación CYPE/BC3",
    "pago.checkout_iniciado": "Checkout Stripe iniciado",
    "pago.compra_registrada": "Compra registrada",
    "licencia.activada": "Licencia activada",
    "equipo.invitacion_enviada": "Invitación de equipo enviada",
}

#: Acciones que ocurren **sin organización** (antes de existir empresa).
#: Debe coincidir con la lista de la función PostgreSQL
#: ``cotizat_security.registrar_evento_producto_global``.
ACCIONES_GLOBALES = frozenset({"cuenta.registrada"})


def etiqueta(accion: str) -> str:
    """Nombre legible de una acción (la propia si es desconocida)."""
    return ACCIONES.get(accion, accion)


def _serializar_detalle(detalle) -> str:
    if not detalle:
        return "{}"
    try:
        texto = json.dumps(detalle, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return "{}"
    return texto if len(texto) <= 2000 else "{}"


def registrar(
    db,
    accion: str,
    *,
    organizacion_id: int | None = None,
    email: str = "",
    detalle: dict | None = None,
) -> bool:
    """Anota un evento de producto de una organización. Best-effort, nunca lanza.

    La organización se toma del contexto de la sesión (``db.info``) salvo
    que se pase ``organizacion_id`` explícito — necesario en las sesiones de
    operador (activación manual) y en el alta de empresa, donde el contexto
    de tenant acaba de nacer. Llamar **después** del commit principal.
    """
    try:
        accion = str(accion or "").strip()
        if accion not in ACCIONES or accion in ACCIONES_GLOBALES:
            return False
        org_id = int(organizacion_id or db.info.get("organizacion_id") or 0)
        if org_id <= 0:
            return False
        db.add(
            EventoProducto(
                organizacion_id=org_id,
                actor_email=str(
                    email or db.info.get("auth_email") or ""
                )[:254],
                accion=accion,
                detalle=_serializar_detalle(detalle),
            )
        )
        db.commit()
        return True
    except Exception:
        log.warning("No se pudo registrar el evento de producto %r.", accion)
        try:
            db.rollback()
        except Exception:
            pass
        return False


def registrar_global(
    db,
    accion: str,
    *,
    email: str = "",
    detalle: dict | None = None,
) -> bool:
    """Anota un evento sin organización (alta de cuenta). Best-effort.

    En PostgreSQL entra por la función SECURITY DEFINER con lista cerrada
    (defensa en profundidad); en SQLite se inserta directo.
    """
    try:
        accion = str(accion or "").strip()
        if accion not in ACCIONES_GLOBALES:
            return False
        email = str(email or "").strip().lower()[:254]
        cuerpo = _serializar_detalle(detalle)
        if db.bind is not None and db.bind.dialect.name == "postgresql":
            db.execute(
                text(
                    "SELECT cotizat_security."
                    "registrar_evento_producto_global("
                    " :email, :accion, :detalle)"
                ),
                {"email": email, "accion": accion, "detalle": cuerpo},
            )
            db.commit()
            return True
        db.add(
            EventoProducto(
                organizacion_id=None,
                actor_email=email,
                accion=accion,
                detalle=cuerpo,
            )
        )
        db.commit()
        return True
    except Exception:
        log.warning("No se pudo registrar el evento global %r.", accion)
        try:
            db.rollback()
        except Exception:
            pass
        return False


def anotar_registro(*, email: str, pais: str = "") -> bool:
    """``cuenta.registrada`` con sesión propia y efímera.

    La ruta de registro no depende de ``get_db`` (todavía no hay
    organización); el mismo patrón que el consentimiento y las sesiones de
    auditoría. El país llega del selector del formulario y solo se usa
    agregado en el panel.
    """
    try:
        from ..database import SessionLocal

        with SessionLocal() as db:
            return registrar_global(
                db,
                "cuenta.registrada",
                email=email,
                detalle={"pais": pais} if pais else None,
            )
    except Exception:
        log.warning("No se pudo anotar el registro de %r.", email)
        return False


# ---------------------------------------------------------------------------
# Latido diario (una fila por organización y día con uso)
# ---------------------------------------------------------------------------

#: Memo por proceso: organizaciones que ya tienen latido hoy. Acelera el
#: caso común (cualquier proceso vivo ya anotó a la organización) para que
#: el coste por petición sea un lookup en memoria; la verificación real
#: sigue siendo la base, así los procesos serverless (frios por definición)
#: no duplican filas.
_LATIDOS: dict[str, set[int]] = {}


def _memo_latidos() -> set[int]:
    hoy = date.today().isoformat()
    registro = _LATIDOS.get(hoy)
    if registro is None:
        _LATIDOS.clear()  # cambió el día: no acumula memoria indefinida
        _LATIDOS[hoy] = registro = set()
    return registro


def latido_diario(db) -> bool:
    """Garantiza una fila ``actividad.diaria`` por organización y día.

    Se llama al abrir la sesión de organización (``get_db``): es el dato
    que convierte «eventos sueltos» en «organizaciones activas por día»,
    cohortes de retención y riesgo de churn. Best-effort como todo aquí.
    """
    try:
        org_id = int(db.info.get("organizacion_id") or 0)
        if org_id <= 0:
            return False
        if org_id in _memo_latidos():
            return True
        desde = datetime.combine(date.today(), datetime.min.time())
        existe = (
            db.query(EventoProducto.id)
            .filter(
                EventoProducto.accion == "actividad.diaria",
                EventoProducto.organizacion_id == org_id,
                EventoProducto.created_at >= desde,
            )
            .first()
        )
        if existe is None:
            db.add(
                EventoProducto(
                    organizacion_id=org_id,
                    accion="actividad.diaria",
                )
            )
            db.commit()
        _memo_latidos().add(org_id)
        return True
    except Exception:
        log.warning("No se pudo anotar el latido diario (org %r).",
                    db.info.get("organizacion_id"))
        try:
            db.rollback()
        except Exception:
            pass
        return False


def dias_sin_uso(ultima: datetime | None, *, hoy: datetime | None = None) -> int | None:
    """Días desde la última actividad (None si nunca hubo). Utilidad del panel."""
    if ultima is None:
        return None
    referencia = hoy or datetime.utcnow()
    return max((referencia - ultima).days, 0)


def ventana(dias: int) -> tuple[datetime, datetime]:
    """ ``(desde, hasta)`` de los últimos ``dias`` hasta ahora."""
    hasta = datetime.utcnow()
    return hasta - timedelta(days=dias), hasta
