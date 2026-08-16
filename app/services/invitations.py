"""Invitaciones de organización y administración segura de membresías."""
from __future__ import annotations

from datetime import datetime, timedelta
import hashlib
import re
import secrets

from sqlalchemy import update
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


def invitaciones_pendientes_para(
    db: Session,
    *,
    usuario: Usuario,
    ahora: datetime | None = None,
) -> list[InvitacionOrganizacion]:
    """Invitaciones vigentes dirigidas al email del usuario autenticado.

    Permite descubrir la invitación **desde dentro de la aplicación**, sin
    volver al correo. Antes, el token vivía únicamente en el enlace del email:
    quien se registraba desde la invitación perdía el hilo al confirmar la
    cuenta (el enlace de confirmación de Supabase apunta a ``/acceso`` fijo, sin
    ``next``) y aterrizaba en «crear organización» sin ninguna forma de aceptar.

    No se filtra por organización a propósito: el destinatario todavía **no**
    es miembro de ninguna, así que el filtro de tenant no aplica todavía. En
    PostgreSQL la política ``cotizat_invitation_select_recipient`` es la que
    restringe la lectura a las invitaciones del propio email verificado, de
    modo que esta consulta no puede devolver las de otra persona ni aunque el
    ORM se equivocara.

    Devuelve la fila de la invitación, nunca el secreto: ``token_hash`` no se
    expone y el nombre de la organización tampoco se lee aquí (``cotizat_org_select``
    exige una membresía que aún no existe).
    """
    if usuario.email_verificado_at is None:
        # Sin email confirmado la invitación no es aceptable; no se anuncia.
        return []
    email = str(usuario.email or "").strip().lower()
    if not email:
        return []
    ahora = ahora or datetime.utcnow()
    return (
        db.query(InvitacionOrganizacion)
        .filter(
            InvitacionOrganizacion.email == email,
            InvitacionOrganizacion.accepted_at.is_(None),
            InvitacionOrganizacion.revoked_at.is_(None),
            InvitacionOrganizacion.expires_at > ahora,
        )
        .order_by(InvitacionOrganizacion.created_at.desc())
        .all()
    )


def aceptar_invitacion_pendiente(
    db: Session,
    *,
    invitacion_id: int,
    usuario: Usuario,
    email_verificado: bool,
    ahora: datetime | None = None,
) -> Membresia:
    """Acepta desde el panel una invitación dirigida al email autenticado.

    Es la variante sin token de :func:`aceptar_invitacion`, para quien ya está
    dentro de la aplicación y no debería tener que volver al correo.

    **No debilita la seguridad.** El token del email prueba el control del
    buzón; aquí esa prueba ya la aportó Supabase al confirmar la dirección, y
    se sigue exigiendo lo mismo que en la ruta con token: sesión iniciada,
    email verificado y coincidencia exacta con el destinatario. Quien pudiera
    abusar de esta ruta tendría que controlar ya la cuenta de correo invitada,
    en cuyo caso también podría leer el enlace original.
    """
    ahora = ahora or datetime.utcnow()
    invitacion = (
        db.query(InvitacionOrganizacion)
        .filter(InvitacionOrganizacion.id == invitacion_id)
        .first()
    )
    return _consumir_invitacion(
        db,
        invitacion=invitacion,
        usuario=usuario,
        email_verificado=email_verificado,
        ahora=ahora,
    )


def aceptar_invitacion(
    db: Session,
    *,
    token: str,
    usuario: Usuario,
    email_verificado: bool,
    ahora: datetime | None = None,
) -> Membresia:
    """Consume la invitación si pertenece al email autenticado y verificado.

    La reclamación del token de un solo uso se hace con un ``UPDATE ... WHERE
    accepted_at IS NULL`` atómico, en lugar de ``SELECT ... FOR UPDATE``. Un
    ``FOR UPDATE`` sobre ``invitaciones_organizacion`` exigiría el privilegio
    UPDATE a nivel de **tabla**, pero el rol de aplicación solo lo tiene a
    nivel de **columna** (concesión deliberada de mínimos privilegios), así
    que producía ``permission denied for table`` (500). El ``rowcount`` del
    UPDATE condicional detecta cualquier consumo en carrera.

    RLS añade una segunda trampa: PostgreSQL evalúa el ``USING`` de las
    políticas SELECT como ``WITH CHECK`` sobre la **fila nueva** de un
    UPDATE. La revisión ``d7f2a9c41e63`` ajusta
    ``cotizat_invitation_select_recipient`` para que la fila aceptada siga
    siendo visible para quien la aceptó; sin ese ajuste el UPDATE moría con
    ``new row violates row-level security policy`` (500 al aceptar).
    """
    token = str(token or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{32,200}", token):
        raise GestionEquipoError("La invitación no es válida o ya caducó.")
    ahora = ahora or datetime.utcnow()
    invitacion = (
        db.query(InvitacionOrganizacion)
        .filter(InvitacionOrganizacion.token_hash == _hash_token(token))
        .first()
    )
    return _consumir_invitacion(
        db,
        invitacion=invitacion,
        usuario=usuario,
        email_verificado=email_verificado,
        ahora=ahora,
    )


def _consumir_invitacion(
    db: Session,
    *,
    invitacion: InvitacionOrganizacion | None,
    usuario: Usuario,
    email_verificado: bool,
    ahora: datetime,
) -> Membresia:
    """Validación y consumo compartidos por las dos vías de aceptación.

    Vive aparte para que aceptar por enlace del email y aceptar desde el panel
    apliquen **exactamente** las mismas comprobaciones: una divergencia entre
    ambas sería precisamente el hueco por el que se colaría un abuso.
    """
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

    # Reclamación atómica del token de un solo uso. Solo triunfa si la
    # invitación sigue pendiente, no revocada y vigente; el UPDATE pasa por la
    # política RLS ``cotizat_invitation_update_recipient``. Sin filas
    # actualizadas significa que otra petición la consumió primero.
    resultado = db.execute(
        update(InvitacionOrganizacion)
        .where(
            InvitacionOrganizacion.id == invitacion.id,
            InvitacionOrganizacion.accepted_at.is_(None),
            InvitacionOrganizacion.revoked_at.is_(None),
            InvitacionOrganizacion.expires_at > ahora,
        )
        .values(accepted_at=ahora, aceptada_por_usuario_id=usuario.id)
    )
    if resultado.rowcount != 1:
        raise GestionEquipoError("La invitación no es válida o ya caducó.")
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
