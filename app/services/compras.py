"""Registro de compras de plan y activación manual de licencias (E1-059).

Flujo del piloto con cobro manual:

    Cliente (sesión iniciada) → elige plan y método → declara datos de
    verificación → sube comprobante → queda ``pendiente`` y el titular recibe
    el email con todo (comprobante adjunto). El operador revisa en el panel
    ``/admin/compras`` y activa (crea/renueva la ``Licencia``) o rechaza.

La compra es una tabla tenant (pertenece a la organización compradora). El
operador la lee por la política RLS marcada con ``es_operador``; la sesión de
cliente solo ve las suyas.
"""
from __future__ import annotations

from datetime import datetime
import json
import logging

from sqlalchemy.orm import Session

from ..datos_pago import (
    ESTADOS_COMPRA,
    PLANES,
    metodo_conocido,
    metodo_info,
    plan_info,
)
from ..models import CompraPlan, Licencia, Organizacion
from .licencias import GestionLicenciaError, crear_licencia

log = logging.getLogger("cotizat.compras")


class GestionCompraError(RuntimeError):
    """La operación sobre una compra no respeta las reglas del registro."""


def _plan_valido(plan: str) -> bool:
    return plan in PLANES


def _metodo_valido(metodo: str) -> bool:
    return metodo_conocido(metodo)


def crear_compra(
    db: Session,
    *,
    organizacion_id: int,
    plan: str,
    metodo_pago: str,
    datos_verificacion: dict,
    comprobante_reference: str,
    comprobante_nombre: str,
    comprobante_mime: str,
    creada_por_usuario_id: int | None,
    creada_por_email: str,
    exigir_comprobante: bool = True,
    stripe_checkout_session_id: str | None = None,
) -> CompraPlan:
    """Registra una compra pendiente con su comprobante.

    No valida el comprobante (eso lo hace la ruta antes de guardarlo en el
    almacenamiento); aquí solo se exige que la referencia exista y que los
    campos de plan/método sean válidos. Stripe no pide comprobante: el
    webhook es la prueba del cobro (``exigir_comprobante=False``).
    """
    plan = str(plan or "").strip().lower()
    metodo_pago = str(metodo_pago or "").strip().lower()
    if not _plan_valido(plan):
        raise GestionCompraError("El plan indicado no existe.")
    if not _metodo_valido(metodo_pago):
        raise GestionCompraError("El método de pago indicado no existe.")
    if exigir_comprobante and not comprobante_reference:
        raise GestionCompraError(
            "Adjunta el comprobante de pago para continuar."
        )
    if not isinstance(datos_verificacion, dict):
        raise GestionCompraError("Los datos de verificación no son válidos.")

    ficha = plan_info(plan)
    compra = CompraPlan(
        organizacion_id=int(organizacion_id),
        plan=plan,
        metodo_pago=metodo_pago,
        importe=float(ficha["importe"]),
        moneda="USD",
        datos_verificacion=json.dumps(
            datos_verificacion, ensure_ascii=False, separators=(",", ":")
        ),
        comprobante_reference=str(comprobante_reference),
        comprobante_nombre=str(comprobante_nombre or "comprobante"),
        comprobante_mime=str(comprobante_mime or "application/octet-stream"),
        estado="pendiente",
        creada_por_usuario_id=creada_por_usuario_id,
        creada_por_email=str(creada_por_email or ""),
    )
    if stripe_checkout_session_id:
        # Se fija en el INSERT: RLS no deja al cliente hacer UPDATE de
        # ``compras_plan`` (solo el operador activa/rechaza).
        compra.stripe_checkout_session_id = str(stripe_checkout_session_id)[:255]
    db.add(compra)
    db.flush()
    return compra


def _exigir_compra(db: Session, compra_id: int) -> CompraPlan:
    compra = db.get(CompraPlan, compra_id)
    if compra is None:
        raise GestionCompraError("La compra indicada no existe.")
    return compra


