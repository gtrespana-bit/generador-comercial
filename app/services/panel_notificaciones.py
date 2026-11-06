"""Centro de notificaciones del panel (A4): pendientes y alertas del negocio.

La campana consulta solamente datos que el operador ya puede leer por RLS
(organizaciones, licencias, compras, operadores). Nunca abre datos de tenant.
"""
from __future__ import annotations

from datetime import date, timedelta

from collections import defaultdict

from sqlalchemy import func

from ..models import CompraPlan, Licencia, OperadorProducto, Organizacion
from ..operadores import ROLES_OPERADOR_ETIQUETA, operadores_configurados
from .licencias import vence_cadena


#: Tope de la campana. Se aplica al final, después de ordenar por gravedad: el
#: `break` a mitad de la lista dejaba fuera las ventas y el soporte solo porque
#: las licencias se consultaban primero.
_TOPE_AVISOS = 15


def notificaciones_admin(
    db,
    *,
    hoy: date | None = None,
) -> list[dict]:
    """Lista ordenada de avisos activos para la campana del panel."""
    hoy = hoy or date.today()
    avisos: list[dict] = []

    # --- Licencias por vencer (≤15 días) ------------------------------
    licencias = db.query(Licencia).all()
    por_org: dict[int, list[Licencia]] = defaultdict(list)
    for lic in licencias:
        por_org[lic.organizacion_id].append(lic)

    organizaciones = {o.id: o for o in db.query(Organizacion).all()}
    nombres = {o.id: o.nombre for o in organizaciones.values()}

    por_vencer = 0
    for org_id, cadena in por_org.items():
        vigente = next((l for l in cadena if l.vigente(hoy)), None)
        if vigente is None:
            continue
        vence_total = vence_cadena(cadena, hoy) or vigente.vence
        dias = max((vence_total - hoy).days, 0)
        if dias <= 15:
            por_vencer += 1
            avisos.append(_aviso(
                "renovacion",
                "critical" if dias <= 3 else "warning",
                f"{nombres.get(org_id, 'Cliente')} vence en {dias} día(s)",
                # Dos enlaces y los dos hacen cosas distintas: uno renueva a este
                # cliente, el otro abre la lista con el MISMO umbral del aviso
                # (antes el aviso decía «1 día» y la lista enseñaba 15).
                f"El acceso caduca el {vence_total:%d/%m/%Y}.",
                f"/admin/clientes/{org_id}?tab=acceso",
                url_lista=f"/admin/clientes?tab=directorio&dias={'3' if dias <= 3 else '15'}",
                etiqueta_lista=f"Ver los {por_vencer} avisos ≤{'3' if dias <= 3 else '15'} d",
            ))
    # --- Actividad por empresa ------------------------------------------
    # El aviso más caro que faltaba: una cuenta que paga y no entra. Se mide con
    # lo que ya escribe la telemetría del producto, sin abrir tablas de tenant.
    for aviso in _avisos_uso(db, hoy, nombres):
        avisos.append(aviso)
        if len(avisos) >= _TOPE_AVISOS:
            break

    # --- Compras pendientes de activar --------------------------------
    pendientes = db.query(CompraPlan).filter(
        CompraPlan.estado == "pendiente"
    ).order_by(CompraPlan.created_at.asc()).limit(3).all()
    for compra in pendientes:
        nombre = nombres.get(compra.organizacion_id, "Cliente")
        avisos.append(_aviso(
            "compra",
            "warning",
            f"Compra #{compra.id} de {nombre} por activar",
            f"Plan {compra.plan} · {compra.moneda} {compra.importe:,.2f}",
            "/admin/ingresos?tab=compras&estado=pendiente",
        ))

    # --- Seguridad del equipo -----------------------------------------
    equipo_db = db.query(OperadorProducto).all()
    env = operadores_configurados()
    if not equipo_db and not env:
        avisos.append(_aviso(
            "equipo",
            "critical",
            "Equipo vacío: nadie puede administrar el panel",
            "Configura COTIZAT_OPERADORES o da de alta un superadmin.",
            "/admin/sistema?tab=equipo",
        ))
    superadmins_activos = sum(
        1 for op in equipo_db if op.rol == "superadmin" and op.activo
    )
    if env and superadmins_activos == 0:
        avisos.append(_aviso(
            "equipo",
            "warning",
            "Sin superadmin activo en la base",
            "El acceso por COTIZAT_OPERADORES sigue funcionando como semilla.",
            "/admin/sistema?tab=equipo",
        ))

    # --- Ventas recientes ---------------------------------------------
    # La campana avisa de lo que se acaba de vender: era el hueco más caro del
    # panel, porque una venta de Stripe se cerraba sola y no aparecía en
    # ninguna alerta (el titular se enteraba por el correo del banco).
    from .panel_ventas import aviso_venta_reciente

    try:
        ventas = aviso_venta_reciente(db, horas=72, limite=3)
    except Exception:
        ventas = []
    for venta in ventas:
        etiqueta = "Renovación" if venta["renovacion"] else "Venta"
        avisos.append(_aviso(
            "venta",
            "info",
            f"{etiqueta}: {venta['plan_nombre']} · {venta['importe']:.2f} {venta['moneda']}",
            (
                f"{venta['organizacion_nombre']} · {venta['metodo_nombre']} · "
                f"{venta['fecha']:%d/%m %H:%M}"
            ),
            "/admin/ingresos?tab=ventas",
        ))

    # --- Mensajes de soporte sin atender -------------------------------
    from .soporte import contadores_soporte, mensajes_sin_atender

    try:
        pendientes_soporte = contadores_soporte(db).get("nuevo", 0)
    except Exception:
        pendientes_soporte = 0
    if pendientes_soporte:
        ultimos = mensajes_sin_atender(db, limite=3)
        primero = ultimos[0] if ultimos else None
        avisos.append(_aviso(
            "soporte",
            "warning",
            f"{pendientes_soporte} mensaje(s) de soporte sin atender",
            (
                f"El último: «{(primero.asunto or primero.mensaje)[:70]}» de "
                f"{primero.email}."
                if primero
                else "Revisa el buzón de soporte del panel."
            ),
            "/admin/clientes?tab=soporte&estado=nuevo",
        ))

    # --- Altas de cuenta y pruebas -------------------------------------
    from .panel_ventas import registros_recientes

    try:
        registros = registros_recientes(db, limite=2, dias=7)
    except Exception:
        registros = []
    for registro in registros:
        avisos.append(_aviso(
            "registro",
            "info",
            f"{registro['titulo']}: {registro['email'] or 'sin correo'}",
            (
                f"{registro['organizacion_nombre']} · {registro['fecha']:%d/%m %H:%M}"
                if registro["organizacion_nombre"]
                else f"Registro del {registro['fecha']:%d/%m %H:%M}"
            ),
            "/admin/clientes?tab=directorio",
        ))

    # --- Estado del negocio -------------------------------------------
    sin_plan = len(organizaciones) - sum(
        1 for cadena in por_org.values() if any(vigente for vigente in cadena if vigente.vigente(hoy))
    )
    if sin_plan > 0:
        avisos.append(_aviso(
            "negocio",
            "info",
            f"{sin_plan} cliente(s) sin plan activo",
            "Revisar la conversión y las oportunidades de renovación.",
            "/admin/clientes?tab=directorio&plan=sin",
        ))

    return _ordenar(avisos)[:_TOPE_AVISOS]


