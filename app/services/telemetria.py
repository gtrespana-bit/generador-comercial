"""Telemetría interna de producto: embudo, activación y retención (E5-012).

Complementa Google Analytics 4 con un dato **propio y del servidor**. GA4
mide la capa pública (tráfico, fuentes, tiempo en página) pero se pierde
todo lo que ocurre tras el login: bloqueadores y consentimiento recortan
las conversiones, la retención máxima es de 14 meses y sus datos no deben
ligarse a cuentas. Aquí lo que se guarda es el mínimo agregado que permite
responder las preguntas del plan comercial (E5: «retención a 3, 6 y 12
meses», «uso recurrente y reducción de abandono»):

- ``cuenta.registrada`` — embudo, paso 1 (evento global, sin organización).
- ``organizacion.creada`` — embudo, paso 2.
- ``actividad.diaria`` — **latido**: una fila por organización y día con
  uso. Es la base de activos por día (DAU por empresa), cohortes de
  retención y riesgo de churn.
- ``presupuesto.creado`` / ``aprobado`` / ``enviado_email`` /
  ``pdf_descargado`` — el ciclo de valor del producto.
- ``importacion.confirmada`` — adopción del importador CYPE/BC3.
- ``pago.compra_registrada`` / ``pago.checkout_iniciado`` /
  ``licencia.activada`` — el embudo de cobro.
- ``equipo.invitacion_enviada`` — señal de crecimiento intra-empresa.

Reglas heredadas de la auditoría (no negociables):

1. **La telemetría jamás rompe el flujo principal**: todas las funciones son
   best-effort, capturan cualquier excepción, hacen ``rollback`` de su
   propio intento y devuelven ``False``/``None``.
2. **Se anota después del commit del cambio principal.**
3. **El detalle nunca lleva datos sensibles** ni de clientes de la
   organización: solo métricas de negocio (plan, país, nº de partidas).
4. **Sin PII innecesaria**: no se guarda IP (ni hash). El ``actor_email``
   es el de la sesión autenticada, dato que el operador ya ve en el panel.
5. **Catálogo cerrado**: la base (PostgreSQL) valida las acciones globales
   contra una lista fija; el servicio valida todo el resto.
"""
from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta

from sqlalchemy import text

from ..models import EventoProducto

log = logging.getLogger("cotizat.telemetria")

#: Catálogo cerrado de acciones (fuente única de verdad). El panel de
#: analítica usa estas etiquetas para pintar nombre legibles.
ACCIONES: dict[str, str] = {
    "cuenta.registrada": "Cuenta registrada",
    "organizacion.creada": "Empresa creada",
    "actividad.diaria": "Uso diario",
    "sesion.activa": "Sesión activa",
    "cliente.creado": "Cliente creado",
    "presupuesto.creado": "Presupuesto creado",
    "presupuesto.aprobado": "Presupuesto aprobado",
    "presupuesto.enviado_email": "Presupuesto enviado por email",
    "presupuesto.pdf_descargado": "PDF de presupuesto descargado",
    "importacion.confirmada": "Importación CYPE/BC3",
    "asistente.consulta": "Consulta al asistente IA",
    "pago.checkout_iniciado": "Checkout Stripe iniciado",
    "pago.compra_registrada": "Compra registrada",
    "licencia.activada": "Licencia activada",
    "equipo.invitacion_enviada": "Invitación de equipo enviada",
}

#: Acciones de **ruido operativo**: se escriben solas con el uso normal y
#: llenarían la tabla de «Eventos recientes» sin aportar información. El panel
#: las oculta por omisión y las ofrece con un interruptor.
ACCIONES_RUIDO = frozenset({"actividad.diaria", "sesion.activa"})

#: Minutos sin presencia para considerar que una empresa ya no está en línea.
PRESENCIA_MINUTOS = 15

#: Cada cuántos minutos se escribe como mucho una fila ``sesion.activa`` por
#: organización. Sin este freno, cada petición autenticada dejaría una fila.
PRESENCIA_ESCRITURA_MINUTOS = 3

#: Acciones que ocurren **sin organización** (antes de existir empresa).
#: Debe coincidir con la lista de la función PostgreSQL
#: ``cotizat_security.registrar_evento_producto_global``.
ACCIONES_GLOBALES = frozenset({"cuenta.registrada"})


def etiqueta(accion: str) -> str:
    """Nombre legible de una acción (la propia si es desconocida)."""
    return ACCIONES.get(accion, accion)


