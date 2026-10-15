"""Buzón de soporte: los mensajes que llegan por el botón de ayuda.

El canal de soporte de CotizaT era el correo (``soporte@cotizat.online``) y
nada más: quien escribía desde dentro de la aplicación tenía que salir a su
cliente de correo, y el titular se enteraba del mensaje solo si lo leía. Este
servicio cierra el circuito:

- **Escribir**: ``registrar_mensaje`` guarda el mensaje en
  ``mensajes_soporte`` y dispara el aviso por correo al buzón de soporte. El
  correo lleva ``reply_to`` del cliente, así que responder desde el buzón
  contesta a la persona correcta.
- **Atender**: el panel lo lee, lo marca y anota la gestión
  (``marcar_estado``). Cada cambio queda en la auditoría del panel.

Nada de esto toca datos de negocio de una organización: el mensaje es del
titular, no del tenant, y la lectura del panel entra por la política de
operador de la tabla.
"""
from __future__ import annotations

import logging
import re

from ..models import (
    ESTADOS_SOPORTE,
    ESTADOS_SOPORTE_ETIQUETA,
    TIPOS_SOPORTE,
    TIPOS_SOPORTE_ETIQUETA,
    MensajeSoporte,
    Organizacion,
)

log = logging.getLogger("cotizat.soporte")

#: Longitudes máximas aceptadas del formulario público. Se recortan en el
#: servicio, no en la plantilla: el límite es del servidor.
MAX_NOMBRE = 200
MAX_ASUNTO = 200
MAX_MENSAJE = 8000
MAX_PAGINA = 500

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class SoporteError(ValueError):
    """El mensaje no cumple los requisitos mínimos del formulario."""


def tipos_validos() -> tuple[str, ...]:
    return tuple(clave for clave, _ in TIPOS_SOPORTE)


def estados_validos() -> tuple[str, ...]:
    return tuple(clave for clave, _ in ESTADOS_SOPORTE)


def normalizar_tipo(tipo: str) -> str:
    clave = str(tipo or "").strip().lower()
    return clave if clave in tipos_validos() else "consulta"


def normalizar_estado(estado: str) -> str:
    clave = str(estado or "").strip().lower()
    return clave if clave in estados_validos() else "nuevo"


def registrar_mensaje(
    db,
    *,
    nombre: str,
    email: str,
    tipo: str = "consulta",
    mensaje: str,
    asunto: str = "",
    pagina: str = "",
    organizacion_id: int | None = None,
    usuario_id: int | None = None,
    ip_hash: str = "",
    notificar: bool = True,
    panel_url: str = "",
) -> tuple[MensajeSoporte, str]:
    """Guarda el mensaje y avisa por correo. Devuelve ``(mensaje, aviso_id)``.

    Lanza :class:`SoporteError` si falta el correo, el mensaje o si algún campo
    pasa del límite. El aviso por correo es *best effort*: si Resend no está
    configurado o falla, el mensaje queda guardado igualmente y se devuelve
    cadena vacía en el segundo valor.
    """
    nombre = str(nombre or "").strip()[:MAX_NOMBRE]
    email = str(email or "").strip().lower()
    mensaje = str(mensaje or "").strip()
    asunto = str(asunto or "").strip()[:MAX_ASUNTO]
    pagina = str(pagina or "").strip()[:MAX_PAGINA]

    if not email or not _EMAIL_RE.fullmatch(email):
        raise SoporteError("Necesitamos un correo válido para poder contestarte.")
    if len(email) > 254:
        raise SoporteError("Ese correo es demasiado largo.")
    if not mensaje:
        raise SoporteError("Cuéntanos en qué podemos ayudarte.")
    if len(mensaje) > MAX_MENSAJE:
        raise SoporteError("El mensaje es demasiado largo; resúmelo un poco.")

    # La organización llega de la cookie de sesión: puede estar caducada, ser de
    # una empresa dada de baja o no ser legible por RLS. En ese caso el mensaje
    # se guarda **sin** organización en lugar de romper: la persona que escribe
    # no puede quedarse sin enviar su queja por una cookie vieja.
    organizacion_nombre = ""
    organizacion_valida: int | None = None
    if organizacion_id:
        try:
            organizacion = db.get(Organizacion, int(organizacion_id))
        except Exception:
            db.rollback()
            organizacion = None
        if organizacion is not None:
            organizacion_valida = int(organizacion_id)
            organizacion_nombre = organizacion.nombre

    fila = MensajeSoporte(
        nombre=nombre,
        email=email,
        organizacion_id=organizacion_valida,
        usuario_id=int(usuario_id) if usuario_id else None,
        tipo=normalizar_tipo(tipo),
        asunto=asunto,
        mensaje=mensaje,
        pagina=pagina,
        estado="nuevo",
        ip_hash=str(ip_hash or "")[:64],
    )
    db.add(fila)
    db.flush()

    aviso_id = ""
    if notificar:
        aviso_id = _avisar(fila, organizacion_nombre=organizacion_nombre, panel_url=panel_url)
        fila.aviso_enviado = bool(aviso_id)
        db.flush()
    return fila, aviso_id


