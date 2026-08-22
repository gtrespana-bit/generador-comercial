"""Router de endpoints para el Asistente de IA (CotizaT Copilot)."""

import json
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from . import common
from .common import get_db, get_authenticated_db
from ..services.asistente_ia import (
    asistente_configurado,
    consultar_asistente_stream,
    consultar_asistente_sync,
    estado_asistente,
    redactar_descripcion_partida,
)

router = APIRouter(prefix="/api/ia", tags=["ia"])


class MensajeChat(BaseModel):
    role: str
    content: str


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


class SolicitudRedaccion(BaseModel):
    titulo: str
    categoria: Optional[str] = ""
    unidad: Optional[str] = "m2"


@router.get("/estado")
def api_estado_ia(db: Session = Depends(get_authenticated_db)):
    """Devuelve el estado de disponibilidad y configuración del asistente de IA."""
    return JSONResponse(estado_asistente())


@router.post("/chat")
async def api_chat_ia(
    solicitud: SolicitudChat,
    db: Session = Depends(get_authenticated_db),
):
    """Endpoint principal de conversación con el asistente de IA."""
    mensajes = [{"role": m.role, "content": m.content} for m in solicitud.messages]
    contexto = solicitud.contexto.model_dump() if solicitud.contexto else None

    if not mensajes:
        return JSONResponse(
            {"ok": False, "error": "No se recibieron mensajes para procesar."},
            status_code=400,
        )

    if solicitud.stream:
        return StreamingResponse(
            consultar_asistente_stream(db, mensajes, contexto),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    respuesta = consultar_asistente_sync(db, mensajes, contexto)
    return JSONResponse({"ok": True, "respuesta": respuesta})


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
