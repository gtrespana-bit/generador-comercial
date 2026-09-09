"""Consultas de conversaciones del asistente para el panel de operador.

Este módulo solo se llama desde rutas protegidas con ``get_operator_db``. No
usa la organización activa del navegador ni acepta un bypass de RLS: en
PostgreSQL la política de operador es la segunda barrera y en SQLite la
puerta es la dependencia del panel.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import and_, desc, exists, func, or_

from ..models import ConversacionIA, MensajeIA, Organizacion


MAX_POR_PAGINA = 50
MAX_EXPORT = 10_000


def _asegurar_operador(db) -> None:
    """Impide que un caller accidental convierta el panel en un bypass tenant."""
    if not db.info.get("es_operador"):
        raise PermissionError("Las conversaciones globales requieren una sesión de operador.")


def _base(db):
    """Consulta global del panel, sin el filtro ORM de un tenant residual."""
    _asegurar_operador(db)
    return db.query(ConversacionIA).execution_options(sin_filtro_organizacion=True)


def _aplicar_filtros(
    consulta,
    *,
    q: str = "",
    usuario: str = "",
    organizacion_id: int | None = None,
    desde: datetime | None = None,
    hasta: datetime | None = None,
):
    """Añade filtros con parámetros SQLAlchemy, incluido texto de mensajes."""
    # La fecha de expiración también es una condición de privacidad: una fila
    # vencida no vuelve a aparecer aunque el operador busque por texto.
    consulta = consulta.filter(ConversacionIA.expires_at > datetime.utcnow())
    if organizacion_id:
        consulta = consulta.filter(ConversacionIA.organizacion_id == int(organizacion_id))
    if usuario:
        consulta = consulta.filter(ConversacionIA.usuario_email.ilike(f"%{usuario}%"))
    if desde is not None:
        consulta = consulta.filter(ConversacionIA.ultimo_mensaje_at >= desde)
    if hasta is not None:
        consulta = consulta.filter(ConversacionIA.ultimo_mensaje_at < hasta)
    texto = str(q or "").strip()
    if texto:
        patron = f"%{texto}%"
        mensaje_coincide = exists().where(
            and_(
                MensajeIA.conversacion_id == ConversacionIA.id,
                MensajeIA.contenido.ilike(patron),
            )
        )
        consulta = consulta.outerjoin(
            Organizacion,
            Organizacion.id == ConversacionIA.organizacion_id,
        ).filter(
            or_(
                ConversacionIA.titulo.ilike(patron),
                ConversacionIA.usuario_email.ilike(patron),
                Organizacion.nombre.ilike(patron),
                Organizacion.slug.ilike(patron),
                mensaje_coincide,
            )
        )
    return consulta


def _mapa_conteos(db, ids: list[int]) -> dict[int, int]:
    if not ids:
        return {}
    filas = (
        db.query(MensajeIA.conversacion_id, func.count(MensajeIA.id))
        .execution_options(sin_filtro_organizacion=True)
        .filter(MensajeIA.conversacion_id.in_(ids))
        .group_by(MensajeIA.conversacion_id)
        .all()
    )
    return {int(conversacion_id): int(cantidad) for conversacion_id, cantidad in filas}


def _organizaciones(db, ids: list[int]) -> dict[int, Organizacion]:
    if not ids:
        return {}
    return {
        int(org.id): org
        for org in db.query(Organizacion)
        .filter(Organizacion.id.in_(ids))
        .all()
    }


def listar_conversaciones(
    db,
    *,
    q: str = "",
    usuario: str = "",
    organizacion_id: int | None = None,
    desde: datetime | None = None,
    hasta: datetime | None = None,
    pagina: int = 1,
    por_pagina: int = MAX_POR_PAGINA,
) -> dict:
    """Devuelve la página filtrada y el total para el paginador del panel."""
    pagina = max(1, int(pagina or 1))
    por_pagina = max(1, min(int(por_pagina or MAX_POR_PAGINA), MAX_POR_PAGINA))
    consulta = _aplicar_filtros(
        _base(db),
        q=q,
        usuario=usuario,
        organizacion_id=organizacion_id,
        desde=desde,
        hasta=hasta,
    )
    total = consulta.order_by(None).distinct().count()
    conversaciones = (
        consulta.distinct()
        .order_by(desc(ConversacionIA.ultimo_mensaje_at), desc(ConversacionIA.id))
        .offset((pagina - 1) * por_pagina)
        .limit(por_pagina)
        .all()
    )
    orgs = _organizaciones(db, [fila.organizacion_id for fila in conversaciones])
    conteos = _mapa_conteos(db, [fila.id for fila in conversaciones])
    filas = [
        {
            "conversacion": fila,
            "organizacion": orgs.get(fila.organizacion_id),
            "mensajes": conteos.get(fila.id, 0),
        }
        for fila in conversaciones
    ]
    paginas = max(1, (total + por_pagina - 1) // por_pagina)
    return {
        "filas": filas,
        "total": int(total or 0),
        "pagina": pagina,
        "paginas": paginas,
        "por_pagina": por_pagina,
    }


def opciones_organizaciones(db) -> list[Organizacion]:
    """Organizaciones visibles al operador para el selector de filtro."""
    _asegurar_operador(db)
    return db.query(Organizacion).order_by(Organizacion.nombre, Organizacion.id).all()


def obtener_conversacion(db, public_id: str) -> dict | None:
    """Carga una conversación y sus mensajes en orden cronológico."""
    conversacion = (
        _base(db)
        .filter(
            ConversacionIA.public_id == str(public_id or "").strip(),
            ConversacionIA.expires_at > datetime.utcnow(),
        )
        .one_or_none()
    )
    if conversacion is None:
        return None
    mensajes = (
        db.query(MensajeIA)
        .execution_options(sin_filtro_organizacion=True)
        .filter(MensajeIA.conversacion_id == conversacion.id)
        .order_by(MensajeIA.orden, MensajeIA.id)
        .all()
    )
    organizacion = db.get(Organizacion, conversacion.organizacion_id)
    return {
        "conversacion": conversacion,
        "organizacion": organizacion,
        "mensajes": mensajes,
    }


def exportar_conversaciones(
    db,
    *,
    q: str = "",
    usuario: str = "",
    organizacion_id: int | None = None,
    desde: datetime | None = None,
    hasta: datetime | None = None,
    limite: int = 10_000,
) -> list[dict]:
    """Exporta el registro activo en un formato separado del backup de negocio.

    Solo se llama desde ``get_operator_db``. El límite evita generar una
    respuesta accidentalmente ilimitada y el resultado mantiene el texto de
    cada mensaje, por lo que la ruta debe seguir auditando la descarga.
    """
    _asegurar_operador(db)
    limite = max(1, min(int(limite or MAX_EXPORT), MAX_EXPORT))
    consulta = _aplicar_filtros(
        _base(db),
        q=q,
        usuario=usuario,
        organizacion_id=organizacion_id,
        desde=desde,
        hasta=hasta,
    )
    conversaciones = (
        consulta.distinct()
        .order_by(desc(ConversacionIA.ultimo_mensaje_at), desc(ConversacionIA.id))
        .limit(limite)
        .all()
    )
    orgs = _organizaciones(db, [fila.organizacion_id for fila in conversaciones])
    conteo_ids = [fila.id for fila in conversaciones]
    mensajes = (
        db.query(MensajeIA)
        .execution_options(sin_filtro_organizacion=True)
        .filter(MensajeIA.conversacion_id.in_(conteo_ids))
        .order_by(MensajeIA.conversacion_id, MensajeIA.orden, MensajeIA.id)
        .all()
        if conteo_ids else []
    )
    por_conversacion: dict[int, list[dict]] = {identificador: [] for identificador in conteo_ids}
    for mensaje in mensajes:
        por_conversacion.setdefault(mensaje.conversacion_id, []).append({
            "role": mensaje.rol,
            "content": mensaje.contenido,
            "created_at": mensaje.created_at.isoformat() if mensaje.created_at else None,
            "complete": bool(mensaje.completo),
        })
    return [
        {
            "conversation_id": conversacion.public_id,
            "organizacion": {
                "id": conversacion.organizacion_id,
                "nombre": (
                    orgs[conversacion.organizacion_id].nombre
                    if orgs.get(conversacion.organizacion_id) else ""
                ),
            },
            "usuario_email": conversacion.usuario_email,
            "titulo": conversacion.titulo,
            "pagina_inicio": conversacion.pagina_inicio,
            "estado": conversacion.estado,
            "created_at": conversacion.created_at.isoformat() if conversacion.created_at else None,
            "ultimo_mensaje_at": (
                conversacion.ultimo_mensaje_at.isoformat()
                if conversacion.ultimo_mensaje_at else None
            ),
            "mensajes": por_conversacion.get(conversacion.id, []),
        }
        for conversacion in conversaciones
    ]