def activar_compra(
    db: Session,
    *,
    compra_id: int,
    operador_email: str,
    hoy=None,
    exigir_comprobante: bool = True,
) -> tuple[CompraPlan, Licencia]:
    """Verifica una compra pendiente y concede la licencia del plan.

    Valida que la compra esté pendiente (no se puede activar dos veces),
    llama a ``crear_licencia`` con el importe real del plan y enlaza la
    licencia resultante a la compra. Devuelve ``(compra, licencia)``.
    Stripe no trae comprobante: el webhook llama con
    ``exigir_comprobante=False``.
    """
    from datetime import date

    hoy = hoy or date.today()
    compra = _exigir_compra(db, compra_id)
    if compra.estado != "pendiente":
        raise GestionCompraError(
            f"La compra ya está {compra.etiqueta_estado.lower()}."
        )
    if exigir_comprobante and not compra.comprobante_reference:
        raise GestionCompraError(
            "La compra no tiene comprobante adjunto; no se puede activar."
        )

    ficha = plan_info(compra.plan)
    licencia = crear_licencia(
        db,
        organizacion_id=compra.organizacion_id,
        origen="pago",
        duracion=ficha["duracion_licencia"],
        importe=compra.importe,
        moneda=compra.moneda or "USD",
        metodo_cobro=_etiqueta_metodo(compra.metodo_pago),
        referencia=_referencia_compra(compra),
        notas=(
            f"Activación de compra #{compra.id} "
            f"({compra.plan}, {compra.etiqueta_estado})."
        ),
        operador_email=operador_email,
        hoy=hoy,
    )
    compra.estado = "activa"
    compra.licencia_id = licencia.id
    # El período se copia sobre la compra a propósito: `licencias` la reserva
    # el RLS al operador, así que sin esta copia el comprador no podría emitir
    # su propio recibo. Además congela lo cobrado aunque la licencia cambie.
    compra.licencia_inicio = licencia.inicio
    compra.licencia_vence = licencia.vence
    compra.revisado_por_email = str(operador_email or "")
    compra.revisado_at = datetime.utcnow()
    db.flush()
    return compra, licencia


def rechazar_compra(
    db: Session,
    *,
    compra_id: int,
    operador_email: str,
) -> CompraPlan:
    """Rechaza una compra pendiente (comprobante inválido, pago incompleto…)."""
    compra = _exigir_compra(db, compra_id)
    if compra.estado != "pendiente":
        raise GestionCompraError(
            f"La compra ya está {compra.etiqueta_estado.lower()}."
        )
    compra.estado = "rechazada"
    compra.revisado_por_email = str(operador_email or "")
    compra.revisado_at = datetime.utcnow()
    db.flush()
    return compra


def _etiqueta_metodo(metodo: str) -> str:
    return metodo_info(metodo)["nombre"]


def _referencia_compra(compra: CompraPlan) -> str:
    """Referencia corta para la licencia: plan + método + operación/ID."""
    datos = compra.datos_verificacion_dict()
    claves = (
        "numero_operacion",
        "hash_transaccion",
        "binance_id_origen",
        "wallet_origen",
    )
    for clave in claves:
        valor = str(datos.get(clave) or "").strip()
        if valor:
            return valor[:60]
    return f"compra-{compra.id}"


#: Columnas ordenables de la cola de compras. La clave viaja en la URL y el
#: tercer elemento es la dirección con la que empieza al pulsarla por primera
#: vez: la fecha y el importe interesan de mayor a menor.
ORDENES_COMPRAS = (
    ("fecha", "Fecha", "desc"),
    ("importe", "Importe", "desc"),
    ("cliente", "Cliente", "asc"),
    ("estado", "Estado", "asc"),
)


def _fila_compra(compra: CompraPlan, org: Organizacion | None) -> dict:
    return {
        "compra": compra,
        "organizacion_nombre": org.nombre if org else "—",
        "plan_nombre": plan_info(compra.plan)["nombre"],
        "metodo_nombre": _etiqueta_metodo(compra.metodo_pago),
        "verificacion": compra.datos_verificacion_dict(),
    }


def _consulta_compras(db: Session, *, estado: str = "pendiente", q: str = ""):
    """Consulta base de la cola: la comparten la pantalla y el CSV.

    La organización entra por ``outerjoin`` para no perder una compra cuyo
    cliente se dio de baja; en ese caso el panel muestra «—» en vez de
    desaparecer la fila.
    """
    from sqlalchemy import or_

    consulta = db.query(CompraPlan, Organizacion).outerjoin(
        Organizacion, CompraPlan.organizacion_id == Organizacion.id
    )
    if estado and estado != "todas":
        consulta = consulta.filter(CompraPlan.estado == estado)

    texto = str(q or "").strip()
    if texto:
        patron = f"%{texto}%"
        condiciones = [
            Organizacion.nombre.ilike(patron),
            Organizacion.slug.ilike(patron),
            CompraPlan.creada_por_email.ilike(patron),
            CompraPlan.comprobante_nombre.ilike(patron),
        ]
        # Escribir el número de compra es la forma más rápida de encontrarla
        # cuando el cliente lo cita en un correo o en una llamada.
        if texto.isdigit():
            condiciones.append(CompraPlan.id == int(texto))
        consulta = consulta.filter(or_(*condiciones))
    return consulta


def _ordenar_compras(consulta, orden: str, direccion: str):
    clave = orden if orden in {o[0] for o in ORDENES_COMPRAS} else "fecha"
    columna = {
        "cliente": Organizacion.nombre,
        "importe": CompraPlan.importe,
        "estado": CompraPlan.estado,
    }.get(clave, CompraPlan.created_at)
    columna = columna.desc() if direccion == "desc" else columna.asc()
    # El id desempata: dos compras del mismo segundo no pueden cambiar de
    # orden entre dos páginas (eso duplicaría o perdería filas al paginar).
    return consulta.order_by(columna, CompraPlan.id.desc())


