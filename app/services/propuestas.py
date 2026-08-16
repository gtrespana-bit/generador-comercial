"""Enlaces públicos, revocables y de alcance mínimo para propuestas.

El secreto solo aparece en la URL entregada al usuario. La base conserva
SHA-256 y un prefijo de identificación; una filtración de la tabla no permite
reconstruir enlaces utilizables. La fila duplica únicamente los datos que la
página pública está autorizada a mostrar y referencia el PDF exacto congelado.
"""
from __future__ import annotations

from datetime import datetime, timedelta
import hashlib
import re
import secrets

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..models import (
    Configuracion,
    EnlacePropuesta,
    Membresia,
    NotaSeguimiento,
    Presupuesto,
    PresupuestoVersion,
    Usuario,
)

TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{32,200}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
DURACIONES_ENLACE = (7, 15, 30, 60, 90)
DECISIONES_PROPUESTA = {"aceptada", "rechazada"}


class GestionEnlacePropuestaError(RuntimeError):
    """La creación, lectura o revocación no respeta las invariantes."""


def hash_token_propuesta(token: str) -> str:
    return hashlib.sha256(str(token or "").encode("utf-8")).hexdigest()


def token_propuesta_valido(token: str) -> bool:
    return bool(TOKEN_RE.fullmatch(str(token or "").strip()))


def crear_enlace_propuesta(
    db: Session,
    *,
    presupuesto: Presupuesto,
    version: PresupuestoVersion,
    config: Configuracion,
    creado_por_usuario_id: int | None,
    duracion_dias: int,
    ahora: datetime | None = None,
) -> tuple[EnlacePropuesta, str]:
    """Revoca enlaces anteriores y crea el único enlace vigente del documento."""
    ahora = ahora or datetime.utcnow()
    if duracion_dias not in DURACIONES_ENLACE:
        raise GestionEnlacePropuestaError("La duración del enlace no es válida.")
    if version.presupuesto_id != presupuesto.id:
        raise GestionEnlacePropuestaError("La versión no pertenece al presupuesto.")
    if not str(version.pdf_snapshot or "").startswith("storage://"):
        raise GestionEnlacePropuestaError(
            "La versión no tiene un PDF congelado disponible."
        )

    anteriores = (
        db.query(EnlacePropuesta)
        .filter(
            EnlacePropuesta.presupuesto_id == presupuesto.id,
            EnlacePropuesta.revoked_at.is_(None),
            EnlacePropuesta.expires_at > ahora,
        )
        .all()
    )
    for anterior in anteriores:
        anterior.revoked_at = ahora

    token = secrets.token_urlsafe(32)
    valido_hasta = presupuesto.fecha + timedelta(days=presupuesto.validez_dias or 30)
    enlace = EnlacePropuesta(
        presupuesto_id=presupuesto.id,
        presupuesto_version_id=version.id,
        presupuesto_version_numero=version.numero_version,
        token_hash=hash_token_propuesta(token),
        token_prefix=token[:8],
        pdf_snapshot=version.pdf_snapshot,
        empresa_nombre=(config.empresa_nombre or "").strip() or "CotizaT",
        cliente_nombre=(presupuesto.cliente.nombre or "").strip(),
        presupuesto_numero=presupuesto.numero,
        presupuesto_titulo=(presupuesto.titulo or "").strip(),
        total=presupuesto.total,
        moneda=presupuesto.moneda,
        fecha_presupuesto=presupuesto.fecha,
        valido_hasta=valido_hasta,
        creado_por_usuario_id=creado_por_usuario_id,
        expires_at=ahora + timedelta(days=duracion_dias),
        created_at=ahora,
    )
    db.add(enlace)
    db.flush()
    return enlace, token


def resolver_enlace_propuesta(
    db: Session,
    *,
    token: str,
    ahora: datetime | None = None,
) -> EnlacePropuesta | None:
    """Resuelve sin distinguir token falso, revocado o caducado."""
    token = str(token or "").strip()
    if not token_propuesta_valido(token):
        return None
    ahora = ahora or datetime.utcnow()
    return (
        db.query(EnlacePropuesta)
        .execution_options(sin_filtro_organizacion=True)
        .filter(
            EnlacePropuesta.token_hash == hash_token_propuesta(token),
            EnlacePropuesta.revoked_at.is_(None),
            EnlacePropuesta.expires_at > ahora,
        )
        .first()
    )


