"""Solicitudes de eliminación total de cuenta y datos (bloque 2).

La tabla ``solicitudes_eliminacion`` es del operador, no de tenant, así que
una sesión de cliente no puede tocarla directamente en PostgreSQL (FORCE RLS
con políticas ``cotizat_se_*``). Como en ``consentimiento``:

- **PostgreSQL (producción):** crear, leer la propia y cancelarla entra por
  las funciones SECURITY DEFINER de la migración ``p5f1c8d2a7b4``, guardadas
  por el claim de sesión ``cotizat.auth_user_id``.
- **SQLite (escritorio y pruebas):** sin RLS, se escribe y consulta directo,
  filtrando siempre por el usuario de la sesión.

La solicitud **no borra nada por sí sola**: la cuenta sigue plenamente usable
hasta que el operador la ejecuta (bloque 3). Registrarla avisa al buzón de
soporte con el mismo criterio de los demás avisos internos: nunca lanza y
nunca deshace lo ya guardado.

Lectura defensiva a propósito: ``solicitud_pendiente`` se llama al pintar
``/cuenta``. Si el código se despliega antes de aplicar el SQL en Supabase,
la tabla aún no existe y el panel no puede romperse por eso: se devuelve
``None`` (como si no hubiera solicitud) y queda registrado en el log. Las
escrituras, en cambio, devuelven el fallo para que la ruta lo declare con
honestidad en lugar de fingir una solicitud registrada que no existe.
"""
from __future__ import annotations

import hashlib
import logging
import os
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from ..models import SolicitudEliminacion

log = logging.getLogger("cotizat.eliminacion")


def hash_email(email: str) -> str:
    """SHA-256 del email normalizado con sal del despliegue, como ``hash_ip``.

    Es la marca irreversible que queda cuando la supresión se ejecuta: el
    correo en claro desaparece de la base, pero el anti-abuso (pruebas
    concedidas, registro de consentimiento) sigue pudiendo reconocer a la
    misma dirección comparando hashes. Fuente única para solicitudes y,
    al ejecutarse la purga, para las demás tablas con email.
    """
    limpia = str(email or "").strip().lower()
    if not limpia:
        return ""
    sal = (
        os.getenv("COTIZAT_HASH_SALT")
        or os.getenv("SUPABASE_SECRET_KEY")
        or "cotizat-sal-local"
    )
    return hashlib.sha256(f"{sal}|{limpia}".encode("utf-8")).hexdigest()


def _es_postgres(db) -> bool:
    return db.bind is not None and db.bind.dialect.name == "postgresql"


def registrar_solicitud(
    db,
    *,
    usuario_id: int,
    auth_user_id: str,
    email: str,
    nombre: str,
    motivo: str,
) -> int | None:
    """Registra la solicitud pendiente y devuelve su id (o ``None`` si falla).

    Idempotente en ambos motores: si ya hay una ``pendiente`` de esta
    persona, devuelve esa misma en lugar de duplicar el acta. El ``commit``
    lo hace la ruta llamante, igual que en el alta de consentimiento.
    """
    email = str(email or "").strip().lower()
    nombre = str(nombre or "")[:200]
    motivo = str(motivo or "").strip()[:4000]
    auth_user_id = str(auth_user_id or "").strip()
    if not email:
        return None
    try:
        if _es_postgres(db):
            solicitud_id = db.execute(
                text(
                    "SELECT cotizat_security.solicitar_eliminacion("
                    " :usuario_id, :auth_user_id, :email, :nombre,"
                    " :motivo, :email_hash)"
                ),
                {
                    "usuario_id": int(usuario_id),
                    "auth_user_id": auth_user_id,
                    "email": email,
                    "nombre": nombre,
                    "motivo": motivo,
                    "email_hash": hash_email(email),
                },
            ).scalar()
            return int(solicitud_id) if solicitud_id else None
        existente = (
            db.query(SolicitudEliminacion)
            .filter(
                SolicitudEliminacion.usuario_id == int(usuario_id),
                SolicitudEliminacion.estado == "pendiente",
            )
            .order_by(SolicitudEliminacion.id.asc())
            .first()
        )
        if existente is not None:
            return int(existente.id)
        fila = SolicitudEliminacion(
            usuario_id=int(usuario_id),
            auth_user_id=auth_user_id,
            email=email,
            nombre=nombre,
            motivo=motivo,
            estado="pendiente",
            created_at=datetime.utcnow(),
            email_hash=hash_email(email),
        )
        db.add(fila)
        db.flush()
        return int(fila.id)
    except SQLAlchemyError:
        log.exception(
            "No se pudo registrar la solicitud de eliminación de %s.", email
        )
        db.rollback()
        return None


