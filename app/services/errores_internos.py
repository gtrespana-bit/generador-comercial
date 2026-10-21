"""Persistencia durable de los errores no capturados (Fase 0.2).

El middleware de ``operacion.py`` captura cada excepción que va a ser un
500 y la agrega en un buffer en memoria que muere con la instancia
serverless. Este servicio es el sumidero que faltaba: guarda la huella
en ``errores_internos`` —con la traza que permite depurar— y avisa por
correo al buzón de siempre **solo ante una huella nueva** (o una que
reaparece tras haberse marcado resuelta).

Reglas, las de todos los avisos internos de la casa:

- **Nunca lanza ni bloquea el camino feliz.** No hay coste por petición:
  solo se entra cuando ya existe un 500. La escritura va en su propia
  sesión (la del request está rota por definición) y cualquier fallo —
  incluida la tabla aún sin migrar— se traga en silencio.
- **Datos mínimos para dar seguimiento.** Solo se conserva el nombre y
  email de una identidad ya verificada, para poder contactar a quien sufrió
  el fallo. La ruta llega saneada (sin query ni tokens), el mensaje sin
  credenciales y la traza pasa por ``logs.redactar`` antes de guardarse,
  recortada a su parte útil.
- **La respuesta HTTP no se toca.** El middleware relanza la excepción
  igual que antes; esto solo deja constancia y, si toca, un correo.

En PostgreSQL la escritura entra por ``cotizat_security.
registrar_error_interno`` (SECURITY DEFINER): el llamante puede no tener
sesión —un 500 anónimo— y el rol de aplicación no tiene INSERT directo
sobre la tabla, ni SELECT sin ser operador. En SQLite el UPSERT se hace
con SQLAlchemy. Se apaga todo con ``COTIZAT_ERRORES_BD=false`` (el buffer
en memoria sigue trabajando como hasta ahora).
"""
from __future__ import annotations

import hashlib
import logging
import os
import threading
import time
import traceback
from collections import deque
from datetime import datetime, timedelta

from sqlalchemy import func, text

from ..database import SessionLocal
from ..logs import redactar
from ..models import ErrorInterno

log = logging.getLogger("cotizat.errores_internos")

#: La parte útil de una traza es el final; guardar más sería peso muerto.
TRAZA_MAXIMO = 6000
#: Tope anti-tormenta de correos «huella nueva» por proceso y hora: un bug
#: que mete identificadores en el mensaje podría generar huellas únicas
#: sin parar, y el buzón del titular no es un log.
AVISOS_MAXIMOS_POR_HORA = 5

_avisos_enviados: deque[float] = deque()
_avisos_lock = threading.Lock()

_FORMATO_FECHA = "%d/%m/%Y %H:%M UTC"


def registro_bd_activado() -> bool:
    """Interruptor: ``COTIZAT_ERRORES_BD=false`` apaga la persistencia."""
    valor = os.environ.get("COTIZAT_ERRORES_BD", "true").strip().lower()
    return valor not in {"0", "false", "no", "off"}


def huella_de(metodo: str, ruta: str, tipo: str, mensaje: str) -> str:
    """sha256 de la identidad del fallo: una fila por huella."""
    base = "|".join([metodo or "", ruta or "", tipo or "", mensaje or ""])
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def traza_de(exc: BaseException) -> str:
    """Traceback redactado y recortado a los últimos caracteres útiles."""
    try:
        texto = "".join(
            traceback.format_exception(type(exc), exc, exc.__traceback__)
        )
    except Exception:  # pragma: no cover - formatear no debería fallar
        return ""
    return redactar(texto)[-TRAZA_MAXIMO:]


# ---------------------------------------------------------------------------
# Escritura (desde el middleware, en hilo aparte)
# ---------------------------------------------------------------------------


def persistir_y_avisar(datos: dict) -> None:
    """Guarda la huella y avisa si es nueva. Nunca lanza.

    ``datos`` lleva metodo/ruta/tipo/mensaje ya saneados (los produce
    ``operacion.datos_error``), más ``traza`` y ``ahora``.
    """
    try:
        if not registro_bd_activado():
            return
        if _persistir(datos):
            _avisar(datos)
    except Exception:  # el diagnóstico jamás rompe nada
        log.debug("No se pudo persistir un error interno.", exc_info=True)


