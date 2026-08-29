"""Auditoría inmutable de las acciones del panel de operador (A2).

A diferencia de ``app/services/auditoria.py`` (que registra eventos *dentro*
de una organización), este registro es del propio negocio del titular: quién
concedió una licencia, quién activó una compra, quién cambió el rol de un
operador. Se guarda en ``public.eventos_admin``.

Contrato (mismo espíritu que la auditoría de tenant):

- Nunca lanza; un fallo de registro no puede romper la acción que se audita.
- Solo inserta y lee (RLS y GRANT sin UPDATE/DELETE en PostgreSQL).
- El detalle es JSON pequeño y sin datos sensibles.
"""
from __future__ import annotations

import json
import logging

log = logging.getLogger("cotizat")

from sqlalchemy import desc

from ..models import EventoAdmin

#: Acciones que se auditan. Lista cerrada para que el panel no acepte
#: acciones inventadas por componentes que no deberían estar ahí, y para que la
#: pantalla de auditoría pueda filtrar por ellas sin escribir el código a mano.
#: ``tests/test_panel_arquitectura.py`` exige que esté cubierta cada ``accion=``
#: que emiten los routers: un registro sin etiqueta es una acción invisible.
ACCIONES_LECIBLES = {
    "equipo.operador_alta": "Alta de operador",
    "equipo.operador_rol": "Cambio de rol de operador",
    "equipo.operador_suspension": "Suspensión de operador",
    "equipo.operador_activacion": "Activación de operador",
    "licencia.concedida": "Licencia concedida",
    "licencia.creada": "Licencia creada",
    "licencia.cancelada": "Licencia cancelada",
    "licencia.suspendida": "Acceso suspendido",
    "compra.activada": "Compra activada",
    "compra.rechazada": "Compra rechazada",
    "aviso.licencias_enviadas": "Avisos de vencimiento enviados",
    "cliente.nota_creada": "Nota de cliente creada",
    "automatizacion.ejecutada": "Automatización ejecutada",
    "crm.cliente_actualizado": "Estado comercial del cliente",
    "admin.vista_guardada": "Vista guardada",
    "admin.vista_eliminada": "Vista eliminada",
    "api_key.creada": "Clave de API creada",
    "api_key.revocada": "Clave de API revocada",
    "web.contenido_guardado": "Borrador de contenido guardado",
    "web.contenido_publicado": "Contenido publicado",
    "web.contenido_descartado": "Borrador de contenido descartado",
    "web.aviso_creado": "Aviso de la web creado",
    "web.aviso_editado": "Aviso de la web editado",
    "web.aviso_alternado": "Visibilidad de aviso cambiada",
    "web.release_creada": "Versión creada",
    "web.release_editada": "Versión editada",
    "web.release_alternada": "Visibilidad de versión cambiada",
    "web.flag_cambiado": "Feature flag cambiado",
}

#: Resultados posibles en el registro; el panel los ofrece como filtro.
RESULTADOS_AUDITORIA = (
    ("", "Todos"),
    ("ok", "Correctas"),
    ("error", "Fallidas"),
)


def _serializar_detalle(detalle: dict | None) -> str:
    """Serialize a JSON pequeño y legible, sin datos sensibles."""
    if not isinstance(detalle, dict):
        return "{}"
    limpio = {}
    for clave, valor in list(detalle.items())[:20]:
        if clave.lower() in {"password", "token", "secret", "api_key"}:
            continue
        try:
            texto = str(valor)
        except Exception:
            texto = ""
        limpio[str(clave)[:60]] = texto[:500]
    return json.dumps(limpio, ensure_ascii=False, default=str)[:2000]


def registrar_evento_admin(
    db,
    *,
    accion: str,
    operador_email: str = "",
    operador_rol: str = "",
    entidad: str = "",
    entidad_id: int | None = None,
    organizacion_id: int | None = None,
    detalle: dict | None = None,
    ip_hash: str = "",
    resultado: str = "ok",
) -> bool:
    """Anota una acción del panel del operador. Best-effort e inmutable."""
    try:
        accion = str(accion or "").strip()
        if not accion:
            return False
        evento = EventoAdmin(
            operador_email=str(operador_email or "").lower()[:254],
            operador_rol=str(operador_rol or "").lower()[:30],
            accion=accion[:60],
            entidad=str(entidad or "")[:40],
            entidad_id=int(entidad_id) if entidad_id is not None else None,
            organizacion_id=(
                int(organizacion_id) if organizacion_id is not None else None
            ),
            detalle=_serializar_detalle(detalle),
            ip_hash=str(ip_hash or "")[:64],
            resultado=str(resultado or "ok")[:20],
        )
        db.add(evento)
        db.commit()
        return True
    except Exception:
        log.warning("No se pudo registrar el evento admin %r.", accion)
        try:
            db.rollback()
        except Exception:
            pass
        return False


def resumen_auditoria_admin(
    db,
    *,
    actor: str = "",
    accion: str = "",
    resultado: str = "",
    organizacion_id: int | None = None,
    limite: int = 200,
    desde=None,
    hasta=None,
) -> list[EventoAdmin]:
    """Eventos del panel, filtrados y ordenados de más reciente a más antiguo.

    ``resultado`` vale ``ok`` o ``error``: poder separar los intentos fallidos
    es la razón por la que el registro guarda el campo, y hasta ahora la única
    forma de verlos era descargar la tabla.
    """
    consulta = db.query(EventoAdmin)
    actor_l = (actor or "").strip().lower()
    if actor_l:
        consulta = consulta.filter(
            EventoAdmin.operador_email.ilike(f"%{actor_l}%")
        )
    if accion:
        consulta = consulta.filter(EventoAdmin.accion == accion.strip())
    if resultado:
        consulta = consulta.filter(EventoAdmin.resultado == resultado.strip().lower())
    if organizacion_id:
        consulta = consulta.filter(
            EventoAdmin.organizacion_id == int(organizacion_id)
        )
    if desde is not None:
        consulta = consulta.filter(EventoAdmin.created_at >= desde)
    if hasta is not None:
        consulta = consulta.filter(EventoAdmin.created_at <= hasta)
    return consulime(consulta, limite)


def consulime(consulta, limite: int):
    return (
        consulta.order_by(desc(EventoAdmin.created_at), desc(EventoAdmin.id))
        .limit(max(1, min(int(limite), 500)))
        .all()
    )


def acciones_disponibles() -> list[tuple[str, str]]:
    return sorted(ACCIONES_LECIBLES.items())
