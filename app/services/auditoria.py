"""Registro de auditoría: quién cambió qué y cuándo (E4-026 / E4-027).

Una única tabla (``eventos_auditoria``) cubre los dos ítems del plan:

- **E4-026** — cambios de negocio: precios de catálogo, estados de
  presupuestos y facturas, envío de documentos, enlaces públicos,
  configuración y organización.
- **E4-027** — sesiones y acciones sensibles: inicio y cierre de sesión,
  cambio de contraseña, gestión del equipo, respaldo, exportación,
  restauración, compras y baja.

Reglas de diseño (no negociables):

1. **La auditoría jamás rompe el flujo principal.** Todas las funciones son
   best-effort: capturan cualquier excepción, hacen ``rollback`` de su propio
   intento y devuelven ``False``. Un fallo del registro se pierde con un
   warning en el log, nunca con un 500 al usuario.
2. **Se anota después del commit del cambio principal.** Así el ``rollback``
   del punto 1 nunca puede arrastrarse el trabajo real de la petición.
3. **El detalle nunca lleva datos sensibles**: ni contraseñas, ni tokens, ni
   claves. Correos de destinatarios sí (son datos de negocio del tenant).
4. **Inmutable**: el servicio solo inserta. En PostgreSQL el rol runtime no
   tiene GRANT de UPDATE/DELETE sobre la tabla.

Dos caminos de escritura:

- ``registrar_evento`` — eventos **de organización** (el 95 %): usa la sesión
  de la petición, que ya lleva el claim de tenant; en PostgreSQL la política
  RLS de INSERT exige ``tenant_access`` con escritura.
- ``registrar_evento_global`` — eventos **sin organización** (login, logout,
  cambio de clave, constancia de baja): en PostgreSQL entran por la función
  SECURITY DEFINER ``cotizat_security.registrar_evento_global`` con lista
  cerrada de acciones; en SQLite se insertan directo.
"""
from __future__ import annotations

import json
import logging

from sqlalchemy import text

from ..models import EventoAuditoria

log = logging.getLogger("cotizat.auditoria")

#: Acciones globales admitidas (lista cerrada, igual en la función PostgreSQL).
ACCIONES_GLOBALES = (
    "sesion.login",
    "sesion.logout",
    "cuenta.clave_cambiada",
    "organizacion.baja",
)


