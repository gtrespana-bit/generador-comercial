"""Router de endpoints para el Asistente de IA (CotizaT Copilot)."""

import json
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from . import common
from .common import get_authenticated_db, get_db
from ..services.asistente_ia import (
    asistente_configurado,
    consultar_asistente_stream,
    consultar_asistente_sync,
    estado_asistente,
    redactar_descripcion_partida,
)
from ..services.conversaciones_ia import (
    ConversacionIAError,
    persistir_respuesta,
    registrar_turno,
    validar_mensajes,
)

router = APIRouter(prefix="/api/ia", tags=["ia"])


class MensajeChat(BaseModel):
    role: str = Field(..., max_length=20)
    content: str = Field(..., max_length=12_000)


class ContextoChat(BaseModel):
    pagina: str = Field(default="", max_length=240)
    presupuesto_id: Optional[int] = Field(default=None, gt=0)
    # Solo se envía para revisión, alcance o preparación de lotes desde el
    # editor. El servicio vuelve a limitar capítulos y partidas antes de leerlo.
    borrador: Optional[List[dict[str, Any]]] = Field(default=None, max_length=100)


class SolicitudChat(BaseModel):
    messages: List[MensajeChat]
    stream: Optional[bool] = True
    contexto: Optional[ContextoChat] = None
    # Clave opaca estable del agregado. La genera el servidor en la primera
    # respuesta y el frontend la reenvía en los turnos siguientes.
    conversation_id: Optional[str] = Field(default=None, max_length=64)
    # Idempotencia del turno actual: evita dos respuestas si el navegador
    # reintenta el POST después de un corte de red.
    turn_id: Optional[str] = Field(default=None, max_length=80)


class SolicitudRedaccion(BaseModel):
    titulo: str
    categoria: Optional[str] = ""
    unidad: Optional[str] = "m2"


@router.get("/estado")
def api_estado_ia(db: Session = Depends(get_authenticated_db)):
    """Devuelve el estado de disponibilidad y configuración del asistente de IA."""
    return JSONResponse(estado_asistente())


def _sse(datos: dict) -> str:
    """Serializa un evento SSE sin permitir que el contenido rompa el formato."""
    return f"data: {json.dumps(datos, ensure_ascii=False)}\n\n"


def _sse_con_identificador(fragmento: str, conversation_id: str) -> tuple[str, list[dict]]:
    """Añade el identificador al SSE del servicio y devuelve sus payloads.

    ``consultar_asistente_stream`` se usa también fuera de HTTP y por eso no
    conoce el agregado persistente. La ruta añade la metadata sin cambiar el
    contrato de los consumidores actuales.
    """
    salida: list[str] = []
    payloads: list[dict] = []
    encontro_data = False
    for linea in str(fragmento or "").splitlines():
        if not linea.strip().startswith("data:"):
            continue
        encontro_data = True
        cuerpo = linea.split(":", 1)[1].strip()
        if not cuerpo or cuerpo == "[DONE]":
            salida.append(f"data: {cuerpo}\n\n")
            continue
        try:
            datos = json.loads(cuerpo)
        except (TypeError, ValueError):
            salida.append(f"data: {cuerpo}\n\n")
            continue
        if not isinstance(datos, dict):
            salida.append(f"data: {cuerpo}\n\n")
            continue
        datos = dict(datos)
        datos["conversation_id"] = conversation_id
        datos["conversacion_id"] = conversation_id
        payloads.append(datos)
        salida.append(_sse(datos))
    if not encontro_data:
        return str(fragmento or ""), payloads
    return "".join(salida), payloads


def _guardar_respuesta_best_effort(
    db: Session,
    registro,
    texto: str,
    *,
    completo: bool,
) -> None:
    """La observabilidad nunca debe convertir una respuesta útil en un 500."""
    if registro is None or registro.respuesta_existente is not None or not texto:
        return
    try:
        persistir_respuesta(
            db,
            registro.conversation_id,
            texto,
            turn_id=registro.turn_id,
            completo=completo,
        )
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        common.log.warning("No se pudo guardar la respuesta del asistente.", exc_info=True)


