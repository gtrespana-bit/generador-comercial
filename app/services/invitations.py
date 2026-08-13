"""Invitaciones de organización y administración segura de membresías."""
from __future__ import annotations

from datetime import datetime, timedelta
import hashlib
import re
import secrets

from sqlalchemy.orm import Session

from ..models import InvitacionOrganizacion, Membresia, Usuario

ROLES_INVITABLES = {"administrador", "miembro", "lectura"}
ROLES_GESTORES = {"propietario", "administrador"}
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class GestionEquipoError(RuntimeError):
    """La operación de equipo no respeta permisos o invariantes."""


def normalizar_email(email: str) -> str:
    normalizado = str(email or "").strip().lower()
    if len(normalizado) > 254 or not _EMAIL_RE.fullmatch(normalizado):
        raise GestionEquipoError("Escribe un email válido.")
    return normalizado


def exigir_gestor(rol_actor: str) -> None:
    if rol_actor not in ROLES_GESTORES:
        raise GestionEquipoError("Tu rol no permite administrar el equipo.")


def _rol_gestor(
    db: Session, organizacion_id: int, actor_usuario_id: int
) -> str:
    membresia = (
        db.query(Membresia)
        .filter(
            Membresia.organizacion_id == organizacion_id,
            Membresia.usuario_id == actor_usuario_id,
            Membresia.activa.is_(True),
        )
        .first()
    )
    rol = membresia.rol if membresia is not None else ""
    exigir_gestor(rol)
    return rol


def _exigir_rol_asignable(rol_actor: str, rol_objetivo: str) -> str:
    exigir_gestor(rol_actor)
    rol_objetivo = str(rol_objetivo or "").strip().lower()
    if rol_objetivo not in ROLES_INVITABLES:
        raise GestionEquipoError("El rol solicitado no es válido.")
    if rol_actor != "propietario" and rol_objetivo == "administrador":
        raise GestionEquipoError("Solo la persona propietaria puede asignar administradores.")
    return rol_objetivo


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def crear_invitacion(
    db: Session,
    *,
    organizacion_id: int,
    actor_usuario_id: int,
    email: str,
    rol: str,
    ahora: datetime | None = None,
    vigencia: timedelta = timedelta(days=7),
) -> tuple[InvitacionOrganizacion, str]:
    """Crea un enlace de un solo uso y guarda únicamente su SHA-256."""
    email = normalizar_email(email)
    actor_rol = _rol_gestor(db, organizacion_id, actor_usuario_id)
    rol = _exigir_rol_asignable(actor_rol, rol)
    ahora = ahora or datetime.utcnow()
    if vigencia <= timedelta(0) or vigencia > timedelta(days=30):
        raise GestionEquipoError("La vigencia de la invitación no es válida.")

    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario is not None:
        existente = (
            db.query(Membresia)
            .filter(
                Membresia.organizacion_id == organizacion_id,
                Membresia.usuario_id == usuario.id,
                Membresia.activa.is_(True),
            )
            .first()
        )
        if existente is not None:
            raise GestionEquipoError("Ese email ya pertenece al equipo.")

    anteriores = (
        db.query(InvitacionOrganizacion)
        .filter(
            InvitacionOrganizacion.organizacion_id == organizacion_id,
            InvitacionOrganizacion.email == email,
            InvitacionOrganizacion.accepted_at.is_(None),
            InvitacionOrganizacion.revoked_at.is_(None),
        )
        .all()
    )
    for anterior in anteriores:
        anterior.revoked_at = ahora

    token = secrets.token_urlsafe(32)
    invitacion = InvitacionOrganizacion(
        organizacion_id=organizacion_id,
        email=email,
        rol=rol,
        token_hash=_hash_token(token),
        invitada_por_usuario_id=actor_usuario_id,
        expires_at=ahora + vigencia,
    )
    db.add(invitacion)
    db.flush()
    return invitacion, token


