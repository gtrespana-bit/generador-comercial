"""Envío de correos transaccionales por API REST (Resend).

CotizaT envía correos de invitación a una organización, avisos de vencimiento
de licencia y presupuestos PDF dirigidos al cliente. Este módulo los manda por
la API REST de Resend con
`urllib`, el mismo patrón que `app/auth.py`, `app/storage.py` y
`app/ratelimit.py`: sin dependencias nuevas en el runtime ni regeneración del
lock.

Configuración mínima: `RESEND_API_KEY` (clave `re_...`, EXCLUSIVA del backend)
y `COTIZAT_EMAIL_FROM` (dirección verificada en Resend). Sin ellas el flujo no
falla: `/equipo` vuelve a mostrar el enlace en pantalla, el comportamiento de
siempre. Un fallo del proveedor tampoco rompe la invitación: la invitación ya
está guardada en la base antes de intentar el envío, y el enlace sigue
disponible una vez en pantalla como respaldo.

Privacidad: solo se envía a Resend la dirección del invitado y el contenido
del correo; ningún secreto del servidor viaja al frontend.
"""
from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import date, datetime
import json
import logging
import os
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request as UrlRequest, urlopen

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..branding import PRODUCT_NAME
from ..database import BASE_DIR

logger = logging.getLogger("cotizat.email")

RESEND_API_URL = "https://api.resend.com/emails"
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

#: Etiquetas estables para el cuerpo del correo, iguales a las de la pantalla.
ETIQUETAS_ROL = {
    "administrador": "Administrador",
    "miembro": "Miembro",
    "lectura": "Solo lectura",
}

_jinja = Environment(
    loader=FileSystemLoader(str(BASE_DIR / "app" / "templates")),
    autoescape=select_autoescape(["html", "xml"]),
)


class EmailNotConfigured(RuntimeError):
    """Faltan variables de entorno o no son válidas para enviar correos."""


class EmailSendError(RuntimeError):
    """El proveedor no confirmó el envío."""


class EmailValidationError(ValueError):
    """Algún dato del correo no es seguro o no cumple los límites."""


@dataclass(frozen=True)
class EmailAttachment:
    """Archivo adjunto enviado por la API de Resend."""

    filename: str
    content: bytes


def _env(nombre: str) -> str:
    return str(os.environ.get(nombre, "")).strip()


def _direccion_valida(direccion: str) -> bool:
    """Acepta `correo@dominio.com` o `Nombre <correo@dominio.com>`."""
    limpia = direccion.strip()
    if "<" in limpia:
        inicio = limpia.rfind("<")
        fin = limpia.rfind(">")
        if inicio == -1 or fin != len(limpia) - 1 or not limpia[:inicio].strip():
            return False
        limpia = limpia[inicio + 1 : fin]
    return bool(_EMAIL_RE.fullmatch(limpia))


@dataclass(frozen=True)
class EmailSettings:
    api_key: str
    from_address: str

    @classmethod
    def from_environment(cls) -> "EmailSettings":
        api_key = _env("RESEND_API_KEY")
        from_address = _env("COTIZAT_EMAIL_FROM")
        if not api_key and not from_address:
            raise EmailNotConfigured(
                "El envío de correos no está configurado (faltan RESEND_API_KEY "
                "y COTIZAT_EMAIL_FROM)."
            )
        if not api_key:
            raise EmailNotConfigured("Falta RESEND_API_KEY.")
        if not api_key.startswith("re_"):
            raise EmailNotConfigured(
                "RESEND_API_KEY debe ser una clave de Resend (empieza por re_)."
            )
        if not from_address:
            raise EmailNotConfigured("Falta COTIZAT_EMAIL_FROM.")
        if "\n" in from_address or "\r" in from_address or not _direccion_valida(from_address):
            raise EmailNotConfigured(
                "COTIZAT_EMAIL_FROM no es una dirección válida. "
                "Usa `Nombre <correo@dominio.com>` o `correo@dominio.com`."
            )
        return cls(api_key=api_key, from_address=from_address)