def _persistir(datos: dict) -> bool:
    """UPSERT por huella. Devuelve «hay que avisar» (nueva o resucitada)."""
    huella = huella_de(
        datos["metodo"], datos["ruta"], datos["tipo"], datos["mensaje"]
    )
    ahora: datetime = datos["ahora"]
    db = SessionLocal()
    try:
        if db.get_bind().dialect.name == "postgresql":
            avisar = db.execute(
                text(
                    "SELECT cotizat_security.registrar_error_interno("
                    ":huella, :metodo, :ruta, :tipo, :mensaje, :traza, "
                    ":usuario_email, :usuario_nombre, :ahora)"
                ),
                {
                    "huella": huella,
                    "metodo": datos["metodo"],
                    "ruta": datos["ruta"],
                    "tipo": datos["tipo"],
                    "mensaje": datos["mensaje"],
                    "traza": datos.get("traza") or "",
                    "usuario_email": str(datos.get("usuario_email") or "")[:254],
                    "usuario_nombre": str(datos.get("usuario_nombre") or "")[:200],
                    "ahora": ahora,
                },
            ).scalar()
            db.commit()
            return bool(avisar)

        fila = (
            db.query(ErrorInterno).filter_by(huella=huella).one_or_none()
        )
        if fila is None:
            db.add(
                ErrorInterno(
                    huella=huella,
                    metodo=datos["metodo"][:10],
                    ruta=datos["ruta"][:160] or "/",
                    tipo=datos["tipo"][:120],
                    mensaje=datos["mensaje"][:300],
                    usuario_email=str(datos.get("usuario_email") or "")[:254],
                    usuario_nombre=str(datos.get("usuario_nombre") or "")[:200],
                    traza=datos.get("traza") or "",
                    ocurrencias=1,
                    primera_vez=ahora,
                    ultima_vez=ahora,
                    resuelto_en=None,
                )
            )
            db.commit()
            return True
        avisar = fila.resuelto_en is not None
        fila.ocurrencias += 1
        fila.ultima_vez = ahora
        fila.traza = datos.get("traza") or ""
        fila.usuario_email = str(datos.get("usuario_email") or "")[:254]
        fila.usuario_nombre = str(datos.get("usuario_nombre") or "")[:200]
        fila.resuelto_en = None
        db.commit()
        return avisar
    finally:
        db.close()


def _cabe_otro_aviso() -> bool:
    """Ventana deslizante de una hora; consume un hueco si lo hay."""
    ahora = time.monotonic()
    with _avisos_lock:
        while _avisos_enviados and ahora - _avisos_enviados[0] > 3600:
            _avisos_enviados.popleft()
        if len(_avisos_enviados) >= AVISOS_MAXIMOS_POR_HORA:
            return False
        _avisos_enviados.append(ahora)
        return True


def _avisar(datos: dict) -> None:
    if not _cabe_otro_aviso():
        log.warning(
            "Error interno nuevo sin avisar (tope de %s/hora): %s %s %s",
            AVISOS_MAXIMOS_POR_HORA,
            datos["metodo"],
            datos["ruta"],
            datos["tipo"],
        )
        return
    from .avisos_negocio import url_panel_absoluta
    from .email import enviar_aviso_error_interno_por_email

    enviar_aviso_error_interno_por_email(
        metodo=datos["metodo"],
        ruta=datos["ruta"],
        tipo=datos["tipo"],
        mensaje=datos["mensaje"],
        traza=datos.get("traza") or "",
        usuario_email=str(datos.get("usuario_email") or "")[:254],
        usuario_nombre=str(datos.get("usuario_nombre") or "")[:200],
        cuando=datos["ahora"].strftime(_FORMATO_FECHA),
        panel_url=url_panel_absoluta("/admin/sistema?tab=estado"),
    )


# ---------------------------------------------------------------------------
# Lecturas y gestión (panel del operador y cron; sesión de operador)
# ---------------------------------------------------------------------------


def _fila_a_dict(fila: ErrorInterno) -> dict:
    """Misma forma que ``operacion.ErrorRegistrado.to_dict`` + gestión."""
    return {
        "id": fila.id,
        "metodo": fila.metodo,
        "ruta": fila.ruta,
        "tipo": fila.tipo,
        "mensaje": fila.mensaje,
        "usuario_email": fila.usuario_email or "",
        "usuario_nombre": fila.usuario_nombre or "",
        "primera_vez": fila.primera_vez.strftime(_FORMATO_FECHA),
        "ultima_vez": fila.ultima_vez.strftime(_FORMATO_FECHA),
        "ocurrencias": fila.ocurrencias,
        "traza": fila.traza or "",
        "resuelto_en": (
            fila.resuelto_en.strftime(_FORMATO_FECHA) if fila.resuelto_en else ""
        ),
    }


def listar_errores_recientes(db, limite: int = 50) -> list[dict]:
    filas = (
        db.query(ErrorInterno)
        .order_by(ErrorInterno.ultima_vez.desc())
        .limit(limite)
        .all()
    )
    return [_fila_a_dict(f) for f in filas]


def contar_errores(db) -> int:
    return int(db.query(func.count(ErrorInterno.id)).scalar() or 0)


def marcar_resuelto(db, error_id: int) -> ErrorInterno | None:
    fila = db.get(ErrorInterno, error_id)
    if fila is None:
        return None
    if fila.resuelto_en is None:
        fila.resuelto_en = datetime.utcnow()
        db.flush()
    return fila


def resumen_activas(db, horas: int = 24) -> list[dict]:
    """Huellas sin resolver con actividad reciente, para el resumen diario."""
    desde = datetime.utcnow() - timedelta(hours=horas)
    filas = (
        db.query(ErrorInterno)
        .filter(
            ErrorInterno.resuelto_en.is_(None),
            ErrorInterno.ultima_vez >= desde,
        )
        .order_by(ErrorInterno.ocurrencias.desc(), ErrorInterno.ultima_vez.desc())
        .all()
    )
    return [_fila_a_dict(f) for f in filas]


def podar_resueltos(db, dias: int = 90) -> int:
    """Borra huellas resueltas sin actividad hace más de ``dias``."""
    corte = datetime.utcnow() - timedelta(days=dias)
    borradas = (
        db.query(ErrorInterno)
        .filter(
            ErrorInterno.resuelto_en.isnot(None),
            ErrorInterno.ultima_vez < corte,
        )
        .delete(synchronize_session=False)
    )
    return int(borradas or 0)
