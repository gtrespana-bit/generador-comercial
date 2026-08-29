"""Centro de cobros del panel (Fase 2, B2).

Une en una sola vista lo que el operador necesita para cerrar el mes:

- **Ingresos del producto** procedentes de `licencias` de pago (dato del
  titular, RLS de operador).
- **Compras de plan** (`compras_plan`) con su estado.
- **Facturas y pagos** de los clientes, leídos solo a través de la función
  `cotizat_security.admin_cobros_cliente` en PostgreSQL (o consulta directa en
  SQLite para pruebas/escritorio).

El servicio nunca abre el contenido de un presupuesto ni desactiva RLS.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import or_, text

from ..models import CompraPlan, Licencia, Organizacion
from .licencias import vence_cadena

_ETIQUETAS_ESTADO_COMPRA = {
    "pendiente": "Pendiente",
    "activa": "Activada",
    "rechazada": "Rechazada",
}


def _normalizar_numero(valor):
    if valor is None:
        return 0.0
    if isinstance(valor, Decimal):
        return float(valor)
    try:
        return float(valor)
    except (TypeError, ValueError):
        return 0.0


def _mes_borde(mes: date):
    inicio = mes.replace(day=1)
    if inicio.month == 12:
        fin = inicio.replace(year=inicio.year + 1, month=1, day=1)
    else:
        fin = inicio.replace(month=inicio.month + 1, day=1)
    return inicio, fin


def _cobros_tenant_mes(db, inicio: date, fin: date) -> list[dict]:
    """Facturas/pagos del mes. En PostgreSQL vía función por cada organización."""
    if db.get_bind().dialect.name == "postgresql":
        orgs = db.query(Organizacion).all()
        movimientos = []
        for org in orgs:
            filas = db.execute(
                text("SELECT * FROM cotizat_security.admin_cobros_cliente(:org)"),
                {"org": int(org.id)},
            ).mappings().all()
            for fila in filas:
                fecha = fila.get("fecha")
                if not fecha:
                    continue
                if isinstance(fecha, datetime):
                    fecha = fecha.date()
                if not (inicio <= fecha < fin):
                    continue
                movimientos.append({
                    "tipo": str(fila.get("tipo") or "factura"),
                    "numero": str(fila.get("numero") or ""),
                    "fecha": fecha,
                    "importe": _normalizar_numero(fila.get("importe")),
                    "moneda": str(fila.get("moneda") or "USD"),
                    "estado": str(fila.get("estado") or ""),
                    "organizacion_id": org.id,
                    "organizacion_nombre": org.nombre,
                })
        return movimientos

    from ..models import Factura, Pago

    movimientos = []
    for f in db.query(Factura).filter(Factura.fecha >= inicio, Factura.fecha < fin).all():
        org = db.get(Organizacion, f.organizacion_id)
        movimientos.append({
            "tipo": "factura",
            "numero": f.numero,
            "fecha": f.fecha,
            "importe": _normalizar_numero(f.total),
            "moneda": f.moneda or "USD",
            "estado": f.estado or "emitida",
            "organizacion_id": f.organizacion_id,
            "organizacion_nombre": org.nombre if org else "—",
        })
    for p in db.query(Pago).filter(Pago.fecha >= inicio, Pago.fecha < fin).all():
        org = db.get(Organizacion, p.organizacion_id)
        movimientos.append({
            "tipo": "pago",
            "numero": p.referencia or f"pago-{p.id}",
            "fecha": p.fecha,
            "importe": _normalizar_numero(p.importe),
            "moneda": p.moneda or "USD",
            "estado": p.estado or "confirmado",
            "organizacion_id": p.organizacion_id,
            "organizacion_nombre": org.nombre if org else "—",
        })
    return movimientos


def resumen_cobros(
    db,
    *,
    mes: date | None = None,
    hoy: date | None = None,
    organizacion_id: int | None = None,
) -> dict:
    """Cobros del mes pedido: producto + compras + facturas/pagos de clientes."""
    hoy = hoy or date.today()
    mes = mes or hoy.replace(day=1)
    inicio, fin = _mes_borde(mes)

    # 1) Ingresos de licencias de pago (dato del titular, ya visible al operador).
    licencias = db.query(Licencia).filter(
        Licencia.origen == "pago",
        Licencia.importe > 0,
    ).all()
    if organizacion_id:
        licencias = [l for l in licencias if l.organizacion_id == organizacion_id]

    compras = (
        db.query(CompraPlan)
        .filter(CompraPlan.created_at >= inicio, CompraPlan.created_at < fin)
        .order_by(CompraPlan.created_at.desc())
        .all()
    )
    if organizacion_id:
        compras = [c for c in compras if c.organizacion_id == organizacion_id]

    orgs = {o.id: o for o in db.query(Organizacion).all()}

    movimientos = []
    for lic in licencias:
        fecha = (lic.created_at or datetime.utcnow()).date()
        if inicio <= fecha < fin:
            movimientos.append({
                "tipo": "licencia",
                "numero": f"lic-{lic.id}",
                "fecha": fecha,
                "importe": _normalizar_numero(lic.importe),
                "moneda": lic.moneda or "USD",
                "estado": "pagada" if lic.origen == "pago" else "sin_cobro",
                "organizacion_id": lic.organizacion_id,
                "organizacion_nombre": orgs.get(lic.organizacion_id).nombre if lic.organizacion_id in orgs else "—",
            })
    for compra in compras:
        fecha = (compra.created_at or datetime.utcnow()).date()
        movimientos.append({
            "tipo": "compra",
            "numero": f"compra-{compra.id}",
            "fecha": fecha,
            "importe": _normalizar_numero(compra.importe),
            "moneda": compra.moneda or "USD",
            "estado": _ETIQUETAS_ESTADO_COMPRA.get(compra.estado, compra.estado),
            "organizacion_id": compra.organizacion_id,
            "organizacion_nombre": orgs.get(compra.organizacion_id).nombre if compra.organizacion_id in orgs else "—",
        })

    if not organizacion_id:
        movimientos.extend(_cobros_tenant_mes(db, inicio, fin))
    else:
        for mov in _cobros_tenant_mes(db, inicio, fin):
            if mov["organizacion_id"] == int(organizacion_id):
                movimientos.append(mov)

    movimientos.sort(key=lambda m: (m["fecha"] or date.min, m["numero"]), reverse=True)

    ingresos_mes = sum(m["importe"] for m in movimientos if m["tipo"] == "licencia")
    cobrado_mes = sum(
        m["importe"] for m in movimientos if m["tipo"] in ("pago", "compra") and m["estado"] in ("confirmado", "Activada", "pagada")
    )
    pendientes_mes = sum(
        1 for m in movimientos
        if m["estado"] in ("pendiente", "Pendiente", "emitida", "vencida")
    )
    return {
        "mes": mes,
        "inicio": inicio,
        "fin": fin - timedelta(days=1),
        "movimientos": movimientos,
        "ingresos_mes": _normalizar_numero(ingresos_mes),
        "cobrado_mes": _normalizar_numero(cobrado_mes),
        "pendientes_mes": pendientes_mes,
        "total_movimientos": len(movimientos),
    }