def listar_compras(
    db: Session,
    *,
    estado: str = "pendiente",
    q: str = "",
    orden: str = "fecha",
    direccion: str = "desc",
    pagina: int = 1,
    por_pagina: int = 25,
) -> tuple[list[dict], dict]:
    """Página de compras con su meta de paginación.

    Sustituye al ``resumen_compras`` completo que cargaba **todas** las compras
    y **todas** las organizaciones en cada visita a la pestaña.
    """
    from .panel_listas import paginar_consulta

    consulta = _ordenar_compras(_consulta_compras(db, estado=estado, q=q), orden, direccion)
    filas, meta = paginar_consulta(consulta, pagina=pagina, por_pagina=por_pagina)
    return [_fila_compra(compra, org) for compra, org in filas], meta


def contadores_compras(db: Session, *, q: str = "") -> dict:
    """Cuántas compras hay por estado, con el mismo filtro de texto.

    Se resuelve con un ``GROUP BY``: antes la pestaña cargaba **todas** las
    compras solo para contarlas y pintar los chips.
    """
    from sqlalchemy import func

    consulta = _consulta_compras(db, estado="todas", q=q)
    filas = (
        consulta.with_entities(CompraPlan.estado, func.count(CompraPlan.id))
        .group_by(CompraPlan.estado)
        .all()
    )
    contadores = {"pendiente": 0, "activa": 0, "rechazada": 0}
    for estado, total in filas:
        contadores[str(estado or "")] = int(total or 0)
    contadores["todas"] = sum(contadores.values())
    return contadores


def exportar_compras(
    db: Session,
    *,
    estado: str = "pendiente",
    q: str = "",
    orden: str = "fecha",
    direccion: str = "desc",
) -> list[dict]:
    """Todas las compras que cumplen el filtro, para el CSV.

    Es la misma consulta que la pantalla, sin recorte: lo que se exporta es
    exactamente lo que se está mirando (mismo filtro y mismo orden).
    """
    consulta = _ordenar_compras(_consulta_compras(db, estado=estado, q=q), orden, direccion)
    return [_fila_compra(compra, org) for compra, org in consulta.all()]


def resumen_compras(db: Session) -> list[dict]:
    """Compras para el panel del operador, de la más reciente a la más antigua.

    Incluye el nombre de la organización compradora (la compra guarda solo el
    id; el panel lo enriquece para que el operador sepa a quién activar).

    Se mantiene para los usos que necesitan el histórico completo (Hoy y la
    ficha del cliente). La pestaña de Compras usa ``listar_compras``.
    """
    compras = db.query(CompraPlan).order_by(CompraPlan.created_at.desc()).all()
    organizaciones = {
        org.id: org for org in db.query(Organizacion).all()
    }
    return [
        _fila_compra(compra, organizaciones.get(compra.organizacion_id))
        for compra in compras
    ]


def compras_de_organizacion(
    db: Session, organizacion_id: int, *, limite: int = 24
) -> list[CompraPlan]:
    """Historial de compras de la organización, para «Mi plan».

    ``compras_plan`` es tabla tenant: la propia organización lo lee sin
    tocar ``licencias``. Se devuelven las más recientes primero (cada
    renovación de Stripe es una compra propia, con su recibo).
    """
    return (
        db.query(CompraPlan)
        .filter(CompraPlan.organizacion_id == int(organizacion_id))
        .order_by(CompraPlan.created_at.desc(), CompraPlan.id.desc())
        .limit(max(int(limite), 1))
        .all()
    )


def ultima_compra_con_recibo(db: Session, organizacion_id: int) -> CompraPlan | None:
    """Última compra activada de una organización, o ``None`` si no hay.

    La usa la tarjeta «Tu plan» para ofrecer el recibo al cliente. Solo se
    consulta ``compras_plan`` (tabla tenant): la sesión del comprador no puede
    leer ``licencias``, y este es justo el motivo por el que la compra guarda
    su propio período.
    """
    return (
        db.query(CompraPlan)
        .filter(
            CompraPlan.organizacion_id == int(organizacion_id),
            CompraPlan.estado == "activa",
            CompraPlan.licencia_id.isnot(None),
            CompraPlan.licencia_vence.isnot(None),
        )
        .order_by(CompraPlan.created_at.desc(), CompraPlan.id.desc())
        .first()
    )


def comprobante_bytes(compra: CompraPlan) -> bytes:
    """Lee los bytes del comprobante desde el almacenamiento privado."""
    from ..storage import read_reference, StorageError

    if not compra.comprobante_reference:
        raise StorageError("La compra no tiene comprobante adjunto.")
    return read_reference(compra.comprobante_reference)


def estados_validos() -> tuple[str, ...]:
    return ESTADOS_COMPRA