def _serializar_detalle(detalle) -> str:
    if not detalle:
        return "{}"
    try:
        texto = json.dumps(detalle, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return "{}"
    return texto if len(texto) <= 2000 else "{}"


def registrar(
    db,
    accion: str,
    *,
    organizacion_id: int | None = None,
    email: str = "",
    detalle: dict | None = None,
) -> bool:
    """Anota un evento de producto de una organización. Best-effort, nunca lanza.

    La organización se toma del contexto de la sesión (``db.info``) salvo
    que se pase ``organizacion_id`` explícito — necesario en las sesiones de
    operador (activación manual) y en el alta de empresa, donde el contexto
    de tenant acaba de nacer. Llamar **después** del commit principal.
    """
    accion = str(accion or "").strip()
    if accion not in ACCIONES or accion in ACCIONES_GLOBALES:
        return False
    org_id = int(organizacion_id or db.info.get("organizacion_id") or 0)
    if org_id <= 0:
        return False
    actor = str(email or db.info.get("auth_email") or "")[:254]
    cuerpo = _serializar_detalle(detalle)
    try:
        db.add(
            EventoProducto(
                organizacion_id=org_id,
                actor_email=actor,
                accion=accion,
                detalle=cuerpo,
            )
        )
        db.commit()
        _ULTIMO_FALLO.pop(accion, None)
        return True
    except Exception as exc:
        _anotar_fallo(accion, exc)
        try:
            db.rollback()
        except Exception:
            pass
    # Segundo intento, solo para lo que decide una medición del negocio.
    if accion in ACCIONES_CRITICAS:
        try:
            if _insertar_en_sesion_nueva(accion, dict(db.info), cuerpo, _bind_de(db)):
                log.warning(
                    "El evento %r se recuperó por la vía de emergencia: la "
                    "sesión de la petición no pudo escribirlo. Revisar el "
                    "estado de la conexión, no es normal.",
                    accion,
                )
                return True
        except Exception as exc:
            _anotar_fallo(accion, exc)
    return False


def registrar_global(
    db,
    accion: str,
    *,
    email: str = "",
    detalle: dict | None = None,
) -> bool:
    """Anota un evento sin organización (alta de cuenta). Best-effort.

    En PostgreSQL entra por la función SECURITY DEFINER con lista cerrada
    (defensa en profundidad); en SQLite se inserta directo.
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
                    "SELECT cotizat_security."
                    "registrar_evento_producto_global("
                    " :email, :accion, :detalle)"
                ),
                {"email": email, "accion": accion, "detalle": cuerpo},
            )
            db.commit()
            return True
        db.add(
            EventoProducto(
                organizacion_id=None,
                actor_email=email,
                accion=accion,
                detalle=cuerpo,
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


def anotar_registro(
    *, email: str, pais: str = "", detalle_extra: dict | None = None
) -> bool:
    """``cuenta.registrada`` con sesión propia y efímera.

    La ruta de registro no depende de ``get_db`` (todavía no hay
    organización); el mismo patrón que el consentimiento y las sesiones de
    auditoría. El país llega del selector del formulario y solo se usa
    agregado en el panel.

    ``detalle_extra`` lleva la atribución de la visita (``origen_mercado``,
    ``origen_seccion``): de qué página pública vino quien se registra. Son
    dos cadenas cortas elegidas de un catálogo cerrado, nunca una URL.
    """
    try:
        from ..database import SessionLocal

        detalle: dict = {}
        if pais:
            detalle["pais"] = pais
        for clave, valor in (detalle_extra or {}).items():
            if isinstance(valor, str) and valor:
                detalle[str(clave)[:32]] = valor[:64]
        with SessionLocal() as db:
            return registrar_global(
                db,
                "cuenta.registrada",
                email=email,
                detalle=detalle or None,
            )
    except Exception:
        log.warning("No se pudo anotar el registro de %r.", email)
        return False


# ---------------------------------------------------------------------------
# Latido diario (una fila por organización y día con uso)
# ---------------------------------------------------------------------------

#: Memo por proceso: organizaciones que ya tienen latido hoy. Acelera el
#: caso común (cualquier proceso vivo ya anotó a la organización) para que
#: el coste por petición sea un lookup en memoria; la verificación real
#: sigue siendo la base, así los procesos serverless (frios por definición)
#: no duplican filas.
_LATIDOS: dict[str, set[int]] = {}


def _memo_latidos() -> set[int]:
    hoy = date.today().isoformat()
    registro = _LATIDOS.get(hoy)
    if registro is None:
        _LATIDOS.clear()  # cambió el día: no acumula memoria indefinida
        _LATIDOS[hoy] = registro = set()
    return registro


#: Acciones cuyo fallo de escritura **sí** hay que poder reconstruir después.
#: El latido y la presencia son ruido: si se pierden, no se pierde una decisión
#: de negocio. Que alguien cree su primer presupuesto, en cambio, es el paso 3
#: del embudo: si se pierde, el panel miente y se optimiza a ciegas.
ACCIONES_CRITICAS = frozenset(
    {
        "presupuesto.creado",
        "presupuesto.aprobado",
        "presupuesto.enviado_email",
        "presupuesto.pdf_descargado",
        "licencia.activada",
        "pago.compra_registrada",
    }
)

#: Motivo del último fallo por acción (para el diagnóstico del panel).
_ULTIMO_FALLO: dict[str, str] = {}


def ultimo_fallo(accion: str | None = None) -> str | dict[str, str]:
    """Por qué falló la última escritura de una acción crítica.

    Existe porque el 02/11/2026 se descubrió que **ningún** evento de cliente
    real había llegado a la base y el sistema no se quejó: ``registrar``
    captura la excepción y devuelve ``False``, así que el panel enseñaba el
    embudo de las cuentas del dueño como si fuera el del negocio. Se conserva
    el motivo en memoria para que ``/admin/analitica`` pueda enseñarlo en vez
    de un cero que parece un dato.
    """
    if accion is None:
        return dict(_ULTIMO_FALLO)
    return _ULTIMO_FALLO.get(str(accion), "")


def _anotar_fallo(accion: str, exc: BaseException | None) -> None:
    """Guarda el motivo y lo deja en el log con nivel warning."""
    motivo = f"{type(exc).__name__}: {exc}" if exc is not None else "desconocido"
    if len(motivo) > 300:
        motivo = motivo[:300] + "…"
    _ULTIMO_FALLO[accion] = motivo
    log.warning(
        "No se pudo registrar el evento de producto %r (%s).",
        accion,
        "crítico para el embudo" if accion in ACCIONES_CRITICAS else "no crítico",
    )


def _bind_de(db):
    """Motor de la sesión, sin abrir transacción ni conexión nueva."""
    try:
        return db.get_bind()
    except Exception:
        return None


def _insertar_en_sesion_nueva(
    accion: str, info_origen: dict, detalle: str, bind=None
) -> bool:
    """Segundo intento del evento crítico, con su propia sesión y transacción.

    El primer intento usa la sesión de la petición que acaba de escribir el
    presupuesto: si esa sesión quedó en una transacción abortada (o el commit
    del evento choca con un ``SAVEPOINT`` ya en vuelo), el evento se pierde sin
    que nadie se entere. Aquí se abre una conexión limpia solo para la
    telemetría y se le reinstalan **los mismos claims de RLS** de la sesión
    original, porque sin `auth_user_id` la política de escritura del tenant
    rechaza el INSERT y el segundo intento fallaría por el mismo motivo.
    """
    from sqlalchemy.orm import sessionmaker

    from ..database import SessionLocal

    # Mismo motor que la sesión original (en pruebas y en escritorio el bind
    # no es el global); el pool es el de siempre, así que esto no abre una
    # conexión nueva al servidor salvo que la anterior esté rota.
    fabrica = sessionmaker(bind=bind) if bind is not None else SessionLocal
    sesion = fabrica()
    try:
        for clave in (
            "auth_user_id",
            "auth_email",
            "organizacion_id",
            "es_operador",
            "operador_rol",
        ):
            if info_origen.get(clave) not in (None, ""):
                sesion.info[clave] = info_origen[clave]
        sesion.add(
            EventoProducto(
                organizacion_id=int(sesion.info.get("organizacion_id") or 0),
                actor_email=str(sesion.info.get("auth_email") or "")[:254],
                accion=accion,
                detalle=detalle,
            )
        )
        sesion.commit()
        return True
    finally:
        sesion.close()


def _confirmar(db, confirmar: bool) -> None:
    """Confirma la anotación, o la deja pendiente para el llamante.

    ``confirmar=False`` la usa la puerta de ``get_db``: anota latido y presencia
    y confirma **una sola vez** al final, para que la petición no pague tres
    transacciones (con sus tres checkouts del pool y sus seis ``set_config`` de
    RLS) donde basta una. El valor por omisión mantiene el contrato de siempre:
    quien llama a estas funciones por su cuenta obtiene una fila persistida.
    """
    if confirmar:
        db.commit()
    else:
        db.flush()


def latido_diario(db, *, confirmar: bool = True) -> bool:
    """Garantiza una fila ``actividad.diaria`` por organización y día.

    Se llama al abrir la sesión de organización (``get_db``): es el dato
    que convierte «eventos sueltos» en «organizaciones activas por día»,
    cohortes de retención y riesgo de churn. Best-effort como todo aquí.
    """
    try:
        org_id = int(db.info.get("organizacion_id") or 0)
        if org_id <= 0:
            return False
        if org_id in _memo_latidos():
            return True
        desde = datetime.combine(date.today(), datetime.min.time())
        existe = (
            db.query(EventoProducto.id)
            .filter(
                EventoProducto.accion == "actividad.diaria",
                EventoProducto.organizacion_id == org_id,
                EventoProducto.created_at >= desde,
            )
            .first()
        )
        if existe is None:
            db.add(
                EventoProducto(
                    organizacion_id=org_id,
                    accion="actividad.diaria",
                )
            )
            # ``confirmar=False`` (la puerta de ``get_db``) deja la fila
            # pendiente y confirma latido y presencia juntos: cada commit extra
            # cerraba la transacción y la siguiente consulta abría otra, con sus
            # seis ``set_config`` de RLS. En una petición de solo lectura eso
            # eran tres transacciones y tres checkouts del pool donde basta uno.
            _confirmar(db, confirmar)
        _memo_latidos().add(org_id)
        return True
    except Exception:
        log.warning("No se pudo anotar el latido diario (org %r).",
                    db.info.get("organizacion_id"))
        try:
            db.rollback()
        except Exception:
            pass
        return False


def dias_sin_uso(ultima: datetime | None, *, hoy: datetime | None = None) -> int | None:
    """Días desde la última actividad (None si nunca hubo). Utilidad del panel."""
    if ultima is None:
        return None
    referencia = hoy or datetime.utcnow()
    return max((referencia - ultima).days, 0)


# ---------------------------------------------------------------------------
# Presencia en vivo (sesion.activa)
# ---------------------------------------------------------------------------

#: Memo por proceso: última vez que se escribió presencia de cada organización.
#: Evita una consulta y una escritura por petición; la verificación real sigue
#: siendo la base, así los procesos serverless (fríos por definición) no
#: duplican filas dentro de la ventana de escritura.
_PRESENCIA: dict[int, datetime] = {}

#: Tope del memo para que un proceso de vida larga no acumule organizaciones.
_PRESENCIA_MAXIMO = 5000


def marcar_presencia(
    db,
    *,
    pagina: str = "",
    ahora: datetime | None = None,
    confirmar: bool = True,
) -> bool:
    """Anota que alguien de la organización está usando el producto **ahora**.

    Es la señal que faltaba para responder «qué empresas están en línea»: el
    latido (``actividad.diaria``) solo deja una fila por día y no distingue
    una empresa trabajando ahora mismo de una que entró a las 8 de la mañana.

    Se escribe como mucho una fila cada ``PRESENCIA_ESCRITURA_MINUTOS`` por
    organización. Best-effort como el resto de la telemetría: nunca lanza y
    nunca rompe la petición.
    """
    try:
        org_id = int(db.info.get("organizacion_id") or 0)
        if org_id <= 0:
            return False
        ahora = ahora or datetime.utcnow()
        ultimo = _PRESENCIA.get(org_id)
        if ultimo is not None and (ahora - ultimo) < timedelta(
            minutes=PRESENCIA_ESCRITURA_MINUTOS
        ):
            return True
        desde = ahora - timedelta(minutes=PRESENCIA_ESCRITURA_MINUTOS)
        existe = (
            db.query(EventoProducto.id)
            .filter(
                EventoProducto.accion == "sesion.activa",
                EventoProducto.organizacion_id == org_id,
                EventoProducto.created_at >= desde,
            )
            .first()
        )
        if existe is None:
            ruta = str(pagina or "")[:120]
            db.add(
                EventoProducto(
                    organizacion_id=org_id,
                    actor_email=str(db.info.get("auth_email") or "")[:254],
                    accion="sesion.activa",
                    detalle=_serializar_detalle({"pagina": ruta} if ruta else None),
                    # La marca temporal es la del instante medido: así la
                    # ventana de escritura se calcula sobre el mismo reloj.
                    created_at=ahora,
                )
            )
            # Igual que el latido: ``confirmar=False`` lo confirma la puerta.
            _confirmar(db, confirmar)
        if len(_PRESENCIA) > _PRESENCIA_MAXIMO:
            _PRESENCIA.clear()
        _PRESENCIA[org_id] = ahora
        return True
    except Exception:
        log.warning(
            "No se pudo anotar la presencia (org %r).",
            db.info.get("organizacion_id"),
        )
        try:
            db.rollback()
        except Exception:
            pass
        return False


def ventana(dias: int) -> tuple[datetime, datetime]:
    """ ``(desde, hasta)`` de los últimos ``dias`` hasta ahora."""
    hasta = datetime.utcnow()
    return hasta - timedelta(days=dias), hasta
