"""Buzón de soporte: los mensajes que llegan por el botón de ayuda.

El canal de soporte de CotizaT era el correo (``soporte@cotizat.online``) y
nada más: quien escribía desde dentro de la aplicación tenía que salir a su
cliente de correo, y el titular se enteraba del mensaje solo si lo leía. Este
servicio cierra el circuito:

- **Escribir**: ``registrar_mensaje`` guarda el mensaje en
  ``mensajes_soporte`` y dispara el aviso por correo al buzón de soporte. El
  correo lleva ``reply_to`` del cliente, así que responder desde el buzón
  contesta a la persona correcta. El guardado es **un único INSERT** con la
  marca del aviso ya puesta (el correo se intenta primero): la política RLS
  de la tabla reserva el UPDATE al operador y marcar ``aviso_enviado``
  después tiraba el registro entero — no «optimizar» este orden.
- **Atender**: el panel lo lee, lo marca y anota la gestión
  (``marcar_estado``). Cada cambio queda en la auditoría del panel.

Nada de esto toca datos de negocio de una organización: el mensaje es del
titular, no del tenant, y la lectura del panel entra por la política de
operador de la tabla.
"""
from __future__ import annotations

import logging
import re

from sqlalchemy import text

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
    idioma: str = "es",
) -> tuple[MensajeSoporte, str]:
    """Guarda el mensaje y avisa por correo. Devuelve ``(mensaje, aviso_id)``.

    Lanza :class:`SoporteError` si falta el correo, el mensaje o si algún campo
    pasa del límite. El aviso por correo es *best effort*: si Resend no está
    configurado o falla, el mensaje queda guardado igualmente y se devuelve
    cadena vacía en el segundo valor. Todo el guardado es un único INSERT
    con la marca del aviso ya puesta (ver el comentario junto a ``_avisar``:
    el UPDATE está reservado al operador por RLS).
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

    # El aviso sale ANTES del INSERT y su marca viaja en la propia fila.
    # No es un capricho de orden: la política RLS de ``mensajes_soporte``
    # admite el INSERT público pero reserva el UPDATE al operador, y el
    # orden anterior (insertar, avisar, marcar ``aviso_enviado`` con un
    # UPDATE del ORM) reventaba en PostgreSQL con StaleDataError justo
    # cuando el correo SÍ había salido — rollback del mensaje y error
    # visible para quien escribía (visto en producción el 20/10/2026).
    # El aviso lleva el mensaje completo, así que ningún orden puede
    # perderlo del todo: o queda en la base, o queda en el buzón.
    aviso_id = ""
    if notificar:
        aviso_id = _avisar(
            fila, organizacion_nombre=organizacion_nombre, panel_url=panel_url, idioma=idioma
        )
    fila.aviso_enviado = bool(aviso_id)
    if db.get_bind().dialect.name == "postgresql":
        # La RLS muerde dos veces más en esta tabla, y las dos se esquivan
        # aquí (reproducido con PostgreSQL real el 20/10/2026):
        #
        # 1. El flush del ORM emite ``INSERT ... RETURNING id`` para
        #    rellenar la clave, y PostgreSQL exige que la fila devuelta
        #    pase también la política SELECT — reservada al operador.
        #    Resultado: «new row violates row-level security policy» con
        #    el correo ya enviado y el mensaje sin guardar. Asignando el
        #    id desde la secuencia (las secuencias no tienen RLS y el
        #    GRANT de la migración lo cubre) el INSERT no pide nada de
        #    vuelta y pasa el WITH CHECK público.
        fila.id = db.execute(
            text("SELECT nextval(pg_get_serial_sequence('mensajes_soporte', 'id'))")
        ).scalar_one()
    db.add(fila)
    db.flush()
    # 2. La instancia sale de la sesión con todo ya cargado: quien llama
    #    lee ``fila.id`` tras el commit, y con ``expire_on_commit`` ese
    #    acceso dispararía un SELECT de refresco que la política reduce
    #    a cero filas (ObjectDeletedError con el mensaje ya guardado y
    #    el correo ya en el buzón).
    db.expunge(fila)
    return fila, aviso_id


def _avisar(
    fila: MensajeSoporte, *, organizacion_nombre: str, panel_url: str, idioma: str = "es"
) -> str:
    """Avisa al buzón de soporte. Nunca lanza: si falla, el mensaje se
    guarda igual y la marca ``aviso_enviado`` queda a falso."""
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
            idioma=idioma,
        )
    except (EmailNotConfigured, EmailValidationError, EmailSendError) as exc:
        log.warning("Mensaje de soporte de %s guardado sin aviso por correo (%s).", fila.email, exc)
    except Exception:
        log.exception("Error avisando del mensaje de soporte de %s.", fila.email)
    return ""


# ---------------------------------------------------------------------------
# Lectura y gestión desde el panel
# ---------------------------------------------------------------------------


#: Columnas ordenables del buzón. La fecha manda por omisión: lo último que
#: llegó es lo que hay que atender.
ORDENES_SOPORTE = (
    ("fecha", "Fecha", "desc"),
    ("estado", "Estado", "asc"),
    ("tipo", "Motivo", "asc"),
)


def _consulta_mensajes(db, *, estado: str = "", tipo: str = "", q: str = ""):
    """Consulta base del buzón: la comparten la bandeja y el CSV.

    El filtro de texto se hacía **en Python después del LIMIT**: buscar un
    correo antiguo solo miraba los últimos 200 mensajes y devolvía «no hay
    resultados» aunque el mensaje existiera. Ahora el filtro va en SQL y el
    total es el de la consulta completa.
    """
    from sqlalchemy import or_

    consulta = db.query(MensajeSoporte, Organizacion.nombre).outerjoin(
        Organizacion, MensajeSoporte.organizacion_id == Organizacion.id
    )
    estado = normalizar_estado(estado) if estado else ""
    if estado:
        consulta = consulta.filter(MensajeSoporte.estado == estado)
    if tipo and tipo in tipos_validos():
        consulta = consulta.filter(MensajeSoporte.tipo == tipo)

    texto = str(q or "").strip()
    if texto:
        patron = f"%{texto}%"
        consulta = consulta.filter(
            or_(
                MensajeSoporte.nombre.ilike(patron),
                MensajeSoporte.email.ilike(patron),
                MensajeSoporte.asunto.ilike(patron),
                MensajeSoporte.mensaje.ilike(patron),
                Organizacion.nombre.ilike(patron),
            )
        )
    return consulta


def _ordenar_mensajes(consulta, orden: str, direccion: str):
    clave = orden if orden in {o[0] for o in ORDENES_SOPORTE} else "fecha"
    columna = {
        "estado": MensajeSoporte.estado,
        "tipo": MensajeSoporte.tipo,
    }.get(clave, MensajeSoporte.created_at)
    columna = columna.desc() if direccion == "desc" else columna.asc()
    return consulta.order_by(columna, MensajeSoporte.id.desc())


def _fila_mensaje(mensaje: MensajeSoporte, organizacion_nombre: str | None) -> dict:
    return {
        "mensaje": mensaje,
        "organizacion_nombre": organizacion_nombre or "",
    }


def listar_mensajes(
    db,
    *,
    estado: str = "",
    tipo: str = "",
    q: str = "",
    orden: str = "fecha",
    direccion: str = "desc",
    pagina: int = 1,
    por_pagina: int = 25,
) -> tuple[list[dict], dict]:
    """Página del buzón con su meta de paginación."""
    from .panel_listas import paginar_consulta

    consulta = _ordenar_mensajes(
        _consulta_mensajes(db, estado=estado, tipo=tipo, q=q), orden, direccion
    )
    filas, meta = paginar_consulta(consulta, pagina=pagina, por_pagina=por_pagina)
    return [_fila_mensaje(mensaje, org_nombre) for mensaje, org_nombre in filas], meta


def exportar_mensajes(
    db,
    *,
    estado: str = "",
    tipo: str = "",
    q: str = "",
    orden: str = "fecha",
    direccion: str = "desc",
) -> list[dict]:
    """Todos los mensajes que cumplen el filtro, para el CSV."""
    consulta = _ordenar_mensajes(
        _consulta_mensajes(db, estado=estado, tipo=tipo, q=q), orden, direccion
    )
    return [_fila_mensaje(mensaje, org_nombre) for mensaje, org_nombre in consulta.all()]


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
    "ORDENES_SOPORTE",
    "SoporteError",
    "contadores_soporte",
    "estados_validos",
    "exportar_mensajes",
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