def _post_resend(
    settings: EmailSettings,
    *,
    to: str,
    subject: str,
    html: str,
    text: str,
    reply_to: str = "",
    attachments: tuple[EmailAttachment, ...] = (),
) -> str:
    """Envía el correo y devuelve el id confirmado por Resend.

    Los adjuntos se codifican en base64 dentro del JSON, que es el formato de
    la API REST. Se limita el total antes de construir el cuerpo para no agotar
    memoria en una función serverless ni convertir este método en un envío de
    archivos arbitrarios.
    """
    if not _direccion_valida(to) or "<" in to:
        raise EmailValidationError("La dirección de destino no es válida.")
    if not subject.strip() or len(subject) > 200 or "\n" in subject or "\r" in subject:
        raise EmailValidationError("El asunto no es válido o supera 200 caracteres.")
    if reply_to and (not _direccion_valida(reply_to) or "<" in reply_to):
        raise EmailValidationError("La dirección de respuesta no es válida.")
    if len(attachments) > 3:
        raise EmailValidationError("No se pueden adjuntar más de 3 archivos.")
    if sum(len(adjunto.content) for adjunto in attachments) > 8 * 1024 * 1024:
        raise EmailValidationError("Los archivos adjuntos superan 8 MB.")

    payload = {
        "from": settings.from_address,
        "to": [to],
        "subject": subject.strip(),
        "html": html,
        "text": text,
    }
    if reply_to:
        payload["reply_to"] = reply_to
    if attachments:
        payload["attachments"] = [
            {
                "filename": Path(adjunto.filename).name[:180] or "archivo.pdf",
                "content": base64.b64encode(adjunto.content).decode("ascii"),
            }
            for adjunto in attachments
        ]
    cuerpo = json.dumps(payload).encode("utf-8")
    request = UrlRequest(
        RESEND_API_URL,
        data=cuerpo,
        headers={
            "Authorization": f"Bearer {settings.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "CotizaT/1.0",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=10) as respuesta:  # noqa: S310 (URL fija)
            crudo = respuesta.read(64 * 1024)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise EmailSendError(
            f"El proveedor de correo no respondió ({type(exc).__name__})."
        ) from exc
    try:
        datos = json.loads(crudo.decode("utf-8"))
        envio_id = str(datos.get("id") or "")
    except (ValueError, UnicodeDecodeError) as exc:
        raise EmailSendError("El proveedor de correo devolvió una respuesta inesperada.") from exc
    if not envio_id:
        raise EmailSendError("El proveedor de correo no confirmó el envío.")
    return envio_id


def enviar_invitacion_por_email(
    *,
    email: str,
    enlace: str,
    organizacion_nombre: str,
    invitador_nombre: str,
    invitador_email: str,
    rol: str,
    caduca_el: datetime,
) -> str:
    """Envía el correo de invitación y devuelve el id del envío.

    Lanza `EmailNotConfigured` si faltan variables y `EmailSendError` si el
    proveedor falla; quien llama decide el respaldo (mostrar el enlace en
    pantalla). La invitación ya debe estar confirmada en la base: este envío
    nunca es la fuente de verdad.
    """
    settings = EmailSettings.from_environment()
    invitador = invitador_nombre.strip() or invitador_email or "Alguien de tu equipo"
    contexto = {
        "product_name": PRODUCT_NAME,
        "organizacion_nombre": organizacion_nombre,
        "invitador": invitador,
        "invitador_email": invitador_email,
        "rol": ETIQUETAS_ROL.get(rol, rol),
        "enlace": enlace,
        "caduca_el": caduca_el,
        "anio": datetime.utcnow().year,
    }
    asunto = f"{invitador} te invitó a {organizacion_nombre} · {PRODUCT_NAME}"
    html = _jinja.get_template("emails/invitacion.html").render(**contexto)
    texto = _jinja.get_template("emails/invitacion.txt").render(**contexto)
    try:
        envio_id = _post_resend(
            settings, to=email, subject=asunto, html=html, text=texto
        )
    except EmailSendError as exc:
        logger.warning("No se pudo enviar la invitación a %s (%s).", email, exc)
        raise
    logger.info("Invitación enviada a %s (id %s).", email, envio_id)
    return envio_id


def email_destino_valido(email: str) -> bool:
    """Valida una dirección simple de destinatario (sin nombre visible)."""
    limpio = str(email or "").strip()
    return len(limpio) <= 254 and "<" not in limpio and _direccion_valida(limpio)


def enviar_presupuesto_por_email(
    *,
    email: str,
    asunto: str,
    mensaje: str,
    empresa_nombre: str,
    cliente_nombre: str,
    presupuesto_numero: str,
    presupuesto_titulo: str,
    total_texto: str,
    pdf: bytes,
    nombre_pdf: str,
    responder_a: str = "",
) -> str:
    """Entrega al cliente un presupuesto PDF y devuelve el id de Resend."""
    email = str(email or "").strip().lower()
    asunto = str(asunto or "").strip()
    mensaje = str(mensaje or "").strip()
    if not email_destino_valido(email):
        raise EmailValidationError("Escribe un email de destino válido.")
    if not asunto or len(asunto) > 200 or "\n" in asunto or "\r" in asunto:
        raise EmailValidationError("El asunto es obligatorio y admite hasta 200 caracteres.")
    if not mensaje:
        raise EmailValidationError("Escribe el mensaje que recibirá el cliente.")
    if len(mensaje) > 5000:
        raise EmailValidationError("El mensaje admite hasta 5.000 caracteres.")
    if not pdf or not pdf.startswith(b"%PDF-"):
        raise EmailValidationError("No se pudo preparar un PDF válido para adjuntar.")
    responder_a = str(responder_a or "").strip().lower()
    if responder_a and not email_destino_valido(responder_a):
        responder_a = ""

    settings = EmailSettings.from_environment()
    contexto = {
        "product_name": PRODUCT_NAME,
        "empresa_nombre": str(empresa_nombre or "").strip() or PRODUCT_NAME,
        "cliente_nombre": str(cliente_nombre or "").strip(),
        "presupuesto_numero": str(presupuesto_numero or "").strip(),
        "presupuesto_titulo": str(presupuesto_titulo or "").strip(),
        "total_texto": str(total_texto or "").strip(),
        "mensaje": mensaje,
        "permite_responder": bool(responder_a),
        "anio": datetime.utcnow().year,
    }
    html = _jinja.get_template("emails/presupuesto.html").render(**contexto)
    texto = _jinja.get_template("emails/presupuesto.txt").render(**contexto)
    try:
        envio_id = _post_resend(
            settings,
            to=email,
            subject=asunto,
            html=html,
            text=texto,
            reply_to=responder_a,
            attachments=(EmailAttachment(filename=nombre_pdf, content=pdf),),
        )
    except EmailSendError as exc:
        logger.warning("No se pudo enviar el presupuesto a %s (%s).", email, exc)
        raise
    logger.info(
        "Presupuesto %s enviado a %s (id %s).",
        presupuesto_numero,
        email,
        envio_id,
    )
    return envio_id


def enviar_respuesta_propuesta_por_email(
    *,
    email: str,
    decision: str,
    empresa_nombre: str,
    cliente_nombre: str,
    presupuesto_numero: str,
    presupuesto_titulo: str,
    version_numero: int,
    respondido_por_nombre: str,
    respondido_por_email: str,
    comentario: str,
    enlace_interno: str,
) -> str:
    """Notifica a un administrador la respuesta registrada por el cliente."""
    email = str(email or "").strip().lower()
    if not email_destino_valido(email):
        raise EmailValidationError("El destinatario interno no es válido.")
    decision = str(decision or "").strip().lower()
    if decision not in {"aceptada", "rechazada"}:
        raise EmailValidationError("La respuesta de la propuesta no es válida.")
    settings = EmailSettings.from_environment()
    contexto = {
        "product_name": PRODUCT_NAME,
        "decision": decision,
        "empresa_nombre": str(empresa_nombre or "").strip() or PRODUCT_NAME,
        "cliente_nombre": str(cliente_nombre or "").strip(),
        "presupuesto_numero": str(presupuesto_numero or "").strip(),
        "presupuesto_titulo": str(presupuesto_titulo or "").strip(),
        "version_numero": int(version_numero),
        "respondido_por_nombre": str(respondido_por_nombre or "").strip(),
        "respondido_por_email": str(respondido_por_email or "").strip().lower(),
        "comentario": str(comentario or "").strip(),
        "enlace_interno": enlace_interno,
        "anio": datetime.utcnow().year,
    }
    asunto = (
        f"Propuesta {decision}: {presupuesto_numero} · "
        f"{cliente_nombre or respondido_por_nombre}"
    )[:200]
    html = _jinja.get_template("emails/respuesta_propuesta.html").render(**contexto)
    texto = _jinja.get_template("emails/respuesta_propuesta.txt").render(**contexto)
    try:
        envio_id = _post_resend(
            settings,
            to=email,
            subject=asunto,
            html=html,
            text=texto,
            reply_to=contexto["respondido_por_email"],
        )
    except EmailSendError as exc:
        logger.warning(
            "No se pudo notificar la respuesta de %s a %s (%s).",
            presupuesto_numero,
            email,
            exc,
        )
        raise
    logger.info(
        "Respuesta de propuesta %s notificada a %s (id %s).",
        presupuesto_numero,
        email,
        envio_id,
    )
    return envio_id


def enviar_aviso_licencia(
    *,
    email: str,
    organizacion_nombre: str,
    vence: date,
    dias_restantes: int,
) -> str:
    """Avisa a un administrador de que el acceso de su organización vence.

    Lo dispara el operador desde el panel de licencias (no hay trabajos en
    segundo plano en el despliegue serverless). Con cobro manual (E1-059) el
    aviso no enlaza a ninguna pasarela: invita a escribir a soporte para
    acordar la renovación, que es exactamente cómo se cobra el piloto.
    """
    settings = EmailSettings.from_environment()
    contexto = {
        "product_name": PRODUCT_NAME,
        "organizacion_nombre": organizacion_nombre,
        "vence": vence,
        "dias_restantes": dias_restantes,
        "soporte_email": _soporte_email(),
        "anio": datetime.utcnow().year,
    }
    asunto = (
        f"Tu acceso a {PRODUCT_NAME} vence el "
        f"{vence.strftime('%d/%m/%Y')} · {organizacion_nombre}"
    )
    html = _jinja.get_template("emails/aviso_licencia.html").render(**contexto)
    texto = _jinja.get_template("emails/aviso_licencia.txt").render(**contexto)
    try:
        envio_id = _post_resend(settings, to=email, subject=asunto, html=html, text=texto)
    except EmailSendError as exc:
        logger.warning(
            "No se pudo enviar el aviso de vencimiento a %s (%s).", email, exc
        )
        raise
    logger.info("Aviso de vencimiento enviado a %s (id %s).", email, envio_id)
    return envio_id


def enviar_solicitud_demo_por_email(
    *,
    nombre: str,
    email: str,
    empresa: str,
    telefono: str = "",
    presupuestos_mes: str = "",
    mensaje: str = "",
) -> str:
    """Notifica al equipo de soporte sobre una nueva solicitud de demo.

    El formulario de la landing pública es la única fuente. Se envía a
    ``SUPPORT_EMAIL`` (configurable vía ``COTIZAT_SUPPORT_EMAIL``). Si el
    correo no está configurado, la solicitud se pierde silenciosamente; no
    es bloqueante porque la landing siempre puede caer en un mailto como
    respaldo.

    Devuelve el id de Resend o ``""`` si no se pudo enviar.
    """
    from ..branding import PRODUCT_NAME, SUPPORT_EMAIL

    nombre = str(nombre or "").strip()
    email = str(email or "").strip().lower()
    empresa = str(empresa or "").strip()
    telefono = str(telefono or "").strip()
    presupuestos_mes = str(presupuestos_mes or "").strip()
    mensaje = str(mensaje or "").strip()

    if not nombre or not email or not email_destino_valido(email):
        raise EmailValidationError("Nombre y email válido son obligatorios.")
    if len(nombre) > 200:
        raise EmailValidationError("El nombre es demasiado largo.")
    if len(empresa) > 200:
        raise EmailValidationError("El nombre de la empresa es demasiado largo.")
    if len(mensaje) > 5000:
        raise EmailValidationError("El mensaje es demasiado largo.")

    destino = _env("COTIZAT_DEMO_DESTINO") or SUPPORT_EMAIL
    if not destino:
        raise EmailNotConfigured("No hay dirección de destino para la solicitud de demo.")

    try:
        settings = EmailSettings.from_environment()
    except EmailNotConfigured:
        logger.warning(
            "Solicitud de demo ignorada: correo no configurado "
            "(RESEND_API_KEY / COTIZAT_EMAIL_FROM)."
        )
        return ""

    contexto = {
        "product_name": PRODUCT_NAME,
        "nombre": nombre,
        "email": email,
        "empresa": empresa,
        "telefono": telefono,
        "presupuestos_mes": presupuestos_mes,
        "mensaje": mensaje,
    }
    asunto = f"Nueva solicitud de demo: {nombre} ({empresa or email})"[:200]
    try:
        html = _jinja.get_template("emails/demo.html").render(**contexto)
    except Exception:
        html = (
            "<h2>Nueva solicitud de demo</h2>"
            f"<p><strong>Nombre:</strong> {nombre}</p>"
            f"<p><strong>Email:</strong> {email}</p>"
            f"<p><strong>Empresa:</strong> {empresa}</p>"
        )
    try:
        texto = _jinja.get_template("emails/demo.txt").render(**contexto)
    except Exception:
        texto = f"Nueva solicitud de demo: {nombre} ({empresa or email})"

    try:
        envio_id = _post_resend(
            settings,
            to=destino,
            subject=asunto,
            html=html,
            text=texto,
            reply_to=email,
        )
    except EmailSendError as exc:
        logger.warning("No se pudo enviar la solicitud de demo (%s).", exc)
        return ""
    logger.info("Solicitud de demo de %s enviada (id %s).", email, envio_id)
    return envio_id


def enviar_compra_por_email(
    *,
    nombre: str,
    email: str,
    organizacion_nombre: str,
    plan_nombre: str,
    importe_texto: str,
    metodo_nombre: str,
    verificacion: dict,
    comprobante_nombre: str,
    comprobante_bytes: bytes,
) -> str:
    """Notifica al titular una compra nueva con su comprobante adjunto.

    Devuelve el id de Resend o ``""`` si el correo no está configurado o el
    envío falla (la compra ya está guardada en la base; el email es el aviso,
    no la fuente de verdad). El operador verá la misma información en el
    panel ``/admin/compras``.
    """
    from ..branding import PRODUCT_NAME, SUPPORT_EMAIL

    destino = _env("COTIZAT_DEMO_DESTINO") or SUPPORT_EMAIL
    if not destino:
        raise EmailNotConfigured(
            "No hay dirección de destino para notificar la compra."
        )
    try:
        settings = EmailSettings.from_environment()
    except EmailNotConfigured:
        logger.warning(
            "Compra sin notificar: correo no configurado "
            "(RESEND_API_KEY / COTIZAT_EMAIL_FROM)."
        )
        return ""

    filas = []
    for clave, etiqueta in _CAMPOS_VERIFICACION_ETIQUETA.items():
        valor = str(verificacion.get(clave) or "").strip()
        if valor:
            filas.append((etiqueta, valor))
    contexto = {
        "product_name": PRODUCT_NAME,
        "nombre": str(nombre or "").strip(),
        "email": str(email or "").strip(),
        "organizacion_nombre": str(organizacion_nombre or "").strip(),
        "plan_nombre": str(plan_nombre or "").strip(),
        "importe_texto": str(importe_texto or "").strip(),
        "metodo_nombre": str(metodo_nombre or "").strip(),
        "verificacion": filas,
        "comprobante_nombre": str(comprobante_nombre or "comprobante"),
    }
    asunto = (
        f"Nueva compra: {plan_nombre} · {metodo_nombre} · "
        f"{organizacion_nombre or email}"
    )[:200]
    try:
        html = _jinja.get_template("emails/compra.html").render(**contexto)
        texto = _jinja.get_template("emails/compra.txt").render(**contexto)
    except Exception:
        html = (
            "<h2>Nueva compra registrada</h2>"
            f"<p><strong>Plan:</strong> {plan_nombre}</p>"
            f"<p><strong>Método:</strong> {metodo_nombre}</p>"
            f"<p><strong>Organización:</strong> {organizacion_nombre}</p>"
        )
        texto = f"Nueva compra: {plan_nombre} ({metodo_nombre})."

    adjunto = EmailAttachment(filename=comprobante_nombre, content=comprobante_bytes)
    try:
        envio_id = _post_resend(
            settings,
            to=destino,
            subject=asunto,
            html=html,
            text=texto,
            reply_to=email,
            attachments=(adjunto,),
        )
    except EmailSendError as exc:
        logger.warning("No se pudo notificar la compra (%s).", exc)
        return ""
    logger.info("Compra de %s notificada (id %s).", email, envio_id)
    return envio_id


_CAMPOS_VERIFICACION_ETIQUETA = {
    "banco_origen": "Banco de origen",
    "numero_operacion": "Número de operación",
    "fecha_pago": "Fecha del pago",
    "nombre_titular": "Titular",
    "binance_id_origen": "ID de Binance de origen",
    "hash_transaccion": "Hash / TXID",
    "telefono_origen": "Teléfono / ID de Kontigo",
    "wallet_origen": "Wallet de origen",
}


def _soporte_email() -> str:
    from ..branding import SUPPORT_EMAIL

    return SUPPORT_EMAIL


def estado_configuracion_email() -> tuple[str, str | None]:
    """Describe el envío de correos para `/readyz`.

    Devuelve `(estado, error)`. Es informativo: un despliegue sin correo
    configurado sigue siendo utilizable porque las invitaciones se entregan
    como enlace en pantalla, así que nunca hace fallar el readiness.
    """
    api_key = _env("RESEND_API_KEY")
    from_address = _env("COTIZAT_EMAIL_FROM")
    if not api_key and not from_address:
        return (
            "no-configurado",
            "Faltan RESEND_API_KEY y COTIZAT_EMAIL_FROM: las invitaciones se "
            "entregan como enlace en pantalla.",
        )
    try:
        EmailSettings.from_environment()
    except EmailNotConfigured as exc:
        return "mal-configurado", str(exc)
    return "configurado", None