def solicitud_pendiente(
    db, *, usuario_id: int, auth_user_id: str
) -> dict | None:
    """La solicitud pendiente de la sesión: ``{id, created_at, motivo}``.

    Defensiva por diseño (ver la cabecera del módulo): ante cualquier fallo
    de base —incluida la tabla aún sin crear— devuelve ``None`` y hace
    ``rollback`` para no dejar la transacción abortada al resto de la
    petición.
    """
    try:
        if _es_postgres(db):
            fila = db.execute(
                text(
                    "SELECT id, created_at, motivo"
                    " FROM cotizat_security.solicitud_eliminacion_pendiente("
                    " :auth_user_id)"
                ),
                {"auth_user_id": str(auth_user_id or "").strip()},
            ).first()
            if fila is None:
                return None
            return {
                "id": int(fila.id),
                "created_at": fila.created_at,
                "motivo": str(fila.motivo or ""),
            }
        fila = (
            db.query(SolicitudEliminacion)
            .filter(
                SolicitudEliminacion.usuario_id == int(usuario_id),
                SolicitudEliminacion.estado == "pendiente",
            )
            .order_by(SolicitudEliminacion.id.asc())
            .first()
        )
        if fila is None:
            return None
        return {
            "id": int(fila.id),
            "created_at": fila.created_at,
            "motivo": str(fila.motivo or ""),
        }
    except SQLAlchemyError:
        log.warning(
            "Solicitud de eliminación sin consultar (¿migración p5f1c8d2a7b4"
            " sin aplicar?); el panel sigue sin la marca."
        )
        db.rollback()
        return None


def cancelar_solicitud(db, *, usuario_id: int, auth_user_id: str) -> bool:
    """Cancela la solicitud pendiente de la sesión. Devuelve si cambió algo.

    Sin contraseña a propósito: cancelar es la dirección segura (nadie hace
    daño impidiendo su propio borrado), y exigirla solo pondría fricción a
    quien se arrepiente. El ``commit`` lo hace la ruta llamante.
    """
    try:
        if _es_postgres(db):
            cancelada = db.execute(
                text(
                    "SELECT cotizat_security.cancelar_solicitud_eliminacion("
                    " :auth_user_id)"
                ),
                {"auth_user_id": str(auth_user_id or "").strip()},
            ).scalar()
            return bool(cancelada)
        filas = (
            db.query(SolicitudEliminacion)
            .filter(
                SolicitudEliminacion.usuario_id == int(usuario_id),
                SolicitudEliminacion.estado == "pendiente",
            )
            .update(
                {
                    SolicitudEliminacion.estado: "cancelada",
                    SolicitudEliminacion.cancelada_at: datetime.utcnow(),
                },
                synchronize_session=False,
            )
        )
        return filas > 0
    except SQLAlchemyError:
        log.exception(
            "No se pudo cancelar la solicitud de eliminación del usuario %s.",
            usuario_id,
        )
        db.rollback()
        return False


def avisar_solicitud(
    *, nombre: str, email: str, motivo: str, panel_url: str
) -> str:
    """Avisa al buzón de soporte de la solicitud nueva. Nunca lanza: la
    solicitud ya está guardada y un fallo de correo no puede deshacerla."""
    from .email import (
        EmailNotConfigured,
        EmailSendError,
        EmailValidationError,
        enviar_solicitud_eliminacion_por_email,
    )

    try:
        return enviar_solicitud_eliminacion_por_email(
            nombre=nombre,
            email=email,
            motivo=motivo,
            panel_url=panel_url,
        )
    except (EmailNotConfigured, EmailValidationError, EmailSendError) as exc:
        log.warning(
            "Solicitud de eliminación de %s guardada sin aviso por correo (%s).",
            email,
            exc,
        )
    except Exception:
        log.exception(
            "Error avisando de la solicitud de eliminación de %s.", email
        )
    return ""