def registrar_respuesta_propuesta(
    db: Session,
    *,
    enlace: EnlacePropuesta,
    decision: str,
    nombre: str,
    email: str,
    comentario: str = "",
    ahora: datetime | None = None,
) -> None:
    """Registra una única respuesta sin conceder acceso al tenant.

    En PostgreSQL la escritura pasa por una función SECURITY DEFINER que solo
    modifica cinco columnas de la fila cuyo hash coincide con el claim del
    enlace. La sesión pública no recibe UPDATE sobre la tabla. SQLite usa la
    misma validación y modifica el objeto directamente.
    """
    decision = str(decision or "").strip().lower()
    nombre = str(nombre or "").strip()
    email = str(email or "").strip().lower()
    comentario = str(comentario or "").strip()
    ahora = ahora or datetime.utcnow()
    if decision not in DECISIONES_PROPUESTA:
        raise GestionEnlacePropuestaError("Selecciona aceptar o rechazar la propuesta.")
    if len(nombre) < 2 or len(nombre) > 200:
        raise GestionEnlacePropuestaError("Escribe tu nombre completo.")
    if len(email) > 254 or not EMAIL_RE.fullmatch(email):
        raise GestionEnlacePropuestaError("Escribe un email válido.")
    if len(comentario) > 2000:
        raise GestionEnlacePropuestaError("El comentario admite hasta 2.000 caracteres.")
    if not enlace.vigente(ahora) or enlace.respuesta != "pendiente":
        raise GestionEnlacePropuestaError(
            "La propuesta ya fue respondida, caducó o fue revocada."
        )

    if db.get_bind().dialect.name == "postgresql":
        enlace_id = db.execute(
            text("""
                SELECT cotizat_security.record_proposal_response(
                    :decision, :nombre, :email, :comentario
                )
            """),
            {
                "decision": decision,
                "nombre": nombre,
                "email": email,
                "comentario": comentario,
            },
        ).scalar_one_or_none()
        if enlace_id != enlace.id:
            raise GestionEnlacePropuestaError(
                "La propuesta ya fue respondida, caducó o fue revocada."
            )
        db.expire(enlace)
        return

    enlace.respuesta = decision
    enlace.respondido_por_nombre = nombre
    enlace.respondido_por_email = email
    enlace.respuesta_comentario = comentario
    enlace.responded_at = ahora
    ultima_version = (
        db.query(PresupuestoVersion)
        .filter(PresupuestoVersion.presupuesto_id == enlace.presupuesto_id)
        .order_by(PresupuestoVersion.numero_version.desc())
        .first()
    )
    presupuesto = db.get(Presupuesto, enlace.presupuesto_id)
    if (
        presupuesto is not None
        and ultima_version is not None
        and ultima_version.id == enlace.presupuesto_version_id
        and presupuesto.estado in {"enviado", "reenviado"}
    ):
        presupuesto.estado = "aprobado" if decision == "aceptada" else "rechazado"
        enlace.estado_presupuesto_actualizado = True
    db.add(NotaSeguimiento(
        organizacion_id=enlace.organizacion_id,
        presupuesto_id=enlace.presupuesto_id,
        texto=(
            f"Propuesta V{enlace.presupuesto_version_numero} {decision} por "
            f"{nombre} ({email})."
        ),
    ))


def destinatarios_respuesta_propuesta(
    db: Session, *, enlace: EnlacePropuesta
) -> list[str]:
    """Correos internos autorizados para recibir la notificación."""
    if (
        db.get_bind().dialect.name == "postgresql"
        and not db.info.get("organizacion_id")
    ):
        filas = db.execute(
            text("""
                SELECT email
                FROM cotizat_security.proposal_notification_recipients(:link_id)
            """),
            {"link_id": enlace.id},
        ).scalars().all()
        return sorted({str(email).strip().lower() for email in filas if email})
    filas = (
        db.query(Usuario.email)
        .join(Membresia, Membresia.usuario_id == Usuario.id)
        .filter(
            Membresia.organizacion_id == enlace.organizacion_id,
            Membresia.activa.is_(True),
            Membresia.rol.in_(("propietario", "administrador")),
            Usuario.activo.is_(True),
        )
        .all()
    )
    return sorted({str(fila[0]).strip().lower() for fila in filas if fila[0]})


def marcar_notificacion_respuesta(
    db: Session,
    *,
    enlace: EnlacePropuesta,
    destinatarios: list[str],
    error: str = "",
    ahora: datetime | None = None,
) -> None:
    """Anota el resultado sin permitir que la sesión pública edite la tabla."""
    ahora = ahora or datetime.utcnow()
    destinatarios_texto = ", ".join(sorted(set(destinatarios)))[:2000]
    error = str(error or "").strip()[:1000]
    if (
        db.get_bind().dialect.name == "postgresql"
        and not db.info.get("organizacion_id")
    ):
        enlace_id = db.execute(
            text("""
                SELECT cotizat_security.mark_proposal_notification(
                    :link_id, :recipients, :error
                )
            """),
            {
                "link_id": enlace.id,
                "recipients": destinatarios_texto,
                "error": error,
            },
        ).scalar_one_or_none()
        if enlace_id != enlace.id:
            raise GestionEnlacePropuestaError(
                "No se pudo registrar el resultado de la notificación."
            )
        db.expire(enlace)
        return
    enlace.notificacion_destinatarios = destinatarios_texto
    enlace.notificacion_error = error
    enlace.notificacion_enviada_at = ahora if destinatarios and not error else None


def revocar_enlace_propuesta(
    db: Session,
    *,
    enlace: EnlacePropuesta,
    ahora: datetime | None = None,
) -> None:
    if enlace.revoked_at is None:
        enlace.revoked_at = ahora or datetime.utcnow()