def aceptar_invitacion(
    db: Session,
    *,
    token: str,
    usuario: Usuario,
    email_verificado: bool,
    ahora: datetime | None = None,
) -> Membresia:
    """Consume la invitación si pertenece al email autenticado y verificado."""
    token = str(token or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{32,200}", token):
        raise GestionEquipoError("La invitación no es válida o ya caducó.")
    ahora = ahora or datetime.utcnow()
    invitacion = (
        db.query(InvitacionOrganizacion)
        .filter(InvitacionOrganizacion.token_hash == _hash_token(token))
        .with_for_update()
        .first()
    )
    if (
        invitacion is None
        or invitacion.accepted_at is not None
        or invitacion.revoked_at is not None
        or invitacion.expires_at <= ahora
    ):
        raise GestionEquipoError("La invitación no es válida o ya caducó.")
    if not email_verificado or usuario.email_verificado_at is None:
        raise GestionEquipoError("Confirma tu email antes de aceptar la invitación.")
    if normalizar_email(usuario.email) != invitacion.email:
        raise GestionEquipoError(
            "Inicia sesión con el mismo email al que se envió la invitación."
        )

    membresia = (
        db.query(Membresia)
        .filter(
            Membresia.organizacion_id == invitacion.organizacion_id,
            Membresia.usuario_id == usuario.id,
        )
        .with_for_update()
        .first()
    )
    if membresia is None:
        membresia = Membresia(
            organizacion_id=invitacion.organizacion_id,
            usuario_id=usuario.id,
            rol=invitacion.rol,
            activa=True,
        )
        db.add(membresia)
    elif not membresia.activa:
        membresia.rol = invitacion.rol
        membresia.activa = True
    # Inserta/reactiva mientras la invitación aún está pendiente: la política
    # RLS de membresías valida precisamente ese hecho dentro de la transacción.
    db.flush()
    # Si otra vía ya activó la membresía, no se degrada ni eleva su rol.

    invitacion.accepted_at = ahora
    invitacion.aceptada_por_usuario_id = usuario.id
    db.flush()
    return membresia


def revocar_invitacion(
    db: Session,
    *,
    invitacion: InvitacionOrganizacion,
    organizacion_id: int,
    actor_usuario_id: int,
    ahora: datetime | None = None,
) -> None:
    if invitacion.organizacion_id != organizacion_id:
        raise GestionEquipoError("La invitación no pertenece a esta organización.")
    actor_rol = _rol_gestor(db, organizacion_id, actor_usuario_id)
    _exigir_rol_asignable(actor_rol, invitacion.rol)
    if invitacion.accepted_at is not None:
        raise GestionEquipoError("La invitación ya fue aceptada.")
    if invitacion.revoked_at is None:
        invitacion.revoked_at = ahora or datetime.utcnow()


def actualizar_membresia(
    db: Session,
    *,
    membresia: Membresia,
    organizacion_id: int,
    actor_usuario_id: int,
    rol: str,
    activa: bool,
) -> Membresia:
    """Actualiza miembros sin permitir tocar propietarios ni autoescalarse."""
    if membresia.organizacion_id != organizacion_id:
        raise GestionEquipoError("La membresía no pertenece a esta organización.")
    actor_rol = _rol_gestor(db, organizacion_id, actor_usuario_id)
    if membresia.rol == "propietario":
        raise GestionEquipoError(
            "La membresía propietaria no se modifica desde esta pantalla."
        )
    if actor_rol != "propietario" and membresia.rol == "administrador":
        raise GestionEquipoError("Solo la persona propietaria puede modificar administradores.")
    rol = _exigir_rol_asignable(actor_rol, rol)
    if membresia.usuario_id == actor_usuario_id and not activa:
        raise GestionEquipoError("No puedes desactivar tu propia membresía.")
    membresia.rol = rol
    membresia.activa = bool(activa)
    db.flush()
    return membresia