def _avisar(fila: MensajeSoporte, *, organizacion_nombre: str, panel_url: str) -> str:
    """Avisa al buzón de soporte. Nunca lanza: el mensaje ya está guardado."""
    from .email import (
        EmailNotConfigured,
        EmailSendError,
        EmailValidationError,
        enviar_mensaje_soporte_por_email,
    )

    try:
        return enviar_mensaje_soporte_por_email(
            nombre=fila.nombre,
            email=fila.email,
            tipo=fila.tipo,
            mensaje=fila.mensaje,
            asunto=fila.asunto,
            organizacion_nombre=organizacion_nombre,
            pagina=fila.pagina,
            panel_url=panel_url,
        )
    except (EmailNotConfigured, EmailValidationError, EmailSendError) as exc:
        log.warning("Mensaje de soporte #%s guardado sin aviso por correo (%s).", fila.id, exc)
    except Exception:
        log.exception("Error avisando del mensaje de soporte #%s.", fila.id)
    return ""


# ---------------------------------------------------------------------------
# Lectura y gestión desde el panel
# ---------------------------------------------------------------------------


def listar_mensajes(
    db,
    *,
    estado: str = "",
    tipo: str = "",
    q: str = "",
    limite: int = 200,
) -> list[dict]:
    """Mensajes del buzón con su organización, del más nuevo al más antiguo."""
    consulta = db.query(MensajeSoporte).order_by(MensajeSoporte.created_at.desc(), MensajeSoporte.id.desc())
    estado = normalizar_estado(estado) if estado else ""
    if estado:
        consulta = consulta.filter(MensajeSoporte.estado == estado)
    if tipo and tipo in tipos_validos():
        consulta = consulta.filter(MensajeSoporte.tipo == tipo)
    filas = consulta.limit(max(1, min(int(limite or 200), 500))).all()

    texto = str(q or "").strip().lower()
    nombres_org = {o.id: o.nombre for o in db.query(Organizacion).all()}
    salida = []
    for fila in filas:
        organizacion_nombre = nombres_org.get(fila.organizacion_id, "") if fila.organizacion_id else ""
        if texto and texto not in " ".join(
            (fila.nombre, fila.email, fila.asunto, fila.mensaje, organizacion_nombre)
        ).lower():
            continue
        salida.append({"mensaje": fila, "organizacion_nombre": organizacion_nombre})
    return salida


def contadores_soporte(db) -> dict:
    """Cuántos mensajes hay por estado (el badge del menú cuenta los nuevos)."""
    from sqlalchemy import func

    filas = (
        db.query(MensajeSoporte.estado, func.count(MensajeSoporte.id))
        .group_by(MensajeSoporte.estado)
        .all()
    )
    contadores = {clave: 0 for clave, _ in ESTADOS_SOPORTE}
    for estado, total in filas:
        contadores[str(estado or "nuevo")] = int(total or 0)
    contadores["todos"] = sum(contadores.values())
    return contadores


def mensajes_sin_atender(db, *, limite: int = 5) -> list[MensajeSoporte]:
    """Los pendientes, para la campana y el «requiere tu acción» de Hoy."""
    return (
        db.query(MensajeSoporte)
        .filter(MensajeSoporte.estado == "nuevo")
        .order_by(MensajeSoporte.created_at.asc(), MensajeSoporte.id.asc())
        .limit(max(1, int(limite or 5)))
        .all()
    )


def marcar_estado(
    db,
    *,
    mensaje_id: int,
    estado: str,
    operador_email: str = "",
    nota: str = "",
    momento=None,
) -> MensajeSoporte:
    """Cambia el estado de gestión del mensaje y anota quién lo atendió."""
    from datetime import datetime

    fila = db.get(MensajeSoporte, int(mensaje_id))
    if fila is None:
        raise SoporteError("El mensaje no existe.")
    estado_normalizado = normalizar_estado(estado)
    fila.estado = estado_normalizado
    nota = str(nota or "").strip()
    if nota:
        fila.nota_interna = nota[:4000]
    if estado_normalizado == "nuevo":
        fila.atendido_por_email = ""
        fila.atendido_at = None
    else:
        fila.atendido_por_email = str(operador_email or "")[:254]
        fila.atendido_at = momento or datetime.utcnow()
    db.flush()
    return fila


def url_bandeja() -> str:
    """URL de la bandeja en el panel (una sola definición para todo el código)."""
    return "/admin/clientes?tab=soporte"


__all__ = [
    "SoporteError",
    "contadores_soporte",
    "estados_validos",
    "listar_mensajes",
    "marcar_estado",
    "mensajes_sin_atender",
    "normalizar_estado",
    "normalizar_tipo",
    "registrar_mensaje",
    "tipos_validos",
    "url_bandeja",
    "ESTADOS_SOPORTE_ETIQUETA",
    "TIPOS_SOPORTE_ETIQUETA",
]
