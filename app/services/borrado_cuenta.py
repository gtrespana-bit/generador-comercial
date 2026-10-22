"""Supresión de cuenta y datos personales solicitada por la persona.

El borrado de organizaciones propias reutiliza el proceso atómico existente
(con eliminación de objetos privados); organizaciones ajenas quedan intactas,
pero se elimina la membresía de la persona. Los datos estrictamente
financieros de Stripe permanecen en el proveedor durante sus plazos legales.
Si Supabase Auth falla después de borrar los datos locales, queda un tombstone
sin email/nombre que bloquea la recreación del perfil y el cron reintenta.
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..models import CompraPlan, Membresia, Usuario

log = logging.getLogger("cotizat.borrado_cuenta")


class BorradoCuentaError(ValueError):
    """La solicitud no se puede ejecutar de forma segura."""


def resumen_borrado_cuenta(db: Session, usuario_id: int) -> list[dict[str, Any]]:
    """Describe empresas propias que se borrarán y empresas ajenas que deja."""
    membresias = (
        db.query(Membresia)
        .filter(Membresia.usuario_id == int(usuario_id), Membresia.activa.is_(True))
        .order_by(Membresia.organizacion_id)
        .all()
    )
    resultado = []
    for membresia in membresias:
        org = membresia.organizacion
        if org is None:
            continue
        es_propietaria = membresia.rol == "propietario"
        miembros = None
        if es_propietaria:
            miembros = (
                db.query(Membresia)
                .filter(
                    Membresia.organizacion_id == membresia.organizacion_id,
                    Membresia.activa.is_(True),
                )
                .count()
            )
        resultado.append(
            {
                "organizacion_id": membresia.organizacion_id,
                "nombre": org.nombre,
                "rol": membresia.rol,
                "se_borrara": es_propietaria,
                "miembros": miembros,
            }
        )
    return resultado


def ejecutar_borrado_local(
    db: Session,
    *,
    usuario_id: int,
    auth_user_id: str,
    email: str,
) -> str:
    """Borra empresas propias y suprime datos personales en una transacción.

    Los archivos privados son externos a PostgreSQL y se eliminan antes de
    confirmar la transacción. Si algo falla, la transacción de datos revierte;
    los metadatos de objetos que ya se borraron permiten reintentar.
    """
    usuario = db.get(Usuario, int(usuario_id))
    if (
        usuario is None
        or usuario.auth_user_id != str(auth_user_id or "")
        or str(usuario.email or "").casefold() != str(email or "").casefold()
    ):
        raise BorradoCuentaError("La sesión ya no coincide con la cuenta que se quiere borrar.")
    if usuario.borrado_pendiente:
        raise BorradoCuentaError("El borrado de esta cuenta ya está en proceso.")

    # Copiar los datos antes de borrar empresas: una organización propietaria
    # desaparece y cascada elimina todas sus membresías, incluido el equipo.
    propias = [
        (m.organizacion_id, m.organizacion.nombre)
        for m in resumen_membresias(db, usuario.id)
        if m.rol == "propietario" and m.organizacion is not None
    ]

    from .baja import ejecutar_baja

    try:
        if db.get_bind().dialect.name == "postgresql":
            comprobantes = db.execute(
                text(
                    "SELECT organizacion_id, referencia "
                    "FROM cotizat_security.obtener_comprobantes_borrado_usuario("
                    ":usuario_id, :auth_user_id, :email)"
                ),
                {
                    "usuario_id": int(usuario_id),
                    "auth_user_id": str(auth_user_id),
                    "email": str(email).strip().lower(),
                },
            ).all()
            ids_propios = {int(org_id) for org_id, _nombre in propias}
            from pathlib import Path

            from ..database import UPLOADS_DIR
            from ..storage import get_storage_backend, object_key_from_reference

            backend = get_storage_backend()
            for org_id, referencia in comprobantes:
                # La baja de empresa ya elimina todos los objetos registrados
                # de esas organizaciones. Para una empresa que permanece,
                # borrar solo el adjunto de pago personal del solicitante.
                object_key = object_key_from_reference(referencia)
                if int(org_id) in ids_propios and object_key:
                    continue
                try:
                    if object_key:
                        backend.delete(object_key)
                    else:
                        # Referencias históricas de SQLite/servidor local; se
                        # resuelven bajo UPLOADS_DIR para impedir traversal.
                        clean = str(referencia or "").strip().lstrip("/")
                        if clean.startswith("static/"):
                            clean = clean[7:]
                        if clean.startswith("uploads/"):
                            clean = clean[8:]
                        root = Path(UPLOADS_DIR).resolve()
                        path = (root / clean).resolve()
                        if clean and root in path.parents:
                            path.unlink(missing_ok=True)
                except Exception as exc:
                    raise BorradoCuentaError(
                        "No se pudo eliminar un comprobante de pago privado; "
                        "no se completó el borrado de la cuenta."
                    ) from exc

        for organizacion_id, nombre in propias:
            db.info["organizacion_id"] = int(organizacion_id)
            db.info["rol_membresia"] = "propietario"
            if db.get_bind().dialect.name == "postgresql":
                # RLS de las compras y archivos filtra antes de llamar a la
                # función SECURITY DEFINER de baja; mover solo db.info no
                # cambia el claim SET LOCAL de esta transacción.
                db.execute(
                    text("SELECT set_config('cotizat.organization_id', :valor, true)"),
                    {"valor": str(organizacion_id)},
                )
            suscripciones = (
                db.query(CompraPlan.stripe_subscription_id)
                .filter(
                    CompraPlan.organizacion_id == int(organizacion_id),
                    CompraPlan.metodo_pago == "stripe",
                    CompraPlan.estado == "activa",
                    CompraPlan.stripe_subscription_id.isnot(None),
                    CompraPlan.stripe_subscription_id != "",
                )
                .all()
            )
            if suscripciones:
                from .stripe import StripeError, fijar_cancelacion_al_vencer

                for subscription_id in {fila[0] for fila in suscripciones}:
                    try:
                        fijar_cancelacion_al_vencer(subscription_id, True)
                    except StripeError as exc:
                        raise BorradoCuentaError(
                            "No se pudo cancelar la renovación de una suscripción. "
                            "No se borró la cuenta; contacta con soporte para evitar "
                            "un cobro posterior."
                        ) from exc
            # La baja exige consentimiento y nombre; la pantalla de borrado
            # informa expresamente de que cada empresa propia y su equipo se
            # eliminan. Se mantiene esa defensa en profundidad aquí.
            ejecutar_baja(
                db,
                nombre_confirmado=nombre,
                confirmar=True,
                commit=False,
                # Este flujo ya programó la cancelación al vencer justo
                # arriba: no debe repetirla ni convertirla en inmediata.
                cancelar_suscripciones=False,
            )

        # La función SECURITY DEFINER verifica auth_user_id + email contra los
        # claims instalados por get_authenticated_db; nunca acepta otro perfil.
        db.execute(
            text(
                "SELECT cotizat_security.suprimir_datos_personales_usuario("
                ":usuario_id, :auth_user_id, :email)"
            ),
            {
                "usuario_id": int(usuario_id),
                "auth_user_id": str(auth_user_id),
                "email": str(email).strip().lower(),
            },
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        if isinstance(exc, BorradoCuentaError):
            raise
        raise BorradoCuentaError(
            "No se pudo completar el borrado local; no se eliminó la identidad de acceso. "
            "Inténtalo de nuevo o contacta con soporte."
        ) from exc
    return str(auth_user_id)


def resumen_membresias(db: Session, usuario_id: int) -> list[Membresia]:
    """Carga las membresías y su organización antes de ejecutar bajas."""
    return (
        db.query(Membresia)
        .filter(Membresia.usuario_id == int(usuario_id), Membresia.activa.is_(True))
        .order_by(Membresia.organizacion_id)
        .all()
    )


def finalizar_tombstone(db: Session, usuario_id: int, auth_user_id: str) -> bool:
    """Elimina el perfil seudonimizado tras borrar Supabase Auth."""
    resultado = db.execute(
        text(
            "SELECT cotizat_security.finalizar_borrado_cuenta("
            ":usuario_id, :auth_user_id)"
        ),
        {"usuario_id": int(usuario_id), "auth_user_id": str(auth_user_id)},
    ).scalar()
    db.commit()
    return bool(resultado)


def reintentar_borrados_pendientes(db: Session, limite: int = 50) -> dict[str, int]:
    """Reintenta Auth Admin para tombstones (ejecución desde el cron protegido)."""
    cantidad = max(1, min(int(limite), 200))
    pendientes = db.execute(
        text(
            "SELECT usuario_id, auth_user_id "
            "FROM cotizat_security.obtener_borrados_pendientes(:limite)"
        ),
        {"limite": cantidad},
    ).all()
    intentados = 0
    completados = 0
    for usuario_id, auth_user_id in pendientes:
        intentados += 1
        try:
            from ..auth import SupabaseAuthClient

            SupabaseAuthClient().delete_user_admin(auth_user_id or "")
            finalizar_tombstone(db, int(usuario_id), auth_user_id or "")
            completados += 1
        except Exception:
            db.rollback()
            log.warning(
                "No se pudo completar un borrado pendiente de cuenta (perfil interno #%s).",
                fila.id,
            )
    return {"intentados": intentados, "completados": completados}