def _serializar_detalle(detalle) -> str:
    if not detalle:
        return "{}"
    try:
        texto = json.dumps(detalle, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return "{}"
    # Un detalle desmedido es señal de que alguien metió un payload entero.
    return texto if len(texto) <= 2000 else "{}"


def registrar_evento(
    db,
    accion: str,
    *,
    entidad: str = "",
    entidad_id: int | None = None,
    detalle: dict | None = None,
) -> bool:
    """Anota un evento de la organización activa. Best-effort, nunca lanza.

    Llamar **después** del commit del cambio principal: si este insert falla,
    el ``rollback`` interno solo puede deshacer el propio evento.
    """
    try:
        organizacion_id = int(db.info.get("organizacion_id") or 0)
        if organizacion_id <= 0:
            return False
        evento = EventoAuditoria(
            organizacion_id=organizacion_id,
            actor_email=str(db.info.get("auth_email") or "")[:254],
            actor_rol=str(db.info.get("rol_membresia") or "")[:20],
            accion=str(accion or "")[:60],
            entidad=str(entidad or "")[:40],
            entidad_id=entidad_id,
            detalle=_serializar_detalle(detalle),
        )
        if not evento.accion:
            return False
        db.add(evento)
        db.commit()
        return True
    except Exception:
        log.warning("No se pudo registrar el evento de auditoría %r.", accion)
        try:
            db.rollback()
        except Exception:
            pass
        return False


def registrar_evento_global(
    db,
    accion: str,
    *,
    email: str = "",
    ip_hash: str = "",
    detalle: dict | None = None,
) -> bool:
    """Anota un evento sin organización (sesión/baja). Best-effort.

    Solo admite las acciones de :data:`ACCIONES_GLOBALES`; en PostgreSQL la
    función SECURITY DEFINER vuelve a validar la lista (defensa en
    profundidad: aunque el código llamara mal, la base no aceptaría una
    acción arbitraria como evento sin organización).
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
                    "SELECT cotizat_security.registrar_evento_global("
                    " :email, :accion, :ip_hash, :detalle)"
                ),
                {
                    "email": email,
                    "accion": accion,
                    "ip_hash": str(ip_hash or "")[:64],
                    "detalle": cuerpo,
                },
            )
            db.commit()
            return True
        db.add(
            EventoAuditoria(
                organizacion_id=None,
                actor_email=email,
                accion=accion,
                detalle=cuerpo,
                ip_hash=str(ip_hash or "")[:64],
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


def anotar_sesion(accion: str, *, email: str, request=None) -> bool:
    """Evento de sesión con una sesión de base propia y efímera.

    Las rutas de autenticación no dependen de ``get_db`` (en el login todavía
    no hay organización), así que este helper abre su propia sesión — el
    mismo patrón que el registro de consentimiento del alta.
    """
    try:
        from ..database import SessionLocal
        from .prueba_gratuita import hash_ip

        ip = ""
        if request is not None and getattr(request, "client", None):
            ip = request.client.host or ""
        with SessionLocal() as db:
            return registrar_evento_global(
                db, accion, email=email, ip_hash=hash_ip(ip)
            )
    except Exception:
        log.warning("No se pudo anotar el evento de sesión %r.", accion)
        return False


# ---------------------------------------------------------------------------
# Lectura para la vista «Actividad» (roles de gestión)
# ---------------------------------------------------------------------------

#: Nombres legibles de las acciones para la vista (fuente única).
ACCIONES_LEGIBLES = {
    "sesion.login": "Inicio de sesión",
    "sesion.logout": "Cierre de sesión",
    "cuenta.clave_cambiada": "Cambio de contraseña",
    "organizacion.baja": "Baja de organización",
    "presupuesto.estado": "Estado del presupuesto",
    "presupuesto.enviado": "Presupuesto enviado por email",
    "propuesta.enlace_creado": "Enlace público creado",
    "propuesta.enlace_revocado": "Enlace público revocado",
    "factura.estado": "Estado de la factura",
    "catalogo.precio_partida": "Precio de partida",
    "catalogo.precios_ajustados": "Ajuste masivo de precios",
    "catalogo.precio_producto": "Precio de producto",
    "catalogo.precio_recurso": "Precio de recurso",
    "configuracion.actualizada": "Configuración actualizada",
    "organizacion.renombrada": "Organización renombrada",
    "equipo.invitacion_enviada": "Invitación enviada",
    "equipo.invitacion_revocada": "Invitación revocada",
    "equipo.rol_cambiado": "Rol de miembro cambiado",
    "equipo.miembro_desactivado": "Miembro desactivado",
    "datos.respaldo_descargado": "Respaldo descargado",
    "datos.exportacion_descargada": "Exportación descargada",
    "datos.restauracion_ejecutada": "Restauración ejecutada",
    "plan.compra_registrada": "Compra de plan registrada",
}


def eventos_de_organizacion(db, *, pagina: int = 1, por_pagina: int = 50):
    """Eventos de la organización activa, más recientes primero.

    Filtra ``organizacion_id`` **explícitamente**: la tabla no es TenantMixin
    y el filtro automático de tenant no la cubre. Devuelve
    ``(eventos, total)``.
    """
    organizacion_id = int(db.info.get("organizacion_id") or 0)
    if organizacion_id <= 0:
        return [], 0
    consulta = db.query(EventoAuditoria).filter(
        EventoAuditoria.organizacion_id == organizacion_id
    )
    total = consulta.count()
    pagina = max(1, int(pagina or 1))
    eventos = (
        consulta.order_by(
            EventoAuditoria.created_at.desc(), EventoAuditoria.id.desc()
        )
        .offset((pagina - 1) * por_pagina)
        .limit(por_pagina)
        .all()
    )
    return eventos, total