def _aviso(
    tipo: str,
    severidad: str,
    titulo: str,
    detalle: str,
    url: str,
    *,
    url_lista: str = "",
    etiqueta_lista: str = "",
) -> dict:
    """Un aviso de la campana.

    ``url`` es el hecho concreto (este cliente, esta compra) y ``url_lista`` es
    opcional: la lista completa con el mismo criterio. Antes solo había una y
    siempre era la lista, así que el aviso «Dureconstru vence en 1 día» no
    llevaba a Dureconstru.
    """
    return {
        "id": f"{tipo}-{len(titulo)}-{hash(titulo)}",
        "tipo": tipo,
        "severidad": severidad,
        "titulo": titulo,
        "detalle": detalle,
        "url": url,
        "url_lista": url_lista,
        "etiqueta_lista": etiqueta_lista,
    }


def _ordenar(avisos: list[dict]) -> list[dict]:
    peso = {"critical": 0, "warning": 1, "info": 2}
    return sorted(avisos, key=lambda a: peso.get(a["severidad"], 3))


def _avisos_uso(db, hoy: date, nombres: dict[int, str], *, dias: int = 7) -> list[dict]:
    """«Paga y no entra» y «entró y no hizo nada»: los dos avisos de producto.

    Se apoya en ``eventos_producto``, que el operador ya puede leer por RLS. Es
    best-effort: si la tabla no está o falla, la campana no se cae, solo deja de
    anunciar esto.
    """
    from ..models import EventoProducto
    from .telemetria import ACCIONES_CRITICAS, ACCIONES_RUIDO

    try:
        desde = hoy - timedelta(days=dias)
        filas = (
            db.query(
                EventoProducto.organizacion_id,
                EventoProducto.accion,
                func.count(EventoProducto.id),
            )
            .filter(EventoProducto.created_at >= desde)
            .group_by(EventoProducto.organizacion_id, EventoProducto.accion)
            .all()
        )
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        return []

    criticas: dict[int, int] = {}
    # Una empresa «ha probado algo» si tiene al menos una acción con contenido;
    # los latidos de presencia (RUIDO) no cuentan como uso.
    probaron: set[int] = set()
    for organizacion_id, accion, total in filas:
        if organizacion_id is None:
            continue
        if accion in ACCIONES_CRITICAS:
            criticas[organizacion_id] = criticas.get(organizacion_id, 0) + int(total)
        if accion not in ACCIONES_RUIDO:
            probaron.add(int(organizacion_id))

    avisos: list[dict] = []
    pagando = _organizaciones_pagando(db, hoy)
    for organizacion_id, vence in pagando.items():
        if criticas.get(organizacion_id):
            continue
        nombre = nombres.get(organizacion_id, "Un cliente")
        avisos.append(_aviso(
            "uso",
            "warning",
            f"{nombre} paga y no lo usa desde hace {dias} día(s)",
            f"Su plan sigue vigente hasta el {vence:%d/%m/%Y} y no ha creado ni "
            "enviado nada. Es la señal más temprana de baja.",
            f"/admin/clientes/{organizacion_id}?tab=actividad",
            url_lista="/admin/analitica?tab=clientes&dias=7",
            etiqueta_lista="Ver uso de todas las empresas",
        ))

    altas = _organizaciones_nuevas(db, hoy)
    for organizacion_id in altas:
        if organizacion_id in probaron:
            continue
        nombre = nombres.get(organizacion_id, "Una cuenta")
        avisos.append(_aviso(
            "activacion",
            "info",
            f"{nombre} se registró y no ha probado nada",
            f"Cuenta creada en los últimos {dias} días sin una sola acción. "
            "Un empujón ahora vale más que un correo dentro de un mes.",
            f"/admin/clientes/{organizacion_id}",
        ))
    return avisos


def _organizaciones_pagando(db, hoy: date) -> dict[int, date]:
    """Organización → fecha de fin de su cadena de licencias vigente."""
    try:
        licencias = db.query(Licencia).all()
    except Exception:
        return {}
    cadenas: dict[int, list[Licencia]] = defaultdict(list)
    for licencia in licencias:
        cadenas[licencia.organizacion_id].append(licencia)
    salida: dict[int, date] = {}
    for organizacion_id, cadena in cadenas.items():
        if not any(lic.vigente(hoy) for lic in cadena):
            continue
        vence = vence_cadena(cadena, hoy)
        if vence:
            salida[organizacion_id] = vence
    return salida


def _organizaciones_nuevas(db, hoy: date, *, dias: int = 7) -> list[int]:
    """Organizaciones dadas de alta en los últimos días."""
    try:
        filas = (
            db.query(Organizacion.id, Organizacion.created_at)
            .filter(Organizacion.created_at >= hoy - timedelta(days=dias))
            .all()
        )
    except Exception:
        return []
    return [organizacion_id for organizacion_id, _ in filas if organizacion_id]