@router.post("/chat")
async def api_chat_ia(
    solicitud: SolicitudChat,
    db: Session = Depends(get_db),
):
    """Endpoint principal: responde y guarda el turno en el tenant activo."""
    mensajes = [{"role": m.role, "content": m.content} for m in solicitud.messages]
    contexto = solicitud.contexto.model_dump() if solicitud.contexto else None

    try:
        # Validar antes de crear una conversación para no dejar agregados vacíos
        # cuando alguien envía un rol arbitrario o un contenido en blanco.
        mensajes = validar_mensajes(mensajes)
    except ConversacionIAError as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=400)

    try:
        registro = registrar_turno(
            db,
            mensajes,
            public_id=solicitud.conversation_id,
            turn_id=solicitud.turn_id,
            contexto=contexto,
        )
    except ConversacionIAError as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=400)
    except Exception:
        # El asistente sigue siendo útil durante una migración pendiente o una
        # incidencia temporal de la tabla de conversaciones. El error queda
        # en logs; no se exponen detalles de esquema al usuario.
        try:
            db.rollback()
        except Exception:
            pass
        common.log.warning("No se pudo preparar la persistencia del chat.", exc_info=True)
        registro = None

    if solicitud.stream:
        def generar():
            conversation_id = registro.conversation_id if registro else ""
            acumulado: list[str] = []
            finalizado = False
            # El primer evento permite que el frontend adopte la clave del
            # servidor incluso antes de recibir el primer token de Groq.
            if conversation_id:
                yield _sse({
                    "texto": "",
                    "finalizado": False,
                    "conversation_id": conversation_id,
                    "conversacion_id": conversation_id,
                })
            try:
                if registro and registro.respuesta_existente is not None:
                    acumulado.append(registro.respuesta_existente)
                    yield _sse({
                        "texto": registro.respuesta_existente,
                        "finalizado": False,
                        "conversation_id": conversation_id,
                        "conversacion_id": conversation_id,
                    })
                    finalizado = True
                    yield _sse({
                        "texto": "",
                        "finalizado": True,
                        "conversation_id": conversation_id,
                        "conversacion_id": conversation_id,
                    })
                else:
                    for fragmento in consultar_asistente_stream(db, mensajes, contexto):
                        enriquecido, payloads = _sse_con_identificador(
                            fragmento, conversation_id
                        )
                        for datos in payloads:
                            if datos.get("texto"):
                                acumulado.append(str(datos["texto"]))
                            if datos.get("finalizado"):
                                finalizado = True
                        yield enriquecido
            except Exception:
                # El servicio normalmente convierte sus fallos en un evento SSE;
                # esta guardia cubre un error de transporte inesperado.
                mensaje_error = "⚠️ No se pudo completar la respuesta del asistente."
                acumulado.append(mensaje_error)
                finalizado = True
                yield _sse({
                    "texto": mensaje_error,
                    "finalizado": True,
                    "error": True,
                    "conversation_id": conversation_id,
                    "conversacion_id": conversation_id,
                })
            finally:
                _guardar_respuesta_best_effort(
                    db,
                    registro,
                    "".join(acumulado),
                    completo=finalizado,
                )

        return StreamingResponse(
            generar(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                **({"X-Conversation-ID": registro.conversation_id} if registro else {}),
            },
        )

    if registro and registro.respuesta_existente is not None:
        respuesta = registro.respuesta_existente
    else:
        respuesta = consultar_asistente_sync(db, mensajes, contexto)
        _guardar_respuesta_best_effort(db, registro, respuesta, completo=True)
    resultado = {"ok": True, "respuesta": respuesta}
    if registro:
        resultado.update({
            "conversation_id": registro.conversation_id,
            "conversacion_id": registro.conversation_id,
        })
    return JSONResponse(resultado)


@router.post("/redactar-descripcion")
async def api_redactar_descripcion(
    solicitud: SolicitudRedaccion,
    db: Session = Depends(get_authenticated_db),
):
    """Genera una especificación técnica rigurosa para una partida."""
    titulo = solicitud.titulo.strip()
    if not titulo:
        return JSONResponse(
            {"ok": False, "error": "El título de la partida es obligatorio."},
            status_code=400,
        )

    descripcion = redactar_descripcion_partida(
        db,
        titulo=titulo,
        categoria=solicitud.categoria or "",
        unidad=solicitud.unidad or "m2",
    )
    return JSONResponse({"ok": True, "descripcion": descripcion})
