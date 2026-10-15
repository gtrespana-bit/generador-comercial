"""Libro de ventas del panel: cada cobro confirmado, con su fecha y su cliente.

El panel sabía calcular MRR, ingresos del mes y cobros del mes natural, pero
**ninguna pantalla respondía a «¿qué he vendido?»**: una venta de Stripe se
confirmaba sola por webhook, quedaba como licencia activa y solo se veía
indagando en la tabla de contratos o en los movimientos del mes. El titular se
enteraba por el correo del banco.

Este servicio responde a las preguntas del negocio, en este orden:

1. **¿Qué acabo de vender?** — ``ultimas_ventas``: la cola de ventas recientes,
   la que se pinta en «Hoy» y resume «novedad desde tu última visita».
2. **¿Cómo va el mes?** — ``resumen_ventas``: ventas de hoy, de la semana, del
   mes, del mes anterior (para comparar), ticket medio y desglose por plan y
   método de cobro, más la lista completa con filtros.
3. **¿De dónde vienen?** — cada fila dice si el cobro fue automático (Stripe,
   incluida la renovación mensual) o manual (comprobante activado por ti), con
   el comprador real y la ficha del cliente a un clic.

La fuente es ``compras_plan`` en estado ``activa`` (y ``licencias`` de pago para
el importe y el período), las dos tablas que el operador ya puede leer por RLS.
No se abre ningún dato de negocio de un cliente.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

from ..datos_pago import METODO_STRIPE, metodo_info, plan_info
from ..models import CompraPlan, Licencia, Organizacion
from ..panel_arquitectura import ruta_panel

#: Ventana en la que una venta se considera «novedad» y se destaca en el panel.
HORAS_NOVEDAD = 48

PERIODOS = (
    ("hoy", "Hoy"),
    ("7d", "Últimos 7 días"),
    ("mes", "Este mes"),
    ("30d", "Últimos 30 días"),
    ("anio", "Este año"),
    ("todo", "Todo"),
)
PERIODOS_ETIQUETA = dict(PERIODOS)


def _fecha_cobro(compra: CompraPlan) -> datetime:
    """Momento en que la venta quedó cobrada.

    ``revisado_at`` es cuando se activó (manual o por webhook); si falta, se
    usa la fecha de creación, que en Stripe es prácticamente la misma y en el
    cobro manual es el día en que el cliente declaró el pago.
    """
    return compra.revisado_at or compra.created_at or datetime.utcnow()


def _importe(compra: CompraPlan, licencia: Licencia | None) -> float:
    if licencia is not None and licencia.importe:
        return float(licencia.importe)
    return float(compra.importe or 0.0)


def _periodo_ventana(periodo: str, hoy: date) -> tuple[datetime | None, datetime | None]:
    """``(desde, hasta)`` en datetime, con ``hasta`` exclusivo."""
    clave = str(periodo or "mes").strip().lower()
    if clave == "hoy":
        inicio = datetime.combine(hoy, datetime.min.time())
        return inicio, inicio + timedelta(days=1)
    if clave == "7d":
        return datetime.combine(hoy - timedelta(days=6), datetime.min.time()), None
    if clave == "30d":
        return datetime.combine(hoy - timedelta(days=29), datetime.min.time()), None
    if clave == "anio":
        return datetime(hoy.year, 1, 1), None
    if clave == "todo":
        return None, None
    inicio_mes = hoy.replace(day=1)
    return datetime(inicio_mes.year, inicio_mes.month, 1), None


def _limites_mes(mes: date) -> tuple[datetime, datetime]:
    inicio = datetime(mes.year, mes.month, 1)
    if mes.month == 12:
        fin = datetime(mes.year + 1, 1, 1)
    else:
        fin = datetime(mes.year, mes.month + 1, 1)
    return inicio, fin


def ventas_confirmadas(db) -> list[dict]:
    """Todas las ventas cobradas, de la más reciente a la más antigua."""
    compras = (
        db.query(CompraPlan)
        .filter(CompraPlan.estado == "activa")
        .order_by(CompraPlan.revisado_at.desc(), CompraPlan.id.desc())
        .all()
    )
    if not compras:
        return []

    organizaciones = {o.id: o for o in db.query(Organizacion).all()}
    licencias = {
        lic.id: lic
        for lic in db.query(Licencia)
        .filter(Licencia.id.in_([c.licencia_id for c in compras if c.licencia_id]))
        .all()
    }

    ventas = []
    for compra in compras:
        licencia = licencias.get(compra.licencia_id) if compra.licencia_id else None
        organizacion = organizaciones.get(compra.organizacion_id)
        try:
            plan_nombre = plan_info(compra.plan)["nombre"]
        except KeyError:
            plan_nombre = compra.plan or "Plan"
        try:
            metodo_nombre = metodo_info(compra.metodo_pago)["nombre"]
        except KeyError:
            metodo_nombre = compra.metodo_pago or "—"
        # Renovación automática: la factura encadena una compra nueva sobre una
        # suscripción de Stripe que ya existía. Se distingue del primer cobro
        # por el origen: la compra del alta nace del checkout (lleva
        # ``stripe_checkout_session_id``) y la renovación nace de la factura,
        # sin sesión de pago. El negocio no lee igual «alta» que «renovación».
        renovacion = bool(compra.stripe_invoice_id) and not bool(
            compra.stripe_checkout_session_id
        )
        ventas.append(
            {
                "compra": compra,
                "licencia": licencia,
                "organizacion_id": compra.organizacion_id,
                "organizacion_nombre": (
                    organizacion.nombre if organizacion else f"Organización #{compra.organizacion_id}"
                ),
                "comprador_email": str(compra.creada_por_email or ""),
                "plan": compra.plan,
                "plan_nombre": plan_nombre,
                "metodo_pago": compra.metodo_pago,
                "metodo_nombre": metodo_nombre,
                "automatica": compra.metodo_pago == METODO_STRIPE,
                "renovacion": renovacion,
                "importe": _importe(compra, licencia),
                "moneda": (licencia.moneda if licencia and licencia.moneda else compra.moneda) or "USD",
                "fecha": _fecha_cobro(compra),
                "inicio": (licencia.inicio if licencia else compra.licencia_inicio),
                "vence": (licencia.vence if licencia else compra.licencia_vence),
                "url_cliente": f"/admin/clientes/{compra.organizacion_id}",
            }
        )
    ventas.sort(key=lambda v: (v["fecha"], v["compra"].id), reverse=True)
    return ventas


def _es_novedad(fecha: datetime, ahora: datetime) -> bool:
    return (ahora - fecha) <= timedelta(hours=HORAS_NOVEDAD)


def _filtrar(
    ventas: list[dict],
    *,
    periodo: str,
    plan: str = "",
    metodo: str = "",
    q: str = "",
    hoy: date,
) -> list[dict]:
    desde, hasta = _periodo_ventana(periodo, hoy)
    texto = str(q or "").strip().lower()
    salida = []
    for venta in ventas:
        fecha = venta["fecha"]
        if desde and fecha < desde:
            continue
        if hasta and fecha >= hasta:
            continue
        if plan and venta["plan"] != plan:
            continue
        if metodo:
            if metodo == "auto" and not venta["automatica"]:
                continue
            if metodo == "manual" and venta["automatica"]:
                continue
            if metodo not in {"auto", "manual"} and venta["metodo_pago"] != metodo:
                continue
        if texto and texto not in " ".join(
            (
                venta["organizacion_nombre"],
                venta["comprador_email"],
                venta["plan_nombre"],
                venta["metodo_nombre"],
                str(venta["compra"].id),
            )
        ).lower():
            continue
        salida.append(venta)
    return salida


def resumen_ventas(
    db,
    *,
    hoy: date | None = None,
    periodo: str = "mes",
    plan: str = "",
    metodo: str = "",
    q: str = "",
    ahora: datetime | None = None,
) -> dict:
    """KPIs del negocio y ventas del período pedido, ya filtradas."""
    hoy = hoy or date.today()
    ahora = ahora or datetime.utcnow()
    periodo = periodo if periodo in PERIODOS_ETIQUETA else "mes"

    todas = ventas_confirmadas(db)
    inicio_mes, fin_mes = _limites_mes(hoy.replace(day=1))
    mes_anterior = (hoy.replace(day=1) - timedelta(days=1)).replace(day=1)
    inicio_mes_anterior, fin_mes_anterior = _limites_mes(mes_anterior)
    inicio_hoy = datetime.combine(hoy, datetime.min.time())
    inicio_7d = datetime.combine(hoy - timedelta(days=6), datetime.min.time())

    total_mes = sum(v["importe"] for v in todas if inicio_mes <= v["fecha"] < fin_mes)
    total_mes_anterior = sum(
        v["importe"] for v in todas if inicio_mes_anterior <= v["fecha"] < fin_mes_anterior
    )
    ventas_mes = [v for v in todas if inicio_mes <= v["fecha"] < fin_mes]
    ventas_hoy = [v for v in todas if v["fecha"] >= inicio_hoy]

    variacion = None
    if total_mes_anterior > 0:
        variacion = round((total_mes - total_mes_anterior) / total_mes_anterior * 100, 1)

    acumulado = sum(v["importe"] for v in todas)
    visibles = _filtrar(todas, periodo=periodo, plan=plan, metodo=metodo, q=q, hoy=hoy)
    for venta in visibles:
        venta["es_novedad"] = _es_novedad(venta["fecha"], ahora)

    por_plan: dict[str, dict] = {}
    por_metodo: dict[str, dict] = {}
    for venta in todas:
        if not (inicio_mes <= venta["fecha"] < fin_mes):
            continue
        fila_plan = por_plan.setdefault(
            venta["plan"], {"plan": venta["plan"], "nombre": venta["plan_nombre"], "total": 0.0, "numero": 0}
        )
        fila_plan["total"] += venta["importe"]
        fila_plan["numero"] += 1
        fila_metodo = por_metodo.setdefault(
            venta["metodo_pago"],
            {"metodo": venta["metodo_pago"], "nombre": venta["metodo_nombre"], "total": 0.0, "numero": 0},
        )
        fila_metodo["total"] += venta["importe"]
        fila_metodo["numero"] += 1

    return {
        "hoy": hoy,
        "periodo": periodo,
        "periodo_etiqueta": PERIODOS_ETIQUETA[periodo],
        "filas": visibles,
        "total_filas": len(visibles),
        "kpis": {
            "ventas_hoy": len(ventas_hoy),
            "importe_hoy": sum(v["importe"] for v in ventas_hoy),
            "ventas_7d": len([v for v in todas if v["fecha"] >= inicio_7d]),
            "importe_7d": sum(v["importe"] for v in todas if v["fecha"] >= inicio_7d),
            "ventas_mes": len(ventas_mes),
            "importe_mes": total_mes,
            "importe_mes_anterior": total_mes_anterior,
            "variacion_mes": variacion,
            "ticket_medio_mes": (total_mes / len(ventas_mes)) if ventas_mes else 0.0,
            "ventas_totales": len(todas),
            "importe_total": acumulado,
            "renovaciones_mes": len([v for v in ventas_mes if v["renovacion"]]),
            "importe_renovaciones_mes": sum(
                v["importe"] for v in ventas_mes if v["renovacion"]
            ),
            "primeras_ventas_mes": len([v for v in ventas_mes if not v["renovacion"]]),
        },
        "por_plan": sorted(por_plan.values(), key=lambda f: f["total"], reverse=True),
        "por_metodo": sorted(por_metodo.values(), key=lambda f: f["total"], reverse=True),
        "url_ventas": ruta_panel("ingresos", "ventas"),
    }


def ultimas_ventas(db, *, limite: int = 5, ahora: datetime | None = None) -> list[dict]:
    """Las últimas ventas confirmadas, con la marca de novedad de 48 h."""
    ahora = ahora or datetime.utcnow()
    ventas = ventas_confirmadas(db)[: max(1, int(limite or 5))]
    for venta in ventas:
        venta["es_novedad"] = _es_novedad(venta["fecha"], ahora)
    return ventas


def aviso_venta_reciente(db, *, horas: int = 72, limite: int = 3) -> list[dict]:
    """Ventas de las últimas horas, para la campana del panel."""
    corte = datetime.utcnow() - timedelta(hours=max(1, int(horas or 72)))
    return [v for v in ventas_confirmadas(db) if v["fecha"] >= corte][: max(1, int(limite or 3))]


# ---------------------------------------------------------------------------
# Altas de cuenta y pruebas: el otro aviso que el titular quiere ver
# ---------------------------------------------------------------------------


def registros_recientes(db, *, limite: int = 6, dias: int = 30) -> list[dict]:
    """Altas de cuenta y empresas nuevas (pruebas) de los últimos días.

    Se leen de la telemetría de producto, que ya anota ``cuenta.registrada``
    (global, antes de existir la empresa) y ``organizacion.creada``. Así el
    panel cuenta el embudo completo sin abrir ninguna tabla de tenant.
    """
    from ..models import EventoProducto

    desde = datetime.utcnow() - timedelta(days=max(1, int(dias or 30)))
    eventos = (
        db.query(EventoProducto)
        .filter(
            EventoProducto.accion.in_(("cuenta.registrada", "organizacion.creada")),
            EventoProducto.created_at >= desde,
        )
        .order_by(EventoProducto.created_at.desc(), EventoProducto.id.desc())
        .limit(max(1, int(limite or 6)) * 3)
        .all()
    )
    organizaciones = {o.id: o.nombre for o in db.query(Organizacion).all()}

    registros = []
    for evento in eventos:
        detalle = evento.detalle_dict()
        if evento.accion == "cuenta.registrada":
            registros.append(
                {
                    "tipo": "cuenta",
                    "titulo": "Cuenta nueva",
                    "email": str(evento.actor_email or ""),
                    "detalle": str(detalle.get("pais") or ""),
                    "organizacion_nombre": "",
                    "fecha": evento.created_at,
                }
            )
        else:
            registros.append(
                {
                    "tipo": "prueba",
                    "titulo": "Empresa nueva",
                    "email": str(evento.actor_email or ""),
                    "detalle": str(detalle.get("pais") or ""),
                    "organizacion_nombre": organizaciones.get(evento.organizacion_id, ""),
                    "fecha": evento.created_at,
                }
            )
        if len(registros) >= max(1, int(limite or 6)):
            break
    return registros


def resumen_registros(db, *, hoy: date | None = None) -> dict:
    """Cuántas altas hay hoy, esta semana y este mes (cabecera de la tarjeta)."""
    from sqlalchemy import func

    from ..models import EventoProducto

    hoy = hoy or date.today()
    inicio_mes = datetime(hoy.year, hoy.month, 1)
    inicio_hoy = datetime.combine(hoy, datetime.min.time())
    inicio_7d = datetime.combine(hoy - timedelta(days=6), datetime.min.time())

    def _contar(desde: datetime) -> int:
        return int(
            db.query(func.count(EventoProducto.id))
            .filter(
                EventoProducto.accion == "cuenta.registrada",
                EventoProducto.created_at >= desde,
            )
            .scalar()
            or 0
        )

    return {
        "hoy": _contar(inicio_hoy),
        "semana": _contar(inicio_7d),
        "mes": _contar(inicio_mes),
    }
