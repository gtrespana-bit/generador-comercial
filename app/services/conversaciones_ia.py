"""Persistencia segura de las conversaciones del asistente.

El navegador conserva el historial para poder construir el prompt, pero hasta
ahora ese historial desaparecía al cerrar la página. Este módulo lo reconcilia
con un agregado tenant y solo guarda el turno nuevo (o los mensajes que falten
al migrar un historial). La reconciliación es importante: el frontend envía el
historial completo y un reintento no puede duplicar todos sus mensajes.

La escritura es deliberadamente independiente del proveedor de IA. Tanto una
respuesta local como una respuesta de Groq, síncrona o en streaming, se
registran con el mismo contrato.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import re
import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import ConversacionIA, MensajeIA

log = logging.getLogger("cotizat.ia")

#: La política de privacidad y el cron usan la misma retención.
RETENCION_DIAS = 365
#: Límite de defensa en profundidad; la API aplica límites equivalentes antes
#: de llegar aquí, pero el servicio también se usa desde pruebas/integraciones.
MAX_MENSAJES_POR_SOLICITUD = 40
MAX_CARACTERES_MENSAJE = 12_000
_PUBLIC_ID_RE = re.compile(r"^[A-Za-z0-9_-]{8,64}$")
_TURNO_ID_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,80}$")


@dataclass(frozen=True)
class RegistroTurno:
    """Resultado de guardar la entrada de un turno antes de llamar a la IA."""

    conversacion: ConversacionIA
    turn_id: str
    #: Texto ya guardado de una respuesta previa cuando el POST es un reintento.
    respuesta_existente: str | None = None

    @property
    def conversation_id(self) -> str:
        """Alias en inglés para el contrato JSON del frontend."""
        return self.conversacion.public_id


class ConversacionIAError(ValueError):
    """La entrada de conversación no cumple el contrato de persistencia."""


def _ahora() -> datetime:
    return datetime.utcnow()


def _organizacion_id(db: Session) -> int:
    """Obtiene el tenant ya resuelto por ``get_db``.

    En SQLite la instalación es monousuario y las pruebas históricas de IA
    sustituyen ``get_db`` por una sesión desnuda; el valor 1 conserva ese
    contrato local. En PostgreSQL no hay fallback: omitir el contexto sería una
    escritura sin propietario y se rechaza.
    """
    valor = db.info.get("organizacion_id")
    if valor is None:
        try:
            es_sqlite = db.get_bind().dialect.name == "sqlite"
        except Exception:
            es_sqlite = False
        if es_sqlite:
            valor = 1
            db.info["organizacion_id"] = valor
    try:
        valor = int(valor or 0)
    except (TypeError, ValueError) as exc:
        raise ConversacionIAError("No hay una organización activa para guardar el chat.") from exc
    if valor <= 0:
        raise ConversacionIAError("No hay una organización activa para guardar el chat.")
    return valor


def validar_mensajes(mensajes: list[dict[str, str]]) -> list[dict[str, str]]:
    """Normaliza y valida roles/contenido antes de persistir o enviar al modelo."""
    if not isinstance(mensajes, list) or not mensajes:
        raise ConversacionIAError("No se recibieron mensajes para procesar.")
    if len(mensajes) > MAX_MENSAJES_POR_SOLICITUD:
        raise ConversacionIAError("La conversación es demasiado larga para procesarla.")

    salida: list[dict[str, str]] = []
    for mensaje in mensajes:
        if not isinstance(mensaje, dict):
            raise ConversacionIAError("El formato de un mensaje no es válido.")
        rol = str(mensaje.get("role") or "").strip().lower()
        contenido = str(mensaje.get("content") or "").strip()
        if rol not in {"user", "assistant"}:
            raise ConversacionIAError("Solo se admiten mensajes de usuario y asistente.")
        if not contenido:
            raise ConversacionIAError("Los mensajes no pueden estar vacíos.")
        if len(contenido) > MAX_CARACTERES_MENSAJE:
            raise ConversacionIAError("Un mensaje supera el tamaño permitido.")
        salida.append({"role": rol, "content": contenido})
    if salida[-1]["role"] != "user":
        raise ConversacionIAError("El último mensaje debe ser una consulta del usuario.")
    return salida


def _validar_public_id(public_id: str | None) -> str | None:
    if public_id in (None, ""):
        return None
    valor = str(public_id).strip()
    if not _PUBLIC_ID_RE.fullmatch(valor):
        raise ConversacionIAError("El identificador de conversación no es válido.")
    return valor


def _turno_id(turn_id: str | None) -> str:
    if turn_id in (None, ""):
        return uuid.uuid4().hex
    valor = str(turn_id).strip()
    if not _TURNO_ID_RE.fullmatch(valor):
        raise ConversacionIAError("El identificador de turno no es válido.")
    return valor


def _usuario_id(db: Session) -> int | None:
    try:
        valor = int(db.info.get("usuario_id") or 0)
    except (TypeError, ValueError):
        return None
    return valor if valor > 0 else None


def _usuario_email(db: Session) -> str:
    return str(db.info.get("auth_email") or "").strip().lower()[:254]


def _coincide(fila: MensajeIA, mensaje: dict[str, str]) -> bool:
    return fila.rol == mensaje["role"] and (fila.contenido or "").strip() == mensaje["content"]


def _buscar_conversacion(db: Session, public_id: str) -> ConversacionIA | None:
    """Busca dentro del tenant ya establecido por ``get_db``.

    No se usa ``sin_filtro_organizacion`` aquí: en SQLite el listener ORM es
    la barrera que evita que una clave pública de otra empresa se pueda leer o
    reutilizar, y en PostgreSQL se suma a RLS.
    """
    return (
        db.query(ConversacionIA)
        .filter(ConversacionIA.public_id == public_id)
        .one_or_none()
    )


def _mensajes_de(db: Session, conversacion_id: int) -> list[MensajeIA]:
    return (
        db.query(MensajeIA)
        .filter(MensajeIA.conversacion_id == conversacion_id)
        .order_by(MensajeIA.orden, MensajeIA.id)
        .all()
    )


def _respuesta_por_turno(db: Session, conversacion_id: int, turn_id: str) -> str | None:
    fila = (
        db.query(MensajeIA)
        .filter(
            MensajeIA.conversacion_id == conversacion_id,
            MensajeIA.rol == "assistant",
            MensajeIA.turn_id == turn_id,
        )
        .order_by(MensajeIA.id.desc())
        .first()
    )
    return fila.contenido if fila is not None else None


def _respuesta_del_ultimo_turno(
    existentes: list[MensajeIA],
    ultimo: dict[str, str],
) -> str | None:
    """Detecta reintentos de clientes antiguos que aún no mandan ``turn_id``."""
    if (
        ultimo["role"] == "user"
        and len(existentes) >= 2
        and existentes[-2].rol == "user"
        and (existentes[-2].contenido or "").strip() == ultimo["content"]
        and existentes[-1].rol == "assistant"
    ):
        return existentes[-1].contenido
    return None


def registrar_turno(
    db: Session,
    mensajes: list[dict[str, str]],
    *,
    public_id: str | None = None,
    turn_id: str | None = None,
    contexto: dict | None = None,
) -> RegistroTurno:
    """Crea/reconcilia una conversación y persiste la entrada del usuario.

    ``mensajes`` es el historial completo que ya usa el asistente. Solo se
    insertan los elementos que no son prefijo de lo guardado. La operación hace
    commit antes de iniciar el streaming para que la duda no se pierda si el
    navegador corta la conexión.
    """
    mensajes = validar_mensajes(mensajes)
    organizacion_id = _organizacion_id(db)
    solicitado = _validar_public_id(public_id)
    clave_turno = _turno_id(turn_id)
    ahora = _ahora()

    conversacion = _buscar_conversacion(db, solicitado) if solicitado else None
    if conversacion is None:
        conversacion = ConversacionIA(
            public_id=solicitado or uuid.uuid4().hex,
            organizacion_id=organizacion_id,
            usuario_id=_usuario_id(db),
            usuario_email=_usuario_email(db),
            titulo=mensajes[0]["content"][:180] if mensajes else "",
            pagina_inicio=str((contexto or {}).get("pagina") or "")[:240],
            estado="activa",
            created_at=ahora,
            updated_at=ahora,
            ultimo_mensaje_at=ahora,
            expires_at=ahora + timedelta(days=RETENCION_DIAS),
        )
        db.add(conversacion)
        try:
            db.flush()
        except IntegrityError:
            # Un cliente no puede conocer el contenido de otra organización,
            # pero sí puede reenviar por accidente una clave pública ajena. No
            # revelamos si existe: empezamos otra conversación con una clave
            # nueva en vez de convertir el choque en un 500.
            db.rollback()
            conversacion = ConversacionIA(
                public_id=uuid.uuid4().hex,
                organizacion_id=organizacion_id,
                usuario_id=_usuario_id(db),
                usuario_email=_usuario_email(db),
                titulo=mensajes[0]["content"][:180],
                pagina_inicio=str((contexto or {}).get("pagina") or "")[:240],
                estado="activa",
                created_at=ahora,
                updated_at=ahora,
                ultimo_mensaje_at=ahora,
                expires_at=ahora + timedelta(days=RETENCION_DIAS),
            )
            db.add(conversacion)
            db.flush()

    existentes = _mensajes_de(db, conversacion.id)

    # Primero el idempotency key explícito. Si el cliente reenvió el mismo
    # turno después de recibir la respuesta, no se consulta de nuevo al modelo.
    respuesta_existente = _respuesta_por_turno(db, conversacion.id, clave_turno)
    if respuesta_existente is None:
        respuesta_existente = _respuesta_del_ultimo_turno(existentes, mensajes[-1])
    if respuesta_existente is not None:
        return RegistroTurno(conversacion, clave_turno, respuesta_existente)

    # Coincidencia de prefijo: la interfaz actual envía el historial entero,
    # pero solo se agrega la cola nueva. Si no coincide (p. ej. historial viejo
    # truncado), se conserva únicamente el último mensaje de usuario para no
    # duplicar ni confiar en un historial mutable del navegador.
    comunes = 0
    while comunes < len(existentes) and comunes < len(mensajes):
        if not _coincide(existentes[comunes], mensajes[comunes]):
            break
        comunes += 1
    por_guardar = mensajes[comunes:] if comunes == len(existentes) else [mensajes[-1]]

    # No vuelvas a agregar el mismo mensaje de usuario si la respuesta falló
    # después de guardar la entrada. En ese caso se permite volver a generar la
    # respuesta, pero el mensaje conservado sigue siendo único por turno.
    ultimo_orden = max((fila.orden for fila in existentes), default=-1)
    for indice, mensaje in enumerate(por_guardar):
        if (
            existentes
            and existentes[-1].rol == mensaje["role"]
            and (existentes[-1].contenido or "").strip() == mensaje["content"]
        ):
            continue
        ultimo_orden += 1
        db.add(
            MensajeIA(
                conversacion_id=conversacion.id,
                organizacion_id=organizacion_id,
                rol=mensaje["role"],
                contenido=mensaje["content"],
                orden=ultimo_orden,
                turn_id=clave_turno if indice == len(por_guardar) - 1 and mensaje["role"] == "user" else None,
                completo=True,
                created_at=ahora,
            )
        )

    if not conversacion.titulo:
        conversacion.titulo = mensajes[0]["content"][:180]
    if not conversacion.usuario_email:
        conversacion.usuario_email = _usuario_email(db)
    if conversacion.usuario_id is None:
        conversacion.usuario_id = _usuario_id(db)
    if not conversacion.pagina_inicio:
        conversacion.pagina_inicio = str((contexto or {}).get("pagina") or "")[:240]
    conversacion.ultimo_mensaje_at = ahora
    conversacion.updated_at = ahora
    conversacion.expires_at = ahora + timedelta(days=RETENCION_DIAS)
    db.commit()
    return RegistroTurno(conversacion, clave_turno, None)


def persistir_respuesta(
    db: Session,
    public_id: str,
    texto: str,
    *,
    turn_id: str | None = None,
    completo: bool = True,
) -> bool:
    """Guarda la respuesta completa o parcial de un turno, una sola vez."""
    clave = _validar_public_id(public_id)
    if not clave:
        return False
    contenido = str(texto or "").strip()
    if not contenido:
        return False
    contenido = contenido[:MAX_CARACTERES_MENSAJE]
    organizacion_id = _organizacion_id(db)
    conversacion = _buscar_conversacion(db, clave)
    if conversacion is None:
        return False
    clave_turno = None
    if turn_id not in (None, ""):
        clave_turno = _turno_id(turn_id)
        existente_turno = _respuesta_por_turno(db, conversacion.id, clave_turno)
        if existente_turno is not None:
            return True

    existentes = _mensajes_de(db, conversacion.id)
    orden = max((fila.orden for fila in existentes), default=-1) + 1
    ahora = _ahora()
    db.add(
        MensajeIA(
            conversacion_id=conversacion.id,
            organizacion_id=organizacion_id,
            rol="assistant",
            contenido=contenido,
            orden=orden,
            turn_id=clave_turno,
            completo=bool(completo),
            created_at=ahora,
        )
    )
    conversacion.ultimo_mensaje_at = ahora
    conversacion.updated_at = ahora
    conversacion.expires_at = ahora + timedelta(days=RETENCION_DIAS)
    try:
        db.commit()
    except IntegrityError:
        # Otra instancia pudo cerrar el mismo turno entre el SELECT y el
        # INSERT. La respuesta ya existe o el mensaje se puede reintentar; en
        # ambos casos el flujo de IA no debe convertirse en un 500.
        db.rollback()
        return True
    return True


def purgar_conversaciones_expiradas(db: Session, *, ahora: datetime | None = None) -> int:
    """Borra conversaciones vencidas (sus mensajes caen por FK CASCADE).

    El cron usa una sesión de operador; en SQLite la misma función sirve para
    pruebas. Una sesión tenant nunca puede activar el bypass ORM global: la
    purga es una tarea de mantenimiento y debe ejecutarse únicamente desde
    ``get_cron_db``.
    """
    tiene_tenant = db.info.get("organizacion_id") is not None
    if tiene_tenant and not db.info.get("es_operador"):
        raise ConversacionIAError("La purga de conversaciones requiere una sesión de operador.")
    if not tiene_tenant and not db.info.get("es_operador"):
        # En SQLite el cron no pasa por get_cron_db y las pruebas necesitan una
        # forma segura de ejercer la tarea global. PostgreSQL siempre llega con
        # ``es_operador`` marcado por la dependencia del cron.
        try:
            es_sqlite = db.get_bind().dialect.name == "sqlite"
        except Exception:
            es_sqlite = False
        if not es_sqlite:
            raise ConversacionIAError("La purga de conversaciones requiere una sesión de operador.")
        db.info["es_operador"] = True
    limite = ahora or _ahora()
    consulta = db.query(ConversacionIA).execution_options(sin_filtro_organizacion=True)
    cantidad = (
        consulta.filter(ConversacionIA.expires_at <= limite)
        .delete(synchronize_session=False)
    )
    db.commit()
    return int(cantidad or 0)


def eliminar_conversacion(
    db: Session,
    public_id: str,
    *,
    global_operador: bool = False,
) -> tuple[bool, int | None]:
    """Elimina un hilo y sus mensajes para atender una petición de borrado.

    La operación deliberadamente vive fuera del backup: las copias de negocio
    no contienen texto del asistente y una eliminación solicitada no debe
    reaparecer al restaurar datos comerciales. En producción solo se permite
    desde una sesión de operador (la ruta de soporte) y la tabla sigue
    protegida por RLS.
    """
    clave = _validar_public_id(public_id)
    if not clave:
        return False, None
    if global_operador and not db.info.get("es_operador"):
        raise ConversacionIAError("El borrado global requiere una sesión de operador.")
    consulta = db.query(ConversacionIA)
    if global_operador:
        consulta = consulta.execution_options(sin_filtro_organizacion=True)
    conversacion = (
        consulta.filter(ConversacionIA.public_id == clave).one_or_none()
    )
    if conversacion is None:
        return False, None
    organizacion_id = conversacion.organizacion_id
    db.delete(conversacion)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return True, organizacion_id


def exportar_conversacion(
    db: Session,
    public_id: str,
    *,
    global_operador: bool = False,
) -> dict | None:
    """Serializa un hilo activo para una exportación de derechos separada.

    El backup de negocio no incluye conversaciones: contienen texto libre y
    tienen una retención distinta. Esta función es el formato explícito para
    una petición de acceso, y el panel de operador la usa solo tras pasar por
    ``get_operator_db``.
    """
    clave = _validar_public_id(public_id)
    if not clave:
        return None
    consulta = db.query(ConversacionIA)
    if global_operador:
        if not db.info.get("es_operador"):
            raise ConversacionIAError("La exportación global requiere una sesión de operador.")
        consulta = consulta.execution_options(sin_filtro_organizacion=True)
    conversacion = (
        consulta.filter(
            ConversacionIA.public_id == clave,
            ConversacionIA.expires_at > _ahora(),
        )
        .one_or_none()
    )
    if conversacion is None:
        return None
    mensajes = db.query(MensajeIA)
    if global_operador:
        mensajes = mensajes.execution_options(sin_filtro_organizacion=True)
    filas = (
        mensajes
        .filter(MensajeIA.conversacion_id == conversacion.id)
        .order_by(MensajeIA.orden, MensajeIA.id)
        .all()
    )
    return {
        "formato": "cotizat-conversacion",
        "version": 1,
        "conversation_id": conversacion.public_id,
        "usuario_email": conversacion.usuario_email,
        "titulo": conversacion.titulo,
        "pagina_inicio": conversacion.pagina_inicio,
        "estado": conversacion.estado,
        "created_at": conversacion.created_at.isoformat() if conversacion.created_at else None,
        "updated_at": conversacion.updated_at.isoformat() if conversacion.updated_at else None,
        "ultimo_mensaje_at": (
            conversacion.ultimo_mensaje_at.isoformat()
            if conversacion.ultimo_mensaje_at else None
        ),
        "mensajes": [
            {
                "role": fila.rol,
                "content": fila.contenido,
                "created_at": fila.created_at.isoformat() if fila.created_at else None,
                "complete": bool(fila.completo),
            }
            for fila in filas
        ],
    }
